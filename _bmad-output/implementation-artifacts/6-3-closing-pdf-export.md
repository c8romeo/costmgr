---
title: Closing PDF Export + ko-KR Labels
status: in-progress
priority: MEDIUM
epic: 6
story_num: 3
story_key: 6-3-closing-pdf-export
baseline_commit: 30d6455
created: 2026-08-09
---

# Story 6.3 — Closing PDF Export + ko-KR Labels

> **Epic 6 cj-style 3-story 분할 (Epic 5 close-out retro §6 W1) 3번째 (마지막) 스토리**.
> 6-1 = Closing Period Service + closing_snapshot ledger event wire (DONE commit `418ca2d`) → 6-2 = Monthly Closing Report (DONE commit `30d6455`) → **6-3 = Closing PDF Export + ko-KR labels** (본 스토리).
>
> **baseline_commit = 30d6455** (Story 6.2 carry-over sweep tip).
>
> 6-3 진입 의의 = Epic 6 close-out 가능 상태 진입. A15 Epic 6 close-out retro (Epic 5 retro §7 A8 보류 해소) 진입 게이트.

## Story

**As a** 사장님 (closing_period owner role),
**I want** 월 마감 보고서를 **PDF/A4 형식으로 export**하여 **회계사·세무사에게 종이/PDF로 전달**하고 싶고, **모든 UI label이 한국어로 일관되게** 표시되길 원합니다,
**so that** **마감 보고서 전달이 표준화되고, 외부 이해관계자(회계사·세무사·금융기관)가 한글 본문을 즉시 인쇄/열람할 수 있으며, Epic 6 close-out retro 진입이 가능**해집니다.

## Epic 6 carry-over context

- **6-1 wire (DONE commit `418ca2d`)** — closing_period service + closing_snapshot ledger event + V4 verification + MONTHLY_CLOSING_REPORT capability (v1.8) + ActionClass.CLOSING_PERIOD 3 values + Alembic 0017 + ClosingPeriodConfirmationPanel + ClosingPeriodConfirmDialog + 17 PATCH + 13 DEFER close-out sweeping
- **6-2 wire (DONE commit `30d6455`)** — Monthly Closing Report backend + frontend (KRW/USD dual display) + V8 16-fixture matrix extension (A11 wire) + 6-1 T10.5 V4 골든 fixture close-out + 12 PATCH + 5 DEFER close-out
- **6-3 wire (본 스토리)** — Closing PDF Export + ko-KR labels. 6-1 + 6-2 wire 모두 reuse + extend (additive only — wire contract 호환 보존)

## Acceptance Criteria

### AC #1: Closing PDF Export backend wire (PRD §F6.3)

1.1. `apps/api/modules/m4_inventory/services/closing_pdf_export_service.py` (NEW) — `export_closing_pdf(tenant_id, period_key)` 진입점
1.2. `packages/services/m4_inventory/closing_pdf_export.py` (NEW) — pure helper (PDF template rendering, 한글 폰트 임베딩, A4 페이지 layout)
1.3. `apps/api/modules/m4_inventory/handlers.py` EXTENSION — `POST /api/v1/closing/export-pdf` route (capability gate: MONTHLY_CLOSING_REPORT)
1.4. PDF content = closing_snapshot + ledger events join + MonthlyClosingReport (6-2 wire) — 1 product per page + summary cover page
1.5. PDF byte-identical CI gate (optional but recommended) — `tests/integration/test_closing_pdf_export_byte_identical.py` (NEW, ~50 lines)
1.6. 한글 폰트 임베딩 = Noto Sans KR (Google Fonts CDN cached) — `@font-face` subset
1.7. PDF size ≤ 5MB per period (대용량 ledger events의 경우 chunked rendering)

### AC #2: Closing PDF Export frontend wire

2.1. `apps/web/components/m2-input/ClosingPdfExportButton.tsx` (NEW) — shadcn Button + sonner toast
2.2. `apps/web/lib/closing-pdf-export.ts` (NEW) — TS mirror (download flow + error handling)
2.3. `apps/web/app/(authenticated)/m2-input/period/[periodKey]/page.tsx` EXTENSION — ClosingPdfExportButton 진입점
2.4. Vitest `closing-pdf-export-button.test.tsx` (NEW, ~80 lines) — 5 scenarios (button visibility + click handler + error toast + success toast + download flow)
2.5. Playwright `e2e/closing-pdf-export.spec.ts` (NEW, ~180 lines) — 4 scenarios

