---
name: handoff-2026-08-25-phase-17-prd-entry-done
description: Phase 17 PRD entry DONE (cj 129). FinOps Sustainability & Carbon Reporting territory 진입. 6 files atomic single sprint = 2 NEW + 4 MODIFIED. D-FINOPS-7 신규 honestly DEFER 보존
metadata:
  type: project
---

# Phase 17 PRD entry handoff (cj-style 129번째 wire)

**Date**: 2026-08-25 (KST)
**Commit**: TBD (cj-style Phase 17 PRD entry atomic docs-only wire = cj-style 129번째 docs only)
**Branch**: `9-3-dev-2026-08-17`
**baseline_commit**: `26fd530` (Phase 16 close-out retro commit = cj-style 128번째 tip)

## What was wired

Phase 17 PRD entry territory — atomic docs-only wire 6 files:

### MODIFIED master PRD (1)
1. `_bmad-output/planning-artifacts/prd.md` — v4.7 → v4.8 EXTENSION (§F33 FinOps Sustainability & Carbon Reporting territory 신규 8 ACs §F33.1~§F33.8 verbatim ~86 sub-ACs (11+11+11+11+11+10+12+10) + AD-44 (a)~(g) 7 sub-decisions + §15 로드맵 Phase 17 row status 백로그 → in-progress + §8.1 M0-(z) AC 신규 + §부록 A 신규 결정 표 + title `bizup 통합 PRD v4.8` EXTENSION + changelog v4.8 (2026-08-25) entry prepend)

### MODIFIED capability matrix (1)
2. `docs/capability-matrix.md` — v1.42 → v1.43 EXTENSION (FINOPS_SUSTAINABILITY 1 NEW row after FINOPS_REPORTING industry-agnostic 4-industry grants ✅/✅/✅/✅ + title v1.42 → v1.43 + v1.43 changelog entry prepend mirroring v1.42 Phase 16 PRD entry pattern verbatim)

### MODIFIED sprint-status (1)
3. `_bmad-output/implementation-artifacts/sprint-status.yaml` — v3.38 → v3.39 EXTENSION (`phase-17-prd-entry: backlog → done` 신규 entry EXTENSION 결정 wire line 1217 직후 EXTENSION + A474~A478 action_items 신규 block 5 entries EXTENSION 결정 wire + last_updated_note_v3_39 Phase 17 PRD entry prepend 결정 wire)

### NEW handoff memory (1)
4. `memory/handoff-2026-08-25-phase-17-prd-entry-done.md` (THIS file)

### NEW commit-msg (1)
5. `commit-msg-phase-17-prd-entry.txt` (CR 9-6 verbatim D5 prevention)

### MODIFIED MEMORY.md (1)
6. `memory/MEMORY.md` — Phase 17 PRD entry hook EXTENSION (Phase 16 PRD entry cycle (cj-style 125번째) → Phase 17 PRD entry (cj-style 129번째) chain EXTENSION 보존 + Phase 17 cj-style 4-entry-point 진입 패턴 verbatim 미러링)

## 8 ACs §F33.1~§F33.8 verbatim ~86 sub-ACs

1. **§F33.1 carbon_emissions_aggregator** (11 sub-ACs) — 6-module cross-rollup carbon emissions aggregator (Phase 11 showback + Phase 12 anomaly + Phase 13 forecast + Phase 14 optimization + Phase 15 tag_governance + Phase 16 executive) + CarbonEmissionsRollup TypedDict 14 fields (carbon_rollup_id + tenant_id + period_key + scope enum tenant/department/cost_center/product_line + scope_chain value_jsonb 6-module source attribution + total_carbon_emissions_kgco2e NUMERIC(20,4) + scope1_emissions_kgco2e + scope2_emissions_kgco2e + scope3_emissions_kgco2e + carbon_offset_kgco2e + net_carbon_emissions_kgco2e + renewable_energy_pct + computed_at + trace_id)

2. **§F33.2 sustainability_kpi_selector** (11 sub-ACs) — 8 NEW KPI calculations (total_carbon_emissions_kgco2e + scope1_emissions_kgco2e + scope2_emissions_kgco2e + scope3_emissions_kgco2e + carbon_intensity_kgco2e_per_krw = total_carbon / total_cost + data_center_pue = Power Usage Effectiveness + renewable_energy_pct + carbon_offset_kgco2e via VCU + CER + KCU registries) + 6-module index hints

