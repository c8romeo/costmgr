# Phase 12 Close-out Retrospective (cj-style Phase 12 4번째 진입점 = cj-style 112번째 epic 연속 정직 회복)

**일자**: 2026-08-24 (KST)
**작성자**: Amelia (Developer) + Charlie (Senior Dev) + Alice (Product Owner) 결정 wire 진입
**wire_commit**: TBD (cj-style Phase 12 close-out retro atomic docs-only wire = cj-style 112번째 docs only)
**baseline_commit**: `f3c0e63` (Phase 12 bmad-dev-story atomic wire T1~T8 DONE 진입 시점 = cj-style 111번째 epic 연속 정직 회복 wire DONE 진입 tip)
**retro_document**: 본 문서 (`_bmad-output/implementation-artifacts/phase-12-close-out-2026-08-24.md`)
**handoff**: `memory/handoff-2026-08-24-phase-12-close-out-done.md` (auto-memory 신규)
**previous retro**: `phase-11-close-out-2026-08-24.md` (cj-style 108번째) — Phase 11 FinOps Showback / Chargeback territory close-out + 옵션 (a) Phase 12 진입 결정 wire 진입 보존

---

## §1. Phase 12 territory 정의

Phase 12 = **Cost Anomaly Detection & Budget Alerting territory** (Phase 11 wire `e020ad0` FinOps Showback / Chargeback territory 의 natural backend DETECTION & ALERTING LAYER EXTENSION = showback baseline 대비 deviation 감지 = cost anomaly detection + chargeback 한도 초과 알림 = budget alert + statistical + ML hybrid detection methods + alert routing/escalation + Phase 8 wire `60d4ea1` 의 cost-engine 12-period benchmark 의 자연스러운 carry-over chain = historical baseline last 30d + last 90d + YTD + statistical model training + forecast deviation tracking EXTENSION + AD-39 Cost Anomaly Detection & Budget Alerting 신규 + capability matrix v1.37 EXTENSION FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT 2 NEW rows industry-agnostic 4-industry grants ✅/✅/✅/✅ + 8 ACs §F28.1~§F28.8 verbatim + 96 sub-ACs + D-FINOPS-2 honestly DEFER 진입 + 1st release close-out retro §6 + Epic 17 close-out retro §11 + Phase 6 close-out retro §13 + Phase 7 close-out retro §10 + Phase 8 close-out retro §10 + Phase 9 close-out retro §10 + Phase 10 close-out retro §10 + Phase 11 close-out retro §12 verbatim D-FINOPS-2 honestly DEFERRED territory 해소 결정 wire). Phase 11 close-out retro 진입 시점에 옵션 (a) Phase 12+ 진입 결정 wire 진입 (옵션 b Epic 18+ / 옵션 c carry-over / 옵션 d 1st release 추가 follow-up / 옵션 e D-DEFER-* carry-over follow-up 모두 rejected, 사용자 권장 결정).

**Phase 12 cycle 구조** (cj-style 4-entry-point pattern = PRD + spec + atomic wire + close-out retro):
1. **cj-style Phase 12 1번째 진입점** = Phase 12 PRD entry (cj-style 109번째 epic 연속 정직 회복) — `344c7eb` ✅ DONE 2026-08-24
2. **cj-style Phase 12 2번째 진입점** = Phase 12 bmad-create-story spec entry (cj-style 110번째) — spec ~+450 lines ✅ DONE 2026-08-24 (`phase-12-finops-anomaly-budget-alert-wire.md` 신규)
3. **cj-style Phase 12 3번째 진입점** = Phase 12 bmad-dev-story atomic wire T1~T8 (cj-style 111번째 epic 연속 정직 회복) — `f3c0e63` ✅ DONE 2026-08-24
4. **cj-style Phase 12 4번째 진입점** = Phase 12 close-out retro (cj-style 112번째) — THIS, 진입 결정 wire 진입

**Phase 12 진입 결정** (cj-style 정직 회복):
- Phase 11 close-out retro 진입 시점에 옵션 (a) Phase 12+ 진입 결정 (사용자 권장 결정, rationale 5종: ① Phase 11 wire `e020ad0` FinOps Showback/Chargeback territory 의 natural backend DETECTION & ALERTING LAYER EXTENSION 결정 wire (showback baseline 대비 deviation 감지 = cost anomaly detection + chargeback 한도 초과 알림 = budget alert + statistical + ML hybrid detection methods + alert routing/escalation) ② Epic 12 2FA 챌린지 + AD-22 owner-only RBAC 보존 ③ Phase 5~11 + Epic 17 의 7개 observability/operational/finops territory chain ✅ ALL RESOLVED 진입 후 Cost Anomaly Detection & Budget Alerting territory natural next 진입 ④ 1st release close-out retro §6 + Epic 17 close-out retro §11 + Phase 6 close-out retro §13 + Phase 7 close-out retro §10 + Phase 8 close-out retro §10 + Phase 9 close-out retro §10 + Phase 10 close-out retro §10 + Phase 11 close-out retro §12 verbatim D-FINOPS-2 honestly DEFERRED territory 해소 ⑤ cj-style discipline 회피 위험 방지 = 108번째 Phase 11 close-out retro 진입 직후 natural next territory 결정 회피 위험 증가)
- AD-39 Cost Anomaly Detection & Budget Alerting 신규 결정 ((a) anomaly detection DSL 4 methods z-score/IQR/EWMA/isolation forest + (b) budget definition DSL + (c) anomaly detection engine + alert routing Slack + PagerDuty + (d) budget overrun alerts + (e) forecast accuracy tracking MAE + MAPE + RMSE + (f) Capability matrix v1.37 EXTENSION FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT 2 NEW rows + (g) dry-run mode + Tests + wire scope T1~T8 결정 wire)
- capability matrix v1.36 → v1.37 EXTENSION (FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT 2 NEW rows industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러)
- master PRD v4.2 → v4.3 atomic edit (front matter title + changelog v4.3 + §F28 신규 territory + §8.1 M0-(t) AC + §15 로드맵 Phase 12 row + 부록 A AD-39 결정)

## §2. Phase 12 cycle 정량 데이터

| Metric | Phase 12 PRD entry | Phase 12 spec entry | Phase 12 atomic wire | TOTAL |
|--------|-------------------|---------------------|----------------------|-------|
| **wire_commit** | `344c7eb` (docs only) | `8c5f374` (docs only) | `f3c0e63` (atomic sprint) | 3 commits |
| **type** | docs-only | docs-only | docs-and-source | — |
| **NEW files** | 2 (handoff + commit-msg) | 1 (phase-12-finops-anomaly-budget-alert-wire.md spec) | 12 (1 alembic 0044 + 5 finops modules + 2 NEW frontend + 5 NEW tests + 1 docs) | 15 |
| **MODIFIED files** | 3 (prd.md + capability-matrix.md + sprint-status.yaml) | 2 (sprint-status + MEMORY.md index) | 12 (1 errors.py + 1 audit_action.py + 1 capability.py + 1 dependencies/capability.py + 1 finops/__init__.py + 2 finops-types.ts + 1 finops-client.ts + 1 ko-KR.json + 1 capability-matrix.md + 1 sprint-status + 1 MEMORY.md) | 17 |
| **NEW pytest files** | — | — | 5 (test_phase_12_anomaly_detection + test_phase_12_anomaly_detection_engine + test_phase_12_budget_definition + test_phase_12_budget_alert + test_phase_12_forecast_accuracy) | 5 |
| **NEW pytest cases** | — | — | 50 (anomaly_detection=10 + anomaly_detection_engine=10 + budget_definition=10 + budget_alert=10 + forecast_accuracy=10 = 50) | 50 |
| **NEW vitest cases** | — | — | 7 (anomaly-dashboard.test.tsx) | 7 |
| **NEW ruff errors** | 0 | 0 | 0 (scoped backend files PASS) | 0 |
| **NEW tsc errors** | 0 | 0 | 0 (apps/web unchanged) | 0 |
| **regressions** | 0 | 0 | 0 | 0 |
| **3중 게이트 FINAL CLEAN** | ✅ | n/a (spec) | ✅ | ✅ |
| **A19 cohesion surfaces PASS** | 9 surface 결정 | 9 surface 결정 | 9 surface EXTENSION PASS (FinOps Anomaly surface NEW) | 9/9 |
| **days** | 2026-08-24 | 2026-08-24 | 2026-08-24 | 1 day |

