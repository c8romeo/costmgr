"use client";

/**
 * apps/web/components/m9-abc/AbcValidationStatus.tsx — Story 9.1
 *
 * Status display for a single-layer ABC 100% validation result.
 *
 * Per AC #4 (Story 9.1):
 *  - Shows sum_pct, count, is_valid, hash, message_ko.
 *  - Korean SSOT message shown when is_valid=False.
 *  - V8 determinism hash (sha256:64-hex) displayed as a badge.
 *
 * Parent: <AbcValidationPanel>.
 */

import { useTranslations } from "next-intl";

import { isValidV8Hash } from "@/lib/m9-abc-validation";
import type { ValidationLayerWire } from "@/lib/m9-abc-validation";

interface AbcValidationStatusProps {
  layer: ValidationLayerWire;
}

export function AbcValidationStatus({
  layer,
}: AbcValidationStatusProps): React.ReactElement {
  const t = useTranslations("abc_validation");

  const targetLabelKey = `target_label_${layer.target}` as const;
  const targetLabel = t(targetLabelKey);

  return (
    <div
      className={
        layer.is_valid
          ? "rounded border border-green-300 bg-green-50 p-3"
          : "rounded border border-red-300 bg-red-50 p-3"
      }
      data-testid={`abc-validation-status-${layer.target}`}
      data-valid={layer.is_valid ? "true" : "false"}
    >
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">{targetLabel}</h3>
        <span
          className={
            layer.is_valid
              ? "rounded bg-green-200 px-2 py-0.5 text-xs font-medium text-green-800"
              : "rounded bg-red-200 px-2 py-0.5 text-xs font-medium text-red-800"
          }
        >
          {layer.is_valid ? t("status_valid") : t("status_invalid")}
        </span>
      </div>

      <dl className="mt-2 grid grid-cols-2 gap-x-3 gap-y-1 text-sm">
        <dt className="text-gray-600">{t("field_sum_pct")}</dt>
        <dd className="font-mono">{layer.sum_pct}%</dd>
        <dt className="text-gray-600">{t("field_count")}</dt>
        <dd>{layer.count}</dd>
        <dt className="text-gray-600">{t("field_hash")}</dt>
        <dd className="break-all font-mono text-xs">
          {isValidV8Hash(layer.hash)
            ? `${layer.hash.slice(0, 16)}…`
            : layer.hash}
        </dd>
      </dl>

      {layer.message_ko !== null ? (
        <p
          className="mt-2 text-sm text-red-700"
          data-testid={`abc-validation-message-${layer.target}`}
        >
          {layer.message_ko}
        </p>
      ) : null}
    </div>
  );
}