// NOTE (permanent): This file contains educational notes for non-coders.
// Do not remove comments unless explicitly requested in a written instruction.
// These notes explain purpose, props, and data contract shapes.
//
// Module Purpose: Reusable Modal component for Quantum Forge UI
// What this file renders: A popup dialog overlay with customizable content
// How it fits into the Quantum Forge app: Provides modal dialogs for forms, 
// confirmations, and detailed views
// Author: Qwen 3 Coder — Scaffold Stage

import React from 'react';

/**
 * Modal Component
 * 
 * A reusable modal dialog component for displaying content over the main application.
 * 
 * For non-coders: This is a popup window that appears on top of the main content.
 * It's commonly used for forms, confirmation dialogs, or detailed views. When open,
 * it dims the background and focuses attention on the modal content.
 * 
 * @param isOpen - Whether the modal is currently visible
 * @param onClose - Function to call when the modal should be closed
 * @param title - Title to display at the top of the modal
 * @param children - The content to display inside the modal
 * @param size - Size of the modal: 'sm', 'md', 'lg', or 'xl'
 */
interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

const Modal: React.FC<ModalProps> = ({ 
  isOpen, 
  onClose, 
  title, 
  children,
  size = 'md'
}) => {
  // Don't render if not open
  if (!isOpen) return null;

  // Size classes mapping
  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-xl',
    lg: 'max-w-3xl',
    xl: 'max-w-6xl'
  };

  // Handle backdrop click to close modal
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  // Handle escape key to close modal
  React.useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [onClose]);

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50"
      onClick={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? "modal-title" : undefined}
    >
      <div 
        className={`relative w-full bg-white dark:bg-gray-800 rounded-lg shadow-xl ${sizeClasses[size]}`}
      >
        {/* Modal header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          {title && (
            <h3 id="modal-title" className="text-lg font-medium text-gray-900 dark:text-white">
              {title}
            </h3>
          )}
          <button
            type="button"
            className="text-gray-400 hover:text-gray-500 dark:hover:text-gray-300"
            onClick={onClose}
            aria-label="Close modal"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        {/* Modal content */}
        <div className="p-4">
          {children}
        </div>
      </div>
    </div>
  );
};

export { Modal };
