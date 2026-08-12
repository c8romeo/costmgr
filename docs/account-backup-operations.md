# Account Backup Operations (Story 12.2)

**Story:** 12.2 — Daily Auto-Backup + JSON Self-Download
**PRD:** §F12.2 + §M12-b + §NFR4
**AD references:** AD-2 INSERT-only, AD-3 multi-tenancy, AD-10 owner-only role,
AD-11 layer rule, AD-15 §4 envelope, NFR4 (RPO 24h / RTO 4h / 30-day retention)

---

## Overview

Story 12.2 wires the operational infrastructure for tenant data backup:
- **Daily auto-backup** (`apps/api/jobs/backup_daily.py`) — 7-table JSON dump per tenant
- **30-day retention sweep** (`apps/api/jobs/backup_retention.py`) — soft-delete purge
- **Owner-only JSON self-download** (`apps/api/modules/m12_account/handlers.py`)
- **Per-tenant audit trail** (`ActionClass.ACCOUNT_BACKUP` 5 values)

The system stores backups as **JSONB rows** in a Postgres table (`tenant_backups`)
rather than Supabase Storage or S3. This decision minimizes operational complexity
(no new SDK, no new bucket, no new env vars) while keeping RLS as the access
control mechanism.

---

## Architecture (AD-11 layer rule)

```
┌───────────────────────────────────────────────────────────────┐
│ pure kernel: packages/services/m12_account/backup_export.py   │
│   - serialize_backup_payload (stdlib JSON)                    │
│   - compute_payload_sha256 (stdlib hashlib)                   │
│   - build_backup_envelope (schema_version="1.0" + 7 tables)   │
│   - collapse_audit_logs (365-day window)                      │
└───────────────────────────────────────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────────┐
│ service: apps/api/modules/m12_account/services/               │
│          backup_export_service.py                             │
│   - BackupExportService.run_backup                            │
│   - BackupExportService.run_retention_sweep                   │
│   - BackupExportService.trigger_backup                        │
│   - BackupExportService.list_recent_backups                   │
│   - BackupExportService.fetch_backup_payload                  │
│   - audit_first emit (CR 1.1 pattern)                         │
└───────────────────────────────────────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────────┐
│ HTTP routes: apps/api/modules/m12_account/handlers.py         │
│   - GET  /api/v1/account/backups/recent          (owner-only)│
│   - GET  /api/v1/account/backups/{id}/download   (owner-only)│
│   - POST /api/v1/account/backups/trigger          (owner-only)│
└───────────────────────────────────────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────────┐
│ cron jobs: apps/api/jobs/                                     │
│   - backup_daily.py      KST 02:00 (UTC 17:00) — 7-table dump│
│   - backup_retention.py  KST 03:00 (UTC 18:00) — 30-day sweep│
└───────────────────────────────────────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────────┐
│ frontend: apps/web/                                           │
│   - components/m12-account/BackupDownloadPanel.tsx            │
│   - app/[locale]/(dashboard)/account/backups/page.tsx         │
│   - lib/m12-account-backup.ts (TS mirror)                     │
│   - messages/ko-KR.json::account_backup (18 strings)          │
└───────────────────────────────────────────────────────────────┘
```

---

## Database Schema (Alembic 0024)

Table: `tenant_backups` (12 columns + 2 indexes + partial UNIQUE)

| Column                      | Type           | Notes                                      |
|-----------------------------|----------------|--------------------------------------------|
| `backup_id`                 | UUID           | PK, default `gen_random_uuid()`            |
| `tenant_id`                 | UUID           | FK → tenants(id) ON DELETE CASCADE         |
| `backup_date`               | TIMESTAMP      | YYYY-MM-DD anchor (KST date)               |
| `created_at`                | TIMESTAMPTZ    | default `now()`                            |
| `schema_version`            | TEXT           | default `'1.0'` (envelope version)         |
| `payload`                   | JSONB          | full 7-table dump                          |
| `payload_sha256`            | TEXT           | hex sha256 of payload bytes                |
| `row_count_total`           | INTEGER        | total rows in payload                      |
| `audit_log_exported_rows`   | INTEGER        | count of audit_logs rows included          |
| `retention_class`           | TEXT           | default `'daily'` (quarterly honestly DEFER) |
| `purged_at`                 | TIMESTAMPTZ    | NULL = active; non-NULL = soft-deleted     |
| `triggered_by_user_id`      | UUID           | FK → users(id) ON DELETE SET NULL          |

**Indexes:**
- `tenant_backups_tenant_id_backup_date_idx` (tenant_id, backup_date DESC) — list query
- `tenant_backups_purged_at_idx` partial WHERE purged_at IS NULL — sweep filter
- `tenant_backups_unique_active_per_day` partial UNIQUE (tenant_id, backup_date)
  WHERE purged_at IS NULL — one active backup per tenant per day

