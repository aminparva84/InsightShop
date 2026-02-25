"""
AI Action Executor: runs backend actions from structured JSON (action + parameters).
Used by the AI decision engine; never returns free text—only structured results.
"""
from __future__ import annotations

import re
import json
from typing import Any, Optional

# Lazy imports to avoid circular deps and to use app context
def _db():
    from models.database import db
    return db

def _Product():
    from models.product import Product
    return Product

def _CartItem():
    from models.cart import CartItem
    return CartItem

def _WishlistItem():
    from models.wishlist import WishlistItem
    return WishlistItem

def _search_products_by_criteria(criteria):
    """Search products by criteria (in-executor to avoid circular import). Case-insensitive for category and color."""
    from sqlalchemy import or_, and_
    from datetime import date
    Product = _Product()
    query = Product.query.filter_by(is_active=True)
    if criteria.get('category'):
        query = query.filter(Product.category.ilike(criteria['category']))
    if criteria.get('color'):
        query = query.filter(Product.color.ilike(criteria['color']))
    if criteria.get('size'):
        query = query.filter_by(size=criteria['size'])
    if criteria.get('fabric'):
        query = query.filter_by(fabric=criteria['fabric'])
    if criteria.get('clothing_type'):
        query = query.filter(Product.clothing_type.ilike(f'%{criteria["clothing_type"]}%'))
    if criteria.get('occasion'):
        query = query.filter_by(occasion=criteria['occasion'])
    if criteria.get('age_group'):
        query = query.filter_by(age_group=criteria['age_group'])
    if criteria.get('min_price') is not None:
        query = query.filter(Product.price >= float(criteria['min_price']))
    if criteria.get('max_price') is not None:
        query = query.filter(Product.price <= float(criteria['max_price']))
    if criteria.get('search'):
        search_term = criteria['search']
        query = query.filter(
            or_(
                Product.name.ilike(f'%{search_term}%'),
                Product.description.ilike(f'%{search_term}%'),
                Product.clothing_type.ilike(f'%{search_term}%'),
            )
        )

    if criteria.get('on_sale'):
        today = date.today()
        # 1) Product-level sale
        query_sale = query.filter(
            and_(
                Product.sale_enabled == True,
                Product.sale_start.isnot(None),
                Product.sale_end.isnot(None),
                Product.sale_percentage.isnot(None),
                Product.sale_start <= today,
                Product.sale_end >= today,
            )
        )
        products_product_sale = query_sale.limit(50).all()
        ids_seen = {p.id for p in products_product_sale}
        # 2) Global Sale table: products matching criteria that are in an active Sale
        try:
            from models.sale import Sale
            active_sales = Sale.query.filter_by(is_active=True).all()
        except Exception:
            active_sales = []
        candidates = query.limit(100).all()
        extra = []
        for p in candidates:
            if p.id in ids_seen:
                continue
            if getattr(p, '_is_product_sale_active', None) and p._is_product_sale_active(today):
                extra.append(p)
                ids_seen.add(p.id)
                continue
            for s in active_sales:
                if s.is_currently_active(today) and s.matches_product(p):
                    extra.append(p)
                    ids_seen.add(p.id)
                    break
        combined = list(products_product_sale) + extra
        return [p.to_dict() for p in combined[:50]]
    return [p.to_dict() for p in query.limit(50).all()]

def _search_products_vector(query, n_results=20):
    from utils.vector_db import search_products_vector
    return search_products_vector(query, n_results=n_results)

def _normalize_category(val):
    try:
        from utils.spelling_tolerance import normalize_category
        return normalize_category(val) if val else None
    except Exception:
        return val if val else None

def _normalize_color(val):
    try:
        from utils.spelling_tolerance import normalize_color_spelling
        return normalize_color_spelling(val) if val else None
    except Exception:
        return val if val else None

