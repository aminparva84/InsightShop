import React from 'react';
import './ProductRating.css';

const ProductRating = ({ rating = 0, reviewCount = 0, showCount = true }) => {
  const fullStars = Math.floor(rating);
  const hasHalfStar = rating % 1 >= 0.5;
  const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);

  return (
    <div className="product-rating">
      <div className="stars">
        {[...Array(fullStars)].map((_, i) => (
          <span key={i} className="star full">★</span>
        ))}
        {hasHalfStar && <span className="star half">★</span>}
        {[...Array(emptyStars)].map((_, i) => (
          <span key={i} className="star empty">★</span>
        ))}
      </div>
      {showCount && reviewCount > 0 && (
        <span className="review-count">({reviewCount})</span>
      )}
      {rating > 0 && (
        <span className="rating-value">{rating.toFixed(1)}</span>
      )}
    </div>
  );
};

export default ProductRating;

