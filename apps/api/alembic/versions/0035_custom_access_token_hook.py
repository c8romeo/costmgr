"""Story Phase 3-0 — custom_access_token_hook PL/pgSQL function.

Phase 3-0 (cj-style Epic 14 carry-over 2번째, "fix" 종류) — auth 계약
수직 슬라이스 진입 결정 wire. GoTrue 의 `custom_access_token` hook 가
JWT 를 mint 할 때마다 호출되어, `auth.users` 의 사용자에 대해
`tenant_memberships` 를 조회해 `app_metadata` 에 `tenant_id` / `role` /
`industry` 를 주입한다.

근본 원인 (조사 결과 요약):
- hook 가 disable 상태 + 함수가 부재 → mint 된 JWT 가 `app_metadata`
  비어있음 → `apps.api.core.security.decode_jwt` 의 `app_metadata.get(
  "tenant_id")` 가 None → 모든 API 가 401.
- `supabase/config.toml` 의 `[auth.hook.custom_access_token]` 블록이
  `enabled = false` 이며, 참조된 `public.custom_access_token_hook` 함수가
  저장소에 존재하지 않았다 (grep 0 hit).

해결 (이 마이그레이션):
- `public.custom_access_token_hook(event jsonb) RETURNS jsonb` PL/pgSQL 함수
  생성. Supabase GoTrue 가 정의한 시그니처 (event = `{user_id, claims}`).
- 가장 권한이 높은 `tenant_membership` 1행을 골라 `tenant_id` + `role` +
  `tenants.industry` 를 `app_metadata` 에 주입.
- `SECURITY DEFINER` 로 호출되어 RLS 우회 (hook 는 JWT mint 시점에
  GoTrue 컨텍스트에서 실행되므로 사용자 RLS 컨텍스트가 없음).
- `STABLE` (DB 변경 없음, 순수 read).
- `OR REPLACE` (재실행 안전).

알려진 한계 (다음 sprint 에서 처리):
- 사용자가 어떤 `tenant_membership` 에도 속하지 않으면 `app_metadata`
  가 그대로 비어있음 → 사용자가 받은 JWT 로는 모든 API 가 401. 이는
  signup 시 `tenants` + `tenant_memberships` 가 atomic 으로 만들어지지
  않기 때문이며, Phase 3-0 의 다음 단계 (signup → 로컬 테넌트 생성
  경로 wire) 에서 해소한다.

wire scope = T1 (alembic 0035 = public.custom_access_token_hook 신규) +
T2 (supabase/config.toml hook enabled = true).
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0035_custom_access_token_hook"
down_revision: str | None = "0034_listen_notify_consume_cross_tenant_fanout"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Hook SQL — Supabase GoTrue 가 매 JWT mint 마다 호출한다.
#
# 입력 event 형태 (Supabase 공식): jsonb 한 객체. user_id 는 string,
# claims 는 인증 메타데이터 객체 (sub, aud, role, email, app_metadata,
# user_metadata 등). 우리는 claims.app_metadata 를 보강해 반환한다.
#
# 출력: 동일 event 구조에서 `claims.app_metadata` 에 tenant_id / role /
# industry 가 추가된 jsonb.
#
# 권한 결정: 한 user 가 여러 tenant 에 속할 수 있으므로 (consultant_proxy
# 가 대표), `tenant_memberships.role` 의 우선순위 (owner > member > viewer
# > consultant_proxy) + `joined_at ASC` 로 첫 membership 을 고른다.
_HOOK_SQL = r"""
CREATE OR REPLACE FUNCTION public.custom_access_token_hook(event jsonb)
RETURNS jsonb
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    v_user_id         uuid;
    v_claims          jsonb;
    v_app_metadata    jsonb;
    v_tenant_id       uuid;
    v_role            text;
    v_industry        text;
    v_has_membership  boolean;
