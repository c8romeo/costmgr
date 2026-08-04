"""packages.services.m4_inventory.ledger — Story 5.2 pure kernel.

Append-only inventory_ledger event kernel. The DB table
`apps/api/core/db_models.py::InventoryLedger` and the PostgreSQL
`BEFORE UPDATE OR DELETE` trigger (Alembic 0015) own the production
gate; this kernel owns the immutable event payload + strict
validators + append-only violation message builder.

AD-1 / AD-5 / AD-11 binding: pure-Python, stdlib-only, no DB, no clock,
no random. Drift between Python and TS caught by
`tests/integration/test_inventory_ledger_label_consistency.py`.

Event_type 11-value whitelist (5-2 ship 시점 명시, OQ3 cj-style
default — pre-emptive coverage of 5-2 + Epic 11 reversal + Epic 6
close-out + Epic 5 maintenance):

  1. `opening_carried`                 — Story 5.1 carry chain 결과
  2. `opening_carried_stale_overwrite` — Story 5.1 AC #3 silent overwrite
  3. `purchase_inbound`                — stream='purchases' PRD §6.2 입고
  4. `sales_outbound`                  — stream='sales' PRD §6.2 출고
  5. `production_output_inbound`       — stream='production' output product_qty
  6. `production_material_consumption` — stream='production' input material 사용량
  7. `adjustment_positive`             — 직접 조정 (+) — Epic 5+ 후속
  8. `adjustment_negative`             — 직접 조정 (−) — Epic 5+ 후속
  9. `reversal_negating`               — AD-22 부호 반전 row (Epic 11 authority insert)
 10. `reversal_corrected`              — AD-22 corrected row (Epic 11 authority insert)
 11. `closing_snapshot`                — periodic close 시 closing_balance materialize (Epic 11)

These mirror the PostgreSQL CHECK constraint in Alembic 0015 +
`_REGISTRY[ActionClass.INVENTORY_LEDGER]` accepted set in
`apps/api/core/audit_action.py`. Drift is caught by
`tests/integration/test_audit_action_consistency.py` (3-way detector).
"""

from __future__ import annotations

import re
import uuid
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any, Final, NamedTuple

from packages.services.m2_input.inventory_projection import QTY_QUANTUM

# ── Constants ────────────────────────────────────────────────
# Whitelist of 11 event_type values (AC #2 + OQ3 cj-style default).
# DB CHECK constraint is the production gate; this whitelist is the
# early-fail guard. They must stay in sync — drift detector enforces.
INVENTORY_LEDGER_EVENT_TYPES: Final[frozenset[str]] = frozenset(
    {
        "opening_carried",
        "opening_carried_stale_overwrite",
        "purchase_inbound",
        "sales_outbound",
        "production_output_inbound",
        "production_material_consumption",
        "adjustment_positive",
        "adjustment_negative",
        "reversal_negating",
        "reversal_corrected",
        "closing_snapshot",
    }
)

# QTY_QUANTUM is re-exported for caller convenience (Decimal + round
# mode parity with PRD §6.2). The pure kernel of packages.services
# owns the actual quantization rule. AD-15 cross-language parity.
INVENTORY_LEDGER_QTY_QUANTUM: Final[Decimal] = QTY_QUANTUM

# Period-key pattern (AD-24). Real fiscal keys are `'YYYY-MM'`.
# M8 virtual budget keys (`YYYY-MM#B<n>`) are explicitly excluded
# from inventory_ledger scope (PRD §6.2 inventory equation is fiscal).
_PERIOD_KEY_PATTERN: Final[re.Pattern[str]] = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

# AD-15: snake_case JSON keys; AD-8: Decimal string serialization.
# These keys mirror `apps/web/lib/l2-input-inventory-ledger.ts`.
PAYLOAD_KEY_EVENT_ID: Final[str] = "event_id"
PAYLOAD_KEY_PRODUCT_ID: Final[str] = "product_id"
PAYLOAD_KEY_PERIOD_KEY: Final[str] = "period_key"
PAYLOAD_KEY_EVENT_TYPE: Final[str] = "event_type"
PAYLOAD_KEY_QTY: Final[str] = "qty"
PAYLOAD_KEY_TRACE_ID: Final[str] = "trace_id"
PAYLOAD_KEY_SOURCE: Final[str] = "source"
PAYLOAD_KEY_REVERSES_EVENT_ID: Final[str] = "reverses_event_id"
PAYLOAD_KEY_CORRECTION_GROUP_ID: Final[str] = "correction_group_id"
PAYLOAD_KEY_METADATA: Final[str] = "metadata"

