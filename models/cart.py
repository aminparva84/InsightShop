from models.database import db
from datetime import datetime

class CartItem(db.Model):
    __tablename__ = 'cart_items'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    selected_color = db.Column(db.String(50), nullable=True)  # Selected color variant
    selected_size = db.Column(db.String(20), nullable=True)  # Selected size variant
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    product = db.relationship('Product', lazy='joined')
    
    def to_dict(self):
        """Convert cart item to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'product': self.product.to_dict() if self.product else None,
            'quantity': self.quantity,
            'selected_color': self.selected_color,
            'selected_size': self.selected_size,
            'subtotal': float(self.product.price * self.quantity) if self.product else 0.0,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

