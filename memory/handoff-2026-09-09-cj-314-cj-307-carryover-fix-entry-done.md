# cj-314 cj-307 carryover fix — Handoff

> **Sprint**: cj-314 cj-307 carryover fix (cj-style 271번째)
> **Date**: 2026-09-09 KST (D-5)
> **Status**: ✅ **CLOSED ✅ HONEST** (entry sprint, sprint-status v4.87 → v4.88 EXTENSION)
> **Next**: cj-314 wire 1 (capability matrix drift 10 fixes, ~1h, RECOMMENDED) 또는 cj-314 batch A 또는 cj-316

---

## §1 Sprint Overview

cj-314 entry sprint 는 **cj-312 wire 의 "32 failures" estimate 의 정직 회복** + **cj-307 carryover 의 HONEST scope (66 failures + 22 errors = 88 items) triage** 입니다.
- cj-312 wire 의 "32 failures" 가 actual 66 failures 의 2x underestimate 정직 인정
- cj-313 stale tests 정정이 collection errors 만 fix 했고, deeper test failures 66건이 surface 됨
- cj-314 multi-sub-sprint 결정 wire: wire 1~6 또는 batch A/B/C

---

## §2 Sprint Scope (5 files docs-only atomic)

| File | Type | LOC | Description |
|---|---|---|---|
| `phase-30-cj-314-cj-307-carryover-fix-entry-2026-09-09.md` | NEW content | ~350 | 9-section §1~§9 sprint doc |
| `commit-msg-cj-314.txt` | NEW meta | ~95 | commit message |
| `handoff-2026-09-09-cj-314-cj-307-carryover-fix-entry-done.md` | NEW meta | ~150 | 본 handoff |
| `sprint-status.yaml` | MODIFIED meta | +A732 +last_updated_note_v4_88 | v4.87 → v4.88 EXTENSION |
| `memory/MEMORY.md` | MODIFIED meta | +cj-314 hook +active sprint state | hook EXTENSION |

---

## §3 cj-312 wire estimate 의 정직 회복

### cj-312 wire 의 "32 failures + 22 errors + 3 collection errors" claim
- **"3 collection errors"** → cj-313 으로 해소 (cj-style 270th 보존)
- **"22 errors"** → 실제 pytest 결과와 일치 (cj-312 audit 의 단일 정확 부분)
- **"32 failures"** → actual 66 failures = 2x underestimate ⚠️

### 정직 회복 rationale
- CR 11-3 honest-DEFER discipline: cj-style 257th + 267th + 270th 패턴 verbatim mirror
- cj-313 stale tests 정정이 collection errors 만 fix 했고, deeper test failures 66건이 surface 됨
- 결정 wire 보존: cj-312 wire 의 audit 결과 종합 (19 findings) 결정 wire 그대로

---

## §4 cj-307 carryover 의 HONEST scope (88 items)

### A. Capability matrix drift — 10 failures
- test_capability_matrix_v1_21_drift / v1_25 / v1_26 / v1_28 / v1_29 / v1_30 / v1_31 / v1_39 / v1_51 / v1_52 (10)
- **Root cause**: docs/capability-matrix.md 의 특정 version reference 부재

### B. Phase 10 SLO family — 30 failures (largest)
- audit_action (6) + error_budget (6) + governance (6) + multi_region_aggregator (5) + slo_burn_rate_evaluator (6) + slo_dsl (5) = 34 (overlapping count)
- **Root cause**: apps/api/modules/slo/ 의 typed exception class 이름 변경 + VALID_* prefix + 새 함수 미구현

### C. Phase 8 ESLint/SLO/SLI — 9 failures
- p99_budget (5) + slo_sli (4)
- **Root cause**: apps/web/ ESLint rule 파일 부재 + docs/slo-sli.md 부재

### D. Phase 5/9/16/26/30 + Phase 3 — 7 failures
- Phase 3 hook migration (1) + Phase 5 capability integration (2) + Phase 5 audit log verification (1) + Phase 9 audit action (1) + Phase 16 scheduled executive dispatch (1) + Phase 26 cost anomaly ML prediction (1) + Phase 8 performance audit action (1) = 8

### E. Phase 30 scheduled reports — 3 failures
- idempotency_violation + persistence_error + invalid_strategy
- **Root cause**: apps/api/modules/reports/scheduled_serializers 의 typed exception 미구현

### F. Other consistency — 7 failures
- commit_consistency + conventions_lint + production_consumption_label + sdr_test_count_drift + audit_action_centralization + capability_matrix_phase_25_8_acs + phase_8_p99_budget (1 more)

### G. 22 errors (12 visible + 10 TBD)
- test_epic_15_alembic_0037_external_identities (12 visible: migration shape + indexes + RLS policies + check constraints + downgrade)
- **Root cause**: alembic 0037 migration shape drift test

---

## §5 cj-314 multi-sub-sprint 결정 wire

### Option 1: 6 sub-sprint approach (atomic 단일 sprint 원칙)
| Sprint | Scope | Effort |
|---|---|---|
| cj-314 wire 1 | Capability matrix drift 10 fixes | ~1h |
| cj-314 wire 2 | Phase 10 SLO family ~30 fixes | ~2-3h |
| cj-314 wire 3 | Phase 8 ESLint/SLO/SLI 9 fixes | ~1h |
| cj-314 wire 4 | Phase 5/9/16/26/30/Phase 30 + others ~10 fixes | ~1-2h |
| cj-314 wire 5 | Epic 15 alembic 0037 12 errors | ~1h |
| cj-314 wire 6 | errors TBD 10 fixes | ~1h |
| **TOTAL** | **66 failures + 12 errors = 78 fixes** | **~7-9h** |

