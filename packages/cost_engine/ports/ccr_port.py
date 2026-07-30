"""packages.cost_engine.ports.ccr_port — TDABC Capacity Cost Rate port (AD-21).

AD-21: Single CCR definition.
  CCR = department_indirect_cost / practical_capacity_hours
  CCR is computed in 1원 units. Unused capacity is reported separately.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from packages.cost_engine.core.money import KRW


@dataclass(frozen=True)
class CCRResult:
    """Capacity Cost Rate calculation result."""

    tenant_id: UUID
    period_key: str
    department_id: UUID
    ccr_per_hour: KRW  # 1원 precision
    practical_capacity_hours: Decimal
    unused_capacity_hours: Decimal
    unused_capacity_cost: KRW


class CCRPort(Protocol):
    """The single owner of CCR computation (AD-21). M3 calls this; never recomputes."""

    def compute(self, tenant_id: UUID, period_key: str, department_id: UUID) -> CCRResult: ...
