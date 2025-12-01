import React from 'react';
import './ConfirmationDialog.css';

const ConfirmationDialog = ({ message, onConfirm, onCancel, confirmText = 'Confirm', cancelText = 'Cancel' }) => {
  return (
    <div className="confirmation-overlay" onClick={onCancel}>
      <div className="confirmation-dialog" onClick={(e) => e.stopPropagation()}>
        <div className="confirmation-content">
          <p className="confirmation-message">{message}</p>
          <div className="confirmation-actions">
            <button className="confirmation-btn confirmation-btn-cancel" onClick={onCancel}>
              {cancelText}
            </button>
            <button className="confirmation-btn confirmation-btn-confirm" onClick={onConfirm}>
              {confirmText}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConfirmationDialog;

