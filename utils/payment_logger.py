"""
Utility for logging payment attempts to the payment_logs table.
"""
from models.database import db
from models.payment_log import PaymentLog
from flask import request
import json


def log_payment_attempt(
    order_id=None,
    user_id=None,
    payment_method='unknown',
    amount=0.0,
    currency='USD',
    status='pending',
    transaction_id=None,
    payment_intent_id=None,
    external_transaction_id=None,
    request_data=None,
    response_data=None,
    error_message=None,
    card_last4=None,
    card_brand=None
):
    """
    Log a payment attempt to the payment_logs table.
    
    Args:
        order_id: Order ID (if available)
        user_id: User ID (if available)
        payment_method: Payment method (stripe, jpmorgan, etc.)
        amount: Payment amount
        currency: Currency code
        status: Payment status (pending, completed, failed, etc.)
        transaction_id: Internal transaction ID
        payment_intent_id: Payment intent ID (Stripe)
        external_transaction_id: External transaction ID (JPMorgan, Stripe charge ID, etc.)
        request_data: Request payload (dict or JSON string)
        response_data: Response data (dict or JSON string)
        error_message: Error message if payment failed
        card_last4: Last 4 digits of card
        card_brand: Card brand (Visa, Mastercard, etc.)
    """
    try:
        # Get IP address and user agent
        ip_address = request.remote_addr if request else None
        user_agent = request.headers.get('User-Agent') if request else None
        
        # Convert request/response data to JSON string if dict
        request_data_str = None
        if request_data:
            if isinstance(request_data, dict):
                request_data_str = json.dumps(request_data)
            else:
                request_data_str = str(request_data)
        
        response_data_str = None
        if response_data:
            if isinstance(response_data, dict):
                response_data_str = json.dumps(response_data)
            else:
                response_data_str = str(response_data)
        
        # Create payment log entry
        payment_log = PaymentLog(
            order_id=order_id,
            user_id=user_id,
            payment_method=payment_method,
            amount=amount,
            currency=currency,
            status=status,
            transaction_id=transaction_id,
            payment_intent_id=payment_intent_id,
            external_transaction_id=external_transaction_id,
            request_data=request_data_str,
            response_data=response_data_str,
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent,
            card_last4=card_last4,
            card_brand=card_brand
        )
        
        db.session.add(payment_log)
        db.session.commit()
        
        return payment_log
        
    except Exception as e:
        # Don't fail the payment if logging fails
        db.session.rollback()
        print(f"Error logging payment attempt: {str(e)}")
        return None

