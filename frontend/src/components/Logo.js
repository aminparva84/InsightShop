import React from 'react';
import './Logo.css';

const Logo = () => {
  return (
    <div className="logo-container">
      <svg 
        className="logo-svg" 
        viewBox="0 0 100 100" 
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Hanger Shape - More realistic */}
        <path
          d="M50 15 L35 22 L35 45 Q35 55 45 60 L45 80 Q45 88 50 88 Q55 88 55 80 L55 60 Q65 55 65 45 L65 22 Z"
          fill="#d4af37"
          stroke="#1a2332"
          strokeWidth="2.5"
        />
        {/* Hook */}
        <path
          d="M50 15 Q50 8 42 8 Q34 8 34 15"
          fill="none"
          stroke="#1a2332"
          strokeWidth="3"
          strokeLinecap="round"
        />
        {/* AI Sparkle/Stars around hanger */}
        <g className="ai-sparkles">
          <circle cx="25" cy="20" r="2.5" fill="#d4af37" opacity="0.9">
            <animate attributeName="opacity" values="0.4;1;0.4" dur="2s" repeatCount="indefinite" />
          </circle>
          <circle cx="75" cy="20" r="2.5" fill="#d4af37" opacity="0.9">
            <animate attributeName="opacity" values="0.4;1;0.4" dur="2s" begin="0.5s" repeatCount="indefinite" />
          </circle>
          <circle cx="20" cy="40" r="2" fill="#d4af37" opacity="0.8">
            <animate attributeName="opacity" values="0.4;1;0.4" dur="2s" begin="1s" repeatCount="indefinite" />
          </circle>
          <circle cx="80" cy="40" r="2" fill="#d4af37" opacity="0.8">
            <animate attributeName="opacity" values="0.4;1;0.4" dur="2s" begin="1.5s" repeatCount="indefinite" />
          </circle>
          {/* AI symbol - small sparkle lines */}
          <path
            d="M25 20 L20 25 M75 20 L80 25"
            stroke="#d4af37"
            strokeWidth="1.5"
            opacity="0.7"
          />
        </g>
      </svg>
    </div>
  );
};

export default Logo;

