# Benzene xTB Calculation Results

## Overview
- **Molecule:** Benzene (C6H6)
- **Method:** xTB (GFN2-xTB)
- **Status:** ✅ CONVERGED
- **Date:** 2025-11-02 10:38:52

## Key Results

### Energetics
- **Total Energy:** -14.420 Hartree (-392.5 eV)
- **HOMO-LUMO Gap:** 0.117 eV
- **Optimization Iterations:** 219
- **Gradient Norm:** 0.0027 Eh/a0 (excellent convergence)

### Computational Performance
- **Wall Time:** 2.23 seconds
- **CPU Time:** 9.44 seconds
- **Speedup (Parallel):** 4.23x

### Molecular Properties
- **Dipole Moment:** 1.196 Debye
- **Polarizability:** 98.27 a.u.
- **Molecular Mass:** 78.11 u

## Files Generated
| File | Purpose |
|------|---------|
| `xtbopt.xyz` | Optimized 3D coordinates |
| `charges` | Atomic partial charges |
| `wbo` | Wiberg bond orders |
| `xtbopt.log` | Full calculation log |
| `xtbtopo.mol` | Molecular topology |

## Quality Checks
✅ Geometry optimization converged
✅ Gradient norm < 0.01 (excellent)
✅ HOMO-LUMO gap physically reasonable
✅ Energy matches expected value

## References
- xTB Version: 6.7.1
- Hamiltonian: GFN2-xTB
- Reference: Bannwarth, Ehlert, Grimme, JCTC 2019
