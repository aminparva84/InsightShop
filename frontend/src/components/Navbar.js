import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import { FaUserTie, FaCloudRain, FaSocks, FaShoePrints } from 'react-icons/fa';
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
import { useAuth } from '../contexts/AuthContext';
import { useCart } from '../contexts/CartContext';
import SpotlightCard from './SpotlightCard';
import './Navbar.css';

const NAV_MOBILE_BREAKPOINT = 768;

/* Genders and clothing categories for slider filter (matches products API) */
const GENDERS = [
  { id: 'men', label: 'Men' },
  { id: 'women', label: 'Women' },
  { id: 'kids', label: 'Kids' },
];

/* Same categorical icons as Home logo loop */
const CLOTHING_CATEGORIES = [
  { id: 'shirts', label: 'Shirts', Icon: GiShirt },
  { id: 't_shirts', label: 'T-Shirts', Icon: GiTShirt },
  { id: 'pants', label: 'Pants', Icon: GiTrousers },
  { id: 'jackets', label: 'Jackets', Icon: GiMonclerJacket },
  { id: 'coats', label: 'Coats', Icon: FaCloudRain },
  { id: 'dresses', label: 'Dresses', Icon: GiDress },
  { id: 'skirts', label: 'Skirts', Icon: GiSkirt },
  { id: 'shorts', label: 'Shorts', Icon: GiShorts },
  { id: 'sweaters', label: 'Sweaters', Icon: GiWool },
  { id: 'hoodies', label: 'Hoodies', Icon: GiHoodie },
  { id: 'socks', label: 'Socks', Icon: FaSocks },
  { id: 'shoes', label: 'Shoes', Icon: FaShoePrints },
  { id: 'sandals', label: 'Sandals', Icon: GiSandal },
  { id: 'sneakers', label: 'Sneakers', Icon: GiRunningShoe },
  { id: 'pajamas', label: 'Pajamas', Icon: GiNightSleep },
  { id: 'blouses', label: 'Blouses', Icon: GiAmpleDress },
  { id: 'underwear', label: 'Underwear', Icon: GiUnderwear },
  { id: 'suits', label: 'Suits', Icon: FaUserTie },
];

const SearchIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <path d="M21 21L16.65 16.65M19 11C19 15.4183 15.4183 19 11 19C6.58172 19 3 15.4183 3 11C3 6.58172 6.58172 3 11 3C15.4183 3 19 6.58172 19 11Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