def _normalize_clothing_type(val):
    try:
        from utils.spelling_tolerance import normalize_clothing_type
        return normalize_clothing_type(val) if val else None
    except Exception:
        return val if val else None


# Allowed actions (backend must implement each)
ACTIONS = frozenset({
    'SEARCH_PRODUCTS',
    'ADD_TO_CART', 'REMOVE_FROM_CART', 'UPDATE_CART_ITEM', 'CLEAR_CART',
    'ADD_TO_WISHLIST', 'REMOVE_FROM_WISHLIST', 'CLEAR_WISHLIST', 'ADD_WISHLIST_TO_CART',
    'VIEW_CART', 'VIEW_WISHLIST', 'VIEW_PRODUCTS', 'VIEW_HOME', 'VIEW_CHECKOUT',
    'Response', 'NONE',
})


def _normalize_action(action: str) -> str:
    """Normalize action string so common LLM variants/corruptions still map to a known action."""
    if not action or not isinstance(action, str):
        return (action or "").strip() or "NONE"
    a = action.strip()
    if not a:
        return "NONE"
    a_upper = a.upper()
    if a_upper in ACTIONS:
        return a_upper
    # Common search variants (including partial/corrupt output)
    if a_upper in ("SEARCH", "SEARCH_PRODUCT", "SEARCHPRODUCTS", "SEARCH PRODUCTS"):
        return "SEARCH_PRODUCTS"
    if "SEARCH" in a_upper and "PRODUCT" in a_upper:
        return "SEARCH_PRODUCTS"
    return a_upper


def execute_action(
    action: str,
    parameters: dict,
    *,
    current_user: Optional[Any] = None,
    flask_request: Optional[Any] = None,
) -> dict:
    """
    Execute one backend action. Returns a single dict:
    {
        "success": bool,
        "data": optional (products list, cart, redirect path, etc.),
        "error": optional str,
        "redirect_path": optional str (for VIEW_*),
        "message_override": optional str (to override AI message with backend result),
    }
    """
    if not action:
        return {"success": False, "error": "Missing action or parameters"}
    if parameters is None or not isinstance(parameters, dict):
        parameters = {}

    action_upper = _normalize_action(action)
    if action_upper in ("RESPONSE", "NONE", ""):
        return {"success": True, "data": None}

    if action_upper == "SEARCH_PRODUCTS":
        return _execute_search_products(parameters)

    if action_upper == "ADD_TO_CART":
        return _execute_add_to_cart(parameters, current_user=current_user, flask_request=flask_request)
    if action_upper == "REMOVE_FROM_CART":
        return _execute_remove_from_cart(parameters, current_user=current_user, flask_request=flask_request)
    if action_upper == "UPDATE_CART_ITEM":
        return _execute_update_cart_item(parameters, current_user=current_user, flask_request=flask_request)
    if action_upper == "CLEAR_CART":
        return _execute_clear_cart(current_user=current_user, flask_request=flask_request)

    if action_upper == "ADD_TO_WISHLIST":
        return _execute_add_to_wishlist(parameters, current_user=current_user)
    if action_upper == "REMOVE_FROM_WISHLIST":
        return _execute_remove_from_wishlist(parameters, current_user=current_user)
    if action_upper == "CLEAR_WISHLIST":
        return _execute_clear_wishlist(current_user=current_user)
    if action_upper == "ADD_WISHLIST_TO_CART":
        return _execute_add_wishlist_to_cart(current_user=current_user, flask_request=flask_request)

    if action_upper == "VIEW_CART":
        return {"success": True, "redirect_path": "/cart", "data": None}
    if action_upper == "VIEW_WISHLIST":
        return {"success": True, "redirect_path": "/wishlist", "data": None}
    if action_upper == "VIEW_PRODUCTS":
        return {"success": True, "redirect_path": "/products", "data": None}
    if action_upper == "VIEW_HOME":
        return {"success": True, "redirect_path": "/", "data": None}
    if action_upper == "VIEW_CHECKOUT":
        return {"success": True, "redirect_path": "/checkout", "data": None}

    return {"success": False, "error": f"Unknown action: {action}"}


