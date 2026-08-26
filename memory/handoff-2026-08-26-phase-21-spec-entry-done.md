---
name: handoff-2026-08-26-phase-21-spec-entry-done
description: Phase 21 spec entry DONE (cj-style 150번째 epic 연속 정직 회복 atomic docs-only wire). FinOps Reserved Capacity Planning territory 결정 wire 진입. 5 files = 3 NEW + 2 MODIFIED atomic docs-only sprint.
metadata:
  type: project
---

# Phase 21 spec entry DONE — cj-style 150번째

## 결정 wire 요약

Phase 21 (FinOps Reserved Capacity Planning territory) spec entry 진입 완료. cj-style 150번째 epic 연속 정직 회복. 8 ACs §F37.1~§F37.8 verbatim → 86 detailed sub-ACs (12+12+12+12+12+12+4+10) pre-flight 정합 sweep 만족 결정 wire. T1~T8 + ~40 subtasks. AD-49 신규 (a)~(g) 7 sub-decisions 보존.

- **cj-style 진입점**: 150번째
- **결정 wire 일자**: 2026-08-26 (KST)
- **territory**: FinOps Reserved Capacity Planning
- **선택 이유 (process-design 관점)**: Phase 21 PRD entry `563ac9c` (cj-style 149번째) 진입 직후 자연스러운 spec entry 진입 = cj-style 4-entry-point cycle PRD entry → spec entry → wire → close-out retro 의 2번째 단계 진입 결정 wire (Phase 17 spec entry cj-style 130번째 + Phase 18 spec entry cj-style 134번째 + Phase 19 spec entry cj-style 138번째 + Phase 20 spec entry cj-style 143번째 패턴 verbatim 미러)
- **files**: 5 files atomic single sprint = **3 NEW + 2 MODIFIED**
  - 1 NEW spec file `_bmad-output/implementation-artifacts/phase-21-finops-reserved-capacity-planning-wire.md` (~+440 LOC)
  - 1 NEW handoff memory (this file)
  - 1 NEW commit-msg (`_bmad-output/implementation-artifacts/commit-msg-phase-21-spec-entry.txt`)
  - 1 MODIFIED sprint-status v3.59 → v3.60 (`_bmad-output/implementation-artifacts/sprint-status.yaml`)
  - 1 MODIFIED MEMORY.md hook EXTENSION (`memory/MEMORY.md`)

## Phase 21 territory 결정 (8 ACs §F37.1~§F37.8 → 86 sub-ACs)

