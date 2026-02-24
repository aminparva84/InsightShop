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
          <ProductCard
            product={product}
            showCompareCheckbox={showCompareCheckbox}
            selectedForCompare={selectedForCompare.includes(product.id)}
            onToggleCompare={onToggleCompare}
          />
        </div>
      ))}
    </div>
  );
};

export default ProductGrid;

