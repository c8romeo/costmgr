"""apps.api.modules.m5_reports.exceptions — Story 9.4 typed exceptions.

Story 9.4 (Epic 9 4번째 진입점) — 4 NEW typed exceptions + Korean SSOT
envelope messages for Report #21 (Cost Object Breakdown):

  - Report21PeriodNotCommittedError        (422 REPORT21_PERIOD_NOT_COMMITTED)
  - Report21NoBreakdownError               (422 REPORT21_NO_COST_OBJECT_BREAKDOWN)
  - Report21BreakdownNotFoundError         (404 REPORT21_BREAKDOWN_NOT_FOUND)
  - Report21PdfGenerationError             (500 REPORT_PDF_GENERATION_ERROR)
                                              (CR 12-5 D-14 typed envelope main.py REUSE 0 NEW)

Pure re-export from kernel + service-layer extensions (AD-15 §4 envelope).
"""
from __future__ import annotations

# Pure kernel exceptions re-export (9-1 + 9-2 + 9-3 surface 유지)
from packages.cost_engine.abc_engine import (
    AbcValidationNotFoundError,
    ActivityValidationError,
    AllocationBalanceError,
    CcrComputeError,
    CostPoolValidationError,
    DriverValidationError,
    EmptyDepartmentsError,
    Report21InconsistentStateError,
    TooManyDepartmentsError,
)

# ── Story 9.4 typed exceptions (CR 12-5 D-14 envelope main.py handler 등록) ──


class Report21PeriodNotCommittedError(Exception):
    """PRD §9 + §7.3 — Report #21 (period 미커밋) HTTP 422 envelope.

    Period가 아직 commit되지 않은 시점 — V7 verdict + breakdown 부재 시
    `Report21Service.build_report21` 가 envelope RAISE.

    `period_key` identifies which period failed (machine code),
    `reason` is the human-readable Korean reason.
    """

    def __init__(
        self,
        message: str,
        *,
        period_key: str,
        reason: str,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.period_key = period_key
        self.reason = reason


class Report21NoBreakdownError(Exception):
    """PRD §9 + §V7 — Report #21 (breakdown 부재) HTTP 422 envelope.

    Cost Object Breakdown rows 부재 시 raise. service-layer pre-validation
    guard (CR 12-5 L3 3-layer defense).

    `period_key` identifies which period failed (machine code),
    `reason` is the human-readable Korean reason.
    """

    def __init__(
        self,
        message: str,
        *,
        period_key: str,
        reason: str,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.period_key = period_key
        self.reason = reason


class Report21BreakdownNotFoundError(Exception):
    """PRD §9 + §F9.3 — Report #21 (breakdown not found) HTTP 404 envelope.

    Commit 안된 period + 기존 breakdown 부재 시 service-layer RAISE
    (compute_and_persist 11-step pipeline 미실행 OR JSONB subdoc 부재).

    `period_key` identifies which period failed (machine code),
    `reason` is the human-readable Korean reason.
    """

    def __init__(
        self,
        message: str,
        *,
        period_key: str,
        reason: str,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.period_key = period_key
        self.reason = reason


class Report21PdfGenerationError(Exception):
    """PRD §9 #21 + §V8 — Report #21 PDF generation HTTP 500 envelope.

    PDF byte composition 실패 시 service-layer RAISE. CR 12-5 D-14
    typed envelope main.py REUSE 0 NEW handlers.

    `reason` is the human-readable Korean reason.
    """

    def __init__(
        self,
        message: str,
        *,
        reason: str,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.reason = reason


# ── Korean SSOT envelope messages (CR 12-5 D-14) ─────────────────


REPORT21_PERIOD_NOT_COMMITTED_KO: str = (
    "리포트 #21 생성 전 회계기간이 커밋되지 않았습니다"
)
REPORT21_NO_COST_OBJECT_BREAKDOWN_KO: str = (
    "리포트 #21: 원가대상별 배부 데이터가 없습니다"
)
REPORT21_BREAKDOWN_NOT_FOUND_KO: str = (
    "리포트 #21: 원가대상별 원가 집계표를 찾을 수 없습니다"
)
REPORT_PDF_GENERATION_ERROR_KO: str = (
    "리포트 PDF 생성 실패 — 서버 관리자에게 문의하세요"
)


__all__ = [
    # Re-exports from kernel (9-1 + 9-2 + 9-3 + 9-4 surfaces)
    "CostPoolValidationError",
    "ActivityValidationError",
    "DriverValidationError",
    "AbcValidationNotFoundError",
    "CcrComputeError",
    "AllocationBalanceError",
    "EmptyDepartmentsError",
    "TooManyDepartmentsError",
    "Report21InconsistentStateError",
    # 9-4 service-layer typed exceptions (CR 12-5 D-14 envelope main.py handler)
    "Report21PeriodNotCommittedError",
    "Report21NoBreakdownError",
    "Report21BreakdownNotFoundError",
    "Report21PdfGenerationError",
    # Korean messages (CR 12-5 D-14)
    "REPORT21_PERIOD_NOT_COMMITTED_KO",
    "REPORT21_NO_COST_OBJECT_BREAKDOWN_KO",
    "REPORT21_BREAKDOWN_NOT_FOUND_KO",
    "REPORT_PDF_GENERATION_ERROR_KO",
]
