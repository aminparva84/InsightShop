# AI Agent Architecture — InsightShop

This document describes how the **AI shopping assistant** is designed and how it is intended to function in the InsightShop project.

---

## 1. Overview

The AI Agent is a **conversational shopping assistant** that:

- Answers in natural language and helps users find clothing.
- Can use **multiple LLM providers** (OpenAI, Google Gemini, Anthropic, AWS Bedrock), chosen or configured by the admin.
- Uses **product search** (filters, vector search, fashion rules) to suggest real catalog items.
- Supports **voice** (speech input and text-to-speech via AWS Polly), **image upload** (find similar / fashion match), **product comparison**, and **cart actions** (e.g. “add product X to cart”).

The frontend talks to the backend over REST; the backend builds context (products, fashion knowledge, season), calls the selected LLM, and returns a response plus optional product IDs and UI actions (e.g. show in chat vs. update product grid).

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                                  │
│  • AIChat.js — chat UI, voice in/out, product cards, image upload        │
│  • Used on: Home, Products, Admin (AI Assistant panel)                  │
│  • Calls: /api/ai/chat, /api/ai/text-to-speech, /api/ai/upload-image…   │
└────────────────────────────────────────┬────────────────────────────────┘
                                         │ REST (JSON)
                                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         API LAYER (Flask)                                │
│  • routes/ai_agent.py — chat, search, filter, compare, TTS, image APIs   │
│  • routes/ai_cart.py — add-to-cart by product id/color/size (AI-driven)  │
│  • Prefix: /api/ai                                                       │
└────────────────────────────────────────┬────────────────────────────────┘
                                         │
         ┌───────────────────────────────┼───────────────────────────────┐
         ▼                               ▼                               ▼
┌─────────────────┐           ┌─────────────────────┐           ┌─────────────────┐
│ Provider &      │           │ Search & context    │           │ Voice & media   │
│ LLM selection   │           │                     │           │                 │
│                 │           │ • Product filters   │           │ • AWS Polly     │
│ • AiAssistant   │           │ • Vector search     │           │   (TTS)         │
│   Config        │           │ • Fashion KB        │           │ • Vision APIs   │
│ • AISelected    │           │ • Seasonal context  │           │   (image anal.) │
│   Provider      │           │ • Fashion match     │           │                 │
└────────┬────────┘           └──────────┬──────────┘           └────────┬────────┘
         │                               │                               │
         ▼                               ▼                               ▼
┌─────────────────┐           ┌─────────────────────┐           ┌─────────────────┐
│ LLM providers   │           │ Data & utils        │           │ External        │
│ (one active)    │           │                     │           │                 │
│ • OpenAI        │           │ • Product model     │           │ • AWS Polly     │
│ • Gemini        │           │ • vector_db         │           │ • OpenAI/Gemini/│
│ • Anthropic     │           │ • fashion_kb        │           │   Anthropic/    │
│ • AWS Bedrock   │           │ • seasonal_events   │           │   Bedrock vision │
└─────────────────┘           │ fashion_match_rules │           └─────────────────┘
                              │ spelling_tolerance   │
                              │ product_relations   │
                              └─────────────────────┘
