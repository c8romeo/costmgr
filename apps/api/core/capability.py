"""apps.api.core.capability — industry-aware capability enforcement (F-44).

Story 1.1 — F-44. Resolves the decision that backend endpoints should also
reject mismatched-industry writes (vs. frontend-only filtering). This
module provides:

- `Capability` — enum of industry-scoped capabilities (BOM, ABC, etc.).
- `INDUSTRY_CAPABILITY_MAP` — which Industry values unlock which Capability.
- `enforce_capability` — FastAPI dependency that reads the tenant's industry
  via `get_tenant_context` + `get_tenant_settings` and raises
  `IndustryCapabilityError` (403 INDUSTRY_NOT_SUPPORTED) if the tenant's
  industry does not unlock the requested capability.
- `require_capability(capability)` — helper to attach to a route.

The actual endpoints that opt into this gate live in Epic 2+ (m1_baseline
= BOM/CostPool/Inventory, m2_input = inputs, etc.). Story 1.1 only
provides the gate — wiring is deferred.

Example (Epic 2+):

    from apps.api.core.capability import require_capability, Capability

    @router.post("/api/v1/bom", dependencies=[Depends(require_capability(Capability.BOM))])
    async def create_bom(...): ...
"""

from __future__ import annotations

import uuid
from enum import Enum
from typing import Final

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.db import get_session
from apps.api.core.tenant_context import TenantContext, get_tenant_context
from packages.services.m0_onboarding.industry_menu import Industry


