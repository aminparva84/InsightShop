"""
AI Action Dispatcher — maps each canonical AI action to a backend handler (API).

When the AI returns a JSON with "action" and "parameters", this module ensures
that action is executed by the correct backend (execute_action, execute_tool, or inline logic).
Every action the AI can return has exactly one handler here.

Action → Backend (API) mapping:
  NONE                 → no-op (message only)
  REDIRECT             → inline redirect_map → redirect_to path
  ADD_TO_CART          → agent_executor.execute_action('add_item')
  REMOVE_FROM_CART     → agent_executor.execute_action('remove_item')
  VIEW_CART            → agent_executor.execute_action('show_cart')
  CLEAR_CART           → agent_executor.execute_action('clear_cart')
  UPDATE_CART_ITEM     → remove_item then add_item (agent_executor)
  ADD_TO_WISHLIST      → tool_executor.execute_tool('wishlist_add')
  REMOVE_FROM_WISHLIST → tool_executor.execute_tool('wishlist_remove')
  VIEW_WISHLIST        → tool_executor.execute_tool('wishlist_view')
  SEARCH_PRODUCTS      → tool_executor.execute_tool('search_products')
  COMPARE_PRODUCTS     → Product.query + inline comparison text
"""

from typing import Any, Dict, List, Optional

from models.product import Product
from utils.agent_executor import execute_action, can_execute_action
from utils.tool_executor import execute_tool


# All internal action names that the chat route can dispatch (after canonical -> internal mapping).
DISPATCHABLE_ACTIONS = frozenset({
    'none',
    'redirect',
    'add_item',
    'remove_item',
    'show_cart',
    'clear_cart',
    'update_cart_item',
    'add_to_wishlist',
    'remove_from_wishlist',
    'view_wishlist',
    'search_products',
    'compare_products',
})


def _get_current_user():
    from routes.auth import get_current_user_optional
    return get_current_user_optional()


# ---------------------------------------------------------------------------
# Handlers: each action triggers one backend path
# ---------------------------------------------------------------------------

