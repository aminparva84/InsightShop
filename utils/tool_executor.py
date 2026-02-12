"""
Backend tool executor for InsightShop AI assistant.

- Executes tools by name with validated arguments.
- Authorization (user vs admin) is enforced by the caller (routes) via validate_tool_call;
  this module performs the actual operations.
- Uses existing agent_executor for cart actions and DB logic for admin actions.
"""

from typing import Any, Dict, Optional
from flask import request
from models.database import db
from models.product import Product
from models.order import Order
from models.sale import Sale
from models.review import Review
from models.user import User
from utils.agent_executor import execute_action
from utils.vector_db import add_product_to_vector_db, update_product_in_vector_db, delete_product_from_vector_db
from utils.sale_automation import run_sale_automation
from sqlalchemy import or_
import json
from datetime import datetime


def _context_user():
    """Current user from request (same as agent_executor)."""
    from routes.auth import get_current_user_optional
    return get_current_user_optional()


# ---------------------------------------------------------------------------
# User tools (cart: map MCP params -> agent_executor params)
# ---------------------------------------------------------------------------

def _tool_cart_add_item(args: Dict[str, Any]) -> Dict[str, Any]:
    params = {
        'product_id': args.get('product_id'),
        'quantity': args.get('quantity', 1),
        'color': args.get('selected_color'),
        'size': args.get('selected_size'),
        'clothing_type': args.get('clothing_type'),
        'category': args.get('category'),
    }
    return execute_action('add_item', params)


def _tool_cart_remove_item(args: Dict[str, Any]) -> Dict[str, Any]:
    params = {
        'product_id': args.get('product_id'),
        'quantity': args.get('quantity'),
        'color': args.get('selected_color'),
        'size': args.get('selected_size'),
        'clothing_type': args.get('clothing_type'),
    }
    return execute_action('remove_item', params)


def _tool_cart_show(args: Dict[str, Any]) -> Dict[str, Any]:
    return execute_action('show_cart', {})


def _tool_cart_clear(args: Dict[str, Any]) -> Dict[str, Any]:
    return execute_action('clear_cart', {})


# ---------------------------------------------------------------------------
# User tools: search, compare, review, order (implement here)
# ---------------------------------------------------------------------------

def _tool_search_products(args: Dict[str, Any]) -> Dict[str, Any]:
    from utils.vector_db import search_products_vector
    query = (args.get('query') or '').strip() or None
    category = (args.get('category') or '').strip().lower() or None
    if category and category not in ('men', 'women', 'kids'):
        category = None
    size = (args.get('size') or '').strip() or None
    max_price = args.get('max_price')
    sort_by = (args.get('sort_by') or 'relevance').strip() or 'relevance'

    if query:
        product_ids = search_products_vector(query, n_results=20)
        if product_ids:
            q = Product.query.filter(Product.id.in_(product_ids), Product.is_active == True)
        else:
            q = Product.query.filter(
                or_(
                    Product.name.ilike(f'%{query}%'),
                    Product.description.ilike(f'%{query}%')
                ),
                Product.is_active == True
            )
    else:
        q = Product.query.filter_by(is_active=True)

    if category:
        q = q.filter_by(category=category)
    if size:
        q = q.filter(
            or_(
                Product.size.ilike(f'%{size}%'),
                Product.available_sizes.ilike(f'%{size}%')
            )
        )
    if max_price is not None and max_price > 0:
        q = q.filter(Product.price <= float(max_price))

    if sort_by == 'price_low':
        q = q.order_by(Product.price.asc())
    elif sort_by == 'price_high':
        q = q.order_by(Product.price.desc())
    elif sort_by == 'rating':
        q = q.order_by(Product.rating.desc().nullslast())
    products = q.limit(20).all()

    return {
        'success': True,
        'count': len(products),
        'products': [p.to_dict() for p in products],
    }


def _tool_compare_products(args: Dict[str, Any]) -> Dict[str, Any]:
    product_ids = args.get('product_ids') or []
    if len(product_ids) < 2:
        return {'success': False, 'message': 'At least 2 product IDs required.', 'products': []}
    products = Product.query.filter(Product.id.in_(product_ids[:10]), Product.is_active == True).all()
    return {
        'success': True,
        'count': len(products),
        'products': [p.to_dict() for p in products],
    }


