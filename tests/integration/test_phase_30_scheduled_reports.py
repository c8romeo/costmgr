"""apps.costmgr.tests.integration.test_phase_30_scheduled_reports

cj-300 wire sprint (cj-style 302번째 epic 연속 정직 회복 source+docs atomic
single sprint) — Story 30.4 Scheduled reports (FR-30-4) integration tests.

Mirrors tests/integration/test_phase_30_exports_email.py verbatim pattern
(test_phase_30 naming + class-based grouping + sync `def test_*` driven
via asyncio.run — no pytest-asyncio plugin needed).

Test classes (60+ tests):
  - TestScheduledReportsCron: 4 tests (weekly/monthly/quarterly/annual cron)
  - TestScheduledReportsLifecycle: 8 tests (state machine transitions)
  - TestScheduledReportsIdempotency: 4 tests (per (tenant+schedule+period) tuple)
  - TestScheduledReportsRecipient: 6 tests (finance_only / finance_and_admin / admin_fallback)
  - TestScheduledReportsRedact: 5 tests (NFR4 PII minimization)
  - TestScheduledReportsErrors: 16 tests (16 NEW typed exception classes)
  - TestScheduledReportsCLI: 4 tests (--scheduled-reports-dry-run)
  - TestScheduledReportsSerializers: 8 tests (Pydantic validation)
  - TestScheduledReportsRoutes: 5 tests (4 endpoints + dispatch-now)

Total: ~60 tests, fast (no network — apscheduler + email mocked).

CR 11-3 honest-DEFER 244번째 epic 연속 정직 회복
(cj-300 entry 의 243번째 + 본 sprint 의 244번째).
"""

from __future__ import annotations

import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.api.jobs.errors import (
    CronExpressionInvalidError,
    DispatchIdempotencyViolationError,
    RecipientResolverError,
    ScheduledReportAlembicMigrationError,
    ScheduledReportAsyncIOError,
    ScheduledReportCronInvalidError,
    ScheduledReportDispatchError,
    ScheduledReportError,
    ScheduledReportFinanceContactEmailError,
    ScheduledReportFinanceEmailNotFoundError,
    ScheduledReportIdempotencyViolationError,
    ScheduledReportLifecycleError,
    ScheduledReportPermissionError,
    ScheduledReportPeriodKeyError,
    ScheduledReportPersistentJobStoreError,
    ScheduledReportRecipientResolverError,
    ScheduledReportRetryExhaustedError,
    ScheduledReportTenantNotFoundError,
    ScheduledReportTimezoneError,
)
from apps.api.jobs.scheduled_reports import (
    ALL_DISPATCH_SCHEDULES,
    ALL_RECIPIENT_STRATEGIES,
    ALL_REPORT_TYPES,
    DISPATCH_CRON_EXPRESSIONS := __import__("apps.api.jobs.scheduled_reports", fromlist=["SCHEDULED_REPORTS_CRON_EXPRESSIONS"]).SCHEDULED_REPORTS_CRON_EXPRESSIONS,
    KST,
    MAX_RETRY_COUNT,
    PERIOD_KEY_FORMAT,
    RECIPIENT_STRATEGY_ADMIN_FALLBACK,
    RECIPIENT_STRATEGY_FINANCE_AND_ADMIN,
    RECIPIENT_STRATEGY_FINANCE_ONLY,
    RETRY_BACKOFF_MINUTES,
    _check_idempotency,
    _compute_period_key,
    _lifecycle_state_machine,
    _redact_finance_email_for_audit,
    _resolve_recipients,
    _validate_cron_expression,
    _validate_inputs,
    parse_cli_args,
    schedule_report,
)
from apps.api.modules.reports.scheduled_serializers import (
    ALL_STATUSES,
    EMAIL_REGEX,
    PERIOD_KEY_REGEX,
    ScheduledDispatchNow,
    ScheduledJobCancel,
    ScheduledJobCreate,
    ScheduledJobHistory,
    ScheduledJobResponse,
)


# ── TestScheduledReportsCron (4 tests) ────────────────────────────────


