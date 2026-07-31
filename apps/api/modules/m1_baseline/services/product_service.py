"""apps.api.modules.m1_baseline.services.product_service — product catalog CRUD (Story 2.1).

Writes/reads on the ``products`` table (PRD §8.M1). All state-changing
operations write a typed ``audit_logs`` row BEFORE the data write (AD-2).
Hard delete is forbidden — soft-delete via ``is_active`` (AC #5).

Layering (AD-1 / AD-11):
- Pure helpers live in ``packages/services/m1_baseline/``.
- This module wires them to SQLAlchemy + FastAPI dependencies.
- It does NOT import ``packages.cost_engine`` (AD-11 layer rule).

Concurrency:
- Code uniqueness is enforced by the database (UNIQUE index on
  ``(tenant_id, code)``). Auto-generation is a fast-path optimization
  for the common case; the unique index is the ground truth for AC #3.
- The product row is locked with ``SELECT ... FOR UPDATE`` before PATCH
  to prevent concurrent update races.

Money typing (AD-8):
- ``unit_cost_krw`` is BIGINT (no fractional won). Python ``int``.
- ``unit_cost_usd`` is NUMERIC(18,2). Python ``Decimal`` with
  ``ROUND_HALF_EVEN`` rounding (Story 0.4 chunk-B parity).

Capability gate (AC #6 / F-44):
- All 4 routes use ``require_capability(Capability.PRODUCT)``.
- POST additionally gates ``material`` / ``semi_product`` types against
  the tenant's industry — service tenants cannot register physical
  catalog items (no BOM menu → no material entries).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Final

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.audit import emit_audit
from apps.api.core.db_models import Product
from apps.api.modules.m1_baseline.schemas import (
    ProductCreateRequest,
    ProductUpdateRequest,
)
from packages.common.uuid7 import uuid7 as _uuid7
from packages.services.m0_onboarding.industry_menu import Industry
from packages.services.m1_baseline.product_code import (
    InvalidProductCodeError,
    generate_next_code,
    is_valid_code_format,
    parse_code,
)
from packages.services.m1_baseline.schemas import (
    ProductType,
    type_to_prefix,
)


# ── Typed exceptions (mapped to HTTP by handlers.py) ────────
class ProductNotFoundError(Exception):
    """404 PRODUCT_NOT_FOUND — product row missing for the given (tenant, product_id)."""

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        product_id: uuid.UUID,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"product {product_id!s} not found for tenant {tenant_id!s}"
        )
        self.tenant_id = tenant_id
        self.product_id = product_id
        self.trace_id = trace_id


class ProductCodeDuplicateError(Exception):
    """409 PRODUCT_CODE_DUPLICATE — same (tenant_id, code) already exists.

    The unique index (uq_products_tenant_code) surfaces 409 deterministically.
    The auto-generation in `create_product()` is a fast-path optimization;
    the index is the ground truth for AC #3.
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        code: str,
        existing_product_id: uuid.UUID | None,
        trace_id: str,
    ) -> None:
        super().__init__(f"code {code!r} already exists for tenant {tenant_id!s}")
        self.tenant_id = tenant_id
        self.code = code
        self.existing_product_id = existing_product_id
        self.trace_id = trace_id


class ProductImmutableFieldError(Exception):
    """403 PRODUCT_IMMUTABLE_FIELD — attempt to change `code` or `product_type` via PATCH.

    Both fields are immutable after creation:
    - `code` change = BOM/ledger drift (AD-18 single product identity)
    - `product_type` change = Story 2.3 integrity guard territory
    """

    def __init__(
        self,
        *,
        field: str,
        trace_id: str,
    ) -> None:
        super().__init__(f"field {field!r} is immutable after creation")
        self.field = field
        self.trace_id = trace_id


