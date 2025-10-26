# Quantum Forge - H₂ Hybrid Simulation Example
# Author: Qwen 3 Coder
# Description: Complete example of hybrid simulation for H₂ molecule
# --------------------------------------------------------------

# ============================================================
# Example Purpose: Demonstrate complete hybrid H₂ simulation
# What this example does: 
#   1. Simulates H₂ molecule vibration using classical mechanics
#   2. Calculates electronic energy using quantum mechanics
#   3. Combines results in hybrid framework
# ============================================================

"""
H₂ Hybrid Simulation Example

This script demonstrates the complete hybrid quantum-classical simulation
workflow using the Quantum Forge platform, specifically for the H₂ molecule.

Educational Note - Why H₂?
========================
The hydrogen molecule (H₂) is the simplest molecule in the universe:
- 2 protons (nuclei)
- 2 electrons
- Simplest quantum mechanical system with chemical bonding

H₂ is perfect for demonstrating hybrid simulation because:
1. Simple enough to understand completely
2. Complex enough to show quantum effects
3. Fast to compute for examples
4. Physically meaningful results

The simulation shows:
1. Classical: How H atoms vibrate (Newtonian mechanics)
2. Quantum: How electrons behave (Schrödinger equation)
3. Hybrid: Combined picture of nuclear motion + electronic structure
"""

import sys
import os
import numpy as np

# Add src to path to import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from classical_sim.classical_simulator import ClassicalSimulator
from quantum_kernel.quantum_solver import QuantumSolver
from hybrid_pipeline.hybrid_simulator import HybridSimulator
from utils.visualization import SimulationVisualizer

def run_h2_classical_simulation():
    """
    Run classical simulation of H₂ vibration.
    
    Educational Note - Classical H₂ Model:
    ===================================
    In the classical model:
    - H atoms are point particles with mass
    - They interact via forces (Lennard-Jones potential)
    - Motion follows Newton's laws: F = ma
    - Energy is conserved (in ideal system)
    
    This gives us:
    - Nuclear positions over time
    - Vibrational motion
    - Classical energy estimates
    """
    print("=== Classical H₂ Simulation ===")
    print("Simulating H₂ vibration using Newtonian mechanics")
    print("- H atoms treated as classical particles")
    print("- Motion governed by forces and F = ma")
    print("- Fast computation for large systems")
    print("="*50)
    
    # Create classical simulator for just 2 H atoms
    classical_sim = ClassicalSimulator(
        num_particles=2,        # Just H₂ molecule
        box_size=10.0,          # Large enough box
        temperature=50.0        # Low temperature for controlled motion
    )
    
    # Run a short simulation to get some motion
    positions_history = []
    energy_history = []
    
    for step in range(30):
        classical_sim.run_step(dt=0.01)
        positions_history.append(classical_sim.get_positions().copy())
        # Simple energy estimate
        kinetic = 0.5 * np.sum(classical_sim.velocities**2)
        potential = classical_sim._calculate_potential_energy()
        energy_history.append(kinetic + potential)
    
    print(f"\nClassical simulation complete!")
    print(f"Final H-H distance: {np.linalg.norm(positions_history[-1][0] - positions_history[-1][1]):.4f} Å")
    
    return positions_history, energy_history

def run_h2_quantum_calculation(h2_positions):
    """
    Run quantum calculation for H₂ electronic structure.
    
    Educational Note - Quantum H₂ Model:
    ==================================
    In the quantum model:
    - Electrons are wavefunctions (probability distributions)
    - Solve Schrödinger equation: HΨ = EΨ
    - Include electron correlation and quantum effects
    - Much more accurate but computationally expensive
    
    This gives us:
    - Exact electronic energy
    - Molecular orbitals
    - Quantum mechanical wavefunctions
    """
    print("\n=== Quantum H₂ Calculation ===")
    print("Calculating H₂ electronic structure using quantum mechanics")
    print("- Electrons treated as quantum wavefunctions")
    print("- Solving Schrödinger equation HΨ = EΨ")
    print("- Includes electron correlation effects")
    print("="*50)
    
    # Create quantum solver for H₂ (2 electrons)
    quantum_solver = QuantumSolver(
        num_electrons=2,        # H₂ has 2 electrons
        num_orbitals=4,         # Minimal basis for demonstration
        basis_type="minimal"
    )
    
    # Calculate quantum mechanical energy
    total_energy = quantum_solver.calculate_electronic_energy(h2_positions)
    
    # Get molecular orbitals
    orbitals = quantum_solver.get_molecular_orbitals()
    eigenvalues = quantum_solver.eigenvalues if hasattr(quantum_solver, 'eigenvalues') else None
    
    print(f"\nQuantum calculation complete!")
    print(f"H-H distance: {np.linalg.norm(h2_positions[0] - h2_positions[1]):.4f} Å")
    print(f"Total electronic energy: {total_energy:.6f} Hartree")
    
    return total_energy, eigenvalues, orbitals

