/**
 * apps/web/components/m1-baseline/products/ProductTypeBadge.tsx
 *
 * Story 2.1 — Task 5.3. Colored badge per product type (PRD §8.M1).
 *
 * Color pairs follow WCAG 2.1 AA contrast guidelines (≥ 4.5:1):
 *   - product     → bg-green-50  + text-green-700  (#15803d on #f0fdf4)
 *   - semi_product → bg-purple-50 + text-purple-700 (#7e22ce on #faf5ff)
 *   - material    → bg-blue-50   + text-blue-700   (#1d4ed8 on #eff6ff)
 *   - goods       → bg-orange-50 + text-orange-700 (#c2410c on #fff7ed)
 *   - service     → bg-gray-100  + text-gray-700   (#374151 on #f3f4f6)
 *
 * UX-locked: ko-KR label, Professional tone. The badge also carries an
 * `aria-label` so screen readers announce "원자재" rather than the enum
 * literal "material".
 *
 * When the product is inactive, an additional `data-inactive` style
 * overlay is applied (gray + strikethrough) per AC #5.
 */

import type { ProductType } from "@/lib/api-client";

export interface ProductTypeBadgeProps {
  productType: ProductType;
  /** When false, renders a muted overlay (gray + strikethrough). */
  isActive?: boolean;
}

interface BadgeStyle {
  background: string;
  color: string;
  borderColor: string;
}

const BADGE_STYLE: Record<ProductType, BadgeStyle> = {
  product: {
    background: "#f0fdf4",
    color: "#15803d",
    borderColor: "#bbf7d0",
  },
  semi_product: {
    background: "#faf5ff",
    color: "#7e22ce",
    borderColor: "#e9d5ff",
  },
  material: {
    background: "#eff6ff",
    color: "#1d4ed8",
    borderColor: "#bfdbfe",
  },
  goods: {
    background: "#fff7ed",
    color: "#c2410c",
    borderColor: "#fed7aa",
  },
  service: {
    background: "#f3f4f6",
    color: "#374151",
    borderColor: "#e5e7eb",
  },
};

const TYPE_LABEL_KO: Record<ProductType, string> = {
  product: "제품",
  semi_product: "반제품",
  material: "원자재",
  goods: "상품",
  service: "서비스",
};

// M8b: neutral fallback for an unknown productType. A future Story 2.3
// schema addition (e.g. `asset`) would otherwise produce an
// `undefined.color` crash. The fallback keeps the badge legible
// instead of crashing the table row.
const FALLBACK_STYLE: BadgeStyle = {
  background: "#f1f5f9",
  color: "#475569",
  borderColor: "#cbd5e1",
};
const FALLBACK_LABEL_KO = "알 수 없음";

export function ProductTypeBadge({
  productType,
  isActive = true,
}: ProductTypeBadgeProps) {
  const style = BADGE_STYLE[productType] ?? FALLBACK_STYLE;
  const label = TYPE_LABEL_KO[productType] ?? FALLBACK_LABEL_KO;

  return (
    <span
      role="img"
      aria-label={label}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "0.25rem",
        padding: "0.125rem 0.5rem",
        borderRadius: 9999,
        border: `1px solid ${style.borderColor}`,
        background: isActive ? style.background : "#f3f4f6",
        color: isActive ? style.color : "#9ca3af",
        fontSize: "0.75rem",
        fontWeight: 600,
        lineHeight: 1.4,
        textDecoration: isActive ? "none" : "line-through",
      }}
    >
      {label}
      {!isActive && (
        <span
          aria-hidden="true"
          style={{
            fontSize: "0.625rem",
            fontWeight: 500,
            marginLeft: "0.25rem",
            color: "#9ca3af",
          }}
        >
          (비활성)
        </span>
      )}
    </span>
  );
}