def _build_criteria(parameters: dict) -> dict:
    """Build search criteria from parameters; normalize category/color/clothing_type."""
    criteria = {}
    if parameters.get("category"):
        criteria["category"] = _normalize_category(parameters["category"]) or parameters["category"]
    if parameters.get("color"):
        criteria["color"] = _normalize_color(parameters["color"]) or parameters["color"]
    if parameters.get("clothing_type"):
        criteria["clothing_type"] = _normalize_clothing_type(parameters["clothing_type"]) or parameters["clothing_type"]
    if parameters.get("min_price") is not None:
        try:
            criteria["min_price"] = float(parameters["min_price"])
        except (TypeError, ValueError):
            pass
    if parameters.get("max_price") is not None:
        try:
            criteria["max_price"] = float(parameters["max_price"])
        except (TypeError, ValueError):
            pass
    if parameters.get("search"):
        criteria["search"] = str(parameters["search"]).strip()
    if parameters.get("query"):
        criteria["search"] = str(parameters["query"]).strip()
    if parameters.get("size"):
        criteria["size"] = str(parameters["size"]).strip()
    if parameters.get("fabric"):
        criteria["fabric"] = str(parameters["fabric"]).strip()
    if parameters.get("occasion"):
        criteria["occasion"] = str(parameters["occasion"]).strip()
    if parameters.get("on_sale") is True or parameters.get("on_sale") == "true" or parameters.get("on_sale") == "1":
        criteria["on_sale"] = True
    return criteria


def _build_vector_query_from_criteria(criteria: dict) -> Optional[str]:
    """Build a natural-language query string from search criteria for vector search. Returns None if nothing to search."""
    parts = []
    if criteria.get("color"):
        parts.append(str(criteria["color"]).strip())
    if criteria.get("category"):
        parts.append(str(criteria["category"]).strip())
    if criteria.get("clothing_type"):
        parts.append(str(criteria["clothing_type"]).strip())
    if criteria.get("fabric"):
        parts.append(str(criteria["fabric"]).strip())
    if criteria.get("occasion"):
        parts.append(str(criteria["occasion"]).strip())
    if criteria.get("on_sale") is True or criteria.get("on_sale") == "true" or criteria.get("on_sale") == "1":
        parts.append("on sale")
    if criteria.get("max_price") is not None:
        try:
            parts.append(f"under {float(criteria['max_price'])}")
        except (TypeError, ValueError):
            pass
    if criteria.get("min_price") is not None:
        try:
            parts.append(f"over {float(criteria['min_price'])}")
        except (TypeError, ValueError):
            pass
    if not parts:
        return None
    return " ".join(parts)


def _filter_products_by_criteria(product_dicts: list, criteria: dict) -> list:
    """Filter a list of product dicts (from to_dict()) by the same criteria used in search. Case-insensitive for category/color."""
    if not criteria or not product_dicts:
        return product_dicts
    result = []
    for p in product_dicts:
        if criteria.get("category") and (p.get("category") or "").lower() != (criteria["category"] or "").lower():
            continue
        if criteria.get("color") and (p.get("color") or "").lower() != (criteria["color"] or "").lower():
            continue
        if criteria.get("size") and (p.get("size") or "").strip() != (criteria["size"] or "").strip():
            continue
        if criteria.get("fabric") and (p.get("fabric") or "").strip() != (criteria["fabric"] or "").strip():
            continue
        if criteria.get("clothing_type"):
            ct = (p.get("clothing_type") or "").strip().lower()
            want = (criteria["clothing_type"] or "").strip().lower()
            if ct != want and want not in ct:
                continue
        if criteria.get("occasion") and (p.get("occasion") or "").strip() != (criteria["occasion"] or "").strip():
            continue
        if criteria.get("min_price") is not None:
            try:
                price = float(p.get("price") or p.get("original_price") or 0)
                if price < float(criteria["min_price"]):
                    continue
            except (TypeError, ValueError):
                pass
        if criteria.get("max_price") is not None:
            try:
                price = float(p.get("price") or p.get("original_price") or 0)
                if price > float(criteria["max_price"]):
                    continue
            except (TypeError, ValueError):
                pass
        if criteria.get("on_sale") is True or criteria.get("on_sale") == "true" or criteria.get("on_sale") == "1":
            if not p.get("on_sale"):
                continue
        result.append(p)
    return result


