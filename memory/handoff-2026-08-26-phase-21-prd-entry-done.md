---
name: handoff-2026-08-26-phase-21-prd-entry-done
description: Phase 21 PRD entry DONE (cj-style 149번째). FinOps Reserved Capacity Planning territory 결정 wire 진입. 6 files atomic docs-only sprint. master PRD v6.0 → v7.0 + capability matrix v1.46 → v1.47.
metadata:
  type: project
---

# Phase 21 PRD entry DONE — cj-style 149번째

## 결정 wire 요약

Phase 21 (FinOps Reserved Capacity Planning territory) PRD entry 진입 완료. cj-style 149번째 epic 연속 정직 회복. master PRD v6.0 → v7.0 atomic edit. Capability matrix v1.46 → v1.47 EXTENSION FINOPS_RESERVED_CAPACITY_PLANNING.

- **cj-style 진입점**: 149번째
- **결정 wire 일자**: 2026-08-26 (KST)
- **territory**: FinOps Reserved Capacity Planning
- **선택 이유 (process-design 관점)**: 5 FinOps modules (Phase 13 forecast + Phase 14 optimization + Phase 18 commitment + Phase 19 pricing + Phase 20 multi_cloud) 의 natural composition layer. 새로운 backend infra 불필요, reuse 최대화, risk 최소화, 비즈니스 가치 최고
- **files**: 6 files atomic single sprint = **2 NEW + 4 MODIFIED**
  - 1 MODIFIED master PRD v6.0 → v7.0 (`_bmad-output/planning-artifacts/prd.md`)
  - 1 MODIFIED capability matrix v1.46 → v1.47 (`docs/capability-matrix.md`)
  - 1 MODIFIED sprint-status v3.58 → v3.59 (`_bmad-output/implementation-artifacts/sprint-status.yaml`)
  - 1 MODIFIED MEMORY.md hook EXTENSION (`memory/MEMORY.md`)
  - 1 NEW handoff memory (this file)
  - 1 NEW commit-msg (`_bmad-output/implementation-artifacts/commit-msg-phase-21-prd-entry.txt`)

## Phase 21 territory 결정

### §F37.1~§F37.8 8 ACs verbatim

1. **§F37.1 demand_forecast_aggregator** (`apps/api/modules/finops/reserved_capacity/demand_forecast_aggregator.py` NEW ~+220 LOC + `aggregate_demand_forecast(tenant_id, period_key, scope_chain) -> ReservedCapacityDemandForecast` TypedDict 16 fields + 5-module cross-join EXTENSION (Phase 13 + 14 + 18 + 19 + 20) + confidence interval (low/high/width → volatile + growth + declining + stable) + seasonal_factor + growth_rate_pct 4 industries baseline + audit-first INSERT `demand_forecast_calculated`)

2. **§F37.2 capacity_planning_aggregator** (`apps/api/modules/finops/reserved_capacity/capacity_planning_aggregator.py` NEW ~+220 LOC + `plan_reserved_capacity` TypedDict 18 fields + 6 reserved_capacity_tier enum + break_even_utilization_pct + capacity_headroom_pct 10~20% + MINIMUM_SAVINGS_PCT=5.0 + MINIMUM_SAVINGS_KRW=1M + audit-first INSERT `capacity_planning_recommended`)

3. **§F37.3 commitment_recommendation_engine** (`apps/api/modules/finops/reserved_capacity/commitment_recommendation_engine.py` NEW ~+250 LOC + `generate_commitment_recommendation` TypedDict 17 fields + confidence_score + risk_score + execution_strategy 4 enum + high-value (≥ 10M KRW/year) → Epic 12 2FA 챌린지 + owner approval flow + audit-first INSERT `commitment_recommendation_generated`)

4. **§F37.4 reserved_capacity_orchestrator** (`apps/api/modules/finops/reserved_capacity/reserved_capacity_orchestrator.py` NEW ~+250 LOC + `orchestrate_reserved_capacity` TypedDict 19 fields + composition_step_chain 5 step (demand_forecast → capacity_planning → commitment_recommendation → execute) + 4 cadence schedule (daily + weekly + monthly + quarterly KST pytz) + dry-run mode + 1 NEW CLI flag + audit-first INSERT `reserved_capacity_orchestrator_triggered`)

5. **§F37.5 reserved_capacity dashboard UI** (`apps/web/app/[locale]/(dashboard)/admin/finops/reserved-capacity/page.tsx` NEW ~+220 LOC + 5 sub-components + `apps/web/components/finops/FinopsReservedCapacityDashboardPanel.tsx` NEW Client component ~+250 LOC + 5-tab layout + Recharts 2.12.7 AD-14 stack pin + owner-only RBAC AD-22 + Epic 12 2FA 챌린지 + ko-KR.json `finops_reserved_capacity.*` namespace EXTENSION ~30 keys)

6. **§F37.6 Capability matrix v1.47 EXTENSION FINOPS_RESERVED_CAPACITY_PLANNING** (`apps/api/core/capability.py` MODIFIED + `apps/api/dependencies/capability.py` MODIFIED require_finops_reserved_capacity + drift detector `tests/integration/test_capability_matrix_v1_47_drift.py` NEW 8 NEW pytest cases + ALLOWED_SERVICE_SUBMODULES 즉시 sweep EXTENSION = m21_finops_reserved_capacity 신규 submodule 등록)

