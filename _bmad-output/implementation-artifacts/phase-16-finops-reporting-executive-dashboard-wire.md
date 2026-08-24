---
baseline_commit: 4f11d03
status: ready-for-dev
cj_style_entry_point: 126
story_key: phase-16-finops-reporting-executive-dashboard-wire
---

# Phase 16 FinOps Reporting & Executive Dashboard wire spec (cj-style 126번째 epic 연속 정직 회복)

## Story

**As a** finance team / FinOps analyst / department cost center owner / cloud architect / compliance officer / tenant admin / enterprise onboarding lead / executive leadership (CEO + CFO + CTO) / board observer
**I want** FinOps Reporting & Executive Dashboard territory 결정 wire (executive_dashboard_aggregator `aggregate_executive_dashboard` + 5 modules cross-join (Phase 11 showback + Phase 12 anomaly + Phase 13 forecast + Phase 14 optimization + Phase 15 tag_governance) + ExecutiveRollup TypedDict 16 fields + 4 scope options tenant + department + cost_center + product_line + cross-module KPI selector `select_cross_module_kpis` + 8 NEW KPI calculations (total_monthly_cost_krw + monthly_cost_growth_pct + cost_per_employee_krw + cost_anomaly_count_30d + forecast_deviation_pct + idle_cost_monthly_krw + tag_compliance_pct + optimization_realized_savings_krw) + 5-module index hints + executive report generation engine `generate_executive_report` + PDF + CSV + Excel 3 export_format + 3 cadence monthly + quarterly + annual + ExecutiveReport TypedDict 13 fields + scheduled dispatch KST cron `schedule_executive_dispatch` + 4 cron schedules weekly Mon 09:00 + monthly 1st-day 09:00 + quarterly 1st-day 09:00 + annual Jan-1 09:00 + recipient resolver Slack + Email + S3 archive dispatch + ScheduledDispatch TypedDict 10 fields + tenant-scoped executive role RBAC owner-only + Role.EXECUTIVE_VIEWER 1 NEW enum + require_executive_role() 1 NEW dep + executive dashboard UI 5 sub-components (ExecutiveDashboardAggregator + CrossModuleKPISelector + ExecutiveReportGeneratorPanel + ScheduledDispatchConfigPanel + ComplianceTrendMiniChart) + ko-KR.json `finops_reporting.*` namespace EXTENSION ~30 keys + Capability matrix v1.41 → v1.42 EXTENSION FINOPS_REPORTING + audit-first INSERT 8 NEW + ActionClass.FINOPS_REPORTING)
**so that** Phase 11 wire `e020ad0` (showback + chargeback) + Phase 12 wire `f3c0e63` (anomaly detection + budget alert) + Phase 13 wire `8b98030` (forecasting + capacity planning) + Phase 14 wire `e904485` (optimization + rightsizing) + Phase 15 wire `1b800d9` (tag governance + cost allocation) 의 5-module FinOps territory 의 natural EXECUTIVE ROLLUP LAYER 결정 wire 진입 (5 module outputs → single executive rollup for CEO/CFO/CTO decision-making + cross-module KPI selector 의 8 NEW KPI calculations = total monthly cost + growth + per-employee + anomaly count + forecast deviation + idle cost + tag compliance + optimization realized savings + executive report generation engine 의 PDF/CSV/Excel 3 export format + monthly/quarterly/annual 3 cadence + scheduled dispatch KST cron 4 cron schedules weekly/monthly/quarterly/annual + recipient resolver Slack + Email + S3 archive + tenant-scoped executive role RBAC owner-only + executive dashboard UI 5 sub-components + ko-KR.json `finops_reporting.*` EXTENSION ~30 keys) = Phase 15 FinOps territory 의 EXECUTIVE ROLLUP LAYER EXTENSION 결정 (5 module outputs → executive decision layer) + Phase 16 PRD entry `4f11d03` (cj-style 125번째) DONE 진입 정합 보존 + Epic 12 2FA 챌린지 보존 + AD-22 owner-only RBAC 보존 + D-FINOPS-6 honestly DEFER 보존 진입 결정 wire + Phase 15 close-out retro `102f370` §13 verbatim 해소 결정 wire 보존).

## Context

cj-style Phase 16 2번째 진입점 (cj-style 126번째) 진입 결정 wire 진입 완료:
- Phase 16 PRD entry `4f11d03` (cj-style 125번째) DONE 진입 정합 보존
- Phase 15 close-out retro `102f370` (cj-style 124번째) + Phase 15 atomic wire T1~T8 `1b800d9` (cj-style 123번째) + Phase 15 spec entry `69c29df` (cj-style 122번째) + Phase 15 PRD entry `87393b4` (cj-style 121번째) + Phase 14 close-out retro `5b367d9` (cj-style 120번째) + Phase 14 atomic wire T1~T8 `e904485` (cj-style 119번째) + Phase 14 spec entry `30637f6` (cj-style 118번째) + Phase 14 PRD entry `0e3f8d9` (cj-style 117번째) + Phase 13 close-out retro `850b4f8` (cj-style 116번째) + Phase 13 atomic wire T1~T8 `8b98030` (cj-style 115번째) + Phase 13 spec entry `77ed55f` (cj-style 114번째) + Phase 13 PRD entry `d31dfc8` (cj-style 113번째) + Phase 12 close-out retro `3354e83` (cj-style 112번째) + Phase 12 atomic wire T1~T8 `f3c0e63` (cj-style 111번째) + Phase 12 spec entry `8c5f374` (cj-style 110번째) + Phase 12 PRD entry `344c7eb` (cj-style 109번째) + Phase 11 close-out retro `80df15b` (cj-style 108번째) + Phase 11 atomic wire T1~T8 `e020ad0` (cj-style 107번째) + Phase 11 spec entry `82c93a8` (cj-style 106번째) + Phase 11 PRD entry `16d7698` (cj-style 105번째) + Phase 10 close-out retro `733d428` (cj-style 104번째) + Phase 10 wire `ac5d6c5` (cj-style 103번째) 결정 wire 모두 DONE 진입 정합 보존
- D-FINOPS-6 honestly DEFER 보존 진입 결정 wire (Phase 16 PRD entry 진입 시점에 carry-over chain 정직 회복 결정 wire + Phase 15 close-out retro `102f370` §13 + Phase 14 close-out retro `5b367d9` §13 + Phase 13 close-out retro `850b4f8` §13 + Phase 12 close-out retro `3354e83` §13 + Phase 11 close-out retro `80df15b` §12 + Phase 10 close-out retro `733d428` §10 + Phase 9 close-out retro `634427d` §10 + Phase 8 close-out retro `ab495a8` §10 + Phase 7 close-out retro `326fa9f` §10 + Phase 6 close-out retro `f9f006c` §13 + Epic 17 close-out retro `be8f3bd` §11 + 1st release close-out retro §6 "FinOps Reporting & Executive Dashboard 결정 wire 보류, Phase 16+ 진입 시점" verbatim 해소 + Phase 16 PRD entry 진입 시점에 1 NEW 결정 wire)
- D-FINOPS-5 ✅ RESOLVED 보존 진입 결정 wire
- D-FINOPS-4 ✅ RESOLVED 보존 진입 결정 wire
- D-FINOPS-3 ✅ RESOLVED 보존 진입 결정 wire
- D-FINOPS-2 ✅ RESOLVED 보존 진입 결정 wire
- D-FINOPS-1 ✅ RESOLVED 보존 진입 결정 wire
- D-SLO-1 ✅ RESOLVED 보존 진입 결정 wire
- D-CHAOS-1 ✅ RESOLVED 보존 진입 결정 wire
- D-PERFORMANCE-1 ✅ RESOLVED 보존 진입 결정 wire
- D-OBSERVABILITY-1 ✅ RESOLVED 보존 진입 결정 wire
- Phase 16 PRD entry 의 8 ACs §F32.1~§F32.8 verbatim 결정 wire 보존
- Capability matrix v1.41 → v1.42 EXTENSION FINOPS_REPORTING 1 NEW row 결정 wire (industry-agnostic 4-industry grants ✅/✅/✅/✅ CR 12-1 L4 precedent 미러)
- AD-43 FinOps Reporting & Executive Dashboard 신규 결정 wire 진입 (a)~(g) 7 sub-decisions

## 8 ACs (PRD §F32.1~§F32.8 verbatim) → ~86 detailed sub-ACs

### §F32.1 executive_dashboard_aggregator (12 sub-ACs)
- F32.1-1 `apps/api/modules/finops/executive_dashboard_aggregator.py` NEW (~+200 LOC + `aggregate_executive_dashboard(tenant_id, scope_type, scope_id, period_key) -> ExecutiveRollup` + 5 modules cross-join (Phase 11 wire `e020ad0` showback + Phase 12 wire `f3c0e63` anomaly + Phase 13 wire `8b98030` forecast + Phase 14 wire `e904485` optimization + Phase 15 wire `1b800d9` tag_governance) 결정 wire + CR 12-5 D-PARITY-01 verbatim + 4 industries baseline industry-agnostic + per-tenant override EXTENSION)
- F32.1-2 `ExecutiveRollup` TypedDict 16 fields 결정 wire (rollup_id UUID PK + tenant_id UUID + scope_type enum tenant/department/cost_center/product_line + scope_id TEXT + period_key TEXT e.g. "2026-08" + showback_total_krw NUMERIC(20, 2) + anomaly_count_30d INT + forecast_projection_krw NUMERIC(20, 2) + optimization_savings_krw NUMERIC(20, 2) + tag_compliance_pct NUMERIC(8, 4) + idle_cost_krw NUMERIC(20, 2) + department_breakdown JSONB + cost_center_breakdown JSONB + resource_type_breakdown JSONB + generated_at TIMESTAMPTZ + trace_id TEXT)
- F32.1-3 4 scope_type 옵션 결정 wire (tenant 전체 tenant rollup + department 특정 department_id 기준 + cost_center 특정 cost_center_id 기준 + product_line 특정 product_line_id 기준 + scope_type default = tenant + per-tenant override JSONB + cross-tenant isolation test)
- F32.1-4 5-module cross-join 결정 wire ((1) Phase 11 showback_total_krw from `phase_11_finops_showback_department` table + (2) Phase 12 anomaly_count_30d from `phase_12_finops_anomaly_detection` table + (3) Phase 13 forecast_projection_krw from `phase_13_finops_forecast_projection` table + (4) Phase 14 optimization_savings_krw from `phase_14_finops_optimization_recommendation` table + (5) Phase 15 tag_compliance_pct from `phase_15_finops_compliance_report` table → single ExecutiveRollup join 결정 wire)
- F32.1-5 5-module cross-join RLS 자동 적용 결정 wire (CR 0-2 verbatim + tenant_id selector + cross-tenant isolation 검증 + Phase 11~15 wire 의 phase_11_finops_* ~ phase_15_finops_* tables RLS 정합 보존)
- F32.1-6 period selector 결정 wire (period_key TEXT e.g. "2026-08" monthly + "2026-Q3" quarterly + "2026" annual + per-tenant override period_selector default current month + Phase 11 wire `e020ad0` 의 showback period selector EXTENSION 정합 + Phase 8 wire `60d4ea1` 의 cost-engine 12-period benchmark EXTENSION 정합)
- F32.1-7 ExecutiveRollup cache layer 결정 wire (Redis cache 24h TTL per (tenant_id + scope_type + scope_id + period_key) tuple + cache_key SHA-256 + cache miss 시 recompute + audit-first INSERT `cross_module_kpi_calculated` CR 1-1 verbatim)
- F32.1-8 5-module index hints 결정 wire (PostgreSQL index on `(tenant_id, period_key)` for phase_11_finops_showback + index on `(tenant_id, detected_at)` for phase_12_finops_anomaly + index on `(tenant_id, forecast_period)` for phase_13_finops_forecast + index on `(tenant_id, recommendation_status)` for phase_14_finops_optimization + index on `(tenant_id, period_key)` for phase_15_finops_compliance 결정 wire)
- F32.1-9 executive dashboard pure validator CR 11-4 P-015 verbatim 결정 wire (`validate_executive_rollup(tenant_id, scope_type, scope_id)` validator + 5 layer defense (syntax + semantic + tenant-scope RLS + scope_type validation + period_key validation) + `ExecutiveRollupInvalidError(400)` + `ExecutiveRollupScopeError(404)` + `ExecutiveRollupPeriodError(422)` CR 12-5 D-14 envelope)
- F32.1-10 audit-first INSERT `executive_dashboard_viewed` 결정 wire (CR 1-1 verbatim 적용 + ActionClass.FINOPS_REPORTING 신규 정의 + emit_audit_typed BEFORE executive dashboard view + per-tenant RLS 자동 적용 + multi-tenant isolation test)
- F32.1-11 typed exception envelope CR 12-5 D-14 verbatim 결정 wire (4 NEW typed exception classes: `ExecutiveRollupInvalidError(400)` + `ExecutiveRollupScopeError(404)` + `ExecutiveRollupPeriodError(422)` + `ExecutiveRollupCrossModuleJoinError(500)`)
- F32.1-12 dry-run mode `--finops-reporting-dry-run` CLI flag 결정 wire (dry-run 시 actual ExecutiveRollup calculation skip + audit-first INSERT `finops_reporting_dry_run_executed` CR 1-1 verbatim + phase_16_finops_executive_rollup_preview table alembic 0048 신규 결정 wire)

