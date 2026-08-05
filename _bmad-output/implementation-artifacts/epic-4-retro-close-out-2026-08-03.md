---
epic: 4
epic_title: Cost Calculation & Verification
date: 2026-08-03
status: completed
facilitator: Amelia (Developer)
participants:
  - Alice (Product Owner)
  - Charlie (Senior Dev)
  - Dana (QA Engineer)
  - Elena (Junior Dev)
  - kjw (Project Lead)
duration: ~30 minutes (lightweight + close-out 결정 — Epic 1·2·3 retro 패턴 + A2/A3/A4 cj-style defaults)
scope_note: Epic 4 회고 범위 = 4-1·4-2·4-3·4-4 (4/4 done, full close-out). partial retro (4-1·4-2 only, 2026-08-03) supersede.
---

# Epic 4 회고 — Cost Calculation & Verification (Close-out)

## 1. Epic 요약

| 지표 | 값 |
|---|---|
| 완료 스토리 | 4 / 4 (100%) — 4-1 done · 4-2 done · 4-3 done · 4-4 done |
| 누적 신규 테스트 | 280+ (4-1: 67 in-scope / 4-2: 30 / 4-3: 25+ / 4-4: 61+ with parametrize) |
| Alembic 마이그레이션 | 0012 (fiscal_period_snapshots + calc_log) · 0013 (verification_log) |
| Capability 추가 | 0 (`COST_CALCULATION` 4-1 T3 introduced, no new row) |
| 신규 typed exception | 12 (4-1: 1 / 4-2: 4 / 4-3: 5 / 4-4: 2) |
| Pre-existing failures | 8건 + 27 lint → 2026-08-03 commit 4d088f5 (Epic 4 회고 A1 즉시 처리) |
| CR 1.1 drift | 4번째 epic 연속 재발 → A5 spike 2026-08-03 design proposal, partial impl in 4-3 + 4-4 |
| SDR verdict | 4-1 APPROVE (F-1 spec patch) · 4-2 APPROVE (1 HIGH + 5 LOW) · 4-3 REQUEST CHANGES → patches F-1~F-10 → done · 4-4 dev-story execute clean (3중 게이트 green) |

**Epic 4 스토리 구성 (전체)**

- **Story 4.1 — Pure Cost Engine (No I/O, No Clock)** (status: done, 2026-08-02)
  - `compute_period_cost(monthly_input, baseline) -> CalcResult` 순수 함수 커널 (Story 0.1 헥사고날 코어 스캐폴드 위 첫 concrete function)
  - 8-stage 산식 체인 (PRD §6.1) + banker's rounding (AD-15) + `result_hash = sha256(stable JSON)`
  - AD-22 boundary strengthening: engine은 `state='draft'`만 반환 (regex guard + `_DRAFT_STATE` constant + module docstring)
  - 3중 purity gate (ruff + import-linter + AST) — 67 in-scope tests green
  - `docs/capability-matrix.md` v1.1 (Epic 3 회고 A5 동반): `COST_CALCULATION` 행 추가 (service-only ❌ 명시)
  - V8 placeholder contract shipped (Story 4-4 fill 진입점 보존)

- **Story 4.2 — Single Calculation Endpoint (REPEATABLE READ)** (status: done, 2026-08-03)
  - `POST /api/v1/calc` 1개 진입점 (AD-19)
  - REPEATABLE READ + `SELECT ... FOR UPDATE` on monthly_input_periods (AD-4)
  - Epic 3 A4 close-time hook wire: `is_blocked=true` → 409 `MONTHLY_INPUT_BLOCKED` typed envelope (PRD §A11 "마감 시 차단" 정책)
  - AD-22 state transition (engine returns draft → service INSERTs at `state='verified'`)
  - Idempotency: same `result_hash` → 200 OK + 기존 snapshot 응답 (no INSERT, no audit). 다른 hash → 409 `FISCAL_PERIOD_SNAPSHOT_DIVERGED`
  - 4 typed exceptions (AD-15 envelope) + Alembic 0012 + RLS + calc_log audit + 26 reference tests (5 e2e `@pytest.mark.skip` Story 0.5 plumbing)

- **Story 4.3 — Verification V1·V4·V7·V8 in Order + verdict field** (status: done, 2026-08-03)
  - `VerificationRunner.run_all(monthly_input, baseline, calc_result, *, industry: Industry) -> Verdict` — 3-layer 책임 분리 (Engine/Service/Handler)
  - 4 rule pure kernels: V1 완전배부 / V4 4요소 분해 (PRD §11) / V7 ABC 무결성 (service-only) / V8 placeholder stub
  - AD-12 ordering invariant: `if item.status == "failed": break` (이전 검증 실패 시 후속 검증 abort)
  - `Verdict` envelope + `VerificationItem` typed literal (CR 2.3 `extra='forbid'`)
  - TS mirror parity: `apps/web/lib/m3-verdict.ts` (Epic 2 W4 + Epic 3 W3 패턴)
  - CR 1.1 audit: `verification_log` table 신규 (Alembic 0013) + `verification_passed`/`verification_failed`/`verification_skipped` enum
  - SDR verdict: REQUEST CHANGES → F-1 (async tests → `asyncio.run` wrapper) + F-2 (SDR overclaim correction) + F-3~F-6 (docs/V8 marker/Industry enum/A5 drift detector) + F-7~F-10 (LOW)
  - 25+ test cases (3중 게이트 clean) + A5 forward-lock partial (F-6 drift detector test 추가)

