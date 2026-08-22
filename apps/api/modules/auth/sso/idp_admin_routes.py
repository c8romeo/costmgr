"""apps.api.modules.auth.sso.idp_admin_routes — Tenant IdP admin CRUD API.

Epic 16 — T3 (AC #3.1~#3.8) — F19.3 Tenant IdP CRUD API endpoints.

Sibling module of Epic 15 `saml_routes.py` (different domain: per-tenant
IdP admin management vs SAML response consumption). Both share the same
router prefix pattern and CR 12-5 D-14 typed exception envelope.

5 routes (mounted at `/api/v1/admin/tenant/`):
  1. GET  /api/v1/admin/tenant/{tenant_slug}/idp
     — list current tenant's IdP config (0 or 1 row per UNIQUE).
  2. POST /api/v1/admin/tenant/{tenant_slug}/idp
     — create new IdP config (metadata_xml OR direct fields).
  3. PUT  /api/v1/admin/tenant/{tenant_slug}/idp
     — full-replace existing IdP config.
  4. DELETE /api/v1/admin/tenant/{tenant_slug}/idp
     — soft-delete (enabled=FALSE), owner role required.
  5. POST /api/v1/admin/tenant/{tenant_slug}/idp/test
     — validation dry-run, returns 8-step pass/fail list.

CR 0-2 RLS lesson: tenant context (GUC `app.tenant_id`) is auto-applied
via `get_tenant_context` dep — no manual SET LOCAL needed.
CR 1-1 audit-first: 4 NEW audit log rows (tenant_idp_created/updated/
deleted/tested) INSERTed BEFORE the tenant_idps row mutation.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Path
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.audit_action import ActionClass, emit_audit_typed
from apps.api.core.capability import require_any_role, require_role
from apps.api.core.db import get_session
from apps.api.core.security import (
    CROSS_TENANT_ACCESS,
    JWTClaims,
    decode_jwt,
)
from apps.api.core.tenant_context import TenantContext, get_tenant_context
from apps.api.dependencies.capability import require_tenant_idp_management
from apps.api.modules.auth.sso.idp_metadata_validator import (
    IDPMetadataError,
    validate_idp_metadata,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin/tenant", tags=["auth-idp-admin"])


# ── Typed exceptions (CR 12-5 D-14 envelope) ──────────────────────────


class TenantIdPError(Exception):
    """Base Tenant IdP admin failure (CR 12-5 D-14 envelope)."""

    def __init__(
        self,
        code: str,
        message_ko: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message_ko = message_ko
        self.details: dict[str, Any] = details or {}
        super().__init__(message_ko)


class TenantIdPAlreadyExistsError(TenantIdPError):
    """409 TENANT_IDP_ALREADY_EXISTS — duplicate (tenant_id, entity_id)."""

    def __init__(self, tenant_slug: str) -> None:
        super().__init__(
            code="TENANT_IDP_ALREADY_EXISTS_KO",
            message_ko="이 tenant 에 이미 IdP 가 등록되어 있습니다",
            details={"tenant_slug": tenant_slug},
        )


class TenantIdPNotFoundError(TenantIdPError):
    """404 TENANT_IDP_NOT_FOUND — no IdP config for this tenant."""

    def __init__(self, tenant_slug: str) -> None:
        super().__init__(
            code="TENANT_IDP_NOT_FOUND_KO",
            message_ko="IdP 설정을 찾을 수 없습니다",
            details={"tenant_slug": tenant_slug},
        )


class TenantIdPForbiddenError(TenantIdPError):
    """403 TENANT_IDP_FORBIDDEN — caller not owner/admin of this tenant."""

    def __init__(self, reason: str, tenant_slug: str) -> None:
        super().__init__(
            code="TENANT_IDP_FORBIDDEN_KO",
            message_ko="IdP 관리 권한이 없습니다",
            details={"reason": reason, "tenant_slug": tenant_slug},
        )


class TenantIdPMetadataInvalidError(TenantIdPError):
    """400 TENANT_IDP_METADATA_INVALID — IdP metadata validation failed."""

    def __init__(self, code: str, message_ko: str, details: dict[str, Any]) -> None:
        super().__init__(
            code="TENANT_IDP_METADATA_INVALID_KO",
            message_ko=f"IdP 메타데이터가 유효하지 않습니다 ({message_ko})",
            details={"validator_code": code, **details},
        )


# ── Request/response models ───────────────────────────────────────────


class IdPConfigResponse(BaseModel):
    """Tenant IdP config envelope."""

    model_config = ConfigDict(extra="forbid")

    id: str
    tenant_id: str
    idp_entity_id: str
    idp_sso_url: str
    idp_slo_url: str | None
    idp_x509_cert_sha256: str  # fingerprint only — NFR4 PII minimization
    acs_url: str
    name_id_format: str | None
    enabled: bool
    created_at: str
    updated_at: str


class IdPConfigCreateRequest(BaseModel):
    """Tenant IdP config create request.

    Either `metadata_xml` (preferred — full IdP metadata XML) OR all of
    the direct fields must be provided. Backend validates via
    `validate_idp_metadata` and writes the canonical row.
    """

    model_config = ConfigDict(extra="forbid")

    metadata_xml: str | None = None
    idp_entity_id: str | None = None
    idp_sso_url: str | None = None
    idp_x509_cert_pem: str | None = None
    idp_slo_url: str | None = None
    acs_url: str | None = None
    name_id_format: str | None = None
    enabled: bool = True


class IdPTestResultStep(BaseModel):
    """Single 8-step validation result."""

    model_config = ConfigDict(extra="forbid")

    step: int
    name: str
    passed: bool
    detail: str | None = None


class IdPTestResultResponse(BaseModel):
    """Validation dry-run result."""

    model_config = ConfigDict(extra="forbid")

    passed: bool
    steps: list[IdPTestResultStep]
    metadata: dict[str, Any] | None = None


# ── Helpers ───────────────────────────────────────────────────────────


async def _resolve_tenant_id_from_slug(
    session: AsyncSession,
    tenant_slug: str,
    ctx: TenantContext,
) -> uuid.UUID:
    """Resolve `tenant_slug` → tenant_id with cross-tenant check.

    Raises TenantIdPForbiddenError if the slug belongs to a different
    tenant than the JWT context (CROSS_TENANT_ACCESS invariant).
    """
    row = (
        await session.execute(
            text("SELECT id FROM public.tenants WHERE slug = :slug LIMIT 1"),
            {"slug": tenant_slug},
        )
    ).first()
    if row is None:
        raise TenantIdPForbiddenError(
            reason="tenant_not_found",
            tenant_slug=tenant_slug,
        )
    tenant_id = row[0]
    if tenant_id != ctx.tenant_id:
        # Cross-tenant access denied — no info leak about other tenant.
        raise TenantIdPForbiddenError(
            reason=CROSS_TENANT_ACCESS,
            tenant_slug=tenant_slug,
        )
    return tenant_id


def _cert_fingerprint(cert_pem: str) -> str:
    """Compute SHA-256 fingerprint of a PEM cert (NFR4 PII minimization).

    The audit log stores ONLY the fingerprint, never the raw cert body.
    """
    # Strip PEM markers + whitespace before hashing.
    body = "".join(
        line.strip()
        for line in cert_pem.splitlines()
        if line.strip() and "BEGIN" not in line and "END" not in line
    )
    return hashlib.sha256(body.encode("ascii")).hexdigest()


# ── GET /api/v1/admin/tenant/{tenant_slug}/idp ───────────────────────


@router.get(
    "/{tenant_slug}/idp",
    response_model=list[IdPConfigResponse],
    dependencies=[
        Depends(require_any_role("owner", "admin")),
        Depends(require_tenant_idp_management),
    ],
)
async def list_tenant_idp(
    tenant_slug: str = Path(..., min_length=1, max_length=64),
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> list[IdPConfigResponse]:
    """Return the current tenant's IdP config (0 or 1 row)."""
    tenant_id = await _resolve_tenant_id_from_slug(session, tenant_slug, ctx)
    rows = (
        await session.execute(
            text(
                """
                SELECT id, tenant_id, idp_entity_id, idp_sso_url, idp_slo_url,
                       idp_x509_cert, acs_url, name_id_format, enabled,
                       created_at, updated_at
                FROM public.tenant_idps
                WHERE tenant_id = :tenant_id
                ORDER BY created_at DESC
                LIMIT 1
                """
            ),
            {"tenant_id": str(tenant_id)},
        )
    ).fetchall()
    if not rows:
        return []
    return [
        IdPConfigResponse(
            id=str(r[0]),
            tenant_id=str(r[1]),
            idp_entity_id=r[2],
            idp_sso_url=r[3],
            idp_slo_url=r[4],
            idp_x509_cert_sha256=_cert_fingerprint(r[5]),
            acs_url=r[6],
            name_id_format=r[7],
            enabled=r[8],
            created_at=r[9].isoformat() if r[9] else "",
            updated_at=r[10].isoformat() if r[10] else "",
        )
        for r in rows
    ]


