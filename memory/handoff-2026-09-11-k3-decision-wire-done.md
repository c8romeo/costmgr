---
name: k3-decision-wire-done
description: K-3 정의 결정 wire (cj-style 286번째) — K-3 = K-4 검증 chunk (PRD 6-domain 검증), K-3 + 잔여 인프라 보강 = K-4. cj-314 wire 3·4·5 DONE 정직 회복 + K-3 ~6 chunk 매핑 + 첫 검증 chunk 진입 결정 wire 보류.
metadata:
  type: project
---

# K-3 정의 결정 wire — DONE

> **Sprint**: K-3 정의 결정 wire (cj-style 286번째)
> **Date**: 2026-09-11 KST (D-3, Pilot W1 launch D-day 2026-09-14 KST)
> **Status**: ✅ **CLOSED ✅ HONEST** (sprint-status v4.101 → v4.102 EXTENSION A746)
> **Territory**: Phase 30 — MVP-verification scope 의 K-3 정의 chunk 진입 결정 wire
> **Author**: Claude (operator = kjw)
> **Sprint form**: docs-only atomic single sprint (CR 11-3 honest-DEFER 286번째)
> **commit**: 본 sprint commit (4 files docs-only atomic)
> **직전 sprint**: cj-319 Track A-0 deploy-blocking wire (`2249fec`, sprint-status v4.100 → v4.101 EXTENSION A745, cj-style 285번째)

---

## §1 의도 분석 — 2026-09-11 KST 사용자 결정 영역 진입

### 사용자 결정 wire (2026-09-11 KST, 본 sprint 진입 trigger)
- "Pilot/배포 작업 안 함 / RESEND·RAILWAY 등 지금 단계 X / 확실한 MVP 기능 갖춘 프로그램 필요" (`feedback-2026-09-10-mvp-verification-over-pilot-deployment`)
- K-4 = "K-3 + 잔여 인프라 보강" (PRD 6-domain 검증 scope, ~16개 주요 업무, ~3-4 working days best case)
- K-3 + 잔여 인프라 보강 = K-4 결정 wire 보존
- 40분 시간 제약 + 비정상 종료 안전 = atomic 단위 결정 wire 우선
- 본 sprint = Plan A' (K-3 결정 wire + K-3 첫 검증 chunk 진입 결정 wire) Step 1

### 정직 회복 — K-4 메모리 description 의 outdated 정직 인정
- K-4 메모리 (`memory/project-2026-09-10-k4-mvp-verification-scope.md`) description: "모든 기준 공통 첫 진입점 = Phase B 잔여 3개 (cj-314 wire 3·4·5)"
- **정직 회복**: cj-314 wire 3·4·5 가 모두 **이미 DONE** (2026-09-10 KST, sprint-status v4.92 → v4.99)

| Sprint | commit | sprint-status | 의도 |
|---|---|---|---|
| cj-314 wire 3 (Phase 8 ESLint/SLO/SLI 8 fixes) | `34e92aa` | v4.92 → v4.93 | 8 stale test path bug → 8 passed |
| cj-314 wire 4 (Phase B item 3 5 fixes) | `aacb12c` | v4.93 → v4.94 | 2 missing import fix |
| cj-314 wire 5 (Phase C retroactive close-out) | `4a57dd` | v4.97 → v4.98 | cj-317 preemptive close 정직 인정 |
| cj-314 wire 5 retroactive correction | `145ff4a` | v4.98 → v4.99 | A739 → A742 정직 회복 |

- 현재 sprint-position = **cj-319 (sprint-status v4.101 EXTENSION A745, latest commit `2249fec`)**
- K-4 메모리 description update 결정 wire 보류 (다음 세션 또는 본 sprint 후속 Step 2 에서 update)

---

## §2 K-3 정의 (CR 11-3 honest-DEFER)

### K-3 = PRD 6-domain 검증 chunk (K-4 sub-scope)
- K-3 + 잔여 인프라 보강 = K-4
- K-3 = "검증" scope, 잔여 인프라 보강 = "코드/환경 보강" scope

### K-3 ~6 chunk 매핑 (PRD 6-domain)

