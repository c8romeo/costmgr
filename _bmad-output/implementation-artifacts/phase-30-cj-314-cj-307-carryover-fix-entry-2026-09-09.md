# cj-314 cj-307 carryover fix — Entry Sprint 결과

> **Sprint**: cj-314 cj-307 carryover fix (cj-style 271번째)
> **Date**: 2026-09-09 KST (D-5, Pilot W1 launch D-day 2026-09-14 KST)
> **Territory**: Phase 30 — MVP hardening 7-checkpoint audit 의 Checkpoint 2 (Test coverage) cj-307 carryover fix scope
> **Author**: Claude (operator = kjw)
> **Sprint form**: entry (cj-style 271번째 docs-only atomic single sprint, 후속 wire sprints 진입 결정 wire)
> **직전 sprint**: cj-313 wire (`cfe5eca`, sprint-status v4.86 → v4.87 EXTENSION)

---

## §1 의도 분석 — cj-312 wire 의 "32 failures" estimate 정직 회복

### cj-312 wire 의 claim
> "32 failures + 22 errors + 3 collection errors 의 정확한 triage" (cj-style 269번째 audit 결과)

### 실제 verification 결과 — ⚠️ 2x underestimate 정직 회복
- cj-313 wire 가 7 stale tests 정정한 후 pytest 재실행 결과: **5554 tests collected, 66 failed + 22 errors + 5306 passed + 160 skipped**
- cj-312 wire 의 "3 collection errors" → cj-313 으로 해소 (cj-style 270th 보존)
- cj-312 wire 의 "22 errors" → 실제 일치 (cj-312 audit 의 단일 정확 부분)
- cj-312 wire 의 "32 failures" → **actual 66 failures = 2x underestimate** ⚠️

### 정직 회복 rationale
- CR 11-3 honest-DEFER discipline: cj-style 257th (cj-305b retroactive) + 267th (cj-310 retroactive) + 270th (cj-313 retroactive) 패턴 verbatim mirror
- cj-312 wire 의 "32 failures" estimate 의 정직 회복을 본 sprint 의 본질로 삼음
- cj-313 stale tests 정정이 collection errors 만 fix 했고, deeper test failures 66건이 surface 됨
- 실제 cj-307 carryover scope = 88 total items (66 failures + 22 errors)

### 결정 wire 보존
- cj-309~cj-313 wire 결정 wire 그대로 (Pilot W1 + cj-309b B-1 + Resend + cj-307 aal1 + cj-304 4 gaps + cj-300 APScheduler KST + capability matrix v1.54 EXTENSION + audit_action EXTENSION)
- cj-313 fix 결과 보존 (5554 tests + 0 collection errors)
- cj-316 FastAPI on_event → lifespan migration 결정 wire 보존

---

## §2 cj-314 cj-307 carryover 의 실제 scope (66 failures + 22 errors = 88 items)

### A. Capability matrix drift — 10 failures
```
tests/integration/test_capability_matrix_v1_21_drift.py::test_capability_matrix_v1_21_title
tests/integration/test_capability_matrix_v1_25_drift.py::TestCapabilityV125Version::test_capability_matrix_at_v1_25
tests/integration/test_capability_matrix_v1_26_drift.py::TestCapabilityMatrixVersion::test_matrix_at_v1_26
tests/integration/test_capability_matrix_v1_28_drift.py::TestCapabilityMatrixVersion::test_matrix_at_v1_28
tests/integration/test_capability_matrix_v1_29_drift.py::TestCapabilityMatrixVersion::test_matrix_at_v1_29
tests/integration/test_capability_matrix_v1_30_drift.py::TestCapabilityMatrixVersion::test_matrix_at_v1_30
tests/integration/test_capability_matrix_v1_31_drift.py::TestCapabilityMatrixVersion::test_matrix_at_v1_31
tests/integration/test_capability_matrix_v1_39_drift.py::test_capability_matrix_version_v1_39
tests/integration/test_capability_matrix_v1_51_drift.py::test_capability_matrix_phase_25_8_acs
tests/integration/test_capability_matrix_v1_52_drift.py::test_capability_matrix_v1_52_header_present
```

**Root cause (추정)**: docs/capability-matrix.md 의 특정 version reference 부재 (cj-297 wire 의 capability matrix v1.54 EXTENSION 이전 version 들이 drift test 에서 검증)

