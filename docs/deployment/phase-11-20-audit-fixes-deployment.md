# Phase 11~20 Audit-Fixes Deployment Guide

> **Phase 11~20 audit-fixes sprint (cj-style 154~156)** —
> Deployment guide for the canonical `emit_audit_typed` signature
> fix applied to 24 broken sites across 14 FinOps modules. No new
> modules added; this is a backward-compatible signature correction
> that improves audit log integrity.

## §1. Scope

This deployment guide covers:

1. **Phase 11~20 audit-fixes sprint `379ca8e`** (cj-style 154) — 24
   canonical signature sites added across 14 FinOps modules.
2. **Phase 11~20 audit-fixes backfill `4e1f0b3`** (cj-style 155) —
   semantic test backfill (52 NEW pytest tests PASS).
3. **Phase 11~20 audit-fixes docs backfill** (cj-style 156, this
   sprint) — 9 NEW docs + 1 MODIFIED capability-matrix.md.

This is a **Layer 1 source change** + **Layer 2 test change** +
**Layer 3 docs change** with **NO breaking API changes**. The
canonical signature is backward-compatible because aggregator +
dispatcher call sites previously had broken signatures (silent-pass);
router call sites previously had no audit call at all.

## §2. Pre-deployment checklist

- [ ] **Git status clean** — `git status --short` shows only the
       sprint files (no uncommitted changes from prior sprints).
- [ ] **Backend pytest passes** — `pytest tests/api/core/test_audit_fixes_phase_11_20_signature.py -v` (44 tests) +
       `pytest tests/api/core/test_audit_fixes_phase_11_20_backfill.py -v` (52 tests + 2 SKIP).
- [ ] **Audit log drift detector passes** — `pytest tests/api/core/test_audit_action_consistency.py -v`.
- [ ] **Frontend TS mirror passes** — `pnpm test __tests__/audit-action-mirror.test.ts`.
- [ ] **No NEW ruff errors** — `ruff check apps/api/modules/finops/` scoped (0 NEW, 95 pre-existing baseline).
- [ ] **No NEW tsc errors** — `tsc --noEmit` (apps/web frontend unchanged).
- [ ] **Capability matrix updated** — `docs/capability-matrix.md` v1.47 EXTENSION note appended.

## §3. Deployment steps

### Step 1 — Pull latest main + sprint commits

```bash
git fetch origin
git checkout main
git pull origin main
git log --oneline -5
```

Expected commits (most recent first):
- `4e1f0b3` cj-style 155 — Phase 11~20 audit-fixes test backfill
- `379ca8e` cj-style 154 — Phase 11~20 audit-fixes sprint
- (this sprint's commit) cj-style 156 — Phase 11~20 audit-fixes docs backfill

### Step 2 — Verify audit log table schema

The `audit_logs` table schema is unchanged. Verify:

```bash
psql $SUPABASE_URL -c "\d audit_logs"
```

Expected columns (per CR 0-2 RLS):
- `id` (UUID, PK)
- `tenant_id` (UUID, NOT NULL)
- `action_class` (VARCHAR, NOT NULL)
- `action` (VARCHAR, NOT NULL)
- `actor_id` (UUID, NULL allowed for system actions)
- `target_id` (UUID, NULL allowed)
- `reason` (TEXT, NOT NULL — ko-KR per NFR18)
- `payload` (JSONB, NOT NULL — must include `trace_id` key)
- `created_at` (TIMESTAMPTZ, NOT NULL, default NOW())

### Step 3 — Restart backend service

```bash
# Railway
railway up --service api

# Or local Docker
docker-compose restart api
```

The new audit call sites will start INSERTing into `audit_logs` on
the next request that triggers a FinOps aggregator / dispatcher /
router endpoint.

### Step 4 — Verify audit log INSERTs

After deployment, trigger an executive dashboard view:

```bash
curl -X GET https://api.costmgr.com/finops/executive/dashboard \
  -H "Authorization: Bearer $JWT_TOKEN"
```

Then check the audit log:

```bash
psql $SUPABASE_URL -c "
  SELECT action_class, action, actor_id, target_id, reason, payload->>'trace_id' AS trace_id
  FROM audit_logs
  WHERE action_class = 'finops_reporting'
    AND action = 'executive_dashboard_viewed'
  ORDER BY created_at DESC
  LIMIT 5;
"
```

Expected: at least 1 row per dashboard view, with `trace_id`
matching the request's trace context.

### Step 5 — Monitor drift detector

The drift detector (`test_audit_action_consistency.py`) runs as part
of the CI suite. If a future sprint adds a new action without
registering it in `_REGISTRY` or updating the TS mirror, the CI will
fail. No action needed post-deployment.

## §4. Rollback strategy

If the audit call sites cause unexpected issues (e.g. unexpected
audit log volume, performance regression):

### Option A — Disable audit INSERT (temporary)

Set `EMIT_AUDIT_DISABLED=true` in environment. The aggregator +
dispatcher + router call sites will silently no-op (the lazy import
guard + `with suppress(ImportError):` ensures no exception is raised).

### Option B — Revert to sprint commit (permanent)

```bash
git revert <sprint-commit-hash>  # Phase 11~20 audit-fixes sprint
git revert <backfill-commit-hash>  # Phase 11~20 audit-fixes backfill
git push origin main
```

Reverts are safe because the audit call sites are additive (no
removal of existing functionality).

## §5. Post-deployment monitoring

Watch for:

1. **Audit log volume** — should increase by ~24 events per FinOps
   action. Compare to pre-sprint baseline.
2. **Sentry errors** — `emit_audit_typed` errors are silently-passed
   in router mode. Watch for Sentry alerts tagged `audit_logs_insert_failed`.
3. **Database load** — `audit_logs` INSERT is on the same transaction
   as the primary INSERT. Watch for slow queries (> 500ms p95).
4. **RLS policy** — `audit_logs` row-level security should filter by
   `tenant_id` per CR 0-2. Verify with a multi-tenant test.

## §6. Cross-references

- **Main deployment runbook**: `docs/deployment.md` (Phase 4 cj-style 55)
- **Canonical signature spec**: `docs/audit-fixes-canonical-signature.md`
- **24 broken sites recovery log**: `docs/audit-fixes-broken-sites-recovery.md`
- **Registry reference**: `docs/audit-fixes-registry-reference.md`
- **Migration guide**: `docs/audit-fixes-migration-guide.md`
- **AD-49**: `docs/architecture-decisions/AD-49-phase-11-20-audit-fixes.md`
- **Routers reference**: `docs/api/routers/finops-executive-dashboard-routes.md`
- **Runbook: signature recovery**: `docs/runbooks/finops-aggregator-canonical-signature-recovery.md`
- **Runbook: audit log investigation**: `docs/runbooks/audit-log-investigation.md`
