---
title: Epic 11 Second Carry-Over Sprint (A41) — 3 items sprint-up
status: ready-for-dev
priority: HIGH
epic: 11
story_num: 5
story_key: 11-5-epic-11-second-carry-over-sprint
baseline_commit: dc85ab9
created: 2026-08-19
updated: 2026-08-19
---

> **A41 Epic 11 carry-over sprint** (Epic 10 retro §7 신규 결정 + 사용자 옵션 (a) wire 진입 결정 = "A41 carry-over sprint 진입 시 wire"). 본 스토리는 A41의 carry-over CLOSE-OUT 부분 (A13 residual + A17 + A18) 만 다룬다. A40 Report #15 wire (~1,500 LOC 9-surface) 는 **별도 Sprint 11-6 dedicated wire** 로 분리 (process design 관점에서 per-sprint scope 위험 최소화 결정).
>
> **baseline_commit = `dc85ab9`** (smoke-fix sprint atomic wire tip = Epic 10 4-story wire + smoke-fix 5 fixes + CI green gate).
>
> **Epic 11 close-out retro (2026-08-09) §7 A13~A18 결정 wire** + **Epic 10 close-out retro (2026-08-19) §7 A41 신규 결정**.

# Story 11.5 — Epic 11 Second Carry-Over Sprint (A41 close-out)

## Epic context

Epic 11 cj-style 3-story 분할 (Epic 5 close-out retro §6 W1) 모두 done 진입:

- **11-1** = M11 module authority + AD-22 reversal ledger wire ✅ done (commit `b4961a6`, 2026-08-08)
- **11-2** = close-sequence-lock ✅ done (commit `caacfc7`, 2026-08-08)
- **11-3** = snapshot-persistence-with-reverse ✅ done (commit `4e4e8d6`, 2026-08-09)
- **11-4** = first carry-over sprint (A13 sprint-up 첫 시도) ✅ done (commit `4e4e8d6` re-verification, 2026-08-10) — 16 of 18 DEFER items **resolved** during post-sprint close-out verification cycle, 2 still-pending

**Epic 11 close-out retro** (cj-style 7-section lightweight, 2026-08-09) 완료. epic-11 done + epic-11-retrospective done. 6 NEW action items A13~A18.

**Epic 10 close-out retro** (2026-08-19) §7 A41 신규 결정 — A41 = Epic 11 second carry-over sprint. 본 스토리 (11-5) = A41 close-out 부분. **Sprint 11-6** = A40 Report #15 dedicated wire (A33 forward-lock + A19 cohesion 9 surface).

## Sprint-up scope (3 items — 본 스토리)

### Item 1: A13 residual (2 items — close-out)

**Reference**: 11-4 spec §Task 8 (a) + (c) + §Review Findings + handoff-2026-08-10-11-4-done-final.md §3 18 honestly DEFER.

After 11-4 post-sprint close-out verification cycle (2026-08-10 ~ 2026-08-19 cross-epic retroactive), 16 of 18 DEFER items were **resolved** (mostly by later epic work — Epic 10 retro verification + Sprint 10-1 partial wire + smoke-fix sprint 5 fixes). **Only 2 items remain**.

#### D-001: page.tsx mount — 4 m11_close components

- **Source**: 11-4 D-001 — `apps/web/app/(authenticated)/m2-input/period/[periodKey]/page.tsx` (not created during 11-4 sprint)
- **Current state** (검증 2026-08-19):
  - `apps/web/app/[locale]/(dashboard)/m2-input/period/[periodKey]/page.tsx` — **DOES NOT EXIST** (Glob returned no files)
  - 4 m11_close components exist but never mounted:
    - `apps/web/components/m11-close/SnapshotPersistencePanel.tsx` ✅
    - `apps/web/components/m11-close/ReversalExecuteDialog.tsx` ✅
    - `apps/web/components/m11-close/ReopenOperatorDialog.tsx` ✅
    - `apps/web/components/m11-close/CacheInvalidationChannelBadge.tsx` ✅
