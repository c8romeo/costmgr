---
baseline_commit: db005e8
status: backlog
cj_style_entry_point: 195
story_key: phase-28-t2-frontend-follow-up-prd
---

# Epic 28 T2 frontend follow-up PRD (cj-style 195번째 epic 연속 정직 회복)

## Story

**As a** FinOps practitioner / cloud architect / tenant admin / 1st release customer / DevOps engineer
**I want** Epic 28 follow-up sprint 결정 wire (Epic 28 wire Q2 backend-only sprint `db005e8` (cj-style 193번째) 의 honestly DEFER 보존 결정 wire 회복 = **T2 frontend dashboard UI + 5 NEW sub-components** (CrossPhaseKPIOverview + SavedViewManager + DrillDownExplorer + ExportConfigPanel + DashboardSharingPanel) + **FinopsInteractiveDashboardPanel.tsx orchestrator** (5-tab layout + dry-run toggle default ON per CR 11-3 honest-DEFER discipline) + **2 NEW RSC pages** (`/admin/finops/interactive-dashboard/{page,layout}.tsx`) + **2 NEW TS mirrors** (`interactive-dashboard-types.ts` Python TypedDict parity + `interactive-dashboard-client.ts` 11 endpoint fetch parity CR 12-5 D-PARITY-01 inversion) + **~25-28 NEW vitest cases** (Phase 26 pattern verbatim mirror) + **ko-KR.json EXTENSION ~30 keys** `finops_interactive_dashboard.*` namespace (NFR18 ko-KR SSOT) + **dry-run mode UI** + **Epic 12 2FA 챌린지 mandatory ≥ 10M KRW/year sharing scope** + **AD-22 owner-only RBAC** + **8 ACs §F44.1~§F44.8 + T1~T7 + Dev Notes 21종** + **wire scope T1~T7**) 결정 wire
**so that** Epic 28 atomic wire (cj-style 193번째) 의 honestly DEFER 보존 결정 wire 진입 정직 회복 = Phase 28 PRD entry `62b2e32` (cj-style 191번째) 의 §F43.4 (dashboard UI 5 NEW sub-components + 2 TS mirrors + 2 RSC pages) + Phase 28 spec entry `5f29a56` (cj-style 192번째) 의 T2 frontend dashboard UI 결정 wire + Phase 28 atomic wire Q2 backend-only `db005e8` (cj-style 193번째) 의 Q2 결정 wire (backend-only sprint 의 T2 frontend honestly DEFER → follow-up sprint 결정 wire 보존) + Epic 28 close-out retro `epic-28-retro-2026-08-29.md` (cj-style 194번째) 의 §12 옵션 (a) "T2 frontend follow-up sprint 진입 결정 wire (cj-style 195번째)" verbatim 진입 = cj-style 4-entry-point cycle 의 follow-up sprint 진입 결정 wire (Phase 28 PRD entry → spec entry → wire → close-out retro 의 4-entry-point cycle 의 후속 follow-up sprint 진입 정직 회복) + Phase 28 territory = Epic 28 wire (cj-style 193) 의 4 NEW backend modules (`cross_phase_aggregator` + `saved_view_engine` + `export_pipeline` + `dashboard_router`) 의 **frontend UI surface 신규 진입** = Epic 28 wire 의 backend ledger data 활용 → 새 frontend infra 불필요 + reuse 최대화 + risk 최소화 + 비즈니스 가치 최고 (executive dashboard surface = 비용 통제 layer 직접적 ROI) + Epic 12 2FA 챌린지 mandatory high-value ≥ 10M KRW/year sharing scope + AD-22 owner-only RBAC + NFR4 PII minimization ✅ PRESERVED + NFR18 ko-KR SSOT + **AD-57 신규 (a)~(c) 3 sub-decisions** 모두 결정 wire 진입 + D-FINOPS-15 honestly DEFER 보존 + CR 11-3 honest-DEFER 90번째 epic 연속 정직 회복 verification 결정 wire 진입 + 3중 게이트 impact NONE (docs only 변경 = cj-style 195번째 wire 진입 표준 = docs only sprint) 결정 wire.

## Context

cj-style Epic 28 follow-up sprint 1번째 진입점 (cj-style 195번째) 진입 결정 wire 진입 완료:

- Epic 28 close-out retro (cj-style 194번째) DONE 진입 정합 보존
- Phase 28 atomic wire Q2 backend-only `db005e8` (cj-style 193번째) DONE 진입 정합 보존
- Phase 28 spec entry `5f29a56` (cj-style 192번째) DONE 진입 정합 보존
- Phase 28 PRD entry `62b2e32` (cj-style 191번째) DONE 진입 정합 보존
- Phase 25 extra=forbid 조이기 source sprint `232fc49` (cj-style 190번째) DONE 진입 정합 보존
- Phase 21~26 Layer 2 P1 + Layer 3 P2 carry-over `d38f388` (cj-style 189번째) DONE 진입 정합 보존
- Phase 27 Layer 2 P1 + Layer 3 P2 carry-over `836a8d4` (cj-style 188번째) DONE 진입 정합 보존
- Phase 26 vitest frontend test sprint `2dd9744` (cj-style 187번째) DONE 진입 정합 보존
- Phase 26 dashboard UI extension sprint `fbc6f42` (cj-style 186번째) DONE 진입 정합 보존
- Phase 26 cj-182 close-out retro (cj-style 185번째) DONE 진입 정합 보존
- Phase 26 capability matrix extension (cj-style 184번째) DONE 진입 정합 보존
- Phase 26 atomic wire `0cf2547` (cj-style 183번째) DONE 진입 정합 보존
- Phase 26 spec entry `36efc71` (cj-style 182번째) DONE 진입 정합 보존
- Phase 26 PRD entry `b95ebc3` (cj-style 181번째) DONE 진입 정합 보존
- audit-fixes sprint close-out retro (cj-style 178번째) DONE 진입 정합 보존
- audit-fixes sprint retroactive correction (cj-style 177 follow-up) DONE 진입 정합 보존
- audit-fixes sprint wire (cj-style 176번째) DONE 진입 정합 보존
- audit-fixes sprint entry (cj-style 166번째) DONE 진입 정합 보존
- Phase 25 close-out retro `6119791` (cj-style 175번째) DONE 진입 정합 보존
- Phase 25 integration follow-up `1fc8302` (cj-style 174 follow-up) DONE 진입 정합 보존
- Phase 25 wire `de1b69d` (cj-style 173번째) DONE 진입 정합 보존
- Phase 25 spec entry `5e8d435` (cj-style 172번째) DONE 진입 정합 보존
- Phase 25 PRD entry `5e8d435` (cj-style 171번째) DONE 진입 정합 보존
- Phase 11~20 audit-fixes chain (cj-style 154/155/156/157) DONE 진입 정합 보존
- Phase 11~27 18-capability FinOps territory chain ✅ ALL WIRED INTEGRATED 진입 정합 보존
- Epic 1~17 ALL DONE 진입 정합 보존
- 1st release cycle ALL DONE 진입 정합 보존

