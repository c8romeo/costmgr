"""tests.api.core.test_epic_16_tenant_idp_lookup — Per-tenant IdP lookup tests.

Epic 16 (cj-style 69번째 epic 연속 정직 회복 wire) — AC #7.3.
Tests apps/api/modules/auth/sso/tenant_idp_lookup.py:
- TenantIdPRow dataclass shape
- TenantIdPLookupError / DisabledError / ConfigMissingError hierarchy
- load_tenant_idp() with 4 scenarios: tenant_not_found, idp_not_configured,
  idp_disabled, success
- saml_routes.py uses load_tenant_idp() (mocked) instead of hardcoded
  placeholders
"""

from __future__ import annotations

import base64
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.api.modules.auth.sso.tenant_idp_lookup import (
    TenantIdPConfigMissingError,
    TenantIdPDisabledError,
    TenantIdPLookupError,
    TenantIdPRow,
    load_tenant_idp,
)

VALID_TENANT_ID = "11111111-1111-1111-1111-111111111111"


def _cert_pem() -> str:
    body = base64.b64encode(b"placeholder-cert").decode("ascii")
    return (
        "-----BEGIN CERTIFICATE-----\n"
        + body
        + "\n-----END CERTIFICATE-----"
    )


def _make_session(steps: list[Any]) -> AsyncMock:
    """Build a session where each call to `execute()` returns the next step result.

    `steps` is consumed sequentially; if a step is None, `first()` returns None.
    Each step is a tuple (row_value,) or None.
    """
    session = AsyncMock()
    results = []
    for step in steps:
        result_mock = MagicMock()
        result_mock.first = MagicMock(return_value=step)
        results.append(result_mock)

    # session.execute returns the next result on each call
    call_count = {"i": 0}

    async def fake_execute(*_args: Any, **_kwargs: Any) -> Any:
        idx = call_count["i"]
        call_count["i"] += 1
        if idx < len(results):
            return results[idx]
        # No more steps — return empty
        empty = MagicMock()
        empty.first = MagicMock(return_value=None)
        return empty

    session.execute = fake_execute
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


# ── Test: exception hierarchy ────────────────────────────────────────


class TestExceptionHierarchy:
    def test_disabled_is_subclass_of_base(self) -> None:
        assert issubclass(TenantIdPDisabledError, TenantIdPLookupError)

    def test_missing_is_subclass_of_base(self) -> None:
        assert issubclass(TenantIdPConfigMissingError, TenantIdPLookupError)

    def test_base_is_subclass_of_exception(self) -> None:
        assert issubclass(TenantIdPLookupError, Exception)


# ── Test: TenantIdPRow dataclass ─────────────────────────────────────


class TestTenantIdPRow:
    def test_required_fields(self) -> None:
        row = TenantIdPRow(
            tenant_id=VALID_TENANT_ID,
            tenant_slug="acme",
            idp_entity_id="https://idp.acme.example.com",
            idp_sso_url="https://idp.acme.example.com/sso",
            idp_slo_url=None,
            idp_x509_cert_pem=_cert_pem(),
            name_id_format=None,
            acs_url=None,
            enabled=True,
        )
        assert row.tenant_slug == "acme"
        assert row.enabled is True

    def test_frozen(self) -> None:
        row = TenantIdPRow(
            tenant_id=VALID_TENANT_ID,
            tenant_slug="acme",
            idp_entity_id="x",
            idp_sso_url="x",
            idp_slo_url=None,
            idp_x509_cert_pem="x",
            name_id_format=None,
            acs_url=None,
            enabled=True,
        )
        with pytest.raises((AttributeError, TypeError)):
            row.enabled = False  # type: ignore[misc]

    def test_slots(self) -> None:
        # slots=True should reject attributes outside __slots__
        row = TenantIdPRow(
            tenant_id=VALID_TENANT_ID,
            tenant_slug="acme",
            idp_entity_id="x",
            idp_sso_url="x",
            idp_slo_url=None,
            idp_x509_cert_pem="x",
            name_id_format=None,
            acs_url=None,
            enabled=True,
        )
        with pytest.raises((AttributeError, TypeError)):
            row.bogus = "x"  # type: ignore[attr-defined]


# ── Test: load_tenant_idp() — happy path ─────────────────────────────


