/**
 * apps/web/components/calc/CalcButton.tsx
 *
 * Story 1.2 — Task 6.1. The [계산] primary action button.
 *
 * Behaviour (refactored to address Chunk-A code review findings):
 *   - Reads completion status via `useSettingsCompletion()`.
 *   - Disabled (gray, `aria-disabled="true"`) until `status.is_complete === true`.
 *     The button is **focusable** (F-15) — `aria-disabled` instead of HTML
 *     `disabled` so keyboard users see the tooltip.
 *   - Hover/focus/touch tooltip (F-1 + F-19):
 *     · complete → "원가 계산 실행"
 *     · top-level fields missing → "<fields>을(를) 모두 완료해 주세요 (N/4 완료)"
 *     · allocation criteria incomplete → "배부기준 3종을 모두 완료해 주세요
 *       (N/3 완료): <criterion>(<count>행), …"
 *   - Per-field deep links (F-2): each missing item links to the wizard
 *     with the right tab/anchor pre-selected.
 *   - Locale-aware click destination (F-3): `/[locale]/m3-calculate/period`.
 *   - Touch tap toggles the tooltip (F-19) so onClick handler is wired.
 *   - The tooltip itself is a sibling of the disabled control (F-23) so no
 *     interactive `<Link>` is nested inside `role="tooltip"`.
 *
 * UX-locked:
 *   - WCAG AA contrast (gray on disabled, blue on enabled).
 *   - "Professional 톤" — primary action shape, not playful.
 *   - ko-KR copy.
 */

"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useId, useState } from "react";

import { useSettingsCompletion } from "@/hooks/useSettingsCompletion";
import type { CompletionStatus } from "@/lib/api-client";

export interface CalcButtonProps {
  accessToken?: string;
}

// ── Tooltip text generator (F-1) ──────────────────────────────
interface MissingLink {
  label: string;
  href: string;
}

interface TooltipShape {
  main: string;
  missingLinks: MissingLink[];
}

function buildTooltip(status: CompletionStatus): TooltipShape {
  if (status.is_complete) {
    return { main: "원가 계산 실행", missingLinks: [] };
  }

  const topMissing: string[] = [];
  if (!status.fiscal_year_start_completed) topMissing.push("회계연도 시작월");
  if (!status.currency_completed) topMissing.push("통화");
  if (!status.language_completed) topMissing.push("언어");

  if (topMissing.length > 0) {
    const completedCount =
      (status.fiscal_year_start_completed ? 1 : 0) +
      (status.currency_completed ? 1 : 0) +
      (status.language_completed ? 1 : 0) +
      (status.allocation_criteria_completed ? 1 : 0);
    return {
      main: `${topMissing.join("/")}을(를) 모두 완료해 주세요 (${completedCount}/4 완료)`,
      missingLinks: [
        { label: "설정 마법사로 이동 →", href: "/settings/wizard" },
      ],
    };
  }

  // Allocation criteria incomplete.
  const allocMissing: string[] = [];
  if (status.direct_indirect_count === 0)
    allocMissing.push("직접/간접 계정 분류 (0행)");
  if (status.fixed_variable_count === 0)
    allocMissing.push("고정/변동 분류 (0행)");
  if (status.drivers_required && status.drivers_count === 0)
    allocMissing.push("동인 정의 (0행)");

  const denominator = status.drivers_required ? 3 : 2;
  const doneInAllocator =
    (status.direct_indirect_count > 0 ? 1 : 0) +
    (status.fixed_variable_count > 0 ? 1 : 0) +
    (status.drivers_required && status.drivers_count > 0 ? 1 : 0);

  const tabLinks: MissingLink[] = [];
  if (status.direct_indirect_count === 0)
    tabLinks.push({
      label: "직접/간접 계정 분류 →",
      href: "/settings/wizard?tab=direct_indirect",
    });
  if (status.fixed_variable_count === 0)
    tabLinks.push({
      label: "고정/변동 분류 →",
      href: "/settings/wizard?tab=fixed_variable",
    });
  if (status.drivers_required && status.drivers_count === 0)
    tabLinks.push({
      label: "동인 정의 →",
      href: "/settings/wizard?tab=drivers",
    });

  return {
    main: `배부기준 3종을 모두 완료해 주세요 (${doneInAllocator}/${denominator} 완료): ${allocMissing.join(", ")}`,
    missingLinks:
      tabLinks.length > 0
        ? tabLinks
        : [{ label: "설정 마법사로 이동 →", href: "/settings/wizard" }],
  };
}

