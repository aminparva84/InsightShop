import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import { useAuth, REDIRECT_KEY } from '../contexts/AuthContext';
import './Auth.css';

const Login = ({ returnPath: returnPathProp }) => {
  const { login, googleLogin, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const fromUrlOrStorage = searchParams.get('redirect') || location.state?.from || sessionStorage.getItem(REDIRECT_KEY) || '/';
  const redirectTo = returnPathProp != null ? returnPathProp : fromUrlOrStorage;
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [googleReady, setGoogleReady] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      sessionStorage.removeItem(REDIRECT_KEY);
      navigate(redirectTo, { replace: true });
    }
  }, [isAuthenticated, navigate, redirectTo]);

  // Load Google GSI script only on Login page to avoid "Failed to fetch" on other pages (e.g. product detail)
  useEffect(() => {
    if (window.google?.accounts?.id) {
      setGoogleReady(true);
      return;
    }
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = () => setGoogleReady(true);
    script.onerror = () => setGoogleReady(false);
    document.body.appendChild(script);
    return () => {
      if (script.parentNode) script.parentNode.removeChild(script);
    };
  }, []);

  useEffect(() => {
    if (!googleReady || !window.google) return;
    const clientId = process.env.REACT_APP_GOOGLE_CLIENT_ID || '';
    if (!clientId) return;
    window.google.accounts.id.initialize({
      client_id: clientId,
      callback: handleGoogleSignIn
    });
    const btn = document.getElementById('google-signin-button');
    if (btn) window.google.accounts.id.renderButton(btn, { theme: 'outline', size: 'large', width: 320 });
  }, [googleReady]);

  const handleGoogleSignIn = async (response) => {
    try {
      setLoading(true);
      const result = await googleLogin(response.credential);
      if (result.success) {
        sessionStorage.removeItem(REDIRECT_KEY);
        navigate(redirectTo, { replace: true });
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
      sessionStorage.removeItem(REDIRECT_KEY);
      navigate(redirectTo, { replace: true });
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

        {googleReady && window.google && (
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

