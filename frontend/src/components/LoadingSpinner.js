import React from 'react';
import './LoadingSpinner.css';

const LoadingSpinner = ({ message = 'Loading...' }) => {
  return (
    <div className="loading-spinner-container">
      <div className="loading-spinner-content">
        <div className="spinner"></div>
        {message && <p className="loading-message">{message}</p>}
      </div>
    </div>
  );
};

export default LoadingSpinner;

