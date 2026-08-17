/**
 * apps/web/__tests__/components/m9-abc.AbcDispatchResultCard.test.tsx — Story 9.7
 *
 * Vitest tests for AbcDispatchResultCard (discriminated union renderer).
 *
 * Coverage (T2 A35):
 *   - Trad path rendering (4 cases) — isCalcAbcResponse returns false
 *   - ABC path rendering (8 cases) — isCalcAbcResponse returns true (via V7 badge + CCR table + breakdown table + unused table + snapshot_id)
 *
 * Total: ~12 NEW vitest cases (T2 A35 wire).
 */

import { render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it } from "vitest";

import koKR from "@/messages/ko-KR.json";

import { AbcDispatchResultCard } from "@/components/m9-abc/AbcDispatchResultCard";
import type {
  CalcAbcResponse,
  CalcResponse,
} from "@/lib/m9-abc-dispatch";

const messages = koKR;

function renderWithIntl(node: React.ReactElement): React.ReactElement {
  return (
    <NextIntlClientProvider locale="ko-KR" messages={messages}>
      {node}
    </NextIntlClientProvider>
  );
}

const tradOutcome: CalcResponse = {
  tenant_id: "00000000-0000-0000-0000-000000000001",
  period_key: "2026-08",
  baseline_revision: 1,
  material_cost: 5_000_000,
  labor_cost: 3_000_000,
  overhead_cost: 2_000_000,
  manufacturing_cost: 10_000_000,
  inventory_adjustment: 0,
  result_hash: "sha256:trad0000000000000000000000000000000000000000000000000000",
  state: "verified",
  trace_id: "trace-trad-001",
  verdict: {
    verification_status: "passed",
    verifications: [],
    top_failure: null,
    trace_id: "trace-trad-001",
  },
};

const abcOutcome: CalcAbcResponse = {
  engine_type: "abc",
  tenant_id: "00000000-0000-0000-0000-000000000001",
  period_key: "2026-08",
  baseline_revision: 1,
  allocation_outcome: {
    breakdown: [
      {
        department_id: "dept-001",
        product_id: "prod-A",
        activity_id: "act-001",
        driver_id: "drv-001",
        allocated_krw: "13200000",
      },
      {
        department_id: "dept-002",
        product_id: "prod-B",
        activity_id: "act-002",
        driver_id: "drv-002",
        allocated_krw: "13200000",
      },
    ],
    unused_capacity: {
      rows: [],
      is_balanced: true,
      delta_krw: "0",
    },
    v7_verdict: {
      is_balanced: true,
      breakdown_sum: "26400000",
      unused_cost: "0",
      expected_sum: "26400000",
      delta_krw: "0",
      hash: "sha256:v70000000000000000000000000000000000000000000000000000000",
    },
    ccr: {
      departments: [
        {
          department_id: "dept-001",
          ccr_per_hour: "33000",
          hash: "sha256:ccr000000000000000000000000000000000000000000000000000000",
        },
        {
          department_id: "dept-002",
          ccr_per_hour: "33000",
          hash: "sha256:ccr000000000000000000000000000000000000000000000000000001",
        },
      ],
    },
    is_balanced: true,
  },
  snapshot_id: "00000000-0000-0000-0000-000000000abc",
  result_hash: "sha256:abc000000000000000000000000000000000000000000000000000000",
  state: "verified",
  trace_id: "trace-abc-001",
  verdict: {
    verification_status: "passed",
    verifications: [
      {
        code: "V7",
        status: "passed",
        message_ko: "V7 무결성 통과 (1원 단위)",
        details: { is_balanced: true },
      },
    ],
    top_failure: null,
    trace_id: "trace-abc-001",
  },
};

// ── Trad path rendering (4 cases) ─────────────────────────────

describe("AbcDispatchResultCard trad path", () => {
  it("renders trad result card when outcome has no engine_type", () => {
    render(renderWithIntl(<AbcDispatchResultCard outcome={tradOutcome} />));
    expect(screen.getByTestId("abc-dispatch-result-trad")).toBeTruthy();
  });

  it("sets data-engine-type='trad' on trad result card", () => {
    render(renderWithIntl(<AbcDispatchResultCard outcome={tradOutcome} />));
    expect(
      screen
        .getByTestId("abc-dispatch-result-trad")
        .getAttribute("data-engine-type"),
    ).toBe("trad");
  });

  it("renders 4 trad cost fields (material / labor / overhead / manufacturing)", () => {
    render(renderWithIntl(<AbcDispatchResultCard outcome={tradOutcome} />));
    expect(screen.getByTestId("abc-dispatch-trad-material-cost")).toBeTruthy();
    expect(screen.getByTestId("abc-dispatch-trad-labor-cost")).toBeTruthy();
    expect(screen.getByTestId("abc-dispatch-trad-overhead-cost")).toBeTruthy();
    expect(
      screen.getByTestId("abc-dispatch-trad-manufacturing-cost"),
    ).toBeTruthy();
  });

  it("renders trad result_hash in footer", () => {
    render(renderWithIntl(<AbcDispatchResultCard outcome={tradOutcome} />));
    expect(screen.getByTestId("abc-dispatch-trad-result-hash")).toBeTruthy();
    expect(
      screen.getByTestId("abc-dispatch-trad-result-hash").textContent,
    ).toContain("sha256:trad");
  });
});