def run_h2_hybrid_simulation():
    """
    Run complete hybrid simulation of H₂.
    
    Educational Note - Hybrid H₂ Simulation:
    ======================================
    The hybrid approach combines:
    1. Classical simulation: Fast nuclear motion
    2. Quantum calculation: Accurate electronic structure
    3. Intelligent switching: Quantum when needed
    
    Benefits:
    - Speed of classical for nuclear dynamics
    - Accuracy of quantum for electronic properties
    - Efficient use of computational resources
    - Physically meaningful results
    """
    print("=== Hybrid H₂ Simulation ===")
    print("Combining classical and quantum methods")
    print("- Classical: Fast H atom motion")
    print("- Quantum: Accurate electron behavior")
    print("- Hybrid: Best of both worlds")
    print("="*50)
    
    # Create hybrid simulator
    hybrid_sim = HybridSimulator(
        num_classical_particles=2,      # Just H₂
        num_quantum_electrons=2,        # H₂ electrons
        box_size=5.0,                   # Small box for H₂
        temperature=100.0               # Moderate temperature
    )
    
    # Run hybrid simulation
    energy_history = hybrid_sim.run_simulation(
        num_steps=25,                    # Short demo
        dt=0.01,                        # Time step
        quantum_frequency=5             # Quantum calc every 5 steps
    )
    
    # Get final results
    positions = hybrid_sim.get_classical_positions()
    h2_distance = np.linalg.norm(positions[0] - positions[1])
    
    quantum_results = hybrid_sim.get_quantum_results()
    
    print(f"\nFinal H₂ configuration:")
    print(f"H-H distance: {h2_distance:.4f} Å")
    
    if quantum_results is not None:
        eigenvalues, eigenvectors = quantum_results
        print(f"Ground state energy: {eigenvalues[0]:.6f} Hartree")
    
    return energy_history, positions, quantum_results

def visualize_h2_results(classical_positions, classical_energies, 
                        hybrid_energies, quantum_results):
    """
    Visualize the H₂ simulation results.
    
    Educational Note - Importance of Visualization:
    ==============================================
    Visualization transforms abstract numbers into insights:
    - Energy plots show simulation stability
    - Trajectory plots reveal molecular motion
    - Orbital diagrams show electron distribution
    - Comparisons validate different methods
    """
    print("\n=== Visualizing H₂ Results ===")
    print("Creating plots to understand simulation results")
    print("="*50)
    
    # Create visualizer
    visualizer = SimulationVisualizer()
    
    # Plot classical energy history
    print("\n📊 Plotting classical energy history...")
    visualizer.plot_energy_history(classical_energies[:15], "H₂ Classical Energy")
    
    # Plot trajectories
    print("\n🏃 Plotting H₂ trajectories...")
    visualizer.plot_classical_trajectory(classical_positions[:15], [0, 1])
    
    # Plot quantum results if available
    if quantum_results is not None:
        eigenvalues, eigenvectors = quantum_results
        print("\n⚛️  Plotting quantum orbitals...")
        visualizer.plot_quantum_orbitals(eigenvalues, eigenvectors, 4)
    
    # Compare methods
    print("\n📈 Comparing classical and hybrid energies...")
    min_len = min(len(classical_energies), len(hybrid_energies))
    visualizer.plot_comparison(
        classical_energies[:min_len], 
        hybrid_energies[:min_len]
    )

def main():
    """
    Main function: Run complete H₂ hybrid simulation demonstration.
    
    Educational Note - This is the complete workflow:
    ==============================================
    1. Classical simulation: Fast nuclear motion
    2. Quantum calculation: Accurate electronic structure
    3. Hybrid simulation: Combined approach
    4. Visualization: Understanding results
    
    This demonstrates how Quantum Forge makes complex
    quantum-classical simulation accessible and understandable.
    """
    print("🚀 Quantum Forge H₂ Hybrid Simulation Demo")
    print("="*60)
    print("This demonstrates hybrid quantum-classical simulation")
    print("for the hydrogen molecule (H₂) - the simplest molecule")
    print("="*60)
    
    try:
        # Step 1: Classical simulation
        print("\nStep 1: Classical H₂ Simulation")
        classical_positions, classical_energies = run_h2_classical_simulation()
        
        # Step 2: Quantum calculation (at final positions)
        print("\nStep 2: Quantum H₂ Calculation")
        final_h2_positions = classical_positions[-1][:2]  # Just H atoms
        quantum_energy, eigenvalues, orbitals = run_h2_quantum_calculation(final_h2_positions)
        
        # Step 3: Hybrid simulation
        print("\nStep 3: Hybrid H₂ Simulation")
        hybrid_energies, final_positions, quantum_results = run_h2_hybrid_simulation()
        
        # Step 4: Visualization
        print("\nStep 4: Visualization and Analysis")
        visualize_h2_results(classical_positions, classical_energies, 
                           hybrid_energies, quantum_results)
        
        # Summary
        print("\n" + "="*60)
        print("✅ H₂ Hybrid Simulation Complete!")
        print("="*60)
        print("Key Results:")
        print(f"  📏 Final H-H distance: {np.linalg.norm(final_positions[0] - final_positions[1]):.4f} Å")
        print(f"  ⚡ Classical energy range: [{min(classical_energies):.4f}, {max(classical_energies):.4f}]")
        print(f"  🧠 Hybrid energy range: [{min(hybrid_energies):.4f}, {max(hybrid_energies):.4f}]")
        
        if quantum_results is not None:
            eigenvalues, _ = quantum_results
            print(f"  ⚛️  Quantum ground state: {eigenvalues[0]:.6f} Hartree")
        
        print("\n🎯 What You Learned:")
        print("  - Classical: Fast nuclear motion (Newtonian mechanics)")
        print("  - Quantum: Accurate electronic structure (Schrödinger equation)")
        print("  - Hybrid: Efficient combination of both methods")
        print("  - Visualization: Transforming data into insights")
        
        print("\n🌟 This demonstrates the power of hybrid simulation!")
        print("   Complex quantum systems made accessible and understandable.")
        
    except Exception as e:
        print(f"\n❌ Error in simulation: {str(e)}")
        print("Please check that all dependencies are installed.")
        print("Run: pip install -r requirements.txt")

if __name__ == "__main__":
    main()
