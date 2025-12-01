from flask import Blueprint, request, jsonify
from models.database import db
from models.payment import Payment
from models.order import Order
from routes.auth import require_auth
from config import Config
from utils.jpmorgan_payments import get_jpmorgan_client

payments_bp = Blueprint('payments', __name__)

# Initialize Stripe if configured
try:
    import stripe
    if Config.STRIPE_SECRET_KEY:
        stripe.api_key = Config.STRIPE_SECRET_KEY
except ImportError:
    stripe = None

@payments_bp.route('/create-intent', methods=['POST'])
def create_payment_intent():
    """Create a Stripe payment intent (works for authenticated and guest users)."""
    try:
        data = request.get_json()
        
        order_id = data.get('order_id')
        if not order_id:
            return jsonify({'error': 'Order ID is required'}), 400
        
        # Check if user is authenticated
        user = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            try:
                from routes.auth import verify_jwt_token
                token = auth_header[7:]
                payload = verify_jwt_token(token)
                if payload:
                    from models.user import User
                    user = User.query.get(payload['user_id'])
            except:
                pass
        
        # Get order - for authenticated users, verify ownership; for guests, allow by order_id
        if user:
            order = Order.query.filter_by(id=order_id, user_id=user.id).first_or_404()
        else:
            # Guest order - verify by order_id only (in production, add email verification)
            order = Order.query.filter_by(id=order_id).first_or_404()
        
        if order.status != 'pending':
            return jsonify({'error': 'Order is not pending payment'}), 400
        
        # Check if payment already exists
        existing_payment = Payment.query.filter_by(order_id=order_id, status='completed').first()
        if existing_payment:
            return jsonify({'error': 'Order already paid'}), 400
        
        if not Config.STRIPE_SECRET_KEY:
            # Mock payment for development
            payment = Payment(
                order_id=order.id,
                payment_method='stripe',
                amount=order.total,
                status='completed'
            )
            db.session.add(payment)
            order.status = 'processing'
            db.session.commit()
            
            return jsonify({
                'message': 'Payment processed (mock)',
                'payment': payment.to_dict()
            }), 200
        
        # Create Stripe payment intent
        intent = stripe.PaymentIntent.create(
            amount=int(float(order.total) * 100),  # Convert to cents
            currency='usd',
            metadata={
                'order_id': order.id,
                'user_id': user.id
            }
        )
        
        # Create payment record
        payment = Payment(
            order_id=order.id,
            payment_method='stripe',
            payment_intent_id=intent.id,
            amount=order.total,
            status='pending'
        )
        db.session.add(payment)
        db.session.commit()
        
        return jsonify({
            'client_secret': intent.client_secret,
            'payment': payment.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@payments_bp.route('/confirm', methods=['POST'])
def confirm_payment():
    """Confirm a payment (works for authenticated and guest users)."""
    try:
        data = request.get_json()
        
        payment_id = data.get('payment_id')
        payment_intent_id = data.get('payment_intent_id')
        
        if not payment_id and not payment_intent_id:
            return jsonify({'error': 'Payment ID or Payment Intent ID is required'}), 400
        
        # Check if user is authenticated
        user = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            try:
                from routes.auth import verify_jwt_token
                token = auth_header[7:]
                payload = verify_jwt_token(token)
                if payload:
                    from models.user import User
                    user = User.query.get(payload['user_id'])
            except:
                pass
        
        if payment_intent_id:
            payment = Payment.query.filter_by(payment_intent_id=payment_intent_id).first_or_404()
        else:
            payment = Payment.query.get_or_404(payment_id)
        
        order = Order.query.get_or_404(payment.order_id)
        
        # Verify ownership for authenticated users
        if user and order.user_id and order.user_id != user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        if not Config.STRIPE_SECRET_KEY or stripe is None:
            # Mock confirmation
            payment.status = 'completed'
            order.status = 'processing'
            db.session.commit()
            
            return jsonify({
                'message': 'Payment confirmed (mock)',
                'payment': payment.to_dict()
            }), 200
        
        # Verify with Stripe
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        if intent.status == 'succeeded':
            payment.status = 'completed'
            order.status = 'processing'
            db.session.commit()
            
            return jsonify({
                'message': 'Payment confirmed',
                'payment': payment.to_dict()
            }), 200
        else:
            return jsonify({'error': f'Payment not succeeded: {intent.status}'}), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@payments_bp.route('', methods=['GET'])
@require_auth
def get_payments():
    """Get user's payments."""
    try:
        user = request.current_user
        orders = Order.query.filter_by(user_id=user.id).all()
        order_ids = [order.id for order in orders]
        
        payments = Payment.query.filter(Payment.order_id.in_(order_ids)).order_by(Payment.created_at.desc()).all()
        
        return jsonify({
            'payments': [payment.to_dict() for payment in payments]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@payments_bp.route('/jpmorgan/token', methods=['GET'])
def get_jpmorgan_token():
    """Get J.P. Morgan Payments access token (for testing/debugging)."""
    try:
        client = get_jpmorgan_client()
        token = client._get_access_token(force_refresh=True)
        return jsonify({
            'access_token': token,
            'message': 'Token retrieved successfully'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@payments_bp.route('/jpmorgan/create-payment', methods=['POST'])
def create_jpmorgan_payment():
    """Create a payment using J.P. Morgan Payments API (works for authenticated and guest users)."""
    try:
        data = request.get_json()
        
        order_id = data.get('order_id')
        if not order_id:
            return jsonify({'error': 'Order ID is required'}), 400
        
        # Check if user is authenticated
        user = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            try:
                from routes.auth import verify_jwt_token
                token = auth_header[7:]
                payload = verify_jwt_token(token)
                if payload:
                    from models.user import User
                    user = User.query.get(payload['user_id'])
            except:
                pass
        
        # Get order - for authenticated users, verify ownership; for guests, allow by order_id
        if user:
            order = Order.query.filter_by(id=order_id, user_id=user.id).first_or_404()
        else:
            # Guest order - verify by order_id only (in production, add email verification)
            order = Order.query.filter_by(id=order_id).first_or_404()
        
        if order.status != 'pending':
            return jsonify({'error': 'Order is not pending payment'}), 400
        
        # Check if payment already exists
        existing_payment = Payment.query.filter_by(order_id=order_id, status='completed').first()
        if existing_payment:
            return jsonify({'error': 'Order already paid'}), 400
        
        # Get payment details from request
        card_number = data.get('card_number')
        expiry_month = data.get('expiry_month')
        expiry_year = data.get('expiry_year')
        
        if not card_number or not expiry_month or not expiry_year:
            return jsonify({'error': 'Card number, expiry month, and expiry year are required'}), 400
        
        # Convert order total to smallest currency unit (cents for USD)
        amount_cents = int(float(order.total) * 100)
        
        # Get J.P. Morgan Payments client
        client = get_jpmorgan_client()
        
        # Create payment request
        payment_response = client.create_payment(
            amount=amount_cents,
            currency=order.currency or 'USD',
            card_number=card_number,
            expiry_month=int(expiry_month),
            expiry_year=int(expiry_year),
            capture_method=data.get('capture_method', 'NOW'),
            merchant_company_name=data.get('merchant_company_name', 'InsightShop'),
            merchant_product_name=data.get('merchant_product_name', 'InsightShop Application'),
            merchant_version=data.get('merchant_version', '1.0.0'),
            merchant_category_code=data.get('merchant_category_code', '4899'),
            is_bill_payment=data.get('is_bill_payment', True),
            initiator_type=data.get('initiator_type', 'CARDHOLDER'),
            account_on_file=data.get('account_on_file', 'NOT_STORED'),
            is_amount_final=data.get('is_amount_final', True)
        )
        
        # Extract transaction details
        transaction_id = payment_response.get('transactionId')
        response_status = payment_response.get('responseStatus')
        response_code = payment_response.get('responseCode')
        response_message = payment_response.get('responseMessage')
        
        # Determine payment status based on response
        if response_status == 'SUCCESS' and response_code == 'APPROVED':
            payment_status = 'completed'
            order.status = 'processing'
        else:
            payment_status = 'failed'
        
        # Create payment record
        payment = Payment(
            order_id=order.id,
            payment_method='jpmorgan',
            payment_intent_id=transaction_id,  # Store transaction ID in payment_intent_id field
            amount=order.total,
            currency=order.currency or 'USD',
            status=payment_status,
            transaction_id=transaction_id
        )
        db.session.add(payment)
        db.session.commit()
        
        return jsonify({
            'message': 'Payment processed',
            'payment': payment.to_dict(),
            'jpmorgan_response': {
                'transaction_id': transaction_id,
                'response_status': response_status,
                'response_code': response_code,
                'response_message': response_message,
                'full_response': payment_response
            }
        }), 200
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@payments_bp.route('/jpmorgan/payment-status/<transaction_id>', methods=['GET'])
def get_jpmorgan_payment_status(transaction_id):
    """Get payment status from J.P. Morgan Payments API."""
    try:
        # Check if user is authenticated
        user = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            try:
                from routes.auth import verify_jwt_token
                token = auth_header[7:]
                payload = verify_jwt_token(token)
                if payload:
                    from models.user import User
                    user = User.query.get(payload['user_id'])
            except:
                pass
        
        # Get payment record
        payment = Payment.query.filter_by(transaction_id=transaction_id).first_or_404()
        order = Order.query.get_or_404(payment.order_id)
        
        # Verify ownership for authenticated users
        if user and order.user_id and order.user_id != user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get status from J.P. Morgan Payments API
        client = get_jpmorgan_client()
        status_response = client.get_payment_status(transaction_id)
        
        # Update payment status if needed
        response_status = status_response.get('responseStatus')
        response_code = status_response.get('responseCode')
        
        if response_status == 'SUCCESS' and response_code == 'APPROVED' and payment.status != 'completed':
            payment.status = 'completed'
            if order.status == 'pending':
                order.status = 'processing'
            db.session.commit()
        elif response_code and response_code != 'APPROVED' and payment.status == 'pending':
            payment.status = 'failed'
            db.session.commit()
        
        return jsonify({
            'payment': payment.to_dict(),
            'jpmorgan_status': status_response
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

