"""tests.api.core.test_epic_16_idp_metadata_validator — 8-step validator unit tests.

Epic 16 (cj-style 69번째 epic 연속 정직 회복 wire) — AC #7.1.
Tests apps/api/modules/auth/sso/idp_metadata_validator.py 8 validation
steps (PRD §F19.2 verbatim) + 4 error envelopes (CR 12-5 D-14 verbatim).
"""

from __future__ import annotations

import base64

import pytest

from apps.api.modules.auth.sso.idp_metadata_validator import (
    IDPMetadataInvalidEntityIdError,
    IDPMetadataInvalidSSOUrlError,
    IDPMetadataInvalidX509Error,
    IDPMetadataMalformedError,
    validate_idp_metadata,
)

# ── Fixture XML builders ──────────────────────────────────────────────


def _valid_b64_cert() -> str:
    """Generate a valid-looking (but not crypto-verified) base64 cert blob."""
    return base64.b64encode(b"placeholder-cert-for-unit-test").decode("ascii")


def _wrap_pem(raw_b64: str) -> str:
    cleaned = "".join(raw_b64.split())
    lines = [cleaned[i : i + 64] for i in range(0, len(cleaned), 64)]
    return (
        "-----BEGIN CERTIFICATE-----\n"
        + "\n".join(lines)
        + "\n-----END CERTIFICATE-----"
    )


def _build_valid_metadata(tenant_slug: str = "acme") -> str:
    """Construct a valid IdP metadata XML for the happy path."""
    return f"""<?xml version="1.0"?>
<EntityDescriptor xmlns="urn:oasis:names:tc:SAML:2.0:metadata"
                  entityID="https://idp.{tenant_slug}.example.com/saml/metadata">
  <IDPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
    <KeyDescriptor use="signing">
      <KeyInfo xmlns="http://www.w3.org/2000/09/xmldsig#">
        <X509Data>
          <X509Certificate>{_valid_b64_cert()}</X509Certificate>
        </X509Data>
      </KeyInfo>
    </KeyDescriptor>
    <SingleLogoutService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                        Location="https://idp.{tenant_slug}.example.com/slo"/>
    <NameIDFormat>urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress</NameIDFormat>
    <SingleSignOnService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                        Location="https://idp.{tenant_slug}.example.com/sso"/>
  </IDPSSODescriptor>
</EntityDescriptor>
"""


# ── Step 1: well-formedness ───────────────────────────────────────────


class TestWellFormedness:
    def test_valid_xml_returns_metadata(self) -> None:
        md = validate_idp_metadata(_build_valid_metadata(), "acme")
        assert md["entity_id"].startswith("https://idp.acme.")

    def test_malformed_xml_raises(self) -> None:
        with pytest.raises(IDPMetadataMalformedError) as exc:
            validate_idp_metadata("<not><closed>", "acme")
        assert exc.value.code == "IDP_METADATA_MALFORMED_KO"
        assert exc.value.details["reason"] == "xml_parse_error"

    def test_empty_string_raises(self) -> None:
        with pytest.raises(IDPMetadataMalformedError):
            validate_idp_metadata("", "acme")


# ── Step 2: root element = EntityDescriptor ──────────────────────────


class TestRootElement:
    def test_wrong_root_raises(self) -> None:
        xml = (
            '<NotEntityDescriptor xmlns="urn:oasis:names:tc:SAML:2.0:metadata"'
            ' entityID="https://idp.acme.example.com"/>'
        )
        with pytest.raises(IDPMetadataInvalidEntityIdError) as exc:
            validate_idp_metadata(xml, "acme")
        assert exc.value.details["reason"] == "root_not_entity_descriptor"


# ── Step 3: entityID extraction ───────────────────────────────────────


class TestEntityId:
    def test_missing_entity_id_raises(self) -> None:
        xml = (
            '<EntityDescriptor xmlns="urn:oasis:names:tc:SAML:2.0:metadata"/>'
        )
        with pytest.raises(IDPMetadataInvalidEntityIdError) as exc:
            validate_idp_metadata(xml, "acme")
        assert exc.value.details["reason"] == "entity_id_missing"

    def test_non_uri_entity_id_raises(self) -> None:
        xml = (
            '<EntityDescriptor xmlns="urn:oasis:names:tc:SAML:2.0:metadata"'
            ' entityID="not-a-uri"/>'
        )
        with pytest.raises(IDPMetadataInvalidEntityIdError) as exc:
            validate_idp_metadata(xml, "acme")
        assert exc.value.details["reason"] == "entity_id_not_uri"


# ── Step 4: IDPSSODescriptor presence ────────────────────────────────


class TestIDPSSODescriptor:
    def test_missing_raises(self) -> None:
        xml = (
            '<EntityDescriptor xmlns="urn:oasis:names:tc:SAML:2.0:metadata"'
            ' entityID="https://idp.acme.example.com"/>'
        )
        with pytest.raises(IDPMetadataMalformedError) as exc:
            validate_idp_metadata(xml, "acme")
        assert exc.value.details["reason"] == "idpsso_descriptor_missing"


# ── Step 5: X509Certificate PEM wrap ──────────────────────────────────


