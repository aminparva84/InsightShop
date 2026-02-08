import React, { createContext, useState, useContext, useEffect, useRef } from 'react';
import axios from 'axios';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const TOKEN_KEY = 'token';
const REDIRECT_KEY = 'loginRedirect';

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(null);
  const logoutRef = useRef(null);

  // When any API returns 401 or 422 (invalid/expired token), clear session so user can log in again
  useEffect(() => {
    const interceptor = axios.interceptors.response.use(
      (res) => res,
      (err) => {
        if (err.response?.status === 401 || err.response?.status === 422) {
          if (logoutRef.current) logoutRef.current();
        }
        return Promise.reject(err);
      }
    );
    return () => axios.interceptors.response.eject(interceptor);
  }, []);

  // Read token after mount so we never redirect before localStorage is read (avoids wrong redirect on /members, /admin)
  useEffect(() => {
    const stored = localStorage.getItem(TOKEN_KEY);
    setToken(stored);
    if (!stored) setLoading(false);
  }, []);

  useEffect(() => {
    if (!token) return;
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    fetchUser();
  }, [token]);

  const fetchUser = async () => {
    try {
      const response = await axios.get('/api/auth/me');
      setUser(response.data.user);
    } catch (error) {
      console.error('Error fetching user:', error);
      // Clear session on 401 or 422 (expired/invalid/malformed token); keep token on network/5xx so refresh keeps URL
      if (error.response?.status === 401 || error.response?.status === 422) {
        logout();
      }
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await axios.post('/api/auth/login', { email, password });
      const { token, user } = response.data;
      setToken(token);
      setUser(user);
      localStorage.setItem(TOKEN_KEY, token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.error || 'Login failed' };
    }
  };

  const register = async (email, password, first_name, last_name) => {
    try {
      const response = await axios.post('/api/auth/register', {
        email,
        password,
        first_name,
        last_name
      });
      return { success: true, message: response.data.message };
    } catch (error) {
      return { success: false, error: error.response?.data?.error || 'Registration failed' };
    }
  };

  const googleLogin = async (credential) => {
    try {
      const response = await axios.post('/api/auth/google', { credential });
      const { token, user } = response.data;
      setToken(token);
      setUser(user);
      localStorage.setItem(TOKEN_KEY, token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.error || 'Google login failed' };
    }
  };

  const verifyEmail = async (token) => {
    try {
      const response = await axios.post('/api/auth/verify', { token });
      if (response.data.user) {
        setUser(response.data.user);
      }
      return { success: true, message: response.data.message };
    } catch (error) {
      return { success: false, error: error.response?.data?.error || 'Verification failed' };
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem(TOKEN_KEY);
    delete axios.defaults.headers.common['Authorization'];
  };
  logoutRef.current = logout;

  const value = {
    user,
    token,
    loading,
    login,
    register,
    googleLogin,
    verifyEmail,
    logout,
    isAuthenticated: !!user
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export { REDIRECT_KEY };

