---
baseline_commit: 16d7698
status: ready-for-dev
cj_style_entry_point: 106
story_key: phase-11-finops-showback-chargeback-wire
---

# Phase 11 FinOps Showback / Chargeback wire spec (cj-style 106번째 epic 연속 정직 회복)

## Story

**As a** finance team / department cost center owner / tenant admin / FinOps analyst / enterprise onboarding lead / compliance officer
**I want** FinOps Showback / Chargeback territory 결정 wire (showback DSL `ShowbackDefinition` TypedDict 13 fields + period selector 6 modes + comparison view + chargeback engine 3 rule types (flat_fee / proportional_allocation / metered) + markup + tax + department cost center mapping + showback dashboard UI + chart components + CSV/PDF export + scheduled delivery + capability matrix v1.36 EXTENSION FINOPS_SHOWBACK + FINOPS_CHARGEBACK)
**so that** Phase 10 wire `ac5d6c5` SLO_ENGINEERING + Phase 9 wire `e7670e1` CHAOS_ENGINEERING + Phase 8 wire `60d4ea1` PERFORMANCE_TESTING + Phase 7 wire `59b56cd` OBSERVABILITY_TRACES + OBSERVABILITY_METRICS + Phase 6 wire `24e1cd7` AUDIT_LOG_RETENTION + Phase 5 wire `f093f8c` MULTI_REGION_BACKUP + FAILOVER + Epic 17 wire `2ada2ec` AUDIT_LOG_VIEW + Epic 7~10 ABC/TDABC territory 의 natural FinOps territory EXTENSION + Epic 12 2FA 챌린지 보존 + AD-22 owner-only RBAC 보존 + D-FINOPS-1 honestly DEFER 보존 진입 결정 wire + Phase 10 close-out retro `733d428` §10 verbatim 해소 결정 wire 보존.

## Context

cj-style Phase 11 2번째 진입점 (cj-style 106번째) 진입 결정 wire 진입 완료:
- Phase 11 PRD entry `16d7698` (cj-style 105번째) DONE 진입 정합 보존
- Phase 10 close-out retro `733d428` (cj-style 104번째) + Phase 10 atomic wire T1~T8 `ac5d6c5` (cj-style 103번째) + Phase 10 spec entry `3c80ef0` (cj-style 102번째) + Phase 10 PRD entry `09db4d4` (cj-style 101번째) + Phase 9 close-out retro `634427d` (cj-style 100번째) + Phase 9 atomic wire T1~T8 `e7670e1` (cj-style 99번째) 결정 wire 모두 DONE 진입 정합 보존
- D-FINOPS-1 honestly ✅ RESOLVED 보존 진입 결정 wire (Phase 10 close-out retro §10 verbatim 해소 + Phase 11 PRD entry 진입 시점에 1 NEW 결정 wire)
- D-SLO-1 ✅ RESOLVED 보존 진입 결정 wire
- D-CHAOS-1 ✅ RESOLVED 보존 진입 결정 wire
- D-PERFORMANCE-1 ✅ RESOLVED 보존 진입 결정 wire
- D-OBSERVABILITY-1 ✅ RESOLVED 보존 진입 결정 wire
- Phase 11 PRD entry 의 7 ACs §F27.1~§F27.7 verbatim 결정 wire 보존

## 7 ACs (PRD §F27.1~§F27.7 verbatim) → 78 detailed sub-ACs

### §F27.1 showback DSL + period selector + comparison view (12 sub-ACs)
- F27.1-1 `apps/api/modules/finops/showback_dsl.py` NEW (~+150 LOC + showback builder 함수 + 5 group_by 옵션 결정 wire (department + cost_center + product_line + service + custom_tag) + 6 period selector 모드 결정 wire (current month + previous month + last 3 months + last 6 months + YTD + custom range) + 4 industries baseline + per-tenant override EXTENSION 결정 wire)
- F27.1-2 `apps/api/modules/finops/showback_query.py` NEW (~+120 LOC + query_showback_breakdown 함수 + query_showback_comparison 함수 + DepartmentBreakdown TypedDict 8 fields + ComparisonView TypedDict 7 fields 결정 wire + CR 12-5 D-PARITY-01 verbatim 적용)
- F27.1-3 showback audit-first INSERT 결정 wire (`showback_generated` 1 NEW action + ActionClass.FINOPS + CR 1-1 verbatim 적용 + emit_audit_typed BEFORE showback generation + per-tenant RLS 자동 적용)
- F27.1-4 comparison view 결정 wire (delta_pct + delta_amount calculation + 부호 표기 + ko-KR.json `finops.*` namespace EXTENSION 결정 wire CR 11-4 D-002 verbatim SSOT)
- F27.1-5 period selector 6 모드 calendar arithmetic 결정 wire (current month = KST 이번달 1일 ~ 말일 + previous month = KST 지난달 1일 ~ 말일 + last_3_months + last_6_months + YTD + custom range + leap year / month boundary 안전 결정 wire)
- F27.1-6 group_by 5 옵션 column mapping 결정 wire (department → departments.name + cost_center → cost_centers.code + product_line → product_lines.name + service → services.name + custom_tag → tenant_settings.custom_tags JSONB + JOIN 1개 + RLS 자동 적용 CR 0-2 verbatim 결정 wire)
- F27.1-7 showback DSL pure validator CR 11-4 P-015 verbatim 결정 wire (parse_showback_definition 함수 + 6 validation rules + 1 NEW error class ShowbackDefinitionInvalidError(400) CR 12-5 D-14 envelope 결정 wire)
- F27.1-8 4 industries baseline industry-agnostic 결정 wire (manufacturing + service + manufacturing_service + manufacturing_service_other 모두 showback 가능 + per-tenant override EXTENSION + Epic 1~17 + Phase 3~10 territory 와 동일 industry-agnostic 4-industry grants ✅/✅/✅/✅ 미러 결정 wire)
- F27.1-9 query_showback_breakdown pagination 결정 wire (page_size default 20 + max 100 + offset 기반 pagination + tenant_id RLS 자동 적용 + Page[DepartmentBreakdown] 결정 wire + total_count 포함)
- F27.1-10 showback cache layer 결정 wire (Redis cache 5분 TTL + cache key = (tenant_id, period_key, group_by, query_hash) + cache invalidation 시점: AD-25 의 LISTEN/NOTIFY `cost_engine_cache` channel EXTENSION 결정 wire + NFR4 PII minimization 정합 보존)
- F27.1-11 showback currency 결정 wire (KRW 기본 + tenant 의 currency_code per-tenant EXTENSION 결정 wire + tenant_settings.currency_code column + ISO 4217 currency code 결정 + currency formatting 결정 (1,234,567 KRW / 1,234,567.89 USD 등))
- F27.1-12 showback export format 결정 wire (export_showback_csv StreamingResponse 결정 wire + Excel-compatible UTF-8 BOM + comma-separated + double-quote escape + audit-first INSERT `showback_exported` CR 1-1 verbatim + 1 NEW error class ShowbackExportError(500) CR 12-5 D-14 envelope 결정 wire)