- **Wire scope**:
  - NEW `apps/web/app/[locale]/(dashboard)/m2-input/period/[periodKey]/page.tsx` (RSC Server Component, ~30 LOC)
  - 4 m11_close component imports + JSX mount inside `period-info-card` layout block
  - Session/tenant context Server Component layout
  - Error boundary wrapping components (defensive — components have known shape requirements)

#### P-011: dead code deletion

- **Source**: 11-4 P-011 — unused `REOPEN_CACHE_INVALIDATION_CHANNELS` re-export in `apps/web/lib/closing-period.ts:193-196`
- **Current state** (검증 2026-08-19):
  - `apps/web/lib/closing-period.ts:182-196` declares `REOPEN_CACHE_INVALIDATION_CHANNELS` (4-item tuple)
  - Grep across `apps/web/` + `packages/` for symbol returned **ZERO importers**
  - `CacheInvalidationChannelBadge.tsx` only imports `CACHE_INVALIDATION_CHANNELS` (the OTHER export)
- **Wire scope**:
  - DELETE lines 193-196 from `apps/web/lib/closing-period.ts`
  - Grep verify zero importers (final sweep)
  - Optional: Add import-only test (defensive against regression)

### Item 2: A17 — W2 reopen flow AD-25 4-channel verification

**Reference**: Epic 11 close-out retro §7 A17 결정 + `apps/api/modules/m11_close/services/reopen_service.py:48-65` + `apps/api/core/cache_invalidation_publisher.py:47-54`.

W2 reopen flow = `reopen_service.py:209-217` `publisher.publish_multi(channels=list(REOPEN_CHANNELS_W2_SUBSET), ...)` where:
- `REOPEN_CHANNELS_ALL` = 4 channels (`ai_cache` + `cost_engine_cache` + `fiscal_period_cache` + `closing_snapshot_cache`)
- `REOPEN_CHANNELS_W2_SUBSET` = 2 channels (`fiscal_period_cache` + `closing_snapshot_cache`)

A17 = "ai_cache + cost_engine_cache + fiscal_period_cache + closing_snapshot_cache 4-channel 모두 publish 검증" — i.e., explicit AD-25 spec verification that all 4 channels are technically publishable + subset-relationship test.

**Wire scope** (extend `tests/api/m11_close/test_reopen_service.py`):

- 4 NEW test cases:
  1. `test_execute_reopen_calls_publish_multi_with_w2_subset` — spy `CacheInvalidationPublisher.publish_multi` via `unittest.mock.AsyncMock` + assert exact `channels` arg
  2. `test_execute_reopen_publishes_receipts_with_correct_envelope` — receipt shape: `channel ∈ {fiscal_period_cache, closing_snapshot_cache}` + `tenant_id == self.tenant_id` + `target_event_id == fiscal_period_id` + `correction_group_id == fiscal_period_id` + `trace_id == self.trace_id` + `published_at` ISO-8601 parseable
  3. `test_reopen_channels_all_is_superset_of_w2_subset` — explicit subset-relationship assertion: `set(REOPEN_CHANNELS_W2_SUBSET) ⊆ set(REOPEN_CHANNELS_ALL)` + length difference
  4. `test_publish_multi_rejects_non_allowed_channel` — D-7 invariant verification: empty-channel-set error or fail-fast for invalid subset

CR 4-3 lesson 정합 — async test pattern: `def test_* + asyncio.run(_impl())`.

### Item 3: A18 — A5 audit_action drift detector 3-way extension

**Reference**: Epic 11 close-out retro §7 A18 결정 + `apps/api/core/audit_action.py:204-314`.

A18 = "A5 audit_action drift detector 3-way extension (11-1/11-2/11-3 4 ActionClass × 15 values fill)". 4 ActionClass + 15 values inventory:

