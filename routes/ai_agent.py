from flask import Blueprint, request, jsonify
from models.database import db
from models.product import Product
from models.ai_assistant_config import AiAssistantConfig, AISelectedProvider, FIXED_PROVIDERS
from utils.vector_db import search_products_vector
from utils.fashion_kb import get_fashion_knowledge_base_text, get_color_matching_advice, get_fabric_info, get_occasion_advice
from utils.spelling_tolerance import normalize_clothing_type, normalize_category, normalize_color_spelling
from utils.fashion_match_rules import find_matching_products, get_match_explanation
from utils.seasonal_events import get_seasonal_context_text, get_current_season, get_upcoming_holidays, get_seasonal_recommendations
from utils.product_relations import ensure_product_relations, get_related_clothing_types
from routes.auth import require_auth, get_current_user_optional
from config import Config
import boto3
import csv
import json
import os
import requests
import time
import threading
from sqlalchemy import or_

ai_agent_bp = Blueprint('ai_agent', __name__)

# Path to docs/ai_debug.csv for logging every AI assistant prompt/response
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AI_DEBUG_CSV = os.path.join(_project_root, 'docs', 'ai_debug.csv')


def append_ai_debug_log(message, response=None, action_json=None, error=None):
    """Append one row to docs/ai_debug.csv: message, response, action_json, error. Thread-safe append."""
    if not message and not response and not error:
        return
    try:
        resp_str = (response or '').strip()
        if isinstance(action_json, dict):
            action_str = json.dumps(action_json) if action_json else ''
        else:
            action_str = (action_json or '').strip()
        err_str = (error or '').strip()
        file_exists = os.path.isfile(AI_DEBUG_CSV)
        with open(AI_DEBUG_CSV, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['message', 'response', 'action_json', 'error'])
            writer.writerow([message, resp_str, action_str, err_str])
    except Exception:
        pass  # Do not break chat on log failure


# Canonical action names for message_json / ai_debug (decision engine actions pass through as-is).
INTERNAL_TO_CANONICAL = {'none': 'NONE', 'response': 'Response'}
CANONICAL_ACTIONS = frozenset({
    'NONE', 'Response', 'SEARCH_PRODUCTS',
    'ADD_TO_CART', 'REMOVE_FROM_CART', 'UPDATE_CART_ITEM', 'CLEAR_CART',
    'ADD_TO_WISHLIST', 'REMOVE_FROM_WISHLIST', 'CLEAR_WISHLIST', 'ADD_WISHLIST_TO_CART',
    'VIEW_CART', 'VIEW_WISHLIST', 'VIEW_PRODUCTS', 'VIEW_HOME', 'VIEW_CHECKOUT',
})


def _action_canonical(action):
    if not action:
        return 'NONE'
    a = (action or '').strip()
    key = a.lower()
    if key in INTERNAL_TO_CANONICAL:
        return INTERNAL_TO_CANONICAL[key]
    return a.upper() if a.upper() in CANONICAL_ACTIONS else a.upper()


def build_message_json(permission, action, error, respond, status, filters=None, confidence=None):
    """Build the standard JSON for every message. Used by chat stubs for frontend compatibility."""
    if confidence is None:
        confidence = 0.5
    try:
        confidence = max(0.0, min(1.0, float(confidence)))
    except (TypeError, ValueError):
        confidence = 0.5
    action = action if action is not None else 'none'
    out = {
        'permission': bool(permission),
        'action': action,
        'error': str(error).strip() if error else None,
        'respond': str(respond).strip() if respond else '',
        'status': status if status in ('success', 'error', 'denied') else ('success' if not error else 'error'),
        'confidence': confidence,
        'action_canonical': _action_canonical(action),
        'parameters': dict(filters) if filters and isinstance(filters, dict) else {},
        'message': (respond or '').strip() or (str(error).strip() if error else ''),
    }
    if filters is not None and isinstance(filters, dict):
        out['filters'] = {k: v for k, v in filters.items() if v is not None and v != ''}
    return out


def build_canonical_action_json(action_canonical, parameters, message, confidence=None):
    """Build minimal canonical JSON for ai_debug."""
    if confidence is None:
        confidence = 0.5
    try:
        confidence = max(0.0, min(1.0, float(confidence)))
    except (TypeError, ValueError):
        confidence = 0.5
    return {
        'action': action_canonical if action_canonical in CANONICAL_ACTIONS else 'NONE',
        'parameters': dict(parameters) if isinstance(parameters, dict) else {},
        'message': (message or '').strip(),
        'confidence': confidence,
    }


def _debug_action_from_payload(payload):
    """Build action_json dict for append_ai_debug_log from a response payload."""
    if not payload:
        return build_canonical_action_json('NONE', {}, '')
    mj = payload.get('message_json')
    if mj is not None:
        action_c = mj.get('action_canonical') or INTERNAL_TO_CANONICAL.get((mj.get('action') or 'none').lower(), 'NONE')
        params = mj.get('parameters')
        if params is None and mj.get('filters'):
            params = mj['filters']
        return build_canonical_action_json(action_c or 'NONE', params or {}, mj.get('message') or mj.get('respond') or '', mj.get('confidence'))
    return build_canonical_action_json(
        INTERNAL_TO_CANONICAL.get((payload.get('action') or 'none').lower(), 'NONE'),
        {},
        payload.get('response') or '',
    )


# Project-level Gemini rate limit: minimum seconds between Gemini API requests (avoids burst 429s)
GEMINI_MIN_DELAY = 0.3
_gemini_last_request_time = [0.0]
_gemini_throttle_lock = threading.Lock()


def _gemini_throttle():
    """Enforce minimum delay between Gemini requests to stay under project rate limits."""
    with _gemini_throttle_lock:
        now = time.time()
        elapsed = now - _gemini_last_request_time[0]
        if elapsed < GEMINI_MIN_DELAY and _gemini_last_request_time[0] > 0:
            time.sleep(GEMINI_MIN_DELAY - elapsed)
        _gemini_last_request_time[0] = time.time()


def _normalize_llm_error(exc):
    """Turn requests/API exceptions into a short, user-friendly message for admin test UI."""
    s = str(exc).strip()
    if not s:
        return 'Request failed'
    # HTTP status patterns
    if '401' in s or 'Unauthorized' in s:
        return 'Invalid API key or unauthorized'
    if '403' in s or 'Forbidden' in s:
        return 'Access forbidden — check API key permissions'
    if '429' in s or 'rate limit' in s.lower():
        # Try to include Google's quota message so user knows which limit was hit (RPM/TPM/RPD)
        if hasattr(exc, 'response') and exc.response is not None:
            try:
                body = getattr(exc.response, 'text', None) or ''
                if body:
                    data = json.loads(body)
                    err = data.get('error')
                    if isinstance(err, dict):
                        raw = err.get('message') or err.get('status') or ''
                    elif isinstance(err, str):
                        raw = err
                    else:
                        raw = ''
                    if raw:
                        raw_lower = raw.lower()
                        # Quota/billing exceeded: show actionable steps and links
                        if 'quota' in raw_lower and ('billing' in raw_lower or 'plan' in raw_lower):
                            return (
                                'Gemini quota exceeded — Check your plan and billing: '
                                '1) Open Google AI Studio → https://aistudio.google.com/app/apikey — confirm your project has billing enabled and upgrade to a paid tier if needed. '
                                '2) See rate limits and tiers: https://ai.google.dev/gemini-api/docs/rate-limits'
                            )
                        return f'Rate limited — {raw[:180]}'
            except Exception:
                pass
        return 'Rate limited — try again in a moment'
    if '500' in s or '502' in s or '503' in s:
        return 'Provider server error — try again later'
    if 'timeout' in s.lower() or 'timed out' in s.lower():
        return 'Request timed out'
    if 'Connection' in s or 'connection' in s:
        return 'Connection failed — check network'
    # Try to extract JSON error message from response body (e.g. OpenAI/Anthropic, Google)
    if hasattr(exc, 'response') and exc.response is not None:
        try:
            body = getattr(exc.response, 'text', None) or ''
            if body:
                data = json.loads(body)
                err = data.get('error') or data.get('error_message')
                msg = None
                if isinstance(err, dict) and err.get('message'):
                    msg = err['message'][:200]
                elif isinstance(err, str):
                    msg = err[:200]
                if msg:
                    # Vertex/GCP often returns "API key not valid. Please pass a valid API key."
                    if 'api key' in msg.lower() and 'valid' in msg.lower():
                        msg += ' Use a Vertex AI API key (Google Cloud Console or GOOGLE_API_KEY / VERTEX_API_KEY), not a Gemini AI Studio key.'
                    return msg
        except Exception:
            pass
    # Fallback: first line, truncated
    return s.split('\n')[0][:200] if s else 'Request failed'

DEFAULT_SYSTEM_PROMPT = """You are a professional shopping assistant for InsightShop. Be helpful, concise, and clear. Use a polite, business-appropriate tone. Answer only what the user asked; do not recommend or suggest products unless they explicitly asked for recommendations or suggestions. When listing products they asked for, state Product #ID, name, and price. Do not use excessive exclamation points, slang, or overly casual language."""

# Decision engine: AI must return ONLY valid JSON with action, parameters, message, confidence. No free text outside JSON.
DECISION_ENGINE_SYSTEM_PROMPT = """You are the decision engine for InsightShop. You are NOT a casual chatbot. For EVERY user message you MUST respond with exactly one JSON object and nothing else. No markdown, no explanation, no text before or after the JSON.

Required JSON shape (use exactly these keys):
{
  "action": "<REQUIRED>",
  "parameters": { },
  "message": "<REQUIRED>",
  "confidence": <number between 0 and 1>
}

Allowed actions:
- "Response" — Use for ANY question that does not require a backend action: advice, styling tips, explanations, store policies, product comparisons, "what should I wear", "how do I...", opinions, casual chat. Put your full helpful answer in the "message" field. parameters: {}. Do NOT use NONE for these—use Response and give a real answer in message.
- "NONE" — Only when intent is truly unclear or ambiguous (e.g. could be cart OR wishlist). Ask one short clarification question in message. Use empty parameters {}. Do NOT use NONE for general questions—use Response.
- "SEARCH_PRODUCTS" — User wants to search/browse products. Extract filters into parameters: category (men/women/kids), color, min_price, max_price, search (or query), clothing_type, size, fabric, occasion. Use null for unspecified filters. Keep a memory of filters from recent messages when user adds refinements (e.g. "under 50" after a search).
- "ADD_TO_CART" — Add item to cart. parameters: product_id (required), quantity (default 1), selected_color, selected_size. NEVER invent product_id; if missing use action "NONE" and ask which product.
- "REMOVE_FROM_CART" — parameters: product_id or item_id, selected_color, selected_size.
- "UPDATE_CART_ITEM" — parameters: item_id or product_id, quantity, selected_color, selected_size, old_color, old_size.
- "CLEAR_CART" — Empty the SHOPPING CART (items to buy). parameters: {}. Use only when user says "clear cart", "empty my cart", "remove all from cart".
- "ADD_TO_WISHLIST" — parameters: product_id (required). If missing use "NONE".
- "REMOVE_FROM_WISHLIST" — parameters: product_id.
- "CLEAR_WISHLIST" — Empty the WISHLIST (saved/favorite items). parameters: {}. Use when user says "clear my wishlist", "empty wishlist", "remove all from wishlist". Do NOT use CLEAR_CART for wishlist.
- "ADD_WISHLIST_TO_CART" — User wants to add ALL wishlist items to cart (e.g. "add everything in my wishlist to cart", "add all wishlist items to my cart"). parameters: {}. Use this when the user asks to add the whole wishlist or all wishlist items; do NOT use NONE or ask one-by-one.
- "VIEW_CART", "VIEW_WISHLIST", "VIEW_PRODUCTS", "VIEW_HOME", "VIEW_CHECKOUT" — Navigation. parameters: {}.

Rules:
- parameters must contain ONLY structured data (numbers, strings, null). No natural language inside parameters.
- message: short, friendly, user-facing sentence. No technical jargon.
- confidence: 0.95 = very confident, 0.6 = somewhat ambiguous, 0.3 = likely misunderstood. If unclear use "NONE" and confidence < 0.5.
- Output ONLY the JSON object. No other text."""



def _env_api_key(provider):
    """Get API key from env (including after loading from AWS Secrets Manager)."""
    import os
    if provider == 'openai':
        return os.getenv('OPENAI_API_KEY') or getattr(Config, 'OPENAI_API_KEY', None)
    if provider == 'gemini':
        return os.getenv('GEMINI_API_KEY') or getattr(Config, 'GEMINI_API_KEY', None)
    if provider == 'anthropic':
        return os.getenv('ANTHROPIC_API_KEY') or getattr(Config, 'ANTHROPIC_API_KEY', None)
    if provider == 'vertex':
        # Vertex AI quickstart uses GOOGLE_API_KEY; also support VERTEX_API_KEY and GOOGLE_APPLICATION_CREDENTIALS
        return (
            os.getenv('VERTEX_API_KEY')
            or os.getenv('GOOGLE_API_KEY')
            or os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            or getattr(Config, 'VERTEX_API_KEY', None)
            or getattr(Config, 'GOOGLE_API_KEY', None)
        )
    return None


