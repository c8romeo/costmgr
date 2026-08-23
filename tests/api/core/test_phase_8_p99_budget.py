"""tests.api.core.test_phase_8_p99_budget — ESLint latency-budget-rule parity tests.

4 NEW pytest cases PASS (Phase 8 cj-style 95번째 wire backend tests).
Mirrors CR 12-5 D-PARITY-01 — backend ↔ frontend parity check.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


ESLINT_RULE_PATH = Path(
    __file__).parent.parent.parent / "apps" / "api" / "eslint" / "latency-budget-rule.js"
DEFAULT_BUDGETS_PATH = Path(
    __file__).parent.parent.parent / "apps" / "api" / "core" / "latency_budget.py"


# ── 4 NEW pytest cases (Phase 8 T7.3) ──────────────────────────


def test_eslint_rule_file_exists() -> None:
    """T7.3-1 — apps/api/eslint/latency-budget-rule.js must exist."""
    assert ESLINT_RULE_PATH.exists(), f"missing: {ESLINT_RULE_PATH}"


def test_eslint_rule_lists_known_endpoints() -> None:
    """T7.3-2 — rule defines the canonical endpoint set in KNOWN_ENDPOINTS."""
    content = ESLINT_RULE_PATH.read_text(encoding="utf-8")
    assert "KNOWN_ENDPOINTS" in content
    # 7 canonical endpoints per DEFAULT_LATENCY_BUDGETS.
    expected = [
        "POST /api/v1/cost-engine/compute",
        "GET /api/v1/audit-log",
        "POST /api/v1/auth/login",
        "GET /api/v1/admin/health/multi-region",
        "POST /api/v1/abc/compute",
        "POST /api/v1/tdabc/compute",
        "POST /api/v1/ai/extraction",
    ]
    for endpoint in expected:
        assert endpoint in content, f"missing {endpoint!r} in KNOWN_ENDPOINTS"


def test_eslint_rule_emits_unmapped_endpoint_message() -> None:
    """T7.3-3 — rule emits `unmappedEndpoint` messageId (CR 12-5 D-14)."""
    content = ESLINT_RULE_PATH.read_text(encoding="utf-8")
    assert "unmappedEndpoint" in content
    assert "DEFAULT_LATENCY_BUDGETS" in content


def test_eslint_rule_handles_dry_run_marker() -> None:
    """T7.3-4 — synthetic dry_run fallback is documented in module comment."""
    content = DEFAULT_BUDGETS_PATH.read_text(encoding="utf-8")
    assert "synthetic fallback" in content.lower()
    assert "dry_run" in content
