# FinOps Aggregator Canonical Signature Recovery Runbook

> **Target audience:** Backend developer + on-call engineer
> debugging broken `emit_audit_typed` call sites in FinOps
> aggregator modules (executive_dashboard_aggregator, sustainability,
> commitment, pricing, reserved_capacity, multi_cloud).

## §1. Symptom: "Audit logs missing for FinOps actions"

The most common symptom:

```
audit_logs table has 0 rows for:
- finops_reporting.executive_dashboard_viewed
- finops_sustainability.carbon_emissions_aggregated
- finops_commitment.commitment_inventory_aggregated
- finops_pricing.cross_module_pricing_kpi_calculated
```

Pre-`379ca8e` (Phase 11~20 audit-fixes sprint), this was the
expected behavior — the 24 broken sites had broken signatures +
silent-pass imports.

Post-`379ca8e`, the canonical signature is restored. If audit logs
are STILL missing for FinOps actions after deployment, follow this
runbook.

## §2. Triage checklist

Run these checks in order:

### Check 1 — Verify canonical signature is in use

```bash
grep -rn "emit_audit_typed" apps/api/modules/finops/
```

Expected output: each call site should have:

- `action_class=ActionClass.FINOPS_*` keyword
- `action=` keyword (one of 8 per territory)
- `actor_id=` or `target_id=` keywords
- `tenant_id=` keyword at the END
- `payload=` (NOT `metadata=`)
- `reason=` in ko-KR

**Anti-patterns to flag:**

- `metadata=` instead of `payload=`
- `resource_id=` instead of `target_id=`
- `trace_id=` instead of `payload={"trace_id": ...}`
- Positional arguments (after `session`)

If any anti-pattern is found, apply the fix from
`docs/audit-fixes-canonical-signature.md`.

### Check 2 — Verify `ActionClass` import

```bash
grep -rn "from apps.api.core.audit_action import" apps/api/modules/finops/
```

Expected output: each file should import `ActionClass` from
`apps.api.core.audit_action`. The enum value should match the
territory:

| File | ActionClass enum |
|------|------------------|
| `executive_dashboard_aggregator.py` | `ActionClass.FINOPS_REPORTING` |
| `sustainability/*.py` | `ActionClass.FINOPS_SUSTAINABILITY` |
| `commitment/*.py` | `ActionClass.FINOPS_COMMITMENT` |
| `pricing/*.py` | `ActionClass.FINOPS_PRICING` |
| `reserved_capacity/*.py` | `ActionClass.FINOPS_RESERVED_CAPACITY_PLANNING` |
| `multi_cloud/*.py` | `ActionClass.FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION` |

If `ActionClass` is missing from a file's imports, the lazy import
inside the function will fail. Add the import.

### Check 3 — Verify mode-aware guard

For **aggregator / report_generator / dispatch** mode:

```python
if db_session is not None and not dry_run:
    if emit_audit_typed is not None:
        await emit_audit_typed(...)
```

For **router** mode:

```python
with suppress(ImportError):
    await emit_audit_typed(...)
```

**Anti-patterns to flag:**

- Missing `if db_session is not None and not dry_run:` guard (causes
  audit INSERT in CLI mode → false audit log entries).
- Missing `if emit_audit_typed is not None:` guard (causes
  AttributeError when ImportError).
- Using `try/except ImportError: pass` in router mode (ruff SIM105
  violation; use `with suppress(ImportError):` instead).

### Check 4 — Verify `payload` includes `trace_id`

```bash
grep -rn '"trace_id":' apps/api/modules/finops/ | head -30
```

Expected: every `payload=` keyword should include `"trace_id":` as a
key. If missing, add it (drift detector will fail otherwise).

### Check 5 — Run drift detector

```bash
pytest tests/api/core/test_audit_action_consistency.py -v
pytest tests/api/core/test_audit_fixes_phase_11_20_signature.py -v
pytest tests/api/core/test_audit_fixes_phase_11_20_backfill.py -v
```

