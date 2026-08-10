# V8 Regression Suite

> **Status (2026-08-09, Story 11.4)** — V8 18→22 골든 fixture matrix extension
> (Epic 11 carry-over A13 sprint-up 결정). 4 NEW 골든 fixtures shipped for
> AD-20 state machine + AD-22 reversal 영구화 + W2 reopen flow:
> `snapshot_committed.json` (verified→committed) +
> `reversal_negating_snapshot.json` (AD-22 sign-negating) +
> `reversal_corrected_snapshot.json` (AD-22 corrected row + corrected_period_key) +
> `reopen_committed.json` (W2 owner-only reopen with operator_action 4-value enum).
> `V8_FIXTURE_COUNT = 22` (`packages/cost_engine/tests/regression_v8/__init__.py`).
> AD-25 4-channel publisher wire (`ai_cache` + `cost_engine_cache` +
> `fiscal_period_cache` + `closing_snapshot_cache`) + banker's rounding parity
> (CR 0-4) 모두 pinned. CR 4-4 lesson 정합 (V8 byte-identical CI gate).
>
> **Status (2026-08-02, Story 4.4)** — 12 골든 fixture 매트릭스 (4 industries
> × 3 baseline shapes) ship 완료. `tests/regression_v8/test_regression_v8_fixtures.py`
> 가 CI mandatory gate 로 wire 됨 (`@pytest.mark.engine` + `@pytest.mark.v8_regression`).
> `verify_v8_golden_match` audit action (Story 4.4 forward-lock) 가
> `verification_log.action` literal 에 추가됨.
>
> **Status (Story 4.1)**: placeholder contract placed.
> **Status (Story 0.3)**: directory + README created.

---

## What is V8?

V8 is the **8th verification layer** in the costmgr verification chain
(see `docs/cost-engine.md` §Verification Envelope). It captures the
**byte-identical 결정론 contract** — for any input that has a published
expected output, the cost engine must produce that output exactly, in KRW
integer units, and `result_hash` (sha256 stable_json) must match the 골든.

V8 fixtures are **golden output snapshots** that encode:

- Input: a normalized monthly state (M1 baseline + M2 input streams) +
  `tenant_id` (random uuid4 — engine `result_hash` is tenant-scoped)
- Expected: the computed cost breakdown + `result_hash` + `state="draft"`
- Tolerance: 0 KRW (byte-identical — no rounding tolerance)
- Lock: `_fixture_lock_sha256` = sha256(stable_json(golden)) 64-char hex

---

## Fixture 매트릭스 (Story 4.4 — 12 fixtures)

`packages/cost_engine/tests/regression_v8/fixtures/` 에 발행되는 **12 JSON** 파일:

| Industry \ Shape | b-small | b-standard | b-complex |
|---|---|---|---|
| `manufacturing` | `manufacturing__b-small.json` | `manufacturing__b-standard.json` | `manufacturing__b-complex.json` |
| `manufacturing_service` | `manufacturing_service__b-small.json` | `manufacturing_service__b-standard.json` | `manufacturing_service__b-complex.json` |
| `service` | `service__b-small.json` | `service__b-standard.json` | `service__b-complex.json` |
| `manufacturing_service_other` | `manufacturing_service_other__b-small.json` | `manufacturing_service_other__b-standard.json` | `manufacturing_service_other__b-complex.json` |

### baseline shape 분포 (canonical 매칭)

`fixture_loader.select_golden_for_input()` 가 `monthly_input.monthly_total + fte` 로 shape 추론:

| Shape | material + labor + indirect 한도 | fte 한도 |
|---|---|---|
| `b-small`    | ≤ 2,000,000 KRW | ≤ 5  |
| `b-standard` | ≤ 10,000,000 KRW | ≤ 20 |
| `b-complex`  | (else) | (else) |

선택된 fixture 가 없으면 (Epic 11 reversal fallback 시) `placeholder=True`
분기로 통과 — 실제 비교는 매트릭스 내 fixture 가 있을 때만 발동.

### Lock invariants (per-fixture)

각 fixture 가 가지는 3가지 lock:

1. **`_fixture_lock_sha256`** — `sha256(stable_json(golden))` 64자 hex.
   골든 변경 후 publisher 미실행 시 `test_v8_fixture_lock_sha256_validates`
   가 fail.
2. **`tenant_id`** — random `uuid4()`. Engine `result_hash` 가 tenant-scoped
   (AD-16 stable_json) 이므로, V8 byte-identical 비교는 fixture 입력의
   `tenant_id` 그대로 사용해야 한다.
3. **`golden.state = "draft"`** — AD-22 invariant (engine always draft).

---

## When V8 must run

V8 골든 매트릭스는 **모든 PR** 에서 mandatory CI gate 이다
(`@pytest.mark.engine` + `@pytest.mark.v8_regression` — pytest 기본 호출
자동 포함, `--ignore` / `--deselect` 금지). STACK_PIN bump 시 추가 강제:

| Trigger | V8 required? |
|---|---|
| Patch update of unpinned transitive | No |
| Bump pinned package (`[STACK BUMP]`) | **Yes** |
| Change to cost_engine core/ | **Yes** (lock sha256 회귀) |
| Change to cost_engine adapters/ | **Yes** |
| Change to V8 fixture itself | **Yes** (lock sha256 재계산) |
| Refactor only (no version change) | Recommended |

---

## How to run

### CI / dev — 검증 (no fixture regeneration)

```bash
# Full V8 매트릭스
uv run pytest tests/regression_v8/ -v

# Story 4.4 fixture 매트릭스만
uv run pytest tests/regression_v8/test_regression_v8_fixtures.py -v

# 12 fixture 중 1개만 (parametrize fixture_id)
uv run pytest "tests/regression_v8/test_regression_v8_fixtures.py::test_v8_golden_byte_identical_for_each_fixture[manufacturing__b-small]" -v
```

### Local — 골든 fixture 추가 / 변경

```bash
# 신규 fixture 생성 (1 industry × 3 shapes)
python -m packages.cost_engine.tests.regression_v8.fixture_publisher \
    --industry manufacturing

# 전체 12 fixture 재생성 (주의: golden 변경 후에만)
python -m packages.cost_engine.tests.regression_v8.fixture_publisher --all

# Check-only 모드 (CI default; lock sha256 일치 검증만)
python -m packages.cost_engine.tests.regression_v8.fixture_publisher --check-only
```

**주의**: `--all` 은 골든 변경 후 1회 실행 후 lock sha256 재계산. 매 PR
에서 실행 금지. 정상 운영은 `--check-only`.

---

## Test inventory (28+ cases, mandatory)

`tests/regression_v8/test_regression_v8_fixtures.py` 의 case 분류:

| Category | Cases | 비고 |
|---|---|---|
| Fixture count + matrix | 3 | `test_v8_fixture_count_is_12`, `test_v8_fixture_matrix_covers_all_4_industries`, `test_v8_fixture_matrix_covers_all_3_baseline_shapes` |
| Lock sha256 | 12 (parametrize) | `test_v8_fixture_lock_sha256_validates[fixture_id]` |
| Byte-identical | 12 (parametrize) | `test_v8_golden_byte_identical_for_each_fixture[fixture_id]` |
| 100x determinism | 12 (parametrize) | `test_v8_golden_100x_determinism[fixture_id]` (AD-16) |
| Failed-path shape | 1 | `test_v8_golden_failed_path_format` (CR 2.3 extra='forbid') |
| Industry × V* firing | 4 (parametrize) | `test_v8_golden_industry_skip_matrix[industry]` |
| Idempotent re-call | 12 (parametrize) | `test_v8_golden_idempotent_re_call[fixture_id]` (20 iterations each) |
| Registry | 2 | `test_v8_rule_registry_uniqueness`, `test_v8_rule_is_in_registry` |
| Loader API smoke | 3 | `test_load_golden_for_industry_*`, `test_select_golden_for_input_*` |
| **Total** | **61+** | |

모든 case 가 `@pytest.mark.engine` + `@pytest.mark.v8_regression` 둘 다
marking. `pytest` 기본 호출이 자동 포함.

---

## Adding a new baseline shape

새 shape (예: `b-enterprise`) 도입 절차:

