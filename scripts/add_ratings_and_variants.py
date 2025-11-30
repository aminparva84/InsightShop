"""Add ratings and available colors/sizes to existing products."""
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

def add_ratings_and_variants():
    """Add ratings and available color/size variants to products."""
    with app.app_context():
        products = Product.query.filter_by(is_active=True).all()
        updated = 0
        
        # Group products by base name (without color)
        product_groups = {}
        for product in products:
            # Extract base name (remove color prefix)
            base_name = product.name
            for color in ALL_COLORS:
                if product.name.startswith(color + ' '):
                    base_name = product.name[len(color) + 1:]
                    break
            
            if base_name not in product_groups:
                product_groups[base_name] = []
            product_groups[base_name].append(product)
        
        # For each product group, collect available colors and sizes
        for base_name, group_products in product_groups.items():
            available_colors = list(set([p.color for p in group_products if p.color]))
            available_sizes = list(set([p.size for p in group_products if p.size]))
            
            # Update each product in the group with available variants
            for product in group_products:
                # Set available colors (at least the product's own color, plus some random others)
                if not product.available_colors:
                    colors_list = [product.color] if product.color else []
                    # Add 2-4 more random colors
                    other_colors = [c for c in ALL_COLORS if c != product.color]
                    additional_colors = random.sample(other_colors, min(random.randint(2, 4), len(other_colors)))
                    colors_list.extend(additional_colors)
                    product.available_colors = json.dumps(list(set(colors_list)))
                
                # Set available sizes (at least the product's own size, plus all standard sizes)
                if not product.available_sizes:
                    sizes_list = [product.size] if product.size else []
                    # Add all standard sizes
                    sizes_list.extend([s for s in ALL_SIZES if s not in sizes_list])
                    product.available_sizes = json.dumps(sizes_list)
                
                # Add random rating (3.5 to 5.0) and review count (10 to 500)
                if not product.rating or product.rating == 0:
                    product.rating = round(random.uniform(3.5, 5.0), 2)
                    product.review_count = random.randint(10, 500)
                
                updated += 1
                
                if updated % 100 == 0:
                    db.session.commit()
                    print(f"Updated {updated} products...")
        
        db.session.commit()
        print(f"Successfully added ratings and variants to {updated} products!")

if __name__ == '__main__':
    add_ratings_and_variants()

