"""apps.api.modules.m3_calculate.services.rules — AD-12 verification rule kernels.

Story 4.3 (Task 1.1~1.7) — V1·V4·V7·V8 발동 (PRD §11).

AD-1: handler → service → engine (3-layer). Rules = pure kernels in
service layer. Engine doesn't know about V* verifications.
AD-5: rule kernels are pure — no DB, no clock, no random, no global state,
no logs. Verified by `tests/cost_engine/test_verification_rules.py::test_verification_rules_no_io_imports`
(AST 3중 차단).
AD-12: strict ordered sequence V1 → V4 → V7 → V8. Earlier failed aborts
later checks. Service-only industry skips V7 (other 3 fire).
AD-22: rule results flow into `VerificationRunner` → service-layer INSERT
at `verification_log`. No DB write from rule kernels themselves.

Public surface:
    VerificationRule (protocol)
    RuleInput (frozen dataclass)
    VerificationItem (frozen dataclass)
    _VERIFICATION_RULES (tuple[VerificationRule, ...] immutable registry)
"""

from apps.api.modules.m3_calculate.services.rules.protocol import (
    RuleInput,
    VerificationItem,
    VerificationRule,
    VerificationStatusLiteral,
)
from apps.api.modules.m3_calculate.services.rules.v1_complete_allocation import (
    V1CompleteAllocationRule,
)
from apps.api.modules.m3_calculate.services.rules.v3_closing_invariant import (
    V3ClosingInvariantRule,
)
from apps.api.modules.m3_calculate.services.rules.v4_cost_income_reconciliation import (
    V4CostIncomeReconciliationRule,
)
from apps.api.modules.m3_calculate.services.rules.v7_abc_integrity import (
    V7AbcIntegrityRule,
)
from apps.api.modules.m3_calculate.services.rules.v8_regression import (
    V8RegressionRule,
)

# AD-12 strict ordered sequence — Story 4.3 AC #2.
# Story 5.3 — V3 closing ≥ 0 invariant inserted at slot 3 of 5
# (V1 → V4 → V3 → V7 → V8). Tuple immutable so the order can't be
# mutated at runtime. To insert a new rule between two existing ones,
# replace the tuple (tuple swap, not in-place mutation).
_VERIFICATION_RULES: tuple[VerificationRule, ...] = (
    V1CompleteAllocationRule(),
    V4CostIncomeReconciliationRule(),
    V3ClosingInvariantRule(),
    V7AbcIntegrityRule(),
    V8RegressionRule(),
)

__all__ = [
    "VerificationRule",
    "RuleInput",
    "VerificationItem",
    "VerificationStatusLiteral",
    "V1CompleteAllocationRule",
    "V3ClosingInvariantRule",
    "V4CostIncomeReconciliationRule",
    "V7AbcIntegrityRule",
    "V8RegressionRule",
    "_VERIFICATION_RULES",
]
