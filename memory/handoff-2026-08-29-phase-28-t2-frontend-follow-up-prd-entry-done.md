---
name: handoff-2026-08-29-phase-28-t2-frontend-follow-up-prd-entry-done
description: Epic 28 T2 frontend follow-up PRD entry DONE (cj-style 195th). 5 files = 3 NEW + 2 MODIFIED atomic docs-only sprint. Epic 28 wire Q2 backend-only honestly DEFER 회복 = CR 11-3 honest-DEFER 90번째 epic 연속 정직 회복. T2 frontend dashboard UI + 5 NEW sub-components + 2 RSC pages + 2 TS mirrors + vitest ~25-28 NEW + ko-KR.json EXTENSION ~30 keys finops_interactive_dashboard.* namespace.
metadata:
  type: project
  cycle: cj-style-195
  phase: phase-28-t2-frontend-follow-up-prd-entry
  baseline_commit: db005e8
---

# Epic 28 T2 frontend follow-up PRD entry DONE (cj-style 195번째)

옵션 (b) 진입 결정 wire — cj-style 194 (Epic 28 close-out retro) 의 §12 옵션 (b) /
§14 Action Items #1 verbatim 회복 (retro commit-msg 의 next-line 옵션 (b) =
T2 frontend follow-up sprint 결정 wire 진입). Phase 28 atomic wire Q2
backend-only sprint `db005e8` (cj-style 193번째) 의 honestly DEFER 보존 결정
wire 회복 정직 회복 = **CR 11-3 honest-DEFER 90번째 epic 연속 정직 회복**.

## Verified actual scope (atomic single sprint)

**5 files = 3 NEW + 2 MODIFIED** (atomic single sprint 의 docs only 변경):

3 NEW:
1. `_bmad-output/implementation-artifacts/phase-28-t2-frontend-follow-up-prd.md`
   (~+220 LOC, 8 ACs §F44.1~§F44.8 verbatim → ~78 sub-ACs pre-flight 정합 sweep 만족).
2. `_bmad-output/implementation-artifacts/commit-msg-cj-195.txt`.
3. `memory/handoff-2026-08-29-phase-28-t2-frontend-follow-up-prd-entry-done.md` (this file).

2 MODIFIED:
1. `_bmad-output/implementation-artifacts/sprint-status.yaml` v4.02 → v4.03 EXTENSION
   (action_items A791~A795 + last_updated_note_v4_03).
2. `memory/MEMORY.md` (hook EXTENSION).

## Epic 28 T2 frontend follow-up territory 결정 wire

T2 frontend dashboard UI surface 신규 진입 결정 wire = Epic 28 wire `db005e8` 의
4 NEW backend modules (cross_phase_aggregator + saved_view_engine +
export_pipeline + dashboard_router) 의 frontend UI surface 신규 진입 결정 wire:

### §F44.1 CrossPhaseKPIOverview sub-component (12 sub-ACs)

18 KPI tile grid (Phase 11~28 18 unified KPIs) + 5-dim weighted aggregation gauge
(cost 0.30 + usage 0.20 + performance 0.20 + compliance 0.15 + sla 0.15) +
`DASHBOARD_KPI_DIMENSION_WEIGHTS` constant parity + `PHASE_KPI_SOURCE_MODULES`
18-entry dict parity + `INTERACTIVE_DASHBOARD_ENGINE_VERSION` engine version display
+ Recharts 2.12.7 AD-14 stack pin.

### §F44.2 SavedViewManager sub-component (10 sub-ACs)

5 CRUD UI (create / read / update / delete / execute) + 12 NEW pre-defined view
templates dropdown (CostByCloudProvider + CostByService + CostByCostCenter +
CostByDepartment + CostByBusinessUnit + CostByTag + SavingsByOptimizationType +
CommitmentUtilizationByCloud + BudgetVarianceByPeriod + SustainabilityByCloudProvider +
VendorSpendByCategory + ReservedInstanceUtilizationByTier) + 7-dim granularity
selector (minute/hour/day/week/month/quarter/year) + max_saved_views_per_tenant=50 +
cache TTL 5 minutes + audit-first INSERT 4 NEW (saved_view_created/updated/deleted/executed).

