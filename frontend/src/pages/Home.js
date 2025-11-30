import React, { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import AIChat from '../components/AIChat';
import ProductGrid from '../components/ProductGrid';
import './Home.css';

const Home = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAIChat, setShowAIChat] = useState(false);

  useEffect(() => {
    fetchFeaturedProducts();
  }, []);

  const fetchFeaturedProducts = async () => {
    try {
      const response = await axios.get('/api/products?per_page=12');
      console.log('API Response:', response.data);
      if (response.data && response.data.products) {
        const productsList = response.data.products;
        console.log('Products fetched:', productsList.length);
        setProducts(productsList);
      } else {
        console.error('Invalid response format:', response.data);
        setProducts([]);
      }
    } catch (error) {
      console.error('Error fetching products:', error);
      console.error('Error details:', error.response?.data || error.message);
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="home">
      {/* Hero Section */}
      <section className="hero">
        <div className="hero-content">
          <h1 className="hero-title">Welcome to InsightShop</h1>
          <p className="hero-subtitle">Discover Fashion That Fits Your Style</p>
          <div className="hero-buttons">
            <Link to="/products" className="btn btn-primary">Shop Now</Link>
            <button 
              onClick={() => {
                console.log('AI Chat button clicked');
                setShowAIChat(true);
              }} 
              className="btn btn-secondary"
              style={{ cursor: 'pointer' }}
            >
              🤖 Ask AI Assistant
            </button>
          </div>
          
        </div>
      </section>

            {/* AI Chat Section */}
            {showAIChat && (
              <div className="ai-chat-overlay" onClick={() => setShowAIChat(false)}>
                <div className="ai-chat-container" onClick={(e) => e.stopPropagation()}>
                  <AIChat 
                    onClose={() => setShowAIChat(false)} 
                    onMinimize={() => setShowAIChat(false)}
                  />
                </div>
              </div>
            )}

      {/* Featured Products */}
      <section className="featured-products">
        <div className="container">
          <h2 className="section-title">Featured Products</h2>
          {loading ? (
            <div className="spinner"></div>
          ) : products.length > 0 ? (
            <ProductGrid products={products} />
          ) : (
            <div className="no-products-message">
              <p>No products available at the moment.</p>
              <Link to="/products" className="btn btn-primary">Browse All Products</Link>
            </div>
          )}
          {products.length > 0 && (
            <div className="section-footer">
              <Link to="/products" className="btn btn-outline">View All Products</Link>
            </div>
          )}
        </div>
      </section>

      {/* Categories */}
      <section className="categories">
        <div className="container">
          <h2 className="section-title">Shop by Category</h2>
          <div className="category-grid">
            <Link to="/products?category=men" className="category-card">
              <div className="category-icon">👔</div>
              <h3>Men</h3>
            </Link>
            <Link to="/products?category=women" className="category-card">
              <div className="category-icon">👗</div>
              <h3>Women</h3>
            </Link>
            <Link to="/products?category=kids" className="category-card">
              <div className="category-icon">👶</div>
              <h3>Kids</h3>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Home;

