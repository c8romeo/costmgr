/**
 * apps/web/components/settings/wizard/LanguageStep.tsx
 *
 * Story 1.2 — Task 5.4. AC #1: 언어 저장.
 * MVP language lock (NFR-18) — ko-KR only. The step renders a read-only
 * confirmation card; the POST still fires so the wizard's `language_completed`
 * flag flips and the [계산] tooltip recognises the field as done.
 *
 * UX-locked (Story ux-locked-decisions §4): ko-KR only in MVP.
 *
 * Review patches applied:
 *   F-12 — `inFlightRef` guards double-click.
 *   F-16 — server-truth merge.
 *   F-17 — `isLocked` based on `completion.language_completed` only.
 */

"use client";

import { useRef, useState } from "react";

import { ApiError, saveLanguage } from "@/lib/api-client";
import type { CompletionStatus } from "@/lib/api-client";

export interface LanguageStepProps {
  initial?: string | null;
  completion: CompletionStatus | null;
  accessToken?: string;
  onSaved: (next: CompletionStatus) => void;
  onError: (msg: string) => void;
}

export function LanguageStep({
  initial,
  completion,
  accessToken,
  onSaved,
  onError,
}: LanguageStepProps) {
  const [isSaving, setIsSaving] = useState(false);
  const inFlightRef = useRef<boolean>(false); // F-12
  // F-17: completed flag is sufficient (post-F-7 initial is reliable).
  const isLocked = completion?.language_completed === true;

  async function handleSave() {
    if (inFlightRef.current) return; // F-12
    inFlightRef.current = true;
    setIsSaving(true);
    try {
      const res = await saveLanguage("ko-KR", accessToken);
      // F-16: server-truth.
      onSaved({
        ...(completion as CompletionStatus),
        language_completed: true,
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
      aria-labelledby="wizard-language-heading"
      style={{
        padding: "1.25rem 1.5rem",
        border: "1px solid #e2e8f0",
        borderRadius: 8,
        background: "#fff",
        marginBottom: "1rem",
      }}
    >
      <h2
        id="wizard-language-heading"
        style={{ fontSize: "1.125rem", fontWeight: 700, marginBottom: "0.25rem" }}
      >
        언어
      </h2>
      <p style={{ color: "#475569", fontSize: "0.9rem", marginBottom: "0.75rem" }}>
        MVP는 한국어만 지원합니다. (NFR-18 · Story ux-locked-decisions §4)
      </p>

      <div
        role="group"
        aria-label="언어 (MVP: 한국어 고정)"
        style={{
          padding: "1rem",
          border: "1px solid #cbd5e1",
          borderRadius: 8,
          background: "#f1f5f9",
          marginBottom: "1rem",
        }}
      >
        <div style={{ fontWeight: 700, marginBottom: 4 }}>한국어 (ko-KR)</div>
        <div style={{ color: "#475569", fontSize: "0.85rem" }}>
          선택됨 — MVP 단계에서는 변경할 수 없습니다
        </div>
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
        {isSaving ? "저장 중…" : isLocked ? "저장됨" : "확인"}
      </button>
    </section>
  );
}
