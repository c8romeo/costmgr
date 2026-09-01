/**
 * apps/web/app/[locale]/layout.tsx — locale-segment layout.
 *
 * cj-253 (D-CI-FUNC-5 PART 4) — NextIntlClientProvider 누락 root cause CLOSED.
 *
 * next-intl 인프라 (i18n.ts + middleware + messages/ko-KR.json) 는 정상 동작
 * 중이었으나 client component 가 `useTranslations()` 를 호출하려면
 * `<NextIntlClientProvider messages={...}>` 가 트리에 존재해야 했다. 이 파일이
 * 부재하여 web-e2e SSR 단계에서 "Failed to call useTranslations because the
 * context from NextIntlClientProvider was not found" 가 1272회 발생.
 *
 * 디자인 결정:
 *  - getMessages() : server-side 에서 messages/ko-KR.json 을 로드하여 provider
 *    에 주입. 클라이언트 컴포넌트에서 `useTranslations('namespace')` 호출 가능.
 *  - root app/layout.tsx 가 이미 <html>/<body> 소유 → 이 layout 은 fragment 만
 *    반환 (중복 <html> 금지, root layout 의 Pretendard font / Toaster 유지).
 *  - i18n.ts 가 locale 을 'ko-KR' 하드코드 → provider 의 locale prop 도 'ko-KR'
 *    고정. params.locale 는 향후 multi-locale 도입 시 사용 (현재 미사용).
 *  - unstable_setRequestLocale 미사용 — 모든 layout 이 `dynamic =
 *    'force-dynamic'` 이므로 정적 렌더 회피됨.
 *  - 'use client' 미사용 — server layout 으로 동작 (getMessages 는 server-only).
 *
 * 영향 범위 (100 files useTranslations caller):
 *   - clients: 변경 0 (이 layout 만 추가하면 자동 적용)
 *   - 다른 layout: 변경 0 (root / (dashboard) / (auth) 모두 그대로)
 *   - wiring: 새 파일 1개 +15 lines
 */
import { NextIntlClientProvider } from "next-intl";
import { getMessages } from "next-intl/server";
import type { ReactNode } from "react";

type LocaleLayoutProps = {
  children: ReactNode;
  params: { locale: string };
};

export default async function LocaleLayout({
  children,
  params: _params,
}: LocaleLayoutProps) {
  const messages = await getMessages();

  return (
    <NextIntlClientProvider locale="ko-KR" messages={messages}>
      {children}
    </NextIntlClientProvider>
  );
}
