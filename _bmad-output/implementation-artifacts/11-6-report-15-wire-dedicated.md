---
title: Report #15 Wire Dedicated (활동원가 내역서 — A40 결정 wire 진입점)
status: ready-for-dev
priority: HIGH
epic: 11
story_num: 6
story_key: 11-6-report-15-wire-dedicated
baseline_commit: 1060360
created: 2026-08-19
updated: 2026-08-19
---

> **A40 결정 wire** (Epic 10 close-out retro 2026-08-19 §7 신규 결정 + 사용자 옵션 (a) wire 진입 결정 = "A41 carry-over sprint 진입 시 wire"). 본 스토리는 A40 = Report #15 wire (활동원가 내역서) **dedicated sprint** = A33 forward-lock (A19 cohesion 9 surface 진입) + A32 forward-lock (A30 SHARED factory reuse 1st case) + A31 forward-lock (Report #15 wire schedule).
>
> **baseline_commit = `1060360`** (Story 11.5 atomic wire tip = Epic 11 second carry-over sprint = A41 close-out part wire).
>
> **Epic 9 close-out retro (2026-08-17) §7 A31~A33 결정 wire** + **Epic 10 close-out retro (2026-08-19) §7 A40 신규 결정 wire** + **Epic 11 second carry-over sprint (11-5, 2026-08-19) §Scope 분할 결정 (Option B SPLIT)** = 본 스토리 scope.

# Story 11.6 — Report #15 Wire Dedicated (활동원가 내역서)

## Epic context

