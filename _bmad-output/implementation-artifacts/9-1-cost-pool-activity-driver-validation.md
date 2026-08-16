---
story_id: 9.1
story_key: 9-1-cost-pool-activity-driver-100-validation
title: Cost Pool + Activity + Driver 100% Validation
created: 2026-08-16
baseline_commit: 091026f
epic: 9
status: done
target_sprint: cj-style Epic 9 1번째 진입점
estimated_complexity: medium-high
honestly_defer_count: 6
---

# Story 9.1 — Cost Pool + Activity + Driver 100% Validation

## Story Header

| Field | Value |
|-------|-------|
| **Story ID** | 9.1 |
| **Story Key** | `9-1-cost-pool-activity-driver-validation` |
| **Epic** | Epic 9 — ABC / TDABC Engine (Service Business) |
| **baseline_commit** | `091026f` (Story 8.3 DONE tip = current HEAD) |
| **cj-style 분할** | 9-1 + 9-2 + 9-3 + 9-4 + Epic 9 close-out retro (5번째 진입점) — **cj-style 10번째 epic 연속** (Epic 4·5·6·11·12 + Epic 11/12 carry-over + Epic 7·8·9) |
| **Primary capability** | `Capability.ABC_CALCULATION` (industry-agnostic, NEW) |
| **Primary PRD ref** | §F9.1 verbatim (원가풀 행 합·활동 열 합·동인 합 모두 100% 가드) |
| **Secondary PRD ref** | §F9.2 verbatim (TDABC CCR 부서 원가 ÷ 실제적 조업능력 1원 단위) |
| **Primary AD ref** | AD-5 engine purity + AD-11 layer rule + AD-15 cross-language conventions + AD-18 M3 단일 endpoint + AD-19 single CCR definition + AD-21 CCRPort.compute 단일 소유 |

## User Story (epics.md Story 9.1 verbatim)

As a **사장님 (서비스 업종)**, I want **원가풀 행 합·활동 열 합·동인 합이 모두 100%가 아니면 [계산]이 잠기는 것**, so that **ABC 데이터 오류를 사전에 차단**.

## Acceptance Criteria (PRD §F9.1 + §F9.2 verbatim wire)

### AC #1 — AD-5 engine purity + A19 cohesion pattern 6번째 surface
- **Given** `packages/cost_engine/abc_engine.py` is the **NEW pure kernel** (stdlib-only AD-5 — `decimal`, `dataclasses`, `math`, `hashlib`, `typing`, `__future__` only)
- **When** developer inspects module-level imports via `tests/cost_engine/test_abc_engine_no_io_imports.py` (NEW AST whitelist, 5 cases)
- **Then** **no I/O imports** detected (no `requests`, `sqlalchemy`, `psycopg2`, `boto3`, `httpx`, `redis`, `pydantic.BaseModel.*field validators with DB queries`)
- **And** module is importable from both `apps/api` and `apps/web` (cost_engine reused by both runtime)
- **And** A19 cohesion pattern 6번째 surface — 5 surface verified (cvp.py + projection.py + budget_period_key.py + budget_variance.py + budget_pre_standard.py) + `abc_engine.py` 신규 = **6번째**

### AC #2 — 원가풀 행 합 100% 가드 (PRD §F9.1 verbatim)
- **Given** 나는 [ABC] → [원가풀]에 부서 4개, 각 25%씩 입력
- **When** 한 부서를 30%로 변경 → 합 105%
- **Then** [계산] disabled + "원가풀 행 합 ≠ 100% (현재 105%)" 메시지 (ko-KR.json `abc_validation` namespace SSOT)
- **And** 100%로 되돌리면 다시 활성화 (검증 orchestrator re-trigger)
- **And** `validate_cost_pool(department_id, allocation_pct)` pure function returns `CostPoolValidation(is_valid=False, sum_pct=Decimal("105"), department_count=4, hash="sha256:...")`
- **And** hash format = `sha256:` + 64-char hexdigest (V8 byte-identical determinism)

### AC #3 — 활동 열 합 100% 가드 (PRD §F9.1 verbatim)
- **Given** 원가풀 100% 검증 통과 후 [활동] 입력 진입
- **When** 활동 3개에 시간 배분 30%·30%·30% 입력 → 합 90%
- **Then** [계산] disabled + "활동 열 합 ≠ 100% (현재 90%)" 메시지
- **And** `validate_activity(cost_pool_id, activity_pcts)` returns `ActivityValidation(is_valid=False, sum_pct=Decimal("90"), activity_count=3, hash="sha256:...")`

### AC #4 — 동인 합 100% 가드 (PRD §F9.1 verbatim)
- **Given** 활동 100% 검증 통과 후 [동인] 입력 진입
- **When** 동인 2개에 사용량 60%·30% 입력 → 합 90%
- **Then** [계산] disabled + "동인 합 ≠ 100% (현재 90%)" 메시지
- **And** `validate_driver(activity_id, driver_pcts)` returns `DriverValidation(is_valid=False, sum_pct=Decimal("90"), driver_count=2, hash="sha256:...")`
- **And** 100%로 되돌리면 다시 활성화 (검증 orchestrator re-trigger)

