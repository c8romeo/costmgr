# 차월 추정 (Next-Month Projection) — Story 7.2 (Epic 7)

> **2026-08-15 — Story 7.2 (Next-Month Projection with 4 Required Parameters)
> T1~T8 atomic wire DONE.** PRD §F7.2 verbatim: "차월 추정 시
> 차입금·이자율·상승률·세율 4종 파라미터 사용자 입력 강제."

## 1. 개요 (Overview)

차월(예: 2026-08) 추정 시 **차입금·이자율·원가 상승률·법인세율 4종
파라미터**를 모두 입력해야 [예측 실행] 버튼이 활성화되며, 결과는
**시뮬레이션 카드 4개 + 차트 1개 + PDF 다운로드 버튼 1개**로 제공됩니다.

**핵심 의도**: 4종 필수 가정 누락 방지 (PRD §F7.2 + AC #2) + 1초 이내
응답성 (NFR9 P95 ≤ 5초 → 7-2 P95 ≤ 1초) + 엔진 순수성 (AD-5).

## 2. 사용자 스토리 (User Story)

```
As a 사원,
I want 차월(예: 2026-08) 추정 시 차입금·이자율·상승률·세율 4종을
모두 입력해야 [예측 실행]이 활성화되고 결과는 카드 + 차트 + PDF 3종으로
받는 것,
so that F7.2 (필수 가정 누락 방지) + NFR9 (1초 이내 응답성) +
AD-5 (엔진 순수성으로 V8 회귀 가능) + AD-11 (의존 방향 일관성) +
Epic 6 §9 #20+ 원가 예측 보고서 PDF 출력 (3종 결과) 모두 만족.
```

## 3. 아키텍처 (Architecture)

### 의존 방향 (AD-11 layer rule)

```
apps/web → apps/api → packages/services/m7_simulation/ → packages/cost_engine/projection.py
   ↓          ↓                   ↓                              ↓
 (RSC +     (HTTP         (thin wrappers:                  (pure kernel,
 client)    handlers)     serializers +                    stdlib-only,
                          pdf_helpers)                     no I/O)
```

- **Single direction strict** — engine은 services / adapters / UI를
  import 하지 않음 (AD-11 reverse-direction 명시).
- **`packages/cost_engine/projection.py` → `packages/cost_engine/cvp.py`**
  1방향 호출 (7-2는 CVPBaseline input을 받음, reverse 호출 없음).

### 모듈 authority

- **`apps/api/modules/m7_simulation/`** (7-1 wire EXTENSION) —
  본 스토리 = 1 NEW POST endpoint + 1 EXTENDED GET endpoint +
  1 NEW POST PDF endpoint.
- **`packages/services/m7_simulation/`** (thin wrappers, A19 cohesion
  패턴) — `projection_serializers.py` + `projection_pdf_helpers.py`.
- **`packages/cost_engine/projection.py`** (NEW 분리 surface) —
  3 pure functions + 2 frozen dataclasses + 3 typed exceptions +
  1 hash function.

## 4. 4종 파라미터 (Inputs)

| 필드 | 타입 | 범위 | 의미 |
|------|------|------|------|
| `loan_amount` | int (KRW) | `> 0` | 차입금 (원) |
| `interest_rate` | number (%) | `0 ~ 100` | 이자율 |
| `cost_inflation_rate` | number (%) | `-50 ~ 100` | 원가 상승률 (디플레~인플레) |
| `corporate_tax_rate` | number (%) | `0 ~ 100` | 법인세율 |

**검증 게이트** (AC #2 + CR 11-4 D-005):
- **Client (Zod)**: `apps/web/lib/m7-simulation-projection-schema.ts`
  — `loan_amount: z.number().positive().int()`, 나머지 3종은
  `.min().max()` 범위 검증.
- **Server (Pydantic v2)**: `apps/api/modules/m7_simulation/schemas.py`
  — 동일 검증 (defense-in-depth).
- **Kernel (Python)**: `packages/cost_engine/projection.py` —
  3종 edge cases (`loan_amount < 0`, `interest_rate` 범위 외,
  `corporate_tax_rate` 범위 외) → `ProjectionInvalidInputError`.

## 5. 결과 카드 + 차트 + PDF (3종 결과)

### 5.1 시뮬레이션 카드 4개

| 카드 | 출처 (Python kernel) | 의미 |
|------|----------------------|------|
| `projected_revenue` | `baseline.monthly_revenue × (1 + cost_inflation_rate/100)` | 차월 매출 |
| `projected_fixed_cost` | `baseline.monthly_fixed_cost + interest_expense` | 차월 고정비 + 이자 |
| `pre_tax_income` | `projected_revenue - projected_variable_cost - projected_fixed_cost` | 세전 이익 |
| `after_tax_income` | `pre_tax_income - max(0, pre_tax_income) × (corporate_tax_rate/100)` | 세후 이익 |

각 카드는 `baseline_value` 대비 delta_pct 표시 + 화살표 (↑/↓/=) +
색상 (green=개선 / red=악화 / gray=동일).

### 5.2 비교 차트 1개 (Recharts ComposedChart)

`apps/web/components/m7-simulation/ProjectionComparisonChart.tsx`:
- **Bar**: 매출 / 변동비 / 고정비 / 세후이익 (기준 vs 추정)
- **Line**: 추정 추세 (overlay)
- **XAxis**: 4종 변수명
- **YAxis**: KRW 천단위 구분

### 5.3 PDF 다운로드 (Epic 6 §9 #20+ envelope)

`apps/web/components/m7-simulation/ProjectionPdfButton.tsx`:
- **Endpoint**: `POST /api/v1/simulation/projection/report/pdf`
- **Envelope**: `{ report_code: "COST_PREDICTION", title: "원가 예측 보고서",
  period_key, projection_month, baseline_summary, projection_inputs,
  projection_results, generated_at_kst }`
- **Format**: A4 portrait + KRW 정수 + ko-KR only (NFR18)
- **4-state**: idle / loading / success / error

## 6. CR 11-4 lessons carry (D-001, D-002, D-005, P-015)

- **D-001**: `apps/web/app/[locale]/(dashboard)/simulation/projection/page.tsx`
  MUST actually mount `<ProjectionClient>` (NOT just create file).
  → 검증: `page.tsx` JSX return에 `<ProjectionClient ... />` 必존재.
- **D-002**: ko-KR.json SSOT only — `apps/web/messages/ko-KR.json` 단일
  SSOT (NOT `apps/web/lib/ko-KR.json`).
  → 검증: `test_m7_simulation_projection_cross_language_drift.py::test_ko_kr_json_no_duplicate_ko_kr_at_lib`.
- **D-005**: TS mirror `projectNextMonthTS` MUST raise (NOT silent
  fall-through) on invalid inputs.
  → 검증: `apps/web/__tests__/lib/m7-simulation-projection.test.ts` —
  baseline null → throw.
- **P-015**: ko-KR.json `projection_simulation` namespace SSOT drift detector.
  → 검증: `test_m7_simulation_projection_cross_language_drift.py::test_ko_kr_json_projection_simulation_namespace_registered`.

## 7. NFR coverage

| NFR | 설명 | 검증 방법 |
|-----|------|-----------|
| NFR9 | P95 ≤ 1초 (compute만) | `performance.now()` before/after (browser console) |
| NFR16 | V8 byte-identical 결정론 | `compute_projection_hash` sha256 (`hashlib.sha256`) |
| NFR17 | ROUND_HALF_EVEN Decimal precision | Python `decimal.Decimal` + TS `Math.round` (KRW 정수) |
| NFR18 | ko-KR only MVP | PDF envelope + UI 모두 ko-KR |

## 8. 6 honestly DEFER (CR 11-3 12번째 epic 연속)

자세한 내용은 [`docs/deferred-work.md`](./deferred-work.md) ## Deferred from: 7-2 참조:

| # | Item | Reason |
|---|------|--------|
| 1 | AI 추천 4종 파라미터 | Epic 10 carry-over (F10.1 input_drafts 우회 필수) |
| 2 | 차월 추정 시나리오 저장 | Epic 8 Budget Pre-Standard Cost 패턴 (7-3 retro 결정) |
| 3 | Monte Carlo projection sensitivity | multi-variate, 7-3 retro 결정 |
| 4 | PDF 보고서 다국어 | ko-KR only per NFR18 (2차 multi-locale) |
| 5 | Playwright E2E (16 cases) | sprint-scale follow-up |
| 6 | Web Worker offload | 200ms P95 측정 충분, over-engineering 회피 |

## 9. 다음 단계

- (A) **7-3 Epic 7 close-out retro** (cj-style 3번째 진입점) 진입
- (B) **Epic 8 8-2 spec 진입** (cj-style 3-story 분할)
- (C) **7-2 follow-up sprint** for 6 honestly DEFER (carry-over pattern 6번째)
