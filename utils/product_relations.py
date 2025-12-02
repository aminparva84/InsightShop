"""Utility functions for managing product relations based on clothing types."""

from models.database import db
from models.product import Product
from sqlalchemy import or_, and_

# Import ProductRelation with error handling in case table doesn't exist yet
try:
    from models.product_relation import ProductRelation
except ImportError:
    ProductRelation = None

# Clothing type compatibility mapping
# Maps clothing types to related types that go well together
CLOTHING_TYPE_RELATIONS = {
    'T-Shirt': ['Shoes', 'Sneakers', 'Socks', 'Jeans', 'Shorts'],
    'Shirt': ['Shoes', 'Socks', 'Pants', 'Chinos'],
    'Dress Shirt': ['Shoes', 'Socks', 'Dress Pants', 'Chinos'],
    'Polo Shirt': ['Shoes', 'Sneakers', 'Socks', 'Shorts', 'Jeans'],
    'Blouse': ['Shoes', 'Heels', 'Socks', 'Skirt', 'Pants'],
    'Dress': ['Shoes', 'Heels', 'Sandals', 'Socks'],
    'Jeans': ['Shoes', 'Sneakers', 'Boots', 'Socks'],
    'Chinos': ['Shoes', 'Sneakers', 'Socks'],
    'Shorts': ['Shoes', 'Sneakers', 'Sandals', 'Socks'],
    'Skirt': ['Shoes', 'Heels', 'Sandals', 'Socks'],
    'Leggings': ['Shoes', 'Sneakers', 'Socks'],
    'Hoodie': ['Shoes', 'Sneakers', 'Socks'],
    'Sweater': ['Shoes', 'Sneakers', 'Socks'],
    'Jacket': ['Shoes', 'Sneakers', 'Socks'],
    'Blazer': ['Shoes', 'Socks'],
    'Coat': ['Shoes', 'Boots', 'Socks'],
    'Suit': ['Shoes', 'Socks'],
    'Pants': ['Shoes', 'Sneakers', 'Socks'],
    'Trousers': ['Shoes', 'Socks'],
}

def get_related_clothing_types(clothing_type):
    """Get related clothing types for a given clothing type."""
    if not clothing_type:
        return []
    
    # Direct match
    if clothing_type in CLOTHING_TYPE_RELATIONS:
        return CLOTHING_TYPE_RELATIONS[clothing_type]
    
    # Partial match (e.g., "T-Shirt" matches "T-Shirt")
    for key, related in CLOTHING_TYPE_RELATIONS.items():
        if key.lower() in clothing_type.lower() or clothing_type.lower() in key.lower():
            return related
    
    # Default: if it's a top, suggest shoes and socks
    top_keywords = ['shirt', 'blouse', 'top', 'tee', 't-shirt', 'polo']
    if any(keyword in clothing_type.lower() for keyword in top_keywords):
        return ['Shoes', 'Sneakers', 'Socks']
    
    return []

def ensure_product_relations(product_id, clothing_type=None):
    """
    Ensure that product relations exist for a given product.
    If relations don't exist, create them based on clothing type.
    """
    if not product_id:
        return []
    
    # Get the product
    product = Product.query.get(product_id)
    if not product or not product.is_active:
        return []
    
    # Use product's clothing_type if not provided
    if not clothing_type:
        clothing_type = product.clothing_type
    
    # Get related clothing types
    related_types = get_related_clothing_types(clothing_type)
    if not related_types:
        return []
    
    # Find existing relations
    if not ProductRelation:
        return []
    
    existing_relations = ProductRelation.query.filter_by(
        product_id=product_id,
        is_fashion_match=True
    ).all()
    existing_related_ids = {rel.related_product_id for rel in existing_relations}
    
    # Find products with matching clothing types
    related_products = Product.query.filter(
        and_(
            Product.clothing_type.in_(related_types),
            Product.is_active == True,
            Product.id != product_id
        )
    ).limit(10).all()
    
    created_count = 0
    for related_product in related_products:
        # Skip if relation already exists
        if related_product.id in existing_related_ids:
            continue
        
        # Skip if reverse relation exists (avoid duplicates)
        reverse_exists = ProductRelation.query.filter_by(
            product_id=related_product.id,
            related_product_id=product_id
        ).first()
        if reverse_exists:
            continue
        
        # Create relation
        try:
            relation = ProductRelation(
                product_id=product_id,
                related_product_id=related_product.id,
                is_fashion_match=True,
                match_score=1.0
            )
            db.session.add(relation)
            created_count += 1
        except Exception as e:
            # Relation might already exist (unique constraint)
            db.session.rollback()
            continue
    
    if created_count > 0:
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
    
    return related_products

def get_related_products_for_cart(cart_product_ids):
    """
    Get related products for items in cart.
    Returns a list of related products, prioritizing those with existing relations.
    """
    if not cart_product_ids or not ProductRelation:
        return []
    
    # Get all related product IDs from relations
    related_ids_query = db.session.query(ProductRelation.related_product_id).filter(
        and_(
            ProductRelation.product_id.in_(cart_product_ids),
            ProductRelation.is_fashion_match == True
        )
    ).distinct()
    
    related_ids = [row[0] for row in related_ids_query.all()]
    
    # If no relations exist, try to create them
    if not related_ids:
        for product_id in cart_product_ids:
            product = Product.query.get(product_id)
            if product:
                ensure_product_relations(product_id, product.clothing_type)
        
        # Query again after creating relations
        related_ids_query = db.session.query(ProductRelation.related_product_id).filter(
            and_(
                ProductRelation.product_id.in_(cart_product_ids),
                ProductRelation.is_fashion_match == True
            )
        ).distinct()
        related_ids = [row[0] for row in related_ids_query.all()]
    
    # Exclude products already in cart
    related_ids = [rid for rid in related_ids if rid not in cart_product_ids]
    
    if not related_ids:
        return []
    
    # Get the actual products
    related_products = Product.query.filter(
        and_(
            Product.id.in_(related_ids),
            Product.is_active == True
        )
    ).limit(12).all()
    
    return related_products

