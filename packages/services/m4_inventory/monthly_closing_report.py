"""packages.services.m4_inventory.monthly_closing_report — Story 6.2 pure kernel.

Monthly Closing Report = closing 시점 closing_snapshot ledger events +
inventory_ledger 전체 + fiscal_period_snapshots 3-source read-only
aggregate (PRD §F5 + §F5.2 + §V4 + §A11 4-layer defense).

Pure-Python, stdlib-only helpers consumed by:
- `apps/api/modules/m4_inventory/services/monthly_closing_report_service.py`
  (T3 service layer — MonthlyClosingReportService.get_monthly_closing_report +
  audit_trail + verify_monthly_closing_report_v4)
- `apps/web/lib/monthly-closing-report.ts` (TS mirror — AC #2)
- `tests/services/m4_inventory/test_monthly_closing_report.py` (T9.1 — 18 cases)

AD-1 / AD-5 / AD-11 binding: pure-Python, stdlib-only, no DB, no clock,
no random. Drift between Python and TS caught by
`tests/integration/test_monthly_closing_report_label_consistency.py`
(NEW 6-2 — T9.7 AD-15 §11 cross-language parity 9 cases).

Closing report view mode classification (PRD §F5):
- CLOSING_REPORT_READY: 3 source 모두 >= 1 → 마감 보고서 fully populated
  (KPI 박스 4개 + Table + Chart + audit-trail 모두 표시).
- CLOSING_REPORT_PARTIAL: 일부 source 만 >= 1 → 일부 빈 source 표시 +
  "잠시 후 갱신" sonner toast (자동 retry cj-style default OQ1=(a)).
- CLOSING_REPORT_EMPTY: 3 source 모두 0건 → "마감 데이터 없음" Alert +
  Table/Chart 비노출 + audit-trail empty.

Korean message SSOT (AD-15 §11):
- `MONTHLY_CLOSING_REPORT_TITLE_KO` mirrors
  `apps/web/lib/monthly-closing-report.ts::formatMonthlyClosingReportTitleKo`.
- `MONTHLY_CLOSING_REPORT_EMPTY_KO` mirrors
  `apps/web/lib/monthly-closing-report.ts::formatMonthlyClosingReportEmptyKo`.
- `CURRENCY_PAIR_DISPLAY_KO_FORMAT` mirrors
  `apps/web/lib/monthly-closing-report.ts::formatCurrencyPairDisplayKo`.

KRW/USD dual display (AD-8 + PRD §F5.2):
- KRW = BIGINT (정수) — DB 그대로.
- USD = NUMERIC(18,2) (소수 2자리) — `closing_qty_krw / exchange_rate`
  USD 환산 (banker's rounding via `QTY_QUANTUM` from `inventory_projection`).
- 환율 source = `tenant_settings.baseline.currency_pair.usd_krw_rate`
  (PRD §F5.2 SSOT — 한국은행 명시, OQ4 cj-style default (a)).

A8 inline projection deprecation timeline:
- 6-2 wire 시점 (현재): inline projection 보존 상태로 wire (1 epic
  maintenance window 진행 중), monthly_closing_report aggregator는
  ledger aggregate + 5-2 wire + 6-1 wire + 4-2 wire 4-source read-only join.
- Epic 6 close-out 시점에 fold-in vs deprecate 결정 필수
  (A8 결정 — Epic 5 retro §7 A8).
"""

from __future__ import annotations

import uuid
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Final, NamedTuple

from packages.services.m2_input.inventory_projection import QTY_QUANTUM

# ── Constants ────────────────────────────────────────────────
# Korean message SSOT (AD-15 §11 parity with TS
# `formatMonthlyClosingReportTitleKo` + `formatMonthlyClosingReportEmptyKo`).
# Drift caught by integration test
# `tests/integration/test_monthly_closing_report_label_consistency.py`.
MONTHLY_CLOSING_REPORT_TITLE_KO: Final[str] = "월 마감 보고서"
MONTHLY_CLOSING_REPORT_EMPTY_KO: Final[str] = "마감 데이터 없음"

# Currency pair display format (PRD §F5.2 + OQ4 cj-style default (a)).
# 한국은행 = KRW/USD 환율 SSOT source.
CURRENCY_PAIR_DISPLAY_KO_FORMAT: Final[str] = "1 USD = {rate_krw} KRW ({source_ko} {rate_as_of})"

