import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useWishlist } from '../contexts/WishlistContext';
import ProductCard from '../components/ProductCard';
import './Wishlist.css';

const HeartFilled = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
    <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
  </svg>
);

const Wishlist = () => {
  const { items, loading, fetchWishlist } = useWishlist();

  useEffect(() => {
    fetchWishlist();
  }, [fetchWishlist]);

  if (loading) {
    return <div className="wishlist-page"><div className="spinner" /></div>;
  }

  return (
    <div className="wishlist-page">
      <div className="container">
        <h1 className="page-title">My Wishlist</h1>
        <p className="wishlist-subtitle">
          Items you've saved for later. You'll be notified about price drops and when items are back in stock.
        </p>

        {items.length === 0 ? (
          <div className="wishlist-empty">
            <span className="wishlist-empty-icon" aria-hidden="true"><HeartFilled /></span>
            <h2>Your wishlist is empty</h2>
            <p>Save items you like by clicking the heart on product cards or product pages.</p>
            <Link to="/products" className="btn btn-primary">Browse Products</Link>
          </div>
        ) : (
          <div className="wishlist-grid">
            {items.map((entry) => {
              const product = entry.product;
              if (!product) return null;
              const notifications = entry.notifications || {};
              return (
                <div key={entry.id} className="wishlist-card-wrapper">
                  <div className="wishlist-card-badges">
                    {notifications.price_dropped && (
                      <span className="wishlist-badge wishlist-badge--price">Price drop</span>
                    )}
                    {notifications.back_in_stock && (
                      <span className="wishlist-badge wishlist-badge--stock">Back in stock</span>
                    )}
                  </div>
                  <ProductCard product={product} />
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default Wishlist;
