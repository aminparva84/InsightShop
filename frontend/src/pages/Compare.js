import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import axios from 'axios';
import { useCart } from '../contexts/CartContext';
import { useNotification } from '../contexts/NotificationContext';
import SizeSelector from '../components/SizeSelector';
import ColorSwatches from '../components/ColorSwatches';
import './Compare.css';

const Compare = () => {
  const [searchParams] = useSearchParams();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const { addToCart } = useCart();
  const { showSuccess, showError, showWarning } = useNotification();
  const [selectedSizes, setSelectedSizes] = useState({}); // { productId: selectedSize }
  const [selectedColors, setSelectedColors] = useState({}); // { productId: selectedColor }
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
      const fetchedProducts = response.data.products || [];
      setProducts(fetchedProducts);
      
      // Initialize default selections for each product
      const initialSizes = {};
      const initialColors = {};
      fetchedProducts.forEach(product => {
        if (product.available_sizes && product.available_sizes.length > 0) {
          initialSizes[product.id] = product.available_sizes[0];
        }
        if (product.available_colors && product.available_colors.length > 0) {
          initialColors[product.id] = product.available_colors[0];
        }
      });
      setSelectedSizes(initialSizes);
      setSelectedColors(initialColors);
    } catch (error) {
      console.error('Error fetching products for comparison:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = async (productId) => {
    const selectedColor = selectedColors[productId] || null;
    const selectedSize = selectedSizes[productId] || null;
    const result = await addToCart(productId, 1, selectedColor, selectedSize);
    if (result.success) {
      showSuccess('Added to cart!');
      const product = products.find((p) => p.id === productId);
      const stock = product?.stock_quantity;
      const remaining = typeof result.remaining_stock === 'number' ? result.remaining_stock : (typeof stock === 'number' ? Math.max(0, stock - 1) : null);
      const lowStockCount = typeof remaining === 'number' ? remaining : (typeof stock === 'number' && stock >= 1 && stock <= 5 ? stock : null);
      if (lowStockCount !== null && lowStockCount >= 1 && lowStockCount <= 5) {
        const message = `Only ${lowStockCount} left in stock. Make sure to finalize your purchase soon before the item is sold out.`;
        setTimeout(() => showSuccess(message, 6000), 100);
      }
    } else {
      showError(result.error || 'Failed to add to cart');
    }
  };

  const handleSizeChange = (productId, size) => {
    setSelectedSizes(prev => ({ ...prev, [productId]: size }));
  };

  const handleColorChange = (productId, color) => {
    setSelectedColors(prev => ({ ...prev, [productId]: color }));
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
                        onError={(e) => {
                          e.target.src = 'https://via.placeholder.com/150?text=Product';
                          e.target.onerror = null; // Prevent infinite loop
                        }}
                      />
                      <h3>{product.name}</h3>
                      <div className="product-price">${parseFloat(product.price).toFixed(2)}</div>
                      
                      {/* Color Selection - Only show if multiple colors available */}
                      {product.available_colors && product.available_colors.length > 1 && (
                        <div style={{ margin: '8px 0' }}>
                          <ColorSwatches 
                            colors={product.available_colors} 
                            selectedColor={selectedColors[product.id] || product.available_colors[0]}
                            onColorSelect={(color) => handleColorChange(product.id, color)}
                          />
                        </div>
                      )}
                      
                      {/* Size Selection - Only show if multiple sizes available */}
                      {product.available_sizes && product.available_sizes.length > 1 && (
                        <div style={{ margin: '8px 0' }}>
                          <SizeSelector 
                            sizes={product.available_sizes} 
                            selectedSize={selectedSizes[product.id] || product.available_sizes[0]}
                            onSizeSelect={(size) => handleSizeChange(product.id, size)}
                          />
                        </div>
                      )}
                      
                      <button 
                        onClick={() => handleAddToCart(product.id)}
                        className="btn btn-primary btn-sm"
                        style={{ marginTop: '12px' }}
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

