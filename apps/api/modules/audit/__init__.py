"""apps.api.modules.audit — Audit log viewer & activity stream module (Epic 17).

Epic 17 (cj-style 82번째 epic 연속 정직 회복 atomic wire) — T1 + T4 + T5.

This module centralizes audit log read access for the owner/admin
audit log viewer UI (`/api/v1/audit-log/*`) + the all-members activity
stream UI (`/api/v1/activity`) + the cross-region read-replica query
path (Phase 5 carry-over) + CSV export (`/api/v1/audit-log/export`).

Sub-modules:
  - `audit_log_query` — query / count / get_entry / activity stream
  - `audit_log_export` — CSV export streaming response
  - `audit_log_routes` — FastAPI router for the 5 endpoints

All query functions enforce:
  - RLS auto-isolation via tenant_id GUC (CR 0-2 verbatim)
  - owner/admin role gate on audit-log entries (AD-22 verbatim)
  - capability gate AUDIT_LOG_VIEW (CR 12-5 D-GATE-01 inversion)
  - audit-first INSERT `audit_log_exported` on CSV export (CR 1-1 verbatim)
  - cross-region read-replica routing with primary fallback (Phase 5 carry-over)

AD-11: this module imports only stdlib + FastAPI/SQLAlchemy/Pydantic.
"""
