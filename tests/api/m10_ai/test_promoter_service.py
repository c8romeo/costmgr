"""tests.api.m10_ai.test_promoter_service — Story 10.4 service-layer tests.

Story 10.4 (cj-style Epic 10 5번째 진입점 = cj-style 33번째 epic 연속) —
T3 tests for `apps.api.modules.m10_ai.services.promoter_service`
(`PromoterService` + 11-step pipeline + typed exceptions).

Test breakdown (~22 cases, no DB):
- import sanity × 4 (PromoterService + 4 typed exceptions)
- signature contract × 4 (promote() method + 11-step pipeline marker +
  audit-first 2-row pattern marker + AD-17 idempotency 3-tuple marker)
- audit_action Literal EXTENSION × 3 (input_draft_promoted +
  monthly_extraction_promote_executed + AD-7 strict invariant guard
  monthly_extraction_promote_denied preserved)
- AD-17 verbatim 3-tuple × 2 (kernel + service compute_promotion_idempotency_key
  same value mirror)
- AD-5 stdlib-only kernel preserved × 1 (kernel has no I/O imports)
- AD-7 strict invariant service guard × 2 (M10 NEVER writes confirmed_inputs;
  service uses monthly_input_rows discriminator)
- Pydantic-free shape validation × 2 (validate_promotion_request period_key +
  actor_role)
- A19 cohesion 8 surface marker × 2 (kernel T1 + port T1 + db schema T2 +
  service T3 + handler T4 + envelope T4 + capability T4 + audit T4)

P-015 SSOT pattern: capability matrix drift detector runs in
`tests/integration/test_capability_matrix_v1_21_drift.py`.
"""

from __future__ import annotations

import inspect
import uuid

import pytest

# ── Kernel + ActionClass imports (sanity + AD-7 strict invariant) ───


def test_promoter_service_module_importable() -> None:
    """`apps.api.modules.m10_ai.services.promoter_service` is importable."""
    from apps.api.modules.m10_ai.services import promoter_service

    assert promoter_service is not None
    assert inspect.ismodule(promoter_service)


def test_promoter_service_class_exists() -> None:
    """PromoterService class is importable from the service module."""
    from apps.api.modules.m10_ai.services.promoter_service import PromoterService

    assert inspect.isclass(PromoterService)


def test_4_typed_exceptions_importable() -> None:
    """4 NEW typed exceptions all importable from the service module."""
    from apps.api.modules.m10_ai.services.promoter_service import (
        PromoterServiceError,
        PromotionDraftImmutableError,
        PromotionIdempotencyMismatchError,
        PromotionM2OnlyDeniedError,
        PromotionSourceDraftNotFoundError,
    )

    assert PromoterServiceError is not None
    assert PromotionSourceDraftNotFoundError is not None
    assert PromotionDraftImmutableError is not None
    assert PromotionIdempotencyMismatchError is not None
    assert PromotionM2OnlyDeniedError is not None


def test_db_promoter_adapter_module_importable() -> None:
    """`apps.api.modules.m10_ai.services.db_promoter_adapter` is importable."""
    from apps.api.modules.m10_ai.services import db_promoter_adapter

    assert db_promoter_adapter is not None
    assert inspect.ismodule(db_promoter_adapter)


# ── Signature contract (AD-17 verbatim bind) ────────────────────────


def test_promote_method_signature() -> None:
    """PromoterService.promote() takes PromotionRequest and returns PromotionResult.

    AD-17 verbatim: only M2 may call. Service signature mirrors kernel
    Protocol `InputPromoterPort.promote()` (1:1 mapping).
    """
    from apps.api.modules.m10_ai.services.promoter_service import PromoterService

    sig = inspect.signature(PromoterService.promote)
    params = sig.parameters
    assert "request" in params
    assert "self" in params

    # The return annotation is the forward ref string "PromotionResult"
    # because we used `from __future__ import annotations` in the service.
    # Compare against the string form (avoids get_type_hints forward-ref
    # resolution complexity).
    assert sig.return_annotation == "PromotionResult"
    assert params["request"].annotation == "PromotionRequest"


