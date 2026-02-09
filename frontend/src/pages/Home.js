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

      {/* Shop by Category (gender + clothing types) */}
      <section className="shop-by-category">
        <div className="container">
          <h2 className="section-title">Shop by Category</h2>
          <div className="clothing-category-grid">
            {[
              { type: 'gender', id: 'men', label: 'Men', Icon: FaUserTie, path: '/products?category=men' },
              { type: 'gender', id: 'women', label: 'Women', Icon: FaUser, path: '/products?category=women' },
              { type: 'gender', id: 'kids', label: 'Kids', Icon: FaChild, path: '/products?category=kids' },
              { type: 'clothing', id: 'pants', label: 'Pants', Icon: GiTrousers, path: '/products?clothing_category=pants' },
              { type: 'clothing', id: 'shirts', label: 'Shirts', Icon: GiShirt, path: '/products?clothing_category=shirts' },
              { type: 'clothing', id: 't_shirts', label: 'T-Shirts', Icon: GiTShirt, path: '/products?clothing_category=t_shirts' },
              { type: 'clothing', id: 'jackets', label: 'Jackets', Icon: GiMonclerJacket, path: '/products?clothing_category=jackets' },
              { type: 'clothing', id: 'coats', label: 'Coats', Icon: FaCloudRain, path: '/products?clothing_category=coats' },
              { type: 'clothing', id: 'socks', label: 'Socks', Icon: FaSocks, path: '/products?clothing_category=socks' },
              { type: 'clothing', id: 'dresses', label: 'Dresses', Icon: GiDress, path: '/products?clothing_category=dresses' },
              { type: 'clothing', id: 'skirts', label: 'Skirts', Icon: GiSkirt, path: '/products?clothing_category=skirts' },
              { type: 'clothing', id: 'shorts', label: 'Shorts', Icon: GiShorts, path: '/products?clothing_category=shorts' },
              { type: 'clothing', id: 'sweaters', label: 'Sweaters', Icon: GiWool, path: '/products?clothing_category=sweaters' },
              { type: 'clothing', id: 'hoodies', label: 'Hoodies', Icon: GiHoodie, path: '/products?clothing_category=hoodies' },
              { type: 'clothing', id: 'shoes', label: 'Shoes', Icon: FaShoePrints, path: '/products?clothing_category=shoes' },
              { type: 'clothing', id: 'sandals', label: 'Sandals', Icon: GiSandal, path: '/products?clothing_category=sandals' },
              { type: 'clothing', id: 'sneakers', label: 'Sneakers', Icon: GiRunningShoe, path: '/products?clothing_category=sneakers' },
              { type: 'clothing', id: 'pajamas', label: 'Pajamas', Icon: GiNightSleep, path: '/products?clothing_category=pajamas' },
              { type: 'clothing', id: 'blouses', label: 'Blouses', Icon: GiAmpleDress, path: '/products?clothing_category=blouses' },
              { type: 'clothing', id: 'underwear', label: 'Underwear', Icon: GiUnderwear, path: '/products?clothing_category=underwear' },
              { type: 'clothing', id: 'suits', label: 'Suits', Icon: FaUserTie, path: '/products?clothing_category=suits' },
            ].map(({ id, label, Icon, path }) => (
              <div
                key={`${id}-${label}`}
                className="clothing-category-card"
                onClick={() => navigate(path)}
                onKeyDown={(e) => e.key === 'Enter' && navigate(path)}
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

