"""
Shipping API Routes
Provides endpoints for calculating shipping rates from FedEx and UPS.
"""
from flask import Blueprint, request, jsonify
from utils.shipping import ShippingService
from utils.guest_cart import get_guest_cart
from models.cart import CartItem
from models.user import User
from routes.auth import get_current_user_optional
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

shipping_bp = Blueprint('shipping', __name__)

@shipping_bp.route('/rates', methods=['POST'])
def calculate_shipping_rates():
    """
    Calculate shipping rates for a destination.
    
    Request body:
    {
        "destination": {
            "street": "123 Main St",
            "city": "New York",
            "state": "NY",
            "zip": "10001",
            "country": "US"
        },
        "weight": 2.5,  # Optional, will calculate from cart if not provided
        "dimensions": {  # Optional
            "length": 10,
            "width": 8,
            "height": 6
        }
    }
    
    Returns:
    {
        "fedex": [...],
        "ups": [...],
        "errors": [...]
    }
    """
    try:
        data = request.get_json()
        
        # Get destination from request
        destination = data.get('destination', {})
        if not all([destination.get('city'), destination.get('state'), destination.get('zip')]):
            return jsonify({'error': 'Destination city, state, and zip are required'}), 400
        
        # Get user and cart items
        user = get_current_user_optional()
        cart_items = []
        
        if user:
            # Authenticated user cart
            cart_items_db = CartItem.query.filter_by(user_id=user.id).all()
            for item in cart_items_db:
                if item.product:
                    cart_items.append({
                        'product': item.product.to_dict() if hasattr(item.product, 'to_dict') else {},
                        'quantity': item.quantity
                    })
        else:
            # Guest cart
            from models.product import Product
            guest_cart = get_guest_cart()
            for cart_item in guest_cart:
                product = Product.query.get(cart_item['product_id'])
                if product:
                    cart_items.append({
                        'product': product.to_dict() if hasattr(product, 'to_dict') else {},
                        'quantity': cart_item['quantity']
                    })
        
        # Initialize shipping service
        shipping_service = ShippingService()
        
        # Get weight and dimensions
        weight = data.get('weight')
        if not weight:
            weight = shipping_service.calculate_package_weight(cart_items)
        
        dimensions = data.get('dimensions')
        if not dimensions:
            dimensions = shipping_service.calculate_package_dimensions(cart_items)
        
        # Calculate total value (optional, for insurance)
        total_value = None
        if cart_items:
            total_value = Decimal('0.00')
            for item in cart_items:
                product = item.get('product', {})
                price = Decimal(str(product.get('price', 0)))
                quantity = item.get('quantity', 1)
                total_value += price * quantity
        
        # Calculate rates
        rates = shipping_service.calculate_rates(
            destination=destination,
            weight=weight,
            dimensions=dimensions,
            value=total_value
        )
        
        return jsonify(rates), 200
        
    except Exception as e:
        logger.error(f"Error calculating shipping rates: {str(e)}")
        return jsonify({'error': f'Failed to calculate shipping rates: {str(e)}'}), 500

@shipping_bp.route('/rates/quick', methods=['POST'])
def quick_shipping_rates():
    """
    Quick shipping rate calculation with minimal data.
    
    Request body:
    {
        "zip": "10001",
        "state": "NY",
        "country": "US"
    }
    
    Returns simplified rate options.
    """
    try:
        data = request.get_json()
        
        zip_code = data.get('zip')
        state = data.get('state')
        country = data.get('country', 'US')
        
        if not zip_code or not state:
            return jsonify({'error': 'ZIP code and state are required'}), 400
        
        destination = {
            'street': '',  # Not required for quick estimate
            'city': '',    # Not required for quick estimate
            'state': state,
            'zip': zip_code,
            'country': country
        }
        
        shipping_service = ShippingService()
        
        # Use default weight and dimensions for quick estimate
        weight = 2.0  # Default 2 lbs
        dimensions = {
            'length': 10,
            'width': 8,
            'height': 6
        }
        
        rates = shipping_service.calculate_rates(
            destination=destination,
            weight=weight,
            dimensions=dimensions
        )
        
        # Return simplified format
        all_rates = []
        for carrier, carrier_rates in rates.items():
            if carrier != 'errors':
                all_rates.extend(carrier_rates)
        
        # Sort by price and return cheapest options
        all_rates.sort(key=lambda x: x.get('price', 999))
        
        return jsonify({
            'rates': all_rates[:6],  # Return top 6 cheapest options
            'errors': rates.get('errors', [])
        }), 200
        
    except Exception as e:
        logger.error(f"Error calculating quick shipping rates: {str(e)}")
        return jsonify({'error': f'Failed to calculate shipping rates: {str(e)}'}), 500


