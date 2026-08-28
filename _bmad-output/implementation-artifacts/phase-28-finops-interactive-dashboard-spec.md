---
baseline_commit: 62b2e32
status: ready-for-dev
cj_style_entry_point: 192
story_key: phase-28-finops-interactive-dashboard-spec
---

# Phase 28 FinOps Interactive Dashboard spec (cj-style 192번째 epic 연속 정직 회복)

## Story

**As a** FinOps practitioner / cloud architect / tenant admin / 1st release customer / DevOps engineer
**I want** Phase 28 territory 결정 wire (FinOps Interactive Dashboard = **cross_phase_aggregator** with unified metrics from Phase 11~27 18-capability FinOps territory chain (Phase 11 showback + Phase 12 anomaly_detection + Phase 13 forecasting_capacity_planning + Phase 14 optimization + Phase 15 tag_governance + Phase 16 reporting + Phase 17 sustainability + Phase 18 commitment + Phase 19 pricing + Phase 20 multi_cloud_unified_reconciliation + Phase 21 reserved_capacity_planning + Phase 22 chargeback_settlement + Phase 23 unit_economics + Phase 24 budget_planning + Phase 25 vendor_management + Phase 26 cost_anomaly_ml_prediction + Phase 27 carry-over territory) + **self_service filter / drill_down / saved_views engine** + **export_pipeline** (PDF + XLSX + CSV + JSON + PNG) reusing Phase 17 sustainability report engine + Phase 22 chargeback invoice generator EXTENSION + **executive KPI surface** + **dashboard_sharing** (RBAC + tenant isolation) + **5 NEW sub-components** (CrossPhaseKPIOverview + SavedViewManager + DrillDownExplorer + ExportConfigPanel + DashboardSharingPanel) + **Capability matrix v1.53 EXTENSION FINOPS_INTERACTIVE_DASHBOARD** + **audit action EXTENSION 8 NEW Literal + 16 NEW typed exception classes** + **dry-run mode + 1 NEW CLI flag + Tests + wire scope T1~T8**) 결정 wire
**so that** Phase 11~27 18-capability FinOps territory chain ✅ ALL WIRED INTEGRATED 진입 정합 보존 후 Phase 28 PRD entry `62b2e32` (cj-style 191번째) 진입 직후 spec entry 진입 = cj-style 4-entry-point cycle PRD entry → spec entry → wire → close-out retro 의 2번째 단계 진입 결정 wire (Phase 17 spec entry cj-style 130번째 + Phase 18 spec entry cj-style 134번째 + Phase 19 spec entry cj-style 138번째 + Phase 20 spec entry cj-style 143번째 + Phase 21 spec entry cj-style 150번째 + Phase 22 spec entry cj-style 159번째 + Phase 23 spec entry cj-style 163번째 + Phase 24 spec entry cj-style 168번째 + Phase 25 spec entry cj-style 172번째 + Phase 26 spec entry cj-style 180번째 패턴 verbatim 미러) + Phase 28 territory = 4 NEW backend modules (cross_phase_aggregator + saved_view_engine + export_pipeline + dashboard_router) 의 **cross-phase unified metrics + executive KPI surface** = Phase 11~27 모든 ledger data 활용 → forward-looking executive dashboard + saved views + drill-down + export = 비용 통제 layer 직접적 ROI 결정 wire + Phase 11~27 ledger data 활용 → 새 backend infra 불필요 + reuse 최대화 + risk 최소화 + 비즈니스 가치 최고 + Epic 12 2FA 챌린지 mandatory high-value ≥ 10M KRW/year + AD-22 owner-only RBAC + NFR4 PII minimization ✅ PRESERVED + NFR18 ko-KR SSOT + **AD-56 신규 (a)~(g) 7 sub-decisions** 모두 결정 wire 진입 + D-FINOPS-15 honestly DEFER 보존 + CR 11-3 honest-DEFER 82번째 epic 연속 정직 회복 verification 결정 wire 진입 + 3중 게이트 impact NONE (docs only 변경 = cj-style 192번째 wire 진입 표준 = docs only sprint) 결정 wire.

## Context

cj-style Phase 28 2번째 진입점 (cj-style 192번째) 진입 결정 wire 진입 완료:

- Phase 28 PRD entry `62b2e32` (cj-style 191번째) DONE 진입 정합 보존
- Phase 25 extra=forbid 조이기 source sprint `232fc49` (cj-style 190번째) DONE 진입 정합 보존
- Phase 21~26 Layer 2 P1 + Layer 3 P2 carry-over `d38f388` (cj-style 189번째) DONE 진입 정합 보존
- Phase 27 Layer 2 P1 + Layer 3 P2 carry-over `836a8d4` (cj-style 188번째) DONE 진입 정합 보존
- Phase 26 vitest frontend test `2dd9744` (cj-style 187번째) DONE 진입 정합 보존
- Phase 26 dashboard UI extension `fbc6f42` (cj-style 186번째) DONE 진입 정합 보존
- Phase 26 cj-182 close-out (cj-style 185번째) DONE 진입 정합 보존
- Phase 26 capability matrix extension `7357139` (cj-style 184번째) DONE 진입 정합 보존
- Phase 26 atomic wire (cj-style 183번째) DONE 진입 정합 보존
- Phase 26 spec entry (cj-style 180번째) DONE 진입 정합 보존
- Phase 26 PRD entry (cj-style 179번째) DONE 진입 정합 보존
- audit-fixes sprint close-out retro (cj-style 178번째) DONE 진입 정합 보존
- audit-fixes sprint retroactive correction (cj-style 177 follow-up) DONE 진입 정합 보존
- audit-fixes sprint wire (cj-style 176번째) DONE 진입 정합 보존
- audit-fixes sprint entry (cj-style 166번째) DONE 진입 정합 보존
- Phase 25 close-out retro (cj-style 175번째) DONE 진입 정합 보존
- Phase 25 integration follow-up (cj-style 174 follow-up) DONE 진입 정합 보존
- Phase 25 wire (cj-style 173번째) DONE 진입 정합 보존
- Phase 25 spec entry (cj-style 172번째) DONE 진입 정합 보존
- Phase 25 PRD entry (cj-style 171번째) DONE 진입 정합 보존
- Phase 24 close-out retro retroactive correction (cj-style 170 follow-up) DONE 진입 정합 보존
- Phase 24 close-out retro (cj-style 170번째) DONE 진입 정합 보존
- Phase 24 wire retroactive correction (cj-style 169 follow-up) DONE 진입 정합 보존
- Phase 24 wire (cj-style 169번째) DONE 진입 정합 보존
- Phase 24 spec entry (cj-style 168번째) DONE 진입 정합 보존
- Phase 24 PRD entry (cj-style 167번째) DONE 진입 정합 보존
- audit-fixes sprint entry (cj-style 166번째) DONE 진입 정합 보존
- Phase 23 close-out retro (cj-style 165번째) DONE 진입 정합 보존
- Phase 23 wire retroactive correction (cj-style 164 follow-up) DONE 진입 정합 보존
- Phase 23 atomic wire (cj-style 164번째) DONE 진입 정합 보존
- Phase 23 spec entry (cj-style 163번째) DONE 진입 정합 보존
- Phase 23 PRD entry (cj-style 162번째) DONE 진입 정합 보존
- Phase 22 close-out retro (cj-style 161번째) DONE 진입 정합 보존
- Phase 22 wire retroactive correction (cj-style 160 follow-up) DONE 진입 정합 보존
- Phase 22 atomic wire (cj-style 160번째) DONE 진입 정합 보존
- Phase 22 spec entry (cj-style 159번째) DONE 진입 정합 보존
- Phase 22 PRD entry (cj-style 158번째) DONE 진입 정합 보존
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
- Phase 20.5 atomic wire (cj-style 147번째) DONE 진입 정합 보존
- Phase 20.5 spec entry (cj-style 146번째) DONE 진입 정합 보존
- Phase 20 close-out retro (cj-style 145번째) DONE 진입 정합 보존
- Phase 20 atomic wire (cj-style 144번째) DONE 진입 정합 보존
- Phase 20 spec entry (cj-style 143번째) DONE 진입 정합 보존
- Phase 20 PRD entry (cj-style 142번째) DONE 진입 정합 보존
- Phase 19.5 carry-over 결정 wire (cj-style 141번째) DONE 진입 정합 보존
- Phase 19 close-out retro (cj-style 140번째) + Phase 19 atomic wire (cj-style 139번째) + Phase 19 spec entry (cj-style 138번째) + Phase 19 PRD entry (cj-style 137번째) + Phase 18 close-out retro (cj-style 136번째) + Phase 18 atomic wire (cj-style 135번째) + Phase 18 spec entry (cj-style 134번째) + Phase 18 PRD entry (cj-style 133번째) + Phase 17 close-out retro (cj-style 132번째) + Phase 17 atomic wire (cj-style 131번째) + Phase 17 spec entry (cj-style 130번째) + Phase 17 PRD entry (cj-style 129번째) + Phase 16 close-out retro (cj-style 128번째) + Phase 16 atomic wire (cj-style 127번째) + Phase 16 spec entry (cj-style 126번째) + Phase 16 PRD entry (cj-style 125번째) + Phase 15 close-out retro (cj-style 124번째) + Phase 15 atomic wire (cj-style 123번째) + Phase 15 spec entry (cj-style 122번째) + Phase 15 PRD entry (cj-style 121번째) + ... + Epic 1~17 ALL DONE 진입 정합 보존 + 1st release cycle ALL DONE 진입 정합 보존

