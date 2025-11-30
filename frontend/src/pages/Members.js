import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import './Members.css';

const Members = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    fetchDashboard();
  }, [isAuthenticated, navigate]);

  const fetchDashboard = async () => {
    try {
      const response = await axios.get('/api/members/dashboard');
      setDashboard(response.data);
    } catch (error) {
      console.error('Error fetching dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!isAuthenticated || loading) {
    return <div className="spinner"></div>;
  }

  return (
    <div className="members-page">
      <div className="container">
        <h1 className="page-title">My Account</h1>

        <div className="members-tabs">
          <button
            className={activeTab === 'dashboard' ? 'active' : ''}
            onClick={() => setActiveTab('dashboard')}
          >
            Dashboard
          </button>
          <button
            className={activeTab === 'orders' ? 'active' : ''}
            onClick={() => setActiveTab('orders')}
          >
            Orders
          </button>
          <button
            className={activeTab === 'payments' ? 'active' : ''}
            onClick={() => setActiveTab('payments')}
          >
            Payments
          </button>
        </div>

        {activeTab === 'dashboard' && dashboard && (
          <div className="dashboard-content">
            <div className="stats-grid">
              <div className="stat-card">
                <h3>Total Orders</h3>
                <p className="stat-value">{dashboard.statistics.total_orders}</p>
              </div>
              <div className="stat-card">
                <h3>Pending Orders</h3>
                <p className="stat-value">{dashboard.statistics.pending_orders}</p>
              </div>
              <div className="stat-card">
                <h3>Total Spent</h3>
                <p className="stat-value">${dashboard.statistics.total_spent.toFixed(2)}</p>
              </div>
              <div className="stat-card">
                <h3>Completed Orders</h3>
                <p className="stat-value">{dashboard.statistics.completed_orders}</p>
              </div>
            </div>

            <div className="recent-section">
              <h2>Recent Orders</h2>
              {dashboard.recent_orders.length > 0 ? (
                <div className="orders-list">
                  {dashboard.recent_orders.map(order => (
                    <div key={order.id} className="order-card">
                      <div className="order-header">
                        <span className="order-number">{order.order_number}</span>
                        <span className={`order-status ${order.status}`}>{order.status}</span>
                      </div>
                      <div className="order-details">
                        <p>Total: ${order.total.toFixed(2)}</p>
                        <p>Date: {new Date(order.created_at).toLocaleDateString()}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p>No orders yet</p>
              )}
            </div>
          </div>
        )}

        {activeTab === 'orders' && (
          <OrdersTab />
        )}

        {activeTab === 'payments' && (
          <PaymentsTab />
        )}
      </div>
    </div>
  );
};

const OrdersTab = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    try {
      const response = await axios.get('/api/members/orders');
      setOrders(response.data.orders);
    } catch (error) {
      console.error('Error fetching orders:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="spinner"></div>;

  return (
    <div className="orders-tab">
      {orders.length > 0 ? (
        <div className="orders-list">
          {orders.map(order => (
            <div key={order.id} className="order-card">
              <div className="order-header">
                <span className="order-number">{order.order_number}</span>
                <span className={`order-status ${order.status}`}>{order.status}</span>
              </div>
              <div className="order-items">
                {order.items.map(item => (
                  <div key={item.id} className="order-item">
                    <span>{item.product?.name} x {item.quantity}</span>
                    <span>${item.subtotal.toFixed(2)}</span>
                  </div>
                ))}
              </div>
              <div className="order-totals">
                <div className="order-total-row">
                  <span>Subtotal:</span>
                  <span>${order.subtotal.toFixed(2)}</span>
                </div>
                <div className="order-total-row">
                  <span>Tax:</span>
                  <span>${order.tax.toFixed(2)}</span>
                </div>
                <div className="order-total-row">
                  <span>Shipping:</span>
                  <span>${order.shipping_cost.toFixed(2)}</span>
                </div>
                <div className="order-total-row total">
                  <span>Total:</span>
                  <span>${order.total.toFixed(2)}</span>
                </div>
              </div>
              <div className="order-shipping">
                <p><strong>Shipping to:</strong></p>
                <p>{order.shipping_name}</p>
                <p>{order.shipping_address}</p>
                <p>{order.shipping_city}, {order.shipping_state} {order.shipping_zip}</p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p>No orders found</p>
      )}
    </div>
  );
};

const PaymentsTab = () => {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPayments();
  }, []);

  const fetchPayments = async () => {
    try {
      const response = await axios.get('/api/members/payments');
      setPayments(response.data.payments);
    } catch (error) {
      console.error('Error fetching payments:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="spinner"></div>;

  return (
    <div className="payments-tab">
      {payments.length > 0 ? (
        <div className="payments-list">
          {payments.map(payment => (
            <div key={payment.id} className="payment-card">
              <div className="payment-header">
                <span className="payment-id">{payment.transaction_id}</span>
                <span className={`payment-status ${payment.status}`}>{payment.status}</span>
              </div>
              <div className="payment-details">
                <p>Amount: ${payment.amount.toFixed(2)}</p>
                <p>Method: {payment.payment_method}</p>
                <p>Date: {new Date(payment.created_at).toLocaleDateString()}</p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p>No payments found</p>
      )}
    </div>
  );
};

export default Members;

