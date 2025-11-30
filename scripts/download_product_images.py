"""Download unique images for each product from Unsplash API."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.product import Product
from models.database import db
import requests
import time
import random
from urllib.parse import quote

# Unsplash API - You can get a free API key from https://unsplash.com/developers
# For now, we'll use Unsplash Source API which doesn't require authentication
UNSPLASH_SOURCE_BASE = "https://source.unsplash.com/600x400/?"

# Alternative: Use Unsplash API with your access key (uncomment and add your key)
# UNSPLASH_ACCESS_KEY = os.getenv('UNSPLASH_ACCESS_KEY', '')
# UNSPLASH_API_BASE = "https://api.unsplash.com/search/photos"

# Search terms mapping for different product types
SEARCH_TERMS = {
    'T-Shirt': {
        'men': ['men t-shirt', 'male t-shirt', 'mens casual shirt'],
        'women': ['women t-shirt', 'female t-shirt', 'womens casual shirt'],
        'kids': ['kids t-shirt', 'children t-shirt', 'child t-shirt']
    },
    'Polo Shirt': {
        'men': ['men polo shirt', 'male polo', 'mens polo'],
        'women': ['women polo shirt', 'female polo', 'womens polo'],
        'kids': ['kids polo shirt', 'children polo']
    },
    'Dress Shirt': {
        'men': ['men dress shirt', 'male dress shirt', 'mens formal shirt'],
        'women': ['women dress shirt', 'female dress shirt', 'womens blouse'],
        'kids': ['kids dress shirt', 'children dress shirt']
    },
    'Blouse': {
        'women': ['women blouse', 'female blouse', 'womens blouse', 'ladies blouse']
    },
    'Dress': {
        'women': ['women dress', 'female dress', 'womens dress', 'ladies dress'],
        'kids': ['kids dress', 'children dress', 'girls dress']
    },
    'Jeans': {
        'men': ['men jeans', 'male jeans', 'mens jeans'],
        'women': ['women jeans', 'female jeans', 'womens jeans'],
        'kids': ['kids jeans', 'children jeans']
    },
    'Chinos': {
        'men': ['men chinos', 'male chinos', 'mens chinos']
    },
    'Shorts': {
        'men': ['men shorts', 'male shorts', 'mens shorts'],
        'women': ['women shorts', 'female shorts', 'womens shorts'],
        'kids': ['kids shorts', 'children shorts']
    },
    'Skirt': {
        'women': ['women skirt', 'female skirt', 'womens skirt', 'ladies skirt']
    },
    'Leggings': {
        'women': ['women leggings', 'female leggings', 'womens leggings']
    },
    'Hoodie': {
        'men': ['men hoodie', 'male hoodie', 'mens hoodie'],
        'women': ['women hoodie', 'female hoodie', 'womens hoodie'],
        'kids': ['kids hoodie', 'children hoodie']
    },
    'Sweater': {
        'men': ['men sweater', 'male sweater', 'mens sweater'],
        'women': ['women sweater', 'female sweater', 'womens sweater'],
        'kids': ['kids sweater', 'children sweater']
    },
    'Jacket': {
        'men': ['men jacket', 'male jacket', 'mens jacket'],
        'women': ['women jacket', 'female jacket', 'womens jacket'],
        'kids': ['kids jacket', 'children jacket']
    },
    'Blazer': {
        'men': ['men blazer', 'male blazer', 'mens blazer'],
        'women': ['women blazer', 'female blazer', 'womens blazer']
    },
    'Coat': {
        'women': ['women coat', 'female coat', 'womens coat']
    },
    'Suit': {
        'men': ['men suit', 'male suit', 'mens suit']
    },
    'Shoes': {
        'men': ['men shoes', 'male shoes', 'mens shoes'],
        'women': ['women shoes', 'female shoes', 'womens shoes'],
        'kids': ['kids shoes', 'children shoes']
    },
    'Sneakers': {
        'men': ['men sneakers', 'male sneakers', 'mens sneakers'],
        'women': ['women sneakers', 'female sneakers', 'womens sneakers'],
        'kids': ['kids sneakers', 'children sneakers']
    },
    'Heels': {
        'women': ['women heels', 'female heels', 'womens heels', 'ladies heels']
    },
    'Sandals': {
        'women': ['women sandals', 'female sandals', 'womens sandals']
    },
    'Pajamas': {
        'kids': ['kids pajamas', 'children pajamas', 'kids sleepwear']
    }
}

def get_search_term(product):
    """Get search term for a product."""
    product_name_lower = product.name.lower()
    category = product.category.lower()
    color = product.color.lower() if product.color else None
    
    # Find matching clothing type
    for clothing_type, categories in SEARCH_TERMS.items():
        if clothing_type.lower() in product_name_lower:
            if category in categories:
                terms = categories[category]
                # Add color to search term if available
                if color:
                    return f"{color} {random.choice(terms)}"
                return random.choice(terms)
    
    # Fallback
    if category == 'men':
        return f"men {product_name_lower}"
    elif category == 'women':
        return f"women {product_name_lower}"
    else:
        return f"kids {product_name_lower}"

def get_image_url_unsplash_source(search_term):
    """Get image URL from Unsplash Source (no API key needed)."""
    # Use Unsplash Source API - random image based on search term
    encoded_term = quote(search_term)
    # Add random seed based on product ID to get different images
    return f"{UNSPLASH_SOURCE_BASE}{encoded_term}&sig={random.randint(1000, 9999)}"

def get_image_url_unsplash_api(search_term, access_key):
    """Get image URL from Unsplash API (requires API key)."""
    if not access_key:
        return None
    
    try:
        url = f"{UNSPLASH_API_BASE}?query={quote(search_term)}&per_page=30&client_id={access_key}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('results') and len(data['results']) > 0:
                # Select a random image from results
                photo = random.choice(data['results'])
                return photo['urls']['regular']
    except Exception as e:
        print(f"Error fetching from Unsplash API: {e}")
    
    return None

def download_product_images(use_api=False, access_key=None, limit=None):
    """Download and assign unique images to products."""
    with app.app_context():
        products = Product.query.filter_by(is_active=True).all()
        
        if limit:
            products = products[:limit]
        
        updated = 0
        failed = 0
        
        print(f"Starting to download images for {len(products)} products...")
        print("Using Unsplash Source API (no authentication required)")
        if use_api and access_key:
            print("Using Unsplash API with access key")
        
        for i, product in enumerate(products, 1):
            try:
                search_term = get_search_term(product)
                
                if use_api and access_key:
                    image_url = get_image_url_unsplash_api(search_term, access_key)
                    if not image_url:
                        # Fallback to source API
                        image_url = get_image_url_unsplash_source(search_term)
                else:
                    image_url = get_image_url_unsplash_source(search_term)
                
                product.image_url = image_url
                updated += 1
                
                if i % 100 == 0:
                    db.session.commit()
                    print(f"Updated {i}/{len(products)} products... (Success: {updated}, Failed: {failed})")
                    # Rate limiting - be respectful to Unsplash
                    time.sleep(1)
                
            except Exception as e:
                print(f"Error processing product {product.id}: {e}")
                failed += 1
                # Use a default image on error
                defaults = {
                    'men': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=600&h=400&fit=crop&q=80',
                    'women': 'https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=600&h=400&fit=crop&q=80',
                    'kids': 'https://images.unsplash.com/photo-1503341504253-dff4815485f1?w=600&h=400&fit=crop&q=80'
                }
                product.image_url = defaults.get(product.category.lower(), defaults['men'])
        
        db.session.commit()
        print(f"\n✅ Successfully updated {updated} product images!")
        print(f"❌ Failed: {failed} products")
        print(f"\nNote: Images are loaded from Unsplash on-demand. For production, consider:")
        print("1. Downloading and hosting images locally")
        print("2. Using Unsplash API with your access key for better results")
        print("3. Caching images to reduce API calls")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Download product images from Unsplash')
    parser.add_argument('--limit', type=int, help='Limit number of products to update')
    parser.add_argument('--use-api', action='store_true', help='Use Unsplash API (requires access key)')
    parser.add_argument('--access-key', type=str, help='Unsplash API access key')
    
    args = parser.parse_args()
    
    download_product_images(
        use_api=args.use_api,
        access_key=args.access_key or os.getenv('UNSPLASH_ACCESS_KEY'),
        limit=args.limit
    )

