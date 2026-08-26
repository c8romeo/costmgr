# Audit Log Investigation Runbook

> **Target audience:** Backend on-call engineer + Compliance auditor
> investigating missing or unexpected audit log entries in
> `audit_logs` table.

## §1. Symptom triage

### Symptom 1 — Missing audit log entries

**Possible causes:**

1. **Pre-Phase 11~20 audit-fixes** (pre-`379ca8e`) — the 24 broken
   sites silently-passed. This is the most common cause for FinOps
   territory entries missing before 2026-08-27.
2. **`emit_audit_typed` import failure** — the lazy import in
   aggregator mode raises `ImportError` → `emit_audit_typed is None`
   → silent-pass.
3. **`db_session is None`** — CLI / dry-run mode → no audit INSERT.
4. **`dry_run=True`** — POST /dry-run endpoint or CLI flag → no audit
   INSERT (intentional for preview-only actions).
5. **RLS policy filter** — `tenant_id` mismatch → row not visible to
   the query caller.
6. **Audit log retention** — entries older than retention period
   (Phase 6 wire) are purged.

### Symptom 2 — Unexpected audit log entries

**Possible causes:**

1. **Duplicate INSERT** — race condition between concurrent requests.
   Verify by checking `trace_id` (should be unique per request).
2. **Wrong tenant_id** — RLS bypass or misconfigured `tenant_id`
   propagation.
3. **Wrong action_class / action** — drift between call site and
   registry. Run drift detector:
   `pytest tests/api/core/test_audit_action_consistency.py -v`.

### Symptom 3 — Audit log INSERT failures (Sentry alerts)

**Possible causes:**

1. **Database connection issue** — Supabase PITR failover, network
   partition, connection pool exhaustion.
2. **RLS policy violation** — `tenant_id` mismatch → INSERT rejected.
3. **Schema mismatch** — column added/removed without migration.
4. **Lock contention** — `audit_logs` table lock held by another
   transaction.

## §2. Investigation steps

### Step 1 — Verify audit log table exists + schema

```bash
psql $SUPABASE_URL -c "\d audit_logs"
```

Expected columns:
- `id` (UUID, PK)
- `tenant_id` (UUID, NOT NULL)
- `action_class` (VARCHAR, NOT NULL)
- `action` (VARCHAR, NOT NULL)
- `actor_id` (UUID, NULL allowed)
- `target_id` (UUID, NULL allowed)
- `reason` (TEXT, NOT NULL)
- `payload` (JSONB, NOT NULL)
- `created_at` (TIMESTAMPTZ, NOT NULL)

### Step 2 — Verify RLS policy

```bash
psql $SUPABASE_URL -c "
  SELECT schemaname, tablename, policyname, permissive, roles, qual
  FROM pg_policies
  WHERE tablename = 'audit_logs';
"
```

Expected: at least 1 RLS policy enforcing `tenant_id = current_setting('app.tenant_id')::UUID`.

### Step 3 — Query for missing entries

Replace `<expected-action>` with the action string (e.g.
`executive_dashboard_viewed`) and `<tenant-id>` with the tenant UUID:

```sql
-- Expected: at least 1 row per request
SELECT count(*), date_trunc('hour', created_at) AS hour
FROM audit_logs
WHERE tenant_id = '<tenant-id>'
  AND action = '<expected-action>'
  AND created_at > NOW() - INTERVAL '1 hour'
GROUP BY 2
ORDER BY 2 DESC;
```

If `count = 0`:

1. Check if `trace_id` is in `payload` column (should match the
   request that triggered the action):
   ```sql
   SELECT * FROM audit_logs
   WHERE payload->>'trace_id' = '<trace-id>';
   ```
2. If no rows → the audit INSERT didn't fire. Check the application
   logs for the trace_id:
   ```bash
   grep "<trace-id>" /var/log/costmgr/api.log
   ```
3. If application logs show the action was attempted → ImportError
   or db_session None. Apply hot-fix per
   `docs/runbooks/finops-aggregator-canonical-signature-recovery.md`.