# ── Capability enum ──────────────────────────────────────────
class Capability(str, Enum):  # noqa: UP042 — preserve str/Enum combo (Pydantic v2 interop baseline, pre-Phase-4)
    """Backend capabilities gated by industry.

    These map to menu items the sidebar hides for incompatible industries
    (Story 1.1 §AC #2/§AC #3). The frontend hides the menu entries;
    this module enforces that writes to the corresponding backend
    endpoints are also rejected, so a service tenant cannot bypass the
    UI filter and POST directly to /api/v1/bom.
    """

    BOM = "bom"  # manufacturing / mfg+service / mfg+service+other
    OPENING_INVENTORY = "opening_inventory"
    INVENTORY_LEDGER = "inventory_ledger"
    COST_POOL = "cost_pool"  # service / mfg+service / mfg+service+other
    ACTIVITY = "activity"
    DRIVER = "driver"
    SEGMENT_SPLIT = "segment_split"  # mfg+service / mfg+service+other only
    # Story 5.3 — closing-guard capability (PRD §F4.2 + §V3). Granted to
    # manufacturing-kind industries (manufacturing / mfg+service /
    # mfg+service+other). Service-only tenants do NOT have inventory
    # so the closing-guard gate has nothing to check (industry skip matrix
    # in `ClosingGuardService`).
    INVENTORY_CLOSING_GUARD = "inventory_closing_guard"
    # Story 1.3 — AI document extraction (Task 3.6). Granted to every
    # Industry per the ARCHITECTURE-SPINE capability map (all four
    # industries can use AI extraction). This is a defense-in-depth gate
    # on the M10 routes, not a tenant-kind filter.
    AI_EXTRACT = "ai_extract"
    # Story 10.1 (Epic 10) — AI insight capability (PRD §F10.1 + §8.1 M10).
    # Industry-agnostic per CR 12-1 L4 precedent (mirrors TWO_FACTOR_AUTH /
    # BACKUP_EXPORT / BUDGET_SCENARIO / CVP_SIMULATION / ABC_CALCULATION).
    # Granted to all 4 industries. Gates POST /api/v1/ai/extract-monthly.
    # Drift detector: tests/integration/test_capability_matrix_v1_21_drift.py
    # (matrix row already declared; backend enum was the missing half).
    AI_INSIGHT = "ai_insight"
    # Story 13.1 (Epic 13) — LISTEN/NOTIFY cache invalidation consume
    # capability (PRD §F13.1 + §AD-25 + A39/A51/A52 결정 wire).
    # Industry-agnostic per CR 12-1 L4 precedent (mirrors AI_INSIGHT
    # 10-1 wire pattern). All 4 industries can register the LISTEN
    # daemon (PostgreSQL NOTIFY is a tenant-level primitive, not a
    # industry-specific feature). Gates the daemon registration only;
    # the 4-channel dispatch table is unchanged for all industries.
    # Drift detector: tests/integration/test_capability_matrix_v1_22_drift.py
    # (capability matrix v1.22 NEW row).
    LISTEN_NOTIFY = "listen_notify"
    # Story 2.1 — product catalog. Every industry has SOME product type
    # (service tenants register `service` products even without a BOM).
    # The PRODUCT capability gates the catalog CRUD itself.
    PRODUCT = "product"
    # Story 2.1 — gated subset: only industries that own a physical
    # bill-of-materials can register `material` / `semi_product` types.
    # Service tenants cannot (no BOM menu → no material entries).
    # R6: service tenants STILL register `product` + `goods` — finished
    # products and trade goods are BOM-independent catalog rows.
    PRODUCT_MATERIAL = "product_material"
    # Story 3.1 — Monthly input production stream. Service tenants have
    # no manufacturing capability → the [생산] tab is hidden. The other
    # 5 streams (orders/sales/purchases/expenses/labor) are ungated;
    # the gate here only protects the production-stream writes. PRD §8.M2(b).
    MONTHLY_INPUT_PRODUCTION = "monthly_input_production"
    # Story 4.1 — Periodic cost calculation. Granted to all industries
    # with a manufacturing footprint (manufacturing / mfg+service /
    # mfg+service+other). Service-only tenants do NOT have a [계산] tab
    # — they will have Epic 9 ABC costing instead. The engine itself
    # (packages.cost_engine.core.period_cost) is industry-agnostic and
    # always returns `state="draft"` (AD-22 — service layer owns state
    # transitions). The capability gate here only checks that the
    # caller MAY run CalcPort.compute_period_cost at all.
    COST_CALCULATION = "cost_calculation"
    # Story 6.1 — Monthly Closing Report capability (PRD §F4.3 + §F5).
    # Granted to manufacturing-kind industries (manufacturing / mfg+service /
    # mfg+service+other). Service-only tenants do NOT have a [마감] tab
    # because they have no inventory ledger to snapshot.
    MONTHLY_CLOSING_REPORT = "monthly_closing_report"
    # Story 11.1 (Epic 11) — Reversal request capability (PRD §F11.3).
    # Granted to manufacturing-kind industries (manufacturing / mfg+service /
    # mfg+service+other). Service-only tenants do NOT have inventory ledger
    # so the reversal entrypoint is denied at the capability gate (PRISM).
    # Wired through `m11_close` module authority (M11) for AD-22 reversal
    # sequence + AD-25 cache invalidation publisher.
    REVERSAL_REQUEST = "reversal_request"
    # Story 11.2 (Epic 11) — 4-stage close sequence lock capability
    # (PRD §F11.1 + §8.M11(a)). Granted to manufacturing-kind
    # industries (manufacturing / mfg+service / mfg+service+other).
    # Service-only tenants do NOT have a close sequence (no inventory
    # ledger → no fiscal_periods row to lock down).
    CLOSE_SEQUENCE_LOCK = "close_sequence_lock"
    # Story 11.3 (Epic 11) — Snapshot persistence capability (PRD §F11.2 +
    # AD-20 state machine). Gates the POST /close/snapshots/commit +
    # GET /close/snapshots/{period_key} routes. Granted to manufacturing-
    # kind industries; service-only tenants have no fiscal_period_snapshots.
    SNAPSHOT_PERSISTENCE = "snapshot_persistence"
    # Story 11.3 (Epic 11) — Reversal execute capability (PRD §F11.3 +
    # AD-22 reversal 영구화). Gates the POST /close/snapshots/reverse
    # route. Distinct from REVERSAL_REQUEST (which gates AD-22 reversal
    # REQUEST 11-1 wire); this gates the EXECUTE step (3-tier guard
    # against fiscal_period_snapshots.state='committed'). Granted to
    # manufacturing-kind industries.
    REVERSAL_EXECUTE = "reversal_execute"
    # Story 11.3 (Epic 11) — Reopen operator capability (W2 reopen flow).
    # Gates the POST /close/sequence/reopen route. AD-10 owner-only
    # is enforced at the require_role layer; this capability gate is
    # the industry-aware front. Granted to manufacturing-kind industries;
    # service-only tenants do NOT have fiscal_periods to reopen.
    REOPEN_OPERATOR = "reopen_operator"
    # Story 12.2 (Epic 12) — Daily backup export + JSON self-download
    # capability (PRD §F12.2 + §M12-b). Industry-agnostic security baseline
    # (CR 12-1 L4 precedent — 2FA pattern). Granted to all 4 industries
    # because backup is operational infrastructure, not industry-specific.
    # NOT enforced as a route gate (mirrors TWO_FACTOR_AUTH): owner-only
    # via AD-10 `require_role("owner")`. Documented in capability-matrix
    # v1.14 for industry-parity auditability.
    BACKUP_EXPORT = "backup_export"
    # Story 12.1 + 12.4 (Epic 12) — 2FA mandatory gate capability
    # (PRD §F12.1 + §M12-a). Industry-agnostic security baseline — 2FA
    # is operational infrastructure, not industry-specific. Granted to
    # all 4 industries. NOT enforced as a route gate (CR 12-1 L4):
    # 2FA allowlist is owner+member at the `require_any_role` layer.
    # Originally documented in capability-matrix v1.13 (12-1) but the
    # enum entry was missed — 12-2 carry-over fix (drift detector
    # `tests/integration/test_capability_matrix_v1_14_drift.py` surfaces it).
    TWO_FACTOR_AUTH = "two_factor_auth"
    # Story 12.3 (Epic 12) — Account deletion + retention consent
    # capability (PRD §F12.3 + NFR4 2절 5년 audit 보존 + 30일 hard
    # delete + NFR7 2FA 강제). Industry-agnostic security baseline
    # (CR 12-1 L4 precedent — mirrors TWO_FACTOR_AUTH + BACKUP_EXPORT
    # patterns). Granted to all 4 industries because deletion is
    # operational infrastructure (data subject right / GDPR Art.17),
    # not industry-specific. Enforced ONLY on the destructive endpoint
    # POST /account/deletion/request (the 3-layer TOTP defense target).
    # Other endpoints (challenge-token / cancel / status) gate ONLY on
    # `require_role("owner")` per AD-10.
    ACCOUNT_DELETION = "account_deletion"
    # Story 8.1 (Epic 8) — Virtual budget period key + scenario lock
    # capability (PRD §F8.1 + AD-24 period key typed pattern).
    # Industry-agnostic baseline — "budget scenario는 tenant-level 재무
    # baseline" — 모든 industry 동일 적용 (CR 12-1 L4 precedent +
    # 7-1/7-2 industry-agnostic 동일 적용). Granted to all 4 industries
    # because budget scenarios are financial planning infrastructure,
    # not industry-specific. Reused by Story 8-2 (variance table) +
    # Story 8-3 (pre-standard cost preview) — 신규 capability 추가 0건
    # (CR 11-3 즉시 sweep 회피). Documented in capability-matrix v1.17.
    BUDGET_SCENARIO = "budget_scenario"
    # Story 7.1 (Epic 7) — CVP/BEP slider simulation capability
    # (PRD §F7.1 + AD-5 engine purity). Industry-agnostic baseline
    # (CR 12-1 L4 precedent — manufacturing 3종 ✅ + service-only ✅).
    # Granted to all 4 industries because CVP/BEP is financial
    # planning infrastructure, not industry-specific. Used as the
    # capability gate for both POST /simulation/cvp/compute and
    # GET /simulation/cvp/baseline routes. Documented in
    # capability-matrix v1.17.
    CVP_SIMULATION = "cvp_simulation"
    # Story 9.1 (Epic 9) — ABC 100% validation guard capability
    # (PRD §F9.1 + AD-5 engine purity + A19 cohesion pattern 6번째 surface).
    # Industry-agnostic baseline (CR 12-1 L4 precedent — manufacturing 3종 ✅
    # + service-only ✅). Granted to all 4 industries because ABC validation
    # is a precursor guard before CCR allocation (9-2 / 9-3 / 9-4 follow-up).
    # Used as the capability gate for POST /api/v1/abc/{cost-pools,activities,
    # drivers/validate,validate} routes. Documented in capability-matrix v1.18.
    # 9-2 / 9-3 / 9-4 동일 capability 재사용 (CR 11-3 즉시 sweep 회피).
    ABC_CALCULATION = "abc_calculation"
    # Story 14.1 (Epic 14) — Cross-tenant invalidation fan-out capability
    # (PRD §F14.1 + §AD-25 EXTENSION 5+ channels + A53+A57+A58+A59 결정 wire).
    # Industry-agnostic per CR 12-1 L4 precedent (mirrors LISTEN_NOTIFY 13-1
    # wire pattern). All 4 industries can register the cross-tenant fan-out
    # channel listener (PostgreSQL NOTIFY is a tenant-level primitive, not
    # an industry-specific feature). Gates the cross_tenant_fanout channel
    # listener registration for cross-tenant invalidation fan-out
    # (multi-tenant isolation 검증 포함, CR 0-2 RLS lesson 적용).
    # Drift detector: tests/integration/test_capability_matrix_v1_23_drift.py
    # (capability matrix v1.23 EXTENSION 2 NEW rows).
    LISTEN_NOTIFY_TENANT_FANOUT = "listen_notify_tenant_fanout"
    # Story 14.1 (Epic 14) — Multi-process coordination capability
    # (PRD §F14.2 + §AD-25 EXTENSION 5+ channels + A53+A57+A58+A59 결정 wire).
    # Industry-agnostic per CR 12-1 L4 precedent (mirrors LISTEN_NOTIFY 13-1
    # wire pattern). All 4 industries can register the multi-process
    # coordination leader election listener (PostgreSQL advisory lock is a
    # tenant-level primitive, not industry-specific). Gates the
    # multi-process coordination leader election + follower takeover.
    # Drift detector: tests/integration/test_capability_matrix_v1_23_drift.py
    # (capability matrix v1.23 EXTENSION 2 NEW rows).
    LISTEN_NOTIFY_MULTIPROCESS = "listen_notify_multiprocess"
    # Story phase-3.1 (Phase 3 cj-style 2번째 진입점) — Auth Foundation
    # Wire (PRD §F15 + AD-26 + A65+A66+A67+A68+A69 결정 wire).
    # Industry-agnostic per CR 12-1 L4 precedent (mirrors 2FA / backup /
    # deletion / 4-stage close / reversal / LOCK pattern). All 4 industries
    # have the LOGIN + SIGNUP + AUTH_MIDDLEWARE + FORGOT_PASSWORD + LOGOUT
    # surface — authentication is operational infrastructure, not
    # industry-specific. Gates the corresponding auth endpoints. The
    # capability matrix v1.24 (already declared in `docs/capability-matrix.md`
    # during Phase 3 PRD entry) declares the 5 NEW rows; this backend enum
    # is the missing half. Drift detector:
    # tests/integration/test_capability_matrix_v1_24_drift.py.
    LOGIN = "login"
    SIGNUP = "signup"
    AUTH_MIDDLEWARE = "auth_middleware"
    FORGOT_PASSWORD = "forgot_password"
    LOGOUT = "logout"
    # Story phase-4 (Phase 4 cj-style 3번째 진입점) — Deployment territory
    # capability gates (PRD §F16.7 + AD-27 + A73+A74+A76+A77+A78 결정 wire).
    # Industry-agnostic per CR 12-1 L4 precedent (mirrors 2FA / backup /
    # deletion / 4-stage close / reversal / LOCK / auth / LISTEN_NOTIFY
    # pattern). All 4 industries have the DEPLOYMENT_PROD +
    # DEPLOYMENT_STAGING + DEPLOYMENT_DATABASE_BACKUP + DEPLOYMENT_HEALTH_CHECK
    # surface — deployment is operational infrastructure, not
    # industry-specific. Gates the corresponding deployment endpoints.
    # The capability matrix v1.25 (already declared in
    # `docs/capability-matrix.md` during Phase 4 PRD entry) declares the
    # 4 NEW rows; this backend enum is the missing half. Drift detector:
    # tests/integration/test_capability_matrix_v1_25_drift.py.
    DEPLOYMENT_PROD = "deployment_prod"
    DEPLOYMENT_STAGING = "deployment_staging"
    DEPLOYMENT_DATABASE_BACKUP = "deployment_database_backup"
    DEPLOYMENT_HEALTH_CHECK = "deployment_health_check"
    # Story Epic 15 — Magic link + Social OAuth + SSO enterprise SAML
    # capability gates (PRD §F17.5 + AD-28 + A79+A80+A81+A82 결정 wire).
    # Industry-agnostic per CR 12-1 L4 precedent (mirrors 2FA / backup /
    # deletion / 4-stage close / reversal / LOCK / auth / LISTEN_NOTIFY
    # / DEPLOYMENT_* pattern). All 4 industries have the magic link +
    # social OAuth + SSO surface — authentication is operational
    # infrastructure, not industry-specific. Gates the corresponding
    # auth endpoints (POST /api/v1/auth/audit/magic-link-sent, etc.).
    # The capability matrix v1.26 (already declared in
    # `docs/capability-matrix.md` during Epic 15 PRD entry) declares
    # the 5 NEW rows; this backend enum is the missing half. Drift
    # detector: tests/integration/test_capability_matrix_v1_26_drift.py.
    MAGIC_LINK = "magic_link"
    SOCIAL_OAUTH_GOOGLE = "social_oauth_google"
    SOCIAL_OAUTH_NAVER = "social_oauth_naver"
    SOCIAL_OAUTH_KAKAO = "social_oauth_kakao"
    SSO_ENTERPRISE = "sso_enterprise"
    # Story 1st-release (1st release launch wire — cj-style 64번째 진입점) —
    # LAUNCH_LANDING + LAUNCH_TOS + LAUNCH_SUPPORT + LAUNCH_MONITORING
    # (PRD §F18.1~§F18.6 + AD-29 + capability matrix v1.27 EXTENSION 4 NEW
    # rows). Industry-agnostic per CR 12-1 L4 precedent (mirrors
    # MAGIC_LINK / SOCIAL_OAUTH_* / SSO_ENTERPRISE / DEPLOYMENT_* / LOGIN /
    # SIGNUP / AUTH_MIDDLEWARE / FORGOT_PASSWORD / LOGOUT). All 4 industries
    # can access the launch territory (landing page, ToS/Privacy, support
    # channels, production verification, launch communications). Drift
    # detector lives at tests/integration/test_capability_matrix_v1_27_drift.py
    # (capability matrix v1.27 NEW 4 rows).
    LAUNCH_LANDING = "launch_landing"
    LAUNCH_TOS = "launch_tos"
    LAUNCH_SUPPORT = "launch_support"
    LAUNCH_MONITORING = "launch_monitoring"
    # Story Epic 16 (cj-style 69번째 epic 연속 정직 회복 wire) —
    # TENANT_IDP_MANAGEMENT — Tenant IdP admin management territory
    # (alembic 0038 tenant_idps + IdP metadata validator + CRUD API +
    # admin UI + per-tenant SAML routing EXTENSION). Industry-agnostic
    # per CR 12-1 L4 precedent (mirrors SSO_ENTERPRISE / LISTEN_NOTIFY
    # / AUTH_MIDDLEWARE / LAUNCH_* / DEPLOYMENT_* pattern). All 4
    # industries get tenant IdP admin management. Drift detector lives
    # at tests/integration/test_capability_matrix_v1_28_drift.py
    # (capability matrix v1.28 EXTENSION 1 NEW row).
    TENANT_IDP_MANAGEMENT = "tenant_idp_management"
    # Phase 5 (cj-style 75번째 wire) — MULTI_REGION_BACKUP —
    # Cross-region backup territory (alembic 0039 phase_5_replication_lag
    # + phase_5_dr_drill_results + failover_orchestrator + dr_drill +
    # multi-region health observability). Industry-agnostic per CR 12-1
    # L4 precedent (mirrors DEPLOYMENT_DATABASE_BACKUP pattern). All 4
    # industries get multi-region backup capability.
    MULTI_REGION_BACKUP = "multi_region_backup"
    # Phase 5 (cj-style 75번째 wire) — MULTI_REGION_FAILOVER —
    # Cross-region failover trigger capability (POST /api/v1/admin/
    # failover owner-only). Industry-agnostic per CR 12-1 L4 precedent.
    # All 4 industries get multi-region failover capability. Drift
    # detector lives at tests/integration/test_capability_matrix_v1_29
    # _drift.py (capability matrix v1.29 EXTENSION 2 NEW rows).
    MULTI_REGION_FAILOVER = "multi_region_failover"
    # Epic 17 (cj-style 82번째 epic 연속 정직 회복 wire) — AUDIT_LOG_VIEW —
    # Audit log viewer + activity stream territory (PRD §F21 + AD-32
    # (a)~(g) sub-decisions). Industry-agnostic per CR 12-1 L4 precedent
    # (mirrors MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER Phase 5 wire
    # pattern + TENANT_IDP_MANAGEMENT Epic 16 wire + SSO_ENTERPRISE
    # Epic 15 wire + LISTEN_NOTIFY 13/14 wire + AUTH_MIDDLEWARE Phase 3
    # wire + LAUNCH_* 1st release wire + DEPLOYMENT_* Phase 4 wire
    # pattern verbatim). All 4 industries get AUDIT_LOG_VIEW capability
    # (audit log viewer is operational infrastructure / observability,
    # not industry-specific). Gates the audit log viewer routes
    # (audit_log list / count / entry lookup / CSV export).
    # (Note: the activity route is intentionally NOT gated — the
    # activity stream is broad, all tenant members allowed, PRD §F21.3
    # verbatim.) Drift detector lives at
    # tests/integration/test_capability_matrix_v1_30_drift.py (capability
    # matrix v1.30 EXTENSION 1 NEW row).
    AUDIT_LOG_VIEW = "audit_log_view"
    # Phase 6 (cj-style 87번째 epic 연속 정직 회복 wire) — AUDIT_LOG_RETENTION
    # — Audit Log Retention Policy territory (PRD §F22 + AD-33 (a)~(g)
    # sub-decisions). Industry-agnostic per CR 12-1 L4 precedent (mirrors
    # MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER Phase 5 wire +
    # AUDIT_LOG_VIEW Epic 17 wire + TENANT_IDP_MANAGEMENT Epic 16 wire +
    # SSO_ENTERPRISE Epic 15 wire + LISTEN_NOTIFY 13/14 wire +
    # AUTH_MIDDLEWARE Phase 3 wire + LAUNCH_* 1st release wire +
    # DEPLOYMENT_* Phase 4 wire pattern verbatim). All 4 industries get
    # AUDIT_LOG_RETENTION capability (audit log retention is operational
    # infrastructure / compliance baseline, not industry-specific). Gates
    # the retention policy DSL + automatic purge job + archive storage +
    # GDPR Article 17 erasure routes
    # (apps/api/modules/audit/retention/retention_routes.py +
    # erasure.py). Drift detector lives at
    # tests/integration/test_capability_matrix_v1_31_drift.py
    # (capability matrix v1.31 EXTENSION 1 NEW row).
    AUDIT_LOG_RETENTION = "audit_log_retention"
    # Phase 7 (cj-style 91번째 wire) — OBSERVABILITY_TRACES — Observability
    # Stack 강화 territory (PRD §F23.1 + §F23.6 + AD-34 (f) sub-decisions).
    # Industry-agnostic per CR 12-1 L4 precedent (mirrors MULTI_REGION_BACKUP
    # + MULTI_REGION_FAILOVER Phase 5 wire + AUDIT_LOG_VIEW Epic 17 wire +
    # AUDIT_LOG_RETENTION Phase 6 wire + TENANT_IDP_MANAGEMENT Epic 16 wire
    # + SSO_ENTERPRISE Epic 15 wire + LISTEN_NOTIFY 13/14 wire +
    # AUTH_MIDDLEWARE Phase 3 wire + LAUNCH_* 1st release wire +
    # DEPLOYMENT_* Phase 4 wire pattern verbatim). All 4 industries get
    # OBSERVABILITY_TRACES capability (OpenTelemetry distributed tracing is
    # operational observability baseline, not industry-specific). Gates the
    # trace_id lookup + alert ack + PagerDuty manual trigger routes
    # (apps/api/core/tracing.py + apps/api/modules/observability/alerting.py
    # routes). Drift detector lives at
    # tests/integration/test_capability_matrix_v1_32_drift.py
    # (capability matrix v1.32 EXTENSION 1 NEW row).
    OBSERVABILITY_TRACES = "observability_traces"
    # Phase 7 (cj-style 91번째 wire) — OBSERVABILITY_METRICS — Observability
    # Stack 강화 territory (PRD §F23.2 + §F23.6 + AD-34 (f) sub-decisions).
    # Industry-agnostic per CR 12-1 L4 precedent (mirrors OBSERVABILITY_TRACES
    # Phase 7 wire + MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER Phase 5 wire
    # + AUDIT_LOG_VIEW Epic 17 wire + AUDIT_LOG_RETENTION Phase 6 wire +
    # TENANT_IDP_MANAGEMENT Epic 16 wire + SSO_ENTERPRISE Epic 15 wire +
    # LISTEN_NOTIFY 13/14 wire + AUTH_MIDDLEWARE Phase 3 wire + LAUNCH_*
    # 1st release wire + DEPLOYMENT_* Phase 4 wire pattern verbatim). All
    # 4 industries get OBSERVABILITY_METRICS capability (Prometheus custom
    # metrics + Grafana dashboards are operational observability baseline,
    # not industry-specific). Gates the /metrics endpoint + Grafana dashboard
    # embed routes (apps/api/core/metrics.py + alerting routes). Drift
    # detector lives at tests/integration/test_capability_matrix_v1_32_drift.py
    # (capability matrix v1.32 EXTENSION 1 NEW row).
    OBSERVABILITY_METRICS = "observability_metrics"
    # Phase 8 (cj-style 95번째 wire) — PERFORMANCE_TESTING — Performance/
    # Load Testing territory (PRD §F24 + AD-35 (a)~(g) sub-decisions).
    # Industry-agnostic per CR 12-1 L4 precedent (mirrors OBSERVABILITY_TRACES
    # + OBSERVABILITY_METRICS Phase 7 wire + AUDIT_LOG_RETENTION Phase 6 wire
    # + AUDIT_LOG_VIEW Epic 17 wire + MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER
    # Phase 5 wire + TENANT_IDP_MANAGEMENT Epic 16 wire + SSO_ENTERPRISE
    # Epic 15 wire + LISTEN_NOTIFY 13/14 wire + AUTH_MIDDLEWARE Phase 3
    # wire + LAUNCH_* 1st release wire + DEPLOYMENT_* Phase 4 wire pattern
    # verbatim). All 4 industries get PERFORMANCE_TESTING capability
    # (k6 load testing + SLO/SLI definitions + p99 latency budget +
    # latency regression detector + performance regression gate CI +
    # cost-engine benchmark V8 golden fixture are operational performance
    # / observability baseline, not industry-specific). Gates the
    # manual k6 load test trigger + SLO dashboard view + latency
    # regression dashboard + cost-engine benchmark invalidate routes
    # (apps/api/core/load_test_runner.py + apps/api/core/latency_budget.py
    # + apps/api/modules/performance_testing routes). Drift detector
    # lives at tests/integration/test_capability_matrix_v1_33_drift.py
    # (capability matrix v1.33 EXTENSION 1 NEW row).
    PERFORMANCE_TESTING = "performance_testing"
    # Phase 9 (cj-style 99번째 wire) — CHAOS_ENGINEERING — Chaos
    # Engineering / Game Day territory (PRD §F25 + AD-36 (a)~(g)
    # sub-decisions). Industry-agnostic per CR 12-1 L4 precedent
    # (mirrors PERFORMANCE_TESTING Phase 8 wire + OBSERVABILITY_*
    # Phase 7 wire + AUDIT_LOG_RETENTION Phase 6 wire + AUDIT_LOG_VIEW
    # Epic 17 wire + MULTI_REGION_BACKUP/FAILOVER Phase 5 wire +
    # TENANT_IDP_MANAGEMENT Epic 16 wire + SSO_ENTERPRISE Epic 15 wire
    # + LISTEN_NOTIFY 13/14 wire + AUTH_MIDDLEWARE Phase 3 wire +
    # LAUNCH_* 1st release wire + DEPLOYMENT_* Phase 4 wire pattern
    # verbatim). All 4 industries get CHAOS_ENGINEERING capability
    # (chaos engineering is operational resilience / observability
    # baseline, not industry-specific). Gates the chaos experiment
    # routes (manual k6 + manual abort + auto-rollback + continuous
    # chaos + chaos_game_day + tenant-scoped + multi-region chaos
    # routes). Drift detector lives at
    # tests/integration/test_capability_matrix_v1_34_drift.py
    # (capability matrix v1.34 EXTENSION 1 NEW row).
    CHAOS_ENGINEERING = "chaos_engineering"
    # Phase 10 (cj-style 103번째 wire) — SLO_ENGINEERING — SLO Engineering /
    # Error Budget Management territory (PRD §F26 + AD-37 (a)~(g)
    # sub-decisions). Industry-agnostic per CR 12-1 L4 precedent (mirrors
    # CHAOS_ENGINEERING Phase 9 wire + PERFORMANCE_TESTING Phase 8 wire +
    # OBSERVABILITY_* Phase 7 wire + AUDIT_LOG_RETENTION Phase 6 wire +
    # AUDIT_LOG_VIEW Epic 17 wire + MULTI_REGION_BACKUP/FAILOVER Phase 5
    # wire pattern verbatim). All 4 industries get SLO_ENGINEERING
    # capability (SLO engineering is operational resilience / observability
    # baseline, not industry-specific). Gates the SLO routes (manual SLO
    # create/update/delete + multi-region aggregation + tenant-scoped
    # override + error budget freeze/unfreeze + governance review + SLO
    # breach auto-rollback trigger + dry-run mode). Drift detector lives
    # at tests/integration/test_capability_matrix_v1_35_drift.py
    # (capability matrix v1.35 EXTENSION 1 NEW row).
    SLO_ENGINEERING = "slo_engineering"
    # Phase 11 (cj-style 107번째 wire) — FINOPS_SHOWBACK — FinOps Showback
    # / Chargeback territory (PRD §F27 + AD-38 (a)~(g) sub-decisions).
    # Industry-agnostic per CR 12-1 L4 precedent (mirrors SLO_ENGINEERING
    # Phase 10 wire + CHAOS_ENGINEERING Phase 9 wire + PERFORMANCE_TESTING
    # Phase 8 wire + OBSERVABILITY_* Phase 7 wire + AUDIT_LOG_RETENTION
    # Phase 6 wire + AUDIT_LOG_VIEW Epic 17 wire +
    # MULTI_REGION_BACKUP/FAILOVER Phase 5 wire pattern verbatim). All 4
    # industries get FINOPS_SHOWBACK + FINOPS_CHARGEBACK capabilities
    # (FinOps is financial reporting baseline, not industry-specific).
    # Gates the FinOps routes in apps/api/modules/finops/ (showback
    # generation + department mapping update + chargeback calculation +
    # CSV/PDF export + dry-run mode). Drift detector lives at
    # tests/integration/test_capability_matrix_v1_36_drift.py
    # (capability matrix v1.36 EXTENSION 2 NEW rows).
    FINOPS_SHOWBACK = "finops_showback"
    FINOPS_CHARGEBACK = "finops_chargeback"
    # Phase 12 (cj-style 111번째 wire) — FINOPS_ANOMALY_DETECTION —
    # Cost Anomaly Detection & Budget Alerting territory (PRD §F28 +
    # AD-39 (a)~(g) sub-decisions). Industry-agnostic per CR 12-1 L4
    # precedent (mirrors FINOPS_SHOWBACK + FINOPS_CHARGEBACK Phase 11
    # wire + SLO_ENGINEERING Phase 10 wire + CHAOS_ENGINEERING Phase 9
    # wire + PERFORMANCE_TESTING Phase 8 wire + OBSERVABILITY_* Phase 7
    # wire + AUDIT_LOG_RETENTION Phase 6 wire + AUDIT_LOG_VIEW Epic 17
    # wire + MULTI_REGION_BACKUP/FAILOVER Phase 5 wire pattern verbatim).
    # All 4 industries get FINOPS_ANOMALY_DETECTION capability (anomaly
    # detection is financial observability baseline, not
    # industry-specific). Gates the anomaly detection routes
    # (apps/api/modules/finops/anomaly_detection.py +
    # anomaly_detection_engine.py + forecast_accuracy.py). Drift
    # detector lives at
    # tests/integration/test_capability_matrix_v1_37_drift.py
    # (capability matrix v1.37 EXTENSION 2 NEW rows).
    FINOPS_ANOMALY_DETECTION = "finops_anomaly_detection"
    # Phase 12 (cj-style 111번째 wire) — FINOPS_BUDGET_ALERT — Cost
    # Anomaly Detection & Budget Alerting territory (PRD §F28.4 +
    # AD-39 (a)~(g) sub-decisions). Industry-agnostic per CR 12-1 L4
    # precedent (mirrors FINOPS_ANOMALY_DETECTION Phase 12 wire +
    # FINOPS_SHOWBACK + FINOPS_CHARGEBACK Phase 11 wire pattern verbatim).
    # All 4 industries get FINOPS_BUDGET_ALERT capability (budget
    # alerting is financial observability baseline, not industry-specific).
    # Gates the budget definition + budget alert routing routes
    # (apps/api/modules/finops/budget_definition.py + budget_alert.py).
    # Drift detector lives at
    # tests/integration/test_capability_matrix_v1_37_drift.py
    # (capability matrix v1.37 EXTENSION 2 NEW rows).
    FINOPS_BUDGET_ALERT = "finops_budget_alert"
    # Phase 13 (cj-style 115번째 wire) — FINOPS_FORECASTING_CAPACITY_PLANNING
    # — Cost Forecasting & Capacity Planning territory (PRD §F29.6 +
    # AD-39 (a)~(g) sub-decisions). Industry-agnostic per CR 12-1 L4
    # precedent (mirrors FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT
    # Phase 12 wire + FINOPS_SHOWBACK + FINOPS_CHARGEBACK Phase 11 wire
    # pattern verbatim). All 4 industries get
    # FINOPS_FORECASTING_CAPACITY_PLANNING capability (financial
    # forecasting baseline, not industry-specific). Gates the forecast
    # definition + forecast generation + capacity headroom + budget
    # burn-rate + forecast accuracy + model retraining routes
    # (apps/api/modules/finops/forecast_definition.py +
    # forecast_engine.py + forecast_model_registry.py +
    # capacity_headroom.py + budget_burnrate.py +
    # forecast_accuracy_tracker.py). Drift detector lives at
    # tests/integration/test_capability_matrix_v1_39_drift.py
    # (capability matrix v1.39 EXTENSION 1 NEW row).
    FINOPS_FORECASTING_CAPACITY_PLANNING = "finops_forecasting_capacity_planning"

    # Phase 14 (cj-style 119번째 wire) — FINOPS_OPTIMIZATION
    # (optimization_definition + rightsizing_engine +
    # idle_resource_detector + commitment_recommender +
    # optimization_accuracy_tracker). Industry-agnostic (CR 12-1 L4
    # precedent mirrors FINOPS_FORECASTING_CAPACITY_PLANNING Phase 13 +
    # FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12 + FINOPS
    # Phase 11 pattern verbatim). All 4 industries get
    # FINOPS_OPTIMIZATION capability (manufacturing + service +
    # manufacturing_service + manufacturing_service_other).
    # Gates require_finops_optimization dep in
    # apps/api/dependencies/capability.py. Drift detector lives at
    # tests/integration/test_capability_matrix_v1_40_drift.py
    # (capability matrix v1.40 EXTENSION 1 NEW row).
    FINOPS_OPTIMIZATION = "finops_optimization"

    # Phase 15 (cj-style 123번째 wire) — FINOPS_TAG_GOVERNANCE
    # (tag_policy_dsl + untagged_resource_detector +
    # allocation_rules_engine + allocation_audit +
    # chargeback_allocation_reconciliation + reconciliation approval
    # workflow). Industry-agnostic (CR 12-1 L4 precedent mirrors
    # FINOPS_OPTIMIZATION Phase 14 + FINOPS_FORECASTING_CAPACITY_PLANNING
    # Phase 13 + FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12 +
    # FINOPS Phase 11 pattern verbatim). All 4 industries get
    # FINOPS_TAG_GOVERNANCE capability (financial cost allocation
    # baseline, not industry-specific). Gates require_finops_tag_governance
    # dep in apps/api/dependencies/capability.py. Drift detector lives at
    # tests/integration/test_capability_matrix_v1_41_drift.py (capability
    # matrix v1.41 EXTENSION 1 NEW row).
    FINOPS_TAG_GOVERNANCE = "finops_tag_governance"

    # Phase 16 (cj-style 127번째 wire) — FINOPS_REPORTING
    # (executive_dashboard_aggregator + cross_module_kpi_selector +
    # executive_report_generator + scheduled_executive_dispatch +
    # executive role RBAC). Industry-agnostic per CR 12-1 L4 precedent
    # (mirrors FINOPS_TAG_GOVERNANCE Phase 15 + FINOPS_OPTIMIZATION
    # Phase 14 + FINOPS_FORECASTING_CAPACITY_PLANNING Phase 13 +
    # FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12 +
    # FINOPS Phase 11 pattern verbatim). All 4 industries get
    # FINOPS_REPORTING capability (executive reporting is a
    # business-level concern, not industry-specific). Gates
    # require_finops_reporting dep in
    # apps/api/dependencies/capability.py. Drift detector lives at
    # tests/integration/test_capability_matrix_v1_42_drift.py (capability
    # matrix v1.42 EXTENSION 1 NEW row).
    FINOPS_REPORTING = "finops_reporting"

    # Phase 17 (cj-style 131번째 wire) — FINOPS_SUSTAINABILITY
    # (carbon_emissions_aggregator + sustainability_kpi_selector +
    # sustainability_report_generator + scheduled_sustainability_dispatch +
    # sustainability role RBAC). Industry-agnostic per CR 12-1 L4 precedent
    # (mirrors FINOPS_REPORTING Phase 16 + FINOPS_TAG_GOVERNANCE Phase 15 +
    # FINOPS_OPTIMIZATION Phase 14 + FINOPS_FORECASTING_CAPACITY_PLANNING
    # Phase 13 + FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12 +
    # FINOPS Phase 11 pattern verbatim). All 4 industries get
    # FINOPS_SUSTAINABILITY capability (sustainability & carbon reporting
    # is a business-level regulatory concern per EU CSRD + SEC Climate
    # Disclosure + EU Taxonomy + IFRS S2 + 한국 KSSB, not industry-specific).
    # Gates require_finops_sustainability dep in
    # apps/api/dependencies/capability.py. Drift detector lives at
    # tests/integration/test_capability_matrix_v1_43_drift.py (capability
    # matrix v1.43 EXTENSION 1 NEW row).
    FINOPS_SUSTAINABILITY = "finops_sustainability"
    # Phase 18 (cj-style 135번째 wire) — FINOPS_COMMITMENT — Cloud
    # commitment management (RIs/SPs/CUDs) for AWS + Azure + GCP +
    # Naver Cloud + KT Cloud. Industry-agnostic per FinOps Foundation
    # + AWS Cost Optimization Pillar + Azure Cost Optimization + GCP
    # Cost Optimization + 한국 조달청 클라우드 commitment 가이드라인
    # (CR 12-1 L4 precedent mirrors FINOPS_SUSTAINABILITY Phase 17 wire +
    # FINOPS_REPORTING Phase 16 wire + FINOPS_TAG_GOVERNANCE Phase 15 wire
    # + FINOPS_OPTIMIZATION Phase 14 wire + FINOPS_FORECASTING_CAPACITY_PLANNING
    # Phase 13 wire + FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12 wire
    # + FINOPS Phase 11 wire pattern verbatim). All 4 industries get
    # FINOPS_COMMITMENT capability (cloud commitment management is a
    # business-level financial concern per FinOps Foundation + cloud
    # provider cost optimization pillars, not industry-specific).
    # Gates require_finops_commitment dep in
    # apps/api/dependencies/capability.py. Drift detector lives at
    # tests/integration/test_capability_matrix_v1_44_drift.py (capability
    # matrix v1.44 EXTENSION 1 NEW row).
    FINOPS_COMMITMENT = "finops_commitment"
    # Phase 19 (cj-style 139번째 wire) — FINOPS_PRICING — Pricing, Rate
    # Card & TCO Modeling for AWS + Azure + GCP + Naver Cloud + KT Cloud.
    # Industry-agnostic per FinOps Foundation + AWS Pricing Models EDP +
    # Azure Pricing Calculator EA + GCP Pricing Calculator CUD + 한국
    # 공공 조달 가격 가이드라인 (CR 12-1 L4 precedent mirrors
    # FINOPS_COMMITMENT Phase 18 wire + FINOPS_SUSTAINABILITY Phase 17
    # wire + FINOPS_REPORTING Phase 16 wire + FINOPS_TAG_GOVERNANCE
    # Phase 15 wire + FINOPS_OPTIMIZATION Phase 14 wire +
    # FINOPS_FORECASTING_CAPACITY_PLANNING Phase 13 wire +
    # FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12 wire +
    # FINOPS Phase 11 wire pattern verbatim). All 4 industries get
    # FINOPS_PRICING capability (pricing & TCO modeling is a
    # business-level financial concern per FinOps Foundation + cloud
    # provider pricing models + 한국 공공 조달 가격 가이드라인, not
    # industry-specific). Gates require_finops_pricing dep in
    # apps/api/dependencies/capability.py. Drift detector lives at
    # tests/integration/test_capability_matrix_v1_45_drift.py (capability
    # matrix v1.45 EXTENSION 1 NEW row).
    FINOPS_PRICING = "finops_pricing"
    # Phase 20 (cj-style 144번째 wire) — FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION
    # — FinOps Multi-Cloud Cost Unified Reconciliation for 5 cloud providers
    # (AWS EDP + Azure EA + GCP CUD Pricing + Naver Cloud Volume Tier + KT
    # Cloud Volume Tier) + 5 marketplace (AWS + Azure + GCP + Naver + KT).
    # Industry-agnostic per FinOps Foundation Multi-Cloud Cost Management
    # pillar (CR 12-1 L4 precedent mirrors FINOPS_PRICING Phase 19 wire +
    # FINOPS_COMMITMENT Phase 18 wire + FINOPS_SUSTAINABILITY Phase 17 wire
    # + FINOPS_REPORTING Phase 16 wire + FINOPS_TAG_GOVERNANCE Phase 15
    # wire + FINOPS_OPTIMIZATION Phase 14 wire +
    # FINOPS_FORECASTING_CAPACITY_PLANNING Phase 13 wire + Phase 12 wire +
    # Phase 11 wire pattern verbatim). All 4 industries get
    # FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION capability (multi-cloud
    # cost unified reconciliation is a business-level FinOps pillar per
    # FinOps Foundation + 5 cloud provider cross-rollup pattern, not
    # industry-specific). Gates require_finops_multi_cloud dep in
    # apps/api/dependencies/capability.py. Drift detector lives at
    # tests/integration/test_capability_matrix_v1_46_drift.py (capability
    # matrix v1.46 EXTENSION 1 NEW row).
    FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION = "finops_multi_cloud_unified_reconciliation"
    # Phase 21 (cj-style 151번째 wire) — FINOPS_RESERVED_CAPACITY_PLANNING
    # — FinOps Reserved Capacity Planning for 5-module composition layer
    # (Phase 13 forecast + Phase 14 optimization + Phase 18 commitment +
    # Phase 19 pricing + Phase 20 multi_cloud weighted average → single
    # demand_forecast_id + capacity_plan_id + commitment_recommendation_id
    # + orchestration_id + 4 cadence schedule KST pytz + 6 reserved_capacity_tier
    # + 4 execution_strategy). Industry-agnostic per FinOps Foundation
    # Reserved Capacity Planning pillar (CR 12-1 L4 precedent mirrors
    # FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION Phase 20 wire +
    # FINOPS_PRICING Phase 19 wire + FINOPS_COMMITMENT Phase 18 wire +
    # FINOPS_SUSTAINABILITY Phase 17 wire + FINOPS_REPORTING Phase 16 wire
    # + FINOPS_TAG_GOVERNANCE Phase 15 wire + FINOPS_OPTIMIZATION Phase 14
    # wire + FINOPS_FORECASTING_CAPACITY_PLANNING Phase 13 wire + Phase 12
    # wire + Phase 11 wire pattern verbatim). All 4 industries get
    # FINOPS_RESERVED_CAPACITY_PLANNING capability (reserved capacity
    # planning is a business-level FinOps pillar per FinOps Foundation +
    # 5-module composition layer pattern, not industry-specific). Gates
    # require_finops_reserved_capacity dep in
    # apps/api/dependencies/capability.py. Drift detector lives at
    # tests/integration/test_capability_matrix_v1_47_drift.py (capability
    # matrix v1.47 EXTENSION 1 NEW row).
    FINOPS_RESERVED_CAPACITY_PLANNING = "finops_reserved_capacity_planning"


