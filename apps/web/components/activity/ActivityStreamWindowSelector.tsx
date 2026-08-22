"use client";

/**
 * apps/web/components/activity/ActivityStreamWindowSelector.tsx — Epic 17 T3 (AC #3.4)
 *
 * Window selector for the activity stream timeline.
 *
 * 4 options: 1일 / 7일 / 30일 / 90일. Default 7일.
 *
 * Controlled component — the parent (ActivityStreamPanel) owns the
 * window state and refetches on change.
 */

import { useTranslations } from "next-intl";

interface ActivityStreamWindowSelectorProps {
  value: 1 | 7 | 30 | 90;
  onChange: (next: 1 | 7 | 30 | 90) => void;
}

export function ActivityStreamWindowSelector({
  value,
  onChange,
}: ActivityStreamWindowSelectorProps): React.ReactElement {
  const t = useTranslations("activity");
  const options: ReadonlyArray<{ days: 1 | 7 | 30 | 90; labelKey: string }> = [
    { days: 1, labelKey: "window_day_1" },
    { days: 7, labelKey: "window_day_7" },
    { days: 30, labelKey: "window_day_30" },
    { days: 90, labelKey: "window_day_90" },
  ];
  return (
    <fieldset
      data-testid="activity-stream-window-selector"
      style={{
        display: "flex",
        gap: "0.5rem",
        alignItems: "center",
        border: "1px solid var(--border)",
        borderRadius: 8,
        padding: "0.5rem 1rem",
        marginBottom: "1rem",
      }}
    >
      <legend style={{ fontSize: "0.85rem" }}>
        {t("window_selector_label")}
      </legend>
      {options.map((opt) => (
        <button
          key={opt.days}
          type="button"
          data-testid={`activity-window-${opt.days}`}
          aria-pressed={value === opt.days}
          onClick={() => onChange(opt.days)}
          style={{
            background: value === opt.days ? "var(--accent)" : "transparent",
            color: value === opt.days ? "var(--accent-fg)" : "inherit",
            padding: "0.25rem 0.75rem",
            borderRadius: 4,
            border: "1px solid var(--border)",
            cursor: "pointer",
          }}
        >
          {t(opt.labelKey)}
        </button>
      ))}
    </fieldset>
  );
}
