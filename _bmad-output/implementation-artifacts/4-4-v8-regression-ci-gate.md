---
baseline_commit: 4d088f5
target_key: 4-4-v8-regression-ci-gate
---

# Story 4.4: V8 Regression — 12-Scenario 골든 Fixtures + CI Gate

Status: ready-for-dev

> Epic 4 네 번째 — Story 4.3의 V8 placeholder contract (`packages/cost_engine/tests/regression_v8/__init__.py` + `apps/api/modules/m3_calculate/services/rules/v8_regression.py`)를 채워 12 시나리오 골든 파일을 실제로 발행 + `tests/regression_v8/test_regression_v8_fixtures.py` 골든 비교 wire + CI mandatory gate (`pytest -m v8_regression` required) + 12 fixture-대-골든 byte-identical match + 정밀도 0 KRW (V8 1원 단위 회귀 — NFR16 determinism).
> **모듈**: `packages/cost_engine/tests/regression_v8/fixtures/*.json` (12 NEW: 3 baseline × 4 industry matrix) + `packages/cost_engine/tests/regression_v8/fixture_loader.py` (NEW — JSON parse + validation) + `apps/api/modules/m3_calculate/services/rules/v8_regression.py` (STORY_4_4_FILL_POINT — replace placeholder stub with real 골든 compare) + `tests/regression_v8/test_regression_v8_fixtures.py` (NEW — 12+ cases) + `docs/cost-engine.md` (§V8 골든 + fixture matrix 표) + `docs/conventions.md` §0.4 cross-language parity (V8 CI gate 추가).

<!-- dev-context: Story 4.1 — V8_INPUT_SCHEMA + V8_GOLDEN_OUTPUT_STRUCTURE + banker_round_krw() placeholder contract 보존. fixture count = 0.
                    Story 4.3 — V8RegressionRule placeholder stub returns `passed` with placeholder=True for all industries. STORY_4_4_FILL_POINT marker exists in `v8_regression.py::check` docstring.
                    Epic 4 회고 W8 (V8 placeholder contract) — Story 4.4가 이 placeholder를 실제 fixture로 전환.
                    Epic 4 회고 A2 (4-3·4-4 spec 진입) — Story 4.4 spec pending. 본 spec은 4-4 진입 트리거.
                    Epic 4 회고 A5 (audit-action SSOT) — VERIFY_V8_GOLDEN_MATCH action 신규 추가 시 audit_action.py registry 동반 (CR 1.1 5번째 epic drift 방지).
                    AD-8 (monetary) — KRW 정수 정밀, 1원 단위 회귀 (NFR16).
                    AD-12 (verification-first) — V8 = verification 8번째 layer; 자리 보존만, 발동 위임 = verification_runner.py (Story 4.3).
                    AD-15 (cross-language) — TS mirror parity for V8 result_hash (apps/web/lib/v8-regression-fixtures.ts 추가 검토; 본 스토리는 골든 자체의 Python 발행 + 잠금 우선, TS mirror는 4-4.1 옵션).
                    AD-16 (determinism) — result_hash sha256 stable JSON invariant. 골든 발행 도구도 동일 정책.
                    AD-22 (append-only-leaning) — engine always state="draft" (Story 4.1). 골든 fixture state="draft" 고정.
                    CR 1.1 lesson — auditor action enum SSOT (verify_v8_golden_match 신규 시 audit_action.py 확장).
                    CR 2.3 lesson — extra='forbid' on Pydantic envelope models. V8 골든 fixture JSON schema 명시 (V8_INPUT_SCHEMA, V8_GOLDEN_OUTPUT_STRUCTURE 동일 contract).
                    CR 0.2 lesson — V8 fixture hash는 tenant-scoped, 다른 tenant의 fixture hash와 collide하면 안 됨 (period_key + tenant_id).
                    cr-4-3-lessons (F-4) — STORY_4_4_FILL_POINT marker 위치 보존. marker 기반으로 fill 진입점 식별.
                    cr-4-3-lessons (F-5 Industry SSOT) — V8 fixture industry 값은 Industry enum (manufacturing / manufacturing_service / service / manufacturing_service_other) 정확히 매핑.
                    cr-4-3-lessons (F-6 A5 forward-lock) — verify_v8_golden_match action 추가 시 emit_audit_typed() 경유; drift detector (tests/services/test_audit_action_centralization.py)와 동시 통과.
                    Epic 5 Story 5-2 (inventory ledger) — V4 4요소 분해 ④재고조정 = KRW(0) 영구 (5-1/5-2 fold-in 전). V8 골든도 동일하게 inventory_adjustment = KRW(0).
                    0.5 plumbing — backend-only, frontend 영향 없음. V8 fixture는 backend JSON. -->

## Story

As a **사장님 (small/medium business owner)**,
I want **`POST /api/v1/calc` 호출 때마다 V8 (1원 단위 회귀) 가 12 시나리오 골든 파일과 byte-identical match를 자동 검증하여, 엔진 계산이 한 사람 합의된 회계사 Excel 결과와 1원 단위로 일치한다는 것을 매 마감마다 즉시 확인**,
so that **"원가 계산이 한참 뒤에 틀어졌다" 같은 부검 노이즈가 차단되고, 회계사가 "이 숫자 Excel이랑 같은가?" 물으면 V8 verdict envelope + 골든 fixture 매트릭스 (4 industries × 3 baseline shapes = 12) + 일자별 회귀 트래킹이 한 화면에 보임 — 버그/오탈자/패키지 업그레이드로 인한 1원 단위 회귀가 CI에서 즉시 차단됨** — AD-8 (monetary integer) · AD-12 (verification 8번째) · AD-16 (determinism) · NFR16 (V8 1원 단위 회귀) · F3.2 (V1·V4·V7·V8 자동 발동) · F6.1 (마감·계산 시점 두 곳).

## Acceptance Criteria

1. **Given** Story 4.3의 `apps/api/modules/m3_calculate/services/rules/v8_regression.py::check` `STORY_4_4_FILL_POINT` docstring marker + `packages/cost_engine/tests/regression_v8/__init__.py::V8_FIXTURE_COUNT = 0`
   **When** 본 스토리 dev-story 진행 시
   **Then** 다음 책임 분리가 유지된다:
     - **Fixture publisher** (NEW `packages/cost_engine/tests/regression_v8/fixture_loader.py`) — JSON 파싱 + V8_INPUT_SCHEMA 검증 + tenant_id + period_key collision 회피 + V8_BANKER_ROUNDING 적용 (publisher가 fixture를 만들 때 쓰는 정책). pure helper (no DB).
     - **Engine producer** (`packages/cost_engine/core/period_cost.py::compute_period_cost`) — Story 4.1 그대로. V8 verification 모름.
     - **Service integration** (`apps/api/modules/m3_calculate/services/rules/v8_regression.py::check`) — STORY_4_4_FILL_POINT 자리에 `fixture_loader.load_golden(input)` + `compute_period_cost(...)` 결과와 byte-identical 비교 + status='passed'|'failed' 반환 + details.golden_diff(`{'left': {...}, 'right': {...}, 'fields_diff': [...]}`) 추가. placeholder=True 분기는 Epic 11 회귀 시 fallback으로 보존.
     - **CI gate** (`tests/regression_v8/test_regression_v8_fixtures.py`) — 12+ cases (12 fixture × ≥1 = 12 base + 4 industry skip matrix parametrize). 마커 `pytest.mark.v8_regression` + `@pytest.mark.engine` 동시 적용. `pytest` 기본 호출에 자동 포함 (no skip 옵션).

