---
title: Epic 11 Carry-Over Sprint — 11-3 honestly DEFER 3 items sprint-up
status: ready-for-dev
priority: HIGH
epic: 11
story_num: 4
story_key: 11-4-epic-11-carry-over-sprint
baseline_commit: 4e4e8d6
created: 2026-08-09
---

# Story 11.4 — Epic 11 Carry-Over Sprint (A13 sprint-up)

> **Epic 11 close-out retro (2026-08-09) §7 A13 결정**: 11-3 honestly DEFER 8 items 중 **3 items sprint-up 결정** — T8 frontend (HIGH) + V8 22→26 골든 fixture matrix extension (MEDIUM) + capability matrix v1.12 fill (MEDIUM). 나머지 5 items honestly DEFER to follow-up sweep.
>
> **baseline_commit = 4e4e8d6** (Story 11.3 bmad-code-review 3rd sweep done tip).
>
> **Full scope reference**: [`_bmad-output/implementation-artifacts/11-3-snapshot-persistence-with-reverse.md`](./11-3-snapshot-persistence-with-reverse.md) §Honestly DEFER section + §Review Findings §DEFER subsection + §Tasks / Subtasks §Task 8 (subtask 8.1–8.26) + §AC #7 carry-over.

## Epic context

Epic 11 cj-style 3-story 분할 (Epic 5 close-out retro §6 W1) 모두 done 진입:

- **11-1** = M11 module authority + AD-22 reversal ledger wire + A9 fill + H6 fix + AD-25 1-channel ✅ done (commit `b4961a6`)
- **11-2** = close-sequence-lock ✅ done (commit `caacfc7`)
- **11-3** = snapshot-persistence-with-reverse ✅ done (commit `4e4e8d6`, 3rd sweep done)

Epic 11 close-out retro (cj-style 7-section lightweight, 2026-08-09) 완료. epic-11: in-progress → done. epic-11-retrospective: optional → done. 6 NEW action items A13–A18 appended. **A13 본문 = 본 스토리 scope**.

## Sprint-up scope (3 items — 본 스토리)

### Item 1: T8 frontend (HIGH priority)

**Reference**: 11-3 spec §Task 8 (a) + (c) + subtask 8.1–8.20.

#### TS mirrors (carry from 11-2 DEFER + 11-3 NEW)

