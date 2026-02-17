import React, { useMemo, useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
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
import LogoLoop from '../components/LogoLoop';
import FlowingMenu from '../components/FlowingMenu';
import BlurText from '../components/BlurText';
import './Home.css';

/* Seasonal menu: images from Unsplash (season-themed, free to use) */
const SEASONAL_ITEMS = [
  { link: '/products?season=spring', text: 'Spring', image: 'https://images.unsplash.com/photo-1522383225653-ed111181a951?w=600&q=80', logo: <FaSeedling />, logoColor: '#2d7d46' },
  { link: '/products?season=summer', text: 'Summer', image: 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=600&q=80', logo: <FaSun />, logoColor: '#d4a017' },
  { link: '/products?season=fall', text: 'Fall', image: 'https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=600&q=80', logo: <FaLeaf />, logoColor: '#c45c26' },
  { link: '/products?season=winter', text: 'Winter', image: 'https://images.unsplash.com/photo-1706893684108-fa7ca5718c3a?w=600&q=80', logo: <FaSnowflake />, logoColor: '#4a7ba7' },
];

const CATEGORIES = [
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
];

const openAIChatPopup = () => {
  window.dispatchEvent(new CustomEvent('openAIChat'));
};

/* Stable arrays for TextType so animation effect deps don’t churn on re-render */
const Home = () => {
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  const categoryLogos = useMemo(() => CATEGORIES, []);

  const renderCategoryItem = useMemo(
    () => (item, key) => {
      const Icon = item.Icon;
      return (
        <Link
          to={item.path}
          className="clothing-category-card logoloop-category-card"
          aria-label={`Shop ${item.label}`}
        >
          <div className="clothing-category-icon">
            <Icon />
          </div>
          <h3>{item.label}</h3>
        </Link>
      );
    },
    []
  );

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

  const heroModelSrc = `${process.env.PUBLIC_URL || ''}/images/hero-model.png`;

  return (
    <div className="home">
      {/* Top Banner: 4 layers with IDs for reference
          Asset 1 = background, Asset 2 = rounded rect, Asset 3 = image, Asset 4 = text */}
      <section className="hero banner-four-layers">
        {/* Asset 1: Background */}
        <div id="banner-asset-1" className="hero-layer hero-layer-bg" data-asset-name="background" aria-hidden="true" />
        {/* Asset 2 + 3: grouped for shared hover (rounded rect + image) */}
        <div className="hero-banner-assets-group">
          <div id="banner-asset-2" className="hero-layer hero-layer-rounded-rect" data-asset-name="rounded-rectangle" aria-hidden="true" />
          <div id="banner-asset-3" className="hero-layer hero-layer-image" data-asset-name="model-image">
            <img src={heroModelSrc} alt="" className="hero-layer-image-img" />
          </div>
        </div>
        {/* Asset 4: Text (INSIGHT SHOP + insight shop) – BlurText animation */}
        <div id="banner-asset-4" className="hero-layer hero-layer-text" data-asset-name="text">
          <h1 className="hero-title-line">
            <BlurText
              id="banner-asset-4-subtitle"
              text="insight shop"
              as="span"
              delay={280}
              animateBy="words"
              direction="top"
              className="hero-subtitle-script"
            />
            <BlurText
              id="banner-asset-4-title"
              text="INSIGHT SHOP"
              as="span"
              delay={250}
              animateBy="words"
              direction="top"
              className="hero-title"
            />
          </h1>
        </div>
        <button type="button" className="hero-cta" onClick={openAIChatPopup}>
          Chat with Ai assistant
        </button>
        <span className="hero-help-info">HELP INFO</span>
      </section>

      {/* Hard to find – asset-20 container, Asset 19 text + image overlapping */}
      <section className="home-hard-to-find" aria-labelledby="hard-to-find-heading">
        <div className="home-hard-to-find-container">
          <div className="home-hard-to-find-content">
            <p id="hard-to-find-heading" className="home-hard-to-find-text">
              HARD TO FIND<br />WHAT YOU NEED?
            </p>
            <img
              src={`${process.env.PUBLIC_URL || ''}/images/asset-19.png`}
              alt=""
              className="home-hard-to-find-image"
              aria-hidden="true"
            />
          </div>
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

      {/* Shop by Category (LogoLoop: two rows, opposite directions) */}
      <section className="shop-by-category">
        <div className="container">
          <h2 className="section-title">Shop by Category</h2>
          <div className="shop-by-category-loop-wrapper" aria-label="Shop by category">
            <LogoLoop
              logos={categoryLogos}
              speed={40}
              direction="right"
              logoHeight={56}
              gap={24}
              hoverSpeed={60}
              scaleOnHover
              fadeOut
              fadeOutColor="#ffffff"
              renderItem={renderCategoryItem}
              ariaLabel="Shop by category"
              className="shop-by-category-logoloop"
            />
          </div>
          <div className="shop-by-category-loop-wrapper shop-by-category-loop-row-2" aria-label="Shop by category">
            <LogoLoop
              logos={categoryLogos}
              speed={40}
              direction="left"
              logoHeight={56}
              gap={24}
              hoverSpeed={60}
              scaleOnHover
              fadeOut
              fadeOutColor="#ffffff"
              renderItem={renderCategoryItem}
              ariaLabel="Shop by category"
              className="shop-by-category-logoloop"
            />
          </div>
        </div>
      </section>

      {/* Seasonal Shopping — FlowingMenu with logos */}
      <section className="seasonal-shopping">
        <div className="container">
          <h2 className="section-title">Seasonal Shopping</h2>
          <div className="seasonal-flowing-wrap">
            <FlowingMenu
              items={SEASONAL_ITEMS}
              speed={15}
              textColor="#ffffff"
              bgColor="#060010"
              marqueeBgColor="#ffffff"
              marqueeTextColor="#060010"
              borderColor="#ffffff"
              linkComponent={Link}
            />
          </div>
        </div>
      </section>
    </div>
  );
};

export default Home;

