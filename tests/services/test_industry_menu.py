"""tests.services.test_industry_menu — pure-function tests for industry_menu.py.

Story 1.1 — Task 6.5. These tests have NO DB, NO web, NO clock dependency.
They verify the canonical industry → menu mapping and the A7 전진법 +
7-day grace decision function.

Per AD-5 / AD-15: tests live alongside the canonical domain code and run
under `pytest tests/services/`.
"""

from __future__ import annotations

import pytest

from packages.services.m0_onboarding.industry_menu import (
    GRACE_PERIOD_DAYS,
    INDUSTRY_LABEL_KO,
    Industry,
    IndustryChangeDecision,
    MenuItem,
    SEGMENT_SPLIT_TOOLTIP,
    get_menu,
    get_menu_labels,
    is_industry_change_allowed,
)


# ───────────────────────────────────────────────────────────────
# Industry enum (Task 1.1)
# ───────────────────────────────────────────────────────────────


def test_industry_enum_has_exactly_four_values() -> None:
    """PRD §4.1 mandates 4 options — no more, no less."""
    assert len(Industry) == 4
    assert {i.value for i in Industry} == {
        "manufacturing",
        "service",
        "manufacturing_service",
        "manufacturing_service_other",
    }


def test_industry_enum_values_are_snake_case() -> None:
    """AD-15: enum values must be snake_case."""
    for member in Industry:
        assert member.value == member.value.lower(), f"{member.value} not lowercase"
        assert " " not in member.value, f"{member.value} contains space"


def test_industry_label_ko_matches_prd_canonical() -> None:
    """Decision §2: PRD §4.1 set (제조업 / 서비스업 / 제조+서비스 / 제조+서비스+기타)."""
    assert INDUSTRY_LABEL_KO[Industry.MANUFACTURING] == "제조업"
    assert INDUSTRY_LABEL_KO[Industry.SERVICE] == "서비스업"
    assert INDUSTRY_LABEL_KO[Industry.MANUFACTURING_SERVICE] == "제조+서비스"
    assert INDUSTRY_LABEL_KO[Industry.MANUFACTURING_SERVICE_OTHER] == "제조+서비스+기타"


# ───────────────────────────────────────────────────────────────
# MenuItem enum (Task 1.2)
# ───────────────────────────────────────────────────────────────


def test_menu_item_enum_keys_match_spec() -> None:
    """Verify the canonical set of menu identifiers (17 items per Story 1.1 spec).

    Note: the count is implementation-defined — what matters is that the
    core PRD §8 modules are represented.
    """
    keys = {m.name for m in MenuItem}
    assert "BOM" in keys
    assert "OPENING_INVENTORY" in keys
    assert "INVENTORY_LEDGER" in keys
    assert "COST_POOL" in keys
    assert "ACTIVITY" in keys
    assert "DRIVER" in keys
    assert "SEGMENT_SPLIT" in keys


def test_menu_item_korean_labels_match_spec() -> None:
    """Verify the user-facing Korean labels are stable (UI consumes them)."""
    assert MenuItem.BOM.value == "BOM"
    assert MenuItem.OPENING_INVENTORY.value == "기초재고"
    assert MenuItem.INVENTORY_LEDGER.value == "수불부"
    assert MenuItem.COST_POOL.value == "원가풀"
    assert MenuItem.ACTIVITY.value == "활동"
    assert MenuItem.DRIVER.value == "동인"
    assert MenuItem.SEGMENT_SPLIT.value == "카브아웃 분할"


# ───────────────────────────────────────────────────────────────
# Industry → Menu map (Task 1.3)
# ───────────────────────────────────────────────────────────────


def test_get_menu_for_manufacturing() -> None:
    """① 제조업: BOM/기초재고/수불부 노출, 원가풀/활동/동인 숨김."""
    menu = get_menu(Industry.MANUFACTURING)
    assert MenuItem.BOM in menu
    assert MenuItem.OPENING_INVENTORY in menu
    assert MenuItem.INVENTORY_LEDGER in menu
    assert MenuItem.COST_POOL not in menu
    assert MenuItem.ACTIVITY not in menu
    assert MenuItem.DRIVER not in menu
    assert MenuItem.SEGMENT_SPLIT not in menu


def test_get_menu_for_service() -> None:
    """② 서비스업: BOM/기초재고/수불부 숨김, 원가풀/활동/동인 노출 (epics AC explicit)."""
    menu = get_menu(Industry.SERVICE)
    assert MenuItem.BOM not in menu
    assert MenuItem.OPENING_INVENTORY not in menu  # epics AC explicit (Decision §4)
    assert MenuItem.INVENTORY_LEDGER not in menu
    assert MenuItem.COST_POOL in menu
    assert MenuItem.ACTIVITY in menu
    assert MenuItem.DRIVER in menu
    assert MenuItem.SEGMENT_SPLIT not in menu


def test_get_menu_for_manufacturing_service() -> None:
    """③ 제조+서비스: 모두 노출 + 카브아웃 분할."""
    menu = get_menu(Industry.MANUFACTURING_SERVICE)
    # Manufacturing items
    assert MenuItem.BOM in menu
    assert MenuItem.OPENING_INVENTORY in menu
    assert MenuItem.INVENTORY_LEDGER in menu
    # Service items
    assert MenuItem.COST_POOL in menu
    assert MenuItem.ACTIVITY in menu
    assert MenuItem.DRIVER in menu
    # Plus segment split
    assert MenuItem.SEGMENT_SPLIT in menu


def test_get_menu_for_manufacturing_service_other() -> None:
    """④ 제조+서비스+기타: ③과 동일한 메뉴 (격리 로직은 m3_calculate 내부)."""
    menu_iii = get_menu(Industry.MANUFACTURING_SERVICE)
    menu_iv = get_menu(Industry.MANUFACTURING_SERVICE_OTHER)
    assert set(menu_iii) == set(menu_iv)


