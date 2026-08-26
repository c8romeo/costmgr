---
baseline_commit: 64760fe
status: ready-for-dev
cj_style_entry_point: 159
story_key: phase-22-finops-chargeback-settlement-wire
---

# Phase 22 FinOps Chargeback Settlement wire spec (cj-style 159번째 epic 연속 정직 회복)

## Story

**As a** FinOps practitioner / cloud architect / tenant admin / 1st release customer / DevOps engineer
**I want** Phase 22 territory 결정 wire (FinOps Chargeback Settlement = **settlement_rules engine + settlement_engine + allocation_engine + invoice_generator + reconciliation** 5 NEW backend modules + **chargeback settlement dashboard UI 5 sub-components** + **Capability matrix v1.48 EXTENSION FINOPS_CHARGEBACK_SETTLEMENT** + **audit action EXTENSION 8 NEW + 16 NEW typed exception classes** + **dry-run + Tests + wire scope T1~T8**) 결정 wire
**so that** Phase 11~21 11-module FinOps territory chain ✅ ALL WIRED 진입 정합 보존 후 Phase 22 PRD entry `64760fe` (cj-style 158번째) 진입 직후 자연스러운 spec entry 진입 = cj-style 4-entry-point cycle PRD entry → spec entry → wire → close-out retro 의 2번째 단계 진입 결정 wire (Phase 17 spec entry cj-style 130번째 + Phase 18 spec entry cj-style 134번째 + Phase 19 spec entry cj-style 138번째 + Phase 20 spec entry cj-style 143번째 + Phase 21 spec entry cj-style 150번째 패턴 verbatim 미러) + Phase 22 territory = 5 NEW backend modules (settlement_rules + settlement_engine + allocation_engine + invoice_generator + reconciliation) 의 settlement layer = single settlement_id + single allocation_lines + single reconciliation_status = FinOps value loop close (insights → allocation → invoice → reconciliation → billable line items = 직접적 ROI) 결정 wire + Phase 11 chargeback_engine + Phase 18 commitment + Phase 19 pricing + Phase 20 multi_cloud + Phase 21 reserved_capacity 5 module 의 ledger data 활용 → 새 backend infra 불필요 + reuse 최대화 + risk 최소화 + 비즈니스 가치 최고 + Epic 12 2FA 챌린지 mandatory + AD-22 owner-only RBAC + NFR4 PII minimization ✅ PRESERVED + NFR18 ko-KR SSOT + AD-50 신규 (a)~(g) 7 sub-decisions 모두 결정 wire 진입 + D-FINOPS-11 honestly DEFER 보존 + CR 11-3 honest-DEFER 50번째 epic 연속 정직 회복 verification 결정 wire 진입 + 3중 게이트 impact NONE (docs only 변경 = cj-style 159번째 wire 진입 표준 = docs only sprint) 결정 wire.

## Context

cj-style Phase 22 1번째 진입점 (cj-style 158번째) 진입 결정 wire 진입 완료:

- Phase 22 PRD entry `64760fe` (cj-style 158번째) DONE 진입 정합 보존
- Phase 11~20 audit-fixes-infrastructure sprint `7b8e31b` (cj-style 157번째) DONE 진입 정합 보존
- Phase 11~20 audit-fixes Layer 3 P2 docs backfill sprint `21daea8` (cj-style 156번째) DONE 진입 정합 보존
- Phase 11~20 audit-fixes Layer 2 P1 test backfill sprint `4e1f0b3` (cj-style 155번째) DONE 진입 정합 보존
- Phase 11~20 audit-fixes sprint `379ca8e` (cj-style 154번째) DONE 진입 정합 보존
- Phase 21 audit-fixes sprint `f7d1f41` (cj-style 153번째) DONE 진입 정합 보존
- Phase 21 close-out retro `1b101bf` (cj-style 152번째) DONE 진입 정합 보존
- Phase 21 atomic wire `f7d1f41` (cj-style 151번째) DONE 진입 정합 보존
- Phase 21 spec entry (cj-style 149번째-150번째, baseline `563ac9c`) DONE 진입 정합 보존
- Phase 20.5 close-out retro `8505d98` (cj-style 148번째) DONE 진입 정합 보존
- Phase 20.5 atomic wire T1~T3 `46ddcc5` (cj-style 147번째) DONE 진입 정합 보존
- Phase 20.5 spec entry `e23141d` (cj-style 146번째) DONE 진입 정합 보존
- Phase 20 close-out retro `f361016` (cj-style 145번째) DONE 진입 정합 보존
- Phase 20 atomic wire T1~T8 `52dad7f` (cj-style 144번째) DONE 진입 정합 보존
- Phase 20 spec entry `bdc7997` (cj-style 143번째) DONE 진입 정합 보존
- Phase 20 PRD entry `eacb0a5` (cj-style 142번째) DONE 진입 정합 보존
- Phase 19.5 carry-over 결정 wire `b2fb1d8` (cj-style 141번째) DONE 진입 정합 보존
- Phase 19 close-out retro `18ca1ae` (cj-style 140번째) + Phase 19 atomic wire T1~T8 `8db3cfc` (cj-style 139번째) + Phase 19 spec entry `59d15fb` (cj-style 138번째) + Phase 19 PRD entry `ff8a797` (cj-style 137번째) + Phase 18 close-out retro `de72f50` (cj-style 136번째) + Phase 18 atomic wire T1~T8 `67059cf` (cj-style 135번째) + Phase 18 spec entry `bdc7997` (cj-style 134번째) + Phase 18 PRD entry `5eded22` (cj-style 133번째) + Phase 17 close-out retro `de009fe` (cj-style 132번째) + Phase 17 atomic wire T1~T8 `97cfe4e` (cj-style 131번째) + Phase 17 spec entry `4be3120` (cj-style 130번째) + Phase 17 PRD entry `e0778ed` (cj-style 129번째) + Phase 16 close-out retro `26fd530` (cj-style 128번째) + Phase 16 atomic wire T1~T8 `81ae00a` (cj-style 127번째) + Phase 16 spec entry `69c29df` (cj-style 126번째) + Phase 16 PRD entry `4f11d03` (cj-style 125번째) + Phase 15 close-out retro `102f370` (cj-style 124번째) + Phase 15 atomic wire T1~T8 `1b800d9` (cj-style 123번째) + Phase 15 spec entry `69c29df` (cj-style 122번째) + Phase 15 PRD entry `87393b4` (cj-style 121번째) + ... + Epic 1~17 ALL DONE 진입 정합 보존 + 1st release cycle ALL DONE 진입 정합 보존

