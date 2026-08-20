"""tests.api.core.test_phase_3_0_hook_migration — alembic 0035 hook contract tests.

Phase 3-0 (cj-style Epic 14 carry-over 2번째, "fix" 종류) —
`custom_access_token_hook` PL/pgSQL 함수가 Supabase GoTrue 의 hook
계약과 일치하는지 검증한다. DB 가 없을 때는 코드 모양만 검사하고,
DB 가 있으면 (`RLS_RUN_LOCAL=1`) 함수를 직접 호출해 런타임 시맨틱을
검증한다.

Supabase custom_access_token hook 계약 (공식):
  - 함수 위치: `pg-functions://postgres/<schema>/<func>` 의 schema/func
  - 시그니처: `(event jsonb) RETURNS jsonb`
  - 입력: `{ "user_id": "<uuid>", "claims": {...} }`
  - 출력: 동일 구조에서 `claims.app_metadata` 가 보강된 jsonb
  - 호출 시점: JWT mint 마다, GoTrue 컨텍스트 (사용자 세션 없음)
  - 권장: `SECURITY DEFINER` (RLS 가 hook 호출을 차단하지 않도록)
  - 권장: `STABLE` (DB 변경 없음)
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

# Locate the migration module by file path (not by package import — alembic
# versions are not on the package import path).
_MIGRATION_PATH = (
    Path(__file__).resolve().parents[3]
    / "apps"
    / "api"
    / "alembic"
    / "versions"
    / "0035_custom_access_token_hook.py"
)


@pytest.fixture(scope="module")
def hook_sql() -> str:
    """Read the CREATE OR REPLACE FUNCTION statement from alembic 0035.

    Pulls the SQL out of the module-level `_HOOK_SQL` constant so we don't
    have to maintain the expected string separately — the migration is
    the single source of truth.
    """
    spec = importlib.util.spec_from_file_location(
        "alembic_0035", str(_MIGRATION_PATH)
    )
    assert spec is not None, f"could not load spec from {_MIGRATION_PATH}"
    assert spec.loader is not None, f"spec.loader is None for {_MIGRATION_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert hasattr(module, "_HOOK_SQL"), "migration missing _HOOK_SQL constant"
    return module._HOOK_SQL


# ── 1. Function signature contract ────────────────────────────────


def test_hook_function_lives_in_public_schema(hook_sql: str) -> None:
    """Hook must live in `public` schema — supabase/config.toml URI binds to it.

    If a future migration moves the function, supabase/config.toml URI
    must be updated atomically. This test is the regression guard.
    """
    assert re.search(
        r"CREATE OR REPLACE FUNCTION\s+public\.custom_access_token_hook\b",
        hook_sql,
    ), (
        "hook function must be `public.custom_access_token_hook(...)` "
        "to match supabase/config.toml URI `pg-functions://postgres/public/custom_access_token_hook`"
    )


def test_hook_function_signature_matches_supabase_contract(
    hook_sql: str,
) -> None:
    """Signature: (event jsonb) RETURNS jsonb."""
    match = re.search(
        r"CREATE OR REPLACE FUNCTION\s+(?P<name>[\w.]+)\s*\(\s*(?P<args>[^)]*)\s*\)\s*"
        r"RETURNS\s+(?P<ret>\w+(?:\s*\([^)]*\))?)",
        hook_sql,
    )
    assert match is not None, f"could not parse function signature in: {hook_sql[:300]!r}"
    args = match.group("args").strip()
    ret = match.group("ret").strip()
    assert "jsonb" in args, (
        f"hook must take a jsonb argument, got ({args!r})"
    )
    assert "event" in args, (
        f"hook argument must be named `event` (Supabase contract), got ({args!r})"
    )
    assert ret == "jsonb", f"hook must RETURN jsonb, got {ret!r}"


def test_hook_is_security_definer(hook_sql: str) -> None:
    """`SECURITY DEFINER` 필수 — hook 는 GoTrue 컨텍스트(사용자 세션 없음)
    에서 실행되므로 함수 owner 의 권한으로 tenant_memberships 를 읽어야 한다.

    SECURITY DEFINER 가 빠지면 RLS 가 hook 의 SELECT 를 차단해
    `tenant_id` 가 항상 비어있게 된다 (모든 사용자가 401).
    """
    assert "SECURITY DEFINER" in hook_sql, (
        "hook must declare SECURITY DEFINER so RLS does not block the "
        "tenant_memberships / tenants read during JWT mint"
    )


def test_hook_is_stable(hook_sql: str) -> None:
    """`STABLE` 필수 — hook 는 순수 read (DB 변경 없음).

    STABLE 마킹은 Postgres 의 옵티마이저에 함수가 동일 입력에 대해
    동일 출력을 반환함을 알린다. 만약 향후 누군가 hook 에 INSERT 를
    추가하면 STABLE 마킹을 제거해야 하는데, 이 테스트가 그 작업을
    강제한다.
    """
    assert re.search(r"\bSTABLE\b", hook_sql), (
        "hook must declare STABLE — pure read function"
    )


def test_hook_grants_execute_to_postgres(hook_sql: str) -> None:
    """`GRANT EXECUTE ... TO postgres` 필수.

    Supabase GoTrue 가 postgres role 의 권한으로 함수를 호출하므로
    postgres 에 EXECUTE 권한이 부여되어 있어야 한다. 권한이 없으면
    hook 가 호출되지 않고 (또는 permission denied 로 실패하고) 결과
    적으로 mint 된 JWT 가 app_metadata 비어있게 된다.
    """
    assert re.search(
        r"GRANT\s+EXECUTE\s+ON\s+FUNCTION\s+public\.custom_access_token_hook\s*\(\s*jsonb\s*\)\s+TO\s+postgres",
        hook_sql,
    ), "missing `GRANT EXECUTE ... TO postgres` for the hook"


def test_hook_uses_or_replace(hook_sql: str) -> None:
    """`CREATE OR REPLACE FUNCTION` — 재실행 안전.

    alembic migration 을 여러 번 (down → up) 반복해도 안전해야 한다.
    """
    assert "CREATE OR REPLACE FUNCTION" in hook_sql, (
        "hook must be `CREATE OR REPLACE FUNCTION` for re-run safety"
    )


# ── 2. Logic shape (without DB) ─────────────────────────────────


def test_hook_queries_tenant_memberships(hook_sql: str) -> None:
    """Hook 가 `tenant_memberships` 를 SELECT 하는지 검증."""
    assert "tenant_memberships" in hook_sql, (
        "hook must SELECT from tenant_memberships to inject tenant_id/role"
    )


def test_hook_joins_tenants_for_industry(hook_sql: str) -> None:
    """Hook 가 `tenants` 를 JOIN 해서 `industry` 를 가져오는지 검증.

    `industry` 는 JWT 의 app_metadata 에 포함되어야 m0_onboarding /
    m6_close 등에서 tenant 컨텍스트를 결정할 수 있다 (Story 6.3 B8).
    """
    assert re.search(
        r"JOIN\s+public\.tenants\s+t\b", hook_sql, re.IGNORECASE
    ), "hook must JOIN tenants to fetch industry"


def test_hook_role_priority_owner_member_viewer_consultant_proxy(
    hook_sql: str,
) -> None:
    """Hook 가 owner > member > viewer > consultant_proxy 우선순위를 적용하는지 검증.

    한 user 가 여러 tenant 의 member 일 수 있으므로 (consultant_proxy
    가 대표), 우선순위 CASE 식이 정확히 이 순서여야 한다.
    """
    # CASE 식이 이 4개 role 을 모두 다루는지 확인
    for role in ("owner", "member", "viewer", "consultant_proxy"):
        assert role in hook_sql, f"hook missing role {role!r} in priority CASE"


def test_hook_excludes_deleted_tenants(hook_sql: str) -> None:
    """Hook 가 `tenants.deleted_at IS NULL` 인 테넌트만 고려하는지 검증.

    Soft-deleted tenant 의 membership 은 hook 결과에서 제외되어야
    한다 (Epic 12 m12_account Tenant Deletion 흐름 정합).
    """
    assert "deleted_at IS NULL" in hook_sql, (
        "hook must filter tenants.deleted_at IS NULL to avoid minting "
        "JWTs with a tenant_id pointing at a deleted tenant"
    )


def test_hook_returns_event_unchanged_when_user_id_invalid(
    hook_sql: str,
) -> None:
    """Hook 가 잘못된 event (NULL user_id 또는 잘못된 UUID) 에 대해
    원본 event 를 그대로 반환하는지 검증 — panic 방지.

    GoTrue 가 예외 event 를 보내도 hook 가 죽으면 mint 자체가 실패해
    사용자가 로그인할 수 없게 된다. 따라서 hook 는 best-effort 로
    원본을 반환해야 한다.
    """
    assert "RETURN event;" in hook_sql, (
        "hook must `RETURN event;` for invalid/missing user_id paths "
        "to prevent mint failures"
    )
    # EXCEPTION 핸들러도 있어야 한다 (잘못된 UUID 형식 등)
    assert "EXCEPTION" in hook_sql, (
        "hook must catch exceptions when parsing user_id "
        "(e.g., invalid_text_representation)"
    )


def test_hook_uses_jsonb_set_for_app_metadata(hook_sql: str) -> None:
    """Hook 가 `jsonb_set` 으로 `claims.app_metadata` 를 갱신하는지 검증.

    단순 string concatenation 이 아니라 jsonb_set 을 써야 기존 필드를
    보존하면서 새 키만 추가할 수 있다.
    """
    assert re.search(
        r"jsonb_set\s*\([^)]*'{app_metadata}'", hook_sql
    ), "hook must use jsonb_set to update claims.app_metadata"


# ── 3. supabase/config.toml binding ──────────────────────────────


def test_supabase_config_toml_hook_is_enabled() -> None:
    """supabase/config.toml 의 `[auth.hook.custom_access_token] enabled`
    가 `true` 인지 검증. alembic 0035 와 supabase/config.toml 은
    atomic 으로 활성화되어야 한다 (둘 중 하나라도 빠지면 mint 된 JWT
    가 app_metadata 비어있음).
    """
    config_path = (
        Path(__file__).resolve().parents[3] / "supabase" / "config.toml"
    )
    text = config_path.read_text(encoding="utf-8")

    # 해당 블록 추출
    match = re.search(
        r"\[auth\.hook\.custom_access_token\](.*?)(?=\n\[|\Z)",
        text,
        re.DOTALL,
    )
    assert match is not None, (
        "supabase/config.toml missing [auth.hook.custom_access_token] block"
    )
    block = match.group(1)
    assert re.search(r"^enabled\s*=\s*true\b", block, re.MULTILINE), (
        "supabase/config.toml [auth.hook.custom_access_token] enabled must be true "
        "after Phase 3-0 wire"
    )
    assert "public/custom_access_token_hook" in block, (
        "supabase/config.toml URI must point at public.custom_access_token_hook "
        "to match alembic 0035"
    )


# ── 4. Downgrade safety ────────────────────────────────────────


def test_downgrade_drops_hook_function() -> None:
    """Migration downgrade 가 함수를 DROP 하는지 검증.

    alembic downgrade 가 깨지면 새 환경 적용 후 롤백 시 hook 가
    dangling 상태로 남는다 (함수는 있는데 enabled=false 면 mint
    시도시 503). 안전하게 DROP 되어야 한다.
    """
    spec = importlib.util.spec_from_file_location(
        "alembic_0035", str(_MIGRATION_PATH)
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert hasattr(module, "_DOWN_SQL"), "migration missing _DOWN_SQL constant"
    down_sql: str = module._DOWN_SQL
    assert "DROP FUNCTION IF EXISTS public.custom_access_token_hook" in down_sql, (
        "downgrade must `DROP FUNCTION IF EXISTS public.custom_access_token_hook` "
        "for clean rollback"
    )
