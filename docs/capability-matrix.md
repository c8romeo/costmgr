# Capability Matrix

> **Single source of truth** for the `Industry × Capability` gating that
> Epic 1 / 2 / 3 stories need to coordinate. Replaces the per-story
> capability tables with one consolidated matrix.

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
| `COST_POOL` | 9.x | ❌ | ✅ | ✅ | ✅ |
| `ACTIVITY` | 9.x | ❌ | ✅ | ✅ | ✅ |
| `DRIVER` | 9.x | ❌ | ✅ | ✅ | ✅ |
| `SEGMENT_SPLIT` | 9.x | ❌ | ❌ | ✅ | ✅ |
| `AI_EXTRACT` | 1.3 | ✅ | ✅ | ✅ | ✅ |
| `PRODUCT` (catalog CRUD) | 2.1 | ✅ | ✅ | ✅ | ✅ |
| `PRODUCT_MATERIAL` | 2.1 | ✅ | ❌ | ✅ | ✅ |
| `MONTHLY_INPUT_PRODUCTION` | 3.1 | ✅ | ❌ | ✅ | ✅ |

## Notes

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
  (`TODO(epic-5)` marker in `inventory_projection.py`).
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
| 5.x — Inventory | `OPENING_INVENTORY`, `INVENTORY_LEDGER` |
| 9.x — ABC | `COST_POOL`, `ACTIVITY`, `DRIVER`, `SEGMENT_SPLIT` |

## Changelog

- 2026-08-01 — Initial matrix (Epic 1 회고 A4 + Epic 2 회고 A3 + Epic 3 Story 3.1).
- 2026-08-01 — Story 3.2 footnote added (payroll override + labor precision path).
- 2026-08-01 — Story 3.3 footnote added (음수재고·조업도 실시간 경고;
  capability-ungated; warnings aggregate on m2_input state response).
- Future: each capability addition appends one row to the matrix and
  one row to the Changelog.