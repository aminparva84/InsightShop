import React from 'react';
import {
  FaBox,
  FaTruck,
  FaGlobeAmericas,
  FaSearch,
  FaFileInvoiceDollar,
} from 'react-icons/fa';
import './InfoPages.css';
import './ShippingInfo.css';

const ShippingInfo = () => {
  return (
    <div className="info-page shipping-info-page">
      <header className="info-page-hero">
        <h1>Shipping Information</h1>
        <p>Clear, transparent shipping—so you know exactly when to expect your order.</p>
      </header>

      <div className="info-page-content">
        <section className="info-section">
          <h2>Processing Times</h2>
          <p>Orders are processed on business days (Monday – Friday, excluding holidays).</p>
          <div className="info-table-wrap">
            <table className="info-table">
              <thead>
                <tr>
                  <th>Order placed</th>
                  <th>Expected ship date</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Before 12:00 PM (EST)</td>
                  <td>Same business day</td>
                </tr>
                <tr>
                  <td>After 12:00 PM (EST)</td>
                  <td>Next business day</td>
                </tr>
                <tr>
                  <td>Weekends & holidays</td>
                  <td>Next business day</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section className="info-section">
          <h2>Shipping Methods</h2>
          <div className="info-icon-row">
            <div className="icon-wrap">
              <FaTruck />
            </div>
            <div className="text">
              <h3>Standard Shipping</h3>
              <p>Delivery in 5–7 business days. Tracked from dispatch.</p>
            </div>
          </div>
          <div className="info-icon-row">
            <div className="icon-wrap">
              <FaBox />
            </div>
            <div className="text">
              <h3>Express Shipping</h3>
              <p>Delivery in 2–3 business days. Available at checkout for eligible orders.</p>
            </div>
          </div>
        </section>

        <section className="info-section">
          <h2>Delivery Time Estimates</h2>
          <p>Times below are from the date your order ships (not from order date).</p>
          <div className="info-table-wrap">
            <table className="info-table">
              <thead>
                <tr>
                  <th>Region</th>
                  <th>Standard</th>
                  <th>Express</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Continental US</td>
                  <td>5–7 business days</td>
                  <td>2–3 business days</td>
                </tr>
                <tr>
                  <td>Alaska & Hawaii</td>
                  <td>7–10 business days</td>
                  <td>4–5 business days</td>
                </tr>
                <tr>
                  <td>Canada</td>
                  <td>7–14 business days</td>
                  <td>4–6 business days</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section className="info-section">
          <h2>Shipping Costs</h2>
          <div className="info-table-wrap">
            <table className="info-table">
              <thead>
                <tr>
                  <th>Method</th>
                  <th>Cost</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Standard (orders over $75)</td>
                  <td>Free</td>
                </tr>
                <tr>
                  <td>Standard (orders under $75)</td>
                  <td>$5.99</td>
                </tr>
                <tr>
                  <td>Express</td>
                  <td>$12.99</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section className="info-section">
          <h2>International Shipping</h2>
          <div className="info-icon-row">
            <div className="icon-wrap">
              <FaGlobeAmericas />
            </div>
            <div className="text">
              <p>
                We ship to select international destinations. Shipping costs and delivery times
                are calculated at checkout based on your country. Orders may be subject to customs
                clearance and local duties or taxes (see below).
              </p>
            </div>
          </div>
        </section>

        <section className="info-section">
          <h2>Tracking Information</h2>
          <div className="info-icon-row">
            <div className="icon-wrap">
              <FaSearch />
            </div>
            <div className="text">
              <p>
                Once your order ships, you'll receive an email with a tracking link. You can also
                view tracking in your account under Order History. If you don't see tracking updates
                within 24 hours of receiving the email, please contact us.
              </p>
            </div>
          </div>
        </section>

        <section className="info-section">
          <h2>Customs & Duties</h2>
          <div className="info-icon-row">
            <div className="icon-wrap">
              <FaFileInvoiceDollar />
            </div>
            <div className="text">
              <p>
                For international orders, customs fees, import duties, or taxes may apply and are
                the responsibility of the recipient. These charges are determined by your country's
                customs authority. We are not able to estimate or control these fees. If you have
                questions, we recommend contacting your local customs office.
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default ShippingInfo;
