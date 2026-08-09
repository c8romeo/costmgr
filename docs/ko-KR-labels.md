# ko-KR Labels SSOT Guide (Story 6.3)

> ko-KR label SSOT — cross-language parity contract (AD-15 §11)

## 1. SSOT Surfaces

Korean labels live in 4 SSOT surfaces that MUST remain identical:

| Surface | Path | Scope |
|---|---|---|
| Python kernel constants | `packages/services/**/closing_pdf_export.py` | Title / Empty |
| TS mirror constants | `apps/web/lib/closing-pdf-export.ts` | Title / Empty / Industry |
| Python helper functions | `apps/api/core/labels_ko.py` + `packages/cost_engine/labels_ko.py` | Format helpers |
| ko-KR.json namespace | `apps/web/messages/ko-KR.json` | UI strings |

## 2. Cross-Surface Parity Contract (AD-15 §11)

Per AD-15 §11, every Korean label MUST have an identical value across
all 4 SSOT surfaces. The `test_closing_pdf_export_ko_kr_comprehensive.py`
test suite enforces this contract:

- **8 scenarios** validate the 6 surface coherence
- **4 scenarios** validate Python ↔ TS mirror parity
- **2 scenarios** validate industry codes parity (4 canonical)

## 3. Canonical Korean Labels

### 3.1 Closing PDF Export

| Key | Value |
|---|---|
| `CLOSING_PDF_EXPORT_TITLE_KO` | `"마감 보고서 PDF Export"` |
| `CLOSING_PDF_EXPORT_EMPTY_KO` | `"PDF 데이터 없음"` |
| `closing_pdf_export.button_label` | `"PDF 다운로드"` |
| `closing_pdf_export.button_downloading` | `"PDF 생성 중..."` |
| `closing_pdf_export.panel_section_label` | `"PDF Export"` |
| `closing_pdf_export.toast_success_export` | `"PDF 다운로드 완료 ({size})"` |
| `closing_pdf_export.toast_error_invalid_industry` | `"업종 미지원: ..."` |
| `closing_pdf_export.toast_error_size_exceeded` | `"PDF 크기 초과: 5MB cap (PRD §F6.3)"` |
| `closing_pdf_export.toast_error_audit_emit` | `"PDF 저장 audit emit 실패: ..."` |

### 3.2 Error Envelope Messages (AD-15 §4)

- 422: `"업종 미지원: 4 canonical industries 중 하나여야 합니다 ..."`
- 409: `"PDF 크기 초과: 5MB cap (PRD §F6.3)"`
- 500: `"PDF 저장 audit emit 실패: 서버 측 CR 1.1 invariant 위반"`

### 3.3 Industry Codes (4 canonical)

```python
CLOSING_PDF_INDUSTRY_VALUES = [
    "manufacturing",
    "manufacturing_service",
    "manufacturing_service_other",
    "service",
]
```

## 4. Cross-Surface Drift Detector

The `test_closing_pdf_export_ko_kr_comprehensive.py` integration test
runs as part of the 3중 게이트 CI gate. Any drift between surfaces
FAILS the build.

### 4.1 Drift scenarios detected

- Python kernel missing TS mirror constant → drift detected
- TS mirror value ≠ Python value → drift detected
- ko-KR.json namespace key missing → drift detected
- API envelope message_ko not in Korean → drift detected
- Vitest mock map missing key → drift detected
- Service exception not mapped in main.py → drift detected

### 4.2 Why cross-language parity matters

PRD §F6.3 + AD-15 §11 require consistent Korean UX across:
1. Backend PDF generation (rendered text)
2. Frontend button label + toast messages
3. Error envelope responses (422/409/500)

A drift would cause users to see English errors in ko-KR locale,
breaking the WCAG AA + Professional 톤 locked UX decisions.

## 5. labels-ko.ts Helper Module (Story 6.3 W3 close-out)

`apps/web/lib/labels-ko.ts` (NEW) consolidates Korean label formatters:

- `formatKrwUsd(krw, usd)` — KRW/USD dual display (parity with panel)
- `formatClosingPeriodLabelKo(periodKey)` — closing period label
- `formatClosingSnapshotEventLabelKo(count)` — closing snapshot count label
- `formatCurrencyPairKo(pair)` — currency pair label
- `formatOperatorActionKo(action)` — 4-value operator action enum

Constants:
- `CLOSING_PERIOD_LABEL_KO = "마감 기간"`
- `CLOSING_SNAPSHOT_EVENT_LABEL_KO = "마감 스냅샷"`
- `CURRENCY_PAIR_LABEL_KO = "환율 (KRW/USD)"`
- `OPERATOR_ACTION_LABELS_KO` (4-value enum)

## 6. Maintenance Workflow

When adding a new Korean label:

1. Add Python kernel constant in `packages/services/**/`
2. Add TS mirror constant in `apps/web/lib/closing-pdf-export.ts`
3. Add ko-KR.json key in `apps/web/messages/ko-KR.json`
4. Add helper function in `labels_ko.py` if format helper needed
5. Add test scenario in `test_closing_pdf_export_*_consistency.py`
6. Verify cross-surface parity via 3중 게이트 CI gate

## Cross-Reference

- AD: AD-15 (cross-language parity) §4 (envelope) + §11 (drift detector)
- UX: ko-KR locale + WCAG AA + Professional 톤 (locked decisions)
- Stories: 6-1 (closing-period) + 6-2 (monthly-closing-report) +
           6-3 (closing-pdf-export + ko-KR labels)