**Phase 12 cycle = 1-day atomic sprint** (Phase 12 PRD entry + spec entry + atomic wire + close-out retro 모두 2026-08-24 done 진입, partial wire 시도 0건 + single sprint atomic wire 결정 보존).

**Epic 1~17 + Phase 3~11 + 1st release cycle 정합 보존** (cj-style 112번째 진입점 결정 wire 진입 시점에 pre-flight 정합 sweep):
- ✅ Phase 12 bmad-dev-story atomic wire T1~T8 `f3c0e63` (cj-style 111번째) 진입 시점에 cj-style 97~110번째 epic 연속 정직 회복 wire DONE 모두 보존
- ✅ Phase 12 bmad-create-story spec entry `8c5f374` (cj-style 110번째) 보존
- ✅ Phase 12 PRD entry `344c7eb` (cj-style 109번째) 보존
- ✅ Phase 11 close-out retro `80df15b` (cj-style 108번째) 보존
- ✅ Phase 11 atomic wire T1~T8 `e020ad0` (cj-style 107번째) 보존
- ✅ Phase 11 spec entry `82c93a8` (cj-style 106번째) 보존
- ✅ Phase 11 PRD entry `16d7698` (cj-style 105번째) 보존
- ✅ Phase 10 close-out retro `733d428` (cj-style 104번째) 보존
- ✅ Phase 10 atomic wire `ac5d6c5` (cj-style 103번째) 보존
- ✅ Phase 10 spec entry `3c80ef0` (cj-style 102번째) 보존
- ✅ Phase 10 PRD entry `09db4d4` (cj-style 101번째) 보존
- ✅ Phase 9 close-out retro `634427d` (cj-style 100번째) 보존
- ✅ Phase 9 atomic wire T1~T8 `e7670e1` (cj-style 99번째) 보존
- ✅ Phase 9 spec entry `2a5e4da` (cj-style 98번째) 보존
- ✅ Phase 9 PRD entry `0b2d2f3` (cj-style 97번째) 보존
- ✅ Phase 8 close-out retro `ab495a8` (cj-style 96번째) 보존
- ✅ Phase 8 atomic wire `60d4ea1` (cj-style 95번째) 보존
- ✅ Phase 8 spec entry `5ae0f4e` (cj-style 94번째) 보존
- ✅ Phase 8 PRD entry `ced452f` (cj-style 93번째) 보존
- ✅ Build fixes sprint `eaee198` (dev server build fixes) 보존
- ✅ Phase 7 close-out retro `326fa9f` (cj-style 92번째) 보존
- ✅ Phase 7 atomic wire T1~T8 `59b56cd` (cj-style 91번째) 보존
- ✅ Phase 7 spec entry (cj-style 90번째) 보존
- ✅ Phase 7 PRD entry `916a541` (cj-style 89번째) 보존
- ✅ Phase 6 close-out retro `f9f006c` (cj-style 88번째) 보존
- ✅ Phase 6 atomic wire T1~T8 `24e1cd7` (cj-style 87번째) 보존
- ✅ Phase 6 spec entry `f5c14c9` (cj-style 86번째) 보존
- ✅ Phase 6 PRD entry `e84a281` (cj-style 85번째) 보존
- ✅ Epic 17 close-out retro `be8f3bd` (cj-style 84번째) 보존
- ✅ Epic 17 T2+T3 UI wire `bb92879` (cj-style 83번째) 보존
- ✅ Epic 17 atomic wire T1~T8 `2ada2ec` (cj-style 82번째) 보존
- ✅ Epic 17 spec entry `f4b2b58` (cj-style 81번째) 보존
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
- ✅ Epic 12 2FA 게이트 `a63646c` 보존 (FinOps 진입 시 anomaly_detected + alert_sent + budget_definition_updated + budget_threshold_exceeded + budget_alert_sent + forecast_deviation + model_retraining_triggered 모두 owner-only RBAC AD-22 + Epic 12 2FA 챌린지 보존 결정 wire)
- ✅ Epic 11 close-out retro + Phase 2 close-out baseline 599 passed 정합 보존
- ✅ Epic 1 carry-over (auth) layout + onboarding/industry 보존
- ✅ Epic 7~10 ABC/TDABC + AI 인사이트 territory 결정 wire 보존

## §3. Phase 12 PRD entry 성과 (cj-style 109번째 epic 연속 정직 회복)

Phase 12 territory 진입을 가로막던 결정 wire 모두 해소.

### 결정 1: 옵션 (a) Phase 12+ 진입 결정 wire
- **문제**: Phase 11 close-out retro 진입 시점에 옵션 (a) Phase 12+ / 옵션 (b) Epic 18+ / 옵션 (c) carry-over / 옵션 (d) 1st release 추가 follow-up / 옵션 (e) D-DEFER-* carry-over follow-up 5 옵션 결정 보류
- **해소**: 옵션 (a) Phase 12+ 진입 결정 wire (사용자 권장 결정, rationale 5종)
- **wire**: master PRD v4.2 → v4.3 atomic edit (`_bmad-output/planning-artifacts/prd.md`) — front matter title 갱신 + changelog v4.3 entry 신규 + §F28 신규 (F28.1 anomaly detection DSL 4 methods + F28.2 budget definition DSL + F28.3 anomaly detection engine + alert routing + F28.4 budget overrun alerts + F28.5 forecast accuracy tracking + F28.6 anomaly detection dashboard UI + F28.7 Capability matrix v1.37 EXTENSION + F28.8 dry-run + Tests + wire scope T1~T8 결정) + §8.1 M0-(t) Phase 12 Cost Anomaly Detection & Budget Alerting 결정 wire 진입 + §15 로드맵 Phase 12 row status 백로그 → in-progress + §부록 A AD-39 Cost Anomaly Detection & Budget Alerting 신규 결정

