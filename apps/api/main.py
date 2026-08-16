"""
apps/api/main.py — FastAPI entry (Story 0.1 stub + Story 0.2 attach).

Only a single /health route in this story. Domain endpoints are added in Epic 4+.

AD-1, AD-11 compliance:
  - This module imports only stdlib + FastAPI/uvicorn
  - It does NOT import packages.cost_engine.core directly
  - It MAY import packages.cost_engine.ports (via apps.api.core.ports_bridge — added in later stories)
"""

import uuid as _uuid_mod

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from apps.api.core.cache_invalidation_publisher import (
    CacheInvalidationChannelInvalidError,
)
from apps.api.core.capability import (
    ForbiddenRoleError,
    IndustryCapabilityError,
)
from apps.api.core.pipa_gate import (
    PipaConsentMissingError,
    PipaReviewRequiredError,
)
from apps.api.core.security import AuthError
from apps.api.modules.m0_onboarding import router as m0_onboarding_router
from apps.api.modules.m1_baseline import router as m1_baseline_router
from apps.api.modules.m2_input import router as m2_input_router
from apps.api.modules.m2_input.services.monthly_input_service import (
    MonthlyInputCompanyBurdenRateError,
    MonthlyInputFteReadOnlyError,
    MonthlyInputInvalidLaborShapeError,
    MonthlyInputInventoryProjectionError,
    MonthlyInputPayrollSettingsInvalidError,
    MonthlyInputPayTypeMismatchError,
    MonthlyInputWarningsReadOnlyError,
)
from apps.api.modules.m3_calculate import router as m3_calculate_router
from apps.api.modules.m3_calculate.services import (
    BaselineNotReadyError,
    CalcServiceError,
    FiscalPeriodSnapshotDivergedError,
    MonthlyInputBlockedError,
)
from apps.api.modules.m4_inventory import router as m4_inventory_router
from apps.api.modules.m4_inventory.services.closing_guard_service import (
    ClosingGuardAuditEmitError,
    ClosingGuardInvalidPeriodKeyError,
    ClosingGuardNegativeInventoryError,
    ClosingGuardProductionConsumptionError,
    ClosingGuardServiceOnlyTenantError,
)
from apps.api.modules.m4_inventory.services.closing_pdf_export_service import (
    ClosingPdfExportAuditEmitError,
    ClosingPdfExportInvalidIndustryError,
    ClosingPdfExportSizeExceededError,
)
from apps.api.modules.m4_inventory.services.ledger_service import (
    AppendOnlyLedgerViolationError,
    InventoryLedgerInvalidEventTypeError,
    InventoryLedgerPeriodKeyFormatError,
    InventoryLedgerReversalNotYetWiredError,
)
from apps.api.modules.m4_inventory.services.opening_carry_service import (
    MonthlyInputCarryChainLimitError,
    MonthlyInputCarryPrevPeriodNotFoundError,
    MonthlyInputOpeningLockViolationError,
    MonthlyInputOpeningManualEditError,
)
from apps.api.modules.m7_simulation import router as m7_simulation_router
from apps.api.modules.m7_simulation.exceptions import (
    CVP_BASELINE_NOT_FOUND_KO,
    CVP_INVALID_DELTA_KO,
    INVALID_PROJECTION_MONTH_KO,
    PROJECTION_BASELINE_NOT_FOUND_KO,
    PROJECTION_INPUTS_INVALID_KO,
    CVPBaselineNotFoundError,
    CVPInvalidDeltaError,
    InvalidProjectionMonthError,
    ProjectionBaselineNotFoundError,
    ProjectionInputsInvalidError,
)
from apps.api.modules.m8_budget import (
    router as m8_budget_router,
)
from apps.api.modules.m8_budget import (
    variance_router as m8_budget_variance_router,
)
from apps.api.modules.m8_budget.exceptions import (
    BUDGET_INVALID_VARIANCE_PERIOD_KO,
    BUDGET_INVALID_VIRTUAL_KEY_KO,
    BUDGET_SCENARIO_LIMIT_EXCEEDED_KO,
    BUDGET_SCENARIO_NOT_FOUND_KO,
    BUDGET_VARIANCE_NOT_FOUND_KO,
    BudgetScenarioNotFoundError,
    BudgetVarianceNotFoundError,
    InvalidVariancePeriodError,
    InvalidVirtualBudgetPeriodKeyError,
    ScenarioLimitExceededError,
)
from apps.api.modules.m9_abc import router as m9_abc_router
from apps.api.modules.m10_ai import router as m10_ai_router
from apps.api.modules.m10_ai.handlers import _pipa_error_response
from apps.api.modules.m11_close import router as m11_close_router
from apps.api.modules.m11_close.exceptions import (
    ReopenAuditEmitFailedError,
    ReopenOperatorActionInvalidError,
    ReversalSnapshotMismatchError,
    SnapshotAlreadyCommittedError,
    SnapshotNotFoundError,
)
from apps.api.modules.m11_close.services.close_sequence_service import (
    CloseSequenceAlreadyInitiatedError,
    CloseSequenceCapabilityDeniedError,
    CloseSequenceNotInitiatedError,
    CloseSequenceStepMismatchError,
    ClosingSequenceAlreadyConfirmedError,
    ClosingSequenceAuditEmitError,
    PartialCloseBlockedError,
)
from apps.api.modules.m11_close.services.reversal_service import (
    LockedPeriodReversalRejectedError,
    ReversalDuplicateError,
    ReversalRejectedError,
    ReversalTargetNotFoundError,
    ReversalUnauthorizedError,
)
from apps.api.modules.m12_account import router as m12_account_router
from apps.api.modules.m12_account.exceptions import (
    BackupExportServiceError,
    BackupNotFoundError,
    BackupPayloadTooLargeError,
    BackupRetentionCutoffInvalidError,
    BackupServiceAuditEmitError,
    TwoFactorAlreadyEnabledError,
    TwoFactorAuditEmitError,
    TwoFactorCryptoKeyMissingError,
    TwoFactorDisableUnauthorizedError,
    TwoFactorEncryptionError,
    TwoFactorNotEnabledError,
    TwoFactorRecoveryExhaustedError,
    TwoFactorUserNotFoundError,
)
from apps.api.modules.m12_account.services.account_deletion_service import (
    ACCOUNT_DELETION_AUDIT_EMIT_FAILED_KO,
    ACCOUNT_DELETION_HARD_DELETE_FAILED_KO,
    DELETION_CHALLENGE_TOKEN_EXPIRED_KO,
    DELETION_CHALLENGE_TOKEN_INVALID_KO,
    DELETION_CONSENT_DECRYPTION_FAILED_KO,
    DELETION_CONSENT_ENCRYPTION_FAILED_KO,
    AccountDeletionAuditEmitError,
    AccountDeletionHardDeleteError,
    DeletionChallengeTokenExpiredError,
    DeletionChallengeTokenInvalidError,
    DeletionConsentDecryptionError,
    DeletionConsentEncryptionError,
)
from apps.api.modules.m12_account.services.audit_extension import (
    AUDIT_EMIT_FAILED_KO,
    BACKUP_AUDIT_EMIT_FAILED_KO,
    BACKUP_NOT_FOUND_KO,
    BACKUP_PAYLOAD_TOO_LARGE_KO,
    BACKUP_RETENTION_CUTOFF_INVALID_KO,
    BACKUP_SERVICE_ERROR_KO,
    CHALLENGE_LOCKED_OUT_KO,
    CHALLENGE_TOKEN_ALREADY_CONSUMED_KO,
    CHALLENGE_TOKEN_EXPIRED_KO,
    CHALLENGE_TOKEN_INVALID_KO,
    CHALLENGE_TOKEN_PURPOSE_MISMATCH_KO,
    DISABLE_UNAUTHORIZED_KO,
    ENCRYPTION_FAILED_KO,
    KEY_MISSING_KO,
    RECOVERY_EXHAUSTED_KO,
    SETUP_ALREADY_ENABLED_KO,
    SETUP_NOT_ENABLED_KO,
    TWO_FACTOR_CHALLENGE_FAILED_KO,
    USER_NOT_FOUND_KO,
)
from apps.api.modules.m12_account.services.two_factor_challenge_service import (
    ChallengeTokenAlreadyConsumedError,
    ChallengeTokenExpiredError,
    ChallengeTokenInvalidError,
    ChallengeTokenPurposeMismatchError,
    TwoFactorChallengeFailedError,
)
from packages.services.m12_account.totp import (
    TotpInvalidCodeError,
    TotpLockoutError,
    TotpRecoveryInvalidError,
)
from packages.services.m12_account.two_factor_gate import (
    ForbiddenRoleError as M12ForbiddenRoleError,
)
from packages.services.m12_account.two_factor_gate import (
    TwoFactorRequiredError,
)

app = FastAPI(
    title="bizup/costmgr API",
    version="0.1.0",
    description="원가 관리 SaaS — FastAPI modular monolith (AD-1)",
)

# Story 1.1 — M0 onboarding (industry selector + menu auto-toggle)
app.include_router(m0_onboarding_router)

# Story 1.2 — Settings wizard scaffolds (M1 baseline + M9 ABC read endpoints)
app.include_router(m1_baseline_router)
app.include_router(m9_abc_router)

# Story 1.3 — M10 AI document extraction (upload / list / reprocess + drafts CRUD / promote)
app.include_router(m10_ai_router)

# Story 3.1 — M2 monthly input capture (6-stream tabs + 일자별 toggle + completion gate)
# Story 3.2 — M2 labor precision (pay_type 분기 + 5 breakdown fields + tenant payroll override)
app.include_router(m2_input_router)

# Story 4.2 — M3 single calculation endpoint (POST /api/v1/calc).
# AD-19 single entry point. AD-4 REPEATABLE READ handled inside the handler.
# AD-1 binding: handler → service (calc_orchestrator) → engine (period_cost).
app.include_router(m3_calculate_router)

# Story 5.1 — M4 inventory opening carry manual trigger.
# Auto-carry chain hooks into m2_input_service (get_state + save_row);
# this router only exposes the explicit manual trigger.
app.include_router(m4_inventory_router)

# Story 8.1 — M8 budget vs actual scenario CRUD (PRD §F8.1).
# AD-24 period key typed pattern + 1차 시나리오 1개 잠금.
# 3 NEW routes (Story 8.1):
# - POST /api/v1/budget/scenarios             (201 owner+member create)
# - GET  /api/v1/budget/scenarios             (200 4-role list)
# - GET  /api/v1/budget/scenarios/{period_key} (200 4-role get-by-key)
# 2 NEW routes (Story 8.2):
# - GET  /api/v1/budget/variance/{period_key} (200 4-role variance table)
# - GET  /api/v1/budget/variance/{period_key}/pdf (200 envelope, 8-3 DEFER PDF)
app.include_router(m8_budget_router)
app.include_router(m8_budget_variance_router)

