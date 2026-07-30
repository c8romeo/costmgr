# Onboarding JSONB Schema (Story 1.2)

> **Canonical reference** for the `tenant_settings.onboarding` JSONB namespace.
> Enforced by `apps/api/core/jsonb_schemas.py` (validator) +
> `apps/api/modules/m0_onboarding/schemas.py` (per-field Pydantic models).

## 1. Aggregate layout

`tenant_settings` is one row per tenant (created in Story 0.2 signup).
AD-23 reserves four JSONB namespaces: `onboarding` / `baseline` / `abc` / `ai`.
M0 onboarding owns `onboarding.*` exclusively.

```json
{
  "industry": "manufacturing",
  "is_initial": false,
  "selected_at": "2026-07-25T08:00:00Z",

  "fiscal_year_start": "2026-01",
  "currency": "KRW",
  "language": "ko-KR",
  "allocation_criteria": {
    "direct_indirect":  { "completed": true, "count": 5, "last_updated": "2026-08-01T00:00:00Z" },
    "fixed_variable":   { "completed": true, "count": 5, "last_updated": "2026-08-01T00:00:00Z" },
    "drivers":          { "completed": false, "count": 0, "last_updated": null }
  }
}
```

## 2. Field rules

| Field | Type | Rule | Source | AD/Story |
|---|---|---|---|---|
| `industry` | `string` enum | one of `manufacturing` / `service` / `manufacturing_service` / `manufacturing_service_other` | Story 1.1 | AD-23, PRD §4.1 |
| `is_initial` | `bool` | `true` only on first write (Story 1.1 F-2) | Story 1.1 | — |
| `selected_at` | `string` ISO-8601 UTC | must be parseable + not materially future (F-15/16) | Story 1.1 | A1 |
| `fiscal_year_start` | `string` `YYYY-MM` | month ∈ 01..12 | Story 1.2 | A1, AD-24 |
| `currency` | `string` enum | one of `KRW` / `USD` | Story 1.2 | A6, AD-8 |
| `language` | `string` enum | MVP is `ko-KR` only (NFR-18) | Story 1.2 | NFR-18, ux-locked-decisions §4 |
| `allocation_criteria.direct_indirect` | object | `{completed: bool, count: int ≥ 1, last_updated: ISO-8601}` | Story 1.2 | PRD §8.M0(b) |
| `allocation_criteria.fixed_variable`  | object | same shape | Story 1.2 | PRD §8.M0(b) |
| `allocation_criteria.drivers`         | object | same shape | Story 1.2 | PRD §8.M0(b), A11 |

## 3. Industry-conditional completion (PRD §8.M0(b))

The `[계산]` button stays disabled until **all four fields** are saved AND
**every required criterion** has `count ≥ 1`.

| Industry | `direct_indirect` | `fixed_variable` | `drivers` |
|---|---|---|---|
| `manufacturing` (①) | ✅ required | ✅ required | ⛔ skipped (no ABC engine) |
| `service` (②) | ✅ required | ✅ required | ✅ required |
| `manufacturing_service` (③) | ✅ required | ✅ required | ✅ required |
| `manufacturing_service_other` (④) | ✅ required | ✅ required | ✅ required |

Computed by `packages.services.m0_onboarding.settings_completion.compute_completion()`.

## 4. Validator entrypoints

| Caller | Function | Behavior |
|---|---|---|
| Service layer writes | `enforce_onboarding_schema(jsonb, trace_id, partial=True)` | Raises `OnboardingValidationError` → 400 JSONB_SCHEMA_VIOLATION |
| Service layer reads (defensive) | `validate_onboarding_schema(jsonb)` | Returns list of `OnboardingSchemaError` (empty = clean) |
| Tests | `validate_onboarding_schema(jsonb, partial=False)` | Asserts every canonical field is present + valid |

## 5. Migration history

| Migration | Purpose |
|---|---|
| `0001_tenants_users_memberships_settings.py` | Creates `tenant_settings` + JSONB columns (Story 0.2). |
| `0002_tenant_settings_onboarding_defaults.py` | Adds JSONB default + GIN index (Story 1.1). |
| `0003_settings_version_bigint.py` | `settings_version` int4 → int8 (Story 1.1 F-17). |
| `0004_tenant_settings_onboarding_extend.py` | Wizard JSONB schema check (Story 1.2). |

## 6. A7 (전진법) locking

`fiscal_year_start` and `currency` follow the same A7 lock as `industry`
(see `docs/onboarding-flow.md`):
- 7-day grace window after first save.
- After first calculation (`last_calc_date` set) → 409 FISCAL_YEAR_LOCKED /
  CURRENCY_LOCKED regardless of grace.

See `apps/api/modules/m0_onboarding/services/settings_service.py`
methods `update_onboarding_field` / `update_allocation_criteria`.

## 7. References

- [Source: `docs/conventions.md#AD-23`] — One tenant settings aggregate
- [Source: `docs/conventions.md#AD-8`] — Monetary types
- [Source: `prd.md#8.M0(b)`] — Calc-block enforcement
- [Source: `prd.md#3.A1`] — Fiscal year axiom
- [Source: `prd.md#3.A7`] — 전진법
- [Source: `prd.md#3.A11`] — CCR definition (allocation criteria source)
- [Source: `apps/api/core/jsonb_schemas.py`] — Validator implementation
- [Source: `packages/services/m0_onboarding/settings_completion.py`] — Pure completion function