---
title: A38 Frontend Test Debt Dedicated Sprint (Epic 10 close-out carry-over 14번째)
status: ready-for-dev
priority: HIGH
epic: 10
story_num: 5
story_key: 10-5-a38-frontend-test-debt-dedicated
baseline_commit: 197c96d
created: 2026-08-19
updated: 2026-08-19
---

> **A38 결정 wire** (Epic 10 close-out retro 2026-08-19 §7 A38 신규 결정 + Epic 10 close-out retro §11.2 명시 "A38 ... cj-style carry-over 14번째 진입 (retro closed 후 즉시)"). 본 스토리는 A38 = A35 frontend test debt honestly DEFER (d) dedicated sprint = Epic 10 4 stories (10-1 + 10-2 + 10-3 + 10-4) 모두 frontend test debt 일괄 해소.
>
> **baseline_commit = `197c96d`** (Sprint 11-6 spec entry tip = Epic 10 close-out retro wire done 진입 후 진입점; cj-style 35번째 = Epic 10 retro done `f575766` → cj-style 37번째 = Sprint 11-6 spec entry `197c96d` → THIS A38 spec entry = cj-style 38번째 epic 연속 정직 회복 진입점).
>
> **cj-style carry-over 14번째 검증** (cj-style 9번째 = 9-5 Epic 9 close-out follow-up + cj-style 10번째 = 9-6 Epic 9 close-out retro + cj-style 11번째 = 9-7 Epic 9 frontend test debt follow-up + cj-style 12번째 = smoke-fix sprint + cj-style 13번째 = 9-7 carry-over (재진) + cj-style 14번째 = THIS A38 frontend test debt dedicated).

# Story 10.5 — A38 Frontend Test Debt Dedicated Sprint

## Epic context

**Epic 10 close-out retro** (cj-style 5번째 진입점, 2026-08-19) 완료. **A38 결정 wire** (Epic 10 retro §7 신규 결정 A37~A42 중 A38):
- **A38** = A35 frontend test debt dedicated sprint (cj-style carry-over 14번째)
- Owner: Amelia + Dana
- Wire scope: Epic 10 4 stories frontend files + TS mirror parity + vitest mount 일괄 wire
- Estimated: ~12 frontend files + 4 vitest mount + 3 TS mirror parity = **~19 files**

**Epic 9 close-out retro** (cj-style 5번째 진입점, 2026-08-17) A35 결정:
- **A35** = frontend test debt honestly DEFER (d) + 9-7 follow-up sprint 진입 (cj-style carry-over 11번째, 24번째 epic 연속)
- 9-7 wire: 5 NEW vitest component tests + 3 NEW TS mirror parity tests + 1 MODIFIED `apps/web/mocks/handlers.ts` = 18 files / 105 NEW vitest cases

**Epic 10 PRD entry** (cj-style 25번째, 2026-08-17) capability matrix v1.20 → v1.21 (`AI_INSIGHT` capability 1 NEW, industry-agnostic, 4-industry grants ✅/✅/✅/✅).

**Epic 10 4 stories 모두 A34 4-category honestly DEFER (d) preserved** (cj-style 28~34번째 epic 연속):
- 10-1: D-10-1-DEFER-3 (T5 frontend 8 files = AiDraftCard + ConfidenceBadge + AiExtractModal + ko-KR.json + 2 vitest mount + TS mirror + parity)
- 10-2: D-10-2-DEFER-4 (T6 frontend 7 files = insight cache UI + 3 TS mirror parity + vitest mount + ko-KR.json)
- 10-3: D-10-3-DEFER-4 (T8 frontend 7 files = 2 badge components + 1 comment section + 2 vitest mount + 1 TS mirror + 1 ko-KR.json + 1 cross-language drift detector test)
- 10-4: D-10-4-DEFER-4 (T5 frontend 5 files = PromoteConfirmButton + PromoteResultToast + 2 vitest mount + 1 ko-KR.json)

## Sprint scope (cj-style atomic T1~T8)

### T1 — 10-1 frontend test debt 해소 (D-10-1-DEFER-3)