# ── Industry → Capability map (F-41-resolved) ────────────────
# Mirrors the visibility rules in `packages/services/m0_onboarding/industry_menu.py`.
_INDUSTRY_CAPABILITIES: Final[dict[Industry, frozenset[Capability]]] = {
    Industry.MANUFACTURING: frozenset(
        {
            Capability.BOM,
            Capability.OPENING_INVENTORY,
            Capability.INVENTORY_LEDGER,
            # Story 5.3 — manufacturing tenants get closing-guard gate
            # (PRD §F4.2 + §V3).
            Capability.INVENTORY_CLOSING_GUARD,
            Capability.AI_EXTRACT,  # Story 1.3 — all industries can use AI extraction
            # Story 10.1 (Epic 10) — manufacturing tenants get AI_INSIGHT
            # (industry-agnostic, validation guard CR 12-1 L4 + 7-1/7-2/8-1
            # /8-2/8-3 precedent). Gates POST /api/v1/ai/extract-monthly.
            Capability.AI_INSIGHT,
            # Story 13.1 (Epic 13) — manufacturing tenants get LISTEN_NOTIFY
            # (industry-agnostic, validation guard CR 12-1 L4 + AI_INSIGHT
            # 10-1 wire pattern). Gates the LISTEN daemon registration for
            # AD-25 cache invalidation consume trigger EXTENSION.
            Capability.LISTEN_NOTIFY,
            # Story 2.1 — manufacturing tenants can register all 5 product types.
            Capability.PRODUCT,
            Capability.PRODUCT_MATERIAL,
            # Story 3.1 — manufacturing tenants get the [생산] tab.
            Capability.MONTHLY_INPUT_PRODUCTION,
            # Story 4.1 — manufacturing tenants can run §6.1 원가 계산.
            Capability.COST_CALCULATION,
            # Story 6.1 — manufacturing tenants get Monthly Closing Report.
            Capability.MONTHLY_CLOSING_REPORT,
            # Story 11.1 — manufacturing tenants get REVERSAL_REQUEST
            # (PRD §F11.3 — AD-22 reversal sequence + AD-25 publisher).
            Capability.REVERSAL_REQUEST,
            # Story 11.2 — manufacturing tenants get the 4-stage
            # close sequence lock (PRD §F11.1 + §8.M11(a)).
            Capability.CLOSE_SEQUENCE_LOCK,
            # Story 11.3 — manufacturing tenants get SNAPSHOT_PERSISTENCE
            # (AD-20 state machine), REVERSAL_EXECUTE (AD-22 영구화),
            # and REOPEN_OPERATOR (W2 reopen flow).
            Capability.SNAPSHOT_PERSISTENCE,
            Capability.REVERSAL_EXECUTE,
            Capability.REOPEN_OPERATOR,
            # Story 12.2 — manufacturing tenants get BACKUP_EXPORT
            # (industry-agnostic, security baseline CR 12-1 L4).
            Capability.BACKUP_EXPORT,
            # Story 12.1 — manufacturing tenants get TWO_FACTOR_AUTH
            # (industry-agnostic, security baseline CR 12-1 L4).
            Capability.TWO_FACTOR_AUTH,
            # Story 12.3 — manufacturing tenants get ACCOUNT_DELETION
            # (industry-agnostic, security baseline CR 12-1 L4).
            Capability.ACCOUNT_DELETION,
            # Story 8.1 — manufacturing tenants get BUDGET_SCENARIO
            # (industry-agnostic, financial baseline CR 12-1 L4 +
            # 7-1/7-2 L4 precedent — all industries grant).
            Capability.BUDGET_SCENARIO,
            # Story 7.1 — manufacturing tenants get CVP_SIMULATION
            # (industry-agnostic, financial baseline CR 12-1 L4).
            Capability.CVP_SIMULATION,
            # Story 9.1 — manufacturing tenants get ABC_CALCULATION
            # (industry-agnostic, validation guard CR 12-1 L4 + 7-1/7-2/8-1/8-2/8-3 precedent).
            Capability.ABC_CALCULATION,
            # Story 14.1 (Epic 14) — manufacturing tenants get
            # LISTEN_NOTIFY_TENANT_FANOUT + LISTEN_NOTIFY_MULTIPROCESS
            # (industry-agnostic, validation guard CR 12-1 L4 +
            # LISTEN_NOTIFY 13-1 wire pattern).
            Capability.LISTEN_NOTIFY_TENANT_FANOUT,
            Capability.LISTEN_NOTIFY_MULTIPROCESS,
            # Story phase-3.1 — manufacturing tenants get LOGIN + SIGNUP +
            # AUTH_MIDDLEWARE + FORGOT_PASSWORD + LOGOUT (industry-agnostic,
            # security baseline CR 12-1 L4 + 2FA / deletion / backup pattern).
            Capability.LOGIN,
            Capability.SIGNUP,
            Capability.AUTH_MIDDLEWARE,
            Capability.FORGOT_PASSWORD,
            Capability.LOGOUT,
            # Story phase-4 — manufacturing tenants get DEPLOYMENT_PROD +
            # DEPLOYMENT_STAGING + DEPLOYMENT_DATABASE_BACKUP +
            # DEPLOYMENT_HEALTH_CHECK (industry-agnostic, operational
            # infrastructure CR 12-1 L4 + LISTEN_NOTIFY 13-1/14-1 wire
            # pattern). All 4 industries get deployment capability.
            Capability.DEPLOYMENT_PROD,
            Capability.DEPLOYMENT_STAGING,
            Capability.DEPLOYMENT_DATABASE_BACKUP,
            Capability.DEPLOYMENT_HEALTH_CHECK,
            # Story Epic 15 — manufacturing tenants get MAGIC_LINK +
            # SOCIAL_OAUTH_GOOGLE + SOCIAL_OAUTH_NAVER +
            # SOCIAL_OAUTH_KAKAO + SSO_ENTERPRISE (industry-agnostic,
            # auth surface EXTENSION, CR 12-1 L4 precedent +
            # DEPLOYMENT_* 4-1 wire pattern).
            Capability.MAGIC_LINK,
            Capability.SOCIAL_OAUTH_GOOGLE,
            Capability.SOCIAL_OAUTH_NAVER,
            Capability.SOCIAL_OAUTH_KAKAO,
            Capability.SSO_ENTERPRISE,
            # Story 1st-release (cj-style 64번째) — manufacturing tenants get
            # LAUNCH_LANDING + LAUNCH_TOS + LAUNCH_SUPPORT +
            # LAUNCH_MONITORING (industry-agnostic, CR 12-1 L4 precedent).
            Capability.LAUNCH_LANDING,
            Capability.LAUNCH_TOS,
            Capability.LAUNCH_SUPPORT,
            Capability.LAUNCH_MONITORING,
            # Epic 16 (cj-style 69번째) — manufacturing tenants get
            # TENANT_IDP_MANAGEMENT (industry-agnostic, CR 12-1 L4 precedent).
            Capability.TENANT_IDP_MANAGEMENT,
            # Phase 5 (cj-style 75번째 wire) — manufacturing tenants get
            # MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER
            # (industry-agnostic, CR 12-1 L4 precedent + DEPLOYMENT_*
            # Phase 4 v1.25 pattern verbatim).
            Capability.MULTI_REGION_BACKUP,
            Capability.MULTI_REGION_FAILOVER,
            # Epic 17 (cj-style 82번째 wire) — manufacturing tenants get
            # AUDIT_LOG_VIEW (industry-agnostic, observability baseline
            # CR 12-1 L4 precedent + MULTI_REGION_BACKUP +
            # MULTI_REGION_FAILOVER Phase 5 wire pattern verbatim).
            Capability.AUDIT_LOG_VIEW,
            # Phase 6 (cj-style 87번째 wire) — manufacturing/service/겸영/겸영+기타
            # tenants get AUDIT_LOG_RETENTION (industry-agnostic, compliance
            # baseline CR 12-1 L4 precedent + AUDIT_LOG_VIEW Epic 17 wire +
            # MULTI_REGION_BACKUP/FAILOVER Phase 5 wire pattern verbatim).
            Capability.AUDIT_LOG_RETENTION,
            # Phase 7 (cj-style 91번째 wire) — tenants get
            # OBSERVABILITY_TRACES + OBSERVABILITY_METRICS
            # (industry-agnostic, observability baseline CR 12-1 L4 precedent
            # + AUDIT_LOG_RETENTION Phase 6 wire + AUDIT_LOG_VIEW Epic 17
            # wire + MULTI_REGION_BACKUP/FAILOVER Phase 5 wire pattern
            # verbatim). All 4 industries get both observability
            # capabilities (OpenTelemetry distributed tracing + Prometheus
            # custom metrics + Grafana dashboards are operational baseline).
            Capability.OBSERVABILITY_TRACES,
            Capability.OBSERVABILITY_METRICS,
            # Phase 8 (cj-style 95번째 wire) — manufacturing tenants get
            # PERFORMANCE_TESTING (industry-agnostic, performance /
            # observability baseline CR 12-1 L4 precedent + OBSERVABILITY_*
            # Phase 7 wire pattern verbatim).
            Capability.PERFORMANCE_TESTING,
            # Phase 9 (cj-style 99번째 wire) — manufacturing tenants get
            # CHAOS_ENGINEERING (industry-agnostic, chaos engineering
            # baseline CR 12-1 L4 precedent + PERFORMANCE_TESTING Phase 8
            # wire + OBSERVABILITY_* Phase 7 wire pattern verbatim).
            Capability.CHAOS_ENGINEERING,
            # Phase 10 (cj-style 103번째 wire) — all industries get
            # SLO_ENGINEERING (industry-agnostic, SLO engineering baseline
            # CR 12-1 L4 precedent + CHAOS_ENGINEERING Phase 9 wire +
            # PERFORMANCE_TESTING Phase 8 wire + OBSERVABILITY_* Phase 7
            # wire pattern verbatim).
            Capability.SLO_ENGINEERING,
            # Phase 11 (cj-style 107번째 wire) — manufacturing tenants
            # get FINOPS_SHOWBACK + FINOPS_CHARGEBACK (industry-agnostic,
            # FinOps financial reporting baseline CR 12-1 L4 precedent +
            # SLO_ENGINEERING Phase 10 wire + CHAOS_ENGINEERING Phase 9
            # wire + PERFORMANCE_TESTING Phase 8 wire + OBSERVABILITY_*
            # Phase 7 wire pattern verbatim).
            Capability.FINOPS_SHOWBACK,
            Capability.FINOPS_CHARGEBACK,
            # Phase 12 (cj-style 111번째 wire) — manufacturing tenants
            # get FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT
            # (industry-agnostic, FinOps financial observability baseline
            # CR 12-1 L4 precedent + FINOPS_SHOWBACK + FINOPS_CHARGEBACK
            # Phase 11 wire pattern verbatim).
            Capability.FINOPS_ANOMALY_DETECTION,
            Capability.FINOPS_BUDGET_ALERT,
            # Phase 13 (cj-style 115번째 wire) — manufacturing tenants
            # get FINOPS_FORECASTING_CAPACITY_PLANNING (industry-agnostic,
            # FinOps financial forecasting baseline CR 12-1 L4 precedent +
            # FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12 wire
            # + FINOPS_SHOWBACK + FINOPS_CHARGEBACK Phase 11 wire pattern
            # verbatim). 4-model parallel run (ARIMA + Prophet + LSTM +
            # ensemble) + 90일 lookahead + capacity headroom +
            # budget burn-rate + MAE/MAPE/RMSE banker's rounding CR 5-1
            # + retraining trigger (MAPE > 20% for 3 consecutive periods).
            Capability.FINOPS_FORECASTING_CAPACITY_PLANNING,
            # Phase 14 (cj-style 119번째 wire) — manufacturing tenants
            # get FINOPS_OPTIMIZATION (industry-agnostic, FinOps
            # ACTIONABLE RECOMMENDATION LAYER EXTENSION of Phase 13
            # forecast baseline CR 12-1 L4 precedent + FINOPS_FORECASTING
            # + FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12
            # wire + FINOPS_SHOWBACK + FINOPS_CHARGEBACK Phase 11 wire
            # pattern verbatim). 5 resource types parallel run (compute +
            # storage + database + network + container) + 80+ AWS EC2
            # instance type mapping + z-score < -2.0 idle detection +
            # 6 commitment_type + 1y/3y break-even + precision + recall
            # + realized_savings + accuracy_score retraining trigger.
            Capability.FINOPS_OPTIMIZATION,
            # Phase 15 (cj-style 123번째 wire) — manufacturing tenants
            # get FINOPS_TAG_GOVERNANCE (industry-agnostic, FinOps
            # cost allocation baseline CR 12-1 L4 precedent +
            # FINOPS_OPTIMIZATION Phase 14 wire + FINOPS_FORECASTING
            # + FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12
            # wire + FINOPS Phase 11 wire pattern verbatim).
            # tag_policy_dsl + untagged_resource_detector +
            # allocation_rules_engine + allocation_audit +
            # chargeback_allocation_reconciliation + reconciliation
            # approval workflow + 6 resource_types + 4 enforcement_levels
            # + 5 rule_types + 3 reconciliation strategy.
            Capability.FINOPS_TAG_GOVERNANCE,
            # Phase 16 (cj-style 127번째 wire) — FINOPS_REPORTING
            # (industry-agnostic, FinOps executive reporting layer CR 12-1
            # L4 precedent + FINOPS_TAG_GOVERNANCE Phase 15 wire +
            # FINOPS_OPTIMIZATION Phase 14 wire + FINOPS_FORECASTING +
            # FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12 wire
            # + FINOPS Phase 11 wire pattern verbatim). 5-module
            # cross-join (Phase 11~15) + 8 NEW KPI calculations +
            # executive report generator PDF/CSV/Excel + scheduled
            # dispatch KST cron + tenant-scoped executive role RBAC.
            Capability.FINOPS_REPORTING,
            # Phase 17 (cj-style 131번째 wire) — FINOPS_SUSTAINABILITY
            # (industry-agnostic per CR 12-1 L4 precedent + FINOPS_REPORTING
            # Phase 16 wire + FINOPS_TAG_GOVERNANCE Phase 15 wire +
            # FINOPS_OPTIMIZATION Phase 14 wire + FINOPS_FORECASTING +
            # FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12 wire
            # + FINOPS Phase 11 wire pattern verbatim). 6-module cross-rollup
            # (Phase 11~16) + 8 NEW KPI calculations + sustainability report
            # generator PDF/CSV/Excel + scheduled dispatch KST cron +
            # tenant-scoped sustainability role RBAC. Sustainability &
            # carbon reporting applies industry-agnostically per EU CSRD +
            # SEC Climate Disclosure + EU Taxonomy + IFRS S2 + 한국 KSSB.
            Capability.FINOPS_SUSTAINABILITY,
            # Phase 18 (cj-style 135번째 wire) — FINOPS_COMMITMENT
            # (industry-agnostic per CR 12-1 L4 precedent + FINOPS_SUSTAINABILITY
            # Phase 17 wire + FINOPS_REPORTING Phase 16 wire +
            # FINOPS_TAG_GOVERNANCE Phase 15 wire + FINOPS_OPTIMIZATION
            # Phase 14 wire + FINOPS_FORECASTING + FINOPS_ANOMALY_DETECTION
            # + FINOPS_BUDGET_ALERT Phase 12 wire + FINOPS Phase 11 wire
            # pattern verbatim). 7-module cross-rollup (Phase 11~17) +
            # 5-cloud-provider breakdown (AWS + Azure + GCP + Naver + KT) +
            # 8 NEW KPI calculations + commitment report generator
            # PDF/CSV/Excel + scheduled dispatch KST cron + tenant-scoped
            # commitment role RBAC. Cloud commitment management applies
            # industry-agnostically per FinOps Foundation + AWS Cost
            # Optimization Pillar + Azure Cost Optimization + GCP Cost
            # Optimization + 한국 조달청 클라우드 commitment 가이드라인.
            Capability.FINOPS_COMMITMENT,
            # Phase 19 (cj-style 139번째 wire) — FINOPS_PRICING
            # (industry-agnostic per CR 12-1 L4 precedent + FINOPS_COMMITMENT
            # Phase 18 wire + FINOPS_SUSTAINABILITY Phase 17 wire +
            # FINOPS_REPORTING Phase 16 wire + FINOPS_TAG_GOVERNANCE Phase 15
            # wire + FINOPS_OPTIMIZATION Phase 14 wire + FINOPS_FORECASTING +
            # FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12 wire +
            # FINOPS Phase 11 wire pattern verbatim). 8-module cross-rollup
            # (Phase 11~18) + 5-cloud-provider breakdown (AWS + Azure + GCP +
            # Naver + KT) + 6-pricing-model × 4-unit-metric matrix + 8 NEW
            # KPI calculations + pricing report generator PDF/CSV/Excel +
            # scheduled dispatch KST cron + tenant-scoped pricing role RBAC.
            # Pricing & TCO modeling applies industry-agnostically per FinOps
            # Foundation + AWS Pricing Models EDP + Azure Pricing Calculator
            # EA + GCP Pricing Calculator CUD + 한국 공공 조달 가격 가이드라인.
            Capability.FINOPS_PRICING,
            # Phase 20 (cj-style 144번째 wire) — FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION
            # (industry-agnostic per CR 12-1 L4 precedent + FINOPS_PRICING
            # Phase 19 wire + FINOPS_COMMITMENT Phase 18 wire + Phase 17 wire
            # + Phase 16 wire + Phase 15 wire + Phase 14 wire + Phase 13 wire
            # + Phase 12 wire + Phase 11 wire pattern verbatim). 9-module
            # cross-rollup (Phase 11~19) + 5-cloud-provider breakdown +
            # 5-marketplace source breakdown + 9 NEW cost KPI calculations +
            # marketplace report generator + scheduled dispatch KST cron +
            # multi-cloud viewer role RBAC. Multi-cloud cost unified
            # reconciliation applies industry-agnostically per FinOps
            # Foundation Multi-Cloud Cost Management pillar.
            Capability.FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION,
            # Phase 21 (cj-style 151번째 wire) — FINOPS_RESERVED_CAPACITY_PLANNING
            # (industry-agnostic per CR 12-1 L4 precedent +
            # FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION Phase 20 wire +
            # FINOPS_PRICING Phase 19 wire + FINOPS_COMMITMENT Phase 18 wire
            # + FINOPS_SUSTAINABILITY Phase 17 wire + FINOPS_REPORTING Phase
            # 16 wire + FINOPS_TAG_GOVERNANCE Phase 15 wire +
            # FINOPS_OPTIMIZATION Phase 14 wire + FINOPS_FORECASTING
            # Phase 13 wire + FINOPS_ANOMALY_DETECTION +
            # FINOPS_BUDGET_ALERT Phase 12 wire + FINOPS Phase 11 wire
            # pattern verbatim). 5-module composition layer (Phase 13
            # forecast + Phase 14 optimization + Phase 18 commitment +
            # Phase 19 pricing + Phase 20 multi_cloud weighted average →
            # single demand_forecast_id + capacity_plan_id +
            # commitment_recommendation_id + orchestration_id) + 6
            # reserved_capacity_tier (1y/3y × no/partial/all upfront) +
            # 4 execution_strategy + 4 cadence schedule (daily 02:00 +
            # weekly Mon 03:00 + monthly 1st-day 04:00 + quarterly 1st-day
            # 05:00 KST pytz) + dry-run mode + Epic 12 2FA 챌린지
            # mandatory (high-value threshold 10M KRW/year). Reserved
            # capacity planning applies industry-agnostically per FinOps
            # Foundation Reserved Capacity Planning pillar + 5-module
            # composition layer pattern.
            Capability.FINOPS_RESERVED_CAPACITY_PLANNING,
        }
    ),
    Industry.SERVICE: frozenset(
        {
            Capability.COST_POOL,
            Capability.ACTIVITY,
            Capability.DRIVER,
            Capability.AI_EXTRACT,
            # Story 10.1 (Epic 10) — service tenants get AI_INSIGHT
            # (industry-agnostic, validation guard CR 12-1 L4).
            Capability.AI_INSIGHT,
            # Story 13.1 (Epic 13) — service tenants get LISTEN_NOTIFY
            # (industry-agnostic, validation guard CR 12-1 L4 + AI_INSIGHT
            # 10-1 wire pattern). Gates the LISTEN daemon registration.
            Capability.LISTEN_NOTIFY,
            # Story 2.1 — service tenants get PRODUCT (catalog CRUD) but
            # NOT PRODUCT_MATERIAL (no BOM → no physical raw/semi entries).
            Capability.PRODUCT,
            # Story 3.1 — service tenants have NO production capability
            # → the [생산] tab is hidden. The other 5 streams
            # (orders/sales/purchases/expenses/labor) are ungated.
            # Story 4.1 — service tenants do NOT have COST_CALCULATION
            # (no manufacturing footprint → no [계산] tab; they will
            # use Epic 9 ABC costing instead — gate owner: m9_abc).
            # Story 12.2 — service tenants get BACKUP_EXPORT
            # (industry-agnostic, security baseline CR 12-1 L4).
            Capability.BACKUP_EXPORT,
            # Story 12.1 — service tenants get TWO_FACTOR_AUTH
            # (industry-agnostic, security baseline CR 12-1 L4).
            Capability.TWO_FACTOR_AUTH,
            # Story 12.3 — service tenants get ACCOUNT_DELETION
            # (industry-agnostic, security baseline CR 12-1 L4).
            Capability.ACCOUNT_DELETION,
            # Story 8.1 — service tenants get BUDGET_SCENARIO
            # (industry-agnostic, financial baseline CR 12-1 L4 +
            # 7-1/7-2 L4 precedent — all industries grant).
            Capability.BUDGET_SCENARIO,
            # Story 7.1 — service tenants get CVP_SIMULATION
            # (industry-agnostic, financial baseline CR 12-1 L4).
            Capability.CVP_SIMULATION,
            # Story 9.1 — service tenants get ABC_CALCULATION
            # (industry-agnostic, validation guard CR 12-1 L4).
            Capability.ABC_CALCULATION,
            # Story 14.1 (Epic 14) — service tenants get
            # LISTEN_NOTIFY_TENANT_FANOUT + LISTEN_NOTIFY_MULTIPROCESS
            # (industry-agnostic, validation guard CR 12-1 L4 +
            # LISTEN_NOTIFY 13-1 wire pattern).
            Capability.LISTEN_NOTIFY_TENANT_FANOUT,
            Capability.LISTEN_NOTIFY_MULTIPROCESS,
            # Story phase-3.1 — service tenants get LOGIN + SIGNUP +
            # AUTH_MIDDLEWARE + FORGOT_PASSWORD + LOGOUT (industry-agnostic,
            # security baseline CR 12-1 L4).
            Capability.LOGIN,
            Capability.SIGNUP,
            Capability.AUTH_MIDDLEWARE,
            Capability.FORGOT_PASSWORD,
            Capability.LOGOUT,
            # Story phase-4 — service tenants get DEPLOYMENT_PROD +
            # DEPLOYMENT_STAGING + DEPLOYMENT_DATABASE_BACKUP +
            # DEPLOYMENT_HEALTH_CHECK (industry-agnostic, operational
            # infrastructure CR 12-1 L4 + LISTEN_NOTIFY 13-1/14-1 wire
            # pattern). All 4 industries get deployment capability.
            Capability.DEPLOYMENT_PROD,
            Capability.DEPLOYMENT_STAGING,
            Capability.DEPLOYMENT_DATABASE_BACKUP,
            Capability.DEPLOYMENT_HEALTH_CHECK,
            # Story Epic 15 — service tenants get MAGIC_LINK +
            # SOCIAL_OAUTH_GOOGLE + SOCIAL_OAUTH_NAVER +
            # SOCIAL_OAUTH_KAKAO + SSO_ENTERPRISE (industry-agnostic,
            # CR 12-1 L4 precedent).
            Capability.MAGIC_LINK,
            Capability.SOCIAL_OAUTH_GOOGLE,
            Capability.SOCIAL_OAUTH_NAVER,
            Capability.SOCIAL_OAUTH_KAKAO,
            Capability.SSO_ENTERPRISE,
            # Story 1st-release (cj-style 64번째) — service tenants get
            # LAUNCH_LANDING + LAUNCH_TOS + LAUNCH_SUPPORT +
            # LAUNCH_MONITORING (industry-agnostic, CR 12-1 L4 precedent).
            Capability.LAUNCH_LANDING,
            Capability.LAUNCH_TOS,
            Capability.LAUNCH_SUPPORT,
            Capability.LAUNCH_MONITORING,
            # Epic 16 (cj-style 69번째) — service tenants get
            # TENANT_IDP_MANAGEMENT (industry-agnostic, CR 12-1 L4 precedent).
            Capability.TENANT_IDP_MANAGEMENT,
            # Phase 5 (cj-style 75번째 wire) — service tenants get
            # MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER
            # (industry-agnostic, CR 12-1 L4 precedent).
            Capability.MULTI_REGION_BACKUP,
            Capability.MULTI_REGION_FAILOVER,
            # Epic 17 (cj-style 82번째 wire) — service tenants get
            # AUDIT_LOG_VIEW (industry-agnostic, observability baseline
            # CR 12-1 L4 precedent + MULTI_REGION_BACKUP +
            # MULTI_REGION_FAILOVER Phase 5 wire pattern verbatim).
            Capability.AUDIT_LOG_VIEW,
            # Phase 6 (cj-style 87번째 wire) — manufacturing/service/겸영/겸영+기타
            # tenants get AUDIT_LOG_RETENTION (industry-agnostic, compliance
            # baseline CR 12-1 L4 precedent + AUDIT_LOG_VIEW Epic 17 wire +
            # MULTI_REGION_BACKUP/FAILOVER Phase 5 wire pattern verbatim).
            Capability.AUDIT_LOG_RETENTION,
            # Phase 7 (cj-style 91번째 wire) — tenants get
            # OBSERVABILITY_TRACES + OBSERVABILITY_METRICS
            # (industry-agnostic, observability baseline CR 12-1 L4 precedent
            # + AUDIT_LOG_RETENTION Phase 6 wire + AUDIT_LOG_VIEW Epic 17
            # wire + MULTI_REGION_BACKUP/FAILOVER Phase 5 wire pattern
            # verbatim). All 4 industries get both observability
            # capabilities (OpenTelemetry distributed tracing + Prometheus
            # custom metrics + Grafana dashboards are operational baseline).
            Capability.OBSERVABILITY_TRACES,
            Capability.OBSERVABILITY_METRICS,
            # Phase 8 (cj-style 95번째 wire) — service tenants get
            # PERFORMANCE_TESTING (industry-agnostic, performance /
            # observability baseline CR 12-1 L4 precedent).
            Capability.PERFORMANCE_TESTING,
            # Phase 9 (cj-style 99번째 wire) — service tenants get
            # CHAOS_ENGINEERING (industry-agnostic, chaos engineering
            # baseline CR 12-1 L4 precedent).
            Capability.CHAOS_ENGINEERING,
            # Phase 10 (cj-style 103번째 wire) — all industries get
            # SLO_ENGINEERING (industry-agnostic, SLO engineering baseline
            # CR 12-1 L4 precedent + CHAOS_ENGINEERING Phase 9 wire +
            # PERFORMANCE_TESTING Phase 8 wire + OBSERVABILITY_* Phase 7
            # wire pattern verbatim).
            Capability.SLO_ENGINEERING,
            # Phase 11 (cj-style 107번째 wire) — service tenants get
            # FINOPS_SHOWBACK + FINOPS_CHARGEBACK (industry-agnostic,
            # FinOps financial reporting baseline CR 12-1 L4 precedent +
            # SLO_ENGINEERING Phase 10 wire + CHAOS_ENGINEERING Phase 9
            # wire + PERFORMANCE_TESTING Phase 8 wire + OBSERVABILITY_*
            # Phase 7 wire pattern verbatim).
            Capability.FINOPS_SHOWBACK,
            Capability.FINOPS_CHARGEBACK,
            # Phase 12 (cj-style 111번째 wire) — service tenants get
            # FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT
            # (industry-agnostic, CR 12-1 L4 precedent).
            Capability.FINOPS_ANOMALY_DETECTION,
            Capability.FINOPS_BUDGET_ALERT,
            # Phase 13 (cj-style 115번째 wire) — service tenants get
            # FINOPS_FORECASTING_CAPACITY_PLANNING (industry-agnostic,
            # CR 12-1 L4 precedent).
            Capability.FINOPS_FORECASTING_CAPACITY_PLANNING,
            # Phase 14 (cj-style 119번째 wire) — service tenants get
            # FINOPS_OPTIMIZATION (industry-agnostic, FinOps
            # ACTIONABLE RECOMMENDATION LAYER EXTENSION of Phase 13
            # forecast baseline CR 12-1 L4 precedent).
            Capability.FINOPS_OPTIMIZATION,
            # Phase 15 (cj-style 123번째 wire) — service tenants get
            # FINOPS_TAG_GOVERNANCE (industry-agnostic, FinOps cost
            # allocation baseline CR 12-1 L4 precedent).
            Capability.FINOPS_TAG_GOVERNANCE,
            # Phase 16 (cj-style 127번째 wire) — FINOPS_REPORTING
            # (industry-agnostic, FinOps executive reporting layer CR 12-1
            # L4 precedent + FINOPS_TAG_GOVERNANCE Phase 15 wire +
            # FINOPS_OPTIMIZATION Phase 14 wire + FINOPS_FORECASTING +
            # FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12 wire
            # + FINOPS Phase 11 wire pattern verbatim). 5-module
            # cross-join (Phase 11~15) + 8 NEW KPI calculations +
            # executive report generator PDF/CSV/Excel + scheduled
            # dispatch KST cron + tenant-scoped executive role RBAC.
            Capability.FINOPS_REPORTING,
            # Phase 17 (cj-style 131번째 wire) — FINOPS_SUSTAINABILITY
            # (industry-agnostic per CR 12-1 L4 precedent + FINOPS_REPORTING
            # Phase 16 wire + FINOPS_TAG_GOVERNANCE Phase 15 wire +
            # FINOPS_OPTIMIZATION Phase 14 wire + FINOPS_FORECASTING +
            # FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12 wire
            # + FINOPS Phase 11 wire pattern verbatim). 6-module cross-rollup
            # (Phase 11~16) + 8 NEW KPI calculations + sustainability report
            # generator PDF/CSV/Excel + scheduled dispatch KST cron +
            # tenant-scoped sustainability role RBAC. Sustainability &
            # carbon reporting applies industry-agnostically per EU CSRD +
            # SEC Climate Disclosure + EU Taxonomy + IFRS S2 + 한국 KSSB.
            Capability.FINOPS_SUSTAINABILITY,
            # Phase 18 (cj-style 135번째 wire) — FINOPS_COMMITMENT
            # (industry-agnostic per CR 12-1 L4 precedent + FINOPS_SUSTAINABILITY
            # Phase 17 wire + FINOPS_REPORTING Phase 16 wire +
            # FINOPS_TAG_GOVERNANCE Phase 15 wire + FINOPS_OPTIMIZATION
            # Phase 14 wire + FINOPS_FORECASTING + FINOPS_ANOMALY_DETECTION
            # + FINOPS_BUDGET_ALERT Phase 12 wire + FINOPS Phase 11 wire
            # pattern verbatim). 7-module cross-rollup (Phase 11~17) +
            # 5-cloud-provider breakdown (AWS + Azure + GCP + Naver + KT) +
            # 8 NEW KPI calculations + commitment report generator
            # PDF/CSV/Excel + scheduled dispatch KST cron + tenant-scoped
            # commitment role RBAC. Cloud commitment management applies
            # industry-agnostically per FinOps Foundation + AWS Cost
            # Optimization Pillar + Azure Cost Optimization + GCP Cost
            # Optimization + 한국 조달청 클라우드 commitment 가이드라인.
            Capability.FINOPS_COMMITMENT,
            # Phase 19 (cj-style 139번째 wire) — FINOPS_PRICING
            # (industry-agnostic per CR 12-1 L4 precedent + FINOPS_COMMITMENT
            # Phase 18 wire + FINOPS_SUSTAINABILITY Phase 17 wire +
            # FINOPS_REPORTING Phase 16 wire + FINOPS_TAG_GOVERNANCE Phase 15
            # wire + FINOPS_OPTIMIZATION Phase 14 wire + FINOPS_FORECASTING +
            # FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12 wire +
            # FINOPS Phase 11 wire pattern verbatim). 8-module cross-rollup
            # (Phase 11~18) + 5-cloud-provider breakdown (AWS + Azure + GCP +
            # Naver + KT) + 6-pricing-model × 4-unit-metric matrix + 8 NEW
            # KPI calculations + pricing report generator PDF/CSV/Excel +
            # scheduled dispatch KST cron + tenant-scoped pricing role RBAC.
            # Pricing & TCO modeling applies industry-agnostically per FinOps
            # Foundation + AWS Pricing Models EDP + Azure Pricing Calculator
            # EA + GCP Pricing Calculator CUD + 한국 공공 조달 가격 가이드라인.
            Capability.FINOPS_PRICING,
            # Phase 20 (cj-style 144번째 wire) — FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION
            # (industry-agnostic per CR 12-1 L4 precedent + FINOPS_PRICING
            # Phase 19 wire + FINOPS_COMMITMENT Phase 18 wire + Phase 17 wire
            # + Phase 16 wire + Phase 15 wire + Phase 14 wire + Phase 13 wire
            # + Phase 12 wire + Phase 11 wire pattern verbatim). 9-module
            # cross-rollup (Phase 11~19) + 5-cloud-provider breakdown +
            # 5-marketplace source breakdown + 9 NEW cost KPI calculations +
            # marketplace report generator + scheduled dispatch KST cron +
            # multi-cloud viewer role RBAC. Multi-cloud cost unified
            # reconciliation applies industry-agnostically per FinOps
            # Foundation Multi-Cloud Cost Management pillar.
            Capability.FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION,
            # Phase 21 (cj-style 151번째 wire) — FINOPS_RESERVED_CAPACITY_PLANNING
            # (industry-agnostic per CR 12-1 L4 precedent +
            # FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION Phase 20 wire +
            # FINOPS_PRICING Phase 19 wire + FINOPS_COMMITMENT Phase 18 wire
            # + FINOPS_SUSTAINABILITY Phase 17 wire + FINOPS_REPORTING Phase
            # 16 wire + FINOPS_TAG_GOVERNANCE Phase 15 wire +
            # FINOPS_OPTIMIZATION Phase 14 wire + FINOPS_FORECASTING
            # Phase 13 wire + FINOPS_ANOMALY_DETECTION +
            # FINOPS_BUDGET_ALERT Phase 12 wire + FINOPS Phase 11 wire
            # pattern verbatim). 5-module composition layer + 6
            # reserved_capacity_tier + 4 execution_strategy + 4 cadence
            # schedule KST pytz + dry-run mode + Epic 12 2FA 챌린지
            # mandatory (high-value threshold 10M KRW/year).
            Capability.FINOPS_RESERVED_CAPACITY_PLANNING,
        }
    ),
    Industry.MANUFACTURING_SERVICE: frozenset(
        {
            Capability.BOM,
            Capability.OPENING_INVENTORY,
            Capability.INVENTORY_LEDGER,
            # Story 5.3 — 겸영 tenants get closing-guard gate
            # (PRD §F4.2 + §V3).
            Capability.INVENTORY_CLOSING_GUARD,
            Capability.COST_POOL,
            Capability.ACTIVITY,
            Capability.DRIVER,
            Capability.SEGMENT_SPLIT,
            Capability.AI_EXTRACT,
            # Story 10.1 (Epic 10) — 겸영 tenants get AI_INSIGHT
            # (industry-agnostic, validation guard CR 12-1 L4).
            Capability.AI_INSIGHT,
            # Story 13.1 (Epic 13) — 겸영 tenants get LISTEN_NOTIFY
            # (industry-agnostic, validation guard CR 12-1 L4 + AI_INSIGHT
            # 10-1 wire pattern). Gates the LISTEN daemon registration.
            Capability.LISTEN_NOTIFY,
            # Story 2.1 — both engines → full product catalog.
            Capability.PRODUCT,
            Capability.PRODUCT_MATERIAL,
            # Story 3.1 — 겸영 tenants get the [생산] tab.
            Capability.MONTHLY_INPUT_PRODUCTION,
            # Story 4.1 — 겸영 tenants get BOTH §6.1 traditional costing
            # AND Epic 9 ABC costing (rows above). m3_calculate service
            # routes only check COST_CALCULATION; M9 routes check
            # COST_POOL/ACTIVITY/DRIVER.
            Capability.COST_CALCULATION,
            # Story 6.1 — 겸영 tenants get Monthly Closing Report.
            Capability.MONTHLY_CLOSING_REPORT,
            # Story 11.1 — 겸영 tenants get REVERSAL_REQUEST.
            Capability.REVERSAL_REQUEST,
            # Story 11.2 — 겸영 tenants get the 4-stage close
            # sequence lock (manufacturing footprint present).
            Capability.CLOSE_SEQUENCE_LOCK,
            # Story 11.3 — 겸영 tenants get SNAPSHOT_PERSISTENCE +
            # REVERSAL_EXECUTE + REOPEN_OPERATOR.
            Capability.SNAPSHOT_PERSISTENCE,
            Capability.REVERSAL_EXECUTE,
            Capability.REOPEN_OPERATOR,
            # Story 12.2 — 겸영 tenants get BACKUP_EXPORT
            # (industry-agnostic, security baseline CR 12-1 L4).
            Capability.BACKUP_EXPORT,
            # Story 12.1 — 겸영 tenants get TWO_FACTOR_AUTH
            # (industry-agnostic, security baseline CR 12-1 L4).
            Capability.TWO_FACTOR_AUTH,
            # Story 12.3 — 겸영 tenants get ACCOUNT_DELETION
            # (industry-agnostic, security baseline CR 12-1 L4).
            Capability.ACCOUNT_DELETION,
            # Story 8.1 — 겸영 tenants get BUDGET_SCENARIO
            # (industry-agnostic, financial baseline CR 12-1 L4 +
            # 7-1/7-2 L4 precedent — all industries grant).
            Capability.BUDGET_SCENARIO,
            # Story 7.1 — 겸영 tenants get CVP_SIMULATION
            # (industry-agnostic, financial baseline CR 12-1 L4).
            Capability.CVP_SIMULATION,
            # Story 9.1 — 겸영 tenants get ABC_CALCULATION
            # (industry-agnostic, validation guard CR 12-1 L4).
            Capability.ABC_CALCULATION,
            # Story 14.1 (Epic 14) — 겸영 tenants get
            # LISTEN_NOTIFY_TENANT_FANOUT + LISTEN_NOTIFY_MULTIPROCESS
            # (industry-agnostic, validation guard CR 12-1 L4 +
            # LISTEN_NOTIFY 13-1 wire pattern).
            Capability.LISTEN_NOTIFY_TENANT_FANOUT,
            Capability.LISTEN_NOTIFY_MULTIPROCESS,
            # Story phase-3.1 — 겸영 tenants get LOGIN + SIGNUP +
            # AUTH_MIDDLEWARE + FORGOT_PASSWORD + LOGOUT (industry-agnostic,
            # security baseline CR 12-1 L4).
            Capability.LOGIN,
            Capability.SIGNUP,
            Capability.AUTH_MIDDLEWARE,
            Capability.FORGOT_PASSWORD,
            Capability.LOGOUT,
            # Story phase-4 — 겸영 tenants get DEPLOYMENT_PROD +
            # DEPLOYMENT_STAGING + DEPLOYMENT_DATABASE_BACKUP +
            # DEPLOYMENT_HEALTH_CHECK (industry-agnostic, operational
            # infrastructure CR 12-1 L4 + LISTEN_NOTIFY 13-1/14-1 wire
            # pattern). All 4 industries get deployment capability.
            Capability.DEPLOYMENT_PROD,
            Capability.DEPLOYMENT_STAGING,
            Capability.DEPLOYMENT_DATABASE_BACKUP,
            Capability.DEPLOYMENT_HEALTH_CHECK,
            # Story Epic 15 — 겸영 tenants get MAGIC_LINK +
            # SOCIAL_OAUTH_GOOGLE + SOCIAL_OAUTH_NAVER +
            # SOCIAL_OAUTH_KAKAO + SSO_ENTERPRISE (industry-agnostic,
            # CR 12-1 L4 precedent).
            Capability.MAGIC_LINK,
            Capability.SOCIAL_OAUTH_GOOGLE,
            Capability.SOCIAL_OAUTH_NAVER,
            Capability.SOCIAL_OAUTH_KAKAO,
            Capability.SSO_ENTERPRISE,
            # Story 1st-release (cj-style 64번째) — 겸영 tenants get
            # LAUNCH_LANDING + LAUNCH_TOS + LAUNCH_SUPPORT +
            # LAUNCH_MONITORING (industry-agnostic, CR 12-1 L4 precedent).
            Capability.LAUNCH_LANDING,
            Capability.LAUNCH_TOS,
            Capability.LAUNCH_SUPPORT,
            Capability.LAUNCH_MONITORING,
            # Epic 16 (cj-style 69번째) — 겸영 tenants get
            # TENANT_IDP_MANAGEMENT (industry-agnostic, CR 12-1 L4 precedent).
            Capability.TENANT_IDP_MANAGEMENT,
            # Phase 5 (cj-style 75번째 wire) — 겸영 tenants get
            # MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER
            # (industry-agnostic, CR 12-1 L4 precedent).
            Capability.MULTI_REGION_BACKUP,
            Capability.MULTI_REGION_FAILOVER,
            # Epic 17 (cj-style 82번째 wire) — 겸영 tenants get
            # AUDIT_LOG_VIEW (industry-agnostic, observability baseline
            # CR 12-1 L4 precedent + MULTI_REGION_BACKUP +
            # MULTI_REGION_FAILOVER Phase 5 wire pattern verbatim).
            Capability.AUDIT_LOG_VIEW,
            # Phase 6 (cj-style 87번째 wire) — manufacturing/service/겸영/겸영+기타
            # tenants get AUDIT_LOG_RETENTION (industry-agnostic, compliance
            # baseline CR 12-1 L4 precedent + AUDIT_LOG_VIEW Epic 17 wire +
            # MULTI_REGION_BACKUP/FAILOVER Phase 5 wire pattern verbatim).
            Capability.AUDIT_LOG_RETENTION,
            # Phase 7 (cj-style 91번째 wire) — tenants get
            # OBSERVABILITY_TRACES + OBSERVABILITY_METRICS
            # (industry-agnostic, observability baseline CR 12-1 L4 precedent
            # + AUDIT_LOG_RETENTION Phase 6 wire + AUDIT_LOG_VIEW Epic 17
            # wire + MULTI_REGION_BACKUP/FAILOVER Phase 5 wire pattern
            # verbatim). All 4 industries get both observability
            # capabilities (OpenTelemetry distributed tracing + Prometheus
            # custom metrics + Grafana dashboards are operational baseline).
            Capability.OBSERVABILITY_TRACES,
            Capability.OBSERVABILITY_METRICS,
            # Phase 8 (cj-style 95번째 wire) — 겸영 tenants get
            # PERFORMANCE_TESTING (industry-agnostic, performance /
            # observability baseline CR 12-1 L4 precedent).
            Capability.PERFORMANCE_TESTING,
            # Phase 9 (cj-style 99번째 wire) — 겸영 tenants get
            # CHAOS_ENGINEERING (industry-agnostic, chaos engineering
            # baseline CR 12-1 L4 precedent).
            Capability.CHAOS_ENGINEERING,
            # Phase 10 (cj-style 103번째 wire) — all industries get
            # SLO_ENGINEERING (industry-agnostic, SLO engineering baseline
            # CR 12-1 L4 precedent + CHAOS_ENGINEERING Phase 9 wire +
            # PERFORMANCE_TESTING Phase 8 wire + OBSERVABILITY_* Phase 7
            # wire pattern verbatim).
            Capability.SLO_ENGINEERING,
            # Phase 11 (cj-style 107번째 wire) — 겸영 tenants get
            # FINOPS_SHOWBACK + FINOPS_CHARGEBACK (industry-agnostic,
            # FinOps financial reporting baseline CR 12-1 L4 precedent).
            Capability.FINOPS_SHOWBACK,
            Capability.FINOPS_CHARGEBACK,
            # Phase 12 (cj-style 111번째 wire) — 겸영 tenants get
            # FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT
            # (industry-agnostic, CR 12-1 L4 precedent).
            Capability.FINOPS_ANOMALY_DETECTION,
            Capability.FINOPS_BUDGET_ALERT,
            # Phase 13 (cj-style 115번째 wire) — 겸영 tenants get
            # FINOPS_FORECASTING_CAPACITY_PLANNING (industry-agnostic,
            # CR 12-1 L4 precedent).
            Capability.FINOPS_FORECASTING_CAPACITY_PLANNING,
            # Phase 14 (cj-style 119번째 wire) — 겸영 tenants get
            # FINOPS_OPTIMIZATION (industry-agnostic, FinOps
            # ACTIONABLE RECOMMENDATION LAYER EXTENSION of Phase 13
            # forecast baseline CR 12-1 L4 precedent).
            Capability.FINOPS_OPTIMIZATION,
            # Phase 15 (cj-style 123번째 wire) — 겸영 tenants get
            # FINOPS_TAG_GOVERNANCE (industry-agnostic, FinOps cost
            # allocation baseline CR 12-1 L4 precedent).
            Capability.FINOPS_TAG_GOVERNANCE,
            # Phase 16 (cj-style 127번째 wire) — FINOPS_REPORTING
            # (industry-agnostic, FinOps executive reporting layer CR 12-1
            # L4 precedent + FINOPS_TAG_GOVERNANCE Phase 15 wire +
            # FINOPS_OPTIMIZATION Phase 14 wire + FINOPS_FORECASTING +
            # FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12 wire
            # + FINOPS Phase 11 wire pattern verbatim). 5-module
            # cross-join (Phase 11~15) + 8 NEW KPI calculations +
            # executive report generator PDF/CSV/Excel + scheduled
            # dispatch KST cron + tenant-scoped executive role RBAC.
            Capability.FINOPS_REPORTING,
            # Phase 17 (cj-style 131번째 wire) — FINOPS_SUSTAINABILITY
            # (industry-agnostic per CR 12-1 L4 precedent + FINOPS_REPORTING
            # Phase 16 wire + FINOPS_TAG_GOVERNANCE Phase 15 wire +
            # FINOPS_OPTIMIZATION Phase 14 wire + FINOPS_FORECASTING +
            # FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12 wire
            # + FINOPS Phase 11 wire pattern verbatim). 6-module cross-rollup
            # (Phase 11~16) + 8 NEW KPI calculations + sustainability report
            # generator PDF/CSV/Excel + scheduled dispatch KST cron +
            # tenant-scoped sustainability role RBAC. Sustainability &
            # carbon reporting applies industry-agnostically per EU CSRD +
            # SEC Climate Disclosure + EU Taxonomy + IFRS S2 + 한국 KSSB.
            Capability.FINOPS_SUSTAINABILITY,
            # Phase 18 (cj-style 135번째 wire) — FINOPS_COMMITMENT
            # (industry-agnostic per CR 12-1 L4 precedent + FINOPS_SUSTAINABILITY
            # Phase 17 wire + FINOPS_REPORTING Phase 16 wire +
            # FINOPS_TAG_GOVERNANCE Phase 15 wire + FINOPS_OPTIMIZATION
            # Phase 14 wire + FINOPS_FORECASTING + FINOPS_ANOMALY_DETECTION
            # + FINOPS_BUDGET_ALERT Phase 12 wire + FINOPS Phase 11 wire
            # pattern verbatim). 7-module cross-rollup (Phase 11~17) +
            # 5-cloud-provider breakdown (AWS + Azure + GCP + Naver + KT) +
            # 8 NEW KPI calculations + commitment report generator
            # PDF/CSV/Excel + scheduled dispatch KST cron + tenant-scoped
            # commitment role RBAC. Cloud commitment management applies
            # industry-agnostically per FinOps Foundation + AWS Cost
            # Optimization Pillar + Azure Cost Optimization + GCP Cost
            # Optimization + 한국 조달청 클라우드 commitment 가이드라인.
            Capability.FINOPS_COMMITMENT,
            # Phase 19 (cj-style 139번째 wire) — FINOPS_PRICING
            # (industry-agnostic per CR 12-1 L4 precedent + FINOPS_COMMITMENT
            # Phase 18 wire + FINOPS_SUSTAINABILITY Phase 17 wire +
            # FINOPS_REPORTING Phase 16 wire + FINOPS_TAG_GOVERNANCE Phase 15
            # wire + FINOPS_OPTIMIZATION Phase 14 wire + FINOPS_FORECASTING +
            # FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12 wire +
            # FINOPS Phase 11 wire pattern verbatim). 8-module cross-rollup
            # (Phase 11~18) + 5-cloud-provider breakdown (AWS + Azure + GCP +
            # Naver + KT) + 6-pricing-model × 4-unit-metric matrix + 8 NEW
            # KPI calculations + pricing report generator PDF/CSV/Excel +
            # scheduled dispatch KST cron + tenant-scoped pricing role RBAC.
            # Pricing & TCO modeling applies industry-agnostically per FinOps
            # Foundation + AWS Pricing Models EDP + Azure Pricing Calculator
            # EA + GCP Pricing Calculator CUD + 한국 공공 조달 가격 가이드라인.
            Capability.FINOPS_PRICING,
            # Phase 20 (cj-style 144번째 wire) — FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION
            # (industry-agnostic per CR 12-1 L4 precedent + FINOPS_PRICING
            # Phase 19 wire + FINOPS_COMMITMENT Phase 18 wire + Phase 17 wire
            # + Phase 16 wire + Phase 15 wire + Phase 14 wire + Phase 13 wire
            # + Phase 12 wire + Phase 11 wire pattern verbatim). 9-module
            # cross-rollup (Phase 11~19) + 5-cloud-provider breakdown +
            # 5-marketplace source breakdown + 9 NEW cost KPI calculations +
            # marketplace report generator + scheduled dispatch KST cron +
            # multi-cloud viewer role RBAC. Multi-cloud cost unified
            # reconciliation applies industry-agnostically per FinOps
            # Foundation Multi-Cloud Cost Management pillar.
            Capability.FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION,
            # Phase 21 (cj-style 151번째 wire) — FINOPS_RESERVED_CAPACITY_PLANNING
            # (industry-agnostic per CR 12-1 L4 precedent +
            # FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION Phase 20 wire +
            # FINOPS_PRICING Phase 19 wire + FINOPS_COMMITMENT Phase 18 wire
            # + FINOPS_SUSTAINABILITY Phase 17 wire + FINOPS_REPORTING Phase
            # 16 wire + FINOPS_TAG_GOVERNANCE Phase 15 wire +
            # FINOPS_OPTIMIZATION Phase 14 wire + FINOPS_FORECASTING
            # Phase 13 wire + FINOPS_ANOMALY_DETECTION +
            # FINOPS_BUDGET_ALERT Phase 12 wire + FINOPS Phase 11 wire
            # pattern verbatim). 5-module composition layer + 6
            # reserved_capacity_tier + 4 execution_strategy + 4 cadence
            # schedule KST pytz + dry-run mode + Epic 12 2FA 챌린지
            # mandatory (high-value threshold 10M KRW/year).
            Capability.FINOPS_RESERVED_CAPACITY_PLANNING,
        }
    ),
    Industry.MANUFACTURING_SERVICE_OTHER: frozenset(
        {
            Capability.BOM,
            Capability.OPENING_INVENTORY,
            Capability.INVENTORY_LEDGER,
            # Story 5.3 — 겸영 + other tenants get closing-guard gate
            # (PRD §F4.2 + §V3).
            Capability.INVENTORY_CLOSING_GUARD,
            Capability.COST_POOL,
            Capability.ACTIVITY,
            Capability.DRIVER,
            Capability.SEGMENT_SPLIT,
            Capability.AI_EXTRACT,
            # Story 10.1 (Epic 10) — full matrix tenants get AI_INSIGHT
            # (industry-agnostic, validation guard CR 12-1 L4).
            Capability.AI_INSIGHT,
            # Story 13.1 (Epic 13) — full matrix tenants get LISTEN_NOTIFY
            # (industry-agnostic, validation guard CR 12-1 L4 + AI_INSIGHT
            # 10-1 wire pattern). Gates the LISTEN daemon registration.
            Capability.LISTEN_NOTIFY,
            # Story 2.1 — full catalog + 격리 버킷.
            Capability.PRODUCT,
            Capability.PRODUCT_MATERIAL,
            # Story 3.1 — full matrix.
            Capability.MONTHLY_INPUT_PRODUCTION,
            # Story 4.1 — full matrix + 격리 버킷.
            Capability.COST_CALCULATION,
            # Story 6.1 — full matrix tenants get Monthly Closing Report.
            Capability.MONTHLY_CLOSING_REPORT,
            # Story 11.1 — full matrix tenants get REVERSAL_REQUEST.
            Capability.REVERSAL_REQUEST,
            # Story 11.2 — full matrix tenants get the 4-stage close
            # sequence lock (manufacturing footprint present).
            Capability.CLOSE_SEQUENCE_LOCK,
            # Story 11.3 — full matrix tenants get SNAPSHOT_PERSISTENCE +
            # REVERSAL_EXECUTE + REOPEN_OPERATOR.
            Capability.SNAPSHOT_PERSISTENCE,
            Capability.REVERSAL_EXECUTE,
            Capability.REOPEN_OPERATOR,
            # Story 12.2 — full matrix tenants get BACKUP_EXPORT
            # (industry-agnostic, security baseline CR 12-1 L4).
            Capability.BACKUP_EXPORT,
            # Story 12.1 — full matrix tenants get TWO_FACTOR_AUTH
            # (industry-agnostic, security baseline CR 12-1 L4).
            Capability.TWO_FACTOR_AUTH,
            # Story 12.3 — full matrix tenants get ACCOUNT_DELETION
            # (industry-agnostic, security baseline CR 12-1 L4).
            Capability.ACCOUNT_DELETION,
            # Story 8.1 — full matrix tenants get BUDGET_SCENARIO
            # (industry-agnostic, financial baseline CR 12-1 L4 +
            # 7-1/7-2 L4 precedent — all industries grant).
            Capability.BUDGET_SCENARIO,
            # Story 7.1 — full matrix tenants get CVP_SIMULATION
            # (industry-agnostic, financial baseline CR 12-1 L4).
            Capability.CVP_SIMULATION,
            # Story 9.1 — full matrix tenants get ABC_CALCULATION
            # (industry-agnostic, validation guard CR 12-1 L4).
            Capability.ABC_CALCULATION,
            # Story 14.1 (Epic 14) — full matrix tenants get
            # LISTEN_NOTIFY_TENANT_FANOUT + LISTEN_NOTIFY_MULTIPROCESS
            # (industry-agnostic, validation guard CR 12-1 L4 +
            # LISTEN_NOTIFY 13-1 wire pattern).
            Capability.LISTEN_NOTIFY_TENANT_FANOUT,
            Capability.LISTEN_NOTIFY_MULTIPROCESS,
            # Story phase-3.1 — full matrix tenants get LOGIN + SIGNUP +
            # AUTH_MIDDLEWARE + FORGOT_PASSWORD + LOGOUT (industry-agnostic,
            # security baseline CR 12-1 L4).
            Capability.LOGIN,
            Capability.SIGNUP,
            Capability.AUTH_MIDDLEWARE,
            Capability.FORGOT_PASSWORD,
            Capability.LOGOUT,
            # Story phase-4 — full matrix tenants get DEPLOYMENT_PROD +
            # DEPLOYMENT_STAGING + DEPLOYMENT_DATABASE_BACKUP +
            # DEPLOYMENT_HEALTH_CHECK (industry-agnostic, operational
            # infrastructure CR 12-1 L4 + LISTEN_NOTIFY 13-1/14-1 wire
            # pattern). All 4 industries get deployment capability.
            Capability.DEPLOYMENT_PROD,
            Capability.DEPLOYMENT_STAGING,
            Capability.DEPLOYMENT_DATABASE_BACKUP,
            Capability.DEPLOYMENT_HEALTH_CHECK,
            # Story Epic 15 — 겸영+기타 tenants get MAGIC_LINK +
            # SOCIAL_OAUTH_GOOGLE + SOCIAL_OAUTH_NAVER +
            # SOCIAL_OAUTH_KAKAO + SSO_ENTERPRISE (industry-agnostic,
            # CR 12-1 L4 precedent).
            Capability.MAGIC_LINK,
            Capability.SOCIAL_OAUTH_GOOGLE,
            Capability.SOCIAL_OAUTH_NAVER,
            Capability.SOCIAL_OAUTH_KAKAO,
            Capability.SSO_ENTERPRISE,
            # Story 1st-release (cj-style 64번째) — 겸영+기타 tenants get
            # LAUNCH_LANDING + LAUNCH_TOS + LAUNCH_SUPPORT +
            # LAUNCH_MONITORING (industry-agnostic, CR 12-1 L4 precedent).
            Capability.LAUNCH_LANDING,
            Capability.LAUNCH_TOS,
            Capability.LAUNCH_SUPPORT,
            Capability.LAUNCH_MONITORING,
            # Epic 16 (cj-style 69번째) — 겸영+기타 tenants get
            # TENANT_IDP_MANAGEMENT (industry-agnostic, CR 12-1 L4 precedent).
            Capability.TENANT_IDP_MANAGEMENT,
            # Phase 5 (cj-style 75번째 wire) — 겸영+기타 tenants get
            # MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER
            # (industry-agnostic, CR 12-1 L4 precedent).
            Capability.MULTI_REGION_BACKUP,
            Capability.MULTI_REGION_FAILOVER,
            # Epic 17 (cj-style 82번째 wire) — 겸영+기타 tenants get
            # AUDIT_LOG_VIEW (industry-agnostic, observability baseline
            # CR 12-1 L4 precedent + MULTI_REGION_BACKUP +
            # MULTI_REGION_FAILOVER Phase 5 wire pattern verbatim).
            Capability.AUDIT_LOG_VIEW,
            # Phase 6 (cj-style 87번째 wire) — manufacturing/service/겸영/겸영+기타
            # tenants get AUDIT_LOG_RETENTION (industry-agnostic, compliance
            # baseline CR 12-1 L4 precedent + AUDIT_LOG_VIEW Epic 17 wire +
            # MULTI_REGION_BACKUP/FAILOVER Phase 5 wire pattern verbatim).
            Capability.AUDIT_LOG_RETENTION,
            # Phase 7 (cj-style 91번째 wire) — tenants get
            # OBSERVABILITY_TRACES + OBSERVABILITY_METRICS
            # (industry-agnostic, observability baseline CR 12-1 L4 precedent
            # + AUDIT_LOG_RETENTION Phase 6 wire + AUDIT_LOG_VIEW Epic 17
            # wire + MULTI_REGION_BACKUP/FAILOVER Phase 5 wire pattern
            # verbatim). All 4 industries get both observability
            # capabilities (OpenTelemetry distributed tracing + Prometheus
            # custom metrics + Grafana dashboards are operational baseline).
            Capability.OBSERVABILITY_TRACES,
            Capability.OBSERVABILITY_METRICS,
            # Phase 8 (cj-style 95번째 wire) — full matrix tenants get
            # PERFORMANCE_TESTING (industry-agnostic, performance /
            # observability baseline CR 12-1 L4 precedent).
            Capability.PERFORMANCE_TESTING,
            # Phase 9 (cj-style 99번째 wire) — full matrix tenants get
            # CHAOS_ENGINEERING (industry-agnostic, chaos engineering
            # baseline CR 12-1 L4 precedent).
            Capability.CHAOS_ENGINEERING,
            # Phase 10 (cj-style 103번째 wire) — all industries get
            # SLO_ENGINEERING (industry-agnostic, SLO engineering baseline
            # CR 12-1 L4 precedent + CHAOS_ENGINEERING Phase 9 wire +
            # PERFORMANCE_TESTING Phase 8 wire + OBSERVABILITY_* Phase 7
            # wire pattern verbatim).
            Capability.SLO_ENGINEERING,
            # Phase 11 (cj-style 107번째 wire) — full matrix tenants get
            # FINOPS_SHOWBACK + FINOPS_CHARGEBACK (industry-agnostic,
            # FinOps financial reporting baseline CR 12-1 L4 precedent).
            Capability.FINOPS_SHOWBACK,
            Capability.FINOPS_CHARGEBACK,
            # Phase 12 (cj-style 111번째 wire) — full matrix tenants get
            # FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT
            # (industry-agnostic, CR 12-1 L4 precedent).
            Capability.FINOPS_ANOMALY_DETECTION,
            Capability.FINOPS_BUDGET_ALERT,
            # Phase 13 (cj-style 115번째 wire) — full matrix tenants get
            # FINOPS_FORECASTING_CAPACITY_PLANNING (industry-agnostic,
            # CR 12-1 L4 precedent).
            Capability.FINOPS_FORECASTING_CAPACITY_PLANNING,
            # Phase 14 (cj-style 119번째 wire) — full matrix tenants get
            # FINOPS_OPTIMIZATION (industry-agnostic, FinOps
            # ACTIONABLE RECOMMENDATION LAYER EXTENSION of Phase 13
            # forecast baseline CR 12-1 L4 precedent).
            Capability.FINOPS_OPTIMIZATION,
            # Phase 15 (cj-style 123번째 wire) — full matrix tenants get
            # FINOPS_TAG_GOVERNANCE (industry-agnostic, FinOps cost
            # allocation baseline CR 12-1 L4 precedent).
            Capability.FINOPS_TAG_GOVERNANCE,
            # Phase 16 (cj-style 127번째 wire) — FINOPS_REPORTING
            # (industry-agnostic, FinOps executive reporting layer CR 12-1
            # L4 precedent + FINOPS_TAG_GOVERNANCE Phase 15 wire +
            # FINOPS_OPTIMIZATION Phase 14 wire + FINOPS_FORECASTING +
            # FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12 wire
            # + FINOPS Phase 11 wire pattern verbatim). 5-module
            # cross-join (Phase 11~15) + 8 NEW KPI calculations +
            # executive report generator PDF/CSV/Excel + scheduled
            # dispatch KST cron + tenant-scoped executive role RBAC.
            Capability.FINOPS_REPORTING,
            # Phase 17 (cj-style 131번째 wire) — FINOPS_SUSTAINABILITY
            # (industry-agnostic per CR 12-1 L4 precedent + FINOPS_REPORTING
            # Phase 16 wire + FINOPS_TAG_GOVERNANCE Phase 15 wire +
            # FINOPS_OPTIMIZATION Phase 14 wire + FINOPS_FORECASTING +
            # FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12 wire
            # + FINOPS Phase 11 wire pattern verbatim). 6-module cross-rollup
            # (Phase 11~16) + 8 NEW KPI calculations + sustainability report
            # generator PDF/CSV/Excel + scheduled dispatch KST cron +
            # tenant-scoped sustainability role RBAC. Sustainability &
            # carbon reporting applies industry-agnostically per EU CSRD +
            # SEC Climate Disclosure + EU Taxonomy + IFRS S2 + 한국 KSSB.
            Capability.FINOPS_SUSTAINABILITY,
            # Phase 18 (cj-style 135번째 wire) — FINOPS_COMMITMENT
            # (industry-agnostic per CR 12-1 L4 precedent + FINOPS_SUSTAINABILITY
            # Phase 17 wire + FINOPS_REPORTING Phase 16 wire +
            # FINOPS_TAG_GOVERNANCE Phase 15 wire + FINOPS_OPTIMIZATION
            # Phase 14 wire + FINOPS_FORECASTING + FINOPS_ANOMALY_DETECTION
            # + FINOPS_BUDGET_ALERT Phase 12 wire + FINOPS Phase 11 wire
            # pattern verbatim). 7-module cross-rollup (Phase 11~17) +
            # 5-cloud-provider breakdown (AWS + Azure + GCP + Naver + KT) +
            # 8 NEW KPI calculations + commitment report generator
            # PDF/CSV/Excel + scheduled dispatch KST cron + tenant-scoped
            # commitment role RBAC. Cloud commitment management applies
            # industry-agnostically per FinOps Foundation + AWS Cost
            # Optimization Pillar + Azure Cost Optimization + GCP Cost
            # Optimization + 한국 조달청 클라우드 commitment 가이드라인.
            Capability.FINOPS_COMMITMENT,
            # Phase 19 (cj-style 139번째 wire) — FINOPS_PRICING
            # (industry-agnostic per CR 12-1 L4 precedent + FINOPS_COMMITMENT
            # Phase 18 wire + FINOPS_SUSTAINABILITY Phase 17 wire +
            # FINOPS_REPORTING Phase 16 wire + FINOPS_TAG_GOVERNANCE Phase 15
            # wire + FINOPS_OPTIMIZATION Phase 14 wire + FINOPS_FORECASTING +
            # FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12 wire +
            # FINOPS Phase 11 wire pattern verbatim). 8-module cross-rollup
            # (Phase 11~18) + 5-cloud-provider breakdown (AWS + Azure + GCP +
            # Naver + KT) + 6-pricing-model × 4-unit-metric matrix + 8 NEW
            # KPI calculations + pricing report generator PDF/CSV/Excel +
            # scheduled dispatch KST cron + tenant-scoped pricing role RBAC.
            # Pricing & TCO modeling applies industry-agnostically per FinOps
            # Foundation + AWS Pricing Models EDP + Azure Pricing Calculator
            # EA + GCP Pricing Calculator CUD + 한국 공공 조달 가격 가이드라인.
            Capability.FINOPS_PRICING,
            # Phase 20 (cj-style 144번째 wire) — FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION
            # (industry-agnostic per CR 12-1 L4 precedent + FINOPS_PRICING
            # Phase 19 wire + FINOPS_COMMITMENT Phase 18 wire + Phase 17 wire
            # + Phase 16 wire + Phase 15 wire + Phase 14 wire + Phase 13 wire
            # + Phase 12 wire + Phase 11 wire pattern verbatim). 9-module
            # cross-rollup (Phase 11~19) + 5-cloud-provider breakdown +
            # 5-marketplace source breakdown + 9 NEW cost KPI calculations +
            # marketplace report generator + scheduled dispatch KST cron +
            # multi-cloud viewer role RBAC. Multi-cloud cost unified
            # reconciliation applies industry-agnostically per FinOps
            # Foundation Multi-Cloud Cost Management pillar.
            Capability.FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION,
            # Phase 21 (cj-style 151번째 wire) — FINOPS_RESERVED_CAPACITY_PLANNING
            # (industry-agnostic per CR 12-1 L4 precedent +
            # FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION Phase 20 wire +
            # FINOPS_PRICING Phase 19 wire + FINOPS_COMMITMENT Phase 18 wire
            # + FINOPS_SUSTAINABILITY Phase 17 wire + FINOPS_REPORTING Phase
            # 16 wire + FINOPS_TAG_GOVERNANCE Phase 15 wire +
            # FINOPS_OPTIMIZATION Phase 14 wire + FINOPS_FORECASTING
            # Phase 13 wire + FINOPS_ANOMALY_DETECTION +
            # FINOPS_BUDGET_ALERT Phase 12 wire + FINOPS Phase 11 wire
            # pattern verbatim). 5-module composition layer + 6
            # reserved_capacity_tier + 4 execution_strategy + 4 cadence
            # schedule KST pytz + dry-run mode + Epic 12 2FA 챌린지
            # mandatory (high-value threshold 10M KRW/year).
            Capability.FINOPS_RESERVED_CAPACITY_PLANNING,
        }
    ),
}


