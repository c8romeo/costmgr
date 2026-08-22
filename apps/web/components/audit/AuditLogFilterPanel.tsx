"use client";

/**
 * apps/web/components/audit/AuditLogFilterPanel.tsx — Epic 17 T2 (AC #2.2)
 *
 * Filter form for the audit log viewer.
 *
 * Provides 7 filter fields (actor_id, action, action_class,
 * resource_type, start_date, end_date, trace_id) with an Apply button
 * that bubbles the current filter snapshot up to the parent
 * AuditLogPanel via `onApply`. The parent owns the refetch logic;
 * this component is presentational + collect-the-state.
 *
 * Per PRD §F21.2 + AD-32 (b): filters map 1:1 to the backend
 * AuditLogQueryFilters TypedDict (CR 12-5 D-PARITY-01 inversion).
 */

import { useState } from "react";
import { useTranslations } from "next-intl";

import type { AuditLogQueryFilters } from "@/lib/audit/audit-log-client";

interface AuditLogFilterPanelProps {
  filters: AuditLogQueryFilters;
  onApply: (next: AuditLogQueryFilters) => void;
  onReset: () => void;
}

interface DraftFilters {
  actor_id: string;
  action: string;
  action_class: string;
  resource_type: string;
  resource_id: string;
  start_date: string;
  end_date: string;
  trace_id: string;
}

function toDraft(filters: AuditLogQueryFilters): DraftFilters {
  return {
    actor_id: filters.actor_id ?? "",
    action: filters.action ?? "",
    action_class: filters.action_class ?? "",
    resource_type: filters.resource_type ?? "",
    resource_id: filters.resource_id ?? "",
    start_date: filters.start_date ?? "",
    end_date: filters.end_date ?? "",
    trace_id: filters.trace_id ?? "",
  };
}

function toFilters(draft: DraftFilters): AuditLogQueryFilters {
  const trim = (s: string): string | null => (s.trim() === "" ? null : s.trim());
  return {
    actor_id: trim(draft.actor_id),
    action: trim(draft.action),
    action_class: trim(draft.action_class),
    resource_type: trim(draft.resource_type),
    resource_id: trim(draft.resource_id),
    start_date: trim(draft.start_date),
    end_date: trim(draft.end_date),
    trace_id: trim(draft.trace_id),
  };
}

export function AuditLogFilterPanel({
  filters,
  onApply,
  onReset,
}: AuditLogFilterPanelProps): React.ReactElement {
  const t = useTranslations("audit_log");
  const [draft, setDraft] = useState<DraftFilters>(toDraft(filters));

  const handleApply = () => {
    onApply(toFilters(draft));
  };

  return (
    <section
      data-testid="audit-log-filter-panel"
      aria-label={t("filter_panel_title")}
      style={{
        border: "1px solid var(--border)",
        borderRadius: 8,
        padding: "1rem",
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
        gap: "0.75rem",
      }}
    >
      <label>
        <span style={{ display: "block", fontSize: "0.85rem" }}>
          {t("filter_actor_label")}
        </span>
        <input
          data-testid="audit-log-filter-actor"
          type="text"
          value={draft.actor_id}
          onChange={(e) =>
            setDraft((d) => ({ ...d, actor_id: e.target.value }))
          }
        />
      </label>
      <label>
        <span style={{ display: "block", fontSize: "0.85rem" }}>
          {t("filter_action_label")}
        </span>
        <input
          data-testid="audit-log-filter-action"
          type="text"
          value={draft.action}
          onChange={(e) => setDraft((d) => ({ ...d, action: e.target.value }))}
        />
      </label>
      <label>
        <span style={{ display: "block", fontSize: "0.85rem" }}>
          {t("filter_action_class_label")}
        </span>
        <input
          data-testid="audit-log-filter-action-class"
          type="text"
          value={draft.action_class}
          onChange={(e) =>
            setDraft((d) => ({ ...d, action_class: e.target.value }))
          }
        />
      </label>
      <label>
        <span style={{ display: "block", fontSize: "0.85rem" }}>
          {t("filter_resource_type_label")}
        </span>
        <input
          data-testid="audit-log-filter-resource-type"
          type="text"
          value={draft.resource_type}
          onChange={(e) =>
            setDraft((d) => ({ ...d, resource_type: e.target.value }))
          }
        />
      </label>
      <label>
        <span style={{ display: "block", fontSize: "0.85rem" }}>
          {t("filter_resource_id_label")}
        </span>
        <input
          data-testid="audit-log-filter-resource-id"
          type="text"
          value={draft.resource_id}
          onChange={(e) =>
            setDraft((d) => ({ ...d, resource_id: e.target.value }))
          }
        />
      </label>
      <label>
        <span style={{ display: "block", fontSize: "0.85rem" }}>
          {t("filter_start_date_label")}
        </span>
        <input
          data-testid="audit-log-filter-start-date"
          type="date"
          value={draft.start_date}
          onChange={(e) =>
            setDraft((d) => ({ ...d, start_date: e.target.value }))
          }
        />
      </label>
      <label>
        <span style={{ display: "block", fontSize: "0.85rem" }}>
          {t("filter_end_date_label")}
        </span>
        <input
          data-testid="audit-log-filter-end-date"
          type="date"
          value={draft.end_date}
          onChange={(e) =>
            setDraft((d) => ({ ...d, end_date: e.target.value }))
          }
        />
      </label>
      <label>
        <span style={{ display: "block", fontSize: "0.85rem" }}>
          {t("filter_trace_id_label")}
        </span>
        <input
          data-testid="audit-log-filter-trace-id"
          type="text"
          value={draft.trace_id}
          onChange={(e) =>
            setDraft((d) => ({ ...d, trace_id: e.target.value }))
          }
        />
      </label>
      <div
        style={{
          gridColumn: "1 / -1",
          display: "flex",
          gap: "0.5rem",
          justifyContent: "flex-end",
        }}
      >
        <button
          data-testid="audit-log-filter-reset"
          type="button"
          onClick={onReset}
        >
          {t("filter_reset_button")}
        </button>
        <button
          data-testid="audit-log-filter-apply"
          type="button"
          onClick={handleApply}
        >
          {t("filter_apply_button")}
        </button>
      </div>
    </section>
  );
}
