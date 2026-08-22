"""apps.api.modules.auth — Authentication module (Epic 15).

Re-exports the SSO enterprise SAML router + auth audit endpoint
for the main app to include.
"""

from __future__ import annotations

from apps.api.modules.auth.audit_routes import router as auth_audit_router
from apps.api.modules.auth.sso import sso_router

__all__ = ["sso_router", "auth_audit_router"]
