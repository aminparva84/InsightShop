import React, { useMemo, useState, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'motion/react';
import axios from 'axios';
import { FaUserTie, FaUser, FaChild, FaSeedling, FaSun, FaLeaf, FaSnowflake, FaSocks, FaShoePrints, FaCloudRain } from 'react-icons/fa';
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
import FlowingMenu from '../components/FlowingMenu';
import BlurText from '../components/BlurText';
import AIChat from '../components/AIChat';
import WavyUnderline from '../components/WavyUnderline';
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
const BANNER_TEXT_FADEOUT_MS = 5000;
const BANNER_TEXT_FADEOUT_DURATION_S = 2;

const MOBILE_BREAKPOINT = 640;
const MOBILE_PRODUCTS_LIMIT = 4; // 2 rows × 2 columns on mobile

const Home = () => {
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [bannerPhase, setBannerPhase] = useState('idle'); // 'idle' | 'fadingOut' | 'fadedOut'
  const [bannerTextKey, setBannerTextKey] = useState(0);
  const bannerCompleteCountRef = useRef(0);
  const bannerTimeoutRef = useRef(null);
  const [isMobile, setIsMobile] = useState(typeof window !== 'undefined' && window.innerWidth <= MOBILE_BREAKPOINT);

  useEffect(() => {
    const onResize = () => setIsMobile(window.innerWidth <= MOBILE_BREAKPOINT);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  useEffect(() => {
    fetchFeaturedProducts();
  }, []);

  const handleBannerTextAnimationComplete = () => {
    bannerCompleteCountRef.current += 1;
    if (bannerCompleteCountRef.current === 2) {
      bannerCompleteCountRef.current = 0;
      bannerTimeoutRef.current = setTimeout(
        () => setBannerPhase('fadingOut'),
        BANNER_TEXT_FADEOUT_MS
      );
    }
  };

  useEffect(() => {
    return () => {
      if (bannerTimeoutRef.current) clearTimeout(bannerTimeoutRef.current);
    };
  }, []);

  useEffect(() => {
    if (bannerPhase !== 'fadedOut') return;
    setBannerTextKey((k) => k + 1);
    setBannerPhase('idle');
  }, [bannerPhase]);

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
      {/* Top Banner: background, main image (top-banner.png) on right, text */}
      <section className="hero banner-four-layers">
        {/* Asset 1: Background */}
        <div id="banner-asset-1" className="hero-layer hero-layer-bg" data-asset-name="background" aria-hidden="true" />
        {/* Main banner image – right side, responsive */}
        <div id="banner-main" className="hero-layer hero-layer-banner-main" data-asset-name="top-banner" aria-hidden="true">
          <img src={`${process.env.PUBLIC_URL || ''}/images/top-banner.png`} alt="" className="hero-layer-banner-main-img" />
        </div>
        {/* Asset 4: Text + chat – text first, chat template always under it */}
        <div className="hero-banner-text-and-chat">
          <motion.div
            id="banner-asset-4"
            className="hero-layer hero-layer-text"
            data-asset-name="text"
            initial={{ opacity: 1, filter: 'blur(0px)', y: 0 }}
            animate={
              bannerPhase === 'fadingOut'
                ? { opacity: 0, filter: 'blur(10px)', y: -50 }
                : { opacity: 1, filter: 'blur(0px)', y: 0 }
            }
            transition={{
              duration: bannerPhase === 'fadingOut' ? BANNER_TEXT_FADEOUT_DURATION_S : 0,
            }}
            onAnimationComplete={() => {
              if (bannerPhase === 'fadingOut') setBannerPhase('fadedOut');
            }}
          >
            <h1 className="hero-title-line">
              <BlurText
                key={`subtitle-${bannerTextKey}`}
                id="banner-asset-4-subtitle"
                text="insight shop"
                as="span"
                delay={280}
                animateBy="words"
                direction="top"
                className="hero-subtitle-script"
                onAnimationComplete={handleBannerTextAnimationComplete}
              />
              <BlurText
                key={`title-${bannerTextKey}`}
                id="banner-asset-4-title"
                text="INSIGHT SHOP"
                as="span"
                delay={250}
                animateBy="words"
                direction="top"
                className="hero-title"
                onAnimationComplete={handleBannerTextAnimationComplete}
              />
            </h1>
          </motion.div>
          {/* Inline AI chat in banner – always under banner-asset-4 */}
          <div className="hero-chat-inline-wrap" aria-label="AI chat in banner">
            <AIChat isInline />
          </div>
        </div>
      </section>

      {/* Mid banner: same bg as site, container (mid-asset-2); subtitle (mid-asset-3); doodle (mid-doodle) under mid-asset-2 */}
      <section id="mid-asset-1" className="mid-banner" aria-labelledby="mid-banner-heading">
        <div id="mid-asset-2" className="mid-banner-container">
          <p id="mid-banner-heading" className="mid-banner-title">
            HARD TO FIND<br />
            <span className="mid-banner-title-line">
              WHAT YOU NEED?
              <span id="mid-asset-3" className="mid-banner-subtitle">It&apos;s okay!</span>
            </span>
          </p>
        </div>
        <img
          id="mid-doodle"
          src={`${process.env.PUBLIC_URL || ''}/images/mid-doodle.png`}
          alt=""
          className="mid-banner-doodle"
          aria-hidden="true"
        />
      </section>

      {/* Featured Products */}
      <section className="featured-products">
        <div className="container">
          <div className="section-title-wrap">
            <h2 className="section-title">Featured Products</h2>
            <WavyUnderline color="#373F2E" className="section-title-wavy" />
          </div>
          <div className="featured-products-actions">
            <Link to="/products" className="featured-products-action-btn nav-bar-styler-gender-button">
              Search
            </Link>
            <button type="button" onClick={openAIChatPopup} className="featured-products-action-btn nav-bar-styler-gender-button" aria-label="Ask AI for help">
              Ask AI
            </button>
          </div>
          <div className="featured-products-line" aria-hidden="true" />
          {loading ? (
            <div className="spinner"></div>
          ) : products.length > 0 ? (
            <>
              <ProductGrid products={isMobile ? products.slice(0, MOBILE_PRODUCTS_LIMIT) : products} />
              <div className="featured-products-line" aria-hidden="true" />
              <div className="featured-products-view-all">
                <Link to="/products" className="featured-products-view-all-link">View all products</Link>
              </div>
            </>
          ) : (
            <div className="no-products-message">
              <p>No products available at the moment. Ask the AI assistant to find products!</p>
            </div>
          )}
        </div>
      </section>

      {/* Seasonal Shopping — FlowingMenu with logos */}
      <section className="seasonal-shopping">
        <div className="container">
          <div className="section-title-wrap">
            <h2 className="section-title">Seasonal Shopping</h2>
            <WavyUnderline color="#373F2E" className="section-title-wavy" />
          </div>
          <div className="seasonal-flowing-wrap">
            <FlowingMenu
              items={SEASONAL_ITEMS}
              speed={15}
              textColor="#E8E4DC"
              bgColor="transparent"
              marqueeBgColor="#E8E4DC"
              marqueeTextColor="#373F2E"
              borderColor="rgba(232, 228, 220, 0.35)"
              linkComponent={Link}
            />
          </div>
        </div>
      </section>
    </div>
  );
};

export default Home;

