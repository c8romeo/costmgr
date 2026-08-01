"""apps.api.modules.m2_input.services — M2 monthly input service layer.

Re-exports `MonthlyInputService` (Story 3.1) + the typed exception
hierarchy (Story 3.1 + 3.2 + 3.3) so callers can
`from apps.api.modules.m2_input.services import MonthlyInputService`.
"""

from apps.api.modules.m2_input.services.monthly_input_service import (  # noqa: F401
    MonthlyInputCapabilityError,
    MonthlyInputCompanyBurdenRateError,
    MonthlyInputFteReadOnlyError,
    MonthlyInputInventoryProjectionError,
    MonthlyInputInvalidLaborShapeError,
    MonthlyInputInvalidPayloadError,
    MonthlyInputNotFoundError,
    MonthlyInputPayTypeMismatchError,
    MonthlyInputPayrollSettingsInvalidError,
    MonthlyInputPeriodLockedError,
    MonthlyInputService,
    MonthlyInputStreamNotSupportedError,
    MonthlyInputWarningsReadOnlyError,
)

__all__ = [
    "MonthlyInputService",
    "MonthlyInputNotFoundError",
    "MonthlyInputInvalidPayloadError",
    "MonthlyInputPeriodLockedError",
    "MonthlyInputCapabilityError",
    "MonthlyInputStreamNotSupportedError",
    # Story 3.2 — labor precision exceptions
    "MonthlyInputInvalidLaborShapeError",
    "MonthlyInputFteReadOnlyError",
    "MonthlyInputPayrollSettingsInvalidError",
    "MonthlyInputCompanyBurdenRateError",
    "MonthlyInputPayTypeMismatchError",
    # Story 3.3 — warning / projection exceptions
    "MonthlyInputWarningsReadOnlyError",
    "MonthlyInputInventoryProjectionError",
]
