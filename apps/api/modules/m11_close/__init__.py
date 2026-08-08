"""M11 Close & Audit module — Epic 11 stories 11.1~11.3 will populate this.

Story 11.1 — REVERSAL_REQUEST wire:
- `router` is the FastAPI APIRouter for `POST /api/v1/close/reversal-requests`,
  `GET /api/v1/close/reversal-requests/{correction_group_id}`, and
  `POST /api/v1/close/cache-invalidation`.
"""

from apps.api.modules.m11_close.handlers import router

__all__ = ["router"]
