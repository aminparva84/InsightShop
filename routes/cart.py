from flask import Blueprint, request, jsonify, session
from models.database import db
from models.cart import CartItem
from models.product import Product
from routes.auth import require_auth
from sqlalchemy.orm import joinedload
from utils.guest_cart import (
    get_guest_cart, add_to_guest_cart, update_guest_cart_item,
    remove_from_guest_cart, clear_guest_cart
)

cart_bp = Blueprint('cart', __name__)

@cart_bp.route('', methods=['GET'])
def get_cart():
    """Get cart items (authenticated or guest)."""
    try:
        # Check if user is authenticated
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            try:
                from routes.auth import verify_jwt_token
                token = auth_header[7:]
                payload = verify_jwt_token(token)
                if payload:
                    from models.user import User
                    user = User.query.get(payload['user_id'])
                    if user:
                        cart_items = CartItem.query.filter_by(user_id=user.id).all()
                        total = sum(item.product.price * item.quantity for item in cart_items if item.product)
                        return jsonify({
                            'items': [item.to_dict() for item in cart_items],
                            'total': float(total),
                            'is_guest': False
                        }), 200
            except:
                pass
        
        # Guest cart
        guest_cart = get_guest_cart()
        items = []
        total = 0.0
        
        for cart_item in guest_cart:
            product = Product.query.get(cart_item['product_id'])
            if product and product.is_active:
                item_total = float(product.price) * cart_item['quantity']
                total += item_total
                items.append({
                    'id': f"guest_{cart_item['product_id']}",
                    'product_id': cart_item['product_id'],
                    'product': product.to_dict(),
                    'quantity': cart_item['quantity'],
                    'selected_color': cart_item.get('selected_color'),
                    'selected_size': cart_item.get('selected_size'),
                    'subtotal': item_total
                })
        
        return jsonify({
            'items': items,
            'total': total,
            'is_guest': True
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cart_bp.route('', methods=['POST'])
def add_to_cart():
    """Add item to cart (authenticated or guest)."""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        selected_color = data.get('selected_color')
        selected_size = data.get('selected_size')
        
        if not product_id:
            return jsonify({'error': 'Product ID is required'}), 400
        
        product = Product.query.get(product_id)
        if not product or not product.is_active:
            return jsonify({'error': 'Product not found'}), 404
        
        # If color/size specified, try to find matching product variant
        if selected_color or selected_size:
            # Find product with matching color and size
            query = Product.query.filter_by(
                category=product.category,
                is_active=True
            )
            
            # Extract base product name (remove color from name)
            base_name_parts = product.name.split(' for ')
            if len(base_name_parts) > 1:
                base_name = base_name_parts[1] if len(base_name_parts) > 1 else product.name
            else:
                # Try to extract clothing type
                for clothing_type in ['T-Shirt', 'Polo Shirt', 'Dress Shirt', 'Jeans', 'Chinos', 'Shorts', 
                                     'Blouse', 'Dress', 'Skirt', 'Leggings', 'Hoodie', 'Sweater', 
                                     'Jacket', 'Blazer', 'Coat', 'Suit', 'Shoes', 'Sneakers', 'Heels', 
                                     'Sandals', 'Pajamas']:
                    if clothing_type in product.name:
                        base_name = clothing_type
                        break
                else:
                    base_name = product.name
            
            if selected_color:
                query = query.filter_by(color=selected_color)
            if selected_size:
                query = query.filter_by(size=selected_size)
            
            # Try to find matching variant
            variant = query.first()
            if variant:
                product = variant
                product_id = variant.id
        
        if product.stock_quantity < quantity:
            return jsonify({'error': 'Insufficient stock'}), 400
        
        # Check if user is authenticated
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            try:
                from routes.auth import verify_jwt_token
                token = auth_header[7:]
                payload = verify_jwt_token(token)
                if payload:
                    from models.user import User
                    user = User.query.get(payload['user_id'])
                    if user:
                        # Authenticated user
                        existing_item = CartItem.query.filter_by(
                            user_id=user.id,
                            product_id=product_id,
                            selected_color=selected_color,
                            selected_size=selected_size
                        ).first()
                        
                        if existing_item:
                            existing_item.quantity += quantity
                            if existing_item.quantity > product.stock_quantity:
                                return jsonify({'error': 'Insufficient stock'}), 400
                        else:
                            cart_item = CartItem(
                                user_id=user.id,
                                product_id=product_id,
                                quantity=quantity,
                                selected_color=selected_color,
                                selected_size=selected_size
                            )
                            db.session.add(cart_item)
                        
                        db.session.commit()
                        return jsonify({'message': 'Item added to cart'}), 200
            except:
                pass
        
        # Guest cart
        add_to_guest_cart(product_id, quantity, selected_color, selected_size)
        return jsonify({'message': 'Item added to cart'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@cart_bp.route('/<item_id>', methods=['PUT'])
def update_cart_item(item_id):
    """Update cart item quantity (authenticated or guest)."""
    try:
        data = request.get_json()
        quantity = int(data.get('quantity', 1))
        
        if quantity < 1:
            return jsonify({'error': 'Quantity must be at least 1'}), 400
        
        # Check if guest cart item
        if item_id.startswith('guest_'):
            product_id = int(item_id.replace('guest_', ''))
            product = Product.query.get(product_id)
            if not product:
                return jsonify({'error': 'Product not found'}), 404
            if product.stock_quantity < quantity:
                return jsonify({'error': 'Insufficient stock'}), 400
            
            update_guest_cart_item(product_id, quantity)
            return jsonify({'message': 'Cart item updated'}), 200
        
        # Authenticated user
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authentication required'}), 401
        
        from routes.auth import verify_jwt_token
        token = auth_header[7:]
        payload = verify_jwt_token(token)
        if not payload:
            return jsonify({'error': 'Invalid token'}), 401
        
        from models.user import User
        user = User.query.get(payload['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 401
        
        cart_item = CartItem.query.filter_by(id=int(item_id), user_id=user.id).first_or_404()
        product = Product.query.get(cart_item.product_id)
        if product and product.stock_quantity < quantity:
            return jsonify({'error': 'Insufficient stock'}), 400
        
        cart_item.quantity = quantity
        db.session.commit()
        
        return jsonify({'message': 'Cart item updated', 'item': cart_item.to_dict()}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@cart_bp.route('/<item_id>', methods=['DELETE'])
def remove_from_cart(item_id):
    """Remove item from cart (authenticated or guest)."""
    try:
        # Check if guest cart item
        if item_id.startswith('guest_'):
            product_id = int(item_id.replace('guest_', ''))
            remove_from_guest_cart(product_id)
            return jsonify({'message': 'Item removed from cart'}), 200
        
        # Authenticated user
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authentication required'}), 401
        
        from routes.auth import verify_jwt_token
        token = auth_header[7:]
        payload = verify_jwt_token(token)
        if not payload:
            return jsonify({'error': 'Invalid token'}), 401
        
        from models.user import User
        user = User.query.get(payload['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 401
        
        cart_item = CartItem.query.filter_by(id=int(item_id), user_id=user.id).first_or_404()
        db.session.delete(cart_item)
        db.session.commit()
        
        return jsonify({'message': 'Item removed from cart'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@cart_bp.route('/clear', methods=['DELETE'])
def clear_cart():
    """Clear all items from cart (authenticated or guest)."""
    try:
        # Check if authenticated
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            try:
                from routes.auth import verify_jwt_token
                token = auth_header[7:]
                payload = verify_jwt_token(token)
                if payload:
                    from models.user import User
                    user = User.query.get(payload['user_id'])
                    if user:
                        CartItem.query.filter_by(user_id=user.id).delete()
                        db.session.commit()
                        return jsonify({'message': 'Cart cleared'}), 200
            except:
                pass
        
        # Guest cart
        clear_guest_cart()
        return jsonify({'message': 'Cart cleared'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

