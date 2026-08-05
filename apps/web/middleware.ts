// apps/web/middleware.ts — next-intl middleware
// Story 0.5 — T6.5 (AC #6)

import createMiddleware from "next-intl/middleware";

export default createMiddleware({
  locales: ["ko-KR"],
  defaultLocale: "ko-KR",
  localePrefix: "as-needed",
});

export const config = {
  // Match all pathnames except for
  // - API, _next, _vercel, monitoring endpoints
  matcher: ["/((?!api|_next|_vercel|.*\\..*).*)"],
};
