// apps/web/lib/m12-account-backup.ts — Story 12.2 TS mirror.
//
// Pure kernel SSOT parity for the M12 backup subsystem. Mirrors the
// Python pure kernel `packages/services/m12_account/backup_export.py`.
// This file MUST stay in lockstep with the Python kernel — drift is
// caught by `tests/web/lib/m12-account-backup-parity.test.ts` (cross-language
// drift detector, Story 12.2 T7 + CR 12-5 D-13 pattern).
//
// AD-15 §11 SSOT: ko-KR.json is the canonical Korean SSOT for user-visible
// strings (CR 11-4 D-002). These constants are the **non-i18n** numeric
// and enum constants that need to match Python 1:1.

/** Mirrors `packages/services/m12_account/backup_export.py::SCHEMA_VERSION`. */
export const BACKUP_SCHEMA_VERSION = "1.0" as const;

/** Mirrors `packages/services/m12_account/backup_export.py::MAX_PAYLOAD_BYTES`. */
export const BACKUP_MAX_PAYLOAD_BYTES = 50 * 1024 * 1024;

/** Mirrors `packages/services/m12_account/backup_export.py::AUDIT_LOG_WINDOW_DAYS`. */
export const BACKUP_AUDIT_LOG_WINDOW_DAYS = 365 as const;

/**
 * Mirrors `packages/services/m12_account/backup_export.py::BACKUP_TABLES`.
 *
 * The 7 backup tables (must match Python tuple order — drift detector pins).
 * Schema mapping (per epics.md 6 표현 → 실 DB 7 매핑):
 *   - tenant_settings         → tenant_settings
 *   - products                → products
 *   - bom_lines               → bom_lines
 *   - monthly_input_periods   → monthly_input_periods
 *   - monthly_input_rows      → monthly_input_rows
 *   - fiscal_period_snapshots → fiscal_period_snapshots
 *   - audit_logs              → audit_logs (last 365d window)
 */
export const BACKUP_TABLES = [
  "tenant_settings",
  "products",
  "bom_lines",
  "monthly_input_periods",
  "monthly_input_rows",
  "fiscal_period_snapshots",
  "audit_logs",
] as const;

/**
 * Mirrors `apps/api/modules/m12_account/services/backup_export_service.py::DEFAULT_LIST_DAYS`.
 * Exposed in the kernel via `__all__` for endpoint query-param default.
 */
export const BACKUP_DEFAULT_LIST_DAYS = 7 as const;

/**
 * Mirrors `apps/api/jobs/backup_retention.py` 30-day rolling sweep
 * (NFR4 §1절: "백업 보관 30일(자동)").
 */
export const BACKUP_RETENTION_DAYS = 30 as const;

/**
 * Mirrors `apps/api/modules/m12_account/services/backup_export_service.py::MAX_LIST_DAYS`.
 * Service caps `days` query param at 30 (PRD safety cap).
 */
export const BACKUP_MAX_LIST_DAYS = 30 as const;

/** Item shape returned by `GET /api/v1/account/backups/recent`. */
export interface BackupListItem {
  backup_id: string;
  backup_date: string;
  schema_version: string;
  payload_sha256: string;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  payload_size_bytes: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  row_count_total: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  audit_log_exported_rows: number;
  created_at: string;
}

/** Envelope returned by `GET /api/v1/account/backups/recent`. */
export interface BackupListResponse {
  items: BackupListItem[];
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  total_count: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  days: number;
  trace_id: string;
}

/** Response from `POST /api/v1/account/backups/trigger`. */
export interface BackupTriggerResponse {
  backup_id: string;
  backup_date: string;
  payload_sha256: string;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  row_count_total: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  audit_log_exported_rows: number;
  created_at: string;
  trace_id: string;
}

/**
 * Build `backup-YYYY-MM-DD.json` filename (mirrors Python
 * `_build_backup_filename` in `apps/api/modules/m12_account/handlers.py`).
 */
export function buildBackupFilename(backupDateIso: string): string {
  return `backup-${backupDateIso}.json`;
}

/** Format byte count as human-readable string (B / KB / MB). */
// eslint-disable-next-line @typescript-eslint/no-restricted-types
export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}
