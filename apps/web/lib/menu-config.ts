/**
 * apps/web/lib/menu-config.ts — TypeScript mirror of the canonical
 * industry → menu map defined in
 * `packages/services/m0_onboarding/industry_menu.py`.
 *
 * THIS FILE IS NOT THE SOURCE OF TRUTH. The Python module is canonical
 * (AD-23: one tenant_settings aggregate, one enum per module). Drift
 * between this file and the Python enum is caught by
 * `tests/integration/test_menu_config_consistency.py`.
 *
 * Per Story 1.1 — Task 3.5: the menu ordering, Korean labels, and
 * tooltip strings MUST match the Python side exactly. Update both
 * together.
 */

export const INDUSTRY_VALUES = [
  "manufacturing",
  "service",
  "manufacturing_service",
  "manufacturing_service_other",
] as const;

// `(typeof INDUSTRY_VALUES)[number]` is TS's "indexed access type" — extracts
// the literal union from a const array. `number` here is the keyword for
// "any element of this tuple", not the JS `number` primitive. Safe to use
// outside money contexts.
/* eslint-disable-next-line @typescript-eslint/no-restricted-types */
export type Industry = (typeof INDUSTRY_VALUES)[number];

export const INDUSTRY_LABEL_KO: Record<Industry, string> = {
  manufacturing: "제조업",
  service: "서비스업",
  manufacturing_service: "제조+서비스",
  manufacturing_service_other: "제조+서비스+기타",
};

export const GRACE_PERIOD_DAYS = 7;
export const SEGMENT_SPLIT_TOOLTIP = "재무제표 업로드 필수 (§7.3 [A10])";

// Canonical industry → Korean menu label list. The order is preserved
// per PRD §8 (display order). The frontend renders the strings verbatim.
// Story 12.5: "계정 보안" added for all 4 industries (2FA is industry-agnostic
// security baseline per CR 12-1 L4 — every user must be able to enroll/disable).
export const INDUSTRY_MENU_MAP: Record<Industry, readonly string[]> = {
  manufacturing: [
    "품목",
    "BOM",
    "기초재고",
    "수불부",
    "계정과목",
    "부서",
    "거래처",
    "AI추출",
    "시뮬레이션",
    "예산",
    "보고서",
    "마감",
    "계정관리",
    "계정 보안",
  ],
  service: [
    "원가풀",
    "활동",
    "동인",
    "계정과목",
    "부서",
    "거래처",
    "AI추출",
    "시뮬레이션",
    "예산",
    "보고서",
    "마감",
    "계정관리",
    "계정 보안",
  ],
  manufacturing_service: [
    "품목",
    "BOM",
    "기초재고",
    "수불부",
    "원가풀",
    "활동",
    "동인",
    "카브아웃 분할",
    "계정과목",
    "부서",
    "거래처",
    "AI추출",
    "시뮬레이션",
    "예산",
    "보고서",
    "마감",
    "계정관리",
    "계정 보안",
  ],
  manufacturing_service_other: [
    "품목",
    "BOM",
    "기초재고",
    "수불부",
    "원가풀",
    "활동",
    "동인",
    "카브아웃 분할",
    "계정과목",
    "부서",
    "거래처",
    "AI추출",
    "시뮬레이션",
    "예산",
    "보고서",
    "마감",
    "계정관리",
    "계정 보안",
  ],
};

/** Per-industry UI hints (PRD §4.1 4지선다 표 descriptions). */
export const INDUSTRY_DESCRIPTION_KO: Record<Industry, string> = {
  manufacturing: "전통 개별원가 엔진 — BOM·기초재고·수불부 기반",
  service: "ABC 엔진 — 원가풀·활동·동인 기반",
  manufacturing_service: "두 엔진 병행 — 카브아웃 분할 필수",
  manufacturing_service_other:
    "두 엔진 + '기타' 부문 격리 버킷 — 원가계산 제외",
};

/**
 * Per-industry lucide-react icon name.
 * Story 0.5 T8.1 — closes Story 1.1 F-33 deferral.
 * Mirror in packages/services/m0_onboarding/industry_menu.py (F-37).
 * Drift detected by tests/integration/test_menu_config_consistency.py.
 */
export const INDUSTRY_ICON: Record<Industry, string> = {
  manufacturing: "Factory",
  service: "Briefcase",
  manufacturing_service: "Layers",
  manufacturing_service_other: "Boxes",
};

