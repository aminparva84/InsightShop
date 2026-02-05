import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Login from '../pages/Login';

/**
 * Protects a route: shows Login inline (same URL) when not authenticated,
 * so the return path is never lost and we never redirect to /cart.
 */
function RequireAuth({ path, requireSuperadmin, children }) {
  const { token, user, loading: authLoading } = useAuth();
  const navigate = useNavigate();

  if (authLoading) {
    return <div className="spinner" />;
  }

  if (!token) {
    return <Login returnPath={path} />;
  }

  if (!user) {
    return <div className="spinner" />;
  }

  if (requireSuperadmin && !user.is_superadmin) {
    navigate('/members', { replace: true });
    return <div className="spinner" />;
  }

  return children;
}

export default RequireAuth;
