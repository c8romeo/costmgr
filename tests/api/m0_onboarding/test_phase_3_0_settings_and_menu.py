"""tests.api.m0_onboarding.test_phase_3_0_settings_and_menu — M0 source health gap tests.

Source health 갭 회복 wire (순서 2, cj-style 307번째 정직 회복) — M0 +4 tests:
M0 onboarding 모듈의 menu mapping + industry change grace period +
signup completion invariant coverage 보강. env-free (Pydantic + pure helper only),
LOW risk.

검증 항목 (4 tests, 사용자 지시 verbatim 반영):

1. **Menu mapping completeness (PRD §4.1 + §8.M0(a))**
   - 4 industry enum values 모두 get_menu() non-empty list
   - MenuItem orphan value 검출 (drift-detector friendly)

2. **Industry 변경 grace period (PRD §8.M0 + AD-23 + A7)**
   - days_since_selection < GRACE_PERIOD_DAYS → allowed=True
   - days_since_selection >= GRACE_PERIOD_DAYS → allowed=False

3. **Industry enum ↔ label 일치 (PRD §4.1)**
   - INDUSTRY_LABEL_KO keys == Industry enum members
   - 모든 label unique + non-empty + 한글

4. **Signup completion invariant (PRD §8.M0(b))**
   - tenant_settings 비어있을 때 is_complete=False + missing list 채워짐
   - 모든 field set 시 is_complete=True + missing empty
"""
from __future__ import annotations

import re


# ── Test 1 — Menu mapping completeness (PRD §4.1 + §8.M0(a)) ─────────


def test_get_menu_4_industries_all_non_empty_no_orphan_menu_items():
    """PRD §4.1 + §8.M0(a): 4 industries 모두 menu non-empty + MenuItem orphan 0.

    - 4 industries (MANUFACTURING / SERVICE / MANUFACTURING_SERVICE /
      MANUFACTURING_SERVICE_OTHER) 모두 get_menu() non-empty list 반환
    - 모든 MenuItem enum 멤버가 적어도 1개 industry menu 에 등장 (drift-detector friendly)
    """
    from apps.api.modules.m0_onboarding.menu import Industry, MenuItem, get_menu

    expected_industries = {
        Industry.MANUFACTURING,
        Industry.SERVICE,
        Industry.MANUFACTURING_SERVICE,
        Industry.MANUFACTURING_SERVICE_OTHER,
    }

    # (a) 4 industries 모두 non-empty
    for industry in expected_industries:
        menu = get_menu(industry)
        assert isinstance(menu, list)
        assert len(menu) >= 1, (
            f"get_menu({industry}) must be non-empty (PRD §8.M0(a) auto-toggle)"
        )

    # (b) MenuItem orphan 검출 (drift-detector friendly)
    all_items = set(MenuItem)
    seen_items: set[MenuItem] = set()
    for industry in Industry:
        seen_items.update(get_menu(industry))
    orphans = all_items - seen_items
    assert not orphans, f"MenuItem orphan values (no industry mapping): {orphans}"


# ── Test 2 — Industry change grace period (PRD §8.M0 + AD-23 + A7) ────


