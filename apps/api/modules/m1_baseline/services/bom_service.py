"""apps.api.modules.m1_baseline.services.bom_service — BOM matrix CRUD (Story 2.2).

Writes/reads on the ``bom_lines`` table (PRD §8.M1(b), §6.1(1)). All
state-changing operations write a typed ``audit_logs`` row BEFORE the
data write (AD-2 audit-first).

Layering (AD-1 / AD-11):
- Pure helpers live in ``packages/services/m1_baseline/bom_validation.py``.
- This module wires them to SQLAlchemy + FastAPI dependencies.
- It does NOT import ``packages.cost_engine`` (AD-11 layer rule).

CR 2.1 lesson (100% invariant):
- **No per-row POST/PATCH/DELETE endpoints**. The 100% invariant must
  hold atomically across the entire BOM. Per-row add/remove would let
  the BOM dip below 100% temporarily. The only mutation paths are:
  - ``set_bom`` — bulk replace (PUT semantics)
  - ``clear_bom`` — clear all rows for a parent
- Both are atomic (single transaction; DELETE then INSERT in `set_bom`).

Money typing (AD-8) extended to ratio:
- ``ratio`` is ``NUMERIC(7,4)``. Python ``Decimal``. ``ROUND_HALF_EVEN``
  (Story 0.4 chunk-B). The Pydantic schema enforces `max_digits=7,
  decimal_places=4`; the service still calls ``quantize_ratio`` as
  defense-in-depth (AD-15 §4 error envelope).

Audit-first (AD-2):
- ``emit_audit_typed()`` is called BEFORE the DELETE/INSERT with ``flush=True``.
- The audit row records the full snapshot diff (AC #3:
  ``changed_ratios=[{child_product_id, before, after}, ...]``).
- ``idempotent no-op skip`` is honored when the new payload exactly
  equals the stored state (no audit row). The first write (where stored
  was empty) MUST emit an audit row — the service distinguishes the two.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


def _bom_unique_constraint_name_in(orig: object) -> str | None:
    """M10 (Review): extract the constraint name from a 23505 error.

    Returns the constraint name (e.g. ``"uq_bom_lines_tenant_parent_child"``)
    when present, else ``None``. Falls back to a substring scan against the
    stringified error as a last resort.
    """
    diag = getattr(orig, "diag", None)
    if diag is not None:
        name = getattr(diag, "constraint_name", None)
        if isinstance(name, str) and name:
            return name
    s = str(orig)
    if "uq_bom_lines_tenant_parent_child" in s:
        return "uq_bom_lines_tenant_parent_child"
    return None


from apps.api.core.audit_action import ActionClass, emit_audit_typed  # noqa: E402
from apps.api.core.db_models import BOMLine, Product  # noqa: E402
from apps.api.modules.m1_baseline.schemas import (  # noqa: E402
    BOMLineResponse,
    BOMResponse,
    BOMSetRequest,
)
from packages.common.uuid7 import uuid7 as _uuid7  # noqa: E402
from packages.services.m1_baseline.bom_validation import (  # noqa: E402
    TARGET_TOTAL,
    quantize_ratio,
    sum_ratios,
)
from packages.services.m1_baseline.schemas import (  # noqa: E402
    ProductType,
    is_valid_bom_child,
    is_valid_bom_parent,
)


# ── Typed exceptions (mapped to HTTP by handlers.py) ────────
class BOMParentNotFoundError(Exception):
    """404 BOM_PARENT_NOT_FOUND — parent product does not exist for tenant.

    Mirrors `ProductNotFoundError` from Story 2.1 (AC #5). RLS-scoped;
    the parent lookup returns None even if the row exists for another
    tenant.
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        parent_product_id: uuid.UUID,
        trace_id: str,
    ) -> None:
        super().__init__(f"bom parent {parent_product_id!s} not found for tenant {tenant_id!s}")
        self.tenant_id = tenant_id
        self.parent_product_id = parent_product_id
        self.trace_id = trace_id


