"use client";

/**
 * apps/web/components/m12-account/DeletionConsentCheckbox.tsx — Story 12.3
 *
 * Client Component for the Korean consent template acknowledgement
 * checkbox (owner-only, destructive endpoint prerequisite).
 *
 * Used INSIDE the AccountDeletionModal consent step. The owner MUST
 * check this checkbox BEFORE the [삭제 요청] button is enabled.
 *
 * UX locked: 격식체 종결 (AD-15 §11) + Negative/Destructive token.
 */

import { useTranslations } from "next-intl";

import { DELETION_CONSENT_TEMPLATE_KO } from "@/lib/m12-account-deletion";

interface DeletionConsentCheckboxProps {
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
}

export function DeletionConsentCheckbox({
  checked,
  onCheckedChange,
}: DeletionConsentCheckboxProps): React.ReactElement {
  const t = useTranslations("account_deletion");

  return (
    <div className="rounded-md border border-warning/30 bg-warning/5 p-3">
      <label className="flex items-start gap-3 text-sm">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => onCheckedChange(e.target.checked)}
          className="mt-0.5 h-4 w-4 rounded border-input"
          aria-required="true"
        />
        <span>
          <span className="font-medium">{t("consent_acknowledge")}</span>
          <span className="mt-1 block whitespace-pre-line text-muted-foreground">
            {DELETION_CONSENT_TEMPLATE_KO}
          </span>
        </span>
      </label>
    </div>
  );
}