**Epic 9 close-out retro** (cj-style 7-section lightweight, 2026-08-17) 완료. 6 NEW action items A31~A36 결정:
- **A31** = Report #15 wire schedule (cj-style Epic 9 6번째 진입점 권장)
- **A32** = A30 SHARED factory pattern reuse entry 1st case (Report #15)
- **A33** = A19 cohesion pattern 9 surface 진입 시점 = Report #15 wire

**Epic 10 close-out retro** (cj-style 5번째 진입점, 2026-08-19) 완료. 6 NEW action items A37~A42 결정:
- **A40** = A31/A32/A33 (Report #15 wire schedule) 처리 결정 — ✅ **사용자 결정 2026-08-19 = 옵션 (a) = A41 Epic 11 carry-over sprint 진입 시 wire**

**Epic 11 close-out retro** (cj-style 7-section lightweight, 2026-08-09) 완료. 6 NEW action items A13~A18 결정:
- A13/A17/A18 → 11-4 + 11-5 carry-over sprint DONE (commit `1060360`)
- A41 = Epic 11 second carry-over sprint = A13 close-out part DONE (`1060360`)
- **A40 Report #15 wire** = 별도 Sprint 11-6 dedicated wire = 본 스토리

**Sprint 11-5 scope 분할 결정 (Option B SPLIT, 2026-08-19)**: Sprint 11-5 = A41 close-out part (A13 residual + A17 + A18, ~400 LOC atomic) / Sprint 11-6 = A40 Report #15 wire dedicated (~1,500 LOC atomic, 9 A19 surfaces). cj-style atomic discipline 보존.

## Sprint scope (9 A19 cohesion surfaces — 본 스토리)

### Report #15 — 활동원가 내역서 (PRD §9 #15 verbatim)

**Primary PRD ref**: §9 #15 verbatim ("활동원가 내역서 — 활동별 원가·동인 단가") + §7.1 ABC Step 0~3 (활동·동인 매트릭스) + §9 공통 규격 (한·영 + KRW·USD + A4 인쇄 + PDF 내보내기 + 격식체 서술).

**Primary AD ref**: AD-5 engine purity + AD-11 layer rule + AD-15 cross-language conventions + AD-22 ledger append-only (CR 1.1 audit-first invariant) + AD-23 settings aggregate (KRW/USD 환율).

**Capability**: `Capability.ABC_CALCULATION` (industry-agnostic, 9-1 wire 그대로 재사용). Capability matrix v1.21 변경 0건 (CR 12-1 L4 precedent).

**Auth scope**: `require_role("owner")` for owners + service-only (MANUFACTURING 테넌트 회색 "비활성" 처리).

**D-9-4-DEFER-2 해소**: 9-4 wire 시점에 `pdf_generator._compose_report15_pdf` placeholder 그대로 + `_validate_report_pdf_request` Discriminated union `report_id=15` member 1개 추가 wire만 done. 본 스토리 = Report #15 본체 wire (활동별 원가·동인 단가).

### Surface 1 — Backend pure kernel EXTENSION (`packages/cost_engine/abc_engine.py`)

A19 cohesion pattern 7 surface (9-1 + 9-2 + 9-3 + 9-4 EXTENSION 누적) — Report #15 wire 진입 시점에 동일 surface EXTENSION.

**Wire scope**:
- 1 pure function: `compute_report15_hash(*, activity_breakdown: list[ActivityCostRow], period_key: str, v7_verdict: V7Verdict) -> str` (V8 byte-identical determinism)
- 1 frozen dataclass: `ActivityCostRow(activity_id: str, activity_name_ko: str, activity_name_en: str, total_cost_krw: Decimal, total_cost_usd: Decimal, driver_count: int, cost_per_driver_krw: Decimal, cost_per_driver_usd: Decimal, allocated_krw: Decimal, allocated_usd: Decimal, hash: str)` (Pydantic v2 frozen)
- 1 frozen dataclass: `Report15Summary(activity_count: int, total_cost_krw: Decimal, total_cost_usd: Decimal, total_driver_count: int, hash: str)`
- 1 typed exception: `Report15InconsistentStateError` (HTTP 422 REPORT15_INCONSISTENT_STATE)
- AD-5 stdlib-only (9-1 + 9-2 + 9-3 + 9-4 + 11-6 동일 surface, NO cross-import)

**Tests**: `tests/cost_engine/test_abc_engine_report15.py` NEW ~28 cases (compute_report15_hash × 8 + ActivityCostRow × 6 + Report15Summary × 4 + Report15InconsistentStateError × 4 + frozen dataclass × 6).

### Surface 2 — A30 SHARED factory EXTENSION (`packages/services/m5_reports/pdf_generator.py`)

A19 cohesion pattern **9 surface 진입** (A33 forward-lock) — Report #15 wire 진입 시점에 pdf_generator `_compose_report15_pdf` 본체 wire (placeholder → 본체).

**Wire scope** (9-4 wire placeholder → 본체):
- `_compose_report15_pdf` 본체 wire: 활동별 행 + 동인 단가 + KRW/USD + 격식체 서술 (A4 인쇄 최적화 동일 surface 재사용)
- `_validate_report_pdf_request` Discriminated union `report_id=15` payload invariants wire:
  - `report_id=15` → payload MUST be non-empty (활동 1개 이상 필수, PRD §9 #15 verbatim — 활동 데이터 부재 시 422 envelope)
  - payload 행 dict[str, str] JSON-safe shape (KRW amounts as Decimal-as-string)
- 5 NEW constants: `REPORT15_PDF_TITLE_KO = "활동원가 내역서"` + `REPORT15_PDF_EMPTY_KO = "활동 데이터 없음"` + `REPORT15_REPORT_CODE = "ACTIVITY_COST_DETAIL"` + `REPORT15_ACTIVITY_NAME_KO` + `REPORT15_ACTIVITY_NAME_EN`

**Tests**: `tests/services/test_m5_reports_pdf_generator.py` EXTENSION ~16 NEW cases (Report #15 compose × 6 + payload validation × 4 + REPORT15_* constants × 4 + Discriminated union × 2).

### Surface 3 — A30 SHARED factory reuse 1st case (A32 forward-lock 결정 wire)

본 surface wire = Report #15 진입 시점에 A30 SHARED factory 패턴 reuse 진입 1st case. Report #21 동일 surface (`generate_report_pdf(*, request)`) 그대로 재사용 + `report_id=15` discriminator 1개 추가.

### Surface 4 — M5 reports service layer `Report15Service` (CR 1.1 audit-first + V7 balance)

**Wire scope**:
- `apps/api/modules/m5_reports/services/report15_service.py` NEW
  - `Report15Service.build_report15(*, tenant_id: UUID, period_key: str, include_krw_usd: bool, year_over_year: bool) -> Report15Response` NEW method
  - `_to_report15_state(*, snapshot: FiscalPeriodSnapshot, activity_breakdown: list[ActivityCostRow], v7_verdict: V7Verdict, currency_pair: CurrencyPair) -> Report15Response` ORM→kernel boundary (CR 12-1 L3 precedent, 9-3 `_to_abc_allocation_state` + 9-4 `_to_report21_state` 패턴 미러)
  - LAZY Verdict imports (circular import 방지 — `from apps.api.core.verdict import Verdict, VerdictStatus` inside method body)
- `apps/api/modules/m5_reports/services/__init__.py` EXTENSION (Report15Service export)
- `apps/api/modules/m5_reports/exceptions.py` EXTENSION (4 NEW typed exceptions: `Report15PeriodNotCommittedError` + `Report15NoActivityBreakdownError` + `Report15BreakdownNotFoundError` + `Report15InconsistentStateError` + 4 Korean SSOT)
- `apps/api/modules/m5_reports/schemas.py` EXTENSION (NEW Pydantic models for `Report15Response` + `ActivityCostRow` + `CurrencyPair` + `V7BalanceResult` + extended `ReportPdfRequest` for `report_id=15` payload schema)
- `apps/api/main.py` EXTENSION (4 NEW envelope handlers: 422 REPORT15_PERIOD_NOT_COMMITTED + 422 REPORT15_NO_ACTIVITY_BREAKDOWN + 404 REPORT15_BREAKDOWN_NOT_FOUND + 422 REPORT15_INCONSISTENT_STATE — CR 12-5 D-14 verbatim)
- `packages/services/m5_reports/__init__.py` EXTENSION (re-export `Report15Service`, 9-2 + 9-4 re-export 패턴 미러)
- `tests/services/test_m5_reports_report15_service.py` NEW ~18 cases (build_report15 × 6 + _to_report15_state × 4 + audit-first × 2 + deleted-period × 2 + V7 balance guard × 2 + activity cost breakdown)
- `tests/architecture/test_api_calls_only_ports.py` EXTENSION (ALLOWED_SERVICE_SUBMODULES 그대로 보존 — Report15Service는 M5 reports service layer ONLY)

### Surface 5 — M5 reports HTTP handlers (`apps/api/modules/m5_reports/handlers.py`)

**Wire scope**:
- `apps/api/modules/m5_reports/handlers.py` EXTENSION (9-4 wire handlers 동일 file)
  - `GET /api/v1/reports/15` endpoint (read-only, AC #4 verbatim)
  - `POST /api/v1/reports/15/pdf` endpoint (PDF export, AC #5 verbatim)
  - Capability gate: `Depends(require_capability(Capability.ABC_CALCULATION))` (9-1 + 9-2 + 9-3 + 9-4 동일 capability 보존 — capability matrix v1.21 변경 0)
  - Role gate: `require_role("owner")` (export 권한)
  - 응답 헤더: `Content-Disposition: attachment; filename="report-15-{tenant_id}-{period_key}.pdf"` (PDF export)
- `apps/api/main.py` EXTENSION (M5 reports router 등록 그대로 보존)
- `tests/api/test_m5_reports_handlers.py` EXTENSION ~12 NEW cases (GET /api/v1/reports/15 × 6 + POST /api/v1/reports/15/pdf × 4 + capability gate × 1 + envelope × 1)

### Surface 6 — Frontend RSC + components + TS mirrors + ko-KR.json SSOT (CR 11-4 lessons applied)

**Wire scope**:
- `apps/web/app/[locale]/(dashboard)/reports/15/page.tsx` NEW RSC (CR 11-4 D-001 mounts `<Report15Panel>` JSX, Report #21 page.tsx 패턴 미러)
- 3 NEW components (cj-style 9-4 component pattern 미러):
  - `Report15Panel` (main Client Component, Form + display + PDF export button)
  - `ActivityCostBreakdownTable` (activity_id별 행 + 동인 단가 + KRW/USD toggle)
  - `ActivityCostPdfExportButton` (PDF 내보내기 trigger)
- 2 NEW TS mirrors (CR 11-4 D-005 unknown state reject):
  - `apps/web/lib/report15.ts` (Report15Response + ActivityCostRow + CurrencyPair + V7BalanceResult type union + 4 type guards)
  - `apps/web/lib/report15-pdf.ts` (ReportPdfRequest + ReportPdfResult frozen type mirrors for `report_id=15`)
- `apps/web/messages/ko-KR.json` EXTENSION `report15` namespace ~25 strings SSOT (CR 11-4 D-002, A30 SHARED `pdf_common` namespace 그대로 재사용)

**Tests**:
- vitest: `apps/web/__tests__/components/m5-reports.Report15Panel.test.tsx` NEW ~10 cases (mount + capability gate + KRW/USD toggle + PDF export trigger)
- vitest: `apps/web/__tests__/lib/report15-parity.test.ts` NEW ~6 cases (TS mirror parity with Python pure kernel)
- vitest: `apps/web/__tests__/lib/report15-pdf-parity.test.ts` NEW ~4 cases (ReportPdfRequest `report_id=15` payload schema parity)
- Playwright: `apps/web/e2e/m5-reports-report15.spec.ts` NEW 4 E2E scenarios (mount + display + KRW/USD toggle + PDF export)

### Surface 7 — Cross-language drift detector + V8 byte-identical determinism (CR 12-5 D-13 + V8 invariant)

**Wire scope**:
- Cross-language drift detector EXTENSION (`tests/integration/test_m5_reports_cross_lang_drift.py`):
  - 8+ NEW vectors: format helpers (KRW/USD, ko-KR/en-US, A4 page size, sha256 hash) + envelope codes (REPORT15_*) + discriminated union types (Report15Response + ReportPdfRequest `report_id=15`)
- V8 골든 fixture: Report #15 expected bytes (deterministic JSON serialization order)
- V8 byte-identical determinism (PRD §V8):
  - Report #15 main response hash = `sha256(sorted JSON)` (V8 invariant)
  - PDF binary hash = `sha256(pdf_bytes)` (PDF generation determinism)
- A30 PDF generator parity: Report #15 + Report #21 share `generate_report_pdf(*, request)` factory (Discriminated union `report_id` literal)

**Tests**: `tests/cost_engine/test_report15_hash_determinism.py` NEW V8 byte-identical 6 cases (Report #15 + PDF byte hash) + drift detector EXTENSION 8 NEW cases.

### Surface 8 — Audit-first AD-22 wire (CR 1.1 invariant)

**Wire scope**:
- `apps/api/modules/m5_reports/services/report15_service.py` EXTENSION (build_report15 진입 시 audit log INSERT — `audit_logs.action='report15_generated'` + tenant_id + actor_id + period_key + report_id + generation_hash + trace_id)
- `apps/api/core/audit_action.py` EXTENSION (`ActionClass.REPORT_GENERATION` 1 NEW + `report15_generated` 1 NEW Literal value)
- `tests/integration/test_audit_action_3way_extension_drift.py` EXTENSION (1 NEW REPORT_GENERATION case × 3-way = registry + call site + DB-N/A) — A18 wire 패턴 보존

### Surface 9 — Capability matrix no-change (CR 12-1 L4 precedent)

- `apps/api/core/capability.py` 변경 0건 (9-1 wire 그대로 재사용 — `Capability.ABC_CALCULATION` 보존)
- `docs/capability-matrix.md` 변경 0건 (9-1 wire 그대로 보존)
- `tests/integration/test_capability_matrix_drift.py` 변경 0건 (no NEW capability row)

## Honestly DEFER to follow-up sweep

본 스토리 scope 외. follow-up sweep 또는 Epic 12 진입 시점에 결정.

| Item | Scope | Reason |
|---|---|---|
| Report #16 (원가대상 수익성 보고서) wire | 동일 A30 SHARED factory reuse 2nd case (report_id=16) | cj-style Epic 11 7번째 진입점 또는 Epic 12 territory. A30 SHARED factory placeholder 그대로 보존. |
| Report #17/18/19/20 wire | 동일 surface EXTENSION (5 reports × ~1,500 LOC × 5 = ~7,500 LOC) | 별도 epic territory (A39 LISTEN/NOTIFY separate epic 결정 후속) |
| Report #21 PDF 본체 polish (9-4 wire 후속) | 9-4 wire 본체 그대로 보존, polish 결정 후속 | A40 본 스토리 = Report #15 우선, Report #21 polish는 별도 |

## Tasks / Subtasks

본 스토리는 atomic single sprint T1~T8 wire:

- [ ] **Task 1: Surface 1 kernel EXTENSION** (AC: #1)
  - [ ] Subtask 1.1: `packages/cost_engine/abc_engine.py` EXTENSION (compute_report15_hash + ActivityCostRow + Report15Summary + Report15InconsistentStateError)
  - [ ] Subtask 1.2: `packages/cost_engine/__init__.py` EXTENSION (3 NEW exports)
  - [ ] Subtask 1.3: `tests/cost_engine/test_abc_engine_report15.py` NEW (~28 cases)
  - [ ] Subtask 1.4: `tests/cost_engine/test_abc_engine_no_io_imports.py` EXTENSION (NEW 4 cases: stdlib whitelist EXTENSION report15)
- [ ] **Task 2: Surface 2 A30 SHARED factory EXTENSION** (AC: #2)
  - [ ] Subtask 2.1: `packages/services/m5_reports/pdf_generator.py` EXTENSION (_compose_report15_pdf 본체 + _validate_report_pdf_request payload invariants + 5 REPORT15_* constants)
  - [ ] Subtask 2.2: `tests/services/test_m5_reports_pdf_generator.py` EXTENSION (~16 NEW cases)
- [ ] **Task 3: Surface 4 service layer NEW** (AC: #3)
  - [ ] Subtask 3.1: `apps/api/modules/m5_reports/services/report15_service.py` NEW (Report15Service.build_report15 + _to_report15_state)
  - [ ] Subtask 3.2: `apps/api/modules/m5_reports/services/__init__.py` EXTENSION (Report15Service export)
  - [ ] Subtask 3.3: `apps/api/modules/m5_reports/exceptions.py` EXTENSION (4 NEW typed exceptions + 4 Korean SSOT)
  - [ ] Subtask 3.4: `apps/api/modules/m5_reports/schemas.py` EXTENSION (NEW Pydantic models for Report15Response + ActivityCostRow + extended ReportPdfRequest for report_id=15)
  - [ ] Subtask 3.5: `apps/api/main.py` EXTENSION (4 NEW envelope handlers per CR 12-5 D-14 verbatim)
  - [ ] Subtask 3.6: `packages/services/m5_reports/__init__.py` EXTENSION (re-export Report15Service)
  - [ ] Subtask 3.7: `tests/services/test_m5_reports_report15_service.py` NEW (~18 cases)
  - [ ] Subtask 3.8: `tests/architecture/test_api_calls_only_ports.py` EXTENSION (ALLOWED_SERVICE_SUBMODULES 그대로 보존)
- [ ] **Task 4: Surface 5 handlers EXTENSION** (AC: #4)
  - [ ] Subtask 4.1: `apps/api/modules/m5_reports/handlers.py` EXTENSION (GET /api/v1/reports/15 + POST /api/v1/reports/15/pdf endpoints)
  - [ ] Subtask 4.2: `apps/api/main.py` EXTENSION (router 등록 그대로 보존)
  - [ ] Subtask 4.3: `tests/api/test_m5_reports_handlers.py` EXTENSION (~12 NEW cases)
- [ ] **Task 5: Surface 6 frontend NEW** (AC: #5)
  - [ ] Subtask 5.1: `apps/web/app/[locale]/(dashboard)/reports/15/page.tsx` NEW RSC
  - [ ] Subtask 5.2: 3 NEW components (Report15Panel + ActivityCostBreakdownTable + ActivityCostPdfExportButton)
  - [ ] Subtask 5.3: 2 NEW TS mirrors (apps/web/lib/report15.ts + report15-pdf.ts)
  - [ ] Subtask 5.4: ko-KR.json EXTENSION report15 namespace (~25 strings)
  - [ ] Subtask 5.5: vitest 3 NEW files (Report15Panel mount + parity × 2)
  - [ ] Subtask 5.6: Playwright 1 NEW spec (4 E2E scenarios)
- [ ] **Task 6: Surface 7 cross-lang drift + V8 determinism** (AC: #6)
  - [ ] Subtask 6.1: `tests/integration/test_m5_reports_cross_lang_drift.py` EXTENSION (~8 NEW vectors)
  - [ ] Subtask 6.2: `tests/cost_engine/test_report15_hash_determinism.py` NEW (V8 byte-identical 6 cases)
- [ ] **Task 7: Surface 8 audit-first AD-22 wire** (AC: #7)
  - [ ] Subtask 7.1: `apps/api/modules/m5_reports/services/report15_service.py` EXTENSION (audit log INSERT in build_report15)
  - [ ] Subtask 7.2: `apps/api/core/audit_action.py` EXTENSION (ActionClass.REPORT_GENERATION 1 NEW + report15_generated 1 NEW)
  - [ ] Subtask 7.3: `tests/integration/test_audit_action_3way_extension_drift.py` EXTENSION (1 NEW REPORT_GENERATION case)
- [ ] **Task 8: T6 docs + sprint-status sync** (AC: #8)
  - [ ] Subtask 8.1: `docs/abc-report-15.md` NEW (Activity Cost Detail wire spec — Report #21 doc 패턴 미러)
  - [ ] Subtask 8.2: `docs/deferred-work.md` EXTENSION (`## Deferred from: 11-6` section)
  - [ ] Subtask 8.3: `sprint-status.yaml` 11-6 entry: ready-for-dev → in-progress → done
- [ ] **Task 9: T7 3중 게이트 FINAL CLEAN verification** (AC: #9)
- [ ] **Task 10: T8 atomic commit + memory handoff** (AC: #10)

## Acceptance Criteria

1. **Surface 1 kernel**: `compute_report15_hash` + `ActivityCostRow` + `Report15Summary` + `Report15InconsistentStateError` 모두 wire, AD-5 stdlib-only verified, 28 NEW pytest cases PASS
2. **Surface 2 A30 SHARED factory**: `_compose_report15_pdf` 본체 wire + payload invariants wire + 5 REPORT15_* constants, 16 NEW pytest cases PASS
3. **Surface 4 service**: `Report15Service.build_report15` + `_to_report15_state` + 4 typed exceptions + 4 envelope handlers + ALLOWED_SERVICE_SUBMODULES preserved, 18 NEW pytest cases PASS
4. **Surface 5 handlers**: GET /api/v1/reports/15 + POST /api/v1/reports/15/pdf endpoints wire + capability gate + role gate + Content-Disposition header, 12 NEW pytest cases PASS
5. **Surface 6 frontend**: page.tsx NEW + 3 NEW components mount (CR 11-4 D-001) + 2 NEW TS mirrors + ko-KR.json SSOT (CR 11-4 D-002) + unknown state reject (CR 11-4 D-005), 20 NEW vitest cases PASS + 4 NEW Playwright scenarios PASS
6. **Surface 7 cross-lang + V8**: 8 NEW cross-lang vectors + V8 byte-identical 6 cases PASS
7. **Surface 8 audit-first**: AD-22 ledger append-only verified (CR 1.1 invariant) + audit log INSERT in build_report15 + ActionClass.REPORT_GENERATION wire + 1 NEW REPORT_GENERATION 3-way case PASS
8. **Docs sync**: `docs/abc-report-15.md` NEW + `docs/deferred-work.md` 11-6 section + `sprint-status.yaml` 11-6 status: done
9. **3중 게이트 FINAL CLEAN**: ruff scoped 0 NEW + ruff full 0 NEW (CR 11-4 lesson) + import-linter 2 KEPT 0 broken + pytest focused 60+ NEW PASS + vitest 20 NEW PASS + Playwright 4 NEW scenarios PASS + tsc zero NEW + A36 SDR 4-step PASS
10. **Atomic commit + memory handoff**: `git commit -F <file>` (NOT PowerShell here-string per CR 9-6 D5 prevention) + separate memory handoff commit

## Dev Notes

### CR 11-3 lessons applied

1. **ALLOWED_SERVICE_SUBMODULES sweep 즉시** — 본 스토리 wire = `apps/api/modules/m5_reports/services/report15_service.py` NEW → `packages/services/m5_reports/__init__.py` EXTENSION re-export → architecture test fail-fast로 allowlist 누락 감지 (CR 11-3 D-2)
2. **ruff scoped auto-fix sweep 일괄** — wire file 작성 직후 `uv run ruff check <files> --fix` 한 번에 해결
3. **CR 4-3 fix script sweep** — async test pattern: `def test_X(args) -> None: ... async def _impl() -> None: ... asyncio.run(_impl())` 변환
4. **SDR MAX claim separate line** — "**N tests collected**" 별도 line (parser unambiguous)
5. **abnormal-halt recovery checkpoint** — T1~TN partial done 시점에 commit → 후속 fix는 별도 commit 분리

### CR 11-4 lessons applied

1. **page.tsx mount discipline** — components MUST be actually mounted (D-001), not just created. Report #15 page.tsx = Report #21 page.tsx 패턴 미러 (Report21Panel → Report15Panel JSX mount 검증)
2. **ko-KR.json SSOT** — `apps/web/messages/ko-KR.json` ONLY, no `apps/web/lib/ko-KR.json` (D-002)
3. **TS mirror unknown state** — explicit `return {authorized: false, ...}` for unknown/malformed input (D-005)
4. **P-015 SSOT drift detector** — ko-KR.json (lib) ↔ messages/ko-KR.json cross-lang parity 자동 검증 (CR 11-4 P-015)

### CR 12-5 lessons applied

1. **D-GATE-01 inversion** — capability gate `Depends(require_capability(Capability.ABC_CALCULATION))` 1-route (9-1 + 9-2 + 9-3 + 9-4 + 11-6 동일 capability). dual-route는 Report #21 only (CR 12-5 inversion 결정)
2. **D-PARITY-01 inversion** — TS mirror + Python pure kernel 4 type guards parity (CR 12-5 inversion 결정)
3. **TOTP chain** — Report #15 audit log INSERT는 audit-first chain (AD-22 append-only invariant 보존)
4. **cross-language drift detector** — Surface 7 wire = 8 NEW vectors EXTENSION

### CR 9-6 D5 prevention

- commit message = `git commit -F <file>` (NOT PowerShell here-string)
- commit subject = "Story 11.6 (Epic 11 6번째 진입점, cj-style 37번째 epic 연속): ..."

### Critical Path

1. **kernel 작성 직후**: `pytest tests/cost_engine/test_abc_engine_report15.py -v` 28 NEW cases PASS
2. **pdf_generator EXTENSION 직후**: `pytest tests/services/test_m5_reports_pdf_generator.py -v` Report #15 cases PASS
3. **service layer 작성 직후**: `pytest tests/services/test_m5_reports_report15_service.py -v` 18 NEW cases PASS + architecture test ALLOWED_SERVICE_SUBMODULES 그대로 보존 검증
4. **handlers 작성 직후**: `pytest tests/api/test_m5_reports_handlers.py -v -k "report_15"` 12 NEW cases PASS
5. **TS mirror 작성 직후**: `pnpm exec tsc --noEmit` 0 errors 검증 (cross-language parity fail-fast)
6. **page.tsx 작성 직후**: `pnpm exec vitest run apps/web/__tests__/components/m5-reports.Report15Panel.test.tsx -v` mount verification PASS
7. **전체 wire 후**: `pytest apps/api/modules/m5_reports/ tests/services/ tests/integration/ -v` 회귀 0건 + `pnpm exec vitest run apps/web/__tests__/ -v` 회귀 0건

### Critical Path Before 11-6 dev-story

없음. baseline_commit = `1060360` 그대로 사용. 모든 wire는 incremental T1~T8 atomic commit 진입.

## Testing Standards

- pytest: 28 (Surface 1) + 16 (Surface 2) + 18 (Surface 4) + 12 (Surface 5) + 8 (Surface 7 cross-lang) + 6 (Surface 7 V8) + 1 (Surface 8 audit) = **~89 NEW pytest cases**
- vitest: 10 (Report15Panel mount) + 6 (report15 parity) + 4 (report15-pdf parity) = **~20 NEW vitest cases**
- Playwright: **4 NEW E2E scenarios**
- import-linter: 2 KEPT (no new service submodule, Report15Service는 m5_reports service layer ONLY)
- A5 drift detector: 1 NEW REPORT_GENERATION case (Surface 8 audit-first)

**MAX SDR claim 갱신**: 직전 11-5 wire (43 PASS = 15 A17 + 28 A18) → 11-6 wire 후 ~132 NEW PASS 추가 → separate line 갱신 (CR 11-2 lesson).

## 3중 게이트 final clean (mandatory CI)

- ruff scoped (11-6 surface ~12 files) → All checks passed
- import-linter (변경 0 — Report15Service는 m5_reports service layer ONLY, packages/services/m5_reports/__init__.py EXTENSION re-export) → 2 KEPT 0 broken
- pytest (11-6 surface ~89 NEW tests) → All checks passed
- tsc (2 NEW TS mirrors + 3 NEW components) → 0 errors
- vitest (20 NEW cases) → 20/20 pass
- Playwright E2E (4 NEW scenarios) → 4/4 pass
- SDR drift detector → MAX claim 갱신 separate line (CR 11-2 lesson)

## References

- [Source: `_bmad-output/implementation-artifacts/9-4-abc-report-21-cost-object-breakdown.md` §A30 SHARED factory pattern + §AC #5 PDF export + §AC #8 A19 cohesion 8 surface]
- [Source: `_bmad-output/implementation-artifacts/epic-9-retro-2026-08-17.md` §7 A31/A32/A33 결정]
- [Source: `_bmad-output/implementation-artifacts/epic-10-retro-2026-08-19.md` §7 A40 신규 결정 (옵션 a)]
- [Source: `_bmad-output/implementation-artifacts/11-5-epic-11-second-carry-over-sprint.md` §Scope 분할 결정 (Option B SPLIT)]
- [PRD: `_bmad-output/planning-artifacts/prd.md` §9 #15 활동원가 내역서 verbatim]
- [CR 11-3 lesson: [[cr-11-3-lessons]]]
- [CR 11-4 lesson: [[cr-11-4-lessons]]]
- [CR 12-5 lesson: [[cr-12-5-lessons]]]
- [CR 9-6 D5 prevention: commit message `git commit -F <file>`]

## Open Questions

- **OQ-11-6-1**: A38 frontend test debt dedicated sprint 진입 시점 — 본 스토리 close-out 직후 OR Epic 12 12-1 carry-over sprint 진입 후 (사용자 결정 대기)
- **OQ-11-6-2**: A37 master PRD v2.0 edit 진입 시점 — 본 스토리 close-out 직후 OR Epic 12 진입 후 (사용자 결정 대기)
- **OQ-11-6-3**: Report #16 wire 진입 시점 — 본 스토리 close-out 직후 (cj-style Epic 11 7번째 진입점) OR Epic 12 진입 후 (사용자 결정 대기)
