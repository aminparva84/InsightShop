"""Sale model for managing discounts and promotions."""

from models.database import db
from datetime import datetime, date
from sqlalchemy import Index

class Sale(db.Model):
    __tablename__ = 'sales'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)  # e.g., "Valentine's Day Sale", "Summer Clearance"
    description = db.Column(db.Text, nullable=True)
    
    # Sale type: 'holiday', 'seasonal', 'event', 'general'
    sale_type = db.Column(db.String(50), nullable=False, default='general', index=True)
    
    # Associated event/holiday (optional)
    event_name = db.Column(db.String(100), nullable=True)  # e.g., "valentines_day", "christmas"
    
    # Discount percentage (0-100)
    discount_percentage = db.Column(db.Numeric(5, 2), nullable=False)  # e.g., 25.00 for 25% off
    
    # Sale dates
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date, nullable=False, index=True)
    
    # Product filters (JSON)
    # Can filter by: category, color, clothing_type, fabric, occasion, age_group
    # Example: {"category": "women", "clothing_type": "Dress"}
    product_filters = db.Column(db.Text, nullable=True)  # JSON string
    
    # Is sale active
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    
    # Auto-activate based on event date
    auto_activate = db.Column(db.Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_sale_dates', 'start_date', 'end_date'),
        Index('idx_sale_active_dates', 'is_active', 'start_date', 'end_date'),
    )
    
    def is_currently_active(self, check_date=None):
        """Check if sale is currently active.
        Sales stay active until manually deactivated by admin (is_active=False).
        End date is informational only - sales don't auto-expire."""
        if check_date is None:
            check_date = date.today()
        
        # Sale must be active (not manually deactivated)
        if not self.is_active:
            return False
        
        # Sale must have started (start_date check)
        if check_date < self.start_date:
            return False
        
        # End date is informational - sales don't auto-expire
        # They stay active until admin manually deactivates them
        return True
    
    def to_dict(self):
        """Convert sale to dictionary."""
        import json
        
        filters = {}
        try:
            if self.product_filters:
                filters = json.loads(self.product_filters) if isinstance(self.product_filters, str) else self.product_filters
        except:
            pass
        
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'sale_type': self.sale_type,
            'event_name': self.event_name,
            'discount_percentage': float(self.discount_percentage) if self.discount_percentage else 0.0,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'product_filters': filters,
            'is_active': self.is_active,
            'auto_activate': self.auto_activate,
            'is_currently_active': self.is_currently_active(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def matches_product(self, product):
        """Check if sale applies to a specific product."""
        import json
        
        if not self.is_currently_active():
            return False
        
        if not self.product_filters:
            return True  # No filters = applies to all products
        
        try:
            filters = json.loads(self.product_filters) if isinstance(self.product_filters, str) else self.product_filters
        except:
            return True  # If filters can't be parsed, apply to all
        
        # Check category
        if 'category' in filters and product.category != filters['category']:
            return False
        
        # Check color
        if 'color' in filters:
            filter_color = filters['color'].lower()
            product_color = (product.color or '').lower()
            if filter_color not in product_color and filter_color not in (product.available_colors or '').lower():
                return False
        
        # Check clothing_type
        if 'clothing_type' in filters and product.clothing_type != filters['clothing_type']:
            return False
        
        # Check fabric
        if 'fabric' in filters:
            filter_fabric = filters['fabric'].lower()
            product_fabric = (product.fabric or '').lower()
            if filter_fabric not in product_fabric:
                return False
        
        # Check occasion
        if 'occasion' in filters and product.occasion != filters['occasion']:
            return False
        
        # Check age_group
        if 'age_group' in filters and product.age_group != filters['age_group']:
            return False
        
        return True

