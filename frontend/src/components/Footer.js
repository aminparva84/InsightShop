import React from 'react';
import { Link } from 'react-router-dom';
import Logo from './Logo';
import './Footer.css';

const Footer = () => {
  return (
    <footer className="footer">
      <div className="footer-container">
        <div className="footer-content">
          <div className="footer-section">
            <Link to="/" className="footer-brand">
              <Logo />
              <span className="footer-brand-text">InsightShop</span>
            </Link>
            <p className="footer-description">
              Your modern clothing store with AI-powered shopping assistance.
              Discover fashion that fits your style.
            </p>
          </div>

          <div className="footer-section">
            <h3 className="footer-title">Quick Links</h3>
            <ul className="footer-links">
              <li><Link to="/">Home</Link></li>
              <li><Link to="/products">Products</Link></li>
              <li><Link to="/cart">Shopping Cart</Link></li>
            </ul>
          </div>

          <div className="footer-section">
            <h3 className="footer-title">Account</h3>
            <ul className="footer-links">
              <li><Link to="/login">Login</Link></li>
              <li><Link to="/register">Register</Link></li>
              <li><Link to="/members">My Account</Link></li>
            </ul>
          </div>

          <div className="footer-section">
            <h3 className="footer-title">Support</h3>
            <ul className="footer-links">
              <li><a href="#about">About Us</a></li>
              <li><a href="#contact">Contact</a></li>
              <li><a href="#shipping">Shipping Info</a></li>
              <li><a href="#returns">Returns</a></li>
            </ul>
          </div>
        </div>

        <div className="footer-bottom">
          <p>&copy; {new Date().getFullYear()} InsightShop. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;