# Story 7.1 — M7 CVP/BEP slider simulation (PRD §F7.1).
# 2 NEW routes:
# - POST /api/v1/simulation/cvp/compute    (200 — baseline + simulated BEP)
# - GET  /api/v1/simulation/cvp/baseline   (200/404 — committed snapshot baseline)
# Capability: CVP_SIMULATION (industry-agnostic per CR 12-1 L4).
app.include_router(m7_simulation_router)

# Story 11.1 — M11 reversal sequence (AD-22 sign-negating + corrected row +
# AD-25 cache invalidation publisher). 3 NEW routes:
# - POST /api/v1/close/reversal-requests (201 REVERSAL_COMPLETED)
# - GET /api/v1/close/reversal-requests/<correction_group_id> (200)  # noqa: ERA001 — FastAPI path template syntax
# - POST /api/v1/close/cache-invalidation (200 AD-25 publish receipt)
app.include_router(m11_close_router)

# Story 12.4 (Epic 12 carry-over sprint) — M12 2FA mandatory gate (PRD §F12.1 + §M12-a).
# 9 NEW routes:
# - POST /api/v1/account/2fa/setup                  (201 setup initiated)
# - POST /api/v1/account/2fa/verify                 (200 setup completed)
# - POST /api/v1/account/2fa/challenge              (200 challenge outcome + token)
# - POST /api/v1/account/2fa/recovery               (200 recovery consumed + token)
# - POST /api/v1/account/2fa/disable                (200 2FA disabled)
# - GET  /api/v1/account/2fa/status                 (200 enrollment state read)
# - POST /api/v1/account/2fa/challenge-tokens       (201 HS256 token issued)
# - POST /api/v1/account/2fa/challenge-tokens/consume (200 token consumed)
# - GET  /api/v1/m2-entry-gate                      (200 M2 entry gate state)
app.include_router(m12_account_router)


@app.exception_handler(AuthError)
async def _auth_error_handler(request: Request, exc: AuthError) -> JSONResponse:
    """Map `AuthError` (AD-15) to HTTP 401 with the typed error contract.

    Without this handler, FastAPI returns HTTP 500 for any `AuthError`
    raised in a dependency (AD-15 contract violation).
    """
    return JSONResponse(
        status_code=401,
        content={
            "code": exc.code,
            "message_ko": exc.message_ko,
            "details": exc.details,
            "trace_id": exc.trace_id,
        },
    )


# H5 / AD-15 §4 + AC #6: typed envelope for IndustryCapabilityError.
# Without this, FastAPI returns HTTP 500 for capability mismatches —
# violating the `{code, message_ko, details, trace_id}` contract.
@app.exception_handler(IndustryCapabilityError)
async def _industry_capability_handler(
    request: Request, exc: IndustryCapabilityError
) -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content={
            "code": "INDUSTRY_NOT_SUPPORTED",
            "message_ko": "현재 업종에서 지원하지 않는 기능입니다",
            "details": {
                "current_industry": (exc.current_industry.value if exc.current_industry else None),
                "requested_capability": exc.capability.value,
            },
            "trace_id": exc.trace_id,
        },
    )


# H3 / AD-10 / T4.2: typed envelope for ForbiddenRoleError.
# Without this, FastAPI returns HTTP 500 for role gate failures.
@app.exception_handler(ForbiddenRoleError)
async def _forbidden_role_handler(request: Request, exc: ForbiddenRoleError) -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content={
            "code": "FORBIDDEN_ROLE",
            "message_ko": "소유자(Owner) 권한이 필요합니다",
            "details": {
                "role": exc.role,
                "required_role": exc.required_role,
            },
            "trace_id": exc.trace_id,
        },
    )


# Story 1.3 — PIPA gate dependency-raised exception → 451 typed envelope.
# Without this handler, FastAPI returns HTTP 500 for PIPA gate failures.
@app.exception_handler(PipaConsentMissingError)
async def _pipa_consent_handler(request: Request, exc: PipaConsentMissingError) -> JSONResponse:
    return _pipa_error_response(exc)


# Epic 1 회고 A3 + Epic 3 회고 A1 — operations kill-switch envelope.
# When `PIPA_REVIEW_COMPLETED=false` is set fleet-wide, the gate raises
# `PipaReviewRequiredError` BEFORE the per-tenant check. This handler maps
# it to 503 PIPA_REVIEW_REQUIRED so operators can pause cross-border AI
# processing without redeploying per-tenant consent.
@app.exception_handler(PipaReviewRequiredError)
async def _pipa_review_required_handler(
    request: Request, exc: PipaReviewRequiredError
) -> JSONResponse:
    return JSONResponse(
        status_code=503,  # Service Unavailable
        content={
            "code": "PIPA_REVIEW_REQUIRED",
            "message_ko": (
                "개인정보 보호법 검토가 완료되지 않아 AI 처리를 일시 중단했습니다. "
                "관리자에게 문의해 주세요."
            ),
            "details": {"reason": "operations_kill_switch"},
            "trace_id": exc.trace_id,
        },
    )


