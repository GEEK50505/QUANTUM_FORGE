# Worker

This is a worker for QUANTUM_FORGE with pgmq + SKIP LOCKED fallback.

Usage

```
python services/worker/worker.py --dry-run
```

Environment variables (for real runs)

- `DATABASE_URL` : Postgres DSN (use Supabase service role DB URL for worker writes)
- `SUPABASE_URL` : Supabase project URL (optional, for log uploads)
- `SUPABASE_SERVICE_ROLE_KEY` : Supabase service role key (optional, for log uploads)
- `WORKER_QUEUE` : pgmq queue name (default `xtb_job_queue`)
- `WORKER_POLL_INTERVAL` : seconds between polls when no jobs (default 2)

Notes

- The worker attempts to use `pgmq.receive()` when `pgmq` extension is available.
- Otherwise it falls back to SELECT ... FOR UPDATE SKIP LOCKED to claim queued jobs.
- Use a Service Role DB connection for writing job status/results to bypass RLS.
