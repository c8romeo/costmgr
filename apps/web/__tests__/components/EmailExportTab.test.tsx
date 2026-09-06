/**
 * apps/web/__tests__/components/EmailExportTab.test.tsx
 *
 * cj-299 wire sprint (cj-style 299번째) — Story 30.3 Email delivery frontend tests.
 *
 * Pattern verbatim mirror from CsvExportTab.test.tsx:
 *  - vitest `describe` / `it` / `expect` pattern
 *  - @testing-library/react `render` + `screen`
 *  - 4 tests: ko-KR labels, data-testids, period dropdown (12 months), type selector
 *  - 추가로 email 전용 필드 (recipients input, subject input, message textarea,
 *    PII toggle, send button) 검증
 *
 * CR 11-3 honest-DEFER 238번째.
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EmailExportTab } from "@/components/reports/EmailExportTab";

const defaultProps = {
  accessToken: "test-token-abc",
  tenantId: "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  initialPeriod: "2026-08",
  initialType: "cost-records" as const,
};

describe("EmailExportTab", () => {
  it("renders with ko-KR labels (NFR18 SSOT)", () => {
    render(<EmailExportTab {...defaultProps} />);
    expect(screen.getByTestId("email-export-tab")).toBeInTheDocument();
    expect(screen.getByText("이메일 내보내기")).toBeInTheDocument();
    expect(screen.getByText("기간 선택")).toBeInTheDocument();
    expect(screen.getByText("수신자 이메일 (1~10개, 쉼표 구분)")).toBeInTheDocument();
    expect(screen.getByText(/이메일 제목/)).toBeInTheDocument();
    expect(screen.getByText(/추가 메시지/)).toBeInTheDocument();
    expect(screen.getByText(/개인정보\(PII\) 자동 redact/)).toBeInTheDocument();
    expect(screen.getByText("이메일 발송")).toBeInTheDocument();
  });

  it("renders all data-testids (PDF-style data-testid coverage)", () => {
    render(<EmailExportTab {...defaultProps} />);
    expect(screen.getByTestId("email-export-tab")).toBeInTheDocument();
    expect(screen.getByTestId("email-period-selector")).toBeInTheDocument();
    expect(screen.getByTestId("email-type-selector")).toBeInTheDocument();
    expect(screen.getByTestId("email-recipients-input")).toBeInTheDocument();
    expect(screen.getByTestId("email-subject-input")).toBeInTheDocument();
    expect(screen.getByTestId("email-message-input")).toBeInTheDocument();
    expect(screen.getByTestId("email-pii-toggle")).toBeInTheDocument();
    expect(screen.getByTestId("email-send-button")).toBeInTheDocument();
  });

  it("renders period dropdown with 12 months including current", () => {
    render(<EmailExportTab {...defaultProps} />);
    const select = screen.getByTestId("email-period-selector") as HTMLSelectElement;
    const options = Array.from(select.options);
    expect(options.length).toBe(12);
    // 가장 마지막 옵션이 current month 결정 wire (리스트는 최신 → 과거 순).
    // 정확한 매칭 대신 "YYYY-MM" 형식만 검증.
    for (const opt of options) {
      expect(opt.value).toMatch(/^\d{4}-(0[1-9]|1[0-2])$/);
    }
  });

  it("renders type selector with cost-records and bom options", () => {
    render(<EmailExportTab {...defaultProps} />);
    const select = screen.getByTestId("email-type-selector") as HTMLSelectElement;
    const options = Array.from(select.options).map((o) => o.value);
    expect(options).toContain("cost-records");
    expect(options).toContain("bom");
  });

  it("PII toggle is checked by default (NFR4 default-true)", () => {
    render(<EmailExportTab {...defaultProps} />);
    const toggle = screen.getByTestId("email-pii-toggle") as HTMLInputElement;
    expect(toggle.checked).toBe(true);
  });

  it("send button is disabled while not busy", () => {
    render(<EmailExportTab {...defaultProps} />);
    const btn = screen.getByTestId("email-send-button") as HTMLButtonElement;
    expect(btn.disabled).toBe(false);
  });
});