def _tool_review_create(args: Dict[str, Any]) -> Dict[str, Any]:
    product_id = args.get('product_id')
    rating = float(args.get('rating', 0))
    comment = (args.get('comment') or '').strip()
    user_name = (args.get('user_name') or '').strip()
    user = _context_user()

    product = Product.query.get(product_id)
    if not product or not product.is_active:
        return {'success': False, 'message': 'Product not found.'}
    if not rating or rating < 1 or rating > 5:
        return {'success': False, 'message': 'Rating must be between 1 and 5.'}

    if user:
        existing = Review.query.filter_by(product_id=product_id, user_id=user.id).first()
        if existing:
            return {'success': False, 'message': 'You have already reviewed this product.'}
        review = Review(
            product_id=product_id,
            user_id=user.id,
            rating=rating,
            comment=comment or None,
            user_name=user.first_name or user.email,
        )
    else:
        review = Review(
            product_id=product_id,
            user_id=None,
            rating=rating,
            comment=comment or None,
            user_name=user_name or 'Guest',
        )
    db.session.add(review)
    db.session.commit()
    from routes.reviews import update_product_rating
    update_product_rating(product_id)
    return {'success': True, 'message': 'Review submitted.', 'review_id': review.id}


def _tool_order_status(args: Dict[str, Any]) -> Dict[str, Any]:
    order_id = args.get('order_id')
    email = (args.get('email') or '').strip().lower()
    order = Order.query.get(order_id)
    if not order:
        return {'success': False, 'message': 'Order not found.'}
    if order.guest_email and order.guest_email.lower() != email:
        return {'success': False, 'message': 'Order not found for this email.'}
    user = _context_user()
    if order.user_id and user and order.user_id != user.id:
        return {'success': False, 'message': 'Order not found.'}
    return {
        'success': True,
        'order': order.to_dict(),
        'status': order.status,
    }


def _tool_order_track(args: Dict[str, Any]) -> Dict[str, Any]:
    tracking_number = (args.get('tracking_number') or '').strip()
    if not tracking_number:
        return {'success': False, 'message': 'Tracking number is required.'}
    from models.shipment import Shipment
    shipment = Shipment.query.filter_by(tracking_number=tracking_number).first()
    if not shipment:
        return {'success': False, 'message': 'Shipment not found for this tracking number.'}
    return {
        'success': True,
        'shipment': shipment.to_dict() if hasattr(shipment, 'to_dict') else {
            'tracking_number': shipment.tracking_number,
            'status': getattr(shipment, 'status', None),
            'carrier': getattr(shipment, 'carrier', None),
        },
    }


# ---------------------------------------------------------------------------
# Admin tools (authorization checked by route; we only execute)
# ---------------------------------------------------------------------------

def _tool_admin_product_create(args: Dict[str, Any]) -> Dict[str, Any]:
    name = (args.get('name') or '').strip()
    if not name:
        return {'success': False, 'message': 'Product name is required.'}
    price = float(args.get('price', 0))
    if price < 0:
        return {'success': False, 'message': 'Price must be >= 0.'}
    category = (args.get('category') or '').strip().lower()
    if category not in ('men', 'women', 'kids'):
        return {'success': False, 'message': 'Category must be men, women, or kids.'}

    available_colors = args.get('available_colors')
    available_sizes = args.get('available_sizes')
    if isinstance(available_colors, list):
        available_colors = json.dumps(available_colors) if available_colors else None
    if isinstance(available_sizes, list):
        available_sizes = json.dumps(available_sizes) if available_sizes else None

    product = Product(
        name=name,
        description=args.get('description'),
        price=price,
        category=category,
        color=args.get('color'),
        size=args.get('size'),
        available_colors=available_colors,
        available_sizes=available_sizes,
        fabric=args.get('fabric'),
        clothing_type=args.get('clothing_type'),
        clothing_category=args.get('clothing_category') or 'other',
        stock_quantity=int(args.get('stock_quantity', 0)),
        is_active=args.get('is_active', True),
        rating=0.0,
        review_count=0,
        image_url=args.get('image_url'),
    )
    db.session.add(product)
    db.session.commit()
    try:
        add_product_to_vector_db(product.id, product.to_dict())
    except Exception:
        pass
    return {'success': True, 'message': 'Product created.', 'product': product.to_dict()}


