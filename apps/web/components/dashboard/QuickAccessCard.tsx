/**
 * apps/web/components/dashboard/QuickAccessCard.tsx — 빠른 진입 카드 (3개: M1/M2/M3).
 *
 * cj-style N+19 (2026-09-15 KST, D-Day+1, Dashboard 보강 A=KPI+빠른진입).
 * 결정 wire 보존: sidebar 와 중복이지만 dashboard 에서 1-click 진입 강조.
 * UX-locked: WCAG AA contrast, 좌측 4px blue accent bar (PRD §F design parity
 * with active sidebar item), 호버 시 배경 #f8fafc tint.
 */

import Link from "next/link";
import type { CSSProperties } from "react";

export interface QuickAccessCardProps {
  href: string;
  title: string;
  description: string;
}

const CARD_STYLE: CSSProperties = {
  display: "block",
  padding: "16px 18px 16px 22px",
  background: "#ffffff",
  border: "1px solid #e2e8f0",
  borderRadius: 8,
  textDecoration: "none",
  color: "inherit",
  position: "relative",
  boxShadow: "0 1px 2px rgba(15, 23, 42, 0.04)",
  transition: "background 120ms ease",
};

const ACCENT: CSSProperties = {
  position: "absolute",
  left: 0,
  top: 12,
  bottom: 12,
  width: 4,
  background: "#1d4ed8",
  borderRadius: 2,
};

export function QuickAccessCard({ href, title, description }: QuickAccessCardProps) {
  return (
    <Link href={href} style={CARD_STYLE} className="quick-access-card">
      <span style={ACCENT} aria-hidden="true" />
      <div style={{ fontSize: "1rem", fontWeight: 600, color: "#0f172a", marginBottom: 4 }}>
        {title}
      </div>
      <div style={{ fontSize: "0.8rem", color: "#475569", lineHeight: 1.4 }}>
        {description}
      </div>
    </Link>
  );
}
