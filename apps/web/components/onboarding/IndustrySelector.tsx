/**
 * apps/web/components/onboarding/IndustrySelector.tsx — 4-card industry selector.
 *
 * Story 1.1 — Task 3.2. Client Component. Renders the 4지선다 cards, calls
 * POST `/api/v1/tenant-settings/onboarding/industry` on click, and on
 * success updates the MenuContext (which the sidebar reads).
 *
 * Error handling:
 *   - 422 (invalid industry) → toast "잘못된 업종 값입니다"
 *   - 403 (non-owner)        → toast "owner 역할만 업종을 변경할 수 있습니다"
 *   - 409 INDUSTRY_LOCKED    → toast with A7 전진법 message + show
 *                              current industry (from payload, F-20) as read-only
 *   - Other                 → generic toast
 *
 * F-19: uses a structural type guard based on `status` + `payload.code`
 * rather than `instanceof ApiError` so serialized/cross-realm errors
 * still hit the typed branches.
 *
 * F-21: locale-aware router.push preserves the active [locale] segment.
 *
 * Next-intl integration: ko-KR strings are inlined for now. Story 0.5
 * wires next-intl; we'll swap to `useTranslations('m0_onboarding')`
 * once the i18n bundle is in place.
 */

"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";

import { ApiError, updateIndustry } from "@/lib/api-client";
import {
  INDUSTRY_LABEL_KO,
  INDUSTRY_MENU_MAP,
  INDUSTRY_VALUES,
  type Industry,
} from "@/lib/menu-config";

import { IndustryCard } from "./IndustryCard";
import { useMenuContext } from "../sidebar/MenuContext";

export interface IndustrySelectorProps {
  /** Access token (string) forwarded from the Server Component. (F-4.)
   *  Pass the literal string, not a function — function props cannot
   *  cross the RSC boundary. */
  accessToken?: string;
  /** Optional callback after a successful selection. */
  onSuccess?: (industry: Industry) => void;
}

// F-19: structural type guard — checks `status` + payload shape rather
// than relying on instanceof, which fails for cross-realm/serialized errors.
function isApiErrorLike(err: unknown): err is ApiError {
  return (
    typeof err === "object" &&
    err !== null &&
    "status" in err &&
    typeof (err as { status: unknown }).status === "number" &&
    "payload" in err &&
    typeof (err as { payload: { code?: unknown } }).payload?.code === "string"
  );
}

export function IndustrySelector({
  accessToken,
  onSuccess,
}: IndustrySelectorProps) {
  const router = useRouter();
  const params = useParams<{ locale?: string }>();
  // F-21: derive the locale from the route params. Fallback to "ko-KR"
  // for safety if params are not available (e.g., during SSR).
  const locale: string = (params?.locale as string | undefined) ?? "ko-KR";
  const { setIndustry } = useMenuContext();
  const [selected, setSelected] = useState<Industry | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [lockedMessage, setLockedMessage] = useState<string | null>(null);
  const [lockedIndustry, setLockedIndustry] = useState<Industry | null>(null);

  async function handleSelect(industry: Industry) {
    if (isSubmitting) return;
    setSelected(industry);
    setIsSubmitting(true);
    setToast(null);
    setLockedMessage(null);
    setLockedIndustry(null);

    try {
      const result = await updateIndustry(
        {
          industry,
          onWarningHeader: () => {
            setToast("7일 이내 변경 안내 — 감사 로그에 기록되었습니다");
          },
        },
        accessToken,
      );
      setIndustry(result.industry, result.menu);
      onSuccess?.(result.industry);
      // F-21: navigate within the active locale segment.
      router.push(`/${locale}/dashboard`);
    } catch (err) {
      setSelected(null);
      if (isApiErrorLike(err)) {
        // F-19: structural guard — handle typed branches even when
        // the error object didn't survive `instanceof ApiError`.
        const code = err.payload.code;
        if (code === "INDUSTRY_LOCKED") {
          const details = err.payload.details as {
            next_fiscal_year_start?: string;
            current_industry?: string;
          };
          const nextFy = details?.next_fiscal_year_start ?? "내년";
          // F-20: pull the actual current industry from the payload.
          const rawCurrent = details?.current_industry;
          const currentIndustry =
            rawCurrent && (INDUSTRY_VALUES as readonly string[]).includes(rawCurrent)
              ? (rawCurrent as Industry)
              : null;
          setLockedIndustry(currentIndustry);
          setLockedMessage(
            `업종이 A7 전진법으로 잠겼습니다. 다음 회계연도(${nextFy})부터 변경 가능`,
          );
        } else if (code === "FORBIDDEN_ROLE") {
          setToast("업종 변경은 owner 역할만 가능합니다");
        } else if (code === "TENANT_SETTINGS_NOT_FOUND") {
          setToast("테넌트 설정을 찾을 수 없습니다. 관리자에게 문의하세요");
        } else {
          setToast(err.payload.message_ko);
        }
      } else {
        setToast("업종 저장에 실패했습니다. 잠시 후 다시 시도해 주세요");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section
      aria-labelledby="industry-selector-heading"
      style={{ maxWidth: 720, margin: "0 auto", padding: "2rem 1rem" }}
    >
      <h1
        id="industry-selector-heading"
        style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.5rem" }}
      >
        업종을 선택해 주세요
      </h1>
      <p style={{ color: "#475569", marginBottom: "1.5rem" }}>
        선택한 업종에 따라 메뉴가 자동으로 토글됩니다. 가입 후 7일 이내에는
        변경할 수 있습니다.
      </p>

      <div
        role="radiogroup"
        aria-labelledby="industry-selector-heading"
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "0.75rem",
        }}
      >
        {INDUSTRY_VALUES.map((industry) => (
          <IndustryCard
            key={industry}
            industry={industry}
            selected={selected === industry}
            disabled={isSubmitting}
            onClick={handleSelect}
          />
        ))}
      </div>

      {toast && (
        <p
          role="status"
          style={{
            marginTop: "1rem",
            padding: "0.75rem 1rem",
            borderRadius: 8,
            background: "#fef3c7",
            color: "#92400e",
            fontSize: "0.875rem",
          }}
        >
          {toast}
        </p>
      )}

      {lockedMessage && (
        <p
          role="alert"
          style={{
            marginTop: "1rem",
            padding: "0.75rem 1rem",
            borderRadius: 8,
            background: "#fee2e2",
            color: "#991b1b",
            fontSize: "0.875rem",
          }}
        >
          {lockedMessage}
          <br />
          {/* F-20: render the actual current industry from the API payload, not a hardcoded value. */}
          현재 업종:{" "}
          <strong>
            {lockedIndustry ? INDUSTRY_LABEL_KO[lockedIndustry] : "(확인 불가)"}
          </strong>{" "}
          (읽기 전용)
        </p>
      )}
    </section>
  );
}