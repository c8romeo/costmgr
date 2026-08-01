"""tests.services.test_m2_input_warnings — Story 3.3 warning aggregate pure helpers.

Mirrors Story 3.2's `test_m2_input_labor_conversion.py` pattern: pure,
stdlib-only, no DB, no clock (AD-1/AD-5).

Acceptance Criteria mapping (Story 3.3):
- AC #1: NEGATIVE_CLOSING_INVENTORY fire at closing_qty < 0
- AC #2: aggregate immediate disappear on qty fix
- AC #3: OVERCAPACITY_OPERATING_RATE fire at operating_rate > 100%
- AC #5: independent warning resolution (clear 1, remain other)
- AC #6: service-only tenant → 0 inventory warnings
- AC #8: severity ASC + closing_qty ASC sort
- PRD §A11: severity order error > warning > info
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from packages.services.m2_input.inventory_projection import InventoryMovement
from packages.services.m2_input.warnings import (
    SEVERITY_ORDER,
    Warning,
    WarningCode,
    aggregate_warnings,
    build_inventory_warnings,
    build_operating_rate_warning,
    format_inventory_warning_ko,
    format_operating_rate_ko,
)


# ── Lightweight product stub ─────────────────────────────────
@dataclass(frozen=True)
class _ProductStub:
    """Product duck type: only `product_id` + `product_code` + `name_ko`."""

    product_id: uuid.UUID
    product_code: str
    name_ko: str = ""


# ── WarningCode enum (story 3.3 range) ───────────────────────
def test_warning_codes_python_enum() -> None:
    """2 codes exposed (Story 3.3 scope)."""
    codes = sorted(c.value for c in WarningCode)
    assert codes == sorted(
        ["NEGATIVE_CLOSING_INVENTORY", "OVERCAPACITY_OPERATING_RATE"]
    )


def test_warning_codes_are_strings() -> None:
    """`WarningCode` is `str` enum (AD-15 JSON serialization)."""
    assert WarningCode.NEGATIVE_CLOSING_INVENTORY == "NEGATIVE_CLOSING_INVENTORY"
    assert isinstance(WarningCode.NEGATIVE_CLOSING_INVENTORY, str)


# ── SEVERITY_ORDER (PRD §A11) ────────────────────────────────
def test_severity_order_error_first() -> None:
    """PRD §A11: error > warning > info."""
    assert SEVERITY_ORDER["error"] < SEVERITY_ORDER["warning"]
    assert SEVERITY_ORDER["warning"] < SEVERITY_ORDER["info"]


def test_severity_order_values() -> None:
    """SEVERITY_ORDER canonical values."""
    assert SEVERITY_ORDER == {"error": 0, "warning": 1, "info": 2}


# ── Warning NamedTuple ───────────────────────────────────────
def test_warning_named_tuple_shape() -> None:
    """Warning has code, severity, message_ko, details, stream, trace_id, timestamp."""
    from datetime import UTC, datetime

    w = Warning(
        code="NEGATIVE_CLOSING_INVENTORY",
        severity="error",
        message_ko="PRD-0001(달걀) 기말재고 -30 → 음수 경고",
        details={"product_id": str(uuid.uuid4()), "closing_qty": "-30"},
        stream="sales",
        trace_id="trace-123",
        timestamp=datetime.now(tz=UTC),
    )
    assert w.code == "NEGATIVE_CLOSING_INVENTORY"
    assert w.severity == "error"
    assert w.message_ko.startswith("PRD-0001")
    assert w.stream == "sales"
    assert w.trace_id == "trace-123"


# ── build_inventory_warnings ─────────────────────────────────
def test_build_inventory_warnings_empty() -> None:
    """empty projection → no warnings."""
    assert build_inventory_warnings([]) == []


def test_build_inventory_warnings_single_negative() -> None:
    """AC #1: 1 product closing=-30 → 1 warning."""
    pid = uuid.uuid4()
    proj = [
        InventoryMovement(
            product_id=pid,
            opening_qty=Decimal("100"),
            inbound_qty=Decimal("0"),
            outbound_qty=Decimal("130"),
        ),
    ]
    product = _ProductStub(product_id=pid, product_code="PRD-0001", name_ko="달걀")
    warnings = build_inventory_warnings(proj, product_map={pid: product})
    assert len(warnings) == 1
    assert warnings[0].code == "NEGATIVE_CLOSING_INVENTORY"
    assert warnings[0].severity == "error"
    assert warnings[0].stream == "sales"
    assert warnings[0].details["closing_qty"] == "-30"
    assert warnings[0].details["product_id"] == str(pid)


