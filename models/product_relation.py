from models.database import db
from datetime import datetime

class ProductRelation(db.Model):
    __tablename__ = 'product_relations'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    related_product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    is_fashion_match = db.Column(db.Boolean, default=True, nullable=False, index=True)
    match_score = db.Column(db.Float, default=1.0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    product = db.relationship('Product', foreign_keys=[product_id], backref='related_products')
    related_product = db.relationship('Product', foreign_keys=[related_product_id])
    
    # Unique constraint to prevent duplicate relations
    __table_args__ = (
        db.UniqueConstraint('product_id', 'related_product_id', name='uq_product_relation'),
    )
    
    def to_dict(self):
        """Convert product relation to dictionary."""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'related_product_id': self.related_product_id,
            'is_fashion_match': self.is_fashion_match,
            'match_score': self.match_score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'related_product': self.related_product.to_dict() if self.related_product else None
        }

