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

/* Cart icon – same bag shape as Navbar */
const CartIcon = () => (
  <svg width="22" height="22" viewBox="0 0 70 56" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" preserveAspectRatio="xMidYMid meet">
    <path
      d="M 0 0 C 2.31 0.33 4.62 0.66 7 1 C 9 6.75 9 6.75 9 9 C 10.0339 8.99214 10.0339 8.99214 11.0886 8.98413 C 36.3766 8.81728 36.3766 8.81728 47 10 C 47.495 11.485 47.495 11.485 48 13 C 50.0002 14.2088 50.0002 14.2088 52 15 C 51.67 15.66 51.34 16.32 51 17 C 49.35 17 47.7 17 46 17 C 45.67 18.98 45.34 20.96 45 23 C 45.9075 23.2681 46.815 23.5362 47.75 23.8125 C 50.7299 24.9013 52.6859 25.8639 55 28 C 55 28.66 55 29.32 55 30 C 51.1937 29.3283 47.6479 28.2725 44 27 C 42.7637 30.2452 42 32.7551 42 36.25 C 42 37.1575 42 38.065 42 39 C 40 41 40 41 37 41.25 C 34 41 34 41 32 39 C 31.875 35.375 31.875 35.375 32 32 C 28.535 32.495 28.535 32.495 25 33 C 25.0413 33.9487 25.0825 34.8975 25.125 35.875 C 25 39 25 39 23 41 C 20.0625 41.4375 20.0625 41.4375 17 41 C 15.0625 38.75 15.0625 38.75 14 36 C 14.3125 33.6875 14.3125 33.6875 15 32 C 13.35 31.67 11.7 31.34 10 31 C 9.84443 30.1926 9.68885 29.3851 9.52856 28.5532 C 8.81255 24.9056 8.06302 21.2657 7.3125 17.625 C 7.06822 16.354 6.82395 15.083 6.57227 13.7734 C 6.31768 12.5617 6.06309 11.35 5.80078 10.1016 C 5.46301 8.42054 5.46301 8.42054 5.11841 6.70557 C 4.24319 3.77289 4.24319 3.77289 1.38745 2.61865 C 0.599592 2.4145 -0.188267 2.21034 -1 2 C -0.67 1.34 -0.34 0.68 0 0 Z M 10 12 C 10.33 13.65 10.66 15.3 11 17 C 18.3765 16.2498 25.6783 15.1656 33 14 C 33 13.67 33 13.34 33 13 C 25.3107 11.9394 17.7549 11.9007 10 12 Z M 29.4375 16.875 C 27.5174 17.1496 27.5174 17.1496 25.5586 17.4297 C 22.6868 17.8899 19.8451 18.3993 17 19 C 17 19.33 17 19.66 17 20 C 25.25 20.33 33.5 20.66 42 21 C 42.33 19.68 42.66 18.36 43 17 C 38.2079 15.9483 34.2778 16.1619 29.4375 16.875 Z M 12 25 C 12.33 26.32 12.66 27.64 13 29 C 21.58 29 30.16 29 39 29 C 39.33 27.68 39.66 26.36 40 25 C 34.8382 22.9087 30.348 22.6964 24.875 22.75 C 24.0771 22.7423 23.2791 22.7345 22.457 22.7266 C 16.9456 22.7191 16.9456 22.7191 12 25 Z"
      fill="currentColor"
      transform="translate(9,9)"
    />
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
          <span className="btn-add-cart-icon" aria-hidden="true"><CartIcon /></span>
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

