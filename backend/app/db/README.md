# Backend Database Module

## Overview

This directory contains the complete database infrastructure for Quantum Forge, including:

- SQLAlchemy ORM models for all entities
- Database connection and session management
- Pydantic schemas for API validation
- CRUD operations for all tables
- Structured event logging
- Configuration management

## Quick Start

1. **Set up environment:**

   ```bash
   cp ../../.env.example ../../.env
   # Edit .env with your Supabase credentials
   ```

2. **Install dependencies:**

   ```bash
   pip install -r ../../requirements.txt
   ```

3. **Test connection:**

   ```bash
   python ../scripts/test_database.py
   ```

## Module Structure

```
backend/app/
├── db/
│   ├── __init__.py       # Module exports
│   ├── models.py         # SQLAlchemy ORM (Molecule, Calculation, etc.)
│   ├── database.py       # Connection pool and session management
│   ├── schemas.py        # Pydantic request/response models
│   └── crud.py           # CRUD operations (170+ functions)
├── utils/
│   ├── __init__.py
│   └── logger.py         # Database event logging
└── config.py             # Configuration from environment
```

## Key Components

### Models (models.py)

Six ORM models with relationships:

- `Molecule` - Chemical structures
- `Calculation` - xTB quantum results
- `AtomicProperty` - Per-atom data
- `BatchJob` - Batch processing groups
- `BatchItem` - Batch membership tracking
- `EventLog` - Audit trail

### Database (database.py)

Connection management with:

- Connection pooling (50+ concurrent)
- Session factory for FastAPI
- Health checks
- Automatic table initialization
- Context managers

### Schemas (schemas.py)

Pydantic models for:

- Request/response validation
- API documentation (OpenAPI)
- Type hints and defaults
- Relationship handling

### CRUD (crud.py)

170+ functions for:

- Molecule operations (create, read, list, update, delete)
- Calculation queries (by energy, by gap, by molecule)
- Batch management (create, status tracking)
- Event logging (structured audit trail)
- Statistics (dashboard metrics)

### Logger (utils/logger.py)

Event logging for:

- Calculation start/complete/fail
- Batch start/complete/fail
- Molecule create/delete
- Custom errors and metrics

### Config (config.py)

Environment configuration:

- Database URL construction
- Supabase credentials
- Logging settings
- API configuration

## Usage Examples

### FastAPI Integration

```python
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from backend.app.db.database import setup_database, get_db
from backend.app.db import crud

app = FastAPI()

@app.on_event("startup")
async def startup():
    setup_database()

@app.get("/molecules")
def list_molecules(db: Session = Depends(get_db)):
    molecules, total = crud.list_molecules(db, limit=100)
    return {"molecules": molecules, "total": total}
```

### Standalone Usage

```python
from backend.app.db.database import get_db_context
from backend.app.db import crud

with get_db_context() as db:
    molecules, total = crud.list_molecules(db)
    print(f"Found {total} molecules")
```

### Creating Calculations

```python
from backend.app.db.schemas import CalculationCreate
from backend.app.db import crud

calc = crud.create_calculation(
    db,
    CalculationCreate(
        molecule_id=1,
        energy=-5.105,
        gap=0.60,
        dipole=1.85,
        execution_time_seconds=2.5
    )
)
```

### Event Logging

```python
from backend.app.utils import logger as db_logger

db_logger.log_calculation_completed(
    db=db,
    calculation_id=calc.id,
    molecule_id=mol.id,
    energy=-5.105,
    gap=0.60,
    execution_time_seconds=2.5
)
```

### Data Queries

```python
# Energy range queries
calcs = crud.get_calculations_by_energy_range(db, -10.0, 0.0)

# Gap filtering
calcs = crud.get_calculations_by_gap_range(db, 0.1, 1.0)

# Statistics
stats = crud.get_database_stats(db)
print(f"Success rate: {stats['success_rate']:.1f}%")
```

## Configuration

Set these environment variables in `.env`:

