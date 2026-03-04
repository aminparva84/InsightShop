import React from 'react';
import { Link } from 'react-router-dom';
import Logo from './Logo';
import './Footer.css';

/* Decorative curved line between footer content and bottom bar (matches section title style) */
const FooterDivider = () => (
  <div className="footer-divider" aria-hidden="true">
    <svg viewBox="0 0 200 32" preserveAspectRatio="none" aria-hidden="true">
      <path
        d="M 0 16 Q 50 0 100 16 Q 150 32 200 16"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  </div>
);

const Footer = () => {
  return (
    <footer className="footer">
      <div className="footer-container">
        <div className="footer-content">
          <div className="footer-section footer-brand-section">
            <Link to="/" className="footer-brand">
              <Logo />
              <span className="footer-brand-text">InsightShop</span>
            </Link>
            <p className="footer-description">
              Timeless style meets modern convenience. Quality apparel and thoughtful service—backed by AI-powered assistance when you need it.
            </p>
          </div>

          <div className="footer-section">
            <h3 className="footer-title">Shop</h3>
            <ul className="footer-links">
              <li><Link to="/">Home</Link></li>
              <li><Link to="/products">Products</Link></li>
              <li><Link to="/cart">Cart</Link></li>
            </ul>
          </div>

          <div className="footer-section">
            <h3 className="footer-title">Account</h3>
            <ul className="footer-links">
              <li><Link to="/login">Log In</Link></li>
              <li><Link to="/register">Register</Link></li>
              <li><Link to="/members">My Account</Link></li>
            </ul>
          </div>

          <div className="footer-section">
            <h3 className="footer-title">Support</h3>
            <ul className="footer-links">
              <li><Link to="/about">About Us</Link></li>
              <li><Link to="/contact">Contact</Link></li>
              <li><Link to="/shipping">Shipping</Link></li>
              <li><Link to="/returns">Returns</Link></li>
            </ul>
          </div>
        </div>

        <FooterDivider />

        <div className="footer-bottom">
          <p className="footer-copyright">&copy; {new Date().getFullYear()} InsightShop. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;


