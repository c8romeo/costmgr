/**
 * apps/web/__tests__/components/m10-ai.AiExtractModal.test.tsx — Sprint 10.5 T1 wire (D-10-1-DEFER-3 해소)
 *
 * Vitest tests for AiExtractModal (M10 AI monthly extraction form + display).
 *
 * Coverage (T1):
 *   - Mount + idle state (1 case)
 *   - Form validation (period_key regex) (2 cases)
 *   - Submit handler → success envelope → drafts grid (2 cases)
 *   - low_confidence_warning envelope → banner shown (1 case)
 *   - error envelope → alert role shown (1 case)
 *   - Close button → unmounts (1 case)
 *   - isOpen=false → returns null (1 case)
 *   - onDraftsConfirmed callback invoked on confirm (1 case)
 *   - Loading state (1 case)
 *
 * Total: ~10 NEW vitest cases.
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it, vi, beforeAll, beforeEach } from "vitest";

import { AiExtractModal } from "@/components/m10-ai/AiExtractModal";
import { type MonthlyDraftEntry } from "@/lib/ai-extract";
import { server } from "@/mocks/server";

// jsdom doesn't fully implement FileReader — sync mock here so that
// fireEvent.change on file input immediately produces base64 payload.
beforeAll(() => {
  class MockFileReader {
    result: string = "";
    onload: ((ev: unknown) => void) | null = null;
    onerror: ((ev: unknown) => void) | null = null;
    readAsDataURL(file: File): void {
      // Encode file contents as base64 synchronously
      const buf = Buffer.from(`mock-${file.name}`);
      this.result = `data:application/octet-stream;base64,${buf.toString("base64")}`;
      // Fire synchronously (jsdom doesn't have full FileReader impl)
      if (this.onload) {
        this.onload({ target: this });
      }
    }
  }
   
  (globalThis as any).FileReader = MockFileReader;
});

beforeEach(() => {
  server.resetHandlers();
});

const sampleDrafts: MonthlyDraftEntry[] = [
  {
    field_name: "직접재료비",
    value: "1000000",
    confidence: "0.92",
    target_table: "monthly_inputs",
    evidence_page: 1,
    requires_user_confirmation: false,
  },
  {
    field_name: "기말재고",
    value: "500000",
    confidence: "0.55",
    target_table: "monthly_inputs",
    evidence_page: 3,
    requires_user_confirmation: true,
  },
];

describe("AiExtractModal — Sprint 10.5 T1", () => {
  it("returns null when isOpen=false", () => {
    const { container } = render(
      <AiExtractModal isOpen={false} onClose={(): void => {}} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("mounts dialog + idle state text when isOpen=true", () => {
    render(<AiExtractModal isOpen={true} onClose={(): void => {}} />);
    expect(screen.getByTestId("ai-extract-modal")).toBeInTheDocument();
    expect(screen.getByText(/양식을 작성하고/)).toBeInTheDocument();
  });

  it("validates period_key format — invalid → error message", async () => {
    render(<AiExtractModal isOpen={true} onClose={(): void => {}} />);
    const periodInput = screen.getByTestId("ai-extract-period-input");
    fireEvent.change(periodInput, { target: { value: "2026-7" } });
    fireEvent.click(screen.getByTestId("ai-extract-submit"));
    await waitFor(() => {
      expect(
        screen.getByText(/YYYY-MM 형식이 올바르지 않습니다/),
      ).toBeInTheDocument();
    });
  });

  it("validates period_key format — valid 2026-07 → success draft grid", async () => {
    server.use(
      http.post("/api/v1/ai/extract-monthly", () =>
        HttpResponse.json({
          status: "success",
          extraction_id: "ext-1",
          period_key: "2026-07",
          drafts: sampleDrafts,
          low_confidence_count: 0,
        }),
      ),
    );
    render(<AiExtractModal isOpen={true} onClose={(): void => {}} />);
    fireEvent.change(screen.getByTestId("ai-extract-period-input"), {
      target: { value: "2026-07" },
    });
    fireEvent.change(screen.getByTestId("ai-extract-file-input"), {
      target: { files: [new File(["x"], "doc.pdf")] },
    });
    fireEvent.click(screen.getByTestId("ai-extract-submit"));
    await waitFor(() => {
      expect(screen.getByTestId("ai-extract-drafts-list")).toBeInTheDocument();
    });
  });

  it("shows success drafts grid on success envelope", async () => {
    server.use(
      http.post("/api/v1/ai/extract-monthly", () =>
        HttpResponse.json({
          status: "success",
          extraction_id: "ext-2",
          period_key: "2026-07",
          drafts: sampleDrafts,
          low_confidence_count: 0,
        }),
      ),
    );
    render(<AiExtractModal isOpen={true} onClose={(): void => {}} />);
    fireEvent.change(screen.getByTestId("ai-extract-period-input"), {
      target: { value: "2026-07" },
    });
    fireEvent.change(screen.getByTestId("ai-extract-file-input"), {
      target: { files: [new File(["x"], "doc.pdf")] },
    });
    fireEvent.click(screen.getByTestId("ai-extract-submit"));
    await waitFor(() => {
      expect(screen.getByTestId("ai-extract-drafts-list")).toBeInTheDocument();
      const cards = screen.getAllByTestId("ai-draft-card");
      expect(cards.length).toBe(2);
    });
  });

  it("shows low_confidence_warning banner when envelope status=low_confidence_warning", async () => {
    server.use(
      http.post("/api/v1/ai/extract-monthly", () =>
        HttpResponse.json({
          status: "low_confidence_warning",
          extraction_id: "ext-3",
          period_key: "2026-07",
          drafts: sampleDrafts,
          low_confidence_count: 1,
        }),
      ),
    );
    render(<AiExtractModal isOpen={true} onClose={(): void => {}} />);
    fireEvent.change(screen.getByTestId("ai-extract-period-input"), {
      target: { value: "2026-07" },
    });
    fireEvent.change(screen.getByTestId("ai-extract-file-input"), {
      target: { files: [new File(["x"], "doc.pdf")] },
    });
    fireEvent.click(screen.getByTestId("ai-extract-submit"));
    await waitFor(() => {
      expect(screen.getByText(/신뢰도 낮은 초안 1건/)).toBeInTheDocument();
    });
  });

  it("shows error alert (role=alert) on error envelope", async () => {
    server.use(
      http.post("/api/v1/ai/extract-monthly", () =>
        HttpResponse.json(
          {
            error_code: "AI_PIPA_CONSENT_MISSING",
            message_ko: "개인정보 처리 동의가 필요합니다",
            trace_id: "tr-1",
          },
          { status: 403 },
        ),
      ),
    );
    render(<AiExtractModal isOpen={true} onClose={(): void => {}} />);
    fireEvent.change(screen.getByTestId("ai-extract-period-input"), {
      target: { value: "2026-07" },
    });
    fireEvent.change(screen.getByTestId("ai-extract-file-input"), {
      target: { files: [new File(["x"], "doc.pdf")] },
    });
    fireEvent.click(screen.getByTestId("ai-extract-submit"));
    const alert = await screen.findByTestId("ai-extract-error");
    expect(alert.getAttribute("role")).toBe("alert");
    expect(alert.textContent).toContain("AI_PIPA_CONSENT_MISSING");
  });

  it("close button → invokes onClose callback", () => {
    const onClose = vi.fn();
    render(<AiExtractModal isOpen={true} onClose={onClose} />);
    fireEvent.click(screen.getByTestId("ai-extract-modal-close"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("invokes onDraftsConfirmed when confirm button clicked after success", async () => {
    server.use(
      http.post("/api/v1/ai/extract-monthly", () =>
        HttpResponse.json({
          status: "success",
          extraction_id: "ext-4",
          period_key: "2026-07",
          drafts: sampleDrafts,
          low_confidence_count: 0,
        }),
      ),
    );
    const onDraftsConfirmed = vi.fn();
    render(
      <AiExtractModal
        isOpen={true}
        onClose={(): void => {}}
        onDraftsConfirmed={onDraftsConfirmed}
      />,
    );
    fireEvent.change(screen.getByTestId("ai-extract-period-input"), {
      target: { value: "2026-07" },
    });
    fireEvent.change(screen.getByTestId("ai-extract-file-input"), {
      target: { files: [new File(["x"], "doc.pdf")] },
    });
    fireEvent.click(screen.getByTestId("ai-extract-submit"));
    await waitFor(() => {
      expect(screen.getByTestId("ai-extract-confirm-button")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("ai-extract-confirm-button"));
    expect(onDraftsConfirmed).toHaveBeenCalledTimes(1);
    expect(onDraftsConfirmed.mock.calls[0][0].length).toBe(2);
  });

  it("shows loading state during submission", async () => {
    server.use(
      http.post("/api/v1/ai/extract-monthly", () => new Promise(() => {})),
    );
    render(<AiExtractModal isOpen={true} onClose={(): void => {}} />);
    fireEvent.change(screen.getByTestId("ai-extract-period-input"), {
      target: { value: "2026-07" },
    });
    fireEvent.change(screen.getByTestId("ai-extract-file-input"), {
      target: { files: [new File(["x"], "doc.pdf")] },
    });
    fireEvent.click(screen.getByTestId("ai-extract-submit"));
    await waitFor(() => {
      expect(screen.getByTestId("ai-extract-loading")).toBeInTheDocument();
    });
  });
});