### Epic 28 PRD entry 8 ACs §F44.1~§F44.8 verbatim 보존 (cj-style 195 follow-up sprint)

8 ACs §F44.1~§F44.8 → 78 explicit sub-ACs → ~78 detailed sub-ACs pre-flight 정합 sweep 만족 결정 wire:

1. **§F44.1 CrossPhaseKPIOverview sub-component** — `apps/web/components/finops/interactive-dashboard/CrossPhaseKPIOverview.tsx` (~+280 LOC) 결정 wire + Phase 11~27 18 unified KPI tile grid (Phase 11 showback_krw + Phase 12 anomaly_count + Phase 13 forecast_krw + Phase 14 optimization_savings_krw + Phase 15 tag_compliance_pct + Phase 16 report_krw + Phase 17 sustainability_co2_kg + Phase 18 commitment_utilization_pct + Phase 19 pricing_savings_krw + Phase 20 multi_cloud_reconciliation_krw + Phase 21 reserved_capacity_utilization_pct + Phase 22 chargeback_settlement_krw + Phase 23 unit_economics_cost_per_unit + Phase 24 budget_consumption_pct + Phase 25 vendor_spend_krw + Phase 26 anomaly_ml_score + Phase 27 carry_over_metric + Phase 28 unified_kpi_total = 18 unified KPIs) + 5-dim weighted aggregation gauge (cost 0.30 + usage 0.20 + performance 0.20 + compliance 0.15 + sla 0.15) + `DASHBOARD_KPI_DIMENSION_WEIGHTS` constant parity + `PHASE_KPI_SOURCE_MODULES` 18-entry dict parity + `INTERACTIVE_DASHBOARD_ENGINE_VERSION` engine version display + Recharts 2.12.7 AD-14 stack pin + `useEffect` + `useState` + `fetchUnifiedKPI` async pattern mirroring Phase 26 sub-component verbatim pattern (12 sub-ACs §F44.1.1~§F44.1.12)
2. **§F44.2 SavedViewManager sub-component** — `apps/web/components/finops/interactive-dashboard/SavedViewManager.tsx` (~+260 LOC) 결정 wire + 5 CRUD UI (create / read / update / delete / execute) + 12 NEW pre-defined view templates dropdown (CostByCloudProvider + CostByService + CostByCostCenter + CostByDepartment + CostByBusinessUnit + CostByTag + SavingsByOptimizationType + CommitmentUtilizationByCloud + BudgetVarianceByPeriod + SustainabilityByCloudProvider + VendorSpendByCategory + ReservedInstanceUtilizationByTier) + 7-dim granularity selector (minute/hour/day/week/month/quarter/year) + max_saved_views_per_tenant default 50 + cache TTL 5 minutes + audit-first INSERT 4 NEW (saved_view_created/updated/deleted/executed) (10 sub-ACs §F44.2.1~§F44.2.10)
3. **§F44.3 DrillDownExplorer sub-component** — `apps/web/components/finops/interactive-dashboard/DrillDownExplorer.tsx` (~+260 LOC) 결정 wire + 6-dim drill-down (tenant/cost_center/department/business_unit/tag/cloud_provider/service) + breadcrumb navigation + period_key selector + `DrillDownContext` TypedDict parity + `DrillDownDimension` 7-value enum parity + `DrillDownGranularity` 7-value enum parity + `DrillDownError` 500 typed exception parity (10 sub-ACs §F44.3.1~§F44.3.10)
4. **§F44.4 ExportConfigPanel sub-component** — `apps/web/components/finops/interactive-dashboard/ExportConfigPanel.tsx` (~+260 LOC) 결정 wire + 5 export format radio (pdf + xlsx + csv + json + png) + max_export_size 50MB guard display + 3 auto-retries indicator + 5-state status lifecycle (pending + in_progress + completed + failed + cancelled) + `ExportFormat` enum parity + `ExportJobStatus` enum parity + admin email alert on failure + reuse Phase 17 sustainability report generator (PDF) + Phase 22 chargeback invoice generator (XLSX) EXTENSION (10 sub-ACs §F44.4.1~§F44.4.10)
5. **§F44.5 DashboardSharingPanel sub-component** — `apps/web/components/finops/interactive-dashboard/DashboardSharingPanel.tsx` (~+260 LOC) 결정 wire + 4 sharing scope radio (private + tenant + tenant_owner + cross_tenant) + tenant isolation enforcement + RBAC: only tenant_owner can grant `cross_tenant` scope + sharing expires default 30 days + Slack DM notification + Epic 12 2FA 챌린지 mandatory for high-value grants (sharing scope=cross_tenant + 100+ saved views + ≥10M KRW/year impact) + `DashboardSharingScope` enum parity + `DashboardSharingError` 500 + `DashboardSharingScopeError` 403 + `DashboardSharingExpirationError` 400 typed exceptions parity (10 sub-ACs §F44.5.1~§F44.5.10)
6. **§F44.6 2 RSC pages + capability gate** — `apps/web/app/[locale]/(dashboard)/admin/finops/interactive-dashboard/page.tsx` (~+50 LOC) + `layout.tsx` (~+30 LOC) + `require_finops_interactive_dashboard` capability gate fail-closed 403 Forbidden + CR 1-1 RSC boundary (Server Component handles locale + RBAC + cookies auth check via access token + period_key searchParam + `redirect` to `/{locale}/login` on missing token) + Client Component handles interactive state + ARIA labels WCAG 2.1 AA + `(dashboard)` route group 보호 EXTENSION (8 sub-ACs §F44.6.1~§F44.6.8)
7. **§F44.7 2 TS mirrors + Python TypedDict parity** — `apps/web/lib/finops/interactive-dashboard-types.ts` (~+380 LOC mirroring `apps/api/modules/finops/interactive_dashboard/serializers.py` verbatim) + 7 enum exports (`KPIRefreshCadence` 6-value realtime/hourly/daily/weekly/monthly/on_demand + `ExportFormat` 5-value pdf/xlsx/csv/json/png + `DashboardSharingScope` 4-value private/tenant/tenant_owner/cross_tenant + `DashboardLayout` 3-value grid/masonry/tabs + `DrillDownDimension` 7-value tenant/cost_center/department/business_unit/tag/cloud_provider/service + `DrillDownGranularity` 7-value minute/hour/day/week/month/quarter/year + `ExportJobStatus` 5-value pending/in_progress/completed/failed/cancelled) + 6 TypedDict exports (`UnifiedKPI` 24-field + `KPIBreakdown` 8-field + `DrillDownContext` 6-field + `SavedView` 14-field + `ExportJob` 12-field + `SharingGrant` 8-field) + 4 constant exports (`DASHBOARD_KPI_DIMENSION_WEIGHTS` + `DASHBOARD_CADENCE_HOURS_KST` + `DASHBOARD_RECIPIENT_TEMPLATES` + `INTERACTIVE_DASHBOARD_ENGINE_VERSION`) + `apps/web/lib/finops/interactive-dashboard-client.ts` (~+150 LOC mirroring 11 endpoints from `dashboard_router.py`) + 11 fetch function exports (`fetchHealthcheck` + `createSavedView` + `readSavedView` + `updateSavedView` + `deleteSavedView` + `executeSavedView` + `computeUnifiedKPI` + `startExportJob` + `getExportJobStatus` + `shareDashboard` + `listPredefinedTemplates`) + CR 12-5 D-PARITY-01 inversion EXTENSION (8 sub-ACs §F44.7.1~§F44.7.8)
8. **§F44.8 vitest + ko-KR.json + dry-run + wire scope T1~T7** — `apps/web/__tests__/finops/interactive-dashboard-dashboard.test.tsx` (~+650 LOC, **~25-28 NEW vitest cases**) mirroring Phase 26 `cost-anomaly-ml-prediction-dashboard.test.tsx` verbatim pattern (lib types 4 + lib client 11 endpoints 6 + 5 sub-components × ~4 cases each + orchestrator 1 = ~25 NEW vitest cases PASS) + `apps/web/messages/ko-KR.json` EXTENSION **~30 keys** `finops_interactive_dashboard.*` namespace (CR 11-4 D-001~D-005 SSOT + NFR18 ko-KR SSOT + ARIA labels WCAG 2.1 AA + owner-only notice + 2FA 챌린지 mandatory notice + dry-run toggle label) + dry-run mode UI default ON per CR 11-3 honest-DEFER discipline + wire scope T1~T7 verified + tsc 0 NEW + ruff scoped 0 NEW (10 sub-ACs §F44.8.1~§F44.8.10)

