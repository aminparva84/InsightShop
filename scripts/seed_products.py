"""Seed the database with 1000 clothing products."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.database import db
from models.product import Product
try:
    from utils.vector_db import add_product_to_vector_db
    VECTOR_DB_AVAILABLE = True
except ImportError:
    VECTOR_DB_AVAILABLE = False
    print("Warning: Vector DB not available, skipping vector indexing")
import random
import string

# Product data
CATEGORIES = ['men', 'women', 'kids']
COLORS = ['Red', 'Blue', 'Green', 'Yellow', 'Black', 'White', 'Gray', 'Pink', 'Purple', 'Orange', 'Brown', 'Navy', 'Beige', 'Maroon', 'Teal']
SIZES = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
CLOTHING_TYPES = {
    'men': ['T-Shirt', 'Polo Shirt', 'Dress Shirt', 'Jeans', 'Chinos', 'Shorts', 'Hoodie', 'Sweater', 'Jacket', 'Blazer', 'Suit', 'Underwear', 'Socks', 'Shoes', 'Sneakers'],
    'women': ['T-Shirt', 'Blouse', 'Dress', 'Skirt', 'Jeans', 'Leggings', 'Shorts', 'Hoodie', 'Sweater', 'Jacket', 'Coat', 'Underwear', 'Bra', 'Socks', 'Shoes', 'Heels', 'Sandals'],
    'kids': ['T-Shirt', 'Polo Shirt', 'Dress', 'Jeans', 'Shorts', 'Hoodie', 'Sweater', 'Jacket', 'Underwear', 'Socks', 'Shoes', 'Sneakers', 'Pajamas']
}

DESCRIPTIONS = {
    'T-Shirt': 'Comfortable and stylish t-shirt made from premium cotton. Perfect for everyday wear.',
    'Polo Shirt': 'Classic polo shirt with a modern fit. Great for casual and semi-formal occasions.',
    'Dress Shirt': 'Professional dress shirt with a crisp, clean look. Perfect for the office.',
    'Blouse': 'Elegant blouse with a flattering fit. Versatile for work or casual wear.',
    'Dress': 'Beautiful dress that combines style and comfort. Perfect for any occasion.',
    'Jeans': 'Classic jeans with a perfect fit. Durable and comfortable for everyday wear.',
    'Chinos': 'Smart casual chinos that are both comfortable and stylish.',
    'Shorts': 'Comfortable shorts perfect for warm weather. Great for casual wear.',
    'Skirt': 'Stylish skirt that pairs well with any top. Versatile and comfortable.',
    'Leggings': 'Comfortable leggings perfect for active wear or casual outfits.',
    'Hoodie': 'Cozy hoodie perfect for cooler weather. Soft and comfortable.',
    'Sweater': 'Warm sweater that combines style and comfort. Perfect for layering.',
    'Jacket': 'Stylish jacket that provides warmth without bulk. Great for transitional weather.',
    'Blazer': 'Professional blazer that adds polish to any outfit.',
    'Coat': 'Warm coat perfect for cold weather. Stylish and functional.',
    'Suit': 'Professional suit that fits perfectly. Great for formal occasions.',
    'Underwear': 'Comfortable underwear made from breathable materials.',
    'Bra': 'Supportive and comfortable bra with a perfect fit.',
    'Socks': 'Comfortable socks that keep your feet warm and dry.',
    'Shoes': 'Stylish shoes that are both comfortable and durable.',
    'Sneakers': 'Comfortable sneakers perfect for everyday wear and light exercise.',
    'Heels': 'Elegant heels that add height and style to any outfit.',
    'Sandals': 'Comfortable sandals perfect for warm weather.',
    'Pajamas': 'Comfortable pajamas perfect for a good night\'s sleep.'
}

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

def generate_slug(name):
    """Generate a URL-friendly slug from a name."""
    slug = name.lower()
    slug = slug.replace(' ', '-')
    slug = ''.join(c for c in slug if c.isalnum() or c == '-')
    return slug

def generate_product_name(category, clothing_type, color):
    """Generate a product name."""
    return f"{color} {clothing_type} for {category.capitalize()}"

def generate_price(category, clothing_type):
    """Generate a realistic price based on category and type."""
    base_prices = {
        'men': {'T-Shirt': 25, 'Polo Shirt': 35, 'Dress Shirt': 45, 'Jeans': 60, 'Chinos': 50, 'Shorts': 35, 'Hoodie': 55, 'Sweater': 65, 'Jacket': 80, 'Blazer': 120, 'Suit': 200, 'Underwear': 15, 'Socks': 10, 'Shoes': 80, 'Sneakers': 90},
        'women': {'T-Shirt': 28, 'Blouse': 40, 'Dress': 70, 'Skirt': 45, 'Jeans': 65, 'Leggings': 35, 'Shorts': 38, 'Hoodie': 58, 'Sweater': 68, 'Jacket': 85, 'Coat': 120, 'Underwear': 18, 'Bra': 35, 'Socks': 12, 'Shoes': 85, 'Heels': 95, 'Sandals': 45},
        'kids': {'T-Shirt': 18, 'Polo Shirt': 25, 'Dress': 40, 'Jeans': 35, 'Shorts': 22, 'Hoodie': 40, 'Sweater': 45, 'Jacket': 55, 'Underwear': 12, 'Socks': 8, 'Shoes': 50, 'Sneakers': 55, 'Pajamas': 30}
    }
    
    base = base_prices.get(category, {}).get(clothing_type, 30)
    # Add some variation
    price = base + random.randint(-5, 15)
    return max(10, price)  # Minimum $10

def seed_products():
    """Seed the database with products."""
    with app.app_context():
        print("Starting to seed products...")
        
        products_created = 0
        
        for category in CATEGORIES:
            clothing_types = CLOTHING_TYPES[category]
            
            for clothing_type in clothing_types:
                for color in COLORS:
                    for size in SIZES:
                        # Create product
                        name = generate_product_name(category, clothing_type, color)
                        description = DESCRIPTIONS.get(clothing_type, f'High-quality {clothing_type.lower()} for {category}.')
                        price = generate_price(category, clothing_type)
                        slug = f"{generate_slug(name)}-{size.lower()}-{random.randint(1000, 9999)}"
                        
                        # Get fabric for this clothing type
                        available_fabrics = FABRICS.get(clothing_type, ['100% Cotton', 'Cotton Blend'])
                        fabric = random.choice(available_fabrics)
                        
                        # Determine occasion based on clothing type
                        occasion_map = {
                            'Suit': 'wedding,business_formal',
                            'Dress': 'wedding,date_night,business_casual',
                            'Blazer': 'business_formal,business_casual,date_night',
                            'Dress Shirt': 'business_formal,business_casual',
                            'Blouse': 'business_casual,date_night',
                            'T-Shirt': 'casual,summer',
                            'Jeans': 'casual',
                            'Chinos': 'business_casual,casual',
                            'Shorts': 'casual,summer,outdoor_active',
                            'Sneakers': 'casual,outdoor_active',
                            'Heels': 'business_casual,date_night,wedding',
                            'Sweater': 'winter,casual',
                            'Jacket': 'winter,casual',
                            'Coat': 'winter',
                            'Hoodie': 'casual,winter',
                            'Sandals': 'summer,casual',
                            'Pajamas': 'casual'
                        }
                        occasion = occasion_map.get(clothing_type, 'casual')
                        
                        # Determine age group
                        age_group_map = {
                            'Suit': 'mature',
                            'Dress': 'all',
                            'Blazer': 'mature',
                            'Dress Shirt': 'mature',
                            'T-Shirt': 'all',
                            'Hoodie': 'young_adult',
                            'Sneakers': 'all',
                            'Pajamas': 'all'
                        }
                        age_group = age_group_map.get(clothing_type, 'all')
                        
                        product = Product(
                            name=name,
                            description=description,
                            price=price,
                            category=category,
                            color=color,
                            size=size,
                            fabric=fabric,
                            clothing_type=clothing_type,
                            occasion=occasion,
                            age_group=age_group,
                            image_url=f"https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400&h=400&fit=crop&q=80",
                            stock_quantity=random.randint(5, 50),
                            is_active=True,
                            slug=slug,
                            meta_title=f"{name} - InsightShop",
                            meta_description=f"Shop {name} at InsightShop. {description}"
                        )
                        
                        db.session.add(product)
                        products_created += 1
                        
                        # Commit in batches
                        if products_created % 100 == 0:
                            db.session.commit()
                            print(f"Created {products_created} products...")
        
        # Final commit
        db.session.commit()
        print(f"Successfully created {products_created} products!")
        
        # Add products to vector database
        if VECTOR_DB_AVAILABLE:
            print("Adding products to vector database...")
            products = Product.query.all()
            for i, product in enumerate(products):
                try:
                    add_product_to_vector_db(product.id, product.to_dict())
                    if (i + 1) % 100 == 0:
                        print(f"Added {i + 1} products to vector database...")
                except Exception as e:
                    print(f"Error adding product {product.id} to vector DB: {e}")
        else:
            print("Skipping vector database (not available)")
        
        print("Product seeding completed!")

if __name__ == '__main__':
    seed_products()

