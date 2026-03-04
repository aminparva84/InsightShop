"""Product variation: stock per (product_id, size, color) combination."""
from models.database import db
from datetime import datetime
from sqlalchemy import UniqueConstraint

class ProductVariation(db.Model):
    __tablename__ = 'product_variations'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False, index=True)
    size = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(100), nullable=False)
    stock_quantity = db.Column(db.Integer, default=0, nullable=False)
    sku = db.Column(db.String(100), nullable=True, unique=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    product = db.relationship('Product', backref=db.backref('variations', lazy=True))

    __table_args__ = (
        UniqueConstraint('product_id', 'size', 'color', name='uq_product_variation_size_color'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'size': self.size,
            'color': self.color,
            'stock_quantity': self.stock_quantity,
            'sku': self.sku,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
