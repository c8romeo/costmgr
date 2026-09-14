// apps/web/next.config.ts — Next.js config with next-intl plugin
// Story 0.5 — T6.6 (AC #6)

import createNextIntlPlugin from "next-intl/plugin";
import type { NextConfig } from "next";

const withNextIntl = createNextIntlPlugin("./i18n.ts");

/** @type {import('next').NextConfig} */
const nextConfig: NextConfig = {
  reactStrictMode: true,
  // cj-style N+7 (admin 시점 verification gate) — frontend ↔ backend
  // 자동 연결. 모든 `/api/v1/*` 호출을 backend :8000 으로 forward.
  // 결정 wire 보존: env-free local dev only, LOW risk (config 1 attr).
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: "http://localhost:8000/api/v1/:path*",
      },
    ];
  },
};

export default withNextIntl(nextConfig);
