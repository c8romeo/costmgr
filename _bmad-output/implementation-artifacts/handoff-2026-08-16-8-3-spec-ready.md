# handoff — 2026-08-16 — Story 8.3 spec-ready

## 8.3 (Epic 8 Budget vs Actual 3번째 진입점) bmad-create-story spec 진입 DONE

**baseline_commit** = `091026f` (Story 8.2 DONE tip = current HEAD).
**status**: `8-3-budget-pre-standard-cost-preview: backlog → ready-for-dev`

**Why:** cj-style 3-story 분할 9번째 epic 연속 검증 (Epic 4·5·6·11·12 + Epic 11/12 carry-over + Epic 7·8). 8-3은 epics.md SSOT (lines 990-1000) + 8-1 sprint-up 결정 verbatim ("Pre-standard cost preview `engine_type='budget'` (Story 8-3 결정, cj-style 3번째)") + 8-2 honestly DEFER #5 PDF export 해소의 교차점.

## 3 user decisions locked (2026-08-16)

1. **Pure kernel surface = `packages/cost_engine/budget_pre_standard.py`** (NEW 분리 surface, AD-5 stdlib-only, A19 cohesion pattern 5번째 분리 surface — 8-1 budget_period_key.py + 8-2 budget_variance.py + 7-1 cvp.py + 7-2 projection.py 와 surface 분리). **2 NEW pure functions** (`compute_pre_standard_cost` + `compute_pre_standard_hash`) + **1 NEW frozen dataclass** (`PreStandardCost` with 7 fields).

2. **Pre-Standard Cost Preview primary scope + §9 #20 PDF export secondary scope**:
   - **Primary** = epics.md SSOT verbatim: `fiscal_period_snapshots.engine_type='budget'` Alembic 0027 + `state='verified'` 초기 저장 + `result_hash` V8 determinism + `material_cost + labor_cost + overhead_cost + manufacturing_cost` 4-column reuse + `inventory_adjustment = 0`.
   - **Secondary** = 8-2 honestly DEFER #5 해소: `/variance/{period_key}/pdf` endpoint wire + `VariancePdfButton.tsx` disabled → enabled + Epic 6 M5 PDF generator reuse (READ-ONLY envelope, ko-KR only per NFR18).

3. **Capability gate 재사용 = 기존 `Capability.BUDGET_SCENARIO`** (8-1 + 8-2 wire 그대로, 12-1 L4 industry-agnostic — manufacturing 3종 ✅ + service-only ✅). **신규 capability 추가 0건** (CR 11-3 즉시 sweep 회피).

## wire 표 (8-3 dev-story T1~T8 진입 시)

- **Backend NEW** (12 files): `packages/cost_engine/budget_pre_standard.py` (pure kernel, ~280 lines) + `packages/services/m8_budget/budget_pre_standard_serializers.py` + `budget_pre_standard_pdf_helpers.py` (8-2 PDF envelope SSOT) + `apps/api/modules/m8_budget/services/budget_pre_standard_service.py` + `schemas_pre_standard.py` + 4 NEW typed exceptions (`InvalidPreStandardInputError` 422 + `PreStandardSnapshotNotFoundError` 404 + `PreStandardAlreadyExistsError` 409 + `BudgetVariancePdfNotReadyError` 425) + `apps/api/alembic/versions/0027_budget_pre_standard.py` (CHECK EXTENSION 1→4 values + `idx_fiscal_period_snapshots_engine_type`).
- **Backend MODIFIED** (8 files): `apps/api/main.py` (4 NEW envelope handlers CR 12-5 D-14) + `apps/api/modules/m8_budget/exceptions.py` + `handlers.py` (3 endpoints) + `services/budget_variance_service.py` (`generate_budget_variance_pdf()` placeholder wire) + `services/__init__.py` + `__init__.py` + `tests/architecture/test_api_calls_only_ports.py` (ALLOWED_SERVICE_SUBMODULES +2 sweep, CR 11-3 D-2) + `tests/integration/test_ko_kr_json_ssot.py` (`budget_pre_standard` namespace 정합, CR 12-1 P-015).
- **Frontend NEW** (10 files): `apps/web/app/[locale]/(dashboard)/budget/pre-standard/{layout,page}.tsx` (RSC) + `apps/web/components/m8-budget/{BudgetPreStandardPreview,PreStandardCostTable,PreStandardPdfButton,PreStandardHashBadge}.tsx` (4 NEW) + `apps/web/lib/m8-budget-pre-standard.ts` (TS mirror) + `m8-budget-pre-standard-schema.ts` (Zod) + `m8-budget-pre-standard-bench.ts` (perf benchmark) + `m8-budget-pre-standard.test.ts` (TS mirror parity) + 4 NEW `*.test.tsx` 파일.
- **Frontend MODIFIED** (4 files): `apps/web/messages/ko-KR.json` (NEW `budget_pre_standard` namespace ~18 strings SSOT, CR 11-4 D-002) + `apps/web/lib/menu-config.ts` (sidebar nav entry) + `apps/web/components/m8-budget/VariancePdfButton.tsx` EXTENSION (8-2 wire EXTENSION — disabled → enabled) + `apps/web/components/m8-budget/index.ts` (barrel export).
- **Docs** (5 files): `docs/budget-pre-standard-cost-preview.md` (NEW, ~280 lines, 10 sections) + `docs/capability-matrix.md` v1.17 EXTENSION (8-1 BUDGET_SCENARIO row reuse, 신규 0) + `docs/conventions.md` §AD-11 EXTENSION + `docs/architecture-inventory.md` EXTENSION + `docs/deferred-work.md` EXTENSION (8 honestly DEFER).