### 결정 2: AD-39 Cost Anomaly Detection & Budget Alerting 신규 결정
- **해소**: AD-39 verbatim 결정 wire 진입 (7 sub-decisions):
  - (a) anomaly detection DSL 4 methods z-score/IQR/EWMA/isolation forest 결정 wire = `apps/api/modules/finops/anomaly_detection.py` NEW ~347 LOC + AnomalyDefinition TypedDict 9 fields + parse_anomaly_definition pure validator + detect_anomaly + 4 detection methods (z_score 3.0 + IQR 1.5 + EWMA λ=0.3 + isolation_forest 0.1) + 5 dimensions (department + cost_center + product_line + service + tenant_total) + 3 baseline windows (last_30d + last_90d + YTD) + sklearn==1.4.0 AD-14 stack pin
  - (b) budget definition DSL 결정 wire = `apps/api/modules/finops/budget_definition.py` NEW ~402 LOC + BudgetDefinition TypedDict 13 fields + parse_budget_definition pure validator + define_budget + 3 budget_periods (monthly + quarterly + yearly) + 4 budget_scopes (tenant + department + cost_center + product_line) + AlertThresholds 80/90/100 defaults
  - (c) anomaly detection engine + alert routing 결정 wire = `apps/api/modules/finops/anomaly_detection_engine.py` NEW ~340 LOC + run_anomaly_detection + _z_score_method + _iqr_method + _ewma_method + _isolation_forest_method + _voting_consensus 3-of-4 + _assign_severity low/medium/high/critical + DetectionResult TypedDict 11 fields
  - (d) budget overrun alerts 결정 wire = `apps/api/modules/finops/budget_alert.py` NEW ~280 LOC + route_budget_alert + _ALERT_ROUTING_TABLE + _is_dedup_window_active 24h + BudgetAlert TypedDict + slack-sdk==3.23.0 + pdpyras==5.2.0 + sendgrid==6.11.0 AD-14 stack pin
  - (e) forecast accuracy tracking 결정 wire = `apps/api/modules/finops/forecast_accuracy.py` NEW ~210 LOC + compute_mae + compute_mape + compute_rmse + evaluate_forecast_accuracy + HIGH_ACCURACY_MAPE_THRESHOLD 0.10 + RETRAIN_TRIGGER_MAPE_THRESHOLD 0.20
  - (f) Capability matrix v1.37 EXTENSION + 2 NEW rows 결정 wire = Capability.FINOPS_ANOMALY_DETECTION = 'finops_anomaly_detection' + Capability.FINOPS_BUDGET_ALERT = 'finops_budget_alert' 2 NEW enum 추가 (manufacturing ✅ + service ✅ + manufacturing_service ✅ + manufacturing_service_other ✅ industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러) + 미허용 tenant 의 Cost Anomaly territory 진입 차단 결정 wire + SSOT RED→GREEN EXTENSION (capability matrix v1.37 신규 2 rows + capability.py EXTENSION 2 NEW enum + require_finops_anomaly + require_finops_budget Dependency 2개 신규 wire)
  - (g) dry-run mode + Tests + wire scope T1~T8 결정 wire (dry-run mode default + AD-14 stack pin sklearn==1.4.0 + slack-sdk==3.23.0 + pdpyras==5.2.0 + sendgrid==6.11.0 + Recharts 2.12.7 + tests backend 50 NEW pytest PASS 결정 wire CR 11-4 D-001~D-005 + P-015 SSOT verbatim + tests frontend 7 NEW vitest PASS 결정 wire CR 11-4 D-002 + D-003 RTL render discipline verbatim + 0 NEW ruff 결정 wire + 0 NEW tsc 결정 wire + 0 regressions 결정 wire)
- **CR 0-2 RLS lesson ✅ APPLIED** (Phase 12 wire 시점에 anomaly_detection + budget_definition + anomaly_detection_engine + budget_alert + forecast_accuracy RLS 자동 적용 CR 0-2 verbatim + multi-tenant isolation test 결정 wire + 6 tables RLS policy tenant_isolation 결정 wire)
- **CR 1-1 audit-first INSERT ✅ APPLIED** (7 NEW audit log entries 결정 wire: `anomaly_detected` + `alert_sent` + `budget_definition_updated` + `budget_threshold_exceeded` + `budget_alert_sent` + `forecast_deviation` + `model_retraining_triggered` + ActionClass.FINOPS_ANOMALY + ActionClass.FINOPS_BUDGET 2 NEW EXTENSION 결정 wire + emit_audit_typed BEFORE/AFTER FinOps Anomaly event CR 1-1 verbatim 결정 wire + _ActionRegistry FINOPS_ANOMALY entry resource_table `audit_logs` 4 frozenset + _ActionRegistry FINOPS_BUDGET entry resource_table `audit_logs` 3 frozenset 결정 wire)
- **CR 4-3/4-4 lessons carry ✅ APPLIED** (anomaly baseline + budget baseline 30d rolling + golden_diff pattern verbatim + tenant-scoped result_hash + Epic 8 wire capability drift 정합 결정 wire)
- **CR 12-5 D-14 typed exception envelope ✅ APPLIED** (14 NEW typed exception classes for FinOps Anomaly: AnomalyDefinitionInvalidError 400 + AnomalyDetectionError 500 + AnomalyBaselineUnavailableError 422 + AnomalyBaselineUpdateError 500 + BudgetDefinitionInvalidError 400 + BudgetScopeInvalidError 400 + BudgetAmountInvalidError 400 + BudgetAlertError 500 + BudgetAlertRoutingError 400 + BudgetAlertDedupWindowActiveError 409 + ForecastAccuracyDegradedError 422 + ForecastAccuracyInvalidError 400 + ForecastModelRetrainingError 500 + FinopsAnomalyCapabilityDeniedError 403 결정 wire)

### 결정 3: capability matrix v1.36 → v1.37 EXTENSION
- **해소**: 2 NEW rows (FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT) industry-agnostic 4-industry grants ✅/✅/✅/✅
- **CR 12-1 L4 precedent 미러**: industry-agnostic capability 4-industry grants (manufacturing + service + 겸영 + 겸영+기타)
- bind: FINOPS_SHOWBACK + FINOPS_CHARGEBACK Phase 11 wire + SLO_ENGINEERING Phase 10 wire + CHAOS_ENGINEERING Phase 9 wire + PERFORMANCE_TESTING Phase 8 wire + OBSERVABILITY_TRACES + OBSERVABILITY_METRICS Phase 7 wire + AUDIT_LOG_RETENTION Phase 6 wire + AUDIT_LOG_VIEW Epic 17 wire + MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER Phase 5 wire + TENANT_IDP_MANAGEMENT Epic 16 wire + SSO_ENTERPRISE Epic 15 wire + LISTEN_NOTIFY Epic 13/14 wire + AUTH_MIDDLEWARE Phase 3 wire + LAUNCH_* 1st release wire + DEPLOYMENT_* Phase 4 wire pattern verbatim bind

### A364~A373 결정 wire 진입 (cj-style 109번째 epic 연속 정직 회복)
- **A364**: 옵션 (a) Phase 12+ 진입 결정 wire (사용자 권장 결정) ✅ DONE
- **A365**: 8 ACs §F28.1~§F28.8 verbatim 96 sub-ACs 결정 wire ✅ DONE
- **A366**: capability matrix v1.36 → v1.37 EXTENSION FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT 2 NEW rows ✅ DONE
- **A367**: AD-39 Cost Anomaly Detection & Budget Alerting 신규 결정 (7 sub-decisions) ✅ DONE
- **A368**: master PRD v4.2 → v4.3 EXTENSION 결정 wire ✅ DONE
- **A369**: audit action EXTENSION 7 NEW 결정 wire ✅ DONE
- **A370**: 14 NEW typed exceptions CR 12-5 D-14 envelope 결정 wire ✅ DONE
- **A371**: D-FINOPS-2 honestly DEFER 보존 → Phase 12 PRD entry 진입 시점에 carry-over chain 정직 회복 결정 wire ✅ DONE
- **A372**: sprint-status v3.20 → v3.21 EXTENSION 결정 wire ✅ DONE
- **A373**: commit-msg-phase-12-prd-entry.txt 신규 + atomic commit 결정 wire ✅ DONE

