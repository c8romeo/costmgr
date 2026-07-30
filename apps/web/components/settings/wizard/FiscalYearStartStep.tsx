/**
 * apps/web/components/settings/wizard/FiscalYearStartStep.tsx
 *
 * Story 1.2 — Task 5.2. AC #1: 회계연도 시작월 저장.
 * Month picker (12 buttons in 3×4 grid) + Year picker (current + previous).
 * On save: POST /api/v1/tenant-settings/onboarding/fiscal-year-start.
 *
 * PRD §3.A1 — 회계연도 axiom (period keys derive from YYYY-MM).
 * AD-24 — typed period-key namespaces.
 * UX-locked: ko-KR labels, WCAG AA contrast (dark text on light bg).
 *
 * Review patches applied:
 *   F-8 — month grid uses roving tabindex + Arrow/Home/End handlers
 *         (WCAG-compliant keyboard nav without adding shadcn/Radix deps).
 *   F-12 — `inFlightRef` guards against double-click firing two POSTs.
 *   F-16 — server-truth merge: local `completion` is overwritten with
 *         server-returned `is_complete` + `missing` after save.
 *   F-17 — `isLocked` checks `completion.fiscal_year_start_completed`
 *         only (post-F-7 the value field is reliable, so the parsed
 *         comparison is no longer needed to avoid false positives).
 */

"use client";

import { useCallback, useRef, useState } from "react";

import { ApiError, saveFiscalYearStart } from "@/lib/api-client";
import type { CompletionStatus } from "@/lib/api-client";

const MONTH_LABEL_KO = [
  "1월",
  "2월",
  "3월",
  "4월",
  "5월",
  "6월",
  "7월",
  "8월",
  "9월",
  "10월",
  "11월",
  "12월",
];

export interface FiscalYearStartStepProps {
  initial?: string | null;
  completion: CompletionStatus | null;
  accessToken?: string;
  onSaved: (next: CompletionStatus) => void;
  onError: (msg: string) => void;
}

function parseStored(value: string | null | undefined): {
  year: number;
  month: number;
} | null {
  if (!value) return null;
  const match = /^(\d{4})-(0[1-9]|1[0-2])$/.exec(value);
  if (!match) return null;
  return { year: Number(match[1]), month: Number(match[2]) };
}

function formatStored(year: number, month: number): string {
  return `${year}-${String(month).padStart(2, "0")}`;
}