**Total sub-ACs**: 12+10+10+10+10+8+8+10 = **78 explicit sub-ACs** with nested bullet points → **~78 detailed sub-ACs** pre-flight 정합 sweep 만족 결정 wire.

### AD-57 신규 결정 (a)~(c) 3 sub-decisions (Epic 28 T2 frontend follow-up PRD entry 진입 시점에 결정 wire 진입 완료)

- (a) Interactive Dashboard UI = 5 NEW sub-components + FinopsInteractiveDashboardPanel orchestrator + 2 RSC pages + capability gate fail-closed 403 (Phase 28 PRD entry 의 §F43.4 의 frontend 결정 wire 정직 회복 — backend `db005e8` 의 4 NEW backend modules + 1 alembic 0058 + 8 audit actions + 16 typed exceptions + capability matrix v1.53 EXTENSION 의 frontend UI surface 신규 진입)
- (b) 2 TS mirrors = CR 12-5 D-PARITY-01 inversion EXTENSION (Python TypedDict parity verbatim mirroring `apps/api/modules/finops/interactive_dashboard/serializers.py` + 11 endpoint fetch functions mirroring `dashboard_router.py` + 7 enums + 6 TypedDicts + 4 constants)
- (c) ko-KR.json finops_interactive_dashboard.* namespace EXTENSION ~30 keys + NFR18 SSOT + dry-run mode UI default ON + Epic 12 2FA 챌린지 mandatory ≥ 10M KRW/year sharing scope (Phase 26 `finops_cost_anomaly_ml_prediction.*` namespace pattern verbatim EXTENSION — `section_title` + `section_description` + `cross_phase_kpi_*` + `saved_view_*` + `drill_down_*` + `export_*` + `sharing_*` + `dry_run_*` + `owner_only_notice` + `two_fa_required_notice` + 7-tab labels + 5-dim weighted aggregation note + 12 pre-defined view template labels + 6 export format labels + 4 sharing scope labels + ARIA labels WCAG 2.1 AA)

## Tasks (cj-style 197 wire sprint scope, declared in PRD entry)

### T1: 5 NEW sub-components

- T1.1 `apps/web/components/finops/interactive-dashboard/CrossPhaseKPIOverview.tsx` NEW ~+280 LOC + 18 KPI tile grid + 5-dim weighted aggregation gauge + `DASHBOARD_KPI_DIMENSION_WEIGHTS` parity + `PHASE_KPI_SOURCE_MODULES` 18-entry dict parity + Recharts 2.12.7 AD-14 stack pin
- T1.2 `apps/web/components/finops/interactive-dashboard/SavedViewManager.tsx` NEW ~+260 LOC + 5 CRUD UI + 12 NEW pre-defined templates dropdown + 7-dim granularity selector + audit-first INSERT 4 NEW
- T1.3 `apps/web/components/finops/interactive-dashboard/DrillDownExplorer.tsx` NEW ~+260 LOC + 6-dim drill-down + 7-dim granularity + breadcrumb navigation + `DrillDownContext` TypedDict parity
- T1.4 `apps/web/components/finops/interactive-dashboard/ExportConfigPanel.tsx` NEW ~+260 LOC + 5 export format radio + 50MB guard + 3 auto-retries + 5-state status + admin email alert + reuse Phase 17/22 EXTENSION
- T1.5 `apps/web/components/finops/interactive-dashboard/DashboardSharingPanel.tsx` NEW ~+260 LOC + 4 sharing scope radio + tenant isolation + RBAC + Epic 12 2FA 챌린지 mandatory

### T2: Orchestrator + 2 RSC pages

- T2.1 `apps/web/components/finops/FinopsInteractiveDashboardPanel.tsx` NEW ~+280 LOC + 5-tab layout orchestrator + dry-run toggle default ON per CR 11-3 honest-DEFER discipline + ko-KR labels
- T2.2 `apps/web/app/[locale]/(dashboard)/admin/finops/interactive-dashboard/page.tsx` NEW ~+50 LOC + RSC boundary + cookies auth + redirect + period_key searchParam + `FinopsInteractiveDashboardPanel` render
- T2.3 `apps/web/app/[locale]/(dashboard)/admin/finops/interactive-dashboard/layout.tsx` NEW ~+30 LOC + data-locale + data-capability="finops_interactive_dashboard" wrapper + ARIA labels WCAG 2.1 AA

