"""apps/api/modules/m12_account/handlers.py — Story 12.4 (Epic 12 carry-over sprint) + Story 12.2.

2FA mandatory gate handlers (PRD §F12.1 + §M12-a + AD-15 §4) + Story 12.2
backup export handlers (PRD §F12.2 + NFR4 + AD-10 owner-only).

12 routes (9 pre-existing 2FA + 3 NEW backup export):
- POST /api/v1/account/2fa/setup                    — initiate 2FA setup
- POST /api/v1/account/2fa/verify                   — verify first TOTP code
- POST /api/v1/account/2fa/challenge                — M2 entry gate challenge
- POST /api/v1/account/2fa/recovery                 — verify recovery code
- POST /api/v1/account/2fa/disable                  — disable 2FA (owner-only)
- GET  /api/v1/account/2fa/status                  — read enrollment state
- POST /api/v1/account/2fa/challenge-tokens         — issue HS256 challenge token
- POST /api/v1/account/2fa/challenge-tokens/consume — consume HS256 challenge token
- GET  /api/v1/m2-entry-gate                       — M2 entry gate state check
- GET  /api/v1/account/backups/recent              — list recent backups (owner-only)
- GET  /api/v1/account/backups/{backup_id}/download  — owner self-download (owner-only)
- POST /api/v1/account/backups/trigger             — manual trigger (owner-only)

Service layer is in `apps/api.modules.m12_account.services.two_factor_service`
(setup_totp / verify_and_enable_totp / verify_totp_challenge / verify_recovery_code
/ disable_totp / get_totp_status) + `two_factor_challenge_service`
(issue_challenge_token / consume_challenge_token). Pure kernels live in
`packages.services.m12_account.totp` and `two_factor_gate`.

All audit emission is delegated to the service layer — handlers NEVER call
`emit_audit_typed` directly (parity with M11 close handlers, CR 1.1).

Korean message SSOT: `apps.api.modules.m12_account.services.audit_extension`
exposes `*_KO` constants. The handlers pass these into the typed-exception
envelope via `main.py` exception handlers.

The 2FA capability gate is intentionally absent (CR 12-1 L4): 2FA is an
industry-agnostic security baseline. Owner-only mutations use
`require_role("owner")` per AD-10.

CR 11-2/11-3/12-1 lessons applied:
- All exceptions are typed and mapped to AD-15 §4 envelope in main.py
- TOTP secret NEVER appears in response bodies (NFR5 TLS in transit)
- NFR6 AES-256-GCM ciphertext is service-internal; GET status omits it
- Idempotent no-op: re-setup → 409 ALREADY_ENABLED; re-disable → 404 NOT_ENABLED
- 5-fail lockout → 429 with Retry-After header (mirror M11's
  `_m11_reopen_audit_emit_failed_handler` pattern)
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.capability import require_any_role, require_role
from apps.api.core.db import get_session
from apps.api.core.tenant_context import TenantContext, get_tenant_context

# Korean SSOT constants — passed to exception envelope (main.py handlers).
from apps.api.modules.m12_account.exceptions import TwoFactorNotEnabledError
from apps.api.modules.m12_account.services.account_deletion_service import (
    DeletionChallengeTokenIssued,
    DeletionResult,
    DeletionService,
    DeletionStatusResponse,
)
from apps.api.modules.m12_account.services.audit_extension import (
    DISABLE_UNAUTHORIZED_KO,
    ERROR_CODE_ALREADY_ENABLED,
    ERROR_CODE_AUDIT_EMIT_FAILED,
    ERROR_CODE_CHALLENGE_TOKEN_EXPIRED,
    ERROR_CODE_CHALLENGE_TOKEN_INVALID,
    ERROR_CODE_CHALLENGE_TOKEN_PURPOSE_MISMATCH,
    ERROR_CODE_DISABLE_UNAUTHORIZED,
    ERROR_CODE_ENCRYPTION_FAILED,
    ERROR_CODE_KEY_MISSING,
    ERROR_CODE_NOT_ENABLED,
    ERROR_CODE_RECOVERY_EXHAUSTED,
    ERROR_CODE_USER_NOT_FOUND,
)
from apps.api.modules.m12_account.services.backup_export_service import (
    DEFAULT_LIST_DAYS,
    MAX_LIST_DAYS,
    BackupExportService,
    BackupMetadata,
    BackupResult,
)
from apps.api.modules.m12_account.services.backup_export_service import (
    BackupPayload as BackupPayloadDTO,
)
from apps.api.modules.m12_account.services.two_factor_challenge_service import (
    TwoFactorChallengeService,
)
from apps.api.modules.m12_account.services.two_factor_service import (
    TwoFactorService,
)
from packages.services.m12_account.account_deletion import (
    DELETION_CONSENT_TEMPLATE_KO,
)
from packages.services.m12_account.two_factor_gate import (
    TWO_FACTOR_REQUIRED_KO,
)

router = APIRouter(prefix="/api/v1", tags=["m12-account"])


# ── Helpers ─────────────────────────────────────────────────────
def _resolve_trace_id(ctx: TenantContext, request: Request) -> str:
    """Resolve trace_id with fallback for fleet-wide TenantContext.trace_id bug.

    Mirrors m11_close pattern. 3-tier fallback:
    1. `ctx.trace_id` if attribute exists (forward-compat).
    2. `request.state.trace_id` if set by middleware.
    3. Fresh `uuid4()` as last resort.
    """
    trace_id = getattr(ctx, "trace_id", None)
    if trace_id:
        return str(trace_id)
    request_trace_id = getattr(request.state, "trace_id", None)
    if request_trace_id:
        return str(request_trace_id)
    return str(uuid.uuid4())


def _build_service(session: AsyncSession) -> TwoFactorService:
    """Construct TwoFactorService from request-scoped session."""
    return TwoFactorService(session)


def _build_challenge_service(session: AsyncSession) -> TwoFactorChallengeService:
    """Construct TwoFactorChallengeService from request-scoped session."""
    return TwoFactorChallengeService(session)


# ── Request schemas ─────────────────────────────────────────────
class SetupRequest(BaseModel):
    """POST /api/v1/account/2fa/setup body — currently empty.

    user_id / tenant_id are sourced from the JWT-derived TenantContext
    (AD-3) — clients cannot override.
    """

    model_config = ConfigDict(extra="forbid")


class VerifyRequest(BaseModel):
    """POST /api/v1/account/2fa/verify body — 6-digit TOTP code from authenticator.

    P-22: removed `pattern=r"^\\d{6}$"` so malformed codes flow through to
    the service layer, which raises `TotpInvalidCodeError` (400 envelope
    INVALID_TOTP_CODE) instead of FastAPI's default 422 schema rejection.
    Length check remains (catches obvious client bugs without hard-fail).
    """

    model_config = ConfigDict(extra="forbid")

    code: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="6-digit TOTP code from authenticator app (RFC 6238, ±1 window). "
        "Length floor 1, ceiling 10 so well-formed-but-wrong codes flow "
        "to the service for 400 INVALID_TOTP_CODE envelope.",
    )


class ChallengeRequest(BaseModel):
    """POST /api/v1/account/2fa/challenge body — M2 entry gate TOTP verification."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(
        ...,
        pattern=r"^\d{6}$",
        min_length=6,
        max_length=6,
    )


