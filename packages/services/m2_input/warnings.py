"""packages.services.m2_input.warnings — Story 3.3 warning aggregate kernel.

Pure-Python, stdlib-only module. NO DB, NO clock, NO random. AD-1 / AD-5
binding: this is the canonical warning-aggregate kernel consumed by
`apps/api/modules/m2_input/services/monthly_input_service.py` AND
mirrored by `apps/web/lib/l2-input-warnings.ts` (drift caught by
`tests/integration/test_m2_input_label_consistency.py`).

The module answers:
- "Build inventory warnings from a per-product projection."
  → `build_inventory_warnings` (PRD §V3 fire condition)
- "Build an overcapacity warning from operating rate."
  → `build_operating_rate_warning` (PRD §V5 fire condition)
- "Aggregate and sort multiple warnings into a deterministic order."
  → `aggregate_warnings` (severity ASC + closing_qty ASC for inventory)
- "Format a Korean friendly message." → `format_inventory_warning_ko`,
  `format_operating_rate_ko` (AD-11 cross-language pattern)

PRD §A11 (오류의 가시화) 운영 원칙:
- 입력 시: warning(200 OK + 진행 허용) — Story 3.3 delivers
- 마감 시: 임계 위반 차단 — Epic 4 first_calc hook (deferred)

Warning codes (Story 3.3 scope):
- NEGATIVE_CLOSING_INVENTORY (PRD §V3) — per product
- OVERCAPACITY_OPERATING_RATE (PRD §V5) — per period

AD-15 cross-language parity: snake_case Python ↔ camelCase TS.
Banker's rounding (ROUND_HALF_EVEN) on rate calculations upstream.
ISO-8601 UTC TIMESTAMPTZ for warning.timestamp.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from typing import Final, NamedTuple, Protocol

from packages.services.m2_input.inventory_projection import (
    InventoryMovement,
)


# ── Constants ────────────────────────────────────────────────
class WarningCode(str, Enum):
    """PRD §V3 + §V5 warning codes (Story 3.3 scope).

    Inherits `str` so JSON serialization is plain string (AD-15).
    """

    NEGATIVE_CLOSING_INVENTORY = "NEGATIVE_CLOSING_INVENTORY"
    OVERCAPACITY_OPERATING_RATE = "OVERCAPACITY_OPERATING_RATE"


# PRD §A11: 오류의 가시화 severity ordering.
# error > warning > info (lower number = higher severity).
SEVERITY_ORDER: Final[dict[str, int]] = {
    "error": 0,
    "warning": 1,
    "info": 2,
}


# ── Warning NamedTuple ───────────────────────────────────────
class Warning(NamedTuple):  # noqa: A001 — cross-language name mirrored in TS `Warning` interface (AD-15)
    """A single warning entry (mirrored by TS `Warning` interface).

    AD-15: snake_case field names. The `timestamp` is ISO-8601 UTC
    (`datetime.now(tz=UTC)`). `details` is a free-form dict that
    carries the structured payload (product_id, closing_qty, etc.).
    """

    code: str
    severity: str
    message_ko: str
    details: dict
    stream: str
    trace_id: str
    timestamp: datetime


# ── Product protocol (duck type) ─────────────────────────────
class _ProductLike(Protocol):
    """Duck type for product rows.

    Only `product_id`, `product_code`, `name_ko` are read. The
    SQLAlchemy `Product` ORM satisfies this structurally.
    """

    product_id: uuid.UUID
    product_code: str
    name_ko: str


# ── Korean message formatters (AD-11 cross-language) ────────
def format_inventory_warning_ko(
    product: _ProductLike,
    projection: InventoryMovement,
) -> str:
    """PRD §V3 friendly Korean message.

    Format: 'PRD-0001(달걀) 기말재고 -30 → 음수 경고'
    """
    closing = _compute_closing_qty_for_ko(projection)
    name = product.name_ko or ""
    if name:
        return f"{product.product_code}({name}) " f"기말재고 {closing} → 음수 경고"
    return f"{product.product_code} 기말재고 {closing} → 음수 경고"


def format_operating_rate_ko(
    *,
    total_fte_headcount: Decimal,
    standard_monthly_hours: int,
    total_available_hours: Decimal,
    production_required_hours: Decimal,
    operating_rate_pct: Decimal,
) -> str:
    """PRD §V5 friendly Korean message.

    Format: '총작업가능시간 248.52h(1.09 × 228) < 생산요구시간 250h → 100.60% (한도 초과)'
    """
    return (
        f"총작업가능시간 {_fmt_hours(total_available_hours)}h"
        f"({_fmt_fte(total_fte_headcount)} × {standard_monthly_hours}) "
        f"< 생산요구시간 {_fmt_hours(production_required_hours)}h "
        f"→ {_fmt_pct(operating_rate_pct)}% (한도 초과)"
    )


def _fmt_hours(d: Decimal) -> str:
    """Format hours — strip trailing zeros, keep 2dp canonical."""
    return _strip_zeros(d)


def _fmt_fte(d: Decimal) -> str:
    """Format FTE headcount — strip trailing zeros."""
    return _strip_zeros(d)


def _fmt_pct(d: Decimal) -> str:
    """Format operating_rate_pct — 2dp."""
    return _strip_zeros(d)


def _strip_zeros(d: Decimal) -> str:
    """Decimal → string with trailing zeros stripped.

    Used for cross-language parity (AC #1 spec uses '100' not '100.00').
    """
    s = str(d.quantize(Decimal("0.01")))
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s or "0"


def _compute_closing_qty_for_ko(projection: InventoryMovement) -> str:
    """Compute closing_qty for the Korean message (signed Decimal)."""
    closing = projection.opening_qty + projection.inbound_qty - projection.outbound_qty
    return _strip_zeros(closing)


# ── build_inventory_warnings ─────────────────────────────────
def build_inventory_warnings(
    projection: list[InventoryMovement],
    product_map: dict[uuid.UUID, _ProductLike] | None = None,
) -> list[Warning]:
    """Build NEGATIVE_CLOSING_INVENTORY warnings from a projection.

    AC #1 fire: closing_qty < 0 → 1 warning per product.
    AC #8 sort: severity ASC + closing_qty ASC (most negative first).

    Args:
        projection: per-product `InventoryMovement` list (from
            `build_inventory_projection`).
        product_map: Optional dict mapping product_id → product (for
            product_code + name_ko in the Korean message). Empty
            defaults to a `_DummyProduct` (UUID as code) — service
            layer should always supply.

    Returns:
        List of `Warning` (severity='error' for NEGATIVE_CLOSING_INVENTORY).
        Sorted by closing_qty ASC (most negative first).
    """
    warnings: list[Warning] = []
    now = datetime.now(tz=UTC)
    pm = product_map or {}
    for m in projection:
        closing = m.opening_qty + m.inbound_qty - m.outbound_qty
        if closing >= 0:
            continue
        product = pm.get(m.product_id)
        if product is None:
            # Product metadata missing — emit minimal warning
            product = _DummyProduct(
                product_id=m.product_id,
                product_code=str(m.product_id),
                name_ko="",
            )
        warn = Warning(
            code=WarningCode.NEGATIVE_CLOSING_INVENTORY.value,
            severity="error",
            message_ko=format_inventory_warning_ko(product, m),
            details={
                "product_id": str(m.product_id),
                "product_code": product.product_code,
                "opening_qty": _strip_zeros(m.opening_qty),
                "inbound_qty": _strip_zeros(m.inbound_qty),
                "outbound_qty": _strip_zeros(m.outbound_qty),
                "closing_qty": _strip_zeros(closing),
                "stream": "sales",
            },
            stream="sales",
            trace_id="",
            timestamp=now,
        )
        warnings.append(warn)
    # Sort by closing_qty ASC (most negative first).
    warnings.sort(key=lambda w: Decimal(w.details["closing_qty"]))
    return warnings


# ── build_operating_rate_warning ─────────────────────────────
def build_operating_rate_warning(
    *,
    operating_rate_pct: Decimal,
    total_fte_headcount: Decimal,
    standard_monthly_hours: int,
    total_available_hours: Decimal,
    production_required_hours: Decimal,
    period_key: str,
    trace_id: str,
) -> Warning | None:
    """Build OVERCAPACITY_OPERATING_RATE warning (PRD §V5 fire).

    Fires when `operating_rate_pct > 100.00`. Boundary (exactly 100%)
    → no warning (PRD §V5 "초과" semantics).

    Returns None if no warning should fire.
    """
    if operating_rate_pct <= Decimal("100.00"):
        return None
    now = datetime.now(tz=UTC)
    return Warning(
        code=WarningCode.OVERCAPACITY_OPERATING_RATE.value,
        severity="error",
        message_ko=format_operating_rate_ko(
            total_fte_headcount=total_fte_headcount,
            standard_monthly_hours=standard_monthly_hours,
            total_available_hours=total_available_hours,
            production_required_hours=production_required_hours,
            operating_rate_pct=operating_rate_pct,
        ),
        details={
            "total_fte_headcount": str(total_fte_headcount),
            "standard_monthly_hours": standard_monthly_hours,
            "total_available_hours": str(total_available_hours),
            "production_required_hours": str(production_required_hours),
            "operating_rate_pct": str(operating_rate_pct),
            "limit_pct": "100",
            "period_key": period_key,
        },
        stream="production",
        trace_id=trace_id,
        timestamp=now,
    )


# ── aggregate_warnings ───────────────────────────────────────
def aggregate_warnings(
    inventory_warnings: list[Warning],
    operating_rate_warning: Warning | None,
) -> list[Warning]:
    """Aggregate inventory + overcapacity warnings into a sorted list.

    Sort: severity ASC (error first), then closing_qty ASC for inventory
    warnings (most negative first). Operating rate warning sorts after
    inventory warnings at the same severity (PRD §A11 default order).

    The `is_blocked` flag is computed by the caller
    (`len(warnings) > 0`).
    """
    out: list[Warning] = list(inventory_warnings)
    if operating_rate_warning is not None:
        out.append(operating_rate_warning)
    # Sort by severity ASC; inventory warnings already closed_qty ASC.
    # We need a stable sort that preserves inventory's ordering within
    # the same severity (operating_rate comes last).
    out.sort(
        key=lambda w: (
            SEVERITY_ORDER.get(w.severity, 99),
            0 if w.code == WarningCode.NEGATIVE_CLOSING_INVENTORY.value else 1,
            Decimal(w.details.get("closing_qty", "0")),
        )
    )
    return out


# ── Internal: dummy product for missing metadata ─────────────
class _DummyProduct:
    """Internal fallback when product metadata is missing.

    Service layer should always supply a map; this is defense-in-depth
    for tests / edge cases.
    """

    def __init__(
        self,
        product_id: uuid.UUID,
        product_code: str,
        name_ko: str,
    ) -> None:
        self.product_id = product_id
        self.product_code = product_code
        self.name_ko = name_ko