### §F32.2 cross_module_kpi_selector (10 sub-ACs)
- F32.2-1 `apps/api/modules/finops/cross_module_kpi.py` NEW (~+150 LOC + `select_cross_module_kpis(tenant_id, scope_type, scope_id, period_key, kpi_set) -> Dict[str, KPIMetric]` + 8 NEW KPI calculations + Phase 11~15 wire 의 5-module outputs EXTENSION 결정 wire)
- F32.2-2 KPI #1 `total_monthly_cost_krw` 결정 wire (sum of all showback + chargeback costs in current month from `phase_11_finops_showback_department` table + KPI value NUMERIC(20, 2) + KPI delta vs previous month + KPI trend arrow up/down/flat)
- F32.2-3 KPI #2 `monthly_cost_growth_pct` 결정 wire ((current_month_cost - previous_month_cost) / previous_month_cost × 100 + KPI value NUMERIC(8, 4) + growth_pct > +5% → increasing / -5~+5% → stable / < -5% → decreasing + per-tenant override growth_threshold default 5%)
- F32.2-4 KPI #3 `cost_per_employee_krw` 결정 wire (total_monthly_cost_krw / active_employee_count + active_employee_count from tenant_settings.headcount JSONB + KPI value NUMERIC(20, 2) + benchmark vs industry baseline + Epic 1 carry-over (auth) tenant_settings.headcount EXTENSION 정합)
- F32.2-5 KPI #4 `cost_anomaly_count_30d` 결정 wire (count of anomaly_detection.severity in ('high', 'critical') from `phase_12_finops_anomaly_detection` table within last 30 days + KPI value INT + KPI delta vs previous 30d + Phase 12 wire `f3c0e63` 의 anomaly severity classification EXTENSION 정합)
- F32.2-6 KPI #5 `forecast_deviation_pct` 결정 wire ((actual_cost - forecast_projection) / forecast_projection × 100 from `phase_13_finops_forecast_projection` table + KPI value NUMERIC(8, 4) + forecast_deviation_pct > +10% → over_budget / -10~+10% → on_track / < -10% → under_budget + per-tenant override deviation_threshold default 10%)
- F32.2-7 KPI #6 `idle_cost_monthly_krw` 결정 wire (sum of optimization_recommendation.potential_savings_krw where recommendation_type='idle_resource' from `phase_14_finops_optimization_recommendation` table + KPI value NUMERIC(20, 2) + KPI delta vs previous month + Phase 14 wire `e904485` 의 idle resource detection EXTENSION 정합)
- F32.2-8 KPI #7 `tag_compliance_pct` 결정 wire (avg(compliance_pct) from `phase_15_finops_compliance_report` table current period + KPI value NUMERIC(8, 4) + KPI delta vs previous period + Phase 15 wire `1b800d9` 의 compliance report EXTENSION 정합)
- F32.2-9 KPI #8 `optimization_realized_savings_krw` 결정 wire (sum of realized_savings_krw where recommendation_status='realized' from `phase_14_finops_optimization_recommendation` table + KPI value NUMERIC(20, 2) + KPI delta vs previous month + Phase 14 wire `e904485` 의 optimization accuracy tracker EXTENSION 정합)
- F32.2-10 `KPIMetric` TypedDict 8 fields 결정 wire (kpi_name TEXT + kpi_value NUMERIC + kpi_unit TEXT e.g. "KRW" + "pct" + "count" + kpi_delta NUMERIC nullable + kpi_trend enum up/down/flat + kpi_threshold_status enum on_track/warning/critical + kpi_computed_at TIMESTAMPTZ) + audit-first INSERT `cross_module_kpi_calculated` CR 1-1 verbatim + per-tenant RLS 자동 적용

