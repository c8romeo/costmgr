# FinOps Cloud Commitment Router (Phase 18)

> **Phase 18 (cj-style 135번째 wire)** — FinOps Cloud Commitment territory.
> **Router wire (cj-style 147번째)** — Phase 20.5 Layer 1 P0 critical include.
> **Layer 3 P2 docs backfill (cj-style 188번째)** — Phase 20.5 §F37.3 T3.2 carry-over.

## §1. Introduction

This runbook covers the FinOps Cloud Commitment router introduced in
Phase 18 (cj-style 135번째 wire). It is the cloud commitment discount /
utilization / coverage layer of the FinOps multi-cloud chain: AWS
Savings Plans + GCP Committed Use Discounts + Azure Savings Plans +
Oracle Universal Credits + Alibaba reservations aggregation, with
auto-renewal decision support and idle-commitment detection.

8 routes are mounted at `/api/v1/admin/finops/commitment/`.

PRD §F36.1~§F36.8 (8 ACs → 88 sub-ACs).

## §2. Capability Gate

`Capability.FINOPS_COMMITMENT` is granted to all 4 industries per CR 12-1.

Dependency helper: `require_finops_commitment` in
`apps/api/dependencies/capability.py`.

AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory + NFR4 PII
minimization ✅ PRESERVED.

## §3. Endpoint Inventory

| Method | Path | Purpose |
|---|---|---|
| GET   | `/health` | Healthcheck — returns `{status, router, tenant_id, capability}` |
| GET   | `/rollup` | Commitment inventory rollup (5 cloud provider cross-join) |
| GET   | `/kpis` | Commitment KPIs (utilization + coverage + savings) |
| POST  | `/reports` | Generate commitment report (PDF/CSV/JSON + FINOPS_FOUNDATION) |
| POST  | `/dispatches` | Schedule dispatch (monthly/quarterly/half-yearly/yearly) |
| POST  | `/dispatches/deliver` | Deliver (MS Teams + Slack + Email + S3) |
| GET   | `/utilization-trend` | 12-month utilization trend |
| POST  | `/dry-run` | Dry-run preview tables |

## §4. RBAC Layer

- AD-22 owner-only RBAC.
- Epic 12 2FA 챌린지 mandatory for purchase recommendations.
- NFR4 PII minimization enforced (no personal data in commitment rollups).

## §5. Audit Action Layer

`ActionClass.FINOPS_COMMITMENT` Literal values audited including
commitment_inventory_aggregated, commitment_recommender_executed,
commitment_renewal_decision_made, commitment_idle_detected, etc.

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

- Phase 18 wire: `fc646ac` (cj-style 135th) — aggregator modules
- Phase 20.5 wire: `e23141d` (cj-style 147번째) — router include
- Phase 20.5 close-out retro: honestly DEFERRED docs carry-over
- Phase 26 capability matrix v1.52 EXTENSION: FINOPS_COMMITMENT grant preserved
