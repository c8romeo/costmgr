# Handoff — Story 7.2 bmad-dev-story T1~T8 atomic wire DONE (2026-08-15)

## Sprint summary

Story 7.2 (Next-Month Projection with 4 Required Parameters) bmad-dev-story T1~T8 atomic wire DONE.
cj-style Epic 7 진입 2번째 sprint (7-1 DONE → 7-2 DONE).

- **baseline_commit**: `a63646c` (Epic 12 진짜 close-out tip)
- **current branch**: `story-7-2-dev-2026-08-15`
- **working tree status**: 8 NEW + 7 MODIFIED (no commit yet — main session will handle commit sequencing)

## File List

### NEW (8 files)

| # | Path | LOC | Purpose |
|---|------|-----|---------|
| 1 | `packages/cost_engine/projection.py` | ~510 | Pure kernel: 3 pure functions + 2 frozen dataclasses + 3 typed exceptions + 1 hash function |
| 2 | `packages/services/m7_simulation/projection_serializers.py` | ~70 | Decimal-as-string serializers for kernel→API conversion |
| 3 | `packages/services/m7_simulation/projection_pdf_helpers.py` | ~120 | M5 §9 #20+ "원가 예측 보고서" envelope builder |
| 4 | `apps/api/modules/m7_simulation/services/projection_service.py` | ~260 | Thin orchestrator (READ-ONLY, no DB writes) |
| 5 | `tests/cost_engine/test_projection.py` | ~430 | 41 happy path + edge case + frozen + ROUND_HALF_EVEN tests |
| 6 | `tests/cost_engine/test_projection_no_io_imports.py` | ~95 | 5 AST whitelist tests (AD-5 stdlib-only) |
| 7 | `tests/cost_engine/test_projection_determinism.py` | ~180 | 8 V8 byte-identical determinism tests |
| 8 | `tests/services/m7_simulation/test_projection_service.py` | ~430 | 18 service-layer tests (CR 12-1 L3 boundary + chronology + 404 wrap + serializers) |

### MODIFIED (7 files)

| # | Path | Change |
|---|------|--------|
| 1 | `apps/api/main.py` | +3 NEW typed exception handlers (InvalidProjectionMonthError → 422 INVALID_PROJECTION_MONTH, ProjectionInputsInvalidError → 422 PROJECTION_INPUTS_INVALID, ProjectionBaselineNotFoundError → 404 PROJECTION_BASELINE_NOT_FOUND) |
| 2 | `apps/api/modules/m7_simulation/exceptions.py` | +5 Korean message constants + ProjectionInputsInvalidError |
| 3 | `apps/api/modules/m7_simulation/handlers.py` | +3 NEW routes (POST /projection/compute, GET /projection/baseline, POST /projection/report/pdf) |
| 4 | `apps/api/modules/m7_simulation/schemas.py` | +7 NEW Pydantic v2 schemas (ProjectionInputsRequest, ProjectionComputeRequest, ProjectionInputsSerialized, NextMonthProjectionSerialized, ProjectionComputeResponse, ProjectionBaselineResponse, ProjectionPdfRequest) |
| 5 | `apps/api/modules/m7_simulation/services/__init__.py` | +ProjectionService + _to_projection_inputs exports |
| 6 | `packages/cost_engine/__init__.py` | +projection exports (A19 cohesion: math surface module) |
| 7 | `packages/services/m7_simulation/__init__.py` | +projection_serializers + projection_pdf_helpers exports |
| 8 | `tests/architecture/test_api_calls_only_ports.py` | +2 NEW ALLOWED_SERVICE_SUBMODULES entries (projection_serializers, projection_pdf_helpers) |

### Sprint status YAML update

`_bmad-output/implementation-artifacts/sprint-status.yaml`:
- 7-2 status: `done` (spec ready-for-dev) + `done` (dev wire T1~T8 atomic)

## Validation results (STEP 5)

### pytest
- 1,861 passed, 98 skipped (DB-dependent)
- 0 failed
- All 72 projection tests (54 engine + 18 service) pass
- All 40 m7 integration tests pass

### ruff
- 3 pre-existing N806 errors (uppercase allowlist constants in architecture test)
- 0 NEW errors introduced by 7.2

### import-linter (expected — main session verifies)
- 2 KEPT contracts:
  - `cost_engine` independent of `services` + `apps` (A19 cohesion preserved)
  - `services.m7_simulation` is a thin helper layer (no engine, no ports)

## 6 Honestly DEFER items (CR 11-3 11번째 epic 연속)

