/**
 * apps/web/app/[locale]/(auth)/onboarding/page.tsx — 4-step first-run wizard.
 *
 * 1st release launch (cj-style 64번째 진입점) — T3.2 (AC #3.3) — F18.3 Onboarding guide.
 * - first-run wizard 결정 wire (4-step wizard).
 * - localStorage EXTENSION: costmgr.onboarding.completed flag.
 * - Epic 1 partial scaffold 정합 sweep (D-001 actual mount MUST validate).
 */
"use client";

import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

const STORAGE_KEY = "costmgr.onboarding.completed";

export default function OnboardingPage() {
  const t = useTranslations("onboarding");
  const [step, setStep] = useState(1);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setHydrated(true);
    if (typeof window !== "undefined") {
      const completed = window.localStorage.getItem(STORAGE_KEY);
      if (completed === "true") {
        window.location.href = "/ko-KR/dashboard";
      }
    }
  }, []);

  const handleComplete = () => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, "true");
      window.location.href = "/ko-KR/dashboard";
    }
  };

  const handleSkip = () => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, "true");
      window.location.href = "/ko-KR/dashboard";
    }
  };

  if (!hydrated) {
    return null;
  }

  return (
    <main
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "2rem 1rem",
      }}
    >
      <div style={{ maxWidth: "32rem", width: "100%", textAlign: "center" }}>
        <h1 style={{ fontSize: "1.75rem", fontWeight: 700, marginBottom: "0.5rem" }}>
          {t("welcome_title")}
        </h1>
        <p style={{ opacity: 0.7, marginBottom: "2.5rem" }}>{t("welcome_subtitle")}</p>

        <div
          style={{
            display: "flex",
            justifyContent: "center",
            gap: "0.5rem",
            marginBottom: "2rem",
          }}
        >
          {[1, 2, 3, 4].map((s) => (
            <div
              key={s}
              style={{
                width: "0.5rem",
                height: "0.5rem",
                borderRadius: "50%",
                background: s === step ? "var(--primary, #2563eb)" : "rgba(0,0,0,0.2)",
              }}
              aria-current={s === step ? "step" : undefined}
            />
          ))}
        </div>

        <h2 style={{ fontSize: "1.25rem", fontWeight: 600, marginBottom: "2rem" }}>
          {step === 1 && t("step_dashboard_title")}
          {step === 2 && t("step_data_title")}
          {step === 3 && t("step_reports_title")}
          {step === 4 && t("step_security_title")}
        </h2>

        <div style={{ display: "flex", gap: "1rem", justifyContent: "center" }}>
          {step > 1 && (
            <button
              type="button"
              onClick={() => setStep((s) => s - 1)}
              style={{ padding: "0.5rem 1.5rem", border: "1px solid currentColor", borderRadius: "0.5rem" }}
            >
              이전
            </button>
          )}
          <button
            type="button"
            onClick={handleSkip}
            style={{ padding: "0.5rem 1.5rem", border: "none", background: "transparent" }}
          >
            {t("skip_button")}
          </button>
          {step < 4 ? (
            <button
              type="button"
              onClick={() => setStep((s) => s + 1)}
              style={{
                padding: "0.5rem 1.5rem",
                background: "var(--primary, #2563eb)",
                color: "#fff",
                border: "none",
                borderRadius: "0.5rem",
              }}
            >
              다음
            </button>
          ) : (
            <button
              type="button"
              onClick={handleComplete}
              style={{
                padding: "0.5rem 1.5rem",
                background: "var(--primary, #2563eb)",
                color: "#fff",
                border: "none",
                borderRadius: "0.5rem",
              }}
            >
              {t("complete_button")}
            </button>
          )}
        </div>
      </div>
    </main>
  );
}
