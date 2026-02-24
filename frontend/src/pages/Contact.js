import React, { useState } from 'react';
import axios from 'axios';
import {
  FaEnvelope,
  FaClock,
  FaQuestionCircle,
  FaFacebookF,
  FaInstagram,
  FaTwitter,
} from 'react-icons/fa';
import { Link } from 'react-router-dom';
import './InfoPages.css';
import './Contact.css';

const Contact = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    orderNumber: '',
    message: '',
  });
  const [submitted, setSubmitted] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSending(true);
    setError('');
    try {
      await axios.post('/api/contact', {
        name: formData.name,
        email: formData.email,
        order_number: formData.orderNumber || undefined,
        message: formData.message,
      });
      setSubmitted(true);
      setFormData({ name: '', email: '', orderNumber: '', message: '' });
    } catch (err) {
      const message = err.response?.data?.error || 'Something went wrong. Please try again.';
      setError(message);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="info-page contact-page">
      <header className="info-page-hero">
        <h1>Contact Us</h1>
        <p>Have a question or feedback? We'd love to hear from you.</p>
      </header>

      <div className="info-page-content wide">
        <div className="contact-layout">
          <div className="contact-form-col">
            <section className="info-section contact-form-section">
              <h2>Send a Message</h2>
              {submitted ? (
                <div className="contact-success">
                  <p>Thank you for reaching out. We usually respond within 24 hours.</p>
                </div>
              ) : (
                <form className="contact-form" onSubmit={handleSubmit}>
                  {error && (
                    <div className="alert alert-error" role="alert">
                      {error}
                    </div>
                  )}
                  <div className="form-group">
                    <label className="form-label" htmlFor="contact-name">Name</label>
                    <input
                      id="contact-name"
                      type="text"
                      name="name"
                      className="form-input"
                      value={formData.name}
                      onChange={handleChange}
                      required
                      placeholder="Your name"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label" htmlFor="contact-email">Email</label>
                    <input
                      id="contact-email"
                      type="email"
                      name="email"
                      className="form-input"
                      value={formData.email}
                      onChange={handleChange}
                      required
                      placeholder="your@email.com"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label" htmlFor="contact-order">
                      Order Number <span className="optional">(optional)</span>
                    </label>
                    <input
                      id="contact-order"
                      type="text"
                      name="orderNumber"
                      className="form-input"
                      value={formData.orderNumber}
                      onChange={handleChange}
                      placeholder="e.g. ORD-12345"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label" htmlFor="contact-message">Message</label>
                    <textarea
                      id="contact-message"
                      name="message"
                      className="form-input contact-textarea"
                      value={formData.message}
                      onChange={handleChange}
                      required
                      rows={5}
                      placeholder="How can we help?"
                    />
                  </div>
                  <button
                    type="submit"
                    className="btn btn-primary contact-submit"
                    disabled={sending}
                  >
                    {sending ? 'Sending...' : 'Send Message'}
                  </button>
                </form>
              )}
            </section>
          </div>

          <div className="contact-info-col">
            <section className="info-section contact-info-section">
              <h2>Get in Touch</h2>
              <p className="contact-reassurance">We usually respond within 24 hours.</p>

              <div className="contact-info-item">
                <span className="contact-info-icon">
                  <FaEnvelope />
                </span>
                <div>
                  <h3>Email</h3>
                  <a href="mailto:support@insightshop.com">support@insightshop.com</a>
                </div>
              </div>

              <div className="contact-info-item">
                <span className="contact-info-icon">
                  <FaClock />
                </span>
                <div>
                  <h3>Business Hours</h3>
                  <p>Monday – Friday: 9:00 AM – 6:00 PM (EST)</p>
                  <p>Saturday: 10:00 AM – 4:00 PM (EST)</p>
                  <p>Sunday: Closed</p>
                </div>
              </div>

              <div className="contact-info-item">
                <span className="contact-info-icon">
                  <FaQuestionCircle />
                </span>
                <div>
                  <h3>FAQ</h3>
                  <Link to="/shipping">Shipping & delivery</Link>
                  <br />
                  <Link to="/returns">Returns & refunds</Link>
                </div>
              </div>

              <div className="contact-social">
                <h3>Follow Us</h3>
                <div className="contact-social-icons">
                  <a href="https://facebook.com" target="_blank" rel="noopener noreferrer" aria-label="Facebook">
                    <FaFacebookF />
                  </a>
                  <a href="https://instagram.com" target="_blank" rel="noopener noreferrer" aria-label="Instagram">
                    <FaInstagram />
                  </a>
                  <a href="https://twitter.com" target="_blank" rel="noopener noreferrer" aria-label="Twitter">
                    <FaTwitter />
                  </a>
                </div>
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Contact;
