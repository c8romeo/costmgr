# Audit-Fixes Canonical emit_audit_typed Signature (Phase 11~20)

> **Phase 11~20 audit-fixes sprint (cj-style 154번째 wire)** —
> Canonical `emit_audit_typed` call signature specification for all
> FinOps territory aggregator modules. Backfill reference for the 24
> broken sites that were honestly-DEFER across Phase 16/17/18/19/20
> wire cycles.

## §1. Background

Phase 16~20 wire cycles (`f7d1f41` × 5 sprints) created 14 FinOps
aggregator + dispatcher modules across 4 territories
(`FINOPS_REPORTING` + `FINOPS_SUSTAINABILITY` + `FINOPS_COMMITMENT` +
`FINOPS_PRICING`). All 14 modules called `emit_audit_typed` with a
**broken signature** — the canonical signature expects
keyword-only arguments `(session, *, action_class, action, actor_id,
target_id, reason, payload, tenant_id)`, but the aggregator call sites
passed `(action, tenant_id, actor_id, trace_id, resource_id, metadata)`.

This created a silent-pass pattern: the canonical function
(`apps/api/core/audit_action.py`) has a try/except around the import
(per Phase 1 `try_import_audit_action` pattern), so missing
`audit_logs` INSERTs were silently swallowed — the audit log table had
**zero** rows for any of the 24 sites.

Phase 21 wire (`f7d1f41`) added a NEW `FINOPS_RESERVED_CAPACITY_PLANNING`
territory, exposing 5 more broken sites. Phase 21 close-out retro
`1b101bf` (cj-style 152번째) honestly-DEFERed the signature mismatch.

Phase 11~20 audit-fixes sprint (cj-style 154번째 wire `379ca8e`)
**honestly-DEFERred 정직 회복** for all 24 broken sites.

## §2. Canonical signature

```python
async def emit_audit_typed(
    session: AsyncSession,
    *,
    action_class: ActionClass,
    action: AuditAction,  # type: ignore[valid-type]
    actor_id: Optional[UUID] = None,
    target_id: Optional[UUID] = None,
    reason: str,
    payload: Dict[str, Any],
    tenant_id: UUID,
) -> None:
    """Canonical emit_audit_typed signature — Phase 11~20 audit-fixes SSOT.
    ...
    """
```

Key invariants (CR 1-1 audit-first INSERT + AD-22 owner-only RBAC):

- **`session`** — positional AsyncSession for transactional INSERT.
- **`action_class`** — keyword-only `ActionClass` enum value
  (FINOPS_REPORTING / FINOPS_SUSTAINABILITY / FINOPS_COMMITMENT /
  FINOPS_PRICING / FINOPS_RESERVED_CAPACITY_PLANNING / FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION).
- **`action`** — keyword-only `AuditAction` Literal string.
- **`actor_id`** — keyword-only UUID or None (system actions like
  `scheduled_*` have `actor_id=None`; user-initiated actions have
  `actor_id=user.id`).
- **`target_id`** — keyword-only UUID or None (resource UUID being
  mutated).
- **`reason`** — keyword-only `str` (human-readable, ko-KR per NFR18).
- **`payload`** — keyword-only `Dict[str, Any]` with mandatory
  `"trace_id":` key (from FastAPI request context).
- **`tenant_id`** — keyword-only UUID (tenant scoping per CR 0-2 RLS).

## §3. Mode-aware ImportError guard

Two valid patterns depending on file mode:

### Router mode (`*_routes.py`)

```python
from contextlib import suppress

with suppress(ImportError):
    await emit_audit_typed(
        db_session,
        action_class=ActionClass.FINOPS_REPORTING,
        action="executive_dashboard_viewed",
        actor_id=current_user.id,
        target_id=None,
        reason="Executive dashboard viewed",
        payload={"trace_id": trace_id, "tenant_id": str(tenant_id)},
        tenant_id=tenant_id,
    )
```

Rationale: router files import `emit_audit_typed` at top-of-file.
Using `with suppress(ImportError):` keeps the router file ruff-clean
(SIM105 baseline preservation) and avoids a try/except per call site.

### Aggregator / report_generator / dispatch mode

```python
try:
    from apps.api.core.audit_action import emit_audit_typed
except ImportError:
    emit_audit_typed = None  # type: ignore[assignment]


async def aggregate_executive_dashboard(...):
    ...
    if db_session is not None and not dry_run:
        if emit_audit_typed is not None:
            await emit_audit_typed(
                db_session,
                action_class=ActionClass.FINOPS_REPORTING,
                action="executive_dashboard_aggregated",
                actor_id=None,
                target_id=None,
                reason="Executive dashboard aggregated",
                payload={"trace_id": trace_id, "tenant_id": str(tenant_id)},
                tenant_id=tenant_id,
            )
```

Rationale: aggregator modules import `emit_audit_typed` inside the
function body (lazy import — keeps the kernel pure per CR 1-1 RSC
boundary). The `if emit_audit_typed is not None:` guard handles the
silent-pass case when audit_log INSERT is unavailable.

## §4. Dry-run guard

For **aggregator** modules (NOT router, NOT dispatch), the canonical
guard is:

```python
if db_session is not None and not dry_run:
    if emit_audit_typed is not None:
        await emit_audit_typed(...)
```

This ensures:

1. `db_session=None` (CLI / dry-run mode) → no audit INSERT.
2. `dry_run=True` (POST /dry-run endpoint or CLI flag) → no audit
   INSERT (the action is "previewed" not "executed").
3. `db_session is not None and not dry_run` → audit INSERT fires.

For **router** endpoints, `dry_run` is a query parameter (not a
function argument), so the guard is simpler: `if db_session is not None:`.

For **dispatch** modules (scheduled_*_dispatch.py), `dry_run` is not
applicable — they fire unconditionally, so the guard is
`if db_session is not None and not dry_run:` (the same as aggregator).

## §5. Cross-references

- **24 BROKEN_SITES registry** — `tests/api/core/test_audit_fixes_phase_11_20_signature.py` (cj 154)
- **24 BROKEN_SITES semantic mirror** — `tests/api/core/test_audit_fixes_phase_11_20_backfill.py` (cj 155)
- **4 FINOPS_* registries** — `apps/api/core/audit_action.py` `_ActionRegistry._REGISTRY`
- **AD-49** — `docs/architecture-decisions/AD-49-phase-11-20-audit-fixes.md`
- **Audit log investigation runbook** — `docs/runbooks/audit-log-investigation.md`
- **Canonical signature recovery runbook** — `docs/runbooks/finops-aggregator-canonical-signature-recovery.md`
- **Migration guide** — `docs/audit-fixes-migration-guide.md`
- **Routers reference** — `docs/api/routers/finops-executive-dashboard-routes.md`