def _execute_search_products(parameters: dict) -> dict:
    """Always returns { success: True, data: { products: list, count: int } }. Products is always a list (never None)."""
    try:
        criteria = _build_criteria(parameters)
        search_term = criteria.get("search")
        Product = _Product()

        # 1) Explicit search term: use vector search first, then apply criteria filter for precision
        if search_term:
            try:
                product_ids = _search_products_vector(search_term, n_results=30)
                if product_ids:
                    products = Product.query.filter(
                        Product.id.in_(product_ids),
                        Product.is_active == True
                    ).all()
                    by_id = {p.id: p for p in products}
                    ordered = [by_id[pid].to_dict() for pid in product_ids if pid in by_id]
                    # When we have other criteria (category, color, on_sale, etc.), filter so results match ALL criteria
                    if any(criteria.get(k) for k in ('category', 'color', 'clothing_type', 'on_sale', 'min_price', 'max_price', 'size', 'fabric', 'occasion')):
                        ordered = _filter_products_by_criteria(ordered, criteria)
                    if ordered:
                        return {"success": True, "data": {"products": ordered, "count": len(ordered)}}
            except Exception:
                pass
            # Vector failed or returned nothing (or filter matched nothing) — fall back to criteria
            products = _search_products_by_criteria(criteria)
            return {"success": True, "data": {"products": list(products) if products else [], "count": len(products) if products else 0}}

        # 2) No search term but we have filters: use vector search with a query built from criteria, then filter results
        vector_query = _build_vector_query_from_criteria(criteria)
        if vector_query:
            try:
                product_ids = _search_products_vector(vector_query, n_results=40)
                if product_ids:
                    products = Product.query.filter(
                        Product.id.in_(product_ids),
                        Product.is_active == True
                    ).all()
                    by_id = {p.id: p for p in products}
                    ordered_raw = [by_id[pid].to_dict() for pid in product_ids if pid in by_id]
                # Filter by criteria so we only return products that match (vector can return near-matches)
                filtered = _filter_products_by_criteria(ordered_raw, criteria)
                if filtered:
                    return {"success": True, "data": {"products": filtered, "count": len(filtered)}}
                # When filter removes all, return unfiltered vector results so user sees something (better than empty)
                if ordered_raw:
                    return {"success": True, "data": {"products": ordered_raw, "count": len(ordered_raw)}}
            except Exception:
                pass

        # 3) Fallback: criteria-only SQL search (no vector or vector returned nothing / filter matched nothing)
        products = _search_products_by_criteria(criteria)
        return {"success": True, "data": {"products": list(products) if products else [], "count": len(products) if products else 0}}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": True, "data": {"products": [], "count": 0}}