# ── Exception (mapped to 403 INDUSTRY_NOT_SUPPORTED) ────────
class IndustryCapabilityError(Exception):
    """403 INDUSTRY_NOT_SUPPORTED — tenant's industry does not unlock capability."""

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        current_industry: Industry | None,
        capability: Capability,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"industry {current_industry!r} cannot access capability {capability.value!r}"
        )
        self.tenant_id = tenant_id
        self.current_industry = current_industry
        self.capability = capability
        self.trace_id = trace_id


# ── Public helpers ───────────────────────────────────────────
def industry_supports(industry: Industry, capability: Capability) -> bool:
    """Pure function: does this industry unlock this capability?"""
    return capability in _INDUSTRY_CAPABILITIES.get(industry, frozenset())


def require_capability(capability: Capability):
    """FastAPI dependency factory — returns a dependency that enforces the capability.

    Usage:
        @router.post("/api/v1/bom", dependencies=[Depends(require_capability(Capability.BOM))])

    Reads the tenant's industry via SettingsService.get_tenant_settings and
    raises IndustryCapabilityError (mapped to 403) if unsupported.
    """

    async def _dep(
        ctx: TenantContext = Depends(get_tenant_context),
        session: AsyncSession = Depends(get_session),
    ) -> TenantContext:
        from apps.api.modules.m0_onboarding.services.settings_service import (
            SettingsService,
            TenantSettingsNotFoundError,
        )

        trace_id = str(uuid.uuid4())
        service = SettingsService(session, trace_id=trace_id)
        try:
            row = await service.get_tenant_settings(tenant_id=ctx.tenant_id)
        except TenantSettingsNotFoundError as err:
            # Treat as no industry selected → no capabilities unlocked.
            raise IndustryCapabilityError(
                tenant_id=ctx.tenant_id,
                current_industry=None,
                capability=capability,
                trace_id=trace_id,
            ) from err

        onboarding = dict(row.onboarding or {})
        industry_raw = onboarding.get("industry")
        try:
            industry = Industry(industry_raw) if industry_raw else None
        except ValueError:
            industry = None

        if not industry_supports(industry, capability):
            raise IndustryCapabilityError(
                tenant_id=ctx.tenant_id,
                current_industry=industry,
                capability=capability,
                trace_id=trace_id,
            )
        return ctx

    return _dep