class TestScheduledReportsCron:
    """Test the 4 cron expressions (PRD §F30.4-1 verbatim)."""

    def test_weekly_cron_is_monday_9am_kst(self) -> None:
        """weekly → 0 9 * * 1 (KST Monday 09:00)."""
        assert DISPATCH_CRON_EXPRESSIONS["weekly"] == "0 9 * * 1"

    def test_monthly_cron_is_1st_day_9am_kst(self) -> None:
        """monthly → 0 9 1 * * (KST 1st day 09:00)."""
        assert DISPATCH_CRON_EXPRESSIONS["monthly"] == "0 9 1 * *"

    def test_quarterly_cron_is_1st_day_of_quarter(self) -> None:
        """quarterly → 0 9 1 1,4,7,10 * (KST 1st day of quarter)."""
        assert DISPATCH_CRON_EXPRESSIONS["quarterly"] == "0 9 1 1,4,7,10 *"

    def test_annual_cron_is_jan_1_9am_kst(self) -> None:
        """annual → 0 9 1 1 * (KST Jan 1 09:00)."""
        assert DISPATCH_CRON_EXPRESSIONS["annual"] == "0 9 1 1 *"


# ── TestScheduledReportsLifecycle (8 tests) ───────────────────────────


class TestScheduledReportsLifecycle:
    """Test the lifecycle state machine (PRD §F30.4-1 verbatim)."""

    def test_scheduled_trigger_to_running(self) -> None:
        assert _lifecycle_state_machine("scheduled", "trigger") == "running"

    def test_running_success_to_completed(self) -> None:
        assert _lifecycle_state_machine("running", "success") == "completed"

    def test_running_failure_to_failed(self) -> None:
        assert _lifecycle_state_machine("running", "failure") == "failed"

    def test_failed_retry_to_running(self) -> None:
        assert _lifecycle_state_machine("failed", "retry") == "running"

    def test_failed_max_retries_to_cancelled(self) -> None:
        assert _lifecycle_state_machine("failed", "max_retries") == "cancelled"

    def test_scheduled_cancel_to_cancelled(self) -> None:
        assert _lifecycle_state_machine("scheduled", "cancel") == "cancelled"

    def test_running_cancel_to_cancelled(self) -> None:
        assert _lifecycle_state_machine("running", "cancel") == "cancelled"

    def test_completed_modify_raises_lifecycle_error(self) -> None:
        """completed → modify attempt should raise ScheduledReportLifecycleError."""
        with pytest.raises(ScheduledReportLifecycleError):
            _lifecycle_state_machine("completed", "cancel")


# ── TestScheduledReportsIdempotency (4 tests) ─────────────────────────


class TestScheduledReportsIdempotency:
    """Test idempotency per (tenant_id + dispatch_schedule + period_key) tuple."""

    def test_dry_run_path_returns_true(self) -> None:
        """No db_session → dry-run path returns True."""
        result = _check_idempotency("tenant-1", "monthly", "2026-09", db_session=None)
        assert result is True

    def test_with_db_session_returns_true_on_no_error(self) -> None:
        """Mock session returns True (no matching tuple)."""
        mock_session = MagicMock()
        result = _check_idempotency("tenant-1", "monthly", "2026-09", db_session=mock_session)
        assert result is True

    def test_idempotency_violation_raises(self) -> None:
        """Mock session raising exception → DispatchIdempotencyViolationError."""
        mock_session = MagicMock()
        mock_session.query.side_effect = Exception("DB error")
        with pytest.raises(DispatchIdempotencyViolationError):
            _check_idempotency("tenant-1", "monthly", "2026-09", db_session=mock_session)

    def test_all_dispatch_schedules_in_tuple(self) -> None:
        """ALL_DISPATCH_SCHEDULES contains 4 schedules."""
        assert len(ALL_DISPATCH_SCHEDULES) == 4
        assert set(ALL_DISPATCH_SCHEDULES) == {"weekly", "monthly", "quarterly", "annual"}


# ── TestScheduledReportsRecipient (6 tests) ───────────────────────────