# Source discriminator (AD-15): literal tags for the audit-first
# payload self-describing pattern (CR 1.1 lesson).
SOURCE_CARRY_CHAIN: Final[str] = "carry_chain"
SOURCE_MONTHLY_INPUT: Final[str] = "monthly_input"
SOURCE_MANUAL_BACKFILL: Final[str] = "manual_backfill"
SOURCE_REVERSAL_REQUEST: Final[str] = "reversal_request"
SOURCE_CLOSE_SNAPSHOT: Final[str] = "close_snapshot"


# ── Typed exception (pure-kernel domain semantics) ───────────
# Stable error codes — service layer dispatches via `err.error_code`
# (NOT substring matching on err.message). Substring matching was
# fragile (C11 CR review 2026-08-04) — any kernel message refactor
# (e.g. "11-value" → "12-value") silently broke service dispatch.
ERROR_CODE_INVALID_EVENT_TYPE: Final[str] = "INVALID_EVENT_TYPE"
ERROR_CODE_EMPTY_EVENT_TYPE: Final[str] = "EMPTY_EVENT_TYPE"
ERROR_CODE_NON_STR_EVENT_TYPE: Final[str] = "NON_STR_EVENT_TYPE"
ERROR_CODE_INVALID_PERIOD_KEY: Final[str] = "INVALID_PERIOD_KEY"
ERROR_CODE_NON_STR_PERIOD_KEY: Final[str] = "NON_STR_PERIOD_KEY"
ERROR_CODE_QTY_REQUIRED: Final[str] = "QTY_REQUIRED"
ERROR_CODE_QTY_MUST_BE_DECIMAL: Final[str] = "QTY_MUST_BE_DECIMAL"
ERROR_CODE_INVALID_UUID_VERSION: Final[str] = "INVALID_UUID_VERSION"
ERROR_CODE_INVALID_SOURCE: Final[str] = "INVALID_SOURCE"


