# ABC 100% Validation (Story 9.1, Epic 9)

> PRD §F9.1 verbatim: **"원가풀 행 합·활동 열 합·동인 합 모두 100% 가드"**.
> Epic 9 (ABC / TDABC Engine — Service Business) 1번째 진입점.
>
> **baseline_commit:** `091026f` (Story 8.3 DONE tip)
> **cj-style:** Epic 9 1번째 진입점 (cj-style 4-story 분할: 9-1 + 9-2 + 9-3 + 9-4 + Epic 9 close-out retro 5번째 진입점)

## What is the 100% 가드?

The "100% 가드" (100% guard) is the constraint that 3 ABC layer sums
must equal 100% for the calculation engine to be "unlocked". This is
the **[계산]이 잠기는 것** (calculation is locked) mechanism per
PRD §F9.1 verbatim.

| Layer | Formula | Example |
|---|---|---|
| **cost_pool** | Σ(department allocation_pcts) = 100% | `[25, 25, 25, 25]` → 100% ✅ |
| **activity** | Σ(activity activity_pcts) = 100% | `[50, 50]` → 100% ✅ |
| **driver** | Σ(driver driver_pcts) = 100% | `[60, 40]` → 100% ✅ |

When **all 3 layers** sum to 100% → `all_valid=True` → 계산 활성화 (calculation unlocked).
When **any layer** does NOT sum to 100% → `all_valid=False` → 계산 잠김 (calculation locked).

## Capability gate (v1.18)

`Capability.ABC_CALCULATION` is **industry-agnostic** — granted to all 4
canonical industries (manufacturing 3종 ✅ + service-only ✅).
This follows the CR 12-1 L4 precedent: ABC is operational baseline
infrastructure, not a manufacturing-specific feature.

Drift detector: `tests/integration/test_capability_matrix_v1_18_drift.py`.

## 4 NEW endpoints (PRD §F9.1)

| Endpoint | Purpose | Envelope on failure |
|---|---|---|
| `POST /api/v1/abc/cost-pools` | 원가풀 행 합 100% 가드 검증 | 422 `COST_POOL_INVALID_SUM` |
| `POST /api/v1/abc/activities` | 활동 열 합 100% 가드 검증 | 422 `ACTIVITY_INVALID_SUM` |
| `POST /api/v1/abc/drivers/validate` | 동인 합 100% 가드 검증 | 422 `DRIVER_INVALID_SUM` |
| `POST /api/v1/abc/validate` | 3-layer 100% 가드 동시 검증 | 422 (per-layer) / 404 `ABC_VALIDATION_NOT_FOUND` |

## Wire contract

### POST /api/v1/abc/validate (main entry point)

**Request body:**

```json
{
  "cost_pool_id": "cp-001",
  "activity_id": "act-001",
  "cost_pool": ["25", "25", "25", "25"],
  "activities": ["50", "50"],
  "drivers": ["60", "40"]
}
```

**Response body (200 OK):**

```json
{
  "cost_pool_id": "cp-001",
  "activity_id": "act-001",
  "all_valid": true,
  "layers": [
    {
      "target": "cost_pool",
      "sum_pct": "100",
      "count": 4,
      "is_valid": true,
      "hash": "sha256:abc123...",
      "message_ko": null
    },
    {
      "target": "activity",
      "sum_pct": "100",
      "count": 2,
      "is_valid": true,
      "hash": "sha256:def456...",
      "message_ko": null
    },
    {
      "target": "driver",
      "sum_pct": "100",
      "count": 2,
      "is_valid": true,
      "hash": "sha256:ghi789...",
      "message_ko": null
    }
  ]
}
```

### Korean SSOT (CR 11-4 D-002 ko-KR.json SSOT)

```typescript
// apps/web/lib/m9-abc-validation.ts
ABC_COST_POOL_INVALID_SUM_KO = "원가풀 행 합이 100%가 아닙니다";
ABC_ACTIVITY_INVALID_SUM_KO = "활동 열 합이 100%가 아닙니다";
ABC_DRIVER_INVALID_SUM_KO = "동인 합이 100%가 아닙니다";
ABC_VALIDATION_NOT_FOUND_KO = "ABC 검증 대상을 찾을 수 없습니다";
```

These match the backend constants in
`apps/api/modules/m9_abc/exceptions.py`.

## Architecture (A19 cohesion pattern 6번째 surface)

