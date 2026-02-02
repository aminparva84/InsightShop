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
        
        # Get cart items and calculate prices using sale prices
        cart_items_data = []
        if user and not is_guest:
            # Authenticated user
            cart_items = CartItem.query.filter_by(user_id=user.id).all()
            for cart_item in cart_items:
                if cart_item.product and cart_item.product.is_active:
                    # Get sale price if available
                    try:
                        product_dict = cart_item.product.to_dict()
                        current_price = product_dict.get('price', float(cart_item.product.price) if cart_item.product.price else 0.0)
                    except Exception:
                        current_price = float(cart_item.product.price) if cart_item.product.price else 0.0
                    
                    cart_items_data.append({
                        'product': cart_item.product,
                        'quantity': cart_item.quantity,
                        'price': Decimal(str(current_price))  # Use sale price if on sale
                    })
        else:
            # Guest cart
            from models.product import Product
            guest_cart = get_guest_cart()
            for cart_item in guest_cart:
                product = Product.query.get(cart_item['product_id'])
                if product and product.is_active:
                    # Get sale price if available
                    try:
                        product_dict = product.to_dict()
                        current_price = product_dict.get('price', float(product.price) if product.price else 0.0)
                    except Exception:
                        current_price = float(product.price) if product.price else 0.0
                    
                    cart_items_data.append({
                        'product': product,
                        'quantity': cart_item['quantity'],
                        'price': Decimal(str(current_price))  # Use sale price if on sale
                    })
        
        if not cart_items_data:
            return jsonify({'error': 'Cart is empty'}), 400
        
        # Shipping information
        email = data.get('email', '')
        shipping_name = data.get('shipping_name', '')
        shipping_address = data.get('shipping_address', '')
        shipping_city = data.get('shipping_city', '')
        shipping_state = data.get('shipping_state', '')
        shipping_zip = data.get('shipping_zip', '')
        shipping_country = data.get('shipping_country', 'USA')
        shipping_phone = data.get('shipping_phone', '')
        
        if not all([shipping_name, shipping_address, shipping_city, shipping_state, shipping_zip]):
            return jsonify({'error': 'Shipping information is required'}), 400
        
        # Calculate totals using sale prices
        subtotal = Decimal('0.00')
        order_items_data = []
        
        for item_data in cart_items_data:
            product = item_data['product']
            quantity = item_data['quantity']
            price = item_data['price']  # Already includes sale price if applicable
            
            if product.stock_quantity < quantity:
                return jsonify({'error': f'Insufficient stock for {product.name}'}), 400
            
            item_total = price * quantity
            subtotal += item_total
            
            order_items_data.append({
                'product': product,
                'quantity': quantity,
                'price': price  # Store sale price at time of order
            })
        
        # Calculate tax (8% example)
        tax = subtotal * Decimal('0.08')
        
        # Calculate shipping - use API if shipping method provided, otherwise use default
        shipping_method = data.get('shipping_method', 'Standard Shipping')
        shipping_carrier = data.get('shipping_carrier', 'Standard')
        shipping_cost_input = data.get('shipping_cost')
        
        if shipping_cost_input is not None:
            # Use provided shipping cost from API
            shipping_cost = Decimal(str(shipping_cost_input))
        else:
            # Fallback to default calculation (free over $50, otherwise $5)
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
        
        # Cart is cleared only after successful payment (see routes/payments.py)
        
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

