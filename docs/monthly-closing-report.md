# Monthly Closing Report — Operator/Dev Guide (Story 6.2, Epic 6)

> Epic 6 — PRD §F5 (마감 보고서) + §F5.2 (KRW/USD dual display)
> + §V4 (closing-period consistency verification)

## 1. 개요 (Overview)

PRD §F5: "월 마감 확정 후, 사장님은 마감 보고서 화면에서
(a) closing snapshot (마감 시점 재고 집계), (b) ledger events
(수불 event 전체), (c) fiscal period snapshot (회계 기간 마감 상태)
3-source read-only join 결과를 확인한다. 제조 3종 industry 만 노출
(service-only 는 INDUSTRY_NOT_SUPPORTED)."

PRD §F5.2: "마감 보고서는 KRW 와 USD 를 동시에 표시한다. USD 환율은
한국은행 USD/KRW 매매기준율을 사용하며, 환율은 `tenant_settings.baseline.currency_pair.usd_krw_rate`
JSONB sub-block 에서 읽는다. banker's rounding (ROUND_HALF_EVEN) 으로
USD 2자리까지 표시한다."

PRD §V4: closing-period consistency verification — 4 sources
(`ledger_aggregate` + `closing_snapshot_aggregate` +
`fiscal_period_snapshot_aggregate` + `product_whitelist`) 의 모든
product_id 별 qty 가 일치해야 PASS.

**Story 6.2** wire contract:

1. **3-source read-only join** — `MonthlyClosingReportService.get_monthly_closing_report`
   dispatch (`closing_snapshot` rows + `inventory_ledger` events +
   `monthly_input_periods` finalization status).
2. **View mode classifier** — `classify_report_view_mode` →
   `READY` (3 sources 모두 populated + V4 PASS) / `PARTIAL`
   (일부 source 만 populated / V4 FAIL but non-blocking) / `EMPTY`
   (3 sources 모두 empty → 409 `MonthlyClosingReportEmptyError`).
3. **V4 closing-period consistency verification** — `verify_monthly_closing_report_consistency`
   pure kernel feeds VerificationRunner V4 slot (V1 → **V4** → V3 → V7 → V8
   ordering, AD-12 invariant). Source count = **4** (Story 6.1 V4 wire
   의 2-source extension).
4. **KRW/USD dual display** — `format_period_closing_krw_usd` + 한국은행
   `currency_pair.usd_krw_rate` + ROUND_HALF_EVEN `USD_QUANTUM = Decimal('0.01')`.
5. **Carry-over close** — 5-1 + 5-2 + 5-3 + 0.5 + A12 + 6-1 R4 triage
   9 DEFER + 6-1 T10.5 deferred V4 골든 fixture fill 모두 6-2 spec 진입
   시점에 close.
6. **A11 V8 16-fixture matrix extension** — V8 골든 fixture count
   16 → **18** (12 V8 baseline + 2 V3 + 4 V4/A11 6-2). closing-period-fixture-1
   + fiscal-period-snapshot-fixture-1 2 NEW V8 골든 fixture file 생성
   (6-1 T10.5 carry-over close).

## 2. Wire Contract

### 2.1 Backend 진입점 (3 NEW routes)

```python
# apps/api/modules/m4_inventory/handlers.py
@router.get("/closing-period/report", response_model=MonthlyClosingReportResponse)
async def get_monthly_closing_report(
    period_key: str,
    actor_id: uuid.UUID = Query(...),
    tenant_id: uuid.UUID = Depends(...),
    session: AsyncSession = Depends(get_session),
) -> MonthlyClosingReportResponse:
    """월 마감 보고서 (3-source read-only join + view mode classification).

    200 OK envelope: {period_key, view_mode, closing_snapshot_count,
    ledger_event_count, fiscal_period_snapshot_count, v4_verdict,
    opening_inventory[], closing_per_product[], aggregate}
    403 INDUSTRY_NOT_SUPPORTED (service-only)
    409 MonthlyClosingReportEmptyError (3 sources 모두 empty)
    422 MonthlyClosingReportKrwUsdRateMissingError (currency_pair 누락)
    """

@router.get("/closing-period/report/audit-trail")
async def get_monthly_closing_report_audit_trail(
    period_key: str,
    tenant_id: uuid.UUID = Depends(...),
    session: AsyncSession = Depends(get_session),
) -> list[AuditEntry]:
    """월 마감 보고서 audit trail (action_class='monthly_closing_report' filter)."""

@router.get("/closing-period/report/v4-verdict")
async def get_monthly_closing_report_v4_verdict(
    period_key: str,
    industry: str = Query(...),
    tenant_id: uuid.UUID = Depends(...),
    session: AsyncSession = Depends(get_session),
) -> V4Verdict:
    """V4 closing-period consistency verdict (4-source verification)."""
```