### §F44.3 DrillDownExplorer sub-component (10 sub-ACs)

6-dim drill-down (tenant/cost_center/department/business_unit/tag/cloud_provider/service) +
breadcrumb navigation + period_key selector + `DrillDownContext` TypedDict parity +
`DrillDownDimension` 7-value enum parity + `DrillDownGranularity` 7-value enum parity +
`DrillDownError` 500 typed exception parity.

### §F44.4 ExportConfigPanel sub-component (10 sub-ACs)

5 export format radio (pdf + xlsx + csv + json + png) + max_export_size 50MB guard display
+ 3 auto-retries indicator + 5-state status lifecycle (pending + in_progress + completed
+ failed + cancelled) + `ExportFormat` enum parity + `ExportJobStatus` enum parity +
admin email alert on failure + reuse Phase 17 sustainability report generator (PDF) +
Phase 22 chargeback invoice generator (XLSX) EXTENSION.

### §F44.5 DashboardSharingPanel sub-component (10 sub-ACs)

4 sharing scope radio (private + tenant + tenant_owner + cross_tenant) + tenant isolation
enforcement + RBAC: only tenant_owner can grant `cross_tenant` scope + sharing expires
default 30 days + Slack DM notification + Epic 12 2FA 챌린지 mandatory for high-value grants
(sharing scope=cross_tenant + 100+ saved views + ≥10M KRW/year impact) +
`DashboardSharingScope` enum parity + `DashboardSharingError` 500 +
`DashboardSharingScopeError` 403 + `DashboardSharingExpirationError` 400 typed exceptions parity.

### §F44.6 2 RSC pages + capability gate (8 sub-ACs)

`apps/web/app/[locale]/(dashboard)/admin/finops/interactive-dashboard/page.tsx` (~+50 LOC) +
layout.tsx (~+30 LOC) + `require_finops_interactive_dashboard` capability gate fail-closed
403 Forbidden + CR 1-1 RSC boundary (Server Component handles locale + RBAC + cookies auth
check via access token + period_key searchParam + `redirect` to `/{locale}/login` on missing
token) + Client Component handles interactive state + ARIA labels WCAG 2.1 AA +
`(dashboard)` route group 보호 EXTENSION.

### §F44.7 2 TS mirrors + Python TypedDict parity (8 sub-ACs)

`apps/web/lib/finops/interactive-dashboard-types.ts` (~+380 LOC mirroring
`apps/api/modules/finops/interactive_dashboard/serializers.py` verbatim) +
7 enum exports (`KPIRefreshCadence` 6-value realtime/hourly/daily/weekly/monthly/on_demand +
`ExportFormat` 5-value pdf/xlsx/csv/json/png + `DashboardSharingScope` 4-value
private/tenant/tenant_owner/cross_tenant + `DashboardLayout` 3-value grid/masonry/tabs +
`DrillDownDimension` 7-value tenant/cost_center/department/business_unit/tag/cloud_provider/service +
`DrillDownGranularity` 7-value minute/hour/day/week/month/quarter/year +
`ExportJobStatus` 5-value pending/in_progress/completed/failed/cancelled) +
6 TypedDict exports (`UnifiedKPI` 24-field + `KPIBreakdown` 8-field +
`DrillDownContext` 6-field + `SavedView` 14-field + `ExportJob` 12-field +
`SharingGrant` 8-field) + 4 constant exports (`DASHBOARD_KPI_DIMENSION_WEIGHTS` +
`DASHBOARD_CADENCE_HOURS_KST` + `DASHBOARD_RECIPIENT_TEMPLATES` +
`INTERACTIVE_DASHBOARD_ENGINE_VERSION`) +
`apps/web/lib/finops/interactive-dashboard-client.ts` (~+150 LOC mirroring 11 endpoints
from `dashboard_router.py`) + 11 fetch function exports (`fetchHealthcheck` +
`createSavedView` + `readSavedView` + `updateSavedView` + `deleteSavedView` +
`executeSavedView` + `computeUnifiedKPI` + `startExportJob` + `getExportJobStatus` +
`shareDashboard` + `listPredefinedTemplates`) + CR 12-5 D-PARITY-01 inversion EXTENSION.

