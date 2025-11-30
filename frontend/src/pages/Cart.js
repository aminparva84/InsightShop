import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useCart } from '../contexts/CartContext';
import { useAuth } from '../contexts/AuthContext';
import SizeSelector from '../components/SizeSelector';
import ColorSwatches from '../components/ColorSwatches';
import './Cart.css';

const Cart = () => {
  const { cartItems, cartTotal, updateCartItem, removeFromCart } = useCart();
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

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
                  <button onClick={() => removeFromCart(item.id)} className="btn-remove">Remove</button>
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
      </div>
    </div>
  );
};

export default Cart;

