---
name: handoff-2026-08-25-phase-17-spec-entry-done
description: Phase 17 spec entry DONE (cj-style 130번째 = Phase 17 2번째 진입점). FinOps Sustainability & Carbon Reporting territory 결정 wire. 5 files atomic single sprint.
metadata:
  type: project
---

# Handoff: Phase 17 Spec Entry DONE

**Date**: 2026-08-25 (KST)
**cj-style sequence**: 130번째 epic 연속 정직 회복 (Phase 17 2번째 진입점)
**Phase territory**: FinOps Sustainability & Carbon Reporting
**Capability**: FINOPS_SUSTAINABILITY (신규) + 4-industry grants ✅/✅/✅/✅ industry-agnostic
**Baseline commit**: `e0778ed` (Phase 17 PRD entry = cj-style 129th tip)
**Spec file**: `_bmad-output/implementation-artifacts/phase-17-finops-sustainability-carbon-reporting-wire.md` (NEW ~+440 LOC)

---

## 1. 결정 wire 요약 (5 결정)

### 결정 1: Phase 17 spec entry 진입 + territory 선정
- 옵션 (a) Phase 17 spec entry 진입 결정 wire (cj-style 130번째)
- 옵션 (a) FinOps Sustainability & Carbon Reporting (Recommended) territory 결정 wire
- rationale 5종: ① cj-style discipline 회피 위험 방지 (129번째 Phase 17 PRD entry 진입 직후 자연스러운 spec entry 진입 = Phase 16 PRD entry 진입 후 spec entry 진입 패턴 verbatim 미러) ② FinOps Sustainability & Carbon Reporting territory 결정 wire = Phase 16 close-out retro 의 FinOps Reporting & Executive Dashboard territory 의 natural SUSTAINABILITY & CARBON REPORTING LAYER EXTENSION (6 FinOps modules + sustainability cross-rollup view + scope 1/2/3 emissions + carbon offset accounting via VCU + CER + KCU registries + renewable energy + data center PUE + carbon intensity kgCO2e/KRW + scheduled sustainability report dispatch PDF + CSV + Excel monthly/quarterly/annual EXTENSION 정직 회복 chain) + EU CSRD + SEC Climate Disclosure + EU Taxonomy + IFRS S2 + 한국 KSSB regulatory driver EXTENSION chain 정직 회복 + Phase 16 wire 의 executive reporting + Phase 15 wire `1b800d9` 의 tag_governance + Phase 14 wire `e904485` 의 optimization + Phase 13 wire `8b98030` 의 forecast + Phase 12 wire `f3c0e63` 의 anomaly + Phase 11 wire `e020ad0` 의 showback territory 의 자연스러운 carry-over chain (cost ⇒ carbon emissions ⇒ carbon intensity ⇒ renewable energy ⇒ PUE ⇒ carbon offset) ③ Epic 1 ~ Epic 17 + Phase 3 ~ Phase 16 + 1st release cycle 모두 wire DONE 정합 보존 ④ Phase 17 spec 8 ACs PRD §F33.1~§F33.8 verbatim → 86 sub-ACs + T1~T8 + 68 subtasks + Dev Notes 17종 + Architecture Alignment cj-style ALLOWED sweep 결정 wire 보존 ⑤ AD-22 owner-only RBAC + Epic 12 2FA 챌린지 보존 + AD-14 stack pin + NFR4 PII minimization ✅ PRESERVED