### §F44.8 vitest + ko-KR.json + dry-run + wire scope T1~T7 (10 sub-ACs)

`apps/web/__tests__/finops/interactive-dashboard-dashboard.test.tsx` (~+650 LOC,
**~25-28 NEW vitest cases**) mirroring Phase 26
`cost-anomaly-ml-prediction-dashboard.test.tsx` verbatim pattern (lib types 4 +
lib client 11 endpoints 6 + 5 sub-components × ~4 cases each + orchestrator 1 =
~25 NEW vitest cases PASS) + `apps/web/messages/ko-KR.json` EXTENSION **~30 keys**
`finops_interactive_dashboard.*` namespace (CR 11-4 D-001~D-005 SSOT + NFR18
ko-KR SSOT + ARIA labels WCAG 2.1 AA + owner-only notice + 2FA 챌린지 mandatory
notice + dry-run toggle label) + dry-run mode UI default ON per CR 11-3
honest-DEFER discipline + wire scope T1~T7 verified + tsc 0 NEW + ruff scoped 0 NEW.

## AD-57 신규 (a)~(c) 3 sub-decisions

(a) Interactive Dashboard UI = 5 NEW sub-components + FinopsInteractiveDashboardPanel
    orchestrator + 2 RSC pages + capability gate fail-closed 403 (Phase 28 PRD entry 의
    §F43.4 의 frontend 결정 wire 정직 회복 — backend `db005e8` 의 4 NEW backend modules
    + 1 alembic 0058 + 8 audit actions + 16 typed exceptions + capability matrix v1.53
    EXTENSION 의 frontend UI surface 신규 진입).
(b) 2 TS mirrors = CR 12-5 D-PARITY-01 inversion EXTENSION (Python TypedDict parity
    verbatim mirroring `apps/api/modules/finops/interactive_dashboard/serializers.py`
    + 11 endpoint fetch functions mirroring `dashboard_router.py` + 7 enums + 6 TypedDicts
    + 4 constants).
(c) ko-KR.json finops_interactive_dashboard.* namespace EXTENSION ~30 keys + NFR18 SSOT
    + dry-run mode UI default ON + Epic 12 2FA 챌린지 mandatory ≥ 10M KRW/year sharing
    scope (Phase 26 `finops_cost_anomaly_ml_prediction.*` namespace pattern verbatim
    EXTENSION).

## CR lessons applied 21종

- CR 0-2 RLS verbatim EXTENSION (Epic 28 wire 의 4 tables + 1 preview table tenant-scoped
  RLS 자동 적용 current_setting('app.tenant_id')::uuid 보존 + frontend 의 tenant_id
  ContextVar 보존).
- CR 1-1 audit-first INSERT 8 NEW (ActionClass.FINOPS_INTERACTIVE_DASHBOARD 의 8 NEW
  audit actions — unified_kpi_calculated + saved_view_created/updated/deleted/executed +
  export_job_started/completed + dashboard_shared).
- CR 1-1 FastAPI ContextVar middleware layer 보존 (Epic 28 wire 의 trace_id ContextVar
  propagation 보존 + frontend 의 period_key searchParam 보존).
- CR 1-1 RSC boundary Next.js 15.x RSC boundary 보존
  (`apps/web/app/[locale]/(dashboard)/admin/finops/interactive-dashboard/{page,layout}.tsx`).
- CR 4-3/4-4 (async-test asyncio.run + Industry enum SSOT + A5 drift detector + golden_diff
  + SDR overclaim 방지).
- CR 5-1 Decimal precision banker's rounding 정합 (NUMERIC(18,2) for KRW + NUMERIC(5,4)
  for percentage ratios + Epic 28 backend wire 의 Decimal precision verbatim EXTENSION).
- CR 9-6 commit message `git commit -F <file>` (D5 prevention + PowerShell here-string 회피).
- CR 11-3 honest-DEFER 90번째 Epic 28 T2 frontend follow-up 결정 wire 진입 (cj-style 193 의
  Q2 backend-only sprint 의 T2 frontend honestly DEFER → follow-up sprint 결정 wire 보존).