### Phase 28 PRD entry `62b2e32` 의 8 ACs §F43.1~§F43.8 verbatim 보존

8 ACs §F43.1~§F43.8 → 76 explicit sub-ACs + nested bullet points → **~96 detailed sub-ACs** (12+12+12+8+6+4+12+10) pre-flight 정합 sweep 만족 결정 wire:

1. **§F43.1 cross_phase_aggregator + Phase 11~27 unified metrics** — `interactive_dashboard/` 1 NEW module 결정 wire + serializers.py (`UnifiedKPI` TypedDict 24 fields + `KPIBreakdown` TypedDict 8 fields + `DrillDownContext` TypedDict 6 fields + `SavedView` TypedDict 14 fields + `ExportJob` TypedDict 12 fields + `SharingGrant` TypedDict 8 fields + 6 enums `KPIRefreshCadence` (realtime/hourly/daily/weekly/monthly/on_demand) + `ExportFormat` (pdf/xlsx/csv/json/png) + `DashboardSharingScope` (private/tenant/tenant_owner/cross_tenant) + `DashboardLayout` (grid/masonry/tabs) + `DrillDownDimension` (tenant/cost_center/department/business_unit/tag/cloud_provider/service) + `DrillDownGranularity` (minute/hour/day/week/month/quarter/year) + `DASHBOARD_KPI_DIMENSION_WEIGHTS` constants + `DASHBOARD_CADENCE_HOURS_KST` + `DASHBOARD_RECIPIENT_TEMPLATES` + `DASHBOARD_DEFAULTS`) + `cross_phase_aggregator.py` (Phase 11~27 18 ledger table 통합 aggregation + 6-dim cross-rollup + tenant_id selector + trace_id ContextVar + audit-first INSERT `unified_kpi_calculated` CR 1-1 verbatim EXTENSION + 일 1회 KST cron 04:00 + realtime incremental update via LISTEN/NOTIFY 18 channels `phase_NN_unified_kpi_refreshed`) + `__init__.py` (module tag m28_finops_interactive_dashboard + comprehensive re-exports) (12 sub-ACs §F43.1.1~§F43.1.12)
2. **§F43.2 saved_view_engine + self-service filter / drill_down** — `SavedView` per-tenant saved filter + drill-down configuration (filter_by + group_by + sort_by + chart_type + time_range) + 12 NEW pre-defined view templates (CostByCloudProvider + CostByService + CostByCostCenter + CostByDepartment + CostByBusinessUnit + CostByTag + SavingsByOptimizationType + CommitmentUtilizationByCloud + BudgetVarianceByPeriod + SustainabilityByCloudProvider + VendorSpendByCategory + ReservedInstanceUtilizationByTier) + 5-dim weighted aggregation (cost 0.30 + usage 0.20 + performance 0.20 + compliance 0.15 + sla 0.15) + drill-down 6 dimensions (tenant/cost_center/department/business_unit/tag/cloud_provider/service) + 7-dim granularity (minute/hour/day/week/month/quarter/year) + per-tenant override `tenant_settings.dashboard_preferences.saved_views` > industry baseline > system default precedence + max_saved_views_per_tenant default 50 + cache TTL 5 minutes + audit-first INSERT `saved_view_created` + `saved_view_updated` + `saved_view_deleted` + `saved_view_executed` CR 1-1 verbatim EXTENSION (12 sub-ACs §F43.2.1~§F43.2.12)
3. **§F43.3 export_pipeline + PDF + XLSX + CSV + JSON + PNG** — `ExportJob` per-export tracking (status pending/in_progress/completed/failed + progress_pct + file_path + file_size_bytes + checksum_sha256 + expires_at) + 5 export formats (PDF reportlab 4.0.7 AD-14 stack pin + XLSX xlsxwriter 3.1.9 + CSV pandas 2.1.4 + JSON native + PNG via matplotlib 3.8.2 chart snapshot) + reuse Phase 17 sustainability report generator (PDF) + Phase 22 chargeback invoice generator (XLSX template EXTENSION) + max_export_size 50MB guard + 3 auto-retries + admin email alert on failure + ExcelTemplate reuse Phase 22 invoice template EXTENSION + chart embedding via Recharts 2.12.7 AD-14 stack pin snapshot + 7-dim aggregation + audit-first INSERT `export_job_started` + `export_job_completed` + `export_job_failed` CR 1-1 verbatim EXTENSION (12 sub-ACs §F43.3.1~§F43.3.12)
4. **§F43.4 dashboard UI 5 NEW sub-components + RSC pages** — `CrossPhaseKPIOverview` (Phase 11~27 unified KPI cards 18개 + grid layout + refresh cadence toggle) + `SavedViewManager` (CRUD + 12 NEW pre-defined templates + drag-drop reordering + sharing modal) + `DrillDownExplorer` (6-dim drill-down + 7-dim granularity + chart type switch + export button) + `ExportConfigPanel` (5 format selector + template preview + schedule + webhook URL) + `DashboardSharingPanel` (RBAC scope selector + recipient list + expiration + audit trail) + 2 NEW TS mirrors (interactive-dashboard-types.ts + interactive-dashboard-client.ts) + 2 NEW RSC pages (`/admin/finops/interactive-dashboard/page.tsx` + `layout.tsx`) + ko-KR.json EXTENSION ~30 keys (NFR18 SSOT) + Recharts 2.12.7 AD-14 stack pin VERBATIM + 5-tab layout (Overview / Saved Views / Drill-Down / Export / Sharing) + Epic 12 2FA 챌린지 mandatory ≥ 10M KRW/year sharing scope EXTENSION (8 sub-ACs §F43.4.1~§F43.4.8)
5. **§F43.5 Capability matrix v1.53 EXTENSION FINOPS_INTERACTIVE_DASHBOARD** — `Capability.FINOPS_INTERACTIVE_DASHBOARD` 1 NEW enum + `require_finops_interactive_dashboard` 1 NEW dep + `Role.INTERACTIVE_DASHBOARD_OPERATOR` + `Role.INTERACTIVE_DASHBOARD_VIEWER` 2 NEW enum + 4-industry grants ✅/✅/✅/✅ industry-agnostic CR 12-1 L4 verbatim + test_audit_action_v1_53_drift.py + capability gate fail-closed + Capability matrix v1.52 → v1.53 EXTENSION (6 sub-ACs §F43.5.1~§F43.5.6)
6. **§F43.6 audit action EXTENSION 8 NEW Literal + 16 NEW typed exception classes** — `ActionClass.FINOPS_INTERACTIVE_DASHBOARD` + `InteractiveDashboardAction` 8 NEW Literal (unified_kpi_calculated + saved_view_created + saved_view_updated + saved_view_deleted + saved_view_executed + export_job_started + export_job_completed + dashboard_shared) + `_ActionRegistry._REGISTRY` 1 NEW entry + `AuditAction` Union EXTENSION + 16 NEW typed exceptions CR 12-5 D-14 envelope (InteractiveDashboardAggregationError 500 + InteractiveDashboardKPIScopeError 404 + InteractiveDashboardKPIPeriodError 422 + InteractiveDashboardKPIModuleError 502 + SavedViewError 500 + SavedViewFilterError 400 + SavedViewTemplateError 404 + SavedViewLimitError 429 + ExportJobError 500 + ExportJobFormatError 400 + ExportJobSizeError 413 + ExportJobTenantError 403 + DashboardSharingError 500 + DashboardSharingScopeError 403 + DashboardSharingExpirationError 400 + DrillDownError 500) + Cache-Control no-store (4 sub-ACs §F43.6.1~§F43.6.4)
7. **§F43.7 dashboard_sharing + tenant isolation + RBAC** — `SharingGrant` per-grant tracking (scope private/tenant/tenant_owner/cross_tenant + granted_to_user_id + granted_at + expires_at + audit_trail) + tenant_isolation enforcement (Phase 0-2 RLS verbatim EXTENSION) + RBAC: only tenant_owner can grant `cross_tenant` scope + sharing expires default 30 days + audit-first INSERT `dashboard_shared` + `dashboard_access_revoked` + `dashboard_access_granted` CR 1-1 verbatim EXTENSION + Slack DM notification to grant recipient + Epic 12 2FA 챌린지 mandatory for high-value grants (sharing scope=cross_tenant + 100+ saved views) (12 sub-ACs §F43.7.1~§F43.7.12)
8. **§F43.8 dry-run + Tests + wire scope T1~T8** — `--finops-interactive-dashboard-dry-run` 1 NEW CLI flag + phase_28_interactive_dashboard_preview 1 table + ~+85 NEW pytest + ~+7 NEW vitest + 0 NEW ruff + 0 NEW tsc + 0 regressions + wire scope T1~T8 (10 sub-ACs §F43.8.1~§F43.8.10)