### 2.2 View mode 분류 (3-state classifier)

```python
# packages/services/m4_inventory/monthly_closing_report.py
REPORT_VIEW_MODE_READY = "READY"      # 3 sources populated + V4 PASS
REPORT_VIEW_MODE_PARTIAL = "PARTIAL"  # 일부 source 만 populated
REPORT_VIEW_MODE_EMPTY = "EMPTY"      # 3 sources 모두 empty → 409

def classify_report_view_mode(
    closing_snapshot_count: int,
    ledger_event_count: int,
    fiscal_period_snapshot_count: int,
    v4_status: Literal["passed", "failed", "skipped"],
) -> Literal["READY", "PARTIAL", "EMPTY"]:
    """월 마감 보고서 view mode 분류.
    - 3 sources 모두 populated + V4 passed → READY
    - 일부 source 만 populated OR V4 failed → PARTIAL
    - 3 sources 모두 count=0 → EMPTY (409 raise caller-side)
    """
```

### 2.3 V4 verification surface (4-source extension)

```python
# packages/cost_engine/monthly_closing_report_aggregator.py
V4_ORDER_INDEX = 2  # AD-12 ordering: V1 → V4 → V3 → V7 → V8
V4_RULE_CODE = "V4"

def verify_monthly_closing_report_consistency(
    ledger_aggregate: dict[UUID, Decimal],
    closing_snapshot_aggregate: dict[UUID, Decimal],
    fiscal_period_snapshot_aggregate: dict[UUID, Decimal],
    product_whitelist: set[UUID],
    industry: str = "manufacturing",
) -> dict:
    """V4 closing-period consistency 4-source verification.
    Returns: {status: Literal["passed"|"failed"|"skipped"],
              code: "V4", failures: [...], source_count: 4,
              skip_reason_ko: Optional[str]}
    """
```

### 2.4 KRW/USD dual display (PRD §F5.2)

```python
# packages/services/m4_inventory/monthly_closing_report.py
USD_QUANTUM = Decimal("0.01")  # NUMERIC(18,2) AD-8 SSOT

def compute_usd_from_krw(
    amount_krw: Decimal,
    exchange_rate: Decimal,
) -> Decimal:
    """KRW → USD conversion (ROUND_HALF_EVEN banker's rounding)."""

def format_period_closing_krw_usd(
    amount_krw: Decimal,
    currency_pair: CurrencyPair,
) -> PeriodClosingDisplay:
    """PRD §F5.2 dual display envelope.
    Returns: PeriodClosingDisplay(amount_krw, amount_usd, currency_pair_display_ko)
    """
```

## 3. UI 진입점 (Frontend Wire)

### 3.1 월 입력 → [마감] tab → MonthlyClosingReportPanel (additive)

```tsx
// apps/web/components/m2-input/MonthlyClosingReportPanel.tsx
<MonthlyClosingReportPanel
  data={monthlyClosingReport}
  v4Verdict={monthlyClosingReportV4Verdict}
  auditTrail={monthlyClosingReportAuditTrail}
/>
```

Capability gate (A10): `capability_granted === false` 면
`null` return (RSC boundary, A10 wire).

View mode dispatch:
- **READY** → green `Alert` ("월 마감 보고서") + 4 KPI cards
  (`closing_snapshot_count` + `ledger_event_count` +
  `fiscal_period_snapshot_count` + `v4_verdict`) + dual display table.
- **PARTIAL** → amber `Alert` + sonner `toast.info('일부 마감 데이터 누락')`.
- **EMPTY** → muted `Alert` + sonner `toast.warning('마감 데이터 없음')`.

### 3.2 Read-only RSC page

```tsx
// apps/web/app/[locale]/(dashboard)/m2-input/period/[periodKey]/monthly-closing-report/page.tsx
export default async function MonthlyClosingReportPage({ params }) {
  // 3 read-only fetches (Promise.all):
  const [report, auditTrail, v4Verdict] = await Promise.all([
    fetchMonthlyClosingReportServerSide(periodKey),
    fetchMonthlyClosingReportAuditTrailServerSide(periodKey),
    fetchMonthlyClosingReportV4VerdictServerSide(periodKey),
  ]);

  // Fail-closed fallback: all 3 null → EMPTY view mode
  if (!report || !auditTrail || !v4Verdict) {
    return <MonthlyClosingReportPanel data={null} viewMode="EMPTY" />;
  }

  return <MonthlyClosingReportPanel data={report} v4Verdict={v4Verdict} auditTrail={auditTrail} />;
}
```

### 3.3 Capability gate UI