2. **Given** 12 fixture matrix (3 baseline shapes × 4 industry × 1 = 12) + Industry enum SSOT
   **When** `packages/cost_engine/tests/regression_v8/fixtures/*.json` 12 파일 발행
   **Then** 다음 매트릭스 커버리지 (AC #2):
     - **Baseline shapes (3)**:
       - **B-Small**: 직영 소규모 — `direct_material=1,000,000 / direct_labor=500,000 / indirect=300,000 / fte=5.0 / standard_monthly_hours=209`
       - **B-Standard**: 표준 제조업 — `direct_material=4_900_000 / direct_labor=2_100_000 / indirect=1_500_000 / fte=12.5 / standard_monthly_hours=209`
       - **B-Complex**: 복합(FTE 정밀·다단계) — `direct_material=12_345_678 / direct_labor=8_765_432 / indirect=4_321_098 / fte=42.0 / standard_monthly_hours=228` (PRD §6.1 730h 시나리오)
     - **Industry values (4)** — Industry enum exact 매핑 (`manufacturing`, `manufacturing_service`, `service`, `manufacturing_service_other`):
       - fixture[0..2] = manufacturing × {B-Small, B-Standard, B-Complex} (3)
       - fixture[3..5] = manufacturing_service × {B-Small, B-Standard, B-Complex} (3)
       - fixture[6..8] = service × {B-Small, B-Standard, B-Complex} (3)
       - fixture[9..11] = manufacturing_service_other × {B-Small, B-Standard, B-Complex} (3)
     - **Total** = 3 × 4 = **12 fixtures**. file naming: `{industry}__{baseline_shape}.json` 예: `manufacturing__b-small.json`, `service__b-complex.json`.

3. **Given** AC #2 fixture 발행 + AC #1 service integration
   **When** `apps/api/modules/m3_calculate/services/rules/v8_regression.py::check(input)` 호출
   **Then** 다음 byte-identical 비교 (AC #3 = strict 0 KRW tolerance):
     - `golden = fixture_loader.load_golden(industry=input.industry, baseline_shape=...)` — fixture 선택은 `input.monthly_input` + `input.baseline` 으로 자동 match (canonical key = sha256(stable_json(input.monthly_input))[:8] 등 deterministic). Epic 11 회귀 시 fallback = placeholder=True.
     - `actual = input.calc_result` (engine-produced)
     - `comparison = {}`
     - **5 KRW 필드** (`material_cost`, `labor_cost`, `overhead_cost`, `manufacturing_cost`, `inventory_adjustment`): `actual[FIELD] == golden[FIELD]` (정수 byte-identical, `banker_round_krw` 적용 후 비교 — engine이 이미 은행원 반올림을 했으므로 동일 결과). mismatch 시 `comparison[FIELD] = {'golden': int, 'actual': int}`.
     - **`result_hash`**: `actual.result_hash == golden.result_hash` (64-char hex SHA-256 byte-identical).
     - **`state`**: 둘 다 `"draft"` (AD-22 invariant — 어느 한쪽이라도 다른 값이면 fail).
     - 모든 필드 pass → `status='passed'`, `details={'fixture_id': '...', 'fields_compared': ['material_cost', ..., 'state']}`.
     - 1개 이상 fail → `status='failed'`, `details.golden_diff = {'left': actual_dict, 'right': golden_dict, 'fields_diff': [list]}`. `message_ko = f"V8 1원 단위 회귀 위반: {[f'{k}={d['golden']}≠{d['actual']}' for k,d in comparison.items()]}"`.

4. **Given** AC #3 byte-identical 비교 + NFR16 determinism
   **When** 같은 fixture + 같은 input으로 100회 반복 호출
   **Then** 다음 determinism invariant (AC #4):
     - 모든 호출에서 `status` / `message_ko` / `details` byte-identical (determinism — 100× 호출 시 100× 같은 결과)
     - `result_hash` byte-identical (engine 단계에서 이미 보장; V8 비교는 그 hash를 비교만 함 — 추가 hashing 없음)
     - `golden_diff` (failed path) deterministic JSON dump 순서 (sort_keys=True)
   **And** `tests/regression_v8/test_regression_v8_fixtures.py::test_v8_golden_byte_identical_for_each_fixture` 12 case (per fixture, 1 initial + 99 re-run with same input → 모두 동일).

5. **Given** AC #1~4 골든 비교 wire + AC #5 industry × baseline 매트릭스
   **When** `VerificationRunner.run_all(...)` Step 6.5 발동
   **Then** 다음 integration (AC #5 — Story 4.3 AC #2 wire 재사용):
     - V8 rule fires for **all industries** (universal — `INDUSTRY_VALUES` 4개 모두). V1·V4·V8 모두 발동, V7 service-only 추가 발동.
     - 각 industry의 첫 번째 fixture (industry × B-Small) 가 manufacturing production tenant_id에 매핑 (UUID v4 unique — 각 fixture 별 다른 tenant_id).
     - Idempotent re-call: 같은 snapshot → 같은 V8 verdict envelope (deterministic 100× — AC #4).
     - `tests/integration/test_verification_order.py::test_step_6_5_v8_golden_match_path` 1 case 추가 (V1·V4 pass + V8 fixture match → verification_status='passed').

6. **Given** CI gate (mandatory `pytest -m v8_regression` 블록 없음 — 본 스토리는 모든 pytest 실행이 V8 fixture gate 자동 포함)
   **When** `uv run pytest` (full, no skip) 실행
   **Then** 다음 3중 게이트 clean (AC #6):
     - `uv run ruff check packages/cost_engine/tests/regression_v8/ tests/regression_v8/ apps/api/modules/m3_calculate/services/rules/ apps/api/core/audit_action.py 0 errors`
     - `uv run import-linter lint` 2 contracts KEPT (V8 fixture loader = pure helper in `packages/cost_engine/tests/regression_v8/`, m3_calculate service layer 그대로)
     - `uv run pytest -m v8_regression` 12 fixture cases + determinism 12 cases + 4 industry skip parametrize = 28+ cases pass
     - `uv run pytest` (full) — V8 regression marker tests 자동 포함 (skip 없음). Story 4-1/4-2/4-3 누적 회귀 0건.

7. **Given** 골든 fixture는 외부 운영 환경에서 변동 불가 (정합성) + 4 industries는 변동 불가
   **When** 본 스토리 commit 안
   **Then** 다음 hash lock + 매트릭스 lock (AC #7 — fixture 무결성):
     - 각 fixture 파일 상단에 `_fixture_lock_sha256 = '<64-hex>'` 주석 라인 (Story 4.1 `banker_round_krw` 패턴과 동일). fixture 내용이 바뀌면 이 lock도 갱신 — 결정적.
     - `packages/cost_engine/tests/regression_v8/__init__.py::V8_FIXTURE_COUNT = 12` (Story 4.1 baseline 0 → 12).
     - 4-industry matrix 검증 테스트: `tests/regression_v8/test_regression_v8_fixtures.py::test_v8_fixture_matrix_covers_all_4_industries` 1 case (Industry enum 4 values × ≥1 fixture each).
     - `tests/regression_v8/test_regression_v8_fixtures.py::test_v8_fixture_matrix_covers_all_3_baseline_shapes` 1 case.

8. **Given** 골든 fixture 발행 + V8 wire + CI gate + 정합성 lock
   **When** `docs/cost-engine.md` §V8 + `docs/conventions.md` §0.4 + `docs/capability-matrix.md` v1.4 갱신
   **Then** 다음 docs wire (AC #8):
     - `docs/cost-engine.md` §V8 골든 추가: 12 fixture 매트릭스 표 (4 industries × 3 baseline shapes) + fixture 추가 절차 (새 baseline shape → 4 JSON file copy 후 fixture_id 변형 + lock sha256 갱신) + byte-identical 비교 의사 코드
     - `docs/conventions.md` §0.4 cross-language parity: "V8 1원 단위 회귀" + "12 fixture matrix = mandatory CI gate (no skip)" 명시
     - `docs/capability-matrix.md` v1.4 (2026-08-03): V8 verification status wire contract row 추가 (Story 4.3 v1.3 + V8 골든 fill wire)
     - `apps/api/core/audit_action.py::ActionClass` (A5 SSOT): `VERIFY_V8_GOLDEN_MATCH = "verify_v8_golden_match"` enum value 추가 + Calc_log fallback 시 audit log insertion 경유 (CR 1.1 forward-lock) — 본 스토리는 enum value + 1 call site stub (Epic 11 reversal close 시 본격 사용).

9. **Given** V8 wire + V8 verification 신규 emit 시
   **When** `verify_v8_golden_match` 가 verification failed 시 audit log emission
   **Then** 다음 audit log semantics (AC #9 — CR 1.1 audit-first):
     - V8 pass → `calc_log(action='compute', result_hash=...)` (Story 4.2 그대로)
     - V8 fail → `calc_log(action='verification_failed', result_hash=None)` + `verification_log(action='verification_failed', top_failure_code='V8', top_failure_message_ko=...)` (Story 4.3 확장 + `apps/api/core/audit_action.py` enum value 추가)
     - `tests/api/test_verdict_envelope.py::test_audit_log_verification_failed_v8_path` 1 case — V8 fail 시 audit log INSERT 시뮬레이션 (CR 1.1 forward-lock 검증)
     - `tests/services/test_audit_action_centralization.py` KEPT — `VERIFY_V8_GOLDEN_MATCH` enum value 추가 후 drift count = 0 유지.

10. **Given** 본 스토리 완료 시점 + A1 (4d088f5) pre-existing failures clean + Story 4-1/4-2/4-3 cumul 회귀 0건
    **When** `uv run pytest` (full) 실행 (AC #10)
    **Then** 다음 3중 게이트 clean + Epic 4 complete 가시화:
      - `uv run ruff check packages/cost_engine/tests/regression_v8/ tests/regression_v8/ apps/api/modules/m3_calculate/services/rules/ packages/services/m0_onboarding/ packages/cost_engine/ tests/cost_engine/ tests/integration/ tests/api/` 0 errors
      - `uv run import-linter lint` 2 contracts KEPT
      - `uv run pytest` (full) — V8 12 fixture gate + Story 4.3 48 + Story 4-2 회귀 + Story 4.1 회귀 모두 green (New V8 cases + 0 pre-existing failures)
      - `git log --grep "^[Ss]tory 4\.4"` commit 1개 = 본 스토리 1 commit (CR 0.3 lesson — 1 commit 1 story)

## Tasks / Subtasks

- [ ] **Task 1 — 골든 fixture 발행 (12 files)** (AC: #2, #7)
  - [ ] 1.1 — 디렉토리 확인 + 생성: `packages/cost_engine/tests/regression_v8/fixtures/` (mkdir -p)
  - [ ] 1.2 — `fixture_publisher.py` (NEW 일회성 도구): `python -m packages.cost_engine.tests.regression_v8.fixture_publisher --industry manufacturing --baseline-shape b-small --output fixtures/manufacturing__b-small.json` → 1 file. **3 baseline × 4 industry = 12 calls. git commit 후 도구는 `--check-only` 모드로 전환** (재발행 시에만 사용, default = check-only).
  - [ ] 1.3 — 12 fixture 발행: `manufacturing__b-small.json` … `manufacturing_service_other__b-complex.json`. 각 파일 content = V8Input (TypedDict structural shape) + V8GoldenOutput (5 KRW + result_hash + state) + `_fixture_lock_sha256 = '<golden hash>'` 헤더 주석.
  - [ ] 1.4 — 골든 발행 정책: story 4.1 `compute_period_cost` 실행 → 결과 그대로 저장 (의도: Excel 회계사 결과와 engine 결과가 동일하다는 가정 하에 engine 자체를 골든으로 잠금; 분리 발행 = Epic 11 reversal decision). lock sha256 = sha256(stable_json(golden_output))[:8] + 56-char random (collision 회피).
  - [ ] 1.5 — `packages/cost_engine/tests/regression_v8/__init__.py::V8_FIXTURE_COUNT` = 0 → 12.

- [ ] **Task 2 — Fixture loader (pure helper)** (AC: #1, #7)
  - [ ] 2.1 — `packages/cost_engine/tests/regression_v8/fixture_loader.py`:
    - `def load_golden_for_industry(industry: str, *, fixtures_root: Path | None = None) -> list[V8Input]`: 1 industry fixture 다건 로드 (skip = 0건이면 error)
    - `def load_golden_by_id(fixture_id: str, *, fixtures_root: Path | None = None) -> tuple[V8Input, V8GoldenOutput]`: 1 fixture 로드 + lock sha256 검증
    - `def select_golden_for_input(monthly_input: MonthlyInput, *, industry: str) -> V8Input`: 입력 → 가장 match하는 fixture (deterministic key = sha256(stable_json((industry, monthly_input)))[:8] 같은 canonical match). MVP = industry + baseline_shape 자동 추론 + 첫 매칭.
  - [ ] 2.2 — `compute_golden_lock_sha256(golden: V8GoldenOutput) -> str`: fixture publisher + loader가 같은 함수 사용.
  - [ ] 2.3 — `validate_v8_input_schema(input_dict: dict) -> None`: V8_INPUT_SCHEMA 검증 (jsonschema 또는 manual; AD-5 purity 보존 위해 manual 권장).
  - [ ] 2.4 — pure helper (no DB, no clock, no random — sha256 deterministic). import-linter boundary test (`packages.cost_engine.tests.regression_v8` 는 pure tests layer, cost_engine core만 import).

- [ ] **Task 3 — V8 rule kernel wire (STORY_4_4_FILL_POINT)** (AC: #1, #3, #4, #5, #9)
  - [ ] 3.1 — `apps/api/modules/m3_calculate/services/rules/v8_regression.py::check` 수정:
    - STORED_4_4_FILL_POINT marker 찾기
    - `golden = fixture_loader.select_golden_for_input(input.monthly_input, industry=input.industry)`
    - `_golden_output = load_golden_by_id(golden["fixture_id"])` → V8GoldenOutput dict
    - `comparison = {}`
    - 5 KRW 필드 byte-identical 비교 (banker_round_krw 적용 — engine 이미 처리, 동일 결과)
    - result_hash byte-identical
    - state byte-identical (모두 "draft")
    - pass → VerificationItem status='passed', details={'fixture_id': ..., 'fields_compared': [5 KRW + state + hash]}
    - fail → status='failed', details.golden_diff (CR 2.3 extra='forbid' consistent)
  - [ ] 3.2 — Epic 11 reversal 시 fallback 보존: `if not golden: return VerificationItem(status='passed', details={'placeholder': True, 'reversal_path': True})` (Epic 11 회귀 시 `golden` = empty list일 때 placeholder 분기).
  - [ ] 3.3 — `apps/api/core/audit_action.py::ActionClass` + `AuditAction` registry 확장: `VERIFY_V8_GOLDEN_MATCH = 'verify_v8_golden_match'` enum value + 1 call site stub (calc_orchestrator.py의 verification_failed emit 시 `top_failure.code == 'V8'` 분기).
  - [ ] 3.4 — `_emit_verification_log` (Story 4.3)가 `top_failure_code` 채울 때 V8 분기 추가: 기존 V1/V4/V7 분기에 `elif code == 'V8': emit verify_v8_golden_match` (CR 1.1 audit-first forward-lock).

- [ ] **Task 4 — CI gate tests (12+ cases)** (AC: #1, #4, #5, #6, #7)
  - [ ] 4.1 — `tests/regression_v8/__init__.py`: tests dir package marker
  - [ ] 4.2 — `tests/regression_v8/test_regression_v8_fixtures.py`:
    - `@pytest.mark.engine` + `@pytest.mark.v8_regression` (CI gate marker). 둘 다 적용.
    - `test_v8_fixture_count_is_12`: 12 fixture files present + count == 12 (V8_FIXTURE_COUNT invariant)
    - `test_v8_fixture_matrix_covers_all_4_industries`: 4 industries × ≥1 fixture (Industry enum SSOT)
    - `test_v8_fixture_matrix_covers_all_3_baseline_shapes`: 3 baseline shapes × ≥1 fixture each
    - `test_v8_fixture_lock_sha256_validates`: 12 fixture 모두 lock sha256 정확
    - `test_v8_golden_byte_identical_for_each_fixture[fixture_path]`: 12 cases (parametrize over 12 fixture paths)
    - `test_v8_golden_100x_determinism[fixture_path]`: 12 cases (determinism invariant)
    - `test_v8_golden_failed_path_format`: 1 fixture mutation → status='failed' + golden_diff shape 확인
    - `test_v8_golden_industry_skip_matrix[industry]`: 4 industries 모두 V8 발동 (universal)
    - `test_v8_golden_idempotent_re_call[fixture_path]`: 12 cases (같은 input → 같은 envelope 100×)
    - total: ~28+ cases
  - [ ] 4.3 — 기존 `tests/cost_engine/test_regression_v8_placeholder.py` (10 cases) KEPT + 1 case 추가: `test_v8_FIXTURE_COUNT_now_12` (Story 4.1 placeholder contract 보존).
  - [ ] 4.4 — `tests/integration/test_verification_order.py` (Story 4.3) 업데이트: `test_step_6_5_v8_golden_match_path` 1 case 추가 (V1·V4 pass + V8 fixture match → verification_status='passed').
  - [ ] 4.5 — `tests/api/test_verdict_envelope.py` 업데이트: `test_audit_log_verification_failed_v8_path` 1 case (V8 fail 시 audit log semantics 검증).

- [ ] **Task 5 — A5 audit_action.py forward-lock (CR 1.1)** (AC: #9)
  - [ ] 5.1 — `apps/api/core/audit_action.py::ActionClass` enum 확장 (F-6 review lock):
    - `VERIFY_V8_GOLDEN_MATCH = "verify_v8_golden_match"` 멤버 추가 (Epic 11 reversal 시 본격 사용)
  - [ ] 5.2 — `AuditAction` Literal union에 문자열 추가: `"action_verify_v8_golden_match"`
  - [ ] 5.3 — `tests/services/test_audit_action_centralization.py` KEPT — drift count = 0 유지 (no legacy `emit_audit(` introduced)
  - [ ] 5.4 — `tests/api/test_verdict_envelope.py::test_audit_log_verification_failed_v8_path` 1 case — V8 fail audit emission path coverage
  - [ ] 5.5 — CR 1.1 forward-lock docs: `docs/conventions.md §10 (audit_action)` 1-line 추가 — V8 path도 registry 거치도록.

- [ ] **Task 6 — Lint + import-linter gate (AC: #6)**
  - [ ] 6.1 — `uv run ruff check packages/cost_engine/tests/regression_v8/ tests/regression_v8/ apps/api/modules/m3_calculate/services/rules/ apps/api/core/audit_action.py tests/cost_engine/ tests/integration/` 0 errors
  - [ ] 6.2 — `uv run ruff format` clean
  - [ ] 6.3 — `uv run import-linter lint` 2 contracts KEPT (V8 fixtures = pure tests layer; cost_engine core과 service layer 모두 그대로)
  - [ ] 6.4 — `tests/cost_engine/test_no_io_imports.py::forbidden` list 확장: V8 wire 경로 포함 = fixture_loader.py, v8_regression.py (이미 v8_regression은 pure 였음; fixture_loader는 cost_engine tests layer라 별도 처리)

- [ ] **Task 7 — Docs (AC: #8)**
  - [ ] 7.1 — `docs/cost-engine.md` §V8 추가 (Story 4.1 §V1·V4·V7·V8 옆):
    - 12 fixture 매트릭스 표 (4 industries × 3 baseline shapes)
    - fixture 추가 절차 (새 baseline shape → 4 JSON file copy + fixture_id + lock sha256 갱신)
    - byte-identical 비교 의사 코드
    - Epic 11 reversal fallback 명시
  - [ ] 7.2 — `docs/conventions.md` §0.4 cross-language parity:
    - "V8 1원 단위 회귀" 추가
    - "12 fixture matrix = mandatory CI gate (no skip)" 명시
    - "V8 골든 fill 변경 시 STORY_4_4_FILL_POINT marker docstring update 필수" — cr-4-3-lessons F-4 패턴
  - [ ] 7.3 — `docs/capability-matrix.md` v1.4 (2026-08-03):
    - V8 verification status wire contract row 추가 (Story 4.3 v1.3에 이어서)
    - COST_CALCULATION unchanged (no new capability row) — V8 wiring은 internal verification layer
  - [ ] 7.4 — `packages/cost_engine/tests/regression_v8/README.md` 업데이트:
    - 12 fixture 매트릭스 표 (4 industries × 3 baseline shapes)
    - "fixture 추가/변경 시 `fixture_publisher.py --check-only` 실행 → lock sha256 mismatch 시 fix"
    - "CI gate = mandatory (no skip marker)"

## Dev Notes

### Architecture binds

- **AD-1 (헥사고날 코어)** — V8 fixtures = `packages/cost_engine/tests/regression_v8/` layer (engine 옆 테스트 인프라). m3_calculate service layer가 fixture_loader를 import하나 pure helper라 AD-5 purity 유지.
- **AD-5 (엔진 순수성)** — fixture_loader + V8 rule 모두 pure. 골든 publish 도구 (fixture_publisher.py)는 일회성 도구 (git commit 후 `--check-only`로 전환); CI에서도 `fixture_publisher.py` 실행 안 함.
- **AD-8 (monetary)** — KRW 정수 정밀, 1원 단위 회귀. V8 byte-identical `banker_round_krw` 적용 후 비교.
- **AD-11 (의존 방향)** — `apps/api/modules/m3_calculate/services/rules/v8_regression.py` → `packages/cost_engine/tests/regression_v8/fixture_loader.py` (cross-layer — engine infrastructure). Story 4.2 AST allowlist가 `m3_calculate/services/` 만 등록했으므로 추가 allowlist entry 필요 (`tests/regression_v8/fixture_loader.py`) — `tests/architecture/test_api_calls_only_ports.py::CORE_IMPORT_ALLOWLIST` 확장.
- **AD-12 (verification 8번째)** — V8 발동 condition = 모든 industries universal (V1·V4·V8 모두 universal).
- **AD-15 (cross-language)** — V8 fixture content는 backend JSON. TS mirror는 옵션 (`apps/web/lib/v8-regression-fixtures.ts`는 4-4.1 — 본 스토지 범위 외).
- **AD-16 (determinism)** — result_hash sha256 stable JSON invariant. V8 wire는 hash를 비교만 함 (재계산 안 함).
- **AD-22 (append-only-leaning)** — engine returns state='draft' ONLY. 골든 fixture state='draft' 고정.
- **CR 0.2 (RLS)** — 골든 fixture은 tenant_id UUID unique, 다른 tenant와 collide 안 함 (sha256 + lock collision 회피). 골든은 test layer라 RLS 미적용.
- **CR 1.1 (audit-first)** — verify_v8_golden_match 신규 emit은 `audit_action.py` enum value + 1 call site stub (CR 1.1 forward-lock).
- **CR 2.3 (extra='forbid')** — V8 golden_diff dict shape (Pydantic dict[str, Any] — VerificationItem.details에 들어감; envelope은 extra='forbid' invariant).
- **cr-4-3-lessons (F-4 STORY_4_4_FILL_POINT)** — marker 위치 보존. V8 rule 변경 시 marker docstring update 필수 (conventions §0.4).
- **cr-4-3-lessons (F-5 Industry SSOT)** — V8 fixture industry 값은 Industry enum exactly 매핑 (cr-4-3-lessons protocol.py INDUSTRY_VALUES와 동일 set).
- **cr-4-3-lessons (F-6 A5 forward-lock)** — verify_v8_golden_match 추가 시 drift detector 통과 (emit_audit_typed 경유).

### Story 0.1 → 4.1 → 4.2 → 4.3 → 4.4 의존성

| Story 산출물 | Story 4.4 사용처 |
|---|---|
| `packages.cost_engine.core.money.KRW` (Story 0.1) | V8 fixture 5 KRW int fields + banker_round_krw (Story 4.1) |
| `packages.cost_engine.core.period_cost.compute_period_cost` (Story 4.1) | 골든 발행 시 producer + V8 wire 시 byte-identical 비교 대상 |
| `packages.cost_engine.tests.regression_v8.__init__` (Story 4.1 T5) | V8_INPUT_SCHEMA + V8_GOLDEN_OUTPUT_STRUCTURE + banker_round_krw() placeholder contract 보존. fixture count 0 → 12 |
| `apps.api.modules.m3_calculate.services.rules.v8_regression` (Story 4.3) | STORY_4_4_FILL_POINT marker 위치 보존 + actual fill |
| `apps.api.modules.m3_calculate.services.rules.protocol` (Story 4.3) | INDUSTRY_VALUES (= Industry enum) — V8 fixture industry 값 매핑 SSOT |
| `apps.api.modules.m3_calculate.services.verification_runner` (Story 4.3) | Step 6.5 V8 발동 — 변경 없음 (V8 rule kernel 자체가 wire 변경) |
| `apps.api.modules.m3_calculate.services.calc_orchestrator` (Story 4.2 + 4.3) | verification_failed emit 시 V8 분기 추가 (top_failure.code == 'V8' → action='verify_v8_golden_match') |
| `apps.api.core.audit_action` (Story 4.3 A5) | ActionClass enum + AuditAction Literal — verify_v8_golden_match 추가 |
| `apps.api.alembic.versions.0013_verification_log` (Story 4.3) | verification_log table — V8 fail audit log emission target |
| `fiscal_period_snapshots` (Story 4.2) | V8 pass → snapshot INSERT (Story 4.2 그대로) |
| `tests/services/test_audit_action_centralization` (Story 4.3 F-6) | KEPT — drift detector forward lock |

### Epic 의존성 (Epic 0+1+2+3+4 자산)

| 자산 | 출처 | 본 스토리 사용처 |
|---|---|---|
| `Industry` enum (Story 1.1) | Epic 1 | V8 fixture industry 값 매핑 (F-5 SSOT) |
| `tenant_settings.baseline` JSONB (Story 1.2) | Epic 1 | 골든 fixture baseline structural shape |
| `monthly_input_periods` rows + warnings (Story 3.3) | Epic 3 | 골든 fixture monthly_input shape (FTE, 6 stream aggregate) |
| `capability_matrix.md` (Epic 1-4 cumul) | Epic 1-4 | v1.4 update — V8 wire contract row + industry × V* firing matrix extension |
| `ActionClass` enum + emit_audit_typed (Story 4.3 A5) | Epic 4 | verify_v8_golden_match 신규 추가 (forward-lock) |
| `V8_INPUT_SCHEMA` + `V8_GOLDEN_OUTPUT_STRUCTURE` + `banker_round_krw` (Story 4.1 T5) | Epic 4 | fixture schema / output structure / rounding policy SSOT |

### 데이터 흐름 (Story 4.4 — V8 골든 fill + wire)

```
[Dev (Story 4.4 execution)]
   ↓ one-shot: `python -m packages.cost_engine.tests.regression_v8.fixture_publisher --all`
   ↓   - For each (industry, baseline_shape) in matrix: 1 file
   ↓   - Engine called with monthly_input + baseline → CalcResult → 5 KRW + result_hash + state
   ↓   - JSON written to fixtures/{industry}__{shape}.json with _fixture_lock_sha256 header comment
   ↓ git commit 12 JSON files + fixture_loader + V8 wire + tests
[CI / pytest]
   ↓ uv run pytest (full, no skip)
   ↓   - tests/regression_v8/test_regression_v8_fixtures.py::test_v8_golden_byte_identical_for_each_fixture[*]
   ↓     - 12 fixture × 1 cases = 12 fixture 골든 load + 5 KRW + result_hash + state byte-identical compare
   ↓   - tests/cost_engine/test_regression_v8_placeholder.py (Story 4.1) KEPT — V8_FIXTURE_COUNT == 12 invariant
[Live / POST /api/v1/calc]
   ↓ apps/api/modules/m3_calculate/services/calc_orchestrator.py::run_calculation
   ↓ Step 6.5: VerificationRunner.run_all(...)
   ↓   for rule in _VERIFICATION_RULES:
   ↓     if industry != Service: skip V7 (silent)
   ↓     item = rule.check(RuleInput(...))
   ↓     if V8 fixture mismatch → status='failed', top_failure={'code': 'V8', ...}
   ↓   verdict = Verdict(verification_status, verifications, top_failure, trace_id)
   ↓   if verdict.verification_status == 'failed':
   ↓     calc_log(action='verification_failed', result_hash=None) [CR 1.1]
   ↓     verification_log(action='verification_failed', top_failure_code='V8', ...) [V8 분기]
   ↓     ROLLBACK
   ↓     return CalcResponse(verdict=verdict) [200 OK + envelope, NOT 4xx]
```

### 골든 발행 도구 (`fixture_publisher.py`) 의사 코드

```python
# packages/cost_engine/tests/regression_v8/fixture_publisher.py
# One-shot 도구 — git commit 후 --check-only 모드로 전환.

import argparse
import hashlib
import json
import sys
from pathlib import Path
from uuid import UUID, uuid4

from packages.cost_engine.core.money import KRW
from packages.cost_engine.core.period_cost import Baseline, compute_period_cost
from packages.cost_engine.ports.calc_port import MonthlyInput
from packages.cost_engine.tests.regression_v8 import (
    V8Input, V8GoldenOutput, compute_golden_lock_sha256
)


# 3 baseline shapes (PRD §6.1 fixtures)
BASELINE_SHAPES = {
    "b-small":    {"material": 1_000_000,   "labor": 500_000,     "indirect": 300_000,   "fte": 5.0,  "hours": 209},
    "b-standard": {"material": 4_900_000,   "labor": 2_100_000,   "indirect": 1_500_000, "fte": 12.5, "hours": 209},
    "b-complex":  {"material": 12_345_678,  "labor": 8_765_432,   "indirect": 4_321_098, "fte": 42.0, "hours": 228},  # 730h 시나리오
}


def publish_one(industry: str, baseline_shape: str, fixtures_root: Path) -> None:
    """1 industry × 1 baseline shape = 1 JSON file 발행."""
    s = BASELINE_SHAPES[baseline_shape]
    mi = MonthlyInput(
        tenant_id=uuid4(),
        period_key="2026-07",
        direct_material_krw=KRW(s["material"]),
        direct_labor_krw=KRW(s["labor"]),
        indirect_krw=KRW(s["indirect"]),
        fte_headcount=Decimal(str(s["fte"])),
    )
    baseline = Baseline(
        fiscal_period="2026-07",
        standard_monthly_hours=s["hours"],
        bom_ratio_validated=True,
        allocation_basis_set=True,
    )
    calc = compute_period_cost(monthly_input=mi, baseline=baseline)

    golden = V8GoldenOutput(
        material_cost=int(calc.material_cost),
        labor_cost=int(calc.labor_cost),
        overhead_cost=int(calc.overhead_cost),
        manufacturing_cost=int(calc.manufacturing_cost),
        inventory_adjustment=int(calc.inventory_adjustment),
        result_hash=calc.result_hash,
        state="draft",
    )
    lock_sha = compute_golden_lock_sha256(golden)
    fixture_id = f"{industry}__{baseline_shape}"

    fixture_obj = {
        "fixture_id": fixture_id,
        "fixture_version": "1.0.0",
        "tenant_id": str(mi.tenant_id),
        "period_key": "2026-07",
        "monthly_input": {  # structural shape (not class instance)
            "direct_material_krw": int(mi.direct_material_krw),
            "direct_labor_krw": int(mi.direct_labor_krw),
            "indirect_krw": int(mi.indirect_krw),
            "fte_headcount": str(mi.fte_headcount),
        },
        "baseline": {
            "fiscal_period": baseline.fiscal_period,
            "standard_monthly_hours": baseline.standard_monthly_hours,
            "bom_ratio_validated": baseline.bom_ratio_validated,
            "allocation_basis_set": baseline.allocation_basis_set,
        },
        "_fixture_lock_sha256": lock_sha,
        "golden": golden,
    }
    out_path = fixtures_root / f"{industry}__{baseline_shape}.json"
    out_path.write_text(json.dumps(fixture_obj, indent=2, ensure_ascii=False, sort_keys=True))


INDUSTRY_VALUES = ["manufacturing", "manufacturing_service", "service", "manufacturing_service_other"]
ALL_BASELINE_SHAPES = list(BASELINE_SHAPES.keys())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Publish all 12 fixtures")
    parser.add_argument("--check-only", action="store_true", help="Validate lock sha256 (no publish)")
    parser.add_argument("--industry", choices=INDUSTRY_VALUES)
    parser.add_argument("--baseline-shape", choices=ALL_BASELINE_SHAPES)
    parser.add_argument("--fixtures-root", default=Path(__file__).parent / "fixtures")
    args = parser.parse_args()

    if args.check_only:
        # Validate mode — CI/dev both use this. No filesystem writes.
        from packages.cost_engine.tests.regression_v8.fixture_loader import load_golden_by_id
        for industry in INDUSTRY_VALUES:
            for shape in ALL_BASELINE_SHAPES:
                fixture_id = f"{industry}__{shape}"
                _input, golden = load_golden_by_id(fixture_id, fixtures_root=args.fixtures_root)
                expected = compute_golden_lock_sha256(golden)
                assert _input["_fixture_lock_sha256"] == expected, f"Lock mismatch: {fixture_id}"
        return 0

    if args.all:
        for industry in INDUSTRY_VALUES:
            for shape in ALL_BASELINE_SHAPES:
                publish_one(industry, shape, args.fixtures_root)
        return 0

    if args.industry and args.baseline_shape:
        publish_one(args.industry, args.baseline_shape, args.fixtures_root)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
```

### Fixture loader (pure helper)

```python
# packages/cost_engine/tests/regression_v8/fixture_loader.py

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import UUID

from packages.cost_engine.core.period_cost import Baseline, MonthlyInput
from packages.cost_engine.tests.regression_v8 import (
    V8_GOLDEN_OUTPUT_STRUCTURE, V8_INPUT_SCHEMA, V8GoldenOutput, V8Input,
)


# fix V8Input TypedDict → plain dict at runtime (TypedDict is just a typing aid)
def _validate_v8_input(input_dict: dict[str, Any]) -> None:
    """Manual V8_INPUT_SCHEMA validation (AD-5 purity: no jsonschema)."""
    assert set(input_dict.keys()) >= set(V8_INPUT_SCHEMA["required"]), (
        f"V8Input missing required keys: {set(V8_INPUT_SCHEMA['required']) - set(input_dict.keys())}"
    )
    for k, v in input_dict["monthly_input"].items():
        if k in ("direct_material_krw", "direct_labor_krw", "indirect_krw"):
            assert isinstance(v, int), f"monthly_input.{k} must be int"
        elif k == "fte_headcount":
            assert isinstance(v, str), f"monthly_input.fte_headcount must be str (Decimal)"


def compute_golden_lock_sha256(golden: V8GoldenOutput) -> str:
    """Deterministic lock sha256 — golden 변경 감지."""
    blob = json.dumps(golden, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def load_golden_by_id(fixture_id: str, *, fixtures_root: Path | None = None) -> tuple[V8Input, V8GoldenOutput]:
    """1 fixture load + lock sha256 검증.

    Returns: (input_dict, golden_output)
    Raises: FileNotFoundError, ValueError (lock mismatch)
    """
    if fixtures_root is None:
        fixtures_root = Path(__file__).parent / "fixtures"
    path = fixtures_root / f"{fixture_id}.json"
    obj = json.loads(path.read_text(encoding="utf-8"))
    _validate_v8_input(obj)
    expected = compute_golden_lock_sha256(obj["golden"])
    assert obj["_fixture_lock_sha256"] == expected, (
        f"Lock mismatch for {fixture_id}: expected={expected}, actual={obj['_fixture_lock_sha256']}"
    )
    return obj, obj["golden"]


def load_golden_for_industry(industry: str, *, fixtures_root: Path | None = None) -> list[V8Input]:
    """1 industry의 모든 fixture 반환 (fallback path / matrix cover 검증)."""
    if fixtures_root is None:
        fixtures_root = Path(__file__).parent / "fixtures"
    paths = sorted(fixtures_root.glob(f"{industry}__*.json"))
    return [json.loads(p.read_text(encoding="utf-8")) for p in paths]


def select_golden_for_input(*, industry: str, monthly_input: MonthlyInput, fixtures_root: Path | None = None) -> V8Input | None:
    """산업 입력에 가장 적합한 fixture select.

    Strategy: monthly_input KRW 합계 + fte_headcount → baseline shape 추론
              (PRD §6.1의 3 baseline shape 분포와 match).
    MVP: 단순 canonical match — fte ≤ 5 = b-small, 5 < fte ≤ 20 = b-standard, fte > 20 = b-complex.
    Returns None if no fixture found (Epic 11 reversal fallback trigger).
    """
    if fixtures_root is None:
        fixtures_root = Path(__file__).parent / "fixtures"
    monthly_total = int(monthly_input.direct_material_krw) + int(monthly_input.direct_labor_krw) + int(monthly_input.indirect_krw)
    fte = float(monthly_input.fte_headcount)
    if monthly_total <= 2_000_000 and fte <= 5:
        shape = "b-small"
    elif monthly_total <= 10_000_000 and fte <= 20:
        shape = "b-standard"
    else:
        shape = "b-complex"
    path = fixtures_root / f"{industry}__{shape}.json"
    if not path.exists():
        return None
    obj = json.loads(path.read_text(encoding="utf-8"))
    _validate_v8_input(obj)
    return obj
```

### V8 rule wire (STORY_4_4_FILL_POINT fill)

```python
# apps/api/modules/m3_calculate/services/rules/v8_regression.py
# (Story 4.3 baseline + Story 4.4 fill)

from packages.cost_engine.tests.regression_v8.fixture_loader import (
    select_golden_for_input, load_golden_by_id, compute_golden_lock_sha256,
)


class V8RegressionRule:
    @property
    def name(self) -> Literal["V8"]:
        return "V8"

    def applies_to(self, *, industry: str) -> bool:
        return True  # universal

    def check(self, input: RuleInput) -> VerificationItem:
        """Pure 1원 단위 회귀 (AC #3) — fixture 골든 vs engine result."""
        # 1. fixture select (industry + baseline shape 추론)
        golden_input = select_golden_for_input(industry=input.industry, monthly_input=input.monthly_input)
        if golden_input is None:
            # Epic 11 reversal fallback — placeholder True 분기 보존
            return VerificationItem(
                code="V8", status="passed",
                message_ko="V8 엔진 대조 placeholder (Epic 11 fallback)",
                details={"placeholder": True, "story_4_4_no_fixture_for_industry": input.industry},
            )

        # 2. load golden output + lock 검증
        _, golden_output = load_golden_by_id(golden_input["fixture_id"])

        # 3. byte-identical comparison (5 KRW + result_hash + state)
        actual = input.calc_result
        fields_compared = []
        comparison = {}
        for field, golden_val in golden_output.items():
            actual_val = getattr(actual, field)
            if int(actual_val) != int(golden_val):
                comparison[field] = {"golden": int(golden_val), "actual": int(actual_val)}
            else:
                fields_compared.append(field)

        # 4. deterministic verdict
        if not comparison:
            return VerificationItem(
                code="V8", status="passed",
                message_ko=f"V8 1원 단위 회귀 정상 (fixture_id={golden_input['fixture_id']})",
                details={"fixture_id": golden_input["fixture_id"], "fields_compared": fields_compared},
            )

        fields_diff = sorted(comparison.keys())
        diff_summary = ", ".join(
            f"{f}={comparison[f]['golden']}≠{comparison[f]['actual']}" for f in fields_diff
        )
        return VerificationItem(
            code="V8", status="failed",
            message_ko=f"V8 1원 단위 회귀 위반: {diff_summary}",
            details={
                "fixture_id": golden_input["fixture_id"],
                "golden_diff": {"left": dict(actual), "right": dict(golden_output), "fields_diff": fields_diff},
            },
        )
```

### A5 audit_action.py forward-lock (V8 분기 추가)

```python
# apps/api/core/audit_action.py — Story 4.4 forward-lock
class ActionClass(str, __import__("enum").Enum):
    # ... existing members (TENANT_SETTINGS, SERVICE_ROLE, UPLOADED_DOCUMENT, INPUT_DRAFT, PRODUCT, BOM, MONTHLY_INPUT, BOM_MATRIX, AI_DOCUMENT)
    VERIFY_V8_GOLDEN_MATCH = "verify_v8_golden_match"  # NEW — Story 4.4 forward-lock

AuditAction = Literal[
    # ... existing literals
    "action_verify_v8_golden_match",  # NEW
]
```

```python
# apps/api/modules/m3_calculate/services/calc_orchestrator.py — V8 분기
async def _write_verification_log(top_failure: VerificationItem | None) -> None:
    if top_failure is None:
        return
    if top_failure.code == "V8":
        action = AuditAction.action_verify_v8_golden_match  # forward-lock
    else:
        action = AuditAction.action_verification_failed  # V1·V4·V7
    await emit_audit_typed(
        session=self.session,  # type: ignore[arg-type]
        action_class=ActionClass.VERIFY_V8_GOLDEN_MATCH,
        action=action,
        # ... standard fields
    )
```

### Determinism + idempotent re-call (AC #4 + #5)

```python
# tests/regression_v8/test_regression_v8_fixtures.py

import pytest

from apps.api.modules.m3_calculate.services.rules import _VERIFICATION_RULES
from apps.api.modules.m3_calculate.services.rules.protocol import (
    RuleInput, INDUSTRY_VALUES,
)
from apps.api.modules.m3_calculate.services.verification_runner import VerificationRunner
# (... other imports)

ALL_INDUSTRIES = INDUSTRY_VALUES  # ['manufacturing', 'manufacturing_service', 'service', 'manufacturing_service_other']


@pytest.mark.engine
@pytest.mark.v8_regression
@pytest.mark.parametrize("industry", ALL_INDUSTRIES)
def test_v8_golden_byte_identical_for_each_fixture(industry: str) -> None:
    """12 fixture per industry × 3 baseline shape → 골든 vs engine byte-identical."""
    # 3 baseline shapes per industry — 12 cases
    ...


@pytest.mark.engine
@pytest.mark.v8_regression
def test_v8_fixture_count_is_12() -> None:
    """V8_FIXTURE_COUNT invariant — Story 4.1 baseline 0 → Story 4.4 = 12."""
    from packages.cost_engine.tests.regression_v8 import V8_FIXTURE_COUNT
    assert V8_FIXTURE_COUNT == 12

    from pathlib import Path
    fixtures_dir = Path(__file__).parents[2] / "packages/cost_engine/tests/regression_v8/fixtures"
    assert len(list(fixtures_dir.glob("*.json"))) == 12


@pytest.mark.engine
@pytest.mark.v8_regression
def test_v8_fixture_matrix_covers_all_4_industries() -> None:
    """4 industries × ≥1 fixture (F-5 SSOT)."""
    from pathlib import Path
    fixtures_dir = Path(__file__).parents[2] / "packages/cost_engine/tests/regression_v8/fixtures"
    industries = {p.stem.split("__")[0] for p in fixtures_dir.glob("*.json")}
    assert industries == set(ALL_INDUSTRIES), f"industries={industries}"


@pytest.mark.engine
@pytest.mark.v8_regression
def test_v8_fixture_matrix_covers_all_3_baseline_shapes() -> None:
    """3 baseline shapes × ≥1 fixture."""
    from pathlib import Path
    fixtures_dir = Path(__file__).parents[2] / "packages/cost_engine/tests/regression_v8/fixtures"
    shapes = {p.stem.split("__")[1] for p in fixtures_dir.glob("*.json")}
    assert shapes == {"b-small", "b-standard", "b-complex"}, f"shapes={shapes}"
```

### PIPA / PII / Logging

- 본 스토리는 PIPA gate **불필요** — V8 verification은 local engine + JSON fixture (no AI/cross-border). Story 4.3 동일.
- V8 fixture content는 KRW 정수만 포함; PII 없음. tenant_id UUID는 test layer라 dummy (uuid4()).
- 골든 발행 시 `print()` OK (CI/dev 1회성 도구). fixture_loader 런타임 call site에서는 structlog 금지 (AD-5).

### Anti-patterns to avoid (CR lessons)

- **골든 fixture을 영구 변경 (lock sha256 갱신 없이)** — AC #7 정합성 위반. `fixture_publisher.py --check-only` 가 lock mismatch fail.
- **V8 wire in 4xx response** — Story 4.3 AC #4 학습. verification failed → 200 OK + envelope (NOT 4xx).
- **Float for V8 fixture 5 KRW** — AD-8 위반. `int` only. KRW 정수 정밀 1원 단위 회귀.
- **골든 발행 도구를 CI에 등록** — Story 4.4 의도 위반. `fixture_publisher.py` 는 dev 1회성 + `--check-only` 모드만 CI에 노출 (lock 검증). 발행 자체는 git-commit-only.
- **`compute_golden_lock_sha256` 의 randomness** — AD-16 determinism 위반. sha256 stable JSON (sort_keys=True) 정책.
- **`verify_v8_golden_match` 신규 시 A5 미반영** — CR 1.1 5번째 epic drift. ActionClass enum value + drift detector 통과 필수.
- **V8 fixture = 0 (placeholder만)** — AC #6/#7 위반. V8_FIXTURE_COUNT = 12.
- **`select_golden_for_input` 가 random 선택** — determinism 위반. canonical key = industry + canonical shape 추론 (PRD §6.1 fte/material bins).
- **골든 fixture에 `_fixture_lock_sha256` 누락** — AC #7 정합성. 모든 12 fixture에 header comment + lock field 필수.
- **PowerShell Out-File for 한글 doc** — CR 0.4 lesson. `Write` 도구만 사용.
- **V8 mismatch → e.stop() 또는 raise** — Story 4.3 AC #4 학습. envelope return (NOT raise). AD-12 ordering: V1 fail 후 V8 abort — V8 만 fail 시 envelope return + ROLLBACK 후 audit log emission.

## Open Questions (cj-style defaults)

| # | 질문 | 디폴트 | 변경 시 영향 |
|---|---|---|---|
| OQ1 | 12 fixture matrix dimensions — 3 baseline × 4 industry vs 4 industry × 3 baseline vs 4 industry × 3 baseline? | **3 baseline × 4 industry = 12** (PRD §6.1 baseline shapes × industry enum). cj-style: industry entropy를 행축으로 baseline shape을 열축 (matrix 가독성). | matrix 가독성 차이만. engine 로직 동일. |
| OQ2 | 골든 발행 source — engine 자체 (Story 4.1 compute_period_cost) vs 외부 Excel 회계사 결과? | **engine 자체** (Story 4.1 baseline — 분리 발행은 Epic 11 reversal decision) | Epic 11 reversal 시 행·열 swap으로 회계 Excel 발행 가능. CR 1.1 forward-lock — 골든 변경 시 audit log emission (V8 fail 분기에 흡수). |
| OQ3 | 골든 발행 시기 — Story 4.4 commit vs 별도 commit? | **Story 4.4 commit 안에 12 JSON + fixture_loader + V8 wire 포함** — 1 commit 1 story (CR 0.3 lesson) | 별도 commit 시 partial wire + Epic 5 carry 위험. |
| OQ4 | CR 1.1 forward-lock — `verify_v8_golden_match` action 추가 vs placeholder? | **ActionClass enum value + 1 call site stub 추가** (Story 4.4 forward-lock — Epic 11 reversal 시 본격 사용) | placeholder 유지 시 A5 drift detector가 호출 site 누락 감지 못함. 5번째 epic drift 리스크. |
| OQ5 | V8 골든 비교 시작 시점 — V8 VerificationItem.status='failed' 후 calc_log action='verification_failed' 그대로 vs 신규 action='verify_v8_golden_match'? | **status='failed' envelope + calc_log action='verify_v8_golden_match' (top_failure.code == 'V8')** — V1·V4·V7 분기와 분리 | 신규 action 사용 시 audit_action.py forward-lock 완성. |
| OQ6 | 골든 lock sha256 collision 회피 — sha256 truncated vs sha256 + random? | **sha256(stable_json(golden)) (64-char hex, no truncate)** — deterministic, no collision risk | truncated 시 collision 위험 (현실적으로 낮지만). |

## Definition of Done

- [ ] AC #1~#10 모두 pass (pytest + ruff + import-linter 3중 게이트)
- [ ] Task 1~7 모든 subtask check
- [ ] `tests/regression_v8/test_regression_v8_fixtures.py` 28+ cases green (12 fixture byte-identical + 12 determinism + 4 industry matrix + 3 baseline shape matrix + lock + count + idempotent)
- [ ] `tests/cost_engine/test_regression_v8_placeholder.py` (Story 4.1 10 cases) KEPT + `test_v8_FIXTURE_COUNT_now_12` 1 case 추가
- [ ] `tests/integration/test_verification_order.py` V8 wire case 추가 (Step 6.5 V8 골든 match path)
- [ ] `tests/api/test_verdict_envelope.py` V8 audit log case 추가 (`test_audit_log_verification_failed_v8_path`)
- [ ] `tests/services/test_audit_action_centralization.py` (Story 4.3 F-6) KEPT + drift count = 0 유지
- [ ] `packages/cost_engine/tests/regression_v8/fixtures/*.json` 12 files committed + `_fixture_lock_sha256` header
- [ ] `packages/cost_engine/tests/regression_v8/__init__.py::V8_FIXTURE_COUNT` = 12
- [ ] `apps/api/core/audit_action.py` `ActionClass.VERIFY_V8_GOLDEN_MATCH` 추가 + `AuditAction.action_verify_v8_golden_match`
- [ ] `apps/api/modules/m3_calculate/services/rules/v8_regression.py` STORY_4_4_FILL_POINT fill
- [ ] `uv run ruff check` 0 errors on 4-4 scope
- [ ] `uv run import-linter lint` 2 contracts KEPT
- [ ] `uv run pytest` (full) — 12 + Story 4-3 48 + Story 4-2 회귀 + Story 4-1 회귀 = 100+ cases 0회귀
- [ ] Story 4-1 (Story 4.1 77 cases) 0건 회귀
- [ ] Story 4-2 (Story 4.2 30+ cases) 0건 회귀
- [ ] Story 4-3 (48 + 1 skip) 0건 회귀
- [ ] **A1 (4d088f5) — 0 pre-existing failures**
- [ ] `docs/cost-engine.md` §V8 12 fixture matrix + byte-identical pseudocode
- [ ] `docs/conventions.md` §0.4 cross-language parity (V8 mandatory CI gate + STORY_4_4_FILL_POINT)
- [ ] `docs/capability-matrix.md` v1.4 (V8 wire + industry × V* firing matrix extension)
- [ ] `packages/cost_engine/tests/regression_v8/README.md` 12 fixture matrix + check-only 가이드
- [ ] 5 deferral 명시: (a) TS mirror `apps/web/lib/v8-regression-fixtures.ts` = 4-4.1 옵션, (b) state='committed' 전이 = Epic 11 M11, (c) state='reversed' 전이 = Epic 11 Story 11-3, (d) Epic 9 ABC 풀·활동·동인 100% 검증 = Story 9-1, (e) Epic 5 5-1/5-2 inventory_adjustment fold-in = Epic 5 (V4 placeholder 영구) — V8 골든은 inventory_adjustment = KRW(0) 발행을 Epic 5 fold-in 후 재발행 결정 = Epic 5 회고 시 reopen Story 4-4
- [ ] sprint-status.yaml: `4-4-v8-regression-ci-gate` → backlog → ready-for-dev (current change)
- [ ] epic-4: in-progress 유지

## References

- Epic 4: Cost Calculation & Verification — `_bmad-output/planning-artifacts/epics.md` lines 758-816
- Story 4.4 PRD requirement — epics.md "V8 1원 단위 회귀 골든 파일 fill + CI gate"
- Story 4.4 PRD F6.1 — `prd.md` lines 458-459: "시스템은 §11 V1~V8을 마감 진입 시점과 계산 시점 두 곳에서 자동 발동한다"
- AD-8 monetary integer — `ARCHITECTURE-SPINE.md` KRW integer 1원 단위
- AD-12 verification-first — `ARCHITECTURE-SPINE.md` lines 112-116
- AD-16 determinism — `ARCHITECTURE-SPINE.md` result_hash sha256 stable JSON
- AD-22 append-only-leaning — `ARCHITECTURE-SPINE.md` engine always state="draft"
- Story 4.1 spec — `_bmad-output/implementation-artifacts/4-1-pure-cost-engine-no-i-o-no-clock.md` (engine pure + V8 placeholder contract 보존)
- Story 4.3 spec — `_bmad-output/implementation-artifacts/4-3-verification-v1-v4-v7-v8-order.md` (V8VerificationRule + STORY_4_4_FILL_POINT marker)
- Story 4.3 review — `_bmad-output/implementation-artifacts/.review/story-4-3-review.md` (F-4 marker + F-5 Industry SSOT + F-6 A5 forward-lock)
- cr-4-3-lessons — `memory/cr-4-3-lessons.md` (5 epic lessons)
- A5 spike — `_bmad-output/implementation-artifacts/a5-audit-action-inversion-spike-2026-08-03.md`
- Epic 4 partial retro — `_bmad-output/implementation-artifacts/epic-4-retro-2026-08-03.md` (A2 4-3·4-4 spec 진입)
- CR 1.1 lesson — `memory/cr-1-1-lessons.md`
- CR 0.2 lesson — `memory/cr-0-2-lessons.md`
- CR 2.3 lesson — `memory/cr-2-1-lessons.md`
- `packages/cost_engine/tests/regression_v8/__init__.py` (Story 4.1 T5 contract)
- `docs/conventions.md` §0.4 cross-language parity (Story 4.3 added)
- `docs/cost-engine.md` (Story 4.1 §V1·V4·V7·V8 + Story 4.3 §verification envelope)
- `docs/capability-matrix.md` v1.3 (Story 4.3 wire contract row — v1.4 본 스토리에서 update)
