import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import axios from 'axios';
import { useCart } from '../contexts/CartContext';
import { useNotification } from '../contexts/NotificationContext';
import './Compare.css';

const Compare = () => {
  const [searchParams] = useSearchParams();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const { addToCart } = useCart();
  const { showSuccess, showError } = useNotification();
  const productIds = searchParams.get('ids')?.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id)) || [];

  useEffect(() => {
    if (productIds.length > 0) {
      fetchProducts();
    } else {
      setLoading(false);
    }
  }, [productIds.join(',')]);

  const fetchProducts = async () => {
    try {
      setLoading(true);
      const response = await axios.post('/api/ai/compare', {
        product_ids: productIds
      });
      setProducts(response.data.products || []);
    } catch (error) {
      console.error('Error fetching products for comparison:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = async (productId) => {
    const result = await addToCart(productId, 1);
    if (result.success) {
      showSuccess('Added to cart!');
    } else {
      showError(result.error || 'Failed to add to cart');
    }
  };

  if (loading) {
    return <div className="spinner"></div>;
  }

  if (productIds.length < 2) {
    return (
      <div className="compare-page">
        <div className="container">
          <h1>Compare Products</h1>
          <p>Please select at least 2 products to compare.</p>
          <Link to="/products" className="btn btn-primary">Browse Products</Link>
        </div>
      </div>
    );
  }

  if (products.length < 2) {
    return (
      <div className="compare-page">
        <div className="container">
          <h1>Compare Products</h1>
          <p>Could not load products for comparison.</p>
          <Link to="/products" className="btn btn-primary">Browse Products</Link>
        </div>
      </div>
    );
  }

  // Get all unique attributes for comparison
  const attributes = ['name', 'price', 'category', 'color', 'size', 'stock_quantity', 'description'];
  const comparison = {
    price_range: {
      min: Math.min(...products.map(p => parseFloat(p.price))),
      max: Math.max(...products.map(p => parseFloat(p.price)))
    },
    categories: [...new Set(products.map(p => p.category))],
    colors: [...new Set(products.map(p => p.color).filter(Boolean))]
  };

  return (
    <div className="compare-page">
      <div className="container">
        <div className="compare-header">
          <h1>Compare Products</h1>
          <Link to="/products" className="btn btn-outline">Back to Products</Link>
        </div>

        <div className="compare-table-wrapper">
          <table className="compare-table">
            <thead>
              <tr>
                <th>Attribute</th>
                {products.map(product => (
                  <th key={product.id} className="product-column">
                    <div className="product-header">
                      <img 
                        src={product.image_url || 'https://via.placeholder.com/150'} 
                        alt={product.name}
                        className="compare-product-image"
                      />
                      <h3>{product.name}</h3>
                      <div className="product-price">${parseFloat(product.price).toFixed(2)}</div>
                      <button 
                        onClick={() => handleAddToCart(product.id)}
                        className="btn btn-primary btn-sm"
                      >
                        Add to Cart
                      </button>
                      <Link 
                        to={`/products/${product.id}`}
                        className="btn-link"
                      >
                        View Details
                      </Link>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="attribute-label"><strong>Price</strong></td>
                {products.map(product => (
                  <td key={product.id}>${parseFloat(product.price).toFixed(2)}</td>
                ))}
              </tr>
              <tr>
                <td className="attribute-label"><strong>Category</strong></td>
                {products.map(product => (
                  <td key={product.id}>{product.category}</td>
                ))}
              </tr>
              <tr>
                <td className="attribute-label"><strong>Color</strong></td>
                {products.map(product => (
                  <td key={product.id}>
                    <span className="color-badge" style={{backgroundColor: product.color?.toLowerCase() || '#ccc'}}>
                      {product.color || 'N/A'}
                    </span>
                  </td>
                ))}
              </tr>
              <tr>
                <td className="attribute-label"><strong>Size</strong></td>
                {products.map(product => (
                  <td key={product.id}>{product.size || 'N/A'}</td>
                ))}
              </tr>
              <tr>
                <td className="attribute-label"><strong>Stock</strong></td>
                {products.map(product => (
                  <td key={product.id}>
                    <span className={product.stock_quantity > 0 ? 'in-stock' : 'out-of-stock'}>
                      {product.stock_quantity > 0 ? `${product.stock_quantity} in stock` : 'Out of stock'}
                    </span>
                  </td>
                ))}
              </tr>
              <tr>
                <td className="attribute-label"><strong>Description</strong></td>
                {products.map(product => (
                  <td key={product.id} className="description-cell">
                    {product.description || 'No description available'}
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>

        <div className="compare-summary">
          <h2>Summary</h2>
          <div className="summary-grid">
            <div className="summary-item">
              <strong>Price Range:</strong> ${comparison.price_range.min.toFixed(2)} - ${comparison.price_range.max.toFixed(2)}
            </div>
            <div className="summary-item">
              <strong>Categories:</strong> {comparison.categories.join(', ')}
            </div>
            <div className="summary-item">
              <strong>Colors:</strong> {comparison.colors.join(', ') || 'N/A'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Compare;

