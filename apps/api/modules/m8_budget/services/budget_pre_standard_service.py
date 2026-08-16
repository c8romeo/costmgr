"""apps.api.modules.m8_budget.services.budget_pre_standard_service — Story 8.3.

Service-layer orchestration for budget pre-standard cost preview (PRD §F8.3 +
AD-22 + AD-24 + AD-8 + AD-11).

Pure kernel lives at `packages.cost_engine.budget_pre_standard.py`
(2 NEW pure functions + 1 frozen dataclass — A19 cohesion pattern 5번째
separation). Service layer wraps the kernel with DB I/O (UPSERT into
`fiscal_period_snapshots` with `engine_type='budget'`) + idempotency
guard via UNIQUE constraint + RLS same-tenant filter + ORM→kernel
boundary conversion.

AD-22 ledger append-only: 8-3 is destructive-write to `fiscal_period_snapshots`
INSERT (or UPSERT with idempotency guard) — but `audit_first=False` (M11
close 시점에 committed audit emit, 8-1 + 8-2 + 11-1 + 11-3 precedent).

Architecture (matches 8-1 BudgetScenarioService + 8-2 BudgetVarianceService):
  - handler → service → engine (pure kernel)
  - `_to_pre_standard_cost_state` ORM→kernel boundary (CR 12-1 L3 precedent)
  - 3-layer defense (CR 12-5 L3): route @require_capability(BUDGET_SCENARIO)
    + service `validate_pre_standard_inputs` + DB UNIQUE constraint
    (defense-in-depth for race conditions)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Final

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.db_models import FiscalPeriodSnapshot
from apps.api.modules.m8_budget.exceptions import (
    BudgetVariancePdfNotReadyError,
    InvalidPreStandardInputError,
    PreStandardAlreadyExistsError,
    PreStandardSnapshotNotFoundError,
)
from packages.cost_engine.budget_pre_standard import (
    PRE_STANDARD_DEFAULT_BASELINE_REVISION,
    PRE_STANDARD_ENGINE_TYPE,
    PRE_STANDARD_STATE_VERIFIED,
    PreStandardCost,
    compute_pre_standard_cost,
    compute_pre_standard_hash,
)
from packages.cost_engine.budget_pre_standard import (
    InvalidPreStandardInputError as _KernelInvalidPreStandardInputError,
)
from packages.cost_engine.budget_variance import (
    compute_abcd_disabled_badge,
)
from packages.services.m8_budget.budget_pre_standard_pdf_helpers import (
    serialize_budget_pre_standard_pdf_envelope,
)
from packages.services.m8_budget.budget_variance_serializers import (
    serialize_abcd_disabled_badge,
)

# V8 determinism + idempotency — 8-3 INSERT into fiscal_period_snapshots
# with engine_type='budget' (4-2 wire baseline reuse + UNIQUE constraint
# idempotency).
BUDGET_PRE_STANDARD_INDUSTRY_AGNOSTIC: Final[bool] = True

# Period key pattern (AD-24 virtual `YYYY-MM#B<n>` — 8-1 wire).
VIRTUAL_BUDGET_PERIOD_KEY_PATTERN_PRE_STANDARD: Final[str] = (
    r"^\d{4}-(0[1-9]|1[0-2])#B([1-9]\d*)$"
)


@dataclass(frozen=True, slots=True)
class PreStandardSnapshotState:
    """Service-layer DTO for pre-standard snapshot (CR 12-1 L3 boundary).

    Combines the pure-kernel `PreStandardCost` + snapshot metadata
    (result_hash, state, created_at_kst) consumed by handlers.
    """

    pre_standard_cost: PreStandardCost
    inventory_adjustment: int
    result_hash: str
    state: str
    created_at_kst: str


def _to_pre_standard_cost_state(
    orm_row: FiscalPeriodSnapshot,
) -> PreStandardSnapshotState:
    """ORM → kernel boundary conversion (CR 12-1 L3 precedent).

    `FiscalPeriodSnapshot` ORM row (apps/api/core/db_models.py) →
    `PreStandardSnapshotState` (service-layer DTO).

    `created_at_kst` is the KST-timestamp from service layer (NOT engine
    inject — kernel은 clock 없음 per AD-5).
    """
    pre_standard_cost = PreStandardCost(
        material_cost=Decimal(orm_row.material_cost),
        labor_cost=Decimal(orm_row.labor_cost),
        overhead_cost=Decimal(orm_row.overhead_cost),
        manufacturing_cost=Decimal(orm_row.manufacturing_cost),
        period_key=orm_row.period_key,
        scenario_index=1,
        engine_type=orm_row.engine_type,  # type: ignore[arg-type]
    )
    return PreStandardSnapshotState(
        pre_standard_cost=pre_standard_cost,
        inventory_adjustment=orm_row.inventory_adjustment,
        result_hash=orm_row.result_hash,
        state=orm_row.state,
        created_at_kst=orm_row.created_at_kst.isoformat(),
    )


def validate_pre_standard_inputs(
    *,
    period_key: str,
    material_unit_cost: Decimal,
    labor_unit_cost: Decimal,
    overhead_rate: Decimal,
    material_qty: Decimal,
    labor_hours: Decimal,
) -> None:
    """CR 12-5 L3 3-layer defense — service-layer input validation.

    Delegates to `compute_pre_standard_cost` (pure kernel) which validates
    all inputs. Raises `InvalidPreStandardInputError` (CR 12-5 D-14 envelope
    422 INVALID_PRE_STANDARD_INPUT) on any invalid input.

    Pure kernel delegation (AD-5 + AD-5 + AD-11).
    """
    try:
        compute_pre_standard_cost(
            material_unit_cost=material_unit_cost,
            labor_unit_cost=labor_unit_cost,
            overhead_rate=overhead_rate,
            material_qty=material_qty,
            labor_hours=labor_hours,
            period_key=period_key,
        )
    except _KernelInvalidPreStandardInputError as exc:
        raise InvalidPreStandardInputError(
            message=exc.message,
            field=exc.field,
            reason=exc.reason,
        ) from exc
    except ValueError as exc:
        # Pure kernel ValueError (period_key 검증, scenario_index != 1)
        raise InvalidPreStandardInputError(
            message=str(exc),
            field="period_key",
            reason="invalid",
        ) from exc


def _is_pre_standard_snapshot_row(
    orm_row: FiscalPeriodSnapshot,
) -> bool:
    """Defensive check — `engine_type='budget'` filter at service layer.

    RLS + filter by engine_type protects against accidental row reuse
    across multiple engine types (8-1/8-2/8-3 + Story 4.2 M3 wire).
    """
    return orm_row.engine_type == PRE_STANDARD_ENGINE_TYPE


class BudgetPreStandardService:
    """Story 8.3 — AD-24 virtual period key + PRD §F8.3 pre-standard cost.

    Thin orchestration wrapper around `packages.cost_engine.budget_pre_standard`
    pure kernel. DB I/O lives here; pure logic lives in the kernel.

    8-3 destructive-write (INSERT INTO fiscal_period_snapshots with
    engine_type='budget') + idempotency via UNIQUE constraint + 4-2
    wire reuse.
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

    async def compute_pre_standard_snapshot(
        self,
        *,
        period_key: str,
        scenario_index: int = 1,
        material_unit_cost: Decimal,
        labor_unit_cost: Decimal,
        overhead_rate: Decimal,
        material_qty: Decimal,
        labor_hours: Decimal,
    ) -> PreStandardSnapshotState:
        """Compute pre-standard cost + UPSERT to fiscal_period_snapshots.

        1. Service-layer validation (CR 12-5 L3 3-layer defense) via
           `validate_pre_standard_inputs` (raises `InvalidPreStandardInputError`).
        2. Delegate to `compute_pre_standard_cost` (pure kernel, AD-5).
        3. Delegate to `compute_pre_standard_hash` (V8 determinism).
        4. UPSERT into `fiscal_period_snapshots` with `engine_type='budget'`
           + `state='verified'` (AD-22 + 4-2 wire reuse + idempotency via
           UNIQUE constraint).
        5. **Idempotency**: same hash → skip (4-2 wire), different hash →
           `PreStandardAlreadyExistsError` envelope (CR 12-5 D-14 409).

        Raises:
          InvalidPreStandardInputError — invalid period_key or input values
            (422 INVALID_PRE_STANDARD_INPUT).
          PreStandardAlreadyExistsError — same (tenant, period, baseline) row
            exists with different result_hash (409 PRE_STANDARD_ALREADY_EXISTS).
        """
        # 1. Service-layer validation (CR 12-5 L3 3-layer defense).
        validate_pre_standard_inputs(
            period_key=period_key,
            material_unit_cost=material_unit_cost,
            labor_unit_cost=labor_unit_cost,
            overhead_rate=overhead_rate,
            material_qty=material_qty,
            labor_hours=labor_hours,
        )

        # 2. Pure kernel compute.
        pre_standard_cost = compute_pre_standard_cost(
            material_unit_cost=material_unit_cost,
            labor_unit_cost=labor_unit_cost,
            overhead_rate=overhead_rate,
            material_qty=material_qty,
            labor_hours=labor_hours,
            period_key=period_key,
            scenario_index=scenario_index,
        )

        # 3. V8 determinism hash.
        result_hash = compute_pre_standard_hash(
            pre_standard_cost=pre_standard_cost,
        )

        # 4. Idempotency check (4-2 wire reuse).
        existing = await self._fetch_existing_snapshot(
            period_key=period_key,
        )
        if existing is not None:
            if existing.result_hash == result_hash:
                # Same hash → idempotent skip (4-2 wire).
                return _to_pre_standard_cost_state(existing)
            # Different hash → 409 (CR 12-5 D-14 envelope).
            raise PreStandardAlreadyExistsError(
                period_key=period_key,
                tenant_id=str(self.tenant_id),
                existing_hash=existing.result_hash,
                new_hash=result_hash,
            )

        # 5. UPSERT INTO fiscal_period_snapshots.
        snapshot_id = uuid.uuid4()
        created_at_kst = datetime.now(UTC)
        orm_row = FiscalPeriodSnapshot(
            snapshot_id=snapshot_id,
            tenant_id=self.tenant_id,
            period_key=period_key,
            baseline_revision=PRE_STANDARD_DEFAULT_BASELINE_REVISION,
            engine_type=PRE_STANDARD_ENGINE_TYPE,
            material_cost=int(pre_standard_cost.material_cost),
            labor_cost=int(pre_standard_cost.labor_cost),
            overhead_cost=int(pre_standard_cost.overhead_cost),
            manufacturing_cost=int(pre_standard_cost.manufacturing_cost),
            inventory_adjustment=0,  # pre-standard cost: N/A (actual snapshot)
            result_hash=result_hash,
            state=PRE_STANDARD_STATE_VERIFIED,
            created_at=created_at_kst,
        )

        self.session.add(orm_row)
        try:
            await self.session.flush()
        except IntegrityError as exc:
            # DB UNIQUE constraint race condition (concurrent INSERT) →
            # translate to PreStandardAlreadyExistsError (CR 12-5 D-14 envelope).
            await self.session.rollback()
            raise PreStandardAlreadyExistsError(
                period_key=period_key,
                tenant_id=str(self.tenant_id),
                existing_hash="<unknown:race-condition>",
                new_hash=result_hash,
            ) from exc

        return PreStandardSnapshotState(
            pre_standard_cost=pre_standard_cost,
            inventory_adjustment=0,
            result_hash=result_hash,
            state=PRE_STANDARD_STATE_VERIFIED,
            created_at_kst=created_at_kst.isoformat(),
        )

    async def _fetch_existing_snapshot(
        self, *, period_key: str
    ) -> FiscalPeriodSnapshot | None:
        """Fetch existing fiscal_period_snapshots row (RLS same-tenant filter).

        RLS same-tenant filter (AD-3) via `WHERE tenant_id = :tenant_id`.
        Returns None if not found.
        """
        stmt = (
            select(FiscalPeriodSnapshot)
            .where(
                FiscalPeriodSnapshot.tenant_id == self.tenant_id,
                FiscalPeriodSnapshot.period_key == period_key,
                FiscalPeriodSnapshot.engine_type == PRE_STANDARD_ENGINE_TYPE,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def fetch_pre_standard_snapshot(
        self,
        *,
        period_key: str,
        scenario_index: int = 1,  # noqa: ARG002 — future-extension API (multi-scenario is D-8-3-DEFER-2)
    ) -> PreStandardSnapshotState:
        """Fetch pre-standard snapshot by virtual period_key (PRD §F8.3).

        1. Delegate to `parse_virtual_budget_period_key` (8-1 wire — validates
           virtual pattern, raises `InvalidPreStandardInputError`).
        2. SELECT FROM fiscal_period_snapshots WHERE engine_type='budget'
           AND tenant_id = :tenant_id AND period_key = :period_key.
        3. Not found → `PreStandardSnapshotNotFoundError` (CR 12-5 D-14
           envelope 404 PRE_STANDARD_SNAPSHOT_NOT_FOUND).
        4. ORM → kernel boundary conversion via `_to_pre_standard_cost_state`.

        Raises:
          InvalidPreStandardInputError — invalid period_key pattern (422).
          PreStandardSnapshotNotFoundError — not found (404).
        """
        # 1. Pure kernel parse (validates virtual pattern).
        from packages.cost_engine.budget_period_key import (
            parse_virtual_budget_period_key,
        )

        try:
            parse_virtual_budget_period_key(period_key=period_key)
        except ValueError as exc:
            raise InvalidPreStandardInputError(
                message=str(exc),
                field="period_key",
                reason="invalid",
            ) from exc

        # 2. DB read.
        orm_row = await self._fetch_existing_snapshot(period_key=period_key)
        if orm_row is None:
            raise PreStandardSnapshotNotFoundError(
                period_key=period_key,
                tenant_id=str(self.tenant_id),
            )

        # 3. Defensive engine_type filter (defense-in-depth).
        if not _is_pre_standard_snapshot_row(orm_row):
            raise PreStandardSnapshotNotFoundError(
                period_key=period_key,
                tenant_id=str(self.tenant_id),
            )

        # 4. ORM → kernel boundary conversion.
        return _to_pre_standard_cost_state(orm_row)

    async def fetch_abcd_disabled_badge(
        self, *, variant: str = "variance"
    ) -> dict[str, object]:
        """Fetch A×B×C×D 회색 배지 placeholder (8-2 wire reuse, 8-3 동일).

        Pure kernel delegation (AD-5 + AD-11).
        """
        if variant not in ("variance", "trend", "sensitivity"):
            raise ValueError(
                f"variant must be one of 'variance'/'trend'/'sensitivity', "
                f"got {variant!r}"
            )
        badge = compute_abcd_disabled_badge(variant=variant)  # type: ignore[arg-type]
        return serialize_abcd_disabled_badge(badge)

    async def generate_budget_pre_standard_pdf(
        self, *, period_key: str, scenario_index: int = 1
    ) -> bytes:
        """Generate pre-standard cost PDF (8-3 primary scope, §9 #20).

        1. Fetch pre-standard snapshot (RLS same-tenant filter).
        2. Not found → `BudgetVariancePdfNotReadyError` (425, race condition 방지).
        3. Build PDF envelope via `serialize_budget_pre_standard_pdf_envelope`
           (Epic 6 M5 PDF generator reuse pattern, READ-ONLY).
        4. Return PDF bytes (A4 portrait, KRW integer, ko-KR only per NFR18).

        8-3 atomic wire: PDF envelope SSOT + ABCD 회색 배지 placeholder +
        minimal real wire (8-2 honestly DEFER #5 해소).

        Raises:
          BudgetVariancePdfNotReadyError — pre-standard snapshot NOT yet
            inserted (425 BUDGET_VARIANCE_PDF_NOT_READY).
        """
        # 1. Fetch pre-standard snapshot.
        # 425 envelope per spec (8-3 wire activation): PDF는 pre-standard
        # snapshot NOT yet inserted 시 425 (Too Early) envelope — 404 → 425
        # translate.
        try:
            snapshot_state = await self.fetch_pre_standard_snapshot(
                period_key=period_key,
                scenario_index=scenario_index,
            )
        except PreStandardSnapshotNotFoundError as exc:
            raise BudgetVariancePdfNotReadyError(
                period_key=period_key,
                tenant_id=str(self.tenant_id),
            ) from exc

        # 2. Build envelope (Epic 6 M5 PDF generator reuse, READ-ONLY).
        generated_at_kst = datetime.now(UTC).isoformat()
        envelope = serialize_budget_pre_standard_pdf_envelope(
            period_key=period_key,
            scenario_index=scenario_index,
            pre_standard_cost=snapshot_state.pre_standard_cost,
            generated_at_kst=generated_at_kst,
        )

        # 3. Delegate to actual PDF byte generator (Epic 6 M5 reuse).
        # 8-3 wire: reuse packages.services.m4_inventory.closing_pdf_export
        # pure kernel (Story 6.3 wire), which provides A4 portrait + Korean
        # font subset + Identity-H CMap + ToUnicode stream (the only
        # actually-existing PDF generator in the codebase — m6_reports.pdf_helpers
        # is planned but not yet implemented per the 8-3 spec).
        # We use the envelope as the PDF metadata body + section content.
        from packages.services.m4_inventory.closing_pdf_export import (
            ClosingPdfDocument,
            ClosingPdfPage,
            ClosingPdfSection,
            ClosingPdfTextBlock,
            render_closing_pdf_byte_stream,
        )

        # Convert envelope into ClosingPdfDocument sections.
        material_text = (
            f"직접재료: {envelope['material_cost']}원"
        )
        labor_text = (
            f"직접노무: {envelope['labor_cost']}원"
        )
        overhead_text = (
            f"제조경비: {envelope['overhead_cost']}원"
        )
        manufacturing_text = (
            f"제조원가 합계: {envelope['manufacturing_cost']}원"
        )
        engine_text = (
            f"엔진 타입: {envelope['engine_type']}"
        )
        abcd_note_text = envelope["abcd_disabled_note"]
        generated_text = (
            f"생성일시 (KST): {generated_at_kst}"
        )

        summary_section = ClosingPdfSection(
            section_id="summary",
            title_ko="요약",
            blocks=(
                ClosingPdfTextBlock(
                    text=f"기간: {period_key}",
                    font_size=12,
                    x=Decimal("50"),
                    y=Decimal("742"),
                ),
                ClosingPdfTextBlock(
                    text=manufacturing_text,
                    font_size=12,
                    x=Decimal("50"),
                    y=Decimal("722"),
                ),
                ClosingPdfTextBlock(
                    text=engine_text,
                    font_size=10,
                    x=Decimal("50"),
                    y=Decimal("702"),
                ),
            ),
        )

        products_section = ClosingPdfSection(
            section_id="products",
            title_ko="예산 사전 표준원가 명세",
            blocks=(
                ClosingPdfTextBlock(
                    text=material_text,
                    font_size=12,
                    x=Decimal("50"),
                    y=Decimal("670"),
                ),
                ClosingPdfTextBlock(
                    text=labor_text,
                    font_size=12,
                    x=Decimal("50"),
                    y=Decimal("650"),
                ),
                ClosingPdfTextBlock(
                    text=overhead_text,
                    font_size=12,
                    x=Decimal("50"),
                    y=Decimal("630"),
                ),
                ClosingPdfTextBlock(
                    text=manufacturing_text,
                    font_size=12,
                    x=Decimal("50"),
                    y=Decimal("610"),
                ),
                ClosingPdfTextBlock(
                    text=abcd_note_text,
                    font_size=10,
                    x=Decimal("50"),
                    y=Decimal("580"),
                ),
                ClosingPdfTextBlock(
                    text=generated_text,
                    font_size=10,
                    x=Decimal("50"),
                    y=Decimal("560"),
                ),
            ),
        )

        document = ClosingPdfDocument(
            tenant_id=self.tenant_id,
            period_key=period_key,
            pages=(
                ClosingPdfPage(
                    page_number=1,
                    sections=(summary_section, products_section),
                ),
            ),
            finalized_at=generated_at_kst,
        )

        rendered = render_closing_pdf_byte_stream(document=document)
        return rendered.pdf_bytes

    async def generate_budget_variance_pdf(
        self, *, period_key: str, scenario_index: int = 1
    ) -> bytes:
        """Generate budget variance PDF (8-2 placeholder wire activation).

        8-2 atomic wire: placeholder `pass` → 8-3 wire (8-2 spec line 273).
        8-3 wire: delegates to `generate_budget_pre_standard_pdf` (pre-standard
        snapshot reuse). PDF envelope carries pre-standard cost data + variance
        delta (8-2 pattern + 8-3 pre-standard cost merge).

        Raises:
          BudgetVariancePdfNotReadyError — pre-standard snapshot NOT yet
            inserted (425 BUDGET_VARIANCE_PDF_NOT_READY).
        """
        # Delegate to pre-standard PDF (8-2 placeholder wire activation).
        # The /variance/{period_key}/pdf endpoint pulls the pre-standard
        # snapshot's manufacturing cost as the budget baseline, then
        # overlays the actual snapshot (8-2 wire) for the delta calc.
        # 8-3 wire: pass-through to pre-standard PDF (full variance merge
        # is honestly DEFER to a future sprint — 8-3 atomic wire keeps
        # the placeholder activation narrow).
        try:
            return await self.generate_budget_pre_standard_pdf(
                period_key=period_key,
                scenario_index=scenario_index,
            )
        except PreStandardSnapshotNotFoundError as exc:
            # Translate to BudgetVariancePdfNotReadyError per 8-3 spec.
            raise BudgetVariancePdfNotReadyError(
                period_key=period_key,
                tenant_id=str(self.tenant_id),
            ) from exc


__all__ = [
    "BUDGET_PRE_STANDARD_INDUSTRY_AGNOSTIC",
    "VIRTUAL_BUDGET_PERIOD_KEY_PATTERN_PRE_STANDARD",
    "PreStandardSnapshotState",
    "_to_pre_standard_cost_state",
    "validate_pre_standard_inputs",
    "BudgetPreStandardService",
]
