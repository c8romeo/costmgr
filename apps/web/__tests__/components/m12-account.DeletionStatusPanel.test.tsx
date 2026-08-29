// apps/web/__tests__/components/m12-account.DeletionStatusPanel.test.tsx — Story 12.3
//
// Component test for the DeletionStatusPanel (CR 11-4 D-001 — page.tsx
// actually mounts + renders).
//
// 6 cases verify:
//  - Renders the panel title (Korean)
//  - ACTIVE status shows "활성" label + [계정 삭제하기] button
//  - PENDING_DELETION status shows "삭제 대기" + days remaining + [취소하기]
//  - DELETED status (initialStatus=null) shows terminal message
//  - Korean SSOT strings from ko-KR.json (CR 11-4 D-002)

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { DeletionStatusPanel } from "../../components/m12-account/DeletionStatusPanel";
import { TenantDeletionStatus } from "../../lib/m12-account-deletion";
import type { DeletionStatusResponse } from "../../lib/m12-account-deletion";
import koKR from "../../messages/ko-KR.json";

vi.mock("next-intl", () => ({
  useTranslations: (namespace: string) => {
    return (key: string, vars?: Record<string, string | number>) => {
      const messages = (koKR as unknown as Record<string, Record<string, string>>)[namespace];
      let template = messages?.[key] ?? `[${namespace}.${key}]`;
      if (vars) {
         
        for (const [k, v] of Object.entries(vars)) {
          template = template.replace(`{${k}}`, String(v));
        }
      }
      return template;
    };
  },
}));

function makeStatus(
  statusValue: TenantDeletionStatusValue,
  options: { scheduledFor?: string | null } = {},
): DeletionStatusResponse {
  return {
    tenant_id: "00000000-0000-0000-0000-000000000001",
    status: statusValue,
    deletion_requested_at: null,
    deletion_requested_by_user_id: null,
    deletion_consent_id: null,
    deletion_scheduled_for: options.scheduledFor ?? null,
    trace_id: "trace-1",
  };
}

// Minimal alias to keep the test ergonomic
type TenantDeletionStatusValue = (typeof TenantDeletionStatus)[keyof typeof TenantDeletionStatus];

describe("DeletionStatusPanel component (Story 12.3)", () => {
  const baseProps = { accessToken: "test-token" };

  it("renders the panel title in Korean", () => {
    render(
      <DeletionStatusPanel
        initialStatus={makeStatus(TenantDeletionStatus.ACTIVE)}
        {...baseProps}
      />,
    );
    // ko-KR.json: account_deletion.panel_title = "계정 해지 상태"
    expect(screen.getByText("계정 해지 상태")).toBeInTheDocument();
  });

  it("ACTIVE status shows 활성 label + [계정 삭제하기] button", () => {
    render(
      <DeletionStatusPanel
        initialStatus={makeStatus(TenantDeletionStatus.ACTIVE)}
        {...baseProps}
      />,
    );
    expect(screen.getByText("활성")).toBeInTheDocument();
    // ko-KR.json: account_deletion.start_deletion = "계정 삭제하기"
    expect(
      screen.getByRole("button", { name: "계정 삭제하기" }),
    ).toBeInTheDocument();
  });

  it("PENDING_DELETION status shows 삭제 대기 + days remaining + [취소하기]", () => {
    // 30일 후 = 2026-09-14T10:00:00Z (from 2026-08-15T10:00:00Z base)
    const scheduledFor = "2099-01-01T00:00:00Z"; // Far future — many days remaining
    render(
      <DeletionStatusPanel
        initialStatus={makeStatus(TenantDeletionStatus.PENDING_DELETION, {
          scheduledFor,
        })}
        {...baseProps}
      />,
    );
    expect(screen.getByText("삭제 대기")).toBeInTheDocument();
    // ko-KR.json: account_deletion.days_remaining = "완전 삭제까지 {days}일 남음"
    expect(screen.getByText(/완전 삭제까지 \d+일 남음/)).toBeInTheDocument();
    // ko-KR.json: account_deletion.cancel_deletion = "취소하기"
    expect(
      screen.getByRole("button", { name: "취소하기" }),
    ).toBeInTheDocument();
  });

  it("DELETED status (initialStatus=null) shows terminal message", () => {
    render(
      <DeletionStatusPanel
        initialStatus={null}
        {...baseProps}
      />,
    );
    // ko-KR.json: account_deletion.status_deleted = "계정이 완전히 삭제되었습니다 (5년 감사 보존 후 영구 폐기)."
    expect(
      screen.getByText(/계정이 완전히 삭제되었습니다/),
    ).toBeInTheDocument();
  });

  it("renders without access token (fail-safe — refresh just returns null)", () => {
    expect(() =>
      render(
        <DeletionStatusPanel
          initialStatus={makeStatus(TenantDeletionStatus.ACTIVE)}
          accessToken={undefined}
        />,
      ),
    ).not.toThrow();
  });

  it("pending_deletion with null scheduled_for shows label only (no days)", () => {
    render(
      <DeletionStatusPanel
        initialStatus={makeStatus(TenantDeletionStatus.PENDING_DELETION, {
          scheduledFor: null,
        })}
        {...baseProps}
      />,
    );
    expect(screen.getByText("삭제 대기")).toBeInTheDocument();
    // No "완전 삭제까지" text — daysLeft is null
    expect(screen.queryByText(/완전 삭제까지/)).toBeNull();
  });
});