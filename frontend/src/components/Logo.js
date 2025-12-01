import React from 'react';
import logoImage from '../logo.png';
import './Logo.css';

const Logo = ({ size = 'default', className = '' }) => {
  const sizeClass = size === 'small' ? 'logo-small' : size === 'large' ? 'logo-large' : '';
  
  return (
    <div className={`logo-container ${className}`}>
      <img 
        src={logoImage}
        alt="InsightShop Logo"
        className={`logo-image ${sizeClass}`}
      />
    </div>
  );
};

export default Logo;

