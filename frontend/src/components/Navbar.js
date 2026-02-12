import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { useCart } from '../contexts/CartContext';
import Logo from './Logo';
import './Navbar.css';

const NAV_MOBILE_BREAKPOINT = 768;

const Navbar = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const { cartCount } = useCart();
  const navigate = useNavigate();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

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

  const closeMenu = () => setMenuOpen(false);

  const cartIcon = (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <path d="M3 3H5L5.4 5M7 13H17L21 5H5.4M7 13L5.4 5M7 13L4.7 15.3C4.3 15.7 4.6 16.5 5.1 16.5H17M17 13V17C17 18.1 17.9 19 19 19C20.1 19 21 18.1 21 17V13M9 19.5C9.8 19.5 10.5 20.2 10.5 21C10.5 21.8 9.8 22.5 9 22.5C8.2 22.5 7.5 21.8 7.5 21C7.5 20.2 8.2 19.5 9 19.5ZM20 19.5C20.8 19.5 21.5 20.2 21.5 21C21.5 21.8 20.8 22.5 20 22.5C19.2 22.5 18.5 21.8 18.5 21C18.5 20.2 19.2 19.5 20 19.5Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );

  const navLinks = (
    <>
      <Link to="/" className="nav-link" onClick={closeMenu}>Home</Link>
      <Link to="/products" className="nav-link" onClick={closeMenu}>Products</Link>
      <Link to="/cart" className="nav-link cart-link cart-icon-link" title="Shopping Cart" onClick={closeMenu}>
        {cartIcon}
        {cartCount > 0 && <span className="cart-badge" aria-label={`${cartCount} items in cart`}>{cartCount}</span>}
      </Link>
      {isAuthenticated ? (
        <>
          <Link to="/members" className="nav-link" onClick={closeMenu}>My Account</Link>
          {user?.is_superadmin && (
            <Link to="/admin" className="nav-link" onClick={closeMenu}>Admin</Link>
          )}
          <div className="user-menu">
            <span className="user-name">{user?.first_name}</span>
            <button type="button" onClick={() => { handleLogout(); closeMenu(); }} className="btn-logout">Logout</button>
          </div>
        </>
      ) : (
        <>
          <Link to="/login" className="nav-link" onClick={closeMenu}>Login</Link>
          <Link to="/register" className="btn btn-primary btn-nav" onClick={closeMenu}>Sign Up</Link>
        </>
      )}
    </>
  );

  return (
    <nav className="navbar" role="navigation" aria-label="Main navigation">
      <div className="navbar-container">
        <Link to="/" className="navbar-brand" onClick={closeMenu}>
          <Logo />
          <span className="brand-text">InsightShop</span>
        </Link>

        <div className="navbar-links" id="navbar-menu">
          {navLinks}
        </div>

        <button
          type="button"
          className="navbar-toggler"
          aria-expanded={menuOpen}
          aria-controls="navbar-menu"
          aria-label={menuOpen ? 'Close menu' : 'Open menu'}
          onClick={() => setMenuOpen(!menuOpen)}
        >
          <span className="toggler-bar" />
          <span className="toggler-bar" />
          <span className="toggler-bar" />
        </button>
      </div>

      <div
        className={`navbar-overlay ${menuOpen ? 'navbar-overlay--open' : ''}`}
        aria-hidden="true"
        onClick={closeMenu}
      />
      <div className={`navbar-mobile ${menuOpen ? 'navbar-mobile--open' : ''}`} id="navbar-mobile">
        <div className="navbar-mobile-header">
          <button
            type="button"
            className="navbar-mobile-back"
            aria-label="Close menu"
            onClick={closeMenu}
          >
            <span className="navbar-mobile-back-icon" aria-hidden="true">←</span>
            <span className="navbar-mobile-back-text">Back</span>
          </button>
        </div>
        <div className="navbar-mobile-links">
          {navLinks}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
