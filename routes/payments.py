from flask import Blueprint, request, jsonify
from models.database import db
from models.payment import Payment
from models.order import Order
from routes.auth import require_auth
from config import Config

payments_bp = Blueprint('payments', __name__)

# Initialize Stripe if configured
try:
    import stripe
    if Config.STRIPE_SECRET_KEY:
        stripe.api_key = Config.STRIPE_SECRET_KEY
except ImportError:
    stripe = None

@payments_bp.route('/create-intent', methods=['POST'])
@require_auth
def create_payment_intent():
    """Create a Stripe payment intent."""
    try:
        user = request.current_user
        data = request.get_json()
        
        order_id = data.get('order_id')
        if not order_id:
            return jsonify({'error': 'Order ID is required'}), 400
        
        order = Order.query.filter_by(id=order_id, user_id=user.id).first_or_404()
        
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
@require_auth
def confirm_payment():
    """Confirm a payment."""
    try:
        user = request.current_user
        data = request.get_json()
        
        payment_id = data.get('payment_id')
        payment_intent_id = data.get('payment_intent_id')
        
        if not payment_id and not payment_intent_id:
            return jsonify({'error': 'Payment ID or Payment Intent ID is required'}), 400
        
        if payment_intent_id:
            payment = Payment.query.filter_by(payment_intent_id=payment_intent_id).first_or_404()
        else:
            payment = Payment.query.get_or_404(payment_id)
        
        order = Order.query.get_or_404(payment.order_id)
        
        if order.user_id != user.id:
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