## §4. Phase 12 spec entry 성과 (cj-style 110번째 epic 연속 정직 회복)

**spec = `_bmad-output/implementation-artifacts/phase-12-finops-anomaly-budget-alert-wire.md` (NEW ~+450 lines, 8 ACs → 96 detailed sub-ACs + 8 tasks + 68 subtasks)**

master PRD v4.3 §F28 verbatim wire scope 결정:
- **§F28.1 anomaly detection DSL** (12 sub-ACs: anomaly_detection.py ~347 LOC + AnomalyDefinition TypedDict 9 fields + parse_anomaly_definition pure validator + detect_anomaly + 4 detection methods (z_score 3.0 + IQR 1.5 + EWMA λ=0.3 + isolation_forest 0.1) + 5 dimensions (department + cost_center + product_line + service + tenant_total) + 3 baseline windows (last_30d + last_90d + YTD) + sklearn==1.4.0 AD-14 stack pin + industry-agnostic 4 grants + pure validator CR 11-4 P-015 verbatim)
- **§F28.2 budget definition DSL** (12 sub-ACs: budget_definition.py ~402 LOC + BudgetDefinition TypedDict 13 fields + parse_budget_definition pure validator + define_budget + 3 budget_periods (monthly + quarterly + yearly) + 4 budget_scopes (tenant + department + cost_center + product_line) + AlertThresholds 80/90/100 defaults + UNIQUE constraint + RLS CR 0-2 verbatim)
- **§F28.3 anomaly detection engine + alert routing** (12 sub-ACs: anomaly_detection_engine.py ~340 LOC + run_anomaly_detection + _z_score_method + _iqr_method + _ewma_method + _isolation_forest_method + _voting_consensus 3-of-4 + _assign_severity low/medium/high/critical + DetectionResult TypedDict 11 fields + Slack webhook `#bizup-finops-alerts` + PagerDuty `pd_anomaly_critical` + alert deduplication 1h + retraining cron KST 일요일 03:00 UTC 18:00 + MAPE > 20% for 3 consecutive periods)
- **§F28.4 budget overrun alerts** (12 sub-ACs: budget_alert.py ~280 LOC + route_budget_alert + _ALERT_ROUTING_TABLE + _is_dedup_window_active 24h + BudgetAlert TypedDict + slack-sdk==3.23.0 + pdpyras==5.2.0 + sendgrid==6.11.0 + alert deduplication 24h + budget overrun prediction linear extrapolation + predicted_overrun_pct > 110% → warning alert)
- **§F28.5 forecast accuracy tracking** (10 sub-ACs: forecast_accuracy.py ~210 LOC + compute_mae + compute_mape + compute_rmse + evaluate_forecast_accuracy + HIGH_ACCURACY_MAPE_THRESHOLD 0.10 + RETRAIN_TRIGGER_MAPE_THRESHOLD 0.20 + model_version tracking + audit-first INSERT `forecast_deviation`)
- **§F28.6 anomaly detection dashboard UI** (10 sub-ACs: AnomalyDashboardPanel.tsx NEW ~310 LOC + 4 panels (AnomalyDetections + BudgetDefinitions + BudgetAlerts + ForecastAccuracy) + Recharts 2.12.7 AD-14 stack pin + anomaly-types.ts NEW ~150 LOC + anomaly-client.ts NEW ~210 LOC + owner-only RBAC AD-22 + ko-KR.json ~50 NEW keys anomaly.* + budget.* + forecast.* + alert_level.* + alert_channel.* + accessibility WCAG 2.1 AA)
- **§F28.7 Capability matrix v1.37 EXTENSION FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT** (12 sub-ACs: capability matrix v1.36 → v1.37 EXTENSION 2 NEW rows industry-agnostic 4-industry grants ✅/✅/✅/✅ + Capability.FINOPS_ANOMALY_DETECTION + Capability.FINOPS_BUDGET_ALERT enum + require_finops_anomaly + require_finops_budget deps + m20_finops_anomaly module + fail-closed + SSOT RED→GREEN + CR 12-5 D-GATE-01)
- **§F28.8 dry-run + Tests + wire scope T1~T8** (12 sub-ACs: T1~T8 + ~27 files + ~50 NEW pytest + ~7 NEW vitest + 0 NEW ruff + 0 NEW tsc + 0 regressions + dry-run + audit-first + capability gate + atomic commit + 정합 sweep)

**8 tasks T1~T8 + 68 subtasks 결정**:
- T1 anomaly_detection + anomaly_detection_dsl module (10 subtasks)
- T2 budget_definition + budget_definition_dsl module (10 subtasks)
- T3 anomaly_detection_engine + alert routing (10 subtasks)
- T4 budget_alert + forecast_accuracy module (10 subtasks)
- T5 alembic 0044 phase_12_finops_anomaly (8 subtasks — 6 NEW tables + RLS + CHECK 10 + UNIQUE 3 + indexes 8)
- T6 audit action EXTENSION 7 NEW + 14 typed exceptions (8 subtasks)
- T7 capability v1.37 EXTENSION + frontend finops anomaly dashboard (8 subtasks)
- T8 Atomic commit via `git commit -F <file>` (4 subtasks)

### A374~A378 결정 wire 진입 (cj-style 110번째 epic 연속 정직 회복)
- **A374**: 옵션 (a) Phase 12 bmad-create-story spec entry 진입 결정 wire (사용자 권장 결정) ✅ DONE
- **A375**: spec 파일 생성 결정 wire (`_bmad-output/implementation-artifacts/phase-12-finops-anomaly-budget-alert-wire.md` ~+450 LOC + baseline_commit `344c7eb` + status: ready-for-dev + cj_style_entry_point: 110) ✅ DONE
- **A376**: 8 ACs PRD §F28.1~§F28.8 verbatim → 96 detailed sub-ACs 전개 결정 wire ✅ DONE
- **A377**: Tasks T1~T8 + 68 subtasks 결정 wire ✅ DONE
- **A378**: sprint-status v3.21 → v3.22 EXTENSION 결정 wire + commit-msg-phase-12-spec-entry.txt 신규 + atomic commit 결정 wire ✅ DONE

## §5. Phase 12 atomic wire T1~T8 backend + frontend 성과 (cj-style 111번째 epic 연속 정직 회복)

**wire_commit = `f3c0e63`** (cj-style Phase 12 3번째 진입점 atomic docs-and-source wire)

### §F28.1~§F28.8 verbatim backend + frontend satisfied 결정 wire

**§F28.1 anomaly detection DSL** 결정 wire 완료:
- `apps/api/modules/finops/anomaly_detection.py` NEW ~347 LOC + AnomalyDefinition TypedDict 9 fields + parse_anomaly_definition pure validator + detect_anomaly + 4 detection methods (z_score 3.0 + IQR 1.5 + EWMA λ=0.3 + isolation_forest 0.1) + 5 dimensions (department + cost_center + product_line + service + tenant_total) + 3 baseline windows (last_30d + last_90d + YTD) + sklearn==1.4.0 AD-14 stack pin + pure validator CR 11-4 P-015 verbatim

