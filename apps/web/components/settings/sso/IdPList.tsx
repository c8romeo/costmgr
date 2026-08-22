/**
 * apps/web/components/settings/sso/IdPList.tsx — Epic 16 T4 (AC #7.4)
 *
 * Renders the current tenant's IdP config (0 or 1 row) plus action
 * buttons (create / edit / test / delete).
 *
 * Korean SSOT: apps/web/messages/ko-KR.json::settings_sso.
 *
 * CR 11-4 D-005 (unknown state reject) — when `config` is null we
 * render the empty-state CTA. The owner-only delete button is
 * visually distinct (red) and requires explicit confirmation via
 * the confirm() dialog before invoking the onDelete handler.
 */

"use client";

import * as React from "react";
import { useTranslations } from "next-intl";

import type { IdPConfig } from "@/lib/auth/admin-idp-client";

export interface IdPListProps {
  config: IdPConfig | null;
  loading: boolean;
  onCreate: () => void;
  onEdit: () => void;
  onTest: () => void;
  onDelete: () => Promise<boolean>;
}

export function IdPList(props: IdPListProps): React.ReactElement {
  const t = useTranslations("settings_sso");
  const [confirming, setConfirming] = React.useState(false);

  if (props.config === null) {
    return (
      <section
        data-testid="idp-list-empty"
        className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-6 text-center"
      >
        <p className="mb-4 text-sm text-slate-600">{t("empty_message")}</p>
        <button
          type="button"
          data-testid="idp-list-empty-create-button"
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={props.loading}
          onClick={props.onCreate}
        >
          {t("create_button")}
        </button>
      </section>
    );
  }

  const c = props.config;
  return (
    <section
      data-testid="idp-list-configured"
      className="space-y-4 rounded-lg border border-slate-200 bg-white p-6"
    >
      <header className="flex items-start justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">
            {t("configured_title")}
          </h2>
          <p className="text-sm text-slate-600">
            {c.enabled ? t("status_enabled") : t("status_disabled")}
          </p>
        </div>
        <span
          data-testid="idp-list-status-badge"
          className={
            c.enabled
              ? "rounded-full bg-green-100 px-2 py-1 text-xs font-medium text-green-800"
              : "rounded-full bg-slate-200 px-2 py-1 text-xs font-medium text-slate-700"
          }
        >
          {c.enabled ? t("status_enabled") : t("status_disabled")}
        </span>
      </header>

      <dl className="grid grid-cols-1 gap-3 text-sm md:grid-cols-2">
        <div>
          <dt className="font-medium text-slate-500">{t("field_entity_id")}</dt>
          <dd className="break-all text-slate-900">{c.idp_entity_id}</dd>
        </div>
        <div>
          <dt className="font-medium text-slate-500">{t("field_sso_url")}</dt>
          <dd className="break-all text-slate-900">{c.idp_sso_url}</dd>
        </div>
        <div>
          <dt className="font-medium text-slate-500">{t("field_slo_url")}</dt>
          <dd className="break-all text-slate-900">
            {c.idp_slo_url ?? t("not_set")}
          </dd>
        </div>
        <div>
          <dt className="font-medium text-slate-500">{t("field_cert_sha256")}</dt>
          <dd className="break-all font-mono text-xs text-slate-700">
            {c.idp_x509_cert_sha256}
          </dd>
        </div>
        <div>
          <dt className="font-medium text-slate-500">{t("field_acs_url")}</dt>
          <dd className="break-all text-slate-900">{c.acs_url}</dd>
        </div>
        <div>
          <dt className="font-medium text-slate-500">{t("field_name_id")}</dt>
          <dd className="break-all text-slate-900">
            {c.name_id_format ?? t("not_set")}
          </dd>
        </div>
      </dl>

      <div className="flex flex-wrap gap-2 border-t border-slate-200 pt-4">
        <button
          type="button"
          data-testid="idp-list-edit-button"
          className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={props.loading}
          onClick={props.onEdit}
        >
          {t("edit_button")}
        </button>
        <button
          type="button"
          data-testid="idp-list-test-button"
          className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={props.loading}
          onClick={props.onTest}
        >
          {t("test_button")}
        </button>
        {confirming ? (
          <>
            <button
              type="button"
              data-testid="idp-list-delete-confirm-button"
              className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={props.loading}
              onClick={async () => {
                await props.onDelete();
                setConfirming(false);
              }}
            >
              {t("delete_confirm_button")}
            </button>
            <button
              type="button"
              data-testid="idp-list-delete-cancel-button"
              className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
              onClick={() => setConfirming(false)}
            >
              {t("cancel_button")}
            </button>
          </>
        ) : (
          <button
            type="button"
            data-testid="idp-list-delete-button"
            className="rounded-md border border-red-300 bg-white px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={props.loading}
            onClick={() => setConfirming(true)}
          >
            {t("delete_button")}
          </button>
        )}
      </div>
    </section>
  );
}
