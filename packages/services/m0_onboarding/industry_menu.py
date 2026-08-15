"""packages.services.m0_onboarding.industry_menu — industry → menu mapping (Story 1.1).

Pure-Python, stdlib-only module that defines the canonical Industry enum,
the MenuItem enum, and the industry → menu map (PRD §4.1 + §8.M0(a)).

This module is imported by:
- apps/api/modules/m0_onboarding/*        (FastAPI handlers, Pydantic schemas)
- packages/services/m0_onboarding/__init__.py  (re-export)
- tests/services/test_industry_menu.py    (pure-function unit tests)
- tests/integration/test_menu_config_consistency.py (drift check vs TS mirror)

AD binds enforced here:
- AD-1 / AD-5 — pure (no I/O, no DB, no clock, no random). Only `enum` + `dataclasses`.
- AD-15 — snake_case enum values, PascalCase class names. Korean labels are
  user-facing strings (data), not code identifiers.
- AD-23 — `Industry` is a namespaced enum under `tenant_settings.onboarding`
  (JSONB). One row per tenant, one enum per module.
- A7 — `is_industry_change_allowed()` enforces the 전진법: industry can be
  changed only while `is_initial=true` OR within the 7-day grace period.

Korean labels (Decision §2): PRD §4.1 canonical set:
    ① 제조업 / ② 서비스업 / ③ 제조+서비스 / ④ 제조+서비스+기타
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final


# ── Industry enum (PRD §4.1) ─────────────────────────────────
class Industry(str, Enum):
    """PRD §4.1 4지선다 — backend canonical enum values (snake_case)."""

    MANUFACTURING = "manufacturing"  # ① 제조업
    SERVICE = "service"  # ② 서비스업
    MANUFACTURING_SERVICE = "manufacturing_service"  # ③ 제조+서비스 (겸영)
    MANUFACTURING_SERVICE_OTHER = "manufacturing_service_other"  # ④ 제조+서비스+기타


# ── MenuItem enum (PRD §8) ──────────────────────────────────
class MenuItem(str, Enum):
    """PRD §8 module-level menu items — values are Korean labels (UI-facing).

    Enum NAME is the canonical Python identifier (PascalCase per AD-15).
    Enum VALUE is the user-facing Korean label consumed by the frontend.
    """

    PRODUCT = "품목"
    BOM = "BOM"
    OPENING_INVENTORY = "기초재고"
    INVENTORY_LEDGER = "수불부"
    COST_POOL = "원가풀"
    ACTIVITY = "활동"
    DRIVER = "동인"
    SEGMENT_SPLIT = "카브아웃 분할"
    ACCOUNT = "계정과목"
    DEPARTMENT = "부서"
    CUSTOMER = "거래처"
    AI_EXTRACT = "AI추출"
    SIMULATION = "시뮬레이션"
    BUDGET = "예산"
    REPORT = "보고서"
    CLOSE = "마감"
    ACCOUNT_MGMT = "계정관리"
    # Story 12.3 — Account deletion + retention consent UI
    # (PRD §F12.3 + NFR4 2절 5년 audit 보존 + 30일 hard delete retention).
    # Industry-agnostic security baseline (CR 12-1 L4 precedent — mirrors
    # BACKUP_EXPORT 12-2 + TWO_FACTOR_AUTH 12-1). Available in every
    # industry because deletion is a data subject right (GDPR Art.17),
    # not an industry-specific feature.
    ACCOUNT_SETTINGS = "계정 설정"
    # Story 12.5 — 2FA self-service UI (industry-agnostic security baseline).
    # Available in every industry (PRD §F12.1 / §M12-a applies to all tenants).
    ACCOUNT_SECURITY = "계정 보안"


# ── Industry → Menu map (PRD §4.1 / §8.M0(a)) ─────────────
# ① 제조업: 전통 개별원가 엔진. BOM·기초재고·수불부 노출, ABC 메뉴(원가풀·활동·동인) 숨김.
# ② 서비스업: ABC 엔진. 제조 메뉴 3종 숨김, ABC 메뉴 3종 노출.
# ③ 제조+서비스: 두 엔진 병행. 전부 노출 + 카브아웃 분할(§7.3 [A10]).
# ④ 제조+서비스+기타: ③ + 격리 버킷. 메뉴는 ③과 동일(격리 로직은 m3_calculate 내부).
# Story 12.5: "계정 보안" appended to every industry menu (2FA industry-agnostic).
# Story 12.3: "계정 설정" inserted between "계정관리" + "계정 보안"
# (account deletion UI is industry-agnostic security baseline).
_INDUSTRY_MENU_MAP: Final[dict[Industry, tuple[MenuItem, ...]]] = {
    Industry.MANUFACTURING: (
        MenuItem.PRODUCT,
        MenuItem.BOM,
        MenuItem.OPENING_INVENTORY,
        MenuItem.INVENTORY_LEDGER,
        MenuItem.ACCOUNT,
        MenuItem.DEPARTMENT,
        MenuItem.CUSTOMER,
        MenuItem.AI_EXTRACT,
        MenuItem.SIMULATION,
        MenuItem.BUDGET,
        MenuItem.REPORT,
        MenuItem.CLOSE,
        MenuItem.ACCOUNT_MGMT,
        MenuItem.ACCOUNT_SETTINGS,
        MenuItem.ACCOUNT_SECURITY,
    ),
    Industry.SERVICE: (
        MenuItem.COST_POOL,
        MenuItem.ACTIVITY,
        MenuItem.DRIVER,
        MenuItem.ACCOUNT,
        MenuItem.DEPARTMENT,
        MenuItem.CUSTOMER,
        MenuItem.AI_EXTRACT,
        MenuItem.SIMULATION,
        MenuItem.BUDGET,
        MenuItem.REPORT,
        MenuItem.CLOSE,
        MenuItem.ACCOUNT_MGMT,
        MenuItem.ACCOUNT_SETTINGS,
        MenuItem.ACCOUNT_SECURITY,
    ),
    Industry.MANUFACTURING_SERVICE: (
        MenuItem.PRODUCT,
        MenuItem.BOM,
        MenuItem.OPENING_INVENTORY,
        MenuItem.INVENTORY_LEDGER,
        MenuItem.COST_POOL,
        MenuItem.ACTIVITY,
        MenuItem.DRIVER,
        MenuItem.SEGMENT_SPLIT,
        MenuItem.ACCOUNT,
        MenuItem.DEPARTMENT,
        MenuItem.CUSTOMER,
        MenuItem.AI_EXTRACT,
        MenuItem.SIMULATION,
        MenuItem.BUDGET,
        MenuItem.REPORT,
        MenuItem.CLOSE,
        MenuItem.ACCOUNT_MGMT,
        MenuItem.ACCOUNT_SETTINGS,
        MenuItem.ACCOUNT_SECURITY,
    ),
    Industry.MANUFACTURING_SERVICE_OTHER: (
        MenuItem.PRODUCT,
        MenuItem.BOM,
        MenuItem.OPENING_INVENTORY,
        MenuItem.INVENTORY_LEDGER,
        MenuItem.COST_POOL,
        MenuItem.ACTIVITY,
        MenuItem.DRIVER,
        MenuItem.SEGMENT_SPLIT,
        MenuItem.ACCOUNT,
        MenuItem.DEPARTMENT,
        MenuItem.CUSTOMER,
        MenuItem.AI_EXTRACT,
        MenuItem.SIMULATION,
        MenuItem.BUDGET,
        MenuItem.REPORT,
        MenuItem.CLOSE,
        MenuItem.ACCOUNT_MGMT,
        MenuItem.ACCOUNT_SETTINGS,
        MenuItem.ACCOUNT_SECURITY,
    ),
}


# ── Tooltip strings (AD-15, UX hint) ────────────────────────
# When the user hovers "카브아웃 분할", the frontend shows this tooltip
# (PRD §4.1 + §7.3 [A10]).
SEGMENT_SPLIT_TOOLTIP: Final[str] = "재무제표 업로드 필수 (§7.3 [A10])"


# ── INDUSTRY_ICON (Story 0.5 T8.3 — closes Story 1.1 F-37) ───
# Mirror of apps/web/lib/menu-config.ts::INDUSTRY_ICON. Stores icon
# name only (Python side has no SVG component). Drift between this and
# the TS mirror is caught by tests/integration/test_menu_config_consistency.py.
INDUSTRY_ICON: Final[dict[Industry, str]] = {
    Industry.MANUFACTURING: "Factory",
    Industry.SERVICE: "Briefcase",
    Industry.MANUFACTURING_SERVICE: "Layers",
    Industry.MANUFACTURING_SERVICE_OTHER: "Boxes",
}


# ── Industry label dictionary (Decision §2: PRD §4.1 set) ──
INDUSTRY_LABEL_KO: Final[dict[Industry, str]] = {
    Industry.MANUFACTURING: "제조업",
    Industry.SERVICE: "서비스업",
    Industry.MANUFACTURING_SERVICE: "제조+서비스",
    Industry.MANUFACTURING_SERVICE_OTHER: "제조+서비스+기타",
}


# ── Public helpers ──────────────────────────────────────────
def get_menu(industry: Industry) -> list[MenuItem]:
    """Return the menu list for `industry`. Order is preserved (PRD §8 display order).

    Pure function — safe to call from request handlers and tests.
    """
    return list(_INDUSTRY_MENU_MAP[industry])


def get_menu_labels(industry: Industry) -> list[str]:
    """Return Korean menu labels (the frontend renders these directly)."""
    return [item.value for item in _INDUSTRY_MENU_MAP[industry]]


@dataclass(frozen=True)
class IndustryChangeDecision:
    """Result of `is_industry_change_allowed()` — both the boolean and reason.

    The reason is exposed in the API response so the frontend can show a
    precise toast ("locked", "initial", "within-grace", etc.) without
    re-deriving from the boolean.
    """

    allowed: bool
    reason: str  # "initial" | "within_grace" | "locked_after_grace" | "locked_after_calc"
    days_since_selection: int


# 7-day grace period (Decision §1, Option A — locked). Documented in
# `docs/onboarding-flow.md` and surfaces as `X-Onboarding-Warning` header
# on subsequent changes.
GRACE_PERIOD_DAYS: Final[int] = 7


def is_industry_change_allowed(
    current_industry: Industry | None,
    target_industry: Industry,
    is_initial: bool,
    days_since_selection: int,
) -> IndustryChangeDecision:
    """Pure decision function — does NOT touch the DB or clock.

    Logic (A7 전진법 + 7-day grace, per Story 1.1 Subtask 1.5):
        allowed = is_initial OR days_since_selection < GRACE_PERIOD_DAYS

    - `current_industry is None`           → first-time onboarding → allowed
      (the function then never sees `is_initial` since there's no prior row).
    - `current_industry == target_industry` → idempotent no-op → allowed.
    - `is_initial == True`                 → still in initial onboarding window
      → allowed. The frontend does NOT show the warning header in this case.
    - `is_initial == False` AND `days_since_selection < 7`
                                          → within 7-day grace → allowed.
      The frontend SHOULD show the `X-Onboarding-Warning:
      initial-change-allowed-for-7-days` header.
    - `is_initial == False` AND `days_since_selection >= 7`
                                          → A7 전진법 enforced → locked.
      Returns reason `locked_after_grace`. The 409 response carries
      `next_fiscal_year_start` in the details (AC #4).

    Args:
        current_industry: The tenant's current industry (None = never selected).
        target_industry: The industry the user wants to switch to.
        is_initial: True if this is the first onboarding selection
            (Story 0.2 default) or a pre-grace-period change. After the
            first change is applied, the service sets this to False
            (see `SettingsService.update_industry`).
        days_since_selection: Number of full days since `selected_at`.
            Pass -1 when `current_industry` is None (no selection yet) — the
            function then defers to `is_initial`.

    Returns:
        `IndustryChangeDecision(allowed, reason, days_since_selection)`.
    """
    # First-time onboarding (current_industry is None) — always allowed.
    if current_industry is None:
        return IndustryChangeDecision(
            allowed=True,
            reason="initial",
            days_since_selection=days_since_selection,
        )

    # Same industry → idempotent no-op. Treat as allowed.
    if current_industry == target_industry:
        return IndustryChangeDecision(
            allowed=True,
            reason="initial" if is_initial else "no_change",
            days_since_selection=days_since_selection,
        )

    # Decision rule (Subtask 1.5 spec): is_initial OR days_since < GRACE.
    if is_initial or days_since_selection < GRACE_PERIOD_DAYS:
        # Distinguish "initial onboarding" from "within grace" so the
        # frontend can show different toast/header copy.
        reason = "initial" if is_initial else "within_grace"
        return IndustryChangeDecision(
            allowed=True,
            reason=reason,
            days_since_selection=days_since_selection,
        )

    # Outside grace → A7 전진법 locked.
    return IndustryChangeDecision(
        allowed=False,
        reason="locked_after_grace",
        days_since_selection=days_since_selection,
    )
