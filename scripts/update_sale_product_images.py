"""Update the 5 special-offer products to use special-offer-1.png through special-offer-5.png."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.database import db
from models.product import Product

NAMES_AND_IMAGES = [
    ("Autumn Plaid High-Waisted Shorts", "special-offer-1.png"),
    ("Sky Blue Ribbed Polo Sweater", "special-offer-2.png"),
    ("Burgundy Relaxed Crewneck Tee", "special-offer-3.png"),
    ("Warm Plaid Pleated Trousers", "special-offer-4.png"),
    ("Sage Green Pleated Cuff Shorts", "special-offer-5.png"),
]


def update_sale_product_images():
    with app.app_context():
        updated = 0
        for name, filename in NAMES_AND_IMAGES:
            p = Product.query.filter_by(name=name).first()
            if p:
                p.image_url = f"/api/images/{filename}"
                updated += 1
                print(f"Updated image for: {name}")
            else:
                print(f"Product not found: {name}")
        db.session.commit()
        print(f"Done. Updated {updated} product(s).")


if __name__ == "__main__":
    update_sale_product_images()
