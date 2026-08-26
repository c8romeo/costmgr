---
baseline_commit: 563ac9c
status: ready-for-dev
cj_style_entry_point: 150
story_key: phase-21-finops-reserved-capacity-planning-wire
---

# Phase 21 FinOps Reserved Capacity Planning wire spec (cj-style 150번째 epic 연속 정직 회복)

## Story

**As a** FinOps practitioner / cloud architect / tenant admin / 1st release customer / DevOps engineer
**I want** Phase 21 territory 결정 wire (FinOps Reserved Capacity Planning = **demand_forecast_aggregator** + **capacity_planning_aggregator** + **commitment_recommendation_engine** + **reserved_capacity_orchestrator** + **reserved_capacity dashboard UI 5 sub-components** + **Capability matrix v1.47 EXTENSION FINOPS_RESERVED_CAPACITY_PLANNING** + **audit action EXTENSION 8 NEW + 16 NEW typed exception classes** + **dry-run + Tests + wire scope T1~T8**) 결정 wire
**so that** Phase 11~20 10-module FinOps territory chain ✅ ALL WIRED 진입 정합 보존 후 Phase 21 PRD entry `563ac9c` (cj-style 149번째) 진입 직후 자연스러운 spec entry 진입 = cj-style 4-entry-point cycle PRD entry → spec entry → wire → close-out retro 의 2번째 단계 진입 결정 wire (Phase 17 spec entry cj-style 130번째 + Phase 18 spec entry cj-style 134번째 + Phase 19 spec entry cj-style 138번째 + Phase 20 spec entry cj-style 143번째 패턴 verbatim 미러) + Phase 21 territory = 5 FinOps modules (Phase 13 forecast + Phase 14 optimization + Phase 18 commitment + Phase 19 pricing + Phase 20 multi_cloud) 의 natural composition layer = single demand_forecast_id + single capacity_plan_id + single commitment_recommendation_id + single orchestration_id (composition_step_chain 5 step EXTENSION) 결정 wire + new backend infra 불필요 + reuse 최대화 + risk 최소화 + 비즈니스 가치 최고 + Epic 12 2FA 챌린지 mandatory + AD-22 owner-only RBAC + NFR4 PII minimization ✅ PRESERVED + NFR18 ko-KR SSOT + AD-49 신규 (a)~(g) 7 sub-decisions 모두 결정 wire 진입 + D-FINOPS-10 honestly DEFER 보존 + CR 11-3 honest-DEFER 40번째 epic 연속 정직 회복 verification 결정 wire 진입 + 3중 게이트 impact NONE (docs only 변경 = cj-style 150번째 wire 진입 표준 = docs only sprint) 결정 wire.

## Context

cj-style Phase 21 1번째 진입점 (cj-style 149번째) 진입 결정 wire 진입 완료:

- Phase 21 PRD entry `563ac9c` (cj-style 149번째) DONE 진입 정합 보존
- Phase 20.5 close-out retro `8505d98` (cj-style 148번째) DONE 진입 정합 보존
- Phase 20.5 atomic wire T1~T3 `46ddcc5` (cj-style 147번째) DONE 진입 정합 보존
- Phase 20.5 spec entry `e23141d` (cj-style 146번째) DONE 진입 정합 보존
- Phase 20 close-out retro `f361016` (cj-style 145번째) DONE 진입 정합 보존
- Phase 20 atomic wire T1~T8 `52dad7f` (cj-style 144번째) DONE 진입 정합 보존
- Phase 20 spec entry `bdc7997` (cj-style 143번째) DONE 진입 정합 보존
- Phase 20 PRD entry `eacb0a5` (cj-style 142번째) DONE 진입 정합 보존
- Phase 19.5 carry-over 결정 wire `b2fb1d8` (cj-style 141번째) DONE 진입 정합 보존
- Phase 19 close-out retro `18ca1ae` (cj-style 140번째) + Phase 19 atomic wire T1~T8 `8db3cfc` (cj-style 139번째) + Phase 19 spec entry `59d15fb` (cj-style 138번째) + Phase 19 PRD entry `ff8a797` (cj-style 137번째) + Phase 18 close-out retro `de72f50` (cj-style 136번째) + Phase 18 atomic wire T1~T8 `67059cf` (cj-style 135번째) + Phase 18 spec entry `bdc7997` (cj-style 134번째) + Phase 18 PRD entry `5eded22` (cj-style 133번째) + Phase 17 close-out retro `de009fe` (cj-style 132번째) + Phase 17 atomic wire T1~T8 `97cfe4e` (cj-style 131번째) + Phase 17 spec entry `4be3120` (cj-style 130번째) + Phase 17 PRD entry `e0778ed` (cj-style 129번째) + Phase 16 close-out retro `26fd530` (cj-style 128번째) + Phase 16 atomic wire T1~T8 `81ae00a` (cj-style 127번째) + Phase 16 spec entry `69c29df` (cj-style 126번째) + Phase 16 PRD entry `4f11d03` (cj-style 125번째) + Phase 15 close-out retro `102f370` (cj-style 124번째) + Phase 15 atomic wire T1~T8 `1b800d9` (cj-style 123번째) + Phase 15 spec entry `69c29df` (cj-style 122번째) + Phase 15 PRD entry `87393b4` (cj-style 121번째) + ... + Epic 1~17 ALL DONE 진입 정합 보존 + 1st release cycle ALL DONE 진입 정합 보존

### Phase 21 PRD entry `563ac9c` 의 8 ACs §F37.1~§F37.8 verbatim 보존