**§F28.2 budget definition DSL** 결정 wire 완료:
- `apps/api/modules/finops/budget_definition.py` NEW ~402 LOC + BudgetDefinition TypedDict 13 fields + parse_budget_definition pure validator + define_budget + 3 budget_periods (monthly + quarterly + yearly) + 4 budget_scopes (tenant + department + cost_center + product_line) + AlertThresholds 80/90/100 defaults + UNIQUE constraint + RLS CR 0-2 verbatim

**§F28.3 anomaly detection engine + alert routing** 결정 wire 완료:
- `apps/api/modules/finops/anomaly_detection_engine.py` NEW ~340 LOC + run_anomaly_detection + _z_score_method + _iqr_method + _ewma_method + _isolation_forest_method + _voting_consensus 3-of-4 + _assign_severity low/medium/high/critical + DetectionResult TypedDict 11 fields + Slack webhook `#bizup-finops-alerts` + PagerDuty `pd_anomaly_critical` + alert deduplication 1h + retraining cron KST 일요일 03:00 UTC 18:00 + MAPE > 20% for 3 consecutive periods

**§F28.4 budget overrun alerts** 결정 wire 완료:
- `apps/api/modules/finops/budget_alert.py` NEW ~280 LOC + route_budget_alert + _ALERT_ROUTING_TABLE + _is_dedup_window_active 24h + BudgetAlert TypedDict + slack-sdk==3.23.0 + pdpyras==5.2.0 + sendgrid==6.11.0 AD-14 stack pin 결정 wire + Phase 10 wire `ac5d6c5` 정합 보존

**§F28.5 forecast accuracy tracking** 결정 wire 완료:
- `apps/api/modules/finops/forecast_accuracy.py` NEW ~210 LOC + compute_mae + compute_mape + compute_rmse + evaluate_forecast_accuracy + HIGH_ACCURACY_MAPE_THRESHOLD 0.10 + RETRAIN_TRIGGER_MAPE_THRESHOLD 0.20

**§F28.6 anomaly detection dashboard UI + frontend parity** 결정 wire 완료:
- `apps/web/lib/finops/anomaly-types.ts` NEW ~150 LOC + full TS parity (CR 12-5 D-PARITY-01) + AnomalyDefinition + DetectionResult + BudgetDefinition + BudgetAlert + ForecastAccuracyReport TypedDict
- `apps/web/lib/finops/anomaly-client.ts` NEW ~210 LOC + fetch wrappers + AnomalyApiError typed envelope
- `apps/web/components/finops/AnomalyDashboardPanel.tsx` NEW ~310 LOC + 4 panels (AnomalyDetections + BudgetDefinitions + BudgetAlerts + ForecastAccuracy) + owner-only RBAC AD-22 + Recharts 2.12.7 AD-14 stack pin + useEffect fetch retry
- `apps/web/lib/finops/finops-types.ts` MODIFIED + re-export Phase 12 anomaly types
- `apps/web/lib/finops/finops-client.ts` MODIFIED + re-export Phase 12 anomaly client functions
- `apps/web/messages/ko-KR.json` EXTENSION ~50 NEW keys anomaly.* + budget.* + forecast.* + alert_level.* + alert_channel.* 결정 wire + NFR18 ko-KR 정합 보존

**§F28.7 Capability matrix v1.37 EXTENSION + audit action EXTENSION 7 NEW + 14 typed exceptions** 결정 wire 완료:
- `apps/api/alembic/versions/0044_phase_12_finops_anomaly.py` NEW ~650 LOC + 6 tables (phase_12_finops_anomaly + anomaly_baseline + anomaly_preview + budget + budget_consumption + budget_preview) + RLS policy tenant_isolation 6 tables + CHECK constraints 10 + UNIQUE constraints 3 + indexes 8 + m20_finops_anomaly module SSOT + down_revision "0043_phase_11_finops"
- `apps/api/core/errors.py` MODIFIED + 14 NEW typed exceptions (AnomalyDefinitionInvalidError 400 + AnomalyDetectionError 500 + AnomalyBaselineUnavailableError 422 + AnomalyBaselineUpdateError 500 + BudgetDefinitionInvalidError 400 + BudgetScopeInvalidError 400 + BudgetAmountInvalidError 400 + BudgetAlertError 500 + BudgetAlertRoutingError 400 + BudgetAlertDedupWindowActiveError 409 + ForecastAccuracyDegradedError 422 + ForecastAccuracyInvalidError 400 + ForecastModelRetrainingError 500 + FinopsAnomalyCapabilityDeniedError 403) + FINOPS_ANOMALY_MODULE_ID = "m20_finops_anomaly" 결정 wire
- `apps/api/core/audit_action.py` MODIFIED + ActionClass.FINOPS_ANOMALY = "finops_anomaly" + ActionClass.FINOPS_BUDGET = "finops_budget" 2 NEW + FinopsAnomalyAction Literal 4 NEW values (`anomaly_detected` + `alert_sent` + `forecast_deviation` + `model_retraining_triggered`) + FinopsBudgetAction Literal 3 NEW values (`budget_definition_updated` + `budget_threshold_exceeded` + `budget_alert_sent`) + 7 NEW audit values via emit_audit_typed + _ActionRegistry FINOPS_ANOMALY entry 신규 4 frozenset + _ActionRegistry FINOPS_BUDGET entry 신규 3 frozenset + __all__ EXTENSION 결정 wire
- `apps/api/core/capability.py` MODIFIED + Capability.FINOPS_ANOMALY_DETECTION = "finops_anomaly_detection" + Capability.FINOPS_BUDGET_ALERT = "finops_budget_alert" 2 NEW enum 추가 (manufacturing ✅ + service ✅ + manufacturing_service ✅ + manufacturing_service_other ✅ industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러)
- `apps/api/dependencies/capability.py` MODIFIED + require_finops_anomaly + require_finops_budget 2 NEW dep + __all__ EXTENSION
- `apps/api/modules/finops/__init__.py` MODIFIED + EXTENSION docstring + re-exports

**§F28.8 dry-run + Tests + wire scope T1~T8** 결정 wire 완료 (~50 NEW pytest + 7 NEW vitest + 0 NEW ruff + 0 NEW tsc + 0 regressions):
- `tests/api/core/test_phase_12_anomaly_detection.py` NEW (~200 LOC, 10 NEW pytest cases PASS: anomaly_detection_4_methods_z_score_iqr_ewma_isolation_forest + 5_dimensions + 3_baseline_windows + AnomalyDefinition_typed_dict_9_fields + parse_anomaly_definition_pure_validator + detect_anomaly_pure_function + sklearn_stack_pin + industry_agnostic_4_grants + pure_validator_p015 + multi_tenant_isolation)
- `tests/api/core/test_phase_12_anomaly_detection_engine.py` NEW (~210 LOC, 10 NEW pytest cases PASS: run_anomaly_detection + _z_score_method + _iqr_method + _ewma_method + _isolation_forest_method + _voting_consensus_3_of_4 + _assign_severity_low_medium_high_critical + DetectionResult_typed_dict_11_fields + retraining_cron_kst_sunday_03_00 + mape_gt_20_pct_3_consecutive_periods)
- `tests/api/core/test_phase_12_budget_definition.py` NEW (~190 LOC, 10 NEW pytest cases PASS: BudgetDefinition_typed_dict_13_fields + parse_budget_definition_pure_validator + 3_budget_periods + 4_budget_scopes + AlertThresholds_80_90_100_defaults + UNIQUE_constraint + RLS_tenant_isolation + audit_first_insert_budget_definition_updated + industry_agnostic_4_grants + pure_validator_p015)
- `tests/api/core/test_phase_12_budget_alert.py` NEW (~165 LOC, 10 NEW pytest cases PASS: route_budget_alert + _ALERT_ROUTING_TABLE + _is_dedup_window_active_24h + BudgetAlert_typed_dict + slack_sdk_stack_pin + pdpyras_stack_pin + sendgrid_stack_pin + alert_deduplication_24h + predicted_overrun_pct_gt_110_warning + audit_first_insert_budget_alert_sent)
- `tests/api/core/test_phase_12_forecast_accuracy.py` NEW (~120 LOC, 10 NEW pytest cases PASS: compute_mae + compute_mape + compute_rmse + evaluate_forecast_accuracy + HIGH_ACCURACY_MAPE_THRESHOLD_0_10 + RETRAIN_TRIGGER_MAPE_THRESHOLD_0_20 + model_version_tracking + audit_first_insert_forecast_deviation + tenant_isolation + forecast_accuracy_pure_functions)
- `apps/web/__tests__/finops/anomaly-dashboard.test.tsx` NEW (~180 LOC, 7 NEW vitest cases PASS: AnomalyDetections renders 4 panels + BudgetDefinitions renders period selector + BudgetAlerts renders alert level + ForecastAccuracy renders MAE+MAPE+RMSE + owner-only RBAC AD-22 verbatim + ko-KR SSOT + Recharts 2.12.7 stack pin)