// ─────────────────────────────────────────────────────────────────────
// Story 2.1 — product type catalog (PRD §8.M1)
//
// Mirror of the Python `ProductType` enum. Drift between this and
// `packages/services/m1_baseline/schemas.py::ProductType` is caught by
// `tests/integration/test_capability_consistency.py`.
//
// Allowed-type-per-industry is derived from the Capability gate:
//   - INDUSTRY_ALLOWED_PRODUCT_TYPES[industry] ← types a tenant of that
//     industry can register. `service` tenants see only `service`-typed
//     products; the rest see all 5.
// ─────────────────────────────────────────────────────────────────────

export const PRODUCT_TYPE_VALUES = [
  "product",
  "semi_product",
  "material",
  "goods",
  "service",
] as const;

/* eslint-disable-next-line @typescript-eslint/no-restricted-types */
export type ProductType = (typeof PRODUCT_TYPE_VALUES)[number];

export const PRODUCT_TYPE_LABEL_KO: Record<ProductType, string> = {
  product: "제품",
  semi_product: "반제품",
  material: "원자재",
  goods: "상품",
  service: "서비스",
};

// 3-letter code prefix per type (PRD §8.M1 "코드"). Mirror of
// `packages/services/m1_baseline/schemas.py::PRODUCT_TYPE_PREFIX`.
export const PRODUCT_TYPE_PREFIX: Record<ProductType, string> = {
  product: "PRD",
  semi_product: "SEM",
  material: "MAT",
  goods: "GDS",
  service: "SVC",
};

/** Per-type color for the badge (CSS custom-property slot name in globals.css). */
export const PRODUCT_TYPE_COLOR_VAR: Record<ProductType, string> = {
  product: "--badge-product-color",
  semi_product: "--badge-semi-color",
  material: "--badge-material-color",
  goods: "--badge-goods-color",
  service: "--badge-service-color",
};

/**
 * Per-industry allowed product-type subset. Mirror of the Python
 * `Capability` × `ProductType` matrix in `apps/api/core/capability.py`
 * — drift caught by `tests/integration/test_capability_consistency.py`.
 *
 * Rule (Story 2.1, AC #6, R6 review patch):
 *   - Every industry with the `PRODUCT` capability gets the catalog
 *     trio (`product`, `goods`, `service`) — a service tenant can
 *     still sell finished products and trade goods even without a BOM.
 *   - `material` + `semi_product` are gated by the additional
 *     `PRODUCT_MATERIAL` capability (only granted to industries that
 *     own a BOM — manufacturing, mfg+service, mfg+service+other).
 */
export const INDUSTRY_ALLOWED_PRODUCT_TYPES: Record<Industry, readonly ProductType[]> = {
  manufacturing: ["product", "semi_product", "material", "goods", "service"],
  service: ["product", "goods", "service"],
  manufacturing_service: ["product", "semi_product", "material", "goods", "service"],
  manufacturing_service_other: ["product", "semi_product", "material", "goods", "service"],
};

// ─────────────────────────────────────────────────────────────────────
// Story 3.1 — six-stream monthly input visibility (PRD §8.M2(b))
//
// Mirror of the Python `STREAMS_FOR_INDUSTRY` map in
// `packages/services/m2_input/stream_completion.py` — drift caught by
// `tests/integration/test_m2_input_label_consistency.py`.
//
// Rule: service tenants hide the [생산] tab (no manufacturing capability).
// The other 5 streams are visible to every industry. Backend gate is
// `Capability.MONTHLY_INPUT_PRODUCTION`; this map is the UI projection.
// ─────────────────────────────────────────────────────────────────────

export const MONTHLY_INPUT_STREAM_VALUES = [
  "orders",
  "production",
  "sales",
  "purchases",
  "expenses",
  "labor",
] as const;

/* eslint-disable-next-line @typescript-eslint/no-restricted-types */
export type MonthlyInputStream = (typeof MONTHLY_INPUT_STREAM_VALUES)[number];

export const MONTHLY_INPUT_STREAM_LABEL_KO: Record<MonthlyInputStream, string> = {
  orders: "주문",
  production: "생산",
  sales: "판매",
  purchases: "구매",
  expenses: "경비",
  labor: "인원",
};

/** Per-industry visible-stream subset (PRD §8.M2(b)). */
export const INDUSTRY_VISIBLE_STREAMS: Record<Industry, readonly MonthlyInputStream[]> = {
  manufacturing: ["orders", "production", "sales", "purchases", "expenses", "labor"],
  service: ["orders", "sales", "purchases", "expenses", "labor"],
  manufacturing_service: ["orders", "production", "sales", "purchases", "expenses", "labor"],
  manufacturing_service_other: ["orders", "production", "sales", "purchases", "expenses", "labor"],
};

