"""apps.api.core.security — Supabase JWT decoder (AD-3, AD-10).

Story 0.2 — Tasks 5.1~5.5.

Uses PyJWT for HS256 signature verification with `SUPABASE_JWT_SECRET`.
Reads `tenant_id` and `role` from `payload['app_metadata']` only — NEVER
from `user_metadata` (user-editable — AD-3 violation).

Per AD-15 error contract: returns typed `TENANT_FORBIDDEN` errors
(`{code, message_ko, details, trace_id}`).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

import jwt
from jwt.exceptions import (
    DecodeError,
    ExpiredSignatureError,
    InvalidSignatureError,
    InvalidTokenError,
)

from apps.api.core.settings import get_settings

# Typed error per AD-15
TENANT_FORBIDDEN = "TENANT_FORBIDDEN"
# Cross-tenant access violation — the spec's example error string
# (AC #3). Raised when a service or query targets a tenant other than
# the JWT's `app_metadata.tenant_id`. Distinct from TENANT_FORBIDDEN
# which is a generic auth failure code.
CROSS_TENANT_ACCESS = "CROSS_TENANT_ACCESS"
CROSS_TENANT_MESSAGE_KO = "다른 테넌트 데이터에 접근할 수 없습니다"


class AuthError(Exception):
    """Typed auth error — mapped to HTTP 401 by the FastAPI exception handler."""

    def __init__(
        self,
        code: str,
        message_ko: str,
        details: dict[str, Any] | None = None,
        trace_id: str | None = None,
    ) -> None:
        super().__init__(message_ko)
        self.code = code
        self.message_ko = message_ko
        self.details = details or {}
        self.trace_id = trace_id or str(uuid.uuid4())


@dataclass(frozen=True)
class JWTClaims:
    """Decoded JWT claims — pure value object."""

    tenant_id: uuid.UUID
    role: str
    user_id: uuid.UUID
    raw: dict[str, Any]


def _error_payload(code: str, message_ko: str, trace_id: str | None = None) -> dict[str, Any]:
    """Build the AD-15 error payload."""
    return {
        "code": code,
        "message_ko": message_ko,
        "details": {},
        "trace_id": trace_id or str(uuid.uuid4()),
    }


def decode_jwt(token: str) -> JWTClaims:
    """Decode and verify a Supabase JWT.

    - HS256 signature verified with `SUPABASE_JWT_SECRET`.
    - `exp` claim validated (with 30s leeway, configurable via JWT_LEEWAY_SEC).
    - `tenant_id` and `role` extracted from `app_metadata` (server-controlled).
    - Raises `TENANT_FORBIDDEN` (401) on any failure.
    """
    settings = get_settings()
    if not settings.supabase_jwt_secret:
        raise AuthError(
            code=TENANT_FORBIDDEN,
            message_ko="인증 서버가 설정되지 않았습니다 (SUPABASE_JWT_SECRET 누락)",
        )

    leeway = 30  # default 30s — Task 5.5
    if settings.jwt_leeway_sec is not None:
        leeway = settings.jwt_leeway_sec

    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            leeway=leeway,
            options={"require": ["exp"]},
        )
    except ExpiredSignatureError as e:
        raise AuthError(
            code=TENANT_FORBIDDEN,
            message_ko="토큰이 만료되었습니다. 다시 로그인해 주세요",
            details={"reason": "expired"},
        ) from e
    except (InvalidSignatureError, DecodeError, InvalidTokenError) as e:
        # CR 2026-07-25 JWT-2: use a stable reason code instead of the
        # library exception class name (which leaks PyJWT internals).
        raise AuthError(
            code=TENANT_FORBIDDEN,
            message_ko="유효하지 않은 인증 토큰입니다",
            details={"reason": "invalid_token"},
        ) from e

    # tenant_id MUST come from app_metadata (server-controlled), NEVER user_metadata
    app_metadata = payload.get("app_metadata") or {}
    tenant_id_raw = app_metadata.get("tenant_id")
    if not tenant_id_raw:
        raise AuthError(
            code=TENANT_FORBIDDEN,
            message_ko="토큰에 테넌트 정보가 없습니다",
            details={"reason": "no_tenant_id"},
        )

    try:
        tenant_id = uuid.UUID(str(tenant_id_raw))
    except (ValueError, TypeError) as e:
        raise AuthError(
            code=TENANT_FORBIDDEN,
            message_ko="토큰의 테넌트 ID 형식이 잘못되었습니다",
            details={"reason": "invalid_tenant_id"},
        ) from e

    user_id_raw = payload.get("sub")
    if not user_id_raw:
        raise AuthError(
            code=TENANT_FORBIDDEN,
            message_ko="토큰에 사용자 정보가 없습니다",
            details={"reason": "no_sub"},
        )
    try:
        user_id = uuid.UUID(str(user_id_raw))
    except (ValueError, TypeError) as e:
        raise AuthError(
            code=TENANT_FORBIDDEN,
            message_ko="토큰의 사용자 ID 형식이 잘못되었습니다",
            details={"reason": "invalid_sub"},
        ) from e

    role = str(app_metadata.get("role") or "viewer")  # Task 5.3 default

    return JWTClaims(
        tenant_id=tenant_id,
        role=role,
        user_id=user_id,
        raw=payload,
    )


def decode_jwt_or_none(token: str | None) -> JWTClaims | None:
    """Decode JWT, returning None on missing/empty token (for optional auth)."""
    if not token:
        return None
    return decode_jwt(token)


def raise_cross_tenant_access(
    expected_tenant: uuid.UUID,
    actual_tenant: uuid.UUID | None = None,
) -> None:
    """Raise the spec's cross-tenant access error (AC #3).

    Use this when a service layer detects that an operation targets a
    tenant other than the one in the JWT claims. The spec mandates the
    exact Korean message "다른 테넌트 데이터에 접근할 수 없습니다" and the
    `CROSS_TENANT_ACCESS` code, distinct from the generic auth failures.
    """
    details: dict[str, Any] = {"expected_tenant_id": str(expected_tenant)}
    if actual_tenant is not None:
        details["actual_tenant_id"] = str(actual_tenant)
    raise AuthError(
        code=CROSS_TENANT_ACCESS,
        message_ko=CROSS_TENANT_MESSAGE_KO,
        details=details,
    )