3. **§F33.3 sustainability_report_generation_engine** (11 sub-ACs) — PDF (reportlab==4.0.7 + Korean font registration + 8-section template CSRD-aligned) + CSV (pandas==2.1.4 + openpyxl==3.1.2) + Excel (xlsxwriter==3.1.9 IFRS S2 metrics) + 3 cadence (monthly + quarterly + annual) + SustainabilityReport TypedDict 13 fields + 5-framework support (CSRD + SEC Climate Disclosure + EU Taxonomy + IFRS S2 + KSSB)

4. **§F33.4 scheduled_sustainability_dispatch** (11 sub-ACs) — 4 cron schedules (weekly Mon 09:00 KST + monthly 1st-day 09:00 KST + quarterly 1st-day 09:00 KST + annual Jan-1 09:00 KST) + recipient resolver (Slack + Email + S3 archive dispatch) + ScheduledSustainabilityDispatch TypedDict 10 fields

5. **§F33.5 tenant-scoped sustainability role RBAC** (11 sub-ACs) — owner-only RBAC + Role.SUSTAINABILITY_VIEWER 1 NEW enum + require_sustainability_role() Dependency 1 NEW wire (Phase 16 `require_executive_role` 패턴 verbatim) + 미허용 tenant 의 sustainability dashboard 진입 차단 + tenant-level override EXTENSION (tenant_owner_id 의 delegated sustainability viewer 권한 OPTIONAL) + Epic 12 2FA 챌린지 보존

6. **§F33.6 sustainability dashboard UI** (10 sub-ACs) — 5 sub-components (CarbonEmissionsAggregator + SustainabilityKPISelector + SustainabilityReportGeneratorPanel + ScheduledDispatchConfigPanel + ComplianceTrendMiniChart) + ko-KR.json `finops_sustainability.*` namespace EXTENSION ~30 keys (CR 11-4 D-002 verbatim SSOT) + ARIA labels WCAG 2.1 AA + Recharts 2.12.7 AD-14 stack pin

7. **§F33.7 Capability matrix v1.43 EXTENSION** (12 sub-ACs) — FINOPS_SUSTAINABILITY 1 NEW row industry-agnostic 4-industry grants ✅/✅/✅/✅ (CR 12-1 L4 precedent verbatim) + ActionClass.FINOPS_SUSTAINABILITY 1 NEW (CR 1-1 audit-first INSERT 8 NEW Literal values)

8. **§F33.8 dry-run + Tests + wire scope T1~T8** (10 sub-ACs) — dry-run mode 5 NEW CLI flags + apps/api pytest tests + apps/web vitest tests + wire scope T1~T8 결정 wire 보존

## AD-44 FinOps Sustainability & Carbon Reporting 신규 (a)~(g) 7 sub-decisions

(a) carbon_emissions_aggregator 6-module cross-join + CarbonEmissionsRollup TypedDict 14 fields + 4 scope 옵션 tenant + department + cost_center + product_line + carbon offsets via VCU + CER + KCU registries

(b) sustainability_kpi_selector 8 NEW KPI calculations total_carbon_emissions_kgco2e + scope1/2/3_emissions_kgco2e + carbon_intensity_kgco2e_per_krw + data_center_pue + renewable_energy_pct + carbon_offset_kgco2e + 6-module index hints

(c) sustainability report generation engine PDF + CSV + Excel + 3 cadence monthly + quarterly + annual + SustainabilityReport TypedDict 13 fields + 5-framework support CSRD + SEC Climate Disclosure + EU Taxonomy + IFRS S2 + KSSB + 8-section PDF template

(d) scheduled dispatch KST cron 4 cron schedules weekly Mon 09:00 + monthly 1st-day 09:00 + quarterly 1st-day 09:00 + annual Jan-1 09:00 + recipient resolver Slack + Email + S3 archive dispatch + ScheduledSustainabilityDispatch TypedDict 10 fields

(e) tenant-scoped sustainability role RBAC owner-only + Role.SUSTAINABILITY_VIEWER 1 NEW enum + require_sustainability_role() Dependency 1 NEW wire + 4 industries baseline (manufacturing ≤ 0.0008 + service ≤ 0.0004 + manufacturing_service ≤ 0.0006 + manufacturing_service_other ≤ 0.0007 kgCO2e/KRW)

(f) sustainability dashboard UI 5 sub-components CarbonEmissionsAggregator + SustainabilityKPISelector + SustainabilityReportGeneratorPanel + ScheduledDispatchConfigPanel + ComplianceTrendMiniChart + ko-KR.json finops_sustainability.* namespace EXTENSION ~30 keys + ARIA labels WCAG 2.1 AA + Recharts 2.12.7 AD-14 stack pin