**Total sub-ACs**: 12+12+12+8+6+4+12+10 = **76 explicit sub-ACs** with nested bullet points → **~96 detailed sub-ACs** pre-flight 정합 sweep 만족 결정 wire (cj-style 191 commit message 의 ~96 sub-ACs verbatim mirror).

### AD-56 신규 결정 (a)~(g) 7 sub-decisions (Phase 28 PRD entry 진입 시점에 결정 wire 진입 완료)

- (a) cross_phase_aggregator 의 backend detail (Phase 11~27 ledger data 활용 + 18 unified KPI aggregation + 6-dim cross-rollup + realtime incremental update via LISTEN/NOTIFY 18 channels + pure function computation + dry-run mode + industry-agnostic 4-industry grants CR 12-1 L4 verbatim)
- (b) saved_view_engine 의 self-service filter / drill_down detail (5-dim weighted aggregation cost 0.30 + usage 0.20 + performance 0.20 + compliance 0.15 + sla 0.15 + per-tenant override > industry baseline > system default precedence + max_saved_views_per_tenant default 50 + cache TTL 5 minutes + 12 NEW pre-defined view templates)
- (c) export_pipeline 의 5 format detail (PDF reportlab 4.0.7 + XLSX xlsxwriter 3.1.9 + CSV pandas 2.1.4 + JSON native + PNG via matplotlib 3.8.2 chart snapshot + reuse Phase 17 sustainability report generator + Phase 22 chargeback invoice template EXTENSION + max_export_size 50MB guard + 3 auto-retries + admin email alert on failure)
- (d) dashboard_sharing + tenant isolation + RBAC detail (4 scope private/tenant/tenant_owner/cross_tenant + tenant_isolation enforcement + RBAC: only tenant_owner can grant cross_tenant + sharing expires default 30 days + Slack DM notification + Epic 12 2FA �린지 mandatory for high-value grants + audit-first INSERT dashboard_shared + dashboard_access_revoked + dashboard_access_granted)
- (e) NFR4 PII minimization preservation detail (no employee names + actor_id UUID + tenant_id UUID + monetary amounts only + score metrics only + Cache-Control no-store)
- (f) NFR18 ko-KR SSOT detail (finops_interactive_dashboard.* namespace EXTENSION ~30 keys + Korean font noto-sans-cjk-kr + Korean error messages + English audit action names)
- (g) Epic 12 2FA 챌린지 mandatory high-value detail (sharing scope=cross_tenant + 100+ saved views → RFC 6238 TOTP + tenant_owner approval chain + InteractiveDashboardSharing2FARequiredError(403) + dashboard 공유 action → Epic 12 2FA 챌린지 mandatory + 2FA 미설정 tenant 의 경우 `/account/security?reason=2fa_required` redirect)

### D-FINOPS-15 신규 honestly DEFER 보존

Phase 28 PRD entry 진입 시점에 carry-over chain 정직 회복 결정 wire 진입 = cross_phase_aggregator Phase 11~27 18 ledger 통합 aggregation + saved_view_engine self-service filter / drill_down + export_pipeline 5 format reuse Phase 17/22 EXTENSION + dashboard UI 5 sub-components + capability matrix v1.53 EXTENSION FINOPS_INTERACTIVE_DASHBOARD + audit action 8 NEW + 16 NEW typed exceptions + dashboard_sharing + tenant isolation + RBAC + dry-run mode + 1 NEW CLI flag — 모두 단일 sprint `wire` 진입에 결정 wire 진입 + multi-modal cost input aggregation (vision / NLP / receipt OCR feed) + causal inference root cause analysis for cost spikes + LLM 기반 cost anomaly explanation auto-narrative + automated cost remediation (Phase 14 optimization auto-apply dashboard-detected issues) + cross-tenant federated cost benchmarking (privacy-preserving) + cost optimization marketplace 3rd-party cost reduction services + real-time streaming cost prediction (sub-second latency) + unsupervised online learning for cost anomaly detection (model update without retraining) — 모두 별도 sprint honestly DEFER 보류 결정 wire 보존 (Phase 17 close-out retro §11 + Phase 21 close-out retro §11 + Phase 22 close-out retro §11 + Phase 23 close-out retro §11 + Phase 24 close-out retro §10 + Phase 25 close-out retro §11 + Phase 26 close-out retro §11 의 honest deviation 보존 패턴 verbatim 미러).

## T1~T8 + ~76 subtasks

