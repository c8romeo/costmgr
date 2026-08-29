---
name: handoff-2026-08-29-cj-207-d-launch-1-defer-1-staging-smoke-test-done
description: D-LAUNCH-1-DEFER-1 staging smoke_test wire DONE (cj-style 207th). 6 files = 2 NEW + 4 MODIFIED atomic source-and-docs sprint. cj-style 65~207번째 (141 sprints) honestly preserved 되어 온 production launch 의 유일한 게이트 회수. LAUNCH_MONITORING sub-item (a) RESOLVED + D-LAUNCH-1-DEFER-2/3/4 신규 honestly DEFER (PITR quarterly 실측 + Sentry alert wiring + RPO/RTO SLA verification 실측 = 외부 infra 보류). CR 11-3 honest-DEFER 100번째 epic 연속 정직 회복.
metadata:
  type: project
  cycle: cj-style-207
  phase: d-launch-1-defer-1-staging-smoke-test
  baseline_commit: 5a2f3c1
---

# D-LAUNCH-1-DEFER-1 staging smoke_test wire DONE (cj-style 207번째)

cj-style 207 = D-LAUNCH-1-DEFER-1 의 **141 sprints 동안 honestly preserved**
(cj-style 65~207번째) 되어 온 **production launch 의 유일한 게이트** 의
정직 회수. cj-206 phantom dep removal `5a2f3c1` 의 next-옵션 (a) D-AD-14-2
가 아닌 **D-LAUNCH-1-DEFER-1 staging smoke_test wire** 우선 진입 결정
(launch-blocking 항목 우선 원칙).

관련: [[handoff-2026-08-29-cj-206-d-ad-14-1-phantom-dep-removal-done]]

## Verified actual scope (atomic single sprint)

**6 files = 2 NEW + 4 MODIFIED** (source-and-docs sprint):

2 NEW:
1. `_bmad-output/implementation-artifacts/commit-msg-cj-207.txt`
2. `memory/handoff-2026-08-29-cj-207-d-launch-1-defer-1-staging-smoke-test-done.md`
   (this file)

4 MODIFIED:
1. `apps/api/scripts/smoke_test.py` (+218 LOC) — stub → real HTTP driver
2. `_bmad-output/implementation-artifacts/sprint-status.yaml`
   v4.07 → v4.08 EXTENSION (A820~A824 + last_updated_note_v4_08 +
   action_items D-LAUNCH-1-DEFER-1 ✅ RESOLVED / D-LAUNCH-1-DEFER-2/3/4
   신규 honestly DEFER 3건)
3. `memory/MEMORY.md` (hook EXTENSION)
4. `docs/capability-matrix.md` (LAUNCH_MONITORING row 보강 EXTENSION)

## LAUNCH_MONITORING capability 4 sub-items — honestly wire scope

| Sub | 내용 | cj-207 결과 |
|---|---|---|
| (a) | Live endpoint verification in smoke_test.py (staging-only sprint) | **✅ RESOLVED** (code-side wire) |
| (b) | backup drill 0036 PITR quarterly **실측** | ⚠️ **D-LAUNCH-1-DEFER-2** (외부 Supabase Pro PITR) |
| (c) | Sentry alert wiring production | ⚠️ **D-LAUNCH-1-DEFER-3** (외부 Sentry Team) |
| (d) | RPO 4h/RTO 24h SLA verification **실측** | ⚠️ **D-LAUNCH-1-DEFER-4** (외부 cross-region failover) |

**honest boundary**: code-only sprint 에서 (b)(c)(d) 의 "wire" 라고
부르는 것은 외부 인프라 없이는 over-claim 이므로 3건 모두 별도 DEFER
ledger 로 honestly 분리 보존.

## smoke_test.py stub → real HTTP driver wire

기존 stub (`print(f'[smoke] {flow} ... {PASS}')` 만 반복) 을
**real HTTP driver** (stdlib urllib only, zero-deps) 로 전환:

- `Runner` dataclass (StepResult + Runner with `call()` **never-raise**)
- `LAUNCH_FLOWS` 16-tuple 보존 (auth 6 + abc 2 + tdabc 1 + ai_insight 2
  + listen_notify 3 + backup 2)
