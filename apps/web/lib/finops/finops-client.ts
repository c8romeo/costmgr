/**
 * apps/web/lib/finops/finops-client.ts —
 * Phase 11 T7 (cj-style 107번째 wire) — FinOps Showback / Chargeback
 * client. Mirrors apps/web/lib/slo/slo-client.ts pattern verbatim.
 *
 * TypedDict parity (CR 12-5 D-PARITY-01) — the ShowbackDefinition +
 * DepartmentBreakdown + ComparisonView + ChargebackRule +
 * ChargebackResult + DepartmentCostCenterMapping types here mirror the
 * backend Python TypedDicts in apps/api/modules/finops/.
 */
import type {
  ChargebackResult,
  ChargebackRule,
  ComparisonView,
  DepartmentBreakdown,
  DepartmentCostCenterMapping,
  ExportFormat,
  ShowbackDefinition,
} from "@/lib/finops/finops-types";

export type {
  ChargebackResult,
  ChargebackRule,
  ComparisonView,
  DepartmentBreakdown,
  DepartmentCostCenterMapping,
  ExportFormat,
  ShowbackDefinition,
};

export interface FinopsApiPage<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export class FinopsApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly trace_id: string;
  constructor(
    message: string,
    status: number,
    code: string,
    trace_id: string,
  ) {
    super(message);
    this.name = "FinopsApiError";
    this.status = status;
    this.code = code;
    this.trace_id = trace_id;
  }
}

const DEFAULT_TIMEOUT_MS = 15_000;

interface RequestOptions {
  accessToken: string;
  locale?: string;
  signal?: AbortSignal;
}

async function request<T>(
  path: string,
  init: RequestInit & { accessToken: string; locale?: string },
): Promise<T> {
  const { accessToken, locale, signal, ...rest } = init;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);
  const externalSignal = signal;
  try {
    const headers: Record<string, string> = {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
      ...((rest.headers ?? {}) as Record<string, string>),
    };
    if (locale) headers["Accept-Language"] = locale;
    const res = await fetch(path, {
      ...rest,
      headers,
      signal: externalSignal ?? controller.signal,
    });
    if (!res.ok) {
      const body = (await res.json().catch(() => ({}))) as {
        code?: string;
        message?: string;
        trace_id?: string;
      };
      throw new FinopsApiError(
        body.message ?? res.statusText,
        res.status,
        body.code ?? "FINOPS_API_ERROR",
        body.trace_id ?? "",
      );
    }
    return (await res.json()) as T;
  } finally {
    clearTimeout(timeout);
  }
}

export async function listShowbackBreakdown(
  definition: ShowbackDefinition,
  opts: RequestOptions,
): Promise<FinopsApiPage<DepartmentBreakdown>> {
  return request<FinopsApiPage<DepartmentBreakdown>>(
    "/api/v1/admin/finops/showback/breakdown",
    {
      method: "POST",
      accessToken: opts.accessToken,
      locale: opts.locale,
      body: JSON.stringify(definition),
    },
  );
}

export async function listShowbackComparison(
  definition: ShowbackDefinition,
  opts: RequestOptions,
): Promise<FinopsApiPage<ComparisonView>> {
  return request<FinopsApiPage<ComparisonView>>(
    "/api/v1/admin/finops/showback/comparison",
    {
      method: "POST",
      accessToken: opts.accessToken,
      locale: opts.locale,
      body: JSON.stringify(definition),
    },
  );
}

export async function listChargebackResults(
  period_key: string,
  opts: RequestOptions,
): Promise<FinopsApiPage<ChargebackResult>> {
  return request<FinopsApiPage<ChargebackResult>>(
    `/api/v1/admin/finops/chargeback?period_key=${encodeURIComponent(period_key)}`,
    {
      method: "GET",
      accessToken: opts.accessToken,
      locale: opts.locale,
    },
  );
}

export async function listDepartmentMappings(
  opts: RequestOptions,
): Promise<FinopsApiPage<DepartmentCostCenterMapping>> {
  return request<FinopsApiPage<DepartmentCostCenterMapping>>(
    "/api/v1/admin/finops/department-mappings",
    {
      method: "GET",
      accessToken: opts.accessToken,
      locale: opts.locale,
    },
  );
}

export async function exportChargeback(
  period_key: string,
  format: ExportFormat,
  opts: RequestOptions,
): Promise<Blob> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);
  try {
    const headers: Record<string, string> = {
      Authorization: `Bearer ${opts.accessToken}`,
    };
    if (opts.locale) headers["Accept-Language"] = opts.locale;
    const res = await fetch(
      `/api/v1/admin/finops/chargeback/export?period_key=${encodeURIComponent(
        period_key,
      )}&format=${format}`,
      { method: "GET", headers, signal: opts.signal ?? controller.signal },
    );
    if (!res.ok) {
      const body = (await res.json().catch(() => ({}))) as {
        code?: string;
        message?: string;
      };
      throw new FinopsApiError(
        body.message ?? res.statusText,
        res.status,
        body.code ?? "FINOPS_API_ERROR",
        "",
      );
    }
    return await res.blob();
  } finally {
    clearTimeout(timeout);
  }
}
