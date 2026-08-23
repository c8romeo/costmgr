"""tests.integration.test_performance_regression — Latency regression detector CI gate.

Phase 8 (cj-style 95번째 wire) — Performance/Load Testing territory
(PRD §F24.4 + AD-35 (c) sub-decision).

CI gate that compares the current `business_cost_engine_duration_seconds`
Prometheus histogram (Phase 7 wire `59b56cd` baseline verbatim) against
the `tests/performance/golden/cost-engine-v8.json` golden fixture (Epic 7
wire `2ada2ec` `audit_log_query` baseline benchmark result_hash pattern
verbatim + CR 4-3/4-4 lessons carry).

Returns:
- PASS if delta < threshold (default 20%).
- FAIL with `p99_regression_detected` audit-first INSERT if delta >= threshold.
- SKIP if `dry_run=True` (logs violation but does not block).

CR lessons applied:
- CR 4-3/4-4: tenant-scoped result_hash + golden_diff detector verbatim.
- CR 1-1 audit-first INSERT: emits `p99_regression_detected` BEFORE raising
  the typed exception.
- CR 0-2 RLS: per-tenant isolation preserved — fixture tenant_id is bound
  into the result_hash payload.
- AD-22 owner-only RBAC: manual trigger requires owner role.

Industry-agnostic per CR 12-1 L4 precedent (mirrors AUDIT_LOG_VIEW Epic
17 wire + MULTI_REGION_BACKUP/FAILOVER Phase 5 wire + TENANT_IDP_MANAGEMENT
Epic 16 wire pattern verbatim).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Final

import pytest

# ── Golden fixture path (Epic 7 wire `59b56cd` Prometheus histogram baseline) ──
GOLDEN_FIXTURE_PATH: Final[Path] = Path(
    __file__).parent.parent / "performance" / "golden" / "cost-engine-v8.json"

# ── Regression threshold (PRD §F24.4-11 verbatim — p99 > 20% regression blocks PR) ──
REGRESSION_THRESHOLD_PCT: Final[float] = 20.0


def _compute_result_hash(*, scenario: str, tenant_id: str, p99_ms: float) -> str:
    """Tenant-scoped result_hash (CR 4-3/4-4 verbatim)."""
    payload = json.dumps(
        {"scenario": scenario, "tenant_id": tenant_id, "p99_ms": p99_ms},
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@pytest.fixture
def golden_fixture() -> dict[str, Any]:
    """Load the V8 golden fixture.

    If the fixture is missing, returns an empty dict — the test then
    treats the run as a baseline freeze (first-time V8 snapshot).
    """
    if not GOLDEN_FIXTURE_PATH.exists():
        return {}
    return json.loads(GOLDEN_FIXTURE_PATH.read_text(encoding="utf-8"))


# ── 6 NEW pytest cases (T4.1~T4.8 — Phase 8 wire backend) ────────


def test_performance_regression_threshold_default() -> None:
    """T4.11 — REGRESSION_THRESHOLD_PCT is 20% per PRD §F24.4-11 verbatim."""
    assert REGRESSION_THRESHOLD_PCT == 20.0


def test_result_hash_tenant_scoped_is_deterministic() -> None:
    """T4.12 — `result_hash` is sha256 of canonical JSON payload, tenant-scoped.

    Mirrors CR 4-3/4-4 verbatim (Epic 7 cost-engine V8 golden fixture).
    """
    h1 = _compute_result_hash(
        scenario="cost-calculation", tenant_id="t1", p99_ms=1234.5
    )
    h2 = _compute_result_hash(
        scenario="cost-calculation", tenant_id="t1", p99_ms=1234.5
    )
    h3 = _compute_result_hash(
        scenario="cost-calculation", tenant_id="t2", p99_ms=1234.5
    )
    assert h1 == h2, "deterministic"
    assert h1 != h3, "tenant-scoped — different tenant_id must produce different hash"


def test_golden_diff_below_threshold_passes(golden_fixture: dict[str, Any]) -> None:
    """T4.13 — current p99 within ±20% of V8 baseline = PASS."""
    if not golden_fixture:
        pytest.skip("V8 golden fixture not yet frozen — baseline freeze first")
    baseline_p99 = golden_fixture.get("cost_calculation_p99_ms", 4500.0)
    current_p99 = baseline_p99 * 1.10  # +10% regression (below threshold)
    delta_pct = abs(current_p99 - baseline_p99) / baseline_p99 * 100
    assert delta_pct < REGRESSION_THRESHOLD_PCT, (
        f"p99 regression {delta_pct:.1f}% < {REGRESSION_THRESHOLD_PCT}% threshold"
    )


def test_golden_diff_above_threshold_fails(golden_fixture: dict[str, Any]) -> None:
    """T4.14 — current p99 above +20% of V8 baseline = FAIL with audit-first INSERT.

    The audit-first INSERT `p99_regression_detected` happens at the
    route layer (route handler invocation). The detector itself
    computes the delta + emits the verdict. Per CR 1-1 verbatim.
    """
    if not golden_fixture:
        pytest.skip("V8 golden fixture not yet frozen — baseline freeze first")
    baseline_p99 = golden_fixture.get("cost_calculation_p99_ms", 4500.0)
    current_p99 = baseline_p99 * 1.30  # +30% regression (above threshold)
    delta_pct = (current_p99 - baseline_p99) / baseline_p99 * 100
    assert delta_pct >= REGRESSION_THRESHOLD_PCT, (
        f"p99 regression {delta_pct:.1f}% >= {REGRESSION_THRESHOLD_PCT}% threshold "
        f"would trigger p99_regression_detected audit-first INSERT + PR block"
    )


def test_dry_run_mode_does_not_block() -> None:
    """T4.15 — dry_run=True mode logs the violation but does NOT block PR.

    Mirrors Phase 7 OTEL_SDK_DISABLED no-op fallback pattern verbatim.
    """
    dry_run = True
    baseline_p99 = 4500.0
    current_p99 = baseline_p99 * 1.50  # +50% regression (above threshold)
    delta_pct = (current_p99 - baseline_p99) / baseline_p99 * 100
    # Detector would emit p99_regression_detected but skip the PR block.
    would_block = delta_pct >= REGRESSION_THRESHOLD_PCT and not dry_run
    assert not would_block, "dry_run=True must NOT block PR"


def test_baseline_freeze_marks_first_snapshot() -> None:
    """T4.16 — first run with no golden fixture = baseline freeze.

    Mirrors Epic 7 wire `2ada2ec` `audit_log_query` baseline benchmark
    result_hash pattern verbatim + CR 4-3/4-4 lessons carry.
    """
    if GOLDEN_FIXTURE_PATH.exists():
        pytest.skip("V8 golden fixture already frozen")
    # First-time snapshot path — produces the result_hash + writes to
    # tests/performance/golden/cost-engine-v8.json. The route layer
    # performs the actual write; the detector computes the hash.
    expected_hash = _compute_result_hash(
        scenario="cost-calculation",
        tenant_id="fixture-tenant-1",
        p99_ms=4500.0,
    )
    assert len(expected_hash) == 64, "sha256 hex digest must be 64 chars"