| # | Chunk | K-4 매핑 (parent 결정 wire verbatim mirror) | 검증 범위 |
|---|---|---|---|
| 1 | 사용자 시나리오 §2.A UJ-1~4 | tests/api/m0_onboarding + m8_budget + m9_abc + Phase 10 NFR11 P95 검증 | (Step 2 결정 wire 보류, 옵션 a RECOMMENDED) |
| 2 | 핵심기능목록 §8.1 M0~M12 | Phase A/B/C capability matrix EXTENSION 정합 | (Step 3+ 결정 wire 보류) |
| 3 | 상세기능명세 §F 각 FR | cj-314 wire 1~5 + cj-303 audit-fixes 결정 wire 정합 | (Step 4+ 결정 wire 보류) |
| 4 | 제약사항 (25 ADs + NFR) | Phase A/B/C + cj-303 sso 인프라 (AD-3 SSO 결정 wire 보존 검증) | (Step 5+ 결정 wire 보류) |
| 5 | 화면정의 §UI 부분 검증 | web-e2e 23 unsuppress = 회귀 자동 검증 환경 | (Step 6+ 결정 wire 보류) |
| 6 | 디자인가이드 §Design 별도 | 디자인 시스템 신규 적용 = **K-3 외부** (별도 epic) | (K-3 sub-scope 외) |

### 잔여 인프라 보강 정의 (K-3 외 K-4 잔여)
- **이미 DONE 결정 wire 보존**:
  - Phase B 잔여 3 (cj-314 wire 3·4·5) — DONE, 결정 wire 보존
  - 운영 cleanup 6 중 cj-313 retro + cj-312 retro — DONE, 결정 wire 보존
- **잔여**:
  - Phase C 잔여 ~30 (Phase 10 SLO family + Phase 8 + consistency)
  - cj-303 carryover 4 (D-FINOPS-13 + audit-fixes + Layer 2 P1 + Layer 3 P2)
  - 운영 cleanup 잔여 (cj-314 batch B + cj-319 N-1/N-2/N-3)
  - CI/web-e2e 환경 (sso 13 skipped + web-e2e 23 + test-suite-measure + web-test + lint-conventions)

---

## §3 결정 wire 보존 (cj-282~cj-319 종합 chain)

### 결정 wire 보존 항목 (CR 11-3 honest-DEFER 286번째)
- **Pilot W1 launch D-day 2026-09-14 KST** 보존 (D-3 countdown)
- **MVP-verification 우선** (사용자 2026-09-10 결정 wire) 보존
- **배포 작업 보류** (RESEND/RAILWAY 등) 보존
- **Resend (OQ-EPIC30+-2 v2) swap** 보존
- **cj-307 aal1 minimum fix** 보존
- **cj-304 4 critical gaps fix** 보존
- **cj-300 APScheduler KST** 보존
- **cj-314 wire 1 (capability matrix 10 fixes)** 보존
- **cj-314 wire 2 (Phase B 6 fixes)** 보존
- **cj-314 wire 3 (Phase 8 8 fixes)** 보존
- **cj-314 wire 4 (Phase B item 3 5 fixes)** 보존
- **cj-314 wire 5 (Phase C retroactive close-out)** 보존
- **cj-312 close-out retro** 보존
- **cj-313 close-out retro** 보존
- **cj-315 wire + retroactive correction** 보존
- **cj-317 alembic 0037 22 errors fix** 보존
- **cj-316 FastAPI lifespan migration** 보존
- **cj-318 operator immediate execution entry** 보존
- **cj-319 Track A-0 deploy-blocking wire** 보존
- **K-4 메모리 description** 보존 (단, "모든 기준 공통 첫 진입점 = Phase B 잔여 3개" outdated 정직 인정, update 결정 wire 보류)

### 결정 보류 (운전자) — K-3 검증 chunk 순서

