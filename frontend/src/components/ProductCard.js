import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useCart } from '../contexts/CartContext';
import { useNotification } from '../contexts/NotificationContext';
import ProductRating from './ProductRating';
import ColorSwatches from './ColorSwatches';
import SizeSelector from './SizeSelector';
import './ProductCard.css';

const ProductCard = ({ product, compact = false }) => {
  const { addToCart } = useCart();
  const { showSuccess, showError } = useNotification();
  const [selectedColor, setSelectedColor] = useState(product.available_colors?.[0] || product.color || null);
  const [selectedSize, setSelectedSize] = useState(product.available_sizes?.[0] || product.size || null);
  
  // Debug: Log sizes for troubleshooting (only in development)
  useEffect(() => {
    if (product.available_sizes && process.env.NODE_ENV === 'development') {
      console.log(`Product ${product.id} (${product.name}): available_sizes =`, product.available_sizes, 'length:', product.available_sizes.length);
    }
  }, [product.id, product.available_sizes]);

  const handleAddToCart = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    // Guest shopping enabled - no login required
    const result = await addToCart(product.id, 1, selectedColor, selectedSize);
    if (result.success) {
      showSuccess('Added to cart!');
    } else {
      showError(result.error || 'Failed to add to cart');
    }
  };

  return (
    <Link to={`/products/${product.id}`} className={`product-card ${compact ? 'compact' : ''}`}>
      <div className="product-image">
        <img 
          src={product.image_url || `https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400&h=400&fit=crop&q=80`} 
          alt={product.name}
          onError={(e) => {
            e.target.src = `https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400&h=400&fit=crop&q=80`;
          }}
        />
        <div className="product-overlay">
          <button onClick={handleAddToCart} className="btn-add-cart">
            Add to Cart
          </button>
        </div>
      </div>
      <div className="product-info">
        <h3 className="product-name">{product.name}</h3>
        <ProductRating rating={product.rating || 0} reviewCount={product.review_count || 0} />
        <div className="product-meta">
          <span className="product-category">{product.category}</span>
        </div>
        {product.available_colors && product.available_colors.length > 0 && (
          <ColorSwatches 
            colors={product.available_colors} 
            selectedColor={selectedColor}
            onColorSelect={(color) => {
              setSelectedColor(color);
            }}
          />
        )}
        {product.available_sizes && product.available_sizes.length > 0 && (
          <SizeSelector 
            sizes={product.available_sizes} 
            selectedSize={selectedSize}
            onSizeSelect={(size) => {
              setSelectedSize(size);
            }}
          />
        )}
        <div className="product-price">${product.price.toFixed(2)}</div>
      </div>
    </Link>
  );
};

export default ProductCard;