def _execute_add_to_cart(
    parameters: dict,
    *,
    current_user: Optional[Any] = None,
    flask_request: Optional[Any] = None,
) -> dict:
    product_id = parameters.get("product_id")
    if product_id is None:
        return {"success": False, "error": "product_id is required"}
    try:
        product_id = int(product_id)
    except (TypeError, ValueError):
        return {"success": False, "error": "product_id must be an integer"}
    quantity = parameters.get("quantity")
    if quantity is None:
        quantity = 1
    try:
        quantity = max(1, int(quantity))
    except (TypeError, ValueError):
        quantity = 1
    selected_color = parameters.get("selected_color") or parameters.get("color")
    selected_size = parameters.get("selected_size") or parameters.get("size")

    Product = _Product()
    product = Product.query.get(product_id)
    if not product or not product.is_active:
        return {"success": False, "error": "Product not found"}
    if (product.stock_quantity or 0) < quantity:
        return {"success": False, "error": "Insufficient stock"}

    if current_user:
        CartItem = _CartItem()
        db = _db()
        existing = CartItem.query.filter_by(
            user_id=current_user.id,
            product_id=product_id,
            selected_color=selected_color,
            selected_size=selected_size,
        ).first()
        if existing:
            new_qty = min(existing.quantity + quantity, product.stock_quantity)
            existing.quantity = new_qty
        else:
            db.session.add(CartItem(
                user_id=current_user.id,
                product_id=product_id,
                quantity=min(quantity, product.stock_quantity),
                selected_color=selected_color,
                selected_size=selected_size,
            ))
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
        return {"success": True, "message_override": f"I've added {quantity} item(s) to your cart."}

    if flask_request:
        from utils.guest_cart import add_to_guest_cart
        add_to_guest_cart(product_id, quantity, selected_color, selected_size)
        return {"success": True, "message_override": f"I've added {quantity} item(s) to your cart."}
    return {"success": False, "error": "Please sign in or use the site to add items to your cart."}


def _execute_remove_from_cart(
    parameters: dict,
    *,
    current_user: Optional[Any] = None,
    flask_request: Optional[Any] = None,
) -> dict:
    product_id = parameters.get("product_id")
    item_id = parameters.get("item_id")
    if product_id is None and item_id is None:
        return {"success": False, "error": "product_id or item_id is required"}
    if current_user and item_id and not str(item_id).startswith("guest_"):
        try:
            CartItem = _CartItem()
            db = _db()
            item = CartItem.query.filter_by(id=int(item_id), user_id=current_user.id).first()
            if item:
                db.session.delete(item)
                db.session.commit()
                return {"success": True, "message_override": "Item removed from your cart."}
        except Exception as e:
            _db().session.rollback()
            return {"success": False, "error": str(e)}
    product_id = product_id or (int(str(item_id).replace("guest_", "").split("_")[0]) if item_id and str(item_id).startswith("guest_") else None)
    if product_id is None:
        return {"success": False, "error": "product_id or item_id is required"}
    try:
        product_id = int(product_id)
    except (TypeError, ValueError):
        return {"success": False, "error": "Invalid product_id"}
    selected_color = parameters.get("selected_color") or parameters.get("color")
    selected_size = parameters.get("selected_size") or parameters.get("size")
    if current_user:
        CartItem = _CartItem()
        db = _db()
        q = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id)
        if selected_color is not None:
            q = q.filter_by(selected_color=selected_color)
        if selected_size is not None:
            q = q.filter_by(selected_size=selected_size)
        item = q.first()
        if item:
            db.session.delete(item)
            db.session.commit()
            return {"success": True, "message_override": "Item removed from your cart."}
        return {"success": False, "error": "Item not found in cart."}
    if flask_request:
        from utils.guest_cart import remove_from_guest_cart
        ok = remove_from_guest_cart(product_id, selected_color, selected_size)
        return {"success": True, "message_override": "Item removed from your cart."} if ok else {"success": False, "error": "Item not found in cart."}
    return {"success": False, "error": "Please sign in or use the site to update your cart."}


