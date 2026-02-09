"""
AI Agent Action Executor — maps LLM JSON decisions to safe backend operations.

- Allowed actions are explicitly defined; unknown actions are rejected.
- Permission checks are enforced in code (do not trust the LLM alone).
- Product resolution: color, clothing_type, product_id from our Product model.
"""

from models.database import db
from models.product import Product
from models.cart import CartItem
from routes.auth import get_current_user_optional
from utils.guest_cart import (
    get_guest_cart,
    add_to_guest_cart,
    remove_from_guest_cart,
    clear_guest_cart,
)
from utils.color_names import normalize_color_name
from utils.spelling_tolerance import normalize_clothing_type, normalize_color_spelling
from sqlalchemy import or_
import json
import re

# ---------------------------------------------------------------------------
# Allowed actions (single source of truth — backend decides, not the LLM)
# ---------------------------------------------------------------------------
ALLOWED_ACTIONS = frozenset({
    'add_item',      # Add product(s) to cart
    'remove_item',   # Remove product(s) from cart
    'show_cart',     # Return current cart summary
    'clear_cart',    # Clear all cart items
    'none',          # No executable action
})

# Actions that require no parameters (besides implicit user/session)
NO_PARAM_ACTIONS = frozenset({'show_cart', 'clear_cart', 'none'})


def _get_current_user():
    """Get current user from request (same as routes). Returns User or None."""
    return get_current_user_optional()


def _normalize_color_for_db(color_str):
    """Map user/LLM color string to DB-friendly value (e.g. 'white' -> 'White')."""
    if not color_str or not str(color_str).strip():
        return None
    s = str(color_str).strip().lower()
    # Use project color normalization if available
    from utils.color_names import normalize_color_name
    out = normalize_color_name(s)
    if out:
        return out.capitalize() if isinstance(out, str) else out
    from utils.spelling_tolerance import normalize_color_spelling
    out = normalize_color_spelling(s)
    if out:
        return out.capitalize() if isinstance(out, str) else out
    return color_str.capitalize()


def _normalize_clothing_type_for_db(clothing_str):
    """Map user/LLM clothing type to DB value (e.g. 'shirt' -> 'Shirt', 't-shirt' -> 'T-Shirt')."""
    if not clothing_str or not str(clothing_str).strip():
        return None
    normalized = normalize_clothing_type(str(clothing_str).strip())
    if not normalized:
        return None
    if normalized == 't-shirt':
        return 'T-Shirt'
    return normalized.capitalize()


def resolve_products(color=None, clothing_type=None, category=None, product_id=None, limit=10):
    """
    Resolve products by color, clothing_type, category, or exact product_id.
    Returns list of Product models (is_active=True), up to `limit`.
    """
    query = Product.query.filter_by(is_active=True)
    if product_id is not None:
        p = query.filter_by(id=int(product_id)).first()
        return [p] if p else []
    if color:
        col = _normalize_color_for_db(color)
        if col:
            # Match Product.color or JSON available_colors
            try:
                query = query.filter(
                    or_(
                        Product.color.ilike(col),
                        Product.color.ilike(col.lower()),
                        Product.available_colors.ilike(f'%"{col}"%'),
                        Product.available_colors.ilike(f'%"{col.lower()}"%'),
                    )
                )
            except Exception:
                query = query.filter(
                    or_(
                        Product.color.ilike(col),
                        Product.color.ilike(col.lower()),
                    )
                )
    if clothing_type:
        ct = _normalize_clothing_type_for_db(clothing_type)
        if ct:
            query = query.filter(
                or_(
                    Product.clothing_type.ilike(ct),
                    Product.clothing_type.ilike(ct.lower()),
                    Product.name.ilike(f'%{ct}%'),
                    Product.clothing_category.ilike(f'%{ct}%'),
                )
            )
    if category:
        cat = (str(category).strip().lower() or '').replace(' ', '')
        if cat in ('men', 'women', 'kids'):
            query = query.filter_by(category=cat)
    products = query.limit(max(1, min(limit, 20))).all()
    return products


