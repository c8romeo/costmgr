"""apps.api.modules.m10_ai — M10 AI extraction module (Story 1.3).

Routes (registered by handlers.py):
  POST /api/v1/ai-documents                — upload a document + run extraction
  GET  /api/v1/ai-documents                — list the tenant's uploaded documents
  GET  /api/v1/ai-documents/{document_id}  — read one uploaded document + drafts
  POST /api/v1/ai-documents/{id}/reprocess — retry a failed extraction

  GET  /api/v1/ai-drafts                   — list input_drafts (filter by state)
  PATCH /api/v1/ai-drafts/{draft_id}       — confirm/reject one draft
  POST /api/v1/ai-drafts/promote           — promote confirmed drafts → company_subblock

AD-1 / AD-11 layering:
  - This package owns the FastAPI router + Pydantic schemas.
  - The port (`packages.services.m10_ai.extraction_port`) lives in the
    services layer; the adapter (`apps.api.modules.m10_ai.adapters.*`)
    implements it.
  - Persistence uses the service_role session (AD-2 — M10 owns the
    uploads + drafts aggregate; M0 does not touch it).

Real Anthropic SDK integration is gated by [STACK BUMP] workflow
(Story 0.3 lesson) — `claude_vision.py` exists as a stub. The fake
adapter (`fake_adapter.py`) is the default for tests + dev without an
API key.
"""

from apps.api.modules.m10_ai.handlers import router  # noqa: E402,F401

