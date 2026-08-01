---
baseline_commit: 8724161
---

# Story 3.1: Six-Stream Monthly Input UI (Month-Total Default)

Status: ready-for-dev

> Epic 3 첫 스토리 — "엑셀에서 옮기는 작업을 한 페이지 안에서 끝낸다" (Epic goal).
> 6종 데이터(주문·생산·판매·구매·경비·인원)를 월합계/일자별 토글로 입력하고,
> 완료 게이트(노란 점 + [계산] 활성화)를 Epic 1 `compute_completion()` 패턴으로 통합.
> **모듈**: `m2_input/` (architecture 253줄 `m2_input/                # MonthInputAdapter + InputPromoter`)

<!-- dev-context: Epic 1 retro W6 (company_subblock JSONB 승격), L2 (pure function + JSONB aggregate),
                    W4 (audit-first + idempotent no-op), C5 (TS mirror parity) — 모든 패턴 전사 적용.
     Epic 2 회고 W4 (Python source ↔ TS mirror regex 검증), W2 (capability matrix 표준화).
     Action Items A1+A2+A4를 본 스펙 본문에 명시적으로 처리한다. -->

## Story

As a **사장님** (small/medium business owner),
I want **"2026-07" 같은 기간을 선택하면 주문·생산·판매·구매·경비·인원 6개 탭이 가로로 보이고, 기본은 월합계 모드, 일자별 토글 시 31행 그리드가 펼쳐지는 것**,
so that **엑셀에서 옮기던 6종 입력을 한 페이지 안에서 끝내고, 미완료 탭은 노란 점으로 표시되어 다음에 어디를 채워야 할지 즉시 알 수 있다** — PRD §6 (월 입력) · §8.M2 (Six-stream input) · F2.1 (일자별 토글).

## Acceptance Criteria

1. **Given** I am on `/[locale]/(dashboard)/m2-input` and the tenant has completed M0 (industry chosen) + M1 (at least one product in catalog)
   **When** I select a period `period_key="2026-07"` and the page mounts
   **Then** the API returns `GET /api/v2/monthly-input/{period_key}/state` with a body `{period_key, mode: "month_total", streams: {orders: {...}, production: {...}, sales: {...}, purchases: {...}, expenses: {...}, labor: {...}}, completion: {orders: false|true, production: ..., ...}, is_complete: false, capability_mask: [...]}` where `capability_mask` carries the industry-conditional tab visibility (PRD §8.M2(b) — `service` 업종은 `production` 탭 hidden)
   **And** the frontend renders 5 (service) or 6 (manufacturing) horizontal tabs in the order **주문 → 생산 → 판매 → 구매 → 경비 → 인원**
   **And** the default mode is `month_total` and the daily toggle is OFF; the body of each tab shows one row per `MonthlyInputRow` schema (qty + amount, NOT per-day)
   **And** the tab header shows a Korean label (e.g. "주문") — NOT the enum literal (AD-15 §1 snake_case ↔ Korean label mirror, 검증은 `tests/integration/test_m2_input_label_consistency.py`)

2. **Given** I am on the page with `mode=month_total`
   **When** I click the "일자별" toggle
   **Then** the body expands to a 31-row grid (rows 1–31 of the period) where each row has qty + amount editable per day (PRD F2.1, 31일 / 30일 / 28일 모두 동일하게 31행 placeholder + day=29·30·31은 비활성 회색)
   **And** the toggle's PATCH `POST /api/v2/monthly-input/{period_key}/mode` with body `{mode: "daily"}` is sent FIRST, and only after 200 does the UI swap layout (optimistic update 금지 — 다른 탭의 일별 데이터 0과 충돌 방지)
   **And** switching back to month_total collapses the grid and rolls up the daily rows to a month-total display (sum, NOT average — Epic 3.3 음수재고 검증과 일관)

3. **Given** I have just opened the page for `period_key="2026-07"` and I have NOT entered anything yet
   **When** the tab headers render
   **Then** each tab header (주문/생산/판매/구매/경비/인원) shows a **yellow dot (●)** to its right indicating "this stream has no data yet" — driven by the `completion.<stream>` boolean in the GET response
   **And** as soon as I save at least one valid row in any tab, that tab's yellow dot disappears (the next GET round-trips with `completion.<stream>=true`)
   **And** **all** streams show green (no yellow) ⇒ `is_complete=true` ⇒ the [계산] button is enabled and the gate tooltip reads "계산을 시작할 수 있습니다"
   **And** if any stream still has a yellow dot ⇒ `is_complete=false` ⇒ the [계산] button stays disabled with tooltip "미완료: 주문, 인원" (CSV list of missing stream labels, ordered per PRD §8.M2(b))

