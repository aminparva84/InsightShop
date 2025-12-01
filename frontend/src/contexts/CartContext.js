import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from './AuthContext';

// Configure axios to send cookies for session management
axios.defaults.withCredentials = true;

const CartContext = createContext();

export const useCart = () => {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
};

export const CartProvider = ({ children }) => {
  const [cartItems, setCartItems] = useState([]);
  const [cartTotal, setCartTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    // Fetch cart for both authenticated and guest users
    fetchCart();
  }, [isAuthenticated]);

  const fetchCart = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/cart');
      const items = response.data.items || [];
      const total = response.data.total || 0;
      setCartItems(items);
      setCartTotal(total);
    } catch (error) {
      // For 401 (unauthorized), treat as empty guest cart
      if (error.response?.status === 401) {
        setCartItems([]);
        setCartTotal(0);
      } else {
        console.error('Error fetching cart:', error);
      }
    } finally {
      setLoading(false);
    }
  };

  const addToCart = async (productId, quantity = 1, selectedColor = null, selectedSize = null) => {
    // Guest shopping - no authentication required
    try {
      await axios.post('/api/cart', { 
        product_id: productId, 
        quantity,
        selected_color: selectedColor,
        selected_size: selectedSize
      });
      await fetchCart();
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.error || 'Failed to add to cart' };
    }
  };

  const updateCartItem = async (itemId, quantity, selectedColor = null, selectedSize = null) => {
    try {
      const payload = { quantity };
      if (selectedColor !== null) payload.selected_color = selectedColor;
      if (selectedSize !== null) payload.selected_size = selectedSize;
      await axios.put(`/api/cart/${itemId}`, payload);
      await fetchCart();
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.error || 'Failed to update cart' };
    }
  };

  const removeFromCart = async (itemId, selectedColor = null, selectedSize = null) => {
    try {
      // For guest cart items, send color and size in request body
      // Axios DELETE requires data to be in the config object with proper headers
      const config = {
        headers: {
          'Content-Type': 'application/json'
        }
      };
      
      if (itemId.startsWith('guest_')) {
        // Always send data for guest cart items to ensure proper matching
        config.data = {};
        if (selectedColor !== null && selectedColor !== undefined) {
          config.data.selected_color = selectedColor;
        }
        if (selectedSize !== null && selectedSize !== undefined) {
          config.data.selected_size = selectedSize;
        }
      }
      
      await axios.delete(`/api/cart/${itemId}`, config);
      
      // Force refresh cart with a small delay to ensure backend session is updated
      await new Promise(resolve => setTimeout(resolve, 100));
      await fetchCart();
      
      return { success: true };
    } catch (error) {
      console.error('Error removing from cart:', error);
      // Still try to refresh cart even on error
      await fetchCart();
      return { success: false, error: error.response?.data?.error || 'Failed to remove from cart' };
    }
  };

  const clearCart = async () => {
    try {
      await axios.delete('/api/cart/clear');
      setCartItems([]);
      setCartTotal(0);
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.error || 'Failed to clear cart' };
    }
  };

  const cartCount = cartItems.reduce((sum, item) => sum + item.quantity, 0);

  const value = {
    cartItems,
    cartTotal,
    cartCount,
    loading,
    addToCart,
    updateCartItem,
    removeFromCart,
    clearCart,
    fetchCart
  };

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
};