| ActionClass | 11-X | Values count | Literal values |
|---|---|---|---|
| `REVERSAL_LOG` | 11-1 | 5 | reversal_negating_inserted + reversal_corrected_inserted + reversal_rejected + reversal_unauthorized + m11_reversal_handler_invoked |
| `MONTHLY_CLOSING` | 11-2 | 4 | closing_sequence_initiated + closing_sequence_step_completed + closing_sequence_blocked + closing_sequence_confirmed |
| `SNAPSHOT_PERSISTENCE` | 11-3 | 4 | snapshot_persistence_committed + snapshot_persistence_reversed + snapshot_persistence_blocked + snapshot_persistence_reopened |
| `REOPEN_OPERATOR` | 11-3 | 2 | reopen_authorized + reopen_completed |

Plus `MONTHLY_INPUT_PERIOD` extension (`opening_inventory_unlocked`, 11-1) that drift detector missed.

DB CHECK parity: NONE of these have CHECK constraints:
- `reversal_log.action` has no CHECK per alembic 0019 comment ("AD-22 reversal_log info only (NO action CHECK)")
- `audit_logs.action` has NO CHECK per AD-2 invariant + conventions.md §10.1

So 3-way extension = **registry ↔ call sites** (2-way effective, with explicit DB-N/A documented in test docstring).

**Wire scope** (NEW file `tests/integration/test_audit_action_3way_extension_drift.py`):

- 15 3-way extension cases (5 + 4 + 4 + 2):
  - REVERSAL_LOG 5 cases: registry present + each literal validate succeeds + call site scan `apps/api/modules/m11_close/services/reversal_service.py`
  - MONTHLY_CLOSING 4 cases: same pattern for `close_sequence_service.py`
  - SNAPSHOT_PERSISTENCE 4 cases: same pattern for `snapshot_persistence_service.py` + `reversal_execute_service.py`
  - REOPEN_OPERATOR 2 cases: same pattern for `reopen_service.py:181-184`
- 1 case: MONTHLY_INPUT_PERIOD.opening_unlocked (`monthly_input_period_opening_unlocked`)
- 1 case EXTENSION: `test_service_layer_writers_use_registry_validate` — scan 3 NEW service files (reopen_service.py + close_sequence_service.py + snapshot_persistence_service.py) for `_ActionRegistry.validate()` presence (currently only scans calc_orchestrator.py)

**Total**: 16 NEW test cases.

## Honestly DEFER to Sprint 11-6 (separate story)

| Item | Scope | Reason |
|---|---|---|
| A40 Report #15 wire (활동원가 내역서) | 9 A19 surfaces (kernel + payload schema + backend service/endpoint/schemas/exceptions + frontend page/panel/TS mirror + tests + capability matrix no-change + audit-first AD-22 wire). ~1,500 NEW LOC. | Epic 10 retro A40 framed as "LOW RISK reuse case" but actual wire is substantial (9 surfaces × full A19 cohesion). Per process design risk analysis, dedicated Sprint 11-6 with proper A19 9-surface budget preferred over mixed-scope atomic sprint. A40 option (a) 결정 honored (decision executes, just split into 2 execution sprints). |

## Tasks / Subtasks

본 스토리는 atomic single sprint T1~T8 wire:

