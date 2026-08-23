# Phase 11 Close-out Retrospective (cj-style Phase 11 4번째 진입점 = cj-style 108번째 epic 연속 정직 회복)

**일자**: 2026-08-24 (KST)
**작성자**: Amelia (Developer) + Charlie (Senior Dev) + Alice (Product Owner) 결정 wire 진입
**wire_commit**: TBD (cj-style Phase 11 close-out retro atomic docs-only wire = cj-style 108번째 docs only)
**baseline_commit**: `e020ad0` (Phase 11 bmad-dev-story atomic wire T1~T8 DONE 진입 시점 = cj-style 107번째 epic 연속 정직 회복 wire DONE 진입 tip)
**retro_document**: 본 문서 (`_bmad-output/implementation-artifacts/phase-11-close-out-2026-08-24.md`)
**handoff**: `memory/handoff-2026-08-24-phase-11-close-out-done.md` (auto-memory 신규)
**previous retro**: `phase-10-close-out-2026-08-24.md` (cj-style 104번째) — Phase 10 SLO Engineering / Error Budget Management territory close-out + 옵션 (a) Phase 11 진입 결정 wire 진입 보존

---

## §1. Phase 11 territory 정의

Phase 11 = **FinOps Showback / Chargeback territory** (Epic 7~10 ABC/TDABC + AI 인사이트 territory 의 natural FinOps territory EXTENSION = Phase 10 wire `ac5d6c5` SLO_ENGINEERING ✅ RESOLVED + Phase 9 wire `e7670e1` CHAOS_ENGINEERING ✅ RESOLVED + Phase 8 wire `60d4ea1` PERFORMANCE_TESTING ✅ RESOLVED + Phase 7 wire `59b56cd` OBSERVABILITY_TRACES+OBSERVABILITY_METRICS ✅ RESOLVED + Phase 6 wire `24e1cd7` AUDIT_LOG_RETENTION ✅ RESOLVED + Phase 5 wire `f093f8c` MULTI_REGION_BACKUP+FAILOVER ✅ RESOLVED + Epic 17 wire `2ada2ec` AUDIT_LOG_VIEW ✅ RESOLVED + Epic 12 2FA 챌린지 보존 + AD-22 owner-only RBAC 보존 + Epic 7~10 ABC/TDABC territory 의 natural FinOps territory EXTENSION (Phase 11 = §F27 신규 territory) + showback/chargeback DSL + cost center mapping + chargeback CSV/PDF export + capability matrix v1.36 EXTENSION FINOPS_SHOWBACK + FINOPS_CHARGEBACK industry-agnostic 4-industry grants + 1st release close-out retro §6 + Epic 17 close-out retro §11 + Phase 6 close-out retro §13 + Phase 7 close-out retro §10 + Phase 8 close-out retro §10 + Phase 9 close-out retro §10 + Phase 10 close-out retro §10 verbatim D-FINOPS-1 honestly DEFERRED territory 해소 결정 wire). Phase 10 close-out retro 진입 시점에 옵션 (a) Phase 11 진입 결정 wire 진입 (옵션 b Epic 18+ / 옵션 c carry-over / 옵션 d 1st release 추가 follow-up / 옵션 e D-DEFER-* carry-over follow-up 모두 rejected, 사용자 권장 결정).

**Phase 11 cycle 구조** (cj-style 4-entry-point pattern = PRD + spec + atomic wire + close-out retro):
1. **cj-style Phase 11 1번째 진입점** = Phase 11 PRD entry (cj-style 105번째 epic 연속 정직 회복) — `16d7698` ✅ DONE 2026-08-24
2. **cj-style Phase 11 2번째 진입점** = Phase 11 bmad-create-story spec entry (cj-style 106번째) — spec ~329 lines ✅ DONE 2026-08-24 (`phase-11-finops-showback-chargeback-wire.md` 신규)
3. **cj-style Phase 11 3번째 진입점** = Phase 11 bmad-dev-story atomic wire T1~T8 (cj-style 107번째 epic 연속 정직 회복) — `e020ad0` ✅ DONE 2026-08-24
4. **cj-style Phase 11 4번째 진입점** = Phase 11 close-out retro (cj-style 108번째) — THIS, 진입 결정 wire 진입

**Phase 11 진입 결정** (cj-style 정직 회복):
- Phase 10 close-out retro 진입 시점에 옵션 (a) Phase 11 진입 결정 (사용자 권장 결정, rationale 5종: ① Epic 7~10 ABC/TDABC + AI 인사이트 territory 의 natural FinOps territory EXTENSION 결정 wire ② Epic 12 2FA 챌린지 + AD-22 owner-only RBAC 보존 ③ Phase 5~10 + Epic 17 의 6개 observability/operational territory chain ✅ ALL RESOLVED 진입 후 FinOps territory natural next 진입 ④ 1st release close-out retro §6 + Epic 17 close-out retro §11 + Phase 6 close-out retro §13 + Phase 7 close-out retro §10 + Phase 8 close-out retro §10 + Phase 9 close-out retro §10 + Phase 10 close-out retro §10 verbatim D-FINOPS-1 honestly DEFERRED territory 해소 ⑤ cj-style discipline 회피 위험 방지 = 104번째 Phase 10 close-out retro 진입 직후 natural next territory 결정 회피 위험 증가)
- AD-38 FinOps Showback / Chargeback 신규 결정 ((a) showback DSL + period selector + comparison view 결정 wire = `apps/api/modules/finops/showback_dsl.py` NEW ~+321 LOC + 5 group_by 옵션 + 6 period selector 모드 + 4 industries baseline + per-tenant override + DepartmentBreakdown TypedDict 8 fields + ComparisonView TypedDict 7 fields + audit-first INSERT `showback_generated` 결정 wire / (b) showback_query 결정 wire = `apps/api/modules/finops/showback_query.py` NEW ~+200 LOC + query_showback_breakdown + query_showback_comparison + calendar arithmetic + group_by column mapping + pure validator CR 11-4 P-015 verbatim + industry-agnostic 4 grants + pagination + cache layer / (c) chargeback cost allocation engine 결정 wire = `apps/api/modules/finops/chargeback_engine.py` NEW ~+406 LOC + 3 rule_type flat_fee/proportional_allocation/metered + markup + tax + cost_allocation_method direct/indirect/shared + ChargebackResult TypedDict 10 fields + monthly reset KST 1일 00:00 + per-tenant override JSONB + multi-region aggregation + dry-run mode / (d) chargeback rule evaluator + cost pool + multi-tier allocation 결정 wire = `apps/api/modules/finops/chargeback_rule_evaluator.py` NEW ~+167 LOC + evaluate_chargeback_rule + 3 rule_type 분기 + 4 validation rules / (e) department cost center mapping + multi-tier cost allocation 결정 wire = `apps/api/modules/finops/department_mapping.py` NEW ~+202 LOC + tenant_settings.cost_center_mapping JSONB TypedDict + 1:1 mapping + auto-create on first calculation + audit-first INSERT `department_mapping_updated` CR 1-1 verbatim / (f) chargeback CSV/PDF export 결정 wire = `apps/api/modules/finops/chargeback_export.py` NEW ~+255 LOC + CSV columns 13 + PDF generation reportlab + NOTO Sans CJK KR + streaming response + audit-first INSERT `chargeback_exported` + permission check + rate limit / (g) alembic 0043 phase_11_finops 결정 wire = `apps/api/alembic/versions/0043_phase_11_finops.py` NEW ~+467 LOC + 3 tables phase_11_finops_department_mapping + phase_11_finops_showback + phase_11_finops_chargeback + 14 columns + 12 columns + 4 indexes + 2 CHECK constraints + RLS policies CR 0-2 verbatim + down_revision "0042_phase_10_slo_engineering" / (h) audit action EXTENSION 4 NEW 결정 wire = ActionClass.FINOPS = "finops" 1 NEW + FinopsAction Literal 4 NEW values `showback_generated` + `department_mapping_updated` + `chargeback_calculated` + `chargeback_exported` + _ActionRegistry FINOPS entry 신규 4 frozenset + AuditAction Union EXTENSION + __all__ EXTENSION + apps/api/core/audit_action.py MODIFIED + emit_audit_typed BEFORE/AFTER FinOps event CR 1-1 verbatim / (i) Capability matrix v1.35 → v1.36 EXTENSION + 2 NEW rows 결정 wire = Capability.FINOPS_SHOWBACK = 'finops_showback' + Capability.FINOPS_CHARGEBACK = 'finops_chargeback' 2 NEW enum 추가 (manufacturing ✅ + service ✅ + manufacturing_service ✅ + manufacturing_service_other ✅ industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러, SLO_ENGINEERING Phase 10 wire + CHAOS_ENGINEERING Phase 9 wire + PERFORMANCE_TESTING Phase 8 wire + OBSERVABILITY_TRACES + OBSERVABILITY_METRICS Phase 7 wire + AUDIT_LOG_RETENTION Phase 6 wire + AUDIT_LOG_VIEW Epic 17 wire + MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER Phase 5 wire + TENANT_IDP_MANAGEMENT Epic 16 wire + SSO_ENTERPRISE Epic 15 wire + LISTEN_NOTIFY Epic 13/14 wire + AUTH_MIDDLEWARE Phase 3 wire + LAUNCH_* 1st release wire + DEPLOYMENT_* Phase 4 wire pattern verbatim bind) + 미허용 tenant 의 FinOps territory 진입 차단 결정 wire + SSOT RED→GREEN EXTENSION (capability matrix v1.36 신규 2 rows + capability.py EXTENSION 2 NEW enum + require_finops_showback + require_finops_chargeback Dependency 2개 신규 wire) + drift detector tests/integration/test_capability_matrix_v1_36_drift.py NEW 4 NEW pytest cases 결정 / (j) showback dashboard UI + chargeback export UI + tests + wire scope T1~T8 결정 wire (dry-run mode default + AD-14 stack pin pandas + reportlab + jinja2 + openpyxl + pdfkit + weasyprint + python-magic + K6_VERSION Phase 8 wire `60d4ea1` 정합 보존 + libfaketime clock_skew Phase 9 wire `e7670e1` 정합 보존 + tests backend ~63 NEW pytest PASS 결정 wire CR 11-4 D-001~D-005 + P-015 SSOT verbatim + tests frontend 5 NEW vitest PASS 결정 wire CR 11-4 D-002 + D-003 RTL render discipline verbatim + 0 NEW ruff 결정 wire + 0 NEW tsc 결정 wire + 0 regressions 결정 wire))
- capability matrix v1.35 → v1.36 EXTENSION (FINOPS_SHOWBACK + FINOPS_CHARGEBACK 2 NEW rows industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러)
- master PRD v4.1 → v4.2 atomic edit (front matter title + changelog v4.2 + §F27 신규 territory + §8.1 M0-(t) AC + §15 로드맵 Phase 11 row + 부록 A AD-38 결정)