class ProductCapabilityError(Exception):
    """403 INDUSTRY_NOT_SUPPORTED — tenant's industry disallows this product type.

    AC #6 / F-44 — service tenants cannot register `material` or
    `semi_product` types. The capability gate is enforced in the
    handler (POST); this exception carries the typed details.
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        current_industry: Industry | None,
        requested_type: ProductType,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"industry {current_industry!r} cannot register type {requested_type.value!r}"
        )
        self.tenant_id = tenant_id
        self.current_industry = current_industry
        self.requested_type = requested_type
        self.trace_id = trace_id


# ── Industry × type gate (AC #6) ─────────────────────────────
# Service tenants cannot register `material` or `semi_product`.
# Other industries (including the service-hybrid ③ / ④) can register all
# 5 types including the `service` product type for their ABC.
_TYPE_REQUIRES_PRODUCT_MATERIAL: Final[set[ProductType]] = {
    ProductType.MATERIAL,
    ProductType.SEMI_PRODUCT,
}


def is_type_allowed_for_industry(
    industry: Industry | None,
    product_type: ProductType,
) -> bool:
    """Pure helper: does `industry` allow `product_type`?

    Returns True unless the type needs the PRODUCT_MATERIAL capability
    AND the industry's industry does not unlock it. Service tenants
    see False for material/semi_product; everyone else sees True.
    """
    if product_type not in _TYPE_REQUIRES_PRODUCT_MATERIAL:
        return True
    # material / semi_product — needs PRODUCT_MATERIAL capability.
    if industry is None:
        return False  # no industry selected → conservative deny
    # Avoid circular import; resolve the capability directly.
    from apps.api.core.capability import (
        Capability,  # noqa: PLC0415  (lazy: capability module is small)
        industry_supports,  # noqa: PLC0415
    )

    return industry_supports(industry, Capability.PRODUCT_MATERIAL)


# ── Service ──────────────────────────────────────────────────
class ProductService:
    """Stateless service-layer facade for product CRUD.

    Mirrors `SettingsService` constructor pattern. One instance per
    request — the caller (handlers.py) owns the session lifecycle.
    """

    def __init__(self, session: AsyncSession, *, trace_id: str | None = None) -> None:
        self.session = session
        self.trace_id = trace_id or str(uuid.uuid4())

    # ── list_products ────────────────────────────────────────
    async def list_products(
        self,
        *,
        tenant_id: uuid.UUID,
        product_type: ProductType | None = None,
        is_active: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Product], int]:
        """Return (items, total) — newest-first, RLS already filtered.

        `is_active=None` means "no filter applied" (caller passes True/False
        to scope to active-only or inactive-only).
        """
        # Total count (RLS already enforced at the query layer).
        count_stmt = select(func.count(Product.id)).where(Product.tenant_id == tenant_id)
        if product_type is not None:
            count_stmt = count_stmt.where(Product.product_type == product_type.value)
        if is_active is not None:
            count_stmt = count_stmt.where(Product.is_active == is_active)
        total = (await self.session.execute(count_stmt)).scalar_one()

        # Items. M4: limit/offset are validated by FastAPI's Pydantic Query
        # (ge=1, le=1000 / ge=0) in the handler — no in-service clamp needed.
        stmt = (
            select(Product)
            .where(Product.tenant_id == tenant_id)
            .order_by(Product.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if product_type is not None:
            stmt = stmt.where(Product.product_type == product_type.value)
        if is_active is not None:
            stmt = stmt.where(Product.is_active == is_active)

        result = await self.session.execute(stmt)
        items = list(result.scalars().all())
        return items, int(total)

    # ── get_product ──────────────────────────────────────────
    async def get_product(
        self,
        *,
        tenant_id: uuid.UUID,
        product_id: uuid.UUID,
    ) -> Product:
        """Single fetch. Raises ProductNotFoundError when RLS filters the row out."""
        stmt = select(Product).where(
            Product.tenant_id == tenant_id,
            Product.id == product_id,
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            raise ProductNotFoundError(
                tenant_id=tenant_id,
                product_id=product_id,
                trace_id=self.trace_id,
            )
        return row

    # ── create_product ───────────────────────────────────────
    async def create_product(
        self,
        *,
        tenant_id: uuid.UUID,
        actor_id: uuid.UUID,
        industry: Industry | None,
        body: ProductCreateRequest,
    ) -> Product:
        """Insert a product row + audit log.

        Steps:
        1. Capability gate (AC #6): industry must allow `body.product_type`.
        2. Validate or auto-generate `code` (cross-validate prefix vs type).
        3. Compute `new_id` (UUID v7 — AD-15 §3).
        4. INSERT audit_logs row BEFORE the products INSERT, with
           `target_id=new_id` (H1: no racy backfill).
        5. INSERT products row (UNIQUE index may surface 409).
        6. Flush + return refreshed row.

        Raises:
            ProductCapabilityError: industry × type mismatch (AC #6).
            InvalidProductCodeError: explicit `code` is malformed (AC #1 422)
                or empty string (M8) or prefix mismatches type (M7).
            ProductCodeDuplicateError: same (tenant, code) collision (AC #3 409).
        """
        # Step 1: capability gate.
        if not is_type_allowed_for_industry(industry, body.product_type):
            raise ProductCapabilityError(
                tenant_id=tenant_id,
                current_industry=industry,
                requested_type=body.product_type,
                trace_id=self.trace_id,
            )

        # Step 2: code resolution.
        if body.code is None:
            code = await self._next_code(
                tenant_id=tenant_id, product_type=body.product_type
            )
        elif body.code == "":
            # M8: explicit empty string is malformed input, not a request
            # to auto-generate. Different from `None` (auto-generate).
            raise InvalidProductCodeError(body.code, "code cannot be empty string")
        else:
            if not is_valid_code_format(body.code):
                raise InvalidProductCodeError(
                    body.code, "manual code must match PREFIX-XXXX"
                )
            # M7: cross-validate manual code prefix vs body.product_type.
            code_prefix_type, _seq = parse_code(body.code)
            if code_prefix_type != body.product_type:
                raise InvalidProductCodeError(
                    body.code,
                    f"prefix does not match product_type={body.product_type.value!r}",
                )
            code = body.code

        now = datetime.now(tz=UTC)

        # Step 3: compute new_id (H2 — use UUID v7, no silent v4 fallback).
        new_id = _uuid7()

        # Step 4: audit-first (AD-2 / H1). `target_id` is set at write time —
        # no racy backfill query, no race between concurrent POSTs.
        await emit_audit(
            self.session,
            actor_id=actor_id,
            action="product_created",
            target_table="products",
            target_id=new_id,
            reason=None,
            payload={
                "tenant_id": str(tenant_id),
                "product_type": body.product_type.value,
                "code": code,
                "name": body.name,
                # CR 1.1 lesson: payload is self-describing. changed_fields is
                # the full list for an INSERT (initial write), before/after
                # is omitted because there's no prior state.
                "changed_fields": [
                    "product_type",
                    "code",
                    "name",
                    "unit",
                    "unit_cost_krw",
                    "unit_cost_usd",
                    "description",
                    "is_active",
                ],
                "trace_id": self.trace_id,
            },
            tenant_id=tenant_id,
            flush=True,  # audit row committed before the product INSERT
        )

        # Step 5: INSERT products row.
        product = Product(
            id=new_id,
            tenant_id=tenant_id,
            product_type=body.product_type.value,
            code=code,
            name=body.name,
            unit=body.unit,
            unit_cost_krw=body.unit_cost_krw,
            unit_cost_usd=body.unit_cost_usd,
            description=body.description,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        self.session.add(product)
        try:
            await self.session.flush()
        except IntegrityError as err:
            # M6: distinguish unique-constraint violations from other
            # integrity failures (FK / NOT NULL / CHECK). Only the unique
            # index on (tenant_id, code) maps to 409.
            await self.session.rollback()
            if not is_unique_code_error(err):
                raise
            # The UNIQUE index (tenant_id, code) surface. Look up the existing
            # row so the API can echo `details.product_id` to the frontend (AC #3).
            existing = await self._find_by_code(tenant_id=tenant_id, code=code)
            existing_id = existing.id if existing is not None else None
            raise ProductCodeDuplicateError(
                tenant_id=tenant_id,
                code=code,
                existing_product_id=existing_id,
                trace_id=self.trace_id,
            ) from err

        await self.session.refresh(product)
        return product

    # ── update_product ───────────────────────────────────────
    async def update_product(
        self,
        *,
        tenant_id: uuid.UUID,
        actor_id: uuid.UUID,
        product_id: uuid.UUID,
        body: ProductUpdateRequest,
    ) -> Product:
        """Partial update with audit-first + immutable-field guards.

        Per AC #4: `code` and `product_type` are immutable. Attempting to
        set them via PATCH raises ProductImmutableFieldError (403).

        Per CR 1.1 lesson: payload is `{changed_fields, before, after}` map.
        """
        # Lock + load.
        load_stmt = (
            select(Product)
            .where(
                Product.tenant_id == tenant_id,
                Product.id == product_id,
            )
            .with_for_update()
        )
        result = await self.session.execute(load_stmt)
        row = result.scalar_one_or_none()
        if row is None:
            raise ProductNotFoundError(
                tenant_id=tenant_id,
                product_id=product_id,
                trace_id=self.trace_id,
            )

        # Reject any attempt to PATCH `code` or `product_type`. The
        # `model_dump(exclude_unset=True)` shows only what the caller
        # actually sent (Pydantic partial-update semantics).
        sent = body.model_dump(exclude_unset=True)
        if "code" in sent:
            raise ProductImmutableFieldError(field="code", trace_id=self.trace_id)
        if "product_type" in sent:
            raise ProductImmutableFieldError(field="product_type", trace_id=self.trace_id)

        # Compute before/after for changed fields (CR 1.1 self-describing payload).
        # M5: `is_active` is intentionally excluded — soft-delete toggle has a
        # dedicated audit event (`product_soft_deleted` / `product_reactivated`)
        # and must route through `soft_delete_product`, not PATCH.
        candidate_fields = ("name", "unit", "unit_cost_krw", "unit_cost_usd", "description")
        changed_fields: list[str] = []
        before: dict[str, object] = {}
        after: dict[str, object] = {}
        for field in candidate_fields:
            if field in sent:
                new_value = getattr(body, field)
                old_value = getattr(row, field)
                if new_value != old_value:
                    changed_fields.append(field)
                    before[field] = _serializable(old_value)
                    after[field] = _serializable(new_value)
                setattr(row, field, new_value)

        # CR 1.1 lesson: idempotent no-op audit skip is fine when no fields
        # actually changed. The initial-write case (where stored was null)
        # would always set changed_fields for the populated fields, so the
        # distinction lands cleanly.
        if not changed_fields:
            return row

        row.updated_at = datetime.now(tz=UTC)

        # Audit-first.
        await emit_audit(
            self.session,
            actor_id=actor_id,
            action="product_updated",
            target_table="products",
            target_id=row.id,
            reason=None,
            payload={
                "tenant_id": str(tenant_id),
                "product_id": str(row.id),
                "code": row.code,
                "changed_fields": changed_fields,
                "before": before,
                "after": after,
                "trace_id": self.trace_id,
            },
            tenant_id=tenant_id,
            flush=True,
        )
        await self.session.flush()
        await self.session.refresh(row)
        return row

    # ── soft_delete_product ──────────────────────────────────
    async def soft_delete_product(
        self,
        *,
        tenant_id: uuid.UUID,
        actor_id: uuid.UUID,
        product_id: uuid.UUID,
        is_active: bool,
    ) -> Product:
        """Toggle `is_active`. Soft-delete only (AC #5; AD-2 append-only)."""
        load_stmt = (
            select(Product)
            .where(
                Product.tenant_id == tenant_id,
                Product.id == product_id,
            )
            .with_for_update()
        )
        result = await self.session.execute(load_stmt)
        row = result.scalar_one_or_none()
        if row is None:
            raise ProductNotFoundError(
                tenant_id=tenant_id,
                product_id=product_id,
                trace_id=self.trace_id,
            )

        if row.is_active == is_active:
            # No-op (CR 1.1: idempotent no-op audit skip).
            return row

        before = row.is_active
        row.is_active = is_active
        row.updated_at = datetime.now(tz=UTC)

        await emit_audit(
            self.session,
            actor_id=actor_id,
            action="product_soft_deleted" if not is_active else "product_reactivated",
            target_table="products",
            target_id=row.id,
            reason=None,
            payload={
                "tenant_id": str(tenant_id),
                "product_id": str(row.id),
                "code": row.code,
                "changed_fields": ["is_active"],
                "before": {"is_active": before},
                "after": {"is_active": is_active},
                "trace_id": self.trace_id,
            },
            tenant_id=tenant_id,
            flush=True,
        )
        await self.session.flush()
        await self.session.refresh(row)
        return row

    # ── internal helpers ─────────────────────────────────────
    async def _next_code(
        self,
        *,
        tenant_id: uuid.UUID,
        product_type: ProductType,
    ) -> str:
        """Compute the next per-tenant per-type sequence code.

        Uses `parse_code` on existing rows to extract the integer suffix.
        The UNIQUE index is the ground truth; this is a fast-path optimization.
        Race conditions surface as ProductCodeDuplicateError (409 AC #3).
        """
        prefix = type_to_prefix(product_type)
        # Pull all codes with the matching prefix for this tenant + type.
        # Use the indexed columns only; the in-Python regex parse handles
        # the suffix extraction (cheaper than a regex-on-DB query).
        stmt = (
            select(Product.code)
            .where(
                Product.tenant_id == tenant_id,
                Product.product_type == product_type.value,
                Product.code.like(f"{prefix}-%"),
            )
        )
        result = await self.session.execute(stmt)
        max_seq = 0
        for (raw_code,) in result.all():
            try:
                _pt, seq = parse_code(raw_code)
            except InvalidProductCodeError:
                continue
            if _pt == product_type and seq > max_seq:
                max_seq = seq
        return generate_next_code({product_type: max_seq}, product_type)

    async def _find_by_code(
        self,
        *,
        tenant_id: uuid.UUID,
        code: str,
    ) -> Product | None:
        stmt = select(Product).where(
            Product.tenant_id == tenant_id,
            Product.code == code,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


# ── Module-level helpers ─────────────────────────────────────
def _serializable(value: object) -> object:
    """Convert Decimal/datetime/UUID for the audit payload JSONB.

    CR 1.1 lesson: payload redaction isn't strictly required for the
    product table (no passwords/secrets), but the format helper keeps
    `before` / `after` shapes uniform with other audit rows.
    """
    from datetime import date as _date

    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime | _date):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    return value


def is_unique_code_error(err: IntegrityError) -> bool:
    """True if `err` is a unique-constraint violation on (tenant_id, code).

    M6: used to distinguish AC #3 PRODUCT_CODE_DUPLICATE (409) from other
    integrity failures (FK / NOT NULL / CHECK) which must surface as 500.
    PostgreSQL SQLSTATE 23505 = unique_violation.
    """
    orig = err.orig
    # asyncpg: `.sqlstate` attribute is the canonical 5-char SQLSTATE.
    if hasattr(orig, "sqlstate") and orig.sqlstate == "23505":
        return True
    # psycopg2/3: `.pgcode` is the SQLSTATE.
    if hasattr(orig, "pgcode") and orig.pgcode == "23505":
        return True
    # Final fallback: string match (e.g. wrapped exceptions).
    return "uq_products_tenant_code" in str(orig) or "23505" in str(orig)