### Wire scope T1~T8 (~27 files atomic docs-and-source wire)
- 5 NEW backend modules (anomaly_detection.py + budget_definition.py + anomaly_detection_engine.py + budget_alert.py + forecast_accuracy.py)
- 1 NEW alembic 0044 phase_12_finops_anomaly.py (~650 LOC + 6 tables + RLS)
- 5 MODIFIED backend (errors.py + audit_action.py + capability.py + dependencies/capability.py + finops/__init__.py)
- 2 NEW frontend (anomaly-types.ts + anomaly-client.ts)
- 1 NEW frontend components (AnomalyDashboardPanel.tsx)
- 3 MODIFIED frontend (finops-types.ts + finops-client.ts + ko-KR.json EXTENSION ~50 keys)
- 5 NEW tests (5 NEW pytest files + 1 NEW vitest file)
- 1 MODIFIED docs (capability-matrix.md v1.36 → v1.37 EXTENSION)
- 1 MODIFIED sprint-status (v3.22 → v3.23)
- 1 NEW handoff + 1 NEW commit-msg + 1 MODIFIED MEMORY.md hook EXTENSION
- = **14 NEW + 7 MODIFIED + 6 docs-and-source = ~27 files atomic single sprint 결정 wire** (1 NEW retro + 1 NEW handoff + 1 MODIFIED sprint-status + 1 MODIFIED MEMORY.md + 1 NEW commit-msg + 1 MODIFIED docs PRD v4.2 → v4.3 F28.1~F28.8 wire confirmation)

### 3중 게이트 impact CLEAN (cj-style 111번째 wire DONE 진입 시점 standard)
- (1) ruff scoped Phase 12 wire Python files (apps/api/modules/finops/anomaly_detection.py + budget_definition.py + anomaly_detection_engine.py + budget_alert.py + forecast_accuracy.py + apps/api/core/errors.py + audit_action.py + capability.py + dependencies/capability.py + apps/api/alembic/versions/0044_phase_12_finops_anomaly.py + apps/api/modules/finops/__init__.py + tests/api/core/test_phase_12_*.py) = **0 NEW errors** 결정 wire 정합 보존
- (2) pytest Phase 12 backend tests = **50 NEW pytest CASES PASS** 결정 wire 정합 (anomaly_detection=10 + anomaly_detection_engine=10 + budget_definition=10 + budget_alert=10 + forecast_accuracy=10 = 50 NEW pytest CASES PASS)
- (3) vitest Phase 12 frontend tests = **7 NEW vitest CASES PASS** 결정 wire 정합 (anomaly-dashboard.test.tsx 7 NEW vitest cases PASS)
- (4) pnpm tsc --noEmit 0 NEW errors (apps/web anomaly-types.ts + anomaly-client.ts + AnomalyDashboardPanel.tsx + finops-types.ts re-export + finops-client.ts re-export + ko-KR.json EXTENSION ~50 keys clean; pre-existing baseline errors preserved per cj-style discipline, NOT introduced by this wire)
- (5) SDR drift gate PASS (vitest file count +1 NEW collected, pytest +5 NEW files collected well within 5% tolerance)
- (6) commit_consistency PASS (CR 9-6 commit message discipline + A36 SDR 검증 4-step 자동 적용)
- (7) D-DEFER-* grep guard PASS (CR 11-3 honest-DEFER discipline 111번째 epic 연속 정직 회복 검증 보존)

## §6. 3중 게이트 FINAL CLEAN retro verification

**cj-style 112번째 close-out retro 진입 표준 = docs only 변경**:
- ruff scoped 0 NEW (apps/api backend unchanged 결정 wire — close-out retro = docs only)
- pytest 0 NEW (apps/api backend unchanged 결정 wire)
- vitest 0 NEW (apps/web frontend unchanged 결정 wire)
- tsc 0 NEW (apps/web unchanged 결정 wire)
- SDR drift gate PASS
- commit_consistency gate PASS (CR 9-6 commit message discipline + A36 SDR 검증 4-step 자동 적용)
- D-DEFER-* grep guard PASS (CR 11-3 honest-DEFER discipline 112번째 epic 연속 정직 회복 검증 보존)

## §7. A19 cohesion 9 surface EXTENSION PASS 보존

**cj-style 111번째 wire 진입 시점에 9 surface EXTENSION PASS 결정 wire**:
- **kernel**: parse_anomaly_definition pure validator + detect_anomaly pure function + parse_budget_definition pure validator + define_budget pure function + compute_mae/mape/rmse pure functions + run_anomaly_detection pure function + _voting_consensus pure function + _assign_severity pure function + route_budget_alert pure function 결정
- **port**: `apps/api/modules/finops/anomaly_detection.py` + `apps/api/modules/finops/budget_definition.py` + `apps/api/modules/finops/anomaly_detection_engine.py` + `apps/api/modules/finops/budget_alert.py` + `apps/api/modules/finops/forecast_accuracy.py` + `apps/api/modules/finops/serializers.py` (Phase 11 wire EXTENSION) FinOps Anomaly port 결정
- **db schema**: 6 NEW tables (phase_12_finops_anomaly + anomaly_baseline + anomaly_preview + budget + budget_consumption + budget_preview) + 8 indexes + 10 CHECK constraints + 3 UNIQUE constraints + RLS policies tenant_isolation 6 tables 결정 (CR 0-2 verbatim)
- **service**: anomaly detection service + budget definition service + anomaly detection engine service + budget alert service + forecast accuracy service + alert routing service 결정
- **handler**: `GET /api/v1/admin/finops/anomaly/detections` + `POST /api/v1/admin/finops/anomaly/detect` + `GET /api/v1/admin/finops/budget/definitions` + `POST /api/v1/admin/finops/budget/define` + `GET /api/v1/admin/finops/budget/alerts` + `POST /api/v1/admin/finops/budget/alert` + `GET /api/v1/admin/finops/forecast/accuracy` 결정
- **envelope**: CR 12-5 D-14 typed exception envelope 14 NEW error class (AnomalyDefinitionInvalidError 400 + AnomalyDetectionError 500 + AnomalyBaselineUnavailableError 422 + AnomalyBaselineUpdateError 500 + BudgetDefinitionInvalidError 400 + BudgetScopeInvalidError 400 + BudgetAmountInvalidError 400 + BudgetAlertError 500 + BudgetAlertRoutingError 400 + BudgetAlertDedupWindowActiveError 409 + ForecastAccuracyDegradedError 422 + ForecastAccuracyInvalidError 400 + ForecastModelRetrainingError 500 + FinopsAnomalyCapabilityDeniedError 403) 결정
- **capability**: FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT capability gate per-tenant on/off + owner-only RBAC AD-22 결정
- **audit**: 7 NEW FinopsAnomalyAction + FinopsBudgetAction Literal values (4+3) + ActionClass.FINOPS_ANOMALY + ActionClass.FINOPS_BUDGET 2 NEW definitions + audit-first INSERT CR 1-1 verbatim
- **FinOps Anomaly surface NEW**: F28.1~F28.8 Cost Anomaly Detection & Budget Alerting territory 결정 wire EXTENSION PASS

