"""apps.api.integrations — third-party service integrations.

Phase 16 wire (cj-style 127번째) — FinOps Reporting & Executive Dashboard
territory (PRD §F32.3 verbatim + AD-43 (c) decision).

This package centralises third-party service integrations including:
- `s3_archive` — S3 archive upload for executive reports (Phase 16
  EXTENSION) + presigned URL generation.

AD-14 stack pin — boto3 (S3 client) + presigned URL 7-day expiry.
"""
from __future__ import annotations

__all__ = ["s3_archive"]