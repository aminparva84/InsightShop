from flask import Blueprint, request, jsonify
from models.database import db
from models.product import Product
from routes.auth import require_auth
from sqlalchemy import or_, func, desc, asc

products_bp = Blueprint('products', __name__)

@products_bp.route('', methods=['GET'])
def get_products():
    """Get all products with optional filters."""
    try:
        # Check database connection
        if not db.session:
            return jsonify({'error': 'Database connection not available'}), 500
        category = request.args.get('category', '')
        color = request.args.get('color', '')
        search = request.args.get('search', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Support filtering by product IDs (for AI results)
        product_ids_param = request.args.get('ids', '')
        if product_ids_param:
            try:
                # Parse product IDs more robustly
                product_ids = []
                for id_str in product_ids_param.split(','):
                    id_str = id_str.strip()
                    if id_str:  # Only process non-empty strings
                        try:
                            product_id = int(id_str)
                            if product_id > 0:  # Ensure positive ID
                                product_ids.append(product_id)
                        except ValueError:
                            # Skip invalid IDs but continue processing
                            continue
                
                if product_ids:
                    # Fetch products by IDs and maintain order
                    products = Product.query.filter(
                        Product.id.in_(product_ids),
                        Product.is_active == True
                    ).all()
                    # Maintain order from the IDs list
                    product_dict = {p.id: p for p in products}
                    ordered_products = [product_dict[id] for id in product_ids if id in product_dict]
                    return jsonify({
                        'products': [p.to_dict() for p in ordered_products],
                        'total': len(ordered_products),
                        'page': 1,
                        'per_page': len(ordered_products),
                        'pages': 1
                    }), 200
                else:
                    # If no valid IDs found, return empty result instead of falling through
                    return jsonify({
                        'products': [],
                        'total': 0,
                        'page': 1,
                        'per_page': 0,
                        'pages': 1
                    }), 200
            except Exception as e:
                # Log error but return empty result for AI queries
                print(f"Error parsing product IDs: {e}")
                return jsonify({
                    'products': [],
                    'total': 0,
                    'page': 1,
                    'per_page': 0,
                    'pages': 1
                }), 200
        
        query = Product.query.filter_by(is_active=True)
        
        if category:
            query = query.filter_by(category=category)
        
        if color:
            query = query.filter_by(color=color)
        
        size = request.args.get('size', '')
        if size:
            query = query.filter_by(size=size)
        
        fabric = request.args.get('fabric', '')
        if fabric:
            query = query.filter_by(fabric=fabric)
        
        season = request.args.get('season', '')
        if season:
            query = query.filter_by(season=season)
        
        clothing_category = request.args.get('clothing_category', '')
        if clothing_category:
            query = query.filter_by(clothing_category=clothing_category)
        
        min_price = request.args.get('min_price', '')
        if min_price:
            try:
                query = query.filter(Product.price >= float(min_price))
            except ValueError:
                pass
        
        max_price = request.args.get('max_price', '')
        if max_price:
            try:
                query = query.filter(Product.price <= float(max_price))
            except ValueError:
                pass
        
        if search:
            query = query.filter(
                or_(
                    Product.name.ilike(f'%{search}%'),
                    Product.description.ilike(f'%{search}%')
                )
            )
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Convert products to dict with error handling
        products_list = []
        for p in pagination.items:
            try:
                products_list.append(p.to_dict())
            except Exception as e:
                # If to_dict fails (e.g., Sale table issue), create basic dict
                import traceback
                print(f"Error converting product {p.id} to dict: {e}")
                print(traceback.format_exc())
                # Return basic product info without sale data
                products_list.append({
                    'id': p.id,
                    'name': p.name,
                    'description': p.description,
                    'price': float(p.price) if p.price else 0.0,
                    'original_price': float(p.price) if p.price else 0.0,
                    'on_sale': False,
                    'category': p.category,
                    'color': p.color,
                    'season': getattr(p, 'season', None),
                    'clothing_category': getattr(p, 'clothing_category', 'other'),
                    'image_url': p.image_url,
                    'is_active': p.is_active
                })
        
        return jsonify({
            'products': products_list,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }), 200
        
    except Exception as e:
        import traceback
        print(f"Error in get_products: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

# IMPORTANT: Specific routes must come BEFORE the dynamic route to avoid conflicts
@products_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all product categories."""
    try:
        categories = db.session.query(Product.category).distinct().all()
        return jsonify({
            'categories': [cat[0] for cat in categories if cat[0]]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@products_bp.route('/colors', methods=['GET'])
def get_colors():
    """Get all product colors."""
    try:
        colors = db.session.query(Product.color).distinct().filter(
            Product.color.isnot(None),
            Product.is_active == True
        ).all()
        return jsonify({
            'colors': [color[0] for color in colors if color[0]]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@products_bp.route('/sizes', methods=['GET'])
def get_sizes():
    """Get all available sizes."""
    try:
        sizes = db.session.query(Product.size).distinct().filter(
            Product.size.isnot(None),
            Product.is_active == True
        ).all()
        sizes_list = [size[0] for size in sizes if size[0]]
        return jsonify({'sizes': sorted(sizes_list)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@products_bp.route('/fabrics', methods=['GET'])
def get_fabrics():
    """Get all available fabrics."""
    try:
        fabrics = db.session.query(Product.fabric).distinct().filter(
            Product.fabric.isnot(None),
            Product.is_active == True
        ).all()
        fabrics_list = [fabric[0] for fabric in fabrics if fabric[0]]
        return jsonify({'fabrics': sorted(fabrics_list)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@products_bp.route('/seasons', methods=['GET'])
def get_seasons():
    """Get all product seasons."""
    try:
        seasons = db.session.query(Product.season).distinct().filter(
            Product.season.isnot(None),
            Product.is_active == True
        ).all()
        seasons_list = [s[0] for s in seasons if s[0]]
        return jsonify({'seasons': sorted(seasons_list)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@products_bp.route('/clothing-categories', methods=['GET'])
def get_clothing_categories():
    """Get all product clothing categories (pants, shirts, jackets, etc.)."""
    try:
        categories = db.session.query(Product.clothing_category).distinct().filter(
            Product.clothing_category.isnot(None),
            Product.is_active == True
        ).all()
        categories_list = [c[0] for c in categories if c[0]]
        return jsonify({'clothing_categories': sorted(categories_list)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@products_bp.route('/price-range', methods=['GET'])
def get_price_range():
    """Get min and max price range."""
    try:
        from sqlalchemy import func
        result = db.session.query(
            func.min(Product.price).label('min'),
            func.max(Product.price).label('max')
        ).filter(Product.is_active == True).first()
        
        if result:
            min_price = float(result.min) if result.min is not None else 0
            max_price = float(result.max) if result.max is not None else 1000
        else:
            min_price = 0
            max_price = 1000
        
        return jsonify({
            'min': min_price,
            'max': max_price
        }), 200
    except Exception as e:
        print(f"Error in get_price_range: {e}")
        return jsonify({'error': str(e)}), 500

@products_bp.route('/search', methods=['POST'])
def search_products():
    """
    Enhanced product search for AI agent (The Personal Shopper).
    Inputs: query (str), max_price (float), category (str), size (str), sort_by (str)
    Output: JSON list of products with Name, Price, Image URL, and Add to Cart link
    """
    try:
        data = request.get_json() or {}
        
        # Get search parameters
        query_text = data.get('query', '').strip()
        max_price = data.get('max_price')
        category = data.get('category', '').strip()
        size = data.get('size', '').strip()
        sort_by = data.get('sort_by', 'relevance')  # relevance, rating, price_low, price_high
        
        # Build query - only active products with inventory
        query = Product.query.filter(
            Product.is_active == True,
            Product.stock_quantity > 0
        )
        
        # Apply filters
        if category:
            query = query.filter_by(category=category)
        
        if size:
            query = query.filter_by(size=size)
        
        season = data.get('season', '').strip()
        if season:
            query = query.filter_by(season=season)
        
        clothing_category = data.get('clothing_category', '').strip()
        if clothing_category:
            query = query.filter_by(clothing_category=clothing_category)
        
        if max_price is not None:
            try:
                max_price_float = float(max_price)
                query = query.filter(Product.price <= max_price_float)
            except (ValueError, TypeError):
                pass
        
        # Apply search query
        if query_text:
            query = query.filter(
                or_(
                    Product.name.ilike(f'%{query_text}%'),
                    Product.description.ilike(f'%{query_text}%'),
                    Product.clothing_type.ilike(f'%{query_text}%'),
                    Product.color.ilike(f'%{query_text}%')
                )
            )
        
        # Apply sorting
        if sort_by == 'rating' or 'review' in query_text.lower() or 'best rated' in query_text.lower():
            # Sort by rating (highest first), then by review count
            query = query.order_by(desc(Product.rating), desc(Product.review_count))
        elif sort_by == 'price_low':
            query = query.order_by(asc(Product.price))
        elif sort_by == 'price_high':
            query = query.order_by(desc(Product.price))
        else:
            # Default: relevance (by rating if available, otherwise by name)
            query = query.order_by(desc(Product.rating), Product.name)
        
        # Limit results
        products = query.limit(50).all()
        
        # Format results for AI agent
        results = []
        for product in products:
            product_dict = product.to_dict()
            results.append({
                'id': product.id,
                'name': product.name,
                'price': float(product.price) if product.price else 0.0,
                'original_price': product_dict.get('original_price', float(product.price) if product.price else 0.0),
                'on_sale': product_dict.get('on_sale', False),
                'image_url': product.image_url or '',
                'category': product.category,
                'rating': float(product.rating) if product.rating else 0.0,
                'review_count': product.review_count or 0,
                'stock_quantity': product.stock_quantity,
                'add_to_cart_url': f'/api/cart',  # Frontend will handle the actual add to cart
                'product_url': f'/products/{product.id}',
                'description': product.description or ''
            })
        
        return jsonify({
            'success': True,
            'products': results,
            'total': len(results),
            'filters_applied': {
                'query': query_text,
                'max_price': max_price,
                'category': category,
                'size': size,
                'season': season,
                'clothing_category': clothing_category,
                'sort_by': sort_by
            }
        }), 200
        
    except Exception as e:
        import traceback
        print(f"Error in search_products: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@products_bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get a single product by ID."""
    try:
        product = Product.query.get(product_id)
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        if not product.is_active:
            return jsonify({'error': 'Product not found'}), 404
        
        return jsonify({'product': product.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

