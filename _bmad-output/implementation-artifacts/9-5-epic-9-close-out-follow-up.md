---
story_id: 9.5
story_key: 9-5-epic-9-close-out-follow-up
title: Epic 9 close-out follow-up (A27 결정 + D-9-4-DEFER-1 docs 정합 + DEFER items 보존)
created: 2026-08-17
baseline_commit: 2489e50
epic: 9
status: ready-for-dev
target_sprint: cj-style Epic 9 5번째 진입점 (cj-style carry-over 9번째, A27 결정 적용)
estimated_complexity: medium-low
honestly_defer_count: 4
---

# Story 9.5 — Epic 9 close-out follow-up (A27 결정 + D-9-4-DEFER-1 docs 정합 + 4 honestly DEFER 보존)

## Story Header

| Field | Value |
|-------|-------|
| **Story ID** | 9.5 |
| **Story Key** | `9-5-epic-9-close-out-follow-up` |
| **Epic** | Epic 9 — ABC / TDABC Engine (Service Business) |
| **baseline_commit** | `2489e50` (Story 9.4 atomic wire close-out tip = current HEAD, 2026-08-17) |
| **cj-style 진입점** | cj-style Epic 9 5번째 진입점 (cj-style carry-over 9번째) — Epic 9 close-out follow-up sprint. cj-style 22번째 epic 연속 (Epic 0·1·2·3·4·5·6·7·8·11·12 + Epic 7·8·9·Walking Skeleton MVP + Epic 9 4번째 + **Epic 9 close-out follow-up**) |
| **Trigger 결정** | **A27 결정 적용** (Epic 8 retro `epic-8-retro-2026-08-16.md` §7 A27: "A19 follow-up sprint for 8 honestly DEFER — Epic 8 only 통합 follow-up sprint — 우선 wire + 나머지 7 items honestly DEFER 유지. Epic 9 진입 전 또는 병행 (cj-style carry-over 9번째)" — 본 story는 Epic 9 only 통합 follow-up) |
| **Forward-lock** | **A30 forward-lock 보존** (Report #15 wire = Epic 9 close-out retro A31+ 결정, 본 story scope 외) + **A28/A29 forward-lock wire 보존** (9-2/9-3 변경 0) |
| **Primary capability** | N/A (no capability change; docs/spec 정합 only) |
| **Primary PRD ref** | §9 #21 verbatim ("부문귀속명세서") + epics.md Story 9.4 ("원가대상별 원가 집계표") — D-9-4-DEFER-1 정합 |
| **Baseline wire** | 9-4 atomic wire 19 NEW + 17 MODIFIED = ~36 files (3중 게이트 FINAL CLEAN, 4 honest DEFER) + 9-3 + 9-2 + 9-1 + Walking Skeleton MVP wire 보존 |

## User Story (cj-style carry-over sprint + A27 결정 verbatim)

As **Epic 9 close-out PM**, I want **Epic 9 honestly DEFER 4 items (D-9-3-DEFER-2 + D-9-4-DEFER-1~3) 의 우선순위 결정 + D-9-4-DEFER-1 docs 정합** so that **Epic 9 close-out retro (cj-style 5번째 진입점)가 clean baseline으로 진입 가능 + A31+ forward-lock 결정 (Report #15 wire 포함) 의 정확한 inputs 제공**.

**Note on A27 결정 정합**: Epic 8 retro A27 = "**Playwright E2E 우선 wire + 나머지 7 items honestly DEFER 유지**". Epic 9 honestly DEFER profile = (D-9-3-DEFER-2 + D-9-4-DEFER-1~4) 5 items. 본 story wire scope:
- **WIRE (RESOLVE)**: D-9-4-DEFER-1 (docs 정합 — 단일 항목, 본 story scope)
- **honestly DEFER (preserve in deferred-work.md)**: D-9-3-DEFER-2 + D-9-4-DEFER-2 + D-9-4-DEFER-3 + D-9-4-DEFER-4

**Why A27 priority (Playwright E2E) 미적용**: Epic 9 honestly DEFER items = **mixed profile** (1 docs 정합 + 1 retro decision input + 1 separate epic scope + 1 separate sprint scope + 1 activity standard hour code work). A27 priority는 Epic 8처럼 "Playwright E2E 단일 우선 항목" 구조일 때 적용 가능. Epic 9는 단일 우선 항목 부재 → **D-9-4-DEFER-1 (lowest risk + docs only) RESOLVE + 나머지 honestly DEFER 보존** 결정.

**Auth scope**: N/A (no auth/permission change; docs/spec 정합 only).

## Acceptance Criteria (A27 결정 + D-9-4-DEFER-1 verbatim wire + 4 honestly DEFER 보존)

### AC #1 — D-9-4-DEFER-1 RESOLVE: epics.md vs PRD §9 #21 docs 정합

**Conflict 분석 (verbatim wire)**:
- PRD §9 #21 verbatim (prd.md line 137, 401, 513, 732): **"부문귀속명세서"** (법인세법 시행규칙 제76조 2기준 카브아웃 분할 근거 공시 보고서)
- epics.md Story 9.4 (line 1052, 1056): **"원가대상별 원가 집계표"** (Cost Object Breakdown, ABC results display)
- 9-4 architecture-inventory.md line 918 (9-4 sprint 추가): **INCORRECT** claim — "PRD §9 #21 verbatim: '원가대상별 원가 집계표 (Cost Object Breakdown)'" — 실제 PRD §9 #21 verbatim ≠ 이 문구 (PRD는 "부문귀속명세서")
- 9-4 implementation = **합성 scope** (PRD §9 #21 SSOT + epics.md 9.4 product_id별 행 extension)

**Given** 사장님이 [보고서] → [원가대상별 원가 집계표] (Report #21) 클릭 (epics.md 9.4 UX label 보존)
**And** backend `Report21Service.build_report21` + `_compose_report21_pdf` (9-4 wire 보존, 변경 0)
**When** architecture-inventory.md §9.4 line 918 incorrect verbatim claim 수정 + deferred-work.md D-9-4-DEFER-1 정합 decision entry + capability-matrix v1.20 status 보존
**Then** PRD §9 #21 verbatim "부문귀속명세서" + epics.md 9.4 "원가대상별 원가 집계표" 모두 정합하게 wire
**And** Report #21 PDF 라벨 = **"원가대상별 원가 집계표 (부문귀속명세서 §9 #21 기반)"** hybrid label (hybrid 결정 = 9-5 follow-up 결정 wire, retro A31+ confirm 가능)
**And** UX 표기 = **"[원가대상별 원가 집계표]"** (epics.md 9.4 UX label 보존, 변경 0)

### AC #2 — 4 honestly DEFER items 보존 (CR 11-3 discipline 22번째 epic 연속)

deferred-work.md NEW section "Deferred from: Epic 9 close-out follow-up (2026-08-17)" 추가:

- **D-9-3-DEFER-2**: Activity standard hour 자동 추출 — Epic 9 close-out follow-up scope 외 (별도 sprint). Activity standard hour은 9-1 wire에서 manual entry 확정 (UX). 자동 추출 = time tracking data source 통합 필요 (별도 epic). **Where**: `packages/cost_engine/abc_engine.py` ActivityStandard dataclass + `apps/web/components/m9-abc/ActivityStandardEditor.tsx` (9-1 wire). **To pick up**: 별도 sprint (cj-style carry-over 10번째, Epic 10+ 시점)
- **D-9-4-DEFER-2**: Report #15 wire (활동원가 내역서) = A30 SHARED factory 패턴 재사용. **A31+ 결정 wire** (Epic 9 close-out retro 진입점). **Where**: `packages/services/m5_reports/pdf_generator.py::_compose_report15_pdf` placeholder (9-4 wire). **To pick up**: Epic 9 close-out retro A31+ 결정 후 별도 story
- **D-9-4-DEFER-3**: AI 자동 분석의견 (PRD §9 #16 + §A11 + §10) — **separate epic scope** (AI capability, 별도 epic territory). **Where**: PRD §9 #16 verbatim + §A11 (자동 분석 SSOT) + §10 (AI agent contract). **To pick up**: Epic 11+ AI capability epic
- **D-9-4-DEFER-4**: Playwright E2E (Epic 9 전체) — **dedicated sprint** (12-5 T6 pattern, A27 priority 미적용 사유 — Epic 9 mixed honestly DEFER profile에서 단일 우선 항목 부재). **Where**: `apps/web/e2e/` Epic 9 4 stories (9-1+9-2+9-3+9-4). **To pick up**: Epic 9 close-out retro A31+ 결정 후 Playwright E2E dedicated sprint

### AC #3 — sprint-status.yaml sync + capability-matrix v1.20 보존

- `9-5-epic-9-close-out-follow-up: ready-for-dev → in-progress → done`
- `epic-9: in-progress → done` (cj-style 4-story + 1 follow-up 모두 완료)
- `epic-9-retrospective: optional → ready-for-dev` (cj-style 5번째 진입점, follow-up done 후 진입)
- `last_updated_note`: `2026-08-17: 9-5 follow-up done (cj-style 22번째 epic 연속, A27 결정 적용, D-9-4-DEFER-1 RESOLVE + 4 honestly DEFER 보존)`
- capability-matrix.md v1.20 status 보존 (변경 0, capability matrix drift detector 0 NEW)

### AC #4 — 3중 게이트 FINAL CLEAN (cj-style atomic single sprint)

- **ruff scoped** (`apps/api` + `apps/web` + `packages`): All checks passed (0 NEW errors)
- **import-linter**: 2 KEPT (cost_engine_forbidden_io + engine_core_to_adapters_forbidden), 0 broken
- **pytest focused**: pre-existing baseline 보존 (1108+ passed + 118 skipped + 0 failed baseline 보존; 9-5 surface 0 NEW tests — docs/spec 정합 only)
- **tsc**: zero NEW for 9-5 (docs 변경 only)
- **vitest**: zero NEW for 9-5 (frontend 변경 only = architecture-inventory §9.4 1 line correction)

### AC #5 — Atomic wire close-out (cj-style 22번째 epic 연속, partial wire 시도 0건)

- Single atomic commit (cj-style discipline 정합)
- Handoff memory entry `handoff-2026-08-17-9-5-done.md` NEW
- MEMORY.md index sync
- 4 honestly DEFER items preserved in deferred-work.md (CR 11-3 discipline 22번째 epic 연속)

## Tasks (cj-style atomic single sprint T1~T10)

### T1 — Spec entry 보존

- [x] T1.1 `_bmad-output/implementation-artifacts/9-5-epic-9-close-out-follow-up.md` NEW (본 파일)
- [x] T1.2 sprint-status.yaml `9-5-epic-9-close-out-follow-up: ready-for-dev` entry 추가

### T2 — D-9-4-DEFER-1 docs 정합 wire (AC #1)

- [ ] T2.1 `docs/architecture-inventory.md` §9.4 line 918 incorrect verbatim claim 수정
  - Before: `> PRD §9 #21 verbatim: **"원가대상별 원가 집계표 (Cost Object Breakdown)"**.`
  - After: `> **PRD §9 #21 verbatim (prd.md §7.3 + §9 #21)**: "부문귀속명세서 (카브아웃 근거 공시, §7.3)". **epics.md Story 9.4 UX label**: "원가대상별 원가 집계표 (Cost Object Breakdown)". **9-4 implementation**: 합성 scope (PRD §9 #21 SSOT + epics.md 9.4 product_id별 행 extension). **정합 차이**: D-9-4-DEFER-1 RESOLVE in 9-5 follow-up (hybrid PDF 라벨 "원가대상별 원가 집계표 (부문귀속명세서 §9 #21 기반)" + UX 표기 보존).`
- [ ] T2.2 `docs/architecture-inventory.md` §9.4 line 918 footnote 추가: D-9-4-DEFER-1 reference (deferred-work.md)
- [ ] T2.3 `docs/abc-report-21.md` §1 Overview section hybrid PDF 라벨 결정 반영 (있는 경우)
- [ ] T2.4 PDF byte composition `_compose_report21_pdf` 확인 — hybrid label wire 검토 (변경 최소, 라벨만)

### T3 — deferred-work.md Epic 9 DEFER items 보존 (AC #2)

- [ ] T3.1 `_bmad-output/implementation-artifacts/deferred-work.md` NEW section 추가:
  ```
  ## Deferred from: Epic 9 close-out follow-up (2026-08-17)

  > cj-style Epic 9 5번째 진입점 follow-up sprint (A27 결정 적용). 1 RESOLVE + 4 honestly DEFER (CR 11-3 discipline 22번째 epic 연속).

  - **D-9-4-DEFER-1 RESOLVED (9-5)** — epics.md "원가대상별 원가 집계표" vs PRD §9 #21 "부문귀속명세서" 정합. PDF 라벨 = "원가대상별 원가 집계표 (부문귀속명세서 §9 #21 기반)" hybrid. UX 표기 = "[원가대상별 원가 집계표]" (epics.md 9.4 보존). architecture-inventory.md §9.4 line 918 incorrect verbatim claim 수정. **Where**: docs/architecture-inventory.md §9.4 + docs/abc-report-21.md §1 + PDF byte composition hybrid label.

  - **D-9-3-DEFER-2** — Activity standard hour 자동 추출. Epic 9 close-out follow-up scope 외. 별도 sprint. **Where**: `packages/cost_engine/abc_engine.py` ActivityStandard dataclass + `apps/web/components/m9-abc/ActivityStandardEditor.tsx`. **To pick up**: cj-style carry-over 10번째 (Epic 10+ 시점).

  - **D-9-4-DEFER-2** — Report #15 wire (활동원가 내역서). **A31+ 결정 wire** (Epic 9 close-out retro). **Where**: `packages/services/m5_reports/pdf_generator.py::_compose_report15_pdf` placeholder. **To pick up**: Epic 9 close-out retro A31+ 결정 후 별도 story.

  - **D-9-4-DEFER-3** — AI 자동 분석의견. Separate epic scope (AI capability). **Where**: PRD §9 #16 + §A11 + §10. **To pick up**: Epic 11+ AI capability epic.

  - **D-9-4-DEFER-4** — Playwright E2E (Epic 9 전체). Dedicated sprint. A27 priority 미적용 사유 (Epic 9 mixed DEFER profile). **Where**: `apps/web/e2e/` Epic 9 4 stories. **To pick up**: Epic 9 close-out retro A31+ 결정 후 Playwright E2E dedicated sprint (12-5 T6 pattern).
  ```

### T4 — capability-matrix v1.20 status 보존 (AC #3)

- [ ] T4.1 `docs/capability-matrix.md` v1.20 EXTENSION status 확인 (변경 0)
- [ ] T4.2 capability-matrix v1.20 drift detector 0 NEW (보존)

### T5 — sprint-status.yaml sync (AC #3)

- [ ] T5.1 `9-5-epic-9-close-out-follow-up: ready-for-dev → in-progress → done`
- [ ] T5.2 `epic-9: in-progress → done` (cj-style 4-story + 1 follow-up 모두 완료)
- [ ] T5.3 `epic-9-retrospective: optional → ready-for-dev` (cj-style 5번째 진입점 ready)
- [ ] T5.4 `last_updated_note`: `2026-08-17: 9-5 follow-up done (cj-style 22번째 epic 연속, A27 결정 적용, D-9-4-DEFER-1 RESOLVE + 4 honestly DEFER 보존)`

### T6 — 3중 게이트 verification (AC #4)

- [ ] T6.1 `ruff check apps/api apps/web packages` → All checks passed
- [ ] T6.2 `lint-imports` → 2 KEPT, 0 broken
- [ ] T6.3 `pytest --collect-only -q` → baseline 보존 (1108+ tests collected)
- [ ] T6.4 `pnpm tsc --noEmit` → zero NEW errors for 9-5
- [ ] T6.5 vitest baseline 보존 (변경 0)

### T7 — Atomic commit + handoff (AC #5)

- [ ] T7.1 Single atomic commit: `Story 9.5 (Epic 9 close-out follow-up, cj-style 22번째): D-9-4-DEFER-1 RESOLVE + 4 honestly DEFER 보존 (A27 결정 적용)`
- [ ] T7.2 `_bmad-output/planning-artifacts/handoff-2026-08-17-9-5-done.md` NEW
- [ ] T7.3 MEMORY.md index sync (handoff-2026-08-17-9-5-done entry)

### T8 — Post-commit sanity check

- [ ] T8.1 `git status` clean (untracked empty files `Epic`/`Story`/`capability`/Korean-named 보존 = 사용자 의도)
- [ ] T8.2 `git log --oneline -5` atomic commit 확인
- [ ] T8.3 `git diff HEAD~1 --stat` wire scope 확인

## Dev Notes

### A27 결정 정합 분석

Epic 8 retro `epic-8-retro-2026-08-16.md` §7 A27 verbatim:
> A27 A19 follow-up sprint for 8 honestly DEFER
> Epic 8 only 통합 follow-up sprint — D-8-3-DEFER-7 Playwright E2E (8-1+8-2+8-3 모두 mirror, 12-5 T6 패턴) **우선 wire** + 나머지 7 items **honestly DEFER 유지**. Epic 9 진입 전 또는 병행 (cj-style carry-over 9번째).

**A27 priority 적용 조건**: "Playwright E2E 단일 우선 항목"이 존재할 때. Epic 8 honestly DEFER profile = Playwright E2E (8-1+8-2+8-3 mirror) 1개 우선 + 7 honestly DEFER.

**Epic 9 honestly DEFER profile = mixed**:
- D-9-3-DEFER-2: Activity standard hour 자동 추출 (code work)
- D-9-4-DEFER-1: docs 정합 (docs only)
- D-9-4-DEFER-2: Report #15 wire (retro decision input)
- D-9-4-DEFER-3: AI 자동 분석의견 (separate epic scope)
- D-9-4-DEFER-4: Playwright E2E (dedicated sprint scope)

**A27 priority 미적용 결정** (9-5 AC #1 verbatim): Epic 9는 "단일 우선 항목 부재" → **D-9-4-DEFER-1 (lowest risk + docs only) RESOLVE + 나머지 honestly DEFER 보존**.

### D-9-4-DEFER-1 정합 결정 분석

**Option A**: PRD §9 #21 verbatim 보존 ("부문귀속명세서") — Report #21 = "부문귀속명세서". 9-4 implementation 변경 (Report #21 label 변경).

**Option B**: epics.md 9.4 UX label 보존 ("원가대상별 원가 집계표") — Report #21 = "원가대상별 원가 집계표". 9-4 implementation 변경 없음.

**Option C (선택)**: Hybrid label — PDF 라벨 = **"원가대상별 원가 집계표 (부문귀속명세서 §9 #21 기반)"**. 9-4 implementation 변경 최소 (라벨 text만). UX 표기 보존.

**선택 사유**: Option A는 9-4 wire 사후 변경 → cj-style discipline 위반 (atomic wire 사후 변경). Option B는 PRD §9 #21 verbatim 무시 → PRD SSOT 위반. **Option C = 양쪽 SSOT 모두 존중 + 9-4 wire 변경 최소**.

### CR lessons applied (9-5 carry-over sprint)

- **CR 11-3**: honest-DEFER discipline — 4 honestly DEFER preserved (CR 11-3 22번째 epic 연속)
- **CR 11-2**: SDR claim 보존 (baseline 보존, no NEW SDR claim)
- **CR 11-4**: ko-KR.json SSOT cross-language parity (UX 표기 보존)
- **CR 12-1**: layer rule 보존 (no code change, layer boundary 무관)

## Lessons carry (9-5 follow-up sprint)

- **L1 (cj-style carry-over sprint 9번째)**: Epic 9 only 통합 follow-up sprint. A27 결정 적용. D-9-4-DEFER-1 RESOLVE + 4 honestly DEFER 보존. partial wire 시도 0건, single sprint dedicated.
- **L2 (D-9-4-DEFER-1 hybrid label 결정)**: PRD §9 #21 verbatim + epics.md UX label 정합 = hybrid PDF 라벨. SSOT 양쪽 모두 존중 + 9-4 wire 변경 최소.
- **L3 (A27 priority 미적용 조건)**: "단일 우선 항목 부재" 시 A27 priority 미적용 = D-9-4-DEFER-1 (lowest risk + docs only) RESOLVE + 나머지 honestly DEFER.
- **L4 (architecture-inventory verbatim claim 정확성)**: 9-4 sprint line 918 incorrect claim → 9-5 follow-up 정정. verbatim quote 정확성 discipline.

## Deferred work (4 honestly DEFER 보존)

- **D-9-3-DEFER-2**: Activity standard hour 자동 추출 → 별도 sprint (cj-style carry-over 10번째)
- **D-9-4-DEFER-2**: Report #15 wire → A31+ 결정 (Epic 9 close-out retro)
- **D-9-4-DEFER-3**: AI 자동 분석의견 → separate epic (AI capability)
- **D-9-4-DEFER-4**: Playwright E2E → dedicated sprint (Epic 9 close-out retro A31+ 결정 후)

## References

- spec prior: `_bmad-output/implementation-artifacts/9-4-abc-report-21-cost-object-breakdown.md` (D-9-4-DEFER-1 origin)
- spec prior: `_bmad-output/implementation-artifacts/9-3-abc-calculation-routed-via-m3-endpoint.md` (D-9-3-DEFER-2 origin)
- handoff prior: [[handoff-2026-08-17-9-4-done]] (4 honestly DEFER source)
- handoff prior: [[handoff-2026-08-17-9-3-done]] (D-9-3-DEFER-2 + A29 forward-lock wire)
- A27 결정 source: [[handoff-2026-08-16-epic-8-retro-done]] (cj-style carry-over 9번째 패턴)
- A19 carry-over sprint pattern: [[handoff-2026-08-15-a19-inventory-projection-deprecate-done]] (single sprint atomic wire)
- CR 11-3 honest-DEFER discipline: [[cr-11-3-lessons]]

## Next steps

- **Epic 9 close-out retro (cj-style 5번째 진입점)**: 9-5 follow-up done 진입. A31+ forward-lock 결정 (Report #15 wire = A30 SHARED factory 패턴 재사용 entry). Epic 9 close-out retro 결정 일정.
- **D-9-4-DEFER-4 Playwright E2E**: Epic 9 close-out retro A31+ 결정 후 dedicated sprint (12-5 T6 pattern)
- **Epic 10 진입**: A31+ 결정 기반 Epic 10 PRD §F10 + cj-style 분할 진입점