def _tool_admin_product_prepare_create(args: Dict[str, Any]) -> Dict[str, Any]:
    """Return redirect_prefill so the admin is sent to the Add Product form with fields pre-filled. No DB write."""
    name = (args.get('name') or '').strip()
    if not name:
        return {'success': False, 'message': 'Product name is required.'}
    price = args.get('price')
    if price is None:
        return {'success': False, 'message': 'Price is required.'}
    try:
        price = float(price)
    except (TypeError, ValueError):
        return {'success': False, 'message': 'Price must be a number.'}
    category = (args.get('category') or 'men').strip().lower()
    if category not in ('men', 'women', 'kids'):
        return {'success': False, 'message': 'Category must be men, women, or kids.'}
    available_colors = args.get('available_colors')
    available_sizes = args.get('available_sizes')
    if not isinstance(available_colors, list):
        available_colors = [available_colors] if available_colors else []
    if not isinstance(available_sizes, list):
        available_sizes = [available_sizes] if available_sizes else []
    prefill = {
        'name': name,
        'description': (args.get('description') or '').strip(),
        'price': price,
        'category': category,
        'color': (args.get('color') or '').strip(),
        'size': (args.get('size') or '').strip(),
        'available_colors': available_colors,
        'available_sizes': available_sizes,
        'fabric': (args.get('fabric') or '').strip(),
        'clothing_type': (args.get('clothing_type') or '').strip(),
        'dress_style': '',
        'occasion': '',
        'age_group': '',
        'season': (args.get('season') or 'all_season').strip(),
        'clothing_category': (args.get('clothing_category') or 'other').strip(),
        'image_url': (args.get('image_url') or '').strip(),
        'stock_quantity': int(args.get('stock_quantity', 0)) if args.get('stock_quantity') is not None else 0,
        'is_active': args.get('is_active', True),
    }
    return {
        'success': True,
        'message': 'Form prepared. You will be redirected to the Add Product page to review and submit.',
        'action': 'redirect_prefill',
        'path': '/admin',
        'tab': 'products',
        'openProductForm': True,
        'prefill': prefill,
    }


def _tool_admin_product_prepare_edit(args: Dict[str, Any]) -> Dict[str, Any]:
    """Return redirect_prefill so the admin is sent to the Edit Product form with the given fields pre-filled. No DB write."""
    product_id = int(args.get('product_id'))
    product = Product.query.get(product_id)
    if not product:
        return {'success': False, 'message': 'Product not found.'}
    # Build prefill: only include fields that were explicitly provided (partial update for form)
    prefill = {}
    if 'name' in args and args['name'] is not None:
        prefill['name'] = str(args['name']).strip()
    if 'description' in args:
        prefill['description'] = (args['description'] or '').strip()
    if 'price' in args:
        try:
            prefill['price'] = float(args['price'])
        except (TypeError, ValueError):
            pass
    if 'category' in args and args['category'] in ('men', 'women', 'kids'):
        prefill['category'] = args['category']
    if 'stock_quantity' in args:
        prefill['stock_quantity'] = int(args['stock_quantity']) if args['stock_quantity'] is not None else 0
    if 'color' in args:
        prefill['color'] = (args['color'] or '').strip()
    if 'size' in args:
        prefill['size'] = (args['size'] or '').strip()
    if 'available_colors' in args:
        prefill['available_colors'] = args['available_colors'] if isinstance(args['available_colors'], list) else []
    if 'available_sizes' in args:
        prefill['available_sizes'] = args['available_sizes'] if isinstance(args['available_sizes'], list) else []
    if 'fabric' in args:
        prefill['fabric'] = (args['fabric'] or '').strip()
    if 'clothing_type' in args:
        prefill['clothing_type'] = (args['clothing_type'] or '').strip()
    if 'clothing_category' in args:
        prefill['clothing_category'] = (args['clothing_category'] or 'other').strip()
    if 'season' in args:
        prefill['season'] = (args['season'] or 'all_season').strip()
    if 'image_url' in args:
        prefill['image_url'] = (args['image_url'] or '').strip()
    if 'is_active' in args:
        prefill['is_active'] = bool(args['is_active'])
    if not prefill:
        return {'success': False, 'message': 'Provide at least one field to update (e.g. name, price, description).'}
    # Merge with current product so the form has full state; frontend will merge prefill over product
    base = product.to_dict()
    full_prefill = {
        'name': base.get('name', ''),
        'description': base.get('description', ''),
        'price': base.get('price', ''),
        'category': base.get('category', 'men'),
        'color': base.get('color', ''),
        'size': base.get('size', ''),
        'available_colors': base.get('available_colors') or [],
        'available_sizes': base.get('available_sizes') or [],
        'fabric': base.get('fabric', ''),
        'clothing_type': base.get('clothing_type', ''),
        'dress_style': base.get('dress_style', ''),
        'occasion': base.get('occasion', ''),
        'age_group': base.get('age_group', ''),
        'season': base.get('season', 'all_season'),
        'clothing_category': base.get('clothing_category', 'other'),
        'image_url': base.get('image_url', ''),
        'stock_quantity': base.get('stock_quantity', 0),
        'is_active': base.get('is_active', True),
    }
    for k, v in prefill.items():
        full_prefill[k] = v
    return {
        'success': True,
        'message': 'Edit form prepared. You will be redirected to the product edit page to review and save.',
        'action': 'redirect_prefill',
        'path': '/admin',
        'tab': 'products',
        'editProductId': product_id,
        'prefill': full_prefill,
    }


