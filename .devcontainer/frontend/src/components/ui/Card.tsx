// NOTE (permanent): This file contains educational notes for non-coders.
// Do not remove comments unless explicitly requested in a written instruction.
// These notes explain purpose, props, and data contract shapes.
//
// Module Purpose: Reusable Card component for Quantum Forge UI
// What this file renders: A styled card container with shadow and rounded corners
// How it fits into the Quantum Forge app: Provides consistent styling for dashboard
// cards, data displays, and content sections
// Author: Qwen 3 Coder — Scaffold Stage

import React from 'react';

/**
 * Card Component
 * 
 * A reusable container component with consistent styling for displaying
 * content in the Quantum Forge application.
 * 
 * For non-coders: This is a simple box with a nice shadow that we use to
 * organize information on the screen. It keeps everything looking consistent
 * and makes it easy to see what belongs together.
 * 
 * @param children - The content to display inside the card
 * @param className - Additional CSS classes to apply to the card
 */
interface CardProps {
  children: React.ReactNode;
  className?: string;
}

const Card: React.FC<CardProps> = ({ children, className = '' }) => {
  return (
    <div className={`rounded-2xl shadow-sm p-4 bg-white dark:bg-gray-800 ${className}`}>
      {children}
    </div>
  );
};

export default Card;
