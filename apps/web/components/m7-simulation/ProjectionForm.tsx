"use client";

/**
 * apps/web/components/m7-simulation/ProjectionForm.tsx — Story 7.2 (Epic 7)
 *
 * React form for the 4 required parameters:
 *   - 차입금 (KRW 정수) / 이자율 (%) / 원가 상승률 (%) / 법인세율 (%)
 *
 * Per AC #2:
 *  - All 4 fields must be present + valid before [예측 실행] is enabled.
 *  - 100ms debounced validation triggers `allFieldsFilled` state.
 *  - [예측 실행] button `disabled={!allFieldsFilled}`.
 *
 * Implementation note (D-7-2-DEFER-7 honestly deferred):
 *  - Spec recommended react-hook-form + Zod schema, but those packages
 *    are not yet in apps/web/package.json. We use plain React useState +
 *    inline validation here, mirroring the same validation logic from
 *    `apps/web/lib/m7-simulation-projection-schema.ts` (Zod-style bounds).
 *  - This keeps the sprint within dependency scope; a follow-up sprint
 *    can add `zod` + `react-hook-form` and migrate to the Zod schema.
 */

import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

import {
  CORPORATE_TAX_RATE_MAX,
  CORPORATE_TAX_RATE_MIN,
  COST_INFLATION_RATE_MAX,
  COST_INFLATION_RATE_MIN,
  INTEREST_RATE_MAX,
  INTEREST_RATE_MIN,
  LOAN_AMOUNT_MAX,
  LOAN_AMOUNT_MIN,
  type ProjectionInputsSerialized,
} from "@/lib/m7-simulation-projection";

interface ProjectionFormProps {
  onSubmit: (values: ProjectionInputsSerialized) => void;
  onValidityChange: (isValid: boolean) => void;
  isSubmitting: boolean;
}

interface FormFields {
  loan_amount: string;
  interest_rate: string;
  cost_inflation_rate: string;
  corporate_tax_rate: string;
}

interface FormErrors {
  loan_amount: string | null;
  interest_rate: string | null;
  cost_inflation_rate: string | null;
  corporate_tax_rate: string | null;
}

const EMPTY_FIELDS: FormFields = {
  loan_amount: "",
  interest_rate: "",
  cost_inflation_rate: "",
  corporate_tax_rate: "",
};

export function ProjectionForm({
  onSubmit,
  onValidityChange,
  isSubmitting,
}: ProjectionFormProps): React.ReactElement {
  const t = useTranslations("projection_simulation");
  const [fields, setFields] = useState<FormFields>(EMPTY_FIELDS);
  const [errors, setErrors] = useState<FormErrors>({
    loan_amount: null,
    interest_rate: null,
    cost_inflation_rate: null,
    corporate_tax_rate: null,
  });

  // Validate fields, update errors + isValid.
  useEffect(() => {
    const newErrors = validateFields(fields, t);
    setErrors(newErrors);
    const allValid = Object.values(newErrors).every((e) => e === null);
    // 100ms debounce for `onValidityChange` to avoid jitter on every keystroke.
    const timer = setTimeout(() => {
      onValidityChange(allValid);
    }, 100);
    return () => clearTimeout(timer);
  }, [fields, onValidityChange, t]);

  const submitDisabled =
    isSubmitting ||
    errors.loan_amount !== null ||
    errors.interest_rate !== null ||
    errors.cost_inflation_rate !== null ||
    errors.corporate_tax_rate !== null ||
    fields.loan_amount === "" ||
    fields.interest_rate === "" ||
    fields.cost_inflation_rate === "" ||
    fields.corporate_tax_rate === "";

  const handleSubmit = (e: React.FormEvent): void => {
    e.preventDefault();
    if (submitDisabled) return;
    onSubmit({
      loan_amount: fields.loan_amount,
      interest_rate: fields.interest_rate,
      cost_inflation_rate: fields.cost_inflation_rate,
      corporate_tax_rate: fields.corporate_tax_rate,
    });
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-4 rounded border p-4"
      aria-label={t("form_section_label")}
      data-testid="projection-form"
    >
      <h2 className="text-lg font-medium">{t("form_section_label")}</h2>

      <ProjectionInput
        label={t("form_loan_amount")}
        suffix="원"
        type="number"
        step="1"
        min={LOAN_AMOUNT_MIN}
        max={LOAN_AMOUNT_MAX}
        placeholder="10000000"
        value={fields.loan_amount}
        onChange={(v) => setFields((p) => ({ ...p, loan_amount: v }))}
        error={errors.loan_amount}
        data-testid="projection-input-loan-amount"
        name="loan_amount"
      />

      <ProjectionInput
        label={t("form_interest_rate")}
        suffix="%"
        type="number"
        step="0.01"
        min={INTEREST_RATE_MIN}
        max={INTEREST_RATE_MAX}
        placeholder="5"
        value={fields.interest_rate}
        onChange={(v) => setFields((p) => ({ ...p, interest_rate: v }))}
        error={errors.interest_rate}
        data-testid="projection-input-interest-rate"
        name="interest_rate"
      />

      <ProjectionInput
        label={t("form_cost_inflation_rate")}
        suffix="%"
        type="number"
        step="0.01"
        min={COST_INFLATION_RATE_MIN}
        max={COST_INFLATION_RATE_MAX}
        placeholder="3"
        value={fields.cost_inflation_rate}
        onChange={(v) => setFields((p) => ({ ...p, cost_inflation_rate: v }))}
        error={errors.cost_inflation_rate}
        data-testid="projection-input-cost-inflation-rate"
        name="cost_inflation_rate"
      />

      <ProjectionInput
        label={t("form_corporate_tax_rate")}
        suffix="%"
        type="number"
        step="0.01"
        min={CORPORATE_TAX_RATE_MIN}
        max={CORPORATE_TAX_RATE_MAX}
        placeholder="22"
        value={fields.corporate_tax_rate}
        onChange={(v) => setFields((p) => ({ ...p, corporate_tax_rate: v }))}
        error={errors.corporate_tax_rate}
        data-testid="projection-input-corporate-tax-rate"
        name="corporate_tax_rate"
      />

      <button
        type="submit"
        disabled={submitDisabled}
        aria-disabled={submitDisabled}
        title={
          submitDisabled
            ? t("form_submit_button_tooltip")
            : t("form_submit_button")
        }
        data-testid="projection-submit-button"
        className={`w-full rounded px-4 py-2 text-white ${
          submitDisabled
            ? "cursor-not-allowed bg-gray-400"
            : "bg-blue-600 hover:bg-blue-700"
        }`}
      >
        {isSubmitting
          ? t("form_submit_button_submitting")
          : t("form_submit_button")}
      </button>
    </form>
  );
}