### 결정 2: spec 파일 생성 결정 wire
- phase-17-finops-sustainability-carbon-reporting-wire.md ~+440 LOC
- baseline_commit `e0778ed` (Phase 17 PRD entry)
- status `ready-for-dev`
- cj_style_entry_point 130
- Story: FinOps Sustainability & Carbon Reporting territory implementation spec
- 8 ACs §F33.1~§F33.8 verbatim → 86 detailed sub-ACs (11+11+11+11+11+10+12+10)
- T1~T8 + 68 subtasks (T1 10 + T2 10 + T3 10 + T4 10 + T5 8 + T6 8 + T7 8 + T8 4 = 68 subtasks)
- Dev Notes 17종 (CR lessons + AD-22 + AD-14 + NFR4 + Epic 12 2FA + AD-44 (a)~(g) + D-FINOPS-7 honestly DEFER 보존)
- Architecture Alignment cj-style ALLOWED sweep (m25_finops_sustainability module + ALLOWED_SERVICE_SUBMODULES sweep)
- Files Affected ~33 files estimate (~21 NEW + ~12 MODIFIED)
- Test Coverage: ~62 NEW pytest PASS + ~8 NEW vitest PASS + 0 NEW ruff + 0 NEW tsc

### 결정 3: 8 ACs §F33.1~§F33.8 verbatim → 86 sub-ACs 전개 결정 wire
- §F33.1 carbon_emissions_aggregator: aggregate_carbon_emissions + 6-module cross-rollup Phase 11~16 EXTENSION + CarbonEmissionsRollup TypedDict 14 fields + 4 scope 옵션 tenant/department/cost_center/product_line + 6-module cross-join RLS + period selector + cache layer 24h TTL Redis + 6-module index hints + audit-first INSERT `carbon_emissions_aggregated` + typed exception envelope 4 NEW = 11 sub-ACs
- §F33.2 sustainability_kpi_selector: KPI #1 total_carbon_emissions_kgco2e + KPI #2 scope1_emissions_kgco2e + KPI #3 scope2_emissions_kgco2e + KPI #4 scope3_emissions_kgco2e + KPI #5 carbon_intensity_kgco2e_per_krw = total_carbon / total_cost + KPI #6 data_center_pue = Power Usage Effectiveness + KPI #7 renewable_energy_pct + KPI #8 carbon_offset_kgco2e via VCU + CER + KCU registries + SustainabilityKPIMetric TypedDict 8 fields + audit-first INSERT `sustainability_kpi_calculated` = 11 sub-ACs
- §F33.3 sustainability_report_generation_engine: 3 export_format PDF reportlab==4.0.7 + CSV pandas==2.1.4 + Excel xlsxwriter==3.1.9 + 3 cadence monthly + quarterly + annual + SustainabilityReport TypedDict 13 fields + 5-framework support (CSRD + SEC Climate Disclosure + EU Taxonomy + IFRS S2 + KSSB) + S3 archive + delivery + recipient resolver 4종 + audit-first INSERT 2 NEW + typed exception envelope 4 NEW = 11 sub-ACs
- §F33.4 scheduled_sustainability_dispatch: 4 cron schedules weekly Mon 09:00 + monthly 1st-day 09:00 + quarterly 1st-day 09:00 + annual Jan-1 09:00 + apscheduler==3.10.4 + pytz==2024.1 + ScheduledSustainabilityDispatch TypedDict 10 fields + lifecycle state machine + idempotency + retry policy + audit-first INSERT 2 NEW + typed exception envelope 4 NEW = 11 sub-ACs
- §F33.5 tenant_scoped_sustainability_role_rbac: Role.SUSTAINABILITY_VIEWER 신규 + require_sustainability_role 신규 dep + tenant-scoped RBAC + Epic 12 2FA 챌린지 mandatory + AD-22 owner-only RBAC + phase_11~16 carry-over 검증 + typed exception envelope 3 NEW = 11 sub-ACs
- §F33.6 sustainability_dashboard_ui: 5 sub-components CarbonEmissionsAggregator + SustainabilityKPISelector + SustainabilityReportGeneratorPanel + ScheduledDispatchConfigPanel + ComplianceTrendMiniChart + ko-KR.json finops_sustainability.* namespace EXTENSION ~30 keys + ARIA labels WCAG 2.1 AA + Recharts 2.12.7 AD-14 stack pin = 10 sub-ACs
- §F33.7 Capability matrix v1.43 EXTENSION FINOPS_SUSTAINABILITY + Capability.FINOPS_SUSTAINABILITY 1 NEW enum + FinopsSustainabilityAction 8 NEW Literal + require_finops_sustainability 1 NEW dep + 4-industry grants ✅/✅/✅/✅ + phase_11~16 carry-over 검증 = 12 sub-ACs
- §F33.8 dry-run + Tests + wire scope T1~T8: 10 sub-ACs
- = 11+11+11+11+11+10+12+10 = **86 sub-ACs 만족 pre-flight 정합 sweep**