1. `fixture_publisher.py::BASELINE_SHAPES` dict 에 새 shape tuple 등록:
   `(max_total_krw, max_fte, "b-enterprise")` 등.
2. `python -m packages.cost_engine.tests.regression_v8.fixture_publisher --all`
   로 1 industry × 4 industries = 4 JSON 파일 생성.
3. 각 fixture 의 `_fixture_lock_sha256` 자동 재계산 (publisher 가 dictionary
   순서대로 갱신).
4. `tests/regression_v8/test_regression_v8_fixtures.py::test_v8_fixture_matrix_covers_all_3_baseline_shapes`
   의 `ALL_SHAPES` tuple 에 새 shape 추가 — parametrize set 자동 확장.
5. CI 게이트가 자동으로 새 shape 의 12 case parametrize 추가.

---

## Status / Changelog

- **Story 0.3** — directory + README 생성 (placeholder).
- **Story 4.1 (2026-08-02)** — T5 placeholders:
  `__init__.py` 에 `V8Input` / `V8GoldenOutput` / `V8_INPUT_SCHEMA` /
  `V8_GOLDEN_OUTPUT_STRUCTURE` / `V8_BANKER_ROUNDING` / `V8_FIXTURE_COUNT = 0` /
  `banker_round_krw()` 정의. `tests/cost_engine/test_regression_v8_placeholder.py`
  가 contract shape 강제.
- **Story 4.4 (2026-08-02)** — 12 fixture 매트릭스 ship:
  - `V8_FIXTURE_COUNT = 12`
  - 12 JSON 골든 발행 (4 industries × 3 baseline shapes)
  - `tests/regression_v8/test_regression_v8_fixtures.py` 28+ cases (61+ with parametrize)
  - `verify_v8_golden_match` audit action forward-lock
  - Industry enum canonical names parity (`manufacturing_service`,
    `manufacturing_service_other`)
  - `fixture_loader.py` (lock sha256 + select_golden_for_input + load_golden_*)
  - CR 2.3 extra='forbid' invariant 골든 diff shape
- **Story 11.4 (2026-08-09, Epic 11 carry-over A13 sprint-up)** — V8 18→22 matrix extension:
  - `V8_FIXTURE_COUNT = 18 → 22`
  - 4 NEW JSON 골든 발행 (AD-20 + AD-22 + W2):
    - `snapshot_committed.json` — AD-20 state machine transition (verified→committed)
      + 4-channel cache invalidation publisher wire (AD-25).
    - `reversal_negating_snapshot.json` — AD-22 reversal 영구화 sign-negating row
      with correction_group_id link + 4-channel cache invalidation.
    - `reversal_corrected_snapshot.json` — AD-22 corrected row with
      corrected_period_key (AD-24 typed 'YYYY-MM') + banker's rounding parity (CR 0-4).
    - `reopen_committed.json` — W2 reopen flow with operator_action 4-value enum
      + reason length 20-500 audit-justification (AD-15) + 2-channel cache
      invalidation (fiscal_period_cache + closing_snapshot_cache).
  - 4 NEW test cases (snapshot_committed fixture shape + reversal_negating fixture
    shape + reversal_corrected fixture shape + reopen_committed fixture shape)
  - `SNAPSHOT_REVERSAL_FIXTURE_IDS` tuple export (`__init__.py`)
  - `SNAPSHOT_REVERSAL_FIXTURE_COUNT = 4` constant
  - CR 4-4 lesson 정합 (V8 byte-identical CI gate + tenant-scoped result_hash)

---

## Cross-references

- `docs/cost-engine.md` §V8 1원 단위 결정론 — 12 fixture 매트릭스 + byte-identical 비교 의사 코드
- `docs/conventions.md` §0.5 — Verification rule purity gate + Story 4.4 V8 CI gate
- `docs/capability-matrix.md` v1.4 — V8 wire + Industry canonical names parity
- `apps/api/core/audit_action.py` — `verify_v8_golden_match` audit action
- `apps/api/modules/m3_calculate/services/calc_orchestrator.py` — V8 audit log wire-up
- `tests/web/test_m3_verdict_parity.py` — TS mirror Industry enum parity