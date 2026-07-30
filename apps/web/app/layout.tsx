// apps/web/app/layout.tsx — Next.js App Router root layout (Story 0.1 stub)
// Locale: ko-KR (AD-15), Pretendard font fallback (deferred to bmad-ux).

import type { ReactNode } from 'react';

export const metadata = {
  title: 'bizup/costmgr',
  description: '원가 관리 SaaS (modular monolith + hexagonal core)',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ko">
      <head>
        <link
          rel="stylesheet"
          href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css"
        />
      </head>
      <body style={{ fontFamily: 'Pretendard Variable, Pretendard, -apple-system, system-ui, sans-serif' }}>
        {children}
      </body>
    </html>
  );
}
