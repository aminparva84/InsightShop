import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from './AuthContext';

const WishlistContext = createContext();

export const useWishlist = () => {
  const context = useContext(WishlistContext);
  if (!context) {
    throw new Error('useWishlist must be used within a WishlistProvider');
  }
  return context;
};

export const WishlistProvider = ({ children }) => {
  const { isAuthenticated, token } = useAuth();
  const [productIds, setProductIds] = useState(new Set());
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchWishlistIds = useCallback(async () => {
    if (!token || !isAuthenticated) {
      setProductIds(new Set());
      setItems([]);
      return;
    }
    try {
      const res = await axios.get('/api/wishlist/ids');
      setProductIds(new Set(res.data.product_ids || []));
    } catch (err) {
      setProductIds(new Set());
    }
  }, [token, isAuthenticated]);

  const fetchWishlist = useCallback(async () => {
    if (!token || !isAuthenticated) {
      setItems([]);
      setProductIds(new Set());
      return;
    }
    setLoading(true);
    try {
      const res = await axios.get('/api/wishlist?notifications=true');
      const list = res.data.items || [];
      setItems(list);
      setProductIds(new Set(list.map((i) => i.product_id)));
    } catch (err) {
      setItems([]);
      setProductIds(new Set());
    } finally {
      setLoading(false);
    }
  }, [token, isAuthenticated]);

  useEffect(() => {
    fetchWishlistIds();
  }, [fetchWishlistIds]);

  const isInWishlist = useCallback(
    (productId) => productIds.has(Number(productId)),
    [productIds]
  );

  const addToWishlist = useCallback(
    async (productId) => {
      if (!token || !isAuthenticated) return { success: false, error: 'Please log in to save items to your wishlist.' };
      try {
        await axios.post('/api/wishlist', { product_id: productId });
        setProductIds((prev) => new Set([...prev, Number(productId)]));
        await fetchWishlistIds();
        return { success: true };
      } catch (err) {
        const msg = err.response?.data?.error || 'Failed to add to wishlist';
        return { success: false, error: msg };
      }
    },
    [token, isAuthenticated, fetchWishlistIds]
  );

  const removeFromWishlist = useCallback(
    async (productId) => {
      if (!token || !isAuthenticated) return { success: false, error: 'Not logged in' };
      try {
        await axios.delete(`/api/wishlist/${productId}`);
        setProductIds((prev) => {
          const next = new Set(prev);
          next.delete(Number(productId));
          return next;
        });
        setItems((prev) => prev.filter((i) => i.product_id !== Number(productId)));
        return { success: true };
      } catch (err) {
        const msg = err.response?.data?.error || 'Failed to remove from wishlist';
        return { success: false, error: msg };
      }
    },
    [token, isAuthenticated]
  );

  const toggleWishlist = useCallback(
    async (productId) => {
      const id = Number(productId);
      if (productIds.has(id)) {
        return removeFromWishlist(id);
      }
      return addToWishlist(id);
    },
    [productIds, addToWishlist, removeFromWishlist]
  );

  const value = {
    productIds,
    items,
    loading,
    wishlistCount: productIds.size,
    isInWishlist,
    addToWishlist,
    removeFromWishlist,
    toggleWishlist,
    fetchWishlist,
    fetchWishlistIds,
  };

  return <WishlistContext.Provider value={value}>{children}</WishlistContext.Provider>;
};