### 결정 4: Tasks T1~T8 + 68 subtasks 결정 wire
- T1: carbon_emissions_aggregator + reporting/sustainability module + CarbonEmissionsRollup TypedDict + 4 scope options = 10 subtasks
- T2: sustainability_kpi_selector + 8 NEW KPI + 6-module index hints + SCOPE_1/2/3 emissions calculation = 10 subtasks
- T3: sustainability_report_generator + 3 export_format + 5-framework support (CSRD + SEC + EU Taxonomy + IFRS S2 + KSSB) = 10 subtasks
- T4: scheduled_sustainability_dispatch + 4 cron schedules + apscheduler + pytz + recipient resolver = 10 subtasks
- T5: alembic 0049 phase_17_finops_sustainability 6 NEW tables + RLS + CHECK + UNIQUE + indexes = 8 subtasks
- T6: audit action EXTENSION 8 NEW typed exceptions + 8 NEW audit values + ActionClass.FINOPS_SUSTAINABILITY + Capability.FINOPS_SUSTAINABILITY + 4-industry grants = 8 subtasks
- T7: capability matrix v1.43 EXTENSION + apps/web/components/sustainability/SustainabilityDashboardPanel + admin/finops/sustainability page + lib/sustainability-client + ko-KR.json EXTENSION ~30 keys = 8 subtasks
- T8: 3중 게이트 FINAL CLEAN atomic commit = 4 subtasks
- = 10+10+10+10+8+8+8+4 = **68 subtasks 결정 wire**

### 결정 5: sprint-status v3.39 → v3.40 EXTENSION + atomic commit + 5 files
- 5 files atomic single sprint 결정 wire
- 1 NEW spec file
- 1 MODIFIED sprint-status v3.39 → v3.40
- 1 NEW handoff memory
- 1 NEW commit-msg
- 1 MODIFIED MEMORY.md hook EXTENSION
- = 3 NEW + 2 MODIFIED = **5 files atomic single sprint**

---

## 2. 5 files atomic single sprint inventory

| File | Status | LOC | Description |
|---|---|---|---|
| `_bmad-output/implementation-artifacts/phase-17-finops-sustainability-carbon-reporting-wire.md` | NEW | ~+440 LOC | spec file (Story + 8 ACs §F33.1~§F33.8 verbatim → 86 sub-ACs + T1~T8 + 68 subtasks + Dev Notes + Architecture Alignment + Files Affected + Test Coverage) |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | MODIFIED | v3.39→v3.40 EXTENSION | sprint-status v3.40 + phase-17-spec-entry entry + A479~A483 + last_updated_note v3.40 |
| `memory/handoff-2026-08-25-phase-17-spec-entry-done.md` | NEW | this file | handoff memory |
| `_bmad-output/implementation-artifacts/commit-msg-phase-17-spec-entry.txt` | NEW | commit message | atomic commit CR 9-6 D5 prevention |
| `memory/MEMORY.md` | MODIFIED | EXTENSION | MEMORY.md hook EXTENSION |

**Total**: 3 NEW + 2 MODIFIED = 5 files atomic single sprint 결정 wire 진입 완료

---

## 3. CR lessons applied 17종 (verbatim 보존)