@orders_bp.route('/status', methods=['POST'])
def get_order_status():
    """
    Get order status by order_id and email validation.
    Input: order_id (string), email (string)
    Output: Current status, order date, and list of items
    """
    try:
        data = request.get_json()
        order_id = data.get('order_id')
        email = data.get('email', '').strip().lower()
        
        if not order_id:
            return jsonify({'error': 'order_id is required'}), 400
        
        if not email:
            return jsonify({'error': 'email is required'}), 400
        
        # Convert order_id to int if it's a string
        try:
            order_id = int(order_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid order_id format'}), 400
        
        # Query the order
        order = Order.query.filter_by(id=order_id).first()
        
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        # Validate email matches the order
        order_email = None
        if order.user_id:
            # Authenticated order - get user email
            user = User.query.get(order.user_id)
            if user:
                order_email = user.email.lower().strip()
        else:
            # Guest order - use guest_email
            order_email = (order.guest_email or '').lower().strip()
        
        if order_email != email:
            return jsonify({'error': 'Email does not match this order'}), 403
        
        # Return order status information
        return jsonify({
            'success': True,
            'order_id': order.id,
            'order_number': order.order_number,
            'status': order.status,  # Processing, Shipped, Delivered, etc.
            'order_date': order.created_at.isoformat() if order.created_at else None,
            'items': [item.to_dict() for item in order.items],
            'total': float(order.total) if order.total else 0.0,
            'shipping_address': {
                'name': order.shipping_name,
                'address': order.shipping_address,
                'city': order.shipping_city,
                'state': order.shipping_state,
                'zip': order.shipping_zip,
                'country': order.shipping_country
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orders_bp.route('/track', methods=['POST'])
def track_shipment():
    """
    Track shipment by tracking number (mock implementation).
    Input: tracking_number (string)
    Output: Human-readable status update
    """
    try:
        data = request.get_json()
        tracking_number = data.get('tracking_number', '').strip().upper()
        
        if not tracking_number:
            return jsonify({'error': 'tracking_number is required'}), 400
        
        # Check if tracking number exists in shipments table
        try:
            from models.shipment import Shipment
            shipment = Shipment.query.filter_by(tracking_number=tracking_number).first()
            
            if shipment:
                # Real shipment found
                status_messages = {
                    'pending': 'Your shipment is being prepared.',
                    'in_transit': f'Your shipment is in transit. Estimated delivery: {shipment.estimated_delivery.strftime("%B %d, %Y") if shipment.estimated_delivery else "TBD"}.',
                    'delivered': f'Your shipment was delivered on {shipment.delivered_at.strftime("%B %d, %Y at %I:%M %p") if shipment.delivered_at else "N/A"}.',
                    'exception': 'There is an exception with your shipment. Please contact customer service.'
                }
                
                message = status_messages.get(shipment.status, 'Your shipment status is being updated.')
                
                return jsonify({
                    'success': True,
                    'tracking_number': tracking_number,
                    'carrier': shipment.carrier,
                    'status': shipment.status,
                    'message': message,
                    'estimated_delivery': shipment.estimated_delivery.isoformat() if shipment.estimated_delivery else None,
                    'delivered_at': shipment.delivered_at.isoformat() if shipment.delivered_at else None
                }), 200
        except ImportError:
            # Shipment model not available, use mock logic
            pass
        
        # Mock tracking logic based on tracking number prefix
        if tracking_number.startswith('UPS'):
            return jsonify({
                'success': True,
                'tracking_number': tracking_number,
                'carrier': 'UPS',
                'status': 'in_transit',
                'message': 'In Transit - Arriving Tomorrow by 8 PM.',
                'estimated_delivery': None
            }), 200
        elif tracking_number.startswith('FEDEX') or tracking_number.startswith('FDX'):
            return jsonify({
                'success': True,
                'tracking_number': tracking_number,
                'carrier': 'FEDEX',
                'status': 'delivered',
                'message': 'Delivered at Front Porch.',
                'delivered_at': None
            }), 200
        elif tracking_number.startswith('USPS'):
            return jsonify({
                'success': True,
                'tracking_number': tracking_number,
                'carrier': 'USPS',
                'status': 'in_transit',
                'message': 'In Transit - Expected delivery in 2-3 business days.',
                'estimated_delivery': None
            }), 200
        else:
            # Generic tracking number
            return jsonify({
                'success': True,
                'tracking_number': tracking_number,
                'carrier': 'Unknown',
                'status': 'in_transit',
                'message': 'Your shipment is in transit. Please check back later for updates.',
                'estimated_delivery': None
            }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