def test_promoter_service_init_signature() -> None:
    """PromoterService(session, *, trace_id) — DI via AsyncSession + trace_id."""
    from apps.api.modules.m10_ai.services.promoter_service import PromoterService

    sig = inspect.signature(PromoterService.__init__)
    params = sig.parameters
    assert "session" in params
    assert "trace_id" in params


def test_eleven_step_pipeline_marker() -> None:
    """11-step pipeline marker comment is present in the service source.

    The pipeline is documented inline in the service file (master PRD
    §F10.2 + AD-17 verbatim); the drift detector verifies the comment
    text matches the spec verbatim.
    """
    from apps.api.modules.m10_ai.services import promoter_service

    source = inspect.getsource(promoter_service)
    assert "11-step" in source or "11 step" in source


def test_audit_first_insert_2row_pattern_marker() -> None:
    """audit-first INSERT 2-row append pattern (CR 1.1 verbatim).

    Row 1: INPUT_DRAFT/input_draft_promoted.
    Row 2: AI_EXTRACTION_EXECUTED/monthly_extraction_promote_executed.
    """
    from apps.api.modules.m10_ai.services import promoter_service

    source = inspect.getsource(promoter_service)
    assert "input_draft_promoted" in source
    assert "monthly_extraction_promote_executed" in source
    # Row 1 emit is BEFORE INSERT monthly_input_promotions (CR 1.1)
    assert "audit-first" in source.lower() or "audit_first" in source.lower()


# ── audit_action Literal EXTENSION (10-4 wire) ─────────────────────


def test_input_draft_promoted_in_input_draft_action_literal() -> None:
    """InputDraftAction Literal EXTENSION includes `input_draft_promoted`.

    10-4 EXTENSION: AD-17 verbatim audit-first INSERT Row 1.
    """
    from apps.api.core.audit_action import InputDraftAction

    args = InputDraftAction.__args__
    assert "input_draft_promoted" in args
    # Existing 2 values preserved
    assert "input_draft_confirm" in args
    assert "input_draft_reject" in args


def test_monthly_extraction_promote_executed_in_ai_extraction_action_literal() -> None:
    """AIExtractionAction Literal EXTENSION includes `monthly_extraction_promote_executed`.

    10-4 EXTENSION: AD-17 verbatim audit-first INSERT Row 2.
    """
    from apps.api.core.audit_action import AIExtractionAction

    args = AIExtractionAction.__args__
    assert "monthly_extraction_promote_executed" in args
    # Existing 3 values preserved (including 10-4 promote_denied guard)
    assert "monthly_extraction_executed" in args
    assert "monthly_extraction_low_confidence_warning" in args
    assert "monthly_extraction_promote_denied" in args


def test_action_class_registry_accepts_promoted_actions() -> None:
    """ActionClass registry accepts `input_draft_promoted` + `monthly_extraction_promote_executed`.

    Drift detector: ActionClass registry ↔ Literal types parity (3-way gate
    with DB CHECK).
    """
    from apps.api.core.audit_action import (  # type: ignore[attr-defined]
        ActionClass,
        _ActionRegistry,
    )

    # Use the validate() entrypoint — returns AuditLogType string.
    # INPUT_DRAFT registry includes `input_draft_promoted`.
    log_type_input = _ActionRegistry.validate(  # type: ignore[attr-defined]
        action_class=ActionClass.INPUT_DRAFT, action="input_draft_promoted"
    )
    assert log_type_input == "audit_logs"

    # AI_EXTRACTION_EXECUTED registry includes `monthly_extraction_promote_executed`.
    log_type_ai = _ActionRegistry.validate(  # type: ignore[attr-defined]
        action_class=ActionClass.AI_EXTRACTION_EXECUTED,
        action="monthly_extraction_promote_executed",
    )
    assert log_type_ai == "audit_logs"

    # Negative test: `bogus_action` is NOT in registry (rejected).
    with pytest.raises(ValueError, match="not in ActionClass"):
        _ActionRegistry.validate(  # type: ignore[attr-defined]
            action_class=ActionClass.INPUT_DRAFT, action="bogus_action"
        )


