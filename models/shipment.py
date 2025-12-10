from models.database import db
from datetime import datetime
import uuid

class Shipment(db.Model):
    __tablename__ = 'shipments'
    
    id = db.Column(db.Integer, primary_key=True)
    tracking_number = db.Column(db.String(100), unique=True, nullable=False, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    carrier = db.Column(db.String(50), nullable=False)  # UPS, FEDEX, USPS, etc.
    
    # Shipping status
    status = db.Column(db.String(50), nullable=False, default='pending', index=True)  # pending, in_transit, delivered, exception
    estimated_delivery = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    
    # Shipping details
    shipping_address = db.Column(db.Text, nullable=False)
    shipping_city = db.Column(db.String(100), nullable=False)
    shipping_state = db.Column(db.String(100), nullable=False)
    shipping_zip = db.Column(db.String(20), nullable=False)
    shipping_country = db.Column(db.String(100), nullable=False, default='USA')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    order = db.relationship('Order', backref='shipments', lazy=True)
    
    def __init__(self, **kwargs):
        super(Shipment, self).__init__(**kwargs)
        if not self.tracking_number:
            self.tracking_number = self.generate_tracking_number()
    
    @staticmethod
    def generate_tracking_number(carrier='TRK'):
        """Generate a unique tracking number."""
        carrier_prefix = carrier.upper()[:4]
        return f"{carrier_prefix}{datetime.utcnow().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"
    
    def to_dict(self):
        """Convert shipment to dictionary."""
        return {
            'id': self.id,
            'tracking_number': self.tracking_number,
            'order_id': self.order_id,
            'carrier': self.carrier,
            'status': self.status,
            'estimated_delivery': self.estimated_delivery.isoformat() if self.estimated_delivery else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'shipping_address': self.shipping_address,
            'shipping_city': self.shipping_city,
            'shipping_state': self.shipping_state,
            'shipping_zip': self.shipping_zip,
            'shipping_country': self.shipping_country,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