def test_industry_change_grace_period_boundary_decisions():
    """PRD §8.M0 grace period: GRACE_PERIOD_DAYS 이내 변경 allowed, 초과 시 locked.

    is_industry_change_allowed() returns IndustryChangeDecision with `allowed`
    field. 경계값 검증:
    - day 0: allowed=True (가입 직후)
    - day GRACE_PERIOD_DAYS-1: allowed=True (grace 마지막 -1)
    - day GRACE_PERIOD_DAYS: allowed=False (A7 전진법 enforcement)
    """
    from apps.api.modules.m0_onboarding.menu import (
        GRACE_PERIOD_DAYS,
        Industry,
        is_industry_change_allowed,
    )

    current = Industry.MANUFACTURING
    target = Industry.SERVICE

    # day 0: within grace
    d0 = is_industry_change_allowed(
        current_industry=current,
        target_industry=target,
        is_initial=False,
        days_since_selection=0,
    )
    assert d0.allowed is True
    assert d0.reason == "within_grace"

    # day GRACE_PERIOD_DAYS-1: still within grace
    d_pre = is_industry_change_allowed(
        current_industry=current,
        target_industry=target,
        is_initial=False,
        days_since_selection=GRACE_PERIOD_DAYS - 1,
    )
    assert d_pre.allowed is True
    assert d_pre.reason == "within_grace"

    # day GRACE_PERIOD_DAYS: A7 전진법 → locked
    d_locked = is_industry_change_allowed(
        current_industry=current,
        target_industry=target,
        is_initial=False,
        days_since_selection=GRACE_PERIOD_DAYS,
    )
    assert d_locked.allowed is False
    assert d_locked.reason == "locked_after_grace"


# ── Test 3 — Industry enum ↔ label 일치 (PRD §4.1) ───────────────────


def test_industry_label_ko_drift_detection_keys_and_values():
    """PRD §4.1: INDUSTRY_LABEL_KO ↔ Industry enum drift 0.

    (a) label dictionary keys == Industry enum members (1:1 매핑)
    (b) 모든 label unique + non-empty + 한글 포함 (Hangul Syllables U+AC00~U+D7A3)
    """
    from apps.api.modules.m0_onboarding.menu import INDUSTRY_LABEL_KO, Industry

    # (a) keys ↔ enum members
    label_keys = set(INDUSTRY_LABEL_KO.keys())
    enum_members = set(Industry)
    assert label_keys == enum_members, (
        f"INDUSTRY_LABEL_KO keys drift from Industry enum. "
        f"only-in-labels={label_keys - enum_members}, "
        f"only-in-enum={enum_members - label_keys}"
    )

    # (b) uniqueness + non-empty + 한글
    labels = list(INDUSTRY_LABEL_KO.values())
    assert len(labels) == len(set(labels)), (
        f"INDUSTRY_LABEL_KO has duplicate values: {labels}"
    )

    korean_pattern = re.compile(r"[가-힣]")
    for label in labels:
        assert isinstance(label, str) and len(label) > 0, f"empty label: {label!r}"
        assert korean_pattern.search(label), (
            f"label missing Korean characters: {label!r}"
        )


# ── Test 4 — Signup completion invariant (PRD §8.M0(b)) ───────────────


def test_compute_completion_incomplete_then_complete_transition():
    """PRD §8.M0(b): settings 비어있을 때 incomplete, 모두 set 시 complete.

    (a) tenant_settings=None + allocation_counts=None → is_complete=False
        + missing list ≥ 3 (PRD §8.M0(b) 최소 3종 settings 보고)
    (b) 모든 필수 field set → is_complete=True + missing empty
    """
    from packages.services.m0_onboarding.settings_completion import (
        compute_completion,
    )

    # (a) incomplete
    incomplete = compute_completion(
        industry="manufacturing",
        tenant_settings=None,
        allocation_counts=None,
    )
    assert incomplete.is_complete is False
    assert isinstance(incomplete.missing, list)
    assert len(incomplete.missing) >= 3, (
        f"PRD §8.M0(b): 최소 3종 settings 미완료 시 missing 에 보고되어야 함. "
        f"got missing={incomplete.missing}"
    )

    # (b) complete (모든 필수 field 채워짐)
    complete = compute_completion(
        industry="manufacturing",
        tenant_settings={
            "fiscal_year_start": 1,
            "currency": "KRW",
            "language": "ko-KR",
        },
        allocation_counts={
            "direct_indirect": 10,
            "fixed_variable": 10,
            "allocation_basis": 3,
        },
    )
    assert complete.is_complete is True, (
        f"all-set 상태에서 is_complete=True 여야 함. got missing={complete.missing}"
    )
    assert complete.missing == [], (
        f"all-set 상태에서 missing list 가 비어야 함. got missing={complete.missing}"
    )