def get_effective_api_key_for_provider(provider):
    """Return (api_key, source) for a provider. source is 'admin' or 'env'. Decrypts stored keys."""
    try:
        c = AiAssistantConfig.query.filter_by(provider=provider).first()
        if c and c.api_key:
            from utils.secret_storage import decrypt_ciphertext
            return decrypt_ciphertext(c.api_key), 'admin'
        if provider == 'openai':
            key = _env_api_key('openai')
            if key:
                return key, 'env'
        if provider == 'gemini':
            key = _env_api_key('gemini')
            if not key:
                from utils.secrets_loader import load_into_env, get_gemini_api_key_from_aws
                load_into_env()
                key = _env_api_key('gemini')
            if not key:
                # Exception: fetch Gemini key directly from AWS Secrets Manager so admin does not need to set it
                key = get_gemini_api_key_from_aws()
            if key:
                return key, 'env'
        if provider == 'anthropic':
            key = _env_api_key('anthropic')
            if key:
                return key, 'env'
        if provider == 'vertex':
            key = _env_api_key('vertex')
            if key:
                return key, 'env'
    except Exception:
        pass
    return None, 'env'


def get_config_for_provider(provider):
    """Return internal dict for a provider with effective api_key (for call_llm)."""
    try:
        c = AiAssistantConfig.query.filter_by(provider=provider).first()
        api_key, source = get_effective_api_key_for_provider(provider)
        base = c.to_internal_dict() if c else {'provider': provider, 'model_id': None, 'region': None, 'is_enabled': False}
        base['api_key'] = api_key
        base['source'] = source
        if 'is_enabled' not in base:
            base['is_enabled'] = getattr(c, 'is_enabled', False) if c else False
        return base
    except Exception:
        return {'provider': provider, 'api_key': None, 'model_id': None, 'region': None, 'is_enabled': False}


def get_selected_provider():
    """Return selected provider: 'auto' or one of openai, gemini, anthropic, vertex."""
    try:
        row = AISelectedProvider.query.first()
        selected = (row.provider if row else 'auto')
        # Legacy: if DB had 'bedrock' selected, treat as auto (Bedrock removed)
        if selected == 'bedrock':
            return 'auto'
        return selected
    except Exception:
        return 'auto'


def get_effective_provider_config():
    """Return internal dict for the provider to use. Only enabled providers with an API key are used."""
    selected = get_selected_provider()
    if selected != 'auto':
        cfg = get_config_for_provider(selected)
        if cfg.get('is_enabled') and cfg.get('api_key'):
            return cfg
        return None
    for p in FIXED_PROVIDERS:
        cfg = get_config_for_provider(p)
        if cfg.get('is_enabled') and cfg.get('api_key'):
            return cfg
    return None


def get_active_ai_config():
    """Return a config-like object for backward compat: use effective provider config."""
    cfg = get_effective_provider_config()
    if not cfg:
        return None
    class _ConfigLike:
        def to_internal_dict(self):
            return cfg
    return _ConfigLike()


# Initialize Polly client for text-to-speech (AWS Polly only; LLMs are direct API)
polly_client = None
polly_available = False
if Config.AWS_REGION:
    try:
        # Try to initialize Polly client
        # First, try with explicit credentials if provided
        if Config.AWS_ACCESS_KEY_ID and Config.AWS_SECRET_ACCESS_KEY:
            polly_client = boto3.client(
                'polly',
                region_name=Config.AWS_REGION,
                aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY
            )
        else:
            # Fall back to default credential chain (AWS CLI, IAM role, etc.)
            # This allows using AWS CLI configured credentials
            polly_client = boto3.client(
                'polly',
                region_name=Config.AWS_REGION
            )
        
        # Test the client by listing voices (lightweight operation)
        try:
            polly_client.describe_voices(LanguageCode='en-US')
            polly_available = True
            print("[OK] AWS Polly client initialized successfully and verified")
            print(f"   Using region: {Config.AWS_REGION}")
            if not Config.AWS_ACCESS_KEY_ID or not Config.AWS_SECRET_ACCESS_KEY:
                print("   Using AWS default credential chain (AWS CLI credentials)")
        except Exception as test_error:
            print(f"[WARNING] AWS Polly client created but test failed: {test_error}")
            print("   This might indicate missing permissions or incorrect credentials")
            polly_client = None
    except Exception as e:
        print(f"[ERROR] Error initializing Polly client: {e}")
        print("   Voice feature will be disabled")
        polly_client = None

def get_all_products_for_ai():
    """Get all products formatted for AI context (full details + reviews). Use only when full catalog is needed."""
    products = Product.query.filter_by(is_active=True).all()
    return [p.to_dict_for_ai() for p in products]


def get_product_count_for_ai():
    """Lightweight: total count of active products (no loading)."""
    return Product.query.filter_by(is_active=True).count()


def get_product_sample_for_ai(limit=20):
    """Lightweight sample of products for chat system prompt (id, name, price, category, color only)."""
    products = Product.query.filter_by(is_active=True).limit(limit).all()
    return [
        {'id': p.id, 'name': p.name, 'price': float(p.price), 'category': p.category, 'color': (p.color or 'N/A')}
        for p in products
    ]


def get_products_on_sale(limit=20):
    """Return products that are currently on sale (product-level or global sale), for AI and search."""
    products = Product.query.filter_by(is_active=True).order_by(Product.id).all()
    on_sale = []
    for p in products:
        if len(on_sale) >= limit:
            break
        try:
            if p.get_sale_price() is not None:
                on_sale.append(p)
        except Exception:
            continue
    return [p.to_dict() for p in on_sale], [p.id for p in on_sale]

def search_products_by_criteria(criteria):
    """Search products by various criteria."""
    query = Product.query.filter_by(is_active=True)
    
    if criteria.get('category'):
        query = query.filter_by(category=criteria['category'])
    
    if criteria.get('color'):
        query = query.filter_by(color=criteria['color'])
    
    if criteria.get('size'):
        query = query.filter_by(size=criteria['size'])
    
    if criteria.get('fabric'):
        query = query.filter_by(fabric=criteria['fabric'])
    
    if criteria.get('clothing_type'):
        query = query.filter_by(clothing_type=criteria['clothing_type'])
    
    if criteria.get('occasion'):
        query = query.filter_by(occasion=criteria['occasion'])
    
    if criteria.get('age_group'):
        query = query.filter_by(age_group=criteria['age_group'])
    
    if criteria.get('min_price'):
        query = query.filter(Product.price >= criteria['min_price'])
    
    if criteria.get('max_price'):
        query = query.filter(Product.price <= criteria['max_price'])
    
    if criteria.get('search'):
        search_term = criteria['search']
        query = query.filter(
            or_(
                Product.name.ilike(f'%{search_term}%'),
                Product.description.ilike(f'%{search_term}%'),
                Product.clothing_type.ilike(f'%{search_term}%')
            )
        )
    
    return [p.to_dict() for p in query.limit(50).all()]