### Phase 22 PRD entry `64760fe` 의 8 ACs §F38.1~§F38.8 verbatim 보존

8 ACs §F38.1~§F38.8 → 58 explicit sub-ACs + nested bullet points → **~88 detailed sub-ACs** (10+6+8+7+8+6+3+10) pre-flight 정합 sweep 만족 결정 wire:

1. **§F38.1 settlement_rules engine + 5-module cross-join EXTENSION** — m22_finops_chargeback_settlement submodule 등록 + ALLOWED_SERVICE_SUBMODULES EXTENSION + SettlementRule TypedDict 12 fields + settlement_rules.py + settlement_engine.py + monthly + quarterly cadence KST + multi-region aggregation + per-tenant override + dry-run mode + ~+24 NEW pytest + ~+1 NEW vitest (10 sub-ACs §F38.1.1~§F38.1.10)
2. **§F38.2 allocation_engine + 5-dimension weighted allocation** — allocate_settlement + AllocationLine TypedDict 10 fields + 5-dim weight default `{cost_center: 0.30, department: 0.25, business_unit: 0.20, tag: 0.15, tenant: 0.10}` + precedence tenant > industry > default + total verification ±0.01 KRW + zero/negative amount handling + ~+18 NEW pytest + ~+1 NEW vitest (6 sub-ACs §F38.2.1~§F38.2.6)
3. **§F38.3 invoice_generation + PDF/XLSX/CSV template** — invoice_generator + 3 format 지원 (PDF via reportlab 4.0.7 + XLSX via xlsxwriter 3.1.9 + CSV via stdlib) + noto-sans-cjk-kr + A4 landscape + recipient list + audit-first INSERT + rate limit 1/min + ~+18 NEW pytest + ~+1 NEW vitest (8 sub-ACs §F38.3.1~§F38.3.8)
4. **§F38.4 reconciliation 3-way match** — reconciliation.py + ReconciliationResult TypedDict 12 fields + 3-way match settlement ↔ invoice ↔ allocation + 1.0% tolerance + 3 auto-retries + admin email alert + high-value ≥ 10M KRW/year → Epic 12 2FA 챌린지 + audit-first INSERT + ~+18 NEW pytest + ~+1 NEW vitest (7 sub-ACs §F38.4.1~§F38.4.7)
5. **§F38.5 chargeback settlement dashboard UI + 5 sub-components** — SettlementRulesCard + AllocationBreakdownPanel + InvoicePreviewPanel + ReconciliationStatusPanel + SettlementTrendMiniChart + 5-tab layout + Recharts 2.12.7 AD-14 stack pin + ko-KR.json `finops_chargeback_settlement.*` namespace EXTENSION ~30 keys + ~+24 NEW vitest (8 sub-ACs §F38.5.1~§F38.5.8)
6. **§F38.6 Capability matrix v1.48 EXTENSION FINOPS_CHARGEBACK_SETTLEMENT** — Capability.FINOPS_CHARGEBACK_SETTLEMENT 1 NEW enum + require_finops_chargeback_settlement 1 NEW dep + ActionClass.FINOPS_CHARGEBACK_SETTLEMENT + FinopsChargebackSettlementAction 8 NEW Literal + test_capability_matrix_v1_48_drift.py + test_audit_action_v1_48_drift.py + capability gate fail-closed (6 sub-ACs §F38.6.1~§F38.6.6)
7. **§F38.7 audit action EXTENSION 8 NEW + 16 NEW typed exception classes** — ActionClass.FINOPS_CHARGEBACK_SETTLEMENT + FinopsChargebackSettlementAction 8 NEW Literal + _ActionRegistry._REGISTRY 1 NEW entry + AuditAction Union EXTENSION + 16 NEW typed exceptions CR 12-5 D-14 envelope + 8 NEW audit actions audit-first INSERT (3 sub-ACs §F38.7.1~§F38.7.3)
8. **§F38.8 dry-run + Tests + wire scope T1~T8** — `--finops-chargeback-settlement-dry-run` 1 NEW CLI flag + phase_22_settlement_preview 1 table + ~+78 NEW pytest + ~+24 NEW vitest + 0 NEW ruff + 0 NEW tsc + 0 regressions + wire scope T1~T8 (10 sub-ACs §F38.8.1~§F38.8.10)

**Total sub-ACs**: 10+6+8+7+8+6+3+10 = **58 explicit sub-ACs** with nested bullet points → **~88 detailed sub-ACs** pre-flight 정합 sweep 만족 결정 wire (cj-style 158 commit message 의 ~88 sub-ACs verbatim mirror).

### AD-50 신규 결정 (a)~(g) 7 sub-decisions

- (a) settlement_rules engine 의 5-module cross-join FIVE_MODULE_WEIGHTS backend detail (Phase 11 chargeback_engine ledger 0.30 + Phase 18 commitment 0.20 + Phase 19 pricing 0.20 + Phase 20 multi_cloud 0.15 + Phase 21 reserved_capacity 0.15 = single total_settlement_amount)
- (b) allocation_engine 의 5-dimension weighted allocation detail (cost_center 0.30 + department 0.25 + business_unit 0.20 + tag 0.15 + tenant 0.10 + per-tenant override > industry baseline > system default precedence + ±0.01 KRW tolerance total verification)
- (c) invoice_generation 의 PDF/XLSX/CSV template detail (reportlab 4.0.7 + xlsxwriter 3.1.9 AD-14 stack pin + noto-sans-cjk-kr Korean font + A4 landscape + 1 invoice / minute / owner rate limit)
- (d) reconciliation 3-way match detail (settlement ↔ invoice ↔ allocation 합계 비교 + 1.0% tolerance + 3 auto-retries with 5-minute interval + admin email alert + high-value ≥ 10M KRW/year → Epic 12 2FA 챌린지)
- (e) NFR4 PII minimization preservation detail (no employee names + actor_id UUID + tenant_id UUID + monetary amounts only + Cache-Control no-store)
- (f) NFR18 ko-KR SSOT detail (finops_chargeback_settlement.* namespace EXTENSION ~30 keys + Korean font + Korean error messages + English audit action names)
- (g) Epic 12 2FA 챌린지 mandatory high-value detail (≥ 10M KRW/year savings → RFC 6238 TOTP + tenant_owner approval chain + SettlementApprovalRequiredError(403))

