// NOTE (permanent): This file contains educational notes for non-coders.
// Do not remove comments unless explicitly requested in a written instruction.
// These notes explain purpose, props, and data contract shapes.
//
// Module Purpose: Reusable Table component for Quantum Forge UI
// What this file renders: A styled table with consistent formatting
// How it fits into the Quantum Forge app: Displays tabular data throughout the application
// such as simulation jobs, datasets, and model information
// Author: Qwen 3 Coder — Scaffold Stage

import React from 'react';

/**
 * Table Component
 * 
 * A reusable table component with consistent styling for displaying
 * tabular data in the Quantum Forge application.
 * 
 * For non-coders: This is a formatted table that displays information in rows
 * and columns, like a spreadsheet. It's used throughout the app to show lists
 * of simulations, datasets, and other structured information.
 * 
 * @param children - The table content (thead, tbody, etc.)
 * @param className - Additional CSS classes to apply to the table
 */
interface TableProps {
  children: React.ReactNode;
  className?: string;
}

const Table: React.FC<TableProps> = ({ children, className = '' }) => {
  return (
    <div className="overflow-hidden rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
      <table className={`min-w-full divide-y divide-gray-200 dark:divide-gray-700 ${className}`}>
        {children}
      </table>
    </div>
  );
};

/**
 * Table Head Component
 * 
 * A styled header section for the table.
 */
interface TableHeadProps {
  children: React.ReactNode;
  className?: string;
}

Table.Head = ({ children, className = '' }: TableHeadProps) => {
  return (
    <thead className={`bg-gray-50 dark:bg-gray-800 ${className}`}>
      {children}
    </thead>
  );
};

/**
 * Table Body Component
 * 
 * A styled body section for the table.
 */
interface TableBodyProps {
  children: React.ReactNode;
  className?: string;
}

Table.Body = ({ children, className = '' }: TableBodyProps) => {
  return (
    <tbody className={`divide-y divide-gray-200 dark:divide-gray-700 bg-white dark:bg-gray-900 ${className}`}>
      {children}
    </tbody>
  );
};

/**
 * Table Row Component
 * 
 * A styled row for the table.
 */
interface TableRowProps {
  children: React.ReactNode;
  className?: string;
}

Table.Row = ({ children, className = '' }: TableRowProps) => {
  return (
    <tr className={`${className}`}>
      {children}
    </tr>
  );
};

/**
 * Table Header Cell Component
 * 
 * A styled header cell for the table.
 */
interface TableHeaderCellProps {
  children: React.ReactNode;
  className?: string;
}

Table.HeaderCell = ({ children, className = '' }: TableHeaderCellProps) => {
  return (
    <th 
      scope="col" 
      className={`px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider ${className}`}
    >
      {children}
    </th>
  );
};

/**
 * Table Cell Component
 * 
 * A styled data cell for the table.
 */
interface TableCellProps {
  children: React.ReactNode;
  className?: string;
}

Table.Cell = ({ children, className = '' }: TableCellProps) => {
  return (
    <td className={`px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-200 ${className}`}>
      {children}
    </td>
  );
};

export default Table;