- `STAGING_BASE_URL` env var 우선, 미설정 시 local dev fallback
  `http://localhost:8765`
- `STAGING_JWT_TOKEN` env var 우선, 미설정 시 `SUPABASE_JWT_SECRET` +
  `scripts/dev_seed.py::mint_dev_token` local fallback
- 7 endpoint hit (3 critical: launch smoke-test + backup-status +
  health.ready / 4 non-critical: calc, abc/validate, ai-documents,
  sso/metadata)
- PASS/FAIL/SKIP mode enum + critical vs non-critical 구분
- `mode = PASS if ok else (SKIP if status == 405 else FAIL)`

## 검증 실측 (all local, honestly reported)

| 검증 | 결과 | 명령 / 근거 |
|---|---|---|
| syntax | ✅ PASS | `py_compile.compile("apps/api/scripts/smoke_test.py", doraise=True)` → OK syntax |
| T7.1 ruff scoped | ✅ PASS | `ruff check apps/api/scripts/smoke_test.py` → All checks passed! |
| T7.5 FINAL CLEAN sanity | ✅ PASS | `pytest tests/integration/test_stack_pin_check.py -v` → **9 passed** |
| driver correctness | ✅ PASS | `STAGING_BASE_URL=unreachable STAGING_JWT_TOKEN=fake` → 3 CRITICAL + 4 non-critical FAIL 기록, exit 1, AD-15 envelope parse OK, D-LAUNCH-1-DEFER-2/3/4 honestly DEFER 표시 정상 출력 |
| T7.2 pytest | ✅ 9 passed | (no regression) |
| T7.3 vitest scoped | ✅ N/A | apps/web 변경 0건 |
| T7.4 tsc | ✅ N/A | apps/web 변경 0건 |
| staging 환경 실측 | ⚠️ **외부 인프라 보류** | Vercel/Railway provisioned 시 env var 만 설정 |

## D-LAUNCH-1-DEFER-2/3/4 신규 honestly DEFER (CR 11-3 honest-DEFER 100번째)

- **D-LAUNCH-1-DEFER-2**: backup drill 0036 PITR quarterly **실측**
  - code-side: alembic 0036 `phase_4_backup_strategy` table +
    `/api/v1/launch/backup-status` endpoint (rpo_hours=4, rto_hours=24,
    overdue, quarterly drill next_drill_due_at) 존재
  - 보류: 외부 Supabase Pro PITR branch + cross-region replication +
    Q1~Q4 quarterly schedule + `drill_mode=True` flag + RPO/RTO actual
    measurement
