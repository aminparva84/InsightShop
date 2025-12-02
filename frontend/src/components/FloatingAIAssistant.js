import React, { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import AIChat from './AIChat';
import Logo from './Logo';
import './FloatingAIAssistant.css';

const AI_HINTS = [
  "Ask me to find products by color, size, or style",
  "I can help you compare products by ID number",
  "Try: 'Show me blue shirts for men'",
  "Ask: 'Compare product 1, 2, 3' to see differences",
  "I know about fabrics, colors, and styling advice",
  "Say 'What should I wear for a business meeting?'",
  "I can help you find the perfect outfit for any occasion",
  "Ask me about fashion matching and color coordination",
  "I can suggest complementary items for your cart",
  "Try: 'What colors match with blue?'",
  "Ask: 'Help me style this outfit'",
  "I can analyze images and find similar products"
];

const CART_AI_HINTS = [
  "I can suggest items that match what's in your cart",
  "Ask: 'What goes well with my cart items?'",
  "Try: 'Help me complete my outfit'",
  "I can suggest complementary colors and styles",
  "Ask me about fashion matching for your cart",
  "Say: 'What accessories match my cart?'",
  "I can help you find coordinating pieces",
  "Try: 'Suggest items that match my style'"
];

const FloatingAIAssistant = () => {
  const location = useLocation();
  const [showChat, setShowChat] = useState(false);
  const [currentHint, setCurrentHint] = useState(0);
  const [showHint, setShowHint] = useState(true);
  // Only show on cart page, so always use cart hints
  const hints = CART_AI_HINTS;
  const [chatSize, setChatSize] = useState(() => {
    // Load saved size from localStorage or use defaults
    const saved = localStorage.getItem('aiChatSize');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        return { width: 420, height: 630 }; // Added 30px to default height
      }
    }
    return { width: 420, height: 630 }; // Added 30px to default height
  });
  const [isResizing, setIsResizing] = useState(false);
  const chatContainerRef = useRef(null);

  // Rotate hints every 5 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentHint(prev => (prev + 1) % hints.length);
    }, 5000);
    return () => clearInterval(interval);
  }, [hints.length]);

  // Hide hint when chat is open
  useEffect(() => {
    setShowHint(!showChat);
  }, [showChat]);

  // Save chat size to localStorage when it changes
  useEffect(() => {
    if (showChat) {
      localStorage.setItem('aiChatSize', JSON.stringify(chatSize));
    }
  }, [chatSize, showChat]);

  // Handle resize
  useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (e) => {
      if (!chatContainerRef.current) return;

      const container = chatContainerRef.current;
      const rect = container.getBoundingClientRect();
      
      const newWidth = e.clientX - rect.left;
      const newHeight = e.clientY - rect.top;

      // Set minimum and maximum sizes
      const minWidth = 320;
      const maxWidth = window.innerWidth - 40;
      const minHeight = 400;
      const maxHeight = window.innerHeight - 40;

      setChatSize({
        width: Math.max(minWidth, Math.min(maxWidth, newWidth)),
        height: Math.max(minHeight, Math.min(maxHeight, newHeight))
      });
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing]);

  // Only show on cart page
  if (location.pathname !== '/cart') {
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
        <div className="ai-button-icon">
          <Logo size="small" />
        </div>
        <div className="ai-button-text">AI Assistant</div>
        {showHint && (
          <div className="ai-hint-bubble">
            <div className="hint-arrow"></div>
            <p className="hint-text">{hints[currentHint]}</p>
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
        <div 
          ref={chatContainerRef}
          className="ai-chat-fixed-container"
          style={{
            width: `${chatSize.width}px`,
            height: `${chatSize.height}px`
          }}
        >
          <AIChat 
            onClose={() => setShowChat(false)} 
            onMinimize={() => setShowChat(false)}
          />
          <div 
            className="resize-handle"
            onMouseDown={(e) => {
              e.preventDefault();
              setIsResizing(true);
            }}
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M8 12L12 8M12 12L16 8M4 16L8 12" stroke="#d4af37" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </div>
        </div>
      )}
    </>
  );
};

export default FloatingAIAssistant;