```
[UI: AbcValidationPanel + AbcValidationForm]
   ↓ POST /api/v1/abc/validate
HTTP layer (apps/api/modules/m9_abc/handlers.py)
   ↓ 3-layer defense: require_capability + require_role
Service layer (apps/api/modules/m9_abc/services/abc_validation_service.py)
   ↓ validate_abc_pct_list (CR 12-5 L3)
   ↓ _to_validation_state boundary (CR 12-1 L3)
Pure kernel (packages/cost_engine/abc_engine.py)
   ↓ validate_100_percent_guard (4 funcs + 3 frozen dataclasses + 4 typed exceptions)
   ↓ compute_validation_hash (V8 determinism sha256:64-hex)
JSON-safe serializer (packages/services/m9_abc/abc_validation_serializers.py)
   ↓ serialize_validation_state (CR 11-3 ALLOWED_SERVICE_SUBMODULES)
UI rendering (AbcValidationGuardBadge + AbcValidationStatus)
```

## 9-1 honestly DEFER (A26 forward-lock)

9-1 = validation only, NO INSERT/UPDATE/DELETE on persistent storage.
The validation layer is the **pre-condition** for ABC calculation
engines (CCR compute + ABC allocation) that come in Stories 9-2 + 9-3.

| DEFER ID | Description | Forward-lock target |
|---|---|---|
| D-9-1-DEFER-1 | CCR compute | Story 9-2 |
| D-9-1-DEFER-2 | ABC allocation engine | Story 9-3 |
| D-9-1-DEFER-3 | M3 endpoint dispatch (AD-19) | Story 9-3 |
| D-9-1-DEFER-4 | Cost Object Breakdown | Story 9-2 |
| D-9-1-DEFER-5 | Multi-industry ABC (§14.B Non-Goal #1) | (none) |
| D-9-1-DEFER-6 | Playwright E2E | carry-over sprint |

## Cross-references

- `packages/cost_engine/abc_engine.py` — pure kernel (A19 cohesion pattern 6번째)
- `apps/api/modules/m9_abc/handlers.py` — 4 NEW endpoints
- `apps/api/modules/m9_abc/services/abc_validation_service.py` — orchestrator
- `apps/api/modules/m9_abc/schemas.py` — 5 NEW Pydantic v2 models
- `apps/api/modules/m9_abc/exceptions.py` — 4 NEW typed exceptions + 4 Korean SSOT
- `apps/api/main.py` — 4 NEW @app.exception_handler decorators
- `apps/api/core/capability.py` — `Capability.ABC_CALCULATION` enum + 4-industry grants
- `packages/services/m9_abc/abc_validation_serializers.py` — JSON-safe thin serializer
- `apps/web/lib/m9-abc-validation.ts` — TS mirror (types + validators)
- `apps/web/lib/m9-abc-validation-schema.ts` — TS validation schema
- `apps/web/components/m9-abc/AbcValidationPanel.tsx` — main Client Component
- `apps/web/components/m9-abc/AbcValidationForm.tsx` — 3-input form
- `apps/web/components/m9-abc/AbcValidationStatus.tsx` — single-layer status
- `apps/web/components/m9-abc/AbcValidationGuardBadge.tsx` — 3-layer guard badge
- `apps/web/messages/ko-KR.json` — NEW `abc_validation` namespace (29 strings)
- `apps/web/app/[locale]/(dashboard)/budget/abc-validation/page.tsx` — RSC page
- `tests/cost_engine/test_abc_engine*.py` — 47 pure kernel cases
- `tests/services/test_m9_abc_validation_service.py` — 30 service-layer cases
- `tests/api/m9_abc/test_abc_validation_handlers.py` — 20 handler + schema cases
- `tests/integration/test_capability_matrix_v1_18_drift.py` — 12 capability pin cases
- `apps/web/__tests__/lib/m9-abc-validation-schema-parity.test.ts` — 33 TS parity cases
- `apps/web/__tests__/components/m9-abc.*.test.tsx` — 13 component cases

## Wire change history

- **2026-08-16 (Story 9.1)** — Initial wire. A19 cohesion pattern 6번째
  surface (`abc_engine.py`). 4 NEW routes + 4 NEW typed exception envelopes +
  1 NEW capability (v1.18). 6 honestly DEFER to 9-2 / 9-3 / carry-over.