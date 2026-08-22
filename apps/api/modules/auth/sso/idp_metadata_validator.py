"""apps.api.modules.auth.sso.idp_metadata_validator — SAML 2.0 IdP metadata XML validator.

Epic 16 — T2 (AC #2.1~#2.7) — F19.2 IdP metadata XML validation service.

Sibling module of Epic 15 `saml_validator.py` (different domain: IdP
metadata XML validation vs SAML response validation). Both modules
share the CR 12-5 D-14 typed exception envelope pattern.

8 validation steps (PRD §F19.2 verbatim):
  1. XML well-formedness check (xml.etree.ElementTree.fromstring).
  2. Root element = EntityDescriptor (urn:oasis:names:tc:SAML:2.0:metadata).
  3. entityID attribute extraction.
  4. IDPSSODescriptor element presence check.
  5. KeyDescriptor / X509Certificate extraction + PEM wrap.
  6. SingleSignOnService Location (https:// required).
  7. SingleLogoutService Location (optional, https:// when present).
  8. tenant_slug matching against entityID host part.

All validation failures raise typed exceptions (CR 12-5 D-14 envelope)
that the route layer translates into ko-KR error envelopes.

AD-14 stack pin: lxml>=5.0.0 is OPTIONAL — this module uses stdlib
xml.etree.ElementTree (sufficient for the validation surface). lxml
is only needed if a future Epic wires XML schema validation.
"""

from __future__ import annotations

import base64
import binascii
import logging
import xml.etree.ElementTree as ET
from typing import TypedDict
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


# ── Typed exceptions (CR 12-5 D-14 envelope) ──────────────────────────


class IDPMetadataError(Exception):
    """Base IdP metadata validation failure (CR 12-5 D-14 envelope)."""

    def __init__(self, code: str, message_ko: str, details: dict[str, object] | None = None):
        self.code = code
        self.message_ko = message_ko
        self.details: dict[str, object] = details or {}
        super().__init__(message_ko)


class IDPMetadataMalformedError(IDPMetadataError):
    """IdP metadata XML is malformed or not well-formed."""

    def __init__(self, reason: str = "xml_parse_error") -> None:
        super().__init__(
            code="IDP_METADATA_MALFORMED_KO",
            message_ko="IdP 메타데이터 XML 형식이 올바르지 않습니다",
            details={"reason": reason},
        )


class IDPMetadataInvalidEntityIdError(IDPMetadataError):
    """EntityID attribute missing or does not follow SAML 2.0 spec."""

    def __init__(self, reason: str = "entity_id_invalid", entity_id: str | None = None) -> None:
        super().__init__(
            code="IDP_METADATA_INVALID_ENTITY_ID_KO",
            message_ko="EntityID 가 SAML 2.0 스펙을 따르지 않습니다",
            details={"reason": reason, "entity_id": entity_id},
        )


class IDPMetadataInvalidX509Error(IDPMetadataError):
    """X509Certificate is not PEM-formatted or base64 decode fails."""

    def __init__(self, reason: str = "x509_pem_invalid") -> None:
        super().__init__(
            code="IDP_METADATA_INVALID_X509_KO",
            message_ko="X509Certificate 가 PEM 형식이 아니거나 base64 디코딩 실패",
            details={"reason": reason},
        )


class IDPMetadataInvalidSSOUrlError(IDPMetadataError):
    """SingleSignOnService URL is missing or not https://."""

    def __init__(self, reason: str = "sso_url_invalid", url: str | None = None) -> None:
        super().__init__(
            code="IDP_METADATA_INVALID_SSO_URL_KO",
            message_ko="SingleSignOnService URL 은 https:// 이어야 합니다",
            details={"reason": reason, "url": url},
        )


# ── Return TypedDict ──────────────────────────────────────────────────


class IdPMetadata(TypedDict):
    """Validated IdP metadata extracted from the XML document.

    Returned by `validate_idp_metadata()` after all 8 validation steps
    pass. Used as the source of truth for `tenant_idps` row INSERT.
    """

    entity_id: str
    sso_url: str
    slo_url: str | None
    x509_cert_pem: str
    name_id_format: str | None


# ── SAML 2.0 metadata namespace ───────────────────────────────────────

