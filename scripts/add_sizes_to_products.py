"""Add multiple sizes to all products that don't have available_sizes set."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.product import Product
from models.database import db
import json

# Standard sizes for all products
ALL_SIZES = ['XS', 'S', 'M', 'L', 'XL', 'XXL']

def add_sizes_to_products():
    """Add available_sizes to all products that don't have them."""
    with app.app_context():
        products = Product.query.filter_by(is_active=True).all()
        updated = 0
        
        for product in products:
            # Always ensure product has all standard sizes
            try:
                # Start with product's current size or default to M
                base_size = product.size if product.size else 'M'
                sizes_list = [base_size]
                
                # Add all standard sizes
                sizes_list.extend([s for s in ALL_SIZES if s not in sizes_list])
                
                # Ensure we have all sizes in the correct order
                final_sizes = []
                for size in ALL_SIZES:
                    if size in sizes_list:
                        final_sizes.append(size)
                
                # Update the product with all sizes
                product.available_sizes = json.dumps(final_sizes)
                updated += 1
                
                if updated % 100 == 0:
                    db.session.commit()
                    print(f"Updated {updated} products...")
            except Exception as e:
                print(f"Error updating product {product.id}: {e}")
                continue
        
        db.session.commit()
        print(f"Successfully added sizes to {updated} products!")
        print(f"All products now have sizes: {ALL_SIZES}")

if __name__ == '__main__':
    add_sizes_to_products()

