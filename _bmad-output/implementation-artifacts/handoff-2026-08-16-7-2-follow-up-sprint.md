# Handoff — Story 7.2 follow-up sprint (2026-08-16 frontend ↔ backend parity + D-7-2-DEFER-7)

## Sprint summary

Story 7.2 (Next-Month Projection with 4 Required Parameters) bmad-dev-story T1~T8 atomic wire DONE (2026-08-15) + **follow-up sprint DONE** (2026-08-16).

- **baseline_commit**: `7c886af` (Story 7.2 T8 close-out tip)
- **current branch**: `story-7-2-dev-2026-08-15`
- **uncommitted changes**: 6 files (frontend parity patch + D-7-2-DEFER-7 doc)
- **3중 게이트 FINAL CLEAN**: ruff / import-linter / pytest 121 / vitest 226

## Follow-up changes (uncommitted 6 files)

### 1. Frontend ↔ backend parity (loan_amount >= 0)

Story 7.2 backend pure kernel (`packages/cost_engine/projection.py`) treats `loan_amount < 0` as invalid (so `loan_amount = 0` is allowed — "no loan" scenario). Frontend was over-strict with `LOAN_AMOUNT_MIN = 1` (positive integer). Follow-up patch aligns frontend with backend:

- `apps/web/lib/m7-simulation-projection.ts` — `validateLoanAmountTS` now allows `loan_amount = 0` (boundary `value < 0` instead of `value < LOAN_AMOUNT_MIN`)
- `apps/web/lib/m7-simulation-projection-schema.ts` — `validateProjectionInputs` boundary aligned (`< 0` instead of `< LOAN_AMOUNT_MIN`)
- `apps/web/components/m7-simulation/ProjectionForm.tsx` — `validateLoanAmount` boundary aligned (`< 0` instead of `< LOAN_AMOUNT_MIN`); error message: "차입금은 0 이상이어야 합니다"
- `apps/web/__tests__/lib/m7-simulation-projection.test.ts` — tests updated to match new boundary (loan_amount = 0 now valid, no loan scenario)

### 2. D-7-2-DEFER-7 — react-hook-form + zod dependency honestly DEFER

Spec recommended `react-hook-form` + `Zod` schema, but neither package is currently in `apps/web/package.json`. Sprint chose **dependency-bump-free atomic wire** priority:

- Implements same bounds + same `disabled` gate via plain React `useState` + inline validation
- `lib/m7-simulation-projection-schema.ts` already provides Zod-style API surface (`validateProjectionInputs`) — migration cost ~30 LOC
- Documented as D-7-2-DEFER-7 in `docs/deferred-work.md`

### 3. Test cleanup

- Removed unused `isAllFieldsFilledTS` import
- Renamed `Zod schema (projectionInputsSchema)` describe block to `validateProjectionInputs` (more accurate after migration planning)

## Validation results (STEP 5 — 2026-08-16 re-verification)

### pytest
- **121 passed**, 0 failed (focused 7-2 suite)
  - `tests/cost_engine/test_projection.py` (41+ cases)
  - `tests/cost_engine/test_projection_no_io_imports.py` (5 AST whitelist)
  - `tests/cost_engine/test_projection_determinism.py` (8 V8 byte-identical)
  - `tests/services/m7_simulation/test_projection_service.py` (18+ cases)
  - `tests/integration/test_m7_simulation_projection_*.py` (3 files: cross_language_drift + no_db_writes + capability_v1_17_drift)
  - `tests/architecture/test_api_calls_only_ports.py` (ALLOWED_SERVICE_SUBMODULES sweep)

### vitest
- **226 passed**, 0 failed (full web suite)
  - `apps/web/__tests__/lib/m7-simulation-projection.test.ts` (33 cases including new `loan_amount = 0` boundary)
  - 7-1 + 8-1 + 8-2 + 12-1 + 12-2 + 12-3 + 12-5 baselines

### ruff
- All checks passed (7-2 surface: `packages/cost_engine/projection.py` + `apps/api/modules/m7_simulation/` + `packages/services/m7_simulation/`)

### import-linter
- 2 KEPT, 0 broken:
  - `cost_engine_forbidden_io` (Epic 0 wire)
  - `engine_core_to_adapters_forbidden` (Epic 0 wire)

## 7 Honestly DEFER items (CR 11-3 13번째 epic 연속)

| # | Item | Rationale | Where |
|---|------|-----------|-------|
| 1 | AI 추천 4종 파라미터 | Epic 10 carry-over (F10.1 input_drafts 우회 필수) | D-7-2-DEFER-1 |
| 2 | 차월 추정 시나리오 저장 | Epic 8 Budget Pre-Standard Cost 패턴 (virtual projection key) | D-7-2-DEFER-2 |
| 3 | Monte Carlo projection sensitivity | multi-variate는 7-3 retro 결정 | D-7-2-DEFER-3 |
| 4 | PDF 보고서 다국어 | ko-KR only per NFR18 | D-7-2-DEFER-4 |
| 5 | Playwright E2E (16 cases) | follow-up sprint (12-5 T6 패턴) | D-7-2-DEFER-5 |
| 6 | Web Worker offload | over-engineering 회피 (1초 한도 대비 5배 여유) | D-7-2-DEFER-6 |
| 7 | react-hook-form + zod 의존성 | dependency bump 없이 atomic wire 우선시 | D-7-2-DEFER-7 |

