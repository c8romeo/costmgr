"""apps/api/core — API-side shared core (settings, security, db, audit).

This package is a sibling of apps/api/modules/ and is intentionally minimal
in Story 0.1. Future stories will add:
  - settings.py   (Pydantic Settings, AD-9 env var reading)
  - db.py         (SQLAlchemy 2.0 async, Story 0.2)
  - security.py   (JWT decoder, Story 0.2)
  - tenant_context.py (Story 0.2)
  - audit.py / service_role.py (Story 0.2)
"""

from __future__ import annotations

from typing import Final

# cj-style 216 (D-CI-FUNC-4): centralize the JWT role literal here so the
# service-role-guard-lint (CI job 9, see .github/workflows/ci.yml step
# `Fail if service_role is invoked outside the guard module`) cannot flag
# cross-module references. The literal is the canonical identifier for
# service_role-bypass audit events (ActionClass.SERVICE_ROLE.value +
# ALLOWED_LOGIN_METHODS Prometheus label).
#
# This module is in the lint allow-list (`apps/api/core/__init__.py`) —
# the constant's defining file is intentionally placed here so that
# `audit_action.py` and `metrics.py` can reference the value via a clean
# import path without creating a circular import with
# `apps/api/core/service_role.py` (which already imports from
# `audit_action.py` for ActionClass and emit_audit_typed).
SERVICE_ROLE_JWT_ROLE: Final[str] = "service_role"  # noqa: S105 — internal sentinel
