import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useCart } from '../contexts/CartContext';
import { useNotification } from '../contexts/NotificationContext';
import ProductRating from '../components/ProductRating';
import ColorSwatches from '../components/ColorSwatches';
import SizeSelector from '../components/SizeSelector';
import './ProductDetail.css';

const ProductDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { addToCart } = useCart();
  const { showSuccess, showError } = useNotification();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const [selectedColor, setSelectedColor] = useState(null);
  const [selectedSize, setSelectedSize] = useState(null);

  useEffect(() => {
    fetchProduct();
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

            <div className="product-price">${product.price.toFixed(2)}</div>
            
            {/* Color Selection */}
            {product.available_colors && product.available_colors.length > 0 && (
              <ColorSwatches 
                colors={product.available_colors} 
                selectedColor={selectedColor}
                onColorSelect={setSelectedColor}
              />
            )}
            
            {/* Size Selection */}
            {product.available_sizes && product.available_sizes.length > 0 && (
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
                  onChange={(e) => setQuantity(parseInt(e.target.value) || 1)}
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
      </div>
    </div>
  );
};

export default ProductDetail;