---

## RLS Policies (`supabase/policies/0014_tenant_backups_rls.sql`)

5-policy split per AD-3:

| Policy                                | Effect                                                |
|---------------------------------------|-------------------------------------------------------|
| `tenant_backups_select_same_tenant`   | Same-tenant SELECT (members can list metadata)        |
| `tenant_backups_select_owner`         | Owner-only SELECT (full payload download)             |
| `tenant_backups_insert_owner`         | Owner-only INSERT (manual trigger)                    |
| (NO UPDATE policy)                    | AD-2 INSERT-only — RLS rejects all app-role UPDATEs   |
| (NO DELETE policy)                    | AD-2 INSERT-only — RLS rejects all app-role DELETEs   |

**Special case:** the `purged_at` soft-delete column is updated by the retention
cron under **service-role** (bypasses RLS). This is the ONLY permitted UPDATE path.

`consultant_proxy` is NOT granted access — backups contain `audit_logs` rows
(NFR6-sensitive) so cross-tenant access is forbidden.

---

## HTTP API (AD-15 §4 envelope)

### `GET /api/v1/account/backups/recent`

List recent backups (owner-only).

**Query params:**
- `days` (int, default 7, max 30) — window size

**Response 200:**
```json
{
  "items": [
    {
      "backup_id": "uuid",
      "backup_date": "2026-08-12",
      "schema_version": "1.0",
      "payload_sha256": "abc123...",
      "payload_size_bytes": 1048576,
      "row_count_total": 12345,
      "audit_log_exported_rows": 500,
      "created_at": "2026-08-12T17:00:00Z"
    }
  ],
  "total_count": 1,
  "days": 7,
  "trace_id": "uuid"
}
```

### `GET /api/v1/account/backups/{backup_id}/download`

Download backup as JSON bytes (owner-only).

**Response 200:**
- `Content-Type: application/json`
- `Content-Disposition: attachment; filename="backup-YYYY-MM-DD.json"`
- `X-Backup-SHA256: <hex>` (client verification)
- `X-Backup-Trace-Id: <uuid>`
- Body: full backup envelope (schema_version + 7 tables)

**404 BACKUP_NOT_FOUND** if backup_id is missing, purged, or cross-tenant.

### `POST /api/v1/account/backups/trigger`

Manual owner-triggered backup (owner-only).

**Request body:** `{}` (Pydantic forbid-extra)

**Response 201:**
```json
{
  "backup_id": "uuid",
  "backup_date": "2026-08-12",
  "payload_sha256": "abc123...",
  "row_count_total": 12345,
  "audit_log_exported_rows": 500,
  "created_at": "2026-08-12T17:00:00Z",
  "trace_id": "uuid"
}
```

---

## Audit Trail (`ActionClass.ACCOUNT_BACKUP` — 5 values)

| Action                     | When                                                  |
|----------------------------|-------------------------------------------------------|
| `backup_created`           | New backup INSERT succeeded                           |
| `backup_failed`            | Backup run raised an exception (CR 1.1 audit-first)   |
| `backup_retention_purged`  | 30-day sweep marked a row as purged                   |
| `backup_downloaded`        | Owner downloaded a backup JSON                       |
| `backup_triggered`         | Manual owner trigger initiated                        |

All audit rows are INSERT-only (AD-2) and routed to `audit_logs` table.

---

## Cron Schedule (NFR4 RPO 24h / RTO 4h)

| Job                | Schedule (KST) | Schedule (UTC) | Per-Tenant | Notes                                       |
|--------------------|----------------|----------------|------------|---------------------------------------------|
| `backup_daily`     | 02:00          | 17:00          | Yes        | 7-table dump + INSERT                       |
| `backup_retention` | 03:00          | 18:00          | Yes        | 30-day rolling sweep (UPDATE purged_at)     |

**Precedent:** `apps/api/jobs/document_retention.py:51-83` (Story 1.3).

**Failure isolation:** one tenant's failure does not block other tenants.
The cron runner logs the exception and continues.

---

## Capability Matrix v1.14

`Capability.BACKUP_EXPORT` is documented as **industry-agnostic** (CR 12-1 L4
precedent — security baseline). Granted to ALL 4 canonical industries:
manufacturing / service / manufacturing_service / manufacturing_service_other.

**NOT enforced as a route gate.** Per CR 12-1 L4, the capability is documented
but route access is gated by `require_role("owner")` (AD-10) only.

Reference: `docs/capability-matrix.md` v1.14.

---

## TS Mirror (`apps/web/lib/m12-account-backup.ts`)

