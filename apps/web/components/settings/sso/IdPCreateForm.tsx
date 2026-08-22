/**
 * apps/web/components/settings/sso/IdPCreateForm.tsx — Epic 16 T4 (AC #7.4)
 *
 * Tenant IdP config create form (POST /api/v1/admin/tenant/{slug}/idp).
 *
 * Two input modes (mutually exclusive):
 *   1. metadata_xml — paste full SAML EntityDescriptor XML; backend
 *      runs 8-step validator (PRD §F19.2).
 *   2. Direct fields — idp_entity_id + idp_sso_url + idp_x509_cert_pem
 *      (+ optional idp_slo_url, acs_url, name_id_format).
 *
 * Korean SSOT: apps/web/messages/ko-KR.json::settings_sso.
 *
 * CR 11-4 D-005 (unknown state reject) — at least one of the two
 * modes must be valid before submission; the submit button is
 * disabled until required fields are present.
 */

"use client";

import * as React from "react";
import { useTranslations } from "next-intl";

import type { IdPCreateRequest } from "@/lib/auth/admin-idp-client";

export interface IdPCreateFormProps {
  loading: boolean;
  onCancel: () => void;
  onSubmit: (body: IdPCreateRequest) => Promise<boolean>;
}

export function IdPCreateForm(
  props: IdPCreateFormProps,
): React.ReactElement {
  const t = useTranslations("settings_sso");

  const [mode, setMode] = React.useState<"xml" | "direct">("xml");
  const [metadataXml, setMetadataXml] = React.useState("");
  const [idpEntityId, setIdpEntityId] = React.useState("");
  const [idpSsoUrl, setIdpSsoUrl] = React.useState("");
  const [idpX509CertPem, setIdpX509CertPem] = React.useState("");
  const [idpSloUrl, setIdpSloUrl] = React.useState("");
  const [acsUrl, setAcsUrl] = React.useState("");
  const [nameIdFormat, setNameIdFormat] = React.useState("");
  const [enabled, setEnabled] = React.useState(true);

  const xmlValid = metadataXml.trim().length > 0;
  const directValid =
    idpEntityId.trim().length > 0 &&
    idpSsoUrl.trim().length > 0 &&
    idpX509CertPem.trim().length > 0;
  const submitEnabled =
    !props.loading && (mode === "xml" ? xmlValid : directValid);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!submitEnabled) return;
    const body: IdPCreateRequest =
      mode === "xml"
        ? { metadata_xml: metadataXml.trim(), enabled }
        : {
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
      data-testid="idp-create-form"
      className="space-y-4 rounded-lg border border-slate-200 bg-white p-6"
      onSubmit={handleSubmit}
    >
      <header className="space-y-2">
        <h2 className="text-lg font-semibold text-slate-900">
          {t("create_title")}
        </h2>
        <p className="text-sm text-slate-600">{t("create_subtitle")}</p>
      </header>

      <div
        data-testid="idp-create-mode-toggle"
        className="flex gap-2 rounded-md border border-slate-200 p-1"
      >
        <button
          type="button"
          data-testid="idp-create-mode-xml"
          aria-pressed={mode === "xml"}
          className={
            mode === "xml"
              ? "flex-1 rounded bg-blue-600 px-3 py-2 text-sm font-medium text-white"
              : "flex-1 rounded px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          }
          onClick={() => setMode("xml")}
        >
          {t("mode_xml")}
        </button>
        <button
          type="button"
          data-testid="idp-create-mode-direct"
          aria-pressed={mode === "direct"}
          className={
            mode === "direct"
              ? "flex-1 rounded bg-blue-600 px-3 py-2 text-sm font-medium text-white"
              : "flex-1 rounded px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          }
          onClick={() => setMode("direct")}
        >
          {t("mode_direct")}
        </button>
      </div>

      {mode === "xml" ? (
        <div>
          <label
            htmlFor="idp-create-metadata-xml"
            className="block text-sm font-medium text-slate-700"
          >
            {t("field_metadata_xml")}
          </label>
          <textarea
            id="idp-create-metadata-xml"
            data-testid="idp-create-metadata-xml"
            className="mt-1 block w-full rounded-md border border-slate-300 p-2 font-mono text-xs"
            rows={10}
            value={metadataXml}
            onChange={(e) => setMetadataXml(e.target.value)}
            placeholder='<EntityDescriptor xmlns="urn:oasis:names:tc:SAML:2.0:metadata" ...>'
            required
          />
        </div>
      ) : (
        <div className="space-y-3">
          <div>
            <label
              htmlFor="idp-create-entity-id"
              className="block text-sm font-medium text-slate-700"
            >
              {t("field_entity_id")}
            </label>
            <input
              id="idp-create-entity-id"
              data-testid="idp-create-entity-id"
              type="text"
              className="mt-1 block w-full rounded-md border border-slate-300 p-2 text-sm"
              value={idpEntityId}
              onChange={(e) => setIdpEntityId(e.target.value)}
              required
            />
          </div>
          <div>
            <label
              htmlFor="idp-create-sso-url"
              className="block text-sm font-medium text-slate-700"
            >
              {t("field_sso_url")}
            </label>
            <input
              id="idp-create-sso-url"
              data-testid="idp-create-sso-url"
              type="url"
              className="mt-1 block w-full rounded-md border border-slate-300 p-2 text-sm"
              value={idpSsoUrl}
              onChange={(e) => setIdpSsoUrl(e.target.value)}
              required
            />
          </div>
          <div>
            <label
              htmlFor="idp-create-x509-cert"
              className="block text-sm font-medium text-slate-700"
            >
              {t("field_x509_cert_pem")}
            </label>
            <textarea
              id="idp-create-x509-cert"
              data-testid="idp-create-x509-cert"
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
              htmlFor="idp-create-slo-url"
              className="block text-sm font-medium text-slate-700"
            >
              {t("field_slo_url")} ({t("optional")})
            </label>
            <input
              id="idp-create-slo-url"
              data-testid="idp-create-slo-url"
              type="url"
              className="mt-1 block w-full rounded-md border border-slate-300 p-2 text-sm"
              value={idpSloUrl}
              onChange={(e) => setIdpSloUrl(e.target.value)}
            />
          </div>
          <div>
            <label
              htmlFor="idp-create-acs-url"
              className="block text-sm font-medium text-slate-700"
            >
              {t("field_acs_url")} ({t("optional")})
            </label>
            <input
              id="idp-create-acs-url"
              data-testid="idp-create-acs-url"
              type="url"
              className="mt-1 block w-full rounded-md border border-slate-300 p-2 text-sm"
              value={acsUrl}
              onChange={(e) => setAcsUrl(e.target.value)}
            />
          </div>
          <div>
            <label
              htmlFor="idp-create-name-id"
              className="block text-sm font-medium text-slate-700"
            >
              {t("field_name_id")} ({t("optional")})
            </label>
            <input
              id="idp-create-name-id"
              data-testid="idp-create-name-id"
              type="text"
              className="mt-1 block w-full rounded-md border border-slate-300 p-2 text-sm"
              value={nameIdFormat}
              onChange={(e) => setNameIdFormat(e.target.value)}
            />
          </div>
        </div>
      )}

      <div className="flex items-center gap-2">
        <input
          id="idp-create-enabled"
          data-testid="idp-create-enabled"
          type="checkbox"
          checked={enabled}
          onChange={(e) => setEnabled(e.target.checked)}
        />
        <label htmlFor="idp-create-enabled" className="text-sm text-slate-700">
          {t("field_enabled")}
        </label>
      </div>

      <div className="flex gap-2 border-t border-slate-200 pt-4">
        <button
          type="submit"
          data-testid="idp-create-submit-button"
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={!submitEnabled}
        >
          {props.loading ? t("submitting") : t("create_button")}
        </button>
        <button
          type="button"
          data-testid="idp-create-cancel-button"
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
