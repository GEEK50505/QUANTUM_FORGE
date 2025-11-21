# Quantum Forge - Comprehensive Data Management Analysis

## Executive Summary

This document provides a deep analysis of all data that needs to be managed in Quantum Forge across the entire stack (backend, frontend, xTB, user sessions).

---

## 1. DATA DOMAINS IDENTIFIED

### 1.1 Quantum Chemistry Computations (xTB)

**Current Status**: Partially captured (energy, gap, etc.)  
**Gaps**: Timing metrics, convergence details, error tracking, retry information

**Data Points**:

- **Pre-execution**: Input molecule, XYZ file hash, parameters, optimization level
- **During execution**: Process ID, memory usage, CPU time, wall-clock time, intermediate steps
- **Post-execution**: Energy values (total, orbital), convergence status, forces, charges, dipole
- **Atomic data**: Per-atom properties (charges, positions, forces, orbital energies)
- **Failures**: Error message, error type (timeout, convergence, invalid input), stderr output

**xTB Metrics**:

- Execution time (seconds, breakdown: optimization vs frequency analysis)
- Memory peak (MB)
- Convergence iterations
- SCF cycles
- xTB version + method (GFN2-xTB, GFN-FF, etc.)
- Solvation model if used (GBSA, ALPB, implicit solvent)

### 1.2 Frontend Session State

**Current Status**: Ephemeral (lost on page refresh)  
**Gaps**: Complete persistence of UI state

**Data Points**:

- **User Context**: User ID/email, authentication token, API key
- **UI State**: Current view/page, active molecule, selected calculation, filters
- **Editor State**: Molecule editor content, XYZ text, editing mode
- **Sidebar State**: Expanded/collapsed sections, active tab
- **Theme**: Dark/light mode preference, font size, layout preferences
- **Workspace**: Recently viewed molecules, favorite calculations, pinned batches
- **Form State**: Incomplete job submissions, temporary parameters, drafts
- **Notifications**: Dismissed alerts, notification preferences
- **History**: Search history, recent calculations, view history

### 1.3 Batch Processing Metadata

**Current Status**: Basic (name, status, counts)  
**Gaps**: Timing, success rates, failure analysis, retry tracking

**Data Points**:

- Batch start/end times, total duration
- Per-molecule execution time (min/max/avg)
- Success rate (%), failure rate (%), retry count
- Error breakdown (convergence failures, timeouts, input errors)
- Resource usage (total CPU time, memory footprint)

### 1.4 Error & Failure Tracking

**Current Status**: Local log files only  
**Gaps**: Searchable database, error categorization, retry logic

**Data Points**:

- Error type (validation, timeout, convergence, system)
- Error message and stack trace
- Timestamp and context (which job, molecule, user)
- Retry attempts (count, delays, backoff strategy)
- Resolution (manual fix, auto-retry, user action)
- Severity (info, warning, error, critical)

### 1.5 Performance Metrics & Analytics

**Current Status**: None  
**Gaps**: Complete analytics infrastructure

**Data Points**:

- **API Metrics**: Request count, response time, error rate, throughput
- **Calculation Metrics**: Average time by molecule size, method, optimization level
- **System Metrics**: CPU usage, memory usage, disk I/O, queue depth
- **User Metrics**: Active users, job submission rate, molecule library size
- **ML Metrics**: Dataset statistics, outliers, distribution by property

### 1.6 User Preferences & Settings

**Current Status**: Hardcoded/theme only  
**Gaps**: Comprehensive user configuration

**Data Points**:

- **Display Preferences**: Theme, language, units (Hartree vs eV), precision
- **Calculation Defaults**: Default optimization level, method, solvation
- **Notifications**: Email alerts, Slack webhooks, failure notifications
- **API Keys**: User's API keys, rate limits, usage quota
- **Bookmarks**: Favorite molecules, saved searches, pinned batches

### 1.7 Multi-User & Security

**Current Status**: User isolation via RLS  
**Gaps**: Audit trail, permission system, organization support

**Data Points**:

- **Authentication**: User credentials (hashed), 2FA, login history
- **Permissions**: Role (admin, researcher, viewer), data access level
- **Audit Trail**: Who accessed what data, when, what changes made
- **Organizations**: Team/project grouping, shared workspaces
- **API Quotas**: Rate limits, storage quotas, concurrent job limits

### 1.8 System State & Health

**Current Status**: Implicit in job status  
**Gaps**: Explicit health monitoring, capacity planning

**Data Points**:

- **Queue Status**: Jobs pending, running, completed, failed
- **xTB Availability**: Is xTB process running, availability, version
- **API Health**: Response times, error rates, database connection status
- **Database Health**: Connection pool usage, query performance, storage
- **Resource Utilization**: CPU %, memory %, disk space

