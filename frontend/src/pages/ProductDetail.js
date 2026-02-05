import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useCart } from '../contexts/CartContext';
import { useNotification } from '../contexts/NotificationContext';
import { useAuth } from '../contexts/AuthContext';
import ProductRating from '../components/ProductRating';
import ColorSwatches from '../components/ColorSwatches';
import SizeSelector from '../components/SizeSelector';
import './ProductDetail.css';

const ProductDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { addToCart } = useCart();
  const { showSuccess, showError } = useNotification();
  const { user, token } = useAuth();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const [selectedColor, setSelectedColor] = useState(null);
  const [selectedSize, setSelectedSize] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [newReview, setNewReview] = useState({ rating: 5, comment: '', user_name: '' });

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
    } else {
      showError(result.error || 'Failed to add to cart');
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
    return <div className="spinner"></div>;
  }

  if (!product) {
    return <div className="container">Product not found</div>;
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

            <div className="product-actions">
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
        <div className="reviews-section" style={{ marginTop: '40px', padding: '20px 0' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h2>Reviews ({reviews.length})</h2>
            <button
              onClick={() => setShowReviewForm(!showReviewForm)}
              className="btn btn-primary"
              style={{ padding: '8px 16px' }}
            >
              {showReviewForm ? 'Cancel' : 'Write a Review'}
            </button>
          </div>

          {/* Review Form */}
          {showReviewForm && (
            <div style={{ 
              border: '1px solid #e0e0e0', 
              borderRadius: '8px', 
              padding: '20px', 
              marginBottom: '30px',
              background: '#f8f9fa'
            }}>
              <h3 style={{ marginBottom: '15px' }}>Write Your Review</h3>
              {!user && (
                <div style={{ marginBottom: '15px' }}>
                  <label style={{ display: 'block', marginBottom: '5px', fontWeight: '600' }}>Your Name *</label>
                  <input
                    type="text"
                    value={newReview.user_name}
                    onChange={(e) => setNewReview({ ...newReview, user_name: e.target.value })}
                    placeholder="Enter your name"
                    style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                  />
                </div>
              )}
              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '600' }}>Rating *</label>
                <div style={{ display: 'flex', gap: '5px' }}>
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      type="button"
                      onClick={() => setNewReview({ ...newReview, rating: star })}
                      style={{
                        background: 'none',
                        border: 'none',
                        fontSize: '24px',
                        cursor: 'pointer',
                        color: star <= newReview.rating ? '#d4af37' : '#d1d5db',
                        padding: 0
                      }}
                    >
                      ★
                    </button>
                  ))}
                  <span style={{ marginLeft: '10px', color: '#666' }}>{newReview.rating} out of 5</span>
                </div>
              </div>
              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '600' }}>Comment (Optional)</label>
                <textarea
                  value={newReview.comment}
                  onChange={(e) => setNewReview({ ...newReview, comment: e.target.value })}
                  placeholder="Share your thoughts about this product..."
                  rows="4"
                  style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px', resize: 'vertical' }}
                />
              </div>
              <button
                onClick={handleSubmitReview}
                className="btn btn-primary"
                style={{ padding: '10px 20px' }}
              >
                Submit Review
              </button>
            </div>
          )}

          {/* Reviews List */}
          <div>
            {reviews.length === 0 ? (
              <p style={{ color: '#666', textAlign: 'center', padding: '40px' }}>
                No reviews yet. Be the first to review this product!
              </p>
            ) : (
              reviews.map((review) => (
                <div
                  key={review.id}
                  style={{
                    border: '1px solid #e0e0e0',
                    borderRadius: '8px',
                    padding: '20px',
                    marginBottom: '15px',
                    background: 'white'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '10px' }}>
                    <div>
                      <div style={{ fontWeight: '600', marginBottom: '5px' }}>
                        {review.user_name || 'Anonymous'}
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <div style={{ display: 'flex', gap: '2px' }}>
                          {[1, 2, 3, 4, 5].map((star) => (
                            <span
                              key={star}
                              style={{
                                fontSize: '16px',
                                color: star <= review.rating ? '#d4af37' : '#d1d5db'
                              }}
                            >
                              ★
                            </span>
                          ))}
                        </div>
                        <span style={{ fontSize: '12px', color: '#666' }}>
                          {new Date(review.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>
                  {review.comment && (
                    <p style={{ marginTop: '10px', color: '#333', lineHeight: '1.6' }}>
                      {review.comment}
                    </p>
                  )}
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

