# cost-engine — Pure §6.1 원가 산식 엔진

> **Status (2026-08-02, Story 4.2)**: `POST /api/v1/calc` 엔드포인트 + REPEATABLE READ 트랜잭션 + idempotency + audit-first 작성 완료.
> **Owner**: `packages/cost_engine/` (kebab: pure Python core)
> **Consumer**: `apps/api/modules/m3_calculate/` (Story 4-2)

## 목적

PRD §6.1 8단계 산식 체인을 구현하는 **순수 함수** (`compute_period_cost`) 의
소스 오브 트루스. V8 1원 단위 회귀 검증의 기준점이자, 후속 모든 원가
계산(story 4-2 endpoint, 4-3 V1/V4/V7 검증, 5.x inventory, 9.x ABC) 의
공통 kernel.

## 책임 (Responsibilities)

1. **Pure compute**: `(MonthlyInput, Baseline) → CalcResult` 결정론.
2. **8-stage 산식 체인 실행**: PRD §6.1 (1)~(8) — 8개 stage helper.
3. **결정론적 hash 산출**: `result_hash = sha256(stable_json_dumps(snapshot))`.
4. **방어-in-depth 검증**: 음수 KRW, invalid period_key, BOM/allocation
   gate. Service layer가 canonical validator 이지만 engine 도 명시적
   거부로 invariant 를 pure-function test 에 노출.

## 책임 아님 (Non-Responsibilities)

- ❌ DB read/write — adapter layer (`apps/api/modules/m3_calculate`) 담당.
- ❌ Clock — `datetime.now()` 등 wall clock 사용 금지. V8 결정론 보호.
- ❌ Random — `random.choice` 등 non-deterministic source 금지.
- ❌ Global state — module-level mutable container 금지.
- ❌ State transition — engine returns `state="draft"` ONLY. `verified`/
   `committed`/`reversed` 는 service layer (M11 reversal) 담당.
- ❌ Industry gating — engine is industry-agnostic. Capability gate 는
   API boundary (`apps/api/core/capability.py::Capability.COST_CALCULATION`).

## AD 바인딩 (Architecture Decision Links)

| AD | 영향 | 강제 위치 |
|---|---|---|
| AD-1 | Hexagonal core. `core/` is pure; `adapters/` 는 DB-bound. | import-linter contract `engine_core_to_adapters_forbidden` |
| AD-5 | Pure: no I/O, no DB, no clock, no random, no global state. | `tests/cost_engine/test_no_io_imports.py` AST guard |
| AD-8 | KRW = `int`, USD = `Decimal(2dp)`, `float` forbidden. | `tests/cost_engine/test_money_purity.py` + `test_period_cost_purity.py::test_krw_types_are_int` |
| AD-11 | `core` MUST NOT import `adapters`. | import-linter contract `engine_core_to_adapters_forbidden` |
| AD-15 | snake_case, ROUND_HALF_EVEN banker's rounding. | `test_period_cost_purity.py::test_round_half_even_bankers_rounding` |
| AD-16 | `result_hash = sha256(stable_json_dumps(snapshot))`. | `test_period_cost_purity.py::test_result_hash_is_64char_hex` |
| AD-19 | Single calculation entry point (`POST /api/v1/calc`). Story 4-2 에서 wiring. | `apps/api/main.py` (deferred) |
| AD-22 | Engine returns `state="draft"` ONLY. Service layer owns transitions. | `test_period_cost_purity.py::test_state_always_draft` + `test_no_io_imports.py::test_engine_state_transitions_only_draft` |
| AD-24 | Period key format: `YYYY-MM` real fiscal, `YYYY-MM#B<n>` virtual budget. | `test_period_cost_purity.py::test_period_key_format_validation` |

## 인터페이스 (Public API)

```python
from packages.cost_engine import (
    # Pure kernel
    compute_period_cost,
    Baseline,
    # I/O dataclasses (typed contracts)
    MonthlyInput,
    CalcResult,
    # Monetary primitives
    KRW,
    USD,
)

def compute_period_cost(monthly_input: MonthlyInput, baseline: Baseline) -> CalcResult:
    """§6.1 8단계 산식 체인 pure function.
    
    Returns:
        CalcResult with all KRW fields as int, result_hash as 64-char hex,
        state='draft' invariant.
    """
```

