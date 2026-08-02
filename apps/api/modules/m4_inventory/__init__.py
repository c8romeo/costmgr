"""M4 Inventory module — Epic 5 stories 5.1~5.3.

Story 5.1 (this revision) wires `opening_inventory` JSONB auto-carry
chain via `apps.api.modules.m4_inventory.services.opening_carry_service`
and exposes a single manual trigger route:

  POST /api/v1/inventory/opening-carry/{period_id}

The auto-carry chain hooks into
`apps.api.modules.m2_input.services.monthly_input_service` (get_state +
save_row); no separate auto-trigger route is needed.

Story 5.3 will add the frontend toast sonner consumer for carry chain
events; that lands separately under Story 0.5 plumbing.
"""

from apps.api.modules.m4_inventory.handlers import router

__all__ = ["router"]
