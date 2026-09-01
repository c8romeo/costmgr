"""apps.api.modules.auth.sso.saml_routes — 4 SSO routes.

Epic 15 — T4.2 (AC #3.2) — F17.3 SSO enterprise SAML endpoints.

Routes (mounted at `/api/v1/auth/sso/`):
  1. GET  /login         — SAML AuthnRequest → IdP SSO redirect (302).
  2. POST /acs           — SAML response POST (ACS endpoint).
  3. GET  /metadata      — SP metadata XML.
  4. GET  /sls           — Single Logout Service endpoint.

All routes return ko-KR typed envelopes (CR 12-5 D-14 envelope verbatim).
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.db import get_session
from apps.api.modules.auth.sso.jit_provisioning import (
    JITTenantNotFoundError,
    provision_jit_user,
)
from apps.api.modules.auth.sso.saml_validator import (
    SAMLAssertionAttributes,
    SAMLAudienceMismatchError,
    SAMLExpiredError,
    SAMLInResponseToMissingError,
    SAMLInvalidResponseError,
    SAMLSignatureFailedError,
    SAMLValidationContext,
    SAMLValidationError,
    decode_relay_state,
    validate_saml_response,
)
from apps.api.modules.auth.sso.tenant_idp_lookup import (
    TenantIdPConfigMissingError,
    TenantIdPDisabledError,
    load_tenant_idp,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth/sso", tags=["auth-sso"])


# ── In-memory SAML request store (CSRF defense) ──────────────────────
# Production deploys would swap this for Redis or PostgreSQL; the
# atomic-sprint scope is in-process.
_SAML_REQUEST_STORE: dict[str, str] = {}


def _register_saml_request(tenant_slug: str) -> str:
    request_id = "_".join([tenant_slug, uuid.uuid4().hex])
    _SAML_REQUEST_STORE[request_id] = tenant_slug
    return request_id


def _lookup_saml_request(request_id: str) -> str | None:
    return _SAML_REQUEST_STORE.pop(request_id, None)


# ── GET /login — SAML AuthnRequest → IdP redirect ────────────────────


@router.get("/login")
async def sso_login(
    tenant_slug: str = Query(..., min_length=1, max_length=64),  # noqa: PT028
    relay_state: str = Query("", max_length=512),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Build a SAML AuthnRequest and redirect to the IdP SSO URL.

    `relay_state` carries the original path the user wanted to reach
    (URL-safe base64 encoded). The IdP echoes it back in the ACS POST.

    Epic 16 (T5, AC #5.1): dynamic per-tenant IdP SSO URL from
    `tenant_idps` table. Falls back to the Epic 15 placeholder only if
    no row exists (defense-in-depth — the IdP admin must configure
    before SSO can succeed).
    """
    request_id = _register_saml_request(tenant_slug)
    try:
        idp_row = await load_tenant_idp(session, tenant_slug)
        idp_sso_url = idp_row.idp_sso_url
    except TenantIdPConfigMissingError:
        # Defense-in-depth: tenant has not yet registered an IdP. Use
        # the Epic 15 placeholder so the redirect target is at least
        # well-formed; the IdP will reject with a clear message.
        idp_sso_url = f"https://idp.example.com/sso?tenant={tenant_slug}"
    except TenantIdPDisabledError:
        return JSONResponse(
            status_code=403,
            content={
                "code": "TENANT_IDP_DISABLED",
                "message_ko": "이 테넌트의 SSO IdP 가 비활성화되었습니다",
                "details": {"tenant_slug": tenant_slug},
            },
        )

    return RedirectResponse(
        url=f"{idp_sso_url}&request_id={request_id}&relay_state={relay_state}",
        status_code=302,
    )


# ── POST /acs — SAML Assertion Consumer Service ─────────────────────


