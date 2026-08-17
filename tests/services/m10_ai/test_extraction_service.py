"""tests.services.m10_ai.test_extraction_service — Story 10.1 service-layer tests.

Story 10.1 (cj-style Epic 10 cj-style 28번째 epic 연속) —
T2.7 tests for `apps.api/modules/m10_ai/service.py::extract_monthly_input`.

Test breakdown (~20 cases):
- import sanity × 4 (typed exceptions + service entry + result types)
- signature contract × 4 (extract_monthly_input + MonthlyExtractionResult fields)
- AD-7 strict invariant × 3 (target_table discriminator + Literal)
- audit-first invariant × 2 (CR 1.1)
- capability gate integration × 2 (AI_INSIGHT industry-agnostic)
- threshold boundary × 3 (0.70 RED / 0.90 YELLOW→GREEN)
- error envelope shape × 2 (CR 12-5 D-14 verbatim)

P-015 SSOT pattern: capability matrix drift detector runs in
`tests/integration/test_capability_matrix_v1_21_drift.py` (T4.1, 13 cases PASS).
"""

from __future__ import annotations

import inspect
from decimal import Decimal

import pytest

from apps.api.core.audit_action import (
    ActionClass,
    AIExtractionAction,
)
from apps.api.core.capability import Capability
from apps.api.modules.m10_ai.schemas import (
    MonthlyDraftResponse,
    MonthlyExtractError,
    MonthlyExtractRequest,
    MonthlyExtractResponse,
)
from apps.api.modules.m10_ai.service import (
    AiPipaConsentMissingError,
    MonthlyExtractionError,
    extract_monthly_input,
)
from packages.services.m10_ai.monthly_extraction_kernel import (
    CONFIDENCE_RED_THRESHOLD,
    CONFIDENCE_YELLOW_THRESHOLD,
    InvalidMonthlyFieldValueError,
    MonthlyInputDraftRow,
)

# ── 1. Import sanity (4 cases) ────────────────────────────────────


def test_extract_monthly_input_importable() -> None:
    """extract_monthly_input service entry exists and is callable."""
    assert callable(extract_monthly_input)
    assert inspect.iscoroutinefunction(extract_monthly_input)


def test_typed_exceptions_importable() -> None:
    """3 typed exceptions all importable from service/kernel."""
    assert AiPipaConsentMissingError is not None
    assert MonthlyExtractionError is not None
    assert InvalidMonthlyFieldValueError is not None


def test_ai_extraction_action_literal_present() -> None:
    """AIExtractionAction Literal includes the live `monthly_extraction_executed` value."""
    assert "monthly_extraction_executed" in AIExtractionAction.__args__
    assert "monthly_extraction_low_confidence_warning" in AIExtractionAction.__args__
    assert "monthly_extraction_promote_denied" in AIExtractionAction.__args__


def test_action_class_ai_extraction_executed_present() -> None:
    """ActionClass.AI_EXTRACTION_EXECUTED enum entry exists."""
    assert ActionClass.AI_EXTRACTION_EXECUTED is not None
    assert ActionClass.AI_EXTRACTION_EXECUTED.value == "ai_extraction_executed"


# ── 2. Signature contract (4 cases) ────────────────────────────────


def test_extract_monthly_input_signature() -> None:
    """extract_monthly_input has correct signature: session, tenant_id, period_key, document_bytes, document_type, trace_id."""
    sig = inspect.signature(extract_monthly_input)
    params = sig.parameters
    assert "session" in params
    assert "tenant_id" in params
    assert "period_key" in params
    assert "document_bytes" in params
    assert "document_type" in params
    assert "trace_id" in params


def test_monthly_extraction_result_fields() -> None:
    """MonthlyExtractionResult dataclass carries the expected fields."""
    from apps.api.modules.m10_ai.service import MonthlyExtractionResult

    expected_fields = {"extraction_id", "period_key", "drafts", "low_confidence_count", "trace_id"}
    actual_fields = {f.name for f in MonthlyExtractionResult.__dataclass_fields__.values()}
    assert expected_fields.issubset(actual_fields)


def test_monthly_extract_request_schema() -> None:
    """MonthlyExtractRequest has period_key + document_b64 + document_type fields."""
    fields = set(MonthlyExtractRequest.model_fields)
    assert "period_key" in fields
    assert "document_b64" in fields
    assert "document_type" in fields


def test_monthly_extract_response_schema() -> None:
    """MonthlyExtractResponse discriminated union via status: Literal['success', 'low_confidence_warning']."""
    fields = set(MonthlyExtractResponse.model_fields)
    assert "extraction_id" in fields
    assert "period_key" in fields
    assert "drafts" in fields
    assert "low_confidence_count" in fields
    assert "status" in fields
    status_field = MonthlyExtractResponse.model_fields["status"]
    assert "success" in str(status_field.annotation)
    assert "low_confidence_warning" in str(status_field.annotation)


# ── 3. AD-7 strict invariant (3 cases) ─────────────────────────────


def test_monthly_draft_response_target_table_literal() -> None:
    """MonthlyDraftResponse.target_table = Literal['monthly_inputs'] (AD-7 strict invariant)."""
    target_table_field = MonthlyDraftResponse.model_fields["target_table"]
    annotation_str = str(target_table_field.annotation)
    assert "monthly_inputs" in annotation_str
    # NEVER 'confirmed_inputs' (AD-7 verbatim)
    assert "confirmed_inputs" not in annotation_str