/* Cart icon – custom asset (bag/shopping cart shape) */
const CartIcon = () => (
  <svg width="33" height="33" viewBox="0 0 70 56" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" preserveAspectRatio="xMidYMid meet">
    <path
      d="M0 0 C2.31 0.33 4.62 0.66 7 1 C9 6.75 9 6.75 9 9 C10.03386841 8.99214478 10.03386841 8.99214478 11.08862305 8.98413086 C36.37660601 8.81727622 36.37660601 8.81727622 47 10 C47.495 11.485 47.495 11.485 48 13 C50.00016466 14.20882096 50.00016466 14.20882096 52 15 C51.67 15.66 51.34 16.32 51 17 C49.35 17 47.7 17 46 17 C45.67 18.98 45.34 20.96 45 23 C45.9075 23.268125 46.815 23.53625 47.75 23.8125 C50.72991834 24.90131632 52.68590359 25.86391101 55 28 C55 28.66 55 29.32 55 30 C51.1936543 29.32829194 47.64793184 28.27253436 44 27 C42.76374569 30.24516757 42 32.75509971 42 36.25 C42 37.1575 42 38.065 42 39 C40 41 40 41 37 41.25 C34 41 34 41 32 39 C31.875 35.375 31.875 35.375 32 32 C28.535 32.495 28.535 32.495 25 33 C25.04125 33.94875 25.0825 34.8975 25.125 35.875 C25 39 25 39 23 41 C20.0625 41.4375 20.0625 41.4375 17 41 C15.0625 38.75 15.0625 38.75 14 36 C14.3125 33.6875 14.3125 33.6875 15 32 C13.35 31.67 11.7 31.34 10 31 C9.84442627 30.19256348 9.68885254 29.38512695 9.52856445 28.55322266 C8.81254593 24.90560097 8.06302155 21.26567177 7.3125 17.625 C7.06822266 16.35398437 6.82394531 15.08296875 6.57226562 13.7734375 C6.31767578 12.56171875 6.06308594 11.35 5.80078125 10.1015625 C5.46300659 8.42054443 5.46300659 8.42054443 5.1184082 6.70556641 C4.24319101 3.77288621 4.24319101 3.77288621 1.38745117 2.61865234 C0.59959229 2.41449707 -0.1882666 2.2103418 -1 2 C-0.67 1.34 -0.34 0.68 0 0 Z M10 12 C10.33 13.65 10.66 15.3 11 17 C18.37653219 16.24984418 25.67831776 15.16558465 33 14 C33 13.67 33 13.34 33 13 C25.31068715 11.93940512 17.75493514 11.90071918 10 12 Z M29.4375 16.875 C27.51744141 17.14957031 27.51744141 17.14957031 25.55859375 17.4296875 C22.68679224 17.88993231 19.84505263 18.3993171 17 19 C17 19.33 17 19.66 17 20 C25.25 20.33 33.5 20.66 42 21 C42.33 19.68 42.66 18.36 43 17 C38.20791647 15.94825987 34.27781651 16.16189585 29.4375 16.875 Z M12 25 C12.33 26.32 12.66 27.64 13 29 C21.58 29 30.16 29 39 29 C39.33 27.68 39.66 26.36 40 25 C34.83822715 22.90873512 30.3480169 22.6964305 24.875 22.75 C24.07707031 22.74226563 23.27914062 22.73453125 22.45703125 22.7265625 C16.94557969 22.71908376 16.94557969 22.71908376 12 25 Z"
      fill="currentColor"
      transform="translate(9,9)"
    />
  </svg>
);