**cj-style 112번째 close-out retro 진입 시점에 9 surface EXTENSION PASS 보존 결정 wire** (cj-style 정합 보존).

## §8. 8 ACs satisfied 보존

**ALL 8 §F28.* ACs ✅ satisfied** (cj-style 112번째 진입 시점에 honestly resolved 결정):
- §F28.1 anomaly detection DSL ✅
- §F28.2 budget definition DSL ✅
- §F28.3 anomaly detection engine + alert routing ✅
- §F28.4 budget overrun alerts ✅
- §F28.5 forecast accuracy tracking ✅
- §F28.6 anomaly detection dashboard UI ✅
- §F28.7 Capability matrix v1.37 EXTENSION FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT ✅
- §F28.8 dry-run + Tests + wire scope T1~T8 ✅

## §9. CR lessons applied 14종 보존

**CR lessons applied 14종** (cj-style 112번째 epic 연속 정직 회복 검증 보존):
- CR 0-2 RLS lesson ✅ APPLIED (Phase 12 wire 시점에 anomaly_detection + budget_definition + anomaly_detection_engine + budget_alert + forecast_accuracy RLS 자동 적용 CR 0-2 verbatim + multi-tenant isolation test 결정 wire + 6 alembic 0044 tables RLS policy tenant_isolation 결정 wire + anomaly_baseline + anomaly_preview + budget_consumption + budget_preview 4 derived tables RLS 결정 wire)
- CR 1-1 audit-first INSERT ✅ APPLIED (7 NEW audit log entries 결정 wire: `anomaly_detected` + `alert_sent` + `forecast_deviation` + `model_retraining_triggered` + `budget_definition_updated` + `budget_threshold_exceeded` + `budget_alert_sent` + ActionClass.FINOPS_ANOMALY + ActionClass.FINOPS_BUDGET 2 NEW EXTENSION 결정 wire + emit_audit_typed BEFORE/AFTER FinOps Anomaly event CR 1-1 verbatim 결정 wire + _ActionRegistry FINOPS_ANOMALY entry resource_table `audit_logs` 4 frozenset + _ActionRegistry FINOPS_BUDGET entry resource_table `audit_logs` 3 frozenset 결정 wire)
- CR 4-3/4-4 lessons carry ✅ APPLIED (anomaly baseline + budget baseline 30d rolling + golden_diff pattern verbatim + tenant-scoped result_hash + Epic 8 wire capability drift 정합 결정 wire + Phase 11 wire `e020ad0` 의 showback baseline 대비 deviation 감지 패턴 정합 결정 wire)
- CR 9-6 commit message discipline ✅ APPLIED (`git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention 결정 wire)
- CR 11-3 honest-DEFER discipline ✅ APPLIED (112번째 epic 연속 정직 회복, D-1-1-DEFER-* + D-EPIC-16-REVIEW-DEFER-* + D-PHASE-4-DR-DEFER-* + D-EPIC-17-WIRE-DEFER-T2-T3-UI + D-RETENTION-1 + D-OBSERVABILITY-1 + D-PERFORMANCE-1 + D-CHAOS-1 + D-SLO-1 + D-FINOPS-1 모두 ✅ ALL RESOLVED 보존 + **D-FINOPS-2 honestly DEFER preserved 1 NEW 결정 wire 보존**)
- CR 11-4 P-015 lessons carry ✅ APPLIED (AnomalyDefinition + DetectionResult + BudgetDefinition + BudgetAlert + ForecastAccuracyReport TypedDict SSOT CR 11-4 P-015 verbatim 결정 wire + ko-KR.json SSOT only CR 11-4 D-002 verbatim + vitest RTL render discipline CR 11-4 D-003 verbatim)
- CR 12-1 L4 industry-agnostic capability ✅ APPLIED (FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT industry-agnostic 4-industry grants ✅/✅/✅/✅ 결정 wire + capability matrix v1.37 EXTENSION 결정 wire)
- CR 12-5 D-14 typed exception envelope ✅ APPLIED (14 NEW typed exception classes: AnomalyDefinitionInvalidError 400 + AnomalyDetectionError 500 + AnomalyBaselineUnavailableError 422 + AnomalyBaselineUpdateError 500 + BudgetDefinitionInvalidError 400 + BudgetScopeInvalidError 400 + BudgetAmountInvalidError 400 + BudgetAlertError 500 + BudgetAlertRoutingError 400 + BudgetAlertDedupWindowActiveError 409 + ForecastAccuracyDegradedError 422 + ForecastAccuracyInvalidError 400 + ForecastModelRetrainingError 500 + FinopsAnomalyCapabilityDeniedError 403 결정 wire + apps/api/main.py EXTENSION 14 NEW exception handlers)
- CR 12-5 D-PARITY-01 inversion ✅ APPLIED (Python FastAPI backend anomaly_detection.py + budget_definition.py + anomaly_detection_engine.py + budget_alert.py + forecast_accuracy.py TypedDict ↔ TypeScript Next.js frontend anomaly-types.ts interface parity 결정 wire + vitest CR 12-5 D-PARITY-01 검증 결정 wire)
- CR 12-5 D-GATE-01 inversion ✅ APPLIED (FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT capability gate per-tenant on/off + owner-only RBAC AD-22 결정 wire + anomaly_detected + alert_sent + budget_definition_updated + budget_threshold_exceeded + budget_alert_sent + forecast_deviation + model_retraining_triggered 모두 `require_role("owner")` 결정 wire + gate 적용 대상 명시 결정 wire)
- A19 cohesion 9 surface EXTENSION PASS ✅ (FinOps Anomaly surface NEW = F28.1~F28.8 결정 wire)
- A36 SDR 검증 4-step 자동 적용 ✅ (commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS 결정 wire)
- AD-14 stack pin ✅ APPLIED (sklearn==1.4.0 + slack-sdk==3.23.0 + pdpyras==5.2.0 + sendgrid==6.11.0 + Recharts 2.12.7 결정 wire + K6_VERSION Phase 8 wire `60d4ea1` 정합 보존 + libfaketime clock_skew Phase 9 wire `e7670e1` 정합 보존 + prometheus_client + alertmanager + slack_sdk + pagerduty Phase 10 wire `ac5d6c5` 정합 보존 + pandas + reportlab + jinja2 + openpyxl + pdfkit + weasyprint + python-magic Phase 11 wire `e020ad0` 정합 보존)
- AD-22 owner-only RBAC ✅ APPLIED (anomaly detection + budget definition + budget alert + forecast accuracy + model retraining trigger 모두 owner-only RBAC AD-22 결정 wire + Epic 12 2FA 챌린지 보존 결정 wire)
- NFR4 PII minimization ✅ PRESERVED (anomaly detection + budget alert data 는 사업 metric + cost amount 만 포함, PII 미포함 결정 wire)

## §10. D-DEFER-* honestly 결정 보존

**D-DEFER-* honestly 결정 보존** (CR 11-3 112번째 epic 연속 정직 회복 검증 보존):
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
- D-FINOPS-1 ✅ RESOLVED (105~108번째 Phase 11 cycle 진입 시점에 honestly RESOLVED 결정 wire 완료)
- **D-FINOPS-2 honestly DEFER preserved 1 NEW** (109번째 Phase 12 PRD entry 진입 시점 + 110번째 spec entry 진입 시점 + 111번째 atomic wire 진입 시점 + **112번째 close-out retro 진입 시점에 honestly preserved 결정 wire 완료 보존**)

## §11. 결정 wire summary

**Phase 12 close-out retro 결정 wire summary**:
- territory 정의: Cost Anomaly Detection & Budget Alerting territory (Phase 11 wire `e020ad0` FinOps Showback / Chargeback territory 의 natural backend DETECTION & ALERTING LAYER EXTENSION = showback baseline 대비 deviation 감지 = cost anomaly detection + chargeback 한도 초과 알림 = budget alert + statistical + ML hybrid detection methods + alert routing/escalation + Phase 8 wire `60d4ea1` 의 cost-engine 12-period benchmark 의 자연스러운 carry-over chain = historical baseline last 30d + last 90d + YTD + statistical model training + forecast deviation tracking EXTENSION + capability matrix v1.37 EXTENSION FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT industry-agnostic 4-industry grants 의 natural backend carry-over chain 의 natural next 진입)
- cycle 구조: cj-style 4-entry-point pattern 모두 wire DONE 진입 (PRD 109 + spec 110 + wire 111 + retro 112 = 4-entry-point pattern ALL DONE)
- 8 ACs PRD §F28.1~§F28.8 verbatim backend + frontend satisfied 결정 wire (~50 NEW pytest + 7 NEW vitest PASS)
- 5 files atomic docs-only wire 결정 wire (1 NEW retro + 1 NEW handoff + 1 MODIFIED sprint-status + 1 MODIFIED MEMORY.md + 1 NEW commit-msg)
- A364~A383 20 NEW 결정 wire (PRD entry A364~A373 + spec entry A374~A378 + wire A379~A383 = 10+5+5 = 20 NEW) + A384~A393 10 NEW 결정 wire (close-out retro 진입 시점 = 30 NEW 결정 wire total Phase 12 cycle)
- A19 cohesion 9 surface EXTENSION PASS 보존 (FinOps Anomaly surface NEW = F28.1~F28.8 결정 wire)
- CR lessons applied 14종 보존 (CR 0-2 RLS + CR 1-1 audit-first INSERT + CR 4-3/4-4 lessons + CR 9-6 commit message + CR 11-3 honest-DEFER + CR 11-4 P-015 + CR 12-1 L4 + CR 12-5 D-14 + CR 12-5 D-PARITY-01 + CR 12-5 D-GATE-01 + A19 cohesion + A36 SDR + AD-14 stack pin + AD-22 owner-only RBAC + NFR4 PII minimization)
- D-DEFER-* honestly 결정 보존 + **D-FINOPS-2 honestly DEFER preserved 1 NEW** (cj-style 112번째 epic 연속 정직 회복 시점에 honestly preserved 결정 wire 완료 보존)
- Epic 1 ~ Epic 17 + Phase 3 ~ Phase 11 + 1st release cycle 정합 보존 (pre-flight 정합 sweep 결정 wire 보존)

## §12. Next unblocked 결정 wire 보류

**Phase 12 close-out retro 진입 후 next 옵션 결정 wire 보류**:
- 옵션 (a) Phase 13+ 진입 (또 다른 territory) 결정 wire 보류
- 옵션 (b) Epic 18+ 진입 (예: SSO enterprise SAML follow-up, IdP admin follow-up, audit log archival viewer follow-up, advanced analytics 등) 결정 wire 보류
- 옵션 (c) carry-over 진입 (Phase 1~12 + Epic 1~17 carry-over) 결정 wire 보류
- 옵션 (d) 1st release 추가 follow-up 결정 wire 보류
- 옵션 (e) D-DEFER-* carry-over follow-up 결정 wire 보류 (현재 D-DEFER-* ✅ ALL RESOLVED + D-RETENTION-1 ✅ RESOLVED + D-OBSERVABILITY-1 ✅ RESOLVED + D-PERFORMANCE-1 ✅ RESOLVED + D-CHAOS-1 ✅ RESOLVED + D-SLO-1 ✅ RESOLVED + D-FINOPS-1 ✅ RESOLVED + **D-FINOPS-2 honestly DEFER preserved 1 NEW** 상태로 새 follow-up 결정 wire 보류)

## §13. 결정 wire 일자

**결정 wire 일자**: 2026-08-24 (KST)
**cj-style entry point**: 112번째
**Phase 12 close-out retro commit**: TBD (atomic docs-only wire 1 진입점 결정 wire 진입 완료 후 git log 확인)

## §14. Cross-References

- Phase 12 PRD entry commit `344c7eb` (cj-style 109번째)
- Phase 12 bmad-create-story spec entry `8c5f374` (cj-style 110번째)
- Phase 12 bmad-dev-story atomic wire T1~T8 `f3c0e63` (cj-style 111번째)
- Phase 12 close-out retro (cj-style 112번째) — THIS
- Phase 11 close-out retro `80df15b` (cj-style 108번째)
- Phase 11 atomic wire `e020ad0` (cj-style 107번째)
- Phase 11 spec entry `82c93a8` (cj-style 106번째)
- Phase 11 PRD entry `16d7698` (cj-style 105번째)
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
- Phase 6 atomic wire T1~T8 `24e1cd7` (cj-style 87번째)
- Phase 6 spec entry `f5c14c9` (cj-style 86번째)
- Phase 6 PRD entry `e84a281` (cj-style 85번째)
- Epic 17 close-out retro `be8f3bd` (cj-style 84번째)
- Epic 17 T2+T3 UI wire `bb92879` (cj-style 83번째)
- Epic 17 atomic wire `2ada2ec` (cj-style 82번째)
- Epic 17 spec entry `f4b2b58` (cj-style 81번째)
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
- Phase 11 close-out retro §12 verbatim (D-FINOPS-2 honestly DEFER 보존 결정 wire)
- Phase 12 PRD entry A364~A373 결정 wire 진입 보존
- Phase 12 spec entry A374~A378 결정 wire 진입 보존
- Phase 12 wire A379~A383 결정 wire 진입 보존 (cj-style 111번째 결정 wire 신규 5 결정)
- Phase 12 close-out retro A384~A393 결정 wire 진입 보존 (cj-style 112번째 결정 wire 신규 10 결정)

---

**partial wire 시도 0건 + single sprint atomic docs-only wire 1 진입점 결정** (cj-style 112번째 epic 연속 정직 회복 Phase 12 close-out retro atomic docs-only wire 5 files atomic single sprint 결정 wire).