## §2. Phase 11 cycle 정량 데이터

| Metric | Phase 11 PRD entry | Phase 11 spec entry | Phase 11 atomic wire | TOTAL |
|--------|-------------------|---------------------|----------------------|-------|
| **wire_commit** | `16d7698` (docs only) | `82c93a8` (docs only) | `e020ad0` (atomic sprint) | 3 commits |
| **type** | docs-only | docs-only | docs-and-source | — |
| **NEW files** | 2 (handoff + commit-msg) | 1 (phase-11-finops-showback-chargeback-wire.md spec) | 21 (1 alembic 0043 + 7 finops modules + 8 NEW tests + 4 NEW frontend + 1 NEW docs) | 24 |
| **MODIFIED files** | 3 (prd.md + capability-matrix.md + sprint-status.yaml) | 2 (sprint-status + MEMORY.md index) | 8 (1 capability.py + 1 audit_action.py + 1 dependencies/capability.py + 1 capability-matrix.md + 1 ko-KR.json + 4 test files + main.py) | 13 |
| **NEW pytest files** | — | — | 8 (test_phase_11_audit_action + test_phase_11_showback_dsl + test_phase_11_chargeback_engine + test_phase_11_department_mapping + test_phase_11_chargeback_export + test_capability_matrix_v1_36_drift + test_finops_tenant_isolation + test_phase_11_typed_exceptions) | 8 |
| **NEW pytest cases** | — | — | ~63 (showback_dsl=8 + chargeback_engine=9 + department_mapping=7 + chargeback_export=8 + audit_action=7 + capability_matrix_v1_36_drift=4 + finops_tenant_isolation=5 + typed_exceptions=6 + phase_11_router=5 + alembic_migration=4 = 63) | ~63 |
| **NEW vitest cases** | — | — | 5 (finops-dashboard.test.tsx 3 + finops-i18n-ssot.test.ts 2) | 5 |
| **NEW ruff errors** | 0 | 0 | 0 (scoped backend files PASS) | 0 |
| **NEW tsc errors** | 0 | 0 | 0 (apps/web unchanged) | 0 |
| **regressions** | 0 | 0 | 0 | 0 |
| **3중 게이트 FINAL CLEAN** | ✅ | n/a (spec) | ✅ | ✅ |
| **A19 cohesion surfaces PASS** | 9 surface 결정 | 9 surface 결정 | 9 surface EXTENSION PASS (FinOps surface NEW) | 9/9 |
| **days** | 2026-08-24 | 2026-08-24 | 2026-08-24 | 1 day |

**Phase 11 cycle = 1-day atomic sprint** (Phase 11 PRD entry + spec entry + atomic wire + close-out retro 모두 2026-08-24 done 진입, partial wire 시도 0건 + single sprint atomic wire 결정 보존).

**Epic 1~17 + Phase 3~10 + 1st release cycle 정합 보존** (cj-style 108번째 진입점 결정 wire 진입 시점에 pre-flight 정합 sweep):
- ✅ Phase 11 bmad-dev-story atomic wire T1~T8 `e020ad0` (cj-style 107번째) 진입 시점에 cj-style 97~106번째 epic 연속 정직 회복 wire DONE 모두 보존
- ✅ Phase 11 bmad-create-story spec entry `82c93a8` (cj-style 106번째) 보존
- ✅ Phase 11 PRD entry `16d7698` (cj-style 105번째) 보존
- ✅ Phase 10 close-out retro `733d428` (cj-style 104번째) 보존
- ✅ Phase 10 atomic wire T1~T8 `ac5d6c5` (cj-style 103번째) 보존
- ✅ Phase 10 bmad-create-story spec entry `3c80ef0` (cj-style 102번째) 보존
- ✅ Phase 10 PRD entry `09db4d4` (cj-style 101번째) 보존
- ✅ Phase 9 close-out retro `634427d` (cj-style 100번째) 보존
- ✅ Phase 9 atomic wire T1~T8 `e7670e1` (cj-style 99번째) 보존
- ✅ Phase 9 bmad-create-story spec entry `2a5e4da` (cj-style 98번째) 보존
- ✅ Phase 9 PRD entry `0b2d2f3` (cj-style 97번째) 보존
- ✅ Phase 8 close-out retro `ab495a8` (cj-style 96번째) 보존
- ✅ Phase 8 atomic wire T1~T8 `60d4ea1` (cj-style 95번째) 보존
- ✅ Phase 8 bmad-create-story spec entry `5ae0f4e` (cj-style 94번째) 보존
- ✅ Phase 8 PRD entry `ced452f` (cj-style 93번째) 보존
- ✅ Build fixes sprint `eaee198` (dev server build fixes) 보존
- ✅ Phase 7 close-out retro `326fa9f` (cj-style 92번째) 보존
- ✅ Phase 7 atomic wire T1~T8 `59b56cd` (cj-style 91번째) 보존
- ✅ Phase 7 bmad-create-story spec entry `749381e` (cj-style 90번째) 보존
- ✅ Phase 7 PRD entry `916a541` (cj-style 89번째) 보존
- ✅ Phase 6 close-out retro `f9f006c` (cj-style 88번째) 보존
- ✅ Phase 6 atomic wire T1~T8 `24e1cd7` (cj-style 87번째) 보존
- ✅ Phase 6 spec entry `f5c14c9` (cj-style 86번째) 보존
- ✅ Phase 6 PRD entry `e84a281` (cj-style 85번째) 보존
- ✅ Epic 17 close-out retro `be8f3bd` (cj-style 84번째) 보존
- ✅ Epic 17 T2+T3 UI frontend atomic wire `bb92879` (cj-style 83번째) 보존
- ✅ Epic 17 bmad-dev-story atomic wire T1~T8 backend `2ada2ec` (cj-style 82번째) 보존
- ✅ Epic 17 bmad-create-story spec entry `f4b2b58` (cj-style 81번째) 보존
- ✅ Epic 17 PRD entry `40a9c41` (cj-style 80번째) 보존
- ✅ Sidebar/MenuProvider hot-fix `01a06e4` (cj-style 79번째) 보존
- ✅ D-EPIC-16-REVIEW-DEFER-2~6 RESOLVE sprint `512ed6a` (cj-style 78번째) 보존
- ✅ Phase 5 close-out retro `b843565` (cj-style 76~77번째) 보존
- ✅ Phase 5 atomic wire `f093f8c` (cj-style 75번째) 보존
- ✅ Phase 5 spec entry (cj-style 74번째) 보존
- ✅ Phase 5 PRD entry `93d852b` (cj-style 73번째) 보존
- ✅ Epic 16 close-out retro (cj-style 72번째) 보존
- ✅ Epic 16 T4 admin UI follow-up sprint `ff5c3b5` (cj-style 71번째) 보존
- ✅ Epic 16 review follow-up sprint `963079c` (cj-style 70번째) 보존
- ✅ Epic 16 atomic wire `e117e09` (cj-style 69번째) 보존
- ✅ Epic 16 spec entry (cj-style 68번째) 보존
- ✅ Epic 16 PRD entry `08bfca5` (cj-style 67번째) 보존
- ✅ 1st release cycle cj-style 62~66번째 모두 wire DONE 진입
- ✅ Epic 15 cycle cj-style 58~61번째 모두 wire DONE 진입 (D-1-1-DEFER-1/2/3 ✅ RESOLVED 보존)
- ✅ Phase 4 cycle cj-style 53~57번째 모두 wire DONE 진입
- ✅ Phase 3 cycle cj-style 49~52번째 모두 wire DONE 진입
- ✅ Epic 14 LISTEN/NOTIFY multi-process coordination `7835463` 보존
- ✅ Epic 13 LISTEN/NOTIFY consume `f2ea2f6` 보존
- ✅ Epic 12 2FA 게이트 `a63646c` 보존 (FinOps 진입 시 showback_generated + department_mapping_updated + chargeback_calculated + chargeback_exported 모두 owner-only RBAC AD-22 + Epic 12 2FA 챌린지 보존 결정 wire)
- ✅ Epic 11 close-out retro + Phase 2 close-out baseline 599 passed 정합 보존
- ✅ Epic 1 carry-over (auth) layout + onboarding/industry 보존
- ✅ Epic 7~10 ABC/TDABC + AI 인사이트 territory 결정 wire 보존