### §F27.2 chargeback cost allocation engine (12 sub-ACs)
- F27.2-1 `apps/api/modules/finops/chargeback_engine.py` NEW (~+180 LOC + ChargebackRule TypedDict 6 fields + compute_chargeback 함수 결정 wire + CR 12-5 D-PARITY-01 verbatim + CR 12-5 D-14 envelope)
- F27.2-2 chargeback rule 3종 결정 wire (정액제 flat_fee + 비례배분 proportional_allocation + 사용량 기반 metered + tiered pricing 결정 wire + Tier 1/2/3 결정)
- F27.2-3 `apps/api/modules/finops/chargeback_rule_evaluator.py` NEW (~+100 LOC + evaluate_chargeback_rule 함수 + 1 NEW error class ChargebackRuleInvalidError(400) + 1 NEW error class ChargebackCalculationError(500) CR 12-5 D-14 envelope + 4 validation rules 결정 wire)
- F27.2-4 markup + tax 결정 wire (markup_pct default 0% + max 50% range 0~50% + 0.01 step granularity + tax_pct default 10% VAT + per-tenant override EXTENSION + tenant_settings.tax_pct column 결정 wire)
- F27.2-5 cost_allocation_method enum direct/indirect/shared 결정 wire (direct = department 직접 귀속 + indirect = 공통 비용 department 비례 배부 + shared = multiple department 공유 + usage 비례 분배 + 3 method default weight 결정 wire)
- F27.2-6 ChargebackResult TypedDict 결정 wire (10 fields + Decimal precision 결정 + banker's rounding 적용 CR 5-1 verbatim + per-tenant currency_code 적용 결정 wire)
- F27.2-7 chargeback monthly reset KST 1일 00:00 결정 wire (cron KST 매월 1일 00:00 UTC 15:00 + chargeback_period_monthly cron 자동 트리거 + Phase 10 wire `ac5d6c5` monthly reset KST 1일 00:00 + 30d rolling calculation 정합 보존 + audit-first INSERT `chargeback_calculated` CR 1-1 verbatim 결정 wire)
- F27.2-8 chargeback per-tenant override EXTENSION 결정 wire (tenant_settings.chargeback_overrides JSONB TypedDict + policy evaluation precedence tenant override > industry baseline > system default 결정 wire + Phase 10 wire `ac5d6c5` tenant_settings.slo_overrides JSONB pattern verbatim 미러)
- F27.2-9 chargeback multi-region aggregation 결정 wire (Phase 5 wire `f093f8c` phase_5_replication_lag table 정합 + primary Seoul + secondary Tokyo replica EXTENSION + cross-region cost variance detection EXTENSION + region_weight_map default `{seoul: 0.6, tokyo: 0.3, singapore: 0.1}` 결정 wire + audit-first INSERT `chargeback_calculated_multi_region` CR 1-1 verbatim)
- F27.2-10 chargeback dry-run mode 결정 wire (`--finops-chargeback-dry-run` CLI flag + compute_chargeback dry-run parameter + dry-run 시 actual chargeback_calculated INSERT skip + chargeback_preview 테이블 alembic 0043 신규 + audit-first INSERT `chargeback_dry_run_executed` CR 1-1 verbatim 결정 wire)
- F27.2-11 chargeback validation error envelope 결정 wire (CR 12-5 D-14 verbatim + ChargebackRuleInvalidError(400) message_ko + ChargebackCalculationError(500) message_ko + ko-KR.json `finops.*` EXTENSION 결정 wire CR 11-4 D-002 verbatim SSOT)
- F27.2-12 chargeback audit log + tenant isolation 결정 wire (CR 1-1 verbatim + CR 0-2 RLS lesson 적용 + 4 NEW audit log entries: chargeback_calculated + chargeback_dry_run_executed + chargeback_rule_updated + chargeback_override_applied + action_class='FINOPS' + multi-tenant isolation test 결정 wire + Phase 6 wire `24e1cd7` audit-first INSERT pattern verbatim 미러)

### §F27.3 department cost center mapping (10 sub-ACs)
- F27.3-1 `apps/api/modules/finops/department_mapping.py` NEW (~+120 LOC + tenant_settings.cost_center_mapping JSONB TypedDict + cost_center_id pattern 결정 wire `CC-{4-digit-number}` format + UNIQUE constraint `UNIQUE (tenant_id, department_id)` + RLS policy `tenant_id = current_setting('app.tenant_id')::uuid` CR 0-2 verbatim 결정 wire)
- F27.3-2 department_id ↔ cost_center_id 1:1 mapping 결정 wire (한 department 는 하나의 cost_center 에만 매핑 + 한 cost_center 는 여러 department 매핑 가능 (1:N) + validate_department_mapping pure function CR 11-4 P-015 verbatim + 4 validation rules 결정 wire)
- F27.3-3 auto-create on first calculation 결정 wire (first showback 계산 시 department 가 존재하지 않으면 auto-create + default cost_center_id 자동 생성 (CC-{4-digit-random}) + audit-first INSERT `department_mapping_updated` CR 1-1 verbatim + actor_id='system' 결정 wire)
- F27.3-4 department_mapping audit-first INSERT 결정 wire (`department_mapping_updated` 1 NEW action + ActionClass.FINOPS + CR 1-1 verbatim + emit_audit_typed BEFORE mapping 변경 + per-tenant RLS 자동 적용 + multi-tenant isolation test 결정 wire)
- F27.3-5 `apps/api/alembic/versions/0043_phase_11_finops.py` NEW (~+200 LOC + phase_11_finops_department_mapping table 9 columns 결정 wire + tenant_id UUID + department_id TEXT + cost_center_id TEXT NOT NULL + auto_created BOOLEAN DEFAULT FALSE + created_at TIMESTAMPTZ DEFAULT NOW() + updated_at TIMESTAMPTZ DEFAULT NOW() + created_by UUID + updated_by UUID + UNIQUE constraint `(tenant_id, department_id)` + RLS policy CR 0-2 verbatim + down_revision "0042_phase_10_slo_engineering" 결정 wire)
- F27.3-6 phase_11_finops_showback table 14 columns 결정 wire (showback_id UUID PK + tenant_id UUID + period_key TEXT NOT NULL + department_id TEXT + cost_center_id TEXT + group_by TEXT enum + total_amount NUMERIC(20, 2) + currency_code TEXT default 'KRW' + tenant_industry TEXT + industry_baseline_amount NUMERIC(20, 2) nullable + override_applied BOOLEAN DEFAULT FALSE + computed_at TIMESTAMPTZ DEFAULT NOW() + trace_id TEXT + tenant_id_period_key_department_id UNIQUE constraint 결정 wire)
- F27.3-7 phase_11_finops_chargeback table 12 columns 결정 wire (chargeback_id UUID PK + tenant_id UUID + period_key TEXT NOT NULL + department_id TEXT + rule_type TEXT enum + base_amount NUMERIC(20, 2) + markup_amount NUMERIC(20, 2) + tax_amount NUMERIC(20, 2) + total_amount NUMERIC(20, 2) + currency_code TEXT default 'KRW' + computed_at TIMESTAMPTZ DEFAULT NOW() + trace_id TEXT + UNIQUE constraint `(tenant_id, period_key, department_id, rule_type)` 결정 wire)
- F27.3-8 alembic 0043 의 4 indexes 결정 wire (idx_phase_11_finops_showback_tenant_id_period_key + idx_phase_11_finops_showback_department_id + idx_phase_11_finops_chargeback_tenant_id_period_key + idx_phase_11_finops_chargeback_rule_type + 2 CHECK constraints 결정 wire: currency_code IN ('KRW', 'USD', 'EUR', 'JPY', 'CNY') + rule_type IN ('flat_fee', 'proportional_allocation', 'metered'))
- F27.3-9 alembic 0043 의 down_revision 결정 wire (down_revision "0042_phase_10_slo_engineering" + upgrade 결정 wire: 3 tables CREATE + 4 indexes CREATE + 2 CHECK constraints CREATE + RLS policies CREATE + downgrade 결정 wire: DROP TABLE × 3 + DROP INDEX × 4 + DROP CONSTRAINT × 2 + DROP POLICY × 3)
- F27.3-10 department_mapping cache invalidation 결정 wire (Redis cache 5분 TTL + cache key = (tenant_id, department_id) + LISTEN/NOTIFY `cost_center_mapping_cache` channel 신규 + AD-25 LISTEN/NOTIFY 4-channel publisher EXTENSION 결정 wire: cost_engine_cache + fiscal_period_cache + closing_snapshot_cache + ai_cache + cost_center_mapping_cache 5-channel EXTENSION + Phase 5 wire `f093f8c` multi-region replication 정합 보존 + NFR4 PII minimization ✅ PRESERVED 결정 wire)

### §F27.4 showback dashboard UI (10 sub-ACs)
- F27.4-1 `apps/web/app/[locale]/(dashboard)/admin/finops/page.tsx` NEW (~+150 LOC + 4 components 결정 wire: ShowbackPeriodSelector + ShowbackDepartmentBreakdownChart + ShowbackComparisonView + ShowbackCSVExportButton + owner-only RBAC AD-22 verbatim + Epic 12 2FA 챌린지 보존 + (dashboard) route group 보호 Phase 3-1 T1 wire 정합 결정 wire)
- F27.4-2 ShowbackPeriodSelector 결정 wire (6 period selector 모드 UI: current_month + previous_month + last_3_months + last_6_months + YTD + custom range + radio button + date range picker + onChange handler + ko-KR.json `finops_period_label` EXTENSION + CR 11-4 D-002 verbatim SSOT + RTL render discipline 결정 wire)
- F27.4-3 ShowbackDepartmentBreakdownChart 결정 wire (Recharts BarChart + X-axis department names + Y-axis amount (currency formatted) + tooltip on hover + tenant currency_code 적용 + tooltip ko-KR 결정 + responsive design 결정 wire (mobile + tablet + desktop) + Phase 7 wire `59b56cd` Recharts Grafana dashboard EXTENSION 정합)
- F27.4-4 ShowbackComparisonView 결정 wire (2-column side-by-side layout (current_period + previous_period) + delta_pct + delta_amount 시각화 (▲ green / ▼ red / — no change) + comparison period selector 결정 (previous_month vs last_year_same_month 등 5 옵션) + RTL render discipline + ko-KR.json `finops_comparison_label` + `finops_variance_label` EXTENSION 결정 wire)
- F27.4-5 ShowbackCSVExportButton 결정 wire (클릭 시 export_showback_csv API 호출 + StreamingResponse download trigger + filename 결정: showback-{tenant_slug}-{period_key}.csv + UX 결정: loading state + success toast + error toast + audit-first INSERT `showback_exported` CR 1-1 verbatim + ko-KR.json `finops_export_label` + `finops_csv_export_label` EXTENSION 결정 wire)
- F27.4-6 owner-only RBAC AD-22 verbatim 결정 wire ((dashboard)/admin/finops/ route group 의 middleware 결정 wire = owner role required require_role("owner") FastAPI Dependency + Epic 12 2FA 챌린지 보존 결정 wire (2FA 미설정 시 /account/security?reason=2fa_required redirect 결정) + Phase 3-1 T1 wire (dashboard) route group 보호 정합)
- F27.4-7 ko-KR.json `finops.*` namespace EXTENSION 결정 wire (~25 keys CR 11-4 D-002 verbatim SSOT 결정 wire: finops_dashboard_title + finops_section_label + finops_period_label + finops_department_label + finops_cost_center_label + finops_showback_label + finops_chargeback_label + finops_group_by_label + finops_comparison_label + finops_variance_label + finops_delta_pct_label + finops_delta_amount_label + finops_markup_label + finops_tax_label + finops_export_label + finops_csv_export_label + finops_pdf_export_label + finops_dry_run_label + finops_owner_only_label + finops_chargeback_rule_flat_fee + finops_chargeback_rule_proportional + finops_chargeback_rule_metered + loading_finops + error_finops_failed + empty_state + i18n SSOT drift detector 적용 결정 wire)
- F27.4-8 `apps/web/lib/finops/finops-client.ts` NEW (~+150 LOC + ShowbackRequest + DepartmentBreakdown + ComparisonView + ChargebackRule + ChargebackExport TypedDict CR 12-5 D-PARITY-01 verbatim + fetchShowbackBreakdown + fetchShowbackComparison + exportShowbackCSV + exportChargebackPDF API wrapper functions + ChargebackApiError typed envelope `{code, message_ko, details, trace_id}` CR 12-5 D-14 envelope + audit-first INSERT BEFORE fetch CR 1-1 verbatim 적용 결정 wire)
- F27.4-9 finops dashboard period selector + comparison view 정합 결정 wire (period 변경 시 automatic refetch + cache invalidation (TanStack Query) + loading state + error boundary 적용 결정 wire + Phase 7 wire `59b56cd` grafana dashboard 의 React Query pattern verbatim 미러 + NFR18 ko-KR 정합 결정 wire)
- F27.4-10 finops dashboard accessibility 결정 wire (WCAG 2.1 AA compliance Epic 12 의 2FA �린지 UI 와 동일 표준 + ARIA labels 결정 wire ko-KR inline + i18n SSOT + keyboard navigation 결정 wire: Tab + Enter + Arrow keys + screen reader 지원 + Phase 12 Epic 1 UX v1.0 locked decision 결정 wire Dark MVP / WCAG AA / Professional / ko-KR verbatim 보존)

### §F27.5 chargeback CSV/PDF export (10 sub-ACs)
- F27.5-1 `apps/api/modules/finops/chargeback_export.py` NEW (~+150 LOC + export_chargeback_csv StreamingResponse 결정 wire + Excel-compatible UTF-8 BOM + comma-separated + double-quote escape for amount_json + filename 결정: chargeback-{tenant_slug}-{period_key}.csv + streaming response Phase 7 wire `59b56cd` audit_log_export.py StreamingResponse pattern verbatim 미러 + 1 NEW error class ChargebackExportError(500) CR 12-5 D-14 envelope 결정 wire)
- F27.5-2 CSV columns 결정 wire (13 columns: chargeback_id + tenant_slug + period_key + department_id + cost_center_id + rule_type + base_amount + markup_amount + tax_amount + total_amount + currency_code + computed_at ISO 8601 + trace_id + header row + UTF-8 BOM Excel 호환 결정 wire)
- F27.5-3 export_chargeback_pdf bytes 결정 wire (reportlab 기반 PDF generation 결정 wire + company logo Phase 1 wire branding assets 정합 + department breakdown 차트 PDF 임베드 (Recharts → matplotlib → PDF 변환 또는 reportlab.graphics 결정) + page layout 결정: title + period + tenant_slug + table + footer + page numbers + reportlab AD-14 stack pin 결정 wire reportlab==4.0.7)
- F27.5-4 PDF generation 결정 wire (SimpleDocTemplate + Table + Paragraph 3 components + font 결정: 한글 �트 NOTO Sans CJK KR 결정 wire + noto-sans-cjk-kr AD-14 stack pin + page size A4 + orientation landscape department breakdown wide table + filename chargeback-{tenant_slug}-{period_key}.pdf 결정 wire)
- F27.5-5 streaming response 결정 wire (StreamingResponse 의 generator 함수 + 대용량 chargeback 데이터 memory-efficient streaming + Content-Disposition: attachment header + Content-Type: text/csv; charset=utf-8 또는 application/pdf + Cache-Control: no-store 민감 데이터 cache 방지 + NFR4 PII minimization 정합 결정 wire)
- F27.5-6 audit-first INSERT `chargeback_exported` 결정 wire (CR 1-1 verbatim + action_class='FINOPS' + action='chargeback_exported' + actor_id + tenant_id + period_key + export_format enum csv/pdf + row_count + file_size_bytes + trace_id + per-tenant RLS 자동 적용 + Phase 6 wire `24e1cd7` 5 NEW audit log entries pattern verbatim 미러 결정 wire)
- F27.5-7 export permission check 결정 wire (owner-only RBAC AD-22 verbatim + require_role("owner") FastAPI Dependency + Epic 12 2FA 챌린지 보존 + Epic 12 M12-a 2FA 미설정 시 /account/security?reason=2fa_required redirect + 미허용 tenant 의 export 차단 capability gate FINOPS_CHARGEBACK + FINOPS_SHOWBACK 자동 적용 결정 wire)
- F27.5-8 export rate limit 결정 wire (Phase 10 wire `ac5d6c5` SLO breach rate limit EXTENSION pattern verbatim 미러 + owner 1 export / minute default + rate limit 초과 시 429 status + Retry-After header + 1 NEW error class ChargebackExportRateLimitedError(429) CR 12-5 D-14 envelope + audit-first INSERT `chargeback_export_rate_limited` CR 1-1 verbatim 결정 wire)
- F27.5-9 export error handling 결정 wire (CR 12-5 D-14 verbatim + ChargebackRuleInvalidError(400) message_ko + ChargebackCalculationError(500) message_ko + ChargebackExportError(500) message_ko + ko-KR.json `finops.*` EXTENSION CR 11-4 D-002 verbatim SSOT: error_finops_failed + finops_export_label 결정 wire)
- F27.5-10 export cache 결정 wire (Redis cache 결정 wire CSV/PDF 의 byte stream cache 5분 TTL + cache key = (tenant_id, period_key, export_format, query_hash) + cache invalidation 시점: AD-25 LISTEN/NOTIFY `cost_engine_cache` channel EXTENSION + NFR4 PII minimization 정합 보존 + 동시 export 요청 시 cache hit 으로 backend load 감소 결정 wire)

### §F27.6 capability matrix v1.36 EXTENSION FINOPS_SHOWBACK + FINOPS_CHARGEBACK (12 sub-ACs)
- F27.6-1 Capability matrix v1.35 → v1.36 EXTENSION 결정 wire (2 NEW rows FINOPS_SHOWBACK + FINOPS_CHARGEBACK industry-agnostic 4-industry grants ✅/✅/✅/✅ CR 12-1 L4 precedent 미러)
- F27.6-2 `apps/api/core/capability.py` MODIFIED (Capability.FINOPS_SHOWBACK = "finops_showback" + Capability.FINOPS_CHARGEBACK = "finops_chargeback" 2 NEW enum + 4 `_INDUSTRY_CAPABILITIES` blocks EXTENSION industry-agnostic ✅/✅/✅/✅ 결정 wire)
- F27.6-3 `apps/api/dependencies/capability.py` MODIFIED (require_finops_showback + require_finops_chargeback 2 NEW dep + __all__ EXTENSION 결정 wire)
- F27.6-4 `docs/capability-matrix.md` MODIFIED (capability matrix v1.35 → v1.36 EXTENSION + 2 NEW rows FINOPS_SHOWBACK + FINOPS_CHARGEBACK industry-agnostic 4-industry grants ✅/✅/✅/✅ 결정 wire + m18_slo_engineering 의 section EXTENSION 결정 wire: FINOPS section 신규 추가)
- F27.6-5 `tests/integration/test_capability_matrix_v1_36_drift.py` NEW 10 NEW pytest cases 결정 wire (capability matrix v1.36 의 FINOPS_SHOWBACK + FINOPS_CHARGEBACK row 존재 검증 + 4-industry grants 검증 + Capability enum 값 검증 + require_finops_showback + require_finops_chargeback dependency 동작 검증 + 미허용 tenant 진입 차단 검증 + Phase 10 wire `tests/integration/test_capability_matrix_v1_35_drift.py` 패턴 verbatim 미러)
- F27.6-6 미허용 tenant 의 FinOps 진입 차단 결정 wire (require_finops_showback + require_finops_chargeback dependency 의 미허용 tenant 진입 차단 검증 + 403 Forbidden + FORBIDDEN_KO message 결정 wire ("FinOps capability 미허용 tenant") + Epic 12 2FA 챌린지 보존 + AD-22 owner-only RBAC 정합)
- F27.6-7 m18_slo_engineering + m19_finops 결정 wire (apps/api/modules/finops/__init__.py NEW 결정 wire + apps/api/modules/finops/serializers.py NEW 결정 wire m18_slo_engineering.slo_engineering_serializers Phase 10 wire EXTENSION pattern verbatim 미러 + module version 결정 wire m19_finops 결정 wire)
- F27.6-8 SSOT RED→GREEN EXTENSION 결정 wire (capability matrix v1.36 신규 2 rows + capability.py EXTENSION 2 NEW enum + require_finops_showback + require_finops_chargeback 2 NEW deps 결정 wire + drift detector + A36 SDR 검증 4-step 자동 적용 결정 wire + CR 12-5 D-GATE-01 inversion 적용 보존)
- F27.6-9 CR 12-1 L4 industry-agnostic capability 결정 wire (FINOPS_SHOWBACK + FINOPS_CHARGEBACK 모두 industry-agnostic 4-industry grants ✅/✅/✅/✅ 결정 wire manufacturing + service + manufacturing_service + manufacturing_service_other 모두 허용 + Phase 10 wire SLO_ENGINEERING industry-agnostic 4-industry grants pattern verbatim 미러)
- F27.6-10 capability gate fail-closed 결정 wire (미허용 tenant 의 FinOps 진입 시 403 Forbidden + capability matrix v1.36 row 부재 시 fail-closed + Capability.FINOPS_SHOWBACK + Capability.FINOPS_CHARGEBACK enum 부재 시 fail-closed + AD-22 owner-only RBAC 정합 + Epic 12 2FA 챌린지 보존 + NFR4 PII minimization 정합 보존 결정 wire)
- F27.6-11 Phase 11 wire scope T1~T8 결정 wire (T1 showback_dsl + showback_query + T2 chargeback_engine + chargeback_rule_evaluator + T3 department_mapping + tenant_settings JSONB schema + T4 chargeback CSV/PDF export + T5 alembic 0043 + T6 audit action EXTENSION 3 NEW + T7 capability v1.36 + frontend finops dashboard + T8 atomic commit 결정 wire)
- F27.6-12 Phase 11 wire SLI integration 결정 wire (Phase 10 wire `ac5d6c5` 의 4 SLIs 자연스러운 EXTENSION 결정 wire + cost_engine p99 < 5s + signups success_rate > 99% + logins p99 < 1s + audit log purge success_rate > 99.9% + Phase 9 wire `e7670e1` chaos_experiment baseline + Phase 8 wire `60d4ea1` cost-engine V8 골든 fixture + Phase 7 wire `59b56cd` Prometheus custom metrics 자연스러운 EXTENSION 결정 wire)

### §F27.7 dry-run + Tests + wire scope T1~T8 (12 sub-ACs)
- F27.7-1 Phase 11 wire scope T1~T8 결정 wire (T1 showback_dsl + showback_query module + T2 chargeback_engine + chargeback_rule_evaluator + T3 department_mapping + tenant_settings JSONB schema + T4 chargeback CSV/PDF export + T5 alembic 0043 phase_11_finops + T6 audit action EXTENSION 3 NEW + T7 capability v1.36 + frontend finops dashboard + T8 atomic commit 결정 wire)
- F27.7-2 Phase 11 wire estimated files ~18 NEW + ~12 MODIFIED = ~30 files atomic single sprint 결정 wire
- F27.7-3 Phase 11 wire backend tests 결정 wire (~46 NEW pytest PASS 결정 wire: showback_dsl 6 + chargeback_engine 7 + department_mapping 5 + chargeback_export 6 + alembic 0043 4 + audit action 8 + capability matrix v1.36 10 = ~46 NEW pytest PASS)
- F27.7-4 Phase 11 wire frontend tests 결정 wire (~5 NEW vitest PASS 결정 wire: ShowbackPeriodSelector + ShowbackDepartmentBreakdownChart owner-only ack prompt AD-22 verbatim + ShowbackComparisonView RTL render + ko-KR SSOT 2 + finops dashboard parity CR 12-5 D-PARITY-01 = ~5 NEW vitest PASS)
- F27.7-5 Phase 11 wire 0 NEW ruff 결정 wire (apps/api backend 결정 wire + 기존 ruff scoped 0 NEW 정합 보존)
- F27.7-6 Phase 11 wire 0 NEW tsc 결정 wire (apps/web frontend 결정 wire + 기존 tsc 0 NEW 정합 보존)
- F27.7-7 Phase 11 wire 0 regressions 결정 wire (3중 게이트 FINAL CLEAN + ruff scoped 0 NEW + pytest 0 NEW failures + vitest 0 NEW failures + tsc 0 NEW errors)
- F27.7-8 Phase 11 wire dry-run mode 결정 wire (--finops-dry-run CLI flag + showback DSL dry-run parameter + chargeback engine dry-run parameter + CSV/PDF export dry-run parameter + dry-run 시 actual chargeback_calculated INSERT skip + dry-run 시 actual CSV/PDF export skip + dry-run 시 actual department_mapping_updated INSERT skip + dry-run 결과 preview chargeback_preview 테이블 alembic 0043 신규)
- F27.7-9 Phase 11 wire audit-first INSERT 결정 wire (3 NEW audit log entries 결정 wire: showback_generated + department_mapping_updated + chargeback_exported + ActionClass.FINOPS 신규 정의)
- F27.7-10 Phase 11 wire capability gate FINOPS_SHOWBACK + FINOPS_CHARGEBACK 결정 wire (capability matrix v1.35 → v1.36 EXTENSION 2 NEW row industry-agnostic 4-industry grants ✅/✅/✅/✅ + drift detector `tests/integration/test_capability_matrix_v1_36_drift.py` NEW 10 NEW pytest cases 결정 wire)
- F27.7-11 Phase 11 wire atomic commit via `git commit -F <file>` 결정 wire (CR 9-6 D5 prevention + PowerShell here-string 회피 결정 wire)
- F27.7-12 Phase 11 wire scope T1~T8 정합 sweep 결정 wire (Epic 1 ~ Epic 17 + Phase 3 ~ Phase 10 + 1st release cycle 정합 보존 + 결정 회피 0건 보장 + CR lessons applied 14종 + D-DEFER-* tracking 결정 wire)

## 8 tasks (T1~T8) + 68 subtasks

### T1: showback_dsl + showback_query module (13 subtasks)
- T1.1: `apps/api/modules/finops/` NEW 디렉토리 + finops modules SSOT 디렉토리 결정 wire
- T1.2: `apps/api/modules/finops/showback_dsl.py` NEW (~+150 LOC + showback builder 함수 + 5 group_by 옵션 + 6 period selector 모드 + 4 industries baseline + per-tenant override EXTENSION + SHOWBACK_PERIOD_DEFAULTS constants 결정 wire)
- T1.3: `apps/api/modules/finops/showback_query.py` NEW (~+120 LOC + query_showback_breakdown 함수 + query_showback_comparison 함수 + DepartmentBreakdown TypedDict 8 fields + ComparisonView TypedDict 7 fields 결정 wire CR 12-5 D-PARITY-01 verbatim)
- T1.4: showback pure validator CR 11-4 P-015 verbatim 적용 결정 wire (parse_showback_definition 함수 + 6 validation rules + ShowbackDefinitionInvalidError(400) CR 12-5 D-14 envelope)
- T1.5: showback period selector 6 모드 calendar arithmetic 결정 wire (KST 이번달/지난달/최근 3개월/최근 6개월/YTD/custom range + leap year/month boundary 안전)
- T1.6: showback audit-first INSERT 결정 wire (`showback_generated` 1 NEW action + ActionClass.FINOPS + CR 1-1 verbatim)
- T1.7: showback owner-only RBAC 결정 wire (showback generation 모두 owner-only AD-22 + Epic 12 2FA 챌린지 + governance_required=True mandatory)
- T1.8: showback dry-run mode default 결정 wire (dry_run=True flag + audit-first INSERT `showback_dryrun` + no actual showback generation)
- T1.9: showback_query CR 0-2 RLS verbatim 적용 결정 wire + tenant_id selector + cross-tenant isolation 검증 결정 wire
- T1.10: showback cache layer 결정 wire (Redis cache 5분 TTL + cache key = (tenant_id, period_key, group_by, query_hash) + LISTEN/NOTIFY `cost_engine_cache` channel EXTENSION)
- T1.11: showback currency formatting 결정 wire (KRW 기본 + tenant currency_code per-tenant EXTENSION + ISO 4217 currency code + 1,234,567 KRW / 1,234,567.89 USD format)
- T1.12: showback export format 결정 wire (export_showback_csv StreamingResponse + UTF-8 BOM + comma-separated + double-quote escape + audit-first INSERT `showback_exported` + ShowbackExportError(500) CR 12-5 D-14 envelope)
- T1.13: showback_dsl + showback_query 6 NEW pytest cases 결정 wire (TypedDict validation + 6 period selector 모드 + 5 group_by 옵션 + comparison view delta_pct/delta_amount + audit-first INSERT + owner-only RBAC + dry_run default)

### T2: chargeback_engine + chargeback_rule_evaluator module (10 subtasks)
- T2.1: `apps/api/modules/finops/chargeback_engine.py` NEW (~+180 LOC + ChargebackRule TypedDict 6 fields + compute_chargeback 함수 + CR 12-5 D-PARITY-01 verbatim + CR 12-5 D-14 envelope)
- T2.2: chargeback rule 3종 결정 wire (정액제 flat_fee + 비례배분 proportional_allocation + 사용량 기반 metered + tiered pricing Tier 1/2/3)
- T2.3: `apps/api/modules/finops/chargeback_rule_evaluator.py` NEW (~+100 LOC + evaluate_chargeback_rule 함수 + ChargebackRuleInvalidError(400) + ChargebackCalculationError(500) CR 12-5 D-14 envelope + 4 validation rules)
- T2.4: chargeback markup + tax 결정 wire (markup_pct 0~50% + tax_pct 0~100% + per-tenant override EXTENSION + tenant_settings.tax_pct column + Decimal precision + banker's rounding CR 5-1 verbatim)
- T2.5: chargeback cost_allocation_method enum 결정 wire (direct 1.0 + indirect 0.5 + shared 0.0 baseline + Phase 7 wire `59b56cd` 7 NEW business metrics 자연스러운 carry-over chain)
- T2.6: ChargebackResult TypedDict 10 fields 결정 wire (chargeback_id + tenant_id + period_key + department_id + cost_center_id + rule_type + base_amount + markup_amount + tax_amount + total_amount + trace_id + Decimal precision + banker's rounding)
- T2.7: chargeback monthly reset KST 1일 00:00 결정 wire (cron KST 매월 1일 00:00 UTC 15:00 + chargeback_period_monthly cron 자동 트리거 + Phase 10 wire `ac5d6c5` monthly reset 정합 + audit-first INSERT `chargeback_calculated` CR 1-1 verbatim)
- T2.8: chargeback per-tenant override EXTENSION 결정 wire (tenant_settings.chargeback_overrides JSONB TypedDict + policy evaluation precedence tenant override > industry baseline > system default)
- T2.9: chargeback multi-region aggregation 결정 wire (Phase 5 wire `f093f8c` phase_5_replication_lag table 정합 + primary Seoul + secondary Tokyo replica EXTENSION + region_weight_map default `{seoul: 0.6, tokyo: 0.3, singapore: 0.1}` + audit-first INSERT `chargeback_calculated_multi_region` CR 1-1 verbatim)
- T2.10: chargeback dry-run mode 결정 wire (`--finops-chargeback-dry-run` CLI flag + dry-run parameter + dry-run 시 actual chargeback_calculated INSERT skip + chargeback_preview 테이블 alembic 0043 신규 + audit-first INSERT `chargeback_dry_run_executed` + 7 NEW pytest cases)

### T3: department_mapping + tenant_settings JSONB schema (8 subtasks)
- T3.1: `apps/api/modules/finops/department_mapping.py` NEW (~+120 LOC + tenant_settings.cost_center_mapping JSONB TypedDict + cost_center_id pattern `CC-{4-digit-number}` format + UNIQUE constraint + RLS policy CR 0-2 verbatim)
- T3.2: department_id ↔ cost_center_id 1:1 mapping 결정 wire (한 department 는 하나의 cost_center 에만 매핑 + 한 cost_center 는 여러 department 매핑 가능 1:N + validate_department_mapping pure function CR 11-4 P-015 verbatim + 4 validation rules)
- T3.3: department_mapping auto-create on first calculation 결정 wire (first showback 계산 시 department 가 존재하지 않으면 auto-create + default cost_center_id 자동 생성 CC-{4-digit-random} + audit-first INSERT `department_mapping_updated` CR 1-1 verbatim + actor_id='system')
- T3.4: department_mapping audit-first INSERT 결정 wire (`department_mapping_updated` 1 NEW action + ActionClass.FINOPS + CR 1-1 verbatim + emit_audit_typed BEFORE mapping 변경 + per-tenant RLS 자동 적용 + multi-tenant isolation test)
- T3.5: `apps/api/alembic/versions/0043_phase_11_finops.py` NEW (~+200 LOC + phase_11_finops_department_mapping table 9 columns 결정 wire + UNIQUE constraint + RLS policy + down_revision "0042_phase_10_slo_engineering")
- T3.6: phase_11_finops_showback table 14 columns 결정 wire (showback_id UUID PK + tenant_id UUID + period_key TEXT NOT NULL + department_id TEXT + cost_center_id TEXT + group_by TEXT enum + total_amount NUMERIC(20, 2) + currency_code TEXT default 'KRW' + tenant_industry TEXT + industry_baseline_amount NUMERIC(20, 2) nullable + override_applied BOOLEAN DEFAULT FALSE + computed_at TIMESTAMPTZ DEFAULT NOW() + trace_id TEXT + UNIQUE constraint)
- T3.7: phase_11_finops_chargeback table 12 columns 결정 wire (chargeback_id UUID PK + tenant_id UUID + period_key TEXT NOT NULL + department_id TEXT + rule_type TEXT enum + base_amount NUMERIC(20, 2) + markup_amount NUMERIC(20, 2) + tax_amount NUMERIC(20, 2) + total_amount NUMERIC(20, 2) + currency_code TEXT default 'KRW' + computed_at TIMESTAMPTZ DEFAULT NOW() + trace_id TEXT + UNIQUE constraint `(tenant_id, period_key, department_id, rule_type)`)
- T3.8: department_mapping cache invalidation 결정 wire (Redis cache 5분 TTL + cache key = (tenant_id, department_id) + LISTEN/NOTIFY `cost_center_mapping_cache` channel 신규 + AD-25 LISTEN/NOTIFY 5-channel publisher EXTENSION + Phase 5 wire `f093f8c` multi-region replication 정합 보존 + NFR4 PII minimization ✅ PRESERVED + 5 NEW pytest cases)

### T4: chargeback CSV/PDF export (8 subtasks)
- T4.1: `apps/api/modules/finops/chargeback_export.py` NEW (~+150 LOC + export_chargeback_csv StreamingResponse + UTF-8 BOM + comma-separated + double-quote escape + filename 결정 + 1 NEW error class ChargebackExportError(500) CR 12-5 D-14 envelope)
- T4.2: CSV columns 13 columns 결정 wire (chargeback_id + tenant_slug + period_key + department_id + cost_center_id + rule_type + base_amount + markup_amount + tax_amount + total_amount + currency_code + computed_at ISO 8601 + trace_id + header row + UTF-8 BOM Excel 호환)
- T4.3: export_chargeback_pdf bytes 결정 wire (reportlab 기반 PDF generation + company logo Phase 1 wire branding assets 정합 + department breakdown 차트 PDF 임베드 + page layout + reportlab AD-14 stack pin 결정 wire reportlab==4.0.7)
- T4.4: PDF generation 결정 wire (SimpleDocTemplate + Table + Paragraph 3 components + 한글 폰트 NOTO Sans CJK KR 결정 wire + noto-sans-cjk-kr AD-14 stack pin + page size A4 + orientation landscape + filename chargeback-{tenant_slug}-{period_key}.pdf)
- T4.5: streaming response 결정 wire (StreamingResponse 의 generator 함수 + 대용량 chargeback 데이터 memory-efficient streaming + Content-Disposition + Content-Type + Cache-Control: no-store + NFR4 PII minimization 정합)
- T4.6: chargeback audit-first INSERT `chargeback_exported` 결정 wire (CR 1-1 verbatim + action_class='FINOPS' + action='chargeback_exported' + actor_id + tenant_id + period_key + export_format enum csv/pdf + row_count + file_size_bytes + trace_id + per-tenant RLS 자동 적용)
- T4.7: export permission check 결정 wire (owner-only RBAC AD-22 verbatim + require_role("owner") FastAPI Dependency + Epic 12 2FA 챌린지 보존 + Epic 12 M12-a 2FA 미설정 시 redirect + capability gate FINOPS_CHARGEBACK + FINOPS_SHOWBACK 자동 적용)
- T4.8: export rate limit 결정 wire (owner 1 export / minute default + rate limit 초과 시 429 + Retry-After header + ChargebackExportRateLimitedError(429) CR 12-5 D-14 envelope + audit-first INSERT `chargeback_export_rate_limited` CR 1-1 verbatim + 6 NEW pytest cases)

### T5: alembic 0043 phase_11_finops (8 subtasks)
- T5.1: `apps/api/alembic/versions/0043_phase_11_finops.py` NEW (~+200 LOC + 3 tables CREATE + 4 indexes CREATE + 2 CHECK constraints CREATE + 3 RLS policies CREATE 결정 wire)
- T5.2: phase_11_finops_department_mapping table 9 columns 결정 wire (id UUID PK + tenant_id UUID + department_id TEXT + cost_center_id TEXT NOT NULL + auto_created BOOLEAN DEFAULT FALSE + created_at TIMESTAMPTZ DEFAULT NOW() + updated_at TIMESTAMPTZ DEFAULT NOW() + created_by UUID + updated_by UUID + UNIQUE constraint `(tenant_id, department_id)`)
- T5.3: phase_11_finops_showback table 14 columns 결정 wire (showback_id UUID PK + tenant_id UUID + period_key TEXT NOT NULL + department_id TEXT + cost_center_id TEXT + group_by TEXT enum + total_amount NUMERIC(20, 2) + currency_code TEXT default 'KRW' + tenant_industry TEXT + industry_baseline_amount NUMERIC(20, 2) nullable + override_applied BOOLEAN DEFAULT FALSE + computed_at TIMESTAMPTZ DEFAULT NOW() + trace_id TEXT + UNIQUE constraint)
- T5.4: phase_11_finops_chargeback table 12 columns 결정 wire (chargeback_id UUID PK + tenant_id UUID + period_key TEXT NOT NULL + department_id TEXT + rule_type TEXT enum + base_amount NUMERIC(20, 2) + markup_amount NUMERIC(20, 2) + tax_amount NUMERIC(20, 2) + total_amount NUMERIC(20, 2) + currency_code TEXT default 'KRW' + computed_at TIMESTAMPTZ DEFAULT NOW() + trace_id TEXT + UNIQUE constraint `(tenant_id, period_key, department_id, rule_type)`)
- T5.5: 4 indexes 결정 wire (idx_phase_11_finops_showback_tenant_id_period_key + idx_phase_11_finops_showback_department_id + idx_phase_11_finops_chargeback_tenant_id_period_key + idx_phase_11_finops_chargeback_rule_type)
- T5.6: 2 CHECK constraints 결정 wire (currency_code IN ('KRW', 'USD', 'EUR', 'JPY', 'CNY') + rule_type IN ('flat_fee', 'proportional_allocation', 'metered'))
- T5.7: 3 tables RLS policies 결정 wire (CR 0-2 verbatim + tenant_id = current_setting('app.tenant_id')::uuid + Phase 10 wire 정합 + Phase 5 wire phase_5_replication_lag table 정합 + Phase 9 wire phase_9_chaos_experiments table 정합)
- T5.8: alembic migration 4 NEW pytest cases 결정 wire + `tests/integration/test_finops_tenant_isolation.py` NEW multi-tenant isolation test 결정 wire (Phase 5/7/9 wire pattern verbatim + L2 single_tenant override 가 다른 tenant 에 영향 없음 검증)

### T6: audit action EXTENSION 3 NEW (9 subtasks)
- T6.1: `apps/api/core/audit_action.py` MODIFIED (ActionClass.FINOPS 신규 정의 + FinopsAction Literal 3 NEW values + _ActionRegistry FINOPS entry 신규 3개 등록 + __all__ EXTENSION + AuditAction Union EXTENSION 결정 wire)
- T6.2: ActionClass.FINOPS = 'finops' 신규 정의 결정 wire (CR 12-1 L4 precedent 미러 SLO_ENGINEERING + CHAOS_ENGINEERING + PERFORMANCE_TESTING + OBSERVABILITY_TRACES + OBSERVABILITY_METRICS + AUDIT_LOG_RETENTION + AUDIT_LOG_VIEW + MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER + TENANT_IDP_MANAGEMENT + SSO_ENTERPRISE + LISTEN_NOTIFY + AUTH_MIDDLEWARE + LAUNCH_* + DEPLOYMENT_* pattern verbatim bind)
- T6.3: FinopsAction Literal 3 NEW values 결정 wire = `showback_generated` + `department_mapping_updated` + `chargeback_exported` (CR 1-1 verbatim 적용 + payload structure 정의)
- T6.4: _ActionRegistry FINOPS entry 신규 3개 등록 결정 wire (resource_table "phase_11_finops_*" + action_class=FINOPS + 3 NEW actions acceptance + reject 결정 wire)
- T6.5: AuditAction Union EXTENSION 결정 wire (apps/api/core/audit_action.py MODIFIED + FinopsAction Union 추가 + type alias update 결정 wire)
- T6.6: emit_audit_typed BEFORE/AFTER FinOps event CR 1-1 verbatim 적용 결정 wire (showback_generated 의 audit_first INSERT 가 showback generation 직전에 실행 + department_mapping_updated AFTER mapping 변경 + chargeback_exported AFTER CSV/PDF export + trace_id propagation + actor_id capture + tenant_id capture)
- T6.7: multi-tenant isolation 결정 wire (3 NEW action 의 tenant_id 가 RLS 와 정합 + cross-tenant audit log leak 방지 결정 wire)
- T6.8: AuditAction Literal EXTENSION 검증 결정 wire (apps/api/main.py EXTENSION + finops endpoints 의 audit_first INSERT 호출 + typed exception envelope CR 12-5 D-14 적용)
- T6.9: 8 NEW pytest cases 결정 wire (AuditAction Literal 값 검증 + ActionClass.FINOPS enum value + resource_table + emit_audit_typed BEFORE/AFTER FinOps event CR 1-1 verbatim 적용 + multi-tenant isolation + trace_id propagation + typed exception envelope + dry-run default)

### T7: capability v1.36 EXTENSION + frontend finops dashboard (8 subtasks)
- T7.1: `apps/api/core/capability.py` MODIFIED (Capability.FINOPS_SHOWBACK + Capability.FINOPS_CHARGEBACK 2 NEW enum + 4 `_INDUSTRY_CAPABILITIES` blocks EXTENSION industry-agnostic ✅/✅/✅/✅ CR 12-1 L4 precedent 미러)
- T7.2: `apps/api/dependencies/capability.py` MODIFIED (require_finops_showback + require_finops_chargeback 2 NEW dep + __all__ EXTENSION 결정 wire)
- T7.3: capability matrix v1.35 → v1.36 EXTENSION title update + v1.36 changelog entry prepend + 2 NEW rows FINOPS_SHOWBACK + FINOPS_CHARGEBACK industry-agnostic 4-industry grants ✅/✅/✅/✅ 결정 wire
- T7.4: `tests/integration/test_capability_matrix_v1_36_drift.py` NEW 10 NEW pytest cases 결정 wire (Capability.FINOPS_SHOWBACK + Capability.FINOPS_CHARGEBACK enum + 4 industries grants + v1.35 + v1.34 + v1.33 + v1.32 + v1.31 preservation + Phase 5 v1.29 + Epic 16 v1.28 + Epic 17 v1.30 + Phase 6 v1.31 + Phase 7 v1.32 + Phase 8 v1.33 + Phase 9 v1.34 + Phase 10 v1.35 pattern verbatim)
- T7.5: `docs/capability-matrix.md` MODIFIED v1.35 → v1.36 EXTENSION 결정 wire (2 NEW rows FINOPS_SHOWBACK + FINOPS_CHARGEBACK industry-agnostic 4-industry grants + FINOPS section 신규 추가)
- T7.6: 미허용 tenant 의 FinOps 진입 차단 결정 wire (require_finops_showback + require_finops_chargeback dep + capability gate per-tenant on/off)
- T7.7: FinOps capability gate 적용 대상 명시 결정 wire (require_finops_showback + require_finops_chargeback → /admin/finops/* endpoints + showback generation + chargeback calculation + CSV/PDF export)
- T7.8: SSOT RED→GREEN EXTENSION 결정 wire (capability matrix v1.36 신규 2 rows + capability.py EXTENSION 2 NEW enum + require_finops_showback + require_finops_chargeback 2 NEW deps wire + drift detector EXTENSION)

### T8: atomic commit (4 subtasks)
- T8.1: 3중 게이트 impact NONE 결정 wire (ruff scoped 0 NEW + pytest 0 NEW failures + vitest 0 NEW failures + tsc 0 NEW errors)
- T8.2: A19 cohesion pattern 9 surface EXTENSION PASS 결정 wire (FinOps showback/chargeback surface NEW = F27.1~F27.7)
- T8.3: atomic commit via `git commit -F <file>` (CR 9-6 D5 prevention + PowerShell here-string 회피)
- T8.4: sprint-status.yaml `phase-11-spec-entry: backlog → done` transition 결정 wire

## Dev Notes (CR lessons applied 14종)

- **CR 0-2 RLS lesson ✅ APPLIED**: Phase 11 wire 시점에 phase_11_finops_department_mapping + phase_11_finops_showback + phase_11_finops_chargeback 3 tables 모두 RLS 자동 적용 + multi-tenant isolation test 결정 wire + tenant-scoped cost center mapping tenant_id selector 결정 wire + Phase 10 wire phase_10_slo_* table 정합 + Phase 5 wire phase_5_replication_lag table 정합 + Phase 9 wire phase_9_chaos_experiments table 정합
- **CR 1-1 audit-first INSERT ✅ APPLIED**: ActionClass.FINOPS 신규 정의 + 3 NEW audit log entries (`showback_generated` + `department_mapping_updated` + `chargeback_exported`) 결정 wire + emit_audit_typed BEFORE/AFTER FinOps event CR 1-1 verbatim 적용
- **CR 4-3/4-4 lessons carry ✅ APPLIED**: showback baseline + chargeback baseline 30d rolling + golden_diff pattern verbatim 미러 + tenant-scoped result_hash 결정 wire + Epic 8 wire `e117e09` capability drift detector 정합 패턴 + Epic 17 wire `2ada2ec` audit_log_query baseline benchmark result_hash 패턴 verbatim
- **CR 1-1 ContextVar lesson ✅ APPLIED**: trace_id request-scoped ContextVar 바인딩 + 비동기 trace context 보존 CR 1-1 verbatim 적용 + FinOps event 의 trace_id propagation 결정 wire
- **CR 1-1 RSC boundary lesson ✅ APPLIED**: `apps/web/app/[locale]/(dashboard)/admin/finops/page.tsx` Client-only + finops dashboard server-only delegation 결정 wire + CR 1-1 verbatim 적용
- **CR 9-6 commit message discipline ✅ APPLIED**: `git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention 결정 wire
- **CR 11-3 honest-DEFER discipline ✅ APPLIED**: 106번째 epic 연속 정직 회복 결정 wire (D-1-1-DEFER-* + D-EPIC-16-REVIEW-DEFER-* + D-PHASE-4-DR-DEFER-* + D-EPIC-17-WIRE-DEFER-T2-T3-UI + D-RETENTION-1 + D-OBSERVABILITY-1 + D-PERFORMANCE-1 + D-CHAOS-1 + D-SLO-1 모두 ✅ ALL RESOLVED 보존 + D-FINOPS-1 honestly ✅ RESOLVED 보존 진입 결정)
- **CR 11-4 D-001~D-005 + P-015 lessons carry ✅ APPLIED**: dry-run mode UI 진입 시 frontend territory 정합 sweep 결정 wire + ko-KR.json SSOT only + vitest RTL render discipline + owner-only RBAC + unknown state reject + ko-KR.json SSOT drift detector 결정 wire
- **CR 12-1 L4 industry-agnostic capability ✅ APPLIED**: FINOPS_SHOWBACK + FINOPS_CHARGEBACK industry-agnostic 4-industry grants ✅/✅/✅/✅ 결정 wire + capability matrix v1.36 EXTENSION 결정 wire
- **CR 12-5 D-14 typed exception envelope ✅ APPLIED**: 6 NEW typed exception classes (ShowbackDefinitionInvalidError(400) + ShowbackExportError(500) + ChargebackRuleInvalidError(400) + ChargebackCalculationError(500) + ChargebackExportError(500) + ChargebackExportRateLimitedError(429)) 결정 wire + apps/api/main.py EXTENSION 결정 wire
- **CR 12-5 D-PARITY-01 inversion ✅ APPLIED**: Python FastAPI backend showback_dsl.py TypedDict ↔ TypeScript Next.js frontend finops-client.ts interface parity 결정 wire + vitest CR 12-5 D-PARITY-01 검증 결정 wire
- **CR 12-5 D-GATE-01 inversion ✅ APPLIED**: FINOPS_SHOWBACK + FINOPS_CHARGEBACK capability gate per-tenant on/off + owner-only RBAC AD-22 결정 wire + gate 적용 대상 명시 결정 wire
- **A19 cohesion pattern 9 surface EXTENSION PASS ✅**: FinOps showback/chargeback surface NEW = F27.1~F27.7 FinOps Showback / Chargeback territory 결정 wire + spec surface EXTENSION + test surface EXTENSION + docs surface EXTENSION 결정 wire
- **A36 SDR 검증 4-step 자동 적용 ✅**: commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS 결정 wire
- **AD-14 stack pin ✅ APPLIED**: pandas + reportlab + jinja2 + openpyxl + pdfkit + weasyprint + python-magic (Phase 10 wire prometheus_client + alertmanager + slack_sdk + pagerduty + libfaketime EXTENSION 결정 wire)
- **AD-22 owner-only RBAC ✅ APPLIED**: showback generation + chargeback issue + department mapping update + cost pool recalculation 모두 owner-only RBAC AD-22 + Epic 12 2FA 챌린지 보존 결정 wire
- **NFR4 PII minimization ✅ PRESERVED**: showback/chargeback data 는 사업 metric + cost amount 만 포함, PII 미포함 결정 wire

## Architecture Alignment (cj-style ALLOWED sweep — Phase 10 wire 정합)

**ALLOWED_SERVICE_SUBMODULES sweep CR 11-3 D-2 verbatim** (Phase 5 wire `f093f8c` + Phase 7 wire `59b56cd` + Phase 8 wire `60d4ea1` + Phase 9 wire `e7670e1` + Phase 10 wire `ac5d6c5` 정합):

### Backend (FastAPI, Python 3.12)
- ✅ `apps/api/modules/finops/` (NEW): `showback_dsl.py` + `showback_query.py` + `chargeback_engine.py` + `chargeback_rule_evaluator.py` + `department_mapping.py` + `chargeback_export.py` + `__init__.py` + `serializers.py`
- ✅ `apps/api/core/capability.py` (MODIFIED): Capability.FINOPS_SHOWBACK + Capability.FINOPS_CHARGEBACK enum EXTENSION + 4 INDUSTRY_CAPABILITIES EXTENSION
- ✅ `apps/api/dependencies/capability.py` (MODIFIED): require_finops_showback + require_finops_chargeback EXTENSION
- ✅ `apps/api/core/audit_action.py` (MODIFIED): ActionClass.FINOPS + FinopsAction Literal 3 NEW + _ActionRegistry FINOPS entry 3 신규 등록 + __all__ EXTENSION
- ✅ `apps/api/core/errors.py` (MODIFIED): 6 NEW typed exception classes CR 12-5 D-14 verbatim
- ✅ `apps/api/alembic/versions/0043_phase_11_finops.py` (NEW): 3 tables + indexes + RLS policies
- ✅ `apps/api/main.py` (MODIFIED): /admin/finops/* endpoints EXTENSION (CR 1-1 RSC boundary 적용)

### Frontend (Next.js 15.x, TypeScript 5.x)
- ✅ `apps/web/app/[locale]/(dashboard)/admin/finops/page.tsx` (NEW): RSC + finops dashboard
- ✅ `apps/web/app/[locale]/(dashboard)/admin/finops/layout.tsx` (NEW): RTL section wrapper
- ✅ `apps/web/components/finops/FinopsDashboardPanel.tsx` (NEW): 4 components (ShowbackPeriodSelector + ShowbackDepartmentBreakdownChart + ShowbackComparisonView + ShowbackCSVExportButton)
- ✅ `apps/web/lib/finops/finops-client.ts` (NEW): ShowbackRequest + DepartmentBreakdown + ComparisonView + ChargebackRule + ChargebackExport TypedDict CR 12-5 D-PARITY-01 verbatim + 4 fetch wrappers + ChargebackApiError class
- ✅ `apps/web/messages/ko-KR.json` (MODIFIED): EXTENSION `finops.*` namespace ~25 keys 결정 wire

### Tests
- ✅ `tests/api/core/test_phase_11_finops*.py` (NEW): ~36 NEW pytest
- ✅ `tests/integration/test_finops_tenant_isolation.py` (NEW): multi-tenant isolation CR 0-2 verbatim
- ✅ `tests/integration/test_capability_matrix_v1_36_drift.py` (NEW): 10 NEW pytest cases
- ✅ `apps/web/__tests__/finops/finops-dashboard.test.tsx` (NEW): ~5 NEW vitest
- ✅ `apps/web/__tests__/i18n/finops-i18n-ssot.test.ts` (NEW): SSOT drift NFR18 ko-KR 정합

### Docs
- ✅ `docs/finops-showback-chargeback.md` (NEW): ~+200 LOC 14 sections runbook 결정 wire
- ✅ `docs/capability-matrix.md` (MODIFIED): v1.35 → v1.36 EXTENSION

## Files Affected (estimate)

- **~18 NEW**: `apps/api/modules/finops/*` (8 files) + `apps/api/alembic/versions/0043_phase_11_finops.py` + `apps/web/app/[locale]/(dashboard)/admin/finops/{page,layout}.tsx` (2 files) + `apps/web/components/finops/FinopsDashboardPanel.tsx` + `apps/web/lib/finops/finops-client.ts` + tests (4 files) + `docs/finops-showback-chargeback.md`
- **~12 MODIFIED**: `apps/api/core/capability.py` + `apps/api/dependencies/capability.py` + `apps/api/core/audit_action.py` + `apps/api/core/errors.py` + `apps/api/main.py` + `apps/web/messages/ko-KR.json` + `docs/capability-matrix.md` + `_bmad-output/implementation-artifacts/sprint-status.yaml` + `apps/api/alembic/versions/script.py.mako` + `apps/api/main.py` (typed exception handlers EXTENSION) + tenant_settings schema migration + `tests/integration/conftest.py`
- **Total**: ~30 files atomic single sprint

## Test Coverage

- **~46 NEW pytest PASS 결정 wire**:
  - `tests/api/core/test_phase_11_showback_dsl.py` (6 cases): TypedDict validation + 6 period selector 모드 + 5 group_by 옵션 + comparison view + audit-first INSERT + owner-only RBAC + dry_run default
  - `tests/api/core/test_phase_11_chargeback_engine.py` (7 cases): 3 rule_type + markup + tax + cost_allocation_method + audit-first INSERT + multi-region + dry-run
  - `tests/api/core/test_phase_11_department_mapping.py` (5 cases): validate_department_mapping + auto-create + audit-first INSERT + UNIQUE constraint + RLS policy
  - `tests/api/core/test_phase_11_chargeback_export.py` (6 cases): CSV streaming + PDF generation + rate limit + audit-first INSERT + permission check + error envelope
  - `tests/integration/test_finops_tenant_isolation.py` (4 cases): cross-tenant isolation + cost center mapping isolation
  - `tests/integration/test_capability_matrix_v1_36_drift.py` (10 cases): FINOPS_SHOWBACK + FINOPS_CHARGEBACK enum + 4-industry grants + v1.35 + v1.34 + ... preservation
  - `tests/api/core/test_phase_11_audit_action.py` (8 cases): 3 NEW audit log entries + ActionClass.FINOPS + emit_audit_typed CR 1-1
  - **Subtotal**: ~46 NEW pytest PASS

- **~5 NEW vitest PASS 결정 wire**:
  - `apps/web/__tests__/finops/finops-dashboard.test.tsx` (3 cases): ShowbackPeriodSelector + ShowbackDepartmentBreakdownChart + ShowbackComparisonView
  - `apps/web/__tests__/i18n/finops-i18n-ssot.test.ts` (2 cases): ko-KR SSOT drift detection + CR 12-5 D-PARITY-01 verification
  - **Subtotal**: ~5 NEW vitest PASS

- **0 NEW ruff 결정 wire** (apps/api backend 결정 wire + 기존 ruff scoped 0 NEW 정합 보존)
- **0 NEW tsc 결정 wire** (apps/web frontend 결정 wire + 기존 tsc 0 NEW 정합 보존)
- **0 regressions 결정 wire** (3중 게이트 FINAL CLEAN + ruff scoped 0 NEW + pytest 0 NEW failures + vitest 0 NEW failures + tsc 0 NEW errors)

## Notes

- `apps/api/main.py` EXTENSION 시 /admin/finops/* endpoints EXTENSION + require_finops_showback + require_finops_chargeback dep 적용
- `apps/api/core/errors.py` EXTENSION 시 6 NEW typed exception classes + envelope CR 11-4 P-015 적용
- `apps/api/core/audit_action.py` EXTENSION 시 ActionClass.FINOPS + FinopsAction Literal 3 NEW values + _ActionRegistry FINOPS entry 3 신규 등록
- m19_finops.finops_serializers NEW Phase 11 EXTENSION 결정 wire (wire 시점에 sprint-status.yaml action_items EXTENSION + Epic 9 + Epic 16 + Phase 5 wire 정합)
- Phase 10 wire `ac5d6c5` 의 monthly reset KST 1일 00:00 + 30d rolling calculation 정합 결정 wire
- Phase 8 wire `60d4ea1` 의 cost-engine V8 골든 fixture + 4 SLIs 자연스러운 EXTENSION 결정 wire
- Phase 5 wire `f093f8c` multi-region failover 의 region_weight_map 정합 결정 wire + phase_5_replication_lag 100MB threshold 정합
- Phase 7 wire `59b56cd` observability 의 Prometheus custom metrics + Slack channel EXTENSION 결정 wire
- Epic 12 2FA 챌린지 mandatory 결정 wire (showback generation + chargeback issue + department mapping update + CSV/PDF export 모두 Epic 12 2FA 챌린지 mandatory)
- AD-22 owner-only RBAC 보존 결정 wire (showback generation + chargeback issue + department mapping update + cost pool recalculation + CSV/PDF export 모두 owner-only)
- AD-14 stack pin 결정 wire (pandas + reportlab + jinja2 + openpyxl + pdfkit + weasyprint + python-magic)
- NFR4 PII minimization PRESERVED (showback/chargeback data 는 사업 metric + cost amount 만 포함, PII 미포함)
- 3중 게이트 impact NONE (cj-style 106번째 wire 진입 표준 = docs only 변경): ruff scoped 0 NEW + pytest 0 NEW + vitest 0 NEW + tsc 0 NEW
- 7 ACs PRD §F27.1~§F27.7 verbatim → 78 sub-ACs (12+12+10+10+10+12+12 = 78 sub-ACs) satisfied pre-flight 정합 sweep 결정 wire

## Cross-References

- Phase 11 PRD entry `16d7698` (cj-style 105번째)
- Phase 10 wire `ac5d6c5` (cj-style 103번째) — SLO Engineering / Error Budget Management territory 정합
- Phase 10 close-out retro `733d428` (cj-style 104번째) — D-FINOPS-1 honestly DEFER 보존 해소
- Phase 10 spec entry `3c80ef0` (cj-style 102번째)
- Phase 10 PRD entry `09db4d4` (cj-style 101번째)
- Phase 9 wire `e7670e1` (cj-style 99번째) — Chaos Engineering / Game Day territory 정합
- Phase 9 close-out retro `634427d` (cj-style 100번째)
- Phase 8 wire `60d4ea1` (cj-style 95번째) — cost-engine V8 골든 fixture + 4 SLIs 자연스러운 EXTENSION
- Phase 8 close-out retro `ab495a8` (cj-style 96번째)
- Phase 7 wire `59b56cd` (cj-style 91번째) — observability 정합
- Phase 7 close-out retro `326fa9f` (cj-style 92번째)
- Phase 5 wire `f093f8c` (cj-style 75번째) — multi-region failover + replication_lag 정합
- Epic 12 2FA 게이트 `a63646c` — Epic 12 2FA 챌린지 mandatory
- Epic 1 carry-over (auth) — onboarding/industry 보존
- AD-14 stack pin — pandas + reportlab + jinja2 + openpyxl + pdfkit + weasyprint + python-magic
- AD-22 owner-only RBAC — showback generation + chargeback issue + department mapping update + cost pool recalculation + CSV/PDF export
- NFR18 ko-KR — SSOT only invariant
- NFR4 PII minimization — showback/chargeback data PII 미포함
- CR 0-2 RLS lesson, CR 1-1 audit-first INSERT, CR 4-3/4-4 lessons carry, CR 1-1 ContextVar, CR 1-1 RSC boundary, CR 9-6 commit message, CR 11-3 honest-DEFER, CR 11-4 D-001~D-005 + P-015, CR 12-1 L4 industry-agnostic capability, CR 12-5 D-14 envelope, CR 12-5 D-PARITY-01, CR 12-5 D-GATE-01, A19 cohesion 9 surface EXTENSION PASS, A36 SDR 검증 4-step 자동 적용
- m19_finops.finops_serializers NEW Phase 11 EXTENSION 결정 wire (wire 시점에)

## 결정 wire 일자

2026-08-24 (KST)

## next (wire 진입 시)

옵션 (a) Phase 11 bmad-dev-story atomic wire T1~T8 진입 (cj-style 107번째 wire 진입 시점) 결정 wire 진입 / 옵션 (b) Phase 11 close-out retro 진입 (cj-style 108번째) / 옵션 (c) Phase 12+ 진입 / 옵션 (d) Epic 18+ 진입 / 옵션 (e) D-DEFER-* follow-up 진입 결정 wire 보류.