```tsx
// TS mirror (apps/web/lib/monthly-closing-report.ts)
export function isMonthlyClosingReportAllowed(industry: Industry): boolean {
  return industry === "manufacturing"
      || industry === "manufacturing_service"
      || industry === "manufacturing_service_other";
}
```

Service-only industry → RSC redirect to `/m2-input` (silent skip,
ClosingPeriodConfirmationPanel pattern mirror).

## 4. AD-15 Cross-Language Parity (TS ↔ Python)

Pure kernel constants SSOT parity:

| Constant | Python (`packages/services/m4_inventory/monthly_closing_report.py`) | TS (`apps/web/lib/monthly-closing-report.ts`) |
|---|---|---|
| `MONTHLY_CLOSING_REPORT_TITLE_KO` | `"월 마감 보고서"` | `"월 마감 보고서"` |
| `MONTHLY_CLOSING_REPORT_EMPTY_KO` | `"마감 데이터 없음"` | `"마감 데이터 없음"` |
| `REPORT_VIEW_MODE_READY` | `"READY"` | `"READY"` |
| `REPORT_VIEW_MODE_PARTIAL` | `"PARTIAL"` | `"PARTIAL"` |
| `REPORT_VIEW_MODE_EMPTY` | `"EMPTY"` | `"EMPTY"` |
| `USD_QUANTUM` | `Decimal("0.01")` | `"0.01"` |
| `QTY_QUANTUM` (parity helper) | `Decimal("0.0001")` (from `inventory_projection`) | `"0.0001"` |

Drift detector: `tests/integration/test_monthly_closing_report_label_consistency.py`
(9 cases). Drift caught here blocks 6-2 wire from shipping.

## 5. V8 16-fixture matrix extension (A11 PRIMARY)

V8 골든 fixture count extension (6-2):

| Group | Count | Fixtures |
|---|---|---|
| V8 baseline | 12 | 4 industries × 3 baseline shapes (b-small / b-standard / b-complex) |
| V3 | 2 | `closing-invariant-b-standard.json` + `closing-invariant-b-complex.json` (5-3 wire) |
| V4/A11 (6-2) | 4 | `closing-period-b-small.json` + `closing-period-b-standard.json` + `fiscal-period-snapshot-b-small.json` + `fiscal-period-snapshot-b-standard.json` |
| **Total** | **18** | 12 + 2 + 4 |

V8 fixture count drift detector:
- `tests/regression_v8/test_regression_v8_fixtures.py::test_v8_fixture_count_is_18`
- `tests/cost_engine/test_regression_v8_placeholder.py::test_v8_fixture_count_now_18_in_story_6_2`
- `tests/architecture/test_api_calls_only_ports.py::ALLOWED_SERVICE_SUBMODULES`
  includes `"packages.services.m4_inventory.monthly_closing_report"`.

## 6. Carry-over close (5-1 + 5-2 + 5-3 + 0.5 + A12 + 6-1 R4 triage)

### 6.1 Story 5.1 — Opening Inventory Auto-Carry Chain
- Opening Inventory Auto-Carry Chain (PRD §F4.1) → 전월 기말 → 이번 달 기초
  자동 carry. 12-period chain limit + banker's rounding parity (CR 0-4).

### 6.2 Story 5.2 — Inventory Ledger Append-Only Events
- 11 event_type enum (carry_in / carry_out / production / consumption /
  sales / purchase / adjustment / disposal / reversal / closing_snapshot /
  opening_snapshot). 5-2 wire 11th event_type (`closing_snapshot`)
  reserved for 6-1 confirm_closing_period dispatch.

### 6.3 Story 5.3 — Closing Guard
- Closing ≥ 0 invariant guard + V3 verification sync. 5-3 wire 후
  V3 slot fill done.

### 6.4 Story 0.5 — Frontend Plumbing
- shadcn Alert + Dialog + sonner toast + vitest + RTL + jsdom + MSW wire.

### 6.5 A12 — T12.2 test file deferred close-out
- Epic 5 close-out 시점 T12.2 deferred test file close-out done
  (commit 74f3a30).

### 6.6 Story 6.1 — Closing Period Service (R4 triage 9 DEFER + T10.5 V4 fixture fill)
- 6-1 R4 triage 9 DEFER items: frontend (4 files) + capability matrix v1.8
  + 51 NEW tests + 1 NEW doc. 6-1 carry-over close (in-progress → review).
- 6-1 T10.5 deferred V4 골든 fixture fill → 6-2 carry-over close.
  6-2 A11 wire 통합 close-out: closing-period-fixture-1 +
  fiscal-period-snapshot-fixture-1 2 NEW V8 골든 fixture file 생성.

