import React from 'react';
import './SizeSelector.css';

/**
 * Compute whether a size is in stock.
 * - If variationAvailability is provided: in stock if there exists (size, selectedColor or any color) with stock_quantity > 0.
 * - Otherwise use stockBySize: in stock if stockBySize[size] > 0.
 */
function isSizeInStock(size, stockBySize, variationAvailability, selectedColor) {
  if (variationAvailability && variationAvailability.length > 0) {
    const hasStock = (s, c) => {
      const v = variationAvailability.find(
        (x) => String(x.size).trim().toLowerCase() === String(s).trim().toLowerCase() &&
               String(x.color).trim().toLowerCase() === String(c).trim().toLowerCase()
      );
      return v && Number(v.stock_quantity) > 0;
    };
    if (selectedColor) {
      return hasStock(size, selectedColor);
    }
    return variationAvailability.some(
      (v) => String(v.size).trim().toLowerCase() === String(size).trim().toLowerCase() && Number(v.stock_quantity) > 0
    );
  }
  const qty = stockBySize[size];
  return qty !== undefined && qty !== null && Number(qty) > 0;
}

const SizeSelector = ({
  sizes = [],
  selectedSize,
  onSizeSelect,
  stockBySize = {},
  variationAvailability = null,
  selectedColor = null,
}) => {
  if (!sizes || sizes.length <= 1) {
    return null;
  }

  const displaySizes = sizes;

  return (
    <div className="size-selector">
      <label className="size-label">Sizes:</label>
      <div className="size-options">
        {displaySizes.map((size, index) => {
          const inStock = isSizeInStock(size, stockBySize, variationAvailability, selectedColor);
          const isOutOfStock = !inStock;
          return (
            <button
              key={index}
              type="button"
              className={`size-option ${selectedSize === size ? 'selected' : ''} ${isOutOfStock ? 'out-of-stock' : ''}`}
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                if (!isOutOfStock && onSizeSelect) {
                  onSizeSelect(size);
                }
              }}
              disabled={isOutOfStock}
              tabIndex={isOutOfStock ? -1 : 0}
              aria-disabled={isOutOfStock}
              aria-label={isOutOfStock ? `${size} – Unavailable` : `Select size ${size}`}
              title={
                isOutOfStock
                  ? 'This size is not available' + (selectedColor ? ` in ${selectedColor}` : '')
                  : `Select size ${size}`
              }
            >
              <span className="size-option-label">{size}</span>
              {isOutOfStock && <span className="size-option-strike" aria-hidden />}
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default SizeSelector;