Expected: all tests PASS.

## §3. Hot-fix procedure

If the audit call site is broken (anti-pattern detected), apply the
following hot-fix:

### Hot-fix 1 — Broken signature (metadata= or resource_id=)

Replace:

```python
# WRONG
await emit_audit_typed(
    db_session,
    action,
    tenant_id,
    actor_id,
    trace_id,
    resource_id,
    metadata,
)
```

With:

```python
# RIGHT
await emit_audit_typed(
    db_session,
    action_class=ActionClass.FINOPS_REPORTING,  # ← territory-specific
    action="executive_dashboard_viewed",  # ← from _REGISTRY frozenset
    actor_id=actor_id,
    target_id=resource_id,  # ← resource_id → target_id
    reason="경영 대시보드 조회",  # ← ko-KR per NFR18
    payload={"trace_id": trace_id, **metadata},  # ← metadata → payload dict with trace_id
    tenant_id=tenant_id,  # ← keyword, end of args
)
```

### Hot-fix 2 — Missing `ActionClass` import

Add at top of file:

```python
from apps.api.core.audit_action import ActionClass
```

### Hot-fix 3 — Wrong guard (try/except instead of suppress)

Replace:

```python
# WRONG (router mode)
try:
    await emit_audit_typed(...)
except ImportError:
    pass
```

With:

```python
# RIGHT (router mode)
from contextlib import suppress

with suppress(ImportError):
    await emit_audit_typed(...)
```

### Hot-fix 4 — Missing dry_run guard

Replace:

```python
# WRONG (no guard)
await emit_audit_typed(...)
```

With:

```python
# RIGHT
if db_session is not None and not dry_run:
    if emit_audit_typed is not None:
        await emit_audit_typed(...)
```

### Hot-fix 5 — Missing `if emit_audit_typed is not None:` guard

This guard is needed when using the lazy import pattern (aggregator +
dispatch mode). Add it after the lazy import block:

```python
try:
    from apps.api.core.audit_action import emit_audit_typed
except ImportError:
    emit_audit_typed = None  # type: ignore[assignment]


async def aggregate_executive_dashboard(...):
    ...
    if db_session is not None and not dry_run:
        if emit_audit_typed is not None:  # ← THIS GUARD
            await emit_audit_typed(...)
```

## §4. Verification after hot-fix

After applying the hot-fix:

1. Run the audit-fixes tests:
   ```bash
   pytest tests/api/core/test_audit_fixes_phase_11_20_signature.py -v
   pytest tests/api/core/test_audit_fixes_phase_11_20_backfill.py -v
   ```
2. Restart the backend service.
3. Trigger the action that was previously missing audit log entries.
4. Verify the audit log INSERT:
   ```sql
   SELECT * FROM audit_logs
   WHERE action = '<expected-action>'
   ORDER BY created_at DESC
   LIMIT 1;
   ```

## §5. Cross-references

- **Canonical signature spec**: `docs/audit-fixes-canonical-signature.md`
- **24 broken sites recovery log**: `docs/audit-fixes-broken-sites-recovery.md`
- **Registry reference**: `docs/audit-fixes-registry-reference.md`
- **Migration guide**: `docs/audit-fixes-migration-guide.md`
- **AD-49**: `docs/architecture-decisions/AD-49-phase-11-20-audit-fixes.md`
- **Routers reference**: `docs/api/routers/finops-executive-dashboard-routes.md`
- **Deployment guide**: `docs/deployment/phase-11-20-audit-fixes-deployment.md`
- **Runbook: audit log investigation**: `docs/runbooks/audit-log-investigation.md`
- **Audit action drift detector**: `tests/api/core/test_audit_action_consistency.py`
- **Phase 11~20 audit-fixes signature test**: `tests/api/core/test_audit_fixes_phase_11_20_signature.py`
- **Phase 11~20 audit-fixes backfill test**: `tests/api/core/test_audit_fixes_phase_11_20_backfill.py`
