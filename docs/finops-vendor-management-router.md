# FinOps Vendor Management Router (Phase 25)

> **Phase 25 wire** — FinOps Vendor Management territory.
> **Layer 3 P2 docs backfill (cj-style 189번째)** — Phase 21~26 carry-over sprint.

## §1. Introduction

This runbook covers the FinOps Vendor Management router. It is the supplier
layer of the FinOps chain: vendor catalog CRUD, blacklisting, weighted vendor
selection, contract lifecycle advancement, and dry-run scoring.

7 distinct paths (9 operations) are mounted at `/api/finops/vendor-management/`.

Drift detector: `tests/api/modules/finops/test_phase_25_vendor_management_router.py`
(8 pytest cases).

## §2. Capability Gate

`Capability.FINOPS_VENDOR_MANAGEMENT` (`finops_vendor_management`) is granted to
all 4 industries per CR 12-1 L4 industry-agnostic precedent.

Dependency helper: `require_finops_vendor_management` in
`apps/api/dependencies/capability.py` — applied as an explicit
`Depends(require_finops_vendor_management)` on every endpoint.

AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory + NFR4 PII minimization ✅ PRESERVED.

## §3. Endpoint Inventory

| Method | Path | Purpose |
|---|---|---|
| POST  | `/vendors` | Create a vendor (audit-first INSERT, HTTP 201) |
| GET   | `/vendors` | List vendors for the tenant (RLS), filterable by category/status |
| GET   | `/vendors/{vendor_id}` | Read one vendor |
| PATCH | `/vendors/{vendor_id}` | Partial score update |
| POST  | `/vendors/{vendor_id}/blacklist` | Blacklist a vendor with reason + severity |
| POST  | `/selection` | Weighted vendor selection across candidates |
| POST  | `/contracts` | Create a contract with an approval chain |
| POST  | `/contracts/{contract_id}/advance` | Advance contract lifecycle |
| POST  | `/dry-run` | Dry-run vendor scoring (no persistence) |

## §4. Request Model Contract

Seven Pydantic request models are declared in `vendor_management_routes.py`:
`CreateVendorRequest`, `UpdateVendorRequest`, `BlacklistVendorRequest`,
`VendorSelectionRequest`, `CreateContractRequest`, `AdvanceContractRequest`,
`DryRunRequest`.

The five score fields (`cost_score`, `performance_score`, `reliability_score`,
`compliance_score`, `strategic_fit_score`) are bounded `0.0 ≤ x ≤ 100.0` via
`Field(ge=..., le=...)`; `contract_count` is `ge=0`; `approval_chain` requires
at least one entry (`min_length=1`).

**Honest drift note.** Unlike Phase 21, these models do **not** declare
`ConfigDict(extra="forbid")`, so unknown keys are silently ignored (Pydantic's
default). The drift detector pins this *actual* state rather than the desired
one, so tightening to `forbid` shows up as a reviewed source change instead of
a silent behaviour shift. Tightening is a follow-up source sprint, not a
test-only edit.

## §5. Risk Bands and Caps

Defined in `apps/api/modules/finops/vendor_management/serializers.py`:

| Constant | Value | Meaning |
|---|---|---|
| `VENDOR_MANAGEMENT_ENGINE_MODEL_VERSION` | `1.0.0` | Engine model version |
| `VENDOR_RISK_LOW_THRESHOLD` | `30.0` | Below → low risk |
| `VENDOR_RISK_MEDIUM_THRESHOLD` | `60.0` | 30~60 → medium risk |
| `VENDOR_RISK_HIGH_THRESHOLD` | `80.0` | ≥80 → high risk + escalation |
| `MAX_VENDORS_PER_TENANT` | `5,000` | Tenant scale cap |
| `MAX_CONTRACTS_PER_VENDOR` | `100` | Per-vendor contract cap |
| `MAX_CONTRACT_OVERRIDE_KRW` | `10,000,000` | Override requires owner 2FA |
| `TOTAL_VERIFICATION_TOLERANCE_KRW` | `0.01` | Contract-sum tolerance (±0.01 KRW) |
| `AUTO_RENEWAL_WINDOW_DAYS` | `90` | PRD §F41.3 auto-renewal window |

Enum frozensets — `ALL_VENDOR_STATUSES`, `ALL_VENDOR_CATEGORIES`,
`ALL_VENDOR_CONTRACT_LIFECYCLES`, `ALL_VENDOR_PERFORMANCE_SEVERITIES`,
`ALL_VENDOR_SELECTION_MODES`, `ALL_VENDOR_APPROVAL_STEP_STATUSES` — each with a
`*_VALUES` alias.

## §6. Audit Action Layer

Audit-first INSERT auto-activates on vendor creation, score updates,
blacklisting, selection, contract creation, and lifecycle advancement (CR 1-1).

Tenant scoping resolves through `_tenant_id_from_request()`, which reads
`request.state.tenant_id` and falls back to the nil UUID when the request scope
is unavailable (module-level import safety).

## §7. Router Include

Mounted in `apps/api/main.py` via `app.include_router(vendor_management_router)`,
ordered last in the Phase 21~25 block — AFTER `budget_planning_router`
(Phase 24), since vendor contracts check against budget ceilings.

Include smoke test: `tests/api/modules/finops/test_phase_21_26_router_include.py`.

## §8. Cross-References

- Phase 19 pricing router — vendor spend attribution input
- Phase 24 budget planning — `budget_ceiling_krw` enforcement
- Phase 26 capability matrix v1.52 EXTENSION — `FINOPS_VENDOR_MANAGEMENT` grant preserved
- Typed exception `apps/api/core/errors.py:3358` — raised by `get_vendor_endpoint()`