### Step 4 — Query for unexpected entries

```sql
SELECT * FROM audit_logs
WHERE tenant_id = '<tenant-id>'
  AND created_at > NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC;
```

Inspect:

- `actor_id` — should match the user that triggered the action.
- `reason` — should be ko-KR (NFR18).
- `payload->>'trace_id'` — should match a request trace.
- `action_class` + `action` — should be a registered combination
  per `apps/api/core/audit_action.py`.

### Step 5 — Run drift detector

```bash
pytest tests/api/core/test_audit_action_consistency.py -v
```

Expected: all 3-way consistency tests PASS (Literal � registry ↔ TS
mirror parity).

### Step 6 — Check Sentry for audit failures

In Sentry, filter by tag `audit_logs_insert_failed`. Each event
corresponds to a failed `emit_audit_typed` call. Inspect the
exception type and trace.

## §3. Common remediation

### Remediation 1 — Audit INSERT silently-passed (pre-`379ca8e`)

If audit entries are missing for actions BEFORE 2026-08-27
(pre-Phase 11~20 audit-fixes sprint):

**This is expected behavior.** The 24 broken sites had broken
signatures + silent-pass imports. The Phase 11~20 audit-fixes
sprint (`379ca8e`) restored correct behavior — but historical
entries cannot be retroactively INSERTed.

For compliance audits, document the gap in your audit log report:
"Phase 16~21 FinOps territory actions between 2026-08-25 and
2026-08-27 are missing from audit_logs due to broken signature. Phase
11~20 audit-fixes sprint (379ca8e, 2026-08-27) restored correctness.
Future compliance audits will have full coverage."

### Remediation 2 — ImportError in lazy import

If `emit_audit_typed is None` (lazy import failed), the call site
should log to Sentry. Verify:

```python
# apps/api/core/audit_action.py
try:
    from apps.api.core.audit_logs_db import insert_audit_log
except ImportError:
    insert_audit_log = None  # type: ignore[assignment]
```

If the import path is wrong (e.g. `audit_logs_db` doesn't exist),
fix the import path. This is a code bug — open a P1 ticket.

### Remediation 3 — tenant_id mismatch

If `audit_logs` rows exist but are not visible to the query caller:

```sql
SELECT current_setting('app.tenant_id') AS session_tenant_id,
       tenant_id AS row_tenant_id
FROM audit_logs
WHERE id = '<row-id>';
```

If `session_tenant_id != row_tenant_id` → RLS is working correctly.
The query caller doesn't have permission to see this row.

If RLS is misconfigured → verify the RLS policy in step 2.

## §4. Escalation

If the issue persists after remediation:

1. **P1 — Missing critical audit entries** (e.g. compliance-related
   financial events) → escalate to security@costmgr.com within 1 hour.
2. **P2 — Unexpected audit entries** → file a ticket, no immediate
   escalation needed.
3. **P3 — Performance regression** → file a ticket, no immediate
   escalation needed.

## §5. Cross-references

- **Canonical signature spec**: `docs/audit-fixes-canonical-signature.md`
- **24 broken sites recovery log**: `docs/audit-fixes-broken-sites-recovery.md`
- **Registry reference**: `docs/audit-fixes-registry-reference.md`
- **Migration guide**: `docs/audit-fixes-migration-guide.md`
- **AD-49**: `docs/architecture-decisions/AD-49-phase-11-20-audit-fixes.md`
- **Routers reference**: `docs/api/routers/finops-executive-dashboard-routes.md`
- **Deployment guide**: `docs/deployment/phase-11-20-audit-fixes-deployment.md`
- **Runbook: signature recovery**: `docs/runbooks/finops-aggregator-canonical-signature-recovery.md`
- **Audit action drift detector**: `tests/api/core/test_audit_action_consistency.py`
- **Phase 11~20 audit-fixes signature test**: `tests/api/core/test_audit_fixes_phase_11_20_signature.py`
- **Phase 11~20 audit-fixes backfill test**: `tests/api/core/test_audit_fixes_phase_11_20_backfill.py`