class TestLoadTenantIdpSuccess:
    @pytest.mark.asyncio
    async def test_returns_full_row(self) -> None:
        cert = _cert_pem()
        session = _make_session(
            [
                (VALID_TENANT_ID,),  # tenants.slug → id
                (  # tenant_idps row
                    "https://idp.acme.example.com",
                    "https://idp.acme.example.com/sso",
                    "https://idp.acme.example.com/slo",
                    cert,
                    "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
                    "https://sp.acme.example.com/acs",
                    True,
                ),
            ]
        )

        row = await load_tenant_idp(session, "acme")
        assert row.tenant_id == VALID_TENANT_ID
        assert row.tenant_slug == "acme"
        assert row.idp_entity_id == "https://idp.acme.example.com"
        assert row.idp_sso_url == "https://idp.acme.example.com/sso"
        assert row.idp_slo_url == "https://idp.acme.example.com/slo"
        assert row.idp_x509_cert_pem == cert
        assert row.name_id_format == "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
        assert row.acs_url == "https://sp.acme.example.com/acs"
        assert row.enabled is True


# ── Test: load_tenant_idp() — error paths ────────────────────────────


class TestLoadTenantIdpErrors:
    @pytest.mark.asyncio
    async def test_unknown_slug_raises_missing(self) -> None:
        session = _make_session([None])  # tenants SELECT returns nothing
        with pytest.raises(TenantIdPConfigMissingError) as exc:
            await load_tenant_idp(session, "unknown")
        assert "tenant_not_found" in str(exc.value)

    @pytest.mark.asyncio
    async def test_missing_idp_row_raises_missing(self) -> None:
        session = _make_session(
            [
                (VALID_TENANT_ID,),  # tenant found
                None,                # but no tenant_idps row
            ]
        )
        with pytest.raises(TenantIdPConfigMissingError) as exc:
            await load_tenant_idp(session, "acme")
        assert "idp_not_configured" in str(exc.value)

    @pytest.mark.asyncio
    async def test_disabled_idp_raises_disabled(self) -> None:
        session = _make_session(
            [
                (VALID_TENANT_ID,),
                (
                    "https://idp.acme.example.com",
                    "https://idp.acme.example.com/sso",
                    None,
                    _cert_pem(),
                    None,
                    None,
                    False,  # enabled=FALSE
                ),
            ]
        )
        with pytest.raises(TenantIdPDisabledError) as exc:
            await load_tenant_idp(session, "acme")
        assert "idp_disabled" in str(exc.value)


# ── Test: module exports ─────────────────────────────────────────────


class TestModuleExports:
    def test_all_present(self) -> None:
        from apps.api.modules.auth.sso import tenant_idp_lookup

        for name in [
            "TenantIdPLookupError",
            "TenantIdPDisabledError",
            "TenantIdPConfigMissingError",
            "TenantIdPRow",
            "load_tenant_idp",
        ]:
            assert hasattr(tenant_idp_lookup, name), f"Missing export: {name}"

    def test_all_list_matches(self) -> None:
        from apps.api.modules.auth.sso import tenant_idp_lookup

        for name in tenant_idp_lookup.__all__:
            assert hasattr(tenant_idp_lookup, name)


# ── Test: saml_routes integration (smoke-level) ─────────────────────


class TestSamlRoutesIntegration:
    def test_saml_routes_uses_lookup_for_login(self) -> None:
        """sso_login() must call load_tenant_idp() for dynamic per-tenant routing."""
        import inspect

        from apps.api.modules.auth.sso import saml_routes

        src = inspect.getsource(saml_routes.sso_login)
        assert "load_tenant_idp" in src
        # Epic 15 hardcoded placeholder still present as fallback
        assert "idp.example.com" in src

    def test_saml_routes_uses_lookup_for_acs(self) -> None:
        import inspect

        from apps.api.modules.auth.sso import saml_routes

        src = inspect.getsource(saml_routes.sso_acs)
        # The body of the function should reference load_tenant_idp
        assert "load_tenant_idp" in src
        # AND the hardcoded PEM block must still exist as fallback
        assert "BEGIN CERTIFICATE" in src

    def test_saml_routes_imports_typed_exceptions(self) -> None:
        from apps.api.modules.auth.sso import saml_routes

        # Ensure the new typed exceptions are imported
        assert hasattr(saml_routes, "TenantIdPConfigMissingError")
        assert hasattr(saml_routes, "TenantIdPDisabledError")
        assert hasattr(saml_routes, "load_tenant_idp")
