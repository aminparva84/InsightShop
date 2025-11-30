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

  // Function to update products from AI chat - fetch by exact IDs to ensure 100% match
  const updateProductsFromAI = async (productIds) => {
    if (productIds && productIds.length > 0) {
      try {
        setLoading(true);
        console.log('Home: Fetching products by IDs from AI:', productIds);
        const idsParam = productIds.join(',');
        const response = await axios.get(`/api/products?ids=${idsParam}`);
        
        if (response.data && response.data.products) {
          console.log('Home: Received products from API:', response.data.products.length);
          console.log('Home: Product IDs received:', response.data.products.map(p => p.id));
          console.log('Home: Product details:', response.data.products.map(p => ({ 
            id: p.id, 
            name: p.name, 
            category: p.category, 
            color: p.color 
          })));
          
          // Verify we got the exact products requested
          const receivedIds = response.data.products.map(p => p.id).sort();
          const requestedIds = [...productIds].map(id => parseInt(id)).sort();
          
          // Check for missing products
          const missingIds = requestedIds.filter(id => !receivedIds.includes(id));
          const extraIds = receivedIds.filter(id => !requestedIds.includes(id));
          
          if (missingIds.length > 0) {
            console.warn('Home: Missing product IDs:', missingIds);
          }
          if (extraIds.length > 0) {
            console.warn('Home: Extra product IDs (not requested):', extraIds);
          }
          
          // Filter to only include requested products and maintain order
          const productMap = new Map(response.data.products.map(p => [p.id, p]));
          const orderedProducts = productIds
            .map(id => parseInt(id))
            .map(id => productMap.get(id))
            .filter(p => p != null);
          
          console.log('Home: Ordered products count:', orderedProducts.length);
          console.log('Home: Ordered product IDs:', orderedProducts.map(p => p.id));
          console.log('Home: Ordered product categories:', orderedProducts.map(p => p.category));
          
          if (orderedProducts.length > 0) {
            setProducts(orderedProducts);
          } else {
            console.error('Home: No valid products after filtering!');
            setProducts([]);
          }
        } else {
          console.error('Home: No products in API response');
          setProducts([]);
        }
      } catch (error) {
        console.error('Home: Error fetching products by IDs:', error);
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
              <div className="category-icon">👔</div>
              <h3>Men</h3>
            </div>
            <div className="category-card" onClick={() => {
              // Scroll to AI chat and suggest women's products
              document.querySelector('.ai-chat-inline-container')?.scrollIntoView({ behavior: 'smooth' });
            }}>
              <div className="category-icon">👗</div>
              <h3>Women</h3>
            </div>
            <div className="category-card" onClick={() => {
              // Scroll to AI chat and suggest kids' products
              document.querySelector('.ai-chat-inline-container')?.scrollIntoView({ behavior: 'smooth' });
            }}>
              <div className="category-icon">👶</div>
              <h3>Kids</h3>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Home;

