from flask import Blueprint, request, jsonify
from models.database import db
from models.return_model import Return
from models.order import Order, OrderItem
from models.user import User
from datetime import datetime, timedelta
import uuid

returns_bp = Blueprint('returns', __name__)

@returns_bp.route('/initiate', methods=['POST'])
def initiate_return():
    """
    Initiate a return (RMA - Return Merchandise Authorization).
    Inputs: order_id, item_id, reason (enum: "Wrong Size", "Damaged", "Changed Mind")
    Logic: Check if order is < 30 days old. If yes, approve and generate return label.
    Output: Return approval message with printable shipping label URL.
    """
    try:
        data = request.get_json()
        order_id = data.get('order_id')
        item_id = data.get('item_id')
        reason = data.get('reason', '').strip()
        
        # Validate inputs
        if not order_id:
            return jsonify({'error': 'order_id is required'}), 400
        
        if not item_id:
            return jsonify({'error': 'item_id is required'}), 400
        
        if not reason:
            return jsonify({'error': 'reason is required'}), 400
        
        # Validate reason enum
        valid_reasons = ['Wrong Size', 'Damaged', 'Changed Mind']
        if reason not in valid_reasons:
            return jsonify({
                'error': f'reason must be one of: {", ".join(valid_reasons)}'
            }), 400
        
        # Convert IDs to int
        try:
            order_id = int(order_id)
            item_id = int(item_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid order_id or item_id format'}), 400
        
        # Get order
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        # Get order item
        order_item = OrderItem.query.filter_by(
            id=item_id,
            order_id=order_id
        ).first()
        
        if not order_item:
            return jsonify({'error': 'Order item not found'}), 404
        
        # Check if order is < 30 days old
        order_date = order.created_at
        if not order_date:
            return jsonify({'error': 'Order date not available'}), 500
        
        days_since_order = (datetime.utcnow() - order_date).days
        
        if days_since_order > 30:
            return jsonify({
                'success': False,
                'message': "I'm sorry, but this order is outside our 30-day return window. Would you like to speak to a human agent?",
                'days_since_order': days_since_order,
                'return_window_days': 30
            }), 400
        
        # Check if return already exists for this item
        existing_return = Return.query.filter_by(
            order_id=order_id,
            order_item_id=item_id
        ).first()
        
        if existing_return:
            return jsonify({
                'success': True,
                'message': 'A return has already been initiated for this item.',
                'return': existing_return.to_dict()
            }), 200
        
        # Create return
        return_obj = Return(
            order_id=order_id,
            order_item_id=item_id,
            user_id=order.user_id,
            guest_email=order.guest_email,
            reason=reason,
            status='approved'
        )
        
        # Generate mock return label URL
        return_label_id = str(uuid.uuid4())
        return_obj.return_label_url = f'/api/returns/labels/{return_label_id}.pdf'
        
        db.session.add(return_obj)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Return approved! Here is your printable shipping label: {return_obj.return_label_url}. Please drop it off at any UPS location.',
            'return': return_obj.to_dict(),
            'return_label_url': return_obj.return_label_url,
            'days_since_order': days_since_order
        }), 201
        
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"Error in initiate_return: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@returns_bp.route('/<int:return_id>', methods=['GET'])
def get_return(return_id):
    """Get return details by ID."""
    try:
        return_obj = Return.query.get(return_id)
        
        if not return_obj:
            return jsonify({'error': 'Return not found'}), 404
        
        return jsonify({
            'success': True,
            'return': return_obj.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

