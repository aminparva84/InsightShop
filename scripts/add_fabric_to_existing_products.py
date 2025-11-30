"""Add fabric information to existing products."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.product import Product
from models.database import db
import random

# Fabric options by clothing type
FABRICS = {
    'T-Shirt': ['100% Cotton', 'Cotton Blend', 'Organic Cotton'],
    'Polo Shirt': ['100% Cotton', 'Cotton-Polyester Blend', 'Pima Cotton'],
    'Dress Shirt': ['100% Cotton', 'Cotton-Polyester Blend', 'Oxford Cotton'],
    'Blouse': ['100% Cotton', 'Silk', 'Polyester', 'Rayon'],
    'Dress': ['Cotton', 'Polyester', 'Silk', 'Linen', 'Cotton-Polyester Blend'],
    'Jeans': ['100% Cotton Denim', 'Stretch Denim', 'Organic Denim'],
    'Chinos': ['100% Cotton', 'Cotton-Polyester Blend'],
    'Shorts': ['100% Cotton', 'Cotton-Polyester Blend', 'Linen'],
    'Skirt': ['Cotton', 'Polyester', 'Wool Blend', 'Linen'],
    'Leggings': ['Polyester-Spandex Blend', 'Cotton-Spandex Blend', 'Nylon-Spandex'],
    'Hoodie': ['Cotton-Polyester Blend', 'Fleece', '100% Cotton'],
    'Sweater': ['Wool', 'Cashmere', 'Cotton', 'Acrylic', 'Wool Blend'],
    'Jacket': ['Polyester', 'Nylon', 'Cotton', 'Wool Blend'],
    'Blazer': ['Wool', 'Wool Blend', 'Polyester', 'Cotton'],
    'Coat': ['Wool', 'Wool Blend', 'Down', 'Polyester'],
    'Suit': ['Wool', 'Wool Blend', 'Polyester-Wool Blend'],
    'Underwear': ['100% Cotton', 'Cotton-Spandex Blend', 'Modal'],
    'Bra': ['Cotton', 'Polyester-Spandex Blend', 'Lace'],
    'Socks': ['100% Cotton', 'Cotton-Polyester Blend', 'Wool Blend'],
    'Shoes': ['Leather', 'Synthetic Leather', 'Canvas'],
    'Sneakers': ['Canvas', 'Mesh', 'Leather', 'Synthetic'],
    'Heels': ['Leather', 'Synthetic Leather', 'Satin'],
    'Sandals': ['Leather', 'Synthetic', 'Rubber'],
    'Pajamas': ['100% Cotton', 'Cotton-Polyester Blend', 'Flannel']
}

def get_fabric_for_product(product_name):
    """Get appropriate fabric for a product based on its name."""
    product_lower = product_name.lower()
    for clothing_type, fabrics in FABRICS.items():
        if clothing_type.lower() in product_lower:
            return random.choice(fabrics)
    # Default
    return random.choice(['100% Cotton', 'Cotton Blend', 'Polyester'])

def add_fabric_to_products():
    """Add fabric information to existing products."""
    with app.app_context():
        products = Product.query.filter_by(is_active=True).all()
        updated = 0
        
        for product in products:
            if not product.fabric:
                product.fabric = get_fabric_for_product(product.name)
                updated += 1
            
            if updated % 100 == 0:
                db.session.commit()
                print(f"Updated {updated} products...")
        
        db.session.commit()
        print(f"Successfully added fabric information to {updated} products!")

if __name__ == '__main__':
    add_fabric_to_products()

