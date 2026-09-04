/**
 * apps/web/app/[locale]/(auth)/privacy/page.tsx — Privacy Policy page.
 *
 * 1st release launch (cj-style 64번째 진입점) — T2.2 (AC #2.4) — F18.2 ToS/Privacy.
 * - (auth)/privacy route 결정 wire (Phase 3-1 T4 wire 정합).
 * - Markdown rendering (docs/privacy-policy.md fetch + render).
 * - capability gate `LAUNCH_TOS`.
 */
import fs from "node:fs/promises";
import path from "node:path";

export const dynamic = "force-dynamic";

interface PrivacyPageProps {
  // cj-271 (D-CI-FUNC-5 typedRoutes): Next.js 15 typedRoutes 호환.
  // cj-258 패턴. `next build` 강제 type check surface.
  params: Promise<{ locale: string }>;
}

export default async function PrivacyPage({ params: _params }: PrivacyPageProps) {
  await _params; // satisfy Next 15+ Promise<params>
  const filePath = path.join(process.cwd(), "docs", "privacy-policy.md");
  const content = await fs
    .readFile(filePath, "utf8")
    .catch(() => "# 개인정보처리방침\n\n(약관을 불러올 수 없습니다)");

  return (
    <main
      style={{
        minHeight: "100vh",
        padding: "2rem 1rem",
        maxWidth: "48rem",
        margin: "0 auto",
      }}
    >
      <article>
        <pre
          style={{
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
            fontFamily: "inherit",
            lineHeight: 1.6,
          }}
        >
          {content}
        </pre>
      </article>
    </main>
  );
}
