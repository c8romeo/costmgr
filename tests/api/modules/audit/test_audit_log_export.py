"""tests.api.modules.audit.test_audit_log_export — CSV export wire tests.

Epic 17 (cj-style 82번째 epic 연속 정직 회복 wire) — T7 (AC #5.1~#5.8).

Verifies:
  - AuditLogExportError envelope shape (CR 12-5 D-14 verbatim)
  - AuditLogExportForbiddenError (403)
  - AuditLogExportTooLargeError (413)
  - MAX_EXPORT_ROWS = 100_000
"""
from __future__ import annotations

from apps.api.modules.audit.audit_log_export import (
    MAX_EXPORT_ROWS,
    AuditLogExportError,
    AuditLogExportForbiddenError,
    AuditLogExportTooLargeError,
)


class TestMaxExportRowsConstant:
    def test_max_export_rows_is_100k(self) -> None:
        assert MAX_EXPORT_ROWS == 100_000


class TestExportBaseError:
    def test_envelope_shape(self) -> None:
        exc = AuditLogExportError(
            code="AUDIT_LOG_EXPORT_GENERIC_KO",
            message_ko="export 실패",
            details={"reason": "test"},
        )
        assert exc.code == "AUDIT_LOG_EXPORT_GENERIC_KO"
        assert exc.message_ko == "export 실패"
        assert exc.details == {"reason": "test"}

    def test_details_default_empty_dict(self) -> None:
        exc = AuditLogExportError(
            code="X",
            message_ko="y",
        )
        assert exc.details == {}


class TestExportForbiddenError:
    def test_403_envelope(self) -> None:
        exc = AuditLogExportForbiddenError(role="member")
        assert exc.code == "AUDIT_LOG_EXPORT_FORBIDDEN_KO"
        assert exc.details == {"role": "member"}
        assert "권한" in exc.message_ko


class TestExportTooLargeError:
    def test_413_envelope(self) -> None:
        exc = AuditLogExportTooLargeError(
            row_count=150_000, max_rows=100_000
        )
        assert exc.code == "AUDIT_LOG_EXPORT_TOO_LARGE_KO"
        assert exc.details == {"row_count": 150_000, "max_rows": 100_000}
        assert "100,000" in exc.message_ko
