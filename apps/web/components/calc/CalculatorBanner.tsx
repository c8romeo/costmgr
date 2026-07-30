/**
 * apps/web/components/calc/CalculatorBanner.tsx
 *
 * Story 1.2 — Task 6.4. Yellow calculator banner shown at the top of
 * dashboard pages while `is_complete === false`. Hides itself when the
 * settings wizard is finished (so the user is not nagged).
 *
 * Placed in the dashboard home page and any page that opts in. The banner
 * uses the same `useSettingsCompletion` hook as CalcButton to stay in sync.
 *
 * UX-locked: ko-KR, WCAG AA, Professional 톤.
 *
 * Review patches applied:
 *   F-9 — denominator is `drivers_required ? 4 : 3` so the count matches
 *         the actual top-level field set the user has to complete
 *         (manufacturing skips drivers → 3 drivers).
 */

"use client";

import Link from "next/link";

import { useSettingsCompletion } from "@/hooks/useSettingsCompletion";

export interface CalculatorBannerProps {
  accessToken?: string;
}

export function CalculatorBanner({ accessToken }: CalculatorBannerProps) {
  const { status } = useSettingsCompletion(accessToken);

  // Hidden when complete, still loading, or no data yet.
  if (!status || status.is_complete) return null;

  const missing = status.missing;
  // F-9: industry-conditional denominator. CalcButton already uses this
  // exact expression (drivers_required ? 3 : 2) for the allocation sub-
  // grid, so the banner reads consistently: 4 total fields if drivers are
  // required, 3 if not (manufacturing).
  const denominator = status.drivers_required ? 4 : 3;
  return (
    <div
      role="status"
      aria-live="polite"
      style={{
        padding: "0.75rem 1rem",
        background: "#fef3c7",
        border: "1px solid #fcd34d",
        color: "#92400e",
        borderRadius: 6,
        marginBottom: "1rem",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 12,
      }}
    >
      <span>
        ⚠️ 계산 버튼을 사용하려면 설정 마법사를 완료하세요:{" "}
        <strong>
          필수 항목 {denominator - missing.length}/{denominator}
        </strong>
        {missing.length > 0 && (
          <span style={{ marginLeft: 8, fontSize: "0.85rem" }}>
            (미완료: {missing.join(", ")})
          </span>
        )}
      </span>
      <Link
        href="/dashboard/settings/wizard"
        style={{
          padding: "0.4rem 0.75rem",
          background: "#92400e",
          color: "#fef3c7",
          borderRadius: 4,
          textDecoration: "none",
          fontWeight: 600,
          fontSize: "0.85rem",
          whiteSpace: "nowrap",
        }}
      >
        설정 마법사 열기 →
      </Link>
    </div>
  );
}