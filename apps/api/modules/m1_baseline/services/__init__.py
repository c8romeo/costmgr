"""apps.api.modules.m1_baseline.services — M1 baseline service layer.

Re-exports `ProductService` (Story 2.1) and `BOMService` (Story 2.2) so
callers can `from apps.api.modules.m1_baseline.services import ProductService, BOMService`.
"""

from apps.api.modules.m1_baseline.services.bom_service import (  # noqa: F401
    BOMChildNotFoundError,
    BOMDuplicateChildError,
    BOMInvalidChildTypeError,
    BOMInvalidParentTypeError,
    BOMInvalidRatioError,
    BOMParentNotFoundError,
    BOMService,
)
from apps.api.modules.m1_baseline.services.product_service import (  # noqa: F401
    InvalidProductCodeError,
    InvalidProductTypeError,
    ProductCapabilityError,
    ProductCodeDuplicateError,
    ProductImmutableFieldError,
    ProductNotFoundError,
    ProductService,
    ProductTypeHasReferencesError,
)

__all__ = [
    "BOMService",
    "BOMChildNotFoundError",
    "BOMDuplicateChildError",
    "BOMInvalidChildTypeError",
    "BOMInvalidParentTypeError",
    "BOMInvalidRatioError",
    "BOMParentNotFoundError",
    "InvalidProductCodeError",
    "InvalidProductTypeError",
    "ProductCapabilityError",
    "ProductCodeDuplicateError",
    "ProductImmutableFieldError",
    "ProductNotFoundError",
    "ProductService",
    "ProductTypeHasReferencesError",
]