### §F32.3 executive report generation engine (12 sub-ACs)
- F32.3-1 `apps/api/modules/finops/executive_report_generator.py` NEW (~+220 LOC + `generate_executive_report(tenant_id, scope_type, scope_id, period_key, cadence, export_format) -> ExecutiveReport` + ExecutiveRollup EXTENSION + 3 export_format PDF + CSV + Excel 결정 wire)
- F32.3-2 3 export_format 옵션 결정 wire ((1) PDF `reportlab==4.0.7` library + Jinja2 HTML template → PDF conversion + chart embedding Recharts 2.12.7 → PNG → PDF embed + (2) CSV standard csv module + UTF-8 BOM + (3) Excel `openpyxl==3.1.2` library + multi-sheet workbook + chart embedding + 3 format 모두 tenant_id RLS 적용 + per-tenant override export_format default PDF)
- F32.3-3 3 cadence 옵션 결정 wire ((1) monthly = first day of next month + (2) quarterly = first day of next quarter + (3) annual = January 1 of next year + cadence default = monthly + per-tenant override cadence default monthly)
- F32.3-4 PDF report structure 결정 wire (`reportlab.platypus.SimpleDocTemplate` + 6 sections (cover_page + executive_summary + kpi_dashboard + cost_breakdown + trend_analysis + appendix) + Recharts 2.12.7 AD-14 stack pin chart PNG embedding + ExecutiveRollup JSON → Jinja2 template → HTML → PDF conversion)
- F32.3-5 CSV report structure 결정 wire (1 CSV file + 8 columns (period_key + total_monthly_cost_krw + monthly_cost_growth_pct + cost_per_employee_krw + cost_anomaly_count_30d + forecast_deviation_pct + idle_cost_monthly_krw + tag_compliance_pct + optimization_realized_savings_krw) + UTF-8 BOM + ko-KR locale 결정 wire)
- F32.3-6 Excel report structure 결정 wire (`openpyxl.Workbook` + 5 sheets (Summary + KPIMetrics + CostBreakdown + TrendAnalysis + AuditTrail) + 8 KPI metrics in KPIMetrics sheet + Recharts chart embedding via openpyxl.chart + xlsx MIME type 결정 wire)
- F32.3-7 `ExecutiveReport` TypedDict 13 fields 결정 wire (report_id UUID PK + tenant_id UUID + scope_type enum tenant/department/cost_center/product_line + scope_id TEXT + period_key TEXT + cadence enum monthly/quarterly/annual + export_format enum pdf/csv/excel + report_file_url TEXT S3 archive URL + report_size_bytes BIGINT + report_generated_at TIMESTAMPTZ + generated_by UUID actor_id + status enum generating/completed/failed/expired + trace_id TEXT)
- F32.3-8 S3 archive 결정 wire (`apps/api/integrations/s3_archive.py` EXTENSION + report_file upload to s3://costmgr-exec-reports/{tenant_id}/{period_key}/{report_id}.{ext} + presigned URL 7-day expiry + audit-first INSERT `executive_report_generated` CR 1-1 verbatim + Epic 12 2FA 챌린지 보존)
- F32.3-9 executive report delivery 결정 wire (`apps/api/jobs/executive_report_delivery.py` NEW ~+100 LOC + cron KST monthly 1st-day 09:00 + quarterly 1st-day 09:00 + annual Jan-1 09:00 + delivery targets owner-only Slack `#bizup-executive-reports` channel + Email recipients resolver + S3 archive URL + audit-first INSERT `executive_report_dispatched` CR 1-1 verbatim)
- F32.3-10 recipient resolver 결정 wire (recipient_strategy 4종 (1) `owner_only` tenant owner email + Slack DM + (2) `executive_team` tenant_settings.executive_team JSONB + (3) `board_observers` tenant_settings.board_observers JSONB + (4) `custom_recipients` tenant_settings.executive_report_recipients JSONB + recipient_strategy default = owner_only + per-tenant override JSONB + AD-22 owner-only RBAC verbatim 보존)
- F32.3-11 audit-first INSERT `executive_report_generated` + `executive_report_exported` 2 NEW 결정 wire (CR 1-1 verbatim 적용 + ActionClass.FINOPS_REPORTING + emit_audit_typed BEFORE/AFTER executive report event + per-tenant RLS 자동 적용 + multi-tenant isolation test)
- F32.3-12 typed exception envelope CR 12-5 D-14 verbatim 결정 wire (4 NEW typed exception classes: `ExecutiveReportGenerationError(500)` + `ExecutiveReportExportError(500)` + `ExecutiveReportDeliveryError(500)` + `ExecutiveReportArchiveError(500)`)

### §F32.4 scheduled_dispatch_kst_cron (10 sub-ACs)
- F32.4-1 `apps/api/jobs/scheduled_executive_dispatch.py` NEW (~+180 LOC + `schedule_executive_dispatch(tenant_id, dispatch_schedule) -> ScheduledDispatch` + 4 cron schedules weekly + monthly + quarterly + annual KST 결정 wire)
- F32.4-2 4 cron schedules 결정 wire ((1) weekly `0 9 * * 1` KST Monday 09:00 (Phase 11 wire `e020ad0` weekly showback summary EXTENSION) + (2) monthly `0 9 1 * *` KST 1st day of month 09:00 + (3) quarterly `0 9 1 1,4,7,10 *` KST 1st day of quarter 09:00 + (4) annual `0 9 1 1 *` KST January 1 09:00 + KST timezone `pytz.timezone('Asia/Seoul')` 결정 wire)
- F32.4-3 cron scheduler library 결정 wire (`apscheduler==3.10.4` AsyncIOScheduler + PersistentJobStore + audit-first INSERT `executive_scheduled_dispatch_evaluated` CR 1-1 verbatim + Phase 11 wire `e020ad0` 의 chargeback monthly close-out cron EXTENSION 정합 + Phase 12 wire `f3c0e63` 의 budget_alert cron EXTENSION 정합)
- F32.4-4 recipient resolver dispatch 결정 wire (Slack `slack-sdk==3.23.0` AD-14 stack pin webhook URL + Email `sendgrid==6.11.0` AD-14 stack pin recipient list + S3 archive presigned URL + 3 dispatch targets 모두 owner-only RBAC AD-22 verbatim 보존)
- F32.4-5 `ScheduledDispatch` TypedDict 10 fields 결정 wire (dispatch_id UUID PK + tenant_id UUID + dispatch_schedule enum weekly/monthly/quarterly/annual + cron_expression TEXT e.g. "0 9 1 * *" + recipient_strategy enum owner_only/executive_team/board_observers/custom_recipients + recipient_list JSONB + report_id UUID FK nullable + status enum scheduled/running/completed/failed/cancelled + scheduled_at TIMESTAMPTZ + trace_id TEXT)
- F32.4-6 dispatch lifecycle state machine 결정 wire (`scheduled` default → `running` cron trigger 시 → `completed` 성공 시 → `failed` 실패 시 retry 3회 → `cancelled` owner manual cancel 시 + per-tenant override max_retry default 3 + audit-first INSERT `executive_scheduled_dispatch_evaluated` CR 1-1 verbatim)
- F32.4-7 dispatch idempotency 결정 wire (per-(tenant_id + dispatch_schedule + period_key) tuple unique key + 중복 dispatch skip + audit log 에 idempotency_check metadata 저장 + Phase 12 wire `f3c0e63` 의 anomaly detection idempotency EXTENSION 정합)
- F32.4-8 dispatch retry policy 결정 wire (failed dispatch 의 exponential backoff 1min → 5min → 30min + 3회 실패 시 owner-only Slack alert + Epic 12 2FA 챌린지 보존 + audit log 기록 + Phase 9 wire `e7670e1` chaos experiment 의 retry policy EXTENSION 정합)
- F32.4-9 audit-first INSERT `executive_scheduled_dispatch_evaluated` + `executive_report_dispatched` 2 NEW 결정 wire (CR 1-1 verbatim 적용 + ActionClass.FINOPS_REPORTING + emit_audit_typed BEFORE/AFTER scheduled dispatch event + per-tenant RLS 자동 적용)
- F32.4-10 typed exception envelope CR 12-5 D-14 verbatim 결정 wire (4 NEW typed exception classes: `ScheduledDispatchError(500)` + `CronExpressionInvalidError(400)` + `RecipientResolverError(404)` + `DispatchIdempotencyViolationError(422)`)

### §F32.5 tenant_scoped_executive_role_rbac (10 sub-ACs)
- F32.5-1 `apps/api/core/rbac.py` MODIFIED 결정 wire (Role.EXECUTIVE_VIEWER = "executive_viewer" 1 NEW enum + tenant-scoped role + tenant_settings.executive_viewers JSONB list 결정 wire + Phase 1 carry-over (auth) RBAC EXTENSION 정합)
- F32.5-2 `apps/api/dependencies/capability.py` MODIFIED 결정 wire (require_executiveRole 1 NEW dep + tenant_settings.executive_viewers validation + per-tenant RBAC + AD-22 owner-only RBAC EXTENSION 정합 + Epic 12 2FA 챌린지 mandatory)
- F32.5-3 executive viewer permission set 결정 wire (read-only access to ExecutiveRollup + ExecutiveReport + ScheduledDispatch + cross-module KPI selector + dashboard view + report generation + dispatch config + NO write/modify permission + per-tenant override permission_set JSONB)
- F32.5-4 tenant-scoped RBAC 검증 결정 wire (tenant_settings.executive_viewers 의 user_id list 검증 + Epic 1 carry-over (auth) 의 SSO_ENTERPRISE (Epic 15 wire) JWT token validation EXTENSION 정합 + cross-tenant access 차단 403 Forbidden)
- F32.5-5 owner-only access (AD-22 verbatim) 결정 wire (executive dashboard view + executive report generation + scheduled dispatch config 모두 owner-only RBAC AD-22 verbatim 보존 + executive viewer 는 read-only + modify/config 는 owner-only + Epic 12 2FA 챌린지 mandatory)
- F32.5-6 Epic 12 2FA 챌린지 mandatory 결정 wire (executive dashboard view + executive report generation + scheduled dispatch config 모두 Epic 12 2FA 챌린지 mandatory + Epic 12 wire `a63646c` 의 2FA 챌린지 보존 정합)
- F32.5-7 audit-first INSERT `executive_dashboard_viewed` + `executive_report_exported` + `executive_scheduled_dispatch_evaluated` 3 NEW RBAC context 결정 wire (CR 1-1 verbatim 적용 + ActionClass.FINOPS_REPORTING + role_id + user_id + tenant_id + 2fa_verified BOOLEAN metadata + per-tenant RLS 자동 적용)
- F32.5-8 미허용 tenant 의 executive reporting 진입 차단 결정 wire (require_executiveRole dep + capability gate per-tenant on/off + FINOPS_REPORTING capability 부재 시 403 Forbidden + FORBIDDEN_KO message 결정 wire ("FinOps Reporting & Executive Dashboard capability 미허용 tenant") + Epic 12 2FA 챌린지 보존 + AD-22 owner-only RBAC 정합)
- F32.5-9 phase_11~15 carry-over 진입 차단 결정 wire (executive reporting 진입 시 FINOPS_SHOWBACK + FINOPS_CHARGEBACK + FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT + FINOPS_FORECASTING_CAPACITY_PLANNING + FINOPS_OPTIMIZATION + FINOPS_TAG_GOVERNANCE capability 도 동시에 검증 + executive reporting 가 FINOPS_REPORTING 만 있고 Phase 11~15 capability 없는 경우 403 Forbidden 결정 wire)
- F32.5-10 typed exception envelope CR 12-5 D-14 verbatim 결정 wire (3 NEW typed exception classes: `ExecutiveRolePermissionError(403)` + `TenantScopeViolationError(403)` + `CapabilityGateViolationError(403)`)

### §F32.6 executive_dashboard_ui (10 sub-ACs)
- F32.6-1 `apps/web/app/[locale]/(dashboard)/admin/finops/executive-dashboard/page.tsx` NEW (~+220 LOC + 5 components (`ExecutiveDashboardAggregator` + `CrossModuleKPISelector` + `ExecutiveReportGeneratorPanel` + `ScheduledDispatchConfigPanel` + `ComplianceTrendMiniChart`) 결정 wire + owner-only RBAC AD-22 verbatim + Epic 12 2FA 챌린지 보존 결정 wire)
- F32.6-2 `ExecutiveDashboardAggregator` component 결정 wire (4 scope_type 옵션 selectbox tenant + department + cost_center + product_line + period_selector monthly + quarterly + annual + 8 KPI metrics summary card + 5-module breakdown table + refresh button + Recharts 2.12.7 AD-14 stack pin + ko-KR.json `finops_reporting.dashboard.*` 6 keys CR 11-4 D-002 verbatim SSOT)
- F32.6-3 `CrossModuleKPISelector` component 결정 wire (8 KPI toggle selectbox (total_monthly_cost_krw + monthly_cost_growth_pct + cost_per_employee_krw + cost_anomaly_count_30d + forecast_deviation_pct + idle_cost_monthly_krw + tag_compliance_pct + optimization_realized_savings_krw) + KPI value display + KPI delta arrow + KPI trend chart mini line chart 30 days + Recharts 2.12.7 AD-14 stack pin + Phase 12 wire `f3c0e63` 의 AnomalyDetectorPanel KPI cards EXTENSION 정합)
- F32.6-4 `ExecutiveReportGeneratorPanel` component 결정 wire (3 cadence radio button monthly + quarterly + annual + 3 export_format selectbox PDF + CSV + Excel + scope selector + period selector + generate button + recent reports list table (report_id + cadence + export_format + generated_at + size + download button) + ko-KR.json `finops_reporting.report.*` 6 keys)
- F32.6-5 `ScheduledDispatchConfigPanel` component 결정 wire (4 cron schedule selectbox weekly + monthly + quarterly + annual + 4 recipient_strategy radio button owner_only + executive_team + board_observers + custom_recipients + recipient list editor + Slack channel + Email recipients + S3 archive enable toggle + enable/disable button + test_dispatch_button dry-run + Recharts 2.12.7 AD-14 stack pin + ko-KR.json `finops_reporting.dispatch.*` 6 keys)
- F32.6-6 `ComplianceTrendMiniChart` component 결정 wire (Phase 15 tag_compliance_pct 의 past 12-month trend line chart Recharts 2.12.7 AD-14 stack pin + Phase 15 wire `1b800d9` 의 ComplianceReportPanel EXTENSION 정합 + Phase 11 wire `e020ad0` 의 showback trend chart EXTENSION 정합 + ko-KR.json `finops_reporting.trend.*` 4 keys)
- F32.6-7 ko-KR.json `finops_reporting.*` namespace EXTENSION ~30 keys 결정 wire (CR 11-4 D-002 verbatim SSOT) + `finops_reporting.dashboard.title` + `finops_reporting.dashboard.scope_tenant` + `finops_reporting.dashboard.scope_department` + `finops_reporting.dashboard.scope_cost_center` + `finops_reporting.dashboard.scope_product_line` + `finops_reporting.dashboard.refresh` + `finops_reporting.kpi.total_monthly_cost_krw` + `finops_reporting.kpi.monthly_cost_growth_pct` + `finops_reporting.kpi.cost_per_employee_krw` + `finops_reporting.kpi.cost_anomaly_count_30d` + `finops_reporting.kpi.forecast_deviation_pct` + `finops_reporting.kpi.idle_cost_monthly_krw` + `finops_reporting.kpi.tag_compliance_pct` + `finops_reporting.kpi.optimization_realized_savings_krw` + `finops_reporting.report.cadence_monthly` + `finops_reporting.report.cadence_quarterly` + `finops_reporting.report.cadence_annual` + `finops_reporting.report.format_pdf` + `finops_reporting.report.format_csv` + `finops_reporting.report.format_excel` + `finops_reporting.report.generate` + `finops_reporting.dispatch.weekly` + `finops_reporting.dispatch.monthly` + `finops_reporting.dispatch.quarterly` + `finops_reporting.dispatch.annual` + `finops_reporting.dispatch.recipient_owner_only` + `finops_reporting.dispatch.recipient_executive_team` + `finops_reporting.dispatch.recipient_board_observers` + `finops_reporting.dispatch.recipient_custom` + `finops_reporting.dispatch.enable` + `finops_reporting.dispatch.disable` + `finops_reporting.dispatch.test` 등 결정 wire)
- F32.6-8 ARIA labels 결정 wire (WCAG 2.1 AA compliance Epic 12 의 2FA 챌린지 UI 와 동일 표준 + keyboard navigation Tab + Enter + Arrow keys + screen reader 지원 + Phase 15 Epic 1 UX v1.0 locked decision 결정 wire Dark MVP / WCAG AA / Professional / ko-KR verbatim 보존)
- F32.6-9 toast notification 결정 wire (executive_dashboard_viewed 시 toast 자동 표시 + executive_report_generated 시 toast + executive_report_dispatched 시 toast + executive_scheduled_dispatch_evaluated 시 toast + Phase 15 wire `1b800d9` 의 toast notification EXTENSION 정합)
- F32.6-10 Vitest RTL render discipline CR 11-4 D-003 verbatim 결정 wire (~8 NEW vitest cases ExecutiveDashboardAggregator 2 + CrossModuleKPISelector 2 + ExecutiveReportGeneratorPanel 1 + ScheduledDispatchConfigPanel 1 + ComplianceTrendMiniChart 1 + ko-KR SSOT 1 = ~8 NEW vitest PASS + Phase 15 wire `1b800d9` 의 ~5 NEW vitest cases EXTENSION 정합)

