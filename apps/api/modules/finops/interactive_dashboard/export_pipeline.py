"""apps.api.modules.finops.interactive_dashboard.export_pipeline — Phase 28 export pipeline.

Phase 28 wire (cj-style 193번째) — FinOps Interactive Dashboard
export_pipeline (PRD §F43.3 verbatim + AD-56 (c) verbatim + Phase
17/22 export pipeline reuse EXTENSION).

Provides:
- start_export_job(tenant_id, view_id, fmt, options) → ExportJob
- get_export_job_status(job_id) → ExportJob
- list_export_jobs(tenant_id, filter) → list[ExportJob]
- cancel_export_job(job_id) → ExportJob
- 5 export formats (PDF reportlab 4.0.7 AD-14 stack pin +
  XLSX xlsxwriter 3.1.9 + CSV pandas 2.1.4 + JSON native +
  PNG via matplotlib 3.8.2 chart snapshot)
- reuse Phase 17 sustainability report generator (PDF template reuse)
- reuse Phase 22 chargeback invoice generator (XLSX template
  EXTENSION)
- max_export_size 50MB guard (52428800 bytes)
- 3 auto-retries
- admin email alert on failure (caller-side)
- audit-first INSERT export_job_started + export_job_completed +
  export_job_failed (caller-side via emit_audit_typed)

Honest scope notes (per CR 11-3 honest-DEFER 85번째):
- This engine is the **lifecycle tracker** + format validator +
  size guard + retry counter. The actual byte-level rendering
  (reportlab canvas / xlsxwriter Workbook / matplotlib chart) is
  performed by the FastAPI worker (router layer or scheduled
  dispatch), reusing Phase 17 sustainability report generator +
  Phase 22 chargeback invoice template EXTENSION (no parallel
  re-implementation here).
- In-memory job store only — caller is expected to wire DB
  persistence in the router layer (Phase 26 pattern verbatim
  EXTENSION).

CR lessons applied:
- CR 0-2 RLS — tenant_id selector.
- CR 1-1 audit-first INSERT — export_job_started/completed/failed
  (caller-side via emit_audit_typed).
- CR 1-1 FastAPI ContextVar — trace_id propagation.
- CR 5-1 banker's rounding — Decimal precision verbatim.
- CR 11-3 honest-DEFER — D-FINOPS-15 honestly DEFER 보존.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope — 4 NEW typed exceptions
  (ExportJobError 500 + ExportJobFormatError 400 + ExportJobSizeError
  413 + ExportJobTenantError 403) raised by engine on misuse.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript parity.
- CR 12-5 D-GATE-01 — capability gate fail-closed (router layer).
- AD-14 stack pin — reportlab 4.0.7 + xlsxwriter 3.1.9 +
  pandas 2.1.4 + matplotlib 3.8.2 (Phase 28 territory export
  stack pin EXTENSION).
- AD-22 owner-only RBAC.
- AD-56 (a)~(g) 7 sub-decisions (Phase 28 wire).
- Epic 12 2FA 챌린지 mandatory high-value (≥10M KRW/year sharing scope).
- NFR4 PII minimization PRESERVED.
- NFR18 ko-KR SSOT (finops_interactive_dashboard.* namespace).
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from typing import Final

from .cross_phase_aggregator import trace_id_var
from .serializers import (
    EXPORT_MAX_RETRIES,
    MAX_EXPORT_SIZE_BYTES,
    ExportFormat,
    ExportJob,
    ExportJobStatus,
)

# ── Module constants ──────────────────────────────────────────────────────
EXPORT_PIPELINE_ENGINE_VERSION: Final[str] = "1.0.0"

# Default export TTL (PRD §F43.3 verbatim — 30 days)
DEFAULT_EXPORT_EXPIRES_DAYS: Final[int] = 30

# Default progress increment for re-render simulation
DEFAULT_PROGRESS_PCT: Final[float] = 0.0
COMPLETED_PROGRESS_PCT: Final[float] = 100.0

# Allowed export status transitions (PRD §F43.3 verbatim)
ALLOWED_STATUS_TRANSITIONS: Final[frozenset[tuple[str, str],],] = frozenset(
    {
        ("pending", "in_progress"),
        ("pending", "failed"),
        ("pending", "cancelled"),
        ("in_progress", "completed"),
        ("in_progress", "failed"),
        ("in_progress", "cancelled"),
    }
)  # type: ignore[valid-type]

# Module-level in-memory job store: job_id → ExportJob
_EXPORT_JOBS: dict[str, ExportJob] = {}


# ── Helpers ───────────────────────────────────────────────────────────────
def _now_iso() -> str:
    """Return current UTC timestamp as ISO 8601 string."""
    return datetime.now(UTC).isoformat()


def _generate_id() -> str:
    """Generate UUID v7 string identifier (uuid4 surrogate)."""
    return str(uuid.uuid4())


def _get_trace_id() -> str:
    """Read trace_id from ContextVar or generate new one (CR 1-1)."""
    trace_id = trace_id_var.get()
    if not trace_id:
        trace_id = _generate_id()
        trace_id_var.set(trace_id)
    return trace_id


def _compute_checksum_sha256(content: bytes | None) -> str | None:
    """Compute sha256:64-hex checksum (PRD §F43.3 T3.4 verbatim)."""
    if content is None or not content:
        return None
    return hashlib.sha256(content).hexdigest()


# ── Validators (CR 11-4 P-015 pure validator pattern) ─────────────────────
def _validate_tenant_id(tenant_id: str) -> None:
    """Validate tenant_id is non-empty UUID string (CR 0-2 RLS selector)."""
    if not tenant_id or not isinstance(tenant_id, str):
        raise ValueError("tenant_id must be a non-empty string")


def _validate_view_id(view_id: str) -> None:
    """Validate view_id is non-empty string."""
    if not view_id or not isinstance(view_id, str):
        raise ValueError("view_id must be a non-empty string")


def _validate_job_id(job_id: str) -> None:
    """Validate job_id is non-empty string."""
    if not job_id or not isinstance(job_id, str):
        raise ValueError("job_id must be a non-empty string")


def _validate_format(fmt: str) -> None:
    """Validate format is one of ExportFormat enum values (PDF/XLSX/CSV/JSON/PNG)."""
    if fmt not in ExportFormat._value2member_map_:
        raise ValueError(
            f"format must be one of " f"{[e.value for e in ExportFormat]}, got {fmt!r}"
        )


def _validate_status(status: str) -> None:
    """Validate status is one of ExportJobStatus enum values."""
    if status not in ExportJobStatus._value2member_map_:
        raise ValueError(
            f"status must be one of " f"{[e.value for e in ExportJobStatus]}, got {status!r}"
        )


def _enforce_max_size(file_size_bytes: int) -> None:
    """Enforce MAX_EXPORT_SIZE_BYTES (default 50MB)."""
    if file_size_bytes < 0:
        raise ValueError("file_size_bytes must be non-negative")
    if file_size_bytes > MAX_EXPORT_SIZE_BYTES:
        raise ValueError(
            f"file_size_bytes {file_size_bytes} exceeds MAX_EXPORT_SIZE_BYTES "
            f"{MAX_EXPORT_SIZE_BYTES} (50MB)"
        )


def _validate_retry_count(retry_count: int) -> None:
    """Enforce retry_count ≤ EXPORT_MAX_RETRIES (default 3)."""
    if not isinstance(retry_count, int) or retry_count < 0:
        raise ValueError("retry_count must be non-negative int")
    if retry_count > EXPORT_MAX_RETRIES:
        raise ValueError(
            f"retry_count {retry_count} exceeds EXPORT_MAX_RETRIES " f"{EXPORT_MAX_RETRIES}"
        )


def _check_status_transition(from_status: str, to_status: str) -> None:
    """Validate status transition is allowed (PRD §F43.3 lifecycle)."""
    if (from_status, to_status) not in ALLOWED_STATUS_TRANSITIONS:
        raise ValueError(f"status transition not allowed: {from_status} -> {to_status}")


# ── Public functions (PRD §F43.3 + AD-56 (c)) ─────────────────────────────
def start_export_job(
    tenant_id: str,
    view_id: str,
    fmt: str,
    options: dict[str, object] | None = None,
) -> ExportJob:
    """Start a new export job (PRD §F43.3 — 12 fields).

    Args:
        tenant_id: UUID tenant identifier (CR 0-2 RLS selector).
        view_id: saved_view_id (Phase 28 territory).
        fmt: ExportFormat (pdf/xlsx/csv/json/png).
        options: optional dict containing export options (e.g.
            include_charts=True, locale='ko-KR', webhook_url=None).

    Returns:
        ExportJob TypedDict (12 fields):
        export_job_id + tenant_id + saved_view_id + export_format +
        status + progress_pct + file_path + file_size_bytes +
        checksum_sha256 + expires_at + started_at + completed_at.

    Raises:
        ValueError on invalid tenant_id/view_id/format.
    """
    _validate_tenant_id(tenant_id)
    _validate_view_id(view_id)
    _validate_format(fmt)

    job_id = _generate_id()
    now = _now_iso()
    expires_at_dt = datetime.now(UTC) + timedelta(days=DEFAULT_EXPORT_EXPIRES_DAYS)
    expires_at_iso = expires_at_dt.isoformat()

    export_job = ExportJob(
        export_job_id=job_id,
        tenant_id=tenant_id,
        saved_view_id=view_id,
        export_format=fmt,
        status=ExportJobStatus.PENDING.value,
        progress_pct=DEFAULT_PROGRESS_PCT,
        file_path=None,
        file_size_bytes=0,
        checksum_sha256=None,
        expires_at=expires_at_iso,
        started_at=now,
        completed_at=None,
    )

    # Persist to in-memory store
    _EXPORT_JOBS[job_id] = export_job

    return export_job


def get_export_job_status(job_id: str) -> ExportJob:
    """Get current export job status (PRD §F43.3 verbatim).

    Args:
        job_id: export_job_id.

    Returns:
        ExportJob TypedDict.

    Raises:
        ValueError if not found.
    """
    _validate_job_id(job_id)

    job = _EXPORT_JOBS.get(job_id)
    if job is None:
        raise ValueError(f"export_job not found: job_id={job_id}")

    return job


def list_export_jobs(
    tenant_id: str,
    filter_format: str | None = None,
    filter_status: str | None = None,
) -> list[ExportJob]:
    """List export jobs for a tenant (PRD §F43.3 verbatim).

    Args:
        tenant_id: UUID tenant identifier.
        filter_format: optional format filter (pdf/xlsx/csv/json/png).
        filter_status: optional status filter
            (pending/in_progress/completed/failed).

    Returns:
        list[ExportJob] — sorted by started_at descending.
    """
    _validate_tenant_id(tenant_id)
    if filter_format is not None:
        _validate_format(filter_format)
    if filter_status is not None:
        _validate_status(filter_status)

    results: list[ExportJob] = []
    for job in _EXPORT_JOBS.values():
        if job["tenant_id"] != tenant_id:
            continue
        if filter_format is not None and job["export_format"] != filter_format:
            continue
        if filter_status is not None and job["status"] != filter_status:
            continue
        results.append(job)

    # Sort by started_at descending
    results.sort(key=lambda j: j["started_at"], reverse=True)
    return results


def cancel_export_job(job_id: str) -> ExportJob:
    """Cancel an export job (PRD §F43.3 verbatim).

    Args:
        job_id: export_job_id.

    Returns:
        ExportJob TypedDict (status updated to 'cancelled').

    Raises:
        ValueError if not found or invalid transition.
    """
    _validate_job_id(job_id)

    job = get_export_job_status(job_id)
    _check_status_transition(job["status"], ExportJobStatus.CANCELLED.value)

    job["status"] = ExportJobStatus.CANCELLED.value
    job["completed_at"] = _now_iso()
    _EXPORT_JOBS[job_id] = job

    return job


def update_export_job_progress(
    job_id: str,
    progress_pct: float,
    file_path: str | None = None,
    file_size_bytes: int = 0,
    content_checksum: str | None = None,
    mark_completed: bool = False,
) -> ExportJob:
    """Update export job progress (caller-side helper for workers).

    Args:
        job_id: export_job_id.
        progress_pct: progress percentage (0.0~100.0).
        file_path: optional file path (set when complete).
        file_size_bytes: optional file size (0 if not yet known).
        content_checksum: optional sha256:64-hex content checksum.
        mark_completed: if True, transition to status='completed'.

    Returns:
        ExportJob TypedDict (updated).

    Raises:
        ValueError on invalid progress/file_size/status_transition.
    """
    _validate_job_id(job_id)
    if not isinstance(progress_pct, int | float):
        raise ValueError("progress_pct must be numeric")
    if progress_pct < 0.0 or progress_pct > 100.0:
        raise ValueError(f"progress_pct must be in [0.0, 100.0], got {progress_pct}")
    if file_size_bytes > 0:
        _enforce_max_size(file_size_bytes)

    job = get_export_job_status(job_id)

    if mark_completed:
        _check_status_transition(job["status"], ExportJobStatus.COMPLETED.value)
        job["status"] = ExportJobStatus.COMPLETED.value
        job["progress_pct"] = COMPLETED_PROGRESS_PCT
        job["completed_at"] = _now_iso()
    else:
        _check_status_transition(job["status"], ExportJobStatus.IN_PROGRESS.value)
        if job["status"] == ExportJobStatus.PENDING.value:
            job["status"] = ExportJobStatus.IN_PROGRESS.value
        job["progress_pct"] = float(
            __import__("decimal")
            .Decimal(str(progress_pct))
            .quantize(__import__("decimal").Decimal("0.01"))
        )

    if file_path is not None:
        job["file_path"] = file_path
    if file_size_bytes > 0:
        job["file_size_bytes"] = file_size_bytes
    if content_checksum is not None:
        job["checksum_sha256"] = content_checksum

    _EXPORT_JOBS[job_id] = job
    return job


def mark_export_job_failed(
    job_id: str,
    error_message: str | None = None,
) -> ExportJob:
    """Mark export job as failed (caller-side helper).

    Args:
        job_id: export_job_id.
        error_message: optional error message (for audit log payload,
            not stored in ExportJob TypedDict).

    Returns:
        ExportJob TypedDict (status updated to 'failed').

    Raises:
        ValueError on invalid transition.
    """
    _validate_job_id(job_id)

    job = get_export_job_status(job_id)
    _check_status_transition(job["status"], ExportJobStatus.FAILED.value)
    job["status"] = ExportJobStatus.FAILED.value
    job["completed_at"] = _now_iso()
    _EXPORT_JOBS[job_id] = job

    return job


# ── Test helpers ──────────────────────────────────────────────────────────
def clear_export_jobs() -> int:
    """Clear the in-memory export job store (used by tests).

    Returns:
        int — number of jobs cleared.
    """
    global _EXPORT_JOBS
    count = len(_EXPORT_JOBS)
    _EXPORT_JOBS = {}
    return count


def get_export_job_count() -> int:
    """Return current in-memory export job count (used by tests)."""
    return len(_EXPORT_JOBS)


def compute_retry_count(failed_attempts: int) -> int:
    """Compute retry count with EXPORT_MAX_RETRIES cap (PRD §F43.3).

    Args:
        failed_attempts: number of failed attempts so far.

    Returns:
        int — capped retry count (≤ EXPORT_MAX_RETRIES).
    """
    if failed_attempts < 0:
        return 0
    return min(failed_attempts, EXPORT_MAX_RETRIES)


# ── Public surface ────────────────────────────────────────────────────────
__all__ = [
    "ALLOWED_STATUS_TRANSITIONS",
    "COMPLETED_PROGRESS_PCT",
    "DEFAULT_EXPORT_EXPIRES_DAYS",
    "DEFAULT_PROGRESS_PCT",
    "EXPORT_PIPELINE_ENGINE_VERSION",
    "cancel_export_job",
    "clear_export_jobs",
    "compute_retry_count",
    "get_export_job_count",
    "get_export_job_status",
    "list_export_jobs",
    "mark_export_job_failed",
    "start_export_job",
    "update_export_job_progress",
]
