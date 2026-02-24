"""Wishlist model: user-specific saved products for future purchase."""

from models.database import db
from datetime import datetime


class WishlistItem(db.Model):
    """Links a user to a product they saved. Tracks price when added for price-drop notifications."""

    __tablename__ = 'wishlist_items'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)

    # Price when added (for price-drop detection)
    price_when_added = db.Column(db.Numeric(10, 2), nullable=True)
    # Stock when added (0 = was out of stock; for back-in-stock notification)
    was_out_of_stock = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = db.relationship('User', backref=db.backref('wishlist_items', lazy=True, cascade='all, delete-orphan'))
    product = db.relationship('Product', lazy='joined')

    # One entry per user per product
    __table_args__ = (db.UniqueConstraint('user_id', 'product_id', name='uq_wishlist_user_product'),)

    def to_dict(self, include_notifications=False):
        """Convert to dict. If include_notifications, add price_dropped, back_in_stock, on_sale."""
        product_dict = None
        notifications = {}
        if self.product:
            try:
                product_dict = self.product.to_dict()
            except Exception:
                product_dict = {
                    'id': self.product.id,
                    'name': self.product.name,
                    'price': float(self.product.price) if self.product.price else 0.0,
                    'original_price': float(self.product.price) if self.product.price else 0.0,
                    'on_sale': False,
                    'stock_quantity': getattr(self.product, 'stock_quantity', 0),
                    'image_url': getattr(self.product, 'image_url', None),
                }

            if include_notifications:
                current_price = float(self.product.price) if self.product.price else 0.0
                on_sale = False
                try:
                    sale_data = self.product.get_sale_price()
                    if sale_data:
                        current_price = sale_data.get('sale_price') or current_price
                        on_sale = True
                except Exception:
                    pass
                price_added = float(self.price_when_added) if self.price_when_added is not None else current_price
                notifications = {
                    'price_dropped': price_added > 0 and current_price < price_added,
                    'back_in_stock': bool(self.was_out_of_stock and getattr(self.product, 'stock_quantity', 0) > 0),
                    'on_sale': on_sale,
                }

        return {
            'id': self.id,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'product': product_dict,
            'added_at': self.created_at.isoformat() if self.created_at else None,
            'price_when_added': float(self.price_when_added) if self.price_when_added is not None else None,
            **({'notifications': notifications} if include_notifications else {}),
        }