8 ACs §F37.1~§F37.8 → 86 detailed sub-ACs (12+12+12+12+12+12+4+10) pre-flight 정합 sweep 만족 결정 wire:
1. **§F37.1 demand_forecast_aggregator** — 5-module cross-join + ReservedCapacityDemandForecast TypedDict 16 fields + confidence interval + seasonal_factor + growth_rate_pct 4 industries baseline + audit-first INSERT `demand_forecast_calculated` (12 sub-ACs)
2. **§F37.2 capacity_planning_aggregator** — 6 reserved_capacity_tier enum + break_even_utilization_pct + capacity_headroom_pct 10~20% + MINIMUM_SAVINGS_PCT=5.0 + MINIMUM_SAVINGS_KRW=1M + audit-first INSERT `capacity_planning_recommended` (12 sub-ACs)
3. **§F37.3 commitment_recommendation_engine** — confidence_score + risk_score + execution_strategy 4 enum + owner approval flow high-value (≥ 10M KRW/year) → Epic 12 2FA 챌린지 + audit-first INSERT `commitment_recommendation_generated` (12 sub-ACs)
4. **§F37.4 reserved_capacity_orchestrator** — composition_step_chain 5 step + 4 cadence schedule (daily 02:00 + weekly Mon 03:00 + monthly 1st-day 04:00 + quarterly 1st-day 05:00 KST pytz) + dry-run + 1 NEW CLI flag + audit-first INSERT `reserved_capacity_orchestrator_triggered` (12 sub-ACs)
5. **§F37.5 reserved_capacity dashboard UI** — 5 sub-components (DemandForecastPanel + CapacityPlanningPanel + CommitmentRecommendationPanel + ReservedCapacityOrchestratorPanel + ReservedCapacityTrendMiniChart) + FinopsReservedCapacityDashboardPanel.tsx Client component ~+250 LOC + 5-tab layout + Recharts 2.12.7 AD-14 stack pin + ko-KR.json EXTENSION ~30 keys (12 sub-ACs)
6. **§F37.6 Capability matrix v1.47 EXTENSION FINOPS_RESERVED_CAPACITY_PLANNING** — Capability.FINOPS_RESERVED_CAPACITY_PLANNING 1 NEW enum + require_finops_reserved_capacity 1 NEW dep + ActionClass.FINOPS_RESERVED_CAPACITY_PLANNING + FinopsReservedCapacityAction 8 NEW Literal + 16 NEW typed exception classes (CR 12-5 D-14 envelope) + alembic 0053 8 tables + RLS 8 tables + 1 preview table + drift detector (12 sub-ACs)
7. **§F37.7 audit action EXTENSION 8 NEW + 16 NEW typed exception classes** — (reserved_capacity_dashboard_viewed + demand_forecast_calculated + capacity_planning_recommended + commitment_recommendation_generated + reserved_capacity_dry_run_executed + reserved_capacity_kpi_refreshed + reserved_capacity_commitment_executed + reserved_capacity_orchestrator_triggered) + 16 NEW typed exception classes (CR 12-5 D-14 envelope) (4 sub-ACs)
8. **§F37.8 dry-run + Tests + wire scope T1~T8** — 1 NEW CLI flag + phase_21_orchestration_preview 1 table + ~+108 NEW pytest PASS + ~+7 NEW vitest PASS + 0 NEW ruff + 0 regressions + wire scope T1~T8 (10 sub-ACs)

**Total sub-ACs**: 12+12+12+12+12+12+4+10 = **86 sub-ACs** pre-flight 정합 sweep 만족 결정 wire.

### AD-49 신규 결정 (a)~(g) 7 sub-decisions

- (a) demand_forecast_aggregator 의 5-module cross-join backend detail (Phase 13 + Phase 14 + Phase 18 + Phase 19 + Phase 20 module outputs 의 가중 평균 = single forecasted_demand_krw)
- (b) capacity_planning_aggregator 의 reserved_capacity_tier selection algorithm detail (6 tier + break_even_utilization_pct + capacity_headroom_pct + MINIMUM_SAVINGS_PCT=5.0 + MINIMUM_SAVINGS_KRW=1M)
- (c) commitment_recommendation_engine 의 confidence + risk scoring detail (utilization_stability × 0.4 + historical_accuracy × 0.3 + demand_forecast_confidence_pct × 0.3 = confidence_score / savings_pct × 0.4 + commitment_term × 0.3 + commitment_flexibility × 0.3 = risk_score)
- (d) reserved_capacity_orchestrator 의 composition_step_chain 5 step detail (demand_forecast → capacity_planning → commitment_recommendation → approval → execute)
- (e) 4 cadence schedule KST pytz detail (daily 02:00 + weekly Mon 03:00 + monthly 1st-day 04:00 + quarterly 1st-day 05:00 KST pytz timezone('Asia/Seoul'))
- (f) LISTEN/NOTIFY 4 channel cross-tenant invalidation pattern EXTENSION (phase_21_demand_forecast_calculated + phase_21_capacity_planning_recommended + phase_21_commitment_recommendation_generated + phase_21_reserved_capacity_orchestrated)
- (g) owner approval flow high-value threshold detail (≥ 10M KRW/year savings → Epic 12 2FA 챌린지 mandatory + Slack DM + 2FA + approval_chain)

### D-FINOPS-10 honestly DEFER 보존

Phase 21 PRD entry 진입 시점에 carry-over chain 정직 회복 결정 wire 진입 = 5-module composition layer 의 backend detail + reserved_capacity_tier selection algorithm detail + commitment_recommendation confidence + risk scoring detail + reserved_capacity_orchestrator composition_step_chain 5 step detail — 모두 단일 sprint `wire` 진입이 아닌 docs-only entry 에서 honestly defer 결정 wire 보존 (Phase 17 close-out retro `be8f3bd` §11 "FinOps Reserved Capacity Planning 결정 wire 보류, Phase 21+ 진입 시점" verbatim 해소).

## T1~T8 + ~24 subtasks

