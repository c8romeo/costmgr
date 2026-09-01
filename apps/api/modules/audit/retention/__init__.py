"""apps.api.modules.audit.retention — Audit log retention policy module.

Phase 6 (cj-style 87번째 epic 연속 정직 회복 atomic wire) — AD-33 (a)~(g).

Sub-module map:
  - `retention_dsl` — `RetentionPolicy` TypedDict + `RetentionClass` Literal
    + `retain()` builder + `parse_retention_policy()` validation + RLS
    auto-isolation (CR 0-2 verbatim) + `DEFAULT_RETENTION_DAYS` constants.
  - `retention_routes` — retention policy CRUD + cold-archive action +
    purge preview + dry-run trigger (FastAPI APIRouter).
  - `erasure` — GDPR Article 17 right to erasure (`POST /api/v1/audit-log/
    erase`) + owner-only RBAC AD-22 + PII masking via AES-256-GCM NFR6.

Industry-agnostic (CR 12-1 L4 precedent) — all 4 industries get
AUDIT_LOG_RETENTION capability, gating the routes here.
"""

from __future__ import annotations

from apps.api.modules.audit.retention.erasure import (  # noqa: F401
    AuditLogPiiErasureForbiddenError,
    AuditLogPiiErasureNotFoundError,
    request_audit_log_erasure,
)

# Re-exports for `from apps.api.modules.audit.retention import ...`
from apps.api.modules.audit.retention.retention_dsl import (  # noqa: F401
    DEFAULT_RETENTION_DAYS,
    AuditLogRetentionPolicyInvalidError,
    RetentionClass,
    RetentionPolicy,
    parse_retention_policy,
    retain,
)
