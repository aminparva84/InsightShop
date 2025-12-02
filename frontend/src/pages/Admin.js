import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import './Admin.css';

const Admin = () => {
  const { user, token } = useAuth();
  const navigate = useNavigate();
  const [fashionKB, setFashionKB] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('colors');
  const [users, setUsers] = useState([]);
  const [paymentLogs, setPaymentLogs] = useState([]);
  const [paymentLogsLoading, setPaymentLogsLoading] = useState(false);
  const [sales, setSales] = useState([]);
  const [upcomingEvents, setUpcomingEvents] = useState([]);
  const [salesLoading, setSalesLoading] = useState(false);
  const [showSaleForm, setShowSaleForm] = useState(false);
  const [editingSale, setEditingSale] = useState(null);
  const [newSale, setNewSale] = useState({
    name: '',
    description: '',
    sale_type: 'holiday',
    event_name: '',
    discount_percentage: '',
    start_date: '',
    end_date: '',
    product_filters: {},
    is_active: true
  });
  const [message, setMessage] = useState({ type: '', text: '' });

  useEffect(() => {
    // Check if user is admin
    if (!user || !user.is_admin) {
      navigate('/');
      return;
    }

    loadFashionKB();
    loadUsers();
    if (activeTab === 'payment-logs') {
      loadPaymentLogs();
    }
    if (activeTab === 'sales') {
      loadSales();
      loadUpcomingEvents();
    }
  }, [user, navigate, activeTab]);

  const loadFashionKB = async () => {
    try {
      const response = await axios.get('/api/admin/fashion-kb', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.data.success) {
        setFashionKB(response.data.data);
      }
    } catch (error) {
      console.error('Error loading fashion KB:', error);
      setMessage({ type: 'error', text: 'Failed to load fashion knowledge base' });
    } finally {
      setLoading(false);
    }
  };

  const loadUsers = async () => {
    try {
      const response = await axios.get('/api/admin/users', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.data.success) {
        setUsers(response.data.users);
      }
    } catch (error) {
      console.error('Error loading users:', error);
    }
  };

  const handleSaveKB = async () => {
    if (!fashionKB) return;

    setSaving(true);
    setMessage({ type: '', text: '' });

    try {
      const response = await axios.post('/api/admin/fashion-kb', {
        data: fashionKB
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.success) {
        setMessage({ type: 'success', text: response.data.message });
      }
    } catch (error) {
      console.error('Error saving fashion KB:', error);
      setMessage({ type: 'error', text: error.response?.data?.error || 'Failed to save fashion knowledge base' });
    } finally {
      setSaving(false);
    }
  };

  const handleAddColor = () => {
    const color = prompt('Enter color name:');
    const advice = prompt('Enter color matching advice:');
    
    if (color && advice) {
      const newKB = { ...fashionKB };
      if (!newKB.color_matching.by_color) {
        newKB.color_matching.by_color = {};
      }
      newKB.color_matching.by_color[color.toLowerCase()] = advice;
      setFashionKB(newKB);
    }
  };

  const handleRemoveColor = (color) => {
    if (window.confirm(`Remove color matching advice for ${color}?`)) {
      const newKB = { ...fashionKB };
      if (newKB.color_matching.by_color) {
        delete newKB.color_matching.by_color[color];
        setFashionKB(newKB);
      }
    }
  };

  const handleAddFabric = () => {
    const fabricName = prompt('Enter fabric name:');
    if (!fabricName) return;

    const description = prompt('Enter fabric description:');
    const bestFor = prompt('Enter best for:');
    const characteristics = prompt('Enter characteristics:');
    const care = prompt('Enter care instructions:');

    if (description && bestFor && characteristics) {
      const newKB = { ...fashionKB };
      if (!newKB.fabric_guide) {
        newKB.fabric_guide = {};
      }
      newKB.fabric_guide[fabricName.toLowerCase()] = {
        description,
        best_for: bestFor,
        characteristics,
        care: care || ''
      };
      setFashionKB(newKB);
    }
  };

  const handleRemoveFabric = (fabric) => {
    if (window.confirm(`Remove fabric information for ${fabric}?`)) {
      const newKB = { ...fashionKB };
      if (newKB.fabric_guide) {
        delete newKB.fabric_guide[fabric];
        setFashionKB(newKB);
      }
    }
  };

  const loadPaymentLogs = async () => {
    setPaymentLogsLoading(true);
    try {
      const response = await axios.get('/api/admin/payment-logs', {
        headers: { Authorization: `Bearer ${token}` },
        params: { per_page: 100 }
      });
      if (response.data.success) {
        setPaymentLogs(response.data.payment_logs || []);
      }
    } catch (error) {
      console.error('Error loading payment logs:', error);
      setMessage({ type: 'error', text: 'Failed to load payment logs' });
    } finally {
      setPaymentLogsLoading(false);
    }
  };

  const handleToggleAdmin = async (userId, currentStatus) => {
    try {
      const response = await axios.put(`/api/admin/users/${userId}/admin`, {
        is_admin: !currentStatus
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.success) {
        loadUsers();
        setMessage({ type: 'success', text: response.data.message });
      }
    } catch (error) {
      setMessage({ type: 'error', text: error.response?.data?.error || 'Failed to update admin status' });
    }
  };

  const loadSales = async () => {
    setSalesLoading(true);
    try {
      const response = await axios.get('/api/admin/sales', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.data.success) {
        setSales(response.data.sales);
      }
    } catch (error) {
      console.error('Error loading sales:', error);
      setMessage({ type: 'error', text: 'Failed to load sales' });
    } finally {
      setSalesLoading(false);
    }
  };

  const loadUpcomingEvents = async () => {
    try {
      const response = await axios.get('/api/admin/sales/events', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.data.success) {
        setUpcomingEvents({
          holidays: response.data.upcoming_holidays || [],
          current: response.data.current_events || []
        });
      }
    } catch (error) {
      console.error('Error loading events:', error);
    }
  };

  const handleCreateSale = async () => {
    if (!newSale.name || !newSale.discount_percentage || !newSale.start_date) {
      setMessage({ type: 'error', text: 'Please fill in all required fields' });
      return;
    }

    setSaving(true);
    try {
      const saleData = {
        ...newSale,
        discount_percentage: parseFloat(newSale.discount_percentage),
        product_filters: newSale.product_filters || {}
      };

      const response = await axios.post('/api/admin/sales', saleData, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.success) {
        setMessage({ type: 'success', text: 'Sale created successfully!' });
        setShowSaleForm(false);
        setNewSale({
          name: '',
          description: '',
          sale_type: 'holiday',
          event_name: '',
          discount_percentage: '',
          start_date: '',
          end_date: '',
          product_filters: {},
          is_active: true
        });
        loadSales();
      }
    } catch (error) {
      console.error('Error creating sale:', error);
      setMessage({ type: 'error', text: error.response?.data?.error || 'Failed to create sale' });
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateSale = async (saleId, updates) => {
    setSaving(true);
    try {
      const response = await axios.put(`/api/admin/sales/${saleId}`, updates, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.success) {
        setMessage({ type: 'success', text: 'Sale updated successfully!' });
        setEditingSale(null);
        loadSales();
      }
    } catch (error) {
      console.error('Error updating sale:', error);
      setMessage({ type: 'error', text: error.response?.data?.error || 'Failed to update sale' });
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteSale = async (saleId) => {
    if (!window.confirm('Are you sure you want to delete this sale?')) {
      return;
    }

    try {
      const response = await axios.delete(`/api/admin/sales/${saleId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.success) {
        setMessage({ type: 'success', text: 'Sale deleted successfully!' });
        loadSales();
      }
    } catch (error) {
      console.error('Error deleting sale:', error);
      setMessage({ type: 'error', text: error.response?.data?.error || 'Failed to delete sale' });
    }
  };

  const handleToggleSaleActive = async (sale) => {
    await handleUpdateSale(sale.id, { is_active: !sale.is_active });
  };

  const createThanksgivingSale = async () => {
    const today = new Date();
    const nextYear = new Date(today.getFullYear() + 1, 10, 1); // November next year
    const startDate = today.toISOString().split('T')[0];
    const endDate = nextYear.toISOString().split('T')[0];

    setNewSale({
      name: 'Thanksgiving Sale',
      description: 'Celebrate Thanksgiving with amazing deals!',
      sale_type: 'holiday',
      event_name: 'thanksgiving',
      discount_percentage: '40',
      start_date: startDate,
      end_date: endDate,
      product_filters: {},
      is_active: true
    });
    setShowSaleForm(true);
  };

  if (loading) {
    return <div className="admin-page"><div className="container">Loading...</div></div>;
  }

  if (!fashionKB) {
    return <div className="admin-page"><div className="container">Failed to load fashion knowledge base</div></div>;
  }

  return (
    <div className="admin-page">
      <div className="container">
        <h1>Admin Panel</h1>

        {message.text && (
          <div className={`admin-message ${message.type}`}>
            {message.text}
            <button onClick={() => setMessage({ type: '', text: '' })}>×</button>
          </div>
        )}

        <div className="admin-tabs">
          <button
            className={activeTab === 'fashion' ? 'active' : ''}
            onClick={() => setActiveTab('fashion')}
          >
            Fashion Knowledge Base
          </button>
          <button
            className={activeTab === 'users' ? 'active' : ''}
            onClick={() => setActiveTab('users')}
          >
            User Management
          </button>
          <button
            className={activeTab === 'payment-logs' ? 'active' : ''}
            onClick={() => {
              setActiveTab('payment-logs');
              loadPaymentLogs();
            }}
          >
            Payment Logs
          </button>
          <button
            className={activeTab === 'sales' ? 'active' : ''}
            onClick={() => {
              setActiveTab('sales');
              loadSales();
              loadUpcomingEvents();
            }}
          >
            Sales Management
          </button>
        </div>

        {activeTab === 'fashion' && (
          <div className="admin-section">
            <div className="admin-section-header">
              <h2>Fashion Knowledge Base Management</h2>
              <button onClick={handleSaveKB} disabled={saving} className="save-btn">
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>

            <div className="kb-tabs">
              <button
                className={activeTab === 'colors' ? 'active' : ''}
                onClick={() => setActiveTab('colors')}
              >
                Color Matching
              </button>
              <button
                className={activeTab === 'fabrics' ? 'active' : ''}
                onClick={() => setActiveTab('fabrics')}
              >
                Fabrics
              </button>
              <button
                className={activeTab === 'occasions' ? 'active' : ''}
                onClick={() => setActiveTab('occasions')}
              >
                Occasions
              </button>
            </div>

            {activeTab === 'colors' && (
              <div className="kb-section">
                <div className="kb-section-header">
                  <h3>Color Matching Advice</h3>
                  <button onClick={handleAddColor} className="add-btn">+ Add Color</button>
                </div>
                <div className="kb-items">
                  {fashionKB.color_matching?.by_color && Object.entries(fashionKB.color_matching.by_color).map(([color, advice]) => (
                    <div key={color} className="kb-item">
                      <div className="kb-item-header">
                        <strong>{color.charAt(0).toUpperCase() + color.slice(1)}</strong>
                        <button onClick={() => handleRemoveColor(color)} className="remove-btn">Remove</button>
                      </div>
                      <p>{advice}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'fabrics' && (
              <div className="kb-section">
                <div className="kb-section-header">
                  <h3>Fabric Information</h3>
                  <button onClick={handleAddFabric} className="add-btn">+ Add Fabric</button>
                </div>
                <div className="kb-items">
                  {fashionKB.fabric_guide && Object.entries(fashionKB.fabric_guide).map(([fabric, info]) => (
                    <div key={fabric} className="kb-item">
                      <div className="kb-item-header">
                        <strong>{fabric.charAt(0).toUpperCase() + fabric.slice(1)}</strong>
                        <button onClick={() => handleRemoveFabric(fabric)} className="remove-btn">Remove</button>
                      </div>
                      <p><strong>Description:</strong> {info.description}</p>
                      <p><strong>Best for:</strong> {info.best_for}</p>
                      <p><strong>Characteristics:</strong> {info.characteristics}</p>
                      {info.care && <p><strong>Care:</strong> {info.care}</p>}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'occasions' && (
              <div className="kb-section">
                <h3>Occasions</h3>
                <div className="kb-items">
                  {fashionKB.occasions && Object.entries(fashionKB.occasions).map(([occasion, advice]) => (
                    <div key={occasion} className="kb-item">
                      <strong>{occasion.replace('_', ' ').charAt(0).toUpperCase() + occasion.replace('_', ' ').slice(1)}</strong>
                      <p>{advice}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'payment-logs' && (
          <div className="admin-section">
            <h2>Payment Logs</h2>
            <p style={{color: '#6b7280', marginBottom: '24px'}}>
              All payment attempts (successful and failed) are logged here for monitoring and auditing purposes.
            </p>
            
            {paymentLogsLoading ? (
              <div>Loading payment logs...</div>
            ) : (
              <div className="payment-logs-table">
                <table>
                  <thead>
                    <tr>
                      <th>Date/Time</th>
                      <th>User</th>
                      <th>Order ID</th>
                      <th>Method</th>
                      <th>Amount</th>
                      <th>Status</th>
                      <th>Transaction ID</th>
                      <th>Card Info</th>
                      <th>Error</th>
                    </tr>
                  </thead>
                  <tbody>
                    {paymentLogs.length > 0 ? (
                      paymentLogs.map(log => (
                        <tr key={log.id}>
                          <td>{new Date(log.created_at).toLocaleString()}</td>
                          <td>{log.user?.email || 'Guest'}</td>
                          <td>{log.order_id || '-'}</td>
                          <td>{log.payment_method.toUpperCase()}</td>
                          <td>${log.amount.toFixed(2)} {log.currency}</td>
                          <td>
                            <span className={`payment-status ${log.status}`}>
                              {log.status}
                            </span>
                          </td>
                          <td style={{fontSize: '11px'}}>
                            {log.external_transaction_id || log.transaction_id || '-'}
                          </td>
                          <td>
                            {log.card_last4 ? `****${log.card_last4} ${log.card_brand || ''}` : '-'}
                          </td>
                          <td style={{color: '#dc2626', fontSize: '12px', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis'}}>
                            {log.error_message || '-'}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="9" style={{textAlign: 'center', padding: '40px'}}>
                          No payment logs found
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {activeTab === 'users' && (
          <div className="admin-section">
            <h2>User Management</h2>
            <div className="users-table">
              <table>
                <thead>
                  <tr>
                    <th>Email</th>
                    <th>Name</th>
                    <th>Verified</th>
                    <th>Admin</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map(u => (
                    <tr key={u.id}>
                      <td>{u.email}</td>
                      <td>{u.first_name} {u.last_name}</td>
                      <td>{u.is_verified ? '✓' : '✗'}</td>
                      <td>{u.is_admin ? '✓' : '✗'}</td>
                      <td>
                        <button
                          onClick={() => handleToggleAdmin(u.id, u.is_admin)}
                          className={u.is_admin ? 'remove-admin-btn' : 'make-admin-btn'}
                        >
                          {u.is_admin ? 'Remove Admin' : 'Make Admin'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'sales' && (
          <div className="admin-section">
            <div className="admin-section-header">
              <h2>Sales Management</h2>
              <button className="save-btn" onClick={() => setShowSaleForm(!showSaleForm)}>
                {showSaleForm ? 'Cancel' : '+ Create New Sale'}
              </button>
            </div>

            {/* Upcoming Events Section */}
            {upcomingEvents.holidays && upcomingEvents.holidays.length > 0 && (
              <div className="upcoming-events-section" style={{ marginBottom: '30px', padding: '20px', background: '#f8f9fa', borderRadius: '8px' }}>
                <h3>Upcoming Holidays & Events</h3>
                <p style={{ color: '#666', marginBottom: '15px' }}>Quick create sales for upcoming events:</p>
                <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                  {upcomingEvents.holidays.slice(0, 5).map((event, idx) => (
                    <button
                      key={idx}
                      className="save-btn"
                      style={{ fontSize: '12px', padding: '8px 16px' }}
                      onClick={() => {
                        const today = new Date();
                        const nextYear = new Date(today.getFullYear() + 1, 10, 1);
                        const eventDate = new Date(event.date);
                        const startDate = eventDate <= today ? today.toISOString().split('T')[0] : event.date;
                        const endDate = nextYear.toISOString().split('T')[0];
                        
                        setNewSale({
                          name: `${event.name.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} Sale`,
                          description: `Special ${event.name.replace('_', ' ')} sale!`,
                          sale_type: 'holiday',
                          event_name: event.name,
                          discount_percentage: '25',
                          start_date: startDate,
                          end_date: endDate,
                          product_filters: {},
                          is_active: true
                        });
                        setShowSaleForm(true);
                      }}
                    >
                      {event.name.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} ({event.days_until === 0 ? 'Today' : event.days_until === 1 ? 'Tomorrow' : `in ${event.days_until} days`})
                    </button>
                  ))}
                  <button
                    className="save-btn"
                    style={{ fontSize: '12px', padding: '8px 16px', background: '#dc2626' }}
                    onClick={createThanksgivingSale}
                  >
                    🦃 Create Thanksgiving Sale (40% off)
                  </button>
                </div>
              </div>
            )}

            {/* Create/Edit Sale Form */}
            {showSaleForm && (
              <div className="sale-form" style={{ marginBottom: '30px', padding: '20px', border: '1px solid #e0e0e0', borderRadius: '8px' }}>
                <h3>{editingSale ? 'Edit Sale' : 'Create New Sale'}</h3>
                <div style={{ display: 'grid', gap: '15px' }}>
                  <div>
                    <label>Sale Name *</label>
                    <input
                      type="text"
                      value={newSale.name}
                      onChange={(e) => setNewSale({ ...newSale, name: e.target.value })}
                      placeholder="e.g., Thanksgiving Sale"
                      style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                    />
                  </div>
                  <div>
                    <label>Description</label>
                    <textarea
                      value={newSale.description}
                      onChange={(e) => setNewSale({ ...newSale, description: e.target.value })}
                      placeholder="Sale description..."
                      style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px', minHeight: '60px' }}
                    />
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
                    <div>
                      <label>Discount Percentage *</label>
                      <input
                        type="number"
                        value={newSale.discount_percentage}
                        onChange={(e) => setNewSale({ ...newSale, discount_percentage: e.target.value })}
                        placeholder="40"
                        min="0"
                        max="100"
                        style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                      />
                    </div>
                    <div>
                      <label>Sale Type</label>
                      <select
                        value={newSale.sale_type}
                        onChange={(e) => setNewSale({ ...newSale, sale_type: e.target.value })}
                        style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                      >
                        <option value="holiday">Holiday</option>
                        <option value="seasonal">Seasonal</option>
                        <option value="event">Event</option>
                        <option value="general">General</option>
                      </select>
                    </div>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
                    <div>
                      <label>Start Date *</label>
                      <input
                        type="date"
                        value={newSale.start_date}
                        onChange={(e) => setNewSale({ ...newSale, start_date: e.target.value })}
                        style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                      />
                    </div>
                    <div>
                      <label>End Date (Informational - sales stay active until manually deactivated)</label>
                      <input
                        type="date"
                        value={newSale.end_date}
                        onChange={(e) => setNewSale({ ...newSale, end_date: e.target.value })}
                        style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                      />
                    </div>
                  </div>
                  <div>
                    <label>
                      <input
                        type="checkbox"
                        checked={newSale.is_active}
                        onChange={(e) => setNewSale({ ...newSale, is_active: e.target.checked })}
                        style={{ marginRight: '8px' }}
                      />
                      Active (Sale will be active until you uncheck this)
                    </label>
                  </div>
                  <div style={{ display: 'flex', gap: '10px' }}>
                    <button className="save-btn" onClick={handleCreateSale} disabled={saving}>
                      {saving ? 'Saving...' : editingSale ? 'Update Sale' : 'Create Sale'}
                    </button>
                    <button
                      className="save-btn"
                      style={{ background: '#6c757d' }}
                      onClick={() => {
                        setShowSaleForm(false);
                        setEditingSale(null);
                        setNewSale({
                          name: '',
                          description: '',
                          sale_type: 'holiday',
                          event_name: '',
                          discount_percentage: '',
                          start_date: '',
                          end_date: '',
                          product_filters: {},
                          is_active: true
                        });
                      }}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Sales List */}
            {salesLoading ? (
              <div>Loading sales...</div>
            ) : (
              <div className="sales-table">
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ background: '#f8f9fa' }}>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Name</th>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Discount</th>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Type</th>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Start Date</th>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Status</th>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sales.length === 0 ? (
                      <tr>
                        <td colSpan="6" style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
                          No sales created yet. Create your first sale above!
                        </td>
                      </tr>
                    ) : (
                      sales.map(sale => (
                        <tr key={sale.id} style={{ borderBottom: '1px solid #dee2e6' }}>
                          <td style={{ padding: '12px' }}>{sale.name}</td>
                          <td style={{ padding: '12px', fontWeight: 'bold', color: '#dc2626' }}>
                            {sale.discount_percentage}% OFF
                          </td>
                          <td style={{ padding: '12px', textTransform: 'capitalize' }}>{sale.sale_type}</td>
                          <td style={{ padding: '12px' }}>{new Date(sale.start_date).toLocaleDateString()}</td>
                          <td style={{ padding: '12px' }}>
                            <span style={{
                              padding: '4px 8px',
                              borderRadius: '4px',
                              background: sale.is_currently_active ? '#d4edda' : '#f8d7da',
                              color: sale.is_currently_active ? '#155724' : '#721c24',
                              fontSize: '12px',
                              fontWeight: 'bold'
                            }}>
                              {sale.is_currently_active ? 'ACTIVE' : 'INACTIVE'}
                            </span>
                          </td>
                          <td style={{ padding: '12px' }}>
                            <div style={{ display: 'flex', gap: '8px' }}>
                              <button
                                className="save-btn"
                                style={{ fontSize: '12px', padding: '6px 12px', background: sale.is_active ? '#dc2626' : '#28a745' }}
                                onClick={() => handleToggleSaleActive(sale)}
                              >
                                {sale.is_active ? 'Deactivate' : 'Activate'}
                              </button>
                              <button
                                className="save-btn"
                                style={{ fontSize: '12px', padding: '6px 12px', background: '#6c757d' }}
                                onClick={() => handleDeleteSale(sale.id)}
                              >
                                Delete
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Admin;

