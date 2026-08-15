# Virtual Budget Period Key (AD-24 §6.3 — Story 8.1)

**Status**: SPEC WIRE (cj-style atomic) — Epic 8 Story 8.1 (2026-08-15)
**Owner**: Epic 8 (CVP/BEP Simulation + Budget)
**Pattern Source**: PRD §F8.1 + §15 NON-GOAL #2 + AD-24 §6.3

---

## 1. 개요 (Overview)

The M8 budget module introduces a NEW virtual period key type —
**distinct from the real fiscal period key** (§6.1 AD-24).

| Type | Pattern | Example | Module Scope |
|------|---------|---------|--------------|
| Real (실측 월) | `^\d{4}-(0[1-9]|1[0-2])$` | `2026-07` | M2 / M3 / M11 (close) |
| **Virtual (예산 시뮬레이션)** | `^\d{4}-(0[1-9]|1[0-2])#B([1-9]\d*)$` | `2026-07#B1` | **M8 only (8.1)** |

The `#B<n>` suffix disambiguates multiple budget scenarios within the
same real fiscal period. 1차 MVP supports `n=1` only — multi-scenario
comparison is deferred to Story 8.2 (cj-style follow-up sprint).

---

## 2. SSOT (Single Source of Truth)

### 2.1 Pure Kernel (Python)

**File**: `packages/cost_engine/budget_period_key.py`

```python
REAL_PERIOD_KEY_PATTERN: Final[str] = r"^\d{4}-(0[1-9]|1[0-2])$"
VIRTUAL_BUDGET_PERIOD_KEY_PATTERN: Final[str] = (
    r"^(\d{4})-(0[1-9]|1[0-2])#B([1-9]\d*)$"
)
MVP_SCENARIO_INDEX: Final[int] = 1
MVP_MAX_SCENARIOS_PER_TENANT: Final[int] = 1
SCENARIO_LIMIT_EXCEEDED_MESSAGE_KO: Final[str] = (
    "1차 MVP는 시나리오 1개만 지원합니다 (2차 예정)"
)
SCENARIO_HASH_PREFIX: Final[str] = "sha256:"
```

**4 NEW pure functions**:

1. `derive_budget_period_key(*, real_period_key: str, scenario_index: int = MVP_SCENARIO_INDEX) -> str`
   - `real_period_key="2026-07"` + `scenario_index=1` → `"2026-07#B1"`
2. `parse_virtual_budget_period_key(*, period_key: str) -> BudgetPeriodKeyParts`
   - Parses `YYYY-MM#B<n>` into `BudgetPeriodKeyParts(real_period_key, scenario_index, scenario_suffix)`.
3. `validate_scenario_uniqueness(*, existing_count: int) -> None`
   - 1차 MVP = 1 scenario only. `existing_count >= 1` →
     `ScenarioLimitExceededError` (HTTP 409 envelope).
4. `compute_budget_scenario_hash(*, scenario: BudgetScenario) -> str`
   - V8 determinism sha256 digest (32 hex chars + `sha256:` prefix).

**3 NEW frozen dataclasses**:

- `BudgetPeriodKeyParts(real_period_key, scenario_index, scenario_suffix)`
- `BudgetScenario(id, tenant_id, period_key, real_period_key, scenario_index, created_by, created_at_kst)`
- (Frozen for AD-5 stdlib-only purity)

**2 NEW typed exceptions** (CR 12-5 D-14 envelope main.py handlers):

- `ScenarioLimitExceededError` → HTTP **409 SCENARIO_LIMIT_EXCEEDED**
  - `existing_count` attribute for envelope details.
- `InvalidVirtualBudgetPeriodKeyError` → HTTP **422 INVALID_VIRTUAL_BUDGET_PERIOD_KEY**
  - `period_key` + `expected_pattern` attributes for envelope details.

### 2.2 TS Mirror (Frontend)

**File**: `apps/web/lib/m8-budget-scenario.ts`

Mirrors the kernel pattern + helpers. Drift caught by
`apps/web/__tests__/lib/m8-budget-scenario-parity.test.ts` (20 tests).

---

## 3. Architecture Wire (AD-1 + AD-11 + CR 12-5 L3)

### 3.1 Layer rule (AD-11)

```
apps/api/modules/m8_budget/
    handlers.py            ← 3 HTTP endpoints (POST + GET list + GET detail)
    services/              ← thin orchestration wrapper
    schemas.py             ← Pydantic v2 request/response
    exceptions.py          ← typed exceptions (CR 12-5 D-14)
packages/services/m8_budget/
    budget_period_key_serializers.py  ← thin JSON serializers (AD-8 + AD-15 §1)
packages/cost_engine/
    budget_period_key.py   ← PURE kernel (AD-5 stdlib-only)
```

### 3.2 3-Layer Defense (CR 12-5 L3 — scenario 생성 destructive-write)

| Layer | Defense | Component |
|-------|---------|-----------|
| 1. Route | `@require_capability(BUDGET_SCENARIO)` + `@require_any_role("owner", "member")` | `apps/api/modules/m8_budget/handlers.py` |
| 2. Service | `validate_scenario_uniqueness(existing_count=count_scenarios())` | `apps/api/modules/m8_budget/services/budget_scenario_service.py` |
| 3. DB | `UNIQUE(tenant_id, real_period_key)` + `UNIQUE(tenant_id, period_key)` + CHECK patterns | `apps/api/alembic/versions/0026_budget_scenarios.py` |

