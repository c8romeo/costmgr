"""packages.cost_engine.tests.regression_v8.fixture_loader — V8 fixture loader.

Story 4.4 (Task 2) — pure helper for V8 1원 단위 회귀 골든 fixture 로드.

AD-5 purity invariant: no DB, no clock, no random, no I/O (filesystem read OK
because fixture_loader is the boundary that reads JSON from `fixtures/`).
sha256 deterministic — same content → same lock.

Public API:
  - `compute_golden_lock_sha256(golden)` — sha256 deterministic lock
  - `load_golden_by_id(fixture_id, *, fixtures_root=None)` — 1 fixture load + lock verify
  - `load_golden_for_industry(industry, *, fixtures_root=None)` — 1 industry 모든 fixture
  - `select_golden_for_input(*, industry, monthly_input, ...)` — 입력 → canonical fixture

Per cr-4-3-lessons (F-4): STORY_4_4_FILL_POINT marker 위치 보존. fill 진입점.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, TypedDict

from packages.cost_engine.tests.regression_v8 import (
    V8_GOLDEN_OUTPUT_STRUCTURE,
    V8_INPUT_SCHEMA,
)


# Mirrored structural shapes (TypedDict는 runtime dict와 동일).
class V8InputDict(TypedDict, total=False):
    fixture_id: str
    fixture_version: str
    tenant_id: str
    period_key: str
    monthly_input: dict[str, Any]
    baseline: dict[str, Any]
    _fixture_lock_sha256: str
    golden: dict[str, Any]


class V8GoldenOutputDict(TypedDict, total=False):
    material_cost: int
    labor_cost: int
    overhead_cost: int
    manufacturing_cost: int
    inventory_adjustment: int
    result_hash: str
    state: str


def _validate_v8_input_shape(input_dict: dict[str, Any]) -> None:
    """Manual V8_INPUT_SCHEMA validation (AD-5 purity: no jsonschema)."""
    required = set(V8_INPUT_SCHEMA["required"])
    missing = required - set(input_dict.keys())
    assert not missing, (
        f"V8Input missing required keys: {sorted(missing)}. "
        f"Found keys: {sorted(input_dict.keys())}."
    )

    monthly_input = input_dict.get("monthly_input", {})
    mi_required = set(V8_INPUT_SCHEMA["properties"]["monthly_input"]["required"])
    mi_missing = mi_required - set(monthly_input.keys())
    assert not mi_missing, f"monthly_input missing required keys: {sorted(mi_missing)}"

    for k in ("direct_material_krw", "direct_labor_krw", "indirect_krw"):
        v = monthly_input.get(k)
        assert isinstance(v, int), f"monthly_input.{k} must be int, got {type(v).__name__}"

    fte = monthly_input.get("fte_headcount")
    assert isinstance(
        fte, str | int | float
    ), f"monthly_input.fte_headcount must be str (Decimal) or numeric, got {type(fte).__name__}"


def _validate_v8_golden_shape(golden: dict[str, Any]) -> None:
    """Manual V8_GOLDEN_OUTPUT_STRUCTURE validation."""
    required = set(V8_GOLDEN_OUTPUT_STRUCTURE["required"])
    missing = required - set(golden.keys())
    assert not missing, f"V8GoldenOutput missing required keys: {sorted(missing)}"

    for k in ("material_cost", "labor_cost", "overhead_cost", "manufacturing_cost"):
        v = golden.get(k)
        assert isinstance(v, int), f"golden.{k} must be int (KRW 정수), got {type(v).__name__}"
        assert v >= 0, f"golden.{k} must be ≥ 0 (V8_INPUT_SCHEMA minimum=0)"

    inv_adj = golden.get("inventory_adjustment")
    assert isinstance(
        inv_adj, int
    ), f"golden.inventory_adjustment must be int, got {type(inv_adj).__name__}"

    rh = golden.get("result_hash")
    assert isinstance(rh, str)
    assert len(rh) == 64, f"golden.result_hash must be 64-char hex, got len={len(rh)}"
    assert all(
        c in "0123456789abcdef" for c in rh.lower()
    ), f"golden.result_hash must be hex, got {rh[:16]}…"

    state = golden.get("state")
    assert (
        state == "draft"
    ), f"golden.state must be 'draft' (AD-22 — engine returns draft ONLY), got {state!r}"


def compute_golden_lock_sha256(golden: V8GoldenOutputDict) -> str:
    """Deterministic lock sha256 — 골든 변경 감지 (Story 4.4 AC #7).

    AD-16 determinism: sha256(stable_json(golden)) — sort_keys=True 로 key order
    locked. 같은 content → 같은 hash. 변경 시 lock mismatch.
    """
    blob = json.dumps(golden, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _default_fixtures_root() -> Path:
    return Path(__file__).parent / "fixtures"


def load_golden_by_id(
    fixture_id: str,
    *,
    fixtures_root: Path | None = None,
) -> tuple[V8InputDict, V8GoldenOutputDict]:
    """1 fixture load + lock sha256 검증.

    Returns: (input_dict, golden_output)
    Raises:
      FileNotFoundError: fixture file not found
      AssertionError: shape mismatch OR lock sha256 mismatch
    """
    if fixtures_root is None:
        fixtures_root = _default_fixtures_root()
    path = fixtures_root / f"{fixture_id}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"V8 fixture not found: {path}. "
            f"Expected 12 fixtures total (4 industries × 3 baseline shapes)."
        )
    obj = json.loads(path.read_text(encoding="utf-8"))
    _validate_v8_input_shape(obj)
    _validate_v8_golden_shape(obj["golden"])
    expected = compute_golden_lock_sha256(obj["golden"])
    actual = obj.get("_fixture_lock_sha256")
    assert actual == expected, (
        f"V8 lock sha256 mismatch for {fixture_id}: expected={expected}, actual={actual}. "
        f"Re-run fixture_publisher.py to regenerate (Story 4.4)."
    )
    return obj, obj["golden"]


def load_golden_for_industry(
    industry: str,
    *,
    fixtures_root: Path | None = None,
) -> list[V8InputDict]:
    """1 industry의 모든 fixture 반환 (matrix cover 검증 / Epic 11 fallback)."""
    if fixtures_root is None:
        fixtures_root = _default_fixtures_root()
    paths = sorted(fixtures_root.glob(f"{industry}__*.json"))
    fixtures = []
    for p in paths:
        obj = json.loads(p.read_text(encoding="utf-8"))
        _validate_v8_input_shape(obj)
        _validate_v8_golden_shape(obj["golden"])
        fixtures.append(obj)
    return fixtures


def select_golden_for_input(
    *,
    industry: str,
    monthly_input: Any,  # packages.cost_engine.ports.calc_port.MonthlyInput
    fixtures_root: Path | None = None,
) -> V8InputDict | None:
    """산업 + monthly_input KRW 합계 + fte_headcount → canonical fixture 추론 (deterministic).

    Strategy (PRD §6.1 baseline shape 분포 + Story 4.4 AC #2):
      - monthly_total ≤ 2_000_000 AND fte ≤ 5  → b-small
      - monthly_total ≤ 10_000_000 AND fte ≤ 20 → b-standard
      - else (large/complex)                    → b-complex

    Returns None if no fixture found (Epic 11 reversal fallback trigger).
    """
    if fixtures_root is None:
        fixtures_root = _default_fixtures_root()
    monthly_total = (
        int(monthly_input.direct_material_krw)
        + int(monthly_input.direct_labor_krw)
        + int(monthly_input.indirect_krw)
    )
    fte = float(monthly_input.fte_headcount)
    if monthly_total <= 2_000_000 and fte <= 5:
        shape = "b-small"
    elif monthly_total <= 10_000_000 and fte <= 20:
        shape = "b-standard"
    else:
        shape = "b-complex"
    path = fixtures_root / f"{industry}__{shape}.json"
    if not path.exists():
        return None
    obj = json.loads(path.read_text(encoding="utf-8"))
    _validate_v8_input_shape(obj)
    return obj


__all__ = [
    "V8InputDict",
    "V8GoldenOutputDict",
    "compute_golden_lock_sha256",
    "load_golden_by_id",
    "load_golden_for_industry",
    "select_golden_for_input",
]