def test_build_inventory_warnings_positive_no_warning() -> None:
    """closing_qty >= 0 → no warning."""
    pid = uuid.uuid4()
    proj = [
        InventoryMovement(
            product_id=pid,
            opening_qty=Decimal("100"),
            inbound_qty=Decimal("0"),
            outbound_qty=Decimal("30"),
        ),
    ]
    assert build_inventory_warnings(proj, product_map={}) == []


def test_build_inventory_warnings_multiple_products_sorted() -> None:
    """AC #8: 3 products → sorted by closing_qty ASC (most negative first)."""
    p1, p2, p3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    proj = [
        InventoryMovement(
            product_id=p1,
            opening_qty=Decimal("100"),
            inbound_qty=Decimal("0"),
            outbound_qty=Decimal("130"),
        ),  # -30
        InventoryMovement(
            product_id=p2,
            opening_qty=Decimal("100"),
            inbound_qty=Decimal("0"),
            outbound_qty=Decimal("150"),
        ),  # -50
        InventoryMovement(
            product_id=p3,
            opening_qty=Decimal("100"),
            inbound_qty=Decimal("0"),
            outbound_qty=Decimal("110"),
        ),  # -10
    ]
    product_map = {
        p1: _ProductStub(product_id=p1, product_code="PRD-0001"),
        p2: _ProductStub(product_id=p2, product_code="PRD-0002"),
        p3: _ProductStub(product_id=p3, product_code="PRD-0003"),
    }
    warnings = build_inventory_warnings(proj, product_map=product_map)
    assert len(warnings) == 3
    # Most negative first (closing_qty ASC) — PRD-0002 (-50) first
    assert warnings[0].details["closing_qty"] == "-50"
    assert warnings[1].details["closing_qty"] == "-30"
    assert warnings[2].details["closing_qty"] == "-10"


# ── build_operating_rate_warning ─────────────────────────────
def test_build_operating_rate_warning_under_limit() -> None:
    """AC #4: rate < 100 → no warning."""
    result = build_operating_rate_warning(
        operating_rate_pct=Decimal("50.00"),
        total_fte_headcount=Decimal("1.0"),
        standard_monthly_hours=228,
        total_available_hours=Decimal("228"),
        production_required_hours=Decimal("100"),
        period_key="2026-07",
        trace_id="trace-1",
    )
    assert result is None


def test_build_operating_rate_warning_at_limit() -> None:
    """rate = 100% → no warning (PRD §V5 boundary)."""
    result = build_operating_rate_warning(
        operating_rate_pct=Decimal("100.00"),
        total_fte_headcount=Decimal("1.0"),
        standard_monthly_hours=228,
        total_available_hours=Decimal("228"),
        production_required_hours=Decimal("228"),
        period_key="2026-07",
        trace_id="trace-1",
    )
    assert result is None


def test_build_operating_rate_warning_over_limit() -> None:
    """AC #3: rate=110% → 1 warning."""
    w = build_operating_rate_warning(
        operating_rate_pct=Decimal("110.00"),
        total_fte_headcount=Decimal("1.0"),
        standard_monthly_hours=228,
        total_available_hours=Decimal("228"),
        production_required_hours=Decimal("250.8"),
        period_key="2026-07",
        trace_id="trace-1",
    )
    assert w is not None
    assert w.code == "OVERCAPACITY_OPERATING_RATE"
    assert w.severity == "error"
    assert w.stream == "production"
    assert w.details["operating_rate_pct"] == "110.00"


def test_build_operating_rate_warning_ac3_fixture() -> None:
    """AC #3 fixture: 250h / 248.52h → 100.60% (한도 초과)."""
    w = build_operating_rate_warning(
        operating_rate_pct=Decimal("100.60"),
        total_fte_headcount=Decimal("1.09"),
        standard_monthly_hours=228,
        total_available_hours=Decimal("248.52"),
        production_required_hours=Decimal("250"),
        period_key="2026-07",
        trace_id="trace-1",
    )
    assert w is not None
    assert w.code == "OVERCAPACITY_OPERATING_RATE"
    assert w.details["period_key"] == "2026-07"
    assert w.details["operating_rate_pct"] == "100.60"


