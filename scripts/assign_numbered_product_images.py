"""
Assign numbered product images (1.png, 2.png, ...) from static/images to products.
Images are served at /api/images/<n>.png. Cycles through available images by product id.
Add more images as 6.png, 7.png, etc. and re-run to use them (or increase NUM_IMAGES below).
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.product import Product
from models.database import db

# Number of numbered images in static/images (1.png through NUM_IMAGES.png)
NUM_IMAGES = 5


def assign_numbered_images():
    """Set each product's image_url to /api/images/<n>.png where n cycles 1..NUM_IMAGES."""
    with app.app_context():
        products = Product.query.order_by(Product.id).all()
        updated = 0
        for product in products:
            n = (product.id - 1) % NUM_IMAGES + 1
            product.image_url = f"/api/images/{n}.png"
            updated += 1
            if updated % 100 == 0:
                db.session.commit()
                print(f"Updated {updated} products...")
        db.session.commit()
        print(f"Successfully assigned numbered images to {updated} products (1.png–{NUM_IMAGES}.png).")


if __name__ == "__main__":
    assign_numbered_images()
