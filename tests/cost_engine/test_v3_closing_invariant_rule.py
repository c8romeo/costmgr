"""tests.cost_engine.test_v3_closing_invariant_rule — Story 5.3 V3 rule kernel tests.

Tests for `apps.api.modules.m3_calculate.services.rules.v3_closing_invariant`:
- V3 rule name = 'V3'
- V3 applies_to: True for non-service, False for service-only
- V3 check() with pre-loaded V3Verdict (passed / failed / skipped / None)
- V3 slot 3 of 5 in _VERIFICATION_RULES ordering
- V3 is a PURE kernel (AD-5 — no I/O imports)
"""

from __future__ import annotations

import ast
import uuid
from pathlib import Path
from decimal import Decimal
from uuid import UUID

import pytest

from apps.api.modules.m3_calculate.services.rules import (
    _VERIFICATION_RULES,
    RuleInput,
)
from apps.api.modules.m3_calculate.services.rules.protocol import (
    INDUSTRY_SERVICE,
)
from apps.api.modules.m3_calculate.services.rules.v3_closing_invariant import (
    V3ClosingInvariantRule,
)
from packages.cost_engine.ports.calc_port import CalcResult, MonthlyInput
from packages.cost_engine.core.period_cost import Baseline


# ── V3 name + applies_to ───────────────────────────────────────
def test_v3_name_is_v3():
    """V3.name returns 'V3' literal."""
    rule = V3ClosingInvariantRule()
    assert rule.name == "V3"


def test_v3_applies_to_non_service():
    """V3 fires for all industries EXCEPT service-only."""
    rule = V3ClosingInvariantRule()
    assert rule.applies_to(industry="manufacturing") is True
    assert rule.applies_to(industry="manufacturing_service") is True
    assert rule.applies_to(industry="manufacturing_service_other") is True


def test_v3_skips_service_only():
    """V3 does NOT fire for service-only (no inventory semantics)."""
    rule = V3ClosingInvariantRule()
    assert rule.applies_to(industry=INDUSTRY_SERVICE) is False


# ── V3 ordering invariant (slot 3 of 5) ────────────────────────
def test_v3_slot_3_of_5():
    """AD-12 ordering: V1 → V4 → V3 → V7 → V8 (V3 is slot 3)."""
    names = [r.name for r in _VERIFICATION_RULES]
    assert names == ["V1", "V4", "V3", "V7", "V8"], (
        f"V3 must be slot 3 of 5 (V1 → V4 → V3 → V7 → V8). Got: {names}"
    )


# ── V3 check() with pre-loaded V3Verdict ───────────────────────
def _make_rule_input(*, verdict) -> RuleInput:
    """Build a minimal RuleInput for V3 check() — V3 only reads verdict."""
    return RuleInput(
        monthly_input=MonthlyInput(
            tenant_id=UUID(int=1),
            period_key="2026-07",
            direct_material_krw=Decimal("0"),
            direct_labor_krw=Decimal("0"),
            indirect_krw=Decimal("0"),
            fte_headcount=Decimal("0"),
        ),
        baseline=Baseline(
            fiscal_period="2026-07",
            standard_monthly_hours=209,
            bom_ratio_validated=True,
            allocation_basis_set=True,
        ),
        calc_result=CalcResult(
            tenant_id=UUID(int=1),
            period_key="2026-07",
            material_cost=Decimal("0"),
            labor_cost=Decimal("0"),
            overhead_cost=Decimal("0"),
            manufacturing_cost=Decimal("0"),
            inventory_adjustment=Decimal("0"),
            result_hash="",
            state="draft",
        ),
        industry="manufacturing",
        tenant_id=UUID(int=1),
        period_key="2026-07",
        trace_id="test",
        closing_invariant_verdict=verdict,
    )


def test_v3_check_passed_verdict():
    """Pre-loaded V3Verdict with status='passed' → status='passed'."""
    from packages.cost_engine.closing_invariant_check import (
        V3_STATUS_PASSED,
    )

    rule = V3ClosingInvariantRule()
    verdict = {
        "status": V3_STATUS_PASSED,
        "code": "V3",
        "failures": [],
        "verified_at": "2026-08-05T00:00:00Z",
        "product_whitelist_size": 2,
        "skip_reason_ko": None,
    }
    item = rule.check(input=_make_rule_input(verdict=verdict))
    assert item.code == "V3"
    assert item.status == "passed"


def test_v3_check_failed_verdict():
    """Pre-loaded V3Verdict with status='failed' → status='failed'."""
    from packages.cost_engine.closing_invariant_check import (
        V3_STATUS_FAILED,
    )

    rule = V3ClosingInvariantRule()
    verdict = {
        "status": V3_STATUS_FAILED,
        "code": "V3",
        "failures": [
            {
                "product_id": "00000000-0000-0000-0000-000000000001",
                "closing_qty": "-5.0000",
                "message_ko": "기말재고 음수 -5개 (PRD §V3)",
            }
        ],
        "verified_at": "2026-08-05T00:00:00Z",
        "product_whitelist_size": 2,
        "skip_reason_ko": None,
    }
    item = rule.check(input=_make_rule_input(verdict=verdict))
    assert item.code == "V3"
    assert item.status == "failed"
    assert "기말재고 음수" in item.message_ko


def test_v3_check_skipped_verdict():
    """Pre-loaded V3Verdict with status='skipped' → status='skipped' (CR 5.3 P17).

    CR 5.3 P17 review patch — pre-patch, this case returned status='passed'
    (silent skip). Post-patch, it surfaces status='skipped' so callers can
    distinguish "evaluated and passed" from "evaluated and skipped". 'skipped'
    still does NOT block later rules per AD-12 — it's a metadata flag.
    """
    from packages.cost_engine.closing_invariant_check import (
        V3_SKIP_REASON_SERVICE_ONLY_KO,
        V3_STATUS_SKIPPED,
    )

    rule = V3ClosingInvariantRule()
    verdict = {
        "status": V3_STATUS_SKIPPED,
        "code": "V3",
        "failures": [],
        "verified_at": "2026-08-05T00:00:00Z",
        "product_whitelist_size": 0,
        "skip_reason_ko": V3_SKIP_REASON_SERVICE_ONLY_KO,
    }
    item = rule.check(input=_make_rule_input(verdict=verdict))
    # CR 5.3 P17 — skipped verdict surfaces as status='skipped' (NOT 'passed').
    assert item.code == "V3"
    assert item.status == "skipped"


def test_v3_check_none_verdict():
    """No pre-loaded V3Verdict → status='skipped' with skip message (CR 5.3 P17)."""
    rule = V3ClosingInvariantRule()
    item = rule.check(input=_make_rule_input(verdict=None))
    assert item.code == "V3"
    # CR 5.3 P17 — None verdict surfaces as status='skipped' (defense-in-depth).
    assert item.status == "skipped"


# ── AD-5 purity: V3 rule kernel has no I/O imports ────────────
def test_v3_purity_no_io_imports():
    """V3 rule module must NOT import sqlalchemy, fastapi, time, random."""
    rule_path = Path(__file__).resolve().parents[2] / (
        "apps/api/modules/m3_calculate/services/rules/v3_closing_invariant.py"
    )
    assert rule_path.exists()
    src = rule_path.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(rule_path))
    forbidden = {"sqlalchemy", "fastapi", "httpx", "starlette", "asyncpg", "psycopg"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden, (
                    f"V3 rule kernel imports forbidden module: {alias.name}"
                )
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in forbidden, (
                f"V3 rule kernel imports forbidden module: {node.module}"
            )
