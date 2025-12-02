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
    dress_style = db.Column(db.String(100), nullable=True, index=True)  # e.g., "scoop", "v-neck", "bow", "padding", "slit"
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
    
    def get_sale_price(self):
        """Get the sale price if product is on sale, otherwise return original price."""
        try:
            from models.sale import Sale
            from datetime import date
            
            # Check if Sale table exists
            try:
                # Find active sales that apply to this product
                active_sales = Sale.query.filter_by(is_active=True).all()
            except Exception as e:
                # Sale table might not exist yet, return None
                return None
            
            current_date = date.today()
            
            best_discount = 0.0
            sale_info = None
            
            for sale in active_sales:
                try:
                    if sale.is_currently_active(current_date) and sale.matches_product(self):
                        discount = float(sale.discount_percentage) if sale.discount_percentage else 0.0
                        if discount > best_discount:
                            best_discount = discount
                            sale_info = sale
                except Exception:
                    # Skip this sale if there's an error
                    continue
            
            if best_discount > 0:
                original_price = float(self.price) if self.price else 0.0
                sale_price = original_price * (1 - best_discount / 100)
                return {
                    'original_price': original_price,
                    'sale_price': round(sale_price, 2),
                    'discount_percentage': best_discount,
                    'sale': sale_info.to_dict() if sale_info else None
                }
        except Exception:
            # If anything fails, just return None (no sale)
            pass
        
        return None
    
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
        
        # Get sale price if on sale (with error handling)
        sale_data = None
        try:
            sale_data = self.get_sale_price()
        except Exception:
            # If get_sale_price fails (e.g., Sale table doesn't exist), continue without sale
            pass
        
        original_price = float(self.price) if self.price else 0.0
        current_price = sale_data['sale_price'] if sale_data else original_price
        
        result = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': current_price,  # Current price (sale price if on sale)
            'original_price': original_price,  # Always include original price
            'category': self.category,
            'color': self.color,
            'size': self.size,
            'available_colors': available_colors_list if available_colors_list else ([self.color] if self.color else []),
            'available_sizes': available_sizes_list if available_sizes_list else ([self.size] if self.size else []),
            'fabric': self.fabric,
            'clothing_type': self.clothing_type,
            'dress_style': self.dress_style,
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
        
        # Add sale information if on sale
        if sale_data and isinstance(sale_data, dict):
            result['on_sale'] = True
            result['discount_percentage'] = sale_data.get('discount_percentage', 0)
            result['sale'] = sale_data.get('sale')
        else:
            result['on_sale'] = False
        
        return result
    
    def to_dict_for_ai(self):
        """Convert product to dictionary with full details for AI agent, including reviews and ratings."""
        from models.review import Review
        
        fabric_info = f", Fabric: {self.fabric}" if self.fabric else ""
        clothing_type_info = f", Type: {self.clothing_type}" if self.clothing_type else ""
        dress_style_info = f", Style: {self.dress_style}" if self.dress_style else ""
        occasion_info = f", Occasion: {self.occasion}" if self.occasion else ""
        age_group_info = f", Age Group: {self.age_group}" if self.age_group else ""
        
        # Get recent reviews (last 5) for AI context
        recent_reviews = Review.query.filter_by(product_id=self.id).order_by(Review.created_at.desc()).limit(5).all()
        reviews_summary = []
        if recent_reviews:
            for review in recent_reviews:
                review_text = f"Rating: {float(review.rating)}/5.0"
                if review.comment:
                    review_text += f", Comment: {review.comment[:100]}"  # Limit comment length
                reviews_summary.append(review_text)
        
        rating_info = ""
        if self.rating and float(self.rating) > 0:
            rating_info = f", Average Rating: {float(self.rating):.1f}/5.0 ({self.review_count} review{'s' if self.review_count != 1 else ''})"
            if reviews_summary:
                rating_info += f", Recent Reviews: {'; '.join(reviews_summary)}"
        
        return {
            **self.to_dict(),
            'full_description': f"Product #{self.id}: {self.name} - {self.description or ''} - Category: {self.category}, Color: {self.color or 'Various'}, Size: {self.size or 'Various'}{fabric_info}{clothing_type_info}{dress_style_info}{occasion_info}{age_group_info}, Price: ${self.price}{rating_info}",
            'reviews': [r.to_dict() for r in recent_reviews],
            'rating_summary': {
                'average_rating': float(self.rating) if self.rating else 0.0,
                'review_count': self.review_count,
                'recent_reviews': reviews_summary
            }
        }