## 8-stage 산식 체인 (PRD §6.1)

| Stage | Helper | 산식 | 입력 검증 |
|---|---|---|---|
| (1) 직접재료 | `_stage1_material` | `direct_material_krw` (BOM 100% 통과 시 그대로) | `bom_ratio_validated` |
| (2) 직접노무 | `_stage2_labor` | `direct_labor_krw × fte_headcount` (ROUND_HALF_EVEN) | fte_headcount ≥ 0 |
| (3) 제조간접 | `_stage3_overhead` | `indirect_krw` (배부기준 3종 통과 시 그대로) | `allocation_basis_set` |
| (4) 재료 비율 | `_stage4_material_pct` | `material / mfg × 100` (info-only) | mfg != 0 |
| (5) 노무 비율 | `_stage5_labor_pct` | `labor / mfg × 100` (info-only) | mfg != 0 |
| (6) 간접 비율 | `_stage6_overhead_pct` | `overhead / mfg × 100` (info-only) | mfg != 0 |
| (7) 기말재고 조정 | `_stage7_inventory_adjustment` | `KRW(0)` + `TODO(epic-5)` | (Epic 5 fold-in) |
| (8) 제조원가 합계 | `_stage8_manufacturing_cost` | `material + labor + overhead` | (sum only) |

## V8 1원 단위 결정론

`compute_period_cost` 는 100% 결정론:

- 같은 `(MonthlyInput, Baseline)` → byte-identical `CalcResult` 100/100.
- `result_hash` 는 SHA-256 hex 64자 (`packages.cost_engine.tests.regression_v8.V8_GOLDEN_OUTPUT_STRUCTURE`).
- `banker_round_krw()` helper 가 policy 노출 (Story 4.4 fixture builders
  가 동일 rounding 사용).

### V8 골든 fixture 매트릭스 (Story 4.4 — 12 fixtures)

`packages/cost_engine/tests/regression_v8/fixtures/` 에 **12 JSON 파일** 발행.
매트릭스는 **4 industries × 3 baseline shapes** (PRD §6.1):

| Industry \\ Shape | b-small | b-standard | b-complex |
|---|---|---|---|
| `manufacturing` | `manufacturing__b-small.json` | `manufacturing__b-standard.json` | `manufacturing__b-complex.json` |
| `manufacturing_service` | `manufacturing_service__b-small.json` | `manufacturing_service__b-standard.json` | `manufacturing_service__b-complex.json` |
| `service` | `service__b-small.json` | `service__b-standard.json` | `service__b-complex.json` |
| `manufacturing_service_other` | `manufacturing_service_other__b-small.json` | `manufacturing_service_other__b-standard.json` | `manufacturing_service_other__b-complex.json` |

각 파일은 다음 lock invariants 를 가진다:

1. **`_fixture_lock_sha256`** — `sha256(stable_json(golden))` 64자 hex. 골든
   변경 시 lock mismatch → `fixture_publisher.py --check-only` 로 잡힌다.
2. **`tenant_id`** — random `uuid4()`. Engine 의 `result_hash` 가
   tenant-scoped 이므로 (AD-16 stable_json), V8 byte-identical 비교는
   fixture 입력의 `tenant_id` 그대로 사용해야 한다.
3. **`golden.state = "draft"`** — AD-22 invariant (engine always draft).
   골든이 다른 state 값이면 V8 fail.

### baseline shape 분포 (canonical 매칭)

`fixture_loader.select_golden_for_input()` 는 `monthly_input.monthly_total + fte` 로
shape 을 추론:

| Shape | material + labor + indirect 한도 | fte 한도 |
|---|---|---|
| `b-small`    | ≤ 2,000,000 KRW | ≤ 5  |
| `b-standard` | ≤ 10,000,000 KRW | ≤ 20 |
| `b-complex`  | (else) | (else) |

선택된 fixture 가 없으면 (Epic 11 reversal 시) `placeholder=True` 분기 fallback.

