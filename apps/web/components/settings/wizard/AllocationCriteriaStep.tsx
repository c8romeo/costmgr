/**
 * apps/web/components/settings/wizard/AllocationCriteriaStep.tsx
 *
 * Story 1.2 — Task 5.5. AC #3: 배부기준 3종 저장.
 * Three sub-tabs (직접/간접 계정 분류 · 고정/변동 분류 · 동인 정의).
 * Each shows the current count + a link to the M1 baseline / M9 ABC CRUD
 * pages (Epic 2 / Epic 9 full impl). The wizard itself does NOT write
 * counts — it only *reads* them.
 *
 * Industry-conditional drivers_required:
 *   - manufacturing → drivers tab is hidden (A11 — no ABC engine).
 *   - others → drivers required.
 *
 * PRD §3.A11 — CCR computation needs account tags.
 *
 * Review patches applied:
 *   F-6  — removed the "완료로 표시" shortcut button. The wizard must not
 *          allow the user to flip completion without registering real
 *          rows (Pydantic rejects count=0, so the shortcut was already
 *          broken; deleting it makes the contract explicit).
 *   F-21 — `active` tab is reset when the `completion`/`industry` change
 *          such that the previously active tab is no longer visible
 *          (e.g., industry flipped to manufacturing → "drivers" tab is
 *          hidden, switch focus to the first visible tab).
 *   F-22 — `<a href>` → `next/link` `<Link href>` (App Router navigation,
 *          preserves client-side routing + prefetch).
 *   F-31 — empty-state copy (no rows yet) is split into a dedicated
 *          message so the user knows the difference between
 *          "0 rows — go add some" and "completed".
 */

"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { type CompletionStatus } from "@/lib/api-client";
import { INDUSTRY_LABEL_KO, type Industry } from "@/lib/menu-config";

type TabKey = "direct_indirect" | "fixed_variable" | "drivers";

interface TabSpec {
  key: TabKey;
  label: string;
  description: string;
  addHref: string;
  epic: string;
}

const TABS: TabSpec[] = [
  {
    key: "direct_indirect",
    label: "직접/간접 계정 분류",
    description: "계정과목별로 직접원가/간접원가 분류를 등록하세요.",
    addHref: "/dashboard/accounts",
    epic: "2",
  },
  {
    key: "fixed_variable",
    label: "고정/변동 분류",
    description: "계정과목별로 고정비/변동비 분류를 등록하세요.",
    addHref: "/dashboard/accounts",
    epic: "2",
  },
  {
    key: "drivers",
    label: "동인 정의",
    description: "ABC 동인(실제적 조업능력 시간)을 등록하세요.",
    addHref: "/dashboard/driver",
    epic: "9",
  },
];

export interface AllocationCriteriaStepProps {
  completion: CompletionStatus | null;
  industry: string | null;
}

export function AllocationCriteriaStep({
  completion,
  industry,
}: AllocationCriteriaStepProps) {
  const driversRequired = completion?.drivers_required ?? industry !== "manufacturing";
  const visibleTabs = TABS.filter((t) => t.key !== "drivers" || driversRequired);

  // F-26: ko-KR industry label. The backend stores the enum literal
  // (`manufacturing`, `service`, …) but the wizard copy must show the
  // display name from `INDUSTRY_LABEL_KO`. Falls back to "(미설정)" when
  // the user hasn't picked yet.
  const industryLabel: string = industry
    ? (INDUSTRY_LABEL_KO[industry as Industry] ?? industry)
    : "(미설정)";

  const initialActive = visibleTabs[0]?.key ?? "direct_indirect";
  const [active, setActive] = useState<TabKey>(initialActive as TabKey);

  // F-21: reset active tab if it disappears (industry flip → drivers hidden).
  useEffect(() => {
    if (!visibleTabs.some((t) => t.key === active)) {
      setActive(initialActive as TabKey);
    }
  }, [active, initialActive, visibleTabs]);

  function countFor(tab: TabKey): number {
    if (!completion) return 0;
    if (tab === "direct_indirect") return completion.direct_indirect_count;
    if (tab === "fixed_variable") return completion.fixed_variable_count;
    return completion.drivers_count;
  }

  function isComplete(tab: TabKey): boolean {
    return countFor(tab) > 0;
  }

  return (
    <section
      aria-labelledby="wizard-allocation-heading"
      style={{
        padding: "1.25rem 1.5rem",
        border: "1px solid #e2e8f0",
        borderRadius: 8,
        background: "#fff",
        marginBottom: "1rem",
      }}
    >
      <h2
        id="wizard-allocation-heading"
        style={{ fontSize: "1.125rem", fontWeight: 700, marginBottom: "0.25rem" }}
      >
        배부기준 3종
      </h2>
      <p style={{ color: "#475569", fontSize: "0.9rem", marginBottom: "0.75rem" }}>
        업종: <strong>{industryLabel}</strong>
        {!driversRequired ? " — 제조업은 동인 정의를 건너뜁니다 (A11)" : ""}
      </p>

      <div
        role="tablist"
        aria-label="배부기준 탭"
        style={{
          display: "flex",
          gap: 4,
          borderBottom: "1px solid #e2e8f0",
          marginBottom: "0.75rem",
        }}
      >
        {visibleTabs.map((tab) => {
          const selected = tab.key === active;
          return (
            <button
              key={tab.key}
              type="button"
              role="tab"
              aria-selected={selected}
              onClick={() => setActive(tab.key)}
              style={{
                padding: "0.5rem 0.75rem",
                border: "none",
                borderBottom: selected ? "2px solid #2563eb" : "2px solid transparent",
                background: "transparent",
                color: selected ? "#1d4ed8" : "#475569",
                fontWeight: selected ? 700 : 500,
                cursor: "pointer",
              }}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {visibleTabs
        .filter((tab) => tab.key === active)
        .map((tab) => {
          const count = countFor(tab.key);
          const done = isComplete(tab.key);
          return (
            <div key={tab.key} role="tabpanel" aria-label={tab.label}>
              <p style={{ color: "#475569", marginBottom: "0.5rem" }}>{tab.description}</p>

              {/* F-31: split empty-state copy. Zero rows = "go add some";
                  >0 rows = "completed". */}
              {count === 0 ? (
                <div
                  role="status"
                  aria-live="polite"
                  style={{
                    padding: "0.75rem",
                    border: "1px dashed #b45309",
                    background: "#fef3c7",
                    borderRadius: 6,
                    marginBottom: "0.75rem",
                    color: "#7c2d12",
                    fontSize: "0.9rem",
                  }}
                >
                  아직 등록된 행이 없습니다. 아래 버튼을 눌러 한 행 이상을 등록해 주세요.
                </div>
              ) : (
                <p style={{ marginBottom: "0.75rem" }}>
                  현재 등록: <strong>{count}</strong>행{" "}
                  {done && (
                    <span style={{ color: "#15803d", fontWeight: 600 }}>✓ 완료</span>
                  )}
                </p>
              )}

              <div style={{ display: "flex", gap: 8 }}>
                {/* F-22: next/link preserves App Router semantics. */}
                <Link
                  href={tab.addHref}
                  style={{
                    padding: "0.5rem 1rem",
                    background: "#0f172a",
                    color: "#fff",
                    borderRadius: 6,
                    textDecoration: "none",
                    fontWeight: 600,
                  }}
                >
                  추가 / 편집 (Epic {tab.epic})
                </Link>
              </div>
            </div>
          );
        })}
    </section>
  );
}