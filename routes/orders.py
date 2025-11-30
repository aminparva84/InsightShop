from flask import Blueprint, request, jsonify, session
from models.database import db
from models.order import Order, OrderItem
from models.cart import CartItem
from models.user import User
from routes.auth import require_auth
from utils.guest_cart import get_guest_cart
from utils.email import send_order_confirmation_email
from decimal import Decimal
import bcrypt

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('', methods=['POST'])
def create_order():
    """Create a new order from cart (authenticated or guest)."""
    try:
        data = request.get_json()
        
        # Get user (authenticated or guest)
        user = None
        is_guest = True
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Bearer '):
            try:
                from routes.auth import verify_jwt_token
                token = auth_header[7:]
                payload = verify_jwt_token(token)
                if payload:
                    user = User.query.get(payload['user_id'])
                    if user:
                        is_guest = False
            except:
                pass
        
        # Get cart items
        cart_items_data = []
        if user and not is_guest:
            # Authenticated user
            cart_items = CartItem.query.filter_by(user_id=user.id).all()
            for cart_item in cart_items:
                if cart_item.product and cart_item.product.is_active:
                    cart_items_data.append({
                        'product': cart_item.product,
                        'quantity': cart_item.quantity,
                        'price': cart_item.product.price
                    })
        else:
            # Guest cart
            guest_cart = get_guest_cart()
            for cart_item in guest_cart:
                product = Product.query.get(cart_item['product_id'])
                if product and product.is_active:
                    cart_items_data.append({
                        'product': product,
                        'quantity': cart_item['quantity'],
                        'price': product.price
                    })
        
        if not cart_items_data:
            return jsonify({'error': 'Cart is empty'}), 400
        
        # Shipping information
        shipping_name = data.get('shipping_name', '')
        shipping_address = data.get('shipping_address', '')
        shipping_city = data.get('shipping_city', '')
        shipping_state = data.get('shipping_state', '')
        shipping_zip = data.get('shipping_zip', '')
        shipping_country = data.get('shipping_country', 'USA')
        shipping_phone = data.get('shipping_phone', '')
        
        if not all([shipping_name, shipping_address, shipping_city, shipping_state, shipping_zip]):
            return jsonify({'error': 'Shipping information is required'}), 400
        
        # Calculate totals
        subtotal = Decimal('0.00')
        order_items_data = []
        
        for cart_item in cart_items:
            if not cart_item.product or not cart_item.product.is_active:
                continue
            
            if cart_item.product.stock_quantity < cart_item.quantity:
                return jsonify({'error': f'Insufficient stock for {cart_item.product.name}'}), 400
            
            item_total = Decimal(str(cart_item.product.price)) * cart_item.quantity
            subtotal += item_total
            
            order_items_data.append({
                'product': cart_item.product,
                'quantity': cart_item.quantity,
                'price': cart_item.product.price
            })
        
        # Calculate tax (8% example)
        tax = subtotal * Decimal('0.08')
        
        # Calculate shipping (free over $50, otherwise $5)
        shipping_cost = Decimal('0.00') if subtotal >= Decimal('50.00') else Decimal('5.00')
        
        total = subtotal + tax + shipping_cost
        
        # Create order
        order = Order(
            user_id=user.id if user else None,
            guest_email=email if is_guest else None,
            shipping_name=shipping_name,
            shipping_address=shipping_address,
            shipping_city=shipping_city,
            shipping_state=shipping_state,
            shipping_zip=shipping_zip,
            shipping_country=shipping_country,
            shipping_phone=shipping_phone,
            subtotal=subtotal,
            tax=tax,
            shipping_cost=shipping_cost,
            total=total
        )
        
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        # Create order items and update stock
        for item_data in order_items_data:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data['product'].id,
                quantity=item_data['quantity'],
                price=item_data['price']
            )
            db.session.add(order_item)
            
            # Update product stock
            item_data['product'].stock_quantity -= item_data['quantity']
        
        # Clear cart
        if user and not is_guest:
            CartItem.query.filter_by(user_id=user.id).delete()
        else:
            from utils.guest_cart import clear_guest_cart
            clear_guest_cart()
        
        db.session.commit()
        
        # Send order confirmation email
        try:
            send_order_confirmation_email(email, shipping_name, order)
        except Exception as e:
            print(f"Error sending order confirmation email: {e}")
        
        return jsonify({
            'message': 'Order created successfully',
            'order': order.to_dict(),
            'email_sent': True
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@orders_bp.route('', methods=['GET'])
@require_auth
def get_orders():
    """Get user's orders."""
    try:
        user = request.current_user
        orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()
        
        return jsonify({
            'orders': [order.to_dict() for order in orders]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orders_bp.route('/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Get a single order (works for both authenticated and guest orders)."""
    try:
        from routes.auth import get_current_user_optional
        user = get_current_user_optional()
        
        if user:
            # Authenticated user - can only see their own orders
            order = Order.query.filter_by(id=order_id, user_id=user.id).first()
        else:
            # Guest order - allow access if order exists (for confirmation page)
            # In production, you might want to add email verification
            order = Order.query.filter_by(id=order_id).first()
        
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        return jsonify({'order': order.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