---

## 2. PROPOSED DATABASE SCHEMA EXTENSIONS

### 2.1 New Tables Required

#### `user_sessions` - Frontend Session Persistence

```
id (UUID primary key)
user_id (UUID)
session_token (STRING unique)
current_view (STRING) - "molecule_editor", "results_viewer", "batch_manager"
active_molecule_id (INTEGER) - which molecule currently displayed
active_calculation_id (INTEGER) - which calculation currently displayed
editor_content (JSONB) - XYZ text, molecule name, parameters being edited
sidebar_state (JSONB) - open/collapsed sections, active tabs
theme_preference (STRING) - "dark", "light"
ui_preferences (JSONB) - font size, layout, units, precision
last_activity (TIMESTAMP) - last activity timestamp
created_at (TIMESTAMP)
expires_at (TIMESTAMP) - session expiration
```

#### `calculation_execution_metrics` - Detailed Timing & Performance

```
id (SERIAL primary key)
calculation_id (INTEGER references calculations.id)
xTB_version (STRING) - e.g., "6.7.1"
method (STRING) - "GFN2-xTB", "GFN-FF", etc.
solvation_model (STRING) - "GBSA", "ALPB", null for vacuum
optimization_level (STRING) - "crude", "normal", "tight"
wall_time_seconds (DOUBLE) - actual wall clock time
cpu_time_seconds (DOUBLE) - CPU time used
scf_cycles (INTEGER) - number of SCF iterations
optimization_cycles (INTEGER) - optimization steps
convergence_iterations (INTEGER) - total iterations to converge
memory_peak_mb (DOUBLE) - peak memory used
is_converged (BOOLEAN)
convergence_criterion_met (DOUBLE) - actual gradient norm
stdout_log (TEXT) - full stdout from xTB
stderr_log (TEXT) - full stderr from xTB
created_at (TIMESTAMP)
```

#### `calculation_errors` - Error Tracking & Retry Management

```
id (SERIAL primary key)
calculation_id (INTEGER references calculations.id)
error_type (VARCHAR 50) - "validation", "timeout", "convergence", "system", "unknown"
error_severity (VARCHAR 20) - "info", "warning", "error", "critical"
error_message (TEXT) - full error message
error_code (VARCHAR 50) - structured code
stack_trace (TEXT) - if applicable
retry_count (INTEGER default 0)
retry_attempts (JSONB) - history of retry attempts with timestamps
user_action_required (BOOLEAN) - does user need to fix?
resolution_notes (TEXT) - how it was resolved
created_at (TIMESTAMP)
resolved_at (TIMESTAMP)
```

#### `performance_metrics` - System-Wide Analytics

```
id (BIGSERIAL primary key)
metric_type (VARCHAR 50) - "api_request", "calculation_completed", "queue_length"
metric_name (VARCHAR 100) - detailed metric name
value (DOUBLE) - metric value
unit (VARCHAR 20) - "ms", "MB", "count", "%"
tags (JSONB) - grouping: {"endpoint": "/api/calculate", "method": "GFN2-xTB"}
timestamp (TIMESTAMP) - when metric was collected
```

#### `user_preferences` - User Configuration

```
user_id (UUID primary key)
display_units (VARCHAR 20) - "hartree", "ev"
display_precision (INTEGER) - decimal places
default_optimization_level (VARCHAR 20) - "normal"
default_solvation (VARCHAR 50) - null or "GBSA"/"ALPB"
theme (VARCHAR 20) - "light", "dark", "auto"
language (VARCHAR 10) - "en", "es", etc.
enable_email_notifications (BOOLEAN)
enable_slack_notifications (BOOLEAN)
slack_webhook_url (TEXT encrypted) - encrypted
notification_on_completion (BOOLEAN)
notification_on_error (BOOLEAN)
updated_at (TIMESTAMP)
```

#### `api_usage_logs` - API Request Tracking

```
id (BIGSERIAL primary key)
user_id (UUID)
endpoint (VARCHAR 255) - "/api/molecules", etc.
method (VARCHAR 10) - "GET", "POST", etc.
status_code (INTEGER) - HTTP status
response_time_ms (INTEGER) - latency
request_size_bytes (INTEGER)
response_size_bytes (INTEGER)
error_message (TEXT) - if failed
query_parameters (JSONB) - sanitized params
created_at (TIMESTAMP)
```

#### `molecule_properties_computed` - Pre-computed ML Features