### 8 ACs verbatim
1. **§F37.1 demand_forecast_aggregator** — 5-module cross-join + ReservedCapacityDemandForecast TypedDict 16 fields + confidence interval + seasonal_factor + growth_rate_pct 4 industries baseline + audit-first INSERT `demand_forecast_calculated` (12 sub-ACs)
2. **§F37.2 capacity_planning_aggregator** — 6 reserved_capacity_tier enum + break_even_utilization_pct + capacity_headroom_pct 10~20% + MINIMUM_SAVINGS_PCT=5.0 + MINIMUM_SAVINGS_KRW=1M + audit-first INSERT `capacity_planning_recommended` (12 sub-ACs)
3. **§F37.3 commitment_recommendation_engine** — confidence_score + risk_score + execution_strategy 4 enum + owner approval flow high-value (≥ 10M KRW/year) → Epic 12 2FA 챌린지 + audit-first INSERT `commitment_recommendation_generated` (12 sub-ACs)
4. **§F37.4 reserved_capacity_orchestrator** — composition_step_chain 5 step + 4 cadence schedule (daily 02:00 + weekly Mon 03:00 + monthly 1st-day 04:00 + quarterly 1st-day 05:00 KST pytz) + dry-run + 1 NEW CLI flag + audit-first INSERT `reserved_capacity_orchestrator_triggered` (12 sub-ACs)
5. **§F37.5 reserved_capacity dashboard UI** — 5 sub-components (DemandForecastPanel + CapacityPlanningPanel + CommitmentRecommendationPanel + ReservedCapacityOrchestratorPanel + ReservedCapacityTrendMiniChart) + FinopsReservedCapacityDashboardPanel.tsx Client component ~+250 LOC + 5-tab layout + Recharts 2.12.7 AD-14 stack pin + ko-KR.json EXTENSION ~30 keys (12 sub-ACs)
6. **§F37.6 Capability matrix v1.47 EXTENSION FINOPS_RESERVED_CAPACITY_PLANNING** — Capability.FINOPS_RESERVED_CAPACITY_PLANNING 1 NEW enum + require_finops_reserved_capacity 1 NEW dep + ActionClass.FINOPS_RESERVED_CAPACITY_PLANNING + FinopsReservedCapacityAction 8 NEW Literal + 16 NEW typed exception classes (CR 12-5 D-14 envelope) + alembic 0053 8 tables + RLS 8 tables + 1 preview table + drift detector (12 sub-ACs)
7. **§F37.7 audit action EXTENSION 8 NEW + 16 NEW typed exception classes** — (reserved_capacity_dashboard_viewed + demand_forecast_calculated + capacity_planning_recommended + commitment_recommendation_generated + reserved_capacity_dry_run_executed + reserved_capacity_kpi_refreshed + reserved_capacity_commitment_executed + reserved_capacity_orchestrator_triggered) + 16 NEW typed exception classes (CR 12-5 D-14 envelope) (4 sub-ACs)
8. **§F37.8 dry-run + Tests + wire scope T1~T8** — 1 NEW CLI flag + phase_21_orchestration_preview 1 table + ~+108 NEW pytest PASS + ~+7 NEW vitest PASS + 0 NEW ruff + 0 regressions + wire scope T1~T8 (10 sub-ACs)

**Total**: 12+12+12+12+12+12+4+10 = **86 sub-ACs** pre-flight 정합 sweep 만족 결정 wire.

## AD-49 신규 결정 (a)~(g) 7 sub-decisions 보존

(a) demand_forecast_aggregator 의 5-module cross-join backend detail — 5 FinOps modules 의 가중 평균 → single forecasted_demand_krw + confidence interval
(b) capacity_planning_aggregator 의 reserved_capacity_tier selection algorithm detail — 6 reserved_capacity_tier (1y/3y × no/partial/all upfront) + break_even_utilization_pct + capacity_headroom_pct
(c) commitment_recommendation_engine 의 confidence + risk scoring detail — confidence_score (utilization_stability × 0.4 + historical_accuracy × 0.3 + demand_forecast_confidence_pct × 0.3) + risk_score (savings_pct × 0.4 + commitment_term × 0.3 + commitment_flexibility × 0.3)
(d) reserved_capacity_orchestrator 의 composition_step_chain 5 step detail — demand_forecast → capacity_planning → commitment_recommendation → approval → execute
(e) 4 cadence schedule KST pytz detail — daily 02:00 + weekly Mon 03:00 + monthly 1st-day 04:00 + quarterly 1st-day 05:00 KST pytz timezone('Asia/Seoul')
(f) LISTEN/NOTIFY 4 channel cross-tenant invalidation pattern EXTENSION — phase_21_demand_forecast_calculated + phase_21_capacity_planning_recommended + phase_21_commitment_recommendation_generated + phase_21_reserved_capacity_orchestrated
(g) owner approval flow high-value threshold detail — ≥ 10M KRW/year savings → Epic 12 2FA 챌린지 mandatory + Slack DM + 2FA + approval_chain

## D-FINOPS-10 honestly DEFER 보존

