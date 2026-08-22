/**
 * apps/web/components/settings/sso/IdPAdminPanel.tsx — Epic 16 T4 (AC #7.4)
 *
 * Orchestrator client component for /settings/sso page (Tenant IdP
 * admin management UI).
 *
 * Per PRD §F19.4 + AD-30 (d) the panel composes 4 sub-components:
 *   - <IdPList>            current config (0 or 1 row) + edit/delete
 *   - <IdPCreateForm>      metadata_xml OR direct fields, submit → POST
 *   - <IdPEditForm>        full-replace, PUT (initial values from list)
 *   - <IdPTestPanel>       8-step dry-run validation result panel
 *
 * Korean SSOT: apps/web/messages/ko-KR.json::settings_sso.
 *
 * CR 11-4 D-001 (page.tsx mount MUST) — `force-dynamic` page renders
 * this client component unconditionally, even when initial fetch
 * returned null. Fail-closed: empty state surfaces and the user can
 * trigger a retry via the client-side refetch.
 *
 * CR 11-4 D-002 (ko-KR.json SSOT only) — all user-facing strings
 * come from `useTranslations("settings_sso")` — never hard-coded.
 *
 * CR 11-4 D-005 (unknown state reject) — when `tenantSlug` is
 * missing, we render an inline "tenant_slug_required" notice and
 * disable create/edit/delete actions. Backend enforces capability
 * gate; frontend surfaces 403 envelopes as typed errors.
 */

"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { toast } from "sonner";

import type { IdPConfig } from "@/lib/auth/admin-idp-client";
import {
  createIdPConfig,
  deleteIdPConfig,
  listIdPConfigs,
  updateIdPConfig,
} from "@/lib/auth/admin-idp-client";

import { IdPCreateForm } from "./IdPCreateForm";
import { IdPEditForm } from "./IdPEditForm";
import { IdPList } from "./IdPList";
import { IdPTestPanel } from "./IdPTestPanel";

export interface IdPAdminPanelProps {
  /** Current tenant slug — required for admin endpoints. */
  tenantSlug: string;
  /** Initial list seeded by the RSC page (F-20 race-free). */
  initialConfigs: IdPConfig[];
  /** Access token forwarded from RSC layout. */
  accessToken: string;
}

type View = "list" | "create" | "edit" | "test";

export function IdPAdminPanel(
  props: IdPAdminPanelProps,
): React.ReactElement {
  const t = useTranslations("settings_sso");
  const router = useRouter();

  const [configs, setConfigs] = React.useState<IdPConfig[]>(props.initialConfigs);
  const [view, setView] = React.useState<View>("list");
  const [loading, setLoading] = React.useState(false);
  const [forbidden, setForbidden] = React.useState(false);

  const hasTenant = props.tenantSlug.length > 0;
  const currentConfig: IdPConfig | null = configs.length > 0 ? configs[0] : null;

  // CR 11-4 D-005 — if no tenant_slug, render the inline notice and
  // disable the action surfaces.
  if (!hasTenant) {
    return (
      <div
        data-testid="idp-admin-tenant-slug-required"
        className="mx-auto max-w-2xl rounded-lg border border-yellow-300 bg-yellow-50 p-6 text-sm text-yellow-800"
      >
        {t("tenant_slug_required")}
      </div>
    );
  }

  const handleRefetch = React.useCallback(async () => {
    setLoading(true);
    try {
      const result = await listIdPConfigs(props.accessToken, props.tenantSlug);
      if (result.ok) {
        setConfigs(result.data);
        setForbidden(false);
      } else if (result.error?.status === 403) {
        setForbidden(true);
      } else if (result.error) {
        toast.error(result.error.message_ko);
      }
    } catch {
      toast.error(t("toast_error_network"));
    } finally {
      setLoading(false);
    }
  }, [props.accessToken, props.tenantSlug, t]);

  const handleCreate = async (
    body: Parameters<typeof createIdPConfig>[2],
  ): Promise<boolean> => {
    setLoading(true);
    try {
      const result = await createIdPConfig(
        props.accessToken,
        props.tenantSlug,
        body,
      );
      if (result.ok) {
        toast.success(t("toast_success_created"));
        setView("list");
        await handleRefetch();
        router.refresh();
        return true;
      }
      if (result.error) {
        toast.error(result.error.message_ko);
      }
      return false;
    } catch {
      toast.error(t("toast_error_network"));
      return false;
    } finally {
      setLoading(false);
    }
  };

  const handleUpdate = async (
    body: Parameters<typeof updateIdPConfig>[2],
  ): Promise<boolean> => {
    setLoading(true);
    try {
      const result = await updateIdPConfig(
        props.accessToken,
        props.tenantSlug,
        body,
      );
      if (result.ok) {
        toast.success(t("toast_success_updated"));
        setView("list");
        await handleRefetch();
        router.refresh();
        return true;
      }
      if (result.error) {
        toast.error(result.error.message_ko);
      }
      return false;
    } catch {
      toast.error(t("toast_error_network"));
      return false;
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (): Promise<boolean> => {
    setLoading(true);
    try {
      const result = await deleteIdPConfig(props.accessToken, props.tenantSlug);
      if (result.ok) {
        toast.success(t("toast_success_deleted"));
        await handleRefetch();
        router.refresh();
        return true;
      }
      if (result.error) {
        toast.error(result.error.message_ko);
      }
      return false;
    } catch {
      toast.error(t("toast_error_network"));
      return false;
    } finally {
      setLoading(false);
    }
  };

  if (forbidden) {
    return (
      <div
        data-testid="idp-admin-forbidden"
        className="mx-auto max-w-2xl rounded-lg border border-red-300 bg-red-50 p-6 text-sm text-red-800"
      >
        {t("forbidden_notice")}
      </div>
    );
  }

  return (
    <div data-testid="idp-admin-panel" className="mx-auto max-w-3xl space-y-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-bold text-slate-900">{t("page_title")}</h1>
        <p className="text-sm text-slate-600">{t("page_subtitle")}</p>
      </header>

      {view === "list" ? (
        <IdPList
          config={currentConfig}
          loading={loading}
          onCreate={() => setView("create")}
          onEdit={() => setView("edit")}
          onTest={() => setView("test")}
          onDelete={handleDelete}
        />
      ) : null}

      {view === "create" ? (
        <IdPCreateForm
          loading={loading}
          onCancel={() => setView("list")}
          onSubmit={handleCreate}
        />
      ) : null}

      {view === "edit" && currentConfig ? (
        <IdPEditForm
          config={currentConfig}
          loading={loading}
          onCancel={() => setView("list")}
          onSubmit={handleUpdate}
        />
      ) : null}

      {view === "test" ? (
        <IdPTestPanel
          accessToken={props.accessToken}
          tenantSlug={props.tenantSlug}
          onCancel={() => setView("list")}
        />
      ) : null}
    </div>
  );
}
