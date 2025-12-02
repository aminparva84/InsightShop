import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import axios from 'axios';
import LoadingSpinner from '../components/LoadingSpinner';
import './OrderConfirmation.css';

const OrderConfirmation = () => {
  const [searchParams] = useSearchParams();
  const orderId = searchParams.get('orderId') || searchParams.get('order');
  const email = searchParams.get('email');
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (orderId) {
      fetchOrder();
    } else {
      setLoading(false);
    }
  }, [orderId]);

  const fetchOrder = async () => {
    try {
      const response = await axios.get(`/api/orders/${orderId}`);
      setOrder(response.data.order);
    } catch (error) {
      console.error('Error fetching order:', error);
      // For guest orders, show success message even if we can't fetch details
      if (orderId) {
        setOrder({
          id: orderId,
          order_number: `ORD-${orderId}`,
          status: 'pending',
          message: 'Your order has been placed successfully!'
        });
      }
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading order details..." />;
  }

  if (!order) {
    return (
      <div className="order-confirmation-page">
        <div className="container">
          <h1>Order Not Found</h1>
          <Link to="/" className="btn btn-primary">Go Home</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="order-confirmation-page">
      <div className="container">
        <div className="confirmation-header">
          <div className="success-icon">✓</div>
          <h1>Order Confirmed!</h1>
          <p>Thank you for your purchase</p>
        </div>

        <div className="order-details">
          <div className="detail-card">
            <h3>Order Information</h3>
            <p><strong>Order Number:</strong> {order.order_number}</p>
            <p><strong>Order Date:</strong> {new Date(order.created_at).toLocaleDateString()}</p>
            <p><strong>Status:</strong> <span className="status-badge">{order.status}</span></p>
            {email && <p><strong>Confirmation Email:</strong> Sent to {email}</p>}
          </div>

          <div className="detail-card">
            <h3>Order Items</h3>
            <div className="order-items-list">
              {order.items.map(item => (
                <div key={item.id} className="order-item-row">
                  <span>{item.product?.name} x {item.quantity}</span>
                  <span>${item.subtotal.toFixed(2)}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="detail-card">
            <h3>Order Summary</h3>
            <div className="summary-row">
              <span>Subtotal:</span>
              <span>${order.subtotal.toFixed(2)}</span>
            </div>
            <div className="summary-row">
              <span>Tax:</span>
              <span>${order.tax.toFixed(2)}</span>
            </div>
            <div className="summary-row">
              <span>Shipping:</span>
              <span>${order.shipping_cost.toFixed(2)}</span>
            </div>
            <div className="summary-row total">
              <span>Total:</span>
              <span>${order.total.toFixed(2)}</span>
            </div>
          </div>

          <div className="detail-card">
            <h3>Shipping Address</h3>
            <p>{order.shipping_name}</p>
            <p>{order.shipping_address}</p>
            <p>{order.shipping_city}, {order.shipping_state} {order.shipping_zip}</p>
            <p>{order.shipping_country}</p>
          </div>
        </div>

        <div className="confirmation-footer">
          <p>An email confirmation has been sent to {email || 'your email'} with your order receipt.</p>
          <div className="action-buttons">
            <Link to="/products" className="btn btn-primary">Continue Shopping</Link>
            <Link to="/login" className="btn btn-outline">Create Account to Track Orders</Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OrderConfirmation;