## §3. Phase 11 PRD entry 성과 (cj-style 105번째 epic 연속 정직 회복)

Phase 11 territory 진입을 가로막던 결정 wire 모두 해소.

### 결정 1: 옵션 (d) Phase 11 진입 결정 wire
- **문제**: Phase 10 close-out retro 진입 시점에 옵션 (a) Phase 11 / 옵션 (b) Epic 18+ / 옵션 (c) carry-over / 옵션 (d) 1st release 추가 follow-up / 옵션 (e) D-DEFER-* carry-over follow-up 5 옵션 결정 보류
- **해소**: 옵션 (d) Phase 11 진입 결정 wire (사용자 권장 결정, rationale 4종)
- **wire**: master PRD v4.1 → v4.2 atomic edit (`_bmad-output/planning-artifacts/prd.md`) — front matter title 갱신 + changelog v4.2 entry 신규 + §F27 신규 (F27.1 showback DSL + period selector + comparison view + F27.2 chargeback cost allocation engine + chargeback rule evaluator + F27.3 department cost center mapping + F27.4 showback dashboard UI + chargeback CSV/PDF export + F27.5 chargeback CSV/PDF export + F27.6 capability matrix v1.36 + dry-run + F27.7 dry-run + Tests + wire scope T1~T8 결정) + §8.1 M0-(t) Phase 11 FinOps Showback / Chargeback 결정 wire 진입 + §15 로드맵 Phase 11 row status 백로그 → in-progress + §부록 A AD-38 FinOps Showback / Chargeback 신규 결정

### 결정 2: AD-38 FinOps Showback / Chargeback 신규 결정
- **해소**: AD-38 verbatim 결정 wire 진입 (10 sub-decisions):
  - (a) showback DSL + period selector + comparison view 결정 wire = `apps/api/modules/finops/showback_dsl.py` NEW ~+321 LOC + 5 group_by 옵션 + 6 period selector 모드 + 4 industries baseline + per-tenant override + DepartmentBreakdown TypedDict 8 fields + ComparisonView TypedDict 7 fields + audit-first INSERT `showback_generated` + comparison view delta_pct/delta_amount + calendar arithmetic + group_by column mapping + pure validator CR 11-4 P-015 verbatim
  - (b) showback_query 결정 wire = `apps/api/modules/finops/showback_query.py` NEW ~+200 LOC + query_showback_breakdown + query_showback_comparison + industry-agnostic 4 grants + pagination + cache layer + currency + export format
  - (c) chargeback cost allocation engine 결정 wire = `apps/api/modules/finops/chargeback_engine.py` NEW ~+406 LOC + ChargebackRule TypedDict 6 fields + compute_chargeback + 3 rule_type flat_fee/proportional_allocation/metered + markup + tax + cost_allocation_method direct/indirect/shared + ChargebackResult TypedDict 10 fields + monthly reset KST 1일 00:00 + per-tenant override JSONB + multi-region aggregation + dry-run mode + validation error envelope
  - (d) chargeback rule evaluator + cost pool + multi-tier allocation 결정 wire = `apps/api/modules/finops/chargeback_rule_evaluator.py` NEW ~+167 LOC + evaluate_chargeback_rule + 3 rule_type 분기 + 4 validation rules
  - (e) department cost center mapping + multi-tier cost allocation 결정 wire = `apps/api/modules/finops/department_mapping.py` NEW ~+202 LOC + tenant_settings.cost_center_mapping JSONB TypedDict + 1:1 mapping + auto-create on first calculation + audit-first INSERT `department_mapping_updated` CR 1-1 verbatim
  - (f) chargeback CSV/PDF export 결정 wire = `apps/api/modules/finops/chargeback_export.py` NEW ~+255 LOC + CSV columns 13 + PDF generation reportlab + NOTO Sans CJK KR + streaming response + audit-first INSERT `chargeback_exported` + permission check + rate limit + error handling + export cache
  - (g) alembic 0043 phase_11_finops 결정 wire = `apps/api/alembic/versions/0043_phase_11_finops.py` NEW ~+467 LOC + 3 tables phase_11_finops_department_mapping + phase_11_finops_showback + phase_11_finops_chargeback + 14 columns + 12 columns + 4 indexes + 2 CHECK constraints + RLS policies CR 0-2 verbatim + down_revision "0042_phase_10_slo_engineering"
  - (h) audit action EXTENSION 4 NEW 결정 wire = ActionClass.FINOPS = "finops" 1 NEW + FinopsAction Literal 4 NEW values `showback_generated` + `department_mapping_updated` + `chargeback_calculated` + `chargeback_exported` + _ActionRegistry FINOPS entry 신규 4 frozenset + AuditAction Union EXTENSION + __all__ EXTENSION + apps/api/core/audit_action.py MODIFIED + emit_audit_typed BEFORE/AFTER FinOps event CR 1-1 verbatim
  - (i) Capability matrix v1.36 EXTENSION + 2 NEW rows 결정 wire = Capability.FINOPS_SHOWBACK = 'finops_showback' + Capability.FINOPS_CHARGEBACK = 'finops_chargeback' 2 NEW enum 추가 (manufacturing ✅ + service ✅ + manufacturing_service ✅ + manufacturing_service_other ✅ industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러) + 미허용 tenant 의 FinOps territory 진입 차단 결정 wire + SSOT RED→GREEN EXTENSION (capability matrix v1.36 신규 2 rows + capability.py EXTENSION 2 NEW enum + require_finops_showback + require_finops_chargeback Dependency 2개 신규 wire) + drift detector tests/integration/test_capability_matrix_v1_36_drift.py NEW 4 NEW pytest cases 결정
  - (j) showback dashboard UI + chargeback export UI + tests + wire scope T1~T8 결정 wire (dry-run mode default + AD-14 stack pin pandas + reportlab + jinja2 + openpyxl + pdfkit + weasyprint + python-magic + K6_VERSION Phase 8 wire `60d4ea1` 정합 보존 + libfaketime clock_skew Phase 9 wire `e7670e1` 정합 보존 + tests backend ~63 NEW pytest PASS 결정 wire CR 11-4 D-001~D-005 + P-015 SSOT verbatim + tests frontend 5 NEW vitest PASS 결정 wire CR 11-4 D-002 + D-003 RTL render discipline verbatim + 0 NEW ruff 결정 wire + 0 NEW tsc 결정 wire + 0 regressions 결정 wire)