### T1: Phase 21 4 backend aggregators modules (8 subtasks)
- T1.1: `apps/api/modules/finops/reserved_capacity/__init__.py` NEW + ALLOWED_SERVICE_SUBMODULES EXTENSION m21_finops_reserved_capacity 신규 submodule 등록 결정 wire (Phase 20 m20_finops_multi_cloud 패턴 보존)
- T1.2: `apps/api/modules/finops/reserved_capacity/demand_forecast_aggregator.py` NEW ~+220 LOC + `aggregate_demand_forecast(tenant_id, period_key, scope_chain) -> ReservedCapacityDemandForecast` TypedDict 16 fields + 5-module cross-join EXTENSION 결정 wire (Phase 13 forecast + Phase 14 optimization + Phase 18 commitment + Phase 19 pricing + Phase 20 multi_cloud 가중 평균 = single forecasted_demand_krw + confidence interval + seasonal_factor + growth_rate_pct 4 industries baseline + audit-first INSERT `demand_forecast_calculated` CR 1-1 verbatim EXTENSION)
- T1.3: `apps/api/modules/finops/reserved_capacity/capacity_planning_aggregator.py` NEW ~+220 LOC + `plan_reserved_capacity` TypedDict 18 fields + 6 reserved_capacity_tier enum + break_even_utilization_pct + capacity_headroom_pct 10~20% + MINIMUM_SAVINGS_PCT=5.0 + MINIMUM_SAVINGS_KRW=1M + audit-first INSERT `capacity_planning_recommended` CR 1-1 verbatim EXTENSION 결정 wire
- T1.4: `apps/api/modules/finops/reserved_capacity/commitment_recommendation_engine.py` NEW ~+250 LOC + `generate_commitment_recommendation` TypedDict 17 fields + confidence_score (utilization_stability × 0.4 + historical_accuracy × 0.3 + demand_forecast_confidence_pct × 0.3) + risk_score (savings_pct × 0.4 + commitment_term × 0.3 + commitment_flexibility × 0.3) + execution_strategy 4 enum (auto_execute_ready + manual_review_required + owner_approval_required + low_confidence) + high-value (≥ 10M KRW/year) → Epic 12 2FA 챌린지 mandatory + owner approval flow + audit-first INSERT `commitment_recommendation_generated` CR 1-1 verbatim EXTENSION 결정 wire
- T1.5: `apps/api/modules/finops/reserved_capacity/reserved_capacity_orchestrator.py` NEW ~+250 LOC + `orchestrate_reserved_capacity` TypedDict 19 fields + composition_step_chain 5 step (demand_forecast → capacity_planning → commitment_recommendation → approval → execute) + 4 cadence schedule (daily 02:00 KST + weekly Mon 03:00 KST + monthly 1st-day 04:00 KST + quarterly 1st-day 05:00 KST pytz timezone('Asia/Seoul')) + dry-run mode + 1 NEW CLI flag (`--finops-reserved-capacity-orchestrator-dry-run`) + audit-first INSERT `reserved_capacity_orchestrator_triggered` CR 1-1 verbatim EXTENSION 결정 wire
- T1.6: `apps/api/modules/finops/reserved_capacity/serializers.py` NEW ~+100 LOC + Pydantic v2 serializers + ReservedCapacityDemandForecast + ReservedCapacityPlan + CommitmentRecommendation + ReservedCapacityOrchestration 4 NEW TypedDict serializers 결정 wire
- T1.7: 4 backend aggregators composition layer 검증 (Phase 13 + 14 + 18 + 19 + 20 module outputs 의 direct import + cross-join) + LISTEN/NOTIFY 4 channel EXTENSION 결정 wire
- T1.8: A19 cohesion 9 surface EXTENSION PASS preserved 검증 (FinOps Reserved Capacity Planning surface NEW = F37.1~F37.8)

### T2: reserved_capacity dashboard UI 5 sub-components (8 subtasks)
- T2.1: `apps/web/app/[locale]/(dashboard)/admin/finops/reserved-capacity/page.tsx` NEW ~+220 LOC + 5 sub-components (DemandForecastPanel + CapacityPlanningPanel + CommitmentRecommendationPanel + ReservedCapacityOrchestratorPanel + ReservedCapacityTrendMiniChart) EXTENSION 결정 wire
- T2.2: `apps/web/app/[locale]/(dashboard)/admin/finops/reserved-capacity/layout.tsx` NEW ~+100 LOC + owner-only RBAC AD-22 verbatim + Epic 12 2FA 챌린지 mandatory + ko-KR.json `finops_reserved_capacity.*` namespace EXTENSION ~30 keys (CR 11-4 D-002 verbatim SSOT) + ARIA labels WCAG 2.1 AA + `(dashboard)` route group 보호 EXTENSION 결정 wire
- T2.3: `apps/web/components/finops/FinopsReservedCapacityDashboardPanel.tsx` NEW Client component ~+250 LOC + 5-tab layout + Recharts visualization (AreaChart + BarChart + LineChart + GanttChart + PieChart) 결정 wire
- T2.4: `apps/web/lib/finops/reserved-capacity-types.ts` NEW TypeScript mirror + 4 NEW TypeScript interfaces (ReservedCapacityDemandForecast + ReservedCapacityPlan + CommitmentRecommendation + ReservedCapacityOrchestration) CR 12-5 D-PARITY-01 inversion EXTENSION 결정 wire
- T2.5: `apps/web/lib/finops/reserved-capacity-client.ts` NEW TypeScript client + 4 NEW methods (aggregateDemandForecast + planReservedCapacity + generateCommitmentRecommendation + orchestrateReservedCapacity) EXTENSION 결정 wire
- T2.6: `apps/web/messages/ko-KR.json` MODIFIED EXTENSION ~30 keys + `finops_reserved_capacity.*` namespace EXTENSION + ARIA labels WCAG 2.1 AA + NFR18 ko-KR SSOT 보존 결정 wire
- T2.7: reserved_capacity dashboard Recharts 2.12.7 AD-14 stack pin EXTENSION + 5 NEW charts (AreaChart + BarChart + LineChart + GanttChart + PieChart) + 4 industries baseline visualization 차이 EXTENSION 결정 wire
- T2.8: reserved_capacity dashboard dry-run mode UI (ReservedCapacityOrchestratorPanel 진입 시 dry-run toggle default: dry-run) + scheduled dispatch KST cron 4 cadence UI + AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory 결정 wire