class TestX509Certificate:
    def test_missing_key_descriptor_raises(self) -> None:
        xml = (
            '<EntityDescriptor xmlns="urn:oasis:names:tc:SAML:2.0:metadata"'
            ' entityID="https://idp.acme.example.com">'
            "<IDPSSODescriptor>"
            '<SingleSignOnService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"'
            ' Location="https://idp.acme.example.com/sso"/>'
            "</IDPSSODescriptor>"
            "</EntityDescriptor>"
        )
        with pytest.raises(IDPMetadataInvalidX509Error) as exc:
            validate_idp_metadata(xml, "acme")
        assert exc.value.details["reason"] == "key_descriptor_missing"

    def test_invalid_base64_raises(self) -> None:
        xml = (
            '<EntityDescriptor xmlns="urn:oasis:names:tc:SAML:2.0:metadata"'
            ' entityID="https://idp.acme.example.com">'
            "<IDPSSODescriptor>"
            "<KeyDescriptor><KeyInfo xmlns=\"http://www.w3.org/2000/09/xmldsig#\">"
            "<X509Data><X509Certificate>not-valid-base64!!!</X509Certificate></X509Data>"
            "</KeyInfo></KeyDescriptor>"
            '<SingleSignOnService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"'
            ' Location="https://idp.acme.example.com/sso"/>'
            "</IDPSSODescriptor>"
            "</EntityDescriptor>"
        )
        with pytest.raises(IDPMetadataInvalidX509Error) as exc:
            validate_idp_metadata(xml, "acme")
        assert exc.value.details["reason"] == "x509_base64_decode_failed"

    def test_valid_cert_returns_pem(self) -> None:
        md = validate_idp_metadata(_build_valid_metadata(), "acme")
        assert md["x509_cert_pem"].startswith("-----BEGIN CERTIFICATE-----")
        assert md["x509_cert_pem"].endswith("-----END CERTIFICATE-----")


# ── Step 6: SSO URL https:// ──────────────────────────────────────────


class TestSSOUrl:
    def test_http_url_raises(self) -> None:
        xml = (
            '<EntityDescriptor xmlns="urn:oasis:names:tc:SAML:2.0:metadata"'
            ' entityID="https://idp.acme.example.com">'
            "<IDPSSODescriptor>"
            f"<KeyDescriptor><KeyInfo xmlns=\"http://www.w3.org/2000/09/xmldsig#\"><X509Data><X509Certificate>{_valid_b64_cert()}</X509Certificate></X509Data></KeyInfo></KeyDescriptor>"
            '<SingleSignOnService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"'
            ' Location="http://idp.acme.example.com/sso"/>'
            "</IDPSSODescriptor>"
            "</EntityDescriptor>"
        )
        with pytest.raises(IDPMetadataInvalidSSOUrlError) as exc:
            validate_idp_metadata(xml, "acme")
        assert exc.value.details["reason"] == "sso_url_not_https"


# ── Step 7: SLO URL optional + https ──────────────────────────────────


class TestSLOUrl:
    def test_optional_when_missing(self) -> None:
        # Build metadata WITHOUT SingleLogoutService.
        cert = _valid_b64_cert()
        xml = (
            '<EntityDescriptor xmlns="urn:oasis:names:tc:SAML:2.0:metadata"'
            ' entityID="https://idp.acme.example.com/saml/metadata">'
            "<IDPSSODescriptor>"
            f"<KeyDescriptor><KeyInfo xmlns=\"http://www.w3.org/2000/09/xmldsig#\"><X509Data><X509Certificate>{cert}</X509Certificate></X509Data></KeyInfo></KeyDescriptor>"
            '<SingleSignOnService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"'
            ' Location="https://idp.acme.example.com/sso"/>'
            "</IDPSSODescriptor>"
            "</EntityDescriptor>"
        )
        md = validate_idp_metadata(xml, "acme")
        assert md["slo_url"] is None

    def test_http_slo_raises(self) -> None:
        xml = (
            '<EntityDescriptor xmlns="urn:oasis:names:tc:SAML:2.0:metadata"'
            ' entityID="https://idp.acme.example.com">'
            "<IDPSSODescriptor>"
            f"<KeyDescriptor><KeyInfo xmlns=\"http://www.w3.org/2000/09/xmldsig#\"><X509Data><X509Certificate>{_valid_b64_cert()}</X509Certificate></X509Data></KeyInfo></KeyDescriptor>"
            '<SingleSignOnService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"'
            ' Location="https://idp.acme.example.com/sso"/>'
            '<SingleLogoutService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"'
            ' Location="http://idp.acme.example.com/slo"/>'
            "</IDPSSODescriptor>"
            "</EntityDescriptor>"
        )
        with pytest.raises(IDPMetadataInvalidSSOUrlError) as exc:
            validate_idp_metadata(xml, "acme")
        assert exc.value.details["reason"] == "slo_url_not_https"


# ── Step 8: tenant slug matching ──────────────────────────────────────


class TestTenantSlugMatch:
    def test_mismatch_raises(self) -> None:
        xml = _build_valid_metadata(tenant_slug="globex")
        with pytest.raises(IDPMetadataInvalidEntityIdError) as exc:
            validate_idp_metadata(xml, "acme")
        assert exc.value.details["reason"] == "tenant_slug_host_mismatch"

    def test_match_returns_metadata(self) -> None:
        md = validate_idp_metadata(_build_valid_metadata("acme"), "acme")
        assert md["entity_id"].startswith("https://idp.acme.")
