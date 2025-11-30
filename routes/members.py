from flask import Blueprint, request, jsonify
from models.database import db
from models.order import Order
from models.payment import Payment
from routes.auth import require_auth

members_bp = Blueprint('members', __name__)

@members_bp.route('/orders', methods=['GET'])
@require_auth
def get_member_orders():
    """Get all orders for the current user."""
    try:
        user = request.current_user
        
        orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()
        
        return jsonify({
            'orders': [order.to_dict() for order in orders],
            'total_orders': len(orders)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@members_bp.route('/payments', methods=['GET'])
@require_auth
def get_member_payments():
    """Get all payments for the current user."""
    try:
        user = request.current_user
        
        # Get all user orders
        orders = Order.query.filter_by(user_id=user.id).all()
        order_ids = [order.id for order in orders]
        
        # Get all payments for those orders
        payments = Payment.query.filter(Payment.order_id.in_(order_ids)).order_by(Payment.created_at.desc()).all()
        
        # Group payments by order
        payments_by_order = {}
        for payment in payments:
            if payment.order_id not in payments_by_order:
                payments_by_order[payment.order_id] = []
            payments_by_order[payment.order_id].append(payment.to_dict())
        
        return jsonify({
            'payments': [payment.to_dict() for payment in payments],
            'payments_by_order': payments_by_order,
            'total_payments': len(payments),
            'total_spent': sum(float(p.amount) for p in payments if p.status == 'completed')
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@members_bp.route('/dashboard', methods=['GET'])
@require_auth
def get_member_dashboard():
    """Get member dashboard data."""
    try:
        user = request.current_user
        
        # Get orders
        orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()
        
        # Get payments
        order_ids = [order.id for order in orders]
        payments = Payment.query.filter(Payment.order_id.in_(order_ids)).all()
        
        # Calculate statistics
        total_spent = sum(float(p.amount) for p in payments if p.status == 'completed')
        total_orders = len(orders)
        pending_orders = len([o for o in orders if o.status in ['pending', 'processing']])
        
        return jsonify({
            'user': user.to_dict(),
            'statistics': {
                'total_orders': total_orders,
                'pending_orders': pending_orders,
                'total_spent': total_spent,
                'completed_orders': len([o for o in orders if o.status == 'delivered'])
            },
            'recent_orders': [order.to_dict() for order in orders[:5]],
            'recent_payments': [payment.to_dict() for payment in payments[:5]]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

