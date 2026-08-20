"""tests.api.core.test_phase_3_0_rls_bridge — Phase 3-0 auth contract regression tests.

Phase 3-0 (cj-style Epic 14 carry-over 2번째, "fix" 종류) — auth 계약
수직 슬라이스 진입 결정 wire. 이 파일은 **DB 없이** 안전 속성만 검증하는
빠른 회귀 가드이다. 통합 시나리오(실제 Postgres + RLS)는
`tests/rls/test_tenant_isolation.py` + 추가 케이스로
`RLS_RUN_LOCAL=1` 게이트에서 실행한다 (현 sprint 범위 밖).

검증 항목:

1. **role allowlist** (`decode_jwt`)
   - 알 수 없는 role → `AuthError(TENANT_FORBIDDEN, "invalid_role")`
   - 4개 정식 role(owner / member / viewer / consultant_proxy) 모두 통과
   - role 누락 → 기본 "viewer" (Story 0.2 Task 5.3 동작 호환)

2. **listener GUC 발행 SQL 정확성** (`attach_tenant_listener`)
   - 정확한 GUC 이름 3개(`app.tenant_id`, `app.user_id`, `request.jwt.claims`)
   - 정확한 직렬화 형태 (UUID 보존, role 보존, JSON compact)
   - service_role 경로(snapshot 미설정) → GUC 0개 발행 (fail-safe)
   - Raw JWT payload 미사용 — `JWTClaims` 의 검증된 컴포넌트로만 재구성

3. **SQL injection 방어** (안전 속성)
   - json.dumps 가 single quote 를 절대 emit 하지 않음
   - `_TenantClaimsSnapshot` 이 frozen 이고 raw payload 슬롯이 없음
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import json
import re
import uuid
from typing import Any

import jwt
import pytest

from apps.api.core.security import (
    ALLOWED_ROLES,
    TENANT_FORBIDDEN,
    AuthError,
    JWTClaims,
    decode_jwt,
)
from apps.api.core.tenant_context import (
    _TenantClaimsSnapshot,
    attach_tenant_listener,
)

# ── Helpers ────────────────────────────────────────────────────────


def _forge_jwt(
    secret: str,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    role: str,
    industry: str | None = None,
    extra_app_metadata: dict[str, Any] | None = None,
) -> str:
    """Forge a valid HS256 JWT for testing.

    `exp` is 1 hour from now (within the 30s leeway accepted by
    `decode_jwt`).
    """
    app_metadata: dict[str, Any] = {
        "tenant_id": str(tenant_id),
        "role": role,
    }
    if industry is not None:
        app_metadata["industry"] = industry
    if extra_app_metadata:
        app_metadata.update(extra_app_metadata)
    payload = {
        "sub": str(user_id),
        "app_metadata": app_metadata,
        "exp": dt.datetime.now(dt.UTC) + dt.timedelta(hours=1),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def _install_listener_recorder() -> tuple[Any, Any, Any, list[str]]:
    """Attach the real `attach_tenant_listener` to a stub engine while
    capturing the SQLAlchemy `begin` handler and the set/clear callbacks.

    Returns `(set_claims_cb, clear_claims_cb, begin_handler, issued_sqls)`.
    The caller populates claims via `set_claims_cb(...)`, then fires
    `begin_handler(recorder_conn)` where `recorder_conn.exec_driver_sql`
    appends to `issued_sqls`.
    """
    from apps.api.core import tenant_context as tc_module

    captured: dict[str, Any] = {"handlers": []}

    def fake_listens_for(*_args: Any, **_kwargs: Any):
        def deco(fn: Any) -> Any:
            captured["handlers"].append(fn)
            return fn

        return deco

    original = tc_module.event.listens_for
    tc_module.event.listens_for = fake_listens_for  # type: ignore[attr-defined]
    try:

        class _StubEngine:
            # `attach_tenant_listener` reads `engine.sync_engine` at
            # decoration time (before our fake `event.listens_for` runs).
            # Provide any sentinel — our fake ignores the target.
            sync_engine = object()

        stub = _StubEngine()
        attach_tenant_listener(stub)  # type: ignore[arg-type]

        hooks = tc_module._ENGINE_HOOKS.get(id(stub))
        assert hooks is not None, "set_claims/clear_claims not registered"
        set_claims_cb, clear_claims_cb = hooks

        handler = captured["handlers"][-1]

        issued: list[str] = []

        class _RecorderConn:
            def exec_driver_sql(self, sql: str) -> None:
                issued.append(sql)

        # Bind the handler to the recorder via a closure so callers
        # don't need to know about the conn shape.
        def fire() -> None:
            handler(_RecorderConn())

        return set_claims_cb, clear_claims_cb, fire, issued
    finally:
        tc_module.event.listens_for = original  # type: ignore[attr-defined]


@pytest.fixture
def listener_recorder():
    """Pytest fixture that yields `_install_listener_recorder()` results."""
    return _install_listener_recorder()


# ── 1. role allowlist (decode_jwt) ────────────────────────────────


def test_decode_jwt_rejects_unknown_role(monkeypatch: pytest.MonkeyPatch) -> None:
    """Phase 3-0: role not in allowlist → TENANT_FORBIDDEN invalid_role."""
    from apps.api.core.settings import get_settings

    settings = get_settings()
    secret = settings.supabase_jwt_secret or "test-secret-for-phase-3-0"
    monkeypatch.setattr(settings, "supabase_jwt_secret", secret, raising=False)

    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    token = _forge_jwt(
        secret,
        tenant_id=tenant_id,
        user_id=user_id,
        role="super_admin",  # NOT in allowlist
    )

    with pytest.raises(AuthError) as exc_info:
        decode_jwt(token)
    assert exc_info.value.code == TENANT_FORBIDDEN
    assert exc_info.value.details.get("reason") == "invalid_role"
    assert exc_info.value.details.get("role") == "super_admin"


def test_decode_jwt_accepts_all_four_roles(monkeypatch: pytest.MonkeyPatch) -> None:
    """Phase 3-0: 4-role allowlist (alembic 0001 tenant_memberships.role CHECK와 동일)."""
    from apps.api.core.settings import get_settings

    settings = get_settings()
    secret = settings.supabase_jwt_secret or "test-secret-for-phase-3-0"
    monkeypatch.setattr(settings, "supabase_jwt_secret", secret, raising=False)

    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    for role in sorted(ALLOWED_ROLES):
        token = _forge_jwt(secret, tenant_id=tenant_id, user_id=user_id, role=role)
        claims = decode_jwt(token)
        assert claims.role == role, f"role {role!r} should pass allowlist"
        assert claims.tenant_id == tenant_id
        assert claims.user_id == user_id


def test_decode_jwt_default_role_is_viewer(monkeypatch: pytest.MonkeyPatch) -> None:
    """role 누락 시 기본값 "viewer" (Story 0.2 Task 5.3 기본 동작 호환)."""
    from apps.api.core.settings import get_settings

    settings = get_settings()
    secret = settings.supabase_jwt_secret or "test-secret-for-phase-3-0"
    monkeypatch.setattr(settings, "supabase_jwt_secret", secret, raising=False)

    payload = {
        "sub": str(uuid.uuid4()),
        "app_metadata": {"tenant_id": str(uuid.uuid4())},  # no role key
        "exp": dt.datetime.now(dt.UTC) + dt.timedelta(hours=1),
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    claims = decode_jwt(token)
    assert claims.role == "viewer"


# ── 2. listener GUC 발행 SQL 정확성 ──────────────────────────────


def test_listener_publishes_three_gucs_for_known_claims(
    listener_recorder: tuple[Any, Any, Any, list[str]],
) -> None:
    """Phase 3-0: 정상 claims → 3개 GUC 발행 (app.tenant_id, app.user_id, request.jwt.claims).

    이 테스트가 빨간불이면 listener 가 정책이 기대하는 GUC 이름 중 하나를
    빠뜨렸다는 뜻이다. RLS 가 빈 GUC를 보고 모든 행을 숨기는 회귀를 잡는다.
    """
    set_claims_cb, _clear_claims_cb, fire, issued = listener_recorder

    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    set_claims_cb(
        JWTClaims(
            tenant_id=tenant_id,
            role="owner",
            user_id=user_id,
            industry="manufacturing",
            raw=None,
        )
    )
    fire()

    assert len(issued) == 3, f"expected 3 GUCs, got {len(issued)}: {issued}"

    # 1) app.tenant_id
    assert any(
        sql == f"SET LOCAL app.tenant_id = '{tenant_id}'" for sql in issued
    ), f"missing app.tenant_id GUC; got {issued}"

    # 2) app.user_id
    assert any(
        sql == f"SET LOCAL app.user_id = '{user_id}'" for sql in issued
    ), f"missing app.user_id GUC; got {issued}"

    # 3) request.jwt.claims — JSON with sub + app_metadata
    jwt_claims_sqls = [s for s in issued if s.startswith("SET LOCAL request.jwt.claims")]
    assert len(jwt_claims_sqls) == 1
    match = re.match(r"SET LOCAL request\.jwt\.claims = '(.+)'$", jwt_claims_sqls[0])
    assert match is not None, f"malformed jwt.claims SQL: {jwt_claims_sqls[0]!r}"
    parsed = json.loads(match.group(1))
    assert parsed["sub"] == str(user_id)
    assert parsed["app_metadata"]["tenant_id"] == str(tenant_id)
    assert parsed["app_metadata"]["role"] == "owner"


def test_listener_is_noop_when_no_snapshot(
    listener_recorder: tuple[Any, Any, Any, list[str]],
) -> None:
    """Phase 3-0: service_role 경로(claims 미설정) → GUC 0개 발행.

    RLS는 GUC 가 비어 있으면 0행을 반환하므로, service_role이 우연히
    풀의 연결을 잡았을 때 직전 요청의 테넌트가 새 요청에 새지 않는다는
    fail-safe 동작을 검증한다.
    """
    _set_claims_cb, _clear_claims_cb, fire, issued = listener_recorder
    fire()
    assert issued == [], f"service_role path must issue 0 GUCs, got {issued}"


def test_listener_json_is_safe_against_role_injection(
    listener_recorder: tuple[Any, Any, Any, list[str]],
) -> None:
    """Phase 3-0: 4개 allowlist role 모두 SQL literal 안에 single quote 가 없다.

    json.dumps 는 string 에 대해 항상 double quote 를 emit 하고,
    allowlist role 문자열에는 single quote / backslash 가 없으므로
    (alembic 0001 CHECK 가 그 문자를 거부), SQL literal 안에
    그대로 넣어도 깨지지 않는다.
    """
    set_claims_cb, _clear_claims_cb, fire, issued = listener_recorder
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()

    for role in sorted(ALLOWED_ROLES):
        issued.clear()
        set_claims_cb(
            JWTClaims(
                tenant_id=tenant_id,
                role=role,
                user_id=user_id,
                industry=None,
                raw=None,
            )
        )
        fire()

        jwt_sql = next(s for s in issued if "request.jwt.claims" in s)
        # 시작/끝 따옴표 제외한 안쪽에 single quote 가 없어야 한다.
        inner = jwt_sql[len("SET LOCAL request.jwt.claims = '") : -1]
        assert "'" not in inner, (
            f"role {role!r}: json payload contains single quote, would break SQL literal: {inner!r}"
        )


def test_listener_does_not_publish_raw_jwt_payload(
    listener_recorder: tuple[Any, Any, Any, list[str]],
) -> None:
    """Phase 3-0: listener 는 `claims.raw` 를 publish 하지 않는다.

    JWT 가 임의 키 (예: `app_metadata.rogue_key`) 를 실어와도, listener 는
    validated components (UUID tenant_id, UUID user_id, allowlist role)
    로만 GUC 를 rebuild 하므로 raw payload 가 GUC 에 누설되지 않는다.
    """
    set_claims_cb, _clear_claims_cb, fire, issued = listener_recorder

    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    rogue_payload = {
        "sub": str(user_id),
        "app_metadata": {
            "tenant_id": str(tenant_id),
            "role": "owner",
            "rogue_key": "'; DROP TABLE tenants; --",
            "nested": {"deep": "value"},
        },
        "exp": 9_999_999_999,
    }
    # JWTClaims.raw 는 다른 모듈에서 사용되므로 보존된다 — 그러나 listener 는
    # 그것을 publish 하지 말아야 한다.
    set_claims_cb(
        JWTClaims(
            tenant_id=tenant_id,
            role="owner",
            user_id=user_id,
            industry=None,
            raw=rogue_payload,
        )
    )
    fire()

    joined = "\n".join(issued)
    assert "DROP TABLE" not in joined, (
        f"raw payload leaked into GUC SQL — listener is not using validated components: {issued}"
    )
    assert "rogue_key" not in joined
    assert "nested" not in joined


# ── 3. SQL injection 방어 ────────────────────────────────────────


def test_tenant_claims_snapshot_is_frozen_and_minimal() -> None:
    """Phase 3-0: `_TenantClaimsSnapshot` 는 frozen 이고 raw payload 슬롯이 없다.

    만약 listener 가 raw payload 를 publish 하려면 snapshot 에 raw 슬롯이
    있어야 한다. 슬롯이 없다는 것은 컴파일 시점에 안전을 보장한다.
    """
    snap = _TenantClaimsSnapshot(
        tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        user_id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
        role="owner",
    )
    # frozen=True → mutation 시 FrozenInstanceError.
    with pytest.raises(dataclasses.FrozenInstanceError):
        snap.tenant_id = uuid.uuid4()  # type: ignore[misc]
    # 그리고 raw payload 슬롯이 아예 없다.
    assert not hasattr(snap, "raw")
    assert not hasattr(snap, "payload")
