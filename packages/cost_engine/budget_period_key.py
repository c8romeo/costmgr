"""packages.cost_engine.budget_period_key — Story 8.1 Budget Period Key pure kernel.

Pure-Python, stdlib-only helpers consumed by:
- `apps/api/modules/m8_budget/services/budget_scenario_service.py`
  (T3 service layer — create_scenario / get_scenario dispatch)

AD-1 / AD-5 / AD-11 binding: pure-Python, stdlib-only, NO sqlalchemy,
NO DB import (cost_engine layer rule). The service layer passes
existing_count (int) as argument; this kernel owns the V8 determinism
+ scenario lock logic + budget period key derivation/parsing.

PRD §F8.1 (1차 시나리오 1개만 허용):
- Virtual budget period key = `YYYY-MM#B<n>` (e.g., `2026-07#B1`)
- 1차 MVP = `scenario_index=1` only (PRD §15 NON-GOAL #2)
- 2nd scenario creation → `ScenarioLimitExceededError` (HTTP 409 envelope)

AD-24 Period Keys (`docs/conventions.md#§6-Period-Keys-(AD-24)`):
- Real (실측 월) = `YYYY-MM` (예: `2026-07`)
- Virtual (예산 시뮬레이션) = `YYYY-MM#B<n>` (예: `2026-07#B1`)
- `#B<n>` = 같은 real 월 안에서 여러 가상 예산을 구분
- 비교 시 `period_key` 전체를 문자열로 비교
- **M8만 virtual key 발급, M11 close는 fiscal key만 잠금**

V8 determinism: `compute_budget_scenario_hash` 는 hashlib.sha256
결정론 digest — 동일 입력 → byte-identical hash (Epic 4 baseline +
7-1/7-2 패턴 동일).

A19 cohesion pattern 3번째 검증: `budget_period_key.py` 는
`packages/cost_engine/cvp.py` (7-1) + `packages/cost_engine/projection.py`
(7-2) 와 surface 분리 — concern 별도 (period key derivation + scenario
lock 은 simulation/budget concern).
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Final

# ── Constants ────────────────────────────────────────────────
# AD-24 real fiscal period pattern (Story 4-2 verbatim).
REAL_PERIOD_KEY_PATTERN: Final[str] = r"^\d{4}-(0[1-9]|1[0-2])$"

# AD-24 virtual budget period pattern (Story 8.1 신규 — M8 only).
# Real fiscal key (`2026-07`) 는 invalid — virtual only.
# group(1) = YYYY, group(2) = MM, group(3) = scenario_index
VIRTUAL_BUDGET_PERIOD_KEY_PATTERN: Final[str] = (
    r"^(\d{4})-(0[1-9]|1[0-2])#B([1-9]\d*)$"
)

# 1차 MVP scenario 한도 (PRD §F8.1 verbatim + §15 NON-GOAL #2).
# scenario_index=1 only (2nd scenario = `scenario_index=2` 는 honestly DEFER
# to Story 8-2 DEFER (b) — trigger: ≥5 테넌트 요청 시).
MVP_SCENARIO_INDEX: Final[int] = 1
MVP_MAX_SCENARIOS_PER_TENANT: Final[int] = 1

# Scenario limit Korean message SSOT (PRD §F8.1 verbatim — CR 12-5 D-14 envelope).
# main.py handler → HTTP 409 SCENARIO_LIMIT_EXCEEDED.
SCENARIO_LIMIT_EXCEEDED_MESSAGE_KO: Final[str] = (
    "1차 MVP는 시나리오 1개만 지원합니다 (2차 예정)"
)

# Hash prefix for compute_budget_scenario_hash (V8 determinism trace).
SCENARIO_HASH_PREFIX: Final[str] = "sha256:"

# ── Frozen dataclasses ───────────────────────────────────────
@dataclass(frozen=True, slots=True)
class BudgetPeriodKeyParts:
    """Parsed virtual budget period key parts (AD-24 §6.2).

    `real_period_key` = `YYYY-MM` (e.g., `2026-07`)
    `scenario_index` = int >= 1 (1차 MVP = 1)
    `scenario_suffix` = literal `#B<n>` (e.g., `#B1`)
    """

    real_period_key: str
    scenario_index: int
    scenario_suffix: str


@dataclass(frozen=True, slots=True)
class BudgetScenario:
    """Frozen budget scenario entity (service layer boundary).

    `id` = UUID v7 (CR 1-1 wire pattern — service layer inject)
    `tenant_id` = UUID (RLS AD-3)
    `period_key` = virtual `YYYY-MM#B<n>` (8-1 SSOT)
    `real_period_key` = `YYYY-MM` (real fiscal key)
    `scenario_index` = int >= 1
    `created_by` = UUID (user)
    `created_at_kst` = ISO 8601 (Postgres TIMESTAMPTZ → str, 결정론)
    """

    id: str
    tenant_id: str
    period_key: str
    real_period_key: str
    scenario_index: int
    created_by: str
    created_at_kst: str


# ── Typed exceptions ────────────────────────────────────────
class ScenarioLimitExceededError(Exception):
    """PRD §F8.1 verbatim + §15 NON-GOAL #2.

    1차 MVP = 1개 시나리오 only. existing_count >= 1 시 raise.
    2차 multi-scenario 비교는 Story 8-2 DEFER (b) honestly.
    """

    def __init__(
        self,
        message: str = SCENARIO_LIMIT_EXCEEDED_MESSAGE_KO,
        *,
        existing_count: int | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.existing_count = existing_count


class InvalidVirtualBudgetPeriodKeyError(ValueError):
    """Invalid period_key format (real fiscal key 또는 malformed string).

    AD-24 §6.2 virtual pattern: `^\\d{4}-(0[1-9]|1[0-2])#B([1-9]\\d*)$`.
    M8 only — M11 close의 fiscal key (`2026-07`) 는 invalid.

    Attributes:
      period_key — 원본 입력 (HTTP envelope details echo용)
      expected_pattern — 정규식 패턴 (HTTP envelope details echo용)
    """

    def __init__(
        self,
        message: str,
        *,
        period_key: str,
        expected_pattern: str,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.period_key = period_key
        self.expected_pattern = expected_pattern


# ── Pattern pre-compiled regex ───────────────────────────────
# AD-5 purity — stdlib-only `re` compile at module import time.
_REAL_PERIOD_KEY_RE: Final[re.Pattern[str]] = re.compile(REAL_PERIOD_KEY_PATTERN)
_VIRTUAL_BUDGET_PERIOD_KEY_RE: Final[re.Pattern[str]] = re.compile(
    VIRTUAL_BUDGET_PERIOD_KEY_PATTERN
)


# ── Pure functions ───────────────────────────────────────────
def derive_budget_period_key(
    *, real_period_key: str, scenario_index: int = MVP_SCENARIO_INDEX
) -> str:
    """AD-24 §6.2 virtual budget period key derivation.

    `f"{real_period_key}#B{scenario_index}"` (예: `"2026-07"` + `1` →
    `"2026-07#B1"`).

    Pure-Python, stdlib-only, deterministic (AD-5 + AD-11).

    Edge cases (ValueError raise):
      - `real_period_key` invalid pattern → "real_period_key must match YYYY-MM"
      - `scenario_index <= 0` → "scenario_index must be >= 1"
      - `scenario_index > 1` (1차 MVP 한도) → "MVP supports scenario_index=1 only"

    V8 determinism: 100회 동일 입력 → 100회 byte-identical 문자열.
    """
    if not isinstance(real_period_key, str):
        raise ValueError(
            f"real_period_key must be str, got {type(real_period_key).__name__}"
        )
    if not _REAL_PERIOD_KEY_RE.match(real_period_key):
        raise ValueError("real_period_key must match YYYY-MM")
    if not isinstance(scenario_index, int):
        raise ValueError(
            f"scenario_index must be int, got {type(scenario_index).__name__}"
        )
    if scenario_index <= 0:
        raise ValueError("scenario_index must be >= 1")
    if scenario_index > MVP_SCENARIO_INDEX:
        # 1차 MVP 한도 — 2차 multi-scenario는 8-2 DEFER (b).
        raise ValueError(
            "MVP supports scenario_index=1 only; 2차 예정"
        )
    return f"{real_period_key}#B{scenario_index}"


def parse_virtual_budget_period_key(*, period_key: str) -> BudgetPeriodKeyParts:
    """AD-24 §6.2 virtual budget period key parser.

    `period_key` = `YYYY-MM#B<n>` (virtual pattern).
    Real fiscal key (`2026-07`) 는 invalid — M8 virtual only.

    Pure-Python, stdlib-only, deterministic.

    Edge cases (ValueError raise):
      - `period_key` invalid pattern → "period_key must match YYYY-MM#B<n>"
        (real fiscal key 거부 + malformed string 거부)
      - `scenario_index > 1` (1차 MVP 한도) → "MVP supports scenario_index=1 only"

    Returns:
      BudgetPeriodKeyParts (frozen dataclass).
    """
    if not isinstance(period_key, str):
        raise InvalidVirtualBudgetPeriodKeyError(
            f"period_key must be str, got {type(period_key).__name__}",
            period_key=str(period_key),
            expected_pattern=VIRTUAL_BUDGET_PERIOD_KEY_PATTERN,
        )
    match = _VIRTUAL_BUDGET_PERIOD_KEY_RE.match(period_key)
    if match is None:
        raise InvalidVirtualBudgetPeriodKeyError(
            "period_key must match YYYY-MM#B<n>",
            period_key=period_key,
            expected_pattern=VIRTUAL_BUDGET_PERIOD_KEY_PATTERN,
        )
    # Pattern: `^(\d{4})-(0[1-9]|1[0-2])#B([1-9]\d*)$`
    # group(1) = YYYY (4 digits), group(2) = MM (01-12), group(3) = scenario_index.
    year = match.group(1)
    month = match.group(2)
    real_period_key = f"{year}-{month}"
    scenario_index = int(match.group(3))
    if scenario_index > MVP_SCENARIO_INDEX:
        raise InvalidVirtualBudgetPeriodKeyError(
            "MVP supports scenario_index=1 only; 2차 예정",
            period_key=period_key,
            expected_pattern=VIRTUAL_BUDGET_PERIOD_KEY_PATTERN,
        )
    scenario_suffix = f"#B{scenario_index}"
    return BudgetPeriodKeyParts(
        real_period_key=real_period_key,
        scenario_index=scenario_index,
        scenario_suffix=scenario_suffix,
    )


def validate_scenario_uniqueness(*, existing_count: int) -> None:
    """PRD §F8.1 verbatim + §15 NON-GOAL #2 scenario lock (1차 MVP = 1개).

    `existing_count == 0` → return None (1st scenario 생성 허용).
    `existing_count >= 1` → `ScenarioLimitExceededError` raise.

    Pure-Python, stdlib-only, no DB / no clock (AD-5 + AD-11).
    Service layer (`budget_scenario_service.count_scenarios`) 가
    existing_count 조회 후 delegate.

    Raises:
      ScenarioLimitExceededError with `existing_count` attribute (CR 12-5 D-14
        envelope main.py handler → HTTP 409 SCENARIO_LIMIT_EXCEEDED).
    """
    if not isinstance(existing_count, int):
        raise ValueError(
            f"existing_count must be int, got {type(existing_count).__name__}"
        )
    if existing_count < 0:
        raise ValueError("existing_count must be >= 0")
    if existing_count >= MVP_MAX_SCENARIOS_PER_TENANT:
        raise ScenarioLimitExceededError(
            SCENARIO_LIMIT_EXCEEDED_MESSAGE_KO,
            existing_count=existing_count,
        )


def compute_budget_scenario_hash(*, scenario: BudgetScenario) -> str:
    """V8 determinism hash for budget scenario (Epic 4 baseline + 7-1/7-2 pattern).

    `hashlib.sha256(repr(scenario).encode()).hexdigest()` — 16바이트 hexdigest
    (32 chars), `sha256:` prefix.

    Pure-Python, stdlib-only, deterministic (AD-5 + NFR16 + AD-11).

    Note: `BudgetScenario` is `frozen=True, slots=True` — repr은
    결정론 (dataclass auto-generated repr).

    Returns:
      `f"sha256:{32-char-hexdigest}"`.
    """
    if not isinstance(scenario, BudgetScenario):
        raise ValueError(
            f"scenario must be BudgetScenario, got {type(scenario).__name__}"
        )
    digest = hashlib.sha256(repr(scenario).encode()).hexdigest()
    return f"{SCENARIO_HASH_PREFIX}{digest}"
