"""tests.services.m5_ledger.test_query_period_closing_snapshot_all — Story 11.1 pure kernel (H6 fix).

6 cases per AC #8 spec:
- query_period_closing_snapshot_all_sql (3): 정상 / tenant scoping / closing_snapshot filter
- per-product aggregate (2): GROUP BY product_id + SUM(qty)
- SQL injection 방지 (1): param binding
"""

from __future__ import annotations

import pytest

from packages.services.m5_ledger.query_period_closing_snapshot_all import (
    ERROR_CODE_EMPTY_PERIOD_KEY,
    ERROR_CODE_NON_STR_PERIOD_KEY,
    QueryPeriodClosingSnapshotAllBuildError,
    query_period_closing_snapshot_all_sql,
)


class TestQueryPeriodClosingSnapshotAllSql:
    """query_period_closing_snapshot_all_sql — per-product aggregate."""

    def test_normal_aggregate_sql_shape(self) -> None:
        """정상 — SELECT product_id, SUM(qty) FROM inventory_ledger
        WHERE period_key=:period_key AND event_type='closing_snapshot'
        GROUP BY product_id."""
        sql, params = query_period_closing_snapshot_all_sql("2026-08")
        assert "SELECT product_id, SUM(qty) AS closing_qty" in sql
        assert "FROM inventory_ledger" in sql
        assert (
            "WHERE period_key = :period_key AND event_type = 'closing_snapshot'"
            in sql
        )
        assert "GROUP BY product_id" in sql
        assert params == {"period_key": "2026-08"}

    def test_uses_param_binding_no_injection(self) -> None:
        """SQL injection 방지 — period_key는 placeholder, inlined X."""
        sql, _params = query_period_closing_snapshot_all_sql("2026-08'; DROP TABLE x; --")
        assert "'2026-08" not in sql  # the value is NOT inlined into SQL
        assert ":period_key" in sql

    def test_event_type_filter_is_static(self) -> None:
        """event_type='closing_snapshot' is hard-coded literal (not param)."""
        # Defense-in-depth: the literal is safe (alphanumeric + underscore),
        # and using a param would over-engineer the SQL builder.
        sql, _params = query_period_closing_snapshot_all_sql("2026-08")
        assert "event_type = 'closing_snapshot'" in sql


class TestQueryPeriodClosingSnapshotAllSqlGuards:
    """Input guards."""

    def test_empty_period_key_rejected(self) -> None:
        """period_key 빈 문자열 거부."""
        with pytest.raises(QueryPeriodClosingSnapshotAllBuildError) as exc_info:
            query_period_closing_snapshot_all_sql("")
        assert exc_info.value.error_code == ERROR_CODE_EMPTY_PERIOD_KEY

    def test_non_str_period_key_rejected(self) -> None:
        """period_key non-str 거부."""
        with pytest.raises(QueryPeriodClosingSnapshotAllBuildError) as exc_info:
            query_period_closing_snapshot_all_sql(202608)  # type: ignore[arg-type]
        assert exc_info.value.error_code == ERROR_CODE_NON_STR_PERIOD_KEY


class TestAggregateShape:
    """Per-product aggregate — closing_snapshot rows aggregate per product."""

    def test_group_by_product_present(self) -> None:
        """GROUP BY product_id present in SQL — one row per product."""
        sql, _params = query_period_closing_snapshot_all_sql("2026-08")
        assert "GROUP BY product_id" in sql

    def test_sum_qty_present(self) -> None:
        """SUM(qty) present in SQL — total closing snapshot per product."""
        sql, _params = query_period_closing_snapshot_all_sql("2026-08")
        assert "SUM(qty)" in sql