- **Story 4.4 — V8 Regression CI Gate** (status: done, 2026-08-03, commit 80f4494)
  - 12 fixture matrix (4 industries × 3 baseline shapes) — V8_FIXTURE_COUNT 0→12
  - `fixture_loader.py` (NEW — `load_golden_by_id` / `load_golden_for_industry` / `select_golden_for_input` / `compute_golden_lock_sha256`)
  - `fixture_publisher` CLI (`--all` / `--check-only` / `--industry`) — 운영 안전
  - `tests/regression_v8/test_regression_v8_fixtures.py` 28+ cases (61+ with parametrize: 3 matrix + 12 lock_sha256 + 12 byte-identical + 12 100x determinism + 1 failed-path shape + 4 industry skip matrix + 12 idempotent re-call + 2 registry + 3 loader API smoke)
  - A5 forward-lock: `audit_action.py::ActionClass.VERIFY_V8_GOLDEN_MATCH` enum 추가 + drift detector 동시 통과
  - Industry canonical names parity 정렬 (TS m3-verdict.ts + Python protocol.py = `manufacturing_service` / `manufacturing_service_other`)
  - 3중 게이트 clean (ruff 0 / import-linter 2 KEPT / pytest 838 pass + 108 skip RLS CI-only + 0 fail)
  - V8 CI gate = mandatory (no skip option)

## 2. 잘된 점 (Wins)

### W1. "Pure kernel → service wiring" 두 스토리 분할 (4-1·4-2) = Epic 5·6·9의 표준 패턴
- 4-1의 pure kernel이 결정론적 `result_hash` 보장 → 4-2 idempotency 검증을 한 줄로 가능
- AC #4: same baseline + same result_hash → 200 OK + 기존 snapshot 응답 (no INSERT, no audit)
- AD-19 단일 진입점 + AD-4 REPEATABLE READ + AD-22 boundary strengthening 모두 wire contract level에서 정렬
- **자산**: Epic 5 (inventory_ledger pure → 5-2 service wiring) · Epic 9 (CCRPort.compute pure → 9-3 ABC routing service) 진입 시 동일 패턴

### W2. AD-22 boundary strengthening (engine returns draft → service writes verified)
- 4-1: `_DRAFT_STATE` constant + regex guard + AD-22 module docstring (engine 절대 verified/committed/reversed 모름)
- 4-2: service layer가 INSERT with `state='verified'` (AD-22 append-only-leaning)
- 4-2 T2.2 (audit-first + `flush=True` before fiscal_period_snapshots INSERT) — CR 1.1 lesson 전사 확산
- Epic 11 M11 reversal 진입점이 깨끗하게 열렸습니다 — engine은 reversal 권한 일절 없음
- **자산**: Epic 5 inventory ledger / Epic 11 reversal / Epic 6 reporting 모두 동일 패턴

### W3. Epic 3 A4 first_calc close-time hook wire contract 정렬 (Epic 3 회고 §6 A4 closed)
- 4-2 AC #3: `is_blocked=true` → 409 `MONTHLY_INPUT_BLOCKED` typed envelope
- Epic 3.3 `warnings`/`is_blocked` read-only flag → Epic 4 first_calc wire에 그대로 활용
- PRD §A11 "입력 시 경고 → 마감 시 차단" 정책이 두 layer로 정확히 분리됨 (Epic 3 W5 그대로)
- Epic 3 회고 §7 A4가 Epic 4 4-2 wire에서 정확히 closed

### W4. capability × type matrix 4 epic 연속 자산 (Epic 3 W2/L4 확장)
- 4-1 T3.1: `COST_CALCULATION` 행 추가 (제조 3종 ✅ / service-only ❌)
- 4-1 SDR F-1 spec drift 발견: spec은 service ✅, impl/doc/test 모두 service ❌ → **spec text 패치로 해결** (impl/doc/test 3중 일관성)
- 4-2 AC #5: service-only tenant → 403 `INDUSTRY_NOT_SUPPORTED` (Epic 9 ABC 라우팅 진입점)
- 4-3: COST_CALCULATION unchanged (no new capability row); service-only tenant은 service layer가 V1/V4 skip + V7/V8 run 분기 처리
- **자산**: Epic 5 (m4_inventory) + Epic 9 (m9_abc) 진입 시 동일 체크리스트

