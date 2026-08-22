/**
 * apps/web/components/support/HelpWidget.tsx — In-app help widget (floating button).
 *
 * 1st release launch (cj-style 64번째 진입점) — T4.2 (AC #4.3) — F18.4 Support channels.
 * - floating button bottom-right corner 결정 wire.
 * - FAQ link + contact form + support@bizup.kr mailto link 결정.
 * - capability gate `LAUNCH_SUPPORT`.
 */
"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";

export function HelpWidget() {
  const t = useTranslations("support");
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-label={t("widget_button")}
        style={{
          position: "fixed",
          bottom: "1.5rem",
          right: "1.5rem",
          width: "3rem",
          height: "3rem",
          borderRadius: "50%",
          background: "var(--primary, #2563eb)",
          color: "#fff",
          border: "none",
          cursor: "pointer",
          fontSize: "1.5rem",
          boxShadow: "0 4px 12px rgba(0,0,0,0.2)",
          zIndex: 999,
        }}
      >
        ?
      </button>
      {open && (
        <div
          role="dialog"
          aria-label={t("title")}
          style={{
            position: "fixed",
            bottom: "5rem",
            right: "1.5rem",
            width: "20rem",
            maxWidth: "calc(100vw - 3rem)",
            background: "var(--bg, #fff)",
            color: "var(--fg, #000)",
            border: "1px solid rgba(0,0,0,0.1)",
            borderRadius: "0.75rem",
            padding: "1.25rem",
            boxShadow: "0 8px 24px rgba(0,0,0,0.15)",
            zIndex: 999,
          }}
        >
          <h2 style={{ fontSize: "1.1rem", fontWeight: 600, marginBottom: "0.75rem" }}>
            {t("title")}
          </h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            <a
              href="/ko-KR/support"
              style={{ color: "var(--primary, #2563eb)", textDecoration: "none" }}
            >
              {t("contact_form_title")}
            </a>
            <a
              href="/ko-KR/faq"
              style={{ color: "var(--primary, #2563eb)", textDecoration: "none" }}
            >
              {t("faq_link")}
            </a>
            <a
              href={`mailto:${t("email_value")}`}
              style={{ color: "var(--primary, #2563eb)", textDecoration: "none" }}
            >
              {t("email_label")}: {t("email_value")}
            </a>
          </div>
          <div style={{ marginTop: "1rem", fontSize: "0.8rem", opacity: 0.7 }}>
            <div>{t("sla_p1")}</div>
            <div>{t("sla_p2")}</div>
          </div>
        </div>
      )}
    </>
  );
}
