"""apps.api.modules.m3_calculate.services.rules.v3_closing_invariant — V3 rule kernel.

Story 5.3 (Task 5.1) — V3: closing ≥ 0 invariant (PRD §V3 + §F4.2).

AD-5 purity: rule kernel itself is pure (no DB, no clock, no I/O).
The orchestrator pre-loads the V3Verdict TypedDict via
`ClosingGuardService.validate_closing_invariant_against_active_products()`
BEFORE `VerificationRunner.run_all()`. The rule kernel consumes the
pre-loaded verdict and returns a VerificationItem.

This preserves the AD-5 purity invariant for all 5 rules
(V1·V4·V3·V7·V8) — verified by AST import check
`tests/cost_engine/test_verification_rules.py::test_verification_rules_no_io_imports`.

AD-12 ordering: V3 is slot 3 of 5 (V1 → V4 → V3 → V7 → V8).
Earlier failed aborts later (CR 1.1 lesson preserved).

Per-industry firing:
- V3 fires for all industries EXCEPT service-only (no inventory semantics).
- skip_reason surfaced via `VerificationItem.details.skip_reason_ko`.
"""

from __future__ import annotations

from typing import Literal

from apps.api.modules.m3_calculate.services.rules.protocol import (
    RuleInput,
    VerificationItem,
)
from packages.cost_engine.closing_invariant_check import (
    V3_RULE_CODE,
    V3_SKIP_REASON_SERVICE_ONLY_KO,
    V3_STATUS_FAILED,
    V3_STATUS_PASSED,
    V3_STATUS_SKIPPED,
)


class V3ClosingInvariantRule:
    """V3 — closing ≥ 0 invariant (PRD §V3 + §F4.2).

    Per-industry firing: True for non-service industries (manufacturing,
    retail, mixed). False for service-only (no inventory semantics —
    V3 would always skip with `V3_SKIP_REASON_SERVICE_ONLY_KO`).
    """

    @property
    def name(self) -> Literal["V3"]:
        return V3_RULE_CODE  # 'V3'

    def applies_to(self, *, industry: str) -> bool:
        # V3 fires for every industry EXCEPT service-only (no inventory).
        return industry != "service"

    def check(self, input: RuleInput) -> VerificationItem:
        """Pure check. Consumes pre-loaded V3Verdict.

        The orchestrator pre-loads `closing_invariant_verdict` via
        ClosingGuardService.validate_closing_invariant_against_active_products().
        V3 kernel just adapts the verdict shape to VerificationItem.

        CR 5.3 P17 review patch — SKIP semantic fix.
        Pre-patch: when V3 verdict.status == 'skipped' (industry=service
        OR empty aggregate+whitelist), the V3 kernel returned
        VerificationItem.status='passed' (silent skip). Post-patch:
        returns VerificationItem.status='skipped' so callers can
        distinguish "evaluated and passed" from "evaluated and skipped".
        Per AD-12, 'skipped' does NOT block later rules (still
        metadata-only); the `verifications[]` array now carries V3
        entries with status='skipped' when applicable.

        Returns:
            VerificationItem with code='V3', status mapped from
            V3_STATUS_* (passed → 'passed', failed → 'failed',
            skipped → 'skipped' — distinct from 'passed').
        """
        verdict = input.closing_invariant_verdict
        if verdict is None:
            # Defense-in-depth — orchestrator should always pre-load.
            # If absent, treat as skipped (no harm to other rules).
            return VerificationItem(
                code="V3",
                status="skipped",
                message_ko=V3_SKIP_REASON_SERVICE_ONLY_KO,
                details={
                    "v3_status": V3_STATUS_SKIPPED,
                    "skip_reason_ko": "V3 verdict not pre-loaded — orchestrator must call ClosingGuardService",
                    "failures_count": 0,
                    "product_whitelist_size": 0,
                },
            )

        v3_status = verdict.get("status")
        failures = verdict.get("failures") or []
        skip_reason_ko = verdict.get("skip_reason_ko")

        if v3_status == V3_STATUS_FAILED:
            top_failure = failures[0] if failures else {}
            top_product_id = top_failure.get("product_id", "")
            top_closing_qty = top_failure.get("closing_qty", "0")
            top_message_ko = top_failure.get("message_ko", "기말재고 음수")
            return VerificationItem(
                code="V3",
                status="failed",
                message_ko=(
                    f"{top_message_ko} (product={top_product_id}, " f"closing={top_closing_qty}개)"
                ),
                details={
                    "v3_status": V3_STATUS_FAILED,
                    "failures_count": len(failures),
                    "failures": failures,
                    "product_whitelist_size": verdict.get("product_whitelist_size", 0),
                    "top_failure": top_failure,
                    "skip_reason_ko": None,
                },
            )

        if v3_status == V3_STATUS_SKIPPED:
            # CR 5.3 P17 — SKIP surfaces as VerificationItem.status='skipped'.
            return VerificationItem(
                code="V3",
                status="skipped",
                message_ko=f"V3 skip: {skip_reason_ko or ''}",
                details={
                    "v3_status": V3_STATUS_SKIPPED,
                    "failures_count": 0,
                    "product_whitelist_size": verdict.get("product_whitelist_size", 0),
                    "skip_reason_ko": skip_reason_ko,
                },
            )

        # passed → status='passed'
        return VerificationItem(
            code="V3",
            status="passed",
            message_ko=(
                f"closing ≥ 0 invariant 정상 (product_whitelist_size="
                f"{verdict.get('product_whitelist_size', 0)})"
            ),
            details={
                "v3_status": V3_STATUS_PASSED,
                "failures_count": 0,
                "product_whitelist_size": verdict.get("product_whitelist_size", 0),
                "skip_reason_ko": None,
            },
        )


__all__ = ["V3ClosingInvariantRule"]
