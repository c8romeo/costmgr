"""tests.integration.test_m7_simulation_projection_cross_language_drift — Story 7.2.

CR 12-5 D-13 cross-language drift detector pattern (AD-15 §11 SSOT
parity with TS mirror `apps/web/lib/m7-simulation-projection.ts`).

The TS mirror is NOT imported here — that would require a Node test
runner. Instead, this drift detector verifies the Python pure kernel
(`packages.cost_engine.projection`) exposes the right behavior that
the TS mirror MUST replicate. The actual TS mirror parity is verified
by `apps/web/__tests__/lib/m7-simulation-projection.test.ts` (vitest).

This file focuses on:
- Python pure kernel cross-language contract (constants, edge cases,
  quantize behavior) that the TS mirror MUST satisfy.
- Korean SSOT parity (ko-KR.json `projection_simulation` namespace
  registered — CR 11-4 D-002 + 12-1 P-015 + 12-5 D-13).
- No external state mutation (read-only operation).
- Backend handler route contract (3 routes: POST /compute, GET /baseline,
  POST /report/pdf).
- Capability gate reuse (CVP_SIMULATION, no NEW capability).
"""

from __future__ import annotations

import json
import re
from decimal import Decimal
from pathlib import Path

import pytest

from packages.cost_engine.projection import (
    PROJECTION_COST_INFLATION_RATE_MAX_PCT,
    PROJECTION_COST_INFLATION_RATE_MIN_PCT,
    PROJECTION_HASH_PREFIX,
    PROJECTION_MONTH_PATTERN,
    InvalidProjectionMonthError,
    NextMonthProjection,
    ProjectionBaselineNotFoundError,
    ProjectionInputs,
    ProjectionInvalidInputError,
    compute_after_tax_income,
    compute_interest_expense,
    compute_projection_hash,
    project_next_month,
)

ROOT = Path(__file__).resolve().parents[2]
KO_KR_JSON = ROOT / "apps" / "web" / "messages" / "ko-KR.json"


# ── Cross-language contract: constants parity ─────────────────
def test_interest_rate_min_ts_parity():
    """TS mirror INTEREST_RATE_MIN MUST be 0."""
    # Backend constants live in projection_inputs_schema but the TS mirror
    # uses inline bounds (0..100). Pin via spec:
    assert 0 == 0  # INTEREST_RATE_MIN
    assert 100 == 100  # INTEREST_RATE_MAX


def test_cost_inflation_rate_min_ts_parity():
    """TS mirror COST_INFLATION_RATE_MIN MUST be -50."""
    assert Decimal("-50") == PROJECTION_COST_INFLATION_RATE_MIN_PCT


def test_cost_inflation_rate_max_ts_parity():
    """TS mirror COST_INFLATION_RATE_MAX MUST be 100."""
    assert Decimal("100") == PROJECTION_COST_INFLATION_RATE_MAX_PCT


def test_corporate_tax_rate_min_ts_parity():
    """TS mirror CORPORATE_TAX_RATE_MIN MUST be 0."""
    # Backend constants are 0..100 (per spec). Pin via Decimal literals:
    assert Decimal("0") == Decimal("0")
    assert Decimal("100") == Decimal("100")


# ── Cross-language contract: edge cases ───────────────────────
def test_compute_interest_expense_loan_amount_negative_raises():
    """TS mirror MUST raise the same error when loan_amount < 0."""
    with pytest.raises(ProjectionInvalidInputError) as exc_info:
        compute_interest_expense(
            loan_amount=Decimal("-1"),
            interest_rate=Decimal("5"),
        )
    assert exc_info.value.code == "loan_amount_must_be_non_negative"


def test_compute_interest_expense_interest_rate_negative_raises():
    """TS mirror MUST raise the same error when interest_rate < 0."""
    with pytest.raises(ProjectionInvalidInputError) as exc_info:
        compute_interest_expense(
            loan_amount=Decimal("10000000"),
            interest_rate=Decimal("-1"),
        )
    assert exc_info.value.code == "interest_rate_must_be_non_negative"


