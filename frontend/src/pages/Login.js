import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './Auth.css';

const Login = () => {
  const { login, googleLogin, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const redirectTo = searchParams.get('redirect') || '/';
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // After login, redirect to cart so user sees merged cart (guest items + their cart)
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/cart', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    // Initialize Google Sign-In
    if (window.google) {
      window.google.accounts.id.initialize({
        client_id: process.env.REACT_APP_GOOGLE_CLIENT_ID || '',
        callback: handleGoogleSignIn
      });
    }
  }, []);

  const handleGoogleSignIn = async (response) => {
    try {
      setLoading(true);
      const result = await googleLogin(response.credential);
      if (result.success) {
        navigate('/cart', { replace: true });
      } else {
        setError(result.error);
      }
    } catch (error) {
      setError('Google sign-in failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const result = await login(formData.email, formData.password);
    if (result.success) {
      navigate('/cart', { replace: true });
    } else {
      setError(result.error);
    }
    setLoading(false);
  };

  return (
    <div className="auth-page">
      <div className="auth-container">
        <h1>Login</h1>
        <p className="auth-subtitle">
          {redirectTo === '/checkout' ? 'Please log in to proceed to checkout' : 'Welcome back to InsightShop'}
        </p>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label className="form-label">Email</label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              required
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              required
              className="form-input"
            />
          </div>

          <button type="submit" disabled={loading} className="btn btn-primary btn-auth">
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <div className="auth-divider">
          <span>OR</span>
        </div>

        {window.google && (
          <div id="google-signin-button" className="google-signin-container"></div>
        )}

        <p className="auth-footer">
          Don't have an account? <Link to="/register">Sign up</Link>
        </p>
      </div>
    </div>
  );
};

export default Login;

