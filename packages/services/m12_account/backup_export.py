"""packages.services.m12_account.backup_export — Story 12.2 pure kernel.

AD-11 layer rule: pure-Python, stdlib-only. NO DB, NO clock at module
level, NO random at module level.

7-table JSON dump + sha256 deterministic digest:
- `serialize_backup_payload` — stable JSON (sort_keys + separators)
- `compute_payload_sha256` — hashlib.sha256 hex digest
- `build_backup_envelope` — top-level schema_version 1.0 envelope
- `collapse_audit_logs` — 365-day sliding window for audit_logs
- 50 MB payload cap with BackupPayloadTooLargeError

Korean messages — AD-15 §11 SSOT. Mirrored verbatim in
`apps/web/lib/m12-account-backup.ts`.

This module is the M12 module authority's pure kernel — service layer
(`apps/api/modules/m12_account/services/backup_export_service.py`)
imports these helpers and adds DB / audit / session concerns.

NFR4 (PRD §NFR4): "RPO 24h / RTO 4h / 백업 보관 30일(자동), 1년(분기)
/ 감사로그 5년 append-only".

Quarterly 1-year archive is honestly DEFER (per CR 11-3 — sprint-scale).
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from typing import Any, Final
from uuid import UUID

# ── Constants ────────────────────────────────────────────────
SCHEMA_VERSION: Final[str] = "1.0"

# 50 MB payload cap — guards tenant_backups row size + RLS JSONB perf
MAX_PAYLOAD_BYTES: Final[int] = 50 * 1024 * 1024

# audit_logs 365-day sliding window (NFR4 retention + 5y audit balance)
AUDIT_LOG_WINDOW_DAYS: Final[int] = 365

# 7-table fixed set (epics.md AC verbatim, split into 7 DB tables)
BACKUP_TABLES: Final[tuple[str, ...]] = (
    "tenant_settings",
    "products",
    "bom_lines",
    "monthly_input_periods",
    "monthly_input_rows",
    "fiscal_period_snapshots",
    "audit_logs",
)


# ── Error codes — pure-kernel domain semantics (AD-15 §4 envelope contract)
ERROR_CODE_PAYLOAD_TOO_LARGE: Final[str] = "BACKUP_PAYLOAD_TOO_LARGE"
ERROR_CODE_ENVELOPE_INVALID: Final[str] = "BACKUP_ENVELOPE_INVALID"
ERROR_CODE_RETENTION_CUTOFF_INVALID: Final[str] = "BACKUP_RETENTION_CUTOFF_INVALID"

# Korean constants — AD-15 §11 SSOT (mirrored in ko-KR.json account_backup)
BACKUP_EXPORT_TITLE_KO: Final[str] = "백업 다운로드"
BACKUP_RETENTION_PURGED_KO: Final[str] = "30일 보관 만료 백업 정리"
BACKUP_FAILED_KO: Final[str] = "백업 생성 실패"
BACKUP_TRIGGERED_KO: Final[str] = "수동 백업 트리거"
BACKUP_DOWNLOADED_KO: Final[str] = "백업 다운로드 완료"
PAYLOAD_TOO_LARGE_KO: Final[str] = "백업 페이로드가 50MB를 초과했습니다"


# ── Typed exceptions ──────────────────────────────────────────
class BackupExportServiceError(Exception):
    """Base pure-kernel backup export error (500 envelope)."""

    def __init__(self, message_ko: str = BACKUP_EXPORT_TITLE_KO) -> None:
        self.message_ko = message_ko
        self.error_code = "BACKUP_SERVICE_ERROR"
        super().__init__(message_ko)


class BackupPayloadTooLargeError(BackupExportServiceError):
    """Pure-kernel payload size limit (50 MB cap).

    HTTP envelope (AD-15 §4): 422 BACKUP_PAYLOAD_TOO_LARGE
    (service layer maps to envelope).
    """

    def __init__(
        self,
        message_ko: str = PAYLOAD_TOO_LARGE_KO,
        *,
        size_bytes: int = 0,
        max_bytes: int = MAX_PAYLOAD_BYTES,
    ) -> None:
        self.message_ko = message_ko
        self.error_code = ERROR_CODE_PAYLOAD_TOO_LARGE
        self.size_bytes = size_bytes
        self.max_bytes = max_bytes
        super().__init__(message_ko)


class BackupEnvelopeInvalidError(BackupExportServiceError):
    """Pure-kernel envelope validation failed (422 envelope)."""

    def __init__(
        self, message_ko: str = BACKUP_EXPORT_TITLE_KO, *, reason: str = ""
    ) -> None:
        self.message_ko = message_ko
        self.error_code = ERROR_CODE_ENVELOPE_INVALID
        self.reason = reason
        super().__init__(message_ko)


class BackupRetentionCutoffInvalidError(BackupExportServiceError):
    """Pure-kernel retention cutoff is invalid (422 envelope).

    HTTP envelope (AD-15 §4): 422 BACKUP_RETENTION_CUTOFF_INVALID
    """

    def __init__(
        self, message_ko: str = BACKUP_RETENTION_PURGED_KO, *, reason: str = ""
    ) -> None:
        self.message_ko = message_ko
        self.error_code = ERROR_CODE_RETENTION_CUTOFF_INVALID
        self.reason = reason
        super().__init__(message_ko)


# ── Pure-kernel functions ─────────────────────────────────────
def serialize_backup_payload(payload: dict[str, Any]) -> bytes:
    """Serialize backup payload to deterministic UTF-8 JSON bytes.

    Precedent: `packages/cost_engine/core/period_cost.py:153-159`
    `_stable_json_dumps` — `sort_keys=True, separators=(",", ":"),
    default=str`. AD-11 pure kernel — caller passes timestamp separately.

    Args:
        payload: Envelope dict (already shaped via `build_backup_envelope`).

    Returns:
        UTF-8 encoded JSON bytes — deterministic for given input.

    Raises:
        BackupPayloadTooLargeError: If serialized bytes > MAX_PAYLOAD_BYTES.
    """
    if not isinstance(payload, dict):
        raise BackupEnvelopeInvalidError(reason="payload must be dict")
    blob = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
        ensure_ascii=False,
    ).encode("utf-8")
    if len(blob) > MAX_PAYLOAD_BYTES:
        raise BackupPayloadTooLargeError(
            size_bytes=len(blob), max_bytes=MAX_PAYLOAD_BYTES
        )
    return blob


def compute_payload_sha256(payload_bytes: bytes) -> str:
    """Compute deterministic sha256 hex digest of payload bytes.

    Args:
        payload_bytes: UTF-8 JSON bytes (from `serialize_backup_payload`).

    Returns:
        64-char lowercase hex digest.

    Raises:
        BackupEnvelopeInvalidError: If payload_bytes is empty.
    """
    if not payload_bytes:
        raise BackupEnvelopeInvalidError(reason="payload_bytes must be non-empty")
    return hashlib.sha256(payload_bytes).hexdigest()


def build_backup_envelope(
    *,
    backup_id: UUID,
    tenant_id: UUID,
    created_at: datetime,
    backup_date: date,
    tables: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Build the top-level schema_version 1.0 envelope.

    Envelope keys (deterministic order — for sort_keys=True stability):
    - `schema_version`: "1.0"
    - `backup_id`: UUID as str
    - `tenant_id`: UUID as str
    - `created_at`: ISO-8601 UTC timestamp
    - `backup_date`: YYYY-MM-DD KST date
    - `tables`: dict[table_name, list[dict]] — 7 fixed set
    - `row_count_total`: sum of all table counts

    Args:
        backup_id: New backup row PK (uuid4).
        tenant_id: Tenant owning this backup.
        created_at: UTC datetime when backup was generated.
        backup_date: KST date for this backup.
        tables: 7-table dump (see BACKUP_TABLES tuple).

    Returns:
        Envelope dict (caller passes to `serialize_backup_payload`).
    """
    if not tables:
        raise BackupEnvelopeInvalidError(reason="tables must be non-empty dict")
    missing = [t for t in BACKUP_TABLES if t not in tables]
    if missing:
        raise BackupEnvelopeInvalidError(
            reason=f"missing required tables: {missing!r}"
        )
    row_count_total = sum(len(rows) for rows in tables.values())
    return {
        "schema_version": SCHEMA_VERSION,
        "backup_id": str(backup_id),
        "tenant_id": str(tenant_id),
        "created_at": created_at.isoformat(),
        "backup_date": backup_date.isoformat(),
        "tables": dict(tables),
        "row_count_total": row_count_total,
    }