### W5. AD-15 banker's rounding parity TS/Python (Epic 3 W6 + Story 0.4 chunk-B 활용)
- 4-1 T1: 모든 KRW 산출에 `Decimal.quantize(..., ROUND_HALF_EVEN)`
- `test_round_half_even_bankers_rounding` 4 canonical half-boundary cases
- `tests/regression_v8/__init__.py::banker_round_krw()` helper — V8 골든 12 시나리오 contract 보존 (Story 4-4 fill)
- 4-3 V1 1원 단위 tolerance: `|V1_delta| <= KRW(1)` (banker's rounding 후 비교)
- 4-4 V8 byte-identical: 골든 5 KRW 필드 + result_hash + state 모두 정수 일치
- **자산**: Epic 4 4 stories 모든 비율/단가 계산에 동일 패턴

### W6. Audit-first + idempotent no-op (CR 1.1) Epic 4 정착 + 4-3 audit_action.py forward-lock
- 4-2 T2.2: `flush=True` after calc_log INSERT, before fiscal_period_snapshots INSERT
- 4-2 AC #4: idempotent re-call → audit log 안 남김 (`action='idempotent_skip'`)
- 4-2 AC #8: `calc_log` audit table — append-only (no UPDATE/DELETE)
- 4-3: `verification_log` table 신규 + DB CHECK constraint (CR 1.1 future-proof) — A5 forward-lock 첫 wire 사례
- 4-4: `audit_action.py::ActionClass.VERIFY_V8_GOLDEN_MATCH` enum 추가 + drift detector (`tests/services/test_audit_action_centralization.py`) 동시 통과
- **자산**: Epic 5 inventory_ledger append-only + Epic 11 reversal_log에도 동일 pattern

### W7. AD-19 단일 진입점 + AD-4 REPEATABLE READ + AD-12 verification ordering 동시 구현
- 4-2 AC #2: 8-step ordered lock acquisition (deadlock-free by ordered access) + `SELECT ... FOR UPDATE` 직렬화
- 4-3: V1 → V4 → V7 → V8 strict ordering + abort-on-fail invariant
- 다른 public calc endpoint 0개 — Epic 9 ABC routing은 별도 endpoint (Story 9-3)
- **자산**: Epic 5 (inventory wiring) + Epic 9 (ABC routing) 진입 시 동일 단일 진입점 패턴

### W8. V8 placeholder contract → 12 시나리오 골든 fill (4-1·4-3·4-4 분할)
- 4-1 T5: `tests/regression_v8/__init__.py` TypedDict + JSON-Schema + `banker_round_krw()` helper (placeholder)
- 4-3: `V8RegressionRule` placeholder stub + `STORY_4_4_FILL_POINT` marker (CR 4-3 lesson — F-4)
- 4-4: 12 fixture 매트릭스 발행 + `fixture_loader.py` (4 API: load_golden_by_id / load_golden_for_industry / select_golden_for_input / compute_golden_lock_sha256) + CI mandatory gate (no skip)
- 4-4: 4 industries × 3 baseline shapes = 12 fixtures + lock sha256 + byte-identical + 100x determinism 검증
- **자산**: Epic 5/6 verification surface에서도 동일 pattern — placeholder 먼저 ship, fill은 다음 스토리

### W9. CR 4-3 lessons 즉시 wire (F-1~F-10 patches)
- F-1: async test → `def test_x() -> None: asyncio.run(_impl())` 패턴 일관 적용 (CR 0.2 lesson 회귀 방지)
- F-5: Industry enum canonical SSOT + `INDUSTRY_VALUES` mirror 금지 → Industry enum 직접 import
- F-6: A5 forward-lock (`emit_audit_typed` SSOT) + drift detector (AST-grep `emit_audit(` hits = 0) — Epic 5/6/7/11 audit log 일관성 자산
- F-4: `STORY_4_4_FILL_POINT` docstring marker (다음 contributor가 5분 안에 fill 진입점 식별)
- **자산**: Epic 5 inventory_ledger / Epic 11 reversal_log 진입 시 A5 forward-lock + Industry enum SSOT 패턴 즉시 적용

### W10. Epic 4 frontend zero-debt (4-1~4-4 모두 backend-only)
- 4 stories 모두 backend-only + CI. shadcn Tabs / sonner / vitest / Playwright 0.5 plumbing 모두 NOT blocking
- frontend AC scope 0건 → frontend 0.5 plumbing 부담 누적 없음 (Epic 1·2·3 누적 frontend deferral과 격리)
- **자산**: Epic 5 5-1 + 5-2도 backend-only로 진입 가능 (Epic 4 패턴 그대로)

## 3. 개선할 점 (Challenges)

### C1. 8 pre-existing failures + 27 lint (Epic 1·2·3·4 4번째 epic 연속) — A1 즉시 처리
- Story 4.1 SDR F-4~F-11 식별, Epic 4 회고 A1 권고 Option A 채택 → **2026-08-03 commit 4d088f5 batched fix (8 failures + 27 lint)**
- F-4 PT011 (1min) + F-5 alembic 0008 sync (30min) + F-6 money.py reverse-direction (1-2h architecture decision) + F-7 services leak refactor (1-2h) + F-8 cp949 encoding pin (15min) + F-9·F-10·F-11 STACK_PIN.yaml sync (15min) = 1h 즉시 + architecture 2-4h
- **A1 즉시 처리** = Epic 5 진입 clean baseline
- **개선**: Epic 5 close-out 시 동일 패턴 — pre-existing failures를 retro 시 1 action item으로 batch
- **위험**: Epic 5·6·7까지 "사실상 표준" 고착화 가속 (5번째/6번째/7번째 epic 연속 batch)

### C2. CR 1.1 audit-action inversion — 4번째 epic 연속 재발 + A5 forward-lock으로 자산화
- Story 1.1 (industry inversion) → 1.3 (f-string interpolation) → 2.1 (conditional ternary) → 4.2 (calc_log enum 진화) → 4.3 (verification_log) → 4.4 (verify_v8_golden_match) **5번째 epic 연속**
- 4-3 review F-6 patch: A5 forward-lock audit action (`emit_audit_typed` SSOT) + drift detector (`tests/services/test_audit_action_centralization.py`) — **자산화 첫 사례**
- 4-4: A5 forward-lock 검증 (VERIFY_V8_GOLDEN_MATCH enum 추가 후 drift count = 0 유지)
- **미해결**: Phase 1+2 (audit_action.py + 22 call sites migrate) NOT done — 4-3 + 4-4 commit 안에 partial impl만 (F-6 + verify_v8_golden_match enum)
- **A5 결정 (cj-style default)**: Phase 1+2를 Epic 5 5-1 spec 진입 전 별도 적용 (4-8h, A5 spike 디자인 그대로)
- **위험**: Phase 1+2 미적용 시 Epic 5/6/7/11 audit log가 "사실상 표준"으로 drift 5번째/6번째/7번째 epic 연속 가속

### C3. Epic 5 inventory ledger fold-in 진입점 미해결 — Epic 3 A3 carry-over 3번째
- 4-1/4-2에서 `inventory_adjustment = KRW(0)` placeholder + `TODO(epic-5)` marker (Epic 3.3 패턴 그대로)
- 4-2 AC #9: `inventory_adjustment BIGINT NOT NULL DEFAULT 0` 컬럼 Epic 5 5-1/5-2에서 swap
- 4-3 V4 4요소 분해 ④재고조정 = `KRW(0)` 영구 (5-1/5-2 fold-in 전 placeholder 명시)
- `LEDGER_REFERENCE_QUERY_STUB`는 Epic 2.3이 도입, Epic 3.3이 활용, Epic 4.2 + 4-3 + 4-4 그대로 — 한 줄 swap 가능
- **A3 결정 (cj-style default, 본 회고 close-out)**: 3-story 분할 유지 (5-1 → 5-2 → 5-3). inline projection deprecation timeline은 5-2 spec에서 명시

### C4. 4-3 review F-1 (async tests) 4-1/4-2 회귀 패턴 — pytest-asyncio 부재
- dev-story가 `@pytest.mark.asyncio` decorator + `async def test_*` 사용 → 12 tests failed
- project-wide 패턴은 `def test_x(): asyncio.run(_impl())` (sync wrapper + private async impl) — `tests/api/test_calc_orchestrator.py` 템플릿
- F-1 patch: 12 async tests → `asyncio.run` wrapper, `@pytest.mark.engine` marker 유지
- **위험**: 다음 dev-story에서 같은 패턴 회귀 가능 — Story 0.5 plumbing 결정 시점에 pytest-asyncio 도입 결정도 동반
- **개선**: A5 forward-lock (drift detector)와 같은 패턴으로 `tests/cost_engine/test_no_async_decorator.py` AST guard 추가 검토 (Epic 5 carry)

### C5. V8 fixture 발행 정책 (Epic 4 4-4 OQ) — engine 자체를 골든으로 잠금
- 4-4 T1.4: 골든 발행 = `compute_period_cost` 실행 → 결과 그대로 저장 (의도: Excel 회계사 결과와 engine 결과가 동일하다는 가정)
- **위험**: engine bug가 골든에 박힘 → Epic 11 reversal decision에서 "engine이 맞다 vs 회계사가 맞다" 분리 발행 결정 필요
- **개선**: Epic 11 spec 진입 시 `fixture_publisher` 외부 도구 (Excel import / 회계사 verify pipeline) 검토

### C6. 4-3 review F-2 SDR overclaim (CR 1.1 lesson variant) — agent reports match what the audit log says, not what pytest says
- dev-story가 "64 passed + 1 skipped" claim → 실제 30 sync + 12 async-failed
- F-2 patch: SDR honest test count + F-1 root cause 명시
- **위험**: dev-story agent가 future release에서 같은 overclaim 가능
- **개선**: A5 forward-lock (drift detector)와 같은 패턴으로 "SDR test count vs pytest actual count" drift detector (CR 0.4 AST file detection 패턴) — Epic 5 carry

### C7. 4-3 review F-5 Industry enum SSOT drift — protocol.py parallel literal set
- `protocol.py`가 `INDUSTRY_MANUFACTURING_RETAIL = "manufacturing_retail"` / `INDUSTRY_MIXED = "mixed"` 별도 literal (legacy 명명) → Industry enum SSOT는 `MANUFACTURING_SERVICE` / `MANUFACTURING_SERVICE_OTHER`
- F-5 patch: `INDUSTRY_VALUES` = Industry enum 직접 import + parity test (`test_industry_values_match_industry_enum`)
- **자산**: Epic 5 inventory_ledger 진입 시 동일 pattern — Industry enum SSOT 직접 import, parallel literal set 생성 금지
- **위험**: Epic 5 m4_inventory에서 다른 module이 같은 drift 가능 — A5 forward-lock (drift detector) 확장

## 4. 핵심 인사이트 (Top Lessons)

### L1. "Pure kernel → service wiring" 두 스토리 분할 = Epic 5·6·9의 표준 패턴
- 4-1: engine pure (decisions) → 4-2: service wiring (integration)
- Epic 5: inventory_ledger pure → Story 5-2 service wiring
- Epic 9: CCRPort.compute pure → Story 9-3 ABC routing service
- **자산**: Epic 5/9 spec 진입 시 "kernel vs wiring" 분리 우선 결정

### L2. capability × type matrix = 4 epic 연속 자산 (Epic 1·2·3 회고 L4 확장)
- 4-1 SDR F-1: spec text drift을 impl/doc/test 3중 일관성으로 잡아냄 (defense in depth)
- capability-matrix.md가 wire contract의 single source of truth
- **자산**: Epic 5 (m4_inventory) + Epic 9 (m9_abc) 진입 시 동일 체크리스트

### L3. AD-22 boundary strengthening (engine draft-only) = Epic 11 reversal 진입점 보존
- 4-1: `_DRAFT_STATE` constant + regex guard
- 4-2: service writes `state='verified'` via append-only events
- Epic 11 M11 reversal은 engine과 무관 (service layer만 authorize)
- **자산**: Epic 5 inventory ledger / Epic 11 reversal / Epic 6 reporting 모두 동일 패턴

### L4. Pre-existing failures batched for Epic retro = 4 epic 연속 패턴 (CR 1.1 lesson 정착)
- Epic 1·2·3·4 회고에서 pre-existing failures를 회고 action item으로 일괄 처리
- A1 즉시 처리 (commit 4d088f5) = Epic 5 진입 clean baseline
- **자산**: Epic 5 close-out 시 동일 패턴 — pre-existing failures를 retro 시 1 action item으로 batch

### L5. Idempotency by result_hash = Epic 5 ledger append-only와 같은 wire contract
- 4-2 AC #4: 같은 baseline + same result_hash → no INSERT (immutable ledger 원칙)
- Epic 5 inventory_ledger append-only events도 동일 패턴
- **자산**: Epic 5/11에서 result_hash 기반 idempotency 재사용

### L6. V8 placeholder contract → 12 시나리오 골든 fill = "ship-then-fill" 표준 패턴
- 4-1 T5 placeholder + 4-3 STORY_4_4_FILL_POINT marker + 4-4 12 fixture fill
- "Ship contract first, fill content later" = wire contract 호환 + 회귀 위험 최소화
- **자산**: Epic 5/6 verification surface에서도 동일 pattern — placeholder 먼저 ship, fill은 다음 스토리

### L7. A5 forward-lock (audit action SSOT) + drift detector = 4번째 epic 연속 drift → 자산
- 4-3 review F-6 patch: A5 forward-lock + drift detector (`emit_audit(` AST-grep hits = 0)
- 4-4: A5 forward-lock 검증 (VERIFY_V8_GOLDEN_MATCH enum 추가 후 drift count = 0)
- **자산**: Epic 5/6/7/11 audit log 일관성 — `tests/services/test_audit_action_centralization.py` 동시 통과
- **미완료**: Phase 1+2 (audit_action.py + 22 call sites migrate) — Epic 5 5-1 진입 전 별도 적용

### L8. CR 4-3 lessons 즉시 wire (F-1~F-10) = CR pattern 학습 = Epic 5 carry-over 자산
- F-1 async test pattern (no pytest-asyncio) → `asyncio.run` wrapper 일관 적용
- F-4 STORY_FILL_POINT marker → 다음 contributor 5분 안에 fill 진입점 식별
- F-5 Industry enum SSOT → parallel literal set 생성 금지
- F-6 A5 forward-lock → drift detector + SSOT + Epic 5/6/7/11 일관성 자산
- **자산**: Epic 5 진입 시 "CR lessons memory = 즉시 적용 가능한 패턴 카탈로그"로 활용

## 5. Previous Epic Follow-through (Epic 1·2·3 retrospectives)

### Epic 3 회고 A1~A5 follow-through

| ID | 액션 | 상태 | 비고 |
|---|---|---|---|
| A1 | PIPA env-flag fallback (Epic 1 A3 carry) | ✅ done | 2026-08-02 — `pipa_gate.py` 11/11 tests |
| A2 | Story 0.5 plumbing 4번째 재평가 | ✅ done | Epic 4 4 stories 모두 backend-only + CI. 0.5 NOT blocking. blocking 시점: Epic 5 toast / Epic 6 charts |
| A3 | Epic 5 ledger fold-in 진입점 | ✅ done (cj-style) | **본 회고 §6 A3 결정**: 3-story 분할 유지 (5-1 → 5-2 → 5-3), inline projection deprecation timeline은 5-2 spec에서 명시 |
| A4 | Epic 4 first_calc close-time hook 설계 | ✅ done | 4-2 AC #3 wire: `is_blocked` → 409 `MONTHLY_INPUT_BLOCKED` |
| A5 | `docs/capability-matrix.md` v1.1 | ✅ done | 4-1 T3: `COST_CALCULATION` 행 + footnote 갱신 |

### Epic 2 회고 A1~A4 follow-through

| ID | 액션 | 상태 | 비고 |
|---|---|---|---|
| A1 | Story 1-1 정식 done 마킹 | ✅ done | Epic 1 회고 §11 즉시 실행 결과 |
| A2 | Story 1-3 dev-story 실행 | ✅ done | Epic 4 close-out 시 backend 코어 + 5 deferral 명시 |
| A3 | `docs/capability-matrix.md` 작성 | ✅ done | Epic 1 A4와 통합 — Story 3.1 T3.5 |
| A4 | Story 0.5 plumbing 우선순위 재평가 | ✅ done | Epic 3 frontend 11+ deferral 결정 — **Epic 5부터 frontend 영향 시작** (Epic 3 A2에서 resolved) |

### Epic 1 회고 A1~A4 follow-through

| ID | 액션 | 상태 | 비고 |
|---|---|---|---|
| A1 | Story 1-3 close-out 결정 | ✅ done | Epic 1 회고 §11 즉시 실행 — backend 코어 done + 5 deferral 명시 |
| A2 | shadcn Tabs 설치 확인 | ✅ done | Story 3.1 frontend 5 deferral 결정 — Story 0.5 plumbing 의존 명시 |
| A3 | PIPA env-flag fallback 추가 | ✅ done | Epic 3 A1에서 3번째 carry resolved |
| A4 | `docs/capability-matrix.md` 작성 | ✅ done | Story 3.1 T3.5에서 통합 작성 (11+ capability × 4 industry) |

### Epic 4 회고 (partial, 2026-08-03) A1~A5 follow-through

| ID | 액션 | 상태 | 비고 |
|---|---|---|---|
| A1 | Pre-existing 8 failures + 27 lint 즉시 정리 | ✅ done | 2026-08-03 commit 4d088f5 (chore: A1 pre-existing failures 정리) |
| A2 | Story 4-3 + 4-4 spec 진입 (V1·V4·V7·V8 verification + V8 CI gate) | ✅ done | 4-3 (F-1~F-10 patches) + 4-4 (12 fixture matrix + V8 CI gate) → 4-3 + 4-4 모두 done |
| A3 | Epic 5 ledger fold-in 진입점 명시 (Epic 3 A3 carry 3번째) | ✅ done (cj-style, 본 회고) | 3-story 분할 유지 + 5-2 spec에서 inline projection deprecation timeline |
| A4 | Epic 5 frontend toast 0.5 plumbing 결정 (Epic 3 A2 Epic 2 A4 carry) | ✅ done (cj-style, 본 회고) | 0.5 plumbing을 Epic 5 5-3 진입 전 별도 Story. 5-1 + 5-2는 backend-only로 진행 |
| A5 | CR 1.1 전사 single source of truth fix (별도 스파이크) | ⏳ in-progress | 4-8h scope. spike done (a5-audit-action-inversion-spike-2026-08-03.md). Phase 1+2 partial done in 4-3 (F-6 drift detector) + 4-4 (VERIFY_V8_GOLDEN_MATCH enum). **Full Phase 1+2 = Epic 5 5-1 spec 진입 전 별도 적용** |

## 6. Next Epic Preview — Epic 5: Inventory & Stock Control

### Epic 5 의존성 (Epic 1·2·3·4 완료분)

| 의존 항목 | 상태 | 비고 |
|---|---|---|
| `monthly_input_periods.opening_inventory` JSONB (Story 3.3) | ✅ ready | Epic 5 5-1 auto-carry 진입점 |
| `LEDGER_REFERENCE_QUERY_STUB` (Epic 2.3) | ✅ ready | Epic 5 5-2 ledger fold-in 한 줄 swap |
| `fiscal_period_snapshots.inventory_adjustment` (4-2) | ✅ ready | Epic 5 5-2 fold-in 대상 |
| `V4.4_elements.inventory_adjustment_krw` (4-3) | ✅ ready | Epic 5 5-2 fold-in 검증 (KRW(0) 영구) |
| `monthly_input_rows` 6-stream (Story 3.1) | ✅ stable | Epic 5 5-1 inbound/outbound aggregate |
| `compute_period_cost` `inventory_adjustment` placeholder (4-1) | ✅ ready | Epic 5 5-2 fold-in swap |
| Story 3.3 warnings (V3/V5) | ✅ stable | Epic 5 5-3 negative closing inventory guard |
| A5 forward-lock (drift detector, audit_action.py) | ⏳ in-progress | Epic 5 5-1 spec 진입 전 Phase 1+2 별도 적용 (A5 결정) |
| Pre-existing 0 failures (4d088f5) | ✅ clean | Epic 5 진입 clean baseline |

### Story 구성 (PRD §F4.1·§F4.2·§V3)

- **5-1** Opening Inventory Auto-Carry Chain — `monthly_input_periods.opening_inventory` JSONB + Epic 3.3 inline projection fold-in 진입점
- **5-2** Inventory Ledger Append-Only Events — `LEDGER_REFERENCE_QUERY_STUB` swap + `fiscal_period_snapshots.inventory_adjustment` wire
- **5-3** Negative Closing Inventory Guard — Story 3.3 V3 warning + 5-2 ledger events 종합 검증 (frontend toast 필요)

### Epic 5 첫 스토리 진입 전 결정 (cj-style defaults applied, 본 회고)

**A3 — Epic 5 ledger fold-in 진입점 (cj-style default 결정)**

3-story 분할 유지 (5-1 → 5-2 → 5-3). inline projection deprecation timeline은 5-2 spec에서 명시.

| Story | 책임 | Epic 3.3 inline projection 처리 |
|---|---|---|
| 5-1 | opening auto-carry chain (PRD §F4.1) | `LEDGER_REFERENCE_QUERY_STUB` swap 시작점. inline projection 유지 + auto-carry chain 추가 |
| 5-2 | inventory_ledger append-only events (PRD §F4.2) | inline projection → ledger aggregation 마이그레이션. **deprecation timeline 명시**: 5-2 commit + 1 epic maintenance (Epic 6 close-out 시 제거) |
| 5-3 | negative closing inventory guard (PRD §V3) | ledger events 종합 검증. **frontend toast** = 0.5 plumbing 진입점 |

**Rationale**:
1. 3-story 분할이 Epic 1·2·3·4 progressive enhancement 패턴 (W1·L1)과 일치 — Epic 5 5-1 → 5-2 → 5-3 각 스토리가 additive
2. 5-2가 `LEDGER_REFERENCE_QUERY_STUB` swap + inline projection deprecation = 두 가지 책임 → spec 명시 필요
3. 5-3 frontend toast = 0.5 plumbing 진입점 명확화

**A4 — Epic 5 frontend toast 0.5 plumbing (cj-style default 결정)**

0.5 plumbing을 Epic 5 5-3 진입 전 별도 Story로 진행. Epic 5 5-1 + 5-2는 backend-only로 진행 (Epic 4 패턴).

| Phase | 책임 | Owner | Deadline |
|---|---|---|---|
| **Phase 1** (Epic 5 5-1 진입 전) | shadcn Tabs / sonner / vitest / Playwright 4종 모두 wire. **Story 0.5 plumbing** = 별도 story file | Amelia | Epic 5 5-1 spec 진입 전 (즉시) |
| Phase 2 (Epic 5 5-1 + 5-2) | backend-only (Epic 4 패턴) | Amelia | Epic 5 5-1 + 5-2 spec 진행 중 |
| Phase 3 (Epic 5 5-3 진입 전) | 5-3 frontend toast 진입 가능 | Amelia | 5-3 spec 진입 전 |

**Rationale**:
1. Epic 4 4 stories 모두 backend-only로 0.5 plumbing NOT blocking (Epic 3 A2 결정) — Epic 5 5-1 + 5-2도 동일 패턴
2. Epic 5 5-3은 frontend toast 필수 → 0.5 plumbing이 5-3 spec 진입 전 완료되어야 함
3. **4번째 epic 연속 deferral = "사실상 표준" 고착화 가속** — Epic 5 5-3 진입 전 0.5 plumbing 별도 Story로 차단
4. Epic 6 (charts) 진입 시 0.5 plumbing 이미 완료 → 6-3 PDF/print 등 frontend chart 패턴에 즉시 활용

## 7. Action Items (Epic 4 close-out + Epic 5 진입)

| ID | 액션 | Owner | Deadline | 성공 기준 |
|---|---|---|---|---|
| **A1** | Pre-existing 8 failures + 27 lint 즉시 정리 | Amelia + Charlie | ✅ done (2026-08-03) | commit 4d088f5 — Epic 5 진입 clean baseline |
| **A2** | Story 4-3 + 4-4 spec 진입 (V1·V4·V7·V8 + V8 CI gate) | Amelia + Alice | ✅ done (2026-08-03) | 4-3 (F-1~F-10 patches) + 4-4 (12 fixture matrix + V8 CI gate) → 4-3 + 4-4 모두 done. 838 pass + 108 skip RLS CI-only + 0 fail |
| **A3** | Epic 5 ledger fold-in 진입점 명시 (cj-style 결정) | Alice + Amelia | ✅ done (본 회고) | 3-story 분할 유지 (5-1 → 5-2 → 5-3). inline projection deprecation timeline = 5-2 spec에서 명시 |
| **A4** | Epic 5 frontend toast 0.5 plumbing 결정 (cj-style 결정) | Amelia | ✅ done (본 회고) | 0.5 plumbing을 Epic 5 5-3 진입 전 별도 Story. Epic 5 5-1 + 5-2는 backend-only |
| **A5** | CR 1.1 전사 single source of truth fix (Phase 1+2) | Charlie + Amelia | **Epic 5 5-1 spec 진입 전 (즉시)** | `apps/api/core/audit_action.py` 작성 (ActionClass 13 + AuditAction 30+ Literal + _ActionRegistry) + 22 call sites migrate + `verification_log` CHECK constraint (Alembic 0013) + drift detector (`tests/services/test_audit_action_centralization.py`) KEPT. `uv run pytest` (full) = 0 failed. Phase 3+4 (기존 audit_logs CHECK + 3-way drift detector)는 Epic 5 spec 진입 시 별도 |
| **A6** | Story 0.5 plumbing 5번째 재평가 (별도 Story) | Amelia | ✅ done (2026-08-05, Story 0.5 landing) | shadcn Tabs / sonner / vitest / Playwright 4종 wire. F-1 / F-30 / F-31 / F-32 / F-33 / F-37 / F-42 / M11 / TYPES-1 closed. Epic 5 5-3 frontend toast 진입 가능. `docs/frontend-toolchain.md` v1.0 SSOT |
| **A7** | Epic 4 0.5 plumbing C4/C6 carry (async test pattern + SDR overclaim) | Amelia + Dana | Epic 5 carry | `tests/cost_engine/test_no_async_decorator.py` AST guard + SDR test count vs pytest actual count drift detector. CR 4-3 lessons C4·C6 carry-over |

## 8. Epic 4 Close-out Tasks

**Done (2026-08-03):**
- [x] A1 pre-existing 8 failures + 27 lint 정리 (commit 4d088f5)
- [x] A2 4-3 (F-1~F-10 patches) + 4-4 (12 fixture matrix + V8 CI gate) → done
- [x] A3 Epic 5 ledger fold-in cj-style 결정
- [x] A4 Epic 5 frontend toast 0.5 plumbing cj-style 결정
- [x] Story 4-3 review F-1 (async tests) + F-5 (Industry enum SSOT) + F-6 (A5 forward-lock) 즉시 wire
- [x] Story 4-4 A5 forward-lock verification (`verify_v8_golden_match` enum + drift count = 0)
- [x] Epic 4 close-out retro 본 문서

**Critical Path (Epic 5 진입 전):**
- [ ] A5 CR 1.1 Phase 1+2 (audit_action.py + 22 call sites migrate + verification_log CHECK) — Epic 5 5-1 spec 진입 전 별도 적용 (4-8h, A5 spike 디자인 그대로)
- [x] A6 Story 0.5 plumbing 별도 Story — ✅ done 2026-08-05 (Epic 5 5-3 spec 진입 전 dep satisfied)

**Nice-to-have (Epic 4 close-out 시 병행 가능):**
- [ ] A7 Epic 4 0.5 plumbing C4/C6 carry — Epic 5 carry
- [ ] 4-3 + 4-4 docs/cost-engine.md §V1·V4·V7·V8 verification 섹션 추가 (이미 4-3 + 4-4 dev-story에서 작성 완료)

## 9. Readiness Assessment

| 항목 | 상태 | 비고 |
|---|---|---|
| Testing & Quality | ✅ 백엔드 280+ tests (engine 67 + orchestrator/endpoint/e2e 30 + verification 25+ + V8 regression 61+ with parametrize) | 5 e2e `@pytest.mark.skip` (Story 0.5 plumbing). pre-existing 0 failures (A1 done) |
| Deployment | ⏳ Supabase defer-to-pilot | sprint-status 유지 |
| Stakeholder Acceptance | ⏳ Sprint 0 내부 진행 | 정식 acceptance 미정 |
| Technical Health | ✅ 안정 | AD-1·5·8·11·15·19·22·24 모두 일관 적용. engine은 pure, service는 wire contract owner. V8 CI gate mandatory |
| Unresolved Blockers | ⚠️ A5 Phase 1+2 미완 + A6 0.5 plumbing 미완 + Epic 5 ledger fold-in (A3 cj-style 결정) | Epic 4 done은 본 회고로. Epic 5 진입은 A5 + A6 완료 후 |
| Capability Matrix | ✅ Epic 1+2+3+4 통합 (13+ capabilities × 4 industries) | `COST_CALCULATION` 4-1 T3 + V8 verification status wire 4-3 v1.3 + V8 골든 fill wire 4-4 v1.4 |
| Audit Action SSOT | ⏳ A5 Phase 1+2 pending | A5 forward-lock partial (4-3 F-6 + 4-4 verify_v8_golden_match) |

## 10. Significant Discoveries

**없음 (Epic 4 wire contract은 Epic 3 회고 + PRD §F3.1·§F4.2·§A11 일치)**

다만 **모니터링 항목**:

- Epic 1·2·3·4 retrospective 누적 패턴: pre-existing failures 4번째 epic 연속 batch → A1 즉시 처리로 Epic 5 진입 clean baseline 확보. Epic 5 close-out 시점에 **5번째 재평가 권고** (CR 1.1 lesson)
- Epic 3 A3 Epic 5 ledger fold-in이 3번째 epic 연속 carry-over (Epic 2 A3 → Epic 3 A3 → Epic 4 A3) → **본 회고 A3 cj-style 결정으로 resolved** (3-story 분할 유지)
- Epic 2 A4 Epic 5 frontend toast 0.5 plumbing 3번째 epic 연속 carry-over (Epic 2 A4 → Epic 3 A2 → Epic 4 A4) → **본 회고 A4 cj-style 결정으로 resolved** (5-3 진입 전 별도 Story)
- CR 1.1 lesson (audit-action inversion) 4번째 epic 연속 재발 → A5 forward-lock 자산화 (F-6 drift detector) + A5 spike 디자인 Phase 1+2 Epic 5 5-1 진입 전 별도 적용 결정
- Story 0.5 plumbing 누적 4번째 epic 연속 deferral → Epic 5 5-3 진입 전 별도 Story로 차단 (A6 결정). ✅ done 2026-08-05 (Story 0.5 landing). Epic 5 5-3 frontend toast + Epic 6 charts + Epic 7 BEP + Epic 8 budget 모두 frontend plumbing dep satisfied

## 11. 다음 단계

1. **즉시 (Epic 5 5-1 spec 진입 전)**:
   - A5 CR 1.1 Phase 1+2 (audit_action.py + 22 call sites migrate + verification_log CHECK) — 4-8h, Charlie + Amelia
   - ~~A6 Story 0.5 plumbing 별도 Story 작성 + spec 진입 — ✅ done 2026-08-05 (Story 0.5 landing)~~
2. **Epic 5 5-1 spec 진입 (A5 done 후, A6 done)**: bmad-create-story (5-1 opening-inventory-auto-carry-chain, baseline_commit = Story 4-4 commit 80f4494)
3. **Story 5-1 spec 진입 전 결정**:
   - A3 (cj-style): 3-story 분할 유지 (5-1 → 5-2 → 5-3). 5-2 spec에서 inline projection deprecation timeline 명시
4. **Story 5-3 spec 진입 전 결정**:
   - A4 (cj-style): 0.5 plumbing 별도 Story 완료 (5-3 frontend toast 진입 가능)
5. **Epic 5 회고 시**: A5 + A6 + A7 follow-through 결정. pre-existing failures 5번째 재평가

### A5 + A7 wire 완료 시점 pytest collection count (2026-08-03)

- **954 tests collected** (CR 4-3 F-2 SDR drift detector의 pytest --collect-only -q 결과)
- 4-1 SDR claim (698 passed) 대비 +256 tests 추가
- 추가 내역:
  - A5 drift detector: `tests/integration/test_audit_action_consistency.py` (4 tests) + `tests/services/test_audit_action_centralization.py` (2 tests)
  - A7 wire: `tests/cost_engine/test_no_async_decorator.py` (2 tests) + `tests/integration/test_sdr_test_count_drift.py` (2 tests)
  - A5 alembic 0014 fixture: `verification_log` V8 골든 fixture 12 + other Epic 4 carry-over
- SDR drift detector 통과 조건: `actual_count ∈ [max_claim, max_claim + 50]`. 본 claim 추가 후 drift window 재설정.

### Story 5.2 in-progress pytest collection count (2026-08-04, 5-2 T1-T3 + T5 + T6 done)

- **1023 tests collected** (Story 5.2 partial: T1 ledger.py 42 + T2 ledger_query.py 20 + T6 event_type drift 4 + 5-2 docs/architecture allowlist 2 = 68 신규)
- 본 retro claim (954) 대비 +69 tests 추가

### Story 5.2 review complete pytest collection count (2026-08-04, 5-2 dev-story complete + bmad-code-review applied)

- **1105 tests collected** (Story 5.2 full: post-T4 wire + T7 capability gate + T8 swap + T9 tests + 5-2 review patches P1-P16 applied = 82 신규)
- 5-2 in-progress claim (1023) 대비 +82 tests 추가
- 본 review claim으로 override: MAX SDR claim = 1105 (CR 4-3 F-2 A7 wire)
- 추가 내역 (Story 5.2 SPEC 진입 시점까지):
  - T1 pure kernel `tests/services/m4_inventory/test_ledger.py` (42 tests: 11 parametrized event_type + 13 build_event_payload + 4 NamedTuple + 4 append_only_violation_message + ...)
  - T2 pure kernel #2 `tests/services/m4_inventory/test_ledger_query.py` (20 tests: 5 constants + 7 period_closing + 6 carry_chain + 4 SQL safety)
  - T6 event_type drift `tests/integration/test_inventory_ledger_event_type_drift.py` (4 tests: kernel↔migration + kernel↔ORM + count_is_11 + expected_set)
- SDR drift detector 통과 조건: `actual_count ∈ [max_claim, max_claim + 50]`. 본 claim 추가 후 drift window 재설정 (954 → 1023).

## 12. 팀 인사와 마무리

Amelia (Developer): "Epic 4 4 stories 모두 done, V8 CI gate가 mandatory로 wire되어 1원 단위 회귀가 CI에서 즉시 차단됩니다. W1 'pure kernel → service wiring' 분할 + W2 AD-22 boundary strengthening + W8 V8 placeholder → 12 fixture fill이 Epic 5·6·9의 좋은 패턴 자산입니다. L7 A5 forward-lock + drift detector가 5번째 epic 연속 drift를 자산화 — 4-3 review F-6 + 4-4 verify_v8_golden_match가 첫 wire 사례입니다."

Charlie (Senior Dev): "PRD §A11 '입력 시 경고 → 마감 시 차단' 정책이 Epic 3.3 (입력 layer) + Epic 4.2 (마감 layer) + Epic 4.3 (verification) + Epic 4.4 (V8 regression) 4 layer로 정확히 분리됨. wire contract level에서 정렬. A5 Phase 1+2를 Epic 5 5-1 spec 진입 전 별도 적용 결정 — 4번째 epic 연속 재발은 A5 forward-lock 자산으로 capture됐고, 다음 22 call sites migrate + drift detector 통과가 Epic 5/6/7/11 audit log 일관성의 핵심."

Alice (Product Owner): "A3 (Epic 5 ledger fold-in) + A4 (frontend toast 0.5 plumbing) cj-style 결정 완료 — 3-story 분할 유지 + 0.5 plumbing을 Epic 5 5-3 진입 전 별도 Story. A1 pre-existing 8 failures + 27 lint (commit 4d088f5) + A2 4-3 + 4-4 done으로 Epic 4 close-out입니다. Epic 5 진입은 A5 + A6 done 후."

Dana (QA Engineer): "백엔드 280+ tests 안정 (engine 67 + orchestrator/endpoint/e2e 30 + verification 25+ + V8 regression 61+ with parametrize). 5 e2e `@pytest.mark.skip` (Story 0.5 plumbing). pre-existing 0 failures (A1 done). V8 CI gate mandatory로 V8 1원 단위 회귀 즉시 차단. C4 (async test pattern) + C6 (SDR overclaim) carry-over — A7 Epic 5 carry 결정."

Elena (Junior Dev): "Epic 1·2·3 회고 패턴 (lightweight 25-30분 + 12 sections + 이전 epic follow-through) 4번째 반복 — 회고 운영이 안정화됐습니다. L8 CR 4-3 lessons 즉시 wire (F-1~F-10) = CR pattern 학습 = Epic 5 carry-over 자산. A6 Story 0.5 plumbing 별도 Story가 Epic 5 5-3 frontend toast 진입점입니다."

kjw (Project Lead): "회고 종료. Epic 4 close-out — 4-1·4-2·4-3·4-4 모두 done. A2 4-4 part done 마킹. A3 + A4 cj-style 결정 완료. Epic 5 진입은 A5 (CR 1.1 Phase 1+2) + A6 (Story 0.5 plumbing 별도 Story) done 후."
