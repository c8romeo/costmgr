"""apps.api.modules.auth.sso — SSO enterprise SAML module (Epic 15).

Re-exports the SAML routes + helpers for the main app to include.
"""

from __future__ import annotations

from apps.api.modules.auth.sso.saml_routes import router as sso_router

__all__ = ["sso_router"]
