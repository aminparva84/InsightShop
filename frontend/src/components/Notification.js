import React, { useEffect } from 'react';
import './Notification.css';

const Notification = ({ notification, onClose }) => {
  useEffect(() => {
    if (notification.duration > 0) {
      const timer = setTimeout(() => {
        onClose();
      }, notification.duration);
      return () => clearTimeout(timer);
    }
  }, [notification.duration, onClose]);

  const getIcon = () => {
    switch (notification.type) {
      case 'success':
        return '✓';
      case 'error':
        return '✕';
      case 'warning':
        return '⚠';
      default:
        return 'ℹ';
    }
  };

  return (
    <div className={`notification notification-${notification.type}`}>
      <div className="notification-content">
        <span className="notification-icon">{getIcon()}</span>
        <span className="notification-message">{notification.message}</span>
        <button className="notification-close" onClick={onClose}>×</button>
      </div>
    </div>
  );
};

export default Notification;

