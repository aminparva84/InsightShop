import React, { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { FaUserTie, FaUser, FaChild } from 'react-icons/fa';
import AIChat from '../components/AIChat';
import ProductGrid from '../components/ProductGrid';
import Logo from '../components/Logo';
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
      if (response.data && response.data.products) {
        const productsList = response.data.products;
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

  // Function to update products from AI chat - fetch by exact IDs to ensure 100% match
  const updateProductsFromAI = async (productIds) => {
    if (productIds && productIds.length > 0) {
      try {
        setLoading(true);
        const idsParam = productIds.join(',');
        const response = await axios.get(`/api/products?ids=${idsParam}`);
        
        if (response.data && response.data.products) {
          // Filter to only include requested products and maintain order
          const productMap = new Map(response.data.products.map(p => [p.id, p]));
          const orderedProducts = productIds
            .map(id => parseInt(id))
            .map(id => productMap.get(id))
            .filter(p => p != null);
          
          if (orderedProducts.length > 0) {
            setProducts(orderedProducts);
          } else {
            setProducts([]);
          }
        } else {
          setProducts([]);
        }
      } catch (error) {
        console.error('Error fetching products by IDs:', error);
        setProducts([]);
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <div className="home">
      {/* Hero Section */}
      <section className="hero">
        <div className="hero-content">
          <Logo size="large" />
          <h1 className="hero-title">Welcome to InsightShop - Get AI Help</h1>
          <p className="hero-subtitle">Discover Fashion That Fits Your Style</p>
        </div>
      </section>

      {/* AI Chat Section - Inline */}
      <section className="ai-chat-section">
        <div className="container">
          <div className="ai-chat-inline-container">
            <AIChat 
              onClose={null} 
              onMinimize={null} 
              isInline={true}
              onProductsUpdate={updateProductsFromAI}
            />
          </div>
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
            <div className="category-card" onClick={() => {
              // Scroll to AI chat and suggest men's products
              document.querySelector('.ai-chat-inline-container')?.scrollIntoView({ behavior: 'smooth' });
            }}>
              <div className="category-icon">
                <FaUserTie />
              </div>
              <h3>Men</h3>
            </div>
            <div className="category-card" onClick={() => {
              // Scroll to AI chat and suggest women's products
              document.querySelector('.ai-chat-inline-container')?.scrollIntoView({ behavior: 'smooth' });
            }}>
              <div className="category-icon">
                <FaUser />
              </div>
              <h3>Women</h3>
            </div>
            <div className="category-card" onClick={() => {
              // Scroll to AI chat and suggest kids' products
              document.querySelector('.ai-chat-inline-container')?.scrollIntoView({ behavior: 'smooth' });
            }}>
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

