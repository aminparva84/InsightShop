import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import ProductCard from '../components/ProductCard';
import './Members.css';

const Members = () => {
  const { isAuthenticated, loading: authLoading, token } = useAuth();
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [suggestedProducts, setSuggestedProducts] = useState([]);
  const [allOrders, setAllOrders] = useState([]);

  useEffect(() => {
    if (authLoading || !token || !isAuthenticated) return;
    fetchDashboard();
    fetchAllOrders();
  }, [isAuthenticated, authLoading, token]);

  useEffect(() => {
    if (!loading && (allOrders.length > 0 || !dashboard || dashboard.recent_orders.length === 0)) {
      fetchSuggestions();
    }
  }, [allOrders, dashboard, loading]);

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

  const fetchAllOrders = async () => {
    try {
      const response = await axios.get('/api/members/orders');
      setAllOrders(response.data.orders || []);
    } catch (error) {
      console.error('Error fetching orders:', error);
    }
  };

  const fetchSuggestions = async () => {
    try {
      // Fetch general product suggestions for member area
      const response = await axios.get('/api/products?per_page=8');
      setSuggestedProducts(response.data.products || []);
    } catch (error) {
      console.error('Error fetching suggestions:', error);
    }
  };

  if (authLoading || !token || !isAuthenticated || loading) {
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
              <h2>Your Orders</h2>
              {allOrders.length > 0 ? (
                <div className="orders-list">
                  {allOrders.map(order => (
                    <div key={order.id} className="order-card">
                      <div className="order-header">
                        <span className="order-number">{order.order_number}</span>
                        <span className={`order-status ${order.status}`}>{order.status}</span>
                      </div>
                      <div className="order-items">
                        {order.items && order.items.map(item => (
                          <div key={item.id} className="order-item">
                            <span>{item.product?.name} x {item.quantity}</span>
                            <span>${item.subtotal.toFixed(2)}</span>
                          </div>
                        ))}
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

            {suggestedProducts.length > 0 && (
              <div className="suggestions-section">
                <h2>You Might Also Like</h2>
                <div className="suggestions-grid">
                  {suggestedProducts.map(product => (
                    <ProductCard key={product.id} product={product} />
                  ))}
                </div>
              </div>
            )}
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
  const [paymentLogs, setPaymentLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAllAttempts, setShowAllAttempts] = useState(false);

  useEffect(() => {
    fetchPayments();
  }, []);

  const fetchPayments = async () => {
    try {
      const response = await axios.get('/api/members/payments');
      setPayments(response.data.payments || []);
      setPaymentLogs(response.data.payment_logs || []);
    } catch (error) {
      console.error('Error fetching payments:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="spinner"></div>;

  const displayData = showAllAttempts ? paymentLogs : payments;
  const totalSpent = payments.filter(p => p.status === 'completed').reduce((sum, p) => sum + p.amount, 0);

  return (
    <div className="payments-tab">
      <div style={{marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
        <div>
          <h2 style={{margin: 0, marginBottom: '8px'}}>Payment History</h2>
          <p style={{margin: 0, color: '#6b7280', fontSize: '14px'}}>
            Total Spent: <strong>${totalSpent.toFixed(2)}</strong> | 
            Total Payments: <strong>{payments.length}</strong> | 
            Total Attempts: <strong>{paymentLogs.length}</strong>
          </p>
        </div>
        <label style={{display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer'}}>
          <input
            type="checkbox"
            checked={showAllAttempts}
            onChange={(e) => setShowAllAttempts(e.target.checked)}
          />
          <span>Show all attempts (including failed)</span>
        </label>
      </div>

      {displayData.length > 0 ? (
        <div className="payments-list">
          {displayData.map((item, index) => {
            const isLog = showAllAttempts;
            const transactionId = isLog ? (item.transaction_id || item.external_transaction_id || `LOG-${item.id}`) : item.transaction_id;
            
            return (
              <div key={isLog ? `log-${item.id}` : `payment-${item.id}`} className="payment-card">
                <div className="payment-header">
                  <span className="payment-id">{transactionId}</span>
                  <span className={`payment-status ${item.status}`}>{item.status}</span>
                </div>
                <div className="payment-details">
                  <p><strong>Amount:</strong> ${item.amount.toFixed(2)} {item.currency}</p>
                  <p><strong>Method:</strong> {item.payment_method.toUpperCase()}</p>
                  <p><strong>Date:</strong> {new Date(item.created_at).toLocaleString()}</p>
                  {isLog && item.card_last4 && (
                    <p><strong>Card:</strong> ****{item.card_last4} {item.card_brand ? `(${item.card_brand})` : ''}</p>
                  )}
                  {isLog && item.error_message && (
                    <p style={{color: '#dc2626', marginTop: '8px'}}><strong>Error:</strong> {item.error_message}</p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <p>No payments found</p>
      )}
    </div>
  );
};

export default Members;

