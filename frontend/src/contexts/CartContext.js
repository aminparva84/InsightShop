import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from './AuthContext';

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
      setCartItems(response.data.items || []);
      setCartTotal(response.data.total || 0);
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

  const updateCartItem = async (itemId, quantity) => {
    try {
      await axios.put(`/api/cart/${itemId}`, { quantity });
      await fetchCart();
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.error || 'Failed to update cart' };
    }
  };

  const removeFromCart = async (itemId) => {
    try {
      await axios.delete(`/api/cart/${itemId}`);
      await fetchCart();
      return { success: true };
    } catch (error) {
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