BEGIN
    -- 1. event 에서 user_id 와 claims 추출. event 가 NULL 이거나
    --    user_id 가 없으면 그대로 반환 (호출자가 비정상 event 를 받았을
    --    때 hook 이 panic 하지 않도록 한다).
    IF event IS NULL OR event->>'user_id' IS NULL THEN
        RETURN event;
    END IF;

    BEGIN
        v_user_id := (event->>'user_id')::uuid;
    EXCEPTION WHEN invalid_text_representation THEN
        RETURN event;
    END;

    v_claims := event->'claims';
    IF v_claims IS NULL THEN
        v_claims := '{}'::jsonb;
    END IF;

    v_app_metadata := coalesce(v_claims->'app_metadata', '{}'::jsonb);

    -- 2. 해당 user 의 "가장 권한이 높은" tenant_membership 1 행을 고른다.
    --    한 user 가 여러 tenant 의 member 일 수 있다 (consultant_proxy
    --    가 여러 tenant 를 컨설팅하는 케이스). 우선순위:
    --      owner (3) > member (2) > viewer (1) > consultant_proxy (0)
    --    동률이면 joined_at 이 가장 빠른 행 (가장 오래된 membership 우선).
    --
    --    SECURITY DEFINER 로 실행되므로 함수 owner (보통 postgres) 의
    --    권한으로 모든 tenant_memberships / tenants 행을 읽는다.
    --    RLS 가 hook 호출을 차단하지 않기 위해 필수.
    SELECT
        m.tenant_id,
        m.role,
        t.industry
    INTO
        v_tenant_id,
        v_role,
        v_industry
    FROM public.tenant_memberships m
    JOIN public.tenants t ON t.id = m.tenant_id
    WHERE m.user_id = v_user_id
      AND t.deleted_at IS NULL
    ORDER BY
        CASE m.role
            WHEN 'owner'            THEN 3
            WHEN 'member'           THEN 2
            WHEN 'viewer'           THEN 1
            WHEN 'consultant_proxy' THEN 0
            ELSE -1
        END DESC,
        m.joined_at ASC
    LIMIT 1;

    GET DIAGNOSTICS v_has_membership = ROW_COUNT;

    -- 3. membership 이 있을 때만 app_metadata 에 주입. 기존에 다른 키가
    --    이미 들어있었다면 보존한다 (예: marketing_consent 등 다른 필드).
    IF v_has_membership THEN
        v_app_metadata := v_app_metadata
            || jsonb_build_object(
                'tenant_id', v_tenant_id,
                'role',      v_role,
                'industry',  v_industry
            );
    END IF;

    -- 4. claims 와 event 를 갱신해 반환.
    v_claims := jsonb_set(v_claims, '{app_metadata}', v_app_metadata, true);
    RETURN jsonb_set(event, '{claims}', v_claims, true);
END;
$$;
"""

# 함수 owner 와 실행 권한 명시. Supabase 의 GoTrue auth hook 은
# `postgres` role 의 권한으로 함수를 호출하므로 EXECUTE 권한이
# postgres 에 부여되어 있어야 한다. anon / authenticated / service_role
# 에도 부여해 두면 직접 psql 로 테스트할 때 편하다.
#
# D-CI-FUNC-9 cj-226 fix: each statement below is its own op.execute()
# call because asyncpg's prepared-statement protocol rejects a single
# cursor.execute() string containing multiple ;-separated commands  # noqa: ERA001
# ("cannot insert multiple commands into a prepared statement"). The  # noqa: ERA001
# function body itself is one statement, but ALTER / REVOKE / GRANT are  # noqa: ERA001
# separate ones — we must split them. (Other migrations such as 0019  # noqa: ERA001
# and 0021 already follow this pattern.)  # noqa: ERA001
_OWNER_SQL = r"""
ALTER FUNCTION public.custom_access_token_hook(jsonb) OWNER TO postgres;
"""

_REVOKE_SQL = r"""
REVOKE ALL ON FUNCTION public.custom_access_token_hook(jsonb) FROM PUBLIC;
"""

_GRANT_SQL = r"""
GRANT EXECUTE ON FUNCTION public.custom_access_token_hook(jsonb) TO postgres;
"""


_DOWN_SQL = r"""
DROP FUNCTION IF EXISTS public.custom_access_token_hook(jsonb);
"""


def upgrade() -> None:
    # Each op.execute() must carry a SINGLE SQL statement. The function
    # DDL (_HOOK_SQL) is one CREATE FUNCTION statement; the owner /
    # revoke / grant statements are each separate.
    op.execute(_HOOK_SQL)
    op.execute(_OWNER_SQL)
    op.execute(_REVOKE_SQL)
    op.execute(_GRANT_SQL)


def downgrade() -> None:
    op.execute(_DOWN_SQL)
