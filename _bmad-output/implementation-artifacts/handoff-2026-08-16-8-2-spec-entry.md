# Handoff — Story 8.2 bmad-create-story spec entry DONE (2026-08-16)

## Sprint summary

Story 8.2 (Budget vs Actual Variance Table with ABCD Gray Badge) bmad-create-story spec 진입 DONE (backlog → ready-for-dev, cj-style 8번째 epic 연속 검증).

- **baseline_commit**: `2911162` (Story 7.2 follow-up sprint tip = current HEAD)
- **current branch**: `story-7-2-dev-2026-08-15`
- **next step**: `bmad-dev-story 8-2 T1~T8 실행` OR `Epic 8 8-3 spec 진입 (cj-style 3번째)` OR `8-2 honestly DEFER follow-up sprint`

## Spec wire contract (verbatim from PRD §F8.2 + epics.md Story 8.2)

**epics.md Story 8.2 AC verbatim** (lines 978-988):
- 4컬럼 (예산 / 실적 / 차액 / 차이율 %) 표시
- 차이율 ±5% 이상은 노랑, ±10% 이상은 빨강
- 5번째 컬럼 "A×B×C×D 원가 차이 분석"은 회색 배지("2차 예정")로 비활성
- 비고란에 "[NON-GOAL for MVP: A×B×C×D 엔진 미구현]" 표기

**PRD §F8.2 verbatim**: "예산-실적 대조 시 모든 차이 행 + A×B×C×D 미구현 회색 배지."

**PRD §15 NON-GOAL #1 verbatim**: "A×B×C×D 예산 편성 엔진. §부록 B에 명세만 보존, 1차 비구현. trigger: ≥ 5 테넌트 요청 시."

**PRD §10 M8 (b) verbatim**: "시스템은 예산 실적 대조 시 모든 차이 행을 표시하고, A×B×C×D 편성 엔진이 미구현이면 회색 배지로 '2차 예정'을 표시한다."

## 3 user decisions locked (2026-08-16)

1. **Pure kernel surface = `packages/cost_engine/budget_variance.py`** (NEW 분리 surface, AD-5 stdlib-only, A19 cohesion pattern 4번째 — 8-1 budget_period_key.py + 7-1 cvp.py + 7-2 projection.py와 surface 분리):
   - `compute_variance(*, budget_value, actual_value) -> Variance` (5 fields frozen dataclass)
   - `compute_variance_color(*, variance_pct) -> Literal["gray", "yellow", "red"]`
   - `compute_variance_hash(*, variance) -> str` (sha256, V8 determinism)
   - `compute_abcd_disabled_badge(*, variant) -> ABCDDisabledBadge` (NON-GOAL placeholder)

