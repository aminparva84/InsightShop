import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useCart } from '../contexts/CartContext';
import { useNotification } from '../contexts/NotificationContext';
import ProductRating from './ProductRating';
import './ProductCard.css';

const COLOR_MAP = {
  black: '#000000', white: '#FFFFFF', red: '#FF0000', blue: '#0000FF', green: '#008000',
  yellow: '#FFFF00', gray: '#808080', grey: '#808080', pink: '#FFC0CB', purple: '#800080',
  orange: '#FFA500', brown: '#A52A2A', navy: '#000080', beige: '#F5F5DC', maroon: '#800000',
  teal: '#008080', burgundy: '#800020', olive: '#808000', sage: '#9DC183', cream: '#FFFDD0',
  tan: '#D2B48C', mustard: '#FFDB58', gold: '#FFD700', silver: '#C0C0C0', charcoal: '#36454F',
  'forest green': '#228B22', 'sky blue': '#87CEEB', 'light blue': '#ADD8E6', sienna: '#A0522D',
  rust: '#B7410E', 'dark green': '#006400', 'dark blue': '#00008B'
};

const getColorHex = (colorName) => {
  if (!colorName) return '#CCCCCC';
  const key = String(colorName).toLowerCase().trim();
  return COLOR_MAP[key] || '#CCCCCC';
};

const ProductCard = ({ product, compact = false }) => {
  const { addToCart } = useCart();
  const { showSuccess, showError } = useNotification();
  const [selectedColor] = useState(product.available_colors?.[0] || product.color || null);
  const [selectedSize] = useState(product.available_sizes?.[0] || product.size || null);

  const handleAddToCart = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    // Guest shopping enabled - no login required
    const result = await addToCart(product.id, 1, selectedColor, selectedSize);
    if (result.success) {
      showSuccess('Added to cart!');
      const stock = product?.stock_quantity;
      const remaining = typeof result.remaining_stock === 'number' ? result.remaining_stock : (typeof stock === 'number' ? Math.max(0, stock - 1) : null);
      const lowStockCount = typeof remaining === 'number' ? remaining : (typeof stock === 'number' && stock >= 1 && stock <= 5 ? stock : null);
      if (lowStockCount !== null && lowStockCount >= 1 && lowStockCount <= 5) {
        const message = `Only ${lowStockCount} left in stock. Make sure to finalize your purchase soon before the item is sold out.`;
        setTimeout(() => showSuccess(message, 6000), 100);
      }
    } else {
      showError(result.error || 'Failed to add to cart');
    }
  };

  const baseUrl = process.env.PUBLIC_URL || '';
  const rawSrc = product.image_url || 'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400&h=400&fit=crop&q=80';
  const imageSrc = rawSrc.startsWith('/') ? baseUrl + rawSrc : rawSrc;

  return (
    <Link to={`/products/${product.id}`} className={`product-card ${compact ? 'compact' : ''} ${product.on_sale ? 'product-card--on-sale' : ''}`}>
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
                <span className="original-price">${product.original_price.toFixed(2)}</span>
                <span className="sale-price">${product.price.toFixed(2)}</span>
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
      <button type="button" onClick={handleAddToCart} className="btn-add-cart">
        <span className="btn-add-cart-text btn-add-cart-text-desktop">Add to cart</span>
        <span className="btn-add-cart-text btn-add-cart-text-mobile" aria-hidden="true">Add</span>
        <span className="btn-add-cart-icon" aria-hidden="true">+</span>
      </button>
    </Link>
  );
};

export default ProductCard;

