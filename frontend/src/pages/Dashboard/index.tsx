// NOTE (permanent): This file contains educational notes for non-coders.
// Do not remove comments unless explicitly requested in a written instruction.
// These notes explain purpose, props, and data contract shapes.
//
// Module Purpose: Main dashboard page for Quantum Forge
// What this file renders: Dashboard landing with KPIs and simulation controls
// How it fits into the Quantum Forge app: This is the primary landing page that shows
// system status and provides quick access to run simulations
// Author: Qwen 3 Coder — Scaffold Stage

import React from 'react';
import OverviewCards from './OverviewCards';
import SimulationControls from './SimulationControls';

/**
 * Dashboard Page Component
 * 
 * This is the main landing page for the Quantum Forge application. It displays
 * key performance indicators and provides controls to start new simulations.
 * 
 * For non-coders: This page gives you a quick overview of your quantum-classical
 * simulation system. You can see how many jobs are running, check the last result,
 * and start new simulations with the big "Run Demo" button.
 */
const DashboardPage: React.FC = () => {
  return (
    <div className="p-4 md:p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Quantum Forge Dashboard
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Hybrid quantum-classical simulation control
        </p>
      </div>
      
      <div className="grid grid-cols-1 gap-6 mb-6">
        {/* KPI Overview Cards */}
        <OverviewCards />
      </div>
      
      <div className="grid grid-cols-1 gap-6">
        {/* Simulation Controls */}
        <SimulationControls />
      </div>
    </div>
  );
};

export default DashboardPage;