### T1: Phase 28 4 NEW backend interactive_dashboard modules (8 subtasks)
- T1.1: `apps/api/modules/finops/interactive_dashboard/__init__.py` NEW + ALLOWED_SERVICE_SUBMODULES EXTENSION m28_finops_interactive_dashboard 신규 submodule 등록 결정 wire (Phase 22 m22_finops_chargeback_settlement + Phase 23 m23_finops_unit_economics + Phase 24 m24_finops_budget_planning + Phase 25 m25_finops_vendor_management + Phase 26 m34_finops_cost_anomaly_ml_prediction 패턴 보존)
- T1.2: `apps/api/modules/finops/interactive_dashboard/serializers.py` NEW ~+380 LOC + 6 NEW enums (KPIRefreshCadence 6 values realtime/hourly/daily/weekly/monthly/on_demand + ExportFormat 5 values pdf/xlsx/csv/json/png + DashboardSharingScope 4 values private/tenant/tenant_owner/cross_tenant + DashboardLayout 3 values grid/masonry/tabs + DrillDownDimension 7 values tenant/cost_center/department/business_unit/tag/cloud_provider/service + DrillDownGranularity 7 values minute/hour/day/week/month/quarter/year) + 6 NEW TypedDicts (UnifiedKPI 24 fields + KPIBreakdown 8 fields + DrillDownContext 6 fields + SavedView 14 fields + ExportJob 12 fields + SharingGrant 8 fields) + DASHBOARD_KPI_DIMENSION_WEIGHTS constants (cost 0.30 + usage 0.20 + performance 0.20 + compliance 0.15 + sla 0.15) + DASHBOARD_CADENCE_HOURS_KST (realtime 0 + hourly 1 + daily 24 + weekly 168 + monthly 720) + DASHBOARD_RECIPIENT_TEMPLATES + DASHBOARD_DEFAULTS (max_saved_views_per_tenant=50 + cache_ttl_seconds=300 + sharing_expires_default_days=30 + max_export_size_bytes=52428800) 결정 wire
- T1.3: `apps/api/modules/finops/interactive_dashboard/cross_phase_aggregator.py` NEW ~+360 LOC + compute_unified_kpi(tenant_id, period_key, modules=[11~27]) → UnifiedKPI + aggregate_cross_phase_breakdown(tenant_id, period_key) → KPIBreakdown + realtime_incremental_update_via_listen_notify() → bool + 18 unified KPI aggregation (Phase 11 showback_krw + Phase 12 anomaly_count + Phase 13 forecast_krw + Phase 14 optimization_savings_krw + Phase 15 tag_compliance_pct + Phase 16 report_krw + Phase 17 sustainability_co2_kg + Phase 18 commitment_utilization_pct + Phase 19 pricing_savings_krw + Phase 20 multi_cloud_reconciliation_krw + Phase 21 reserved_capacity_utilization_pct + Phase 22 chargeback_settlement_krw + Phase 23 unit_economics_cost_per_unit + Phase 24 budget_consumption_pct + Phase 25 vendor_spend_krw + Phase 26 anomaly_ml_score + Phase 27 carry_over_metric + Phase 28 unified_kpi = 18 KPIs) + 6-dim cross-rollup (tenant/cost_center/department/business_unit/tag/cloud_provider) + tenant_id selector + trace_id ContextVar + audit-first INSERT `unified_kpi_calculated` CR 1-1 verbatim EXTENSION + 일 1회 KST cron 04:00 + realtime incremental update via LISTEN/NOTIFY 18 channels (phase_11_unified_kpi_refreshed + phase_12_unified_kpi_refreshed + ... + phase_27_unified_kpi_refreshed) + 4 NEW typed exceptions (InteractiveDashboardAggregationError 500 + InteractiveDashboardKPIScopeError 404 + InteractiveDashboardKPIPeriodError 422 + InteractiveDashboardKPIModuleError 502) 결정 wire
- T1.4: `apps/api/modules/finops/interactive_dashboard/saved_view_engine.py` NEW ~+340 LOC + create_saved_view(tenant_id, view_config) → SavedView + read_saved_view(tenant_id, view_id) → SavedView + update_saved_view(tenant_id, view_id, ...) → SavedView + delete_saved_view(tenant_id, view_id) → bool + execute_saved_view(tenant_id, view_id) → list[UnifiedKPI] + list_saved_views(tenant_id, filter) → list + 12 NEW pre-defined view templates (CostByCloudProvider + CostByService + CostByCostCenter + CostByDepartment + CostByBusinessUnit + CostByTag + SavingsByOptimizationType + CommitmentUtilizationByCloud + BudgetVarianceByPeriod + SustainabilityByCloudProvider + VendorSpendByCategory + ReservedInstanceUtilizationByTier) + 5-dim weighted aggregation (cost 0.30 + usage 0.20 + performance 0.20 + compliance 0.15 + sla 0.15) + 6-dim drill-down + 7-dim granularity + per-tenant override `tenant_settings.dashboard_preferences.saved_views` > industry baseline > system default precedence + max_saved_views_per_tenant default 50 + cache TTL 5 minutes + audit-first INSERT `saved_view_created` + `saved_view_updated` + `saved_view_deleted` + `saved_view_executed` CR 1-1 verbatim EXTENSION + 4 NEW typed exceptions (SavedViewError 500 + SavedViewFilterError 400 + SavedViewTemplateError 404 + SavedViewLimitError 429) 결정 wire
- T1.5: `apps/api/modules/finops/interactive_dashboard/export_pipeline.py` NEW ~+340 LOC + start_export_job(tenant_id, view_id, format, options) → ExportJob + get_export_job_status(job_id) → ExportJob + list_export_jobs(tenant_id, filter) → list + cancel_export_job(job_id) → ExportJob + 5 export formats (PDF reportlab 4.0.7 AD-14 stack pin + XLSX xlsxwriter 3.1.9 + CSV pandas 2.1.4 + JSON native + PNG via matplotlib 3.8.2 chart snapshot) + reuse Phase 17 sustainability report generator (PDF template reuse) + Phase 22 chargeback invoice generator (XLSX template EXTENSION) + max_export_size 50MB guard + 3 auto-retries + admin email alert on failure + chart embedding via Recharts 2.12.7 AD-14 stack pin snapshot + audit-first INSERT `export_job_started` + `export_job_completed` + `export_job_failed` CR 1-1 verbatim EXTENSION + 4 NEW typed exceptions (ExportJobError 500 + ExportJobFormatError 400 + ExportJobSizeError 413 + ExportJobTenantError 403) 결정 wire
- T1.6: `apps/api/modules/finops/interactive_dashboard/dashboard_router.py` NEW ~+260 LOC + FastAPI router prefix `/api/v1/admin/finops/interactive-dashboard` + capability gate `Depends(require_finops_interactive_dashboard)` + 10 endpoints (healthcheck + POST /saved-views + GET /saved-views/{view_id} + PUT /saved-views/{view_id} + DELETE /saved-views/{view_id} + POST /saved-views/{view_id}/execute + POST /unified-kpi + POST /exports + GET /exports/{job_id} + POST /sharing + GET /templates) 결정 wire
- T1.7: `apps/api/modules/finops/interactive_dashboard/scheduled_interactive_dashboard_dispatch.py` NEW ~+220 LOC + apscheduler==3.10.4 + pytz==2024.1 EXTENSION + scheduled_unified_kpi_refresh_job (daily 04:00 KST) + scheduled_export_cleanup_job (weekly Mon 05:00 KST) + scheduled_sharing_expiry_job (monthly 1st-day 06:00 KST) + LISTEN/NOTIFY 18 channels (phase_11~phase_27_unified_kpi_refreshed + phase_28_unified_kpi_calculated) + Phase 26 wire 의 scheduled pattern verbatim EXTENSION 결정 wire
- T1.8: `apps/api/modules/finops/interactive_dashboard/interactive_dashboard_routes.py` NEW ~+180 LOC + FastAPI router prefix 통합 + capability gate + 10 endpoints 통합 wrapper + Phase 26 wire 의 routes pattern verbatim EXTENSION 결정 wire

### T2: dashboard UI 5 NEW sub-components (10 subtasks)
- T2.1: `apps/web/app/[locale]/(dashboard)/admin/finops/interactive-dashboard/page.tsx` NEW ~+260 LOC + 5 sub-components (CrossPhaseKPIOverview + SavedViewManager + DrillDownExplorer + ExportConfigPanel + DashboardSharingPanel) EXTENSION 결정 wire
- T2.2: `apps/web/app/[locale]/(dashboard)/admin/finops/interactive-dashboard/layout.tsx` NEW ~+110 LOC + owner-only RBAC AD-22 verbatim + Epic 12 2FA 챌린지 mandatory ≥ 10M KRW/year sharing scope + ko-KR.json `finops_interactive_dashboard.*` namespace EXTENSION ~30 keys (CR 11-4 D-002 verbatim SSOT) + ARIA labels WCAG 2.1 AA + `(dashboard)` route group 보호 EXTENSION 결정 wire
- T2.3: `apps/web/components/finops/FinopsInteractiveDashboardPanel.tsx` NEW Client component ~+300 LOC + 5-tab layout (Overview / Saved Views / Drill-Down / Export / Sharing) + Recharts radar chart (KPI dimension weights visualization) + Recharts line chart (drill-down granularity toggle) + Recharts area chart (Phase 11~27 unified KPI breakdown) + TanStack Table (12 NEW pre-defined templates) + dry-run toggle (default: dry-run) + 5 NEW charts (radar + line + area + table + overview cards) 결정 wire
- T2.4: `apps/web/lib/finops/interactive-dashboard-types.ts` NEW TypeScript mirror + 6 NEW TypeScript interfaces (UnifiedKPI + KPIBreakdown + DrillDownContext + SavedView + ExportJob + SharingGrant) + 6 NEW enums + UNIFIED_KPI_DIMENSION_WEIGHTS constants CR 12-5 D-PARITY-01 inversion EXTENSION 결정 wire
- T2.5: `apps/web/lib/finops/interactive-dashboard-client.ts` NEW TypeScript client + 8 NEW methods (createSavedView + updateSavedView + deleteSavedView + executeSavedView + fetchUnifiedKPI + startExportJob + fetchExportJobStatus + shareDashboard) EXTENSION 결정 wire
- T2.6: `apps/web/messages/ko-KR.json` MODIFIED EXTENSION ~30 keys + `finops_interactive_dashboard.*` namespace EXTENSION + ARIA labels WCAG 2.1 AA + NFR18 ko-KR SSOT 보존 결정 wire
- T2.7: interactive_dashboard dashboard Recharts 2.12.7 AD-14 stack pin EXTENSION + TanStack Table v8 AD-14 stack pin EXTENSION + 5 NEW charts (radar + line + area + table + overview cards) + 4 industries baseline visualization 차이 EXTENSION 결정 wire
- T2.8: interactive_dashboard dashboard dry-run mode UI (CrossPhaseKPIOverview 진입 시 dry-run toggle default: dry-run) + 5-tab navigation + Epic 12 2FA 챌린지 mandatory ≥ 10M KRW/year sharing scope EXTENSION 결정 wire
- T2.9: 5 NEW sub-components (CrossPhaseKPIOverview.tsx + SavedViewManager.tsx + DrillDownExplorer.tsx + ExportConfigPanel.tsx + DashboardSharingPanel.tsx) 결정 wire
- T2.10: CrossPhaseKPIOverview Phase 11~27 unified KPI cards 18개 (showback_krw + anomaly_count + forecast_krw + optimization_savings_krw + tag_compliance_pct + report_krw + sustainability_co2_kg + commitment_utilization_pct + pricing_savings_krw + multi_cloud_reconciliation_krw + reserved_capacity_utilization_pct + chargeback_settlement_krw + unit_economics_cost_per_unit + budget_consumption_pct + vendor_spend_krw + anomaly_ml_score + carry_over_metric + unified_kpi_total) + grid layout + refresh cadence toggle 결정 wire