- CR 0-2: RLS auto-application 6 tables (Phase 16 wire `81ae00a` EXTENSION)
- CR 1-1: audit-first INSERT 8 NEW (carbon_emissions_aggregated + sustainability_kpi_calculated + sustainability_report_generated + sustainability_report_exported + sustainability_scheduled_dispatch_evaluated + sustainability_report_dispatched + sustainability_dry_run_executed + carbon_offset_registered) + audit action EXTENSION
- CR 4-3/4-4: Industry enum SSOT + A5 drift detector + golden_diff
- CR 9-6 D5 prevention: commit message discipline `git commit -F <file>` via commit-msg-phase-17-spec-entry.txt
- CR 11-3: honest-DEFER 26번째 + ALLOWED_SERVICE_SUBMODULES 즉시 sweep + ruff auto-fix
- CR 11-4 P-015: ko-KR.json EXTENSION ~30 keys finops_sustainability.* namespace (verbatim SSOT)
- CR 11-4 D-001~D-005: TS mirror parity + cross-language drift detector
- CR 12-1 L4: industry-agnostic 4-industry grants ✅/✅/✅/✅
- CR 12-5 D-14: typed exception envelope 16 NEW (CarbonEmissionsRollupInvalidError(400) + CarbonEmissionsRollupScopeError(404) + CarbonEmissionsRollupPeriodError(422) + CarbonEmissionsCrossModuleJoinError(500) + SustainabilityKPIError(500) + SustainabilityReportGenerationError(500) + SustainabilityReportExportError(500) + SustainabilityReportArchiveError(500) + ScheduledSustainabilityDispatchError(500) + SustainabilityCronExpressionInvalidError(400) + SustainabilityRecipientResolverError(404) + SustainabilityDispatchIdempotencyViolationError(422) + SustainabilityRolePermissionError(403) + SustainabilityTenantScopeViolationError(403) + SustainabilityCapabilityGateViolationError(403) + SustainabilityAccuracyDegradationError(500))
- CR 12-5 D-PARITY-01 inversion: TS mirror parity
- CR 12-5 D-GATE-01 inversion: capability gate inversion
- A19 cohesion: 9 surface EXTENSION PASS
- A36 SDR 검증 4-step 자동 적용
- AD-14 stack pin: Recharts 2.12.7 + slack-sdk==3.23.0 + pdpyras==5.2.0 + sendgrid==6.11.0 + reportlab==4.0.7 + openpyxl==3.1.2 + pandas==2.1.4 + xlsxwriter==3.1.9 + apscheduler==3.10.4 + pytz==2024.1
- AD-22 owner-only RBAC + Epic 12 2FA 챌린지 보존 + NFR4 PII minimization ✅ PRESERVED

---

## 4. AD-44 FinOps Sustainability & Carbon Reporting 신규 (a)~(g) 7 sub-decisions

(a) carbon_emissions_aggregator 6-module cross-join + CarbonEmissionsRollup TypedDict 14 fields + 4 scope 옵션 tenant + department + cost_center + product_line + carbon offsets via VCU + CER + KCU registries

(b) sustainability_kpi_selector 8 NEW KPI calculations total_carbon_emissions_kgco2e + scope1/2/3_emissions_kgco2e + carbon_intensity_kgco2e_per_krw + data_center_pue + renewable_energy_pct + carbon_offset_kgco2e + 6-module index hints

(c) sustainability report generation engine PDF + CSV + Excel + 3 cadence monthly + quarterly + annual + SustainabilityReport TypedDict 13 fields + 5-framework support CSRD + SEC + EU Taxonomy + IFRS S2 + KSSB + 8-section PDF template

(d) scheduled dispatch KST cron 4 cron schedules weekly Mon 09:00 + monthly 1st-day 09:00 + quarterly 1st-day 09:00 + annual Jan-1 09:00 + recipient resolver Slack + Email + S3 archive dispatch + ScheduledSustainabilityDispatch TypedDict 10 fields

