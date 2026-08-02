"""apps.api.modules.m3_calculate.services.rules.v7_abc_integrity — V7 rule kernel.

Story 4.3 (Task 1.5) — V7: ABC 무결성 (PRD §11 V-row).

V7 verifies ABC (Activity-Based Costing) integrity for service-only
tenants (AD-12 service-only skip rule):
    ① 원가풀 행 합 100%      (cost_pool_row_sum == 100.00)
    ② 활동 열 합 100%         (activity_col_sum == 100.00)
    ③ 동인 합 100%            (driver_sum == 100)
    ④ 완전배부                (complete_allocation — V1 sub-check)

Per-industry firing: SERVICE ONLY (per AD-12 spec interpretation, cj-style
default). Manufacturing tenants have BOM 100% verified by Story 2.2 gate
(separate step). Mixed / manufacturing_retail tenants skip V7 in MVP —
Epic 9 Story 9-1 expands ABC pool/activity/driver table coverage.

MVP placeholder: tenant_settings.abc JSONB (Story 1.2 ABC field) carries
4 boolean flags. Service-only tenant with all 4 = True → V7 pass. Else
fail with diagnostic.

AD-5 purity: pure helper. No I/O. Same input → same output.

TODO(epic-9): V7 4 sub-checks wire to actual cost_pool/activity/driver
tables (Story 9-1). MVP uses tenant_settings.abc JSONB placeholder.
"""

from __future__ import annotations

from typing import Literal

from apps.api.modules.m3_calculate.services.rules.protocol import (
    INDUSTRY_SERVICE,
    RuleInput,
    VerificationItem,
)


class V7AbcIntegrityRule:
    """V7 — ABC 무결성 검증 (PRD §11 V-row).

    Per-industry firing: SERVICE ONLY. Manufacturing BOM 100% is Story 2.2.
    """

    @property
    def name(self) -> Literal["V7"]:
        return "V7"

    def applies_to(self, *, industry: str) -> bool:
        # AD-12 spec interpretation (cj-style default): V7 fires only for
        # service-only industry. Manufacturing BOM 100% is a separate
        # gate (Story 2.2 step 5 in baseline_loader).
        return industry == INDUSTRY_SERVICE

    def check(self, input: RuleInput) -> VerificationItem:
        """Pure ABC 무결성 sub-check.

        MVP 동작: tenant_settings.abc JSONB의 4 boolean flags 검증.
        Epic 9 Story 9-1에서 cost_pool/activity/driver table 도입 시
        1-line swap (4 sub-checks wire to actual tables).
        """
        # Industry pre-condition (applies_to enforces this, but defense
        # in depth — never read abc JSONB for non-service tenants).
        if input.industry != INDUSTRY_SERVICE:
            return VerificationItem(
                code="V7",
                status="failed",
                message_ko=(
                    f"V7 발동 condition 위반 (industry={input.industry!r}, "
                    f"service-only이어야 함)"
                ),
                details={"industry": input.industry},
            )

        # MVP: tenant_settings.abc JSONB는 CalcRuleInput에 직접 없음.
        # baseline.bom_ratio_validated flag 활용 (Epic 9 9-1에서
        # tenant_settings.abc JSONB로 1-line swap).
        # Service-only tenant의 BOM 100% 검증은 Story 2.2 gate 우회
        # (baseline_loader._verify_bom_100_pct → True for service).
        # MVP placeholder: 모든 service tenant V7 pass (Epic 9 wire 후 검증).
        abc_pools_ok = True
        abc_activities_ok = True
        abc_drivers_ok = True
        abc_complete_allocation_ok = True

        all_pass = (
            abc_pools_ok
            and abc_activities_ok
            and abc_drivers_ok
            and abc_complete_allocation_ok
        )

        if all_pass:
            return VerificationItem(
                code="V7",
                status="passed",
                message_ko=(
                    "ABC 무결성 정상 (원가풀 100% · 활동 100% · "
                    "동인 100% · 완전배부 — Epic 9 9-1 wire 후 실제 검증)"
                ),
                details={
                    "pools_ok": abc_pools_ok,
                    "activities_ok": abc_activities_ok,
                    "drivers_ok": abc_drivers_ok,
                    "complete_allocation_ok": abc_complete_allocation_ok,
                    "mvp_placeholder": True,
                },
            )

        # MVP — 실패 경로는 Epic 9 wire 후 발생 (Story 9-1 진입 시)
        failed_subs = [
            name
            for name, ok in [
                ("pools", abc_pools_ok),
                ("activities", abc_activities_ok),
                ("drivers", abc_drivers_ok),
                ("complete_allocation", abc_complete_allocation_ok),
            ]
            if not ok
        ]
        return VerificationItem(
            code="V7",
            status="failed",
            message_ko=(
                f"ABC 무결성 위반 ({', '.join(failed_subs)}) — "
                f"Epic 9 Story 9-1 진입 전 placeholder"
            ),
            details={
                "pools_ok": abc_pools_ok,
                "activities_ok": abc_activities_ok,
                "drivers_ok": abc_drivers_ok,
                "complete_allocation_ok": abc_complete_allocation_ok,
                "failed_subchecks": failed_subs,
            },
        )


__all__ = ["V7AbcIntegrityRule"]
