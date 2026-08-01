# 월 입력 (Monthly Input Capture) — Story 3.1 운영자 가이드

> M2 모듈 (`apps/api/modules/m2_input/`)이 어떻게 동작하고,
> 6종 입력(주문·생산·판매·구매·경비·인원)을 어떻게 캡처하는지 설명한다.

## 한 줄 요약

테넌트가 기간(예: `2026-07`)을 선택하면 **M2 월 입력** 모듈이 5~6개 탭을
가로로 보여주고, 사용자가 row를 저장할 때마다 노란 점이 사라진다.
모든 탭의 노란 점이 사라지면 [계산] 버튼이 활성화된다. 한 번에 한
row라도 저장 = 해당 stream의 노란 점 해제.

## 동작 흐름

```
[Web m2-input 페이지]
   ↓ GET /api/v2/monthly-input/{period_key}/state
[m2_input.handlers.get_monthly_input_state]
   ↓ compute_stream_completion (pure, packages.services.m2_input)
   → MonthlyInputStateResponse {rows, completion, is_complete, missing,
                                 capability_mask, fte_display}

[사용자 row 입력 → POST /rows]
   ↓ SELECT FOR UPDATE monthly_input_rows natural key
   ↓ idempotent no-op?  → 200 + no audit (CR 1.1)
   ↓ emit_audit(action='monthly_input_row_saved', flush=True)
   ↓ INSERT or UPDATE monthly_input_rows
   → MonthlyInputStateResponse (yellow dot + [계산] 즉시 갱신)
```

## 6 stream 정의 (PRD §8.M2(b))

| Stream | Backend enum | 한글 라벨 | product_id | 비고 |
|---|---|---|---|---|
| `orders` | `Stream.ORDERS` | 주문 | 필수 | PRD §6.1 주문 입력 |
| `production` | `Stream.PRODUCTION` | 생산 | 필수 | **제조 업종만** (Capability gate) |
| `sales` | `Stream.SALES` | 판매 | 필수 | PRD §6.1 판매 입력 |
| `purchases` | `Stream.PURCHASES` | 구매 | 필수 | PRD §6.1 매입 입력 |
| `expenses` | `Stream.EXPENSES` | 경비 | NULL | 일반 경비 (GL 코드 미정) |
| `labor` | `Stream.LABOR` | 인원 | NULL | `workers`/`days_per_worker`/`daily_wage_krw` 입력 → FTE 환산 |

탭 순서: **주문 → 생산 → 판매 → 구매 → 경비 → 인원** (PRD §8.M2(b) sequence).

## Capability Matrix (PRD §8.M2(b))

[Capability Matrix](./capability-matrix.md) 참조. 핵심 매트릭스:

| Industry | 주문 | 생산 | 판매 | 구매 | 경비 | 인원 |
|---|---|---|---|---|---|---|
| `manufacturing` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `service` | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| `manufacturing_service` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `manufacturing_service_other` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

서비스 업종에서 `[생산]` 탭은 hidden. 다른 5 stream은 모든 업종에서 입력 가능.

## 노란 점 / [계산] 게이트 동작

| Stream 행 수 | 노란 점 | [계산] 상태 |
|---|---|---|
| 0 | 🟡 노랑 | disabled (해당 stream이 missing에 포함) |
| ≥1 | ⚪ 없음 | (다른 stream이 모두 채워지면 enabled) |

`is_complete = 모든 visible stream에 ≥1 row` → `true`일 때 [계산] 활성화.

missing list의 한국어 라벨 순서 (PRD §8.M2(b)):
```
제조: 주문 → 생산 → 판매 → 구매 → 경비 → 인원
서비스: 주문 → 판매 → 구매 → 경비 → 인원
```

## 일자별/월합계 모드 (PRD F2.1)

`mode` 필드는 period 단위 (한 period에 1 mode):
- `month_total` (default) — 1 row per (product, stream). `day_no=NULL`
- `daily` — 1 row per (product, stream, day_no=1..31)

