"""apps.api.modules.m9_abc.schemas — M9 ABC Pydantic models (Story 1.2).

Scaffold only — full ABC engine lands in Epic 9 (Story 9.x). This module
ships the read endpoint needed by the Settings Wizard completion status
query.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DriverRequest(BaseModel):
    """Body of POST /api/v1/abc/drivers.

    Story 1.2 Task 4.2 — scaffold endpoint that the wizard calls to register
    a cost-driver. Real Epic 9 module will move this into a full driver CRUD.
    """

    model_config = ConfigDict(extra="forbid")

    driver_name: str = Field(..., min_length=1, max_length=120)
    unit: str = Field(..., min_length=1, max_length=40)
    practical_capacity_hours: int = Field(..., ge=0)


class DriverCountResponse(BaseModel):
    """Body of GET /api/v1/abc/drivers."""

    model_config = ConfigDict(extra="forbid")

    driver_count: int = Field(..., description="Number of drivers registered.")
