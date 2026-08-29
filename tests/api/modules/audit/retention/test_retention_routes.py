"""tests.api.modules.audit.retention.test_retention_routes — response model tests.

D-AD-14-2 (cj-style 208 source sprint) — 6 NEW pytest cases covering:

  - RetentionPolicyResponse BaseModel field set matches kernel
    RetentionPolicy(dict) verbatim (TS mirror parity, CR 12-5 D-PARITY-01).
  - RetentionPolicyResponse(**parse_retention_policy(...)) round-trip
    preserves all 5 fields.
  - RetentionPolicyResponse.model_dump() produces the same JSON shape
    as the kernel dict (wire-format parity).
  - RetentionPolicyResponse field types are correct
    (tenant_id: str, action_class: RetentionClass, days: int,
     archive: bool, mask_pii: bool).
  - import apps.api.main does NOT raise FastAPIError
    (regression guard for D-AD-14-2 source defect).

The fix wire: kernel `RetentionPolicy(dict)` in `retention_dsl.py`
remains the pure-functional return type for `retain()` /
`parse_retention_policy()` (preserving all existing kernel tests'
`["key"]` access pattern). The API surface introduces a dedicated
`RetentionPolicyResponse(BaseModel)` in `retention_routes.py` so
FastAPI's `response_model=` parameter accepts it.
"""
from __future__ import annotations

import typing
import uuid
from typing import get_type_hints

from apps.api.modules.audit.retention.retention_dsl import (
    DEFAULT_RETENTION_DAYS,
    parse_retention_policy,
)
from apps.api.modules.audit.retention.retention_routes import (
    RetentionPolicyResponse,
)


class TestRetentionPolicyResponseShape:
    """RetentionPolicyResponse field set / TS mirror parity."""

    def test_field_set_matches_kernel_dict_keys(self) -> None:
        """The 5 RetentionPolicyResponse fields MUST match the kernel dict keys.

        CR 12-5 D-PARITY-01 inversion: Python ↔ TypeScript field parity.
        """
        annotations = get_type_hints(RetentionPolicyResponse)
        assert set(annotations) == {
            "tenant_id",
            "action_class",
            "days",
            "archive",
            "mask_pii",
        }

    def test_field_types_match_kernel_contract(self) -> None:
        """Field types must be the canonical AD-8/AD-22/CR 12-5 contract."""
        annotations = get_type_hints(RetentionPolicyResponse)
        assert annotations["tenant_id"] is str
        assert annotations["days"] is int
        assert annotations["archive"] is bool
        assert annotations["mask_pii"] is bool
        # action_class is RetentionClass Literal["admin"|"auth"|"data"|"security"]
        # — typing.get_type_hints resolves Literal to its underlying form.
        assert typing.get_args(annotations["action_class"]) == (
            "admin",
            "auth",
            "data",
            "security",
        )


class TestRetentionPolicyResponseRoundTrip:
    """parse_retention_policy() → RetentionPolicyResponse(**) round-trip."""

    def _tenant(self) -> uuid.UUID:
        return uuid.UUID("11111111-1111-1111-1111-111111111111")

    def test_round_trip_preserves_all_5_fields(self) -> None:
        policy = parse_retention_policy(
            self._tenant(),
            {"action_class": "admin", "days": 365, "archive": True, "mask_pii": True},
        )
        response = RetentionPolicyResponse(**policy)
        assert response.tenant_id == "11111111-1111-1111-1111-111111111111"
        assert response.action_class == "admin"
        assert response.days == 365
        assert response.archive is True
        assert response.mask_pii is True

    def test_model_dump_matches_kernel_dict_shape(self) -> None:
        """model_dump() JSON shape MUST equal the kernel dict (wire-format parity)."""
        policy = parse_retention_policy(
            self._tenant(),
            {"action_class": "security", "days": 2555, "archive": True, "mask_pii": True},
        )
        response = RetentionPolicyResponse(**policy)
        dumped = response.model_dump()
        assert dumped == {
            "tenant_id": "11111111-1111-1111-1111-111111111111",
            "action_class": "security",
            "days": 2555,
            "archive": True,
            "mask_pii": True,
        }
        # CR 12-5 D-PARITY-01: JSON keys match TS mirror verbatim.
        assert set(dumped) == set(policy)

    def test_default_days_round_trip_for_all_4_classes(self) -> None:
        """Each RetentionClass default day count must round-trip cleanly."""
        for cls in ("admin", "auth", "data", "security"):
            policy = parse_retention_policy(self._tenant(), {"action_class": cls})
            response = RetentionPolicyResponse(**policy)
            assert response.days == DEFAULT_RETENTION_DAYS[cls]
            assert response.action_class == cls


class TestImportAppsApiMainRegressionGuard:
    """Regression guard: importing apps.api.main must NOT raise FastAPIError.

    D-AD-14-2 pre-existing defect: RetentionPolicy(dict) used as
    `response_model=` raised fastapi.exceptions.FastAPIError at
    apps.api.main import time. Fix wire (cj-style 208) introduces
    RetentionPolicyResponse(BaseModel) for the API surface, keeping
    kernel RetentionPolicy(dict) intact.
    """

    def test_apps_api_main_imports_cleanly(self) -> None:
        import importlib

        importlib.import_module("apps.api.main")