def test_get_menu_returns_list_not_tuple() -> None:
    """Subtask 1.4 — return type is `list[MenuItem]` (frontend iterates)."""
    menu = get_menu(Industry.MANUFACTURING)
    assert isinstance(menu, list)


def test_get_menu_labels_returns_korean_strings() -> None:
    """The frontend renders `get_menu_labels()` output directly."""
    labels = get_menu_labels(Industry.SERVICE)
    assert "원가풀" in labels
    assert "활동" in labels
    assert "동인" in labels
    assert "BOM" not in labels
    assert "기초재고" not in labels
    assert "수불부" not in labels


# ───────────────────────────────────────────────────────────────
# Tooltip string (PRD §4.1 + §7.3 [A10])
# ───────────────────────────────────────────────────────────────


def test_segment_split_tooltip_matches_prd() -> None:
    """The 카브아웃 분할 tooltip is part of the UX-locked decision (Decision §4 + AC #3)."""
    assert SEGMENT_SPLIT_TOOLTIP == "재무제표 업로드 필수 (§7.3 [A10])"


# ───────────────────────────────────────────────────────────────
# Grace period (Decision §1)
# ───────────────────────────────────────────────────────────────


def test_grace_period_constant_is_seven_days() -> None:
    """Decision §1: 7-day grace period — locked value."""
    assert GRACE_PERIOD_DAYS == 7


# ───────────────────────────────────────────────────────────────
# is_industry_change_allowed (Task 1.5, A7 전진법)
# ───────────────────────────────────────────────────────────────


def test_allowed_when_no_current_industry() -> None:
    """First-time onboarding (current=None) → always allowed."""
    decision = is_industry_change_allowed(
        current_industry=None,
        target_industry=Industry.SERVICE,
        is_initial=True,
        days_since_selection=-1,
    )
    assert decision.allowed is True
    assert decision.reason == "initial"


def test_allowed_when_same_industry_idempotent() -> None:
    """Same-industry POST is a no-op — return allowed=True."""
    decision = is_industry_change_allowed(
        current_industry=Industry.MANUFACTURING,
        target_industry=Industry.MANUFACTURING,
        is_initial=False,
        days_since_selection=30,
    )
    assert decision.allowed is True
    assert decision.reason == "no_change"


def test_allowed_when_is_initial_true() -> None:
    """is_initial=True covers first change within the funnel — always allowed."""
    decision = is_industry_change_allowed(
        current_industry=Industry.SERVICE,
        target_industry=Industry.MANUFACTURING,
        is_initial=True,
        days_since_selection=0,
    )
    assert decision.allowed is True


def test_allowed_within_seven_day_grace() -> None:
    """Decision §1 Option A: within 7 days, change allowed + warning header."""
    decision = is_industry_change_allowed(
        current_industry=Industry.MANUFACTURING,
        target_industry=Industry.SERVICE,
        is_initial=False,
        days_since_selection=3,
    )
    assert decision.allowed is True
    assert decision.reason == "within_grace"


def test_allowed_on_day_six_boundary() -> None:
    """Day 6 (inclusive) → still within grace."""
    decision = is_industry_change_allowed(
        current_industry=Industry.MANUFACTURING,
        target_industry=Industry.SERVICE,
        is_initial=False,
        days_since_selection=6,
    )
    assert decision.allowed is True


def test_locked_after_seven_day_grace() -> None:
    """Day 7+ with is_initial=False → A7 전진법 enforced (locked)."""
    decision = is_industry_change_allowed(
        current_industry=Industry.MANUFACTURING,
        target_industry=Industry.SERVICE,
        is_initial=False,
        days_since_selection=7,
    )
    assert decision.allowed is False
    assert decision.reason == "locked_after_grace"


def test_locked_after_long_period() -> None:
    """Day 365 → still locked."""
    decision = is_industry_change_allowed(
        current_industry=Industry.MANUFACTURING,
        target_industry=Industry.SERVICE,
        is_initial=False,
        days_since_selection=365,
    )
    assert decision.allowed is False
    assert decision.reason == "locked_after_grace"


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (Industry.MANUFACTURING, Industry.SERVICE),
        (Industry.SERVICE, Industry.MANUFACTURING),
        (Industry.MANUFACTURING_SERVICE, Industry.SERVICE),
        (Industry.MANUFACTURING_SERVICE_OTHER, Industry.MANUFACTURING),
    ],
)
def test_all_industry_transitions_locked_after_grace(
    current: Industry, target: Industry
) -> None:
    """A7 전진법 applies to ALL industry transitions after grace expires."""
    decision = is_industry_change_allowed(
        current_industry=current,
        target_industry=target,
        is_initial=False,
        days_since_selection=10,
    )
    assert decision.allowed is False
    assert decision.reason == "locked_after_grace"


def test_decision_dataclass_is_frozen() -> None:
    """IndustryChangeDecision is a frozen dataclass — immutable."""
    decision = is_industry_change_allowed(None, Industry.SERVICE, True, -1)
    with pytest.raises((AttributeError, Exception)):
        decision.allowed = False  # type: ignore[misc]


# ───────────────────────────────────────────────────────────────
# Drift guard (helps detect accidental enum mutations)
# ───────────────────────────────────────────────────────────────


def test_no_industry_value_is_korean() -> None:
    """Korean labels belong in INDUSTRY_LABEL_KO, not as enum values (AD-15)."""
    for member in Industry:
        is_ascii = all(ord(c) < 128 for c in member.value)
        assert is_ascii, f"Industry value {member.value!r} contains non-ASCII characters"
