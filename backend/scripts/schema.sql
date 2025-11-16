-- Quantum Forge Database Schema
-- PostgreSQL schema for Supabase with all required tables, indexes, and RLS policies
-- Run this migration in Supabase SQL editor before deploying the application

-- ============================================================================
-- ENABLE REQUIRED EXTENSIONS
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- CREATE BASE TABLES
-- ============================================================================

-- MOLECULES TABLE: stores unique molecular structures
-- Used to de-duplicate molecules across multiple calculations
-- Can be queried by researchers for structure analysis and pattern discovery
CREATE TABLE molecules (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,  -- For future user isolation
    name VARCHAR(255) NOT NULL,  -- e.g., "water", "benzene"
    smiles TEXT UNIQUE NOT NULL,  -- SMILES notation - unique identifier
    formula VARCHAR(255) NOT NULL,  -- Chemical formula (e.g., "H2O")
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,  -- Extra fields: molecular_weight, logP, etc.
    
    -- Constraints
    CONSTRAINT smiles_not_empty CHECK (LENGTH(TRIM(smiles)) > 0),
    CONSTRAINT name_not_empty CHECK (LENGTH(TRIM(name)) > 0)
);

-- CALCULATIONS TABLE: stores individual xTB calculation results
-- This is the main table for ML training data
-- One molecule can have multiple calculations (different parameters, refinements)
CREATE TABLE calculations (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    molecule_id INTEGER NOT NULL REFERENCES molecules(id) ON DELETE CASCADE,
    
    -- Core xTB outputs
    energy DOUBLE PRECISION NOT NULL,  -- Total energy in Hartree
    homo DOUBLE PRECISION,  -- Highest occupied molecular orbital
    lumo DOUBLE PRECISION,  -- Lowest unoccupied molecular orbital
    gap DOUBLE PRECISION,  -- HOMO-LUMO gap
    dipole DOUBLE PRECISION,  -- Dipole moment in Debye
    total_charge DOUBLE PRECISION DEFAULT 0.0,  -- Total molecular charge
    
    -- Execution metadata
    execution_time_seconds DOUBLE PRECISION NOT NULL,  -- Runtime in seconds
    xtb_version VARCHAR(50),  -- Version of xTB used
    solvation VARCHAR(50),  -- Solvent model if used (e.g., "GBSA", "ALPB")
    method VARCHAR(50) DEFAULT 'GFN2-xTB',  -- Method used
    convergence_status VARCHAR(50) DEFAULT 'converged',  -- converged, not_converged, error
    
    -- File references (for debugging/recomputation)
    xyz_file_hash VARCHAR(64),  -- SHA256 hash of input XYZ
    output_json_path TEXT,  -- Path to original xtbout.json
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb  -- Extra fields: custom parameters, notes, etc.
);

-- ATOMIC PROPERTIES TABLE: per-atom data for ML feature engineering
-- Stores atomic charges, positions, forces for each atom in each calculation
-- Critical for training atom-level ML models
CREATE TABLE atomic_properties (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    calculation_id INTEGER NOT NULL REFERENCES calculations(id) ON DELETE CASCADE,
    
    -- Atom identification
    atom_index INTEGER NOT NULL,  -- 0-based index in the molecule
    element VARCHAR(3) NOT NULL,  -- Element symbol (H, C, N, O, etc.)
    atomic_number INTEGER NOT NULL,  -- Atomic number
    
    -- Computed properties
    partial_charge DOUBLE PRECISION,  -- Mulliken or other charge model
    position_x DOUBLE PRECISION NOT NULL,  -- Angstroms
    position_y DOUBLE PRECISION NOT NULL,
    position_z DOUBLE PRECISION NOT NULL,
    force_x DOUBLE PRECISION,  -- Force in atomic units
    force_y DOUBLE PRECISION,
    force_z DOUBLE PRECISION,
    
    -- Energy contribution
    orbital_energy DOUBLE PRECISION,  -- Orbital energy if available
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- BATCH JOBS TABLE: groups calculations for bulk processing
-- Used for organizing multiple molecules (drug discovery, materials screening)
CREATE TABLE batch_jobs (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Batch metadata
    batch_name VARCHAR(255) NOT NULL,  -- User-friendly name
    description TEXT,  -- Why this batch was created
    status VARCHAR(50) DEFAULT 'pending',  -- pending, in_progress, completed, failed
    
    -- Tracking
    total_molecules INTEGER DEFAULT 0,
    successful_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    
    -- Parameters applied to all molecules in batch
    parameters JSONB DEFAULT '{}'::jsonb,  -- Shared xTB parameters
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    metadata JSONB DEFAULT '{}'::jsonb
);

-- BATCH ITEMS TABLE: link molecules to batches
-- Many-to-many relationship: batch can have many molecules, molecule can be in many batches
CREATE TABLE batch_items (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    batch_id INTEGER NOT NULL REFERENCES batch_jobs(id) ON DELETE CASCADE,
    molecule_id INTEGER NOT NULL REFERENCES molecules(id) ON DELETE CASCADE,
    
    -- Item status within batch
    status VARCHAR(50) DEFAULT 'pending',  -- pending, processing, completed, failed, skipped
    calculation_id INTEGER REFERENCES calculations(id) ON DELETE SET NULL,
    
    -- Error tracking
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Ensure no duplicates in a batch
    CONSTRAINT unique_batch_molecule UNIQUE (batch_id, molecule_id)
);

-- EVENT LOGS TABLE: comprehensive audit trail
-- Every action (create, update, delete, error) is logged here
-- Essential for debugging, monitoring, and compliance
CREATE TABLE event_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Event classification
    event_type VARCHAR(50) NOT NULL,  -- calculation_started, calculation_completed, batch_failed, etc.
    entity_type VARCHAR(50) NOT NULL,  -- molecules, calculations, batches, etc.
    entity_id INTEGER,  -- ID of the entity being acted upon
    
    -- Error tracking
    status VARCHAR(50) DEFAULT 'success',  -- success, warning, error
    error_message TEXT,
    error_code VARCHAR(50),
    
    -- Context for debugging
    context JSONB DEFAULT '{}'::jsonb,  -- xTB version, method, parameters, etc.
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexing hint
    service VARCHAR(50) DEFAULT 'api'  -- Which service generated the log
);

