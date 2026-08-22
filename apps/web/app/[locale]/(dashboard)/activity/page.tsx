/**
 * apps/web/app/[locale]/(dashboard)/activity/page.tsx — Epic 17 T3 (AC #3.1)
 *
 * RSC page for /activity (activity stream timeline).
 *
 * Per PRD §F21.3 + AD-32 (c):
 *   - Server-side fetch initial activity stream via
 *     `fetchActivityStreamServerSide` (F-20 race-free initial fetch).
 *   - Hand the response (or fail-closed null) to `<ActivityStreamPanel>`
 *     which orchestrates ActivityStreamTimeline /
 *     ActivityStreamEntry / ActivityStreamWindowSelector.
 *
 * Window selector is URL-synced via `?window_days=...` (default 7).
 *
 * The path resolves under `/[locale]/(dashboard)/activity`. It is
 * the frontend half of Epic 17 territory (the backend was wired in
 * commit `2ada2ec`).
 */
import { cookies } from "next/headers";

import { ActivityStreamPanel } from "@/components/activity/ActivityStreamPanel";
import { fetchActivityStreamServerSide } from "@/lib/server-api";

export const dynamic = "force-dynamic";

interface ActivityPageProps {
  params: Promise<{ locale: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

function toStr(v: string | string[] | undefined): string | undefined {
  if (Array.isArray(v)) return v[0];
  return v;
}

const ALLOWED_WINDOWS: ReadonlyArray<1 | 7 | 30 | 90> = [1, 7, 30, 90];

function toWindowDays(raw: string | undefined): 1 | 7 | 30 | 90 {
  const n = parseInt(raw ?? "7", 10);
  if (ALLOWED_WINDOWS.includes(n as 1 | 7 | 30 | 90)) {
    return n as 1 | 7 | 30 | 90;
  }
  return 7;
}

export default async function ActivityPage({
  params,
  searchParams,
}: ActivityPageProps): Promise<React.ReactElement> {
  await params;

  const cookieStore = await cookies();
  const accessToken = cookieStore.get("sb-access-token")?.value;
  if (!accessToken) {
    return (
      <main className="p-6">
        <p>세션이 만료되었습니다. 다시 로그인해 주세요.</p>
      </main>
    );
  }

  const traceId = crypto.randomUUID();
  const sp = await searchParams;
  const windowDays = toWindowDays(toStr(sp.window_days));

  const initialGroups = await fetchActivityStreamServerSide(
    accessToken,
    windowDays,
    traceId,
  );

  return (
    <main className="p-6">
      <ActivityStreamPanel
        accessToken={accessToken}
        initialGroups={initialGroups ?? []}
        initialWindowDays={windowDays}
      />
    </main>
  );
}