# Story 3.2 — labor precision error envelopes (AD-15 §4).
# Without these, FastAPI returns HTTP 500 for the new `_validate_labor_shape`
# + `_load_payroll_settings` failure paths. Mapped to typed codes so the
# frontend can show specific Korean hints ("daily mode doesn't use
# monthly_salary_basis_krw", etc).
@app.exception_handler(MonthlyInputInvalidLaborShapeError)
async def _m2_invalid_labor_shape_handler(
    request: Request, exc: MonthlyInputInvalidLaborShapeError
) -> JSONResponse:
    """400 MONTHLY_INPUT_INVALID_LABOR_SHAPE — labor stream missing required
    pay_type-specific fields (Task 3.1 `_validate_labor_shape` AC #4)."""
    return JSONResponse(
        status_code=400,
        content={
            "code": "MONTHLY_INPUT_INVALID_LABOR_SHAPE",
            "message_ko": "인건비 입력 항목이 부족합니다",
            "details": exc.details,
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(MonthlyInputFteReadOnlyError)
async def _m2_fte_read_only_handler(
    request: Request, exc: MonthlyInputFteReadOnlyError
) -> JSONResponse:
    """400 MONTHLY_INPUT_FTE_READ_ONLY — AC #5 direct write attempt on
    `fte_headcount` / `fte_wage_krw` (derived fields)."""
    return JSONResponse(
        status_code=400,
        content={
            "code": "MONTHLY_INPUT_FTE_READ_ONLY",
            "message_ko": "FTE 인원·인건비는 자동 계산 항목입니다 (직접 수정 불가)",
            "details": {"field": exc.field},
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(MonthlyInputPayrollSettingsInvalidError)
async def _m2_payroll_settings_invalid_handler(
    request: Request, exc: MonthlyInputPayrollSettingsInvalidError
) -> JSONResponse:
    """400 MONTHLY_INPUT_PAYROLL_SETTINGS_INVALID — out-of-range value in
    `tenant_settings.payroll.*` (Task 3.1 `_load_payroll_settings`)."""
    return JSONResponse(
        status_code=400,
        content={
            "code": "MONTHLY_INPUT_PAYROLL_SETTINGS_INVALID",
            "message_ko": "인건비 정책 값이 올바르지 않습니다",
            "details": exc.details,
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(MonthlyInputCompanyBurdenRateError)
async def _m2_company_burden_rate_handler(
    request: Request, exc: MonthlyInputCompanyBurdenRateError
) -> JSONResponse:
    """422 MONTHLY_INPUT_COMPANY_BURDEN_RATE — service-side re-check
    catches bypasses (Task 3.1)."""
    return JSONResponse(
        status_code=422,
        content={
            "code": "MONTHLY_INPUT_COMPANY_BURDEN_RATE",
            "message_ko": "회사부담임률은 0과 1 사이여야 합니다",
            "details": {"value": exc.value},
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(MonthlyInputPayTypeMismatchError)
async def _m2_pay_type_mismatch_handler(
    request: Request, exc: MonthlyInputPayTypeMismatchError
) -> JSONResponse:
    """400 MONTHLY_INPUT_PAY_TYPE_MISMATCH — pay_type별 forbidden 필드
    사용 시 (예: daily + monthly_salary_basis_krw)."""
    return JSONResponse(
        status_code=400,
        content={
            "code": "MONTHLY_INPUT_PAY_TYPE_MISMATCH",
            "message_ko": "급여유형과 입력 항목이 맞지 않습니다",
            "details": exc.details,
            "trace_id": exc.trace_id,
        },
    )


# Story 3.3 — warning / projection error envelopes (AD-15 §4).
# Maps the 2 new typed exceptions (Task 3.2) so the frontend can
# distinguish advisory warnings from server-side errors.
@app.exception_handler(MonthlyInputWarningsReadOnlyError)
async def _m2_warnings_read_only_handler(
    request: Request, exc: MonthlyInputWarningsReadOnlyError
) -> JSONResponse:
    """400 MONTHLY_INPUT_WARNINGS_READ_ONLY — AC #7 server-side defense.

    `warnings` / `is_blocked` / `warnings_count` / `top_n_severity`
    are DERIVED fields (PRD §A11); PATCH attempts on them surface as
    `extra_fields_not_allowed` via Pydantic v2's `extra="forbid"`
    first. This handler covers the defense-in-depth path that
    bypasses Pydantic (raw DB writes, internal scripts).
    """
    return JSONResponse(
        status_code=400,
        content={
            "code": "MONTHLY_INPUT_WARNINGS_READ_ONLY",
            "message_ko": "경고 항목은 자동 계산 항목입니다 (직접 수정 불가)",
            "details": {"field": exc.field},
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(MonthlyInputInventoryProjectionError)
async def _m2_inventory_projection_handler(
    request: Request, exc: MonthlyInputInventoryProjectionError
) -> JSONResponse:
    """422 MONTHLY_INPUT_INVENTORY_PROJECTION — projection kernel failure.

    Fires when the inventory projection kernel (PRD §6.2) cannot
    reach a deterministic state. Mapped to 422 (PRD §V6 ENVELOPE
    for "data not processable") — operator-facing message hints at
    "raw balance out of range" / "missing product metadata" so the
    user can self-correct without needing to read a trace_id.
    """
    return JSONResponse(
        status_code=422,
        content={
            "code": "MONTHLY_INPUT_INVENTORY_PROJECTION",
            "message_ko": "재고 계산에 실패했습니다 (기초재고 또는 제품정보 확인)",
            "details": exc.details,
            "trace_id": exc.trace_id,
        },
    )


# H3 (Review) / AD-15 §4: detect BOM ratio decimal-places violations and
# convert them to a typed 422 BOM_INVALID_RATIO envelope. Without this,
# Pydantic's `max_digits=7, decimal_places=4` violation on BOMRowInput.ratio
# returns a generic FastAPI 422 — violating the typed error contract.
#
# All other RequestValidationError paths fall back to FastAPI's default
# `{"detail": [...]}` shape to preserve client compatibility.
@app.exception_handler(RequestValidationError)
async def _bom_validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Map BOMRowInput.ratio decimal-places violations to typed envelope.

    Match shape: loc == ("body", "lines", <index>, "ratio") and
    type in {decimal_max_places, decimal_max_digits, greater_than,
    less_than_equal}. Other validation errors are passed through with
    the default `detail` shape.
    """
    errors = exc.errors()
    trace_id = str(_uuid_mod.uuid4())
    for err in errors:
        loc = err.get("loc", ())
        if (
            len(loc) == 4
            and loc[0] == "body"
            and loc[1] == "lines"
            and loc[2].__class__.__name__ == "int"
            and loc[3] == "ratio"
            and err.get("type")
            in {
                "decimal_max_places",
                "decimal_max_digits",
                "greater_than",
                "less_than_equal",
                "decimal_whole_digits",
            }
        ):
            child_idx: int = loc[2]
            return JSONResponse(
                status_code=422,
                content={
                    "code": "BOM_INVALID_RATIO",
                    "message_ko": (
                        f"비중은 0보다 크고 100 이하이며 소수점 4자리까지 "
                        f"입력 가능합니다 (행 {child_idx})."
                    ),
                    "details": {
                        "field": "ratio",
                        "index": child_idx,
                        "violation": err.get("type"),
                        "input": err.get("input"),
                    },
                    "trace_id": trace_id,
                },
            )
    # Non-BOM validation errors — fall through to FastAPI default shape.
    return JSONResponse(
        status_code=422,
        content={"detail": errors},
    )


# Story 4.2 — M3 calculation error envelopes (AD-15 §4).
# Maps the 4 typed exceptions from `m3_calculate.services`:
#
# - 409 MONTHLY_INPUT_BLOCKED — Epic 3 A4 close-time hook.
#   Fired by orchestrator when `monthly_input_periods.is_blocked=true`.
#   The user must clear the warnings + re-toggle the [마감] button.
#
# - 409 FISCAL_PERIOD_SNAPSHOT_DIVERGED — same (tenant, period, baseline,
#   engine) row exists with DIFFERENT result_hash. Operator must
#   investigate (PRD §V6 — divergent state requires manual action,
#   not silent overwrite).
#
# - 422 BASELINE_NOT_READY — BOM 100% not validated OR allocation basis
#   3종 missing (PRD §F0.2 + §F1.1). Engine rejects too (defense in
#   depth); service layer is the canonical validator.
#
# - 500 INTERNAL_ERROR — generic orchestrator failure (DB connection,
#   engine ValueError not mapped to typed errors, etc.).
@app.exception_handler(MonthlyInputBlockedError)
async def _m3_monthly_input_blocked_handler(
    request: Request, exc: MonthlyInputBlockedError
) -> JSONResponse:
    """409 MONTHLY_INPUT_BLOCKED — Epic 3 A4 close-time hook.

    Story 3.3 set `is_blocked=true` after user clicks [마감] when
    `len(warnings) > 0`. Story 4.2 calc refuses to compute on a
    blocked period (PRD §A11 close-time rule).
    """
    return JSONResponse(
        status_code=409,
        content={
            "code": "MONTHLY_INPUT_BLOCKED",
            "message_ko": (
                f"입력 마감된 기간입니다 (경고 {exc.warnings_count}건). "
                "경고를 해결한 뒤 다시 마감해 주세요."
            ),
            "details": {
                "warnings_count": exc.warnings_count,
                "top_n_severity": exc.top_n_severity,
                "period_key": exc.period_key,
            },
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(FiscalPeriodSnapshotDivergedError)
async def _m3_snapshot_diverged_handler(
    request: Request, exc: FiscalPeriodSnapshotDivergedError
) -> JSONResponse:
    """409 FISCAL_PERIOD_SNAPSHOT_DIVERGED — AC #4 divergent state.

    Idempotency: same result_hash → no-op, return existing.
    Divergence: different result_hash → 409 because baseline mutated
    underneath without bumping baseline_revision.
    """
    return JSONResponse(
        status_code=409,
        content={
            "code": "FISCAL_PERIOD_SNAPSHOT_DIVERGED",
            "message_ko": (
                "동일 기간에 다른 계산 결과가 있습니다. "
                "baseline이 변경되었을 수 있으니 관리자에게 문의해 주세요."
            ),
            "details": {
                "baseline_revision": exc.baseline_revision,
                "engine_type": exc.engine_type,
                "existing_hash": exc.existing_hash,
                "new_hash": exc.new_hash,
            },
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(BaselineNotReadyError)
async def _m3_baseline_not_ready_handler(
    request: Request, exc: BaselineNotReadyError
) -> JSONResponse:
    """422 BASELINE_NOT_READY — PRD §F0.2 (allocation basis 3종) or
    §F1.1 (BOM 100%) gate failure."""
    return JSONResponse(
        status_code=422,
        content={
            "code": "BASELINE_NOT_READY",
            "message_ko": (
                "계산 사전조건이 충족되지 않았습니다. "
                "BOM 100% 검증과 배부기준 3종을 먼저 완료해 주세요."
            ),
            "details": exc.details,
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(CalcServiceError)
async def _m3_calc_service_error_handler(request: Request, exc: CalcServiceError) -> JSONResponse:
    """500 INTERNAL_ERROR — orchestrator wrapped an unexpected error."""
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_ERROR",
            "message_ko": "계산 처리 중 오류가 발생했습니다.",
            "details": exc.details,
            "trace_id": exc.trace_id,
        },
    )


# ─────────────────────────────────────────────────────────────
# Story 5.1 — M4 inventory opening carry chain exception handlers
# (AD-15 §4 envelope mapping)
# ─────────────────────────────────────────────────────────────


@app.exception_handler(MonthlyInputOpeningManualEditError)
async def _m4_opening_manual_edit_handler(
    request: Request, exc: MonthlyInputOpeningManualEditError
) -> JSONResponse:
    """400 MONTHLY_INPUT_OPENING_MANUAL_EDIT — user attempted to
    write `stream='opening_inventory'` row (PRD §F4.1).
    """
    return JSONResponse(
        status_code=400,
        content={
            "code": "MONTHLY_INPUT_OPENING_MANUAL_EDIT",
            "message_ko": ("기초재고는 자동 이월되며 수동 입력이 차단됩니다."),
            "details": {
                "period_key": exc.period_key,
                "tenant_id": str(exc.tenant_id),
                # H4: spec literal — auto_carried_value (carry chain 현재 값)
                # Story 5.2 spec 진입 시 opening_inventory JSONB lookup 결과 wire
                "auto_carried_value": None,
            },
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(MonthlyInputOpeningLockViolationError)
async def _m4_opening_lock_violation_handler(
    request: Request, exc: MonthlyInputOpeningLockViolationError
) -> JSONResponse:
    """500 MONTHLY_INPUT_OPENING_LOCK_VIOLATION — JSONB shape
    inconsistent (defense-in-depth guard).
    """
    return JSONResponse(
        status_code=500,
        content={
            "code": "MONTHLY_INPUT_OPENING_LOCK_VIOLATION",
            "message_ko": ("기초재고 잠금 상태가 손상되었습니다. 관리자에게 문의하세요."),
            "details": {
                "period_key": exc.period_key,
                "tenant_id": str(exc.tenant_id),
                **exc.details,
            },
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(MonthlyInputCarryChainLimitError)
async def _m4_carry_chain_limit_handler(
    request: Request, exc: MonthlyInputCarryChainLimitError
) -> JSONResponse:
    """422 MONTHLY_INPUT_CARRY_CHAIN_LIMIT — chain depth > limit.
    Manual trigger required for deeper chains.
    """
    # L6: use INVENTORY_PERIOD_CHAIN_LIMIT constant from opening_carry_service
    # instead of hardcoded "12"
    from apps.api.modules.m4_inventory.services.opening_carry_service import (
        INVENTORY_PERIOD_CHAIN_LIMIT,
    )

    return JSONResponse(
        status_code=422,
        content={
            "code": "MONTHLY_INPUT_CARRY_CHAIN_LIMIT",
            "message_ko": (
                f"이월 체인 깊이({exc.depth})가 한도({INVENTORY_PERIOD_CHAIN_LIMIT})를 "
                f"초과했습니다. 수동 트리거가 필요합니다."
            ),
            "details": {
                "depth": exc.depth,
                "limit": INVENTORY_PERIOD_CHAIN_LIMIT,
                "period_key": exc.period_key,
                "tenant_id": str(exc.tenant_id),
            },
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(MonthlyInputCarryPrevPeriodNotFoundError)
async def _m4_carry_prev_not_found_handler(
    request: Request, exc: MonthlyInputCarryPrevPeriodNotFoundError
) -> JSONResponse:
    """422 MONTHLY_INPUT_CARRY_PREV_PERIOD_NOT_FOUND — prev period
    missing for the tenant.
    """
    return JSONResponse(
        status_code=422,
        content={
            "code": "MONTHLY_INPUT_CARRY_PREV_PERIOD_NOT_FOUND",
            "message_ko": (
                f"이전 기간({exc.prev_period_key})이 존재하지 않습니다. "
                f"먼저 이전 기간을 생성하세요."
            ),
            "details": {
                "prev_period_key": exc.prev_period_key,
                "current_period_key": exc.current_period_key,
                "tenant_id": str(exc.tenant_id),
            },
            "trace_id": exc.trace_id,
        },
    )


# ─────────────────────────────────────────────────────────────
# Story 5.2 — M4 inventory_ledger exception handlers
# (AD-15 §4 envelope mapping for AD-2 append-only + 11-value
# event_type + AD-24 period_key + Epic 11 reversal forward-fill)
# ─────────────────────────────────────────────────────────────


@app.exception_handler(AppendOnlyLedgerViolationError)
async def _m4_append_only_violation_handler(
    request: Request, exc: AppendOnlyLedgerViolationError
) -> JSONResponse:
    """500 APPEND_ONLY_LEDGER_VIOLATION — service-layer AST guard
    caught an UPDATE/DELETE/TRUNCATE/DROP attempt on inventory_ledger.

    AC #3 — 2nd axis of 3중 방어:
    1. DB trigger raises (1st axis) → SQLAlchemy error
    2. Service-layer `_assert_not_modifying` (this exception, 2nd axis)
    3. Audit log emission: `inventory_ledger_event_rejected` (3rd axis)

    When the 2nd axis fires, the DB has NOT been touched. The audit log
    emission is the responsibility of the calling service path; this
    handler only maps the typed exception to the AD-15 envelope.
    """
    return JSONResponse(
        status_code=500,
        content={
            "code": "APPEND_ONLY_LEDGER_VIOLATION",
            "message_ko": ("수불부는 원장만 기록 가능하며 수정·삭제 불가합니다"),
            "details": {
                "event_id": str(exc.event_id) if exc.event_id else None,
                "attempted_op": exc.attempted_op,
                "tenant_id": str(exc.tenant_id),
                **exc.details,
            },
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(InventoryLedgerInvalidEventTypeError)
async def _m4_invalid_event_type_handler(
    request: Request, exc: InventoryLedgerInvalidEventTypeError
) -> JSONResponse:
    """422 INVENTORY_LEDGER_INVALID_EVENT_TYPE — event_type not in the
    11-value whitelist (defense-in-depth; pure kernel rejects upstream).
    """
    return JSONResponse(
        status_code=422,
        content={
            "code": "INVENTORY_LEDGER_INVALID_EVENT_TYPE",
            "message_ko": (
                f"수불 이벤트 타입({exc.event_type!r})이 유효한 11개 값 목록에 없습니다"
            ),
            "details": {
                "event_type": exc.event_type,
                "tenant_id": str(exc.tenant_id),
            },
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(InventoryLedgerPeriodKeyFormatError)
async def _m4_period_key_format_handler(
    request: Request, exc: InventoryLedgerPeriodKeyFormatError
) -> JSONResponse:
    """422 INVENTORY_LEDGER_PERIOD_KEY_FORMAT — period_key AD-24 mismatch.

    PRD §6.2 inventory equation is fiscal ('YYYY-MM'). M8 virtual budget
    keys ('YYYY-MM#B<n>') are explicitly excluded from inventory_ledger.
    """
    return JSONResponse(
        status_code=422,
        content={
            "code": "INVENTORY_LEDGER_PERIOD_KEY_FORMAT",
            "message_ko": (f"기간 키({exc.period_key!r})는 'YYYY-MM' 형식이어야 합니다"),
            "details": {
                "period_key": exc.period_key,
                "tenant_id": str(exc.tenant_id),
            },
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(InventoryLedgerReversalNotYetWiredError)
async def _m4_reversal_not_yet_wired_handler(
    request: Request, exc: InventoryLedgerReversalNotYetWiredError
) -> JSONResponse:
    """501 INVENTORY_LEDGER_REVERSAL_NOT_YET_WIRED — Epic 11 forward-fill.

    M4 entrypoint emits `inventory_ledger_reversal_requested` audit
    marker. The actual reversal sequence INSERT (negating row +
    optional corrected row) is owned by Epic 11 module authority
    (`m11_reversal` module). Until M11 ships, the endpoint returns 501.
    """
    return JSONResponse(
        status_code=501,
        content={
            "code": "INVENTORY_LEDGER_REVERSAL_NOT_YET_WIRED",
            "message_ko": (
                "수불 반전 기능은 Epic 11 모듈 출시 후 활성화됩니다. " "현재는 요청만 기록됩니다."
            ),
            "details": {
                "event_id": str(exc.event_id),
                "tenant_id": str(exc.tenant_id),
                "epic": "Epic 11",
            },
            "trace_id": exc.trace_id,
        },
    )


# ─────────────────────────────────────────────────────────────
# Story 5.3 — M4 closing_guard exception handlers (AD-15 §4).
# Without these, FastAPI returns HTTP 500 for the 5 typed exceptions
# raised by ClosingGuardService — violating the typed envelope
# contract. Mapping:
# - 409 NEGATIVE_CLOSING_INVENTORY — PRD §F4.2 close attempt blocked.
# - 422 CLOSING_GUARD_INVALID_PERIOD_KEY — period_key AD-24 mismatch.
# - 403 INDUSTRY_NOT_SUPPORTED — service-only tenant attempted guard.
# - 500 CLOSING_GUARD_PRODUCTION_CONSUMPTION_ERROR — BOM reconcile fail.
# - 500 CLOSING_GUARD_AUDIT_EMIT_ERROR — CR 1.1 audit-first fail-closed.
# ─────────────────────────────────────────────────────────────


@app.exception_handler(ClosingGuardNegativeInventoryError)
async def _m4_closing_guard_negative_inventory_handler(
    request: Request, exc: ClosingGuardNegativeInventoryError
) -> JSONResponse:
    """409 NEGATIVE_CLOSING_INVENTORY — closing ≥ 0 invariant violated.

    Story 5.3 P4 review patch: SELECT FOR UPDATE row-level lock prevents
    concurrent close attempts from racing past the closing-guard gate.
    P5: 1-shot INSERT atomicity prevents partial event flush.
    """
    return JSONResponse(
        status_code=409,
        content={
            "code": "NEGATIVE_CLOSING_INVENTORY",
            "message_ko": exc.banner_ko,
            "details": {
                "period_key": exc.period_key,
                "tenant_id": str(exc.tenant_id),
                "negative_products": {
                    str(pid): str(qty) for pid, qty in exc.negative_products.items()
                },
            },
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(ClosingGuardInvalidPeriodKeyError)
async def _m4_closing_guard_invalid_period_key_handler(
    request: Request, exc: ClosingGuardInvalidPeriodKeyError
) -> JSONResponse:
    """422 CLOSING_GUARD_INVALID_PERIOD_KEY — period_key not 'YYYY-MM'."""
    return JSONResponse(
        status_code=422,
        content={
            "code": "CLOSING_GUARD_INVALID_PERIOD_KEY",
            "message_ko": f"기간 키({exc.period_key!r})는 'YYYY-MM' 형식이어야 합니다",
            "details": {
                "period_key": exc.period_key,
                "tenant_id": str(exc.tenant_id),
            },
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(ClosingGuardServiceOnlyTenantError)
async def _m4_closing_guard_service_only_handler(
    request: Request, exc: ClosingGuardServiceOnlyTenantError
) -> JSONResponse:
    """403 INDUSTRY_NOT_SUPPORTED — service-only tenant attempted guard."""
    return JSONResponse(
        status_code=403,
        content={
            "code": "INDUSTRY_NOT_SUPPORTED",
            "message_ko": "현재 업종에서 지원하지 않는 기능입니다",
            "details": {
                "feature": "closing_guard",
                "tenant_id": str(exc.tenant_id),
                "industry": exc.industry,
            },
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(ClosingGuardProductionConsumptionError)
async def _m4_closing_guard_production_consumption_handler(
    request: Request, exc: ClosingGuardProductionConsumptionError
) -> JSONResponse:
    """500 CLOSING_GUARD_PRODUCTION_CONSUMPTION_ERROR — BOM reconciliation fail.

    Story 5.3 W1: BOM-aware reconciliation raised a typed error on invalid
    BOM child shape, non-finite Decimal, or BOM matrix malformed. Mapped to
    500 because the failure indicates operator data corruption, not user
    input — operator must investigate via the audit trail.
    """
    return JSONResponse(
        status_code=500,
        content={
            "code": "CLOSING_GUARD_PRODUCTION_CONSUMPTION_ERROR",
            "message_ko": "BOM 수불부 정합성 검증에 실패했습니다 (관리자에게 문의)",
            "details": {
                "tenant_id": str(exc.tenant_id),
                **exc.details,
            },
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(ClosingGuardAuditEmitError)
async def _m4_closing_guard_audit_emit_handler(
    request: Request, exc: ClosingGuardAuditEmitError
) -> JSONResponse:
    """500 CLOSING_GUARD_AUDIT_EMIT_ERROR — CR 1.1 audit-first fail-closed.

    Story 5.3 AD-2 audit-first: if audit row emission fails, the closing
    guard MUST refuse to advance (fail-closed). Mapped to 500 so operator
    sees the audit backlog issue immediately.
    """
    return JSONResponse(
        status_code=500,
        content={
            "code": "CLOSING_GUARD_AUDIT_EMIT_ERROR",
            "message_ko": "closing-guard audit emit 실패 (관리자에게 문의)",
            "details": {
                "tenant_id": str(exc.tenant_id),
                **exc.details,
            },
            "trace_id": exc.trace_id,
        },
    )


# Story 6.3 — Closing PDF export exception handlers (AD-15 §4 envelope).
# Without these, FastAPI returns HTTP 500 for any closing-pdf-export typed
# error, violating the AD-15 `{code, message_ko, details, trace_id}` contract.
@app.exception_handler(ClosingPdfExportInvalidIndustryError)
async def _m4_closing_pdf_export_invalid_industry_handler(
    request: Request, exc: ClosingPdfExportInvalidIndustryError
) -> JSONResponse:
    """422 CLOSING_PDF_EXPORT_INVALID_INDUSTRY — W5 deferral guard.

    Story 6.3 PRD §F6.3: industry extension follow-up (Epic 12+ 결정).
    Until then, only 4 canonical industries accepted.
    """
    return JSONResponse(
        status_code=422,
        content={
            "code": "CLOSING_PDF_EXPORT_INVALID_INDUSTRY",
            "message_ko": (
                "업종 미지원: 4 canonical industries 중 하나여야 합니다 "
                "(manufacturing / manufacturing_service / "
                "manufacturing_service_other / service)"
            ),
            "details": {
                "tenant_id": str(exc.tenant_id),
                "period_key": exc.period_key,
                "industry": exc.industry,
            },
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(ClosingPdfExportSizeExceededError)
async def _m4_closing_pdf_export_size_exceeded_handler(
    request: Request, exc: ClosingPdfExportSizeExceededError
) -> JSONResponse:
    """409 CLOSING_PDF_EXPORT_SIZE_EXCEEDED — PDF > 5MB cap.

    Story 6.3 PRD §F6.3: PDF size ≤ 5MB per period (chunked rendering cap).
    B4: `size_bytes` reflects the actual rendered PDF size (no longer a
    pages*1MB approximation). `cap_bytes` is the 5MB cap.
    """
    return JSONResponse(
        status_code=409,
        content={
            "code": "CLOSING_PDF_EXPORT_SIZE_EXCEEDED",
            "message_ko": "PDF 크기 초과: 5MB cap (PRD §F6.3)",
            "details": {
                "tenant_id": str(exc.tenant_id),
                "period_key": exc.period_key,
                "size_bytes": exc.size_bytes,
                "cap_bytes": exc.cap_bytes,
            },
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(ClosingPdfExportAuditEmitError)
async def _m4_closing_pdf_export_audit_emit_handler(
    request: Request, exc: ClosingPdfExportAuditEmitError
) -> JSONResponse:
    """500 CLOSING_PDF_EXPORT_AUDIT_EMIT_ERROR — CR 1.1 audit-first invariant.

    Story 6.3 PRD §F6.3: closing_pdf_export_viewed audit row MUST be emitted
    BEFORE PDF byte render. If audit emit fails, the PDF export MUST refuse
    to advance (fail-closed).
    """
    return JSONResponse(
        status_code=500,
        content={
            "code": "CLOSING_PDF_EXPORT_AUDIT_EMIT_ERROR",
            "message_ko": "PDF export audit emit 실패 (관리자에게 문의)",
            "details": {
                "tenant_id": str(exc.tenant_id),
                **exc.details,
            },
            "trace_id": exc.trace_id,
        },
    )


# Story 11.1 — M11 reversal sequence exception handlers.
# Without these, FastAPI returns HTTP 500 for any reversal-flow typed error,
# violating the AD-15 `{code, message_ko, details, trace_id}` contract.
@app.exception_handler(ReversalTargetNotFoundError)
async def _m11_reversal_target_not_found_handler(
    request: Request, exc: ReversalTargetNotFoundError
) -> JSONResponse:
    """404 REVERSAL_TARGET_NOT_FOUND — target_event_id not in tenant ledger."""
    return JSONResponse(
        status_code=404,
        content={
            "code": "REVERSAL_TARGET_NOT_FOUND",
            "message_ko": "반전 대상 이벤트를 찾을 수 없습니다",
            "details": {
                "tenant_id": str(exc.tenant_id),
                "target_event_id": str(exc.target_event_id),
            },
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(ReversalRejectedError)
async def _m11_reversal_rejected_handler(
    request: Request, exc: ReversalRejectedError
) -> JSONResponse:
    """403 REVERSAL_REJECTED — capability/period gate rejected."""
    return JSONResponse(
        status_code=403,
        content={
            "code": "REVERSAL_REJECTED",
            "message_ko": exc.reason_ko,
            "details": {
                "tenant_id": str(exc.tenant_id),
                "target_event_id": str(exc.target_event_id),
            },
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(ReversalUnauthorizedError)
async def _m11_reversal_unauthorized_handler(
    request: Request, exc: ReversalUnauthorizedError
) -> JSONResponse:
    """403 REVERSAL_UNAUTHORIZED — caller is not the actor or role mismatch."""
    return JSONResponse(
        status_code=403,
        content={
            "code": "REVERSAL_UNAUTHORIZED",
            "message_ko": "반전 권한이 없습니다 (발행자 본인 또는 admin만 가능)",
            "details": {
                "tenant_id": str(exc.tenant_id),
                "actor_id": str(exc.actor_id),
                "target_event_id": str(exc.target_event_id),
            },
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(ReversalDuplicateError)
async def _m11_reversal_duplicate_handler(
    request: Request, exc: ReversalDuplicateError
) -> JSONResponse:
    """422 REVERSAL_DUPLICATE — (tenant_id, reverses_event_id) unique violation."""
    return JSONResponse(
        status_code=422,
        content={
            "code": "REVERSAL_DUPLICATE",
            "message_ko": "이미 반전된 이벤트입니다",
            "details": {
                "tenant_id": str(exc.tenant_id),
                "target_event_id": str(exc.target_event_id),
            },
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(LockedPeriodReversalRejectedError)
async def _m11_locked_period_reversal_rejected_handler(
    request: Request, exc: LockedPeriodReversalRejectedError
) -> JSONResponse:
    """422 LOCKED_PERIOD_REVERSAL_REJECTED — period_status='locked'."""
    return JSONResponse(
        status_code=422,
        content={
            "code": "LOCKED_PERIOD_REVERSAL_REJECTED",
            "message_ko": "잠금(locked)된 기간의 이벤트는 반전할 수 없습니다",
            "details": {
                "tenant_id": str(exc.tenant_id),
                "target_event_id": str(exc.target_event_id),
                "period_key": exc.period_key,
            },
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(CacheInvalidationChannelInvalidError)
async def _cache_invalidation_channel_invalid_handler(
    request: Request, exc: CacheInvalidationChannelInvalidError
) -> JSONResponse:
    """422 CACHE_INVALIDATION_INVALID_CHANNEL — channel not in ALLOWED_CHANNELS."""
    return JSONResponse(
        status_code=422,
        content={
            "code": "CACHE_INVALIDATION_INVALID_CHANNEL",
            "message_ko": "허용되지 않은 캐시 무효화 채널입니다",
            "details": {
                "channel": exc.channel,
            },
            "trace_id": exc.trace_id,
        },
    )


# ── Story 11.2 — 4 NEW exception handlers for close sequence ────
@app.exception_handler(PartialCloseBlockedError)
async def _m11_partial_close_blocked_handler(
    request: Request, exc: PartialCloseBlockedError
) -> JSONResponse:
    """409 PARTIAL_CLOSE_BLOCKED — 4단계 미완료 시 confirm_close_sequence 거부."""
    return JSONResponse(
        status_code=409,
        content={
            "code": "PARTIAL_CLOSE_BLOCKED",
            "message_ko": exc.reject_reason_ko,
            "details": {
                "tenant_id": str(exc.tenant_id),
                "period_key": exc.period_key,
                "missing_step": exc.missing_step,
            },
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(CloseSequenceAlreadyInitiatedError)
async def _m11_close_sequence_already_initiated_handler(
    request: Request, exc: CloseSequenceAlreadyInitiatedError
) -> JSONResponse:
    """409 CLOSE_SEQUENCE_ALREADY_INITIATED — initiate 중복 호출."""
    return JSONResponse(
        status_code=409,
        content={
            "code": "CLOSE_SEQUENCE_ALREADY_INITIATED",
            "message_ko": "이미 마감 시퀀스가 시작되었습니다",
            "details": {
                "tenant_id": str(exc.tenant_id),
                "period_key": exc.period_key,
            },
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(CloseSequenceNotInitiatedError)
async def _m11_close_sequence_not_initiated_handler(
    request: Request, exc: CloseSequenceNotInitiatedError
) -> JSONResponse:
    """409 CLOSE_SEQUENCE_NOT_INITIATED — step_complete/confirm before initiate.

    Story 11.2 3rd-sweep fix: distinct from ALREADY_INITIATED. Prior
    implementation raised ALREADY_INITIATED for the never-initiated case
    (semantically inverted). New dedicated error code makes the wire
    contract unambiguous.
    """
    return JSONResponse(
        status_code=409,
        content={
            "code": "CLOSE_SEQUENCE_NOT_INITIATED",
            "message_ko": "마감 시퀀스가 시작되지 않았습니다. 먼저 initiate를 호출하세요.",
            "details": {
                "tenant_id": str(exc.tenant_id),
                "period_key": exc.period_key,
            },
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(CloseSequenceStepMismatchError)
async def _m11_close_sequence_step_mismatch_handler(
    request: Request, exc: CloseSequenceStepMismatchError
) -> JSONResponse:
    """409 CLOSE_SEQUENCE_STEP_MISMATCH — 단계 순서 mismatch."""
    return JSONResponse(
        status_code=409,
        content={
            "code": "CLOSE_SEQUENCE_STEP_MISMATCH",
            "message_ko": (
                f"단계 순서가 맞지 않습니다 (시도: {exc.attempted_step}, "
                f"기대: {exc.expected_step})"
            ),
            "details": {
                "tenant_id": str(exc.tenant_id),
                "period_key": exc.period_key,
                "attempted_step": exc.attempted_step,
                "expected_step": exc.expected_step,
            },
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(CloseSequenceCapabilityDeniedError)
async def _m11_close_sequence_capability_denied_handler(
    request: Request, exc: CloseSequenceCapabilityDeniedError
) -> JSONResponse:
    """403 CLOSE_SEQUENCE_CAPABILITY_DENIED — service-only tenant."""
    return JSONResponse(
        status_code=403,
        content={
            "code": "CLOSE_SEQUENCE_CAPABILITY_DENIED",
            "message_ko": "마감 시퀀스 잠금 권한이 없습니다 (제조 부문 전용)",
            "details": {
                "tenant_id": str(exc.tenant_id),
                "industry": exc.industry,
            },
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(ClosingSequenceAlreadyConfirmedError)
async def _m11_closing_sequence_already_confirmed_handler(
    request: Request, exc: ClosingSequenceAlreadyConfirmedError
) -> JSONResponse:
    """409 ALREADY_CONFIRMED — fiscal_periods.status='closed'."""
    return JSONResponse(
        status_code=409,
        content={
            "code": "ALREADY_CONFIRMED",
            "message_ko": "이미 마감 시퀀스가 확정되었습니다",
            "details": {
                "tenant_id": str(exc.tenant_id),
                "period_key": exc.period_key,
                "closed_at": exc.closed_at,
            },
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(ClosingSequenceAuditEmitError)
async def _m11_closing_sequence_audit_emit_handler(
    request: Request, exc: ClosingSequenceAuditEmitError
) -> JSONResponse:
    """500 — audit-first emit failed."""
    return JSONResponse(
        status_code=500,
        content={
            "code": "CLOSING_SEQUENCE_AUDIT_EMIT_FAILED",
            "message_ko": "마감 시퀀스 audit 기록 실패",
            "details": {"error": exc.message},
            "trace_id": exc.trace_id,
        },
    )


# ── Story 11.3 — 4 NEW exception handlers (AD-20 + AD-22 + W2) ──


@app.exception_handler(SnapshotAlreadyCommittedError)
async def _m11_snapshot_already_committed_handler(
    request: Request, exc: SnapshotAlreadyCommittedError
) -> JSONResponse:
    """409 SNAPSHOT_ALREADY_COMMITTED — re-commit on non-verified state."""
    return JSONResponse(
        status_code=409,
        content={
            "code": "SNAPSHOT_ALREADY_COMMITTED",
            "message_ko": "스냅샷이 이미 커밋되어 다시 커밋할 수 없습니다",
            "details": {
                "tenant_id": str(exc.tenant_id),
                "snapshot_id": str(exc.snapshot_id),
                "period_key": exc.period_key,
                "current_state": exc.current_state,
            },
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(ReversalSnapshotMismatchError)
async def _m11_reversal_snapshot_mismatch_handler(
    request: Request, exc: ReversalSnapshotMismatchError
) -> JSONResponse:
    """409 REVERSAL_SNAPSHOT_MISMATCH — target snapshot not in 'committed' state."""
    return JSONResponse(
        status_code=409,
        content={
            "code": "REVERSAL_SNAPSHOT_MISMATCH",
            "message_ko": "되돌리기 대상 스냅샷 상태가 커밋 상태가 아닙니다",
            "details": {
                "tenant_id": str(exc.tenant_id),
                "target_event_id": str(exc.target_event_id),
                "snapshot_id": (
                    str(exc.snapshot_id) if exc.snapshot_id else None
                ),
                "current_state": exc.current_state,
            },
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(ReopenOperatorActionInvalidError)
async def _m11_reopen_operator_action_invalid_handler(
    request: Request, exc: ReopenOperatorActionInvalidError
) -> JSONResponse:
    """422 REOPEN_OPERATOR_ACTION_INVALID — invalid operator_action or reason length."""
    return JSONResponse(
        status_code=422,
        content={
            "code": "REOPEN_OPERATOR_ACTION_INVALID",
            "message_ko": "재오픈 operator_action 또는 사유 길이가 유효하지 않습니다",
            "details": {
                "tenant_id": str(exc.tenant_id),
                "fiscal_period_id": str(exc.fiscal_period_id),
                "operator_action": exc.operator_action,
                "reason_length": exc.reason_length,
            },
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(ReopenAuditEmitFailedError)
async def _m11_reopen_audit_emit_failed_handler(
    request: Request, exc: ReopenAuditEmitFailedError
) -> JSONResponse:
    """503 REOPEN_AUDIT_EMIT_FAILED — audit subsystem unavailable (transient)."""
    response = JSONResponse(
        status_code=503,
        content={
            "code": "REOPEN_AUDIT_EMIT_FAILED",
            "message_ko": "재오픈 audit 기록 실패 (일시적 오류, 재시도 가능)",
            "details": {"error": exc.message},
            "trace_id": exc.trace_id,
        },
    )
    response.headers["Retry-After"] = "5"
    return response


@app.exception_handler(SnapshotNotFoundError)
async def _m11_snapshot_not_found_handler(
    request: Request, exc: SnapshotNotFoundError
) -> JSONResponse:
    """404 SNAPSHOT_NOT_FOUND — fiscal_period_snapshots row missing."""
    return JSONResponse(
        status_code=404,
        content={
            "code": "SNAPSHOT_NOT_FOUND",
            "message_ko": "해당 스냅샷을 찾을 수 없습니다",
            "details": {
                "tenant_id": str(exc.tenant_id),
                "snapshot_id": str(exc.snapshot_id),
            },
            "trace_id": exc.trace_id,
        },
    )


# ─────────────────────────────────────────────────────────────────
# Story 12.4 — M12 2FA mandatory gate exception handlers (16 wired).
# CR 11-2/11-3 lesson: all typed service exceptions get AD-15 §4 envelope.
# Korean SSOT from `apps.api.modules.m12_account.services.audit_extension`.
# ─────────────────────────────────────────────────────────────────


@app.exception_handler(TwoFactorNotEnabledError)
async def _m12_two_factor_not_enabled_handler(
    request: Request, exc: TwoFactorNotEnabledError
) -> JSONResponse:
    """400 TWO_FACTOR_NOT_ENABLED — user has no pending/completed 2FA setup."""
    return JSONResponse(
        status_code=400,
        content={
            "code": "TWO_FACTOR_NOT_ENABLED",
            "message_ko": SETUP_NOT_ENABLED_KO,
            "details": {"user_id": str(exc.user_id)},
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(TwoFactorAlreadyEnabledError)
async def _m12_two_factor_already_enabled_handler(
    request: Request, exc: TwoFactorAlreadyEnabledError
) -> JSONResponse:
    """409 TWO_FACTOR_ALREADY_ENABLED — re-setup without explicit disable."""
    return JSONResponse(
        status_code=409,
        content={
            "code": "TWO_FACTOR_ALREADY_ENABLED",
            "message_ko": SETUP_ALREADY_ENABLED_KO,
            "details": {
                "user_id": str(exc.user_id),
                "enabled_at": exc.enabled_at,
            },
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(TwoFactorAuditEmitError)
async def _m12_two_factor_audit_emit_handler(
    request: Request, exc: TwoFactorAuditEmitError
) -> JSONResponse:
    """503 TWO_FACTOR_AUDIT_EMIT_FAILED — audit subsystem unavailable (transient)."""
    response = JSONResponse(
        status_code=503,
        content={
            "code": "TWO_FACTOR_AUDIT_EMIT_FAILED",
            "message_ko": AUDIT_EMIT_FAILED_KO,
            "details": {"error": exc.message},
            "trace_id": exc.trace_id,
        },
    )
    response.headers["Retry-After"] = "5"
    return response


@app.exception_handler(TwoFactorEncryptionError)
async def _m12_two_factor_encryption_handler(
    request: Request, exc: TwoFactorEncryptionError
) -> JSONResponse:
    """400 TWO_FACTOR_ENCRYPTION_ERROR — NFR6 AES-256-GCM ciphertext failure."""
    return JSONResponse(
        status_code=400,
        content={
            "code": "TWO_FACTOR_ENCRYPTION_ERROR",
            "message_ko": ENCRYPTION_FAILED_KO,
            "details": {"error": exc.message},
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(TwoFactorCryptoKeyMissingError)
async def _m12_two_factor_key_missing_handler(
    request: Request, exc: TwoFactorCryptoKeyMissingError
) -> JSONResponse:
    """500 TWO_FACTOR_KEY_MISSING — env misconfiguration (v1 key absent)."""
    return JSONResponse(
        status_code=500,
        content={
            "code": "TWO_FACTOR_KEY_MISSING",
            "message_ko": KEY_MISSING_KO,
            "details": {"key_id": exc.key_id},
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(TwoFactorRecoveryExhaustedError)
async def _m12_two_factor_recovery_exhausted_handler(
    request: Request, exc: TwoFactorRecoveryExhaustedError
) -> JSONResponse:
    """410 TWO_FACTOR_RECOVERY_EXHAUSTED — all 8 recovery codes consumed."""
    return JSONResponse(
        status_code=410,
        content={
            "code": "TWO_FACTOR_RECOVERY_EXHAUSTED",
            "message_ko": RECOVERY_EXHAUSTED_KO,
            "details": {"user_id": str(exc.user_id)},
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(TwoFactorDisableUnauthorizedError)
async def _m12_two_factor_disable_unauthorized_handler(
    request: Request, exc: TwoFactorDisableUnauthorizedError
) -> JSONResponse:
    """403 TWO_FACTOR_DISABLE_UNAUTHORIZED — neither current code nor admin override."""
    return JSONResponse(
        status_code=403,
        content={
            "code": "TWO_FACTOR_DISABLE_UNAUTHORIZED",
            "message_ko": DISABLE_UNAUTHORIZED_KO,
            "details": {
                "user_id": str(exc.user_id),
                "reason": exc.reason,
            },
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(TwoFactorUserNotFoundError)
async def _m12_two_factor_user_not_found_handler(
    request: Request, exc: TwoFactorUserNotFoundError
) -> JSONResponse:
    """404 TWO_FACTOR_USER_NOT_FOUND — user_id not in tenant."""
    return JSONResponse(
        status_code=404,
        content={
            "code": "TWO_FACTOR_USER_NOT_FOUND",
            "message_ko": USER_NOT_FOUND_KO,
            "details": {"user_id": str(exc.user_id)},
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(TotpInvalidCodeError)
async def _m12_totp_invalid_code_handler(
    request: Request, exc: TotpInvalidCodeError
) -> JSONResponse:
    """401 TOTP_INVALID_CODE — 6-digit code mismatch (RFC 6238)."""
    return JSONResponse(
        status_code=401,
        content={
            "code": "TOTP_INVALID_CODE",
            "message_ko": "인증 코드가 올바르지 않습니다",
            "details": {},
            "trace_id": str(_uuid_mod.uuid4()),
        },
    )


@app.exception_handler(TotpLockoutError)
async def _m12_totp_lockout_handler(
    request: Request, exc: TotpLockoutError
) -> JSONResponse:
    """429 TOTP_LOCKOUT — 5 consecutive failures → 15-min lockout (Retry-After)."""
    response = JSONResponse(
        status_code=429,
        content={
            "code": "TOTP_LOCKOUT",
            "message_ko": CHALLENGE_LOCKED_OUT_KO,
            "details": {"retry_after_seconds": exc.retry_after_seconds},
            "trace_id": str(_uuid_mod.uuid4()),
        },
    )
    response.headers["Retry-After"] = str(exc.retry_after_seconds)
    return response


@app.exception_handler(TotpRecoveryInvalidError)
async def _m12_totp_recovery_invalid_handler(
    request: Request, exc: TotpRecoveryInvalidError
) -> JSONResponse:
    """401 TOTP_RECOVERY_INVALID — recovery code mismatch or already used."""
    return JSONResponse(
        status_code=401,
        content={
            "code": "TOTP_RECOVERY_INVALID",
            "message_ko": "복구 코드가 올바르지 않거나 이미 사용되었습니다",
            "details": {},
            "trace_id": str(_uuid_mod.uuid4()),
        },
    )


@app.exception_handler(ChallengeTokenExpiredError)
async def _m12_challenge_token_expired_handler(
    request: Request, exc: ChallengeTokenExpiredError
) -> JSONResponse:
    """401 TWO_FACTOR_CHALLENGE_TOKEN_EXPIRED — JWT exp claim past now()."""
    return JSONResponse(
        status_code=401,
        content={
            "code": "TWO_FACTOR_CHALLENGE_TOKEN_EXPIRED",
            "message_ko": CHALLENGE_TOKEN_EXPIRED_KO,
            "details": {"token_jti": exc.token_jti, "expired_at": exc.expired_at},
            "trace_id": str(_uuid_mod.uuid4()),
        },
    )


@app.exception_handler(ChallengeTokenInvalidError)
async def _m12_challenge_token_invalid_handler(
    request: Request, exc: ChallengeTokenInvalidError
) -> JSONResponse:
    """401 TWO_FACTOR_CHALLENGE_TOKEN_INVALID — signature / binding mismatch."""
    # P-25: use exc.trace_id when available so audit + envelope share
    # the same correlation ID.
    return JSONResponse(
        status_code=401,
        content={
            "code": "TWO_FACTOR_CHALLENGE_TOKEN_INVALID",
            "message_ko": CHALLENGE_TOKEN_INVALID_KO,
            "details": {"reason": exc.reason},
            "trace_id": getattr(exc, "trace_id", None) or str(_uuid_mod.uuid4()),
        },
    )


@app.exception_handler(ChallengeTokenPurposeMismatchError)
async def _m12_challenge_token_purpose_mismatch_handler(
    request: Request, exc: ChallengeTokenPurposeMismatchError
) -> JSONResponse:
    """401 TWO_FACTOR_CHALLENGE_TOKEN_PURPOSE_MISMATCH — wrong purpose claim."""
    # P-25: use exc.trace_id when available.
    return JSONResponse(
        status_code=401,
        content={
            "code": "TWO_FACTOR_CHALLENGE_TOKEN_PURPOSE_MISMATCH",
            "message_ko": CHALLENGE_TOKEN_PURPOSE_MISMATCH_KO,
            "details": {"actual_purpose": exc.actual_purpose},
            "trace_id": getattr(exc, "trace_id", None) or str(_uuid_mod.uuid4()),
        },
    )


# ── Story 12.4 review P-08: 4 missing exception classes — handlers ──
@app.exception_handler(ChallengeTokenAlreadyConsumedError)
async def _m12_challenge_token_already_consumed_handler(
    request: Request, exc: ChallengeTokenAlreadyConsumedError
) -> JSONResponse:
    """401 CHALLENGE_TOKEN_ALREADY_CONSUMED — replay attempt (P-05)."""
    return JSONResponse(
        status_code=401,
        content={
            "code": "CHALLENGE_TOKEN_ALREADY_CONSUMED",
            "message_ko": CHALLENGE_TOKEN_ALREADY_CONSUMED_KO,
            "details": {"jti": exc.token_jti},
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(TwoFactorChallengeFailedError)
async def _m12_two_factor_challenge_failed_handler(
    request: Request, exc: TwoFactorChallengeFailedError
) -> JSONResponse:
    """401 TWO_FACTOR_CHALLENGE_FAILED — TOTP code verification failed."""
    return JSONResponse(
        status_code=401,
        content={
            "code": "TWO_FACTOR_CHALLENGE_FAILED",
            "message_ko": TWO_FACTOR_CHALLENGE_FAILED_KO,
            "details": {
                "reason": exc.reason,
                "failed_attempts": exc.failed_attempts,
            },
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(TwoFactorRequiredError)
async def _m12_two_factor_required_handler(
    request: Request, exc: TwoFactorRequiredError
) -> JSONResponse:
    """403 TWO_FACTOR_REQUIRED — user must register TOTP before M2 entry."""
    return JSONResponse(
        status_code=403,
        content={
            "code": "TWO_FACTOR_REQUIRED",
            "message_ko": exc.message_ko,
            "details": {"target": exc.target},
            "trace_id": str(_uuid_mod.uuid4()),
        },
    )


@app.exception_handler(M12ForbiddenRoleError)
async def _m12_two_factor_forbidden_role_handler(
    request: Request, exc: M12ForbiddenRoleError
) -> JSONResponse:
    """403 FORBIDDEN_ROLE — viewer/consultant_proxy cannot enter M2."""
    return JSONResponse(
        status_code=403,
        content={
            "code": "FORBIDDEN_ROLE",
            "message_ko": exc.message_ko,
            "details": {"role": exc.role, "target": exc.target},
            "trace_id": str(_uuid_mod.uuid4()),
        },
    )


# ── Story 12.2 — 5 backup envelope handlers (CR 12-5 D-14) ─────
@app.exception_handler(BackupNotFoundError)
async def _backup_not_found_handler(
    request: Request, exc: BackupNotFoundError
) -> JSONResponse:
    """404 BACKUP_NOT_FOUND — backup_id does not resolve in tenant_backups."""
    return JSONResponse(
        status_code=404,
        content={
            "code": "BACKUP_NOT_FOUND",
            "message_ko": BACKUP_NOT_FOUND_KO,
            "details": {
                "backup_id": str(exc.backup_id),
                "tenant_id": str(exc.tenant_id),
            },
            "trace_id": getattr(exc, "trace_id", None)
            or str(_uuid_mod.uuid4()),
        },
    )


@app.exception_handler(BackupPayloadTooLargeError)
async def _backup_payload_too_large_handler(
    request: Request, exc: BackupPayloadTooLargeError
) -> JSONResponse:
    """422 BACKUP_PAYLOAD_TOO_LARGE — serialized JSON exceeds 50 MB cap."""
    return JSONResponse(
        status_code=422,
        content={
            "code": "BACKUP_PAYLOAD_TOO_LARGE",
            "message_ko": BACKUP_PAYLOAD_TOO_LARGE_KO,
            "details": {
                "size_bytes": exc.size_bytes,
                "max_bytes": exc.max_bytes,
            },
            "trace_id": getattr(exc, "trace_id", None)
            or str(_uuid_mod.uuid4()),
        },
    )


@app.exception_handler(BackupRetentionCutoffInvalidError)
async def _backup_retention_cutoff_invalid_handler(
    request: Request, exc: BackupRetentionCutoffInvalidError
) -> JSONResponse:
    """422 BACKUP_RETENTION_CUTOFF_INVALID — retention sweep cutoff invalid."""
    return JSONResponse(
        status_code=422,
        content={
            "code": "BACKUP_RETENTION_CUTOFF_INVALID",
            "message_ko": BACKUP_RETENTION_CUTOFF_INVALID_KO,
            "details": {"reason": exc.reason},
            "trace_id": getattr(exc, "trace_id", None)
            or str(_uuid_mod.uuid4()),
        },
    )


@app.exception_handler(BackupServiceAuditEmitError)
async def _backup_service_audit_emit_handler(
    request: Request, exc: BackupServiceAuditEmitError
) -> JSONResponse:
    """503 BACKUP_AUDIT_EMIT_FAILED — audit-first emit failed (CR 1.1)."""
    return JSONResponse(
        status_code=503,
        headers={"Retry-After": "5"},
        content={
            "code": "BACKUP_AUDIT_EMIT_FAILED",
            "message_ko": BACKUP_AUDIT_EMIT_FAILED_KO,
            "details": {"message": exc.message},
            "trace_id": getattr(exc, "trace_id", None)
            or str(_uuid_mod.uuid4()),
        },
    )


@app.exception_handler(BackupExportServiceError)
async def _backup_export_service_error_handler(
    request: Request, exc: BackupExportServiceError
) -> JSONResponse:
    """500 BACKUP_SERVICE_ERROR — generic backup service failure."""
    return JSONResponse(
        status_code=500,
        content={
            "code": "BACKUP_SERVICE_ERROR",
            "message_ko": BACKUP_SERVICE_ERROR_KO,
            "details": {"message": exc.message},
            "trace_id": getattr(exc, "trace_id", None)
            or str(_uuid_mod.uuid4()),
        },
    )


# ── Story 12.3 (Epic 12) — Account Deletion + Retention Consent ──
# CR 12-5 L3: destructive endpoint 3-layer TOTP defense wired here at HTTP boundary.
# 6 NEW typed exception envelopes (HTTP 401/500/503) for:
#   - DeletionChallengeTokenInvalidError      (401, CR 12-1 L1 JWT verify)
#   - DeletionChallengeTokenExpiredError      (401, CR 12-1 L1 JWT verify)
#   - DeletionConsentEncryptionError          (500, NFR6 AES-256-GCM AAD collision)
#   - DeletionConsentDecryptionError          (500, NFR6 AES-256-GCM AAD collision)
#   - AccountDeletionAuditEmitError           (503, CR 1.1 audit-first fail-closed)
#   - AccountDeletionHardDeleteError          (500, cron-only hard delete failure)
@app.exception_handler(DeletionChallengeTokenInvalidError)
async def _m12_account_deletion_challenge_token_invalid_handler(
    request: Request, exc: DeletionChallengeTokenInvalidError
) -> JSONResponse:
    """401 DELETION_CHALLENGE_TOKEN_INVALID — JWT signature/binding mismatch.

    CR 12-5 L3 (route require_role("owner") + service verify_totp_challenge +
    handler audit-first) — this envelope is the HTTP layer of the L3 chain
    when the destructive challenge token fails cryptographic validation.
    """
    return JSONResponse(
        status_code=401,
        content={
            "code": "DELETION_CHALLENGE_TOKEN_INVALID",
            "message_ko": DELETION_CHALLENGE_TOKEN_INVALID_KO,
            "details": {"reason": exc.reason} if hasattr(exc, "reason") else {},
            "trace_id": getattr(exc, "trace_id", None) or str(_uuid_mod.uuid4()),
        },
    )


@app.exception_handler(DeletionChallengeTokenExpiredError)
async def _m12_account_deletion_challenge_token_expired_handler(
    request: Request, exc: DeletionChallengeTokenExpiredError
) -> JSONResponse:
    """401 DELETION_CHALLENGE_TOKEN_EXPIRED — JWT exp claim past now().

    PyJWT verify_exp=False + caller-controlled now (CR 12-1 L1). This
    envelope is raised when the explicit time check fails.
    """
    return JSONResponse(
        status_code=401,
        content={
            "code": "DELETION_CHALLENGE_TOKEN_EXPIRED",
            "message_ko": DELETION_CHALLENGE_TOKEN_EXPIRED_KO,
            "details": {},
            "trace_id": getattr(exc, "trace_id", None) or str(_uuid_mod.uuid4()),
        },
    )


@app.exception_handler(DeletionConsentEncryptionError)
async def _m12_account_deletion_consent_encryption_handler(
    request: Request, exc: DeletionConsentEncryptionError
) -> JSONResponse:
    """500 DELETION_CONSENT_ENCRYPTION_FAILED — NFR6 AES-256-GCM failure.

    Distinct AAD = b"deletion_consent" (CR 12-1 L2). Never reuse backup AAD.
    """
    return JSONResponse(
        status_code=500,
        content={
            "code": "DELETION_CONSENT_ENCRYPTION_FAILED",
            "message_ko": DELETION_CONSENT_ENCRYPTION_FAILED_KO,
            "details": {"message": exc.message},
            "trace_id": getattr(exc, "trace_id", None) or str(_uuid_mod.uuid4()),
        },
    )


@app.exception_handler(DeletionConsentDecryptionError)
async def _m12_account_deletion_consent_decryption_handler(
    request: Request, exc: DeletionConsentDecryptionError
) -> JSONResponse:
    """500 DELETION_CONSENT_DECRYPTION_FAILED — NFR6 AES-256-GCM failure.

    Distinct AAD = b"deletion_consent" (CR 12-1 L2). Never reuse backup AAD.
    """
    return JSONResponse(
        status_code=500,
        content={
            "code": "DELETION_CONSENT_DECRYPTION_FAILED",
            "message_ko": DELETION_CONSENT_DECRYPTION_FAILED_KO,
            "details": {"message": exc.message},
            "trace_id": getattr(exc, "trace_id", None) or str(_uuid_mod.uuid4()),
        },
    )


@app.exception_handler(AccountDeletionAuditEmitError)
async def _m12_account_deletion_audit_emit_handler(
    request: Request, exc: AccountDeletionAuditEmitError
) -> JSONResponse:
    """503 ACCOUNT_DELETION_AUDIT_EMIT_FAILED — CR 1.1 audit-first fail-closed.

    CR 1.1 invariant: audit emit MUST happen BEFORE state transition; if the
    audit subsystem fails, the destructive state change MUST NOT proceed and
    the client MUST be told to retry. Retry-After = 5s.
    """
    return JSONResponse(
        status_code=503,
        headers={"Retry-After": "5"},
        content={
            "code": "ACCOUNT_DELETION_AUDIT_EMIT_FAILED",
            "message_ko": ACCOUNT_DELETION_AUDIT_EMIT_FAILED_KO,
            "details": {"message": exc.message},
            "trace_id": getattr(exc, "trace_id", None) or str(_uuid_mod.uuid4()),
        },
    )


@app.exception_handler(AccountDeletionHardDeleteError)
async def _m12_account_deletion_hard_delete_handler(
    request: Request, exc: AccountDeletionHardDeleteError
) -> JSONResponse:
    """500 ACCOUNT_DELETION_HARD_DELETE_FAILED — cron-only hard delete failure.

    Raised only by run_hard_delete_cron (T3). Not user-reachable. The hard
    delete job will retry on the next cron tick (KST 04:00 / UTC 19:00).
    """
    return JSONResponse(
        status_code=500,
        content={
            "code": "ACCOUNT_DELETION_HARD_DELETE_FAILED",
            "message_ko": ACCOUNT_DELETION_HARD_DELETE_FAILED_KO,
            "details": {"message": exc.message},
            "trace_id": getattr(exc, "trace_id", None) or str(_uuid_mod.uuid4()),
        },
    )


# ── Story 8.1 (Epic 8) — M8 Budget Scenario CRUD + 1차 MVP 잠금 ──
# CR 12-5 D-14: 3 NEW typed exception envelopes (HTTP 404/409/422) for:
#   - BudgetScenarioNotFoundError          (404 BUDGET_SCENARIO_NOT_FOUND)
#   - ScenarioLimitExceededError           (409 SCENARIO_LIMIT_EXCEEDED — 1차 MVP 한도)
#   - InvalidVirtualBudgetPeriodKeyError   (422 INVALID_VIRTUAL_BUDGET_PERIOD_KEY)
@app.exception_handler(BudgetScenarioNotFoundError)
async def _m8_budget_scenario_not_found_handler(
    request: Request, exc: BudgetScenarioNotFoundError
) -> JSONResponse:
    """404 BUDGET_SCENARIO_NOT_FOUND — GET /budget/scenarios/{period_key} 미존재."""
    return JSONResponse(
        status_code=404,
        content={
            "code": "BUDGET_SCENARIO_NOT_FOUND",
            "message_ko": BUDGET_SCENARIO_NOT_FOUND_KO,
            "details": {
                "period_key": exc.period_key,
                "tenant_id": exc.tenant_id,
            },
            "trace_id": getattr(exc, "trace_id", None)
            or str(_uuid_mod.uuid4()),
        },
    )


@app.exception_handler(ScenarioLimitExceededError)
async def _m8_budget_scenario_limit_exceeded_handler(
    request: Request, exc: ScenarioLimitExceededError
) -> JSONResponse:
    """409 SCENARIO_LIMIT_EXCEEDED — 1차 MVP 시나리오 1개 한도 초과.

    Service-layer `validate_scenario_uniqueness` 1차 gate + DB UNIQUE
    제약 defense-in-depth 2차 gate (CR 12-5 L3).
    """
    return JSONResponse(
        status_code=409,
        content={
            "code": "SCENARIO_LIMIT_EXCEEDED",
            "message_ko": BUDGET_SCENARIO_LIMIT_EXCEEDED_KO,
            "details": {
                "existing_count": exc.existing_count,
                "max_scenarios": 1,
            },
            "trace_id": getattr(exc, "trace_id", None)
            or str(_uuid_mod.uuid4()),
        },
    )


@app.exception_handler(InvalidVirtualBudgetPeriodKeyError)
async def _m8_budget_invalid_virtual_key_handler(
    request: Request, exc: InvalidVirtualBudgetPeriodKeyError
) -> JSONResponse:
    """422 INVALID_VIRTUAL_BUDGET_PERIOD_KEY — AD-24 가상 패턴 위반.

    패턴: `^\\d{4}-(0[1-9]|1[0-2])#B[1-9]\\d*$`
    """
    return JSONResponse(
        status_code=422,
        content={
            "code": "INVALID_VIRTUAL_BUDGET_PERIOD_KEY",
            "message_ko": BUDGET_INVALID_VIRTUAL_KEY_KO,
            "details": {
                "period_key": exc.period_key,
                "expected_pattern": exc.expected_pattern,
            },
            "trace_id": getattr(exc, "trace_id", None)
            or str(_uuid_mod.uuid4()),
        },
    )


# Story 8.2 — 2 NEW typed exception envelopes (CR 12-5 D-14):
#   - BudgetVarianceNotFoundError        (404 BUDGET_VARIANCE_NOT_FOUND)
#   - InvalidVariancePeriodError         (422 INVALID_VARIANCE_PERIOD)
@app.exception_handler(BudgetVarianceNotFoundError)
async def _m8_budget_variance_not_found_handler(
    request: Request, exc: BudgetVarianceNotFoundError
) -> JSONResponse:
    """404 BUDGET_VARIANCE_NOT_FOUND — GET /budget/variance/{period_key} 미존재.

    Story 8.2 (PRD §F8.2) — period_key에 해당하는 budget scenario 미존재 또는
    fiscal_period_snapshots verified row가 없는 경우 (read-only 8-2 atomic wire).
    """
    return JSONResponse(
        status_code=404,
        content={
            "code": "BUDGET_VARIANCE_NOT_FOUND",
            "message_ko": BUDGET_VARIANCE_NOT_FOUND_KO,
            "details": {
                "period_key": exc.period_key,
                "tenant_id": exc.tenant_id,
            },
            "trace_id": getattr(exc, "trace_id", None)
            or str(_uuid_mod.uuid4()),
        },
    )


@app.exception_handler(InvalidVariancePeriodError)
async def _m8_budget_invalid_variance_period_handler(
    request: Request, exc: InvalidVariancePeriodError
) -> JSONResponse:
    """422 INVALID_VARIANCE_PERIOD — variance endpoint period_key 위반.

    Story 8.2 (PRD §F8.2 + AD-24) — variance endpoint는 VIRTUAL period_key
    (`YYYY-MM#B<n>`)만 허용. Real fiscal key (`YYYY-MM`) 또는 malformed string
    시 raise.
    """
    return JSONResponse(
        status_code=422,
        content={
            "code": "INVALID_VARIANCE_PERIOD",
            "message_ko": BUDGET_INVALID_VARIANCE_PERIOD_KO,
            "details": {
                "period_key": exc.period_key,
                "expected_pattern": exc.expected_pattern,
            },
            "trace_id": getattr(exc, "trace_id", None)
            or str(_uuid_mod.uuid4()),
        },
    )


@app.exception_handler(CVPBaselineNotFoundError)
async def _m7_simulation_baseline_not_found_handler(
    request: Request, exc: CVPBaselineNotFoundError
) -> JSONResponse:
    """404 CVP_BASELINE_NOT_FOUND — PRD §F7.1 baseline 미존재.

    CR 12-5 D-14 typed envelope.
    """
    return JSONResponse(
        status_code=404,
        content={
            "code": "CVP_BASELINE_NOT_FOUND",
            "message_ko": CVP_BASELINE_NOT_FOUND_KO,
            "details": {
                "tenant_id": exc.tenant_id,
                "period_key": exc.period_key,
            },
            "trace_id": str(_uuid_mod.uuid4()),
        },
    )


@app.exception_handler(CVPInvalidDeltaError)
async def _m7_simulation_invalid_delta_handler(
    request: Request, exc: CVPInvalidDeltaError
) -> JSONResponse:
    """422 CVP_INVALID_DELTA — PRD §F7.1 delta bounds 위반.

    CR 12-5 D-14 typed envelope.
    """
    return JSONResponse(
        status_code=422,
        content={
            "code": "CVP_INVALID_DELTA",
            "message_ko": CVP_INVALID_DELTA_KO,
            "details": {
                "field": exc.field,
                "value": str(exc.value),
            },
            "trace_id": str(_uuid_mod.uuid4()),
        },
    )


@app.exception_handler(InvalidProjectionMonthError)
async def _m7_simulation_invalid_projection_month_handler(
    request: Request, exc: InvalidProjectionMonthError
) -> JSONResponse:
    """422 INVALID_PROJECTION_MONTH — PRD §F7.2 projection_month 위반.

    CR 12-5 D-14 typed envelope. Format mismatch or chronological
    invariant violation (projection_month > period_key).
    """
    return JSONResponse(
        status_code=422,
        content={
            "code": "INVALID_PROJECTION_MONTH",
            "message_ko": INVALID_PROJECTION_MONTH_KO,
            "details": {
                "period_key": exc.period_key,
                "projection_month": exc.projection_month,
                "reason": getattr(exc, "reason", None),
            },
            "trace_id": str(_uuid_mod.uuid4()),
        },
    )


@app.exception_handler(ProjectionInputsInvalidError)
async def _m7_simulation_projection_inputs_invalid_handler(
    request: Request, exc: ProjectionInputsInvalidError
) -> JSONResponse:
    """422 PROJECTION_INPUTS_INVALID — PRD §F7.2 4종 파라미터 (차입금·이자율·상승률·세율) 범위/형식 위반.

    CR 12-5 D-14 typed envelope. Wraps kernel-level `ProjectionInvalidInputError`
    into HTTP envelope via service-layer translator.
    """
    return JSONResponse(
        status_code=422,
        content={
            "code": "PROJECTION_INPUTS_INVALID",
            "message_ko": PROJECTION_INPUTS_INVALID_KO,
            "details": {
                "tenant_id": exc.tenant_id,
                "period_key": exc.period_key,
                "field": getattr(exc, "field", None),
                "reason": exc.reason,
            },
            "trace_id": str(_uuid_mod.uuid4()),
        },
    )


@app.exception_handler(ProjectionBaselineNotFoundError)
async def _m7_simulation_projection_baseline_not_found_handler(
    request: Request, exc: ProjectionBaselineNotFoundError
) -> JSONResponse:
    """404 PROJECTION_BASELINE_NOT_FOUND — PRD §F7.2 baseline 미존재.

    CR 12-5 D-14 typed envelope. Wraps CVP baseline fetch failure
    into projection-specific 404 envelope.
    """
    return JSONResponse(
        status_code=404,
        content={
            "code": "PROJECTION_BASELINE_NOT_FOUND",
            "message_ko": PROJECTION_BASELINE_NOT_FOUND_KO,
            "details": {
                "tenant_id": getattr(exc, "tenant_id", None),
                "period_key": getattr(exc, "period_key", None),
            },
            "trace_id": str(_uuid_mod.uuid4()),
        },
    )


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint — used by Railway / Vercel / CI smoke tests."""
    return {"status": "ok", "service": "costmgr-api", "version": "0.1.0"}


@app.on_event("startup")
async def _attach_tenant_listener() -> None:
    """Story 0.2 — wire the SET LOCAL app.current_tenant_id listener.

    Imported lazily so test environments without a real DB engine don't crash.
    """
    try:
        from apps.api.core.db import get_engine
        from apps.api.core.tenant_context import attach_tenant_listener

        attach_tenant_listener(get_engine())
    except RuntimeError:
        # No DATABASE_URL configured (e.g. README quickstart smoke test). Skip.
        pass
