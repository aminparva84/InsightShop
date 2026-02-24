import React from 'react';
import { Link } from 'react-router-dom';
import './InfoPages.css';
import './Returns.css';

const Returns = () => {
  return (
    <div className="info-page returns-page">
      <header className="info-page-hero">
        <h1>Returns & Refunds</h1>
        <p>We want you to love what you wear. If something isn't right, we're here to help.</p>
      </header>

      <div className="info-page-content">
        <div className="info-reassurance">
          We want you to love what you wear. Our return process is simple and stress-free.
        </div>

        <section className="info-section">
          <h2>Return Policy Overview</h2>
          <p>
            You may return most unworn, unwashed items in original condition with tags attached
            within our return window. We'll process your refund once we receive and inspect the
            return. Exchanges are subject to availability.
          </p>
        </section>

        <section className="info-section">
          <h2>Return Window</h2>
          <p>
            You have <strong>30 days</strong> from the delivery date to start a return. Items
            must be postmarked by the 30th day to be eligible.
          </p>
        </section>

        <section className="info-section">
          <h2>Eligibility</h2>
          <ul>
            <li>Item must be unworn, unwashed, and in original condition</li>
            <li>All original tags and packaging should be attached where possible</li>
            <li>Item must have been purchased from InsightShop (no third-party or resale)</li>
            <li>Proof of purchase may be required</li>
          </ul>
        </section>

        <section className="info-section">
          <h2>How to Start a Return</h2>
          <ol className="info-steps">
            <li>
              <span className="step-num">1</span>
              <div className="step-text">
                <strong>Log in to your account</strong>
                <p>Go to Order History and select the order containing the item you want to return.</p>
              </div>
            </li>
            <li>
              <span className="step-num">2</span>
              <div className="step-text">
                <strong>Select items and reason</strong>
                <p>Choose which items to return and provide a brief reason. This helps us improve.</p>
              </div>
            </li>
            <li>
              <span className="step-num">3</span>
              <div className="step-text">
                <strong>Print your label</strong>
                <p>We'll email you a prepaid return label. Pack the items securely and attach the label.</p>
              </div>
            </li>
            <li>
              <span className="step-num">4</span>
              <div className="step-text">
                <strong>Ship your return</strong>
                <p>Drop the package at any participating carrier location. Keep your receipt until the return is processed.</p>
              </div>
            </li>
          </ol>
        </section>

        <section className="info-section">
          <h2>Refund Processing Time</h2>
          <p>
            Once we receive your return, we'll inspect it and process your refund within
            <strong> 5–7 business days</strong>. Refunds are issued to the original payment
            method. Depending on your bank or card issuer, it may take an additional 3–10
            business days for the refund to appear on your statement.
          </p>
        </section>

        <section className="info-section">
          <h2>Exchanges</h2>
          <p>
            Need a different size or color? Start a return for the original item and place a
            new order for the replacement. This ensures you get the correct item quickly. If
            you prefer an exchange for the same item in a different size, contact us and we
            can assist when inventory is available.
          </p>
        </section>

        <section className="info-section">
          <h2>Non-Returnable Items</h2>
          <p>The following items cannot be returned:</p>
          <ul>
            <li>Final sale items (clearly marked at checkout)</li>
            <li>Swimwear (for hygiene reasons, unless tags are attached and unworn)</li>
            <li>Personal care or beauty products</li>
            <li>Gift cards</li>
          </ul>
        </section>

        <div className="info-cta-block">
          <p>Ready to start your return? Log in to your account to begin.</p>
          <Link to="/members" className="btn btn-primary">Start a Return</Link>
        </div>
      </div>
    </div>
  );
};

export default Returns;
