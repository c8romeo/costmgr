# Closing PDF Export (Story 6.3)

> 운영 매뉴얼 — PRD §F6.3 + AD-15 §4 envelope + W5 industry guard

## 1. Overview

**Closing PDF Export** 서비스는 월 마감 보고서(monthly closing report)를
PDF(A4, ≤ 5MB) 형식으로 다운로드할 수 있게 합니다. 회계사·세무사·
금융기관 외부 이해관계자 전달용 산출물입니다.

**진입점:** `POST /api/v1/inventory/monthly-closing-report/export-pdf`

**Capability gate:** `Capability.MONTHLY_CLOSING_REPORT` (6-2 wire 완료)

**Industry guard:** 4 canonical industries (manufacturing /
manufacturing_service / manufacturing_service_other / service) —
service-only tenant은 422 에러.

## 2. Architecture

```
[User clicks Button]
    → ClosingPdfExportButton.tsx (Client Component)
        → fetch('/api/v1/inventory/monthly-closing-report/export-pdf', {industry})
            → handlers.py POST /export-pdf route
                → ClosingPdfExportService.export_closing_pdf
                    1. Industry guard (4 canonical values)
                    2. 4-source read-only join (closing_snapshot + ledger + fiscal_period + monthly_input)
                    3. audit-first emit (CR 1.1) — `monthly_closing_report_viewed`
                    4. PDF render (pure helper — stdlib-only PDF 1.4)
                    5. Return Response(application/pdf)
                → 3 typed exceptions → main.py envelope handlers (422/409/500)
```

## 3. Key Constraints

### 3.1 PDF size cap (PRD §F6.3)

- **MAX_PDF_SIZE_BYTES = 5 × 1024 × 1024** (5 MB hard cap)
- size exceeded → `409 CLOSING_PDF_EXPORT_SIZE_EXCEEDED`
- Korean message: `"PDF 크기 초과: 5MB cap (PRD §F6.3)"`

### 3.2 Industry guard (W5 deferral)

- 4 canonical industries만 허용
- mismatch → `422 CLOSING_PDF_EXPORT_INVALID_INDUSTRY`
- Korean message: `"업종 미지원: 4 canonical industries 중 하나여야 합니다 ..."`

### 3.3 Audit-first invariant (CR 1.1)

- 5-step pipeline에서 **audit emit이 PDF render보다 먼저 실행**
- action: `monthly_closing_report_viewed`
- action_class: `ActionClass.MONTHLY_CLOSING_REPORT`
- audit 실패 → `500 CLOSING_PDF_EXPORT_AUDIT_EMIT_ERROR`

## 4. Korean Labels (SSOT)

| SSOT Surface | Constant | Value |
|---|---|---|
| Python kernel | `CLOSING_PDF_EXPORT_TITLE_KO` | `"마감 보고서 PDF Export"` |
| Python kernel | `CLOSING_PDF_EXPORT_EMPTY_KO` | `"PDF 데이터 없음"` |
| TS mirror | `CLOSING_PDF_EXPORT_TITLE_KO` | `"마감 보고서 PDF Export"` (identical) |
| ko-KR.json | `closing_pdf_export.button_label` | `"PDF 다운로드"` |
| ko-KR.json | `closing_pdf_export.panel_section_help` | `"월 마감 보고서를 PDF(A4, ≤ 5MB)로..."` |

**AD-15 §11 cross-language parity:** 모든 surface에서 label identical.

## 5. Wire Spec

### 5.1 Backend wire

- `packages/services/m4_inventory/closing_pdf_export.py` (pure helper, stdlib-only)
- `apps/api/modules/m4_inventory/services/closing_pdf_export_service.py` (service layer)
- `apps/api/modules/m4_inventory/handlers.py` POST /export-pdf route
- `apps/api/main.py` 3 exception handlers (422/409/500)

### 5.2 Frontend wire

- `apps/web/lib/closing-pdf-export.ts` (TS mirror — AD-15 §11)
- `apps/web/components/m2-input/ClosingPdfExportButton.tsx` (Client Component)
- `apps/web/lib/server-api.ts` `fetchTenantSettingsServerSide` (W5 industry fetch)
- `apps/web/messages/ko-KR.json` `closing_pdf_export` namespace (10 keys)

### 5.3 ko-KR labels surface

- `apps/web/lib/labels-ko.ts` (NEW — Story 6.3 T4 W3 close-out)
- Python `labels_ko.py` SSOT
- `apps/web/messages/ko-KR.json` SSOT

## 6. Tests (T1-T6 close-out)

| Layer | File | Cases |
|---|---|---|
| Pure kernel | `tests/services/m4_inventory/test_closing_pdf_export.py` | 20 |
| Service | `tests/api/m4_inventory/test_closing_pdf_export_service.py` | 6 |
| Envelope | `tests/api/m4_inventory/test_closing_pdf_export_envelope.py` | 4 |
| Parity | `tests/integration/test_closing_pdf_export_label_consistency.py` | 8 |
| ko-KR comprehensive | `tests/integration/test_closing_pdf_export_ko_kr_comprehensive.py` | 8 |
| V8 runner E2E | `packages/cost_engine/tests/regression_v8/test_v8_runner_e2e.py` | 6 |
| Timeline | `tests/integration/test_inline_projection_deprecation_timeline.py` | 7 |
| Action inventory | `tests/integration/test_6_3_action_inventory_preservation.py` | 6 |
| Architecture | `tests/architecture/test_api_calls_only_ports.py` | 3 |
| Vitest | `apps/web/__tests__/closing-pdf-export.test.tsx` | 12 |
| Playwright | `apps/web/e2e/v8-runner.spec.ts` | 4 (skip-if-not-wired) |
| **Total** | | **84 cases** |

## 7. Carry-over / Deferrals

### 7.1 6-2 carry-over close-out (T4 W1-W5)

- W1: `__init__.py` re-export close ✅
- W2: V8 fixture placeholder docstring (Epic 11 close-out 결정) ✅
- W3: panel `formatKrwUsd` → `labels-ko.ts` ✅
- W4: 2 missing test files (V8 runner E2E + Playwright spec) ✅
- W5: `industry='trad'` hard-code docstring ✅

### 7.2 A8 timeline (T5)

- 6-3 wire 시점: inline projection 보존 상태로 wire
- Epic 6 close-out 시점에 fold-in vs deprecate 결정
- Epic 11 reversal 진입 시 inline projection 완전 제거

### 7.3 Epic 12+ 결정 보류

- W2 fixture placeholder regen entrypoint: Epic 11 close-out 후
- W5 industry extension: Epic 12+ 결정

## Cross-Reference

- PRD: §F5 (마감 보고서) + §F5.2 (KRW/USD dual display) + §F6.3 (PDF export)
- AD: AD-15 (cross-language parity) + AD-22 (reversal entrypoint)
- AC: #1 PDF export wire / #2 frontend download flow /
       #3 ko-KR labels / #4 6-2 carry-over close-out /
       #5 capability matrix / #6 A8 timeline / #7 A5+A7+A11+A12 close
- Wire: 6-1 closing-period + 6-2 monthly-closing-report + 6-3 closing-pdf-export