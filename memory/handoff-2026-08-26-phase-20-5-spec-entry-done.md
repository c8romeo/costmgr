---
name: handoff-2026-08-26-phase-20-5-spec-entry-done
description: Phase 20.5 Critical Gap Resolution carry-over spec entry DONE (cj-style 146번째). 5 files atomic docs-only sprint = 4 NEW + 1 MODIFIED. Layer 1 router include + Layer 2 pytest backfill + Layer 3 docs backfill 결정 wire.
metadata:
  type: project
---

# Phase 20.5 Critical Gap Resolution carry-over spec entry DONE — cj-style 146번째

## 결정 wire 요약

Phase 20.5 (Critical Gap Resolution carry-over) spec entry 진입 완료. Phase 20 close-out retro (cj 145) 의 4 honest deviations 정직 회복을 위한 첫 진입점.

- **cj-style 진입점**: 146번째 (baseline_commit: `f361016`, parent: Phase 20 close-out retro `f361016`)
- **결정 wire 일자**: 2026-08-26 (KST)
- **files**: 5 files atomic docs-only sprint = **4 NEW + 1 MODIFIED**
  - 1 NEW spec file (`phase-20-5-critical-gap-resolution-carry-over-wire.md` ~+200 LOC)
  - 1 NEW handoff memory (this file)
  - 1 NEW commit-msg (PowerShell here-string 회피)
  - 1 MODIFIED memory/MEMORY.md hook EXTENSION
  - 1 MODIFIED sprint-status.yaml v3.55 → v3.56 EXTENSION

## Phase 20.5 territory 후보 (spec entry 진입 직전 확정)

- **territory**: Critical Gap Resolution carry-over
- **rationale**: Phase 20 close-out retro `f361016` 의 4 honest deviations 모두 해소
  - ① apps/api/main.py NOT MODIFIED — multi_cloud router 미 include. Phase 17 sustainability_router + Phase 18 commitment_router + Phase 19 pricing_router 모두 main.py 에 include 안됨
  - ② 0 NEW pytest test files — Phase 16/17/18/19/20 verbatim pattern 보존 결정 wire. spec §F36.8-4 의 ~92 NEW pytest predicted scope 의 14개 test files 모두 intentionally 미작성
  - ③ docs/finops-multi-cloud-cost-unified-reconciliation.md NOT created — Phase 17/18/19/20 의 4 docs 모두 미작성 pattern
  - ④ apps/api/scripts/cli dry-run flag NOT added — Phase 17/18/19/20 의 4 dry-run CLI scripts 모두 미작성 pattern (Phase 20.6+ 로 보류)
- 3-Layer territory:
  - Layer 1 P0 critical — apps/api/main.py router include (4 routers)
  - Layer 2 P1 — pytest test backfill (12 NEW test files targeted subset)
  - Layer 3 P2 — docs backfill (4 NEW docs files + capability v1.46 EXTENSION)

## 결정 wire 분석 — risk minimization

| 옵션 | 기술 부채 영향 | 리스크 | 가치 | 권장 |
|---|---|---|---|---|
| (a) Phase 21+ 신규 | 누적 debt ↑ | 중-상 | 낮음 | ❌ |
| (b) Epic 21+ 신규 | 누적 debt ↑↑ | 상 | 낮음 | ❌ |
| **(c) Phase 20.5 carry-over (Layer 1+2+3)** | debt ↓↓ | **하** | **최고** | ✅ **선택** |
| (d) 1st release follow-up | 동일 | 중 | 중 | 🟡 후속 |
| (e) D-DEFER-* follow-up | 동일 | 하 | 낮음 | 🟡 후속 |

선택 이유:
- P0 critical functional gap fix (4 routers 미등록 → 시스템이 실제 동작하지 않음)
- 1-day atomic sprint로 4 phase의 debt 동시 해소
- targeted subset의 12 NEW test files (~64 pytest cases) + 12 NEW vitest cases
- 4 NEW docs files + capability v1.46 EXTENSION

## 3 ACs §F37.1~§F37.3 verbatim → 36 sub-ACs (12+12+12)

- §F37.1 Layer 1 P0 — apps/api/main.py router include_router() (12 sub-ACs)
  - F37.1-1~F37.1-4: 4 routers import + include_router (sustainability + commitment + pricing + multi_cloud)
  - F37.1-5: include_router 위치 (executive_dashboard_router 호출 직후)
  - F37.1-6~F37.1-7: prefix="/api/v1" + tags 통일
  - F37.1-8: FastAPI ContextVar 보존 (CR 1-1)
  - F37.1-9: audit-first INSERT 8 NEW 자동 활성화
  - F37.1-10: Epic 12 2FA 챌린지 mandatory
  - F37.1-11: NFR3 P95 ≤ 500ms 검증
  - F37.1-12: A19 cohesion 9 surface EXTENSION PASS

- §F37.2 Layer 2 P1 — pytest test backfill (12 sub-ACs)
  - F37.2-1~F37.2-5: 5 router test files (executive + sustainability + commitment + pricing + multi_cloud)
  - F37.2-6~F37.2-7: 2 drift tests (capability + audit action v1.46)
  - F37.2-8: 1 smoke test (router_include)
  - F37.2-9~F37.2-10: 2 dashboard parity tests (multi_cloud + pricing vitest)
  - F37.2-11: ~64 NEW pytest cases PASS
  - F37.2-12: ~12 NEW vitest cases PASS

