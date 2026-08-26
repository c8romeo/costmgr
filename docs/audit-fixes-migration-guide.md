# Audit-Fixes Migration Guide (Phase 11~20)

> **Phase 11~20 audit-fixes sprint (cj-style 154번째 wire)** —
> Step-by-step migration guide for adding a NEW canonical
> `emit_audit_typed` call site to a FinOps aggregator / router /
> dispatch module. Use this guide when extending Phase 16~21 FinOps
> territory modules.

## §1. When to add a NEW audit site

Add a NEW canonical `emit_audit_typed` call site when:

1. Creating a NEW backend aggregator function that mutates audit-relevant state.
2. Adding a NEW FastAPI router endpoint that triggers a tenant-visible action.
3. Adding a NEW scheduled dispatch job that runs without user interaction.
4. Extending an EXISTING aggregator with a NEW mode (e.g. `dry_run` flag, new export format).

Do NOT add a NEW site for:

- Pure read operations (CR 1-1 read-mostly invariant — only INSERT/UPDATE/DELETE triggers audit).
- Internal helper functions that don't mutate state.
- Frontend-only actions (audit is backend-only, frontend uses Sentry traces instead).

## §2. Migration steps

### Step 1 — Determine the ActionClass + action Literal

```python
# 1. Pick the ActionClass enum value (matches the FinOps territory)
from apps.api.core.audit_action import ActionClass

action_class = ActionClass.FINOPS_REPORTING  # or FINOPS_SUSTAINABILITY, FINOPS_COMMITMENT, FINOPS_PRICING, FINOPS_RESERVED_CAPACITY_PLANNING, FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION

# 2. Pick the action Literal string (must be registered in _REGISTRY)
action = "executive_dashboard_aggregated"  # 8 values per territory — see docs/audit-fixes-registry-reference.md
```

### Step 2 — Add the action to `_ActionRegistry._REGISTRY` (if NEW)

If you're introducing a NEW action (not in existing 8 per territory),
first add it to `_ActionRegistry._REGISTRY` AND to the
`FinopsReportingAction` Literal (or other territory Literal):

```python
# apps/api/core/audit_action.py
ActionClass.FINOPS_REPORTING: (
    "audit_logs",
    frozenset({
        "executive_dashboard_viewed",
        ...
        "executive_dashboard_aggregated",
        # NEW action ↓
        "executive_dashboard_anomaly_detected",  # ← your new action
    }),
),
```

Then update the Literal:

```python
FinopsReportingAction = Literal[
    ...
    "executive_dashboard_anomaly_detected",  # ← add here too
]
```

Then run the drift detector:

```bash
pytest tests/api/core/test_audit_action_consistency.py -v
```

### Step 3 — Update the frontend TS mirror

If frontend needs to display the action:

```typescript
// apps/web/lib/finops/audit-actions-mirror.ts
export const FinopsReportingActions = [
  "executive_dashboard_viewed",
  ...
  "executive_dashboard_anomaly_detected",  // ← add here
] as const;
```

Run the frontend drift detector:

```bash
pnpm test __tests__/audit-action-mirror.test.ts
```

### Step 4 — Wire the canonical call site

#### Router mode (`*_routes.py`)

```python
from contextlib import suppress

from apps.api.core.audit_action import ActionClass, emit_audit_typed

@router.post("/executive-dashboard/anomaly")
async def detect_anomaly(
    payload: AnomalyRequest,
    db_session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
    trace_id: str = Query(...),
):
    ...
    with suppress(ImportError):
        await emit_audit_typed(
            db_session,
            action_class=ActionClass.FINOPS_REPORTING,
            action="executive_dashboard_anomaly_detected",
            actor_id=current_user.id,
            target_id=None,
            reason="Executive dashboard anomaly detected",
            payload={"trace_id": trace_id, "tenant_id": str(current_user.tenant_id)},
            tenant_id=current_user.tenant_id,
        )
    return {"anomaly_id": anomaly_id, ...}
```

#### Aggregator mode

