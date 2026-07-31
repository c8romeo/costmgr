"""M1 Baseline / BOM module — Epic 2 stories 2.1~2.3 will populate this.

Story 1.2 scaffold: `router` exposes the account-classification endpoints
needed by the Settings Wizard completion status query.
"""

from apps.api.modules.m1_baseline.handlers import router

__all__ = ["router"]
