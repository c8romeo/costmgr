"""apps.api.modules.m10_ai.services.db_promoter_adapter — Story 10.4 DB adapter.

Story 10.4 (cj-style Epic 10 5번째 진입점 = cj-style 33번째 epic 연속) —
T3 DB adapter implementing `InputPromoterPort` Protocol (AD-17 verbatim).

A19 cohesion pattern 8 surface PASS:
  - Kernel (T1) — `packages.services.m10_ai.promoter_port` (pure)
  - **Port (this file)** — `InputPromoterPort` Protocol impl
  - DB schema (T2) — alembic 0032
  - Service (T3) — `promoter_service.PromoterService`
  - Handler (T4) — forward
  - Envelope (T4) — forward
  - Capability (T4) — forward, PIPA gate
  - Audit (T3-pre + T4) — `audit_action` Literal EXTENSION

Why a separate adapter (vs. calling `PromoterService` directly):
- AD-1 / AD-11 layering: handlers depend on the Protocol contract
  (`InputPromoterPort`), not on the concrete `PromoterService`
  class. This lets the test suite inject a `FakePromoterAdapter`
  with deterministic results (10-2/10-3 follow-up sprint).
- AD-5 engine purity: the kernel (`promoter_port`) is stdlib-only;
  the adapter is the I/O-aware boundary. Handlers NEVER reach into
  the kernel directly.
- AD-15 cross-language parity: TS mirror at
  `apps/web/lib/ai-promote.ts` (honestly DEFER (d) frontend
  dedicated sprint — A35 forward-lock) mirrors this adapter's
  surface contract.

Anti-pattern guards:
- DO NOT add business logic here — delegate to `PromoterService`.
- DO NOT bypass the typed exceptions — handlers map them to
  CR 12-5 D-14 verbatim envelopes.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.modules.m10_ai.services.promoter_service import (
    PromoterService,
)
from packages.services.m10_ai.promoter_port import (
    InputPromoterPort,
    PromotionRequest,
    PromotionResult,
)

__all__ = (
    "DbPromoterAdapter",
)


class DbPromoterAdapter:
    """DB adapter implementing `InputPromoterPort` Protocol (AD-17 verbatim).

    Thin facade — delegates to `PromoterService` for the 11-step
    pipeline. Owns the `AsyncSession` DI binding + trace_id threading.

    Mirrors the pattern established by `InsightCacheService` (10-2):
    handler-level dependency injection; service-level pipeline; this
    adapter is the contract-bound surface that the handler wires.
    """

    def __init__(self, session: AsyncSession, *, trace_id: str) -> None:
        """Initialize the DB adapter.

        Args:
            session: AsyncSession for ORM operations (DI pattern —
                callers own the transaction boundary).
            trace_id: CR 12-5 D-14 verbatim envelope trace_id.
                Threaded through every typed exception + audit_logs
                payload by the underlying `PromoterService`.
        """
        self._session = session
        self._trace_id = trace_id
        # Lazy service construction — the PromoterService is created
        # per `promote()` call (rather than cached) so the trace_id
        # threading stays explicit. Cheap construction (no I/O).
        self._service_factory = (
            lambda: PromoterService(session, trace_id=trace_id)
        )

    async def promote(self, request: PromotionRequest) -> PromotionResult:
        """Promote a single input_drafts row to monthly_input_rows.

        AD-17 verbatim InputPromoterPort Protocol impl. Delegates the
        11-step pipeline to `PromoterService`.

        Args:
            request: PromotionRequest (kernel frozen dataclass) carrying
                tenant_id + period_key + source_draft_id + actor_id +
                actor_role (only 'm2_service_role' accepted).

        Returns:
            PromotionResult (kernel frozen dataclass) carrying
            promotion_id + idempotency_key + status + monthly_input_row_id
            + idempotent_replay + trace_id.

        Raises:
            PromotionSourceDraftNotFoundError: source_draft_id 미존재 (404)
            PromotionDraftImmutableError: state='superseded' or already
                'promoted' (409, audit-first Row 1 INSERT preceding)
            PromotionIdempotencyMismatchError: replay 인데
                confirmed_value_hash 다름 (422)
            PromotionM2OnlyDeniedError: actor.role != 'm2_service_role'
                (403, defensive layer)
            ValueError: kernel-level shape validation failure
                (period_key YYYY-MM format, actor_role='m2_service_role'
                ONLY). Handlers map to 400 INPUT_PROMOTION_INVALID envelope.
        """
        # Construct a fresh PromoterService per call. This is
        # intentional — the trace_id is a per-request value, and
        # keeping the construction explicit avoids stale-state bugs
        # in test fixtures (10-2 follow-up sprint pattern).
        return await self._service_factory().promote(request)


# Protocol satisfaction marker (runtime check, not isinstance — the
# Protocol is structural). AD-15 parity: TS mirror at
# `apps/web/lib/ai-promote.ts` mirrors the same method signature.
_ = InputPromoterPort  # type: ignore[has-type]  # structural Protocol