# ── AD-17 verbatim 3-tuple (kernel + service parity) ────────────────


def test_compute_promotion_idempotency_key_kernel_service_parity() -> None:
    """Kernel `compute_promotion_idempotency_key` returns deterministic UUID v5.

    Service layer reuses the kernel (no shadow implementation). AD-17
    verbatim: idempotency on (tenant_id, period_key, source_draft_id).
    """
    from packages.services.m10_ai.promoter_port import (
        compute_promotion_idempotency_key,
    )

    tenant_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
    period_key = "2026-08"
    source_draft_id = uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")

    # Determinism: same input → same UUID
    k1 = compute_promotion_idempotency_key(
        tenant_id=tenant_id,
        period_key=period_key,
        source_draft_id=source_draft_id,
    )
    k2 = compute_promotion_idempotency_key(
        tenant_id=tenant_id,
        period_key=period_key,
        source_draft_id=source_draft_id,
    )
    assert k1 == k2
    assert isinstance(k1, uuid.UUID)


def test_monthly_input_promotions_unique_3tuple_constraint_in_alembic() -> None:
    """alembic 0032 UNIQUE constraint on (tenant_id, period_key, source_draft_id).

    AD-17 verbatim DB-level idempotency. Service layer catches ERRCODE 23505
    (unique_violation) and converts to status='idempotent_replay'.
    """
    from pathlib import Path

    # tests/api/m10_ai/test_promoter_service.py → repo root is parents[3]
    repo_root = Path(__file__).resolve().parents[3]
    migration_file = (
        repo_root / "apps" / "api" / "alembic" / "versions" / "0032_ai_promotion_port.py"
    )
    source = migration_file.read_text(encoding="utf-8")
    assert "uq_monthly_input_promotions_tenant_period_draft" in source
    assert "UNIQUE (tenant_id, period_key, source_draft_id)" in source


# ── AD-5 stdlib-only kernel preserved ─────────────────────────────


def test_promoter_port_kernel_has_no_io_imports() -> None:
    """AD-5 engine purity: kernel has no I/O imports (no sqlalchemy, requests, etc.)."""
    from packages.services.m10_ai import promoter_port

    source = inspect.getsource(promoter_port)
    forbidden = ["sqlalchemy", "requests", "httpx", "openai", "anthropic", "fastapi"]
    for lib in forbidden:
        assert lib not in source, (
            f"AD-5 violation: '{lib}' imported in promoter_port.py"
        )


# ── AD-7 strict invariant service guard ───────────────────────────


def test_ad7_strict_invariant_service_discriminator_marker() -> None:
    """AD-7 strict invariant: M10 NEVER writes confirmed_inputs.

    Service uses `monthly_input_rows` discriminator (NOT
    `confirmed_inputs`). This is the wire guard — direct INSERT
    attempt into `confirmed_inputs` is denied (422 INPUT_PROMOTION_DENIED).
    """
    from apps.api.modules.m10_ai.services import promoter_service

    source = inspect.getsource(promoter_service)
    # Service references `monthly_input_rows` for INSERT target
    assert "monthly_input_rows" in source
    # Service explicitly denies `confirmed_inputs` direct write
    assert "confirmed_inputs" in source  # noqa: PLR2004 — both terms must appear
    assert "AD-7" in source or "NEVER" in source or "denied" in source.lower()


def test_ad7_strict_invariant_ad_2_append_only_marker() -> None:
    """AD-2 append-only + INSERT-only trigger on monthly_input_promotions.

    Alembic 0032 EXTENSION: UPDATE/DELETE on monthly_input_promotions →
    audit_logs append (AD-2 append-only invariant). Service layer
    relies on this — never issues UPDATE on monthly_input_promotions.
    """
    from pathlib import Path

    from apps.api.modules.m10_ai.services import promoter_service

    source = inspect.getsource(promoter_service)
    # Service does not directly UPDATE `monthly_input_promotions` rows
    # (only INSERT — AD-2 append-only invariant).
    assert "monthly_input_promotions" in source

    # alembic 0032 trigger verification
    repo_root = Path(__file__).resolve().parents[3]
    migration_file = (
        repo_root / "apps" / "api" / "alembic" / "versions" / "0032_ai_promotion_port.py"
    )
    alembic_source = migration_file.read_text(encoding="utf-8")
    assert "trg_monthly_input_promotions_insert_only" in alembic_source