class BOMInvalidParentTypeError(Exception):
    """422 BOM_INVALID_PARENT_TYPE — parent is not in {product, semi_product}.

    Per AC #6 / PRD §6.1 — `material` is the BOM leaf; `goods` and
    `service` have no sub-components.
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        parent_product_id: uuid.UUID,
        parent_type: ProductType,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"parent {parent_product_id!s} type {parent_type.value!r} " f"is not a valid BOM parent"
        )
        self.tenant_id = tenant_id
        self.parent_product_id = parent_product_id
        self.parent_type = parent_type
        self.trace_id = trace_id


class BOMInvalidChildTypeError(Exception):
    """422 BOM_INVALID_CHILD_TYPE — child is not in {material, semi_product}.

    Per AC #5 / PRD §6.1(1) — only `material` and `semi_product`
    participate in BOM rollups.
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        child_product_id: uuid.UUID,
        child_type: ProductType,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"child {child_product_id!s} type {child_type.value!r} " f"is not a valid BOM child"
        )
        self.tenant_id = tenant_id
        self.child_product_id = child_product_id
        self.child_type = child_type
        self.trace_id = trace_id


class BOMDuplicateChildError(Exception):
    """422 BOM_DUPLICATE_CHILD — same child_product_id appears twice in PUT payload.

    Per AC #7. Pre-validated in the service (before INSERT) so the
    caller gets a typed 422 rather than a 23505 → 500.
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        duplicate_child_product_id: uuid.UUID,
        occurrences: int,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"child {duplicate_child_product_id!s} appears {occurrences} times in BOM payload"
        )
        self.tenant_id = tenant_id
        self.duplicate_child_product_id = duplicate_child_product_id
        self.occurrences = occurrences
        self.trace_id = trace_id


class BOMInvalidRatioError(Exception):
    """422 BOM_INVALID_RATIO — a ratio fails the service-level range check.

    Defense-in-depth — Pydantic v2 should catch this at the wire
    boundary (gt=0, le=100, max_digits=7, decimal_places=4). If a caller
    bypasses Pydantic, the service still rejects.
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        child_product_id: uuid.UUID,
        ratio: Decimal,
        max_decimal_places: int = 4,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"child {child_product_id!s} ratio {ratio!s} has more than "
            f"{max_decimal_places} decimal places or is out of range"
        )
        self.tenant_id = tenant_id
        self.child_product_id = child_product_id
        self.ratio = ratio
        self.max_decimal_places = max_decimal_places
        self.trace_id = trace_id


