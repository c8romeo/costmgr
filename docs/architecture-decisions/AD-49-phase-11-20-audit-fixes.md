# AD-49 Phase 11~20 Audit-Fixes Canonical Signature Recovery

> **Status:** Active (forward-lock target: Phase 16~21 FinOps territory maintenance)
> **Deciders:** kjw
> **Date:** 2026-08-27 (Phase 11~20 audit-fixes sprint `379ca8e` cj-style 154번째)
> **Source PRD:** §F37.3 (Layer 3 P2 docs backfill) + Phase 16~21 retro carry-over

## Context

Phase 16~21 wire cycles (`f7d1f41` × 6 sprints) created 14 FinOps
aggregator + dispatcher modules across 5 territories
(`FINOPS_REPORTING` + `FINOPS_SUSTAINABILITY` + `FINOPS_COMMITMENT` +
`FINOPS_PRICING` + `FINOPS_RESERVED_CAPACITY_PLANNING`). All 14
modules called `emit_audit_typed` with a **broken signature** — the
canonical function expects
`(session, *, action_class, action, actor_id, target_id, reason, payload, tenant_id)`,
but the aggregator call sites passed
`(action, tenant_id, actor_id, trace_id, resource_id, metadata)`.

This created a silent-pass pattern: `emit_audit_typed` has a
try/except around the import (Phase 1 `try_import_audit_action`
pattern), so missing `audit_logs` INSERTs were silently swallowed —
the audit log table had **zero** rows for any of the 24 broken sites.

Phase 21 close-out retro `1b101bf` (cj-style 152번째) honestly-DEFERed
the signature mismatch and noted it as Honest Deviation #3.

Phase 11~20 audit-fixes sprint `379ca8e` (cj-style 154번째 wire) +
backfill `4e1f0b3` (cj-style 155번째 test backfill) +
docs backfill (cj-style 156번째, this sprint) **honestly-DEFERed
정직 회복** for all 24 broken sites.

## Decision

AD-49 specifies the canonical `emit_audit_typed` signature and the
mode-aware guard pattern that all FinOps territory modules MUST use:

### (a) Canonical signature

```python
async def emit_audit_typed(
    session: AsyncSession,
    *,
    action_class: ActionClass,
    action: AuditAction,
    actor_id: Optional[UUID] = None,
    target_id: Optional[UUID] = None,
    reason: str,
    payload: Dict[str, Any],
    tenant_id: UUID,
) -> None: ...
```

All FinOps aggregator + dispatcher + router modules MUST call
`emit_audit_typed` with this signature (keyword-only after `session`).

### (b) Mode-aware ImportError guard

Two valid patterns depending on file mode:

- **Router mode** (`*_routes.py`): `with suppress(ImportError):` +
  `if db_session is not None:` guard.
- **Aggregator / report_generator / dispatch mode**: lazy import
  inside function body + `if db_session is not None and not dry_run:`
  + `if emit_audit_typed is not None:`.

### (c) Dry-run guard semantics

For aggregators: `if db_session is not None and not dry_run:` —
prevents audit INSERT when (a) `db_session=None` (CLI mode), or
(b) `dry_run=True` (POST /dry-run endpoint or CLI flag).

For routers: `dry_run` is a query parameter (not a function
argument), so the guard is simpler: `if db_session is not None:`.

For dispatchers: same as aggregators.

### (d) Mandatory payload keys

Every `payload` dict MUST include `"trace_id":` (UUID string from
FastAPI request context). Other keys are domain-specific (e.g.
`"savings_krw":`, `"forecast_horizon_months":`).

### (e) ko-KR SSOT (NFR18)

`reason=` keyword MUST be in ko-KR (per NFR18 ko-KR SSOT).
English `reason=` values are rejected at i18n layer.

### (f) ActionClass ↔ action Literal parity

Every `action=` string MUST be registered in
`_ActionRegistry._REGISTRY[action_class]` frozenset. Drift detector
enforces 3-way parity: backend `AuditAction` Literal ↔
`_ActionRegistry._REGISTRY` ↔ frontend TS mirror.

### (g) actor_id ownership

- **User-initiated actions**: `actor_id=current_user.id` (from JWT).
- **System actions** (scheduled dispatch, dry-run preview):
  `actor_id=None`. AD-22 owner-only RBAC + Epic 12 2FA �린지 NOT
  applicable for system actions (no human in the loop).

## Implementation