## 7. 운영 가이드 (Operator)

### 7.1 정상 흐름 (Happy Path)

1. 사장님이 월 마감 확정 (6-1 wire — `POST /closing-period/confirm`).
2. [마감] tab 클릭 → `ClosingPeriodConfirmationPanel` 아래
   `MonthlyClosingReportPanel` 표시 (READY view mode).
3. 4 KPI 카드 (closing snapshot count + ledger event count +
   fiscal period snapshot count + V4 verdict) + dual display
   table 표시.
4. V4 PASS → "월 마감 보고서" green Alert.
5. KRW/USD dual display: 한국은행 USD/KRW 매매기준율 기준
   `1 USD = 1,320 KRW (한국은행 2026-07-25)` + `KRW 1,320,000 = USD 1,000.00`.

### 7.2 비정상 흐름 (Edge Case)

#### PARTIAL view mode

1. 일부 source 만 populated (e.g. closing snapshot count=0 +
   ledger_event_count=10) → PARTIAL view mode.
2. amber Alert + sonner `toast.info('일부 마감 데이터 누락')`.
3. 사장님은 closing snapshot 재실행 후 다시 진입.

#### V4 FAIL

1. 4-source aggregate 불일치 (e.g. ledger SUM=100, closing snapshot=99)
   → V4 verdict `failed` → KPI 빨강 + failures list 표시.
2. PRD §V4 사양: V4 fail 은 non-blocking (계산 자체는 성공,
   lock 만 service layer 책임). PARTIAL view mode dispatch.

#### EMPTY view mode (3 sources 모두 count=0)

1. 3 sources 모두 empty → `MonthlyClosingReportEmptyError` (409).
2. muted Alert + sonner `toast.warning('마감 데이터 없음')`.
3. 사장님은 먼저 입출고 입력 + 마감 확정한 후 다시 진입.

#### 환율 누락 (currency_pair.usd_krw_rate 부재)

1. tenant_settings.baseline.currency_pair 누락 → 422
   `MonthlyClosingReportKrwUsdRateMissingError`.
2. 한국은행 USD/KRW 매매기준율 조회 후 tenant_settings 입력 필요.

### 7.3 Capability 거부 (service-only tenant)

1. `tenant_settings.industry === 'service'` →
   `MonthlyClosingReportPanel` 자체가 비노출.
2. GET 시도 시 403 INDUSTRY_NOT_SUPPORTED typed envelope.
3. Epic 9 ABC costing path 사용 (cost_pool / activity / driver capability).

### 7.4 Audit Log 조회

```
GET /api/v1/inventory/closing-period/report/audit-trail?period_key=2026-07
→ audit_logs entries filtered by action_class='monthly_closing_report'
```

UI 에서는 `MonthlyClosingReportPanel` + audit-trail-list 통합 표시.

## 8. A8 Inline Projection Deprecation Timeline (Epic 5 retro §7 A8)

**5-2 commit + 1 epic maintenance window 종료 시점 = Epic 6 close-out 시점.**

- 6-1 wire 시점 (Epic 6 진입점): inline projection 보존 (1 epic
  maintenance window 진행 중) + closing_period snapshot 은 ledger
  aggregate (5-2 wire) 사용.
- 6-2 wire: inline projection 보존 상태로 wire. Monthly closing report
  는 read-only 3-source join.
- **Epic 6 close-out 시점에 fold-in vs deprecate 결정** (Epic 11
  reversal 진입 시 inline projection 완전 제거).

## 9. Cross-Reference

- PRD: §F5 (마감 보고서) + §F5.2 (KRW/USD dual display) + §V4
  (closing-period consistency verification) + §A11 (입력 시 경고 +
  마감 시 차단 + 마감 확정 시 snapshot 3-layer)
- AD: AD-1 (modular monolith) + AD-2 (append-only ledger) +
  AD-4 (atomicity) + AD-6 (close lock) + AD-8 (monetary types) +
  AD-11 (layer rule) + AD-12 (verification ordering) +
  AD-15 (cross-language parity) + AD-22 (reversal entrypoint)
- A5: forward-lock ActionClass registry ↔ DB CHECK ↔ call sites
- A8: Epic 3.3 inline projection deprecation timeline (Epic 6 close-out
  시점 fold-in)
- A9: Epic 11 reversal (deferred)
- A10: `MONTHLY_CLOSING_REPORT` capability (manufacturing 3종 ✅ /
  service-only ❌)
- A11: V8 16-fixture matrix extension (6-2 PRIMARY — 16 → 18)
- Carry-over: 5-1 + 5-2 + 5-3 + 0.5 + A12 + 6-1 R4 triage +
  6-1 T10.5 V4 골든 fixture fill
