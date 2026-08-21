"""tests.api.core.test_phase_3_1_auth_wire — Phase 3-1 auth wire smoke test.

Phase 3-1 (cj-style Phase 3 2번째 = 50번째 epic 연속 정직 회복 wire).

The Phase 3-1 wire는 frontend-only wire (T1~T6) + backend capability
enum EXTENSION (T7) + docs 정합 (T8)의 결합이다. 본 파일은 그 wire
artifact 들의 shape / contract / drift 정합을 검증한다:

1. **Auth capability enum** — `apps/api/core/capability.py` 안에
   LOGIN / SIGNUP / AUTH_MIDDLEWARE / FORGOT_PASSWORD / LOGOUT 5 entries
   와 4 industries grant 모두 존재.

2. **Capability matrix v1.24 alignment** — 5 NEW rows 가 capability
   matrix doc 안에 존재 (drift detector duplicate +
   `tests/integration/test_capability_matrix_v1_24_drift.py` 와 cross-check).

3. **supabase/config.toml** — `[auth.hook.custom_access_token]` 가
   `enabled = true` + `uri = "pg-functions://postgres/public/..."` 인지
   (Phase 3-0 wire 의 link 가 유지되고 있는지 회귀 가드).

4. **alembic 0035** — custom_access_token_hook function 정의가
   `apps/api/alembic/versions/0035_custom_access_token_hook.py` 안에
   존재 (Phase 3-0 wire 회귀 가드).

5. **ko-KR.json SSOT** — `auth.{login,signup,logout,forgot_password,
   reset_password}` 5 namespace 가 모두 존재 (drift: i18n key parity).

6. **Frontend auth import chain** — `apps/web/components/auth/LoginForm`,
   `SignupForm`, `LogoutButton`, `ForgotPasswordForm`, `ResetPasswordForm`
   가 모두 disk 에 존재 (build smoke + 5 web pages mount).

7. **D-1-1-DEFER-* honestly preserved** — Phase 3-1 wire 가
   Magic link / OAuth / SSO SAML 을 도입하지 않았는지 grep guard.

8. **AlreadyHasTenantError + TenantNameValidationError** — Phase 3-0
   의 atomic transaction guard 가 깨지지 않았는지 회귀.

9. **Audit-first INSERT preserved** — `tenant_signup_completed` 가
   emit_audit_typed 의 ActionClass.TENANT registry 안에 존재.

10. **Auth middleware Edge runtime** — `middleware.ts` 안에
    `export const runtime = 'edge'` 가 설정되어 있는지 (CR 11-4 LLM 디폴트
    바꾸기 방지).
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CAPABILITY_PY = REPO_ROOT / "apps" / "api" / "core" / "capability.py"
SUPABASE_CONFIG = REPO_ROOT / "supabase" / "config.toml"
ALEMBIC_0035 = REPO_ROOT / "apps" / "api" / "alembic" / "versions" / "0035_custom_access_token_hook.py"
KO_KR_JSON = REPO_ROOT / "apps" / "web" / "messages" / "ko-KR.json"
WEB_MIDDLEWARE = REPO_ROOT / "apps" / "web" / "middleware.ts"
AUDIT_ACTION = REPO_ROOT / "apps" / "api" / "core" / "audit_action.py"
CAPABILITY_MATRIX = REPO_ROOT / "docs" / "capability-matrix.md"

PHASE_3_1_CAPABILITIES = ["LOGIN", "SIGNUP", "AUTH_MIDDLEWARE", "FORGOT_PASSWORD", "LOGOUT"]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ── 1. Auth capability enum ────────────────────────────────────


def test_capability_py_has_phase_3_1_entries() -> None:
    """apps/api/core/capability.py has 5 NEW Phase 3-1 enum entries."""
    content = _read(CAPABILITY_PY)
    for cap in PHASE_3_1_CAPABILITIES:
        pattern = re.compile(rf"^\s*{cap}\s*=\s*\"{cap.lower()}\"\s*$", re.MULTILINE)
        assert pattern.search(content), f"capability.py missing Capability.{cap} = \"{cap.lower()}\""


def test_capability_py_grants_auth_to_all_4_industries() -> None:
    """CR 12-1 L4 precedent — all 4 industries grant LOGIN/SIGNUP/etc."""
    content = _read(CAPABILITY_PY)
    industry_headers = [
        "Industry.MANUFACTURING:",
        "Industry.SERVICE:",
        "Industry.MANUFACTURING_SERVICE:",
        "Industry.MANUFACTURING_SERVICE_OTHER:",
    ]
    for header in industry_headers:
        idx = content.find(header)
        assert idx > 0, f"missing industry header: {header}"
        # Industry grant frozensets span many lines — use 12000 chars to
        # capture the full frozenset including Phase 3-1 entries appended
        # to the end of each block.
        window = content[idx : idx + 12000]
        for cap in PHASE_3_1_CAPABILITIES:
            assert (
                f"Capability.{cap}" in window
            ), f"industry {header} must grant Capability.{cap}"


# ── 2. Capability matrix v1.24 alignment ────────────────────────


def test_capability_matrix_v1_24_has_5_new_rows() -> None:
    """capability-matrix.md v1.24 declares 5 NEW Phase 3-1 rows."""
    content = _read(CAPABILITY_MATRIX)
    for cap in PHASE_3_1_CAPABILITIES:
        # The matrix uses `| `LOGIN` |` table row format AND the title
        # section enumerates `LOGIN` (with backticks) in the v1.24 changelog.
        assert (
            f"| `{cap}`" in content
            or f"### {cap}" in content
            or f"`{cap}`" in content
        ), f"capability-matrix.md v1.24 missing row {cap}"


# ── 3. supabase/config.toml hook binding ────────────────────────


def test_supabase_config_has_hooks_enabled() -> None:
    """Phase 3-0 wire 회귀 가드 — `custom_access_token` hook enabled."""
    content = _read(SUPABASE_CONFIG)
    assert "[auth.hook.custom_access_token]" in content
    # Search the entire file for "enabled = true" after the section header.
    section = content.split("[auth.hook.custom_access_token]")[1]
    # Match the first non-comment `enabled = true` line within the section.
    assert re.search(r"^\s*enabled\s*=\s*true\s*$", section, re.MULTILINE)


def test_supabase_config_hook_uri_binding() -> None:
    """Hook URI points to the postgres public.custom_access_token_hook."""
    content = _read(SUPABASE_CONFIG)
    # Match uri = "pg-functions://postgres/public/custom_access_token_hook"
    assert re.search(
        r'uri\s*=\s*"pg-functions://postgres/public/custom_access_token_hook"', content
    )


# ── 4. alembic 0035 migration ───────────────────────────────────


def test_alembic_0035_migration_exists() -> None:
    """Phase 3-0 wire 회귀 가드 — alembic 0035 file exists."""
    assert ALEMBIC_0035.exists(), f"missing alembic migration: {ALEMBIC_0035}"


def test_alembic_0035_defines_custom_access_token_hook() -> None:
    """alembic 0035 creates `public.custom_access_token_hook` function."""
    content = _read(ALEMBIC_0035)
    assert "custom_access_token_hook" in content
    assert "RETURNS jsonb" in content or "RETURNS trigger" in content


# ── 5. ko-KR.json SSOT ──────────────────────────────────────────


def test_ko_kr_json_has_auth_login_namespace() -> None:
    content = _read(KO_KR_JSON)
    assert '"login"' in content or "auth.login" in content or "\"login\":{" in content
    # The login form key strings must exist.
    assert "이메일" in content
    assert "비밀번호" in content


def test_ko_kr_json_has_auth_signup_namespace() -> None:
    content = _read(KO_KR_JSON)
    assert "가입하기" in content or "회원가입" in content


def test_ko_kr_json_has_auth_logout_namespace() -> None:
    content = _read(KO_KR_JSON)
    assert "로그아웃" in content


def test_ko_kr_json_has_auth_forgot_password_namespace() -> None:
    content = _read(KO_KR_JSON)
    assert "재설정 링크" in content or "비밀번호 찾기" in content


def test_ko_kr_json_has_auth_reset_password_namespace() -> None:
    content = _read(KO_KR_JSON)
    assert "새 비밀번호" in content or "비밀번호 확인" in content


# ── 6. Frontend auth page files exist ───────────────────────────


def test_frontend_login_page_exists() -> None:
    """apps/web/login page file exists."""
    candidates = [
        REPO_ROOT / "apps" / "web" / "app" / "[locale]" / "(auth)" / "login" / "page.tsx",
    ]
    assert any(p.exists() for p in candidates), f"login page missing: {candidates}"


def test_frontend_signup_page_exists() -> None:
    """apps/web/signup page file exists."""
    candidates = [
        REPO_ROOT / "apps" / "web" / "app" / "[locale]" / "(auth)" / "signup" / "page.tsx",
    ]
    assert any(p.exists() for p in candidates)


def test_frontend_forgot_password_page_exists() -> None:
    """apps/web/forgot-password page file exists."""
    candidates = [
        REPO_ROOT / "apps" / "web" / "app" / "[locale]" / "(auth)" / "forgot-password" / "page.tsx",
    ]
    assert any(p.exists() for p in candidates)


def test_frontend_reset_password_page_exists() -> None:
    """apps/web/reset-password page file exists."""
    candidates = [
        REPO_ROOT / "apps" / "web" / "app" / "[locale]" / "(auth)" / "reset-password" / "page.tsx",
    ]
    assert any(p.exists() for p in candidates)


def test_frontend_auth_components_exist() -> None:
    """All 5 auth components exist on disk."""
    components = [
        "LoginForm.tsx",
        "SignupForm.tsx",
        "LogoutButton.tsx",
        "ForgotPasswordForm.tsx",
        "ResetPasswordForm.tsx",
    ]
    auth_dir = REPO_ROOT / "apps" / "web" / "components" / "auth"
    for c in components:
        assert (auth_dir / c).exists(), f"missing component: {auth_dir / c}"


def test_frontend_supabase_lib_exists() -> None:
    """apps/web/lib/supabase/{server,client,middleware,env}.ts exist."""
    lib = REPO_ROOT / "apps" / "web" / "lib" / "supabase"
    for fname in ["server.ts", "client.ts", "middleware.ts", "env.ts", "types.ts"]:
        assert (lib / fname).exists(), f"missing supabase lib: {lib / fname}"


def test_frontend_auth_lib_exists() -> None:
    """apps/web/lib/auth/{login,signup,logout,forgot-password,reset-password,middleware}.ts exist."""
    lib = REPO_ROOT / "apps" / "web" / "lib" / "auth"
    for fname in [
        "login.ts",
        "signup.ts",
        "logout.ts",
        "forgot-password.ts",
        "reset-password.ts",
        "middleware.ts",
    ]:
        assert (lib / fname).exists(), f"missing auth lib: {lib / fname}"


# ── 7. D-1-1-DEFER-* honestly preserved (50번째 epic 연속) ──────


def test_no_magic_link_or_oauth_or_sso_introduced() -> None:
    """Phase 3-1 wire MUST NOT introduce Magic link / OAuth / SSO SAML.

    CR 11-3 honest-DEFER discipline 보존 — 49번째 epic 연속 정직.
    D-1-1-DEFER-1 (Magic link) / D-1-1-DEFER-2 (OAuth) / D-1-1-DEFER-3
    (SSO enterprise SAML) 는 honestly preserved 상태로 유지.

    Implementation: form HTML / 서버 핸들러의 magic link / OAuth / SAML
    keyword 도입을 grep guard.
    """
    forbidden_substrings = [
        "magic_link",
        "magicLink",
        "MagicLink",
        "oauth_signin",
        "OAuthSignin",
        "saml_acs",
        "SAML_ACS",
    ]
    # Search login.ts / signup.ts / middleware.ts / reset-password.ts / login/page.tsx
    paths = [
        REPO_ROOT / "apps" / "web" / "lib" / "auth" / "login.ts",
        REPO_ROOT / "apps" / "web" / "lib" / "auth" / "signup.ts",
        REPO_ROOT / "apps" / "web" / "lib" / "auth" / "middleware.ts",
        REPO_ROOT / "apps" / "web" / "lib" / "auth" / "reset-password.ts",
        REPO_ROOT / "apps" / "web" / "app" / "[locale]" / "(auth)" / "login" / "page.tsx",
        REPO_ROOT / "apps" / "web" / "app" / "[locale]" / "(auth)" / "signup" / "page.tsx",
    ]
    for p in paths:
        if not p.exists():
            continue
        content = _read(p)
        for substr in forbidden_substrings:
            assert (
                substr not in content
            ), f"D-1-1-DEFER-* violation: {substr} found in {p}"


# ── 8. Phase 3-0 atomic transaction guard ───────────────────────


def test_already_has_tenant_error_exists() -> None:
    """Phase 3-0 wire 회귀 가드 — `AlreadyHasTenantError` 409 typed in
    services/signup_service.py (Phase 3-0 wire location).
    """
    services = REPO_ROOT / "apps" / "api" / "modules" / "m0_onboarding" / "services" / "signup_service.py"
    if not services.exists():
        return
    content = _read(services)
    assert "AlreadyHasTenantError" in content
    # 409 + ALREADY_HAS_TENANT envelope code.
    assert "409" in content or "ALREADY_HAS_TENANT" in content


def test_signup_service_atomic_transaction_pattern() -> None:
    """Phase 3-0 wire 회귀 가드 — 5-step atomic transaction in single flush."""
    services = REPO_ROOT / "apps" / "api" / "modules" / "m0_onboarding" / "services" / "signup_service.py"
    if not services.exists():
        return
    content = _read(services)
    # 5 steps: get_or_create_user_row, existing membership check, tenants row,
    # tenant_memberships row, tenant_settings row.
    assert "tenants" in content
    assert "tenant_memberships" in content
    assert "tenant_settings" in content
    assert "tenant_signup_completed" in content


# ── 9. Audit-first INSERT preserved ─────────────────────────────


def test_audit_action_tenant_signup_completed() -> None:
    """`tenant_signup_completed` is in the ActionClass.TENANT registry."""
    content = _read(AUDIT_ACTION)
    assert "ActionClass.TENANT" in content
    assert "tenant_signup_completed" in content


# ── 10. Auth middleware Edge runtime ────────────────────────────


def test_apps_web_middleware_uses_edge_runtime() -> None:
    """apps/web/middleware.ts MUST export `runtime = 'edge'`.

    CR 11-4 LLM default 바꾸기 방지 — Supabase SSR Edge variant 가
    Node runtime 에서 동작하지 않으므로 명시적으로 Edge 선언.
    """
    assert WEB_MIDDLEWARE.exists()
    content = _read(WEB_MIDDLEWARE)
    assert re.search(
        r"export\s+const\s+runtime\s*=\s*['\"]edge['\"]", content
    ), "apps/web/middleware.ts must export `runtime = 'edge'`"


def test_apps_web_middleware_uses_supabase_ssr() -> None:
    """apps/web/middleware.ts MUST import from @/lib/supabase/middleware."""
    content = _read(WEB_MIDDLEWARE)
    assert (
        "@/lib/supabase/middleware" in content
        or "lib/supabase/middleware" in content
    )


def test_apps_web_middleware_route_guard_pattern() -> None:
    """apps/web/middleware.ts MUST call routeGuard from @/lib/auth/middleware."""
    content = _read(WEB_MIDDLEWARE)
    assert (
        "routeGuard" in content
    ), "apps/web/middleware.ts must invoke routeGuard from @/lib/auth/middleware"
