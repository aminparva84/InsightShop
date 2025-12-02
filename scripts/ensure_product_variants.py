"""Ensure all products have multiple available colors and sizes."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.product import Product
from models.database import db
import json
import random

# Available colors and sizes
ALL_COLORS = ['Red', 'Blue', 'Green', 'Yellow', 'Black', 'White', 'Gray', 'Pink', 'Purple', 'Orange', 'Brown', 'Navy', 'Beige', 'Maroon', 'Teal']
ALL_SIZES = ['XS', 'S', 'M', 'L', 'XL', 'XXL']

def ensure_product_variants():
    """Ensure all products have multiple available colors and all sizes."""
    with app.app_context():
        products = Product.query.filter_by(is_active=True).all()
        updated_colors = 0
        updated_sizes = 0
        
        for product in products:
            updated = False
            
            # Ensure product has multiple colors (3-6 colors)
            try:
                current_colors = []
                if product.available_colors:
                    try:
                        current_colors = json.loads(product.available_colors) if isinstance(product.available_colors, str) else product.available_colors
                    except:
                        current_colors = [product.color] if product.color else []
                else:
                    current_colors = [product.color] if product.color else []
                
                # If product has less than 3 colors, add more
                if len(current_colors) < 3:
                    # Start with the product's primary color
                    colors_list = [product.color] if product.color and product.color not in current_colors else current_colors
                    
                    # Add 2-5 more random colors (total 3-6 colors)
                    other_colors = [c for c in ALL_COLORS if c not in colors_list]
                    num_additional = random.randint(2, 5)
                    additional_colors = random.sample(other_colors, min(num_additional, len(other_colors)))
                    colors_list.extend(additional_colors)
                    
                    # Ensure we have at least 3 colors
                    while len(colors_list) < 3:
                        remaining = [c for c in ALL_COLORS if c not in colors_list]
                        if remaining:
                            colors_list.append(random.choice(remaining))
                        else:
                            break
                    
                    product.available_colors = json.dumps(list(set(colors_list)))
                    updated_colors += 1
                    updated = True
                elif len(current_colors) > 6:
                    # Limit to 6 colors max
                    product.available_colors = json.dumps(current_colors[:6])
                    updated_colors += 1
                    updated = True
            except Exception as e:
                print(f"Error updating colors for product {product.id}: {e}")
            
            # Ensure product has all standard sizes
            try:
                current_sizes = []
                if product.available_sizes:
                    try:
                        current_sizes = json.loads(product.available_sizes) if isinstance(product.available_sizes, str) else product.available_sizes
                    except:
                        current_sizes = [product.size] if product.size else []
                else:
                    current_sizes = [product.size] if product.size else []
                
                # Ensure all standard sizes are present
                final_sizes = []
                for size in ALL_SIZES:
                    if size not in final_sizes:
                        final_sizes.append(size)
                
                # If sizes are different, update
                if set(current_sizes) != set(final_sizes):
                    product.available_sizes = json.dumps(final_sizes)
                    updated_sizes += 1
                    updated = True
            except Exception as e:
                print(f"Error updating sizes for product {product.id}: {e}")
            
            if updated and (updated_colors + updated_sizes) % 100 == 0:
                db.session.commit()
                print(f"Updated {updated_colors + updated_sizes} product variants...")
        
        db.session.commit()
        print(f"\nSuccessfully updated product variants!")
        print(f"  - Colors updated: {updated_colors} products")
        print(f"  - Sizes updated: {updated_sizes} products")
        print(f"  - All products now have 3-6 colors and all 6 sizes")

if __name__ == '__main__':
    ensure_product_variants()