### §F32.7 Capability matrix v1.42 EXTENSION (12 sub-ACs)
- F32.7-1 Capability matrix v1.41 → v1.42 EXTENSION 결정 wire (1 NEW row FINOPS_REPORTING industry-agnostic 4-industry grants ✅/✅/✅/✅ CR 12-1 L4 precedent 미러)
- F32.7-2 `apps/api/core/capability.py` MODIFIED 결정 wire (Capability.FINOPS_REPORTING = "finops_reporting" 1 NEW enum + 4 `_INDUSTRY_CAPABILITIES` blocks EXTENSION industry-agnostic ✅/✅/✅/✅)
- F32.7-3 `apps/api/dependencies/capability.py` MODIFIED 결정 wire (require_finops_reporting 1 NEW dep + `__all__` EXTENSION)
- F32.7-4 `docs/capability-matrix.md` MODIFIED 결정 wire (capability matrix v1.41 → v1.42 EXTENSION + 1 NEW row FINOPS_REPORTING industry-agnostic 4-industry grants ✅/✅/✅/✅ + FINOPS_REPORTING section 신규 추가)
- F32.7-5 `apps/api/modules/finops/reporting/__init__.py` NEW + `apps/api/modules/finops/reporting/serializers.py` NEW 결정 wire (Phase 15 wire `1b800d9` m23_finops_tag_governance EXTENSION pattern verbatim 미러 + m24_finops_reporting module 결정 wire)
- F32.7-6 미허용 tenant 의 executive reporting 진입 차단 결정 wire (require_finops_reporting dep + capability gate per-tenant on/off + 403 Forbidden + FORBIDDEN_KO message 결정 wire ("FinOps Reporting & Executive Dashboard capability 미허용 tenant") + Epic 12 2FA 챌린지 보존 + AD-22 owner-only RBAC 정합)
- F32.7-7 phase_11~15 carry-over 진입 차단 결정 wire (executive reporting 진입 시 FINOPS_SHOWBACK + FINOPS_CHARGEBACK + FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT + FINOPS_FORECASTING_CAPACITY_PLANNING + FINOPS_OPTIMIZATION + FINOPS_TAG_GOVERNANCE capability 도 동시에 검증 + FINOPS_REPORTING 만 있고 Phase 11~15 capability 없는 경우 403 Forbidden 결정 wire)
- F32.7-8 drift detector 8 NEW pytest cases 결정 wire (`tests/integration/test_capability_matrix_v1_42_drift.py` NEW + Phase 15 wire `1b800d9` `test_capability_matrix_v1_41_drift.py` 패턴 verbatim 미러)
- F32.7-9 m24_finops_reporting module 결정 wire (apps/api/modules/finops/__init__.py EXTENSION + m24_finops_reporting.reporting_serializers NEW 결정 wire + Phase 15 wire `1b800d9` m23_finops_tag_governance.tag_governance_serializers EXTENSION pattern verbatim 미러)
- F32.7-10 SSOT RED→GREEN EXTENSION + A36 SDR 검증 4-step 자동 적용 결정 wire (capability matrix v1.42 신규 1 row + capability.py EXTENSION 1 NEW enum + require_finops_reporting 1 NEW dep 결정 wire + drift detector EXTENSION)
- F32.7-11 CR 12-1 L4 industry-agnostic capability 결정 wire (FINOPS_REPORTING industry-agnostic 4-industry grants ✅/✅/✅/✅ 결정 wire manufacturing + service + manufacturing_service + manufacturing_service_other 모두 허용)
- F32.7-12 capability gate 의 fail-closed 결정 wire (미허용 tenant 의 executive reporting 진입 차단 + capability matrix v1.42 row 부재 시 fail-closed + Capability enum 부재 시 fail-closed + AD-22 owner-only RBAC 정합 + Epic 12 2FA 챌린지 보존 + NFR4 PII minimization 정합 보존)

### §F32.8 dry-run + Tests + wire scope T1~T8 (12 sub-ACs)
- F32.8-1 dry-run mode 결정 wire (`--finops-reporting-dry-run` + `--finops-executive-dashboard-dry-run` + `--finops-cross-module-kpi-dry-run` + `--finops-executive-report-dry-run` + `--finops-scheduled-dispatch-dry-run` 5 CLI flag + ExecutiveRollup dry-run parameter + cross-module KPI dry-run parameter + executive report dry-run parameter + scheduled dispatch dry-run parameter + dry-run 시 actual `executive_dashboard_viewed` + `cross_module_kpi_calculated` + `executive_report_generated` + `executive_report_exported` + `executive_report_dispatched` + `executive_scheduled_dispatch_evaluated` audit-first INSERT skip 결정 wire)
- F32.8-2 dry-run 의 preview 결과 결정 wire (phase_16_finops_executive_rollup_preview + phase_16_finops_cross_module_kpi_preview + phase_16_finops_executive_report_preview + phase_16_finops_scheduled_dispatch_preview 4 table 결정 wire + preview_id UUID PK + tenant_id UUID + preview_type enum + period_key TEXT + preview_data JSONB + computed_at TIMESTAMPTZ DEFAULT NOW() + trace_id TEXT + RLS 자동 적용 CR 0-2 verbatim 결정 wire + audit-first INSERT `finops_reporting_dry_run_executed` CR 1-1 verbatim 결정 wire)
- F32.8-3 dry-run 의 CLI flag 결정 wire (`--finops-reporting-dry-run` + `--finops-executive-dashboard-dry-run` + `--finops-cross-module-kpi-dry-run` + `--finops-executive-report-dry-run` + `--finops-scheduled-dispatch-dry-run` 5 NEW CLI flag + Phase 15 wire `1b800d9` `--finops-tag-policy-dry-run` + `--finops-untagged-resource-dry-run` + `--finops-allocation-rule-dry-run` + `--finops-compliance-report-dry-run` + `--finops-chargeback-reconciliation-dry-run` 패턴 verbatim 미러)
- F32.8-4 tests ~+60 NEW pytest PASS 결정 wire (executive_dashboard_aggregator 8 + cross_module_kpi 10 + executive_report_generator 9 + scheduled_executive_dispatch 7 + alembic 0048 6 + audit action 8 + capability matrix v1.42 8 + executive_rbac 4 = ~+60 NEW pytest PASS)
- F32.8-5 vitest tests ~+8 NEW vitest PASS 결정 wire (ExecutiveDashboardAggregator 2 + CrossModuleKPISelector 2 + ExecutiveReportGeneratorPanel 1 + ScheduledDispatchConfigPanel 1 + ComplianceTrendMiniChart 1 + ko-KR SSOT 1 = ~8 NEW vitest PASS + Phase 15 wire `1b800d9` 의 ~5 NEW vitest cases EXTENSION 정합)
- F32.8-6 ruff + tsc 0 NEW + SDR drift gate 결정 wire (0 NEW ruff + 0 NEW tsc + 0 regressions + SDR drift gate PASS 결정 wire + A36 SDR 검증 4-step 자동 적용)
- F32.8-7 wire scope T1~T8 결정 wire (~+27-33 files estimate = ~+21 NEW + ~+12 MODIFIED atomic single sprint = Phase 15 wire `1b800d9` 의 ~19 files pattern verbatim 미러)
- F32.8-8 A19 cohesion pattern 9 surface EXTENSION PASS 결정 wire (FinOps Reporting & Executive Dashboard surface NEW = F32.1~F32.8 + spec surface EXTENSION + test surface EXTENSION + docs surface EXTENSION)
- F32.8-9 CR lessons applied 17종 결정 wire (CR 0-2 + CR 1-1 + CR 4-3/4-4 + CR 1-1 ContextVar + CR 1-1 RSC boundary + CR 9-6 + CR 11-3 + CR 11-4 + CR 12-1 + CR 12-5 D-14 + CR 12-5 D-PARITY-01 + CR 12-5 D-GATE-01 + A19 cohesion + A36 SDR 검증 + AD-14 + AD-22 + NFR4)
- F32.8-10 D-DEFER-* honestly 결정 wire (D-FINOPS-6 honestly preserved → Phase 16 PRD entry 진입 시점에 carry-over chain 정직 회복 결정 wire + D-FINOPS-5 ✅ RESOLVED + D-FINOPS-4 ✅ RESOLVED + D-FINOPS-3 ✅ RESOLVED + D-FINOPS-2 ✅ RESOLVED + D-FINOPS-1 ✅ RESOLVED + D-SLO-1 ✅ RESOLVED + D-CHAOS-1 ✅ RESOLVED + D-PERFORMANCE-1 ✅ RESOLVED + D-OBSERVABILITY-1 ✅ RESOLVED + D-RETENTION-1 ✅ RESOLVED + D-EPIC-17-WIRE-DEFER-T2-T3-UI ✅ RESOLVED + D-PHASE-4-DR-DEFER-1/2 ✅ RESOLVED + D-EPIC-16-REVIEW-DEFER-2~6 ✅ RESOLVED + D-1-1-DEFER-1/2/3 ✅ RESOLVED 모두 보존)
- F32.8-11 Epic 1 ~ Epic 17 + Phase 3 ~ Phase 15 + 1st release cycle 정합 보존 결정 wire (cj-style 125번째 wire entry 모두 DONE 진입 정합 보존 + Phase 16 PRD entry `4f11d03` + Phase 15 close-out retro `102f370` + Phase 15 atomic wire T1~T8 `1b800d9` + Phase 15 spec entry `69c29df` + Phase 15 PRD entry `87393b4` 모두 정합)
- F32.8-12 partial wire 시도 0건 + single sprint atomic docs-only wire 1 진입점 결정 wire (cj-style 126번째 epic 연속 정직 회복 Phase 16 spec entry atomic docs-only wire 5 files atomic single sprint 결정 wire)

## 8 tasks (T1~T8) + 68 subtasks

### T1: executive_dashboard_aggregator + executive_reporting module (10 subtasks)
- T1.1: `apps/api/modules/finops/executive_dashboard_aggregator.py` NEW (~+200 LOC + aggregate_executive_dashboard 함수 + 5-module cross-join + ExecutiveRollup TypedDict 16 fields + 4 scope_type 옵션 tenant/department/cost_center/product_line + 5-module cross-join RLS 자동 적용 CR 0-2 verbatim + 4 industries baseline industry-agnostic 결정 wire)
- T1.2: ExecutiveRollup TypedDict 16 fields 결정 wire (rollup_id + tenant_id + scope_type enum + scope_id + period_key + showback_total_krw + anomaly_count_30d + forecast_projection_krw + optimization_savings_krw + tag_compliance_pct + idle_cost_krw + department_breakdown + cost_center_breakdown + resource_type_breakdown + generated_at + trace_id)
- T1.3: 4 scope_type 옵션 결정 wire (tenant 전체 tenant rollup + department 특정 department_id + cost_center 특정 cost_center_id + product_line 특정 product_line_id + scope_type default = tenant + per-tenant override JSONB)
- T1.4: 5-module cross-join 결정 wire (Phase 11 showback_total_krw + Phase 12 anomaly_count_30d + Phase 13 forecast_projection_krw + Phase 14 optimization_savings_krw + Phase 15 tag_compliance_pct → single ExecutiveRollup join + Phase 11 wire `e020ad0` + Phase 12 wire `f3c0e63` + Phase 13 wire `8b98030` + Phase 14 wire `e904485` + Phase 15 wire `1b800d9` EXTENSION 정합)
- T1.5: period selector 결정 wire (period_key TEXT monthly/quarterly/annual + per-tenant override period_selector default current month + Phase 11 wire `e020ad0` 의 showback period selector EXTENSION 정합 + Phase 8 wire `60d4ea1` 의 cost-engine 12-period benchmark EXTENSION 정합)
- T1.6: ExecutiveRollup cache layer 결정 wire (Redis cache 24h TTL per (tenant_id + scope_type + scope_id + period_key) tuple + cache_key SHA-256 + cache miss 시 recompute + audit-first INSERT `cross_module_kpi_calculated` CR 1-1 verbatim)
- T1.7: 5-module index hints 결정 wire (PostgreSQL index on `(tenant_id, period_key)` for phase_11_finops_showback + index on `(tenant_id, detected_at)` for phase_12_finops_anomaly + index on `(tenant_id, forecast_period)` for phase_13_finops_forecast + index on `(tenant_id, recommendation_status)` for phase_14_finops_optimization + index on `(tenant_id, period_key)` for phase_15_finops_compliance)
- T1.8: executive dashboard pure validator CR 11-4 P-015 verbatim 적용 결정 wire (validate_executive_rollup + 5 layer defense + ExecutiveRollupInvalidError(400) + ExecutiveRollupScopeError(404) + ExecutiveRollupPeriodError(422) CR 12-5 D-14 envelope)
- T1.9: audit-first INSERT `executive_dashboard_viewed` 결정 wire (CR 1-1 verbatim 적용 + ActionClass.FINOPS_REPORTING + emit_audit_typed BEFORE executive dashboard view + per-tenant RLS 자동 적용 + multi-tenant isolation test)
- T1.10: 8 NEW pytest cases 결정 wire (ExecutiveRollup TypedDict 16 fields + 4 scope_type 옵션 + 5-module cross-join + period selector + cache layer + 5-module index hints + audit-first INSERT + typed exception envelope)