전환:
```
POST /api/v2/monthly-input/{period_key}/mode?mode=daily
```

전환 동작:
- `month_total` → `daily`: 기존 row들은 그대로 (`day_no=NULL`). UI에서
  31행 placeholder가 펼쳐짐 (DB row는 신규 생성 X, render-only).
- `daily` → `month_total`: 31행 day별 row들의 합산 표시 (sum, not avg).
  Epic 3.3 음수재고 검증과 일관.

`mode` 토글은 `baseline_revision`을 증가시키지 않음 (UI preference).
`baseline_revision`은 Epic 4 first_calc에서만 bump (Story 3.4 후속).

## FTE 환산 ([인원] 탭 read-only display) — Story 3.2 hook surface

`workers × days_per_worker / 22` (PRD default `workdays_in_month=22`)
→ `format_fte_headcount` (ROUND_HALF_EVEN, 2dp).

`fte_headcount × 2,500,000원` (PRD default `monthly_salary_basis_krw`)
→ `compute_fte_wage_krw` → `2,725,000원` (3명×8일 예시).

Story 3.1은 read-only display만 노출. 정밀 FTE 계산은 Story 3.2.

## Audit log

모든 mutation은 AD-2 audit-first 패턴:
1. SELECT FOR UPDATE row
2. `emit_audit(action=..., flush=True)`
3. INSERT/UPDATE/DELETE

`action` 값:
- `monthly_input_row_created` (POST /rows 새 row)
- `monthly_input_row_updated` (PATCH 또는 값 변경)
- `monthly_input_row_deleted` (DELETE)
- `monthly_input_mode_changed` (POST /mode)

CR 1.1 lesson: 동일 값 재저장 → audit row 없음, version 미증가.

## 자연키 + Unique

`monthly_input_rows`는 partial unique index로 자연키 보호:
```sql
UNIQUE (tenant_id, period_id, stream,
        COALESCE(product_id, '00000000-0000-0000-0000-000000000000'),
        COALESCE(day_no, 0))
```

- `labor`/`expenses` row → `product_id=NULL` → COALESCE sentinel
- `month_total` row → `day_no=NULL` → COALESCE 0

같은 (tenant, period, stream, product, day)에 row 2개 insert 시
IntegrityError → 400 INVALID_PAYLOAD `natural_key_collision`.

## RLS

`supabase/policies/0009_monthly_input_rls.sql`:
- `monthly_input_periods` + `monthly_input_rows` 모두 ENABLE + FORCE RLS
- 4-policy split (SELECT all roles / INSERT owner / UPDATE owner / DELETE owner)
- `DELETE` 허용 (PRD §8.M2 user-input data, NOT ledger)

cross-tenant → RLS predicate 거부 → 404 / 0 rows affected.

## 환경 / 환경 변수

| 변수 | 기본값 | 설명 |
|---|---|---|
| `MONTHLY_SALARY_BASIS_KRW` | `2_500_000` | PRD default — [인원] 탭 FTE 환산 임금 |
| `WORKDAYS_IN_MONTH` | `22` | PRD default — FTE 계산 분모 |

상수 위치: `apps/api/modules/m2_input/services/monthly_input_service.py`.
Story 3.2에서 `tenant_settings.payroll.*` JSONB override 추가 예정.

## PIPA / PII / Logging