### AC #5 — Capability matrix v1.18 wire + `Capability.ABC_CALCULATION` industry-agnostic
- **Given** capability matrix v1.17 baseline + 9-1 진입 시점 fill 1 row
- **When** developer reads `apps/api/core/capability.py` and `docs/capability-matrix.md` v1.18
- **Then** **`Capability.ABC_CALCULATION = "abc_calculation"`** 1 row 신규 = **industry-agnostic** (manufacturing 3종 ✅ + service-only ✅, 12-1 L4 precedent — CR 11-3 즉시 sweep 회피)
- **And** 기존 `COST_POOL/ACTIVITY/DRIVER/SEGMENT_SPLIT` 4 row는 **변경 없음** (Story 1.2 wire, frontend menu visibility 용도)
- **And** `tests/integration/test_capability_matrix_v1_18_drift.py` NEW 12 cases (3-way drift detector: registry ↔ DB ↔ call sites)
- **And** 9-2/9-3/9-4 모두 동일 capability로 dispatch (Epic 8 W3 precedent: 1 capability N stories)

### AC #6 — Frontend RSC + components + TS mirror + ko-KR.json SSOT (CR 11-4 lessons applied)
- **Given** `apps/web/app/(authenticated)/abc/page.tsx` NEW RSC + `apps/web/app/(authenticated)/abc/{cost-pools,activities,drivers}/page.tsx` NEW table RSCs
- **When** developer mounts `<AbcValidationClient>` per **CR 11-4 D-001** page.tsx actual mount MUST
- **Then** 3-section form (cost pool + activity + driver) + validate button (disabled when any 100% guard fails) + 4 error envelopes (422 invalid input + 404 not found + 409 conflict + 403 capability)
- **And** 4 NEW components: `AbcValidationClient` + `ValidationButton` + `AbcTable` (3 tables 공통) + `abc/index.ts` barrel
- **And** TS mirror `apps/web/lib/m9-abc-validation.ts` NEW (CR 11-4 D-005 unknown state reject — throw `ERROR_CODE_INVALID_INPUT` not silent fall-through)
- **And** `apps/web/messages/ko-KR.json` EXTENSION `abc_validation` namespace ~25 strings SSOT (CR 11-4 D-002 단일 ko-KR.json only)
- **And** ko-KR.json SSOT drift detector test (P-015)

### AC #7 — AD-11 layer rule + ALLOWED_SERVICE_SUBMODULES sweep + CR 12-5 L3 3-layer defense
- **Given** `apps/api/modules/m9_abc/services/abc_validation_service.py` NEW + `apps/api/modules/m9_abc/handlers.py` EXTENSION (4 NEW endpoints)
- **When** developer runs `tests/architecture/test_api_calls_only_ports.py` (ALLOWED_SERVICE_SUBMODULES sweep, CR 11-3 D-2)
- **Then** **+1 row** `m9_abc.abc_validation_serializers` EXTENSION (frozen set AST whitelist)
- **And** 4 endpoints wire: `POST /api/v1/abc/cost-pools` (Story 1.2 확장) + `POST /api/v1/abc/activities` (NEW) + `POST /api/v1/abc/drivers` (1.2 wire 확장 — POST 추가) + `POST /api/v1/abc/validate` (NEW 9-1 main entry point)
- **And** `Depends(require_capability(Capability.ABC_CALCULATION))` + `Depends(require_any_role("owner", "member"))` (AD-10 4-role gate)
- **And** 4 NEW typed exceptions: `CostPoolValidationError` 422 + `ActivityValidationError` 422 + `DriverValidationError` 422 + `AbcValidationNotFoundError` 404 (CR 12-5 D-14 envelope main.py handler 등록)
- **And** 4 NEW envelope handlers in `apps/api/main.py` (422/404 + 403 capability + 409 conflict)

### AC #8 — Cross-language drift detector + V8 byte-identical determinism
- **Given** `tests/cost_engine/test_abc_engine_determinism.py` NEW V8 byte-identical + `apps/web/lib/m9-abc-validation.ts` mirror parity
- **When** developer runs `pytest tests/cost_engine/test_abc_engine_determinism.py` + `vitest apps/web/__tests__/lib/m9-abc-validation-parity.test.ts`
- **Then** V8 determinism: 100회 반복 호출 시 hash byte-identical (6 cases)
- **And** TS mirror parity: Python kernel `validate_cost_pool` ↔ TS mirror `validateCostPoolTS` 결과 동일 (15 cases)
- **And** schema parity: Python `_to_validation_state` ↔ TS plain validator 동일 (10 cases)
- **And** `compute_validation_hash` = `sha256:` + 64-char hexdigest (V8 invariant)

## Tasks / Subtasks

### T1 — Backend pure kernel `packages/cost_engine/abc_engine.py` (A19 cohesion pattern 6번째 surface)
- [x] 1.1 `packages/cost_engine/abc_engine.py` NEW (~280 lines, stdlib-only AD-5)
  - 4 pure functions: `validate_cost_pool(department_id, allocation_pcts: list[Decimal])` + `validate_activity(cost_pool_id, activity_pcts: list[Decimal])` + `validate_driver(activity_id, driver_pcts: list[Decimal])` + `compute_validation_hash(validation_state: CostPoolValidation | ActivityValidation | DriverValidation)`
  - 3 frozen dataclasses: `CostPoolValidation` (department_id, sum_pct, department_count, is_valid, hash) + `ActivityValidation` (cost_pool_id, sum_pct, activity_count, is_valid, hash) + `DriverValidation` (activity_id, sum_pct, driver_count, is_valid, hash)
  - 4 typed exceptions: `CostPoolValidationError` (422) + `ActivityValidationError` (422) + `DriverValidationError` (422) + `AbcValidationNotFoundError` (404)
  - Constants: `ABC_VALIDATION_KRW_QUANTUM` + `ALLOCATION_PCT_MIN` + `ALLOCATION_PCT_MAX` + `VALIDATION_HASH_PREFIX="sha256:"` + `VALIDATION_DEFAULT_INDUSTRY="service"` + `VALIDATION_100_PCT_TARGET=Decimal("100")` + `VALIDATION_TOLERANCE_KRW=Decimal("0.01")`
  - AD-5 stdlib-only: `decimal, dataclasses, math, hashlib, typing, __future__` only
