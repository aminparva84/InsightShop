"""Routes for sale automation (can be called by scheduled tasks)."""

from flask import Blueprint, request, jsonify
from models.database import db
from utils.sale_automation import run_sale_automation, auto_activate_sales, sync_holiday_sales
from config import Config
import os

sale_automation_bp = Blueprint('sale_automation', __name__)

# Secret key for automation endpoint (set in environment or use default)
AUTOMATION_SECRET = os.getenv('AUTOMATION_SECRET', 'change-this-in-production')


def verify_automation_request():
    """Verify that the request is authorized (from cron/scheduled task)."""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        return token == AUTOMATION_SECRET
    return False


@sale_automation_bp.route('/run', methods=['POST'])
def run_automation():
    """
    Run sale automation tasks.
    This endpoint should be called daily by a cron job or scheduled task.
    
    Authorization: Bearer token matching AUTOMATION_SECRET environment variable.
    """
    try:
        # Verify authorization
        if not verify_automation_request():
            return jsonify({'error': 'Unauthorized'}), 401
        
        with db.session.begin():
            results = run_sale_automation()
        
        return jsonify({
            'success': True,
            'results': results
        }), 200
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in sale automation: {e}")
        print(error_trace)
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': error_trace if Config.DEBUG else None
        }), 500


@sale_automation_bp.route('/activate', methods=['POST'])
def activate_sales():
    """Activate sales based on start dates."""
    try:
        if not verify_automation_request():
            return jsonify({'error': 'Unauthorized'}), 401
        
        with db.session.begin():
            results = auto_activate_sales()
        
        return jsonify({
            'success': True,
            'results': results
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@sale_automation_bp.route('/sync-holidays', methods=['POST'])
def sync_holidays():
    """Sync holiday sales with current dates."""
    try:
        if not verify_automation_request():
            return jsonify({'error': 'Unauthorized'}), 401
        
        with db.session.begin():
            results = sync_holiday_sales()
        
        return jsonify({
            'success': True,
            'results': results
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