### T3: 2 TS mirrors

- T3.1 `apps/web/lib/finops/interactive-dashboard-types.ts` NEW ~+380 LOC + 7 enum exports + 6 TypedDict exports + 4 constant exports + CR 12-5 D-PARITY-01 inversion EXTENSION
- T3.2 `apps/web/lib/finops/interactive-dashboard-client.ts` NEW ~+150 LOC + 11 fetch function exports mirroring `dashboard_router.py` + credentials include + Content-Type JSON

### T4: vitest coverage

- T4.1 `apps/web/__tests__/finops/interactive-dashboard-dashboard.test.tsx` NEW ~+650 LOC + **~25-28 NEW vitest cases** mirroring Phase 26 `cost-anomaly-ml-prediction-dashboard.test.tsx` verbatim pattern (lib types 4 + lib client 6 endpoint tests + 5 sub-components × ~4 cases each + orchestrator 1 case)

### T5: ko-KR.json EXTENSION

- T5.1 `apps/web/messages/ko-KR.json` MODIFIED EXTENSION **~30 NEW keys** `finops_interactive_dashboard.*` namespace (NFR18 ko-KR SSOT + ARIA labels WCAG 2.1 AA + owner-only notice + 2FA 챌린지 mandatory notice + dry-run toggle label)

### T6: dry-run + 2FA 챌린지 + owner-only RBAC

- T6.1 dry-run mode UI default ON per CR 11-3 honest-DEFER discipline + Epic 12 2FA 챌린지 mandatory ≥ 10M KRW/year sharing scope + AD-22 owner-only RBAC + `InteractiveDashboardSharing2FARequiredError` 403 typed exception parity

### T7: 3중 게이트 FINAL CLEAN atomic commit

- T7.1 ruff scoped 0 NEW runtime errors verified via re-run
- T7.2 vitest ~25-28 NEW PASS verified via `pnpm vitest run __tests__/finops/interactive-dashboard-dashboard.test.tsx`
- T7.3 tsc 0 NEW verified via `pnpm tsc --noEmit`
- T7.4 atomic commit via `git commit -F <file>` CR 9-6 D5 prevention + PowerShell here-string 회피

**Subtotal**: 5+3+2+1+1+1+4 = **~17 subtasks** 결정 wire (Phase 26 T1~T8 + ~40 subtasks pattern 의 frontend-only version EXTENSION — alembic/T4 audit_action/T5 capability matrix EXTENSION 모두 cj-193 에서 DONE 진입 정합 보존 → cj-197 T2 frontend only sprint 에서 제거).

## Dev Notes 21종 (CR lessons applied — 20종 preserved + 1 NEW T2-frontend-specific)

- **CR 0-2 RLS verbatim EXTENSION** (Epic 28 wire 의 4 tables + 1 preview table 의 tenant-scoped RLS 자동 적용 current_setting('app.tenant_id')::uuid 보존 + frontend 의 tenant_id ContextVar 보존)
- **CR 1-1 audit-first INSERT 8 NEW** (ActionClass.FINOPS_INTERACTIVE_DASHBOARD 의 8 NEW audit actions — unified_kpi_calculated + saved_view_created/updated/deleted/executed + export_job_started/completed + dashboard_shared)
- **CR 1-1 FastAPI ContextVar middleware layer** 보존 (Epic 28 wire 의 trace_id ContextVar propagation 보존 + frontend 의 period_key searchParam 보존)
- **CR 1-1 RSC boundary** Next.js 15.x RSC boundary 보존 (`apps/web/app/[locale]/(dashboard)/admin/finops/interactive-dashboard/{page,layout}.tsx`)
- **CR 4-3/4-4** (async-test asyncio.run + Industry enum SSOT + A5 drift detector + golden_diff + SDR overclaim 방지)
- **CR 5-1 Decimal precision banker's rounding** 정합 (NUMERIC(18,2) for KRW + NUMERIC(5,4) for percentage ratios + Epic 28 backend wire 의 Decimal precision verbatim EXTENSION)
- **CR 9-6 commit message `git commit -F <file>`** (D5 prevention + PowerShell here-string 회피)
- **CR 11-3 honest-DEFER 90번째** Epic 28 T2 frontend follow-up 결정 wire 진입 (cj-style 193 의 Q2 backend-only sprint 의 T2 frontend honestly DEFER → follow-up sprint 결정 wire 보존)
- **ALLOWED_SERVICE_SUBMODULES 즉시 sweep EXTENSION** — Epic 28 wire 진입 시점에 `apps/api/modules/finops/__init__.py` 의 submodule 목록 즉시 sweep EXTENSION = m28_finops_interactive_dashboard 신규 submodule 등록 (Epic 28 T2 frontend follow-up sprint 에서는 backend 변경 0건 → ALLOWED_SERVICE_SUBMODULES sweep 보존 결정 wire 진입)
- **CR 11-4 D-001~D-005** ko-KR.json `finops_interactive_dashboard.*` namespace EXTENSION ~30 keys SSOT + NFR18 ko-KR SSOT
- **P-015 SSOT** ko-KR.json finops_interactive_dashboard.* 단일 SSOT 결정 wire 진입
- **CR 12-1 L4 industry-agnostic capability grants** (4-industry ✅/✅/✅/✅) EXTENSION 결정 wire 진입 (Epic 28 wire 의 FINOPS_INTERACTIVE_DASHBOARD industry-agnostic grants 보존)
- **CR 12-5 D-14 typed exception envelope** 16 NEW (Epic 28 wire 의 InteractiveDashboardAggregationError + InteractiveDashboardKPIScopeError + InteractiveDashboardKPIPeriodError + InteractiveDashboardKPIModuleError + SavedViewError + SavedViewFilterError + SavedViewTemplateError + SavedViewLimitError + ExportJobError + ExportJobFormatError + ExportJobSizeError + ExportJobTenantError + DashboardSharingError + DashboardSharingScopeError + DashboardSharingExpirationError + DrillDownError = 16 NEW typed exceptions CR 12-5 D-14 envelope 적용 결정 wire 보존)
- **CR 12-5 D-PARITY-01 inversion** TypeScript mirror parity (`interactive-dashboard-types.ts` + `interactive-dashboard-client.ts`) 결정 wire 진입 (cj-style 197 T2 frontend only sprint 의 T3.1 + T3.2 EXTENSION)
- **CR 12-5 D-GATE-01 inversion** capability gate inversion (`require_finops_interactive_dashboard` + fail-closed 403 Forbidden) 결정 wire 진입 (cj-style 193 의 T5.3 EXTENSION)
- **A19 cohesion 9 surface EXTENSION PASS preserved** — Epic 28 T2 frontend follow-up sprint 진입 시점에 Surface 7 (TypeScript mirror) ⚠️ N/A → ✅ EXTENSION + Surface 8 (ko-KR SSOT) ⚠️ N/A → ✅ EXTENSION 결정 wire 진입 (cj-style 193 의 A19 cohesion 9 surface PARTIAL preserved → A19 cohesion 9 surface FULL EXTENSION preserved 결정 wire 보존)
- **A36 SDR 검증 4-step** 자동 적용 결정 wire (PRD entry 진입 시점에 자동)
- **AD-14 stack pin** Recharts 2.12.7 + reportlab 4.0.7 + xlsxwriter 3.1.9 + pandas 2.1.4 + matplotlib 3.8.2 + apscheduler 3.10.4 + pytz 2024.1 + noto-sans-cjk-kr EXTENSION 결정 wire (Epic 28 PRD entry 의 Dev Notes AD-14 verbatim EXTENSION)
- **AD-22 owner-only RBAC** FinopsInteractiveDashboardPanel.tsx orchestrator + 5 sub-components + 2 RSC pages 모두 owner-only RBAC EXTENSION 결정 wire (CrossPhaseKPIOverview + SavedViewManager + DrillDownExplorer + ExportConfigPanel + DashboardSharingPanel + sharing grants 모두 owner-only)
- **Epic 12 2FA 챌린지 mandatory** destructive endpoint 의 3-layer defense EXTENSION 결정 wire (sharing scope=cross_tenant + 100+ saved views + ≥ 10M KRW/year impact → RFC 6238 TOTP + tenant_owner approval chain + Slack DM + 2FA 미설정 redirect + InteractiveDashboardSharing2FARequiredError 403 typed exception)
- **NFR4 PII minimization ✅ PRESERVED** (Epic 28 wire 결정 wire 시 PII minimization 자동 보존 → Epic 28 T2 frontend follow-up sprint 진입 시에도 PII minimization 보존)
- **NFR18 ko-KR SSOT** apps/web/messages/ko-KR.json finops_interactive_dashboard.* namespace EXTENSION ~30 keys SSOT 보존 결정 wire
- **AD-50 + AD-51 + AD-52 + AD-53 + AD-54 + AD-55 + AD-56 + AD-57 신규** AD-50/51/52/53 (Phase 22~25 a~g 7 sub-decisions) + AD-54 (audit-fixes sprint cj-style 176 honest recovery SSOT) + AD-55 (Phase 26 a~g 7 sub-decisions) + AD-56 (Epic 28 wire a~g 7 sub-decisions) + **AD-57 신규 (Epic 28 T2 frontend follow-up PRD entry a~c 3 sub-decisions)** = 8 ADs 신규 결정 wire 진입 (cj-style 191 의 AD-50/51/52/53/54/55 + cj-style 193 의 AD-56 + **cj-style 195 의 AD-57 EXTENSION 결정 wire 진입**)
- **NEW: Epic 28 T2 frontend follow-up sprint = cj-style 195번째 follow-up sprint (Phase 28 backend-only wire Q2 honestly DEFER 회복)**: T2 frontend dashboard UI + 5 NEW sub-components + 2 RSC pages + 2 TS mirrors + vitest ~25-28 NEW cases + ko-KR.json EXTENSION ~30 keys `finops_interactive_dashboard.*` namespace 결정 wire 진입 = CR 11-3 honest-DEFER 90번째 epic 연속 정직 회복 + Surface 7 (TypeScript mirror) ⚠️ N/A → ✅ EXTENSION + Surface 8 (ko-KR SSOT) ⚠️ N/A → ✅ EXTENSION 결정 wire 보존

