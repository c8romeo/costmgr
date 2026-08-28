# FinOps Multi-Cloud Cost Unified Reconciliation Router (Phase 20 + AD-47)

> **Phase 20 (cj-style 144번째 wire)** — FinOps Multi-Cloud Cost Unified Reconciliation territory.
> **AD-47** — multi-cloud-cost-unified-reconciliation 신규 (Phase 20.5 §F37.3 T3.6 carry-over).
> **Router wire (cj-style 147번째)** — Phase 20.5 Layer 1 P0 critical include.
> **Layer 3 P2 docs backfill (cj-style 188번째)** — Phase 20.5 §F37.3 T3.4 + T3.6 carry-over.

## §1. Introduction

This runbook covers the FinOps Multi-Cloud Cost Unified Reconciliation
router introduced in Phase 20 (cj-style 144번째 wire). It is the
cross-cloud reconciliation layer that ties together rate-card
discrepancies, cost-source attribution, market-place SaaS pricing
integration, and an autonomous negotiation bot trigger for
multi-cloud procurement savings.

8 routes are mounted at `/api/v1/admin/finops/multi-cloud/`.

PRD §F36.1~§F36.8 (8 ACs → 88 sub-ACs).

## §2. AD-47 — Multi-Cloud Cost Unified Reconciliation

AD-47 multi-cloud-cost-unified-reconciliation 신규 (Phase 20.5 §F37.3 T3.6).

The router aggregates 5 sub-modules:
1. `rate_card_reconciliation_aggregator` — rate card reconciliation
2. `cost_reconciliation_aggregator` — 9-module cost attribution
3. `negotiation_bot` — autonomous multi-cloud procurement bot
4. `blended_unblended_tracker` — blended vs unblended tracking
5. `marketplace_saas_pricing_integrator` — marketplace SaaS pricing integration

The reconciliation engine emits a `MultiCloudCostReconciliation`
TypedDict with **19 strict fields** (Phase 20 typed-invariants
verbatim). Any missing field raises `MultiCloudCostReconciliationError`
(CR 11-4 P-015 verbatim 5-layer defense).

## §3. Capability Gate

`Capability.FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION` is granted
to all 4 industries per CR 12-1.

Dependency helper: `require_finops_multi_cloud` in
`apps/api/dependencies/capability.py`.

AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory + NFR4 PII
minimization ✅ PRESERVED.

## §4. Endpoint Inventory

| Method | Path | Purpose |
|---|---|---|
| GET   | `/health` | Healthcheck — returns `{status, router, tenant_id, capability}` |
| GET   | `/rate-card-reconciliations` | Rate-card discrepancies aggregation |
| GET   | `/cost-reconciliations` | Multi-cloud cost attributions (9-module) |
| POST  | `/negotiation-bot/trigger` | Trigger negotiation bot (provider + savings threshold) |
| GET   | `/blended-unblended` | Blended vs unblended tracking |
| POST  | `/marketplace-saas/integrate` | Marketplace SaaS pricing integration |
| POST  | `/dispatches` | Schedule multi-cloud dispatch (weekly + monthly) |
| POST  | `/dry-run` | Dry-run preview tables |

## §5. RBAC Layer

- AD-22 owner-only RBAC for all routes.
- Epic 12 2FA 챌린지 mandatory for `negotiation-bot/trigger` and
  `marketplace-saas/integrate` (financial-impact endpoints).
- NFR4 PII minimization enforced (no personal data in cost rollups).

## §6. Audit Action Layer

`ActionClass.FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION` Literal
values audited including
rate_card_reconciled, cost_reconciled, negotiation_bot_triggered,
blended_unblended_tracked, marketplace_saas_integrated, etc.

Audit-first INSERT auto-activates on POST endpoints (CR 1-1).

## §7. 8 ACs §F36.1~§F36.8

8 ACs + 88 sub-ACs verbatim satisfied:
- §F36.1 capability wiring ✅
- §F36.2 routers ✅
- §F36.3 typed_exceptions (19-field strict invariant) ✅
- §F36.4 audit_actions ✅
- §F36.5 RBAC ✅
- §F36.6 typed_serializer ✅
- §F36.7 dispatch ✅
- §F36.8 owner-only + 2FA ✅

## §8. Cross-References

- Phase 20 wire: `52dad7f` (cj-style 144th) — aggregator modules
- Phase 20.5 wire: `e23141d` (cj-style 147번째) — router include
- Phase 20.5 close-out retro: AD-47 carry-over 결정 wire
- Phase 26 capability matrix v1.52 EXTENSION: capability grant preserved
