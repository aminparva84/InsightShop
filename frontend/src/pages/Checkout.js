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
  const [paymentMethod, setPaymentMethod] = useState('stripe'); // 'stripe' or 'chase'
  const [cardData, setCardData] = useState({
    cardNumber: '',
    expiryDate: '',
    cvv: '',
    cardholderName: ''
  });
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

            <h3 style={{marginTop: '30px', marginBottom: '20px', color: '#7c3aed'}}>Payment Information</h3>
            
            <div className="form-group">
              <label className="form-label">Payment Method *</label>
              <div style={{display: 'flex', gap: '16px', marginBottom: '20px'}}>
                <label style={{display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', padding: '12px', border: paymentMethod === 'stripe' ? '2px solid #7c3aed' : '2px solid #e5e7eb', borderRadius: '8px', flex: 1}}>
                  <input
                    type="radio"
                    name="payment_method"
                    value="stripe"
                    checked={paymentMethod === 'stripe'}
                    onChange={(e) => setPaymentMethod(e.target.value)}
                    style={{margin: 0}}
                  />
                  <span>💳 Credit/Debit Card (Stripe)</span>
                </label>
                <label style={{display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', padding: '12px', border: paymentMethod === 'chase' ? '2px solid #7c3aed' : '2px solid #e5e7eb', borderRadius: '8px', flex: 1, opacity: 0.5}}>
                  <input
                    type="radio"
                    name="payment_method"
                    value="chase"
                    checked={paymentMethod === 'chase'}
                    onChange={(e) => setPaymentMethod(e.target.value)}
                    disabled
                    style={{margin: 0}}
                  />
                  <span>🏦 Chase Payment (Coming Soon)</span>
                </label>
              </div>
            </div>

            {paymentMethod === 'stripe' && (
              <div style={{background: '#f9fafb', padding: '20px', borderRadius: '8px', marginBottom: '20px'}}>
                <div className="form-group">
                  <label className="form-label">Cardholder Name *</label>
                  <input
                    type="text"
                    value={cardData.cardholderName}
                    onChange={(e) => setCardData({...cardData, cardholderName: e.target.value})}
                    required
                    className="form-input"
                    placeholder="John Doe"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Card Number *</label>
                  <input
                    type="text"
                    value={cardData.cardNumber}
                    onChange={(e) => {
                      const value = e.target.value.replace(/\s/g, '').replace(/\D/g, '');
                      const formatted = value.match(/.{1,4}/g)?.join(' ') || value;
                      setCardData({...cardData, cardNumber: formatted});
                    }}
                    maxLength={19}
                    required
                    className="form-input"
                    placeholder="1234 5678 9012 3456"
                  />
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Expiry Date *</label>
                    <input
                      type="text"
                      value={cardData.expiryDate}
                      onChange={(e) => {
                        let value = e.target.value.replace(/\D/g, '');
                        if (value.length >= 2) {
                          value = value.slice(0, 2) + '/' + value.slice(2, 4);
                        }
                        setCardData({...cardData, expiryDate: value});
                      }}
                      maxLength={5}
                      required
                      className="form-input"
                      placeholder="MM/YY"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">CVV *</label>
                    <input
                      type="text"
                      value={cardData.cvv}
                      onChange={(e) => {
                        const value = e.target.value.replace(/\D/g, '').slice(0, 4);
                        setCardData({...cardData, cvv: value});
                      }}
                      maxLength={4}
                      required
                      className="form-input"
                      placeholder="123"
                    />
                  </div>
                </div>
                <small style={{color: '#6b7280', fontSize: '12px', display: 'block', marginTop: '8px'}}>
                  🔒 Your payment information is secure. We use Stripe for secure payment processing.
                </small>
              </div>
            )}

            {paymentMethod === 'chase' && (
              <div style={{background: '#fef3c7', padding: '20px', borderRadius: '8px', marginBottom: '20px', textAlign: 'center'}}>
                <p style={{color: '#92400e', margin: 0}}>
                  ⚠️ Chase Payment integration is coming soon. Please use Stripe for now.
                </p>
              </div>
            )}

            <button type="submit" disabled={loading || paymentMethod === 'chase'} className="btn btn-primary btn-submit">
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

