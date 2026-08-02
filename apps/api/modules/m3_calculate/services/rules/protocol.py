"""apps.api.modules.m3_calculate.services.rules.protocol — AD-5 pure rule contract.

Story 4.3 (Task 1.2) — VerificationRule protocol + RuleInput + VerificationItem.

AD-5 purity invariant:
- NO `sqlalchemy`, `psycopg`, `asyncpg` (DB layer).
- NO `fastapi`, `starlette`, `httpx` (web layer).
- NO `time`, `datetime.datetime.now()`, `os.environ` (clock/IO).
- NO `random`, `secrets` (non-determinism).

Verified by AST import check in
`tests/cost_engine/test_verification_rules.py::test_verification_rules_no_io_imports`.

`VerificationStatus` is intentionally limited to `passed` / `failed`. The
`skipped` value lives outside this enum because skipped rules do NOT
appear in `verifications[]` (Story 4.3 AC #2 — applies_to=False → silent
skip → not in array). The `VerificationStatusLiteral` here is for the
individual item's status, not the envelope-level `top_failure` discriminator.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol
from uuid import UUID

from packages.cost_engine.core.period_cost import Baseline
from packages.cost_engine.ports.calc_port import CalcResult, MonthlyInput
from packages.services.m0_onboarding.industry_menu import Industry

# Per-industry firing rule (Story 4.3 AC #7):
# - V1, V4, V8: fire for all industries (universal invariants).
# - V7: fires only for service-only industry (`ABC 무결성`). Manufacturing
#   BOM 100% is enforced by Story 2.2 gate (separate step).
#
# Industry values are SSOT-re-exported from `packages.services.m0_onboarding.industry_menu.Industry`
# so any new tenant industry value propagates to the verification rules
# (CR 1.1 lesson — drift detector enforced in tests/api/test_verdict_envelope.py).
INDUSTRY_MANUFACTURING: Literal["manufacturing"] = Industry.MANUFACTURING.value
INDUSTRY_MANUFACTURING_SERVICE: Literal["manufacturing_service"] = (
    Industry.MANUFACTURING_SERVICE.value
)
INDUSTRY_SERVICE: Literal["service"] = Industry.SERVICE.value
INDUSTRY_MANUFACTURING_SERVICE_OTHER: Literal["manufacturing_service_other"] = (
    Industry.MANUFACTURING_SERVICE_OTHER.value
)

# Back-compat alias — some tests had a `INDUSTRY_MANUFACTURING_RETAIL` name.
# Keep pointing at the canonical "manufacturing_service" string so legacy
# references still resolve while the canonical enum drives truth.
INDUSTRY_MANUFACTURING_RETAIL: Literal["manufacturing_service"] = (
    INDUSTRY_MANUFACTURING_SERVICE
)
INDUSTRY_MIXED: Literal["manufacturing_service_other"] = (
    INDUSTRY_MANUFACTURING_SERVICE_OTHER
)

# Tenant.industry column CheckConstraint enum values (db_models.py:62-64).
INDUSTRY_VALUES: tuple[str, ...] = tuple(member.value for member in Industry)

# Verification item status — passed / failed only.
# `skipped` is excluded because applies_to=False rules are silently
# omitted from the `verifications[]` array (Story 4.3 AC #2 AD-12 ordering
# invariant + AC #3 envelope shape).
VerificationStatusLiteral = Literal["passed", "failed"]


@dataclass(frozen=True)
class RuleInput:
    """Frozen rule input — pure data, no I/O.

    Story 4.3 (Task 1.2) — every field is serializable + deterministic.
    `tenant_id`, `period_key`, `trace_id` are identifiers for audit log
    carriers (consumed by `VerificationRunner`, NOT by rule kernels).
    """

    monthly_input: MonthlyInput
    baseline: Baseline
    calc_result: CalcResult
    industry: str  # Tenant.industry enum value (one of INDUSTRY_VALUES)
    tenant_id: UUID
    period_key: str
    trace_id: str


@dataclass(frozen=True)
class VerificationItem:
    """Frozen rule output — pure data, no I/O.

    `code`: V1/V4/V7/V8 discriminator (PRD §11).
    `status`: passed/failed.
    `message_ko`: Korean human-readable diagnostic. Used by the
        `CalcResponse.verdict` envelope. NOT localized dynamically —
        deterministic for V8 regression.
    `details`: rule-specific payload (V1: delta_krw, V4: 4_elements,
        V7: pools/activities, V8: placeholder contract flags).
    """

    code: Literal["V1", "V4", "V7", "V8"]
    status: VerificationStatusLiteral
    message_ko: str
    details: dict[str, Any]


class VerificationRule(Protocol):
    """AD-5 pure verification rule protocol.

    Story 4.3 AC #2: every rule kernel implements this 3-method contract.
    Implementations live in `apps/api/modules.m3_calculate.services.rules.*`
    (one module per rule — flat module layout for import-linter testability).
    """

    @property
    def name(self) -> str:
        """Rule discriminator — 'V1' / 'V4' / 'V7' / 'V8'."""
        ...

    def applies_to(self, *, industry: str) -> bool:
        """Return True iff this rule fires for the given industry.

        Per AD-12:
        - V1, V4, V8: True for all industries (universal invariants).
        - V7: True only for `service` (ABC 무결성). Manufacturing tenants
          have BOM 100% verified by Story 2.2 gate (separate step).

        Rules with applies_to=False are silently omitted from the
        `verifications[]` envelope (Story 4.3 AC #2).
        """
        ...

    def check(self, input: RuleInput) -> VerificationItem:
        """Pure rule evaluation. No I/O. Same input → same output (AD-5)."""
        ...
