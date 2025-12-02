from flask import Blueprint, request, jsonify
from models.database import db
from models.review import Review
from models.product import Product
from models.user import User
from routes.auth import require_auth
from sqlalchemy import func
from functools import wraps

reviews_bp = Blueprint('reviews', __name__)

def get_current_user_optional():
    """Get current user if authenticated, otherwise return None."""
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        try:
            from routes.auth import verify_jwt_token
            token = auth_header[7:]
            payload = verify_jwt_token(token)
            if payload:
                user = User.query.get(payload['user_id'])
                return user
        except:
            pass
    return None

@reviews_bp.route('/products/<int:product_id>/reviews', methods=['GET'])
def get_product_reviews(product_id):
    """Get all reviews for a product."""
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        pagination = Review.query.filter_by(product_id=product_id).order_by(
            Review.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'reviews': [review.to_dict() for review in pagination.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reviews_bp.route('/products/<int:product_id>/reviews', methods=['POST'])
def create_review(product_id):
    """Create a new review for a product."""
    try:
        product = Product.query.get(product_id)
        if not product or not product.is_active:
            return jsonify({'error': 'Product not found'}), 404
        
        data = request.get_json()
        rating = float(data.get('rating', 0))
        comment = data.get('comment', '').strip()
        user_name = data.get('user_name', '').strip()
        
        # Validate rating
        if not rating or rating < 1.0 or rating > 5.0:
            return jsonify({'error': 'Rating must be between 1.0 and 5.0'}), 400
        
        # Get current user (optional - allows guest reviews)
        user = get_current_user_optional()
        
        # Check if user already reviewed this product
        if user:
            existing_review = Review.query.filter_by(
                product_id=product_id,
                user_id=user.id
            ).first()
            if existing_review:
                return jsonify({'error': 'You have already reviewed this product'}), 400
        
        # Create review
        review = Review(
            product_id=product_id,
            user_id=user.id if user else None,
            rating=rating,
            comment=comment if comment else None,
            user_name=user_name if not user else None
        )
        
        db.session.add(review)
        db.session.commit()
        
        # Update product rating and review count
        update_product_rating(product_id)
        
        return jsonify({
            'message': 'Review submitted successfully',
            'review': review.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@reviews_bp.route('/reviews/<int:review_id>', methods=['PUT'])
@require_auth
def update_review(review_id):
    """Update a review (only by the author or admin)."""
    try:
        review = Review.query.get(review_id)
        if not review:
            return jsonify({'error': 'Review not found'}), 404
        
        user = request.current_user
        
        # Check if user is the author or admin
        if review.user_id != user.id and not user.is_admin:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        if 'rating' in data:
            rating = float(data['rating'])
            if rating < 1.0 or rating > 5.0:
                return jsonify({'error': 'Rating must be between 1.0 and 5.0'}), 400
            review.rating = rating
        
        if 'comment' in data:
            review.comment = data['comment'].strip() or None
        
        db.session.commit()
        
        # Update product rating
        update_product_rating(review.product_id)
        
        return jsonify({
            'message': 'Review updated successfully',
            'review': review.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@reviews_bp.route('/reviews/<int:review_id>', methods=['DELETE'])
@require_auth
def delete_review(review_id):
    """Delete a review (only by the author or admin)."""
    try:
        review = Review.query.get(review_id)
        if not review:
            return jsonify({'error': 'Review not found'}), 404
        
        user = request.current_user
        
        # Check if user is the author or admin
        if review.user_id != user.id and not user.is_admin:
            return jsonify({'error': 'Unauthorized'}), 403
        
        product_id = review.product_id
        db.session.delete(review)
        db.session.commit()
        
        # Update product rating
        update_product_rating(product_id)
        
        return jsonify({'message': 'Review deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def update_product_rating(product_id):
    """Update product's average rating and review count based on reviews."""
    try:
        # Calculate average rating and count
        result = db.session.query(
            func.avg(Review.rating).label('avg_rating'),
            func.count(Review.id).label('count')
        ).filter_by(product_id=product_id).first()
        
        product = Product.query.get(product_id)
        if product:
            if result.avg_rating:
                product.rating = round(float(result.avg_rating), 2)
            else:
                product.rating = 0.0
            product.review_count = result.count or 0
            db.session.commit()
    except Exception as e:
        print(f"Error updating product rating: {e}")
        db.session.rollback()

