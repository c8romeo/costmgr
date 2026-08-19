/**
 * apps/web/app/[locale]/(dashboard)/ai/comments/page.tsx — Sprint 10.5 T3 wire (D-10-3-DEFER-4 해소)
 *
 * Story 10.3 (AI Reference vs Auto Analysis Badge Separation) RSC mount page.
 *
 * Per AC #3 (Sprint 10.5 T3):
 *  - Server-side render: pass accessToken to `<AiCommentSection>`
 *    (Client Component).
 *  - CR 11-4 D-001: page MUST actually mount the JSX.
 */

import { cookies } from "next/headers";

import { AiCommentSection } from "@/components/m10-ai";

export const dynamic = "force-dynamic";

interface AiCommentsPageProps {
  params: Promise<{ locale: string }>;
}

export default async function AiCommentsPage({
  params,
}: AiCommentsPageProps): Promise<React.ReactElement> {
  await params;

  const cookieStore = await cookies();
  const accessToken = cookieStore.get("sb-access-token")?.value;

  return (
    <AiCommentSection
      accessToken={accessToken}
      initialPeriodKey={new Date().toISOString().slice(0, 7)}
    />
  );
}
