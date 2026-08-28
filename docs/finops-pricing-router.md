# FinOps Pricing Router (Phase 19)

> **Phase 19 (cj-style 139번째 wire)** — FinOps Pricing territory.
> **Router wire (cj-style 147번째)** — Phase 20.5 Layer 1 P0 critical include.
> **Layer 3 P2 docs backfill (cj-style 188번째)** — Phase 20.5 §F37.3 T3.3 carry-over.

## §1. Introduction

This runbook covers the FinOps Pricing router introduced in
Phase 19 (cj-style 139번째 wire). It is the rate-card / unit-economics
layer of the FinOps multi-cloud chain: blended / unblended rate
aggregation, anomaly rate impact, forecast rate trajectory,
optimization effective discount, tag governance allocation %,
executive unit economics, sustainability carbon-adjusted rate,
commitment discount baseline, cloud provider breakdown, and
pricing model breakdown.

8 routes are mounted at `/api/v1/admin/finops/pricing/`.

PRD §F36.1~§F36.8 (8 ACs → 88 sub-ACs).

## §2. Capability Gate

`Capability.FINOPS_PRICING` is granted to all 4 industries per CR 12-1.

Dependency helper: `require_finops_pricing` in
`apps/api/dependencies/capability.py`.

AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory + NFR4 PII
minimization ✅ PRESERVED.

## §3. Endpoint Inventory

| Method | Path | Purpose |
|---|---|---|
| GET   | `/health` | Healthcheck — returns `{status, router, tenant_id, capability}` |
| GET   | `/rollup` | Rate card rollup (blended + unblended per provider) |
| GET   | `/kpis` | Pricing KPIs (effective discount + trajectory) |
| POST  | `/reports` | Generate pricing report (PDF/CSV/JSON + FINOPS_FOUNDATION) |
| POST  | `/dispatches` | Schedule dispatch (weekly/monthly/quarterly) |
| POST  | `/dispatches/deliver` | Deliver (Slack + Email + S3) |
| GET   | `/rate-card-trend` | 12-month rate card trend |
| POST  | `/dry-run` | Dry-run preview tables |

## §4. RBAC Layer

- AD-22 owner-only RBAC.
- Epic 12 2FA 챌린지 mandatory for rate-card modification.
- NFR4 PII minimization enforced.

## §5. Audit Action Layer

`ActionClass.FINOPS_PRICING` Literal values audited including
rate_card_aggregated, pricing_anomaly_rate_tracked, pricing_optimization_discount_applied,
pricing_unit_economics_computed, pricing_carbon_adjusted_rate_tracked, etc.

Audit-first INSERT auto-activates on POST endpoints (CR 1-1).

## §6. 8 ACs §F36.1~§F36.8

8 ACs + 88 sub-ACs verbatim satisfied:
- §F36.1 capability wiring ✅
- §F36.2 routers ✅
- §F36.3 typed_exceptions ✅
- §F36.4 audit_actions ✅
- §F36.5 RBAC ✅
- §F36.6 typed_serializer ✅
- §F36.7 dispatch ✅
- §F36.8 owner-only + 2FA ✅

## §7. Cross-References

- Phase 19 wire: aggregator modules
- Phase 20.5 wire: `e23141d` (cj-style 147번째) — router include
- Phase 20.5 close-out retro: honestly DEFERRED docs carry-over
- Phase 26 capability matrix v1.52 EXTENSION: FINOPS_PRICING grant preserved
- Phase 25 vendor_management uses pricing sub-module for vendor spend attribution