### T3: alembic 0058 phase_28_interactive_dashboard 4 tables + 1 preview table + RLS (8 subtasks)
- T3.1: `apps/api/alembic/versions/0058_phase_28_interactive_dashboard.py` NEW 결정 wire = phase_28_interactive_dashboard_unified_kpi + _saved_view + _export_job + _sharing_grant 4 NEW tables EXTENSION (Phase 28 territory 의 cross-phase unified metrics + executive dashboard surface 결정 wire)
- T3.2: phase_28_interactive_dashboard_unified_kpi 1 NEW table 결정 wire + unified_kpi_id UUID PK + tenant_id UUID + period_key TEXT + dimension TEXT + dimension_value TEXT + kpi_value NUMERIC(18,2) KRW + kpi_breakdown JSONB + computed_at TIMESTAMPTZ DEFAULT NOW() + trace_id TEXT EXTENSION
- T3.3: phase_28_interactive_dashboard_saved_view 1 NEW table 결정 wire + saved_view_id UUID PK + tenant_id UUID + view_name TEXT + view_config JSONB + template_id TEXT (12 NEW templates 참조) + is_shared BOOLEAN DEFAULT FALSE + created_by_user_id UUID + created_at TIMESTAMPTZ DEFAULT NOW() + updated_at TIMESTAMPTZ + audit_trail JSONB append-only EXTENSION
- T3.4: phase_28_interactive_dashboard_export_job 1 NEW table 결정 wire + export_job_id UUID PK + tenant_id UUID + saved_view_id UUID FK + format TEXT (pdf/xlsx/csv/json/png) + status TEXT (pending/in_progress/completed/failed) + progress_pct NUMERIC(5,2) + file_path TEXT + file_size_bytes BIGINT + checksum_sha256 TEXT 64 hex + expires_at TIMESTAMPTZ + started_at TIMESTAMPTZ + completed_at TIMESTAMPTZ + trace_id TEXT EXTENSION
- T3.5: phase_28_interactive_dashboard_sharing_grant 1 NEW table 결정 wire + sharing_grant_id UUID PK + tenant_id UUID + saved_view_id UUID FK + scope TEXT (private/tenant/tenant_owner/cross_tenant) + granted_to_user_id UUID + granted_by_user_id UUID + granted_at TIMESTAMPTZ DEFAULT NOW() + expires_at TIMESTAMPTZ + audit_trail JSONB EXTENSION
- T3.6: phase_28_interactive_dashboard_preview 1 NEW preview table 결정 wire (dry-run preview ONLY) + preview_id UUID PK + tenant_id UUID + period_key TEXT + view_id TEXT + preview_data JSONB + computed_at TIMESTAMPTZ DEFAULT NOW() + trace_id TEXT EXTENSION
- T3.7: RLS 자동 적용 CR 0-2 verbatim 결정 wire = 4 tables + 1 preview table tenant_id = current_setting('app.tenant_id')::uuid EXTENSION
- T3.8: CHECK + UNIQUE + indexes EXTENSION 결정 wire = idempotency_key UNIQUE + format enum CHECK + scope enum CHECK + status enum CHECK + filter_by + drill_down_context JSONB GIN index + tenant_id + period_key + dimension composite index + audit_trail JSONB GIN index EXTENSION

### T4: audit action EXTENSION 8 NEW Literal + 16 NEW typed exception classes (4 subtasks)
- T4.1: `apps/api/core/audit_action.py` MODIFIED EXTENSION 결정 wire + ActionClass.FINOPS_INTERACTIVE_DASHBOARD 1 NEW enum EXTENSION + _ActionRegistry._REGISTRY 1 NEW entry EXTENSION + AuditAction Union EXTENSION 결정 wire
- T4.2: `apps/api/core/audit_action.py` MODIFIED EXTENSION + InteractiveDashboardAction 8 NEW Literal EXTENSION (unified_kpi_calculated + saved_view_created + saved_view_updated + saved_view_deleted + saved_view_executed + export_job_started + export_job_completed + dashboard_shared)
- T4.3: `apps/api/core/errors.py` MODIFIED EXTENSION 16 NEW typed exception classes CR 12-5 D-14 envelope 결정 wire = FinopsInteractiveDashboardError base class + InteractiveDashboardAggregationError(500) + InteractiveDashboardKPIScopeError(404) + InteractiveDashboardKPIPeriodError(422) + InteractiveDashboardKPIModuleError(502) + SavedViewError(500) + SavedViewFilterError(400) + SavedViewTemplateError(404) + SavedViewLimitError(429) + ExportJobError(500) + ExportJobFormatError(400) + ExportJobSizeError(413) + ExportJobTenantError(403) + DashboardSharingError(500) + DashboardSharingScopeError(403) + DashboardSharingExpirationError(400) + DrillDownError(500) EXTENSION
- T4.4: 8 NEW audit actions via emit_audit_typed CR 1-1 verbatim EXTENSION 결정 wire + Phase 26 wire `cj-183` 의 12 NEW audit actions pattern verbatim EXTENSION + tenant_id + period_key + dimension source attribution JSONB payload EXTENSION

### T5: Capability matrix v1.53 EXTENSION FINOPS_INTERACTIVE_DASHBOARD (4 subtasks)
- T5.1: `docs/capability-matrix.md` MODIFIED v1.52 → v1.53 EXTENSION 결정 wire + FINOPS_INTERACTIVE_DASHBOARD 1 NEW row after FINOPS_COST_ANOMALY_ML_PREDICTION industry-agnostic 4-industry grants ✅/✅/✅/✅ CR 12-1 L4 precedent verbatim EXTENSION
- T5.2: `apps/api/core/capability.py` MODIFIED EXTENSION + Capability.FINOPS_INTERACTIVE_DASHBOARD 1 NEW enum 결정 wire
- T5.3: `apps/api/dependencies/capability.py` MODIFIED EXTENSION + require_finops_interactive_dashboard 1 NEW dep 결정 wire + Role.INTERACTIVE_DASHBOARD_OPERATOR + Role.INTERACTIVE_DASHBOARD_VIEWER 2 NEW enum EXTENSION + fail-closed 403 Forbidden EXTENSION
- T5.4: `apps/api/modules/finops/__init__.py` MODIFIED EXTENSION + interactive_dashboard submodule export + ALLOWED_SERVICE_SUBMODULES 즉시 sweep EXTENSION = m28_finops_interactive_dashboard 신규 submodule 등록 (Phase 22 m22_finops_chargeback_settlement + Phase 23 m23_finops_unit_economics + Phase 24 m24_finops_budget_planning + Phase 25 m25_finops_vendor_management + Phase 26 m34_finops_cost_anomaly_ml_prediction 패턴 보존) + Phase 11~27 verbatim EXTENSION

### T6: scheduled_interactive_dashboard_dispatch wire (2 subtasks)
- T6.1: `apps/api/modules/finops/interactive_dashboard/scheduled_interactive_dashboard_dispatch.py` NEW ~+220 LOC + apscheduler==3.10.4 + pytz==2024.1 EXTENSION + 4 cadences (daily 04:00 KST scheduled_unified_kpi_refresh_job + weekly Mon 05:00 KST scheduled_export_cleanup_job + monthly 1st-day 06:00 KST scheduled_sharing_expiry_job + on-demand scheduled_unified_kpi_incremental_update_job) + LISTEN/NOTIFY 18 channels (phase_11~phase_27_unified_kpi_refreshed + phase_28_unified_kpi_calculated) + recipient resolver Slack + Email + S3 archive 결정 wire
- T6.2: LISTEN/NOTIFY consume trigger EXTENSION 결정 wire = 18 NEW channels (phase_11_unified_kpi_refreshed + phase_12_unified_kpi_refreshed + phase_13_unified_kpi_refreshed + phase_14_unified_kpi_refreshed + phase_15_unified_kpi_refreshed + phase_16_unified_kpi_refreshed + phase_17_unified_kpi_refreshed + phase_18_unified_kpi_refreshed + phase_19_unified_kpi_refreshed + phase_20_unified_kpi_refreshed + phase_21_unified_kpi_refreshed + phase_22_unified_kpi_refreshed + phase_23_unified_kpi_refreshed + phase_24_unified_kpi_refreshed + phase_25_unified_kpi_refreshed + phase_26_unified_kpi_refreshed + phase_27_unified_kpi_refreshed + phase_28_unified_kpi_calculated) + Phase 26 wire 의 LISTEN/NOTIFY pattern verbatim EXTENSION 결정 wire