### T3: alembic 0053 phase_21_reserved_capacity_planning 8 tables + RLS + 1 preview table (6 subtasks)
- T3.1: `apps/api/alembic/versions/0053_phase_21_reserved_capacity_planning.py` NEW 8 NEW tables 결정 wire = phase_21_reserved_capacity_demand_forecast + phase_21_demand_forecast_audit + phase_21_reserved_capacity_plan + phase_21_capacity_planning_audit + phase_21_commitment_recommendation + phase_21_commitment_recommendation_audit + phase_21_reserved_capacity_orchestration + phase_21_orchestration_audit EXTENSION
- T3.2: phase_21_orchestration_preview 1 NEW preview table 결정 wire + preview_id UUID PK + tenant_id UUID + period_key TEXT + orchestration_data JSONB + computed_at TIMESTAMPTZ DEFAULT NOW() + trace_id TEXT EXTENSION
- T3.3: RLS 자동 적용 CR 0-2 verbatim 결정 wire = 8 tables tenant_id = current_setting('app.tenant_id')::uuid + 1 preview table RLS EXTENSION
- T3.4: CHECK + UNIQUE + indexes EXTENSION 결정 wire = idempotency_key UNIQUE + scope enum CHECK + 5-module source attribution JSONB GIN index + period_key + scope composite index EXTENSION
- T3.5: alembic 0053 down_revision 결정 wire = 0052 (Phase 20 wire `52dad7f` 의 alembic 0052 EXTENSION) EXTENSION
- T3.6: alembic upgrade + downgrade 검증 결정 wire + Phase 20 wire 의 alembic 0052 pattern verbatim EXTENSION

### T4: audit action EXTENSION 8 NEW + 16 NEW typed exception classes (4 subtasks)
- T4.1: `apps/api/core/audit_action.py` MODIFIED EXTENSION 결정 wire + ActionClass.FINOPS_RESERVED_CAPACITY_PLANNING 1 NEW enum EXTENSION
- T4.2: `apps/api/core/audit_action.py` MODIFIED EXTENSION + FinopsReservedCapacityAction 8 NEW Literal EXTENSION (reserved_capacity_dashboard_viewed + demand_forecast_calculated + capacity_planning_recommended + commitment_recommendation_generated + reserved_capacity_dry_run_executed + reserved_capacity_kpi_refreshed + reserved_capacity_commitment_executed + reserved_capacity_orchestrator_triggered)
- T4.3: `apps/api/core/errors.py` MODIFIED EXTENSION 16 NEW typed exception classes CR 12-5 D-14 envelope 결정 wire = ReservedCapacityDemandForecastError(500) + ReservedCapacityDemandForecastScopeError(404) + ReservedCapacityDemandForecastPeriodError(422) + ReservedCapacityDemandForecastModuleError(502) + ReservedCapacityPlanningError(500) + ReservedCapacityPlanningScopeError(404) + ReservedCapacityPlanningTierError(422) + ReservedCapacityPlanningGuardError(500) + ReservedCapacityRecommendationError(500) + ReservedCapacityRecommendationConfidenceError(500) + ReservedCapacityRecommendationApprovalError(500) + ReservedCapacityRecommendationExecutionError(500) + ReservedCapacityOrchestratorError(500) + ReservedCapacityOrchestratorStepError(500) + ReservedCapacityDryRunError(500) + ReservedCapacityIdempotencyError(500)
- T4.4: 8 NEW audit actions via emit_audit_typed CR 1-1 verbatim EXTENSION 결정 wire + Phase 20 wire `52dad7f` 의 8 NEW audit actions pattern verbatim EXTENSION

### T5: Capability matrix v1.47 EXTENSION FINOPS_RESERVED_CAPACITY_PLANNING (4 subtasks)
- T5.1: `docs/capability-matrix.md` MODIFIED v1.46 → v1.47 EXTENSION 결정 wire + FINOPS_RESERVED_CAPACITY_PLANNING 1 NEW row after FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION industry-agnostic 4-industry grants ✅/✅/✅/✅ CR 12-1 L4 precedent verbatim EXTENSION
- T5.2: `apps/api/core/capability.py` MODIFIED EXTENSION + Capability.FINOPS_RESERVED_CAPACITY_PLANNING 1 NEW enum 결정 wire
- T5.3: `apps/api/dependencies/capability.py` MODIFIED EXTENSION + require_finops_reserved_capacity 1 NEW dep 결정 wire
- T5.4: `apps/api/modules/finops/__init__.py` MODIFIED EXTENSION + reserved_capacity submodule export + ALLOWED_SERVICE_SUBMODULES 즉시 sweep EXTENSION = m21_finops_reserved_capacity 신규 submodule 등록 (Phase 20 m20_finops_multi_cloud 패턴 보존) + Phase 11~20 verbatim EXTENSION