export function CalcButton({ accessToken }: CalcButtonProps) {
  const { status, isLoading } = useSettingsCompletion(accessToken);
  const tooltipId = useId();
  const [showTooltip, setShowTooltip] = useState(false);
  const params = useParams<{ locale?: string }>();
  const locale = params?.locale ?? "ko-KR";

  // F-15: button is focusable regardless of disabled state — `aria-disabled`
  // conveys the state to AT, but the element stays in tab order so the
  // tooltip is reachable via keyboard.
  // F-27: `isLoading` is intentionally NOT consulted here — `useSettingsCompletion`
  // sets isLoading=true only on the FIRST fetch, before any data exists.
  // After that, background refetches leave isLoading alone, so the button
  // does not flicker disabled during polling.
  const isComplete = status?.is_complete ?? false;
  const ariaDisabled = !isComplete;
  const tooltip = status ? buildTooltip(status) : null;
  const calcHref = `/${locale}/m3-calculate/period`;

  function handleClick(e: React.MouseEvent | React.TouchEvent) {
    if (ariaDisabled) {
      e.preventDefault();
      setShowTooltip((v) => !v); // F-19: touch toggle.
      return;
    }
    // enabled: navigation happens via <Link> for the enabled branch.
  }

  return (
    <div
      style={{ position: "relative", display: "inline-block", width: "100%" }}
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
      onFocus={() => setShowTooltip(true)}
      onBlur={() => setShowTooltip(false)}
    >
      {isComplete ? (
        // F-29: enabled <Link> — no `aria-disabled` (default false).
        <Link
          href={calcHref}
          aria-describedby={tooltipId}
          style={{
            display: "block",
            width: "100%",
            padding: "0.6rem 1rem",
            background: "#2563eb",
            color: "#fff",
            border: "none",
            borderRadius: 6,
            textDecoration: "none",
            textAlign: "center",
            fontWeight: 700,
            fontSize: "0.95rem",
          }}
        >
          [계산]
        </Link>
      ) : (
        <button
          type="button"
          aria-disabled={ariaDisabled}
          aria-describedby={tooltipId}
          onClick={handleClick}
          // F-15: focusable even when disabled; no `disabled` attribute.
          style={{
            display: "block",
            width: "100%",
            padding: "0.6rem 1rem",
            background: "#94a3b8",
            color: "#fff",
            border: "none",
            borderRadius: 6,
            cursor: "not-allowed",
            fontWeight: 700,
            fontSize: "0.95rem",
          }}
        >
          [계산]
        </button>
      )}

      {tooltip && (
        // F-23: tooltip is a SIBLING of the button — its content is rendered
        // as plain text + per-field links below it as siblings, NOT inside
        // the role="tooltip" element. This avoids the ARIA violation of
        // nesting interactive elements.
        <span
          id={tooltipId}
          role="tooltip"
          style={{
            position: "absolute",
            left: 0,
            top: "calc(100% + 6px)",
            minWidth: 240,
            maxWidth: 320,
            padding: "0.5rem 0.75rem",
            background: "#0f172a",
            color: "#f8fafc",
            borderRadius: 6,
            fontSize: "0.85rem",
            lineHeight: 1.4,
            zIndex: 50,
            visibility: showTooltip ? "visible" : "hidden",
            opacity: showTooltip ? 1 : 0,
            transition: "opacity 120ms ease-in",
          }}
        >
          {tooltip.main}
        </span>
      )}

      {/* F-23 + F-2: per-field Links live as SIBLINGS (not nested in
          role="tooltip") — they're positioned absolutely so the visual
          chrome looks the same as before but the ARIA semantics are correct. */}
      {tooltip && showTooltip && tooltip.missingLinks.length > 0 && (
        <div
          style={{
            position: "absolute",
            left: 0,
            top: "calc(100% + 6px + 2.6rem)",
            minWidth: 240,
            maxWidth: 320,
            display: "flex",
            flexDirection: "column",
            gap: 4,
            padding: "0.4rem 0.5rem",
            background: "#1e293b",
            color: "#f8fafc",
            borderRadius: 6,
            fontSize: "0.8rem",
            zIndex: 51,
          }}
        >
          {tooltip.missingLinks.map((link) => (
            <Link
              key={link.href}
              href={`/${locale}${link.href}`}
              style={{ color: "#93c5fd", textDecoration: "underline" }}
            >
              {link.label}
            </Link>
          ))}
        </div>
      )}

      {/* Loading skeleton placeholder — only on first mount. */}
      {isLoading && (
        <span
          aria-hidden="true"
          style={{
            position: "absolute",
            inset: 0,
            background: "rgba(255,255,255,0.5)",
            borderRadius: 6,
          }}
        />
      )}
    </div>
  );
}
