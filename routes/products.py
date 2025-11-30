from flask import Blueprint, request, jsonify
from models.database import db
from models.product import Product
from routes.auth import require_auth
from sqlalchemy import or_

products_bp = Blueprint('products', __name__)

@products_bp.route('', methods=['GET'])
def get_products():
    """Get all products with optional filters."""
    try:
        category = request.args.get('category', '')
        color = request.args.get('color', '')
        search = request.args.get('search', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
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
        
        return jsonify({
            'products': [p.to_dict() for p in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }), 200
        
    except Exception as e:
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

@products_bp.route('/price-range', methods=['GET'])
def get_price_range():
    """Get min and max price range."""
    try:
        from sqlalchemy import func
        result = db.session.query(
            func.min(Product.price).label('min'),
            func.max(Product.price).label('max')
        ).filter(Product.is_active == True).first()
        
        return jsonify({
            'min': float(result.min) if result.min else 0,
            'max': float(result.max) if result.max else 1000
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

