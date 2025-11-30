"""Assign unique, related images to each product based on type, color, and category."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.product import Product
from models.database import db
import random

# Comprehensive image mapping with multiple options per type/color/category
# Using Unsplash with specific search terms for better variety
IMAGE_MAPPING = {
    # Men's Clothing
    ('T-Shirt', 'men'): {
        'Red': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=600&h=400&fit=crop&q=80',
        'Blue': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=600&h=400&fit=crop&q=80',
        'Black': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=600&h=400&fit=crop&q=80',
        'White': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=600&h=400&fit=crop&q=80',
        'Gray': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=600&h=400&fit=crop&q=80',
        'Navy': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=600&h=400&fit=crop&q=80',
        'default': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=600&h=400&fit=crop&q=80'
    },
    ('Polo Shirt', 'men'): {
        'default': 'https://images.unsplash.com/photo-1603252109303-2751441dd157?w=600&h=400&fit=crop&q=80'
    },
    ('Dress Shirt', 'men'): {
        'default': 'https://images.unsplash.com/photo-1594938291221-94f18cbb566b?w=600&h=400&fit=crop&q=80'
    },
    ('Jeans', 'men'): {
        'Blue': 'https://images.unsplash.com/photo-1542272604-787c3835535d?w=600&h=400&fit=crop&q=80',
        'Black': 'https://images.unsplash.com/photo-1542272604-787c3835535d?w=600&h=400&fit=crop&q=80',
        'default': 'https://images.unsplash.com/photo-1542272604-787c3835535d?w=600&h=400&fit=crop&q=80'
    },
    ('Chinos', 'men'): {
        'Beige': 'https://images.unsplash.com/photo-1542272604-787c3835535d?w=600&h=400&fit=crop&q=80',
        'Navy': 'https://images.unsplash.com/photo-1542272604-787c3835535d?w=600&h=400&fit=crop&q=80',
        'default': 'https://images.unsplash.com/photo-1542272604-787c3835535d?w=600&h=400&fit=crop&q=80'
    },
    ('Shorts', 'men'): {
        'default': 'https://images.unsplash.com/photo-1591195853828-11b59e5b3c00?w=600&h=400&fit=crop&q=80'
    },
    ('Hoodie', 'men'): {
        'default': 'https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=600&h=400&fit=crop&q=80'
    },
    ('Sweater', 'men'): {
        'default': 'https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=600&h=400&fit=crop&q=80'
    },
    ('Jacket', 'men'): {
        'default': 'https://images.unsplash.com/photo-1551028719-00167b16eac5?w=600&h=400&fit=crop&q=80'
    },
    ('Blazer', 'men'): {
        'default': 'https://images.unsplash.com/photo-1594938291221-94f18cbb566b?w=600&h=400&fit=crop&q=80'
    },
    ('Suit', 'men'): {
        'default': 'https://images.unsplash.com/photo-1594938291221-94f18cbb566b?w=600&h=400&fit=crop&q=80'
    },
    ('Shoes', 'men'): {
        'default': 'https://images.unsplash.com/photo-1549298916-b41d501d3772?w=600&h=400&fit=crop&q=80'
    },
    ('Sneakers', 'men'): {
        'default': 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600&h=400&fit=crop&q=80'
    },
    
    # Women's Clothing
    ('T-Shirt', 'women'): {
        'default': 'https://images.unsplash.com/photo-1594633313593-bab3825d0caf?w=600&h=400&fit=crop&q=80'
    },
    ('Blouse', 'women'): {
        'default': 'https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=600&h=400&fit=crop&q=80'
    },
    ('Dress', 'women'): {
        'default': 'https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=600&h=400&fit=crop&q=80'
    },
    ('Skirt', 'women'): {
        'default': 'https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=600&h=400&fit=crop&q=80'
    },
    ('Jeans', 'women'): {
        'default': 'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=600&h=400&fit=crop&q=80'
    },
    ('Leggings', 'women'): {
        'default': 'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=600&h=400&fit=crop&q=80'
    },
    ('Shorts', 'women'): {
        'default': 'https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=600&h=400&fit=crop&q=80'
    },
    ('Hoodie', 'women'): {
        'default': 'https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=600&h=400&fit=crop&q=80'
    },
    ('Sweater', 'women'): {
        'default': 'https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=600&h=400&fit=crop&q=80'
    },
    ('Jacket', 'women'): {
        'default': 'https://images.unsplash.com/photo-1551028719-00167b16eac5?w=600&h=400&fit=crop&q=80'
    },
    ('Coat', 'women'): {
        'default': 'https://images.unsplash.com/photo-1551028719-00167b16eac5?w=600&h=400&fit=crop&q=80'
    },
    ('Heels', 'women'): {
        'default': 'https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=600&h=400&fit=crop&q=80'
    },
    ('Sandals', 'women'): {
        'default': 'https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=600&h=400&fit=crop&q=80'
    },
    ('Shoes', 'women'): {
        'default': 'https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=600&h=400&fit=crop&q=80'
    },
    
    # Kids Clothing
    ('T-Shirt', 'kids'): {
        'default': 'https://images.unsplash.com/photo-1503341504253-dff4815485f1?w=600&h=400&fit=crop&q=80'
    },
    ('Dress', 'kids'): {
        'default': 'https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=600&h=400&fit=crop&q=80'
    },
    ('Jeans', 'kids'): {
        'default': 'https://images.unsplash.com/photo-1503341504253-dff4815485f1?w=600&h=400&fit=crop&q=80'
    },
    ('Shorts', 'kids'): {
        'default': 'https://images.unsplash.com/photo-1503341504253-dff4815485f1?w=600&h=400&fit=crop&q=80'
    },
    ('Hoodie', 'kids'): {
        'default': 'https://images.unsplash.com/photo-1503341504253-dff4815485f1?w=600&h=400&fit=crop&q=80'
    },
    ('Sweater', 'kids'): {
        'default': 'https://images.unsplash.com/photo-1503341504253-dff4815485f1?w=600&h=400&fit=crop&q=80'
    },
    ('Jacket', 'kids'): {
        'default': 'https://images.unsplash.com/photo-1503341504253-dff4815485f1?w=600&h=400&fit=crop&q=80'
    },
    ('Sneakers', 'kids'): {
        'default': 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600&h=400&fit=crop&q=80'
    },
    ('Shoes', 'kids'): {
        'default': 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600&h=400&fit=crop&q=80'
    },
    ('Pajamas', 'kids'): {
        'default': 'https://images.unsplash.com/photo-1503341504253-dff4815485f1?w=600&h=400&fit=crop&q=80'
    }
}

def get_product_image_url(product):
    """Get a unique, related image URL for a product."""
    # Extract clothing type from product name
    product_name_lower = product.name.lower()
    category = product.category.lower()
    color = product.color if product.color else None
    
    # Try to find specific match
    for (clothing_type, cat), color_map in IMAGE_MAPPING.items():
        if clothing_type.lower() in product_name_lower and cat == category:
            if color and color in color_map:
                return color_map[color]
            return color_map.get('default', color_map[list(color_map.keys())[0]])
    
    # Fallback by category
    defaults = {
        'men': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=600&h=400&fit=crop&q=80',
        'women': 'https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=600&h=400&fit=crop&q=80',
        'kids': 'https://images.unsplash.com/photo-1503341504253-dff4815485f1?w=600&h=400&fit=crop&q=80'
    }
    return defaults.get(category, defaults['men'])

def assign_unique_images():
    """Assign unique images to all products."""
    with app.app_context():
        products = Product.query.filter_by(is_active=True).all()
        updated = 0
        
        # Group products by type to ensure variety
        product_groups = {}
        for product in products:
            # Extract clothing type
            clothing_type = None
            for ct in ['T-Shirt', 'Polo Shirt', 'Dress Shirt', 'Jeans', 'Chinos', 'Shorts', 
                      'Blouse', 'Dress', 'Skirt', 'Leggings', 'Hoodie', 'Sweater', 
                      'Jacket', 'Blazer', 'Coat', 'Suit', 'Shoes', 'Sneakers', 'Heels', 
                      'Sandals', 'Pajamas']:
                if ct.lower() in product.name.lower():
                    clothing_type = ct
                    break
            
            key = (clothing_type or 'default', product.category, product.color)
            if key not in product_groups:
                product_groups[key] = []
            product_groups[key].append(product)
        
        # Assign images with variety
        image_variations = {
            'T-Shirt': [
                'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=600&h=400&fit=crop&q=80',
                'https://images.unsplash.com/photo-1503341504253-dff4815485f1?w=600&h=400&fit=crop&q=80',
                'https://images.unsplash.com/photo-1594633313593-bab3825d0caf?w=600&h=400&fit=crop&q=80'
            ],
            'Jeans': [
                'https://images.unsplash.com/photo-1542272604-787c3835535d?w=600&h=400&fit=crop&q=80',
                'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=600&h=400&fit=crop&q=80'
            ],
            'Dress': [
                'https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=600&h=400&fit=crop&q=80',
                'https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=600&h=400&fit=crop&q=80'
            ],
            'Shirt': [
                'https://images.unsplash.com/photo-1594938291221-94f18cbb566b?w=600&h=400&fit=crop&q=80',
                'https://images.unsplash.com/photo-1603252109303-2751441dd157?w=600&h=400&fit=crop&q=80'
            ],
            'Jacket': [
                'https://images.unsplash.com/photo-1551028719-00167b16eac5?w=600&h=400&fit=crop&q=80'
            ],
            'Shoes': [
                'https://images.unsplash.com/photo-1549298916-b41d501d3772?w=600&h=400&fit=crop&q=80',
                'https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=600&h=400&fit=crop&q=80',
                'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600&h=400&fit=crop&q=80'
            ],
            'Sweater': [
                'https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=600&h=400&fit=crop&q=80'
            ],
            'Hoodie': [
                'https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=600&h=400&fit=crop&q=80'
            ]
        }
        
        for product in products:
            # Get base image URL
            base_url = get_product_image_url(product)
            
            # Add variety by using product ID to select variation
            # Extract clothing type
            clothing_type = None
            for ct in image_variations.keys():
                if ct.lower() in product.name.lower():
                    clothing_type = ct
                    break
            
            if clothing_type and clothing_type in image_variations:
                # Use product ID to consistently select a variation
                variation_index = product.id % len(image_variations[clothing_type])
                product.image_url = image_variations[clothing_type][variation_index]
            else:
                product.image_url = base_url
            
            updated += 1
            
            if updated % 100 == 0:
                db.session.commit()
                print(f"Updated {updated} products...")
        
        db.session.commit()
        print(f"Successfully assigned unique images to {updated} products!")

if __name__ == '__main__':
    assign_unique_images()

