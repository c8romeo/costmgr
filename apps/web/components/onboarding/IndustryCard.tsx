/**
 * apps/web/components/onboarding/IndustryCard.tsx — single 4지선다 card.
 *
 * Story 1.1 — Task 3.3. UX-locked: Professional 톤 + ko-KR. Selected
 * state shows a blue border + checkmark icon (per ux-locked-decisions).
 *
 * Story 0.5 T8 — renders INDUSTRY_ICON (lucide-react component) above the
 * label. Closes Story 1.1 F-33 deferral.
 */

"use client";

import { Boxes, Briefcase, Factory, Layers, type LucideIcon } from "lucide-react";

import type { Industry } from "@/lib/menu-config";
import {
  INDUSTRY_DESCRIPTION_KO,
  INDUSTRY_ICON,
  INDUSTRY_LABEL_KO,
} from "@/lib/menu-config";

const ICON_MAP: Record<string, LucideIcon> = {
  Factory,
  Briefcase,
  Layers,
  Boxes,
};

export interface IndustryCardProps {
  industry: Industry;
  selected: boolean;
  disabled?: boolean;
  onClick: (industry: Industry) => void;
}

export function IndustryCard({
  industry,
  selected,
  disabled = false,
  onClick,
}: IndustryCardProps) {
  const Icon = ICON_MAP[INDUSTRY_ICON[industry]] ?? Factory;

  return (
    <button
      type="button"
      aria-pressed={selected}
      disabled={disabled}
      onClick={() => onClick(industry)}
      style={{
        textAlign: "left",
        padding: "1.25rem",
        borderRadius: 12,
        border: selected ? "2px solid #2563eb" : "1px solid #e5e7eb",
        background: selected ? "#eff6ff" : "white",
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.6 : 1,
        transition: "all 120ms ease",
        boxShadow: selected
          ? "0 1px 3px rgba(37, 99, 235, 0.18)"
          : "0 1px 2px rgba(0, 0, 0, 0.04)",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          gap: "0.75rem",
        }}
      >
        <Icon
          aria-hidden="true"
          size={28}
          strokeWidth={1.5}
          color={selected ? "#2563eb" : "#475569"}
        />
        <div style={{ flex: 1 }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "flex-start",
              gap: "0.5rem",
            }}
          >
            <h3
              style={{
                fontSize: "1.05rem",
                fontWeight: 600,
                margin: 0,
                color: "#0f172a",
              }}
            >
              {INDUSTRY_LABEL_KO[industry]}
            </h3>
            {selected && (
              <span
                aria-label="선택됨"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: 24,
                  height: 24,
                  borderRadius: "50%",
                  background: "#2563eb",
                  color: "white",
                  fontSize: 14,
                  fontWeight: 700,
                }}
              >
                ✓
              </span>
            )}
          </div>
          <p
            style={{
              marginTop: "0.5rem",
              fontSize: "0.875rem",
              color: "#475569",
              lineHeight: 1.5,
            }}
          >
            {INDUSTRY_DESCRIPTION_KO[industry]}
          </p>
        </div>
      </div>
    </button>
  );
}