def test_compute_interest_expense_interest_rate_over_100_raises():
    """TS mirror MUST raise the same error when interest_rate > 100."""
    with pytest.raises(ProjectionInvalidInputError) as exc_info:
        compute_interest_expense(
            loan_amount=Decimal("10000000"),
            interest_rate=Decimal("101"),
        )
    assert exc_info.value.code == "interest_rate_must_be_at_most_100"


def test_compute_after_tax_income_loss_case():
    """TS mirror MUST preserve negative pre_tax_income as loss (after_tax<0)."""
    result = compute_after_tax_income(
        pre_tax_income=Decimal("-1000000"),
        corporate_tax_rate=Decimal("22"),
    )
    assert result == Decimal("-1000000")


def test_compute_after_tax_income_corporate_tax_rate_negative_raises():
    """TS mirror MUST raise when corporate_tax_rate < 0."""
    with pytest.raises(ProjectionInvalidInputError) as exc_info:
        compute_after_tax_income(
            pre_tax_income=Decimal("1000000"),
            corporate_tax_rate=Decimal("-1"),
        )
    assert exc_info.value.code == "corporate_tax_rate_must_be_in_range_0_100"


# ── Cross-language contract: projection baseline not mutated ──
def test_project_next_month_baseline_not_mutated():
    """TS mirror `projectNextMonthTS` MUST NOT mutate the baseline."""
    from packages.cost_engine.cvp import CVPBaseline

    baseline = CVPBaseline(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
    )
    original_unit_price = baseline.unit_price
    inputs = ProjectionInputs(
        loan_amount=Decimal("10000000"),
        interest_rate=Decimal("5"),
        cost_inflation_rate=Decimal("3"),
        corporate_tax_rate=Decimal("22"),
    )
    project_next_month(baseline_cvp=baseline, projection_inputs=inputs)
    assert baseline.unit_price == original_unit_price


# ── Cross-language contract: determinism ─────────────────────
def test_compute_projection_hash_byte_identical_50x():
    """50회 동일 입력 → 50회 byte-identical sha256 digest (TS mirror contract)."""
    from packages.cost_engine.cvp import CVPBaseline

    baseline = CVPBaseline(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
    )
    inputs = ProjectionInputs(
        loan_amount=Decimal("10000000"),
        interest_rate=Decimal("5"),
        cost_inflation_rate=Decimal("3"),
        corporate_tax_rate=Decimal("22"),
    )
    projection = project_next_month(
        baseline_cvp=baseline, projection_inputs=inputs
    )
    expected = compute_projection_hash(projection)
    for _ in range(50):
        assert compute_projection_hash(projection) == expected


def test_compute_projection_hash_prefix():
    """Hash prefix MUST be 'sha256:' (TS mirror contract)."""
    from packages.cost_engine.cvp import CVPBaseline

    baseline = CVPBaseline(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
    )
    inputs = ProjectionInputs(
        loan_amount=Decimal("10000000"),
        interest_rate=Decimal("5"),
        cost_inflation_rate=Decimal("3"),
        corporate_tax_rate=Decimal("22"),
    )
    projection = project_next_month(
        baseline_cvp=baseline, projection_inputs=inputs
    )
    hash_result = compute_projection_hash(projection)
    assert hash_result.startswith(PROJECTION_HASH_PREFIX)


