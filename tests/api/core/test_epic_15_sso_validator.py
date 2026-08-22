"""tests.api.core.test_epic_15_sso_validator — SAML 2.0 validator tests.

Epic 15 (cj-style 60번째 epic 연속 정직 회복 wire) — AC #7.3.
Tests the SAML response validation surface (signature, timestamps,
audience, destination, in-response-to, relay state).
"""

from __future__ import annotations

import base64
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SAML_VALIDATOR = (
    REPO_ROOT
    / "apps"
    / "api"
    / "modules"
    / "auth"
    / "sso"
    / "saml_validator.py"
)


@pytest.fixture(scope="module")
def validator_module():
    """Import the validator module (skip if python3-saml is unavailable)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "saml_validator", str(SAML_VALIDATOR)
    )
    if spec is None or spec.loader is None:
        pytest.skip("saml_validator module not loadable")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"saml_validator import failed: {exc}")
    return module


def _build_saml_response(
    *,
    issuer: str = "https://idp.example.com",
    destination: str = "https://api.costmgr.example.com/api/v1/auth/sso/acs?tenant=acme",
    in_response_to: str = "_request_id_123",
    not_before: str | None = "2026-01-01T00:00:00Z",
    not_on_or_after: str | None = "2099-12-31T23:59:59Z",
    audience: str = "costmgr-sp",
    name_id: str = "user-123",
    email: str = "user@example.com",
    include_signature: bool = True,
) -> str:
    """Build a minimal SAML 2.0 response XML and base64-encode it."""
    sig = "<ds:Signature xmlns:ds='http://www.w3.org/2000/09/xmldsig#'><ds:SignedInfo/></ds:Signature>" if include_signature else ""
    not_before_xml = f' NotBefore="{not_before}"' if not_before else ""
    not_after_xml = f' NotOnOrAfter="{not_on_or_after}"' if not_on_or_after else ""
    xml = f"""<?xml version="1.0"?>
<samlp:Response xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
                xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
                Destination="{destination}"
                InResponseTo="{in_response_to}">
  {sig}
  <saml:Issuer>{issuer}</saml:Issuer>
  <saml:Assertion ID="_assertion_1">
    <saml:Conditions{not_before_xml}{not_after_xml}>
      <saml:AudienceRestriction>
        <saml:Audience>{audience}</saml:Audience>
      </saml:AudienceRestriction>
    </saml:Conditions>
    <saml:Subject>
      <saml:NameID>{name_id}</saml:NameID>
    </saml:Subject>
    <saml:AttributeStatement>
      <saml:Attribute Name="email">
        <saml:AttributeValue>{email}</saml:AttributeValue>
      </saml:Attribute>
    </saml:AttributeStatement>
  </saml:Assertion>
</samlp:Response>"""
    return base64.b64encode(xml.encode("utf-8")).decode("ascii")


class TestValidateSamlResponse:
    def test_valid_response(self, validator_module) -> None:
        saml_b64 = _build_saml_response()
        ctx = validator_module.SAMLValidationContext(
            acs_url="https://api.costmgr.example.com/api/v1/auth/sso/acs?tenant=acme",
            sp_entity_id="costmgr-sp",
            expected_audience="costmgr-sp",
            expected_in_response_to="_request_id_123",
        )
        result = validator_module.validate_saml_response(
            saml_response_b64=saml_b64,
            idp_cert_pem="-----BEGIN CERTIFICATE-----\nMIIB\n-----END CERTIFICATE-----",
            ctx=ctx,
        )
        assert result.email == "user@example.com"
        assert result.name_id == "user-123"
        assert result.issuer == "https://idp.example.com"

    def test_invalid_base64(self, validator_module) -> None:
        ctx = validator_module.SAMLValidationContext(
            acs_url="https://api.costmgr.example.com/api/v1/auth/sso/acs",
            sp_entity_id="costmgr-sp",
            expected_audience="costmgr-sp",
            expected_in_response_to=None,
        )
        with pytest.raises(validator_module.SAMLInvalidResponseError):
            validator_module.validate_saml_response(
                saml_response_b64="!!not base64!!",
                idp_cert_pem="",
                ctx=ctx,
            )

    def test_missing_signature(self, validator_module) -> None:
        saml_b64 = _build_saml_response(include_signature=False)
        ctx = validator_module.SAMLValidationContext(
            acs_url="https://api.costmgr.example.com/api/v1/auth/sso/acs?tenant=acme",
            sp_entity_id="costmgr-sp",
            expected_audience="costmgr-sp",
            expected_in_response_to="_request_id_123",
        )
        with pytest.raises(validator_module.SAMLSignatureFailedError):
            validator_module.validate_saml_response(
                saml_response_b64=saml_b64,
                idp_cert_pem="",
                ctx=ctx,
            )

    def test_audience_mismatch(self, validator_module) -> None:
        saml_b64 = _build_saml_response(audience="wrong-audience")
        ctx = validator_module.SAMLValidationContext(
            acs_url="https://api.costmgr.example.com/api/v1/auth/sso/acs?tenant=acme",
            sp_entity_id="costmgr-sp",
            expected_audience="costmgr-sp",
            expected_in_response_to="_request_id_123",
        )
        with pytest.raises(validator_module.SAMLAudienceMismatchError):
            validator_module.validate_saml_response(
                saml_response_b64=saml_b64,
                idp_cert_pem="",
                ctx=ctx,
            )

    def test_in_response_to_mismatch(self, validator_module) -> None:
        saml_b64 = _build_saml_response(in_response_to="different_id")
        ctx = validator_module.SAMLValidationContext(
            acs_url="https://api.costmgr.example.com/api/v1/auth/sso/acs?tenant=acme",
            sp_entity_id="costmgr-sp",
            expected_audience="costmgr-sp",
            expected_in_response_to="_request_id_123",
        )
        with pytest.raises(validator_module.SAMLInResponseToMissingError):
            validator_module.validate_saml_response(
                saml_response_b64=saml_b64,
                idp_cert_pem="",
                ctx=ctx,
            )

    def test_expired(self, validator_module) -> None:
        saml_b64 = _build_saml_response(
            not_before="2020-01-01T00:00:00Z",
            not_on_or_after="2020-12-31T23:59:59Z",
        )
        ctx = validator_module.SAMLValidationContext(
            acs_url="https://api.costmgr.example.com/api/v1/auth/sso/acs?tenant=acme",
            sp_entity_id="costmgr-sp",
            expected_audience="costmgr-sp",
            expected_in_response_to="_request_id_123",
        )
        with pytest.raises(validator_module.SAMLExpiredError):
            validator_module.validate_saml_response(
                saml_response_b64=saml_b64,
                idp_cert_pem="",
                ctx=ctx,
            )


class TestRelayState:
    def test_decode_valid(self, validator_module) -> None:
        original = "/dashboard"
        encoded = base64.urlsafe_b64encode(original.encode("utf-8")).decode("ascii")
        assert validator_module.decode_relay_state(encoded) == original

    def test_decode_empty(self, validator_module) -> None:
        assert validator_module.decode_relay_state("") == ""
        assert validator_module.decode_relay_state(None) == ""

    def test_decode_invalid(self, validator_module) -> None:
        with pytest.raises(validator_module.SAMLRelayStateDecodeError):
            validator_module.decode_relay_state("!!not base64!!")
