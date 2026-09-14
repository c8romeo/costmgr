/**
 * apps/web/app/[locale]/(dashboard)/monthly-input/ai-extract/AiExtractPageClient.tsx —
 * cj-style N+15 (D-Day MVP demo, 2026-09-14 KST).
 *
 * Thin client wrapper for the AI Extract RSC mount page. The RSC page
 * cannot pass `onClose` (an event handler function) to the
 * `<AiExtractModal>` Client Component, so we move the close handler
 * into a Client Component that bridges RSC props (accessToken +
 * defaultPeriodKey) → serializable client props.
 *
 * AD-7 verbatim preserved: this page is DISPLAY ONLY on
 * monthly_input_rows. Promote-to-confirmed flow remains in /ai/promote.
 */

"use client";

import { useRouter } from "next/navigation";

import { AiExtractModal } from "@/components/m10-ai";

interface AiExtractPageClientProps {
  accessToken?: string;
  defaultPeriodKey: string;
}

export function AiExtractPageClient({
  accessToken,
  defaultPeriodKey,
}: AiExtractPageClientProps): React.ReactElement {
  const router = useRouter();

  const handleClose = (): void => {
    // RSC entry point — closing returns to the monthly-input shell
    // (history.back fallback, then router.push as the canonical path).
    if (typeof window !== "undefined" && window.history.length > 1) {
      window.history.back();
    } else {
      router.push("/monthly-input");
    }
  };

  return (
    <AiExtractModal
      accessToken={accessToken}
      isOpen={true}
      onClose={handleClose}
      defaultPeriodKey={defaultPeriodKey}
    />
  );
}
