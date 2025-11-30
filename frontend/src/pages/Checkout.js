import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useCart } from '../contexts/CartContext';
import { useAuth } from '../contexts/AuthContext';
import { useNotification } from '../contexts/NotificationContext';
import './Checkout.css';

const Checkout = () => {
  const { cartItems, cartTotal, clearCart } = useCart();
  const { isAuthenticated } = useAuth();
  const { showError, showSuccess } = useNotification();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    shipping_name: '',
    shipping_address: '',
    shipping_city: '',
    shipping_state: '',
    shipping_zip: '',
    shipping_country: 'USA',
    shipping_phone: '',
    create_account: false,
    password: ''
  });

  if (cartItems.length === 0) {
    navigate('/cart');
    return null;
  }

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Create order (works for both authenticated and guest)
      const orderResponse = await axios.post('/api/orders', formData);
      const order = orderResponse.data.order;

      // Create payment intent
      const paymentResponse = await axios.post('/api/payments/create-intent', {
        order_id: order.id
      });

      // For now, just confirm the payment (in production, integrate Stripe Elements)
      if (paymentResponse.data.client_secret) {
        await axios.post('/api/payments/confirm', {
          payment_intent_id: paymentResponse.data.payment.payment_intent_id
        });
      }

      await clearCart();
      
      // Redirect to order confirmation (works for both authenticated and guest)
      navigate(`/order-confirmation?orderId=${order.id}&email=${encodeURIComponent(formData.email)}`);
    } catch (error) {
      console.error('Checkout error:', error);
      showError(error.response?.data?.error || 'Checkout failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const subtotal = cartTotal;
  const tax = subtotal * 0.08;
  const shipping = subtotal >= 50 ? 0 : 5;
  const total = subtotal + tax + shipping;

  return (
    <div className="checkout-page">
      <div className="container">
        <h1 className="page-title">Checkout</h1>

        <div className="checkout-layout">
          <form onSubmit={handleSubmit} className="checkout-form">
            <h2>Checkout Information</h2>
            
            <div className="form-group">
              <label className="form-label">Email Address *</label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
                className="form-input"
                placeholder="your@email.com"
              />
              <small style={{color: '#6b7280', fontSize: '12px'}}>We'll send your order confirmation here</small>
            </div>
            
            {!isAuthenticated && (
              <div className="form-group" style={{background: '#f0f9ff', padding: '16px', borderRadius: '8px', marginBottom: '20px'}}>
                <label style={{display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer'}}>
                  <input
                    type="checkbox"
                    name="create_account"
                    checked={formData.create_account}
                    onChange={(e) => setFormData({...formData, create_account: e.target.checked})}
                  />
                  <span>Create an account (optional) - Save your info for faster checkout next time</span>
                </label>
                {formData.create_account && (
                  <div style={{marginTop: '12px'}}>
                    <input
                      type="password"
                      name="password"
                      value={formData.password}
                      onChange={handleChange}
                      placeholder="Choose a password"
                      className="form-input"
                      minLength={6}
                      required={formData.create_account}
                    />
                  </div>
                )}
              </div>
            )}
            
            <h3 style={{marginTop: '30px', marginBottom: '20px', color: '#7c3aed'}}>Shipping Information</h3>
            
            <div className="form-group">
              <label className="form-label">Full Name *</label>
              <input
                type="text"
                name="shipping_name"
                value={formData.shipping_name}
                onChange={handleChange}
                required
                className="form-input"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Address *</label>
              <input
                type="text"
                name="shipping_address"
                value={formData.shipping_address}
                onChange={handleChange}
                required
                className="form-input"
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">City *</label>
                <input
                  type="text"
                  name="shipping_city"
                  value={formData.shipping_city}
                  onChange={handleChange}
                  required
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">State *</label>
                <input
                  type="text"
                  name="shipping_state"
                  value={formData.shipping_state}
                  onChange={handleChange}
                  required
                  className="form-input"
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">ZIP Code *</label>
                <input
                  type="text"
                  name="shipping_zip"
                  value={formData.shipping_zip}
                  onChange={handleChange}
                  required
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Phone</label>
                <input
                  type="tel"
                  name="shipping_phone"
                  value={formData.shipping_phone}
                  onChange={handleChange}
                  className="form-input"
                />
              </div>
            </div>

            <button type="submit" disabled={loading} className="btn btn-primary btn-submit">
              {loading ? 'Processing...' : 'Complete Order'}
            </button>
          </form>

          <div className="checkout-summary">
            <h2>Order Summary</h2>
            <div className="summary-items">
              {cartItems.map(item => (
                <div key={item.id} className="summary-item">
                  <span>{item.product?.name} x {item.quantity}</span>
                  <span>${item.subtotal.toFixed(2)}</span>
                </div>
              ))}
            </div>
            <div className="summary-totals">
              <div className="summary-row">
                <span>Subtotal:</span>
                <span>${subtotal.toFixed(2)}</span>
              </div>
              <div className="summary-row">
                <span>Tax:</span>
                <span>${tax.toFixed(2)}</span>
              </div>
              <div className="summary-row">
                <span>Shipping:</span>
                <span>{shipping === 0 ? 'Free' : `$${shipping.toFixed(2)}`}</span>
              </div>
              <div className="summary-row total">
                <span>Total:</span>
                <span>${total.toFixed(2)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Checkout;