const Navbar = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const { cartCount } = useCart();
  const navigate = useNavigate();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [sliderGender, setSliderGender] = useState('men'); // 'men' | 'women' | 'kids' – Men selected by default, one always active

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= NAV_MOBILE_BREAKPOINT) setMenuOpen(false);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    setMenuOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (menuOpen) {
      document.body.classList.add('navbar-menu-open');
    } else {
      document.body.classList.remove('navbar-menu-open');
    }
    return () => document.body.classList.remove('navbar-menu-open');
  }, [menuOpen]);

  const handleLogout = () => {
    logout();
    axios.delete('/api/cart/clear').catch(() => {});
    navigate('/');
  };

  const closeMenu = () => {
    setMenuOpen(false);
    setSliderGender('men'); // reset so Men is selected when menu opens again
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    closeMenu();
    const trimmed = searchQuery.trim();
    if (trimmed) {
      navigate(`/products?search=${encodeURIComponent(trimmed)}`);
    } else {
      navigate('/products');
    }
  };

  /* Top bar: Home, Products, and Cart (icon only); Account, Log in, Sign up live in the menu */
  const navLinks = (
    <>
      <Link to="/" className="nav-link" onClick={closeMenu}>Home</Link>
      <Link to="/products" className="nav-link" onClick={closeMenu}>Products</Link>
      <Link to="/cart" className="nav-link nav-cart-link" title="Shopping Cart" onClick={closeMenu} aria-label={cartCount > 0 ? `${cartCount} items in cart` : 'Shopping Cart'}>
        <span className="nav-cart-icon" aria-hidden="true"><CartIcon /></span>
        {cartCount > 0 && <span className="cart-badge" aria-label={`${cartCount} items in cart`}>{cartCount}</span>}
      </Link>
    </>
  );

  /* Slider top: Account, Login/Logout only (Cart is in navbar) */
  const sliderTopLinks = (
    <div className="navbar-slider-top">
      {isAuthenticated ? (
        <>
          <Link to="/members" className="navbar-slider-link" onClick={closeMenu}>Account</Link>
          {user?.is_superadmin && (
            <Link to="/admin" className="navbar-slider-link" onClick={closeMenu}>Admin</Link>
          )}
          <button type="button" onClick={() => { handleLogout(); closeMenu(); }} className="navbar-slider-link navbar-slider-btn">
            Logout
          </button>
        </>
      ) : (
        <>
          <Link to="/login" className="navbar-slider-link" onClick={closeMenu}>Log In</Link>
          <Link to="/register" className="navbar-slider-link navbar-slider-register" onClick={closeMenu}>Sign Up</Link>
        </>
      )}
    </div>
  );

  return (
    <header className="navbar-wrapper">
      <nav className="navbar navbar-pill" role="navigation" aria-label="Main navigation">
        <div className="navbar-container">
          <button
            type="button"
            className="navbar-hamburger"
            aria-expanded={menuOpen}
            aria-controls="navbar-menu"
            aria-label={menuOpen ? 'Close menu' : 'Open menu'}
            onClick={() => setMenuOpen(!menuOpen)}
          >
            <span className="hamburger-bar" />
            <span className="hamburger-bar" />
            <span className="hamburger-bar" />
          </button>

          <form className="navbar-search-form" onSubmit={handleSearchSubmit} role="search">
            <div className="navbar-search-bar">
              <SearchIcon />
              <input
                type="search"
                className="navbar-search-input"
                placeholder="SEARCH"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                aria-label="Search products"
                autoComplete="off"
              />
            </div>
          </form>

          <div className="navbar-links" id="navbar-menu">
            {navLinks}
          </div>
        </div>

        {/* Dropdown expands downward from the nav; content starts below the nav bar */}
        <div
          className={`navbar-dropdown ${menuOpen ? 'navbar-dropdown--open' : ''}`}
          id="navbar-mobile"
          role="dialog"
          aria-label="Menu"
          aria-hidden={!menuOpen}
        >
          <div className="navbar-dropdown-inner">
            {sliderTopLinks}
            <div className="navbar-slider-filters">
              <span className="navbar-slider-filters-label">Shop by</span>
              <div className="navbar-slider-genders">
                {GENDERS.map((g) => (
                  <button
                    key={g.id}
                    type="button"
                    className={`navbar-slider-gender-btn ${sliderGender === g.id ? 'navbar-slider-gender-btn--active' : ''}`}
                    onClick={() => setSliderGender(g.id)}
                    aria-expanded={sliderGender === g.id}
                    aria-controls={`slider-categories-${g.id}`}
                  >
                    {g.label}
                  </button>
                ))}
              </div>
              {sliderGender && (
                <div id={`slider-categories-${sliderGender}`} className="navbar-slider-categories" role="region" aria-label={`${GENDERS.find((g) => g.id === sliderGender)?.label} categories`}>
                  {CLOTHING_CATEGORIES.map((cat) => {
                    const CategoryIcon = cat.Icon;
                    return (
                      <SpotlightCard
                        key={cat.id}
                        className="navbar-slider-category-spotlight"
                        spotlightColor="rgba(255, 255, 255, 0.4)"
                      >
                        <Link
                          to={`/products?category=${sliderGender}&clothing_category=${cat.id}`}
                          className="navbar-slider-category-row"
                          onClick={closeMenu}
                        >
                          <span className="navbar-slider-category-name">{cat.label}</span>
                          <span className="navbar-slider-category-icon" aria-hidden="true">
                            <CategoryIcon />
                          </span>
                        </Link>
                      </SpotlightCard>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      </nav>

      <div
        className={`navbar-overlay ${menuOpen ? 'navbar-overlay--open' : ''}`}
        aria-hidden="true"
        onClick={closeMenu}
      />
    </header>
  );
};

export default Navbar;
