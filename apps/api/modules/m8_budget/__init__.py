"""M8 Budget vs Actual module — Epic 8 stories 8.1~8.3 populate this.

Story 8.1 — Virtual Budget Period Key + Scenario Lock to One
  (PRD §F8.1 + AD-24 period key typed pattern + 1차 시나리오 1개 잠금)
  + Story 8.2 — Budget vs Actual Variance Table with ABCD Gray Badge
  (PRD §F8.2 — honestly DEFER follow-up)
  + Story 8.3 — Budget Pre-Standard Cost Preview
  (`engine_type='budget'` + `fiscal_period_snapshots` reuse — honestly DEFER).

Module authority mirrors Epic 4·5·6·11·12 cj-style 7번째 epic 패턴:
  - `handlers.py` — 3 endpoints (POST / GET list / GET by period_key)
  - `services/budget_scenario_service.py` — thin orchestration wrapper
  - `schemas.py` — Pydantic v2 request/response
  - `exceptions.py` — 3 typed exceptions (CR 12-5 D-14 envelope)

Capability gate: `Capability.BUDGET_SCENARIO` (industry-agnostic, CR 12-1 L4 +
7-1/7-2 L4 precedent — all 4 industries grant).
"""

from apps.api.modules.m8_budget.handlers import router, variance_router

__all__ = ["router", "variance_router"]