def _execute_update_cart_item(
    parameters: dict,
    *,
    current_user: Optional[Any] = None,
    flask_request: Optional[Any] = None,
) -> dict:
    item_id = parameters.get("item_id")
    product_id = parameters.get("product_id")
    quantity = parameters.get("quantity", 1)
    try:
        quantity = max(1, int(quantity))
    except (TypeError, ValueError):
        quantity = 1
    selected_color = parameters.get("selected_color") or parameters.get("color")
    selected_size = parameters.get("selected_size") or parameters.get("size")
    if current_user and item_id and not str(item_id).startswith("guest_"):
        try:
            CartItem = _CartItem()
            Product = _Product()
            db = _db()
            item = CartItem.query.filter_by(id=int(item_id), user_id=current_user.id).first()
            if not item:
                return {"success": False, "error": "Cart item not found."}
            product = Product.query.get(item.product_id)
            if product and product.stock_quantity < quantity:
                return {"success": False, "error": "Insufficient stock."}
            item.quantity = quantity
            if selected_color is not None:
                item.selected_color = selected_color
            if selected_size is not None:
                item.selected_size = selected_size
            db.session.commit()
            return {"success": True, "message_override": "Cart updated."}
        except Exception as e:
            _db().session.rollback()
            return {"success": False, "error": str(e)}
    if flask_request and (item_id or product_id):
        from utils.guest_cart import update_guest_cart_item
        pid = product_id
        if pid is None and item_id and str(item_id).startswith("guest_"):
            try:
                pid = int(str(item_id).replace("guest_", "").split("_")[0])
            except (ValueError, IndexError):
                pass
        if pid is not None:
            ok = update_guest_cart_item(
                int(pid), quantity,
                selected_color=selected_color, selected_size=selected_size,
                old_color=parameters.get("old_color"), old_size=parameters.get("old_size"),
            )
            return {"success": True, "message_override": "Cart updated."} if ok else {"success": False, "error": "Cart item not found."}
    return {"success": False, "error": "item_id or product_id required."}


def _execute_clear_cart(
    *,
    current_user: Optional[Any] = None,
    flask_request: Optional[Any] = None,
) -> dict:
    if current_user:
        CartItem = _CartItem()
        db = _db()
        CartItem.query.filter_by(user_id=current_user.id).delete()
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
        return {"success": True, "message_override": "Your cart is now empty."}
    if flask_request:
        from utils.guest_cart import clear_guest_cart
        clear_guest_cart()
        return {"success": True, "message_override": "Your cart is now empty."}
    return {"success": False, "error": "Please sign in or use the site to clear your cart."}


def _execute_add_to_wishlist(parameters: dict, *, current_user: Optional[Any] = None) -> dict:
    if not current_user:
        return {"success": False, "error": "Please sign in to add items to your wishlist."}
    product_id = parameters.get("product_id")
    if product_id is None:
        return {"success": False, "error": "product_id is required"}
    try:
        product_id = int(product_id)
    except (TypeError, ValueError):
        return {"success": False, "error": "product_id must be an integer"}
    Product = _Product()
    WishlistItem = _WishlistItem()
    db = _db()
    product = Product.query.get(product_id)
    if not product or not product.is_active:
        return {"success": False, "error": "Product not found"}
    existing = WishlistItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if existing:
        return {"success": True, "message_override": "This item is already in your wishlist."}
    item = WishlistItem(user_id=current_user.id, product_id=product_id)
    db.session.add(item)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": str(e)}
    return {"success": True, "message_override": "Added to your wishlist."}


def _execute_remove_from_wishlist(parameters: dict, *, current_user: Optional[Any] = None) -> dict:
    if not current_user:
        return {"success": False, "error": "Please sign in to manage your wishlist."}
    product_id = parameters.get("product_id")
    if product_id is None:
        return {"success": False, "error": "product_id is required"}
    try:
        product_id = int(product_id)
    except (TypeError, ValueError):
        return {"success": False, "error": "product_id must be an integer"}
    WishlistItem = _WishlistItem()
    db = _db()
    item = WishlistItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if not item:
        return {"success": False, "error": "Product not in wishlist."}
    db.session.delete(item)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": str(e)}
    return {"success": True, "message_override": "Removed from your wishlist."}


