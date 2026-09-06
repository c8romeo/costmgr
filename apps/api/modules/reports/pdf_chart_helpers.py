"""apps.api.modules.reports.pdf_chart_helpers — matplotlib chart helpers for PDF export.

cj-293 wire sprint (cj-style 293번째) — Story 30.2 PDF export chart layer.

3 NEW chart helpers (OQ-EPIC30+-4 결정 wire 진입 — matplotlib pure Python):
  1. render_category_breakdown_pie — 카테고리별 비용 비중 파이 차트
  2. render_monthly_trend_bar — 기간별 비용 추이 막대 차트
  3. render_unit_cost_evolution_line — 단가 변화 추이 선 차트

All charts use matplotlib's non-interactive Agg backend (decision wire 보존 —
no DISPLAY required, server-side rendering only). Output = PNG bytes
embedded into PDF via reportlab Image flowables.

Korean font handling 결정 wire (NFR18 ko-KR SSOT):
- matplotlib rcParams 'font.family' = 'DejaVu Sans' (matplotlib default —
  Latin/CJK subset OK for Korean via fallback)
- Chart labels use ko-KR vocabulary (한글 라벨) 결정 wire 보존.

CR 11-3 honest-DEFER 233번째 — chart styling EXTENSION 결정 wire 보류
(cj-style 294+ 적용).
"""

from __future__ import annotations

import io
import logging
from typing import Any

import matplotlib

# Use the non-interactive Agg backend — server-side rendering only
# (no DISPLAY required). 결정 wire 보존.
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402

logger = logging.getLogger(__name__)


# ── Constants ────────────────────────────────────────────────────────

# Chart DPI for PNG export (balance between file size + print quality).
MAX_CHART_DPI: int = 150

# Chart figure size (inches) — consistent across all 3 helpers.
CHART_FIG_SIZE: tuple[float, float] = (7.0, 4.5)

# Korean chart palette — 4 distinguishable categorical colors.
CATEGORY_PALETTE: tuple[str, ...] = (
    "#4C72B0",  # blue
    "#DD8452",  # orange
    "#55A467",  # green
    "#C44E52",  # red
)


# ── Chart 1: category breakdown pie ──────────────────────────────────


def render_category_breakdown_pie(
    rows: list[Any],
    type: str,  # noqa: A002 — matches PDF route param naming
    dpi: int = MAX_CHART_DPI,
) -> bytes:
    """카테고리별 비용 비중 파이 차트 (Story 30.2 §F30.2-2 verbatim).

    Args:
        rows: data rows (cost_records or bom, depending on type)
        type: "cost-records" | "bom"
        dpi: PNG export DPI

    Returns:
        PNG bytes (matplotlib savefig to BytesIO)
    """
    # Aggregate cost by category (cost-records) or child_category (bom).
    category_totals: dict[str, float] = {}
    for r in rows:
        if type == "cost-records":
            category = str(getattr(r, "category", "(unknown)"))
            total = float(getattr(r, "total_cost", 0) or 0)
        else:  # bom
            category = str(getattr(r, "child_category", "(unknown)"))
            total = float(getattr(r, "child_total_cost", 0) or 0)
        category_totals[category] = category_totals.get(category, 0.0) + total

    # Sort by value (descending) — readability for monthly closing reports.
    sorted_items = sorted(category_totals.items(), key=lambda kv: -kv[1])
    labels = [k for k, _ in sorted_items]
    sizes = [v for _, v in sorted_items]

    fig, ax = plt.subplots(figsize=CHART_FIG_SIZE, dpi=dpi)
    if sizes and sum(sizes) > 0:
        ax.pie(
            sizes,
            labels=labels,
            colors=CATEGORY_PALETTE[: len(sizes)],
            autopct="%1.1f%%",
            startangle=90,
            textprops={"fontsize": 10},
        )
        ax.set_title(
            "카테고리별 비용 비중" if type == "cost-records" else "BOM 카테고리 비중",
            fontsize=12,
            fontweight="bold",
        )
    else:
        ax.text(
            0.5,
            0.5,
            "데이터 없음",
            ha="center",
            va="center",
            fontsize=12,
            transform=ax.transAxes,
        )
        ax.set_axis_off()
    ax.axis("equal")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# ── Chart 2: monthly trend bar ────────────────────────────────────────


