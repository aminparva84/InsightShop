"""Add occasion, age_group, clothing_type fields and extract them from existing products."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.product import Product
from models.database import db
import re

# Clothing type mapping from product names
CLOTHING_TYPES = {
    'T-Shirt': ['t-shirt', 'tshirt', 'tee'],
    'Polo Shirt': ['polo'],
    'Dress Shirt': ['dress shirt', 'button-down', 'button down'],
    'Blouse': ['blouse'],
    'Dress': ['dress'],
    'Jeans': ['jeans'],
    'Chinos': ['chinos'],
    'Shorts': ['shorts'],
    'Skirt': ['skirt'],
    'Leggings': ['leggings'],
    'Hoodie': ['hoodie'],
    'Sweater': ['sweater'],
    'Jacket': ['jacket'],
    'Blazer': ['blazer'],
    'Coat': ['coat'],
    'Suit': ['suit'],
    'Shoes': ['shoes'],
    'Sneakers': ['sneakers'],
    'Heels': ['heels'],
    'Sandals': ['sandals'],
    'Pajamas': ['pajamas', 'pjs']
}

# Occasion mapping based on product characteristics
OCCASION_MAPPING = {
    'wedding': ['suit', 'dress', 'blazer', 'formal', 'elegant'],
    'business_formal': ['suit', 'dress shirt', 'blazer', 'dress'],
    'business_casual': ['chinos', 'dress shirt', 'blazer', 'polo shirt', 'dress pants'],
    'casual': ['t-shirt', 'jeans', 'shorts', 'hoodie', 'sneakers'],
    'date_night': ['dress', 'blazer', 'button-down', 'dress shirt'],
    'outdoor_active': ['sneakers', 'shorts', 'athletic'],
    'summer': ['shorts', 'dress', 'sandals', 't-shirt'],
    'winter': ['coat', 'sweater', 'jacket', 'hoodie']
}

# Age group mapping
AGE_GROUP_MAPPING = {
    'young_adult': ['t-shirt', 'hoodie', 'sneakers', 'jeans', 'shorts'],
    'mature': ['dress shirt', 'blazer', 'chinos', 'suit', 'dress'],
    'senior': ['comfortable', 'classic', 'suit', 'dress', 'blazer'],
    'all': []  # Default for versatile items
}

def extract_clothing_type(product_name):
    """Extract clothing type from product name."""
    name_lower = product_name.lower()
    for clothing_type, keywords in CLOTHING_TYPES.items():
        for keyword in keywords:
            if keyword in name_lower:
                return clothing_type
    return None

def determine_occasion(product):
    """Determine appropriate occasions for a product."""
    occasions = []
    name_lower = product.name.lower()
    description_lower = (product.description or '').lower()
    combined_text = f"{name_lower} {description_lower}"
    
    for occasion, keywords in OCCASION_MAPPING.items():
        for keyword in keywords:
            if keyword in combined_text:
                if occasion not in occasions:
                    occasions.append(occasion)
    
    # Default to casual if no specific occasion found
    if not occasions:
        occasions = ['casual']
    
    # Return as comma-separated string for storage
    return ','.join(occasions)

def determine_age_group(product):
    """Determine appropriate age group for a product."""
    name_lower = product.name.lower()
    description_lower = (product.description or '').lower()
    combined_text = f"{name_lower} {description_lower}"
    
    # Check for age-specific keywords
    if any(keyword in combined_text for keyword in ['classic', 'elegant', 'sophisticated', 'mature', 'professional']):
        return 'mature'
    elif any(keyword in combined_text for keyword in ['young', 'trendy', 'casual', 'sporty']):
        return 'young_adult'
    elif any(keyword in combined_text for keyword in ['comfortable', 'easy', 'relaxed']):
        return 'senior'
    else:
        # Default based on category
        if product.category == 'kids':
            return 'young_adult'
        elif product.category in ['men', 'women']:
            # Check clothing type
            clothing_type = extract_clothing_type(product.name)
            if clothing_type in ['Suit', 'Dress', 'Blazer', 'Dress Shirt']:
                return 'mature'
            else:
                return 'all'
        return 'all'

def add_search_fields():
    """Add occasion, age_group, and clothing_type to all products."""
    with app.app_context():
        print("Starting to add search fields to products...")
        products = Product.query.all()
        updated_count = 0
        
        for product in products:
            updated = False
            
            # Extract clothing type
            if not product.clothing_type:
                clothing_type = extract_clothing_type(product.name)
                if clothing_type:
                    product.clothing_type = clothing_type
                    updated = True
            
            # Determine occasion
            if not product.occasion:
                occasion = determine_occasion(product)
                if occasion:
                    product.occasion = occasion
                    updated = True
            
            # Determine age group
            if not product.age_group:
                age_group = determine_age_group(product)
                if age_group:
                    product.age_group = age_group
                    updated = True
            
            if updated:
                db.session.add(product)
                updated_count += 1
                
                if updated_count % 100 == 0:
                    db.session.commit()
                    print(f"Updated {updated_count} products...")
        
        db.session.commit()
        print(f"Successfully added search fields to {updated_count} products!")
        print(f"Total products: {len(products)}")

if __name__ == '__main__':
    add_search_fields()

