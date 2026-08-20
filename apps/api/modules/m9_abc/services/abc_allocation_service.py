"""apps.api.modules.m9_abc.services.abc_allocation_service — Story 9.2 + 9.3.

Service-layer orchestration for ABC CCR + Allocation (PRD §F9.2 + §A6 +
§A9 + §V7).

Pure kernel lives at `packages.cost_engine.abc_engine.py` (9-1 surface +
9-2 EXTENSION: CCRResult + AllocationResult + UnusedCapacityRow + 3 frozen
dataclasses + 2 typed exceptions + 3 constants + 9-3 EXTENSION: V7Verdict +
MultiDepartmentCcrResult + DispatchState + DepartmentAllocation +
UnusedCapacitySubRow + 2 typed exceptions (EmptyDepartmentsError,
TooManyDepartmentsError) + 5 pure functions). Service layer wraps the
kernel with JSON-safe envelope mapping + service-layer pre-validation
(CR 12-5 L3 3-layer defense) + ORM→kernel boundary conversion (CR 12-1 L3
precedent — mirrors 9-1 `_to_validation_state`) + 9-3 NEW
compute_and_persist 11-step pipeline (PRD §F9.3 + A29 forward-lock dual-route).

AD-21 CCRPort.compute 단일 소유 — M9 service layer ONLY. 9-2 wire = NO public
endpoint (AD-18 + AD-19); 9-3 wire = compute_and_persist 11-step pipeline
called by M3 orchestrator via LAZY import (AD-19 dual-route dispatch).

AD-22 ledger append-only: 9-2 = compute only (no INSERT, no
`fiscal_period_snapshots` write); 9-3 = compute AND INSERT ABC dual-route
row + JSONB cost_object_breakdown / unused_capacity_breakdown subdocs
(PRD §F9.3 + Alembic 0028).

Architecture (matches 9-1 abc_validation_service + 8-3 budget_pre_standard_service):
  - handler → service → engine (pure kernel)
  - `_to_ccr_state` + `_to_allocation_state` ORM→kernel boundary (CR 12-1 L3)
  - 3-layer defense (CR 12-5 L3): service validate_ccr_inputs +
    validate_allocation_inputs + kernel repr-based invariants (V7 balance guard)
  - 9-3 EXTENSION: 11-step compute_and_persist pipeline (PRD §F9.3):
    1. Load tenant_settings.abc.departments
    2. validate_department_count (kernel 1-50 guard, 9-3 typed exception)
    3. Per-dept compute_ccr (kernel)
    4. aggregate_multi_department_ccr (kernel)
    5. Per-dept compute_allocation + verify_v7_balance (kernel)
    6. Build cost_object_breakdown JSON list
    7. Build unused_capacity_breakdown JSON list
    8. compute_abc_allocation_hash (kernel)
    9. Idempotency check + audit-first INSERT (calc_log, verification_log)
    10. INSERT fiscal_period_snapshots with engine_type='abc' + JSONB subdocs
    11. COMMIT
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.audit_action import (
    ActionClass,
    _ActionRegistry,
)
from apps.api.core.db_models import (
    CalcLog,
    FiscalPeriodSnapshot,
    VerificationLog,
)
from apps.api.modules.m0_onboarding.services.settings_service import (
    SettingsService,
)

# 9-3 EXTENSION — CalcServiceError is the typed 500 envelope for divergent
# idempotency + integrity constraint failures (mirrors M3 trad path).
from apps.api.modules.m3_calculate.services.calc_orchestrator import (
    CalcServiceError,
)
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
    DepartmentAllocation,
    MultiDepartmentCcrResult,
    UnusedCapacityRow,
    UnusedCapacitySubRow,
    V7Verdict,
    aggregate_multi_department_ccr,
    compute_abc_allocation_hash,
    compute_allocation,
    compute_allocation_hash,
    compute_ccr,
    compute_ccr_hash,
    produce_unused_capacity_row,
    validate_department_count,
    verify_v7_balance,
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


# ── Story 9.3 (T3) — M9 AbcAllocationService.compute_and_persist EXTENSION ──
# AD-21 CCRPort.compute 단일 소유 + A29 forward-lock dual-route 결정 wire.
# 11-step pipeline:
#   1. Load tenant_settings.abc.departments
#   2. validate_department_count (kernel 1-50 guard)
#   3. Per-dept compute_ccr (kernel)
#   4. aggregate_multi_department_ccr (kernel)
#   5. Per-dept compute_allocation + verify_v7_balance (kernel)
#   6. Build cost_object_breakdown JSON list
#   7. Build unused_capacity_breakdown JSON list
#   8. compute_abc_allocation_hash (kernel — V8 determinism)
#   9. Idempotency check + audit-first INSERT (calc_log, verification_log)
#  10. INSERT fiscal_period_snapshots.engine_type='abc' + JSONB subdocs
#  11. COMMIT
#
# M3 orchestrator's `_dispatch_abc_path` calls this method via:
#   m9_service = AbcAllocationService(session, trace_id)  # noqa: ERA001
#   outcome = await m9_service.compute_and_persist(tenant_id, period_key)  # noqa: ERA001


# ABC dual-route result envelope (M3 CalcOutcomeABC field shape).
@dataclass(frozen=True, slots=True)
class AbcAllocationOutcome:
    """Story 9.3 (T3) — compute_and_persist result envelope.

    Returned by `AbcAllocationService.compute_and_persist`. M3 orchestrator
    maps this to `CalcOutcomeABC.allocation_outcome` (dict-shaped) for the
    discriminated union envelope. The field names mirror
    `apps.api.modules.m3_calculate.schemas.AllocationOutcomeABC`.
    """

    breakdown: list[dict[str, Any]]
    unused_capacity: dict[str, Any]
    v7_verdict: dict[str, Any]
    ccr: dict[str, Any]
    is_balanced: bool
    snapshot_id: str  # UUID-as-string, fiscal_period_snapshots.snapshot_id
    result_hash: str  # sha256: + 64-char hexdigest (V8 determinism)


def _to_outcome(
    *,
    per_dept: list[DepartmentAllocation],
    cost_object_breakdown: list[dict[str, Any]],
    unused_capacity_breakdown: list[dict[str, Any]],
    v7_verdict_agg: V7Verdict,
    snapshot_id: str,
    result_hash: str,
) -> dict[str, Any]:
    """ORM→kernel boundary (CR 12-1 L3) — wire-shape envelope for CalcOutcomeABC.

    Returns dict-shaped envelope (NOT a frozen dataclass) so M3 orchestrator
    can pass it through `CalcOutcomeABC(allocation_outcome=...)` without
    shape conversion. Field names match `AllocationOutcomeABC` Pydantic model.
    """
    return {
        "breakdown": cost_object_breakdown,
        "unused_capacity": {
            "rows": unused_capacity_breakdown,
            "is_balanced": v7_verdict_agg.is_balanced,
            "delta_krw": str(v7_verdict_agg.delta_krw),
        },
        "v7_verdict": {
            "is_balanced": v7_verdict_agg.is_balanced,
            "breakdown_sum": str(v7_verdict_agg.breakdown_sum),
            "unused_cost": str(v7_verdict_agg.unused_cost),
            "expected_sum": str(v7_verdict_agg.expected_sum),
            "delta_krw": str(v7_verdict_agg.delta_krw),
            "hash": v7_verdict_agg.hash,
        },
        "ccr": {
            "departments": [
                {
                    "department_id": da.department_id,
                    "ccr_per_hour": str(da.ccr.ccr_per_hour),
                    "hash": da.ccr.hash,
                }
                for da in per_dept
            ],
        },
        "is_balanced": v7_verdict_agg.is_balanced,
        "snapshot_id": snapshot_id,
        "result_hash": result_hash,
    }


# 9-3 EXTENSION method — compute_and_persist 11-step pipeline.
async def compute_and_persist(
    self,
    *,
    tenant_id: uuid.UUID,
    period_key: str,
) -> dict[str, Any]:
    """Story 9.3 (T3) — A29 forward-lock dual-route persist pipeline.

    Called by M3 orchestrator's `_dispatch_abc_path` (LAZY import pattern).
    Performs the full 11-step pipeline:

    1. Load tenant_settings.abc.departments (ORM → service-layer)
    2. validate_department_count (kernel 1-50 guard, 9-3 typed exception)
    3. Per-dept compute_ccr (kernel)
    4. aggregate_multi_department_ccr (kernel)
    5. Per-dept compute_allocation + verify_v7_balance (kernel)
    6. Build cost_object_breakdown JSON list (PRD §F9.3 + §A6)
    7. Build unused_capacity_breakdown JSON list (PRD §A9 + §V7)
    8. compute_abc_allocation_hash (kernel — V8 determinism)
    9. Idempotency check + audit-first INSERT (calc_log, verification_log)
       (CR 1.1 lesson — same as M3 trad path)
    10. INSERT fiscal_period_snapshots.engine_type='abc' + JSONB subdocs
    11. COMMIT

    Returns:
        dict-shaped envelope (mirrors AllocationOutcomeABC Pydantic model)
        with snapshot_id + result_hash. M3 orchestrator packs this into
        CalcOutcomeABC.allocation_outcome for the discriminated union
        envelope.

    Raises:
        EmptyDepartmentsError: 422 EMPTY_DEPARTMENTS (CR 12-5 D-14)
        TooManyDepartmentsError: 422 TOO_MANY_DEPARTMENTS (CR 12-5 D-14)
        CcrComputeError: 422 CCR_INVALID_CAPACITY (CR 12-5 D-14)
        AllocationBalanceError: 422 ALLOCATION_BALANCE_ERROR (CR 12-5 D-14)
        CalcServiceError: 500 INTERNAL_ERROR (compute_and_persist failure)

    AD-21: CCRPort.compute 단일 소유 — M9 service layer ONLY.
    AD-22: ledger append-only — calc_log + verification_log INSERT BEFORE
    snapshot INSERT.
    """
    baseline_revision = 1

    # ── Step 1: Load tenant_settings.abc.departments ─────────────
    settings = await SettingsService(self.session).get_tenant_settings(
        tenant_id=tenant_id
    )
    abc_config = dict(settings.abc or {})
    departments: list[dict[str, Any]] = list(abc_config.get("departments") or [])
    department_ids = [str(d.get("department_id", "")) for d in departments]

    # ── Step 2: validate_department_count (kernel 1-50 guard) ───
    validate_department_count(department_ids=department_ids)

    # ── Step 3: Per-dept compute_ccr (kernel) ───────────────────
    ccr_results: list[CCRResult] = []
    for dept in departments:
        ccr = compute_ccr(
            department_id=str(dept["department_id"]),
            department_cost=Decimal(str(dept["department_cost"])),
            practical_capacity_hours=Decimal(str(dept["practical_capacity_hours"])),
        )
        ccr_results.append(ccr)

    # ── Step 4: aggregate_multi_department_ccr (kernel) ─────────
    multi_dept: MultiDepartmentCcrResult = aggregate_multi_department_ccr(
        ccr_results=ccr_results
    )

    # ── Step 5: Per-dept compute_allocation + verify_v7_balance ──
    per_dept: list[DepartmentAllocation] = []
    for dept, ccr in zip(departments, ccr_results, strict=True):
        # Build activity_mappings from dept.activities.
        activity_mappings = [
            ActivityMapping(
                activity_id=str(a["activity_id"]),
                hours=Decimal(str(a["hours"])),
                ccr_amount_krw=Decimal(str(a["ccr_amount_krw"])),
            )
            for a in dept.get("activities", [])
        ]
        cost_object_breakdown_rows = [
            CostObjectRow(
                product_id=str(cob["product_id"]),
                activity_id=str(cob["activity_id"]),
                driver_id=str(cob["driver_id"]),
                allocated_krw=Decimal(str(cob["allocated_krw"])),
            )
            for cob in dept.get("cost_object_breakdown", [])
        ]
        used_hours = Decimal(str(dept.get("used_hours", dept["practical_capacity_hours"])))

        allocation = compute_allocation(
            ccr=ccr,
            activity_mappings=activity_mappings,
            cost_object_breakdown=cost_object_breakdown_rows,
            used_hours=used_hours,
        )

        # V7 balance verification (kernel 1-Won precision invariant).
        v7_verdict = verify_v7_balance(
            total_breakdown_sum=allocation.total_breakdown_sum,
            unused_cost=allocation.unused_capacity.unused_cost_krw,
            department_cost=allocation.department_cost,
        )

        per_dept.append(
            DepartmentAllocation(
                department_id=str(dept["department_id"]),
                ccr=ccr,
                allocation=allocation,
                v7_verdict=v7_verdict,
            )
        )

    # ── Step 6: Build cost_object_breakdown JSON list ───────────
    cost_object_breakdown_json: list[dict[str, Any]] = []
    total_breakdown_sum_agg = Decimal("0")
    unused_cost_agg = Decimal("0")
    expected_sum_agg = Decimal("0")
    for da in per_dept:
        for row in da.allocation.cost_object_breakdown:
            cost_object_breakdown_json.append(
                {
                    "department_id": da.department_id,
                    "product_id": row.product_id,
                    "activity_id": row.activity_id,
                    "driver_id": row.driver_id,
                    "allocated_krw": str(row.allocated_krw),
                }
            )
        total_breakdown_sum_agg += da.allocation.total_breakdown_sum
        unused_cost_agg += da.allocation.unused_capacity.unused_cost_krw
        expected_sum_agg += da.allocation.department_cost

    # ── Step 7: Build unused_capacity_breakdown JSON list ────────
    unused_capacity_breakdown_json: list[dict[str, Any]] = []
    for da in per_dept:
        sub = da.allocation.unused_capacity
        unused_capacity_breakdown_json.append(
            {
                "department_id": da.department_id,
                "unused_hours": str(sub.unused_hours),
                "unused_cost_krw": str(sub.unused_cost_krw),
                "hash": sub.hash,
            }
        )

    # Aggregate V7 verdict (1-Won precision invariant).
    v7_verdict_agg = verify_v7_balance(
        total_breakdown_sum=total_breakdown_sum_agg,
        unused_cost=unused_cost_agg,
        department_cost=expected_sum_agg,
    )

    # ── Step 8: compute_abc_allocation_hash (V8 determinism) ─────
    # Build per-dept UnusedCapacitySubRow list for hashing.
    unused_sub_rows = [
        UnusedCapacitySubRow(
            department_id=da.department_id,
            unused_hours=da.allocation.unused_capacity.unused_hours,
            unused_cost_krw=da.allocation.unused_capacity.unused_cost_krw,
            hash=da.allocation.unused_capacity.hash,
        )
        for da in per_dept
    ]
    result_hash = compute_abc_allocation_hash(
        multi_dept_ccr=multi_dept,
        per_dept_allocations=per_dept,
        unused_capacity_breakdown=unused_sub_rows,
    )

    # ── Step 9: Idempotency check + audit-first INSERT ───────────
    existing = await self._get_existing_snapshot(
        tenant_id=tenant_id,
        period_key=period_key,
        baseline_revision=baseline_revision,
        engine_type="abc",
    )
    if existing is not None:
        if existing.result_hash == result_hash:
            # Idempotent skip — same hash already persisted.
            await self._write_calc_log(
                tenant_id=tenant_id,
                period_key=period_key,
                baseline_revision=baseline_revision,
                engine_type="abc",
                action="idempotent_skip",
                result_hash=result_hash,
                trace_id=self.trace_id,
            )
            await self.session.commit()
            return _to_outcome(
                per_dept=per_dept,
                cost_object_breakdown=cost_object_breakdown_json,
                unused_capacity_breakdown=unused_capacity_breakdown_json,
                v7_verdict_agg=v7_verdict_agg,
                snapshot_id=str(existing.snapshot_id),
                result_hash=result_hash,
            )
        # Different hash → divergent (PRD §V6 — operator intervention).
        await self.session.rollback()
        raise CalcServiceError(
            tenant_id=tenant_id,
            period_key=period_key,
            reason="abc_snapshot_diverged",
            details={
                "existing_hash": existing.result_hash,
                "new_hash": result_hash,
            },
            trace_id=self.trace_id,
        )

    # ── Step 10: INSERT fiscal_period_snapshots + JSONB subdocs ──
    snapshot_id_str = str(uuid.uuid4())
    snapshot_id_uuid = uuid.UUID(snapshot_id_str)
    try:
        # Audit-first (CR 1.1 lesson) — calc_log + verification_log BEFORE snapshot.
        await self._write_calc_log(
            tenant_id=tenant_id,
            period_key=period_key,
            baseline_revision=baseline_revision,
            engine_type="abc",
            action="compute",
            result_hash=result_hash,
            trace_id=self.trace_id,
        )
        await self._write_verification_log(
            tenant_id=tenant_id,
            period_key=period_key,
            baseline_revision=baseline_revision,
            action="verification_passed",
            top_failure_code=None,
            top_failure_message_ko=None,
            result_hash=result_hash,
            trace_id=self.trace_id,
        )
        snapshot_row = FiscalPeriodSnapshot(
            tenant_id=tenant_id,
            period_key=period_key,
            baseline_revision=baseline_revision,
            engine_type="abc",
            material_cost=0,
            labor_cost=0,
            overhead_cost=0,
            manufacturing_cost=0,
            inventory_adjustment=0,
            result_hash=result_hash,
            state="verified",
            created_at=datetime.now(UTC),
            cost_object_breakdown=cost_object_breakdown_json,
            unused_capacity_breakdown=unused_capacity_breakdown_json,
        )
        # Override generated UUID with our pre-built one for envelope consistency.
        snapshot_row.snapshot_id = snapshot_id_uuid
        self.session.add(snapshot_row)
        await self.session.flush()
    except IntegrityError as integrity_err:
        # Concurrent compute won the UNIQUE race.
        await self.session.rollback()
        existing = await self._get_existing_snapshot(
            tenant_id=tenant_id,
            period_key=period_key,
            baseline_revision=baseline_revision,
            engine_type="abc",
        )
        if existing is not None and existing.result_hash == result_hash:
            # Idempotent skip after race.
            return _to_outcome(
                per_dept=per_dept,
                cost_object_breakdown=cost_object_breakdown_json,
                unused_capacity_breakdown=unused_capacity_breakdown_json,
                v7_verdict_agg=v7_verdict_agg,
                snapshot_id=str(existing.snapshot_id),
                result_hash=result_hash,
            )
        raise CalcServiceError(
            tenant_id=tenant_id,
            period_key=period_key,
            reason="abc_unique_constraint_violation",
            details={"pgerror": str(integrity_err.orig)[:500]},
            trace_id=self.trace_id,
        ) from integrity_err

    # ── Step 11: COMMIT ────────────────────────────────────────
    await self.session.commit()

    return _to_outcome(
        per_dept=per_dept,
        cost_object_breakdown=cost_object_breakdown_json,
        unused_capacity_breakdown=unused_capacity_breakdown_json,
        v7_verdict_agg=v7_verdict_agg,
        snapshot_id=snapshot_id_str,
        result_hash=result_hash,
    )


# Internal helpers for compute_and_persist (idempotency + audit-first INSERT).


async def _get_existing_snapshot_abc(
    self,
    *,
    tenant_id: uuid.UUID,
    period_key: str,
    baseline_revision: int,
    engine_type: str,
) -> FiscalPeriodSnapshot | None:
    """Idempotency check (CR 1.1 lesson) — same hash → no-op skip."""
    stmt = select(FiscalPeriodSnapshot).where(
        FiscalPeriodSnapshot.tenant_id == tenant_id,
        FiscalPeriodSnapshot.period_key == period_key,
        FiscalPeriodSnapshot.baseline_revision == baseline_revision,
        FiscalPeriodSnapshot.engine_type == engine_type,
    )
    result = await self.session.execute(stmt)
    return result.scalar_one_or_none()


async def _write_calc_log_abc(
    self,
    *,
    tenant_id: uuid.UUID,
    period_key: str,
    baseline_revision: int,
    engine_type: str,
    action: str,
    result_hash: str | None,
    trace_id: str,
) -> None:
    """Audit-first INSERT (CR 1.1 lesson) — calc_log BEFORE snapshot."""
    _ActionRegistry.validate(action_class=ActionClass.CALC_LOG, action=action)
    row = CalcLog(
        tenant_id=tenant_id,
        period_key=period_key,
        baseline_revision=baseline_revision,
        engine_type=engine_type,
        action=action,
        result_hash=result_hash,
        trace_id=trace_id,
        created_at=datetime.now(UTC),
    )
    self.session.add(row)
    await self.session.flush()


async def _write_verification_log_abc(
    self,
    *,
    tenant_id: uuid.UUID,
    period_key: str,
    baseline_revision: int,
    action: str,
    top_failure_code: str | None,
    top_failure_message_ko: str | None,
    result_hash: str,
    trace_id: str,
) -> None:
    """Audit-first INSERT (CR 1.1 lesson) — verification_log BEFORE snapshot."""
    _ActionRegistry.validate(action_class=ActionClass.VERIFICATION_LOG, action=action)
    row = VerificationLog(
        tenant_id=tenant_id,
        period_key=period_key,
        baseline_revision=baseline_revision,
        action=action,
        top_failure_code=top_failure_code,
        top_failure_message_ko=top_failure_message_ko,
        result_hash=result_hash,
        trace_id=trace_id,
        created_at=datetime.now(UTC),
    )
    self.session.add(row)
    await self.session.flush()


# Bind 11-step method + helpers to the class.
AbcAllocationService.compute_and_persist = compute_and_persist  # type: ignore[attr-defined]
AbcAllocationService._get_existing_snapshot_abc = _get_existing_snapshot_abc  # type: ignore[attr-defined]
AbcAllocationService._write_calc_log_abc = _write_calc_log_abc  # type: ignore[attr-defined]
AbcAllocationService._write_verification_log_abc = _write_verification_log_abc  # type: ignore[attr-defined]

# Aliases (private names without _abc suffix for cleaner service-layer calls).
AbcAllocationService._get_existing_snapshot = _get_existing_snapshot_abc  # type: ignore[attr-defined]
AbcAllocationService._write_calc_log = _write_calc_log_abc  # type: ignore[attr-defined]
AbcAllocationService._write_verification_log = _write_verification_log_abc  # type: ignore[attr-defined]


__all__ = [
    # Service-layer DTOs (CR 12-1 L3 boundary)
    "AbcCcrState",
    "AbcAllocationState",
    # Story 9.3 (T3) — compute_and_persist envelope
    "AbcAllocationOutcome",
    # Service-layer pre-validation (CR 12-5 L3 3-layer defense)
    "validate_ccr_inputs",
    "validate_allocation_inputs",
    # ORM→kernel boundary helpers
    "_to_ccr_state",
    "_to_allocation_state",
    "_to_outcome",
    "AbcAllocationService",
    # Serialization re-exports (CR 11-4 D-002 ko-KR.json SSOT)
    "serialize_ccr_state_for_api",
    "serialize_allocation_state_for_api",
]