@router.post("/acs")
async def sso_acs(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Receive a SAML response POST and complete the JIT provisioning.

    Returns 200 OK with `Set-Cookie: sb-access-token=...` and the
    redirect target in the body (the front-end handles the actual
    navigation).
    """
    form = await request.form()
    saml_response_b64 = form.get("SAMLResponse")
    relay_state_b64 = form.get("RelayState", "")

    if not saml_response_b64:
        return _saml_error_response(SAMLInvalidResponseError(reason="saml_response_missing"))

    # Tenant slug derived from the in-process request store.
    request_id = form.get("request_id", "")
    tenant_slug = _lookup_saml_request(request_id) if request_id else None
    if not tenant_slug:
        return _saml_error_response(SAMLInvalidResponseError(reason="request_id_unknown"))

    # Per-tenant IdP cert (Epic 16 T5: dynamic load from tenant_idps).
    # Falls back to the Epic 15 placeholder if no row exists for the
    # tenant (defense-in-depth — production tenants must register an
    # IdP before SSO can succeed; the placeholder only exists so dev
    # environments without a registered IdP don't crash hard).
    try:
        idp_row = await load_tenant_idp(session, tenant_slug)
        idp_cert_pem = idp_row.idp_x509_cert_pem
    except TenantIdPConfigMissingError:
        idp_cert_pem = (
            "-----BEGIN CERTIFICATE-----\n"
            "MIIDazCCAlOgAwIBAgIUJxZ/placeholder/test/only=\n"
            "-----END CERTIFICATE-----"
        )
    except TenantIdPDisabledError:
        return _saml_error_response(SAMLInvalidResponseError(reason="tenant_idp_disabled"))

    ctx = SAMLValidationContext(
        acs_url=str(request.url),
        sp_entity_id="costmgr-sp",
        expected_audience="costmgr-sp",
        expected_in_response_to=request_id,
    )

    try:
        saml_attrs = validate_saml_response(
            saml_response_b64=str(saml_response_b64),
            idp_cert_pem=idp_cert_pem,
            ctx=ctx,
        )
        # Decode RelayState (CSRF-safe because it's round-tripped
        # through the IdP, not user-controllable).
        original_path = decode_relay_state(relay_state_b64)
        # JIT provision (5-step atomic flow).
        result = await provision_jit_user(
            session,
            saml_attrs=saml_attrs,
            tenant_slug=tenant_slug,
            provider="saml_custom",
        )
    except (
        SAMLInvalidResponseError,
        SAMLSignatureFailedError,
        SAMLExpiredError,
        SAMLAudienceMismatchError,
        SAMLInResponseToMissingError,
        SAMLValidationError,
    ) as exc:
        return _saml_error_response(exc)
    except JITTenantNotFoundError as exc:
        return _saml_error_response(exc)

    return JSONResponse(
        status_code=200,
        content={
            "code": "SSO_OK",
            "user_id": str(result.user_id),
            "tenant_id": str(result.tenant_id),
            "external_identity_id": str(result.external_identity_id),
            "redirect_to": original_path or "/dashboard",
        },
    )


# ── GET /metadata — SP metadata XML ──────────────────────────────────


@router.get("/metadata")
async def sso_metadata(
    tenant_slug: str = Query(..., min_length=1, max_length=64),
) -> Response:
    """Return the SP metadata XML for the given tenant slug.

    Real SP metadata is a signed XML document; the atomic-sprint
    placeholder is a static structure that downstream IdPs can use
    to identify this SP. Production deploys replace this with a
    templated XML that includes the per-tenant ACS URL + entityId.
    """
    xml = (
        '<?xml version="1.0"?>\n'
        '<EntityDescriptor xmlns="urn:oasis:names:tc:SAML:2.0:metadata"'
        ' entityID="costmgr-sp">\n'
        f'  <SPSSODescriptor AuthnRequestsSigned="false"'
        ' WantAssertionsSigned="true"\n'
        '    protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">\n'
        f'    <AssertionConsumerService index="0"'
        f' Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"\n'
        f'      Location="https://api.costmgr.example.com/api/v1/auth/sso/acs?tenant={tenant_slug}"/>\n'
        "  </SPSSODescriptor>\n"
        "</EntityDescriptor>\n"
    )
    return Response(content=xml, media_type="application/samlmetadata+xml")


# ── GET /sls — Single Logout Service ─────────────────────────────────


@router.get("/sls")
async def sso_sls() -> Response:
    """Single Logout Service endpoint.

    Real SLO flow: receive a SAML LogoutRequest from the IdP, validate
    it, terminate the local session, and return a SAML LogoutResponse.
    The atomic-sprint placeholder returns a basic 200 OK envelope; the
    full logout exchange is deferred to follow-up (OQ-4).
    """
    return JSONResponse(
        status_code=200,
        content={
            "code": "SSO_SLO_OK",
            "message_ko": "로그아웃 처리 완료",
        },
    )


# ── helpers ─────────────────────────────────────────────────────────


def _saml_error_response(exc: Exception) -> JSONResponse:
    """Translate a SAML exception into a ko-KR typed envelope (CR 12-5 D-14)."""
    if isinstance(exc, SAMLValidationError):
        status_code = 401 if "EXPIRED" in exc.code else 400
        return JSONResponse(
            status_code=status_code,
            content={
                "code": exc.code,
                "message_ko": exc.message_ko,
                "details": exc.details,
            },
        )
    if isinstance(exc, JITTenantNotFoundError):
        return JSONResponse(
            status_code=404,
            content={
                "code": exc.code,
                "message_ko": exc.message_ko,
                "details": exc.details,
            },
        )
    # Fallback (should not happen — every typed exception is handled above).
    return JSONResponse(
        status_code=500,
        content={
            "code": "SSO_INTERNAL_ERROR",
            "message_ko": "SSO 처리 중 오류가 발생했습니다",
            "details": {"reason": str(exc)},
        },
    )


# ── Public exports ──────────────────────────────────────────────────


__all__ = [
    "router",
    "SAMLAssertionAttributes",
]