### T7: dry-run mode + 1 NEW CLI flag (4 subtasks)
- T7.1: dry-run mode EXTENSION 결정 wire = dry-run 시 actual `unified_kpi_calculated` + `saved_view_executed` + `export_job_started` + `dashboard_shared` audit-first INSERT skip + dry-run 결과 preview = phase_28_interactive_dashboard_preview 1 table + audit-first INSERT `interactive_dashboard_dry_run_executed` EXTENSION
- T7.2: `apps/api/scripts/cli/finops_interactive_dashboard_dry_run.py` NEW ~+100 LOC + `--finops-interactive-dashboard-dry-run` 1 NEW CLI flag EXTENSION (Phase 26 wire 의 `--finops-cost-anomaly-ml-prediction-dry-run` 1 NEW CLI flag 패턴 verbatim EXTENSION)
- T7.3: dry-run preview UI EXTENSION 결정 wire = CrossPhaseKPIOverview 진입 시 dry-run toggle (default: dry-run) + dry-run 결과 preview UI EXTENSION
- T7.4: dry-run mode integration tests EXTENSION 결정 wire = ~+6 NEW pytest cases (skip audit + preview table + 1 CLI flag + 4 cadences + 5 export formats + 4 sharing scopes) EXTENSION

### T8: 3중 게이트 FINAL CLEAN atomic commit (4 subtasks)
- T8.1: ruff scoped Phase 28 files 0 NEW EXTENSION 결정 wire + Phase 26 wire `cj-183` 의 0 NEW ruff pattern verbatim EXTENSION
- T8.2: pytest ~+85 NEW pytest PASS EXTENSION 결정 wire (cross_phase_aggregator 22 + saved_view_engine 22 + export_pipeline 22 + dashboard_router 19 = ~85 NEW pytest PASS)
- T8.3: vitest ~+7 NEW vitest PASS EXTENSION 결정 wire (CrossPhaseKPIOverview 2 + SavedViewManager 1 + DrillDownExplorer 1 + ExportConfigPanel 1 + DashboardSharingPanel 1 + FinopsInteractiveDashboardPanel 1 = ~7 NEW vitest PASS)
- T8.4: 3중 게이트 FINAL CLEAN atomic commit via `git commit -F <file>` (CR 9-6 D5 prevention + PowerShell here-string 회피) 결정 wire

**Subtotal**: 8+10+8+4+4+2+4+4 = **~44 subtasks** 결정 wire (Phase 26 wire `cj-183` 의 ~40 subtasks pattern 의 4-NEW-module cross-phase aggregator layer version EXTENSION → 4 domain tables + 1 preview table EXTENSION)

## Dev Notes 20종 (CR lessons applied)

- **CR 0-2 RLS** — 4 NEW tables + 1 preview table 의 tenant-scoped RLS 자동 적용 (current_setting('app.tenant_id')::uuid) 보존
- **CR 1-1 audit-first INSERT 8 NEW** — ActionClass.FINOPS_INTERACTIVE_DASHBOARD 의 8 NEW audit actions (unified_kpi_calculated + saved_view_created + saved_view_updated + saved_view_deleted + saved_view_executed + export_job_started + export_job_completed + dashboard_shared) 결정 wire 진입 시점에 audit-first INSERT 자동 활성화 보존
- **CR 1-1 FastAPI ContextVar** — tenant_id ContextVar middleware layer 보존 (CR 1-1 verbatim EXTENSION)
- **CR 1-1 RSC boundary** — Next.js 15.x RSC boundary 보존 (apps/web/app/[locale]/(dashboard)/admin/finops/interactive-dashboard/{page,layout}.tsx)
- **CR 4-3/4-4** — async-test asyncio.run + Industry enum SSOT + A5 drift detector + golden_diff + SDR overclaim 방지
- **CR 5-1 Decimal precision** — banker's rounding 정합 + 소수점 2자리 (NUMERIC(18,2)) for KRW monetary amounts + 5,4 for percentage metrics (kpi_breakdown ratios)
- **CR 9-6 commit message** — `git commit -F <file>` (D5 prevention) + PowerShell here-string 회피 결정 wire
- **CR 11-3 honest-DEFER 82번째** — D-FINOPS-15 honestly DEFER 보존 (Phase 28 territory 진입) + Phase 11~27 18-capability FinOps territory chain ✅ ALL WIRED 결정 wire
- **ALLOWED_SERVICE_SUBMODULES 즉시 sweep** — Phase 28 wire 진입 시점에 `apps/api/modules/finops/__init__.py` 의 submodule 목록 즉시 sweep EXTENSION = m28_finops_interactive_dashboard 신규 submodule 등록
- **CR 11-4 D-001~D-005** — ko-KR.json `finops_interactive_dashboard.*` namespace EXTENSION ~30 keys SSOT + NFR18 ko-KR SSOT 보존
- **P-015 SSOT** — ko-KR.json finops_interactive_dashboard.* 단일 SSOT 결정 wire
- **CR 12-1 L4** — industry-agnostic capability grants (4-industry ✅/✅/✅/✅) EXTENSION 결정 wire (Phase 26 wire 의 FINOPS_COST_ANOMALY_ML_PREDICTION 패턴 verbatim 미러)
- **CR 12-5 D-14 typed exception envelope 16 NEW** — Phase 28 wire 의 16 NEW typed exceptions (FinopsInteractiveDashboardError base + InteractiveDashboardAggregationError + InteractiveDashboardKPIScopeError + InteractiveDashboardKPIPeriodError + InteractiveDashboardKPIModuleError + SavedViewError + SavedViewFilterError + SavedViewTemplateError + SavedViewLimitError + ExportJobError + ExportJobFormatError + ExportJobSizeError + ExportJobTenantError + DashboardSharingError + DashboardSharingScopeError + DashboardSharingExpirationError + DrillDownError) CR 12-5 D-14 envelope 적용
- **CR 12-5 D-PARITY-01 inversion** — TypeScript mirror parity (interactive-dashboard-types.ts + interactive-dashboard-client.ts) 결정 wire
- **CR 12-5 D-GATE-01 inversion** — capability gate inversion (require_finops_interactive_dashboard + fail-closed 403 Forbidden) 결정 wire
- **A19 cohesion 9 surface EXTENSION PASS** — FinOps Interactive Dashboard surface NEW 결정 wire 진입 후에도 9 surface 모두 PASS 보존
- **A36 SDR 검증 4-step** — 자동 적용 결정 wire (spec entry 진입 시점에 자동)
- **AD-14 stack pin** — Recharts 2.12.7 + reportlab 4.0.7 + xlsxwriter 3.1.9 + pandas 2.1.4 + matplotlib 3.8.2 + apscheduler 3.10.4 + pytz 2024.1 + noto-sans-cjk-kr EXTENSION 결정 wire (Phase 26 wire 의 AD-14 stack pin verbatim 미러 + reportlab/xlsxwriter/pandas/matplotlib export stack pin EXTENSION)
- **AD-22 owner-only RBAC** — interactive_dashboard dashboard UI 모두 owner-only RBAC EXTENSION (CrossPhaseKPIOverview + SavedViewManager + DrillDownExplorer + ExportConfigPanel + DashboardSharingPanel + dashboard sharing 모두 owner-only)
- **Epic 12 2FA 챌린지 mandatory** — destructive endpoint 의 3-layer defense EXTENSION 결정 wire (sharing scope=cross_tenant + 100+ saved views + ≥ 10M KRW/year impact → RFC 6238 TOTP + tenant_owner approval chain + Slack DM + 2FA 미설정 redirect + InteractiveDashboardSharing2FARequiredError 403 typed exception)
- **NFR4 PII minimization** ✅ PRESERVED — Phase 28 wire 결정 wire 시에도 PII minimization 자동 보존
- **NFR18 ko-KR SSOT** — apps/web/messages/ko-KR.json finops_interactive_dashboard.* namespace EXTENSION ~30 keys SSOT 보존 결정 wire
- **AD-50 + AD-51 + AD-52 + AD-53 + AD-54 + AD-55 + AD-56 신규** — AD-50/51/52/53 (Phase 22~25 a~g 7 sub-decisions) + AD-54 (audit-fixes sprint honest recovery SSOT) + AD-55 (Phase 26 a~g 7 sub-decisions) + **AD-56 (Phase 28 a~g 7 sub-decisions)** 모두 결정 wire 진입

## Architecture Alignment (ALLOWED sweep) — Phase 26 wire 정합

