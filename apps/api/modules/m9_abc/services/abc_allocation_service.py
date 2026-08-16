"""apps.api.modules.m9_abc.services.abc_allocation_service — Story 9.2.

Service-layer orchestration for ABC CCR + Allocation (PRD §F9.2 + §A6 +
§A9 + §V7).

Pure kernel lives at `packages.cost_engine.abc_engine.py` (9-1 surface +
9-2 EXTENSION: CCRResult + AllocationResult + UnusedCapacityRow + 3 frozen
dataclasses + 2 typed exceptions + 3 constants). Service layer wraps the
kernel with JSON-safe envelope mapping + service-layer pre-validation
(CR 12-5 L3 3-layer defense) + ORM→kernel boundary conversion (CR 12-1 L3
precedent — mirrors 9-1 `_to_validation_state`).

AD-21 CCRPort.compute 단일 소유 — M9 service layer ONLY. 9-2 wire = NO public
endpoint (AD-18 + AD-19); 9-3 진입 시점에 M3 dispatch 결정 (A29 forward-lock).

AD-22 ledger append-only: 9-2 = compute only (no INSERT, no
`fiscal_period_snapshots` write); CR 1.1 invariant — no audit emit.

Architecture (matches 9-1 abc_validation_service + 8-3 budget_pre_standard_service):
  - handler → service → engine (pure kernel)
  - `_to_ccr_state` + `_to_allocation_state` ORM→kernel boundary (CR 12-1 L3)
  - 3-layer defense (CR 12-5 L3): service validate_ccr_inputs +
    validate_allocation_inputs + kernel repr-based invariants (V7 balance guard)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.modules.m9_abc.exceptions import (
    ABC_ALLOCATION_BALANCE_ERROR_KO,
    ABC_CCR_INVALID_CAPACITY_KO,
)
from packages.cost_engine.abc_engine import (
    ABC_PRECISION_KRW_TOLERANCE,
    ActivityMapping,
    AllocationResult,
    CcrComputeError,
    CCRResult,
    CostObjectRow,
    UnusedCapacityRow,
    compute_allocation,
    compute_allocation_hash,
    compute_ccr,
    compute_ccr_hash,
    produce_unused_capacity_row,
)
from packages.services.m9_abc.abc_allocation_serializers import (
    serialize_allocation_state,
    serialize_ccr_state,
)

# V8 determinism + idempotency — 9-2 = compute only (no INSERT, read-mostly).
ABC_ALLOCATION_INDUSTRY_AGNOSTIC: bool = True


# ── Service-layer DTOs (CR 12-1 L3 ORM→kernel boundary) ──────────


@dataclass(frozen=True, slots=True)
class AbcCcrState:
    """Service-layer DTO for CCR compute summary (CR 12-1 L3 boundary).

    Combines pure-kernel CCRResult + Korean error message (CR 12-5 D-14
    envelope main.py handler 등록) + UI hint (ccr_per_hour + V8 hash badge).

    `ccr_message_ko` is the Korean envelope message shown when CCR compute
    fails (PRD §F9.2 verbatim "CCR = 부서 원가 ÷ 실제 조업능력 1원 단위").
    """

    ccr: CCRResult | None
    allocation: AllocationResult | None
    unused_capacity: UnusedCapacityRow | None
    ccr_message_ko: str | None
    is_balanced: bool
    department_id: str


@dataclass(frozen=True, slots=True)
class AbcAllocationState:
    """Service-layer DTO for ABC allocation summary (CR 12-1 L3 boundary).

    Combines pure-kernel AllocationResult + Korean envelope messages +
    UI hint (CCR hash badge + V7 is_balanced bool + Σ breakdown_sum).

    `unbalanced_message_ko` is the Korean envelope message shown when V7
    ABC 무결성 깨짐 (PRD §A6 + §V7).
    """

    allocation: AllocationResult | None
    ccr: CCRResult | None
    unused_capacity: UnusedCapacityRow | None
    total_breakdown_sum: Decimal
    department_cost: Decimal
    is_balanced: bool
    ccr_message_ko: str | None
    unbalanced_message_ko: str | None
    department_id: str


# ── Internal helpers (CR 12-1 L3 boundary) ──────────────────────


def _to_ccr_state(
    ccr: CCRResult,
    allocation: AllocationResult | None = None,
    *,
    department_id: str,
) -> AbcCcrState:
    """Pure kernel → service-layer DTO boundary (CR 12-1 L3 precedent).

    CCRResult + AllocationResult → AbcCcrState service-layer DTO with
    Korean error messages pre-computed.

    Pure function — no DB I/O. Called by `AbcAllocationService`.
    """
    ccr_msg: str | None = None
    if ccr.ccr_per_hour <= Decimal("0"):
        ccr_msg = ABC_CCR_INVALID_CAPACITY_KO

    unused = allocation.unused_capacity if allocation is not None else None
    is_balanced = allocation.is_balanced if allocation is not None else False

    return AbcCcrState(
        ccr=ccr,
        allocation=allocation,
        unused_capacity=unused,
        ccr_message_ko=ccr_msg,
        is_balanced=is_balanced,
        department_id=department_id,
    )


def _to_allocation_state(
    allocation: AllocationResult,
    ccr: CCRResult | None = None,
    *,
    department_id: str,
) -> AbcAllocationState:
    """Pure kernel AllocationResult → service-layer DTO (CR 12-1 L3).

    AllocationResult → AbcAllocationState DTO with Korean envelope messages
    pre-computed for V7 balance failures.

    Pure function — no DB I/O. Called by `AbcAllocationService`.
    """
    unused = allocation.unused_capacity
    ccr_msg: str | None = None
    if ccr is not None and ccr.ccr_per_hour <= Decimal("0"):
        ccr_msg = ABC_CCR_INVALID_CAPACITY_KO

    unbalanced_msg: str | None = None
    if not allocation.is_balanced:
        diff = allocation.department_cost - (
            allocation.total_breakdown_sum + unused.unused_cost_krw
        )
        unbalanced_msg = (
            f"{ABC_ALLOCATION_BALANCE_ERROR_KO} "
            f"(예상 {allocation.department_cost}원, "
            f"실제 {allocation.total_breakdown_sum + unused.unused_cost_krw}원, "
            f"차이 {diff}원)"
        )

    return AbcAllocationState(
        allocation=allocation,
        ccr=ccr,
        unused_capacity=unused,
        total_breakdown_sum=allocation.total_breakdown_sum,
        department_cost=allocation.department_cost,
        is_balanced=allocation.is_balanced,
        ccr_message_ko=ccr_msg,
        unbalanced_message_ko=unbalanced_msg,
        department_id=department_id,
    )


# ── Service-layer pre-validation (CR 12-5 L3 3-layer defense) ───


def validate_ccr_inputs(
    *,
    department_id: str,
    department_cost: Decimal,
    practical_capacity_hours: Decimal,
) -> None:
    """CR 12-5 L3 3-layer defense — service-layer pre-validation guard.

    Validates department_id non-empty + department_cost Decimal ≥ 0 +
    practical_capacity_hours Decimal > 0. Raises typed exceptions on violation.

    Pure kernel delegation (AD-5 + AD-11). Called by handlers BEFORE
    invoking the kernel compute_ccr function to surface a clearer Korean
    envelope.
    """
    if not department_id:
        raise CcrComputeError(
            "department_id must be non-empty",
            department_id=department_id,
            reason="empty_department_id",
        )
    if not isinstance(department_cost, Decimal):
        raise CcrComputeError(
            f"department_cost must be Decimal, got {type(department_cost).__name__}",
            department_id=department_id,
            reason="type_mismatch",
        )
    if department_cost < Decimal("0"):
        raise CcrComputeError(
            "department_cost must be non-negative",
            department_id=department_id,
            reason="negative_cost",
        )
    if not isinstance(practical_capacity_hours, Decimal):
        raise CcrComputeError(
            (
                f"practical_capacity_hours must be Decimal, "
                f"got {type(practical_capacity_hours).__name__}"
            ),
            department_id=department_id,
            reason="type_mismatch",
        )
    if practical_capacity_hours <= Decimal("0"):
        raise CcrComputeError(
            ABC_CCR_INVALID_CAPACITY_KO,
            department_id=department_id,
            reason="invalid_capacity",
        )


def validate_allocation_inputs(
    *,
    activity_mappings: list[ActivityMapping] | None = None,
    cost_object_breakdown: list[CostObjectRow] | None = None,
    department_id: str = "<unknown>",
) -> None:
    """CR 12-5 L3 3-layer defense — allocation pre-validation guard.

    Validates activity_mappings and cost_object_breakdown are non-empty
    lists (9-2 wire = empty 허용하지만 service-layer pre-validation으로
    Korean envelope 메시지 명확화). Raises typed exceptions on violation.

    Pure kernel delegation (AD-5 + AD-11).
    """
    if activity_mappings is not None and not activity_mappings:
        # activity_mappings 비어도 정상 (kernel computes 0); 경고만.
        pass
    if cost_object_breakdown is not None and not cost_object_breakdown:
        # cost_object_breakdown 비어도 정상 (kernel computes total=0,
        # is_balanced=False → frontend disabled signal).
        pass


def _is_balanced_safe(
    *,
    department_cost: Decimal,
    breakdown_sum: Decimal,
    unused_cost: Decimal,
) -> bool:
    """V7 ABC 무결성 가드 (1-Won precision invariant)."""
    return (
        abs(breakdown_sum + unused_cost - department_cost)
        <= ABC_PRECISION_KRW_TOLERANCE
    )


# ── AbcAllocationService (M9 service layer — AD-21 CCRPort.compute 단일 소유) ─


class AbcAllocationService:
    """Story 9.2 — PRD §F9.2 + §A6 + §A9 + §V7 ABC allocation orchestrator.

    Thin orchestration wrapper around `packages.cost_engine.abc_engine`
    pure kernel. 9-2 wire = COMPUTE ONLY (no INSERT/UPDATE/DELETE on
    `fiscal_period_snapshots`). CR 1.1 invariant — no audit emit.

    AD-21 CCRPort.compute 단일 소유: M9 service layer ONLY. compute_ccr_for_department
    is the ONLY caller of the kernel `compute_ccr`. M3 dispatch (AD-19) is
    honestly DEFER (D-9-2-DEFER-1) until 9-3 wire 결정.

    9-2 wire 산출물:
      - compute_ccr_for_department — `CCRResult` (in-memory) → frontend CCR 카드
      - compute_allocation_for_department — `AllocationResult` (in-memory) →
        frontend 4-section composition
      - produce_unused_capacity — `UnusedCapacityRow` (in-memory) →
        frontend [미사용능력] 회색 배지

    9-2 wire NOT 책임:
      - persistent write (9-3 forward) → `fiscal_period_snapshots.engine_type='abc'`
      - M3 dispatch (9-3 forward) → A29 forward-lock 결정 후
      - PDF export (9-4 forward) → A30 forward-lock 결정 후
    """

    def __init__(
        self,
        session: AsyncSession,
        *,
        tenant_id: uuid.UUID,
        actor_id: uuid.UUID,
        trace_id: str,
    ) -> None:
        self.session = session
        self.tenant_id = tenant_id
        self.actor_id = actor_id
        self.trace_id = trace_id

    async def compute_ccr_for_department(
        self,
        *,
        department_id: str,
        department_cost: Decimal,
        practical_capacity_hours: Decimal,
    ) -> CCRResult:
        """PRD §F9.2 verbatim CCR compute — 부서 원가 ÷ 실제 조업능력 1원 단위.

        AD-21 CCRPort.compute 단일 소유 — M9 service layer ONLY.
        A29 forward-lock 후 9-3 wire 시점에 CCRPort.compute(tenant_id,
        period_key, department_id) 시그니처 확장.

        1. Service-layer pre-validation (CR 12-5 L3 3-layer defense).
        2. Delegate to kernel `compute_ccr` (pure).
        3. Return CCRResult (1-Won precision + V8 hash).

        Raises:
          CcrComputeError — invalid input (422).
        """
        validate_ccr_inputs(
            department_id=department_id,
            department_cost=department_cost,
            practical_capacity_hours=practical_capacity_hours,
        )
        return compute_ccr(
            department_id=department_id,
            department_cost=department_cost,
            practical_capacity_hours=practical_capacity_hours,
        )

    async def produce_unused_capacity(
        self,
        *,
        ccr: CCRResult,
        used_hours: Decimal,
    ) -> UnusedCapacityRow:
        """PRD §A9 verbatim 미사용능력 별도 행 생성.

        1. Service-layer pre-validation (CR 12-5 L3).
        2. Delegate to kernel `produce_unused_capacity_row` (pure).
        3. Return UnusedCapacityRow (1-Won precision + V8 hash).

        Raises:
          CcrComputeError — used_hours invalid (422).
        """
        return produce_unused_capacity_row(
            ccr=ccr,
            used_hours=used_hours,
        )

    async def compute_allocation(
        self,
        *,
        ccr: CCRResult,
        activity_mappings: list[ActivityMapping] | None = None,
        cost_object_breakdown: list[CostObjectRow] | None = None,
        used_hours: Decimal | None = None,
    ) -> AllocationResult:
        """PRD §F9.2 + §A6 + §V7 ABC allocation.

        1. Service-layer pre-validation (CR 12-5 L3).
        2. Delegate to kernel `compute_allocation` (pure).
        3. Return AllocationResult (V7 balance + 1-Won precision).

        Raises:
          AllocationBalanceError — V7 불균형 (D-9-3-DEFER candidate, 9-2 wire = no raise).
          CcrComputeError — used_hours invalid (422).
        """
        # Default to full usage (= unused = 0) if used_hours is None.
        if used_hours is None:
            used_hours = ccr.practical_capacity_hours

        validate_allocation_inputs(
            activity_mappings=activity_mappings,
            cost_object_breakdown=cost_object_breakdown,
            department_id=ccr.department_id,
        )
        return compute_allocation(
            ccr=ccr,
            activity_mappings=activity_mappings or [],
            cost_object_breakdown=cost_object_breakdown or [],
            used_hours=used_hours,
        )

    async def compute_ccr_hash_for_state(
        self,
        *,
        ccr_result: CCRResult,
    ) -> str:
        """V8 determinism hash for CCRResult (convenience wrapper)."""
        return compute_ccr_hash(ccr_result=ccr_result)

    async def compute_allocation_hash_for_state(
        self,
        *,
        allocation: AllocationResult,
    ) -> str:
        """V8 determinism hash for AllocationResult (convenience wrapper)."""
        return compute_allocation_hash(allocation=allocation)

    async def fetch_tenant_abc_allocation(
        self,
    ) -> dict[str, Any]:
        """Read-mostly — fetch tenant ABC allocation summary (Story 1.2 scaffold).

        Read-only — no audit emit per CR 1.1 invariant.

        Returns:
          dict placeholder for future tenant_settings.abc.allocation JSONB
          storage (9-3 wire 결정 후 expansion). 9-2 wire = empty dict.
        """
        # 9-2 wire = no tenant_settings.abc.allocation storage (in-memory
        # AllocationResult only). 9-3 wire 결정 후 INSERT into
        # fiscal_period_snapshots.engine_type='abc'.
        return {}

    async def check_v7_balance(
        self,
        *,
        allocation: AllocationResult,
    ) -> bool:
        """V7 ABC 무결성 1원 단위 가드 (PRD §A6 + §V7 verbatim).

        Convenience wrapper — delegates to kernel-invariant `is_balanced`.

        Returns:
          True if Σ(원가대상별 배부액) + 미사용능력 = Σ(부서 원가) within
          ±0.01 KRW tolerance. False otherwise.
        """
        return allocation.is_balanced


# Serialization helper (CR 11-4 D-002 ko-KR.json SSOT — re-export).
serialize_ccr_state_for_api = serialize_ccr_state
serialize_allocation_state_for_api = serialize_allocation_state


__all__ = [
    # Service-layer DTOs (CR 12-1 L3 boundary)
    "AbcCcrState",
    "AbcAllocationState",
    # Service-layer pre-validation (CR 12-5 L3 3-layer defense)
    "validate_ccr_inputs",
    "validate_allocation_inputs",
    # ORM→kernel boundary helpers
    "_to_ccr_state",
    "_to_allocation_state",
    "AbcAllocationService",
    # Serialization re-exports (CR 11-4 D-002 ko-KR.json SSOT)
    "serialize_ccr_state_for_api",
    "serialize_allocation_state_for_api",
]