# ── Role gate (AD-10) — owner-only mutations ─────────────────
class ForbiddenRoleError(Exception):
    """403 FORBIDDEN_ROLE — caller's role does not allow this mutation.

    AD-10 + T4.2: only `owner` may run POST/PATCH. member/viewer are
    read-only on product catalog. Mapped to HTTP 403 by main.py global
    handler.
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
        required_role: str,
        trace_id: str,
    ) -> None:
        super().__init__(f"role {role!r} forbidden; required {required_role!r}")
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.role = role
        self.required_role = required_role
        self.trace_id = trace_id


def require_role(required_role: str):
    """FastAPI dependency factory — enforce a minimum role on the route.

    H3 / AD-10 / T4.2 — owner-only mutations. The `role` is read from
    `TenantContext.role` (set by JWT decoding in `get_tenant_context`).

    Usage:
        @router.post(
            "/products",
            dependencies=[Depends(require_role("owner"))],
        )
    """

    async def _dep(
        ctx: TenantContext = Depends(get_tenant_context),
    ) -> TenantContext:
        trace_id = str(uuid.uuid4())
        if ctx.role != required_role:
            raise ForbiddenRoleError(
                tenant_id=ctx.tenant_id,
                user_id=ctx.user_id,
                role=ctx.role,
                required_role=required_role,
                trace_id=trace_id,
            )
        return ctx

    return _dep


def require_any_capability(*allowed_capabilities: Capability):
    """FastAPI dependency factory — enforce ANY of the listed capabilities on the route.

    Story 9.3 (T2 prep + T6 capability-matrix v1.19) — A29 forward-lock
    dual-route gate. M3 orchestrator's POST /api/v1/calc route accepts
    EITHER COST_CALCULATION (manufacturing-kind) OR ABC_CALCULATION
    (service-kind) — service-layer `_resolve_engine_type` further
    discriminates by `tenant.industry == 'service'` for M9 dispatch
    (AD-19 dual-route).

    CR 12-1 L4 precedent — mirrors `require_any_role` multi-role pattern.

    Usage:
        @router.post(
            "/api/v1/calc",
            dependencies=[Depends(
                require_any_capability(
                    Capability.COST_CALCULATION, Capability.ABC_CALCULATION
                )
            )],
        )

    Raises:
        IndustryCapabilityError: 403 INDUSTRY_NOT_SUPPORTED if NONE of the
            allowed capabilities are unlocked by the tenant's industry.
            Mapped to HTTP 403 by main.py global handler.
    """
    allowed = frozenset(allowed_capabilities)

    async def _dep(
        ctx: TenantContext = Depends(get_tenant_context),
        session: AsyncSession = Depends(get_session),
    ) -> TenantContext:
        from apps.api.modules.m0_onboarding.services.settings_service import (
            SettingsService,
            TenantSettingsNotFoundError,
        )

        trace_id = str(uuid.uuid4())
        service = SettingsService(session, trace_id=trace_id)
        try:
            row = await service.get_tenant_settings(tenant_id=ctx.tenant_id)
        except TenantSettingsNotFoundError as settings_err:
            # Treat as no industry selected → no capabilities unlocked.
            # Raise the FIRST capability as the canonical error.
            raise IndustryCapabilityError(
                tenant_id=ctx.tenant_id,
                current_industry=None,
                capability=next(iter(allowed)),
                trace_id=trace_id,
            ) from settings_err

        onboarding = dict(row.onboarding or {})
        industry_raw = onboarding.get("industry")
        try:
            industry = Industry(industry_raw) if industry_raw else None
        except ValueError:
            industry = None

        # ANY-OF semantics: pass if at least one allowed capability is
        # unlocked by the tenant's industry. Otherwise raise the FIRST
        # capability as the canonical 403 error.
        for cap in allowed:
            if industry_supports(industry, cap):
                return ctx
        raise IndustryCapabilityError(
            tenant_id=ctx.tenant_id,
            current_industry=industry,
            capability=next(iter(allowed)),
            trace_id=trace_id,
        )

    return _dep


def require_any_role(*allowed_roles: str):
    """FastAPI dependency factory — enforce role ∈ {allowed_roles} on the route.

    Story 12.4 review P-10: M2 entry gates (consume_challenge_token, etc.)
    need to allow owner OR member (NOT viewer/consultant_proxy). This
    helper is the multi-role complement of `require_role`.

    Usage:
        @router.post(
            "/account/2fa/challenge-tokens/consume",
            dependencies=[Depends(require_any_role("owner", "member"))],
        )
    """
    allowed = frozenset(allowed_roles)

    async def _dep(
        ctx: TenantContext = Depends(get_tenant_context),
    ) -> TenantContext:
        trace_id = str(uuid.uuid4())
        if ctx.role not in allowed:
            raise ForbiddenRoleError(
                tenant_id=ctx.tenant_id,
                user_id=ctx.user_id,
                role=ctx.role,
                required_role="|".join(sorted(allowed)),
                trace_id=trace_id,
            )
        return ctx

    return _dep


# ──────────────────────────────────────────────────────────────────
# Story 10.4 (Epic 10 5번째 진입점, cj-style 33번째 epic 연속) — AD-17
# verbatim "only M2 may call InputPromoter.promote" M2-only gate.
#
# AD-17 invariants:
#   - `InputPromoter.promote(tenant_id, period_key, source_draft_id)` is the
#     canonical promotion port. Only the M2 module authority may invoke it.
#   - Cross-module HTTP access (frontend, owner UI, other modules) MUST be
#     rejected at the FastAPI dependency boundary BEFORE body parsing —
#     this is the 1st line of defense.
#   - The service-layer (kernel `validate_promotion_request`) re-checks
#     `actor_role='m2_service_role'` Literal as the canonical audit anchor —
#     this is the 2nd line of defense.
#   - The audit_logs INSERT (CR 1.1 verbatim — Row 1 + Row 2 audit-first
#     INSERT) carries the actor role as part of the audit baseline.
#
# Mirrors `require_role` factory shape but with a SYNTHETIC service-role
# identifier (`m2_service_role`) rather than a human RBAC role. The M2
# module issues inter-module service-role JWTs distinct from
# owner/member/viewer/consultant_proxy; only those unlock this gate.
# ──────────────────────────────────────────────────────────────────


# Synthetic service-role identifier (M2 module authority). Distinct from
# the 4 human RBAC roles (owner/member/viewer/consultant_proxy).
M2_SERVICE_ROLE: Final[str] = "m2_service_role"


class M2OnlyUserError(Exception):
    """403 INPUT_PROMOTION_M2_ONLY — caller is NOT the M2 module authority.

    AD-17 verbatim: only the M2 module may invoke
    `InputPromoter.promote(...)`. Cross-module HTTP access (frontend,
    owner UI, other modules) is rejected at the FastAPI dependency layer
    with this typed exception. The kernel-side
    `validate_promotion_request` re-checks the `actor_role` Literal as a
    defense-in-depth guard; this HTTP-side gate is the 1st line of
    defense that fires BEFORE body parsing.

    Distinct from `ForbiddenRoleError` (which gates RBAC roles — owner
    / member / viewer / consultant_proxy). The M2 service-role is a
    synthetic identifier, not a human RBAC role, so it gets its own
    typed exception to keep the AD-15 envelope mapping unambiguous.

    Mapped to HTTP 403 INPUT_PROMOTION_M2_ONLY by main.py global
    handler (T4 B4 wire).
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        actual_role: str,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"AD-17 M2-only denied: actual_role={actual_role!r}, "
            f"required={M2_SERVICE_ROLE!r}"
        )
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.actual_role = actual_role
        self.trace_id = trace_id