(g) Capability matrix v1.43 EXTENSION FINOPS_SUSTAINABILITY + audit-first INSERT 8 NEW via emit_audit_typed + ActionClass.FINOPS_SUSTAINABILITY 1 NEW + FinopsSustainabilityAction 8 NEW Literal + apps/api/core/capability.py MODIFIED Capability.FINOPS_SUSTAINABILITY + apps/api/dependencies/capability.py MODIFIED require_finops_sustainability + apps/api/core/role.py MODIFIED Role.SUSTAINABILITY_VIEWER + 4-industry grants ✅/✅/✅/✅ industry-agnostic per CR 12-1 L4 verbatim + dry-run 5 NEW CLI flags + Tests + wire scope T1~T8

## Pre-flight sweep results

- 3중 게이트 impact NONE: ruff scoped 0 NEW + pytest 0 NEW failures + vitest 0 NEW failures + tsc 0 NEW errors
- Capability matrix v1.42 → v1.43 EXTENSION verified
- AD-44 (a)~(g) 7 sub-decisions all defined
- AD-22 owner-only RBAC + Epic 12 2FA 챌린지 보존
- D-FINOPS-7 honestly DEFER 보존
- 17 CR lessons all applied (CR 0-2 + CR 1-1 + CR 4-3/4-4 + CR 9-6 + CR 11-3 + CR 11-4 + CR 12-1 + CR 12-5 D-14 + CR 12-5 D-PARITY-01 + CR 12-5 D-GATE-01 + A19 cohesion 9 surface EXTENSION + A36 SDR 검증 + AD-14 + AD-22 + AD-44 + NFR4 + NFR18)

## Epic 1~17 + Phase 3~16 + 1st release cycle 정합 보존

Phase 17 PRD entry 진입 시점에 pre-flight 정합 sweep 만족 = Epic 1~17 + Phase 3~16 + 1st release cycle 모두 wire DONE 진입 정합 보존 + Phase 16 4-entry-point (PRD entry + spec entry + wire + retro) ALL DONE 진입 정합 보존 + Phase 17 1-entry-point (PRD entry) 진입 완료 정합 보존.

## Phase 16 → Phase 17 carry-over chain

Phase 16 close-out retro (cj-style 128번째) 의 FinOps Reporting & Executive Dashboard territory + Phase 15 wire `1b800d9` (cj-style 123번째) FinOps Tag Governance territory + Phase 14 wire `e904485` (cj-style 119번째) FinOps Optimization territory + Phase 13 wire `8b98030` (cj-style 115번째) FinOps Forecasting territory + Phase 12 wire `f3c0e63` (cj-style 111번째) Cost Anomaly Detection & Budget Alerting territory + Phase 11 wire `e020ad0` (cj-style 107번째) FinOps Showback / Chargeback territory 의 자연스러운 carry-over chain (cost ⇒ carbon emissions ⇒ carbon intensity ⇒ renewable energy ⇒ PUE ⇒ carbon offset EXTENSION 정직 회복 chain 결정). Phase 16 territory (5 FinOps modules cross-join + executive-grade rollup + 8 NEW KPI + executive report PDF/CSV/Excel + scheduled dispatch KST cron) 의 natural SUSTAINABILITY & CARBON REPORTING LAYER EXTENSION (6-module cross-join + sustainability cross-rollup view + scope 1/2/3 emissions + carbon offset accounting + renewable energy + scheduled sustainability report dispatch PDF + CSV + Excel monthly/quarterly/annual EXTENSION 정직 회복 chain 결정) — EU CSRD + SEC Climate Disclosure + EU Taxonomy + IFRS S2 + 한국 KSSB regulatory driver EXTENSION chain 정직 회복.

## next

옵션 (a) Phase 17 spec entry 진입 (cj-style 130번째) / 옵션 (b) Phase 17 atomic wire T1~T8 진입 (cj-style 131번째) / 옵션 (c) Phase 17 close-out retro 진입 (cj-style 132번째) / 옵션 (d) Epic 18+ 진입 / 옵션 (e) D-DEFER-* follow-up 결정 wire 보류.

**Why:** Phase 17 PRD entry completion marks the entry into the cj-style 4-entry-point cycle's 1st entry point (PRD entry) for FinOps Sustainability & Carbon Reporting territory. Phase 16 cycle ALL DONE 진입 정합 보존 (PRD entry + spec entry + wire + retro = cj-style 128번째 진입 완료) + Phase 17 1-entry-point (PRD entry) cj-style 129번째 진입 완료.

**How to apply:** When resuming, the working tree is at the Phase 17 PRD entry commit (TBD) on branch 9-3-dev-2026-08-17. Next action depends on chosen option from (a)~(e) above. The cj-style 4-entry-point (PRD 129 + spec 130 + wire 131 + retro 132) cycle continues the pattern verbatim.
