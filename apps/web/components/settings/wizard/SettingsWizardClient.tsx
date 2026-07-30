/**
 * apps/web/components/settings/wizard/SettingsWizardClient.tsx
 *
 * Story 1.2 — Task 5.1 (Client Component body). Owns the completion-status
 * state shared by the 4 step components + the [계산] button (Task 6).
 *
 * Each step's `onSaved` callback patches the local `completion` state
 * from the server's response (`is_complete`, `missing`). The
 * `useSettingsCompletion` hook keeps the server-side view in sync via
 * background polling (30-second cadence).
 *
 * F-1: a function prop CANNOT be passed across the RSC boundary, so the
 * Server Component page hands a STRING (`accessToken`) here and this
 * Client Component constructs the handlers internally.
 *
 * F-7: this Client consumes the typed `fiscal_year_start_value`,
 * `currency_value`, `industry` fields on `CompletionStatus` — server-side
 * initial fetch supplies them so the wizard pickers are pre-seeded on
 * first render.
 *
 * F-20: receives `initialCompletion` (server-fetched) and seeds both the
 * `useState` and the hook from it — no race between user clicks and the
 * first poll.
 *
 * F-5: the previous "if status && completion" reconciliation branch was a
 * setState-during-render hot path; we now consume the polled status
 * directly via the hook so the seeded state never goes stale.
 */

"use client";

import { useCallback, useState } from "react";

import { useSettingsCompletion } from "@/hooks/useSettingsCompletion";
import type { CompletionStatus } from "@/lib/api-client";

import { AllocationCriteriaStep } from "./AllocationCriteriaStep";
import { CurrencyStep } from "./CurrencyStep";
import { FiscalYearStartStep } from "./FiscalYearStartStep";
import { LanguageStep } from "./LanguageStep";

export interface SettingsWizardClientProps {
  accessToken?: string;
  initialCompletion?: CompletionStatus | null;
}

export function SettingsWizardClient({
  accessToken,
  initialCompletion,
}: SettingsWizardClientProps) {
  // F-20: seed the hook from the server-fetched initial completion.
  // The hook's `status` is the source of truth — we keep a separate
  // local `completion` only so step components can mutate it synchronously
  // in their `onSaved` callbacks (optimistic update with `settings_version`
  // tracked server-side).
  const { status, refetch } = useSettingsCompletion(accessToken, initialCompletion);
  const [completion, setCompletion] = useState<CompletionStatus | null>(
    initialCompletion ?? null,
  );
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSaved = useCallback((next: CompletionStatus) => {
    setCompletion(next);
    setErrorMessage(null);
    refetch();
  }, [refetch]);

  const handleError = useCallback((msg: string) => {
    setErrorMessage(msg);
  }, []);

  return (
    <div>
      {errorMessage && (
        <div
          role="alert"
          style={{
            padding: "0.75rem 1rem",
            background: "#fee2e2",
            border: "1px solid #fca5a5",
            color: "#991b1b",
            borderRadius: 6,
            marginBottom: "1rem",
          }}
        >
          저장 실패: {errorMessage}
        </div>
      )}

      <FiscalYearStartStep
        initial={completion?.fiscal_year_start_value ?? null}
        completion={completion}
        accessToken={accessToken}
        onSaved={handleSaved}
        onError={handleError}
      />

      <CurrencyStep
        initial={completion?.currency_value ?? null}
        completion={completion}
        accessToken={accessToken}
        onSaved={handleSaved}
        onError={handleError}
      />

      <LanguageStep
        initial={completion?.language_completed ? "ko-KR" : null}
        completion={completion}
        accessToken={accessToken}
        onSaved={handleSaved}
        onError={handleError}
      />

      {/* AllocationCriteriaStep is read-only — it shows counts from the
          CompletionStatus the server already returned. Row CRUD happens in
          M1 baseline / M9 ABC pages (Epic 2 / Epic 9). F-6 removed the
          shortcut button so the wizard cannot flip completion itself. */}
      <AllocationCriteriaStep
        completion={completion}
        industry={completion?.industry ?? null}
      />

      {completion && (
        <aside
          aria-label="설정 완료 상태"
          style={{
            padding: "0.75rem 1rem",
            background: completion.is_complete ? "#dcfce7" : "#fef3c7",
            border: `1px solid ${completion.is_complete ? "#86efac" : "#fcd34d"}`,
            borderRadius: 6,
            marginTop: "1rem",
          }}
        >
          {completion.is_complete ? (
            <span style={{ color: "#15803d", fontWeight: 600 }}>
              ✓ 모든 설정이 완료되었습니다 — [계산] 버튼을 사용할 수 있습니다.
            </span>
          ) : (
            <span style={{ color: "#92400e" }}>
              ⚠ 미완료 항목: {completion.missing.join(", ")}
            </span>
          )}
        </aside>
      )}
    </div>
  );
}
