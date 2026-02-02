import React, { useState } from 'react';
import './Logo.css';

// Logo is in public folder, so we reference it directly
const logoImage = '/logo.png';

const Logo = ({ size = 'default', className = '' }) => {
  const [imageError, setImageError] = useState(false);
  const sizeClass = size === 'small' ? 'logo-small' : size === 'large' ? 'logo-large' : '';
  
  const handleImageError = () => {
    setImageError(true);
  };
  
  return (
    <div className={`logo-container ${className}`}>
      {!imageError ? (
        <img 
          src={logoImage}
          alt="InsightShop Logo"
          className={`logo-image ${sizeClass}`}
          onError={handleImageError}
        />
      ) : (
        <div className={`logo-placeholder ${sizeClass}`}>
          <span className="logo-text">InsightShop</span>
        </div>
      )}
    </div>
  );
};

export default Logo;

