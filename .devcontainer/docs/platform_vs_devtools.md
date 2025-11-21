# Platform vs Development Tools

## Platform Components (Main Codebase)

### Core Functionality
- `/backend/*` - Server, API, and simulation logic
- `/frontend/*` - User interface and client-side code
- `/docs/*` - Platform documentation
- Configuration files (package.json, requirements.txt, etc.)

### Key Features
- Quantum chemistry calculations
- Simulation pipelines
- User interface
- Data management

## Development Tools (.devtools)

### VS Code Integration
- Editor settings
- Launch configurations
- Debugging setups

### Extension Support
- Roo Code integration
- Cline extension setup
- Development assistance tools

### OpenRouter Integration
- API key management
- Development environment
- Testing tools

### Scripts
- Environment setup
- Key management
- Development utilities

## Important Notes

1. Keep platform code and development tools separate
2. Do not import development tools in platform code
3. Development tools are for local use only
4. Platform code should work without development tools