```python
async def aggregate_executive_dashboard_anomaly(
    tenant_id: UUID,
    db_session: Optional[AsyncSession] = None,
    dry_run: bool = False,
    trace_id: Optional[str] = None,
) -> AnomalyResult:
    """Aggregate anomaly detection across Phase 12 modules."""
    try:
        from apps.api.core.audit_action import emit_audit_typed
    except ImportError:
        emit_audit_typed = None  # type: ignore[assignment]

    ...

    if db_session is not None and not dry_run:
        if emit_audit_typed is not None:
            await emit_audit_typed(
                db_session,
                action_class=ActionClass.FINOPS_REPORTING,
                action="executive_dashboard_anomaly_detected",
                actor_id=None,
                target_id=None,
                reason="Executive dashboard anomaly detected",
                payload={"trace_id": trace_id, "tenant_id": str(tenant_id)},
                tenant_id=tenant_id,
            )

    return result
```

#### Dispatch mode (`scheduled_*_dispatch.py`)

```python
async def scheduled_anomaly_dispatch(
    tenant_id: UUID,
    db_session: AsyncSession,
    trace_id: str,
):
    """Scheduled daily anomaly dispatch (cron KST 02:00)."""
    try:
        from apps.api.core.audit_action import emit_audit_typed
    except ImportError:
        emit_audit_typed = None  # type: ignore[assignment]

    ...

    if db_session is not None and not dry_run:
        if emit_audit_typed is not None:
            await emit_audit_typed(
                db_session,
                action_class=ActionClass.FINOPS_REPORTING,
                action="executive_dashboard_anomaly_detected",
                actor_id=None,
                target_id=None,
                reason="Scheduled anomaly detection completed",
                payload={"trace_id": trace_id, "tenant_id": str(tenant_id)},
                tenant_id=tenant_id,
            )
```

### Step 5 — Add ko-KR i18n strings (NFR18)

```json
// apps/web/messages/ko-KR.json
{
  "finops_reporting": {
    "audit_actions": {
      "executive_dashboard_anomaly_detected": "경영 대시보드 이상 탐지"
    }
  }
}
```

### Step 6 — Run drift + audit tests

```bash
# Backend audit drift detector
pytest tests/api/core/test_audit_action_consistency.py -v

# Backend audit-fixes structural test (cj 154 pattern)
pytest tests/api/core/test_audit_fixes_phase_11_20_signature.py -v

# Backend audit-fixes semantic test (cj 155 pattern)
pytest tests/api/core/test_audit_fixes_phase_11_20_backfill.py -v

# Frontend TS mirror drift
pnpm test __tests__/audit-action-mirror.test.ts
```

### Step 7 — Update capability matrix (if NEW territory)

If you're introducing a NEW FinOps territory (not just a NEW action),
update `docs/capability-matrix.md` and bump the version (e.g.
`v1.47 → v1.48 EXTENSION`). Add a new entry to the version history
with the new row + drift detector test reference.

## §3. Common pitfalls

1. **Passing positional arguments** — `emit_audit_typed` is keyword-only after `session`. Always use `action_class=...`, `action=...`, etc.

2. **Missing `trace_id` in payload** — every audit site MUST include `"trace_id":` in the payload dict (mandatory key, see §2 of `audit-fixes-canonical-signature.md`).

3. **Missing `tenant_id` keyword** — `tenant_id` MUST be a keyword argument, not positional. Always end the call with `tenant_id=tenant_id`.

4. **`actor_id=None` confusion** — system actions (scheduled dispatch) have `actor_id=None`. User-initiated actions have `actor_id=current_user.id`. Never hardcode an actor.

5. **Router vs Aggregator guard confusion** — routers use `with suppress(ImportError):` + `if db_session is not None:`. Aggregators + dispatchers use lazy import + `if db_session is not None and not dry_run:` + `if emit_audit_typed is not None:`.

6. **Forgetting ko-KR strings** — `reason=` keyword is ko-KR (NFR18). Don't pass English.

7. **Skipping drift detector** — always run `test_audit_action_consistency.py` after adding a new action. The 3-way drift detector catches Literal ↔ registry ↔ TS mirror divergence.

## §4. Cross-references

- **Canonical signature** — `docs/audit-fixes-canonical-signature.md`
- **24 broken sites recovery log** — `docs/audit-fixes-broken-sites-recovery.md`
- **Registry reference** — `docs/audit-fixes-registry-reference.md`
- **AD-49** — `docs/architecture-decisions/AD-49-phase-11-20-audit-fixes.md`
- **Routers reference** — `docs/api/routers/finops-executive-dashboard-routes.md`
- **Runbook: signature recovery** — `docs/runbooks/finops-aggregator-canonical-signature-recovery.md`
- **Runbook: audit log investigation** — `docs/runbooks/audit-log-investigation.md`