### B. Phase 10 SLO family — 30 failures (largest category)
```
tests/api/core/test_phase_10_audit_action.py: 6 failures
  - test_audit_action_union_accepts_slo_target_updated
  - test_audit_action_union_accepts_slo_budget_exhausted
  - test_audit_action_union_accepts_slo_violation_detected
  - test_normalize_audit_action_slo_target_updated_returns_enum
  - test_invalid_audit_action_returns_false
  - test_slo_engineering_registered_in_registry

tests/api/core/test_phase_10_error_budget.py: 6 failures
tests/api/core/test_phase_10_governance.py: 6 failures
tests/api/core/test_phase_10_multi_region_aggregator.py: 5 failures
tests/api/core/test_phase_10_slo_burn_rate_evaluator.py: 6 failures
tests/api/core/test_phase_10_slo_dsl.py: 5 failures
```

**Root cause (추정)**: apps/api/modules/slo/ 의 typed exception class 이름 변경 + VALID_* prefix 추가 + 새 함수 미구현 (cj-313 fix #3/#4 의 import 정정 외 추가 변경 필요)

### C. Phase 8 ESLint/SLO/SLI — 9 failures
```
tests/api/core/test_phase_8_p99_budget.py: 5 failures
  - test_eslint_rule_file_exists
  - test_eslint_rule_lists_known_endpoints
  - test_eslint_rule_emits_unmapped_endpoint_message
  - test_eslint_rule_handles_dry_run_marker
  - (1 more)

tests/api/core/test_phase_8_slo_sli.py: 4 failures
  - test_slo_sli_doc_exists
  - test_slo_sli_doc_defines_4_canonical_slas
  - test_slo_sli_doc_defines_30d_rolling_window
  - test_slo_sli_doc_owner_only_rbac
```

**Root cause (추정)**: apps/web/ ESLint rule 파일 부재 + docs/slo-sli.md 부재

### D. Phase 5/9/16/26/30 + Phase 3 — 7 failures
```
tests/api/core/test_phase_3_0_hook_migration.py::test_hook_grants_execute_to_postgres
tests/api/core/test_phase_5_audit_log_verification.py::TestCR1Compliance::test_dr_drill_emits_audit_first
tests/api/core/test_phase_5_capability_integration.py::TestMultiRegionBackupCapability::test_capability_granted_to_all_4_industries
tests/api/core/test_phase_5_capability_integration.py::TestMultiRegionFailoverCapability::test_capability_granted_to_all_4_industries
tests/api/core/test_phase_9_audit_action.py::test_audit_action_union_includes_chaos_engineering_action
tests/api/core/test_phase_16_scheduled_executive_dispatch.py::test_invalid_schedule_raises_error
tests/api/core/test_phase_26_cost_anomaly_ml_prediction_audit_action.py::test_action_class_count_includes_cost_anomaly_ml_prediction
tests/api/core/test_phase_8_performance_audit_action.py::test_audit_action_union_includes_performance_test_action
```

### E. Phase 30 scheduled reports — 3 failures
```
tests/integration/test_phase_30_scheduled_reports.py:
  - TestScheduledReportsIdempotency::test_idempotency_violation_raises
  - TestScheduledReportsErrors::test_scheduled_report_persistence_error
  - TestScheduledReportsSchedule::test_schedule_report_invalid_strategy_raises
```

**Root cause (추정)**: apps/api/modules/reports/scheduled_serializers 의 typed exception 미구현 (cj-313 fix #5 의 import path 정정 외 추가 변경 필요)

### F. Other consistency — 7 failures
```
tests/integration/test_commit_consistency.py::test_commit_subject_story_key_matches_done_entry
tests/integration/test_conventions_lint.py::test_ruff_passes_on_clean_repo
tests/integration/test_production_consumption_label_consistency.py::test_incomplete_bom_fallback_reason_parity
tests/integration/test_sdr_test_count_drift.py::test_max_sdr_claim_matches_pytest_collection
tests/services/test_audit_action_centralization.py::test_no_legacy_emit_audit_call_sites
```

### G. 22 errors (12 visible + 10 TBD)
```
tests/api/core/test_epic_15_alembic_0037_external_identities.py: 12 errors visible
  - TestMigrationShape::test_metadata_jsonb
  - TestIndexes::test_provider_puid_unique
  - TestIndexes::test_user_provider_index
  - TestIndexes::test_tenant_provider_index
  - TestIndexes::test_last_used_at_desc_index
  - TestCheckConstraints::test_provider_check
  - TestCheckConstraints::test_puid_not_empty_check
  - TestRLSPolicies::test_rls_enabled
  - TestRLSPolicies::test_tenant_isolation_policy
  - TestRLSPolicies::test_service_role_bypass
  - TestRLSPolicies::test_anon_block
  - TestDowngrade::test_drop_table
  - TestDowngrade::test_drop_rls
```

**Root cause (추정)**: alembic 0037 migration shape + indexes + RLS policies + check constraints 의 drift test (alembic upgrade/downgrade 후 검증)

---

## §3 cj-314 multi-sub-sprint 결정 wire (cj-314 wire 1~6 또는 batch A/B/C)

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
| cj-314 wire HIGH | High-severity failures only (Phase 10 SLO family) ~30 fixes | ~2-3h |
| 나머지 honestly DEFER | Capability matrix drift + Phase 8 + Phase 30 + others + errors TBD | post-launch |

---

## §4 Sprint Scope (5 files docs-only atomic)

| File | Type | LOC | Description |
|---|---|---|---|
| `phase-30-cj-314-cj-307-carryover-fix-entry-2026-09-09.md` | NEW content | ~350 | 9-section §1~§9 본 sprint doc |
| `commit-msg-cj-314.txt` | NEW meta | ~95 | commit message |
| `handoff-2026-09-09-cj-314-cj-307-carryover-fix-entry-done.md` | NEW meta | ~150 | 7-section §1~§7 handoff |
| `sprint-status.yaml` | MODIFIED meta | +A732 +last_updated_note_v4_88 | v4.87 → v4.88 EXTENSION |
| `memory/MEMORY.md` | MODIFIED meta | +cj-314 hook +active sprint state | hook EXTENSION |

---

## §5 cj-312 wire estimate 의 정직 회복

### cj-312 wire 의 "32 failures + 22 errors + 3 collection errors" claim
- **"3 collection errors"** → cj-313 으로 해소 (cj-style 270th 보존)
- **"22 errors"** → 실제 pytest 결과와 일치 (cj-312 audit 의 단일 정확 부분)
- **"32 failures"** → actual 66 failures = 2x underestimate ⚠️

### 정직 회복 rationale
- CR 11-3 honest-DEFER retroactive correction discipline (cj-style 257th + 267th + 270th verbatim mirror)
- cj-313 stale tests 정정이 collection errors 만 fix 했고, deeper test failures 66건이 surface 됨
- 결정 wire 보존: cj-312 wire 의 audit 결과 종합 (19 findings) 결정 wire 그대로

---

## §6 결정 wire 보존 (cj-309~cj-313 wire 결정 wire 그대로)

### 결정 wire 보존 항목
- **Pilot W1 launch D-day 2026-09-14 KST** 보존
- **cj-309b B-1 Pilot candidate outreach** 보존 (Tier 1 5 + Tier 2 3 = 8, D-2 발송 honestly DEFER)
- **Resend (OQ-EPIC30+-2 v2) swap** 보존
- **cj-307 aal1 minimum fix** 보존
- **cj-304 4 critical gaps fix** 보존
- **cj-300 APScheduler KST** 보존
- **cumulative 43 → 44 sprints** 결정 wire 보존

### cj-307 carryover 의 HONEST scope
- cj-307 의 32+22+3 estimate = 57 items
- Actual cj-307 carryover scope = **88 items (66 failures + 22 errors)** = 1.5x cj-307 estimate
- 결정 wire: cj-314 wire 1~6 또는 batch A/B/C 진입

---

## §7 CR 11-3 honest-DEFER 271번째

### 결정 wire chain (cj-style 220번째~271번째)
- cj-282 (220번째) → cj-282a (221+222) → cj-282b (223~238) → cj-297 (237th) → cj-298 (238th)
- cj-299 (239~242) → cj-300 (243+244) → cj-301 (245) → cj-302 (246+247)
- cj-303 (248+249+250) → cj-304 (251+252+253) → cj-305 (254+255)
- cj-305b (256+257) → cj-306 (259) → cj-307 (261) → cj-308 (263)
- cj-309 (264) → cj-309b (265) → cj-310 (266) → cj-310 retroactive (267)
- cj-311 entry (268) → cj-312 wire (269) → cj-313 wire (270)
- **cj-314 entry (271)** ← **본 sprint**

### cumulative 결정 wire 보존
- **43/43** (cj-282~cj-313) → **+1 NEW = 44/44 cumulative** (cj-314 entry 신규)
- 결정 wire 보존: cj-309~cj-313 wire 결정 wire 그대로
- sprint-status v4.87 → **v4.88 EXTENSION** 결정 wire (A732 cj-314 entry + last_updated_note_v4_88)

### CR lessons applied
- CR 0-2 (RLS) + CR 1-1 (audit-first INSERT) + CR 1-1 (ContextVar + RSC boundary)
- CR 4-3/4-4 + CR 5-1 (Decimal precision banker's rounding)
- CR 9-6 (commit message `git commit -F <file>`)
- **CR 11-3 (honest-DEFER retroactive correction discipline)** — cj-314 entry 에서 verbatim mirror (cj-style 257th + 267th + 270th 패턴)
- CR 11-4 (P-015 pure validator pattern)
- CR 12-1 (L4 industry-agnostic capability)
- CR 12-5 (D-14 typed exception envelope + D-PARITY-01 + D-GATE-01)

---

## §8 Honestly DEFER 결정 wire 보존

### 비용 발생 항목 honestly DEFER (사용자 결정 wire 2026-09-09)
- ❌ Railway Hobby plan ($5/mo) — launch day 결정 wire
- ❌ Vercel Pro plan ($20/mo) — launch day 결정 wire
- ❌ Resend Pro plan ($20/mo) — launch day 결정 wire
- ❌ Supabase Pro plan ($25/mo) — launch day 결정 wire
- ❌ Custom DNS (Cloudflare) — launch day 결정 wire
- ❌ Sentry Pro plan — launch day 결정 wire

### cj-style 결정 wire honestly DEFER
- ❌ Pilot candidate outreach 발송 (D-2 2026-09-12 honestly DEFER)
- ❌ W1~W8 weekly tracking (launch day 부터 결정 wire)

### cj-314 + cj-316 carryover 결정 wire 보존
- **cj-314 wire 1~6** 또는 **batch A/B/C** 결정 wire 보류 (operator choice)
- **cj-316 FastAPI on_event → lifespan migration** (HIGH severity, cj-style 272번째) — pytest 실행 시 DeprecationWarning visible

### PRE-EXISTING honestly DEFER 6건 (cj-style 보존)
1. web-e2e Playwright 23 skip (cj-282a/b)
2. test-suite-measure 잔여 (cj-282a)
3. web-test 잔여 (cj-282a)
4. lint-conventions (apps/web)
5. Sentry (post-W1, cj-305 wire)
6. custom DNS (post-W1, cj-305 wire)

---

## §9 Next unblocked 결정 wire 보류 + 결정 wire 일자

### 결정 보류 옵션 (cj-314 entry 직후)
| 옵션 | 내용 | Effort |
|---|---|---|
| **(a) cj-314 wire 1 — capability matrix drift 10 fixes** | atomic single sprint | ~1h |
| **(b) cj-314 batch A — capability matrix + Phase 8 + consistency ~26 fixes** | batch single sprint | ~2-3h |
| **(c) cj-314 wire 2 — Phase 10 SLO family ~30 fixes** | atomic single sprint | ~2-3h |
| **(d) cj-316 FastAPI on_event → lifespan migration** | HIGH severity | ~1-2h |
| **(e) carryover honestly DEFER 유지** | cj-314 wire 결정 보류 | 0 effort |

### 결정 wire 일자
- **2026-09-09 KST (D-5)**

### Honestly DEFER 결정 wire (cj-314 entry close-out 후)
- ① Pilot launch D-day (2026-09-14) → 비용 발생 결정 wire 보류
- ② W1~W8 weekly follow-up 결정 wire (launch day 부터)
- ③ PRD v2 EXTENSION 결정 wire (cj-314 fix 후)
- ④ 비용 발생 항목 모두 (사용자 결정 wire, launch day 까지 honestly DEFER)

---

## §10 Cross-references + CR 11-3 정직 회복

### Cross-references
- **cj-style feedback** `prioritize-mvp-hardening-before-deploy` (2026-09-07) — 본 sprint 의 trigger
- **cj-style feedback** `count-remaining-before-start` (2026-09-07) — 매 주요 업무 진입 직전 잔여 주요 업무 개수 안내
- **cj-307 wire** (`a1cb7ad`) — auth-callback aal1 minimum fix (cj-314 결정 wire 의 source)
- **cj-310 retroactive correction** (`6972571`) — headline 정직 회복 (cj-314 의 정직 회복 패턴 출처)
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

**Next**: cj-314 wire 1 (capability matrix drift 10 fixes, ~1h, RECOMMENDED) 또는 cj-314 batch A (~26 fixes, ~2-3h) 또는 cj-316 FastAPI on_event → lifespan migration (~1-2h)