4. **Given** I save a row in the [주문] tab with `product_id="PRD-0001"`, `qty=10`, `unit_price_krw=5000`, `amount_krw=50000`, `mode="month_total"`
   **When** I click 「저장」
   **Then** the API persists one row in `monthly_input_rows` with `tenant_id` from JWT, `period_key="2026-07"`, `stream="orders"`, `product_id` (FK → `products.id`, RLS-scoped), `qty=10`, `unit_price_krw=5000` (BIGINT KRW, AD-8), `amount_krw=50000` (BIGINT KRW, AD-8), `mode="month_total"`, `day_no=NULL` (month-total mode ⇒ single row per `(product, stream)`), `baseline_revision=<current>` (default 1)
   **And** an `audit_logs` row is written **before** the data write (AD-2) with `action='monthly_input_row_saved', target_table='monthly_input_rows', target_id=<new_id>, payload={tenant_id, period_key, stream, product_id, qty, amount_krw, baseline_revision, trace_id}`
   **And** the response is 200 with the row body + updated `completion` payload (so the UI can clear the yellow dot without an extra round-trip)
   **And** the same row saved again with identical values is a **no-op**: 200 + body, no new audit row, no version bump (CR 1.1 idempotent no-op pattern)
   **And** the row saved with `qty` or `amount_krw` different from existing values updates in place + writes one audit row with `before`/`after` snapshot (CR 2.1 lesson)

5. **Given** I am on the [인원] tab and the tenant is `manufacturing_service` (ABC engine active, `LABOR_FTE` enabled per capability matrix)
   **When** I enter 일용직 3명, 각 8일, 일급 150,000원 and click 「저장」
   **Then** the [인원] tab body shows two **read-only** computed fields below the input rows: `fte_headcount = 3 × 8 / 22 ≈ 1.09명` (decimal, 2 places) and `fte_wage_krw = fte_headcount × monthly_salary_basis_krw` (sourced from `tenant_settings.payroll.monthly_salary_basis_krw` if set, else PRD default = 2,500,000원)
   **And** the computed fields display in disabled inputs (greyed-out, `tabindex="-1"`, no manual edit) — this is a placeholder for Story 3.2 full FTE conversion feature, but the **plumbing** (read-only display + decimal rounding) must be wired so 3.2 can be additive (cj-style default)
   **And** `monthly_input_rows` for the [인원] tab stores **only** the inputs (count/days_per_worker/daily_wage_krw) — FTE computed fields are derived on read, not stored (AD-13: MonthInputAdapter normalizes, not the row)

6. **Given** the tenant is `service` industry (no manufacturing capability)
   **When** the page renders
   **Then** the [생산] tab is **not** in the horizontal tab list (5 tabs total: 주문/판매/구매/경비/인원 — PRD §8.M2(b))
   **And** `capability_mask` in the GET response is `["orders", "sales", "purchases", "expenses", "labor"]` (no `"production"`)
   **And** if the user POSTs `monthly_input_rows` with `stream="production"` directly (URL-poking), the API returns 403 `{code: "INDUSTRY_NOT_SUPPORTED", message_ko: "제조업 업종에서만 입력 가능합니다", details: {stream: "production", tenant_industry: "service"}, trace_id: "..."}` (AD-15 envelope)
   **And** the `Capability` enum gains a new entry `MONTHLY_INPUT_PRODUCTION` granted to `manufacturing | manufacturing_service | manufacturing_service_other` only — drift verified by `tests/integration/test_capability_consistency.py` extension (Epic 1 회고 A4 — `docs/capability-matrix.md` 동반 작성)

## Tasks / Subtasks

