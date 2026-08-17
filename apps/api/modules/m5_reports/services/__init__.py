"""apps.api.modules.m5_reports.services — Story 9.4 re-exports.

Re-exports `Report21Service` for handler import convenience + JSON-safe
serializer re-exports for envelope (CR 12-1 L3 + AD-15 §1 boundary).
"""
from __future__ import annotations

from apps.api.modules.m5_reports.services.report21_service import (
    Report21Service,
    Report21State,
)

__all__ = [
    "Report21Service",
    "Report21State",
]