## Architecture Alignment (ALLOWED sweep) — Epic 28 PRD entry 정합

- **Frontend (Next.js 15.x, TypeScript 5.x)** — Epic 28 T2 frontend follow-up sprint 진입 시점에 신규 결정 wire 진입:
  - 2 NEW `apps/web/app/[locale]/(dashboard)/admin/finops/interactive-dashboard/{page,layout}.tsx` (~+80 LOC)
  - 1 NEW `apps/web/components/finops/FinopsInteractiveDashboardPanel.tsx` (~+280 LOC, 5-tab layout orchestrator)
  - 5 NEW `apps/web/components/finops/interactive-dashboard/{CrossPhaseKPIOverview,SavedViewManager,DrillDownExplorer,ExportConfigPanel,DashboardSharingPanel}.tsx` (~+1,320 LOC, 250-280 LOC each)
  - 2 NEW `apps/web/lib/finops/interactive-dashboard-{types,client}.ts` (~+530 LOC, types ~+380 + client ~+150)
  - 1 NEW `apps/web/__tests__/finops/interactive-dashboard-dashboard.test.tsx` (~+650 LOC, ~25-28 NEW vitest cases)
  - MODIFIED `apps/web/messages/ko-KR.json` EXTENSION ~30 keys `finops_interactive_dashboard.*` namespace
- **Backend (FastAPI, Python 3.12)** — Epic 28 T2 frontend follow-up sprint 진입 시점에 변경 0건 (cj-style 193 의 Q2 backend-only sprint 의 T1~T8 결정 wire 보존):
  - Epic 28 wire 의 4 NEW backend modules + 1 alembic 0058 + 8 audit actions + 16 typed exceptions + capability matrix v1.53 EXTENSION 모두 보존 (cj-style 193 결정 wire 진입 정합)
- **Tests**:
  - ~+25-28 NEW vitest PASS (Phase 26 pattern verbatim mirror — lib types 4 + lib client 6 + 5 sub-components × ~4 + orchestrator 1 = ~25 NEW vitest cases PASS)
  - 0 NEW pytest + 0 NEW ruff + 0 NEW tsc + 0 regressions 결정 wire 보존
- **Docs (cumulative; wire sprint will write)**:
  - PRD file (this file) NEW ~+218 LOC (verbatim mirroring cj-191 PRD entry `phase-28-finops-interactive-dashboard-prd.md` LOC)
  - Handoff memory NEW
  - Commit-msg NEW
  - Sprint-status MODIFIED v4.02 → v4.03
  - MEMORY.md MODIFIED hook EXTENSION

## Files Affected (estimate ~14-16 files = 12 NEW + 3-4 MODIFIED, **wire sprint scope**) — **PRD entry sprint 5 files = 3 NEW + 2 MODIFIED**

### PRD entry sprint (cj-style 195, this sprint) — 5 files = 3 NEW + 2 MODIFIED (cj-style 191 verbatim mirror)

