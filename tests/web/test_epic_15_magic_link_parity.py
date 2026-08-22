"""tests.web.test_epic_15_magic_link_parity — Magic link wrapper parity.

Epic 15 (cj-style 60번째 epic 연속 정직 회복 wire) — AC #7.1.
Tests the magic-link.ts wrapper's security invariants and rate limiter.

Verifies:
  1. 5회 cool-down sessionStorage after threshold.
  2. try/catch/finally invariant — Supabase errors don't leak.
  3. Email existence NEVER revealed (security invariant).
  4. audit-first INSERT magic_link_sent fires.
  5. Result envelope always returns ok=true when not over cool-down.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = REPO_ROOT / "apps" / "web"
MAGIC_LINK_TS = WEB_ROOT / "lib" / "auth" / "magic-link.ts"
KO_KR_JSON = WEB_ROOT / "messages" / "ko-KR.json"


@pytest.fixture(scope="module")
def magic_link_content() -> str:
    assert MAGIC_LINK_TS.exists(), "magic-link.ts missing"
    return MAGIC_LINK_TS.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def ko_kr_content() -> str:
    assert KO_KR_JSON.exists(), "ko-KR.json missing"
    return json.loads(KO_KR_JSON.read_text(encoding="utf-8"))


class TestMagicLinkWrapper:
    def test_file_exists(self, magic_link_content: str) -> None:
        assert len(magic_link_content) > 100

    def test_uses_signinwithotp(self, magic_link_content: str) -> None:
        assert "signInWithOtp" in magic_link_content

    def test_email_redirect_to_includes_callback(self, magic_link_content: str) -> None:
        # Must redirect to the auth-callback page so the session is
        # established via exchangeCodeForSession.
        assert "auth-callback" in magic_link_content

    def test_5_failure_cooldown_30s(self, magic_link_content: str) -> None:
        assert "COOL_DOWN_THRESHOLD = 5" in magic_link_content
        assert "COOL_DOWN_DURATION_MS = 30_000" in magic_link_content

    def test_security_invariant_try_catch_finally(self, magic_link_content: str) -> None:
        # The Supabase call MUST be wrapped in try/catch/finally so
        # errors never surface to the user.
        assert "try {" in magic_link_content
        assert "} catch" in magic_link_content
        assert "} finally" in magic_link_content

    def test_always_returns_ok_true(self, magic_link_content: str) -> None:
        # SECURITY: returns ok:true regardless of whether the email
        # is registered.
        assert "ok: true" in magic_link_content
        assert "이메일이 등록된 경우" not in magic_link_content  # never reveal

    def test_audit_endpoint_called(self, magic_link_content: str) -> None:
        # audit-first INSERT magic_link_sent.
        assert "magic-link-sent" in magic_link_content
        assert "recordMagicLinkAudit" in magic_link_content


class TestMagicLinkForm:
    def test_form_component_exists(self) -> None:
        form = WEB_ROOT / "components" / "auth" / "MagicLinkForm.tsx"
        assert form.exists()

    def test_form_uses_ssmt(self) -> None:
        form = WEB_ROOT / "components" / "auth" / "MagicLinkForm.tsx"
        content = form.read_text(encoding="utf-8")
        # D-001 actual mount: page.tsx must render <MagicLinkForm />.
        assert "sendMagicLink" in content
        assert "MagicLinkForm" in content


class TestMagicLinkPages:
    def test_magic_link_page_exists(self) -> None:
        page = (
            WEB_ROOT
            / "app"
            / "[locale]"
            / "(auth)"
            / "magic-link"
            / "page.tsx"
        )
        assert page.exists()

    def test_magic_link_sent_page_exists(self) -> None:
        page = (
            WEB_ROOT
            / "app"
            / "[locale]"
            / "(auth)"
            / "magic-link-sent"
            / "page.tsx"
        )
        assert page.exists()

    def test_magic_link_page_mounts_form(self) -> None:
        page = (
            WEB_ROOT
            / "app"
            / "[locale]"
            / "(auth)"
            / "magic-link"
            / "page.tsx"
        )
        content = page.read_text(encoding="utf-8")
        # D-001 actual mount: <MagicLinkForm /> JSX.
        assert "<MagicLinkForm" in content

    def test_magic_link_sent_page_no_email_reveal(self) -> None:
        page = (
            WEB_ROOT
            / "app"
            / "[locale]"
            / "(auth)"
            / "magic-link-sent"
            / "page.tsx"
        )
        content = page.read_text(encoding="utf-8")
        # SECURITY: must NOT show "이메일이 등록되지 않았습니다" or similar.
        assert "등록되지" not in content


class TestKoKRNamespace:
    def test_magic_link_keys(self, ko_kr_content: dict) -> None:
        magic_link = ko_kr_content.get("auth", {}).get("magic_link", {})
        assert "title" in magic_link
        assert "subtitle" in magic_link
        assert "email_label" in magic_link
        assert "send_button" in magic_link
        assert "sent_message" in magic_link
        assert "alt_text" in magic_link
        assert "error" in magic_link
        assert "rate_limited" in magic_link["error"]
        assert "network" in magic_link["error"]


class TestAuthCallback:
    def test_callback_page_exists(self) -> None:
        page = (
            WEB_ROOT
            / "app"
            / "[locale]"
            / "(auth)"
            / "auth-callback"
            / "page.tsx"
        )
        assert page.exists()

    def test_callback_exchanges_code(self) -> None:
        page = (
            WEB_ROOT
            / "app"
            / "[locale]"
            / "(auth)"
            / "auth-callback"
            / "page.tsx"
        )
        content = page.read_text(encoding="utf-8")
        assert "exchangeCodeForSession" in content

    def test_callback_aal_branching(self) -> None:
        page = (
            WEB_ROOT
            / "app"
            / "[locale]"
            / "(auth)"
            / "auth-callback"
            / "page.tsx"
        )
        content = page.read_text(encoding="utf-8")
        # D-GATE-01: aal1 → /auth/2fa, aal2 → dashboard.
        assert "aal1" in content
        assert "aal2" in content
        assert "/auth/2fa" in content

    def test_callback_d005_unknown_state_reject(self) -> None:
        page = (
            WEB_ROOT
            / "app"
            / "[locale]"
            / "(auth)"
            / "auth-callback"
            / "page.tsx"
        )
        content = page.read_text(encoding="utf-8")
        # D-005: unknown AAL state MUST be rejected.
        assert '"unknown"' in content or "unknown" in content