### byte-identical 비교 의사 코드

```python
# apps/api/modules/m3_calculate/services/rules/v8_regression.py::check
def check(self, input: RuleInput) -> VerificationItem:
    golden_input = select_golden_for_input(
        industry=input.industry, monthly_input=input.monthly_input
    )
    if golden_input is None:
        return VerificationItem(
            code="V8", status="passed",
            details={"placeholder": True, "no_fixture_for_industry": input.industry},
        )

    _input, golden_output = load_golden_by_id(golden_input["fixture_id"])

    golden_diff = {}
    for field in ("material_cost", "labor_cost", "overhead_cost",
                  "manufacturing_cost", "inventory_adjustment",
                  "result_hash", "state"):
        actual_val = getattr(input.calc_result, field)
        golden_val = golden_output[field]
        if str(actual_val) != str(golden_val):
            golden_diff[field] = {"golden": golden_val, "actual": actual_val}

    if not golden_diff:
        return VerificationItem(
            code="V8", status="passed",
            details={"fixture_id": golden_input["fixture_id"],
                     "fields_compared": [/* 7 fields */]},
        )

    return VerificationItem(
        code="V8", status="failed",
        details={"fixture_id": golden_input["fixture_id"],
                 "golden_diff": {"left": {...}, "right": {...}, "fields_diff": [...]}},
    )
```

### Fixture 추가 / 변경 절차

새 baseline shape 을 도입할 때:

1. `BASELINE_SHAPES` dict 에 새 shape 을 등록:
   `fixture_publisher.py` 의 `b-small/b-standard/b-complex` 3 tuple 옆에 추가.
2. 1 industry × 4 industries = 4 JSON 파일 생성:
   `python -m packages.cost_engine.tests.regression_v8.fixture_publisher --all`
3. `_fixture_lock_sha256` 자동 재계산 (publisher 가 dictionary 순서대로
   갱신).
4. `tests/regression_v8/test_regression_v8_fixtures.py::test_v8_fixture_matrix_covers_all_3_baseline_shapes`
   가 새 shape 도 커버하는지 확인 (parametrize set 갱신).
5. **`--all` 모드는 git commit 후 사용 금지**. 정상 운영은 `--check-only`
   (CI / dev default).

### CI gate (mandatory, no skip)

`tests/regression_v8/test_regression_v8_fixtures.py` 는 `@pytest.mark.engine`
+ `@pytest.mark.v8_regression` 둘 다 marking. `pytest` 기본 호출이 자동으로
포함 (no `--ignore` / `--deselect`). 28+ cases:

- `test_v8_fixture_count_is_12` (V8_FIXTURE_COUNT invariant)
- `test_v8_fixture_matrix_covers_all_4_industries` (F-5 Industry SSOT)
- `test_v8_fixture_matrix_covers_all_3_baseline_shapes`
- `test_v8_fixture_lock_sha256_validates[fixture_id]` × 12 (parametrize)
- `test_v8_golden_byte_identical_for_each_fixture[fixture_id]` × 12
- `test_v8_golden_100x_determinism[fixture_id]` × 12 (AD-16)
- `test_v8_golden_failed_path_format` (CR 2.3 extra='forbid' shape)
- `test_v8_golden_industry_skip_matrix[industry]` × 4
- `test_v8_golden_idempotent_re_call[fixture_id]` × 12
- `test_v8_rule_registry_uniqueness`, `test_v8_rule_is_in_registry`

## Capability gate (boundary)

`Capability.COST_CALCULATION` (`apps/api/core/capability.py`) 가
industry gating 담당. Story 4.1 spec:

| Industry | COST_CALCULATION |
|---|---|
| manufacturing | ✅ |
| service | ❌ (Epic 9 ABC instead) |
| manufacturing_service | ✅ |
| manufacturing_service_other | ✅ |

Engine core 의 어떤 코드도 `Industry` / `Capability` 를 import 하지 않는다
(`tests/integration/test_capability_consistency.py::test_cost_calculation_engine_is_industry_agnostic` 가
단언).

## Verification Envelope (V1·V4·V7·V8) — Story 4.3