(e) tenant-scoped sustainability role RBAC owner-only + Role.SUSTAINABILITY_VIEWER 1 NEW enum + require_sustainability_role() Dependency 1 NEW wire + 4 industries baseline (manufacturing ≤ 0.0008 + service ≤ 0.0004 + manufacturing_service ≤ 0.0006 + manufacturing_service_other ≤ 0.0007 kgCO2e/KRW)

(f) sustainability dashboard UI 5 sub-components CarbonEmissionsAggregator + SustainabilityKPISelector + SustainabilityReportGeneratorPanel + ScheduledDispatchConfigPanel + ComplianceTrendMiniChart + ko-KR.json finops_sustainability.* namespace EXTENSION ~30 keys + ARIA labels WCAG 2.1 AA + Recharts 2.12.7 AD-14 stack pin

(g) Capability matrix v1.43 EXTENSION FINOPS_SUSTAINABILITY + audit-first INSERT 8 NEW + ActionClass.FINOPS_SUSTAINABILITY 1 NEW + FinopsSustainabilityAction 8 NEW Literal + apps/api/core/capability.py MODIFIED Capability.FINOPS_SUSTAINABILITY + apps/api/dependencies/capability.py MODIFIED require_finops_sustainability + apps/api/core/role.py MODIFIED Role.SUSTAINABILITY_VIEWER + 4-industry grants ✅/✅/✅/✅ industry-agnostic + dry-run 5 NEW CLI flags + Tests + wire scope T1~T8

---

## 5. Pre-flight sweep results

- 3중 게이트 impact NONE: ruff scoped 0 NEW + pytest 0 NEW + vitest 0 NEW + tsc 0 NEW
- Capability matrix v1.42 → v1.43 EXTENSION verified
- AD-44 (a)~(g) 7 sub-decisions all defined
- AD-22 owner-only RBAC + Epic 12 2FA 챌린지 보존
- D-FINOPS-7 honestly DEFER 보존
- 17 CR lessons all applied

---

## 6. Epic 1~17 + Phase 3~16 + 1st release cycle 정합 보존

Phase 17 spec entry 진입 시점에 pre-flight 정합 sweep 만족 = Epic 1~17 + Phase 3~16 + 1st release cycle 모두 wire DONE 진입 정합 보존 + Phase 16 4-entry-point (PRD entry + spec entry + wire + retro) ALL DONE 진입 정합 보존 + Phase 17 2-entry-point (PRD entry + spec entry) 진입 완료 정합 보존.

---

## 7. Phase 16 → Phase 17 carry-over chain

Phase 16 close-out retro (cj-style 128번째) 의 FinOps Reporting & Executive Dashboard territory + Phase 15 wire `1b800d9` (cj-style 123번째) FinOps Tag Governance territory + Phase 14 wire `e904485` (cj-style 119번째) FinOps Optimization territory + Phase 13 wire `8b98030` (cj-style 115번째) FinOps Forecasting territory + Phase 12 wire `f3c0e63` (cj-style 111번째) Cost Anomaly Detection & Budget Alerting territory + Phase 11 wire `e020ad0` (cj-style 107번째) FinOps Showback / Chargeback territory 의 자연스러운 carry-over chain (cost ⇒ carbon emissions ⇒ carbon intensity ⇒ renewable energy ⇒ PUE ⇒ carbon offset EXTENSION 정직 회복 chain 결정). Phase 16 territory (5 FinOps modules cross-join + executive-grade rollup + 8 NEW KPI + executive report PDF/CSV/Excel + scheduled dispatch KST cron) 의 natural SUSTAINABILITY & CARBON REPORTING LAYER EXTENSION (6-module cross-join + sustainability cross-rollup view + scope 1/2/3 emissions + carbon offset accounting + renewable energy + scheduled sustainability report dispatch PDF + CSV + Excel monthly/quarterly/annual EXTENSION 정직 회복 chain 결정) — EU CSRD + SEC Climate Disclosure + EU Taxonomy + IFRS S2 + 한국 KSSB regulatory driver EXTENSION chain 정직 회복.