Phase 21 PRD entry 진입 시점에 carry-over chain 정직 회복 결정 wire 진입 = 5-module composition layer 의 backend detail + reserved_capacity_tier selection algorithm detail + commitment_recommendation confidence + risk scoring detail + reserved_capacity_orchestrator composition_step_chain 5 step detail — 모두 단일 sprint `wire` 진입이 아닌 docs-only entry 에서 honestly defer 결정 wire 보존. Phase 21 spec entry 진입 시점에 carry-over chain 정직 회복 verification 결정 wire 진입 (CR 11-3 honest-DEFER 40번째 epic 연속 정직 회복).

## Phase 21 carry-over chain (cj-style 1~4번째 진입점 결정 보존)

(1) cj-style Phase 21 1번째 진입점 = Phase 21 PRD entry (cj-style 149번째): ✅ DONE 2026-08-26 (`563ac9c`)
(2) cj-style Phase 21 2번째 진입점 = Phase 21 spec (cj-style 150번째): ✅ DONE 2026-08-26 (this sprint)
(3) cj-style Phase 21 3번째 진입점 = Phase 21 atomic wire T1~T8 (cj-style 151번째): 진입 대기
(4) cj-style Phase 21 4번째 진입점 = Phase 21 close-out retro (cj-style 152번째): 진입 대기

## Files Affected (wire sprint estimate, cj 151)

estimated ~25 files atomic single sprint = ~21 NEW + ~4 MODIFIED (Phase 20 wire `52dad7f` 의 ~30-35 files pattern 의 5-module composition layer version EXTENSION):
- Backend: 4 NEW modules (~+940 LOC: demand_forecast_aggregator + capacity_planning_aggregator + commitment_recommendation_engine + reserved_capacity_orchestrator) + 1 NEW serializers.py + 1 NEW __init__.py + 1 NEW alembic 0053 (8 tables + RLS + 1 preview table) + 1 NEW scheduled_dispatch + 1 NEW scripts/cli (~+1,340 LOC)
- Frontend: 2 NEW RSC pages (~+320 LOC) + 1 NEW Client component (~+250 LOC) + 2 NEW TS mirrors (~+100 LOC)
- Tests: ~+108 NEW pytest PASS + ~+7 NEW vitest PASS
- MODIFIED: capability.py + dependencies/capability.py + audit_action.py + errors.py + modules/finops/__init__.py + ko-KR.json

## Pre-flight 정합 sweep (cj-style 150번째 진입 시점)

- Epic 1 ~ Epic 17 + Phase 3 ~ Phase 20 + Phase 19.5 + Phase 20.5 + 1st release cycle 정합 보존
- Phase 11~20 10-module FinOps territory chain ✅ ALL WIRED 진입 정합 보존
- Phase 17/18/19/20 4-module FinOps territory chain ✅ ALL WIRED (Phase 20.5 wire 진입 후) 진입 정합 보존
- Phase 11~19 9-module FinOps territory chain ✅ ALL WIRED 진입 정합 보존
- Capability matrix v1.47 EXTENSION FINOPS_RESERVED_CAPACITY_PLANNING 보존
- AD-47 + AD-48 + AD-49 신규 결정 chain 정합
- CR lessons applied 18종 (CR 0-2 + CR 1-1 + CR 4-3/4-4 + CR 9-6 + CR 11-3 + CR 11-4 + CR 12-1 + CR 12-5 D-14 + CR 12-5 D-PARITY-01 + CR 12-5 D-GATE-01 + A19 + A36 + AD-14 + AD-22 + AD-49 + NFR4 + NFR18)
- 3중 게이트 impact NONE (docs only 변경)
- 1-day atomic sprint discipline 결정 wire

## 결정 wire 일자: 2026-08-26 (KST)

next: 옵션 (a) Phase 21 atomic wire T1~T8 진입 결정 wire (cj-style 151번째) / 옵션 (b) Phase 21 close-out retro 진입 결정 wire (cj-style 152번째) / 옵션 (c) Epic 21+ 진입 결정 wire / 옵션 (d) D-DEFER-* follow-up 결정 wire 보류.
