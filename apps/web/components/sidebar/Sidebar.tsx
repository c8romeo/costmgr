/**
 * apps/web/components/sidebar/Sidebar.tsx — industry-aware left navigation.
 *
 * Story 1.1 — Task 4.1. Reads the menu from `useMenuContext()` and
 * renders one `<SidebarItem>` per entry. Items outside the active
 * menu are NOT rendered — that's the auto-toggle.
 *
 * UX-locked: WCAG AA contrast (Story ux-locked-decisions).
 *   - Active item: bold + left blue accent bar.
 *   - Hover: subtle background tint.
 *   - `카브아웃 분할` shows the §7.3 [A10] tooltip on hover (Task 4.3).
 *
 * Review patches applied:
 *   F-11 — `pathname.startsWith(href)` was a false-positive source: any
 *          sibling route whose path is a string prefix (`/dashboard/acc`
 *          vs `/dashboard/accounts`) lit up the wrong item. Replaced with
 *          an exact-match-or-path-segment check that honours the `/`
 *          segment boundary.
 */

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { CalcButton } from "@/components/calc/CalcButton";
import { SEGMENT_SPLIT_TOOLTIP } from "@/lib/menu-config";

import { useMenuContext } from "./MenuContext";
import { SidebarItem } from "./SidebarItem";

const ROUTE_BY_LABEL: Record<string, string> = {
  // cj-style N+13 + N+14 (D-Day MVP demo, 2026-09-14 KST) — ROUTE_BY_LABEL
  // updated to match the actual Next.js app/ routes. Manufacturing route
  // group uses `/(dashboard)/` so the group prefix doesn't appear in the
  // URL. Routes below are leaf paths with valid page.tsx (no synthetic
  // placeholder routes). 결정 wire 보존: env-free local dev only, LOW risk
  // (data table update only). `monthly_input_periods` has only one seeded
  // period (2026-08), so periodKey-bound routes hard-code that key.
  품목: "/m1-baseline/products",
  BOM: "/m1-baseline/products",
  기초재고: "/m2-input/period/2026-08",
  수불부: "/m2-input/period/2026-08",
  원가풀: "/budget/abc-allocation",
  활동: "/budget/abc-calculation",
  동인: "/budget/abc-validation",
  "카브아웃 분할": "/budget/pre-standard",
  계정과목: "/settings/wizard",
  부서: "/settings/wizard",
  거래처: "/settings/wizard",
  // AI추출 — page exists at /monthly-input/ai-extract but renders HTTP 500
  // (Server Component passes onClose event handler to Client Component —
  // real Next.js boundary bug, out of scope for route-rename edit).
  // Honestly DEFERRED — admin can navigate via direct URL.
  AI추출: "/monthly-input/ai-extract",
  시뮬레이션: "/simulation/cvp",
  예산: "/budget/abc-allocation",
  보고서: "/reports/15",
  마감: "/m2-input/period/2026-08/monthly-closing-report",
  계정관리: "/account/settings",
  // Story 12.5 — 2FA self-service UI (industry-agnostic security baseline)
  "계정 보안": "/account/security",
  // Story 12.2 — daily backup download UI (industry-agnostic security baseline)
  "백업 다운로드": "/account/backups",
};

/** F-11: path is active iff it equals `href` exactly or begins with
 *  `${href}/` (so segment boundaries are honoured and e.g.
 *  `/m2-input/period` does NOT light up `/m2-input/period/[periodKey]`). */
function isActivePath(pathname: string, href: string): boolean {
  if (pathname === href) return true;
  return pathname.startsWith(`${href}/`);
}

export interface SidebarProps {
  /** Access token forwarded from the Server Component layout (F-1, F-38). */
  accessToken?: string;
}

export function Sidebar({ accessToken }: SidebarProps = {}) {
  const { menu } = useMenuContext();
  const pathname = usePathname() ?? "";

  return (
    <nav
      aria-label="주 메뉴"
      style={{
        width: 232,
        minHeight: "100vh",
        padding: "1rem 0.5rem",
        background: "#f8fafc",
        borderRight: "1px solid #e2e8f0",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div style={{ marginBottom: "0.75rem" }}>
        <CalcButton accessToken={accessToken} />
      </div>
      <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
        {menu.map((label) => {
          const href = ROUTE_BY_LABEL[label] ?? "/dashboard";
          const active = isActivePath(pathname, href);
          const tooltip = label === "카브아웃 분할" ? SEGMENT_SPLIT_TOOLTIP : undefined;
          return (
            <li key={label} style={{ marginBottom: 2 }}>
              <Link
                href={href}
                style={{ textDecoration: "none", color: "inherit" }}
              >
                <SidebarItem label={label} active={active} tooltip={tooltip} />
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
