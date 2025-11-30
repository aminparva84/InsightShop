import React from 'react';
import './SizeSelector.css';

const SizeSelector = ({ sizes = [], selectedSize, onSizeSelect, stockBySize = {} }) => {
  if (!sizes || sizes.length === 0) {
    return null;
  }

  return (
    <div className="size-selector">
      <label className="size-label">Size:</label>
      <div className="size-options">
        {sizes.map((size, index) => {
          const isOutOfStock = stockBySize[size] === 0 || stockBySize[size] === undefined;
          return (
            <button
              key={index}
              className={`size-option ${selectedSize === size ? 'selected' : ''} ${isOutOfStock ? 'out-of-stock' : ''}`}
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                if (!isOutOfStock && onSizeSelect) {
                  onSizeSelect(size);
                }
              }}
              disabled={isOutOfStock}
              title={isOutOfStock ? 'Out of stock' : `Select size ${size}`}
            >
              {size}
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default SizeSelector;

