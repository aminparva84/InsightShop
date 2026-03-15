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
import { isCombinationInStock, getFirstInStockColorForSize, getFirstInStockSizeForColor } from '../utils/variationAvailability';
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
  const [variation, setVariation] = useState(null);
  const [variationLoading, setVariationLoading] = useState(false);
  const [reviews, setReviews] = useState([]);
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [newReview, setNewReview] = useState({ rating: 5, comment: '', user_name: '' });
  const [copyIdFeedback, setCopyIdFeedback] = useState(false);
  const [selectedImageIndex, setSelectedImageIndex] = useState(0);
  const [descriptionExpanded, setDescriptionExpanded] = useState(false);

  // Resolve image list for current selection: by selected color from images_by_color, else fallback to product.image_url
  const getCurrentImages = () => {
    if (!product) return [];
    const ibc = product.images_by_color && typeof product.images_by_color === 'object' ? product.images_by_color : null;
    const colorKey = selectedColor && ibc ? Object.keys(ibc).find(k => String(k).trim().toLowerCase() === String(selectedColor).trim().toLowerCase()) : null;
    const list = (colorKey && Array.isArray(ibc[colorKey]) && ibc[colorKey].length > 0)
      ? ibc[colorKey]
      : (product.image_url ? [product.image_url] : []);
    return list;
  };

  const currentImages = getCurrentImages();
  const placeholderImg = 'https://via.placeholder.com/600x600?text=Product';

  useEffect(() => {
    setSelectedImageIndex(0);
  }, [selectedColor, product?.id]);

  useEffect(() => {
    setDescriptionExpanded(false);
  }, [product?.id]);

  useEffect(() => {
    fetchProduct();
    fetchReviews();
  }, [id]);

  const hasVariations = product && (
    (product.available_colors && product.available_colors.length > 0) ||
    (product.available_sizes && product.available_sizes.length > 0)
  );

  useEffect(() => {
    if (!id || !product || !hasVariations) {
      setVariation(null);
      setVariationLoading(false);
      return;
    }
    const color = selectedColor || (product.available_colors && product.available_colors[0]) || product.color || '';
    const size = selectedSize || (product.available_sizes && product.available_sizes[0]) || product.size || '';
    if (!size || !color) {
      setVariation(null);
      setVariationLoading(false);
      return;
    }
    setVariationLoading(true);
    const controller = new AbortController();
    axios.get(`/api/products/${id}/variation`, {
      params: { size, color },
      signal: controller.signal
    })
      .then((res) => {
        setVariation(res.data);
        setVariationLoading(false);
      })
      .catch((err) => {
        if (err.name !== 'CanceledError' && err.name !== 'AbortError') {
          setVariation(null);
        }
        setVariationLoading(false);
      });
    return () => controller.abort();
  }, [id, product, hasVariations, selectedColor, selectedSize]);

  const fetchProduct = async () => {
    try {
      const response = await axios.get(`/api/products/${id}`);
      const productData = response.data.product;
      setProduct(productData);

      const sizes = productData.available_sizes || (productData.size ? [productData.size] : []);
      const colors = productData.available_colors || (productData.color ? [productData.color] : []);
      const availability = productData.variation_availability || [];

      // Default to first in-stock (size, color) so we never show "This combination is unavailable"
      const norm = (s) => String(s).trim().toLowerCase();
      let defaultSize = sizes[0];
      let defaultColor = colors[0];
      if (availability.length > 0 && sizes.length && colors.length) {
        outer: for (const sz of sizes) {
          for (const cl of colors) {
            const v = availability.find(
              (x) => norm(x.size) === norm(sz) && norm(x.color) === norm(cl) && Number(x.stock_quantity) > 0
            );
            if (v) {
              defaultSize = sz;
              defaultColor = cl;
              break outer;
            }
          }
        }
      }
      if (sizes.length) setSelectedSize(defaultSize);
      if (colors.length) setSelectedColor(defaultColor);
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

  const availability = product?.variation_availability || [];
  const sizes = product?.available_sizes || (product?.size ? [product.size] : []);
  const colors = product?.available_colors || (product?.color ? [product.color] : []);

  const handleSizeSelect = (size) => {
    setSelectedSize(size);
    if (availability.length && selectedColor && !isCombinationInStock(availability, size, selectedColor)) {
      setSelectedColor(getFirstInStockColorForSize(availability, size, colors));
    }
  };

  const handleColorSelect = (color) => {
    setSelectedColor(color);
    if (availability.length && selectedSize && !isCombinationInStock(availability, selectedSize, color)) {
      setSelectedSize(getFirstInStockSizeForColor(availability, color, sizes));
    }
  };

  const baseUrl = process.env.PUBLIC_URL || '';
  const resolveImageSrc = (url) => (!url ? placeholderImg : (url.startsWith('/') ? baseUrl + url : url));

  const goPrevImage = () => {
    setSelectedImageIndex((i) => (i <= 0 ? currentImages.length - 1 : i - 1));
  };
  const goNextImage = () => {
    setSelectedImageIndex((i) => (currentImages.length <= 1 ? 0 : (i + 1) % currentImages.length));
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
    if (hasVariations && variation && variation.stock_quantity === 0) {
      showError('This variation is out of stock');
      return;
    }
    const result = await addToCart(
      product.id,
      quantity,
      selectedColor,
      selectedSize,
      variation?.variation_id ?? null
    );
    if (result.success) {
      showSuccess('Added to cart!');
      const remaining = typeof result.remaining_stock === 'number' ? result.remaining_stock : (variation?.stock_quantity ?? null);
      if (remaining !== null && remaining >= 1 && remaining <= 5) {
        setTimeout(() => showSuccess(`Only ${remaining} left in stock for this variation.`, 6000), 100);
      }
      if (variation && typeof result.remaining_stock === 'number') {
        setVariation((v) => v ? { ...v, stock_quantity: result.remaining_stock } : v);
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
          <div className="product-image-column">
            <div className="product-image-section">
              <div className="product-image-section-inner">
                {/* Thumbnail strip – desktop only, left side; show even for 1 image so gallery is always visible */}
                {currentImages.length >= 1 && (
                  <div className="product-gallery-thumbnails" aria-hidden="true">
                    {currentImages.map((url, idx) => (
                      <button
                        key={idx}
                        type="button"
                        className={`product-gallery-thumb ${selectedImageIndex === idx ? 'active' : ''}`}
                        onClick={() => setSelectedImageIndex(idx)}
                        aria-label={`View image ${idx + 1} of ${currentImages.length}`}
                      >
                        <img
                          src={resolveImageSrc(url)}
                          alt=""
                          onError={(e) => { e.target.src = placeholderImg; }}
                        />
                      </button>
                    ))}
                  </div>
                )}
                {/* Main image + scroll controls – fixed frame; image uses object-fit */}
                <div className="product-gallery-main">
                  {currentImages.length > 0 ? (
                    <>
                      <img
                        src={resolveImageSrc(currentImages[selectedImageIndex])}
                        alt={product.name}
                        onError={(e) => {
                          e.target.src = placeholderImg;
                        }}
                      />
                      {currentImages.length > 1 && (
                        <>
                          <button
                            type="button"
                            className="product-gallery-btn product-gallery-btn-prev"
                            onClick={goPrevImage}
                            aria-label="Previous image"
                          >
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M15 18l-6-6 6-6" /></svg>
                          </button>
                          <button
                            type="button"
                            className="product-gallery-btn product-gallery-btn-next"
                            onClick={goNextImage}
                            aria-label="Next image"
                          >
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 18l6-6-6-6" /></svg>
                          </button>
                        </>
                      )}
                    </>
                  ) : (
                    <img
                      src={placeholderImg}
                      alt={product.name}
                    />
                  )}
                </div>
              </div>
            </div>
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
            
            {/* Color – always show row; use selector or fallback so layout stays consistent */}
            <div className="product-info-attribute-row product-info-attribute-row--color">
              <span className="attribute-label">Color</span>
              {product.available_colors && product.available_colors.length > 1 ? (
                <ColorSwatches
                  colors={product.available_colors}
                  selectedColor={selectedColor}
                  onColorSelect={handleColorSelect}
                  variationAvailability={product.variation_availability}
                  selectedSize={selectedSize}
                />
              ) : (
                <span className="product-info-attribute-fallback">
                  {colors.length > 0 ? (selectedColor || colors[0] || product.color || 'One Color') : 'One Color'}
                </span>
              )}
            </div>

            {/* Size – always show row; use selector or fallback so layout stays consistent */}
            <div className="product-info-attribute-row product-info-attribute-row--size">
              <span className="attribute-label">Size</span>
              {product.available_sizes && product.available_sizes.length > 1 ? (
                <SizeSelector
                  sizes={product.available_sizes}
                  selectedSize={selectedSize}
                  onSizeSelect={handleSizeSelect}
                  stockBySize={product.size_stock || product.stock_by_size || {}}
                  variationAvailability={product.variation_availability}
                  selectedColor={selectedColor}
                />
              ) : (
                <span className="product-info-attribute-fallback">
                  {sizes.length > 0 ? (selectedSize || sizes[0] || product.size || 'Fixed Size') : 'Fixed Size'}
                </span>
              )}
            </div>

            <div className="product-stock">
              {hasVariations ? (
                variationLoading && (selectedColor || selectedSize) ? (
                  <span className="stock-loading">Checking availability…</span>
                ) : variation != null ? (
                  variation.stock_quantity > 0 ? (
                    <span className="in-stock">In Stock ({variation.stock_quantity} available)</span>
                  ) : (
                    <span className="out-of-stock">Out of Stock</span>
                  )
                ) : (selectedColor && selectedSize) ? (
                  <span className="out-of-stock">Out of Stock</span>
                ) : (
                  <span className="stock-select">Select size and color to see availability</span>
                )
              ) : (
                product.stock_quantity != null ? (
                  product.stock_quantity > 0 ? (
                    <span className="in-stock">In Stock ({product.stock_quantity} available)</span>
                  ) : (
                    <span className="out-of-stock">Out of Stock</span>
                  )
                ) : null
              )}
            </div>

            <div className="product-actions product-actions--wrap">
              <div className="quantity-selector">
                <label>Quantity:</label>
                <input
                  type="number"
                  min="1"
                  max={hasVariations ? (variation?.stock_quantity ?? 99) : (product.stock_quantity ?? 99)}
                  value={quantity}
                  onChange={(e) => {
                    const maxQ = hasVariations ? (variation?.stock_quantity ?? 99) : (product.stock_quantity ?? 99);
                    const raw = parseInt(e.target.value, 10);
                    const clamped = Math.min(maxQ || 1, Math.max(1, Number.isNaN(raw) ? 1 : raw));
                    setQuantity(clamped);
                  }}
                  className="quantity-input"
                />
              </div>

              <button
                onClick={handleAddToCart}
                disabled={hasVariations ? (variation == null || variation.stock_quantity === 0) : (product.stock_quantity != null && product.stock_quantity < 1)}
                className="btn btn-primary btn-add-cart-large"
              >
                Add to Cart
              </button>
            </div>

            {/* Description – inside right column; desktop: 2-line clamp + Read more; mobile: full text */}
            <div className="product-description product-description--in-info">
              <h3>Description</h3>
              <div
                className={`product-description-content ${descriptionExpanded ? 'product-description-content--expanded' : 'product-description-content--collapsed'}`}
              >
                {product.description ? (
                  <p>{product.description}</p>
                ) : (
                  <p className="product-description-empty">No extra description for this product.</p>
                )}
              </div>
              {product.description && (
                <button
                  type="button"
                  className="product-description-read-more"
                  onClick={() => setDescriptionExpanded((e) => !e)}
                  aria-expanded={descriptionExpanded}
                >
                  {descriptionExpanded ? 'Show less' : 'Read more'}
                </button>
              )}
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

