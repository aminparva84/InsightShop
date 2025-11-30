"""Update product images to use better placeholder URLs."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.product import Product
from models.database import db
import random

# Different clothing image URLs from Unsplash
CLOTHING_IMAGES = [
    "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400&h=400&fit=crop&q=80",  # Clothing store
    "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=400&h=400&fit=crop&q=80",  # Fashion
    "https://images.unsplash.com/photo-1483985988355-763728e1935b?w=400&h=400&fit=crop&q=80",  # Shopping
    "https://images.unsplash.com/photo-1445205170230-053b83016050?w=400&h=400&fit=crop&q=80",  # Clothes
    "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=400&h=400&fit=crop&q=80",  # Fashion model
    "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=400&h=400&fit=crop&q=80",  # Style
    "https://images.unsplash.com/photo-1539533018447-63fcce2678e3?w=400&h=400&fit=crop&q=80",  # Apparel
    "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400&h=400&fit=crop&q=80",  # Retail
]

def update_product_images():
    """Update all product images."""
    with app.app_context():
        products = Product.query.all()
        updated = 0
        
        for product in products:
            # Use different images based on category
            if product.category == 'men':
                product.image_url = "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400&h=400&fit=crop&q=80"
            elif product.category == 'women':
                product.image_url = "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=400&h=400&fit=crop&q=80"
            elif product.category == 'kids':
                product.image_url = "https://images.unsplash.com/photo-1483985988355-763728e1935b?w=400&h=400&fit=crop&q=80"
            else:
                product.image_url = random.choice(CLOTHING_IMAGES)
            
            updated += 1
            
            if updated % 100 == 0:
                db.session.commit()
                print(f"Updated {updated} products...")
        
        db.session.commit()
        print(f"Successfully updated {updated} product images!")

if __name__ == '__main__':
    update_product_images()

