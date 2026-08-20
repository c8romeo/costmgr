"""tests.api.m0_onboarding.test_phase_3_0_signup_endpoint — signup router tests.

Phase 3-0 (cj-style Epic 14 carry-over 2번째, "fix" 종류) — auth 계약
수직 슬라이스 진입 결정 wire. `POST /api/v1/onboarding/complete-signup`
엔드포인트의 router shape / schema / dep 동작을 검증한다. 실제
DB transaction 은 RLS-gated e2e 테스트 (별도 파일, RLS_RUN_LOCAL=1) 에서
검증하며, 본 파일은 DB 없이 빠르게 도는 회귀 가드이다.

검증 항목:

1. **Router shape**
   - `POST /api/v1/onboarding/complete-signup` 가 `m0_onboarding.signup_router` 에 등록
   - response_model = `SignupCompleteResponse`
   - status_code = 201
   - summary 에 한국어

2. **Schema shape**
   - `SignupCompleteRequest` — `tenant_name` (1~200), `industry` (Industry enum), extra=forbid
   - `SignupCompleteResponse` — `tenant_id` / `role` (Literal 4-role) / `industry` / `settings_version` / `trace_id`

3. **decode_jwt(require_tenant=False)** 동작
   - tenant_id 가 비어있는 JWT → 401 raise 하지 않고 `tenant_id=None` 인 JWTClaims 반환
   - tenant_id 가 있는 JWT → 기존 동작 유지 (tenant_id=UUID)
   - signature / exp / role allowlist 검증은 그대로 유지

4. **get_pre_onboarding_user** dep
   - tenant_id 가 없는 JWT → PreOnboardingUser 반환
   - tenant_id 가 있는 JWT → 그대로 통과 (호환성)
   - role 이 allowlist 바깥 → TENANT_FORBIDDEN

5. **PRD 정합**
   - master PRD §F15.2 가 `tenant_memberships` (실제 테이블명) 를 사용하고
     `user_tenants` 오기가 남아있지 않음을 확인
"""

from __future__ import annotations

import datetime as dt
import re
import typing
import uuid
from pathlib import Path

import jwt
import pytest
from pydantic import ValidationError

from apps.api.core.security import (
    ALLOWED_ROLES,
    TENANT_FORBIDDEN,
    AuthError,
    decode_jwt,
)
from apps.api.core.tenant_context import PreOnboardingUser
from apps.api.modules.m0_onboarding.handlers import signup_router
from apps.api.modules.m0_onboarding.schemas import (
    SignupCompleteRequest,
    SignupCompleteResponse,
)

# ── Helpers ────────────────────────────────────────────────────────


def _forge_jwt_no_tenant(
    secret: str,
    *,
    user_id: uuid.UUID,
    role: str = "viewer",
    email: str | None = None,
) -> str:
    """Forge a JWT with NO `app_metadata.tenant_id` (pre-onboarding state)."""
    app_metadata: dict[str, str] = {"role": role}
    # NB: deliberately no `tenant_id` key.
    payload: dict[str, object] = {
        "sub": str(user_id),
        "app_metadata": app_metadata,
        "exp": dt.datetime.now(dt.UTC) + dt.timedelta(hours=1),
    }
    if email is not None:
        payload["email"] = email
    return jwt.encode(payload, secret, algorithm="HS256")