def collapse_audit_logs(
    tables: dict[str, list[dict[str, Any]]],
    *,
    cutoff: datetime,
    now: datetime | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Filter audit_logs rows to a 365-day sliding window.

    Per AC #1: "audit_logs는 last 365일만 (NFR4 retention + 5y audit 일관성
    — supabase dump가 너무 커지지 않도록 슬라이딩)".

    Other tables are passed through unchanged.

    Args:
        tables: Envelope's `tables` dict.
        cutoff: Lower bound — rows with `occurred_at < cutoff` are dropped.
        now: Reference "now" for the window (caller-controlled for AD-11
            testability). Default None → rejected (pure kernel contract).

    Returns:
        New dict with audit_logs collapsed. Other tables unchanged.

    Raises:
        BackupRetentionCutoffInvalidError: If `now` not provided or
            cutoff > now.
    """
    if now is None:
        raise BackupRetentionCutoffInvalidError(
            reason="now must be provided (AD-11: no module-level clock)"
        )
    if cutoff > now:
        raise BackupRetentionCutoffInvalidError(
            reason=f"cutoff ({cutoff.isoformat()}) > now ({now.isoformat()})"
        )
    audit_rows = tables.get("audit_logs", [])
    kept: list[dict[str, Any]] = []
    for row in audit_rows:
        occurred_raw = row.get("occurred_at")
        if not occurred_raw:
            continue
        try:
            occurred_dt = _parse_iso8601(occurred_raw)
        except ValueError:
            # Malformed timestamp — drop row defensively (pure-kernel no DB).
            continue
        if occurred_dt >= cutoff:
            kept.append(row)
    new_tables: dict[str, list[dict[str, Any]]] = dict(tables)
    new_tables["audit_logs"] = kept
    return new_tables


def _parse_iso8601(value: str) -> datetime:
    """Parse ISO-8601 timestamp (pure-kernel helper).

    Accepts both `...Z` (Zulu) and `...+00:00` (offset) representations.
    """
    cleaned = value.replace("Z", "+00:00") if value.endswith("Z") else value
    return datetime.fromisoformat(cleaned)


__all__ = [
    # constants
    "SCHEMA_VERSION",
    "MAX_PAYLOAD_BYTES",
    "AUDIT_LOG_WINDOW_DAYS",
    "BACKUP_TABLES",
    # error codes
    "ERROR_CODE_PAYLOAD_TOO_LARGE",
    "ERROR_CODE_ENVELOPE_INVALID",
    "ERROR_CODE_RETENTION_CUTOFF_INVALID",
    # Korean SSOT
    "BACKUP_EXPORT_TITLE_KO",
    "BACKUP_RETENTION_PURGED_KO",
    "BACKUP_FAILED_KO",
    "BACKUP_TRIGGERED_KO",
    "BACKUP_DOWNLOADED_KO",
    "PAYLOAD_TOO_LARGE_KO",
    # exceptions
    "BackupExportServiceError",
    "BackupPayloadTooLargeError",
    "BackupEnvelopeInvalidError",
    "BackupRetentionCutoffInvalidError",
    # functions
    "serialize_backup_payload",
    "compute_payload_sha256",
    "build_backup_envelope",
    "collapse_audit_logs",
]
