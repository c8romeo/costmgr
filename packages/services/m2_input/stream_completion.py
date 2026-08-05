"""packages.services.m2_input.stream_completion — Six-stream completion + FTE math.

Story 3.1 — Task 1.

Pure-Python, stdlib-only module. NO DB, NO clock, NO random. AD-1 / AD-5
binding: this is the canonical completion-decision function consumed by
the API service layer + the frontend TS mirror (`apps/web/lib/m2-input-completion.ts`).
Drift is caught by `tests/integration/test_m2_input_label_consistency.py`.

The function answers:
- "Given the tenant's current row counts per stream, which tabs still have
  a yellow dot?" → `compute_stream_completion`
- "Given the row counts + industry, are all required streams filled?" →
  `is_all_streams_complete` (drives the [계산] button enable gate)
- "Given the [인원] tab inputs, what is the read-only FTE display?" →
  `format_fte_headcount` + `compute_fte_wage_krw` (Story 3.2 hook surface)

Industry-conditional rules (PRD §8.M2(b)):
- manufacturing (①) + ③ + ④: production tab is REQUIRED (6 streams)
- service (②): production tab is HIDDEN (5 streams)

Korean labels (Decision §2): PRD §8.M2(b) canonical set:
    주문 / 생산 / 판매 / 구매 / 경비 / 인원
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Final

from packages.services.m0_onboarding.industry_menu import Industry

# Public constants — Korean labels for the tab headers + completion tooltip.
# Frontend imports the mirror from TS (`apps/web/lib/m2-input-completion.ts`).
# Update both sides together; drift is caught by `test_m2_input_label_consistency.py`.
STREAM_LABELS_KO: Final[dict[str, str]] = {
    "orders": "주문",
    "production": "생산",
    "sales": "판매",
    "purchases": "구매",
    "expenses": "경비",
    "labor": "인원",
}

# Tab order — PRD §8.M2(b) sequence. Frontend uses this for the horizontal
# tab strip layout. MUST match TS mirror's `STREAM_ORDER`.
STREAM_ORDER: Final[tuple[str, ...]] = (
    "orders",
    "production",
    "sales",
    "purchases",
    "expenses",
    "labor",
)

# ── Industry → visible streams map ─────────────────────────────
# Service industry hides the [생산] tab (no manufacturing capability).
# Manufacturing + hybrids show all 6. The `Capability` enum carries the
# gate (`MONTHLY_INPUT_PRODUCTION`), this map is the UI projection.
STREAMS_FOR_INDUSTRY: Final[dict[Industry, frozenset[str]]] = {
    Industry.MANUFACTURING: frozenset(
        {"orders", "production", "sales", "purchases", "expenses", "labor"}
    ),
    Industry.SERVICE: frozenset({"orders", "sales", "purchases", "expenses", "labor"}),
    Industry.MANUFACTURING_SERVICE: frozenset(
        {"orders", "production", "sales", "purchases", "expenses", "labor"}
    ),
    Industry.MANUFACTURING_SERVICE_OTHER: frozenset(
        {"orders", "production", "sales", "purchases", "expenses", "labor"}
    ),
}


@dataclass(frozen=True)
class StreamCompletionStatus:
    """Per-stream completion — one for each visible stream.

    `row_count` is the number of `monthly_input_rows` for this stream
    in the current period. `completed` is the boolean driving the yellow
    dot (False ⇒ yellow, True ⇒ green).
    """

    stream: str
    completed: bool
    row_count: int
    label_ko: str


@dataclass(frozen=True)
class MonthlyCompletionStatus:
    """Aggregate of `compute_stream_completion` + `is_all_streams_complete`.

    Mirrors `m0_onboarding.settings_completion.CompletionStatus` shape so
    the frontend completion-gate UI is symmetric across M0 + M2.
    """

    industry: Industry
    streams: dict[str, StreamCompletionStatus]  # keyed by stream name
    is_complete: bool
    missing: list[str]  # Korean labels, ordered per PRD §8.M2(b)
    capability_mask: list[str]  # sorted stream names visible for this industry


# ── Public API ────────────────────────────────────────────────
def compute_stream_completion(
    industry: Industry,
    rows_by_stream: dict[str, int] | None,
) -> MonthlyCompletionStatus:
    """Pure completion-decision function.

    Args:
        industry: The tenant's industry (None is treated as SERVICE — the
            most restrictive visibility — so a tenant without a chosen
            industry sees 5 tabs, not 6).
        rows_by_stream: Per-stream row counts, e.g.
            `{"orders": 3, "sales": 0, "labor": 2}`. Streams with no
            row count default to 0. None is treated as {}.

    Returns:
        `MonthlyCompletionStatus` — the frontend renders the yellow dot +
        the [계산] button state + the missing-stream tooltip directly
        from this object.

    Anti-pattern guards (spec §Anti-pattern prevention):
    - No DB calls. No clock reads.
    - No side effects. Safe to call from request handlers + tests.
    """
    rows = dict(rows_by_stream or {})

    # Visibility is industry-conditional. If `industry` is unrecognized
    # (e.g. legacy tenant), default to SERVICE (most restrictive).
    visible = STREAMS_FOR_INDUSTRY.get(industry, STREAMS_FOR_INDUSTRY[Industry.SERVICE])

    streams: dict[str, StreamCompletionStatus] = {}
    for stream in STREAM_ORDER:
        if stream not in visible:
            continue
        count = int(rows.get(stream, 0))
        label = STREAM_LABELS_KO[stream]
        streams[stream] = StreamCompletionStatus(
            stream=stream,
            completed=count > 0,
            row_count=count,
            label_ko=label,
        )

    is_complete = all(s.completed for s in streams.values())

    missing: list[str] = []
    for stream in STREAM_ORDER:
        if stream not in visible:
            continue
        status = streams[stream]
        if not status.completed:
            missing.append(status.label_ko)

    return MonthlyCompletionStatus(
        industry=industry,
        streams=streams,
        is_complete=is_complete,
        missing=missing,
        capability_mask=sorted(visible),
    )


def is_all_streams_complete(
    industry: Industry,
    rows_by_stream: dict[str, int] | None,
) -> bool:
    """Convenience — returns just the aggregate boolean.

    Equivalent to `compute_stream_completion(industry, rows_by_stream).is_complete`.
    Kept as a separate function for the [계산] gate test (focused, no
    nested object assertion).
    """
    return compute_stream_completion(industry, rows_by_stream).is_complete


# ── FTE math (Story 3.2 hook surface, read-only in Story 3.1) ──
def format_fte_headcount(
    workers: int,
    days_per_worker: int,
    workdays_in_month: int = 22,
) -> Decimal:
    """Compute FTE headcount for the [인원] tab read-only display.

    Formula: `workers × days_per_worker / workdays_in_month`, rounded to
    2 decimal places with `ROUND_HALF_EVEN` (banker's rounding) so the
    result is identical on Python + TS sides (TS `Math.round` is
    half-away-from-zero; we deliberately diverge to banker's rounding
    here for cross-language parity — TS mirror implements the same
    rule explicitly).

    Args:
        workers: Number of 일용직 workers (≥ 0).
        days_per_worker: Number of days each worker worked in the period (≥ 0).
        workdays_in_month: PRD default = 22. Override per period if the
            tenant's `payroll.workdays_in_month` setting is set (Story 3.2
            may extend; Story 3.1 uses the default).

    Returns:
        Decimal rounded to 2 places. `Decimal("0.00")` if either input is 0.

    Why Decimal (not float): AD-8 monetary parity. Even though FTE itself
    is not money, downstream `compute_fte_wage_krw` multiplies it with a
    KRW amount; precision loss would propagate.
    """
    if workers <= 0 or days_per_worker <= 0 or workdays_in_month <= 0:
        return Decimal("0.00")
    raw = Decimal(workers) * Decimal(days_per_worker) / Decimal(workdays_in_month)
    return raw.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)


def compute_fte_wage_krw(
    fte_headcount: Decimal,
    monthly_salary_basis_krw: int,
) -> int:
    """Compute read-only FTE wage for the [인원] tab display.

    Formula: `int(round(fte_headcount × monthly_salary_basis_krw))`,
    rounded to the nearest integer KRW (banker's rounding via Decimal).

    Args:
        fte_headcount: Output of `format_fte_headcount` (already 2 dp).
        monthly_salary_basis_krw: Tenant's `tenant_settings.payroll.monthly_salary_basis_krw`
            if set; else PRD default = 2,500,000. The caller (API service
            layer) is responsible for fetching the override or falling
            back. This pure function takes the integer it receives.

    Returns:
        `int` KRW. `0` if either input is 0 / negative.
    """
    if fte_headcount <= 0 or monthly_salary_basis_krw <= 0:
        return 0
    result = (fte_headcount * Decimal(monthly_salary_basis_krw)).quantize(
        Decimal("1"), rounding=ROUND_HALF_EVEN
    )
    return int(result)
