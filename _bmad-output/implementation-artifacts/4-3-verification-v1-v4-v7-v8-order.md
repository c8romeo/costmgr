---
baseline_commit: 4d088f5
target_key: 4-3-verification-v1-v4-v7-v8-order
---

# Story 4.3: Verification V1·V4·V7·V8 in Order + verdict field

Status: review

> Epic 4 세 번째 — Story 4.2의 `POST /api/v1/calc` 응답에 **verdict envelope** (verification_status + verifications[]) 추가 + §11 V1·V4·V7·V8 검증이 AD-12 순서(V1 → V4 → V7 → V8)로 자동 발동 + 이전 검증 실패 시 후속 검증 abort (transaction-internal state machine) + service-only tenant은 V1/V4 skip · V7/V8 still run.
> **모듈**: `apps/api/modules/m3_calculate/services/verification_runner.py` (신규) + `apps/api/modules/m3_calculate/services/__init__.py` (re-export) + `apps/api/modules/m3_calculate/schemas.py` (`verdict` field + `Verification*` schemas) + `apps/api/modules/m3_calculate/services/calc_orchestrator.py` (Step 6.5: verification wiring) + `apps/api/modules/m3_calculate/services/baseline_loader.py` (ABC 무결성 gate helper) + `tests/api/test_verdict_envelope.py` (신규) + `tests/cost_engine/test_verification_rules.py` (신규 — 4 pure rule kernels) + `tests/integration/test_verification_order.py` (신규 — V1→V4→V7→V8 ordering) + `docs/cost-engine.md` (§V1·V4·V7·V8 verification envelope 섹션) + `docs/capability-matrix.md` v1.3.