**Total**: 30 NEW + 18 MODIFIED = 48 files (~3,200 lines code + ~900 lines tests + ~400 lines docs).

## 3중 게이트 FINAL CLEAN 목표 (cj-style 9번째 epic + carry-over 9번째 연속)

- **ruff scoped** (8-3 surface: `packages/cost_engine/budget_pre_standard.py` + `apps/api/modules/m8_budget/` + `packages/services/m8_budget/` + `apps/web/components/m8-budget/`): All checks passed
- **import-linter 2 KEPT 0 broken** (ALLOWED_SERVICE_SUBMODULES `m8_budget.budget_pre_standard_serializers` + `budget_pre_standard_pdf_helpers` 추가, AD-11 + AD-22 + cost_engine_forbidden_io + engine_core_to_adapters_forbidden 모두 유지)
- **pytest baseline + ~50 NEW = 2351 + ~50 = ~2401 passed + 127 skipped + 0 failed** (3 pre-existing failures honestly DEFER per A19 carry-over T0 결정, 8-3 추가 회귀 0)
- **vitest 246 baseline + ~40 NEW = ~286 passed** (8-1 budget_scenario 20 + 8-2 budget_variance 49 + 8-3 budget_pre_standard 40 추가)

## 8 honestly DEFER per CR 11-3 15번째 epic 연속 검증

| # | Item | Rationale |
|---|------|-----------|
| 1 | Multi-scenario B2/B3 pre-standard cost preview | 1차 MVP §15 NON-GOAL #2 verbatim — Epic 8 close-out retro §7 honestly DEFER (≥5 테넌트 trigger) |
| 2 | A×B×C×D 편성 엔진 | 1차 MVP §15 NON-GOAL #1 verbatim — 8-2 회색 배지 placeholder only |
| 3 | AI 추천 예산 시나리오 (F10.1 input_drafts) | Epic 10 carry-over, 8-3 scope OUTSIDE |
| 4 | Pre-standard cost ↔ Projection 통합 | 7-2 honestly DEFER (b) 결정 + A8 inline projection deprecate 후 fold-in |
| 5 | Year-over-year pre-standard cost comparison | 1차 MVP N/A, 2차 PRD |
| 6 | Multi-currency USD 환산 | Epic 6 6-2 wire 결정 보존 |
| 7 | Playwright E2E | 12-5 T6 패턴 follow-up sprint (8-1/8-2 honestly DEFER mirror) |
| 8 | Web Worker for large previews | over-engineering 회피, 7-1/8-1/8-2 honestly DEFER mirror |

## CR carry-over summary

- **CR 11-3 lessons carry** (15번째 epic 연속): ALLOWED_SERVICE_SUBMODULES 즉시 sweep (D-2) + ruff auto-fix sweep (D-3) + SDR separate line parser (CR 11-2) + `def test_+asyncio.run` (CR 4-3)
- **CR 11-4 lessons carry**: D-001 (page.tsx actual mount MUST) + D-002 (단일 `apps/web/messages/ko-KR.json` only) + D-005 (TS mirror unknown state reject) + P-015 (ko-KR.json SSOT drift detector)
- **CR 12-1 lessons continue**: L3 (`_to_pre_standard_cost_state` ORM→kernel boundary) + L4 (BUDGET_SCENARIO industry-agnostic reuse)
- **CR 12-5 lessons continue**: D-13 (cross-language drift detector 10+ vectors) + D-14 (4 NEW typed exception main.py handlers) + L3 (3-layer defense route|service|audit for destructive INSERT) + L4 (honest-DEFER discipline)
- **A19 lessons carry**: math surface migration pattern (CR A19 NEW) + `packages/cost_engine/budget_pre_standard.py` SSOT (A19 cohesion pattern 5번째 검증)

## 다음 단계 옵션

1. **`bmad-dev-story 8-3 T1~T8 실행`** (cj-style Epic 8 3번째 atomic wire) — **기본 권장**
2. `Epic 8 close-out retro 진입` (cj-style 4번째 진입점, A19~A22 결정)
3. `8-3 follow-up sprint` for 8 honestly DEFER (cj-style carry-over 9번째)
4. `Epic 9 spec 진입` (cj-style Epic 9 1번째)

**supersedes** prior `8-2-done` handoff status (8-3 spec 진입으로 Epic 8 진행 중).