```
id (SERIAL primary key)
molecule_id (INTEGER references molecules.id)
molecular_weight (DOUBLE)
logp (DOUBLE) - lipophilicity
hydrogen_bond_donors (INTEGER)
hydrogen_bond_acceptors (INTEGER)
rotatable_bonds (INTEGER)
topological_polar_surface_area (DOUBLE)
molar_refractivity (DOUBLE)
computed_at (TIMESTAMP)
```

#### `batch_job_performance` - Batch Statistics

```
batch_id (INTEGER primary key references batch_jobs.id)
execution_start_time (TIMESTAMP)
execution_end_time (TIMESTAMP)
total_execution_time_seconds (DOUBLE)
average_job_time_seconds (DOUBLE)
min_job_time_seconds (DOUBLE)
max_job_time_seconds (DOUBLE)
failed_jobs (INTEGER)
successful_jobs (INTEGER)
timeout_jobs (INTEGER)
convergence_failure_jobs (INTEGER)
average_memory_mb (DOUBLE)
total_cpu_time_hours (DOUBLE)
parallelization_efficiency (DOUBLE)
error_breakdown (JSONB) - {"convergence": 2, "timeout": 1}
```

#### `user_audit_log` - Security & Compliance

```
id (BIGSERIAL primary key)
user_id (UUID)
action (VARCHAR 100) - "login", "data_export", "molecule_delete"
entity_type (VARCHAR 50) - "molecules", "calculations", "batch_jobs"
entity_id (INTEGER)
changes (JSONB) - what changed {"energy": {"old": -10.5, "new": -10.6}}
ip_address (VARCHAR 45)
user_agent (TEXT)
status (VARCHAR 20) - "success", "denied"
reason (TEXT) - why denied
created_at (TIMESTAMP)
```

---

## 3. INTEGRATION POINTS

### 3.1 Backend (xTB Runner) → Supabase

**Current**: Saves to `/workspace/jobs/{job_id}/metadata.json`  
**New**: Also logs to Supabase:

```python
# After xTB execution completes
calculate_execution_metrics(
    calculation_id=calc_id,
    wall_time=elapsed_time,
    cpu_time=result.cpu_time,
    scf_cycles=parsed['scf_cycles'],
    is_converged=parsed['converged'],
    memory_peak=parsed['memory'],
)

log_error_if_failed(
    calculation_id=calc_id,
    error_type="convergence",
    error_message=result.stderr,
    retry_count=attempt,
)

record_performance_metric(
    metric_type="calculation_completed",
    metric_name="xTB_GFN2_normal",
    value=elapsed_time,
    unit="ms",
)
```

### 3.2 Frontend (React) → Supabase

**Current**: All state in React memory  
**New**: Auto-save to `user_sessions` table:

```typescript
// After every state change
useEffect(() => {
  const timer = debounce(async () => {
    await supabaseClient.update("user_sessions", {
      editor_content: editorState,
      active_molecule_id: currentMolecule?.id,
      sidebar_state: sidebarState,
      last_activity: new Date(),
    });
  }, 2000); // debounce 2 seconds
  
  return () => timer.clear();
}, [editorState, currentMolecule, sidebarState]);

// On page load/mount
useEffect(() => {
  const session = await supabaseClient.get("user_sessions", {
    filters: { user_id: currentUser.id },
    limit: 1,
  });
  if (session[0]) {
    restoreEditorState(session[0].editor_content);
    // ... restore other state
  }
}, []);
```

### 3.3 API → Supabase

**Current**: Job metadata in filesystem  
**New**: All metadata in database:

```python
@router.get("/api/calculations/{calc_id}/metrics")
async def get_calculation_metrics(calc_id: int):
    """Return execution metrics, errors, performance data"""
    client = get_supabase_client()
    
    calc = client.get("calculations", filters={"id": calc_id})[0]
    metrics = client.get("calculation_execution_metrics", 
                        filters={"calculation_id": calc_id})[0]
    errors = client.get("calculation_errors", 
                       filters={"calculation_id": calc_id})
    
    return {
        "calculation": calc,
        "metrics": metrics,
        "errors": errors,
    }
```

---

## 4. SPECIFIC USE CASES

### 4.1 Use Case: User Closes Browser During Molecule Editing

**Current**: All work lost  
**New with Supabase**:

1. Editor content auto-saved to `user_sessions.editor_content` every 2 seconds
2. On return, frontend fetches `user_sessions` and restores exact state
3. Result: Seamless continuity, no data loss

### 4.2 Use Case: Calculation Timeout

**Current**: Job marked failed, unclear why  
**New with Supabase**:

1. xTB runner catches timeout exception
2. Creates row in `calculation_errors` with type="timeout", retry_count=1
3. API can query errors for a molecule: "This calculation timed out 3 times"
4. Retry logic checks error history: `error count > 3 → skip retry`
5. Dashboard shows timeout distribution for molecule size analysis