- ALLOWED_SERVICE_SUBMODULES 즉시 sweep EXTENSION — Epic 28 wire 진입 시점에
  `apps/api/modules/finops/__init__.py` 의 submodule 목록 즉시 sweep EXTENSION =
  m28_finops_interactive_dashboard 신규 submodule 등록 (Epic 28 T2 frontend follow-up
  sprint 에서는 backend 변경 0건 → ALLOWED_SERVICE_SUBMODULES sweep 보존 결정 wire 진입).
- CR 11-4 D-001~D-005 ko-KR.json `finops_interactive_dashboard.*` namespace EXTENSION
  ~30 keys SSOT + NFR18 ko-KR SSOT.
- P-015 SSOT ko-KR.json finops_interactive_dashboard.* 단일 SSOT 결정 wire 진입.
- CR 12-1 L4 industry-agnostic capability grants (4-industry ✅/✅/✅/✅) EXTENSION 결정 wire
  진입 (Epic 28 wire 의 FINOPS_INTERACTIVE_DASHBOARD industry-agnostic grants 보존).
- CR 12-5 D-14 typed exception envelope 16 NEW 보존 결정 wire 진입.
- CR 12-5 D-PARITY-01 inversion TypeScript mirror parity (`interactive-dashboard-types.ts`
  + `interactive-dashboard-client.ts`) 결정 wire 진입 (cj-style 197 T2 frontend only sprint
  의 T3.1 + T3.2 EXTENSION).
- CR 12-5 D-GATE-01 inversion capability gate inversion (`require_finops_interactive_dashboard`
  + fail-closed 403 Forbidden) 결정 wire 진입 (cj-style 193 의 T5.3 EXTENSION).
- A19 cohesion 9 surface EXTENSION PARTIAL → FULL preserved 결정 wire 진입 (cj-style 193 의
  Surface 7 TS mirror �️ N/A → ✅ EXTENSION + Surface 8 ko-KR SSOT ⚠️ N/A → ✅ EXTENSION).
- A36 SDR 검증 4-step 자동 적용 결정 wire (PRD entry 진입 시점에 자동).
- AD-14 stack pin Recharts 2.12.7 + reportlab 4.0.7 + xlsxwriter 3.1.9 + pandas 2.1.4 +
  matplotlib 3.8.2 + apscheduler 3.10.4 + pytz 2024.1 + noto-sans-cjk-kr EXTENSION 결정
  wire 진입.
- AD-22 owner-only RBAC FinopsInteractiveDashboardPanel.tsx orchestrator + 5 sub-components
  + 2 RSC pages 모두 owner-only RBAC EXTENSION 결정 wire.
- Epic 12 2FA 챌린지 mandatory destructive endpoint 의 3-layer defense EXTENSION 결정 wire
  (sharing scope=cross_tenant + 100+ saved views + ≥ 10M KRW/year impact → RFC 6238 TOTP
  + tenant_owner approval chain + Slack DM + 2FA 미설정 redirect +
  InteractiveDashboardSharing2FARequiredError 403 typed exception).
- NFR4 PII minimization ✅ PRESERVED (Epic 28 wire 결정 wire 시 PII minimization 자동 보존
  → Epic 28 T2 frontend follow-up sprint 진입 시에도 PII minimization 보존).
- NFR18 ko-KR SSOT apps/web/messages/ko-KR.json finops_interactive_dashboard.* namespace
  EXTENSION ~30 keys SSOT 보존 결정 wire.

## A19 cohesion 9 surface

본 sprint 는 Surface 8 docs EXTENSION 만 (PRD file 신규). 나머지 8 surface NO 변경.
A19 cohesion 9 surface EXTENSION PARTIAL preserved → FULL EXTENSION 결정 wire 보존.
Capability matrix v1.36 → v1.53 EXTENSION chain ✅ PRESERVED (18 + 1 = 19 steps).

## 3중 게이트 PARTIAL FINAL CLEAN 결정 wire

