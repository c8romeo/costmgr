---
name: 1st-release-handoffs-detail
description: 1st release launch (Marketing landing + ToS/Privacy + Onboarding + Support + Production verification + Launch comms 통합 territory) detailed handoff summaries — moved from MEMORY.md index to keep index lean.
metadata:
  node_type: memory
  type: project
  modified: 2026-08-22T15:30:00.000Z
---

# 1st release launch handoffs (Marketing landing + ToS/Privacy + Onboarding + Support + Production verification + Launch comms 통합 territory)

## 1st release PRD entry (cj-style 62번째 epic 연속 정직 회복 atomic docs-only wire)

- **commit**: `e48db06`
- master PRD v3.2 → v3.3 atomic edit + §F18 신규 + AD-29 1st release launch 신규 (6 sub-decisions)
- capability matrix v1.26 → v1.27 EXTENSION 4 NEW rows: LAUNCH_LANDING + LAUNCH_TOS + LAUNCH_SUPPORT + LAUNCH_MONITORING
- A83+A84+A85+A86+A87 5/5 ALL DONE
- 옵션 (d) 1차 출시 진입 결정 (Epic 15 close-out retro §12 4 options 중 사용자 권장 결정, rationale 4종: ① 모든 인프라 wire DONE ② D-1-1-DEFER-1/2/3 ✅ RESOLVED 60번째 ③ cj-style discipline 회피 위험 방지 ④ 비즈니스 우선순위)

## 1st release bmad-create-story spec entry (cj-style 63번째 epic 연속 정직 회복 bmad-create-story spec atomic docs-only wire)

- **spec = `_bmad-output/implementation-artifacts/1st-release-launch-wire.md`** (NEW, ~237 lines, 9 ACs PRD §F18.1~§F18.9 verbatim + 8 tasks T1~T8 + 23 subtasks)
- sprint-status `1st-release-launch-wire: backlog → ready-for-dev` 진입
- A19 cohesion 9 surface EXTENSION PASS (launch surface EXTENSION = F18.1~F18.6 launch territory)
- CR 11-3 honest-DEFER discipline 63번째 epic 연속 정직 회복 결정 wire 진입 (D-1-1-DEFER-1/2/3 ✅ RESOLVED 보존)

## 1st release bmad-dev-story atomic wire T1~T8 DONE (cj-style 64번째 epic 연속 정직 회복 atomic docs-and-source wire DONE)

- **wire_commit**: `be0cf97`
- 32 files atomic single sprint (24 NEW + 8 MODIFIED)
- 9 ACs satisfied (PRD §F18.1~§F18.9 verbatim)
- 3중 게이트 FINAL CLEAN: ruff scoped PASS + pytest 34 collected + vitest 20/20 PASS + tsc 0 NEW + SDR drift gate PASS (pytest 4023 → 4057 +34, vitest 75 → 77 +2) + commit_consistency PASS
- A19 cohesion 9 surface EXTENSION PASS (launch surface EXTENSION = F18.1~F18.6 launch territory)
- D-1-1-DEFER-* honestly ✅ RESOLVED (CR 11-3 64번째 epic 연속 정직 회복)

## 1st release bmad-code-review follow-up sprint (cj-style 65번째 epic 연속 정직 회복 atomic docs-and-source sprint)

- **outcome**: Approve with changes (24 PATCHED + 2 honestly DEFERRED D-LAUNCH-1-DEFER-1)
- 26 findings (4 High + 6 Medium + 15 Low + 1 false positive) — 24 PATCHED + 2 honestly DEFERRED
- 3중 게이트 FINAL CLEAN post-fix: ruff PASS + pytest 34/34 PASS + vitest 20/20 PASS + vitest full suite 757/757 PASS (0 regressions) + pnpm tsc 0 NEW errors (baseline 19 preserved)

## 1st release close-out retro (cj-style 1st release launch 5번째 진입점 = cj-style 66번째 epic 연속 정직 회복 bmad-retrospective atomic docs-only wire)

- **retro_document**: `_bmad-output/implementation-artifacts/1st-release-close-out-2026-08-22.md` (NEW, 13-section cj-style retro = §1 territory 정의 + §2 cycle 정량 데이터 + §3 PRD entry + §4 spec entry + §5 atomic wire + §6 review follow-up + §7 3중 게이트 retro verification FINAL CLEAN + §8 A19 cohesion 9 surface EXTENSION PASS + §9 9 ACs satisfied + §10 CR lessons + §11 D-1-1-DEFER-* ✅ RESOLVED + D-LAUNCH-1-DEFER-1 preserved + §12 결정 wire summary + §13 Cross-References)
- **handoff**: `memory/handoff-2026-08-22-1st-release-close-out-done.md` (NEW)
- **3중 게이트 retro verification FINAL CLEAN** (cj-style 66번째 standard): ruff scoped PASS + pytest 34 collected + vitest 20/20 PASS + tsc 0 NEW + SDR PASS + commit_consistency PASS + D-1-1-DEFER-* grep guard PASS
- **A83+A84+A85+A86+A87 5/5 ALL DONE + APPLIED** + **A88+A89+A90+A91 4/4 신규 결정 wire 진입** (A88 close-out retro + A89 launch checklist 6 conditions ALL PASS + A90 D-LAUNCH-1-DEFER-1 honestly preserved 65~66번째 + A91 D-1-1-DEFER-1/2/3 ✅ RESOLVED 보존 66번째)
- 1st release 5-entry-point pattern 모두 wire DONE 진입 (PRD entry 62번째 + spec entry 63번째 + atomic wire 64번째 + review follow-up 65번째 + close-out retro 66번째)

## Cross-epic 정합 sweep (cj-style 66번째 epic 연속 정직 회복 bmad-retrospective 진입 시점에)

- ✅ Epic 15 PRD entry `dd218fa` + spec entry `9ba92dd` + atomic wire `5f9e37f` + close-out retro `729b223` 결정 wire 모두 보존
- ✅ Phase 4 PRD entry `8e046df` + spec entry + atomic wire `71a033a` + close-out retro `934b35e` 결정 wire 모두 보존
- ✅ Phase 3 cycle close-out 완료 (49~52번째 wire DONE)
- ✅ Epic 12 2FA 게이트 보존
- ✅ Epic 14 LISTEN/NOTIFY multi-process coordination 결정 wire 보존
- ✅ Epic 13 LISTEN/NOTIFY consume 결정 wire 보존
- ✅ Epic 11 close-out retro
- ✅ Phase 2 close-out baseline 599 passed 정합
- ✅ Epic 1 carry-over (auth) layout + onboarding/industry 보존 (F18.3 onboarding guide 정합 결정)
