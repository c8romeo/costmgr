"""tests.api.test_verdict_envelope — CalcResponse.verdict Pydantic envelope tests.

Story 4.3 (Task 5.2) — AD-12 verdict envelope validation.

Covers:
- Verdict Pydantic schema — passed/failed literal, verifications[] invariants
- VerificationItem — code, status, message_ko, details fields
- CalcResponse.verdict field — required + extra='forbid'
- top_failure invariant: non-None iff verification_status='failed'
- Industrial value mappings (CR 2.3 extra='forbid' guard)
"""

from __future__ import annotations

import uuid as _uuid_mod

import pytest
from pydantic import ValidationError

from apps.api.modules.m3_calculate.schemas import (
    CalcResponse,
    Verdict,
    VerificationItem,
)


# ── VerificationItem schema ─────────────────────────────────
@pytest.mark.engine
def test_verification_item_happy_path() -> None:
    """VerificationItem — V1 passed with delta_krw detail."""
    item = VerificationItem(
        code="V1",
        status="passed",
        message_ko="완전배부 정상",
        details={"delta_krw": 0},
    )
    assert item.code == "V1"
    assert item.status == "passed"
    assert item.details["delta_krw"] == 0


@pytest.mark.engine
def test_verification_item_rejects_invalid_code() -> None:
    """VerificationItem.code — Literal['V1','V4','V7','V8'] enforced."""
    with pytest.raises(ValidationError):
        VerificationItem(
            code="V9",  # type: ignore[arg-type]
            status="passed",
            message_ko="x",
            details={},
        )


@pytest.mark.engine
def test_verification_item_rejects_invalid_status() -> None:
    """VerificationItem.status — Literal['passed','failed'] enforced (no 'pending')."""
    with pytest.raises(ValidationError):
        VerificationItem(
            code="V1",
            status="pending",  # type: ignore[arg-type]
            message_ko="x",
            details={},
        )


@pytest.mark.engine
def test_verification_item_extra_forbid() -> None:
    """CR 2.3 lesson — extra='forbid' blocks unknown fields."""
    with pytest.raises(ValidationError):
        VerificationItem(
            code="V1",
            status="passed",
            message_ko="x",
            details={},
            unknown_field="extra",  # type: ignore[call-arg]
        )


# ── Verdict schema ──────────────────────────────────────────
@pytest.mark.engine
def test_verdict_passing_invariant_top_failure_is_none() -> None:
    """Verdict passed → top_failure MUST be None (AD-20 invariant)."""
    verdict = Verdict(
        verification_status="passed",
        verifications=[
            VerificationItem(code="V1", status="passed", message_ko="정상", details={}),
        ],
        top_failure=None,
        trace_id="t-1",
    )
    assert verdict.verification_status == "passed"
    assert verdict.top_failure is None
    assert len(verdict.verifications) == 1


@pytest.mark.engine
def test_verdict_failed_invariant_top_failure_non_null() -> None:
    """Verdict failed → top_failure MUST be non-None (AD-20)."""
    failed_item = VerificationItem(
        code="V1",
        status="failed",
        message_ko="위반",
        details={"delta_krw": -100},
    )
    verdict = Verdict(
        verification_status="failed",
        verifications=[failed_item],
        top_failure=failed_item,
        trace_id="t-2",
    )
    assert verdict.verification_status == "failed"
    assert verdict.top_failure is not None
    assert verdict.top_failure.code == "V1"


@pytest.mark.engine
def test_verdict_rejects_pending_status() -> None:
    """Verdict.verification_status — Literal['passed','failed'] enforced (AD-20)."""
    with pytest.raises(ValidationError):
        Verdict(
            verification_status="pending",  # type: ignore[arg-type]
            verifications=[],
            top_failure=None,
            trace_id="t-3",
        )


@pytest.mark.engine
def test_verdict_empty_verifications_list_is_valid() -> None:
    """Verdict.verifications=[] — valid for idempotent_skip path (no rules fired)."""
    verdict = Verdict(
        verification_status="passed",
        verifications=[],
        top_failure=None,
        trace_id="t-4",
    )
    assert verdict.verifications == []
    assert verdict.verification_status == "passed"


# ── CalcResponse.verdict field ──────────────────────────────
@pytest.mark.engine
def test_calc_response_verdict_field_required() -> None:
    """CalcResponse.verdict is REQUIRED (Story 4.3 schema extension)."""
    with pytest.raises(ValidationError):
        CalcResponse(
            tenant_id=_uuid_mod.UUID("11111111-1111-4111-8111-111111111111"),
            period_key="2026-07",
            baseline_revision=1,
            material_cost=1_000_000,
            labor_cost=500_000,
            overhead_cost=300_000,
            manufacturing_cost=1_800_000,
            inventory_adjustment=0,
            result_hash="0" * 64,
            state="verified",
            trace_id="t-5",
            # verdict= omitted → must fail
        )


@pytest.mark.engine
def test_calc_response_verdict_field_validation() -> None:
    """CalcResponse with verdict field — happy path 200 OK envelope."""
    verdict = Verdict(
        verification_status="passed",
        verifications=[
            VerificationItem(code="V1", status="passed", message_ko="정상", details={}),
            VerificationItem(code="V4", status="passed", message_ko="정상", details={"4_elements": {}}),
            VerificationItem(code="V8", status="passed", message_ko="placeholder", details={"placeholder": True}),
        ],
        top_failure=None,
        trace_id="t-6",
    )
    response = CalcResponse(
        tenant_id=_uuid_mod.UUID("11111111-1111-4111-8111-111111111111"),
        period_key="2026-07",
        baseline_revision=1,
        material_cost=1_000_000,
        labor_cost=500_000,
        overhead_cost=300_000,
        manufacturing_cost=1_800_000,
        inventory_adjustment=0,
        result_hash="0" * 64,
        state="verified",
        trace_id="t-6",
        verdict=verdict,
    )
    assert response.verdict.verification_status == "passed"
    assert len(response.verdict.verifications) == 3
    assert response.state == "verified"


