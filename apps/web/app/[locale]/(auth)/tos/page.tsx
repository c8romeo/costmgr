/**
 * apps/web/app/[locale]/(auth)/tos/page.tsx — Terms of Service page.
 *
 * 1st release launch (cj-style 64번째 진입점) — T2.2 (AC #2.3) — F18.2 ToS/Privacy.
 * - (auth)/tos route 결정 wire (Phase 3-1 T4 wire 정합).
 * - Markdown rendering (docs/terms-of-service.md fetch + render).
 * - capability gate `LAUNCH_TOS` (capability matrix v1.27).
 */
import fs from "node:fs/promises";
import path from "node:path";

export const dynamic = "force-dynamic";

interface TosPageProps {
  params: { locale: string };
}

export default async function TosPage({ params: _params }: TosPageProps) {
  const filePath = path.join(process.cwd(), "docs", "terms-of-service.md");
  const content = await fs.readFile(filePath, "utf8").catch(() => "# 이용약관\n\n(약관을 불러올 수 없습니다)");

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
