"""tests.integration.test_menu_config_consistency — drift guard for menu config.

Story 1.1 — Task 6.6. The canonical industry → menu map lives in TWO
places:

  - `packages/services/m0_onboarding/industry_menu.py` (Python, source of truth)
  - `apps/web/lib/menu-config.ts` (TypeScript mirror, consumed by Next.js)

This test parses the TypeScript file and asserts that:

  1. The set of industry values matches.
  2. The Korean label dictionary matches.
  3. Per-industry menu item lists match exactly (set + order).
  4. The `GRACE_PERIOD_DAYS` constant matches.
  5. The `SEGMENT_SPLIT_TOOLTIP` string matches.

If either side changes, this test fails. The CI lint-conventions job
runs it alongside the Python lint suite.

Why parsing instead of importing? The TS file lives in `apps/web/`,
which is Next.js territory — not on the Python path. Parsing via
`re` keeps the test hermetic (no Node, no ts-node).
"""

from __future__ import annotations

import re
from pathlib import Path

from packages.services.m0_onboarding.industry_menu import (
    GRACE_PERIOD_DAYS,
    INDUSTRY_ICON,
    INDUSTRY_LABEL_KO,
    Industry,
    MenuItem,
    SEGMENT_SPLIT_TOOLTIP,
    get_menu,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
TS_PATH = REPO_ROOT / "apps" / "web" / "lib" / "menu-config.ts"


def _read_ts_source() -> str:
    """Read the TS file as text — fail fast if missing.

    F-25: strip line (`// ...`) and block (`/* ... */`) comments before
    returning so the regex patterns below never match quoted strings that
    appear inside developer commentary. Without this, a doc comment like
    `// e.g. `manufacturing_service` enables both` would falsely satisfy
    the INDUSTRY_VALUES regex.
    """
    if not TS_PATH.exists():
        pytest_skip_or_fail(
            f"TypeScript mirror not found at {TS_PATH}. "
            "Story 1.1 Task 3.5 must create this file alongside the Python enum."
        )
    raw = TS_PATH.read_text(encoding="utf-8")
    # Strip block comments first (so they don't swallow line-comment markers).
    no_block = re.sub(r"/\*.*?\*/", "", raw, flags=re.DOTALL)
    # Strip line comments — only outside of strings is ideal, but TS source
    # for our menu-config.ts never contains a `//` inside a string literal
    # (all string content is Korean/ASCII labels), so a simple line strip
    # is safe and keeps the helper small.
    no_line = re.sub(r"//[^\n]*", "", no_block)
    return no_line


def pytest_skip_or_fail(msg: str) -> None:
    import pytest

    pytest.fail(msg)


# ─────────────────────────────────────────────────────────────
# Industry enum parity
# ─────────────────────────────────────────────────────────────


def test_ts_industry_values_match_python_enum() -> None:
    """Industry enum values must match exactly (snake_case, no extras)."""
    import pytest

    src = _read_ts_source()
    m = re.search(
        r"export\s+const\s+INDUSTRY_VALUES\s*=\s*\[(?P<body>.*?)\]\s*as\s+const",
        src,
        re.DOTALL,
    )
    if not m:
        pytest.fail("Could not find INDUSTRY_VALUES array in menu-config.ts")

    ts_values = re.findall(r'"([a-z_]+)"', m.group("body"))
    py_values = [member.value for member in Industry]
    assert ts_values == py_values, (
        f"Industry values drifted.\n  TS: {ts_values}\n  PY: {py_values}"
    )


def test_ts_industry_label_ko_matches_python() -> None:
    """Korean labels must match PRD §4.1 canonical set."""
    import pytest

    src = _read_ts_source()
    m = re.search(
        r"export\s+const\s+INDUSTRY_LABEL_KO:\s*Record<Industry,\s*string>\s*=\s*\{(?P<body>.*?)\};",
        src,
        re.DOTALL,
    )
    if not m:
        pytest.fail("Could not find INDUSTRY_LABEL_KO object in menu-config.ts")

    body = m.group("body")
    for industry in Industry:
        pattern = rf"{industry.value}:\s*\"(?P<label>[^\"]+)\""
        m2 = re.search(pattern, body)
        assert m2, f"Missing industry key {industry.value!r} in TS INDUSTRY_LABEL_KO"
        assert m2.group("label") == INDUSTRY_LABEL_KO[industry], (
            f"Label drift for {industry.value!r}: "
            f"TS={m2.group('label')!r} PY={INDUSTRY_LABEL_KO[industry]!r}"
        )


# ─────────────────────────────────────────────────────────────
# Per-industry menu list parity (set + order)
# ─────────────────────────────────────────────────────────────


def test_ts_manufacturing_menu_matches_python() -> None:
    import pytest

    src = _read_ts_source()
    _assert_industry_menu_parity(src, "manufacturing", Industry.MANUFACTURING, pytest)


def test_ts_service_menu_matches_python() -> None:
    import pytest

    src = _read_ts_source()
    _assert_industry_menu_parity(src, "service", Industry.SERVICE, pytest)


def test_ts_manufacturing_service_menu_matches_python() -> None:
    import pytest

    src = _read_ts_source()
    _assert_industry_menu_parity(src, "manufacturing_service", Industry.MANUFACTURING_SERVICE, pytest)


def test_ts_manufacturing_service_other_menu_matches_python() -> None:
    import pytest

    src = _read_ts_source()
    _assert_industry_menu_parity(
        src, "manufacturing_service_other", Industry.MANUFACTURING_SERVICE_OTHER, pytest
    )


def _assert_industry_menu_parity(
    src: str, industry_key: str, industry_enum: Industry, pytest_module
) -> None:
    """Pull the menu list for `industry_key` from the TS source and compare."""
    pattern = (
        rf"{industry_key}:\s*\[(?P<body>.*?)\]"
    )
    m = re.search(pattern, src, re.DOTALL)
    if not m:
        pytest_module.fail(f"Industry menu block not found for {industry_key!r}")

    ts_items = re.findall(r'"([^"]+)"', m.group("body"))
    py_items = [m.value for m in get_menu(industry_enum)]
    assert ts_items == py_items, (
        f"Menu list drift for {industry_enum.value}.\n"
        f"  TS ({len(ts_items)}): {ts_items}\n"
        f"  PY ({len(py_items)}): {py_items}"
    )


# ─────────────────────────────────────────────────────────────
# Constants parity
# ─────────────────────────────────────────────────────────────


def test_ts_grace_period_days_matches_python() -> None:
    import pytest

    src = _read_ts_source()
    m = re.search(r"export\s+const\s+GRACE_PERIOD_DAYS\s*=\s*(\d+)", src)
    if not m:
        pytest.fail("Could not find GRACE_PERIOD_DAYS in menu-config.ts")
    assert int(m.group(1)) == GRACE_PERIOD_DAYS, (
        f"GRACE_PERIOD_DAYS drift: TS={m.group(1)} PY={GRACE_PERIOD_DAYS}"
    )


def test_ts_segment_split_tooltip_matches_python() -> None:
    import pytest

    src = _read_ts_source()
    m = re.search(r"SEGMENT_SPLIT_TOOLTIP\s*=\s*\"(?P<v>[^\"]+)\"", src)
    if not m:
        pytest.fail("Could not find SEGMENT_SPLIT_TOOLTIP in menu-config.ts")
    assert m.group("v") == SEGMENT_SPLIT_TOOLTIP


# ─────────────────────────────────────────────────────────────
# MenuItem enum keys (AD-15 — both sides reference every PRD §8 item)
# ─────────────────────────────────────────────────────────────


def test_python_menuitem_has_korean_label_for_every_ts_label() -> None:
    """For every Korean label in TS, the Python MenuItem enum must have a member.

    Reverse direction — protects against accidental removal of a Python
    enum member when the TS list still references the Korean label.
    """
    import pytest

    src = _read_ts_source()
    # Pull all quoted Korean / ASCII labels from any of the four industry
    # blocks (just the strings inside `["..."]`).
    ts_labels: set[str] = set()
    for industry_key in [m.value for m in Industry]:
        m = re.search(
            rf"{industry_key}:\s*\[(?P<body>.*?)\]",
            src,
            re.DOTALL,
        )
        if m:
            ts_labels.update(re.findall(r'"([^"]+)"', m.group("body")))

    py_labels = {m.value for m in MenuItem}
    missing_in_py = ts_labels - py_labels
    assert not missing_in_py, f"TS labels missing from Python MenuItem enum: {missing_in_py}"


# ─────────────────────────────────────────────────────────────
# INDUSTRY_ICON parity (Story 0.5 T8.4 — closes Story 1.1 F-33+F-37)
# A5 forward-lock drift detector pattern: drift = A5 forward-lock fail.
# ─────────────────────────────────────────────────────────────


def test_industry_icon_parity_ts_matches_python() -> None:
    """INDUSTRY_ICON must match between TS and Python for every industry.

    Both sides store icon NAME (lucide-react convention) — Python side has
    no SVG component. Drift here breaks IndustryCard rendering (TS looks up
    lucide by name) and would be silent in CI otherwise.
    """
    import pytest

    src = _read_ts_source()
    m = re.search(
        r"export\s+const\s+INDUSTRY_ICON:\s*Record<Industry,\s*string>\s*=\s*\{(?P<body>.*?)\};",
        src,
        re.DOTALL,
    )
    if not m:
        pytest.fail("Could not find INDUSTRY_ICON object in menu-config.ts")

    body = m.group("body")
    for industry in Industry:
        pattern = rf'{industry.value}:\s*"(?P<icon>[^"]+)"'
        m2 = re.search(pattern, body)
        assert m2, f"Missing industry key {industry.value!r} in TS INDUSTRY_ICON"
        assert m2.group("icon") == INDUSTRY_ICON[industry], (
            f"INDUSTRY_ICON drift for {industry.value!r}: "
            f"TS={m2.group('icon')!r} PY={INDUSTRY_ICON[industry]!r}"
        )