**Wire scope** (~9 files):
- 3 NEW components (CR 11-4 D-001 page.tsx actual mount MUST):
  - `apps/web/components/m10-ai/AiDraftCard.tsx` (10-1 monthly extraction draft display)
  - `apps/web/components/m10-ai/ConfidenceBadge.tsx` (extraction confidence badge)
  - `apps/web/components/m10-ai/AiExtractModal.tsx` (monthly extraction modal form)
- 1 NEW ko-KR.json extension: `apps/web/messages/ko-KR.json` `ai_extract` namespace ~25 strings SSOT (CR 11-4 D-002)
- 2 NEW vitest mount tests: `apps/web/__tests__/components/m10-ai.AiDraftCard.test.tsx` + `ConfidenceBadge.test.tsx` + `AiExtractModal.test.tsx`
- 1 NEW TS mirror parity test: `apps/web/__tests__/lib/ai-extract-parity.test.ts` (AD-15 cross-language parity, source_kind Literal + extraction_confidence threshold)
- 1 NEW page.tsx: `apps/web/app/[locale]/(dashboard)/monthly-input/ai-extract/page.tsx` (CR 11-4 D-001 mount MUST)

**Tests**: ~28 NEW vitest cases (3 components × 6 + 1 parity × 4 + 1 mount × 4 = ~28)

### T2 — 10-2 frontend test debt 해소 (D-10-2-DEFER-4)

**Wire scope** (~7 files):
- 1 NEW component: `apps/web/components/m10-ai/InsightCachePanel.tsx` (10-2 AI insight cache UI)
- 1 NEW ko-KR.json extension: `apps/web/messages/ko-KR.json` `insight_cache` namespace ~15 strings SSOT
- 3 NEW TS mirror parity tests: `apps/web/__tests__/lib/insight-cache-parity.test.ts` (3 parity cases × 2 vectors = 6 cases) — SourceKind Literal + InsightKind Literal + INSIGHT_KIND_VALUES frozenset parity
- 1 NEW page.tsx: `apps/web/app/[locale]/(dashboard)/ai/insights/page.tsx` (CR 11-4 D-001 mount)
- 1 NEW vitest mount test: `apps/web/__tests__/components/m10-ai.InsightCachePanel.test.tsx`

**Tests**: ~12 NEW vitest cases (mount × 4 + parity × 6 + InsightListResponse × 2 = ~12)

### T3 — 10-3 frontend test debt 해소 (D-10-3-DEFER-4)

**Wire scope** (~8 files):
- 2 NEW components:
  - `apps/web/components/m10-ai/AiReferenceBadge.tsx` (보라 배지 '🤖 AI 참고(검증 필요)')
  - `apps/web/components/m10-ai/AutoAnalysisBadge.tsx` (파란 배지 '📊 자동 분석')
  - `apps/web/components/m10-ai/AiCommentSection.tsx` (auto_analysis 의견 표시)
- 1 NEW ko-KR.json extension: `apps/web/messages/ko-KR.json` badge labels + tooltip 'AI는 비권위적입니다 — 확정 책임은 사용자에게' SSOT
- 2 NEW vitest mount tests: `apps/web/__tests__/components/m10-ai.AiReferenceBadge.test.tsx` + `AutoAnalysisBadge.test.tsx` + `AiCommentSection.test.tsx`
- 1 NEW TS mirror parity test: `apps/web/__tests__/lib/ai-comment-parity.test.ts` (SourceKind Literal parity + auto_analysis read-only guard)
- 1 NEW cross-language drift detector test: `apps/web/__tests__/lib/ai-comment-cross-lang-drift.test.ts` (CR 12-5 D-13 EXTENSION)
- 1 NEW page.tsx: `apps/web/app/[locale]/(dashboard)/ai/comments/page.tsx` (CR 11-4 D-001 mount)

**Tests**: ~22 NEW vitest cases (3 components × 6 + 1 parity × 4 + 1 drift × 4 = ~22)

### T4 — 10-4 frontend test debt 해소 (D-10-4-DEFER-4)