2. **Severity thresholds = ±5% yellow / ±10% red** (PRD §F8.2 verbatim + epics.md AC):
   - `abs(variance_pct) < 5` → `normal` (gray)
   - `5 <= abs(variance_pct) < 10` → `warning` (yellow)
   - `abs(variance_pct) >= 10` → `critical` (red)
   - 부호(sign) 보존 (음수 = 절감, 양수 = 초과)
   - Decimal ROUND_HALF_EVEN (banker's rounding, AD-8 + NFR17)

3. **Capability gate 재사용 = 기존 `Capability.BUDGET_SCENARIO`** (8-1 wire 그대로, 신규 capability 0건 = CR 11-3 즉시 sweep 회피, 산업 agnostic 12-1 L4 + 7-1/7-2 L4 precedent).

## 6 AC + 8 tasks atomic wire

### AC 표
- **AC#1** — 순수 엔진 함수 surface `packages/cost_engine/budget_variance.py` (AD-5 + AD-11 + NFR16 + A19 4번째 분리 surface)
- **AC#2** — Severity thresholds ±5% ±10% + 부호 보존 + ROUND_HALF_EVEN
- **AC#3** — Capability gate + RLS + 4-role + no DB write (READ-ONLY, 200ms P95)
- **AC#4** — Frontend `/budget/variance` RSC + table + 5컬럼 + ko-KR.json SSOT
- **AC#5** — Cross-language drift detector + no DB writes + V8 byte-identical
- **AC#6** — AD-11 layer rule + ALLOWED_SERVICE_SUBMODULES sweep + PDF 보고서 wire + ABCD gray badge placeholder

### Tasks 표 (T1~T8 atomic wire, single sprint commitment)
- **T1** — Pure kernel (Budget variance math surface) — `packages/cost_engine/budget_variance.py` + 35+ pytest cases
- **T2** — Engine purity gate (AD-5 + import-linter + ruff custom rule)
- **T3** — Service layer (thin wrappers + variance fetch + PDF envelope)
- **T4** — HTTP routes + main.py wire + ABCD placeholder
- **T5** — Alembic + RLS (N/A — no schema 변경)
- **T6** — Frontend (RSC + table + 5 components + TS mirror + ko-KR.json)
- **T7** — Tests + docs + 3중 게이트 final clean
- **T8** — Atomic wire close-out (handoff + sprint-status)

### Estimated file inventory
**29 NEW + 15 MODIFIED = 44 files** (~3,000 lines code + ~800 lines tests + ~400 lines docs)

**NEW files** (sample):
1. `packages/cost_engine/budget_variance.py` (~250 lines)
2. `tests/cost_engine/test_budget_variance.py` (~35+ cases)
3. `apps/api/modules/m8_budget/services/budget_variance_service.py` (~200 lines)
4. `apps/web/components/m8-budget/BudgetVarianceTable.tsx` (~250 lines)
5. `apps/web/components/m8-budget/ABCDGrayBadge.tsx` (~60 lines, 회색 배지 placeholder)
6. `apps/web/lib/m8-budget-variance.ts` (~140 lines TS mirror)
7. `apps/web/messages/ko-KR.json` EXTENSION (`budget_variance` namespace 20 strings)
8. `docs/budget-variance-table.md` (~250 lines, 9 sections)

**MODIFIED files** (sample):
1. `apps/api/main.py` — m8_budget router include EXTENSION
2. `apps/api/modules/m8_budget/exceptions.py` EXTENSION — 2 NEW typed exceptions
3. `apps/api/modules/m8_budget/handlers.py` EXTENSION — 1 NEW GET endpoint
4. `tests/architecture/test_api_calls_only_ports.py` — ALLOWED_SERVICE_SUBMODULES sweep EXTENSION
5. `docs/capability-matrix.md` v1.17 EXTENSION (8-1 BUDGET_SCENARIO reuse, 신규 row 0)

## CR lessons applied

- **AD-5 stdlib-only**: pure kernel uses only `decimal, dataclasses, math, hashlib, typing` — verified by `test_budget_variance_no_io_imports.py` AST whitelist
- **AD-11 layer rule**: `apps/api → packages/services/m8_budget/ → packages/cost_engine/budget_variance.py` 단방향 strict
- **AD-15 cross-language**: Decimal-as-string + 4 decimal places ROUND_HALF_EVEN parity with TS decimal.js
- **AD-22 ledger append-only**: variance = READ-ONLY (no DB writes — AD-22 보존)
- **AD-24 period key typed**: `YYYY-MM#B1` validation (8-1 wire + 8-2 reuse)
- **NFR16 V8 determinism**: `compute_variance_hash` 결정론 (8-1 + 7-1 + 7-2 pattern)
- **NFR17 monetary types**: KRW integer BigInteger + Decimal 4 decimal places precision
- **NFR18 ko-KR MVP lock**: 단일 `apps/web/messages/ko-KR.json` (CR 11-4 D-002)
- **CR 1.1 audit invariant**: no DB writes (audit_logs 0건 + budget_scenarios 변경 0건 — read-only 명시)

## 7 Honestly DEFER items (CR 11-3 14번째 epic 연속)

| # | Item | Rationale | Where |
|---|------|-----------|-------|
| 1 | Multi-scenario 비교 (B2, B3, …) | 1차 MVP NON-GOAL #2 §15 verbatim | D-8-2-DEFER-1 (8-3 honestly DEFER (a)) |
| 2 | A×B×C×D 편성 엔진 | 1차 MVP NON-GOAL #1 §15 verbatim (회색 배지 placeholder 명시) | D-8-2-DEFER-2 |
| 3 | Scenario-level grouping (B1 별도 행) | 단일 scenario 1차 MVP (8-1 wire) | D-8-2-DEFER-3 |
| 4 | Year-over-year comparison (전년 동월) | 1차 MVP N/A | D-8-2-DEFER-4 |
| 5 | PDF export (예산-실적 차이 명세서) | Epic 6 M5 PDF generator reuse, 8-3 honestly DEFER | D-8-2-DEFER-5 |
| 6 | Playwright E2E | sprint-scale (12-5 T6 패턴, follow-up sprint) | D-8-2-DEFER-6 |
| 7 | Web Worker for large tables | over-engineering 회피, 1초 한도 대비 5배 여유 | D-8-2-DEFER-7 |

## 3중 게이트 baseline target

- **ruff**: scoped (8-2 surface) All checks passed
- **import-linter**: 2 KEPT 0 broken (cost_engine_forbidden_io + engine_core_to_adapters_forbidden)
- **pytest**: `2256 → ~2351` (+95 NEW) — pre-existing 3 honestly DEFER per A19 carry-over T0 결정
- **vitest**: `197 → ~246` (+49 NEW) — 8-1 budget_scenario 20 + 8-2 budget_variance 49 추가

## Sprint status

**8-2 bmad-create-story spec entry DONE (2026-08-16)**.

- cj-style Epic 8 분할 2번째 진입점 (8-1 done + 8-2 ready-for-dev + 8-3 backlog)
- CR 11-3 14번째 epic 연속 (honest-DEFER discipline + A19 cohesion pattern 4번째 분리 surface)
- sprint-status.yaml: 8-2 added with detailed entry + last_updated: 2026-08-15 → 2026-08-16

## 다음 옵션

- (A) `bmad-dev-story 8-2 T1~T8 실행` (cj-style atomic sprint — 8-1 + 8-2 single sprint wire)
- (B) `Epic 8 8-3 spec 진입` (cj-style 3번째 진입점 — Budget Pre-Standard Cost Preview)
- (C) `8-2 honestly DEFER follow-up sprint` (7 honestly DEFER 통합 wire, cj-style carry-over 8번째)
- (D) 다른 epic 진입 (e.g. Epic 1 1-3 partial follow-up)
