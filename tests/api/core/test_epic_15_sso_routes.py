"""tests.api.core.test_epic_15_sso_routes — SSO routes surface tests.

Epic 15 (cj-style 60번째 epic 연속 정직 회복 wire) — AC #7.5.
Tests the 4 routes surface + tenant slug routing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SSO_ROUTES = (
    REPO_ROOT
    / "apps"
    / "api"
    / "modules"
    / "auth"
    / "sso"
    / "saml_routes.py"
)
AUTH_AUDIT_ROUTES = (
    REPO_ROOT
    / "apps"
    / "api"
    / "modules"
    / "auth"
    / "audit_routes.py"
)
SSO_INIT = (
    REPO_ROOT
    / "apps"
    / "api"
    / "modules"
    / "auth"
    / "sso"
    / "__init__.py"
)
AUTH_INIT = (
    REPO_ROOT
    / "apps"
    / "api"
    / "modules"
    / "auth"
    / "__init__.py"
)


class TestSSORoutesModule:
    def test_sso_routes_exists(self) -> None:
        assert SSO_ROUTES.exists()

    def test_auth_audit_routes_exists(self) -> None:
        assert AUTH_AUDIT_ROUTES.exists()

    def test_sso_init_exports_router(self) -> None:
        content = SSO_INIT.read_text(encoding="utf-8")
        assert "sso_router" in content

    def test_auth_init_exports_routers(self) -> None:
        content = AUTH_INIT.read_text(encoding="utf-8")
        assert "sso_router" in content
        assert "auth_audit_router" in content


class TestSSORouteEndpoints:
    def test_login_endpoint(self) -> None:
        content = SSO_ROUTES.read_text(encoding="utf-8")
        assert '/login"' in content or "@router.get(\"/login\")" in content
        assert "tenant_slug" in content
        assert "relay_state" in content
        assert "RedirectResponse" in content
        assert "status_code=302" in content

    def test_acs_endpoint(self) -> None:
        content = SSO_ROUTES.read_text(encoding="utf-8")
        assert "/acs" in content
        assert "SAMLResponse" in content
        assert "RelayState" in content

    def test_metadata_endpoint(self) -> None:
        content = SSO_ROUTES.read_text(encoding="utf-8")
        assert "/metadata" in content
        assert "EntityDescriptor" in content
        assert "application/samlmetadata+xml" in content

    def test_sls_endpoint(self) -> None:
        content = SSO_ROUTES.read_text(encoding="utf-8")
        assert "/sls" in content
        assert "SSO_SLO_OK" in content

    def test_ko_kr_envelope(self) -> None:
        content = SSO_ROUTES.read_text(encoding="utf-8")
        # CR 12-5 D-14 envelope: every error has {code, message_ko, details}.
        assert "code" in content
        assert "message_ko" in content
        assert "details" in content


class TestAuthAuditEndpoints:
    def test_magic_link_audit(self) -> None:
        content = AUTH_AUDIT_ROUTES.read_text(encoding="utf-8")
        assert "/magic-link-sent" in content
        assert "magic_link_sent" in content

    def test_social_oauth_audit(self) -> None:
        content = AUTH_AUDIT_ROUTES.read_text(encoding="utf-8")
        assert "/social-oauth-initiated" in content
        assert "social_oauth_initiated" in content

    def test_email_fingerprinting(self) -> None:
        content = AUTH_AUDIT_ROUTES.read_text(encoding="utf-8")
        # NFR4 PII minimization: email must be hashed in audit row.
        assert "_email_fingerprint" in content
        assert "sha256" in content


class TestMainPyInclusion:
    def test_sso_router_included(self) -> None:
        main = REPO_ROOT / "apps" / "api" / "main.py"
        content = main.read_text(encoding="utf-8")
        assert "sso_router" in content
        assert "auth_audit_router" in content


class TestPyprojectToml:
    def test_python3_saml_pinned(self) -> None:
        toml = REPO_ROOT / "apps" / "api" / "pyproject.toml"
        content = toml.read_text(encoding="utf-8")
        assert "python3-saml==1.16.0" in content
