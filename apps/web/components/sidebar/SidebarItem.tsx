/**
 * apps/web/components/sidebar/SidebarItem.tsx — single sidebar entry.
 *
 * Story 1.1 — Task 4.2. Active state: bold + left blue accent bar.
 * Tooltip (Task 4.3) is rendered via the native `title` attribute for
 * now (no JS popover dependency — Story 0.5 introduces the design
 * system's tooltip component).
 */

"use client";

export interface SidebarItemProps {
  label: string;
  active: boolean;
  tooltip?: string;
}

export function SidebarItem({ label, active, tooltip }: SidebarItemProps) {
  return (
    <div
      title={tooltip}
      style={{
        position: "relative",
        padding: "0.5rem 0.75rem 0.5rem 0.875rem",
        borderLeft: active ? "3px solid #2563eb" : "3px solid transparent",
        background: active ? "#eff6ff" : "transparent",
        color: active ? "#0f172a" : "#334155",
        fontWeight: active ? 600 : 400,
        fontSize: "0.9rem",
        borderRadius: 4,
        cursor: "pointer",
        transition: "background 80ms ease",
      }}
    >
      {label}
    </div>
  );
}
