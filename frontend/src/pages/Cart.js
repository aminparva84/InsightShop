import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useCart } from '../contexts/CartContext';
import { useAuth } from '../contexts/AuthContext';
import SizeSelector from '../components/SizeSelector';
import ColorSwatches from '../components/ColorSwatches';
import ProductCard from '../components/ProductCard';
import axios from 'axios';
import './Cart.css';

const Cart = () => {
  const { cartItems, cartTotal, updateCartItem, removeFromCart } = useCart();
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [suggestedProducts, setSuggestedProducts] = useState([]);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);

  // Fetch suggested products based on cart items
  // IMPORTANT: This hook must be called before any early returns
  useEffect(() => {
    const fetchSuggestions = async () => {
      if (cartItems.length === 0) {
        setSuggestedProducts([]);
        return;
      }

      try {
        setLoadingSuggestions(true);
        // Get categories and colors from cart items
        const categories = [...new Set(cartItems.map(item => item.product?.category).filter(Boolean))];
        const colors = [...new Set(cartItems.map(item => item.product?.color || item.selected_color).filter(Boolean))];
        
        // Build query params
        const params = new URLSearchParams();
        if (categories.length > 0) {
          params.append('category', categories[0]); // Use first category
        }
        if (colors.length > 0) {
          params.append('color', colors[0]); // Use first color
        }
        params.append('per_page', '8');

        // Exclude products already in cart
        const cartProductIds = cartItems.map(item => item.product_id || item.product?.id).filter(Boolean);
        if (cartProductIds.length > 0) {
          // Fetch all products and filter out cart items
          const response = await axios.get(`/api/products?${params.toString()}`);
          const allProducts = response.data.products || [];
          const filtered = allProducts.filter(p => !cartProductIds.includes(p.id));
          setSuggestedProducts(filtered.slice(0, 8));
        } else {
          const response = await axios.get(`/api/products?${params.toString()}`);
          setSuggestedProducts((response.data.products || []).slice(0, 8));
        }
      } catch (error) {
        console.error('Error fetching suggestions:', error);
        setSuggestedProducts([]);
      } finally {
        setLoadingSuggestions(false);
      }
    };

    fetchSuggestions();
  }, [cartItems]);

  const handleQuantityChange = async (itemId, newQuantity) => {
    if (newQuantity < 1) {
      await removeFromCart(itemId);
    } else {
      await updateCartItem(itemId, newQuantity);
    }
  };

  const handleSizeChange = async (itemId, newSize) => {
    const item = cartItems.find(i => i.id === itemId);
    if (item) {
      await updateCartItem(itemId, item.quantity, item.selected_color, newSize);
    }
  };

  const handleColorChange = async (itemId, newColor) => {
    const item = cartItems.find(i => i.id === itemId);
    if (item) {
      await updateCartItem(itemId, item.quantity, newColor, item.selected_size);
    }
  };

  const handleRemove = async (itemId) => {
    const item = cartItems.find(i => i.id === itemId);
    if (item) {
      await removeFromCart(itemId, item.selected_color, item.selected_size);
    } else {
      await removeFromCart(itemId);
    }
  };

  // Guest shopping enabled - no login required
  if (cartItems.length === 0) {
    return (
      <div className="cart-page">
        <div className="container">
          <div className="cart-empty">
            <h2>Your cart is empty</h2>
            <Link to="/" className="btn btn-primary">Continue Shopping</Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="cart-page">
      <div className="container">
        <h1 className="page-title">Shopping Cart</h1>

        <div className="cart-layout">
          <div className="cart-items">
            {cartItems.map(item => (
              <div key={item.id} className="cart-item">
                <img
                  src={item.product?.image_url || 'https://via.placeholder.com/150x150?text=Product'}
                  alt={item.product?.name}
                  className="cart-item-image"
                  onError={(e) => {
                    e.target.src = 'https://via.placeholder.com/150x150?text=Product';
                    e.target.onerror = null; // Prevent infinite loop
                  }}
                />
                <div className="cart-item-info">
                  <h3>{item.product?.name}</h3>
                  <div className="cart-item-meta">
                    <span>{item.product?.category}</span>
                  </div>
                  <div className="cart-item-variants">
                    {item.product?.available_colors && item.product.available_colors.length > 0 && (
                      <div className="cart-variant-selector">
                        <label>Color:</label>
                        <ColorSwatches
                          colors={item.product.available_colors}
                          selectedColor={item.selected_color || item.product.available_colors[0]}
                          onColorSelect={(color) => handleColorChange(item.id, color)}
                        />
                      </div>
                    )}
                    {item.product?.available_sizes && item.product.available_sizes.length > 0 && (
                      <div className="cart-variant-selector">
                        <label>Size:</label>
                        <SizeSelector
                          sizes={item.product.available_sizes}
                          selectedSize={item.selected_size || item.product.available_sizes[0]}
                          onSizeSelect={(size) => handleSizeChange(item.id, size)}
                        />
                      </div>
                    )}
                  </div>
                  <div className="cart-item-price">${item.product?.price.toFixed(2)}</div>
                </div>
                <div className="cart-item-actions">
                  <div className="quantity-controls">
                    <button onClick={() => handleQuantityChange(item.id, item.quantity - 1)}>-</button>
                    <span>{item.quantity}</span>
                    <button onClick={() => handleQuantityChange(item.id, item.quantity + 1)}>+</button>
                  </div>
                  <div className="cart-item-subtotal">${item.subtotal.toFixed(2)}</div>
                  <button onClick={() => handleRemove(item.id)} className="btn-remove">Remove</button>
                </div>
              </div>
            ))}
          </div>

          <div className="cart-summary">
            <h3>Order Summary</h3>
            <div className="summary-row">
              <span>Subtotal:</span>
              <span>${cartTotal.toFixed(2)}</span>
            </div>
            <div className="summary-row">
              <span>Tax:</span>
              <span>${(cartTotal * 0.08).toFixed(2)}</span>
            </div>
            <div className="summary-row">
              <span>Shipping:</span>
              <span>{cartTotal >= 50 ? 'Free' : '$5.00'}</span>
            </div>
            <div className="summary-row total">
              <span>Total:</span>
              <span>${(cartTotal * 1.08 + (cartTotal >= 50 ? 0 : 5)).toFixed(2)}</span>
            </div>
            <Link to="/checkout" className="btn btn-primary btn-checkout">
              Proceed to Checkout
            </Link>
          </div>
        </div>

        {/* Suggested Products Section */}
        {suggestedProducts.length > 0 && (
          <div className="cart-suggestions">
            <h2 className="section-title">You Might Also Like</h2>
            {loadingSuggestions ? (
              <div className="spinner"></div>
            ) : (
              <div className="suggestions-grid">
                {suggestedProducts.map(product => (
                  <ProductCard key={product.id} product={product} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Cart;

