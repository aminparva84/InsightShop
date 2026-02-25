import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useCart } from '../contexts/CartContext';
import { useNotification } from '../contexts/NotificationContext';
import { useAuth } from '../contexts/AuthContext';
import { useWishlist } from '../contexts/WishlistContext';
import ProductRating from '../components/ProductRating';
import ColorSwatches from '../components/ColorSwatches';
import SizeSelector from '../components/SizeSelector';
import './ProductDetail.css';

const ProductDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { addToCart } = useCart();
  const { showSuccess, showError, showWarning } = useNotification();
  const { user, token, isAuthenticated } = useAuth();
  const { isInWishlist, toggleWishlist } = useWishlist();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const [selectedColor, setSelectedColor] = useState(null);
  const [selectedSize, setSelectedSize] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [newReview, setNewReview] = useState({ rating: 5, comment: '', user_name: '' });
  const [copyIdFeedback, setCopyIdFeedback] = useState(false);

  useEffect(() => {
    fetchProduct();
    fetchReviews();
  }, [id]);

  const fetchProduct = async () => {
    try {
      const response = await axios.get(`/api/products/${id}`);
      const productData = response.data.product;
      setProduct(productData);
      
      // Set default selections
      if (productData.available_colors && productData.available_colors.length > 0) {
        setSelectedColor(productData.available_colors[0]);
      } else if (productData.color) {
        setSelectedColor(productData.color);
      }
      
      if (productData.available_sizes && productData.available_sizes.length > 0) {
        setSelectedSize(productData.available_sizes[0]);
      } else if (productData.size) {
        setSelectedSize(productData.size);
      }
    } catch (error) {
      console.error('Error fetching product:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchReviews = async () => {
    try {
      const response = await axios.get(`/api/products/${id}/reviews`);
      setReviews(response.data.reviews || []);
    } catch (error) {
      console.error('Error fetching reviews:', error);
    }
  };

  const handleAddToCart = async () => {
    if (!selectedColor && product.available_colors && product.available_colors.length > 0) {
      showError('Please select a color');
      return;
    }
    if (!selectedSize && product.available_sizes && product.available_sizes.length > 0) {
      showError('Please select a size');
      return;
    }
    
    // Guest shopping enabled - no login required
    const result = await addToCart(product.id, quantity, selectedColor, selectedSize);
    if (result.success) {
      showSuccess('Added to cart!');
      // Low stock alert: show second toast after a tick so both notifications appear (avoids React batching)
      const stock = product?.stock_quantity;
      const remaining = typeof result.remaining_stock === 'number' ? result.remaining_stock : (typeof stock === 'number' ? Math.max(0, stock - quantity) : null);
      const lowStockCount = typeof remaining === 'number' ? remaining : (typeof stock === 'number' && stock >= 1 && stock <= 5 ? stock : null);
      if (lowStockCount !== null && lowStockCount >= 1 && lowStockCount <= 5) {
        const message = `Only ${lowStockCount} left in stock. Make sure to finalize your purchase soon before the item is sold out.`;
        setTimeout(() => showSuccess(message, 6000), 100);
      }
    } else {
      showError(result.error || 'Failed to add to cart');
    }
  };

  const handleWishlistToggle = async () => {
    if (!isAuthenticated) {
      showError('Please log in to save items to your wishlist.');
      return;
    }
    const result = await toggleWishlist(product.id);
    if (result.success) {
      showSuccess(isInWishlist(product.id) ? 'Removed from wishlist' : 'Added to wishlist');
    } else if (result.error) {
      showError(result.error);
    }
  };

  const handleCopyProductId = async () => {
    const idStr = String(product.id);
    try {
      await navigator.clipboard.writeText(idStr);
      showSuccess('Product ID copied to clipboard');
      setCopyIdFeedback(true);
      setTimeout(() => setCopyIdFeedback(false), 2000);
    } catch (err) {
      showError('Failed to copy product ID');
    }
  };

  const handleSubmitReview = async () => {
    if (!newReview.rating || newReview.rating < 1 || newReview.rating > 5) {
      showError('Please select a rating between 1 and 5');
      return;
    }
    if (!user && !newReview.user_name.trim()) {
      showError('Please enter your name');
      return;
    }

    try {
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const response = await axios.post(
        `/api/products/${id}/reviews`,
        {
          rating: newReview.rating,
          comment: newReview.comment,
          user_name: !user ? newReview.user_name : undefined
        },
        { headers }
      );

      if (response.data) {
        showSuccess('Review submitted successfully!');
        setNewReview({ rating: 5, comment: '', user_name: '' });
        setShowReviewForm(false);
        fetchReviews();
        fetchProduct(); // Refresh product to update rating
      }
    } catch (error) {
      showError(error.response?.data?.error || 'Failed to submit review');
    }
  };

  if (loading) {
    return (
      <div className="product-detail-page">
        <div className="container product-detail-loading">
          <div className="spinner" aria-label="Loading product"></div>
        </div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="product-detail-page">
        <div className="container product-detail-not-found">
          <p>Product not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="product-detail-page">
      <div className="container">
        <div className="product-detail-layout">
          <div className="product-image-section">
            <img
              src={product.image_url || 'https://via.placeholder.com/600x600?text=Product'}
              alt={product.name}
              onError={(e) => {
                e.target.src = 'https://via.placeholder.com/600x600?text=Product';
              }}
            />
          </div>

          <div className="product-info-section">
            <h1 className="product-title">{product.name}</h1>
            
            <ProductRating rating={product.rating || 0} reviewCount={product.review_count || 0} />
            
            <div className="product-meta">
              <span className="product-category">{product.category}</span>
              {product.fabric && <span className="product-fabric">{product.fabric}</span>}
            </div>

            <div className="product-price">
              {product.on_sale ? (
                <>
                  <span className="original-price">${product.original_price.toFixed(2)}</span>
                  <span className="sale-price">${product.price.toFixed(2)}</span>
                  {product.discount_percentage && (
                    <span className="discount-badge">-{product.discount_percentage.toFixed(0)}%</span>
                  )}
                </>
              ) : (
                <span>${product.price.toFixed(2)}</span>
              )}
            </div>

            <div className="product-detail-actions-row">
            <button
              type="button"
              className={`product-detail-wishlist-btn ${isInWishlist(product.id) ? 'product-detail-wishlist-btn--active' : ''}`}
              onClick={handleWishlistToggle}
              aria-label={isInWishlist(product.id) ? 'Remove from wishlist' : 'Add to wishlist'}
            >
              {isInWishlist(product.id) ? (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                  <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
                </svg>
              ) : (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
                </svg>
              )}
            </button>
            <button
              type="button"
              className="btn-copy-product-id"
              onClick={handleCopyProductId}
              aria-label="Copy product ID to clipboard"
            >
              {copyIdFeedback ? 'Copied!' : 'Copy product ID'}
            </button>
            </div>
            
            {/* Color Selection - Only show if multiple colors available */}
            {product.available_colors && product.available_colors.length > 1 && (
              <ColorSwatches 
                colors={product.available_colors} 
                selectedColor={selectedColor}
                onColorSelect={setSelectedColor}
              />
            )}
            
            {/* Size Selection - Only show if multiple sizes available */}
            {product.available_sizes && product.available_sizes.length > 1 && (
              <SizeSelector 
                sizes={product.available_sizes} 
                selectedSize={selectedSize}
                onSizeSelect={setSelectedSize}
              />
            )}

            {product.description && (
              <div className="product-description">
                <h3>Description</h3>
                <p>{product.description}</p>
              </div>
            )}

            <div className="product-stock">
              {product.stock_quantity > 0 ? (
                <span className="in-stock">In Stock ({product.stock_quantity} available)</span>
              ) : (
                <span className="out-of-stock">Out of Stock</span>
              )}
            </div>

            <div className="product-actions product-actions--wrap">
              <div className="quantity-selector">
                <label>Quantity:</label>
                <input
                  type="number"
                  min="1"
                  max={product.stock_quantity}
                  value={quantity}
                  onChange={(e) => {
                    const raw = parseInt(e.target.value, 10);
                    const clamped = Math.min(product.stock_quantity || 1, Math.max(1, Number.isNaN(raw) ? 1 : raw));
                    setQuantity(clamped);
                  }}
                  className="quantity-input"
                />
              </div>

              <button
                onClick={handleAddToCart}
                disabled={product.stock_quantity === 0}
                className="btn btn-primary btn-add-cart-large"
              >
                Add to Cart
              </button>
            </div>
          </div>
        </div>

        {/* Reviews Section */}
        <div className="reviews-section">
          <div className="reviews-section-header">
            <h2>Reviews ({reviews.length})</h2>
            <button
              type="button"
              onClick={() => setShowReviewForm(!showReviewForm)}
              className="btn btn-write-review"
            >
              {showReviewForm ? 'Cancel' : 'Write a Review'}
            </button>
          </div>

          {/* Review Form */}
          {showReviewForm && (
            <div className="review-form-card">
              <h3>Write Your Review</h3>
              {!user && (
                <div className="review-form-field">
                  <label htmlFor="review-name">Your Name *</label>
                  <input
                    id="review-name"
                    type="text"
                    value={newReview.user_name}
                    onChange={(e) => setNewReview({ ...newReview, user_name: e.target.value })}
                    placeholder="Enter your name"
                  />
                </div>
              )}
              <div className="review-form-field">
                <label>Rating *</label>
                <div className="review-form-stars">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      type="button"
                      onClick={() => setNewReview({ ...newReview, rating: star })}
                      data-active={star <= newReview.rating}
                      aria-label={`${star} star${star !== 1 ? 's' : ''}`}
                    >
                      ★
                    </button>
                  ))}
                  <span className="star-label">{newReview.rating} out of 5</span>
                </div>
              </div>
              <div className="review-form-field">
                <label htmlFor="review-comment">Comment (Optional)</label>
                <textarea
                  id="review-comment"
                  value={newReview.comment}
                  onChange={(e) => setNewReview({ ...newReview, comment: e.target.value })}
                  placeholder="Share your thoughts about this product..."
                  rows={4}
                />
              </div>
              <button type="button" onClick={handleSubmitReview} className="btn btn-submit-review">
                Submit Review
              </button>
            </div>
          )}

          {/* Reviews List */}
          <div>
            {reviews.length === 0 ? (
              <p className="reviews-empty">
                No reviews yet. Be the first to review this product!
              </p>
            ) : (
              reviews.map((review) => (
                <div key={review.id} className="review-card">
                  <div className="review-card-header">
                    <div>
                      <div className="review-card-author">{review.user_name || 'Anonymous'}</div>
                      <div className="review-card-meta">
                        <div className="review-card-stars">
                          {[1, 2, 3, 4, 5].map((star) => (
                            <span key={star} className={star <= review.rating ? '' : 'empty'}>
                              ★
                            </span>
                          ))}
                        </div>
                        <span className="review-card-date">
                          {new Date(review.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>
                  {review.comment && <p className="review-card-comment">{review.comment}</p>}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProductDetail;

