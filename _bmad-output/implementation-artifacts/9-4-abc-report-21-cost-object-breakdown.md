---
story_id: 9.4
story_key: 9-4-abc-report-21-cost-object-breakdown
title: ABC Report #21 (Cost Object Breakdown + Unused Capacity Full Breakdown + A30 Forward-Lock PDF Generator)
created: 2026-08-17
baseline_commit: a67951b
epic: 9
status: ready-for-dev
target_sprint: cj-style Epic 9 4번째 진입점 (DONE bmad-create-story 2026-08-17)
estimated_complexity: high
honestly_defer_count: 4
---

# Story 9.4 — ABC Report #21 (Cost Object Breakdown + Unused Capacity Full Breakdown + A30 Forward-Lock PDF Generator)

## Story Header

| Field | Value |
|-------|-------|
| **Story ID** | 9.4 |
| **Story Key** | `9-4-abc-report-21-cost-object-breakdown` |
| **Epic** | Epic 9 — ABC / TDABC Engine (Service Business) |
| **baseline_commit** | `a67951b` (Story 9.3 T10 close-out tip = current HEAD, 2026-08-17) |
| **cj-style 분할** | 9-1 + 9-2 + 9-3 + **9-4** + Epic 9 close-out retro (5번째 진입점) — **cj-style 20번째 epic 연속** (Epic 4·5·6·11·12 + Epic 11/12 carry-over + Epic 7·8·9·Walking Skeleton MVP + Epic 9 3번째 + **Epic 9 4번째**) |
| **Forward-lock** | **A30 결정 wire** (Report #21 ↔ Report #15 PDF generator reuse — SHARED `pdf_generator.py` factory pattern, 9-3 handoff `handoff-2026-08-17-9-3-done.md` lock) |
| **Primary capability** | `Capability.ABC_CALCULATION` (industry-agnostic, 9-1 wire 그대로 재사용) + `Capability.COST_CALCULATION` (전통 엔진, dual-route ANY-OF) |
| **Primary PRD ref** | §9 #21 verbatim ("부문귀속명세서, 카브아웃 근거 공시, §7.3") + §7.3 (법인세법 시행규칙 제76조 2기준) + §9 공통 규격 (한·영 + KRW·USD + A4 인쇄 + PDF 내보내기) |
| **Secondary PRD ref** | §A6 (완전배부·대차평형 1원 단위) + §A9 (미사용능력 별도 관리) + §V7 (ABC 무결성) + §V8 (V8 byte-identical determinism) |
| **Primary AD ref** | AD-5 engine purity + AD-11 layer rule + AD-15 cross-language conventions + AD-16 fiscal snapshot contract + AD-18 single product identity + AD-19 single endpoint + AD-20 calculation state machine + AD-22 ledger append-only |
| **Baseline wire** | 9-3 atomic wire 14 NEW + 23 MODIFIED = 37 files (3중 게이트 FINAL CLEAN, 4 honest DEFER) + 9-2 + 9-1 + Walking Skeleton MVP wire 보존 |

## User Story (epics.md Story 9.4 verbatim + PRD §9 #21 verbatim)

As a **사장님**, I want **§9 #21 "원가대상별 원가 집계표"** (PRD §9 #21 verbatim "부문귀속명세서, 카브아웃 근거 공시, §7.3") **가 ABC 결과를 보여주는 것**, so that **여행상품/물류 서비스별 원가 구조를 확인**.

**Note on epics.md vs PRD §9 #21 정합**: epics.md Story 9.4 user story says "원가대상별 원가 집계표" (Cost Object Breakdown) but PRD §9 #21 verbatim says "부문귀속명세서 (카브아웃 근거 공시)" — these are RELATED but DIFFERENT scopes. 본 story는 PRD §9 #21 verbatim (SSOT) + epics.md 9.4 extension (product_id별 행 + 4컬럼) = **합성 scope**로 wire. 정합 차이는 D-9-4-DEFER-1로 honestly DEFER (PDF 라벨 + UX 표기 결정 필요).

**Auth scope**: `require_role("owner")` for owners (보고서 export 권한) + service-only (MANUFACTURING 테넌트 회색 "비활성" 처리).

## Acceptance Criteria (PRD §9 #21 + §7.3 + epics.md 9.4 + §9 공통 규격 verbatim wire)

### AC #1 — A30 forward-lock dual-report PDF generator 결정 wire (9-3 handoff 진입점)

- 9-3 handoff `handoff-2026-08-17-9-3-done.md` A30 forward-lock 결정 wire:
  - **Report #21** (Cost Object Breakdown, 본 story) + **Report #15** (활동원가 내역서, 향후 진입) = **SHARED `pdf_generator.py` factory pattern**
  - 결정 사항: `packages/services/m5_reports/pdf_generator.py` NEW
    - 1 frozen dataclass: `ReportPdfRequest(report_id: Literal[15, 16, 17, 18, 19, 20, 21], tenant_id: ULID, period_key: str, include_krw_usd: bool, locale: str, page_size: Literal["A4"])` discriminated union
    - 1 frozen dataclass: `ReportPdfResult(pdf_bytes: bytes, sha256: str, generated_at: datetime, hash: str, page_count: int)`
    - 1 typed exception: `ReportPdfGenerationError` (500 REPORT_PDF_GENERATION_ERROR)
    - 1 pure function: `generate_report_pdf(*, request: ReportPdfRequest, rows: list[ReportRow]) -> ReportPdfResult` (AD-5 stdlib-only + A4 인쇄 최적화)
    - 1 constant: `PDF_HASH_PREFIX: Final[str] = "sha256:"` (V8 determinism)
    - 1 constant: `REPORT_PDF_LOCALES: Final[tuple[str, ...]] = ("ko-KR", "en-US")` (한·영 SSOT)
  - **D-9-3-DEFER-1 Report #21 PDF export 해소** (본 story wire)
  - **D-9-3-DEFER-3 Unused capacity full breakdown 해소** (T3 wire)
  - Report #15 (활동원가 내역서) 진입 시점은 `report_id=15` discriminated union member 1개 추가로 wire (현재 story 범위 외, **Report #15 entry = 9-4 follow-up 또는 Epic 9 close-out follow-up, D-9-4-DEFER-2**로 honestly DEFER)

### AC #2 — Report #21 Cost Object Breakdown 본문 (PRD §9 #21 + epics.md 9.4 verbatim)

- **Given** 사장님이 [보고서] → [원가대상별 원가 집계표] (Report #21) 클릭
- **When** 서비스 업종(SERVICE) 테넌트에서 진입
- **Then** `product_id`(원가대상)별 행 + 4컬럼 (원가풀·활동·동인·배부액) 표시
  - 데이터 소스: `fiscal_period_snapshots.cost_object_breakdown` JSONB (9-3 wire 0028 Alembic)
  - JOIN: `PRODUCT(product_id)` SSOT (AD-18 single product identity)
  - V7 balance invariant: `Σ(product_id별 배부액) = Σ(department_indirect_cost) - 미사용능력` (PRD §A6)
- **And** 제조업(MANUFACTURING) 테넌트에서는 `engine_type='trad'`만 표시되고 ABC 컬럼은 회색 "비활성" 배지 (epics.md 9.4 verbatim)
- **And** KRW/USD 동시 표시 (PRD §F5.2 + §9 공통 규격):
  - KRW: Decimal-as-string, 1원 단위 (정수), 천단위 콤마
  - USD: float, 소수 2자리, 천단위 콤마
  - 환율: `tenant_settings.onboarding.fx_rate` (AD-23 settings aggregate)
- **And** 다년 조회 + 전년 비교 (PRD §9 공통 규격) + 음수 (1,234) 빨강 (PRD §A11)
- **And** 한·영 + 격식체 서술 (PRD §9 공통 규격)

### AC #3 — D-9-3-DEFER-3 Unused capacity full breakdown by department 해소 (T3 wire)

- **Given** Report #21 본문에 미사용능력 섹션이 포함
- **When** 사장님이 미사용능력 행 펼침 (accordion) 클릭
- **Then** 부서별 미사용능력 breakdown 표시:
  - 데이터 소스: `fiscal_period_snapshots.unused_capacity_breakdown` JSONB (9-3 wire 0028 Alembic)
  - 부서별 행: `department_id` + `unused_hours` + `unused_cost_krw` + `unused_cost_usd` (V7 balance: Σ unused = Σ department - Σ breakdown)
  - V8 byte-identical determinism: `hash = sha256(sorted JSON)` (V8 invariant)
- **And** "미사용능력 보고서" (§9 #18) cross-reference link (Report #18 진입 시 본 보고서로 back)
- **And** 사용시간(`practical_capacity_hours - unused_hours`) 별도 표시 (PRD §7.2 TDABC + §A9)

### AC #4 — Capability dual-route + 읽기 전용 compute path (AD-19 + AD-20 + CR 12-1 L4)

- Capability gate: `Depends(require_any_capability(Capability.COST_CALCULATION, Capability.ABC_CALCULATION))` (9-3 wire ANY-OF 그대로 재사용, capability matrix 변경 0)
- Role gate: `require_role("owner")` (보고서 export 권한)
- HTTP method: `GET /api/v1/reports/21` (read-only, AD-19 + AD-20 state machine: only `committed` snapshots visible)
- Query params: `period_key: str` (YYYY-MM typed, AD-24) + `include_krw_usd: bool = True` + `year_over_year: bool = False`
- Response: `Report21Response(report_id: 21, engine_type: Literal["trad", "abc"], rows: list[Report21Row], unused_capacity: list[UnusedCapacityRow], period_key: str, currency_pair: CurrencyPair, total_unused_krw: Decimal, v7_verdict: V7BalanceResult, generated_at: datetime, hash: str)` (Pydantic v2 frozen)
- 에러 envelope (CR 12-5 D-14 verbatim):
  - `422 REPORT21_PERIOD_NOT_COMMITTED` (period_key not committed)
  - `422 REPORT21_NO_COST_OBJECT_BREAKDOWN` (service-only tenant but no ABC computation)
  - `404 REPORT21_BREAKDOWN_NOT_FOUND` (period_key + segment_id NOT FOUND in fiscal_period_snapshots)
  - `500 REPORT_PDF_GENERATION_ERROR` (PDF export failure)

### AC #5 — Report #21 PDF export (D-9-3-DEFER-1 해소, A30 SHARED PDF generator)

- **Given** 사장님이 Report #21 화면 우상단 [PDF 내보내기] 버튼 클릭
- **When** PDF export 요청
- **Then** POST `/api/v1/reports/21/pdf` 호출 (NEW endpoint, 9-4 wire)
  - Capability dual-route + role gate 동일 (AC #4)
  - Request body: `ReportPdfRequest` (A30 SHARED frozen dataclass)
  - Response: `application/pdf` (binary) + Content-Disposition: `attachment; filename="report-21-{tenant_id}-{period_key}.pdf"`
  - V8 determinism: `sha256:` 64-hex prefix (PDF hash)
- **And** A4 인쇄 최적화 (PRD §9 공통 규격):
  - 페이지 크기: A4 (210mm × 297mm)
  - 폰트: ko-KR (한글) + en-US (영문) 격식체 서술
  - 격자 + 헤더/푸터 (페이지 번호 + 생성 시각 KST)
  - PDF/A 호환 (PRD §9 공통 규격)
- **And** Report #15 (활동원가 내역서) wire 시 SHARED factory 패턴 재사용 (Discriminated union `ReportPdfRequest.report_id=15` member 1개 추가, 9-4 follow-up)

### AC #6 — Frontend RSC + components + TS mirrors + ko-KR.json SSOT (CR 11-4 lessons applied)

- `apps/web/app/[locale]/(dashboard)/reports/report-21/page.tsx` NEW RSC (CR 11-4 D-001 mounts `<Report21Panel>` JSX)
- 4 NEW components (cj-style 9-3 component pattern 미러):
  - `Report21Panel` (main Client Component, Form + display + PDF export button)
  - `Report21CostObjectBreakdownTable` (product_id별 행 + 4컬럼 + KRW/USD toggle)
  - `Report21UnusedCapacityAccordion` (부서별 미사용능력 행 펼침/접힘)
  - `Report21PdfExportButton` (PDF 내보내기 trigger)
- 2 NEW TS mirrors (CR 11-4 D-005 unknown state reject):
  - `apps/web/lib/report21.ts` (Report21Response + Report21Row + CurrencyPair + V7BalanceResult type union + 4 type guards)
  - `apps/web/lib/report21-pdf.ts` (ReportPdfRequest + ReportPdfResult frozen type mirrors)
- `apps/web/messages/ko-KR.json` EXTENSION `report21` namespace ~37 strings SSOT (CR 11-4 D-002, A30 SHARED `pdf_common` namespace 12 strings 추가)

### AC #7 — Cross-language drift detector + V8 byte-identical determinism + A30 PDF generator parity

- Cross-language drift detector (CR 12-5 D-13):
  - 10+ vectors: format helpers (KRW/USD, ko-KR/en-US, A4 page size, sha256 hash) + envelope codes (REPORT21_*) + discriminated union types (Report21Response + ReportPdfRequest)
  - V8 골든 fixture: Report #21 expected bytes (deterministic JSON serialization order)
- V8 byte-identical determinism (PRD §V8):
  - Report #21 main response hash = `sha256(sorted JSON)` (V8 invariant)
  - PDF binary hash = `sha256(pdf_bytes)` (PDF generation determinism)
  - 2 hash functions: `compute_report21_hash` + `compute_report_pdf_hash`
- A30 PDF generator parity: Report #15 + Report #21 share `generate_report_pdf(*, request, rows)` factory (Discriminated union `report_id` literal)

### AC #8 — A19 cohesion pattern 8 surface (9-4 EXTENSION 누적, `pdf_generator.py` 동일 surface)

- `packages/services/m5_reports/pdf_generator.py` NEW (A19 cohesion pattern 8 surface, 9-1 + 9-2 + 9-3 + **9-4** EXTENSION)
- AD-5 stdlib-only: `decimal, dataclasses, hashlib, io, typing, __future__` only (PDF byte composition reading existing PDF + `reportlab` 3rd party lib 1개, kernel pure helper stdlib-only, PDF composition is service layer)
- M5 reports module wire: `apps/api/modules/m5_reports/` (현재 empty, 9-4 wire = 첫 진입점)

## Tasks / Subtasks

### T1 — Backend pure kernel EXTENSION (`packages/cost_engine/abc_engine.py` 9-3 surface 누적)

- [ ] 1.1 `packages/cost_engine/abc_engine.py` EXTENSION (9-4 surface 누적, A19 cohesion pattern 7 surface)
  - **Report #21 hash determinism**:
    - 1 pure function: `compute_report21_hash(*, cost_object_breakdown: list[CostObjectRow], unused_capacity_breakdown: list[UnusedCapacitySubRow], period_key: str, v7_verdict: V7Verdict) -> str`
    - 1 frozen dataclass: `Report21Summary(product_count: int, total_allocated_krw: Decimal, total_unused_krw: Decimal, hash: str)`
    - 1 typed exception: `Report21InconsistentStateError` (HTTP 422 REPORT21_INCONSISTENT_STATE)
  - **PDF byte-equality determinism**:
    - 1 pure function: `compute_report_pdf_hash(*, pdf_bytes: bytes) -> str` (V8 byte-identical)
    - 1 constant: `REPORT_PDF_HASH_PREFIX: Final[str] = "sha256:"`
  - AD-5 stdlib-only (9-1 + 9-2 + 9-3 + 9-4 동일 surface, NO cross-import)
- [ ] 1.2 `packages/cost_engine/__init__.py` EXTENSION (2 NEW frozen dataclass exports: `Report21Summary` + `Report21InconsistentStateError`)
- [ ] 1.3 `tests/cost_engine/test_abc_engine_report21.py` NEW ~32 cases (compute_report21_hash × 8 + Report21Summary × 6 + Report21InconsistentStateError × 4 + compute_report_pdf_hash × 6 + frozen dataclass × 8)
- [ ] 1.4 `tests/cost_engine/test_abc_engine_no_io_imports.py` EXTENSION (NEW 6 cases: stdlib whitelist EXTENSION pdf_generator)

### T2 — A30 SHARED PDF generator service layer (`packages/services/m5_reports/pdf_generator.py`)

- [ ] 2.1 `packages/services/m5_reports/pdf_generator.py` NEW (A19 cohesion pattern 8 surface, A30 SHARED factory)
  - 1 frozen dataclass: `ReportPdfRequest(report_id: Literal[15, 16, 17, 18, 19, 20, 21], tenant_id: str, period_key: str, include_krw_usd: bool, locale: str, page_size: Literal["A4"])`
  - 1 frozen dataclass: `ReportPdfResult(pdf_bytes: bytes, sha256: str, generated_at: datetime, page_count: int, hash: str)`
  - 1 typed exception: `ReportPdfGenerationError` (HTTP 500 REPORT_PDF_GENERATION_ERROR)
  - 1 main function: `generate_report_pdf(*, request: ReportPdfRequest, rows: list[ReportRow]) -> ReportPdfResult` (AD-5 stdlib-only + A4 인쇄 최적화)
  - 2 constants: `PDF_HASH_PREFIX = "sha256:"` + `REPORT_PDF_LOCALES = ("ko-KR", "en-US")`
  - PDF byte composition: `reportlab` Python lib 사용 (PRD §9 공통 규격 A4 인쇄 최적화 PDF/A 호환)
  - 격자 + 헤더/푸터 + 페이지 번호 + KST 생성 시각
- [ ] 2.2 `packages/services/m5_reports/__init__.py` EXTENSION (SHARED `generate_report_pdf` + `ReportPdfRequest` re-export)
- [ ] 2.3 `tests/cost_engine/test_report21_hash_determinism.py` NEW V8 byte-identical (6 cases: Report #21 + PDF byte hash)
- [ ] 2.4 `tests/services/test_m5_reports_pdf_generator.py` NEW ~24 cases (Request × 4 + Result × 4 + generate_report_pdf × 8 + typed exception × 4 + locale list × 4)

### T3 — M5 reports service layer `Report21Service` (CR 1.1 audit-first + V7 balance)

- [ ] 3.1 `apps/api/modules/m5_reports/services/report21_service.py` NEW
  - `Report21Service.build_report21(*, tenant_id: UUID, period_key: str, include_krw_usd: bool, year_over_year: bool) -> Report21Response` NEW method
  - `_to_report21_state(*, snapshot: FiscalPeriodSnapshot, cost_object_breakdown: list[CostObjectRow], unused_capacity_breakdown: list[UnusedCapacitySubRow], v7_verdict: V7Verdict, currency_pair: CurrencyPair) -> Report21Response` ORM→kernel boundary (CR 12-1 L3 precedent, 9-3 `_to_abc_allocation_state` 패턴 미러)
  - LAZY Verdict imports (circular import 방지 — `from apps.api.core.verdict import Verdict, VerdictStatus` inside method body)
- [ ] 3.2 `apps/api/modules/m5_reports/services/__init__.py` EXTENSION (Report21Service export)
- [ ] 3.3 `apps/api/modules/m5_reports/exceptions.py` EXTENSION (4 NEW typed exceptions: `Report21PeriodNotCommittedError` + `Report21NoCostObjectBreakdownError` + `Report21BreakdownNotFoundError` + `Report21InconsistentStateError` + 4 Korean SSOT)
- [ ] 3.4 `apps/api/modules/m5_reports/schemas.py` EXTENSION (NEW Pydantic models for `Report21Response` + `Report21Row` + `UnusedCapacityRow` + `CurrencyPair` + `V7BalanceResult` + `ReportPdfRequest` + `ReportPdfResponse`)
- [ ] 3.5 `apps/api/main.py` EXTENSION (4 NEW envelope handlers: 422 REPORT21_PERIOD_NOT_COMMITTED + 422 REPORT21_NO_COST_OBJECT_BREAKDOWN + 404 REPORT21_BREAKDOWN_NOT_FOUND + 500 REPORT_PDF_GENERATION_ERROR — CR 12-5 D-14 verbatim)
- [ ] 3.6 `packages/services/m5_reports/__init__.py` EXTENSION (re-export `Report21Service`, 9-2 re-export 패턴 미러)
- [ ] 3.7 `tests/services/test_m5_reports_report21_service.py` NEW ~18 cases (build_report21 × 6 + _to_report21_state × 4 + audit-first × 2 + deleted-period × 2 + V7 balance guard × 2 + unused capacity)
- [ ] 3.8 `tests/architecture/test_api_calls_only_ports.py` EXTENSION (ALLOWED_SERVICE_SUBMODULES 그대로 보존 — Report21Service는 M5 reports service layer ONLY)

### T4 — M5 reports HTTP handlers (`apps/api/modules/m5_reports/handlers.py`)

- [ ] 4.1 `apps/api/modules/m5_reports/handlers.py` NEW
  - `GET /api/v1/reports/21` endpoint (read-only, AC #4 verbatim)
  - `POST /api/v1/reports/21/pdf` endpoint (PDF export, AC #5 verbatim)
  - Capability dual-route gate: `Depends(require_any_capability(Capability.COST_CALCULATION, Capability.ABC_CALCULATION))` (9-3 wire ANY-OF 그대로 재사용)
  - Role gate: `require_role("owner")` (export 권한)
  - 응답 헤더: `Content-Disposition: attachment; filename="report-21-{tenant_id}-{period_key}.pdf"` (PDF export)
- [ ] 4.2 `apps/api/modules/m5_reports/__init__.py` EXTENSION (router export)
- [ ] 4.3 `apps/api/main.py` EXTENSION (M5 reports router 등록)
- [ ] 4.4 `tests/api/test_m5_reports_handlers.py` NEW ~14 cases (GET /api/v1/reports/21 × 6 + POST /api/v1/reports/21/pdf × 4 + capability gate × 2 + envelope × 2)

### T5 — Frontend RSC + 4 NEW components + 2 TS mirrors + ko-KR.json SSOT (CR 11-4 lessons applied)

- [ ] 5.1 `apps/web/app/[locale]/(dashboard)/reports/report-21/page.tsx` NEW RSC (CR 11-4 D-001 mounts `<Report21Panel>` JSX)
- [ ] 5.2 `apps/web/components/m5-reports/Report21Panel.tsx` NEW (main Client Component, Form + display + PDF export button)
- [ ] 5.3 `apps/web/components/m5-reports/Report21CostObjectBreakdownTable.tsx` NEW (product_id별 행 + 4컬럼 + KRW/USD toggle)
- [ ] 5.4 `apps/web/components/m5-reports/Report21UnusedCapacityAccordion.tsx` NEW (부서별 미사용능력 행 펼침/접힘)
- [ ] 5.5 `apps/web/components/m5-reports/Report21PdfExportButton.tsx` NEW (PDF 내보내기 trigger)
- [ ] 5.6 `apps/web/components/m5-reports/index.ts` EXTENSION (4 NEW component exports)
- [ ] 5.7 `apps/web/lib/report21.ts` NEW TS mirror (Report21Response + Report21Row + CurrencyPair + V7BalanceResult + 4 type guards, CR 11-4 D-005 unknown state reject)
- [ ] 5.8 `apps/web/lib/report21-pdf.ts` NEW TS validation schema (ReportPdfRequest + ReportPdfResult mirrors + discriminated union `report_id: Literal[15, 16, 17, 18, 19, 20, 21]`)
- [ ] 5.9 `apps/web/messages/ko-KR.json` EXTENSION `report21` namespace ~37 strings SSOT (CR 11-4 D-002) + `pdf_common` namespace 12 strings (A30 SHARED SSOT)
- [ ] 5.10 `apps/web/__tests__/lib/report21-parity.test.ts` NEW ~28 cases (cross-language parity: Report21Response × 8 + CurrencyPair × 4 + V7BalanceResult × 4 + ReportPdfRequest × 4 + types × 8)
- [ ] 5.11 `apps/web/__tests__/components/m5-reports/Report21CostObjectBreakdownTable.test.tsx` NEW ~12 cases (KRW/USD toggle × 4 + row expansion × 4 + year-over-year × 4)
- [ ] 5.12 `apps/web/__tests__/components/m5-reports/Report21UnusedCapacityAccordion.test.tsx` NEW ~10 cases (expand/collapse × 4 + 부서별 rows × 4 + error state × 2)
- [ ] 5.13 `apps/web/__tests__/components/m5-reports/Report21PdfExportButton.test.tsx` NEW ~8 cases (PDF download trigger × 4 + error state × 2 + disabled state × 2)
- [ ] 5.14 `apps/web/e2e/report-21-pdf-export.spec.ts` NEW ~6 scenarios (Playwright E2E, 1차 smoke only) — **D-9-4-DEFER-4로 honestly DEFER (subsequent E2E coverage)**

### T6 — Capability matrix v1.20 EXTENSION (CR 12-1 L4 precedent variadic helper reuse)

- [ ] 6.1 `docs/capability-matrix.md` EXTENSION (v1.20 changelog entry, NO new capability, capability matrix 변경 0 — `require_any_capability` 9-3 wire 그대로 재사용)
- [ ] 6.2 `tests/integration/test_capability_matrix_v1_20_drift.py` NEW 7 cases (v1.20 markers + Report21Service capability reuse 검증)

### T7 — Docs + architecture + ADR extension

- [ ] 7.1 `docs/abc-report-21.md` NEW (~280 lines, 9 sections, PRD §9 #21 + §7.3 + §A6/A9/V7/V8 verbatim SSOT)
  - §1 Overview (Report #21 vs PRD §9 #21 verbatim)
  - §2 Cost Object Breakdown 본문 (product_id별 행 + 4컬럼 매트릭스)
  - §3 Unused Capacity Full Breakdown (D-9-3-DEFER-3 해소, department별 행)
  - §4 KRW/USD 동시 표시 (PRD §F5.2)
  - §5 A30 SHARED PDF Generator (Report #21 + Report #15 factory pattern)
  - §6 Capability dual-route + Role gate (CR 12-1 L4 precedent)
  - §7 V7 balance + V8 determinism invariants
  - §8 Wire contract (9-4 = Report #21 + SHARED PDF generator, A30 forward-lock)
  - §9 Cross-references (9-4)
- [ ] 7.2 `docs/architecture-inventory.md` EXTENSION §9.4 NEW (130+ lines)
  - 모듈 구조 9-4 EXTENSION (M5 reports module 첫 진입점)
  - Pure kernel EXTENSION (9-4 surface A19 cohesion pattern 7)
  - A30 SHARED PDF generator factory pattern (Report #21 + Report #15)
  - Wire contract (9-4 = Report #21, A30 forward-lock)
  - Cross-references (9-4)
- [ ] 7.3 `docs/conventions.md` EXTENSION §6.12 NEW (M5 reports dual-route rule + A30 SHARED PDF generator convention) + §6.13 NEW (PDF byte-equality determinism + V8 hash prefix)
- [ ] 7.4 `docs/architecture-decisions/AD-19-endpoint-dispatch.md` EXTENSION (Change history entry: 2026-08-17 Story 9.4 A30 forward-lock SHARED PDF generator 결정)
- [ ] 7.5 `docs/capability-matrix.md` EXTENSION (v1.20 changelog entry, NO new capability row)
- [ ] 7.6 `docs/deferred-work.md` EXTENSION D-9-4-DEFER-1~4

### T8 — sprint-status sync + handoff memory

- [ ] 8.1 `_bmad-output/implementation-artifacts/sprint-status.yaml`: `9-4` → `ready-for-dev` + comprehensive dev-wire note
- [ ] 8.2 handoff memory: `handoff-2026-08-17-9-4-spec-ready.md` (spec entry DONE, A30 forward-lock 결정 일정 wire)
- [ ] 8.3 `MEMORY.md` EXTENSION (added handoff-2026-08-17-9-4-spec-ready entry under Epic 9 section)

### T9 — 3중 게이트 final clean (TBD at dev-story 진입)

- [ ] 9.1 **ruff check** (final scope): 0 NEW for 9-4 files (pre-existing baseline 11 UP042 + 9-3 cycle 4 + 9-2 cycle 5 + 9-1 cycle 5 = 25 baseline honestly DEFERRED to A22 follow-up)
- [ ] 9.2 **import-linter** verified FINAL CLEAN: `PYTHONPATH=apps:packages:. python -c "from importlinter.cli import import_linter; ..."` → "Contracts: 2 kept, 0 broken."
- [ ] 9.3 **pytest focused**: ~150 NEW passed (T1 32 + T2 24 + T3 18 + T4 14 + T6 7 + V8 6 + 9-4 specific 49)
- [ ] 9.4 **vitest**: ~58 NEW passed (T5.10 28 + T5.11 12 + T5.12 10 + T5.13 8)
- [ ] 9.5 **tsc** (m5-reports files): zero NEW errors

### T10 — Atomic wire close-out + Epic 9 close-out retro 결정 일정

- [ ] 10.1 A31+ 결정 일정 (Epic 9 close-out retro 진입 시점): Report #15 (활동원가 내역서) wire 일정 — A30 SHARED factory 패턴 재사용
- [ ] 10.2 Epic 9 close-out retro 결정 일정 (cj-style 5번째 진입점): 9-4 done 진입 후 retro 실행
- [ ] 10.3 partial wire 시도 0건 + single sprint atomic wire T1~T10 (cj-style atomic discipline)
- [ ] 10.4 handoff memory: `handoff-2026-08-17-9-4-done.md` (T1~T10 atomic wire, 4 honestly DEFER, A31+ forward-lock 결정 일정)

## Dev Notes

### Architecture Compliance (AD 정합)

- **AD-5** engine purity: `abc_engine.py` EXTENSION stdlib-only (9-1 + 9-2 + 9-3 + 9-4 동일 surface) + `pdf_generator.py` NEW stdlib-only + reportlab 3rd party lib (service layer PDF composition only)
- **AD-8** Decimal-as-string: 1-Won precision (KRW 정수) + USD 소수 2자리 (PRD §9 공통 규격)
- **AD-11** layer rule: ui → api → services → ports → engine — 9-4 = M5 reports service layer → kernel (M5 reports read-only compute path, AD-19 + AD-20 verbatim)
- **AD-15** cross-language conventions: Decimal-as-string (AD-8) / ko-KR SSOT / no I/O in pure kernel / hash byte-identical — 9-1 + 9-2 + 9-3 + 9-4 동일
- **AD-16** fiscal snapshot contract: `fiscal_period_snapshots` uniquely keyed by `(tenant_id, period_key, segment_id, engine_type)` (9-3 wire cost_object_breakdown + unused_capacity_breakdown JSONB 재사용)
- **AD-18** single product identity: `PRODUCT(product_id)` SSOT (epics.md 9.4 AC product_id별 행 정합)
- **AD-19** single endpoint: GET /api/v1/reports/21 + POST /api/v1/reports/21/pdf (M5 reports read-only, 9-4 wire 정합)
- **AD-20** calculation state machine: only `committed` snapshots visible (M5 reports read-only compute path)
- **AD-21** `CCRPort.compute` 단일 소유 (9-2 wire 보존, 9-4 변경 0)
- **AD-22** ledger append-only: Report #21 read-only (no INSERT, only SELECT from fiscal_period_snapshots)

### A30 forward-lock dual-report PDF generator 결정 (9-2 → 9-3 → 9-4 wire)

- **A30 결정 wire (9-4 spec 진입 시점)**:
  - **Report #21** (Cost Object Breakdown, 본 story) + **Report #15** (활동원가 내역서, 향후 진입) = SHARED `packages/services/m5_reports/pdf_generator.py` factory pattern
  - 결정 근거:
    - Report #21 + Report #15 모두 §9 공통 규격 (한·영 + KRW·USD + A4 인쇄 + PDF 내보내기) 충족
    - Discriminated union `ReportPdfRequest.report_id: Literal[15, 16, 17, 18, 19, 20, 21]`로 7개 보고서 PDF generator 확장 가능
    - 9-4 wire = `report_id=21` member 1개 + Report #15 wire 시 `report_id=15` member 1개 추가 (factory pattern 그대로 reuse)
- **D-9-3-DEFER-1 Report #21 PDF export 해소** (T2 + T4 + T5 wire)
- **D-9-3-DEFER-3 Unused capacity full breakdown 해소** (T3 wire)
- **Report #15 entry 결정 일정**: A31+ 결정 (Epic 9 close-out retro 진입 시점)

### A19 cohesion pattern 8 surface (A26 Option A 채택 정합)

- `packages/cost_engine/abc_engine.py` 9-1 + 9-2 + 9-3 + **9-4** EXTENSION (A19 cohesion pattern 7 surface, A26 Option A)
- `packages/services/m5_reports/pdf_generator.py` NEW (A19 cohesion pattern 8 surface, A30 SHARED factory)
- AD-21: M9 service layer ONLY CCRPort.compute 단일 소유 (9-4 변경 0)
- Cross-import 0건 (9-2 + 9-3 + 9-4 동일 surface)

### CR 11-3 honest-DEFER discipline 20번째 epic 연속 (Epic 9 4번째 진입점)

- 4 honestly DEFER (모두 structural W-class):
  - **D-9-4-DEFER-1**: epics.md "원가대상별 원가 집계표" vs PRD §9 #21 "부문귀속명세서" 정합 (PDF 라벨 + UX 표기 결정 필요) → Epic 9 close-out follow-up
  - **D-9-4-DEFER-2**: Report #15 (활동원가 내역서) wire = A30 SHARED factory 패턴 재사용 entry → A31+ 결정 (Epic 9 close-out retro 진입 시점)
  - **D-9-4-DEFER-3**: AI 자동 분석의견 (PRD §9 #16 + §A11 + §10) → 9-4 follow-up (cj-style Report #21 본문 + Unused capacity + PDF export 우선)
  - **D-9-4-DEFER-4**: Playwright E2E (12-5 T6 pattern) — 9-4 wire는 1차 smoke only (T5.14 6 scenarios), full E2E coverage Epic 9 close-out follow-up (A27 결정)

### CR 11-4 lessons carry (D-001/D-002/D-005/P-015)

- D-001: page.tsx actual mount `<Report21Panel>` JSX MUST (5.1 wire)
- D-002: ko-KR.json SSOT only (5.9 wire, `report21` namespace 37 + `pdf_common` namespace 12 strings)
- D-005: TS mirror unknown state reject (5.7 + 5.8 wire, Report21Response + ReportPdfRequest type guards)
- P-015: ko-KR.json SSOT drift detector (T6.2 wire, v1.20 markers)

### CR 12-1 lessons continue

- L3: `_to_report21_state` ORM→kernel boundary (T3.1 wire, 9-3 `_to_abc_allocation_state` 패턴 미러)
- L4: `require_any_capability` Industry-agnostic precedent (T4.1 wire, 9-3 ANY-OF 그대로 재사용)
- variadic helper 9-3 wire 그대로 재사용, capability matrix 변경 0

### CR 12-5 lessons continue

- D-13: cross-language drift detector 10+ vectors (T6 wire + 12 NEW tests)
- D-14: typed exception main.py envelope REUSE 0 NEW handlers (T3.5 wire, 4 NEW envelope handlers per exception)
- L3: 3-layer defense (route guard + service guard + validation guard for fiscal_period_snapshots read-only state)
- L4: honest-DEFER discipline 4 items (D-9-4-DEFER-1~4)

### A19 lessons carry (math surface migration pattern)

- A19 cohesion pattern 8 surface 분리 검증 (9-1 + 9-2 + 9-3 + 9-4 동일 surface `abc_engine.py`)
- A26 Option A 채택 정합 (cross-import 0건)
- A19 lessons: math surface migration + carry-over sprint pattern + build_inventory_projection runtime migration + TS mirror dead code + architecture test ALLOWED sweep

### Read files being modified (CRITICAL per workflow step 3)

- `packages/cost_engine/abc_engine.py` (9-1 + 9-2 + 9-3 EXTENSION 보존, 9-4 EXTENSION)
- `packages/cost_engine/__init__.py` (9-1 + 9-2 + 9-3 EXTENSION 보존, 9-4 EXTENSION)
- `apps/api/core/capability.py` (9-3 wire `require_any_capability` 보존, 9-4 변경 0)
- `apps/api/main.py` (9-1 + 9-3 envelope handlers 보존, 9-4 EXTENSION 4 NEW handlers)
- `apps/api/modules/m3_calculate/handlers.py` (9-3 wire 보존, 9-4 변경 0)
- `apps/api/modules/m3_calculate/schemas.py` (9-3 wire 보존, 9-4 변경 0)
- `apps/api/modules/m9_abc/services/abc_allocation_service.py` (9-2 + 9-3 EXTENSION 보존, 9-4 변경 0)
- `apps/api/alembic/versions/0028_abc_fiscal_period_breakdown.py` (9-3 wire 보존, 9-4 변경 0)
- `docs/architecture-decisions/AD-19-endpoint-dispatch.md` (9-3 wire EXTENSION 보존, 9-4 EXTENSION)

### A story implementation must leave the system working end-to-end — not just satisfy its stated ACs

- 9-4 wire = Report #21 + SHARED PDF generator (M5 reports 첫 진입점, e2e 작동)
- GET /api/v1/reports/21 + POST /api/v1/reports/21/pdf endpoints callable
- Frontend RSC mounts `<Report21Panel>` + 4 components wire
- PDF export end-to-end (Request → service → factory → bytes → response)
- 9-4 wire 변경 scope: pure kernel EXTENSION (abc_engine.py) + NEW service layer (pdf_generator.py) + NEW M5 reports service (report21_service.py) + NEW M5 reports handlers + Frontend RSC + 4 components + 2 TS mirrors + ko-KR.json SSOT
- 9-2 + 9-3 wire 변경 0 (forward-lock 보존)

## Project Structure Notes

### NEW files (9-4 wire 표)

- `packages/cost_engine/abc_engine.py` EXTENSION → 9-4 surface (4 NEW funcs + 1 NEW dataclass + 1 NEW typed exception + 1 NEW constant)
- `packages/cost_engine/__init__.py` EXTENSION (2 NEW exports)
- `packages/services/m5_reports/pdf_generator.py` NEW (A19 cohesion pattern 8 surface, A30 SHARED factory)
- `packages/services/m5_reports/__init__.py` EXTENSION (SHARED generate_report_pdf re-export)
- `apps/api/modules/m5_reports/__init__.py` NEW (M5 reports module 첫 진입점)
- `apps/api/modules/m5_reports/handlers.py` NEW (GET /api/v1/reports/21 + POST /api/v1/reports/21/pdf)
- `apps/api/modules/m5_reports/schemas.py` NEW (Report21Response + ReportPdfRequest + Pydantic v2 models)
- `apps/api/modules/m5_reports/services/__init__.py` NEW (Report21Service export)
- `apps/api/modules/m5_reports/services/report21_service.py` NEW (CR 12-1 L3 ORM→kernel boundary)
- `apps/api/modules/m5_reports/exceptions.py` NEW (4 NEW typed exceptions + 4 Korean SSOT)
- `apps/web/app/[locale]/(dashboard)/reports/report-21/page.tsx` NEW RSC
- `apps/web/components/m5-reports/Report21Panel.tsx` + `Report21CostObjectBreakdownTable.tsx` + `Report21UnusedCapacityAccordion.tsx` + `Report21PdfExportButton.tsx` NEW (4 components)
- `apps/web/components/m5-reports/index.ts` EXTENSION (4 NEW exports)
- `apps/web/lib/report21.ts` + `report21-pdf.ts` NEW (2 TS mirrors)
- `tests/cost_engine/test_abc_engine_report21.py` NEW (~32 cases)
- `tests/cost_engine/test_report21_hash_determinism.py` NEW V8 byte-identical (6 cases)
- `tests/cost_engine/test_abc_engine_no_io_imports.py` EXTENSION (6 NEW cases)
- `tests/services/test_m5_reports_pdf_generator.py` NEW (~24 cases)
- `tests/services/test_m5_reports_report21_service.py` NEW (~18 cases)
- `tests/api/test_m5_reports_handlers.py` NEW (~14 cases)
- `tests/integration/test_capability_matrix_v1_20_drift.py` NEW (7 cases)
- `apps/web/__tests__/lib/report21-parity.test.ts` NEW (~28 cases)
- `apps/web/__tests__/components/m5-reports/Report21CostObjectBreakdownTable.test.tsx` + `Report21UnusedCapacityAccordion.test.tsx` + `Report21PdfExportButton.test.tsx` NEW (3 components, ~30 cases)
- `apps/web/e2e/report-21-pdf-export.spec.ts` NEW (Playwright E2E 1차 smoke 6 scenarios)
- `docs/abc-report-21.md` NEW (~280 lines)
- `docs/abc-report-21-architecture.md` NEW (architecture 9-4 surface)

### MODIFIED files (9-4 wire EXTENSION)

- `apps/api/main.py` EXTENSION (4 NEW envelope handlers + M5 reports router 등록)
- `packages/cost_engine/__init__.py` EXTENSION (2 NEW exports)
- `docs/architecture-inventory.md` EXTENSION §9.4 NEW (130+ lines)
- `docs/conventions.md` EXTENSION §6.12 + §6.13 NEW
- `docs/architecture-decisions/AD-19-endpoint-dispatch.md` EXTENSION (A30 forward-lock SHARED PDF generator section)
- `docs/capability-matrix.md` EXTENSION (v1.20 changelog entry)
- `docs/deferred-work.md` EXTENSION D-9-4-DEFER-1~4
- `apps/web/messages/ko-KR.json` EXTENSION (`report21` namespace 37 + `pdf_common` namespace 12 strings)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (9-4 status backlog → ready-for-dev)

### UNCHANGED files (9-4 wire scope 외부)

- `apps/api/modules/m3_calculate/handlers.py` (9-3 wire 보존, 9-4 변경 0)
- `apps/api/modules/m3_calculate/schemas.py` (9-3 wire 보존, 9-4 변경 0)
- `apps/api/modules/m9_abc/services/abc_allocation_service.py` (9-2 + 9-3 EXTENSION 보존, 9-4 변경 0)
- `apps/api/alembic/versions/0026_abc_engine_first_revision.py` (9-1 wire 보존, 9-4 변경 0)
- `apps/api/alembic/versions/0027_budget_pre_standard.py` (8-3 wire 보존, 9-4 변경 0)
- `apps/api/alembic/versions/0028_abc_fiscal_period_breakdown.py` (9-3 wire 보존, 9-4 변경 0)
- `packages/cost_engine/abc_engine.py` (9-1 + 9-2 + 9-3 EXTENSION 보존, 9-4 EXTENSION만 추가)
- `apps/api/core/capability.py` (9-3 wire `require_any_capability` 보존, 9-4 변경 0)

## References

### PRD verbatim source

- §9 #21 ("부문귀속명세서, 카브아웃 근거 공시, §7.3") — dept selection source
- §7.3 (법인세법 시행규칙 제76조 2기준, 부문 카브아웃) — split basis
- §9 공통 규격 (한·영 + KRW·USD + A4 인쇄 + PDF 내보내기 + 격식체 서술)
- §F5.2 (KRW/USD 동시 표시)
- §A6 (완전배부·대차평형 1원 단위)
- §A9 (미사용능력 별도 관리)
- §A11 (오류의 가시화)
- §V7 (ABC 무결성)
- §V8 (V8 byte-identical determinism)
- §15 (Non-Goal: 통합된 단일 보고서 PDF/A 최적화 라이브러리 아님 — `reportlab` 3rd party 사용 결정)

### Architecture verbatim source

- AD-5 (engine purity, stdlib-only)
- AD-8 (Decimal-as-string, 1-Won precision)
- AD-11 (layer rule)
- AD-15 (cross-language conventions)
- AD-16 (fiscal snapshot contract)
- AD-18 (single product identity)
- AD-19 (single endpoint)
- AD-20 (calculation state machine)
- AD-21 (CCRPort.compute 단일 소유)
- AD-22 (ledger append-only)

### Epic 9 source (epics.md lines 1050-1060 verbatim)

```
#### Story 9.4: ABC Report #21 (Cost Object Breakdown)

As a 사장님, I want §9 #21 "원가대상별 원가 집계표"가 ABC 결과를 보여주는 것, so that 여행상품/물류 서비스별 원가 구조를 확인.

Acceptance Criteria:

- Given 나는 [보고서] → [원가대상별 원가 집계표] 클릭
- When 서비스 업종 테넌트에서 진입
- Then product_id(원가대상)별 행 + 원가풀·활동·동인·배부액 4컬럼 표시
- And 제조업 테넌트에서는 engine_type='trad'만 표시되고 ABC 컬럼은 회색("비활성")
- And KRW/USD 동시 표시 (F5.2)
```

### Story 9.3: ABC Calculation Routed via M3 Endpoint

- `_bmad-output/implementation-artifacts/9-3-abc-calculation-routed-via-m3-endpoint.md` (9-3 spec)
- `handoff-2026-08-17-9-3-done.md` (9-3 T10 close-out)
- `packages/cost_engine/abc_engine.py` (9-3 surface EXTENSION, 9-4 wire 동일 surface)
- `apps/api/alembic/versions/0028_abc_fiscal_period_breakdown.py` (9-3 wire, 9-4 cost_object_breakdown + unused_capacity_breakdown JSONB 재사용)

### Related handoffs (in-process)

- `handoff-2026-08-16-9-2-done.md` (9-2 atomic wire T1~T8 done)
- `handoff-2026-08-17-9-3-done.md` (9-3 atomic wire T1~T10 done)
- `handoff-2026-08-16-9-1-done.md` (9-1 atomic wire T1~T8 done)

### 9-3 files to read (for 9-4 wire consistency)

- `packages/cost_engine/abc_engine.py` (9-3 surface EXTENSION, 9-4 EXTENSION 동일 surface)
- `apps/api/core/capability.py` (9-3 wire `require_any_capability` ANY-OF)
- `apps/api/modules/m3_calculate/handlers.py` (9-3 wire capability dual-route gate pattern)
- `apps/api/modules/m3_calculate/schemas.py` (9-3 wire discriminated union envelope pattern)
- `apps/api/modules/m9_abc/services/abc_allocation_service.py` (9-3 wire 11-step pipeline + CR 12-1 L3 boundary)
- `apps/api/alembic/versions/0028_abc_fiscal_period_breakdown.py` (9-3 wire JSONB persistence)
- `apps/web/components/m9-abc/AbcDispatchPanel.tsx` (9-3 wire component pattern, 9-4 Report21Panel 미러)
- `apps/web/lib/m9-abc-dispatch.ts` (9-3 wire TS mirror pattern, 9-4 report21.ts 미러)

## Dev Agent Record

### 결정 사항 (locked at spec 진입)

- **A30 forward-lock 결정 (9-4 spec 진입 시점)**:
  - Report #21 + Report #15 = SHARED `pdf_generator.py` factory pattern (Discriminated union `report_id: Literal[15, 16, 17, 18, 19, 20, 21]`)
  - 결정 근거: 두 보고서 모두 §9 공통 규격 (한·영 + KRW·USD + A4 인쇄 + PDF 내보내기) 충족
  - 9-4 wire = Report #21 + SHARED factory (9-4 본 story 범위)
  - Report #15 wire = A31+ 결정 (Epic 9 close-out retro 진입 시점)
- **epics.md vs PRD §9 #21 정합**:
  - epics.md 9.4 = "원가대상별 원가 집계표" (Cost Object Breakdown)
  - PRD §9 #21 verbatim = "부문귀속명세서 (카브아웃 근거 공시)"
  - 결정: 9-4 wire = 합성 scope (PRD §9 #21 SSOT + epics.md 9.4 product_id별 행 extension), 정합 차이 D-9-4-DEFER-1 honestly DEFER
- **PDF library**: `reportlab` Python 3rd party lib 사용 (PRD §9 A4 인쇄 최적화 PDF/A 호환)
- **Pure kernel EXTENSION**: 동일 surface `abc_engine.py` (9-1 + 9-2 + 9-3 + 9-4, A19 cohesion pattern 7)
- **SHARED factory**: `packages/services/m5_reports/pdf_generator.py` NEW (A19 cohesion pattern 8 surface)
- **M5 reports module**: `apps/api/modules/m5_reports/` (현재 empty, 9-4 wire = 첫 진입점)

### 변경 통계 (10 tasks atomic wire)

- 26 NEW + 9 MODIFIED = ~35 files (target)
- pytest focused ~150 NEW + vitest ~58 NEW + tsc zero NEW
- 4 honestly DEFER per CR 11-3 20번째 epic 연속

### Critical files (locked at spec 진입)

- `packages/cost_engine/abc_engine.py` (9-3 surface EXTENSION, 9-4 EXTENSION 동일 surface)
- `packages/services/m5_reports/pdf_generator.py` NEW (A30 SHARED factory)
- `apps/api/modules/m5_reports/services/report21_service.py` NEW (CR 12-1 L3 ORM→kernel boundary)
- `apps/api/modules/m5_reports/handlers.py` NEW (GET /api/v1/reports/21 + POST /api/v1/reports/21/pdf)
- `apps/web/app/[locale]/(dashboard)/reports/report-21/page.tsx` NEW RSC

### Completion Notes (2026-08-17, T1~T10 atomic wire TBD — 다음 세션 wire 진입)

#### T1 — Backend pure kernel EXTENSION (TBD at dev-story 진입)

- **2 NEW frozen dataclasses** in `packages/cost_engine/abc_engine.py`:
  `Report21Summary`, `Report21InconsistentStateError` (cumulative: 9-1 3 + 9-2 5 + 9-3 5 + 9-4 2 = 15 frozen dataclasses total
  in surface 7).
- **2 NEW pure functions**: `compute_report21_hash` + `compute_report_pdf_hash`.
- **1 NEW constant**: `REPORT_PDF_HASH_PREFIX="sha256:"`.
- **~32 NEW pytest cases** (T1.3 + T1.4 + T1.5).

#### T2 — A30 SHARED PDF generator service layer (TBD)

- `packages/services/m5_reports/pdf_generator.py` NEW (A19 cohesion pattern 8 surface).
- 1 frozen dataclass: `ReportPdfRequest` (Discriminated union `report_id: Literal[15, 16, 17, 18, 19, 20, 21]`).
- 1 frozen dataclass: `ReportPdfResult`.
- 1 typed exception: `ReportPdfGenerationError`.
- 1 main function: `generate_report_pdf` (AD-5 stdlib-only + reportlab 3rd party).
- 2 constants: `PDF_HASH_PREFIX` + `REPORT_PDF_LOCALES`.
- **~24 NEW pytest cases** (T2.4).

#### T3 — M5 reports service layer `Report21Service` (TBD)

- `apps/api/modules/m5_reports/services/report21_service.py` NEW (`build_report21` method + `_to_report21_state` CR 12-1 L3 ORM→kernel boundary + LAZY Verdict imports).
- `apps/api/modules/m5_reports/exceptions.py` NEW (4 NEW typed exceptions + 4 Korean SSOT).
- `apps/api/main.py` EXTENSION (4 NEW envelope handlers: 422 REPORT21_PERIOD_NOT_COMMITTED + 422 REPORT21_NO_COST_OBJECT_BREAKDOWN + 404 REPORT21_BREAKDOWN_NOT_FOUND + 500 REPORT_PDF_GENERATION_ERROR).
- **~18 NEW pytest cases** (T3.7).

#### T4 — M5 reports HTTP handlers (TBD)

- `apps/api/modules/m5_reports/handlers.py` NEW (GET /api/v1/reports/21 + POST /api/v1/reports/21/pdf).
- Capability dual-route gate: `require_any_capability(Capability.COST_CALCULATION, Capability.ABC_CALCULATION)`.
- Role gate: `require_role("owner")`.
- **~14 NEW pytest cases** (T4.4).

#### T5 — Frontend RSC + 4 components + 2 TS mirrors + ko-KR.json SSOT (TBD)

- 1 NEW RSC `apps/web/app/[locale]/(dashboard)/reports/report-21/page.tsx`.
- 4 NEW Client Components: `Report21Panel` + `Report21CostObjectBreakdownTable` + `Report21UnusedCapacityAccordion` + `Report21PdfExportButton`.
- 2 NEW TS mirrors: `report21.ts` + `report21-pdf.ts`.
- `apps/web/messages/ko-KR.json` EXTENSION (`report21` namespace 37 + `pdf_common` namespace 12 strings SSOT).
- **~58 NEW vitest cases** (T5.10 + T5.11 + T5.12 + T5.13).

#### T6 — Capability matrix v1.20 EXTENSION (TBD)

- `docs/capability-matrix.md` EXTENSION (v1.20 changelog entry, NO new capability).
- **~7 NEW drift detector tests** (T6.2).

#### T7 — Docs + architecture + ADR extension (TBD)

- `docs/abc-report-21.md` NEW (~280 lines, 9 sections).
- `docs/architecture-inventory.md` EXTENSION §9.4 NEW (130+ lines).
- `docs/conventions.md` EXTENSION §6.12 + §6.13 NEW.
- `docs/architecture-decisions/AD-19-endpoint-dispatch.md` EXTENSION A30 forward-lock section.
- `docs/deferred-work.md` EXTENSION D-9-4-DEFER-1~4.

#### T8 — sprint-status sync + handoff memory (TBD)

- `_bmad-output/implementation-artifacts/sprint-status.yaml`: `9-4` → `ready-for-dev`.
- handoff memory: `handoff-2026-08-17-9-4-spec-ready.md`.
- `MEMORY.md` EXTENSION (added handoff entry under Epic 9 section).

#### T9 — 3중 게이트 final clean (TBD)

- **ruff check** (final scope): 0 NEW for 9-4 files (pre-existing baseline 25 honestly DEFERRED to A22 follow-up).
- **import-linter** verified FINAL CLEAN: 2 KEPT contracts.
- **pytest focused**: ~150 NEW passed.
- **vitest**: ~58 NEW passed.
- **tsc** (m5-reports files): zero NEW errors.

#### T10 — Atomic wire close-out + A31+ forward-lock 결정 일정 (TBD)

- **A31+ 결정 일정** (Epic 9 close-out retro 진입 시점): Report #15 wire 일정 + A30 SHARED factory 패턴 재사용 entry.
- **Epic 9 close-out retro** 결정 일정 (cj-style 5번째 진입점): 9-4 done 진입 후.
- **wire scope**: 26 NEW + 9 MODIFIED = ~35 files (target) + cj-style atomic single sprint T1~T10 (no partial wire).
- **handoff memory**: `handoff-2026-08-17-9-4-done.md`.

## Honestly DEFER (CR 11-3 20번째 epic 연속)

| ID | Item | 결정 시점 | Rationale | Structural W-class |
|----|------|-----------|-----------|-------------------|
| **D-9-4-DEFER-1** | epics.md "원가대상별 원가 집계표" vs PRD §9 #21 "부문귀속명세서" 정합 (PDF 라벨 + UX 표기 결정) | Epic 9 close-out follow-up | PRD §9 #21 SSOT + epics.md 9.4 extension 합성 scope, 정합 차이 honestly DEFER | ✅ |
| **D-9-4-DEFER-2** | Report #15 (활동원가 내역서) wire = A30 SHARED factory 패턴 재사용 entry | A31+ 결정 (Epic 9 close-out retro 진입 시점) | 9-4 wire = Report #21 + SHARED factory, Report #15 entry 후속 | ✅ |
| **D-9-4-DEFER-3** | AI 자동 분석의견 (PRD §9 #16 + §A11 + §10) | 9-4 follow-up | cj-style Report #21 본문 + Unused capacity + PDF export 우선, AI 의견 후속 | ✅ |
| **D-9-4-DEFER-4** | Playwright E2E (12-5 T6 pattern) | Epic 9 close-out follow-up (A27 결정) | 9-4 wire는 1차 smoke only (T5.14 6 scenarios), full E2E coverage Epic 9 close-out follow-up | ✅ |

**제외된 candidates** (Epic boundary 외부 또는 PRD §15 Non-Goal verbatim):
- (a) Report #16/#17/#18/#19/#20 wire (Report #21 + SHARED factory 우선, 나머지는 후속)
- (b) Cross-region report export (AD-9 disabled) — Epic boundary 외부
- (c) Multiple PDF 병렬 내보내기 (9-4 = 1 report 1 PDF, 다중 동시 export 2차)

## Status

**Status: ready-for-dev** (2026-08-17, bmad-create-story spec 진입 DONE)

**Final spec summary**:
- A30 forward-lock dual-report PDF generator 결정 wire (Report #21 + Report #15 SHARED factory)
- baseline_commit = `a67951b` (Story 9.3 T10 close-out tip = current HEAD)
- 26 NEW + 9 MODIFIED = ~35 files (target)
- 4 honestly DEFER per CR 11-3 20번째 epic 연속
- 9-3 wire 보존 (변경 0) + 9-2 wire 보존 (변경 0) + 9-1 wire 보존 (변경 0) + Walking Skeleton MVP wire 보존 (변경 0)
- A31+ forward-lock 결정 일정 (Epic 9 close-out retro 진입 시점)
- Epic 9 close-out retro 결정 일정 (9-4 done 진입 후, cj-style 5번째)