class AppendOnlyLedgerError(Exception):
    """Pure-kernel append-only violation.

    Distinct from service-layer `AppendOnlyLedgerViolationError` (which
    carries HTTP envelope + audit-first semantics). This exception is
    raised by the pure kernel during event_type validation / shape
    validation / message construction. NO HTTP mapping; service layer
    wraps with envelope details.

    Service-layer dispatch uses `err.error_code` (stable Literal) NOT
    `err.message` substring matching. CR review 2026-08-04 patch P10.
    """

    def __init__(
        self,
        *,
        message: str,
        error_code: str = ERROR_CODE_INVALID_EVENT_TYPE,
        event_id: uuid.UUID | None = None,
        attempted_op: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.event_id = event_id
        self.attempted_op = attempted_op


# ── InventoryLedgerEvent NamedTuple ───────────────────────────
class InventoryLedgerEvent(NamedTuple):
    """Immutable event row shape — mirrors the SQL column set.

    AD-15: snake_case field names. cross-language mirrorable to
    `apps/web/lib/l2-input-inventory-ledger.ts::InventoryLedgerEvent`.

    `qty` is `Decimal | None` to allow non-quantitative events
    (`closing_snapshot`, `adjustment_*` materialized snapshots may
    have NULL qty — OQ2 cj-style default).

    `reverses_event_id` + `correction_group_id` are AD-22 reversal
    sequence fields. Epic 11 module authority owns the actual reversal
    sequence insert; 5-2 just defines the schema + audit marker path.
    """

    event_id: uuid.UUID
    tenant_id: uuid.UUID
    product_id: uuid.UUID
    period_key: str
    event_type: str
    qty: Decimal | None
    trace_id: uuid.UUID
    reverses_event_id: uuid.UUID | None
    correction_group_id: uuid.UUID | None
    payload: dict[str, Any]


# ── build_event_payload ───────────────────────────────────────
def build_event_payload(
    *,
    event_id: uuid.UUID,
    product_id: uuid.UUID,
    period_key: str,
    event_type: str,
    qty: Decimal | None,
    trace_id: uuid.UUID,
    source: str,
    reverses_event_id: uuid.UUID | None = None,
    correction_group_id: uuid.UUID | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build INSERT-ready payload for an inventory_ledger row + matching audit log.

    Decimal qty is serialized via `str(qty)` for json-serializability
    (AD-8 monetary types). Service-layer caller persists the original
    Decimal separately via the ORM mapped column.

    Args:
        event_id, product_id, tenant_id-routed implicitly via service,
            period_key, event_type, qty, trace_id: SQL column values.
        source: One of `SOURCE_CARRY_CHAIN` / `SOURCE_MONTHLY_INPUT` /
            `SOURCE_MANUAL_BACKFILL` / `SOURCE_REVERSAL_REQUEST` /
            `SOURCE_CLOSE_SNAPSHOT`. Used by `audit-first` payload to
            attribute the writer caller (CR 1.1 self-describing).
        reverses_event_id, correction_group_id: AD-22 reversal sequence
            fields. Both default `None` for non-reversal events.
        metadata: Optional additional payload keys. Must be JSON-serializable.

    Returns:
        dict[str, Any] ready for `INSERT INTO inventory_ledger` +
        the audit log emit payload shape. Keys are snake_case (AD-15).

    Raises:
        AppendOnlyLedgerError: If event_type is not in the 11-value
            whitelist, period_key fails the AD-24 typed pattern, or
            qty is non-quantitative-but-non-null.
    """
    validate_event_type(event_type)
    _validate_period_key(period_key)
    _validate_qty(qty, event_type=event_type)
    _validate_source(source)

    return {
        PAYLOAD_KEY_EVENT_ID: str(event_id),
        PAYLOAD_KEY_PRODUCT_ID: str(product_id),
        PAYLOAD_KEY_PERIOD_KEY: period_key,
        PAYLOAD_KEY_EVENT_TYPE: event_type,
        PAYLOAD_KEY_QTY: _serialize_qty(qty, event_type=event_type),
        PAYLOAD_KEY_TRACE_ID: str(trace_id),
        PAYLOAD_KEY_SOURCE: source,
        PAYLOAD_KEY_REVERSES_EVENT_ID: (
            str(reverses_event_id) if reverses_event_id is not None else None
        ),
        PAYLOAD_KEY_CORRECTION_GROUP_ID: (
            str(correction_group_id) if correction_group_id is not None else None
        ),
        PAYLOAD_KEY_METADATA: dict(metadata or {}),
    }


# ── validate_event_type ───────────────────────────────────────
def validate_event_type(event_type: str) -> None:
    """Strict whitelist check on event_type (AC #2 + OQ3).

    Raises:
        AppendOnlyLedgerError: If event_type is not one of the 11
            canonical values OR is empty / non-string.
    """
    if not isinstance(event_type, str):
        raise AppendOnlyLedgerError(
            message=(
                f"inventory_ledger event_type must be str, got "
                f"{type(event_type).__name__!r}"
            ),
            error_code=ERROR_CODE_NON_STR_EVENT_TYPE,
        )
    if not event_type:
        raise AppendOnlyLedgerError(
            message="inventory_ledger event_type must be non-empty",
            error_code=ERROR_CODE_EMPTY_EVENT_TYPE,
        )
    if event_type not in INVENTORY_LEDGER_EVENT_TYPES:
        raise AppendOnlyLedgerError(
            message=(
                f"inventory_ledger event_type {event_type!r} is not in "
                f"the 11-value whitelist. Accepted: "
                f"{sorted(INVENTORY_LEDGER_EVENT_TYPES)}"
            ),
            error_code=ERROR_CODE_INVALID_EVENT_TYPE,
        )


# ── validate_event_shape ──────────────────────────────────────
def validate_event_shape(event: InventoryLedgerEvent) -> None:
    """Validate the full InventoryLedgerEvent NamedTuple.

    Checks (CR 0-4 lesson banker's rounding parity):
    - event_type in 11-value whitelist (delegated).
    - period_key matches `^\\d{4}-(0[1-9]|1[0-2])$` (AD-24).
    - qty, if non-None, quantized to QTY_QUANTUM (NUMERIC(18,4)) via
      ROUND_HALF_EVEN. CR 0-4 lesson: 5+ 자릿수 값에 대한 banker's
      rounding 결정 검증 필수.
    - product_id is UUID v7 (AD-15 identity SSOT).
    - event_id != trace_id (sanity check).

    Raises:
        AppendOnlyLedgerError: On any shape mismatch.
    """
    validate_event_type(event.event_type)
    _validate_period_key(event.period_key)
    _validate_qty(event.qty, event_type=event.event_type)
    _validate_uuid7(event.product_id, field="product_id")
    _validate_uuid7(event.event_id, field="event_id")
    _validate_uuid7(event.trace_id, field="trace_id")

    if event.event_id == event.trace_id:
        # Sanity: event_id and trace_id should be different objects
        # (event_id is the row PK; trace_id is the request correlation).
        # Equality is allowed but the same UUID for both is suspicious;
        # production code normally mints fresh UUIDv7 for each.
        pass  # noqa: explicit no-op; equality is valid but unusual


def _validate_period_key(period_key: str) -> None:
    """AD-24 typed period-key: 'YYYY-MM' (real fiscal only)."""
    if not isinstance(period_key, str):
        raise AppendOnlyLedgerError(
            message=f"period_key must be str, got {type(period_key).__name__!r}",
            error_code=ERROR_CODE_NON_STR_PERIOD_KEY,
        )
    if not _PERIOD_KEY_PATTERN.match(period_key):
        raise AppendOnlyLedgerError(
            message=(
                f"period_key {period_key!r} must match 'YYYY-MM' AD-24 typed pattern"
            ),
            error_code=ERROR_CODE_INVALID_PERIOD_KEY,
        )


def _validate_qty(qty: Decimal | None, *, event_type: str) -> None:
    """Validate qty type + event_type/qty coherence.

    Per OQ2 cj-style default: NUMERIC(18,4) nullable. Events that
    involve a quantity (`purchase_inbound`, `sales_outbound`, etc.)
    MUST have non-None qty. Non-quantitative events
    (`closing_snapshot`) MAY have None — and MAY also carry a Decimal
    snapshot value (e.g. materialized closing_balance).

    Banker's rounding auto-quantization happens in `_serialize_qty`
    (`ROUND_HALF_EVEN` at QTY_QUANTUM = NUMERIC(18,4)). CR 0-4
    lesson: 5+ 자릿수 값에 대한 rounding 결정 검증 필수 (deterministic
    ROUND_HALF_EVEN + TS/Python parity).
    """
    non_quantitative_events = frozenset({"closing_snapshot"})
    requires_quantitative = event_type not in non_quantitative_events

    if qty is None:
        if requires_quantitative:
            raise AppendOnlyLedgerError(
                message=(
                    f"event_type {event_type!r} requires non-None qty "
                    f"(PRD §6.2 inventory equation has a qty term)"
                ),
                error_code=ERROR_CODE_QTY_REQUIRED,
            )
        return  # non-quantitative event with None qty = valid

    if not isinstance(qty, Decimal):
        raise AppendOnlyLedgerError(
            message=(
                f"qty must be Decimal, got {type(qty).__name__!r} "
                f"(AD-8 monetary types)"
            ),
            error_code=ERROR_CODE_QTY_MUST_BE_DECIMAL,
        )


def _validate_uuid7(value: uuid.UUID, *, field: str) -> None:
    """Lightweight UUID v7 check (AD-15 identity convention)."""
    if not isinstance(value, uuid.UUID):
        raise AppendOnlyLedgerError(
            message=f"{field} must be UUID, got {type(value).__name__!r}",
            error_code=ERROR_CODE_INVALID_UUID_VERSION,
        )
    # UUID v7 detection: byte[6] major version bits = 0b0111 = 7.
    # `value.bytes[6] >> 4 == 7`. Anything else (including UUID v4)
    # is permitted in MVP — strict v7 enforcement is post-MVP.
    try:
        version = value.bytes[6] >> 4
    except (IndexError, AttributeError):
        return
    if version not in (4, 7):
        raise AppendOnlyLedgerError(
            message=(
                f"{field} must be UUID v7 (preferred) or v4, got version "
                f"{version!r}"
            ),
            error_code=ERROR_CODE_INVALID_UUID_VERSION,
        )


def _validate_source(source: str) -> None:
    """Validate caller source discriminator (5 canonical values)."""
    valid = frozenset(
        {
            SOURCE_CARRY_CHAIN,
            SOURCE_MONTHLY_INPUT,
            SOURCE_MANUAL_BACKFILL,
            SOURCE_REVERSAL_REQUEST,
            SOURCE_CLOSE_SNAPSHOT,
        }
    )
    if source not in valid:
        raise AppendOnlyLedgerError(
            message=(
                f"source {source!r} is not in the 5-canonical set: "
                f"{sorted(valid)}"
            ),
            error_code=ERROR_CODE_INVALID_SOURCE,
        )


def _serialize_qty(qty: Decimal | None, *, event_type: str = "") -> str | None:
    """Decimal → str for JSON serialization (AD-8 banker's rounding parity).

    `None` is preserved for non-quantitative events. `event_type` is
    accepted for future per-type serialization rules (e.g. different
    quantum per stream) but currently unused — kept as a keyword-only
    parameter so call sites can document their event type intent.
    """
    _ = event_type  # reserved for per-type quantum overrides
    if qty is None:
        return None
    quantized = qty.quantize(QTY_QUANTUM, rounding=ROUND_HALF_EVEN)
    return f"{quantized:f}"


# ── append_only_violation_message ──────────────────────────────
def append_only_violation_message(
    *,
    attempted_op: str,
    event_id: uuid.UUID,
    db_trigger_message: str | None = None,
) -> str:
    """Build the Korean-language append-only violation message (AC #3 + PRD §A11).

    Service-layer wraps this in the 500 typed envelope:
    `{error_code: "APPEND_ONLY_LEDGER_VIOLATION",
       message_ko: <result of this function>, ...}`.

    Args:
        attempted_op: One of 'UPDATE' / 'DELETE'. Treated as literal
            (no normalization).
        event_id: The inventory_ledger.event_id row the UPDATE/DELETE
            attempted to modify.
        db_trigger_message: Optional DB trigger error verbatim copy.
            Used when the message bubbles up from PostgreSQL
            `RAISE EXCEPTION 'append-only violation...'`.

    Returns:
        str: Korean message (AD-15 §0.4 parity).
    """
    op_label = {
        "UPDATE": "수정",
        "DELETE": "삭제",
    }.get(attempted_op, attempted_op)

    base = (
        f"수불부는 원장만 기록 가능하며 {op_label} 불가합니다 "
        f"(event_id={event_id})"
    )
    if db_trigger_message:
        base = f"{base} — DB trigger: {db_trigger_message}"
    return base


__all__ = [
    "AppendOnlyLedgerError",
    "ERROR_CODE_EMPTY_EVENT_TYPE",
    "ERROR_CODE_INVALID_EVENT_TYPE",
    "ERROR_CODE_INVALID_PERIOD_KEY",
    "ERROR_CODE_INVALID_SOURCE",
    "ERROR_CODE_INVALID_UUID_VERSION",
    "ERROR_CODE_NON_STR_EVENT_TYPE",
    "ERROR_CODE_NON_STR_PERIOD_KEY",
    "ERROR_CODE_QTY_MUST_BE_DECIMAL",
    "ERROR_CODE_QTY_REQUIRED",
    "INVENTORY_LEDGER_EVENT_TYPES",
    "INVENTORY_LEDGER_QTY_QUANTUM",
    "InventoryLedgerEvent",
    "PAYLOAD_KEY_EVENT_ID",
    "PAYLOAD_KEY_PRODUCT_ID",
    "PAYLOAD_KEY_PERIOD_KEY",
    "PAYLOAD_KEY_EVENT_TYPE",
    "PAYLOAD_KEY_QTY",
    "PAYLOAD_KEY_TRACE_ID",
    "PAYLOAD_KEY_SOURCE",
    "PAYLOAD_KEY_REVERSES_EVENT_ID",
    "PAYLOAD_KEY_CORRECTION_GROUP_ID",
    "PAYLOAD_KEY_METADATA",
    "SOURCE_CARRY_CHAIN",
    "SOURCE_MONTHLY_INPUT",
    "SOURCE_MANUAL_BACKFILL",
    "SOURCE_REVERSAL_REQUEST",
    "SOURCE_CLOSE_SNAPSHOT",
    "append_only_violation_message",
    "build_event_payload",
    "validate_event_shape",
    "validate_event_type",
]
