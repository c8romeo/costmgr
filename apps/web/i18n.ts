// apps/web/i18n.ts — next-intl getRequestConfig
// Story 0.5 — T6.4 (AC #6)
//
// Locale: ko-KR default (post-MVP multi-locale deferred).
// Messages loaded from ./messages/${locale}.json.

import { getRequestConfig } from "next-intl/server";

export default getRequestConfig(async () => {
  const locale = "ko-KR";

  return {
    locale,
    timeZone: "Asia/Seoul",
    messages: (await import(`./messages/${locale}.json`)).default,
  };
});