// ── ABC path rendering (8 cases) ─────────────────────────────

describe("AbcDispatchResultCard abc path", () => {
  it("renders abc result card when isCalcAbcResponse narrows true", () => {
    render(renderWithIntl(<AbcDispatchResultCard outcome={abcOutcome} />));
    expect(screen.getByTestId("abc-dispatch-result-abc")).toBeTruthy();
  });

  it("sets data-engine-type='abc' and data-snapshot-id on abc result card", () => {
    render(renderWithIntl(<AbcDispatchResultCard outcome={abcOutcome} />));
    const card = screen.getByTestId("abc-dispatch-result-abc");
    expect(card.getAttribute("data-engine-type")).toBe("abc");
    expect(card.getAttribute("data-snapshot-id")).toBe("00000000-0000-0000-0000-000000000abc");
  });

  it("renders V7 verdict badge with balanced status", () => {
    render(renderWithIntl(<AbcDispatchResultCard outcome={abcOutcome} />));
    const badge = screen.getByTestId("abc-dispatch-v7-badge");
    expect(badge.getAttribute("data-is-balanced")).toBe("true");
  });

  it("renders CCR table with 2 departments", () => {
    render(renderWithIntl(<AbcDispatchResultCard outcome={abcOutcome} />));
    const ccrTable = screen.getByTestId("abc-dispatch-ccr-table");
    expect(ccrTable).toBeTruthy();
    // 2 CCR rows + 1 header row = 3 rows in tbody/thead combined
    expect(ccrTable.querySelectorAll("tr").length).toBeGreaterThanOrEqual(3);
  });

  it("renders cost object breakdown table with 2 rows", () => {
    render(renderWithIntl(<AbcDispatchResultCard outcome={abcOutcome} />));
    const breakdown = screen.getByTestId("abc-dispatch-breakdown-table");
    expect(breakdown).toBeTruthy();
    expect(breakdown.querySelectorAll("tbody tr").length).toBe(2);
  });

  it("does NOT render unused table when unused_capacity.rows is empty", () => {
    render(renderWithIntl(<AbcDispatchResultCard outcome={abcOutcome} />));
    expect(screen.queryByTestId("abc-dispatch-unused-table")).toBeNull();
  });

  it("renders abc snapshot_id in footer", () => {
    render(renderWithIntl(<AbcDispatchResultCard outcome={abcOutcome} />));
    expect(screen.getByTestId("abc-dispatch-abc-snapshot-id").textContent).toBe(
      "00000000-0000-0000-0000-000000000abc",
    );
  });

  it("renders abc result_hash in footer", () => {
    render(renderWithIntl(<AbcDispatchResultCard outcome={abcOutcome} />));
    expect(screen.getByTestId("abc-dispatch-abc-result-hash").textContent).toBe(
      "sha256:abc000000000000000000000000000000000000000000000000000000",
    );
  });
});

// ── V7 unbalanced branch (2 cases — extra coverage) ─────────

describe("AbcDispatchResultCard V7 unbalanced", () => {
  const abcOutcomeUnbalanced: CalcAbcResponse = {
    ...abcOutcome,
    allocation_outcome: {
      ...abcOutcome.allocation_outcome,
      v7_verdict: {
        ...abcOutcome.allocation_outcome.v7_verdict,
        is_balanced: false,
        delta_krw: "1500",
      },
    },
  };

  it("renders V7 badge with data-is-balanced='false'", () => {
    render(
      renderWithIntl(
        <AbcDispatchResultCard outcome={abcOutcomeUnbalanced} />,
      ),
    );
    const badge = screen.getByTestId("abc-dispatch-v7-badge");
    expect(badge.getAttribute("data-is-balanced")).toBe("false");
  });

  it("renders delta_krw formatted with Δ prefix when unbalanced", () => {
    render(
      renderWithIntl(
        <AbcDispatchResultCard outcome={abcOutcomeUnbalanced} />,
      ),
    );
    const badge = screen.getByTestId("abc-dispatch-v7-badge");
    expect(badge.textContent).toContain("Δ");
  });
});