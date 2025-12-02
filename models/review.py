from models.database import db
from datetime import datetime

class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)  # Nullable for guest reviews
    rating = db.Column(db.Numeric(2, 1), nullable=False)  # Rating from 1.0 to 5.0
    comment = db.Column(db.Text, nullable=True)  # Optional review text
    user_name = db.Column(db.String(100), nullable=True)  # For guest reviews or display name
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    product = db.relationship('Product', backref='reviews', lazy=True)
    user = db.relationship('User', backref='reviews', lazy=True)
    
    def to_dict(self):
        """Convert review to dictionary."""
        user_name = self.user_name
        if not user_name and self.user:
            user_name = f"{self.user.first_name} {self.user.last_name}"
        if not user_name:
            user_name = 'Anonymous'
        
        return {
            'id': self.id,
            'product_id': self.product_id,
            'user_id': self.user_id,
            'rating': float(self.rating) if self.rating else 0.0,
            'comment': self.comment,
            'user_name': user_name,
            'user_email': self.user.email if self.user else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

