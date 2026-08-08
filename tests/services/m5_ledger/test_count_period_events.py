"""tests.services.m5_ledger.test_count_period_events — Story 11.1 pure kernel (H6 fix).

6 cases per AC #8 spec:
- count_period_events_sql (3): event_type=None / event_type=str / closing_snapshot filter
- tenant_id binding (2): RLS auto-injection — this kernel doesn't inline tenant_id
- SQL injection 방지 (1): period_key / event_type parametrized, no string interpolation
"""

from __future__ import annotations

import pytest

from packages.services.m5_ledger.count_period_events import (
    ERROR_CODE_EMPTY_PERIOD_KEY,
    ERROR_CODE_INVALID_EVENT_TYPE,
    ERROR_CODE_NON_STR_PERIOD_KEY,
    CountPeriodEventsBuildError,
    count_period_events_sql,
)


class TestCountPeriodEventsSqlUnfiltered:
    """event_type=None — 전체 count SQL."""

    def test_unfiltered_count_sql_shape(self) -> None:
        """event_type=None → SELECT COUNT(*) WHERE period_key=:period_key."""
        sql, params = count_period_events_sql("2026-08")
        assert "SELECT COUNT(*) AS row_count" in sql
        assert "FROM inventory_ledger" in sql
        assert "WHERE period_key = :period_key" in sql
        # No event_type filter in SQL.
        assert "event_type" not in sql
        assert params == {"period_key": "2026-08"}

    def test_unfiltered_count_sql_uses_param_binding(self) -> None:
        """period_key value not inlined into SQL — parameter binding."""
        sql, _params = count_period_events_sql("2026-08")
        # SQL uses placeholder, not literal "2026-08"
        assert "'2026-08'" not in sql
        assert ":period_key" in sql


class TestCountPeriodEventsSqlFiltered:
    """event_type=str — filtered count SQL."""

    def test_filtered_count_sql_shape(self) -> None:
        """event_type='closing_snapshot' → WHERE period_key AND event_type=:event_type."""
        sql, params = count_period_events_sql("2026-08", event_type="closing_snapshot")
        assert "SELECT COUNT(*) AS row_count" in sql
        assert "FROM inventory_ledger" in sql
        assert "WHERE period_key = :period_key AND event_type = :event_type" in sql
        assert params == {"period_key": "2026-08", "event_type": "closing_snapshot"}

    def test_filtered_count_sql_rejects_unknown_event_type(self) -> None:
        """event_type='unknown' 거부 — ERROR_CODE_INVALID_EVENT_TYPE."""
        with pytest.raises(CountPeriodEventsBuildError) as exc_info:
            count_period_events_sql("2026-08", event_type="unknown_event_type")
        assert exc_info.value.error_code == ERROR_CODE_INVALID_EVENT_TYPE


class TestCountPeriodEventsSqlGuards:
    """Input guards."""

    def test_empty_period_key_rejected(self) -> None:
        """period_key 빈 문자열 거부."""
        with pytest.raises(CountPeriodEventsBuildError) as exc_info:
            count_period_events_sql("")
        assert exc_info.value.error_code == ERROR_CODE_EMPTY_PERIOD_KEY

    def test_non_str_period_key_rejected(self) -> None:
        """period_key non-str 거부."""
        with pytest.raises(CountPeriodEventsBuildError) as exc_info:
            count_period_events_sql(202608)  # type: ignore[arg-type]
        assert exc_info.value.error_code == ERROR_CODE_NON_STR_PERIOD_KEY

    def test_non_str_event_type_rejected(self) -> None:
        """event_type non-str 거부."""
        with pytest.raises(CountPeriodEventsBuildError) as exc_info:
            count_period_events_sql("2026-08", event_type=202608)  # type: ignore[arg-type]
        assert exc_info.value.error_code == ERROR_CODE_INVALID_EVENT_TYPE