# ── POST /api/v1/admin/tenant/{tenant_slug}/idp ──────────────────────


@router.post(
    "/{tenant_slug}/idp",
    response_model=IdPConfigResponse,
    status_code=201,
    dependencies=[
        Depends(require_any_role("owner", "admin")),
        Depends(require_tenant_idp_management),
    ],
)
async def create_tenant_idp(
    body: IdPConfigCreateRequest,
    tenant_slug: str = Path(..., min_length=1, max_length=64),
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> IdPConfigResponse:
    """Create a new IdP config for the tenant.

    audit-first INSERT (CR 1-1 verbatim) BEFORE the tenant_idps INSERT.
    """
    tenant_id = await _resolve_tenant_id_from_slug(session, tenant_slug, ctx)

    # Resolve metadata either from XML or from direct fields.
    if body.metadata_xml:
        try:
            md = validate_idp_metadata(body.metadata_xml, tenant_slug)
        except IDPMetadataError as exc:
            raise TenantIdPMetadataInvalidError(
                code=exc.code,
                message_ko=exc.message_ko,
                details=exc.details,
            ) from exc
        entity_id = md["entity_id"]
        sso_url = md["sso_url"]
        x509_cert = md["x509_cert_pem"]
        slo_url = md["slo_url"]
        name_id_format = md["name_id_format"]
        acs_url = body.acs_url or f"https://{_placeholder_acs_host()}/api/v1/auth/sso/acs?tenant={tenant_slug}"
    else:
        # Direct field mode — all 4 required fields must be present.
        if not (body.idp_entity_id and body.idp_sso_url and body.idp_x509_cert_pem):
            raise TenantIdPMetadataInvalidError(
                code="IDP_METADATA_MALFORMED_KO",
                message_ko="metadata_xml 또는 4개 직접 입력 필드가 필요합니다",
                details={"missing_fields": _missing_direct_fields(body)},
            )
        entity_id = body.idp_entity_id
        sso_url = body.idp_sso_url
        x509_cert = body.idp_x509_cert_pem
        slo_url = body.idp_slo_url
        name_id_format = body.name_id_format
        acs_url = body.acs_url or f"https://{_placeholder_acs_host()}/api/v1/auth/sso/acs?tenant={tenant_slug}"

    # Check for existing IdP (UNIQUE (tenant_id, idp_entity_id)).
    existing = (
        await session.execute(
            text(
                """
                SELECT id FROM public.tenant_idps
                WHERE tenant_id = :tenant_id AND idp_entity_id = :entity_id
                LIMIT 1
                """
            ),
            {"tenant_id": str(tenant_id), "entity_id": entity_id},
        )
    ).first()
    if existing is not None:
        raise TenantIdPAlreadyExistsError(tenant_slug=tenant_slug)

    # Audit-first INSERT (CR 1-1 verbatim).
    await emit_audit_typed(
        session,
        action_class=ActionClass.AUTH,
        action="tenant_idp_created",
        actor_id=ctx.user_id,
        target_id=None,
        tenant_id=tenant_id,
        payload={
            "entity_id": entity_id,
            "sso_url": sso_url,
            "x509_cert_sha256": _cert_fingerprint(x509_cert),
            "acs_url": acs_url,
        },
    )

    # INSERT tenant_idps row.
    new_id = uuid.uuid4()
    await session.execute(
        text(
            """
            INSERT INTO public.tenant_idps (
                id, tenant_id, idp_entity_id, idp_sso_url, idp_slo_url,
                idp_x509_cert, acs_url, name_id_format, enabled,
                created_by, updated_by
            ) VALUES (
                :id, :tenant_id, :entity_id, :sso_url, :slo_url,
                :cert, :acs_url, :name_id_format, :enabled,
                :created_by, :updated_by
            )
            """
        ),
        {
            "id": str(new_id),
            "tenant_id": str(tenant_id),
            "entity_id": entity_id,
            "sso_url": sso_url,
            "slo_url": slo_url,
            "cert": x509_cert,
            "acs_url": acs_url,
            "name_id_format": name_id_format,
            "enabled": body.enabled,
            "created_by": str(ctx.user_id),
            "updated_by": str(ctx.user_id),
        },
    )
    await session.commit()

    return IdPConfigResponse(
        id=str(new_id),
        tenant_id=str(tenant_id),
        idp_entity_id=entity_id,
        idp_sso_url=sso_url,
        idp_slo_url=slo_url,
        idp_x509_cert_sha256=_cert_fingerprint(x509_cert),
        acs_url=acs_url,
        name_id_format=name_id_format,
        enabled=body.enabled,
        created_at="",
        updated_at="",
    )


# ── PUT /api/v1/admin/tenant/{tenant_slug}/idp ───────────────────────


@router.put(
    "/{tenant_slug}/idp",
    response_model=IdPConfigResponse,
    dependencies=[
        Depends(require_any_role("owner", "admin")),
        Depends(require_tenant_idp_management),
    ],
)
async def update_tenant_idp(
    body: IdPConfigCreateRequest,
    tenant_slug: str = Path(..., min_length=1, max_length=64),
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> IdPConfigResponse:
    """Full-replace update of the tenant's IdP config."""
    tenant_id = await _resolve_tenant_id_from_slug(session, tenant_slug, ctx)

    # Resolve metadata either from XML or from direct fields.
    if body.metadata_xml:
        try:
            md = validate_idp_metadata(body.metadata_xml, tenant_slug)
        except IDPMetadataError as exc:
            raise TenantIdPMetadataInvalidError(
                code=exc.code,
                message_ko=exc.message_ko,
                details=exc.details,
            ) from exc
        entity_id = md["entity_id"]
        sso_url = md["sso_url"]
        x509_cert = md["x509_cert_pem"]
        slo_url = md["slo_url"]
        name_id_format = md["name_id_format"]
        acs_url = body.acs_url or f"https://{_placeholder_acs_host()}/api/v1/auth/sso/acs?tenant={tenant_slug}"
    else:
        if not (body.idp_entity_id and body.idp_sso_url and body.idp_x509_cert_pem):
            raise TenantIdPMetadataInvalidError(
                code="IDP_METADATA_MALFORMED_KO",
                message_ko="metadata_xml 또는 4개 직접 입력 필드가 필요합니다",
                details={"missing_fields": _missing_direct_fields(body)},
            )
        entity_id = body.idp_entity_id
        sso_url = body.idp_sso_url
        x509_cert = body.idp_x509_cert_pem
        slo_url = body.idp_slo_url
        name_id_format = body.name_id_format
        acs_url = body.acs_url or f"https://{_placeholder_acs_host()}/api/v1/auth/sso/acs?tenant={tenant_slug}"

    # Audit-first INSERT.
    await emit_audit_typed(
        session,
        action_class=ActionClass.AUTH,
        action="tenant_idp_updated",
        actor_id=ctx.user_id,
        target_id=None,
        tenant_id=tenant_id,
        payload={
            "entity_id": entity_id,
            "sso_url": sso_url,
            "x509_cert_sha256": _cert_fingerprint(x509_cert),
            "acs_url": acs_url,
        },
    )

    # UPDATE — find existing row.
    row_result = (
        await session.execute(
            text(
                """
                UPDATE public.tenant_idps
                SET idp_entity_id = :entity_id,
                    idp_sso_url = :sso_url,
                    idp_slo_url = :slo_url,
                    idp_x509_cert = :cert,
                    acs_url = :acs_url,
                    name_id_format = :name_id_format,
                    enabled = :enabled,
                    updated_by = :updated_by
                WHERE tenant_id = :tenant_id
                RETURNING id, created_at, updated_at
                """
            ),
            {
                "tenant_id": str(tenant_id),
                "entity_id": entity_id,
                "sso_url": sso_url,
                "slo_url": slo_url,
                "cert": x509_cert,
                "acs_url": acs_url,
                "name_id_format": name_id_format,
                "enabled": body.enabled,
                "updated_by": str(ctx.user_id),
            },
        )
    ).first()
    if row_result is None:
        await session.rollback()
        raise TenantIdPNotFoundError(tenant_slug=tenant_slug)
    await session.commit()

    return IdPConfigResponse(
        id=str(row_result[0]),
        tenant_id=str(tenant_id),
        idp_entity_id=entity_id,
        idp_sso_url=sso_url,
        idp_slo_url=slo_url,
        idp_x509_cert_sha256=_cert_fingerprint(x509_cert),
        acs_url=acs_url,
        name_id_format=name_id_format,
        enabled=body.enabled,
        created_at=row_result[1].isoformat() if row_result[1] else "",
        updated_at=row_result[2].isoformat() if row_result[2] else "",
    )


# ── DELETE /api/v1/admin/tenant/{tenant_slug}/idp ────────────────────


@router.delete(
    "/{tenant_slug}/idp",
    status_code=200,
    dependencies=[
        Depends(require_role("owner")),
        Depends(require_tenant_idp_management),
    ],
)
async def delete_tenant_idp(
    tenant_slug: str = Path(..., min_length=1, max_length=64),
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Soft-delete IdP config (enabled=FALSE)."""
    tenant_id = await _resolve_tenant_id_from_slug(session, tenant_slug, ctx)

    await emit_audit_typed(
        session,
        action_class=ActionClass.AUTH,
        action="tenant_idp_deleted",
        actor_id=ctx.user_id,
        target_id=None,
        tenant_id=tenant_id,
        payload={"tenant_slug": tenant_slug},
    )

    result = (
        await session.execute(
            text(
                """
                UPDATE public.tenant_idps
                SET enabled = FALSE, updated_by = :updated_by
                WHERE tenant_id = :tenant_id
                RETURNING id
                """
            ),
            {"tenant_id": str(tenant_id), "updated_by": str(ctx.user_id)},
        )
    ).first()
    if result is None:
        await session.rollback()
        raise TenantIdPNotFoundError(tenant_slug=tenant_slug)
    await session.commit()

    return {"code": "TENANT_IDP_DISABLED_OK", "id": str(result[0])}


# ── POST /api/v1/admin/tenant/{tenant_slug}/idp/test ─────────────────


@router.post(
    "/{tenant_slug}/idp/test",
    response_model=IdPTestResultResponse,
    dependencies=[
        Depends(require_any_role("owner", "admin")),
        Depends(require_tenant_idp_management),
    ],
)
async def test_tenant_idp(
    body: IdPConfigCreateRequest,
    tenant_slug: str = Path(..., min_length=1, max_length=64),  # noqa: PT028
    ctx: TenantContext = Depends(get_tenant_context),  # noqa: PT028
    session: AsyncSession = Depends(get_session),  # noqa: PT028
) -> IdPTestResultResponse:
    """Validate IdP metadata XML without writing to DB.

    audit-first INSERT `tenant_idp_tested` BEFORE running validator.
    """
    tenant_id = await _resolve_tenant_id_from_slug(session, tenant_slug, ctx)

    await emit_audit_typed(
        session,
        action_class=ActionClass.AUTH,
        action="tenant_idp_tested",
        actor_id=ctx.user_id,
        target_id=None,
        tenant_id=tenant_id,
        payload={"tenant_slug": tenant_slug, "has_metadata_xml": body.metadata_xml is not None},
    )

    steps: list[IdPTestResultStep] = []
    if not body.metadata_xml:
        return IdPTestResultResponse(
            passed=False,
            steps=[
                IdPTestResultStep(step=1, name="metadata_xml_present", passed=False, detail="metadata_xml is required for /test endpoint"),
            ],
            metadata=None,
        )

    try:
        md = validate_idp_metadata(body.metadata_xml, tenant_slug)
    except IDPMetadataError as exc:
        # Single failure step (validator already reported the failing step).
        steps.append(
            IdPTestResultStep(
                step=0,
                name="validator_exception",
                passed=False,
                detail=f"{exc.code}: {exc.message_ko}",
            )
        )
        await session.commit()
        return IdPTestResultResponse(passed=False, steps=steps, metadata=None)

    # All 8 steps passed — emit success markers.
    step_names = [
        "xml_well_formedness",
        "root_entity_descriptor",
        "entity_id_present",
        "idpsso_descriptor_present",
        "x509_cert_present",
        "sso_url_https",
        "slo_url_optional_https",
        "tenant_slug_host_match",
    ]
    for i, name in enumerate(step_names, start=1):
        steps.append(IdPTestResultStep(step=i, name=name, passed=True))

    await session.commit()
    return IdPTestResultResponse(
        passed=True,
        steps=steps,
        metadata={
            "entity_id": md["entity_id"],
            "sso_url": md["sso_url"],
            "slo_url": md["slo_url"],
            "name_id_format": md["name_id_format"],
        },
    )


# ── Internal helpers ──────────────────────────────────────────────────


def _missing_direct_fields(body: IdPConfigCreateRequest) -> list[str]:
    missing: list[str] = []
    if not body.idp_entity_id:
        missing.append("idp_entity_id")
    if not body.idp_sso_url:
        missing.append("idp_sso_url")
    if not body.idp_x509_cert_pem:
        missing.append("idp_x509_cert_pem")
    if not body.acs_url:
        missing.append("acs_url")
    return missing


def _placeholder_acs_host() -> str:
    """Best-effort ACS host — production uses PUBLIC_API_BASE_URL."""
    return "api.costmgr.example.com"


# Re-export the typed JWTClaims class so callers can `decode_jwt` without
# importing the security module separately.
__all__ = [
    "router",
    "TenantIdPError",
    "TenantIdPAlreadyExistsError",
    "TenantIdPNotFoundError",
    "TenantIdPForbiddenError",
    "TenantIdPMetadataInvalidError",
    "JWTClaims",
    "decode_jwt",
]