async def get_current_m2_user(
    ctx: TenantContext = Depends(get_tenant_context),
) -> TenantContext:
    """FastAPI dependency — AD-17 verbatim M2-only gate.

    Verifies the authenticated session carries `role='m2_service_role'`
    in its JWT. The M2 module issues inter-module service-role JWTs
    (distinct from owner/member/viewer/consultant_proxy); only those
    tokens unlock this gate.

    Returns the `TenantContext` so the route can use it directly.
    Raises `M2OnlyUserError` (403 INPUT_PROMOTION_M2_ONLY) otherwise —
    the Pydantic envelope `PromoteM2OnlyError` carries the wire shape
    (`status='m2_only'`, `code='INPUT_PROMOTION_M2_ONLY'`, etc.).

    Layer ordering in the route:
        @router.post(
            "/ai/promote",
            dependencies=[
                Depends(require_pipa_review),   # 1st: AD-22 + D-10-3-DEFER-6
                Depends(get_current_m2_user),   # 2nd: AD-17 M2-only
                Depends(require_capability(Capability.AI_INSIGHT)),  # 3rd: industry
            ],
        )

    The dependency returns the same `TenantContext` so all three gates
    stack without re-fetching the JWT. Mirrors `require_role("owner")`
    shape but with a synthetic service-role identifier rather than a
    human RBAC role.
    """
    trace_id = str(uuid.uuid4())
    if ctx.role != M2_SERVICE_ROLE:
        raise M2OnlyUserError(
            tenant_id=ctx.tenant_id,
            user_id=ctx.user_id,
            actual_role=ctx.role,
            trace_id=trace_id,
        )
    return ctx


# Alias for naming consistency with the `require_*` factory family.
# Both names point to the same dependency.
require_m2_only = get_current_m2_user