# ── aggregate_warnings ───────────────────────────────────────
def test_aggregate_warnings_empty() -> None:
    """empty inventory + no overcapacity → []."""
    assert aggregate_warnings([], None) == []


def test_aggregate_warnings_inventory_only() -> None:
    """1 inventory warning → 1 output."""
    pid = uuid.uuid4()
    inv_warnings = [
        Warning(
            code="NEGATIVE_CLOSING_INVENTORY",
            severity="error",
            message_ko="...",
            details={"product_id": str(pid), "closing_qty": "-30"},
            stream="sales",
            trace_id="trace-1",
            timestamp=None,  # type: ignore[arg-type]
        ),
    ]
    result = aggregate_warnings(inv_warnings, None)
    assert len(result) == 1
    assert result[0].code == "NEGATIVE_CLOSING_INVENTORY"


def test_aggregate_warnings_independent_resolution() -> None:
    """AC #5: items 1+2 → clear 1 → item 2 remains."""
    pid1 = uuid.uuid4()
    pid2 = uuid.uuid4()
    inv_warnings = [
        Warning(
            code="NEGATIVE_CLOSING_INVENTORY",
            severity="error",
            message_ko="w1",
            details={"product_id": str(pid1), "closing_qty": "-30"},
            stream="sales",
            trace_id="trace-1",
            timestamp=None,  # type: ignore[arg-type]
        ),
        Warning(
            code="NEGATIVE_CLOSING_INVENTORY",
            severity="error",
            message_ko="w2",
            details={"product_id": str(pid2), "closing_qty": "-50"},
            stream="sales",
            trace_id="trace-1",
            timestamp=None,  # type: ignore[arg-type]
        ),
    ]
    # Clear inv warning 1: only pid2 remains (-50)
    cleared = inv_warnings[1:]
    result = aggregate_warnings(cleared, None)
    assert len(result) == 1
    assert result[0].details["product_id"] == str(pid2)
    assert result[0].details["closing_qty"] == "-50"


def test_aggregate_warnings_combined_inventory_and_overcapacity() -> None:
    """AC #5: both inventory + overcapacity → 2 warnings."""
    pid = uuid.uuid4()
    inv_warnings = [
        Warning(
            code="NEGATIVE_CLOSING_INVENTORY",
            severity="error",
            message_ko="inv",
            details={"product_id": str(pid), "closing_qty": "-30"},
            stream="sales",
            trace_id="trace-1",
            timestamp=None,  # type: ignore[arg-type]
        ),
    ]
    op_w = Warning(
        code="OVERCAPACITY_OPERATING_RATE",
        severity="error",
        message_ko="op",
        details={"operating_rate_pct": "110.00"},
        stream="production",
        trace_id="trace-1",
        timestamp=None,  # type: ignore[arg-type]
    )
    result = aggregate_warnings(inv_warnings, op_w)
    assert len(result) == 2


def test_warnings_sorted_by_severity_and_closing_qty() -> None:
    """AC #8: severity ASC + closing_qty ASC."""
    pid1 = uuid.uuid4()
    pid2 = uuid.uuid4()
    # Mixed severity: 1 warning (error) + 1 warning (warning/info)
    inv_warnings = [
        Warning(
            code="NEGATIVE_CLOSING_INVENTORY",
            severity="error",
            message_ko="err",
            details={"product_id": str(pid1), "closing_qty": "-30"},
            stream="sales",
            trace_id="trace-1",
            timestamp=None,  # type: ignore[arg-type]
        ),
    ]
    op_w = Warning(
        code="OVERCAPACITY_OPERATING_RATE",
        severity="error",
        message_ko="op",
        details={"operating_rate_pct": "110.00"},
        stream="production",
        trace_id="trace-1",
        timestamp=None,  # type: ignore[arg-type]
    )
    result = aggregate_warnings(inv_warnings, op_w)
    # Both error → severity tie → order by inventory vs operating_rate
    # (PRD §A11: error first; same-severity warnings keep input order)
    assert result[0].severity == "error"
    assert result[1].severity == "error"