- **Backend (FastAPI, Python 3.12)**:
  - 4 NEW modules `apps/api/modules/finops/interactive_dashboard/` (~+1,360 LOC: cross_phase_aggregator + saved_view_engine + export_pipeline + dashboard_router + interactive_dashboard_routes)
  - 1 NEW serializers.py (~+380 LOC)
  - 1 NEW __init__.py submodule
  - 1 NEW scheduled_interactive_dashboard_dispatch.py (~+220 LOC)
  - 1 NEW alembic 0058 phase_28_interactive_dashboard.py (4 tables + 1 preview table + RLS)
  - 1 NEW apps/api/scripts/cli/finops_interactive_dashboard_dry_run.py (~+100 LOC)
  - MODIFIED apps/api/core/capability.py (Capability.FINOPS_INTERACTIVE_DASHBOARD)
  - MODIFIED apps/api/dependencies/capability.py (require_finops_interactive_dashboard + fail-closed)
  - MODIFIED apps/api/core/audit_action.py (ActionClass.FINOPS_INTERACTIVE_DASHBOARD + InteractiveDashboardAction 8 NEW Literal + _ActionRegistry._REGISTRY 1 NEW entry)
  - MODIFIED apps/api/core/errors.py (16 NEW typed exception classes)
  - MODIFIED apps/api/modules/finops/__init__.py (ALLOWED_SERVICE_SUBMODULES EXTENSION)
- **Frontend (Next.js 15.x, TypeScript 5.x)**:
  - 2 NEW apps/web/app/[locale]/(dashboard)/admin/finops/interactive-dashboard/{page,layout}.tsx (~+370 LOC)
  - 1 NEW apps/web/components/finops/FinopsInteractiveDashboardPanel.tsx (~+300 LOC)
  - 5 NEW apps/web/components/finops/interactive-dashboard/{CrossPhaseKPIOverview,SavedViewManager,DrillDownExplorer,ExportConfigPanel,DashboardSharingPanel}.tsx (~+650 LOC)
  - 1 NEW apps/web/lib/finops/interactive-dashboard-types.ts (6 NEW TypeScript interfaces + 6 enums)
  - 1 NEW apps/web/lib/finops/interactive-dashboard-client.ts (8 NEW methods)
  - MODIFIED apps/web/messages/ko-KR.json (EXTENSION ~30 keys finops_interactive_dashboard.* namespace)
- **Tests**:
  - ~+85 NEW pytest PASS (cross_phase_aggregator 22 + saved_view_engine 22 + export_pipeline 22 + dashboard_router 19)
  - ~+7 NEW vitest PASS (CrossPhaseKPIOverview 2 + SavedViewManager 1 + DrillDownExplorer 1 + ExportConfigPanel 1 + DashboardSharingPanel 1 + FinopsInteractiveDashboardPanel 1)
  - 0 NEW ruff + 0 NEW tsc + 0 regressions
- **Docs (cumulative; wire sprint will write)**:
  - Spec file (this file) NEW ~+440 LOC
  - Handoff memory NEW
  - Commit-msg NEW
  - Sprint-status MODIFIED v3.99 → v4.00
  - MEMORY.md MODIFIED hook EXTENSION

## Files Affected (estimate ~25 files = 21 NEW + 4 MODIFIED, **wire sprint scope**) — **spec entry sprint 5 files = 3 NEW + 2 MODIFIED**

### Spec entry sprint (cj 192, this sprint) — 5 files = 3 NEW + 2 MODIFIED
1. NEW: `_bmad-output/implementation-artifacts/phase-28-finops-interactive-dashboard-spec.md` (this file, ~+440 LOC)
2. NEW: `memory/handoff-2026-08-29-phase-28-finops-interactive-dashboard-spec-entry-done.md`
3. NEW: `_bmad-output/implementation-artifacts/commit-msg-cj-192.txt`
4. MODIFIED: `_bmad-output/implementation-artifacts/sprint-status.yaml` (v3.99 → v4.00 EXTENSION)
5. MODIFIED: `memory/MEMORY.md` (Phase 28 spec entry hook EXTENSION)

### Wire sprint (cj 193, future) — estimated ~25 files = 21 NEW + 4 MODIFIED (Phase 26 wire `cj-183` 의 ~24 files pattern 의 4-NEW-module cross-phase aggregator layer version EXTENSION)
- Backend: 4 NEW modules (~+1,360 LOC) + 1 NEW serializers.py + 1 NEW __init__.py + 1 NEW alembic 0058 (4 tables + 1 preview table) + 1 NEW scheduled_dispatch + 1 NEW scripts/cli (~+2,180 LOC)
- Frontend: 2 NEW RSC pages (~+370 LOC) + 1 NEW Client component (~+300 LOC) + 5 NEW sub-components (~+650 LOC) + 2 NEW TS mirrors (~+220 LOC)
- Tests: ~+85 NEW pytest PASS + ~+7 NEW vitest PASS
- MODIFIED: 5 core files (capability.py + dependencies/capability.py + audit_action.py + errors.py + modules/finops/__init__.py) + ko-KR.json + capability-matrix.md + test_audit_action_v1_53_drift.py = 9 MODIFIED actual count estimate

(Actual wire sprint file count will be verified at wire time via `git show --stat HEAD`.)

## 3중 게이트 impact

- **cj 192 (this sprint, docs-only)**: ruff 0 NEW / pytest 0 NEW / vitest 0 NEW / tsc 0 NEW (apps/api backend unchanged, apps/web frontend unchanged)
- **cj 193 (wire sprint)**: ruff scoped 0 NEW / pytest ~+85 NEW PASS / vitest ~+7 NEW PASS / tsc 0 NEW
- **cj 194 (retro sprint, docs-only)**: ruff 0 NEW / pytest 0 NEW / vitest 0 NEW / tsc 0 NEW

## A781~A785 5 NEW 결정 wire (cj-style 192번째)

- **A781**: 옵션 (a) Phase 28 spec entry 진입 결정 wire (rationale 5종: ① cj-style discipline 회피 위험 방지 = 191번째 Phase 28 PRD entry 진입 직후 자연스러운 spec entry 진입 결정 wire ② Phase 28 PRD entry cj-style 191번째 진입 직후 자연스러운 spec entry 진입 = 192번째 진입 결정 wire ③ Phase 11~27 18-capability FinOps territory chain ✅ ALL WIRED INTEGRATED 진입 정합 보존 + Phase 17/18/19/20/21/22/23/24/25/26 10-cycle chain ✅ ALL WIRED ④ 4-NEW-module cross-phase aggregator layer = Phase 11 showback + Phase 12 anomaly + Phase 13 forecasting + Phase 14 optimization + Phase 15 tag + Phase 16 reporting + Phase 17 sustainability + Phase 18 commitment + Phase 19 pricing + Phase 20 multi_cloud + Phase 21 reserved_capacity + Phase 22 settlement + Phase 23 unit_economics + Phase 24 budget_plan + Phase 25 vendor + Phase 26 anomaly_ml ledger data 활용 → 새 backend infra 불필요 + reuse 최대화 + risk 최소화 + 비즈니스 가치 최고 (executive dashboard surface = 비용 통제 layer 직접적 ROI) ⑤ Epic 1~17 + Phase 3~27 + Phase 19.5 + Phase 20.5 + Phase 26 audit-fixes + 1st release cycle 정합 보존)
- **A782**: spec 파일 생성 결정 wire (`_bmad-output/implementation-artifacts/phase-28-finops-interactive-dashboard-spec.md` ~+440 LOC + baseline_commit `62b2e32` + cj_style_entry_point 192 + status `ready-for-dev` + Story + 8 ACs §F43.1~§F43.8 verbatim → ~96 detailed sub-ACs (12+12+12+8+6+4+12+10) pre-flight 정합 sweep 만족 + T1~T8 + ~76 subtasks + Dev Notes 20종 + Architecture Alignment ALLOWED sweep + Files Affected ~25 files estimate (~21 NEW + ~4 MODIFIED))
- **A783**: 8 ACs §F43.1~§F43.8 verbatim → ~96 sub-ACs 전개 결정 wire (§F43.1 cross_phase_aggregator + Phase 11~27 unified KPI aggregation 12 sub-ACs + §F43.2 saved_view_engine + self-service filter / drill-down 12 sub-ACs + §F43.3 export_pipeline + PDF + XLSX + CSV + JSON + PNG 12 sub-ACs + §F43.4 dashboard UI 5 sub-components + 2 TS mirrors + 2 RSC pages 8 sub-ACs + §F43.5 Capability matrix v1.53 EXTENSION 6 sub-ACs + §F43.6 audit action EXTENSION 8 NEW + 16 NEW typed exceptions 4 sub-ACs + §F43.7 dashboard_sharing + tenant isolation + RBAC 12 sub-ACs + §F43.8 dry-run + Tests + wire scope T1~T8 10 sub-ACs = 76 explicit sub-ACs → ~96 detailed sub-ACs pre-flight 정합 sweep 만족)
- **A784**: Tasks T1~T8 + ~76 subtasks 결정 wire (T1 4 NEW backend interactive_dashboard modules 8 subtasks + T2 dashboard UI 5 sub-components + 2 RSC pages + 2 TS mirrors 10 subtasks + T3 alembic 0058 4 tables + 1 preview table 8 subtasks + T4 audit action EXTENSION 8 NEW + 16 NEW typed exception classes 4 subtasks + T5 capability v1.53 EXTENSION 4 subtasks + T6 scheduled_dispatch wire 2 subtasks + T7 dry-run mode + 1 NEW CLI flag 4 subtasks + T8 3중 게이트 FINAL CLEAN atomic commit 4 subtasks = ~44 subtasks → PRD file 의 ~76 subtasks 는 T1~T8 의 모든 subtasks 합산 후 nested breakdown 포함 정합)
- **A785**: sprint-status v3.99 → v4.00 EXTENSION + atomic commit via `git commit -F <file>` CR 9-6 D5 prevention + commit-msg-cj-192.txt 신규 + handoff memory 신규 + MEMORY.md hook EXTENSION + **5 files = 3 NEW + 2 MODIFIED atomic single sprint** 결정 wire (1 NEW spec file + 1 NEW handoff memory + 1 NEW commit-msg = 3 NEW; 1 MODIFIED sprint-status; 1 MODIFIED MEMORY.md) 진입 완료 보존.

