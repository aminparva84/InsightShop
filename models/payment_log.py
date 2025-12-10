from models.database import db
from datetime import datetime
import json

class PaymentLog(db.Model):
    """Log table for all payment attempts (successful or not) for admin monitoring."""
    __tablename__ = 'payment_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    payment_method = db.Column(db.String(50), nullable=False, index=True)  # stripe, jpmorgan, etc.
    
    # Payment details
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(10), default='USD', nullable=False)
    status = db.Column(db.String(50), nullable=False, index=True)  # pending, completed, failed, refunded, cancelled
    
    # Transaction identifiers
    transaction_id = db.Column(db.String(255), nullable=True, index=True)
    payment_intent_id = db.Column(db.String(255), nullable=True, index=True)
    external_transaction_id = db.Column(db.String(255), nullable=True, index=True)  # JPMorgan transaction ID, Stripe charge ID, etc.
    
    # Request/Response data (stored as JSON)
    request_data = db.Column(db.Text, nullable=True)  # JSON string of request payload
    response_data = db.Column(db.Text, nullable=True)  # JSON string of API response
    error_message = db.Column(db.Text, nullable=True)  # Error message if payment failed
    
    # Additional metadata
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4 or IPv6
    user_agent = db.Column(db.String(500), nullable=True)
    card_last4 = db.Column(db.String(4), nullable=True)  # Last 4 digits of card (if available)
    card_brand = db.Column(db.String(50), nullable=True)  # Visa, Mastercard, etc.
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __init__(self, **kwargs):
        super(PaymentLog, self).__init__(**kwargs)
        # Convert dict to JSON string for request/response data
        if isinstance(self.request_data, dict):
            self.request_data = json.dumps(self.request_data)
        if isinstance(self.response_data, dict):
            self.response_data = json.dumps(self.response_data)
    
    def to_dict(self):
        """Convert payment log to dictionary."""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'user_id': self.user_id,
            'payment_method': self.payment_method,
            'amount': float(self.amount) if self.amount else 0.0,
            'currency': self.currency,
            'status': self.status,
            'transaction_id': self.transaction_id,
            'payment_intent_id': self.payment_intent_id,
            'external_transaction_id': self.external_transaction_id,
            'request_data': json.loads(self.request_data) if self.request_data else None,
            'response_data': json.loads(self.response_data) if self.response_data else None,
            'error_message': self.error_message,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'card_last4': self.card_last4,
            'card_brand': self.card_brand,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


