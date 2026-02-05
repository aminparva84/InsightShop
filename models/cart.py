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
        try:
            product_dict = self.product.to_dict() if self.product else None
        except Exception:
            # If to_dict fails, create basic product dict
            if self.product:
                product_dict = {
                    'id': self.product.id,
                    'name': self.product.name,
                    'price': float(self.product.price) if self.product.price else 0.0,
                    'original_price': float(self.product.price) if self.product.price else 0.0,
                    'on_sale': False,
                    'stock_quantity': getattr(self.product, 'stock_quantity', 0)
                }
            else:
                product_dict = None
        
        # Calculate subtotal using current price (sale price if on sale)
        if self.product and product_dict:
            current_price = product_dict.get('price', float(self.product.price) if self.product.price else 0.0)
            subtotal = current_price * self.quantity
        else:
            subtotal = 0.0
        
        return {
            'id': self.id,
            'user_id': self.user_id,
            'product': product_dict,
            'quantity': self.quantity,
            'selected_color': self.selected_color,
            'selected_size': self.selected_size,
            'subtotal': subtotal,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