### T6: scheduled_dispatch_job wire (2 subtasks)
- T6.1: `apps/api/modules/finops/reserved_capacity/scheduled_reserved_capacity_dispatch.py` NEW ~+150 LOC + apscheduler==3.10.4 + pytz==2024.1 EXTENSION + 4 cadence schedule (daily 02:00 + weekly Mon 03:00 + monthly 1st-day 04:00 + quarterly 1st-day 05:00 KST) + recipient resolver Slack + Email + S3 archive 결정 wire
- T6.2: LISTEN/NOTIFY consume trigger EXTENSION 결정 wire = 4 NEW channel (phase_21_demand_forecast_calculated + phase_21_capacity_planning_recommended + phase_21_commitment_recommendation_generated + phase_21_reserved_capacity_orchestrated) + Phase 13 wire `8b98030` LISTEN/NOTIFY pattern verbatim EXTENSION 결정 wire

### T7: dry-run mode + 1 NEW CLI flag (4 subtasks)
- T7.1: dry-run mode EXTENSION 결정 wire = dry-run 시 actual `reserved_capacity_orchestrator_triggered` audit-first INSERT skip + dry-run 결과 preview = phase_21_orchestration_preview 1 table + audit-first INSERT `reserved_capacity_dry_run_executed` EXTENSION
- T7.2: `apps/api/scripts/cli/finops_reserved_capacity_dry_run.py` NEW ~+100 LOC + `--finops-reserved-capacity-orchestrator-dry-run` 1 NEW CLI flag EXTENSION 결정 wire (Phase 20 wire `52dad7f` 의 5 NEW CLI flags 패턴 verbatim EXTENSION)
- T7.3: dry-run preview UI EXTENSION 결정 wire = ReservedCapacityOrchestratorPanel 진입 시 dry-run toggle (default: dry-run) + dry-run 결과 preview UI EXTENSION
- T7.4: dry-run mode integration tests EXTENSION 결정 wire = ~+6 NEW pytest cases (skip audit + preview table + CLI flag + 4 cadence) EXTENSION

### T8: 3중 게이트 FINAL CLEAN atomic commit (4 subtasks)
- T8.1: ruff scoped Phase 21 files 0 NEW EXTENSION 결정 wire + Phase 20 wire `52dad7f` 의 0 NEW ruff pattern verbatim EXTENSION
- T8.2: pytest ~+108 NEW pytest PASS EXTENSION 결정 wire (demand_forecast_aggregator 24 + capacity_planning_aggregator 30 + commitment_recommendation_engine 24 + reserved_capacity_orchestrator 30 = ~+108 NEW pytest PASS)
- T8.3: vitest ~+7 NEW vitest PASS EXTENSION 결정 wire (DemandForecastPanel 1 + CapacityPlanningPanel 1 + CommitmentRecommendationPanel 1 + ReservedCapacityOrchestratorPanel 1 + ReservedCapacityTrendMiniChart 1 + ko-KR SSOT 2 + finops reserved_capacity dashboard parity CR 12-5 D-PARITY-01 = ~+7 NEW vitest PASS)
- T8.4: 3중 게이트 FINAL CLEAN atomic commit via `git commit -F <file>` (CR 9-6 D5 prevention + PowerShell here-string 회피) 결정 wire

**Subtotal**: 8+8+6+4+4+2+4+4 = **~40 subtasks** 결정 wire (Phase 20 wire `52dad7f` 의 ~68 subtasks pattern 의 5-module composition layer version EXTENSION)

## Dev Notes 18종 (CR lessons applied)