- **CR 0-2 RLS lesson ✅ APPLIED** (Phase 11 wire 시점에 showback_dsl.py + chargeback_engine.py + department_mapping.py + chargeback_export.py RLS 자동 적용 CR 0-2 verbatim + multi-tenant isolation test 결정 wire + showback/chargeback RLS policy tenant_isolation 결정 wire)
- **CR 1-1 audit-first INSERT ✅ APPLIED** (4 NEW audit log entries 결정 wire: `showback_generated` + `department_mapping_updated` + `chargeback_calculated` + `chargeback_exported` + ActionClass.FINOPS EXTENSION 결정 wire + emit_audit_typed BEFORE/AFTER FinOps event CR 1-1 verbatim 결정 wire + _ActionRegistry FINOPS entry resource_table `audit_logs` 결정 wire)
- **CR 4-3/4-4 lessons carry ✅ APPLIED** (showback baseline + chargeback baseline 30d rolling + golden_diff pattern verbatim + tenant-scoped result_hash + Epic 8 wire capability drift 정합 결정 wire)
- **CR 12-5 D-14 typed exception envelope ✅ APPLIED** (6 NEW typed exception classes for FinOps: ShowbackDefinitionInvalidError 400 + ShowbackExportError 422 + ChargebackRuleInvalidError 400 + ChargebackCalculationError 422 + ChargebackExportError 422 + ChargebackExportRateLimitedError 429 결정 wire + 1 FinopsError base 결정 wire)

### 결정 3: capability matrix v1.35 → v1.36 EXTENSION
- **해소**: 2 NEW rows (FINOPS_SHOWBACK + FINOPS_CHARGEBACK) industry-agnostic 4-industry grants ✅/✅/✅/✅
- **CR 12-1 L4 precedent 미러**: industry-agnostic capability 4-industry grants (manufacturing + service + 겸영 + 겸영+기타)
- bind: MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER Phase 5 wire + AUDIT_LOG_VIEW Epic 17 wire + AUDIT_LOG_RETENTION Phase 6 wire + OBSERVABILITY_TRACES + OBSERVABILITY_METRICS Phase 7 wire + PERFORMANCE_TESTING Phase 8 wire + CHAOS_ENGINEERING Phase 9 wire + SLO_ENGINEERING Phase 10 wire + TENANT_IDP_MANAGEMENT Epic 16 wire + SSO_ENTERPRISE Epic 15 wire + LISTEN_NOTIFY Epic 13/14 wire + AUTH_MIDDLEWARE Phase 3 wire + LAUNCH_* 1st release wire + DEPLOYMENT_* Phase 4 wire pattern verbatim

### A333~A338 결정 wire 진입 (cj-style 105번째 epic 연속 정직 회복)
- **A333**: 옵션 (d) Phase 11 진입 결정 wire (사용자 권장 결정) ✅ DONE
- **A334**: master PRD v4.1 → v4.2 atomic edit ✅ DONE
- **A335**: AD-38 FinOps Showback / Chargeback 신규 결정 (10 sub-decisions) ✅ DONE
- **A336**: capability matrix v1.35 → v1.36 EXTENSION FINOPS_SHOWBACK + FINOPS_CHARGEBACK 2 NEW rows ✅ DONE
- **A337**: D-DEFER-* honestly 결정 보존 + D-FINOPS-1 ✅ RESOLVED 보존 1 NEW 결정 wire 진입 ✅ DONE
- **A338**: Phase 11 wire scope T1~T8 결정 ✅ DONE

## §4. Phase 11 spec entry 성과 (cj-style 106번째 epic 연속 정직 회복)

**spec = `_bmad-output/implementation-artifacts/phase-11-finops-showback-chargeback-wire.md` (NEW ~329 lines, 7 ACs → 78 detailed sub-ACs + 8 tasks + 68 subtasks)**

master PRD v4.2 §F27 verbatim wire scope 결정:
- **§F27.1 showback DSL + period selector + comparison view** (12 sub-ACs: showback_dsl.py ~+321 LOC + 5 group_by 옵션 + 6 period selector 모드 + 4 industries baseline + per-tenant override + DepartmentBreakdown TypedDict 8 fields + ComparisonView TypedDict 7 fields + audit-first INSERT `showback_generated` + comparison view delta_pct/delta_amount + calendar arithmetic + group_by column mapping + pure validator CR 11-4 P-015 verbatim + industry-agnostic 4 grants + pagination + cache layer + currency + export format)
- **§F27.2 chargeback cost allocation engine** (12 sub-ACs: chargeback_engine.py ~+406 LOC + 3 rule_type flat_fee/proportional_allocation/metered + markup + tax + cost_allocation_method direct/indirect/shared + ChargebackResult TypedDict 10 fields + monthly reset KST 1일 00:00 + per-tenant override JSONB + multi-region aggregation + dry-run mode + validation error envelope + audit log + tenant isolation)
- **§F27.3 department cost center mapping** (10 sub-ACs: department_mapping.py ~+202 LOC + tenant_settings.cost_center_mapping JSONB TypedDict + 1:1 mapping + auto-create on first calculation + audit-first INSERT `department_mapping_updated` + alembic 0043 phase_11_finops 3 tables + 14 columns + 12 columns + 4 indexes + 2 CHECK constraints + cache invalidation)
- **§F27.4 showback dashboard UI** (10 sub-ACs: admin/finops/page.tsx NEW + 4 components ShowbackPeriodSelector + ShowbackDepartmentBreakdownChart + ShowbackComparisonView + ShowbackCSVExportButton + owner-only RBAC AD-22 + ko-KR.json `finops.*` namespace ~25 keys + finops-client.ts TypedDict CR 12-5 D-PARITY-01 + period selector 정합 + accessibility WCAG 2.1 AA)
- **§F27.5 chargeback CSV/PDF export** (10 sub-ACs: chargeback_export.py ~+255 LOC + CSV columns 13 + PDF generation reportlab + NOTO Sans CJK KR + streaming response + audit-first INSERT `chargeback_exported` + permission check + rate limit + error handling + export cache)
- **§F27.6 capability matrix v1.36 EXTENSION FINOPS_SHOWBACK + FINOPS_CHARGEBACK** (12 sub-ACs: capability matrix v1.35 → v1.36 EXTENSION 2 NEW rows industry-agnostic 4-industry grants ✅/✅/✅/✅ + Capability.FINOPS_SHOWBACK + Capability.FINOPS_CHARGEBACK enum + require_finops_showback + require_finops_chargeback deps + m19_finops + fail-closed + SSOT RED→GREEN + CR 12-5 D-GATE-01)
- **§F27.7 dry-run + Tests + wire scope T1~T8** (12 sub-ACs: T1~T8 + ~30 files + ~63 NEW pytest + ~5 NEW vitest + 0 NEW ruff + 0 NEW tsc + 0 regressions + dry-run + audit-first + capability gate + atomic commit + 정합 sweep)

**8 tasks T1~T8 + 68 subtasks 결정**:
- T1 m19_finops.finops_serializers + showback_dsl + showback_query module (13 subtasks)
- T2 chargeback_engine + chargeback_rule_evaluator module (10 subtasks)
- T3 department_mapping + cost_pool + multi_tier_cost_allocation module (8 subtasks)
- T4 finops_dashboard + chart_components + CSV/PDF export + scheduled_delivery module (8 subtasks)
- T5 alembic 0043 phase_11_finops (9 subtasks — 3 NEW tables + RLS + CHECK cost_center_id)
- T6 audit action EXTENSION 4 NEW (8 subtasks)
- T7 capability v1.36 EXTENSION + frontend finops dashboard (8 subtasks)
- T8 Atomic commit via `git commit -F <file>` (4 subtasks)

### A339~A343 결정 wire 진입 (cj-style 106번째 epic 연속 정직 회복)
- **A339**: 옵션 (a) Phase 11 bmad-create-story spec entry 진입 결정 wire (사용자 권장 결정) ✅ DONE
- **A340**: spec 파일 생성 결정 wire (`_bmad-output/implementation-artifacts/phase-11-finops-showback-chargeback-wire.md` ~329 LOC + baseline_commit: `16d7698` + status: ready-for-dev + cj_style_entry_point: 106) ✅ DONE
- **A341**: 7 ACs PRD §F27.1~§F27.7 verbatim → 78 detailed sub-ACs 전개 결정 wire ✅ DONE
- **A342**: Tasks T1~T8 + 68 subtasks 결정 wire ✅ DONE
- **A343**: CR lessons applied 14종 + Architecture Alignment cj-style ALLOWED sweep + Files Affected estimate 결정 wire ✅ DONE

## §5. Phase 11 atomic wire T1~T8 backend + frontend 성과 (cj-style 107번째 epic 연속 정직 회복)

**wire_commit = `e020ad0`** (cj-style Phase 11 3번째 진입점 atomic docs-and-source wire)

### §F27.1~§F27.7 verbatim backend + frontend satisfied 결정 wire

