import React from 'react';
import logoImage from '../Gemini_Generated_Image_wlisx4wlisx4wlis.png';
import './Logo.css';

const Logo = () => {
  return (
    <div className="logo-container">
      <img 
        src={logoImage}
        alt="InsightShop Logo"
        className="logo-image"
      />
    </div>
  );
};

export default Logo;