def parse_agent_response(text):
    """
    Parse LLM output as a single JSON object.
    Handles raw JSON or markdown code blocks (```json ... ```).
    Returns dict with 'action' and optionally 'params'; or None on parse failure.
    """
    if not text or not isinstance(text, str):
        return None
    text = text.strip()
    # Strip markdown code block if present
    if '```' in text:
        match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
        if match:
            text = match.group(1).strip()
    # Find first { ... } object
    start = text.find('{')
    if start == -1:
        return None
    depth = 0
    end = -1
    for i in range(start, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                end = i
                break
    if end == -1:
        return None
    try:
        obj = json.loads(text[start : end + 1])
        if isinstance(obj, dict) and 'action' in obj:
            return obj
    except json.JSONDecodeError:
        pass
    return None


def can_execute_action(action, params, user):
    """
    Permission check: is this user/session allowed to run this action with these params?
    - Cart actions (add_item, remove_item, show_cart, clear_cart) are allowed for everyone (guest or user).
    - Unknown actions are denied.
    """
    if action not in ALLOWED_ACTIONS:
        return False, "Action not allowed"
    if action == 'none':
        return True, None
    # All current actions are cart-related; allow both guest and authenticated
    return True, None


def execute_add_item(params, user):
    """
    Execute add_item: add product(s) to cart.
    params: product_id (optional), color (optional), clothing_type (optional), quantity (optional, default 1), size (optional), category (optional)
    If product_id is set, add that product (with optional color/size). Otherwise resolve by color + clothing_type
    and add the requested quantity to the first matching product only (e.g. "add 3 white shirts" = 3 of one white shirt).
    """
    product_id = params.get('product_id')
    color = params.get('color')
    clothing_type = params.get('clothing_type')
    category = params.get('category')
    quantity = int(params.get('quantity', 1))
    size = params.get('size')
    quantity = max(1, min(quantity, 10))
    added = []
    errors = []

    if product_id is not None:
        products = resolve_products(product_id=int(product_id), limit=1)
    else:
        products = resolve_products(color=color, clothing_type=clothing_type, category=category, limit=5)

    if not products:
        return {
            'success': False,
            'message': 'No matching products found.',
            'added': [],
        }

    # When resolved by description (no product_id), add the full quantity to one product only (e.g. "3 white shirts" = 3 of one white shirt)
    if product_id is None:
        products = products[:1]
    for product in products:
        qty = quantity
        if product.stock_quantity < qty:
            qty = product.stock_quantity
        if qty < 1:
            errors.append(f'{product.name}: out of stock')
            continue
        selected_color = _normalize_color_for_db(color) if color else None
        selected_size = str(size).strip() if size else None
        # Validate color/size against product if needed
        if selected_color and getattr(product, 'available_colors', None):
            try:
                avail = product.available_colors
                colors_list = json.loads(avail) if isinstance(avail, str) else avail
                if colors_list and selected_color not in colors_list:
                    # Try matching case-insensitively
                    if not any(c and c.lower() == selected_color.lower() for c in colors_list):
                        selected_color = colors_list[0] if colors_list else None
            except Exception:
                pass
        if selected_size and getattr(product, 'available_sizes', None):
            try:
                avail = product.available_sizes
                sizes_list = json.loads(avail) if isinstance(avail, str) else avail
                if sizes_list and selected_size not in sizes_list:
                    selected_size = sizes_list[0] if sizes_list else None
            except Exception:
                pass

        if user:
            existing = CartItem.query.filter_by(
                user_id=user.id,
                product_id=product.id,
                selected_color=selected_color,
                selected_size=selected_size,
            ).first()
            if existing:
                new_qty = min(existing.quantity + qty, product.stock_quantity)
                add_qty = new_qty - existing.quantity
                if add_qty > 0:
                    existing.quantity = new_qty
                    db.session.commit()
                    added.append({'product_id': product.id, 'name': product.name, 'quantity': add_qty})
            else:
                cart_item = CartItem(
                    user_id=user.id,
                    product_id=product.id,
                    quantity=qty,
                    selected_color=selected_color,
                    selected_size=selected_size,
                )
                db.session.add(cart_item)
                db.session.commit()
                added.append({'product_id': product.id, 'name': product.name, 'quantity': qty})
        else:
            guest_cart = get_guest_cart()
            current = sum(
                item.get('quantity', 0)
                for item in guest_cart
                if item.get('product_id') == product.id
                and item.get('selected_color') == selected_color
                and item.get('selected_size') == selected_size
            )
            can_add = min(qty, product.stock_quantity - current)
            if can_add > 0:
                add_to_guest_cart(product.id, can_add, selected_color, selected_size)
                added.append({'product_id': product.id, 'name': product.name, 'quantity': can_add})

    if errors and not added:
        return {'success': False, 'message': '; '.join(errors), 'added': []}
    return {
        'success': True,
        'message': f'Added {len(added)} item(s) to your cart.' if added else 'Nothing added (stock limit).',
        'added': added,
    }


def execute_remove_item(params, user):
    """
    Execute remove_item: remove product(s) from cart, optionally by quantity.
    params: product_id (optional), color (optional), clothing_type (optional), quantity (optional).
    If quantity is set (e.g. 1), reduce that item's quantity by that amount; remove the line only if it becomes 0.
    If quantity is omitted, remove all matching items (entire line).
    When resolving by color/clothing_type, only the first matching product is used (one cart line).
    """
    product_id = params.get('product_id')
    color = params.get('color')
    clothing_type = params.get('clothing_type')
    quantity = params.get('quantity')  # None = remove all; 1 = remove one unit, etc.
    if quantity is not None:
        quantity = max(1, int(quantity))
    removed = []
    total_units_removed = 0

    if product_id is not None:
        products = resolve_products(product_id=int(product_id), limit=1)
    else:
        products = resolve_products(color=color, clothing_type=clothing_type, limit=1)

    if not products:
        return {
            'success': True,
            'message': 'No matching product in your cart.',
            'removed': [],
        }

    product = products[0]
    sel_color = _normalize_color_for_db(color) if color else None
    sel_size = None

    if user:
        items = CartItem.query.filter_by(user_id=user.id, product_id=product.id).all()
        # Match color/size if we have them
        for item in items:
            if sel_color is not None and item.selected_color != sel_color:
                continue
            if sel_size is not None and item.selected_size != sel_size:
                continue
            current = item.quantity
            to_remove = quantity if quantity is not None else current
            if to_remove >= current:
                total_units_removed += current
                db.session.delete(item)
                removed.append({'product_id': product.id, 'name': product.name, 'quantity': current})
            else:
                item.quantity = current - to_remove
                total_units_removed += to_remove
                removed.append({'product_id': product.id, 'name': product.name, 'quantity': to_remove})
            break  # only one matching line
        db.session.commit()
    else:
        units = remove_from_guest_cart(product.id, sel_color, sel_size, quantity=quantity)
        if units > 0:
            total_units_removed = units
            removed.append({'product_id': product.id, 'name': product.name, 'quantity': units})

    msg = f'Removed {total_units_removed} item(s) from your cart.' if total_units_removed else 'No matching item found in your cart.'
    return {
        'success': True,
        'message': msg,
        'removed': removed,
    }


def execute_show_cart(user):
    """Return current cart summary (items count and total). Uses same logic as GET /api/cart."""
    if user:
        items = CartItem.query.filter_by(user_id=user.id).all()
        total = 0.0
        cart_items = []
        for item in items:
            if item.product:
                try:
                    d = item.product.to_dict()
                    price = d.get('price', float(item.product.price) if item.product.price else 0.0)
                except Exception:
                    price = float(item.product.price) if item.product.price else 0.0
                total += price * item.quantity
                cart_items.append({
                    'product_id': item.product_id,
                    'name': item.product.name,
                    'quantity': item.quantity,
                    'price': float(price),
                    'subtotal': price * item.quantity,
                })
        return {
            'success': True,
            'message': f'Your cart has {len(cart_items)} item(s).',
            'count': len(cart_items),
            'total': round(total, 2),
            'items': cart_items,
            'is_guest': False,
        }
    guest_cart = get_guest_cart()
    total = 0.0
    cart_items = []
    for g in guest_cart:
        product = Product.query.get(g.get('product_id'))
        if product and product.is_active:
            price = float(product.price) if product.price else 0.0
            qty = int(g.get('quantity', 1))
            total += price * qty
            cart_items.append({
                'product_id': product.id,
                'name': product.name,
                'quantity': qty,
                'price': price,
                'subtotal': price * qty,
            })
    return {
        'success': True,
        'message': f'Your cart has {len(cart_items)} item(s).',
        'count': len(cart_items),
        'total': round(total, 2),
        'items': cart_items,
        'is_guest': True,
    }


def execute_clear_cart(user):
    """Clear all items from cart."""
    if user:
        CartItem.query.filter_by(user_id=user.id).delete()
        db.session.commit()
    else:
        clear_guest_cart()
    return {'success': True, 'message': 'Your cart has been cleared.', 'cleared': True}


def execute_action(action, params):
    """
    Execute the given action with params. Uses current Flask request for user/session.
    Returns a result dict with success, message, and action-specific data.
    """
    user = _get_current_user()

    if action == 'none':
        return {'success': True, 'message': 'No action to perform.', 'action': 'none'}

    if action == 'add_item':
        return execute_add_item(params or {}, user)
    if action == 'remove_item':
        return execute_remove_item(params or {}, user)
    if action == 'show_cart':
        return execute_show_cart(user)
    if action == 'clear_cart':
        return execute_clear_cart(user)

    return {'success': False, 'message': 'Unknown action.', 'action': action}
