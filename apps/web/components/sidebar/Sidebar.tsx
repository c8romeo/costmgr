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
  품목: "/dashboard/products",
  BOM: "/dashboard/bom",
  기초재고: "/dashboard/opening-inventory",
  수불부: "/dashboard/inventory-ledger",
  원가풀: "/dashboard/cost-pool",
  활동: "/dashboard/activity",
  동인: "/dashboard/driver",
  "카브아웃 분할": "/dashboard/segment-split",
  계정과목: "/dashboard/accounts",
  부서: "/dashboard/departments",
  거래처: "/dashboard/customers",
  AI추출: "/dashboard/ai-extract",
  시뮬레이션: "/dashboard/simulation",
  예산: "/dashboard/budget",
  보고서: "/dashboard/reports",
  마감: "/dashboard/close",
  계정관리: "/dashboard/account",
};

/** F-11: path is active iff it equals `href` exactly or begins with
 *  `${href}/` (so segment boundaries are honoured and `/dashboard/accounts`
 *  does NOT light up `/dashboard/account`). */
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
