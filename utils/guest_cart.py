"""Guest cart management using session."""
from flask import session
import json

GUEST_CART_SESSION_KEY = 'guest_cart'

def get_guest_cart():
    """Get guest cart from session."""
    cart = session.get(GUEST_CART_SESSION_KEY, [])
    # Ensure backward compatibility
    for item in cart:
        if 'selected_color' not in item:
            item['selected_color'] = None
        if 'selected_size' not in item:
            item['selected_size'] = None
    return cart

def add_to_guest_cart(product_id, quantity, selected_color=None, selected_size=None):
    """Add item to guest cart."""
    cart = get_guest_cart()
    
    # Check if same product with same color/size already exists
    for item in cart:
        if (item['product_id'] == product_id and 
            item.get('selected_color') == selected_color and 
            item.get('selected_size') == selected_size):
            item['quantity'] += quantity
            session[GUEST_CART_SESSION_KEY] = cart
            session.modified = True  # Force Flask to save the session
            return True
    
    # Add new item
    cart.append({
        'product_id': product_id,
        'quantity': quantity,
        'selected_color': selected_color,
        'selected_size': selected_size
    })
    session[GUEST_CART_SESSION_KEY] = cart
    session.modified = True  # Force Flask to save the session
    return True

def update_guest_cart_item(product_id, quantity, selected_color=None, selected_size=None, old_color=None, old_size=None):
    """Update guest cart item. Finds item by product_id and old color/size, then updates to new color/size."""
    cart = get_guest_cart()
    
    # Normalize None values for comparison
    def normalize_value(val):
        if val is None or val == '':
            return None
        return val
    
    # Use old_color/old_size to find the item, or use selected_color/selected_size if old not provided
    search_color = normalize_value(old_color) if old_color is not None else normalize_value(selected_color)
    search_size = normalize_value(old_size) if old_size is not None else normalize_value(selected_size)
    
    new_color = normalize_value(selected_color)
    new_size = normalize_value(selected_size)
    
    # First, check if an item with the NEW color/size already exists
    existing_item = None
    for item in cart:
        item_product_id = item.get('product_id')
        item_color = normalize_value(item.get('selected_color'))
        item_size = normalize_value(item.get('selected_size'))
        
        if (item_product_id == product_id and 
            item_color == new_color and 
            item_size == new_size):
            existing_item = item
            break
    
    # Find the item to update (by old color/size or current color/size)
    item_to_update = None
    for item in cart:
        item_product_id = item.get('product_id')
        item_color = normalize_value(item.get('selected_color'))
        item_size = normalize_value(item.get('selected_size'))
        
        # Check if product_id matches
        if item_product_id == product_id:
            # Match by old color/size if provided, otherwise by current color/size
            color_match = (search_color is None) or (item_color == search_color)
            size_match = (search_size is None) or (item_size == search_size)
            
            if color_match and size_match:
                item_to_update = item
                break
    
    if item_to_update:
        # If we're changing to a variant that already exists, merge quantities
        if existing_item and existing_item != item_to_update:
            # Merge: add quantity to existing item, remove old item
            existing_item['quantity'] = existing_item.get('quantity', 0) + quantity
            cart.remove(item_to_update)
        else:
            # Update the item
            if quantity <= 0:
                cart.remove(item_to_update)
            else:
                item_to_update['quantity'] = quantity
                # Update color/size if provided and different
                if selected_color is not None:
                    item_to_update['selected_color'] = selected_color
                if selected_size is not None:
                    item_to_update['selected_size'] = selected_size
        
        session[GUEST_CART_SESSION_KEY] = cart
        session.modified = True  # Force Flask to save the session
        return True
    
    return False

def remove_from_guest_cart(product_id, selected_color=None, selected_size=None):
    """Remove ONE item from guest cart that matches the criteria."""
    cart = get_guest_cart()
    original_count = len(cart)
    
    # Normalize None values for comparison (handle both None and empty string)
    def normalize_value(val):
        if val is None or val == '':
            return None
        return val
    
    normalized_selected_color = normalize_value(selected_color)
    normalized_selected_size = normalize_value(selected_size)
    
    # Find and remove the FIRST matching item (remove only one, not all)
    removed = False
    for i, item in enumerate(cart):
        item_product_id = item.get('product_id')
        item_color = normalize_value(item.get('selected_color'))
        item_size = normalize_value(item.get('selected_size'))
        
        # Check if this item matches
        product_match = item_product_id == product_id
        
        if product_match:
            # If color/size are specified, they must match
            # If not specified, match any item with this product_id
            color_match = (normalized_selected_color is None) or (item_color == normalized_selected_color)
            size_match = (normalized_selected_size is None) or (item_size == normalized_selected_size)
            
            if color_match and size_match:
                # Remove this item (only the first match)
                cart.pop(i)
                removed = True
                break
    
    # Update session and mark as modified to ensure Flask saves it
    if removed:
        session[GUEST_CART_SESSION_KEY] = cart
        session.modified = True  # Force Flask to save the session
    
    return removed

def clear_guest_cart():
    """Clear guest cart."""
    if GUEST_CART_SESSION_KEY in session:
        del session[GUEST_CART_SESSION_KEY]
        session.modified = True  # Force Flask to save the session
    return True