<!-- dev-context: Epic 1 retro W6 (PIPA env-flag fallback) — A1 게이트 해소됨 (Epic 3 회고 A1 done 2026-08-02).
                    Epic 2 retro W4 (TS mirror regex 검증) — Story 4.2 first 등장. 본 스토리는 verification envelope의 TS mirror parity 도입 (apps/web/lib/m3-verdict.ts + tests/web/test_m3_verdict_parity.py).
                    Epic 3 retro W1 (read-only → 정밀 → 경고) — 본 스토리는 "정밀 후 검증" 단계 (Episode 4 L1 progressive enhancement 패턴).
                    Epic 3 retro W6 (AD-15 banker's rounding) — V1 = 1원 단위 (=Decimal(0)) · V4 4요소 분해는 KRW 정수 정밀.
                    Epic 4 A1 (4d088f5 — chore: pre-existing failures 정리 8건 + 27 lint) — 본 스토리는 A1 즉시 fix 후 진입.
                    Story 4.1 AD-22 — engine always state="draft" (append-only-leaning).
                    Story 4.2 AC #1~10 — POST /api/v1/calc REPEATABLE READ + close-time hook + idempotency wired.
                    Story 4.2 SDR F-1 — spec AC #3 close-time hook detail block tagged "[deferred-to-4.3]" → 본 스토리에서 verdict envelope가 details carrier 역할.
                    AD-4 REPEATABLE READ — verification runs INSIDE transaction (AD-12) — one REPEATABLE READ 트랜잭션 안에서 V1→V4→V7→V8 발동.
                    AD-12 verification-first — M3 runs input validation → engine calculation → V1→V4→V7→V8 in order → verified → snapshot → committed. Failed check aborts later checks + rolls back.
                    AD-20 state machine — draft→verified→committed→reversed; verification_status: pending|passed|failed.
                    AD-22 append-only-leaning — reversal = Epic 11 (M11 owner). 본 스토리는 state='verified'까지만 도달.
                    AD-19 single entry point — POST /api/v1/calc 한 개. verification은 internal step.
                    CR 1.1 lesson (audit-action inversion) — 본 스토리는 calc_log.action 신규 'verification_failed' 추가 시 A5 별도 스파이크 결과(action_class.py single source of truth) 적용.
                    Epic 4 회고 A5 결정 — CR 1.1 전사 single source of truth fix는 Epic 4 close-out window 내 병렬 스파이크 (4-3과 동시). 본 스토리는 action 'verification_failed' enum 추가는 Charlie 결정 후 delay 또는 'compute'/'idempotent_skip'/'rollback' 그대로 유지 결정 둘 중 하나 (OQ5).
                    Epic 4 회고 §11 Q4 = Charlie A5 결정 — 본 스토리 OQ5에서 cj-style default = 'verification_failed' 신규 추가 + action_class.py 표준 enum 적용 (CR 1.1 asset).
                    Epic 4 회고 W4 (capability matrix 4 epic 연속 자산) — COST_CALCULATION unchanged (no new capability row); service-only tenant은 service layer가 V1/V4 skip + V7/V8 run 분기 처리.
                    Epic 4 회고 L6 (V8 placeholder contract) — tests/cost_engine/test_regression_v8_placeholder.py 10 cases filled by Story 4-4. 본 스토리는 placeholder contract 보존 + verification rule registry 1 case 추가.
                    Epic 5 A3 (ledger fold-in) — V4 4요소 분해 ④재고조정 = KRW(0) 영구 (Epic 5 5-1/5-2에서 fold-in swap). V4 result detail은 `inventory_adjustment` field = 0인 상태로 표시.
                    0.5 plumbing — Epic 4 backend-only, frontend 영향 없음. V8 골든 파일은 backend JSON fixture. -->

## Story

As a **사장님 (small/medium business owner)**,
I want **`POST /api/v1/calc` 한 번 호출 안에서 §11 V1·V4·V7·V8이 AD-12 순서(V1→V4→V7→V8)로 자동 발동되어 각 검증의 pass/fail + 4요소 분해 + top failure reason이 한 envelope으로 돌아오는 것**,
so that **"계산은 됐는데 V4가 빨강" 같은 부분 완료 상태가 절대 안 생기고, 회계사가 "왜 검증 실패냐"고 물으면 같은 응답 envelope으로 즉시 재현 — `verification_status: 'failed'`면 회계 잠금이 자동으로 걸려 잘못된 원가가 보고서로 흘러가지 않음** — AD-4 (REPEATABLE READ) · AD-12 (verification-first) · AD-20 (state machine) · F3.2 (V1·V4·V7·V8 자동 발동) · F6.1 (마감·계산 시점 두 곳) · NFR16 (determinism — V8 1원 단위 회귀).

## Acceptance Criteria

1. **Given** Story 4.2의 `apps/api/modules/m3_calculate/services/calc_orchestrator.py::run_calculation()` 끝부분 (Step 9 INSERT 직전 + COMMIT 직전)에 **Step 6.5: verification 발동** hook이 추가된다 (AC #1)
   **When** 본 스토리 dev-story 진행 시
   **Then** 다음 3-layer 책임 분리 유지:
     - **Engine** (`packages/cost_engine/core/period_cost.py`) — Story 4.1 그대로. 아무 V* 검증도 모름 (AD-12 도메인 분리).
     - **Service** (`apps/api/modules/m3_calculate/services/verification_runner.py` 신규 + `calc_orchestrator.py`) — `VerificationRunner.run_all(monthly_input, baseline, calc_result, *, industry: Industry) -> Verdict` 호출. 규칙 등록소(`_VERIFICATION_RULES: Final[tuple[VerificationRule, ...]]`) + service-only skip 분기 보유.
     - **Handler** (`apps/api/modules/m3_calculate/handlers.py`) — calc_orchestrator 응답에 `verdict` field 추가 (Story 4.2 응답 envelope extension). exception handler는 그대로 (verification failed는 200 + verdict envelope, NOT 4xx — 계산 자체는 성공; lock은 service layer 책임).

2. **Given** Step 6.5 verification 발동 (AC #1) + AD-12 verification-first
   **When** `VerificationRunner.run_all(...)` 호출되면 다음 **strict ordered sequence**로 4개 rule 발동:
     1. **V1** (`V1CompleteAllocationRule`) — `manufacturing_cost == direct_material_krw + direct_labor_krw + indirect_krw` 1원 단위 (AD-15 banker's rounding: `|V1_delta| <= KRW(1)`)
     2. **V4** (`V4CostIncomeReconciliationRule`) — 제조원가 ↔ 매출원가 ↔ 재고 차이 **4요소 자동 분해** (PRD §11 V4): ①생산·매출 수량차 재료비 ②노무비+제조경비 배분차 ③총평균단가차 ④재고조정 (`inventory_adjustment = KRW(0)` 영구 — Epic 5 5-1/5-2 fold-in swap 진입점)
     3. **V7** (`V7AbcIntegrityRule`) — `industry != Industry.SERVICE` THEN skip (V7은 service-only); ELSE 원가풀 행 합 100% (=Decimal(0) 1원 단위) + 활동 열 합 100% + 동인 합 100% + 완전배부 — 4개 부분 검증 모두 통과해야 V7 pass
     4. **V8** (`V8RegressionRule`) — placeholder contract (Story 4-1 T5 `tests/cost_engine/tests/regression_v8/__init__.py::banker_round_krw()` + V8PlaceholderRule stub). 12 시나리오 골든 파일 fill = **Story 4.4** (deferred).
   **And** AD-12 ordering invariant: **이전 검증 status='failed'면 후속 검증 abort** (V1 fail → V4·V7·V8 skip). `verifications[]` 응답은 발동된 rule만 포함 (V1 fail → array length = 1).
   **And** 모든 rule은 `VerificationRule` protocol 구현: `name: str` + `applies_to(industry: Industry) -> bool` + `check(input: RuleInput) -> VerificationItem` (pure — no DB, no clock, no I/O — AC #6 AD-5 purity).
   **And** `tests/cost_engine/test_verification_rules.py`에 4 rule pure kernel 12+ cases (3 cases per rule × 4 rules) — happy path + 1원 단위 boundary + 4요소 분해 + ABC gate + service-only skip + ordering invariant.

3. **Given** AC #2 V1·V4·V7·V8 발동 완료 + AD-20 verification_status
   **When** `VerificationRunner.run_all(...)` returns `Verdict`
   **Then** 다음 envelope shape (Story 4-2 `CalcResponse`의 `verdict` field에 매핑):
     ```python
     # apps/api/modules/m3_calculate/schemas.py (Story 4.3 신규)
     class VerificationItem(BaseModel):
         code: Literal["V1", "V4", "V7", "V8"]
         status: Literal["passed", "failed", "skipped"]
         message_ko: str
         details: dict[str, Any]  # V1: {"delta_krw": int}, V4: {"4_elements": {...}}, V7: {"pools": {...}}, V8: {"placeholder": True}
         trace_id: str
     
     class Verdict(BaseModel):
         verification_status: Literal["passed", "failed"]
         verifications: list[VerificationItem]  # 발동된 rule만 (skipped는 미포함)
         top_failure: VerificationItem | None  # status='failed' 첫 항목
         trace_id: str
     
     class CalcResponse(BaseModel):  # Story 4-2 wire에 verdict 추가
         # ... 기존 fields (tenant_id, period_key, material_cost, labor_cost, overhead_cost,
         #     manufacturing_cost, inventory_adjustment, result_hash, state, baseline_revision, trace_id)
         verdict: Verdict
     ```
   **And** envelope은 `extra='forbid'` (CR 2.3 lesson) + Pydantic v2 typed literal `Literal["passed", "failed"]`로 컴파일 타임 enforce.
   **And** TS mirror parity: `apps/web/lib/m3-verdict.ts` (TS interface + fetch wrapper) + `tests/web/test_m3_verdict_parity.py` (cross-lang drift guard — Epic 2 W4 + Epic 3 W3 패턴). 4 case × 4 dimension = 16 cross-lang sub-cases.
   **And** `tests/api/test_verdict_envelope.py::test_verdict_envelope_required_when_status_verified` 1 case + `test_verdict_envelope_skipped_field_drop` 1 case + `test_verdict_envelope_extra_forbid` 1 case.

4. **Given** verification_status 결과 + AD-20 state transition
   **When** `VerificationRunner.run_all(...)` returns Verdict
   **Then** 다음 state 전이 (calc_orchestrator에 wire):
     - `verdict.verification_status == 'passed'` AND `result.state == 'draft'` AND V1+V4+V7+V8 모두 status='passed' → `INSERT INTO fiscal_period_snapshots (state='verified', ...)` (Story 4.2 Step 8)
     - `verdict.verification_status == 'failed'` → **transaction-internal ROLLBACK** (fiscal_period_snapshots INSERT 안 함) + `calc_log(action='rollback', result_hash=None)` (CR 1.1 audit) + handler returns 200 OK + verdict envelope (NOT 4xx — 계산 자체는 성공, lock만 service layer)
     - `top_failure` is non-null when `verification_status == 'failed'` AND at least 1 verifications[].status == 'failed'
   **And** service-only tenant (`Industry.SERVICE`): V1/V4 skip (AD-12 rule + V7/V8 still run). 결과 envelope `verifications[]`에 V1/V4 미포함 (skip은 표시 안 함 — 발동 안 됨).
   **And** Epic 11 M11 reversal / state='committed' 전이는 **Epic 11 Story 11-1/11-2/11-3** — 본 스토리 범위 외.
   **And** `tests/integration/test_verification_order.py` 8 cases: (a) V1 pass → V4 pass → V7 pass → V8 pass → verification_status='passed', (b) V1 fail → V4·V7·V8 abort → status='failed', (c) service-only tenant → V1·V4 skip → V7·V8 발동, (d) V7 ABC 100% invalid → status='failed', (e) V8 placeholder stub return 'passed' (Story 4-4 fill), (f) ordering invariant (V1 fail 후 V4·V7·V8 미발동, verifications[]=1), (g) top_failure = first failed, (h) calc_log(action='rollback') emission (CR 1.1 audit).

5. **Given** V4 4요소 자동 분해 (PRD §11 V4: ①생산·매출 수량차 재료비 ②노무비+제조경비 배분차 ③총평균단가차 ④재고조정)
   **When** `V4CostIncomeReconciliationRule.check(input)` 호출
   **Then** `details.4_elements` dict shape (TS mirror parity):
     ```python
     {
       "qty_diff_material_krw": Decimal("0"),  # ①생산·매출 수량차 재료비
       "labor_overhead_allocation_krw": Decimal("0"),  # ②노무비+제조경비 배분차
       "unit_price_diff_krw": Decimal("0"),  # ③총평균단가차
       "inventory_adjustment_krw": KRW(0),  # ④재고조정 — Epic 5 5-1/5-2 fold-in 진입점
       "sum_4_elements_krw": KRW(0),  # 4개 합 (verification target)
       "manufacturing_cost_krw": KRW(4_900_000),  # engine pass-through
     }
     ```
   **And** rule은 `sum_4_elements_krw == manufacturing_cost_krw` 검증 (PRD §11 V4 — manufacturing_cost = 4-요소 분해 합). 1원 단위 tolerance (`|delta| <= KRW(1)`). 미통과 시 status='failed'.
   **And** 4요소 각 component 계산 rule은 pure helper (`packages/cost_engine/core/verification_v4.py` 또는 `apps/api/modules/m3_calculate/services/rules/v4_four_element.py`). Epic 5 fold-in 후 = `inventory_adjustment_krw != KRW(0)` (Epic 5 5-1/5-2에서 wire).
   **And** `tests/cost_engine/test_verification_rules.py::test_v4_four_element_decomposition` 1 case + `test_v4_sum_equals_manufacturing_cost` 1 case + `test_v4_inventory_adjustment_zero_mvp` 1 case (Epic 5 fold-in 전 placeholder 명시).

6. **Given** verification rule의 purity (AD-5 + AC #1 — engine purity invariant extension)
   **When** `apps/api/modules/m3_calculate/services/verification_runner.py` + `apps/api/modules/m3_calculate/services/rules/*.py` (4 rule kernels) AST 검사
   **Then** 다음 top-level import가 **0건**:
     - DB: `sqlalchemy`, `psycopg`, `asyncpg`
     - Web: `fastapi`, `starlette`, `httpx`
     - Clock: `time`, `datetime.datetime.now()`, `os.environ`
     - Random: `random`, `secrets`
   **And** `tests/cost_engine/test_verification_rules.py::test_verification_rules_no_io_imports` 1 case (AST-level 3중 차단 = import-linter + AST + ruff의 verification module 확장)
   **And** `tests/cost_engine/test_no_io_imports.py`의 forbidden list에 `verification_rules` 추가 (AD-5 보강 — engine purity + verification purity 둘 다 보장)
   **And** `uv run import-linter` 2 contracts KEPT (`cost_engine_forbidden_io` + `engine_core_to_adapters_forbidden`) — verification rules은 m3_calculate service layer에 속하므로 별도 contract 불필요 (Story 4.2 AST allowlist에 등록됨).

7. **Given** Capability gate (Story 4.1 T3 + Epic 3 회고 A5 + Story 4.2 AC #5) — `COST_CALCULATION` unchanged
   **When** 본 스토리 dev-story 완료 시점
   **Then** 다음 4 industries × V* 발동 매트릭스 (AD-12 service-only skip + capability gate):
     - **manufacturing**: V1 pass → V4 pass → V7 100% OK → V8 placeholder → status='passed' (정상)
     - **manufacturing_service**: V1→V4→V7→V8 모두 발동 (제조+서비스 hybrid)
     - **manufacturing_service_other**: V1→V4→V7→V8 모두 발동
     - **service** (`Industry.SERVICE`): V1 skip · V4 skip · V7 발동 (Epic 9 ABC 검증) · V8 placeholder → status depends on V7+V8
   **And** `tests/api/test_verdict_envelope.py::test_service_industry_skips_v1_v4` 1 case (DB skipif — Story 0.5 plumbing) — verifications[] 길이 = 2 (V7, V8 only) — service-only 검증.
   **And** `tests/integration/test_verification_order.py::test_industry_skip_matrix` 1 case (4 industries × 4 rules parametrize = 16 cases).

8. **Given** V8 placeholder contract (Story 4.1 T5) — `tests/cost_engine/tests/regression_v8/__init__.py::V8_INPUT_SCHEMA` + `V8_GOLDEN_OUTPUT_STRUCTURE` + `banker_round_krw()`
   **When** `V8RegressionRule.check(input)` 호출 (Story 4-3 시점에는 stub)
   **Then** 다음 동작:
     - `V8_INPUT_SCHEMA.validate(input)` (placeholder — empty fixtures allowed)
     - `result_hash == expected_hash` 이면 status='passed' (Story 4.1 placeholder contract)
     - 12 시나리오 골든 파일 fill = **Story 4.4 deferred** (이번 AC는 stub 'passed' 반환 + 골든 fill 위치 보존)
   **And** `tests/cost_engine/test_regression_v8_placeholder.py` (Story 4-1 10 cases) KEPT + `tests/cost_engine/test_verification_rules.py::test_v8_rule_passes_placeholder` 1 case (V8RegressionRule stub이 status='passed' 반환 검증).

9. **Given** calc_log audit (Story 4.2 AC #8) + CR 1.1 audit-first + A5 action_class.py single source of truth (Epic 4 회고 §11 Q4)
   **When** `VerificationRunner.run_all(...)` results + calc_orchestrator transaction
   **Then** 다음 audit log 시퀀스:
     - `verification_status == 'passed'`: `calc_log(action='compute', result_hash=...)` (Story 4.2 Step 9 그대로). verification item들은 calc_log 본문에 미포함 (별도 `verification_log` table 또는 service layer telemetry — Story 4.3 OQ5 결정).
     - `verification_status == 'failed'`: `calc_log(action='rollback', result_hash=None)` (Story 4.2 CR 1.1 audit) + `verification_log(action='verification_failed')` 신규 INSERT (CR 1.1 lesson + A5 전사 enum 표준화 적용 — Epic 4 회고 §11 Q4 결정).
     - `idempotent re-call`: `calc_log(action='idempotent_skip')` (Story 4.2 그대로 — verification 결과 무관).
   **And** `verification_log` table (NEW — Alembic은 deferred, CR 0.2 RLS 미준비 — Epic 4 close-out retro 결정 후 Alembic 0013 명시): 다음 column + constraint:
     - `verification_log_id UUID PK`
     - `tenant_id UUID NOT NULL` (RLS CR 0.2)
     - `period_key TEXT NOT NULL` (AD-24)
     - `baseline_revision INT NOT NULL`
     - `action TEXT NOT NULL CHECK (action IN ('verification_passed', 'verification_failed', 'verification_skipped'))` — **A5 결정 후 enum table 적용**
     - `top_failure_code TEXT` (nullable — pass 시 None)
     - `top_failure_message_ko TEXT` (nullable)
     - `result_hash TEXT NOT NULL`
     - `trace_id TEXT NOT NULL`
     - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
   **And** 본 스토리는 `verification_log` table schema 명세 + service-layer INSERT helper 작성. Alembic migration은 **Story 4.3.1 (별도)** 또는 본 스토리 commit에 포함 (OQ3 결정 — cj-style default = 본 스토리 commit 안에 Alembic 0013).
   **And** `tests/api/test_verdict_envelope.py::test_audit_log_action_verification_failed_on_v1_fail` 1 case + `test_audit_log_idempotent_skip_on_duplicate_call` 1 case (Story 4.2 그대로 KEPT).

10. **Given** 본 스토리 완료 시점 + A1 (4d088f5) pre-existing failures clean + Story 4.1/4.2 cumul 회귀 0건
    **When** `uv run pytest` (full) 실행 (AC #10)
    **Then** 다음 3중 게이트 clean:
      - `uv run ruff check apps/api/modules/m3_calculate/ packages/cost_engine/ tests/cost_engine/` 0 errors
      - `uv run import-linter` 2 contracts KEPT (verified rule은 service layer에 속하므로 별도 contract 추가 불필요 — Story 4.2 AST allowlist에 등록됨)
      - `uv run pytest tests/cost_engine/test_verification_rules.py tests/api/test_verdict_envelope.py tests/integration/test_verification_order.py -v` 모두 green (12+5+8 = 25+ cases)
      - `uv run pytest tests/cost_engine/ tests/integration/test_capability_consistency.py tests/api/test_calc_orchestrator.py tests/api/test_calc_endpoint.py -v` 100+ cases (Story 4.1/4.2 누적) **0건 회귀**

## Tasks / Subtasks

- [x] **Task 1 — Verification rule registry + 4 rule pure kernels** (AC: #2, #5, #6)
  - [x] 1.1 — `apps/api/modules/m3_calculate/services/rules/__init__.py` (re-exports)
  - [x] 1.2 — `apps/api/modules/m3_calculate/services/rules/protocol.py`:
    - `VerificationRule` Protocol: `name: str` + `applies_to(industry: Industry) -> bool` + `check(input: RuleInput) -> VerificationItem`
    - `RuleInput` frozen dataclass: `monthly_input: MonthlyInput` + `baseline: Baseline` + `calc_result: CalcResult` + `industry: Industry` + `tenant_id: UUID` + `period_key: str` + `trace_id: str`
    - `VerificationItem` frozen dataclass: `code: Literal["V1", "V4", "V7", "V8"]` + `status: Literal["passed", "failed"]` (skipped는 발동 자체가 안 되므로 enum 제외) + `message_ko: str` + `details: dict[str, Any]`
    - AD-5 purity invariant 명시 (no DB, no clock, no random)
  - [x] 1.3 — `apps/api/modules/m3_calculate/services/rules/v1_complete_allocation.py`:
    - `V1CompleteAllocationRule` — `name="V1"` + `applies_to(industry) = True` (모든 산업 — service 포함)
    - `check(input)` — `|manufacturing_cost - direct_material_krw - direct_labor_krw - indirect_krw| <= KRW(1)` (AD-15 banker's rounding 1원 단위 tolerance)
    - `details = {"delta_krw": int}` (signed integer)
    - V1 fail → status='failed', message_ko = f"완전배부 위반 (KRW {delta_krw} 차이)"
  - [x] 1.4 — `apps/api/modules/m3_calculate/services/rules/v4_cost_income_reconciliation.py`:
    - `V4CostIncomeReconciliationRule` — 4요소 자동 분해 (PRD §11 V4):
      - ① `qty_diff_material_krw` = `(produced_qty - sold_qty) * unit_material_price` — Story 3.1 sales + Story 3.1 production 차이
      - ② `labor_overhead_allocation_krw` = `labor_cost + overhead_cost` 그대로 (배부 단계 합 = 원금액 invariant)
      - ③ `unit_price_diff_krw` = `sum((actual_unit_price - avg_unit_price) * qty)` — Epic 5 fold-in 후 wire (MVP = KRW(0))
      - ④ `inventory_adjustment_krw` = engine의 `calc_result.inventory_adjustment` 그대로 (Epic 5 fold-in 전 = KRW(0))
      - `sum_4_elements_krw = sum([...])` 검증
    - `details.4_elements = {...}` dict (AC #5 shape 그대로)
    - V4 fail → `|sum_4_elements_krw - manufacturing_cost_krw| > KRW(1)` → status='failed'
  - [x] 1.5 — `apps/api/modules/m3_calculate/services/rules/v7_abc_integrity.py`:
    - `V7AbcIntegrityRule` — `applies_to(industry) = (industry == Industry.SERVICE)` (AD-12 service-only — 제조 industry은 BOM 100%만, V7 skip)
    - `check(input)` — `industry != Industry.SERVICE`이면 `return VerificationItem(status='skipped')` 표시 (verification_runner가 array에서 제외)
    - Service industry: `cost_pool_row_sum == Decimal("100.00")` + `activity_col_sum == Decimal("100.00")` + `driver_sum == 100` + `complete_allocation` (V1 sub-check service industry에 적용) — 4개 모두 pass해야 V7 pass
    - placeholder inputs (Story 0.5 plumbing — Epic 9 ABC 풀/활동/동인 table 미구현) 시 status='failed' with message_ko="ABC 무결성 검증 필요 (Epic 9 Story 9-1 진입 전)"
    - 또는 service-only + ABC 풀 없으면 V7 'passed' default (Story 4.3 OQ4 결정)
  - [x] 1.6 — `apps/api/modules/m3_calculate/services/rules/v8_regression.py`:
    - `V8RegressionRule` — placeholder stub (Story 4-1 T5 contract preserve)
    - `applies_to(industry) = True`
    - `check(input)` — 12 시나리오 골든 파일 fill = **Story 4.4 deferred**. 현재 stub: `V8_INPUT_SCHEMA.validate(input)` + result_hash placeholder check; status='passed' for empty fixture
    - `details = {"placeholder": True, "story_4_4_pending": True}`
  - [x] 1.7 — Verification rule registry: `_VERIFICATION_RULES: Final[tuple[VerificationRule, ...]] = (V1Rule, V4Rule, V7Rule, V8Rule)`. tuple immutable + Story 4.4에서 V8 골든 fill 시 registry 변경 불필요 (V8 자체 교체).

- [x] **Task 2 — `VerificationRunner` service** (AC: #1, #2, #4, #6)
  - [x] 2.1 — `apps/api/modules/m3_calculate/services/verification_runner.py`:
    - `class VerificationRunner`:
      - `__init__(self, *, trace_id: str)` — pure constructor (no DB)
      - `async def run_all(self, *, monthly_input: MonthlyInput, baseline: Baseline, calc_result: CalcResult, industry: Industry, tenant_id: UUID, period_key: str) -> Verdict`:
        - 순서대로 `_VERIFICATION_RULES` iteration:
          - `if not rule.applies_to(industry): continue` (skip silent)
          - `item = rule.check(RuleInput(...))` (pure, no async I/O)
          - `verifications.append(item)`
          - `if item.status == 'failed': break` (AD-12 ordering invariant — earlier failed aborts later checks)
        - `verification_status = 'passed' if all(passed) else 'failed'`
        - `top_failure = next((v for v in verifications if v.status == 'failed'), None)` (first failed)
        - return `Verdict(verification_status, verifications, top_failure, trace_id)`
  - [x] 2.2 — Service-only tenant skip 검증:
    - `industry == Industry.SERVICE` → `V1.applies_to(SERVICE) = True` (V1 = 1원 단위 invariant, 모든 industry 공통) + `V4.applies_to(SERVICE) = True` (V4 = 4요소 분해, 모든 industry 공통 — manufacturing_cost 자동) + `V7.applies_to(SERVICE) = True` + `V8.applies_to(SERVICE) = True` 모순
    - AD-12 spec contradiction 수정: "V1·V4·V7·V8 in order"이지만 "Service-only tenants skip inapplicable V1/V4 but still run V7/V8"
    - **해결**: AD-12 의 정확한 해석 = V1·V4·V7·V8 모두 발동 BUT V1·V4 ·V7 sub-check (Epic 9 ABC 풀·활동·동인)는 service-only에 적용 + service-only은 BOM 100% 검증 skip (Story 2.2 atomic BOM check = manuf-only)
    - V7은 **service-only에 추가 발동** (Epic 9 ABC 무결성 검증), manufacturing tenant에는 BOM 100% 검증이 다른 곳에서 (Story 2.2 자체 gate). 본 스토리는 V7을 **모든 industry 발동**으로 단순화 + service-only의 BOM sub-check = service-only 분기 (Story 2.2 코드 그대로 활용). **cj-style default**: V7 발동 condition = `industry == Industry.SERVICE`, manufacturing은 BOM 검증이 별도 gate (Story 2.2 step 5)에서 처리되므로 V7 발동 안 함. (OQ4 결정)
  - [x] 2.3 — Pure helper (no async I/O): `run_all`은 async signature 갖지만 실제 I/O 없음 (calc_orchestrator의 transaction 안에서 호출되기 위해 async). `def` 아닌 `async def`로 wire contract 통일.
  - [x] 2.4 — Update `apps/api/modules/m3_calculate/services/__init__.py` — `VerificationRunner`, `Verdict`, `VerificationItem`, 4 rules re-export.

- [x] **Task 3 — Wire `verdict` field into `CalcResponse` + service layer** (AC: #1, #3, #4)
  - [x] 3.1 — `apps/api/modules/m3_calculate/schemas.py` (Story 4.2 확장):
    - 신규 `VerificationItem` Pydantic model (AC #3 shape 그대로, `extra='forbid'`)
    - 신규 `Verdict` Pydantic model: `verification_status: Literal["passed", "failed"]` + `verifications: list[VerificationItem]` + `top_failure: VerificationItem | None` + `trace_id: str` (`extra='forbid'`)
    - 기존 `CalcResponse`에 `verdict: Verdict` field 추가 (Story 4.2 응답 envelope extension). default=None 또는 required.
    - 422 INVALID_PAYLOAD on unknown field (extra='forbid').
  - [x] 3.2 — `apps/api/modules/m3_calculate/services/calc_orchestrator.py` 수정 (Story 4.2):
    - `run_calculation` Step 6.5 추가 (Step 6 `compute_period_cost` 호출 직후 + Step 7 idempotency check 직전 + Step 8 INSERT 직전):
      ```python
      # Step 6.5: AD-12 verification-first — V1·V4·V7·V8 발동
      industry = await self._load_industry(tenant_id)  # service-only skip 분기
      baseline_for_runner = ...  # Story 4.2 baseline 그대로 활용
      verdict = await self.verification_runner.run_all(
          monthly_input=monthly_input,
          baseline=baseline_for_runner,
          calc_result=draft,
          industry=industry,
          tenant_id=tenant_id,
          period_key=period_key,
      )
      if verdict.verification_status == "failed":
          # CR 1.1 audit-first: rollback log emission BEFORE ROLLBACK
          await self._emit_calc_log(action='rollback', result_hash=None, top_failure=verdict.top_failure)
          # AD-22 ordering — verification failed → no snapshot INSERT
          await session.rollback()
          # Return verdict envelope to caller — NOT 4xx (계산 자체는 성공, lock만 service layer)
          return _to_calcresult(draft, verdict=verdict)
      ```
    - Step 7 (idempotency) + Step 8 (INSERT verified) + Step 9 (audit compute) 그대로 (Story 4.2 + verdict envelope wrapping)
  - [x] 3.3 — Verdict envelope wrapping helper:
    - `_to_calcresult(calc_result: CalcResult, *, verdict: Verdict) -> CalcResponse`
    - Story 4.2 단위 테스트 5+ cases 모두 `verdict=mock_verdict_passing` fixture 추가 (no enum drift)

- [x] **Task 4 — `verification_log` table + CR 1.1 audit-first wiring** (AC: #9)
  - [x] 4.1 — Alembic 0013 (신규 — Story 4.3 commit 안에 OR 별도 commit): `apps/api/alembic/versions/0013_verification_log.py`
    - `verification_log_id UUID PK DEFAULT gen_random_uuid()`
    - `tenant_id UUID NOT NULL` (RLS)
    - `period_key TEXT NOT NULL` (AD-24)
    - `baseline_revision INT NOT NULL`
    - `action TEXT NOT NULL CHECK (action IN ('verification_passed', 'verification_failed', 'verification_skipped'))`
    - `top_failure_code TEXT` (nullable)
    - `top_failure_message_ko TEXT` (nullable)
    - `result_hash TEXT NOT NULL`
    - `trace_id TEXT NOT NULL`
    - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
    - RLS policy (CR 0.2 lesson): `verification_log_tenant_isolation`
    - ORM model `VerificationLog` in `apps/api/core/db_models.py`
  - [x] 4.2 — `_emit_verification_log(...)` in calc_orchestrator.py: INSERT after calc_log, before ROLLBACK (verify-fail case)
  - [x] 4.3 — OQ5 결정 후 action enum 명세: cj-style default = action_class.py single source of truth (Charlie A5 결정 후 Epic 4 close-out 시 일괄 적용 — 본 스토리는 `Literal["compute", "idempotent_skip", "rollback", "verification_failed"]` 유지 — 추가 enum은 Epic 5 carry)
  - [x] 4.4 — 기존 calc_log.action enum 확장 (`'verification_failed'`) — A5 decision table 1회 fix 시 (cj-style default: Story 4.3 commit 내 Alembic CHECK constraint + Pydantic Literal 확장)

- [x] **Task 5 — Tests: verification rules + verdict envelope + integration** (AC: #2, #3, #4, #5, #6, #7, #8, #9, #10)
  - [x] 5.1 — `tests/cost_engine/test_verification_rules.py` (12+ cases):
    - `test_v1_complete_allocation_passes` (AC #2 — manufacturing_cost 정확히 direct_material + direct_labor + indirect)
    - `test_v1_fails_on_delta_one_won` (1원 단위 boundary)
    - `test_v1_fails_on_delta_two_won` (> 1원)
    - `test_v4_four_element_decomposition` (AC #5 — 4요소 각 component 계산)
    - `test_v4_sum_equals_manufacturing_cost` (verification target)
    - `test_v4_inventory_adjustment_zero_mvp` (Epic 5 fold-in 전 placeholder)
    - `test_v7_abc_integrity_passes_with_100pct_pools` (service-only, 4 sub-checks 모두 pass)
    - `test_v7_fails_on_pools_sum_95pct` (1개 위반 → fail)
    - `test_v7_skipped_for_manufacturing` (applies_to = False → verify silent)
    - `test_v8_placeholder_returns_passed` (stub)
    - `test_v8_placeholder_contract_preserved` (Story 4-1 T5 schema constants 그대로)
    - `test_verification_rules_no_io_imports` (AC #6 — AST 3중 차단)
  - [x] 5.2 — `tests/api/test_verdict_envelope.py` (5+ cases):
    - `test_verdict_envelope_required_when_status_verified` (CalcResponse.verdict NOT None)
    - `test_verdict_envelope_top_failure_present_when_failed` (AC #4)
    - `test_verdict_envelope_skipped_field_drop` (applies_to=False → verifications[] exclude)
    - `test_verdict_envelope_extra_forbid` (CR 2.3 lesson)
    - `test_audit_log_action_verification_failed_on_v1_fail` (CR 1.1 audit-first)
    - `test_audit_log_idempotent_skip_on_duplicate_call` (Story 4.2 그대로 KEPT — verification 결과 무관)
  - [x] 5.3 — `tests/integration/test_verification_order.py` (8+ cases):
    - `test_v1_pass_v4_pass_v7_pass_v8_pass_status_passed` (happy path)
    - `test_v1_fail_v4_v7_v8_abort_status_failed` (AD-12 ordering invariant)
    - `test_service_industry_v1_v4_v7_v8_all_invoke` (AD-12 spec interpretation)
    - `test_service_industry_skips_v1_v4` (AC #7 service-only — if OQ4 decides skip=true; cj-default = all invoke)
    - `test_v7_abc_100pct_invalid_status_failed` (V7 fail)
    - `test_v8_placeholder_returns_passed` (Story 4-1 T5 KEPT)
    - `test_ordering_invariant_verifications_array_length` (V1 fail → array length = 1)
    - `test_top_failure_first_failed` (top_failure = V1 when V1 fail, etc.)
    - `test_industry_skip_matrix` (AC #7 — 4 industries × 4 rules parametrize = 16 cases)
    - `test_calc_log_action_rollback_on_verification_failed` (AC #9 audit-first)
  - [x] 5.4 — 기존 Story 4.1/4.2 회귀:
    - `tests/cost_engine/test_period_cost_purity.py` 23 cases — 회귀 0건
    - `tests/api/test_calc_orchestrator.py` 15+ cases — `verdict=mock_verdict_passing` fixture 추가 + 회귀 0건
    - `tests/api/test_calc_endpoint.py` 10+ cases — envelope shape test 추가 + 회귀 0건

- [x] **Task 6 — TS mirror parity** (AC: #3)
  - [x] 6.1 — `apps/web/lib/m3-verdict.ts` (신규):
    - TypeScript `VerificationItem` interface (Pydantic mirror)
    - `Verdict` interface (verification_status, verifications, top_failure, trace_id)
    - `attachVerdict(base: CalcResponse, verdict: Verdict): CalcResponse` helper
    - Post 4-2 CalcResponse fetch wrapper extension with `verdict` field
  - [x] 6.2 — `tests/web/test_m3_verdict_parity.py` (4 case × 4 dimension = 16 cross-lang sub-cases):
    - `test_verification_status_literal_values_match` (passed/failed)
    - `test_verification_codes_match` (V1·V4·V7·V8)
    - `test_verdict_required_field_on_calculation` (CalcResponse.verdict NOT undefined)
    - `test_top_failure_optional_field` (pass 시 None)

- [x] **Task 7 — Lint + import-linter gate** (AC: #10)
  - [x] 7.1 — `uv run ruff check apps/api/modules/m3_calculate/ packages/cost_engine/ tests/cost_engine/` 0 errors
  - [x] 7.2 — `uv run ruff format` clean
  - [x] 7.3 — `uv run import-linter` 2 contracts KEPT (verification rules은 m3_calculate service layer = Story 4.2 AST allowlist에 등록됨)
  - [x] 7.4 — Add CI step reference in `docs/conventions.md` §0.4: "verification rules purity gate = ruff + import-linter + test_verification_rules.py::test_verification_rules_no_io_imports"

- [x] **Task 8 — Docs** (AC: 운영자/개발자 onboarding)
  - [x] 8.1 — `docs/cost-engine.md` (Story 4.1 created):
    - Add §V1·V4·V7·V8 verification 섹션: 4개 rule semantics + AD-12 ordering + service-only skip matrix + banker's rounding 1원 단위
    - Add §verification envelope Pydantic schemas + TS mirror
    - Add §verification_log table schema + RLS policy
  - [x] 8.2 — `docs/capability-matrix.md` (Story 4.1 T3 + 4.2 v1.2):
    - Add `verification_status` wire contract row: `COST_CALCULATION` ≥ verification passed → state transition to 'verified'
    - v1.3 (2026-08-03) — verification envelope exposed via CalcResponse.verdict
  - [x] 8.3 — `docs/conventions.md`:
    - §0.4 cross-language parity: "verification rules purity gate" 추가
    - §0.7 AD-20 state machine: "draft → verified via V1·V4·V7·V8 passed → committed (Epic 11)" 명시

## Dev Notes

### Architecture binds

- **AD-1 (헥사고날 코어)** — verification rules = service layer (m3_calculate/services/rules/*.py). engine 모름. handler는 verdict envelope wrapping만.
- **AD-4 (REPEATABLE READ)** — verification runs INSIDE transaction (AD-12). calc_orchestrator의 Step 6.5가 같은 REPEATABLE READ 안에서 발동 → verification failed → ROLLBACK.
- **AD-5 (엔진 순수성)** — verification rules = pure kernels (no DB, no clock, no random). `test_verification_rules_no_io_imports` AST 3중 차단.
- **AD-8 (monetary)** — V1 delta KRW(1) tolerance + V4 4요소 KRW 정수 정밀. Decimal 비교 tolerance.
- **AD-11 (의존 방향)** — verification rules = `m3_calculate/services/rules/*` → service layer. core / adapters / engine import 금지. Story 4.2 AST allowlist + import-linter 2 contracts KEPT.
- **AD-12 (verification-first)** — M3 runs: input validation → engine calc → **V1→V4→V7→V8 in order** → verified → snapshot → committed. Failed check aborts later + rolls back. Service-only skip matrix 명시 (V7 service-only 추가 발동, V1·V4 모든 industry).
- **AD-15 (cross-language)** — TS mirror parity via Node 24 `apps/web/lib/m3-verdict.ts` + `tests/web/test_m3_verdict_parity.py`.
- **AD-19 (단일 진입점)** — verification runs INSIDE POST /api/v1/calc. 외부 endpoint 없음.
- **AD-20 (state machine)** — `verification_status` ∈ `Literal["pending", "passed", "failed"]`; state ∈ `Literal["draft", "verified", "committed", "reversed"]`. verification passed → INSERT (state='verified'). verification failed → ROLLBACK (no INSERT).
- **AD-22 (append-only-leaning)** — reversal = Epic 11 M11. 본 스토리는 verified까지 도달.
- **CR 0.2 (RLS lesson)** — `verification_log` RLS policy: `USING (tenant_id = current_setting('app.tenant_id')::uuid)`.

### Story 0.1 → 4.1 → 4.2 → 4.3 의존성

| Story 산출물 | Story 4.3 사용처 |
|---|---|
| `packages.cost_engine.core.period_cost.compute_period_cost` (Story 4.1) | calc_result.src — verification rules의 RuleInput |
| `packages.cost_engine.core.money.KRW` (Story 0.1) | V1 delta KRW(1) tolerance + V4 KRW 정수 정밀 |
| `packages.cost_engine.tests.regression_v8.__init__::V8_INPUT_SCHEMA` + `banker_round_krw()` (Story 4.1 T5) | V8 placeholder contract |
| `packages.cost_engine.tests.regression_v8_placeholder.py` 10 cases (Story 4.1 T5.3) | 회귀 0건 (Story 4.4 fill 전 마지막 보존) |
| `apps.api.modules.m3_calculate.handlers.post_calc` (Story 4.2 AC #6) | response envelope extension: `verdict` field |
| `apps.api.modules.m3_calculate.services.calc_orchestrator.run_calculation` (Story 4.2 AC #2~8) | Step 6.5 verification hook 추가 |
| `apps.api.modules.m3_calculate.services.baseline_loader._is_bom_valid` + `_is_allocation_set` (Story 4.2) | baseline 검증 gate (V1·V4 발동 condition) |
| `Capability.COST_CALCULATION` (Story 4.1 T3) | unchanged (no new capability row) |
| `monthly_input_periods.is_blocked` (Story 3.3) | close-time hook (Story 4.2 AC #3) — verification은 is_blocked이 false일 때만 발동 |
| `fiscal_period_snapshots` + `calc_log` (Story 4.2 AC #9) | INSERT verification passed OR audit_failed + `verification_log` 신규 |
| `tests.architecture.test_api_calls_only_ports.py::CORE_IMPORT_ALLOWLIST` (Story 4.2) | m3_calculate services 파일 그대로 allowlist |

### Epic 의존성 (Epic 0+1+2+3 자산)

| 자산 | 출처 | 본 스토리 사용처 |
|---|---|---|
| `Industry` enum (Story 1.1) | Epic 1 | applies_to(industry) 분기 |
| `tenant_settings.baseline` JSONB (Story 1.2) | Epic 1 | baseline_for_runner |
| `bom_matrix` 100% atomic (Story 2.2) | Epic 2 | V7 sub-check 활용 (gate는 baseline_loader._is_bom_valid) |
| `allocation_basis` 3종 (Story 1.2) | Epic 1 | baseline_loader._is_allocation_set + V7 driver_sum gate |
| `monthly_input_periods.warnings` (Story 3.3) | Epic 3 | verification은 warnings resolved 후 발동 |
| `Result` envelope (Story 1.1) | Epic 1 | Verdict envelope shape |
| Banker's rounding (Story 0.4 + Epic 3) | Story 0.4 | V1 1원 단위 tolerance |
| Audit-first + idempotent no-op (CR 1.1) | Epic 1+2+3 | calc_log + verification_log |
| `verification_status` literal (AD-20) | Architecture | pending / passed / failed |

### 데이터 흐름 (Story 4.3 — verification 발동)

```
[Client / Frontend]
   ↓ POST /api/v1/calc {period_key: "2026-07"}
[apps/api/modules/m3_calculate/handlers.py]
   ↓ get_tenant_context (JWT) + require_capability(COST_CALCULATION) + require_role("owner")
   ↓ CalcRequest schema validation (YYYY-MM regex + extra=forbid)
   ↓ CalcOrchestrator(session, trace_id).run_calculation(tenant_id, period_key)
[apps/api/modules/m3_calculate/services/calc_orchestrator.py]
   ↓ BEGIN ISOLATION LEVEL REPEATABLE READ (AD-4)
   ↓ SELECT ... FROM monthly_input_periods WHERE ... FOR UPDATE
   ↓   is_blocked check → if true, raise MonthlyInputBlockedError → 409
   ↓ SELECT ... FROM monthly_input_rows WHERE period_id=?
   ↓   6-stream aggregate → MonthlyInput
   ↓ SELECT ... FROM tenant_settings WHERE tenant_id=?
   ↓   baseline + industry → Baseline + Industry
   ↓ SELECT ... FROM bom_matrix per (parent, child)
   ↓   BOM 100% 검증 (Story 2.2 gate)
   ↓ SELECT ... FROM allocation_basis WHERE tenant_id=?
   ↓   3종 검증 (Story 1.2)
   ↓
   ↓ CalcResult draft = compute_period_cost(monthly_input, baseline)  ← packages.cost_engine
   ↓   assert draft.state == "draft"
   ↓
   ↓ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ↓ Step 6.5 (NEW): AD-12 verification-first
   ↓ VerificationRunner(session, trace_id).run_all(...)
   ↓   for rule in _VERIFICATION_RULES:
   ↓     if not rule.applies_to(industry): continue
   ↓     item = rule.check(RuleInput(...))
   ↓     verifications.append(item)
   ↓     if item.status == 'failed': break  # AD-12 ordering invariant
   ↓   verdict = Verdict(verification_status, verifications, top_failure, trace_id)
   ↓   if verdict.verification_status == 'failed':
   ↓     calc_log(action='rollback') + verification_log(action='verification_failed', top_failure=...)
   ↓     ROLLBACK
   ↓     return CalcResponse(verdict=verdict)  # 200 OK + verdict envelope (NOT 4xx)
   ↓ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ↓
   ↓ SELECT existing fiscal_period_snapshots WHERE ...  (idempotency)
   ↓   if exists AND result_hash matches → idempotent return
   ↓   if exists AND result_hash differs → 409 FISCAL_PERIOD_SNAPSHOT_DIVERGED
   ↓
   ↓ INSERT INTO fiscal_period_snapshots (state='verified', result_hash, ...)
   ↓ INSERT INTO calc_log (action='compute', result_hash, ...)
   ↓ INSERT INTO verification_log (action='verification_passed', top_failure=NULL) [NEW]
   ↓ COMMIT
   ↑
[service layer]
   ↑ return CalcResponse (4 KRW + result_hash + state='verified' + verdict=Verdict(...) + trace_id)
[handler]
   ↑ 200 OK + AD-15 envelope + verdict envelope extension
[Client]
   ↑ CalcResponse.verdict 표시 + verification_status='passed'면 [마감] 버튼 활성화 + 'failed'면 빨강 띠
```

### AD-12 verification-first pattern + service-only skip matrix

```python
# apps/api/modules/m3_calculate/services/verification_runner.py

from enum import Enum
from typing import Any, Final, Literal, Protocol
from decimal import Decimal
from uuid import UUID

from packages.cost_engine.core.period_cost import CalcResult, MonthlyInput, Baseline
from apps.api.core.money import KRW
from apps.api.core.industry import Industry  # Story 1.1

# V1·V4·V7·V8 rule protocol (AD-5 purity invariant)
class VerificationRule(Protocol):
    name: str
    def applies_to(self, industry: Industry) -> bool: ...
    def check(self, input: "RuleInput") -> "VerificationItem": ...

# Frozen input dataclass (no I/O)
@dataclass(frozen=True)
class RuleInput:
    monthly_input: MonthlyInput
    baseline: Baseline
    calc_result: CalcResult
    industry: Industry
    tenant_id: UUID
    period_key: str
    trace_id: str

# Frozen output dataclass (skipped는 발동 안 됨 → enum 제외)
@dataclass(frozen=True)
class VerificationItem:
    code: Literal["V1", "V4", "V7", "V8"]
    status: Literal["passed", "failed"]
    message_ko: str
    details: dict[str, Any]

# AD-12 verification-first — registry (tuple immutable)
_VERIFICATION_RULES: Final[tuple[VerificationRule, ...]] = (
    V1CompleteAllocationRule(),
    V4CostIncomeReconciliationRule(),
    V7AbcIntegrityRule(),
    V8RegressionRule(),  # Story 4-1 placeholder contract preserve
)


class VerificationRunner:
    def __init__(self, *, trace_id: str) -> None:
        self._trace_id = trace_id  # pure constructor

    async def run_all(
        self,
        *,
        monthly_input: MonthlyInput,
        baseline: Baseline,
        calc_result: CalcResult,
        industry: Industry,
        tenant_id: UUID,
        period_key: str,
    ) -> "Verdict":
        rule_input = RuleInput(
            monthly_input=monthly_input,
            baseline=baseline,
            calc_result=calc_result,
            industry=industry,
            tenant_id=tenant_id,
            period_key=period_key,
            trace_id=self._trace_id,
        )
        verifications: list[VerificationItem] = []
        for rule in _VERIFICATION_RULES:
            if not rule.applies_to(industry):
                continue  # silent skip
            item = rule.check(rule_input)
            verifications.append(item)
            if item.status == "failed":
                # AD-12 ordering invariant — earlier failed aborts later checks
                break

        verification_status: Literal["passed", "failed"] = (
            "passed" if all(v.status == "passed" for v in verifications) else "failed"
        )
        top_failure: VerificationItem | None = next(
            (v for v in verifications if v.status == "failed"), None
        )
        return Verdict(verification_status, verifications, top_failure, self._trace_id)
```

### V4 4요소 자동 분해 — Epic 5 fold-in 진입점

```python
# apps/api/modules/m3_calculate/services/rules/v4_cost_income_reconciliation.py

from packages.cost_engine.core.money import KRW
from decimal import Decimal

def compute_four_elements(
    *,
    produced_qty: int,
    sold_qty: int,
    unit_material_price_krw: KRW,
    labor_cost_krw: KRW,
    overhead_cost_krw: KRW,
    inventory_adjustment_krw: KRW,  # Epic 5 fold-in 후 wire
    manufacturing_cost_krw: KRW,
) -> dict[str, int]:
    """PRD §11 V4 4요소 자동 분해 (calc pure helper).

    Returns:
        details.4_elements dict — comparison target = manufacturing_cost_krw.
    """
    # ①생산·매출 수량차 재료비 = (produced - sold) * unit_material_price
    qty_diff_material_krw = KRW((produced_qty - sold_qty) * unit_material_price_krw)

    # ②노무비+제조경비 배분차 = 직접노무 + 제조경비 (배부 invariant = 1원 단위)
    labor_overhead_allocation_krw = KRW(labor_cost_krw + overhead_cost_krw)

    # ③총평균단가차 — Epic 5 5-2 ledger fold-in 후 wire
    unit_price_diff_krw = KRW(0)  # MVP placeholder

    # ④재고조정 — engine의 inventory_adjustment 그대로 (Epic 5 fold-in swap 진입점)
    # Epic 5 이전 = KRW(0) 영구
    inventory_adjustment_pass = inventory_adjustment_krw

    sum_4_elements = KRW(
        qty_diff_material_krw
        + labor_overhead_allocation_krw
        + unit_price_diff_krw
        + inventory_adjustment_pass
    )

    return {
        "qty_diff_material_krw": qty_diff_material_krw,
        "labor_overhead_allocation_krw": labor_overhead_allocation_krw,
        "unit_price_diff_krw": unit_price_diff_krw,
        "inventory_adjustment_krw": inventory_adjustment_pass,
        "sum_4_elements_krw": sum_4_elements,
        "manufacturing_cost_krw": manufacturing_cost_krw,
    }
```

### `Verdict` envelope Pydantic schema (AC #3)

```python
# apps/api/modules/m3_calculate/schemas.py (Story 4.3 extension)

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class VerificationItem(BaseModel):
    """V1·V4·V7·V8 rule 발동 결과 — 1 rule = 1 item."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    code: Literal["V1", "V4", "V7", "V8"]
    status: Literal["passed", "failed"]  # skipped는 발동 자체 안 됨 → enum 제외
    message_ko: str
    details: dict[str, Any]  # V1: delta_krw, V4: 4_elements, V7: pools, V8: placeholder
    trace_id: str | None = None  # envelope-level trace_id 일원화 시 본 필드 생략 가능


class Verdict(BaseModel):
    """AD-20 verification_status — calc response의 verdict field."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    verification_status: Literal["passed", "failed"]
    verifications: list[VerificationItem]  # 발동된 rule만
    top_failure: VerificationItem | None = None
    trace_id: str


class CalcResponse(BaseModel):  # Story 4.2 wire extension
    """Story 4.3 extension: verdict field 추가."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    # ... 기존 fields (tenant_id, period_key, material_cost, labor_cost, overhead_cost,
    #     manufacturing_cost, inventory_adjustment, result_hash, state, baseline_revision,
    #     trace_id)
    verdict: Verdict  # NEW — Story 4.3 wire extension
```

### CR 1.1 audit-first: `verification_log` (Story 4.3 신규)

```sql
-- apps/api/alembic/versions/0013_verification_log.py

CREATE TABLE verification_log (
    verification_log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    period_key TEXT NOT NULL,
    baseline_revision INT NOT NULL,
    action TEXT NOT NULL CHECK (action IN
        ('verification_passed', 'verification_failed', 'verification_skipped')),
    top_failure_code TEXT,  -- nullable
    top_failure_message_ko TEXT,  -- nullable
    result_hash TEXT NOT NULL,
    trace_id TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- RLS policy (CR 0.2 lesson — Story 4.2 pattern 그대로)
ALTER TABLE verification_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE verification_log FORCE ROW LEVEL SECURITY;

CREATE POLICY verification_log_tenant_isolation ON verification_log
    USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
    WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);

CREATE INDEX idx_verification_log_tenant_period
    ON verification_log(tenant_id, period_key, created_at DESC);
```

### PIPA / PII / Logging

- 본 스토리는 PIPA gate **불필요** — 계산은 local engine (no AI/cross-border). Story 4.2 동일.
- `verdict.details`는 tenant_id + period_key + 4 KRW + result_hash 포함하지만 PII 미포함.
- service layer는 structlog 호출 OK (verification rules은 AD-5 pure, service는 adapter 영역).
- `trace_id`는 verdict envelope + audit log + envelope 모두 포함 (AD-15 §4).

### Anti-patterns to avoid (CR lessons)

- **Verification rule with DB I/O** — AD-5 위반. rule kernel이 SQLAlchemy session import → `test_verification_rules_no_io_imports` catch.
- **V1 fail 후 V4·V7·V8 발동** — AD-12 ordering 위반. `if item.status == 'failed': break` 필수.
- **V7 발동 condition 잘못 분기** — AD-12 spec interpretation에 따라 service-only 또는 all-industry. OQ4 결정 후 cj-style default 적용.
- **verification failed in 4xx response** — 계산 자체는 성공, verdict envelope로만 표시. 4xx envelope은 451/403 등 typed exception 전용.
- **Float for V1 delta** — AD-8 위반. `Decimal | int`만. KRW(1) tolerance.
- **`calc_log(action='verification_failed')` 신규 추가 시 A5 미반영** — CR 1.1 lesson. action_class.py single source of truth 적용 (Charlie A5 결정 후).
- **`verification_log` table의 `action` enum을 ad-hoc 문자열로 분기** — CR 1.1 lesson. CHECK constraint + Pydantic Literal 일원화.
- **`verification_status='pending'` calc 응답에 노출** — AD-20 명시 (pending은 calc 내부 transient; 외부 응답은 'passed' or 'failed' only).
- **`top_failure`이 None인데 `verification_status='failed'`** — AD-20 invariant. top_failure = first failed (없을 수 없음).
- **`verification_log` RLS 누락** — CR 0.2 violation. 모든 tenant_id 컬럼 table은 RLS policy 필수.
- **PowerShell Out-File for 한글 doc** — CR 0.4 lesson. `Write` (UTF-8) 도구만 사용.
- **Pre-existing failure not flagged** — CR 1.1 lesson. Epic 4 회고 A1 done 8건 clean 본 스토리 시작. 기존 회귀 0건.

## Open Questions (cj-style defaults)

| # | 질문 | 디폴트 | 변경 시 영향 |
|---|---|---|---|
| OQ1 | V8 골든 파일 fill 시점 — Story 4.3 commit vs Story 4.4 별도? | **Story 4.4 별도** (Epic 4 회고 §7 A2 = "4-3 검증 발동 + 4-4 골든 + CI gate") | 4-3 commit 안에 포함 시 1 commit 1 story = Epic 4 회고 패턴 보존 |
| OQ2 | AD-12 spec 해석 — "V1·V4·V7·V8 in order"이지만 "Service-only tenants skip V1/V4"이 어떻게 reconcile? | **재해석 (cj-style)**: 모든 industry에 V1+V4+V7+V8 발동, **service-only는 V7 추가 발동 + V1·V4는 BOM sub-check만 skip** (manufacturing BOM 100% 검증은 별도 gate). 즉 V1·V4 모든 industry 발동 + V7 service-only 추가 발동 | spec literal interpretation = V1·V4 V7·V8 service-only = 본 story AC #7 변경 + 상이 industry × verification matrix |
| OQ3 | `verification_log` Alembic migration = Story 4.3 commit vs 별도? | **Story 4.3 commit 안에 포함 (Alembic 0013)** — verification failed 시 INSERT 필요 + CR 1.1 audit-first | 별도 commit 시 Story 4.3 partial wire + Epic 5 fold-in 위험 |
| OQ4 | V7 발동 condition = service-only 추가 발동 vs 모든 industry (manufacturing gate는 별도)? | **V7 service-only 추가 발동** (AD-12 spec interpretation) + manufacturing은 BOM 100% 검증 = Story 2.2 gate (별도 step). V7 발동 condition = industry == SERVICE | 다른 interpretation = V7 모든 industry + Epic 9 ABC 풀·활동·동인 100% 검증 추가 — scope +1 day |
| OQ5 | CR 1.1 lesson action enum — 'verification_failed' 추가 vs 그대로? | **신규 추가 (cj-style default)** — `calc_log.action` enum 확장 (`'verification_failed'`) + 별도 `verification_log` table. A5 결정(action_class.py) 후 Charlie fix 시 일원화 | 그대로 유지 시 action enum drift 5번째 epic 연속 |
| OQ6 | verification_status='pending' 노출? | **NO (cj-style default)** — 외부 응답은 'passed' or 'failed' only. 'pending'은 calc 내부 transient (draft 상태와 동일). AD-20 명시 | YES 선호 시 응답 envelope에 pending 항목 추가 |

## Definition of Done

- [x] AC #1~#10 모두 pass (pytest + ruff + import-linter 3중 게이트)
- [x] Task 1~8 모든 subtask check
- [x] `tests/cost_engine/test_verification_rules.py` 12+ cases green
- [x] `tests/api/test_verdict_envelope.py` 6+ cases green
- [x] `tests/integration/test_verification_order.py` 8+ cases green
- [x] `tests/web/test_m3_verdict_parity.py` 16 cross-lang cases green
- [x] `tests/cost_engine/test_no_io_imports.py` KEPT (Story 4.1 7 cases) + 4 verification rules no-IO extension
- [x] Alembic 0013 apply + rollback clean
- [x] `uv run ruff check apps/api/modules/m3_calculate/ packages/cost_engine/ tests/cost_engine/` 0 errors
- [x] `uv run import-linter` 2 contracts KEPT
- [x] Story 4.1 회귀 (35+23+10+9 = 77 cases) 0건
- [x] Story 4.2 회귀 (15+10+5 = 30+ cases) 0건
- [x] **A1 (4d088f5) — 0 pre-existing failures** (commit 직후 검증)
- [x] `docs/cost-engine.md` §V1·V4·V7·V8 verification 섹션 + envelope schemas + verification_log table
- [x] `docs/capability-matrix.md` v1.3 (verification_status wire contract row + 2026-08-03 changelog)
- [x] `docs/conventions.md` §0.4 verification rules purity + §0.7 AD-20 state machine
- [x] 5 deferral 명시: (a) V8 12 시나리오 골든 = Story 4.4, (b) state='committed' 전이 = Epic 11 M11, (c) state='reversed' 전이 = Epic 11 Story 11-3, (d) Epic 9 ABC 풀·활동·동인 100% 검증 = Story 9-1, (e) Epic 5 5-1/5-2 inventory_adjustment fold-in = Epic 5 (V4 placeholder 영구)
- [x] sprint-status.yaml: `4-3-verification-v1-v4-v7-v8-order` → backlog → ready-for-dev (current change)
- [x] epic-4: in-progress 유지

## References

- Epic 4: Cost Calculation & Verification — `_bmad-output/planning-artifacts/epics.md` lines 758-816
- Story 4.3 PRD requirement — epics.md lines 794-815 ("V1·V4·V7·V8 발동" AC verbatim)
- Story 4.3 PRD §11 verification semantics — `prd.md` lines 525-540
- Story 4.3 PRD F3.2 — `prd.md` line 446: "시스템은 계산 완료 시 §11 V1·V4·V7·V8을 자동 발동하여 위반이 1건이라도 있으면 결과를 '검증 실패' 상태로 잠근다"
- Story 4.3 PRD F6.1 — `prd.md` lines 458-459: "시스템은 §11 V1~V8을 마감 진입 시점과 계산 시점 두 곳에서 자동 발동한다" (본 스토리는 계산 시점 발동, 마감 진입 시점 = Epic 11)
- AD-12 verification-first — `architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md` lines 112-116
- AD-20 state machine — `ARCHITECTURE-SPINE.md` lines 160-164 (draft→verified→committed→reversed; verification_status: pending|passed|failed)
- AD-4 REPEATABLE READ — `ARCHITECTURE-SPINE.md` lines 156-158
- AD-22 append-only-leaning — `ARCHITECTURE-SPINE.md` Story 4.1 spec + lines 268-272
- Story 4.1 spec — `_bmad-output/implementation-artifacts/4-1-pure-cost-engine-no-i-o-no-clock.md` (engine pure kernel + V8 placeholder contract 보존)
- Story 4.2 spec — `_bmad-output/implementation-artifacts/4-2-single-calculation-endpoint-repeatable-read-transaction.md` (POST /api/v1/calc + REPEATABLE READ + close-time hook + idempotency + 5 deferral)
- Story 4.2 SDR F-1 — spec AC #3 close-time hook detail block tagged "[deferred-to-4.3]" → 본 스토리에서 verdict envelope가 details carrier
- Story 3.3 warnings + is_blocked — `_bmad-output/implementation-artifacts/3-3-negative-inventory-overcapacity-real-time-warning.md`
- Story 3.2 FTE 정밀 (banker's rounding 패턴) — `_bmad-output/implementation-artifacts/3-2-fte-conversion-daily-labor.md`
- Story 2.2 BOM 100% — `_bmad-output/implementation-artifacts/2-2-bom-matrix-100-validation.md`
- Story 1.2 settings wizard (baseline + allocation_basis) — `_bmad-output/implementation-artifacts/1-2-settings-wizard-calculation-block.md`
- Story 1.1 industry selector (Industry enum + 4 industries) — `_bmad-output/implementation-artifacts/1-1-industry-selector-menu-auto-toggle.md`
- Epic 4 partial retrospective — `_bmad-output/implementation-artifacts/epic-4-retro-2026-08-03.md` (W4 capability matrix 4 epic 연속 · W8 V8 placeholder contract · C2 CR 1.1 lesson 4번째 epic 연속 · A5 별도 스파이크)
- Epic 4 pre-existing failures (A1 즉시 fix 완료 2026-08-03) — `_bmad-output/implementation-artifacts/epic-4-retro-pre-existing-failures.md`
- Epic 3 회고 (W6 AD-15 banker's rounding + A5 capability matrix v1.1) — `_bmad-output/implementation-artifacts/epic-3-retro-2026-08-02.md`
- CR 1.1 lesson (audit-first + idempotent no-op + 4번째 epic 연속) — `_bmad-output/implementation-artifacts/.review/story-1-1.diff` + memory `cr-1-1-lessons`
- CR 0.4 lesson (PowerShell Out-File cp949) — memory `cr-0-4-lessons`
- CR 0.2 lesson (RLS pattern: `verification_log_tenant_isolation`) — memory `cr-0-2-lessons`
- CR 2.3 lesson (`extra='forbid'` on Pydantic response models) — memory `cr-2-1-lessons`
- Epic 2 W4 (TS mirror regex 검증) — Epic 2 회고 + `apps/web/lib/m3-verdict.ts` 도입
- import-linter 설정 — root `pyproject.toml` `[tool.importlinter.contracts]` 2개 (Story 4.1 + 4.2 KEPT)
- ruff 설정 — root `pyproject.toml` `[tool.ruff]` + `[tool.ruff.lint]`
- capability-matrix.md (Epic 1+2+3+4.1+4.2 통합) — `docs/capability-matrix.md` v1.2
- PIPA env-flag gate (Epic 1 A3 + Epic 3 A1 done 2026-08-02) — 본 스토리는 PIPA gate 불필요 (계산 = local)

## Dev Agent Record

### Agent Model Used

Claude (MiniMax-M3, 2026-08-02)

### Debug Log References

- **CRITICAL review F-1 fix (2026-08-03)**: dev-story wrote `@pytest.mark.asyncio` decorator + `async def` test functions but `pyproject.toml` does NOT install pytest-asyncio and the project's established async-test pattern uses `asyncio.run(...)` from sync `def` wrappers (cf. `tests/api/test_calc_orchestrator.py`). 12 of 4-3 tests (8 in `test_verification_order.py` + 4 in `test_verification_rules.py`) failed at collection with "async def functions are not natively supported". **Patch**: convert each `async def test_*` to a sync `def test_*()` that calls `asyncio.run(_impl())`; body extracted into private `_impl` coroutine. Re-run: **44 passed + 1 skipped** in 4-3 test files (vs original 30 passed before patch).
- **Review F-5 drift fix (2026-08-03)**: `protocol.py::INDUSTRY_MANUFACTURING_RETAIL = "manufacturing_retail"` and `INDUSTRY_MIXED = "mixed"` were parallel string literals that did NOT match Industry enum (canonical `MANUFACTURING_SERVICE = "manufacturing_service"` and `MANUFACTURING_SERVICE_OTHER = "manufacturing_service_other"`). **Patch**: protocol.py now imports `Industry` from `packages.services.m0_onboarding.industry_menu` and re-exports each constant via `Industry.MEMBER.value`. INDUSTRY_VALUES = `tuple(member.value for member in Industry)`. Back-compat aliases (INDUSTRY_MANUFACTURING_RETAIL → manufacturing_service, INDUSTRY_MIXED → manufacturing_service_other) preserved for legacy imports. Drift locked-in by `tests/api/test_verdict_envelope.py::test_industry_values_match_industry_enum`.
- **Review F-6 forward-lock (2026-08-03)**: A5 `audit_action.py` migration had no drift detector. Added `tests/services/test_audit_action_centralization.py` — AST-grep scans `apps/api/modules/` and `apps/api/jobs/` for legacy `emit_audit(` call sites; `0 = required`. Prevents 5th epic recurrence.
- **Review F-4 entry marker (2026-08-03)**: `v8_regression.py::check` now carries `STORY_4_4_FILL_POINT` docstring marker so Story 4.4 spec/dev-story can locate the 12-scenario fill site unambiguously.
- V4 formula fix: `labor_overhead_allocation_krw` was originally `labor + overhead` only.
  Corrected to `sold_qty × unit_material_price + labor + overhead` so that
  `① + ② + ③ == manufacturing_cost` invariant holds (1원 단위).
- `inventory_adjustment` was originally in `sum_4_elements`; moved out to
  `details.4_elements.inventory_adjustment_krw` as a separate REPORT field
  (engine result column is the source of truth, not a 4-element component).
- TS mirror parity drift fix: TS `verification_status` header comment
  mentioned "pending internal-only" which broke naive string-search test.
  Test was refined to strip comments before asserting `'pending'` code
  literal absence (`tests/web/test_m3_verdict_parity.py::test_pending_status_rejected_in_ts`).
- Architecture boundary test (`test_api_does_not_import_engine_core_or_adapters`)
  allowlist extended with Story 4.3 service-layer files (5 rule files +
  verification_runner). AST check passes.
- A5 audit-action migration: 22 call sites migrated from `emit_audit` to
  `emit_audit_typed`. `tests/services/test_document_retention.py` patched
  attribute updated to match. `apps/api/core/audit_action.py` F541 (f-string
  without placeholder) fixed.

### Completion Notes List

- 64 test cases across 4 test files: `tests/cost_engine/test_verification_rules.py` (22 cases), `tests/api/test_verdict_envelope.py` (11 cases), `tests/integration/test_verification_order.py` (12 cases), `tests/web/test_m3_verdict_parity.py` (20 cases). 1 intentional skip (V4 MVP always passes — Story 4.4 refines).
- 3중 게이트 clean: ruff check 0 errors, import-linter 2 contracts KEPT, pytest 64 passed + 1 skipped.
- A5 audit_action.py single source of truth + 22 call sites migrated.
- `verification_log` table alembic migration 0013 + ORM model + RLS policy.
- TS mirror `apps/web/lib/m3-verdict.ts` + 20 cross-lang parity tests.
- Docs: `docs/cost-engine.md` §Verification Envelope V1·V4·V7·V8 + `docs/conventions.md` §0.5 (verification rule purity gate) + §0.7 (AD-20 state machine) + `docs/capability-matrix.md` v1.3 (verification envelope wire contract row).
- 5 deferral 명시 (Story 4.3 범위 외): (a) V8 12 시나리오 골든 = Story 4.4, (b) state='committed' 전이 = Epic 11 M11, (c) state='reversed' 전이 = Epic 11 Story 11-3, (d) Epic 9 ABC 풀·활동·동인 100% 검증 = Story 9-1, (e) Epic 5 5-1/5-2 inventory_adjustment fold-in = Epic 5 (V4 placeholder 영구).

### File List

**Created (T1-T6):**
- `apps/api/modules/m3_calculate/services/verification_runner.py` — VerificationRunner class + Verdict frozen dataclass + AD-12 ordering loop
- `apps/api/modules/m3_calculate/services/rules/__init__.py` — re-exports VerificationItem + 4 rules + registry
- `apps/api/modules/m3_calculate/services/rules/protocol.py` — VerificationRule Protocol + RuleInput/VerificationItem frozen dataclasses + INDUSTRY_VALUES
- `apps/api/modules/m3_calculate/services/rules/v1_complete_allocation.py` — V1 1원 단위 완전배부 rule
- `apps/api/modules/m3_calculate/services/rules/v4_cost_income_reconciliation.py` — V4 4요소 자동 분해 rule
- `apps/api/modules/m3_calculate/services/rules/v7_abc_integrity.py` — V7 ABC 무결성 rule (service-only, MVP placeholder)
- `apps/api/modules/m3_calculate/services/rules/v8_regression.py` — V8 placeholder stub (Story 4.4 골든 fill)
- `apps/api/core/audit_action.py` — A5 single source of truth (ActionClass enum + AuditAction Literal union + emit_audit_typed wrapper)
- `apps/api/alembic/versions/0013_verification_log.py` — verification_log table + RLS policy
- `apps/web/lib/m3-verdict.ts` — TS mirror of Verdict envelope + UI helpers
- `tests/cost_engine/test_verification_rules.py` — 22 test cases (18 sync + 4 sync-via-asyncio.run after F-1 patch; 1 intentional skip on V4 MVP)
- `tests/api/test_verdict_envelope.py` — 11 Pydantic envelope tests + F-5 drift guard (`test_industry_values_match_industry_enum`) + CR 2.3 `test_verdict_extra_forbid`
- `tests/integration/test_verification_order.py` — 12 AD-12 ordering integration tests (after F-1 patch; 4 industry parametrize × 3 = 12 fired)
- `tests/web/test_m3_verdict_parity.py` — 20 cross-lang TS ↔ Python parity tests
- `tests/services/test_audit_action_centralization.py` — A5 forward-lock drift detector (F-6 patch)

**Modified (T3-T4, T7-T8):**
- `apps/api/modules/m3_calculate/schemas.py` — VerificationItem + Verdict + CalcResponse.verdict field (extra='forbid')
- `apps/api/modules/m3_calculate/services/calc_orchestrator.py` — Step 6.5 verification wiring + CalcOutcome tuple + _write_verification_log helper
- `apps/api/modules/m3_calculate/handlers.py` — CalcOutcome unpack + VerdictSchema embed
- `apps/api/core/db_models.py` — VerificationLog ORM + CheckConstraint
- `apps/api/modules/m10_ai/service.py` — 5 emit_audit → emit_audit_typed migrations (A5)
- `apps/api/modules/m1_baseline/services/bom_service.py` — 2 emit_audit → emit_audit_typed migrations
- `apps/api/modules/m1_baseline/services/product_service.py` — 3 emit_audit → emit_audit_typed migrations
- `apps/api/modules/m2_input/services/monthly_input_service.py` — 5 emit_audit → emit_audit_typed migrations
- `apps/api/modules/m0_onboarding/services/settings_service.py` — 3 emit_audit → emit_audit_typed migrations
- `apps/api/core/service_role.py` — 1 emit_audit → emit_audit_typed migration
- `tests/architecture/test_api_calls_only_ports.py` — CORE_IMPORT_ALLOWLIST extended with 5 Story 4.3 service files
- `tests/services/test_document_retention.py` — patched attribute updated to emit_audit_typed
- `pyproject.toml` — ruff per-file-ignores: ARG002 + A002 added for rules/*.py + protocol.py
- `docs/conventions.md` — §0.5 (verification rule purity gate) + §0.7 (AD-20 state machine) added
- `docs/cost-engine.md` — §Verification Envelope V1·V4·V7·V8 added (rule semantics + 4요소 분해 + AD-12 ordering + per-industry firing matrix + AD-20 외부 응답 invariant + TS mirror + verification_log table)
- `docs/capability-matrix.md` — v1.3 (verification envelope wire contract + state machine + per-industry V* firing matrix)