# Closing report view mode classification 3 codes (PRD §F5 + §V4 + §A11).
REPORT_VIEW_MODE_READY: Final[str] = "CLOSING_REPORT_READY"
REPORT_VIEW_MODE_PARTIAL: Final[str] = "CLOSING_REPORT_PARTIAL"
REPORT_VIEW_MODE_EMPTY: Final[str] = "CLOSING_REPORT_EMPTY"

REPORT_VIEW_MODES: Final[frozenset[str]] = frozenset(
    {
        REPORT_VIEW_MODE_READY,
        REPORT_VIEW_MODE_PARTIAL,
        REPORT_VIEW_MODE_EMPTY,
    }
)

# USD precision (AD-8 monetary types — NUMERIC(18,2)).
USD_QUANTUM: Final[Decimal] = Decimal("0.01")

# Currency pair direction (PRD §F5.2 — USD → KRW). The `from_currency` is
# USD and `to_currency` is KRW (한국은행 USD/KRW 매매기준율).
CURRENCY_FROM_USD: Final[str] = "USD"
CURRENCY_TO_KRW: Final[str] = "KRW"


# ── MonthlyClosingReportError ─────────────────────────────────
class MonthlyClosingReportError(Exception):
    """Pure-kernel monthly closing report domain error.

    Distinct from service-layer typed exceptions (which carry HTTP
    envelope + audit-first semantics). This exception is raised by the
    pure kernel when invariants are violated at the domain level
    (e.g. invalid view_mode, non-finite qty, negative exchange_rate).
    NO HTTP mapping; service layer wraps with envelope details.
    """

    def __init__(
        self,
        *,
        message: str,
        error_code: str = "MONTHLY_CLOSING_REPORT_ERROR",
        period_key: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.period_key = period_key


# ── CurrencyPair ──────────────────────────────────────────────
class CurrencyPair(NamedTuple):
    """Pure-data currency pair for KRW/USD dual display (PRD §F5.2).

    AD-15: snake_case field names. Mirrors TS
    `apps/web/lib/monthly-closing-report.ts::CurrencyPair`.

    `rate` is `usd_krw_rate` (1 USD = X KRW, 한국은행 매매기준율).
    `rate_source_ko` = Korean source label (e.g. "한국은행").
    `rate_as_of` = ISO-8601 date string when the rate was sampled.

    Closed values: from_currency=USD, to_currency=KRW (OQ4 cj-style
    default (a) — 한국은행 SSOT).
    """

    from_currency: str
    to_currency: str
    rate: Decimal  # usd_krw_rate (KRW per 1 USD)
    rate_source_ko: str
    rate_as_of: str  # ISO-8601 date string


# ── ClosingSnapshotEventLite ──────────────────────────────────
class ClosingSnapshotEventLite(NamedTuple):
    """Pure-data closing_snapshot ledger event lite (per-product).

    Mirrors TS
    `apps/web/lib/l2-input-inventory-ledger.ts::ClosingSnapshotEvent`.
    Pure kernel does NOT carry the full 5-2 ClosingSnapshotEvent shape —
    only the fields needed for the closing report aggregator
    (product_id + closing_qty + finalized_at).
    """

    product_id: uuid.UUID
    closing_qty: Decimal
    finalized_at: str  # ISO-8601 UTC


# ── LedgerEventLite ───────────────────────────────────────────
class LedgerEventLite(NamedTuple):
    """Pure-data inventory_ledger event lite (per-product).

    Pure kernel lite — only product_id + event_type used for
    `closing_per_product.ledger_event_count` aggregate.
    """

    product_id: uuid.UUID
    event_type: str


# ── FiscalPeriodSnapshotLite ──────────────────────────────────
class FiscalPeriodSnapshotLite(NamedTuple):
    """Pure-data fiscal_period_snapshots lite (per-product).

    4-2 wire cost data source (PRD §6.1 — material_cost + labor_cost +
    overhead_cost + manufacturing_cost). Pure kernel lite — only
    product_id + engine_type used for the 4-source aggregate count.
    """

    product_id: uuid.UUID
    engine_type: str  # 'trad' filter applied by service layer


# ── OpeningInventoryEntryLite ─────────────────────────────────
class OpeningInventoryEntryLite(NamedTuple):
    """Pure-data monthly_input_periods.opening_inventory JSONB lite.

    5-1 wire JSONB column (PRD §F4.1 carry-over). Pure kernel lite —
    only product_id + opening_qty used for the per-product opening_qty
    in ClosingPerProductRow.
    """

    product_id: uuid.UUID
    opening_qty: Decimal


# ── ClosingPerProductRow ──────────────────────────────────────
class ClosingPerProductRow(NamedTuple):
    """Pure-data per-product closing report row.

    Mirrors TS
    `apps/web/lib/monthly-closing-report.ts::ClosingPerProductRow`.
    ClosingPerProductRow is the per-product closing report row used
    in the closing report Table (AC #2 — top 10 products by closing_qty).

    `closing_qty_krw`: KRW 정수 (DB BIGINT 그대로 — stringified for
    AD-15 §11 parity with TS Decimal).
    `closing_qty_usd`: USD 소수 2자리 (banker's rounding).
    `delta_krw`: closing_qty_krw - opening_qty_krw (KRW 정수).
    `delta_usd`: delta_krw 환산 USD (banker's rounding).
    """

    product_id: uuid.UUID
    product_code: str
    product_name: str
    opening_qty_krw: Decimal
    closing_qty_krw: Decimal
    closing_qty_usd: Decimal
    delta_krw: Decimal
    delta_usd: Decimal
    ledger_event_count: int


# ── MonthlyClosingReportAggregate ─────────────────────────────
class MonthlyClosingReportAggregate(NamedTuple):
    """Pure-data monthly closing report aggregate.

    Mirrors TS
    `apps/web/lib/monthly-closing-report.ts::MonthlyClosingReportResponse`
    (excluding V4 verdict + audit_trail which are service-layer computed).

    - `period_key`: 'YYYY-MM' AD-24 typed.
    - `view_mode`: REPORT_VIEW_MODES 3 codes.
    - `allowed`: True iff view_mode == CLOSING_REPORT_READY.
    - `closing_per_product`: list[ClosingPerProductRow] sorted by
      closing_qty DESC (OQ5 cj-style default (a) — 큰 액수 마감 우선).
    - `closing_snapshot_count`: closing_snapshot ledger events count
      (6-1 wire SSOT).
    - `ledger_event_count`: 전체 inventory_ledger event count (5-2 wire).
    - `fiscal_period_snapshot_count`: fiscal_period_snapshots
      engine_type='trad' count (4-2 wire).
    - `finalized_at`: ISO-8601 UTC (None when not finalized yet).
    - `currency_pair`: 환율 source (PRD §F5.2 SSOT).
    """

    period_key: str
    view_mode: str
    allowed: bool
    closing_per_product: list[ClosingPerProductRow]
    closing_snapshot_count: int
    ledger_event_count: int
    fiscal_period_snapshot_count: int
    finalized_at: str | None
    currency_pair: CurrencyPair | None


# ── compute_usd_from_krw ──────────────────────────────────────
def compute_usd_from_krw(
    amount_krw: Decimal,
    *,
    exchange_rate: Decimal,
) -> Decimal:
    """Pure USD 환산 — `amount_krw / exchange_rate` (PRD §F5.2).

    Banker's rounding (ROUND_HALF_EVEN) precision to 2 decimal places
    (USD_QUANTUM). Cross-language parity with TS Decimal helper
    `computeUsdFromKrw` (AD-15 §11).

    Args:
        amount_krw: KRW 정수 (Decimal). May be 0 or negative.
        exchange_rate: usd_krw_rate (1 USD = X KRW). MUST be > 0.

    Returns:
        Decimal — USD 환산 (소수 2자리).

    Raises:
        MonthlyClosingReportError: If exchange_rate <= 0 or
            non-finite (defense-in-depth — caller must validate 환율
            source before calling).
    """
    if not isinstance(amount_krw, Decimal):
        raise MonthlyClosingReportError(
            message=(
                f"amount_krw must be Decimal, got {type(amount_krw).__name__!r}"
            ),
            error_code="AMOUNT_KRW_MUST_BE_DECIMAL",
        )
    if not isinstance(exchange_rate, Decimal):
        raise MonthlyClosingReportError(
            message=(
                f"exchange_rate must be Decimal, got "
                f"{type(exchange_rate).__name__!r}"
            ),
            error_code="EXCHANGE_RATE_MUST_BE_DECIMAL",
        )
    if not exchange_rate.is_finite() or exchange_rate <= Decimal("0"):
        raise MonthlyClosingReportError(
            message=(
                f"exchange_rate must be > 0 and finite, got {exchange_rate!r}"
            ),
            error_code="INVALID_EXCHANGE_RATE",
        )
    if not amount_krw.is_finite():
        raise MonthlyClosingReportError(
            message=(
                f"amount_krw is non-finite {amount_krw!r}"
            ),
            error_code="NON_FINITE_AMOUNT_KRW",
        )
    return (amount_krw / exchange_rate).quantize(
        USD_QUANTUM, rounding=ROUND_HALF_EVEN
    )


# ── format_period_closing_krw_usd ─────────────────────────────
class PeriodClosingDisplay(NamedTuple):
    """Pure-data KRW/USD dual display formatting result.

    Mirrors TS `PeriodClosingDisplay` (AC #2 — closing report row
    KRW/USD dual display).
    """

    amount_krw: Decimal  # KRW 정수 (stringified for AD-15 §11)
    amount_usd: Decimal  # USD 소수 2자리


def format_period_closing_krw_usd(
    amount_krw: Decimal,
    *,
    currency_pair: CurrencyPair,
) -> PeriodClosingDisplay:
    """KRW/USD dual display formatting (AD-8 + PRD §F5.2).

    Args:
        amount_krw: KRW 정수 (Decimal). Banker's rounding via
            QTY_QUANTUM applied for deterministic parity.
        currency_pair: 환율 source (한국은행 SSOT).

    Returns:
        PeriodClosingDisplay — `amount_krw` (KRW 정수) + `amount_usd`
        (USD 소수 2자리 환산).

    Raises:
        MonthlyClosingReportError: If currency_pair invalid or
            amount_krw non-finite.
    """
    if currency_pair is None:
        raise MonthlyClosingReportError(
            message="currency_pair must not be None",
            error_code="CURRENCY_PAIR_REQUIRED",
        )
    # KRW quantization via QTY_QUANTUM (banker's rounding) for parity
    # with TS Decimal serialization.
    if not isinstance(amount_krw, Decimal):
        raise MonthlyClosingReportError(
            message=(
                f"amount_krw must be Decimal, got {type(amount_krw).__name__!r}"
            ),
            error_code="AMOUNT_KRW_MUST_BE_DECIMAL",
        )
    if not amount_krw.is_finite():
        raise MonthlyClosingReportError(
            message=(
                f"amount_krw is non-finite {amount_krw!r}"
            ),
            error_code="NON_FINITE_AMOUNT_KRW",
        )
    amount_krw_quantized = amount_krw.quantize(
        QTY_QUANTUM, rounding=ROUND_HALF_EVEN
    )
    amount_usd = compute_usd_from_krw(
        amount_krw_quantized,
        exchange_rate=currency_pair.rate,
    )
    return PeriodClosingDisplay(
        amount_krw=amount_krw_quantized,
        amount_usd=amount_usd,
    )


# ── classify_report_view_mode ─────────────────────────────────
def classify_report_view_mode(
    *,
    ledger_event_count: int,
    closing_snapshot_count: int,
    fiscal_period_snapshot_count: int,
) -> str:
    """Classify the monthly closing report view mode (PRD §F5).

    Classification rules (in priority order):
    1. 3 source 모두 0건 → CLOSING_REPORT_EMPTY (마감 데이터 없음).
    2. 3 source 모두 >= 1 → CLOSING_REPORT_READY (fully populated).
    3. 일부 source 만 >= 1 → CLOSING_REPORT_PARTIAL (잠시 후 갱신).

    Args:
        ledger_event_count: 전체 inventory_ledger event count (5-2 wire).
        closing_snapshot_count: closing_snapshot ledger events count
            (6-1 wire SSOT).
        fiscal_period_snapshot_count: fiscal_period_snapshots
            engine_type='trad' count (4-2 wire).

    Returns:
        str — one of REPORT_VIEW_MODES 3 codes.

    Raises:
        MonthlyClosingReportError: If any count is negative
            (defense-in-depth — caller must validate before calling).
    """
    for name, value in (
        ("ledger_event_count", ledger_event_count),
        ("closing_snapshot_count", closing_snapshot_count),
        ("fiscal_period_snapshot_count", fiscal_period_snapshot_count),
    ):
        if value < 0:
            raise MonthlyClosingReportError(
                message=(
                    f"{name} must be >= 0, got {value!r}"
                ),
                error_code="NEGATIVE_SOURCE_COUNT",
            )

    # Priority 1: all zero → EMPTY
    if (
        ledger_event_count == 0
        and closing_snapshot_count == 0
        and fiscal_period_snapshot_count == 0
    ):
        return REPORT_VIEW_MODE_EMPTY

    # Priority 2: all >= 1 → READY
    if (
        ledger_event_count >= 1
        and closing_snapshot_count >= 1
        and fiscal_period_snapshot_count >= 1
    ):
        return REPORT_VIEW_MODE_READY

    # Priority 3: partial
    return REPORT_VIEW_MODE_PARTIAL


# ── is_monthly_closing_report_allowed ─────────────────────────
def is_monthly_closing_report_allowed(mode: str) -> bool:
    """Return True iff `mode == REPORT_VIEW_MODE_READY`.

    Single source of truth for the closing-report gate (PRD §F5).
    Mirrors TS `isMonthlyClosingReportAllowed` in
    `apps/web/lib/monthly-closing-report.ts`.

    Args:
        mode: One of REPORT_VIEW_MODES 3 codes.

    Returns:
        bool — True iff mode is CLOSING_REPORT_READY.

    Raises:
        MonthlyClosingReportError: If mode is not in REPORT_VIEW_MODES
            (defense-in-depth — caller must classify first).
    """
    if mode not in REPORT_VIEW_MODES:
        raise MonthlyClosingReportError(
            message=(
                f"closing report view mode {mode!r} is not in the 3-code "
                f"set. Accepted: {sorted(REPORT_VIEW_MODES)}"
            ),
            error_code="INVALID_REPORT_VIEW_MODE",
        )
    return mode == REPORT_VIEW_MODE_READY


# ── format_currency_pair_display_ko ───────────────────────────
def format_currency_pair_display_ko(currency_pair: CurrencyPair) -> str:
    """Build the Korean currency pair display message (PRD §F5.2).

    Mirrors TS `formatCurrencyPairDisplayKo` for AD-15 §11 parity.
    Example: "1 USD = 1,320 KRW (한국은행 2026-07-25)".

    Args:
        currency_pair: 환율 source.

    Returns:
        str — Korean currency pair display message SSOT.
    """
    rate_krw_str = f"{int(currency_pair.rate):,}"
    return CURRENCY_PAIR_DISPLAY_KO_FORMAT.format(
        rate_krw=rate_krw_str,
        source_ko=currency_pair.rate_source_ko,
        rate_as_of=currency_pair.rate_as_of,
    )


# ── aggregate_monthly_closing_report ──────────────────────────
def aggregate_monthly_closing_report(
    closing_snapshot_events: list[ClosingSnapshotEventLite],
    ledger_events: list[LedgerEventLite],
    fiscal_period_snapshots: list[FiscalPeriodSnapshotLite],
    opening_inventory_entries: list[OpeningInventoryEntryLite],
    *,
    period_key: str,
    currency_pair: CurrencyPair | None,
    product_code_lookup: dict[uuid.UUID, tuple[str, str]] | None = None,
) -> MonthlyClosingReportAggregate:
    """Aggregate the monthly closing report from 4-source join (PRD §F5).

    Read-only aggregator — closing_snapshot_events + ledger_events +
    fiscal_period_snapshots + opening_inventory_entries 4-source join →
    MonthlyClosingReportAggregate.

    Pure kernel — no DB, no clock, no random. Caller passes:
    - 6-1 closing_snapshot ledger events (per-product closing_qty).
    - 5-2 inventory_ledger 전체 events (per-product ledger_event_count).
    - 4-2 fiscal_period_snapshots engine_type='trad' aggregate (per-product
      fiscal_period_snapshot_count).
    - 5-1 monthly_input_periods.opening_inventory JSONB (per-product
      opening_qty).
    - 환율 source (tenant_settings.baseline.currency_pair).

    Args:
        closing_snapshot_events: list[ClosingSnapshotEventLite]
            (6-1 wire SSOT — closing_snapshot ledger events).
        ledger_events: list[LedgerEventLite]
            (5-2 wire — inventory_ledger 전체 events).
        fiscal_period_snapshots: list[FiscalPeriodSnapshotLite]
            (4-2 wire — fiscal_period_snapshots engine_type='trad').
        opening_inventory_entries: list[OpeningInventoryEntryLite]
            (5-1 wire — monthly_input_periods.opening_inventory JSONB).
        period_key: 'YYYY-MM' AD-24 typed period key.
        currency_pair: 환율 source (PRD §F5.2 — None for service-only
            tenant or when 환율 not available).
        product_code_lookup: dict[product_id → (product_code,
            product_name)] (optional — caller-provided; defaults to
            placeholder strings when None).

    Returns:
        MonthlyClosingReportAggregate — closing report aggregate
        (read-only display payload).

    Raises:
        MonthlyClosingReportError: If period_key invalid or any input
            contains non-finite Decimal (defense-in-depth).
    """
    if not period_key or not isinstance(period_key, str):
        raise MonthlyClosingReportError(
            message=(
                f"period_key must be non-empty string, got {period_key!r}"
            ),
            error_code="INVALID_PERIOD_KEY",
            period_key=period_key,
        )

    # Per-product ledger_event_count aggregate (5-2 wire).
    ledger_event_count_per_product: dict[uuid.UUID, int] = {}
    for event in ledger_events:
        if not isinstance(event.product_id, uuid.UUID):
            raise MonthlyClosingReportError(
                message=(
                    f"ledger event product_id must be UUID, got "
                    f"{type(event.product_id).__name__!r}"
                ),
                error_code="INVALID_PRODUCT_ID",
                period_key=period_key,
            )
        ledger_event_count_per_product[event.product_id] = (
            ledger_event_count_per_product.get(event.product_id, 0) + 1
        )

    # Per-product closing_qty aggregate (6-1 wire).
    closing_qty_per_product: dict[uuid.UUID, Decimal] = {}
    finalized_at_per_product: dict[uuid.UUID, str] = {}
    for snapshot in closing_snapshot_events:
        if not isinstance(snapshot.closing_qty, Decimal):
            raise MonthlyClosingReportError(
                message=(
                    f"closing_snapshot closing_qty must be Decimal, got "
                    f"{type(snapshot.closing_qty).__name__!r}"
                ),
                error_code="QTY_MUST_BE_DECIMAL",
                period_key=period_key,
            )
        if not snapshot.closing_qty.is_finite():
            raise MonthlyClosingReportError(
                message=(
                    f"closing_snapshot closing_qty is non-finite "
                    f"{snapshot.closing_qty!r}"
                ),
                error_code="NON_FINITE_QTY",
                period_key=period_key,
            )
        closing_qty_per_product[snapshot.product_id] = (
            snapshot.closing_qty.quantize(QTY_QUANTUM, rounding=ROUND_HALF_EVEN)
        )
        finalized_at_per_product[snapshot.product_id] = snapshot.finalized_at

    # Per-product fiscal_period_snapshot_count aggregate (4-2 wire).
    fiscal_period_snapshot_count_per_product: dict[uuid.UUID, int] = {}
    for fps in fiscal_period_snapshots:
        if fps.engine_type != "trad":
            continue
        fiscal_period_snapshot_count_per_product[fps.product_id] = (
            fiscal_period_snapshot_count_per_product.get(fps.product_id, 0) + 1
        )

    # Per-product opening_qty aggregate (5-1 wire).
    opening_qty_per_product: dict[uuid.UUID, Decimal] = {}
    for entry in opening_inventory_entries:
        if not isinstance(entry.opening_qty, Decimal):
            raise MonthlyClosingReportError(
                message=(
                    f"opening_inventory opening_qty must be Decimal, got "
                    f"{type(entry.opening_qty).__name__!r}"
                ),
                error_code="QTY_MUST_BE_DECIMAL",
                period_key=period_key,
            )
        if not entry.opening_qty.is_finite():
            raise MonthlyClosingReportError(
                message=(
                    f"opening_inventory opening_qty is non-finite "
                    f"{entry.opening_qty!r}"
                ),
                error_code="NON_FINITE_QTY",
                period_key=period_key,
            )
        opening_qty_per_product[entry.product_id] = (
            entry.opening_qty.quantize(QTY_QUANTUM, rounding=ROUND_HALF_EVEN)
        )

    # Master product_id set (union of all 4 sources).
    all_product_ids: set[uuid.UUID] = set(closing_qty_per_product) | set(
        ledger_event_count_per_product
    ) | set(fiscal_period_snapshot_count_per_product) | set(
        opening_qty_per_product
    )

    # Build ClosingPerProductRow per product (KRW/USD dual display).
    rows: list[ClosingPerProductRow] = []
    for pid in sorted(all_product_ids, key=str):
        opening_qty_krw = opening_qty_per_product.get(pid, Decimal("0"))
        closing_qty_krw = closing_qty_per_product.get(pid, Decimal("0"))
        delta_krw = closing_qty_krw - opening_qty_krw

        if currency_pair is not None:
            closing_qty_usd = compute_usd_from_krw(
                closing_qty_krw,
                exchange_rate=currency_pair.rate,
            )
            delta_usd = compute_usd_from_krw(
                delta_krw,
                exchange_rate=currency_pair.rate,
            )
        else:
            # 환율 missing — fallback 0.00 (PRD §F5.2 SSOT — 환율 source
            # missing 시 read-only display fallback; service layer will
            # raise CLOSING_REPORT_KRW_USD_RATE_MISSING typed envelope).
            closing_qty_usd = Decimal("0.00")
            delta_usd = Decimal("0.00")

        # Product code/name lookup (caller-provided; defaults).
        if product_code_lookup and pid in product_code_lookup:
            code, name = product_code_lookup[pid]
        else:
            code = f"PRD-{str(pid)[:8]}"
            name = f"제품-{str(pid)[:8]}"

        rows.append(
            ClosingPerProductRow(
                product_id=pid,
                product_code=code,
                product_name=name,
                opening_qty_krw=opening_qty_krw,
                closing_qty_krw=closing_qty_krw,
                closing_qty_usd=closing_qty_usd,
                delta_krw=delta_krw,
                delta_usd=delta_usd,
                ledger_event_count=ledger_event_count_per_product.get(pid, 0),
            )
        )

    # Sort by closing_qty DESC (OQ5 cj-style default (a) — 큰 액수 마감 우선).
    rows.sort(key=lambda r: r.closing_qty_krw, reverse=True)

    # Counters for view_mode classification.
    closing_snapshot_count = len(closing_snapshot_events)
    ledger_event_count = len(ledger_events)
    fiscal_period_snapshot_count = len(
        [fps for fps in fiscal_period_snapshots if fps.engine_type == "trad"]
    )

    # View mode classification (PRD §F5).
    view_mode = classify_report_view_mode(
        ledger_event_count=ledger_event_count,
        closing_snapshot_count=closing_snapshot_count,
        fiscal_period_snapshot_count=fiscal_period_snapshot_count,
    )
    allowed = is_monthly_closing_report_allowed(view_mode)

    # Finalized_at (earliest closing_snapshot finalized_at — 6-1 wire).
    finalized_at: str | None = None
    if finalized_at_per_product:
        finalized_at = min(finalized_at_per_product.values())

    return MonthlyClosingReportAggregate(
        period_key=period_key,
        view_mode=view_mode,
        allowed=allowed,
        closing_per_product=rows,
        closing_snapshot_count=closing_snapshot_count,
        ledger_event_count=ledger_event_count,
        fiscal_period_snapshot_count=fiscal_period_snapshot_count,
        finalized_at=finalized_at,
        currency_pair=currency_pair,
    )


__all__ = [
    "CURRENCY_FROM_USD",
    "CURRENCY_PAIR_DISPLAY_KO_FORMAT",
    "CURRENCY_TO_KRW",
    "ClosingPerProductRow",
    "ClosingSnapshotEventLite",
    "CurrencyPair",
    "FiscalPeriodSnapshotLite",
    "LedgerEventLite",
    "MONTHLY_CLOSING_REPORT_EMPTY_KO",
    "MONTHLY_CLOSING_REPORT_TITLE_KO",
    "MonthlyClosingReportAggregate",
    "MonthlyClosingReportError",
    "OpeningInventoryEntryLite",
    "PeriodClosingDisplay",
    "QTY_QUANTUM",  # re-export for downstream consumers
    "REPORT_VIEW_MODES",
    "REPORT_VIEW_MODE_EMPTY",
    "REPORT_VIEW_MODE_PARTIAL",
    "REPORT_VIEW_MODE_READY",
    "USD_QUANTUM",
    "aggregate_monthly_closing_report",
    "classify_report_view_mode",
    "compute_usd_from_krw",
    "format_currency_pair_display_ko",
    "format_period_closing_krw_usd",
    "is_monthly_closing_report_allowed",
]
