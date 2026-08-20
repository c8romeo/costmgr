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
# Phase 3-0: JWT `app_metadata.role` allowlist. alembic 0001
# `tenant_memberships.role` CHECK 제약과 동일 집합. RLS 가
# `auth.jwt() -> 'app_metadata' ->> 'role'` 로 결정하므로
# decoder 단계에서 검증해야 한다. 외부 노출 이름(`ALLOWED_ROLES`)은
# tests 가 회귀 가드로 import 한다 (private `_ALLOWED_ROLES` 는
# 모듈 내부 전용 alias).
ALLOWED_ROLES = frozenset({"owner", "member", "viewer", "consultant_proxy"})
_ALLOWED_ROLES = ALLOWED_ROLES
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
    """Decoded JWT claims — pure value object.

    Phase 3-0: `tenant_id` is `Optional` to support the pre-onboarding
    path (`decode_jwt(token, require_tenant=False)`). Every other
    authenticated route still receives a concrete UUID because
    `require_tenant=True` (default) rejects empty `app_metadata.tenant_id`
    at decode time.
    """

    tenant_id: uuid.UUID | None
    role: str
    user_id: uuid.UUID
    # Story 6.3 B8: industry is server-controlled (read from
    # tenant_settings via app_metadata.industry). Used by the
    # closing PDF export handler to source the industry from
    # authenticated context rather than the request query string.
    industry: str | None = None
    raw: dict[str, Any] | None = None


def _error_payload(code: str, message_ko: str, trace_id: str | None = None) -> dict[str, Any]:
    """Build the AD-15 error payload."""
    return {
        "code": code,
        "message_ko": message_ko,
        "details": {},
        "trace_id": trace_id or str(uuid.uuid4()),
    }


def decode_jwt(token: str, *, require_tenant: bool = True) -> JWTClaims:
    """Decode and verify a Supabase JWT.

    - HS256 signature verified with `SUPABASE_JWT_SECRET`.
    - `exp` claim validated (with 30s leeway, configurable via JWT_LEEWAY_SEC).
    - `tenant_id` and `role` extracted from `app_metadata` (server-controlled).
    - Raises `TENANT_FORBIDDEN` (401) on any failure.

    Phase 3-0 (Epic 1 carry-over = auth contract): `require_tenant=False` 는
    signup 직후 단계 — 사용자는 Supabase `auth.users` 에 존재하지만 아직
    `tenant_memberships` 가 없어 hook 가 `app_metadata.tenant_id` 를 주입하지
    못한 JWT — 에서 사용한다. 이 경로에서는 tenant_id 가 없어도 `sub` /
    `role` / `industry` 만으로 user identity 를 인정해
    `POST /api/v1/onboarding/complete-signup` 가 첫 테넌트를 만들 수 있게
    한다.
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
            # Walking Skeleton (2026-08-16): explicitly disable `aud`
            # verification. PyJWT 2.x raises `InvalidAudienceError` whenever
            # the token contains an `aud` claim and no explicit `audience`
            # is passed to `decode()`. Supabase tokens always carry
            # `aud: "authenticated"`; we identify tenants via `app_metadata`
            # (AD-3), not via the audience, so the check is unneeded and
            # was rejecting every dev token.
            options={"require": ["exp"], "verify_aud": False},
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
        if require_tenant:
            raise AuthError(
                code=TENANT_FORBIDDEN,
                message_ko="토큰에 테넌트 정보가 없습니다",
                details={"reason": "no_tenant_id"},
            )
        # Phase 3-0: pre-onboarding 경로. tenant_id 가 비어있어도
        # user_id / role / industry 는 인정. 후속 endpoint 가
        # tenant_memberships 를 만들고, 사용자가
        # `supabase.auth.refreshSession()` 으로 새 JWT 를 받으면
        # `app_metadata.tenant_id` 가 채워진다.
        tenant_id = None
    else:
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

    # Phase 3-0 (auth 계약 수직 슬라이스): role allowlist 검증 추가.
    # 기존 코드는 토큰의 role 필드를 그대로 통과시켜 handler-level
    # `require_role("owner")` 만 의존했다. 하지만 SQL GUC인
    # `request.jwt.claims` 로 rebuild 해서 publish 할 때, RLS 정책
    # (예: m0_onboarding 의 `auth.jwt() -> 'app_metadata' ->> 'role'`)
    # 도 이 값을 신뢰한다. 따라서 JWT 시크릿으로 사인된 페이로드라 해도
    # allowlist 바깥의 값은 거부하는 게 옳다.
    # alembic 0001 의 `tenant_memberships.role` CHECK 제약과 동일 집합.
    role_raw = app_metadata.get("role") or "viewer"
    role = str(role_raw)
    if role not in _ALLOWED_ROLES:
        raise AuthError(
            code=TENANT_FORBIDDEN,
            message_ko="토큰의 역할 정보가 유효하지 않습니다",
            details={"reason": "invalid_role", "role": role},
        )
    # Story 6.3 B8: industry is server-controlled and lives in
    # `app_metadata.industry`. If absent (older tokens, before the
    # Story 6.3 wire), the handler will treat it as missing and
    # raise a typed 422 envelope via the service layer.
    industry_raw = app_metadata.get("industry")
    industry = str(industry_raw) if industry_raw is not None else None

    return JWTClaims(
        tenant_id=tenant_id,
        role=role,
        user_id=user_id,
        industry=industry,
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
