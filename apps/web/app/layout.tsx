// apps/web/app/layout.tsx — Next.js App Router root layout
// Story 0.5 — T1.5/T1.6 (AC #1) — Pretendard next/font/local + Tailwind globals.css
//                  T3.3 (AC #3) — sonner <Toaster /> wired
// Resolves Story 0.1 L4 (Pretendard CDN without SRI) + Story 0.4 design tokens.

import localFont from "next/font/local";
import type { ReactNode } from "react";

import { Toaster } from "@/components/ui/sonner";

import "./globals.css";

const pretendard = localFont({
  src: "../public/fonts/PretendardVariable.woff2",
  display: "swap",
  weight: "45 920",
  variable: "--font-pretendard",
  preload: true,
  fallback: [
    "-apple-system",
    "BlinkMacSystemFont",
    "system-ui",
    "Roboto",
    "Helvetica Neue",
    "Segoe UI",
    "Apple SD Gothic Neo",
    "Noto Sans KR",
    "Malgun Gothic",
    "sans-serif",
  ],
});

export const metadata = {
  title: "bizup/costmgr",
  description: "원가 관리 SaaS (modular monolith + hexagonal core)",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ko" className={pretendard.variable}>
      <body className="bg-background text-foreground font-sans antialiased">
        {children}
        <Toaster />
      </body>
    </html>
  );
}