- 인건비(`daily_wage_krw`, `fte_wage_krw`)는 **PII** — MVP에서 logging
  마스킹은 미적용. **운영 전 `redact_processor` 후속 필수** (Epic 1 회고 C1 defer #3).
- `memo TEXT` (500자 제한) — 사용자 입력 그대로 저장.
  PIPA cross-border gate 적용 (Epic 1 m10_ai 패턴; `require_pipa_review`).

## Deferral / 후속 작업

이번 스토리에서 **의도적으로 미완성** 항목:

1. **Frontend 6-tab + 일자별 toggle UI** — Story 0.5 plumbing 의존
   (shadcn/ui Tabs 설치 후 진행). AC 검증은 backend tests로만 done.
2. **FTE 정밀 계산** — Story 3.2 (PRD §6.1). 본 스펙은 read-only
   display hook만 노출.
3. **음수재고/조업도 실시간 경고** — Story 3.3 (PRD §3.A4).
4. **MonthInputAdapter 본체** — Epic 4 first_calc 진입 시 작성 (AD-13).
5. **InputPromoter** — Story 3.4 (M10 AI drafts → monthly_input promotion).
6. **baseline_revision 발행 정책** — Epic 4 first_calc에서만 bump
   (현재는 단순 입력 수정 in-place).

## 실패 시나리오 매핑 (AD-15 envelope)

| 코드 | HTTP | 원인 |
|---|---|---|
| `INDUSTRY_NOT_SUPPORTED` | 403 | service 업종에서 production stream 작성 시도 |
| `FORBIDDEN_ROLE` | 403 | member/viewer가 mutation 시도 |
| `MONTHLY_INPUT_INVALID_PAYLOAD` | 400 | stream-conditional 요구사항 위반 (product_id 부재 등) |
| `MONTHLY_INPUT_NOT_FOUND` | 404 | row 또는 period 없음 |
| `MONTH_INPUT_PERIOD_LOCKED` | 409 | Epic 4 first_calc 후 lock된 period |
| `PIPA_CONSENT_MISSING` | 451 | memo 필드 cross-border 위반 (Story 3.1 memo는 PIPA gate 적용) |

## 디버깅

- 모든 mutation은 `trace_id` 부여 → 응답 `X-Trace-Id` 헤더 + `audit_logs.payload.trace_id`
- `audit_logs.action='monthly_input_row_created'` / `'updated'` / `'deleted'` / `'mode_changed'`로 행위 추적
- `monthly_input_rows.memo`는 500자 truncate + `redact_processor` 후속 (defer #3)

## FTE 정밀 (Story 3.2)

Story 3.1에서 도입한 read-only FTE hook 표시는 Story 3.2에서 PRD §6.1
인건비 정밀 계산으로 **승격**되었다 (`additive` 변경 — Story 3.1 호환).
자세한 내용은 [docs/monthly-input-fte.md](./monthly-input-fte.md) 참조.

핵심 변경:
- `monthly_input_rows`에 7개 신규 컬럼 (`pay_type` + 5 breakdown + `company_burden_rate`)
- `tenant_settings.payroll` JSONB sub-block (per-tenant override)
- `pay_type='monthly'` (정규직, basis 환산) ↔ `pay_type='daily'` (일용직, direct sum)
- `MonthlyInputService._validate_labor_shape()` — pay_type별 shape validation
- 5개 typed exceptions (Task 3.2): 모두 AD-15 §4 envelope으로 응답
- `FteDisplay` enriched: `pay_type` · `breakdown` · `source_rows` · `payroll_settings`
- TS mirror `apps/web/lib/l2-input-fte.ts` — cross-language drift sentinel

## 참조

- 스펙: `_bmad-output/implementation-artifacts/3-1-six-stream-monthly-input-ui-month-total-default.md`
- FTE 정밀 가이드: [docs/monthly-input-fte.md](./monthly-input-fte.md)
- Architecture: AD-13 (`MonthInputAdapter`) · AD-17 (`InputPromoter`)
- Architecture: AD-13 (`MonthInputAdapter`) · AD-17 (`InputPromoter`)
- Capability matrix: `docs/capability-matrix.md`
- 이전 Epic 가이드:
  - `docs/ai-document-extraction.md` (Story 1.3 — input_drafts 패턴)
  - `docs/architecture-decisions/AD-7-ai-extraction-table-naming.md`
- 다음 Epic: Epic 4 (Cost Calculation & Verification) — first_calc에서
  `monthly_input_periods.baseline_revision` bump + `locked_by_calculation=true`