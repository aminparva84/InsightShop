import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import Footer from '../components/Footer';
import {
  HiOutlineSquares2X2,
  HiOutlineCube,
  HiOutlineArchiveBox,
  HiOutlineUsers,
  HiOutlineCurrencyDollar,
  HiOutlineShoppingCart,
  HiOutlineStar,
  HiOutlineCreditCard,
  HiOutlineBookOpen,
  HiOutlineCpuChip,
} from 'react-icons/hi2';
import './Admin.css';

// Default structure when fashion KB API fails so admin panel still renders
const DEFAULT_FASHION_KB = {
  color_matching: { basics: '', by_color: {} },
  style_advice: { fit: '', layering: '', proportions: '' },
  occasions: {},
  fabric_guide: {},
  dress_styles: { necklines: {}, dress_features: {}, men_styles: {} },
  styling_tips: { build_wardrobe: '', accessories: '', seasonal_transitions: '' }
};

const Admin = () => {
  const { user, token, loading: authLoading } = useAuth();
  const [fashionKB, setFashionKB] = useState(null);
  const [fashionKBLoadError, setFashionKBLoadError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [fashionSubTab, setFashionSubTab] = useState('colors');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [users, setUsers] = useState([]);
  const [paymentLogs, setPaymentLogs] = useState([]);
  const [paymentLogsLoading, setPaymentLogsLoading] = useState(false);
  const [sales, setSales] = useState([]);
  const [upcomingEvents, setUpcomingEvents] = useState([]);
  const [salesLoading, setSalesLoading] = useState(false);
  const [showSaleForm, setShowSaleForm] = useState(false);
  const [editingSale, setEditingSale] = useState(null);
  const [products, setProducts] = useState([]);
  const [productsLoading, setProductsLoading] = useState(false);
  const [showProductForm, setShowProductForm] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [reviewsLoading, setReviewsLoading] = useState(false);
  const [orders, setOrders] = useState([]);
  const [ordersLoading, setOrdersLoading] = useState(false);
  const [statistics, setStatistics] = useState(null);
  const [statisticsLoading, setStatisticsLoading] = useState(false);
  const [carts, setCarts] = useState([]);
  const [cartsLoading, setCartsLoading] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [showUserDetails, setShowUserDetails] = useState(false);
  const [showPasswordReset, setShowPasswordReset] = useState(false);
  const [newPassword, setNewPassword] = useState('');
  const [newProduct, setNewProduct] = useState({
    name: '',
    description: '',
    price: '',
    category: 'men',
    color: '',
    size: '',
    available_colors: [],
    available_sizes: [],
    fabric: '',
    clothing_type: '',
    dress_style: '',
    occasion: '',
    age_group: '',
    season: 'all_season',
    clothing_category: 'other',
    image_url: '',
    stock_quantity: 0,
    is_active: true
  });
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
  const [productValidationErrors, setProductValidationErrors] = useState([]);
  const [selectedOrderId, setSelectedOrderId] = useState(null);
  const [orderDetail, setOrderDetail] = useState(null);
  const [orderDetailLoading, setOrderDetailLoading] = useState(false);
  const [aiProviders, setAiProviders] = useState([]);
  const [aiSelectedProvider, setAiSelectedProvider] = useState('auto');
  const [aiAssistantLoading, setAiAssistantLoading] = useState(false);
  const [aiProviderSaving, setAiProviderSaving] = useState(null);
  const [aiProviderTesting, setAiProviderTesting] = useState(null);
  const [aiProviderKeyInputs, setAiProviderKeyInputs] = useState({});
  const productFormRef = useRef(null);

  useEffect(() => {
    if (authLoading || !token || !user || !user.is_superadmin) return;
    loadFashionKB();
    loadUsers();
    if (activeTab === 'dashboard') {
      loadStatistics();
    }
    if (activeTab === 'payment-logs') {
      loadPaymentLogs();
    }
    if (activeTab === 'sales') {
      loadSales();
      loadUpcomingEvents();
    }
    if (activeTab === 'users') {
      loadUsers();
    }
    if (activeTab === 'products') {
      loadProducts();
    }
    if (activeTab === 'reviews') {
      loadReviews();
    }
    if (activeTab === 'orders') {
      loadOrders();
    }
    if (activeTab === 'statistics') {
      loadStatistics();
    }
    if (activeTab === 'carts') {
      loadCarts();
    }
    if (activeTab === 'ai-assistant') {
      loadAiProviders();
    }
  }, [user, token, authLoading, activeTab]);

  // Fetch order detail when View is clicked in Orders tab
  useEffect(() => {
    if (!selectedOrderId || !token) {
      if (!selectedOrderId) setOrderDetail(null);
      return;
    }
    let cancelled = false;
    setOrderDetailLoading(true);
    setOrderDetail(null);
    axios.get(`/api/admin/orders/${selectedOrderId}`, {
      headers: { Authorization: `Bearer ${token}` }
    }).then(res => {
      if (!cancelled && res.data.success && res.data.order) setOrderDetail(res.data.order);
    }).catch(err => {
      if (!cancelled) setMessage({ type: 'error', text: err.response?.data?.error || 'Failed to load order details' });
    }).finally(() => {
      if (!cancelled) setOrderDetailLoading(false);
    });
    return () => { cancelled = true; };
  }, [selectedOrderId, token]);

  const loadFashionKB = async () => {
    setFashionKBLoadError(null);
    try {
      const response = await axios.get('/api/admin/fashion-kb', {
        headers: { Authorization: token ? `Bearer ${token}` : undefined }
      });
      if (response.data.success) {
        setFashionKB(response.data.data);
      }
    } catch (error) {
      console.error('Error loading fashion KB:', error);
      const errorMsg = error.response?.data?.error || error.message || 'Failed to load fashion knowledge base';
      setFashionKBLoadError(errorMsg);
      setMessage({ type: 'error', text: errorMsg });
      setFashionKB(DEFAULT_FASHION_KB);
    } finally {
      setLoading(false);
    }
  };

  const loadUsers = async () => {
    try {
      const response = await axios.get('/api/admin/users', {
        headers: { Authorization: token ? `Bearer ${token}` : undefined }
      });
      if (response.data.success) {
        setUsers(response.data.users);
      }
    } catch (error) {
      console.error('Error loading users:', error);
    }
  };

  const loadAiProviders = async () => {
    setAiAssistantLoading(true);
    try {
      const response = await axios.get('/api/admin/ai-assistant/providers', {
        headers: { Authorization: token ? `Bearer ${token}` : undefined }
      });
      if (response.data.success) {
        setAiProviders(response.data.providers || []);
        setAiSelectedProvider(response.data.selected_provider || 'auto');
      }
    } catch (error) {
      console.error('Error loading AI providers:', error);
      setMessage({ type: 'error', text: error.response?.data?.error || 'Failed to load AI providers' });
    } finally {
      setAiAssistantLoading(false);
    }
  };

  const handleSaveProviderKey = async (provider, apiKey) => {
    setAiProviderSaving(provider);
    setMessage({ type: '', text: '' });
    try {
      const response = await axios.patch(`/api/admin/ai-assistant/providers/${provider}`, { api_key: apiKey || '' }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.data.success) {
        setMessage({ type: 'success', text: 'API key saved.' });
        setAiProviderKeyInputs(prev => ({ ...prev, [provider]: '' }));
        loadAiProviders();
      }
    } catch (error) {
      setMessage({ type: 'error', text: error.response?.data?.error || 'Failed to save' });
    } finally {
      setAiProviderSaving(null);
    }
  };

  const handleToggleProviderEnabled = async (provider, currentEnabled) => {
    setAiProviderSaving(provider);
    setMessage({ type: '', text: '' });
    try {
      const response = await axios.patch(
        `/api/admin/ai-assistant/providers/${provider}`,
        { is_enabled: !currentEnabled },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (response.data.success) {
        setMessage({ type: 'success', text: currentEnabled ? 'Provider disabled.' : 'Provider enabled.' });
        loadAiProviders();
      }
    } catch (error) {
      setMessage({ type: 'error', text: error.response?.data?.error || 'Failed to update' });
    } finally {
      setAiProviderSaving(null);
    }
  };

  const handleTestProvider = async (provider) => {
    setAiProviderTesting(provider);
    setMessage({ type: '', text: '' });
    try {
      const response = await axios.post(`/api/admin/ai-assistant/providers/${provider}/test`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.data.success) {
        setMessage({ type: 'success', text: response.data.message || `Valid — ${response.data.latency_ms} ms` });
        loadAiProviders();
      } else {
        setMessage({ type: 'error', text: response.data.error || 'Test failed' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: error.response?.data?.error || 'Test failed' });
    } finally {
      setAiProviderTesting(null);
    }
  };

  const handleSelectedProviderChange = async (provider) => {
    setAiSelectedProvider(provider);
    try {
      await axios.put('/api/admin/ai-assistant/selected-provider', { provider }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMessage({ type: 'success', text: 'Default model updated.' });
    } catch (error) {
      setMessage({ type: 'error', text: error.response?.data?.error || 'Failed to update' });
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

  const handleRunSaleAutomation = async () => {
    if (!window.confirm('Run sale automation? This will activate sales based on their start dates and sync holiday sales.')) {
      return;
    }

    setSaving(true);
    try {
      const response = await axios.post('/api/admin/sales/run-automation', {}, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.success) {
        const results = response.data.results;
        let message = 'Sale automation completed successfully!\n\n';
        
        if (results.auto_activate) {
          message += `Activated: ${results.auto_activate.activated} sale(s)\n`;
        }
        if (results.sync_holidays) {
          message += `Created: ${results.sync_holidays.created} sale(s)\n`;
          message += `Updated: ${results.sync_holidays.updated} sale(s)\n`;
        }
        
        setMessage({ type: 'success', text: message });
        loadSales(); // Refresh sales list
      } else {
        setMessage({ type: 'error', text: response.data.error || 'Failed to run automation' });
      }
    } catch (error) {
      console.error('Error running sale automation:', error);
      setMessage({ type: 'error', text: error.response?.data?.error || 'Failed to run sale automation' });
    } finally {
      setSaving(false);
    }
  };

  const loadOrders = async () => {
    setOrdersLoading(true);
    try {
      const response = await axios.get('/api/admin/orders', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.data.success) {
        setOrders(response.data.orders);
      }
    } catch (error) {
      console.error('Error loading orders:', error);
      setMessage({ type: 'error', text: 'Failed to load orders' });
    } finally {
      setOrdersLoading(false);
    }
  };

  const handleUpdateOrderStatus = async (orderId, newStatus) => {
    if (!window.confirm(`Update order status to ${newStatus}?`)) {
      return;
    }

    setSaving(true);
    try {
      const response = await axios.put(`/api/admin/orders/${orderId}/status`, { status: newStatus }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.success) {
        setMessage({ type: 'success', text: `Order status updated to ${newStatus}` });
        loadOrders();
      }
    } catch (error) {
      console.error('Error updating order status:', error);
      setMessage({ type: 'error', text: error.response?.data?.error || 'Failed to update order status' });
    } finally {
      setSaving(false);
    }
  };

  const loadStatistics = async () => {
    setStatisticsLoading(true);
    try {
      const response = await axios.get('/api/admin/statistics', {
        headers: { Authorization: token ? `Bearer ${token}` : undefined }
      });
      if (response.data.success && response.data.statistics) {
        setStatistics(response.data.statistics);
      }
    } catch (error) {
      console.error('Error loading statistics:', error);
      setMessage({ type: 'error', text: error.response?.data?.error || 'Failed to load statistics' });
    } finally {
      setStatisticsLoading(false);
    }
  };

  const loadCarts = async () => {
    setCartsLoading(true);
    try {
      const response = await axios.get('/api/admin/carts', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.data.success) {
        setCarts(response.data.carts);
      }
    } catch (error) {
      console.error('Error loading carts:', error);
      setMessage({ type: 'error', text: 'Failed to load carts' });
    } finally {
      setCartsLoading(false);
    }
  };

  const handleDeleteUser = async (userId, userEmail) => {
    if (!window.confirm(`Are you sure you want to delete user ${userEmail}? This action cannot be undone.`)) {
      return;
    }

    setSaving(true);
    try {
      const response = await axios.delete(`/api/admin/users/${userId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.success) {
        setMessage({ type: 'success', text: `User ${userEmail} deleted successfully` });
        loadUsers();
      }
    } catch (error) {
      console.error('Error deleting user:', error);
      setMessage({ type: 'error', text: error.response?.data?.error || 'Failed to delete user' });
    } finally {
      setSaving(false);
    }
  };

  const handleViewUserDetails = async (userId) => {
    try {
      const response = await axios.get(`/api/admin/users/${userId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.data.success) {
        setSelectedUser(response.data.user);
        setShowUserDetails(true);
      }
    } catch (error) {
      console.error('Error loading user details:', error);
      setMessage({ type: 'error', text: 'Failed to load user details' });
    }
  };

  const handleResetPassword = async (userId) => {
    if (!newPassword || newPassword.length < 6) {
      setMessage({ type: 'error', text: 'Password must be at least 6 characters' });
      return;
    }

    if (!window.confirm('Are you sure you want to reset this user\'s password?')) {
      return;
    }

    setSaving(true);
    try {
      const response = await axios.put(`/api/admin/users/${userId}/password`, { new_password: newPassword }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.success) {
        setMessage({ type: 'success', text: 'Password reset successfully' });
        setShowPasswordReset(false);
        setNewPassword('');
      }
    } catch (error) {
      console.error('Error resetting password:', error);
      setMessage({ type: 'error', text: error.response?.data?.error || 'Failed to reset password' });
    } finally {
      setSaving(false);
    }
  };

  const handleClearUserCart = async (userId) => {
    if (!window.confirm('Are you sure you want to clear this user\'s cart?')) {
      return;
    }

    setSaving(true);
    try {
      const response = await axios.delete(`/api/admin/carts/user/${userId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.success) {
        setMessage({ type: 'success', text: 'Cart cleared successfully' });
        loadCarts();
      }
    } catch (error) {
      console.error('Error clearing cart:', error);
      setMessage({ type: 'error', text: error.response?.data?.error || 'Failed to clear cart' });
    } finally {
      setSaving(false);
    }
  };

  const loadProducts = async () => {
    setProductsLoading(true);
    try {
      const response = await axios.get('/api/admin/products', {
        headers: { Authorization: token ? `Bearer ${token}` : undefined },
        params: { per_page: 500 }
      });
      if (response.data.success) {
        setProducts(response.data.products || []);
      }
    } catch (error) {
      console.error('Error loading products:', error);
      setMessage({ type: 'error', text: 'Failed to load products' });
    } finally {
      setProductsLoading(false);
    }
  };

  const validateProductForm = (product) => {
    const errs = [];
    const name = (product.name || '').trim();
    if (!name) errs.push('Product name is required.');
    else if (name.length > 255) errs.push('Product name must be 255 characters or less.');
    const priceStr = product.price;
    if (priceStr === '' || priceStr === null || priceStr === undefined) {
      errs.push('Price is required.');
    } else {
      const p = parseFloat(priceStr);
      if (Number.isNaN(p)) errs.push('Price must be a valid number (e.g. 29.99).');
      else if (p < 0) errs.push('Price must be zero or greater.');
    }
    const cat = (product.category || '').trim().toLowerCase();
    if (!cat) errs.push('Gender is required.');
    else if (!['men', 'women', 'kids'].includes(cat)) errs.push('Gender must be Men, Women, or Kids.');
    const sq = product.stock_quantity;
    const sqNum = typeof sq === 'number' ? sq : parseInt(sq, 10);
    if (sq !== '' && sq !== null && sq !== undefined && (Number.isNaN(sqNum) || sqNum < 0)) {
      errs.push('Stock quantity must be a whole number zero or greater.');
    }
    return errs;
  };

  const handleCreateProduct = async () => {
    const errors = validateProductForm(newProduct);
    if (errors.length > 0) {
      setProductValidationErrors(errors);
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }
    setProductValidationErrors([]);
    setSaving(true);
    try {
      const payload = {
        ...newProduct,
        name: (newProduct.name || '').trim(),
        price: parseFloat(newProduct.price),
        stock_quantity: typeof newProduct.stock_quantity === 'number' ? newProduct.stock_quantity : parseInt(String(newProduct.stock_quantity), 10) || 0,
        description: newProduct.description || null,
        category: (newProduct.category || 'men').trim().toLowerCase(),
        clothing_category: newProduct.clothing_category || 'other',
        season: newProduct.season || 'all_season'
      };
      const response = await axios.post('/api/admin/products', payload, {
        headers: { Authorization: token ? `Bearer ${token}` : undefined }
      });

      if (response.data.success) {
        setMessage({ type: 'success', text: 'Product created successfully!' });
        setShowProductForm(false);
        setNewProduct({
          name: '',
          description: '',
          price: '',
          category: 'men',
          color: '',
          size: '',
          available_colors: [],
          available_sizes: [],
          fabric: '',
          clothing_type: '',
          dress_style: '',
          occasion: '',
          age_group: '',
          season: 'all_season',
          clothing_category: 'other',
          image_url: '',
          stock_quantity: 0,
          is_active: true
        });
        loadProducts();
      }
    } catch (error) {
      console.error('Error creating product:', error);
      const errMsg = error.response?.data?.error || 'Failed to create product';
      const errList = error.response?.data?.errors;
      if (Array.isArray(errList) && errList.length > 0) {
        setProductValidationErrors(errList);
      } else {
        setProductValidationErrors([errMsg]);
      }
      setMessage({ type: 'error', text: errMsg });
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } finally {
      setSaving(false);
    }
  };

  // Scroll to top when product validation errors are shown
  useEffect(() => {
    if (productValidationErrors.length > 0) {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, [productValidationErrors]);

  const handleUpdateProduct = async (productId, updates) => {
    const errors = validateProductForm(updates);
    if (errors.length > 0) {
      setProductValidationErrors(errors);
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }
    setProductValidationErrors([]);
    setSaving(true);
    try {
      const payload = {
        ...updates,
        name: (updates.name || '').trim(),
        price: parseFloat(updates.price),
        stock_quantity: typeof updates.stock_quantity === 'number' ? updates.stock_quantity : parseInt(String(updates.stock_quantity), 10) || 0,
        category: (updates.category || 'men').trim().toLowerCase(),
        clothing_category: updates.clothing_category || 'other',
        season: updates.season || 'all_season'
      };
      const response = await axios.put(`/api/admin/products/${productId}`, payload, {
        headers: { Authorization: token ? `Bearer ${token}` : undefined }
      });

      if (response.data.success) {
        setMessage({ type: 'success', text: 'Product updated successfully!' });
        setEditingProduct(null);
        loadProducts();
      }
    } catch (error) {
      console.error('Error updating product:', error);
      const errMsg = error.response?.data?.error || 'Failed to update product';
      const errList = error.response?.data?.errors;
      if (Array.isArray(errList) && errList.length > 0) {
        setProductValidationErrors(errList);
      } else {
        setProductValidationErrors([errMsg]);
      }
      setMessage({ type: 'error', text: errMsg });
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteProduct = async (productId) => {
    if (!window.confirm('Are you sure you want to delete this product?')) {
      return;
    }

    try {
      const response = await axios.delete(`/api/admin/products/${productId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.success) {
        setMessage({ type: 'success', text: 'Product deleted successfully!' });
        loadProducts();
      }
    } catch (error) {
      console.error('Error deleting product:', error);
      setMessage({ type: 'error', text: error.response?.data?.error || 'Failed to delete product' });
    }
  };

  const handleEditProduct = (product) => {
    setEditingProduct(product);
    setNewProduct({
      name: product.name || '',
      description: product.description || '',
      price: product.price || '',
      category: product.category || 'men',
      color: product.color || '',
      size: product.size || '',
      available_colors: product.available_colors || [],
      available_sizes: product.available_sizes || [],
      fabric: product.fabric || '',
      clothing_type: product.clothing_type || '',
      dress_style: product.dress_style || '',
      occasion: product.occasion || '',
      age_group: product.age_group || '',
      season: product.season || 'all_season',
      clothing_category: product.clothing_category || 'other',
      image_url: product.image_url || '',
      stock_quantity: product.stock_quantity || 0,
      is_active: product.is_active !== undefined ? product.is_active : true
    });
    setShowProductForm(true);
  };

  const addColorToProduct = (color) => {
    if (color && !newProduct.available_colors.includes(color)) {
      setNewProduct({
        ...newProduct,
        available_colors: [...newProduct.available_colors, color]
      });
    }
  };

  const removeColorFromProduct = (color) => {
    setNewProduct({
      ...newProduct,
      available_colors: newProduct.available_colors.filter(c => c !== color)
    });
  };

  const addSizeToProduct = (size) => {
    if (size && !newProduct.available_sizes.includes(size)) {
      setNewProduct({
        ...newProduct,
        available_sizes: [...newProduct.available_sizes, size]
      });
    }
  };

  const removeSizeFromProduct = (size) => {
    setNewProduct({
      ...newProduct,
      available_sizes: newProduct.available_sizes.filter(s => s !== size)
    });
  };

  const loadReviews = async () => {
    setReviewsLoading(true);
    try {
      const response = await axios.get('/api/admin/reviews', {
        headers: { Authorization: `Bearer ${token}` },
        params: { per_page: 100 }
      });
      if (response.data.success) {
        setReviews(response.data.reviews || []);
      }
    } catch (error) {
      console.error('Error loading reviews:', error);
      setMessage({ type: 'error', text: 'Failed to load reviews' });
    } finally {
      setReviewsLoading(false);
    }
  };

  const handleDeleteReview = async (reviewId) => {
    if (!window.confirm('Are you sure you want to delete this review?')) {
      return;
    }

    try {
      const response = await axios.delete(`/api/admin/reviews/${reviewId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.success) {
        setMessage({ type: 'success', text: 'Review deleted successfully!' });
        loadReviews();
      }
    } catch (error) {
      console.error('Error deleting review:', error);
      setMessage({ type: 'error', text: error.response?.data?.error || 'Failed to delete review' });
    }
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

  const createCyberMondaySale = async () => {
    const today = new Date();
    const nextYear = new Date(today.getFullYear() + 1, 10, 1); // November next year
    const startDate = today.toISOString().split('T')[0];
    const endDate = nextYear.toISOString().split('T')[0];

    setNewSale({
      name: 'Cyber Monday Sale',
      description: 'Get amazing deals on Cyber Monday! 45% off on all products!',
      sale_type: 'holiday',
      event_name: 'cyber_monday',
      discount_percentage: '45',
      start_date: startDate,
      end_date: endDate,
      product_filters: {},
      is_active: true
    });
    setShowSaleForm(true);
  };

  if (authLoading || !user || !user.is_superadmin || loading) {
    return <div className="admin-page"><div className="container">Loading...</div></div>;
  }

  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', Icon: HiOutlineSquares2X2 },
    { id: 'products', label: 'Products', Icon: HiOutlineCube },
    { id: 'orders', label: 'Orders', Icon: HiOutlineArchiveBox },
    { id: 'users', label: 'Users', Icon: HiOutlineUsers },
    { id: 'sales', label: 'Sales', Icon: HiOutlineCurrencyDollar },
    { id: 'carts', label: 'Carts', Icon: HiOutlineShoppingCart },
    { id: 'reviews', label: 'Reviews', Icon: HiOutlineStar },
    { id: 'payment-logs', label: 'Payments', Icon: HiOutlineCreditCard },
    { id: 'fashion', label: 'Fashion KB', Icon: HiOutlineBookOpen },
    { id: 'ai-assistant', label: 'AI Assistant', Icon: HiOutlineCpuChip },
  ];

  return (
    <div className="admin-page">
      {/* Mobile Overlay */}
      {sidebarOpen && (
        <div 
          className="sidebar-overlay"
          onClick={() => setSidebarOpen(false)}
          aria-label="Close sidebar"
        />
      )}
      <div className="admin-layout">
        {/* Sidebar Navigation */}
        <aside className={`admin-sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
          <div className="sidebar-header">
            <h2>Admin Center</h2>
            <button 
              className="sidebar-toggle"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              aria-label={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
            >
              {sidebarOpen ? '←' : '→'}
            </button>
          </div>
          <nav className="sidebar-nav" role="navigation" aria-label="Admin navigation">
            <ul>
              {menuItems.map(item => (
                <li key={item.id}>
                  <button
                    className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
                    onClick={() => {
                      setActiveTab(item.id);
                      if (item.id === 'dashboard') loadStatistics();
                      if (item.id === 'products') loadProducts();
                      if (item.id === 'orders') loadOrders();
                      if (item.id === 'sales') { loadSales(); loadUpcomingEvents(); }
                      if (item.id === 'reviews') loadReviews();
                      if (item.id === 'payment-logs') loadPaymentLogs();
                      if (item.id === 'carts') loadCarts();
                      if (item.id === 'ai-assistant') loadAiProviders();
                    }}
                    aria-current={activeTab === item.id ? 'page' : undefined}
                    title={item.label}
                  >
                    <span className="nav-icon"><item.Icon aria-hidden /></span>
                    {sidebarOpen && <span className="nav-label">{item.label}</span>}
                  </button>
                </li>
              ))}
            </ul>
          </nav>
          <div className="sidebar-footer">
            {sidebarOpen && (
              <div className="admin-info">
                <p><strong>Logged in as:</strong></p>
                <p>{user?.email}</p>
              </div>
            )}
          </div>
        </aside>

        {/* Main content + footer wrapper: responsive to sidebar width */}
        <div className={`admin-content-wrapper ${!sidebarOpen ? 'sidebar-closed' : ''}`}>
        <main className="admin-main">
          <div className="admin-header">
            <h1>
              {(() => {
                const item = menuItems.find(i => i.id === activeTab);
                const Icon = item?.Icon;
                return Icon ? <><Icon aria-hidden className="admin-header-icon" /> {item.label}</> : 'Admin Panel';
              })()}
            </h1>
            <div className="header-actions">
              <button 
                className="mobile-menu-toggle"
                onClick={() => setSidebarOpen(!sidebarOpen)}
                aria-label="Toggle menu"
              >
                ☰
              </button>
            </div>
          </div>

          {message.text && (
            <div className={`admin-message ${message.type}`} role="alert">
              <span>{message.text}</span>
              <button 
                onClick={() => setMessage({ type: '', text: '' })}
                aria-label="Close message"
              >
                ×
              </button>
            </div>
          )}

          {/* Dashboard View */}
          {activeTab === 'dashboard' && (
            <div className="admin-section">
              <div className="dashboard-grid">
                {statisticsLoading ? (
                  <div>Loading statistics...</div>
                ) : statistics ? (
                  <>
                    <div className="stat-card primary">
                      <div className="stat-icon">👥</div>
                      <div className="stat-content">
                        <h3>Total Users</h3>
                        <div className="stat-value">{statistics.users?.total ?? 0}</div>
                        <div className="stat-detail">
                          {statistics.users?.admins ?? 0} admins, {statistics.users?.active ?? 0} active
                        </div>
                      </div>
                    </div>

                    <div className="stat-card success">
                      <div className="stat-icon">🛍️</div>
                      <div className="stat-content">
                        <h3>Products</h3>
                        <div className="stat-value">{statistics.products?.active ?? 0}</div>
                        <div className="stat-detail">
                          {statistics.products?.low_stock ?? 0} low stock, {statistics.products?.out_of_stock ?? 0} out of stock
                        </div>
                      </div>
                    </div>

                    <div className="stat-card warning">
                      <div className="stat-icon">📦</div>
                      <div className="stat-content">
                        <h3>Orders Today</h3>
                        <div className="stat-value">{statistics.orders?.today ?? 0}</div>
                        <div className="stat-detail">
                          {statistics.orders?.pending ?? 0} pending, {statistics.orders?.processing ?? 0} processing
                        </div>
                      </div>
                    </div>

                    <div className="stat-card info">
                      <div className="stat-icon">💰</div>
                      <div className="stat-content">
                        <h3>Revenue (Month)</h3>
                        <div className="stat-value">${Number(statistics.revenue?.this_month ?? 0).toFixed(2)}</div>
                        <div className="stat-detail">
                          Today: ${Number(statistics.revenue?.today ?? 0).toFixed(2)}
                        </div>
                      </div>
                    </div>

                    <div className="dashboard-section">
                      <h2>Quick Stats</h2>
                      <div className="stats-grid">
                        <div className="stat-box">
                          <h4>Total Orders</h4>
                          <p className="stat-number">{statistics.orders?.total ?? 0}</p>
                        </div>
                        <div className="stat-box">
                          <h4>Active Sales</h4>
                          <p className="stat-number">{statistics.sales?.active ?? 0}</p>
                        </div>
                        <div className="stat-box">
                          <h4>Total Reviews</h4>
                          <p className="stat-number">{statistics.reviews?.total ?? 0}</p>
                        </div>
                        <div className="stat-box">
                          <h4>Total Revenue</h4>
                          <p className="stat-number">${Number(statistics.revenue?.total ?? 0).toFixed(2)}</p>
                        </div>
                      </div>
                    </div>

                    <div className="dashboard-section">
                      <h2>Order Status Breakdown</h2>
                      <div className="status-grid">
                        <div className="status-item pending">
                          <span className="status-label">Pending</span>
                          <span className="status-count">{statistics.orders?.pending ?? 0}</span>
                        </div>
                        <div className="status-item processing">
                          <span className="status-label">Processing</span>
                          <span className="status-count">{statistics.orders?.processing ?? 0}</span>
                        </div>
                        <div className="status-item shipped">
                          <span className="status-label">Shipped</span>
                          <span className="status-count">{statistics.orders?.shipped ?? 0}</span>
                        </div>
                        <div className="status-item delivered">
                          <span className="status-label">Delivered</span>
                          <span className="status-count">{statistics.orders?.delivered ?? 0}</span>
                        </div>
                      </div>
                    </div>

                    <div className="dashboard-section" style={{ background: '#f0f9ff', border: '1px solid #bae6fd', borderRadius: 8, padding: 16 }}>
                      <h2 style={{ marginTop: 0 }}>📋 Seeded Data</h2>
                      <p style={{ margin: '0 0 8px 0', color: '#0c4a6e' }}>
                        Users from <strong>seed_users.py</strong> (superadmin, demo users) and products from <strong>seed_products.py</strong> appear in the <strong>Users</strong> and <strong>Products</strong> tabs. Use the sidebar to view and manage them.
                      </p>
                    </div>

                    <div className="dashboard-section">
                      <h2>Quick Actions</h2>
                      <div className="quick-actions">
                        <button 
                          className="action-btn"
                          onClick={() => {
                            setActiveTab('products');
                            loadProducts();
                          }}
                        >
                          ➕ Add Product
                        </button>
                        <button 
                          className="action-btn"
                          onClick={() => {
                            setActiveTab('sales');
                            loadSales();
                            loadUpcomingEvents();
                          }}
                        >
                          💰 Create Sale
                        </button>
                        <button 
                          className="action-btn"
                          onClick={() => {
                            setActiveTab('orders');
                            loadOrders();
                          }}
                        >
                          📦 View Orders
                        </button>
                        <button 
                          className="action-btn"
                          onClick={handleRunSaleAutomation}
                          disabled={saving}
                        >
                          🔄 Run Automation
                        </button>
                      </div>
                    </div>
                  </>
                ) : (
                  <div>No statistics available</div>
                )}
              </div>
            </div>
          )}

          {/* Fashion Knowledge Base Section */}
          {activeTab === 'fashion' && (
            <div className="admin-section">
              <div className="admin-section-header">
                <h2>Fashion Knowledge Base Management</h2>
                <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
                  {fashionKBLoadError && (
                    <button type="button" className="btn btn-outline" onClick={() => { setLoading(true); loadFashionKB(); }}>
                      Retry load
                    </button>
                  )}
                  <button onClick={handleSaveKB} disabled={saving} className="save-btn">
                    {saving ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
              </div>
              {fashionKBLoadError && (
                <p style={{ marginBottom: 16, color: '#b91c1c', fontSize: 14 }}>Fashion KB failed to load: {fashionKBLoadError}</p>
              )}

              <div className="kb-tabs">
                <button
                  className={fashionSubTab === 'colors' ? 'active' : ''}
                  onClick={() => setFashionSubTab('colors')}
                  aria-label="Color matching advice"
                >
                  Color Matching
                </button>
                <button
                  className={fashionSubTab === 'fabrics' ? 'active' : ''}
                  onClick={() => setFashionSubTab('fabrics')}
                  aria-label="Fabric information"
                >
                  Fabrics
                </button>
                <button
                  className={fashionSubTab === 'occasions' ? 'active' : ''}
                  onClick={() => setFashionSubTab('occasions')}
                  aria-label="Occasion styling"
                >
                  Occasions
                </button>
              </div>

              {fashionSubTab === 'colors' && (
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

              {fashionSubTab === 'fabrics' && (
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

              {fashionSubTab === 'occasions' && (
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

          {/* Payment Logs Section */}
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

          {/* User Management Section */}
          {activeTab === 'users' && (
          <div className="admin-section">
            <h2>User Management</h2>
            <div className="users-table">
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ background: '#f8f9fa' }}>
                    <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Email</th>
                    <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Name</th>
                    <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Verified</th>
                    <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Admin</th>
                    <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map(u => (
                    <tr key={u.id} style={{ borderBottom: '1px solid #dee2e6' }}>
                      <td style={{ padding: '12px' }}>{u.email}</td>
                      <td style={{ padding: '12px' }}>{u.first_name} {u.last_name}</td>
                      <td style={{ padding: '12px' }}>{u.is_verified ? '✓' : '✗'}</td>
                      <td style={{ padding: '12px' }}>{u.is_admin ? '✓' : '✗'}</td>
                      <td style={{ padding: '12px' }}>
                        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                          {u.is_superadmin ? (
                            <span style={{ fontSize: '12px', padding: '6px 12px', color: '#666' }} title="Superadmin cannot be removed as admin">Superadmin</span>
                          ) : (
                            <button
                              onClick={() => handleToggleAdmin(u.id, u.is_admin)}
                              className={u.is_admin ? 'remove-admin-btn' : 'make-admin-btn'}
                              style={{ fontSize: '12px', padding: '6px 12px' }}
                            >
                              {u.is_admin ? 'Remove Admin' : 'Make Admin'}
                            </button>
                          )}
                          <button
                            onClick={() => handleViewUserDetails(u.id)}
                            className="save-btn"
                            style={{ fontSize: '12px', padding: '6px 12px', background: '#3b82f6' }}
                          >
                            View Details
                          </button>
                          <button
                            onClick={() => {
                              setSelectedUser(u);
                              setShowPasswordReset(true);
                            }}
                            className="save-btn"
                            style={{ fontSize: '12px', padding: '6px 12px', background: '#f59e0b' }}
                          >
                            Reset Password
                          </button>
                          {!u.is_superadmin && (
                            <button
                              onClick={() => handleDeleteUser(u.id, u.email)}
                              className="save-btn"
                              style={{ fontSize: '12px', padding: '6px 12px', background: '#dc2626' }}
                              disabled={saving}
                            >
                              Delete
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {showUserDetails && selectedUser && (
              <div style={{ marginTop: '30px', padding: '20px', background: '#f8f9fa', borderRadius: '8px' }}>
                <h3>User Details: {selectedUser.email}</h3>
                <div style={{ display: 'grid', gap: '10px', marginTop: '15px' }}>
                  <p><strong>Name:</strong> {selectedUser.first_name} {selectedUser.last_name}</p>
                  <p><strong>Email:</strong> {selectedUser.email}</p>
                  <p><strong>Verified:</strong> {selectedUser.is_verified ? 'Yes' : 'No'}</p>
                  <p><strong>Admin:</strong> {selectedUser.is_admin ? 'Yes' : 'No'}</p>
                  <p><strong>Superadmin:</strong> {selectedUser.is_superadmin ? 'Yes' : 'No'}</p>
                  <p><strong>Orders:</strong> {selectedUser.order_count || 0}</p>
                  <p><strong>Cart Items:</strong> {selectedUser.cart_item_count || 0}</p>
                </div>
                <button
                  onClick={() => {
                    setShowUserDetails(false);
                    setSelectedUser(null);
                  }}
                  className="save-btn"
                  style={{ marginTop: '15px', background: '#6c757d' }}
                >
                  Close
                </button>
              </div>
            )}

            {showPasswordReset && selectedUser && (
              <div style={{ marginTop: '30px', padding: '20px', background: '#f8f9fa', borderRadius: '8px' }}>
                <h3>Reset Password for {selectedUser.email}</h3>
                <div style={{ marginTop: '15px' }}>
                  <label style={{ display: 'block', marginBottom: '5px' }}>New Password (min 6 characters):</label>
                  <input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    style={{ width: '300px', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                    placeholder="Enter new password"
                  />
                </div>
                <div style={{ marginTop: '15px', display: 'flex', gap: '10px' }}>
                  <button
                    onClick={() => handleResetPassword(selectedUser.id)}
                    className="save-btn"
                    disabled={saving || !newPassword || newPassword.length < 6}
                  >
                    {saving ? 'Resetting...' : 'Reset Password'}
                  </button>
                  <button
                    onClick={() => {
                      setShowPasswordReset(false);
                      setSelectedUser(null);
                      setNewPassword('');
                    }}
                    className="save-btn"
                    style={{ background: '#6c757d' }}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

          {/* Sales Management Section */}
          {activeTab === 'sales' && (
          <div className="admin-section">
            <div className="admin-section-header">
              <h2>Sales Management</h2>
              <div style={{ display: 'flex', gap: '10px' }}>
                <button 
                  className="save-btn" 
                  onClick={handleRunSaleAutomation}
                  disabled={saving}
                  style={{ 
                    background: '#10b981', 
                    fontSize: '14px',
                    padding: '10px 20px'
                  }}
                  title="Run sale automation to activate sales based on dates and sync holiday sales"
                >
                  {saving ? 'Running...' : '🔄 Run Sale Automation'}
                </button>
                <button className="save-btn" onClick={() => setShowSaleForm(!showSaleForm)}>
                  {showSaleForm ? 'Cancel' : '+ Create New Sale'}
                </button>
              </div>
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
                  <button
                    className="save-btn"
                    style={{ fontSize: '12px', padding: '8px 16px', background: '#1a2332' }}
                    onClick={createCyberMondaySale}
                  >
                    💻 Create Cyber Monday Sale (45% off)
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

          {/* Product Management Section */}
          {activeTab === 'products' && (
          <div className="admin-section" ref={productFormRef}>
            <div className="admin-section-header">
              <h2>Product Management</h2>
              <button className="save-btn" onClick={() => {
                setShowProductForm(!showProductForm);
                setProductValidationErrors([]);
                if (showProductForm) {
                  setEditingProduct(null);
                  setNewProduct({
                    name: '',
                    description: '',
                    price: '',
                    category: 'men',
                    color: '',
                    size: '',
                    available_colors: [],
                    available_sizes: [],
                    fabric: '',
                    clothing_type: '',
                    dress_style: '',
                    occasion: '',
                    age_group: '',
                    season: 'all_season',
                    clothing_category: 'other',
                    image_url: '',
                    stock_quantity: 0,
                    is_active: true
                  });
                }
              }}>
                {showProductForm ? 'Cancel' : '+ Create New Product'}
              </button>
            </div>

            {productValidationErrors.length > 0 && (
              <div className="admin-product-validation-errors" role="alert" style={{ marginBottom: '20px' }}>
                <strong>Please fix the following:</strong>
                <ul>
                  {productValidationErrors.map((msg, i) => (
                    <li key={i}>{msg}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Create/Edit Product Form */}
            {showProductForm && (
              <div className="sale-form" style={{ marginBottom: '30px', padding: '20px', border: '1px solid #e0e0e0', borderRadius: '8px' }}>
                <h3>{editingProduct ? 'Edit Product' : 'Create New Product'}</h3>
                <div style={{ display: 'grid', gap: '15px' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
                    <div>
                      <label>Product Name *</label>
                      <input
                        type="text"
                        value={newProduct.name}
                        onChange={(e) => { setNewProduct({ ...newProduct, name: e.target.value }); if (productValidationErrors.length) setProductValidationErrors([]); }}
                        placeholder="e.g., Classic T-Shirt"
                        style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                      />
                    </div>
                    <div>
                      <label>Price *</label>
                      <input
                        type="number"
                        step="0.01"
                        value={newProduct.price}
                        onChange={(e) => { setNewProduct({ ...newProduct, price: e.target.value }); if (productValidationErrors.length) setProductValidationErrors([]); }}
                        placeholder="29.99"
                        style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                      />
                    </div>
                  </div>
                  <div>
                    <label>Description</label>
                    <textarea
                      value={newProduct.description}
                      onChange={(e) => setNewProduct({ ...newProduct, description: e.target.value })}
                      placeholder="Product description..."
                      style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px', minHeight: '80px' }}
                    />
                  </div>
                  {/* Category, Gender & Season — matches table columns */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '15px' }}>
                    <div>
                      <label>Category (clothing type) *</label>
                      <select
                        value={newProduct.clothing_category || 'other'}
                        onChange={(e) => { setNewProduct({ ...newProduct, clothing_category: e.target.value || 'other' }); if (productValidationErrors.length) setProductValidationErrors([]); }}
                        style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                      >
                        <option value="pants">Pants</option>
                        <option value="shirts">Shirts</option>
                        <option value="t_shirts">T-Shirts</option>
                        <option value="jackets">Jackets</option>
                        <option value="coats">Coats</option>
                        <option value="socks">Socks</option>
                        <option value="dresses">Dresses</option>
                        <option value="skirts">Skirts</option>
                        <option value="shorts">Shorts</option>
                        <option value="sweaters">Sweaters</option>
                        <option value="hoodies">Hoodies</option>
                        <option value="underwear">Underwear</option>
                        <option value="shoes">Shoes</option>
                        <option value="sandals">Sandals</option>
                        <option value="sneakers">Sneakers</option>
                        <option value="pajamas">Pajamas</option>
                        <option value="blouses">Blouses</option>
                        <option value="leggings">Leggings</option>
                        <option value="suits">Suits</option>
                        <option value="other">Other</option>
                      </select>
                    </div>
                    <div>
                      <label>Gender *</label>
                      <select
                        value={newProduct.category}
                        onChange={(e) => { setNewProduct({ ...newProduct, category: e.target.value }); if (productValidationErrors.length) setProductValidationErrors([]); }}
                        style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                      >
                        <option value="men">Men</option>
                        <option value="women">Women</option>
                        <option value="kids">Kids</option>
                      </select>
                    </div>
                    <div>
                      <label>Season *</label>
                      <select
                        value={newProduct.season || 'all_season'}
                        onChange={(e) => { setNewProduct({ ...newProduct, season: e.target.value || 'all_season' }); if (productValidationErrors.length) setProductValidationErrors([]); }}
                        style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                      >
                        <option value="spring">Spring</option>
                        <option value="summer">Summer</option>
                        <option value="fall">Fall</option>
                        <option value="winter">Winter</option>
                        <option value="all_season">All season</option>
                      </select>
                    </div>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
                    <div>
                      <label>Stock Quantity</label>
                      <input
                        type="number"
                        value={newProduct.stock_quantity}
                        onChange={(e) => { setNewProduct({ ...newProduct, stock_quantity: parseInt(e.target.value, 10) || 0 }); if (productValidationErrors.length) setProductValidationErrors([]); }}
                        style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                      />
                    </div>
                    <div>
                      <label>Image URL</label>
                      <input
                        type="text"
                        value={newProduct.image_url}
                        onChange={(e) => setNewProduct({ ...newProduct, image_url: e.target.value })}
                        placeholder="https://..."
                        style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                      />
                    </div>
                  </div>

                  {/* Available Colors Section */}
                  <div style={{ border: '1px solid #e0e0e0', padding: '15px', borderRadius: '4px' }}>
                    <label style={{ fontWeight: 'bold', marginBottom: '10px', display: 'block' }}>Available Colors</label>
                    <div style={{ display: 'flex', gap: '10px', marginBottom: '10px', flexWrap: 'wrap' }}>
                      {newProduct.available_colors.map((color, idx) => (
                        <span key={idx} style={{ 
                          padding: '5px 10px', 
                          background: '#1a2332', 
                          color: 'white', 
                          borderRadius: '4px',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '5px'
                        }}>
                          {color}
                          <button 
                            onClick={() => removeColorFromProduct(color)}
                            style={{ background: 'none', border: 'none', color: 'white', cursor: 'pointer' }}
                          >×</button>
                        </span>
                      ))}
                    </div>
                    <div style={{ display: 'flex', gap: '10px' }}>
                      <input
                        type="text"
                        placeholder="Add color (e.g., Red, Blue)"
                        onKeyPress={(e) => {
                          if (e.key === 'Enter') {
                            e.preventDefault();
                            addColorToProduct(e.target.value.trim());
                            e.target.value = '';
                          }
                        }}
                        style={{ flex: 1, padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                      />
                      <button
                        type="button"
                        onClick={(e) => {
                          const input = e.target.previousElementSibling;
                          addColorToProduct(input.value.trim());
                          input.value = '';
                        }}
                        className="save-btn"
                        style={{ padding: '8px 16px' }}
                      >
                        Add Color
                      </button>
                    </div>
                    <div style={{ marginTop: '10px' }}>
                      <label>Default Color</label>
                      <input
                        type="text"
                        value={newProduct.color}
                        onChange={(e) => setNewProduct({ ...newProduct, color: e.target.value })}
                        placeholder="Primary/default color"
                        style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                      />
                    </div>
                  </div>

                  {/* Available Sizes Section */}
                  <div style={{ border: '1px solid #e0e0e0', padding: '15px', borderRadius: '4px' }}>
                    <label style={{ fontWeight: 'bold', marginBottom: '10px', display: 'block' }}>Available Sizes</label>
                    <div style={{ display: 'flex', gap: '10px', marginBottom: '10px', flexWrap: 'wrap' }}>
                      {newProduct.available_sizes.map((size, idx) => (
                        <span key={idx} style={{ 
                          padding: '5px 10px', 
                          background: '#1a2332', 
                          color: 'white', 
                          borderRadius: '4px',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '5px'
                        }}>
                          {size}
                          <button 
                            onClick={() => removeSizeFromProduct(size)}
                            style={{ background: 'none', border: 'none', color: 'white', cursor: 'pointer' }}
                          >×</button>
                        </span>
                      ))}
                    </div>
                    <div style={{ display: 'flex', gap: '10px' }}>
                      <input
                        type="text"
                        placeholder="Add size (e.g., S, M, L, XL)"
                        onKeyPress={(e) => {
                          if (e.key === 'Enter') {
                            e.preventDefault();
                            addSizeToProduct(e.target.value.trim());
                            e.target.value = '';
                          }
                        }}
                        style={{ flex: 1, padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                      />
                      <button
                        type="button"
                        onClick={(e) => {
                          const input = e.target.previousElementSibling;
                          addSizeToProduct(input.value.trim());
                          input.value = '';
                        }}
                        className="save-btn"
                        style={{ padding: '8px 16px' }}
                      >
                        Add Size
                      </button>
                    </div>
                    <div style={{ marginTop: '10px' }}>
                      <label>Default Size</label>
                      <input
                        type="text"
                        value={newProduct.size}
                        onChange={(e) => setNewProduct({ ...newProduct, size: e.target.value })}
                        placeholder="Primary/default size"
                        style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                      />
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
                    <div>
                      <label>Fabric</label>
                      <input
                        type="text"
                        value={newProduct.fabric}
                        onChange={(e) => setNewProduct({ ...newProduct, fabric: e.target.value })}
                        placeholder="e.g., 100% Cotton"
                        style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                      />
                    </div>
                    <div>
                      <label>Clothing Type</label>
                      <input
                        type="text"
                        value={newProduct.clothing_type}
                        onChange={(e) => setNewProduct({ ...newProduct, clothing_type: e.target.value })}
                        placeholder="e.g., T-Shirt, Dress, Jeans"
                        style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                      />
                    </div>
                  </div>

                  <div>
                    <label>
                      <input
                        type="checkbox"
                        checked={newProduct.is_active}
                        onChange={(e) => setNewProduct({ ...newProduct, is_active: e.target.checked })}
                        style={{ marginRight: '8px' }}
                      />
                      Active (Product will be visible to customers)
                    </label>
                  </div>

                  <div style={{ display: 'flex', gap: '10px' }}>
                    <button className="save-btn" onClick={editingProduct ? () => handleUpdateProduct(editingProduct.id, newProduct) : handleCreateProduct} disabled={saving}>
                      {saving ? 'Saving...' : editingProduct ? 'Update Product' : 'Create Product'}
                    </button>
                    <button
                      className="save-btn"
                      style={{ background: '#6c757d' }}
                      onClick={() => {
                        setShowProductForm(false);
                        setEditingProduct(null);
                        setNewProduct({
                          name: '',
                          description: '',
                          price: '',
                          category: 'men',
                          color: '',
                          size: '',
                          available_colors: [],
                          available_sizes: [],
                          fabric: '',
                          clothing_type: '',
                          dress_style: '',
                          occasion: '',
                          age_group: '',
                          season: 'all_season',
                          clothing_category: 'other',
                          image_url: '',
                          stock_quantity: 0,
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

            {/* Products List */}
            {productsLoading ? (
              <div>Loading products...</div>
            ) : (
              <div className="sales-table">
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ background: '#f8f9fa' }}>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Name</th>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Category</th>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Gender</th>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Season</th>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Price</th>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Colors</th>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Sizes</th>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Stock</th>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Status</th>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {products.length === 0 ? (
                      <tr>
                        <td colSpan="10" style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
                          No products found. Create your first product above!
                        </td>
                      </tr>
                    ) : (
                      products.map(product => (
                        <tr key={product.id} style={{ borderBottom: '1px solid #dee2e6' }}>
                          <td style={{ padding: '12px' }}>{product.name}</td>
                          <td style={{ padding: '12px', textTransform: 'capitalize' }}>{(product.clothing_category || product.category || '-').replace(/_/g, ' ')}</td>
                          <td style={{ padding: '12px', textTransform: 'capitalize' }}>{product.category || '-'}</td>
                          <td style={{ padding: '12px', textTransform: 'capitalize' }}>{(product.season || 'all_season').replace(/_/g, ' ')}</td>
                          <td style={{ padding: '12px' }}>${parseFloat(product.price).toFixed(2)}</td>
                          <td style={{ padding: '12px' }}>
                            {product.available_colors && product.available_colors.length > 0 
                              ? product.available_colors.join(', ') 
                              : product.color || '-'}
                          </td>
                          <td style={{ padding: '12px' }}>
                            {product.available_sizes && product.available_sizes.length > 0 
                              ? product.available_sizes.join(', ') 
                              : product.size || '-'}
                          </td>
                          <td style={{ padding: '12px' }}>{product.stock_quantity}</td>
                          <td style={{ padding: '12px' }}>
                            <span style={{
                              padding: '4px 8px',
                              borderRadius: '4px',
                              background: product.is_active ? '#d4edda' : '#f8d7da',
                              color: product.is_active ? '#155724' : '#721c24',
                              fontSize: '12px',
                              fontWeight: 'bold'
                            }}>
                              {product.is_active ? 'ACTIVE' : 'INACTIVE'}
                            </span>
                          </td>
                          <td style={{ padding: '12px' }}>
                            <div style={{ display: 'flex', gap: '8px' }}>
                              <button
                                className="save-btn"
                                style={{ fontSize: '12px', padding: '6px 12px', background: '#28a745' }}
                                onClick={() => handleEditProduct(product)}
                              >
                                Edit
                              </button>
                              <button
                                className="save-btn"
                                style={{ fontSize: '12px', padding: '6px 12px', background: '#dc2626' }}
                                onClick={() => handleDeleteProduct(product.id)}
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

          {/* Reviews Management Section */}
          {activeTab === 'reviews' && (
          <div className="admin-section">
            <h2>Reviews & Ratings Management</h2>
            <p style={{color: '#6b7280', marginBottom: '24px'}}>
              View and manage all product reviews and ratings submitted by customers.
            </p>
            
            {reviewsLoading ? (
              <div>Loading reviews...</div>
            ) : (
              <div className="sales-table">
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ background: '#f8f9fa' }}>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Product</th>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>User</th>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Rating</th>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Comment</th>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Date</th>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reviews.length === 0 ? (
                      <tr>
                        <td colSpan="6" style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
                          No reviews found yet.
                        </td>
                      </tr>
                    ) : (
                      reviews.map(review => (
                        <tr key={review.id} style={{ borderBottom: '1px solid #dee2e6' }}>
                          <td style={{ padding: '12px' }}>
                            {review.product ? review.product.name : `Product #${review.product_id}`}
                          </td>
                          <td style={{ padding: '12px' }}>
                            {review.user_name || review.user_email || 'Anonymous'}
                            {review.user_email && (
                              <div style={{ fontSize: '11px', color: '#666' }}>{review.user_email}</div>
                            )}
                          </td>
                          <td style={{ padding: '12px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                              <span style={{ fontWeight: 'bold' }}>{review.rating}</span>
                              <div style={{ display: 'flex', gap: '2px' }}>
                                {[1, 2, 3, 4, 5].map((star) => (
                                  <span
                                    key={star}
                                    style={{
                                      fontSize: '14px',
                                      color: star <= review.rating ? '#d4af37' : '#d1d5db'
                                    }}
                                  >
                                    ★
                                  </span>
                                ))}
                              </div>
                            </div>
                          </td>
                          <td style={{ padding: '12px', maxWidth: '300px' }}>
                            {review.comment ? (
                              <div style={{ 
                                overflow: 'hidden', 
                                textOverflow: 'ellipsis', 
                                whiteSpace: 'nowrap',
                                maxWidth: '300px'
                              }}>
                                {review.comment}
                              </div>
                            ) : (
                              <span style={{ color: '#999', fontStyle: 'italic' }}>No comment</span>
                            )}
                          </td>
                          <td style={{ padding: '12px', fontSize: '12px', color: '#666' }}>
                            {new Date(review.created_at).toLocaleDateString()}
                          </td>
                          <td style={{ padding: '12px' }}>
                            <button
                              className="save-btn"
                              style={{ fontSize: '12px', padding: '6px 12px', background: '#dc2626' }}
                              onClick={() => handleDeleteReview(review.id)}
                            >
                              Delete
                            </button>
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

          {/* Orders Management Section */}
          {activeTab === 'orders' && (
          <div className="admin-section">
            <h2>Orders Management</h2>
            {ordersLoading ? (
              <div>Loading orders...</div>
            ) : (
              <div className="sales-table">
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ background: '#f8f9fa' }}>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Order #</th>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Customer</th>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Total</th>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Status</th>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Date</th>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {orders.length === 0 ? (
                      <tr>
                        <td colSpan="6" style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
                          No orders found.
                        </td>
                      </tr>
                    ) : (
                      orders.map(order => (
                        <tr key={order.id} style={{ borderBottom: '1px solid #dee2e6' }}>
                          <td style={{ padding: '12px' }}>{order.order_number}</td>
                          <td style={{ padding: '12px' }}>
                            {order.shipping_name}
                            {order.guest_email && <div style={{ fontSize: '11px', color: '#666' }}>{order.guest_email}</div>}
                          </td>
                          <td style={{ padding: '12px' }}>${Number(order.total ?? 0).toFixed(2)}</td>
                          <td style={{ padding: '12px' }}>
                            <select
                              value={order.status}
                              onChange={(e) => handleUpdateOrderStatus(order.id, e.target.value)}
                              style={{ padding: '4px 8px', borderRadius: '4px', border: '1px solid #ddd' }}
                            >
                              <option value="pending">Pending</option>
                              <option value="processing">Processing</option>
                              <option value="shipped">Shipped</option>
                              <option value="delivered">Delivered</option>
                              <option value="cancelled">Cancelled</option>
                            </select>
                          </td>
                          <td style={{ padding: '12px', fontSize: '12px', color: '#666' }}>
                            {new Date(order.created_at).toLocaleDateString()}
                          </td>
                          <td style={{ padding: '12px' }}>
                            <button
                              className="save-btn"
                              style={{ fontSize: '12px', padding: '6px 12px' }}
                              onClick={() => setSelectedOrderId(order.id)}
                            >
                              View
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {/* Order detail modal */}
            {(selectedOrderId != null) && (
              <div
                className="admin-modal-overlay"
                style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}
                onClick={() => setSelectedOrderId(null)}
                role="dialog"
                aria-modal="true"
                aria-label="Order details"
              >
                <div
                  className="admin-modal-content"
                  style={{ background: '#fff', borderRadius: 8, maxWidth: 600, width: '100%', maxHeight: '90vh', overflow: 'auto', boxShadow: '0 4px 20px rgba(0,0,0,0.15)' }}
                  onClick={e => e.stopPropagation()}
                >
                  <div style={{ padding: 20, borderBottom: '1px solid #eee', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h3 style={{ margin: 0 }}>Order Details</h3>
                    <button type="button" onClick={() => setSelectedOrderId(null)} style={{ padding: '6px 12px', cursor: 'pointer' }} aria-label="Close">×</button>
                  </div>
                  <div style={{ padding: 20 }}>
                    {orderDetailLoading ? (
                      <div>Loading order...</div>
                    ) : orderDetail ? (
                      <>
                        <p><strong>Order #:</strong> {orderDetail.order_number}</p>
                        <p><strong>Status:</strong> {orderDetail.status}</p>
                        <p><strong>Date:</strong> {orderDetail.created_at ? new Date(orderDetail.created_at).toLocaleString() : '—'}</p>
                        <p><strong>Customer:</strong> {orderDetail.shipping_name}{orderDetail.guest_email ? ` (${orderDetail.guest_email})` : ''}</p>
                        <p><strong>Shipping:</strong> {orderDetail.shipping_address}, {orderDetail.shipping_city}, {orderDetail.shipping_state} {orderDetail.shipping_zip}</p>
                        <p><strong>Subtotal:</strong> ${Number(orderDetail.subtotal ?? 0).toFixed(2)} | <strong>Tax:</strong> ${Number(orderDetail.tax ?? 0).toFixed(2)} | <strong>Shipping:</strong> ${Number(orderDetail.shipping_cost ?? 0).toFixed(2)} | <strong>Total:</strong> ${Number(orderDetail.total ?? 0).toFixed(2)}</p>
                        <h4 style={{ marginTop: 16, marginBottom: 8 }}>Items</h4>
                        <ul style={{ margin: 0, paddingLeft: 20 }}>
                          {(orderDetail.items || []).map(item => (
                            <li key={item.id}>
                              {item.product?.name ?? 'Product'} × {item.quantity} — ${Number(item.price ?? 0).toFixed(2)} each
                            </li>
                          ))}
                        </ul>
                      </>
                    ) : (
                      <div>No order data.</div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}


          {/* Cart Management Section */}
          {activeTab === 'carts' && (
          <div className="admin-section">
            <h2>Cart Management</h2>
            {cartsLoading ? (
              <div>Loading carts...</div>
            ) : (
              <div className="sales-table">
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ background: '#f8f9fa' }}>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>User Email</th>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Items</th>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Estimated Total</th>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {carts.length === 0 ? (
                      <tr>
                        <td colSpan="4" style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
                          No active carts found.
                        </td>
                      </tr>
                    ) : (
                      carts.map(cart => (
                        <tr key={cart.user_id} style={{ borderBottom: '1px solid #dee2e6' }}>
                          <td style={{ padding: '12px' }}>{cart.user_email}</td>
                          <td style={{ padding: '12px' }}>{cart.item_count}</td>
                          <td style={{ padding: '12px' }}>${cart.estimated_total.toFixed(2)}</td>
                          <td style={{ padding: '12px' }}>
                            <button
                              className="save-btn"
                              style={{ fontSize: '12px', padding: '6px 12px', background: '#dc2626' }}
                              onClick={() => handleClearUserCart(cart.user_id)}
                            >
                              Clear Cart
                            </button>
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

          {/* AI Assistant Section: 4 fixed providers + model dropdown */}
          {activeTab === 'ai-assistant' && (
          <div className="admin-section">
            <h2>AI Assistant</h2>
            <div style={{ marginBottom: 24, display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
              <label style={{ fontWeight: 600 }}>Model (default for chatbot):</label>
              <div style={{ width: 68, flexShrink: 0 }}>
                <select
                  value={aiSelectedProvider}
                  onChange={(e) => handleSelectedProviderChange(e.target.value)}
                  style={{
                    width: '100%',
                    maxWidth: '100%',
                    padding: '4px 6px',
                    borderRadius: 6,
                    border: '1px solid #d1d5db',
                    fontSize: '0.85rem',
                    boxSizing: 'border-box',
                    minWidth: 0,
                  }}
                >
                  <option value="auto">Auto</option>
                  <option value="openai">OpenAI</option>
                  <option value="gemini">Google Gemini</option>
                  <option value="anthropic">Anthropic</option>
                </select>
              </div>
              <span style={{ color: '#6b7280', fontSize: '0.9rem' }}>Auto uses the first enabled provider with a valid key. Enable a provider with the switch after saving and testing its API key.</span>
            </div>
            {aiAssistantLoading ? (
              <div>Loading...</div>
            ) : (
              <div className="sales-table">
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ background: '#f8f9fa' }}>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Provider</th>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Enabled</th>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>SDK</th>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>API key</th>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Source</th>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Valid</th>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Last tested</th>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Test</th>
                    </tr>
                  </thead>
                  <tbody>
                    {aiProviders.map((p) => (
                      <tr key={p.provider} style={{ borderBottom: '1px solid #dee2e6' }}>
                        <td style={{ padding: '12px' }}>{p.name}</td>
                        <td style={{ padding: '12px', minWidth: 56 }}>
                          <button
                            type="button"
                            role="switch"
                            aria-checked={!!p.is_enabled}
                            disabled={!p.is_valid}
                            title={!p.is_valid ? 'Add and test an API key to unlock' : (p.is_enabled ? 'Disable provider' : 'Enable provider')}
                            onClick={() => p.is_valid && handleToggleProviderEnabled(p.provider, !!p.is_enabled)}
                            style={{
                              position: 'relative',
                              width: 44,
                              height: 24,
                              padding: 0,
                              border: 'none',
                              borderRadius: 12,
                              cursor: p.is_valid ? 'pointer' : 'not-allowed',
                              backgroundColor: !p.is_valid ? '#d1d5db' : (p.is_enabled ? '#22c55e' : '#d1d5db'),
                              transition: 'background-color 0.2s',
                              flexShrink: 0,
                            }}
                          >
                            <span
                              style={{
                                position: 'absolute',
                                top: 2,
                                left: p.is_enabled ? 22 : 2,
                                width: 20,
                                height: 20,
                                borderRadius: '50%',
                                backgroundColor: '#fff',
                                boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
                                transition: 'left 0.2s',
                              }}
                            />
                          </button>
                        </td>
                        <td style={{ padding: '12px' }}>{p.sdk_installed_backend ? '✓' : '✗'}</td>
                        <td style={{ padding: '12px' }}>
                            <form
                              onSubmit={(e) => {
                                e.preventDefault();
                                const v = aiProviderKeyInputs[p.provider];
                                if (v !== undefined && v !== '••••••••' && v.trim()) handleSaveProviderKey(p.provider, v.trim());
                              }}
                              style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}
                            >
                              <input
                                type="password"
                                placeholder={p.source === 'env' ? 'From env' : 'Paste API key'}
                                value={aiProviderKeyInputs[p.provider] ?? (p.api_key ? '••••••••' : '')}
                                onChange={(e) => setAiProviderKeyInputs(prev => ({ ...prev, [p.provider]: e.target.value }))}
                                style={{ width: '100%', maxWidth: 280, padding: 6, borderRadius: 4, border: '1px solid #d1d5db' }}
                                aria-label={`API key for ${p.name}`}
                              />
                              <button
                                type="submit"
                                className="save-btn"
                                style={{ fontSize: '11px', padding: '4px 8px' }}
                                disabled={aiProviderSaving === p.provider}
                              >
                                {aiProviderSaving === p.provider ? 'Saving...' : 'Save'}
                              </button>
                            </form>
                        </td>
                        <td style={{ padding: '12px' }}>{p.source === 'admin' ? 'Admin' : 'Env'}</td>
                        <td style={{ padding: '12px' }}>{p.is_valid ? '✓' : '✗'}</td>
                        <td style={{ padding: '12px' }}>{p.last_tested_at ? new Date(p.last_tested_at).toLocaleString() : '—'}</td>
                        <td style={{ padding: '12px' }}>
                          <button
                            type="button"
                            className="save-btn"
                            style={{ fontSize: '12px', padding: '6px 12px' }}
                            onClick={() => handleTestProvider(p.provider)}
                            disabled={aiProviderTesting === p.provider}
                          >
                            {aiProviderTesting === p.provider ? 'Testing...' : 'Test'}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
        </main>
        <Footer />
        </div>
      </div>
    </div>
  );
};

export default Admin;