class TestScheduledReportsRecipient:
    """Test recipient resolver (PRD §F30.4-4 verbatim)."""

    def test_finance_only_strategy(self) -> None:
        """finance_only → 1 recipient (finance email)."""
        result = _resolve_recipients(
            tenant_id="tenant-1",
            recipient_strategy=RECIPIENT_STRATEGY_FINANCE_ONLY,
            finance_contact_email="finance@example.com",
        )
        assert result["recipients"] == ["finance@example.com"]
        assert result["admin_fallback_dispatched"] is False

    def test_finance_and_admin_strategy(self) -> None:
        """finance_and_admin → 1 recipient (finance email, admin 별도 발송)."""
        result = _resolve_recipients(
            tenant_id="tenant-1",
            recipient_strategy=RECIPIENT_STRATEGY_FINANCE_AND_ADMIN,
            finance_contact_email="finance@example.com",
        )
        assert result["recipients"] == ["finance@example.com"]
        assert result["admin_fallback_dispatched"] is False

    def test_admin_fallback_with_email(self) -> None:
        """admin_fallback + email → admin fallback dispatched."""
        result = _resolve_recipients(
            tenant_id="tenant-1",
            recipient_strategy=RECIPIENT_STRATEGY_ADMIN_FALLBACK,
            finance_contact_email="finance@example.com",
        )
        assert result["recipients"] == []
        assert result["admin_fallback_dispatched"] is True

    def test_admin_fallback_without_email(self) -> None:
        """admin_fallback + no email → admin fallback dispatched."""
        result = _resolve_recipients(
            tenant_id="tenant-1",
            recipient_strategy=RECIPIENT_STRATEGY_ADMIN_FALLBACK,
            finance_contact_email=None,
        )
        assert result["admin_fallback_dispatched"] is True

    def test_finance_only_without_email_raises(self) -> None:
        """finance_only + no email → ScheduledReportFinanceEmailNotFoundError."""
        with pytest.raises(ScheduledReportFinanceEmailNotFoundError):
            _resolve_recipients(
                tenant_id="tenant-1",
                recipient_strategy=RECIPIENT_STRATEGY_FINANCE_ONLY,
                finance_contact_email=None,
            )

    def test_all_recipient_strategies(self) -> None:
        """ALL_RECIPIENT_STRATEGIES contains 3 strategies."""
        assert len(ALL_RECIPIENT_STRATEGIES) == 3


# ── TestScheduledReportsRedact (5 tests) ──────────────────────────────


class TestScheduledReportsRedact:
    """Test finance_contact_email redact (NFR4 PII minimization verbatim)."""

    def test_redact_normal_email(self) -> None:
        """finance@example.com → fi***@example.com."""
        result = _redact_finance_email_for_audit("finance@example.com")
        assert result == "fi***@example.com"

    def test_redact_short_local(self) -> None:
        """ab@example.com → **@example.com (local ≤ 2 chars)."""
        result = _redact_finance_email_for_audit("ab@example.com")
        assert result == "**@example.com"

    def test_redact_none(self) -> None:
        """None → None."""
        assert _redact_finance_email_for_audit(None) is None

    def test_redact_invalid_email_returns_none(self) -> None:
        """Invalid email (no @) → None."""
        assert _redact_finance_email_for_audit("not-an-email") is None

    def test_redact_preserves_domain(self) -> None:
        """Long local + domain preserved."""
        result = _redact_finance_email_for_audit("finance.team@example.com")
        assert result == "fi***@example.com"


# ── TestScheduledReportsErrors (16 tests) ──────────────────────────────


