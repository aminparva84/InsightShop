import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { FaUserTie, FaCloudRain, FaSocks, FaShoePrints } from 'react-icons/fa';
import {
  GiTrousers,
  GiShirt,
  GiTShirt,
  GiMonclerJacket,
  GiDress,
  GiAmpleDress,
  GiSkirt,
  GiShorts,
  GiWool,
  GiHoodie,
  GiSandal,
  GiRunningShoe,
  GiNightSleep,
  GiUnderwear,
} from 'react-icons/gi';
import { useNotification } from '../contexts/NotificationContext';
import { useAuth } from '../contexts/AuthContext';
import { useWishlist } from '../contexts/WishlistContext';
import ProductRating from './ProductRating';
import AddToCartModal from './AddToCartModal';
import { getColorHex } from '../utils/colorMap';
import './ProductCard.css';

const HeartOutline = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
  </svg>
);
const HeartFilled = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
    <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
  </svg>
);

/* Same icons as Navbar clothing categories – id → Icon component */
const CLOTHING_CATEGORY_ICONS = {
  shirts: GiShirt,
  t_shirts: GiTShirt,
  pants: GiTrousers,
  jackets: GiMonclerJacket,
  coats: FaCloudRain,
  dresses: GiDress,
  skirts: GiSkirt,
  shorts: GiShorts,
  sweaters: GiWool,
  hoodies: GiHoodie,
  socks: FaSocks,
  shoes: FaShoePrints,
  sandals: GiSandal,
  sneakers: GiRunningShoe,
  pajamas: GiNightSleep,
  blouses: GiAmpleDress,
  underwear: GiUnderwear,
  suits: FaUserTie,
};

const ProductCard = ({ product, compact = false, showCompareCheckbox = false, selectedForCompare = false, onToggleCompare }) => {
  const { showSuccess, showError } = useNotification();
  const { isAuthenticated } = useAuth();
  const { isInWishlist, toggleWishlist } = useWishlist();
  const [addToCartModalOpen, setAddToCartModalOpen] = useState(false);

  const outOfStock = typeof product.stock_quantity === 'number' && product.stock_quantity <= 0;
  const inWishlist = isInWishlist(product.id);

  const handleAddToCart = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (outOfStock) return;
    setAddToCartModalOpen(true);
  };

  const handleWishlistClick = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isAuthenticated) {
      showError('Please log in to save items to your wishlist.');
      return;
    }
    const result = await toggleWishlist(product.id);
    if (result.success) {
      showSuccess(inWishlist ? 'Removed from wishlist' : 'Added to wishlist');
    } else if (result.error) {
      showError(result.error);
    }
  };

  const baseUrl = process.env.PUBLIC_URL || '';
  const rawSrc = product.image_url || 'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400&h=400&fit=crop&q=80';
  const imageSrc = rawSrc.startsWith('/') ? baseUrl + rawSrc : rawSrc;

  const handleCompareClick = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  return (
    <>
      <div className={`product-card ${compact ? 'compact' : ''} ${product.on_sale ? 'product-card--on-sale' : ''}`}>
        <Link to={`/products/${product.id}`} className="product-card-link" aria-label={`View ${product.name}`}>
          {showCompareCheckbox && (
        <div className="compare-checkbox-wrapper" title="Compare" onClick={handleCompareClick} role="presentation">
          <label className="compare-checkbox">
            <input
              type="checkbox"
              checked={selectedForCompare}
              onChange={() => onToggleCompare && onToggleCompare(product.id)}
              onClick={(e) => e.stopPropagation()}
              aria-label={`Compare ${product.name}`}
            />
            <span>Compare</span>
          </label>
        </div>
      )}
      {product.on_sale && product.discount_percentage != null && (
        <span className="product-card-sale-badge">-{Number(product.discount_percentage).toFixed(0)}%</span>
      )}
      <div className="product-image">
        <div className="product-image-inner">
          <img 
            src={imageSrc} 
            alt={product.name}
            onError={(e) => {
              e.target.src = 'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400&h=400&fit=crop&q=80';
            }}
          />
        </div>
      </div>
      <div className="product-info">
        <div className="product-info-row">
          <h3 className="product-name">{product.name}</h3>
          <div className="product-price">
            {product.on_sale ? (
              <>
                <span className="sale-price">${product.price.toFixed(2)}</span>
                <span className="original-price">${product.original_price.toFixed(2)}</span>
              </>
            ) : (
              <span>${product.price.toFixed(2)}</span>
            )}
          </div>
        </div>
        <ProductRating rating={product.rating || 0} reviewCount={product.review_count || 0} />
        <div className="product-meta">
          {product.category && (
            <span className="product-category">{product.category}</span>
          )}
          {product.clothing_category && product.clothing_category !== 'other' && CLOTHING_CATEGORY_ICONS[product.clothing_category] && (
            <span
              className="product-meta-clothing-icon"
              title={(product.clothing_category || '').replace(/_/g, ' ')}
              aria-label={`Clothing: ${(product.clothing_category || '').replace(/_/g, ' ')}`}
            >
              {React.createElement(CLOTHING_CATEGORY_ICONS[product.clothing_category], { 'aria-hidden': true })}
            </span>
          )}
          {product.available_colors && product.available_colors.length > 0 && (
            <span className="product-meta-colors" aria-label="Available colors">
              {product.available_colors.map((color, idx) => (
                <span
                  key={idx}
                  className="product-meta-color-swatch"
                  style={{ backgroundColor: getColorHex(color) }}
                  title={color}
                />
              ))}
            </span>
          )}
        </div>
      </div>
        </Link>
      <div className="product-card-actions">
        <button
          type="button"
          className={`product-card-wishlist-btn ${inWishlist ? 'product-card-wishlist-btn--active' : ''}`}
          onClick={handleWishlistClick}
          aria-label={inWishlist ? `Remove ${product.name} from wishlist` : `Add ${product.name} to wishlist`}
          title={inWishlist ? 'Remove from wishlist' : 'Add to wishlist'}
        >
          {inWishlist ? <HeartFilled /> : <HeartOutline />}
        </button>
        <button
          type="button"
          onClick={handleAddToCart}
          className="btn-add-cart"
          disabled={outOfStock}
          aria-disabled={outOfStock}
          aria-label={outOfStock ? `${product.name} is out of stock` : `Add ${product.name} to cart`}
        >
          <span className="btn-add-cart-text btn-add-cart-text-desktop">Add to cart</span>
          <span className="btn-add-cart-text btn-add-cart-text-mobile" aria-hidden="true">Add</span>
          <span className="btn-add-cart-icon" aria-hidden="true">+</span>
        </button>
      </div>
      </div>
    <AddToCartModal
      productId={product.id}
      isOpen={addToCartModalOpen}
      onClose={() => setAddToCartModalOpen(false)}
      initialProduct={product}
    />
    </>
  );
};

export default ProductCard;

