/**
 * apps/web/components/settings/sso/IdPTestPanel.tsx — Epic 16 T4 (AC #7.4)
 *
 * Tenant IdP metadata 8-step validation dry-run panel
 * (POST /api/v1/admin/tenant/{slug}/idp/test).
 *
 * Operator pastes a SAML EntityDescriptor XML; the panel issues the
 * test request and renders the 8-step pass/fail list (PRD §F19.2):
 *   1. xml_well_formedness
 *   2. root_entity_descriptor
 *   3. entity_id_present
 *   4. idpsso_descriptor_present
 *   5. x509_cert_present
 *   6. sso_url_https
 *   7. slo_url_optional_https
 *   8. tenant_slug_host_match
 *
 * Korean SSOT: apps/web/messages/ko-KR.json::settings_sso.
 */

"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { toast } from "sonner";

import { testIdPConfig } from "@/lib/auth/admin-idp-client";

export interface IdPTestPanelProps {
  accessToken: string;
  tenantSlug: string;
  onCancel: () => void;
}

export function IdPTestPanel(props: IdPTestPanelProps): React.ReactElement {
  const t = useTranslations("settings_sso");

  const [metadataXml, setMetadataXml] = React.useState("");
  const [running, setRunning] = React.useState(false);
  const [result, setResult] = React.useState<{
    passed: boolean;
    steps: { step: number; name: string; passed: boolean; detail: string | null }[];
    metadata: {
      entity_id: string;
      sso_url: string;
      slo_url: string | null;
      name_id_format: string | null;
    } | null;
  } | null>(null);

  const submitEnabled = !running && metadataXml.trim().length > 0;

  const handleRun = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!submitEnabled) return;
    setRunning(true);
    try {
      const res = await testIdPConfig(
        props.accessToken,
        props.tenantSlug,
        metadataXml.trim(),
      );
      if (res.ok && res.data) {
        setResult(res.data);
        if (res.data.passed) {
          toast.success(t("toast_success_test_passed"));
        } else {
          toast.error(t("toast_error_test_failed"));
        }
      } else if (res.error) {
        toast.error(res.error.message_ko);
        setResult(null);
      }
    } catch {
      toast.error(t("toast_error_network"));
    } finally {
      setRunning(false);
    }
  };

  return (
    <form
      data-testid="idp-test-panel"
      className="space-y-4 rounded-lg border border-slate-200 bg-white p-6"
      onSubmit={handleRun}
    >
      <header className="space-y-2">
        <h2 className="text-lg font-semibold text-slate-900">
          {t("test_title")}
        </h2>
        <p className="text-sm text-slate-600">{t("test_subtitle")}</p>
      </header>

      <div>
        <label
          htmlFor="idp-test-metadata-xml"
          className="block text-sm font-medium text-slate-700"
        >
          {t("field_metadata_xml")}
        </label>
        <textarea
          id="idp-test-metadata-xml"
          data-testid="idp-test-metadata-xml"
          className="mt-1 block w-full rounded-md border border-slate-300 p-2 font-mono text-xs"
          rows={10}
          value={metadataXml}
          onChange={(e) => setMetadataXml(e.target.value)}
          placeholder='<EntityDescriptor xmlns="urn:oasis:names:tc:SAML:2.0:metadata" ...>'
          required
        />
      </div>

      <div className="flex gap-2 border-t border-slate-200 pt-4">
        <button
          type="submit"
          data-testid="idp-test-run-button"
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={!submitEnabled}
        >
          {running ? t("test_running") : t("test_button")}
        </button>
        <button
          type="button"
          data-testid="idp-test-cancel-button"
          className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          onClick={props.onCancel}
          disabled={running}
        >
          {t("cancel_button")}
        </button>
      </div>

      {result ? (
        <section
          data-testid="idp-test-result"
          className="space-y-3 border-t border-slate-200 pt-4"
        >
          <h3 className="text-sm font-semibold text-slate-700">
            {result.passed
              ? t("test_result_passed")
              : t("test_result_failed")}
          </h3>
          <ol className="space-y-2 text-sm">
            {result.steps.map((s) => (
              <li
                key={`${s.step}-${s.name}`}
                data-testid={`idp-test-step-${s.step}`}
                className="flex items-start gap-2"
              >
                <span
                  className={
                    s.passed
                      ? "rounded-full bg-green-100 px-2 py-1 text-xs font-medium text-green-800"
                      : "rounded-full bg-red-100 px-2 py-1 text-xs font-medium text-red-800"
                  }
                >
                  {s.passed ? "OK" : "FAIL"}
                </span>
                <span className="flex-1">
                  <strong>
                    {s.step}. {s.name}
                  </strong>
                  {s.detail ? (
                    <p className="text-xs text-slate-600">{s.detail}</p>
                  ) : null}
                </span>
              </li>
            ))}
          </ol>
          {result.metadata ? (
            <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-xs">
              <p>
                <strong>entity_id:</strong> {result.metadata.entity_id}
              </p>
              <p>
                <strong>sso_url:</strong> {result.metadata.sso_url}
              </p>
              <p>
                <strong>slo_url:</strong>{" "}
                {result.metadata.slo_url ?? t("not_set")}
              </p>
              <p>
                <strong>name_id_format:</strong>{" "}
                {result.metadata.name_id_format ?? t("not_set")}
              </p>
            </div>
          ) : null}
        </section>
      ) : null}
    </form>
  );
}
