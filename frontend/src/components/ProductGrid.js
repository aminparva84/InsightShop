import React from 'react';
import ProductCard from './ProductCard';
import './ProductGrid.css';

const ProductGrid = ({ products, onToggleCompare, selectedForCompare = [], showCompareCheckbox = false }) => {
  if (!products || products.length === 0) {
    return <div className="no-products">No products found</div>;
  }

  return (
    <div className="product-grid">
      {products.map(product => (
        <div key={product.id} className="product-grid-item-wrapper">
          {showCompareCheckbox && (
            <div className="compare-checkbox-wrapper">
              <label className="compare-checkbox">
                <input
                  type="checkbox"
                  checked={selectedForCompare.includes(product.id)}
                  onChange={() => onToggleCompare && onToggleCompare(product.id)}
                />
                <span>Compare</span>
              </label>
            </div>
          )}
          <ProductCard product={product} />
        </div>
      ))}
    </div>
  );
};

export default ProductGrid;

