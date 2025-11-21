# QUANTUM_FORGE Platform Structure

## Core Components

### Backend (`/backend`)

#### API Layer (`/backend/api`)
- Main FastAPI application
- API routes and endpoints
- Request/response schemas
- Job management

#### Core Logic (`/backend/core`)
- Core business logic
- Configuration management
- Logging and monitoring
- XTB runner integration

#### Simulation Engine (`/backend/simulation`)
- Classical simulation (XTB)
- Quantum kernel integration
- Hybrid pipeline
- Utility functions

#### Data Layer (`/backend/db`)
- Database models
- Job storage
- Data persistence

### Frontend (`/frontend`)

#### Source Code (`/src`)
- React components
- TypeScript interfaces
- State management
- API integration

#### Public Assets (`/public`)
- Static files
- Images and icons
- Public resources

#### Components
- UI components
- Form elements
- Visualization tools
- Layout components

### Documentation (`/docs`)
- API documentation
- Architecture decisions
- Project structure
- Onboarding guide

### Configuration
- `package.json` - Frontend dependencies
- `requirements.txt` - Python dependencies
- `tsconfig.json` - TypeScript configuration
- Build and deployment configs

## Development Notes

1. This structure represents the core platform functionality
2. Development tools and workflow enhancements are maintained separately in `.devtools`
3. Each component is designed to be modular and maintainable
4. Follow the established patterns when adding new features