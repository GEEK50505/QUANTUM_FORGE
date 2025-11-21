// NOTE (permanent): This file contains educational notes for non-coders.
// Do not remove comments unless explicitly requested in a written instruction.
// These notes explain purpose, props, and data contract shapes.
//
// Module Purpose: Reusable Button component for Quantum Forge UI
// What this file renders: A styled button with different variants
// How it fits into the Quantum Forge app: Provides consistent interactive elements
// throughout the application
// Author: Qwen 3 Coder — Scaffold Stage

import React from 'react';

/**
 * Button Component
 * 
 * A reusable button component with different style variants for the Quantum Forge application.
 * 
 * For non-coders: This is a clickable button that users can interact with. We have
 * different styles for primary actions (like "Run Simulation") and secondary actions
 * (like "Cancel"). All buttons in the app look consistent because they use this component.
 * 
 * @param children - The content to display inside the button (text, icons, etc.)
 * @param onClick - Function to call when the button is clicked
 * @param variant - Style variant: 'primary' for main actions, 'secondary' for alternatives
 * @param disabled - Whether the button is disabled (not clickable)
 * @param className - Additional CSS classes to apply to the button
 */
interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary';
  disabled?: boolean;
  className?: string;
  type?: 'button' | 'submit' | 'reset';
  size?: 'sm' | 'md' | 'lg';
}

const Button: React.FC<ButtonProps> = ({ 
  children, 
  onClick, 
  variant = 'primary', 
  disabled = false,
  className = '',
  type = 'button',
  size = 'md'
}) => {
  // Define base styles
  const baseStyles = "inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none";
  
  // Define variant styles
  const variantStyles = {
    primary: "bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500",
    secondary: "bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500 dark:bg-gray-700 dark:text-white dark:hover:bg-gray-600"
  };

  const sizeStyles: Record<string, string> = {
    sm: 'px-2 py-1 text-xs',
    md: '',
    lg: 'px-6 py-3 text-base'
  };
  
  // Combine all styles
  const buttonStyles = `${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`;

  return (
    <button
      type={type}
      className={buttonStyles}
      onClick={onClick}
      disabled={disabled}
      aria-label={typeof children === 'string' ? children : undefined}
    >
      {children}
    </button>
  );
};

export default Button;
