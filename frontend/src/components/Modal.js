import React, { useEffect, useRef, useCallback } from 'react';
import { createPortal } from 'react-dom';
import './Modal.css';

/**
 * Reusable accessible modal. Renders as a popup via portal to document.body
 * so it is never clipped by parent overflow/transform.
 * - ESC to close
 * - Click overlay to close (optional via closeOnOverlayClick)
 * - Focus trap inside modal
 * - aria-modal, role="dialog"
 */
const Modal = ({
  isOpen,
  onClose,
  children,
  className = '',
  ariaLabelledBy,
  ariaDescribedBy,
  closeOnOverlayClick = true,
}) => {
  const overlayRef = useRef(null);
  const contentRef = useRef(null);
  const previousActiveElement = useRef(null);

  const handleOverlayClick = useCallback(
    (e) => {
      if (!closeOnOverlayClick) return;
      if (e.target === overlayRef.current) {
        onClose();
      }
    },
    [closeOnOverlayClick, onClose]
  );

  const handleKeyDown = useCallback(
    (e) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      }
    },
    [onClose]
  );

  // Focus trap: keep focus inside modal when open
  useEffect(() => {
    if (!isOpen) return;

    previousActiveElement.current = document.activeElement;

    const content = contentRef.current;
    if (!content) return;

    const focusables = content.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const first = focusables[0];
    const last = focusables[focusables.length - 1];

    if (first) first.focus();

    const trap = (e) => {
      if (e.key !== 'Tab') return;
      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          if (last) last.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          if (first) first.focus();
        }
      }
    };

    document.addEventListener('keydown', trap);
    document.body.style.overflow = 'hidden';

    return () => {
      document.removeEventListener('keydown', trap);
      document.body.style.overflow = '';
      if (previousActiveElement.current && typeof previousActiveElement.current.focus === 'function') {
        previousActiveElement.current.focus();
      }
    };
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDownEffect = (e) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      }
    };
    document.addEventListener('keydown', handleKeyDownEffect);
    return () => document.removeEventListener('keydown', handleKeyDownEffect);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const modalContent = (
    <div
      ref={overlayRef}
      className="modal-overlay"
      onClick={handleOverlayClick}
      onKeyDown={handleKeyDown}
      role="dialog"
      aria-modal="true"
      aria-labelledby={ariaLabelledBy}
      aria-describedby={ariaDescribedBy}
    >
      <div
        ref={contentRef}
        className={`modal-content ${className}`}
        onClick={(e) => e.stopPropagation()}
      >
        {children}
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
};

export default Modal;