Mirrors the Python pure kernel constants. Drift detector:
`tests/web/lib/test_m12_account_backup_parity.py` (CR 12-5 D-13 pattern).

| Python (`packages/services/m12_account/backup_export.py`) | TS (`apps/web/lib/m12-account-backup.ts`) |
|-----------------------------------------------------------|------------------------------------------|
| `SCHEMA_VERSION = "1.0"`                                  | `BACKUP_SCHEMA_VERSION = "1.0"`          |
| `MAX_PAYLOAD_BYTES = 50 * 1024 * 1024`                    | `BACKUP_MAX_PAYLOAD_BYTES = 50 * 1024 * 1024` |
| `AUDIT_LOG_WINDOW_DAYS = 365`                             | `BACKUP_AUDIT_LOG_WINDOW_DAYS = 365`     |
| `BACKUP_TABLES = (7 entries)`                             | `BACKUP_TABLES = [...]` (same order)     |
| `DEFAULT_LIST_DAYS = 7` (service)                         | `BACKUP_DEFAULT_LIST_DAYS = 7`           |
| `MAX_LIST_DAYS = 30` (service)                            | `BACKUP_MAX_LIST_DAYS = 30`              |
| (cron) `30-day retention`                                 | `BACKUP_RETENTION_DAYS = 30`             |

---

## Korean SSOT (AD-15 §11)

- Backend Korean messages: `apps/api/modules/m12_account/services/audit_extension.py` (`*_KO` constants)
- Frontend Korean strings: `apps/web/messages/ko-KR.json::account_backup` (18 keys)

The frontend `BackupDownloadPanel` uses `useTranslations("account_backup")` for
all user-visible strings. The Python backend uses `BACKUP_*_KO` constants in
the audit emission layer.

---

## Tests

| Test file                                                       | Cases | Coverage                              |
|-----------------------------------------------------------------|-------|---------------------------------------|
| `tests/services/m12_account/test_backup_export.py`              | 26    | pure kernel (serialize + sha256)      |
| `tests/api/m12_account/test_backup_export_service.py`           | 19    | service layer (5 methods + audit)     |
| `tests/api/jobs/test_backup_daily.py`                           | 5     | daily cron (per-tenant isolation)     |
| `tests/api/jobs/test_backup_retention.py`                       | 6     | retention cron (cutoff default 30d)   |
| `tests/api/m12_account/test_backup_handlers_route_shape.py`     | 14    | HTTP routes (paths, gates, schemas)   |
| `tests/integration/test_capability_matrix_v1_14_drift.py`       | 11    | Capability ↔ docs ↔ 4-industry grant  |
| `tests/integration/test_tenant_backups_0024_migration.py`       | 21    | Alembic 0024 + RLS 0014 DDL parity     |
| `tests/web/lib/test_m12_account_backup_parity.py`               | 14    | Python ↔ TS cross-language drift       |
| **TOTAL**                                                       | **116** | all 7 backend modules + frontend      |

---

## Honestly DEFER (CR 11-3 — sprint-scale)

These are documented in `docs/deferred-work.md` under "Story 12.2 carry-over":

1. **Quarterly 1-year archive** — long-term retention class (PRD §NFR4 §2).
2. **Manual restore endpoint** — `POST /api/v1/account/backups/{id}/restore`
   (currently the cron + DB-level restore is the only path).
3. **Playwright E2E** — 16 NEW cases (owner UI flows) per Story 12.5 T6
   pattern, sprint-scale.
4. **gzip compression** — payload > 1MB could benefit from `Content-Encoding: gzip`.
5. **Cross-region replication** — multi-region Postgres read replica for DR.

---

## Operational Notes

**Restore procedure** (operator manual, not user-facing):

```sql
-- 1. Find the backup row
SELECT payload, payload_sha256 FROM tenant_backups
WHERE tenant_id = '<tenant-uuid>'
  AND backup_date = '<YYYY-MM-DD>'
  AND purged_at IS NULL;

-- 2. Verify sha256
-- Compare returned payload_sha256 against local sha256(payload::text).

-- 3. Apply table-by-table (in BACKUP_TABLES order)
-- The payload is a JSONB envelope; iterate keys and INSERT.
```

**Quarterly 1-year archive** is NOT wired. Backups beyond 30 days are
soft-deleted (`purged_at`) and removed by future GC. For regulatory retention,
operators must manually export the JSONB row before purge.

**Alerting:** the cron runner (Railway / GitHub Actions) should emit a Slack
alert on any `backup_failed` audit row. The 5 audit values are routable via
the existing audit publisher.

---

**CR 12-1 L4 + CR 12-5 D-13 + CR 11-3 honest-DEFER + CR 11-4 D-001/D-002/D-005**
lessons applied. See memory file `cr-12-2-lessons` (future).
