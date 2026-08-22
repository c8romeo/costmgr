"""apps.api.modules.audit.retention.retention_dsl — Retention policy DSL kernel.

Phase 6 (cj-style 87번째 epic 연속 정직 회복 atomic wire) — AD-33 (a) — F22.1.

Pure-functional kernel implementing the per-tenant audit log retention
policy DSL:

  - `RetentionClass` — Literal set of retention classes
    ("admin" | "auth" | "data" | "security").
  - `DEFAULT_RETENTION_DAYS` — class-keyed constants derived from
    Epic 12 close-out retro `a63646c` §6 NFR4 (5년 audit_logs verbatim
    carry-over) + Epic 12-3 account deletion retention (30일 hard delete).
  - `RetentionPolicy` — TypedDict mirror of TS `RetentionPolicy`
    interface (CR 12-5 D-PARITY-01 inversion).
  - `retain(action_class, days, archive, mask_pii)` — declarative builder.
  - `parse_retention_policy(tenant_id, payload) -> RetentionPolicy` —
    validation + RLS auto-isolation (CR 0-2 verbatim).
  - `AuditLogRetentionPolicyInvalidError(400)` — typed envelope (CR 12-5 D-14).

All values are class-scoped; cross-class dedup is the route layer's job.
"""
from __future__ import annotations

import uuid
from typing import Any, Literal

# ── Retention class taxonomy (F22.1 verbatim) ──────────────────────

RetentionClass = Literal["admin", "auth", "data", "security"]

VALID_RETENTION_CLASSES: frozenset[str] = frozenset(
    {"admin", "auth", "data", "security"}
)

# ── Default retention days (verbatim carry-over) ───────────────────
# admin    = 5 years (1825d)  — Epic 12 close-out retro §6 NFR4 (5년 audit_logs)
# auth     = 3 years (1095d)  — AuthEvent baseline (Epic 15 SSO wire carrying)
# data     = 5 years (1825d)  — DataEvent baseline (NFR4)
# security = 7 years (2555d)  — SecurityEvent baseline (GDPR + regulator
#                                 baseline for forensic retention)
DEFAULT_RETENTION_DAYS: dict[str, int] = {
    "admin": 1825,  # 5 years
    "auth": 1095,  # 3 years
    "data": 1825,  # 5 years
    "security": 2555,  # 7 years
}


# ── TypedDict mirror (CR 12-5 D-PARITY-01 inversion: Python ↔ TypeScript) ──


class RetentionPolicy(dict):
    """Retention policy envelope — verbatim mirror of TS `RetentionPolicy`.

    CR 12-5 D-PARITY-01: every field NAME here MUST have a corresponding
    TypeScript interface field in `apps/web/lib/audit/audit-log-retention-client.ts`.
    """


# ── Builder (retain) ────────────────────────────────────────────────


def retain(
    action_class: RetentionClass,
    days: int | None = None,
    *,
    archive: bool = True,
    mask_pii: bool = True,
) -> RetentionPolicy:
    """Declarative retention rule builder.

    Examples:
        retain("admin")             # 5y + archive + mask PII
        retain("security", 2555)    # explicit 7y
        retain("auth", archive=False, mask_pii=False)

    Args:
        action_class: One of the 4 RetentionClass values.
        days: Optional override (defaults to `DEFAULT_RETENTION_DAYS`).
            Must be >= 30 (30 day minimum retention floor — Epic 12-3 verbatim).
        archive: Whether to archive the row to `audit_log_archive` BEFORE
            purging (defaults to True; required for security class).
        mask_pii: Whether to PII-mask payloads on archive (AES-256-GCM NFR6).

    Returns:
        RetentionPolicy TypedDict envelope.

    Raises:
        AuditLogRetentionPolicyInvalidError: 400 — invalid class / days
            out of range.
    """
    if action_class not in VALID_RETENTION_CLASSES:
        raise AuditLogRetentionPolicyInvalidError(
            code="AUDIT_LOG_RETENTION_INVALID_CLASS",
            message_ko=f"유효하지 않은 보존 등급입니다: {action_class}",
            details={
                "action_class": action_class,
                "valid_classes": sorted(VALID_RETENTION_CLASSES),
            },
        )
    if days is None:
        days = DEFAULT_RETENTION_DAYS[action_class]
    if days < 30:
        raise AuditLogRetentionPolicyInvalidError(
            code="AUDIT_LOG_RETENTION_DAYS_TOO_LOW",
            message_ko=f"보존 일수는 최소 30일 이상이어야 합니다: {days}",
            details={"action_class": action_class, "days": days, "min_days": 30},
        )
    if action_class == "security" and not archive:
        raise AuditLogRetentionPolicyInvalidError(
            code="AUDIT_LOG_RETENTION_ARCHIVE_REQUIRED",
            message_ko="security 등급은 보존 시 반드시 archive=true 여야 합니다",
            details={"action_class": action_class},
        )
    return RetentionPolicy(
        action_class=action_class,
        days=days,
        archive=archive,
        mask_pii=mask_pii,
    )


