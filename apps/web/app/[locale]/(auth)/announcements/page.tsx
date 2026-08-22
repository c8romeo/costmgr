/**
 * apps/web/app/[locale]/(auth)/announcements/page.tsx — In-app announcement page.
 *
 * 1st release launch (cj-style 64번째 진입점) — T8.2 (AC #6.4) — F18.6 Public launch communications.
 * - (auth)/announcements route 결정 wire (in-app announcement banner).
 * - Markdown rendering (docs/launch-announcement.md fetch + render).
 */
import fs from "node:fs/promises";
import path from "node:path";

export const dynamic = "force-dynamic";

interface AnnouncementsPageProps {
  params: { locale: string };
}

export default async function AnnouncementsPage({ params: _params }: AnnouncementsPageProps) {
  const filePath = path.join(process.cwd(), "docs", "launch-announcement.md");
  const content = await fs
    .readFile(filePath, "utf8")
    .catch(() => "# 출시 안내\n\n(문서를 불러올 수 없습니다)");

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
