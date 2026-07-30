"""apps.api.modules.m0_onboarding.menu — re-export shim.

Story 1.1 — Task 2.6 (re-exports). Keeps the import path local to the API
module (apps.api.modules.m0_onboarding.*) while the canonical
implementation lives in `packages.services.m0_onboarding.industry_menu`.

This indirection lets future stories evolve the API module independently
from the shared domain (e.g. add a route-specific validator) without
touching `packages.services` — which is also consumed by the TS mirror
in `apps/web/lib/menu-config.ts`.
"""

from __future__ import annotations

from packages.services.m0_onboarding.industry_menu import (  # noqa: F401 — re-export
    GRACE_PERIOD_DAYS,
    INDUSTRY_LABEL_KO,
    SEGMENT_SPLIT_TOOLTIP,
    Industry,
    IndustryChangeDecision,
    MenuItem,
    get_menu,
    get_menu_labels,
    is_industry_change_allowed,
)

__all__ = [
    "GRACE_PERIOD_DAYS",
    "INDUSTRY_LABEL_KO",
    "Industry",
    "IndustryChangeDecision",
    "MenuItem",
    "SEGMENT_SPLIT_TOOLTIP",
    "get_menu",
    "get_menu_labels",
    "is_industry_change_allowed",
]
