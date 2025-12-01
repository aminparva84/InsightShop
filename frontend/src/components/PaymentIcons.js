import React from 'react';
import './PaymentIcons.css';

const PaymentIcons = ({ size = 'medium', showLabel = false }) => {
  // Using real payment icons from reliable CDN sources
  const iconHeight = size === 'small' ? 24 : size === 'large' ? 40 : 32;
  
  const paymentMethods = [
    {
      name: 'Visa',
      title: 'Visa',
      imageUrl: 'https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/visa.svg',
      alt: 'Visa'
    },
    {
      name: 'Mastercard',
      title: 'Mastercard',
      imageUrl: 'https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/mastercard.svg',
      alt: 'Mastercard'
    },
    {
      name: 'American Express',
      title: 'American Express',
      imageUrl: 'https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/americanexpress.svg',
      alt: 'American Express'
    },
    {
      name: 'Discover',
      title: 'Discover',
      imageUrl: 'https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/discover.svg',
      alt: 'Discover'
    }
  ];
  
  return (
    <div className="payment-icons-container">
      {showLabel && (
        <div className="payment-icons-label">We accept:</div>
      )}
      <div className="payment-icons">
        {paymentMethods.map((method) => (
          <div 
            key={method.name} 
            className={`payment-icon ${method.name.toLowerCase().replace(' ', '-')}-icon`} 
            title={method.title}
          >
            <img 
              src={method.imageUrl} 
              alt={method.alt}
              height={iconHeight}
              style={{ 
                width: 'auto',
                height: `${iconHeight}px`,
                objectFit: 'contain'
              }}
              onError={(e) => {
                // Fallback to colored background with text if image fails to load
                e.target.style.display = 'none';
                const fallback = document.createElement('div');
                fallback.className = 'payment-icon-fallback';
                fallback.textContent = method.name === 'American Express' ? 'AMEX' : method.name.toUpperCase().substring(0, 4);
                fallback.style.cssText = `
                  width: ${iconHeight * 2.5}px;
                  height: ${iconHeight}px;
                  display: flex;
                  align-items: center;
                  justify-content: center;
                  background: ${method.name === 'Visa' ? '#1434CB' : 
                              method.name === 'Mastercard' ? '#EB001B' : 
                              method.name === 'American Express' ? '#006FCF' : '#FF6000'};
                  color: white;
                  font-size: ${iconHeight * 0.3}px;
                  font-weight: bold;
                  border-radius: 4px;
                `;
                e.target.parentElement.appendChild(fallback);
              }}
            />
          </div>
        ))}
      </div>
    </div>
  );
};

export default PaymentIcons;