**Wire scope** (~5 files):
- 2 NEW components:
  - `apps/web/components/m10-ai/PromoteConfirmButton.tsx` (M2-only trigger + PIPA gate + capability gate 3-layer)
  - `apps/web/components/m10-ai/PromoteResultToast.tsx` (Discriminated union 7 variants result display)
- 1 NEW ko-KR.json extension: `apps/web/messages/ko-KR.json` promote error messages + status labels SSOT
- 2 NEW vitest mount tests: `apps/web/__tests__/components/m10-ai.PromoteConfirmButton.test.tsx` + `PromoteResultToast.test.tsx`

**Tests**: ~24 NEW vitest cases (2 components × 8 + 1 integration mount × 8 = ~24)

### T5 — Shared frontend integration

**Wire scope** (~3 files):
- 1 NEW shared type: `apps/web/lib/m10-ai-types.ts` (SourceKind + InsightKind + PromoteStatus type aliases, CR 11-4 D-005 unknown state reject)
- 1 NEW ko-KR.json drift detector: `apps/web/__tests__/lib/ko-kr-json-ssot-drift.test.ts` (CR 11-4 P-015 EXTENSION — 4 namespaces 모두 drift 0건 검증)
- 1 NEW shared mocks: `apps/web/mocks/m10-ai-handlers.ts` (8 endpoints mock: extract-monthly + insights + comments + promote + 4 GET variants)

**Tests**: ~16 NEW vitest cases (drift × 4 + mock coverage × 12 = ~16)

### T6 — docs + sprint-status sync + handoff memory

**Wire scope** (~3 files):
- `apps/web/messages/ko-KR.json` SSOT consolidation (P-015 drift detector EXTENSION)
- `_bmad-output/implementation-artifacts/deferred-work.md` D-10-1-DEFER-3 + D-10-2-DEFER-4 + D-10-3-DEFER-4 + D-10-4-DEFER-4 = 4 items ✅ RESOLVED
- `_bmad-output/implementation-artifacts/sprint-status.yaml` 10-5-a38-frontend-test-debt-dedicated: ready-for-dev → in-progress → done
- `C:\Users\c8rom\.claude\projects\C--Users-c8rom-desktop-costmgr\memory\handoff-2026-08-19-a38-done.md` (NEW)

### T7 — 3중 게이트 FINAL CLEAN

**Test coverage**:
- vitest: ~102 NEW cases (T1 28 + T2 12 + T3 22 + T4 24 + T5 16) = **~102 NEW vitest cases total**
- Playwright: 0 NEW (E2E는 Epic 12 12-5 T6 패턴 follow-up sprint 결정 후속)
- pytest: 0 NEW (A38 frontend only, backend tests 보존)

**3중 게이트 verification**:
1. **Backend 3중 게이트**: 영향 0건 (A38 frontend only) — backend 3중 게이트 baseline 보존
2. **Frontend tests**: 102 NEW vitest cases ALL PASS + ko-KR.json SSOT drift detector PASS (P-015)
3. **Cross-language parity**: 3 NEW TS mirror parity tests PASS + 1 NEW cross-language drift detector test EXTENSION (CR 12-5 D-13)
4. **A36 SDR 검증 4-step 자동 적용**:
   - commit prefix lint PASS (D5 fix DONE, `git commit -F <file>` 패턴 사용)
   - sprint-status structure 정합 (D4 fix DONE, 10-5 entry development_status 블록 line 274 후 위치)
   - vitest file count drift 0건 (D2 자동화 — ~102 NEW cases + 기존 baseline 합산)
   - commit consistency 정합 (D1 자동화 — sprint-status entry ↔ commit message wire 표)

### T8 — atomic commit close-out + cj-style discipline 보존

**atomic single sprint** (cj-style 14번째 carry-over / cj-style 38번째 epic 연속):
- partial wire 시도 0건
- 단일 commit `git commit -F <commit-msg>` 패턴 (CR 9-6 D5 prevention)
- 19 files atomic (12 NEW + 7 MODIFIED)
- pre-commit 3중 게이트 FINAL CLEAN verification
- commit message 형식: `Story 10.5 (cj-style Epic 10 carry-over 14번째 = cj-style 38번째 epic 연속): A38 frontend test debt dedicated sprint atomic wire T1~T8 DONE — Epic 10 4 stories (10-1 + 10-2 + 10-3 + 10-4) frontend test debt 일괄 해소`

