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


__all__ = [
    "BaseError",
    "BadRequestError",
    "ForbiddenError",
    "ConflictError",
    "UnprocessableEntityError",
    "LockedError",
    "GatewayTimeoutError",
]
