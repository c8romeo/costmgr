"""tests.integration.test_completion_consistency — cross-language completion parity.

Story 1.2 — Task 7.5. `compute_completion()` lives in Python
(`packages/services/m0_onboarding/settings_completion.py`); the TypeScript
frontend has the equivalent logic inline inside `useSettingsCompletion`
consumers. The two MUST agree on `is_complete` and `missing` for every
legal input shape.

This file exercises the **Python** truth source. The TypeScript mirror test
lives in `apps/web/__tests__/computeCompletion.test.ts` (deferred — Vitest
not installed in MVP; tracked under Story 0.5).

The CI gate for full parity runs both Python + TypeScript via the same
parametrized input set. For now this file documents the canonical input
matrix so the TS test (when added) can mirror the parameter list.
"""

from __future__ import annotations

import pytest

from packages.services.m0_onboarding.settings_completion import compute_completion


@pytest.mark.parametrize(
    ("industry", "onboarding", "counts", "expected_missing_count", "expected_complete"),
    [
        # 1. fully empty — all four top-level fields missing
        (None, {}, {"direct_indirect": 0, "fixed_variable": 0, "drivers": 0}, 6, False),
        # 2. fiscal year only set (manufacturing skips drivers → 4 missing)
        (
            "manufacturing",
            {"fiscal_year_start": "2026-01"},
            {"direct_indirect": 0, "fixed_variable": 0, "drivers": 0},
            4,
            False,
        ),
        # 3. all top-level set, criteria missing (manufacturing skips drivers)
        (
            "manufacturing",
            {
                "fiscal_year_start": "2026-01",
                "currency": "KRW",
                "language": "ko-KR",
            },
            {"direct_indirect": 0, "fixed_variable": 0, "drivers": 0},
            2,
            False,
        ),
        # 4. full manufacturing set
        (
            "manufacturing",
            {
                "fiscal_year_start": "2026-01",
                "currency": "KRW",
                "language": "ko-KR",
                "allocation_criteria": {
                    "direct_indirect": {"count": 5},
                    "fixed_variable": {"count": 5},
                },
            },
            {"direct_indirect": 5, "fixed_variable": 5, "drivers": 0},
            0,
            True,
        ),
        # 5. service — drivers required
        (
            "service",
            {
                "fiscal_year_start": "2026-01",
                "currency": "KRW",
                "language": "ko-KR",
                "allocation_criteria": {
                    "direct_indirect": {"count": 5},
                    "fixed_variable": {"count": 5},
                },
            },
            {"direct_indirect": 5, "fixed_variable": 5, "drivers": 0},
            1,
            False,
        ),
    ],
)
def test_python_compute_completion_matrix(
    industry: str | None,
    onboarding: dict,
    counts: dict,
    expected_missing_count: int,
    expected_complete: bool,
) -> None:
    """Canonical input matrix — TypeScript test (apps/web) mirrors this."""
    result = compute_completion(industry, onboarding, counts)  # type: ignore[arg-type]
    assert len(result.missing) == expected_missing_count, (
        f"expected {expected_missing_count} missing, got {result.missing}"
    )
    assert result.is_complete is expected_complete