def _execute_clear_wishlist(*, current_user: Optional[Any] = None) -> dict:
    """Remove all items from the user's wishlist. Requires authentication."""
    if not current_user:
        return {"success": False, "error": "Please sign in to clear your wishlist."}
    WishlistItem = _WishlistItem()
    db = _db()
    deleted = WishlistItem.query.filter_by(user_id=current_user.id).delete()
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": str(e)}
    return {"success": True, "message_override": "Your wishlist is now empty."}


def _execute_add_wishlist_to_cart(
    *,
    current_user: Optional[Any] = None,
    flask_request: Optional[Any] = None,
) -> dict:
    """Add all items from the user's wishlist to their cart. Requires authentication."""
    if not current_user:
        return {"success": False, "error": "Please sign in to add wishlist items to your cart."}
    WishlistItem = _WishlistItem()
    CartItem = _CartItem()
    Product = _Product()
    db = _db()
    items = WishlistItem.query.filter_by(user_id=current_user.id).all()
    if not items:
        return {"success": True, "message_override": "Your wishlist is empty. Add some items first!"}
    added = 0
    skipped = 0
    for wi in items:
        product_id = wi.product_id
        product = Product.query.get(product_id)
        if not product or not product.is_active:
            skipped += 1
            continue
        stock = product.stock_quantity or 0
        if stock < 1:
            skipped += 1
            continue
        quantity = 1
        existing = CartItem.query.filter_by(
            user_id=current_user.id,
            product_id=product_id,
            selected_color=None,
            selected_size=None,
        ).first()
        if existing:
            new_qty = min(existing.quantity + quantity, stock)
            if new_qty > existing.quantity:
                existing.quantity = new_qty
                added += 1
        else:
            db.session.add(CartItem(
                user_id=current_user.id,
                product_id=product_id,
                quantity=min(quantity, stock),
                selected_color=None,
                selected_size=None,
            ))
            added += 1
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": str(e)}
    if added == 0 and skipped == 0:
        return {"success": True, "message_override": "Your wishlist is empty."}
    if added == 0:
        return {"success": True, "message_override": "None of your wishlist items are in stock right now. I couldn't add any to your cart."}
    if skipped == 0:
        return {"success": True, "message_override": f"I've added all {added} item(s) from your wishlist to your cart."}
    return {"success": True, "message_override": f"I've added {added} item(s) from your wishlist to your cart. {skipped} could not be added (out of stock or unavailable)."}


def _message_looks_like_json(msg: str) -> bool:
    """True if the message field appears to contain raw JSON (should not be shown to user)."""
    if not msg or not isinstance(msg, str):
        return False
    s = msg.strip()
    if '"action":' in s or '"action"' in s or '{"action"' in s or "'action':" in s:
        return True
    if re.search(r'\{\s*"action"\s*:', s) or re.search(r"\{\s*'action'\s*:", s):
        return True
    return False


def _parameters_look_like_search(parameters: dict) -> bool:
    """True if parameters look like a product search (infer SEARCH_PRODUCTS when action is missing/corrupt)."""
    if not parameters or not isinstance(parameters, dict):
        return False
    search_keys = {"category", "color", "min_price", "max_price", "search", "query", "on_sale", "clothing_type", "size", "fabric", "occasion"}
    return bool(search_keys & set(parameters.keys()))


def _sanitize_parsed_message(action: str, message: str) -> str:
    """If the parsed message contains raw JSON, return a safe short message instead."""
    if not message or not _message_looks_like_json(message):
        return (message or '').strip()
    action_upper = (action or '').strip().upper()
    safe = {
        'ADD_TO_CART': "I've added the item to your cart.",
        'REMOVE_FROM_CART': "Item removed from your cart.",
        'UPDATE_CART_ITEM': "Cart updated.",
        'CLEAR_CART': "Your cart is now empty.",
        'ADD_TO_WISHLIST': "Added to your wishlist.",
        'REMOVE_FROM_WISHLIST': "Removed from your wishlist.",
        'CLEAR_WISHLIST': "Your wishlist is now empty.",
        'ADD_WISHLIST_TO_CART': "I've added wishlist items to your cart.",
        'SEARCH_PRODUCTS': "Here are the results.",
    }
    return safe.get(action_upper, "Done.")