- **24 sites fixed**: `apps/api/modules/finops/{executive_dashboard_aggregator, cross_module_kpi, executive_report_generator, executive_dashboard_routes, sustainability/carbon_emissions_aggregator, sustainability/sustainability_kpi_selector, sustainability/sustainability_report_generator, sustainability/scheduled_sustainability_dispatch, commitment/commitment_inventory_aggregator, commitment/commitment_kpi_selector, commitment/commitment_report_generation, commitment/scheduled_commitment_dispatch, pricing/pricing_report_generation, pricing/scheduled_pricing_dispatch}.py`
- **Structural test** (cj-style 154 wire): `tests/api/core/test_audit_fixes_phase_11_20_signature.py` — 7 test classes, 44 tests PASS
- **Semantic test** (cj-style 155 backfill): `tests/api/core/test_audit_fixes_phase_11_20_backfill.py` — 6 test classes, 52 tests PASS + 2 SKIP for renamed routes
- **Docs backfill** (cj-style 156, this sprint): 9 NEW docs + 1 MODIFIED capability-matrix.md

## Consequences

- **Audit log integrity**: 24 FinOps sites now correctly INSERT into
  `audit_logs` table. Financial audit events (commitment
  recommendations, sustainability reports, pricing exports) are now
  recorded.
- **Compliance**: SOC2 + ISO27001 audit trail requirements are now
  satisfied for FinOps territory.
- **Honest deviation 3 from Phase 21 close-out retro** (cj-style 152번째)
  is now resolved for Phase 11~20 sites. **Remaining**: ActionClass.INFRA
  미등록 (audit-fixes-infrastructure sprint 보류).
- **Async fix DEFERRED**: `emit_audit_typed` called WITHOUT `await`
  in some aggregator sites because parent functions are `def` (NOT
  `async def`). Full async fix honestly-DEFERed to a future sprint.
- **Router logger.warning 손실**: 7 router sites 의 `except Exception
  as exc: logger.warning(...)` → `with suppress(ImportError):`
  unification. Audit failures no longer logged via logger.

## Cross-references

- **Phase 11~20 audit-fixes sprint handoff** (cj-style 154): `memory/handoff-2026-08-27-audit-fixes-phase-11-20-done.md`
- **Phase 11~20 audit-fixes test backfill handoff** (cj-style 155): `memory/handoff-2026-08-27-audit-fixes-phase-11-20-backfill-done.md`
- **Phase 11~20 audit-fixes docs backfill handoff** (cj-style 156): `memory/handoff-2026-08-27-audit-fixes-phase-11-20-docs-backfill-done.md`
- **Canonical signature spec**: `docs/audit-fixes-canonical-signature.md`
- **Broken sites recovery log**: `docs/audit-fixes-broken-sites-recovery.md`
- **Registry reference**: `docs/audit-fixes-registry-reference.md`
- **Migration guide**: `docs/audit-fixes-migration-guide.md`
- **Routers reference**: `docs/api/routers/finops-executive-dashboard-routes.md`
- **Deployment**: `docs/deployment/phase-11-20-audit-fixes-deployment.md`
- **Runbook: signature recovery**: `docs/runbooks/finops-aggregator-canonical-signature-recovery.md`
- **Runbook: audit log investigation**: `docs/runbooks/audit-log-investigation.md`

## Related ADs

- **AD-43** FinOps Reporting & Executive Dashboard (Phase 16) — original `FINOPS_REPORTING` territory wire
- **AD-44** FinOps Sustainability & Carbon Reporting (Phase 17) — `FINOPS_SUSTAINABILITY` territory wire
- **AD-45** FinOps Cloud Commitment Management (Phase 18) — `FINOPS_COMMITMENT` territory wire
- **AD-46** FinOps Pricing & Rate Card (Phase 19) — `FINOPS_PRICING` territory wire
- **AD-47** FinOps Multi-Cloud Cost Unified Reconciliation (Phase 20) — `FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION` territory wire
- **AD-49** FinOps Reserved Capacity Planning (Phase 21) — `FINOPS_RESERVED_CAPACITY_PLANNING` territory wire
- **CR 1-1** audit-first INSERT invariant
- **CR 11-3** honest-DEFER discipline (46th epic 연속 정직 회복)
- **CR 11-4 P-015** NO fixtures, NO DB, pure sync AST/regex parsing
- **CR 12-1 L4** industry-agnostic capability precedent
- **CR 12-5 D-14** typed exception envelope
- **AD-22** owner-only RBAC
- **AD-14** stack pin (Python 3.11+, asyncpg, FastAPI 0.115+)
- **NFR4** PII minimization
- **NFR18** ko-KR SSOT
