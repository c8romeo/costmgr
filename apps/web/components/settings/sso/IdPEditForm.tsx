/**
 * apps/web/components/settings/sso/IdPEditForm.tsx — Epic 16 T4 (AC #7.4)
 *
 * Tenant IdP config full-replace edit form (PUT /api/v1/admin/tenant/{slug}/idp).
 *
 * Pre-fills direct fields from the existing `IdPConfig`. NOTE: the
 * backend returns the SHA-256 fingerprint only (NFR4 PII minimization)
 * — we therefore render a "재입력 필요" notice for the cert field and
 * require the operator to paste the full PEM cert again on every
 * update.
 *
 * Korean SSOT: apps/web/messages/ko-KR.json::settings_sso.
 *
 * CR 11-4 D-005 (unknown state reject) — submit button is disabled
 * until all 3 required direct fields are valid.
 */

"use client";

import { useTranslations } from "next-intl";
import * as React from "react";

import type { IdPConfig, IdPCreateRequest } from "@/lib/auth/admin-idp-client";

export interface IdPEditFormProps {
  config: IdPConfig;
  loading: boolean;
  onCancel: () => void;
  onSubmit: (body: IdPCreateRequest) => Promise<boolean>;
}

export function IdPEditForm(props: IdPEditFormProps): React.ReactElement {
  const t = useTranslations("settings_sso");
  const c = props.config;

  const [idpEntityId, setIdpEntityId] = React.useState(c.idp_entity_id);
  const [idpSsoUrl, setIdpSsoUrl] = React.useState(c.idp_sso_url);
  const [idpX509CertPem, setIdpX509CertPem] = React.useState("");
  const [idpSloUrl, setIdpSloUrl] = React.useState(c.idp_slo_url ?? "");
  const [acsUrl, setAcsUrl] = React.useState(c.acs_url);
  const [nameIdFormat, setNameIdFormat] = React.useState(c.name_id_format ?? "");
  const [enabled, setEnabled] = React.useState(c.enabled);

  const submitEnabled =
    !props.loading &&
    idpEntityId.trim().length > 0 &&
    idpSsoUrl.trim().length > 0 &&
    idpX509CertPem.trim().length > 0;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!submitEnabled) return;
    const body: IdPCreateRequest = {
      idp_entity_id: idpEntityId.trim(),
      idp_sso_url: idpSsoUrl.trim(),
      idp_x509_cert_pem: idpX509CertPem.trim(),
      idp_slo_url: idpSloUrl.trim() || null,
      acs_url: acsUrl.trim() || null,
      name_id_format: nameIdFormat.trim() || null,
      enabled,
    };
    await props.onSubmit(body);
  };

  return (
    <form
      data-testid="idp-edit-form"
      className="space-y-4 rounded-lg border border-slate-200 bg-white p-6"
      onSubmit={handleSubmit}
    >
      <header className="space-y-2">
        <h2 className="text-lg font-semibold text-slate-900">
          {t("edit_title")}
        </h2>
        <p className="text-sm text-slate-600">{t("edit_subtitle")}</p>
        <div
          data-testid="idp-edit-cert-notice"
          className="rounded-md border border-yellow-300 bg-yellow-50 p-3 text-xs text-yellow-800"
        >
          <p>
            <strong>{t("current_fingerprint_label")}:</strong>{" "}
            <span className="font-mono">{c.idp_x509_cert_sha256}</span>
          </p>
          <p className="mt-1">{t("cert_reenter_notice")}</p>
        </div>
      </header>

      <div className="space-y-3">
        <div>
          <label
            htmlFor="idp-edit-entity-id"
            className="block text-sm font-medium text-slate-700"
          >
            {t("field_entity_id")}
          </label>
          <input
            id="idp-edit-entity-id"
            data-testid="idp-edit-entity-id"
            type="text"
            className="mt-1 block w-full rounded-md border border-slate-300 p-2 text-sm"
            value={idpEntityId}
            onChange={(e) => setIdpEntityId(e.target.value)}
            required
          />
        </div>
        <div>
          <label
            htmlFor="idp-edit-sso-url"
            className="block text-sm font-medium text-slate-700"
          >
            {t("field_sso_url")}
          </label>
          <input
            id="idp-edit-sso-url"
            data-testid="idp-edit-sso-url"
            type="url"
            className="mt-1 block w-full rounded-md border border-slate-300 p-2 text-sm"
            value={idpSsoUrl}
            onChange={(e) => setIdpSsoUrl(e.target.value)}
            required
          />
        </div>
        <div>
          <label
            htmlFor="idp-edit-x509-cert"
            className="block text-sm font-medium text-slate-700"
          >
            {t("field_x509_cert_pem")} ({t("required_on_update")})
          </label>
          <textarea
            id="idp-edit-x509-cert"
            data-testid="idp-edit-x509-cert"
            className="mt-1 block w-full rounded-md border border-slate-300 p-2 font-mono text-xs"
            rows={6}
            value={idpX509CertPem}
            onChange={(e) => setIdpX509CertPem(e.target.value)}
            placeholder="-----BEGIN CERTIFICATE-----&#10;...&#10;-----END CERTIFICATE-----"
            required
          />
        </div>
        <div>
          <label
            htmlFor="idp-edit-slo-url"
            className="block text-sm font-medium text-slate-700"
          >
            {t("field_slo_url")} ({t("optional")})
          </label>
          <input
            id="idp-edit-slo-url"
            data-testid="idp-edit-slo-url"
            type="url"
            className="mt-1 block w-full rounded-md border border-slate-300 p-2 text-sm"
            value={idpSloUrl}
            onChange={(e) => setIdpSloUrl(e.target.value)}
          />
        </div>
        <div>
          <label
            htmlFor="idp-edit-acs-url"
            className="block text-sm font-medium text-slate-700"
          >
            {t("field_acs_url")} ({t("optional")})
          </label>
          <input
            id="idp-edit-acs-url"
            data-testid="idp-edit-acs-url"
            type="url"
            className="mt-1 block w-full rounded-md border border-slate-300 p-2 text-sm"
            value={acsUrl}
            onChange={(e) => setAcsUrl(e.target.value)}
          />
        </div>
        <div>
          <label
            htmlFor="idp-edit-name-id"
            className="block text-sm font-medium text-slate-700"
          >
            {t("field_name_id")} ({t("optional")})
          </label>
          <input
            id="idp-edit-name-id"
            data-testid="idp-edit-name-id"
            type="text"
            className="mt-1 block w-full rounded-md border border-slate-300 p-2 text-sm"
            value={nameIdFormat}
            onChange={(e) => setNameIdFormat(e.target.value)}
          />
        </div>
      </div>

      <div className="flex items-center gap-2">
        <input
          id="idp-edit-enabled"
          data-testid="idp-edit-enabled"
          type="checkbox"
          checked={enabled}
          onChange={(e) => setEnabled(e.target.checked)}
        />
        <label htmlFor="idp-edit-enabled" className="text-sm text-slate-700">
          {t("field_enabled")}
        </label>
      </div>

      <div className="flex gap-2 border-t border-slate-200 pt-4">
        <button
          type="submit"
          data-testid="idp-edit-submit-button"
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={!submitEnabled}
        >
          {props.loading ? t("submitting") : t("edit_button")}
        </button>
        <button
          type="button"
          data-testid="idp-edit-cancel-button"
          className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          onClick={props.onCancel}
          disabled={props.loading}
        >
          {t("cancel_button")}
        </button>
      </div>
    </form>
  );
}
