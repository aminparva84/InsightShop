from flask import Blueprint, request, jsonify, session
from models.database import db
from models.cart import CartItem
from models.product import Product
from models.product_variation import ProductVariation
from routes.auth import require_auth
from sqlalchemy.orm import joinedload
from config import Config
from utils.guest_cart import (
    get_guest_cart, add_to_guest_cart, update_guest_cart_item,
    remove_from_guest_cart, clear_guest_cart
)
from utils.product_relations import get_related_products_for_cart
from utils.cart_matching_pairs import get_matching_pairs_for_cart

cart_bp = Blueprint('cart', __name__)

@cart_bp.route('', methods=['GET'])
def get_cart():
    """Get cart items (authenticated or guest)."""
    try:
        # Check database connection
        if not db.session:
            return jsonify({'error': 'Database connection not available'}), 500
        # Check if user is authenticated
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            try:
                from routes.auth import verify_jwt_token
                token = auth_header[7:]
                payload = verify_jwt_token(token)
                if payload:
                    from models.user import User
                    user = User.query.get(payload.get('sub') or payload.get('user_id'))
                    if user:
                        # Merge guest cart into user cart if session has guest items (e.g. after login)
                        guest_cart = get_guest_cart()
                        if guest_cart:
                            for g in guest_cart:
                                product_id = g.get('product_id')
                                quantity = int(g.get('quantity', 1))
                                selected_color = g.get('selected_color')
                                selected_size = g.get('selected_size')
                                variation_id = g.get('variation_id')
                                product = Product.query.get(product_id) if product_id else None
                                if not product or not product.is_active or quantity < 1:
                                    continue
                                variation = None
                                if variation_id:
                                    variation = ProductVariation.query.get(variation_id)
                                if not variation and (selected_size or selected_color):
                                    variation = ProductVariation.query.filter_by(
                                        product_id=product_id,
                                        size=selected_size or '',
                                        color=selected_color or ''
                                    ).first()
                                if variation:
                                    existing = CartItem.query.filter_by(
                                        user_id=user.id,
                                        product_id=product_id,
                                        variation_id=variation.id
                                    ).first()
                                    if existing:
                                        old_qty = existing.quantity
                                        new_qty = min(old_qty + quantity, variation.stock_quantity)
                                        variation.stock_quantity -= (new_qty - old_qty)
                                        existing.quantity = new_qty
                                    else:
                                        qty = min(quantity, variation.stock_quantity)
                                        if qty > 0:
                                            variation.stock_quantity -= qty
                                            db.session.add(CartItem(
                                                user_id=user.id,
                                                product_id=product_id,
                                                variation_id=variation.id,
                                                quantity=qty,
                                                selected_color=variation.color,
                                                selected_size=variation.size
                                            ))
                                else:
                                    existing = CartItem.query.filter_by(
                                        user_id=user.id,
                                        product_id=product_id,
                                        selected_color=selected_color,
                                        selected_size=selected_size
                                    ).first()
                                    if existing:
                                        new_qty = min(existing.quantity + quantity, product.stock_quantity)
                                        existing.quantity = new_qty
                                    else:
                                        qty = min(quantity, product.stock_quantity)
                                        if qty > 0:
                                            db.session.add(CartItem(
                                                user_id=user.id,
                                                product_id=product_id,
                                                quantity=qty,
                                                selected_color=selected_color,
                                                selected_size=selected_size
                                            ))
                            try:
                                db.session.commit()
                            except Exception:
                                db.session.rollback()
                            clear_guest_cart()

                        cart_items = CartItem.query.filter_by(user_id=user.id).all()
                        # Calculate total using sale prices if available
                        total = 0.0
                        for item in cart_items:
                            if item.product:
                                try:
                                    product_dict = item.product.to_dict()
                                    current_price = product_dict.get('price', float(item.product.price) if item.product.price else 0.0)
                                except Exception:
                                    current_price = float(item.product.price) if item.product.price else 0.0
                                total += current_price * item.quantity
                        return jsonify({
                            'items': [item.to_dict() for item in cart_items],
                            'total': float(total),
                            'is_guest': False
                        }), 200
            except:
                pass
        
        # Guest cart
        guest_cart = get_guest_cart()
        items = []
        total = 0.0
        
        for index, cart_item in enumerate(guest_cart):
            product = Product.query.get(cart_item['product_id'])
            if product and product.is_active:
                try:
                    product_dict = product.to_dict()
                    current_price = product_dict.get('price', float(product.price) if product.price else 0.0)
                except Exception:
                    # If to_dict fails, use basic product info
                    product_dict = {
                        'id': product.id,
                        'name': product.name,
                        'price': float(product.price) if product.price else 0.0,
                        'original_price': float(product.price) if product.price else 0.0,
                        'on_sale': False,
                        'image_url': product.image_url,
                        'stock_quantity': getattr(product, 'stock_quantity', 0)
                    }
                    current_price = float(product.price) if product.price else 0.0
                
                item_total = current_price * cart_item['quantity']
                total += item_total
                
                # Create unique ID that includes product_id, color, size, and index
                # This ensures each cart item has a unique identifier
                color_part = cart_item.get('selected_color') or 'none'
                size_part = cart_item.get('selected_size') or 'none'
                unique_id = f"guest_{cart_item['product_id']}_{color_part}_{size_part}_{index}"
                
                items.append({
                    'id': unique_id,
                    'product_id': cart_item['product_id'],
                    'variation_id': cart_item.get('variation_id'),
                    'product': product_dict,
                    'quantity': cart_item['quantity'],
                    'selected_color': cart_item.get('selected_color'),
                    'selected_size': cart_item.get('selected_size'),
                    'subtotal': item_total
                })
        
        return jsonify({
            'items': items,
            'total': total,
            'is_guest': True
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cart_bp.route('', methods=['POST'])
def add_to_cart():
    """Add item to cart (authenticated or guest). Stock is per variation (product_id + size + color)."""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        selected_color = data.get('selected_color')
        selected_size = data.get('selected_size')
        variation_id = data.get('variation_id')  # Optional: if provided, use it; else resolve from size+color

        if not product_id:
            return jsonify({'error': 'Product ID is required'}), 400

        product = Product.query.get(product_id)
        if not product or not product.is_active:
            return jsonify({'error': 'Product not found'}), 404

        # Resolve variation: by variation_id or by (product_id, size, color)
        variation = None
        if variation_id:
            variation = ProductVariation.query.filter_by(id=variation_id, product_id=product_id).first()
        if not variation and (selected_size is not None and selected_color is not None):
            variation = ProductVariation.query.filter_by(
                product_id=product_id,
                size=(selected_size or '').strip(),
                color=(selected_color or '').strip()
            ).first()

        # If product has any variations, we require a valid variation
        has_variations = ProductVariation.query.filter_by(product_id=product_id).count() > 0
        if has_variations:
            if not variation:
                return jsonify({'error': 'Please select a valid size and color'}), 400
            if variation.stock_quantity <= 0:
                return jsonify({'error': 'This variation is out of stock'}), 400
            if variation.stock_quantity < quantity:
                return jsonify({'error': 'Insufficient stock for this variation'}), 400
            selected_size = variation.size
            selected_color = variation.color
        else:
            # Legacy: no variations table rows - use product-level stock (e.g. old data)
            if getattr(product, 'stock_quantity', 0) < quantity:
                return jsonify({'error': 'Insufficient stock'}), 400

        # Check if user is authenticated
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            try:
                from routes.auth import verify_jwt_token
                token = auth_header[7:]
                payload = verify_jwt_token(token)
                if payload:
                    from models.user import User
                    user = User.query.get(payload.get('sub') or payload.get('user_id'))
                    if user:
                        if has_variations:
                            existing_item = CartItem.query.filter_by(
                                user_id=user.id,
                                product_id=product_id,
                                variation_id=variation.id
                            ).first()
                            if existing_item:
                                new_total = existing_item.quantity + quantity
                                if new_total > variation.stock_quantity:
                                    return jsonify({'error': 'Insufficient stock for this variation'}), 400
                                existing_item.quantity = new_total
                                variation.stock_quantity -= quantity
                                remaining_stock = variation.stock_quantity
                            else:
                                variation.stock_quantity -= quantity
                                remaining_stock = variation.stock_quantity
                                db.session.add(CartItem(
                                    user_id=user.id,
                                    product_id=product_id,
                                    variation_id=variation.id,
                                    quantity=quantity,
                                    selected_color=selected_color,
                                    selected_size=selected_size
                                ))
                        else:
                            existing_item = CartItem.query.filter_by(
                                user_id=user.id,
                                product_id=product_id,
                                selected_color=selected_color,
                                selected_size=selected_size
                            ).first()
                            if existing_item:
                                new_total = existing_item.quantity + quantity
                                if new_total > product.stock_quantity:
                                    return jsonify({'error': 'Insufficient stock'}), 400
                                existing_item.quantity = new_total
                                remaining_stock = product.stock_quantity - new_total
                            else:
                                cart_item = CartItem(
                                    user_id=user.id,
                                    product_id=product_id,
                                    quantity=quantity,
                                    selected_color=selected_color,
                                    selected_size=selected_size
                                )
                                db.session.add(cart_item)
                                remaining_stock = product.stock_quantity - quantity

                        db.session.commit()
                        return jsonify({'message': 'Item added to cart', 'remaining_stock': remaining_stock if has_variations else remaining_stock}), 200
            except Exception:
                pass

        # Guest cart
        if has_variations:
            guest_cart = get_guest_cart()
            current_in_cart = sum(
                item.get('quantity', 0)
                for item in guest_cart
                if (item.get('product_id') == product_id and item.get('variation_id') == variation.id)
            )
            if not current_in_cart:
                current_in_cart = sum(
                    item.get('quantity', 0)
                    for item in guest_cart
                    if (item.get('product_id') == product_id
                        and item.get('selected_color') == selected_color
                        and item.get('selected_size') == selected_size)
                )
            if current_in_cart + quantity > variation.stock_quantity:
                return jsonify({'error': 'Insufficient stock for this variation'}), 400
            quantity_to_add = min(quantity, variation.stock_quantity - current_in_cart)
            variation.stock_quantity -= quantity_to_add
            db.session.commit()
            add_to_guest_cart(product_id, quantity_to_add, selected_color, selected_size, variation_id=variation.id)
            remaining_stock = variation.stock_quantity
        else:
            guest_cart = get_guest_cart()
            current_in_cart = sum(
                item.get('quantity', 0)
                for item in guest_cart
                if (item.get('product_id') == product_id
                    and item.get('selected_color') == selected_color
                    and item.get('selected_size') == selected_size)
            )
            if current_in_cart + quantity > product.stock_quantity:
                return jsonify({'error': 'Insufficient stock'}), 400
            quantity_to_add = min(quantity, product.stock_quantity - current_in_cart)
            add_to_guest_cart(product_id, quantity_to_add, selected_color, selected_size)
            remaining_stock = product.stock_quantity - (current_in_cart + quantity_to_add)
        return jsonify({'message': 'Item added to cart', 'remaining_stock': remaining_stock}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@cart_bp.route('/<item_id>', methods=['PUT'])
def update_cart_item(item_id):
    """Update cart item quantity, color, or size (authenticated or guest)."""
    try:
        print(f"PUT /api/cart/{item_id} called")
        
        # Check database connection
        if not db.session:
            return jsonify({'error': 'Database connection not available'}), 500
        
        data = request.get_json()
        if not data:
            print("No JSON data in request")
            return jsonify({'error': 'Request body is required'}), 400
        
        quantity = int(data.get('quantity', 1))
        selected_color = data.get('selected_color')
        selected_size = data.get('selected_size')
        old_color = data.get('old_color')  # For finding the item to update
        old_size = data.get('old_size')    # For finding the item to update
        
        print(f"Update request - quantity: {quantity}, color: {selected_color}, size: {selected_size}, old_color: {old_color}, old_size: {old_size}")
        
        if quantity < 1:
            return jsonify({'error': 'Quantity must be at least 1'}), 400
        
        # Check if guest cart item
        if item_id.startswith('guest_'):
            # Parse the unique ID format: guest_{product_id}_{color}_{size}_{index}
            # Or fallback to old format: guest_{product_id}
            parts = item_id.replace('guest_', '').split('_')
            
            try:
                # Extract product_id (first part)
                if len(parts) >= 1:
                    product_id = int(parts[0])
                else:
                    # Fallback: try to parse as single number
                    product_id = int(item_id.replace('guest_', ''))
                print(f"Parsed product_id: {product_id} from item_id: {item_id}")
            except (ValueError, IndexError) as e:
                print(f"Invalid item ID format: {item_id}, error: {e}")
                return jsonify({'error': 'Invalid item ID format'}), 400
            
            # Use selected_color and selected_size from request body if provided
            # Otherwise, try to extract from item_id or use None
            if selected_color is None and len(parts) >= 2:
                # Try to extract from item_id (parts[1] might be color)
                # But it's better to rely on request body
                pass
            
            product = Product.query.get(product_id)
            if not product:
                print(f"Product {product_id} not found")
                return jsonify({'error': 'Product not found'}), 404
            if product.stock_quantity < quantity:
                print(f"Insufficient stock: requested {quantity}, available {product.stock_quantity}")
                return jsonify({'error': 'Insufficient stock'}), 400
            
            # For guest cart, we need to find the item by product_id, color, and size
            # The update function will handle finding and updating the correct item
            print(f"Calling update_guest_cart_item with product_id={product_id}, quantity={quantity}, color={selected_color}, size={selected_size}, old_color={old_color}, old_size={old_size}")
            success = update_guest_cart_item(product_id, quantity, selected_color, selected_size, old_color, old_size)
            if success:
                print("Guest cart item updated successfully")
                return jsonify({'message': 'Cart item updated'}), 200
            else:
                print("Guest cart item not found")
                # Debug: show current cart contents
                from utils.guest_cart import get_guest_cart
                current_cart = get_guest_cart()
                print(f"Current cart has {len(current_cart)} items:")
                for idx, item in enumerate(current_cart):
                    print(f"  [{idx}] product_id={item.get('product_id')}, color={item.get('selected_color')}, size={item.get('selected_size')}, qty={item.get('quantity')}")
                return jsonify({'error': 'Cart item not found'}), 404
        
        # Authenticated user
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authentication required'}), 401
        
        from routes.auth import verify_jwt_token
        token = auth_header[7:]
        payload = verify_jwt_token(token)
        if not payload:
            return jsonify({'error': 'Invalid token'}), 401
        
        from models.user import User
        user = User.query.get(payload.get('sub') or payload.get('user_id'))
        if not user:
            return jsonify({'error': 'User not found'}), 401
        
        cart_item = CartItem.query.filter_by(id=int(item_id), user_id=user.id).first_or_404()
        product = Product.query.get(cart_item.product_id)
        if cart_item.variation_id:
            variation = ProductVariation.query.get(cart_item.variation_id)
            if variation:
                old_qty = cart_item.quantity
                variation.stock_quantity += old_qty
                if quantity > variation.stock_quantity:
                    variation.stock_quantity -= old_qty
                    db.session.rollback()
                    return jsonify({'error': 'Insufficient stock for this variation'}), 400
                variation.stock_quantity -= quantity
        else:
            if product and product.stock_quantity < quantity:
                return jsonify({'error': 'Insufficient stock'}), 400
        cart_item.quantity = quantity
        if selected_color is not None:
            cart_item.selected_color = selected_color
        if selected_size is not None:
            cart_item.selected_size = selected_size
        db.session.commit()
        
        return jsonify({'message': 'Cart item updated', 'item': cart_item.to_dict()}), 200
        
    except Exception as e:
        db.session.rollback()
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in update_cart_item for item_id={item_id}: {e}")
        print(f"Traceback: {error_trace}")
        return jsonify({'error': str(e), 'traceback': error_trace if Config.DEBUG else None}), 500

@cart_bp.route('/<item_id>', methods=['DELETE'])
def remove_from_cart(item_id):
    """Remove item from cart (authenticated or guest)."""
    try:
        print(f"DELETE /api/cart/{item_id} called")
        
        # Check if guest cart item
        if item_id.startswith('guest_'):
            # Parse the unique ID format: guest_{product_id}_{color}_{size}_{index}
            # Or fallback to old format: guest_{product_id}
            parts = item_id.replace('guest_', '').split('_')
            
            try:
                # Try to parse new format with color/size/index
                if len(parts) >= 1:
                    # Extract product_id (first part)
                    product_id = int(parts[0])
                else:
                    # Fallback: try to parse as single number
                    product_id = int(item_id.replace('guest_', ''))
            except (ValueError, IndexError):
                print(f"Invalid item ID format: {item_id}")
                return jsonify({'error': 'Invalid item ID format'}), 400
            
            # Get selected_color and selected_size from request body (more reliable)
            # Flask needs request.get_json(force=True) for DELETE requests sometimes
            try:
                # Try multiple methods to get JSON data from DELETE request
                if request.is_json:
                    data = request.get_json() or {}
                else:
                    data = request.get_json(force=True, silent=True) or {}
            except Exception as e:
                print(f"Error parsing JSON from DELETE request: {e}")
                data = {}
            
            selected_color = data.get('selected_color')
            selected_size = data.get('selected_size')
            
            # Find the guest cart item to get variation_id and quantity (to restore stock)
            current_cart = get_guest_cart()
            removed_qty = 0
            variation_id_to_restore = None
            for item in current_cart:
                if (item.get('product_id') == product_id and
                    item.get('selected_color') == selected_color and
                    item.get('selected_size') == selected_size):
                    removed_qty = item.get('quantity', 0)
                    variation_id_to_restore = item.get('variation_id')
                    break
            
            result = remove_from_guest_cart(product_id, selected_color, selected_size)
            if variation_id_to_restore and removed_qty > 0:
                variation = ProductVariation.query.get(variation_id_to_restore)
                if variation:
                    variation.stock_quantity += removed_qty
                    try:
                        db.session.commit()
                    except Exception:
                        db.session.rollback()
            
            return jsonify({'message': 'Item removed from cart', 'removed': result}), 200
        
        # Authenticated user
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            # For guest users, try to remove from guest cart if item_id is numeric
            try:
                product_id = int(item_id)
                try:
                    data = request.get_json(force=True, silent=True) or {}
                except:
                    data = {}
                selected_color = data.get('selected_color')
                selected_size = data.get('selected_size')
                remove_from_guest_cart(product_id, selected_color, selected_size)
                return jsonify({'message': 'Item removed from cart'}), 200
            except (ValueError, TypeError):
                return jsonify({'error': 'Authentication required'}), 401
        
        from routes.auth import verify_jwt_token
        token = auth_header[7:]
        payload = verify_jwt_token(token)
        if not payload:
            return jsonify({'error': 'Invalid token'}), 401
        
        from models.user import User
        user = User.query.get(payload.get('sub') or payload.get('user_id'))
        if not user:
            return jsonify({'error': 'User not found'}), 401
        
        cart_item = CartItem.query.filter_by(id=int(item_id), user_id=user.id).first_or_404()
        if cart_item.variation_id:
            variation = ProductVariation.query.get(cart_item.variation_id)
            if variation:
                variation.stock_quantity += cart_item.quantity
        db.session.delete(cart_item)
        db.session.commit()
        
        return jsonify({'message': 'Item removed from cart'}), 200
        
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"Error in remove_from_cart: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@cart_bp.route('/clear', methods=['DELETE'])
def clear_cart():
    """Clear all items from cart (authenticated or guest)."""
    try:
        # Check if authenticated
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            try:
                from routes.auth import verify_jwt_token
                token = auth_header[7:]
                payload = verify_jwt_token(token)
                if payload:
                    from models.user import User
                    user = User.query.get(payload.get('sub') or payload.get('user_id'))
                    if user:
                        for item in CartItem.query.filter_by(user_id=user.id).all():
                            if item.variation_id:
                                v = ProductVariation.query.get(item.variation_id)
                                if v:
                                    v.stock_quantity += item.quantity
                        CartItem.query.filter_by(user_id=user.id).delete()
                        db.session.commit()
                        return jsonify({'message': 'Cart cleared'}), 200
            except:
                pass
        
        # Guest cart: restore variation stock for each item then clear
        guest_cart = get_guest_cart()
        for item in guest_cart:
            vid = item.get('variation_id')
            qty = int(item.get('quantity', 0))
            if vid and qty > 0:
                v = ProductVariation.query.get(vid)
                if v:
                    v.stock_quantity += qty
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
        clear_guest_cart()
        return jsonify({'message': 'Cart cleared'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@cart_bp.route('/suggestions', methods=['GET'])
def get_cart_suggestions():
    """Get related product suggestions based on items in cart."""
    try:
        # Get cart items (authenticated or guest)
        auth_header = request.headers.get('Authorization')
        cart_product_ids = []
        
        if auth_header and auth_header.startswith('Bearer '):
            try:
                from routes.auth import verify_jwt_token
                token = auth_header[7:]
                payload = verify_jwt_token(token)
                if payload:
                    from models.user import User
                    user = User.query.get(payload.get('sub') or payload.get('user_id'))
                    if user:
                        cart_items = CartItem.query.filter_by(user_id=user.id).all()
                        cart_product_ids = [item.product_id for item in cart_items if item.product_id]
            except:
                pass
        
        # If no authenticated cart, check guest cart
        if not cart_product_ids:
            guest_cart = get_guest_cart()
            cart_product_ids = [item['product_id'] for item in guest_cart if item.get('product_id')]
        
        if not cart_product_ids:
            return jsonify({'products': []}), 200
        
        # Get related products
        related_products = get_related_products_for_cart(cart_product_ids)
        
        # Convert to dict format
        products_data = [p.to_dict() for p in related_products]
        
        return jsonify({
            'products': products_data,
            'count': len(products_data)
        }), 200
        
    except Exception as e:
        import traceback
        print(f"Error in get_cart_suggestions: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e), 'products': []}), 500


@cart_bp.route('/matching-pairs', methods=['GET'])
def get_cart_matching_pairs():
    """
    Get AI-powered matching pair recommendations for items in the cart.
    Uses fashion knowledge base and product relations to suggest items that
    go well with what the user has (e.g. white shirt -> brown pants).
    """
    try:
        auth_header = request.headers.get('Authorization')
        cart_product_ids = []

        if auth_header and auth_header.startswith('Bearer '):
            try:
                from routes.auth import verify_jwt_token
                token = auth_header[7:]
                payload = verify_jwt_token(token)
                if payload:
                    from models.user import User
                    user = User.query.get(payload.get('sub') or payload.get('user_id'))
                    if user:
                        cart_items = CartItem.query.filter_by(user_id=user.id).all()
                        cart_product_ids = [item.product_id for item in cart_items if item.product_id]
            except Exception:
                pass

        if not cart_product_ids:
            guest_cart = get_guest_cart()
            cart_product_ids = [item['product_id'] for item in guest_cart if item.get('product_id')]

        if not cart_product_ids:
            return jsonify({'matches': [], 'count': 0}), 200

        pairs = get_matching_pairs_for_cart(cart_product_ids, max_results=8)
        matches = [
            {'product': p['product'].to_dict(), 'reason': p['reason']}
            for p in pairs
        ]
        return jsonify({'matches': matches, 'count': len(matches)}), 200

    except Exception as e:
        import traceback
        print(f"Error in get_cart_matching_pairs: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e), 'matches': []}), 500

