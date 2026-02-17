import React from 'react';
import './HeroChatPreview.css';

/**
 * Chatbot preview for the hero banner: sits left of banner-asset-2/3, under banner-asset-4.
 * Matches the design mockup: dark olive panel, "Ai" header + wavy line, sample bubbles, input.
 */
const HeroChatPreview = ({ onOpenChat }) => {
  return (
    <div
      className="hero-chat-preview"
      role="presentation"
      aria-hidden="true"
    >
      <div className="hero-chat-preview__panel">
        <header className="hero-chat-preview__header">
          <span className="hero-chat-preview__ai">Ai</span>
          <img
            src={`${process.env.PUBLIC_URL || ''}/images/asset-34.png`}
            alt=""
            className="hero-chat-preview__wavy"
            aria-hidden="true"
          />
        </header>
        <div className="hero-chat-preview__messages">
          <div className="hero-chat-preview__bubble hero-chat-preview__bubble--user">
            Help me discover fashion that fits my style.
          </div>
          <div className="hero-chat-preview__bubble hero-chat-preview__bubble--assistant">
            Sure! I will help you find the products you need!
          </div>
          <div className="hero-chat-preview__typing" aria-hidden="true">
            <span className="hero-chat-preview__typing-dot" />
            <span className="hero-chat-preview__typing-dot" />
            <span className="hero-chat-preview__typing-dot" />
          </div>
        </div>
        <div className="hero-chat-preview__input-wrap">
          <span className="hero-chat-preview__input-placeholder">type you question here</span>
        </div>
      </div>
      <button
        type="button"
        className="hero-chat-preview__cta-overlay"
        onClick={onOpenChat}
        aria-label="Open AI chat"
      />
    </div>
  );
};

export default HeroChatPreview;