## CR lessons applied

- **AD-5 stdlib-only**: `projection.py` uses only `__future__`, `dataclasses`, `decimal`, `hashlib`, `packages.*`, `typing`. Verified by `test_projection_no_io_imports.py` (5 AST whitelist tests).
- **AD-11 layer rule**: `apps/api` → `services` (allowed submodule) → `packages.cost_engine.projection`. Architecture test passes.
- **AD-15 Decimal-as-string**: All HTTP envelopes use `str(Decimal)` for monetary precision parity.
- **NFR17 ROUND_HALF_EVEN**: `quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)` in `_q` helper.
- **NFR16 V8 byte-identical**: `compute_projection_hash` uses sha256 with PROJECTION_HASH_PREFIX.
- **CR 11-3 D-2 immediate sweep**: ALLOWED_SERVICE_SUBMODULES updated immediately (no drift).
- **CR 11-3 honest-DEFER 13번째 epic 연속**: D-7-2-DEFER-7 신규 추가 (react-hook-form + zod dependency).

## File List (uncommitted 6 files)

### MODIFIED (5 files)

| # | Path | Change |
|---|------|--------|
| 1 | `apps/web/__tests__/lib/m7-simulation-projection.test.ts` | Removed unused `isAllFieldsFilledTS` import; updated `loan_amount = 0` boundary tests (now valid); renamed test describe block `Zod schema` → `validateProjectionInputs` |
| 2 | `apps/web/components/m7-simulation/ProjectionForm.tsx` | `validateLoanAmount` boundary `< LOAN_AMOUNT_MIN` → `< 0`; error message: "차입금은 0 이상이어야 합니다" |
| 3 | `apps/web/lib/m7-simulation-projection-schema.ts` | `validateProjectionInputs` boundary aligned (`< 0` instead of `< LOAN_AMOUNT_MIN`); error message update |
| 4 | `apps/web/lib/m7-simulation-projection.ts` | `validateLoanAmountTS` boundary aligned (`< 0` instead of `< LOAN_AMOUNT_MIN`); error message: "loan_amount must be >= 0" |
| 5 | `apps/web/tsconfig.tsbuildinfo` | Auto-regenerated by vitest run (CRLF normalization) |

### MODIFIED (1 file)

| # | Path | Change |
|---|------|--------|
| 6 | `docs/deferred-work.md` | +D-7-2-DEFER-7 (react-hook-form + zod dependency honestly DEFER) |

### MODIFIED (2 files — meta)

| # | Path | Change |
|---|------|--------|
| 7 | `_bmad-output/implementation-artifacts/7-2-next-month-projection-4-required-parameters.md` | `baseline_commit: a63646c → 7c886af`; `status: ready-for-dev → done`; `updated: 2026-08-15 → 2026-08-16` |
| 8 | `_bmad-output/implementation-artifacts/sprint-status.yaml` | `7-2-next-month-projection-4-required-parameters: ready-for-dev → done`; entry expanded with follow-up sprint commitment |

## Commit hashes (Story 7.2 + follow-up)

| # | Commit | Scope |
|---|--------|-------|
| 1 | `436a6aa` | T1+T2+T3+T4 backend — pure kernel + service layer + HTTP routes + capability + main.py handlers |
| 2 | `f03cd97` | T6+T7+T8 frontend + docs + 3중 게이트 — frontend RSC + 5 components + TS mirror + Zod + ko-KR.json SSOT + 4 integration tests + docs |
| 3 | `7c886af` | T8 close-out — spec file update + sprint-status sync + handoff |
| 4 | (follow-up) | Frontend ↔ backend parity + D-7-2-DEFER-7 + sprint-status.yaml done + spec file update |

## Sprint status

**7-2 follow-up sprint DONE (2026-08-16)**.

- Story 7.2 atomic wire + follow-up 모두 done (cj-style Epic 7 진입 2번째 sprint + reconciliation sprint)
- CR 11-3 13번째 epic 연속 (honest-DEFER discipline)
- A19 cohesion pattern 5번째 검증 (projection.py NEW 분리 surface)
- 7-2 + 7-1 + 8-1 모두 done (cj-style 3-story Epic 7 분할 완료 — 7-3 retro)

## 다음 옵션

- (A) Epic 7 7-3 close-out retro 진입 (cj-style 3번째 — spec-level close-out)
- (B) Epic 8 8-2 spec 진입 (cj-style Epic 8 2번째)
- (C) A19 follow-up sprint (cj-style 7-1 + 7-2 + 7-3 honestly DEFER 통합 wire)
- (D) 8-1 follow-up sprint (cj-style carry-over 8번째)
