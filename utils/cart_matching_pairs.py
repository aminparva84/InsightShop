"""
Cart Matching Pairs - AI-powered recommendations that complete the look for cart items.
Uses fashion knowledge base, product relations, and fashion match rules.
"""

from models.database import db
from models.product import Product
from sqlalchemy import or_, and_

try:
    from models.product_relation import ProductRelation
except ImportError:
    ProductRelation = None

from utils.fashion_kb import get_color_matching_advice, get_outfit_formula
from utils.fashion_match_rules import find_matching_products, get_match_explanation
from utils.product_relations import get_related_clothing_types


def _resolve_matched_name_to_products(matched_name, exclude_ids, limit=3):
    """
    Resolve a matched product name (e.g. 'Brown Leather Loafers') to actual Product rows.
    Tries: name ilike, then clothing_type from keywords.
    """
    if not matched_name or not exclude_ids:
        return []
    name_lower = matched_name.lower()
    # Build search: product name contains key parts, or clothing_type matches
    parts = [w for w in name_lower.replace("/", " ").replace("-", " ").split() if len(w) > 2]
    if not parts:
        return []
    queries = [Product.name.ilike(f"%{p}%") for p in parts[:3]]  # first 3 meaningful words
    q = Product.query.filter(
        and_(
            Product.is_active == True,
            ~Product.id.in_(exclude_ids),
            or_(*queries)
        )
    ).limit(limit)
    return q.all()


def _get_products_by_clothing_types(clothing_types, exclude_ids, color_hint=None, limit=5):
    """Get products whose clothing_type is in the given list. Optionally prefer color_hint."""
    if not clothing_types or not exclude_ids:
        return []
    q = Product.query.filter(
        and_(
            Product.is_active == True,
            ~Product.id.in_(exclude_ids),
            Product.clothing_type.in_(clothing_types)
        )
    )
    products = q.limit(limit * 2).all()  # fetch extra in case we filter by color
    if color_hint and products:
        # Prefer products whose color pairs well (simple: same color family or neutral)
        color_lower = (color_hint or "").lower()
        neutrals = {"black", "white", "gray", "navy", "beige", "brown", "khaki"}
        def score(p):
            c = (p.color or "").lower()
            if c in neutrals:
                return 2  # neutrals go with everything
            if c == color_lower:
                return 1  # same color (monochromatic)
            return 0
        products = sorted(products, key=score, reverse=True)
    return products[:limit]


def get_matching_pairs_for_cart(cart_product_ids, max_results=8):
    """
    Get product recommendations that "complete the look" for items in the cart.
    Uses ProductRelation (fashion match), fashion_match_rules, and outfit_formulas + color KB.

    Returns:
        List of dicts: { "product": <Product>, "reason": str }
        Sorted by relevance; no duplicates; excludes cart product IDs.
    """
    if not cart_product_ids:
        return []
    exclude_ids = set(cart_product_ids)
    cart_products = Product.query.filter(
        and_(Product.id.in_(cart_product_ids), Product.is_active == True)
    ).all()
    if not cart_products:
        return []

    results = []  # list of { "product": Product, "reason": str, "sort_key": (priority, id) }
    seen_ids = set(exclude_ids)

    # 1) ProductRelation: related products with is_fashion_match=True
    if ProductRelation:
        for cart_product in cart_products:
            relations = ProductRelation.query.filter_by(
                product_id=cart_product.id,
                is_fashion_match=True
            ).limit(4).all()
            for rel in relations:
                if rel.related_product_id in seen_ids:
                    continue
                related = Product.query.get(rel.related_product_id)
                if related and related.is_active:
                    seen_ids.add(related.id)
                    results.append({
                        "product": related,
                        "reason": f"Pairs well with your {cart_product.name}",
                        "sort_key": (1, related.id),
                    })
                    if len(results) >= max_results * 2:
                        break
            if len(results) >= max_results * 2:
                break

    # 2) Fashion match rules: find_matching_products(primary_name) -> resolve names to products
    for cart_product in cart_products:
        matches = find_matching_products(cart_product.name, cart_product.id)
        for m in matches:
            matched_name = m.get("matched_product") or m.get("matched")
            match_type = m.get("match_type", "")
            priority = m.get("priority", 2)
            resolved = _resolve_matched_name_to_products(matched_name, seen_ids, limit=2)
            for prod in resolved:
                if prod.id in seen_ids:
                    continue
                seen_ids.add(prod.id)
                explanation = get_match_explanation(match_type)
                reason = f"{explanation} — goes with your {cart_product.name}"
                results.append({
                    "product": prod,
                    "reason": reason,
                    "sort_key": (priority, prod.id),
                })
            if len(results) >= max_results * 2:
                break
        if len(results) >= max_results * 2:
            break

    # 3) Outfit formulas + related clothing types: suggest by category
    for cart_product in cart_products:
        formula = get_outfit_formula(cart_product.name or cart_product.clothing_type or "")
        related_types = get_related_clothing_types(cart_product.clothing_type)
        if not related_types:
            continue
        color_hint = cart_product.color
        suggested = _get_products_by_clothing_types(
            related_types, list(seen_ids), color_hint=color_hint, limit=3
        )
        for prod in suggested:
            if prod.id in seen_ids:
                continue
            seen_ids.add(prod.id)
            reason = f"Completes the look with your {cart_product.name}"
            results.append({
                "product": prod,
                "reason": reason,
                "sort_key": (2, prod.id),
            })
        if len(results) >= max_results * 2:
            break

    # Deduplicate by product id (keep first occurrence), sort by sort_key, then limit
    by_id = {}
    for r in results:
        pid = r["product"].id
        if pid not in by_id:
            by_id[pid] = r
    ordered = sorted(by_id.values(), key=lambda x: x["sort_key"])
    final = ordered[:max_results]
    return [{"product": item["product"], "reason": item["reason"]} for item in final]