### T2: cross_module_kpi + 8 NEW KPI + executive_reporting module (10 subtasks)
- T2.1: `apps/api/modules/finops/cross_module_kpi.py` NEW (~+150 LOC + select_cross_module_kpis 함수 + 8 NEW KPI calculations + Phase 11~15 wire 의 5-module outputs EXTENSION 결정 wire + CR 12-5 D-PARITY-01 verbatim)
- T2.2: KPIMetric TypedDict 8 fields 결정 wire (kpi_name + kpi_value NUMERIC + kpi_unit TEXT e.g. "KRW"/"pct"/"count" + kpi_delta NUMERIC nullable + kpi_trend enum up/down/flat + kpi_threshold_status enum on_track/warning/critical + kpi_computed_at + audit-first INSERT `cross_module_kpi_calculated` CR 1-1 verbatim)
- T2.3: KPI #1 total_monthly_cost_krw + KPI #2 monthly_cost_growth_pct 결정 wire (sum of all showback + chargeback costs current month + (current_month_cost - previous_month_cost) / previous_month_cost × 100 + per-tenant override growth_threshold default 5%)
- T2.4: KPI #3 cost_per_employee_krw 결정 wire (total_monthly_cost_krw / active_employee_count from tenant_settings.headcount JSONB + benchmark vs industry baseline + Epic 1 carry-over (auth) tenant_settings.headcount EXTENSION 정합)
- T2.5: KPI #4 cost_anomaly_count_30d + KPI #5 forecast_deviation_pct 결정 wire (count of anomaly_detection.severity in ('high', 'critical') within last 30 days from phase_12_finops_anomaly_detection + (actual_cost - forecast_projection) / forecast_projection × 100 from phase_13_finops_forecast_projection + per-tenant override deviation_threshold default 10%)
- T2.6: KPI #6 idle_cost_monthly_krw + KPI #7 tag_compliance_pct 결정 wire (sum of optimization_recommendation.potential_savings_krw where recommendation_type='idle_resource' from phase_14_finops_optimization + avg(compliance_pct) from phase_15_finops_compliance_report current period + Phase 14 + Phase 15 wire EXTENSION 정합)
- T2.7: KPI #8 optimization_realized_savings_krw 결정 wire (sum of realized_savings_krw where recommendation_status='realized' from phase_14_finops_optimization + KPI delta vs previous month + Phase 14 wire `e904485` 의 optimization accuracy tracker EXTENSION 정합)
- T2.8: cross-module KPI selector period selector + scope selector 결정 wire (period_key TEXT monthly/quarterly/annual + 4 scope_type 옵션 tenant/department/cost_center/product_line + per-tenant override JSONB)
- T2.9: KPI threshold classification 결정 wire (각 KPI 별 threshold_status (on_track/warning/critical) + per-tenant override threshold JSONB + per-KPI override JSONB)
- T2.10: 10 NEW pytest cases 결정 wire (8 KPI calculations + KPIMetric TypedDict + period selector + scope selector + threshold classification + audit-first INSERT + typed exception envelope + multi-tenant isolation)

