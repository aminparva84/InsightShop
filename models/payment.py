from models.database import db
from datetime import datetime
import uuid

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    payment_method = db.Column(db.String(50), nullable=False)  # stripe, paypal, etc.
    payment_intent_id = db.Column(db.String(255), nullable=True)  # Stripe payment intent ID
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(10), default='USD', nullable=False)
    status = db.Column(db.String(50), nullable=False, default='pending', index=True)  # pending, completed, failed, refunded
    transaction_id = db.Column(db.String(255), unique=True, nullable=True, index=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __init__(self, **kwargs):
        super(Payment, self).__init__(**kwargs)
        if not self.transaction_id:
            self.transaction_id = self.generate_transaction_id()
    
    @staticmethod
    def generate_transaction_id():
        """Generate a unique transaction ID."""
        return f"TXN-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8].upper()}"
    
    def to_dict(self):
        """Convert payment to dictionary."""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'payment_method': self.payment_method,
            'payment_intent_id': self.payment_intent_id,
            'amount': float(self.amount) if self.amount else 0.0,
            'currency': self.currency,
            'status': self.status,
            'transaction_id': self.transaction_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