export function FiscalYearStartStep({
  initial,
  completion,
  accessToken,
  onSaved,
  onError,
}: FiscalYearStartStepProps) {
  const parsed = parseStored(initial);
  const [year, setYear] = useState<number>(parsed?.year ?? new Date().getFullYear());
  const [month, setMonth] = useState<number>(parsed?.month ?? 1);
  const [isSaving, setIsSaving] = useState(false);
  // F-12: `inFlightRef` prevents a double-click from firing two POSTs.
  // `disabled` only takes effect AFTER React commits `isSaving=true`,
  // so the guard must be synchronous.
  const inFlightRef = useRef<boolean>(false);
  // F-17: `is_initial` is determined solely by the completion flag — once
  // F-7 supplies `fiscal_year_start_value`, the parsed-comparison gate
  // becomes redundant (would only block re-saves with the same value).
  const isLocked = completion?.fiscal_year_start_completed === true;

  // F-8: roving tabindex for the 12-month grid (radigroup semantics).
  const [activeMonthIndex, setActiveMonthIndex] = useState<number>(
    (parsed?.month ?? 1) - 1,
  );

  const onMonthKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLButtonElement>) => {
      if (e.key === "ArrowRight" || e.key === "ArrowDown") {
        e.preventDefault();
        setActiveMonthIndex((i) => (i + 1) % 12);
      } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        e.preventDefault();
        setActiveMonthIndex((i) => (i - 1 + 12) % 12);
      } else if (e.key === "Home") {
        e.preventDefault();
        setActiveMonthIndex(0);
      } else if (e.key === "End") {
        e.preventDefault();
        setActiveMonthIndex(11);
      } else if (e.key === " " || e.key === "Enter") {
        e.preventDefault();
        setMonth(activeMonthIndex + 1);
      }
    },
    [activeMonthIndex],
  );

  async function handleSave() {
    if (inFlightRef.current) return; // F-12: double-click guard.
    inFlightRef.current = true;
    setIsSaving(true);
    try {
      const res = await saveFiscalYearStart(formatStored(year, month), accessToken);
      // F-16: server-truth merge.
      onSaved({
        ...(completion as CompletionStatus),
        fiscal_year_start_completed: true,
        is_complete: res.is_complete,
        missing: res.missing,
      });
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : String(e);
      onError(msg);
    } finally {
      inFlightRef.current = false;
      setIsSaving(false);
    }
  }

  return (
    <section
      aria-labelledby="wizard-fiscal-year-heading"
      style={{
        padding: "1.25rem 1.5rem",
        border: "1px solid #e2e8f0",
        borderRadius: 8,
        background: "#fff",
        marginBottom: "1rem",
      }}
    >
      <h2
        id="wizard-fiscal-year-heading"
        style={{ fontSize: "1.125rem", fontWeight: 700, marginBottom: "0.25rem" }}
      >
        회계연도 시작월
      </h2>
      <p style={{ color: "#475569", fontSize: "0.9rem", marginBottom: "0.75rem" }}>
        회계연도가 시작되는 달을 선택하세요. (PRD §3.A1 · 12월 결산이 기본값)
      </p>

      <div role="group" aria-label="연도 선택" style={{ marginBottom: "0.75rem" }}>
        <label
          htmlFor="wizard-year"
          style={{ display: "inline-block", marginRight: 8, fontWeight: 600 }}
        >
          연도
        </label>
        <select
          id="wizard-year"
          value={year}
          onChange={(e) => setYear(Number(e.target.value))}
          style={{
            padding: "0.25rem 0.5rem",
            border: "1px solid #cbd5e1",
            borderRadius: 4,
          }}
        >
          {[year - 1, year, year + 1].map((y) => (
            <option key={y} value={y}>
              {y}년
            </option>
          ))}
        </select>
      </div>

      <div
        role="radiogroup"
        aria-label="월 선택"
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, 1fr)",
          gap: 8,
          marginBottom: "1rem",
        }}
      >
        {MONTH_LABEL_KO.map((label, idx) => {
          const m = idx + 1;
          const selected = m === month;
          const isActive = idx === activeMonthIndex;
          return (
            <button
              key={m}
              ref={(el) => {
                if (isActive && el) el.focus();
              }}
              type="button"
              role="radio"
              aria-checked={selected}
              tabIndex={isActive ? 0 : -1}
              onClick={() => {
                setMonth(m);
                setActiveMonthIndex(idx);
              }}
              onKeyDown={onMonthKeyDown}
              onFocus={() => setActiveMonthIndex(idx)}
              style={{
                padding: "0.5rem 0",
                border: selected ? "2px solid #2563eb" : "1px solid #cbd5e1",
                background: selected ? "#dbeafe" : "#fff",
                borderRadius: 6,
                cursor: "pointer",
                fontWeight: selected ? 700 : 500,
              }}
            >
              {label}
            </button>
          );
        })}
      </div>

      <button
        type="button"
        onClick={handleSave}
        disabled={isSaving || isLocked}
        aria-busy={isSaving}
        style={{
          padding: "0.5rem 1rem",
          background: isSaving || isLocked ? "#94a3b8" : "#2563eb",
          color: "#fff",
          border: "none",
          borderRadius: 6,
          cursor: isSaving || isLocked ? "not-allowed" : "pointer",
          fontWeight: 600,
        }}
      >
        {isSaving ? "저장 중…" : isLocked ? "저장됨" : "저장"}
      </button>
    </section>
  );
}
