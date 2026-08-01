"""tests.integration.test_m2_input_label_consistency — drift guard for m2_input labels.

Story 3.1 — Task 6.3. The canonical six-stream monthly input vocabulary
lives in TWO places:

  - `packages/services/m2_input/stream_completion.py` (Python, source of truth)
  - `apps/web/lib/menu-config.ts` (TypeScript mirror, `MONTHLY_INPUT_STREAM_*`)

This test parses the TypeScript file and asserts that:

  1. The set of MonthlyInputStream values matches.
  2. The Korean label dictionary matches (PRD §8.M2(b)).
  3. The per-industry visibility map matches (PRD §8.M2(b) — service hides production).

The test does NOT use Node / ts-node — just regex parsing, so it's
hermetic to the engine workspace (Epic 2 회고 W4 pattern).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from packages.services.m0_onboarding.industry_menu import Industry
from packages.services.m2_input.stream_completion import (
    STREAM_LABELS_KO,
    STREAMS_FOR_INDUSTRY,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
TS_PATH = REPO_ROOT / "apps" / "web" / "lib" / "menu-config.ts"


def _read_ts_source() -> str:
    """Read the TS file as text, stripping line + block comments.

    F-25 (Story 0.2 lesson): strip comments so doc-comment text doesn't
    satisfy label-matching regexes.
    """
    if not TS_PATH.exists():
        pytest.fail(
            f"Required TypeScript mirror not found at {TS_PATH}. "
            "Story 3.1 T5.5 must create this file alongside the Python module."
        )
    raw = TS_PATH.read_text(encoding="utf-8")
    no_block = re.sub(r"/\*.*?\*/", "", raw, flags=re.DOTALL)
    return re.sub(r"^\s*//.*$", "", no_block, flags=re.MULTILINE)


def _extract_ts_stream_values(ts_src: str) -> list[str]:
    """Extract the array literal under `export const MONTHLY_INPUT_STREAM_VALUES = [...]`."""
    m = re.search(
        r"export\s+const\s+MONTHLY_INPUT_STREAM_VALUES\s*=\s*\[(.*?)\]\s*as\s+const",
        ts_src,
        flags=re.DOTALL,
    )
    if not m:
        pytest.fail(
            "MONTHLY_INPUT_STREAM_VALUES declaration not found in TS mirror"
        )
    body = m.group(1)
    return re.findall(r'"([a-z_]+)"', body)


def _extract_ts_dict(ts_src: str, name: str) -> dict[str, str]:
    """Extract a `name: Record<...>` block — keys are quoted strings.

    Handles the `Record<MonthlyInputStream, string> = { key: "label", ... }` shape.
    """
    m = re.search(
        rf"export\s+const\s+{name}\s*:\s*Record<[^>]+>\s*=\s*\{{(.*?)\}};",
        ts_src,
        flags=re.DOTALL,
    )
    if not m:
        pytest.fail(f"{name} declaration not found in TS mirror")
    body = m.group(1)
    pairs = re.findall(r'([a-z_]+)\s*:\s*"([^"]+)"', body)
    return dict(pairs)


def _extract_ts_visibility(ts_src: str, name: str) -> dict[str, list[str]]:
    """Extract `INDUSTRY_VISIBLE_STREAMS: Record<Industry, readonly MonthlyInputStream[]>`.

    Returns {industry_name: [stream, ...]} for each industry.
    """
    m = re.search(
        rf"export\s+const\s+{re.escape(name)}\s*:\s*Record<[^>]+>\s*=\s*\{{(.*?)\}};",
        ts_src,
        flags=re.DOTALL,
    )
    if not m:
        pytest.fail(f"{name} declaration not found in TS mirror")
    body = m.group(1)
    # Match each industry block: industry_name: ["a", "b", ...]
    industry_blocks = re.findall(
        r"([a-z_]+)\s*:\s*\[([^\]]+)\]",
        body,
    )
    out: dict[str, list[str]] = {}
    for industry_name, streams in industry_blocks:
        stream_list = re.findall(r'"([a-z_]+)"', streams)
        out[industry_name] = stream_list
    return out


# ── Test cases ────────────────────────────────────────────────
def test_stream_values_match_python() -> None:
    """MONTHLY_INPUT_STREAM_VALUES (TS) == STREAM_ORDER (Py, canonical)."""
    ts_src = _read_ts_source()
    ts_values = sorted(_extract_ts_stream_values(ts_src))
    from packages.services.m2_input.stream_completion import STREAM_ORDER

    py_values = sorted(STREAM_ORDER)
    assert ts_values == py_values, (
        f"Stream value drift: TS={ts_values!r}, Py={py_values!r}"
    )


def test_stream_label_ko_matches_python() -> None:
    """Korean labels match (PRD §8.M2(b) — 주문/생산/판매/구매/경비/인원)."""
    ts_src = _read_ts_source()
    ts_labels = _extract_ts_dict(ts_src, "MONTHLY_INPUT_STREAM_LABEL_KO")
    assert ts_labels == dict(STREAM_LABELS_KO), (
        f"Label drift: TS={ts_labels!r}, Py={dict(STREAM_LABELS_KO)!r}"
    )


def test_visible_streams_manufacturing_matches_python() -> None:
    """제조업은 6 stream 모두 노출 (PRD §8.M2(b))."""
    ts_src = _read_ts_source()
    ts_visibility = _extract_ts_visibility(ts_src, "INDUSTRY_VISIBLE_STREAMS")
    ts_mfg = sorted(ts_visibility.get("manufacturing", []))
    py_mfg = sorted(STREAMS_FOR_INDUSTRY[Industry.MANUFACTURING])
    assert ts_mfg == py_mfg, (
        f"Manufacturing visibility drift: TS={ts_mfg!r}, Py={py_mfg!r}"
    )


def test_visible_streams_service_excludes_production() -> None:
    """서비스업은 5 stream (production hidden — PRD §8.M2(b))."""
    ts_src = _read_ts_source()
    ts_visibility = _extract_ts_visibility(ts_src, "INDUSTRY_VISIBLE_STREAMS")
    ts_service = sorted(ts_visibility.get("service", []))
    py_service = sorted(STREAMS_FOR_INDUSTRY[Industry.SERVICE])
    assert ts_service == py_service, (
        f"Service visibility drift: TS={ts_service!r}, Py={py_service!r}"
    )
    # Defense in depth — explicitly check production absence.
    assert "production" not in ts_service
    assert "production" not in py_service


def test_visible_streams_count_matches_across_industries() -> None:
    """모든 industry에서 stream 수가 Python과 일치."""
    ts_src = _read_ts_source()
    ts_visibility = _extract_ts_visibility(ts_src, "INDUSTRY_VISIBLE_STREAMS")
    for industry in Industry:
        ts_count = len(ts_visibility.get(industry.value, []))
        py_count = len(STREAMS_FOR_INDUSTRY[industry])
        assert ts_count == py_count, (
            f"{industry.value} stream count drift: "
            f"TS={ts_count}, Py={py_count}"
        )