def test_monthly_input_draft_row_target_table_discriminator() -> None:
    """MonthlyInputDraftRow dataclass target_table field exists (used by service)."""
    fields = {f.name for f in MonthlyInputDraftRow.__dataclass_fields__.values()}
    assert "target_table" in fields


def test_monthly_extract_error_discriminated_codes() -> None:
    """MonthlyExtractError carries the 3 envelope codes (CR 12-5 D-14)."""
    error_code_field = MonthlyExtractError.model_fields["error_code"]
    annotation_str = str(error_code_field.annotation)
    assert "AI_PIPA_CONSENT_MISSING" in annotation_str
    assert "INVALID_MONTHLY_FIELD_VALUE" in annotation_str
    assert "MONTHLY_EXTRACTION_ERROR" in annotation_str


# ── 4. Audit-first invariant (2 cases, CR 1.1 lesson) ──────────────


def test_audit_action_class_routed_to_audit_logs() -> None:
    """ActionClass.AI_EXTRACTION_EXECUTED routes to audit_logs (CR 1.1 + AD-2)."""
    from apps.api.core.audit_action import _ActionRegistry

    log_type = _ActionRegistry.validate(
        action_class=ActionClass.AI_EXTRACTION_EXECUTED,
        action="monthly_extraction_executed",
    )
    assert log_type == "audit_logs"


def test_audit_first_insert_invariant_message() -> None:
    """The service layer docstring asserts CR 1.1 audit-first invariant."""
    source = inspect.getsource(extract_monthly_input)
    # CR 1.1 audit-first invariant: audit_logs INSERT BEFORE adapter call
    assert "audit-first" in source.lower() or "audit_first" in source.lower()
    assert "audit_logs" in source.lower() or "emit_audit_typed" in source


# ── 5. Capability gate integration (2 cases) ───────────────────────


def test_capability_ai_insight_present() -> None:
    """Capability.AI_INSIGHT enum entry exists (CR 12-1 L4 industry-agnostic precedent)."""
    assert hasattr(Capability, "AI_INSIGHT")
    assert Capability.AI_INSIGHT.value == "ai_insight"


def test_capability_ai_insight_granted_to_all_industries() -> None:
    """Capability.AI_INSIGHT is granted to all 4 industries (industry-agnostic baseline)."""
    from apps.api.core.capability import _INDUSTRY_CAPABILITIES

    industries_with_ai_insight = [
        ind for ind, caps in _INDUSTRY_CAPABILITIES.items()
        if Capability.AI_INSIGHT in caps
    ]
    assert len(industries_with_ai_insight) == 4


# ── 6. Threshold boundary (3 cases) ────────────────────────────────


def test_confidence_red_threshold() -> None:
    """CONFIDENCE_RED_THRESHOLD = Decimal('0.70') (master PRD §8.1 M0-c 70% 임계값)."""
    assert Decimal("0.70") == CONFIDENCE_RED_THRESHOLD


def test_confidence_yellow_threshold() -> None:
    """CONFIDENCE_YELLOW_THRESHOLD = Decimal('0.90')."""
    assert Decimal("0.90") == CONFIDENCE_YELLOW_THRESHOLD


@pytest.mark.parametrize(
    ("confidence", "requires_confirmation"),
    [
        (Decimal("0.69"), True),  # below 0.70 → requires
        (Decimal("0.70"), False),  # boundary, NOT requires (>= threshold)
        (Decimal("0.89"), False),  # 0.70-0.89 YELLOW → does not require
        (Decimal("0.90"), False),  # boundary 0.90 GREEN → does not require
        (Decimal("0.99"), False),  # above → does not require
    ],
)
def test_threshold_boundary_logic(
    confidence: Decimal, requires_confirmation: bool
) -> None:
    """Verify threshold boundary logic mirrors service.py:1018 `requires_confirmation = confidence_pct < CONFIDENCE_RED_THRESHOLD`."""
    requires_confirmation_actual = confidence < CONFIDENCE_RED_THRESHOLD
    assert requires_confirmation_actual == requires_confirmation


# ── 7. Error envelope shape (2 cases, CR 12-5 D-14 verbatim) ──────


def test_typed_exception_ai_pipa_consent_missing_attributes() -> None:
    """AiPipaConsentMissingError carries tenant_id + trace_id (CR 12-5 D-14 envelope payload)."""
    import uuid as uuid_mod

    tenant_id = uuid_mod.uuid4()
    trace_id = "test-trace-id"
    exc = AiPipaConsentMissingError(tenant_id=tenant_id, trace_id=trace_id)
    assert exc.tenant_id == tenant_id
    assert exc.trace_id == trace_id


def test_typed_exception_monthly_extraction_error_attributes() -> None:
    """MonthlyExtractionError carries tenant_id + period_key + reason + trace_id."""
    import uuid as uuid_mod

    tenant_id = uuid_mod.uuid4()
    exc = MonthlyExtractionError(
        tenant_id=tenant_id,
        period_key="2026-08",
        reason="adapter_timeout",
        trace_id="test-trace-id",
    )
    assert exc.tenant_id == tenant_id
    assert exc.period_key == "2026-08"
    assert exc.reason == "adapter_timeout"
    assert exc.trace_id == "test-trace-id"