interface ProjectionInputProps {
  label: string;
  suffix: string;
  type: "number" | "text";
  step?: string;
  min?: number;
  max?: number;
  placeholder?: string;
  value: string;
  onChange: (value: string) => void;
  error: string | null;
  name: string;
  "data-testid"?: string;
}

function ProjectionInput({
  label,
  suffix,
  type,
  step,
  min,
  max,
  placeholder,
  value,
  onChange,
  error,
  name,
  ...rest
}: ProjectionInputProps): React.ReactElement {
  return (
    <div>
      <label className="block text-sm font-medium" htmlFor={name}>
        {label}
      </label>
      <div className="mt-1 flex items-center gap-2">
        <input
          id={name}
          type={type}
          step={step}
          min={min}
          max={max}
          placeholder={placeholder}
          value={value}
          name={name}
          onChange={(e) => onChange(e.target.value)}
          className={`flex-1 rounded border px-3 py-2 font-mono text-sm ${
            error ? "border-red-300" : "border-gray-300"
          }`}
          {...rest}
        />
        <span className="text-sm text-gray-500">{suffix}</span>
      </div>
      {error ? (
        <p className="mt-1 text-xs text-red-600" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}

// ── Validation helpers (mirror Zod schema bounds) ─────────────
type Translator = (key: string) => string;

function validateFields(fields: FormFields, t: Translator): FormErrors {
  return {
    loan_amount: validateLoanAmount(fields.loan_amount, t),
    interest_rate: validateInterestRate(fields.interest_rate, t),
    cost_inflation_rate: validateCostInflationRate(
      fields.cost_inflation_rate,
      t,
    ),
    corporate_tax_rate: validateCorporateTaxRate(
      fields.corporate_tax_rate,
      t,
    ),
  };
}

function validateLoanAmount(value: string, t: Translator): string | null {
  if (value === "") return t("form_loan_amount_required");
  const n = parseFloat(value);
  if (!Number.isFinite(n)) return "차입금은 숫자여야 합니다";
  if (!Number.isInteger(n)) return "차입금은 정수여야 합니다 (KRW)";
  if (n < 0) return "차입금은 0 이상이어야 합니다";
  if (n > LOAN_AMOUNT_MAX) return "차입금은 1조 원 이하여야 합니다";
  return null;
}

function validateInterestRate(value: string, t: Translator): string | null {
  if (value === "") return t("form_interest_rate_required");
  const n = parseFloat(value);
  if (!Number.isFinite(n)) return "이자율은 숫자여야 합니다";
  if (n < INTEREST_RATE_MIN) return "이자율은 0% 이상이어야 합니다";
  if (n > INTEREST_RATE_MAX) return "이자율은 100% 이하여야 합니다";
  return null;
}

function validateCostInflationRate(
  value: string,
  t: Translator,
): string | null {
  if (value === "") return t("form_cost_inflation_rate_required");
  const n = parseFloat(value);
  if (!Number.isFinite(n)) return "원가 상승률은 숫자여야 합니다";
  if (n < COST_INFLATION_RATE_MIN)
    return "원가 상승률은 -50% 이상이어야 합니다";
  if (n > COST_INFLATION_RATE_MAX) return "원가 상승률은 100% 이하여야 합니다";
  return null;
}

function validateCorporateTaxRate(
  value: string,
  t: Translator,
): string | null {
  if (value === "") return t("form_corporate_tax_rate_required");
  const n = parseFloat(value);
  if (!Number.isFinite(n)) return "법인세율은 숫자여야 합니다";
  if (n < CORPORATE_TAX_RATE_MIN) return "법인세율은 0% 이상이어야 합니다";
  if (n > CORPORATE_TAX_RATE_MAX) return "법인세율은 100% 이하여야 합니다";
  return null;
}
