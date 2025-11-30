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
            return True
    
    # Add new item
    cart.append({
        'product_id': product_id,
        'quantity': quantity,
        'selected_color': selected_color,
        'selected_size': selected_size
    })
    session[GUEST_CART_SESSION_KEY] = cart
    return True

def update_guest_cart_item(product_id, quantity, selected_color=None, selected_size=None):
    """Update guest cart item. Finds item by product_id and updates all fields."""
    cart = get_guest_cart()
    
    # Find item by product_id (first match)
    for item in cart:
        if item['product_id'] == product_id:
            if quantity <= 0:
                cart.remove(item)
            else:
                item['quantity'] = quantity
                if selected_color is not None:
                    item['selected_color'] = selected_color
                if selected_size is not None:
                    item['selected_size'] = selected_size
            session[GUEST_CART_SESSION_KEY] = cart
            return True
    
    return False

def remove_from_guest_cart(product_id, selected_color=None, selected_size=None):
    """Remove item from guest cart."""
    cart = get_guest_cart()
    cart = [item for item in cart if not (
        item['product_id'] == product_id and 
        item.get('selected_color') == selected_color and 
        item.get('selected_size') == selected_size
    )]
    session[GUEST_CART_SESSION_KEY] = cart
    return True

def clear_guest_cart():
    """Clear guest cart."""
    if GUEST_CART_SESSION_KEY in session:
        del session[GUEST_CART_SESSION_KEY]
    return True