### 3.3 RLS (Row Level Security — supabase/policies/0016_budget_scenarios_rls.sql)

4-policy split:

1. **SELECT** same-tenant (4-role: owner + member + viewer + consultant_proxy)
2. **INSERT** owner + member (viewer + consultant_proxy denied)
3. **UPDATE** blocked (`USING (false)` — read-mostly invariant)
4. **DELETE** blocked (`USING (false)` — AD-2 INSERT-only soft invariant)

---

## 4. HTTP API

### 4.1 `POST /api/v1/budget/scenarios`

**Auth**: `@require_capability(BUDGET_SCENARIO)` + `@require_any_role("owner", "member")`

**Request body**:

```json
{
  "real_period_key": "2026-07"
}
```

**Response** (201 Created):

```json
{
  "scenario": {
    "id": "01926...-v7",
    "tenant_id": "01926...-tenant",
    "period_key": "2026-07#B1",
    "real_period_key": "2026-07",
    "scenario_index": 1,
    "scenario_hash": "sha256:abc...",
    "created_by": "01926...-user",
    "created_at_kst": "2026-08-15T..."
  }
}
```

**Error envelopes**:

- **409 SCENARIO_LIMIT_EXCEEDED** — `existing_count >= 1` (1차 MVP lock)
- **422 INVALID_VIRTUAL_BUDGET_PERIOD_KEY** — derived `period_key` malformed
- **422 INVALID_REAL_PERIOD_KEY** — request body `real_period_key` malformed (Pydantic)
- **403 FORBIDDEN_ROLE** — role gate failure

### 4.2 `GET /api/v1/budget/scenarios`

**Auth**: 4-role read gate (`owner + member + viewer + consultant_proxy`)

**Response** (200 OK):

```json
{
  "scenarios": [...],
  "total_count": 0 | 1,
  "trace_id": "..."
}
```

### 4.3 `GET /api/v1/budget/scenarios/{period_key}`

**Auth**: 4-role read gate

**Path param**: `period_key` (AD-24 virtual pattern)

**Error envelopes**:

- **404 BUDGET_SCENARIO_NOT_FOUND** — row missing
- **422 INVALID_VIRTUAL_BUDGET_PERIOD_KEY** — path param malformed

---

## 5. Migration (0026)

```sql
CREATE TABLE budget_scenarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    period_key TEXT NOT NULL,
    real_period_key TEXT NOT NULL,
    scenario_index INTEGER NOT NULL DEFAULT 1,
    scenario_hash TEXT NOT NULL,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at_kst TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_budget_scenarios_tenant_id_period_key UNIQUE (tenant_id, period_key),
    CONSTRAINT uq_budget_scenarios_tenant_id_real_period_key UNIQUE (tenant_id, real_period_key),
    CONSTRAINT ck_budget_scenarios_period_key_pattern
        CHECK (period_key ~ '^\d{4}-(0[1-9]|1[0-2])#B[1-9]\d*'),
    CONSTRAINT ck_budget_scenarios_real_period_key_pattern
        CHECK (real_period_key ~ '^\d{4}-(0[1-9]|1[0-2])'),
    CONSTRAINT ck_budget_scenarios_scenario_index_positive
        CHECK (scenario_index >= 1)
);
```

**Down revision**: 0025_tenants_deletion_status (Story 12.3)

---

## 6. honestly-DEFER (CR 11-3 11번째 epic 연속)

| Item | Trigger | Sprint |
|------|---------|--------|
| Multi-scenario 비교 (`scenario_index >= 2`) | ≥5 테넌트 요청 시 | Story 8.2 cj-style |
| Budget vs Actual Variance Table with ABCD Gray Badge (PRD §F8.2) | Story 8.2 spec 진입 | Story 8.2 cj-style |
| Budget Pre-Standard Cost Preview (`engine_type='budget'`) | Story 8.3 spec 진입 | Story 8.3 cj-style |
| 차월 추정 시나리오 저장 (Epic 7 7-2 carry-over) | ≥5 테넌트 요청 시 | Stage 3 A20 carry-over |
| Playwright E2E | Epic 8 follow-up | Epic 8 follow-up sprint |

---

## 7. References

- `packages/cost_engine/budget_period_key.py` — pure kernel (41 tests)
- `packages/services/m8_budget/` — thin JSON serializer layer
- `apps/api/modules/m8_budget/` — handlers + services + schemas + exceptions
- `apps/api/alembic/versions/0026_budget_scenarios.py` — migration
- `supabase/policies/0016_budget_scenarios_rls.sql` — RLS
- `apps/web/lib/m8-budget-scenario.ts` — TS mirror
- `apps/web/__tests__/lib/m8-budget-scenario-parity.test.ts` — parity tests (20)
- `tests/services/test_m8_budget_scenario_service.py` — service tests (13)
- `tests/cost_engine/test_budget_period_key.py` — kernel tests (36)
- `tests/cost_engine/test_budget_period_key_no_io_imports.py` — purity tests (5)
- `tests/architecture/test_api_calls_only_ports.py` — ALLOWED_SERVICE_SUBMODULES sweep
- `docs/conventions.md#§6.3` — AD-24 §6.3 spec section