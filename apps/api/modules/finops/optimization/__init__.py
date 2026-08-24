"""apps.api.modules.finops.optimization — FinOps Optimization & Rightsizing territory.

Phase 14 (cj-style 119번째 wire) — FinOps Optimization & Rightsizing
territory (PRD §F30.1~§F30.8 + AD-41 (a)~(g) 7 sub-decisions).

This subpackage provides:
- `serializers` — m22_finops_optimization.optimization_serializers
  module version SSOT (CR 12-5 D-PARITY-01 Python ↔ TypeScript mirror).

CR lessons applied:
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface
  parity verification (verifiable via apps/web/lib/finops-optimization/
  finops-optimization-client.ts).
- CR 11-4 P-015 — pure validator pattern.

AD-41 FinOps Optimization & Rightsizing 신규 (Phase 14).
"""
from __future__ import annotations

from apps.api.modules.finops.optimization.serializers import (
    m22_finops_optimization,
    optimization_deserialize,
    optimization_serializers,
)

__all__ = [
    "m22_finops_optimization",
    "optimization_serializers",
    "optimization_deserialize",
]
