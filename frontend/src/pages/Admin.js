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
      </div>
    </div>
  );
};

export default Admin;

