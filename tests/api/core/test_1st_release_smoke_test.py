"""
tests/api/core/test_1st_release_smoke_test.py — 1st release smoke test RE-RUN.

1st release launch (cj-style 64번째 진입점) — T7.2 (AC #9.3) — F18.5 Production verification.
- smoke_test.py RE-RUN 정직 결정 wire (Walking Skeleton MVP + Phase 3 close-out retro §6 해소).
- Epic 1~15 wire flow 정합 sweep.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SMOKE_TEST_PATH = REPO_ROOT / "apps" / "api" / "scripts" / "smoke_test.py"


@pytest.fixture(scope="module")
def smoke_test_module():
    """Load smoke_test.py as a module (it's a script)."""
    if not SMOKE_TEST_PATH.exists():
        pytest.fail(f"smoke_test.py not found at {SMOKE_TEST_PATH}")
    spec = importlib.util.spec_from_file_location("smoke_test", SMOKE_TEST_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["smoke_test"] = module
    spec.loader.exec_module(module)
    return module


def test_smoke_test_module_loads(smoke_test_module):
    """smoke_test.py should load without errors."""
    assert smoke_test_module is not None


def test_smoke_test_flo_includes_auth(smoke_test_module):
    """FLOWS should include all 5 auth methods (Epic 15 wire)."""
    flow_str = " ".join(smoke_test_module.FLOWS)
    assert "magic_link" in flow_str
    assert "oauth_google" in flow_str
    assert "oauth_naver" in flow_str
    assert "oauth_kakao" in flow_str
    assert "sso_enterprise" in flow_str
    assert "2fa" in flow_str


def test_smoke_test_flo_includes_abc(smoke_test_module):
    """FLOWS should include ABC + TDABC engine (Epic 9 wire)."""
    flow_str = " ".join(smoke_test_module.FLOWS)
    assert "abc" in flow_str
    assert "tdabc" in flow_str


def test_smoke_test_flo_includes_ai(smoke_test_module):
    """FLOWS should include AI 인사이트 (Epic 10 wire)."""
    flow_str = " ".join(smoke_test_module.FLOWS)
    assert "ai_insight" in flow_str


def test_smoke_test_flo_includes_listen_notify(smoke_test_module):
    """FLOWS should include LISTEN/NOTIFY (Epic 13/14 wire)."""
    flow_str = " ".join(smoke_test_module.FLOWS)
    assert "listen_notify" in flow_str


def test_smoke_test_flo_includes_backup(smoke_test_module):
    """FLOWS should include backup (Phase 4 wire)."""
    flow_str = " ".join(smoke_test_module.FLOWS)
    assert "backup" in flow_str


def test_smoke_test_run_returns_0(smoke_test_module):
    """run_smoke_test() should return 0 (all flows PASS)."""
    exit_code = smoke_test_module.run_smoke_test()
    assert exit_code == 0


def test_smoke_test_total_flows_count(smoke_test_module):
    """FLOWS should have at least 13 entries (full Epic 1~15 sweep)."""
    assert len(smoke_test_module.FLOWS) >= 13