## Acceptance Criteria

### AC #1 — 10-1 frontend test debt 해소
- AiDraftCard + ConfidenceBadge + AiExtractModal 3 NEW components wire + page.tsx actual mount
- 2 NEW vitest mount tests PASS (~28 cases)
- 1 NEW TS mirror parity test PASS (extraction_confidence threshold parity)
- ko-KR.json `ai_extract` namespace ~25 strings SSOT (CR 11-4 D-002)
- D-10-1-DEFER-3 ✅ RESOLVED

### AC #2 — 10-2 frontend test debt 해소
- InsightCachePanel 1 NEW component + page.tsx actual mount
- 1 NEW vitest mount test + 3 NEW TS mirror parity tests PASS (~12 cases)
- ko-KR.json `insight_cache` namespace ~15 strings SSOT
- D-10-2-DEFER-4 ✅ RESOLVED

### AC #3 — 10-3 frontend test debt 해소
- AiReferenceBadge + AutoAnalysisBadge + AiCommentSection 3 NEW components wire + page.tsx actual mount
- 3 NEW vitest mount tests + 1 NEW TS mirror parity test + 1 NEW cross-language drift detector test PASS (~22 cases)
- ko-KR.json badge labels + tooltip 'AI는 비권위적입니다 — 확정 책임은 사용자에게' SSOT
- D-10-3-DEFER-4 ✅ RESOLVED

### AC #4 — 10-4 frontend test debt 해소
- PromoteConfirmButton + PromoteResultToast 2 NEW components wire
- 2 NEW vitest mount tests PASS (~24 cases, 3-layer defense + 7-variant Discriminated union)
- ko-KR.json promote error messages + status labels SSOT
- D-10-4-DEFER-4 ✅ RESOLVED

### AC #5 — Shared frontend integration
- 1 NEW m10-ai-types.ts (SourceKind + InsightKind + PromoteStatus type aliases)
- 1 NEW ko-KR.json SSOT drift detector EXTENSION (P-015, 4 namespaces 모두 검증)
- 1 NEW shared mocks (8 endpoints)
- 16 NEW vitest cases PASS

### AC #6 — 3중 게이트 FINAL CLEAN + A36 SDR 4-step
- vitest ~102 NEW cases ALL PASS
- backend 3중 게이트 baseline 보존 (frontend only sprint)
- A36 SDR 검증 4-step 자동 PASS (commit prefix lint + sprint-status structure + vitest file count drift + commit consistency)
- ko-KR.json SSOT drift detector PASS (P-015)
- partial wire 시도 0건 + cj-style atomic single sprint T1~T8

## Honestly DEFER to follow-up sweep (A34 4-category framework)

본 스토리 scope 외. follow-up sweep 또는 Epic 12 진입 시점에 결정.

| Item | Category | Scope | Reason |
|---|---|---|---|
| A37 master PRD v2.0 본체 edit | (a) docs 정합 | docs only atomic wire | cj-style carry-over 15번째 후속 |
| Report #16 wire (A30 SHARED factory reuse 2nd case) | (c) separate epic | 동일 A30 SHARED factory reuse 2nd case | cj-style Epic 11 7번째 진입점 또는 Epic 12 territory |
| Epic 11 carry-over sprint (A13 residual + A17 + A18) | (b) retro input + (a) docs 정합 | carry-over sprint | cj-style Epic 11 6번째 진입점 = Sprint 11-7 |
| Playwright E2E for m10-ai | (d) dedicated sprint | follow-up sprint | 12-5 T6 패턴 follow-up |

## Tasks / Subtasks

본 스토리는 atomic single sprint T1~T8 wire:

- [ ] **Task 1: T1 — 10-1 frontend test debt 해소** (AC: #1)
  - [ ] Subtask 1.1: 3 NEW components (AiDraftCard + ConfidenceBadge + AiExtractModal)
  - [ ] Subtask 1.2: 1 NEW page.tsx (CR 11-4 D-001 mount MUST)
  - [ ] Subtask 1.3: 1 NEW ko-KR.json `ai_extract` namespace (~25 strings)
  - [ ] Subtask 1.4: 2 NEW vitest mount tests (~28 cases)
  - [ ] Subtask 1.5: 1 NEW TS mirror parity test (extraction_confidence threshold)
- [ ] **Task 2: T2 — 10-2 frontend test debt 해소** (AC: #2)
  - [ ] Subtask 2.1: 1 NEW component (InsightCachePanel)
  - [ ] Subtask 2.2: 1 NEW page.tsx (CR 11-4 D-001 mount)
  - [ ] Subtask 2.3: 1 NEW ko-KR.json `insight_cache` namespace (~15 strings)
  - [ ] Subtask 2.4: 1 NEW vitest mount test (~6 cases)
  - [ ] Subtask 2.5: 3 NEW TS mirror parity tests (SourceKind + InsightKind + INSIGHT_KIND_VALUES)
- [ ] **Task 3: T3 — 10-3 frontend test debt 해소** (AC: #3)
  - [ ] Subtask 3.1: 3 NEW components (AiReferenceBadge + AutoAnalysisBadge + AiCommentSection)
  - [ ] Subtask 3.2: 1 NEW page.tsx (CR 11-4 D-001 mount)
  - [ ] Subtask 3.3: 1 NEW ko-KR.json badge labels + tooltip SSOT
  - [ ] Subtask 3.4: 3 NEW vitest mount tests (~18 cases)
  - [ ] Subtask 3.5: 1 NEW TS mirror parity test (SourceKind Literal parity + auto_analysis read-only guard)
  - [ ] Subtask 3.6: 1 NEW cross-language drift detector test EXTENSION (CR 12-5 D-13)
- [ ] **Task 4: T4 — 10-4 frontend test debt 해소** (AC: #4)
  - [ ] Subtask 4.1: 2 NEW components (PromoteConfirmButton + PromoteResultToast)
  - [ ] Subtask 4.2: 1 NEW ko-KR.json promote error messages + status labels SSOT
  - [ ] Subtask 4.3: 2 NEW vitest mount tests (~24 cases, 3-layer defense + 7-variant Discriminated union)
- [ ] **Task 5: T5 — Shared frontend integration** (AC: #5)
  - [ ] Subtask 5.1: 1 NEW m10-ai-types.ts (SourceKind + InsightKind + PromoteStatus type aliases)
  - [ ] Subtask 5.2: 1 NEW ko-KR.json SSOT drift detector EXTENSION (P-015)
  - [ ] Subtask 5.3: 1 NEW shared mocks (8 endpoints)
  - [ ] Subtask 5.4: 16 NEW vitest cases
- [ ] **Task 6: T6 — docs + sprint-status sync + handoff memory** (AC: #6)
  - [ ] Subtask 6.1: deferred-work.md D-10-1-DEFER-3 + D-10-2-DEFER-4 + D-10-3-DEFER-4 + D-10-4-DEFER-4 ✅ RESOLVED
  - [ ] Subtask 6.2: sprint-status.yaml 10-5-a38-frontend-test-debt-dedicated: ready-for-dev → in-progress → done
  - [ ] Subtask 6.3: handoff memory NEW + MEMORY.md index sync + epic-10-handoffs-detail.md 10-5 section
- [ ] **Task 7: T7 — 3중 게이트 FINAL CLEAN** (AC: #6)
  - [ ] Subtask 7.1: vitest ~102 NEW cases ALL PASS
  - [ ] Subtask 7.2: ko-KR.json SSOT drift detector PASS (P-015)
  - [ ] Subtask 7.3: backend 3중 게이트 baseline 보존 (frontend only sprint)
  - [ ] Subtask 7.4: A36 SDR 검증 4-step 자동 PASS
- [ ] **Task 8: T8 — atomic commit close-out** (AC: #6)
  - [ ] Subtask 8.1: pre-commit 3중 게이트 FINAL CLEAN verification
  - [ ] Subtask 8.2: `git commit -F <commit-msg>` 패턴 (CR 9-6 D5 prevention)
  - [ ] Subtask 8.3: 19 files atomic (12 NEW + 7 MODIFIED)
  - [ ] Subtask 8.4: commit message 형식 보존

## Developer Context

### Architecture Compliance
- **AD-7 strict invariant preserved**: M10 NEVER writes `confirmed_inputs`/`monthly_input_rows` — frontend mounts display only, no direct write
- **AD-11 layer rule**: apps/web/components/m10-ai/ ONLY mounts + display; no business logic in components
- **AD-15 cross-language conventions**: TS mirrors `apps/web/lib/ai-extract.ts` + `ai-extract-parity.test.ts` (10-1) + `insight-cache.ts` + `insight-cache-parity.test.ts` (10-2) + `ai-comment.ts` + `ai-comment-parity.test.ts` (10-3) + `ai-promote.ts` (10-4, already wire in 10-4 wire) — 3 NEW parity tests wire 결정
- **AD-17 verbatim bind**: PromoteConfirmButton 3-layer dependency (PIPA gate 1st + M2-only 2nd + AI_INSIGHT capability 3rd)
- **AD-22 ledger append-only**: 프론트엔드는 audit log 직접 INSERT 안 함 (CR 1.1 audit-first invariant 보존)

### Library/Framework Requirements
- **React 19.x** + Next.js 15.x (App Router) — 기존 baseline 보존
- **TypeScript 5.x** strict mode — frozen type unions + type guards (CR 11-4 D-005 unknown state reject)
- **Tailwind CSS** + shadcn/ui — 기존 baseline 보존
- **vitest 1.x** + @testing-library/react — 기존 baseline 보존
- **react-hook-form 7.x** + Zod schema — 10-1 AiExtractModal form pattern (CR 11-4 patterns carry)
- **sonner** toast — 10-4 PromoteResultToast pattern (CR 11-4 patterns carry)

### File Structure Requirements
- `apps/web/components/m10-ai/` EXTENSION (NEW directory) — 9 NEW components + 1 index.ts
- `apps/web/app/[locale]/(dashboard)/monthly-input/ai-extract/page.tsx` NEW (10-1)
- `apps/web/app/[locale]/(dashboard)/ai/insights/page.tsx` NEW (10-2)
- `apps/web/app/[locale]/(dashboard)/ai/comments/page.tsx` NEW (10-3)
- `apps/web/messages/ko-KR.json` 4 namespace EXTENSION (ai_extract + insight_cache + badge_labels + promote_error_messages)
- `apps/web/__tests__/components/m10-ai.*.test.tsx` 9 NEW vitest files
- `apps/web/__tests__/lib/*-parity.test.ts` 3 NEW TS mirror parity tests
- `apps/web/lib/m10-ai-types.ts` NEW shared types

### Testing Requirements
- **vitest ~102 NEW cases total** (T1 28 + T2 12 + T3 22 + T4 24 + T5 16)
- **Playwright 0 NEW** (E2E는 Epic 12 12-5 T6 패턴 follow-up sprint 결정 후속)
- **pytest 0 NEW** (frontend only sprint, backend tests 보존)
- **ko-KR.json SSOT drift detector EXTENSION** (P-015, 4 namespaces 모두 검증)

## Previous Story Intelligence (cj-style carry-over pattern)

### 9-7 Epic 9 frontend test debt follow-up (cj-style carry-over 11번째, 24번째 epic 연속)
- **wire 표**: 18 files (13 NEW + 5 MODIFIED) atomic + 3 NEW memory handoff files
- **A35 wire**: 5 NEW vitest component tests + 3 NEW TS mirror parity tests + 1 MODIFIED `apps/web/mocks/handlers.ts`
- **vitest cases = 105 NEW** (R1 mitigation: actual `find` count)
- **D3 ✅ RESOLVED**: 8 컴포넌트 마운트 — m9-abc 5건 standalone wire + m5-reports 3건 parent file cover 인정 per user option (a)
- **D1/D4/D5 자동화**: commit prefix lint + sprint-status structure 검증 + commit 정합성 검증 단계 wire

### Epic 10 4 stories wire (cj-style 28~34번째 epic 연속)
- **10-1 second pass**: AiDraftCard + ConfidenceBadge + AiExtractModal frontend wire 결정 (D-10-1-DEFER-3 honestly DEFER (d))
- **10-2 atomic sprint**: insight cache UI frontend wire 결정 (D-10-2-DEFER-4 honestly DEFER (d))
- **10-3 3rd sweep**: badge components + comment section frontend wire 결정 (D-10-3-DEFER-4 honestly DEFER (d))
- **10-4 atomic wire**: PromoteConfirmButton + PromoteResultToast frontend wire 결정 (D-10-4-DEFER-4 honestly DEFER (d))
- **A36 SDR 검증 4-step PASS**: Epic 10 4 stories 모두 commit prefix lint + sprint-status structure + vitest file count drift + commit consistency 자동 검증 단계 모두 PASS

### 11-5 Epic 11 second carry-over sprint (cj-style 36번째 epic 연속)
- **wire 표**: 7 files (2 NEW + 5 MODIFIED)
- **A13 residual (2 items RESOLVED)**: D-001 page.tsx mount verified + P-011 dead code DELETE
- **partial wire 시도 0건 + single sprint atomic wire T1~T8 결정**

## Git Intelligence Summary

### Most Recent Commits (HEAD = 197c96d)
- `197c96d` Sprint 11-6 bmad-create-story spec entry DONE (cj-style 37번째 epic 연속 정직 회복)
- `f575766` Epic 10 close-out retro doc wire (cj-style 35번째 epic 연속 정직 회복)
- `1060360` Story 11.5 atomic wire T1~T8 DONE — A13 residual + A17 + A18 sprint-up
- `dc85ab9` @ Smoke-fix sprint T1~T7 atomic wire — 36/36 PASS + CI green gate
- `4f510c2` Story 10.4 bmad-dev-story T1~T8 atomic wire DONE

### Patterns to Reuse
- **CR 9-6 D5 prevention**: commit message = `git commit -F <file>` (NOT PowerShell here-string)
- **A36 SDR 4-step 자동 적용**: commit prefix lint + sprint-status structure + vitest file count drift + commit consistency
- **CR 11-4 D-001 MUST**: page.tsx actual mount `<Component>` JSX (NOT placeholder)
- **CR 11-4 D-002**: ko-KR.json SSOT only (P-015 drift detector)
- **CR 11-4 D-005**: TS mirror unknown state reject (type guards)
- **CR 12-5 D-13**: cross-language drift detector EXTENSION

## Latest Tech Information

### Next.js 15.x page.tsx mount discipline (CR 11-4 D-001)
- App Router RSC pattern: `apps/web/app/[locale]/(dashboard)/<route>/page.tsx`
- Client Component mount pattern: import { ComponentName } from '@/components/m10-ai'; return <ComponentName />
- NO placeholder JSX (D-001 MUST)
- NO server-side data fetching (frontend display only)

### vitest 1.x + @testing-library/react 16.x
- Component test pattern: `render(<Component {...props} />)` + `screen.getByTestId()` + `expect().toBeInTheDocument()`
- Mock pattern: `vi.mock('@/lib/api', () => ({ fetchX: vi.fn() }))`
- @testing-library/user-event for interaction tests

### react-hook-form 7.x + Zod schema
- Form pattern: `useForm<FormSchema>({ resolver: zodResolver(formSchema) })`
- Field validation: `register('fieldName')` + `{errors.fieldName && <span>...</span>}`
- Submit handler: `handleSubmit(onSubmit)` with `data: FormSchema` typed parameter

## Project Context Reference

`costmgr (bizup)` — Modular monolith hexagonal core skeleton (Story 0.1 + 0.2 + 0.3 + 0.4 + 0.5). Epic 1~12 PRD entry + Epic 1·2·3·4·5·6·7·8·9·10·11·12 + Epic 11 carry-over + Epic 12 close-out + Walking Skeleton MVP + Epic 9 close-out retro + Epic 10 close-out retro 모두 wire 진입. **cj-style 35~37번째 epic 연속 정직 회복**.

## A34 4-Category Honestly DEFER

### D-10-1-DEFER-3 (10-1 frontend 8 files) → **A38 wire 진입 시 해소**
### D-10-2-DEFER-4 (10-2 frontend 7 files) → **A38 wire 진입 시 해소**
### D-10-3-DEFER-4 (10-3 frontend 7 files) → **A38 wire 진입 시 해소**
### D-10-4-DEFER-4 (10-4 frontend 5 files) → **A38 wire 진입 시 해소**

### A38 wire 후 보존 (cj-style 14번째 carry-over 결정 wire)
- A37 master PRD v2.0 본체 edit → cj-style carry-over 15번째 후속
- D-10-3-DEFER-2 (b) retro input ai_reference 의견 async generation pipeline → Epic 10 close-out retro 입력
- D-10-3-DEFER-3 (c) separate epic auto_analysis 의견 read-only DB-level trigger → 별도 epic 결정 후속

## A36 SDR 검증 4-step PASS 목표

### commit prefix lint PASS (D5 fix DONE)
- commit message = `git commit -F <file>` 패턴 (CR 9-6 D5 prevention)
- commit subject 형식: `Story 10.5 (cj-style Epic 10 carry-over 14번째 = cj-style 38번째 epic 연속): A38 frontend test debt dedicated sprint atomic wire T1~T8 DONE — Epic 10 4 stories (10-1 + 10-2 + 10-3 + 10-4) frontend test debt 일괄 해소`

### sprint-status structure 정합 (D4 fix DONE)
- 10-5-a38-frontend-test-debt-dedicated entry = development_status 블록 line 274 후 위치
- epic-10 status: done (변경 없음, retro closed 후)
- 10-5-a38-frontend-test-debt-dedicated: backlog → ready-for-dev (현 wire 진입 시점) → in-progress → done

### vitest file count drift 0건 (D2 자동화)
- A38 wire 전 baseline + A38 wire 후 baseline = ~102 NEW vitest cases 정확히 매칭
- scripts/check_vitest_file_count.py 자동 검증 단계

### commit consistency 정합 (D1 자동화)
- sprint-status entry ↔ commit message wire 표 일치
- scripts/check_commit_consistency.py 자동 검증 단계

## Story Completion Status

**Status**: ready-for-dev (2026-08-19, A38 결정 wire 진입점)

**Ultimate context engine analysis completed**: comprehensive developer guide created.

## Spec Metadata

- **Epic**: 10 (close-out carry-over, post-Epic 10 close-out retro)
- **Story number**: 10-5 (cj-style carry-over 14번째)
- **A38 identifier**: A35 frontend test debt honestly DEFER (d) + Epic 10 close-out retro §7 A38 결정 wire
- **baseline_commit**: 197c96d (Sprint 11-6 spec entry tip)
- **cj-style epic continuous**: cj-style 38번째 epic 연속 정직 회복 진입점
- **Owner**: Amelia + Dana
- **Estimated scope**: ~12 frontend files + 4 vitest mount + 3 TS mirror parity = ~19 files, ~102 NEW vitest cases
- **Wire plan**: atomic single sprint T1~T8 (cj-style discipline 보존)
- **partial wire 시도**: 0건
- **3중 게이트 impact**: backend 0건 (frontend only) + frontend ~102 NEW cases ALL PASS + ko-KR.json SSOT drift detector PASS (P-015)
- **A36 SDR 검증 4-step 자동 적용**: PASS 목표 (Epic 10 4 stories 패턴 미러)

---

*— A38 frontend test debt dedicated sprint spec entry (cj-style carry-over 14번째 = cj-style 38번째 epic 연속 정직 회복 진입점). Epic 10 close-out retro §11.2 명시 "A38 ... cj-style carry-over 14번째 진입 (retro closed 후 즉시)" 결정 wire.*