def _tool_admin_product_update(args: Dict[str, Any]) -> Dict[str, Any]:
    product_id = int(args.get('product_id'))
    product = Product.query.get(product_id)
    if not product:
        return {'success': False, 'message': 'Product not found.'}
    if 'name' in args and args['name']:
        product.name = args['name']
    if 'description' in args:
        product.description = args.get('description')
    if 'price' in args:
        product.price = float(args['price'])
    if 'category' in args and args['category'] in ('men', 'women', 'kids'):
        product.category = args['category']
    if 'stock_quantity' in args:
        product.stock_quantity = int(args['stock_quantity'])
    if 'color' in args:
        product.color = args.get('color')
    if 'size' in args:
        product.size = args.get('size')
    if 'available_colors' in args:
        v = args['available_colors']
        product.available_colors = json.dumps(v) if isinstance(v, list) else v
    if 'available_sizes' in args:
        v = args['available_sizes']
        product.available_sizes = json.dumps(v) if isinstance(v, list) else v
    if 'image_url' in args:
        product.image_url = args.get('image_url')
    if 'is_active' in args:
        product.is_active = bool(args['is_active'])
    db.session.commit()
    try:
        if product.is_active:
            update_product_in_vector_db(product_id, product.to_dict())
        else:
            delete_product_from_vector_db(product_id)
    except Exception:
        pass
    return {'success': True, 'message': 'Product updated.', 'product': product.to_dict()}


def _tool_admin_product_delete(args: Dict[str, Any]) -> Dict[str, Any]:
    product_id = int(args.get('product_id'))
    product = Product.query.get(product_id)
    if not product:
        return {'success': False, 'message': 'Product not found.'}
    product.is_active = False
    db.session.commit()
    try:
        delete_product_from_vector_db(product_id)
    except Exception:
        pass
    return {'success': True, 'message': 'Product deactivated (soft delete).'}


def _tool_admin_orders_list(args: Dict[str, Any]) -> Dict[str, Any]:
    page = int(args.get('page', 1))
    per_page = min(100, max(1, int(args.get('per_page', 50))))
    status = args.get('status')
    user_id = args.get('user_id')
    search = (args.get('search') or '').strip() or None

    query = Order.query
    if status:
        query = query.filter_by(status=status)
    if user_id:
        query = query.filter_by(user_id=user_id)
    if search:
        query = query.filter(
            or_(
                Order.order_number.ilike(f'%{search}%'),
                Order.shipping_name.ilike(f'%{search}%'),
                Order.guest_email.ilike(f'%{search}%'),
            )
        )
    pagination = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return {
        'success': True,
        'orders': [o.to_dict() for o in pagination.items],
        'pagination': {'page': page, 'per_page': per_page, 'total': pagination.total, 'pages': pagination.pages},
    }


def _tool_admin_order_update_status(args: Dict[str, Any]) -> Dict[str, Any]:
    order_id = int(args.get('order_id'))
    status = (args.get('status') or '').strip().lower()
    valid = ('pending', 'processing', 'shipped', 'delivered', 'cancelled')
    if status not in valid:
        return {'success': False, 'message': f'Status must be one of: {", ".join(valid)}'}
    order = Order.query.get(order_id)
    if not order:
        return {'success': False, 'message': 'Order not found.'}
    order.status = status
    db.session.commit()
    return {'success': True, 'message': f'Order status set to {status}.', 'order': order.to_dict()}


def _tool_admin_sale_create(args: Dict[str, Any]) -> Dict[str, Any]:
    name = (args.get('name') or '').strip()
    if not name:
        return {'success': False, 'message': 'Sale name is required.'}
    discount = float(args.get('discount_percentage', 0))
    if discount < 0 or discount > 100:
        return {'success': False, 'message': 'Discount must be between 0 and 100.'}
    start_date = args.get('start_date')
    end_date = args.get('end_date')
    if not start_date or not end_date:
        return {'success': False, 'message': 'start_date and end_date (YYYY-MM-DD) are required.'}
    try:
        start_d = datetime.strptime(start_date[:10], '%Y-%m-%d').date()
        end_d = datetime.strptime(end_date[:10], '%Y-%m-%d').date()
    except Exception:
        return {'success': False, 'message': 'Invalid date format. Use YYYY-MM-DD.'}
    sale = Sale(
        name=name,
        description=(args.get('description') or '')[:1000],
        sale_type=args.get('sale_type') or 'general',
        discount_percentage=discount,
        start_date=start_d,
        end_date=end_d,
        is_active=args.get('is_active', True),
        auto_activate=args.get('auto_activate', False),
    )
    db.session.add(sale)
    db.session.commit()
    return {'success': True, 'message': 'Sale created.', 'sale': sale.to_dict()}


