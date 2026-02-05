"""AI agent cart operations - allows AI to add items to cart."""
from flask import Blueprint, request, jsonify
from models.database import db
from models.product import Product
from models.cart import CartItem
from routes.auth import get_current_user_optional
from utils.guest_cart import get_guest_cart, add_to_guest_cart
import re

ai_cart_bp = Blueprint('ai_cart', __name__)

def parse_product_id_from_text(text):
    """Extract product ID from text."""
    # Matches "product 123", "product #123", "#123", "id 123"
    match = re.search(r'(?:product\s*#?|id\s*|#)(\d+)', text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None

def parse_color_from_text(text):
    """Extract color from text."""
    colors = ['red', 'blue', 'green', 'yellow', 'black', 'white', 'gray', 'grey', 'pink', 
              'purple', 'orange', 'brown', 'navy', 'beige', 'maroon', 'teal']
    text_lower = text.lower()
    for color in colors:
        if color in text_lower:
            return color.capitalize()
    return None

def parse_size_from_text(text):
    """Extract size from text."""
    sizes = ['xs', 's', 'm', 'l', 'xl', 'xxl', 'small', 'medium', 'large', 'extra large']
    text_lower = text.lower()
    size_map = {
        'small': 'S',
        'medium': 'M',
        'large': 'L',
        'extra large': 'XL'
    }
    for size in sizes:
        if size in text_lower:
            return size_map.get(size, size.upper())
    return None

@ai_cart_bp.route('/add', methods=['POST'])
def ai_add_to_cart():
    """Allow AI to add items to cart with color/size selection."""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        color = data.get('color')
        size = data.get('size')
        quantity = int(data.get('quantity', 1))
        
        if not product_id:
            return jsonify({'error': 'Product ID is required'}), 400
        
        product = Product.query.get(product_id)
        if not product or not product.is_active:
            return jsonify({'error': 'Product not found'}), 404
        
        # If color/size specified, try to find matching variant
        final_product_id = product_id
        if color or size:
            query = Product.query.filter_by(
                category=product.category,
                is_active=True
            )
            
            if color:
                query = query.filter_by(color=color)
            if size:
                query = query.filter_by(size=size)
            
            variant = query.first()
            if variant:
                final_product_id = variant.id
                product = variant
        
        if quantity < 1:
            return jsonify({'error': 'Quantity must be at least 1'}), 400
        if product.stock_quantity < quantity:
            return jsonify({'error': 'Insufficient stock'}), 400
        
        # Get user (authenticated or guest)
        user = get_current_user_optional()
        
        if user:
            # Authenticated user: enforce (existing + new) <= stock
            existing_item = CartItem.query.filter_by(
                user_id=user.id,
                product_id=final_product_id,
                selected_color=color,
                selected_size=size
            ).first()
            
            if existing_item:
                new_total = existing_item.quantity + quantity
                if new_total > product.stock_quantity:
                    return jsonify({'error': 'Insufficient stock'}), 400
                quantity = min(quantity, product.stock_quantity - existing_item.quantity)
                existing_item.quantity += quantity
            else:
                cart_item = CartItem(
                    user_id=user.id,
                    product_id=final_product_id,
                    quantity=quantity,
                    selected_color=color,
                    selected_size=size
                )
                db.session.add(cart_item)
            db.session.commit()
        else:
            # Guest cart: enforce total in cart + new <= stock
            guest_cart = get_guest_cart()
            current_in_cart = sum(
                item.get('quantity', 0)
                for item in guest_cart
                if (item.get('product_id') == final_product_id
                    and item.get('selected_color') == color
                    and item.get('selected_size') == size)
            )
            if current_in_cart + quantity > product.stock_quantity:
                return jsonify({'error': 'Insufficient stock'}), 400
            quantity = min(quantity, product.stock_quantity - current_in_cart)
            add_to_guest_cart(final_product_id, quantity, color, size)
        
        return jsonify({
            'message': f'Added {quantity} {product.name} to cart',
            'product_id': final_product_id,
            'color': color,
            'size': size
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

