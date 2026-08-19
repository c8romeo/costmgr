# ABC Report #15 Activity Cost Detail (Story 11.6, Epic 11)

> **PRD §9 #15 verbatim**: **"활동원가 내역서 (활동별 원가·동인 단가)"** — 활동·동인 매트릭스 (PRD §7.1 ABC Step 0~3).
> **Epic 11 6번째 진입점** (cj-style Epic 11 5번째 진입점 = **cj-style 37번째 epic 연속 정직 회복**).
> **A30 forward-lock**: A32 결정 wire — SHARED PDF generator reuse 1st case (Report #21 본 진입점 + Report #15 = A30 SHARED factory reuse 1st case 결정 wire 진입).
> **A19 cohesion 9 surface**: A33 결정 wire — A19 cohesion 9 surface 진입점 (kernel + SHARED factory + service + handlers + frontend + cross-lang drift + V8 + audit-first = 9 surface).

## What is Report #15?

Report #15 (활동원가 내역서, Activity Cost Detail) is the **Post-2 closing report** that visualizes ABC allocation outcomes broken down by **activity** (not cost object like Report #21). It is the formal output of the 9.3 wire's `fiscal_period_snapshots.activity_breakdown JSONB` column (PRD §7.1 ABC Step 0~3 — 활동·동인 매트릭스).

PRD §7.1 mandates the activity-driver matrix as the **two-step ABC foundation**:
- **Step 0~2**: 활동 정의 → 동인 매핑 → 부서 원가 집계
- **Step 3**: 활동별 원가·동인 단가 결정

Report #15 은 Step 3 결과를 사용자에게 노출하는 KPI report 입니다.

## Report #15 vs Report #21 (PRD §A9 verbatim)

| Aspect | Report #15 | Report #21 |
|--------|-----------|-----------|
| **Breakdown row unit** | 활동 (activity) | 원가대상 (cost object) |
| **Unused capacity row** | 별도 행 없음 (used only) | 별도 행 표시 (PRD §A9) |
| **Focus** | 활동별 KPI (동인 단가) | 원가대상별 집계 (비용 귀속) |
| **Use case** | 운영 KPI | 세무 공시 (법인세법 §76조) |
| **Entry point 결정** | A31 forward-lock 결정 wire | 9-4 wire |

PRD §A9 verbatim — 미사용능력 별도 관리:
- Report #15 = unused_capacity = 0 (별도 행 없음)
- Report #21 = unused_capacity 별도 행 표시

## Report #15 Endpoint Architecture (AD-18 + AD-19 + A30 + A32)

AD-18 mandates **1 endpoint per Report #N**. M5 owns Report #21 + #15 endpoints:

| Method | Path | Capability | Role | Returns |
|--------|------|------------|------|---------|
| `GET` | `/api/v1/reports/15` | `COST_CALCULATION` OR `ABC_CALCULATION` | `owner` + `member` | `Report15Response` (JSON breakdown) |
| `POST` | `/api/v1/reports/15/pdf` | `COST_CALCULATION` OR `ABC_CALCULATION` | `owner` + `member` | `Report15PdfResponse` (Base64-encoded PDF) |

The **dual-route capability gate** uses `require_any_capability(COST_CALCULATION, ABC_CALCULATION)` — ANY-OF semantics (CR 12-5 D-14 envelope handler pattern + CR 12-1 L4 variadic helper precedent).

**A32 forward-lock** 결정 wire: The PDF export uses the SHARED factory
`packages.services.m5_reports.pdf_generator` with Discriminated
union `report_id: Literal[15, 16, 17, 18, 19, 20, 21]` — Report #15
routes to `_compose_report15_pdf` (stdlib-only PDF byte composition,
Type0 CIDFont + Identity-H CMap pattern matching Story 6-3
`closing_pdf_export` 3rd sweep B1 precedent).

## Response Envelope (Report #15)

```python
class Report15ActivityCostRow(BaseModel):
    activity_id: str
    activity_name_ko: str  # 활동명 (한글, 격식체)
    activity_name_en: str  # activity name (English)
    total_cost_krw: str  # Decimal-as-string AD-8
    total_cost_usd: str  # Decimal-as-string AD-8
    driver_count: int  # 동인 횟수
    cost_per_driver_krw: str  # Decimal-as-string AD-8
    cost_per_driver_usd: str  # Decimal-as-string AD-8
    allocated_krw: str  # Decimal-as-string AD-8
    allocated_usd: str  # Decimal-as-string AD-8


class Report15Response(BaseModel):
    period_key: str
    activity_breakdown: list[Report15ActivityCostRow]
    v7_verdict_is_balanced: bool
    generation_hash: str  # V8 byte-equality sha256 hexdigest
    report_code: Literal["ACTIVITY_COST_DETAIL"]
    activity_count: int
    total_driver_count: int
    total_cost_krw: str
    total_cost_usd: str
```

**V7 ABC 무결성** invariant: Σ(activity_cost) = Σ(department_cost) — 1원 단위 검증 (PRD §A6).

**V8 byte-equality** invariant: `compute_report15_hash(activity_breakdown, period_key, v7_verdict)` produces identical SHA-256 hexdigest across 100 repeats (PRD §V8).

## A19 Cohesion 9 Surface 결정 (A33 forward-lock 진입점)

| # | Surface | File |
|---|---------|------|
| 1 | kernel | `packages/cost_engine/abc_engine.py` (`compute_report15_hash` + `ActivityCostRow` + `Report15Summary` + `Report15InconsistentStateError`) |
| 2 | SHARED PDF factory | `packages/services/m5_reports/pdf_generator.py` (`_compose_report15_pdf` 본체 + `REPORT15_*` constants) |
| 3 | schemas | `apps/api/modules/m5_reports/schemas.py` (`Report15Request/Response/PdfRequest/PdfResponse/ActivityCostRow`) |
| 4 | service | `apps/api/modules/m5_reports/services/report15_service.py` (`Report15Service` + `Report15State` + `_to_report15_state` + `serialize_report15_state`) |
| 5 | handlers | `apps/api/modules/m5_reports/handlers.py` (GET + POST endpoints with capability + role gates) |
| 6 | frontend | `apps/web/components/m5-reports/{Report15Panel,ActivityCostBreakdownTable,ActivityCostPdfExportButton}.tsx` + `app/[locale]/(dashboard)/reports/15/page.tsx` + `lib/report15.ts` + `lib/report15-pdf.ts` |
| 7 | cross-language drift | `tests/integration/test_m5_reports_cross_lang_drift.py` (8 cases — backend ↔ TS mirror ↔ ko-KR.json parity) |
| 8 | V8 determinism | `tests/cost_engine/test_report15_hash_determinism.py` (6 cases — SHA-256 hexdigest invariants) |
| 9 | audit-first AD-22 | `apps/api/modules/m5_reports/services/report15_service.py` (`Report15Service.build_report15` AD-22 ledger append-only invariant) |

## A40 결정 wire (Epic 10 close-out retro §7)

A40 — Report #15 wire schedule: 본 sprint 11-6 에서 dedicated sprint 으로 진입 (Epic 10 close-out retro §7 결정). 9 surface 모두 atomic single sweep T1~T10 으로 wire.

## 11-6 Sprint Scope

- 9 surface 모두 wire (atomic single sweep T1~T10)
- 89 NEW pytest cases expected
- 27 NEW vitest cases expected
- 3중 게이트 FINAL CLEAN expected

## Story History

- **2026-08-19 (Sprint 11-6)**: 본 sprint (cj-style Epic 11 5번째 진입점 = cj-style 37번째 epic 연속 정직 회복). Story 11.6 atomic T1~T10 wire 완료.