- **CR 0-2 RLS** — 8 tables + 1 preview table 의 tenant-scoped RLS 자동 적용 (current_setting('app.tenant_id')::uuid) 보존
- **CR 1-1 audit-first INSERT 8 NEW** — ActionClass.FINOPS_RESERVED_CAPACITY_PLANNING 의 8 NEW audit actions (reserved_capacity_dashboard_viewed + demand_forecast_calculated + capacity_planning_recommended + commitment_recommendation_generated + reserved_capacity_dry_run_executed + reserved_capacity_kpi_refreshed + reserved_capacity_commitment_executed + reserved_capacity_orchestrator_triggered) 결정 wire 진입 시점에 audit-first INSERT 자동 활성화 보존
- **CR 1-1 FastAPI ContextVar** — tenant_id ContextVar middleware layer 보존 (CR 1-1 verbatim EXTENSION)
- **CR 1-1 RSC boundary** — Next.js 15.x RSC boundary 보존 (apps/web/app/[locale]/(dashboard)/admin/finops/reserved-capacity/{page,layout}.tsx)
- **CR 4-3/4-4** — async-test asyncio.run + Industry enum SSOT + A5 drift detector + golden_diff + SDR overclaim 방지
- **CR 9-6 commit message** — `git commit -F <file>` (D5 prevention) + PowerShell here-string 회피 결정 wire
- **CR 11-3 honest-DEFER 40번째** — D-FINOPS-10 honestly DEFER 보존 (Phase 21 territory 흡수 완료) + Phase 11~20 10-module FinOps territory chain ✅ ALL WIRED 결정 wire
- **ALLOWED_SERVICE_SUBMODULES 즉시 sweep** — Phase 21 wire 진입 시점에 `apps/api/modules/finops/__init__.py` 의 submodule 목록 즉시 sweep EXTENSION = m21_finops_reserved_capacity 신규 submodule 등록
- **CR 11-4 D-001~D-005** — ko-KR.json `finops_reserved_capacity.*` namespace EXTENSION ~30 keys SSOT + NFR18 ko-KR SSOT 보존
- **P-015 SSOT** — ko-KR.json finops_reserved_capacity.* 단일 SSOT 결정 wire
- **CR 12-1 L4** — industry-agnostic capability grants (4-industry ✅/✅/✅/✅) EXTENSION 결정 wire (Phase 20 wire 의 FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION 패턴 verbatim 미러)
- **CR 12-5 D-14 typed exception envelope 16 NEW** — Phase 21 wire 의 16 NEW typed exceptions (ReservedCapacityDemandForecastError + ReservedCapacityDemandForecastScopeError + ReservedCapacityDemandForecastPeriodError + ReservedCapacityDemandForecastModuleError + ReservedCapacityPlanningError + ReservedCapacityPlanningScopeError + ReservedCapacityPlanningTierError + ReservedCapacityPlanningGuardError + ReservedCapacityRecommendationError + ReservedCapacityRecommendationConfidenceError + ReservedCapacityRecommendationApprovalError + ReservedCapacityRecommendationExecutionError + ReservedCapacityOrchestratorError + ReservedCapacityOrchestratorStepError + ReservedCapacityDryRunError + ReservedCapacityIdempotencyError) CR 12-5 D-14 envelope 적용
- **CR 12-5 D-PARITY-01 inversion** — TypeScript mirror parity (reserved-capacity-types.ts + reserved-capacity-client.ts) 결정 wire
- **CR 12-5 D-GATE-01 inversion** — capability gate inversion (require_finops_reserved_capacity) 결정 wire
- **A19 cohesion 9 surface EXTENSION PASS** — FinOps Reserved Capacity Planning surface NEW 결정 wire 진입 후에도 9 surface 모두 PASS 보존
- **A36 SDR 검증 4-step** — 자동 적용 결정 wire (spec entry 진입 시점에 자동)
- **AD-14 stack pin** — Recharts 2.12.7 + reportlab 4.0.7 + openpyxl 3.1.2 + pandas 2.1.4 + xlsxwriter 3.1.9 + apscheduler 3.10.4 + pytz 2024.1 EXTENSION 결정 wire
- **AD-22 owner-only RBAC** — reserved_capacity dashboard UI 모두 owner-only RBAC EXTENSION (CommitmentRecommendationPanel + ReservedCapacityOrchestratorPanel + auto-execute enable 모두 owner-only)
- **Epic 12 2FA 챌린지 mandatory** — destructive endpoint 의 3-layer defense EXTENSION 결정 wire (high-value ≥ 10M KRW/year savings → owner approval flow + 2FA 챌린지)
- **NFR4 PII minimization** ✅ PRESERVED — Phase 21 wire 결정 wire 시에도 PII minimization 자동 보존
- **NFR18 ko-KR SSOT** — apps/web/messages/ko-KR.json finops_reserved_capacity.* namespace EXTENSION ~30 keys SSOT 보존 결정 wire
- **AD-47 + AD-48 + AD-49 신규** — AD-47 (a)~(g) 7 sub-decisions + AD-48 (a)~(c) 3 sub-decisions + AD-49 (a)~(g) 7 sub-decisions 모두 결정 wire 진입

## Architecture Alignment (ALLOWED sweep) — Phase 20 wire 정합

- **Backend (FastAPI, Python 3.12)**:
  - 4 NEW modules `apps/api/modules/finops/reserved_capacity/` (~+940 LOC: demand_forecast_aggregator + capacity_planning_aggregator + commitment_recommendation_engine + reserved_capacity_orchestrator)
  - 1 NEW serializers.py (~+100 LOC)
  - 1 NEW __init__.py submodule
  - 1 NEW alembic 0053 phase_21_reserved_capacity_planning.py (8 tables + RLS + 1 preview table)
  - 1 NEW scheduled_reserved_capacity_dispatch.py (~+150 LOC)
  - 1 NEW apps/api/scripts/cli/finops_reserved_capacity_dry_run.py (~+100 LOC)
  - MODIFIED apps/api/core/capability.py (Capability.FINOPS_RESERVED_CAPACITY_PLANNING)
  - MODIFIED apps/api/dependencies/capability.py (require_finops_reserved_capacity)
  - MODIFIED apps/api/core/audit_action.py (ActionClass.FINOPS_RESERVED_CAPACITY_PLANNING + FinopsReservedCapacityAction 8 NEW Literal)
  - MODIFIED apps/api/core/errors.py (16 NEW typed exception classes)
  - MODIFIED apps/api/modules/finops/__init__.py (ALLOWED_SERVICE_SUBMODULES EXTENSION)
- **Frontend (Next.js 15.x, TypeScript 5.x)**:
  - 2 NEW apps/web/app/[locale]/(dashboard)/admin/finops/reserved-capacity/{page,layout}.tsx (~+320 LOC)
  - 1 NEW apps/web/components/finops/FinopsReservedCapacityDashboardPanel.tsx (~+250 LOC)
  - 1 NEW apps/web/lib/finops/reserved-capacity-types.ts (4 NEW TypeScript interfaces)
  - 1 NEW apps/web/lib/finops/reserved-capacity-client.ts (4 NEW methods)
  - MODIFIED apps/web/messages/ko-KR.json (EXTENSION ~30 keys finops_reserved_capacity.* namespace)
- **Tests**:
  - ~+108 NEW pytest PASS (demand_forecast_aggregator 24 + capacity_planning_aggregator 30 + commitment_recommendation_engine 24 + reserved_capacity_orchestrator 30)
  - ~+7 NEW vitest PASS (DemandForecastPanel 1 + CapacityPlanningPanel 1 + CommitmentRecommendationPanel 1 + ReservedCapacityOrchestratorPanel 1 + ReservedCapacityTrendMiniChart 1 + ko-KR SSOT 2 + finops reserved_capacity dashboard parity)
  - 0 NEW ruff + 0 NEW tsc + 0 regressions
- **Docs (cumulative; wire sprint will write)**:
  - Spec file (this file) NEW ~+440 LOC
  - Handoff memory NEW
  - Commit-msg NEW
  - Sprint-status MODIFIED v3.59 → v3.60
  - MEMORY.md MODIFIED hook EXTENSION

## Files Affected (estimate ~25 files = 21 NEW + 4 MODIFIED, **wire sprint scope**) — **spec entry sprint 5 files = 3 NEW + 2 MODIFIED**

