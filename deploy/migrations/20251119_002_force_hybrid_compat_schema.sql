-- Destructive migration: Force hybrid-compatible schema
-- Date: 2025-11-19
-- WARNING: This migration is destructive and will DROP existing tables/types if they exist.
-- Only run this on development or after taking backups in production.

-- Drop dependent objects first
DROP TABLE IF EXISTS agent_decisions CASCADE;
DROP TABLE IF EXISTS calculations CASCADE;
DROP TABLE IF EXISTS molecules CASCADE;

-- Drop enum types if they exist
DROP TYPE IF EXISTS calculation_method CASCADE;
DROP TYPE IF EXISTS job_status CASCADE;

-- Ensure extensions available
CREATE EXTENSION IF NOT EXISTS pgcrypto; -- for gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS vector;

-- Recreate enums with the desired future-proof values
CREATE TYPE calculation_method AS ENUM (
  'xtb_gfn2',
  'dft_b3lyp',
  'hybrid_qmmm',
  'vqe_uccsd',
  'qaoa_optimization'
);

CREATE TYPE job_status AS ENUM (
  'queued', 'running', 'completed', 'failed', 'converged_qpu', 'error_mitigation'
);

-- Create molecules table (destructive create)
CREATE TABLE molecules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  smiles TEXT NOT NULL,
  xyz_structure TEXT,
  embedding vector(1024),
  source_type TEXT CHECK (source_type IN ('human_upload', 'agent_generated', 'mutation')),
  parent_molecule_id UUID REFERENCES molecules(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- IVFFLAT index for pgvector (tune lists as needed)
-- Note: ivfflat requires the table to be populated and analyzed before it is effective.
CREATE INDEX idx_molecules_embedding ON molecules USING ivfflat (embedding) WITH (lists = 100);

-- Create master calculations table for hybrid compatibility
CREATE TABLE calculations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  molecule_id UUID REFERENCES molecules(id) NOT NULL,
  method calculation_method NOT NULL DEFAULT 'xtb_gfn2',
  status job_status NOT NULL DEFAULT 'queued',

  -- classical results
  energy_hartree NUMERIC,
  homo_lumo_gap_ev NUMERIC,
  dipole_moment_debye NUMERIC,

  -- quantum bridge
  active_space_config JSONB DEFAULT '{}'::jsonb,
  quantum_metadata JSONB DEFAULT '{}'::jsonb,

  raw_log TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  execution_time_ms INTEGER
);

CREATE INDEX idx_calc_gap ON calculations(homo_lumo_gap_ev);
CREATE INDEX idx_calc_method ON calculations(method);

-- Agent decisions ledger
CREATE TABLE agent_decisions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_version TEXT NOT NULL,
  input_molecule_id UUID REFERENCES molecules(id),
  action_taken TEXT,
  reasoning TEXT,
  resulting_calculation_id UUID REFERENCES calculations(id),
  reward_score FLOAT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Helpful comments
COMMENT ON TABLE calculations IS 'Master calculations table designed for hybrid compatibility (classical+quantum). Uses UUIDs.';
COMMENT ON COLUMN calculations.active_space_config IS 'JSONB storing active space (orbital indices, electrons, multiplicity) for QPU handoff';
COMMENT ON COLUMN calculations.quantum_metadata IS 'JSONB storing QPU backend, shots, ansatz, qubits_used, etc.';
COMMENT ON TABLE molecules IS 'Molecules table with vector embedding and provenance for agentic workflows';
COMMENT ON COLUMN molecules.embedding IS 'pgvector embedding (1024 dim) for similarity search';
COMMENT ON TABLE agent_decisions IS 'Ledger of agent decisions and reasoning used for RL/agentic swarm training';