7. **§F37.7 audit action EXTENSION 8 NEW** (reserved_capacity_dashboard_viewed + demand_forecast_calculated + capacity_planning_recommended + commitment_recommendation_generated + reserved_capacity_dry_run_executed + reserved_capacity_kpi_refreshed + reserved_capacity_commitment_executed + reserved_capacity_orchestrator_triggered) + 16 NEW typed exception classes (CR 12-5 D-14 envelope)

8. **§F37.8 dry-run + Tests + wire scope T1~T8** (~+108 NEW pytest PASS + ~+7 NEW vitest PASS + 0 NEW ruff + 0 regressions + T1 4 backend aggregators + T2 dashboard 5 sub-components + T3 alembic 0053 8 tables + RLS 8 tables + 1 preview table + T4 audit action EXTENSION 8 NEW + 16 NEW typed exception classes + T5 capability v1.47 EXTENSION + T6 scheduled_dispatch_job wire + T7 dry-run mode + 1 NEW CLI flag + T8 3중 게이트 FINAL CLEAN atomic commit)

## AD-49 신규 결정 (a)~(g) 7 sub-decisions

(a) demand_forecast_aggregator 의 5-module cross-join backend detail 결정 wire — 5 FinOps modules 의 가중 평균 → single forecasted_demand_krw + confidence interval
(b) capacity_planning_aggregator 의 reserved_capacity_tier selection algorithm detail 결정 wire — 6 reserved_capacity_tier (1y/3y × no/partial/all upfront) + break_even_utilization_pct + capacity_headroom_pct
(c) commitment_recommendation_engine 의 confidence + risk scoring detail 결정 wire — confidence_score (utilization_stability × 0.4 + historical_accuracy × 0.3 + demand_forecast_confidence_pct × 0.3) + risk_score (savings_pct × 0.4 + commitment_term × 0.3 + commitment_flexibility × 0.3)
(d) reserved_capacity_orchestrator 의 composition_step_chain 5 step detail 결정 wire — demand_forecast → capacity_planning → commitment_recommendation → approval → execute
(e) 4 cadence schedule KST pytz detail 결정 wire — daily 02:00 + weekly Mon 03:00 + monthly 1st-day 04:00 + quarterly 1st-day 05:00 KST pytz timezone('Asia/Seoul')
(f) LISTEN/NOTIFY 4 channel cross-tenant invalidation pattern EXTENSION 결정 wire — phase_21_demand_forecast_calculated + phase_21_capacity_planning_recommended + phase_21_commitment_recommendation_generated + phase_21_reserved_capacity_orchestrated
(g) owner approval flow high-value threshold detail 결정 wire — ≥ 10M KRW/year savings → Epic 12 2FA 챌린지 mandatory + Slack DM + 2FA + approval_chain

## D-FINOPS-10 honestly DEFER 보존

Phase 21 PRD entry 진입 시점에 carry-over chain 정직 회복 결정 wire 진입 = 5-module composition layer 의 backend detail + reserved_capacity_tier selection algorithm detail + commitment_recommendation confidence + risk scoring detail + reserved_capacity_orchestrator composition_step_chain 5 step detail — 모두 단일 sprint `wire` 진입이 아닌 docs-only entry 에서 honestly defer 결정 wire 보존.

## Phase 21 carry-over chain (cj-style 1~4번째 진입점 결정 보존)

(1) cj-style Phase 21 1번째 진입점 = Phase 21 PRD entry (cj-style 149번째): ✅ DONE 2026-08-26
(2) cj-style Phase 21 2번째 진입점 = Phase 21 spec (cj-style 150번째): 진입 대기
(3) cj-style Phase 21 3번째 진입점 = Phase 21 atomic wire T1~T8 (cj-style 151번째): 진입 대기
(4) cj-style Phase 21 4번째 진입점 = Phase 21 close-out retro (cj-style 152번째): 진입 대기

## Pre-flight 정합 sweep (cj-style 149번째 진입 시점)

- Epic 1 ~ Epic 17 + Phase 3 ~ Phase 20 + Phase 19.5 + Phase 20.5 + 1st release cycle 정합 보존
- Phase 17/18/19/20 4-module FinOps territory chain ✅ ALL WIRED (Phase 20.5 wire 진입 후)
- Phase 11/12/13/14/15/16 6-module FinOps territory chain ✅ ALL WIRED (Phase 11~16 wire cycles)
- Capability matrix v1.47 EXTENSION FINOPS_RESERVED_CAPACITY_PLANNING 보존
- AD-47 + AD-48 + AD-49 신규 결정 chain 정합
- CR lessons applied 18종 (CR 0-2 + CR 1-1 + CR 4-3/4-4 + CR 9-6 + CR 11-3 + CR 11-4 + CR 12-1 + CR 12-5 D-14 + CR 12-5 D-PARITY-01 + CR 12-5 D-GATE-01 + A19 + A36 + AD-14 + AD-22 + AD-49 + NFR4 + NFR18)
- 3중 게이트 impact NONE (docs only 변경)
- 1-day atomic sprint discipline 결정 wire

## 결정 wire 일자: 2026-08-26 (KST)

next: 옵션 (a) Phase 21 spec entry 진입 결정 wire (cj-style 150번째) / 옵션 (b) Phase 21 atomic wire T1~T8 진입 결정 wire (cj-style 151번째) / 옵션 (c) Phase 21 close-out retro 진입 결정 wire (cj-style 152번째) / 옵션 (d) Epic 21+ 진입 결정 wire / 옵션 (e) D-DEFER-* follow-up 결정 wire 보류.