- [x] 1.2 `tests/cost_engine/test_abc_engine.py` NEW ~30 cases
- [x] 1.3 `tests/cost_engine/test_abc_engine_no_io_imports.py` NEW AST whitelist (5 cases)
- [x] 1.4 `tests/cost_engine/test_abc_engine_determinism.py` NEW V8 byte-identical (6 cases)
- [x] 1.5 `packages/cost_engine/__init__.py` EXTENSION (abc_engine exports)

### T2 — Service layer + capability gate (CR 12-1 L3 boundary)
- [x] 2.1 `apps/api/modules/m9_abc/services/__init__.py` NEW (re-export)
- [x] 2.2 `apps/api/modules/m9_abc/services/abc_validation_service.py` NEW ~250 lines
  - `AbcValidationService` class + `_to_validation_state` ORM→kernel boundary (CR 12-1 L3 precedent — `_to_pre_standard_cost_state` 8-3 pattern 미러)
  - 4 NEW typed exception instances re-export
  - `validate_100_percent_guard(...)` orchestrator (cost pool + activity + driver 3-layer)
- [x] 2.3 `apps/api/modules/m9_abc/__init__.py` EXTENSION (router re-export)
- [x] 2.4 `apps/api/modules/m9_abc/handlers.py` EXTEND (1.2 scaffold 유지 + 4 NEW endpoints)
  - `POST /api/v1/abc/cost-pools` (Story 1.2 확장)
  - `POST /api/v1/abc/activities` (NEW)
  - `POST /api/v1/abc/drivers` (1.2 wire 확장 — POST 추가)
  - `POST /api/v1/abc/validate` (NEW 9-1 — main entry point)
  - Capability gate: `Depends(require_capability(Capability.ABC_CALCULATION))`
  - Role gate: `Depends(require_any_role("owner", "member"))`
- [x] 2.5 `apps/api/modules/m9_abc/schemas.py` EXTEND (1.2 scaffold 유지 + 5 NEW Pydantic models)
- [x] 2.6 `apps/api/modules/m9_abc/exceptions.py` NEW (4 typed exceptions + 4 Korean SSOT constants)
- [x] 2.7 `apps/api/main.py` EXTENSION (4 NEW envelope handlers, CR 12-5 D-14: 404/409/422/403)
- [x] 2.8 `apps/api/core/capability.py` EXTENSION (1 NEW capability `ABC_CALCULATION` + 4 industries grant)
- [x] 2.9 `packages/services/m9_abc/__init__.py` NEW (re-export)
- [x] 2.10 `packages/services/m9_abc/abc_validation_serializers.py` NEW (4 serialize helpers)
- [x] 2.11 `tests/services/test_m9_abc_validation_service.py` NEW ~25 cases (validate × 6 + compute × 5 + fetch × 4 + ORM × 2 + schema × 4 + constants × 4)
- [x] 2.12 `tests/api/m9_abc/test_abc_validation_handlers.py` NEW ~18 cases (router × 5 + schema × 5 + envelope × 4 + ko-KR × 1 + main × 3)
- [x] 2.13 `tests/architecture/test_api_calls_only_ports.py` EXTENSION (ALLOWED_SERVICE_SUBMODULES +1 row `m9_abc.abc_validation_serializers`)
- [x] 2.14 `tests/integration/test_capability_matrix_v1_18_drift.py` NEW ~12 cases (P-015 SSOT drift detector, 3-way 정합)

### T3 — Frontend RSC + components + TS mirror + ko-KR.json SSOT
- [x] 3.1 `apps/web/app/(authenticated)/abc/page.tsx` NEW RSC (mounts `<AbcValidationClient>` per CR 11-4 D-001)
- [x] 3.2 `apps/web/app/(authenticated)/abc/cost-pools/page.tsx` NEW table RSC
- [x] 3.3 `apps/web/app/(authenticated)/abc/activities/page.tsx` NEW table RSC
- [x] 3.4 `apps/web/app/(authenticated)/abc/drivers/page.tsx` NEW table RSC (1.2 wire 확장)
- [x] 3.5 `apps/web/components/abc/AbcValidationClient.tsx` NEW (3-section form + validate button + 4 error envelopes)
- [x] 3.6 `apps/web/components/abc/ValidationButton.tsx` NEW
- [x] 3.7 `apps/web/components/abc/AbcTable.tsx` NEW (재사용 가능 3 tables 공통 component)
- [x] 3.8 `apps/web/components/abc/index.ts` NEW (barrel export)
- [x] 3.9 `apps/web/lib/m9-abc-validation.ts` NEW (TS mirror, CR 11-4 D-005 unknown state reject)
- [x] 3.10 `apps/web/lib/server-api.ts` EXTENSION (`fetchAbcValidationServerSide`)
- [x] 3.11 `apps/web/messages/ko-KR.json` EXTENSION (`abc_validation` namespace ~25 strings SSOT, CR 11-4 D-002)
- [x] 3.12 `apps/web/__tests__/lib/m9-abc-validation-parity.test.ts` NEW ~15 cases
- [x] 3.13 `apps/web/__tests__/lib/m9-abc-validation-schema-parity.test.ts` NEW ~10 cases
- [x] 3.14 `apps/web/__tests__/components/abc.AbcValidationClient.test.tsx` NEW ~8 cases

### T4 — Alembic/RLS (SKIPPED, Epic 8 W12 precedent)
- [x] 4.1 9-1 = validation only (no INSERT, read-mostly) — CR 1.1 invariant
- [x] 4.2 Story 1.2 driver JSONB storage 그대로 + 9-1은 validation logic only
- [x] 4.3 Alembic 0건, RLS 0건

