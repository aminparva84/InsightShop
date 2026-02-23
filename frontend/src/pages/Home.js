import React, { useMemo, useState, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'motion/react';
import axios from 'axios';
import { FaUserTie, FaUser, FaChild, FaSocks, FaShoePrints, FaCloudRain } from 'react-icons/fa';
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
import BlurText from '../components/BlurText';
import AIChat from '../components/AIChat';
import SectionTitleWithWavy from '../components/SectionTitleWithWavy';
import womanImage from '../assets/woman-image.webp';
import midBannerMain from '../assets/mid-banner-main.webp';
import midBannerMobile from '../assets/mid-banner-mobile.webp';
import './Home.css';

/* Season banners: image + glass overlay + label, link to filtered products */
const SEASON_BANNERS = [
  { name: 'Spring', link: '/products?season=spring', image: 'https://images.unsplash.com/photo-1522383225653-ed111181a951?w=600&q=80' },
  { name: 'Summer', link: '/products?season=summer', image: 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=600&q=80' },
  { name: 'Fall', link: '/products?season=fall', image: 'https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=600&q=80' },
  { name: 'Winter', link: '/products?season=winter', image: 'https://images.unsplash.com/photo-1706893684108-fa7ca5718c3a?w=600&q=80' },
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

/** Featured products: 3 rows × N columns. Columns: 3 (<640px), 4 (640–1024), 5 (≥1024). */
const getFeaturedCount = (width) => {
  if (width < 640) return 9;   // 3 cols × 3 rows
  if (width < 1024) return 12;  // 4 cols × 3 rows
  return 15;                    // 5 cols × 3 rows
};

const Home = () => {
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [specialOffers, setSpecialOffers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [specialOffersLoading, setSpecialOffersLoading] = useState(true);
  const [bannerPhase, setBannerPhase] = useState('idle'); // 'idle' | 'fadingOut' | 'fadedOut'
  const [bannerTextKey, setBannerTextKey] = useState(0);
  const bannerCompleteCountRef = useRef(0);
  const bannerTimeoutRef = useRef(null);
  const [isMobile, setIsMobile] = useState(typeof window !== 'undefined' && window.innerWidth <= MOBILE_BREAKPOINT);
  const [featuredCount, setFeaturedCount] = useState(() =>
    typeof window !== 'undefined' ? getFeaturedCount(window.innerWidth) : 15
  );
  const specialOffersScrollRef = useRef(null);
  const specialOffersDragRef = useRef({ isDragging: false, startX: 0, startScrollLeft: 0 });
  const [specialOffersDragging, setSpecialOffersDragging] = useState(false);

  useEffect(() => {
    const onResize = () => {
      const w = window.innerWidth;
      setIsMobile(w <= MOBILE_BREAKPOINT);
      setFeaturedCount(getFeaturedCount(w));
    };
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  useEffect(() => {
    fetchFeaturedProducts();
  }, []);

  useEffect(() => {
    const fetchSpecialOffers = async () => {
      try {
        const response = await axios.get('/api/products/special-offers?limit=12');
        if (response.data && response.data.products) {
          setSpecialOffers(response.data.products);
        } else {
          setSpecialOffers([]);
        }
      } catch (error) {
        console.error('Error fetching special offers:', error);
        setSpecialOffers([]);
      } finally {
        setSpecialOffersLoading(false);
      }
    };
    fetchSpecialOffers();
  }, []);

  const handleSpecialOffersMouseDown = (e) => {
    if (!specialOffersScrollRef.current) return;
    specialOffersDragRef.current.isDragging = true;
    specialOffersDragRef.current.startX = e.pageX;
    specialOffersDragRef.current.startScrollLeft = specialOffersScrollRef.current.scrollLeft;
    setSpecialOffersDragging(true);
  };
  const handleSpecialOffersMouseMove = (e) => {
    if (!specialOffersDragRef.current.isDragging || !specialOffersScrollRef.current) return;
    e.preventDefault();
    const walk = (e.pageX - specialOffersDragRef.current.startX) * 1.2;
    specialOffersScrollRef.current.scrollLeft = specialOffersDragRef.current.startScrollLeft - walk;
  };
  const handleSpecialOffersMouseUpOrLeave = () => {
    specialOffersDragRef.current.isDragging = false;
    setSpecialOffersDragging(false);
  };
  /* Re-run when special offers mount so ref is set and drag listeners are attached (desktop) */
  useEffect(() => {
    const el = specialOffersScrollRef.current;
    if (!el) return;
    const onMove = (e) => handleSpecialOffersMouseMove(e);
    const onUp = () => handleSpecialOffersMouseUpOrLeave();
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
    return () => {
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
    };
  }, [specialOffers.length]);

  /* Desktop: translate vertical wheel over carousel into horizontal scroll */
  useEffect(() => {
    const el = specialOffersScrollRef.current;
    if (!el) return;
    const onWheel = (e) => {
      if (e.deltaY === 0) return;
      e.preventDefault();
      el.scrollLeft += e.deltaY;
    };
    el.addEventListener('wheel', onWheel, { passive: false });
    return () => el.removeEventListener('wheel', onWheel);
  }, [specialOffers.length]);

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
        // Prefer products that have a valid image URL (local or API); otherwise show all
        const productsWithImages = response.data.products.filter(product => {
          if (!product.image_url) return false;
          return product.image_url.startsWith('/api/images/') ||
                 product.image_url.startsWith('/images/') ||
                 product.image_url.includes('static/images/') ||
                 product.image_url.includes('generated_images/');
        });
        const productsList = productsWithImages.length > 0
          ? productsWithImages.slice(0, 15)
          : response.data.products.slice(0, 15);
        
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
      {/* Top Banner: background, hero image (woman-image) on right, text */}
      <section className="hero banner-four-layers">
        {/* Asset 1: Background */}
        <div id="banner-asset-1" className="hero-layer hero-layer-bg" data-asset-name="background" aria-hidden="true" />
        {/* Content row: text + chat, then hero image exactly on their right */}
        <div className="hero-banner-content">
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
          {/* Hero image – exactly to the right of text and chat */}
          <div id="banner-main" className="hero-layer hero-layer-banner-main" data-asset-name="hero-image" aria-hidden="true">
            <img src={womanImage} alt="" className="hero-layer-banner-main-img" />
          </div>
        </div>
      </section>

      {/* Featured Products (container includes Special offers below) */}
      <section className="featured-products">
        <div className="container">
          {/* Featured Products – first */}
          <div className="section-title-wrap">
            <SectionTitleWithWavy title="Featured Products" />
          </div>
          {loading ? (
            <div className="spinner"></div>
          ) : products.length > 0 ? (
            <>
              <ProductGrid products={products.slice(0, featuredCount)} />
              <div className="featured-products-view-all">
                <Link to="/products" className="featured-products-view-all-link">View all products</Link>
              </div>
            </>
          ) : (
            <div className="no-products-message">
              <p>No products available at the moment. Ask the AI assistant to find products!</p>
            </div>
          )}

          {/* Special offers – after Featured Products, same container */}
          {specialOffers.length > 0 && (
            <div className="special-offers">
              <div className="section-title-wrap">
                <SectionTitleWithWavy title="Special offers" />
              </div>
              {specialOffersLoading ? (
                <div className="spinner"></div>
              ) : (
                <>
                  <div
                    ref={specialOffersScrollRef}
                    className={`special-offers-scroll-wrap${specialOffersDragging ? ' special-offers-scroll-wrap--dragging' : ''}`}
                    onMouseDown={handleSpecialOffersMouseDown}
                    onMouseLeave={handleSpecialOffersMouseUpOrLeave}
                    role="region"
                    aria-label="Special offers carousel"
                  >
                    <ProductGrid products={specialOffers} />
                  </div>
                  <div className="featured-products-view-all">
                    <Link to="/products?on_sale=1" className="featured-products-view-all-link">View all deals</Link>
                  </div>
                  <div className="featured-products-line" aria-hidden="true" />
                </>
              )}
            </div>
          )}
        </div>
      </section>

      {/* Special offers CTA banner – below featured products container, vintage style */}
      <section
        className="special-offers-cta-banner"
        aria-label="Don't miss our special offers"
        style={{ '--special-offers-banner-bg': `url(${process.env.PUBLIC_URL || ''}/images/special-offers-banner.jpg)` }}
      >
        <div className="special-offers-cta-banner-inner">
          <span className="special-offers-cta-banner-accent" aria-hidden="true">— Limited time —</span>
          <h2 className="special-offers-cta-banner-title">Don't Miss Our Special Offers</h2>
          <p className="special-offers-cta-banner-subtitle">Save up to <strong className="special-offers-cta-banner-percent">50%</strong> on curated deals — exclusive savings, crafted for you.</p>
          <Link to="/products?on_sale=1" className="special-offers-cta-banner-btn">View all deals</Link>
        </div>
        <div className="special-offers-cta-banner-ornament" aria-hidden="true" />
      </section>

      {/* Mid banner: image inside centered container, below featured products */}
      <section id="mid-asset-1" className="mid-banner" aria-label="Mid banner">
        <div className="mid-banner-container">
          <picture>
            <source
              media="(max-width: 768px)"
              srcSet={midBannerMobile}
              src={midBannerMobile}
            />
            <img
              src={midBannerMain}
              alt="Hard to find what you need? It's ok!"
              className="mid-banner-image"
            />
          </picture>
        </div>
      </section>

      {/* Season banners: 4 side by side, glass overlay, season-specific hover effects */}
      <section className="season-banners" aria-label="Shop by season">
        <div className="season-banners-inner">
          <div className="section-title-wrap">
            <SectionTitleWithWavy title="Seasonal Shopping" />
          </div>
          <div className="season-banners-container">
          {SEASON_BANNERS.map((season) => (
            <Link
              key={season.name}
              to={season.link}
              className="season-banner-card"
              style={{ backgroundImage: `url(${season.image})` }}
              aria-label={`Shop ${season.name} collection`}
            >
              <span className="season-banner-glass" aria-hidden="true" />
              <span className="season-banner-label">{season.name}</span>
              {/* Season-specific hover effect: snow, petals, heat shimmer, leaves */}
              <div className={`season-banner-effect season-banner-effect--${season.name.toLowerCase()}`} aria-hidden="true">
                {season.name === 'Winter' && Array.from({ length: 14 }, (_, i) => (
                  <span key={i} className="season-particle season-particle--snow" style={{ left: `${(i * 7) % 100}%`, '--anim-delay': `${(i * 0.35) % 4}s`, '--anim-duration': `${2.5 + (i % 3) * 0.5}s` }} />
                ))}
                {season.name === 'Spring' && Array.from({ length: 10 }, (_, i) => (
                  <span key={i} className="season-particle season-particle--petal" style={{ left: `${10 + (i * 9)}%`, '--anim-delay': `${(i * 0.3) % 3}s`, '--anim-duration': `${3 + (i % 2) * 0.6}s` }} />
                ))}
                {season.name === 'Summer' && <span className="season-particle season-particle--shimmer" />}
                {season.name === 'Fall' && Array.from({ length: 10 }, (_, i) => (
                  <span key={i} className="season-particle season-particle--leaf" style={{ left: `${(i * 11) % 95}%`, '--anim-delay': `${(i * 0.25) % 3.5}s`, '--anim-duration': `${2.8 + (i % 2) * 0.4}s` }} />
                ))}
              </div>
            </Link>
          ))}
          </div>
        </div>
      </section>
    </div>
  );
};

export default Home;