### Option 2: 3 batch approach (큰 sprint batch)
| Sprint | Scope | Effort |
|---|---|---|
| cj-314 batch A | Capability matrix + Phase 8 + consistency ~26 fixes | ~2-3h |
| cj-314 batch B | Phase 10 SLO family + Phase 5/9/16/26/30 ~37 fixes | ~4-5h |
| cj-314 batch C | Epic 15 alembic + errors TBD ~22 fixes | ~2h |
| **TOTAL** | **85 fixes** | **~8-10h** |

### Option 3: Honest-defer priority (HIGH severity 만 먼저)
| Sprint | Scope | Effort |
|---|---|---|
| cj-314 wire HIGH | Phase 10 SLO family ~30 fixes | ~2-3h |
| 나머지 honestly DEFER | Capability matrix drift + Phase 8 + Phase 30 + others + errors TBD | post-launch |

---

## §6 결정 wire 보존 (cj-309~cj-313 wire 결정 wire 그대로)

### 결정 wire 보존 항목
- Pilot W1 launch D-day 2026-09-14 KST
- cj-309b B-1 Pilot candidate outreach (Tier 1 5 + Tier 2 3 = 8, D-2 발송 honestly DEFER)
- Resend (OQ-EPIC30+-2 v2) swap
- cj-307 aal1 minimum fix
- cj-304 4 critical gaps fix
- cj-300 APScheduler KST
- capability matrix v1.54 EXTENSION
- audit_action EXTENSION
- **cumulative 43 → 44 sprints** 결정 wire 보존

---

## §7 CR 11-3 honest-DEFER 271번째

### 결정 wire chain (cj-style 220번째~271번째)
- cj-282 (220번째) → ... → cj-313 wire (270번째)
- **cj-314 entry (271)** ← **본 sprint**

### cumulative 결정 wire 보존
- **43/43** (cj-282~cj-313) → **+1 NEW = 44/44 cumulative** (cj-314 entry 신규)
- 결정 wire 보존: cj-309~cj-313 wire 결정 wire 그대로
- sprint-status v4.87 → **v4.88 EXTENSION** 결정 wire (A732 cj-314 entry + last_updated_note_v4_88)

### 정직 회복
- 0 source code 변경 (cj-314 entry 는 docs-only atomic single sprint)
- 37 pins unchanged (cj-303 EXTENSION 보존)
- PRD v7.0 §F/§M/§R unchanged
- capability matrix v1.54 EXTENSION preserved
- audit actions EXTENSION preserved

---

## §8 Next unblocked 결정 wire 보류 + 결정 wire 일자

### 결정 보류 5개 옵션
| 옵션 | 내용 | Effort |
|---|---|---|
| **(a, RECOMMENDED next) cj-314 wire 1** | Capability matrix drift 10 fixes (atomic single sprint) | ~1h |
| **(b) cj-314 batch A** | Capability matrix + Phase 8 + consistency ~26 fixes | ~2-3h |
| **(c) cj-314 wire 2** | Phase 10 SLO family ~30 fixes | ~2-3h |
| **(d) cj-316** | FastAPI on_event → lifespan migration (HIGH severity) | ~1-2h |
| **(e) carryover honestly DEFER 유지** | cj-314 wire 결정 보류 | 0 effort |

### 결정 wire 일자
- **2026-09-09 KST (D-5)**

### Honestly DEFER 결정 wire
- ① Pilot launch D-day (2026-09-14) → 비용 발생 결정 wire 보류
- ② W1~W8 weekly follow-up (launch day 부터)
- ③ PRD v2 EXTENSION (cj-314 fix 후)
- ④ 비용 발생 항목 모두 (사용자 결정 wire, launch day 까지 honestly DEFER)

---

## §9 Cross-references + CR 11-3 정직 회복

### Cross-references
- **cj-style feedback** `prioritize-mvp-hardening-before-deploy` (2026-09-07) — 본 sprint 의 trigger
- **cj-style feedback** `count-remaining-before-start` (2026-09-07) — 매 주요 업무 진입 직전 잔여 주요 업무 개수 안내
- **cj-307 wire** (`a1cb7ad`) — auth-callback aal1 minimum fix
- **cj-310 retroactive correction** (`6972571`) — headline 정직 회복 패턴 출처
- **cj-311 entry** (`69d7d72`) — 7-Checkpoint MVP Audit Entry
- **cj-312 wire** (`a0a27d1`) — 7-Checkpoint Audit Wire (cj-314 의 retroactive correction 대상)
- **cj-313 wire** (`cfe5eca`) — pytest rootdir 정정 (cj-314 의 prerequisite)
- **cj-314 entry** (본 sprint) — cj-307 carryover fix scope triage (cj-style 271번째)

### 결정 wire 정직 회복
- 66 failures + 22 errors = 88 total items to fix
- 결정 wire 보존: cj-309~cj-313 wire 결정 wire 그대로 + 0 source code 변경 (cj-314 entry 는 docs-only)
- CR 11-3 honest-DEFER 271번째 정직 회복 (cj-312 wire estimate 2x underestimate)

---

**CJ-314 ENTRY 결정 wire 보존 완료**

**CR 11-3 honest-DEFER 271번째 결정 wire chain: cj-282 (220번째) → ... → cj-313 wire (270번째) → cj-314 entry (271번째, 본 sprint)**

**Next**: cj-314 wire 1 (capability matrix drift 10 fixes, ~1h, RECOMMENDED) 또는 cj-314 batch A 또는 cj-316