1. NEW: `_bmad-output/implementation-artifacts/phase-28-t2-frontend-follow-up-prd.md` (this file, ~+218 LOC)
2. NEW: `memory/handoff-2026-08-29-phase-28-t2-frontend-follow-up-prd-entry-done.md`
3. NEW: `_bmad-output/implementation-artifacts/commit-msg-cj-195.txt`
4. MODIFIED: `_bmad-output/implementation-artifacts/sprint-status.yaml` (v4.02 → v4.03 EXTENSION)
5. MODIFIED: `memory/MEMORY.md` (Epic 28 T2 frontend follow-up PRD entry hook EXTENSION)

### Spec entry sprint (cj-style 196, future) — estimated ~5 files = 3 NEW + 2 MODIFIED (Epic 28 spec entry `5f29a56` 의 ~5 files pattern verbatim EXTENSION)

### Wire sprint (cj-style 197, future) — estimated ~14-16 files = 12 NEW + 3-4 MODIFIED (Epic 28 wire `db005e8` 의 ~20 files pattern 의 frontend-only version EXTENSION → smaller scope 결정 wire 진입)
- Frontend: 5 NEW sub-components (~+1,320 LOC) + 1 NEW Client component (~+280 LOC) + 2 NEW RSC pages (~+80 LOC) + 2 NEW TS mirrors (~+530 LOC) + 1 NEW vitest (~+650 LOC) + 1 MODIFIED ko-KR.json (~+30 keys) = 12 NEW + 1 MODIFIED
- Tests: ~+25-28 NEW vitest PASS (frontend-only sprint 이므로 pytest 0 NEW + ruff scoped 0 NEW + tsc 0 NEW)
- Docs: 1 NEW commit-msg + 1 NEW handoff memory + 1 MODIFIED sprint-status + 1 MODIFIED MEMORY.md = 2 NEW + 2 MODIFIED
- = ~14-15 files = 12 NEW + 3-4 MODIFIED

### Retro sprint (cj-style 198, future) — estimated ~4 files = 3 NEW + 1 MODIFIED (Epic 28 retro `epic-28-retro-2026-08-29.md` 의 ~4 files pattern verbatim EXTENSION)

(Actual sprint file counts will be verified at wire time via `git show --stat HEAD`.)

## 3중 게이트 impact

- **cj 195 (this sprint, docs-only)**: ruff scoped 0 NEW / pytest 0 NEW / vitest 0 NEW / tsc 0 NEW (apps/api backend 변경 0건 + apps/web frontend 변경 0건 = docs only 변경)
- **cj 196 (spec entry sprint, docs-only)**: ruff scoped 0 NEW / pytest 0 NEW / vitest 0 NEW / tsc 0 NEW
- **cj 197 (wire sprint, frontend-only)**: ruff scoped 0 NEW / pytest 0 NEW / vitest ~+25-28 NEW PASS / tsc 0 NEW
- **cj 198 (retro sprint, docs-only)**: ruff scoped 0 NEW / pytest 0 NEW / vitest 0 NEW / tsc 0 NEW

## A795~A799 5 NEW 결정 wire (cj-style 195번째)

