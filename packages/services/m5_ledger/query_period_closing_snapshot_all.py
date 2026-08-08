"""packages.services.m5_ledger.query_period_closing_snapshot_all — Story 11.1 pure kernel (H6 fix).

H6 production bug fix: `closing_period_service.py:528/531` (closing
period aggregator) calls `LedgerService.query_period_closing_snapshot_all(period_key)`.
This method was not defined. This pure kernel provides the SQL builder
for the per-product closing_snapshot aggregate so the service-layer
method can dispatch without an AttributeError.

AD-1 / AD-11 binding: pure-Python, stdlib-only, NO SQLAlchemy, NO DB,
NO clock, NO random. Returns `(sql_text, params_dict)` ready for
`session.execute(text(sql), params)`.

Drift caught by `tests/services/m5_ledger/test_query_period_closing_snapshot_all.py`.
"""

from __future__ import annotations

from typing import Any, Final

# ── Constants ────────────────────────────────────────────────
ERROR_CODE_EMPTY_PERIOD_KEY: Final[str] = "EMPTY_PERIOD_KEY"
ERROR_CODE_NON_STR_PERIOD_KEY: Final[str] = "NON_STR_PERIOD_KEY"


# ── Typed exception ──────────────────────────────────────────
class QueryPeriodClosingSnapshotAllBuildError(Exception):
    """Pure-kernel closing_snapshot aggregate SQL builder violation.

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


# ── query_period_closing_snapshot_all_sql ────────────────────
def query_period_closing_snapshot_all_sql(
    period_key: str,
) -> tuple[str, dict[str, Any]]:
    """Build (text SQL, params dict) for per-product closing_snapshot aggregate.

    Used by `closing_period_service.py` after the M4 forward-fill fix
    (`LedgerService.count_period_events` companion). Returns one row
    per product with `SUM(qty)` over all `event_type='closing_snapshot'`
    rows for the period. RLS auto-filters by tenant_id.

    Args:
        period_key: AD-24 typed period-key ('YYYY-MM'). Required.

    Returns:
        Tuple of (sql_text, params_dict). Result rows: product_id (UUID
        str), closing_qty (Decimal string).

    Raises:
        QueryPeriodClosingSnapshotAllBuildError: On invalid period_key.
    """
    if not isinstance(period_key, str):
        raise QueryPeriodClosingSnapshotAllBuildError(
            message=f"period_key must be str, got {type(period_key).__name__!r}",
            error_code=ERROR_CODE_NON_STR_PERIOD_KEY,
        )
    if not period_key:
        raise QueryPeriodClosingSnapshotAllBuildError(
            message="period_key must be non-empty",
            error_code=ERROR_CODE_EMPTY_PERIOD_KEY,
        )

    sql = (
        "SELECT product_id, SUM(qty) AS closing_qty "
        "FROM inventory_ledger "
        "WHERE period_key = :period_key AND event_type = 'closing_snapshot' "
        "GROUP BY product_id"
    )
    params: dict[str, Any] = {"period_key": period_key}
    return sql, params


__all__ = [
    "ERROR_CODE_EMPTY_PERIOD_KEY",
    "ERROR_CODE_NON_STR_PERIOD_KEY",
    "QueryPeriodClosingSnapshotAllBuildError",
    "query_period_closing_snapshot_all_sql",
]
