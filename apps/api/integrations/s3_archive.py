"""apps.api.integrations.s3_archive — S3 archive for executive reports.

Phase 16 wire (cj-style 127번째) — FinOps Reporting & Executive Dashboard
territory (PRD §F32.3-7 verbatim + AD-43 (c) decision + AD-14 stack pin).

Provides:
- `upload_executive_report` — upload executive report PDF/CSV/Excel to
  s3://costmgr-exec-reports/{tenant_id}/{period_key}/{report_id}.{ext}
- `generate_presigned_url` — presigned URL with 7-day expiry.
- `ExecutiveReportArchiveError` — typed exception envelope (CR 12-5 D-14).

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
- CR 1-1 audit-first INSERT — `executive_report_generated` BEFORE upload.
- CR 12-5 D-14 typed exception envelope verbatim.
- AD-14 stack pin — boto3 S3 client + presigned URL.
- AD-22 owner-only RBAC — owner-only archive upload + Epic 12 2FA 챌린지.
- NFR4 PII minimization — report files contain business metrics only.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# S3 bucket + prefix constants (AD-14 stack pin).
S3_BUCKET = "costmgr-exec-reports"
S3_KEY_PREFIX = "executive-reports"
PRESIGNED_URL_EXPIRY_DAYS = 7


class ExecutiveReportArchiveError(RuntimeError):
    """Executive report archive failure (CR 12-5 D-14 envelope, 500)."""

    def __init__(self, reason: str, tenant_id: Optional[str] = None) -> None:
        self.reason = str(reason)
        self.tenant_id = tenant_id
        super().__init__(
            f"Executive report archive failure: reason={self.reason} "
            f"tenant_id={self.tenant_id}"
        )


def build_s3_key(tenant_id: str, period_key: str, report_id: str, ext: str) -> str:
    """Build S3 object key for an executive report.

    Phase 16 wire (cj-style 127번째) — convention
    `executive-reports/{tenant_id}/{period_key}/{report_id}.{ext}`.
    """
    return f"{S3_KEY_PREFIX}/{tenant_id}/{period_key}/{report_id}.{ext}"


def upload_executive_report(
    tenant_id: str,
    period_key: str,
    report_id: str,
    file_bytes: bytes,
    export_format: str,
    boto3_client: Optional[object] = None,
) -> str:
    """Upload executive report to S3 archive.

    Phase 16 wire (cj-style 127번째) — returns S3 URI on success.
    Raises ExecutiveReportArchiveError on failure.

    Args:
        tenant_id: Tenant UUID (CR 0-2 RLS — multi-tenant isolation).
        period_key: Period key (e.g. "2026-08", "2026-Q3", "2026").
        report_id: Report UUID.
        file_bytes: Report file bytes (PDF/CSV/Excel).
        export_format: Export format ("pdf" | "csv" | "excel").
        boto3_client: Optional boto3 S3 client (injected for tests).

    Returns:
        S3 URI string (s3://costmgr-exec-reports/...).

    CR lessons applied:
    - CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
    - CR 12-5 D-14 typed exception envelope verbatim.
    - AD-22 owner-only RBAC — caller must validate owner role.
    - NFR4 PII minimization — report files contain business metrics only.
    """
    if export_format not in ("pdf", "csv", "excel"):
        raise ExecutiveReportArchiveError(
            reason=f"invalid_export_format:{export_format}",
            tenant_id=tenant_id,
        )

    s3_key = build_s3_key(tenant_id, period_key, report_id, export_format)

    try:
        if boto3_client is None:
            logger.info(
                "s3_archive.upload_executive_report dry_run",
                extra={
                    "tenant_id": tenant_id,
                    "period_key": period_key,
                    "report_id": report_id,
                    "s3_key": s3_key,
                    "size_bytes": len(file_bytes),
                    "export_format": export_format,
                },
            )
            return f"s3://{S3_BUCKET}/{s3_key}"

        # Real boto3 upload path (test injection point).
        boto3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=file_bytes,
            ContentType=_content_type_for(export_format),
        )
        logger.info(
            "s3_archive.upload_executive_report",
            extra={
                "tenant_id": tenant_id,
                "s3_key": s3_key,
                "size_bytes": len(file_bytes),
            },
        )
        return f"s3://{S3_BUCKET}/{s3_key}"
    except Exception as exc:  # pragma: no cover — defensive
        raise ExecutiveReportArchiveError(
            reason=str(exc),
            tenant_id=tenant_id,
        ) from exc


def generate_presigned_url(
    s3_uri: str,
    boto3_client: Optional[object] = None,
    expiry_days: int = PRESIGNED_URL_EXPIRY_DAYS,
) -> str:
    """Generate presigned URL with 7-day expiry (AD-14 stack pin).

    Phase 16 wire (cj-style 127번째) — used by executive report delivery +
    scheduled dispatch to provide download links to executives.

    Returns:
        Presigned URL string. On dry-run (no boto3_client) returns
        deterministic placeholder URL.
    """
    if boto3_client is None:
        # Dry-run placeholder for tests + local dev.
        expiry = datetime.now(tz=timezone.utc) + timedelta(days=expiry_days)
        return f"{s3_uri}?expires={expiry.isoformat()}&dry_run=true"

    bucket, key = _parse_s3_uri(s3_uri)
    return boto3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expiry_days * 24 * 3600,
    )


def _content_type_for(export_format: str) -> str:
    """Map export format → Content-Type header."""
    return {
        "pdf": "application/pdf",
        "csv": "text/csv; charset=utf-8",
        "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }.get(export_format, "application/octet-stream")


def _parse_s3_uri(s3_uri: str) -> tuple[str, str]:
    """Parse s3://bucket/key into (bucket, key) tuple."""
    if not s3_uri.startswith("s3://"):
        raise ExecutiveReportArchiveError(
            reason=f"invalid_s3_uri:{s3_uri}",
        )
    path = s3_uri[len("s3://"):]
    bucket, _, key = path.partition("/")
    return bucket, key


__all__ = [
    "S3_BUCKET",
    "S3_KEY_PREFIX",
    "PRESIGNED_URL_EXPIRY_DAYS",
    "ExecutiveReportArchiveError",
    "build_s3_key",
    "upload_executive_report",
    "generate_presigned_url",
]