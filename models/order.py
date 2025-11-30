from models.database import db
from datetime import datetime
import uuid

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)  # Nullable for guest orders
    guest_email = db.Column(db.String(255), nullable=True, index=True)  # For guest orders
    
    # Shipping information
    shipping_name = db.Column(db.String(255), nullable=False)
    shipping_address = db.Column(db.Text, nullable=False)
    shipping_city = db.Column(db.String(100), nullable=False)
    shipping_state = db.Column(db.String(100), nullable=False)
    shipping_zip = db.Column(db.String(20), nullable=False)
    shipping_country = db.Column(db.String(100), nullable=False, default='USA')
    shipping_phone = db.Column(db.String(20), nullable=True)
    
    # Order totals
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    tax = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    shipping_cost = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Order status
    status = db.Column(db.String(50), nullable=False, default='pending', index=True)  # pending, processing, shipped, delivered, cancelled
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='order', lazy=True)
    
    def __init__(self, **kwargs):
        super(Order, self).__init__(**kwargs)
        if not self.order_number:
            self.order_number = self.generate_order_number()
    
    @staticmethod
    def generate_order_number():
        """Generate a unique order number."""
        return f"ORD-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    
    def to_dict(self):
        """Convert order to dictionary."""
        return {
            'id': self.id,
            'order_number': self.order_number,
            'user_id': self.user_id,
            'shipping_name': self.shipping_name,
            'shipping_address': self.shipping_address,
            'shipping_city': self.shipping_city,
            'shipping_state': self.shipping_state,
            'shipping_zip': self.shipping_zip,
            'shipping_country': self.shipping_country,
            'shipping_phone': self.shipping_phone,
            'subtotal': float(self.subtotal) if self.subtotal else 0.0,
            'tax': float(self.tax) if self.tax else 0.0,
            'shipping_cost': float(self.shipping_cost) if self.shipping_cost else 0.0,
            'total': float(self.total) if self.total else 0.0,
            'status': self.status,
            'items': [item.to_dict() for item in self.items],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)  # Price at time of order
    
    def to_dict(self):
        """Convert order item to dictionary."""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product': self.product.to_dict() if self.product else None,
            'quantity': self.quantity,
            'price': float(self.price) if self.price else 0.0,
            'subtotal': float(self.price * self.quantity) if self.price else 0.0
        }