- `apps/web/lib/m11-close-sequence.ts` (NEW TS mirror, ~150 lines) — close_sequence_order + close_sequence_state + check_ad6_insert_allowed (11-2 AC #2 (c) + §AC #4 (d) wire)
- `apps/web/lib/m11-close-sequence-parity.ts` (NEW TS parity test, ~120 lines) — Python pure kernel ↔ TS mirror 5 cases
- `apps/web/lib/m11-snapshot-persistence.ts` (NEW TS mirror, ~150 lines) — commit_snapshot_persistence TS mirror
- `apps/web/lib/m11-reversal-execute.ts` (NEW TS mirror, ~150 lines) — reversal_execute_snapshot TS mirror
- `apps/web/lib/m11-reopen.ts` (NEW TS mirror, ~150 lines) — reopen_authorization TS mirror
- `apps/web/lib/closing-period.ts` (EXTENSION, ~30 lines) — SnapshotPersistenceState + ReversalExecuteState + ReopenState + CacheInvalidationChannel TS types

#### 4 NEW 11-3 frontend components

- `apps/web/components/m11-close/SnapshotPersistencePanel.tsx` (NEW shadcn Card + step indicator + sonner toast, ~200 lines)
- `apps/web/components/m11-close/ReversalExecuteDialog.tsx` (NEW shadcn Dialog + ReversalForm + sonner toast, ~250 lines)
- `apps/web/components/m11-close/ReopenOperatorDialog.tsx` (NEW shadcn Dialog + OperatorActionSelect + ReasonTextarea + sonner toast, ~250 lines)
- `apps/web/components/m11-close/CacheInvalidationChannelBadge.tsx` (NEW shadcn Badge + channel icon, ~120 lines)

#### 11-2 carry-over frontend components

- `apps/web/components/m11-close/CloseSequencePanel.tsx` (NEW shadcn Card + StepIndicator + progress bar, ~180 lines)
- `apps/web/components/m11-close/CloseSequenceStepCompleteButton.tsx` (NEW shadcn Button + sonner toast, ~100 lines)
- `apps/web/components/m11-close/CloseSequenceConfirmButton.tsx` (NEW shadcn Button + shadcn Dialog + sonner toast, ~120 lines)

#### ko-KR.json + page wire

- `apps/web/ko-KR.json` (EXTENSION, ~80 lines) — 12 NEW strings (snapshot persistence + reversal + reopen + cache invalidation 4 channels)
- `apps/web/app/(authenticated)/m2-input/period/[periodKey]/page.tsx` (EXTENSION) — 4 NEW frontend components 진입점

#### Vitest + Playwright

- vitest 7 NEW files (TS mirror parity × 5 cases + 11-2 carry-over × 5 cases + 11-3 components × 5+5+5=15 cases)
- Playwright 4 NEW E2E scenarios (snapshot_persistence 4 + reversal_execute 4 + reopen 4 + close_sequence 4 carry-over)

### Item 2: V8 22→26 골든 fixture matrix extension (MEDIUM)

**Reference**: 11-3 spec §Task 8 (b) + subtask 8.21–8.26.

- `packages/cost_engine/tests/regression_v8/fixtures/snapshot_committed.json` (NEW 골든 fixture, ~50 lines)
- `packages/cost_engine/tests/regression_v8/fixtures/reversal_negating_snapshot.json` (NEW 골든 fixture, ~50 lines)
- `packages/cost_engine/tests/regression_v8/fixtures/reversal_corrected_snapshot.json` (NEW 골든 fixture, ~50 lines)
- `packages/cost_engine/tests/regression_v8/fixtures/reopen_committed.json` (NEW 골든 fixture, ~50 lines)
- `tests/regression_v8/test_regression_v8_fixtures.py` (EXTENSION, ~80 lines) — V8 22 → 26 fixture matrix extension
- `packages/cost_engine/tests/regression_v8/README.md` (EXTENSION, ~30 lines) — 4 NEW 골든 fixture 명세

V8 byte-identical CI gate = Story 4-4 pattern 동일. CR 4-4 lesson 정합:
- tenant-scoped result_hash
- golden_diff shape 결정
- 0.5 plumbing 결정 (이미 done)
- 4 industries × verification matrix consistency

### Item 3: capability matrix v1.12 fill (MEDIUM)

**Reference**: 11-3 spec §Task 6 + §AC #5 + §Task 10 Subtask 10.8.

- `apps/api/core/capability.py` (EXTENSION, ~50 lines) — 3 NEW capabilities:
  - `Capability.SNAPSHOT_PERSISTENCE` (manufacturing 3종 ✅ / service-only ❌)
  - `Capability.REVERSAL_EXECUTE` (manufacturing 3종 ✅ / service-only ❌)
  - `Capability.REOPEN_OPERATOR` (manufacturing 3종 ✅ / service-only ❌, AD-10 owner-only role gate 동반)
- `apps/api/modules/m11_close/handlers.py` (EXTENSION) — 4 NEW routes capability gate wire
- `docs/capability-matrix.md` (EXTENSION) — 3 NEW capability 행 추가 (4 industries × 15+ capabilities 정합성)
- `tests/integration/test_capability_matrix_drift.py` (EXTENSION, ~30 lines) — 3 NEW capability gate cases

CR 4-3 lesson 정합: A5 forward-lock + capability × type matrix 8번째 epic 연속 자산.

## Honestly DEFER to follow-up sweep (5 items)

본 스토리 scope 외. follow-up sweep 또는 Epic 12 진입 시점에 결정.

| Item | Scope | Priority |
|---|---|---|
| T10 docs | `docs/snapshot-persistence-with-reverse.md` NEW + 8 EXTENSION (architecture-inventory + monthly-input + closing-period + audit-actions + conventions §10 + closing-guard + capability-matrix + reversal-sequence) | LOW |
| A5 partial wire (audit_action rename refactor) | 11-3 A5 partial wire 완료 → extension sweep | LOW |
| fiscal_period_snapshots.state='committed'→'reopened' full transition | state machine extension | LOW |
| reopen_audit_id != fiscal_period_id (separate reopen audit row) | audit table 분할 | LOW |
| D1 reversal V8 fixtures (3 NEW 골든) | fixture matrix extension 26→29 | LOW |

## Tasks / Subtasks

본 스토리는 A13 carry-over 스프린트로 기존 11-3 §Task 8에서 일부만 재사용. 새로운 task 분할:

- [ ] **Task 1: T8 frontend — TS mirrors + 4 NEW components + 11-2 carry-over 3 components + ko-KR.json + vitest + Playwright** (AC: #1, #2, #3, #4)
  - [ ] Subtask 1.1: TS mirrors 5 NEW files (`apps/web/lib/m11-close-sequence.ts` + `m11-close-sequence-parity.ts` + `m11-snapshot-persistence.ts` + `m11-reversal-execute.ts` + `m11-reopen.ts`)
  - [ ] Subtask 1.2: 4 NEW 11-3 components (SnapshotPersistencePanel + ReversalExecuteDialog + ReopenOperatorDialog + CacheInvalidationChannelBadge)
  - [ ] Subtask 1.3: 11-2 carry-over 3 components (CloseSequencePanel + StepCompleteButton + ConfirmButton)
  - [ ] Subtask 1.4: ko-KR.json 12 NEW strings + page.tsx EXTENSION 진입점
  - [ ] Subtask 1.5: vitest 7 NEW files (parity + components + carry-over)
  - [ ] Subtask 1.6: Playwright 4 NEW E2E scenarios
- [ ] **Task 2: V8 22→26 골든 fixture matrix extension** (AC: #5)
  - [ ] Subtask 2.1: 4 NEW 골든 fixtures (snapshot_committed + reversal_negating_snapshot + reversal_corrected_snapshot + reopen_committed)
  - [ ] Subtask 2.2: test_regression_v8_fixtures EXTENSION (V8 22→26)
  - [ ] Subtask 2.3: README.md EXTENSION (4 NEW fixture 명세)
- [ ] **Task 3: capability matrix v1.12 fill** (AC: #6)
  - [ ] Subtask 3.1: `apps/api/core/capability.py` EXTENSION (3 NEW capabilities)
  - [ ] Subtask 3.2: handlers.py capability gate wire (4 NEW routes)
  - [ ] Subtask 3.3: `docs/capability-matrix.md` EXTENSION (3 NEW rows)
  - [ ] Subtask 3.4: test_capability_matrix_drift EXTENSION (3 NEW cases)

## Acceptance Criteria

1. **T8 frontend TS mirrors**: 5 NEW TS mirror files (`m11-close-sequence.ts` + parity + 11-3 NEW 3 files) + parity test 5 cases × 4 = 20 parity cases pass
2. **T8 frontend components**: 4 NEW 11-3 components + 3 carry-over 11-2 components 모두 wire, vitest 5+5+5+5+5+5+5 = 35 cases pass
3. **T8 frontend E2E**: Playwright 4 NEW scenarios (snapshot_persistence 4 + reversal_execute 4 + reopen 4 + close_sequence 4) = 16 scenarios pass
4. **T8 frontend ko-KR.json + page wire**: 12 NEW strings + page 진입점 모두 wire
5. **V8 22→26 fixture matrix**: 4 NEW 골든 fixtures + test_regression_v8_fixtures EXTENSION (22→26) 모두 byte-identical pass
6. **capability matrix v1.12 fill**: 3 NEW capabilities (SNAPSHOT_PERSISTENCE + REVERSAL_EXECUTE + REOPEN_OPERATOR) wired + drift detector 3 NEW cases pass

## Dev Notes

### CR 11-3 lessons applied

1. **ALLOWED_SERVICE_SUBMODULES sweep 즉시** — service file 작성 직후 architecture test fail-fast로 allowlist 누락 감지
2. **ruff scoped auto-fix sweep 일괄** — 27 errors (W292 + UP038 + SIM300 + SIM222 + ERA001) → `uv run ruff check <files> --fix` 한 번에 해결
3. **CR 4-3 fix script sweep** — `@pytest.mark.asyncio` decorator + missing def line 패턴 → `def test_X(args) -> None: ... async def _impl() -> None: ... asyncio.run(_impl())` 변환
4. **SDR MAX claim separate line** — "**N tests collected**" 별도 line (parser unambiguous)
5. **abnormal-halt recovery checkpoint** — T1~TN partial done 시점에 commit → 후속 fix는 별도 commit 분리

### CR 11-2 lessons applied

1. **AUTHORIZABLE_TARGET_EVENT_TYPES auth-layer divergence sweep** — 11-2 3rd sweep D2 wire 시점에 pattern 정합
2. **ALLOWED_SERVICE_SUBMODULES sweep** — 본 스토리는 frontend + fixture + capability wire로 backend service module 추가 無 (TS mirror + frontend만 추가) → allowlist 변경 불요요
3. **SDR parser line trick** — separate line for unambiguous parser match
4. **post-sweep fix commit** — sweep done 후 별도 commit
5. **abnormal-halt recovery** — checkpoint pattern

### Critical Path

1. **TS mirror 작성 직후**: `pnpm exec tsc --noEmit` 0 errors 검증 (cross-language parity fail-fast)
2. **fixture 작성 직후**: `pytest tests/regression_v8 -v` byte-identical CI gate 검증
3. **capability 추가 직후**: `pytest tests/integration/test_capability_matrix_drift.py` drift detector 검증
4. **frontend component 작성 직후**: `pnpm exec vitest run <file>` + `pnpm exec playwright test <spec>` 검증

### Critical Path Before 11-4 dev-story

없음. baseline_commit = 4e4e8d6 그대로 사용. 모든 wire는 이미 11-3 commit에서 done.

## Testing Standards

- vitest: TS mirror parity 5 cases × 4 files = 20 + frontend components 5+5+5+5+5+5+5 = 35 cases + 11-2 carry-over 5+5+5 = 15 cases = **70 NEW vitest cases**
- Playwright: 16 NEW E2E scenarios (4 components × 4 scenarios)
- pytest: 4 NEW V8 골든 fixture cases + 3 NEW capability matrix drift cases = **7 NEW pytest cases**
- A5 drift detector: 0 NEW (capability v1.12 자체는 이미 A5 forward-lock 패턴 = registry ↔ DB CHECK ↔ call sites 3-way)

**MAX SDR claim 갱신**: 1758 → ~1823 (+65 NEW tests from 6-3 wire, separate line for unambiguous parser match per CR 11-2 lesson)

## 3중 게이트 final clean (mandatory CI)

- ruff scoped (11-4 surface ~30 files) → All checks passed
- import-linter (변경 無 — TS mirror + frontend만 wire) → 2 KEPT 0 broken
- pytest (1758 baseline + 65 NEW from 6-3 wire = **1823 passed + 127 skipped + 0 failed**)
- tsc (5 NEW TS mirrors + 4 NEW components) → 0 errors
- vitest (70 NEW cases) → 70/70 pass
- Playwright E2E (16 NEW scenarios) → 16/16 pass
- SDR drift detector → MAX 1758 → 1823 separate line 갱신 (6-3 wire carry-over)

**MAX SDR claim 갱신**: 1758 → 1823 (6-3 wire +65 NEW tests = separate line)

## References

- [Source: `_bmad-output/implementation-artifacts/11-3-snapshot-persistence-with-reverse.md` §Honestly DEFER + §Task 8 + §AC #7]
- [Source: `_bmad-output/implementation-artifacts/11-2-close-sequence-lock.md` §carry-over DEFER 4 items]
- [Source: `_bmad-output/implementation-artifacts/11-1-m11-reversal-ledger.md` §M11 module authority + AD-22 wire]
- [Source: `_bmad-output/implementation-artifacts/epic-11-retro-2026-08-09.md` §7 A13 결정]
- [CR 11-3 lesson: [[cr-11-3-lessons]]]
- [CR 11-2 lesson: [[cr-11-2-lessons]]]
- [CR 4-3 lesson (async test pattern): [[cr-4-3-lessons]]]
- [CR 4-4 lesson (V8 fixture matrix): [[cr-4-4-lessons]]]

## Dev Agent Record

### Agent Model Used
(pending dev-story execution)

### Debug Log References
(pending dev-story execution)

### Completion Notes List
(pending dev-story execution)

### File List
(pending dev-story execution)

## Review Findings
(pending bmad-code-review execution — recommend R4 triage + carry-over + 3rd sweep pattern)