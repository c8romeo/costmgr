"""apps.api.modules.m1_baseline.schemas — M1 baseline Pydantic models (Story 1.2).

Scaffold only — full CRUD lives in Epic 2 (Story 2.x). This module ships
the read endpoints needed by the Settings Wizard completion status query.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AccountClassificationRequest(BaseModel):
    """Body of POST /api/v1/baseline/accounts/classification.

    Story 1.2 Task 4.1 — scaffold endpoint that the wizard calls to set an
    account's `direct_indirect` / `fixed_variable` classification. The
    real Epic 2 module will move this into a full account CRUD surface.
    """

    model_config = ConfigDict(extra="forbid")

    account_id: str = Field(..., description="Logical account id (UUID string).")
    direct_indirect: str | None = Field(
        default=None,
        description="`direct` | `indirect` (null = unclassified).",
    )
    fixed_variable: str | None = Field(
        default=None,
        description="`fixed` | `variable` (null = unclassified).",
    )


class AccountClassificationResponse(BaseModel):
    """Body of GET /api/v1/baseline/accounts/classification."""

    model_config = ConfigDict(extra="forbid")

    direct_indirect_count: int = Field(
        ..., description="Number of accounts with `direct_indirect` set."
    )
    fixed_variable_count: int = Field(
        ..., description="Number of accounts with `fixed_variable` set."
    )