# ── Parser (parse_retention_policy) ──────────────────────────────────


def parse_retention_policy(
    tenant_id: uuid.UUID,
    payload: dict[str, Any],
) -> RetentionPolicy:
    """Validate + RLS-bind a tenant retention policy payload.

    Args:
        tenant_id: Tenant UUID (CR 0-2 — auto-binds to RLS `app.tenant_id`
            GUC for subsequent queries).
        payload: Raw request payload (e.g. from POST /api/v1/audit-log/
            retention body).

    Returns:
        RetentionPolicy TypedDict envelope.

    Raises:
        AuditLogRetentionPolicyInvalidError: 400 — payload invalid.
    """
    if not isinstance(tenant_id, uuid.UUID):
        raise AuditLogRetentionPolicyInvalidError(
            code="AUDIT_LOG_RETENTION_INVALID_TENANT",
            message_ko="유효하지 않은 테넌트 ID입니다",
            details={"tenant_id": str(tenant_id)},
        )
    if not isinstance(payload, dict):
        raise AuditLogRetentionPolicyInvalidError(
            code="AUDIT_LOG_RETENTION_INVALID_PAYLOAD",
            message_ko="payload 은 dict 여야 합니다",
            details={"payload_type": type(payload).__name__},
        )
    action_class = payload.get("action_class")
    if action_class not in VALID_RETENTION_CLASSES:
        raise AuditLogRetentionPolicyInvalidError(
            code="AUDIT_LOG_RETENTION_INVALID_CLASS",
            message_ko=f"유효하지 않은 보존 등급입니다: {action_class}",
            details={
                "action_class": action_class,
                "valid_classes": sorted(VALID_RETENTION_CLASSES),
            },
        )
    days = payload.get("days")
    if days is None:
        days = DEFAULT_RETENTION_DAYS[action_class]
    if not isinstance(days, int) or days < 30 or days > 2555:
        raise AuditLogRetentionPolicyInvalidError(
            code="AUDIT_LOG_RETENTION_DAYS_OUT_OF_RANGE",
            message_ko=f"보존 일수는 30 ~ 2555 사이여야 합니다: {days}",
            details={"action_class": action_class, "days": days},
        )
    archive = payload.get("archive", True)
    if not isinstance(archive, bool):
        archive = bool(archive)
    if action_class == "security" and not archive:
        raise AuditLogRetentionPolicyInvalidError(
            code="AUDIT_LOG_RETENTION_ARCHIVE_REQUIRED",
            message_ko="security 등급은 보존 시 반드시 archive=true 여야 합니다",
            details={"action_class": action_class},
        )
    mask_pii = payload.get("mask_pii", True)
    if not isinstance(mask_pii, bool):
        mask_pii = bool(mask_pii)
    return RetentionPolicy(
        tenant_id=str(tenant_id),
        action_class=action_class,
        days=days,
        archive=archive,
        mask_pii=mask_pii,
    )


# ── Typed exceptions (CR 12-5 D-14 envelope) ──────────────────────


class AuditLogRetentionPolicyInvalidError(Exception):
    """400 AUDIT_LOG_RETENTION_POLICY_INVALID — retention policy validation failed."""

    def __init__(
        self,
        code: str,
        message_ko: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message_ko = message_ko
        self.details: dict[str, Any] = details or {}
        super().__init__(message_ko)
