"""Admin sales management routes."""

from flask import Blueprint, request, jsonify
from models.database import db
from models.sale import Sale
from routes.admin import require_admin
from utils.seasonal_events import get_upcoming_holidays, get_current_holidays_and_events
from datetime import date, datetime
import json

admin_sales_bp = Blueprint('admin_sales', __name__)

@admin_sales_bp.route('/sales', methods=['GET'])
@require_admin
def get_sales():
    """Get all sales."""
    try:
        sales = Sale.query.order_by(Sale.start_date.desc()).all()
        return jsonify({
            'success': True,
            'sales': [sale.to_dict() for sale in sales]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_sales_bp.route('/sales', methods=['POST'])
@require_admin
def create_sale():
    """Create a new sale."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'discount_percentage', 'start_date', 'end_date']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Create sale
        sale = Sale(
            name=data['name'],
            description=data.get('description', ''),
            sale_type=data.get('sale_type', 'general'),
            event_name=data.get('event_name'),
            discount_percentage=float(data['discount_percentage']),
            start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date(),
            end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date(),
            product_filters=json.dumps(data.get('product_filters', {})) if data.get('product_filters') else None,
            is_active=data.get('is_active', True),
            auto_activate=data.get('auto_activate', False)
        )
        
        db.session.add(sale)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'sale': sale.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_sales_bp.route('/sales/<int:sale_id>', methods=['PUT'])
@require_admin
def update_sale(sale_id):
    """Update a sale."""
    try:
        sale = Sale.query.get_or_404(sale_id)
        data = request.get_json()
        
        if 'name' in data:
            sale.name = data['name']
        if 'description' in data:
            sale.description = data['description']
        if 'sale_type' in data:
            sale.sale_type = data['sale_type']
        if 'event_name' in data:
            sale.event_name = data['event_name']
        if 'discount_percentage' in data:
            sale.discount_percentage = float(data['discount_percentage'])
        if 'start_date' in data:
            sale.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        if 'end_date' in data:
            sale.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        if 'product_filters' in data:
            sale.product_filters = json.dumps(data['product_filters']) if data['product_filters'] else None
        if 'is_active' in data:
            sale.is_active = data['is_active']
        if 'auto_activate' in data:
            sale.auto_activate = data['auto_activate']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'sale': sale.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_sales_bp.route('/sales/<int:sale_id>', methods=['DELETE'])
@require_admin
def delete_sale(sale_id):
    """Delete a sale."""
    try:
        sale = Sale.query.get_or_404(sale_id)
        db.session.delete(sale)
        db.session.commit()
        
        return jsonify({'success': True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_sales_bp.route('/sales/events', methods=['GET'])
@require_admin
def get_events_for_sales():
    """Get upcoming holidays and events that can be used for sales."""
    try:
        upcoming_holidays = get_upcoming_holidays(days_ahead=90)
        current_events = get_current_holidays_and_events()
        
        return jsonify({
            'success': True,
            'upcoming_holidays': upcoming_holidays,
            'current_events': current_events
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_sales_bp.route('/sales/run-automation', methods=['POST'])
@require_admin
def run_sale_automation():
    """Run sale automation tasks (admin only)."""
    try:
        from utils.sale_automation import run_sale_automation
        
        with db.session.begin():
            results = run_sale_automation()
        
        return jsonify({
            'success': True,
            'message': 'Sale automation completed successfully',
            'results': results
        }), 200
        
    except Exception as e:
        db.session.rollback()
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in sale automation: {e}")
        print(error_trace)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

