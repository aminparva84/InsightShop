"""Update product images with real clothing images from Unsplash."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.product import Product
from models.database import db

# Real clothing images from Unsplash based on product type
CLOTHING_IMAGES = {
    'T-Shirt': {
        'men': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400&h=400&fit=crop&q=80',
        'women': 'https://images.unsplash.com/photo-1594633313593-bab3825d0caf?w=400&h=400&fit=crop&q=80',
        'kids': 'https://images.unsplash.com/photo-1503341504253-dff4815485f1?w=400&h=400&fit=crop&q=80'
    },
    'Polo Shirt': {
        'men': 'https://images.unsplash.com/photo-1603252109303-2751441dd157?w=400&h=400&fit=crop&q=80',
        'women': 'https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=400&h=400&fit=crop&q=80',
        'kids': 'https://images.unsplash.com/photo-1503341504253-dff4815485f1?w=400&h=400&fit=crop&q=80'
    },
    'Dress Shirt': {
        'men': 'https://images.unsplash.com/photo-1594938291221-94f18cbb566b?w=400&h=400&fit=crop&q=80',
        'women': 'https://images.unsplash.com/photo-1594633313593-bab3825d0caf?w=400&h=400&fit=crop&q=80',
        'kids': 'https://images.unsplash.com/photo-1503341504253-dff4815485f1?w=400&h=400&fit=crop&q=80'
    },
    'Blouse': {
        'women': 'https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=400&h=400&fit=crop&q=80'
    },
    'Dress': {
        'women': 'https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=400&h=400&fit=crop&q=80',
        'kids': 'https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=400&h=400&fit=crop&q=80'
    },
    'Jeans': {
        'men': 'https://images.unsplash.com/photo-1542272604-787c3835535d?w=400&h=400&fit=crop&q=80',
        'women': 'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=400&h=400&fit=crop&q=80',
        'kids': 'https://images.unsplash.com/photo-1503341504253-dff4815485f1?w=400&h=400&fit=crop&q=80'
    },
    'Chinos': {
        'men': 'https://images.unsplash.com/photo-1542272604-787c3835535d?w=400&h=400&fit=crop&q=80'
    },
    'Shorts': {
        'men': 'https://images.unsplash.com/photo-1591195853828-11b59e5b3c00?w=400&h=400&fit=crop&q=80',
        'women': 'https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=400&h=400&fit=crop&q=80',
        'kids': 'https://images.unsplash.com/photo-1503341504253-dff4815485f1?w=400&h=400&fit=crop&q=80'
    },
    'Skirt': {
        'women': 'https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=400&h=400&fit=crop&q=80'
    },
    'Leggings': {
        'women': 'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=400&h=400&fit=crop&q=80'
    },
    'Hoodie': {
        'men': 'https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=400&h=400&fit=crop&q=80',
        'women': 'https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=400&h=400&fit=crop&q=80',
        'kids': 'https://images.unsplash.com/photo-1503341504253-dff4815485f1?w=400&h=400&fit=crop&q=80'
    },
    'Sweater': {
        'men': 'https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=400&h=400&fit=crop&q=80',
        'women': 'https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=400&h=400&fit=crop&q=80',
        'kids': 'https://images.unsplash.com/photo-1503341504253-dff4815485f1?w=400&h=400&fit=crop&q=80'
    },
    'Jacket': {
        'men': 'https://images.unsplash.com/photo-1551028719-00167b16eac5?w=400&h=400&fit=crop&q=80',
        'women': 'https://images.unsplash.com/photo-1551028719-00167b16eac5?w=400&h=400&fit=crop&q=80',
        'kids': 'https://images.unsplash.com/photo-1503341504253-dff4815485f1?w=400&h=400&fit=crop&q=80'
    },
    'Blazer': {
        'men': 'https://images.unsplash.com/photo-1594938291221-94f18cbb566b?w=400&h=400&fit=crop&q=80'
    },
    'Coat': {
        'women': 'https://images.unsplash.com/photo-1551028719-00167b16eac5?w=400&h=400&fit=crop&q=80'
    },
    'Suit': {
        'men': 'https://images.unsplash.com/photo-1594938291221-94f18cbb566b?w=400&h=400&fit=crop&q=80'
    },
    'Underwear': {
        'men': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400&h=400&fit=crop&q=80',
        'women': 'https://images.unsplash.com/photo-1594633313593-bab3825d0caf?w=400&h=400&fit=crop&q=80',
        'kids': 'https://images.unsplash.com/photo-1503341504253-dff4815485f1?w=400&h=400&fit=crop&q=80'
    },
    'Bra': {
        'women': 'https://images.unsplash.com/photo-1594633313593-bab3825d0caf?w=400&h=400&fit=crop&q=80'
    },
    'Socks': {
        'men': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400&h=400&fit=crop&q=80',
        'women': 'https://images.unsplash.com/photo-1594633313593-bab3825d0caf?w=400&h=400&fit=crop&q=80',
        'kids': 'https://images.unsplash.com/photo-1503341504253-dff4815485f1?w=400&h=400&fit=crop&q=80'
    },
    'Shoes': {
        'men': 'https://images.unsplash.com/photo-1549298916-b41d501d3772?w=400&h=400&fit=crop&q=80',
        'women': 'https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=400&h=400&fit=crop&q=80',
        'kids': 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&h=400&fit=crop&q=80'
    },
    'Sneakers': {
        'men': 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&h=400&fit=crop&q=80',
        'women': 'https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=400&h=400&fit=crop&q=80',
        'kids': 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&h=400&fit=crop&q=80'
    },
    'Heels': {
        'women': 'https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=400&h=400&fit=crop&q=80'
    },
    'Sandals': {
        'women': 'https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=400&h=400&fit=crop&q=80'
    },
    'Pajamas': {
        'kids': 'https://images.unsplash.com/photo-1503341504253-dff4815485f1?w=400&h=400&fit=crop&q=80'
    }
}

def get_image_url(product_name, category):
    """Get appropriate image URL based on product name and category."""
    # Extract clothing type from product name
    for clothing_type, categories in CLOTHING_IMAGES.items():
        if clothing_type.lower() in product_name.lower():
            if category in categories:
                return categories[category]
            # Fallback to first available category
            if categories:
                return list(categories.values())[0]
    
    # Default images by category
    defaults = {
        'men': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400&h=400&fit=crop&q=80',
        'women': 'https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=400&h=400&fit=crop&q=80',
        'kids': 'https://images.unsplash.com/photo-1503341504253-dff4815485f1?w=400&h=400&fit=crop&q=80'
    }
    return defaults.get(category, defaults['men'])

def update_product_images():
    """Update all product images with real clothing images."""
    with app.app_context():
        products = Product.query.all()
        updated = 0
        
        for product in products:
            product.image_url = get_image_url(product.name, product.category)
            updated += 1
            
            if updated % 100 == 0:
                db.session.commit()
                print(f"Updated {updated} products...")
        
        db.session.commit()
        print(f"Successfully updated {updated} product images with real clothing photos!")

if __name__ == '__main__':
    update_product_images()

