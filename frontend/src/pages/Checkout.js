import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useCart } from '../contexts/CartContext';
import { useAuth, REDIRECT_KEY } from '../contexts/AuthContext';
import { useNotification } from '../contexts/NotificationContext';
import PaymentIcons from '../components/PaymentIcons';
import './Checkout.css';

const Checkout = () => {
  const { cartItems, cartTotal, clearCart } = useCart();
  const { user, isAuthenticated, loading: authLoading } = useAuth();
  const { showError, showSuccess } = useNotification();
  const navigate = useNavigate();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      sessionStorage.setItem(REDIRECT_KEY, '/checkout');
      navigate('/login?redirect=/checkout', { state: { from: '/checkout' }, replace: true });
    }
  }, [authLoading, isAuthenticated, navigate]);

  // Pre-fill email from logged-in user
  useEffect(() => {
    if (user?.email) {
      setFormData(prev => ({ ...prev, email: user.email }));
    }
  }, [user]);
  const [loading, setLoading] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState('stripe'); // 'stripe', 'jpmorgan', or 'chase'
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
  const [shippingRates, setShippingRates] = useState([]);
  const [selectedShipping, setSelectedShipping] = useState(null);
  const [loadingRates, setLoadingRates] = useState(false);
  const [shippingError, setShippingError] = useState(null);
  const [validationErrors, setValidationErrors] = useState([]);
  const checkoutCompletedRef = useRef(false);

  // Scroll to top of page when validation errors are shown
  useEffect(() => {
    if (validationErrors.length > 0) {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, [validationErrors]);

  // Valid email format (RFC 5322 simplified)
  const isValidEmail = (email) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test((email || '').trim());

  // Full name: at least 2 chars, must contain at least one letter (allows spaces, hyphens, apostrophes)
  const isValidName = (name) => {
    const s = (name || '').trim();
    if (s.length < 2) return false;
    return /[a-zA-Z]/.test(s);
  };

  // Address: at least 5 chars, must contain at least one letter (street name)
  const isValidAddress = (address) => {
    const s = (address || '').trim();
    if (s.length < 5) return false;
    return /[a-zA-Z]/.test(s);
  };

  const validateForm = () => {
    const errors = [];

    // Email
    const emailTrimmed = (formData.email || '').trim();
    if (!emailTrimmed) {
      errors.push('Email is required.');
    } else if (!isValidEmail(emailTrimmed)) {
      errors.push('Please enter a valid email address (e.g. your@email.com).');
    }

    // Create account password (if opted in)
    if (!isAuthenticated && formData.create_account) {
      const pwd = (formData.password || '').trim();
      if (!pwd) {
        errors.push('Password is required when creating an account.');
      } else if (pwd.length < 6) {
        errors.push('Password must be at least 6 characters.');
      }
    }

    // Shipping - name and address with format validation
    const nameTrimmed = (formData.shipping_name || '').trim();
    if (!nameTrimmed) {
      errors.push('Full name is required.');
    } else if (!isValidName(formData.shipping_name)) {
      errors.push('Please enter a valid full name (at least 2 characters, including letters).');
    }
    const addressTrimmed = (formData.shipping_address || '').trim();
    if (!addressTrimmed) {
      errors.push('Address is required.');
    } else if (!isValidAddress(formData.shipping_address)) {
      errors.push('Please enter a valid address (at least 5 characters, including street name).');
    }
    if (!(formData.shipping_city || '').trim()) {
      errors.push('City is required.');
    }
    if (!(formData.shipping_state || '').trim()) {
      errors.push('State is required.');
    }
    if (!(formData.shipping_zip || '').trim()) {
      errors.push('ZIP code is required.');
    }

    // Card details when Stripe or J.P. Morgan is selected
    if (paymentMethod === 'stripe' || paymentMethod === 'jpmorgan') {
      if (!(cardData.cardholderName || '').trim()) {
        errors.push('Cardholder name is required.');
      }
      const cardNumber = (cardData.cardNumber || '').replace(/\s/g, '');
      if (!cardNumber) {
        errors.push('Card number is required.');
      } else if (cardNumber.length < 13 || cardNumber.length > 19) {
        errors.push('Please enter a valid card number.');
      }
      if (!(cardData.expiryDate || '').trim()) {
        errors.push('Expiry date is required.');
      } else {
        const [month, year] = cardData.expiryDate.split('/');
        if (!month || !year || month.length !== 2 || year.length !== 2) {
          errors.push('Expiry date must be in MM/YY format.');
        } else {
          const m = parseInt(month, 10);
          const y = parseInt(year, 10);
          if (m < 1 || m > 12 || isNaN(m)) {
            errors.push('Expiry month must be between 01 and 12.');
          }
          if (y < 0 || y > 99 || isNaN(y)) {
            errors.push('Expiry year must be a valid 2-digit year (YY).');
          }
        }
      }
      if (!(cardData.cvv || '').trim()) {
        errors.push('CVV is required.');
      } else if (cardData.cvv.length < 3 || cardData.cvv.length > 4) {
        errors.push('CVV must be 3 or 4 digits.');
      }
    }

    return errors;
  };

  // Don't render checkout form until auth is resolved; require login
  if (!authLoading && !isAuthenticated) {
    return null;
  }

  // Don't redirect when: just completed checkout, or currently submitting (order created, payment in progress)
  if (cartItems.length === 0 && !checkoutCompletedRef.current && !loading) {
    navigate('/cart');
    return null;
  }

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    if (validationErrors.length > 0) setValidationErrors([]);

    // Fetch shipping rates when ZIP code and state are entered
    if ((e.target.name === 'shipping_zip' || e.target.name === 'shipping_state') && 
        formData.shipping_zip && formData.shipping_state) {
      fetchShippingRates();
    }
  };
  
  const fetchShippingRates = async () => {
    if (!formData.shipping_zip || !formData.shipping_state) {
      return;
    }
    
    setLoadingRates(true);
    setShippingError(null);
    
    try {
      const response = await axios.post('/api/shipping/rates/quick', {
        zip: formData.shipping_zip,
        state: formData.shipping_state,
        country: formData.shipping_country || 'US'
      });
      
      if (response.data.rates && response.data.rates.length > 0) {
        setShippingRates(response.data.rates);
        // Auto-select cheapest option
        if (!selectedShipping) {
          setSelectedShipping(response.data.rates[0]);
        }
      } else {
        // Use fallback rates
        setShippingRates([{
          service: 'Standard Shipping',
          carrier: 'Standard',
          price: subtotal >= 50 ? 0 : 5,
          estimated_days: 5
        }]);
        setSelectedShipping({
          service: 'Standard Shipping',
          carrier: 'Standard',
          price: subtotal >= 50 ? 0 : 5,
          estimated_days: 5
        });
      }
      
      if (response.data.errors && response.data.errors.length > 0) {
        setShippingError('Some shipping rates unavailable, using standard rates');
      }
    } catch (error) {
      console.error('Error fetching shipping rates:', error);
      setShippingError('Unable to fetch shipping rates, using standard rates');
      // Use fallback
      const fallbackRate = {
        service: 'Standard Shipping',
        carrier: 'Standard',
        price: subtotal >= 50 ? 0 : 5,
        estimated_days: 5
      };
      setShippingRates([fallbackRate]);
      setSelectedShipping(fallbackRate);
    } finally {
      setLoadingRates(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errors = validateForm();
    if (errors.length > 0) {
      setValidationErrors(errors);
      return;
    }
    setValidationErrors([]);
    setLoading(true);

    try {
      // Include selected shipping method in order data
      const orderData = {
        ...formData,
        shipping_method: selectedShipping?.service || 'Standard Shipping',
        shipping_carrier: selectedShipping?.carrier || 'Standard',
        shipping_cost: shipping
      };
      
      // Create order (works for both authenticated and guest)
      const orderResponse = await axios.post('/api/orders', orderData);
      const order = orderResponse.data.order;

      // Process payment based on selected method
      if (paymentMethod === 'jpmorgan') {
        // Validate card data for J.P. Morgan
        if (!cardData.cardNumber || !cardData.expiryDate || !cardData.cvv) {
          throw new Error('Please fill in all card details');
        }

        // Parse expiry date (MM/YY format)
        const [expiryMonth, expiryYear] = cardData.expiryDate.split('/');
        if (!expiryMonth || !expiryYear) {
          throw new Error('Please enter a valid expiry date (MM/YY)');
        }

        // Convert 2-digit year to 4-digit year
        const fullYear = 2000 + parseInt(expiryYear);

        // Remove spaces from card number
        const cardNumber = cardData.cardNumber.replace(/\s/g, '');

        // Create J.P. Morgan payment
        const paymentResponse = await axios.post('/api/payments/jpmorgan/create-payment', {
          order_id: order.id,
          card_number: cardNumber,
          expiry_month: parseInt(expiryMonth),
          expiry_year: fullYear,
          capture_method: 'NOW',
          merchant_company_name: 'InsightShop',
          merchant_product_name: 'InsightShop Application',
          merchant_version: '1.0.0'
        });

        // Check if payment was successful
        if (paymentResponse.data.jpmorgan_response.responseStatus !== 'SUCCESS' || 
            paymentResponse.data.jpmorgan_response.responseCode !== 'APPROVED') {
          throw new Error(paymentResponse.data.jpmorgan_response.responseMessage || 'Payment was not approved');
        }

        showSuccess('Payment processed successfully!');
      } else {
        // Stripe payment flow
        const paymentResponse = await axios.post('/api/payments/create-intent', {
          order_id: order.id
        });

        // For now, just confirm the payment (in production, integrate Stripe Elements)
        if (paymentResponse.data.client_secret) {
          await axios.post('/api/payments/confirm', {
            payment_intent_id: paymentResponse.data.payment.payment_intent_id
          });
        }
      }

      checkoutCompletedRef.current = true;
      await clearCart();

      // Redirect to order confirmation (works for both authenticated and guest)
      navigate(`/order-confirmation?orderId=${order.id}&email=${encodeURIComponent(formData.email)}`);
    } catch (error) {
      console.error('Checkout error:', error);
      setValidationErrors([error.response?.data?.error || 'Checkout failed. Please try again.']);
      showError(error.response?.data?.error || 'Checkout failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const subtotal = cartTotal;
  const tax = subtotal * 0.08;
  const shipping = selectedShipping ? selectedShipping.price : (subtotal >= 50 ? 0 : 5);
  const total = subtotal + tax + shipping;

  return (
    <div className="checkout-page">
      <div className="container">
        <h1 className="page-title">Checkout</h1>

        <div className="checkout-layout">
          <form onSubmit={handleSubmit} className="checkout-form" noValidate>
            <h2>Checkout Information</h2>

            {validationErrors.length > 0 && (
              <div className="checkout-validation-errors" role="alert">
                <strong>Please fix the following:</strong>
                <ul>
                  {validationErrors.map((msg, i) => (
                    <li key={i}>{msg}</li>
                  ))}
                </ul>
              </div>
            )}
            
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
                    onChange={(e) => {
                      setFormData({...formData, create_account: e.target.checked});
                      if (validationErrors.length > 0) setValidationErrors([]);
                    }}
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
            
            {/* Shipping Options */}
            {formData.shipping_zip && formData.shipping_state && (
              <div className="form-group" style={{marginTop: '20px', padding: '20px', background: '#f9fafb', borderRadius: '8px'}}>
                <label className="form-label">Shipping Method *</label>
                {loadingRates ? (
                  <div style={{padding: '20px', textAlign: 'center', color: '#6b7280'}}>
                    Loading shipping rates...
                  </div>
                ) : shippingRates.length > 0 ? (
                  <div style={{display: 'flex', flexDirection: 'column', gap: '12px'}}>
                    {shippingRates.map((rate, index) => (
                      <label
                        key={index}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          padding: '16px',
                          border: selectedShipping?.service === rate.service ? '2px solid #7c3aed' : '2px solid #e5e7eb',
                          borderRadius: '8px',
                          cursor: 'pointer',
                          background: selectedShipping?.service === rate.service ? '#f3f4f6' : 'white',
                          transition: 'all 0.2s'
                        }}
                        onClick={() => setSelectedShipping(rate)}
                      >
                        <div style={{display: 'flex', alignItems: 'center', gap: '12px'}}>
                          <input
                            type="radio"
                            name="shipping_method"
                            value={rate.service}
                            checked={selectedShipping?.service === rate.service}
                            onChange={() => setSelectedShipping(rate)}
                            style={{margin: 0}}
                          />
                          <div>
                            <div style={{fontWeight: 600, color: '#1f2937'}}>
                              {rate.service} {rate.carrier && `(${rate.carrier})`}
                            </div>
                            {rate.estimated_days && (
                              <div style={{fontSize: '12px', color: '#6b7280'}}>
                                Estimated {rate.estimated_days} {rate.estimated_days === 1 ? 'day' : 'days'}
                              </div>
                            )}
                          </div>
                        </div>
                        <div style={{fontWeight: 700, color: '#1f2937', fontSize: '18px'}}>
                          ${rate.price.toFixed(2)}
                        </div>
                      </label>
                    ))}
                  </div>
                ) : (
                  <div style={{padding: '16px', background: '#fef3c7', borderRadius: '8px', color: '#92400e'}}>
                    {shippingError || 'Unable to load shipping rates. Standard shipping will be applied.'}
                  </div>
                )}
                {shippingError && shippingRates.length > 0 && (
                  <div style={{marginTop: '8px', fontSize: '12px', color: '#92400e'}}>
                    ⚠️ {shippingError}
                  </div>
                )}
              </div>
            )}

            <h3 style={{marginTop: '30px', marginBottom: '20px', color: '#7c3aed'}}>Payment Information</h3>
            
            <div style={{marginBottom: '24px', padding: '16px', background: '#f0f9ff', borderRadius: '8px', border: '1px solid #bfdbfe'}}>
              <PaymentIcons size="medium" showLabel={true} />
            </div>
            
            <div className="form-group">
              <label className="form-label">Payment Method *</label>
              <div style={{display: 'flex', gap: '16px', marginBottom: '20px', flexWrap: 'wrap'}}>
                <label style={{display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', padding: '12px', border: paymentMethod === 'stripe' ? '2px solid #7c3aed' : '2px solid #e5e7eb', borderRadius: '8px', flex: 1, minWidth: '200px'}}>
                  <input
                    type="radio"
                    name="payment_method"
                    value="stripe"
                    checked={paymentMethod === 'stripe'}
                    onChange={(e) => {
                      setPaymentMethod(e.target.value);
                      if (validationErrors.length > 0) setValidationErrors([]);
                    }}
                    style={{margin: 0}}
                  />
                  <span>💳 Credit/Debit Card (Stripe)</span>
                </label>
                <label style={{display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', padding: '12px', border: paymentMethod === 'jpmorgan' ? '2px solid #7c3aed' : '2px solid #e5e7eb', borderRadius: '8px', flex: 1, minWidth: '200px'}}>
                  <input
                    type="radio"
                    name="payment_method"
                    value="jpmorgan"
                    checked={paymentMethod === 'jpmorgan'}
                    onChange={(e) => {
                      setPaymentMethod(e.target.value);
                      if (validationErrors.length > 0) setValidationErrors([]);
                    }}
                    style={{margin: 0}}
                  />
                  <span>🏦 J.P. Morgan Payments</span>
                </label>
                <label style={{display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', padding: '12px', border: paymentMethod === 'chase' ? '2px solid #7c3aed' : '2px solid #e5e7eb', borderRadius: '8px', flex: 1, minWidth: '200px', opacity: 0.5}}>
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

            {(paymentMethod === 'stripe' || paymentMethod === 'jpmorgan') && (
              <div style={{background: '#f9fafb', padding: '20px', borderRadius: '8px', marginBottom: '20px'}}>
                <div className="form-group">
                  <label className="form-label">Cardholder Name *</label>
                  <input
                    type="text"
                    value={cardData.cardholderName}
                    onChange={(e) => {
                      setCardData({...cardData, cardholderName: e.target.value});
                      if (validationErrors.length > 0) setValidationErrors([]);
                    }}
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
                      if (validationErrors.length > 0) setValidationErrors([]);
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
                        if (validationErrors.length > 0) setValidationErrors([]);
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
                        if (validationErrors.length > 0) setValidationErrors([]);
                      }}
                      maxLength={4}
                      required
                      className="form-input"
                      placeholder="123"
                    />
                  </div>
                </div>
                <div style={{marginTop: '16px', paddingTop: '16px', borderTop: '1px solid #e5e7eb'}}>
                  <PaymentIcons size="small" showLabel={true} />
                </div>
                <small style={{color: '#6b7280', fontSize: '12px', display: 'block', marginTop: '8px'}}>
                  🔒 Your payment information is secure. 
                  {paymentMethod === 'stripe' 
                    ? ' We use Stripe for secure payment processing.'
                    : ' We use J.P. Morgan Payments for secure payment processing.'}
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
              {loading ? 'Processing Payment...' : 'Complete Order'}
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