`POST /api/v1/calc` 의 응답 envelope에 `verdict` 필드가 노출된다 (AD-12 + AD-20).
4개의 verification rule이 `_VERIFICATION_RULES: Final[tuple[VerificationRule, ...]]` 에 등록되어 **V1 → V4 → V7 → V8** 순서로 발동된다.

### Rule semantics

| Code | Name | 산업 발동 | 검증식 | tolerance |
|---|---|---|---|---|
| **V1** | 완전배부 | universal (모든 industry) | `manufacturing_cost == direct_material + direct_labor + indirect` | `\|delta\| <= KRW(1)` (AD-15 banker's rounding) |
| **V4** | 원가-손익 Reconciliation | universal | `sum(①+②+③) == manufacturing_cost` (④ inventory_adjustment 별도) | `\|delta\| <= KRW(1)` |
| **V7** | ABC 무결성 | `industry == 'service'` only | Epic 9 ABC 풀·활동·동인 100% 검증 (Story 9-1 wire 후) | MVP placeholder `passed` |
| **V8** | 엔진 결정론 회귀 | universal | `result_hash == golden_hash` (Story 4.4 골든 fill 후 wire) | byte-identical 골든 vs engine (12 fixture matrix) |

### V4 4요소 자동 분해 (PRD §11 V4)

```
details.4_elements = {
  "qty_diff_material_krw": KRW,            # ①생산·매출 수량차 재료비
  "labor_overhead_allocation_krw": KRW,    # ②노무비+제조경비 배분차
  "unit_price_diff_krw": KRW,              # ③총평균단가차 (Epic 5 fold-in 후 wire)
  "inventory_adjustment_krw": KRW,         # ④재고조정 (engine result column)
  "sum_4_elements_krw": KRW,               # verification target
  "manufacturing_cost_krw": KRW,           # engine pass-through
}
```

**Invariant**: `① + ② + ③ == manufacturing_cost` (④ inventory_adjustment 는 engine result 의 별도 column 으로 4요소 합에 미포함 — Epic 5 fold-in 후 별도 REPORT 항목).

### AD-12 ordering invariant

```
VerificationRunner.run_all(...) →
  for rule in _VERIFICATION_RULES:  # tuple immutable (V1, V4, V7, V8)
    if not rule.applies_to(industry): continue  # silent skip
    item = rule.check(RuleInput(...))
    verifications.append(item)
    if item.status == 'failed': break  # AD-12 ordering invariant — earlier failed aborts later checks
```

- `verifications[]` 응답에는 발동된 rule만 포함 (applies_to=False → silent skip → array 미포함)
- V1 fail → V4·V7·V8 모두 미발동. `verifications.length == 1`
- `top_failure = first failed VerificationItem` (AD-20 invariant — non-null iff status='failed')

### Per-industry firing matrix (AD-12 spec interpretation)

| Industry | V1 | V4 | V7 | V8 | 발동 수 |
|---|---|---|---|---|---|
| `manufacturing` | ✅ | ✅ | skip | ✅ | 3 |
| `manufacturing_service` | ✅ | ✅ | skip | ✅ | 3 |
| `service` | ✅ | ✅ | ✅ | ✅ | 4 |
| `manufacturing_service_other` | ✅ | ✅ | skip | ✅ | 3 |

V7 service-only: AD-12 spec interpretation. Manufacturing tenant의 BOM 100% 검증은 Story 2.2 atomic BOM check (별도 gate) 가 담당 — V7은 service industry에만 추가 발동.

V8 universal: 12 fixture 매트릭스 (4 industries × 3 baseline shapes) 가 byte-identical 골든 vs engine 비교. `select_golden_for_input()` 가 `industry × shape` 로 canonical 골든 선택 — see §V8 above.

### AD-20 외부 응답 invariant

| Layer | `verification_status` 노출 값 |
|---|---|
| **Engine** (`packages/cost_engine`) | `'draft'` state 만 — verification_status 미존재 |
| **Service** (`apps/api/modules/m3_calculate/services/verification_runner.py`) | 내부에서 `'pending'` transient 가능 |
| **API 응답** (`apps/api/modules/m3_calculate/schemas.py::Verdict`) | `Literal["passed", "failed"]` only — `'pending'` 부재 |
| **TS mirror** (`apps/web/lib/m3-verdict.ts::VerificationStatus`) | `"passed" \| "failed"` only |

Pydantic Literal type + TS `VerificationStatus` mirror 모두 `'pending'` 부재 검증 (`tests/web/test_m3_verdict_parity.py::test_pending_status_rejected_in_python` + `test_pending_status_rejected_in_ts`).

### Pydantic envelope shape (AD-15 §4)

```python
# apps/api/modules/m3_calculate/schemas.py (Story 4.3 extension)

class VerificationItem(BaseModel):
    model_config = ConfigDict(extra="forbid")  # CR 2.3 lesson
    code: Literal["V1", "V4", "V7", "V8"]
    status: Literal["passed", "failed"]  # 'skipped' 는 발동 자체가 안 됨 → enum 제외
    message_ko: str
    details: dict[str, Any]  # V1: delta_krw / V4: 4_elements / V7: pools / V8: placeholder

class Verdict(BaseModel):
    model_config = ConfigDict(extra="forbid")
    verification_status: Literal["passed", "failed"]
    verifications: list[VerificationItem]  # 발동된 rule만
    top_failure: VerificationItem | None  # status='failed' 첫 항목
    trace_id: str

class CalcResponse(BaseModel):  # Story 4-2 wire extension
    # ... 기존 fields (tenant_id, period_key, 4 KRW + result_hash + state + baseline_revision + trace_id)
    verdict: Verdict  # NEW — Story 4-3 wire extension
```

### TS mirror (`apps/web/lib/m3-verdict.ts`)

Python canonical 의 단일 진실 공급원에 TS mirror 가 동기화. 드리프트는 `tests/web/test_m3_verdict_parity.py` 20 cases 로 강제 차단:

- `VerificationCode`, `VerificationStatus`, `VerificationEnvelopeStatus` Literal enum parity
- `Industry` 4-value enum parity (manufacturing / manufacturing_service / service / manufacturing_service_other)
- `INDUSTRY_FIRES_V7` 매트릭스 (service-only)
- Verdict envelope field shape (`verification_status`, `verifications`, `top_failure`, `trace_id`)
- VerificationItem field shape (`code`, `status`, `message_ko`, `details`)
- top_failure invariant (non-null iff `verification_status === 'failed'`)
- UI failure code 매핑 (`ERR_V1_INCOMPLETE_ALLOCATION` / `ERR_V4_COST_INCOME_RECONCILIATION` / `ERR_V7_ABC_INTEGRITY` / `ERR_V8_ENGINE_REGRESSION`)
- `isVerdict` type guard + `topFailureCode` / `firedRuleCodes` helper parity

### `verification_log` table (CR 1.1 audit-first)

verification 결과는 `verification_log` table 에 audit-first 로 INSERT (Story 4-3 신규). RLS policy (`CR 0.2 lesson`):

```sql
CREATE TABLE verification_log (
    verification_log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,                          -- RLS
    period_key TEXT NOT NULL,                          -- AD-24
    baseline_revision INT NOT NULL,
    action TEXT NOT NULL CHECK (action IN
        ('verification_passed', 'verification_failed', 'verification_skipped',
         'verify_v8_golden_match')),  -- Story 4.4 V8 골든 mismatch audit-first (A5 forward-lock)
    top_failure_code TEXT,                             -- nullable
    top_failure_message_ko TEXT,                       -- nullable
    result_hash TEXT NOT NULL,
    trace_id TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE verification_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE verification_log FORCE ROW LEVEL SECURITY;

CREATE POLICY verification_log_tenant_isolation ON verification_log
    USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
    WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
```

Alembic migration: `apps/api/alembic/versions/0013_verification_log.py`. A5 audit-action inversion은 `apps/api/core/audit_action.py::ActionClass` 가 single source of truth.

## V3 — Closing Invariant Verification (Story 5.3, 2026-08-06)

V3 (연결성) verification = closing ≥ 0 invariant. Wire contract:
- 4-3 V3 placeholder → 4-4 V8 골든 → 5-3 V3 fill (closing ≥ 0 invariant rule)
- Pure kernel: `packages/cost_engine/closing_invariant_check.py` (stdlib-only, AD-11 layer rule)
- Service: `apps/api/modules/m3_calculate/services/closing_invariant_verifier.py` (V3 slot fill in VerificationRunner)
- AD-12 ordering: V1 → V4 → V3 → V7 → V8 (5-rule ordering, abort-on-fail pattern)

V3 골든 fixture 2 NEW:
- `v3_closing_pass_manufacturing.json` — 모든 product closing ≥ 0 + V3 verdict = passed
- `v3_closing_fail_manufacturing.json` — 최소 1개 product closing < 0 + V3 verdict = failed
- V8 byte-identical 14 matrix extension (12 → 14)

V3 SKIP semantic:
- industry='service' → status='skipped' (per AD-12 enum)
- empty manufacturing product set → status='skipped'
- reason_ko='service-only tenant은 inventory 의미 없음' (Korean SSOT)

## V4 — Closing-Period Consistency Verification (Story 6.2, 2026-08-08)

V4 (closing-period consistency) verification = 4-source aggregate 일치.
**Story 6.1** 에서 V4 2-source wire (closing snapshot × fiscal period snapshot)
시작 → **Story 6.2** 에서 4-source extension (ledger aggregate +
closing snapshot + fiscal period snapshot + product whitelist).
Wire contract:

- Pure kernel #1: `packages/services/m4_inventory/monthly_closing_report.py`
  (3-source read-only join + view mode classifier)
- Pure kernel #2: `packages/cost_engine/monthly_closing_report_aggregator.py`
  (`verify_monthly_closing_report_consistency` — 4-source V4 verification)
- Service: `apps/api/modules/m4_inventory/services/monthly_closing_report_service.py`
  (V4 slot dispatch + audit-first wire + idempotent no-op skip)
- AD-12 ordering: V1 → **V4** → V3 → V7 → V8 (5-rule ordering, V4 slot 2)

V4 골든 fixture 2 NEW (6-1 T10.5 → 6-2 carry-over close):
- `closing-period-b-small.json` — V4 verdict = passed (4-source 일치)
- `closing-period-b-standard.json` — V4 verdict = failed (1개 product
  4-source 불일치 → failures[] populated + message_ko)
- V8 byte-identical 18 matrix extension (16 → 18 — closing-period 2 +
  fiscal-period-snapshot 2 = 4 V4/A11 fixtures)

V4 SKIP semantic:
- industry='service' → status='skipped' (per AD-12 enum)
- empty 4-source aggregates → status='skipped'
- reason_ko='service-only tenant은 closing report 의미 없음' (Korean SSOT)

V4 source_count invariant:
- 4 sources ALWAYS present in verdict envelope
  (`ledger_aggregate` + `closing_snapshot_aggregate` +
  `fiscal_period_snapshot_aggregate` + `product_whitelist`)
- Drift detector:
  `tests/cost_engine/test_monthly_closing_report_aggregator.py::test_v4_source_count_is_4`
  (T9.2)

## V8 18-fixture matrix extension (Story 6.2, A11 PRIMARY)

V8 byte-identical 골든 매트릭스 (Story 4.4 12 fixtures baseline → Story 5.3 V3 +2 → Story 6.2 V4/A11 +4 = **18 fixtures**):

| Group | Count | Fixtures | Story |
|---|---|---|---|
| V8 baseline | 12 | 4 industries × 3 baseline shapes (b-small / b-standard / b-complex) | 4.4 |
| V3 closing invariant | 2 | `closing-invariant-b-standard.json` + `closing-invariant-b-complex.json` | 5.3 |
| V4 closing-period (small) | 1 | `closing-period-b-small.json` | 6.2 |
| V4 closing-period (standard) | 1 | `closing-period-b-standard.json` | 6.2 |
| V4 fiscal-period-snapshot (small) | 1 | `fiscal-period-snapshot-b-small.json` | 6.2 |
| V4 fiscal-period-snapshot (standard) | 1 | `fiscal-period-snapshot-b-standard.json` | 6.2 |
| **Total** | **18** | 12 + 2 + 4 | — |

Drift detectors:
- `tests/regression_v8/test_regression_v8_fixtures.py::test_v8_fixture_count_is_18`
- `tests/cost_engine/test_regression_v8_placeholder.py::test_v8_fixture_count_now_18_in_story_6_2`
- `tests/architecture/test_api_calls_only_ports.py::ALLOWED_SERVICE_SUBMODULES`
  includes `"packages.services.m4_inventory.monthly_closing_report"`

## Story → engine story mapping

| Story | Engine 영향 |
|---|---|
| 0.1 | Engine skeleton + `money.py` (KRW/USD) — pure foundation |
| 0.3 | `tests/regression_v8/` directory + README — V8 fixture policy |
| 4.1 | `compute_period_cost` + `Baseline` + 8-stage 산식 (본 story) |
| 4.2 | `POST /api/v1/calc` endpoint (Story 4-2) — adapter wiring |
| 4.3 | V1/V4/V7 verification surface (Story 4-3) — engine output consumers |
| 4.4 | V8 골든 fixture 매트릭스 (4 industries × 3 baseline shapes = 12 JSON) + CI gate — engine 결정론 byte-identical 회귀 검출. `verify_v8_golden_match` audit action forward-lock. |
| 5.x | Inventory ledger fold-in (`_stage7_inventory_adjustment` swap) |
| 6.x | Product master — engine consumers (per-product cost breakdown) |
| 6.1 | V4 closing-period consistency 2-source wire (closing snapshot × fiscal period snapshot) — VerificationRunner V4 slot fill |
| **6.2** | **V4 closing-period consistency 4-source extension (ledger + closing snapshot + fiscal period snapshot + product whitelist) + V8 16→18 골든 매트릭스 (closing-period 2 + fiscal-period-snapshot 2 = 4 NEW V4/A11 골든 fixtures) + KRW/USD dual display (PRD §F5.2 ROUND_HALF_EVEN)** |
| 9.x | ABC engine — service layer + Epic 9 separately. Engine kernel reuse. |
| 11    | M11 reversal — service layer, NOT engine. |

## 변경 규칙 (Change rules)

1. **Public API 변경** — `compute_period_cost` 시그니처, `CalcResult` 필드:
   - ADR ticket + Epic 0 회고에서 합의 후에만.
   - V8 골든 파일 재생성 (Story 4.4 owner 동참).
2. **Internal helper 추가/변경** — 8-stage 내부 stage helper:
   - 변경 시 동일 story 에서 V8 placeholder test 갱신.
   - Stage 추가 시 PRD §6.1 에 stage 추가 필요 (PM 동참).
3. **Pure function invariant** — 절대 깨면 안 됨:
   - `import` 가능한 module: `decimal`, `typing`, `uuid`, `dataclasses`,
     `enum`, `collections.abc`, `hashlib`, `json`, `re`.
   - `import` 금지: `sqlalchemy`, `fastapi`, `pydantic`, `requests`,
     `httpx`, `psycopg`, `asyncpg`, `time`, `datetime`, `random`,
     `socket`, `subprocess`, `os`.
   - AST 가드가 매 PR 마다 위반 검사.

## 참고 문서 (References)

- [packages/cost_engine/README.md](../packages/cost_engine/README.md) — engine 디렉토리 가이드
- [docs/capability-matrix.md](capability-matrix.md) v1.1 — capability matrix
- [docs/conventions.md](conventions.md) §AD-5, §AD-8, §AD-15, §AD-22
- [docs/architecture-decisions/AD-5-engine-purity.md](architecture-decisions/) — purity 결정
- [packages/cost_engine/tests/regression_v8/README.md](../packages/cost_engine/tests/regression_v8/README.md) — V8 정책
- Story 4.1 spec: `_bmad-output/implementation-artifacts/4-1-pure-cost-engine-no-i-o-no-clock.md`
- Story 4.1 retrospective: `_bmad-output/implementation-artifacts/4-1-retrospective-2026-08-02.md` (deferred)