def _tool_admin_sale_run_automation(args: Dict[str, Any]) -> Dict[str, Any]:
    results = run_sale_automation()
    return {'success': True, 'message': 'Sale automation run completed.', 'results': results}


def _tool_admin_cart_clear_user(args: Dict[str, Any]) -> Dict[str, Any]:
    from models.cart import CartItem
    user_id = int(args.get('user_id'))
    deleted = CartItem.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    return {'success': True, 'message': f'Cart cleared for user {user_id}.', 'items_removed': deleted}


def _tool_admin_review_delete(args: Dict[str, Any]) -> Dict[str, Any]:
    review_id = int(args.get('review_id'))
    review = Review.query.get(review_id)
    if not review:
        return {'success': False, 'message': 'Review not found.'}
    product_id = review.product_id
    db.session.delete(review)
    db.session.commit()
    from routes.reviews import update_product_rating
    update_product_rating(product_id)
    return {'success': True, 'message': 'Review deleted.'}


# ---------------------------------------------------------------------------
# Auth tools (login: delegate to auth route logic)
# ---------------------------------------------------------------------------

def _tool_auth_login(args: Dict[str, Any]) -> Dict[str, Any]:
    from routes.auth import verify_password
    from flask_jwt_extended import create_access_token
    email = (args.get('email') or '').strip().lower()
    password = (args.get('password') or '')
    if not email or not password:
        return {'success': False, 'message': 'Email and password are required.'}
    user = User.query.filter_by(email=email).first()
    if not user or not user.password_hash:
        return {'success': False, 'message': 'Invalid email or password.'}
    if not verify_password(password, user.password_hash):
        return {'success': False, 'message': 'Invalid email or password.'}
    if not user.is_verified:
        return {'success': False, 'message': 'Please verify your email before logging in.'}
    token = create_access_token(identity=user.id)
    return {
        'success': True,
        'message': 'Logged in.',
        'token': token,
        'user': user.to_dict(),
    }


def _tool_auth_logout(args: Dict[str, Any]) -> Dict[str, Any]:
    return {'success': True, 'message': 'Logged out. Please discard the token on the client.'}


# checkout_proceed is complex (shipping, payment); stub or delegate to orders
def _tool_checkout_proceed(args: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'success': False,
        'message': 'Checkout must be completed in the app. Use the checkout page with your cart.',
    }


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

_TOOL_HANDLERS = {
    'auth_login': _tool_auth_login,
    'auth_logout': _tool_auth_logout,
    'search_products': _tool_search_products,
    'cart_add_item': _tool_cart_add_item,
    'cart_remove_item': _tool_cart_remove_item,
    'cart_show': _tool_cart_show,
    'cart_clear': _tool_cart_clear,
    'compare_products': _tool_compare_products,
    'review_create': _tool_review_create,
    'checkout_proceed': _tool_checkout_proceed,
    'order_status': _tool_order_status,
    'order_track': _tool_order_track,
    'admin_product_create': _tool_admin_product_create,
    'admin_product_prepare_create': _tool_admin_product_prepare_create,
    'admin_product_prepare_edit': _tool_admin_product_prepare_edit,
    'admin_product_update': _tool_admin_product_update,
    'admin_product_delete': _tool_admin_product_delete,
    'admin_orders_list': _tool_admin_orders_list,
    'admin_order_update_status': _tool_admin_order_update_status,
    'admin_sale_create': _tool_admin_sale_create,
    'admin_sale_run_automation': _tool_admin_sale_run_automation,
    'admin_cart_clear_user': _tool_admin_cart_clear_user,
    'admin_review_delete': _tool_admin_review_delete,
}


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a tool by name with the given arguments.
    Does not perform permission checks; caller must use validate_tool_call first.
    Returns a dict with at least 'success' and 'message'; may include tool-specific data.
    """
    handler = _TOOL_HANDLERS.get(tool_name)
    if not handler:
        return {'success': False, 'message': f'Unknown tool: {tool_name}'}
    try:
        result = handler(arguments)
        return result if isinstance(result, dict) else {'success': True, 'result': result}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': str(e)}