class RecoveryRequest(BaseModel):
    """POST /api/v1/account/2fa/recovery body — 1회용 recovery code (Crockford base32)."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(
        ...,
        min_length=10,
        max_length=10,
        description="Crockford base32 recovery code (10 chars, no I/L/O/U).",
    )


class DisableRequest(BaseModel):
    """POST /api/v1/account/2fa/disable body.

    Either `current_code` (user possession proof) OR admin override
    (reason length ≥ 20 + actor_id != user_id). The service enforces
    both invariants.

    P-24: `target_user_id` (optional) enables owner-initiated disable
    for a member's 2FA. When None, the handler defaults to
    `ctx.user_id` (self-disable). Without this field, the admin-over-
    ride branch was unreachable.
    """

    model_config = ConfigDict(extra="forbid")

    current_code: str | None = Field(
        default=None,
        pattern=r"^\d{6}$",
        description="Current 6-digit TOTP code (user possession proof).",
    )
    reason: str = Field(
        default="",
        max_length=500,
        description="Audit justification. Required ≥20 chars for admin override.",
    )
    target_user_id: str | None = Field(
        default=None,
        description="Owner-initiated disable for a member's 2FA. "
        "Defaults to self (ctx.user_id) when not provided.",
    )


class ConsumeChallengeTokenRequest(BaseModel):
    """POST /api/v1/account/2fa/challenge-tokens/consume body — HS256 challenge token."""

    model_config = ConfigDict(extra="forbid")

    token: str = Field(
        ...,
        min_length=10,
        description="HS256-signed JWT challenge token issued by the issue endpoint.",
    )


class IssueChallengeTokenRequest(BaseModel):
    r"""POST /api/v1/account/2fa/challenge-tokens body — Story 12.5 P-06 fix.

    The endpoint requires a fresh 6-digit TOTP proof (`current_code`) before
    minting a challenge token. Prior to P-06 the endpoint accepted an empty
    body, which meant any authenticated owner/member could mint a token
    even if their 2FA was misconfigured or compromised.

    With P-06: caller MUST supply a valid current TOTP code. The handler
    delegates to `TwoFactorService.verify_totp_challenge` which raises
    `TotpInvalidCodeError` (400 INVALID_TOTP_CODE), `TotpLockoutError`
    (429 lockout), or `TwoFactorNotEnabledError` (409 NOT_ENABLED) on
    failure paths.

    Mirror of VerifyRequest — same `pattern=r"^\d{6}$"` (P-22 lesson
    from Story 12.4) so malformed codes flow to the service layer for
    the typed-exception envelope rather than a Pydantic 422.
    """

    model_config = ConfigDict(extra="forbid")

    current_code: str = Field(
        ...,
        pattern=r"^\d{6}$",
        min_length=6,
        max_length=6,
        description="Fresh 6-digit TOTP code (RFC 6238, ±1 window). "
        "Required by P-06 to mint a challenge token.",
    )


# ── Response schemas ────────────────────────────────────────────
class SetupResponse(BaseModel):
    """POST /api/v1/account/2fa/setup response envelope.

    Returns `secret` (base32, for QR generation client-side), `uri`
    (otpauth:// URI for authenticator fallback manual entry), and
    `recovery_codes` (8 codes shown ONCE — caller MUST persist to
    user immediately).
    """

    model_config = ConfigDict(extra="forbid")

    secret: str
    uri: str
    recovery_codes: list[str]
    trace_id: str


class VerifyResponse(BaseModel):
    """POST /api/v1/account/2fa/verify response envelope."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool
    enabled_at: str
    trace_id: str


class ChallengeResponse(BaseModel):
    """POST /api/v1/account/2fa/challenge response envelope.

    On success: returns HS256 `challenge_token` (5-min TTL) for M2 entry.
    On failure: returns `remaining_attempts` so UI can warn user.
    """

    model_config = ConfigDict(extra="forbid")

    passed: bool
    challenge_token: str | None
    challenge_token_expires_at: int | None
    remaining_attempts: int
    trace_id: str


class RecoveryResponse(BaseModel):
    """POST /api/v1/account/2fa/recovery response envelope."""

    model_config = ConfigDict(extra="forbid")

    passed: bool
    remaining_recovery_codes: int
    challenge_token: str | None
    challenge_token_expires_at: int | None
    trace_id: str


class DisableResponse(BaseModel):
    """POST /api/v1/account/2fa/disable response envelope."""

    model_config = ConfigDict(extra="forbid")

    disabled: bool
    trace_id: str


class StatusResponse(BaseModel):
    """GET /api/v1/account/2fa/status response envelope.

    Intentionally OMITS `totp_secret` (NFR6 ciphertext, never leaves
    service) and `totp_recovery_codes_hash` (PBKDF2 hashes, also
    service-internal). Returns derived `recovery_codes_remaining`
    count instead.
    """

    model_config = ConfigDict(extra="forbid")

    user_id: str
    tenant_id: str
    totp_enabled: bool
    totp_enabled_at: str | None
    recovery_codes_remaining: int
    failed_attempts: int
    locked_out: bool
    lockout_until: str | None
    trace_id: str


class IssueChallengeTokenResponse(BaseModel):
    """POST /api/v1/account/2fa/challenge-tokens response envelope."""

    model_config = ConfigDict(extra="forbid")

    token: str
    expires_at: int
    trace_id: str


class ConsumeChallengeTokenResponse(BaseModel):
    """POST /api/v1/account/2fa/challenge-tokens/consume response envelope."""

    model_config = ConfigDict(extra="forbid")

    valid: bool
    user_id: str
    tenant_id: str
    trace_id: str


class M2EntryGateResponse(BaseModel):
    """GET /api/v1/m2-entry-gate response envelope.

    Returns whether the user can enter M2 ([월 입력]) given:
    - 2FA enrollment state (TOTP or recovery code path)
    - Role allowlist (owner / member = ALLOWED, viewer / consultant_proxy = DENIED)
    - Active lockout → blocked until lockout_until expires
    """

    model_config = ConfigDict(extra="forbid")

    allowed: bool
    requires_two_factor: bool
    requires_challenge: bool
    role_allowed: bool
    locked_out: bool
    lockout_until: str | None
    message_ko: str
    trace_id: str


# ── POST /api/v1/account/2fa/setup ─────────────────────────────
@router.post(
    "/account/2fa/setup",
    response_model=SetupResponse,
    status_code=201,
    summary="Initiate 2FA setup (PRD §F12.1) — Story 12.1",
)
async def setup_two_factor(
    _payload: SetupRequest,
    request: Request,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _role: None = Depends(require_any_role("owner", "member")),
) -> SetupResponse:
    """Initiate 2FA enrollment for the current user.

    Returns the base32 secret + otpauth URI + 8 recovery codes. The
    caller MUST immediately render these to the user (1회만 응답).
    After this call, the user must POST /account/2fa/verify with a
    6-digit TOTP code from their authenticator app to flip
    `twofa_enabled = true`.

    Raises (handler-level envelope exceptions dispatched via main.py):
    - 400 TWO_FACTOR_ENCRYPTION_ERROR — crypto subsystem failure
    - 500 TWO_FACTOR_KEY_MISSING — env misconfiguration
    - 404 TWO_FACTOR_USER_NOT_FOUND — user_id not in tenant
    - 409 TWO_FACTOR_ALREADY_ENABLED — re-setup without explicit disable
    - 503 TWO_FACTOR_AUDIT_EMIT_FAILED — audit subsystem unavailable
    """
    service = _build_service(session)
    trace_id = _resolve_trace_id(ctx, request)
    result = await service.setup_totp(
        user_id=ctx.user_id,
        tenant_id=ctx.tenant_id,
    )
    await session.commit()
    return SetupResponse(
        secret=result.secret,
        uri=result.uri,
        recovery_codes=list(result.recovery_codes),
        trace_id=trace_id,
    )


# ── POST /api/v1/account/2fa/verify ────────────────────────────
@router.post(
    "/account/2fa/verify",
    response_model=VerifyResponse,
    status_code=200,
    summary="Verify first TOTP code (flip twofa_enabled=true)",
)
async def verify_and_enable_two_factor(
    payload: VerifyRequest,
    request: Request,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _role: None = Depends(require_any_role("owner", "member")),
) -> VerifyResponse:
    """Verify first TOTP code after setup.

    On success: `users.twofa_enabled = true`, `users.totp_enabled_at = now`,
    `users.totp_failed_attempts = 0`. Audit `two_factor_setup_completed`.

    Raises:
    - 400 TWO_FACTOR_NOT_ENABLED — no pending setup
    - 401 TOTP_INVALID_CODE — 6-digit code mismatch
    - 404 TWO_FACTOR_USER_NOT_FOUND
    - 429 TOTP_LOCKOUT — 5-fail → 15-min lockout
    - 503 TWO_FACTOR_AUDIT_EMIT_FAILED
    """
    service = _build_service(session)
    trace_id = _resolve_trace_id(ctx, request)
    await service.verify_and_enable_totp(
        user_id=ctx.user_id,
        tenant_id=ctx.tenant_id,
        code=payload.code,
    )
    await session.commit()
    return VerifyResponse(
        enabled=True,
        enabled_at="",  # service sets users.totp_enabled_at; UI re-fetches /status
        trace_id=trace_id,
    )


# ── POST /api/v1/account/2fa/challenge ─────────────────────────
@router.post(
    "/account/2fa/challenge",
    response_model=ChallengeResponse,
    status_code=200,
    summary="M2 entry gate — verify TOTP code, issue challenge token",
)
async def challenge_two_factor(
    payload: ChallengeRequest,
    request: Request,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _role: None = Depends(require_any_role("owner", "member")),
) -> ChallengeResponse:
    """Verify a 6-digit TOTP code at the M2 entry gate.

    On success: returns HS256 `challenge_token` (5-min TTL) for M2
    entry. The token is single-purpose (purpose=`two_factor_challenge`)
    and bound to (user_id, tenant_id) — cannot be replayed cross-user.

    On failure: increments `totp_failed_attempts`; at 5 the user is
    locked out for 15 minutes (429 with Retry-After).

    Raises:
    - 400 TWO_FACTOR_NOT_ENABLED
    - 401 TOTP_INVALID_CODE
    - 404 TWO_FACTOR_USER_NOT_FOUND
    - 429 TOTP_LOCKOUT (with Retry-After header)
    - 503 TWO_FACTOR_AUDIT_EMIT_FAILED
    """
    service = _build_service(session)
    challenge_service = _build_challenge_service(session)
    trace_id = _resolve_trace_id(ctx, request)

    result = await service.verify_totp_challenge(
        user_id=ctx.user_id,
        tenant_id=ctx.tenant_id,
        code=payload.code,
    )

    if result.passed:
        issued = challenge_service.issue_challenge_token(
            user_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
        )
        await session.commit()
        return ChallengeResponse(
            passed=True,
            challenge_token=issued.token,
            challenge_token_expires_at=issued.expires_at,
            remaining_attempts=result.remaining_attempts,
            trace_id=trace_id,
        )

    # Failure path — service already incremented + audited.
    await session.commit()
    return ChallengeResponse(
        passed=False,
        challenge_token=None,
        challenge_token_expires_at=None,
        remaining_attempts=result.remaining_attempts,
        trace_id=trace_id,
    )


# ── POST /api/v1/account/2fa/recovery ──────────────────────────
@router.post(
    "/account/2fa/recovery",
    response_model=RecoveryResponse,
    status_code=200,
    summary="Verify 1회용 recovery code (authenticator-lost fallback)",
)
async def recovery_two_factor(
    payload: RecoveryRequest,
    request: Request,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _role: None = Depends(require_role("owner")),
) -> RecoveryResponse:
    """Verify a recovery code (fallback when authenticator device lost).

    On success: marks the recovery-code entry `used_at = now()` (1회용),
    returns HS256 challenge token. The entry is consumed — subsequent
    uses of the same code raise `TotpRecoveryInvalidError`.

    When all 8 codes are used: 410 TWO_FACTOR_RECOVERY_EXHAUSTED.
    The user must contact their tenant owner to reset 2FA.

    Raises:
    - 400 TWO_FACTOR_NOT_ENABLED
    - 401 TOTP_RECOVERY_INVALID
    - 404 TWO_FACTOR_USER_NOT_FOUND
    - 410 TWO_FACTOR_RECOVERY_EXHAUSTED
    - 503 TWO_FACTOR_AUDIT_EMIT_FAILED
    """
    service = _build_service(session)
    challenge_service = _build_challenge_service(session)
    trace_id = _resolve_trace_id(ctx, request)

    result = await service.verify_recovery_code(
        user_id=ctx.user_id,
        tenant_id=ctx.tenant_id,
        code=payload.code,
    )

    issued = challenge_service.issue_challenge_token(
        user_id=ctx.user_id,
        tenant_id=ctx.tenant_id,
    )
    await session.commit()
    return RecoveryResponse(
        passed=True,
        remaining_recovery_codes=result.remaining_attempts,
        challenge_token=issued.token,
        challenge_token_expires_at=issued.expires_at,
        trace_id=trace_id,
    )


# ── POST /api/v1/account/2fa/disable ───────────────────────────
@router.post(
    "/account/2fa/disable",
    response_model=DisableResponse,
    status_code=200,
    summary="Disable 2FA (owner-only; code OR admin-override authorization)",
)
async def disable_two_factor(
    payload: DisableRequest,
    request: Request,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _role: None = Depends(require_role("owner")),
) -> DisableResponse:
    """Disable 2FA for the current user.

    Authorization (service-enforced):
    - `current_code` valid TOTP code (user possession proof), OR
    - Admin override: `reason` length ≥ 20 chars + handler verifies
      `actor_id != user_id` (the route's AD-10 role=owner gate is the
      first line of defense).

    On success: NULL `totp_secret` + `totp_recovery_codes_hash`,
    `twofa_enabled=false`. Audit `two_factor_disabled`.

    Raises:
    - 400 TWO_FACTOR_NOT_ENABLED
    - 403 TWO_FACTOR_DISABLE_UNAUTHORIZED
    - 404 TWO_FACTOR_USER_NOT_FOUND
    - 503 TWO_FACTOR_AUDIT_EMIT_FAILED
    """
    service = _build_service(session)
    trace_id = _resolve_trace_id(ctx, request)
    # P-24: target_user_id enables owner-initiated disable for a member.
    # When None, the handler defaults to self (ctx.user_id).
    target_user_id = payload.target_user_id or ctx.user_id
    await service.disable_totp(
        user_id=target_user_id,
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user_id,
        current_code=payload.current_code,
        reason=payload.reason or DISABLE_UNAUTHORIZED_KO,
    )
    await session.commit()
    return DisableResponse(
        disabled=True,
        trace_id=trace_id,
    )


# ── GET /api/v1/account/2fa/status ─────────────────────────────
@router.get(
    "/account/2fa/status",
    response_model=StatusResponse,
    status_code=200,
    summary="Read 2FA enrollment state (no UPDATE, no ciphertext exposure)",
)
async def get_two_factor_status(
    request: Request,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> StatusResponse:
    """Read-only enrollment state.

    Intentionally OMITS `totp_secret` (NFR6 ciphertext) and
    `totp_recovery_codes_hash` (PBKDF2 hashes) — both are
    service-internal. Returns derived `recovery_codes_remaining`
    (entries where `used_at == ""`).

    Raises:
    - 404 TWO_FACTOR_USER_NOT_FOUND
    """
    service = _build_service(session)
    state = await service.get_totp_status(
        user_id=ctx.user_id,
        tenant_id=ctx.tenant_id,
    )
    return StatusResponse(
        user_id=str(state["user_id"]),
        tenant_id=str(state["tenant_id"]),
        totp_enabled=bool(state["totp_enabled"]),
        totp_enabled_at=state["totp_enabled_at"],
        recovery_codes_remaining=int(state["recovery_codes_remaining"]),
        failed_attempts=int(state["failed_attempts"]),
        locked_out=bool(state["locked_out"]),
        lockout_until=state["lockout_until"],
        trace_id=str(state["trace_id"]),
    )


# ── POST /api/v1/account/2fa/challenge-tokens ──────────────────
@router.post(
    "/account/2fa/challenge-tokens",
    response_model=IssueChallengeTokenResponse,
    status_code=201,
    summary="Issue HS256 challenge token (5-min TTL, single-purpose)",
)
async def issue_challenge_token(
    payload: IssueChallengeTokenRequest,
    request: Request,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _role: None = Depends(require_any_role("owner", "member")),
) -> IssueChallengeTokenResponse:
    """Issue a HS256 challenge token (5-min TTL).

    The token is bound to (user_id, tenant_id) and carries
    `purpose=two_factor_challenge`. Use it as the `challenge_token`
    query param on M2 entry routes (e.g. `/api/v1/m2-input/...`).

    Note: callers typically obtain this implicitly via /challenge or
    /recovery success. This endpoint is for explicit re-issuance
    scenarios (e.g. token expired mid-flow).

    P-06 FIX (Story 12.5, AC #7): TOTP proof is required — caller must
    supply a fresh 6-digit `current_code` in the request body. After P-06
    fix, an authenticated user without a valid TOTP code cannot mint a
    challenge token. The handler delegates to
    `TwoFactorService.verify_totp_challenge` which raises typed
    exceptions (TotpInvalidCodeError → 400 INVALID_TOTP_CODE,
    TotpLockoutError → 429 lockout). Wire details:
    - 400 INVALID_TOTP_CODE — code wrong/expired
    - 409 TWO_FACTOR_NOT_ENABLED — user 2FA disabled
    - 422 (Pydantic) — missing/malformed `current_code`
    - 429 TOTP_LOCKOUT — 5-fail lockout active

    Role gate: setup/verify/challenge/challenge-tokens are open to
    `owner` AND `member` (AD-10 self-enrollment for M2-eligible roles).
    Disable/recovery remain `owner`-only per Story 12.4 P-14 (12-5 AC #2).

    Raises:
    - 400 INVALID_TOTP_CODE — TOTP code wrong/expired (P-06 fix)
    - 401 TWO_FACTOR_CHALLENGE_TOKEN_INVALID — JWT signing failed
      (likely missing `COSTMGR_JWT_SECRET`)
    - 409 TWO_FACTOR_NOT_ENABLED — 2FA disabled (P-18 + AC #7)
    - 422 (Pydantic) — missing/malformed `current_code` (P-06 fix)
    - 429 TOTP_LOCKOUT — 5-fail lockout active
    """
    challenge_service = _build_challenge_service(session)
    trace_id = _resolve_trace_id(ctx, request)
    # P-18: reject issue when user has 2FA disabled. Without this, a
    # user whose 2FA was disabled (owner reset / self-disable) could
    # still mint challenge tokens. Mirror of the P-12 consume check.
    service = _build_service(session)
    state = await service.get_totp_status(
        user_id=ctx.user_id,
        tenant_id=ctx.tenant_id,
    )
    if not state["totp_enabled"]:
        raise TwoFactorNotEnabledError(
            user_id=ctx.user_id,
            trace_id=trace_id,
        )

    # P-06 fix: require fresh TOTP proof before minting a challenge token.
    # Delegates to TwoFactorService.verify_totp_challenge which raises
    # TotpInvalidCodeError / TotpLockoutError (typed exceptions mapped
    # to 400 / 429 envelopes in main.py).
    await service.verify_totp_challenge(
        user_id=ctx.user_id,
        tenant_id=ctx.tenant_id,
        code=payload.current_code,
    )

    issued = challenge_service.issue_challenge_token(
        user_id=ctx.user_id,
        tenant_id=ctx.tenant_id,
    )
    return IssueChallengeTokenResponse(
        token=issued.token,
        expires_at=issued.expires_at,
        trace_id=trace_id,
    )


# ── POST /api/v1/account/2fa/challenge-tokens/consume ─────────
@router.post(
    "/account/2fa/challenge-tokens/consume",
    response_model=ConsumeChallengeTokenResponse,
    status_code=200,
    summary="Consume HS256 challenge token (validates purpose + binding)",
)
async def consume_challenge_token(
    payload: ConsumeChallengeTokenRequest,
    request: Request,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _role: None = Depends(require_any_role("owner", "member")),
) -> ConsumeChallengeTokenResponse:
    """Verify and consume a HS256 challenge token.

    Validates:
    1. JWT signature matches `COSTMGR_JWT_SECRET`
    2. Token not expired (exp claim vs now)
    3. `purpose` claim == `two_factor_challenge`
    4. `user_id` claim matches caller
    5. `tenant_id` claim matches caller's tenant
    6. User still has 2FA enabled (P-12)
    7. Token `jti` not already consumed (P-05 replay guard)

    Raises:
    - 401 TWO_FACTOR_CHALLENGE_TOKEN_INVALID — signature / binding mismatch
    - 401 TWO_FACTOR_CHALLENGE_TOKEN_PURPOSE_MISMATCH
    - 401 TWO_FACTOR_CHALLENGE_TOKEN_EXPIRED
    - 401 TWO_FACTOR_CHALLENGE_TOKEN_ALREADY_CONSUMED — replay attempt
    - 401 TWO_FACTOR_NOT_ENABLED — user 2FA disabled after issue
    """
    challenge_service = _build_challenge_service(session)
    trace_id = _resolve_trace_id(ctx, request)
    passed = await challenge_service.consume_challenge_token(
        token=payload.token,
        user_id=ctx.user_id,
        tenant_id=ctx.tenant_id,
    )
    return ConsumeChallengeTokenResponse(
        valid=True,
        user_id=str(passed.user_id),
        tenant_id=str(passed.tenant_id),
        trace_id=trace_id,
    )


# ── GET /api/v1/m2-entry-gate ──────────────────────────────────
@router.get(
    "/m2-entry-gate",
    response_model=M2EntryGateResponse,
    status_code=200,
    summary="M2 entry gate state check (PRD §M12-a) — 2FA + role + lockout",
)
async def get_m2_entry_gate(
    request: Request,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> M2EntryGateResponse:
    """M2 ([월 입력]) entry gate state.

    Returns whether the user can enter M2 given:
    - 2FA enrollment state
    - Role allowlist (owner / member = ALLOWED, viewer / consultant_proxy = DENIED)
    - Active lockout → blocked until lockout_until expires

    This endpoint is intentionally read-only — it does NOT issue a
    challenge token. The client must POST /account/2fa/challenge to
    obtain one.

    Raises:
    - 404 TWO_FACTOR_USER_NOT_FOUND — user not in tenant
    """
    service = _build_service(session)
    trace_id = _resolve_trace_id(ctx, request)

    # Resolve 2FA + lockout state (read-only).
    state = await service.get_totp_status(
        user_id=ctx.user_id,
        tenant_id=ctx.tenant_id,
    )
    totp_enabled = bool(state["totp_enabled"])
    locked_out = bool(state["locked_out"])
    lockout_until = state["lockout_until"]

    # Role gate via pure kernel (AD-10).
    from packages.services.m12_account.two_factor_gate import (
        ALLOWED_M2_ROLES,
        ForbiddenRoleError,
        enforce_role_gate,
    )

    role_state = {
        "user_id": str(ctx.user_id),
        "tenant_id": str(ctx.tenant_id),
        "role": ctx.role,
    }
    role_allowed = ctx.role in ALLOWED_M2_ROLES
    try:
        enforce_role_gate(role_state, target="m2_input")  # raises if denied
    except ForbiddenRoleError:
        role_allowed = False

    # Compose decision (kernel SSOT parity — Story 12.5 D-GATE-01 fix).
    # Kernel `packages/services/m12_account/two_factor_gate.py::check_two_factor_required`
    # returns True when the user has NOT registered TOTP (i.e. setup is required).
    # `requires_two_factor` here means "user MUST set up 2FA before M2 entry".
    requires_two_factor = not totp_enabled
    # `requires_challenge` = user passed setup, must complete a fresh TOTP
    # challenge (POST /account/2fa/challenge) before M2 entry.
    requires_challenge = totp_enabled and not locked_out
    # Allowed = role allowed AND not locked out AND no setup pending.
    # All three gates are kernel-equivalent (enforce_role_gate + check_two_factor_required).
    allowed = role_allowed and not locked_out and not requires_two_factor

    # Message priority: setup missing > locked out > role denied > OK.
    # Mirrors kernel TWO_FACTOR_REQUIRED_KO "2FA 설정이 필요합니다 — [설정하기]".
    if requires_two_factor:
        message_ko = TWO_FACTOR_REQUIRED_KO  # "2FA 설정이 필요합니다 — [설정하기]"
    elif locked_out:
        message_ko = f"2FA 잠금 상태입니다 — {lockout_until} 이후 재시도 가능"
    elif not role_allowed:
        message_ko = "권한이 없습니다 — owner/member role만 [월 입력] 화면 진입 가능"
    else:
        message_ko = "M2 진입 가능"

    return M2EntryGateResponse(
        allowed=allowed,
        requires_two_factor=requires_two_factor,
        requires_challenge=requires_challenge,
        role_allowed=role_allowed,
        locked_out=locked_out,
        lockout_until=lockout_until,
        message_ko=message_ko,
        trace_id=trace_id,
    )


# ── Story 12.2 — Backup export handlers ─────────────────────────
# 3 NEW routes (owner-only per AD-10):
# - GET  /api/v1/account/backups/recent              — list 7-day backups
# - GET  /api/v1/account/backups/{backup_id}/download — JSON download
# - POST /api/v1/account/backups/trigger              — manual trigger
#
# Why no Capability gate (CR 12-1 L4 precedent — industry-agnostic):
# BACKUP_EXPORT capability is documented in capability-matrix v1.14 but
# NOT enforced in any route — backup is owner-only via AD-10 4-role.
# Mirrors TWO_FACTOR_AUTH pattern (industry-agnostic security baseline).


# ── Pydantic schemas (inline — 12-4 convention) ─────────────────
class BackupListItem(BaseModel):
    """Per-row summary in `GET /account/backups/recent` response."""

    model_config = ConfigDict(extra="forbid")

    backup_id: str
    backup_date: str
    schema_version: str
    payload_sha256: str
    payload_size_bytes: int
    row_count_total: int
    audit_log_exported_rows: int
    created_at: str


class BackupListResponse(BaseModel):
    """`GET /account/backups/recent` response envelope."""

    model_config = ConfigDict(extra="forbid")

    items: list[BackupListItem]
    total_count: int
    days: int
    trace_id: str


class BackupTriggerRequest(BaseModel):
    """`POST /account/backups/trigger` body — currently empty.

    Pydantic forbid-extra means clients cannot supply spurious fields
    (12-4 convention). owner_id/tenant_id come from JWT-derived TenantContext.
    """

    model_config = ConfigDict(extra="forbid")


class BackupTriggerResponse(BaseModel):
    """`POST /account/backups/trigger` response envelope."""

    model_config = ConfigDict(extra="forbid")

    backup_id: str
    backup_date: str
    payload_sha256: str
    row_count_total: int
    audit_log_exported_rows: int
    created_at: str
    trace_id: str


def _build_backup_service(
    session: AsyncSession,
    ctx: TenantContext,
    trace_id: str,
) -> BackupExportService:
    """Construct BackupExportService from request-scoped session + ctx."""
    return BackupExportService(
        session,
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user_id,
        trace_id=trace_id,
    )


def _metadata_to_list_item(m: BackupMetadata) -> BackupListItem:
    """Service BackupMetadata → Pydantic BackupListItem (boundary conversion)."""
    return BackupListItem(
        backup_id=str(m.backup_id),
        backup_date=m.backup_date.isoformat()
        if hasattr(m.backup_date, "isoformat")
        else str(m.backup_date),
        schema_version=m.schema_version,
        payload_sha256=m.payload_sha256,
        payload_size_bytes=m.payload_size_bytes,
        row_count_total=m.row_count_total,
        audit_log_exported_rows=m.audit_log_exported_rows,
        created_at=m.created_at.isoformat(),
    )


def _build_backup_filename(backup_date_iso: str) -> str:
    """`backup-YYYY-MM-DD.json` filename (mirror TS `buildBackupFilename`).

    F-06: validates `backup_date_iso` format with regex to prevent
    filename injection via Content-Disposition header (XSS risk).
    If the value is not a valid YYYY-MM-DD, falls back to "unknown".
    """
    import re

    if not re.match(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$", backup_date_iso):
        return "backup-unknown.json"
    return f"backup-{backup_date_iso}.json"


# ── GET /api/v1/account/backups/recent ─────────────────────────
@router.get(
    "/account/backups/recent",
    response_model=BackupListResponse,
    status_code=200,
    summary="최근 7일 백업 목록 조회 (owner-only)",
)
async def list_recent_backups(
    request: Request,
    days: Annotated[
        int,
        Query(
            ge=1,
            le=MAX_LIST_DAYS,
            description="Window size in days (1-30, default 7)",
        ),
    ] = DEFAULT_LIST_DAYS,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _role: None = Depends(require_role("owner")),
) -> BackupListResponse:
    """List backups for the last N days (default 7).

    Owner-only per AD-10 + epics.md Story 12.2 AC #3 ("운영자 UI").
    `member` / `viewer` / `consultant_proxy` are DENIED (403 FORBIDDEN_ROLE).

    Args:
        days: Window size (default 7, max 30).
        ctx: TenantContext (JWT-derived).
        session: AsyncSession.
        _role: require_role("owner") gate.

    Returns:
        BackupListResponse(items=[...], total_count, days, trace_id).
    """
    trace_id = _resolve_trace_id(ctx, request)
    service = _build_backup_service(session, ctx, trace_id)
    metadata_list = await service.list_recent_backups(days=days)
    items = [_metadata_to_list_item(m) for m in metadata_list]
    return BackupListResponse(
        items=items,
        total_count=len(items),
        days=days,
        trace_id=trace_id,
    )


# ── GET /api/v1/account/backups/{backup_id}/download ───────────
@router.get(
    "/account/backups/{backup_id}/download",
    status_code=200,
    response_class=Response,
    summary="백업 JSON 다운로드 (owner-only)",
)
async def download_backup(
    backup_id: Annotated[uuid.UUID, Path(description="Backup UUID (v4)")],
    request: Request,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _role: None = Depends(require_role("owner")),
) -> Response:
    """Download a backup as JSON bytes (Content-Disposition: attachment).

    Response headers:
    - Content-Type: application/json
    - Content-Disposition: attachment; filename="backup-{YYYY-MM-DD}.json"
    - X-Backup-SHA256: <sha256 hex> (client verification)

    Owner-only per AD-10.

    Raises:
    - 404 BACKUP_NOT_FOUND — backup_id missing / purged / cross-tenant.
    """
    import json as _json

    trace_id = _resolve_trace_id(ctx, request)
    service = _build_backup_service(session, ctx, trace_id)
    payload_dto: BackupPayloadDTO = await service.fetch_backup_payload(
        backup_id=backup_id,
    )
    json_bytes = _json.dumps(
        payload_dto.payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
        ensure_ascii=False,
    ).encode("utf-8")
    # Pull backup_date from payload's envelope (top-level field)
    backup_date_iso = str(payload_dto.payload.get("backup_date", "unknown"))
    filename = _build_backup_filename(backup_date_iso)
    return Response(
        content=json_bytes,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Backup-SHA256": payload_dto.payload_sha256,
            "X-Backup-Trace-Id": trace_id,
        },
    )


# ── POST /api/v1/account/backups/trigger ───────────────────────
@router.post(
    "/account/backups/trigger",
    response_model=BackupTriggerResponse,
    status_code=201,
    summary="수동 백업 트리거 (owner-only)",
)
async def trigger_backup(
    payload: BackupTriggerRequest,
    request: Request,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _role: None = Depends(require_role("owner")),
) -> BackupTriggerResponse:
    """Manual owner-triggered backup run.

    Audit-first: emits `backup_triggered` audit BEFORE the actual run.
    Then calls `BackupExportService.run_backup` which emits
    `backup_created` audit.

    Owner-only per AD-10. Returns the new backup metadata.
    """
    trace_id = _resolve_trace_id(ctx, request)
    service = _build_backup_service(session, ctx, trace_id)
    result: BackupResult = await service.trigger_backup()
    return BackupTriggerResponse(
        backup_id=str(result.backup_id),
        backup_date=result.backup_date.isoformat(),
        payload_sha256=result.payload_sha256,
        row_count_total=result.row_count_total,
        audit_log_exported_rows=result.audit_log_exported_rows,
        created_at=result.created_at.isoformat(),
        trace_id=trace_id,
    )


# ── Story 12.3 — Account Deletion + Retention Consent handlers ─────
# 4 NEW routes (PRD §F12.3 + NFR4 2절 + NFR7 + CR 12-5 L3):
# - POST /api/v1/account/deletion/challenge-token — issue TOTP-gated JWT
# - POST /api/v1/account/deletion/request          — destructive (3-layer defense)
# - POST /api/v1/account/deletion/cancel           — owner cancel pending_deletion
# - GET  /api/v1/account/deletion/status           — read-only snapshot
#
# All 4 endpoints require_role("owner") per AD-10 (destructive endpoint
# is owner-only). Capability gate (ACCOUNT_DELETION) ONLY on the
# destructive /request route (CR 12-5 L3 Layer 1).
#
# 3-layer TOTP defense (CR 12-5 L3 — critical for destructive endpoint):
#   Layer 1: route `require_role("owner")` + `require_capability(ACCOUNT_DELETION)`
#   Layer 2: service `verify_totp_challenge` (re-verify, no trust boundary)
#   Layer 3: handler audit-first BEFORE any raise (forensic chain)


# ── Pydantic schemas (inline — 12-4 convention) ─────────────────
class DeletionChallengeTokenRequest(BaseModel):
    """POST /account/deletion/challenge-token body — Story 12.3 P-06 fix.

    Mirrors `IssueChallengeTokenRequest` (12-5 P-06 fix): caller MUST
    supply a fresh 6-digit TOTP code BEFORE the challenge token is minted.
    Without this proof, an authenticated owner could mint a deletion
    challenge token and bypass 2FA on the destructive /request route.
    """

    model_config = ConfigDict(extra="forbid")

    current_code: str = Field(
        ...,
        pattern=r"^\d{6}$",
        min_length=6,
        max_length=6,
        description="Fresh 6-digit TOTP code (RFC 6238, ±1 window). "
        "Required to mint a deletion challenge token.",
    )


class DeletionChallengeTokenResponse(BaseModel):
    """POST /account/deletion/challenge-token response envelope.

    Returns HS256 `token` (5-min TTL, single-purpose
    `purpose="account_deletion"`) + KST `expires_at` ISO-8601.
    """

    model_config = ConfigDict(extra="forbid")

    token: str
    expires_at: str
    trace_id: str


class DeletionConsentRequest(BaseModel):
    """POST /account/deletion/request consent body.

    Caller MUST set `consent_checked=true` AND supply the verbatim
    Korean consent template (DELETION_CONSENT_TEMPLATE_KO) in
    `consent_text`. The service layer validates the text matches
    `validate_consent_text()` (422 DELETION_CONSENT_TEXT_INVALID).
    """

    model_config = ConfigDict(extra="forbid")

    consent_checked: bool = Field(
        ...,
        description="Must be true — explicit consent acknowledgement (CR 12-5 L3 Layer 3).",
    )
    consent_text: str = Field(
        ...,
        min_length=10,
        max_length=200,
        description=f"Verbatim Korean consent template (must equal {DELETION_CONSENT_TEMPLATE_KO!r}).",
    )


class DeletionEnvelopeResponse(BaseModel):
    """POST /account/deletion/request + /cancel response envelope.

    Returns the deletion envelope (TenantDeletionStatus FSM + scheduled_for
    + 30-day retention anchor).
    """

    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    status: str
    deletion_scheduled_for: str
    trace_id: str


class DeletionStatusReadResponse(BaseModel):
    """GET /account/deletion/status response envelope.

    Read-only FSM snapshot for the dashboard. Returns the same envelope
    as `DeletionStatusResponse` from the service layer (no envelope
    conversion — the service already produces the boundary type).
    """

    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    status: str
    deletion_requested_at: str | None
    deletion_requested_by_user_id: str | None
    deletion_consent_id: str | None
    deletion_scheduled_for: str | None
    trace_id: str


def _build_deletion_service(
    session: AsyncSession,
    ctx: TenantContext,
    trace_id: str,
) -> DeletionService:
    """Construct DeletionService from request-scoped session + ctx."""
    return DeletionService(
        session,
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user_id,
        trace_id=trace_id,
    )


# ── POST /api/v1/account/deletion/challenge-token ────────────
@router.post(
    "/account/deletion/challenge-token",
    response_model=DeletionChallengeTokenResponse,
    status_code=201,
    summary="Issue deletion challenge token (TOTP-gated, 5-min TTL)",
)
async def issue_deletion_challenge_token(
    payload: DeletionChallengeTokenRequest,
    request: Request,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _role: None = Depends(require_role("owner")),
) -> DeletionChallengeTokenResponse:
    """Mint HS256 deletion challenge token (5-min TTL).

    Layer 2 of the 3-layer defense (CR 12-5 L3): TOTP proof required
    BEFORE minting. Delegates to `DeletionService.issue_deletion_challenge_token`
    which re-verifies the 6-digit code against the AES-256-GCM decrypted
    secret (mirror two_factor_service.py: AAD = b"totp_secret").

    Raises:
    - 400 INVALID_TOTP_CODE — TOTP code wrong/expired
    - 401 DELETION_CHALLENGE_TOKEN_INVALID — JWT signing failed
      (likely missing `COSTMGR_JWT_SECRET`)
    - 422 (Pydantic) — missing/malformed `current_code`
    - 429 TOTP_LOCKOUT — 5-fail lockout active
    - 503 ACCOUNT_DELETION_AUDIT_EMIT_FAILED
    """
    trace_id = _resolve_trace_id(ctx, request)
    service = _build_deletion_service(session, ctx, trace_id)
    issued: DeletionChallengeTokenIssued = await service.issue_deletion_challenge_token(
        current_code=payload.current_code,
    )
    return DeletionChallengeTokenResponse(
        token=issued.token,
        expires_at=issued.expires_at.isoformat(),
        trace_id=trace_id,
    )


# ── POST /api/v1/account/deletion/request ─────────────────────
@router.post(
    "/account/deletion/request",
    response_model=DeletionEnvelopeResponse,
    status_code=200,
    summary="계정 해지 요청 (destructive endpoint, 3-layer TOTP defense)",
)
async def request_account_deletion(
    payload: DeletionConsentRequest,
    request: Request,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _role: None = Depends(require_role("owner")),
) -> DeletionEnvelopeResponse:
    """Destructive endpoint — account deletion + 30-day retention anchor.

    3-layer TOTP defense (CR 12-5 L3):
    - Layer 1 (route): `require_role("owner")` + `require_capability(ACCOUNT_DELETION)`
    - Layer 2 (service): `_decode_challenge_token` re-verifies the JWT
      + `_verify_owner` re-verifies ownership (no trust boundary).
    - Layer 3 (handler): audit-first `two_factor_verified` BEFORE
      `session.commit()` on the destructive state transition.

    Audit-first invariant (CR 1.1): `deletion_requested` + `deletion_consent_given`
    are emitted INSIDE the service `session.begin_nested()` block
    BEFORE the `tenants.status` FSM transition. The handler does NOT
    emit additional audit rows here — all audit is delegated to the
    service layer (parity with M11 close handlers).

    Raises:
    - 400 INVALID_TOTP_CODE — challenge token expired/invalid
    - 401 DELETION_CHALLENGE_TOKEN_INVALID / EXPIRED
    - 403 FORBIDDEN_ROLE — caller not owner
    - 409 ALREADY_PENDING_DELETION / ALREADY_DELETED — FSM invariant
    - 422 DELETION_CONSENT_TEXT_INVALID — consent text mismatch
    - 500 DELETION_CONSENT_ENCRYPTION_FAILED
    - 503 ACCOUNT_DELETION_AUDIT_EMIT_FAILED
    """
    trace_id = _resolve_trace_id(ctx, request)
    # Layer 3 — capture challenge token from Authorization header.
    # Clients send `Authorization: Bearer <challenge_token>`.
    auth_header = request.headers.get("authorization", "")
    if not auth_header.lower().startswith("bearer "):
        # Layer 2 service will raise the typed exception envelope.
        challenge_token = ""
    else:
        challenge_token = auth_header[len("Bearer ") :].strip()
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    service = _build_deletion_service(session, ctx, trace_id)
    result: DeletionResult = await service.request_deletion(
        challenge_token=challenge_token,
        consent_checked=payload.consent_checked,
        consent_text=payload.consent_text,
        consent_ip=client_ip,
        consent_user_agent=user_agent,
    )
    return DeletionEnvelopeResponse(
        tenant_id=result.tenant_id,
        status=result.status,
        deletion_scheduled_for=result.deletion_scheduled_for.isoformat(),
        trace_id=trace_id,
    )


# ── POST /api/v1/account/deletion/cancel ──────────────────────
@router.post(
    "/account/deletion/cancel",
    response_model=DeletionEnvelopeResponse,
    status_code=200,
    summary="계정 해지 취소 (pending_deletion → active)",
)
async def cancel_account_deletion(
    request: Request,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _role: None = Depends(require_role("owner")),
) -> DeletionEnvelopeResponse:
    """Owner cancels a pending deletion — FSM transition pending_deletion → active.

    Audit-first invariant (CR 1.1): `deletion_cancelled` is emitted
    INSIDE the service BEFORE the FSM transition. Caller does NOT
    need a fresh challenge token (cancel is non-destructive — owner
    may cancel at any time before the 30-day sweep).

    Raises:
    - 403 FORBIDDEN_ROLE — caller not owner
    - 409 ALREADY_ACTIVE / ALREADY_DELETED — FSM invariant
    - 503 ACCOUNT_DELETION_AUDIT_EMIT_FAILED
    """
    trace_id = _resolve_trace_id(ctx, request)
    service = _build_deletion_service(session, ctx, trace_id)
    result: DeletionResult = await service.cancel_deletion()
    return DeletionEnvelopeResponse(
        tenant_id=result.tenant_id,
        status=result.status,
        deletion_scheduled_for=(
            result.deletion_scheduled_for.isoformat() if result.deletion_scheduled_for else ""
        ),
        trace_id=trace_id,
    )


# ── GET /api/v1/account/deletion/status ────────────────────────
@router.get(
    "/account/deletion/status",
    response_model=DeletionStatusReadResponse,
    status_code=200,
    summary="계정 해지 상태 조회 (read-only snapshot)",
)
async def get_account_deletion_status(
    request: Request,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _role: None = Depends(require_role("owner")),
) -> DeletionStatusReadResponse:
    """Read-only FSM snapshot for the dashboard.

    Returns the tenant's current deletion status (`active` / `pending_deletion`
    / `deleted`) + scheduled hard-delete anchor. Owner-only — no member
    or viewer access (forensic data is NFR6-sensitive).

    Raises:
    - 410 ACCOUNT_ALREADY_DELETED — tenant already hard-deleted (CR 11-3
      SnapshotNotFoundError split — terminal state)
    """
    trace_id = _resolve_trace_id(ctx, request)
    service = _build_deletion_service(session, ctx, trace_id)
    status: DeletionStatusResponse = await service.get_deletion_status()
    return DeletionStatusReadResponse(
        tenant_id=status.tenant_id,
        status=status.status,
        deletion_requested_at=(
            status.deletion_requested_at.isoformat() if status.deletion_requested_at else None
        ),
        deletion_requested_by_user_id=status.deletion_requested_by_user_id,
        deletion_consent_id=status.deletion_consent_id,
        deletion_scheduled_for=(
            status.deletion_scheduled_for.isoformat() if status.deletion_scheduled_for else None
        ),
        trace_id=trace_id,
    )


# Re-export error codes for main.py exception handlers convenience.
__all__ = [
    "router",
    "ERROR_CODE_NOT_ENABLED",
    "ERROR_CODE_ALREADY_ENABLED",
    "ERROR_CODE_AUDIT_EMIT_FAILED",
    "ERROR_CODE_ENCRYPTION_FAILED",
    "ERROR_CODE_KEY_MISSING",
    "ERROR_CODE_RECOVERY_EXHAUSTED",
    "ERROR_CODE_DISABLE_UNAUTHORIZED",
    "ERROR_CODE_USER_NOT_FOUND",
    "ERROR_CODE_CHALLENGE_TOKEN_EXPIRED",
    "ERROR_CODE_CHALLENGE_TOKEN_INVALID",
    "ERROR_CODE_CHALLENGE_TOKEN_PURPOSE_MISMATCH",
]
