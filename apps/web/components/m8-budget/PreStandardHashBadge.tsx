"use client";

/**
 * apps/web/components/m8-budget/PreStandardHashBadge.tsx — Story 8.3
 *
 * V8 determinism hash badge — displays first 8 characters + "전체 보기" tooltip
 * + copy-to-clipboard button.
 */

import { useTranslations } from "next-intl";
import { useState } from "react";

interface PreStandardHashBadgeProps {
  resultHash: string;
}

export function PreStandardHashBadge({
  resultHash,
}: PreStandardHashBadgeProps): React.ReactElement {
  const t = useTranslations("budget_pre_standard");
  const [copied, setCopied] = useState<boolean>(false);

  const displayHash = resultHash.slice(0, 12);
  const handleCopy = async (): Promise<void> => {
    try {
      await navigator.clipboard.writeText(resultHash);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard unavailable; silently ignore.
    }
  };

  return (
    <div
      className="mt-2 inline-flex items-center space-x-2 rounded bg-gray-100 px-2 py-1 text-xs"
      data-testid="pre-standard-hash-badge"
    >
      <span className="font-mono" title={resultHash}>
        {t("hash_badge_label")}: {displayHash}…
      </span>
      <button
        type="button"
        onClick={() => void handleCopy()}
        className="text-blue-600 hover:underline"
        data-testid="hash-copy-button"
      >
        {copied ? t("hash_copied") : t("hash_copy_button")}
      </button>
    </div>
  );
}
