# FinOps Sustainability Router (Phase 17)

> **Phase 17 (cj-style 131번째 wire)** — FinOps Sustainability territory.
> **Router wire (cj-style 147번째)** — Phase 20.5 Layer 1 P0 critical include.
> **Layer 3 P2 docs backfill (cj-style 188번째)** — Phase 20.5 §F37.3 T3.1 carry-over.

## §1. Introduction

This runbook covers the FinOps Sustainability router introduced in
Phase 17 (cj-style 131번째 wire). It is the green-IT / carbon-emissions
layer of the FinOps multi-cloud chain: data center PUE, renewable
energy %, carbon offsets, scope 1/2/3 emissions rollups, and CSRD /
GRI / SASB / TCFD / CDP report generation.

8 routes are mounted at `/api/v1/admin/finops/sustainability/`.

PRD §F36.1~§F36.8 (8 ACs → 88 sub-ACs).

## §2. Capability Gate

`Capability.FINOPS_SUSTAINABILITY` is granted to all 4 industries
per CR 12-1 L4 industry-agnostic precedent.

Dependency helper: `require_finops_sustainability` in
`apps/api/dependencies/capability.py`.

AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory + NFR4 PII
minimization ✅ PRESERVED.

## §3. Endpoint Inventory

| Method | Path | Purpose |
|---|---|---|
| GET   | `/health` | Healthcheck — returns `{status, router, tenant_id, capability}` |
| GET   | `/rollup` | Carbon emissions rollup (scope1/2/3 + intensity) |
| GET   | `/kpis` | Sustainability KPIs (PUE + renewable + offsets) |
| POST  | `/reports` | Generate sustainability report (PDF/CSV/JSON + 5 framework) |
| POST  | `/dispatches` | Schedule dispatch (monthly/quarterly/half-yearly/yearly) |
| POST  | `/dispatches/deliver` | Deliver (Slack + Email + S3 archive) |
| GET   | `/carbon-trend` | 12-month scope1/2/3 trend |
| POST  | `/dry-run` | Dry-run preview tables |

## §4. RBAC Layer

- AD-22 owner-only RBAC.
- Epic 12 2FA 챌린지 mandatory for report generation + dispatch delivery.
- NFR4 PII minimization enforced (no personal data in carbon rollups).

## §5. Audit Action Layer

12 NEW `ActionClass.FINOPS_SUSTAINABILITY` Literal values audited:

`sustainability_rollup_generated`, `sustainability_kpis_computed`,
`sustainability_report_generated`, `sustainability_report_scheduled`,
`sustainability_report_delivered`, `sustainability_carbon_trend_tracked`,
`sustainability_dry_run_executed`, `sustainability_pue_metric_tracked`,
`sustainability_renewable_pct_tracked`, `sustainability_carbon_offset_tracked`,
`sustainability_emissions_scope1_tracked`, `sustainability_emissions_scope3_tracked`.

Audit-first INSERT auto-activates on POST endpoints (CR 1-1).

## §6. 8 ACs §F36.1~§F36.8

- §F36.1 Layer 1 capability_wiring ✅
- §F36.2 Layer 2 routers ✅
- §F36.3 Layer 3 typed_exceptions ✅
- §F36.4 Layer 4 audit_actions ✅
- §F36.5 Layer 5 RBAC ✅
- §F36.6 Layer 6 typed_serializer ✅
- §F36.7 Layer 7 dispatch ✅
- §F36.8 Layer 8 owner-only + 2FA 챌린지 ✅

## §7. Cross-References

- Phase 17 wire: `97cfe4e` (cj-style 131st) — aggregator modules
- Phase 20.5 wire: `e23141d` (cj-style 147번째) — router include
- Phase 20.5 close-out retro: honestly DEFERRED docs carry-over
- Phase 26 capability matrix v1.52 EXTENSION: FINOPS_SUSTAINABILITY grant preserved
