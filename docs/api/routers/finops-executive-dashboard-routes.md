# FinOps Executive Dashboard Routes Reference (Phase 16)

> **Phase 16 wire + Phase 11~20 audit-fixes sprint (cj-style 154번째)** —
> FastAPI router reference for the `FINOPS_REPORTING` territory
> executive dashboard endpoints. 8 endpoints registered in
> `apps/api/modules/finops/executive_dashboard_routes.py`.

## §1. Router file

`apps/api/modules/finops/executive_dashboard_routes.py` — FastAPI
`APIRouter` registered in `apps/api/main.py` via
`app.include_router(executive_dashboard_router)`. The router handles
all `FINOPS_REPORTING` endpoints (Phase 16 territory + Phase 11~20
audit-fixes 7 canonical call sites).

## §2. Endpoints (8 total)

### 2.1 `GET /finops/executive/dashboard`

- **Function**: `view_dashboard`
- **Capability gate**: `Depends(require_finops_reporting)`
- **Audit action**: `executive_dashboard_viewed`
- **Actor**: `current_user.id` (user-initiated)
- **Payload**: `{"trace_id": ..., "tenant_id": ..., "dashboard_type": "executive"}`
- **Audit guard**: `with suppress(ImportError):` + `if db_session is not None:`

### 2.2 `GET /finops/executive/cross-module-kpi`

- **Function**: `view_cross_module_kpi`
- **Capability gate**: `Depends(require_finops_reporting)`
- **Audit action**: `cross_module_kpi_calculated`
- **Actor**: `current_user.id`
- **Payload**: `{"trace_id": ..., "tenant_id": ..., "kpi_type": ...}`

### 2.3 `POST /finops/executive/report/generate`

- **Function**: `generate_report`
- **Capability gate**: `Depends(require_finops_reporting)` + 2FA �린지 (owner-only)
- **Audit action**: `executive_report_generated`
- **Actor**: `current_user.id`
- **Payload**: `{"trace_id": ..., "tenant_id": ..., "report_id": ..., "format": ...}`

### 2.4 `POST /finops/executive/report/export`

- **Function**: `export_report`
- **Capability gate**: `Depends(require_finops_reporting)` + 2FA 챌린지
- **Audit action**: `executive_report_exported`
- **Actor**: `current_user.id`
- **Payload**: `{"trace_id": ..., "tenant_id": ..., "report_id": ..., "format": "pdf|csv|xlsx"}`

### 2.5 `POST /finops/executive/report/dispatch`

- **Function**: `dispatch_report`
- **Capability gate**: `Depends(require_finops_reporting)` + 2FA 챌린지 + owner-only RBAC AD-22
- **Audit action**: `executive_report_dispatched`
- **Actor**: `current_user.id`
- **Payload**: `{"trace_id": ..., "tenant_id": ..., "report_id": ..., "channels": ["slack", "email", "ms_teams"]}`

### 2.6 `POST /finops/executive/dry-run`

- **Function**: `dry_run`
- **Capability gate**: `Depends(require_finops_reporting)`
- **Audit action**: `finops_reporting_dry_run_executed`
- **Actor**: `current_user.id`
- **Payload**: `{"trace_id": ..., "tenant_id": ..., "dry_run_type": ...}`
- **Note**: dry-run mode → no actual mutation; audit still recorded
  for traceability.

### 2.7 `POST /finops/executive/kpi/refresh`

- **Function**: `kpi_refresh`
- **Capability gate**: `Depends(require_finops_reporting)`
- **Audit action**: `executive_dashboard_kpi_refreshed`
- **Actor**: `current_user.id`
- **Payload**: `{"trace_id": ..., "tenant_id": ..., "kpi_type": ...}`

### 2.8 `GET /finops/executive/healthcheck`

- **Function**: `healthcheck`
- **Capability gate**: none (public)
- **Audit action**: none (read-only)
- **Returns**: `{"status": "ok", "territory": "finops_reporting", "version": "v1.47"}`

## §3. Audit call pattern (router mode)

All 7 canonical call sites in `executive_dashboard_routes.py` follow
the router mode pattern:

```python
from contextlib import suppress

from apps.api.core.audit_action import ActionClass, emit_audit_typed


@router.get("/finops/executive/dashboard")
async def view_dashboard(
    db_session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
    trace_id: str = Query(...),
):
    ...
    with suppress(ImportError):
        await emit_audit_typed(
            db_session,
            action_class=ActionClass.FINOPS_REPORTING,
            action="executive_dashboard_viewed",
            actor_id=current_user.id,
            target_id=None,
            reason="경영 대시보드 조회",
            payload={"trace_id": trace_id, "tenant_id": str(current_user.tenant_id)},
            tenant_id=current_user.tenant_id,
        )
    return {"dashboard": ..., "kpis": [...]}
```

## §4. Cross-references

- **Canonical signature spec**: `docs/audit-fixes-canonical-signature.md`
- **24 broken sites recovery log**: `docs/audit-fixes-broken-sites-recovery.md`
- **Registry reference**: `docs/audit-fixes-registry-reference.md`
- **Migration guide**: `docs/audit-fixes-migration-guide.md`
- **AD-43** FinOps Reporting & Executive Dashboard (Phase 16) — original wire
- **AD-49** Phase 11~20 Audit-Fixes Canonical Signature Recovery (Phase 11~20)
- **Router file**: `apps/api/modules/finops/executive_dashboard_routes.py`
- **Aggregator file**: `apps/api/modules/finops/executive_dashboard_aggregator.py`
- **Report generator file**: `apps/api/modules/finops/executive_report_generator.py`
- **KPI selector file**: `apps/api/modules/finops/cross_module_kpi.py`
- **Test files**: `tests/api/core/test_audit_fixes_phase_11_20_signature.py` (cj 154) + `test_audit_fixes_phase_11_20_backfill.py` (cj 155)