def parse_llm_json_response(text: str) -> Optional[dict]:
    """
    Extract a single JSON object from LLM text. Handles markdown code blocks and
    text that mixes natural language with JSON (e.g. "I've added {\"action\": \"ADD_TO_CART\" ...}").
    Expects object with keys: action, parameters, message, confidence.
    Prefers a candidate whose action is a known backend action (so the action actually runs).
    """
    if not text or not isinstance(text, str):
        return None
    text = text.strip()

    def try_parse(s: str) -> Optional[dict]:
        try:
            data = json.loads(s)
            if isinstance(data, dict) and "action" in data:
                if "parameters" not in data:
                    data["parameters"] = {}
                if not isinstance(data.get("parameters"), dict):
                    try:
                        data["parameters"] = json.loads(data["parameters"]) if isinstance(data["parameters"], str) else {}
                    except Exception:
                        data["parameters"] = {}
                if "message" not in data:
                    data["message"] = ""
                if "confidence" not in data:
                    data["confidence"] = 0.7
                return data
        except Exception:
            pass
        return None

    # 1) Try full string (and strip markdown)
    for raw in (text, text.split("\n")[0], "\n".join(text.split("\n")[:30])):
        stripped = raw.strip()
        if stripped.startswith("```"):
            stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
            stripped = re.sub(r"\s*```\s*$", "", stripped)
        parsed = try_parse(stripped)
        if parsed:
            a = (parsed.get("action") or "").strip().upper()
            # If action is missing, unknown, or Response/NONE but params look like search, run search so we attach products
            if (not a or a not in ACTIONS or a in ("RESPONSE", "NONE")) and _parameters_look_like_search(parsed.get("parameters")):
                parsed["action"] = "SEARCH_PRODUCTS"
            msg = (parsed.get("message") or "").strip()
            if _message_looks_like_json(msg):
                parsed["message"] = _sanitize_parsed_message(parsed.get("action"), msg)
            return parsed

    # 2) Find every {...} block that might be our JSON; prefer one with a known backend action
    candidates = []
    i = 0
    while i < len(text):
        start = text.find("{", i)
        if start == -1:
            break
        depth = 0
        for j in range(start, len(text)):
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    candidate = try_parse(text[start : j + 1])
                    if candidate:
                        candidates.append(candidate)
                    i = j + 1
                    break
        else:
            i = start + 1

    # Prefer candidate with a real backend action (so the action actually executes)
    for c in candidates:
        a = (c.get("action") or "").strip().upper()
        # If action is missing, unknown, or Response/NONE but params look like search, run search
        if (not a or a not in ACTIONS or a in ("RESPONSE", "NONE")) and _parameters_look_like_search(c.get("parameters")):
            c["action"] = "SEARCH_PRODUCTS"
            a = "SEARCH_PRODUCTS"
        if a in ACTIONS and a not in ("RESPONSE", "NONE"):
            msg = (c.get("message") or "").strip()
            if _message_looks_like_json(msg):
                c["message"] = _sanitize_parsed_message(c.get("action"), msg)
            return c
    for c in candidates:
        a = (c.get("action") or "").strip().upper()
        if (not a or a not in ACTIONS or a in ("RESPONSE", "NONE")) and _parameters_look_like_search(c.get("parameters")):
            c["action"] = "SEARCH_PRODUCTS"
        msg = (c.get("message") or "").strip()
        if _message_looks_like_json(msg):
            c["message"] = _sanitize_parsed_message(c.get("action"), msg)
        return c

    return None
