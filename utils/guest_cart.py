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

def update_guest_cart_item(product_id, quantity, selected_color=None, selected_size=None):
    """Update guest cart item. Finds item by product_id, color, and size, then updates quantity."""
    cart = get_guest_cart()
    
    # Normalize None values for comparison
    def normalize_value(val):
        if val is None or val == '':
            return None
        return val
    
    normalized_selected_color = normalize_value(selected_color)
    normalized_selected_size = normalize_value(selected_size)
    
    # Find item by product_id AND color/size if provided
    for item in cart:
        item_product_id = item.get('product_id')
        item_color = normalize_value(item.get('selected_color'))
        item_size = normalize_value(item.get('selected_size'))
        
        # Check if product_id matches
        if item_product_id == product_id:
            # If color/size are specified, they must match
            # If not specified, match any item with this product_id
            color_match = (normalized_selected_color is None) or (item_color == normalized_selected_color)
            size_match = (normalized_selected_size is None) or (item_size == normalized_selected_size)
            
            if color_match and size_match:
                # Found the matching item
                if quantity <= 0:
                    cart.remove(item)
                else:
                    item['quantity'] = quantity
                    # Update color/size if provided
                    if selected_color is not None:
                        item['selected_color'] = selected_color
                    if selected_size is not None:
                        item['selected_size'] = selected_size
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