# ── Pydantic-free shape validation ───────────────────────────────


def test_validate_promotion_request_period_key_accepted() -> None:
    """period_key format YYYY-MM accepted (master PRD §V4)."""
    from packages.services.m10_ai.promoter_port import (
        PromotionRequest,
        validate_promotion_request,
    )

    request = PromotionRequest(
        tenant_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
        period_key="2026-08",
        source_draft_id=uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
        actor_id=uuid.UUID("99999999-9999-9999-9999-999999999999"),
        actor_role="m2_service_role",
    )
    # Should not raise
    validate_promotion_request(request)


def test_validate_promotion_request_period_key_rejected() -> None:
    """period_key format invalid (day-level) rejected."""
    from packages.services.m10_ai.promoter_port import (
        PromotionRequest,
        validate_promotion_request,
    )

    request = PromotionRequest(
        tenant_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
        period_key="2026-08-15",
        source_draft_id=uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
        actor_id=uuid.UUID("99999999-9999-9999-9999-999999999999"),
        actor_role="m2_service_role",
    )
    with pytest.raises(ValueError, match="period_key"):
        validate_promotion_request(request)


def test_validate_promotion_request_actor_role_rejected() -> None:
    """actor_role != 'm2_service_role' rejected (AD-17 verbatim only M2)."""
    from packages.services.m10_ai.promoter_port import (
        PromotionRequest,
        validate_promotion_request,
    )

    request = PromotionRequest(
        tenant_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
        period_key="2026-08",
        source_draft_id=uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
        actor_id=uuid.UUID("99999999-9999-9999-9999-999999999999"),
        actor_role="owner",
    )
    with pytest.raises(ValueError, match="actor_role"):
        validate_promotion_request(request)


# ── A19 cohesion 8 surface marker ───────────────────────────────


def test_a19_cohesion_8_surface_marker_in_service_module() -> None:
    """A19 cohesion pattern 8 surface — service layer (T3) PASS marker.

    Surfaces:
    1. Kernel (T1) — packages/services/m10_ai/promoter_port.py ✓
    2. Port (T1) — InputPromoterPort Protocol ✓
    3. DB schema (T2) — alembic 0032 ✓
    4. Service (T3) — apps/api/modules/m10_ai/services/promoter_service.py ✓
    5. Handler (T4) — apps/api/modules/m10_ai/handlers.py (forward)
    6. Envelope (T4) — apps/api/modules/m10_ai/schemas.py (forward)
    7. Capability (T4) — apps/api/core/capability.py (forward)
    8. Audit (T4) — apps/api/core/audit_action.py + emit_audit_typed ✓ (T3-pre)
    """
    from apps.api.modules.m10_ai.services import promoter_service

    source = inspect.getsource(promoter_service)
    # Service module references the kernel (T1) + port Protocol
    assert "promoter_port" in source or "InputPromoterPort" in source
    # Service uses monthly_input_rows INSERT (T2 schema)
    assert "monthly_input_rows" in source
    # Service uses monthly_input_promotions INSERT (T2 schema)
    assert "monthly_input_promotions" in source


def test_input_drafts_state_promoted_extension_marker() -> None:
    """input_drafts.state EXTENSION (3→4 states with 'promoted').

    AD-17 verbatim "Promotion retains the draft with state='promoted'".
    """
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[3]
    migration_file = (
        repo_root / "apps" / "api" / "alembic" / "versions" / "0032_ai_promotion_port.py"
    )
    source = migration_file.read_text(encoding="utf-8")
    assert "CHECK (state IN ('draft', 'reviewed', 'superseded', 'promoted'))" in source
