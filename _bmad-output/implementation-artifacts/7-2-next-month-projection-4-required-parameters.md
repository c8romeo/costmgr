---
title: 'Epic 7 Story 2 — Next-Month Projection with 4 Required Parameters (차월 추정 4종 파라미터 강제 + 카드/차트/PDF 3종 결과)'
status: ready-for-dev
priority: HIGH
epic: 7
story_num: 2
story_key: 7-2-next-month-projection-4-required-parameters
baseline_commit: a63646c
created: 2026-08-15
updated: 2026-08-15
---

> **2026-08-15 — bmad-create-story spec 진입 done** (7-2: backlog → ready-for-dev). **cj-style 3-story 분할 2번째 진입점** (Epic 11 retro §7 A14 권장안 (a) — Epic 4·5·6·11·12 + Epic 11/12 carry-over 6번째 epic 연속). 7-1 (BEP slider) / **7-2 (차월 추정 4종 파라미터 — 현재 진입)** / 7-3 (Epic 7 close-out retro §7 신규 결정 시).
>
> **baseline_commit = `a63646c`** (Story 12.3 T7 follow-up sprint + Epic 12 진짜 close-out tip — current HEAD).
>
> **Story 7-1 bmad-create-story spec 진입 done** (2026-08-15) → bmad-dev-story 7-1 T1~T8 실행 또는 본 7-2와 병행 가능 (cj-style atomic sprint 패턴 유지).
>
> **Three user decisions locked** (2026-08-15):
> 1. **순수 엔진 함수 surface = `packages/cost_engine/projection.py`** (NEW 분리 파일, AD-5 stdlib-only) — `project_next_month(*, baseline_cvp, loan_amount, interest_rate, cost_inflation_rate, corporate_tax_rate) -> NextMonthProjection` + `compute_interest_expense(*, loan_amount, interest_rate) -> Decimal` + `compute_after_tax_income(*, pre_tax_income, corporate_tax_rate) -> Decimal` (3 NEW pure functions + 2 frozen dataclasses: `NextMonthProjection` / `ProjectionInputs`). **`packages/cost_engine/projection.py`** 가 SSOT (A19 math surface migration 패턴 미러 — 7-1과 surface 분리로 cohesion 강화, 7-1은 CVP / 7-2는 projection).
> 2. **Frontend form gate** — react-hook-form + Zod schema + 4종 필드 watch + 1종이라도 비면 [예측 실행] 버튼 disabled. **react-hook-form** + **Zod** (Epic 4 input_drafts wire precedent) — `lodash.debounce` 100ms 입력 검증 디바운싱 (CR 11-4 patterns carry).
> 3. **Capability gate 재사용** = 기존 `Capability.CVP_SIMULATION` (7-1 wire) + 4종 파라미터 강제 (`require_role("owner", "member", "viewer", "consultant_proxy")` 모두 허용). **industry-agnostic** 동일 (manufacturing 3종 ✅ + service-only ✅, 12-1 L4 precedent — "차월 추정은 CVP의 projection 변형").
>
> **cj-style 3-story 분할 6번째 epic 연속 검증** + **CR 11-3 honest-DEFER discipline 10번째 epic 연속** (atomic wire만, partial wire 0).
>
> **A19 lessons carry-over**: math surface migration pattern (CR A19 NEW) — 7-1은 `packages/cost_engine/cvp.py` / 7-2는 `packages/cost_engine/projection.py` (분리 surface). 둘 다 cost_engine SSOT (Story 4-1 wire pattern 미러).
>
> **CR 11-4 lessons carry-over**: D-001 (page.tsx mount MUST actually mount) + D-002 (단일 `apps/web/messages/ko-KR.json` only) + D-005 (TS mirror unknown state fall-through → reject) + P-015 (ko-KR.json SSOT drift detector test).
>
> **CR 12-1 lessons continue applied**: L3 (`_to_projection_inputs(baseline_cvp, form_data)` ORM→kernel boundary conversion, Epic 12-1 _to_totp_state + 12-3 _to_deletion_state precedent) + L4 (CVP_SIMULATION capability 재사용 — industry-agnostic 동일 적용).
>
> **CR 12-5 lessons continue applied**: D-13 (cross-language drift detector pattern) + L4 (honest-DEFER discipline).
>
> **Honestly DEFER (per CR 11-3, partial wire 아님)**:
> - **AI 추천 4종 파라미터** (Epic 10 carry-over, F10.1 input_drafts 우회 필수 — 차입금·이자율·상승률·세율 자동 추천).
> - **차월 추정 시나리오 저장** (Epic 8 Budget Pre-Standard Cost 패턴 — "2026-08#P1" 같은 virtual projection key, 7-3 retro 결정).
> - **Monte Carlo projection sensitivity** (multi-variate sensitivity 분석, 7-3 retro 결정 — 7-1 honestly DEFER #2와 동일 사유).
> - **PDF 보고서 다국어** (ko-KR only per NFR18 — 영문/중문 PDF는 2차, M5 reuse).
> - **Playwright E2E** (sprint-scale, 12-5 T6 패턴, follow-up sprint).
> - **Web Worker offload** (1초 한도 대비 여유, 7-1 honestly DEFER #1과 동일).

# Story 7.2 — Next-Month Projection with 4 Required Parameters

## Epic 7 context

**Epic 7 (CVP/BEP Simulation)** cj-style 3-story 분할 2번째 진입점 (Epic 4·5·6·11·12 + Epic 11/12 carry-over 검증 패턴):

- **7-1** = BEP Slider with 1-Second Recompute (PRD §F7.1 + NFR9 1초 응답 + AD-5 engine purity) ← **done 진입 (ready-for-dev)**
- **7-2** = Next-Month Projection with 4 Required Parameters (PRD §F7.2) ← **이 스토리 (backlog → ready-for-dev)**
- **7-3** = Epic 7 close-out retro §7 (cj-style A14 권장안 (a) — 신규 결정 시)

**Epic 7 모듈 authority**: `apps/api/modules/m7_simulation/` (7-1 wire, EXTENSION) — 본 스토리 = 1 NEW POST endpoint + 1 EXTENDED GET endpoint + 1 NEW POST PDF endpoint.

**Epic 7 capability matrix wire**: 7-1 wire와 동일 `Capability.CVP_SIMULATION` 재사용 (manufacturing 3종 ✅ + service-only ✅ = industry-agnostic). **신규 capability 추가 0건** (CR 11-3 즉시 sweep 회피 — 기존 capability로 dispatch).

**Epic 7 NFR coverage**: NFR9 (P95 ≤ 5초, 7-2는 더 엄격한 1초 이내 — projection은 baseline fetch + pure calc + PDF 생성 합쳐서 1초 한도) + NFR16 (엔진 순수성 — AD-5) + NFR17 (monetary types — AD-8).

## Why this story (atomic wire 결정 근거)

**PRD §F7.2 verbatim**: "차월 추정 시 차입금·이자율·상승률·세율 4종 파라미터 사용자 입력 강제."

**epics.md Story 7.2 AC verbatim** (lines 947-952):
> **Given** 나는 [차월 추정] 탭에 진입
> **When** 4종 파라미터 중 "이자율"만 입력하고 나머지 비움
> **Then** [예측 실행] 버튼이 disabled
> **And** 4종 모두 채우면 활성화
> **And** 파라미터 4종: 차입금(원), 이자율(%), 원가 상승률(%), 법인세율(%)
> **And** 추정 결과는 시뮬레이션 카드 + 차트 + "원가 예측 보고서" PDF 다운로드 버튼 3종으로 제공

**3 second-order decisions** (locked 2026-08-15):

1. **Pure kernel = `packages/cost_engine/projection.py`** (NEW 분리 surface — 7-1 cvp.py와 cohesion 분리, A19 math surface pattern 미러): AD-5 (엔진 순수성) + AD-11 layer rule. **`packages/cost_engine/projection.py` 가 SSOT** (Story 4-1 spec 확정). `packages/services/m7_simulation/` 는 thin orchestration wrappers (CR 11-3 D-2 ALLOWED_SERVICE_SUBMODULES sweep 즉시 + CR 11-1 RSC boundary / FastAPI ContextVar / BigInteger / JSONB lessons carry). **stdlib-only**: `import decimal, dataclasses, math, hashlib, typing` only (no sqlalchemy, no datetime.now, no random). 7-1 cvp.py의 `compute_bep` / `compute_target_profit` / `simulate_cvp` 와 독립 surface (7-2는 차월 projection, 7-1은 BEP slider — concerns 분리).

2. **Frontend form gate = react-hook-form + Zod** (Epic 4 input_drafts wire precedent + CR 11-4 patterns carry): 4종 필드 (`loan_amount`, `interest_rate`, `cost_inflation_rate`, `corporate_tax_rate`) watch + `lodash.debounce` 100ms 입력 검증 + 1종이라도 비면 `[예측 실행]` 버튼 disabled (`disabled={!allFieldsFilled}`). **Web Worker offload honestly DEFER** — over-engineering 회피 (7-1과 동일 패턴).

3. **Capability gate 재사용** = 기존 `Capability.CVP_SIMULATION` (7-1 wire) + 4종 industry-agnostic grant (12-1 L4 precedent — "차월 추정은 CVP의 projection 변형, 모든 industry 동일 적용"). **신규 capability 0건 추가** (CR 11-3 즉시 sweep 회피). `apps/api/modules/m7_simulation/handlers.py` EXTENSION으로 2 NEW POST endpoint (compute + PDF) + 1 EXTENDED GET endpoint.

**+ Epic 7 close-out path**: 7-2 done 진입 후 7-3 close-out retro (cj-style 3번째 진입점 — Epic 11 retro §7 A14 권장안 a).

## User Story

As a **사원**,
I want **차월(예: 2026-08) 추정 시 차입금·이자율·상승률·세율 4종을 모두 입력해야 [예측 실행]이 활성화되고 결과는 카드 + 차트 + PDF 3종으로 받는 것**,
so that **F7.2 (필수 가정 누락 방지) + NFR9 (1초 이내 응답성) + AD-5 (엔진 순수성으로 V8 회귀 가능) + AD-11 (의존 방향 일관성) + Epic 6 §9 #20+ 원가 예측 보고서 PDF 출력 (3종 결과) 모두 만족**.

(PRD §F7.2 + epics.md Story 7.2 verbatim + NFR9·16·17 + AD-5·8·11·18·22 + Epic 7 cj-style 2번째 진입점)

## Acceptance Criteria

### AC #1 — 순수 엔진 함수 surface `packages/cost_engine/projection.py` (epics.md AC #5 verbatim + AD-5 + NFR16)

- **Given** AD-5 엔진 순수성 + AD-11 layer rule + NFR16 V8 회귀 가능 + 7-1 cvp.py와 surface 분리
- **When** `packages/cost_engine/projection.py` NEW 파일 작성 (7-1 cvp.py EXTENSION이 아님 — 분리 surface)
- **Then** **`compute_interest_expense(*, loan_amount: Decimal, interest_rate: Decimal) -> Decimal`**:
  - 공식: `interest_expense = loan_amount * (interest_rate / Decimal("100"))` (이자율 % → Decimal 분수)
  - `interest_rate < 0` → `ValueError("interest_rate must be non-negative")`
  - `loan_amount < 0` → `ValueError("loan_amount must be non-negative")`
  - `interest_rate > Decimal("100")` → `ValueError("interest_rate must be <= 100%")` (비현실적)
- **And** **`compute_after_tax_income(*, pre_tax_income: Decimal, corporate_tax_rate: Decimal) -> Decimal`**:
  - 공식: `after_tax = pre_tax_income * (Decimal("1") - corporate_tax_rate / Decimal("100"))`
  - `corporate_tax_rate < 0` or `> 100` → `ValueError("corporate_tax_rate must be in [0, 100]")`
  - `pre_tax_income < 0` → 손실로 인정 (음수 유지, 법인세 0원 처리)
- **And** **`project_next_month(*, baseline_cvp: CVPBaseline, projection_inputs: ProjectionInputs) -> NextMonthProjection`**:
  - `ProjectionInputs = dataclass(frozen=True)` with 4 fields: `loan_amount: Decimal`, `interest_rate: Decimal`, `cost_inflation_rate: Decimal`, `corporate_tax_rate: Decimal`
  - `NextMonthProjection = dataclass(frozen=True)` with 7 fields:
    - `projected_revenue: Decimal` — baseline.monthly_revenue * (1 + inflation_rate/100)
    - `projected_variable_cost: Decimal` — baseline.monthly_variable_cost * (1 + cost_inflation_rate/100)
    - `projected_fixed_cost: Decimal` — baseline.monthly_fixed_cost + interest_expense (NEW 차입금 이자 추가)
    - `interest_expense: Decimal` — `compute_interest_expense(loan_amount, interest_rate)`
    - `pre_tax_income: Decimal` — projected_revenue - projected_variable_cost - projected_fixed_cost
    - `corporate_tax: Decimal` — `max(0, pre_tax_income) * (corporate_tax_rate / 100)`
    - `after_tax_income: Decimal` — `pre_tax_income - corporate_tax` (손실 시 그대로 음수)
  - 내부적으로 `compute_interest_expense` + `compute_after_tax_income` delegation
  - **`baseline_cvp`은 NOT mutated** (frozen=True + copy semantics, 7-1 simulate_cvp 패턴 미러)
- **And** **`compute_projection_hash(projection: NextMonthProjection) -> str`**:
  - `hashlib.sha256(repr(projection).encode()).hexdigest()` 결정론 digest (V8 회귀용, 7-1 `compute_bep_hash` 패턴)
- **And** **stdlib-only import 검증**:
  - `tests/cost_engine/test_projection_no_io_imports.py` (NEW) — AST parser로 `projection.py` 의 import whitelist 검증 (`decimal`, `dataclasses`, `math`, `hashlib`, `typing` 만 허용, `os, time, random, requests, sqlalchemy, datetime` 모두 차단)
  - 7-1 test_cvp_no_io_imports.py 패턴 미러 (5+ AST cases)
  - ruff custom rule (7-1 wire): `packages/cost_engine/*.py` 에서 forbidden imports → lint error (이미 wire)

### AC #2 — 4종 파라미터 강제 + [예측 실행] 버튼 disabled/enabled (epics.md AC #1~#5 verbatim + react-hook-form + Zod)

- **Given** 4종 파라미터 강제 + react-hook-form + Zod schema
- **When** 사용자 폼 입력 + 1종이라도 비움
- **Then** **[예측 실행] 버튼 disabled**:
  - `disabled={!allFieldsFilled}` — `loan_amount` AND `interest_rate` AND `cost_inflation_rate` AND `corporate_tax_rate` 모두 0보다 크고 빈 문자열 아닐 때만 enabled
  - `aria-disabled="true"` + 시각적 disabled 스타일 (회색 배경, hover 비활성)
  - tooltip: "4종 파라미터를 모두 입력하세요 (차입금·이자율·원가 상승률·법인세율)"
- **And** **4종 모두 채우면 버튼 활성화**:
  - `aria-disabled="false"` + 파란색 배경 (primary)
  - onClick → `POST /api/v1/simulation/projection/compute` with `{ baseline_period_key, projection_month, loan_amount, interest_rate, cost_inflation_rate, corporate_tax_rate }`
- **And** **Zod schema** (`apps/web/lib/m7-simulation-projection-schema.ts` NEW):
  - `loan_amount`: `z.number().positive().int()` (KRW 정수, AD-17 BigInteger parity) — 0보다 큰 정수만
  - `interest_rate`: `z.number().min(0).max(100)` (0~100% 범위, 백엔드와 동일)
  - `cost_inflation_rate`: `z.number().min(-50).max(100)` (-50% ~ +100% 범위, 디플레~인플레)
  - `corporate_tax_rate`: `z.number().min(0).max(100)` (0~100% 범위)
  - 폼 레벨 에러 메시지: ko-KR SSOT (`projection_loan_amount_required` 등)
- **And** **react-hook-form watch + lodash.debounce 100ms** (CR 11-4 patterns carry):
  - `watch(["loan_amount", "interest_rate", "cost_inflation_rate", "corporate_tax_rate"])` → 100ms 디바운싱 → `setAllFieldsFilled(allValid)` → 버튼 disabled 토글
  - 4종 모두 유효할 때만 버튼 활성화 (Zod schema 통과)
- **And** **서버 측 검증** (defense in depth, AC #3과 일치):
  - `apps/api/modules/m7_simulation/services/projection_service.py` 에서 Zod schema와 동일 검증 (Python `pydantic` v2 `Field(gt=0, le=100)`)
  - 클라이언트 우회 시도 차단 (예: devtools로 disabled 속성 제거 → POST 시도 → 422 `PROJECTION_INPUTS_INVALID`)

### AC #3 — Capability gate + industry-agnostic + RLS + NFR9 1초 응답 (AD-3·10·21 + 12-1 L4 precedent + 7-1 capability reuse)

- **Given** AD-3 RLS multi-tenancy + AD-10 4-role + AD-21 단일 CCR + 12-1 L4 industry-agnostic + 7-1 CVP_SIMULATION capability reuse
- **When** `Capability.CVP_SIMULATION` 재사용 + 2 NEW POST endpoint + 1 EXTENDED GET endpoint wire
- **Then** **`apps/api/modules/m7_simulation/handlers.py` EXTENSION**:
  - **`POST /api/v1/simulation/projection/compute`**:
    - Request: `ProjectionComputeRequest(period_key: str, projection_month: str, loan_amount: int, interest_rate: Decimal, cost_inflation_rate: Decimal, corporate_tax_rate: Decimal)`
    - `@require_capability(CVP_SIMULATION)` decorator (7-1 reuse)
    - `require_role("owner", "member", "viewer", "consultant_proxy")` 모두 허용 (AD-10 4-role 모두 — projection은 read-only 시뮬레이션)
    - Service: `fetch_cvp_baseline(period_key)` → `project_next_month(baseline, ProjectionInputs(...))`
    - Response: `ProjectionComputeResponse(baseline, projection_inputs, result: NextMonthProjection, latency_ms: int)`
    - 200 OK + Decimal-as-string (JSON-safe, AD-15) + `compute_projection_hash(result)` 헤더 (`X-Projection-Hash`)
  - **`GET /api/v1/simulation/projection/baseline?period_key=YYYY-MM&projection_month=YYYY-MM`**:
    - `@require_capability(CVP_SIMULATION)` decorator (7-1 reuse)
    - Service: `fetch_cvp_baseline(period_key)` + projection_month 검증 (YYYY-MM 형식 + period_key < projection_month)
    - Response: `ProjectionBaselineResponse(baseline: CVPBaseline, projection_month: str, derived_projection_inputs_hint: dict)` (4종 파라미터 placeholder hint)
  - **`POST /api/v1/simulation/projection/report/pdf`** (NEW):
    - Request: `ProjectionPdfRequest(period_key: str, projection_month: str, projection_inputs: ProjectionInputs, format: Literal["A4"] = "A4")`
    - `@require_capability(CVP_SIMULATION)` decorator
    - Service: `generate_projection_pdf(period_key, projection_month, projection_inputs)` → PDF bytes
    - Response: `application/pdf` (binary) + `Content-Disposition: attachment; filename="cost-prediction-report-{period_key}-{projection_month}.pdf"` (M5 §9 #20+ 보고서 envelope)
    - AD-15 envelope: 422 `PROJECTION_INPUTS_INVALID` (Zod schema 미통과) + 404 `BASELINE_NOT_FOUND` + 200 OK
- **And** **CVP baseline data source (7-1 reuse)**:
  - `fiscal_period_snapshots` + `monthly_input_periods` JOIN으로 baseline CVP 추출 (latest `period_key < projection_month`)
  - **`monthly_input_periods` + `products` + `tenant_settings` aggregation** (pure read query, NO mutation)
  - baseline 추출 후 `packages/cost_engine/projection.py` pure function 호출 (AD-5)
- **And** **RLS same-tenant filter**:
  - `tenant_id` JWT claim → `WHERE tenant_id = :tenant_id` (AD-3 standard pattern, 7-1 precedent)
  - 다른 테넌트 baseline 0건 노출 (Epic 0 RLS verification pattern)
- **And** **NFR9 1초 이내 응답** (7-1과 동일 한도, projection은 baseline fetch + pure calc 합쳐서):
  - **목표**: 100ms baseline fetch + 50ms pure calc + 50ms React re-render = **200ms P95** (1초 한도 대비 5배 여유)
  - PDF 생성은 **별도 endpoint** (`POST /report/pdf`) — 1초 한도 비대상 (PDF는 5초 NFR9 P95 이내, Epic 6 M5 report precedent)
  - `apps/web/lib/m7-projection-bench.ts` (NEW) — `performance.now()` before/after, P95 ≤ 200ms assertion (compute만, PDF 제외)
  - vitest `tests/web/lib/m7-projection-bench.test.ts` (NEW) — 100회 측정 P95 ≤ 200ms

### AC #4 — Frontend `/simulation/projection` RSC + form + 카드/차트/PDF 3종 + ko-KR SSOT (epics.md AC #6 + CR 11-4 D-001·D-002)

- **Given** [차월 추정] 화면 + 4종 폼 + 카드/차트/PDF 3종 결과 + ko-KR.json SSOT
- **When** `apps/web/app/[locale]/(dashboard)/simulation/projection/{layout,page}.tsx` NEW RSC
- **Then** **RSC page** (`page.tsx`):
  - `apps/web/components/m7-simulation/ProjectionClient.tsx` (NEW client component) mount
  - **CR 11-4 D-001 actual mount MUST**: `<ProjectionClient>` JSX return (NOT just create file)
- **And** **ProjectionClient** (client component, 5 NEW):
  - **ProjectionClient.tsx** — main client orchestrator (~300 lines)
    - state: `{ baseline: CVPBaseline | null, formInputs: ProjectionInputs, result: NextMonthProjection | null, isComputing: boolean, pdfBlobUrl: string | null }`
    - onMount: `GET /api/v1/simulation/projection/baseline?period_key=YYYY-MM&projection_month=YYYY-MM` → baseline set + form hint
    - onFormChange → `setFormInputs(new_inputs)` → react-hook-form watch + 100ms debounce → `allFieldsFilled` 갱신
    - onSubmit (예측 실행) → `POST /api/v1/simulation/projection/compute` → result set
    - onDownloadPdf → `POST /api/v1/simulation/projection/report/pdf` → Blob URL set → 자동 다운로드 트리거
    - 4종 결과 영역:
      - **시뮬레이션 카드 4개**: projected_revenue / projected_fixed_cost / pre_tax_income / after_tax_income
      - **차트 1개**: Recharts `ComposedChart` (revenue + variable cost + fixed cost stack + after_tax_income line overlay)
      - **PDF 다운로드 버튼**: "원가 예측 보고서 PDF 다운로드" + 로딩 스피너
  - **ProjectionForm.tsx** (NEW, ~200 lines) — react-hook-form + Zod schema + 4종 입력 + 버튼
    - 4종 Input 컴포넌트: `<ProjectionInput label="차입금 (원)" suffix="원" />` 등
    - `[예측 실행]` 버튼 (`disabled={!allFieldsFilled}`)
  - **ProjectionResultCard.tsx** (NEW, ~80 lines) — 단일 결과 카드 (7-1 CVPResultCard 패턴)
    - props: `{ title: string, value: string, baseline_value?: string, delta_pct?: string, is_improved: boolean }`
    - 화살표 표시 (↑ 개선 / ↓ 악화 / = 동일) — after_tax_income 기준
  - **ProjectionComparisonChart.tsx** (NEW, ~180 lines) — Recharts ComposedChart (7-1 CVPComparisonChart 패턴)
    - baseline vs projected 4 variables 비교 (revenue / variable cost / fixed cost / after_tax_income)
  - **ProjectionPdfButton.tsx** (NEW, ~80 lines) — PDF 다운로드 버튼 + 로딩 상태
    - `onClick` → fetch PDF → Blob URL → `<a download>` 자동 클릭
    - 상태: idle / loading / success / error
- **And** **ko-KR.json** SSOT (CR 11-4 D-002 단일 `apps/web/messages/ko-KR.json` only):
  - 1 NEW namespace `projection` (~25 strings: page_title, projection_month_label, form_loan_amount, form_interest_rate, form_cost_inflation_rate, form_corporate_tax_rate, form_submit_button, form_submit_button_tooltip, card_projected_revenue, card_projected_variable_cost, card_projected_fixed_cost, card_interest_expense, card_pre_tax_income, card_corporate_tax, card_after_tax_income, chart_title, pdf_button_label, pdf_button_loading, pdf_button_error, toast_baseline_not_found, toast_compute_error, etc.)
  - **7-1 cvp_simulation namespace와 분리** (projection 독립 namespace)
- **And** **TS mirror** (`apps/web/lib/m7-simulation-projection.ts`):
  - `ProjectionInputs`, `NextMonthProjection` TS interfaces (7-1 CVPBaseline 패턴)
  - `projectNextMonthTS(baseline, inputs): NextMonthProjection` — TypeScript re-implementation (V8 cross-language parity)
  - **CR 11-4 D-005**: unknown state fall-through → reject (`projectNextMonthTS` baseline null → throw `ERROR_CODE_INVALID_INPUT`)
  - **apps/web/lib/` 단일 SSOT** (CR 11-4 D-002 — ko-KR.json only)
- **And** **디바운싱 + Web Worker honestly DEFER** (7-1 동일):
  - React `useDeferredValue` 또는 `lodash.debounce` 100ms (CR 11-4 patterns carry)
  - Web Worker offload honestly DEFER (1초 한도 대비 5배 여유 — over-engineering 회피)

### AC #5 — Cross-language drift detector + no DB writes + V8 byte-identical (CR 12-5 D-13 + 12-1 P-015 + AD-2 audit-first)

- **Given** AD-15 cross-language conventions + CR 12-5 D-13 structural drift detector + 7-1 cross-language drift 패턴
- **When** 7-2 wire
- **Then** **`tests/integration/test_m7_projection_cross_language_drift.py`** (NEW):
  - **Python ↔ TS parity test**: `project_next_month` Python vs `projectNextMonthTS` TypeScript 10+ vectors
    - 동일 baseline + inputs → 동일 result (`projected_revenue`, `projected_fixed_cost`, `interest_expense`, `pre_tax_income`, `after_tax_income`)
    - Decimal 정밀도 round-trip (TS `decimal.js` ↔ Python `decimal.Decimal`)
    - Edge cases: `corporate_tax_rate = 0` → `after_tax_income == pre_tax_income` / `pre_tax_income < 0` → 손실 유지
  - **ko-KR.json SSOT drift detector** (CR 12-5 L4 + 12-1 P-015):
    - `tests/integration/test_ko_kr_json_ssot.py` EXTENSION — `projection` namespace 정합
    - frontend i18n key가 `apps/web/messages/ko-KR.json` 에만 존재 (NOT `apps/web/lib/ko-KR.json`)
- **And` **no external state mutation**:
  - `tests/integration/test_m7_projection_no_db_writes.py` (NEW) — projection 호출 후 `audit_logs` row 0건 (CR 1.1 invariant — projection = read-only, 7-1과 동일 패턴)
  - **`monthly_closing_report_status` 변경 0건** (M11 close lock 미발동)
  - **`fiscal_period_snapshots` row 변경 0건** (snapshot 미발동)
- **And` **V8 byte-identical CI gate 패턴** (7-1 cvp determinism 패턴 + Epic 4 cost engine 회귀):
  - `tests/cost_engine/test_projection_determinism.py` (NEW) — 100회 동일 입력 byte-identical `projection_hash` (`hashlib.sha256` over `repr(projection)`)
  - **7-1 test_cvp_determinism.py 패턴 미러** (5+ cases)

### AC #6 — AD-11 layer rule + ALLOWED_SERVICE_SUBMODULES sweep + PDF 보고서 wire (epics.md AC #6 + AD-2·5·11·22 + CR 11-3 D-2 + Epic 6 §9 #20+)

- **Given** AD-11 layer rule (`ui → api → services → ports → engine`) + AD-2 append-only + CR 11-3 D-2 ALLOWED_SERVICE_SUBMODULES + Epic 6 M5 PDF report reuse
- **When** 7-2 wire
- **Then` **AD-11 layer rule 검증**:
  - `apps/api/modules/m7_simulation/services/projection_service.py` (NEW service layer, ~200 lines)
  - `packages/services/m7_simulation/` EXTENSION (NEW: `projection_serializers.py` + `projection_pdf_helpers.py`)
  - `packages/cost_engine/projection.py` (pure kernel, stdlib-only, 7-1 cvp.py와 분리 surface)
  - **의존 방향**: `apps/api → packages/services/m7_simulation/ → packages/cost_engine/projection.py` (단방향, AD-11)
  - **import-linter contracts**: 2 KEPT 0 broken (7-1 wire pattern 그대로 유지)
- **And` **ALLOWED_SERVICE_SUBMODULES sweep** (CR 11-3 D-2 즉시, 7-1 wire 패턴 그대로):
  - `tests/architecture/test_api_calls_only_ports.py` EXTENSION — `packages.services.m7_simulation.projection_serializers` + `packages.services.m7_simulation.projection_pdf_helpers` 추가
- **And` **AD-2 audit-first invariant** (CR 1.1):
  - `projection_computed` audit emit (선택적 — read-only operation은 audit skip 가능, 단 옵트인 telemetry, 7-1 동일 패턴)
  - **AC #5 test_m7_projection_no_db_writes로 보장** — audit_logs row 0건 (read-only operation 명시)
- **And` **PDF 보고서 wire** (Epic 6 M5 PDF generator reuse):
  - **`packages/services/m7_simulation/projection_pdf_helpers.py`** (NEW thin wrapper):
    - `serialize_projection_pdf_envelope(*, baseline, projection_inputs, projection, period_key, projection_month) -> dict` — Epic 6 M5 PDF envelope (#20+ 형식)
    - Epic 6 §9 #20+ "원가 예측 보고서" envelope: `{ report_code: "COST_PREDICTION", title: "원가 예측 보고서", period_key, projection_month, baseline_summary, projection_inputs, projection_results, generated_at_kst }`
  - **`apps/api/modules/m7_simulation/services/projection_service.py` `generate_projection_pdf()`**:
    - delegate to `packages/services/m6_reports/pdf_helpers.py:generate_pdf_from_envelope` (Epic 6 M5 reuse, READ-ONLY 패턴)
    - PDF 형식: A4 portrait + KRW 정수 (AD-17 BigInteger parity) + ko-KR only (NFR18)
    - PDF 내부 차트: Recharts SVG → PNG → PDF 임베드 (Epic 6 6-2 wire pattern, frontend 측 차트 캡처)
- **And` **frontend telemetry**:
  - `projection_computed` + `projection_pdf_downloaded` analytics event (PostHog or similar — Epic 10 carry-over, honestly DEFER 시 mock)
  - 본 스토리 범위 외 (honestly DEFER)

## Tasks / Subtasks (atomic wire)

### Task 1 — Pure kernel (Projection math surface)

- **AC**: #1
- **파일**: `packages/cost_engine/projection.py` (NEW, ~250 lines) + `packages/cost_engine/__init__.py` EXTENSION (export 3 NEW pure functions)
- **subtasks**:
  - [ ] 1.1 STDIN-only: `import decimal, dataclasses, math, hashlib, typing` only (AD-5 purity + import-linter, 7-1 패턴 동일)
  - [ ] 1.2 `class ProjectionInputs(frozen=True)` with 4 fields: `loan_amount: Decimal`, `interest_rate: Decimal`, `cost_inflation_rate: Decimal`, `corporate_tax_rate: Decimal`
  - [ ] 1.3 `class NextMonthProjection(frozen=True)` with 7 fields: `projected_revenue`, `projected_variable_cost`, `projected_fixed_cost`, `interest_expense`, `pre_tax_income`, `corporate_tax`, `after_tax_income`
  - [ ] 1.4 `def compute_interest_expense(*, loan_amount: Decimal, interest_rate: Decimal) -> Decimal` — 공식 + 3종 edge cases (`loan_amount < 0` / `interest_rate < 0` / `interest_rate > 100`)
  - [ ] 1.5 `def compute_after_tax_income(*, pre_tax_income: Decimal, corporate_tax_rate: Decimal) -> Decimal` — 공식 + edge cases (`corporate_tax_rate` 범위 + 손실 처리)
  - [ ] 1.6 `def project_next_month(*, baseline_cvp: CVPBaseline, projection_inputs: ProjectionInputs) -> NextMonthProjection` — `compute_interest_expense` + `compute_after_tax_income` delegation
  - [ ] 1.7 `def compute_projection_hash(projection: NextMonthProjection) -> str` — `hashlib.sha256(repr(projection).encode()).hexdigest()` 결정론 digest
- **tests**: `tests/cost_engine/test_projection.py` (NEW, 35+ cases):
  - `compute_interest_expense` 정상범위 + 3종 edge cases (ValueError)
  - `compute_after_tax_income` 정상범위 + 2종 edge cases + 손실 처리 (음수 유지)
  - `project_next_month` 4 variables baseline → projection 정확성
  - `project_next_month` 손실 케이스 (`pre_tax_income < 0`)
  - `compute_projection_hash` 결정론 (RFC test vector)
  - `frozen=True` enforcement (mutation 시도 → FrozenInstanceError)
  - Decimal precision: ROUND_HALF_EVEN parity (TS decimal.js 동일, 7-1 패턴)
  - 100회 determinism test (byte-identical hash)

### Task 2 — Engine purity gate (AD-5 + import-linter + ruff custom rule)

- **AC**: #1
- **파일**: `tests/cost_engine/test_projection_no_io_imports.py` (NEW), 7-1 ruff custom rule reuse
- **subtasks**:
  - [ ] 2.1 `test_projection_no_io_imports.py` AST parser 검증 (7-1 `test_cvp_no_io_imports.py` 패턴 미러):
    - `cost_engine/projection.py` 의 import whitelist: `decimal, dataclasses, math, hashlib, typing` (7-1과 동일 whitelist)
    - forbidden: `os, time, random, requests, sqlalchemy, datetime, json, urllib` 모두 차단 (5+ cases)
  - [ ] 2.2 ruff custom rule (7-1 wire 그대로 — `packages/cost_engine/*.py` 전체 적용):
    - `import os | import time | import random | import requests | import sqlalchemy | import datetime` → lint error
    - 7-2는 신규 surface 추가이지만 동일 rule 적용 (7-1 wire 재사용)
  - [ ] 2.3 `import-linter` contracts 유지:
    - `cost_engine_forbidden_io` (Epic 0 wire) — 1 KEPT 0 broken (7-1 + 7-2 모두 검증)
    - `engine_core_to_adapters_forbidden` (Epic 0 wire) — 1 KEPT 0 broken

### Task 3 — Service layer (thin wrappers + baseline fetch + PDF envelope)

- **AC**: #3, #6
- **파일**: `apps/api/modules/m7_simulation/services/projection_service.py` (NEW, ~200 lines)
- **subtasks**:
  - [ ] 3.1 `class ProjectionService` with `__init__(session, *, tenant_id, actor_id, trace_id)` (7-1 CVPSimulationService precedent + 12-2 BackupExportService precedent)
  - [ ] 3.2 `async def fetch_projection_baseline(self, *, period_key: str, projection_month: str) -> CVPBaseline`:
    - SELECT `monthly_input_periods` + `fiscal_period_snapshots` JOIN (latest `period_key < projection_month`, `state IN ('committed', 'verified')`)
    - delegate to `apps/api/modules/m7_simulation/services/cvp_simulation_service.py:fetch_cvp_baseline` (7-1 reuse) — `projection_month` 검증만 추가 (`period_key < projection_month` 보장)
    - RLS same-tenant filter (`tenant_id = :tenant_id`)
    - Return `CVPBaseline`
  - [ ] 3.3 `async def project_next_month(self, *, baseline: CVPBaseline, projection_inputs: ProjectionInputs) -> NextMonthProjection`:
    - delegate to `packages/cost_engine/projection.py:project_next_month` (pure kernel)
    - no DB writes, no audit emit (read-only operation, AC #5 보장)
    - Return `NextMonthProjection`
  - [ ] 3.4 `async def generate_projection_pdf(self, *, period_key: str, projection_month: str, projection_inputs: ProjectionInputs) -> bytes`:
    - `fetch_projection_baseline(period_key, projection_month)` → `project_next_month(baseline, projection_inputs)`
    - delegate to `packages/services/m7_simulation/projection_pdf_helpers.py:serialize_projection_pdf_envelope`
    - delegate to `packages/services/m6_reports/pdf_helpers.py:generate_pdf_from_envelope` (Epic 6 M5 reuse, READ-ONLY)
    - Return PDF bytes (A4 portrait, KRW integer, ko-KR)
- **파일**: `packages/services/m7_simulation/` EXTENSION (NEW thin wrappers):
  - [ ] 3.5 `projection_serializers.py` — `serialize_projection_inputs`, `serialize_projection_result` (dataclass → dict, JSON-safe Decimal)
  - [ ] 3.6 `projection_pdf_helpers.py` — `serialize_projection_pdf_envelope` (Epic 6 §9 #20+ 형식)
- **tests**: `tests/services/m7_simulation/test_projection_service.py` (NEW, 18+ cases):
  - `fetch_projection_baseline` baseline extraction 정확성 (`period_key < projection_month` 검증)
  - `fetch_projection_baseline` `projection_month <= period_key` → `InvalidProjectionMonthError` raise (chronological invariant)
  - `fetch_projection_baseline` no baseline → `CVPBaselineNotFoundError` raise (7-1 reuse)
  - `fetch_projection_baseline` RLS same-tenant (다른 tenant_id 0건)
  - `project_next_month` pure kernel delegation
  - `generate_projection_pdf` PDF envelope 정확성 (Epic 6 §9 #20+ 형식)
  - `serializers` JSON-safe Decimal
  - `pdf_helpers` envelope 정확성

### Task 4 — HTTP routes + capability gate + main.py wire

- **AC**: #3, #6
- **파일**: `apps/api/modules/m7_simulation/handlers.py` EXTENSION (~+200 lines)
- **subtasks**:
  - [ ] 4.1 `POST /api/v1/simulation/projection/compute`:
    - Request: `ProjectionComputeRequest(period_key: str, projection_month: str, loan_amount: int, interest_rate: Decimal, cost_inflation_rate: Decimal, corporate_tax_rate: Decimal)`
    - `@require_capability(CVP_SIMULATION)` decorator (7-1 reuse)
    - `require_role("owner", "member", "viewer", "consultant_proxy")` 모두 허용
    - Service: `fetch_projection_baseline(period_key, projection_month)` → `project_next_month(baseline, ProjectionInputs(...))`
    - Response: `ProjectionComputeResponse(baseline, projection_inputs, result, latency_ms)` + `X-Projection-Hash` header
    - 200 OK + Decimal-as-string (JSON-safe, AD-15)
  - [ ] 4.2 `GET /api/v1/simulation/projection/baseline?period_key=YYYY-MM&projection_month=YYYY-MM`:
    - `@require_capability(CVP_SIMULATION)` decorator (7-1 reuse)
    - Service: `fetch_projection_baseline(period_key, projection_month)` only
    - Response: `ProjectionBaselineResponse(baseline, projection_month, derived_projection_inputs_hint)`
    - 422 `INVALID_PROJECTION_MONTH` (chronological invariant violation)
  - [ ] 4.3 `POST /api/v1/simulation/projection/report/pdf` (NEW):
    - Request: `ProjectionPdfRequest(period_key: str, projection_month: str, projection_inputs: ProjectionInputs, format: Literal["A4"] = "A4")`
    - `@require_capability(CVP_SIMULATION)` decorator
    - Service: `generate_projection_pdf(period_key, projection_month, projection_inputs)` → PDF bytes
    - Response: `application/pdf` (binary) + `Content-Disposition: attachment; filename="cost-prediction-report-{period_key}-{projection_month}.pdf"`
- **파일**: `apps/api/main.py` EXTENSION:
  - [ ] 4.4 `m7_simulation` router include (7-1 wire + 7-2 EXTENSION) — `projection` sub-router 추가 또는 동일 router에 endpoint 추가
- **파일**: `apps/api/core/capability.py`:
  - [ ] 4.5 (no change) `CVP_SIMULATION` 재사용 (7-1 wire 그대로, 신규 capability 0건)
- **파일**: `apps/api/core/audit_action.py`:
  - [ ] 4.6 (선택) `projection_computed` audit action 추가 (7-1 `simulation_cvp_computed` 미러, ActionClass.SIMULATION 1 value fill, CR 11-3 D-2 sweep)
- **파일**: `apps/api/modules/m7_simulation/exceptions.py` EXTENSION:
  - [ ] 4.7 `InvalidProjectionMonthError` typed exception (D-14 envelope main.py handler 등록)
  - [ ] 4.8 `ProjectionInputsInvalidError` typed exception (D-14 envelope, 422)
- **tests**: `tests/api/test_m7_projection_handlers.py` (NEW, 15+ cases):
  - `POST /api/v1/simulation/projection/compute` 정상 (200 + Decimal-as-string + X-Projection-Hash 헤더)
  - `POST /api/v1/simulation/projection/compute` no capability → 403 CAPABILITY_NOT_GRANTED
  - `POST /api/v1/simulation/projection/compute` no baseline → 404 CVP_BASELINE_NOT_FOUND
  - `POST /api/v1/simulation/projection/compute` invalid 4종 (loan_amount ≤ 0 / interest_rate 범위 외) → 422 PROJECTION_INPUTS_INVALID
  - `POST /api/v1/simulation/projection/compute` `projection_month <= period_key` → 422 INVALID_PROJECTION_MONTH
  - `GET /api/v1/simulation/projection/baseline?period_key=invalid&projection_month=invalid` → 422 INVALID_PERIOD_KEY + INVALID_PROJECTION_MONTH
  - `POST /api/v1/simulation/projection/report/pdf` 정상 (200 + application/pdf + Content-Disposition)
  - `POST /api/v1/simulation/projection/report/pdf` no baseline → 404 CVP_BASELINE_NOT_FOUND
  - latency measurement: 200ms P95 assertion (compute만, PDF 제외)
  - AD-15 envelope contract (4 fields: code, message_ko, details, trace_id)

### Task 5 — Alembic + RLS (N/A — no schema 변경)

- **AC**: N/A (no schema 변경)
- **note**: 7-2는 **순수 read + pure kernel + PDF envelope reuse** — Alembic migration 불요, RLS 신규 정책 불요 (기존 `fiscal_period_snapshots` + `monthly_input_periods` RLS reuse, 7-1과 동일 패턴)
- **subtasks**:
  - [ ] 5.1 (skip) No new tables, no new columns, no new RLS policies
  - [ ] 5.2 (verify) 기존 `fiscal_period_snapshots` RLS policy `supabase/policies/0003_fiscal_period_snapshots_rls.sql` 활용 확인 (Epic 0 wire + 7-1 verify)

### Task 6 — Frontend (RSC + form + 4 inputs + button + 3종 결과 + TS mirror + ko-KR.json)

- **AC**: #2, #4
- **파일**:
  - [ ] 6.1 `apps/web/app/[locale]/(dashboard)/simulation/projection/layout.tsx` (NEW RSC layout)
  - [ ] 6.2 `apps/web/app/[locale]/(dashboard)/simulation/projection/page.tsx` (NEW RSC page — `<ProjectionClient>` actual mount MUST per CR 11-4 D-001)
  - [ ] 6.3 `apps/web/components/m7-simulation/ProjectionClient.tsx` (NEW client component, ~300 lines)
  - [ ] 6.4 `apps/web/components/m7-simulation/ProjectionForm.tsx` (NEW, ~200 lines) — react-hook-form + Zod + 4종 input + button
  - [ ] 6.5 `apps/web/components/m7-simulation/ProjectionResultCard.tsx` (NEW, ~80 lines) — 결과 카드 (7-1 CVPResultCard 패턴)
  - [ ] 6.6 `apps/web/components/m7-simulation/ProjectionComparisonChart.tsx` (NEW, ~180 lines) — Recharts ComposedChart
  - [ ] 6.6a `apps/web/components/m7-simulation/ProjectionPdfButton.tsx` (NEW, ~80 lines) — PDF 다운로드 버튼 + 로딩 상태
  - [ ] 6.7 `apps/web/lib/m7-simulation-projection.ts` (NEW, ~140 lines) — TS mirror + `projectNextMonthTS` + Zod schema
  - [ ] 6.8 `apps/web/lib/m7-simulation-projection-schema.ts` (NEW, ~60 lines) — Zod schema (4종 + form-level)
  - [ ] 6.9 `apps/web/messages/ko-KR.json` EXTENSION — `projection` namespace (~25 strings, 7-1 cvp_simulation namespace와 분리)
  - [ ] 6.10 `apps/web/lib/m7-projection-bench.ts` (NEW, ~30 lines) — perf benchmark
  - [ ] 6.11 `apps/web/components/m7-simulation/index.ts` EXTENSION — barrel export + Projection
  - [ ] 6.12 `apps/web/lib/menu-config.ts` EXTENSION — `/simulation/projection` sidebar nav entry (7-1 `/simulation/cvp` + sibling)
  - [ ] 6.13 디바운싱: react-hook-form watch + `lodash.debounce` 100ms (CR 11-4 patterns carry, 7-1과 동일)
- **tests**:
  - [ ] 6.14 `apps/web/components/m7-simulation/ProjectionClient.test.tsx` (NEW, 12+ cases) — form 입력 → button disabled/enabled → submit → result card 갱신
  - [ ] 6.15 `apps/web/components/m7-simulation/ProjectionForm.test.tsx` (NEW, 10+ cases) — Zod schema + react-hook-form watch + button toggle
  - [ ] 6.16 `apps/web/components/m7-simulation/ProjectionResultCard.test.tsx` (NEW, 5+ cases) — 화살표 + delta_pct 표시
  - [ ] 6.17 `apps/web/components/m7-simulation/ProjectionPdfButton.test.tsx` (NEW, 5+ cases) — idle / loading / success / error 4-state
  - [ ] 6.18 `apps/web/lib/m7-projection-bench.test.ts` (NEW) — 100회 P95 ≤ 200ms (compute만, PDF 제외)
  - [ ] 6.19 `apps/web/lib/m7-simulation-projection.test.ts` (NEW, 10+ cases) — TS mirror parity Python

### Task 7 — Tests + docs + 3중 게이트 final clean

- **AC**: #1, #2, #3, #4, #5, #6
- **subtasks**:
  - [ ] 7.1 Backend tests aggregate:
    - `tests/cost_engine/test_projection.py` (35+ pure kernel)
    - `tests/cost_engine/test_projection_no_io_imports.py` (5+ AST, 7-1 패턴 미러)
    - `tests/cost_engine/test_projection_determinism.py` (5+ V8 byte-identical, 7-1 패턴 미러)
    - `tests/services/m7_simulation/test_projection_service.py` (18+)
    - `tests/api/test_m7_projection_handlers.py` (15+)
    - `tests/integration/test_m7_projection_cross_language_drift.py` (10+ Python↔TS, 7-1 패턴 미러)
    - `tests/integration/test_m7_projection_no_db_writes.py` (4+ audit_logs 0건 + monthly_closing_report_status 변경 0건 + fiscal_period_snapshots 변경 0건)
    - `tests/architecture/test_api_calls_only_ports.py` EXTENSION (ALLOWED_SERVICE_SUBMODULES m7_simulation.projection_serializers + projection_pdf_helpers sweep, CR 11-3 D-2)
  - [ ] 7.2 Frontend tests:
    - `apps/web/components/m7-simulation/ProjectionClient.test.tsx` (12+)
    - `apps/web/components/m7-simulation/ProjectionForm.test.tsx` (10+)
    - `apps/web/components/m7-simulation/ProjectionResultCard.test.tsx` (5+)
    - `apps/web/components/m7-simulation/ProjectionPdfButton.test.tsx` (5+)
    - `apps/web/lib/m7-projection-bench.test.ts` (perf benchmark)
    - `apps/web/lib/m7-simulation-projection.test.ts` (10+ TS mirror)
  - [ ] 7.3 Docs:
    - `docs/next-month-projection.md` (NEW, ~250 lines, 9 sections — 7-1 docs/cvp-simulation.md 패턴 + PDF 보고서 envelope 명시)
    - `docs/capability-matrix.md` v1.16 EXTENSION (7-1 CVP_SIMULATION row reuse 명시, 신규 row 0)
    - `docs/conventions.md` §AD-11 layer rule EXTENSION (m7_simulation service layer 명시, 7-1 + 7-2)
    - `docs/architecture-inventory.md` EXTENSION (m7_simulation projection module entry)
    - `docs/deferred-work.md` EXTENSION (5 honestly DEFER items 명시)
    - `docs/sprint-status.md` sync (7-2: ready-for-dev → in-progress)
  - [ ] 7.4 3중 게이트 mandatory CI (cj-style 7번째 epic + carry-over 7번째 연속):
    - **ruff scoped** (7-2 surface: `packages/cost_engine/projection.py` + `apps/api/modules/m7_simulation/` + `packages/services/m7_simulation/` + `apps/web/components/m7-simulation/`): All checks passed
    - **import-linter 2 KEPT 0 broken** (ALLOWED_SERVICE_SUBMODULES `m7_simulation.projection_serializers` + `projection_pdf_helpers` 추가, AD-11 + AD-22 + cost_engine_forbidden_io + engine_core_to_adapters_forbidden 모두 유지)
    - **pytest baseline + ~80 NEW = 2106 + ~80 = ~2186 passed + 127 skipped + 0 failed** (3 pre-existing failures honestly DEFER per A19 carry-over T0 결정, 7-2 추가 회귀 0)
    - **vitest 158 baseline + ~42 NEW = ~200 passed** (7-1 cvp_simulation 26 + 7-2 projection 42 추가)
    - **3 pre-existing failures** (test_alembic_0022_does_not_exist + test_sdr_test_count_drift + test_tenant_backups_0024_migration) honestly DEFER per A19 carry-over T0 결정 (7-2 scope OUTSIDE)
  - [ ] 7.5 MAX SDR claim 갱신 (CR 11-2 lesson — separate line for unambiguous parser match):
    - `2176 → ~2256` (+80 NEW pytest cases)
    - `184 → ~226` (+42 NEW vitest cases)
    - `2410 → ~2482` total

### Task 8 — Atomic wire close-out (handoff + sprint-status)

- **AC**: all
- **subtasks**:
  - [ ] 8.1 Commit message: `Story 7.2: T1~T7 atomic wire — Next-month projection 4 required parameters + pure kernel + service layer + 3 handlers + frontend form/cards/chart/PDF + cross-language drift + 3중 게이트`
  - [ ] 8.2 sprint-status.yaml EXTENSION — `7-2-next-month-projection-4-required-parameters: ready-for-dev → in-progress → review → done`
  - [ ] 8.3 handoff memory file: `handoff-2026-08-15-7-2-spec-ready.md` (5 honestly DEFER 명시)
  - [ ] 8.4 Epic 7 진입 시점 baseline_commit = `a63646c` (Story 12.3 T7 follow-up tip) 명시
  - [ ] 8.5 다음 단계 명시: `bmad-dev-story 7-2 T1~T8 실행 OR 7-2 + 7-1 동시 sprint (cj-style atomic) OR Epic 7 7-3 close-out retro (cj-style 3번째)`

## Dev Notes

### Architecture patterns & constraints

**AD-5 engine purity (CRITICAL)**:
- `packages/cost_engine/projection.py` 는 **stdlib-only** (decimal, dataclasses, math, hashlib, typing) — NO sqlalchemy, NO datetime.now(), NO random, NO I/O
- **7-1 cvp.py 와 surface 분리** — A19 math surface migration pattern (cohesion 강화, projection은 별도 concern)
- import-linter contracts 2 KEPT 0 broken (Epic 0 wire pattern, 12-1 + Epic 5 reinforcement + 7-1 + 7-2)
- ruff custom rule: `packages/cost_engine/*.py` 에서 forbidden imports → lint error (7-1 wire 그대로, 7-2 신규 surface 추가지만 동일 rule 적용)

**AD-11 layer rule**:
- 의존 방향: `apps/web → apps/api → packages/services/m7_simulation/ → packages/cost_engine/projection.py`
- 단방향 strict (Epic 0 wire pattern, 12-1 reinforcement + 7-1 + 7-2)
- engine은 services / adapters / UI import 불가 (AD-11 reverse-direction 명시)
- **packages/cost_engine/projection.py → packages/cost_engine/cvp.py** 1방향 호출 (7-2는 7-1 BEP baseline을 input으로 받음, reverse 호출 없음)

**AD-3 RLS multi-tenancy**:
- baseline fetch 시 `tenant_id = :tenant_id` 필터 (JWT claim, 7-1 패턴 동일)
- 다른 테넌트 baseline 0건 노출 (Epic 0 fixture test pattern)

**AD-15 cross-language conventions**:
- DB/Python `snake_case`; Next.js routes `kebab-case` (`/simulation/projection`); React/TS types `PascalCase`
- Decimal 정밀도: ROUND_HALF_EVEN (Python `decimal.Decimal` ↔ TS `decimal.js`, 7-1 패턴 동일)
- Period keys follow AD-24 (`YYYY-MM`, projection_month도 동일 형식)
- Errors: `{code, message_ko, details, trace_id}` (AD-15 §4 envelope, 7-1 + 7-2 typed exception main.py handler 등록)

**NFR9 (P95 ≤ 5초) → 7-2 (P95 ≤ 1초, compute만)**:
- 100ms baseline fetch + 50ms pure calc + 50ms React re-render = 200ms P95
- **PDF 생성은 별도 endpoint** (`POST /report/pdf`) — 1초 한도 비대상 (PDF는 5초 NFR9 P95 이내, Epic 6 M5 report precedent)
- Web Worker offload honestly DEFER (over-engineering 회피, 7-1과 동일)

**NFR16 determinism**:
- V8 byte-identical CI gate: 100회 동일 입력 → 100회 동일 `compute_projection_hash(projection)` (Epic 4 baseline extension + 7-1 패턴)
- `hashlib.sha256(repr(projection).encode()).hexdigest()` 결정론 digest

**NFR17 monetary types (AD-8)**:
- BIGINT (KRW integer, `loan_amount` + `projected_revenue` + `projected_fixed_cost`) / NUMERIC(18,4) (이자율/상승률/세율 — Decimal 4자리 정밀도)
- Python `decimal.Decimal`; TS `decimal.js`
- 7-2는 KRW only (USD 환산은 Epic 6 6-2 wire, 본 스토리 범위 외)

**PDF 보고서 envelope (Epic 6 §9 #20+)**:
- Epic 6 M5 PDF generator reuse (READ-ONLY, no audit emit)
- envelope 형식: `{ report_code: "COST_PREDICTION", title: "원가 예측 보고서", period_key, projection_month, baseline_summary, projection_inputs, projection_results, generated_at_kst }`
- PDF 형식: A4 portrait + KRW 정수 + ko-KR only (NFR18)

**Epic 7 capability reuse (7-1 + 7-2)**:
- `Capability.CVP_SIMULATION` 단일 capability로 7-1 + 7-2 dispatch (산업 agnostic 동일 적용)
- 신규 capability 추가 0건 (CR 11-3 즉시 sweep 회피)

**CR 11-4 lessons carry**:
- D-001 (page.tsx mount MUST actually mount `<ProjectionClient>` JSX)
- D-002 (단일 `apps/web/messages/ko-KR.json` only — NOT `apps/web/lib/ko-KR.json`)
- D-005 (TS mirror unknown state MUST raise — `projectNextMonthTS` baseline null → throw `ERROR_CODE_INVALID_INPUT`, NOT silent fall-through)
- P-015 (ko-KR.json SSOT drift detector test — `projection` namespace 정합)

**CR 12-1 lessons continue**:
- L3 (`_to_projection_inputs(form_data)` ORM→kernel boundary conversion, Epic 12-1 _to_totp_state + 12-3 _to_deletion_state precedent)
- L4 (CVP_SIMULATION capability 재사용 — 7-1 + 7-2 industry-agnostic 동일 적용)

**CR 12-5 lessons continue**:
- D-13 (structural cross-language drift detector — `test_m7_projection_cross_language_drift.py` Python↔TS 10+ vectors, 7-1 패턴)
- D-14 (typed exception main.py envelope handler 등록 — `InvalidProjectionMonthError` 422 + `ProjectionInputsInvalidError` 422)
- L4 (honest-DEFER discipline — AI 추천 / 시나리오 저장 / Monte Carlo / PDF 다국어 / Playwright / Web Worker 6 honestly DEFER)

**A19 lessons carry**:
- math surface migration pattern (`packages/services/m2_input/inventory_math.py` precedent — math surface는 `packages/cost_engine/` 또는 `packages/services/<module>/<math>.py`)
- 7-1은 `packages/cost_engine/cvp.py` / 7-2는 `packages/cost_engine/projection.py` (분리 surface, A19 cohesion pattern 미러)

### Source tree components to touch

**NEW files**:
1. `packages/cost_engine/projection.py` (~250 lines)
2. `tests/cost_engine/test_projection.py` (~35+ cases)
3. `tests/cost_engine/test_projection_no_io_imports.py` (~5 cases, 7-1 패턴 미러)
4. `tests/cost_engine/test_projection_determinism.py` (~5 cases, 7-1 패턴 미러)
5. `packages/services/m7_simulation/projection_serializers.py` (~60 lines)
6. `packages/services/m7_simulation/projection_pdf_helpers.py` (~80 lines)
7. `tests/services/m7_simulation/test_projection_service.py` (~18 cases)
8. `apps/api/modules/m7_simulation/services/projection_service.py` (~200 lines)
9. `apps/api/modules/m7_simulation/schemas_projection.py` (~100 lines — Pydantic v2)
10. `tests/api/test_m7_projection_handlers.py` (~15 cases)
11. `tests/integration/test_m7_projection_cross_language_drift.py` (~10 cases, 7-1 패턴 미러)
12. `tests/integration/test_m7_projection_no_db_writes.py` (~4 cases)
13. `apps/web/app/[locale]/(dashboard)/simulation/projection/layout.tsx` (NEW RSC layout)
14. `apps/web/app/[locale]/(dashboard)/simulation/projection/page.tsx` (NEW RSC page)
15. `apps/web/components/m7-simulation/ProjectionClient.tsx` (~300 lines)
16. `apps/web/components/m7-simulation/ProjectionForm.tsx` (~200 lines)
17. `apps/web/components/m7-simulation/ProjectionResultCard.tsx` (~80 lines)
18. `apps/web/components/m7-simulation/ProjectionComparisonChart.tsx` (~180 lines)
19. `apps/web/components/m7-simulation/ProjectionPdfButton.tsx` (~80 lines)
20. `apps/web/components/m7-simulation/ProjectionClient.test.tsx` (~12 cases)
21. `apps/web/components/m7-simulation/ProjectionForm.test.tsx` (~10 cases)
22. `apps/web/components/m7-simulation/ProjectionResultCard.test.tsx` (~5 cases)
23. `apps/web/components/m7-simulation/ProjectionPdfButton.test.tsx` (~5 cases)
24. `apps/web/lib/m7-simulation-projection.ts` (~140 lines TS mirror)
25. `apps/web/lib/m7-simulation-projection-schema.ts` (~60 lines Zod schema)
26. `apps/web/lib/m7-simulation-projection.test.ts` (~10 cases)
27. `apps/web/lib/m7-projection-bench.ts` (~30 lines perf benchmark)
28. `apps/web/lib/m7-projection-bench.test.ts` (~3 cases)
29. `docs/next-month-projection.md` (~250 lines, 9 sections)

**MODIFIED files**:
1. `packages/cost_engine/__init__.py` — export 3 NEW pure functions (`compute_interest_expense`, `compute_after_tax_income`, `project_next_month`) + `compute_projection_hash` (5 lines)
2. `apps/api/main.py` — m7_simulation router include (1 line, 7-1 wire + 7-2 EXTENSION)
3. `apps/api/core/audit_action.py` — `projection_computed` EXTENSION (선택적, 7-1 + 7-2 mirror)
4. `apps/api/modules/m7_simulation/exceptions.py` EXTENSION — 2 NEW typed exceptions (`InvalidProjectionMonthError` + `ProjectionInputsInvalidError`)
5. `apps/api/modules/m7_simulation/handlers.py` EXTENSION — 2 NEW POST + 1 EXTENDED GET endpoint (~+200 lines)
6. `apps/api/modules/m7_simulation/__init__.py` EXTENSION — projection sub-module export
7. `apps/web/messages/ko-KR.json` — `projection` namespace EXTENSION (~25 strings, 7-1 cvp_simulation namespace와 분리)
8. `apps/web/lib/menu-config.ts` — `/simulation/projection` sidebar nav EXTENSION (1 entry)
9. `apps/web/components/m7-simulation/index.ts` EXTENSION — Projection barrel export
10. `docs/capability-matrix.md` v1.16 EXTENSION (7-1 CVP_SIMULATION row reuse 명시, 신규 row 0)
11. `docs/conventions.md` §AD-11 EXTENSION (m7_simulation projection service 명시, 7-1 + 7-2)
12. `docs/architecture-inventory.md` EXTENSION (m7_simulation projection module entry)
13. `docs/deferred-work.md` EXTENSION (6 honestly DEFER items)
14. `_bmad-output/implementation-artifacts/sprint-status.yaml` — 7-2 status sync + last_updated_note
15. `tests/architecture/test_api_calls_only_ports.py` — ALLOWED_SERVICE_SUBMODULES sweep EXTENSION (m7_simulation.projection_serializers + projection_pdf_helpers 추가, CR 11-3 D-2)
16. `tests/integration/test_ko_kr_json_ssot.py` — `projection` namespace 정합 EXTENSION (CR 12-1 P-015)

**Total**: 29 NEW + 16 MODIFIED = 45 files (~3,000 lines code + ~800 lines tests + ~400 lines docs)

### Testing standards summary

**Backend (pytest)**:
- **Pure kernel** (35+ cases): edge cases 5종 ValueError + Decimal precision ROUND_HALF_EVEN parity + frozen=True enforcement + 100회 determinism (7-1 패턴)
- **Service layer** (18+ cases): baseline extraction + chronological invariant (`projection_month > period_key`) + RLS same-tenant + 0 DB writes verification + PDF envelope 정확성
- **Handlers** (15+ cases): 200 OK + 403 CAPABILITY_NOT_GRANTED + 404 CVP_BASELINE_NOT_FOUND + 422 PROJECTION_INPUTS_INVALID + 422 INVALID_PROJECTION_MONTH + PDF Content-Disposition + latency 200ms P95 (compute만)
- **Cross-language drift** (10+ cases): Python ↔ TS parity 10 vectors + edge cases 동일 (7-1 패턴 미러)
- **Audit no-write** (4+ cases): `audit_logs` row 0건 + `monthly_closing_report_status` 변경 0건 + `fiscal_period_snapshots` 변경 0건

**Frontend (vitest)**:
- **ProjectionClient** (12+ cases): form 입력 → button disabled/enabled → submit → result card 갱신 + PDF 다운로드
- **ProjectionForm** (10+ cases): Zod schema + react-hook-form watch + button toggle
- **ProjectionResultCard** (5+ cases): 화살표 + delta_pct 표시
- **ProjectionPdfButton** (5+ cases): idle / loading / success / error 4-state
- **TS mirror parity** (10+ cases): Python `project_next_month` vs TS `projectNextMonthTS` 동일 결과 (7-1 패턴)
- **Performance benchmark** (3+ cases): 100회 P95 ≤ 200ms (compute만, PDF 제외)

**Architecture tests**:
- **ALLOWED_SERVICE_SUBMODULES sweep** (1 case): `m7_simulation.projection_serializers` + `projection_pdf_helpers` 추가 검증 (CR 11-3 D-2)
- **Engine purity** (5+ cases): AST parser로 forbidden imports 차단 검증 (7-1 패턴 미러)

### Project Structure Notes

**Alignment with unified project structure** (cj-style 7번째 epic 검증):
- `apps/api/modules/m7_simulation/` (Epic 11 m11_close + 12-1 m12_account + 7-1 + 7-2 패턴)
- `packages/services/m7_simulation/` (thin wrappers, A19 math surface 패턴 + 7-1 + 7-2 EXTENSION)
- `packages/cost_engine/projection.py` (pure kernel, 7-1 cvp.py와 surface 분리, A19 cohesion pattern)
- `apps/web/components/m7-simulation/` (12-1 m12-account + 7-1 CVPSimulationClient + 7-2 ProjectionClient 패턴)
- `apps/web/app/[locale]/(dashboard)/simulation/projection/` (12-1 /account/security + 7-1 /simulation/cvp 패턴)

**Detected conflicts or variances**:
- None — 7-2는 7-1 wire pattern 그대로 미러 (CVP_SIMULATION capability reuse + cost_engine surface 분리는 A19 cohesion 강화)
- **packages/cost_engine/projection.py** → **packages/cost_engine/cvp.py** 1방향 import (7-2는 CVPBaseline input 받기 위함, reverse 호출 없음)

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Epic-7-CVP/BEP-Simulation`] — Epic 7 + Story 7.2 verbatim
- [Source: `_bmad-output/planning-artifacts/prd.md#§F7.2`] — PRD §F7.2 (차월 추정 4종 파라미터 강제)
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md#AD-5`] — engine purity
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md#AD-11`] — layer rule
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md#AD-15`] — cross-language conventions
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md#AD-3`] — RLS multi-tenancy
- [Source: `_bmad-output/implementation-artifacts/7-1-bep-slider-1-second-recompute.md`] — Story 7.1 spec 진입 패턴 (cj-style 6번째 epic + CVP_SIMULATION capability wire)
- [Source: `_bmad-output/implementation-artifacts/handoff-2026-08-15-a19-inventory-projection-deprecate-done.md`] — A19 carry-over DONE (math surface migration 패턴)
- [Source: `_bmad-output/implementation-artifacts/epic-6-retro-2026-08-09.md`] — Epic 6 close-out retro §7 A8 inline projection deprecate 결정
- [Source: `_bmad-output/implementation-artifacts/epic-11-retro-2026-08-09.md`] — Epic 11 close-out retro §7 A14 cj-style 3-story 분할 권장
- [Source: `_bmad-output/implementation-artifacts/4-1-pure-cost-engine-no-i-o-no-clock.md`] — Story 4.1 cost_engine pure kernel spec (precedent)
- [Source: `_bmad-output/implementation-artifacts/12-1-two-factor-auth-mandatory-gate.md`] — Story 12.1 L4 industry-agnostic capability precedent
- [Source: `_bmad-output/implementation-artifacts/12-3-account-deletion-retention-consent.md#AC-7`] — CR 12-1 L3 _to_<state> ORM→kernel boundary conversion pattern
- [Source: `docs/capability-matrix.md`] — capability matrix v1.16 (7-1 CVP_SIMULATION row reuse, 7-2 신규 row 0)
- [Source: `docs/conventions.md#AD-11-layer-rule`] — 의존 방향 명시
- [Source: `docs/next-month-projection.md`] (will be NEW) — 7-2 도큐먼트
- [Source: `docs/cvp-simulation.md`] (will be NEW per 7-1) — 7-1 도큐먼트 (7-2와 분리)

## Dev Agent Record

### Agent Model Used

Claude Opus 5 (claude-opus-5)

### Debug Log References

N/A (spec 진입 단계 — bmad-dev-story 진입 시 작성)

### Completion Notes List

(To be filled by bmad-dev-story T1~T8 execution)

### File List

(To be filled by bmad-dev-story T1~T8 execution)

## Honestly DEFER (per CR 11-3 10번째 epic 연속 검증)

| # | Item | Rationale | Where |
|---|------|-----------|-------|
| 1 | AI 추천 4종 파라미터 | Epic 10 carry-over (F10.1 input_drafts 우회 필수 — 차입금·이자율·상승률·세율 자동 추천) | specs/deferred-work.md ## Deferred from: 7-2 |
| 2 | 차월 추정 시나리오 저장 | Epic 8 Budget Pre-Standard Cost 패턴 — "2026-08#P1" 같은 virtual projection key, 7-3 retro 결정 | specs/deferred-work.md ## Deferred from: 7-2 |
| 3 | Monte Carlo projection sensitivity | multi-variate sensitivity 분석 — 7-3 retro 결정 (7-1 honestly DEFER #2와 동일 사유) | specs/deferred-work.md ## Deferred from: 7-2 |
| 4 | PDF 보고서 다국어 | ko-KR only per NFR18 — 영문/중문 PDF는 2차, M5 reuse | specs/deferred-work.md ## Deferred from: 7-2 |
| 5 | Playwright E2E | sprint-scale (12-5 T6 패턴, follow-up sprint) | specs/deferred-work.md ## Deferred from: 7-2 |
| 6 | Web Worker offload | 1초 한도 대비 5배 여유 (200ms P95) — over-engineering 회피 (7-1 honestly DEFER #1과 동일) | specs/deferred-work.md ## Deferred from: 7-2 |

---

**Status**: ready-for-dev (cj-style 3-story Epic 7 2번째 진입점, 6번째 epic 연속 검증)
**baseline_commit**: `a63646c`
**다음 단계**: `bmad-dev-story 7-2 T1~T8 실행` OR `7-2 + 7-1 동시 sprint (cj-style atomic)` OR `Epic 7 7-3 close-out retro (cj-style 3번째)`
