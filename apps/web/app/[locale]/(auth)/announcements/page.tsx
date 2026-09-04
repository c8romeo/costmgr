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
  // cj-271 (D-CI-FUNC-5 typedRoutes): Next.js 15 typedRoutes 호환 —
  // `params: { locale: string }` (sync) → `Promise<{ locale: string }>` (async).
  // `next dev` 는 type check skip 했으나 `next build` 는 강제 → step 8 FAIL
  // surface 됨 (cj-258 와 동일 패턴, 1 file 누락).
  params: Promise<{ locale: string }>;
}

export default async function AnnouncementsPage({ params: _params }: AnnouncementsPageProps) {
  await _params; // satisfy Next 15+ Promise<params>
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