### Spec entry sprint (cj 150, this sprint) — 5 files = 3 NEW + 2 MODIFIED
1. NEW: `_bmad-output/implementation-artifacts/phase-21-finops-reserved-capacity-planning-wire.md` (this file, ~+440 LOC)
2. NEW: `memory/handoff-2026-08-26-phase-21-spec-entry-done.md`
3. NEW: `_bmad-output/implementation-artifacts/commit-msg-phase-21-spec-entry.txt`
4. MODIFIED: `_bmad-output/implementation-artifacts/sprint-status.yaml` (v3.59 → v3.60 EXTENSION)
5. MODIFIED: `memory/MEMORY.md` (Phase 21 spec entry hook EXTENSION)

### Wire sprint (cj 151, future) — estimated ~25 files = 21 NEW + 4 MODIFIED (Phase 20 wire `52dad7f` 의 ~30-35 files pattern 의 5-module composition layer version EXTENSION)
- Backend: 4 NEW modules (~+940 LOC) + 1 NEW serializers.py + 1 NEW __init__.py + 1 NEW alembic 0053 + 1 NEW scheduled_dispatch + 1 NEW scripts/cli (~+1,340 LOC)
- Frontend: 2 NEW RSC pages (~+320 LOC) + 1 NEW Client component (~+250 LOC) + 2 NEW TS mirrors (~+100 LOC)
- Tests: ~+108 NEW pytest PASS + ~+7 NEW vitest PASS
- MODIFIED: 4 files (capability.py + dependencies/capability.py + audit_action.py + errors.py + modules/finops/__init__.py + ko-KR.json = 6 MODIFIED actually, but estimates vary)

(Actual wire sprint file count will be verified at wire time via `git show --stat HEAD`.)

## 3중 게이트 impact

- **cj 150 (this sprint, docs-only)**: ruff 0 NEW / pytest 0 NEW / vitest 0 NEW / tsc 0 NEW (apps/api backend unchanged, apps/web frontend unchanged)
- **cj 151 (wire sprint)**: ruff scoped 0 NEW / pytest ~+108 NEW PASS / vitest ~+7 NEW PASS / tsc 0 NEW
- **cj 152 (retro sprint, docs-only)**: ruff 0 NEW / pytest 0 NEW / vitest 0 NEW / tsc 0 NEW

## A579~A583 5 NEW 결정 wire (cj-style 150번째)

- **A579**: 옵션 (a) Phase 21 spec entry 진입 결정 wire (rationale 5종: ① cj-style discipline 회피 위험 방지 = 149번째 Phase 21 PRD entry 진입 직후 자연스러운 spec entry 진입 결정 wire ② Phase 21 PRD entry cj-style 149번째 진입 직후 자연스러운 spec entry 진입 = 150번째 진입 결정 wire ③ Phase 11~20 10-module FinOps territory chain ✅ ALL WIRED 진입 정합 보존 + Phase 17/18/19/20 4-module chain ✅ ALL WIRED ④ 5-module composition layer = reuse 최대화 + risk 최소화 + 비즈니스 가치 최고 ⑤ Epic 1 ~ Epic 17 + Phase 3 ~ Phase 20.5 + 1st release cycle 정합 보존)
- **A580**: spec 파일 생성 결정 wire (`_bmad-output/implementation-artifacts/phase-21-finops-reserved-capacity-planning-wire.md` ~+440 LOC + baseline_commit `563ac9c` + cj_style_entry_point 150 + status `ready-for-dev` + Story + 8 ACs §F37.1~§F37.8 verbatim → 86 detailed sub-ACs (12+12+12+12+12+12+4+10) pre-flight 정합 sweep 만족 + T1~T8 + ~40 subtasks + Dev Notes 18종 + Architecture Alignment ALLOWED sweep + Files Affected ~25 files estimate (~21 NEW + ~4 MODIFIED))
- **A581**: 8 ACs §F37.1~§F37.8 verbatim → 86 sub-ACs 전개 결정 wire (§F37.1 demand_forecast_aggregator 12 sub-ACs + §F37.2 capacity_planning_aggregator 12 sub-ACs + §F37.3 commitment_recommendation_engine 12 sub-ACs + §F37.4 reserved_capacity_orchestrator 12 sub-ACs + §F37.5 reserved_capacity dashboard UI 12 sub-ACs + §F37.6 Capability matrix v1.47 EXTENSION 12 sub-ACs + §F37.7 audit action EXTENSION 8 NEW + 16 NEW typed exception classes 4 sub-ACs + §F37.8 dry-run + Tests + wire scope T1~T8 10 sub-ACs = 86 sub-ACs pre-flight 정합 sweep 만족)
- **A582**: Tasks T1~T8 + ~40 subtasks 결정 wire (T1 4 backend aggregators 8 subtasks + T2 dashboard UI 5 sub-components 8 subtasks + T3 alembic 0053 8 tables 6 subtasks + T4 audit action EXTENSION 8 NEW + 16 NEW typed exception classes 4 subtasks + T5 capability v1.47 EXTENSION 4 subtasks + T6 scheduled_dispatch_job wire 2 subtasks + T7 dry-run mode + 1 NEW CLI flag 4 subtasks + T8 3중 게이트 FINAL CLEAN atomic commit 4 subtasks = ~40 subtasks)
- **A583**: sprint-status v3.59 → v3.60 EXTENSION + atomic commit via `git commit -F <file>` CR 9-6 D5 prevention + commit-msg-phase-21-spec-entry.txt 신규 + handoff memory 신규 + MEMORY.md hook EXTENSION + **5 files = 3 NEW + 2 MODIFIED atomic single sprint** 결정 wire (1 NEW spec file + 1 NEW handoff memory + 1 NEW commit-msg = 3 NEW; 1 MODIFIED sprint-status; 1 MODIFIED MEMORY.md) 진입 완료 보존.

