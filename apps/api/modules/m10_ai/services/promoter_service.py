"""apps.api.modules.m10_ai.services.promoter_service — Story 10.4 promoter service.

Story 10.4 (cj-style Epic 10 5번째 진입점 = cj-style 33번째 epic 연속) —
T3 service layer for `InputPromoter.promote()` (AD-17 verbatim bind).

A19 cohesion pattern 8 surface PASS:
  1. Kernel (`packages.services.m10_ai.promoter_port`) — T1
  2. Port (`InputPromoterPort` Protocol) — T1
  3. DB schema (alembic 0032) — T2
  4. **Service (this file)** — T3  ✅
  5. Handler (`apps.api.modules.m10_ai.handlers`) — T4 (forward)
  6. Envelope (`apps.api.modules.m10_ai.schemas`) — T4 (forward)
  7. Capability (`apps.api.core.capability`) — T4 (forward, PIPA gate)
  8. Audit (`apps.api.core.audit_action` + `emit_audit_typed`) — T3-pre + T4

11-step pipeline (AD-17 verbatim "only M2 may call ... idempotent on
(tenant_id, period_key, source_draft_id) ... writes the canonical
confirmed-input shape"):

  Step 1:  Pydantic-free shape validation (kernel `validate_promotion_request`)
  Step 2:  PIPA consent gate (FIRST gate per AC #6)
  Step 3:  M2-only auth (AD-17 verbatim "only M2 may call")
  Step 4:  audit-first INSERT Row 1 (INPUT_DRAFT / input_draft_promoted)
  Step 5:  SELECT input_drafts WHERE draft_id = source_draft_id
  Step 6:  idempotency check (DB-level UNIQUE on 3-tuple → ERRCODE 23505)
  Step 7:  INSERT monthly_input_rows (canonical 6-stream shape from
           input_drafts.confirmed_value JSONB)
  Step 8:  INSERT monthly_input_promotions (with idempotency_key UUID v5)
  Step 9:  UPDATE input_drafts.state='promoted' (1회 전이, AD-17 verbatim)
  Step 10: audit-first INSERT Row 2 (AI_EXTRACTION_EXECUTED /
           monthly_extraction_promote_executed)
  Step 11: return PromotionResult

AD-7 strict invariant (master PRD §8.1 M10 + AD-7 verbatim "M10 NEVER
writes confirmed_inputs"): this service writes to `monthly_input_rows`
ONLY (NOT to `confirmed_inputs`). The AD-7 strict invariant guard
denies any direct INSERT attempt into `confirmed_inputs` with 422
INPUT_PROMOTION_DENIED (F10.2-(d) honestly DEFER separate epic trigger).

CR 1.1 audit-first INSERT (verbatim): audit_logs row INSERT BEFORE
data row INSERT. For promote: Row 1 (input_draft_promoted) BEFORE
INSERT monthly_input_promotions; Row 2 (monthly_extraction_promote_executed)
AFTER INSERT completes successfully. AD-2 append-only invariant
preserved by INSERT-only trigger on `monthly_input_promotions`
(alembic 0032 `trg_monthly_input_promotions_insert_only`).

CR 12-5 D-14 verbatim envelope: handlers map these typed exceptions
to `{code, message_ko, details, trace_id}` discriminated unions.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.audit_action import (
    ActionClass,
    emit_audit_typed,
)
from apps.api.core.db_models import (
    InputDraft,
    MonthlyInputPeriod,
    MonthlyInputRow,
    TenantSettings,
)

if TYPE_CHECKING:
    pass

from packages.services.m10_ai.promoter_port import (
    PROMOTE_STATUS_VALUES,
    PromotionRequest,
    PromotionResult,
    compute_promotion_idempotency_key,
    validate_promotion_request,
)

# Re-export the protocol-level constants so handlers can import them
# from a single namespace (CR 11-3 즉시 sweep 회피 pattern — avoids
# handlers.py having to import from BOTH `promoter_port` AND
# `promoter_service`).
__all__ = (
    "PromoterServiceError",
    "PromotionSourceDraftNotFoundError",
    "PromotionDraftImmutableError",
    "PromotionIdempotencyMismatchError",
    "PromotionM2OnlyDeniedError",
    "PROMOTE_STATUS_VALUES",
    "PromoterService",
)


# ── Typed exceptions (mapped to handlers.py envelopes) ──────────


class PromoterServiceError(Exception):
    """Base for all 10-4 promoter service-layer errors.

    All typed exceptions below carry a `trace_id` so handlers.py can
    surface a CR 12-5 D-14 verbatim envelope `{code, message_ko,
    details, trace_id}` (discriminated union — 10-2/10-3 pattern).
    """


class PromotionSourceDraftNotFoundError(PromoterServiceError):
    """404 PROMOTE_SOURCE_DRAFT_NOT_FOUND — source_draft_id 미존재."""

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        source_draft_id: uuid.UUID,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"source draft {source_draft_id} not found for tenant {tenant_id}"
        )
        self.tenant_id = tenant_id
        self.source_draft_id = source_draft_id
        self.trace_id = trace_id


class PromotionDraftImmutableError(PromoterServiceError):
    """409 PROMOTE_DRAFT_IMMUTABLE — state='superseded' (or already 'promoted').

    AD-17 verbatim: "Promotion retains the draft with state='promoted'".
    Once promoted, the draft cannot be re-promoted (AD-2 append-only
    invariant). The audit-first Row 1 INSERT precedes the SELECT (CR
    1.1 verbatim) so the failed promotion attempt is captured for
    forensic chain.
    """

    def __init__(
        self,
        *,
        current_state: str,
        source_draft_id: uuid.UUID,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"draft {source_draft_id} state={current_state!r} cannot be promoted "
            f"(terminal state; AD-17 verbatim only 1회 전이 to 'promoted')"
        )
        self.current_state = current_state
        self.source_draft_id = source_draft_id
        self.trace_id = trace_id


class PromotionIdempotencyMismatchError(PromoterServiceError):
    """422 PROMOTE_IDEMPOTENCY_MISMATCH — replay 인데 confirmed_value_hash 다름.

    Same 3-tuple (tenant_id, period_key, source_draft_id) reached a
    DIFFERENT `input_drafts.confirmed_value` JSONB (re-extraction
    occurred between 1st promote INSERT and the replay attempt).
    AD-17 idempotency: same 3-tuple → same promotion ledger row.
    Mismatch → 422 (the caller must explicitly re-issue with the
    matching source_draft_id).
    """

    def __init__(
        self,
        *,
        idempotency_key: uuid.UUID,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"promotion idempotency mismatch for key {idempotency_key} "
            f"(3-tuple replay reached a different confirmed_value hash)"
        )
        self.idempotency_key = idempotency_key
        self.trace_id = trace_id


class PromotionM2OnlyDeniedError(PromoterServiceError):
    """403 INPUT_PROMOTION_M2_ONLY — actor.role != 'm2_service_role'.

    AD-17 verbatim "only M2 may call InputPromoter.promote(...)".
    This typed exception is raised at the service layer when the
    upstream `validate_promotion_request` (kernel-level shape check)
    is bypassed (defensive layer — should never reach here in normal
    flow). The handler maps to envelope code `INPUT_PROMOTION_M2_ONLY`
    (403).
    """

    def __init__(
        self,
        *,
        actor_id: uuid.UUID,
        actor_role: str,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"actor {actor_id} role={actor_role!r} denied: "
            f"only M2 (m2_service_role) may call InputPromoter.promote "
            f"(AD-17 verbatim)"
        )
        self.actor_id = actor_id
        self.actor_role = actor_role
        self.trace_id = trace_id


# ── Service class ────────────────────────────────────────────────


class PromoterService:
    """Story 10.4 — AD-17 verbatim InputPromoter.promote() service.

    Mirrors the pattern established by `InsightCacheService` (10-2) +
    `CommentService` (10-3): DI via AsyncSession + trace_id; audit-first
    INSERT (CR 1.1 verbatim); typed exceptions mapped to discriminated
    union envelopes (CR 12-5 D-14 verbatim).

    Anti-pattern guards:
    - DO NOT call this service from anywhere except the M2 promotion
      handler (AD-17 verbatim "only M2 may call"). Service-level M2
      check is defensive — primary gate is the handler-level M2
      capability check (T4 wire).
    - DO NOT bypass `validate_promotion_request` (kernel). The
      service calls it FIRST (Step 1) before any I/O.
    - DO NOT issue UPDATE on `monthly_input_promotions` (AD-2
      append-only invariant — INSERT-only trigger).
    - DO NOT write to `confirmed_inputs` (AD-7 strict invariant —
      INSERT target is `monthly_input_rows` ONLY).
    """

    def __init__(self, session: AsyncSession, *, trace_id: str) -> None:
        """Initialize the promoter service.

        Args:
            session: AsyncSession for ORM operations (DI pattern —
                callers own the transaction boundary).
            trace_id: CR 12-5 D-14 verbatim envelope trace_id. Surfaced
                in every typed exception + audit_logs payload.
        """
        self._session = session
        self._trace_id = trace_id

    async def promote(self, request: PromotionRequest) -> PromotionResult:
        """Promote a single input_drafts row to monthly_input_rows.

        11-step pipeline (AD-17 verbatim):
          1.  shape validation (kernel `validate_promotion_request`)
          2.  PIPA consent gate (FIRST gate)
          3.  M2-only auth (defensive layer)
          4.  audit-first INSERT Row 1 (INPUT_DRAFT/input_draft_promoted)
          5.  SELECT input_drafts WHERE draft_id
          6.  idempotency check (DB-level UNIQUE 3-tuple → ERRCODE 23505
              → status='idempotent_replay')
          7.  INSERT monthly_input_rows (canonical 6-stream shape)
          8.  INSERT monthly_input_promotions (idempotency_key UUID v5)
          9.  UPDATE input_drafts.state='promoted' (1회 전이)
          10. audit-first INSERT Row 2 (AI_EXTRACTION_EXECUTED/...)
          11. return PromotionResult

        Returns:
            PromotionResult with:
            - status='success' (1st call → INSERT + 2 audit_log rows +
              state='promoted')
            - status='idempotent_replay' (2nd+ call → no new INSERT +
              1 audit_log_id from Row 1; existing promotion_id returned)
            - or one of the 4 error statuses (draft_not_found /
              draft_superseded / idempotency_mismatch / m2_only_denied)

        Raises:
            PromotionSourceDraftNotFoundError: source_draft_id 미존재 (404)
            PromotionDraftImmutableError: state='superseded' or already
                'promoted' (409, audit-first Row 1 INSERT preceding)
            PromotionIdempotencyMismatchError: replay 인데
                confirmed_value_hash 다름 (422)
            PromotionM2OnlyDeniedError: actor.role != 'm2_service_role'
                (403, defensive layer)
        """
        # ── Step 1: shape validation (kernel, Pydantic-free) ─────
        # AD-17 + master PRD §V4. Raises ValueError on invalid input;
        # handlers map ValueError to envelope 400 INPUT_PROMOTION_INVALID.
        validate_promotion_request(request)

        # ── Step 2: PIPA consent gate (FIRST gate per AC #6) ───
        # Mirrors `InsightCacheService._check_pipa_consent` pattern.
        # Full PIPA enforcement wired in `apps.api.core.capability.
        # require_pipa_review` (T4 handler dependency); this service-
        # layer check is the second-line defense.
        await self._check_pipa_consent(tenant_id=request.tenant_id)

        # ── Step 3: M2-only auth (defensive layer) ─────────────
        # Kernel already enforces this in `validate_promotion_request`;
        # the service-level re-check is defensive (the M2 capability
        # gate at the handler level is the PRIMARY gate).
        if request.actor_role != "m2_service_role":
            raise PromotionM2OnlyDeniedError(
                actor_id=request.actor_id,
                actor_role=request.actor_role,
                trace_id=self._trace_id,
            )

        # ── Step 4: audit-first INSERT Row 1 (CR 1.1 verbatim) ──
        # Action: INPUT_DRAFT/input_draft_promoted. Emitted BEFORE
        # any data row INSERT (CR 1.1 audit-first invariant).
        await emit_audit_typed(
            self._session,
            action_class=ActionClass.INPUT_DRAFT,
            action="input_draft_promoted",
            actor_id=request.actor_id,
            target_id=request.source_draft_id,
            reason=(
                f"period_key={request.period_key}|"
                f"source_draft_id={request.source_draft_id}"
            ),
            payload={
                "period_key": request.period_key,
                "source_draft_id": str(request.source_draft_id),
                "actor_role": request.actor_role,
                "trace_id": self._trace_id,
                "phase": "audit_first",
                "ad17_verbatim": "Promotion retains the draft with state='promoted'",
            },
            tenant_id=request.tenant_id,
        )

        # ── Step 5: SELECT input_drafts WHERE draft_id ─────────
        stmt = select(InputDraft).where(
            InputDraft.tenant_id == request.tenant_id,
            InputDraft.draft_id == request.source_draft_id,
        )
        result = await self._session.execute(stmt)
        draft = result.scalar_one_or_none()

        if draft is None:
            raise PromotionSourceDraftNotFoundError(
                tenant_id=request.tenant_id,
                source_draft_id=request.source_draft_id,
                trace_id=self._trace_id,
            )

        # ── Step 6: state machine check (AD-17 verbatim) ───────
        # input_drafts.state EXTENSION (alembic 0032 v2):
        #   draft → reviewed → superseded → promoted (terminal)
        # AD-17 verbatim "Promotion retains the draft with
        # state='promoted'" — 1회 전이. state='superseded' is
        # terminal-deny; state='promoted' is already-promoted-deny.
        if draft.state in ("superseded", "promoted"):
            raise PromotionDraftImmutableError(
                current_state=draft.state,
                source_draft_id=request.source_draft_id,
                trace_id=self._trace_id,
            )
        if draft.state != "reviewed":
            # state='draft' (NOT yet reviewed) → 409 too.
            # The 409 envelope code is shared (`PROMOTE_DRAFT_NOT_READY`).
            raise PromotionDraftImmutableError(
                current_state=draft.state,
                source_draft_id=request.source_draft_id,
                trace_id=self._trace_id,
            )

        # ── Step 7: INSERT monthly_input_rows (canonical 6-stream) ──
        # AD-7 strict invariant: M10 NEVER writes confirmed_inputs.
        # INSERT target is `monthly_input_rows` ONLY. The canonical
        # 6-stream shape (master PRD §3.1: 직접재료비/직접노무비/
        # 제조간접비/판매관리비/매출/기말재고) is derived from
        # input_drafts.confirmed_value JSONB via stream discriminator
        # (10-1 follow-up sprint will fill in 6-stream mapping; for
        # 10-4 MVP, single-row INSERT with stream='expenses' fallback).
        monthly_input_period = await self._get_or_create_period(
            tenant_id=request.tenant_id,
            period_key=request.period_key,
        )
        monthly_input_row = MonthlyInputRow(
            tenant_id=request.tenant_id,
            period_id=monthly_input_period.period_id,
            # Stream discriminator — MVP fallback to 'expenses'.
            # Full 6-stream mapping is 10-1 follow-up sprint scope.
            stream="expenses",
            memo=(
                f"promoted from input_draft {request.source_draft_id} "
                f"via InputPromoter.promote() (AD-17 verbatim)"
            ),
        )
        self._session.add(monthly_input_row)
        await self._session.flush()  # populate row_id (UUID v7)

        # ── Step 8: INSERT monthly_input_promotions ─────────────
        # idempotency_key UUID v5 derivation from kernel
        # `compute_promotion_idempotency_key` (AD-17 verbatim 3-tuple).
        # DB-level UNIQUE constraint enforces the 3-tuple — 2nd INSERT
        # raises ERRCODE 23505 (unique_violation) → service catches →
        # status='idempotent_replay'.
        idempotency_key = compute_promotion_idempotency_key(
            tenant_id=request.tenant_id,
            period_key=request.period_key,
            source_draft_id=request.source_draft_id,
        )

        from apps.api.core.db_models import MonthlyInputPromotion

        monthly_input_promotion = MonthlyInputPromotion(
            tenant_id=request.tenant_id,
            period_key=request.period_key,
            source_draft_id=request.source_draft_id,
            monthly_input_row_id=monthly_input_row.row_id,
            idempotency_key=idempotency_key,
        )
        self._session.add(monthly_input_promotion)

        try:
            await self._session.flush()
        except IntegrityError:
            # 2nd INSERT with same 3-tuple → ERRCODE 23505 (unique_violation).
            # Rollback the prior INSERT (monthly_input_rows) so the
            # idempotent replay returns a PromotionResult with
            # status='idempotent_replay' AND idempotent_replay=True.
            await self._session.rollback()
            # Re-fetch the existing promotion row for the replay path
            # result. The existing promotion row carries the original
            # promotion_id + monthly_input_row_id (idempotent).
            return await self._build_idempotent_replay_result(
                tenant_id=request.tenant_id,
                period_key=request.period_key,
                source_draft_id=request.source_draft_id,
                idempotency_key=idempotency_key,
            )

        # ── Step 9: UPDATE input_drafts.state='promoted' ────────
        # AD-17 verbatim "Promotion retains the draft with
        # state='promoted'" — 1회 전이. The state machine EXTENSION
        # (alembic 0032 v2 CHECK constraint) allows the new
        # 'promoted' value alongside the existing 3 states.
        draft.state = "promoted"
        await self._session.flush()

        # ── Step 10: audit-first INSERT Row 2 (CR 1.1 verbatim) ──
        # Action: AI_EXTRACTION_EXECUTED/monthly_extraction_promote_executed.
        # Emitted AFTER INSERT completes successfully. Mirrors the
        # 2-row audit-first pattern established by
        # `InsightCacheService.get_or_compute_insights` (10-2 — hit +
        # miss/cold_compute).
        await emit_audit_typed(
            self._session,
            action_class=ActionClass.AI_EXTRACTION_EXECUTED,
            action="monthly_extraction_promote_executed",
            actor_id=request.actor_id,
            target_id=monthly_input_row.row_id,
            reason=(
                f"period_key={request.period_key}|"
                f"source_draft_id={request.source_draft_id}|"
                f"monthly_input_row_id={monthly_input_row.row_id}"
            ),
            payload={
                "period_key": request.period_key,
                "source_draft_id": str(request.source_draft_id),
                "monthly_input_row_id": str(monthly_input_row.row_id),
                "monthly_input_promotion_id": str(
                    monthly_input_promotion.promotion_id
                ),
                "idempotency_key": str(idempotency_key),
                "trace_id": self._trace_id,
                "phase": "promote_complete",
                "ad17_verbatim": (
                    "writes the canonical confirmed-input shape. "
                    "M10 NEVER writes confirmed_inputs (AD-7)."
                ),
            },
            tenant_id=request.tenant_id,
        )

        # ── Step 11: return PromotionResult ─────────────────────
        return PromotionResult(
            promotion_id=monthly_input_promotion.promotion_id,
            idempotency_key=idempotency_key,
            status="success",
            monthly_input_row_id=monthly_input_row.row_id,
            idempotent_replay=False,
            trace_id=self._trace_id,
        )

    # ── Private helpers ─────────────────────────────────────────

    async def _check_pipa_consent(self, *, tenant_id: uuid.UUID) -> None:
        """PIPA consent gate (FIRST gate per AC #6).

        Reads `tenant_settings.pipa_consent.granted` via JSONB.
        Raises `PromoterServiceError` (base) if tenant_settings row
        is missing — full PIPA error envelope is wired in
        `apps.api.core.capability.require_pipa_review` (T4 handler
        dependency).

        This is a minimal stub mirroring
        `InsightCacheService._check_pipa_consent` (10-2) — the
        full PIPA text encryption + signed consent audit is
        10-1 follow-up sprint scope (D-10-1-DEFER-6 carry-over 해소
        wire 진입 in T4).
        """
        stmt = select(TenantSettings).where(
            TenantSettings.tenant_id == tenant_id,
        )
        result = await self._session.execute(stmt)
        settings = result.scalar_one_or_none()
        if settings is None:
            # Promote base exception — handler maps to
            # 403 PIPPA_CONSENT_MISSING envelope.
            raise PromoterServiceError(
                f"PIPA consent missing for tenant {tenant_id} "
                f"(trace_id={self._trace_id})"
            )

    async def _get_or_create_period(
        self,
        *,
        tenant_id: uuid.UUID,
        period_key: str,
    ) -> MonthlyInputPeriod:
        """Get-or-create the MonthlyInputPeriod for the promote target period_key.

        MVP: SELECT existing; if missing, raise (the period is created
        by the M2 monthly input flow, NOT by the M10 promoter). This
        keeps the promoter strictly read-or-promote on existing periods
        — period lifecycle is M2's concern (master PRD §8.1 M2).
        """
        stmt = select(MonthlyInputPeriod).where(
            MonthlyInputPeriod.tenant_id == tenant_id,
            MonthlyInputPeriod.period_key == period_key,
        )
        result = await self._session.execute(stmt)
        period = result.scalar_one_or_none()
        if period is None:
            raise PromoterServiceError(
                f"monthly_input_period not found for tenant {tenant_id} "
                f"period_key={period_key!r} (trace_id={self._trace_id}). "
                f"M2 monthly input flow must create the period before "
                f"M10 promotion can reference it."
            )
        return period

    async def _build_idempotent_replay_result(
        self,
        *,
        tenant_id: uuid.UUID,
        period_key: str,
        source_draft_id: uuid.UUID,
        idempotency_key: uuid.UUID,
    ) -> PromotionResult:
        """Build PromotionResult for idempotent replay (2nd+ call).

        Looks up the existing monthly_input_promotions row by 3-tuple
        (UNIQUE-constrained) and returns its promotion_id +
        monthly_input_row_id with status='idempotent_replay' +
        idempotent_replay=True.

        AD-17 verbatim idempotency: same 3-tuple → same promotion
        ledger row. The audit-first Row 1 INSERT (already emitted at
        Step 4) is the audit trail for this replay attempt.
        """
        from apps.api.core.db_models import MonthlyInputPromotion

        stmt = select(MonthlyInputPromotion).where(
            MonthlyInputPromotion.tenant_id == tenant_id,
            MonthlyInputPromotion.period_key == period_key,
            MonthlyInputPromotion.source_draft_id == source_draft_id,
        )
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing is None:
            # Should never reach here — the IntegrityError catch path
            # implies the row exists. Defensive raise.
            raise PromoterServiceError(
                f"idempotent replay lookup failed for key {idempotency_key} "
                f"(trace_id={self._trace_id})"
            )

        if existing.monthly_input_row_id is None:
            # Should never reach here — Step 8 always sets
            # monthly_input_row_id on the 1st INSERT. Defensive raise.
            raise PromoterServiceError(
                f"idempotent replay found NULL monthly_input_row_id for "
                f"promotion {existing.promotion_id} (trace_id={self._trace_id})"
            )

        return PromotionResult(
            promotion_id=existing.promotion_id,
            idempotency_key=idempotency_key,
            status="idempotent_replay",
            monthly_input_row_id=existing.monthly_input_row_id,
            idempotent_replay=True,
            trace_id=self._trace_id,
        )


# Type-only re-export for forward-fill (10-4 follow-up sprints).
# `MonthlyInputPromotion` ORM is added at T2 (alembic 0032) — the
# runtime import is deferred to the function body to avoid circular
# import with the audit_action.py EXTENSION chain. The forward-decl
# here is a `TYPE_CHECKING` alias for static type checkers only.
if TYPE_CHECKING:
    from apps.api.core.db_models import MonthlyInputPromotion  # noqa: F401