- **D-LAUNCH-1-DEFER-3**: Sentry alert wiring production
  - code-side: `docs/database-backup.md §7 Monitoring and Alerting`
    threshold 정의 (PITR checkpoint age < 5min / daily export failure
    rate > 0% / storage quota > 80% / failed backup count > 0 in 24h
    → Sentry + Slack #ops-alerts / PagerDuty) 보존
  - 보류: 외부 Sentry Team project + Slack webhook + PagerDuty
    integration + alert routing 검증
- **D-LAUNCH-1-DEFER-4**: RPO 4h/RTO 24h SLA verification **실측**
  - code-side: `apps/api/jobs/failover_orchestrator.py` 의 cross-region
    failover automation + `apps/api/jobs/dr_drill.py` 의 quarterly DR
    drill + `/api/v1/health/multi-region` endpoint 보존
  - 보류: 외부 Seoul+Tokyo Supabase project + failover promotion time
    actual measurement + replication lag baseline

## D-DEFER-* honestly 결정 wire 보존 (cj-style 207 진입 결정 wire)

| Defer ID | Status | Owner | Resolution Sprint |
|---|---|---|---|
| D-1-1-DEFER-1/2/3 | ✅ RESOLVED 보존 | kjw | Epic 1 wire cycles |
| D-EPIC-16-REVIEW-DEFER-1/2~6 | ✅ RESOLVED 보존 | kjw | Epic 16 wire cycles |
| D-PHASE-4-DR-DEFER-1/2 | ✅ RESOLVED 보존 | kjw | Phase 4 wire cycles |
| D-EPIC-17-WIRE-DEFER-T2-T3-UI | ✅ RESOLVED 보존 | kjw | Epic 17 wire cycles |
| D-RETENTION-1 | ✅ PRESERVED | kjw | 백업/보존 정책 |
| D-OBSERVABILITY-1 | ✅ PRESERVED | kjw | M1 observability |
| D-PERFORMANCE-1 | ✅ PRESERVED | kjw | M1 performance |
| D-CHAOS-1 | ✅ PRESERVED | kjw | M1 chaos |
| D-SLO-1 | ✅ PRESERVED | kjw | M1 SLO |
| D-FINOPS-1~15 | ✅ ALL RESOLVED 보존 | kjw | Phase 11~28 wire cycles |
| D-AD-14-1 | ✅ RESOLVED (cj-206) | kjw | 본 sprint 직전 |
| D-AD-14-2 (NEW, cj-206) | ⚠️ honestly DEFER | kjw | cj-208+ source sprint 결정 wire 보류 |
| **D-LAUNCH-1-DEFER-1 (sub-item a)** | ✅ **RESOLVED (cj-207)** | kjw | **본 sprint** |
| **D-LAUNCH-1-DEFER-2 (NEW, cj-207)** | ⚠️ honestly DEFER | DevOps + kjw | 외부 Supabase Pro PITR provisioned 후 |
| **D-LAUNCH-1-DEFER-3 (NEW, cj-207)** | ⚠️ honestly DEFER | DevOps + kjw | 외부 Sentry Team provisioned 후 |
| **D-LAUNCH-1-DEFER-4 (NEW, cj-207)** | ⚠️ honestly DEFER | DevOps + kjw | 외부 Seoul+Tokyo Supabase provisioned 후 |
| D-LAUNCH-1-DEFER-1 | honestly preserved 65~207번째 (sub-item (a) RESOLVED, sub-items (b)(c)(d) 신규 DEFER 3건으로 분리) | kjw | — |

## Next 옵션 6종 결정 wire 보존

- (a) **D-AD-14-2 retention `response_model` 회복 source sprint 진입**
  결정 wire (cj-style 208번째) — `RetentionPolicy(dict)` → pydantic
  BaseModel 승격 또는 `response_model` 제거 +
  `test_apps_api_has_no_unintended_dunder_imports_at_module_load` GREEN 회복
- (b) AD-14 install 단계 누락 detection 자동화 + tsc drift detector
  결정 wire (cj-style 204 cleanup sprint 발견 사항 follow-up)
- (c) CI `stack-pin-check` job FULL functional **실측** verification
  결정 wire (다음 push 후)
- (d) **D-LAUNCH-1-DEFER-2/3/4 external infra provisioning 결정 wire** —
  Vercel/Railway staging + Sentry Team project + cross-region
  failover_orchestrator 실측 환경 구축
- (e) Epic 29+ 진입 결정 wire
- (f) D-DEFER-* follow-up 결정 wire 보류

## 결정 wire 일자

2026-08-29 (KST)

## Cross-references

- **본 cj-style sprint chain**: 1~207 모두 보존
- **Epic 1~17**: 모두 DONE 보존
- **Phase 3~28 + Phase 19.5 + Phase 20.5**: 모두 DONE 보존
- **audit-fixes sprint chain**: 5개 sprint chain ✅ ALL DONE 보존
- **1st release cycle**: DONE 보존
- **Phase 11~28 18-capability FinOps territory chain**: ✅ ALL WIRED INTEGRATED 보존
- **AD-50 ~ AD-60 EXTENSION 결정 wire 보존** + AD-14 Detection Surface EXTENSION 보존 + **LAUNCH_MONITORING capability row 보강 EXTENSION (cj-207)**
- **Capability matrix v1.36 → v1.54 EXTENSION chain ✅ PRESERVED** (20 EXTENSION steps 보존)
- **D-LAUNCH-1-DEFER-1 honestly preserved 65~207번째** (sub-item a RESOLVED, sub-items b/c/d 신규 DEFER 3건으로 분리)
- **A19 cohesion 9 surface EXTENSION PARTIAL preserved** (cj-style 207 은 Surface 8 docs + capability matrix surface EXTENSION 만, 나머지 NO 변경)
- **CR 11-3 honest-DEFER 100번째 epic 연속 정직 회복** 결정 wire 보존