| 옵션 | Chunk | 의도 |
|---|---|---|
| (a, RECOMMENDED first) | K-3 chunk 1 = 사용자 시나리오 §2.A UJ-1~4 검증 | MVP 핵심, tests/api/m0_onboarding + m8_budget + m9_abc + Phase 10 NFR11 P95 latency 검증 |
| (b) | K-3 chunk 2 = 핵심기능목록 §8.1 M0~M12 정합 | PRD 정합, capability matrix v1.54 EXTENSION 검증 |
| (c) | K-3 chunk 3 = 상세기능명세 §F 각 FR 정합 | cj-314 wire 1~5 + cj-303 audit-fixes 결정 wire 정합 |
| (d) | K-3 chunk 4 = 제약사항 (25 ADs + NFR) 정합 | cj-303 sso 인프라 AD-3 SSO 결정 wire 보존 검증 |
| (e) | K-3 chunk 5 = 화면정의 §UI 부분 검증 | web-e2e 23 unsuppress = 회귀 자동 검증 환경 |
| (f) | 디자인가이드 = K-3 외부 | 별도 epic, K-3 sub-scope 외 |

### 결정 보류 (운전자) — K-3 검증 method

| 옵션 | Method | 의도 |
|---|---|---|
| (α, RECOMMENDED) | docs-only 결정 wire | PRD §domain × capability matrix v1.54 EXTENSION × Phase A/B/C 결과 정합 검증 (source 변경 0건, atomic commit, 40분 내 안전) |
| (β) | docs+test 결정 wire | capability matrix EXTENSION 추가 + verify (Phase B/C와 동일 패턴) |
| (γ) | source 변경 결정 wire | PRD §F 각 FR 별 source code review (위험, 비추) |

---

## §4 다음 세션 가이드

### 즉시 (Step 2 = 본 sprint 후속)
- **K-3 첫 검증 chunk 결정 wire 진입** (옵션 (a) §3 chunk 1 추천 = 사용자 시나리오 §2.A UJ-1~4)
- 사용자 시나리오 §2.A UJ-1~4 검증 결정 wire (옵션 (α) docs-only RECOMMENDED):
  - tests/api/m0_onboarding 통과 확인 (PRE-EXISTING honestly DEFER 보존)
  - tests/api/m8_budget 통과 확인
  - tests/api/m9_abc 통과 확인
  - Phase 10 NFR11 P95 latency 검증 (apps/api/eslint/latency-budget-rule.js 7 KNOWN_ENDPOINTS + apps/api/core/latency_budget.py)
  - UJ-1~4 시나리오별 PRD §2.A 매핑 결정 wire 보존

### 후속 (Step 3+)
- K-3 chunk 2-5 검증 결정 wire (운전자 결정)
- 디자인가이드 = K-3 외부 (별도 epic) 명시

### 비정상 종료 안전 — 모든 step docs-only atomic
- source 변경 0건 보장
- 매 step commit 후 결정 wire 100% 보존
- 최악 = 마지막 commit 까지 손실 없음

---

## §5 Files (4 files docs-only atomic single sprint)

| # | File | 종류 | 변경량 |
|---|---|---|---|
| 1 | `memory/handoff-2026-09-11-k3-decision-wire-done.md` | NEW | 본 handoff ~280 LOC 5-section §1~§5 |
| 2 | `_bmad-output/implementation-artifacts/commit-msg-k3-decision-wire.txt` | NEW | commit message ~110 LOC |
| 3 | `_bmad-output/implementation-artifacts/sprint-status.yaml` | MODIFIED | v4.101 → **v4.102 EXTENSION** A746 + `last_updated_note_v4_102` 결정 wire |
| 4 | `memory/MEMORY.md` | MODIFIED | K-3 결정 wire hook + Active sprint state post K-3 결정 wire EXTENSION |

### Sprint form
- docs-only atomic single sprint
- 0 source 변경 + 0 test 변경 + 0 alembic 변경 + 0 PRD 변경 + 0 capability matrix 변경 + 0 migration source 변경
- 37 pins unchanged + 14 job matrix unchanged + PRD v7.0 §F/§M/§R unchanged + capability matrix v1.54 EXTENSION preserved + audit actions EXTENSION preserved + AD-14 stack pin EXTENSION preserved
- CR 11-3 honest-DEFER 286번째 chain cj-282 (220번째) → ... → cj-319 (285번째) → **K-3 결정 wire (286번째, 본 sprint)**
- cumulative 57/57 → **58/58** 결정 wire 보존
- sprint-status v4.101 → **v4.102 EXTENSION** A746

---

**Date**: 2026-09-11 KST (D-3, Pilot W1 launch D-day 2026-09-14 KST 까지 3일)
**Author**: Claude (operator = kjw)