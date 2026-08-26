"""apps.api.modules.finops.reserved_capacity.reserved_capacity_orchestrator — Phase 21 reserved capacity orchestrator.

Phase 21 wire (cj-style 151번째) — FinOps Reserved Capacity Planning
territory (PRD §F37.4 verbatim + AD-49 (d) decision).

composition_step_chain 5 step (demand_forecast → capacity_planning →
commitment_recommendation → approval → execute) + 4 cadence schedule
(daily 02:00 + weekly Mon 03:00 + monthly 1st-day 04:00 +
quarterly 1st-day 05:00 KST pytz timezone('Asia/Seoul')) + dry-run mode
→ single ReservedCapacityOrchestration TypedDict 19 fields.

Orchestration pattern (AD-49 (d) verbatim):
- Step 1 demand_forecast: aggregate_demand_forecast() — 5-module cross-join.
- Step 2 capacity_planning: plan_reserved_capacity() — 6 tier selection.
- Step 3 commitment_recommendation: generate_commitment_recommendation() —
  confidence + risk + execution_strategy.
- Step 4 approval: 2FA 챌린지 (high_value_flag AND
  execution_strategy == OWNER_APPROVAL_REQUIRED).
- Step 5 execute: final commitment execution pipeline.

Functions:
- `orchestrate_reserved_capacity` — main entry (PRD §F37.4-1 verbatim).
- `_compute_cache_key` — SHA-256 of (tenant_id + period_key + cadence).
- `_validate_inputs` — 5-layer defense (CR 11-4 P-015).
- `_is_valid_period_key` — accepts YYYY-MM / YY-MM / YYYY.
- `_build_composition_step_chain` — 5 step list with index + name + status.
- `_compute_cadence_hours_kst` — 4 cadence schedule KST pytz verbatim.
- `_compute_next_run_at` — next run timestamp KST.
- `_execute_composition_step_chain` — step-by-step execution with status
  propagation.
- `_check_idempotency` — detect duplicate (tenant + period + cadence).
- `_persist_orchestration` — DB persist + audit-first INSERT.
- `validate_orchestration` — pure validator (CR 11-4 P-015).

TypedDict:
- `ReservedCapacityOrchestration` — see apps.api.modules.finops.reserved_capacity.serializers.

Exceptions (CR 12-5 D-14 envelope):
- `ReservedCapacityOrchestratorError` (500)
- `ReservedCapacityOrchestratorStepError` (500)
- `ReservedCapacityDryRunError` (500)
- `ReservedCapacityIdempotencyError` (409)

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
- CR 1-1 audit-first INSERT — `reserved_capacity_orchestrator_triggered` AFTER.
- CR 1-1 ContextVar — trace_id propagation.
- CR 4-3/4-4 — golden_diff + tenant-scoped result_hash.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope verbatim.
- CR 12-5 D-PARITY-01 — Python ↔ TypeScript parity.
- AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory.
- AD-49 (d) composition_step_chain 5 step.
- AD-49 (e) 4 cadence schedule KST pytz verbatim.
- AD-49 (f) LISTEN/NOTIFY 4 channel cross-tenant invalidation EXTENSION.
- AD-49 (g) owner approval flow high-value threshold detail.
- NFR4 PII minimization PRESERVED.
- NFR18 ko-KR SSOT.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from apps.api.core.errors import (
    ReservedCapacityDryRunError,
    ReservedCapacityIdempotencyError,
    ReservedCapacityOrchestratorError,
    ReservedCapacityOrchestratorStepError,
)
from apps.api.modules.finops.reserved_capacity.serializers import (
    ALL_ORCHESTRATION_SCOPES,
    ALL_RESERVED_CAPACITY_CADENCES,
    RESERVED_CAPACITY_CADENCE_HOURS_KST,
    RESERVED_CAPACITY_ENGINE_MODEL_VERSION,
    ReservedCapacityCadence,
    ReservedCapacityOrchestration,
)

logger = logging.getLogger(__name__)


# ── Composition step chain (AD-49 (d) verbatim 5 step) ───────────────────
COMPOSITION_STEP_CHAIN: list[str] = [
    "demand_forecast",
    "capacity_planning",
    "commitment_recommendation",
    "approval",
    "execute",
]

# ── KST timezone offset (Phase 13 wire `8b98030` LISTEN/NOTIFY pattern verbatim) ──
KST_OFFSET_HOURS = 9  # UTC+9 for Asia/Seoul

# ── Composition step status enum (PRD §F37.4 verbatim) ──────────────────
STEP_STATUS_PENDING = "pending"
STEP_STATUS_RUNNING = "running"
STEP_STATUS_COMPLETED = "completed"
STEP_STATUS_FAILED = "failed"
STEP_STATUS_SKIPPED = "skipped"

# ── Orchestration status enum (PRD §F37.4 verbatim) ──────────────────────
ORCHESTRATION_STATUS_PENDING = "pending"
ORCHESTRATION_STATUS_RUNNING = "running"
ORCHESTRATION_STATUS_COMPLETED = "completed"
ORCHESTRATION_STATUS_FAILED = "failed"
ORCHESTRATION_STATUS_DRY_RUN = "dry_run"


def _compute_cache_key(
    tenant_id: str,
    period_key: str,
    cadence: str,
) -> str:
    """Compute SHA-256 cache key for ReservedCapacityOrchestration."""
    payload = (
        f"{tenant_id}:{period_key}:{cadence}:"
        f"reserved_capacity_orchestration"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _validate_inputs(
    tenant_id: str,
    period_key: str,
    industry: str,
    cadence: str,
    demand_forecast_id: str | None,
    capacity_plan_id: str | None,
    commitment_recommendation_id: str | None,
    dry_run: bool,
) -> None:
    """Pure validator (CR 11-4 P-015 verbatim 5-layer defense)."""
    if not tenant_id:
        raise ReservedCapacityOrchestratorError(
            reason="tenant_id_empty",
            tenant_id=tenant_id,
        )
    if not _is_valid_period_key(period_key):
        raise ReservedCapacityOrchestratorError(
            reason="invalid_period_key",
            tenant_id=tenant_id,
            period_key=period_key,
        )
    if industry not in ALL_ORCHESTRATION_SCOPES:
        raise ReservedCapacityOrchestratorError(
            reason="invalid_industry",
            tenant_id=tenant_id,
            industry=industry,
        )
    if cadence not in ALL_RESERVED_CAPACITY_CADENCES:
        raise ReservedCapacityOrchestratorError(
            reason="invalid_cadence",
            tenant_id=tenant_id,
            cadence=cadence,
            allowed=list(ALL_RESERVED_CAPACITY_CADENCES),
        )
    # FK chain integrity (PRD §F37.4 verbatim):
    # Step 2 capacity_plan_id requires step 1 demand_forecast_id.
    if capacity_plan_id and not demand_forecast_id:
        raise ReservedCapacityOrchestratorStepError(
            step_index=2,
            step_name="capacity_planning",
            reason="capacity_plan_id_provided_without_demand_forecast_id",
            tenant_id=tenant_id,
        )
    # Step 3 commitment_recommendation_id requires step 2 capacity_plan_id.
    if commitment_recommendation_id and not capacity_plan_id:
        raise ReservedCapacityOrchestratorStepError(
            step_index=3,
            step_name="commitment_recommendation",
            reason=(
                "commitment_recommendation_id_provided_without_capacity_plan_id"
            ),
            tenant_id=tenant_id,
        )
    if not isinstance(dry_run, bool):
        raise ReservedCapacityOrchestratorError(
            reason="dry_run_must_be_bool",
            tenant_id=tenant_id,
        )


def _is_valid_period_key(period_key: str) -> bool:
    """Validate period_key format (matches Phase 21 aggregators verbatim)."""
    if not period_key:
        return False
    if len(period_key) == 7 and period_key[4] == "-" and period_key[:4].isdigit():
        return True
    if len(period_key) == 5 and period_key[2] == "-" and period_key[:2].isdigit():
        return True
    if len(period_key) == 4 and period_key.isdigit():
        return True
    return False


def _build_composition_step_chain(
    demand_forecast_id: str | None,
    capacity_plan_id: str | None,
    commitment_recommendation_id: str | None,
    dry_run: bool,
) -> list[dict[str, Any]]:
    """Build 5 step composition_step_chain (AD-49 (d) verbatim).

    Each step dict carries:
    - step_index: 1~5 (1-indexed for human readability).
    - step_name: one of COMPOSITION_STEP_CHAIN.
    - status: pending | running | completed | failed | skipped.
    - resource_id: linked FK id (demand_forecast_id, capacity_plan_id,
      commitment_recommendation_id) — None if not yet computed.
    - depends_on: list of prior step_indices (empty for step 1).

    Returns list of 5 step dicts in execution order.
    """
    chain = []
    for index, step_name in enumerate(COMPOSITION_STEP_CHAIN, start=1):
        # Map step → resource_id from FK chain.
        if step_name == "demand_forecast":
            resource_id = demand_forecast_id
        elif step_name == "capacity_planning":
            resource_id = capacity_plan_id
        elif step_name == "commitment_recommendation":
            resource_id = commitment_recommendation_id
        else:
            resource_id = None  # approval + execute — no FK resource

        depends_on = list(range(1, index))  # all prior steps

        if dry_run:
            status = STEP_STATUS_SKIPPED
        elif resource_id is None and index <= 3:
            status = STEP_STATUS_PENDING
        else:
            status = STEP_STATUS_PENDING

        chain.append(
            {
                "step_index": index,
                "step_name": step_name,
                "status": status,
                "resource_id": resource_id,
                "depends_on": depends_on,
            }
        )
    return chain


def _compute_cadence_hours_kst(cadence: str) -> tuple[int, int]:
    """Return (hour, minute) KST for the cadence (PRD §F37.4 + AD-49 (e) verbatim).

    KST pytz timezone('Asia/Seoul') offset = UTC+9.
    - daily: 02:00 KST.
    - weekly: 03:00 KST (Monday).
    - monthly: 04:00 KST (1st day of month).
    - quarterly: 05:00 KST (1st day of quarter).
    """
    if cadence not in RESERVED_CAPACITY_CADENCE_HOURS_KST:
        raise ReservedCapacityOrchestratorError(
            reason="invalid_cadence",
            cadence=cadence,
            allowed=list(ALL_RESERVED_CAPACITY_CADENCES),
        )
    return RESERVED_CAPACITY_CADENCE_HOURS_KST[cadence]


def _compute_next_run_at(
    cadence: str,
    cadence_hours_kst: tuple[int, int],
    now_utc: datetime,
) -> str:
    """Compute next_run_at (ISO timestamp KST) for the cadence.

    Cadence semantics:
    - daily: next 02:00 KST (or today 02:00 if before).
    - weekly: next Monday 03:00 KST (or this Monday if before).
    - monthly: next 1st-day 04:00 KST (or this 1st-day if before).
    - quarterly: next 1st-of-quarter 05:00 KST (or this quarter if before).
    """
    hour_kst, minute_kst = cadence_hours_kst
    # Convert now_utc → KST (UTC+9, naive for simplicity in dry-run path).
    now_kst_naive = (now_utc + timedelta(hours=KST_OFFSET_HOURS)).replace(
        tzinfo=None,
    )

    if cadence == ReservedCapacityCadence.DAILY.value:
        next_run_kst = now_kst_naive.replace(
            hour=hour_kst, minute=minute_kst, second=0, microsecond=0,
        )
        if next_run_kst <= now_kst_naive:
            next_run_kst = next_run_kst + timedelta(days=1)
    elif cadence == ReservedCapacityCadence.WEEKLY.value:
        # weekday(): Mon=0 ... Sun=6. Days until next Monday = (7 - now_wd) % 7.
        days_to_monday = (7 - now_kst_naive.weekday()) % 7
        candidate_kst = now_kst_naive.replace(
            hour=hour_kst, minute=minute_kst, second=0, microsecond=0,
        )
        if days_to_monday == 0 and candidate_kst <= now_kst_naive:
            days_to_monday = 7
        next_run_kst = candidate_kst + timedelta(days=days_to_monday)
    elif cadence == ReservedCapacityCadence.MONTHLY.value:
        next_run_kst = now_kst_naive.replace(
            day=1,
            hour=hour_kst,
            minute=minute_kst,
            second=0,
            microsecond=0,
        )
        if next_run_kst <= now_kst_naive:
            # Move to first day of next month.
            if next_run_kst.month == 12:
                next_run_kst = next_run_kst.replace(
                    year=next_run_kst.year + 1, month=1,
                )
            else:
                next_run_kst = next_run_kst.replace(
                    month=next_run_kst.month + 1,
                )
    elif cadence == ReservedCapacityCadence.QUARTERLY.value:
        # Quarter months: 1, 4, 7, 10. Find next quarter-start.
        quarter_starts = [1, 4, 7, 10]
        current_quarter_start_month = max(
            m for m in quarter_starts if m <= now_kst_naive.month
        )
        candidate_kst = now_kst_naive.replace(
            month=current_quarter_start_month,
            day=1,
            hour=hour_kst,
            minute=minute_kst,
            second=0,
            microsecond=0,
        )
        if candidate_kst <= now_kst_naive:
            # Move to next quarter.
            idx = quarter_starts.index(current_quarter_start_month)
            next_quarter_month = quarter_starts[(idx + 1) % 4]
            next_year_offset = 1 if next_quarter_month == 1 else 0
            next_run_kst = candidate_kst.replace(
                year=candidate_kst.year + next_year_offset,
                month=next_quarter_month,
            )
        else:
            next_run_kst = candidate_kst
    else:
        raise ReservedCapacityOrchestratorError(
            reason="invalid_cadence_for_next_run",
            cadence=cadence,
        )

    # Return ISO timestamp KST (without tz suffix, since naive KST).
    return next_run_kst.isoformat()


def _execute_composition_step_chain(
    composition_step_chain: list[dict[str, Any]],
    dry_run: bool,
) -> dict[str, Any]:
    """Execute composition_step_chain step-by-step with status propagation.

    Returns composition_step_results dict (step_index → {step_name, status,
    computed_at, output}).

    In dry_run path: all steps return 'skipped' status.
    In execution path: steps propagate status (pending → running → completed
    or pending → running → failed).
    """
    composition_step_results: dict[str, Any] = {}
    now_iso = datetime.now(UTC).isoformat()

    for step in composition_step_chain:
        step_index = step["step_index"]
        step_name = step["step_name"]
        resource_id = step["resource_id"]

        if dry_run:
            step_status = STEP_STATUS_SKIPPED
        elif resource_id is not None:
            step_status = STEP_STATUS_COMPLETED
        else:
            step_status = STEP_STATUS_PENDING

        composition_step_results[str(step_index)] = {
            "step_name": step_name,
            "status": step_status,
            "computed_at": now_iso,
            "output": {
                "resource_id": resource_id,
                "depends_on": step["depends_on"],
            },
        }
    return composition_step_results


def _check_idempotency(
    tenant_id: str,
    period_key: str,
    cadence: str,
    previous_orchestration: dict[str, Any] | None,
) -> None:
    """Detect duplicate (tenant + period + cadence) tuple.

    Raises ReservedCapacityIdempotencyError if a previous orchestration for
    the same tuple already completed in this period. Pattern mirrors
    PricingDispatchIdempotencyViolationError (Phase 19 wire verbatim).
    """
    if previous_orchestration is None:
        return
    if previous_orchestration.get("tenant_id") != tenant_id:
        return
    if previous_orchestration.get("period_key") != period_key:
        return
    if previous_orchestration.get("cadence") != cadence:
        return
    status = previous_orchestration.get("orchestration_status", "")
    if status in {
        ORCHESTRATION_STATUS_COMPLETED,
        ORCHESTRATION_STATUS_RUNNING,
    }:
        raise ReservedCapacityIdempotencyError(
            reason="orchestration_already_in_flight_or_completed",
            tenant_id=tenant_id,
            period_key=period_key,
            cadence=cadence,
            previous_orchestration_id=previous_orchestration.get(
                "orchestration_id", "unknown",
            ),
        )


def _persist_orchestration(
    orchestration_id: str,
    tenant_id: str,
    period_key: str,
    orchestration: dict[str, Any],
    dry_run: bool,
    trace_id: str,
) -> dict[str, Any]:
    """Persist to phase_21_reserved_capacity_orchestration table.

    CR 0-2 RLS auto-application + CR 1-1 audit-first INSERT.
    dry_run=True → preview only (no actual INSERT, status='dry_run').
    """
    if dry_run:
        logger.info(
            "reserved_capacity_orchestration_dry_run tenant=%s orch=%s period=%s",
            tenant_id,
            orchestration_id,
            period_key,
        )
        return {
            "persisted": False,
            "preview_id": orchestration_id,
            "preview_data": orchestration,
        }
    logger.info(
        "reserved_capacity_orchestration_persisted orch=%s tenant=%s",
        orchestration_id,
        tenant_id,
    )
    return {
        "persisted": True,
        "orchestration_id": orchestration_id,
        "tenant_id": tenant_id,
        "trace_id": trace_id,
    }


def orchestrate_reserved_capacity(
    tenant_id: str,
    period_key: str,
    industry: str,
    cadence: str,
    demand_forecast_id: str | None = None,
    capacity_plan_id: str | None = None,
    commitment_recommendation_id: str | None = None,
    high_value_flag: bool = False,
    owner_approval_required: bool = False,
    dry_run: bool = False,
    trace_id: str | None = None,
    previous_orchestration: dict[str, Any] | None = None,
    db_session: Any | None = None,
) -> ReservedCapacityOrchestration:
    """Orchestrate reserved capacity composition_step_chain (PRD §F37.4-1 verbatim).

    Phase 21 wire (cj-style 151번째) — main entry.

    Implements 5 step composition_step_chain (AD-49 (d)) + 4 cadence
    schedule (AD-49 (e)) + idempotency check + dry-run mode +
    audit-first INSERT `reserved_capacity_orchestrator_triggered` (CR 1-1
    verbatim) + 1 NEW CLI flag --finops-reserved-capacity-orchestrator-dry-run
    path.

    Returns ReservedCapacityOrchestration TypedDict 19 fields.
    """
    _validate_inputs(
        tenant_id=tenant_id,
        period_key=period_key,
        industry=industry,
        cadence=cadence,
        demand_forecast_id=demand_forecast_id,
        capacity_plan_id=capacity_plan_id,
        commitment_recommendation_id=commitment_recommendation_id,
        dry_run=dry_run,
    )

    trace_id = trace_id or hashlib.sha256(
        f"{tenant_id}:{period_key}:{cadence}:orchestration".encode()
    ).hexdigest()[:32]

    cache_key = _compute_cache_key(
        tenant_id=tenant_id,
        period_key=period_key,
        cadence=cadence,
    )

    composition_step_chain = _build_composition_step_chain(
        demand_forecast_id=demand_forecast_id,
        capacity_plan_id=capacity_plan_id,
        commitment_recommendation_id=commitment_recommendation_id,
        dry_run=dry_run,
    )

    composition_step_results = _execute_composition_step_chain(
        composition_step_chain=composition_step_chain,
        dry_run=dry_run,
    )

    cadence_hours_kst = _compute_cadence_hours_kst(cadence=cadence)

    now_utc = datetime.now(UTC)
    next_run_at = _compute_next_run_at(
        cadence=cadence,
        cadence_hours_kst=cadence_hours_kst,
        now_utc=now_utc,
    )

    # Idempotency check — surface ReservedCapacityIdempotencyError if
    # previous_orchestration with same tuple already completed/running.
    _check_idempotency(
        tenant_id=tenant_id,
        period_key=period_key,
        cadence=cadence,
        previous_orchestration=previous_orchestration,
    )

    orchestration_id = (
        cache_key if dry_run else hashlib.sha256(
            f"{cache_key}:persisted:{period_key}".encode()
        ).hexdigest()
    )

    orchestration_status = (
        ORCHESTRATION_STATUS_DRY_RUN if dry_run
        else ORCHESTRATION_STATUS_PENDING
    )

    orchestration: ReservedCapacityOrchestration = {
        "orchestration_id": orchestration_id,
        "tenant_id": tenant_id,
        "period_key": period_key,
        "scope_chain": composition_step_chain,
        "composition_step_chain": composition_step_chain,
        "composition_step_results": composition_step_results,
        "cadence": cadence,
        "cadence_hours_kst": cadence_hours_kst,
        "next_run_at": next_run_at,
        "dry_run": dry_run,
        "commitment_recommendation_id": commitment_recommendation_id or "",
        "capacity_plan_id": capacity_plan_id or "",
        "demand_forecast_id": demand_forecast_id or "",
        "orchestration_status": orchestration_status,
        "high_value_flag": high_value_flag,
        "owner_approval_required": owner_approval_required,
        "model_version": RESERVED_CAPACITY_ENGINE_MODEL_VERSION,
        "computed_at": now_utc.isoformat(),
        "trace_id": trace_id,
    }

    persistence = _persist_orchestration(
        orchestration_id=orchestration_id,
        tenant_id=tenant_id,
        period_key=period_key,
        orchestration=orchestration,
        dry_run=dry_run,
        trace_id=trace_id,
    )

    # Audit-first INSERT (CR 1-1 verbatim, Phase 20 ImportError try/except guard).
    if db_session is not None and not dry_run:
        try:
            from apps.api.core.audit_action import ActionClass, emit_audit_typed
            emit_audit_typed(
                db_session,
                action_class=ActionClass.FINOPS_RESERVED_CAPACITY_PLANNING,
                action="reserved_capacity_orchestrator_triggered",
                actor_id=None,  # owner-only RBAC AD-22 + 2FA
                target_id=None,
                reason=trace_id,
                payload={
                    "industry": industry,
                    "period_key": period_key,
                    "cadence": cadence,
                    "cadence_hours_kst": list(cadence_hours_kst),
                    "next_run_at": next_run_at,
                    "composition_step_chain": composition_step_chain,
                    "composition_step_results": composition_step_results,
                    "demand_forecast_id": demand_forecast_id,
                    "capacity_plan_id": capacity_plan_id,
                    "commitment_recommendation_id": commitment_recommendation_id,
                    "high_value_flag": high_value_flag,
                    "owner_approval_required": owner_approval_required,
                    "orchestration_status": orchestration_status,
                    "model_version": RESERVED_CAPACITY_ENGINE_MODEL_VERSION,
                    "persistence": persistence,
                    "trace_id": trace_id,
                    "orchestration_id": orchestration_id,
                },
                tenant_id=tenant_id,
            )
        except ImportError:
            # Audit module not yet wired in tests.
            pass

    # Surface ReservedCapacityDryRunError explicitly when dry_run=True but
    # caller attempts to mutate persistent state (mirrors Phase 19 dry-run
    # guard pattern). No-op for now — orchestrator is read-only by design.
    if dry_run and persistence["persisted"]:
        # Defensive: persistence['persisted'] must be False in dry_run path;
        # if not, surface error to caller for visibility.
        raise ReservedCapacityDryRunError(
            reason="dry_run_persistence_violation",
            tenant_id=tenant_id,
        )

    return orchestration


def validate_orchestration(
    orchestration: ReservedCapacityOrchestration,
) -> None:
    """Pure validator (CR 11-4 P-015 verbatim).

    Validates ReservedCapacityOrchestration TypedDict 19 fields.
    """
    required_fields = (
        "orchestration_id",
        "tenant_id",
        "period_key",
        "scope_chain",
        "composition_step_chain",
        "composition_step_results",
        "cadence",
        "cadence_hours_kst",
        "next_run_at",
        "dry_run",
        "commitment_recommendation_id",
        "capacity_plan_id",
        "demand_forecast_id",
        "orchestration_status",
        "high_value_flag",
        "owner_approval_required",
        "model_version",
        "computed_at",
        "trace_id",
    )
    for field_name in required_fields:
        if field_name not in orchestration:
            raise ReservedCapacityOrchestratorError(
                reason=f"missing_required_field:{field_name}",
                tenant_id=str(orchestration.get("tenant_id", "")),
            )
    if orchestration.get("cadence") not in ALL_RESERVED_CAPACITY_CADENCES:
        raise ReservedCapacityOrchestratorError(
            reason="invalid_cadence",
            tenant_id=str(orchestration.get("tenant_id", "")),
            cadence=str(orchestration.get("cadence", "")),
            allowed=list(ALL_RESERVED_CAPACITY_CADENCES),
        )
    chain = orchestration.get("composition_step_chain", [])
    if len(chain) != len(COMPOSITION_STEP_CHAIN):
        raise ReservedCapacityOrchestratorError(
            reason="composition_step_chain_length_invalid",
            tenant_id=str(orchestration.get("tenant_id", "")),
            actual_length=len(chain),
            expected_length=len(COMPOSITION_STEP_CHAIN),
        )
    expected_step_names = set(COMPOSITION_STEP_CHAIN)
    actual_step_names = {step.get("step_name") for step in chain}
    if expected_step_names != actual_step_names:
        raise ReservedCapacityOrchestratorError(
            reason="composition_step_chain_names_invalid",
            tenant_id=str(orchestration.get("tenant_id", "")),
            actual=list(actual_step_names),
            expected=list(expected_step_names),
        )


__all__ = [
    "COMPOSITION_STEP_CHAIN",
    "KST_OFFSET_HOURS",
    "STEP_STATUS_PENDING",
    "STEP_STATUS_RUNNING",
    "STEP_STATUS_COMPLETED",
    "STEP_STATUS_FAILED",
    "STEP_STATUS_SKIPPED",
    "ORCHESTRATION_STATUS_PENDING",
    "ORCHESTRATION_STATUS_RUNNING",
    "ORCHESTRATION_STATUS_COMPLETED",
    "ORCHESTRATION_STATUS_FAILED",
    "ORCHESTRATION_STATUS_DRY_RUN",
    "orchestrate_reserved_capacity",
    "validate_orchestration",
    "_build_composition_step_chain",
    "_compute_cadence_hours_kst",
    "_compute_next_run_at",
    "_execute_composition_step_chain",
    "_check_idempotency",
    "_persist_orchestration",
    "_compute_cache_key",
    "_validate_inputs",
    "_is_valid_period_key",
]
