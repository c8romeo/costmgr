# Capability Matrix (v1.18)

> **Single source of truth** for the `Industry × Capability` gating that
> Epic 1 / 2 / 3 / 4 / 11 / 12 stories need to coordinate. Replaces the per-story
> capability tables with one consolidated matrix.
>
> **v1.18 (2026-08-16, Story 9.1, Epic 9)** — `ABC_CALCULATION`
> ABC / TDABC engine 100% validation guard wire (PRD §F9.1 verbatim —
> "원가풀 행 합·활동 열 합·동인 합 모두 100% 가드"). Story 9.1 wired
> the pure kernel `abc_engine.py` (A19 cohesion pattern 6번째 surface —
> 4 NEW functions + 3 frozen dataclasses + 4 typed exceptions + 7 constants,
> AD-5 stdlib-only) + service layer `AbcValidationService` +
> 4 NEW routes under `/api/v1/abc/*`:
> - POST /api/v1/abc/cost-pools        — 원가풀 행 합 100% 가드
> - POST /api/v1/abc/activities        — 활동 열 합 100% 가드
> - POST /api/v1/abc/drivers/validate  — 동인 합 100% 가드 (1.2 POST /drivers 와 별도)
> - POST /api/v1/abc/validate          — 3-layer 100% 가드 동시 검증 (main entry point)
>
> 4 NEW typed exceptions are mapped to AD-15 §4 envelopes in
> `apps/api/main.py` (CR 12-5 D-14): `CostPoolValidationError` → 422
> COST_POOL_INVALID_SUM / `ActivityValidationError` → 422 ACTIVITY_INVALID_SUM
> / `DriverValidationError` → 422 DRIVER_INVALID_SUM /
> `AbcValidationNotFoundError` → 404 ABC_VALIDATION_NOT_FOUND.
> Alembic/RLS SKIPPED (9-1 = validation only, no INSERT/UPDATE/DELETE —
> CR 1.1 read-mostly invariant; A5 forward-lock 변경 0).
> `ABC_CALCULATION` is **industry-agnostic** (granted to ALL 4 canonical
> industries) — ABC is operational baseline infrastructure (CR 12-1 L4
> precedent — manufacturing 3종 ✅ + service-only ✅). Drift detector:
> `tests/integration/test_capability_matrix_v1_18_drift.py` pins enum ↔
> docs ↔ 4-industry grants for ABC_CALCULATION.
>
> ---
>
> **v1.17 (2026-08-15, Story 8.1, Epic 8)** — `BUDGET_SCENARIO`
> AD-24 §6.3 virtual budget period key + 1차 시나리오 1개 잠금
> (PRD §F8.1 + §15 NON-GOAL #2). Story 8.1 wired the pure kernel
> `budget_period_key.py` (4 NEW functions + 3 frozen dataclasses +
> 2 typed exceptions) + service layer `BudgetScenarioService` +
> audit ActionClass `BUDGET_SCENARIO` (CR 11-3 honest-DEFER for
> audit emit — 8-1 is read-mostly with scenario creation only, no
> audit emit per CR 1.1 invariant — A5 forward-lock 변경 0) +
> 3 NEW routes under `/api/v1/budget/scenarios/*`:
> - POST /api/v1/budget/scenarios            — owner+member create
> - GET  /api/v1/budget/scenarios            — 4-role list (owner+member+viewer+consultant_proxy)
> - GET  /api/v1/budget/scenarios/{period_key} — 4-role detail by virtual period_key
>
> 3 NEW typed exceptions are mapped to AD-15 §4 envelopes in `apps/api/main.py`
> (CR 12-5 D-14): ScenarioLimitExceededError → 409 / InvalidVirtualBudgetPeriodKeyError → 422
> / BudgetScenarioNotFoundError → 404. Alembic 0026 adds `budget_scenarios`
> table (8 columns + 2 UNIQUE + 3 CHECK + 1 index) + RLS policy 0016
> (4-policy split per AD-3 same-tenant + AD-2 INSERT-only soft invariant).
> BUDGET_SCENARIO is **industry-agnostic** (granted to ALL 4 canonical industries) —
> budget planning is operational baseline (CR 12-1 L4 precedent — manufacturing 3종 ✅
> + service-only ✅).
>
> ---
>
> **v1.17 (2026-08-15, Story 7.1, Epic 7)** — `CVP_SIMULATION`
> CVP/BEP slider simulation wire (PRD §F7.1 + §F7.2). 9 NEW pure functions +
> 7 NEW frozen dataclasses + 4 NEW typed exceptions + 1 NEW capability
> (industry-agnostic, CR 12-1 L4 + 7-1/7-2 precedent — all 4 industries
> grant). 2 NEW math surfaces: `cvp.py` + `projection.py` (A19
> cohesion pattern — split per concern).
>
> ---
>
> **v1.15 (2026-08-15, Story 12.3, Epic 12)** — `ACCOUNT_DELETION`

> **Single source of truth** for the `Industry × Capability` gating that
> Epic 1 / 2 / 3 / 4 / 11 / 12 stories need to coordinate. Replaces the per-story
> capability tables with one consolidated matrix.
>
> **v1.15 (2026-08-15, Story 12.3, Epic 12)** — `ACCOUNT_DELETION`
> Account deletion + retention consent wire (PRD §F12.3 + NFR4 2절 5년 audit 보존
> + 30일 hard delete retention + NFR7 2FA 강제 on destructive endpoint +
> AD-2 INSERT-only invariant on `deletion_consents`). Story 12.3 wired the
> pure kernel `account_deletion.py` + service layer `DeletionService` +
> audit ActionClass `ACCOUNT_DELETION` (8 typed values: `deletion_requested`
> + `deletion_consent_given` + `deletion_cancelled` + `deletion_anonymized`
> + `tenant_hard_deleted` + `deletion_failed` + `deletion_2fa_failed`
> + `two_factor_verified`) + 4 NEW routes under `/api/v1/account/deletion/*`:
> - POST /api/v1/account/deletion/challenge-token — TOTP-gated JWT mint
> - POST /api/v1/account/deletion/request          — destructive (3-layer TOTP defense)
> - POST /api/v1/account/deletion/cancel           — owner cancel pending_deletion
> - GET  /api/v1/account/deletion/status           — read-only FSM snapshot
>
> 6 NEW typed exceptions are mapped to AD-15 §4 envelopes in `apps/api/main.py`.
> Alembic 0025 adds `tenants.status` FSM (active|pending_deletion|deleted) +
> `deletion_consents` table + RLS policy 0015 (4-policy split per AD-2
> INSERT-only invariant). ACCOUNT_DELETION is **industry-agnostic**
> (granted to ALL 4 canonical industries) — deletion is operational
> infrastructure (data subject right / GDPR Art.17), not industry-specific.
> Capability gate enforced ONLY on `request_deletion` (destructive endpoint
> — CR 12-5 L3 3-layer defense target); other routes gate ONLY on
> `require_role("owner")` per AD-10.
>
> **v1.14 (2026-08-12, Story 12.2, Epic 12)** — `BACKUP_EXPORT`
> Daily auto-backup + JSON self-download wire (PRD §F12.2 + §M12-b + NFR4).
> Story 12.2 wired the pure kernel + service layer + audit ActionClass
> `ACCOUNT_BACKUP` (5 typed values: `backup_created` + `backup_failed` +
> `backup_retention_purged` + `backup_downloaded` + `backup_triggered`) +
> 3 NEW routes under `/api/v1/account/backups/*`:
> - GET  /api/v1/account/backups/recent              — list 7-day backups
> - GET  /api/v1/account/backups/{backup_id}/download — JSON download
> - POST /api/v1/account/backups/trigger              — manual owner trigger
>
> 5 typed exceptions are mapped to AD-15 §4 envelopes in `apps/api/main.py`.
> Alembic 0024 adds `tenant_backups` table + RLS policy 0014 (5-policy split
> per AD-3). BACKUP_EXPORT is **industry-agnostic** (granted to ALL 4
> canonical industries) — backup is operational infrastructure, not a
> manufacturing feature. AD-10 owner-only gate enforced at route via
> `require_role("owner")` (not via `require_capability`) per CR 12-1 L4
> precedent — capability is documented but NOT enforced.
> Drift detector: `tests/integration/test_capability_matrix_v1_14_drift.py`
> pins enum ↔ docs ↔ 4-industry grants for BACKUP_EXPORT.
>
> **v1.13 (2026-08-10, Story 12.1 + 12.4, Epic 12)** — `TWO_FACTOR_AUTH`
> 2FA mandatory gate wire (PRD §F12.1 + §M12-a + NFR5 TLS + NFR6 AES-256-GCM).
> Story 12.1 wired the pure kernel + service layer + audit ActionClass
> `TWO_FACTOR_AUTH` (6 typed values). Story 12.4 (carry-over sprint)
> wired 8 routes + 1 M2 entry-gate route under `/api/v1/account/2fa/*`
> + `/api/v1/m2-entry-gate`:
> - POST /api/v1/account/2fa/setup
> - POST /api/v1/account/2fa/verify
> - POST /api/v1/account/2fa/challenge
> - POST /api/v1/account/2fa/recovery
> - POST /api/v1/account/2fa/disable (owner-only mutation)
> - GET  /api/v1/account/2fa/status
> - POST /api/v1/account/2fa/challenge-tokens
> - POST /api/v1/account/2fa/challenge-tokens/consume
> - GET  /api/v1/m2-entry-gate
>
> 14 typed exceptions are mapped to AD-15 §4 envelopes in `apps/api/main.py`.
> Alembic 0022 adds 5 `users.totp_*` columns + RLS policy 0013. 2FA is
> **industry-agnostic** (granted to ALL 4 canonical industries) — 2FA is
> a security baseline, not a manufacturing feature. AD-10 4-role allowlist
> (owner / member allowed; viewer / consultant_proxy denied) enforced at
> route via `require_role("owner")` (not via `require_capability`).
> Drift detector: `tests/integration/test_audit_logs_no_action_check_constraint.py`
> pins the "audit_logs has no CHECK" invariant for TWO_FACTOR_AUTH (the
> audit_logs table is intentionally CHECK-less per A5 design).
>
> **v1.12 (2026-08-09, Story 11.3, Epic 11)** — 3 NEW capabilities added
> for AD-20 snapshot persistence + AD-22 reversal 영구화 + W2 reopen flow:
> `SNAPSHOT_PERSISTENCE` (POST /close/snapshots/commit + GET /close/snapshots/{period_key}),
> `REVERSAL_EXECUTE` (POST /close/snapshots/reverse — distinct from
> REVERSAL_REQUEST which gates AD-22 reversal REQUEST 11-1 wire),
> `REOPEN_OPERATOR` (POST /close/sequence/reopen — W2 owner-only operator
> reopen with operator_action 4-value enum). All 3 granted to
> manufacturing-kind 3종 (manufacturing / manufacturing_service /
> manufacturing_service_other); service-only ❌ (403 INDUSTRY_NOT_SUPPORTED).
> AD-25 4-channel publisher wire (`ai_cache` + `cost_engine_cache` +
> `fiscal_period_cache` + `closing_snapshot_cache`) is industry-agnostic
> (no capability gate — it's a cross-cutting infra notification).
>
> **v1.11 (2026-08-08, Story 11.2, Epic 11)** — `CLOSE_SEQUENCE_LOCK`
> capability wire (PRD §F11.1 + §8.M11(a)) for the 4-stage close sequence
> (divisions → manufacturing → abc → common) + partial-close guard
> (PARTIAL_CLOSE_BLOCKED) + ALREADY_CONFIRMED (fiscal_periods.status=
> 'closed'). Granted to manufacturing-kind 3종; service-only ❌.
>
> **v1.10 (2026-08-08, Story 11.1, Epic 11)** — `REVERSAL_REQUEST`
> capability wire (PRD §F11.3) for AD-22 reversal sequence (sign-negating
> + corrected row) + AD-25 1-channel publisher (`ai_cache` only). Granted
> to manufacturing-kind 3종; service-only ❌ (no inventory ledger to reverse).
> POST /close/reversal-requests + GET /close/reversal-requests/{correction_group_id}
> + POST /close/cache-invalidation 3 NEW routes registered.
>
> **v1.6 (2026-08-04, Story 5.2)** — `Capability.INVENTORY_LEDGER` row
> confirmed wired for manufacturing-kind 3종 (manufacturing /
> manufacturing_service / manufacturing_service_other); service-only
> ❌ (403 INDUSTRY_NOT_SUPPORTED). 4 HTTP routes registered
> (POST /events, GET /period-closing, GET /carry-chain,
> POST /reversal-requests). Drift protection:
> `tests/integration/test_inventory_ledger_capability.py` (T9.2).
>
> **v1.5 (2026-08-03, Story 5.1)** — `Capability.OPENING_INVENTORY` row
> confirmed (already wired since Story 3.3 baseline; 5-1 explicit pin).
> Service industry is auto no-op (carry chain returns empty decisions).
>
> **v1.4 (2026-08-02, Story 4.4)** — V8 골든 byte-identical 회귀 매트릭스
> (4 industries × 3 baseline shapes = 12 fixtures) 가 CI mandatory gate 로
> 추가됨. Industry canonical names parity 정렬 (manufacturing_service /
> manufacturing_service_other). `verification_log.action` 에
> `verify_v8_golden_match` audit action 추가 (A5 forward-lock). Capability
> 행 자체는 변경 없음 — V8 은 COST_CALCULATION 응답 envelope 내부 검증
> 으로 wire 됨.
>
> **v1.3 (2026-08-03, Story 4.3)** — verification envelope (V1·V4·V7·V8)
> exposed via `CalcResponse.verdict`. `COST_CALCULATION` capability
> unchanged (no new row); the verdict envelope is wired INTO the existing
> calc response. AD-12 ordering invariant + per-industry V7 firing matrix
> codified (see `docs/conventions.md §0.5` + `docs/cost-engine.md
> #verification-envelope-v1v4v7v8`).
>
> **v1.2 (2026-08-02, Story 4.2)** — POST /api/v1/calc endpoint wired
> behind `COST_CALCULATION` capability; service tenants return 403
> INDUSTRY_NOT_SUPPORTED (Epic 9 ABC is their path).
>
> **v1.9 (2026-08-08, Story 6.2, Epic 6)** — `MONTHLY_CLOSING_REPORT` capability 6-1 wire (월 마감 보고서 read-only join — closing snapshot × ledger events 2-source aggregate, D1 결정 2026-08-08 fiscal_period_snapshots 가 V4 contract source 에서 제외 — PRD §6.1 산식 체인이 manufacturing_cost KRW 임을 명시) extends with **closing report view modes** (READY / PARTIAL / EMPTY 3-state classifier) + **V4 closing-period consistency verification** (3-source extension: ledger + closing snapshot + product whitelist, D1 결정) + **KRW/USD dual display** (PRD §F5.2 — 한국은행 USD/KRW 매매기준율 banker's rounding parity) + 3 NEW routes (`GET /monthly-closing-report` + `GET /monthly-closing-report/audit-trail` + `GET /monthly-closing-report/v4-verdict`) + `ActionClass.MONTHLY_CLOSING_REPORT` 6-2 deferred V4 골든 fixture fill (6-1 T10.5 carry-over close — `v4_closing_period_pass_manufacturing.json` + `v4_closing_period_fail_manufacturing.json` 2 NEW V8 골든 fixtures) + V8 골든 fixture count 16 → 18 (12 V8 baseline + 2 V3 + 4 V4/A11 6-2). Capability 행 자체는 변경 없음 — `MONTHLY_CLOSING_REPORT` capability 6-1 에서 wire done. View mode + V4 verdict 는 response envelope 내부 surface.
>
> **v1.1 (2026-08-02, Story 4.1)** — added `COST_CALCULATION` row.

## Wire contract: `POST /api/v1/calc` response envelope (Story 4.3)

`COST_CALCULATION` 통과 시 응답 envelope:

```python
class CalcResponse(BaseModel):
    # ... 기존 fields (tenant_id, period_key, 4 KRW + result_hash + state + baseline_revision + trace_id)
    state: Literal["verified"] = "verified"   # AD-20 transition: draft → verified via V1·V4·V7·V8 passed
    verdict: Verdict                            # NEW (Story 4.3) — verification envelope
```

**State machine (AD-20 invariant)** — `state ∈ Literal["draft", "verified", "committed", "reversed"]`. 본 스토리 범위는 `verified` 도달까지. `committed` / `reversed` 전이는 Epic 11 M11 owner.

**Verdict envelope wire shape** — `verification_status ∈ Literal["passed", "failed"]` (AD-20 외부 노출 invariant — `'pending'` 부재). 200 OK envelope에 포함되며, 실패 시 ROLLBACK + 200 OK + verdict envelope (NOT 4xx — 계산 자체는 성공, lock만 service layer 책임).

**Per-industry V* firing matrix (AD-12 spec interpretation)** — `manufacturing` / `manufacturing_service` / `manufacturing_service_other` 3 industry는 V1·V4·V8 발동 + V7 silent skip (3 rules). `service` industry는 V1·V4·V7·V8 모두 발동 (4 rules). Epic 9 9-1 wire 후 V7 ABC 무결성 검증 활성화.

**Story 4.4 V8 골든 회귀 매트릭스** — `tests/regression_v8/test_regression_v8_fixtures.py` (28+ cases, `@pytest.mark.v8_regression` — mandatory, no skip). 4 industries × 3 baseline shapes (b-small / b-standard / b-complex) = 12 골든 JSON. `verify_v8_golden_match` audit action (Story 4.4 forward-lock) — V8 fail 시 `verification_log.action = 'verify_v8_golden_match'` 으로 INSERT (CR 1.1 audit-first).

## Industries (PRD §4.1 4지선다)

| Industry | Description |
|---|---|
| `manufacturing` | ① 제조업 — 전통 개별원가 엔진 |
| `service` | ② 서비스업 — ABC 엔진 |
| `manufacturing_service` | ③ 제조+서비스 (겸영) |
| `manufacturing_service_other` | ④ 제조+서비스+기타 |

## Capabilities (Story 1.1 §AC #2, Epic 2 회고 A3, Epic 1 회고 A4)

| Capability | Story | manufacturing | service | manufacturing_service | manufacturing_service_other |
|---|---|---|---|---|---|
| `BOM` | 2.2 | ✅ | ❌ | ✅ | ✅ |
| `OPENING_INVENTORY` | 5.1 | ✅ | ❌ | ✅ | ✅ |
| `INVENTORY_LEDGER` | 5.2 | ✅ | ❌ | ✅ | ✅ |
| `INVENTORY_CLOSING_GUARD` | 5.3 | ✅ | ❌ | ✅ | ✅ |
| `MONTHLY_CLOSING_REPORT` | 6.1 | ✅ | ❌ | ✅ | ✅ |
| `COST_POOL` | 9.x | ❌ | ✅ | ✅ | ✅ |
| `ACTIVITY` | 9.x | ❌ | ✅ | ✅ | ✅ |
| `DRIVER` | 9.x | ❌ | ✅ | ✅ | ✅ |
| `SEGMENT_SPLIT` | 9.x | ❌ | ❌ | ✅ | ✅ |
| `AI_EXTRACT` | 1.3 | ✅ | ✅ | ✅ | ✅ |
| `PRODUCT` | 2.1 | ✅ | ✅ | ✅ | ✅ |
| `PRODUCT_MATERIAL` | 2.1 | ✅ | ❌ | ✅ | ✅ |
| `MONTHLY_INPUT_PRODUCTION` | 3.1 | ✅ | ❌ | ✅ | ✅ |
| `COST_CALCULATION` | 4.1 | ✅ | ❌ | ✅ | ✅ |
| `REVERSAL_REQUEST` | 11.1 | ✅ | ❌ | ✅ | ✅ |
| `CLOSE_SEQUENCE_LOCK` | 11.2 | ✅ | ❌ | ✅ | ✅ |
| `SNAPSHOT_PERSISTENCE` | 11.3 | ✅ | ❌ | ✅ | ✅ |
| `REVERSAL_EXECUTE` | 11.3 | ✅ | ❌ | ✅ | ✅ |
| `REOPEN_OPERATOR` | 11.3 | ✅ | ❌ | ✅ | ✅ |
| `TWO_FACTOR_AUTH` | 12.1 | ✅ | ✅ | ✅ | ✅ |
| `BACKUP_EXPORT` | 12.2 | ✅ | ✅ | ✅ | ✅ |
| `ACCOUNT_DELETION` | 12.3 | ✅ | ✅ | ✅ | ✅ |
| `BUDGET_SCENARIO` | 8.1 | ✅ | ✅ | ✅ | ✅ |
| `CVP_SIMULATION` | 7.1 | ✅ | ✅ | ✅ | ✅ |
| `ABC_CALCULATION` | 9.1, 9.2 | ✅ | ✅ | ✅ | ✅ |

## Notes

- **COST_CALCULATION (Story 4.1)** — gated to industries with a
  manufacturing footprint. Service-only tenants use Epic 9 ABC costing
  (COST_POOL / ACTIVITY / DRIVER) instead. The capability gate is
  enforced at the FastAPI route boundary
  (`apps/api/main.py` + `m3_calculate` module), NOT inside the engine.
  The engine itself (`packages.cost_engine.core.period_cost`) is pure
  and industry-agnostic — it ALWAYS returns `state="draft"` (AD-22
  append-only-leaning). Service layer owns `verified` / `committed`
  / `reversed` transitions.
- **PRODUCT** (catalog) is granted to every industry — service tenants
  still register `product` + `goods` + `service` types (R6 from CR 2.1).
- **PRODUCT_MATERIAL** gates the `material` + `semi_product` types.
  Service tenants cannot register raw materials or semi-finished goods
  (no BOM menu → no physical catalog entries).
- **MONTHLY_INPUT_PRODUCTION** gates the [생산] tab in m2_input only.
  The other 5 streams (orders/sales/purchases/expenses/labor) are
  **ungated** — every industry has them.
- **FTE 정밀 계산 (Story 3.2)** — [`MONTHLY_INPUT_LABOR` capability의 일부].
  추가 capability 부재. PRD §6.1 인건비 구성 (기본급·시간외·복리후생·
  상여·퇴직충당금) + `pay_type` 분기 (monthly 정규직 vs daily 일용직)
  가 [인원] 탭에 통합됨. 직급별 capability 분기 불필요.
- **테넌트별 payroll 정책 override** — `tenant_settings.payroll.*` JSONB
  sub-block으로 per-tenant override (Story 3.2 신규 도입). 빈 dict
  `{}`은 PRD §6.1 default (`monthly_salary_basis_krw=2_500_000`,
  `workdays_in_month=22`, `standard_monthly_hours=228`,
  `company_burden_rate=0.115`)로 fallthrough.
- **음수재고·조업도 실시간 경고 (Story 3.3)** — capability-ungated.
  PRD §A11 오류의 가시화 정책은 입력 시 warning(200 OK + 진행 허용)
  → 마감 시 Epic 4 first_calc hook에서 임계 위반 차단. m2_input 응답에
  `warnings[]`, `is_blocked`, `warnings_count`, `top_n_severity` 4개
  필드가 항상 포함됨. service-only 테넌트는 inventory projection 빈
  결과 → 0개 경고 (예외 아님). 2개 warning code만 노출:
  `NEGATIVE_CLOSING_INVENTORY` (PRD §V3) + `OVERCAPACITY_OPERATING_RATE`
  (PRD §V5). Epic 5 5-1 단계에서 opening_inventory JSONB의 cj-style
  default=0 + ledger-backed read로 자동 전월 기말 carry-chain 진입
  (`TODO(epic-5)` marker — closed in Story 5-2; A19 carry-over sprint
  removed `inventory_projection.py` entirely; math surface is now in
  `packages/services/m2_input/inventory_math.py`).
- **AI_EXTRACT** is granted to every industry (PRD §4.2 AI cross-cutting
  feature). Tenant-only restriction is PIPA consent, not industry.

## Defense in depth

- The matrix above is mirrored in three places:
  1. `apps/api/core/capability.py::Capability` enum + `_INDUSTRY_CAPABILITIES`
  2. `apps/web/lib/menu-config.ts::INDUSTRY_ALLOWED_PRODUCT_TYPES` +
     `INDUSTRY_VISIBLE_STREAMS` (TS projection for sidebar / tabs)
  3. `supabase/policies/0006_products_rls.sql` (RLS tenant_id predicate)
- Drift is caught by:
  - `tests/integration/test_capability_consistency.py`
  - `tests/integration/test_m2_input_label_consistency.py` (Story 3.1)
  - `tests/integration/test_menu_config_consistency.py` (Story 1.1)
- Enforcement order on a write:
  1. `get_tenant_context` reads JWT → `TenantContext`
  2. `require_capability(capability)` checks industry via
     `SettingsService.get_tenant_settings`
  3. Service layer validates per-stream shape
  4. RLS row-level policy enforces `tenant_id = JWT.tenant_id`

## Adding a new capability

1. Add to `Capability` enum + 4-industry mapping in
   `apps/api/core/capability.py`
2. If UI-visible, add to TS mirror (`apps/web/lib/menu-config.ts`)
3. Extend `tests/integration/test_capability_consistency.py` (one param
   row per capability per industry)
4. Update this matrix
5. (If new RLS) add policy file `supabase/policies/XXXX_<table>_rls.sql`

## Story → capability reference

| Story | Capabilities introduced or gated |
|---|---|
| 1.1 — Industry selector | (none — pure framework) |
| 1.3 — AI extraction | `AI_EXTRACT` |
| 2.1 — Product master | `PRODUCT`, `PRODUCT_MATERIAL` |
| 2.2 — BOM matrix | `BOM` |
| 3.1 — Six-stream monthly input | `MONTHLY_INPUT_PRODUCTION` |
| 3.2 — FTE precision + daily labor | (no new capability; FTE precision is part of `MONTHLY_INPUT_LABOR` ungated path; per-tenant payroll override via `tenant_settings.payroll.*` JSONB sub-block) |
| 3.3 — Negative inventory & overcapacity warning | (no new capability; warning aggregate is part of `MONTHLY_INPUT_LABOR` ungated path + PRD §V3/§V5 universal gating on inventory-bearing product types only; service tenants → 0 inventory warnings by construction) |
| 4.1 — Pure cost engine (periodic §6.1 산식) | `COST_CALCULATION` (granted to mfg / mfg+service / mfg+service+other; service-only tenants use ABC instead) |
| 4.3 — Verification envelope (V1·V4·V7·V8) | (no new capability; verdict envelope wired INTO `COST_CALCULATION` response) |
| 4.4 — V8 골든 byte-identical CI gate | (no new capability; 12 fixture 매트릭스가 `COST_CALCULATION` 응답 verdict envelope 의 V8 fail-path audit action (`verify_v8_golden_match`) 으로 wire) |
| 5.x — Inventory | `OPENING_INVENTORY`, `INVENTORY_LEDGER` |
| 9.x — ABC | `COST_POOL`, `ACTIVITY`, `DRIVER`, `SEGMENT_SPLIT`, `ABC_CALCULATION` (9.1) |

## Changelog

- 2026-08-01 — Initial matrix (Epic 1 회고 A4 + Epic 2 회고 A3 + Epic 3 Story 3.1).
- 2026-08-01 — Story 3.2 footnote added (payroll override + labor precision path).
- 2026-08-01 — Story 3.3 footnote added (음수재고·조업도 실시간 경고;
  capability-ungated; warnings aggregate on m2_input state response).
- 2026-08-02 — v1.1 (Story 4.1): `COST_CALCULATION` row added; service-only
  tenants do NOT have COST_CALCULATION (Epic 9 ABC instead). Engine is
  industry-agnostic — gate is enforced at the FastAPI route boundary.
- 2026-08-02 — v1.4 (Story 4.4): V8 byte-identical 골든 매트릭스
  (4 industries × 3 baseline shapes) + `verify_v8_golden_match` audit
  action forward-lock. Industry canonical names parity 정렬. Capability
  행 자체는 변경 없음.
- 2026-08-03 — v1.5 (Story 5.1, Epic 5): 기초재고 자동 이월 체인 (PRD §F4.1)
  추가. `Capability.OPENING_INVENTORY`는 이미 manufacturing-kind
  industry 3종 (manufacturing / manufacturing_service /
  manufacturing_service_other) 에 wired. Service industry는 자동
  no-op (carry chain returns empty decisions — inventory-bearing
  products 없음). Capability 행 자체는 변경 없음 (5-1 wire는
  기존 Capability 사용).
- 2026-08-04 — v1.6 (Story 5.2, Epic 5): `INVENTORY_LEDGER` capability
  row confirmed + 4 HTTP routes registered behind the gate. Drift
  protection added (`tests/integration/test_inventory_ledger_capability.py`).
  Service-only tenants continue to be excluded (403
  INDUSTRY_NOT_SUPPORTED — BOM 없음 → ledger 의미 없음). Capability
  행 자체는 변경 없음 (5-2 wire는 5-1 의 Capability.OPENING_INVENTORY
  와 동일한 manufacturing-kind 3종 wiring 사용).
- 2026-08-06 — v1.7 (Story 5.3): `CLOSING_GUARD` capability wire (manufacturing 3종 ✅ / service-only ❌) + `ActionClass.CLOSING_GUARD` 3 values 채움 + `ActionClass.VERIFICATION` V3 value add (4 → 5) + V3 verification surface wire + Alembic 0016 SQL CHECK constraint (chk_opening_inventory_manual_reject) + monthly_input_rows.created_via column + idx_closing_guard_audit index.
- 2026-08-07 — v1.8 (Story 6.1, Epic 6): `MONTHLY_CLOSING_REPORT` capability wire (manufacturing 3종 ✅ / service-only ❌ INDUSTRY_NOT_SUPPORTED) + 3 NEW routes (`POST /closing-period/confirm` + `GET /closing-period/status` + `GET /closing-period/audit-trail`) + `ActionClass.CLOSING_PERIOD` 3 values 채움 (`closing_period_confirmed` + `closing_period_blocked` + `closing_period_snapshot_inconsistency`) + `ActionClass.VERIFICATION` V4 value add (5 → 6) + V4 closing-period-snapshot verification surface wire + Alembic 0017 (`chk_closing_period_status` 3-state lifecycle + `closing_snapshot_event_count` non-negative CHECK + `finalized_at` + `closed_by_actor_id` + `idx_closing_period_audit` JSONB index) + monthly_input_periods.status lifecycle = `open` → `closing` → `closed` 1-way state machine (AD-6 close lock) + closing_snapshot ledger event wire (5-2 11th event_type).
- 2026-08-08 — v1.9 (Story 6.2, Epic 6): `MONTHLY_CLOSING_REPORT` capability
  6-1 wire done + 6-2 report view modes (READY/PARTIAL/EMPTY 3-state) +
  V4 closing-period consistency 4-source verification + KRW/USD dual
  display (PRD §F5.2 banker's rounding) + 3 NEW routes (report +
  audit-trail + v4-verdict) + V8 골든 fixture 16 → 18 (closing-period-fixture-1
  + fiscal-period-snapshot-fixture-1 2 NEW V8 골든 from 6-1 T10.5 carry-over
  close). Capability 행 자체는 변경 없음 (6-1 wire 그대로 사용).
- 2026-08-12 — v1.14 (Story 12.2, Epic 12): `BACKUP_EXPORT` capability wire
  (industry-agnostic — ALL 4 canonical industries ✅; CR 12-1 L4 precedent —
  "백업은 운영자 인프라") + 3 NEW routes under `/api/v1/account/backups/*`
  (`GET /recent` + `GET /{backup_id}/download` + `POST /trigger`) +
  `ActionClass.ACCOUNT_BACKUP` 5 values 채움 (`backup_created` +
  `backup_failed` + `backup_retention_purged` + `backup_downloaded` +
  `backup_triggered`) + Alembic 0024 (`tenant_backups` table + 12 columns
  + 2 indexes + partial UNIQUE on `(tenant_id, backup_date) WHERE purged_at
  IS NULL`) + RLS 0014 (5-policy split: same-tenant SELECT + owner-only
  SELECT + same-tenant INSERT + UPDATE forbidden + DELETE forbidden) +
  packages/services/m12_account/backup_export pure kernel subtree
  (stdlib-only JSON serialization + sha256 hashing + 7-table dump) +
  `apps/api/jobs/backup_daily.py` (KST 02:00 = UTC 17:00 cron entry) +
  `apps/api/jobs/backup_retention.py` (KST 03:00 = UTC 18:00 retention sweep).
  NFR4: RPO 24h / RTO 4h / 30-day backup retention. AD-10 owner-only gate
  enforced at route via `require_role("owner")` (NOT `require_capability`)
  — capability is documented but intentionally NOT enforced as a route gate
  per CR 12-1 L4 precedent (industry-agnostic security baseline).
- 2026-08-08 — v1.10 (Story 11.1, Epic 11): `REVERSAL_REQUEST` capability wire
  (manufacturing 3종 ✅ / service-only ❌) + 3 NEW routes (`POST /close/reversal-requests`
  + `GET /close/reversal-requests/{correction_group_id}` + `POST /close/cache-invalidation`)
  + `ActionClass.M11_REVERSAL` 2 values 채움 (`m11_reversal_handler_invoked` +
  `inventory_ledger_reversal_logged`) + AD-22 reversal ledger wire +
  AD-25 1-channel publisher (`ai_cache`) + Alembic 0019
  (`cache_invalidation_log` table + 1-channel CHECK + `reversal_log` table
  + partial UNIQUE on `(tenant_id, reverses_event_id)`).
- 2026-08-08 — v1.11 (Story 11.2, Epic 11): `CLOSE_SEQUENCE_LOCK` capability
  wire (manufacturing 3종 ✅ / service-only ❌) + 4 NEW routes
  (`POST /close/sequence/initiate` + `POST /close/sequence/step-complete`
  + `GET /close/sequence/state` + `POST /close/sequence/confirm`) +
  `ActionClass.MONTHLY_CLOSING` 4 values 채움 (`closing_sequence_initiated`
  + `closing_sequence_step_completed` + `closing_sequence_confirmed` +
  `closing_sequence_audit_failed`) + fiscal_periods greenfield table
  (Alembic 0020) + 4-stage sequence (divisions → manufacturing → abc →
  common) + AD-6 INSERT 거부 guard.
- 2026-08-10 — v1.13 (Story 12.1, Epic 12): `TWO_FACTOR_AUTH` capability
  wire (industry-agnostic — ALL 4 canonical industries ✅) +
  5 NEW routes under `/api/v1/2fa` (`POST /setup` + `POST /verify` +
  `POST /challenge` + `POST /recovery` + `POST /disable`) +
  `ActionClass.TWO_FACTOR_AUTH` 6 values 채움
  (`two_factor_setup_initiated` + `two_factor_setup_completed` +
  `two_factor_challenge_passed` + `two_factor_challenge_failed` +
  `two_factor_recovery_consumed` + `two_factor_disabled`) +
  Alembic 0022 (users `totp_secret` BYTEA + 4 totp_* columns +
  `totp_recovery_codes_hash` JSONB) + RLS 0013 + NFR6 AES-256-GCM
  column-level encryption (12-byte nonce + ct + 16-byte tag) +
  NFR5 TLS in-transit (plaintext secret NEVER logged) +
  `packages/services/m12_account/` pure kernel subtree
  (RFC 6238 TOTP + PBKDF2-HMAC-SHA256 recovery hashing +
  2FA gate validation) + `apps/api/core/crypto.py` +
  `apps/api/core/key_manager.py` + service layer (CR 1.1 audit-first
  via `emit_audit_typed` + idempotent no-op re-setup + lockout state
  mgmt + AD-10 4-role gate) + 2FA challenge token HS256 JWT
  (5-min TTL + purpose=`two_factor_challenge`).
- 2026-08-09 — v1.12 (Story 11.3, Epic 11): 3 NEW capability rows added
  (`SNAPSHOT_PERSISTENCE` + `REVERSAL_EXECUTE` + `REOPEN_OPERATOR` —
  all manufacturing 3종 ✅ / service-only ❌) + 4 NEW routes
  (`POST /close/snapshots/commit` + `POST /close/snapshots/reverse`
  + `POST /close/sequence/reopen` + `GET /close/snapshots/{period_key}`)
  + `ActionClass.SNAPSHOT_PERSISTENCE` 4 values +
  `ActionClass.REOPEN_OPERATOR` 2 values 채움 + AD-25 4-channel publisher
  wire (`ai_cache` + `cost_engine_cache` + `fiscal_period_cache` +
  `closing_snapshot_cache`) + Alembic 0021 (`cache_invalidation_log`
  channel CHECK 1 → 4 expansion + 4 per-channel indexes) + RLS 0012
  (cache_invalidation_log 4-policy split) + W2 reopen operator flow
  (`operator_action` 4-value enum + `reason` length 20-500) +
  AD-20 fiscal_period_snapshots state machine
  (`draft` → `verified` → `committed` → `reversed`) + AD-22 reversal
  영구화 (3-tier guard: monthly_input_periods.status='closed' +
  fiscal_periods.status='closed' + fiscal_period_snapshots.state='committed').
- Future: each capability addition appends one row to the matrix and
  one row to the Changelog.
- 2026-08-16 — v1.18 (Story 9.1, Epic 9): `ABC_CALCULATION` capability
  wire (industry-agnostic — ALL 4 canonical industries ✅; CR 12-1 L4
  precedent — "ABC는 운영 인프라") + 4 NEW routes under
  `/api/v1/abc/*` (`POST /cost-pools` + `POST /activities` +
  `POST /drivers/validate` + `POST /validate`) +
  `packages/cost_engine/abc_engine.py` pure kernel (A19 cohesion
  pattern 6번째 surface — 4 functions + 3 frozen dataclasses +
  4 typed exceptions + 7 constants, AD-5 stdlib-only, no I/O, V8
  determinism sha256:64-hex) + service layer `AbcValidationService`
  with `_to_validation_state` ORM→kernel boundary (CR 12-1 L3
  precedent) + `validate_abc_pct_list` 3-layer defense (CR 12-5 L3)
  + 4 NEW typed exception envelopes (422 COST_POOL_INVALID_SUM +
  422 ACTIVITY_INVALID_SUM + 422 DRIVER_INVALID_SUM +
  404 ABC_VALIDATION_NOT_FOUND) + Alembic/RLS SKIPPED (validation
  only, no INSERT/UPDATE/DELETE — CR 1.1 read-mostly invariant;
  A5 forward-lock 변경 0). Drift detector:
  `tests/integration/test_capability_matrix_v1_18_drift.py`.