- [x] **Task 1 — Pure-Python stream completion + schema validators** (AC: #1, #3, #5)
  - [ ] 1.1 — Create `packages/services/m2_input/__init__.py` (empty package init)
  - [ ] 1.2 — Create `packages/services/m2_input/stream_completion.py` (stdlib-only, AD-1/AD-5):
    - `STREAM_LABELS_KO: Final[dict[str, str]]` = `{"orders": "주문", "production": "생산", "sales": "판매", "purchases": "구매", "expenses": "경비", "labor": "인원"}` (PRD §8.M2(b) 순서 보존, KR label mirror)
    - `STREAM_ORDER: Final[tuple[str, ...]]` = `("orders", "production", "sales", "purchases", "expenses", "labor")` (탭 가로 순서 결정)
    - `STREAMS_FOR_INDUSTRY: Final[dict[Industry, frozenset[str]]]`:
      - `manufacturing`: `{orders, production, sales, purchases, expenses, labor}` (6)
      - `manufacturing_service`: 동일 (6)
      - `manufacturing_service_other`: 동일 (6)
      - `service`: `{orders, sales, purchases, expenses, labor}` (5 — production hidden)
    - `compute_stream_completion(rows_by_stream: dict[str, int]) -> dict[str, bool]` — pure: stream → row_count > 0 → `True`. 노란 점 = `False`. None rows_by_stream → all False.
    - `is_all_streams_complete(industry, rows_by_stream) -> bool` — pure: `compute_stream_completion` + `STREAMS_FOR_INDUSTRY` 차집합 = ∅
    - `format_fte_headcount(workers: int, days_per_worker: int, workdays_in_month: int = 22) -> Decimal` — pure (AD-8 Decimal precision), `round_half_even` (TS mirror와 동일 — Epic 1 회고 W2 cross-language parity)
    - `compute_fte_wage_krw(fte_headcount: Decimal, monthly_salary_basis_krw: int) -> int` — pure: `int(round(fte_headcount * monthly_salary_basis_krw))`
  - [ ] 1.3 — Add unit tests `tests/services/test_m2_input_completion.py` (12+ cases):
    - `test_streams_for_manufacturing_returns_six`: 6 streams present, production 포함
    - `test_streams_for_service_returns_five`: 5 streams, production 부재
    - `test_compute_stream_completion_empty`: empty rows → all False
    - `test_compute_stream_completion_orders_present`: `{orders: 3}` → `{orders: True, ...: False}`
    - `test_compute_stream_completion_all_present`: 모든 stream ≥1 row → all True
    - `test_is_all_streams_complete_manufacturing_with_production`: 6 stream 모두 True → True
    - `test_is_all_streams_complete_service_no_production_key`: service 업종 row에 production key 없음 → True (production은 업종에서 제외)
    - `test_format_fte_3_workers_8_days_22_workdays`: → `Decimal("1.09")` (round_half_even)
    - `test_format_fte_zero_workers`: → `Decimal("0.00")`
    - `test_format_fte_30_days_workdays`: → 동일 공식을 30 workdays에도 일관
    - `test_compute_fte_wage_1_09_×_2_500_000`: → `2_725_000` (round)
    - `test_stream_labels_ko_match_prd`: 6 라벨 정확 일치 (회귀 방지)

- [x] **Task 2 — Alembic migration + ORM model (m2_input 핵심 테이블)** (AC: #1, #4, #5)
  - [ ] 2.1 — Create `apps/api/alembic/versions/0009_monthly_input.py` (revision `0009_monthly_input`, down_revision = `0008_ai_documents_idempotency`):
    - `CREATE TABLE IF NOT EXISTS monthly_input_periods`:
      - `id UUID PRIMARY KEY` (UUID v7 default)
      - `tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE`
      - `period_key TEXT NOT NULL` (AD-24 YYYY-MM 포맷)
      - `mode TEXT NOT NULL DEFAULT 'month_total' CHECK (mode IN ('month_total', 'daily'))`
      - `baseline_revision INTEGER NOT NULL DEFAULT 1 CHECK (baseline_revision >= 1)`
      - `locked_by_calculation BOOLEAN NOT NULL DEFAULT false` (AD-13 — 계산 진행 시 lock, Epic 4 first_calc 후 true)
      - `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`
      - `updated_at TIMESTAMPTZ NOT NULL DEFAULT now()`
      - `UNIQUE INDEX uq_monthly_input_periods_tenant_period_revision ON monthly_input_periods(tenant_id, period_key, baseline_revision)` (AD-23 4-namespace 준수)
      - `INDEX idx_monthly_input_periods_tenant_period ON monthly_input_periods(tenant_id, period_key)`
    - `CREATE TABLE IF NOT EXISTS monthly_input_rows`:
      - `id UUID PRIMARY KEY` (UUID v7)
      - `tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE`
      - `period_id UUID NOT NULL REFERENCES monthly_input_periods(id) ON DELETE CASCADE`
      - `stream TEXT NOT NULL CHECK (stream IN ('orders','production','sales','purchases','expenses','labor'))`
      - `product_id UUID NULL REFERENCES products(id) ON DELETE RESTRICT` — `labor` / `expenses`는 product 무관 (서비스/인건비), `orders`/`production`/`sales`/`purchases`는 FK 필수 (CHECK 또는 service layer)
      - `day_no INTEGER NULL CHECK (day_no IS NULL OR (day_no BETWEEN 1 AND 31))` — month_total 모드 = NULL, daily 모드 = 1..31
      - `qty NUMERIC(18,4) NULL CHECK (qty IS NULL OR qty >= 0)` (AD-8 decimal)
      - `unit_price_krw BIGINT NULL CHECK (unit_price_krw IS NULL OR unit_price_krw >= 0)` (AD-8)
      - `amount_krw BIGINT NULL CHECK (amount_krw IS NULL OR amount_krw >= 0)` (AD-8)
      - `workers INTEGER NULL CHECK (workers IS NULL OR workers >= 0)` — labor stream 전용
      - `days_per_worker INTEGER NULL CHECK (days_per_worker IS NULL OR days_per_worker >= 0)` — labor stream 전용
      - `daily_wage_krw BIGINT NULL CHECK (daily_wage_krw IS NULL OR daily_wage_krw >= 0)` — labor stream 전용
      - `memo TEXT NULL CHECK (length(memo) <= 500)`
      - `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`
      - `updated_at TIMESTAMPTZ NOT NULL DEFAULT now()`
      - `UNIQUE INDEX uq_monthly_input_rows_natural ON monthly_input_rows(tenant_id, period_id, stream, COALESCE(product_id, '00000000-0000-0000-0000-000000000000'), COALESCE(day_no, 0))` — partial unique for natural key (AD-23 4-namespace)
      - `INDEX idx_monthly_input_rows_tenant_period_stream ON monthly_input_rows(tenant_id, period_id, stream)`
  - [ ] 2.2 — Add ORM models to `apps/api/core/db_models.py`:
    - `class MonthlyInputPeriod(Base)` + `class MonthlyInputRow(Base)`
    - `Mapped[Decimal | None]` for `qty` (per AD-8)
    - `Mapped[int | None]` for `unit_price_krw` / `amount_krw` / `daily_wage_krw` (AD-8 BIGINT)
    - `Mapped[int | None]` for `workers` / `days_per_worker` (small int)
  - [ ] 2.3 — RLS policy `supabase/policies/0009_monthly_input_rls.sql`:
    - `monthly_input_periods` + `monthly_input_rows`: `USING (tenant_id = auth.uid()::uuid OR auth.jwt() ->> 'role' = 'service_role')` — Epic 0 RLS 패턴 그대로
    - INSERT/UPDATE/DELETE 모두 RLS 적용 (service_role bypass)

- [x] **Task 3 — Capability gate update (MONTHLY_INPUT_PRODUCTION)** (AC: #6)
  - [ ] 3.1 — Update `apps/api/core/capability.py`:
    - Add `MONTHLY_INPUT_PRODUCTION = "monthly_input_production"` to `Capability` enum
    - Update `_INDUSTRY_CAPABILITIES`:
      - `MANUFACTURING`: add capability
      - `SERVICE`: **no** capability (production tab hidden)
      - `MANUFACTURING_SERVICE`: add capability
      - `MANUFACTURING_SERVICE_OTHER`: add capability
  - [ ] 3.2 — Update `packages/services/m0_onboarding/industry_menu.py` (mirror) — capability descriptions for sidebar parity
  - [ ] 3.3 — Update TS mirror `apps/web/lib/menu-config.ts` — capability union type extension
  - [ ] 3.4 — Extend `tests/integration/test_capability_consistency.py` (Epic 1 회고 A4): 4 industries × 7+ capabilities (Epic 1 6 + 1 = 7)
  - [ ] 3.5 — Companion document `docs/capability-matrix.md` (Epic 1+2 회고 공통 A4) — Epic 1+2+3 capability 정의를 한 페이지에서 참조. `m2_input_production` 행 추가.

- [x] **Task 4 — m2_input service + handlers (CRUD + mode toggle + completion gate)** (AC: #1, #2, #3, #4, #5, #6)
  - [ ] 4.1 — Create `apps/api/modules/m2_input/__init__.py`
  - [ ] 4.2 — Create `apps/api/modules/m2_input/schemas.py` (Pydantic v2):
    - `Stream: str = Enum("orders", "production", "sales", "purchases", "expenses", "labor")` (AD-15 snake_case)
    - `Mode: str = Enum("month_total", "daily")`
    - `MonthlyInputRowCreate`: `period_key: str`, `stream: Stream`, `product_id: UUID | None = None`, `day_no: int | None = None` (Field(ge=1, le=31)), `qty: Decimal | None`, `unit_price_krw: int | None`, `amount_krw: int | None`, `workers: int | None`, `days_per_worker: int | None`, `daily_wage_krw: int | None`, `memo: str | None`
    - `MonthlyInputRowUpdate`: all optional (PATCH semantics, exclude_unset=True, CR 1.1)
    - `MonthlyInputRowResponse`: full row + `mode: Mode`
    - `MonthlyInputStateResponse`: `period_key`, `mode: Mode`, `baseline_revision: int`, `rows: list[MonthlyInputRowResponse]`, `completion: dict[Stream, bool]`, `is_complete: bool`, `missing: list[str]`, `capability_mask: list[Stream]`, `fte_display: dict` (인원 stream 한정; service 업종은 빈 dict)
  - [ ] 4.3 — Create `apps/api/modules/m2_input/service.py`:
    - `get_or_create_period(tenant_id, period_key) -> MonthlyInputPeriod` — INSERT if not exists with `mode='month_total', baseline_revision=1`
    - `save_row(tenant_id, period_key, payload: MonthlyInputRowCreate) -> tuple[MonthlyInputRow, dict[Stream, bool]]` — audit-first (CR 1.1):
      1. SELECT FOR UPDATE `monthly_input_rows` natural key
      2. idempotent no-op detection: 동일 (qty, amount_krw, ...) ⇒ 200 + no audit, no version
      3. `emit_audit(action='monthly_input_row_saved', target_id=row.id, payload={...})` with `flush=True`
      4. INSERT/UPDATE row
      5. recompute `completion.<stream>` via `compute_stream_completion` + return
    - `set_mode(tenant_id, period_key, mode: Mode) -> MonthlyInputPeriod` — PATCH mode; 일자별→월합계 롤백은 sum (not avg); 월합계→일자별은 day_no=NULL rows를 31개 placeholder로 expand (NOT persisted — render only)
    - `get_state(tenant_id, period_key) -> MonthlyInputStateResponse` — `compute_stream_completion` + `is_all_streams_complete` + `STREAMS_FOR_INDUSTRY[industry]` ∩
    - `compute_labor_fte(tenant_id, period_key) -> dict` — labor stream rows → `format_fte_headcount` + `compute_fte_wage_krw` (uses `tenant_settings.payroll.monthly_salary_basis_krw ?? 2_500_000` default)
  - [ ] 4.4 — Create `apps/api/modules/m2_input/handlers.py` (FastAPI router, prefix `/api/v2/monthly-input`):
    - `GET /{period_key}/state` → `MonthlyInputStateResponse` (capability_mask + completion + fte_display)
    - `POST /{period_key}/rows` → `save_row` → 201 + state (POST body: MonthlyInputRowCreate)
    - `PATCH /{period_key}/rows/{row_id}` → `save_row` with partial body → 200 + state
    - `DELETE /{period_key}/rows/{row_id}` → DELETE + audit + state recompute (soft: AD-2 append-only-leaning; 이 row는 monthly_input이므로 ledger와 달리 DELETE 허용 — PRD §8.M2)
    - `POST /{period_key}/mode` → `set_mode` → 200 + period
    - 모든 핸들러는 `get_tenant_context` dependency + capability gate (stream=production → MONTHLY_INPUT_PRODUCTION check)
  - [ ] 4.5 — Register router in `apps/api/main.py`: `app.include_router(m2_input_router, prefix="/api/v2")`

- [x] **Task 5 — Frontend: 6-tab page + 일자별 toggle + 노란 점 + [계산] 게이트** (AC: #1, #2, #3)
  - [ ] 5.1 — Verify shadcn Tabs availability (Epic 1 회고 A2): `pnpm dlx shadcn@latest add tabs`. 실패 시 Story 0.5 plumbing 의존으로 명시 defer — frontend AC는 backend test로만 검증 (Epic 1 회고 C1 패턴)
  - [ ] 5.2 — Create `apps/web/app/[locale]/(dashboard)/m2-input/page.tsx`:
    - URL `?period=2026-07` 로 period_key 결정
    - `useMonthlyInputState(period_key)` hook → API GET, 캐시 키 `['m2_input', 'state', period_key]`
    - 5 또는 6개 `<Tabs>` 렌더 (capability_mask 기준)
    - 각 탭의 노란 점 = `!completion[stream]`
    - [계산] 버튼 = `is_complete ? enabled : disabled` + tooltip `missing.join(', ')`
  - [ ] 5.3 — Create `apps/web/components/m2-input/MonthlyInputTab.tsx` (per-stream body):
    - props: `stream`, `rows`, `mode`, `onSave`, `onDelete`, `onModeToggle`
    - `mode='month_total'` → 1 row per product (default sort by product code)
    - `mode='daily'` → 31 rows (Day 29·30·31 비활성 회색)
    - [인원] 탭은 `workers/days_per_worker/daily_wage_krw` 입력 필드 + read-only `fte_headcount`/`fte_wage_krw` 표시
  - [ ] 5.4 — Create `apps/web/components/m2-input/ModeToggle.tsx` — controlled switch, onChange 시 POST `/mode` 호출 후 invalidate cache
  - [ ] 5.5 — Create `apps/web/lib/m2-input-completion.ts` — TS mirror of `stream_completion.py` (label maps + 6-stream order). Drift verified by `tests/integration/test_m2_input_label_consistency.py` (Epic 1 회고 C5 — TS mirror parity 명시)

- [x] **Task 6 — Tests (service + integration)** (AC: #1, #2, #3, #4, #5, #6)
  - [ ] 6.1 — `tests/services/test_m2_input_completion.py` (Task 1.3 위 12 cases)
  - [ ] 6.2 — `tests/services/test_m2_input_fte.py` (4 cases — round-half-even precision parity with TS mirror)
  - [ ] 6.3 — `tests/integration/test_m2_input_label_consistency.py` (5 cases — Python stream_completion.STREAM_LABELS_KO ↔ TS `apps/web/lib/m2-input-completion.ts` mirror via regex parse, Epic 2 W4 패턴)
  - [ ] 6.4 — `tests/integration/test_capability_consistency.py` 확장 (Task 3.4)
  - [ ] 6.5 — `tests/api/test_monthly_input.py` (DB-backed; Story 0.4 CI shim placeholder + 8+ skip-marked reference tests):
    - `test_state_returns_capability_mask_service_no_production` (AC #6 핵심)
    - `test_state_returns_capability_mask_manufacturing_with_production`
    - `test_save_row_audit_first_writes_audit_before_row` (CR 1.1 회귀)
    - `test_save_row_idempotent_noop_no_audit_no_version`
    - `test_save_row_production_403_for_service_industry` (AC #6)
    - `test_set_mode_daily_then_month_total_rolls_up_sum`
    - `test_state_completion_yellow_dot_per_stream`
    - `test_state_fte_display_for_labor_stream`
  - [ ] 6.6 — `tests/rls/test_monthly_input_isolation.py` (cross-tenant 404; Story 0.4 RLS 패턴)

- [x] **Task 7 — Docs** (AC: 전체 운영자/개발자 onboarding)
  - [ ] 7.1 — Create `docs/monthly-input.md` — operator/dev guide:
    - 6 stream 정의 + capability_mask 4-산업 매트릭스 (A4 capability-matrix.md 참조)
    - 일자별↔월합계 토글 round-trip 동작 (sum vs avg)
    - 노란 점 = completion 게이트 시각화 의미
    - [계산] 활성화 조건 + Epic 4 calc endpoint 연결
    - PII (인건비/일급) logging redaction 노트 (Epic 1 회고 C1 defer #3 — `redact_processor` 후속)
    - Deferral: FTE 정밀 계산 (Story 3.2), 음수재고/조업도 경고 (Story 3.3)
  - [ ] 7.2 — Update `docs/capability-matrix.md` (Epic 1+2 회고 A4): `m2_input_production` 행 추가, m2_input industry별 capability visibility 명시

## Dev Notes

### Architecture binds

- **AD-1 (헥사고날)** — m2_input 모듈 = ports/service/handlers 4-layer, MonthInputAdapter는 Epic 4 first_calc 시점에 추가 (현재 스펙은 CRUD + completion만)
- **AD-13 (Input-collection adapter)** — `MonthInputAdapter`는 m2_input 모듈 내부에 정의하되, **Epic 4 [계산] endpoint가 호출하기 전까지 미작성** — 본 스펙은 adapter의 입력(source)만 구축. `compute_labor_fte`가 adapter의 가장 작은 pre-cursor.
- **AD-15 (cross-language)** — snake_case enum, UUID v7, BIGINT KRW (AD-8), ISO-8601 UTC TIMESTAMPTZ, `{code, message_ko, details, trace_id}` 에러 envelope, 한국어 label mirror
- **AD-17 (InputPromoter)** — `M2.m2_input.service.promote_from_drafts()` 시그니처는 **Story 3.4에서 정의** (본 스펙은 direct user-input만 다룸). `M2 is the only caller of InputPromoter.promote()` 규칙 준수 — 본 스펙은 `promote` endpoint를 노출하지 않음
- **AD-22 (append-only-leaning)** — monthly_input_rows는 **DELETE 허용** (PRD §8.M2 user-input이므로 ledger-style append-only 아님). inventory_ledger는 Epic 5에서 별도 append-only. 두 개념 혼동 주의
- **AD-23 (4-namespace)** — `monthly_input_periods (tenant_id, period_key, baseline_revision)` 유니크 + `monthly_input_rows` 자연키 partial unique — 두 namespace 모두 tenant 경계 존중

### Epic 의존성 (Epic 1+2 자산)

| 자산 | 출처 | 본 스펙 사용처 |
|---|---|---|
| `compute_completion()` pure function | Story 1.2 / 1.3 | 패턴: `compute_stream_completion`은 단일 stream 행렬로 단순화 |
| `audit-first + idempotent no-op` | CR 1.1 lesson | Task 4.3 `save_row` |
| `Baseline ↔ product FK` | Story 2.1 | Task 4.2 `MonthlyInputRowCreate.product_id` |
| `PRODUCT_MATERIAL` capability | Story 2.1 | 본 스펙 `MONTHLY_INPUT_PRODUCTION` 인접 — 같은 매트릭스 (제조만) |
| `Industry` enum (4값) | Story 1.1 | Task 1.2 `STREAMS_FOR_INDUSTRY` |
| TS mirror parity test | Epic 2 W4 | Task 6.3 `test_m2_input_label_consistency.py` |

### Capability matrix (A4 — `docs/capability-matrix.md` 동반 작성)

| Capability | manufacturing | service | manufacturing_service | manufacturing_service_other |
|---|---|---|---|---|
| `MONTHLY_INPUT_ORDERS` | ✅ | ✅ | ✅ | ✅ |
| `MONTHLY_INPUT_SALES` | ✅ | ✅ | ✅ | ✅ |
| `MONTHLY_INPUT_PURCHASES` | ✅ | ✅ | ✅ | ✅ |
| `MONTHLY_INPUT_EXPENSES` | ✅ | ✅ | ✅ | ✅ |
| `MONTHLY_INPUT_LABOR` | ✅ | ✅ | ✅ | ✅ |
| `MONTHLY_INPUT_PRODUCTION` | ✅ | ❌ | ✅ | ✅ |

(Epic 1 회고 A4 — Epic 3 본 스펙과 동시 작성)

### 데이터 흐름

```
[Web m2-input page]
   ↓ GET /api/v2/monthly-input/{period}/state
[m2_input.handlers.get_state]
   ↓ compute_stream_completion(rows_by_stream)
[packages.services.m2_input.stream_completion] (pure)
   ↓ is_all_streams_complete + STREAMS_FOR_INDUSTRY[industry]
   → MonthlyInputStateResponse {completion, is_complete, missing, capability_mask, fte_display}
   ↑ frontend: 노란 점 + [계산] 게이트

[사용자 row 입력/저장]
   ↓ POST /api/v2/monthly-input/{period}/rows
[m2_input.handlers.save_row]
   ↓ SELECT FOR UPDATE monthly_input_rows natural key
   ↓ idempotent no-op?  → 200 + no audit (CR 1.1)
   ↓ emit_audit(action='monthly_input_row_saved', flush=True) [if not no-op]
   ↓ INSERT or UPDATE monthly_input_rows
   ↓ compute_stream_completion → return updated completion
```

### PIPA / PII / Logging

- 인건비(`daily_wage_krw`, `fte_wage_krw`)는 PII — `redact_processor` 미설치 상태이므로 logging에서 마스킹 없음 (Epic 1 회고 C1 defer #3 명시). 본 스펙은 `docs/monthly-input.md`에 "MVP: PII 로깅 마스킹 미적용, 운영 전 redact_processor 후속 필수" 경고 추가
- `memo TEXT` (500자 제한) — 사용자 입력 그대로 저장, PIPA cross-border gate 적용 (Epic 1 m10_ai 패턴과 동일하게 tenant_settings.onboarding.pipa_consent 검사)

## Open Questions (cj-style defaults)

| # | 질문 | 디폴트 | 변경 시 영향 |
|---|---|---|---|
| OQ1 | monthly_input aggregate 저장 형태 — JSONB 단일 row vs normalized rows? | **normalized rows** (`monthly_input_rows` per stream/product/day) — Story 2.1 products BOM 패턴과 동일, 집계 쿼리는 SQL로 | JSONB 선호 시 schema 변경 + 어댑터 rewrite |
| OQ2 | `baseline_revision` 발행 시점 — 매번 vs (mode toggle / first_calc 직전만)? | **mode toggle + first_calc 직전** — 단순 입력 수정은 같은 revision에 in-place update. First_calc (Epic 4)가 새 revision을 publish | 매번 발행 시 audit 로그 폭증 + Epic 4 cost engine이 항상 latest revision 읽음 |
| OQ3 | 일자별 mode의 31행 placeholder를 row로 미리 생성? | **render-only placeholder** — DB row는 사용자가 입력한 day만 존재. GET 응답 시 1~31일 scaffold를 동적 생성 | row scaffold 선호 시 31×product×stream row 폭증 |
| OQ4 | 노란 점 = 클라이언트 계산 vs 서버 계산? | **서버 계산** (`completion` 필드) — `is_complete` 일관성 보존 (Epic 1 회고 L1 패턴). 클라이언트는 단순 렌더 | 클라 계산 시 오프라인/지연 시 false-negative 가능 |
| OQ5 | Story 3.1에 Story 3.2(FTE) + Story 3.3(음수재고)의 hook을 어느 깊이까지 포함? | **3.1 = read-only display + capability plumbing만** — 3.2/3.3이 각자 additive 스토리로 진행. 3.1의 [인원] 탭은 `workers/days_per_worker/daily_wage_krw` 입력 + read-only `fte_*` 표시까지만 | 3.2까지 3.1에 합치면 스펙 2배 + 회귀 비용 증가 |
| OQ6 | `monthly_input_rows` DELETE 정책 — append-only vs soft-delete 허용? | **hard delete 허용** — user-input ledger 아님. PRD §8.M2 user 직접 입력 데이터. 단, `audit_logs.action='monthly_input_row_deleted'` 1행 필수 | append-only 선호 시 schema trigger 추가 + reversal 패턴 (AD-22) |

## Definition of Done

- [ ] AC #1~#6 모두 pass (backend test + AC #6 capability gate)
- [ ] Task 1~7 모든 subtask check
- [ ] backend test 16+ cases 모두 green (Task 6.1 + 6.2 + 6.5)
- [ ] `test_m2_input_label_consistency.py` green (Python ↔ TS mirror)
- [ ] `test_capability_consistency.py` 확장 green (4 industries × 7 capabilities)
- [ ] `docs/monthly-input.md` + `docs/capability-matrix.md` 업데이트
- [ ] Deferral 5건 (Epic 1 회고 C1 패턴) 본 스펙에서 명시적으로 차용: (a) shadcn Tabs 미설치 시 frontend AC 미검증, (b) PII redaction 미적용, (c) FTE 정밀은 3.2 후속, (d) 음수재고 경고는 3.3 후속, (e) MonthInputAdapter 본체는 Epic 4 first_calc 시점 후속
- [ ] sprint-status.yaml: `3-1-six-stream-monthly-input-ui-month-total-default` → ready-for-dev (이미 done)

## References

- Epic 3: Monthly Input Capture — `_bmad-output/planning-artifacts/epics.md` lines 707-756
- F2.1: 일자별/월합계 모드 토글 — PRD §6 + §8.M2
- AD-13 / AD-17 — `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md` lines 118-122, 142-146
- Epic 1 회고 — `_bmad-output/implementation-artifacts/epic-1-retro-2026-08-01.md` §6 (Epic 3 의존성) + §7 (A1+A2+A4)
- Epic 2 회고 — `_bmad-output/implementation-artifacts/epic-2-retro-2026-08-01.md` W4 (TS mirror regex 검증)
- CR 1.1 / CR 2.1 lessons — `_bmad-output/implementation-artifacts/.review/story-1-1.diff` + memory `cr-1-1-lessons`
- Story 1.2 `compute_completion()` 패턴 — `packages/services/m0_onboarding/settings_completion.py`
- Story 2.1 product catalog 패턴 — `_bmad-output/implementation-artifacts/2-1-product-item-master-type-tags.md`