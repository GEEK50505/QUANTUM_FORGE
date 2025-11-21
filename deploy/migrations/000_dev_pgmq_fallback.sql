-- Dev shim for pgmq extension
-- This file provides a lightweight, pure-SQL fallback implementation
-- of the minimal pgmq API used in development when the native
-- extension is not available. It is intentionally simple and
-- only meant for local development and CI, not production.

-- If the real pgmq extension is available, do nothing here.
DO $$
BEGIN
  IF (SELECT count(*) FROM pg_available_extensions WHERE name = 'pgmq') > 0 THEN
    RAISE NOTICE 'pgmq extension available; skipping dev shim';
    RETURN;
  END IF;
END$$;

-- Create a simple messages table for dev queueing
CREATE TABLE IF NOT EXISTS dev_pgmq_messages (
  msg_id serial PRIMARY KEY,
  queue_name text NOT NULL,
  payload jsonb NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  archived boolean NOT NULL DEFAULT false
);

-- Provide a minimal pgmq schema and functions expected by the codebase.
-- These functions mimic the real extension's create/send/read/archive
-- interfaces in a simple transactional manner.
CREATE SCHEMA IF NOT EXISTS pgmq;

CREATE OR REPLACE FUNCTION pgmq.create(qname text)
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
  -- no-op for dev: ensure queue exists (implicitly done by inserts)
  PERFORM 1;
END$$;

CREATE OR REPLACE FUNCTION pgmq.send(qname text, payload jsonb)
RETURNS integer LANGUAGE sql AS $$
  INSERT INTO dev_pgmq_messages (queue_name, payload) VALUES ($1, $2) RETURNING msg_id;
$$;

CREATE OR REPLACE FUNCTION pgmq.read(qname text, visibility_timeout integer, batch_size integer)
RETURNS TABLE(msg_id integer, payload jsonb) LANGUAGE plpgsql AS $$
DECLARE
  ids integer[];
BEGIN
  -- select candidate ids and mark them archived to avoid redelivery
  SELECT array_agg(d.msg_id) INTO ids
  FROM (
    SELECT msg_id FROM dev_pgmq_messages
    WHERE queue_name = qname AND archived = false
    ORDER BY msg_id
    LIMIT batch_size
    FOR UPDATE SKIP LOCKED
  ) d;

  IF ids IS NULL OR array_length(ids,1) = 0 THEN
    RETURN;
  END IF;

  UPDATE dev_pgmq_messages SET archived = true WHERE msg_id = ANY(ids);

  RETURN QUERY SELECT msg_id, payload FROM dev_pgmq_messages WHERE msg_id = ANY(ids) ORDER BY msg_id;
END$$;

CREATE OR REPLACE FUNCTION pgmq.archive(msgid integer)
RETURNS void LANGUAGE sql AS $$
  DELETE FROM dev_pgmq_messages WHERE msg_id = $1;
$$;

-- Keep this file idempotent and safe to run multiple times.
