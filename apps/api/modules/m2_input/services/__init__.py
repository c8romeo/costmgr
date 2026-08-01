"""apps.api.modules.m2_input.services — M2 monthly input service layer.

Re-exports `MonthlyInputService` (Story 3.1) so callers can
`from apps.api.modules.m2_input.services import MonthlyInputService`.
"""

from apps.api.modules.m2_input.services.monthly_input_service import (  # noqa: F401
    MonthlyInputCapabilityError,
    MonthlyInputInvalidPayloadError,
    MonthlyInputNotFoundError,
    MonthlyInputPeriodLockedError,
    MonthlyInputService,
    MonthlyInputStreamNotSupportedError,
)

__all__ = [
    "MonthlyInputService",
    "MonthlyInputNotFoundError",
    "MonthlyInputInvalidPayloadError",
    "MonthlyInputPeriodLockedError",
    "MonthlyInputCapabilityError",
    "MonthlyInputStreamNotSupportedError",
]