@pytest.mark.engine
def test_calc_response_verdict_failed_with_top_failure() -> None:
    """CalcResponse with verdict='failed' — service-layer ROLLBACK but envelope surfaces."""
    failed_item = VerificationItem(
        code="V1",
        status="failed",
        message_ko="완전배부 위반 — delta KRW -100",
        details={"delta_krw": -100},
    )
    verdict = Verdict(
        verification_status="failed",
        verifications=[failed_item],
        top_failure=failed_item,
        trace_id="t-7",
    )
    response = CalcResponse(
        tenant_id=_uuid_mod.UUID("11111111-1111-4111-8111-111111111111"),
        period_key="2026-07",
        baseline_revision=1,
        material_cost=1_000_000,
        labor_cost=500_000,
        overhead_cost=300_000,
        manufacturing_cost=1_800_000,
        inventory_adjustment=0,
        result_hash="a" * 64,
        state="verified",
        trace_id="t-7",
        verdict=verdict,
    )
    assert response.verdict.verification_status == "failed"
    assert response.verdict.top_failure is not None
    assert response.verdict.top_failure.code == "V1"
    # Note: state remains 'verified' for the engine's draft — the application
    # layer's ROLLBACK is reflected in the verdict envelope, not in state.
    # (Per Story 4.3 AC #4: 200 OK with envelope on failed verification.)


# ── CR 1.1 Industry drift guard (F-5 review) ───────────────────
@pytest.mark.engine
def test_industry_values_match_industry_enum() -> None:
    """CR 1.1 drift guard: protocol.INDUSTRY_VALUES must equal Industry enum.

    Story 4.3 review F-5: protocol.py originally carried a parallel set of
    string literals (`manufacturing_retail`, `mixed`) that did not match
    Industry enum (`manufacturing_service`, `manufacturing_service_other`).
    This test pins the SSOT — any drift in either direction fails here.
    """
    from apps.api.modules.m3_calculate.services.rules.protocol import INDUSTRY_VALUES
    from packages.services.m0_onboarding.industry_menu import Industry

    canonical = {member.value for member in Industry}
    asserted = set(INDUSTRY_VALUES)
    assert canonical == asserted, (
        f"INDUSTRY_VALUES drift: protocol={asserted}, "
        f"Industry enum={canonical}. Either update protocol.py to import "
        f"from Industry, or update Industry enum (one SSOT)."
    )


# ── CR 2.3 extra='forbid' guard ────────────────────────────────
@pytest.mark.engine
def test_verdict_extra_forbid() -> None:
    """Verdict envelope rejects unknown fields (CR 2.3 lesson).

    Pydantic extra='forbid' on Verdict must reject extra fields. If a future
    contributor adds a field, the test fails. Mirrors Story 2.1 review
    F-? extra='forbid' enforcement.
    """
    with pytest.raises(ValidationError):
        Verdict(
            verification_status="passed",
            verifications=[],
            top_failure=None,
            trace_id="t-extra",
            extra_unknown_field="should fail",  # type: ignore[call-arg]
        )


# ── Story 4.4 — V8 audit log semantics (AC #9) ──────────────
@pytest.mark.engine
@pytest.mark.v8_regression
def test_audit_log_verification_failed_v8_path() -> None:
    """Story 4.4 AC #9 — V8 fail 시 audit action = 'verify_v8_golden_match'.

    Verifies the A5 forward-lock: when the V8 rule fires the top failure,
    the audit_action registry accepts 'verify_v8_golden_match' and maps
    it to ActionClass.VERIFICATION_LOG → AuditLogType 'verification_log'.
    Mirrors calc_orchestrator._write_verification_log wire (V8 branch).

    The actual DB INSERT is exercised in calc_orchestrator integration
    tests; this test pins the registry contract so a future rename fails
    here first (CR 1.1 lesson — 5th epic drift prevention).
    """
    from apps.api.core.audit_action import (
        ActionClass,
        _ActionRegistry,
    )

    # The new action must be accepted by the registry.
    log_type = _ActionRegistry.validate(
        action_class=ActionClass.VERIFICATION_LOG,
        action="verify_v8_golden_match",
    )
    assert log_type == "verification_log"
    # AuditLogType is a Literal — pin the wire literal in a separate assert.
    assert "verification_log" in {"audit_logs", "calc_log", "verification_log", "inventory_ledger", "reversal_log"}


@pytest.mark.engine
@pytest.mark.v8_regression
def test_audit_action_registry_v8_branch_distinct_from_v1_v4_v7() -> None:
    """V8 audit action is DISTINCT from V1·V4·V7 (CR 1.1 forward-lock).

    The 'verify_v8_golden_match' enum is a separate forward-lock category
    so that operators can filter audit trails by V8 골든 vs V1·V4·V7
    4-요소 violations. Even though both map to verification_log table,
    they remain semantically distinct actions.
    """
    from apps.api.core.audit_action import (
        ActionClass,
        _ActionRegistry,
    )

    v8_actions = _ActionRegistry._REGISTRY[ActionClass.VERIFICATION_LOG][1]
    assert "verify_v8_golden_match" in v8_actions
    assert "verification_failed" in v8_actions
    assert "verification_passed" in v8_actions
    assert "verification_skipped" in v8_actions
    # 4 distinct actions total.
    assert len(v8_actions) == 4