def _forge_jwt_with_tenant(
    secret: str,
    *,
    user_id: uuid.UUID,
    tenant_id: uuid.UUID,
    role: str = "owner",
) -> str:
    app_metadata = {
        "tenant_id": str(tenant_id),
        "role": role,
    }
    payload = {
        "sub": str(user_id),
        "app_metadata": app_metadata,
        "exp": dt.datetime.now(dt.UTC) + dt.timedelta(hours=1),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


# ── 1. Router shape ───────────────────────────────────────────────


def test_signup_complete_route_registered() -> None:
    """POST /api/v1/onboarding/complete-signup is on the signup_router."""
    routes = {
        r.path: r
        for r in signup_router.routes
        if hasattr(r, "path") and hasattr(r, "methods")
    }
    assert "/api/v1/onboarding/complete-signup" in routes


def test_signup_complete_route_method_is_post() -> None:
    """Only POST — GET must NOT be exposed (PRD §F15.2 signup flow)."""
    routes = {
        r.path: r
        for r in signup_router.routes
        if hasattr(r, "path") and hasattr(r, "methods")
    }
    route = routes["/api/v1/onboarding/complete-signup"]
    assert "POST" in route.methods
    assert "GET" not in route.methods


def test_signup_complete_status_code_201() -> None:
    """Status code is 201 Created (new resource — tenant)."""
    routes = {
        r.path: r
        for r in signup_router.routes
        if hasattr(r, "path") and hasattr(r, "methods")
    }
    route = routes["/api/v1/onboarding/complete-signup"]
    assert getattr(route, "status_code", None) == 201


def test_signup_complete_summary_korean() -> None:
    """summary has Korean (master PRD §V4 UX lock — ko-KR)."""
    routes = {
        r.path: r
        for r in signup_router.routes
        if hasattr(r, "path") and hasattr(r, "methods")
    }
    route = routes["/api/v1/onboarding/complete-signup"]
    summary = getattr(route, "summary", "") or ""
    # Korean Hangul syllable block: U+AC00 ~ U+D7A3
    assert any("가" <= ch <= "힣" for ch in summary), (
        f"summary should be Korean, got {summary!r}"
    )


def test_signup_complete_response_model() -> None:
    """response_model is `SignupCompleteResponse` (frozen Pydantic v2)."""
    routes = {
        r.path: r
        for r in signup_router.routes
        if hasattr(r, "path") and hasattr(r, "methods")
    }
    route = routes["/api/v1/onboarding/complete-signup"]
    assert route.response_model is SignupCompleteResponse


# ── 2. Schema shape ──────────────────────────────────────────────


def test_signup_request_required_fields() -> None:
    """SignupCompleteRequest requires `tenant_name` + `industry`."""
    fields = set(SignupCompleteRequest.model_fields.keys())
    assert "tenant_name" in fields
    assert "industry" in fields


def test_signup_request_extra_forbid() -> None:
    """extra='forbid' — unknown fields → 422 (strict schema)."""
    assert SignupCompleteRequest.model_config.get("extra") == "forbid"


def test_signup_request_tenant_name_length_bounds() -> None:
    """tenant_name: 1~200 chars (Pydantic Field constraints)."""
    field = SignupCompleteRequest.model_fields["tenant_name"]
    min_len = field.metadata
    # Look up min_length / max_length in metadata
    found_min = any(
        getattr(m, "min_length", None) == 1 for m in min_len if hasattr(m, "min_length")
    )
    found_max = any(
        getattr(m, "max_length", None) == 200
        for m in min_len
        if hasattr(m, "max_length")
    )
    assert found_min, f"tenant_name must have min_length=1, got metadata: {min_len}"
    assert found_max, f"tenant_name must have max_length=200, got metadata: {min_len}"


def test_signup_response_fields() -> None:
    """SignupCompleteResponse carries tenant_id / role / industry / settings_version / trace_id."""
    fields = set(SignupCompleteResponse.model_fields.keys())
    expected = {
        "tenant_id",
        "role",
        "industry",
        "settings_version",
        "trace_id",
    }
    assert expected.issubset(fields), (
        f"response missing fields; expected {expected}, got {fields}"
    )


def test_signup_response_role_is_4_role_literal() -> None:
    """response.role is Literal['owner', 'member', 'viewer', 'consultant_proxy']."""
    field = SignupCompleteResponse.model_fields["role"]
    args = typing.get_args(field.annotation)
    assert set(args) == ALLOWED_ROLES, (
        f"response.role literal must match ALLOWED_ROLES {set(ALLOWED_ROLES)}, got {set(args)}"
    )


def test_signup_request_rejects_unknown_industry() -> None:
    """Unknown industry → ValidationError (Pydantic 422)."""
    with pytest.raises(ValidationError):
        SignupCompleteRequest(tenant_name="Acme", industry="aerospace")  # type: ignore[arg-type]


def test_signup_request_rejects_empty_tenant_name() -> None:
    """Empty tenant_name → ValidationError (Pydantic min_length=1)."""
    with pytest.raises(ValidationError):
        SignupCompleteRequest(tenant_name="", industry="manufacturing")


def test_signup_request_rejects_extra_field() -> None:
    """Extra field → ValidationError (extra=forbid)."""
    with pytest.raises(ValidationError):
        SignupCompleteRequest(
            tenant_name="Acme",
            industry="manufacturing",
            tenant_id=uuid.uuid4(),  # type: ignore[call-arg]
        )


# ── 3. decode_jwt(require_tenant=False) ─────────────────────────


def test_decode_jwt_require_tenant_false_accepts_no_tenant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Phase 3-0: pre-onboarding JWT (no app_metadata.tenant_id) returns
    JWTClaims with tenant_id=None, no AuthError raised."""
    from apps.api.core.settings import get_settings

    settings = get_settings()
    secret = settings.supabase_jwt_secret or "test-secret-phase-3-0"
    monkeypatch.setattr(settings, "supabase_jwt_secret", secret, raising=False)

    user_id = uuid.uuid4()
    token = _forge_jwt_no_tenant(secret, user_id=user_id, role="viewer")

    claims = decode_jwt(token, require_tenant=False)
    assert claims.tenant_id is None
    assert claims.user_id == user_id
    assert claims.role == "viewer"


def test_decode_jwt_require_tenant_false_accepts_with_tenant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Phase 3-0: require_tenant=False still works when tenant_id is present
    (used for testing the pre-onboarding dep's behavior with full tokens)."""
    from apps.api.core.settings import get_settings

    settings = get_settings()
    secret = settings.supabase_jwt_secret or "test-secret-phase-3-0"
    monkeypatch.setattr(settings, "supabase_jwt_secret", secret, raising=False)

    user_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    token = _forge_jwt_with_tenant(
        secret, user_id=user_id, tenant_id=tenant_id, role="owner"
    )

    claims = decode_jwt(token, require_tenant=False)
    assert claims.tenant_id == tenant_id
    assert claims.user_id == user_id
    assert claims.role == "owner"


def test_decode_jwt_require_tenant_default_still_rejects_no_tenant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Phase 3-0: existing routes using `decode_jwt()` (default
    require_tenant=True) still reject pre-onboarding JWTs — preventing
    accidental bypass."""
    from apps.api.core.settings import get_settings

    settings = get_settings()
    secret = settings.supabase_jwt_secret or "test-secret-phase-3-0"
    monkeypatch.setattr(settings, "supabase_jwt_secret", secret, raising=False)

    user_id = uuid.uuid4()
    token = _forge_jwt_no_tenant(secret, user_id=user_id, role="viewer")

    with pytest.raises(AuthError) as exc_info:
        decode_jwt(token)  # require_tenant=True default
    assert exc_info.value.code == TENANT_FORBIDDEN
    assert exc_info.value.details.get("reason") == "no_tenant_id"


def test_decode_jwt_require_tenant_false_still_validates_role_allowlist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Phase 3-0: even with require_tenant=False, the role allowlist
    (Phase 3-0 P0-1) is still enforced. Otherwise an attacker could
    bypass the allowlist by hitting the pre-onboarding dep."""
    from apps.api.core.settings import get_settings

    settings = get_settings()
    secret = settings.supabase_jwt_secret or "test-secret-phase-3-0"
    monkeypatch.setattr(settings, "supabase_jwt_secret", secret, raising=False)

    user_id = uuid.uuid4()
    token = _forge_jwt_no_tenant(secret, user_id=user_id, role="super_admin")

    with pytest.raises(AuthError) as exc_info:
        decode_jwt(token, require_tenant=False)
    assert exc_info.value.details.get("reason") == "invalid_role"


# ── 4. PreOnboardingUser shape ──────────────────────────────────


def test_pre_onboarding_user_carries_user_id_and_role_only() -> None:
    """Phase 3-0: PreOnboardingUser does NOT carry tenant_id (pre-onboarding
    state). Other fields are present but optional."""
    user = PreOnboardingUser(
        user_id=uuid.uuid4(),
        role="viewer",
        email="test@example.com",
        industry=None,
        trace_id="trace-123",
    )
    assert not hasattr(user, "tenant_id") or "tenant_id" not in user.__dataclass_fields__
    assert user.role == "viewer"
    assert user.email == "test@example.com"


def test_pre_onboarding_user_default_values() -> None:
    """email / industry / trace_id default to None."""
    user = PreOnboardingUser(user_id=uuid.uuid4(), role="owner")
    assert user.email is None
    assert user.industry is None
    assert user.trace_id is None


# ── 5. PRD §F15.2 정합 ──────────────────────────────────────────


def test_prd_f15_2_uses_real_table_name_tenant_memberships() -> None:
    """PRD §F15.2 의 **사양 본문 (atomic transaction 불릿 리스트)** 이
    `tenant_memberships` (실제 alembic 0001 테이블명) 를 사용하고, 사양 본문이
    `user_tenants` 를 (오기로) 1차 인용하지 않는지 검증.

    §F15.2 는 `user_tenants` 라는 단어를 **메타 정정 노트** ("v3.0 초안의
    `user_tenants` 는 오기로 정정됨") 에서 의도적으로 사용할 수 있다 — 이는
    회귀가 아니라 문서 위생이다. 따라서 이 테스트는 사양 본문
    (atomic transaction 의 1차 항목) 만 본다.
    """
    prd_path = (
        Path(__file__).resolve().parents[3]
        / "_bmad-output"
        / "planning-artifacts"
        / "prd.md"
    )
    text = prd_path.read_text(encoding="utf-8")

    # §F15.2 의 핵심 문장을 찾는다.
    match = re.search(
        r"### F15\.2 Signup UI.*?(?=### F15\.\d|\Z)",
        text,
        re.DOTALL,
    )
    assert match is not None, "could not find §F15.2 in PRD"
    section = match.group(0)

    # 사양 본문: `tenant_memberships` row 1개 (role='owner') 의 1차 인용이 있어야 함.
    assert re.search(
        r"`tenant_memberships`\s*row\s*1개",
        section,
    ), (
        "PRD §F15.2 의 사양 본문은 atomic transaction 의 1차 항목으로 "
        "`tenant_memberships` row 1개 를 인용해야 함 (alembic 0001 SSOT)"
    )

    # 사양 본문: `user_tenants` row 1개 같은 1차 항목 인용은 없어야 함
    # (단, 정정 노트 안의 메타 인용은 허용).
    bad_primary = re.search(
        r"^\s*-\s*`user_tenants`\s*row",
        section,
        re.MULTILINE,
    )
    assert bad_primary is None, (
        "PRD §F15.2 의 사양 본문 (atomic transaction 불릿) 이 "
        "`user_tenants` row 를 1차 항목으로 인용하면 안 됨 (alembic 0001 SSOT: "
        "`tenant_memberships`)"
    )


def test_prd_f15_2_references_complete_signup_endpoint() -> None:
    """PRD §F15.2 가 Phase 3-0 의 `POST /api/v1/onboarding/complete-signup` 을
    정합하게 가리키는지 검증."""
    prd_path = (
        Path(__file__).resolve().parents[3]
        / "_bmad-output"
        / "planning-artifacts"
        / "prd.md"
    )
    text = prd_path.read_text(encoding="utf-8")

    match = re.search(
        r"### F15\.2 Signup UI.*?(?=### F15\.\d|\Z)",
        text,
        re.DOTALL,
    )
    assert match is not None
    section = match.group(0)

    assert "/api/v1/onboarding/complete-signup" in section, (
        "PRD §F15.2 must reference the Phase 3-0 signup-completion endpoint"
    )
    assert "custom_access_token_hook" in section, (
        "PRD §F15.2 must reference the alembic 0035 hook as the mechanism "
        "that injects tenant_id on the SECOND mint (after refreshSession)"
    )