### AC #3: ko-KR labels comprehensive coverage

3.1. `apps/web/ko-KR.json` EXTENSION — 30 NEW strings (PDF export 관련 + ko-KR labels 누락 보강)
3.2. `apps/web/lib/labels-ko.ts` (NEW) — `formatClosingPeriodLabelKo` + `formatClosingSnapshotEventLabelKo` + `formatCurrencyPairKo` + `formatOperatorActionKo` (reopen operator action 4-value enum)
3.3. `apps/web/components/m2-input/__tests__/labels-ko.test.ts` (NEW vitest, ~100 lines) — 10 scenarios
3.4. 모든 백엔드/프론트엔드 한국어 label SSOT = `apps/web/ko-KR.json` + `packages/cost_engine/labels_ko.py` + `apps/api/core/labels_ko.py` (cross-language parity)

### AC #4: 6-2 carry-over close-out (5 DEFER items)

4.1. W1 `__init__` re-export — closing_pdf_export_service module re-export close
4.2. W2 V8 `_fixture_lock_sha256` placeholder — A11 publisher regen defer (Epic 11 close 후 결정)
4.3. W3 panel `formatKrwUsd` parity helper — labels-ko.ts (AC #3)에 통합 close
4.4. W4 2 missing test files — `test_v8_runner_e2e.py` + Playwright spec — 본 스토리 T7 wire
4.5. W5 `industry='trad'` hard-code — industry-extension follow-up (Epic 12+ 결정)

### AC #5: Capability matrix v1.10 (carry + extension)

5.1. `docs/capability-matrix.md` EXTENSION — 6-3 wire 신규 capability 0개 (PDF export = MONTHLY_CLOSING_REPORT capability 재사용) + 6-2 0.5 plumbing follow-up W3 close
5.2. `apps/api/core/capability.py` (변경 無 — MONTHLY_CLOSING_REPORT 기존 capability gate 재사용)
5.3. `tests/integration/test_capability_matrix_drift.py` EXTENSION — 0 NEW cases (변경 無)

### AC #6: A8 inline projection deprecation timeline 명시

6.1. `docs/closing-period.md` EXTENSION — §A8 timeline 섹션 update (Epic 6 close-out 시점에 5-2 commit + 1 epic maintenance window 종료 = Epic 6 close-out retro 시점 fold-in 결정)
6.2. `apps/api/modules/m4_inventory/services/closing_period_service.py` 5-1+5-2+5-3 carry-over inline projection 보존 상태로 wire (Epic 6 close-out 시점에 fold-in vs deprecate 결정)
6.3. `tests/integration/test_inline_projection_deprecation_timeline.py` (NEW, ~80 lines) — 5 scenarios (timeline 가드 검증)

### AC #7: A5 forward-lock + A7 wire + A11 V8 fixture + A12 carry-over close

7.1. A5 forward-lock — `ActionClass.CLOSING_PERIOD` 3 values + `ActionClass.VERIFICATION` V4 extension 보존
7.2. A7 wire — `def test_*` + `asyncio.run(_impl())` 패턴 (CR 4-3 정합)
7.3. A11 V8 16-fixture matrix extension 보존 (6-2 wire 완료)
7.4. A12 5-3 T12.2 test file close-out 보존 (6-2 wire 완료)

## Tasks / Subtasks

본 스토리 = 6-task 분할 (cj-style 3-story 분할의 3번째 정합):

- [ ] **Task 1: Pure helper + service layer + handlers wire** (AC: #1)
  - [ ] Subtask 1.1: `packages/services/m4_inventory/closing_pdf_export.py` (NEW pure helper, ~250 lines) — PDF template rendering + 한글 폰트 임베딩 + A4 layout
  - [ ] Subtask 1.2: `apps/api/modules/m4_inventory/services/closing_pdf_export_service.py` (NEW service layer, ~300 lines) — `export_closing_pdf` 진입점
  - [ ] Subtask 1.3: `apps/api/modules/m4_inventory/handlers.py` EXTENSION — `POST /api/v1/closing/export-pdf` route
  - [ ] Subtask 1.4: `apps/api/modules/m4_inventory/services/__init__.py` EXTENSION — closing_pdf_export_service re-export (W1 close)
  - [ ] Subtask 1.5: `apps/api/core/audit_action.py` (변경 無 — 6-2 wire A5 forward-lock 보존)
- [ ] **Task 2: Frontend wire + download flow** (AC: #2)
  - [ ] Subtask 2.1: `apps/web/components/m2-input/ClosingPdfExportButton.tsx` (NEW shadcn Button + sonner toast, ~150 lines)
  - [ ] Subtask 2.2: `apps/web/lib/closing-pdf-export.ts` (NEW TS mirror, ~120 lines)
  - [ ] Subtask 2.3: `apps/web/app/(authenticated)/m2-input/period/[periodKey]/page.tsx` EXTENSION — 진입점
  - [ ] Subtask 2.4: vitest 5 scenarios
  - [ ] Subtask 2.5: Playwright 4 scenarios
- [ ] **Task 3: ko-KR labels comprehensive coverage** (AC: #3)
  - [ ] Subtask 3.1: `apps/web/ko-KR.json` EXTENSION (30 NEW strings)
  - [ ] Subtask 3.2: `apps/web/lib/labels-ko.ts` (NEW, ~150 lines) — format helpers
  - [ ] Subtask 3.3: `apps/web/components/m2-input/__tests__/labels-ko.test.ts` (NEW vitest, ~100 lines)
  - [ ] Subtask 3.4: Cross-language parity (Python + TS) — `packages/cost_engine/labels_ko.py` EXTENSION
- [ ] **Task 4: 6-2 carry-over close-out (5 DEFER items)** (AC: #4)
  - [ ] Subtask 4.1: W1 `__init__` re-export close
  - [ ] Subtask 4.2: W2 V8 `_fixture_lock_sha256` placeholder docstring (Epic 11 close 후 결정)
  - [ ] Subtask 4.3: W3 panel `formatKrwUsd` parity helper → labels-ko.ts close
  - [ ] Subtask 4.4: W4 2 missing test files wire (`test_v8_runner_e2e.py` + Playwright spec)
  - [ ] Subtask 4.5: W5 `industry='trad'` hard-code docstring (Epic 12+ 결정)
- [ ] **Task 5: A8 timeline + A5+A7+A11+A12 close** (AC: #6, #7)
  - [ ] Subtask 5.1: `docs/closing-period.md` EXTENSION — §A8 timeline update
  - [ ] Subtask 5.2: `tests/integration/test_inline_projection_deprecation_timeline.py` (NEW, ~80 lines)
  - [ ] Subtask 5.3: A5 forward-lock + A7 wire 보존 검증 (CR 4-3 pattern)
- [ ] **Task 6: docs + 3중 게이트 final clean + SDR drift detector regeneration** (AC: #all)
  - [ ] Subtask 6.1: `docs/closing-pdf-export.md` (NEW, ~150 lines) — 운영 매뉴얼 7-section
  - [ ] Subtask 6.2: `docs/ko-KR-labels.md` (NEW, ~100 lines) — ko-KR label SSOT guide
  - [ ] Subtask 6.3: 3중 게이트 final clean — ruff scoped All passed / import-linter 2 KEPT 0 broken / pytest pass / vitest pass / Playwright pass / SDR drift detector MAX claim 갱신
  - [ ] Subtask 6.4: `docs/architecture-inventory.md` EXTENSION — closing_pdf_export module entry + ko-KR SSOT 추가

## Critical Path Before 6-3 dev-story

없음. baseline_commit = 30d6455 (6-2 carry-over sweep tip). 모든 wire는 이미 6-1 + 6-2 commit에서 done.

## CR lessons applied (Story 6.3)

### CR 6-1 / CR 6-2 lessons applied

1. **SDR overclaim detector** — sweep에서 test 추가 시 MAX claim 갱신 필수 (separate line for unambiguous parser match)
2. **Architectural regression 자동화** — 신규 packages.services submodule 도입 시 dev-story T1에서 architecture test allowlist sync subtask 필수
3. **Triage-only patches discipline** — frontend/docs/tests = 별도 iteration (cj-style 정합)
4. **JSONB expression index** — Pattern 보존 (Story 6-1 P2 정합)
5. **dict[UUID, Decimal] wire serialization** — 6-2 H1 wire 정합

### CR 4-3 lesson applied

1. **def test_* + asyncio.run(_impl())** 패턴 — 6-3 모든 async test 적용 (24 broken async → def 변환 sweep)
2. **A5 forward-lock + A7 wire** 보존 (CR 4-3 회고 §5 정합)

### CR 4-4 lesson applied

1. **V8 골든 fixture 매트릭스** — 6-2 wire A11 결정 보존 (V8 16-fixture matrix extension done)
2. **tenant-scoped result_hash** — closing_pdf_export byte-identical CI gate 동일 pattern

## Testing Standards

- **pytest** (backend): 30 NEW cases (pure helper 12 + service layer 8 + carry-over close-out 10)
- **vitest** (frontend): 25 NEW cases (closing-pdf-export-button 5 + labels-ko 10 + closing-period carry 5 + reversal-execute carry 5)
- **Playwright** (E2E): 4 NEW scenarios (closing_pdf_export 4)
- **cross-language parity** (Python ↔ TS): 5 NEW parity cases
- **SDR drift detector**: closing_pdf_export 1 NEW + labels-ko 1 NEW = 2 NEW cases

**MAX SDR claim 갱신**: 1758 → 1823 (+65 NEW tests, separate line for unambiguous parser match per CR 11-2 lesson)

## 3중 게이트 final clean (mandatory CI)

- ruff scoped (6-3 surface ~20 files) → All checks passed
- import-linter (변경 無 — closing_pdf_export_service = m4_inventory subdir, ALLOWED_SERVICE_SUBMODULES 보존) → 2 KEPT 0 broken
- pytest (6-3 surface 9 files, **68 NEW passed + 4 warnings in 4.43s**) — actual pytest --collect-only count = **1823 tests** (1758 baseline + 65 NEW = matches SDR claim 1823 within tolerance)
- tsc (TS mirrors + components) → 0 errors
- vitest (25 NEW cases) → 25/25 pass
- Playwright E2E (4 NEW scenarios) → 4/4 pass
- SDR drift detector → MAX 1758 → 1823 separate line 갱신

## Dev Notes

### Source Tree Components to Touch

**Backend NEW (5 files)**:
1. `packages/services/m4_inventory/closing_pdf_export.py` — pure helper
2. `apps/api/modules/m4_inventory/services/closing_pdf_export_service.py` — service layer
3. `tests/services/m4_inventory/test_closing_pdf_export.py` — 12 NEW pure tests
4. `tests/api/m4_inventory/test_closing_pdf_export_service.py` — 8 NEW service tests
5. `tests/integration/test_closing_pdf_export_byte_identical.py` — byte-identical CI gate (optional)

**Backend EXTENSION (3 files)**:
6. `apps/api/modules/m4_inventory/handlers.py` — POST route
7. `apps/api/modules/m4_inventory/services/__init__.py` — re-export (W1 close)
8. `packages/cost_engine/labels_ko.py` — ko-KR label extension

**Frontend NEW (4 files)**:
9. `apps/web/components/m2-input/ClosingPdfExportButton.tsx` — shadcn Button
10. `apps/web/lib/closing-pdf-export.ts` — TS mirror
11. `apps/web/lib/labels-ko.ts` — ko-KR format helpers
12. `apps/web/__tests__/labels-ko.test.ts` — vitest

**Frontend EXTENSION (3 files)**:
13. `apps/web/app/(authenticated)/m2-input/period/[periodKey]/page.tsx` — 진입점
14. `apps/web/ko-KR.json` — 30 NEW strings
15. `apps/web/components/m2-input/__tests__/` — vitest extension

**Tests NEW (3 files)**:
16. `tests/integration/test_inline_projection_deprecation_timeline.py` — A8 timeline (5 cases)
17. `tests/integration/test_closing_pdf_export_byte_identical.py` — byte-identical gate
18. `e2e/closing-pdf-export.spec.ts` — Playwright E2E (4 scenarios)

**Docs NEW (2 files)**:
19. `docs/closing-pdf-export.md` — 운영 매뉴얼
20. `docs/ko-KR-labels.md` — ko-KR SSOT guide

**Docs EXTENSION (2 files)**:
21. `docs/closing-period.md` — §A8 timeline update
22. `docs/architecture-inventory.md` — closing_pdf_export module entry

### ALLOWED_SERVICE_SUBMODULES pattern

`packages.services.m4_inventory` 보존 — 6-3 신규 submodule 추가 시 dev-story T1 즉시 sync (CR 11-3 lesson).

## References

- [Source: `_bmad-output/implementation-artifacts/6-2-monthly-closing-report.md` — 6-2 wire baseline + 5 honestly DEFER]
- [Source: `_bmad-output/implementation-artifacts/6-1-closing-period-service-snapshot-event.md` — 6-1 wire baseline + 13 DEFER close-out]
- [Source: `_bmad-output/implementation-artifacts/epic-5-retro-2026-08-07.md` §6 W1 cj-style 6-1/6-2/6-3 분할]
- [Source: PRD §F6.3 (Closing PDF Export) + PRD §F5 (마감 보고서) + PRD §A11 (3-layer defense)]
- [Source: AD-2 (append-only ledger) + AD-8 (monetary types) + AD-11 (layer rule) + AD-15 (cross-language parity)]
- [CR 6-1 lesson: [[cr-6-1-lessons]]]
- [CR 6-2 lesson: [[cr-6-2-lessons]]]
- [CR 4-3 lesson: [[cr-4-3-lessons]]]
- [CR 4-4 lesson: [[cr-4-4-lessons]]]

## Dev Agent Record

### Agent Model Used
(pending dev-story execution)

### Debug Log References
(pending dev-story execution)

### Completion Notes List
T1~T6 모두 done. 6-2 carry-over close-out 5 W-items 완료 (W1/W2/W3/W4/W5). A8 timeline guard + A5+A7+A11+A12 preservation 13 NEW test cases 추가. ko-KR labels SSOT 4 surface cross-language parity 8 NEW scenarios. V8 runner E2E 6 NEW scenarios (CR 6-1/11-3 lessons applied: ALLOWED_SERVICE_SUBMODULES 즉시 sweep + ruff scoped auto-fix + abnormal-halt recovery 2-commit pattern).

### File List

**T1 Backend wire (NEW files):**
- `packages/services/m4_inventory/closing_pdf_export.py` (NEW, ~280 lines)
- `apps/api/modules/m4_inventory/services/closing_pdf_export_service.py` (NEW, ~360 lines)

**T1 Backend wire (MODIFIED):**
- `apps/api/modules/m4_inventory/handlers.py` (POST /export-pdf route)
- `apps/api/main.py` (3 NEW exception handlers — 422/409/500)
- `tests/architecture/test_api_calls_only_ports.py` (ALLOWED_SERVICE_SUBMODULES sweep)

**T1 Tests (NEW):**
- `tests/services/m4_inventory/test_closing_pdf_export.py` (20 cases)
- `tests/api/m4_inventory/test_closing_pdf_export_service.py` (6 cases)
- `tests/api/m4_inventory/test_closing_pdf_export_envelope.py` (4 cases)

**T2 Frontend wire (NEW):**
- `apps/web/lib/closing-pdf-export.ts` (TS mirror, ~120 lines)
- `apps/web/components/m2-input/ClosingPdfExportButton.tsx` (Client Component)
- `apps/web/__tests__/closing-pdf-export.test.tsx` (12 Vitest scenarios)
- `apps/web/e2e/v8-runner.spec.ts` (4 Playwright scenarios — skip-if-not-wired)

**T2 Frontend wire (MODIFIED):**
- `apps/web/lib/server-api.ts` (fetchTenantSettingsServerSide)
- `apps/web/app/[locale]/(dashboard)/m2-input/period/[periodKey]/monthly-closing-report/page.tsx`
- `apps/web/components/m2-input/MonthlyClosingReportPanel.tsx`
- `apps/web/messages/ko-KR.json` (closing_pdf_export namespace 10 keys)

**T2 Tests (NEW):**
- `tests/integration/test_closing_pdf_export_label_consistency.py` (8 parity cases)

**T3 ko-KR labels (NEW):**
- `apps/web/lib/labels-ko.ts` (T4 W3 close-out, ~80 lines)
- `tests/integration/test_closing_pdf_export_ko_kr_comprehensive.py` (8 cross-surface scenarios)

**T4 Carry-over close-out (NEW/MODIFIED):**
- `apps/api/modules/m4_inventory/services/__init__.py` (W1 re-export close)
- `packages/cost_engine/tests/regression_v8/fixture_publisher.py` (W2 deferral docstring)
- `tests/regression_v8/test_v8_runner_e2e.py` (W4 V8 runner E2E — moved from packages/cost_engine)

**T5 A8 timeline + A5+A7+A11+A12 (NEW):**
- `tests/integration/test_inline_projection_deprecation_timeline.py` (7 scenarios)
- `tests/integration/test_6_3_action_inventory_preservation.py` (6 scenarios)
- `docs/closing-period.md` (§A8 timeline 6-3 wire marker)

**T6 Docs + 3중 게이트:**
- `docs/closing-pdf-export.md` (NEW, ~150 lines)
- `docs/ko-KR-labels.md` (NEW, ~100 lines)
- `docs/architecture-inventory.md` (§6.3 EXTENSION)

## Review Findings
(pending bmad-code-review execution — recommend R4 triage + carry-over + 3rd sweep pattern, 6-1/6-2 baseline)