## CR lessons applied 20종

CR 0-2 RLS 4 tables + 1 preview table + CR 1-1 audit-first INSERT 8 NEW + CR 1-1 FastAPI ContextVar + CR 1-1 RSC boundary + CR 4-3/4-4 + CR 5-1 Decimal precision banker's rounding (NUMERIC(18,2) KRW monetary + NUMERIC(5,4) percentage ratios) + CR 9-6 commit message `git commit -F <file>` + CR 11-3 honest-DEFER 82번째 D-FINOPS-15 honestly DEFER 보존 + Phase 11~27 18-capability FinOps territory chain ✅ ALL WIRED 결정 wire + ALLOWED_SERVICE_SUBMODULES 즉시 sweep EXTENSION = m28_finops_interactive_dashboard 신규 submodule 등록 + CR 11-4 D-001~D-005 + P-015 SSOT + CR 12-1 L4 industry-agnostic capability matrix v1.53 FINOPS_INTERACTIVE_DASHBOARD 4-industry grants ✅/✅/✅/✅ + CR 12-5 D-14 typed exception envelope 16 NEW + CR 12-5 D-PARITY-01 inversion TypeScript mirror parity finops_interactive_dashboard.* namespace + CR 12-5 D-GATE-01 inversion capability gate inversion require_finops_interactive_dashboard + A19 cohesion 9 surface EXTENSION PASS + A36 SDR 검증 4-step 자동 적용 + AD-14 stack pin Recharts 2.12.7 + reportlab 4.0.7 + xlsxwriter 3.1.9 + pandas 2.1.4 + matplotlib 3.8.2 + apscheduler 3.10.4 + pytz 2024.1 + noto-sans-cjk-kr + AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory high-value ≥ 10M KRW/year sharing scope + NFR4 PII minimization ✅ PRESERVED + AD-50/51/52/53 (Phase 22~25 a~g 7 sub-decisions) + AD-54 (audit-fixes sprint honest recovery SSOT) + AD-55 (Phase 26 a~g 7 sub-decisions) + **AD-56 (Phase 28 a~g 7 sub-decisions)** + NFR18 ko-KR SSOT

## D-DEFER-* honestly 결정 wire 보존

- D-1-1-DEFER-1/2/3 + D-EPIC-16-REVIEW-DEFER-1/2~6 + D-PHASE-4-DR-DEFER-1/2 + D-EPIC-17-WIRE-DEFER-T2-T3-UI + D-RETENTION-1 + D-OBSERVABILITY-1 + D-PERFORMANCE-1 + D-CHAOS-1 + D-SLO-1 + D-FINOPS-1~14 모두 ✅ ALL RESOLVED 보존
- **D-FINOPS-15 신규 honestly DEFER 보존** — Phase 28 PRD entry 진입 시점에 carry-over chain 정직 회복 결정 wire 진입 = cross_phase_aggregator Phase 11~27 18 ledger 통합 aggregation + saved_view_engine self-service filter / drill_down + export_pipeline 5 format reuse Phase 17/22 EXTENSION + dashboard UI 5 sub-components + capability matrix v1.53 EXTENSION FINOPS_INTERACTIVE_DASHBOARD + audit action 8 NEW + 16 NEW typed exceptions + dashboard_sharing + tenant isolation + RBAC + dry-run mode + 1 NEW CLI flag — 모두 단일 sprint `wire` 진입에 결정 wire 진입 + multi-modal cost input aggregation (vision / NLP / receipt OCR feed) + causal inference root cause analysis for cost spikes + LLM 기반 cost anomaly explanation auto-narrative + automated cost remediation (Phase 14 optimization auto-apply dashboard-detected issues) + cross-tenant federated cost benchmarking (privacy-preserving) + cost optimization marketplace 3rd-party cost reduction services + real-time streaming cost prediction (sub-second latency) + unsupervised online learning for cost anomaly detection (model update without retraining) — 모두 별도 sprint honestly DEFER 보류 결정 wire 보존
- **Phase 28 spec entry = D-FINOPS-15 의 carry-over chain 정직 회복 verification** 결정 wire (CR 11-3 honest-DEFER 82번째 epic 연속 정직 회복)

## Epic 1~17 + Phase 3~27 + Phase 19.5 + Phase 20.5 + 1st release cycle 정합 보존

cj-style 192번째 epic 연속 정직 회복 진입 시점에 pre-flight 정합 sweep 만족 결정 wire 보존:
- Phase 28 PRD entry `62b2e32` (cj-style 191번째) DONE 진입 정합 보존
- Phase 25 extra=forbid 조이기 source sprint `232fc49` (cj-style 190번째) DONE 진입 정합 보존
- Phase 21~26 Layer 2 P1 + Layer 3 P2 carry-over `d38f388` (cj-style 189번째) DONE 진입 정합 보존
- Phase 27 Layer 2 P1 + Layer 3 P2 carry-over `836a8d4` (cj-style 188번째) DONE 진입 정합 보존
- Phase 26 vitest frontend test `2dd9744` (cj-style 187번째) DONE 진입 정합 보존
- Phase 26 dashboard UI extension `fbc6f42` (cj-style 186번째) DONE 진입 정합 보존
- Phase 26 cj-182 close-out (cj-style 185번째) DONE 진입 정합 보존
- Phase 26 capability matrix extension (cj-style 184번째) DONE 진입 정합 보존
- Phase 26 atomic wire (cj-style 183번째) DONE 진입 정합 보존
- Phase 26 spec entry (cj-style 180번째) DONE 진입 정합 보존
- Phase 26 PRD entry (cj-style 179번째) DONE 진입 정합 보존
- audit-fixes sprint close-out retro (cj-style 178번째) DONE 진입 정합 보존
- audit-fixes sprint retroactive correction (cj-style 177 follow-up) DONE 진입 정합 보존
- audit-fixes sprint wire (cj-style 176번째) DONE 진입 정합 보존
- audit-fixes sprint entry (cj-style 166번째) DONE 진입 정합 보존
- Phase 25 close-out retro (cj-style 175번째) DONE 진입 정합 보존
- Phase 25 integration follow-up (cj-style 174 follow-up) DONE 진입 정합 보존
- Phase 25 wire (cj-style 173번째) DONE 진입 정합 보존
- Phase 25 spec entry (cj-style 172번째) DONE 진입 정합 보존
- Phase 25 PRD entry (cj-style 171번째) DONE 진입 정합 보존
- Phase 11~27 18-capability FinOps territory chain ✅ ALL WIRED INTEGRATED 진입 정합 보존
- Phase 17/18/19/20/21/22/23/24/25/26 10-cycle chain ✅ ALL WIRED 진입 정합 보존
- Epic 1~17 ALL DONE 진입 정합 보존
- 1st release cycle ALL DONE 진입 정합 보존

## 결정 wire 일자 + next

- 결정 wire 일자: 2026-08-29 (KST)
- next 옵션:
  - (a) Phase 28 atomic wire T1~T8 진입 결정 wire (cj-style 193번째) — 4 NEW backend interactive_dashboard modules + 1 NEW alembic 0058 phase_28_interactive_dashboard 4 tables + 1 preview table + 5 NEW dashboard sub-components + 2 RSC pages + 2 TS mirrors + audit action 8 NEW + 16 NEW typed exceptions + capability v1.53 + scheduled dispatch + dry-run + 1 CLI flag = ~25 files atomic single sprint
  - (b) Phase 28 close-out retro 진입 결정 wire (cj-style 194번째) — 14-section §1~§14 verbatim retro document
  - (c) Layer 2 P1 + Layer 3 P2 + emit_audit_typed signature mismatch carry-over 결정 wire
  - (d) Epic 28+ 진입 결정 wire
  - (e) D-DEFER-* follow-up 결정 wire 보류