def _call_openai(internal, prompt, system_prompt, timeout=60, temperature=0.3):
    api_key = internal.get('api_key')
    model_id = internal.get('model_id') or 'gpt-4o-mini'
    resp = requests.post(
        'https://api.openai.com/v1/chat/completions',
        headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
        json={
            'model': model_id,
            'messages': [
                {'role': 'system', 'content': system_prompt or DEFAULT_SYSTEM_PROMPT},
                {'role': 'user', 'content': prompt},
            ],
            'max_tokens': 1024,
            'temperature': temperature,
        },
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()
    content = (data.get('choices') or [{}])[0].get('message', {}).get('content', '')
    return content or 'No response from AI'


def _call_openai_with_tools(internal, messages, tools_openai, system_prompt, timeout=90, temperature=0.2):
    """
    Call OpenAI chat completions with tools. messages: list of {role, content} or {role, content, tool_calls} / {role, tool_call_id, content}.
    tools_openai: list of {"type": "function", "function": {"name", "description", "parameters"}}.
    Returns (content: str or None, tool_calls: list of {id, name, arguments_str} or empty).
    """
    api_key = internal.get('api_key')
    model_id = internal.get('model_id') or 'gpt-4o-mini'
    payload = {
        'model': model_id,
        'messages': [{'role': 'system', 'content': system_prompt or DEFAULT_SYSTEM_PROMPT}] + messages,
        'max_tokens': 1024,
        'temperature': temperature,
    }
    if tools_openai:
        payload['tools'] = tools_openai
        payload['tool_choice'] = 'auto'
    resp = requests.post(
        'https://api.openai.com/v1/chat/completions',
        headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
        json=payload,
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()
    msg = (data.get('choices') or [{}])[0].get('message', {})
    content = msg.get('content') or ''
    tool_calls = msg.get('tool_calls') or []
    out_tool_calls = []
    for tc in tool_calls:
        tid = tc.get('id') or ''
        fn = tc.get('function') or {}
        name = (fn.get('name') or '').strip()
        args_str = (fn.get('arguments') or '{}').strip()
        if name:
            out_tool_calls.append({'id': tid, 'name': name, 'arguments_str': args_str})
    return (content.strip() or None, out_tool_calls)


def _call_gemini(internal, prompt, system_prompt, timeout=60, temperature=0.3):
    api_key = internal.get('api_key')
    model_id = (internal.get('model_id') or 'gemini-2.0-flash').strip()
    if not model_id.startswith('models/'):
        model_id = f'models/{model_id}' if model_id else 'models/gemini-2.0-flash'
    url = f'https://generativelanguage.googleapis.com/v1beta/{model_id}:generateContent?key={api_key}'
    body = {
        'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
        'systemInstruction': {'parts': [{'text': system_prompt or DEFAULT_SYSTEM_PROMPT}]},
        'generationConfig': {'maxOutputTokens': 1024, 'temperature': temperature},
    }
    last_exc = None
    for attempt in range(3):
        _gemini_throttle()
        try:
            r = requests.post(url, json=body, headers={'Content-Type': 'application/json'}, timeout=timeout)
            r.raise_for_status()
            data = r.json()
            candidates = data.get('candidates') or []
            if not candidates:
                return 'No response from AI'
            parts = candidates[0].get('content', {}).get('parts') or []
            return parts[0].get('text', '') if parts else 'No response from AI'
        except requests.exceptions.HTTPError as e:
            last_exc = e
            if e.response is not None:
                status = e.response.status_code
                try:
                    err_body = (e.response.text or '')[:500]
                except Exception:
                    err_body = ''
                if status == 429:
                    print(f"[Gemini] 429 Rate limit. Response: {err_body}")
                if status in (429, 503) and attempt < 2:
                    # 429 = rate limit (RPM/TPM/RPD). Wait longer so per-minute window can reset.
                    wait = (15, 45)[attempt] if status == 429 else 2 ** (attempt + 1)
                    print(f"Gemini {status}, retrying in {wait}s (attempt {attempt + 1}/3)")
                    time.sleep(wait)
                    continue
            raise
        except requests.exceptions.RequestException as e:
            last_exc = e
            if attempt < 2:
                time.sleep(2 ** (attempt + 1))
                continue
            raise
    if last_exc is not None:
        raise last_exc
    return 'No response from AI'


def _call_anthropic(internal, prompt, system_prompt, timeout=60, temperature=0.3):
    api_key = internal.get('api_key')
    model_id = internal.get('model_id') or 'claude-3-5-sonnet-20241022'
    r = requests.post(
        'https://api.anthropic.com/v1/messages',
        headers={
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
            'Content-Type': 'application/json',
        },
        json={
            'model': model_id,
            'max_tokens': 1024,
            'temperature': temperature,
            'system': system_prompt or DEFAULT_SYSTEM_PROMPT,
            'messages': [{'role': 'user', 'content': prompt}],
        },
        timeout=timeout,
    )
    r.raise_for_status()
    data = r.json()
    content = data.get('content') or []
    for block in content:
        if block.get('type') == 'text':
            return block.get('text', '')
    return 'No response from AI'


def _get_vertex_credentials(api_key):
    """Return (project_id, access_token) from Vertex api_key (service account JSON string or path to JSON file)."""
    import os
    key = (api_key or '').strip()
    if not key:
        return None, None
    info = None
    if key.startswith('{'):
        try:
            info = json.loads(key)
        except json.JSONDecodeError:
            return None, None
    else:
        path = os.path.expanduser(key)
        if os.path.isfile(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    info = json.load(f)
            except Exception:
                return None, None
        else:
            return None, None
    if not info or info.get('type') != 'service_account':
        return None, None
    project_id = info.get('project_id')
    if not project_id:
        return None, None
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request
        credentials = service_account.Credentials.from_service_account_info(info)
        credentials.refresh(Request())
        return project_id, credentials.token
    except Exception as e:
        print(f"Vertex credentials error: {e}")
        return None, None


def _vertex_use_api_key(api_key):
    """True if Vertex key is a simple API key (use aiplatform.googleapis.com?key=); False if service account JSON."""
    if not api_key or not (api_key or '').strip():
        return False
    key = (api_key or '').strip()
    if key.startswith('{'):
        return False
    import os
    if os.path.isfile(os.path.expanduser(key)):
        return False
    return True


def _call_vertex(internal, prompt, system_prompt, timeout=60, temperature=0.3):
    api_key = (internal.get('api_key') or '').strip()
    model_id = (internal.get('model_id') or 'gemini-2.5-flash-lite').strip()
    body = {
        'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
        'systemInstruction': {'parts': [{'text': system_prompt or DEFAULT_SYSTEM_PROMPT}]},
        'generationConfig': {'maxOutputTokens': 1024, 'temperature': temperature},
    }
    if _vertex_use_api_key(api_key):
        # Vertex AI with API key: global endpoint (per Google Cloud quickstart; use GOOGLE_API_KEY or VERTEX_API_KEY)
        url = f'https://aiplatform.googleapis.com/v1/publishers/google/models/{model_id}:generateContent?key={api_key}'
        r = requests.post(url, json=body, headers={'Content-Type': 'application/json'}, timeout=timeout)
        r.raise_for_status()
        data = r.json()
    else:
        # Vertex with service account: project + region endpoint
        region = (internal.get('region') or 'us-central1').strip()
        project_id, token = _get_vertex_credentials(api_key)
        if not project_id or not token:
            raise RuntimeError('Vertex service account JSON must include project_id and private_key (or use an API key).')
        url = (
            f'https://{region}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{region}'
            f'/publishers/google/models/{model_id}:generateContent'
        )
        r = requests.post(
            url,
            json=body,
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            timeout=timeout,
        )
        r.raise_for_status()
        data = r.json()
    candidates = data.get('candidates') or []
    if not candidates:
        return 'No response from AI'
    parts = candidates[0].get('content', {}).get('parts') or []
    return parts[0].get('text', '') if parts else 'No response from AI'


def call_llm(prompt, system_prompt=None, config=None, temperature=0.3):
    """
    Call the LLM for the given config or effective selected provider.
    Supports provider: openai, gemini, anthropic, vertex (API keys or service account from Admin panel).
    temperature: lower = more precise and consistent (default 0.3 for professional responses).
    """
    if system_prompt is None:
        system_prompt = DEFAULT_SYSTEM_PROMPT
    if config is None:
        config = get_effective_provider_config()
    if not config:
        return {
            'content': "I'm your AI shopping assistant! To get AI responses, the admin needs to set an API key in Admin → AI Assistant, test it, then turn the provider on."
        }
    internal = config if isinstance(config, dict) else getattr(config, 'to_internal_dict', lambda: config)()
    provider = (internal.get('provider') or 'openai').strip().lower()
    api_key = internal.get('api_key')

    def _normalize_empty_content(text):
        """Ensure we never return empty or generic 'No response from AI' to the user."""
        if not text or not (text or '').strip():
            return "The assistant didn't return a response this time. Please try again or rephrase your question."
        if (text or '').strip().lower() == 'no response from ai':
            return "The assistant didn't return a response this time. Please try again or rephrase your question."
        return text

    if provider == 'openai':
        if not api_key:
            return {'content': 'OpenAI API key is not set for this model. Add it in Admin → AI Assistant.'}
        try:
            text = _call_openai(internal, prompt, system_prompt, temperature=temperature)
            return {'content': _normalize_empty_content(text)}
        except Exception as e:
            print(f"Error calling OpenAI: {e}")
            return {'content': _normalize_llm_error(e)}

    if provider == 'gemini':
        if not api_key:
            return {'content': 'Gemini API key is not set for this model. Add it in Admin → AI Assistant.'}
        try:
            text = _call_gemini(internal, prompt, system_prompt, temperature=temperature)
            return {'content': _normalize_empty_content(text)}
        except Exception as e:
            print(f"Error calling Gemini: {e}")
            return {'content': _normalize_llm_error(e)}

    if provider == 'anthropic':
        if not api_key:
            return {'content': 'Anthropic API key is not set. Add it in Admin → AI Assistant or set ANTHROPIC_API_KEY in .env.'}
        try:
            text = _call_anthropic(internal, prompt, system_prompt, temperature=temperature)
            return {'content': _normalize_empty_content(text)}
        except Exception as e:
            print(f"Error calling Anthropic: {e}")
            return {'content': _normalize_llm_error(e)}

    if provider == 'vertex':
        if not api_key:
            return {'content': 'Vertex AI credentials are not set. Add a service account JSON key and region in Admin → AI Assistant.'}
        try:
            text = _call_vertex(internal, prompt, system_prompt, temperature=temperature)
            return {'content': _normalize_empty_content(text)}
        except Exception as e:
            print(f"Error calling Vertex: {e}")
            return {'content': _normalize_llm_error(e)}

    return {'content': f'Unknown provider: {provider}. Use openai, gemini, anthropic, or vertex in Admin → AI Assistant.'}


def _run_decision_engine(message, config, history=None, last_filters=None):
    """
    Run the LLM as a decision engine. Returns (action_json_dict, raw_content).
    action_json_dict is always a dict with action, parameters, message, confidence.
    On parse failure returns fallback NONE dict.
    """
    from utils.ai_action_executor import parse_llm_json_response
    prompt_parts = []
    if last_filters and isinstance(last_filters, dict) and any(v is not None and v != '' for v in last_filters.values()):
        prompt_parts.append("Previous search filters from context (use or merge with new request): " + json.dumps(last_filters))
    if history and isinstance(history, list):
        recent = [h for h in history[-6:] if (h.get('role') or '').lower() in ('user', 'customer') and (h.get('content') or '').strip()]
        if recent:
            prompt_parts.append("Recent messages:\n" + "\n".join((h.get('content') or '').strip() for h in recent))
    prompt_parts.append("Current user message: " + (message or '').strip())
    prompt = "\n\n".join(prompt_parts)
    result = call_llm(prompt, system_prompt=DECISION_ENGINE_SYSTEM_PROMPT, config=config, temperature=0.2)
    raw = (result.get('content') or '').strip()
    parsed = parse_llm_json_response(raw)
    if parsed and isinstance(parsed.get('action'), str):
        if not isinstance(parsed.get('parameters'), dict):
            parsed['parameters'] = {}
        if 'message' not in parsed:
            parsed['message'] = ''
        if 'confidence' not in parsed:
            parsed['confidence'] = 0.7
        return parsed, raw
    # Parse failed: LLM may have returned free-form text (e.g. styling advice). Use it as the message
    # so the user sees the actual response instead of a generic fallback.
    # Do NOT use raw if it contains incomplete JSON (e.g. "Sure, I can {\"action\": ") — would expose internals.
    raw_contains_incomplete_json = (
        raw
        and isinstance(raw, str)
        and (
            '{"action"' in raw
            or '"action":' in raw
            or "'action':" in raw
            or raw.strip().startswith('{')
        )
    )
    if raw and not raw_contains_incomplete_json:
        fallback_message = raw.strip()
    else:
        fallback_message = "I didn't quite get that. Could you rephrase or tell me what you'd like to do?"
    fallback = {
        'action': 'NONE',
        'parameters': {},
        'message': fallback_message,
        'confidence': 0.3,
    }
    return fallback, raw


def _normalize_parameters(parameters):
    """Ensure parameters is a dict. If LLM returns a JSON string, parse it."""
    if parameters is None:
        return {}
    if isinstance(parameters, dict):
        return parameters
    if isinstance(parameters, str):
        try:
            parsed = json.loads(parameters)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def _sanitize_response_text(text, action=None):
    """Never send raw JSON to the client. If the message contains JSON, return a safe short message."""
    if not text or not isinstance(text, str):
        return (text or '').strip()
    s = text.strip()
    if '"action":' in s or '"action"' in s or '{"action"' in s or "'action':" in s:
        action_upper = (action or '').strip().upper()
        safe = {
            'ADD_TO_CART': "I've added the item to your cart.",
            'REMOVE_FROM_CART': "Item removed from your cart.",
            'UPDATE_CART_ITEM': "Cart updated.",
            'CLEAR_CART': "Your cart is now empty.",
        'ADD_TO_WISHLIST': "Added to your wishlist.",
        'REMOVE_FROM_WISHLIST': "Removed from your wishlist.",
        'CLEAR_WISHLIST': "Your wishlist is now empty.",
        'ADD_WISHLIST_TO_CART': "I've added wishlist items to your cart.",
        'SEARCH_PRODUCTS': "Here are the results.",
        }
        return safe.get(action_upper, "Done.")
    return s


def _infer_action_when_none(message):
    """
    When the LLM returns NONE or RESPONSE (e.g. rate limit), infer the correct action from the user message.
    Checks clear/destructive intents first, then view/redirect intents. Returns (action_name, parameters) or (None, None).
    """
    if not message or not isinstance(message, str):
        return None, None
    msg = message.strip().lower()
    if len(msg) < 2:
        return None, None

    # --- Clear / destructive intents first (must be before "view cart" etc.) ---
    # CLEAR_CART: "clear my cart", "empty my cart", "empty cart", "clear cart", "remove all from cart"
    if any(x in msg for x in ('clear my cart', 'clear the cart', 'empty my cart', 'empty the cart', 'empty cart',
                               'clear cart', 'remove all from cart', 'delete all from cart', 'empty my basket')):
        return 'CLEAR_CART', {}
    if msg in ('clear cart', 'empty cart'):
        return 'CLEAR_CART', {}
    # CLEAR_WISHLIST: "clear my wishlist", "empty wishlist", "clear wishlist"
    if any(x in msg for x in ('clear my wishlist', 'clear the wishlist', 'empty my wishlist', 'empty the wishlist',
                              'empty wishlist', 'clear wishlist', 'remove all from wishlist')):
        return 'CLEAR_WISHLIST', {}
    if msg in ('clear wishlist', 'empty wishlist'):
        return 'CLEAR_WISHLIST', {}

    # --- View / redirect intents ---
    # VIEW_CART: "show me my cart", "my cart", "view cart", etc. (not "clear")
    if any(x in msg for x in ('my cart', 'show me my cart', 'view cart', 'see my cart', 'see cart', 'open cart', 'go to cart', 'the cart', 'show cart', 'display cart')):
        return 'VIEW_CART', {}
    if msg in ('cart', 'show cart', 'view my cart'):
        return 'VIEW_CART', {}
    # VIEW_WISHLIST
    if any(x in msg for x in ('my wishlist', 'view wishlist', 'see wishlist', 'see my wishlist', 'open wishlist', 'saved items', 'my saved', 'favorites', 'my favorites')):
        return 'VIEW_WISHLIST', {}
    if msg in ('wishlist', 'show wishlist'):
        return 'VIEW_WISHLIST', {}
    # VIEW_CHECKOUT
    if any(x in msg for x in ('checkout', 'go to checkout', 'place order', 'pay now', 'proceed to checkout')):
        return 'VIEW_CHECKOUT', {}
    # VIEW_PRODUCTS
    if any(x in msg for x in ('view products', 'products page', 'go to products', 'show products page', 'all products')):
        return 'VIEW_PRODUCTS', {}
    if msg in ('products', 'show products') and 'search' not in msg and 'find' not in msg:
        return 'VIEW_PRODUCTS', {}
    # VIEW_HOME
    if any(x in msg for x in ('go home', 'home page', 'main page', 'take me home', 'back to home')):
        return 'VIEW_HOME', {}
    if msg in ('home', 'show home'):
        return 'VIEW_HOME', {}

    return None, None


def _infer_redirect_action(message):
    """When the LLM returns NONE or fails (e.g. rate limit), infer a redirect action from the user message. Returns action name or None."""
    action, _ = _infer_action_when_none(message)
    if action and action.startswith('VIEW_'):
        return action
    return None


def _redirect_friendly_message(action_name):
    """Short user-facing message when we inferred a redirect (e.g. after rate limit)."""
    return {
        'VIEW_CART': "Taking you to your cart.",
        'VIEW_WISHLIST': "Taking you to your wishlist.",
        'VIEW_CHECKOUT': "Taking you to checkout.",
        'VIEW_PRODUCTS': "Taking you to products.",
        'VIEW_HOME': "Taking you to the home page.",
    }.get((action_name or '').upper(), None)


def _message_looks_like_product_search(message):
    """True if the user message suggests they want to search/browse products (so we run vector search even when LLM returns Response/NONE)."""
    if not message or not isinstance(message, str):
        return False
    msg = message.strip().lower()
    if len(msg) < 2:
        return False
    # Never treat redirect intents as product search: cart, wishlist, checkout, home, "view products" (navigation)
    # Also exclude clear/destructive intents (clear cart, clear wishlist) so we don't run product search for them
    if _infer_redirect_action(message) is not None:
        return False
    action_only, _ = _infer_action_when_none(message)
    if action_only is not None:
        return False
    # Explicit product-search phrases
    triggers = [
        'find me', 'find ', 'look for', 'looking for',
        'do you have', 'do we have', 'any ', 'get me', 'i want ', 'i need ',
        'search for', 'search ', 'browse', 'what ', 'which ', 'recommend',
        'on sale', 'for sale', 'discount', 'under $', 'under £', 'less than',
        'over $', 'over £', 'more than', 'between $', 'price',
        'shirt', 'dress', 'pants', 'jeans', 'jacket', 'shoes', 'sweater',
        't-shirt', 'blouse', 'skirt', 'coat', 'clothes', 'clothing', 'items',
        'black ', 'blue ', 'red ', 'white ', 'green ', 'gray ', 'grey ',
        'women', 'men', 'kids', 'women\'s', 'men\'s', 'elegant', 'casual',
    ]
    # "show me" / "show " only count when not followed by cart/wishlist/checkout (already excluded above)
    for t in triggers:
        if t in msg:
            return True
    if 'show me' in msg or 'show ' in msg:
        return True
    # Short queries that look like product keywords (e.g. "black dress", "blue shirts")
    words = [w for w in msg.split() if len(w) > 1]
    if 2 <= len(words) <= 8 and not msg.startswith(('how', 'why', 'when', 'where', 'who', 'can you explain', 'what is', 'what are')):
        if any(w in msg for w in ['clothes', 'clothing', 'dress', 'shirt', 'pants', 'sale', 'item', 'product', 'women', 'men', 'kids']):
            return True
        if any(c in msg for c in ['black', 'blue', 'red', 'white', 'navy', 'gray', 'grey', 'green', 'yellow', 'pink', 'brown', 'beige']):
            return True
    return False


def test_provider_latency(provider, config_override=None):
    """Test one provider; return (latency_ms, error_message). error_message is None on success.
    If config_override is provided (dict with api_key and optionally model_id), use it for this test only."""
    if provider not in FIXED_PROVIDERS:
        return None, 'Invalid provider'
    cfg = config_override
    if not cfg:
        cfg = get_config_for_provider(provider)
    else:
        # Ensure provider and other fields exist; merge with DB config for model_id etc.
        base = get_config_for_provider(provider)
        base = dict(base)
        base['api_key'] = config_override.get('api_key') or base.get('api_key')
        if config_override.get('model_id') is not None:
            base['model_id'] = config_override.get('model_id')
        base['provider'] = provider
        cfg = base
    if not cfg.get('api_key'):
        return None, 'No API key set. Paste a key and click Test, or Save first then Test.'
    start = time.time()
    result = call_llm('Say exactly: OK', system_prompt='Reply with only the two letters: OK', config=cfg)
    elapsed_ms = int((time.time() - start) * 1000)
    content = (result.get('content') or '').strip()
    content_upper = content.upper()
    # Success: model replied with something that looks like "OK" (and is not an error message)
    if content and len(content) <= 20 and content_upper == 'OK':
        return elapsed_ms, None
    if content and len(content) <= 50 and 'OK' in content_upper and 'ERROR' not in content_upper and 'NOT SET' not in content_upper and 'NOT FOUND' not in content_upper:
        return elapsed_ms, None
    # Any other content is treated as error (e.g. "Invalid API key", "Rate limited")
    return None, content or 'Request failed'


def call_llm_vision(config, prompt, image_base64, system_prompt=None, media_type='image/jpeg'):
    """Call the LLM with an image (for product image analysis). Uses config's provider; falls back to text-only if not supported."""
    if config is None:
        config = get_active_ai_config()
    if not config:
        return None
    internal = config.to_internal_dict()
    provider = (internal.get('provider') or 'openai').strip().lower()
    api_key = internal.get('api_key')
    model_id = internal.get('model_id')

    if provider == 'openai' and api_key:
        try:
            content = [{'type': 'text', 'text': prompt}]
            content.append({'type': 'image_url', 'image_url': {'url': f'data:{media_type};base64,{image_base64}'}})
            r = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
                json={
                    'model': model_id or 'gpt-4o-mini',
                    'messages': [
                        {'role': 'system', 'content': system_prompt or 'You are a fashion expert analyzing clothing from images.'},
                        {'role': 'user', 'content': content},
                    ],
                    'max_tokens': 2048,
                },
                timeout=90,
            )
            r.raise_for_status()
            data = r.json()
            text = (data.get('choices') or [{}])[0].get('message', {}).get('content', '')
            return text
        except Exception as e:
            print(f"Error calling OpenAI vision: {e}")
            return None

    if provider == 'gemini' and api_key:
        try:
            mid = (model_id or 'gemini-2.0-flash').strip()
            if not mid.startswith('models/'):
                mid = f'models/{mid}'
            url = f'https://generativelanguage.googleapis.com/v1beta/{mid}:generateContent?key={api_key}'
            body = {
                'contents': [{
                    'parts': [
                        {'text': prompt},
                        {'inline_data': {'mime_type': media_type, 'data': image_base64}},
                    ]
                }],
                'generationConfig': {'maxOutputTokens': 2048},
            }
            if system_prompt:
                body['systemInstruction'] = {'parts': [{'text': system_prompt}]}
            last_exc = None
            for attempt in range(3):
                _gemini_throttle()
                try:
                    r = requests.post(url, json=body, headers={'Content-Type': 'application/json'}, timeout=90)
                    r.raise_for_status()
                    data = r.json()
                    candidates = data.get('candidates') or []
                    if not candidates:
                        return None
                    parts = candidates[0].get('content', {}).get('parts') or []
                    return parts[0].get('text', '') if parts else None
                except requests.exceptions.HTTPError as e:
                    last_exc = e
                    if e.response is not None:
                        status = e.response.status_code
                        if status == 429:
                            try:
                                print(f"[Gemini vision] 429 Rate limit. Response: {(e.response.text or '')[:500]}")
                            except Exception:
                                pass
                        if status in (429, 503) and attempt < 2:
                            wait = (15, 45)[attempt] if status == 429 else 2 ** (attempt + 1)
                            print(f"Gemini vision {status}, retrying in {wait}s (attempt {attempt + 1}/3)")
                            time.sleep(wait)
                            continue
                    break
                except requests.exceptions.RequestException as e:
                    last_exc = e
                    if attempt < 2:
                        time.sleep(2 ** (attempt + 1))
                        continue
                    break
            if last_exc is not None:
                print(f"Error calling Gemini vision: {last_exc}")
            return None
        except Exception as e:
            print(f"Error calling Gemini vision: {e}")
            return None

    if provider == 'anthropic' and api_key:
        try:
            r = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers={'x-api-key': api_key, 'anthropic-version': '2023-06-01', 'Content-Type': 'application/json'},
                json={
                    'model': model_id or 'claude-3-5-sonnet-20241022',
                    'max_tokens': 2048,
                    'system': system_prompt or 'You are a fashion expert analyzing clothing from images.',
                    'messages': [{
                        'role': 'user',
                        'content': [
                            {'type': 'image', 'source': {'type': 'base64', 'media_type': media_type, 'data': image_base64}},
                            {'type': 'text', 'text': prompt},
                        ],
                    }],
                },
                timeout=90,
            )
            r.raise_for_status()
            data = r.json()
            for block in (data.get('content') or []):
                if block.get('type') == 'text':
                    return block.get('text', '')
            return None
        except Exception as e:
            print(f"Error calling Anthropic vision: {e}")
            return None

    if provider == 'vertex' and api_key:
        try:
            key_stripped = (api_key or '').strip()
            mid = (model_id or 'gemini-2.5-flash-lite').strip()
            body = {
                'contents': [{
                    'parts': [
                        {'text': prompt},
                        {'inline_data': {'mime_type': media_type, 'data': image_base64}},
                    ]
                }],
                'generationConfig': {'maxOutputTokens': 2048},
            }
            if system_prompt:
                body['systemInstruction'] = {'parts': [{'text': system_prompt}]}
            if _vertex_use_api_key(key_stripped):
                url = f'https://aiplatform.googleapis.com/v1/publishers/google/models/{mid}:generateContent?key={key_stripped}'
                r = requests.post(url, json=body, headers={'Content-Type': 'application/json'}, timeout=90)
            else:
                project_id, token = _get_vertex_credentials(key_stripped)
                if not project_id or not token:
                    return None
                region = (internal.get('region') or 'us-central1').strip()
                url = (
                    f'https://{region}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{region}'
                    f'/publishers/google/models/{mid}:generateContent'
                )
                r = requests.post(
                    url,
                    json=body,
                    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
                    timeout=90,
                )
            r.raise_for_status()
            data = r.json()
            candidates = data.get('candidates') or []
            if not candidates:
                return None
            parts = candidates[0].get('content', {}).get('parts') or []
            return parts[0].get('text', '') if parts else None
        except Exception as e:
            print(f"Error calling Vertex vision: {e}")
            return None

    return None


@ai_agent_bp.route('/models', methods=['GET'])
def list_ai_models():
    """Return selected provider for display (auto or openai/gemini/anthropic/vertex). No auth required."""
    try:
        return jsonify({
            'success': True,
            'selected_provider': get_selected_provider(),
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Context for the assistant: website policies and pages (for accurate answers)
ASSISTANT_WEBSITE_CONTEXT = """
Website information (use for accurate answers; do not invent):
- Shipping: Orders placed before 12:00 PM EST ship same business day; after 12:00 PM or weekends ship next business day. Standard shipping 5–7 business days; expedited and express options available. Domestic (USA) and international shipping.
- Returns: 30 days from delivery date to start a return. Items must be unworn, unwashed, original condition with tags. Refund after inspection. Exchanges subject to availability. Log in → Order History → select order → choose items and reason to start a return.
- About: InsightShop offers timeless, quality clothing (men, women, kids). Mission: quality first, transparency, customer focus, timeless style.
- Contact: Users can send a message at /contact with name, email, optional order number, and message.
- Policies and pages: /about (Our Story), /shipping (Shipping Information), /returns (Returns & Refunds), /contact (Contact Us).
"""


def get_assistant_user_context(user):
    """Build a short context string about the current user (wishlist, cart, recent orders) for the AI. Returns None if no user."""
    if not user:
        return None
    try:
        from models.wishlist import WishlistItem
        from models.cart import CartItem
        from models.order import Order
        parts = []
        wishlist_count = WishlistItem.query.filter_by(user_id=user.id).count()
        if wishlist_count > 0:
            parts.append(f"{wishlist_count} item(s) in wishlist")
        cart_count = CartItem.query.filter_by(user_id=user.id).count()
        if cart_count > 0:
            parts.append(f"{cart_count} item(s) in cart")
        orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).limit(5).all()
        if orders:
            last = orders[0]
            parts.append(f"recent orders: {len(orders)} (last: #{getattr(last, 'order_number', last.id)} {last.status})")
        if not parts:
            return None
        return "Current user context: " + "; ".join(parts) + "."
    except Exception:
        return None


TOOLS_SYSTEM_PROMPT = """You are a professional, friendly shopping assistant for InsightShop. Respond naturally and conversationally. Be helpful, accurate, and aligned with the brand (quality, transparency, customer focus).

Context awareness:
- Use the provided website information to answer questions about shipping, returns, policies, and pages. Do not invent policy details.
- Use the provided user context (when present) to personalize: reference their wishlist, cart, or order history when relevant.
- When suggesting products, you can reference what they have saved or in cart to make relevant recommendations.

Understanding intent:
- If the user's request is unclear or incomplete, ask one or two short follow-up questions to clarify (e.g. which order, which product, size or style preference).
- For critical or irreversible actions (e.g. clear cart, remove from wishlist), confirm briefly before executing (e.g. "Should I remove that from your wishlist?").
- Use the full conversation history: do not ask again for something the user already said; only ask for what is still missing.

Actions:
- You may only perform user-level actions (search, cart, wishlist, order status, track, compare, review, checkout). Do not perform or claim admin-only actions.
- When the user asks you to do something, use the appropriate tool, then reply in natural language with a clear, concise outcome (e.g. "I've added that to your wishlist.").
- SEARCH REFINEMENT: When the user refines a previous product search (e.g. "the blue ones", "only blue", "show me the ones that are blue", "are any of them blue?"), call search_products with the PREVIOUS filters (e.g. on_sale) preserved and ADD the new filter (e.g. color: "blue"). Do not replace on_sale with false or drop other filters unless the user clearly asks to remove them. Extract color, size, or max_price from the user's message and pass them as filter parameters.
- SEARCH: When the user asks to find/show products (e.g. "women's clothes blue under $80", "show me blue jackets"), ALWAYS call search_products with structured filters extracted from the message: category (men/women/kids), color, max_price, min_price, size, fabric, season, clothing_category, on_sale. Do not pass only a raw "query" string when you can extract these filters—e.g. "blue and under 80$" must become color: "blue", max_price: 80.
- CART: Never say you have added or removed something from the cart unless you actually called the add_item or remove_item tool in this conversation turn and received a success response. If the user asks to add/remove from cart, you MUST call the add_item or remove_item tool; do not reply with "I've added X to your cart" without having called the tool. If you did not call the tool, say instead that you will add it when they confirm, or ask them to say "add [product] to my cart" so you can use the tool.
- If you cannot do something or information is unavailable, say so clearly and suggest alternatives when appropriate.
- Never invent capabilities or make up product or order details; if you don't have the data, say so.

For ADMIN product flows (only when you have admin tools), follow these rules:

1) CREATE A NEW PRODUCT: Do not call admin_product_create with one message. Instead, ask the admin for the required information step by step, like a form. Use the conversation history to see what they have already given you.
   - Required: product name, then price, then category (Men, Women, or Kids). Ask for ONLY the next missing required field—if they gave name already, ask for price; if they gave price already, ask for category.
   - After you have name, price, and category, you may optionally ask for description, stock quantity, color, size, fabric, clothing type, or season. Again, only ask for fields not yet provided.
   When the admin has given you at least name, price, and category, call admin_product_prepare_create with ALL the fields you collected from the ENTIRE conversation (re-read the history so you do not omit any). Then write a friendly response, e.g. "I've filled in the product form with the details you gave me. You're being taken to the Add Product page—review the form and click Create Product to save."

2) EDIT A PRODUCT: First ask which product they want to edit (product ID or name). Then ask which field(s) they want to change and the new value(s). Use the history: if they already gave the product ID or the field to edit, do not ask again. When you have product_id and at least one field to update, call admin_product_prepare_edit. Then write a short response.

3) DELETE A PRODUCT: Ask for the product ID (or name). Then ask for confirmation. Only when the user clearly confirms, call admin_product_delete. Then write a clear response. If they do not confirm, say you have cancelled the deletion.

For all other admin tasks (orders, sales, carts, reviews), use the corresponding tools and then write a short response for the admin to see."""


@ai_agent_bp.route('/chat-with-tools', methods=['POST'])
def chat_with_tools():
    '''Decision-engine chat (authenticated): same as /chat but requires auth. Every message produces structured JSON; backend executes actions. Logs to docs/ai_debug.csv.'''
    try:
        from utils.ai_action_executor import execute_action
        user = get_current_user_optional()
        data = request.get_json() or {}
        message = (data.get('message') or '').strip()
        if not user:
            append_ai_debug_log(message or '', None, None, 'Authorization required')
            return jsonify({
                'success': False,
                'error': 'Authorization required',
                'message_json': build_message_json(False, 'NONE', 'Authorization required', '', 'denied', confidence=0),
            }), 401
        if not message:
            append_ai_debug_log('', None, None, 'Message is required')
            return jsonify({
                'success': False,
                'error': 'Message is required',
                'message_json': build_message_json(False, 'NONE', 'Message is required', '', 'error', confidence=0),
            }), 400
        config = get_effective_provider_config()
        if not config:
            append_ai_debug_log(message, None, None, 'No AI provider available.')
            return jsonify({
                'success': False,
                'error': 'No AI provider available. Set an API key in Admin → AI Assistant.',
                'message_json': build_message_json(False, 'NONE', 'No AI provider available', '', 'error', confidence=0),
            }), 503
        internal = config if isinstance(config, dict) else getattr(config, 'to_internal_dict', lambda: config)()
        provider = (internal.get('provider') or 'openai').strip().lower()
        history = data.get('history') or data.get('conversation_history') or []
        last_filters = data.get('last_filters') or data.get('filters') or {}
        action_json, _ = _run_decision_engine(message, config, history=history, last_filters=last_filters)
        action = (action_json.get('action') or 'NONE').strip()
        parameters = _normalize_parameters(action_json.get('parameters'))
        msg_text = (action_json.get('message') or '').strip()
        # When LLM returns NONE (e.g. rate limit) or RESPONSE, infer the correct action from the user message
        inferred_redirect = None
        if action.upper() in ('RESPONSE', 'NONE'):
            inferred_action, inferred_params = _infer_action_when_none(message)
            if inferred_action:
                action = inferred_action
                parameters = inferred_params if inferred_params is not None else {}
                if action.startswith('VIEW_'):
                    inferred_redirect = action
        confidence = action_json.get('confidence')
        try:
            confidence = max(0.0, min(1.0, float(confidence)))
        except (TypeError, ValueError):
            confidence = 0.5
        response_text = _sanitize_response_text(msg_text, action)
        suggested_products = []
        redirect_path = None
        exec_error = None
        ran_fallback_search = False
        if action.upper() not in ('RESPONSE', 'NONE'):
            result = execute_action(
                action,
                parameters,
                current_user=user,
                flask_request=request,
            )
            if result.get('message_override'):
                response_text = result['message_override']
            if not result.get('success'):
                exec_error = result.get('error') or 'Action failed'
                response_text = exec_error
            # SEARCH_PRODUCTS: always take products from result so search results are never lost
            if action.upper() == 'SEARCH_PRODUCTS' and result.get('data') is not None:
                raw_list = (result.get('data') or {}).get('products')
                suggested_products = list(raw_list) if raw_list is not None else []
            elif result.get('data') and isinstance(result['data'], dict) and result['data'].get('products'):
                suggested_products = result['data']['products']
            if result.get('redirect_path'):
                redirect_path = result['redirect_path']
        else:
            response_text = _sanitize_response_text(response_text, action)
            if last_filters and isinstance(last_filters, dict) and any(v is not None and v != '' for v in last_filters.values()):
                result = execute_action(
                    'SEARCH_PRODUCTS',
                    last_filters,
                    current_user=user,
                    flask_request=request,
                )
                if result.get('success') and result.get('data') and isinstance(result['data'], dict) and result['data'].get('products'):
                    suggested_products = result['data']['products']
            if not suggested_products and _message_looks_like_product_search(message):
                ran_fallback_search = True
                result = execute_action(
                    'SEARCH_PRODUCTS',
                    {'search': message},
                    current_user=user,
                    flask_request=request,
                )
                if result.get('success') and result.get('data') and isinstance(result['data'], dict):
                    products_from_fallback = result['data'].get('products') or []
                    suggested_products = products_from_fallback
                    if not products_from_fallback:
                        response_text = "I couldn't find any products matching that. Try different keywords or filters."
        if inferred_redirect and redirect_path and not exec_error:
            friendly = _redirect_friendly_message(inferred_redirect)
            if friendly:
                response_text = friendly
        action_json_for_log = {'action': action, 'parameters': parameters, 'message': msg_text, 'confidence': confidence}
        append_ai_debug_log(message, response_text, action_json_for_log, exec_error)
        mj = build_message_json(
            True,
            action,
            exec_error,
            response_text,
            'error' if exec_error else 'success',
            filters=parameters,
            confidence=confidence,
        )
        mj['redirect_path'] = redirect_path
        mj['suggested_product_ids'] = [p.get('id') for p in suggested_products if p.get('id')]
        response_action = None
        structured_response = None
        # When executor returned products (search ran), always send product_preview and search_results
        if suggested_products and not exec_error:
            response_action = 'search_results'
            structured_response = {
                'type': 'product_preview',
                'title': 'Search results',
                'products': suggested_products,
                'preview_limit': 5,
                'show_view_all': True,
            }
        elif (action.upper() == 'SEARCH_PRODUCTS' or ran_fallback_search) and not exec_error:
            response_action = 'search_results'
            structured_response = {
                'type': 'no_results',
                'message': 'No products found matching your criteria.',
            }
        elif action.upper() in ('ADD_TO_CART', 'REMOVE_FROM_CART', 'UPDATE_CART_ITEM', 'CLEAR_CART', 'ADD_WISHLIST_TO_CART') and not exec_error:
            response_action = 'agent_executed'
        return jsonify({
            'success': True,
            'response': response_text,
            'selected_provider': provider,
            'action': response_action,
            'structured_response': structured_response,
            'suggested_products': list(suggested_products) if suggested_products else [],
            'suggested_product_ids': mj['suggested_product_ids'],
            'redirect_path': redirect_path,
            'message_json': mj,
        }), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        data = request.get_json() or {}
        message = (data.get('message') or '').strip()
        append_ai_debug_log(message, None, None, str(e))
        return jsonify({
            'success': False,
            'error': str(e),
            'message_json': build_message_json(False, 'NONE', str(e), '', 'error', confidence=0),
        }), 500


@ai_agent_bp.route('/chat', methods=['POST'])
def chat():
    '''Decision-engine chat: every message produces structured JSON (action, parameters, message, confidence). Backend executes actions and returns response + optional products/redirect. Logs every exchange to docs/ai_debug.csv.'''
    try:
        from utils.ai_action_executor import execute_action
        data = request.get_json() or {}
        message = (data.get('message') or '').strip()
        if not message:
            append_ai_debug_log('', None, None, 'Message is required')
            return jsonify({
                'error': 'Message is required',
                'message_json': build_message_json(False, 'NONE', 'Message is required', '', 'error', confidence=0),
            }), 400
        ai_config = get_active_ai_config()
        selected_provider = get_selected_provider()
        if not ai_config:
            append_ai_debug_log(message, None, None, 'No AI provider is available.')
            return jsonify({
                'error': "No AI provider is available. Set an API key in Admin → AI Assistant.",
                'selected_provider': selected_provider,
                'message_json': build_message_json(False, 'NONE', 'No AI provider available', '', 'error', confidence=0),
            }), 503
        config = ai_config.to_internal_dict() if hasattr(ai_config, 'to_internal_dict') else ai_config
        history = data.get('history') or data.get('conversation_history') or []
        last_filters = data.get('last_filters') or data.get('filters') or {}
        action_json, raw_content = _run_decision_engine(message, config, history=history, last_filters=last_filters)
        action = (action_json.get('action') or 'NONE').strip()
        parameters = _normalize_parameters(action_json.get('parameters'))
        msg_text = (action_json.get('message') or '').strip()
        # When LLM returns NONE (e.g. rate limit) or RESPONSE, infer the correct action from the user message
        inferred_redirect = None
        if action.upper() in ('RESPONSE', 'NONE'):
            inferred_action, inferred_params = _infer_action_when_none(message)
            if inferred_action:
                action = inferred_action
                parameters = inferred_params if inferred_params is not None else {}
                if action.startswith('VIEW_'):
                    inferred_redirect = action
        confidence = action_json.get('confidence')
        try:
            confidence = max(0.0, min(1.0, float(confidence)))
        except (TypeError, ValueError):
            confidence = 0.5
        response_text = _sanitize_response_text(msg_text, action)
        suggested_products = []
        redirect_path = None
        exec_error = None
        ran_fallback_search = False
        if action.upper() not in ('RESPONSE', 'NONE'):
            result = execute_action(
                action,
                parameters,
                current_user=get_current_user_optional(),
                flask_request=request,
            )
            if result.get('message_override'):
                response_text = result['message_override']
            if not result.get('success'):
                exec_error = result.get('error') or 'Action failed'
                response_text = exec_error
            # SEARCH_PRODUCTS: always take products from result so search results are never lost
            if action.upper() == 'SEARCH_PRODUCTS' and result.get('data') is not None:
                raw_list = (result.get('data') or {}).get('products')
                suggested_products = list(raw_list) if raw_list is not None else []
            elif result.get('data') and isinstance(result['data'], dict) and result['data'].get('products'):
                suggested_products = result['data']['products']
            if result.get('redirect_path'):
                redirect_path = result['redirect_path']
        else:
            response_text = _sanitize_response_text(response_text, action)
            # Fallback: LLM returned Response/NONE but we have last_filters — run search so we attach products
            if last_filters and isinstance(last_filters, dict) and any(v is not None and v != '' for v in last_filters.values()):
                result = execute_action(
                    'SEARCH_PRODUCTS',
                    last_filters,
                    current_user=get_current_user_optional(),
                    flask_request=request,
                )
                if result.get('success') and result.get('data') and isinstance(result['data'], dict) and result['data'].get('products'):
                    suggested_products = result['data']['products']
            # Fallback: message looks like product search but LLM didn't return SEARCH_PRODUCTS — use vector search with raw message
            if not suggested_products and _message_looks_like_product_search(message):
                ran_fallback_search = True
                result = execute_action(
                    'SEARCH_PRODUCTS',
                    {'search': message},
                    current_user=get_current_user_optional(),
                    flask_request=request,
                )
                if result.get('success') and result.get('data') and isinstance(result['data'], dict):
                    products_from_fallback = result['data'].get('products') or []
                    suggested_products = products_from_fallback
                    if not products_from_fallback:
                        response_text = "I couldn't find any products matching that. Try different keywords or filters."
        if inferred_redirect and redirect_path and not exec_error:
            friendly = _redirect_friendly_message(inferred_redirect)
            if friendly:
                response_text = friendly
        action_json_for_log = {'action': action, 'parameters': parameters, 'message': msg_text, 'confidence': confidence}
        append_ai_debug_log(message, response_text, action_json_for_log, exec_error)
        mj = build_message_json(
            True,
            action,
            exec_error,
            response_text,
            'error' if exec_error else 'success',
            filters=parameters,
            confidence=confidence,
        )
        mj['redirect_path'] = redirect_path
        mj['suggested_product_ids'] = [p.get('id') for p in suggested_products if p.get('id')]
        response_action = None
        structured_response = None
        # When executor returned products (search ran), always send product_preview and search_results
        if suggested_products and not exec_error:
            response_action = 'search_results'
            structured_response = {
                'type': 'product_preview',
                'title': 'Search results',
                'products': suggested_products,
                'preview_limit': 5,
                'show_view_all': True,
            }
        elif (action.upper() == 'SEARCH_PRODUCTS' or ran_fallback_search) and not exec_error:
            response_action = 'search_results'
            structured_response = {
                'type': 'no_results',
                'message': 'No products found matching your criteria.',
            }
        elif action.upper() in ('ADD_TO_CART', 'REMOVE_FROM_CART', 'UPDATE_CART_ITEM', 'CLEAR_CART', 'ADD_WISHLIST_TO_CART') and not exec_error:
            response_action = 'agent_executed'
        return jsonify({
            'response': response_text,
            'suggested_products': list(suggested_products) if suggested_products else [],
            'suggested_product_ids': mj['suggested_product_ids'],
            'redirect_path': redirect_path,
            'selected_provider': selected_provider,
            'action': response_action,
            'structured_response': structured_response,
            'message_json': mj,
        }), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        msg = (request.get_json() or {}).get('message', '')
        append_ai_debug_log(msg, None, None, str(e))
        return jsonify({
            'error': str(e),
            'message_json': build_message_json(False, 'NONE', str(e), '', 'error', confidence=0),
        }), 500


@ai_agent_bp.route('/search', methods=['POST'])
def ai_search():
    """AI-powered product search."""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Use vector search
        product_ids = search_products_vector(query, n_results=20)
        
        if product_ids:
            products = Product.query.filter(Product.id.in_(product_ids)).all()
            products_dict = {p.id: p.to_dict() for p in products}
            # Maintain order from vector search
            ordered_products = [products_dict[pid] for pid in product_ids if pid in products_dict]
        else:
            # Fallback to regular search
            products = Product.query.filter(
                or_(
                    Product.name.ilike(f'%{query}%'),
                    Product.description.ilike(f'%{query}%')
                )
            ).filter_by(is_active=True).limit(20).all()
            ordered_products = [p.to_dict() for p in products]
        
        return jsonify({
            'products': ordered_products,
            'count': len(ordered_products)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_agent_bp.route('/filter', methods=['POST'])
def ai_filter():
    """AI-powered product filtering."""
    try:
        data = request.get_json()
        criteria = data.get('criteria', {})
        
        products = search_products_by_criteria(criteria)
        
        return jsonify({
            'products': products,
            'count': len(products)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_agent_bp.route('/compare', methods=['POST'])
def compare_products():
    """Compare multiple products."""
    try:
        data = request.get_json()
        product_ids = data.get('product_ids', [])
        
        if not product_ids or len(product_ids) < 2:
            return jsonify({'error': 'At least 2 product IDs are required'}), 400
        
        products = Product.query.filter(Product.id.in_(product_ids)).filter_by(is_active=True).all()
        
        if len(products) != len(product_ids):
            return jsonify({'error': 'Some products not found'}), 404
        
        # Convert to dict while session is active
        products_dict = [p.to_dict() for p in products]
        
        return jsonify({
            'products': products_dict,
            'comparison': {
                'price_range': {
                    'min': float(min(p.price for p in products)),
                    'max': float(max(p.price for p in products))
                },
                'categories': list(set(p.category for p in products)),
                'colors': list(set(p.color for p in products if p.color))
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_agent_bp.route('/summarize', methods=['POST'])
def summarize_text():
    """Summarize text for text-to-speech when it's too long."""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        print(f"[SUMMARIZE] Summarizing text ({len(text)} characters)")
        
        # Create a summarization prompt
        summarize_prompt = f"""Please summarize the following text in a concise, natural way that's perfect for speaking aloud. 
Keep the key information and main points, but make it shorter and more conversational. 
Aim for about 50-80 words. Keep the friendly, excited tone if present.

Text to summarize:
{text}

Summary:"""
        
        # Use a simpler system prompt for summarization
        system_prompt = """You are a helpful assistant that creates concise, natural summaries perfect for text-to-speech. 
Keep summaries conversational and maintain the original tone and key information."""
        
        # Call LLM for summarization (use first active config)
        result = call_llm(summarize_prompt, system_prompt, config=get_active_ai_config())
        summary = result.get('content', text)  # Fallback to original if summarization fails
        
        print(f"[SUMMARIZE] Summary created ({len(summary)} characters)")
        
        return jsonify({
            'summary': summary,
            'original_length': len(text),
            'summary_length': len(summary)
        })
        
    except Exception as e:
        print(f"[SUMMARIZE] Error: {str(e)}")
        # Return original text if summarization fails
        return jsonify({
            'summary': text,
            'original_length': len(text),
            'summary_length': len(text),
            'error': str(e)
        }), 200  # Return 200 so frontend can still use the original text

@ai_agent_bp.route('/text-to-speech/status', methods=['GET'])
def tts_status():
    """Check if AWS Polly is available and configured."""
    try:
        # Safely get Config values with defaults
        aws_region = None
        has_credentials = False
        try:
            aws_region = Config.AWS_REGION if hasattr(Config, 'AWS_REGION') and Config.AWS_REGION else None
            has_credentials = bool(
                hasattr(Config, 'AWS_ACCESS_KEY_ID') and Config.AWS_ACCESS_KEY_ID and
                hasattr(Config, 'AWS_SECRET_ACCESS_KEY') and Config.AWS_SECRET_ACCESS_KEY
            )
        except Exception as config_error:
            print(f"Warning: Error accessing Config: {config_error}")
        
        # Check if AWS CLI credentials are available (default credential chain)
        has_aws_cli_credentials = False
        if not has_credentials:
            try:
                # Try to get credentials from default chain
                session = boto3.Session()
                credentials = session.get_credentials()
                if credentials:
                    has_aws_cli_credentials = True
            except:
                pass
        
        status = {
            'available': polly_available,
            'client_initialized': polly_client is not None,
            'aws_region': aws_region,
            'has_credentials': has_credentials,
            'has_aws_cli_credentials': has_aws_cli_credentials
        }
        
        if polly_client and polly_available:
            try:
                # Test by getting available voices (limit to first 5 for response size)
                voices_response = polly_client.describe_voices(LanguageCode='en-US')
                voices_list = voices_response.get('Voices', [])[:5]  # Limit to first 5
                status['test_successful'] = True
                status['available_voices'] = [v['Id'] for v in voices_list]
            except Exception as e:
                status['test_successful'] = False
                status['test_error'] = str(e)
        
        return jsonify(status), 200
    except Exception as e:
        print(f"Error in tts_status: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'available': False}), 500

@ai_agent_bp.route('/text-to-speech', methods=['POST'])
def text_to_speech():
    """Convert text to speech using AWS Polly with natural, excited voices."""
    import re
    import html
    import base64
    import traceback
    
    print("=" * 80)
    print("[AWS POLLY] Text-to-Speech Request Received")
    print("=" * 80)
    
    try:
        data = request.get_json()
        text = data.get('text', '')
        voice_gender = data.get('voice_gender', 'woman')  # 'woman' or 'man'
        voice_id_param = data.get('voice_id', None)  # Optional specific voice ID
        speech_speed = data.get('speech_speed', 1.0)  # Speech speed multiplier (0.5 to 2.0)
        
        # Validate speech speed
        speech_speed = max(0.5, min(2.0, float(speech_speed)))
        
        print(f"[AWS POLLY] Request Details:")
        print(f"  - Text length: {len(text)} characters")
        print(f"  - Voice gender: {voice_gender}")
        print(f"  - Voice ID: {voice_id_param}")
        print(f"  - Speech speed: {speech_speed}x")
        print(f"  - Text preview: {text[:100]}..." if len(text) > 100 else f"  - Text: {text}")
        
        if not text:
            print("[AWS POLLY] ❌ ERROR: No text provided")
            return jsonify({'error': 'Text is required'}), 400
        
        print(f"[AWS POLLY] Checking Polly availability...")
        print(f"  - polly_client exists: {polly_client is not None}")
        print(f"  - polly_available: {polly_available}")
        print(f"  - AWS_ACCESS_KEY_ID configured: {bool(Config.AWS_ACCESS_KEY_ID)}")
        print(f"  - AWS_SECRET_ACCESS_KEY configured: {bool(Config.AWS_SECRET_ACCESS_KEY)}")
        print(f"  - AWS_REGION: {Config.AWS_REGION}")
        
        if not polly_client or not polly_available:
            error_msg = 'Polly client not available. '
            if not Config.AWS_ACCESS_KEY_ID or not Config.AWS_SECRET_ACCESS_KEY:
                error_msg += 'Please configure AWS credentials via .env file (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) or AWS CLI (aws configure).'
            else:
                error_msg += 'Please check your AWS credentials and Polly permissions.'
            print(f"[AWS POLLY] ❌ ERROR: {error_msg}")
            # Return 503 Service Unavailable instead of 500 for missing service
            return jsonify({'error': error_msg, 'service_unavailable': True}), 503
        
        print("[AWS POLLY] ✅ Polly client is available, proceeding with text processing...")
        
        # Clean text for better speech
        clean_text = text
        original_length = len(clean_text)
        
        # Remove product IDs but keep context
        clean_text = re.sub(r'Product\s*#\d+', '', clean_text, flags=re.IGNORECASE)
        # Remove URLs
        clean_text = re.sub(r'https?://[^\s]+', '', clean_text)
        # Remove markdown
        clean_text = clean_text.replace('*', '').replace('_', '').replace('`', '')
        # Remove emojis and special characters (keep basic punctuation)
        clean_text = re.sub(r"[^\w\s.,!?;:()\-'\"]", ' ', clean_text)
        # Clean up spacing
        clean_text = ' '.join(clean_text.split())
        
        print(f"[AWS POLLY] Text cleaning:")
        print(f"  - Original length: {original_length} characters")
        print(f"  - Cleaned length: {len(clean_text)} characters")
        print(f"  - Cleaned text preview: {clean_text[:100]}..." if len(clean_text) > 100 else f"  - Cleaned text: {clean_text}")
        
        if not clean_text:
            print("[AWS POLLY] ❌ ERROR: No valid text after cleaning")
            return jsonify({'error': 'No valid text to convert'}), 400
        
        # Select voice based on user preference or gender
        if voice_id_param:
            # Use specific voice ID if provided
            voice_id = voice_id_param
            print(f"[AWS POLLY] Using user-selected voice: {voice_id}")
        elif voice_gender == 'woman':
            # Default women's voices
            # Kendra - warm, friendly, attractive American voice (very appealing)
            # Alternative: Amy (expressive), Kimberly (smooth), Salli (clear, warm)
            voice_id = 'Kendra'  # Warm, attractive, American accent
        else:
            # Default men's voices
            # Joey - young, energetic, attractive American male voice
            # Alternative: Justin (expressive), Matthew (calm, professional)
            voice_id = 'Joey'  # Attractive, energetic American accent
        
        print(f"[AWS POLLY] Voice selection: {voice_id} (gender: {voice_gender})")
        
        # Use standard engine with SSML for better control over prosody
        # Standard engine supports prosody tags (rate, pitch, volume) for better expression
        import re
        import html
        
        # Escape HTML/XML special characters for SSML
        escaped_text = html.escape(clean_text)
        
        # Detect excitement level in text
        excitement_indicators = ['!', 'OMG', 'wow', 'awesome', 'amazing', 'great', 'perfect', 
                                 'love', 'fantastic', 'excellent', 'wonderful', 'beautiful']
        excitement_level = sum(1 for indicator in excitement_indicators if indicator.lower() in text.lower())
        has_exclamation = '!' in text
        
        # Create SSML with prosody for attractive, warm, appealing American voice
        # Rate: slower for more appealing, seductive feel (82-85% = slower, more alluring)
        # Pitch: slightly lower for warmer, more attractive tone (-1% to +1%)
        # Volume: medium for clear but intimate feel
        # Phonation: soft for appealing, warm, attractive tone
        
        # Calculate rate based on speech speed (base rate * speed multiplier)
        # Base rates: 82% (normal), 85% (excited)
        # SSML rate accepts percentages: 50% to 200%
        base_rate_normal = 82
        base_rate_excited = 85
        
        # Convert speed multiplier to percentage (1.0 = 100%, 0.5 = 50%, 2.0 = 200%)
        # Apply speed to base rate: rate = base_rate * speed
        if excitement_level > 2 or has_exclamation:
            # More excited: use excited base rate adjusted by speed
            rate_percent = int(base_rate_excited * speech_speed)
            rate_percent = max(50, min(200, rate_percent))  # Clamp between 50% and 200%
            ssml_text = f'<speak><prosody rate="{rate_percent}%" pitch="+1%" volume="medium">' \
                       f'<amazon:effect phonation="soft">{escaped_text}</amazon:effect>' \
                       f'</prosody></speak>'
            print(f"[AWS POLLY] Using excited appealing SSML (rate: {rate_percent}%, pitch: +1%, soft phonation, speed: {speech_speed}x)")
        else:
            # Normal: use normal base rate adjusted by speed
            rate_percent = int(base_rate_normal * speech_speed)
            rate_percent = max(50, min(200, rate_percent))  # Clamp between 50% and 200%
            ssml_text = f'<speak><prosody rate="{rate_percent}%" pitch="-1%" volume="medium">' \
                       f'<amazon:effect phonation="soft">{escaped_text}</amazon:effect>' \
                       f'</prosody></speak>'
            print(f"[AWS POLLY] Using warm appealing SSML (rate: {rate_percent}%, pitch: -1%, soft phonation, speed: {speech_speed}x)")
        
        print(f"[AWS POLLY] SSML length: {len(ssml_text)} characters")
        print(f"[AWS POLLY] Text preview: {clean_text[:200]}..." if len(clean_text) > 200 else f"[AWS POLLY] Text: {clean_text}")
        
        # Use standard engine with SSML for better prosody control
        import time
        start_time = time.time()
        response = None
        engine_used = 'standard'
        
        try:
            print(f"[AWS POLLY] Calling AWS Polly with standard engine and SSML...")
            print(f"  - VoiceId: {voice_id}")
            print(f"  - Engine: standard (supports SSML prosody)")
            print(f"  - OutputFormat: mp3")
            print(f"  - TextType: ssml")
            
            response = polly_client.synthesize_speech(
                Text=ssml_text,
                OutputFormat='mp3',
                VoiceId=voice_id,
                TextType='ssml'  # Using SSML for prosody control
                # Standard engine (no Engine parameter = standard)
            )
            elapsed_time = time.time() - start_time
            print(f"[AWS POLLY] ✅ Polly API call successful with standard engine + SSML (took {elapsed_time:.2f}s)")
        except Exception as ssml_error:
            elapsed_time = time.time() - start_time
            error_msg = str(ssml_error)
            print(f"[AWS POLLY] ⚠️ SSML failed, trying plain text with standard engine...")
            print(f"[AWS POLLY] Error: {error_msg}")
            
            # Fallback: plain text without SSML
            try:
                start_time = time.time()
                response = polly_client.synthesize_speech(
                    Text=clean_text,
                    OutputFormat='mp3',
                    VoiceId=voice_id
                    # Standard engine with plain text
                )
                elapsed_time = time.time() - start_time
                print(f"[AWS POLLY] ✅ Polly API call successful with standard engine + plain text (took {elapsed_time:.2f}s)")
            except Exception as plain_error:
                elapsed_time = time.time() - start_time
                print(f"[AWS POLLY] ❌ ERROR: Both SSML and plain text failed after {elapsed_time:.2f}s")
                print(f"[AWS POLLY] Error type: {type(plain_error).__name__}")
                print(f"[AWS POLLY] Error message: {str(plain_error)}")
                print(f"[AWS POLLY] Error traceback:")
                traceback.print_exc()
                raise
        
        # Get audio stream
        print("[AWS POLLY] Reading audio stream from response...")
        audio_stream = response['AudioStream'].read()
        audio_size = len(audio_stream)
        print(f"[AWS POLLY] ✅ Audio stream received: {audio_size} bytes ({audio_size / 1024:.2f} KB)")
        
        # Return as base64 encoded audio
        print("[AWS POLLY] Encoding audio to base64...")
        audio_base64 = base64.b64encode(audio_stream).decode('utf-8')
        base64_size = len(audio_base64)
        print(f"[AWS POLLY] ✅ Base64 encoding complete: {base64_size} characters")
        
        print("[AWS POLLY] ✅ SUCCESS: Returning audio response to client")
        print("=" * 80)
        
        return jsonify({
            'audio': audio_base64,
            'format': 'mp3',
            'voice': voice_id,
            'engine': engine_used
        })
        
    except Exception as e:
        print(f"[AWS POLLY] ❌ EXCEPTION in text-to-speech endpoint")
        print(f"[AWS POLLY] Error type: {type(e).__name__}")
        print(f"[AWS POLLY] Error message: {str(e)}")
        print(f"[AWS POLLY] Full traceback:")
        traceback.print_exc()
        print("=" * 80)
        return jsonify({'error': f'Failed to generate speech: {str(e)}'}), 500

@ai_agent_bp.route('/upload-image', methods=['POST'])
def upload_image():
    """Handle image upload for AI agent to analyze fashion items and find similar products."""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if file_ext not in allowed_extensions:
            return jsonify({'error': f'Invalid file type. Allowed: {", ".join(allowed_extensions)}'}), 400
        
        # Read image data
        from PIL import Image
        import io
        import base64
        import re
        
        image_data = file.read()
        image = Image.open(io.BytesIO(image_data))
        
        # Validate image size (max 10MB)
        if len(image_data) > 10 * 1024 * 1024:
            return jsonify({'error': 'Image too large. Maximum size is 10MB'}), 400
        
        # Resize if too large (max 2000x2000)
        max_dimension = 2000
        if image.size[0] > max_dimension or image.size[1] > max_dimension:
            image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
        
        # Convert to base64 for storage/transmission
        buffered = io.BytesIO()
        # Save as JPEG for smaller size
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        image.save(buffered, format='JPEG', quality=85)
        image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        # Analyze image with AI and extract metadata
        analysis_prompt = """Analyze this fashion image and provide a structured response in the following format. Be thorough and extract ALL available information:

ITEM_TYPE: [e.g., dress, shirt, t-shirt, pants, jeans, blouse, jacket, etc.]
COLOR: [primary color, e.g., blue, red, black, white, navy, etc.]
SECONDARY_COLOR: [if applicable, e.g., white stripes, black buttons, etc.]
CATEGORY: [men, women, or kids]
CLOTHING_TYPE: [specific type like "T-Shirt", "Dress", "Jeans", "Polo Shirt", etc.]
STYLE_FEATURES: [comma-separated list: e.g., v-neck, long sleeve, casual, formal, fitted, loose, etc.]
OCCASION: [e.g., casual, business, date night, wedding, party, etc.]
FABRIC: [if visible, e.g., cotton, denim, polyester, silk, wool, etc.]
PATTERN: [if visible, e.g., solid, striped, floral, plaid, etc.]
SIZE_INDICATOR: [if visible, e.g., small, medium, large, etc.]
SEASON: [if applicable, e.g., spring, summer, fall, winter, all-season]

Then provide a natural, enthusiastic description of the item in 2-3 sentences, highlighting its key features and style."""
        
        # Analyze image using active AI config (OpenAI/Gemini/Anthropic vision)
        metadata = {}
        analysis_text = ""
        similar_products = []
        vision_config = get_active_ai_config()
        analysis_text = call_llm_vision(
            vision_config,
            analysis_prompt,
            image_base64,
            system_prompt="You are a fashion expert analyzing clothing items from images. Provide detailed, structured analysis in the exact format requested. Be thorough and extract ALL available information from the image.",
            media_type='image/jpeg',
        )
        if not analysis_text:
            # Fallback to text-only if no vision-capable config
            response = call_llm(
                "Please analyze this fashion image. " + analysis_prompt,
                system_prompt="You are a fashion expert analyzing clothing items from images. Provide detailed, structured analysis.",
                config=vision_config,
            )
            analysis_text = response.get('content', '')
        elif analysis_text:
            print(f"[IMAGE ANALYSIS] Successfully analyzed image, response length: {len(analysis_text)}")
        
        # Extract metadata from analysis (regardless of vision vs text fallback)
        if analysis_text:
                # Extract ITEM_TYPE or CLOTHING_TYPE
                item_match = re.search(r'(?:ITEM_TYPE|CLOTHING_TYPE):\s*([^\n]+)', analysis_text, re.IGNORECASE)
                if item_match:
                    clothing_type = item_match.group(1).strip()
                    # Normalize common clothing types
                    clothing_type_lower = clothing_type.lower()
                    if 'dress' in clothing_type_lower:
                        metadata['clothing_type'] = 'Dress'
                    elif 'shirt' in clothing_type_lower or 'blouse' in clothing_type_lower:
                        metadata['clothing_type'] = 'Shirt' if 't-shirt' not in clothing_type_lower else 'T-Shirt'
                    elif 't-shirt' in clothing_type_lower or 'tshirt' in clothing_type_lower:
                        metadata['clothing_type'] = 'T-Shirt'
                    elif 'pants' in clothing_type_lower or 'trousers' in clothing_type_lower:
                        metadata['clothing_type'] = 'Pants'
                    elif 'jeans' in clothing_type_lower:
                        metadata['clothing_type'] = 'Jeans'
                    elif 'polo' in clothing_type_lower:
                        metadata['clothing_type'] = 'Polo Shirt'
                    else:
                        metadata['clothing_type'] = clothing_type
                
                # Extract COLOR
                color_match = re.search(r'COLOR:\s*([^\n]+)', analysis_text, re.IGNORECASE)
                if color_match:
                    color = color_match.group(1).strip().lower()
                    # Normalize colors
                    color_map = {
                        'blue': 'Blue', 'navy': 'Navy', 'light blue': 'Blue',
                        'red': 'Red', 'maroon': 'Maroon', 'burgundy': 'Red',
                        'black': 'Black', 'dark': 'Black',
                        'white': 'White', 'cream': 'White', 'ivory': 'White',
                        'green': 'Green', 'emerald': 'Green',
                        'yellow': 'Yellow', 'gold': 'Yellow',
                        'pink': 'Pink', 'rose': 'Pink',
                        'purple': 'Purple', 'violet': 'Purple',
                        'gray': 'Gray', 'grey': 'Gray', 'silver': 'Gray',
                        'brown': 'Brown', 'tan': 'Brown', 'beige': 'Beige',
                        'orange': 'Orange'
                    }
                    for key, value in color_map.items():
                        if key in color:
                            metadata['color'] = value
                            break
                    if 'color' not in metadata:
                        metadata['color'] = color_match.group(1).strip()
                
                # Extract CATEGORY
                category_match = re.search(r'CATEGORY:\s*(men|women|kids)', analysis_text, re.IGNORECASE)
                if category_match:
                    metadata['category'] = category_match.group(1).lower()
                else:
                    # Try to infer from text
                    text_lower = analysis_text.lower()
                    if any(word in text_lower for word in ['women', 'woman', 'ladies', 'female']):
                        metadata['category'] = 'women'
                    elif any(word in text_lower for word in ['men', 'man', 'male', 'gentleman']):
                        metadata['category'] = 'men'
                    elif any(word in text_lower for word in ['kids', 'kid', 'children', 'child']):
                        metadata['category'] = 'kids'
                
                # Extract OCCASION
                occasion_match = re.search(r'OCCASION:\s*([^\n]+)', analysis_text, re.IGNORECASE)
                if occasion_match:
                    occasion = occasion_match.group(1).strip().lower()
                    # Normalize occasions
                    if 'casual' in occasion:
                        metadata['occasion'] = 'casual'
                    elif 'business' in occasion or 'professional' in occasion or 'formal' in occasion:
                        metadata['occasion'] = 'business_formal' if 'formal' in occasion else 'business_casual'
                    elif 'date' in occasion or 'night' in occasion:
                        metadata['occasion'] = 'date_night'
                    elif 'wedding' in occasion:
                        metadata['occasion'] = 'wedding'
                    else:
                        metadata['occasion'] = occasion
                
                # Extract FABRIC
                fabric_match = re.search(r'FABRIC:\s*([^\n]+)', analysis_text, re.IGNORECASE)
                if fabric_match:
                    fabric = fabric_match.group(1).strip()
                    # Normalize fabrics
                    fabric_lower = fabric.lower()
                    if 'cotton' in fabric_lower:
                        metadata['fabric'] = 'Cotton'
                    elif 'polyester' in fabric_lower:
                        metadata['fabric'] = 'Polyester'
                    elif 'wool' in fabric_lower:
                        metadata['fabric'] = 'Wool'
                    elif 'silk' in fabric_lower:
                        metadata['fabric'] = 'Silk'
                    elif 'denim' in fabric_lower:
                        metadata['fabric'] = 'Denim'
                    elif 'linen' in fabric_lower:
                        metadata['fabric'] = 'Linen'
                    else:
                        metadata['fabric'] = fabric
                
                # Extract STYLE_FEATURES
                style_match = re.search(r'STYLE_FEATURES:\s*([^\n]+)', analysis_text, re.IGNORECASE)
                if style_match:
                    style_features = style_match.group(1).strip()
                    # Split by comma and clean up
                    metadata['style_features'] = [s.strip() for s in style_features.split(',') if s.strip()]
                
                # Extract SECONDARY_COLOR
                secondary_color_match = re.search(r'SECONDARY_COLOR:\s*([^\n]+)', analysis_text, re.IGNORECASE)
                if secondary_color_match:
                    secondary_color = secondary_color_match.group(1).strip()
                    if secondary_color and secondary_color.lower() != 'none' and secondary_color.lower() != 'n/a':
                        metadata['secondary_color'] = secondary_color
                
                # Extract PATTERN
                pattern_match = re.search(r'PATTERN:\s*([^\n]+)', analysis_text, re.IGNORECASE)
                if pattern_match:
                    pattern = pattern_match.group(1).strip().lower()
                    pattern_map = {
                        'solid': 'Solid', 'plain': 'Solid',
                        'striped': 'Striped', 'stripe': 'Striped',
                        'floral': 'Floral', 'flower': 'Floral',
                        'plaid': 'Plaid', 'checkered': 'Plaid',
                        'polka dot': 'Polka Dot', 'polkadot': 'Polka Dot',
                        'geometric': 'Geometric', 'abstract': 'Geometric'
                    }
                    for key, value in pattern_map.items():
                        if key in pattern:
                            metadata['pattern'] = value
                            break
                    if 'pattern' not in metadata:
                        metadata['pattern'] = pattern_match.group(1).strip()
                
                # Extract SEASON
                season_match = re.search(r'SEASON:\s*([^\n]+)', analysis_text, re.IGNORECASE)
                if season_match:
                    season = season_match.group(1).strip().lower()
                    season_map = {
                        'spring': 'Spring', 'summer': 'Summer',
                        'fall': 'Fall', 'autumn': 'Fall',
                        'winter': 'Winter', 'all-season': 'All Season',
                        'all season': 'All Season'
                    }
                    for key, value in season_map.items():
                        if key in season:
                            metadata['season'] = value
                            break
                
                # Extract the natural description (text after the structured data)
                # Remove structured metadata lines
                lines = analysis_text.split('\n')
                desc_lines = []
                skip_next = False
                metadata_prefixes = ['ITEM_TYPE:', 'COLOR:', 'SECONDARY_COLOR:', 'CATEGORY:', 'CLOTHING_TYPE:', 
                                    'STYLE_FEATURES:', 'OCCASION:', 'FABRIC:', 'PATTERN:', 'SIZE_INDICATOR:', 'SEASON:']
                for i, line in enumerate(lines):
                    line_stripped = line.strip()
                    if any(line_stripped.startswith(prefix) for prefix in metadata_prefixes):
                        skip_next = True
                        continue
                    if skip_next and not line_stripped:
                        skip_next = False
                        continue
                    if not skip_next and line_stripped:
                        desc_lines.append(line)
                
                if desc_lines:
                    analysis_text = '\n'.join(desc_lines).strip()
                elif not any(line.strip().startswith(('ITEM_TYPE:', 'COLOR:', 'CATEGORY:')) for line in lines):
                    # If no structured format, use the whole text
                    analysis_text = analysis_text.strip()
        
        # Search for similar products based on extracted metadata
        search_criteria = {}
        if metadata.get('category'):
            search_criteria['category'] = metadata['category']
        if metadata.get('color'):
            search_criteria['color'] = metadata['color']
        if metadata.get('clothing_type'):
            search_criteria['clothing_type'] = metadata['clothing_type']
        if metadata.get('occasion'):
            search_criteria['occasion'] = metadata['occasion']
        if metadata.get('fabric'):
            search_criteria['fabric'] = metadata['fabric']
        
        # Search products using criteria
        similar_products = []
        if search_criteria:
            # Try exact match first
            similar_products = search_products_by_criteria(search_criteria)
            
            # If not enough results, try partial matches
            if len(similar_products) < 5:
                # Try without occasion (less strict)
                partial_criteria = {k: v for k, v in search_criteria.items() if k != 'occasion'}
                if partial_criteria and len(partial_criteria) < len(search_criteria):
                    partial_products = search_products_by_criteria(partial_criteria)
                    # Add products not already in similar_products
                    existing_ids = {p['id'] for p in similar_products}
                    for p in partial_products:
                        if p['id'] not in existing_ids:
                            similar_products.append(p)
            
            # If still not enough, try just category and color
            if len(similar_products) < 5 and search_criteria.get('category') and search_criteria.get('color'):
                simple_criteria = {
                    'category': search_criteria['category'],
                    'color': search_criteria['color']
                }
                simple_products = search_products_by_criteria(simple_criteria)
                existing_ids = {p['id'] for p in similar_products}
                for p in simple_products:
                    if p['id'] not in existing_ids:
                        similar_products.append(p)
            
            # If still not enough, try just category
            if len(similar_products) < 5 and search_criteria.get('category'):
                category_only = {'category': search_criteria['category']}
                category_products = search_products_by_criteria(category_only)
                existing_ids = {p['id'] for p in similar_products}
                for p in category_products:
                    if p['id'] not in existing_ids:
                        similar_products.append(p)
        
        # Fallback: use vector search with description
        if len(similar_products) < 3 and analysis_text:
            # Create search query from analysis
            search_terms = []
            if metadata.get('clothing_type'):
                search_terms.append(metadata['clothing_type'])
            if metadata.get('color'):
                search_terms.append(metadata['color'])
            if metadata.get('category'):
                search_terms.append(metadata['category'])
            
            search_query = ' '.join(search_terms) if search_terms else analysis_text[:200]
            vector_product_ids = search_products_vector(search_query, n_results=10)
            if vector_product_ids:
                products = Product.query.filter(Product.id.in_(vector_product_ids)).filter_by(is_active=True).all()
                vector_products = [p.to_dict() for p in products]
                # Add products not already found
                existing_ids = {p['id'] for p in similar_products}
                for p in vector_products:
                    if p['id'] not in existing_ids:
                        similar_products.append(p)
        
        # Limit to 8 products for display
        similar_products = similar_products[:8]
        
        # Format metadata into a nice sentence
        metadata_sentence = ""
        if metadata:
            parts = []
            if metadata.get('clothing_type'):
                parts.append(f"a {metadata['clothing_type']}")
            if metadata.get('color'):
                parts.append(f"in {metadata['color']}")
            if metadata.get('category'):
                parts.append(f"for {metadata['category']}")
            if metadata.get('occasion'):
                parts.append(f"suitable for {metadata['occasion']}")
            
            if parts:
                metadata_sentence = "This appears to be " + " ".join(parts) + "."
            else:
                metadata_sentence = "I've analyzed your image and found some similar items!"
        else:
            metadata_sentence = "I've analyzed your image and found some similar items!"
        
        # Combine analysis and metadata into a natural response
        if analysis_text and "needs to be configured" not in analysis_text:
            full_response = f"{metadata_sentence}\n\n{analysis_text}"
        else:
            full_response = metadata_sentence
        
        if similar_products:
            full_response += f"\n\nI found {len(similar_products)} similar product{'s' if len(similar_products) != 1 else ''} in our store that you might like!"
        
        return jsonify({
            'success': True,
            'message': full_response,
            'image_data': image_base64,
            'image_format': 'jpeg',
            'metadata': metadata,
            'metadata_sentence': metadata_sentence,
            'similar_products': similar_products,
            'similar_product_ids': [p['id'] for p in similar_products]
        })
        
    except Exception as e:
        print(f"Error uploading image: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to process image: {str(e)}'}), 500

@ai_agent_bp.route('/analyze-image', methods=['POST'])
def analyze_image():
    """Analyze uploaded image using AI to provide fashion recommendations."""
    try:
        data = request.get_json()
        image_base64 = data.get('image_data', '')
        user_query = data.get('query', 'What is this item and what would match it?')
        
        if not image_base64:
            return jsonify({'error': 'No image data provided'}), 400
        
        # Decode base64 image
        import base64
        import io
        from PIL import Image
        
        try:
            image_bytes = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            return jsonify({'error': f'Invalid image data: {str(e)}'}), 400
        
        analysis_prompt = f"""You are a fashion expert analyzing a clothing item from an uploaded image.

User's question: {user_query}

Based on the image provided, please:
1. Identify the type of clothing (dress, shirt, pants, etc.)
2. Describe the color(s) and style
3. Suggest matching items or complementary pieces
4. Recommend occasions where this would be appropriate
5. Provide styling tips

Be enthusiastic and helpful, matching the tone of our shopping assistant!"""
        config = get_active_ai_config()
        analysis_text_vision = call_llm_vision(config, analysis_prompt, image_base64, system_prompt="You are a fashion expert helping customers find matching items and styling advice.", media_type='image/jpeg')
        if analysis_text_vision:
            analysis = analysis_text_vision
        elif config:
            response = call_llm(analysis_prompt, system_prompt="You are a fashion expert helping customers find matching items and styling advice.", config=config)
            analysis = response.get('content', 'Unable to analyze image at this time.')
        else:
            analysis = "I can see you've uploaded an image! To get detailed fashion analysis, add and activate an AI model (OpenAI, Gemini, or Anthropic) in Admin → AI Assistant. Until then, you can describe the item and I'll help find similar products!"
        
        # Search for similar products based on the analysis
        # This would be enhanced with actual image recognition/ML in production
        similar_products = []
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'similar_products': similar_products,
            'suggestion': 'Try asking me to find similar items or suggest matching pieces!'
        })
        
    except Exception as e:
        print(f"Error analyzing image: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to analyze image: {str(e)}'}), 500

@ai_agent_bp.route('/find-matches-for-image', methods=['POST'])
def find_matches_for_image():
    """Find matching products for an uploaded image using fashion match table and rules."""
    try:
        data = request.get_json()
        metadata = data.get('metadata', {})
        similar_product_ids = data.get('similar_product_ids', [])
        
        if not metadata and not similar_product_ids:
            return jsonify({'error': 'No metadata or product IDs provided'}), 400
        
        matched_products = []
        match_explanations = []
        
        # If we have similar products, use the first one as primary for fashion matching
        if similar_product_ids:
            primary_product_id = similar_product_ids[0]
            primary_product = Product.query.get(primary_product_id)
            
            if primary_product:
                primary_name = primary_product.name
                
                # Use ProductRelation table for fashion matches
                from models.product_relation import ProductRelation
                from utils.product_relations import ensure_product_relations
                
                # Ensure product relations exist
                ensure_product_relations(primary_product_id, primary_product.clothing_type)
                
                # Get fashion matches from database - get more items for complete outfit
                relations = ProductRelation.query.filter_by(
                    product_id=primary_product_id,
                    is_fashion_match=True
                ).order_by(ProductRelation.match_score.desc()).limit(12).all()
                
                # Group matches by clothing type to ensure complete outfit
                matches_by_type = {}
                for relation in relations:
                    if relation.related_product and relation.related_product.is_active:
                        clothing_type = relation.related_product.clothing_type or 'other'
                        if clothing_type not in matches_by_type:
                            matches_by_type[clothing_type] = []
                        matches_by_type[clothing_type].append({
                            'product': relation.related_product.to_dict(),
                            'score': relation.match_score
                        })
                
                # Prioritize different clothing types for complete outfit
                # If primary is a shirt, prioritize pants, shoes, accessories
                primary_type_lower = primary_product.clothing_type.lower() if primary_product.clothing_type else ''
                
                # Define outfit priorities based on primary item type
                outfit_priorities = []
                if any(word in primary_type_lower for word in ['shirt', 't-shirt', 'blouse', 'top', 'polo']):
                    # For shirts: pants, shoes, accessories
                    outfit_priorities = ['pants', 'chinos', 'jeans', 'trousers', 'shoes', 'sneakers', 'boots', 'accessories', 'belt']
                elif any(word in primary_type_lower for word in ['pants', 'chinos', 'jeans', 'trousers']):
                    # For pants: shirts, shoes, accessories
                    outfit_priorities = ['shirt', 't-shirt', 'blouse', 'top', 'shoes', 'sneakers', 'boots', 'accessories', 'belt']
                elif any(word in primary_type_lower for word in ['dress', 'gown']):
                    # For dresses: shoes, accessories
                    outfit_priorities = ['shoes', 'heels', 'sandals', 'accessories', 'bag', 'jewelry']
                else:
                    # Default: get variety
                    outfit_priorities = ['pants', 'shirt', 'shoes', 'accessories']
                
                # Collect matches prioritizing complete outfit
                existing_ids = {primary_product_id}
                for priority_type in outfit_priorities:
                    for clothing_type, matches in matches_by_type.items():
                        if priority_type.lower() in clothing_type.lower():
                            for match in matches[:2]:  # Max 2 per type
                                if match['product']['id'] not in existing_ids:
                                    matched_products.append(match['product'])
                                    match_explanations.append(f"Complete outfit match - {clothing_type} (score: {match['score']:.2f})")
                                    existing_ids.add(match['product']['id'])
                                    if len(matched_products) >= 8:
                                        break
                        if len(matched_products) >= 8:
                            break
                    if len(matched_products) >= 8:
                        break
                
                # Fill remaining slots with other high-scoring matches
                if len(matched_products) < 8:
                    for relation in relations:
                        if relation.related_product and relation.related_product.is_active:
                            if relation.related_product.id not in existing_ids:
                                matched_products.append(relation.related_product.to_dict())
                                match_explanations.append(f"Fashion match (score: {relation.match_score:.2f})")
                                existing_ids.add(relation.related_product.id)
                                if len(matched_products) >= 8:
                                    break
                
                # Also use fashion match rules as enhancement
                fashion_matches = find_matching_products(primary_name, primary_product_id)
                
                if fashion_matches:
                    # Try to find products matching the fashion match rules
                    existing_ids = {p['id'] for p in matched_products}
                    
                    for match in fashion_matches[:4]:  # Top 4 matches
                        matched_product_name = match['matched_product']
                        match_type = match['match_type']
                        priority = match['priority']
                        
                        # Search for products matching this name/type
                        search_terms = matched_product_name.lower().split()
                        query = Product.query.filter_by(is_active=True)
                        
                        # Try to find products matching the suggested item
                        for term in search_terms:
                            if len(term) > 2:  # Skip very short terms
                                query = query.filter(
                                    or_(
                                        Product.name.ilike(f'%{term}%'),
                                        Product.clothing_type.ilike(f'%{term}%'),
                                        Product.description.ilike(f'%{term}%')
                                    )
                                )
                        
                        matching_products = query.limit(2).all()
                        
                        for product in matching_products:
                            if product.id not in existing_ids and product.id != primary_product_id:
                                matched_products.append(product.to_dict())
                                explanation = get_match_explanation(match_type)
                                match_explanations.append(f"{match_type}: {explanation}")
                                existing_ids.add(product.id)
                                
                                if len(matched_products) >= 8:
                                    break
                        
                        if len(matched_products) >= 8:
                            break
        
        # If no matches found via product relations, use metadata to find matches
        if not matched_products and metadata:
            # Use metadata to search for complementary items
            if metadata.get('clothing_type'):
                clothing_type = metadata['clothing_type']
                # Use fashion match rules to find what matches this clothing type
                fashion_matches = find_matching_products(clothing_type)
                
                for match in fashion_matches[:6]:
                    matched_product_name = match['matched_product']
                    # Search for products matching this name
                    search_terms = matched_product_name.lower().split()
                    query = Product.query.filter_by(is_active=True)
                    
                    for term in search_terms:
                        if len(term) > 2:
                            query = query.filter(
                                or_(
                                    Product.name.ilike(f'%{term}%'),
                                    Product.clothing_type.ilike(f'%{term}%')
                                )
                            )
                    
                    matching_products = query.limit(2).all()
                    existing_ids = {p['id'] for p in matched_products}
                    
                    for product in matching_products:
                        if product.id not in existing_ids:
                            matched_products.append(product.to_dict())
                            match_type = match['match_type']
                            explanation = get_match_explanation(match_type)
                            match_explanations.append(f"{match_type}: {explanation}")
                            existing_ids.add(product.id)
                            
                            if len(matched_products) >= 8:
                                break
                    
                    if len(matched_products) >= 8:
                        break
        
        return jsonify({
            'success': True,
            'matched_products': matched_products[:8],  # Limit to 8
            'match_explanations': match_explanations[:8],
            'count': len(matched_products)
        })
        
    except Exception as e:
        print(f"Error finding matches for image: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to find matches: {str(e)}'}), 500