```

---

## 3. Multi-Provider LLM Setup

The agent does **not** assume a single LLM. It supports **four fixed providers**, with one “active” at a time.

### 3.1 Models and configuration

- **`models/ai_assistant_config.py`**
  - **`AiAssistantConfig`** — one row per provider (`openai`, `gemini`, `anthropic`, `bedrock`). Stores:
    - Display name, optional SDK label
    - API key (optional; if empty, backend uses env/Secrets Manager)
    - Model ID, region (for Bedrock)
    - `is_valid`, `last_tested_at`, `latency_ms` (from admin “Test”)
  - **`AISelectedProvider`** — single row: which provider the chat uses. Values:
    - `auto` — use first provider that has a valid API key (order: openai → gemini → anthropic → bedrock)
    - `openai` | `gemini` | `anthropic` | `bedrock` — use that provider only

- **API key resolution** (in `routes/ai_agent.py`):
  - **Admin-stored key** for a provider is used if set.
  - Otherwise **env vars** (e.g. `OPENAI_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`) or, for Gemini, AWS Secrets Manager.
  - Bedrock can use admin-stored key (as `access_key:secret_key`) or `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`.

### 3.2 How the active provider is chosen

1. Read **selected provider** from `AISelectedProvider` (default `auto`).
2. If not `auto`, use that provider’s config (and its API key from DB or env).
3. If `auto`, iterate over `FIXED_PROVIDERS` and use the first provider that has an API key.

So: **one LLM is used per request**; the “agent” is the same logic (prompts, search, tools) with a pluggable LLM backend.

### 3.3 Admin panel (AI Assistant)

- **Admin → AI Assistant** (in `routes/admin.py`):
  - List the four providers; for each: set API key, model ID (and region for Bedrock), run **Test** (latency/validity).
  - **Select active provider**: Auto or one of the four.
- Test calls `call_llm('Say exactly: OK', ...)` and stores success/latency on `AiAssistantConfig`.

---

## 4. Main Chat Flow (`/api/ai/chat`)

This is the core of the agent: one user message in, one structured response out.

### 4.1 Input

- **message** — user text (lowercased for keyword logic).
- **history** — conversation history (for future use; currently the backend builds a single prompt).
- **selected_product_ids** — product IDs the user has “selected” in the UI (e.g. for “compare selected”).

### 4.2 Steps (in order)

1. **Provider/config**
   - Resolve `get_active_ai_config()` (selected provider + API key). If none, return 503 with a message that admin must set at least one provider.

2. **Comparison**
   - If the message looks like a comparison (“compare”, “which is better”, “compare selected”, etc.) and there are at least two product IDs (from message or `selected_product_ids`), the route:
     - Loads those products
     - Builds a short comparison (e.g. price range, best value)
     - Returns with `action: 'compare'`, `suggested_products`, `suggested_product_ids`, and does **not** call the LLM.

3. **Product search and filters**
   - **Occasion / age** — keyword maps (e.g. wedding, business casual, “over 50”) → filters on `Product`.
   - **Category** — e.g. men/women/kids via `normalize_category(message)` or keywords.
   - **Color** — `normalize_color_name(message)` or spelling-tolerant match.
   - **Clothing type** — `normalize_clothing_type(message)` plus keyword fallbacks (T-Shirt, Shirt, Dress, etc.).
   - **Dress style** — e.g. scoop, v-neck, midi, etc., applied to name/description/`dress_style`.
   - If **any** of these filters are set, a **direct DB query** is run (category strict: only that category). Results cap at 20; IDs and dicts are stored in `vector_product_ids` / `vector_products`.
   - If **no** filters, **vector search** is used (`search_products_vector(message, n_results=10)`). If that returns nothing, a **fallback** keyword search (category, color, clothing type) is run.

4. **“No results” for strict filters**
   - If filters were applied (e.g. category + clothing type) and **zero** products are found, the backend sets a “no results” path: it still calls the LLM but will later return **no** products and **no** `action`, so the frontend shows only the assistant message (e.g. “We don’t have those right now”) and does not update the product grid.

5. **Action for product list**
   - If there are products and the message looks like a product request (e.g. “show”, “find”, “shirt”, “blue”), `action` is set to `search_results`. This is used so the frontend can decide to show products in the grid and/or in the chat.

6. **Context for the LLM**
   - **Fashion knowledge** — `get_fashion_knowledge_base_text()` (e.g. color matching, style, occasions).
   - **Seasonal context** — `get_seasonal_context_text()`, current season, upcoming holidays, seasonal recommendations.
   - **Product sample** — first N products from full catalog (for “examples” in the system prompt).
   - **Search result summary** — “I found N products: Product #id: name - price …” or “No products found for …”.
   - **System prompt** — long prompt describing:
     - Personality (excited, casual, helpful)
     - Rules (e.g. “Complete the look”, urgency for low stock, returns policy, cart recovery)
     - Date/season and seasonal awareness
     - Ratings/reviews usage
     - Format: always mention “Product #ID: Name - Price”
     - Fashion Match Stylist mode when products are found

7. **LLM call**
   - `call_llm(full_prompt, system_prompt, config=ai_config)`.
   - Uses the active provider’s REST/SDK (OpenAI, Gemini, Anthropic, Bedrock). Response is plain text.

8. **Post-LLM**
   - Product list is restored from backup if it was ever overwritten.
   - **Suggested product IDs** — up to 10 IDs from `vector_product_ids` or extracted from `vector_products`.
   - **Action** — if products exist and none was set, set `action = 'search_results'`.
   - **No-results case** — if strict filters and no products, return empty products, no action.
   - **Fashion match suggestions** — if products were found, optionally attach “complete the look” suggestions (from `ProductRelation` and `find_matching_products`).

9. **Response**
   - JSON: `response` (LLM text), `suggested_products`, `suggested_product_ids`, `action`, `fashion_match_suggestions`, `selected_provider`.

So: the **agent** = **deterministic search + filters + context builder + one LLM call + response shaping**. The LLM does not call tools; the backend does all product and comparison logic and only asks the LLM for the natural-language reply and to follow formatting rules.

---

## 5. How the Frontend Uses the Agent

- **AIChat** sends `POST /api/ai/chat` with `message`, `history`, `selected_product_ids`.
- On response:
  - It appends the assistant **message** to the chat.
  - If **`action === 'search_results'`** and there are **`suggested_product_ids`** (or `suggested_products`):
    - On **Home**: it can call **`onProductsUpdate(ids)`** so the Home page product grid shows exactly those IDs (from backend).
    - It may **navigate to Products** with those IDs, or show product cards **inside the chat** (depending on UX).
  - If there are **no** products or **no** action, it only shows the message (e.g. “we don’t have that”) and does not change the grid.
- **Voice**
  - Speech input: browser Speech Recognition → text into the chat input.
  - Speech output: for the assistant message, frontend can call **`/api/ai/text-to-speech`** with text, voice id, speed; backend uses **AWS Polly** and returns base64 audio. Long text can be summarized first via **`/api/ai/summarize`**.
- **Images**
  - User uploads an image; frontend sends it to **`/api/ai/upload-image`** or **`/api/ai/analyze-image`** / **`/api/ai/find-matches-for-image`**. Backend uses the **same selected LLM** (if it supports vision: OpenAI, Gemini, Anthropic, Bedrock) to analyze the image and optionally find similar products or fashion matches.

So the agent “aims to function” as a **single conversational surface** (text + voice + image) that drives **product discovery**, **comparison**, and **grid/page updates** via backend-controlled product IDs and actions.

---

## 6. Supporting Backend Pieces

| Component | Role |
|-----------|------|
| **utils/vector_db.py** | Vector/semantic product search (e.g. ChromaDB or similar) used when no structured filters are detected. |
| **utils/fashion_kb.py** | Fashion knowledge text (color matching, style, occasions, fabrics) injected into the system prompt. |
| **utils/spelling_tolerance.py** | Normalize clothing type, category, color from user message. |
| **utils/seasonal_events.py** | Current date, season, holidays, seasonal recommendations for the prompt. |
| **utils/fashion_match_rules.py** | “Complete the look” style rules; `find_matching_products`, `get_match_explanation`. |
| **utils/product_relations.py** | DB-backed product relations for fashion-match suggestions. |
| **utils/color_names.py** | Normalize color names from message. |
| **routes/ai_cart.py** | Add to cart by product id (and optional color/size); used when the user says things like “add product 5 to cart”. (Blueprint must be registered in the app if used.) |

---

## 7. API Endpoints (Summary)

| Endpoint | Purpose |
|----------|---------|
| `POST /api/ai/chat` | Main chat: one user message → LLM reply + optional product IDs and action. |
| `GET /api/ai/models` | Returns current selected provider (for UI). |
| `POST /api/ai/search` | AI/vector product search. |
| `POST /api/ai/filter` | AI-powered filter. |
| `POST /api/ai/compare` | Compare products by IDs. |
| `POST /api/ai/summarize` | Summarize long text (e.g. before TTS). |
| `GET /api/ai/text-to-speech/status` | Whether Polly is available. |
| `POST /api/ai/text-to-speech` | Turn text into speech (Polly); returns base64 audio. |
| `POST /api/ai/upload-image` | Upload image for analysis. |
| `POST /api/ai/analyze-image` | Analyze uploaded image (vision LLM). |
| `POST /api/ai/find-matches-for-image` | Find similar/fashion-match products from image. |

Admin-specific endpoints (under `/api/admin`) handle listing/updating provider configs and setting the selected provider.

---

## 8. Design Goals (How It Aims to Function)

1. **Provider-agnostic** — Same agent behavior regardless of whether the store uses OpenAI, Gemini, Anthropic, or Bedrock; admin chooses one or “auto”.
2. **Search-first** — Product results are determined by **backend logic** (filters, vector search, fallbacks), not by the LLM choosing IDs; the LLM only explains and formats.
3. **Strict category/filters** — When the user clearly asks for a category or type, the backend enforces it (e.g. only women’s), and returns “no results” cleanly when nothing matches.
4. **Clear contract with frontend** — `action` + `suggested_product_ids` (or `suggested_products`) drive whether the grid updates or the user stays in chat; no duplicate or misleading product lists.
5. **Voice and vision** — Same chat surface; voice in/out via Polly; image analysis and “find similar” via the selected vision-capable LLM.
6. **Fashion and season awareness** — System prompt includes fashion KB and seasonal context so the assistant sounds knowledgeable and context-aware.
7. **Fashion Match / complete the look** — When products are found, backend can attach fashion-match suggestions (DB relations + rules) so the assistant can suggest complementary items.

Overall, the **AI Agent** is a **single, multi-provider conversational layer** that ties together product search, filters, fashion knowledge, seasonality, voice, and images to help users find and compare clothing and, where implemented, update the product grid or cart from the same chat experience.
