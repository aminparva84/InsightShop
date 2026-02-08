import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { FaUserTie, FaUser, FaChild, FaSeedling, FaSun, FaLeaf, FaSnowflake, FaSocks, FaShoePrints, FaCloudRain, FaSearch } from 'react-icons/fa';
import {
  GiTrousers,
  GiShirt,
  GiTShirt,
  GiMonclerJacket,
  GiDress,
  GiAmpleDress,
  GiSkirt,
  GiShorts,
  GiWool,
  GiHoodie,
  GiSandal,
  GiRunningShoe,
  GiNightSleep,
  GiUnderwear,
} from 'react-icons/gi';
import ProductGrid from '../components/ProductGrid';
import './Home.css';

const openAIChatPopup = () => {
  window.dispatchEvent(new CustomEvent('openAIChat'));
};

const Home = () => {
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    const trimmed = searchQuery.trim();
    if (trimmed) {
      navigate(`/products?search=${encodeURIComponent(trimmed)}`);
    }
  };

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
          <form className="home-search-bar" onSubmit={handleSearchSubmit} role="search">
            <div className="home-search-wrapper">
              <FaSearch className="home-search-icon" aria-hidden="true" />
              <input
                type="search"
                className="home-search-input"
                placeholder="Search styles, colors, occasions..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                aria-label="Search products"
                autoComplete="off"
              />
              <button type="submit" className="home-search-btn">
                Search
              </button>
            </div>
          </form>
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

      {/* Shop by Gender */}
      <section className="categories gender-section">
        <div className="container">
          <h2 className="section-title">Shop by Gender</h2>
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

      {/* Shop by Category (clothing types) */}
      <section className="shop-by-category">
        <div className="container">
          <h2 className="section-title">Shop by Category</h2>
          <div className="clothing-category-grid">
            {[
              { id: 'pants', label: 'Pants', Icon: GiTrousers },
              { id: 'shirts', label: 'Shirts', Icon: GiShirt },
              { id: 't_shirts', label: 'T-Shirts', Icon: GiTShirt },
              { id: 'jackets', label: 'Jackets', Icon: GiMonclerJacket },
              { id: 'coats', label: 'Coats', Icon: FaCloudRain },
              { id: 'socks', label: 'Socks', Icon: FaSocks },
              { id: 'dresses', label: 'Dresses', Icon: GiDress },
              { id: 'skirts', label: 'Skirts', Icon: GiSkirt },
              { id: 'shorts', label: 'Shorts', Icon: GiShorts },
              { id: 'sweaters', label: 'Sweaters', Icon: GiWool },
              { id: 'hoodies', label: 'Hoodies', Icon: GiHoodie },
              { id: 'shoes', label: 'Shoes', Icon: FaShoePrints },
              { id: 'sandals', label: 'Sandals', Icon: GiSandal },
              { id: 'sneakers', label: 'Sneakers', Icon: GiRunningShoe },
              { id: 'pajamas', label: 'Pajamas', Icon: GiNightSleep },
              { id: 'blouses', label: 'Blouses', Icon: GiAmpleDress },
              { id: 'underwear', label: 'Underwear', Icon: GiUnderwear },
              { id: 'suits', label: 'Suits', Icon: FaUserTie },
            ].map(({ id, label, Icon }) => (
              <div
                key={id}
                className="clothing-category-card"
                onClick={() => navigate(`/products?clothing_category=${id}`)}
                onKeyDown={(e) => e.key === 'Enter' && navigate(`/products?clothing_category=${id}`)}
                role="button"
                tabIndex={0}
                aria-label={`Shop ${label}`}
              >
                <div className="clothing-category-icon">
                  <Icon />
                </div>
                <h3>{label}</h3>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Seasonal Shopping */}
      <section className="seasonal-shopping">
        <div className="container">
          <h2 className="section-title">Seasonal Shopping</h2>
          <div className="season-grid">
            <div
              className="season-card season-spring"
              onClick={() => navigate('/products?season=spring')}
              onKeyDown={(e) => e.key === 'Enter' && navigate('/products?season=spring')}
              role="button"
              tabIndex={0}
              aria-label="Shop Spring"
            >
              <div className="season-icon">
                <FaSeedling />
              </div>
              <h3>Spring</h3>
            </div>
            <div
              className="season-card season-summer"
              onClick={() => navigate('/products?season=summer')}
              onKeyDown={(e) => e.key === 'Enter' && navigate('/products?season=summer')}
              role="button"
              tabIndex={0}
              aria-label="Shop Summer"
            >
              <div className="season-icon">
                <FaSun />
              </div>
              <h3>Summer</h3>
            </div>
            <div
              className="season-card season-fall"
              onClick={() => navigate('/products?season=fall')}
              onKeyDown={(e) => e.key === 'Enter' && navigate('/products?season=fall')}
              role="button"
              tabIndex={0}
              aria-label="Shop Fall"
            >
              <div className="season-icon">
                <FaLeaf />
              </div>
              <h3>Fall</h3>
            </div>
            <div
              className="season-card season-winter"
              onClick={() => navigate('/products?season=winter')}
              onKeyDown={(e) => e.key === 'Enter' && navigate('/products?season=winter')}
              role="button"
              tabIndex={0}
              aria-label="Shop Winter"
            >
              <div className="season-icon">
                <FaSnowflake />
              </div>
              <h3>Winter</h3>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Home;

