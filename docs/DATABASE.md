# Quantum Forge Database Documentation

## Overview

This document describes the Supabase PostgreSQL database infrastructure for Quantum Forge, including schema design, API integration, and operational procedures.

## Quick Start

### 1. Get Supabase Credentials

1. Create a project at [https://app.supabase.com](https://app.supabase.com)
2. Go to **Settings → Database** to find:
   - **Host**: `[YOUR_PROJECT].supabase.co`
   - **Password**: Your database password
   - **User**: `postgres` (default)

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your Supabase credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```bash
# Connection string (recommended - Supabase connection pooler)
DATABASE_URL=postgresql://postgres:[PASSWORD]@[PROJECT].supabase.co:5432/postgres

# Or use components:
DB_USER=postgres
DB_PASSWORD=[PASSWORD]
DB_HOST=[PROJECT].supabase.co
DB_PORT=5432
DB_NAME=postgres

SUPABASE_URL=https://[PROJECT].supabase.co
SUPABASE_KEY=[YOUR_ANON_KEY]
```

### 3. Initialize Database Schema

Run the migration script in Supabase SQL Editor:

1. Open Supabase Dashboard → **SQL Editor**
2. Click **New Query**
3. Copy contents of `backend/scripts/schema.sql`
4. Click **Run**

This creates all tables, indexes, RLS policies, and indexes.

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 5. Test Connection

```bash
python backend/scripts/test_database.py
```

Expected output:

```
✓ PASS: Config validation
✓ PASS: Engine creation
✓ PASS: Health check
✓ PASS: Create molecule
...
Overall: X/Y tests passed
```

## Database Schema

### Tables

#### molecules

Stores unique molecular structures.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| user_id | UUID | User ID for multi-tenant isolation |
| name | VARCHAR(255) | Human-readable name (e.g., "water") |
| smiles | TEXT | SMILES notation (unique) |
| formula | VARCHAR(255) | Chemical formula (e.g., "H2O") |
| created_at | TIMESTAMP | Creation time |
| updated_at | TIMESTAMP | Last modification |
| metadata | JSONB | Extensible fields |

**Indexes**: smiles (unique), user_id, created_at

**Use Case**: De-duplicate molecules across multiple calculations and batches

#### calculations

xTB calculation results (PRIMARY table for ML training data).

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| molecule_id | INTEGER | Foreign key to molecules |
| energy | FLOAT | Total energy (Hartree) |
| homo | FLOAT | HOMO energy (eV) |
| lumo | FLOAT | LUMO energy (eV) |
| gap | FLOAT | HOMO-LUMO gap (eV) |
| dipole | FLOAT | Dipole moment (Debye) |
| execution_time_seconds | FLOAT | Runtime |
| xtb_version | VARCHAR(50) | xTB version used |
| convergence_status | VARCHAR(50) | converged / error / etc |
| created_at | TIMESTAMP | Creation time |
| metadata | JSONB | Custom fields |

**Indexes**: molecule_id, created_at, energy, gap, (molecule_id, created_at)

**Use Case**: ML training dataset, energy analysis, gap filtering

#### atomic_properties

Per-atom data for atom-level ML models.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| calculation_id | INTEGER | Foreign key to calculations |
| atom_index | INTEGER | 0-based index in molecule |
| element | VARCHAR(3) | Element symbol |
| partial_charge | FLOAT | Mulliken charge |
| position_x/y/z | FLOAT | Coordinates (Angstroms) |
| force_x/y/z | FLOAT | Forces (Hartree/Bohr) |

**Indexes**: calculation_id, element

**Use Case**: Feature engineering for atom-level predictions, force field parameterization

#### batch_jobs

Groups molecules for bulk processing.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| batch_name | VARCHAR(255) | User-friendly name |
| status | VARCHAR(50) | pending / in_progress / completed |
| total_molecules | INTEGER | Expected count |
| successful_count | INTEGER | Successfully completed |
| failed_count | INTEGER | Failed calculations |
| parameters | JSONB | Shared xTB parameters |
| created_at | TIMESTAMP | Start time |

**Use Case**: Track large screening campaigns, monitor progress

#### batch_items

Many-to-many link between batches and molecules.

| Column | Type | Description |
|--------|------|-------------|
| batch_id | INTEGER | Foreign key to batch_jobs |
| molecule_id | INTEGER | Foreign key to molecules |
| status | VARCHAR(50) | pending / processing / completed / failed |
| calculation_id | INTEGER | Link to result |
| error_message | TEXT | Error details if failed |

**Constraints**: Unique (batch_id, molecule_id)

**Use Case**: Track per-molecule status within batch

#### event_logs

Comprehensive audit trail of all operations.

| Column | Type | Description |
|--------|------|-------------|
| id | BIGSERIAL | Primary key |
| event_type | VARCHAR(50) | calculation_started, batch_completed, etc |
| entity_type | VARCHAR(50) | molecules, calculations, batches |
| entity_id | INTEGER | ID of affected entity |
| status | VARCHAR(50) | success / warning / error |
| error_message | TEXT | Error details if status=error |
| context | JSONB | Full event context |
| created_at | TIMESTAMP | When event occurred |

**Indexes**: (user_id, created_at DESC, event_type), event_type, status

**Use Case**: Debugging, monitoring, GDPR compliance

## Python API

### Database Connection

```python
from backend.app.db.database import setup_database, get_db_context

# Application startup
engine, SessionLocal = setup_database()

# In routes (FastAPI)
from fastapi import Depends
from backend.app.db.database import get_db

@app.get("/molecules")
def list_molecules(db: Session = Depends(get_db)):
    return db.query(Molecule).all()

# Outside routes (scripts)
from backend.app.db.database import get_db_context

with get_db_context() as db:
    molecules = db.query(Molecule).all()
```

### CRUD Operations

```python
from backend.app.db import crud
from backend.app.db.schemas import MoleculeCreate, CalculationCreate

# Create molecule
mol = crud.create_molecule(
    db,
    MoleculeCreate(
        name="water",
        smiles="O",
        formula="H2O"
    )
)

# Get molecule
mol = crud.get_molecule(db, molecule_id=1)

# List molecules with pagination
molecules, total = crud.list_molecules(db, skip=0, limit=100)

# Create calculation
calc = crud.create_calculation(
    db,
    CalculationCreate(
        molecule_id=mol.id,
        energy=-5.105,
        gap=0.60,
        execution_time_seconds=2.5
    )
)

# Query by energy range (ML feature queries)
calcs = crud.get_calculations_by_energy_range(db, -10.0, 0.0)

# Get statistics
stats = crud.get_database_stats(db)
print(stats['total_molecules'])
print(stats['success_rate'])
```

### Event Logging

```python
from backend.app.utils import logger as db_logger

# Log calculation start
db_logger.log_calculation_started(
    db=db,
    calculation_id=calc.id,
    molecule_id=mol.id,
    xtb_version="6.7.1",
    method="GFN2-xTB"
)

# Log completion
db_logger.log_calculation_completed(
    db=db,
    calculation_id=calc.id,
    molecule_id=mol.id,
    energy=-5.105,
    gap=0.60,
    execution_time_seconds=2.5
)

# Log failure
db_logger.log_calculation_failed(
    db=db,
    calculation_id=calc.id,
    molecule_id=mol.id,
    error_message="xTB crashed with signal 11",
    error_code="XTB_SEGFAULT"
)
```

## Data Migration

Migrate existing xTB results from filesystem to database:

```bash
# Test migration (dry-run)
python backend/scripts/migrate_existing_data.py --dry-run

# Run migration
python backend/scripts/migrate_existing_data.py

# With options
python backend/scripts/migrate_existing_data.py \
    --jobs-root /workspace/jobs \
    --limit 100 \
    --user-id "user-uuid-here"
```

Output includes:

- Molecules created/skipped
- Calculations migrated
- Atomic properties imported
- Any errors encountered
- Total duration

## Integration with xTB Runner

Update `backend/core/xtb_runner.py` to log to database:

```python
from backend.app.utils import logger as db_logger

class XTBRunner:
    def execute(self, job_id, xyz_file, db):
        try:
            db_logger.log_calculation_started(
                db=db,
                calculation_id=job_id,
                molecule_id=molecule_id,
                xtb_version=self.version
            )
            
            # Run xTB...
            result = self.parse_output(stdout)
            
            db_logger.log_calculation_completed(
                db=db,
                calculation_id=job_id,
                molecule_id=molecule_id,
                energy=result['energy'],
                execution_time_seconds=elapsed
            )
            
        except Exception as e:
            db_logger.log_calculation_failed(
                db=db,
                calculation_id=job_id,
                error_message=str(e)
            )
            raise
```

## Row-Level Security (RLS)

All tables have RLS enabled. Users can only see their own data via `user_id`:

```sql
-- Example: Users can only view their own molecules
CREATE POLICY "Users can view their own molecules" ON molecules
    FOR SELECT USING (auth.uid() = user_id OR user_id IS NULL);
```

For service-level access (backend API), use:

- `SUPABASE_URL` + `SUPABASE_KEY` (service role key from Supabase)
- Or PostgreSQL connection directly with `postgres` user

## Performance Optimization

### Indexes

All critical queries have indexes:

- `calculations(molecule_id, created_at)` for ML dataset queries
- `calculations(energy)` for range queries  
- `event_logs(user_id, created_at DESC, event_type)` for audit trails

### Connection Pooling

- Pool size: 20 connections
- Max overflow: 30 additional connections
- Total capacity: 50+ concurrent requests
- Pool recycle: 3600 seconds (Supabase default)

### Query Tips

```python
# ✓ Fast: Use indexed columns
calcs = db.query(Calculation)\
    .filter(Calculation.molecule_id == mol_id)\
    .filter(Calculation.created_at > cutoff_date)\
    .limit(1000)

# ✗ Slow: Full table scan
calcs = db.query(Calculation)\
    .filter(Calculation.metadata['custom_field'].astext == 'value')\
    .all()

# Batch operations for better performance
db.add_all(calculations)  # Add many at once
db.commit()
```

## Monitoring & Maintenance

### Health Check

```python
from backend.app.db.database import check_db_health

health = check_db_health(engine)
print(health)  # {'status': 'healthy', 'database': 'postgres', ...}
```

### Check Table Sizes

```sql
SELECT 
    table_name,
    pg_size_pretty(pg_total_relation_size(table_name))
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY pg_total_relation_size(table_name) DESC;
```

### Monitor Event Logs

```sql
-- Recent errors
SELECT event_type, error_message, COUNT(*) 
FROM event_logs 
WHERE status = 'error' 
GROUP BY event_type, error_message 
ORDER BY max(created_at) DESC;

-- Calculation success rate
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total,
    COUNT(CASE WHEN convergence_status = 'converged' THEN 1 END) as successful,
    ROUND(100.0 * COUNT(CASE WHEN convergence_status = 'converged' THEN 1 END) / COUNT(*), 1) as success_rate
FROM calculations
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

### Backup Strategy

Supabase automatically backs up data. You can also:

1. Use Supabase CLI to backup: `supabase db pull`
2. Schedule periodic exports via pg_dump
3. Keep JSON exports of critical data

## Troubleshooting

### Connection Errors

```
psycopg2.OperationalError: could not connect to server
```

- Check `DATABASE_URL` is correct
- Verify firewall allows port 5432
- Ensure Supabase project is active

### RLS Policy Errors

```
ERROR: new row violates row-level security policy
```

- Check `user_id` is set correctly
- Verify Supabase `auth.uid()` returns expected value
- Use `SUPABASE_KEY` (service role) for backend operations

### Migration Issues

```
IntegrityError: duplicate key value violates unique constraint
```

- SMILES values must be unique - pre-deduplicate if migrating
- Run migration in transactions (automatic rollback on error)

### Performance Issues

```
Slow queries taking >5 seconds
```

1. Check indexes exist: `\di` in psql
2. Use `EXPLAIN ANALYZE` to check query plan
3. Add missing indexes with SQL:

   ```sql
   CREATE INDEX idx_custom ON table_name(column) WHERE condition;
   ```

## Future Enhancements

1. **Partitioning**: Partition calculations by year for 1M+ row datasets
2. **Full-Text Search**: Add SMILES/formula search with tsearch
3. **Materialized Views**: Cache statistics for faster dashboards
4. **Time-Series**: Store historical energies for convergence tracking
5. **Vector Search**: pgvector for similarity searches on molecular properties
6. **ML Pipeline**: Direct export to ML training frameworks

## References

- [Supabase Documentation](https://supabase.com/docs)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Pydantic](https://docs.pydantic.dev/)