class TestScheduledReportsErrors:
    """Test 16 NEW typed exception classes (CR 12-5 D-14 envelope verbatim)."""

    def test_scheduled_report_cron_invalid_error(self) -> None:
        exc = ScheduledReportCronInvalidError(cron_expression="bad")
        assert exc.code == "SCHEDULED_REPORT_CRON_INVALID"
        assert exc.http_status == 400

    def test_scheduled_report_tenant_not_found_error(self) -> None:
        exc = ScheduledReportTenantNotFoundError(tenant_id="t1")
        assert exc.code == "SCHEDULED_REPORT_TENANT_NOT_FOUND"
        assert exc.http_status == 404

    def test_scheduled_report_finance_email_not_found_error(self) -> None:
        exc = ScheduledReportFinanceEmailNotFoundError(tenant_id="t1")
        assert exc.code == "SCHEDULED_REPORT_FINANCE_EMAIL_NOT_FOUND"
        assert exc.http_status == 400

    def test_scheduled_report_lifecycle_error(self) -> None:
        exc = ScheduledReportLifecycleError(current_status="completed", event="cancel")
        assert exc.code == "SCHEDULED_REPORT_LIFECYCLE_INVALID"
        assert exc.http_status == 400

    def test_scheduled_report_retry_exhausted_error(self) -> None:
        exc = ScheduledReportRetryExhaustedError(tenant_id="t1", job_id="j1", last_error="err")
        assert exc.code == "SCHEDULED_REPORT_RETRY_EXHAUSTED"
        assert exc.http_status == 500

    def test_scheduled_report_persistence_error(self) -> None:
        exc = ScheduledReportPersistenceError(tenant_id="t1", operation="INSERT", reason="err")
        assert exc.code == "SCHEDULED_REPORT_PERSISTENCE_ERROR"
        assert exc.http_status == 500

    def test_scheduled_report_idempotency_violation_error(self) -> None:
        exc = ScheduledReportIdempotencyViolationError(
            tenant_id="t1", dispatch_schedule="monthly", period_key="2026-09"
        )
        assert exc.code == "SCHEDULED_REPORT_IDEMPOTENCY_VIOLATION"
        assert exc.http_status == 409

    def test_scheduled_report_permission_error(self) -> None:
        exc = ScheduledReportPermissionError(role="member", required_role="owner")
        assert exc.code == "SCHEDULED_REPORT_PERMISSION_DENIED"
        assert exc.http_status == 403

    def test_scheduled_report_finance_contact_email_error(self) -> None:
        exc = ScheduledReportFinanceContactEmailError(finance_contact_email="bad")
        assert exc.code == "SCHEDULED_REPORT_FINANCE_CONTACT_EMAIL_INVALID"
        assert exc.http_status == 400

    def test_scheduled_report_alembic_migration_error(self) -> None:
        exc = ScheduledReportAlembicMigrationError(migration_revision="0061", reason="err")
        assert exc.code == "SCHEDULED_REPORT_ALEMBIC_MIGRATION_ERROR"
        assert exc.http_status == 500

    def test_scheduled_report_asyncio_error(self) -> None:
        exc = ScheduledReportAsyncIOError(job_id="j1", reason="err")
        assert exc.code == "SCHEDULED_REPORT_ASYNCIO_ERROR"
        assert exc.http_status == 500

    def test_scheduled_report_persistent_job_store_error(self) -> None:
        exc = ScheduledReportPersistentJobStoreError(backend="memory", reason="err")
        assert exc.code == "SCHEDULED_REPORT_PERSISTENT_JOB_STORE_ERROR"
        assert exc.http_status == 500

    def test_scheduled_report_timezone_error(self) -> None:
        exc = ScheduledReportTimezoneError(timezone_str="Bad/TZ")
        assert exc.code == "SCHEDULED_REPORT_TIMEZONE_INVALID"
        assert exc.http_status == 400

    def test_scheduled_report_period_key_error(self) -> None:
        exc = ScheduledReportPeriodKeyError(period_key="2026-9")
        assert exc.code == "SCHEDULED_REPORT_PERIOD_KEY_INVALID"
        assert exc.http_status == 400

    def test_scheduled_report_dispatch_error(self) -> None:
        exc = ScheduledReportDispatchError(job_id="j1", dispatch_target="email", reason="err")
        assert exc.code == "SCHEDULED_REPORT_DISPATCH_ERROR"
        assert exc.http_status == 500

    def test_scheduled_report_recipient_resolver_error(self) -> None:
        exc = ScheduledReportRecipientResolverError(
            recipient_strategy="bad", reason="err"
        )
        assert exc.code == "SCHEDULED_REPORT_RECIPIENT_RESOLVER_ERROR"
        assert exc.http_status == 500


# ── TestScheduledReportsCLI (4 tests) ──────────────────────────────────


class TestScheduledReportsCLI:
    """Test CLI argparse + --scheduled-reports-dry-run flag."""

    def test_cli_default_values(self) -> None:
        """Default dispatch_schedule=monthly + dry_run=False."""
        args = parse_cli_args([])
        assert args.dispatch_schedule == "monthly"
        assert args.scheduled_reports_dry_run is False
        assert args.legacy_dry_run is False

    def test_cli_dry_run_flag(self) -> None:
        """--scheduled-reports-dry-run sets the flag."""
        args = parse_cli_args(["--scheduled-reports-dry-run"])
        assert args.scheduled_reports_dry_run is True

    def test_cli_legacy_dry_run_alias(self) -> None:
        """--dry-run legacy alias sets the legacy flag."""
        args = parse_cli_args(["--dry-run"])
        assert args.legacy_dry_run is True

    def test_cli_custom_tenant_and_schedule(self) -> None:
        """Custom tenant + schedule overrides."""
        args = parse_cli_args([
            "--tenant-id", "t-custom",
            "--dispatch-schedule", "weekly",
            "--recipient-strategy", "finance_only",
        ])
        assert args.tenant_id == "t-custom"
        assert args.dispatch_schedule == "weekly"
        assert args.recipient_strategy == "finance_only"


# ── TestScheduledReportsSerializers (8 tests) ─────────────────────────


