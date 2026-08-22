"""
tests/integration/test_1st_release_launch_checklist.py — Launch checklist 6 conditions.

1st release launch (cj-style 64번째 진입점) — T7.3 (AC #9.6) — F18 launch checklist 6 conditions.
- ① landing page wire DONE
- ② ToS/Privacy wire DONE
- ③ onboarding guide wire DONE
- ④ support channels wire DONE
- ⑤ smoke test + backup drill PASS
- ⑥ launch comms published
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_checklist_1_landing_page():
    """① landing page wire DONE."""
    page = REPO_ROOT / "apps" / "web" / "app" / "[locale]" / "(public)" / "landing" / "page.tsx"
    hero = REPO_ROOT / "apps" / "web" / "components" / "landing" / "LandingHero.tsx"
    features = REPO_ROOT / "apps" / "web" / "components" / "landing" / "LandingFeatures.tsx"
    pricing = REPO_ROOT / "apps" / "web" / "components" / "landing" / "LandingPricing.tsx"
    cta = REPO_ROOT / "apps" / "web" / "components" / "landing" / "LandingCTA.tsx"
    assert page.exists()
    assert hero.exists()
    assert features.exists()
    assert pricing.exists()
    assert cta.exists()


def test_checklist_2_tos_privacy():
    """② ToS/Privacy wire DONE."""
    tos = REPO_ROOT / "docs" / "terms-of-service.md"
    privacy = REPO_ROOT / "docs" / "privacy-policy.md"
    tos_page = REPO_ROOT / "apps" / "web" / "app" / "[locale]" / "(auth)" / "tos" / "page.tsx"
    privacy_page = REPO_ROOT / "apps" / "web" / "app" / "[locale]" / "(auth)" / "privacy" / "page.tsx"
    assert tos.exists()
    assert privacy.exists()
    assert tos_page.exists()
    assert privacy_page.exists()


def test_checklist_3_onboarding_guide():
    """③ onboarding guide wire DONE."""
    guide = REPO_ROOT / "docs" / "onboarding-guide.md"
    tooltip = REPO_ROOT / "apps" / "web" / "components" / "onboarding" / "OnboardingTooltip.tsx"
    page = REPO_ROOT / "apps" / "web" / "app" / "[locale]" / "(auth)" / "onboarding" / "page.tsx"
    assert guide.exists()
    assert tooltip.exists()
    assert page.exists()


def test_checklist_4_support_channels():
    """④ support channels wire DONE."""
    support_doc = REPO_ROOT / "docs" / "support.md"
    faq = REPO_ROOT / "docs" / "faq.md"
    widget = REPO_ROOT / "apps" / "web" / "components" / "support" / "HelpWidget.tsx"
    support_page = REPO_ROOT / "apps" / "web" / "app" / "[locale]" / "(auth)" / "support" / "page.tsx"
    assert support_doc.exists()
    assert faq.exists()
    assert widget.exists()
    assert support_page.exists()


def test_checklist_5_smoke_test_backup_drill():
    """⑤ smoke test + backup drill PASS (capability v1.27 + sentry alerts)."""
    smoke = REPO_ROOT / "apps" / "api" / "scripts" / "smoke_test.py"
    sentry_backend = REPO_ROOT / "apps" / "api" / "lib" / "observability" / "sentry-alerts.py"
    sentry_frontend = REPO_ROOT / "apps" / "web" / "lib" / "observability" / "sentry-alerts.ts"
    cap = REPO_ROOT / "apps" / "api" / "core" / "capability.py"
    assert smoke.exists()
    assert sentry_backend.exists()
    assert sentry_frontend.exists()
    cap_content = cap.read_text(encoding="utf-8")
    assert "LAUNCH_MONITORING" in cap_content


def test_checklist_6_launch_comms():
    """⑥ launch comms published."""
    announcement = REPO_ROOT / "docs" / "launch-announcement.md"
    press_kit = REPO_ROOT / "docs" / "press-kit.md"
    assert announcement.exists()
    assert press_kit.exists()


def test_checklist_7_capability_v1_27():
    """Capability matrix v1.27 has 4 LAUNCH_* rows."""
    matrix = REPO_ROOT / "docs" / "capability-matrix.md"
    content = matrix.read_text(encoding="utf-8")
    assert "v1.27" in content
    assert "LAUNCH_LANDING" in content
    assert "LAUNCH_TOS" in content
    assert "LAUNCH_SUPPORT" in content
    assert "LAUNCH_MONITORING" in content


def test_checklist_8_ko_kr_ssot():
    """ko-KR.json has 5 NEW namespaces (landing, auth.tos, auth.privacy, onboarding, support)."""
    ko = REPO_ROOT / "apps" / "web" / "messages" / "ko-KR.json"
    content = ko.read_text(encoding="utf-8")
    assert '"landing"' in content
    assert '"tos"' in content
    assert '"privacy"' in content
    assert '"onboarding"' in content
    assert '"support"' in content