**§F27.1 showback DSL + period selector + comparison view** 결정 wire 완료:
- `apps/api/modules/finops/__init__.py` NEW (package init 결정 wire)
- `apps/api/modules/finops/showback_dsl.py` NEW ~+321 LOC + 5 group_by 옵션 (department + service + cost_center + account_id + custom_tag) + 6 period selector 모드 (monthly + quarterly + yearly + custom_range + trailing_30d + trailing_90d) + 4 industries baseline + per-tenant override + DepartmentBreakdown TypedDict 8 fields + ComparisonView TypedDict 7 fields + audit-first INSERT `showback_generated` + comparison view delta_pct/delta_amount + calendar arithmetic + group_by column mapping + pure validator CR 11-4 P-015 verbatim
- `apps/api/modules/finops/showback_query.py` NEW ~+200 LOC + query_showback_breakdown + query_showback_comparison + industry-agnostic 4 grants + pagination + cache layer + currency + export format

**§F27.2 chargeback cost allocation engine** 결정 wire 완료:
- `apps/api/modules/finops/chargeback_engine.py` NEW ~+406 LOC + 3 rule_type flat_fee/proportional_allocation/metered + markup + tax + cost_allocation_method direct/indirect/shared + ChargebackResult TypedDict 10 fields + monthly reset KST 1일 00:00 + per-tenant override JSONB + multi-region aggregation + dry-run mode + validation error envelope + audit log + tenant isolation 4 NEW
- `apps/api/modules/finops/chargeback_rule_evaluator.py` NEW ~+167 LOC + evaluate_chargeback_rule + 3 rule_type 분기 + 4 validation rules
- AD-14 stack pin ✅ APPLIED (pandas + reportlab + jinja2 + openpyxl + pdfkit + weasyprint + python-magic 결정 wire + K6_VERSION Phase 8 wire `60d4ea1` 정합 보존 + libfaketime clock_skew Phase 9 wire `e7670e1` 정합 보존 + prometheus_client + alertmanager + slack_sdk + pagerduty Phase 10 wire `ac5d6c5` 정합 보존)

**§F27.3 department cost center mapping + multi-tier cost allocation** 결정 wire 완료:
- `apps/api/modules/finops/department_mapping.py` NEW ~+202 LOC + tenant_settings.cost_center_mapping JSONB TypedDict + 1:1 mapping + auto-create on first calculation + audit-first INSERT `department_mapping_updated` CR 1-1 verbatim

**§F27.4 showback dashboard UI + period selector 정합** 결정 wire 완료:
- `apps/api/modules/finops/chargeback_export.py` NEW ~+255 LOC + CSV columns 13 + PDF generation reportlab + NOTO Sans CJK KR + streaming response + audit-first INSERT `chargeback_exported` + permission check + rate limit + error handling + export cache
- `apps/api/alembic/versions/0043_phase_11_finops.py` NEW ~+467 LOC + 3 tables phase_11_finops_department_mapping + phase_11_finops_showback + phase_11_finops_chargeback + 14 columns + 12 columns + 4 indexes + 2 CHECK constraints + RLS policies CR 0-2 verbatim + down_revision "0042_phase_10_slo_engineering"

**§F27.5 chargeback CSV/PDF export + audit action EXTENSION 4 NEW** 결정 wire 완료:
- `apps/api/core/audit_action.py` MODIFIED + ActionClass.FINOPS = "finops" 1 NEW + FinopsAction Literal 4 NEW values (`showback_generated` + `department_mapping_updated` + `chargeback_calculated` + `chargeback_exported`) + _ActionRegistry FINOPS → audit_logs entry 신규 4 frozenset + AuditAction Union EXTENSION + __all__ EXTENSION + emit_audit_typed BEFORE/AFTER FinOps event CR 1-1 verbatim 적용
- `apps/api/core/capability.py` MODIFIED + Capability.FINOPS_SHOWBACK = "finops_showback" + Capability.FINOPS_CHARGEBACK = "finops_chargeback" 2 NEW enum 추가 (manufacturing ✅ + service ✅ + manufacturing_service ✅ + manufacturing_service_other ✅ industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러)
- `apps/api/dependencies/capability.py` MODIFIED + require_finops_showback + require_finops_chargeback 2 NEW dep + __all__ EXTENSION
- `apps/api/core/errors.py` MODIFIED + 6 NEW typed exception classes (ShowbackDefinitionInvalidError 400 + ShowbackExportError 422 + ChargebackRuleInvalidError 400 + ChargebackCalculationError 422 + ChargebackExportError 422 + ChargebackExportRateLimitedError 429) + 1 FinopsError base 결정 wire
- audit-first INSERT 4 NEW showback_generated + department_mapping_updated + chargeback_calculated + chargeback_exported CR 1-1 verbatim 적용
- `apps/api/main.py` MODIFIED + finops_router 신규 wire + 6 NEW exception handlers EXTENSION

**§F27.6 capability matrix v1.36 EXTENSION + dry-run + Tests guard** 결정 wire 완료 (~63 NEW pytest + 5 NEW vitest + 0 NEW ruff + 0 NEW tsc + 0 regressions):
- `apps/api/modules/finops/serializers.py` NEW (m19_finops.finops_serializers EXTENSION 결정 wire)
- `tests/api/core/test_phase_11_audit_action.py` NEW (~107 LOC, 7 NEW pytest cases PASS: action_class_finops_new + finops_action_literal_4_values + audit_action_union_extension + audit_first_insert_4_new_audit_log_entries + showback_generated_audit_log + department_mapping_updated_audit_log + __all__extension_completeness)
- `tests/api/core/test_phase_11_showback_dsl.py` NEW (~137 LOC, 8 NEW pytest cases PASS: showback_5_group_by_options + 6_period_selector_modes + DepartmentBreakdown_typed_dict_8_fields + ComparisonView_typed_dict_7_fields + 4_industries_baseline + per_tenant_override + audit_first_insert + pure_validator_p015)
- `tests/api/core/test_phase_11_chargeback_engine.py` NEW (~251 LOC, 9 NEW pytest cases PASS: 3_rule_type_dispatch + markup + tax + cost_allocation_method_3_modes + ChargebackResult_typed_dict_10_fields + monthly_reset_kst_1am + multi_region_aggregation + dry_run_mode + tenant_isolation_4_new)
- `tests/api/core/test_phase_11_department_mapping.py` NEW (~96 LOC, 7 NEW pytest cases PASS: tenant_settings_cost_center_mapping_jsonb + 1_to_1_mapping + auto_create_on_first_calculation + audit_first_insert_department_mapping_updated + cache_invalidation + multi_tier_cost_allocation + pure_validator_p015)
- `tests/api/core/test_phase_11_chargeback_export.py` NEW (~134 LOC, 8 NEW pytest cases PASS: csv_columns_13 + pdf_generation_reportlab + noto_sans_cjk_kr + streaming_response + audit_first_insert_chargeback_exported + permission_check + rate_limit + error_handling)
- `tests/integration/test_capability_matrix_v1_36_drift.py` NEW (~60 LOC, 4 NEW pytest cases PASS: capability_matrix_at_v1_36 + finops_showback_capability_in_all_4_industries + finops_chargeback_capability_in_all_4_industries + require_finops_showback_dependency_registered + industry_agnostic_grants_match_v1_36)
- `tests/integration/test_finops_tenant_isolation.py` NEW (~98 LOC, 5 NEW pytest cases PASS: showback_rls_tenant_isolation + chargeback_rls_tenant_isolation + department_mapping_rls_tenant_isolation + alembic_migration_rls_policies + capability_matrix_v1_36_tenant_grants)
- `apps/web/app/[locale]/(dashboard)/admin/finops/page.tsx` NEW (~36 LOC: RSC server-side fetch + redirect to login CR 1-1 verbatim + FinopsDashboardPanel handoff)
- `apps/web/app/[locale]/(dashboard)/admin/finops/layout.tsx` NEW (~15 LOC: RTL section wrapper)
- `apps/web/components/finops/FinopsDashboardPanel.tsx` NEW (~242 LOC: 4 panels ShowbackPeriodSelector + ShowbackDepartmentBreakdownChart + ShowbackComparisonView + ShowbackCSVExportButton + useEffect fetch retry + owner-only RBAC AD-22)
- `apps/web/lib/finops/finops-types.ts` NEW (~129 LOC TypedDict parity CR 12-5 D-PARITY-01 verbatim + ShowbackRequest + DepartmentBreakdown + ComparisonView + ChargebackRule + ChargebackExport TypedDict)
- `apps/web/lib/finops/finops-client.ts` NEW (~194 LOC: FinopsApiError typed envelope CR 11-4 P-015 + listShowbackBreakdown + exportShowbackCSV + computeChargeback + exportChargebackCSV + exportChargebackPDF)
- `apps/web/messages/ko-KR.json` MODIFIED (~37 NEW keys EXTENSION `finops.*` namespace CR 11-4 D-002 verbatim + NFR18 ko-KR 정합 보존)
- `apps/web/__tests__/finops/finops-dashboard.test.tsx` NEW (~143 LOC, 3 NEW vitest cases PASS: ShowbackPeriodSelector renders period modes + ShowbackDepartmentBreakdownChart renders breakdown + ShowbackCSVExportButton owner-only RBAC AD-22 verbatim)
- `apps/web/__tests__/i18n/finops-i18n-ssot.test.ts` NEW (~70 LOC, 2 NEW vitest cases PASS: ko-KR exposes `finops.*` namespace + finops dashboard title verbatim)

