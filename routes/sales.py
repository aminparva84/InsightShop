"""Sales routes for managing discounts and promotions."""

from flask import Blueprint, request, jsonify
from models.database import db
from models.sale import Sale
from models.product import Product
from routes.auth import require_auth
from datetime import date, datetime
from sqlalchemy import or_
import json

sales_bp = Blueprint('sales', __name__)

@sales_bp.route('/active', methods=['GET'])
def get_active_sales():
    """Get all currently active sales.
    Sales stay active until manually deactivated (is_active=False).
    End date is informational only."""
    try:
        # Check if Sale table exists
        try:
            current_date = date.today()
            # Sales are active if: is_active=True AND start_date <= today
            # End date is informational - sales don't auto-expire
            active_sales = Sale.query.filter(
                Sale.is_active == True,
                Sale.start_date <= current_date
            ).all()
        except Exception as e:
            # Table doesn't exist yet, return empty list
            return jsonify({
                'sales': [],
                'count': 0
            }), 200
        
        return jsonify({
            'sales': [sale.to_dict() for sale in active_sales],
            'count': len(active_sales)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sales_bp.route('/upcoming', methods=['GET'])
def get_upcoming_sales():
    """Get upcoming sales (starting within next 30 days)."""
    try:
        current_date = date.today()
        from datetime import timedelta
        future_date = current_date + timedelta(days=30)
        
        upcoming_sales = Sale.query.filter(
            Sale.is_active == True,
            Sale.start_date > current_date,
            Sale.start_date <= future_date
        ).all()
        
        return jsonify({
            'sales': [sale.to_dict() for sale in upcoming_sales],
            'count': len(upcoming_sales)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sales_bp.route('/current-context', methods=['GET'])
def get_current_sales_context():
    """Get current date, active sales, and upcoming sales for AI chat."""
    try:
        from utils.seasonal_events import get_current_date, get_current_season, get_upcoming_holidays, get_current_holidays_and_events
        
        current_date = get_current_date()
        current_season = get_current_season()
        upcoming_holidays = get_upcoming_holidays(days_ahead=30)
        current_events = get_current_holidays_and_events()
        
        # Get active sales (handle case where table doesn't exist)
        active_sales = []
        upcoming_sales = []
        try:
            # Get active sales (sales stay active until manually deactivated)
            active_sales = Sale.query.filter(
                Sale.is_active == True,
                Sale.start_date <= current_date
            ).all()
            
            # Get upcoming sales (sales that haven't started yet)
            from datetime import timedelta
            future_date = current_date + timedelta(days=30)
            upcoming_sales = Sale.query.filter(
                Sale.is_active == True,
                Sale.start_date > current_date,
                Sale.start_date <= future_date
            ).all()
        except Exception:
            # Sale table doesn't exist yet, use empty lists
            pass
        
        return jsonify({
            'current_date': current_date.isoformat(),
            'current_date_formatted': current_date.strftime('%B %d, %Y'),
            'current_season': current_season,
            'active_sales': [sale.to_dict() for sale in active_sales],
            'upcoming_sales': [sale.to_dict() for sale in upcoming_sales],
            'upcoming_holidays': upcoming_holidays,
            'current_events': current_events
        }), 200
    except Exception as e:
        import traceback
        print(f"Error in get_current_sales_context: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