class BOMChildNotFoundError(Exception):
    """404 BOM_CHILD_NOT_FOUND — a child product referenced in the BOM does not exist.

    L6 (Review): previously mis-reported as `BOMParentNotFoundError` with
    the child ID in `parent_product_id`, misleading the client. The actual
    missing entity is the child.
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        child_product_id: uuid.UUID,
        parent_product_id: uuid.UUID,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"bom child {child_product_id!s} not found for tenant {tenant_id!s} "
            f"(under parent {parent_product_id!s})"
        )
        self.tenant_id = tenant_id
        self.child_product_id = child_product_id
        self.parent_product_id = parent_product_id
        self.trace_id = trace_id


# ── Service ──────────────────────────────────────────────────
class BOMService:
    """Stateless service-layer facade for BOM matrix CRUD.

    Mirrors `ProductService` (Story 2.1). One instance per request —
    the caller (handlers.py) owns the session lifecycle.
    """

    def __init__(self, session: AsyncSession, *, trace_id: str | None = None) -> None:
        self.session = session
        self.trace_id = trace_id or str(uuid.uuid4())

    # ── get_bom ───────────────────────────────────────────────
    async def get_bom(
        self,
        *,
        tenant_id: uuid.UUID,
        parent_product_id: uuid.UUID,
    ) -> BOMResponse:
        """Return the full BOM (lines + computed totals) for a parent.

        AC #1 — RLS-scoped read. The parent must exist AND be visible to
        the tenant (RLS filters out other-tenant rows automatically).

        `is_complete` and `missing_ratio` are **derived** at read time
        via the pure helpers in `packages.services.m1_baseline.bom_validation`.
        """
        parent = await self._load_parent(tenant_id=tenant_id, parent_product_id=parent_product_id)

        # Eager-load child products for denormalized BOMLineResponse.
        # `selectinload` is the right choice — there's no FK relationship
        # on the ORM (only FK constraints on the table), so we use a
        # second query keyed by the child IDs in the result.
        lines_stmt = (
            select(BOMLine)
            .where(
                BOMLine.tenant_id == tenant_id,
                BOMLine.parent_product_id == parent_product_id,
            )
            .order_by(BOMLine.created_at.asc())  # stable for the matrix UI
        )
        lines_result = await self.session.execute(lines_stmt)
        bom_rows = list(lines_result.scalars().all())

        # Batch-load child products in one round-trip.
        child_ids = [r.child_product_id for r in bom_rows]
        children_by_id: dict[uuid.UUID, Product] = {}
        if child_ids:
            children_stmt = select(Product).where(
                Product.tenant_id == tenant_id,
                Product.id.in_(child_ids),
            )
            children_result = await self.session.execute(children_stmt)
            children_by_id = {p.id: p for p in children_result.scalars().all()}

        # Compute derived totals.
        ratios: list[Decimal] = [r.ratio for r in bom_rows]
        total = sum_ratios(ratios)
        # missing = max(100 - total, 0). Pure helper handles the clamp.
        from packages.services.m1_baseline.bom_validation import (
            missing_to_complete as _missing_to_complete,
        )

        missing = _missing_to_complete(ratios)
        is_complete = total == TARGET_TOTAL

        line_responses = [
            self._bom_line_to_response(row, children_by_id.get(row.child_product_id))
            for row in bom_rows
        ]
        # The `updated_at` of the BOM = max(updated_at) across lines, or None
        # if empty.
        last_updated = max((r.updated_at for r in bom_rows), default=None)

        return BOMResponse(
            parent_product_id=parent.id,
            parent_code=parent.code,
            parent_name=parent.name,
            parent_product_type=ProductType(parent.product_type),
            parent_is_active=parent.is_active,
            lines=line_responses,
            total_ratio=total,
            is_complete=is_complete,
            missing_ratio=missing,
            updated_at=last_updated,
        )

    # ── set_bom (bulk replace) ────────────────────────────────
    async def set_bom(
        self,
        *,
        tenant_id: uuid.UUID,
        actor_id: uuid.UUID,
        parent_product_id: uuid.UUID,
        body: BOMSetRequest,
    ) -> BOMResponse:
        """Bulk-replace the BOM atomically (AC #2/AC #3).

        Steps:
        1. Load + validate parent (AC #6).
        2. Pre-validate duplicate children (AC #7) — typed 422 BEFORE INSERT.
        3. Load + validate child types (AC #5).
        4. Quantize each ratio via `quantize_ratio` (AD-8 + Story 0.4
           chunk-B Decimal.set parity). Pydantic should have caught
           invalid ratios, but defense-in-depth.
        5. **Atomic transaction**: DELETE existing rows for
           `(tenant_id, parent_product_id)` + INSERT new rows.
        6. Audit-first (AD-2): write `bom_set` audit row BEFORE the
           DELETE/INSERT. Payload includes `child_count`,
           `total_ratio`, `is_complete`, `changed_ratios`.
        7. Flush + return refreshed BOMResponse.

        CR 2.1 lesson (idempotent no-op audit skip): if the new payload
        exactly equals the stored state (same children, same ratios), the
        service returns the existing BOM WITHOUT emitting an audit row.
        The first write (where stored was empty) always emits.

        CR 2.1 lesson (100% invariant atomic): the DELETE + INSERT are
        in a single transaction. If INSERT fails (e.g., race breaks the
        UNIQUE), the DELETE rolls back too. The audit row stays via
        `flush=True` per AD-2.
        """
        # Step 1: parent load + type validation.
        parent = await self._load_parent(tenant_id=tenant_id, parent_product_id=parent_product_id)
        # M5 (Review): refuse mutations on soft-deleted parents. Treating
        # `is_active=False` as "not found" from the mutation surface keeps
        # the API consistent (GET still surfaces the row so the user can
        # re-activate via ProductService.patch(is_active=true) first).
        if not parent.is_active:
            raise BOMParentNotFoundError(
                tenant_id=tenant_id,
                parent_product_id=parent_product_id,
                trace_id=self.trace_id,
            )
        parent_type = ProductType(parent.product_type)
        if not is_valid_bom_parent(parent_type):
            raise BOMInvalidParentTypeError(
                tenant_id=tenant_id,
                parent_product_id=parent_product_id,
                parent_type=parent_type,
                trace_id=self.trace_id,
            )

        # Step 2: duplicate detection (AC #7).
        seen: dict[uuid.UUID, int] = {}
        for row in body.lines:
            seen[row.child_product_id] = seen.get(row.child_product_id, 0) + 1
        for child_id, occurrences in seen.items():
            if occurrences > 1:
                raise BOMDuplicateChildError(
                    tenant_id=tenant_id,
                    duplicate_child_product_id=child_id,
                    occurrences=occurrences,
                    trace_id=self.trace_id,
                )

        # Step 3: child load + type validation (AC #5).
        child_ids = [row.child_product_id for row in body.lines]
        children_by_id: dict[uuid.UUID, Product] = {}
        if child_ids:
            # H4 (Review): self-reference guard — child must not equal parent.
            # Without this, the calculation engine (Epic 4) would infinite-recurse.
            # DB FK allows self-reference; service is the source of truth.
            for cid in child_ids:
                if cid == parent_product_id:
                    raise BOMInvalidChildTypeError(
                        tenant_id=tenant_id,
                        child_product_id=cid,
                        # Use the parent_type as a stand-in to convey "this is the
                        # parent, not a valid child" — the actual child_type is
                        # unknown at this point.
                        child_type=parent_type,
                        trace_id=self.trace_id,
                    )
            children_stmt = select(Product).where(
                Product.tenant_id == tenant_id,
                Product.id.in_(child_ids),
            )
            children_result = await self.session.execute(children_stmt)
            children_by_id = {p.id: p for p in children_result.scalars().all()}

            # Every child in the payload must resolve to a real product.
            for cid in child_ids:
                child = children_by_id.get(cid)
                if child is None:
                    # L6 (Review): the missing entity is a CHILD, not the parent.
                    # Use a dedicated error so the client can act on the right field.
                    raise BOMChildNotFoundError(
                        tenant_id=tenant_id,
                        child_product_id=cid,
                        parent_product_id=parent_product_id,
                        trace_id=self.trace_id,
                    )
                if not is_valid_bom_child(ProductType(child.product_type)):
                    raise BOMInvalidChildTypeError(
                        tenant_id=tenant_id,
                        child_product_id=cid,
                        child_type=ProductType(child.product_type),
                        trace_id=self.trace_id,
                    )

        # Step 4: quantize each ratio (AD-8).
        # Quantization may slightly shift the value (e.g., 12.345678 → 12.3457).
        # We use the quantized value for both the INSERT and the audit diff.
        new_ratios: dict[uuid.UUID, Decimal] = {}
        for row in body.lines:
            try:
                quantized = quantize_ratio(row.ratio)
            except (TypeError, ValueError) as err:
                raise BOMInvalidRatioError(
                    tenant_id=tenant_id,
                    child_product_id=row.child_product_id,
                    ratio=row.ratio,
                    trace_id=self.trace_id,
                ) from err
            new_ratios[row.child_product_id] = quantized

        # Step 5: load existing BOM for the diff (audit payload).
        existing_stmt = (
            select(BOMLine)
            .where(
                BOMLine.tenant_id == tenant_id,
                BOMLine.parent_product_id == parent_product_id,
            )
            .order_by(BOMLine.created_at.asc())
        )
        existing_result = await self.session.execute(existing_stmt)
        existing_rows = list(existing_result.scalars().all())
        existing_ratios: dict[uuid.UUID, Decimal] = {
            r.child_product_id: r.ratio for r in existing_rows
        }

        # CR 2.1 idempotent no-op skip: if new set == existing set
        # (same keys, same quantized ratios), return without writing.
        if self._is_noop_replace(existing_ratios, new_ratios):
            return await self.get_bom(tenant_id=tenant_id, parent_product_id=parent_product_id)

        # Build the changed_ratios audit payload (AC #3).
        changed_ratios = self._diff_ratios(existing_ratios, new_ratios)
        new_total = sum_ratios(new_ratios.values())
        is_complete = new_total == TARGET_TOTAL

        # Step 6: audit-first (AD-2). Emit BEFORE DELETE/INSERT.
        # Story 4.3 (A5 Phase 1) — typed emit wrapper.
        await emit_audit_typed(
            self.session,
            action_class=ActionClass.BOM_LINE,
            action="bom_set",
            actor_id=actor_id,
            target_id=parent_product_id,
            reason=None,
            payload={
                "tenant_id": str(tenant_id),
                "parent_product_id": str(parent_product_id),
                "child_count": len(new_ratios),
                "total_ratio": str(new_total),
                "is_complete": is_complete,
                # CR 1.1 lesson: self-describing payload — full diff for
                # the audit trail. Includes added / changed / removed.
                "changed_ratios": [
                    {
                        "child_product_id": str(cid),
                        "before": str(before) if before is not None else None,
                        "after": str(after),
                    }
                    for cid, before, after in changed_ratios
                ],
                "trace_id": self.trace_id,
            },
            tenant_id=tenant_id,
            flush=True,  # audit row committed before the bom_lines DELETE/INSERT
        )

        # Step 7: atomic DELETE + INSERT (CR 2.1 lesson — 100% invariant
        # atomic). The DELETE clears existing rows for this parent; the
        # INSERT writes the new set. If either fails, the entire txn
        # rolls back; the audit row also rolls back via `flush=True` +
        # DELETE/INSERT in the same `session.begin()` (single transaction
        # at the call site).
        #
        # L12 (Review): wrap the data write in `begin_nested()` (SAVEPOINT).
        # If INSERT raises IntegrityError, we can roll back JUST the
        # SAVEPOINT (DELETE + INSERTs) while keeping the audit row
        # committed — the AD-2 audit-first guarantee.
        try:
            async with self.session.begin_nested():
                delete_stmt = delete(BOMLine).where(
                    BOMLine.tenant_id == tenant_id,
                    BOMLine.parent_product_id == parent_product_id,
                )
                await self.session.execute(delete_stmt)

                now = datetime.now(tz=UTC)
                new_bom_lines: list[BOMLine] = []
                for cid, ratio in new_ratios.items():
                    new_bom_lines.append(
                        BOMLine(
                            id=_uuid7(),
                            tenant_id=tenant_id,
                            parent_product_id=parent_product_id,
                            child_product_id=cid,
                            ratio=ratio,
                            created_at=now,
                            updated_at=now,
                        )
                    )
                if new_bom_lines:
                    self.session.add_all(new_bom_lines)
                await self.session.flush()
        except IntegrityError as err:
            # SAVEPOINT was auto-rolled back by `begin_nested()` exit —
            # the DELETE + INSERTs are discarded, but the audit row
            # (committed in the outer txn via `flush=True`) survives.
            # Defense-in-depth: race condition broke the UNIQUE index
            # (two concurrent PUTs). Surface as 422 typed error rather
            # than a 500.
            if self._is_unique_bom_violation(err):
                # M10 (Review): parse the actual conflicting child ID from
                # the error when the driver exposes it. Falls back to a
                # random UUID only when the driver doesn't surface the detail.
                duplicate_id = self._extract_duplicate_child_id(err) or uuid.uuid4()
                raise BOMDuplicateChildError(
                    tenant_id=tenant_id,
                    duplicate_child_product_id=duplicate_id,
                    occurrences=2,
                    trace_id=self.trace_id,
                ) from err
            raise

        # Return the refreshed BOM.
        return await self.get_bom(tenant_id=tenant_id, parent_product_id=parent_product_id)

    # ── clear_bom ─────────────────────────────────────────────
    async def clear_bom(
        self,
        *,
        tenant_id: uuid.UUID,
        actor_id: uuid.UUID,
        parent_product_id: uuid.UUID,
    ) -> None:
        """Delete all BOM rows for a parent (AC "BOM 초기화" UI action).

        Audit-first. Emits `bom_cleared` BEFORE the DELETE.

        Raises:
            BOMParentNotFoundError: parent does not exist for tenant.
        """
        parent = await self._load_parent(tenant_id=tenant_id, parent_product_id=parent_product_id)
        # M5 (Review): refuse mutations on soft-deleted parents.
        if not parent.is_active:
            raise BOMParentNotFoundError(
                tenant_id=tenant_id,
                parent_product_id=parent_product_id,
                trace_id=self.trace_id,
            )
        parent_type = ProductType(parent.product_type)
        if not is_valid_bom_parent(parent_type):
            raise BOMInvalidParentTypeError(
                tenant_id=tenant_id,
                parent_product_id=parent_product_id,
                parent_type=parent_type,
                trace_id=self.trace_id,
            )

        # M4 (Review): idempotent no-op audit skip (CR 2.1 lesson). If the
        # BOM is already empty, skip both audit emit and DELETE so the
        # audit log doesn't accumulate noise from repeated "초기화" clicks.
        existing_count_stmt = (
            select(BOMLine.id)
            .where(
                BOMLine.tenant_id == tenant_id,
                BOMLine.parent_product_id == parent_product_id,
            )
            .limit(1)
        )
        existing_count_result = await self.session.execute(existing_count_stmt)
        if existing_count_result.scalar_one_or_none() is None:
            return

        # Audit-first (AD-2). Story 4.3 (A5 Phase 1) — typed emit wrapper.
        await emit_audit_typed(
            self.session,
            action_class=ActionClass.BOM_LINE,
            action="bom_cleared",
            actor_id=actor_id,
            target_id=parent_product_id,
            reason=None,
            payload={
                "tenant_id": str(tenant_id),
                "parent_product_id": str(parent_product_id),
                "trace_id": self.trace_id,
            },
            tenant_id=tenant_id,
            flush=True,
        )

        delete_stmt = delete(BOMLine).where(
            BOMLine.tenant_id == tenant_id,
            BOMLine.parent_product_id == parent_product_id,
        )
        await self.session.execute(delete_stmt)
        await self.session.flush()

    # ── internal helpers ─────────────────────────────────────
    async def _load_parent(
        self,
        *,
        tenant_id: uuid.UUID,
        parent_product_id: uuid.UUID,
    ) -> Product:
        """Load the parent product; raise BOMParentNotFoundError on miss.

        RLS-scoped — if the parent belongs to a different tenant, the
        row is invisible and we raise 404.
        """
        stmt = select(Product).where(
            Product.tenant_id == tenant_id,
            Product.id == parent_product_id,
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            raise BOMParentNotFoundError(
                tenant_id=tenant_id,
                parent_product_id=parent_product_id,
                trace_id=self.trace_id,
            )
        return row

    def _bom_line_to_response(
        self,
        row: BOMLine,
        child: Product | None,
    ) -> BOMLineResponse:
        """ORM row + denormalized child → BOMLineResponse.

        `child` may be None in pathological cases (RLS filtered it out
        even though it exists). M9 (Review): previously fell back to a
        `MATERIAL` best-guess + `is_active=False`, silently masking
        cross-tenant data leaks. We now raise an internal error so the
        regression surfaces immediately rather than producing a
        misleading row.
        """
        if child is None:
            # M9 (Review): surface the regression. The FK RESTRICT on
            # child_product_id guarantees a soft-deleted child still
            # has a row, so a None here means a real RLS or query bug.
            raise RuntimeError(
                f"bom line {row.id!s} references child {row.child_product_id!s} "
                f"that is not visible to tenant {row.tenant_id!s} (RLS filtered or missing)"
            )

        return BOMLineResponse(
            id=row.id,
            child_product_id=row.child_product_id,
            child_code=child.code,
            child_name=child.name,
            child_product_type=ProductType(child.product_type),
            child_is_active=child.is_active,
            ratio=row.ratio,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _is_noop_replace(
        existing: dict[uuid.UUID, Decimal],
        new: dict[uuid.UUID, Decimal],
    ) -> bool:
        """True iff the new payload exactly equals the stored state.

        CR 2.1 lesson — idempotent no-op audit skip. If the caller
        PUTs the same payload twice, the second PUT should not emit an
        audit row. Distinguishes "no-op replace" from "initial BOM write"
        (the latter always emits because `existing` is empty).
        """
        if set(existing.keys()) != set(new.keys()):
            return False
        return all(existing[k] == v for k, v in new.items())

    @staticmethod
    def _diff_ratios(
        existing: dict[uuid.UUID, Decimal],
        new: dict[uuid.UUID, Decimal],
    ) -> list[tuple[uuid.UUID, Decimal | None, Decimal]]:
        """Compute (added, changed, removed) diff for the audit payload.

        Returns list of `(child_product_id, before, after)` tuples where:
        - `before is None` → row was added.
        - `after` equals a value → row was changed (or added with the `before=None`).
        - Removed rows are also captured: `before=old_value, after=None` is
          implied by absence from the dict. We iterate over the symmetric
          difference so the audit log shows the full picture.
        """
        out: list[tuple[uuid.UUID, Decimal | None, Decimal]] = []
        # L10 (Review): `sorted` for stable audit payload order. Set iteration
        # is non-deterministic across runs; downstream consumers (Story 5+
        # 수불부 reconciliation) need a canonical ordering.
        all_ids = sorted(existing.keys() | new.keys())
        for cid in all_ids:
            before = existing.get(cid)
            after = new.get(cid)
            if before is None and after is not None:
                out.append((cid, None, after))
            elif before is not None and after is None:
                # M7 (Review): include removed rows with `after=None` so the
                # audit payload is self-describing (CR 1.1 lesson). The
                # `child_count` still reflects the new state; the diff is
                # recoverable from the changed_ratios entries alone.
                out.append((cid, before, None))
            elif before != after:
                out.append((cid, before, after))
        return out

    @staticmethod
    def _is_unique_bom_violation(err: IntegrityError) -> bool:
        """True iff `err` is the UNIQUE violation on (tenant, parent, child).

        Used for the defense-in-depth race-condition check on bulk-replace.
        PostgreSQL SQLSTATE 23505 = unique_violation.

        M10 (Review): parse the constraint name rather than relying on the
        over-broad `"23505" in str(orig)` substring check, which could
        false-positive on any 23505 in the error message text.
        """
        orig = err.orig
        # asyncpg / psycopg2 expose the SQLSTATE on `.sqlstate` or `.pgcode`.
        if hasattr(orig, "sqlstate") and orig.sqlstate == "23505":
            return _bom_unique_constraint_name_in(orig) is not None
        if hasattr(orig, "pgcode") and orig.pgcode == "23505":
            return _bom_unique_constraint_name_in(orig) is not None
        # Fallback: substring match against the constraint name only.
        return "uq_bom_lines_tenant_parent_child" in str(orig)

    @staticmethod
    def _extract_duplicate_child_id(err: IntegrityError) -> uuid.UUID | None:
        """Best-effort extract the conflicting child_product_id from a 23505.

        asyncpg exposes the row values via `err.orig.diag.message_detail`
        (e.g. ``"Key (tenant_id, parent_product_id, child_product_id)=(..., ..., ...)"``).
        Falls back to ``None`` if the driver doesn't surface the detail.
        """
        orig = err.orig
        diag = getattr(orig, "diag", None)
        detail = getattr(diag, "message_detail", None) if diag is not None else None
        if not isinstance(detail, str) or "(" not in detail:
            return None
        # Parse "Key (col1, col2, col3)=(v1, v2, v3)" — last value is child.
        try:
            rhs = detail.split("=", 1)[1].rstrip(")")
            parts = [p.strip().strip("'\"") for p in rhs.split(",")]
            if len(parts) >= 3:
                return uuid.UUID(parts[-1])
        except (IndexError, ValueError):
            return None
        return None


__all__ = [
    "BOMParentNotFoundError",
    "BOMInvalidParentTypeError",
    "BOMInvalidChildTypeError",
    "BOMDuplicateChildError",
    "BOMInvalidRatioError",
    "BOMChildNotFoundError",
    "BOMService",
]