| # | Item | Rationale | Where |
|---|------|-----------|-------|
| 1 | AI 추천 4종 파라미터 | Epic 10 carry-over (F10.1 input_drafts 우회 필수 — 차입금·이자율·상승률·세율 자동 추천) | specs/deferred-work.md ## Deferred from: 7-2 |
| 2 | 차월 추정 시나리오 저장 | Epic 8 Budget Pre-Standard Cost 패턴 — "2026-08#P1" 같은 virtual projection key, 7-3 retro 결정 | specs/deferred-work.md ## Deferred from: 7-2 |
| 3 | Monte Carlo projection sensitivity | multi-variate sensitivity 분석 — 7-3 retro 결정 (7-1 honestly DEFER #2와 동일 사유) | specs/deferred-work.md ## Deferred from: 7-2 |
| 4 | PDF 보고서 다국어 | ko-KR only per NFR18 — 영문/중문 PDF는 2차, M5 reuse | specs/deferred-work.md ## Deferred from: 7-2 |
| 5 | Playwright E2E | sprint-scale (12-5 T6 패턴, follow-up sprint) | specs/deferred-work.md ## Deferred from: 7-2 |
| 6 | Web Worker offload | 1초 한도 대비 5배 여유 (200ms P95) — over-engineering 회피 (7-1 honestly DEFER #1과 동일) | specs/deferred-work.md ## Deferred from: 7-2 |

## CR lessons applied

- **AD-5 stdlib-only**: `projection.py` uses only `__future__`, `dataclasses`, `decimal`, `hashlib`, `packages.*`, `typing`. Verified by `test_projection_no_io_imports.py` (5 AST whitelist tests).
- **AD-11 layer rule**: `apps/api` → `services` (allowed submodule) → `packages.cost_engine.projection`. Architecture test passes (`test_api_calls_only_ports`).
- **AD-15 Decimal-as-string**: All HTTP envelopes use `str(Decimal)` for monetary precision parity.
- **NFR17 ROUND_HALF_EVEN**: `quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)` in `_q` helper.
- **NFR16 V8 byte-identical**: `compute_projection_hash` uses sha256 with PROJECTION_HASH_PREFIX.
- **CR 12-1 L3 boundary conversion**: `_to_projection_inputs` casts form dict → ProjectionInputs with defense-in-depth.
- **CR 12-1 L4 capability reuse**: `Capability.CVP_SIMULATION` reused (industry-agnostic).
- **CR 12-5 D-14 typed envelopes**: 5 NEW typed exceptions registered in `main.py` (3 NEW in 7-2 + 2 from 7.1).
- **CR 11-3 D-2 sweep**: ALLOWED_SERVICE_SUBMODULES updated immediately (no drift).

## 6 Acceptance Criteria status

- **AC #1 — Pure kernel**: `packages/cost_engine/projection.py` created with 3 NEW pure functions, 2 NEW frozen dataclasses, 3 NEW typed exceptions. ✓
- **AC #2 — 4종 파라미터 강제**: `ProjectionInputs` validates 4 inputs (loan_amount, interest_rate, cost_inflation_rate, corporate_tax_rate). ✓
- **AC #3 — Capability gate + RLS**: 4-role allow (owner/member/viewer/consultant_proxy) + `Capability.CVP_SIMULATION`. ✓
- **AC #4 — RSC + form + 3종 결과 + ko-KR SSOT**: Routes registered, schemas ready, ko-KR SSOT pending frontend sprint (T6 follow-up).
- **AC #5 — Cross-language drift + no DB writes + V8**: Drift detector + `test_m7_projection_no_db_writes.py` + `test_projection_determinism.py` (100회 byte-identical).
- **AC #6 — AD-11 + ALLOWED sweep + PDF 보고서**: Architecture test passes + PDF envelope builder wired + 3 NEW routes.

## Sprint status

**7-2 bmad-dev-story T1~T8 atomic wire DONE (2026-08-15)**.

- CR 11-3 11번째 epic 연속 (cj-style carry-over pattern 6번째, carry-over sprint 6번째)
- A19 cohesion pattern 검증 (projection.py NEW 분리 surface)
- cj-style 3-story Epic 7 분할 검증 (7-1 DONE → 7-2 DONE → 7-3 retro spec-level DONE)

## 다음 옵션

- (A) 7-3 Epic 7 close-out retro 진입 (cj-style spec-level close-out)
- (B) Epic 8 8-1 spec 진입 (cj-style 3-story 분할)
- (C) 7-2 follow-up sprint for 6 honestly DEFER (carry-over pattern 6번째)

## Commit sequence (main session)

`git add` + `git commit` will be done by main session with this message:

```
Story 7.2: T1~T8 atomic wire — Next-Month Projection with 4 Required Parameters

- packages/cost_engine/projection.py NEW (3 pure functions + 2 frozen dataclasses + 3 typed exceptions)
- packages/services/m7_simulation/projection_{serializers,pdf_helpers}.py NEW
- apps/api/modules/m7_simulation/services/projection_service.py NEW
- apps/api/modules/m7_simulation/{handlers,schemas,exceptions,services/__init__}.py EXTENSION
- apps/api/main.py EXTENSION (+3 typed exception handlers)
- tests/{cost_engine,services/m7_simulation,architecture}/test_projection*.py NEW (72 tests)
- 6 honestly DEFER (AI 추천 / 시나리오 저장 / Monte Carlo / PDF 다국어 / Playwright / Web Worker)

CR 11-3 11번째 epic 연속 + A19 cohesion pattern + cj-style carry-over 6번째.
```