---

## 8. D-DEFER-* honestly 결정 보존 (carry-over chain EXTENSION)

| Defer ID | Phase | Status | 비고 |
|---|---|---|---|
| D-FINOPS-1 | Phase 11 close-out | ✅ RESOLVED | honestly 결정 wire |
| D-FINOPS-2 | Phase 12 close-out | ✅ RESOLVED | honestly 결정 wire |
| D-FINOPS-3 | Phase 13 close-out | ✅ RESOLVED | honestly 결정 wire |
| D-FINOPS-4 | Phase 14 close-out | ✅ RESOLVED | honestly 결정 wire 보존 1 NEW |
| D-FINOPS-5 | Phase 15 close-out | ✅ RESOLVED | honestly 결정 wire 보존 |
| D-FINOPS-6 | Phase 16 close-out | ✅ RESOLVED | honestly 결정 wire 보존 |
| **D-FINOPS-7** | **Phase 17 spec entry (현재)** | **🔶 honestly DEFER** | **신규 진입 결정 wire 보존** |

**진입 완료 결정 wire**:
- D-FINOPS-1/2/3/4/5/6 ✅ ALL RESOLVED 보존 (Phase 11 + Phase 12 + Phase 13 + Phase 14 + Phase 15 + Phase 16 close-out retro territory verbatim)
- D-FINOPS-7 🔶 honestly DEFER 보존 (Phase 17 PRD entry 진입 시점 + Phase 17 spec entry 진입 시점)

---

## 9. next 결정 wire 보류

옵션:
- (a) Phase 17 atomic wire T1~T8 진입 (cj-style 131번째)
- (b) Phase 17 close-out retro 진입 (cj-style 132번째)
- (c) Epic 18+ 진입
- (d) D-DEFER-* follow-up 결정 wire 보류

---

## 10. Related memories

- [[handoff-2026-08-25-phase-17-prd-entry-done]] — Phase 17 PRD entry baseline `e0778ed`
- [[handoff-2026-08-25-phase-16-close-out-done]] — Phase 16 close-out retro baseline `26fd530`
- [[handoff-2026-08-25-phase-16-wire-done]] — Phase 16 wire (FINOPS_REPORTING 4-industry ✅)
- [[handoff-2026-08-25-phase-16-spec-entry-done]] — Phase 16 spec entry (cj-style 126번째)
- [[handoff-2026-08-25-phase-16-prd-entry-done]] — Phase 16 PRD entry (cj-style 125번째)
- [[handoff-2026-08-25-phase-15-close-out-done]] — Phase 15 close-out retro

---

## Why

cj-style 129번째 epic 연속 정직 회복 atomic docs-only wire 진입 완료 보존 (Phase 17 1번째 진입점 = cj-style 129번째) 직후, 자연스러운 spec entry 진입 (cj-style 130번째 = Phase 17 2번째 진입점) 결정 wire. 4-entry-point pattern (PRD entry → spec entry → wire → close-out retro) 의 2번째 단계 완료.

## How to apply

Phase 17 atomic wire T1~T8 (cj-style 131번째) 진입 시: 본 메모리 + capability matrix v1.43 + sprint-status v3.40 + master PRD v4.8 §F33 EXTENSION + spec file phase-17-finops-sustainability-carbon-reporting-wire.md 결정 wire 진입 상태 전제 + D-FINOPS-7 honestly DEFER 보존 진입 + AD-44 (a)~(g) 7 sub-decisions pre-flight 정합 sweep + T1~T8 8 tasks + 68 subtasks + 86 sub-ACs + 17종 CR lessons + AD-14 stack pin verbatim 적용.