- [ ] **Task 1: D-001 page.tsx mount** (AC: #1)
  - [ ] Subtask 1.1: Create `apps/web/app/[locale]/(dashboard)/m2-input/period/[periodKey]/page.tsx` (RSC Server Component)
  - [ ] Subtask 1.2: Mount 4 m11_close components (SnapshotPersistencePanel + ReversalExecuteDialog + ReopenOperatorDialog + CacheInvalidationChannelBadge)
  - [ ] Subtask 1.3: Error boundary wrap components (defensive)
- [ ] **Task 2: P-011 dead code delete** (AC: #2)
  - [ ] Subtask 2.1: DELETE `REOPEN_CACHE_INVALIDATION_CHANNELS` from `apps/web/lib/closing-period.ts:193-196`
  - [ ] Subtask 2.2: Grep verify zero importers (final sweep across `apps/web/` + `packages/`)
- [ ] **Task 3: A17 W2 reopen verification tests** (AC: #3, #4, #5, #6)
  - [ ] Subtask 3.1: `tests/api/m11_close/test_reopen_service.py` EXTENSION — 4 NEW test cases (publish_multi call args + receipt envelope + subset-relationship + non-allowed-channel rejection)
- [ ] **Task 4: A18 audit_action drift detector extension** (AC: #7, #8, #9, #10, #11)
  - [ ] Subtask 4.1: NEW `tests/integration/test_audit_action_3way_extension_drift.py` — 15 cases (5 REVERSAL_LOG + 4 MONTHLY_CLOSING + 4 SNAPSHOT_PERSISTENCE + 2 REOPEN_OPERATOR) + 1 MONTHLY_INPUT_PERIOD.opening_unlocked + 1 service-layer scan EXTENSION
- [ ] **Task 5: T6 docs + sprint-status sync** (AC: #12)
  - [ ] Subtask 5.1: `docs/deferred-work.md` EXTENSION — `## Deferred from: 11-5 (Epic 11 second carry-over sprint)` section
  - [ ] Subtask 5.2: `sprint-status.yaml` 11-5 entry: ready-for-dev → in-progress → done
- [ ] **Task 6: T7 3중 게이트 FINAL CLEAN verification** (AC: #13)
- [ ] **Task 7: T8 atomic commit + memory handoff** (AC: #14)

## Acceptance Criteria

1. **D-001 page.tsx**: `/[locale]/(dashboard)/m2-input/period/[periodKey]` RSC page renders, 4 m11_close components mounted in DOM with `data-testid` attributes
2. **P-011 dead code deletion**: `grep -rn "REOPEN_CACHE_INVALIDATION_CHANNELS" apps packages` returns ZERO matches
3. **A17 test 1**: `test_execute_reopen_calls_publish_multi_with_w2_subset` PASS — `publish_multi(channels=['fiscal_period_cache', 'closing_snapshot_cache'], ...)` exact args verified via AsyncMock spy
4. **A17 test 2**: `test_execute_reopen_publishes_receipts_with_correct_envelope` PASS — receipt shape fully verified (channel + tenant_id + target_event_id + correction_group_id + trace_id + published_at ISO-8601)
5. **A17 test 3**: `test_reopen_channels_all_is_superset_of_w2_subset` PASS — subset-relationship explicitly verified
6. **A17 test 4**: `test_publish_multi_rejects_non_allowed_channel` PASS — non-allowed-channel rejection enforced
7. **A18 test 1**: 5 NEW REVERSAL_LOG registry + call site cases PASS
8. **A18 test 2**: 4 NEW MONTHLY_CLOSING registry + call site cases PASS
9. **A18 test 3**: 4 NEW SNAPSHOT_PERSISTENCE registry + call site cases PASS
10. **A18 test 4**: 2 NEW REOPEN_OPERATOR registry + call site cases PASS
11. **A18 test 5 + 6**: 1 MONTHLY_INPUT_PERIOD.opening_unlocked case + 1 service-layer scan EXTENSION PASS
12. **Docs sync**: `docs/deferred-work.md` 11-5 section present + `sprint-status.yaml` 11-5 status: done
13. **3중 게이트 FINAL CLEAN**: ruff scoped 0 NEW + ruff full 0 NEW (CR 11-4 lesson) + import-linter 2 KEPT 0 broken + pytest focused 24 NEW PASS + vitest baseline preserved + tsc zero NEW + A36 SDR 4-step PASS
14. **Atomic commit + memory handoff**: `git commit -F <file>` (NOT PowerShell here-string per CR 9-6 D5 prevention) + separate memory handoff commit

## Dev Notes

### CR 11-3 lessons applied

1. **ALLOWED_SERVICE_SUBMODULES sweep 즉시** — 본 스토리는 frontend page + dead-code delete + tests only → service module 추가 無 → allowlist 변경 불요요
2. **ruff scoped auto-fix sweep 일괄** — wire file 작성 직후 `uv run ruff check <files> --fix` 한 번에 해결
3. **CR 4-3 fix script sweep** — async test pattern: `def test_X(args) -> None: ... async def _impl() -> None: ... asyncio.run(_impl())` 변환
4. **SDR MAX claim separate line** — "**N tests collected**" 별도 line (parser unambiguous)
5. **abnormal-halt recovery checkpoint** — T1~TN partial done 시점에 commit → 후속 fix는 별도 commit 분리

### CR 11-4 lessons applied

1. **page.tsx mount discipline** — components MUST be actually mounted (D-001), not just created
2. **ko-KR.json SSOT** — `apps/web/messages/ko-KR.json` ONLY, no `apps/web/lib/ko-KR.json` (D-002 already resolved by deletion guard)
3. **TS mirror unknown state** — explicit `return {authorized: false, ...}` for unknown/malformed input (D-005 resolved)

### CR 11-2 lessons applied

1. **AUTHORIZABLE_TARGET_EVENT_TYPES auth-layer divergence sweep** — A17 test 1 publish_multi spy catches this pattern
2. **ALLOWED_SERVICE_SUBMODULES sweep** — N/A (no service module addition)
3. **SDR parser line trick** — separate line for unambiguous parser match
4. **post-sweep fix commit** — sweep done 후 별도 commit
5. **abnormal-halt recovery** — checkpoint pattern

### Critical Path

1. **page.tsx 작성 직후**: `pnpm exec tsc --noEmit` 0 errors 검증 (TS component import 정합 fail-fast)
2. **page.tsx 작성 직후**: `pnpm exec vitest run apps/web/components/m11-close/*.test.tsx -v` baseline 회귀 0건 검증 (CR 11-4 lesson pre-existing test 보존)
3. **dead code delete 직후**: `grep -rn "REOPEN_CACHE_INVALIDATION_CHANNELS" apps packages` ZERO matches
4. **A17 test 작성 직후**: `pytest tests/api/m11_close/test_reopen_service.py -v -k "publish_multi"` 4 NEW cases PASS + baseline 회귀 0건
5. **A18 test 작성 직후**: `pytest tests/integration/test_audit_action_3way_extension_drift.py -v` 16 NEW cases PASS + baseline 회귀 0건

### Critical Path Before 11-5 dev-story

없음. baseline_commit = `dc85ab9` 그대로 사용. 모든 wire는 incremental T1~T8 atomic commit 진입.

## Testing Standards

- pytest: 4 NEW A17 cases + 16 NEW A18 cases = **20 NEW pytest cases**
- vitest: **0 NEW** (A13 D-001 = page.tsx mount of existing components; no new components in this sprint)
- playwright: **0 NEW** (D-001 mount 보존; follow-up sweep 가능)
- import-linter: 2 KEPT (no new service submodule)
- A5 drift detector: 16 NEW cases (= 4 ActionClass × 15 values 3-way extension)

## Open Questions

- **OQ-11-5-1**: A40 Report #15 wire Sprint 11-6 진입 시점 — 본 스토리 close-out 직후 OR Epic 12 12-1 carry-over sprint 진입 후 (사용자 결정 대기)
- **OQ-11-5-2**: A38 frontend test debt dedicated sprint 진입 시점 — Epic 10 close-out 후 즉시 OR Sprint 11-6 진입 후 (사용자 결정 대기)
- **OQ-11-5-3**: A39 LISTEN/NOTIFY separate epic 진입 시점 — 차기 epic territory 진입 결정 (사용자 결정 대기)
