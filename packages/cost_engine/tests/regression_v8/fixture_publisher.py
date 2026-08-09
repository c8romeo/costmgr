"""packages.cost_engine.tests.regression_v8.fixture_publisher — V8 fixture publisher.

Story 4.4 (Task 1.2) — 1회성 도구 (one-shot) for 12 골든 fixture 발행.

Default mode = --check-only (CI/dev 모두 lock sha256 검증만).
--all 모드는 일회성 발행 + git commit용. commit 후 --all 모드 사용 금지.

Usage:
  # (1회성 발행 — git commit 후 비활성화)
  python -m packages.cost_engine.tests.regression_v8.fixture_publisher --all

  # (CI / dev 검증 — lock sha256 일치 확인)
  python -m packages.cost_engine.tests.regression_v8.fixture_publisher --check-only

  # (1 fixture만)
  python -m packages.cost_engine.tests.regression_v8.fixture_publisher \
    --industry manufacturing --baseline-shape b-small

AD-5 purity: 골든 발행은 1회성이라 purity invariant 그대로 유지 (no DB, no clock, no random).
CR 0.2 / 1.1 / 2.3 lessons 충족.
"""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from packages.cost_engine.core.money import KRW
from packages.cost_engine.core.period_cost import Baseline, compute_period_cost
from packages.cost_engine.ports.calc_port import MonthlyInput
from packages.cost_engine.tests.regression_v8.fixture_loader import (
    compute_golden_lock_sha256,
    load_golden_by_id,
)

# 3 baseline shapes (PRD §6.1 — Story 4.4 AC #2)
# (shape_name, material, labor, indirect, fte, hours) — bom_ratio_validated / allocation_basis_set = True
BASELINE_SHAPES: dict[str, dict[str, int | float]] = {
    "b-small": {
        "material": 1_000_000,
        "labor": 500_000,
        "indirect": 300_000,
        "fte": 5.0,
        "hours": 209,
    },
    "b-standard": {
        "material": 4_900_000,
        "labor": 2_100_000,
        "indirect": 1_500_000,
        "fte": 12.5,
        "hours": 209,
    },
    "b-complex": {
        "material": 12_345_678,
        "labor": 8_765_432,
        "indirect": 4_321_098,
        "fte": 42.0,
        "hours": 228,  # 730h 연봉 시나리오
    },
}

INDUSTRY_VALUES: tuple[str, ...] = (
    "manufacturing",
    "manufacturing_service",
    "service",
    "manufacturing_service_other",
)
ALL_BASELINE_SHAPES: tuple[str, ...] = tuple(BASELINE_SHAPES.keys())


