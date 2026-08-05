// apps/web/next.config.ts — Next.js config with next-intl plugin
// Story 0.5 — T6.6 (AC #6)

import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./i18n.ts");

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
};

export default withNextIntl(nextConfig);