### 4.3 Use Case: Performance Regression

**Current**: No visibility into if system is slowing down  
**New with Supabase**:

1. Every calculation logs metrics: `execution_time_seconds`, `scf_cycles`
2. Dashboard queries: `SELECT AVG(wall_time_seconds) FROM calculation_execution_metrics WHERE created_at > NOW() - INTERVAL 1 day`
3. Alert if average > threshold
4. Analyze: is it molecule size? xTB version? System load?

### 4.4 Use Case: ML Dataset Preparation

**Current**: Data in calculated results only  
**New with Supabase**:

1. Pre-compute molecular properties in `molecule_properties_computed`
2. Query: Get all molecules with MW < 300 and logP < 5
3. Export: Get top 1000 calculations sorted by gap value
4. Features available: atomic charges, forces, positions (from `atomic_properties`)

### 4.5 Use Case: Audit & Compliance

**Current**: No record of who accessed what  
**New with Supabase**:

1. Every API access logged in `user_audit_log`
2. Query: "What data did user X export last month?"
3. Answer: `SELECT * FROM user_audit_log WHERE user_id='X' AND action='data_export'`

---

## 5. IMPLEMENTATION PRIORITY

### Phase 1: Critical (Week 1)

- [ ] `calculation_execution_metrics` - needed for performance visibility
- [ ] `calculation_errors` - needed for debugging & retry logic
- [ ] `user_sessions` - needed for frontend state persistence
- [ ] xTB runner integration - log metrics after each calculation

### Phase 2: Important (Week 2)

- [ ] `user_preferences` - improves UX  
- [ ] `api_usage_logs` - required for monitoring
- [ ] Frontend session restoration - prevents data loss
- [ ] Performance dashboard

### Phase 3: Enhanced (Week 3)

- [ ] `molecule_properties_computed` - ML feature extraction
- [ ] `batch_job_performance` - batch analytics
- [ ] `user_audit_log` - compliance & security

---

## 6. TECHNICAL DECISIONS

### 6.1 Session Storage Strategy

- **Option A**: Store in `user_sessions` table (chosen) ✅
  - Pros: Persists across device changes, searchable, can share sessions
  - Cons: Extra DB roundtrip
  - **Implementation**: Auto-save every 2 seconds, restore on load

### 6.2 Metrics Collection Strategy  

- **Option A**: Poll from xTB process (resource-heavy)
- **Option B**: Parse xTB output after completion (chosen) ✅
  - Pros: No overhead, accurate, simple
  - Cons: Only post-execution metrics
  - **Implementation**: Extract from stdout/stderr logs

### 6.3 Error Handling Strategy

- **Option A**: Manual retry button
- **Option B**: Automatic retry with exponential backoff (chosen) ✅
  - Pros: Better UX, faster recovery
  - Cons: More complex retry logic
  - **Implementation**: Check error history, implement backoff

---

## 7. SECURITY & PRIVACY CONSIDERATIONS

### 7.1 Row-Level Security (RLS)

- All new tables must have `user_id` column
- RLS policies: Users can only see their own data
- Admin users can see all data for compliance

### 7.2 Sensitive Data Encryption

- `slack_webhook_url` → encrypt before storing
- API keys → never log, use masked values
- user_agent → sanitize personally identifying info

### 7.3 Data Retention

- Session data: Keep 7 days
- Performance metrics: Keep 90 days  
- Audit logs: Keep 1 year (compliance)
- Calculation data: Keep indefinitely (science)

---

## 8. MIGRATION STRATEGY

### 8.1 Backward Compatibility

- Keep existing `/workspace/jobs` directory structure
- Database is **supplement**, not replacement
- If database fails, calculations still work

### 8.2 Gradual Rollout

1. Deploy schema changes
2. Start logging new data (won't use existing data)
3. Test in devcontainer thoroughly
4. Gradually migrate historical data
5. Monitor for anomalies

### 8.3 Rollback Plan

- All new tables are additive (no schema changes to existing tables)
- If issues occur: disable new logging, continue using old system
- No data loss possible

---

## 9. IMPLEMENTATION CHECKLIST

- [ ] Design approved
- [ ] Schema migration SQL written & tested
- [ ] xTB runner modified to log metrics
- [ ] REST client extended with new operations
- [ ] Frontend SessionProvider context created
- [ ] API endpoints for metrics/errors created
- [ ] Performance dashboard component written
- [ ] End-to-end test in devcontainer
- [ ] Documentation written
- [ ] Deployment to production

---

*Analysis completed: 2025-11-14*  
*Ready for implementation phase*
