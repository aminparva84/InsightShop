from models.database import db
from datetime import datetime
import uuid

class Return(db.Model):
    __tablename__ = 'returns'
    
    id = db.Column(db.Integer, primary_key=True)
    return_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    order_item_id = db.Column(db.Integer, db.ForeignKey('order_items.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)  # Nullable for guest returns
    guest_email = db.Column(db.String(255), nullable=True, index=True)  # For guest returns
    
    # Return details
    reason = db.Column(db.String(100), nullable=False)  # "Wrong Size", "Damaged", "Changed Mind"
    status = db.Column(db.String(50), nullable=False, default='pending', index=True)  # pending, approved, rejected, processed
    return_label_url = db.Column(db.String(500), nullable=True)  # URL to printable return label
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    processed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    order = db.relationship('Order', backref='returns', lazy=True)
    order_item = db.relationship('OrderItem', backref='returns', lazy=True)
    user = db.relationship('User', backref='returns', lazy=True)
    
    def __init__(self, **kwargs):
        super(Return, self).__init__(**kwargs)
        if not self.return_number:
            self.return_number = self.generate_return_number()
    
    @staticmethod
    def generate_return_number():
        """Generate a unique return number."""
        return f"RMA-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    
    def to_dict(self):
        """Convert return to dictionary."""
        return {
            'id': self.id,
            'return_number': self.return_number,
            'order_id': self.order_id,
            'order_item_id': self.order_item_id,
            'user_id': self.user_id,
            'guest_email': self.guest_email,
            'reason': self.reason,
            'status': self.status,
            'return_label_url': self.return_label_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'order': self.order.to_dict() if self.order else None,
            'order_item': self.order_item.to_dict() if self.order_item else None
        }

