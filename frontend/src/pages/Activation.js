import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './Activation.css';

const Activation = () => {
  const [searchParams] = useSearchParams();
  const { verifyEmail } = useAuth();
  const navigate = useNavigate();
  const [status, setStatus] = useState('verifying');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const token = searchParams.get('verify');
    if (token) {
      handleVerification(token);
    } else {
      setStatus('error');
      setMessage('No verification token provided');
    }
  }, [searchParams]);

  const handleVerification = async (token) => {
    try {
      const result = await verifyEmail(token);
      if (result.success) {
        setStatus('success');
        setMessage(result.message || 'Email verified successfully!');
        setTimeout(() => {
          navigate('/login');
        }, 3000);
      } else {
        setStatus('error');
        setMessage(result.error || 'Verification failed');
      }
    } catch (error) {
      setStatus('error');
      setMessage('An error occurred during verification');
    }
  };

  return (
    <div className="activation-page">
      <div className="activation-container">
        {status === 'verifying' && (
          <>
            <div className="spinner"></div>
            <h2>Verifying your email...</h2>
          </>
        )}
        {status === 'success' && (
          <>
            <div className="success-icon">✓</div>
            <h2>Email Verified!</h2>
            <p>{message}</p>
            <p>Redirecting to login...</p>
          </>
        )}
        {status === 'error' && (
          <>
            <div className="error-icon">✗</div>
            <h2>Verification Failed</h2>
            <p>{message}</p>
            <a href="/login" className="btn btn-primary">Go to Login</a>
          </>
        )}
      </div>
    </div>
  );
};

export default Activation;