# ── Korean message format (PRD §V3·V5) ──────────────────────
def test_korean_message_format_inventory() -> None:
    """PRD §V3 friendly: 'PRD-0001(달걀) 기말재고 -30 → 음수 경고'."""
    pid = uuid.uuid4()
    product = _ProductStub(product_id=pid, product_code="PRD-0001", name_ko="달걀")
    proj = [
        InventoryMovement(
            product_id=pid,
            opening_qty=Decimal("100"),
            inbound_qty=Decimal("0"),
            outbound_qty=Decimal("130"),
        ),
    ]
    msg = format_inventory_warning_ko(product, proj[0])
    assert msg == "PRD-0001(달걀) 기말재고 -30 → 음수 경고"


def test_korean_message_format_operating_rate() -> None:
    """PRD §V5 friendly: '총작업가능시간 248.52h(1.09 × 228) < 생산요구시간 250h → 100.6% (한도 초과)'."""
    msg = format_operating_rate_ko(
        total_fte_headcount=Decimal("1.09"),
        standard_monthly_hours=228,
        total_available_hours=Decimal("248.52"),
        production_required_hours=Decimal("250"),
        operating_rate_pct=Decimal("100.60"),
    )
    assert "248.52" in msg
    assert "1.09" in msg
    assert "228" in msg
    assert "250" in msg
    # Trailing zeros stripped (AC #3 spec literal: '100.6%')
    assert "100.6" in msg
    assert "한도 초과" in msg


def test_korean_message_format_inventory_no_name() -> None:
    """product.name_ko='' → fallback to code only."""
    pid = uuid.uuid4()
    product = _ProductStub(product_id=pid, product_code="PRD-0001", name_ko="")
    proj = [
        InventoryMovement(
            product_id=pid,
            opening_qty=Decimal("100"),
            inbound_qty=Decimal("0"),
            outbound_qty=Decimal("130"),
        ),
    ]
    msg = format_inventory_warning_ko(product, proj[0])
    assert "PRD-0001" in msg
    assert "기말재고 -30" in msg


# ── Service-only tenant (AC #6) ─────────────────────────────
def test_service_only_tenant_no_inventory_warning() -> None:
    """AC #6: service products → projection empty → 0 warnings."""
    pid_svc = uuid.uuid4()
    # Only service rows → excluded from projection
    rows = [
        _RowStub_factory(stream="sales", pid=pid_svc, qty=Decimal("10"), ptype="service"),
    ]
    from packages.services.m2_input.inventory_projection import build_inventory_projection

    projection = build_inventory_projection(rows, opening_balance=None)
    # Service product is excluded → projection empty
    assert projection == []
    # Empty projection → 0 warnings
    warnings = build_inventory_warnings(projection)
    assert warnings == []


def _RowStub_factory(stream, pid, qty, ptype):
    from tests.services.test_m2_input_inventory_projection import _RowStub

    return _RowStub(stream=stream, product_id=pid, qty=qty, product_type=ptype)


# ── immediate disappear pattern (AC #2) ─────────────────────
def test_warning_aggregate_immediate_disappear() -> None:
    """AC #2: clear warning → state.warnings = []."""
    pid = uuid.uuid4()
    # Frame: closing_qty = -30 → 1 warning
    proj = [
        InventoryMovement(
            product_id=pid,
            opening_qty=Decimal("100"),
            inbound_qty=Decimal("0"),
            outbound_qty=Decimal("130"),
        ),
    ]
    product_map = {
        pid: _ProductStub(product_id=pid, product_code="PRD-0001", name_ko="달걀"),
    }
    warnings = build_inventory_warnings(proj, product_map=product_map)
    assert len(warnings) == 1

    # Fix: closing_qty = 20 (positive) → 0 warnings
    proj_fixed = [
        InventoryMovement(
            product_id=pid,
            opening_qty=Decimal("100"),
            inbound_qty=Decimal("0"),
            outbound_qty=Decimal("80"),
        ),
    ]
    warnings_fixed = build_inventory_warnings(proj_fixed, product_map=product_map)
    assert warnings_fixed == []
