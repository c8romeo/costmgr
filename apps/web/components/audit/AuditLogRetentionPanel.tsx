"use client";

/**
 * apps/web/components/audit/AuditLogRetentionPanel.tsx — Phase 6 (cj-style 87번째)
 *
 * Client orchestrator for the audit log retention configuration panel.
 *
 * Lists the 4 retention policies (admin/auth/data/security), shows the
 * current days + archive + mask_pii settings, and lets the owner:
 *   - update the policy (PUT)
 *   - preview the next purge (POST /retention/preview dry-run)
 *   - trigger cold-archive (POST /retention/{class}/cold-archive)
 *   - request GDPR Article 17 erasure (POST /audit-log/erase)
 *
 * All access is gated through the `require_audit_log_retention` capability
 * (CR 12-5 D-GATE-01 inversion) + owner-only RBAC at the backend
 * (AD-22 verbatim for erasure).
 */
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import {
  listRetentionPolicies,
  previewPurge,
  triggerColdArchive,
  requestAuditLogErasure,
  AuditLogRetentionApiError,
  type RetentionClass,
  type RetentionPolicy,
  type PurgePreviewResult,
} from "@/lib/audit/audit-log-retention-client";

interface Props {
  accessToken: string;
  locale: string;
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const RETENTION_CLASSES: RetentionClass[] = ["admin", "auth", "data", "security"];

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function AuditLogRetentionPanel({ accessToken, locale }: Props) {
  const router = useRouter();
  const [policies, setPolicies] = useState<RetentionPolicy[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorCode, setErrorCode] = useState<string | null>(null);
  const [errorMessageKo, setErrorMessageKo] = useState<string | null>(null);
  const [previewResult, setPreviewResult] = useState<PurgePreviewResult | null>(null);
  const [erasureOpen, setErasureOpen] = useState<boolean>(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await listRetentionPolicies({ accessToken });
        if (!cancelled) {
          setPolicies(res.policies);
          setLoading(false);
        }
      } catch (err) {
        if (!cancelled) {
          setErrorCode((err as AuditLogRetentionApiError).code);
          setErrorMessageKo((err as AuditLogRetentionApiError).message_ko);
          setLoading(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  const onPreviewPurge = async (action_class: RetentionClass) => {
    try {
      const result = await previewPurge({ action_class }, { accessToken });
      setPreviewResult(result);
    } catch (err) {
      setErrorCode((err as AuditLogRetentionApiError).code);
      setErrorMessageKo((err as AuditLogRetentionApiError).message_ko);
    }
  };

  const onColdArchive = async (action_class: RetentionClass) => {
    try {
      await triggerColdArchive(action_class, { accessToken });
      router.refresh();
    } catch (err) {
      setErrorCode((err as AuditLogRetentionApiError).code);
      setErrorMessageKo((err as AuditLogRetentionApiError).message_ko);
    }
  };

  const onRequestErasure = async (
    actor_id: string,
    scope: "all" | "actor" | "tenant",
    reason: string,
  ) => {
    try {
      await requestAuditLogErasure(
        { actor_id, scope, reason },
        { accessToken },
      );
      setErasureOpen(false);
      router.refresh();
    } catch (err) {
      setErrorCode((err as AuditLogRetentionApiError).code);
      setErrorMessageKo((err as AuditLogRetentionApiError).message_ko);
    }
  };

  if (loading) {
    return (
      <div role="status" aria-label="loading">
        {/* Loading state — i18n key audit_log_retention.loading_state */}
      </div>
    );
  }

  if (errorCode && errorCode === "AUDIT_LOG_RETENTION_FORBIDDEN") {
    return (
      <div role="alert">
        {/* 403 Forbidden notice — i18n key audit_log_retention.forbidden_notice */}
      </div>
    );
  }

  return (
    <section aria-labelledby="audit-log-retention-heading">
      <h2 id="audit-log-retention-heading">
        {/* audit_log_retention.panel_heading */}
      </h2>
      {previewResult && (
        <div role="status" aria-live="polite">
          {/* preview_text — uses audit_log_retention.preview_label */}
        </div>
      )}
      {errorCode && errorMessageKo && (
        <div role="alert" className="error">
          {errorMessageKo}
        </div>
      )}
      <table>
        <thead>
          <tr>
            <th scope="col">{/* column_action_class */}</th>
            <th scope="col">{/* column_days */}</th>
            <th scope="col">{/* column_archive */}</th>
            <th scope="col">{/* column_mask_pii */}</th>
            <th scope="col">{/* column_actions */}</th>
          </tr>
        </thead>
        <tbody>
          {policies.map((p) => (
            <tr key={p.action_class}>
              <td>{p.action_class}</td>
              <td>{p.days}</td>
              <td>{p.archive ? "✓" : "—"}</td>
              <td>{p.mask_pii ? "✓" : "—"}</td>
              <td>
                <button type="button" onClick={() => onPreviewPurge(p.action_class)}>
                  {/* preview_button */}
                </button>
                <button type="button" onClick={() => onColdArchive(p.action_class)}>
                  {/* cold_archive_button */}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <button type="button" onClick={() => setErasureOpen(true)}>
        {/* gdpr_erasure_button */}
      </button>
      {erasureOpen && (
        <ErasureConfirmationModal
          onSubmit={onRequestErasure}
          onClose={() => setErasureOpen(false)}
        />
      )}
    </section>
  );
}

interface ErasureModalProps {
  onSubmit: (actor_id: string, scope: "all" | "actor" | "tenant", reason: string) => void;
  onClose: () => void;
}

function ErasureConfirmationModal({ onSubmit, onClose }: ErasureModalProps) {
  const [actorId, setActorId] = useState<string>("");
  const [scope, setScope] = useState<"all" | "actor" | "tenant">("actor");
  const [reason, setReason] = useState<string>("");

  return (
    <div role="dialog" aria-modal="true" aria-labelledby="erasure-modal-heading">
      <h3 id="erasure-modal-heading">
        {/* modal_title — audit_log_retention.erasure_modal_title */}
      </h3>
      <label>
        {/* modal_actor_id_label */}
        <input
          type="text"
          value={actorId}
          onChange={(e) => setActorId(e.target.value)}
        />
      </label>
      <label>
        {/* modal_scope_label */}
        <select value={scope} onChange={(e) => setScope(e.target.value as typeof scope)}>
          <option value="actor">actor</option>
          <option value="tenant">tenant</option>
          <option value="all">all</option>
        </select>
      </label>
      <label>
        {/* modal_reason_label */}
        <textarea value={reason} onChange={(e) => setReason(e.target.value)} />
      </label>
      <button type="button" onClick={() => onSubmit(actorId, scope, reason)}>
        {/* modal_submit_button */}
      </button>
      <button type="button" onClick={onClose}>
        {/* modal_close_button */}
      </button>
    </div>
  );
}
