"""packages.services.m5_ledger.count_period_events — Story 11.1 pure kernel (H6 fix).

H6 production bug fix: `closing_period_service.py:528/531` calls
`LedgerService.count_period_events(period_key)` and
`LedgerService.count_period_events(period_key, event_type="closing_snapshot")`.
These methods were not defined (pre-6-2 wire). This pure kernel
provides the SQL builder + kwargs guard so the service-layer method
can dispatch without an AttributeError.

AD-1 / AD-11 binding: pure-Python, stdlib-only, NO SQLAlchemy, NO DB,
NO clock, NO random. Returns `(sql_text, params_dict)` ready for
`session.execute(text(sql), params)`.

Drift caught by `tests/services/m5_ledger/test_count_period_events.py`.
"""

from __future__ import annotations

from typing import Any, Final

# ── Constants ────────────────────────────────────────────────
# 11-value event_type whitelist (mirror of `ledger.INVENTORY_LEDGER_EVENT_TYPES`).
# The SQL builder only filters by event_type when the caller passes
# a non-None value; the parent kernel's whitelist guard runs at
# INSERT-time (not COUNT-time).
_VALID_EVENT_TYPES: Final[frozenset[str]] = frozenset(
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

# Error codes — pure-kernel domain semantics.
ERROR_CODE_EMPTY_PERIOD_KEY: Final[str] = "EMPTY_PERIOD_KEY"
ERROR_CODE_NON_STR_PERIOD_KEY: Final[str] = "NON_STR_PERIOD_KEY"
ERROR_CODE_INVALID_EVENT_TYPE: Final[str] = "INVALID_EVENT_TYPE"


# ── Typed exception ──────────────────────────────────────────
class CountPeriodEventsBuildError(Exception):
    """Pure-kernel count SQL builder violation.

    NO HTTP mapping; service layer wraps with envelope details.
    Service-layer dispatch uses `err.error_code` (stable Literal).
    """

    def __init__(
        self,
        *,
        message: str,
        error_code: str = ERROR_CODE_EMPTY_PERIOD_KEY,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code


# ── count_period_events_sql ──────────────────────────────────
def count_period_events_sql(
    period_key: str,
    *,
    event_type: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """Build (text SQL, params dict) for counting inventory_ledger rows.

    AD-11 layer rule: text-only SQL builder. Caller (service layer)
    wraps with `text(sql)` and `session.execute(text(sql), params)`.
    The `tenant_id` parameter is auto-injected by RLS context — this
    builder does NOT inline tenant_id (DRY with the RLS-scoped session).

    Args:
        period_key: AD-24 typed period-key ('YYYY-MM'). Required.
        event_type: Optional event_type filter. If None, counts all
            rows for the period. If provided, must be in the 11-value
            whitelist (defense-in-depth — though SQL would simply
            return 0 for unknown types).

    Returns:
        Tuple of (sql_text, params_dict). `params_dict` keys: period_key,
        optional event_type.

    Raises:
        CountPeriodEventsBuildError: On invalid period_key / event_type.
    """
    if not isinstance(period_key, str):
        raise CountPeriodEventsBuildError(
            message=f"period_key must be str, got {type(period_key).__name__!r}",
            error_code=ERROR_CODE_NON_STR_PERIOD_KEY,
        )
    if not period_key:
        raise CountPeriodEventsBuildError(
            message="period_key must be non-empty",
            error_code=ERROR_CODE_EMPTY_PERIOD_KEY,
        )

    if event_type is None:
        # Unfiltered count — used by closing_period_service.py:528.
        sql = (
            "SELECT COUNT(*) AS row_count "
            "FROM inventory_ledger "
            "WHERE period_key = :period_key"
        )
        params: dict[str, Any] = {"period_key": period_key}
        return sql, params

    if not isinstance(event_type, str):
        raise CountPeriodEventsBuildError(
            message=f"event_type must be str when provided, got {type(event_type).__name__!r}",
            error_code=ERROR_CODE_INVALID_EVENT_TYPE,
        )
    if event_type not in _VALID_EVENT_TYPES:
        raise CountPeriodEventsBuildError(
            message=(
                f"event_type {event_type!r} is not in the 11-value whitelist. "
                f"Accepted: {sorted(_VALID_EVENT_TYPES)}"
            ),
            error_code=ERROR_CODE_INVALID_EVENT_TYPE,
        )

    # Filtered count — used by closing_period_service.py:531
    # (`event_type="closing_snapshot"` for closing_snapshot_count).
    sql = (
        "SELECT COUNT(*) AS row_count "
        "FROM inventory_ledger "
        "WHERE period_key = :period_key AND event_type = :event_type"
    )
    params = {"period_key": period_key, "event_type": event_type}
    return sql, params


__all__ = [
    "ERROR_CODE_EMPTY_PERIOD_KEY",
    "ERROR_CODE_NON_STR_PERIOD_KEY",
    "ERROR_CODE_INVALID_EVENT_TYPE",
    "CountPeriodEventsBuildError",
    "count_period_events_sql",
]