## CR lessons applied 18종

CR 0-2 RLS 8 tables + CR 1-1 audit-first INSERT 8 NEW + CR 1-1 FastAPI ContextVar + CR 1-1 RSC boundary + CR 4-3/4-4 + CR 9-6 commit message `git commit -F <file>` + CR 11-3 honest-DEFER 40번째 D-FINOPS-10 honestly DEFER 보존 + Phase 11~20 10-module FinOps territory chain ✅ ALL WIRED 결정 wire + ALLOWED_SERVICE_SUBMODULES 즉시 sweep EXTENSION = m21_finops_reserved_capacity 신규 submodule 등록 + CR 11-4 D-001~D-005 + P-015 SSOT + CR 12-1 L4 industry-agnostic capability matrix v1.47 FINOPS_RESERVED_CAPACITY_PLANNING 4-industry grants ✅/✅/✅/✅ + CR 12-5 D-14 typed exception envelope 16 NEW + CR 12-5 D-PARITY-01 inversion TypeScript mirror parity finops_reserved_capacity.* namespace + CR 12-5 D-GATE-01 inversion capability gate inversion require_finops_reserved_capacity + A19 cohesion 9 surface EXTENSION PASS + A36 SDR 검증 4-step 자동 적용 + AD-14 stack pin Recharts 2.12.7 + reportlab 4.0.7 + openpyxl 3.1.2 + pandas 2.1.4 + xlsxwriter 3.1.9 + apscheduler 3.10.4 + pytz 2024.1 + AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory + NFR4 PII minimization ✅ PRESERVED + AD-47 (a)~(g) 7 sub-decisions + AD-48 (a)~(c) 3 sub-decisions + AD-49 (a)~(g) 7 sub-decisions + NFR18 ko-KR SSOT

## D-DEFER-* honestly 결정 wire 보존

- D-1-1-DEFER-1/2/3 + D-EPIC-16-REVIEW-DEFER-1/2~6 + D-PHASE-4-DR-DEFER-1/2 + D-EPIC-17-WIRE-DEFER-T2-T3-UI + D-RETENTION-1 + D-OBSERVABILITY-1 + D-PERFORMANCE-1 + D-CHAOS-1 + D-SLO-1 + D-FINOPS-1~9 모두 ✅ ALL RESOLVED 보존
- **D-FINOPS-10 신규 honestly DEFER 보존** — Phase 21 PRD entry 진입 시점에 carry-over chain 정직 회복 결정 wire 진입 = 5-module composition layer 의 backend detail + reserved_capacity_tier selection algorithm detail + commitment_recommendation confidence + risk scoring detail + reserved_capacity_orchestrator composition_step_chain 5 step detail — 모두 단일 sprint `wire` 진입이 아닌 docs-only entry 에서 honestly defer 결정 wire 보존
- **Phase 21 spec entry = D-FINOPS-10 의 carry-over chain 정직 회복 verification** 결정 wire (CR 11-3 honest-DEFER 40번째 epic 연속 정직 회복)

## Epic 1~17 + Phase 3~20 + Phase 19.5 + Phase 20.5 + 1st release cycle 정합 보존

cj-style 150번째 epic 연속 정직 회복 진입 시점에 pre-flight 정합 sweep 만족 결정 wire 보존:
- Phase 21 PRD entry `563ac9c` (cj-style 149번째) DONE 진입 정합 보존
- Phase 20.5 close-out retro `8505d98` (cj-style 148번째) DONE 진입 정합 보존
- Phase 20.5 atomic wire `46ddcc5` (cj-style 147번째) DONE 진입 정합 보존
- Phase 20.5 spec entry `e23141d` (cj-style 146번째) DONE 진입 정합 보존
- Phase 20 close-out retro `f361016` (cj-style 145번째) DONE 진입 정합 보존
- Phase 20 atomic wire `52dad7f` (cj-style 144번째) DONE 진입 정합 보존
- Phase 20 spec entry `efc3c59` (cj-style 143번째) DONE 진입 정합 보존
- Phase 20 PRD entry `eacb0a5` (cj-style 142번째) DONE 진입 정합 보존
- Phase 19.5 carry-over 결정 wire `b2fb1d8` (cj-style 141번째) DONE 진입 정합 보존
- Phase 19 close-out retro `18ca1ae` (cj-style 140번째) + Phase 19 atomic wire `8db3cfc` (cj-style 139번째) + Phase 19 spec entry `59d15fb` (cj-style 138번째) + Phase 19 PRD entry `ff8a797` (cj-style 137번째) DONE 진입 정합 보존
- Phase 11~20 10-module FinOps territory chain ✅ ALL WIRED 진입 정합 보존 + Phase 11~19 9-module FinOps territory chain ✅ ALL WIRED 진입 정합 보존
- Epic 1~17 ALL DONE 진입 정합 보존
- 1st release cycle ALL DONE 진입 정합 보존

## 결정 wire 일자 + next

- 결정 wire 일자: 2026-08-26 (KST)
- next 옵션:
  - (a) Phase 21 atomic wire T1~T8 진입 결정 wire (cj-style 151번째) — 4 NEW backend aggregators + 5 NEW dashboard sub-components + alembic 0053 8 tables + audit action 8 NEW + 16 NEW typed exceptions + capability v1.47 + scheduled dispatch + dry-run + 1 CLI flag = ~25 files atomic single sprint
  - (b) Phase 21 close-out retro 진입 결정 wire (cj-style 152번째) — 14-section §1~§14 verbatim retro document
  - (c) Epic 21+ 진입 결정 wire
  - (d) D-DEFER-* follow-up 결정 wire 보류