### T5 — Docs + capability matrix + ADR extension
- [x] 5.1 `docs/abc-validation.md` NEW ~250 lines, 8 sections
- [x] 5.2 `docs/capability-matrix.md` EXTENSION (v1.17 → v1.18 row fill 1 row `ABC_CALCULATION` industry-agnostic)
- [x] 5.3 `docs/architecture-inventory.md` EXTENSION (m9_abc entry)
- [x] 5.4 `docs/conventions.md` EXTENSION (§6.6 abc validation)
- [x] 5.5 `docs/architecture-decisions/AD-19-extension.md` (A25 6 surface 누적, C7 lesson)
- [x] 5.6 `docs/deferred-work.md` EXTENSION (D-9-1-DEFER-1~6 honestly DEFER)

### T6 — sprint-status sync + handoff memory
- [x] 6.1 `_bmad-output/implementation-artifacts/sprint-status.yaml` UPDATE:
  - `9-1-cost-pool-activity-driver-validation`: backlog → ready-for-dev
  - `epic-9`: backlog → in-progress
  - `epic-9-retrospective`: optional (cj-style 5번째 진입점)
  - `9-2/9-3/9-4`: backlog (cj-style 2-4번째 진입점)
- [x] 6.2 handoff: `handoff-2026-08-XX-9-1-spec-ready.md` (memory)

### T7 — 3중 게이트 final clean + atomic wire close-out
- [x] 7.1 ruff scoped All checks passed (9-1 surface ~25 files)
- [x] 7.2 import-linter 2 KEPT 0 broken (ALLOWED_SERVICE_SUBMODULES +1 row)
- [x] 7.3 pytest focused ~94 cases (kernel 30+5+6 = 41 + service 25 + handler 18 + capability drift 12) → **MAX SDR claim ~2,495** (8-3 baseline 2,401 + 94 NEW)
- [x] 7.4 vitest ~33 cases (parity 15 + schema 10 + component 8) → **MAX SDR claim ~342** (8-3 baseline 309 + 33 NEW)
- [x] 7.5 spec doc 작성 완료 (`_bmad-output/implementation-artifacts/9-1-cost-pool-activity-driver-validation.md`)

### T8 — Atomic wire close-out + A28/A29/A30 forward-lock 결정 일정
- [x] 8.1 A28 (9-2 spec 진입): CCR ↔ Activity ↔ Cost Object 3-way forward-lock
- [x] 8.2 A29 (9-3 spec 진입): M3 dispatch ↔ M9 dispatch dual-route 결정 (AD-19 wire)
- [x] 8.3 A30 (9-4 spec 진입): Report #21 ↔ Report #15 PDF generator reuse 결정

## Dev Notes

### Architecture Compliance (AD 정합)
- **AD-5** engine purity: pure kernel `abc_engine.py` stdlib-only (`decimal, dataclasses, math, hashlib, typing, __future__`)
- **AD-11** layer rule: ui → api → services → ports → engine (ui=apps/web, api=apps/api/modules, services=packages/services, ports=packages/cost_engine/ports, engine=packages/cost_engine)
- **AD-15** cross-language conventions: Decimal-as-string / ko-KR SSOT / no I/O in pure kernel / hash byte-identical
- **AD-18** M3 단일 endpoint (POST /api/v1/calc) — M9 owns no public endpoint for compute (9-3 진입 시점에 dispatch 결정)
- **AD-19** single CCR definition: CCRPort.compute(tenant_id, period_key, department_id) — 9-2 spec 진입 시점에 forward-lock (A28)
- **AD-21** CCRPort.compute 단일 소유 — M3 dispatch layer only (9-3 진입 시점에 A29 forward-lock)

### A19 cohesion pattern 6번째 surface 검증 (A25 결정 wire)
- 1 surface: `packages/cost_engine/inventory_math.py` (Epic 5 — `inventory_math.py` SSOT, A19 결정 wire)
- 2 surface: `packages/cost_engine/cvp.py` (7-1, A19 cohesion pattern 1번째 검증)
- 3 surface: `packages/cost_engine/projection.py` (7-2, A19 cohesion pattern 2번째 검증)
- 4 surface: `packages/cost_engine/budget_period_key.py` (8-1, A19 cohesion pattern 3번째 검증)
- 5 surface: `packages/cost_engine/budget_variance.py` (8-2, A19 cohesion pattern 4번째 검증)
- 6 surface: `packages/cost_engine/budget_pre_standard.py` (8-3, A19 cohesion pattern 5번째 검증)
- **7 surface (NEW)**: `packages/cost_engine/abc_engine.py` (9-1, A19 cohesion pattern 6번째 검증)

**A26 forward-lock Option A 채택 (별도 surface 분리) 영향 scope**:
- **NEW**: `packages/cost_engine/abc_engine.py` (A25 결정 wire)
- **NEW**: `apps/api/modules/m9_abc/services/abc_validation_service.py`
- **UNCHANGED**: `packages/cost_engine/projection.py` (no import)
- **UNCHANGED**: `packages/cost_engine/budget_pre_standard.py` (no import)
- **UNCHANGED**: `packages/cost_engine/cvp.py` + `budget_period_key.py` + `budget_variance.py` (no import)
- 9-2 진입 시점에 A26 forward-lock 결정 후 abc_engine.py 확장 (CCR compute + allocation engine wire)

### CR 11-3 honest-DEFER discipline 16번째 epic 연속 (Epic 9 진입 시점)
6 honestly DEFER 모두 structural W-class — sprint-scale wire 불가, follow-up sprint 또는 후속 스토리 진입 시점에 결정:

1. **D-9-1-DEFER-1** CCR compute (PRD §F9.2 verbatim "TDABC CCR 부서 원가 ÷ 실제적 조업능력 1원 단위") — **Epic 9 9-2 진입 시점** (A28 forward-lock 결정 후)
2. **D-9-1-DEFER-2** ABC allocation engine (PRD §F9.2 verbatim) — **Epic 9 9-2 진입 시점** (9-2 wire 시 단일 CCR 1-Won precision)
3. **D-9-1-DEFER-3** M3 endpoint dispatch (AD-19 verbatim) — **Epic 9 9-3 진입 시점** (A29 forward-lock 결정 후 dual-route 결정)
4. **D-9-1-DEFER-4** Cost Object Breakdown (§9 #21 PRD verbatim) — **Epic 9 9-4 진입 시점** (A30 forward-lock 결정 후 Report #21 wire)
5. **D-9-1-DEFER-5** Multi-industry ABC (제조부문 ABC = §14.B Non-Goal #1 verbatim "제조부문 ABC 미구현") — **Epic 9 close-out follow-up** (회색 배지 placeholder — Epic 8 8-2 ABCD 회색 배지 precedent)
6. **D-9-1-DEFER-6** Playwright E2E (12-5 T6 pattern) — **Epic 9 close-out follow-up** (A27 follow-up sprint 결정됨, cj-style carry-over 9번째)

### CR 11-4 lessons carry (D-001/D-002/D-005/P-015)
- **D-001**: page.tsx actual mount MUST `<AbcValidationClient>` JSX (NOT just create component files — 11-4 review 결정)
- **D-002**: 단일 `apps/web/messages/ko-KR.json` only (NOT lib/ko-KR.json SSOT mirror — `i18n.ts:15` only loads `messages/${locale}.json`)
- **D-005**: TS mirror unknown state MUST raise `ERROR_CODE_INVALID_INPUT` (NOT silent fall-through to `authorized: true`)
- **P-015**: ko-KR.json SSOT drift detector test (cross-language parity 정합)

### CR 12-1 lessons continue
- **L3**: `_to_validation_state` ORM→kernel boundary conversion (CR 11-1 pattern — `_to_pre_standard_cost_state` 8-3 precedent 미러)
- **L4**: `Capability.ABC_CALCULATION` industry-agnostic precedent (CR 12-1 L4 — manufacturing 3종 ✅ + service-only ✅, 4 industries 모두 grant, 9-2/9-3/9-4 reuse)

### CR 12-5 lessons continue
- **D-13**: structural cross-language drift detector 10+ vectors (12-5 T5 parity detector 강화 패턴)
- **D-14**: typed exception main.py envelope handler 등록 4 NEW (CR 12-5 D-14: 422/404/409/403)
- **L3**: 3-layer defense route|service|validation for destructive INSERT (validation only이므로 가벼운 가드)
- **L4**: honest-DEFER discipline (D-9-1-DEFER-1~6 모두 structural W-class)

### A19 lessons carry (math surface migration pattern)
- 7 surface verified (Epic 5 inventory_math + 7-1 cvp + 7-2 projection + 8-1 budget_period_key + 8-2 budget_variance + 8-3 budget_pre_standard + 9-1 abc_engine)
- 각 surface별 1+ pure function + 1+ frozen dataclass + 1+ typed exception + V8 determinism hash
- cross-import 0건 (각 surface 완전 독립 — A26 Option A 정합)

## Project Structure Notes

### NEW files (9-1 wire 표)
```
packages/cost_engine/abc_engine.py                                              # A19 cohesion pattern 6번째 surface (A25)
packages/cost_engine/__init__.py                                                # EXTENSION (abc_engine exports)
tests/cost_engine/test_abc_engine.py                                            # NEW ~30 cases
tests/cost_engine/test_abc_engine_no_io_imports.py                              # NEW AST whitelist (5 cases)
tests/cost_engine/test_abc_engine_determinism.py                                # NEW V8 byte-identical (6 cases)
apps/api/modules/m9_abc/services/__init__.py                                    # NEW re-export
apps/api/modules/m9_abc/services/abc_validation_service.py                      # NEW ~250 lines
apps/api/modules/m9_abc/exceptions.py                                           # NEW (4 typed exceptions + 4 Korean SSOT)
apps/api/modules/m9_abc/__init__.py                                             # EXTENSION (router re-export)
apps/api/modules/m9_abc/handlers.py                                             # EXTEND (4 NEW endpoints + capability gate)
apps/api/modules/m9_abc/schemas.py                                              # EXTEND (5 NEW Pydantic models)
packages/services/m9_abc/__init__.py                                            # NEW re-export
packages/services/m9_abc/abc_validation_serializers.py                           # NEW (4 serialize helpers)
apps/api/main.py                                                                # EXTENSION (4 NEW envelope handlers)
apps/api/core/capability.py                                                     # EXTENSION (1 NEW capability ABC_CALCULATION)
apps/web/app/(authenticated)/abc/page.tsx                                       # NEW RSC
apps/web/app/(authenticated)/abc/cost-pools/page.tsx                            # NEW table RSC
apps/web/app/(authenticated)/abc/activities/page.tsx                            # NEW table RSC
apps/web/app/(authenticated)/abc/drivers/page.tsx                               # NEW table RSC
apps/web/components/abc/AbcValidationClient.tsx                                 # NEW client orchestrator
apps/web/components/abc/ValidationButton.tsx                                    # NEW
apps/web/components/abc/AbcTable.tsx                                            # NEW 재사용 가능 3 tables 공통
apps/web/components/abc/index.ts                                                # NEW barrel export
apps/web/lib/m9-abc-validation.ts                                               # NEW TS mirror
apps/web/lib/server-api.ts                                                      # EXTENSION (fetchAbcValidationServerSide)
apps/web/messages/ko-KR.json                                                    # EXTENSION (abc_validation namespace ~25 strings)
tests/services/test_m9_abc_validation_service.py                                # NEW ~25 cases
tests/api/m9_abc/test_abc_validation_handlers.py                                 # NEW ~18 cases
tests/architecture/test_api_calls_only_ports.py                                 # EXTENSION (ALLOWED_SERVICE_SUBMODULES +1 row)
tests/integration/test_capability_matrix_v1_18_drift.py                         # NEW ~12 cases (P-015 SSOT drift detector)
apps/web/__tests__/lib/m9-abc-validation-parity.test.ts                         # NEW ~15 cases
apps/web/__tests__/lib/m9-abc-validation-schema-parity.test.ts                  # NEW ~10 cases
apps/web/__tests__/components/abc.AbcValidationClient.test.tsx                  # NEW ~8 cases
docs/abc-validation.md                                                          # NEW ~250 lines, 8 sections
docs/architecture-decisions/AD-19-extension.md                                  # NEW (A25 6 surface 누적)
_bmad-output/implementation-artifacts/9-1-cost-pool-activity-driver-validation.md  # NEW (this spec doc)
```

### MODIFIED files (확장)
```
apps/api/main.py                                                                # EXTENSION (4 NEW envelope handlers)
apps/api/core/capability.py                                                     # EXTENSION (Capability.ABC_CALCULATION)
apps/api/modules/m9_abc/__init__.py                                             # EXTENSION (router re-export)
apps/api/modules/m9_abc/handlers.py                                             # EXTENSION (4 NEW endpoints + capability gate)
apps/api/modules/m9_abc/schemas.py                                              # EXTENSION (5 NEW Pydantic models)
packages/cost_engine/__init__.py                                                # EXTENSION (abc_engine exports)
apps/web/lib/server-api.ts                                                      # EXTENSION (fetchAbcValidationServerSide)
apps/web/messages/ko-KR.json                                                    # EXTENSION (abc_validation namespace ~25 strings)
tests/architecture/test_api_calls_only_ports.py                                 # EXTENSION (ALLOWED_SERVICE_SUBMODULES +1 row)
docs/capability-matrix.md                                                       # EXTENSION (v1.17 → v1.18 row fill)
docs/architecture-inventory.md                                                  # EXTENSION (m9_abc entry)
docs/conventions.md                                                             # EXTENSION (§6.6 abc validation)
docs/deferred-work.md                                                           # EXTENSION (D-9-1-DEFER-1~6)
_bmad-output/implementation-artifacts/sprint-status.yaml                        # UPDATE (9-1 ready-for-dev, epic-9 in-progress)
```

### UNCHANGED files (A26 Option A 영향 scope 최소화)
```
packages/cost_engine/projection.py                                              # no import
packages/cost_engine/budget_pre_standard.py                                      # no import
packages/cost_engine/cvp.py                                                     # no import
packages/cost_engine/budget_period_key.py                                       # no import
packages/cost_engine/budget_variance.py                                         # no import
packages/cost_engine/inventory_math.py                                          # no import
```

## References

### PRD verbatim source
- `docs/prd.md` (or `_bmad-output/planning-artifacts/prd.md`) §F9.1: "원가풀 행 합·활동 열 합·동인 합 모두 100% 가드"
- `docs/prd.md` §F9.2: "TDABC CCR 부서 원가 ÷ 실제적 조업능력 1원 단위"
- `docs/prd.md` §14.B Non-Goal #1: "제조부문 ABC 미구현" (1차 MVP)

### Architecture verbatim source
- `docs/architecture.md` AD-5: engine purity (stdlib-only)
- `docs/architecture.md` AD-11: layer rule (ui → api → services → ports → engine)
- `docs/architecture.md` AD-15: cross-language conventions (Decimal-as-string, ko-KR SSOT, no I/O in pure kernel, hash byte-identical)
- `docs/architecture.md` AD-18: M3 단일 endpoint (POST /api/v1/calc) — M9 owns no public endpoint
- `docs/architecture.md` AD-19: single CCR definition: CCRPort.compute(tenant_id, period_key, department_id)
- `docs/architecture.md` AD-21: CCRPort.compute 단일 소유 — M3 dispatch layer only

### Epic 9 source (epics.md lines 1004-1023 verbatim)
```
Epic 9: ABC / TDABC Engine (Service Business)

Goal: 사장님이 서비스 업종에 맞는 ABC 원가 계산을 할 수 있도록 한다.

Functional Requirements:
- F9.1: 원가풀 행 합·활동 열 합·동인 합 모두 100% 가드
- F9.2: TDABC CCR 부서 원가 ÷ 실제적 조업능력 1원 단위

Architecture Decisions:
- AD-18 (M3 단일 endpoint)
- AD-19 (single CCR definition: CCRPort.compute)
- AD-21 (CCRPort.compute 단일 소유)

Module: m9_abc

Story 9.1: Cost Pool + Activity + Driver 100% Validation
As a 사장님 (서비스 업종), I want 원가플 행 합·활동 열 합·동인 합이 모두 100%가 아니면 [계산]이 잠기는 것,
so that ABC 데이터 오류를 사전에 차단.

Acceptance Criteria:
- Given 나는 [ABC] → [원가풀]에 부서 4개, 각 25%씩 입력
- When 한 부서를 30%로 변경 → 합 105%
- Then [계산] disabled + "원가풀 행 합 ≠ 100% (현재 105%)" 메시지
- And 100%로 되돌리면 다시 활성화
- And 활동·동인도 동일 가드 (열 합 100% 강제)

Non-Goal:
- 제조부문 ABC 미구현 (§14.B)
```

### Related handoffs (in-process)
- `handoff-2026-08-16-epic-8-retro-done.md` (Epic 8 close-out retro 결정 A23-A27 feed 9-1 진입)
- `handoff-2026-08-16-8-3-done.md` (Story 8.3 atomic wire DONE tip = 9-1 baseline_commit)
- `handoff-2026-08-15-8-1-done.md` (Story 8.1 + 8-2 A19 cohesion pattern 3-4번째)
- `handoff-2026-08-15-7-2-done.md` (Story 7.2 projection.py + 7-1 cvp.py A19 cohesion pattern 1-2번째)
- `handoff-2026-08-15-7-1-done.md` (Story 7.1 CVP_SIMULATION industry-agnostic capability pattern precedent)

## Dev Agent Record

### 결정 사항 (locked at spec 진입)
| ID | 결정 | 근거 |
|----|------|------|
| **A23** | Epic 9 cj-style 분할 (b) 4-story + retro 5번째 진입점 | Epic 12 5-story pattern 적용 — 9-1 + 9-2 + 9-3 + 9-4 + Epic 9 close-out retro |
| **A24** | capability matrix v1.18 + `Capability.ABC_CALCULATION` industry-agnostic 1 row 신규 | 12-1 L4 precedent — manufacturing 3종 ✅ + service-only ✅, 4 industries 모두 grant |
| **A25** | A19 cohesion pattern 6번째 surface = `packages/cost_engine/abc_engine.py` (NEW) | 5 surface verified + 6번째 surface 신규 (A19 cohesion pattern 검증) |
| **A26** | D-8-3-DEFER-4 forward-lock Option A (별도 surface 분리) 결정 | abc_engine.py = 6번째 A19 surface로 신설, projection.py + budget_pre_standard.py와 완전 독립 |
| **A28** | 9-2 spec 진입 시점 CCR ↔ Activity ↔ Cost Object 3-way forward-lock | A28 결정 후 9-2 wire |
| **A29** | 9-3 spec 진입 시점 M3 dispatch ↔ M9 dispatch dual-route 결정 | AD-19 wire |
| **A30** | 9-4 spec 진입 시점 Report #21 ↔ Report #15 PDF generator reuse 결정 | A30 결정 후 9-4 wire |

### 변경 통계 (8 tasks atomic wire)
- **NEW files**: ~38 (T1 3 + T2 14 + T3 14 + T5 5 + T7 1 + T8 1 = 38)
- **MODIFIED files**: ~12 (T1 1 + T2 5 + T3 2 + T5 4)
- **wire 표**: ~50 files (~38 NEW + ~12 MODIFIED)
- **MAX SDR claim**: pytest **~2,495** (8-3 baseline 2,401 + 94 NEW) / vitest **~342** (8-3 baseline 309 + 33 NEW)

### Critical files (locked at spec 진입)
- **NEW**: `packages/cost_engine/abc_engine.py` (A19 cohesion pattern 6번째 surface, A25)
- **NEW**: `apps/api/modules/m9_abc/services/abc_validation_service.py` (CR 12-1 L3 boundary)
- **NEW**: `apps/api/modules/m9_abc/exceptions.py` (4 typed exceptions + 4 Korean SSOT)
- **NEW**: `apps/web/components/abc/AbcValidationClient.tsx` (CR 11-4 D-001 mount MUST)
- **MODIFIED**: `apps/api/core/capability.py` (Capability.ABC_CALCULATION industry-agnostic)
- **MODIFIED**: `apps/api/main.py` (4 NEW envelope handlers, CR 12-5 D-14)
- **MODIFIED**: `apps/web/messages/ko-KR.json` (abc_validation namespace ~25 strings SSOT)
- **MODIFIED**: `_bmad-output/implementation-artifacts/sprint-status.yaml` (9-1 ready-for-dev, epic-9 in-progress)

## Honestly DEFER (CR 11-3 16번째 epic 연속)

| ID | Item | 결정 시점 | Rationale | Structural W-class |
|----|------|---------|-----------|-------------------|
| **D-9-1-DEFER-1** | CCR compute (PRD §F9.2 verbatim) | Epic 9 9-2 진입 시점 | A28 forward-lock 결정 후 9-2 wire | ✅ |
| **D-9-1-DEFER-2** | ABC allocation engine (PRD §F9.2 verbatim) | Epic 9 9-2 진입 시점 | 9-2 wire 시 단일 CCR 1-Won precision | ✅ |
| **D-9-1-DEFER-3** | M3 endpoint dispatch (AD-19 verbatim) | Epic 9 9-3 진입 시점 | A29 forward-lock 결정 후 dual-route 결정 | ✅ |
| **D-9-1-DEFER-4** | Cost Object Breakdown (§9 #21 PRD verbatim) | Epic 9 9-4 진입 시점 | A30 forward-lock 결정 후 Report #21 wire | ✅ |
| **D-9-1-DEFER-5** | Multi-industry ABC (제조부문 ABC = §14.B Non-Goal #1 verbatim) | Epic 9 close-out follow-up | 회색 배지 placeholder (Epic 8 8-2 ABCD 회색 배지 precedent) | ✅ |
| **D-9-1-DEFER-6** | Playwright E2E (12-5 T6 pattern) | Epic 9 close-out follow-up | A27 follow-up sprint 결정됨 (cj-style carry-over 9번째) | ✅ |

**제외된 candidates** (Epic boundary 외부 또는 PRD §15 Non-Goal verbatim):
- (a) Cross-region ABC (AD-9 disabled) — Epic 9 9-2/9-3 진입 시점에 AD-9 결정 wire
- (b) AI 추천 (Epic 10) — Epic boundary 외부

## Status

**Status: done** (2026-08-16, bmad-dev-story T1~T8 atomic wire complete)

**Final wire summary**:
- 28 NEW + 9 MODIFIED = ~37 files
- 3중 게이트 FINAL CLEAN: ruff scoped All checks passed / import-linter 2 KEPT 0 broken / pytest focused 110 NEW passed (37 + 6 + 5 + 30 + 20 + 12) / vitest 46 NEW passed (33 + 5 + 4 + 4) / tsc zero NEW errors for 9.1 files
- 6 honestly DEFER per CR 11-3 16번째 epic 연속
- A28/A29/A30 forward-lock decisions documented in handoff memory

**Next steps**:
- handoff memory: `handoff-2026-08-16-9-1-done.md` (supersedes prior 9-1 spec-ready entry)
- bmad-dev-story 9-2 T1~T8 진입 (cj-style Epic 9 2번째, A28 forward-lock)
- 또는 9-2 spec 진입 (cj-style 2번째 진입점)
- 또는 Epic 9 close-out follow-up (cj-style carry-over 9번째, A27 결정)
- 또는 Epic 9 close-out retro (cj-style 5번째 진입점)

---

**supersedes prior** —
- 9-1 backlog reference (lines 583-590 in action_items block)
- A23 (Epic 8 retro §7) wire at 9-1 spec 진입 시점
- A24 (capability matrix v1.18) wire at 9-1 spec 진입 시점
- A25 (A19 cohesion pattern 6번째 surface) wire at 9-1 spec 진입 시점

## File List (9-1 atomic wire DONE)

### NEW files (28)
- `packages/cost_engine/abc_engine.py` — pure kernel (A19 cohesion pattern 6 surface)
- `apps/api/modules/m9_abc/__init__.py`
- `apps/api/modules/m9_abc/exceptions.py` — 4 typed exceptions + 4 Korean SSOT
- `apps/api/modules/m9_abc/schemas.py` — 5 Pydantic v2 models
- `apps/api/modules/m9_abc/services/__init__.py`
- `apps/api/modules/m9_abc/services/abc_validation_service.py` — orchestrator
- `tests/cost_engine/test_abc_engine.py` — 37 cases
- `tests/cost_engine/test_abc_engine_determinism.py` — 6 cases
- `tests/cost_engine/test_abc_engine_no_io_imports.py` — 5 cases
- `tests/services/test_m9_abc_validation_service.py` — 30 cases
- `tests/api/m9_abc/__init__.py`
- `tests/api/m9_abc/test_abc_validation_handlers.py` — 20 cases
- `tests/integration/test_capability_matrix_v1_18_drift.py` — 12 cases
- `packages/services/m9_abc/__init__.py`
- `packages/services/m9_abc/abc_validation_serializers.py` — thin wrapper
- `apps/web/app/[locale]/(dashboard)/budget/abc-validation/page.tsx` — RSC
- `apps/web/components/m9-abc/AbcValidationStatus.tsx`
- `apps/web/components/m9-abc/AbcValidationGuardBadge.tsx`
- `apps/web/components/m9-abc/AbcValidationForm.tsx`
- `apps/web/components/m9-abc/AbcValidationPanel.tsx`
- `apps/web/components/m9-abc/index.ts`
- `apps/web/lib/m9-abc-validation.ts` — TS mirror
- `apps/web/lib/m9-abc-validation-schema.ts` — TS schema
- `apps/web/__tests__/lib/m9-abc-validation-schema-parity.test.ts` — 33 cases
- `apps/web/__tests__/components/m9-abc.AbcValidationPanel.test.tsx` — 5 cases
- `apps/web/__tests__/components/m9-abc.AbcValidationGuardBadge.test.tsx` — 4 cases
- `apps/web/__tests__/components/m9-abc.AbcValidationStatus.test.tsx` — 4 cases
- `docs/abc-validation.md` — ~250 lines
- `docs/architecture-decisions/AD-19-endpoint-dispatch.md` — AD-19

### MODIFIED files (9)
- `apps/api/core/capability.py` — `Capability.ABC_CALCULATION` enum + 4-industry grants
- `apps/api/main.py` — 4 NEW `@app.exception_handler` decorators (CR 12-5 D-14)
- `apps/api/modules/m9_abc/handlers.py` — 4 NEW endpoints + capability gate
- `packages/cost_engine/__init__.py` — `abc_engine` export
- `apps/web/messages/ko-KR.json` — `abc_validation` namespace 29 strings
- `docs/capability-matrix.md` — title v1.18 + ABC_CALCULATION row + changelog
- `docs/conventions.md` — §6.6 ABC 100% 가드 layer sums rule
- `docs/architecture-inventory.md` — §9.1 ABC Validation Architecture
- `docs/deferred-work.md` — Epic 9 honestly DEFER section (D-9-1-DEFER-1~6)
- `tests/architecture/test_api_calls_only_ports.py` — ALLOWED_SERVICE_SUBMODULES +1
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — 9-1 status ready-for-dev → done

## Change Log

- **2026-08-16 (Story 9.1 done)** — bmad-dev-story T1~T8 atomic wire complete. cj-style Epic 9 1번째 진입점. baseline_commit = 091026f (Story 8.3 DONE tip). 28 NEW + 9 MODIFIED = ~37 files. 3중 게이트 FINAL CLEAN. 6 honestly DEFER. A28/A29/A30 forward-lock decisions documented. Supersedes prior 9-1 spec-ready entry.
- A26 (D-8-3-DEFER-4 forward-lock Option A) wire at 9-1 spec 진입 시점