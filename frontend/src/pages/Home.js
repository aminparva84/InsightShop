import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { FaUserTie, FaUser, FaChild } from 'react-icons/fa';
import ProductGrid from '../components/ProductGrid';
import './Home.css';

const openAIChatPopup = () => {
  window.dispatchEvent(new CustomEvent('openAIChat'));
};

const Home = () => {
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchFeaturedProducts();
  }, []);

  const fetchFeaturedProducts = async () => {
    try {
      // Fetch more products to filter for those with images
      const response = await axios.get('/api/products?per_page=100');
      if (response.data && response.data.products) {
        // Filter products that have images (from generated_images or static/images)
        const productsWithImages = response.data.products.filter(product => {
          if (!product.image_url) return false;
          // Check if image is from our local sources (not external URLs)
          return product.image_url.includes('/api/images/') || 
                 product.image_url.includes('static/images/') ||
                 product.image_url.includes('generated_images/');
        });
        
        // If we have products with images, use them; otherwise use all products
        const productsList = productsWithImages.length > 0 
          ? productsWithImages.slice(0, 12) 
          : response.data.products.slice(0, 12);
        
        setProducts(productsList);
      } else {
        setProducts([]);
      }
    } catch (error) {
      console.error('Error fetching products:', error);
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
          <h1 className="hero-title">Welcome to InsightShop - Get AI Help</h1>
          <p className="hero-subtitle">Discover Fashion That Fits Your Style</p>
          <button
            type="button"
            className="hero-ai-button"
            onClick={openAIChatPopup}
          >
            Chat with AI Assistant
          </button>
        </div>
      </section>

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
              <p>No products available at the moment. Ask the AI assistant to find products!</p>
            </div>
          )}
        </div>
      </section>

      {/* Categories */}
      <section className="categories">
        <div className="container">
          <h2 className="section-title">Shop by Category</h2>
          <div className="category-grid">
            <div
              className="category-card"
              onClick={() => navigate('/products?category=men')}
              onKeyDown={(e) => e.key === 'Enter' && navigate('/products?category=men')}
              role="button"
              tabIndex={0}
              aria-label="Shop Men"
            >
              <div className="category-icon">
                <FaUserTie />
              </div>
              <h3>Men</h3>
            </div>
            <div
              className="category-card"
              onClick={() => navigate('/products?category=women')}
              onKeyDown={(e) => e.key === 'Enter' && navigate('/products?category=women')}
              role="button"
              tabIndex={0}
              aria-label="Shop Women"
            >
              <div className="category-icon">
                <FaUser />
              </div>
              <h3>Women</h3>
            </div>
            <div
              className="category-card"
              onClick={() => navigate('/products?category=kids')}
              onKeyDown={(e) => e.key === 'Enter' && navigate('/products?category=kids')}
              role="button"
              tabIndex={0}
              aria-label="Shop Kids"
            >
              <div className="category-icon">
                <FaChild />
              </div>
              <h3>Kids</h3>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Home;

