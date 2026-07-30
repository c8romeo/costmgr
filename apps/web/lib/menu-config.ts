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

/** Per-card icon (story-level hint; Story 0.5 supplies the icon set). */
export const INDUSTRY_ICON: Record<Industry, string> = {
  manufacturing: "Factory",
  service: "Briefcase",
  manufacturing_service: "Layers",
  manufacturing_service_other: "FolderTree",
};
