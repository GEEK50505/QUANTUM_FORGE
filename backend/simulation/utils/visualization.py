# Quantum Forge Project - Scaffold Stage
# Author: Qwen 3 Coder
# Description: Initial scaffolding with detailed educational notes
# --------------------------------------------------------------

# ============================================================
# Module Purpose: Visualization and Analysis Utilities
# What this block does: Provides tools for visualizing simulation results
# How it fits into the hybrid simulation pipeline: 
#   - Helps users understand and interpret simulation data
#   - Creates plots and visualizations of results
#   - Provides analysis tools for scientific insights
# ============================================================

"""
Visualization Utilities for Quantum Forge

This module provides tools for visualizing and analyzing simulation results.
Good visualization is crucial for understanding complex scientific data.

Key Concepts:
- Visualization transforms numerical data into intuitive graphical representations
- Different types of data need different visualization approaches
- Good visualizations reveal patterns, trends, and outliers
- Interactive visualizations allow deeper exploration

In the hybrid simulation context:
1. Classical trajectories (3D particle motion)
2. Quantum orbitals (electron probability distributions)
3. Energy landscapes (potential energy surfaces)
4. Time series (energy, temperature, pressure over time)
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import List
import matplotlib.animation as animation

class SimulationVisualizer:
    """
    A visualization tool for hybrid quantum-classical simulations.
    
    Why visualization matters in scientific computing:
    =================================================
    Think of visualization as a "translator" between:
    - Raw numbers (what computers understand)
    - Intuitive understanding (what humans need)
    
    Educational Note - The Power of Visualization:
    =============================================
    A single good plot can reveal:
    - Trends that aren't obvious in raw data
    - Errors or anomalies in calculations
    - Physical insights about the system
    - Patterns in complex multi-dimensional data
    
    In molecular simulations, visualization helps us:
    - See how atoms move and interact
    - Understand electronic structure
    - Identify reaction pathways
    - Validate simulation results
    """
    
    def __init__(self):
        """
        Initialize the visualization tools.
        
        Educational Note:
        ----------------
        Visualization tools need to be flexible because:
        1. Different data types require different approaches
        2. Users have different preferences and needs
        3. Scientific insights often come from exploring data visually
        """
        print("Visualization tools initialized")
        plt.style.use('seaborn-v0_8')  # Nice looking plots
    
    def plot_energy_history(self, energy_history: List[float], 
                           title: str = "Simulation Energy History") -> None:
        """
        Plot the energy history over simulation steps.
        
        Educational Note - What Energy History Tells Us:
        ===============================================
        The energy history plot reveals:
        - Convergence: Is the simulation stable?
        - Equilibration: Has the system reached equilibrium?
        - Fluctuations: How much does energy vary?
        - Trends: Is energy increasing, decreasing, or constant?
        
        In a good simulation:
        - Energy should fluctuate around a mean value
        - Large spikes might indicate problems
        - Long-term drift might indicate incomplete equilibration
        """
        steps = range(len(energy_history))
        
        plt.figure(figsize=(10, 6))
        plt.plot(steps, energy_history, 'b-', linewidth=2, marker='o', markersize=3)
        plt.xlabel('Simulation Step')
        plt.ylabel('Total Energy')
        plt.title(title)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Add statistics
        mean_energy = np.mean(energy_history)
        plt.axhline(y=mean_energy, color='r', linestyle='--', 
                   label=f'Mean: {mean_energy:.4f}')
        plt.legend()
        
        plt.show()
        
        print("Energy plot displayed:")
        print(f"  Mean energy: {mean_energy:.6f}")
        print(f"  Energy range: [{min(energy_history):.4f}, {max(energy_history):.4f}]")
    
    def plot_classical_trajectory(self, positions_history: List[np.ndarray],
                                 particle_indices: List[int] = [0, 1]) -> None:
        """
        Plot 3D trajectories of selected particles.
        
        Educational Note - Understanding Trajectories:
        =============================================
        Particle trajectories show:
        - How atoms move through space over time
        - Whether motion is random (gas) or structured (solid)
        - If particles are trapped or free-moving
        - Correlations between particle motions
        
        In 3D space, trajectories can reveal:
        - Diffusion patterns
        - Molecular rotations
        - Vibrational motions
        - Collective behavior
        """
        fig = plt.figure(figsize=(12, 5))
        
        # 3D trajectory plot
        ax1 = fig.add_subplot(121, projection='3d')
        
        colors = ['red', 'blue', 'green', 'orange', 'purple']
        
        for i, idx in enumerate(particle_indices):
            if idx < len(positions_history[0]):
                # Extract trajectory for this particle
                trajectory = np.array([step[idx] for step in positions_history])
                
                ax1.plot(trajectory[:, 0], trajectory[:, 1], trajectory[:, 2],
                        color=colors[i % len(colors)], linewidth=2,
                        label=f'Particle {idx}')
                ax1.scatter(trajectory[0, 0], trajectory[0, 1], trajectory[0, 2],
                           color=colors[i % len(colors)], s=100, marker='o')
                ax1.scatter(trajectory[-1, 0], trajectory[-1, 1], trajectory[-1, 2],
                           color=colors[i % len(colors)], s=100, marker='s')
        
        ax1.set_xlabel('X Position')
        ax1.set_ylabel('Y Position')
        ax1.set_zlabel('Z Position')
        ax1.set_title('3D Particle Trajectories')
        ax1.legend()
        
        # 2D projection plot
        ax2 = fig.add_subplot(122)
        
        for i, idx in enumerate(particle_indices):
            if idx < len(positions_history[0]):
                trajectory = np.array([step[idx] for step in positions_history])
                
                ax2.plot(trajectory[:, 0], trajectory[:, 1],
                        color=colors[i % len(colors)], linewidth=2,
                        label=f'Particle {idx}')
                ax2.scatter(trajectory[0, 0], trajectory[0, 1],
                           color=colors[i % len(colors)], s=100, marker='o')
                ax2.scatter(trajectory[-1, 0], trajectory[-1, 1],
                           color=colors[i % len(colors)], s=100, marker='s')
        
        ax2.set_xlabel('X Position')
        ax2.set_ylabel('Y Position')
        ax2.set_title('2D XY Projection')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
        
        print(f"Trajectory plot displayed for particles: {particle_indices}")
    
    def plot_quantum_orbitals(self, eigenvalues: np.ndarray,
                             eigenvectors: np.ndarray,
                             num_orbitals: int = 4) -> None:
        """
        Visualize quantum molecular orbitals.
        
        Educational Note - What Are Molecular Orbitals?
        ==============================================
        Molecular orbitals are quantum mechanical wavefunctions that describe
        where electrons are likely to be found in a molecule.
        
        Key concepts:
        - Each orbital has a specific energy (eigenvalue)
        - The square of the wavefunction gives probability density
        - Orbitals can be bonding (lower energy) or antibonding (higher energy)
        - Occupied orbitals contain electrons
        
        Visualization shows:
        - Orbital shape and symmetry
        - Energy ordering
        - Spatial distribution of electron density
        """
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        axes = axes.flatten()
        
        num_orbitals = min(num_orbitals, len(eigenvalues), len(axes))
        
        for i in range(num_orbitals):
            ax = axes[i]
            
            # Plot orbital energies as bar chart
            ax.bar([f'Orbital {i}'], [eigenvalues[i]], color='skyblue', alpha=0.7)
            ax.set_ylabel('Energy')
            ax.set_title(f'Orbital {i}: E = {eigenvalues[i]:.4f}')
            ax.grid(True, alpha=0.3)
        
        # Remove unused subplots
        for i in range(num_orbitals, len(axes)):
            axes[i].set_visible(False)
        
        plt.suptitle('Molecular Orbital Energies')
        plt.tight_layout()
        plt.show()
        
        print(f"Quantum orbital plot displayed for {num_orbitals} orbitals")
        for i in range(min(num_orbitals, len(eigenvalues))):
            print(f"  Orbital {i}: Energy = {eigenvalues[i]:.6f}")
    
    def create_animation(self, positions_history: List[np.ndarray],
                         interval: int = 200) -> None:
        """
        Create an animation of particle motion over time.
        
        Educational Note - Animation in Scientific Visualization:
        =======================================================
        Animations are powerful because they:
        - Show time evolution dynamically
        - Reveal motion patterns not visible in static plots
        - Help understand dynamic processes
        - Make complex data more accessible
        
        In molecular dynamics:
        - Animations show how structures evolve
        - Reveal collective motions and vibrations
        - Help identify phase transitions
        - Make abstract concepts tangible
        """
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Determine plot limits
        all_positions = np.concatenate(positions_history)
        x_min, y_min = all_positions[:, :2].min(axis=0) - 1
        x_max, y_max = all_positions[:, :2].max(axis=0) + 1
        
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.set_xlabel('X Position')
        ax.set_ylabel('Y Position')
        ax.set_title('Particle Motion Animation')
        ax.grid(True, alpha=0.3)
        
        # Initialize scatter plot
        scatter = ax.scatter([], [], s=50, c='blue', alpha=0.7)
        
        def animate(frame):
            positions = positions_history[frame]
            scatter.set_offsets(positions[:, :2])
            ax.set_title(f'Particle Motion - Step {frame}')
            return scatter,
        
        # Create animation
        _anim = animation.FuncAnimation(
            fig,
            animate,
            frames=len(positions_history),
            interval=interval,
            blit=True,
            repeat=True,
        )

        plt.show()

        print(f"Animation created with {len(positions_history)} frames")
        print("Close the window to continue...")
    
    def plot_comparison(self, classical_energies: List[float],
                       quantum_energies: List[float],
                       labels: List[str] = None) -> None:
        """
        Compare classical and quantum energy calculations.
        
        Educational Note - Why Compare Methods?
        ======================================
        Comparing different simulation methods helps us:
        - Validate results (do methods agree?)
        - Understand limitations (where do methods differ?)
        - Choose appropriate methods (when to use each?)
        - Improve models (how to make methods better?)
        
        In hybrid simulation, this comparison is essential for:
        - Calibrating classical models to quantum reference
        - Understanding when quantum detail is necessary
        - Optimizing the hybrid approach
        """
        if labels is None:
            labels = [f'Step {i}' for i in range(len(classical_energies))]
        
        x = range(len(classical_energies))
        
        plt.figure(figsize=(12, 6))
        
        plt.plot(x, classical_energies, 'b-o', linewidth=2, markersize=6,
                label='Classical Energy', alpha=0.7)
        plt.plot(x, quantum_energies, 'r-s', linewidth=2, markersize=6,
                label='Quantum Energy', alpha=0.7)
        
        plt.xlabel('Configuration')
        plt.ylabel('Energy')
        plt.title('Classical vs Quantum Energy Comparison')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Add difference plot
        plt.figure(figsize=(12, 6))
        differences = np.array(quantum_energies) - np.array(classical_energies)
        plt.plot(x, differences, 'g-', linewidth=2, marker='d', markersize=6)
        plt.xlabel('Configuration')
        plt.ylabel('Energy Difference (Quantum - Classical)')
        plt.title('Energy Difference: Quantum vs Classical')
        plt.grid(True, alpha=0.3)
        plt.axhline(y=0, color='k', linestyle='--', alpha=0.5)
        plt.tight_layout()
        
        plt.show()
        
        mean_diff = np.mean(differences)
        max_diff = np.max(np.abs(differences))
        
        print("Energy comparison displayed:")
        print(f"  Mean difference: {mean_diff:.6f}")
        print(f"  Max difference: {max_diff:.6f}")
        print("  This shows how quantum corrections improve classical results")

# ============================================================
# Module Summary:
# This visualization module helps users understand simulation results
# - Energy plots show simulation stability and convergence
# - Trajectory plots reveal particle motion patterns
# - Orbital plots show quantum mechanical properties
# - Animations make dynamic processes tangible
# - Comparisons validate different simulation approaches
# 
# Good visualization is essential for scientific understanding
# because it transforms abstract numbers into intuitive insights
# ============================================================

if __name__ == "__main__":
    """
    Minimal working example: Demonstrate visualization tools
    
    Educational Note: This shows how visualization helps understand data
    """
    print("=== Visualization Tools Demo ===")
    print("This demonstrates how to visualize simulation results")
    print("="*40)
    
    # Create some sample data
    np.random.seed(42)  # For reproducible results
    
    # Sample energy history (with some noise)
    steps = 50
    base_energy = -100.0
    energy_history = [base_energy + 0.1 * np.sin(0.2 * i) + 0.05 * np.random.randn() 
                     for i in range(steps)]
    
    # Sample positions history
    positions_history = []
    for i in range(steps):
        # Two particles moving in 3D space
        pos1 = np.array([2 + np.sin(0.1 * i), 1 + np.cos(0.1 * i), 0.5 * np.sin(0.2 * i)])
        pos2 = np.array([3 + 0.5 * np.cos(0.1 * i), 2 + np.sin(0.1 * i), 0.3 * np.cos(0.2 * i)])
        positions_history.append(np.array([pos1, pos2]))
    
    # Sample quantum data
    eigenvalues = np.array([-10.5, -5.2, -2.1, 1.3])
    eigenvectors = np.random.randn(4, 4)  # Simplified
    
    # Create visualizer
    visualizer = SimulationVisualizer()
    
    # Demonstrate different visualization types
    print("\n📊 Plotting energy history...")
    visualizer.plot_energy_history(energy_history[:20], "Sample Energy History")
    
    print("\n🏃 Plotting particle trajectories...")
    visualizer.plot_classical_trajectory(positions_history[:20], [0, 1])
    
    print("\n⚛️  Plotting quantum orbitals...")
    visualizer.plot_quantum_orbitals(eigenvalues, eigenvectors, 4)
    
    print("\n📈 Plotting method comparison...")
    classical_energies = energy_history[:10]
    quantum_energies = [e + 0.5 + 0.1 * np.random.randn() for e in classical_energies]
    visualizer.plot_comparison(classical_energies, quantum_energies)
    
    print("\n🎉 Visualization demo complete!")
    print("These tools help transform raw simulation data into insights")
