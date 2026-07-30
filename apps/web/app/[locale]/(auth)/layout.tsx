/**
 * apps/web/app/[locale]/(auth)/layout.tsx — auth route group shell.
 *
 * Story 1.1 — F-3 (spec File List had this file listed but it was missing
 * from the implementation). Minimal layout so Next.js resolves the (auth)
 * route group consistently for `/login`, `/signup`, `/forgot-password`,
 * `/onboarding/industry`, etc.
 *
 * Subsequent stories add the actual auth shells. This file is intentionally
 * minimal — just `{children}` — to avoid coupling to design tokens Story 0.5
 * will own.
 */

import type { ReactNode } from "react";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        background: "#f8fafc",
      }}
    >
      {children}
    </div>
  );
}