### T3: executive_report_generator + 3 export_format + 3 cadence (10 subtasks)
- T3.1: `apps/api/modules/finops/executive_report_generator.py` NEW (~+220 LOC + generate_executive_report 함수 + 3 export_format PDF/CSV/Excel + 3 cadence monthly/quarterly/annual 결정 wire + CR 12-5 D-PARITY-01 verbatim)
- T3.2: ExecutiveReport TypedDict 13 fields 결정 wire (report_id + tenant_id + scope_type enum + scope_id + period_key + cadence enum + export_format enum + report_file_url TEXT S3 archive URL + report_size_bytes BIGINT + report_generated_at + generated_by UUID actor_id + status enum generating/completed/failed/expired + trace_id)
- T3.3: 3 export_format 옵션 결정 wire ((1) PDF reportlab==4.0.7 library + Jinja2 HTML template → PDF conversion + Recharts 2.12.7 chart PNG embedding + (2) CSV standard csv module + UTF-8 BOM + (3) Excel openpyxl==3.1.2 + multi-sheet workbook + chart embedding + 3 format 모두 tenant_id RLS 적용)
- T3.4: 3 cadence 옵션 결정 wire ((1) monthly = first day of next month + (2) quarterly = first day of next quarter + (3) annual = January 1 of next year + cadence default = monthly + per-tenant override cadence default monthly)
- T3.5: PDF report structure 결정 wire (reportlab.platypus.SimpleDocTemplate + 6 sections cover_page + executive_summary + kpi_dashboard + cost_breakdown + trend_analysis + appendix + Recharts 2.12.7 AD-14 stack pin chart PNG embedding + ExecutiveRollup JSON → Jinja2 template → HTML → PDF conversion)
- T3.6: CSV report structure + Excel report structure 결정 wire (CSV 8 columns period_key + 8 KPI metrics + UTF-8 BOM + ko-KR locale / Excel openpyxl.Workbook + 5 sheets Summary + KPIMetrics + CostBreakdown + TrendAnalysis + AuditTrail + Recharts chart embedding via openpyxl.chart + xlsx MIME type)
- T3.7: S3 archive 결정 wire (apps/api/integrations/s3_archive.py EXTENSION + report_file upload to s3://costmgr-exec-reports/{tenant_id}/{period_key}/{report_id}.{ext} + presigned URL 7-day expiry + audit-first INSERT `executive_report_generated` CR 1-1 verbatim + Epic 12 2FA 챌린지 보존)
- T3.8: executive report delivery 결정 wire (apps/api/jobs/executive_report_delivery.py NEW ~+100 LOC + cron KST monthly 1st-day 09:00 + quarterly 1st-day 09:00 + annual Jan-1 09:00 + delivery targets owner-only Slack `#bizup-executive-reports` channel + Email recipients resolver + S3 archive URL + audit-first INSERT `executive_report_dispatched` CR 1-1 verbatim)
- T3.9: recipient resolver 결정 wire (recipient_strategy 4종 owner_only + executive_team + board_observers + custom_recipients + recipient_strategy default = owner_only + per-tenant override JSONB + AD-22 owner-only RBAC verbatim 보존)
- T3.10: typed exception envelope CR 12-5 D-14 verbatim 결정 wire (4 NEW typed exception classes: ExecutiveReportGenerationError + ExecutiveReportExportError + ExecutiveReportDeliveryError + ExecutiveReportArchiveError + 9 NEW pytest cases)

### T4: scheduled_executive_dispatch + 4 cron schedules + recipient resolver (10 subtasks)
- T4.1: `apps/api/jobs/scheduled_executive_dispatch.py` NEW (~+180 LOC + schedule_executive_dispatch 함수 + 4 cron schedules weekly + monthly + quarterly + annual KST 결정 wire)
- T4.2: 4 cron schedules 결정 wire ((1) weekly 0 9 * * 1 KST Monday 09:00 + (2) monthly 0 9 1 * * KST 1st day of month 09:00 + (3) quarterly 0 9 1 1,4,7,10 * KST 1st day of quarter 09:00 + (4) annual 0 9 1 1 * KST January 1 09:00 + KST timezone pytz.timezone('Asia/Seoul'))
- T4.3: cron scheduler library 결정 wire (apscheduler==3.10.4 AsyncIOScheduler + PersistentJobStore + audit-first INSERT `executive_scheduled_dispatch_evaluated` CR 1-1 verbatim + Phase 11 wire `e020ad0` 의 chargeback monthly close-out cron EXTENSION 정합 + Phase 12 wire `f3c0e63` 의 budget_alert cron EXTENSION 정합)
- T4.4: recipient resolver dispatch 결정 wire (Slack slack-sdk==3.23.0 AD-14 stack pin webhook URL + Email sendgrid==6.11.0 AD-14 stack pin recipient list + S3 archive presigned URL + 3 dispatch targets 모두 owner-only RBAC AD-22 verbatim 보존)
- T4.5: ScheduledDispatch TypedDict 10 fields 결정 wire (dispatch_id + tenant_id + dispatch_schedule enum weekly/monthly/quarterly/annual + cron_expression TEXT + recipient_strategy enum + recipient_list JSONB + report_id UUID FK nullable + status enum scheduled/running/completed/failed/cancelled + scheduled_at + trace_id)
- T4.6: dispatch lifecycle state machine 결정 wire (scheduled default → running cron trigger → completed 성공 → failed 실패 시 retry 3회 → cancelled owner manual cancel + per-tenant override max_retry default 3 + audit-first INSERT `executive_scheduled_dispatch_evaluated` CR 1-1 verbatim)
- T4.7: dispatch idempotency 결정 wire (per-(tenant_id + dispatch_schedule + period_key) tuple unique key + 중복 dispatch skip + audit log 에 idempotency_check metadata 저장 + Phase 12 wire `f3c0e63` 의 anomaly detection idempotency EXTENSION 정합)
- T4.8: dispatch retry policy 결정 wire (failed dispatch 의 exponential backoff 1min → 5min → 30min + 3회 실패 시 owner-only Slack alert + Epic 12 2FA 챌린지 보존 + audit log 기록 + Phase 9 wire `e7670e1` chaos experiment 의 retry policy EXTENSION 정합)
- T4.9: audit-first INSERT `executive_scheduled_dispatch_evaluated` + `executive_report_dispatched` 2 NEW 결정 wire (CR 1-1 verbatim 적용 + ActionClass.FINOPS_REPORTING + emit_audit_typed BEFORE/AFTER scheduled dispatch event + per-tenant RLS 자동 적용)
- T4.10: typed exception envelope CR 12-5 D-14 verbatim 결정 wire (4 NEW typed exception classes: ScheduledDispatchError + CronExpressionInvalidError + RecipientResolverError + DispatchIdempotencyViolationError + 7 NEW pytest cases)

### T5: alembic 0048 phase_16_finops_reporting (8 subtasks)
- T5.1: `apps/api/alembic/versions/0048_phase_16_finops_reporting.py` NEW (~+250 LOC + 6 tables CREATE + indexes + RLS policies + down_revision "0047_phase_15_tag_governance" 결정 wire)
- T5.2: phase_16_finops_executive_rollup table 17 columns 결정 wire (rollup_id UUID PK + tenant_id UUID + scope_type TEXT enum + scope_id TEXT + period_key TEXT + showback_total_krw NUMERIC(20, 2) + anomaly_count_30d INTEGER + forecast_projection_krw NUMERIC(20, 2) + optimization_savings_krw NUMERIC(20, 2) + tag_compliance_pct NUMERIC(8, 4) + idle_cost_krw NUMERIC(20, 2) + department_breakdown JSONB + cost_center_breakdown JSONB + resource_type_breakdown JSONB + cache_key TEXT + generated_at TIMESTAMPTZ + trace_id TEXT + UNIQUE (tenant_id, scope_type, scope_id, period_key))
- T5.3: phase_16_finops_cross_module_kpi table 11 columns 결정 wire (kpi_id UUID PK + tenant_id UUID + scope_type TEXT enum + scope_id TEXT + period_key TEXT + kpi_name TEXT + kpi_value NUMERIC(20, 2) + kpi_unit TEXT + kpi_delta NUMERIC nullable + kpi_trend TEXT enum + kpi_threshold_status TEXT enum + computed_at TIMESTAMPTZ + trace_id TEXT + INDEX)
- T5.4: phase_16_finops_executive_report table 14 columns 결정 wire (report_id UUID PK + tenant_id UUID + scope_type TEXT enum + scope_id TEXT + period_key TEXT + cadence TEXT enum + export_format TEXT enum + report_file_url TEXT + report_size_bytes BIGINT + report_generated_at TIMESTAMPTZ + generated_by UUID + status TEXT enum + expires_at TIMESTAMPTZ + trace_id TEXT + INDEX)
- T5.5: phase_16_finops_scheduled_dispatch table 12 columns 결정 wire (dispatch_id UUID PK + tenant_id UUID + dispatch_schedule TEXT enum + cron_expression TEXT + recipient_strategy TEXT enum + recipient_list JSONB + report_id UUID FK nullable + status TEXT enum + scheduled_at TIMESTAMPTZ + last_run_at TIMESTAMPTZ nullable + next_run_at TIMESTAMPTZ nullable + trace_id TEXT + INDEX)
- T5.6: phase_16_finops_executive_viewer table 8 columns 결정 wire (viewer_id UUID PK + tenant_id UUID + user_id UUID + role TEXT enum EXECUTIVE_VIEWER + granted_by UUID + granted_at TIMESTAMPTZ + expires_at TIMESTAMPTZ nullable + trace_id TEXT + UNIQUE (tenant_id, user_id))
- T5.7: phase_16_finops_recipient_strategy table 9 columns 결정 wire (recipient_strategy_id UUID PK + tenant_id UUID + strategy_name TEXT enum owner_only/executive_team/board_observers/custom_recipients + recipient_list JSONB + delivery_targets JSONB Slack/Email/S3 + enabled BOOLEAN DEFAULT TRUE + created_at + updated_at + trace_id TEXT + UNIQUE (tenant_id, strategy_name))
- T5.8: 6 tables RLS policies + 4 preview tables 결정 wire (CR 0-2 verbatim + tenant_id = current_setting('app.tenant_id')::uuid + Phase 11 wire `e020ad0` phase_11_finops_* table 정합 + Phase 12 wire `f3c0e63` phase_12_finops_* table 정합 + Phase 13 wire `8b98030` phase_13_finops_* table 정합 + Phase 14 wire `e904485` phase_14_finops_* table 정합 + Phase 15 wire `1b800d9` phase_15_finops_* table 정합 + 4 preview tables phase_16_finops_executive_rollup_preview + phase_16_finops_cross_module_kpi_preview + phase_16_finops_executive_report_preview + phase_16_finops_scheduled_dispatch_preview 결정 wire + alembic migration 6 NEW pytest cases + multi-tenant isolation test 결정 wire)

### T6: audit action EXTENSION 8 NEW + typed exception envelope (8 subtasks)
- T6.1: `apps/api/core/audit_action.py` MODIFIED 결정 wire (ActionClass.FINOPS_REPORTING 1 NEW class 신규 정의 + FinopsReportingAction Literal 8 NEW values + _ActionRegistry FINOPS_REPORTING entry 신규 1개 등록 + __all__ EXTENSION + AuditAction Union EXTENSION)
- T6.2: ActionClass.FINOPS_REPORTING = 'finops_reporting' 신규 정의 결정 wire (CR 12-1 L4 precedent 미러 FINOPS_TAG_GOVERNANCE Phase 15 wire + FINOPS_OPTIMIZATION Phase 14 wire + FINOPS_FORECASTING_CAPACITY_PLANNING Phase 13 wire + FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12 wire + FINOPS_SHOWBACK + FINOPS_CHARGEBACK Phase 11 wire pattern verbatim bind)
- T6.3: FinopsReportingAction Literal 8 NEW values 결정 wire = `executive_report_generated` + `executive_dashboard_viewed` + `executive_kpi_refreshed` + `executive_report_exported` + `executive_report_dispatched` + `executive_scheduled_dispatch_evaluated` + `finops_reporting_dry_run_executed` + `cross_module_kpi_calculated` (8 NEW) EXTENSION (CR 1-1 verbatim 적용)
- T6.4: _ActionRegistry FINOPS_REPORTING entry 신규 1개 등록 결정 wire (resource_table "phase_16_finops_*" + action_class=FINOPS_REPORTING + 8 NEW actions acceptance + reject)
- T6.5: emit_audit_typed BEFORE/AFTER FinOps Reporting event CR 1-1 verbatim 적용 결정 wire (executive_report_generated 의 audit_first INSERT 가 executive report generation 직후 실행 + executive_dashboard_viewed AFTER executive dashboard view + executive_kpi_refreshed AFTER cross-module KPI refresh + executive_report_exported AFTER export + executive_report_dispatched AFTER dispatch + executive_scheduled_dispatch_evaluated AFTER scheduled dispatch + finops_reporting_dry_run_executed AFTER dry-run + cross_module_kpi_calculated AFTER KPI 계산 + trace_id propagation + actor_id capture + tenant_id capture)
- T6.6: multi-tenant isolation 결정 wire (8 NEW action 의 tenant_id 가 RLS 와 정합 + cross-tenant audit log leak 방지 결정 wire)
- T6.7: typed exception envelope CR 12-5 D-14 verbatim 결정 wire (16 NEW typed exception classes: ExecutiveRollupInvalidError(400) + ExecutiveRollupScopeError(404) + ExecutiveRollupPeriodError(422) + ExecutiveRollupCrossModuleJoinError(500) + ExecutiveReportGenerationError(500) + ExecutiveReportExportError(500) + ExecutiveReportDeliveryError(500) + ExecutiveReportArchiveError(500) + ScheduledDispatchError(500) + CronExpressionInvalidError(400) + RecipientResolverError(404) + DispatchIdempotencyViolationError(422) + ExecutiveRolePermissionError(403) + TenantScopeViolationError(403) + CapabilityGateViolationError(403) + ReportingAccuracyDegradationError(500))
- T6.8: 8 NEW pytest cases 결정 wire (AuditAction Literal 값 검증 + ActionClass.FINOPS_REPORTING enum value + resource_table + emit_audit_typed BEFORE/AFTER FinOps Reporting event CR 1-1 verbatim 적용 + multi-tenant isolation + trace_id propagation + typed exception envelope + dry-run default)

### T7: capability v1.42 EXTENSION + frontend executive dashboard UI (8 subtasks)
- T7.1: `apps/api/core/capability.py` MODIFIED 결정 wire (Capability.FINOPS_REPORTING 1 NEW enum + 4 `_INDUSTRY_CAPABILITIES` blocks EXTENSION industry-agnostic ✅/✅/✅/✅ CR 12-1 L4 precedent 미러)
- T7.2: `apps/api/dependencies/capability.py` MODIFIED 결정 wire (require_finops_reporting 1 NEW dep + __all__ EXTENSION 결정 wire)
- T7.3: capability matrix v1.41 → v1.42 EXTENSION title update + v1.42 changelog entry prepend + 1 NEW row FINOPS_REPORTING industry-agnostic 4-industry grants ✅/✅/✅/✅ 결정 wire
- T7.4: `tests/integration/test_capability_matrix_v1_42_drift.py` NEW 8 NEW pytest cases 결정 wire (Capability.FINOPS_REPORTING enum + 4 industries grants + v1.41 + v1.40 + v1.39 + v1.38 + v1.37 + v1.36 + v1.35 + v1.34 + v1.33 + v1.32 + v1.31 + v1.30 + v1.29 preservation + Phase 5 v1.29 + Epic 16 v1.28 + Epic 17 v1.30 + Phase 6 v1.31 + Phase 7 v1.32 + Phase 8 v1.33 + Phase 9 v1.34 + Phase 10 v1.35 + Phase 11 v1.36 + Phase 12 v1.37 + Phase 13 v1.38 + Phase 13 v1.39 + Phase 14 v1.40 + Phase 15 v1.41 pattern verbatim)
- T7.5: `docs/capability-matrix.md` MODIFIED v1.41 → v1.42 EXTENSION 결정 wire (1 NEW row FINOPS_REPORTING industry-agnostic 4-industry grants + FINOPS_REPORTING section 신규 추가)
- T7.6: 미허용 tenant 의 FinOps Reporting 진입 차단 결정 wire (require_finops_reporting dep + capability gate per-tenant on/off + phase_15~11 carry-over 검증)
- T7.7: `apps/web/app/[locale]/(dashboard)/admin/finops/executive-dashboard/page.tsx` NEW (~+220 LOC + 5 components 결정 wire: ExecutiveDashboardAggregator + CrossModuleKPISelector + ExecutiveReportGeneratorPanel + ScheduledDispatchConfigPanel + ComplianceTrendMiniChart + owner-only RBAC AD-22 verbatim + Epic 12 2FA 챌린지 보존)
- T7.8: SSOT RED→GREEN EXTENSION 결정 wire (capability matrix v1.42 신규 1 row + capability.py EXTENSION 1 NEW enum + require_finops_reporting 1 NEW dep wire + drift detector EXTENSION + frontend executive dashboard UI wire)

### T8: atomic commit (4 subtasks)
- T8.1: 3중 게이트 impact NONE 결정 wire (ruff scoped 0 NEW + pytest 0 NEW failures + vitest 0 NEW failures + tsc 0 NEW errors)
- T8.2: A19 cohesion pattern 9 surface EXTENSION PASS 결정 wire (FinOps Reporting & Executive Dashboard surface NEW = F32.1~F32.8)
- T8.3: atomic commit via `git commit -F <file>` 결정 wire (CR 9-6 D5 prevention + PowerShell here-string 회피)
- T8.4: sprint-status.yaml `phase-16-spec-entry: backlog → done` transition 결정 wire

## Dev Notes (CR lessons applied 17종)

- **CR 0-2 RLS lesson ✅ APPLIED**: Phase 16 wire 시점에 phase_16_finops_executive_rollup + phase_16_finops_cross_module_kpi + phase_16_finops_executive_report + phase_16_finops_scheduled_dispatch + phase_16_finops_executive_viewer + phase_16_finops_recipient_strategy + phase_16_finops_executive_rollup_preview + phase_16_finops_cross_module_kpi_preview + phase_16_finops_executive_report_preview + phase_16_finops_scheduled_dispatch_preview 10 tables 모두 RLS 자동 적용 + multi-tenant isolation test 결정 wire + tenant-scoped result_hash 결정 wire + Phase 11~15 wire 의 phase_11_finops_* ~ phase_15_finops_* tables RLS 정합 보존
- **CR 1-1 audit-first INSERT ✅ APPLIED**: ActionClass.FINOPS_REPORTING 신규 정의 + 8 NEW audit log entries (`executive_report_generated` + `executive_dashboard_viewed` + `executive_kpi_refreshed` + `executive_report_exported` + `executive_report_dispatched` + `executive_scheduled_dispatch_evaluated` + `finops_reporting_dry_run_executed` + `cross_module_kpi_calculated` = 8 NEW) 결정 wire + emit_audit_typed BEFORE/AFTER FinOps Reporting event CR 1-1 verbatim 적용
- **CR 4-3/4-4 lessons carry ✅ APPLIED**: ExecutiveRollup aggregation + cross-module KPI baseline + executive report golden_diff pattern verbatim 미러 + tenant-scoped result_hash 결정 wire + Epic 8 wire `e117e09` capability drift detector 정합 패턴 + Phase 15 wire `1b800d9` tag governance accuracy baseline result_hash 패턴 verbatim + Phase 14 wire `e904485` optimization accuracy baseline result_hash 패턴 verbatim
- **CR 1-1 ContextVar lesson ✅ APPLIED**: trace_id request-scoped ContextVar 바인딩 + 비동기 trace context 보존 CR 1-1 verbatim 적용 + FinOps Reporting event 의 trace_id propagation 결정 wire
- **CR 1-1 RSC boundary lesson ✅ APPLIED**: `apps/web/app/[locale]/(dashboard)/admin/finops/executive-dashboard/page.tsx` Client-only + executive dashboard server-only delegation 결정 wire + CR 1-1 verbatim 적용
- **CR 9-6 commit message discipline ✅ APPLIED**: `git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention 결정 wire
- **CR 11-3 honest-DEFER discipline ✅ APPLIED**: 126번째 epic 연속 정직 회복 결정 wire (D-1-1-DEFER-* + D-EPIC-16-REVIEW-DEFER-* + D-PHASE-4-DR-DEFER-* + D-EPIC-17-WIRE-DEFER-T2-T3-UI + D-RETENTION-1 + D-OBSERVABILITY-1 + D-PERFORMANCE-1 + D-CHAOS-1 + D-SLO-1 + D-FINOPS-1 + D-FINOPS-2 + D-FINOPS-3 + D-FINOPS-4 + D-FINOPS-5 모두 ✅ ALL RESOLVED 보존 + D-FINOPS-6 honestly DEFER 보존 진입 결정 wire)
- **CR 11-4 D-001~D-005 + P-015 lessons carry ✅ APPLIED**: dry-run mode UI 진입 시 frontend territory 정합 sweep 결정 wire + ko-KR.json SSOT only + vitest RTL render discipline + owner-only RBAC + unknown state reject + ko-KR.json SSOT drift detector 결정 wire
- **CR 12-1 L4 industry-agnostic capability ✅ APPLIED**: FINOPS_REPORTING industry-agnostic 4-industry grants ✅/✅/✅/✅ 결정 wire + capability matrix v1.42 EXTENSION 결정 wire
- **CR 12-5 D-14 typed exception envelope ✅ APPLIED**: 16 NEW typed exception classes (ExecutiveRollupInvalidError(400) + ExecutiveRollupScopeError(404) + ExecutiveRollupPeriodError(422) + ExecutiveRollupCrossModuleJoinError(500) + ExecutiveReportGenerationError(500) + ExecutiveReportExportError(500) + ExecutiveReportDeliveryError(500) + ExecutiveReportArchiveError(500) + ScheduledDispatchError(500) + CronExpressionInvalidError(400) + RecipientResolverError(404) + DispatchIdempotencyViolationError(422) + ExecutiveRolePermissionError(403) + TenantScopeViolationError(403) + CapabilityGateViolationError(403) + ReportingAccuracyDegradationError(500)) 결정 wire + apps/api/main.py EXTENSION 결정 wire
- **CR 12-5 D-PARITY-01 inversion ✅ APPLIED**: Python FastAPI backend executive_dashboard_aggregator.py + cross_module_kpi.py + executive_report_generator.py + scheduled_executive_dispatch.py TypedDict ↔ TypeScript Next.js frontend finops-reporting-client.ts interface parity 결정 wire + vitest CR 12-5 D-PARITY-01 검증 결정 wire
- **CR 12-5 D-GATE-01 inversion ✅ APPLIED**: FINOPS_REPORTING capability gate per-tenant on/off + owner-only RBAC AD-22 결정 wire + gate 적용 대상 명시 결정 wire
- **A19 cohesion pattern 9 surface EXTENSION PASS ✅**: FinOps Reporting & Executive Dashboard surface NEW = F32.1~F32.8 FinOps Reporting & Executive Dashboard territory 결정 wire + spec surface EXTENSION + test surface EXTENSION + docs surface EXTENSION 결정 wire
- **A36 SDR 검증 4-step 자동 적용 ✅**: commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS 결정 wire
- **AD-14 stack pin ✅ APPLIED**: Recharts 2.12.7 + slack-sdk==3.23.0 + pdpyras==5.2.0 + sendgrid==6.11.0 + reportlab==4.0.7 + openpyxl==3.1.2 + apscheduler==3.10.4 + pytz==2024.1 결정 wire + Phase 15 wire `1b800d9` EXTENSION 결정 wire + Phase 14 wire `e904485` EXTENSION 결정 wire + Phase 13 wire `8b98030` EXTENSION 결정 wire + Phase 12 wire `f3c0e63` EXTENSION 결정 wire + Phase 11 wire `e020ad0` EXTENSION 결정 wire
- **AD-22 owner-only RBAC ✅ APPLIED**: executive dashboard view + executive report generation + scheduled dispatch config 모두 owner-only RBAC AD-22 + Epic 12 2FA 챌린지 보존 결정 wire
- **NFR4 PII minimization ✅ PRESERVED**: executive reporting data 는 사업 metric + cost amount + KPI value 만 포함, PII 미포함 결정 wire

## Architecture Alignment (cj-style ALLOWED sweep — Phase 15 wire 정합)

**ALLOWED_SERVICE_SUBMODULES sweep CR 11-3 D-2 verbatim** (Phase 5 wire `f093f8c` + Phase 7 wire `59b56cd` + Phase 8 wire `60d4ea1` + Phase 9 wire `e7670e1` + Phase 10 wire `ac5d6c5` + Phase 11 wire `e020ad0` + Phase 12 wire `f3c0e63` + Phase 13 wire `8b98030` + Phase 14 wire `e904485` + Phase 15 wire `1b800d9` 정합):

### Backend (FastAPI, Python 3.12)
- ✅ `apps/api/modules/finops/` (MODIFIED EXTENSION): `executive_dashboard_aggregator.py` + `cross_module_kpi.py` + `executive_report_generator.py` + `scheduled_executive_dispatch.py` + `reporting/__init__.py` NEW + `reporting/serializers.py` NEW + `__init__.py` EXTENSION + `serializers.py` EXTENSION
- ✅ `apps/api/core/capability.py` (MODIFIED): Capability.FINOPS_REPORTING enum EXTENSION + 4 INDUSTRY_CAPABILITIES EXTENSION
- ✅ `apps/api/core/rbac.py` (MODIFIED): Role.EXECUTIVE_VIEWER enum EXTENSION + tenant-scoped RBAC
- ✅ `apps/api/dependencies/capability.py` (MODIFIED): require_finops_reporting EXTENSION + require_executiveRole EXTENSION
- ✅ `apps/api/core/audit_action.py` (MODIFIED): ActionClass.FINOPS_REPORTING + FinopsReportingAction Literal 8 NEW + _ActionRegistry FINOPS_REPORTING entry 1 신규 등록 + __all__ EXTENSION
- ✅ `apps/api/core/errors.py` (MODIFIED): 16 NEW typed exception classes CR 12-5 D-14 verbatim
- ✅ `apps/api/alembic/versions/0048_phase_16_finops_reporting.py` (NEW): 6 tables + 4 preview tables + indexes + RLS policies
- ✅ `apps/api/jobs/executive_report_delivery.py` (NEW): cron KST monthly 1st-day 09:00 + quarterly 1st-day 09:00 + annual Jan-1 09:00 executive report delivery
- ✅ `apps/api/jobs/scheduled_executive_dispatch.py` (NEW): cron KST weekly Mon 09:00 + monthly 1st-day 09:00 + quarterly 1st-day 09:00 + annual Jan-1 09:00 scheduled dispatch
- ✅ `apps/api/integrations/s3_archive.py` (MODIFIED): executive report S3 archive upload + presigned URL
- ✅ `apps/api/main.py` (MODIFIED): /admin/finops/executive-dashboard/* endpoints EXTENSION (CR 1-1 RSC boundary 적용)

### Frontend (Next.js 15.x, TypeScript 5.x)
- ✅ `apps/web/app/[locale]/(dashboard)/admin/finops/executive-dashboard/page.tsx` (NEW): RSC + executive dashboard
- ✅ `apps/web/app/[locale]/(dashboard)/admin/finops/executive-dashboard/layout.tsx` (NEW): RTL section wrapper
- ✅ `apps/web/components/finops/FinopsExecutiveDashboardPanel.tsx` (NEW): 5 components (ExecutiveDashboardAggregator + CrossModuleKPISelector + ExecutiveReportGeneratorPanel + ScheduledDispatchConfigPanel + ComplianceTrendMiniChart)
- ✅ `apps/web/lib/finops-reporting/finops-reporting-client.ts` (NEW): ExecutiveRollup + KPIMetric + ExecutiveReport + ScheduledDispatch TypedDict CR 12-5 D-PARITY-01 verbatim + 4 fetch wrappers + FinopsReportingApiError class
- ✅ `apps/web/messages/ko-KR.json` (MODIFIED): EXTENSION `finops_reporting.*` namespace ~30 keys 결정 wire

### Tests
- ✅ `tests/api/core/test_phase_16_executive_dashboard_aggregator.py` (NEW): ~8 NEW pytest
- ✅ `tests/api/core/test_phase_16_cross_module_kpi.py` (NEW): ~10 NEW pytest
- ✅ `tests/api/core/test_phase_16_executive_report_generator.py` (NEW): ~9 NEW pytest
- ✅ `tests/api/core/test_phase_16_scheduled_executive_dispatch.py` (NEW): ~7 NEW pytest
- ✅ `tests/api/core/test_phase_16_audit_action.py` (NEW): ~8 NEW pytest
- ✅ `tests/api/core/test_phase_16_executive_rbac.py` (NEW): ~4 NEW pytest
- ✅ `tests/integration/test_finops_reporting_tenant_isolation.py` (NEW): multi-tenant isolation CR 0-2 verbatim
- ✅ `tests/integration/test_capability_matrix_v1_42_drift.py` (NEW): 8 NEW pytest cases
- ✅ `apps/web/__tests__/finops-reporting/finops-executive-dashboard.test.tsx` (NEW): ~7 NEW vitest
- ✅ `apps/web/__tests__/i18n/finops-reporting-i18n-ssot.test.ts` (NEW): SSOT drift NFR18 ko-KR 정합
- ✅ `tests/web/test_finops_reporting_dashboard_parity.py` (NEW): ~10 cases CR 12-5 D-PARITY-01 verification

### Docs
- ✅ `docs/finops-reporting-executive-dashboard.md` (NEW): ~+200 LOC 14 sections runbook 결정 wire
- ✅ `docs/capability-matrix.md` (MODIFIED): v1.41 → v1.42 EXTENSION

## Files Affected (estimate)

- **~21 NEW**: `apps/api/modules/finops/{executive_dashboard_aggregator,cross_module_kpi,executive_report_generator,scheduled_executive_dispatch}.py` (4 files) + `apps/api/modules/finops/reporting/{__init__,serializers}.py` (2 files) + `apps/api/alembic/versions/0048_phase_16_finops_reporting.py` + `apps/api/jobs/{executive_report_delivery,scheduled_executive_dispatch}.py` (2 files) + `apps/web/app/[locale]/(dashboard)/admin/finops/executive-dashboard/{page,layout}.tsx` (2 files) + `apps/web/components/finops/FinopsExecutiveDashboardPanel.tsx` + `apps/web/lib/finops-reporting/finops-reporting-client.ts` + tests (10 files) + `docs/finops-reporting-executive-dashboard.md`
- **~12 MODIFIED**: `apps/api/core/capability.py` + `apps/api/core/rbac.py` + `apps/api/dependencies/capability.py` + `apps/api/core/audit_action.py` + `apps/api/core/errors.py` + `apps/api/main.py` + `apps/api/modules/finops/__init__.py` + `apps/api/modules/finops/serializers.py` + `apps/api/integrations/s3_archive.py` + `apps/web/messages/ko-KR.json` + `docs/capability-matrix.md` + `_bmad-output/implementation-artifacts/sprint-status.yaml` + `tests/integration/conftest.py` + `apps/api/alembic/versions/script.py.mako`
- **Total**: ~33 files atomic single sprint

## Test Coverage

- **~60 NEW pytest PASS 결정 wire**:
  - `tests/api/core/test_phase_16_executive_dashboard_aggregator.py` (8 cases): ExecutiveRollup TypedDict 16 fields + 4 scope_type 옵션 + 5-module cross-join + period selector + cache layer + 5-module index hints + audit-first INSERT + typed exception envelope
  - `tests/api/core/test_phase_16_cross_module_kpi.py` (10 cases): 8 KPI calculations + KPIMetric TypedDict + period selector + scope selector + threshold classification + audit-first INSERT + typed exception envelope + multi-tenant isolation
  - `tests/api/core/test_phase_16_executive_report_generator.py` (9 cases): 3 export_format + 3 cadence + ExecutiveReport TypedDict + S3 archive + delivery + recipient resolver + audit-first INSERT + typed exception envelope
  - `tests/api/core/test_phase_16_scheduled_executive_dispatch.py` (7 cases): 4 cron schedules + ScheduledDispatch TypedDict + lifecycle state machine + idempotency + retry policy + audit-first INSERT + typed exception envelope
  - `tests/api/core/test_phase_16_audit_action.py` (8 cases): 8 NEW audit log entries + ActionClass.FINOPS_REPORTING + emit_audit_typed CR 1-1
  - `tests/api/core/test_phase_16_executive_rbac.py` (4 cases): Role.EXECUTIVE_VIEWER + require_executiveRole + tenant-scoped RBAC + Epic 12 2FA 챌린지
  - `tests/integration/test_finops_reporting_tenant_isolation.py` (6 cases): cross-tenant isolation + executive rollup isolation + cross-module KPI isolation + executive report isolation + scheduled dispatch isolation + recipient strategy isolation
  - `tests/integration/test_capability_matrix_v1_42_drift.py` (8 cases): FINOPS_REPORTING enum + 4-industry grants + v1.41 + v1.40 + ... preservation
  - **Subtotal**: ~60 NEW pytest PASS

- **~8 NEW vitest PASS 결정 wire**:
  - `apps/web/__tests__/finops-reporting/finops-executive-dashboard.test.tsx` (7 cases): ExecutiveDashboardAggregator + CrossModuleKPISelector + ExecutiveReportGeneratorPanel + ScheduledDispatchConfigPanel + ComplianceTrendMiniChart
  - `apps/web/__tests__/i18n/finops-reporting-i18n-ssot.test.ts` (1 cases): ko-KR SSOT drift detection + CR 12-5 D-PARITY-01 verification
  - **Subtotal**: ~8 NEW vitest PASS

- **0 NEW ruff 결정 wire** (apps/api backend 결정 wire + 기존 ruff scoped 0 NEW 정합 보존)
- **0 NEW tsc 결정 wire** (apps/web frontend 결정 wire + 기존 tsc 0 NEW 정합 보존)
- **0 regressions 결정 wire** (3중 게이트 FINAL CLEAN + ruff scoped 0 NEW + pytest 0 NEW failures + vitest 0 NEW failures + tsc 0 NEW errors)

## Notes

- `apps/api/main.py` EXTENSION 시 /admin/finops/executive-dashboard/* endpoints EXTENSION + require_finops_reporting dep 적용
- `apps/api/core/errors.py` EXTENSION 시 16 NEW typed exception classes + envelope CR 11-4 P-015 적용
- `apps/api/core/audit_action.py` EXTENSION 시 ActionClass.FINOPS_REPORTING + FinopsReportingAction Literal 8 NEW values + _ActionRegistry FINOPS_REPORTING entry 1 신규 등록
- m24_finops_reporting.reporting_serializers NEW Phase 16 EXTENSION 결정 wire (Phase 15 wire `1b800d9` m23_finops_tag_governance.tag_governance_serializers EXTENSION pattern verbatim 미러, wire 시점에 sprint-status.yaml action_items EXTENSION)
- Phase 11 wire `e020ad0` 의 showback department breakdown + chargeback department cost center mapping 의 자연스러운 carry-over chain 결정 wire (Phase 16 ExecutiveRollup 의 Phase 11 showback_total_krw EXTENSION territory 결정 wire)
- Phase 12 wire `f3c0e63` 의 anomaly detection severity classification + budget_alert 의 자연스러운 carry-over chain 결정 wire (Phase 16 KPI #4 cost_anomaly_count_30d EXTENSION territory 결정 wire)
- Phase 13 wire `8b98030` 의 forecast accuracy tracker MAE/MAPE/RMSE + capacity headroom analysis 90일 lookahead 의 자연스러운 carry-over chain 결정 wire (Phase 16 KPI #5 forecast_deviation_pct EXTENSION territory 결정 wire)
- Phase 14 wire `e904485` 의 optimization accuracy tracker precision/recall/realized savings + rightsizing engine 5 resource types + idle resource detection 의 자연스러운 carry-over chain 결정 wire (Phase 16 KPI #6 idle_cost_monthly_krw + KPI #8 optimization_realized_savings_krw EXTENSION territory 결정 wire)
- Phase 15 wire `1b800d9` 의 compliance report + tag_governance compliance trend 의 자연스러운 carry-over chain 결정 wire (Phase 16 KPI #7 tag_compliance_pct + ComplianceTrendMiniChart EXTENSION territory 결정 wire)
- Phase 8 wire `60d4ea1` 의 cost-engine V8 골든 fixture + 12-period benchmark 의 자연스러운 carry-over chain (Phase 16 ExecutiveRollup 의 5-module cross-join territory EXTENSION 결정 wire)
- Phase 10 wire `ac5d6c5` 의 4 SLIs 자연스러운 EXTENSION 결정 wire + Phase 9 wire `e7670e1` chaos_experiment baseline EXTENSION 결정 wire (Phase 16 dispatch retry policy EXTENSION territory 결정 wire)
- Phase 7 wire `59b56cd` observability 의 Prometheus custom metrics + Slack channel EXTENSION 결정 wire (Phase 16 executive report delivery 의 Slack `#bizup-executive-reports` channel EXTENSION territory 결정 wire)
- Epic 12 2FA 챌린지 mandatory 결정 wire (executive dashboard view + executive report generation + scheduled dispatch config 모두 Epic 12 2FA 챌린지 mandatory)
- AD-22 owner-only RBAC 보존 결정 wire (executive dashboard view + executive report generation + scheduled dispatch config 모두 owner-only)
- AD-14 stack pin 결정 wire (Recharts 2.12.7 + slack-sdk==3.23.0 + pdpyras==5.2.0 + sendgrid==6.11.0 + reportlab==4.0.7 + openpyxl==3.1.2 + apscheduler==3.10.4 + pytz==2024.1)
- NFR4 PII minimization PRESERVED (executive reporting data 는 사업 metric + cost amount + KPI value 만 포함, PII 미포함)
- 3중 게이트 impact NONE (cj-style 126번째 spec entry 진입 표준 = docs only 변경): ruff scoped 0 NEW + pytest 0 NEW + vitest 0 NEW + tsc 0 NEW
- 8 ACs PRD §F32.1~§F32.8 verbatim → ~88 sub-ACs (12+10+12+10+10+10+12+12 = 88 sub-ACs) satisfied pre-flight 정합 sweep 결정 wire

## Cross-References

- Phase 16 PRD entry `4f11d03` (cj-style 125번째) — FinOps Reporting & Executive Dashboard territory 정합
- Phase 15 close-out retro `102f370` (cj-style 124번째) — D-FINOPS-6 honestly DEFER 보존 해소
- Phase 15 atomic wire T1~T8 `1b800d9` (cj-style 123번째) — FinOps Tag Governance & Cost Allocation territory 정합
- Phase 15 spec entry `69c29df` (cj-style 122번째)
- Phase 15 PRD entry `87393b4` (cj-style 121번째)
- Phase 14 close-out retro `5b367d9` (cj-style 120번째)
- Phase 14 atomic wire T1~T8 `e904485` (cj-style 119번째) — FinOps Optimization & Rightsizing territory 정합
- Phase 14 spec entry `30637f6` (cj-style 118번째)
- Phase 14 PRD entry `0e3f8d9` (cj-style 117번째)
- Phase 13 close-out retro `850b4f8` (cj-style 116번째)
- Phase 13 atomic wire T1~T8 `8b98030` (cj-style 115번째) — FinOps Forecasting & Capacity Planning territory 정합
- Phase 12 close-out retro `3354e83` (cj-style 112번째)
- Phase 12 atomic wire T1~T8 `f3c0e63` (cj-style 111번째) — Cost Anomaly Detection & Budget Alerting territory 정합
- Phase 11 close-out retro `80df15b` (cj-style 108번째)
- Phase 11 atomic wire T1~T8 `e020ad0` (cj-style 107번째) — FinOps Showback / Chargeback territory 정합
- Phase 10 close-out retro `733d428` (cj-style 104번째)
- Phase 10 wire `ac5d6c5` (cj-style 103번째) — SLO Engineering / Error Budget Management territory 정합
- Phase 9 wire `e7670e1` (cj-style 99번째) — Chaos Engineering / Game Day territory 정합
- Phase 8 wire `60d4ea1` (cj-style 95번째) — cost-engine V8 골든 fixture + 12-period benchmark EXTENSION
- Phase 7 wire `59b56cd` (cj-style 91번째) — observability 정합
- Phase 5 wire `f093f8c` (cj-style 75번째) — multi-region failover + replication_lag 정합
- Epic 12 2FA 게이트 `a63646c` — Epic 12 2FA 챌린지 mandatory
- Epic 1 carry-over (auth) — onboarding/industry 보존
- AD-14 stack pin — Recharts 2.12.7 + slack-sdk==3.23.0 + pdpyras==5.2.0 + sendgrid==6.11.0 + reportlab==4.0.7 + openpyxl==3.1.2 + apscheduler==3.10.4 + pytz==2024.1
- AD-22 owner-only RBAC — executive dashboard view + executive report generation + scheduled dispatch config
- AD-43 FinOps Reporting & Executive Dashboard 신규 (a)~(g) 7 sub-decisions
- NFR18 ko-KR — SSOT only invariant
- NFR4 PII minimization — executive reporting data PII 미포함
- CR 0-2 RLS lesson, CR 1-1 audit-first INSERT, CR 4-3/4-4 lessons carry, CR 1-1 ContextVar, CR 1-1 RSC boundary, CR 9-6 commit message, CR 11-3 honest-DEFER, CR 11-4 D-001~D-005 + P-015, CR 12-1 L4 industry-agnostic capability, CR 12-5 D-14 envelope, CR 12-5 D-PARITY-01, CR 12-5 D-GATE-01, A19 cohesion 9 surface EXTENSION PASS, A36 SDR 검증 4-step 자동 적용
- m24_finops_reporting.reporting_serializers NEW Phase 16 EXTENSION 결정 wire (wire 시점에)

## 결정 wire 일자

2026-08-25 (KST)

## next (wire 진입 시)

옵션 (a) Phase 16 bmad-dev-story atomic wire T1~T8 진입 (cj-style 127번째 wire 진입 시점) 결정 wire 진입 / 옵션 (b) Phase 16 close-out retro 진입 (cj-style 128번째) / 옵션 (c) Phase 17+ 진입 / 옵션 (d) Epic 18+ 진입 / 옵션 (e) D-DEFER-* follow-up 진입 결정 wire 보류.