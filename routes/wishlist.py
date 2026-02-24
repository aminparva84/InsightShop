"""Wishlist API: user-specific saved products. Requires authentication."""

from flask import Blueprint, request, jsonify
from models.database import db
from models.wishlist import WishlistItem
from models.product import Product
from routes.auth import require_auth

wishlist_bp = Blueprint('wishlist', __name__)


@wishlist_bp.route('', methods=['GET'])
@require_auth
def get_wishlist():
    """Get current user's wishlist with product details and notification flags."""
    user = request.current_user
    include_notifications = request.args.get('notifications', 'true').lower() in ('1', 'true', 'yes')
    items = WishlistItem.query.filter_by(user_id=user.id).order_by(WishlistItem.created_at.desc()).all()
    return jsonify({
        'items': [item.to_dict(include_notifications=include_notifications) for item in items],
        'count': len(items),
    }), 200


@wishlist_bp.route('/ids', methods=['GET'])
@require_auth
def get_wishlist_ids():
    """Return only product IDs in the wishlist (for UI to show filled heart)."""
    user = request.current_user
    items = WishlistItem.query.filter_by(user_id=user.id).all()
    ids = [item.product_id for item in items]
    return jsonify({'product_ids': ids}), 200


@wishlist_bp.route('', methods=['POST'])
@require_auth
def add_to_wishlist():
    """Add a product to the current user's wishlist."""
    user = request.current_user
    data = request.get_json() or {}
    product_id = data.get('product_id')
    if not product_id:
        return jsonify({'error': 'product_id is required'}), 400
    try:
        product_id = int(product_id)
    except (TypeError, ValueError):
        return jsonify({'error': 'product_id must be an integer'}), 400

    product = Product.query.get(product_id)
    if not product or not product.is_active:
        return jsonify({'error': 'Product not found'}), 404

    existing = WishlistItem.query.filter_by(user_id=user.id, product_id=product_id).first()
    if existing:
        return jsonify({
            'message': 'Already in wishlist',
            'item': existing.to_dict(include_notifications=True),
        }), 200

    price_when_added = float(product.price) if product.price else None
    try:
        sale = product.get_sale_price()
        if sale:
            price_when_added = sale.get('sale_price') or price_when_added
    except Exception:
        pass
    was_out_of_stock = (product.stock_quantity or 0) <= 0

    item = WishlistItem(
        user_id=user.id,
        product_id=product_id,
        price_when_added=price_when_added,
        was_out_of_stock=was_out_of_stock,
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({
        'message': 'Added to wishlist',
        'item': item.to_dict(include_notifications=True),
    }), 201


@wishlist_bp.route('/<int:product_id>', methods=['DELETE'])
@require_auth
def remove_from_wishlist(product_id):
    """Remove a product from the current user's wishlist."""
    user = request.current_user
    item = WishlistItem.query.filter_by(user_id=user.id, product_id=product_id).first()
    if not item:
        return jsonify({'error': 'Product not in wishlist'}), 404
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Removed from wishlist'}), 200