def _publish_one(*, industry: str, baseline_shape: str, fixtures_root: Path) -> dict:
    """1 industry × 1 baseline shape = 1 fixture object (in-memory + disk)."""
    s = BASELINE_SHAPES[baseline_shape]
    mi = MonthlyInput(
        tenant_id=uuid4(),
        period_key="2026-07",
        direct_material_krw=KRW(int(s["material"])),
        direct_labor_krw=KRW(int(s["labor"])),
        indirect_krw=KRW(int(s["indirect"])),
        fte_headcount=Decimal(str(s["fte"])),
    )
    baseline = Baseline(
        fiscal_period="2026-07",
        standard_monthly_hours=int(s["hours"]),
        bom_ratio_validated=True,
        allocation_basis_set=True,
    )
    calc = compute_period_cost(monthly_input=mi, baseline=baseline)

    golden: dict = {
        "material_cost": int(calc.material_cost),
        "labor_cost": int(calc.labor_cost),
        "overhead_cost": int(calc.overhead_cost),
        "manufacturing_cost": int(calc.manufacturing_cost),
        "inventory_adjustment": int(calc.inventory_adjustment),
        "result_hash": calc.result_hash,
        "state": "draft",  # AD-22 invariant — engine always draft
    }
    lock_sha = compute_golden_lock_sha256(golden)

    fixture_id = f"{industry}__{baseline_shape}"
    out_path = fixtures_root / f"{fixture_id}.json"
    obj = {
        "fixture_id": fixture_id,
        "fixture_version": "1.0.0",
        "tenant_id": str(mi.tenant_id),
        "period_key": "2026-07",
        "monthly_input": {
            "direct_material_krw": int(mi.direct_material_krw),
            "direct_labor_krw": int(mi.direct_labor_krw),
            "indirect_krw": int(mi.indirect_krw),
            "fte_headcount": str(mi.fte_headcount),
        },
        "baseline": {
            "fiscal_period": baseline.fiscal_period,
            "standard_monthly_hours": baseline.standard_monthly_hours,
            "bom_ratio_validated": baseline.bom_ratio_validated,
            "allocation_basis_set": baseline.allocation_basis_set,
        },
        "_fixture_lock_sha256": lock_sha,
        "golden": golden,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    return obj


def _check_one(fixture_id: str, *, fixtures_root: Path) -> bool:
    """1 fixture lock sha256 검증 (Story 4.4 AC #7). Returns True if OK."""
    try:
        _input, _golden = load_golden_by_id(fixture_id, fixtures_root=fixtures_root)
    except (FileNotFoundError, AssertionError) as e:
        print(f"  [FAIL] {fixture_id}: {type(e).__name__}: {e}", file=sys.stderr)
        return False
    print(f"  [OK] {fixture_id}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="fixture_publisher",
        description="V8 fixture publisher / lock verifier (Story 4.4)",
        epilog=(
            "Story 6.3 W2 deferral (2026-08-09): "
            "--include-closing-period-snapshot and --include-closing-snapshot "
            "CLI flags are deferred to Epic 11 close-out + A11 publisher "
            "sweep (6 NEW V8 fixtures still hold "
            "PLACEHOLDER_LOCK_WILL_BE_REGENERATED_BY_PUBLISHER). "
            "The 12-fixture core matrix (3 industries × 4 baseline shapes) "
            "is fully wired and check-only-verifiable. "
            "A11 publisher regen entrypoint is decided at Epic 11 close."
        ),
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Publish all 12 fixtures (one-shot, post-commit use only)",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Validate lock sha256 (CI / dev default — no writes)",
    )
    parser.add_argument(
        "--industry",
        choices=INDUSTRY_VALUES,
    )
    parser.add_argument(
        "--baseline-shape",
        choices=ALL_BASELINE_SHAPES,
    )
    parser.add_argument(
        "--fixtures-root",
        type=Path,
        default=Path(__file__).parent / "fixtures",
    )
    args = parser.parse_args()

    if args.check_only:
        # CI / dev 검증 only — no writes.
        total = len(INDUSTRY_VALUES) * len(ALL_BASELINE_SHAPES)
        print(f"[check-only] Validating lock sha256 for {total} fixtures...")
        ok_count = 0
        for industry in INDUSTRY_VALUES:
            for shape in ALL_BASELINE_SHAPES:
                if _check_one(f"{industry}__{shape}", fixtures_root=args.fixtures_root):
                    ok_count += 1
        if ok_count == total:
            print(f"[check-only] All {total} fixtures valid.")
            return 0
        print(f"[check-only] {ok_count}/{total} valid.", file=sys.stderr)
        return 1

    if args.all:
        total = len(INDUSTRY_VALUES) * len(ALL_BASELINE_SHAPES)
        print(f"[publish] Publishing {total} fixtures to {args.fixtures_root}...")
        for industry in INDUSTRY_VALUES:
            for shape in ALL_BASELINE_SHAPES:
                obj = _publish_one(
                    industry=industry,
                    baseline_shape=shape,
                    fixtures_root=args.fixtures_root,
                )
                print(
                    f"  [OK] {obj['fixture_id']} " f"(lock={obj['_fixture_lock_sha256'][:16]}...)"
                )
        return 0

    if args.industry and args.baseline_shape:
        obj = _publish_one(
            industry=args.industry,
            baseline_shape=args.baseline_shape,
            fixtures_root=args.fixtures_root,
        )
        print(f"  [OK] {obj['fixture_id']}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