def handle_none(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """No backend action. Return message only."""
    return {
        'success': True,
        'message': context.get('llm_message') or "How can I help? You can search for products, add to cart, or ask 'show my cart'.",
        'response_action': None,
        'redirect_to': None,
    }


def handle_redirect(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Navigate to a page. No DB call."""
    dest = (params.get('destination') or 'CART_PAGE').strip().upper()
    redirect_map = {
        'CART_PAGE': '/cart',
        'WISHLIST': '/wishlist',
        'CHECKOUT': '/checkout',
        'MY_ORDERS': '/orders',
    }
    path = redirect_map.get(dest, '/cart')
    return {
        'success': True,
        'message': context.get('llm_message') or "Redirecting you.",
        'response_action': 'agent_executed',
        'redirect_to': path,
        'parameters_used': {'destination': dest},
    }


def handle_add_item(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """ADD_TO_CART → agent_executor.execute_action('add_item')."""
    user = _get_current_user()
    allowed, err_msg = can_execute_action('add_item', params, user)
    if not allowed:
        return {
            'success': False,
            'message': err_msg or "I can't do that.",
            'response_action': 'agent_executed',
            'redirect_to': None,
            'denied': True,
        }
    result = execute_action('add_item', params)
    if not result.get('added'):
        result = {**result, 'success': False, 'message': result.get('message') or "Couldn't add that to your cart."}
    return {
        'success': result.get('success', False),
        'message': result.get('message', 'Done.'),
        'response_action': 'agent_executed',
        'redirect_to': '/cart' if result.get('success') else None,
        'agent_result': result,
    }


def handle_remove_item(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """REMOVE_FROM_CART → agent_executor.execute_action('remove_item')."""
    user = _get_current_user()
    allowed, err_msg = can_execute_action('remove_item', params, user)
    if not allowed:
        return {
            'success': False,
            'message': err_msg or "I can't do that.",
            'response_action': 'agent_executed',
            'redirect_to': None,
            'denied': True,
        }
    result = execute_action('remove_item', params)
    return {
        'success': result.get('success', False),
        'message': result.get('message', 'Done.'),
        'response_action': 'agent_executed',
        'redirect_to': '/cart' if result.get('success') else None,
        'agent_result': result,
    }


def handle_show_cart(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """VIEW_CART → agent_executor.execute_action('show_cart')."""
    user = _get_current_user()
    allowed, err_msg = can_execute_action('show_cart', params, user)
    if not allowed:
        return {
            'success': False,
            'message': err_msg or "I can't do that.",
            'response_action': 'agent_executed',
            'redirect_to': None,
            'denied': True,
        }
    result = execute_action('show_cart', params)
    return {
        'success': result.get('success', False),
        'message': result.get('message', 'Done.'),
        'response_action': 'agent_executed',
        'redirect_to': '/cart' if result.get('success') else None,
        'agent_result': result,
    }


def handle_clear_cart(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """CLEAR_CART → agent_executor.execute_action('clear_cart')."""
    user = _get_current_user()
    allowed, err_msg = can_execute_action('clear_cart', params, user)
    if not allowed:
        return {
            'success': False,
            'message': err_msg or "I can't do that.",
            'response_action': 'agent_executed',
            'redirect_to': None,
            'denied': True,
        }
    result = execute_action('clear_cart', params)
    return {
        'success': result.get('success', False),
        'message': result.get('message', 'Done.'),
        'response_action': 'agent_executed',
        'redirect_to': '/cart' if result.get('success') else None,
        'agent_result': result,
    }


def handle_update_cart_item(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """UPDATE_CART_ITEM → remove_item then add_item with new quantity."""
    product_id = params.get('product_id')
    quantity = int(params.get('quantity', 1))
    if not product_id or quantity < 1:
        return {
            'success': False,
            'message': context.get('llm_message') or "Please specify the product and the new quantity.",
            'response_action': None,
            'redirect_to': None,
        }
    user = _get_current_user()
    allowed, err_msg = can_execute_action('remove_item', {'product_id': product_id}, user)
    if not allowed:
        return {
            'success': False,
            'message': err_msg or "I can't do that.",
            'response_action': 'agent_executed',
            'redirect_to': None,
            'denied': True,
        }
    execute_action('remove_item', {'product_id': product_id})
    add_result = execute_action('add_item', {'product_id': product_id, 'quantity': quantity})
    return {
        'success': add_result.get('success', False),
        'message': context.get('llm_message') or ("Updated quantity to {}.".format(quantity) if add_result.get('success') else add_result.get('message', "Could not update cart.")),
        'response_action': 'agent_executed',
        'redirect_to': '/cart' if add_result.get('success') else None,
        'agent_result': add_result,
    }


def handle_add_to_wishlist(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """ADD_TO_WISHLIST → tool_executor.execute_tool('wishlist_add')."""
    product_id = params.get('product_id')
    if not product_id:
        return {
            'success': True,
            'message': context.get('llm_message') or "Which product would you like to add to your wishlist? Please give me the product number.",
            'response_action': None,
            'redirect_to': None,
            'needs_clarification': True,
        }
    result = execute_tool('wishlist_add', {'product_id': int(product_id)})
    return {
        'success': result.get('success', False),
        'message': result.get('message', 'Done.') if result.get('success') else result.get('message', "Could not add to wishlist."),
        'response_action': 'agent_executed',
        'redirect_to': '/wishlist' if result.get('success') else None,
    }


def handle_remove_from_wishlist(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """REMOVE_FROM_WISHLIST → tool_executor.execute_tool('wishlist_remove')."""
    product_id = params.get('product_id')
    if not product_id:
        return {
            'success': True,
            'message': context.get('llm_message') or "Which product should I remove from your wishlist? Please give me the product number.",
            'response_action': None,
            'redirect_to': None,
            'needs_clarification': True,
        }
    result = execute_tool('wishlist_remove', {'product_id': int(product_id)})
    return {
        'success': result.get('success', False),
        'message': result.get('message', 'Done.') if result.get('success') else result.get('message', "Could not remove from wishlist."),
        'response_action': 'agent_executed',
        'redirect_to': None,
    }


def handle_view_wishlist(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """VIEW_WISHLIST → tool_executor.execute_tool('wishlist_view')."""
    result = execute_tool('wishlist_view', {})
    if result.get('success'):
        count = result.get('count', 0)
        return {
            'success': True,
            'message': context.get('llm_message') or "Your wishlist has {} item(s).".format(count),
            'response_action': 'agent_executed',
            'redirect_to': '/wishlist',
        }
    return {
        'success': False,
        'message': result.get('message', "Could not load wishlist."),
        'response_action': 'agent_executed',
        'redirect_to': None,
    }


def handle_search_products(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """SEARCH_PRODUCTS → tool_executor.execute_tool('search_products')."""
    search_params = {
        'query': (params.get('query') or params.get('search') or '').strip() or None,
        'category': (params.get('category') or '').strip().lower() or None,
        'color': (params.get('color') or '').strip() or None,
        'size': (params.get('size') or '').strip() or None,
        'fabric': (params.get('fabric') or '').strip() or None,
        'season': (params.get('season') or '').strip() or None,
        'clothing_category': (params.get('clothing_category') or '').strip() or None,
        'min_price': params.get('min_price'),
        'max_price': params.get('max_price'),
        'sort_by': (params.get('sort_by') or 'relevance').strip() or 'relevance',
        'on_sale': params.get('on_sale') is True,
    }
    if search_params['category'] and search_params['category'] not in ('men', 'women', 'kids'):
        search_params['category'] = None
    result = execute_tool('search_products', search_params)
    products = result.get('products') or []
    filters_used = result.get('filters_used') or {}
    ids = [p.get('id') for p in products if p.get('id')]
    if products:
        response_message = "I found {} product(s) matching your criteria.".format(len(products))
    else:
        response_message = "No products found. Try different filters or keywords."
    return {
        'success': True,
        'message': response_message,
        'response_action': 'search_results',
        'redirect_to': None,
        'products': products,
        'suggested_product_ids': ids,
        'filters_used': filters_used,
    }


def handle_compare_products(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """COMPARE_PRODUCTS → load products and build comparison text."""
    user_prompt_raw = context.get('user_prompt_raw') or ''
    message = context.get('message') or ''
    selected_product_ids = context.get('selected_product_ids') or []
    compare_ids = list(params.get('product_ids') or [])
    if not compare_ids and selected_product_ids:
        compare_ids = list(selected_product_ids)[:10]
    if not compare_ids:
        import re
        compare_ids = [int(m) for m in re.findall(r'\b(?:product\s*)?(?:#)?(\d+)\b', user_prompt_raw or message)]
    compare_ids = list(dict.fromkeys(compare_ids))[:10]
    if len(compare_ids) < 2:
        return {
            'success': False,
            'message': "Please specify at least 2 products to compare (e.g. 'compare product 1 and 2').",
            'response_action': None,
            'redirect_to': None,
            'error': 'Need at least 2 products',
        }
    products = Product.query.filter(Product.id.in_(compare_ids), Product.is_active == True).all()
    if len(products) < 2:
        return {
            'success': False,
            'message': "Could not find at least 2 valid products to compare.",
            'response_action': None,
            'redirect_to': None,
            'error': 'Not enough products found',
        }
    products_dict = [p.to_dict() for p in products]
    price_min = float(min(p.price for p in products))
    price_max = float(max(p.price for p in products))
    price_avg = float(sum(p.price for p in products) / len(products))
    best = min(products, key=lambda p: float(p.price))
    comparison_text = "I've compared {} products for you:\n\n".format(len(products))
    for i, product in enumerate(products, 1):
        comparison_text += "Product #{}: {} - ${:.2f} ({}, {})\n".format(
            product.id, product.name, float(product.price), product.category, product.color or 'N/A'
        )
    comparison_text += "\nPrice Range: ${:.2f} - ${:.2f}\n".format(price_min, price_max)
    comparison_text += "Best Value: Product #{} - {} at ${:.2f}\n".format(best.id, best.name, float(best.price))
    return {
        'success': True,
        'message': comparison_text,
        'response_action': 'compare',
        'redirect_to': None,
        'products': products_dict,
        'suggested_product_ids': [p.id for p in products],
        'compare_ids': [p.id for p in products],
    }


# Registry: internal_action -> handler function
ACTION_HANDLERS = {
    'none': handle_none,
    'redirect': handle_redirect,
    'add_item': handle_add_item,
    'remove_item': handle_remove_item,
    'show_cart': handle_show_cart,
    'clear_cart': handle_clear_cart,
    'update_cart_item': handle_update_cart_item,
    'add_to_wishlist': handle_add_to_wishlist,
    'remove_from_wishlist': handle_remove_from_wishlist,
    'view_wishlist': handle_view_wishlist,
    'search_products': handle_search_products,
    'compare_products': handle_compare_products,
}


def dispatch_action(
    internal_action: str,
    params: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Execute the backend handler for the given AI action.

    :param internal_action: Internal action name (e.g. add_item, search_products).
    :param params: Parameters from the AI JSON (parameters object).
    :param context: Optional dict with llm_message, user_prompt_raw, message, selected_product_ids, etc.
    :return: Result dict with success, message, response_action, redirect_to, and action-specific data.
    """
    context = context or {}
    handler = ACTION_HANDLERS.get(internal_action)
    if not handler:
        return {
            'success': False,
            'message': "That action isn't supported.",
            'response_action': 'agent_executed',
            'redirect_to': None,
            'error': 'Unknown action',
        }
    try:
        return handler(params, context)
    except Exception as e:
        return {
            'success': False,
            'message': str(e) if str(e) else "Something went wrong.",
            'response_action': 'agent_executed',
            'redirect_to': None,
            'error': str(e),
        }
