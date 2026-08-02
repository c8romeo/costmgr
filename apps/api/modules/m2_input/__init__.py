"""M2 Monthly Input Capture module — Story 3.1.

Exposes the FastAPI router for the six-stream monthly input domain.
"""

from apps.api.modules.m2_input.handlers import router

__all__ = ["router"]