- **A795**: 옵션 (a) Epic 28 T2 frontend follow-up PRD entry 진입 결정 wire (rationale 5종: ① cj-style discipline 회피 위험 방지 = 194번째 Epic 28 close-out retro 진입 직후 자연스러운 T2 frontend follow-up PRD entry 진입 결정 wire ② Epic 28 close-out retro cj-style 194번째 진입 직후 자연스러운 T2 frontend follow-up sprint 진입 = 195번째 진입 결정 wire ③ Epic 28 PRD entry cj-style 191번째 + spec entry cj-style 192번째 + atomic wire Q2 backend-only cj-style 193번째 + close-out retro cj-style 194번째 의 4-entry-point cycle 진입 정합 보존 + Epic 28 retro §12 옵션 (a) "T2 frontend follow-up sprint 진입 결정 wire (cj-style 195번째)" verbatim 진입 + Epic 28 retro §14 Action Items #1 "T2 frontend follow-up sprint 진입 결정 wire" verbatim 진입 + Epic 28 wire cj-style 193 의 Q2 결정 wire 의 honestly DEFER 회복 정직 회복 결정 wire ④ Epic 28 wire `db005e8` 의 4 NEW backend modules (cross_phase_aggregator + saved_view_engine + export_pipeline + dashboard_router) 의 frontend UI surface 신규 진입 = Epic 28 wire 의 backend ledger data 활용 → 새 frontend infra 불필요 + reuse 최대화 + risk 최소화 + 비즈니스 가치 최고 (executive dashboard surface = 비용 통제 layer 직접적 ROI) + 4-industry grants ✅/✅/✅/✅ 보존 + Phase 26 dashboard UI extension `fbc6f42` (cj-style 186번째) 의 5 sub-component + 2 RSC page + 2 TS mirror + vitest 28 NEW cases pattern verbatim 미러 ⑤ Epic 1~17 + Phase 3~28 + Phase 19.5 + Phase 20.5 + audit-fixes + 1st release cycle 정합 보존)
- **A796**: PRD 파일 생성 결정 wire (`_bmad-output/implementation-artifacts/phase-28-t2-frontend-follow-up-prd.md` ~+218 LOC + baseline_commit `db005e8` + cj_style_entry_point 195 + status `backlog` + story_key `phase-28-t2-frontend-follow-up-prd` + 8 ACs §F44.1~§F44.8 verbatim → ~78 detailed sub-ACs (12+10+10+10+10+8+8+10) pre-flight 정합 sweep 만족 + T1~T7 + ~17 subtasks + Dev Notes 21종 + Architecture Alignment ALLOWED sweep + Files Affected ~14-16 files estimate (~12 NEW + ~3-4 MODIFIED))
- **A797**: 8 ACs §F44.1~§F44.8 verbatim → ~78 sub-ACs 전개 결정 wire (§F44.1 CrossPhaseKPIOverview 12 sub-ACs + §F44.2 SavedViewManager 10 sub-ACs + §F44.3 DrillDownExplorer 10 sub-ACs + §F44.4 ExportConfigPanel 10 sub-ACs + §F44.5 DashboardSharingPanel 10 sub-ACs + §F44.6 2 RSC pages + capability gate 8 sub-ACs + §F44.7 2 TS mirrors + Python TypedDict parity 8 sub-ACs + §F44.8 vitest + ko-KR.json + dry-run + wire scope T1~T7 10 sub-ACs = ~78 sub-ACs pre-flight 정합 sweep 만족)
- **A798**: Tasks T1~T7 + ~17 subtasks 결정 wire (T1 5 NEW sub-components 5 subtasks + T2 Orchestrator + 2 RSC pages 3 subtasks + T3 2 TS mirrors 2 subtasks + T4 vitest coverage 1 subtask + T5 ko-KR.json EXTENSION 1 subtask + T6 dry-run + 2FA 챌린지 + owner-only RBAC 1 subtask + T7 3중 게이트 FINAL CLEAN atomic commit 4 subtasks = ~17 subtasks)
- **A799**: sprint-status v4.02 → v4.03 EXTENSION + atomic commit via `git commit -F <file>` CR 9-6 D5 prevention + commit-msg-cj-195.txt 신규 + handoff memory 신규 + MEMORY.md hook EXTENSION + **5 files = 3 NEW + 2 MODIFIED atomic single sprint** (cj-style 191 PRD entry 의 5 files = 3 NEW + 2 MODIFIED pattern verbatim 미러) 결정 wire 진입 완료 보존.

## CR lessons applied 21종

CR 0-2 RLS verbatim EXTENSION (4 tables + 1 preview table tenant-scoped RLS) + CR 1-1 audit-first INSERT 8 NEW (ActionClass.FINOPS_INTERACTIVE_DASHBOARD 의 8 NEW audit actions) + CR 1-1 FastAPI ContextVar + CR 1-1 RSC boundary Next.js 15.x + CR 4-3/4-4 (async-test + Industry enum SSOT + A5 drift detector + golden_diff + SDR overclaim 방지) + CR 5-1 Decimal precision banker's rounding 정합 (NUMERIC(18,2) KRW + NUMERIC(5,4) percentage ratios) + CR 9-6 commit message `git commit -F <file>` + CR 11-3 honest-DEFER 90번째 Epic 28 T2 frontend follow-up 진입 + ALLOWED_SERVICE_SUBMODULES 보존 (Epic 28 wire 의 m28_finops_interactive_dashboard 신규 submodule 등록 보존 + cj-195 frontend sprint 에서는 backend 변경 0건) + CR 11-4 D-001~D-005 ko-KR.json `finops_interactive_dashboard.*` namespace EXTENSION ~30 keys SSOT + NFR18 ko-KR SSOT + P-015 SSOT + CR 12-1 L4 industry-agnostic capability matrix v1.53 FINOPS_INTERACTIVE_DASHBOARD 4-industry grants ✅/✅/✅/✅ 보존 + CR 12-5 D-14 typed exception envelope 16 NEW 보존 + CR 12-5 D-PARITY-01 inversion TypeScript mirror parity `interactive-dashboard-types.ts` + `interactive-dashboard-client.ts` (cj-style 197 T3.1 + T3.2 EXTENSION) + CR 12-5 D-GATE-01 inversion capability gate inversion `require_finops_interactive_dashboard` + fail-closed 403 Forbidden + A19 cohesion 9 surface EXTENSION PARTIAL → FULL preserved (Surface 7 + Surface 8 EXTENSION) + A36 SDR 검증 4-step 자동 적용 + AD-14 stack pin Recharts 2.12.7 + reportlab 4.0.7 + xlsxwriter 3.1.9 + pandas 2.1.4 + matplotlib 3.8.2 + apscheduler 3.10.4 + pytz 2024.1 + noto-sans-cjk-kr EXTENSION 결정 wire 진입 + AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory ≥ 10M KRW/year sharing scope EXTENSION + NFR4 PII minimization ✅ PRESERVED + NFR18 ko-KR SSOT + AD-50 + AD-51 + AD-52 + AD-53 + AD-54 + AD-55 + AD-56 + **AD-57 신규** (Epic 28 T2 frontend follow-up PRD entry 진입 결정 wire 진입 완료).

## D-DEFER-* honestly 결정 wire 보존

- D-1-1-DEFER-1/2/3 + D-EPIC-16-REVIEW-DEFER-1/2~6 + D-PHASE-4-DR-DEFER-1/2 + D-EPIC-17-WIRE-DEFER-T2-T3-UI + D-RETENTION-1 + D-OBSERVABILITY-1 + D-PERFORMANCE-1 + D-CHAOS-1 + D-SLO-1 + D-FINOPS-1~14 모두 ✅ ALL RESOLVED 보존
- **D-FINOPS-15 신규 honestly DEFER 보존** — Epic 28 PRD entry (cj-style 191) 진입 시점에 carry-over chain 정직 회복 결정 wire 진입 + Epic 28 T2 frontend follow-up PRD entry (cj-style 195) 진입 시점에 T2 frontend honestly DEFER 회복 결정 wire 진입 + Phase 22~28 retroactive correction honestly DEFER 보존 + 8 items 모두 별도 sprint honestly DEFER 보류 결정 wire 보존 (multi-modal cost input aggregation vision/NLP/receipt OCR feed + causal inference root cause analysis for cost spikes + LLM 기반 cost anomaly explanation auto-narrative + automated cost remediation Phase 14 optimization auto-apply dashboard-detected issues + cross-tenant federated cost benchmarking privacy-preserving + cost optimization marketplace 3rd-party cost reduction services + real-time streaming cost prediction sub-second latency + unsupervised online learning for cost anomaly detection model update without retraining)
- **Phase 28 atomic wire Q2 backend-only sprint = T2 frontend honestly DEFER → 별도 follow-up sprint 결정 wire 보존** (Epic 28 wire cj-style 193 의 Q2 결정 wire)
- **Epic 28 T2 frontend follow-up PRD entry = T2 frontend honestly DEFER 회복 정직 회복 결정 wire 진입 완료** (cj-style 195 번째 결정 wire)
- D-LAUNCH-1-DEFER-1 honestly preserved 65~195번째

## Epic 1~17 + Phase 3~28 + Phase 19.5 + Phase 20.5 + audit-fixes + 1st release cycle 정합 보존

cj-style 195번째 epic 연속 정직 회복 진입 시점에 pre-flight 정합 sweep 만족 결정 wire 보존:

- Epic 28 close-out retro (cj-style 194번째) DONE 진입 정합 보존
- Phase 28 atomic wire Q2 backend-only `db005e8` (cj-style 193번째) DONE 진입 정합 보존
- Phase 28 spec entry `5f29a56` (cj-style 192번째) DONE 진입 정합 보존
- Phase 28 PRD entry `62b2e32` (cj-style 191번째) DONE 진입 정합 보존
- Phase 25 extra=forbid 조이기 source sprint `232fc49` (cj-style 190번째) DONE 진입 정합 보존
- Phase 21~26 Layer 2 P1 + Layer 3 P2 carry-over `d38f388` (cj-style 189번째) DONE 진입 정합 보존
- Phase 27 Layer 2 P1 + Layer 3 P2 carry-over `836a8d4` (cj-style 188번째) DONE 진입 정합 보존
- Phase 26 vitest frontend test `2dd9744` (cj-style 187번째) DONE 진입 정합 보존
- Phase 26 dashboard UI extension `fbc6f42` (cj-style 186번째) DONE 진입 정합 보존
- Phase 26 cj-182 close-out retro (cj-style 185번째) DONE 진입 정합 보존
- Phase 26 capability matrix extension (cj-style 184번째) DONE 진입 정합 보존
- Phase 26 atomic wire `0cf2547` (cj-style 183번째) DONE 진입 정합 보존
- Phase 26 spec entry `36efc71` (cj-style 182번째) DONE 진입 정합 보존
- Phase 26 PRD entry `b95ebc3` (cj-style 181번째) DONE 진입 정합 보존
- audit-fixes sprint close-out retro (cj-style 178번째) DONE 진입 정합 보존
- audit-fixes sprint retroactive correction (cj-style 177 follow-up) DONE 진입 정합 보존
- audit-fixes sprint wire (cj-style 176번째) DONE 진입 정합 보존
- audit-fixes sprint entry (cj-style 166번째) DONE 진입 정합 보존
- Phase 25 close-out retro `6119791` (cj-style 175번째) DONE 진입 정합 보존
- Phase 25 integration follow-up `1fc8302` (cj-style 174 follow-up) DONE 진입 정합 보존
- Phase 25 wire `de1b69d` (cj-style 173번째) DONE 진입 정합 보존
- Phase 25 spec entry `5e8d435` (cj-style 172번째) DONE 진입 정합 보존
- Phase 25 PRD entry `5e8d435` (cj-style 171번째) DONE 진입 정합 보존
- Phase 24 close-out retro retroactive correction `1f30b64` (cj-style 170 follow-up) DONE 진입 정합 보존
- Phase 24 close-out retro `c14199b` (cj-style 170번째) DONE 진입 정합 보존
- Phase 24 wire retroactive correction `69c5e28` (cj-style 169 follow-up) DONE 진입 정합 보존
- Phase 24 wire `615d478` (cj-style 169번째) DONE 진입 정합 보존
- Phase 24 spec entry `b3c6c7c` (cj-style 168번째) DONE 진입 정합 보존
- Phase 24 PRD entry `278f37f` (cj-style 167번째) DONE 진입 정합 보존
- Phase 23 close-out retro `7875ac9` (cj-style 165번째) DONE 진입 정합 보존
- Phase 23 wire retroactive correction `948ff35` (cj-style 164 follow-up) DONE 진입 정합 보존
- Phase 23 atomic wire `f850d0e` (cj-style 164번째) DONE 진입 정합 보존
- Phase 23 spec entry `960d060` (cj-style 163번째) DONE 진입 정합 보존
- Phase 23 PRD entry `2abfdd9` (cj-style 162번째) DONE 진입 정합 보존
- Phase 22 close-out retro `c5726ff` (cj-style 161번째) DONE 진입 정합 보존
- Phase 22 wire retroactive correction `9dbffc5` (cj-style 160 follow-up) DONE 진입 정합 보존
- Phase 22 atomic wire `7acbac0` (cj-style 160번째) DONE 진입 정합 보존
- Phase 22 spec entry `585c53a` (cj-style 159번째) DONE 진입 정합 보존
- Phase 22 PRD entry `64760fe` (cj-style 158번째) DONE 진입 정합 보존
- Phase 11~20 audit-fixes-infrastructure sprint (cj-style 157번째) DONE 진입 정합 보존
- Phase 11~20 audit-fixes Layer 3 P2 docs backfill sprint (cj-style 156번째) DONE 진입 정합 보존
- Phase 11~20 audit-fixes Layer 2 P1 test backfill sprint (cj-style 155번째) DONE 진입 정합 보존
- Phase 11~20 audit-fixes sprint (cj-style 154번째) DONE 진입 정합 보존
- Phase 21 audit-fixes sprint (cj-style 153번째) DONE 진입 정합 보존
- Phase 21 close-out retro (cj-style 152번째) DONE 진입 정합 보존
- Phase 21 atomic wire (cj-style 151번째) DONE 진입 정합 보존
- Phase 21 spec entry (cj-style 150번째) DONE 진입 정합 보존
- Phase 21 PRD entry (cj-style 149번째) DONE 진입 정합 보존
- Phase 20.5 close-out retro (cj-style 148번째) DONE 진입 정합 보존
- Phase 20.5 atomic wire `46ddcc5` (cj-style 147번째) DONE 진입 정합 보존
- Phase 20.5 spec entry (cj-style 146번째) DONE 진입 정합 보존
- Phase 20 close-out retro (cj-style 145번째) DONE 진입 정합 보존
- Phase 20 atomic wire (cj-style 144번째) DONE 진입 정합 보존
- Phase 20 spec entry (cj-style 143번째) DONE 진입 정합 보존
- Phase 20 PRD entry (cj-style 142번째) DONE 진입 정합 보존
- Phase 19.5 carry-over 결정 wire (cj-style 141번째) DONE 진입 정합 보존
- Phase 19 close-out retro (cj-style 140번째) + Phase 19 atomic wire (cj-style 139번째) + Phase 19 spec entry (cj-style 138번째) + Phase 19 PRD entry (cj-style 137번째) + Phase 18 close-out retro (cj-style 136번째) + Phase 18 atomic wire (cj-style 135번째) + Phase 18 spec entry (cj-style 134번째) + Phase 18 PRD entry (cj-style 133번째) + Phase 17 close-out retro (cj-style 132번째) + Phase 17 atomic wire (cj-style 131번째) + Phase 17 spec entry (cj-style 130번째) + Phase 17 PRD entry (cj-style 129번째) + Phase 16 close-out retro (cj-style 128번째) + Phase 16 atomic wire (cj-style 127번째) + Phase 16 spec entry (cj-style 126번째) + Phase 16 PRD entry (cj-style 125번째) + Phase 15 close-out retro (cj-style 124번째) + Phase 15 atomic wire (cj-style 123번째) + Phase 15 spec entry (cj-style 122번째) + Phase 15 PRD entry (cj-style 121번째) + Epic 1~17 ALL DONE 진입 정합 보존 + 1st release cycle ALL DONE 진입 정합 보존
- Phase 11~28 19-capability FinOps territory chain ✅ ALL WIRED INTEGRATED 진입 정합 보존 (Phase 11~27 18-capability + Phase 28 신규)