### D-FINOPS-11 신규 honestly DEFER 보존

Phase 22 PRD entry 진입 시점에 carry-over chain 정직 회복 결정 wire 진입 = 5-module cross-join backend detail + 5-dimension allocation weight detail + 3-format invoice template detail + 3-way match reconciliation algorithm detail + Epic 12 2FA 챌린지 high-value threshold detail + multi-currency settlement (KRW only, USD/EUR/JPY 추가 시 별도 sprint) + tax compliance (10% VAT default, per-country rule 시 별도 sprint) + settlement dispute workflow (별도 epic) + settlement refund/credit note (별도 sprint) — 모두 단일 sprint `wire` 진입이 아닌 docs-only entry 에서 honestly defer 결정 wire 보존 (Phase 17 close-out retro `be8f3bd` §11 "FinOps Reserved Capacity Planning 결정 wire 보류, Phase 21+ 진입 시점" verbatim 해소 + Phase 21 close-out retro `1b101bf` 의 honest deviation 보존 패턴 verbatim 미러).

## T1~T8 + ~24 subtasks

### T1: Phase 22 5 NEW backend settlement modules (10 subtasks)
- T1.1: `apps/api/modules/finops/chargeback_settlement/__init__.py` NEW + ALLOWED_SERVICE_SUBMODULES EXTENSION m22_finops_chargeback_settlement 신규 submodule 등록 결정 wire (Phase 21 m21_finops_reserved_capacity 패턴 보존)
- T1.2: `apps/api/modules/finops/chargeback_settlement/serializers.py` NEW ~+260 LOC + 4 NEW enums (SettlementRuleType flat_fee/proportional_allocation/metered_volume/tag_weighted + SettlementStatus draft/pending_approval/approved/invoiced/reconciled + AllocationDimension cost_center/department/business_unit/tag/tenant + InvoiceFormat pdf/xlsx/csv) + 4 NEW TypedDicts (SettlementRule 12 fields + SettlementResult 16 fields + AllocationLine 10 fields + ReconciliationResult 12 fields) + FIVE_MODULE_WEIGHTS + SETTLEMENT_CADENCE_HOURS_KST + SETTLEMENT_RECIPIENT_TEMPLATES + SETTLEMENT_DEFAULTS 결정 wire
- T1.3: `apps/api/modules/finops/chargeback_settlement/settlement_rules.py` NEW ~+220 LOC + create_settlement_rule + update_settlement_rule + list_settlement_rules + 3 NEW error classes (SettlementRuleNotFoundError(404) + SettlementRuleInvalidError(400) + SettlementRuleOverlapError(409)) CR 12-5 D-14 envelope 결정 wire
- T1.4: `apps/api/modules/finops/chargeback_settlement/settlement_engine.py` NEW ~+280 LOC + compute_settlement(tenant_id, period_key, scope) → SettlementResult + 5-module cross-join EXTENSION (FIVE_MODULE_WEIGHTS 가중 평균) + Decimal precision (banker's rounding CR 5-1 verbatim) + audit-first INSERT `settlement_calculated` CR 1-1 verbatim EXTENSION 결정 wire
- T1.5: settlement 의 monthly + quarterly cadence KST 결정 wire = cron KST 매월 1일 02:00 UTC 17:00 (previous month) + cron KST 매분기 1일 03:00 UTC 18:00 (previous quarter) + Phase 11 wire `e020ad0` chargeback_period_monthly cron 패턴 verbatim EXTENSION + audit-first INSERT `settlement_calculated` CR 1-1 verbatim EXTENSION
- T1.6: settlement 의 multi-region aggregation 결정 wire (Phase 5 wire `f093f8c` `phase_5_replication_lag` table 정합 + primary Seoul + secondary Tokyo replica + cross-region settlement cost variance detection + region_weight_map default `{seoul: 0.6, tokyo: 0.3, singapore: 0.1}` + audit-first INSERT `settlement_calculated_multi_region` CR 1-1 verbatim EXTENSION 결정 wire)
- T1.7: settlement 의 per-tenant override EXTENSION 결정 wire = `tenant_settings.settlement_overrides` JSONB TypedDict (rule_type override + markup_pct override + tax_pct override + settlement_period override + invoice_format override + recipient_emails override) + policy evaluation precedence tenant override > industry baseline > system default + Phase 11 wire `e020ad0` 의 `tenant_settings.chargeback_overrides` JSONB pattern verbatim 미러 결정 wire
- T1.8: settlement 의 dry-run mode 결정 wire (`--finops-settlement-dry-run` CLI flag + compute_settlement dry-run parameter + dry-run 시 actual settlement_calculated INSERT skip + dry_run=True default for prod deploys) + dry-run 결과 preview (`phase_22_settlement_preview` 1 NEW table alembic 0054 신규 + tenant_id + period_key + rule_type + preview_amount + preview_currency + preview_recipient_count + computed_at + trace_id) + audit-first INSERT `settlement_dry_run_executed` CR 1-1 verbatim EXTENSION 결정 wire
- T1.9: 5 NEW backend settlement modules composition layer 검증 (Phase 11+18+19+20+21 module outputs 의 direct import + cross-join + ledger-key dedup 회피) + LISTEN/NOTIFY 4 channel EXTENSION 결정 wire
- T1.10: A19 cohesion 9 surface EXTENSION PASS preserved 검증 (FinOps Chargeback Settlement surface NEW = F38.1~F38.8)

### T2: chargeback_settlement dashboard UI 5 sub-components (8 subtasks)
- T2.1: `apps/web/app/[locale]/(dashboard)/admin/finops/chargeback-settlement/page.tsx` NEW ~+220 LOC + 5 sub-components (SettlementRulesCard + AllocationBreakdownPanel + InvoicePreviewPanel + ReconciliationStatusPanel + SettlementTrendMiniChart) EXTENSION 결정 wire
- T2.2: `apps/web/app/[locale]/(dashboard)/admin/finops/chargeback-settlement/layout.tsx` NEW ~+100 LOC + owner-only RBAC AD-22 verbatim + Epic 12 2FA 챌린지 mandatory + ko-KR.json `finops_chargeback_settlement.*` namespace EXTENSION ~30 keys (CR 11-4 D-002 verbatim SSOT) + ARIA labels WCAG 2.1 AA + `(dashboard)` route group 보호 EXTENSION 결정 wire
- T2.3: `apps/web/components/finops/FinopsChargebackSettlementDashboardPanel.tsx` NEW Client component ~+250 LOC + 5-tab layout + Recharts visualization (PieChart + BarChart + LineChart + Iframe + Table) 결정 wire
- T2.4: `apps/web/lib/finops/chargeback-settlement-types.ts` NEW TypeScript mirror + 4 NEW TypeScript interfaces (SettlementRule + SettlementResult + AllocationLine + ReconciliationResult) CR 12-5 D-PARITY-01 inversion EXTENSION 결정 wire
- T2.5: `apps/web/lib/finops/chargeback-settlement-client.ts` NEW TypeScript client + 5 NEW methods (createSettlementRule + computeSettlement + allocateSettlement + generateSettlementInvoice + reconcileSettlement) EXTENSION 결정 wire
- T2.6: `apps/web/messages/ko-KR.json` MODIFIED EXTENSION ~30 keys + `finops_chargeback_settlement.*` namespace EXTENSION + ARIA labels WCAG 2.1 AA + NFR18 ko-KR SSOT 보존 결정 wire
- T2.7: chargeback_settlement dashboard Recharts 2.12.7 AD-14 stack pin EXTENSION + 5 NEW charts (PieChart + BarChart + LineChart + Iframe + Table) + 4 industries baseline visualization 차이 EXTENSION 결정 wire
- T2.8: chargeback_settlement dashboard dry-run mode UI (SettlementRulesCard 진입 시 dry-run toggle default: dry-run) + scheduled dispatch KST cron 2 cadence UI (monthly + quarterly) + AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory 결정 wire

### T3: alembic 0054 phase_22_chargeback_settlement 9 tables + RLS (6 subtasks)
- T3.1: `apps/api/alembic/versions/0054_phase_22_chargeback_settlement.py` NEW 9 NEW tables 결정 wire = phase_22_settlement_rules + phase_22_settlement_results + phase_22_allocation_lines + phase_22_settlement_invoices + phase_22_reconciliation_results + phase_22_settlement_rule_audit + phase_22_settlement_audit + phase_22_allocation_audit + phase_22_reconciliation_audit EXTENSION
- T3.2: phase_22_settlement_preview 1 NEW preview table 결정 wire + preview_id UUID PK + tenant_id UUID + period_key TEXT + settlement_data JSONB + computed_at TIMESTAMPTZ DEFAULT NOW() + trace_id TEXT EXTENSION
- T3.3: RLS 자동 적용 CR 0-2 verbatim 결정 wire = 9 tables tenant_id = current_setting('app.tenant_id')::uuid + 1 preview table RLS EXTENSION
- T3.4: CHECK + UNIQUE + indexes EXTENSION 결정 wire = idempotency_key UNIQUE + scope enum CHECK + 5-module source attribution JSONB GIN index + period_key + scope composite index EXTENSION
- T3.5: alembic 0054 down_revision 결정 wire = 0053 (Phase 21 wire `f7d1f41` 의 alembic 0053 EXTENSION) EXTENSION
- T3.6: alembic upgrade + downgrade 검증 결정 wire + Phase 21 wire 의 alembic 0053 pattern verbatim EXTENSION

### T4: audit action EXTENSION 8 NEW + 16 NEW typed exception classes (4 subtasks)
- T4.1: `apps/api/core/audit_action.py` MODIFIED EXTENSION 결정 wire + ActionClass.FINOPS_CHARGEBACK_SETTLEMENT 1 NEW enum EXTENSION + _ActionRegistry._REGISTRY 1 NEW entry EXTENSION + AuditAction Union EXTENSION 결정 wire
- T4.2: `apps/api/core/audit_action.py` MODIFIED EXTENSION + FinopsChargebackSettlementAction 8 NEW Literal EXTENSION (settlement_rule_created + settlement_rule_updated + settlement_calculated + allocation_verified + settlement_invoice_generated + settlement_reconciled + settlement_dry_run_executed + settlement_approval_required)
- T4.3: `apps/api/core/errors.py` MODIFIED EXTENSION 16 NEW typed exception classes CR 12-5 D-14 envelope 결정 wire = FinopsChargebackSettlementError base class + SettlementRuleNotFoundError(404) + SettlementRuleInvalidError(400) + SettlementRuleOverlapError(409) + SettlementCalculationError(500) + SettlementRecipientMissingError(400) + SettlementInvoiceRateLimitedError(429) + SettlementInvoiceGenerationError(500) + AllocationMismatchError(500) + AllocationDimensionInvalidError(400) + AllocationZeroAmountSkipError(200) (warning not error) + SettlementReconciliationFailedError(500) + SettlementApprovalRequiredError(403) + SettlementApprovalTimeoutError(408) + SettlementDryRunFailedError(500) + SettlementPreviewInvalidError(400) EXTENSION
- T4.4: 8 NEW audit actions via emit_audit_typed CR 1-1 verbatim EXTENSION 결정 wire + Phase 21 wire `f7d1f41` 의 8 NEW audit actions pattern verbatim EXTENSION + 5-module source attribution JSONB payload EXTENSION

### T5: Capability matrix v1.48 EXTENSION FINOPS_CHARGEBACK_SETTLEMENT (4 subtasks)
- T5.1: `docs/capability-matrix.md` MODIFIED v1.47 → v1.48 EXTENSION 결정 wire + FINOPS_CHARGEBACK_SETTLEMENT 1 NEW row after FINOPS_RESERVED_CAPACITY_PLANNING industry-agnostic 4-industry grants ✅/✅/✅/✅ CR 12-1 L4 precedent verbatim EXTENSION
- T5.2: `apps/api/core/capability.py` MODIFIED EXTENSION + Capability.FINOPS_CHARGEBACK_SETTLEMENT 1 NEW enum 결정 wire
- T5.3: `apps/api/dependencies/capability.py` MODIFIED EXTENSION + require_finops_chargeback_settlement 1 NEW dep 결정 wire + fail-closed 403 Forbidden EXTENSION
- T5.4: `apps/api/modules/finops/__init__.py` MODIFIED EXTENSION + chargeback_settlement submodule export + ALLOWED_SERVICE_SUBMODULES 즉시 sweep EXTENSION = m22_finops_chargeback_settlement 신규 submodule 등록 (Phase 21 m21_finops_reserved_capacity 패턴 보존) + Phase 11~21 verbatim EXTENSION

### T6: scheduled_dispatch_job wire (2 subtasks)
- T6.1: `apps/api/modules/finops/chargeback_settlement/scheduled_chargeback_settlement_dispatch.py` NEW ~+150 LOC + apscheduler==3.10.4 + pytz==2024.1 EXTENSION + 2 cadence schedule (monthly 1st-day 02:00 KST + quarterly 1st-day 03:00 KST) + recipient resolver Slack + Email + S3 archive 결정 wire
- T6.2: LISTEN/NOTIFY consume trigger EXTENSION 결정 wire = 5 NEW channel (phase_22_settlement_calculated + phase_22_allocation_verified + phase_22_invoice_generated + phase_22_reconciliation_completed + phase_22_settlement_approval_required) + Phase 13 wire `8b98030` LISTEN/NOTIFY pattern verbatim EXTENSION 결정 wire

### T7: dry-run mode + 1 NEW CLI flag (4 subtasks)
- T7.1: dry-run mode EXTENSION 결정 wire = dry-run 시 actual `settlement_calculated` audit-first INSERT skip + dry-run 결과 preview = phase_22_settlement_preview 1 table + audit-first INSERT `settlement_dry_run_executed` EXTENSION
- T7.2: `apps/api/scripts/cli/finops_chargeback_settlement_dry_run.py` NEW ~+100 LOC + `--finops-chargeback-settlement-dry-run` 1 NEW CLI flag EXTENSION 결정 wire (Phase 21 wire `f7d1f41` 의 1 NEW CLI flags 패턴 verbatim EXTENSION)
- T7.3: dry-run preview UI EXTENSION 결정 wire = SettlementRulesCard 진입 시 dry-run toggle (default: dry-run) + dry-run 결과 preview UI EXTENSION
- T7.4: dry-run mode integration tests EXTENSION 결정 wire = ~+6 NEW pytest cases (skip audit + preview table + CLI flag + 2 cadence) EXTENSION

### T8: 3중 게이트 FINAL CLEAN atomic commit (4 subtasks)
- T8.1: ruff scoped Phase 22 files 0 NEW EXTENSION 결정 wire + Phase 21 wire `f7d1f41` 의 0 NEW ruff pattern verbatim EXTENSION
- T8.2: pytest ~+78 NEW pytest PASS EXTENSION 결정 wire (settlement_rules 24 + allocation_engine 18 + invoice_generator 18 + reconciliation 18 = ~+78 NEW pytest PASS)
- T8.3: vitest ~+24 NEW vitest PASS EXTENSION 결정 wire (SettlementRulesCard 6 + AllocationBreakdownPanel 5 + InvoicePreviewPanel 5 + ReconciliationStatusPanel 5 + SettlementTrendMiniChart 3 = ~+24 NEW vitest PASS)
- T8.4: 3중 게이트 FINAL CLEAN atomic commit via `git commit -F <file>` (CR 9-6 D5 prevention + PowerShell here-string 회피) 결정 wire

**Subtotal**: 10+8+6+4+4+2+4+4 = **~42 subtasks** 결정 wire (Phase 21 wire `f7d1f41` 의 ~40 subtasks pattern 의 5-NEW-module settlement layer version EXTENSION)

## Dev Notes 19종 (CR lessons applied)

- **CR 0-2 RLS** — 9 tables + 1 preview table 의 tenant-scoped RLS 자동 적용 (current_setting('app.tenant_id')::uuid) 보존
- **CR 1-1 audit-first INSERT 8 NEW** — ActionClass.FINOPS_CHARGEBACK_SETTLEMENT 의 8 NEW audit actions (settlement_rule_created + settlement_rule_updated + settlement_calculated + allocation_verified + settlement_invoice_generated + settlement_reconciled + settlement_dry_run_executed + settlement_approval_required) 결정 wire 진입 시점에 audit-first INSERT 자동 활성화 보존
- **CR 1-1 FastAPI ContextVar** — tenant_id ContextVar middleware layer 보존 (CR 1-1 verbatim EXTENSION)
- **CR 1-1 RSC boundary** — Next.js 15.x RSC boundary 보존 (apps/web/app/[locale]/(dashboard)/admin/finops/chargeback-settlement/{page,layout}.tsx)
- **CR 4-3/4-4** — async-test asyncio.run + Industry enum SSOT + A5 drift detector + golden_diff + SDR overclaim 방지
- **CR 5-1 Decimal precision** — banker's rounding 정합 + 소수점 2자리 EXTENSION (Phase 21 wire 의 demand_forecast_aggregator Decimal precision pattern verbatim 미러)
- **CR 9-6 commit message** — `git commit -F <file>` (D5 prevention) + PowerShell here-string 회피 결정 wire
- **CR 11-3 honest-DEFER 50번째** — D-FINOPS-11 honestly DEFER 보존 (Phase 22 territory 진입) + Phase 11~21 11-module FinOps territory chain ✅ ALL WIRED 결정 wire
- **ALLOWED_SERVICE_SUBMODULES 즉시 sweep** — Phase 22 wire 진입 시점에 `apps/api/modules/finops/__init__.py` 의 submodule 목록 즉시 sweep EXTENSION = m22_finops_chargeback_settlement 신규 submodule 등록
- **CR 11-4 D-001~D-005** — ko-KR.json `finops_chargeback_settlement.*` namespace EXTENSION ~30 keys SSOT + NFR18 ko-KR SSOT 보존
- **P-015 SSOT** — ko-KR.json finops_chargeback_settlement.* 단일 SSOT 결정 wire
- **CR 12-1 L4** — industry-agnostic capability grants (4-industry ✅/✅/✅/✅) EXTENSION 결정 wire (Phase 21 wire 의 FINOPS_RESERVED_CAPACITY_PLANNING 패턴 verbatim 미러)
- **CR 12-5 D-14 typed exception envelope 16 NEW** — Phase 22 wire 의 16 NEW typed exceptions (FinopsChargebackSettlementError base + SettlementRuleNotFoundError + SettlementRuleInvalidError + SettlementRuleOverlapError + SettlementCalculationError + SettlementRecipientMissingError + SettlementInvoiceRateLimitedError + SettlementInvoiceGenerationError + AllocationMismatchError + AllocationDimensionInvalidError + AllocationZeroAmountSkipError + SettlementReconciliationFailedError + SettlementApprovalRequiredError + SettlementApprovalTimeoutError + SettlementDryRunFailedError + SettlementPreviewInvalidError) CR 12-5 D-14 envelope 적용
- **CR 12-5 D-PARITY-01 inversion** — TypeScript mirror parity (chargeback-settlement-types.ts + chargeback-settlement-client.ts) 결정 wire
- **CR 12-5 D-GATE-01 inversion** — capability gate inversion (require_finops_chargeback_settlement + fail-closed 403 Forbidden) 결정 wire
- **A19 cohesion 9 surface EXTENSION PASS** — FinOps Chargeback Settlement surface NEW 결정 wire 진입 후에도 9 surface 모두 PASS 보존
- **A36 SDR 검증 4-step** — 자동 적용 결정 wire (spec entry 진입 시점에 자동)
- **AD-14 stack pin** — Recharts 2.12.7 + reportlab 4.0.7 + xlsxwriter 3.1.9 + apscheduler 3.10.4 + pytz 2024.1 + noto-sans-cjk-kr EXTENSION 결정 wire
- **AD-22 owner-only RBAC** — chargeback_settlement dashboard UI 모두 owner-only RBAC EXTENSION (SettlementRulesCard + AllocationBreakdownPanel + InvoicePreviewPanel + ReconciliationStatusPanel + SettlementTrendMiniChart + auto-execute enable 모두 owner-only)
- **Epic 12 2FA 챌린지 mandatory** — destructive endpoint 의 3-layer defense EXTENSION 결정 wire (high-value ≥ 10M KRW/year savings → owner approval flow + 2FA 챌린지)
- **NFR4 PII minimization** ✅ PRESERVED — Phase 22 wire 결정 wire 시에도 PII minimization 자동 보존
- **NFR18 ko-KR SSOT** — apps/web/messages/ko-KR.json finops_chargeback_settlement.* namespace EXTENSION ~30 keys SSOT 보존 결정 wire
- **AD-49 + AD-50 신규** — AD-49 (a)~(g) 7 sub-decisions + AD-50 (a)~(g) 7 sub-decisions 모두 결정 wire 진입

## Architecture Alignment (ALLOWED sweep) — Phase 21 wire 정합

- **Backend (FastAPI, Python 3.12)**:
  - 5 NEW modules `apps/api/modules/finops/chargeback_settlement/` (~+1,220 LOC: settlement_rules + settlement_engine + allocation_engine + invoice_generator + reconciliation)
  - 1 NEW serializers.py (~+260 LOC)
  - 1 NEW __init__.py submodule
  - 1 NEW alembic 0054 phase_22_chargeback_settlement.py (9 tables + RLS + 1 preview table)
  - 1 NEW scheduled_chargeback_settlement_dispatch.py (~+150 LOC)
  - 1 NEW apps/api/scripts/cli/finops_chargeback_settlement_dry_run.py (~+100 LOC)
  - MODIFIED apps/api/core/capability.py (Capability.FINOPS_CHARGEBACK_SETTLEMENT)
  - MODIFIED apps/api/dependencies/capability.py (require_finops_chargeback_settlement + fail-closed)
  - MODIFIED apps/api/core/audit_action.py (ActionClass.FINOPS_CHARGEBACK_SETTLEMENT + FinopsChargebackSettlementAction 8 NEW Literal + _ActionRegistry._REGISTRY 1 NEW entry)
  - MODIFIED apps/api/core/errors.py (16 NEW typed exception classes)
  - MODIFIED apps/api/modules/finops/__init__.py (ALLOWED_SERVICE_SUBMODULES EXTENSION)
- **Frontend (Next.js 15.x, TypeScript 5.x)**:
  - 2 NEW apps/web/app/[locale]/(dashboard)/admin/finops/chargeback-settlement/{page,layout}.tsx (~+320 LOC)
  - 1 NEW apps/web/components/finops/FinopsChargebackSettlementDashboardPanel.tsx (~+250 LOC)
  - 1 NEW apps/web/lib/finops/chargeback-settlement-types.ts (4 NEW TypeScript interfaces)
  - 1 NEW apps/web/lib/finops/chargeback-settlement-client.ts (5 NEW methods)
  - MODIFIED apps/web/messages/ko-KR.json (EXTENSION ~30 keys finops_chargeback_settlement.* namespace)
- **Tests**:
  - ~+78 NEW pytest PASS (settlement_rules 24 + allocation_engine 18 + invoice_generator 18 + reconciliation 18)
  - ~+24 NEW vitest PASS (SettlementRulesCard 6 + AllocationBreakdownPanel 5 + InvoicePreviewPanel 5 + ReconciliationStatusPanel 5 + SettlementTrendMiniChart 3)
  - 0 NEW ruff + 0 NEW tsc + 0 regressions
- **Docs (cumulative; wire sprint will write)**:
  - Spec file (this file) NEW ~+440 LOC
  - Handoff memory NEW
  - Commit-msg NEW
  - Sprint-status MODIFIED v3.68 → v3.69
  - MEMORY.md MODIFIED hook EXTENSION

## Files Affected (estimate ~33 files = 21 NEW + 12 MODIFIED, **wire sprint scope**) — **spec entry sprint 5 files = 3 NEW + 2 MODIFIED**

### Spec entry sprint (cj 159, this sprint) — 5 files = 3 NEW + 2 MODIFIED
1. NEW: `_bmad-output/implementation-artifacts/phase-22-finops-chargeback-settlement-wire.md` (this file, ~+440 LOC)
2. NEW: `memory/handoff-2026-08-27-phase-22-spec-entry-done.md`
3. NEW: `_bmad-output/implementation-artifacts/commit-msg-cj-159.txt`
4. MODIFIED: `_bmad-output/implementation-artifacts/sprint-status.yaml` (v3.68 → v3.69 EXTENSION)
5. MODIFIED: `memory/MEMORY.md` (Phase 22 spec entry hook EXTENSION)

### Wire sprint (cj 160, future) — estimated ~33 files = 21 NEW + 12 MODIFIED (Phase 21 wire `f7d1f41` 의 ~25 files pattern 의 5-NEW-module settlement layer version EXTENSION)
- Backend: 5 NEW modules (~+1,220 LOC) + 1 NEW serializers.py + 1 NEW __init__.py + 1 NEW alembic 0054 + 1 NEW scheduled_dispatch + 1 NEW scripts/cli (~+1,830 LOC)
- Frontend: 2 NEW RSC pages (~+320 LOC) + 1 NEW Client component (~+250 LOC) + 2 NEW TS mirrors (~+150 LOC)
- Tests: ~+78 NEW pytest PASS + ~+24 NEW vitest PASS
- MODIFIED: 6 files (capability.py + dependencies/capability.py + audit_action.py + errors.py + modules/finops/__init__.py + ko-KR.json = 6 MODIFIED + capability-matrix.md + capability_matrix_v1_48_drift test + audit_action_v1_48_drift test = 9 MODIFIED actually, but estimates vary)

(Actual wire sprint file count will be verified at wire time via `git show --stat HEAD`.)

## 3중 게이트 impact

- **cj 159 (this sprint, docs-only)**: ruff 0 NEW / pytest 0 NEW / vitest 0 NEW / tsc 0 NEW (apps/api backend unchanged, apps/web frontend unchanged)
- **cj 160 (wire sprint)**: ruff scoped 0 NEW / pytest ~+78 NEW PASS / vitest ~+24 NEW PASS / tsc 0 NEW
- **cj 161 (retro sprint, docs-only)**: ruff 0 NEW / pytest 0 NEW / vitest 0 NEW / tsc 0 NEW

## A624~A628 5 NEW 결정 wire (cj-style 159번째)

- **A624**: 옵션 (a) Phase 22 spec entry 진입 결정 wire (rationale 5종: ① cj-style discipline 회피 위험 방지 = 158번째 Phase 22 PRD entry 진입 직후 자연스러운 spec entry 진입 결정 wire ② Phase 22 PRD entry cj-style 158번째 진입 직후 자연스러운 spec entry 진입 = 159번째 진입 결정 wire ③ Phase 11~21 11-module FinOps territory chain ✅ ALL WIRED 진입 정합 보존 + Phase 17/18/19/20/21 5-module chain ✅ ALL WIRED ④ 5-NEW-module settlement layer = Phase 11+18+19+20+21 5 module ledger data 활용 → 새 backend infra 불필요 + reuse 최대화 + risk 최소화 + 비즈니스 가치 최고 ⑤ Epic 1 ~ Epic 17 + Phase 3 ~ Phase 21 + Phase 19.5 + Phase 20.5 + 1st release cycle 정합 보존)
- **A625**: spec 파일 생성 결정 wire (`_bmad-output/implementation-artifacts/phase-22-finops-chargeback-settlement-wire.md` ~+440 LOC + baseline_commit `64760fe` + cj_style_entry_point 159 + status `ready-for-dev` + Story + 8 ACs §F38.1~§F38.8 verbatim → ~88 detailed sub-ACs (10+6+8+7+8+6+3+10) pre-flight 정합 sweep 만족 + T1~T8 + ~42 subtasks + Dev Notes 19종 + Architecture Alignment ALLOWED sweep + Files Affected ~33 files estimate (~21 NEW + ~12 MODIFIED))
- **A626**: 8 ACs §F38.1~§F38.8 verbatim → ~88 sub-ACs 전개 결정 wire (§F38.1 settlement_rules engine + 5-module cross-join 10 sub-ACs + §F38.2 allocation_engine + 5-dim weighted 6 sub-ACs + §F38.3 invoice_generation + PDF/XLSX/CSV template 8 sub-ACs + §F38.4 reconciliation 3-way match 7 sub-ACs + §F38.5 chargeback_settlement dashboard UI 5 sub-components 8 sub-ACs + §F38.6 Capability matrix v1.48 EXTENSION 6 sub-ACs + §F38.7 audit action EXTENSION 8 NEW + 16 NEW typed exception classes 3 sub-ACs + §F38.8 dry-run + Tests + wire scope T1~T8 10 sub-ACs = ~88 sub-ACs pre-flight 정합 sweep 만족)
- **A627**: Tasks T1~T8 + ~42 subtasks 결정 wire (T1 5 NEW backend settlement modules 10 subtasks + T2 dashboard UI 5 sub-components 8 subtasks + T3 alembic 0054 9 tables 6 subtasks + T4 audit action EXTENSION 8 NEW + 16 NEW typed exception classes 4 subtasks + T5 capability v1.48 EXTENSION 4 subtasks + T6 scheduled_dispatch_job wire 2 subtasks + T7 dry-run mode + 1 NEW CLI flag 4 subtasks + T8 3중 게이트 FINAL CLEAN atomic commit 4 subtasks = ~42 subtasks)
- **A628**: sprint-status v3.68 → v3.69 EXTENSION + atomic commit via `git commit -F <file>` CR 9-6 D5 prevention + commit-msg-cj-159.txt 신규 + handoff memory 신규 + MEMORY.md hook EXTENSION + **5 files = 3 NEW + 2 MODIFIED atomic single sprint** 결정 wire (1 NEW spec file + 1 NEW handoff memory + 1 NEW commit-msg = 3 NEW; 1 MODIFIED sprint-status; 1 MODIFIED MEMORY.md) 진입 완료 보존.

## CR lessons applied 19종

CR 0-2 RLS 9 tables + CR 1-1 audit-first INSERT 8 NEW + CR 1-1 FastAPI ContextVar + CR 1-1 RSC boundary + CR 4-3/4-4 + CR 5-1 Decimal precision banker's rounding + CR 9-6 commit message `git commit -F <file>` + CR 11-3 honest-DEFER 50번째 D-FINOPS-11 honestly DEFER 보존 + Phase 11~21 11-module FinOps territory chain ✅ ALL WIRED 결정 wire + ALLOWED_SERVICE_SUBMODULES 즉시 sweep EXTENSION = m22_finops_chargeback_settlement 신규 submodule 등록 + CR 11-4 D-001~D-005 + P-015 SSOT + CR 12-1 L4 industry-agnostic capability matrix v1.48 FINOPS_CHARGEBACK_SETTLEMENT 4-industry grants ✅/✅/✅/✅ + CR 12-5 D-14 typed exception envelope 16 NEW + CR 12-5 D-PARITY-01 inversion TypeScript mirror parity finops_chargeback_settlement.* namespace + CR 12-5 D-GATE-01 inversion capability gate inversion require_finops_chargeback_settlement + A19 cohesion 9 surface EXTENSION PASS + A36 SDR 검증 4-step 자동 적용 + AD-14 stack pin Recharts 2.12.7 + reportlab 4.0.7 + xlsxwriter 3.1.9 + apscheduler 3.10.4 + pytz 2024.1 + noto-sans-cjk-kr + AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory + NFR4 PII minimization ✅ PRESERVED + AD-49 (a)~(g) 7 sub-decisions + AD-50 (a)~(g) 7 sub-decisions + NFR18 ko-KR SSOT

## D-DEFER-* honestly 결정 wire 보존

- D-1-1-DEFER-1/2/3 + D-EPIC-16-REVIEW-DEFER-1/2~6 + D-PHASE-4-DR-DEFER-1/2 + D-EPIC-17-WIRE-DEFER-T2-T3-UI + D-RETENTION-1 + D-OBSERVABILITY-1 + D-PERFORMANCE-1 + D-CHAOS-1 + D-SLO-1 + D-FINOPS-1~10 모두 ✅ ALL RESOLVED 보존
- **D-FINOPS-11 신규 honestly DEFER 보존** — Phase 22 PRD entry 진입 시점에 carry-over chain 정직 회복 결정 wire 진입 = 5-module cross-join backend detail + 5-dimension allocation weight detail + 3-format invoice template detail + 3-way match reconciliation algorithm detail + Epic 12 2FA 챌린지 high-value threshold detail + multi-currency settlement (KRW only) + tax compliance (10% VAT default) + settlement dispute workflow + settlement refund/credit note — 모두 단일 sprint `wire` 진입이 아닌 docs-only entry 에서 honestly defer 결정 wire 보존
- **Phase 22 spec entry = D-FINOPS-11 의 carry-over chain 정직 회복 verification** 결정 wire (CR 11-3 honest-DEFER 50번째 epic 연속 정직 회복)

## Epic 1~17 + Phase 3~21 + Phase 19.5 + Phase 20.5 + 1st release cycle 정합 보존

cj-style 159번째 epic 연속 정직 회복 진입 시점에 pre-flight 정합 sweep 만족 결정 wire 보존:
- Phase 22 PRD entry `64760fe` (cj-style 158번째) DONE 진입 정합 보존
- Phase 11~20 audit-fixes-infrastructure sprint `7b8e31b` (cj-style 157번째) DONE 진입 정합 보존
- Phase 11~20 audit-fixes Layer 3 P2 docs backfill sprint `21daea8` (cj-style 156번째) DONE 진입 정합 보존
- Phase 11~20 audit-fixes Layer 2 P1 test backfill sprint `4e1f0b3` (cj-style 155번째) DONE 진입 정합 보존
- Phase 11~20 audit-fixes sprint `379ca8e` (cj-style 154번째) DONE 진입 정합 보존
- Phase 21 audit-fixes sprint `f7d1f41` (cj-style 153번째) DONE 진입 정합 보존
- Phase 21 close-out retro `1b101bf` (cj-style 152번째) DONE 진입 정합 보존
- Phase 21 atomic wire `f7d1f41` (cj-style 151번째) DONE 진입 정합 보존
- Phase 21 spec entry (cj-style 149~150번째, baseline `563ac9c`) DONE 진입 정합 보존
- Phase 20.5 close-out retro `8505d98` (cj-style 148번째) DONE 진입 정합 보존
- Phase 20.5 atomic wire `46ddcc5` (cj-style 147번째) DONE 진입 정합 보존
- Phase 20.5 spec entry `e23141d` (cj-style 146번째) DONE 진입 정합 보존
- Phase 20 close-out retro `f361016` (cj-style 145번째) DONE 진입 정합 보존
- Phase 20 atomic wire `52dad7f` (cj-style 144번째) DONE 진입 정합 보존
- Phase 20 spec entry `efc3c59` (cj-style 143번째) DONE 진입 정합 보존
- Phase 20 PRD entry `eacb0a5` (cj-style 142번째) DONE 진입 정합 보존
- Phase 19.5 carry-over 결정 wire `b2fb1d8` (cj-style 141번째) DONE 진입 정합 보존
- Phase 19 close-out retro `18ca1ae` (cj-style 140번째) + Phase 19 atomic wire T1~T8 `8db3cfc` (cj-style 139번째) + Phase 19 spec entry `59d15fb` (cj-style 138번째) + Phase 19 PRD entry `ff8a797` (cj-style 137번째) DONE 진입 정합 보존
- Phase 11~21 11-module FinOps territory chain ✅ ALL WIRED 진입 정합 보존 + Phase 17/18/19/20/21 5-module chain ✅ ALL WIRED 진입 정합 보존
- Epic 1~17 ALL DONE 진입 정합 보존
- 1st release cycle ALL DONE 진입 정합 보존

## 결정 wire 일자 + next

- 결정 wire 일자: 2026-08-27 (KST)
- next 옵션:
  - (a) Phase 22 atomic wire T1~T8 진입 결정 wire (cj-style 160번째) — 5 NEW backend settlement modules + 5 NEW dashboard sub-components + alembic 0054 9 tables + audit action 8 NEW + 16 NEW typed exceptions + capability v1.48 + scheduled dispatch + dry-run + 1 CLI flag = ~33 files atomic single sprint
  - (b) Phase 22 close-out retro 진입 결정 wire (cj-style 161번째) — 14-section §1~§14 verbatim retro document
  - (c) Epic 22+ 진입 결정 wire
  - (d) D-DEFER-* follow-up 결정 wire 보류