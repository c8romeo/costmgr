"""apps.api.modules.m10_ai.config — M10 AI extraction module configuration.

Story 1.3 — Task 2.2.

Why a config module (not constants inlined into the adapter):
- The same constants are referenced from (a) the fake adapter for tests,
  (b) the real adapter (when wired), (c) the service layer for validation,
  (d) the retention cron for the 90-day window. A single module keeps
  them in sync.
- The fake adapter reads `DOCUMENT_EXTRACTION_MODEL` so test fixtures
  match production behavior at the schema level (only the provider
  call differs).

Cross-language note:
- The TS mirror is `apps/web/lib/extraction-config.ts` (Story 1.3
  follow-up). Drift is caught by `tests/integration/test_badge_consistency.py`
  reading the keys from both files via regex.
"""

from __future__ import annotations

from typing import Final

# ── Provider selection ───────────────────────────────────────
# Story 1.3 — MVP provider. The Anthropic SDK call is gated by the
# [STACK BUMP] workflow (Story 0.3 lesson). When unset (default in
# tests / dev), `claude_vision.py` raises `AIProviderNotConfiguredError`
# at call time and the service falls back to the fake adapter.
DOCUMENT_EXTRACTION_MODEL: Final[str] = "claude-3-5-sonnet-20241022"

# Default Anthropic Messages API timeout (seconds). Provider calls that
# exceed this are mapped to `error_code='AI_PROVIDER_TIMEOUT'`.
PROVIDER_TIMEOUT_S: Final[float] = 28.0

# ── Upload limits (AD-15: bounded by tenant tier; MVP is uniform) ──
# 8 MiB — generous for a single 사업자등록증 image (typically 200 KiB-2 MiB)
# and small enough to fit a single PDF business license with all pages
# scanned. Tuned for Korean SMB onboarding, not enterprise.
MAX_UPLOAD_BYTES: Final[int] = 8 * 1024 * 1024

# Allowed MIME types. Image MIME uses `image/` prefix; PDF is the only
# document type MVP allows. Adding new types requires updating the
# ALLOWED_MIME set + the TS mirror + the fake adapter's per-MIME fake.
ALLOWED_MIME: Final[frozenset[str]] = frozenset(
    {
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/webp",
    }
)

# Cap PDF processing at this many pages (counted before extraction). The
# fake adapter ignores this; real adapter must enforce or be paginated.
MAX_PDF_PAGES: Final[int] = 10

# ── Retention policy (PRD §F0.4 / privacy) ──────────────────
# 90 days. Documented in `docs/operations/document-retention.md` and
# enforced by `apps/api/jobs/document_retention.py` (Story 1.3 T1.3).
DOCUMENT_RETENTION_DAYS: Final[int] = 90

# ── Confidence thresholds ───────────────────────────────────
# `REVIEW_THRESHOLD` (0.70) lives in `apps/api/core/confidence.py`
# — imported here for `service.py` convenience but NOT redeclared.
# We re-export so callers don't need a second import path.
from apps.api.core.confidence import REVIEW_THRESHOLD  # noqa: E402,F401

# Per-field evidence text cap. The adapter truncates evidence.text to
# this length before it lands in `input_drafts.evidence` JSONB. Defends
# against prompt-injection "evidence" that includes a multi-page
# sensitive blob.
EVIDENCE_TEXT_MAX_CHARS: Final[int] = 200

# ── Idempotency-Key retention ────────────────────────────────
# The M0 / M10 idempotency table keeps dedupe state for this many
# hours. After expiry, a duplicate POST is treated as a fresh upload.
# Stored in `ai_documents.idempotency_key` + created_at index.
IDEMPOTENCY_KEY_TTL_HOURS: Final[int] = 24

# ── Provider feature flag (operations) ──────────────────────
# When `false`, the real `claude_vision.py` adapter raises
# `AIProviderNotConfiguredError`. Tests/dev/CI set this to False.
# Production sets it to True after the [STACK BUMP] wires the SDK.
import os

AI_PROVIDER_ENABLED: Final[bool] = (
    os.getenv("AI_PROVIDER_ENABLED", "false").lower() == "true"
)
