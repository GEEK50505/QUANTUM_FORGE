# Glossary — Quantum_Forge

This glossary defines domain-specific terms used across the codebase and
documentation. It is targeted at the junior developer onboarding to the
project and for reference in code comments.

- xTB: extended Tight Binding — a fast semi-empirical quantum chemistry
  method for estimating molecular energies and performing geometry
  optimizations. Good speed/accuracy balance for workflows where full DFT
  is too expensive.

- DFT: Density Functional Theory — a more accurate (and generally slower)
  quantum mechanical method for electronic structure calculations.

- Hartree: The atomic unit of energy (1 Hartree ≈ 27.2114 eV). Used in
  quantum chemistry outputs.

- HOMO/LUMO: Highest Occupied / Lowest Unoccupied Molecular Orbitals.
  The HOMO-LUMO gap is a simple measure of electronic excitation energy
  (reactivity proxy).

- Geometry optimization: A calculation that iteratively adjusts atomic
  coordinates to find a local minimum of the potential energy surface.

- XYZ file: A simple text format describing a molecule by atom count,
  an optional comment line, and one row per atom with element and 3D
  coordinates.

- REST API: Representational State Transfer — HTTP-based API patterns
  used by the frontend to talk to the backend.

- FastAPI: Python web framework used for high-performance REST APIs in
  this project.

- React: JavaScript library used for the frontend UI.

- Async/await: JavaScript/TypeScript syntax for asynchronous operations.

- State management: Tracking and updating UI state in React components.

- Middleware: Code that runs between request and response (in backend)

For more terms, see other docs in this folder.