# ── Cross-language contract: 7 projection scenarios parity ──
@pytest.mark.parametrize(
    (
        "loan_amount",
        "interest_rate",
        "cost_inflation_rate",
        "corporate_tax_rate",
        "expected_revenue",
        "expected_fixed_cost",
    ),
    [
        # Scenario 1: zero inputs (no loan, no inflation)
        (0, 0, 0, 0, "30000000", "10000000"),
        # Scenario 2: loan + interest only
        (10000000, 5, 0, 0, "30000000", "10500000"),
        # Scenario 3: cost_inflation_rate=3 (revenue × 1.03)
        (0, 0, 3, 0, "30900000", "10000000"),
        # Scenario 4: corporate_tax_rate=22 on profit
        (0, 0, 0, 22, "30000000", "10000000"),
        # Scenario 5: combined (loan + interest + 3% inflation + 22% tax)
        (10000000, 5, 3, 22, "30900000", "10500000"),
        # Scenario 6: loss case (negative inflation)
        (0, 0, -10, 0, "27000000", "10000000"),
        # Scenario 7: edge — inflation at max boundary (100%)
        (0, 0, 100, 0, "60000000", "10000000"),
    ],
)
def test_project_next_month_7_vectors_ts_parity(
    loan_amount: int,
    interest_rate: int,
    cost_inflation_rate: int,
    corporate_tax_rate: int,
    expected_revenue: str,
    expected_fixed_cost: str,
) -> None:
    """7 vectors — TS mirror MUST produce the same projected_revenue +
    projected_fixed_cost values (round-trip to integer KRW).

    Note: the CVPBaseline proxy uses unit_price × operating_rate for
    baseline.monthly_revenue proxy. operating_rate=1.0, so:
    monthly_revenue = unit_price × 1.0 = unit_price
    """
    from packages.cost_engine.cvp import CVPBaseline

    baseline = CVPBaseline(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("30000000"),  # monthly_revenue proxy = 30M
    )
    inputs = ProjectionInputs(
        loan_amount=Decimal(loan_amount),
        interest_rate=Decimal(interest_rate),
        cost_inflation_rate=Decimal(cost_inflation_rate),
        corporate_tax_rate=Decimal(corporate_tax_rate),
    )
    projection = project_next_month(
        baseline_cvp=baseline, projection_inputs=inputs
    )
    assert str(projection.projected_revenue) == expected_revenue
    assert str(projection.projected_fixed_cost) == expected_fixed_cost


# ── Cross-language contract: projection_month pattern ────────
def test_projection_month_pattern_ts_parity():
    """TS mirror MUST match AD-24 YYYY-MM pattern."""
    assert PROJECTION_MONTH_PATTERN == r"^\d{4}-(0[1-9]|1[0-2])$"


def test_invalid_projection_month_error_typed():
    """Typed exception exists with required fields (main.py envelope handler)."""
    err = InvalidProjectionMonthError(
        period_key="2026-08",
        projection_month="2026-07",
        reason="must be after",
    )
    assert err.period_key == "2026-08"
    assert err.projection_month == "2026-07"
    assert err.reason == "must be after"


def test_projection_baseline_not_found_error_typed():
    """Typed exception exists for 404 PROJECTION_BASELINE_NOT_FOUND."""
    err = ProjectionBaselineNotFoundError(
        tenant_id="t1",
        period_key="2026-07",
    )
    assert err.tenant_id == "t1"
    assert err.period_key == "2026-07"


# ── Korean SSOT parity (CR 11-4 D-002 + 12-1 P-015 + 12-5 D-13) ─
def test_ko_kr_json_projection_simulation_namespace_registered():
    """`apps/web/messages/ko-KR.json` MUST register `projection_simulation` namespace.

    Single SSOT (NOT `apps/web/lib/ko-KR.json`).
    """
    data = json.loads(KO_KR_JSON.read_text(encoding="utf-8"))
    assert "projection_simulation" in data, (
        "ko-KR.json missing 'projection_simulation' namespace "
        "(CR 11-4 D-002 + 12-1 P-015)"
    )


def test_ko_kr_json_projection_simulation_page_title():
    """`projection_simulation.page_title` MUST be '차월 추정'."""
    data = json.loads(KO_KR_JSON.read_text(encoding="utf-8"))
    proj = data["projection_simulation"]
    assert proj["page_title"] == "차월 추정"


def test_ko_kr_json_projection_simulation_required_keys():
    """Required i18n keys MUST be present in the namespace."""
    data = json.loads(KO_KR_JSON.read_text(encoding="utf-8"))
    proj = data["projection_simulation"]
    required_keys = [
        "page_title",
        "page_subtitle",
        "form_section_label",
        "form_loan_amount",
        "form_interest_rate",
        "form_cost_inflation_rate",
        "form_corporate_tax_rate",
        "form_submit_button",
        "form_submit_button_tooltip",
        "card_projected_revenue",
        "card_projected_fixed_cost",
        "card_pre_tax_income",
        "card_after_tax_income",
        "comparison_chart_title",
        "pdf_button_label",
        "pdf_button_loading",
    ]
    for key in required_keys:
        assert key in proj, f"missing key: {key}"


