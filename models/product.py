from models.database import db
from datetime import datetime
from sqlalchemy import Index
import json

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    category = db.Column(db.String(50), nullable=False, index=True)  # men, women, kids
    color = db.Column(db.String(50), nullable=True, index=True)  # Primary/default color
    size = db.Column(db.String(20), nullable=True)  # Primary/default size
    available_colors = db.Column(db.Text, nullable=True)  # JSON array of available colors
    available_sizes = db.Column(db.Text, nullable=True)  # JSON array of available sizes
    fabric = db.Column(db.String(100), nullable=True, index=True)  # e.g., "100% Cotton", "Polyester Blend", "Wool"
    clothing_type = db.Column(db.String(100), nullable=True, index=True)  # e.g., "T-Shirt", "Dress", "Jeans", "Suit"
    occasion = db.Column(db.String(100), nullable=True, index=True)  # e.g., "wedding", "business_formal", "casual", "date_night"
    age_group = db.Column(db.String(50), nullable=True, index=True)  # e.g., "young_adult", "mature", "senior", "all"
    image_url = db.Column(db.String(500), nullable=True)
    stock_quantity = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    
    # Ratings
    rating = db.Column(db.Numeric(3, 2), default=0.0, nullable=False)  # Average rating (0.00 to 5.00)
    review_count = db.Column(db.Integer, default=0, nullable=False)  # Number of reviews
    
    # SEO fields
    slug = db.Column(db.String(255), unique=True, nullable=True, index=True)
    meta_title = db.Column(db.String(255), nullable=True)
    meta_description = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    order_items = db.relationship('OrderItem', backref='product', lazy=True)
    
    # Composite indexes for common search patterns
    __table_args__ = (
        Index('idx_category_occasion', 'category', 'occasion'),
        Index('idx_category_age_group', 'category', 'age_group'),
        Index('idx_category_clothing_type', 'category', 'clothing_type'),
        Index('idx_occasion_age_group', 'occasion', 'age_group'),
        Index('idx_category_price', 'category', 'price'),
        Index('idx_category_fabric', 'category', 'fabric'),
        Index('idx_is_active_category', 'is_active', 'category'),
    )
    
    def to_dict(self):
        """Convert product to dictionary."""
        # Parse available colors and sizes from JSON
        available_colors_list = []
        available_sizes_list = []
        try:
            if self.available_colors:
                available_colors_list = json.loads(self.available_colors) if isinstance(self.available_colors, str) else self.available_colors
            if self.available_sizes:
                available_sizes_list = json.loads(self.available_sizes) if isinstance(self.available_sizes, str) else self.available_sizes
        except:
            # Fallback to single color/size if JSON parsing fails
            if self.color:
                available_colors_list = [self.color]
            if self.size:
                available_sizes_list = [self.size]
        
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': float(self.price) if self.price else 0.0,
            'category': self.category,
            'color': self.color,
            'size': self.size,
            'available_colors': available_colors_list if available_colors_list else ([self.color] if self.color else []),
            'available_sizes': available_sizes_list if available_sizes_list else ([self.size] if self.size else []),
            'fabric': self.fabric,
            'clothing_type': self.clothing_type,
            'occasion': self.occasion,
            'age_group': self.age_group,
            'image_url': self.image_url,
            'stock_quantity': self.stock_quantity,
            'is_active': self.is_active,
            'rating': float(self.rating) if self.rating else 0.0,
            'review_count': self.review_count,
            'slug': self.slug,
            'meta_title': self.meta_title,
            'meta_description': self.meta_description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def to_dict_for_ai(self):
        """Convert product to dictionary with full details for AI agent."""
        fabric_info = f", Fabric: {self.fabric}" if self.fabric else ""
        clothing_type_info = f", Type: {self.clothing_type}" if self.clothing_type else ""
        occasion_info = f", Occasion: {self.occasion}" if self.occasion else ""
        age_group_info = f", Age Group: {self.age_group}" if self.age_group else ""
        return {
            **self.to_dict(),
            'full_description': f"Product #{self.id}: {self.name} - {self.description or ''} - Category: {self.category}, Color: {self.color or 'Various'}, Size: {self.size or 'Various'}{fabric_info}{clothing_type_info}{occasion_info}{age_group_info}, Price: ${self.price}"
        }

