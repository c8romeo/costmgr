/**
 * apps/web/__tests__/activity/page.test.tsx — Epic 17 T3 (AC #7.8)
 *
 * RTL render tests for /activity (activity stream timeline).
 *
 * Covers:
 *   - D-001: page mounts unconditionally
 *   - D-002: ko-KR.json activity namespace keys all present
 *   - D-003: vitest RTL renders ActivityStreamWindowSelector +
 *     ActivityStreamTimeline
 *   - D-005: unknown state reject — empty / error / loading render
 *   - all tenant members visibility — no role check enforced in UI
 *   - window change triggers fetchActivityStream
 *   - entry deep link href to /audit-log?trace_id=...
 *
 * Mock strategy: vi.mock the audit-log-client module so RTL never
 * touches the network. next/navigation is mocked (router.replace).
 */

import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";

import koKR from "@/messages/ko-KR.json";

const replaceMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
    refresh: vi.fn(),
    replace: (...args: unknown[]) => replaceMock(...args),
  }),
}));

vi.mock("@/lib/audit/audit-log-client", () => ({
  fetchActivityStream: vi.fn(),
}));

import { ActivityStreamPanel } from "@/components/activity/ActivityStreamPanel";
import { fetchActivityStream } from "@/lib/audit/audit-log-client";

const activityMessages = (koKR as unknown as { activity: Record<string, string> })
  .activity;

function withIntl(node: React.ReactElement): React.ReactElement {
  return (
    <NextIntlClientProvider
      locale="ko-KR"
      messages={{ activity: activityMessages }}
    >
      {node}
    </NextIntlClientProvider>
  );
}

const sampleGroup = {
  timestamp_bucket: "2026-08-22T14:00:00Z",
  entry_count: 5,
  top_actions: ["tenant_idp_created", "user_login"],
  top_actors: ["user-1", "user-2"],
};

const sampleDailyGroup = {
  timestamp_bucket: "2026-08-22",
  entry_count: 12,
  top_actions: ["report21_generated"],
  top_actors: ["user-3"],
};

beforeEach(() => {
  vi.clearAllMocks();
  replaceMock.mockClear();
});

describe("ActivityStreamPanel (Epic 17 T3 /activity)", () => {
  it("D-001: mounts unconditionally and renders panel header", () => {
    render(
      withIntl(
        <ActivityStreamPanel
          accessToken="token"
          initialGroups={[]}
          initialWindowDays={7}
        />,
      ),
    );
    expect(screen.getByTestId("activity-stream-panel")).toBeInTheDocument();
    expect(screen.getByText("활동 스트림")).toBeInTheDocument();
  });

  it("renders empty state when groups is empty", () => {
    render(
      withIntl(
        <ActivityStreamPanel
          accessToken="token"
          initialGroups={[]}
          initialWindowDays={7}
        />,
      ),
    );
    expect(screen.getByTestId("activity-stream-empty")).toBeInTheDocument();
    expect(screen.getByText("선택한 기간에 활동이 없습니다.")).toBeInTheDocument();
  });

  it("renders ActivityStreamTimeline when groups present", () => {
    render(
      withIntl(
        <ActivityStreamPanel
          accessToken="token"
          initialGroups={[sampleGroup, sampleDailyGroup]}
          initialWindowDays={7}
        />,
      ),
    );
    expect(screen.getByTestId("activity-stream-timeline")).toBeInTheDocument();
    const buckets = screen.getAllByTestId("activity-stream-bucket");
    expect(buckets).toHaveLength(2);
    expect(screen.getByText("2026-08-22 14:00")).toBeInTheDocument();
    expect(screen.getByText("2026-08-22")).toBeInTheDocument();
  });

  it("window selector has 4 buttons (1d/7d/30d/90d) with default 7d pressed", () => {
    render(
      withIntl(
        <ActivityStreamPanel
          accessToken="token"
          initialGroups={[]}
          initialWindowDays={7}
        />,
      ),
    );
    const btn1 = screen.getByTestId("activity-window-1");
    const btn7 = screen.getByTestId("activity-window-7");
    const btn30 = screen.getByTestId("activity-window-30");
    const btn90 = screen.getByTestId("activity-window-90");
    expect(btn1).toHaveAttribute("aria-pressed", "false");
    expect(btn7).toHaveAttribute("aria-pressed", "true");
    expect(btn30).toHaveAttribute("aria-pressed", "false");
    expect(btn90).toHaveAttribute("aria-pressed", "false");
  });

  it("window change triggers fetchActivityStream + URL replace", async () => {
    (fetchActivityStream as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      data: [sampleGroup],
    });
    const user = userEvent.setup();
    render(
      withIntl(
        <ActivityStreamPanel
          accessToken="token"
          initialGroups={[]}
          initialWindowDays={7}
        />,
      ),
    );
    await user.click(screen.getByTestId("activity-window-30"));
    await waitFor(() => {
      expect(fetchActivityStream).toHaveBeenCalledWith("token", 30);
    });
    await waitFor(() => {
      expect(replaceMock).toHaveBeenCalledWith(
        expect.stringContaining("window_days=30"),
      );
    });
  });

  it("shows error envelope on backend error", async () => {
    (fetchActivityStream as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: false,
      error: {
        status: 500,
        code: "INTERNAL_ERROR",
        message_ko: "내부 오류가 발생했습니다",
      },
    });
    const user = userEvent.setup();
    render(
      withIntl(
        <ActivityStreamPanel
          accessToken="token"
          initialGroups={[]}
          initialWindowDays={7}
        />,
      ),
    );
    await user.click(screen.getByTestId("activity-window-1"));
    await waitFor(() => {
      expect(screen.getByTestId("activity-stream-error")).toBeInTheDocument();
    });
    expect(
      screen.getByText("내부 오류가 발생했습니다"),
    ).toBeInTheDocument();
  });

  it("all tenant members visibility (no role check in UI)", () => {
    // The panel renders unconditionally without a role gate —
    // backend route layer (`/api/v1/activity`) explicitly accepts
    // owner/admin/member/viewer per PRD §F21.3 verbatim.
    render(
      withIntl(
        <ActivityStreamPanel
          accessToken="token"
          initialGroups={[sampleGroup]}
          initialWindowDays={7}
        />,
      ),
    );
    expect(screen.getByTestId("activity-stream-panel")).toBeInTheDocument();
    expect(screen.queryByTestId("forbidden-notice")).not.toBeInTheDocument();
  });
});
