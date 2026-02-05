import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useCart } from '../contexts/CartContext';
import { useAuth } from '../contexts/AuthContext';
import { useNotification } from '../contexts/NotificationContext';
import SizeSelector from '../components/SizeSelector';
import ColorSwatches from '../components/ColorSwatches';
import ProductCard from '../components/ProductCard';
import ConfirmationDialog from '../components/ConfirmationDialog';
import axios from 'axios';
import './Cart.css';

const isItemUnavailable = (item) => {
  const stock = item.product?.stock_quantity;
  if (stock === undefined || stock === null) return false;
  return stock < 1 || item.quantity > stock;
};

const isItemLowStock = (item) => {
  const raw = item.product?.stock_quantity;
  if (raw === undefined || raw === null) return false;
  const stock = Number(raw);
  return !Number.isNaN(stock) && stock >= 1 && stock <= 5;
};

const Cart = () => {
  const { cartItems, cartTotal, updateCartItem, removeFromCart } = useCart();
  const { isAuthenticated } = useAuth();
  const { showSuccess, showError, showWarning } = useNotification();
  const navigate = useNavigate();
  const [suggestedProducts, setSuggestedProducts] = useState([]);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [matchingPairs, setMatchingPairs] = useState([]);
  const [loadingMatchingPairs, setLoadingMatchingPairs] = useState(false);
  const [confirmationState, setConfirmationState] = useState(null); // { itemId, itemName }
  const notifiedUnavailableRef = useRef(false);

  // Notify user when returning to cart if any items are no longer available
  const unavailableItems = cartItems.filter(isItemUnavailable);
  useEffect(() => {
    if (unavailableItems.length > 0 && !notifiedUnavailableRef.current) {
      showWarning(
        unavailableItems.length === 1
          ? 'One item in your cart is no longer available. Please remove it or update the quantity.'
          : `${unavailableItems.length} items in your cart are no longer available. Please remove them or update the quantity.`,
        6000
      );
      notifiedUnavailableRef.current = true;
    }
    if (unavailableItems.length === 0) {
      notifiedUnavailableRef.current = false;
    }
  }, [unavailableItems.length, showWarning]);

  // Fetch suggested products based on cart items using related products from database
  // IMPORTANT: This hook must be called before any early returns
  useEffect(() => {
    const fetchSuggestions = async () => {
      if (cartItems.length === 0) {
        setSuggestedProducts([]);
        return;
      }

      try {
        setLoadingSuggestions(true);
        
        // Fetch related products from database based on product relations
        const response = await axios.get('/api/cart/suggestions');
        const relatedProducts = response.data.products || [];
        
        // Exclude products already in cart
        const cartProductIds = cartItems.map(item => item.product_id || item.product?.id).filter(Boolean);
        const filtered = relatedProducts.filter(p => !cartProductIds.includes(p.id));
        
        // If we have related products, use them; otherwise fallback to category/color-based
        if (filtered.length > 0) {
          setSuggestedProducts(filtered.slice(0, 8));
        } else {
          // Fallback: Get categories and colors from cart items
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

          // Fetch all products and filter out cart items
          const fallbackResponse = await axios.get(`/api/products?${params.toString()}`);
          const allProducts = fallbackResponse.data.products || [];
          const fallbackFiltered = allProducts.filter(p => !cartProductIds.includes(p.id));
          setSuggestedProducts(fallbackFiltered.slice(0, 8));
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

  // Fetch AI-powered matching pairs (items that go well with cart items)
  useEffect(() => {
    const fetchMatchingPairs = async () => {
      if (cartItems.length === 0) {
        setMatchingPairs([]);
        return;
      }
      try {
        setLoadingMatchingPairs(true);
        const response = await axios.get('/api/cart/matching-pairs');
        const matches = response.data.matches || [];
        const cartProductIds = cartItems.map(item => item.product_id || item.product?.id).filter(Boolean);
        const filtered = matches.filter(m => m.product && !cartProductIds.includes(m.product.id));
        setMatchingPairs(filtered.slice(0, 8));
      } catch (error) {
        console.error('Error fetching matching pairs:', error);
        setMatchingPairs([]);
      } finally {
        setLoadingMatchingPairs(false);
      }
    };
    fetchMatchingPairs();
  }, [cartItems]);

  const handleQuantityChange = async (itemId, newQuantity) => {
    const item = cartItems.find(i => i.id === itemId);
    if (newQuantity < 1) {
      if (item) {
        await removeFromCart(itemId, item.selected_color, item.selected_size);
      } else {
        await removeFromCart(itemId);
      }
    } else {
      const updatePayload = item
        ? [itemId, newQuantity, item.selected_color, item.selected_size, item.selected_color, item.selected_size]
        : [itemId, newQuantity];
      const result = await updateCartItem(...updatePayload);
      if (!result.success) {
        showError(result.error || 'Failed to update quantity');
      }
    }
  };

  const handleSizeChange = async (itemId, newSize) => {
    const item = cartItems.find(i => i.id === itemId);
    if (item) {
      // Pass old size in the request so backend can find the correct item
      const result = await updateCartItem(
        itemId, 
        item.quantity, 
        item.selected_color, 
        newSize,
        item.selected_color,  // old color (same)
        item.selected_size     // old size (to find the item)
      );
      if (!result.success) {
        showError(result.error || 'Failed to update size');
      } else {
        showSuccess('Size updated');
      }
    }
  };

  const handleColorChange = async (itemId, newColor) => {
    const item = cartItems.find(i => i.id === itemId);
    if (item) {
      // Pass old color in the request so backend can find the correct item
      const result = await updateCartItem(
        itemId, 
        item.quantity, 
        newColor, 
        item.selected_size,
        item.selected_color,  // old color (to find the item)
        item.selected_size    // old size (same)
      );
      if (!result.success) {
        showError(result.error || 'Failed to update color');
      } else {
        showSuccess('Color updated');
      }
    }
  };

  const handleRemoveClick = (itemId) => {
    const item = cartItems.find(i => i.id === itemId);
    if (item) {
      const itemName = item.product?.name || 'this item';
      setConfirmationState({ itemId, itemName, selectedColor: item.selected_color, selectedSize: item.selected_size });
    }
  };

  const handleConfirmRemove = async () => {
    if (!confirmationState) return;
    
    const { itemId, selectedColor, selectedSize } = confirmationState;
    setConfirmationState(null);
    
    try {
      const result = await removeFromCart(itemId, selectedColor, selectedSize);
      if (result.success) {
        showSuccess('Item removed from cart');
      } else {
        showError(result.error || 'Failed to remove item from cart');
      }
    } catch (error) {
      showError('Failed to remove item from cart');
    }
  };

  const handleCancelRemove = () => {
    setConfirmationState(null);
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
      {confirmationState && (
        <ConfirmationDialog
          message={`Are you sure you want to remove "${confirmationState.itemName}" from your cart?`}
          onConfirm={handleConfirmRemove}
          onCancel={handleCancelRemove}
          confirmText="Remove"
          cancelText="Cancel"
        />
      )}
      <div className="container">
        <h1 className="page-title">Shopping Cart</h1>

        <div className="cart-layout">
          <div className="cart-items">
            {cartItems.map(item => (
              <div key={item.id} className={`cart-item ${isItemUnavailable(item) ? 'cart-item-unavailable' : ''}`}>
                {isItemUnavailable(item) && (
                  <div className="cart-item-unavailable-banner" role="alert">
                    This item is no longer available. Please remove it or reduce the quantity.
                  </div>
                )}
                {isItemLowStock(item) && (
                  <div className="cart-item-low-stock-message" role="status">
                    Only {Number(item.product?.stock_quantity)} left in stock. Make sure to finalize your purchase soon before the item is sold out.
                  </div>
                )}
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
                  <div className="cart-item-price">
                    {item.product?.on_sale ? (
                      <>
                        <span className="original-price">${item.product?.original_price?.toFixed(2)}</span>
                        <span className="sale-price">${item.product?.price.toFixed(2)}</span>
                        {item.product?.discount_percentage && (
                          <span className="discount-badge">-{item.product.discount_percentage.toFixed(0)}%</span>
                        )}
                      </>
                    ) : (
                      <span>${item.product?.price.toFixed(2)}</span>
                    )}
                  </div>
                </div>
                <div className="cart-item-actions">
                  <div className="quantity-controls">
                    <button onClick={() => handleQuantityChange(item.id, item.quantity - 1)}>-</button>
                    <span>{item.quantity}</span>
                    <button
                      onClick={() => handleQuantityChange(item.id, item.quantity + 1)}
                      disabled={typeof item.product?.stock_quantity === 'number' && item.quantity >= item.product.stock_quantity}
                      title={typeof item.product?.stock_quantity === 'number' && item.quantity >= item.product.stock_quantity ? 'Maximum available in stock' : 'Increase quantity'}
                    >
                      +
                    </button>
                  </div>
                  <div className="cart-item-subtotal">
                    {item.product?.on_sale ? (
                      <>
                        <span className="original-subtotal">${(item.product?.original_price * item.quantity).toFixed(2)}</span>
                        <span className="discounted-subtotal">${item.subtotal.toFixed(2)}</span>
                      </>
                    ) : (
                      <span>${item.subtotal.toFixed(2)}</span>
                    )}
                  </div>
                  <button onClick={() => handleRemoveClick(item.id)} className="btn-remove">Remove</button>
                </div>
              </div>
            ))}
          </div>

          <div className="cart-summary">
            <h3>Order Summary</h3>
            {(() => {
              // Calculate original subtotal and savings
              const originalSubtotal = cartItems.reduce((sum, item) => {
                const originalPrice = item.product?.original_price || item.product?.price || 0;
                return sum + (originalPrice * item.quantity);
              }, 0);
              const totalSavings = originalSubtotal - cartTotal;
              const hasDiscounts = totalSavings > 0;

              return (
                <>
                  {hasDiscounts && (
                    <>
                      <div className="summary-row">
                        <span>Original Subtotal:</span>
                        <span className="original-price">${originalSubtotal.toFixed(2)}</span>
                      </div>
                      <div className="summary-row savings">
                        <span>You Save:</span>
                        <span className="savings-amount">-${totalSavings.toFixed(2)}</span>
                      </div>
                    </>
                  )}
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
                </>
              );
            })()}
            <Link to="/checkout" className="btn btn-primary btn-checkout">
              Proceed to Checkout
            </Link>
          </div>
        </div>

        {/* Matching Pairs - AI-powered recommendations that go well with cart items */}
        <div className="cart-matching-pairs">
          <h2 className="section-title">Matching Pairs</h2>
          <p className="section-subtitle">Items that go well with what you have in your cart</p>
          {loadingMatchingPairs ? (
            <div className="spinner"></div>
          ) : matchingPairs.length > 0 ? (
            <div className="suggestions-grid matching-pairs-grid">
              {matchingPairs.map(({ product, reason }) => (
                <div key={product.id} className="matching-pair-card">
                  <ProductCard product={product} />
                  <p className="matching-pair-reason">{reason}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="matching-pairs-empty">No matching recommendations right now. Keep shopping — we'll suggest pairs as our catalog grows.</p>
          )}
        </div>

        {/* You Might Also Like */}
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

