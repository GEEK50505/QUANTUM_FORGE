# Quantum Forge 🚀

**Next-generation AI-driven scientific computing platform that fuses:**

- Stochastic computing (energy-efficient probabilistic logic)
- Classical + Quantum simulation
- AI-assisted code generation & reproducible research

---

## 🧪 Hybrid Quantum-Classical Simulation Platform

Quantum Forge is a revolutionary platform for atom-accurate simulation of materials and electronic devices. It combines the speed of classical molecular dynamics with the accuracy of quantum mechanical calculations.

**⚠️ NOTE: This project is currently under active development. Features and APIs are subject to change.**

### 🔬 What is Hybrid Simulation?

Think of hybrid simulation like a "multi-scale microscope":

- **Classical part**: Shows the overall structure and motion (like a wide-angle lens)
- **Quantum part**: Shows detailed electronic properties (like a high-magnification lens)
- **Hybrid**: Switches between scales as needed for efficiency and accuracy

This approach gets the best of both worlds:

- **Speed**: Classical methods handle 90%+ of the work
- **Accuracy**: Quantum methods provide detailed information when needed
- **Scalability**: Can handle large systems with quantum accuracy in key regions

---

## 📁 Project Structure

```
QUANTUM_FORGE/
├── backend/                  # Core simulation engine
│   ├── api/                 # FastAPI application
│   ├── core/                # Core business logic
│   ├── simulation/          # Simulation components
│   └── db/                  # Data persistence
├── frontend/                # React-based web interface
│   ├── src/                # Application source
│   └── public/             # Static assets
├── docs/                    # Documentation and guides
│   ├── api/                # API documentation
│   └── tutorials/          # User guides
├── data/                    # Simulation data
├── tests/                   # Test suite
└── requirements.txt        # Python dependencies

For development environment setup, see `.devtools/SETUP.md`
```

---

## 🚀 Quick Start

| Feature | Description | Status |
|---------|-------------|--------|
| **Hybrid Architecture** | Best of classical and quantum methods | Under Development |
| **Educational Focus** | Detailed explanations for learning | Under Development |
| **Modular Design** | Easy to extend and customize | Under Development |
| **Visualization Tools** | Transform data into insights | Under Development |
| **AI Integration** | Future-ready for machine learning | Planned |
| **Web Interface** | React-based dashboard | Under Development |

---

## 🚀 Future Roadmap

- [ ] AI-assisted parameter optimization
- [ ] Stochastic computing integration
- [ ] Cloud deployment options
- [ ] Advanced quantum algorithms (VQE, QAOA)
- [ ] Multi-tenant SaaS architecture

---

## 📖 Documentation

For detailed documentation, see:

- `docs/` directory for tutorials
- Module docstrings for API reference
- `notebooks/` for interactive examples
- `docs/api contracts/api_contract.md` for API specifications

## Troubleshooting

**Network Unreachable / IPv6 Errors**

Some Supabase Direct Postgres endpoints resolve to IPv6-only addresses. Developer machines, Docker hosts, or CI runners without IPv6 routing will see errors like:

- psycopg2.OperationalError: connection to "<db>.supabase.co" port 5432 failed: Network is unreachable

What to do:

- Use the Supavisor Connection Pooler (Session Mode) URL from the Supabase dashboard (Connection Pooling → Session). This pooler exposes IPv4-compatible endpoints and listens on port `5432` (e.g. `<project>.pooler.supabase.com:5432`).
- Copy the *Session* connection string from the Supabase dashboard and set it as your `DATABASE_URL` in your `.env` (or `.env.local`) file — do not use the direct `*.supabase.co` host in IPv4-only environments.
- If you run the worker in Docker/devcontainer, use the pooler URL (Session Mode). The repository's `.env.example` now documents this requirement.

If you cannot use the pooler, alternative options are:

- Enable IPv6 routing on your host/network.
- Run the worker on a host that has IPv6 connectivity (for example, the gateway machine).
- Create a secure SSH tunnel via a machine with IPv6 (not recommended for production without proper key management).

---

## 🤝 Contributing

Quantum Forge welcomes contributions from:

- Scientists and researchers
- Software engineers
- Educators and students
- Industry professionals

**⚠️ Important**: This project is currently under active development. Please check the current status before contributing.

---

## 📄 License

Quantum Forge is ????-source software for advancing scientific computing and education.

---

*"Democratizing complex simulation and accelerating discovery"*

[Multi-tenant SaaS, API, and on-prem deployment ready - under development]
