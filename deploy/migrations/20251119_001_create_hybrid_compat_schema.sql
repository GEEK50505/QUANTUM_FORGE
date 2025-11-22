-- Migration: Create hybrid-compat schema additions
-- Date: 2025-11-19

-- 1) Create enumerated types for calculation methods and job status
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'calculation_method') THEN
        CREATE TYPE calculation_method AS ENUM (
            'xtb_gfn2',
            'dft_b3lyp',
            'hybrid_qmmm',
            'vqe_uccsd',
            'qaoa_optimization'
        );
    END IF;
END$$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'job_status') THEN
        CREATE TYPE job_status AS ENUM (
            'queued', 'running', 'completed', 'failed', 'converged_qpu', 'error_mitigation'
        );
    END IF;
END$$;

-- 2) Enable pgvector extension for embeddings
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_available_extensions WHERE name = 'vector' ) THEN
        CREATE EXTENSION IF NOT EXISTS vector;
    END IF;
END
$$;

-- 3) Create or alter the calculations table to a hybrid-compatible master table
-- Note: This migration will CREATE the table if it does not exist. If your
-- existing schema uses a different primary key type (serial/int), review and
-- adapt the migration before applying in production. We use UUIDs to future-proof.
CREATE TABLE IF NOT EXISTS calculations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    molecule_id UUID NOT NULL,

    -- Execution Metadata
    method calculation_method NOT NULL DEFAULT 'xtb_gfn2',
    status job_status NOT NULL DEFAULT 'queued',

    -- CLASSICAL RESULTS (Structured, Queryable)
    energy_hartree NUMERIC,
    homo_lumo_gap_ev NUMERIC,
    dipole_moment_debye NUMERIC,

    -- THE QUANTUM BRIDGE (JSONB) - orbital indices, electron counts, multiplicity
    active_space_config JSONB DEFAULT '{}'::jsonb,

    -- QPU SPECIFICS (Populate later)
    quantum_metadata JSONB DEFAULT '{}'::jsonb,

    -- RAW OUTPUT (For ML training / archival)
    raw_log TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    execution_time_ms INTEGER
);

-- Indexes for rapid screening
CREATE INDEX IF NOT EXISTS idx_calc_gap ON calculations(homo_lumo_gap_ev);
CREATE INDEX IF NOT EXISTS idx_calc_method ON calculations(method);

-- 4) Alter molecules table to add vector embedding and swarm provenance fields
ALTER TABLE IF EXISTS molecules
    ADD COLUMN IF NOT EXISTS embedding vector(1024),
    ADD COLUMN IF NOT EXISTS source_type TEXT CHECK (source_type IN ('human_upload', 'agent_generated', 'mutation')),
    ADD COLUMN IF NOT EXISTS parent_molecule_id UUID REFERENCES molecules(id),
    ADD COLUMN IF NOT EXISTS xyz_structure TEXT;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'molecules') THEN
        EXECUTE 'CREATE INDEX IF NOT EXISTS idx_molecules_embedding ON molecules USING ivfflat (embedding) WITH (lists = 100)';
    END IF;
END
$$;

-- 5) Create agent_decisions ledger table
CREATE TABLE IF NOT EXISTS agent_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_version TEXT NOT NULL,
    input_molecule_id UUID,
    action_taken TEXT,
    reasoning TEXT,
    resulting_calculation_id UUID,
    reward_score FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add comments for clarity
COMMENT ON TABLE calculations IS 'Master calculations table designed for hybrid compatibility (classical+quantum)';
COMMENT ON COLUMN calculations.active_space_config IS 'JSONB storing active space (orbital indices, electrons, multiplicity) for QPU handoff';
COMMENT ON COLUMN calculations.quantum_metadata IS 'JSONB storing QPU backend, shots, ansatz, qubits_used, etc.';

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'molecules') THEN
        EXECUTE 'COMMENT ON TABLE molecules IS ''Molecules table augmented with vector embedding and provenance for agentic workflows''';
        EXECUTE 'COMMENT ON COLUMN molecules.embedding IS ''pgvector embedding (1024 dim) for similarity search''';
    END IF;
END
$$;

COMMENT ON TABLE agent_decisions IS 'Ledger of agent decisions and reasoning used for RL/agentic swarm training';
