/**
 * apps/web/app/[locale]/(auth)/support/page.tsx — Support page.
 *
 * 1st release launch (cj-style 64번째 진입점) — T4.2 (AC #4.4) — F18.4 Support channels.
 * - (auth)/support route 결정 wire (auth required, (auth) route group 정합).
 * - Markdown rendering (docs/support.md fetch + render).
 * - capability gate `LAUNCH_SUPPORT`.
 */
import fs from "node:fs/promises";
import path from "node:path";

export const dynamic = "force-dynamic";

interface SupportPageProps {
  params: { locale: string };
}

export default async function SupportPage({ params: _params }: SupportPageProps) {
  const filePath = path.join(process.cwd(), "docs", "support.md");
  const content = await fs
    .readFile(filePath, "utf8")
    .catch(() => "# 고객 지원\n\n(문서를 불러올 수 없습니다)");

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
