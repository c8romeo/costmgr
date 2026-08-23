"""apps/api/core/errors.py — Base error hierarchy for typed exception envelope.

CR 12-5 D-14 typed exception envelope + CR 11-4 P-015.

Phase 9 (cj-style 99번째 wire) — central BaseError + HTTPError subclasses
shared by chaos (chaos_experiment + fault_injection + auto_rollback +
tenant_scoping + game_day + continuous_chaos) and prior phases
(dr_drill + failover_orchestrator).
"""
from __future__ import annotations

import uuid
from typing import Any


class BaseError(Exception):
    """Root of the typed-exception hierarchy (CR 12-5 D-14 + CR 11-4 P-015).

    All domain errors inherit from this so catch blocks can reliably
    distinguish typed exceptions from generic Python exceptions.

    Accepts arbitrary keyword args via **kwargs so subclasses can pass
    structured envelope fields (code + message_ko + details + trace_id +
    http_status) without each one redefining __init__.
    """

    http_status: int = 500

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        message = kwargs.pop("message", args[0] if args else "")
        message_ko = kwargs.pop("message_ko", "")
        # Store message_ko as the primary args so __str__ returns it.
        primary = message_ko or message
        super().__init__(primary)
        self.message = message
        self.code = kwargs.pop("code", self.__class__.__name__)
        self.message_ko = message_ko or message
        self.details: dict[str, Any] = kwargs.pop("details", {})
        self.trace_id: str = kwargs.pop("trace_id", str(uuid.uuid4()))
        self.http_status = kwargs.pop("http_status", self.http_status)
        # Store any additional kwargs as attributes
        for key, value in kwargs.items():
            setattr(self, key, value)


# ── HTTP error classes (typed exception envelope helpers) ──────

class BadRequestError(BaseError):
    """HTTP 400 typed error."""

    http_status: int = 400


class ForbiddenError(BaseError):
    """HTTP 403 typed error (owner-only RBAC, AD-22)."""

    http_status: int = 403


class ConflictError(BaseError):
    """HTTP 409 typed error."""

    http_status: int = 409


class UnprocessableEntityError(BaseError):
    """HTTP 422 typed error."""

    http_status: int = 422


class LockedError(BaseError):
    """HTTP 423 typed error."""

    http_status: int = 423


class GatewayTimeoutError(BaseError):
    """HTTP 504 typed error."""

    http_status: int = 504


# ── FinOps Showback / Chargeback typed exceptions ──────
# Phase 11 (cj-style 107번째 wire) — CR 12-5 D-14 typed exception
# envelope applied to 6 NEW exceptions shared across showback_dsl +
# showback_query + chargeback_engine + chargeback_rule_evaluator +
# department_mapping + chargeback_export modules.

# Module identifier used by typed exception envelopes (mirrors
# m17_chaos_engineering + m18_slo_engineering pattern).
FINOPS_MODULE_ID: str = "m19_finops"


class FinopsError(BaseError):
    """Base for FinOps showback/chargeback typed exceptions.

    Provides FINOPS_MODULE_ID class attribute + finops envelope shape
    `{code, message_ko, details, trace_id, module_id}` shared by all
    6 NEW exception subclasses below.
    """

    module_id: str = FINOPS_MODULE_ID


class ShowbackDefinitionInvalidError(FinopsError):
    """HTTP 400 typed error — showback DSL validation failure.

    Raised by parse_showback_definition() when 6 validation rules
    (PRD §F27.1.7 verbatim) detect invalid group_by / period_key /
    currency_code / comparison_period / pagination / tenant_id.
    """

    http_status: int = 400


class ShowbackExportError(FinopsError):
    """HTTP 500 typed error — showback CSV export failure.

    Raised by export_showback_csv() when StreamingResponse generator
    fails (e.g. DB connection drop mid-stream, encoding error).
    """

    http_status: int = 500


class ChargebackRuleInvalidError(FinopsError):
    """HTTP 400 typed error — chargeback rule validation failure.

    Raised by evaluate_chargeback_rule() when 4 validation rules
    detect invalid rule_type / markup_pct / tax_pct / cost_allocation.
    """

    http_status: int = 400


class ChargebackCalculationError(FinopsError):
    """HTTP 500 typed error — chargeback calculation failure.

    Raised by compute_chargeback() when banker's rounding fails or
    Decimal precision overflows.
    """

    http_status: int = 500


class ChargebackExportError(FinopsError):
    """HTTP 500 typed error — chargeback CSV/PDF export failure.

    Raised by export_chargeback_csv() + export_chargeback_pdf()
    when StreamingResponse generator fails (e.g. reportlab rendering
    error, PDF encryption failure).
    """

    http_status: int = 500


class ChargebackExportRateLimitedError(FinopsError):
    """HTTP 429 typed error — chargeback export rate limit exceeded.

    Raised when owner > 1 export / minute default + Retry-After header.
    """

    http_status: int = 429


__all__ = [
    "BaseError",
    "BadRequestError",
    "ForbiddenError",
    "ConflictError",
    "UnprocessableEntityError",
    "LockedError",
    "GatewayTimeoutError",
    # Phase 11 FinOps showback/chargeback typed exceptions (CR 12-5 D-14)
    "FinopsError",
    "FINOPS_MODULE_ID",
    "ShowbackDefinitionInvalidError",
    "ShowbackExportError",
    "ChargebackRuleInvalidError",
    "ChargebackCalculationError",
    "ChargebackExportError",
    "ChargebackExportRateLimitedError",
]