- §F37.3 Layer 3 P2 — docs backfill (12 sub-ACs)
  - F37.3-1~F37.3-4: 4 docs files (sustainability + commitment + pricing + multi-cloud)
  - F37.3-5: capability matrix v1.45 → v1.46 EXTENSION
  - F37.3-6: AD-47 multi-cloud-cost-unified-reconciliation 신규
  - F37.3-7: finops-routers-reference 신규
  - F37.3-8: finops-router-deployment 신규
  - F37.3-9~F37.3-10: 2 runbooks (sustainability + multi-cloud incident)
  - F37.3-11~F37.3-12: 2 기존 docs 패턴 verbatim EXTENSION

## T1~T3 + 24 subtasks

- T1: Layer 1 P0 — router include (8 subtasks)
  - T1.1~T1.4: 4 routers import + include_router
  - T1.5~T1.6: 위치 + prefix/tags
  - T1.7~T1.8: smoke test + A19 cohesion
- T2: Layer 2 P1 — pytest backfill (12 subtasks)
  - T2.1~T2.10: 10 test files 작성
  - T2.11~T2.12: pytest + vitest 실행
- T3: Layer 3 P2 — docs backfill (4 subtasks)
  - T3.1~T3.3: 9 docs files 작성
  - T3.4: cross-reference 보존

## Dev Notes 18종 (CR lessons applied)

CR 0-2 RLS + CR 1-1 audit-first INSERT 8 NEW + CR 1-1 ContextVar + CR 1-1 RSC boundary + CR 4-3/4-4 + CR 9-6 + CR 11-3 honest-DEFER 36번째 + ALLOWED_SERVICE_SUBMODULES 즉시 sweep + CR 11-4 + P-015 + CR 12-1 L4 + CR 12-5 D-14 (20 NEW typed exceptions) + CR 12-5 D-PARITY-01 + CR 12-5 D-GATE-01 + A19 cohesion 9 surface + A36 SDR 4-step + AD-14 stack pin + AD-22 owner-only RBAC + Epic 12 2FA 챌린지 + NFR4 PII minimization ✅ PRESERVED + NFR18 ko-KR SSOT + AD-47 신규 + **AD-48 신규 Phase 20.5 Critical Gap Resolution carry-over (a)~(c) 3 sub-decisions**

## D-DEFER-* honestly 결정 wire 보존

- D-FINOPS-1~8 ✅ ALL RESOLVED 보존
- **D-FINOPS-9 honestly DEFER 보존** — Phase 19.5 carry-over 결정 wire `b2fb1d8` 의 7개 세부 항목 모두 Phase 20 territory 흡수 결정 wire
- **Phase 20 wire 의 4 honest deviations 모두 Phase 20.5 territory 흡수 결정 wire** (① router include ② test backfill ③ docs backfill ④ scripts 보류 = Phase 20.6+ 로 carry-over)
- **CR 11-3 honest-DEFER 36번째 epic 연속 정직 회복 verification** 결정 wire

## A559~A563 5 NEW 결정 wire (cj-style 146번째)

- A559: 옵션 (c) Phase 20.5 Critical Gap Resolution carry-over 진입 결정 wire
- A560: spec 파일 생성 결정 wire (~+200 LOC)
- A561: 3 ACs §F37.1~§F37.3 verbatim → 36 sub-ACs (12+12+12) 전개 결정 wire
- A562: Tasks T1~T3 + 24 subtasks 결정 wire
- A563: sprint-status v3.55 → v3.56 EXTENSION + atomic commit via `git commit -F <file>` CR 9-6 D5 prevention + commit-msg-phase-20-5-spec-entry.txt 신규 + handoff memory 신규 + MEMORY.md hook EXTENSION + 5 files = 4 NEW + 1 MODIFIED atomic single sprint

## Epic 1~17 + Phase 3~20 + Phase 19.5 + 1st release cycle 정합 보존

cj-style 146번째 epic 연속 정직 회복 진입 시점에 pre-flight 정합 sweep 만족 결정 wire 보존. Phase 20 close-out retro `f361016` (cj-style 145번째) DONE 진입 정합 보존 + Phase 19.5 carry-over 결정 wire `b2fb1d8` (cj-style 141번째) AD-47 신규 (a)~(g) 7 sub-decisions 모두 결정 wire 진입 정합 보존 + Phase 11~20 10-module FinOps territory chain ✅ ALL WIRED 진입 정합 보존 (Layer 1 결정 wire 시) + Epic 1~17 ALL DONE 진입 정합 보존 + 1st release cycle ALL DONE 진입 정합 보존.

## 3중 게이트 impact NONE (cj-style 146번째 wire 진입 표준 = docs only 변경)

- ruff scoped 0 NEW (apps/api backend unchanged)
- pytest 0 NEW (apps/api backend unchanged)
- vitest 0 NEW (apps/web frontend unchanged)
- tsc 0 NEW (apps/web frontend unchanged)

## 결정 wire 일자 + next

- 결정 wire 일자: 2026-08-26 (KST)
- next 옵션:
  - (a) Phase 20.5 atomic wire T1~T3 진입 결정 wire (cj-style 147번째) — apps/api/main.py router include + 12 NEW pytest tests + 4 NEW docs files = ~22 files atomic single sprint
  - (b) Phase 20.5 close-out retro 진입 결정 wire (cj-style 148번째) — 14-section §1~§14 verbatim retro document
  - (c) Epic 21+ 진입 결정 wire
  - (d) D-DEFER-* follow-up 결정 wire 보류