-- ============================================================================
-- CREATE INDEXES FOR PERFORMANCE
-- ============================================================================

-- Molecules indexes
CREATE INDEX idx_molecules_user_id ON molecules(user_id);
CREATE INDEX idx_molecules_smiles ON molecules(smiles);  -- Fast lookup by chemical structure
CREATE INDEX idx_molecules_created_at ON molecules(created_at DESC);

-- Calculations indexes (critical for ML data queries)
CREATE INDEX idx_calculations_user_id ON calculations(user_id);
CREATE INDEX idx_calculations_molecule_id ON calculations(molecule_id);
CREATE INDEX idx_calculations_created_at ON calculations(created_at DESC);
CREATE INDEX idx_calculations_energy ON calculations(energy);  -- For range queries
CREATE INDEX idx_calculations_gap ON calculations(gap);  -- HOMO-LUMO gap queries
CREATE INDEX idx_calculations_molecule_created ON calculations(molecule_id, created_at DESC);  -- Composite

-- Atomic properties indexes
CREATE INDEX idx_atomic_properties_user_id ON atomic_properties(user_id);
CREATE INDEX idx_atomic_properties_calculation_id ON atomic_properties(calculation_id);
CREATE INDEX idx_atomic_properties_element ON atomic_properties(element);  -- Group by element

-- Batch indexes
CREATE INDEX idx_batch_jobs_user_id ON batch_jobs(user_id);
CREATE INDEX idx_batch_jobs_status ON batch_jobs(status);
CREATE INDEX idx_batch_items_batch_id ON batch_items(batch_id);
CREATE INDEX idx_batch_items_molecule_id ON batch_items(molecule_id);
CREATE INDEX idx_batch_items_status ON batch_items(status);

-- Event logs indexes (fast filtering for audit trails)
CREATE INDEX idx_event_logs_user_id ON event_logs(user_id);
CREATE INDEX idx_event_logs_created_at ON event_logs(created_at DESC);
CREATE INDEX idx_event_logs_entity_type ON event_logs(entity_type);
CREATE INDEX idx_event_logs_event_type ON event_logs(event_type);
CREATE INDEX idx_event_logs_status ON event_logs(status);
CREATE INDEX idx_event_logs_composite ON event_logs(user_id, created_at DESC, event_type);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- Enable users to only see their own data
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE molecules ENABLE ROW LEVEL SECURITY;
ALTER TABLE calculations ENABLE ROW LEVEL SECURITY;
ALTER TABLE atomic_properties ENABLE ROW LEVEL SECURITY;
ALTER TABLE batch_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE batch_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE event_logs ENABLE ROW LEVEL SECURITY;

-- Molecules RLS
CREATE POLICY "Users can view their own molecules" ON molecules
    FOR SELECT USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "Users can insert their own molecules" ON molecules
    FOR INSERT WITH CHECK (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "Users can update their own molecules" ON molecules
    FOR UPDATE USING (auth.uid() = user_id OR user_id IS NULL);

-- Calculations RLS
CREATE POLICY "Users can view their own calculations" ON calculations
    FOR SELECT USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "Users can insert calculations" ON calculations
    FOR INSERT WITH CHECK (auth.uid() = user_id OR user_id IS NULL);

-- Atomic properties RLS
CREATE POLICY "Users can view their atomic data" ON atomic_properties
    FOR SELECT USING (auth.uid() = user_id OR user_id IS NULL);

-- Batch jobs RLS
CREATE POLICY "Users can view their batch jobs" ON batch_jobs
    FOR SELECT USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "Users can manage their batch jobs" ON batch_jobs
    FOR INSERT WITH CHECK (auth.uid() = user_id OR user_id IS NULL);

-- Batch items RLS
CREATE POLICY "Users can view their batch items" ON batch_items
    FOR SELECT USING (auth.uid() = user_id OR user_id IS NULL);

-- Event logs RLS
CREATE POLICY "Users can view their event logs" ON event_logs
    FOR SELECT USING (auth.uid() = user_id OR user_id IS NULL);

-- ============================================================================
-- GRANTS FOR SERVICE ROLE (backend API)
-- ============================================================================
-- Grant full access to authenticated role for API operations
GRANT ALL ON molecules TO authenticated;
GRANT ALL ON calculations TO authenticated;
GRANT ALL ON atomic_properties TO authenticated;
GRANT ALL ON batch_jobs TO authenticated;
GRANT ALL ON batch_items TO authenticated;
GRANT ALL ON event_logs TO authenticated;

-- Grant sequence access
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- ============================================================================
-- SEED DATA (OPTIONAL: for testing)
-- ============================================================================
-- Uncomment to add test data
-- INSERT INTO molecules (name, smiles, formula) VALUES ('water', 'O', 'H2O');
-- INSERT INTO molecules (name, smiles, formula) VALUES ('methane', 'C', 'CH4');