```bash
# Supabase connection
DATABASE_URL=postgresql://postgres:PASSWORD@PROJECT.supabase.co:5432/postgres

# Or component-based:
DB_USER=postgres
DB_PASSWORD=PASSWORD
DB_HOST=PROJECT.supabase.co
DB_PORT=5432
DB_NAME=postgres

# Logging
LOG_LEVEL=INFO
LOG_FILE=/workspace/logs/app.log

# API
API_HOST=0.0.0.0
API_PORT=8000
```

## API Reference

### Molecules

- `create_molecule(db, molecule_create)` → Molecule
- `get_molecule(db, id)` → Molecule | None
- `get_molecule_by_smiles(db, smiles)` → Molecule | None
- `list_molecules(db, skip=0, limit=100)` → (List[Molecule], int)
- `update_molecule(db, id, update_data)` → Molecule
- `delete_molecule(db, id)` → bool

### Calculations

- `create_calculation(db, calc_create)` → Calculation
- `get_calculation(db, id)` → Calculation | None
- `list_calculations(db, molecule_id=None, skip=0, limit=100)` → (List[Calculation], int)
- `get_calculations_by_energy_range(db, min, max, limit=1000)` → List[Calculation]
- `get_calculations_by_gap_range(db, min, max, limit=1000)` → List[Calculation]

### Atomic Properties

- `create_atomic_properties(db, calc_id, properties_list)` → List[AtomicProperty]
- `get_atomic_properties_for_calculation(db, calc_id)` → List[AtomicProperty]

### Batch Operations

- `create_batch_job(db, batch_create)` → BatchJob
- `get_batch_job(db, id)` → BatchJob | None
- `list_batch_jobs(db, status=None, skip=0, limit=100)` → (List[BatchJob], int)
- `update_batch_job_status(db, id, status)` → BatchJob
- `create_batch_item(db, item_create)` → BatchItem
- `get_batch_items(db, batch_id, status=None)` → List[BatchItem]
- `update_batch_item_status(db, id, status, calculation_id=None)` → BatchItem

### Event Logging

- `log_event(db, event_type, entity_type, ...)` → EventLog
- `get_event_logs(db, entity_type=None, status=None, ...)` → (List[EventLog], int)

### Statistics

- `get_database_stats(db)` → Dict[str, Any]
  - `total_molecules`
  - `total_calculations`
  - `total_batches`
  - `average_energy`
  - `median_gap`
  - `success_rate`
  - `latest_calculation_at`

## Testing

Run the test suite:

```bash
python ../scripts/test_database.py
```

Expected output shows:

- Connection testing
- CRUD operations
- Performance benchmarks
- Statistics calculation
- Event logging

## Documentation

- **Full Guide:** `../../docs/DATABASE.md`
- **Setup Guide:** `../../docs/DATABASE_SETUP.md`
- **Checklist:** `../../docs/IMPLEMENTATION_CHECKLIST.md`
- **Summary:** `../../docs/DATABASE_DELIVERY_SUMMARY.md`

## Performance

- Connection pool: 20 + 30 overflow = 50+ concurrent requests
- Indexes on: molecules.smiles, calculations(molecule_id, created_at), event_logs(user_id, created_at, event_type)
- Designed for 1M+ rows with sub-second indexed queries
- Connection recycling every 3600s (Supabase timeout)

## Data Safety

- Row-Level Security (RLS) for multi-tenant isolation
- UNIQUE constraint on SMILES for de-duplication
- Foreign key constraints with CASCADE delete
- Transaction-based operations (ACID)
- Comprehensive audit trail (event_logs)

## Migration

Migrate existing filesystem data:

```bash
python ../scripts/migrate_existing_data.py --dry-run
python ../scripts/migrate_existing_data.py
```

## Support

For issues, check:

1. `../../docs/DATABASE.md` - Troubleshooting section
2. `../../docs/DATABASE_SETUP.md` - Quick reference
3. Test suite output: `python ../scripts/test_database.py`

## License

Part of the Quantum Forge project. See root LICENSE file.
