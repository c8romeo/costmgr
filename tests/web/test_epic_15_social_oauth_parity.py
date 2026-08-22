"""tests.web.test_epic_15_social_oauth_parity — Social OAuth wrapper parity.

Epic 15 (cj-style 60번째 epic 연속 정직 회복 wire) — AC #7.2.
Tests the social.ts wrapper's whitelist enforcement and rate limiter.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = REPO_ROOT / "apps" / "web"
SOCIAL_TS = WEB_ROOT / "lib" / "auth" / "social.ts"
KO_KR_JSON = WEB_ROOT / "messages" / "ko-KR.json"


@pytest.fixture(scope="module")
def social_content() -> str:
    assert SOCIAL_TS.exists(), "social.ts missing"
    return SOCIAL_TS.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def ko_kr_content() -> str:
    return json.loads(KO_KR_JSON.read_text(encoding="utf-8"))


class TestSocialOAuthWrapper:
    def test_file_exists(self, social_content: str) -> None:
        assert len(social_content) > 100

    def test_uses_signinwithoauth(self, social_content: str) -> None:
        assert "signInWithOAuth" in social_content

    def test_provider_whitelist_strict(self, social_content: str) -> None:
        # AD-7 strict invariant: ALLOWED_SOCIAL_PROVIDERS frozenset
        # MUST contain only google, naver, kakao.
        assert "ALLOWED_SOCIAL_PROVIDERS" in social_content
        assert '"google"' in social_content
        assert '"naver"' in social_content
        assert '"kakao"' in social_content
        # 'facebook' / 'twitter' / 'github' MUST NOT be allowed.
        assert "facebook" not in social_content
        assert "twitter" not in social_content
        assert "github" not in social_content

    def test_provider_disabled_error(self, social_content: str) -> None:
        # Non-whitelisted provider MUST throw PROVIDER_DISABLED.
        assert "PROVIDER_DISABLED" in social_content

    def test_3_failure_cooldown_60s(self, social_content: str) -> None:
        assert "COOL_DOWN_THRESHOLD = 3" in social_content
        assert "COOL_DOWN_DURATION_MS = 60_000" in social_content

    def test_audit_endpoint_called(self, social_content: str) -> None:
        # audit-first INSERT social_oauth_initiated.
        assert "social-oauth-initiated" in social_content
        assert "recordSocialOAuthAudit" in social_content


class TestSocialAuthButtons:
    def test_component_exists(self) -> None:
        comp = WEB_ROOT / "components" / "auth" / "SocialAuthButtons.tsx"
        assert comp.exists()

    def test_component_uses_wrapper(self) -> None:
        comp = WEB_ROOT / "components" / "auth" / "SocialAuthButtons.tsx"
        content = comp.read_text(encoding="utf-8")
        assert "signInWithSocialOAuth" in content

    def test_3_provider_buttons(self) -> None:
        comp = WEB_ROOT / "components" / "auth" / "SocialAuthButtons.tsx"
        content = comp.read_text(encoding="utf-8")
        # Each provider has a button with the right label.
        assert "google" in content.lower()
        assert "naver" in content.lower()
        assert "kakao" in content.lower()
        assert "구글로 계속하기" in content
        assert "네이버로 계속하기" in content
        assert "카카오로 계속하기" in content


class TestKoKRNamespace:
    def test_social_keys(self, ko_kr_content: dict) -> None:
        social = ko_kr_content.get("auth", {}).get("social", {})
        assert "divider_or" in social
        assert "google_button" in social
        assert "naver_button" in social
        assert "kakao_button" in social
        assert "error" in social
        assert "rate_limited" in social["error"]
        assert "provider_disabled" in social["error"]
        assert "network" in social["error"]


class TestLoginPageExtension:
    def test_login_page_uses_social_buttons(self) -> None:
        page = (
            REPO_ROOT
            / "apps"
            / "web"
            / "app"
            / "[locale]"
            / "(auth)"
            / "login"
            / "page.tsx"
        )
        content = page.read_text(encoding="utf-8")
        # D-001 actual mount: <SocialAuthButtons /> JSX.
        assert "<SocialAuthButtons" in content

    def test_login_page_magic_link_entry(self) -> None:
        page = (
            REPO_ROOT
            / "apps"
            / "web"
            / "app"
            / "[locale]"
            / "(auth)"
            / "login"
            / "page.tsx"
        )
        content = page.read_text(encoding="utf-8")
        assert "/magic-link" in content
        assert "매직 링크로 로그인" in content

    def test_login_page_sso_entry(self) -> None:
        page = (
            REPO_ROOT
            / "apps"
            / "web"
            / "app"
            / "[locale]"
            / "(auth)"
            / "login"
            / "page.tsx"
        )
        content = page.read_text(encoding="utf-8")
        assert "엔터프라이즈 SSO" in content
        assert "/sso/" in content