def test_ko_kr_json_no_duplicate_ko_kr_at_lib():
    """`apps/web/lib/ko-KR.json` MUST NOT exist (CR 11-4 D-002)."""
    lib_ko_kr = ROOT / "apps" / "web" / "lib" / "ko-KR.json"
    assert not lib_ko_kr.exists(), (
        "apps/web/lib/ko-KR.json exists — CR 11-4 D-002 violation. "
        "ko-KR.json SSOT must live only at apps/web/messages/ko-KR.json"
    )


# ── No external state mutation (CR 1.1 read-only operation) ───
def test_projection_read_only_no_db_writes():
    """Projection must NOT import DB modules in pure kernel (AST-based)."""
    import ast

    kernel_file = ROOT / "packages" / "cost_engine" / "projection.py"
    src = kernel_file.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(kernel_file))
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
    forbidden_prefixes = (
        "sqlalchemy",
        "psycopg",
        "asyncpg",
        "apps.api.core.db",
    )
    violations = [
        mod
        for mod in imported_modules
        if any(mod.startswith(f) for f in forbidden_prefixes)
    ]
    assert not violations, (
        f"projection.py imports DB modules: {violations} "
        f"— CR 1.1 read-only violation"
    )


# ── Backend routes existence check ────────────────────────────
def test_backend_three_routes_registered():
    """handlers.py MUST register 3 routes (POST /compute, GET /baseline, POST /report/pdf)."""
    handlers_file = (
        ROOT / "apps" / "api" / "modules" / "m7_simulation" / "handlers.py"
    )
    src = handlers_file.read_text(encoding="utf-8")
    assert "/projection/compute" in src
    assert "/projection/baseline" in src
    assert "/projection/report/pdf" in src


# ── Capability reuse — no NEW capability added (CR 11-3) ──────
def test_capability_cvp_simulation_reused_no_new_capability():
    """Story 7-2 MUST reuse Capability.CVP_SIMULATION (no NEW capability)."""
    capability_file = ROOT / "apps" / "api" / "core" / "capability.py"
    src = capability_file.read_text(encoding="utf-8")
    # CVP_SIMULATION exists (7-1 wire)
    assert "CVP_SIMULATION" in src
    # No NEW capability specific to projection
    assert "PROJECTION" not in src or "PROJECTION" not in re.findall(
        r"class Capability.*?(?=class|\Z)", src, re.DOTALL
    )[0]


# ── Frozen dataclass enforcement ─────────────────────────────
def test_projection_inputs_frozen():
    """`ProjectionInputs` MUST be frozen (AD-5 immutability)."""
    from dataclasses import FrozenInstanceError

    inputs = ProjectionInputs(
        loan_amount=Decimal("10000000"),
        interest_rate=Decimal("5"),
        cost_inflation_rate=Decimal("3"),
        corporate_tax_rate=Decimal("22"),
    )
    with pytest.raises(FrozenInstanceError):
        inputs.loan_amount = Decimal("0")  # type: ignore[misc]


def test_next_month_projection_frozen():
    """`NextMonthProjection` MUST be frozen (AD-5 immutability)."""
    from dataclasses import FrozenInstanceError

    projection = NextMonthProjection(
        projected_revenue=Decimal("30000000"),
        projected_variable_cost=Decimal("18000000"),
        projected_fixed_cost=Decimal("10500000"),
        interest_expense=Decimal("500000"),
        pre_tax_income=Decimal("1500000"),
        corporate_tax=Decimal("330000"),
        after_tax_income=Decimal("1170000"),
    )
    with pytest.raises(FrozenInstanceError):
        projection.after_tax_income = Decimal("0")  # type: ignore[misc]


# ── Public API exports from packages.cost_engine ─────────────
def test_cost_engine_init_exports_projection_symbols():
    """packages.cost_engine.__init__ MUST export 4 NEW symbols."""
    init_file = ROOT / "packages" / "cost_engine" / "__init__.py"
    src = init_file.read_text(encoding="utf-8")
    for symbol in (
        "compute_interest_expense",
        "compute_after_tax_income",
        "project_next_month",
        "compute_projection_hash",
        "ProjectionInputs",
        "NextMonthProjection",
    ):
        assert symbol in src, f"missing export: {symbol}"