- ruff scoped: N/A (docs only sprint — ruff 는 Python backend linter).
- pytest: N/A (docs only sprint — pytest 는 Python backend test runner).
- vitest: N/A (docs only sprint — vitest 는 frontend test runner).
- tsc: N/A (docs only sprint — tsc 는 frontend type-checker).

= **3중 게이트 impact NONE** 결정 wire (docs only 변경 = cj-style 195번째 wire 진입 표준).

## Why this matters

**Epic 28 close-out retro (cj-style 194번째) 의 §12 옵션 (a) + §14 Action Items #1**
verbatim 회복: Phase 28 atomic wire Q2 backend-only `db005e8` (cj-style 193번째) 의
**T2 frontend honestly DEFER** → **follow-up sprint 결정 wire 진입 정직 회복**.

Phase 11~27 18-capability FinOps territory chain ✅ ALL WIRED INTEGRATED:
Phase 11 FINOPS_SHOWBACK + Phase 12 FINOPS_ANOMALY_DETECTION/BUDGET_ALERT +
Phase 13 FINOPS_FORECASTING_CAPACITY_PLANNING + Phase 14 FINOPS_OPTIMIZATION +
Phase 15 FINOPS_TAG_GOVERNANCE + Phase 16 FINOPS_REPORTING +
Phase 17 FINOPS_SUSTAINABILITY + Phase 18 FINOPS_COMMITMENT +
Phase 19 FINOPS_PRICING + Phase 20 FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION +
Phase 21 FINOPS_RESERVED_CAPACITY_PLANNING + Phase 22 FINOPS_CHARGEBACK_SETTLEMENT +
Phase 23 FINOPS_UNIT_ECONOMICS + Phase 24 FINOPS_BUDGET_PLANNING +
Phase 25 FINOPS_VENDOR_MANAGEMENT + Phase 26 FINOPS_COST_ANOMALY_ML_PREDICTION +
**Phase 28 FINOPS_INTERACTIVE_DASHBOARD (cj-style 191 PRD + cj-style 192 spec +
cj-style 193 atomic wire Q2 backend-only + cj-style 194 close-out retro +
cj-style 195 T2 frontend follow-up PRD)** =
**19 capabilities** 의 **cross-phase unified metrics + executive KPI surface closure**.

cj-style 195 T2 frontend follow-up sprint = Surface 7 (TS mirror) ⚠️ N/A →
✅ EXTENSION + Surface 8 (ko-KR SSOT) ⚠️ N/A → ✅ EXTENSION 결정 wire 보존
(cj-style 193 의 A19 cohesion 9 surface PARTIAL preserved → A19 cohesion 9
surface FULL EXTENSION preserved 결정 wire 보존).

Epic 28 wire 의 backend ledger data 활용 → 새 frontend infra 불필요 +
reuse 최대화 + risk 최소화 + 비즈니스 가치 최고 (executive dashboard surface =
비용 통제 layer 직접적 ROI).

## 결정 wire 일자

2026-08-29 (KST)

## Next (cj-style 195의 next-옵션)

- 옵션 (a) Phase 28 T2 frontend follow-up spec entry 진입 결정 wire (cj-style 196번째) —
  spec file ~+440 LOC.
- 옵션 (b) Epic 29+ 진입 결정 wire.
- 옵션 (c) Layer 2 P1 + Layer 3 P2 + emit_audit_typed signature mismatch carry-over 결정 wire.
- 옵션 (d) D-DEFER-* follow-up 결정 wire 보류.

## Related

- [[handoff-2026-08-29-epic-28-retro-done]] (cj-style 194th baseline)
- [[handoff-2026-08-29-phase-28-interactive-dashboard-atomic-wire-done]] (cj-style 193th)
- [[handoff-2026-08-29-phase-28-finops-interactive-dashboard-spec-entry-done]] (cj-style 192nd)
- [[handoff-2026-08-29-phase-28-interactive-dashboard-prd-entry-done]] (cj-style 191st)
- [[handoff-2026-08-28-phase-25-extra-forbid-tightening-done]] (cj-style 190th)
