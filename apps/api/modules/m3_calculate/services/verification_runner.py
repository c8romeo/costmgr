"""apps.api.modules.m3_calculate.services.verification_runner — AD-12 verifier.

Story 4.3 (Task 2.1~2.4) — runs V1·V4·V7·V8 in strict ordered sequence.

AD-12 verification-first invariant (ARCHITECTURE-SPINE):
    M3 runs input validation → engine calculation → V1→V4→V7→V8 in
    order → verified → snapshot persistence → committed. A failed check
    aborts later checks. Service-only tenants skip V1/V4 (cj-style
    reinterpretation: V1/V4 universal, V7 service-only) but still run
    V7/V8.

Service-only industry handling:
    - V1, V4, V8: fire for ALL industries (universal invariants).
    - V7: fires only for `service` (per AD-12 spec interpretation).

Earlier-failed aborts later: V1 fail → V4·V7·V8 omitted from
`verifications[]`. The returned `Verdict.verifications` array contains
only the rules that actually fired (silent skip for applies_to=False).

`run_all` is `async def` even though rule kernels are pure (no async I/O).
This matches the orchestrator's signature conventions (`_write_calc_log`,
`_write_fiscal_period_snapshot` are all async) so the orchestrator
seamlessly awaits the runner. The runner itself does not perform any
async I/O — rule kernels are sync.
"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from apps.api.modules.m3_calculate.services.rules import (
    _VERIFICATION_RULES,
    RuleInput,
    VerificationItem,
)
from packages.cost_engine.core.period_cost import Baseline
from packages.cost_engine.ports.calc_port import CalcResult, MonthlyInput

VerificationEnvelopeStatus = Literal["passed", "failed"]


class Verdict:
    """AD-20 verification envelope (Story 4.3 AC #3).

    Pure frozen data class — mirrors the `Verdict` Pydantic model in
    `apps/api/modules/m3_calculate/schemas.py`. Pydantic envelope used
    for HTTP response; this frozen class used for service-layer
    composition (orchestrator → schema envelope).

    Fields:
        verification_status: 'passed' (all fired rules passed) or 'failed'
            (any fired rule failed). Pending state is internal/transient
            (AD-20) and never exposed externally.
        verifications: ordered list of VerificationItem for fired rules
            only. Skipped rules (applies_to=False) are omitted.
        top_failure: first VerificationItem with status='failed', or None
            if all fired rules passed. NOT None iff verification_status='failed'.
        trace_id: AD-15 §4 envelope trace identifier.
    """

    __slots__ = (
        "verification_status",
        "verifications",
        "top_failure",
        "trace_id",
    )

    def __init__(
        self,
        verification_status: VerificationEnvelopeStatus,
        verifications: list[VerificationItem],
        top_failure: VerificationItem | None,
        trace_id: str,
    ) -> None:
        self.verification_status = verification_status
        self.verifications = verifications
        self.top_failure = top_failure
        self.trace_id = trace_id

    def __repr__(self) -> str:
        return (
            f"Verdict(status={self.verification_status!r}, "
            f"verifications={len(self.verifications)} items, "
            f"top_failure={self.top_failure.code if self.top_failure else None!r})"
        )


class VerificationRunner:
    """AD-12 V1·V4·V7·V8 strict ordered sequence runner.

    Usage:
        runner = VerificationRunner(trace_id=trace_id)
        verdict = await runner.run_all(
            monthly_input=..., baseline=..., calc_result=...,
            industry=..., tenant_id=..., period_key=...,
        )
        if verdict.verification_status == "failed":
            # rollback + return envelope to caller (handler → 200 + verdict)
            ...
    """

    def __init__(self, *, trace_id: str) -> None:
        self._trace_id = trace_id  # pure constructor (no DB)

    async def run_all(
        self,
        *,
        monthly_input: MonthlyInput,
        baseline: Baseline,
        calc_result: CalcResult,
        industry: str,
        tenant_id: UUID,
        period_key: str,
    ) -> Verdict:
        """Run the 4-rule strict ordered sequence.

        AD-12 ordering invariant: previous rule status='failed' → abort
        later rules. The `verifications[]` array contains ONLY fired
        rules (silent skip for `applies_to=False`).

        AD-5 purity: rule kernels do not perform I/O. The runner itself
        is also pure (no DB session, no clock). Async signature matches
        orchestrator conventions.
        """
        rule_input = RuleInput(
            monthly_input=monthly_input,
            baseline=baseline,
            calc_result=calc_result,
            industry=industry,
            tenant_id=tenant_id,
            period_key=period_key,
            trace_id=self._trace_id,
        )

        verifications: list[VerificationItem] = []
        for rule in _VERIFICATION_RULES:
            if not rule.applies_to(industry=industry):
                # Silent skip — does NOT appear in verifications[].
                continue
            item = rule.check(rule_input)
            verifications.append(item)
            if item.status == "failed":
                # AD-12 ordering invariant — earlier failed aborts later.
                break

        verification_status: VerificationEnvelopeStatus = (
            "passed"
            if all(v.status == "passed" for v in verifications)
            else "failed"
        )
        top_failure: VerificationItem | None = next(
            (v for v in verifications if v.status == "failed"), None
        )
        return Verdict(
            verification_status=verification_status,
            verifications=verifications,
            top_failure=top_failure,
            trace_id=self._trace_id,
        )


__all__ = [
    "VerificationRunner",
    "Verdict",
    "VerificationEnvelopeStatus",
]