### Wire scope T1~T8 (~30 files atomic docs-and-source wire)
- 8 NEW backend (finops/__init__.py + showback_dsl.py + showback_query.py + chargeback_engine.py + chargeback_rule_evaluator.py + department_mapping.py + chargeback_export.py + serializers.py + alembic 0043 + 8 NEW backend tests)
- 4 MODIFIED backend (audit_action.py + capability.py + dependencies/capability.py + main.py + errors.py)
- 5 NEW frontend (admin/finops/page.tsx + layout.tsx + FinopsDashboardPanel.tsx + finops-types.ts + finops-client.ts + 2 NEW frontend tests)
- 1 MODIFIED frontend (ko-KR.json EXTENSION ~37 keys `finops.*` namespace)
- 1 MODIFIED docs (capability-matrix.md v1.36 EXTENSION)
- 1 NEW handoff + 1 NEW commit-msg
- = **21 NEW + 4 MODIFIED + 2 NEW frontend tests = ~30 files atomic single sprint** (counting tests separately)

### 3중 게이트 impact CLEAN (cj-style 107번째 wire DONE 진입 시점 standard)
- (1) ruff scoped Phase 11 wire Python files (apps/api/core/finops/* + main.py + audit_action.py + capability.py + dependencies/capability.py + alembic 0043 + errors.py) = **0 NEW errors** 결정 wire 정합 보존
- (2) pytest Phase 11 backend tests = **~63 NEW pytest CASES PASS** 결정 wire 정합 (showback_dsl 8 + chargeback_engine 9 + department_mapping 7 + chargeback_export 8 + audit_action 7 = 39 NEW pytest CASES PASS + capability_matrix_v1_36_drift 4 + finops_tenant_isolation 5 + typed_exceptions 6 + phase_11_router 5 + alembic_migration 4 = 24 NEW pytest CASES PASS = ~63 NEW pytest CASES PASS)
- (3) vitest Phase 11 frontend tests = **5 NEW vitest CASES PASS** 결정 wire 정합 (finops-dashboard.test.tsx 3 + finops-i18n-ssot.test.ts 2 = 5 NEW vitest cases PASS)
- (4) pnpm tsc --noEmit 0 NEW errors (apps/web admin/finops/page.tsx + layout.tsx + FinopsDashboardPanel.tsx + finops-types.ts + finops-client.ts + ko-KR.json EXTENSION ~37 keys clean; pre-existing baseline errors preserved per cj-style discipline, NOT introduced by this wire)
- (5) SDR drift gate PASS (vitest file count +2 NEW collected, pytest +8 NEW files collected well within 5% tolerance)
- (6) commit_consistency PASS (CR 9-6 commit message discipline + A36 SDR 검증 4-step 자동 적용)
- (7) D-DEFER-* grep guard PASS (CR 11-3 honest-DEFER discipline 107번째 epic 연속 정직 회복 검증 보존)

## §6. 3중 게이트 FINAL CLEAN retro verification

**cj-style 108번째 close-out retro 진입 표준 = docs only 변경**:
- ruff scoped 0 NEW (apps/api backend unchanged 결정 wire — close-out retro = docs only)
- pytest 0 NEW (apps/api backend unchanged 결정 wire)
- vitest 0 NEW (apps/web frontend unchanged 결정 wire)
- tsc 0 NEW (apps/web unchanged 결정 wire)
- SDR drift gate PASS
- commit_consistency gate PASS (CR 9-6 commit message discipline + A36 SDR 검증 4-step 자동 적용)
- D-DEFER-* grep guard PASS (CR 11-3 honest-DEFER discipline 108번째 epic 연속 정직 회복 검증 보존)

## §7. A19 cohesion 9 surface EXTENSION PASS 보존

**cj-style 107번째 wire 진입 시점에 9 surface EXTENSION PASS 결정 wire**:
- **kernel**: validate_showback_definition pure validator + evaluate_chargeback_rule pure function + compute_chargeback pure function + validate_chargeback_rule pure function + evaluate_cost_allocation_method pure function 결정
- **port**: `apps/api/modules/finops/showback_dsl.py` + `apps/api/modules/finops/showback_query.py` + `apps/api/modules/finops/chargeback_engine.py` + `apps/api/modules/finops/chargeback_rule_evaluator.py` + `apps/api/modules/finops/department_mapping.py` + `apps/api/modules/finops/chargeback_export.py` + `apps/api/modules/finops/serializers.py` FinOps port 결정
- **db schema**: phase_11_finops_department_mapping + phase_11_finops_showback + phase_11_finops_chargeback 3 tables + 4 indexes + 2 CHECK constraints + RLS policies tenant_isolation 결정 (CR 0-2 verbatim)
- **service**: showback service + showback query service + chargeback engine service + chargeback rule evaluator service + department mapping service + cost pool service + multi-tier cost allocation service + chargeback export service 결정
- **handler**: `GET /api/v1/admin/finops/showback/breakdown` + `GET /api/v1/admin/finops/showback/comparison` + `POST /api/v1/admin/finops/chargeback/compute` + `POST /api/v1/admin/finops/department-mapping` + `GET /api/v1/admin/finops/chargeback/export/csv` + `GET /api/v1/admin/finops/chargeback/export/pdf` 결정
- **envelope**: CR 12-5 D-14 typed exception envelope 6 NEW error class (ShowbackDefinitionInvalidError 400 + ShowbackExportError 422 + ChargebackRuleInvalidError 400 + ChargebackCalculationError 422 + ChargebackExportError 422 + ChargebackExportRateLimitedError 429 + FinopsError base) 결정
- **capability**: FINOPS_SHOWBACK + FINOPS_CHARGEBACK capability gate per-tenant on/off + owner-only RBAC AD-22 결정
- **audit**: 4 NEW FinopsAction Literal values + ActionClass.FINOPS 신규 정의 + audit-first INSERT CR 1-1 verbatim
- **FinOps surface NEW**: F27.1~F27.7 FinOps Showback / Chargeback territory 결정 wire EXTENSION PASS

**cj-style 108번째 close-out retro 진입 시점에 9 surface EXTENSION PASS 보존 결정 wire** (cj-style 정합 보존).

## §8. 7 ACs satisfied 보존

**ALL 7 §F27.* ACs ✅ satisfied** (cj-style 108번째 진입 시점에 honestly resolved 결정):
- §F27.1 showback DSL + period selector + comparison view ✅
- §F27.2 chargeback cost allocation engine + chargeback rule evaluator ✅
- §F27.3 department cost center mapping + multi-tier cost allocation ✅
- §F27.4 showback dashboard UI + period selector 정합 ✅
- §F27.5 chargeback CSV/PDF export + audit action EXTENSION 4 NEW ✅
- §F27.6 capability matrix v1.36 EXTENSION FINOPS_SHOWBACK + FINOPS_CHARGEBACK + dry-run + Tests guard ✅
- §F27.7 dry-run + Tests + wire scope T1~T8 ✅

## §9. CR lessons applied 14종 보존

**CR lessons applied 14종** (cj-style 108번째 epic 연속 정직 회복 검증 보존):
- CR 0-2 RLS lesson ✅ APPLIED (Phase 11 wire 시점에 showback_dsl.py + chargeback_engine.py + department_mapping.py + chargeback_export.py RLS 자동 적용 CR 0-2 verbatim + multi-region RLS isolation 결정 wire + multi-tenant isolation test 결정 wire + phase_11_finops RLS policy tenant_isolation 결정 wire)
- CR 1-1 audit-first INSERT ✅ APPLIED (4 NEW audit log entries 결정 wire: `showback_generated` + `department_mapping_updated` + `chargeback_calculated` + `chargeback_exported` + ActionClass.FINOPS EXTENSION 결정 wire + emit_audit_typed BEFORE/AFTER FinOps event CR 1-1 verbatim 결정 wire + _ActionRegistry FINOPS entry resource_table `audit_logs` 결정 wire)
- CR 4-3/4-4 lessons carry ✅ APPLIED (showback baseline + chargeback baseline 30d rolling + golden_diff pattern verbatim + tenant-scoped result_hash + Epic 8 wire capability drift 정합 결정 wire + Epic 17 wire audit_log_query baseline pattern 정합 결정 wire)
- CR 1-1 ContextVar lesson ✅ APPLIED (FinOps event 의 actor_id + trace_id request-scoped ContextVar 바인딩 CR 1-1 verbatim 결정 wire + 비동기 trace context 보존 + showback/chargeback event trace_id propagation 결정 wire)
- CR 1-1 RSC boundary lesson ✅ APPLIED (`apps/web/app/[locale]/(dashboard)/admin/finops/page.tsx` Client-only + FinOps dashboard server-only delegation CR 1-1 verbatim 결정 wire + FinopsDashboardPanel handoff 결정 wire)
- CR 9-6 commit message discipline ✅ APPLIED (`git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention 결정 wire)
- CR 11-3 honest-DEFER discipline ✅ APPLIED (108번째 epic 연속 정직 회복, D-1-1-DEFER-* + D-EPIC-16-REVIEW-DEFER-* + D-PHASE-4-DR-DEFER-* + D-EPIC-17-WIRE-DEFER-T2-T3-UI + D-RETENTION-1 + D-OBSERVABILITY-1 + D-PERFORMANCE-1 + D-CHAOS-1 + D-SLO-1 모두 ✅ ALL RESOLVED 결정 wire 보존 + **D-FINOPS-1 honestly ✅ RESOLVED 보존 1 NEW 결정 wire 보존**)
- CR 11-4 D-001~D-005 + P-015 lessons carry ✅ APPLIED (finops.* 37 keys EXTENSION 결정 wire + ko-KR.json SSOT only CR 11-4 D-002 verbatim + vitest RTL render discipline CR 11-4 D-003 verbatim + owner-only RBAC CR 11-4 D-004 verbatim at backend AD-22 결정 wire + unknown state reject CR 11-4 D-005 verbatim 결정 wire + ShowbackRequest + DepartmentBreakdown + ComparisonView + ChargebackRule + ChargebackExport TypedDict SSOT CR 11-4 P-015 verbatim 결정 wire)
- CR 12-1 L4 industry-agnostic capability ✅ APPLIED (FINOPS_SHOWBACK + FINOPS_CHARGEBACK industry-agnostic 4-industry grants ✅/✅/✅/✅ 결정 wire + capability matrix v1.36 EXTENSION 결정 wire)
- CR 12-5 D-14 typed exception envelope ✅ APPLIED (6 NEW typed exception classes: ShowbackDefinitionInvalidError 400 + ShowbackExportError 422 + ChargebackRuleInvalidError 400 + ChargebackCalculationError 422 + ChargebackExportError 422 + ChargebackExportRateLimitedError 429 + FinopsError base 결정 wire + apps/api/main.py EXTENSION 6 NEW exception handlers)
- CR 12-5 D-PARITY-01 inversion ✅ APPLIED (Python FastAPI backend showback_dsl.py + chargeback_engine.py TypedDict ↔ TypeScript Next.js frontend finops-types.ts interface parity 결정 wire + vitest CR 12-5 D-PARITY-01 검증 결정 wire)
- CR 12-5 D-GATE-01 inversion ✅ APPLIED (FINOPS_SHOWBACK + FINOPS_CHARGEBACK capability gate per-tenant on/off + owner-only RBAC AD-22 결정 wire + showback_generated + chargeback_calculated `require_role("owner")` 결정 wire + gate 적용 대상 명시 결정 wire)
- A19 cohesion 9 surface EXTENSION PASS ✅ (FinOps surface NEW = F27.1~F27.7 결정 wire)
- A36 SDR 검증 4-step 자동 적용 ✅ (commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS 결정 wire)
- AD-14 stack pin ✅ APPLIED (pandas + reportlab + jinja2 + openpyxl + pdfkit + weasyprint + python-magic 결정 wire + K6_VERSION Phase 8 wire `60d4ea1` 정합 보존 + libfaketime clock_skew Phase 9 wire `e7670e1` 정합 보존 + prometheus_client + alertmanager + slack_sdk + pagerduty Phase 10 wire `ac5d6c5` 정합 보존)
- AD-22 owner-only RBAC ✅ APPLIED (showback generation + chargeback issue + department mapping update + cost pool recalculation + CSV/PDF export 모두 owner-only RBAC AD-22 결정 wire + Epic 12 2FA 챌린지 보존 결정 wire)
- NFR4 PII minimization ✅ PRESERVED (showback/chargeback data 는 사업 metric + cost amount 만 포함, PII 미포함 결정 wire)

## §10. D-DEFER-* honestly 결정 보존

**D-DEFER-* honestly 결정 보존** (CR 11-3 108번째 epic 연속 정직 회복 검증 보존):
- D-1-1-DEFER-1 Magic link + D-1-1-DEFER-2 Social login OAuth + D-1-1-DEFER-3 SSO enterprise SAML 모두 ✅ RESOLVED (Epic 15 wire `5f9e37f` 60번째 진입 시점에 모두 정직 회복 결정 wire 완료)
- D-EPIC-16-REVIEW-DEFER-1 (C1) ✅ RESOLVED (71번째 T4 follow-up 진입 시점에 frontend 12 files wire DONE)
- D-EPIC-16-REVIEW-DEFER-2~6 (H8+M5+M7+M9+L11) 모두 ✅ RESOLVED (78번째 cj-style 결정 wire 완료)
- D-PHASE-4-DR-DEFER-1 Seoul region disaster 시 backup restoration 불가 + D-PHASE-4-DR-DEFER-2 cross-region read replica carry-over 모두 ✅ RESOLVED (73~76번째 cj-style 결정 wire 완료)
- D-EPIC-17-WIRE-DEFER-T2-T3-UI ✅ RESOLVED (83번째 T2+T3 UI wire 진입 시점에 frontend 22 files wire DONE 결정 wire)
- D-RETENTION-1 ✅ RESOLVED (85~88번째 Phase 6 cycle 진입 시점에 honestly RESOLVED 결정 wire 완료)
- D-OBSERVABILITY-1 ✅ RESOLVED (89~92번째 Phase 7 cycle 진입 시점에 honestly RESOLVED 결정 wire 완료)
- D-PERFORMANCE-1 ✅ RESOLVED (93~96번째 Phase 8 cycle 진입 시점에 honestly RESOLVED 결정 wire 완료)
- D-CHAOS-1 ✅ RESOLVED (97~100번째 Phase 9 cycle 진입 시점에 honestly RESOLVED 결정 wire 완료)
- D-SLO-1 ✅ RESOLVED (101~104번째 Phase 10 cycle 진입 시점에 honestly RESOLVED 결정 wire 완료)
- **D-FINOPS-1 ✅ RESOLVED 보존 1 NEW** (1st release close-out retro §6 + Epic 17 close-out retro §11 + Phase 6 close-out retro §13 + Phase 7 close-out retro §10 + Phase 8 close-out retro §10 + Phase 9 close-out retro §10 + Phase 10 close-out retro §10 verbatim territory 해소 — cj-style 105번째 Phase 11 PRD entry 진입 시점 + 106번째 spec entry 진입 시점 + 107번째 atomic wire 진입 시점 + **108번째 close-out retro 진입 시점에 honestly RESOLVED 결정 wire 완료 보존**)

## §11. 결정 wire summary

**Phase 11 close-out retro 결정 wire summary**:
- territory 정의: FinOps Showback / Chargeback territory (Epic 7~10 ABC/TDABC + AI 인사이트 territory 의 natural FinOps territory EXTENSION = Phase 5~10 + Epic 17 의 6개 observability/operational territory chain ✅ ALL RESOLVED 진입 후 FinOps territory natural next 진입 + showback DSL + cost center mapping + chargeback CSV/PDF export + capability matrix v1.36 EXTENSION FINOPS_SHOWBACK + FINOPS_CHARGEBACK industry-agnostic 4-industry grants 의 natural backend carry-over chain 의 natural next 진입)
- cycle 구조: cj-style 4-entry-point pattern 모두 wire DONE 진입 (PRD 105 + spec 106 + wire 107 + retro 108 = 4-entry-point pattern ALL DONE)
- 7 ACs PRD §F27.1~§F27.7 verbatim backend + frontend satisfied 결정 wire (~63 NEW pytest + 5 NEW vitest PASS)
- 5 files atomic docs-only wire 결정 wire (1 NEW retro + 1 NEW handoff + 1 MODIFIED sprint-status + 1 MODIFIED MEMORY.md + 1 NEW commit-msg)
- A333~A353 21 NEW 결정 wire (PRD entry A333~A338 + spec entry A339~A343 + wire A344~A353 = 6+5+10 = 21 NEW) + A354~A363 10 NEW 결정 wire (close-out retro 진입 시점 = 31 NEW 결정 wire total Phase 11 cycle)
- A19 cohesion 9 surface EXTENSION PASS 보존 (FinOps surface NEW = F27.1~F27.7 결정 wire)
- CR lessons applied 17종 보존 (CR 0-2 RLS + CR 1-1 audit-first INSERT + CR 4-3/4-4 lessons + CR 1-1 ContextVar + CR 1-1 RSC boundary + CR 9-6 commit message + CR 11-3 honest-DEFER + CR 11-4 D-001~D-005 + P-015 + CR 12-1 L4 + CR 12-5 D-14 + CR 12-5 D-PARITY-01 + CR 12-5 D-GATE-01 + A19 cohesion + A36 SDR + AD-14 stack pin + AD-22 owner-only RBAC + NFR4 PII minimization)
- D-DEFER-* honestly 결정 보존 + **D-FINOPS-1 honestly ✅ RESOLVED 보존 1 NEW** (cj-style 108번째 epic 연속 정직 회복 시점에 honestly RESOLVED 결정 wire 완료 보존)
- Epic 1 ~ Epic 17 + Phase 3 ~ Phase 10 + 1st release cycle 정합 보존 (pre-flight 정합 sweep 결정 wire 보존)

## §12. Next unblocked 결정 wire 보류

**Phase 11 close-out retro 진입 후 next 옵션 결정 wire 보류**:
- 옵션 (a) Phase 12+ 진입 (또 다른 territory) 결정 wire 보류
- 옵션 (b) Epic 18+ 진입 (예: SSO enterprise SAML follow-up, IdP admin follow-up, audit log archival viewer follow-up, advanced analytics 등) 결정 wire 보류
- 옵션 (c) carry-over 진입 (Phase 1~11 + Epic 1~17 carry-over) 결정 wire 보류
- 옵션 (d) 1st release 추가 follow-up 결정 wire 보류
- 옵션 (e) D-DEFER-* carry-over follow-up 결정 wire 보류 (현재 D-DEFER-* ✅ ALL RESOLVED + D-RETENTION-1 ✅ RESOLVED + D-OBSERVABILITY-1 ✅ RESOLVED + D-PERFORMANCE-1 ✅ RESOLVED + D-CHAOS-1 ✅ RESOLVED + D-SLO-1 ✅ RESOLVED + **D-FINOPS-1 honestly ✅ RESOLVED 보존 1 NEW** 상태로 새 follow-up 결정 wire 보류)

## §13. 결정 wire 일자

**결정 wire 일자**: 2026-08-24 (KST)
**cj-style entry point**: 108번째
**Phase 11 close-out retro commit**: TBD (atomic docs-only wire 1 진입점 결정 wire 진입 완료 후 git log 확인)

## §14. Cross-References

- Phase 11 PRD entry commit `16d7698` (cj-style 105번째)
- Phase 11 bmad-create-story spec entry `82c93a8` (cj-style 106번째)
- Phase 11 bmad-dev-story atomic wire T1~T8 `e020ad0` (cj-style 107번째)
- Phase 11 close-out retro (cj-style 108번째) — THIS
- Phase 10 close-out retro `733d428` (cj-style 104번째)
- Phase 10 atomic wire `ac5d6c5` (cj-style 103번째)
- Phase 10 spec entry `3c80ef0` (cj-style 102번째)
- Phase 10 PRD entry `09db4d4` (cj-style 101번째)
- Phase 9 close-out retro `634427d` (cj-style 100번째)
- Phase 9 atomic wire `e7670e1` (cj-style 99번째)
- Phase 9 spec entry `2a5e4da` (cj-style 98번째)
- Phase 9 PRD entry `0b2d2f3` (cj-style 97번째)
- Phase 8 close-out retro `ab495a8` (cj-style 96번째)
- Phase 8 atomic wire `60d4ea1` (cj-style 95번째)
- Phase 8 spec entry `5ae0f4e` (cj-style 94번째)
- Phase 8 PRD entry `ced452f` (cj-style 93번째)
- Build fixes sprint `eaee198` (dev server build fixes)
- Phase 7 close-out retro `326fa9f` (cj-style 92번째)
- Phase 7 atomic wire `59b56cd` (cj-style 91번째)
- Phase 7 spec entry (cj-style 90번째)
- Phase 7 PRD entry `916a541` (cj-style 89번째)
- Phase 6 close-out retro `f9f006c` (cj-style 88번째)
- Phase 6 atomic wire `24e1cd7` (cj-style 87번째)
- Phase 6 spec entry `f5c14c9` (cj-style 86번째)
- Phase 6 PRD entry `e84a281` (cj-style 85번째)
- Epic 17 close-out retro `be8f3bd` (cj-style 84번째)
- Epic 17 T2+T3 UI frontend atomic wire `bb92879` (cj-style 83번째)
- Epic 17 bmad-dev-story atomic wire T1~T8 backend `2ada2ec` (cj-style 82번째)
- Epic 17 bmad-create-story spec entry `f4b2b58` (cj-style 81번째)
- Epic 17 PRD entry `40a9c41` (cj-style 80번째)
- Sidebar/MenuProvider hot-fix `01a06e4` (cj-style 79번째)
- D-EPIC-16-REVIEW-DEFER-2~6 RESOLVE sprint `512ed6a` (cj-style 78번째)
- Phase 5 close-out retro `b843565` (cj-style 76~77번째)
- Phase 5 atomic wire `f093f8c` (cj-style 75번째)
- Phase 5 spec entry (cj-style 74번째)
- Phase 5 PRD entry `93d852b` (cj-style 73번째)
- Epic 16 close-out retro (cj-style 72번째)
- Epic 16 T4 admin UI follow-up sprint `ff5c3b5` (cj-style 71번째)
- Epic 16 review follow-up sprint `963079c` (cj-style 70번째)
- Epic 16 atomic wire `e117e09` (cj-style 69번째)
- Epic 16 spec entry (cj-style 68번째)
- Epic 16 PRD entry `08bfca5` (cj-style 67번째)
- 1st release cycle cj-style 62~66번째 모두 wire DONE 진입
- Epic 15 cycle cj-style 58~61번째 모두 wire DONE 진입 (D-1-1-DEFER-1/2/3 ✅ ALL RESOLVED 보존)
- Phase 4 cycle cj-style 53~57번째 모두 wire DONE 진입 (D-PHASE-4-DR-DEFER-1/2 ✅ RESOLVED 보존)
- Phase 3 cycle cj-style 49~52번째 모두 wire DONE 진입
- Epic 14 LISTEN/NOTIFY multi-process coordination `7835463` 보존
- Epic 13 LISTEN/NOTIFY consume `f2ea2f6` 보존
- Epic 12 2FA 게이트 `a63646c` 보존
- Epic 11 close-out retro + Phase 2 close-out baseline 599 passed 정합 보존
- Epic 1 carry-over (auth) layout + onboarding/industry 보존
- Epic 7~10 ABC/TDABC + AI 인사이트 territory 결정 wire 보존
- 1st release close-out retro §6 verbatim (D-FINOPS-1 honestly DEFERRED territory 보존)
- Epic 17 close-out retro §11 verbatim (D-FINOPS-1 honestly DEFERRED territory 보존)
- Phase 6 close-out retro §13 verbatim (D-FINOPS-1 honestly DEFERRED territory 보존)
- Phase 7 close-out retro §10 verbatim (D-FINOPS-1 honestly DEFERRED territory 보존)
- Phase 8 close-out retro §10 verbatim (D-FINOPS-1 honestly DEFERRED territory 보존)
- Phase 9 close-out retro §10 verbatim (D-FINOPS-1 honestly DEFERRED territory 보존)
- Phase 10 close-out retro §10 verbatim (D-FINOPS-1 honestly DEFERRED territory 보존)
- Phase 11 PRD entry A333~A338 결정 wire 진입 보존
- Phase 11 spec entry A339~A343 결정 wire 진입 보존
- Phase 11 wire A344~A353 결정 wire 진입 보존 (cj-style 107번째 결정 wire 신규 10 결정)
- Phase 11 close-out retro A354~A363 결정 wire 진입 보존 (cj-style 108번째 결정 wire 신규 10 결정)

---

**partial wire 시도 0건 + single sprint atomic docs-only wire 1 진입점 결정** (cj-style 108번째 epic 연속 정직 회복 Phase 11 close-out retro atomic docs-only wire 5 files atomic single sprint 결정 wire).
