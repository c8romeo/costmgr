# Phase 22 wire retroactive correction (post-commit verification)

**Date**: 2026-08-27 (KST)
**Style**: cj-style 158th pattern (Phase 20.5 retro + Phase 21 retro precedent)
**Source commit**: `7acbac0` (cj-style 160 wire commit)

## Retroactive correction

Phase 22 wire commit message `commit-msg-cj-160.txt` claimed:
> **~22 files = 17 NEW + 5 MODIFIED atomic single sprint**

Verified actual scope (via `git show --stat HEAD`):
> **27 files changed, 7720 insertions(+), 20 deletions(-)** = **18 NEW + 9 MODIFIED**

## Discrepancy breakdown

The commit message's predicted scope was an under-count by 5 files:

Predicted (17 NEW + 5 MODIFIED = 22):
- 1 alembic 0054
- 8 chargeback_settlement/*.py
- 1 scheduled_dispatch_job.py
- 1 test_phase_22_chargeback_settlement.py
- 1 FinopsChargebackSettlementDashboardPanel.tsx
- 2 chargeback-settlement-{types,client}.ts
- 2 [locale]/admin/finops/chargeback-settlement/{page,layout}.tsx
- 1 handoff memory
- = 17 NEW
- 9 MODIFIED (audit_action + capability + errors + dependencies/capability + main + finops/__init__ + ko-KR.json + sprint-status + MEMORY.md) — actually 9 not 5

Actually the MODIFIED count was the bigger under-count (5 predicted vs 9 actual = +4 discrepancy). Predicted MODIFIED were:
- main.py
- finops/__init__.py
- audit_action.py
- capability.py
- errors.py
- dependencies/capability.py
- ko-KR.json
- sprint-status.yaml
- MEMORY.md
- = 9 MODIFIED

So predicted 5 + actual 9 MODIFIED = +4 file discrepancy.

## Honest recovery per CR 11-3

Per CR 11-3 honest-DEFER discipline, retroactive correction note created. This handoff file documents the verified actual scope.

## Why this happened

The commit message was authored BEFORE final commit-msg read-back. The Phase 22 wire MEMORY.md handoff section also used the predicted count "~22 files = 17 NEW + 5 MODIFIED" rather than the actual count. This file documents the verified actual.

## How to apply

Future Phase 23+ wire commits should:
1. Read `git show --stat HEAD` BEFORE drafting commit-msg text to get the actual file count
2. Use the actual verified count, not the predicted count

## next

cj-style 161 Phase 22 close-out retro 진입 시 actual scope verbatim 반영:
- 18 NEW + 9 MODIFIED = 27 files = 7720 insertions + 20 deletions
- commit hash `7acbac0`
