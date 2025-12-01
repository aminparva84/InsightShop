import React from 'react';
import './PaymentIcons.css';

const PaymentIcons = ({ size = 'medium', showLabel = false }) => {
  // Using real payment icons from reliable CDN sources with actual brand logos
  const iconHeight = size === 'small' ? 24 : size === 'large' ? 40 : 32;
  
  const paymentMethods = [
    {
      name: 'Visa',
      title: 'Visa',
      // Using reliable CDN sources for payment logos
      imageUrl: 'https://logos-world.net/wp-content/uploads/2020/04/Visa-Logo.png',
      fallbackUrl: 'https://cdn.worldvectorlogo.com/logos/visa-11.svg',
      alt: 'Visa'
    },
    {
      name: 'Mastercard',
      title: 'Mastercard',
      imageUrl: 'https://logos-world.net/wp-content/uploads/2020/09/Mastercard-Logo.png',
      fallbackUrl: 'https://cdn.worldvectorlogo.com/logos/mastercard-6.svg',
      alt: 'Mastercard'
    },
    {
      name: 'American Express',
      title: 'American Express',
      imageUrl: 'https://logos-world.net/wp-content/uploads/2020/07/American-Express-Logo.png',
      fallbackUrl: 'https://cdn.worldvectorlogo.com/logos/american-express-4.svg',
      alt: 'American Express'
    },
    {
      name: 'Discover',
      title: 'Discover',
      imageUrl: 'https://logos-world.net/wp-content/uploads/2020/04/Discover-Logo.png',
      fallbackUrl: 'https://cdn.worldvectorlogo.com/logos/discover-2.svg',
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
                objectFit: 'contain',
                maxWidth: '100%'
              }}
              onError={(e) => {
                // Try fallback URL if primary fails
                if (e.target.src !== method.fallbackUrl) {
                  e.target.src = method.fallbackUrl;
                } else {
                  // If both fail, show a styled fallback
                  e.target.style.display = 'none';
                  const parent = e.target.parentElement;
                  if (!parent.querySelector('.payment-icon-fallback')) {
                    const fallback = document.createElement('div');
                    fallback.className = 'payment-icon-fallback';
                    fallback.textContent = method.name === 'American Express' ? 'AMEX' : method.name.toUpperCase().substring(0, method.name === 'Mastercard' ? 5 : 4);
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
                      font-size: ${iconHeight * 0.25}px;
                      font-weight: bold;
                      border-radius: 4px;
                      padding: 0 8px;
                    `;
                    parent.appendChild(fallback);
                  }
                }
              }}
            />
          </div>
        ))}
      </div>
    </div>
  );
};

export default PaymentIcons;

