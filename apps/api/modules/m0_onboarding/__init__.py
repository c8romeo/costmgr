"""apps.api.modules.m0_onboarding — M0 onboarding module (Story 1.1).

Owns the `tenant_settings.onboarding` JSONB namespace (AD-23). Subsequent
stories in Epic 1 (1.2 wizard, 1.3 AI extraction) extend this package.

Re-exports:
  - `router` (FastAPI APIRouter) — wire into `apps.api.main`
  - `Industry`, `MenuItem`, etc. — domain re-exports for convenience
"""

from __future__ import annotations

from apps.api.modules.m0_onboarding.handlers import router, signup_router
from apps.api.modules.m0_onboarding.menu import (
    GRACE_PERIOD_DAYS,
    INDUSTRY_LABEL_KO,
    SEGMENT_SPLIT_TOOLTIP,
    Industry,
    MenuItem,
    get_menu,
    get_menu_labels,
)

__all__ = [
    "GRACE_PERIOD_DAYS",
    "INDUSTRY_LABEL_KO",
    "Industry",
    "MenuItem",
    "SEGMENT_SPLIT_TOOLTIP",
    "get_menu",
    "get_menu_labels",
    "router",
    "signup_router",
]