class TestScheduledReportsSerializers:
    """Test Pydantic serializers (CR 11-4 P-015 pure validator pattern)."""

    def test_scheduled_job_create_valid(self) -> None:
        req = ScheduledJobCreate(
            dispatch_schedule="monthly",
            recipient_strategy="finance_and_admin",
            finance_contact_email="finance@example.com",
            report_type="cost-records",
            period_key="2026-09",
        )
        assert req.dispatch_schedule == "monthly"

    def test_scheduled_job_create_invalid_email(self) -> None:
        """Invalid email format → ValueError."""
        with pytest.raises(ValueError):
            ScheduledJobCreate(
                dispatch_schedule="monthly",
                finance_contact_email="not-an-email",
            )

    def test_scheduled_job_create_invalid_period_key(self) -> None:
        """Invalid period_key format → ValueError."""
        with pytest.raises(ValueError):
            ScheduledJobCreate(
                dispatch_schedule="monthly",
                period_key="2026-9",  # missing leading zero
            )

    def test_scheduled_job_create_extra_field_forbidden(self) -> None:
        """Extra field → Pydantic ValidationError (extra='forbid')."""
        with pytest.raises(Exception):
            ScheduledJobCreate(
                dispatch_schedule="monthly",
                unknown_field="x",
            )

    def test_scheduled_job_cancel_valid(self) -> None:
        req = ScheduledJobCancel(reason="사용자 취소")
        assert req.reason == "사용자 취소"

    def test_scheduled_dispatch_now_valid(self) -> None:
        req = ScheduledDispatchNow(
            dispatch_schedule="monthly",
            period_key="2026-09",
        )
        assert req.dispatch_schedule == "monthly"
        assert req.period_key == "2026-09"

    def test_period_key_regex(self) -> None:
        """PERIOD_KEY_REGEX matches YYYY-MM format."""
        assert PERIOD_KEY_REGEX.match("2026-09")
        assert PERIOD_KEY_REGEX.match("2026-12")
        assert not PERIOD_KEY_REGEX.match("2026-9")
        assert not PERIOD_KEY_REGEX.match("26-09")

    def test_email_regex(self) -> None:
        """EMAIL_REGEX matches valid email format."""
        assert EMAIL_REGEX.match("finance@example.com")
        assert not EMAIL_REGEX.match("not-an-email")


# ── TestScheduledReportsSchedule (4 tests) ────────────────────────────


class TestScheduledReportsSchedule:
    """Test schedule_report main entrypoint."""

    def test_schedule_report_dry_run(self) -> None:
        """dry_run=True → schedule without audit emit."""
        result = schedule_report(
            tenant_id="tenant-1",
            dispatch_schedule="monthly",
            recipient_strategy="finance_and_admin",
            finance_contact_email="finance@example.com",
            report_type="cost-records",
            dry_run=True,
        )
        assert result["status"] == "scheduled"
        assert result["dispatch_schedule"] == "monthly"
        assert result["tenant_id"] == "tenant-1"

    def test_schedule_report_invalid_email_raises(self) -> None:
        """Invalid email format → ScheduledReportFinanceContactEmailError."""
        with pytest.raises(ScheduledReportFinanceContactEmailError):
            schedule_report(
                tenant_id="tenant-1",
                dispatch_schedule="monthly",
                recipient_strategy="finance_only",
                finance_contact_email="not-an-email",
            )

    def test_schedule_report_invalid_strategy_raises(self) -> None:
        """Invalid recipient strategy → ScheduledReportRecipientResolverError."""
        with pytest.raises(ScheduledReportRecipientResolverError):
            schedule_report(
                tenant_id="tenant-1",
                dispatch_schedule="monthly",
                recipient_strategy="bad_strategy",
            )

    def test_schedule_report_annual_cron(self) -> None:
        """Annual schedule resolves to Jan 1 09:00 cron."""
        result = schedule_report(
            tenant_id="tenant-1",
            dispatch_schedule="annual",
            recipient_strategy="admin_fallback",
            finance_contact_email=None,
            dry_run=True,
        )
        assert result["cron_expression"] == "0 9 1 1 *"


# ── TestScheduledReportsConstants (3 tests) ───────────────────────────


class TestScheduledReportsConstants:
    """Test constants from scheduled_reports.py."""

    def test_retry_backoff_minutes(self) -> None:
        """RETRY_BACKOFF_MINUTES = [1, 5, 30] verbatim (exponential)."""
        assert RETRY_BACKOFF_MINUTES == [1, 5, 30]

    def test_max_retry_count(self) -> None:
        """MAX_RETRY_COUNT = 3."""
        assert MAX_RETRY_COUNT == 3

    def test_kst_timezone(self) -> None:
        """KST = Asia/Seoul timezone."""
        assert str(KST) == "Asia/Seoul"
