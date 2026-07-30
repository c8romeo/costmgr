/**
 * apps/web/components/settings/wizard/CurrencyStep.tsx
 *
 * Story 1.2 — Task 5.3. AC #1: 통화 저장.
 * Two radio cards: KRW (₩) default · USD ($).
 * On save: POST /api/v1/tenant-settings/onboarding/currency.
 *
 * PRD §3.A6 — 1원 단위 검증 (KRW=BIGINT, USD=NUMERIC(18,2)).
 * UX-locked: Professional 톤, WCAG AA contrast.
 *
 * Review patches applied:
 *   F-8 — currency cards use native `<input type="radio">` (built-in
 *         arrow nav + form semantics). Visually hidden inputs; styled
 *         `<label>` carries the visual cards.
 *   F-12 — `inFlightRef` guards double-click.
 *   F-16 — server-truth merge.
 *   F-17 — `isLocked` based on `completion.currency_completed` only
 *         (post-F-7 the stored value is reliable).
 */

"use client";

import { useRef, useState } from "react";

import { ApiError, saveCurrency } from "@/lib/api-client";
import type { CompletionStatus } from "@/lib/api-client";

export interface CurrencyStepProps {
  initial?: "KRW" | "USD" | null;
  completion: CompletionStatus | null;
  accessToken?: string;
  onSaved: (next: CompletionStatus) => void;
  onError: (msg: string) => void;
}

const OPTIONS: Array<{ value: "KRW" | "USD"; label: string; symbol: string; hint: string }> = [
  { value: "KRW", label: "원 (KRW)", symbol: "₩", hint: "한국 원 — 정수(1원 단위)로 저장" },
  { value: "USD", label: "달러 (USD)", symbol: "$", hint: "미 달러 — 소수점 둘째 자리까지" },
];

export function CurrencyStep({
  initial,
  completion,
  accessToken,
  onSaved,
  onError,
}: CurrencyStepProps) {
  const [currency, setCurrency] = useState<"KRW" | "USD">(initial ?? "KRW");
  const [isSaving, setIsSaving] = useState(false);
  const inFlightRef = useRef<boolean>(false); // F-12
  const isLocked = completion?.currency_completed === true; // F-17

  async function handleSave() {
    if (inFlightRef.current) return; // F-12
    inFlightRef.current = true;
    setIsSaving(true);
    try {
      const res = await saveCurrency(currency, accessToken);
      // F-16: server-truth.
      onSaved({
        ...(completion as CompletionStatus),
        currency_completed: true,
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
      aria-labelledby="wizard-currency-heading"
      style={{
        padding: "1.25rem 1.5rem",
        border: "1px solid #e2e8f0",
        borderRadius: 8,
        background: "#fff",
        marginBottom: "1rem",
      }}
    >
      <h2
        id="wizard-currency-heading"
        style={{ fontSize: "1.125rem", fontWeight: 700, marginBottom: "0.25rem" }}
      >
        통화
      </h2>
      <p style={{ color: "#475569", fontSize: "0.9rem", marginBottom: "0.75rem" }}>
        사용할 통화를 선택하세요. (PRD §3.A6 — 1원 단위 검증)
      </p>

      {/* F-8: native radio inputs (browser-handles arrow nav between radios
          sharing a `name`). Visually-hidden inputs; `<label>` carries the
          card chrome and is keyboard-focusable. */}
      <fieldset
        style={{
          border: "none",
          padding: 0,
          margin: "0 0 1rem 0",
          display: "grid",
          gridTemplateColumns: "repeat(2, 1fr)",
          gap: 12,
        }}
      >
        <legend className="sr-only" style={{ position: "absolute", left: -10000 }}>
          통화 선택
        </legend>
        {OPTIONS.map((opt) => {
          const selected = opt.value === currency;
          return (
            <label
              key={opt.value}
              htmlFor={`wizard-currency-${opt.value}`}
              style={{
                display: "block",
                padding: "1rem",
                border: selected ? "2px solid #2563eb" : "1px solid #cbd5e1",
                background: selected ? "#dbeafe" : "#fff",
                borderRadius: 8,
                cursor: "pointer",
              }}
            >
              <input
                id={`wizard-currency-${opt.value}`}
                type="radio"
                name="wizard-currency"
                value={opt.value}
                checked={selected}
                onChange={() => setCurrency(opt.value)}
                style={{ position: "absolute", opacity: 0, pointerEvents: "none" }}
              />
              <div style={{ fontSize: "1.5rem", marginBottom: 4 }}>{opt.symbol}</div>
              <div style={{ fontWeight: 700, marginBottom: 4 }}>{opt.label}</div>
              <div style={{ color: "#475569", fontSize: "0.85rem" }}>{opt.hint}</div>
            </label>
          );
        })}
      </fieldset>

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