_SAML_METADATA_NS = "urn:oasis:names:tc:SAML:2.0:metadata"
_DSIG_NS = "http://www.w3.org/2000/09/xmldsig#"


# ── Validator entry point ─────────────────────────────────────────────


def validate_idp_metadata(
    metadata_xml: str,
    expected_tenant_slug: str,
) -> IdPMetadata:
    """Validate a SAML 2.0 IdP metadata XML document.

    Runs all 8 validation steps (PRD §F19.2 verbatim). Raises a typed
    exception (CR 12-5 D-14 envelope) on any failure. Returns the
    extracted IdPMetadata TypedDict on success.

    Args:
        metadata_xml: Raw XML string from the IdP metadata endpoint.
        expected_tenant_slug: Tenant slug used to validate the entityID
            host part. Example: tenant_slug='acme' must match entityID
            host 'idp.acme.com' (host second-to-last label match).

    Returns:
        IdPMetadata TypedDict with 5 fields: entity_id, sso_url,
        slo_url (optional), x509_cert_pem, name_id_format (optional).

    Raises:
        IDPMetadataMalformedError: XML parse failure (step 1).
        IDPMetadataInvalidEntityIdError: Root element not EntityDescriptor
            (step 2), entityID missing (step 3), or tenant slug mismatch
            (step 8).
        IDPMetadataInvalidX509Error: X509Certificate missing (step 5) or
            PEM decode failure.
        IDPMetadataInvalidSSOUrlError: SingleSignOnService URL missing
            or not https:// (step 6).
    """
    # Step 1: XML well-formedness.
    try:
        root = ET.fromstring(metadata_xml)
    except ET.ParseError as exc:
        raise IDPMetadataMalformedError(reason="xml_parse_error") from exc

    # Step 2: Root element = EntityDescriptor.
    if root.tag != f"{{{_SAML_METADATA_NS}}}EntityDescriptor":
        raise IDPMetadataInvalidEntityIdError(
            reason="root_not_entity_descriptor",
            entity_id=None,
        )

    # Step 3: entityID attribute extraction.
    entity_id = (root.attrib.get("entityID") or "").strip()
    if not entity_id:
        raise IDPMetadataInvalidEntityIdError(reason="entity_id_missing", entity_id=None)
    # Validate entityID is an absolute URL (SAML 2.0 §2.4.2 — must be URI).
    parsed_entity = urlparse(entity_id)
    if parsed_entity.scheme not in ("http", "https"):
        raise IDPMetadataInvalidEntityIdError(
            reason="entity_id_not_uri",
            entity_id=entity_id,
        )

    # Step 4: IDPSSODescriptor element presence check.
    idp_sso_descriptor = root.find(f"{{{_SAML_METADATA_NS}}}IDPSSODescriptor")
    if idp_sso_descriptor is None:
        raise IDPMetadataMalformedError(reason="idpsso_descriptor_missing")

    # Step 5: KeyDescriptor / X509Certificate extraction + PEM wrap.
    key_descriptor = idp_sso_descriptor.find(f"{{{_SAML_METADATA_NS}}}KeyDescriptor")
    if key_descriptor is None:
        raise IDPMetadataInvalidX509Error(reason="key_descriptor_missing")
    x509_data = key_descriptor.find(f"{{{_DSIG_NS}}}KeyInfo")
    if x509_data is None:
        raise IDPMetadataInvalidX509Error(reason="key_info_missing")
    x509_cert_el = x509_data.find(f"{{{_DSIG_NS}}}X509Data")
    if x509_cert_el is None:
        raise IDPMetadataInvalidX509Error(reason="x509_data_missing")
    x509_cert_el2 = x509_cert_el.find(f"{{{_DSIG_NS}}}X509Certificate")
    if x509_cert_el2 is None:
        raise IDPMetadataInvalidX509Error(reason="x509_certificate_missing")
    raw_cert = (x509_cert_el2.text or "").strip()
    if not raw_cert:
        raise IDPMetadataInvalidX509Error(reason="x509_certificate_empty")
    # Validate base64 decodability (defense-in-depth — actual crypto
    # verification is delegated to python3-saml at ACS time).
    try:
        base64.b64decode(raw_cert.encode("ascii"), validate=True)
    except (binascii.Error, ValueError) as exc:
        raise IDPMetadataInvalidX509Error(reason="x509_base64_decode_failed") from exc
    x509_cert_pem = _wrap_x509_pem(raw_cert)

    # Step 6: SingleSignOnService Location (https:// required).
    sso_url = _find_service_location(
        idp_sso_descriptor,
        service_tag="SingleSignOnService",
        required=True,
    )
    if not sso_url.startswith("https://"):
        raise IDPMetadataInvalidSSOUrlError(reason="sso_url_not_https", url=sso_url)

    # Step 7: SingleLogoutService Location (optional, https:// when present).
    slo_url = _find_service_location(
        idp_sso_descriptor,
        service_tag="SingleLogoutService",
        required=False,
    )
    if slo_url is not None and not slo_url.startswith("https://"):
        raise IDPMetadataInvalidSSOUrlError(reason="slo_url_not_https", url=slo_url)

    # Step 8: tenant_slug matching against entityID host part.
    # Match rule: expected_tenant_slug must appear as a label in the
    # entityID host. Example: tenant_slug='acme' must match entityID
    # host 'idp.acme.com' or 'acme.example.com'.
    entity_host = parsed_entity.hostname or ""
    if expected_tenant_slug and expected_tenant_slug not in entity_host.split("."):
        raise IDPMetadataInvalidEntityIdError(
            reason="tenant_slug_host_mismatch",
            entity_id=entity_id,
        )

    # NameID format (optional — extract first one if present).
    name_id_format = _extract_name_id_format(idp_sso_descriptor)

    return IdPMetadata(
        entity_id=entity_id,
        sso_url=sso_url,
        slo_url=slo_url,
        x509_cert_pem=x509_cert_pem,
        name_id_format=name_id_format,
    )


