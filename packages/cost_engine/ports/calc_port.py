"""packages.cost_engine.ports.calc_port — calculation entry point protocol.

AD-19: One calculation entry point and owner. The single POST /api/v1/calc endpoint
dispatches this port for traditional costing and (Epic 9) M9 ABC costing.

AD-4:  The implementer MUST run inside a REPEATABLE READ transaction.
AD-5:  The CORE of this port is a pure function. Adapters wire I/O around it.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from packages.cost_engine.core.money import KRW


@dataclass(frozen=True)
class MonthlyInput:
    """Pure input value object — no DB, no clock."""

    tenant_id: UUID
    period_key: str  # YYYY-MM (AD-24)
    direct_material_krw: KRW
    direct_labor_krw: KRW
    indirect_krw: KRW
    fte_headcount: Decimal  # FTE 환산 (Story 3.2)


@dataclass(frozen=True)
class CalcResult:
    """Pure output value object — deterministic hash for V8 regression."""

    tenant_id: UUID
    period_key: str
    material_cost: KRW
    labor_cost: KRW
    overhead_cost: KRW
    manufacturing_cost: KRW
    inventory_adjustment: KRW
    result_hash: str  # deterministic, AD-16
    state: str  # draft | verified | committed | reversed (AD-20)


class CalcPort(Protocol):
    """The single port for cost calculation. Implemented by the engine core."""

    def compute_period_cost(self, monthly_input: MonthlyInput) -> CalcResult:
        """Pure compute. Same input → same output (AD-5, AD-16)."""
        ...