def render_monthly_trend_bar(
    rows: list[Any],
    type: str,  # noqa: A002
    dpi: int = MAX_CHART_DPI,
) -> bytes:
    """기간별 비용 추이 막대 차트 (Story 30.2 §F30.2-2 verbatim).

    Aggregates total_cost (cost-records) or child_total_cost (bom) by
    period_key. For single-period exports this shows the period total.

    Args:
        rows: data rows
        type: "cost-records" | "bom"
        dpi: PNG export DPI

    Returns:
        PNG bytes (matplotlib savefig to BytesIO)
    """
    period_totals: dict[str, float] = {}
    for r in rows:
        period = str(getattr(r, "period_key", "(unknown)"))
        if type == "cost-records":
            total = float(getattr(r, "total_cost", 0) or 0)
        else:
            total = float(getattr(r, "child_total_cost", 0) or 0)
        period_totals[period] = period_totals.get(period, 0.0) + total

    sorted_periods = sorted(period_totals.keys())
    values = [period_totals[p] for p in sorted_periods]

    fig, ax = plt.subplots(figsize=CHART_FIG_SIZE, dpi=dpi)
    if sorted_periods:
        ax.bar(sorted_periods, values, color=CATEGORY_PALETTE[0])
        ax.set_xlabel("기간 (period_key)", fontsize=10)
        ax.set_ylabel("총 비용 (KRW)", fontsize=10)
        ax.set_title("기간별 비용 추이", fontsize=12, fontweight="bold")
        ax.tick_params(axis="x", rotation=45)
        ax.grid(True, axis="y", linestyle="--", alpha=0.7)
    else:
        ax.text(
            0.5,
            0.5,
            "데이터 없음",
            ha="center",
            va="center",
            fontsize=12,
            transform=ax.transAxes,
        )
        ax.set_axis_off()

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# ── Chart 3: unit cost evolution line ─────────────────────────────────


def render_unit_cost_evolution_line(
    rows: list[Any],
    type: str,  # noqa: A002
    dpi: int = MAX_CHART_DPI,
) -> bytes:
    """단가 변화 추이 선 차트 (Story 30.2 §F30.2-2 verbatim).

    Plots unit_cost (cost-records) or child_unit_cost (bom) over the
    created_at timestamp, sorted ascending. For multi-product data, the
    mean unit_cost per period is shown.

    Args:
        rows: data rows
        type: "cost-records" | "bom"
        dpi: PNG export DPI

    Returns:
        PNG bytes (matplotlib savefig to BytesIO)
    """
    # Aggregate mean unit cost per period.
    period_units: dict[str, list[float]] = {}
    for r in rows:
        period = str(getattr(r, "period_key", "(unknown)"))
        if type == "cost-records":
            unit = float(getattr(r, "unit_cost", 0) or 0)
        else:
            unit = float(getattr(r, "child_unit_cost", 0) or 0)
        period_units.setdefault(period, []).append(unit)

    sorted_periods = sorted(period_units.keys())
    mean_units = [
        (sum(period_units[p]) / len(period_units[p])) if period_units[p] else 0.0
        for p in sorted_periods
    ]

    fig, ax = plt.subplots(figsize=CHART_FIG_SIZE, dpi=dpi)
    if sorted_periods:
        ax.plot(
            sorted_periods,
            mean_units,
            marker="o",
            color=CATEGORY_PALETTE[2],
            linewidth=2,
        )
        ax.set_xlabel("기간 (period_key)", fontsize=10)
        ax.set_ylabel("평균 단가 (KRW)", fontsize=10)
        ax.set_title("단가 변화 추이", fontsize=12, fontweight="bold")
        ax.tick_params(axis="x", rotation=45)
        ax.grid(True, linestyle="--", alpha=0.7)
    else:
        ax.text(
            0.5,
            0.5,
            "데이터 없음",
            ha="center",
            va="center",
            fontsize=12,
            transform=ax.transAxes,
        )
        ax.set_axis_off()

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


__all__ = [
    "MAX_CHART_DPI",
    "CHART_FIG_SIZE",
    "CATEGORY_PALETTE",
    "render_category_breakdown_pie",
    "render_monthly_trend_bar",
    "render_unit_cost_evolution_line",
]