# ── Internal helpers ──────────────────────────────────────────────────


def _find_service_location(
    parent: ET.Element,
    *,
    service_tag: str,
    required: bool,
) -> str | None:
    """Find the first matching service element Location attribute.

    Prefers Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
    when multiple are present (standard SSO redirect binding).
    """
    candidates = parent.findall(f"{{{_SAML_METADATA_NS}}}{service_tag}")
    if not candidates:
        if required:
            raise IDPMetadataMalformedError(reason=f"{service_tag.lower()}_missing")
        return None

    # Prefer HTTP-Redirect binding (standard for IdP-initiated SSO).
    for cand in candidates:
        binding = cand.attrib.get("Binding", "")
        location = cand.attrib.get("Location", "")
        if binding.endswith("HTTP-Redirect") and location:
            return location.strip()
    # Fallback: first non-empty Location.
    for cand in candidates:
        location = cand.attrib.get("Location", "")
        if location.strip():
            return location.strip()
    if required:
        raise IDPMetadataMalformedError(reason=f"{service_tag.lower()}_location_missing")
    return None


def _wrap_x509_pem(raw_base64: str) -> str:
    """Wrap a raw base64 cert in standard PEM envelope."""
    # Strip internal whitespace + line breaks for clean wrap.
    cleaned = "".join(raw_base64.split())
    # Wrap to 64-char lines per RFC 7468 §3.
    lines = [cleaned[i : i + 64] for i in range(0, len(cleaned), 64)]
    return "-----BEGIN CERTIFICATE-----\n" + "\n".join(lines) + "\n-----END CERTIFICATE-----"


def _extract_name_id_format(idp_sso_descriptor: ET.Element) -> str | None:
    """Extract the first NameIDFormat URI from the IDPSSODescriptor."""
    name_id_el = idp_sso_descriptor.find(f"{{{_SAML_METADATA_NS}}}NameIDFormat")
    if name_id_el is None or not (name_id_el.text or "").strip():
        return None
    return (name_id_el.text or "").strip()


__all__ = [
    "validate_idp_metadata",
    "IdPMetadata",
    "IDPMetadataError",
    "IDPMetadataMalformedError",
    "IDPMetadataInvalidEntityIdError",
    "IDPMetadataInvalidX509Error",
    "IDPMetadataInvalidSSOUrlError",
]
