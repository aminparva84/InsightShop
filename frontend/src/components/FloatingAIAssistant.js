import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import AIChat from './AIChat';
import './FloatingAIAssistant.css';

const AI_HINTS = [
  "Ask me to find products by color, size, or style",
  "I can help you compare products by ID number",
  "Try: 'Show me blue shirts for men'",
  "Ask: 'Compare product 1, 2, 3' to see differences",
  "I know about fabrics, colors, and styling advice",
  "Say 'What should I wear for a business meeting?'",
  "I can help you find the perfect outfit for any occasion"
];

const FloatingAIAssistant = () => {
  const [showChat, setShowChat] = useState(false);
  const [currentHint, setCurrentHint] = useState(0);
  const [showHint, setShowHint] = useState(true);
  const location = useLocation();

  // Rotate hints every 5 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentHint(prev => (prev + 1) % AI_HINTS.length);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  // Hide hint when chat is open
  useEffect(() => {
    setShowHint(!showChat);
  }, [showChat]);

  // Don't show on certain pages
  const hideOnPages = ['/checkout', '/order-confirmation'];
  if (hideOnPages.includes(location.pathname)) {
    return null;
  }

  return (
    <>
      <div 
        className="floating-ai-assistant"
        onClick={() => setShowChat(true)}
        onMouseEnter={() => setShowHint(true)}
        onMouseLeave={() => {
          if (!showChat) {
            setTimeout(() => setShowHint(false), 2000);
          }
        }}
      >
        <div className="ai-button-icon">🤖</div>
        <div className="ai-button-text">AI Assistant</div>
        {showHint && (
          <div className="ai-hint-bubble">
            <div className="hint-arrow"></div>
            <p className="hint-text">{AI_HINTS[currentHint]}</p>
            <button 
              className="hint-close"
              onClick={(e) => {
                e.stopPropagation();
                setShowHint(false);
              }}
            >
              ×
            </button>
          </div>
        )}
      </div>

      {showChat && (
        <div className="ai-chat-fixed-container">
          <AIChat 
            onClose={() => setShowChat(false)} 
            onMinimize={() => setShowChat(false)}
          />
        </div>
      )}
    </>
  );
};

export default FloatingAIAssistant;

