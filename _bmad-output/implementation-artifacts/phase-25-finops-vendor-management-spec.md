---
baseline_commit: 5e8d435
status: ready-for-dev
cj_style_entry_point: 172
story_key: phase-25-finops-vendor-management-spec
---

# Phase 25 FinOps Vendor Management spec (cj-style 172번째 epic 연속 정직 회복)

## Story

**As a** FinOps practitioner / cloud architect / tenant admin / 1st release customer / DevOps engineer
**I want** Phase 25 territory 결정 wire (FinOps Vendor Management = **vendor_catalog engine + 6 vendor_category taxonomy (cloud/saas/outsourcing/consulting/hardware/other) EXTENSION + vendor_selection + 5-dim weighted scoring (cost 0.30 + performance 0.25 + reliability 0.20 + compliance 0.15 + strategic_fit 0.10) + vendor_contract_lifecycle sequential (draft → pending_approval → approved → active → expiring_soon → renewed/expired/terminated) + Epic 12 2FA 챌린지 ≥ 10M KRW/year mandatory + tenant_owner approval chain + vendor_performance_evaluation monthly + quarterly cadence (sla_compliance 0.30 + cost_efficiency 0.25 + support_quality 0.25 + innovation 0.20)** + **vendor_management dashboard UI 5 NEW sub-components (VendorCatalogOverviewCard + VendorSelectionScorePanel + VendorContractLifecycleTimeline + VendorPerformanceScorecardTable + VendorSpendAttributionChart)** + **Capability matrix v1.51 EXTENSION FINOPS_VENDOR_MANAGEMENT** + **audit action EXTENSION 12 NEW Literal + 16 NEW typed exception classes** + **dry-run mode + 1 NEW CLI flag + Tests + wire scope T1~T8**) 결정 wire
**so that** Phase 11~24 16-capability FinOps territory chain ✅ ALL WIRED 진입 정합 보존 후 Phase 25 PRD entry `5e8d435` (cj-style 171번째) 진입 직후 spec entry 진입 = cj-style 4-entry-point cycle PRD entry → spec entry → wire → close-out retro 의 2번째 단계 진입 결정 wire (Phase 17 spec entry cj-style 130번째 + Phase 18 spec entry cj-style 134번째 + Phase 19 spec entry cj-style 138번째 + Phase 20 spec entry cj-style 143번째 + Phase 21 spec entry cj-style 150번째 + Phase 22 spec entry cj-style 159번째 + Phase 23 spec entry cj-style 163번째 + Phase 24 spec entry cj-style 168번째 패턴 verbatim 미러) + Phase 25 territory = 5 NEW backend modules (vendor_catalog_engine + vendor_selection_engine + vendor_contract_lifecycle_engine + vendor_performance_evaluation + vendor_spend_attribution) 의 **post-budget-allocation layer** = Phase 14 optimization recommendations + Phase 18 commitment data + Phase 19 pricing rate cards + Phase 22 settlement_results + Phase 23 unit_economics_results + Phase 24 budget_plan ledger data 활용 → forward-looking vendor selection + contract lifecycle + performance evaluation + spend attribution = 비용 직접 통제 layer 직접적 ROI 결정 wire + Phase 14 + Phase 18 + Phase 19 + Phase 22 + Phase 23 + Phase 24 ledger data 활용 → 새 backend infra 불필요 + reuse 최대화 + risk 최소화 + 비즈니스 가치 최고 + Epic 12 2FA 챌린지 mandatory ≥ 10M KRW/year + AD-22 owner-only RBAC + NFR4 PII minimization ✅ PRESERVED + NFR18 ko-KR SSOT + AD-53 신규 (a)~(g) 7 sub-decisions 모두 결정 wire 진입 + D-FINOPS-14 신규 honestly DEFER 보존 + CR 11-3 honest-DEFER 63번째 epic 연속 정직 회복 verification 결정 wire 진입 + 3중 게이트 impact NONE (docs only 변경 = cj-style 172번째 wire 진입 표준 = docs only sprint) 결정 wire.

## Context

cj-style Phase 25 1번째 진입점 (cj-style 171번째) 진입 결정 wire 진입 완료:

- Phase 25 PRD entry `5e8d435` (cj-style 171번째) DONE 진입 정합 보존
- Phase 24 close-out retro retroactive correction `1f30b64` (cj-style 170 follow-up) DONE 진입 정합 보존
- Phase 24 close-out retro `c14199b` (cj-style 170번째) DONE 진입 정합 보존
- Phase 24 wire retroactive correction `69c5e28` (cj-style 169 follow-up) DONE 진입 정합 보존
- Phase 24 wire `615d478` (cj-style 169번째) DONE 진입 정합 보존
- Phase 24 spec entry `b3c6c7c` (cj-style 168번째) DONE 진입 정합 보존
- Phase 24 PRD entry `278f37f` (cj-style 167번째) DONE 진입 정합 보존
- audit-fixes sprint entry `a4ae56d` (cj-style 166번째) DONE 진입 정합 보존
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
- Phase 11~20 audit-fixes-infrastructure sprint `7b8e31b` (cj-style 157번째) DONE 진입 정합 보존
- Phase 11~20 audit-fixes Layer 3 P2 docs backfill sprint `21daea8` (cj-style 156번째) DONE 진입 정합 보존
- Phase 11~20 audit-fixes Layer 2 P1 test backfill sprint `4e1f0b3` (cj-style 155번째) DONE 진입 정합 보존
- Phase 11~20 audit-fixes sprint `379ca8e` (cj-style 154번째) DONE 진입 정합 보존
- Phase 21 audit-fixes sprint `f7d1f41` (cj-style 153번째) DONE 진입 정합 보존
- Phase 21 close-out retro `1b101bf` (cj-style 152번째) DONE 진입 정합 보존
- Phase 21 atomic wire `f7d1f41` (cj-style 151번째) DONE 진입 정합 보존
- Phase 21 spec entry `47545d6` (cj-style 150번째) DONE 진입 정합 보존
- Phase 21 PRD entry `563ac9c` (cj-style 149번째) DONE 진입 정합 보존
- Phase 20.5 close-out retro `8505d98` (cj-style 148번째) DONE 진입 정합 보존
- Phase 20.5 atomic wire `46ddcc5` (cj-style 147번째) DONE 진입 정합 보존
- Phase 20.5 spec entry `e23141d` (cj-style 146번째) DONE 진입 정합 보존
- Phase 20 close-out retro `f361016` (cj-style 145번째) DONE 진입 정합 보존
- Phase 20 atomic wire `52dad7f` (cj-style 144번째) DONE 진입 정합 보존
- Phase 20 spec entry `efc3c59` (cj-style 143번째) DONE 진입 정합 보존
- Phase 20 PRD entry `eacb0a5` (cj-style 142번째) DONE 진입 정합 보존
- Phase 19.5 carry-over 결정 wire `b2fb1d8` (cj-style 141번째) DONE 진입 정합 보존
- Phase 19 close-out retro `18ca1ae` (cj-style 140번째) + Phase 19 atomic wire `8db3cfc` (cj-style 139번째) + Phase 19 spec entry `59d15fb` (cj-style 138번째) + Phase 19 PRD entry `ff8a797` (cj-style 137번째) + Phase 18 close-out retro `de72f50` (cj-style 136번째) + Phase 18 atomic wire `67059cf` (cj-style 135번째) + Phase 18 spec entry `bdc7997` (cj-style 134번째) + Phase 18 PRD entry `5eded22` (cj-style 133번째) + Phase 17 close-out retro `de009fe` (cj-style 132번째) + Phase 17 atomic wire `97cfe4e` (cj-style 131번째) + Phase 17 spec entry `4be3120` (cj-style 130번째) + Phase 17 PRD entry `e0778ed` (cj-style 129번째) + Phase 16 close-out retro `26fd530` (cj-style 128번째) + Phase 16 atomic wire `81ae00a` (cj-style 127번째) + Phase 16 spec entry `69c29df` (cj-style 126번째) + Phase 16 PRD entry `4f11d03` (cj-style 125번째) + Phase 15 close-out retro `102f370` (cj-style 124번째) + Phase 15 atomic wire `1b800d9` (cj-style 123번째) + Phase 15 spec entry `69c29df` (cj-style 122번째) + Phase 15 PRD entry `87393b4` (cj-style 121번째) + ... + Epic 1~17 ALL DONE 진입 정합 보존 + 1st release cycle ALL DONE 진입 정합 보존

### Phase 25 PRD entry `5e8d435` 의 8 ACs §F41.1~§F41.8 verbatim 보존

8 ACs §F41.1~§F41.8 → 48 explicit sub-ACs + nested bullet points → **~88 detailed sub-ACs** (5+5+5+8+6+4+10) pre-flight 정합 sweep 만족 결정 wire:

1. **§F41.1 vendor_catalog engine + 6 vendor_category taxonomy** — `vendor_management/` 1 NEW module 결정 wire + serializers.py (`Vendor` TypedDict 18 fields + `VendorStatus` enum 4 values active/inactive/under_review/blacklisted + `VendorCategory` enum 6 values cloud/saas/outsourcing/consulting/hardware/other + `VENDOR_SELECTION_DIMENSION_WEIGHTS` constants {cost: 0.30, performance: 0.25, reliability: 0.20, compliance: 0.15, strategic_fit: 0.10} + `VENDOR_PERFORMANCE_DIMENSION_WEIGHTS` constants {sla_compliance: 0.30, cost_efficiency: 0.25, support_quality: 0.25, innovation: 0.20} + `VENDOR_CADENCE_HOURS_KST` + `VENDOR_RECIPIENT_TEMPLATES` + `VENDOR_DEFAULTS` + `VENDOR_BLACKLIST_GATE_FLAGS`) + `vendor_catalog_engine.py` (CRUD + 6 vendor_category taxonomy + 4-state lifecycle active → under_review → inactive/blacklisted + 일 1회 KST cron 04:00 + audit-first INSERT `vendor_created` + `vendor_updated` + `vendor_status_changed` + `vendor_blacklisted` CR 1-1 verbatim EXTENSION) + `__init__.py` (module tag m25_finops_vendor_management + comprehensive re-exports) (5 sub-ACs §F41.1.1~§F41.1.5)
2. **§F41.2 vendor_selection + 5-dim weighted scoring** — `VendorSelectionScore` per-dimension score (cost/performance/reliability/compliance/strategic_fit NUMERIC(5,2) range 0.00~100.00) + weighted_total_score (0.00~100.00) + per-tenant override `tenant_settings.vendor_selection_overrides.dimension_weights` > industry baseline > system default precedence + total verification ±0.01 KRW tolerance (CR 5-1 Decimal precision banker's rounding verbatim) + 3 auto-retries + admin email alert + selection_threshold default 60.00 → below threshold 자동 excluded + selection_candidate_limit default 10 (top-N) + score version <= 100.00 strict range + audit-first INSERT `vendor_selection_executed` CR 1-1 verbatim EXTENSION (5 sub-ACs §F41.2.1~§F41.2.5)
3. **§F41.3 vendor_contract_lifecycle sequential + Epic 12 2FA 챌린지** — sequential contract lifecycle (draft → pending_approval → approved → active → expiring_soon → renewed/expired/terminated) + step_index ordering + Epic 12 2FA 챌린지 mandatory ≥ 10M KRW/year (RFC 6238 TOTP) + tenant_owner approval chain (Slack DM + 2FA + approval_chain) + high-value contract ≥ 10M KRW/year → `/account/security?reason=2fa_required` redirect + computed_total_contract_value within budget ceiling auto-approved, over budget ceiling requires Epic 12 2FA 챌린지 mandatory + auto-renewal 90-day window (Phase 24 budget_plan auto-rollover cadence pattern verbatim EXTENSION) + vendor_blacklist compliance gate + audit-first INSERT `vendor_contract_approved` + `vendor_contract_renewed` + `vendor_contract_terminated` + `vendor_risk_flagged` + `vendor_compliance_violation_detected` CR 1-1 verbatim EXTENSION (5 sub-ACs §F41.3.1~§F41.3.5)
4. **§F41.4 vendor_performance_evaluation + dashboard UI 5 NEW sub-components** — `VendorCatalogOverviewCard` (vendor list + CRUD + filter by category) + `VendorSelectionScorePanel` (5-dim Recharts radar chart) + `VendorContractLifecycleTimeline` (contract timeline + renewal alerts) + `VendorPerformanceScorecardTable` (TanStack Table monthly + quarterly scores) + `VendorSpendAttributionChart` (Recharts stacked bar chart: vendor vs budget vs actual) + 2 NEW TS mirrors (vendor-management-types.ts + vendor-management-client.ts) + 2 NEW RSC pages (`/admin/finops/vendor-management/page.tsx` + `layout.tsx`) + ko-KR.json EXTENSION ~35 keys (NFR18 SSOT) (8 sub-ACs §F41.4.1~§F41.4.8)
5. **§F41.5 Capability matrix v1.51 EXTENSION FINOPS_VENDOR_MANAGEMENT** — `Capability.FINOPS_VENDOR_MANAGEMENT` 1 NEW enum + `require_finops_vendor_management` 1 NEW dep + `Role.VENDOR_MANAGEMENT_OPERATOR` + `Role.VENDOR_MANAGEMENT_VIEWER` 2 NEW enum + 4-industry grants ✅/✅/✅/✅ + test_audit_action_v1_51_drift.py + capability gate fail-closed (6 sub-ACs §F41.5.1~§F41.5.6)
6. **§F41.6 audit action EXTENSION 12 NEW Literal + 16 NEW typed exception classes** — `ActionClass.FINOPS_VENDOR_MANAGEMENT` + `FinopsVendorManagementAction` 12 NEW Literal (vendor_created + vendor_updated + vendor_status_changed + vendor_blacklisted + vendor_selection_executed + vendor_contract_approved + vendor_contract_renewed + vendor_contract_terminated + vendor_performance_evaluated + vendor_spend_attributed + vendor_risk_flagged + vendor_dry_run_executed) + `_ActionRegistry._REGISTRY` 1 NEW entry + `AuditAction` Union EXTENSION + 16 NEW typed exceptions CR 12-5 D-14 envelope (VendorNotFoundError 404 + VendorBlacklistError 403 + VendorStatusTransitionError 409 + VendorComplianceViolationError 403 + VendorSelectionScoreError 500 + VendorPerformanceEvaluationError 500 + VendorSpendAttributionError 500 + Vendor2FARequiredError 403 + VendorContractNotFoundError 404 + VendorContractExpiredError 410 + VendorContractTerminationError 409 + VendorContractRenewalError 500 + VendorRiskScoreError 500 + VendorCatalogSyncError 500 + VendorBenchmarkError 500 + VendorPerformanceSLAError 500) + Cache-Control no-store (4 sub-ACs §F41.6.1~§F41.6.4)
7. **§F41.7 vendor_spend_attribution + cross-budget reconciliation** — `VendorSpendAttribution` per-vendor amount (NUMERIC(18,2)) + Phase 22 settlement_results.total_settlement_amount + Phase 24 budget_plan.total_budget_amount + cross-budget reconciliation (Phase 24 over_budget alert chain EXTENSION) + monthly cadence 1st of month 03:00 KST (Phase 24 budget_alert cadence verbatim EXTENSION) + audit-first INSERT `vendor_spend_attributed` CR 1-1 verbatim EXTENSION (5 sub-ACs §F41.7.1~§F41.7.5)
8. **§F41.8 dry-run + Tests + wire scope T1~T8** — `--finops-vendor-management-dry-run` 1 NEW CLI flag + phase_25_vendor_management_preview 1 table + ~+82 NEW pytest + ~+28 NEW vitest + 0 NEW ruff + 0 NEW tsc + 0 regressions + wire scope T1~T8 (10 sub-ACs §F41.8.1~§F41.8.10)

**Total sub-ACs**: 5+5+5+8+6+4+5+10 = **48 explicit sub-ACs** with nested bullet points → **~88 detailed sub-ACs** pre-flight 정합 sweep 만족 결정 wire (cj-style 171 commit message 의 ~88 sub-ACs verbatim mirror).

### AD-53 신규 결정 (a)~(g) 7 sub-decisions (Phase 25 PRD entry 진입 시점에 결정 wire 진입 완료)

- (a) vendor_catalog engine 의 CRUD + lifecycle backend detail (Phase 14 + Phase 18 + Phase 19 ledger data 활용 + 6 vendor_category taxonomy cloud/saas/outsourcing/consulting/hardware/other + 4-state lifecycle active/inactive/under_review/blacklisted + 일 1회 KST cron 04:00 + pure function computation + dry-run mode + industry-agnostic 4-industry grants)
- (b) vendor_selection 의 5-dim weighted scoring detail (cost: 0.30 + performance: 0.25 + reliability: 0.20 + compliance: 0.15 + strategic_fit: 0.10 + per-tenant override > industry baseline > system default precedence + ±0.01 KRW total verification + 3 auto-retries + admin email alert + selection_threshold default 60.00 + score version <= 100.00 strict range)
- (c) vendor_contract_lifecycle sequential detail (step_index ordering + draft → pending_approval → approved → active → expiring_soon → renewed/expired/terminated + Epic 12 2FA 챌린지 mandatory ≥ 10M KRW/year RFC 6238 TOTP + tenant_owner approval_chain + Slack DM notification + auto-renewal 90-day window + over-budget cross-check + vendor_blacklist compliance gate + 16 NEW typed exceptions CR 12-5 D-14 envelope)
- (d) vendor_performance_evaluation + dashboard UI 5 sub-components detail (VendorCatalogOverviewCard + VendorSelectionScorePanel + VendorContractLifecycleTimeline + VendorPerformanceScorecardTable + VendorSpendAttributionChart + Recharts 2.12.7 AD-14 stack pin + TanStack Table + owner-only RBAC AD-22 + ko-KR.json `finops_vendor_management.*` namespace ~35 NEW keys + 2 NEW TS mirrors + 4-dim scoring sla_compliance 0.30 + cost_efficiency 0.25 + support_quality 0.25 + innovation 0.20 + monthly 1st 03:00 KST + quarterly 1st 03:30 KST cadence)
- (e) NFR4 PII minimization preservation detail (no employee names + actor_id UUID + tenant_id UUID + monetary amounts only + score metrics only + Cache-Control no-store)
- (f) NFR18 ko-KR SSOT detail (finops_vendor_management.* namespace EXTENSION ~35 keys + Korean font noto-sans-cjk-kr + Korean error messages + English audit action names)
- (g) Epic 12 2FA 챌린지 mandatory high-value detail (vendor contract approval ≥ 10M KRW/year → RFC 6238 TOTP + tenant_owner approval chain + Vendor2FARequiredError(403) + vendor_blacklist action → Epic 12 2FA 챌린지 mandatory + 2FA 미설정 tenant 의 경우 `/account/security?reason=2fa_required` redirect)

### D-FINOPS-14 신규 honestly DEFER 보존

Phase 25 PRD entry 진입 시점에 carry-over chain 정직 회복 결정 wire 진입 = vendor_catalog 6 vendor_category CRUD + lifecycle detail + vendor_selection 5-dim weighted scoring backend detail + vendor_contract_lifecycle sequential + Epic 12 2FA 챌린지 high-value threshold detail + vendor_performance_evaluation monthly + quarterly cadence detail + vendor_spend_attribution cross-budget reconciliation + vendor_blacklist compliance gate + vendor marketplace integration (external AWS/Azure/GCP marketplace) + vendor auto-procurement (auto PO generation) + vendor consolidation analytics (multi-vendor → single-vendor) + vendor ESG scorecard (environmental + social + governance) + vendor AI-driven RFP generation + vendor SLA auto-inforcement + multi-currency vendor contract FX conversion USD/EUR/JPY + vendor invoice reconciliation (OCR + line-item matching) + vendor onboarding KYC automated + vendor risk scoring ML prediction — 모두 단일 sprint `wire` 진입이 아닌 docs-only entry 에서 honestly defer 결정 wire 보존 (Phase 17 close-out retro `be8f3bd` §11 "FinOps Reserved Capacity Planning 결정 wire 보류, Phase 21+ 진입 시점" verbatim 해소 + Phase 21 close-out retro `1b101bf` + Phase 22 close-out retro `c5726ff` §11 의 honest deviation 보존 패턴 verbatim 미러 + Phase 23 close-out retro `7875ac9` §11 + Phase 24 close-out retro `c14199b` §10 의 honest deviation 보존 패턴 verbatim 미러).

## T1~T8 + ~42 subtasks

### T1: Phase 25 5 NEW backend vendor_management modules (8 subtasks)
- T1.1: `apps/api/modules/finops/vendor_management/__init__.py` NEW + ALLOWED_SERVICE_SUBMODULES EXTENSION m25_finops_vendor_management 신규 submodule 등록 결정 wire (Phase 22 m22_finops_chargeback_settlement + Phase 23 m23_finops_unit_economics + Phase 24 m24_finops_budget_planning 패턴 보존)
- T1.2: `apps/api/modules/finops/vendor_management/serializers.py` NEW ~+320 LOC + 3 NEW enums (VendorStatus 4 values active/inactive/under_review/blacklisted + VendorCategory 6 values cloud/saas/outsourcing/consulting/hardware/other + VendorContractLifecycle 7 values draft/pending_approval/approved/active/expiring_soon/renewed/expired/terminated) + 6 NEW TypedDicts (Vendor 18 fields + VendorSelectionScore 12 fields + VendorContract 16 fields + VendorPerformanceScorecard 14 fields + VendorSpendAttribution 12 fields + VendorBlacklistEntry 10 fields) + VENDOR_SELECTION_DIMENSION_WEIGHTS + VENDOR_PERFORMANCE_DIMENSION_WEIGHTS + VENDOR_CADENCE_HOURS_KST + VENDOR_RECIPIENT_TEMPLATES + VENDOR_DEFAULTS + VENDOR_BLACKLIST_GATE_FLAGS 결정 wire
- T1.3: `apps/api/modules/finops/vendor_management/vendor_catalog_engine.py` NEW ~+340 LOC + create_vendor(tenant_id, vendor_name, vendor_category) → Vendor + read_vendor(tenant_id, vendor_id) → Vendor + update_vendor(tenant_id, vendor_id, ...) → Vendor + delete_vendor(tenant_id, vendor_id, reason) → bool + list_vendors(tenant_id, filter) → Vendor list + 6 vendor_category taxonomy cloud/saas/outsourcing/consulting/hardware/other + 4-state lifecycle active → under_review → inactive/blacklisted + 일 1회 KST cron 04:00 (scheduled_vendor_lifecycle_job) + Decimal precision (banker's rounding CR 5-1 verbatim) + audit-first INSERT `vendor_created` + `vendor_updated` + `vendor_status_changed` + `vendor_blacklisted` CR 1-1 verbatim EXTENSION 결정 wire
- T1.4: `apps/api/modules/finops/vendor_management/vendor_selection_engine.py` NEW ~+300 LOC + execute_vendor_selection(tenant_id, vendor_category, scope) → list[VendorSelectionScore] + 5-dim weighted scoring (cost 0.30 + performance 0.25 + reliability 0.20 + compliance 0.15 + strategic_fit 0.10) + per-tenant override > industry baseline > system default precedence + total verification ±0.01 KRW tolerance + 3 auto-retries + admin email alert + selection_threshold default 60.00 → below threshold 자동 excluded + selection_candidate_limit default 10 (top-N) + score version <= 100.00 strict range + audit-first INSERT `vendor_selection_executed` CR 1-1 verbatim EXTENSION 결정 wire
- T1.5: `apps/api/modules/finops/vendor_management/vendor_contract_lifecycle_engine.py` NEW ~+360 LOC + create_contract(tenant_id, vendor_id, contract_terms) → VendorContract + submit_contract_for_approval(tenant_id, contract_id) → sequential contract lifecycle + step_index ordering + 4-state step status (pending/approved/rejected/skipped) + Epic 12 2FA 챌린지 mandatory ≥ 10M KRW/year (RFC 6238 TOTP) + tenant_owner approval_chain (Slack DM + 2FA + approval_chain) + computed_total_contract_value within budget ceiling auto-approved + over budget ceiling requires Epic 12 2FA 챌린지 mandatory + auto-renewal 90-day window (Phase 24 budget_plan auto-rollover cadence pattern verbatim EXTENSION) + high-value contract ≥ 10M KRW/year → `/account/security?reason=2fa_required` redirect + rejection rolls contract back to draft + audit log + audit-first INSERT `vendor_contract_approved` + `vendor_contract_renewed` + `vendor_contract_terminated` CR 1-1 verbatim EXTENSION 결정 wire
- T1.6: `apps/api/modules/finops/vendor_management/vendor_performance_evaluation.py` NEW ~+280 LOC + evaluate_vendor_performance(tenant_id, vendor_id, period_key) → VendorPerformanceScorecard + 4-dim scoring (sla_compliance 0.30 + cost_efficiency 0.25 + support_quality 0.25 + innovation 0.20) + Phase 11 chargeback data + Phase 18 commitment utilization + Phase 22 settlement_results + Phase 24 budget_vs_actual variance 활용 → per-vendor score_card + monthly cadence (1st of month 03:00 KST) + quarterly cadence (1st of quarter 03:30 KST) + on-demand manual trigger + audit-first INSERT `vendor_performance_evaluated` + `vendor_risk_flagged` CR 1-1 verbatim EXTENSION 결정 wire
- T1.7: `apps/api/modules/finops/vendor_management/vendor_spend_attribution.py` NEW ~+280 LOC + compute_vendor_spend_attribution(tenant_id, vendor_id, period_key) → VendorSpendAttribution + Phase 22 settlement_results.total_settlement_amount (actuals) + Phase 24 budget_plan.total_budget_amount (budget) JOIN on (tenant_id, vendor_id, period_key) + cross-budget reconciliation (Phase 24 over_budget alert chain EXTENSION) + monthly cadence (1st of month 03:00 KST) + audit-first INSERT `vendor_spend_attributed` + `vendor_compliance_violation_detected` CR 1-1 verbatim EXTENSION 결정 wire
- T1.8: `apps/api/modules/finops/vendor_management/scheduled_vendor_management_jobs.py` NEW ~+200 LOC + apscheduler==3.10.4 + pytz==2024.1 EXTENSION + 일 1회 KST cron 04:00 (scheduled_vendor_lifecycle_job) + 1st of month 03:00 KST (scheduled_vendor_performance_evaluation_job) + 1st of quarter 03:30 KST (scheduled_vendor_quarterly_review_job) + 1st of month 03:15 KST (scheduled_vendor_spend_attribution_job) + LISTEN/NOTIFY 12 channel (phase_25_vendor_created + phase_25_vendor_updated + phase_25_vendor_status_changed + phase_25_vendor_blacklisted + phase_25_vendor_selection_executed + phase_25_vendor_contract_approved + phase_25_vendor_contract_renewed + phase_25_vendor_contract_terminated + phase_25_vendor_performance_evaluated + phase_25_vendor_spend_attributed + phase_25_vendor_risk_flagged + phase_25_vendor_dry_run_executed) + Phase 24 wire `615d478` 의 scheduled pattern verbatim EXTENSION 결정 wire

### T2: vendor_management dashboard UI 5 sub-components (8 subtasks)
- T2.1: `apps/web/app/[locale]/(dashboard)/admin/finops/vendor-management/page.tsx` NEW ~+240 LOC + 5 sub-components (VendorCatalogOverviewCard + VendorSelectionScorePanel + VendorContractLifecycleTimeline + VendorPerformanceScorecardTable + VendorSpendAttributionChart) EXTENSION 결정 wire
- T2.2: `apps/web/app/[locale]/(dashboard)/admin/finops/vendor-management/layout.tsx` NEW ~+110 LOC + owner-only RBAC AD-22 verbatim + Epic 12 2FA 챌린지 mandatory + ko-KR.json `finops_vendor_management.*` namespace EXTENSION ~35 keys (CR 11-4 D-002 verbatim SSOT) + ARIA labels WCAG 2.1 AA + `(dashboard)` route group 보호 EXTENSION 결정 wire
- T2.3: `apps/web/components/finops/FinopsVendorManagementDashboardPanel.tsx` NEW Client component ~+300 LOC + 5-tab layout + Recharts radar chart (selection score) + TanStack Table (performance scorecard) + Recharts stacked bar (spend attribution) + Recharts timeline (contract lifecycle) 결정 wire
- T2.4: `apps/web/lib/finops/vendor-management-types.ts` NEW TypeScript mirror + 6 NEW TypeScript interfaces (Vendor + VendorSelectionScore + VendorContract + VendorPerformanceScorecard + VendorSpendAttribution + VendorBlacklistEntry) CR 12-5 D-PARITY-01 inversion EXTENSION 결정 wire
- T2.5: `apps/web/lib/finops/vendor-management-client.ts` NEW TypeScript client + 9 NEW methods (createVendor + updateVendor + executeVendorSelection + createContract + submitContractForApproval + evaluateVendorPerformance + computeVendorSpendAttribution + runDryRun + healthcheck) EXTENSION 결정 wire
- T2.6: `apps/web/messages/ko-KR.json` MODIFIED EXTENSION ~35 keys + `finops_vendor_management.*` namespace EXTENSION + ARIA labels WCAG 2.1 AA + NFR18 ko-KR SSOT 보존 결정 wire
- T2.7: vendor_management dashboard Recharts 2.12.7 AD-14 stack pin EXTENSION + TanStack Table v8 AD-14 stack pin EXTENSION + 5 NEW charts (radar + table + stacked bar + timeline + overview card) + 4 industries baseline visualization 차이 EXTENSION 결정 wire
- T2.8: vendor_management dashboard dry-run mode UI (VendorCatalogOverviewCard 진입 시 dry-run toggle default: dry-run) + scheduled lifecycle KST cron 04:00 UI + AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory 결정 wire

### T3: alembic 0057 phase_25_vendor_management 1 preview table + RLS (6 subtasks)
- T3.1: `apps/api/alembic/versions/0057_phase_25_vendor_management.py` NEW **1 NEW preview table ONLY** 결정 wire (no new domain tables — derived from Phase 14 + Phase 18 + Phase 19 + Phase 22 + Phase 23 + Phase 24 ledger data) = phase_25_vendor_management_preview EXTENSION
- T3.2: phase_25_vendor_management_preview 1 NEW preview table 결정 wire + preview_id UUID PK + tenant_id UUID + vendor_id UUID + vendor_category TEXT + vendor_management_data JSONB + computed_at TIMESTAMPTZ DEFAULT NOW() + trace_id TEXT EXTENSION
- T3.3: RLS 자동 적용 CR 0-2 verbatim 결정 wire = 1 preview table tenant_id = current_setting('app.tenant_id')::uuid EXTENSION
- T3.4: CHECK + UNIQUE + indexes EXTENSION 결정 wire = idempotency_key UNIQUE + vendor_category enum CHECK + 6 vendor_category source attribution JSONB GIN index + vendor_id + period_key composite index EXTENSION
- T3.5: alembic 0057 down_revision 결정 wire = 0056 (Phase 24 wire `615d478` 의 alembic 0056 EXTENSION) EXTENSION
- T3.6: alembic upgrade + downgrade 검증 결정 wire + Phase 24 wire 의 alembic 0056 pattern verbatim EXTENSION

### T4: audit action EXTENSION 12 NEW Literal + 16 NEW typed exception classes (4 subtasks)
- T4.1: `apps/api/core/audit_action.py` MODIFIED EXTENSION 결정 wire + ActionClass.FINOPS_VENDOR_MANAGEMENT 1 NEW enum EXTENSION + _ActionRegistry._REGISTRY 1 NEW entry EXTENSION + AuditAction Union EXTENSION 결정 wire
- T4.2: `apps/api/core/audit_action.py` MODIFIED EXTENSION + FinopsVendorManagementAction 12 NEW Literal EXTENSION (vendor_created + vendor_updated + vendor_status_changed + vendor_blacklisted + vendor_selection_executed + vendor_contract_approved + vendor_contract_renewed + vendor_contract_terminated + vendor_performance_evaluated + vendor_spend_attributed + vendor_risk_flagged + vendor_dry_run_executed)
- T4.3: `apps/api/core/errors.py` MODIFIED EXTENSION 16 NEW typed exception classes CR 12-5 D-14 envelope 결정 wire = FinopsVendorManagementError base class + VendorNotFoundError(404) + VendorBlacklistError(403) + VendorStatusTransitionError(409) + VendorComplianceViolationError(403) + VendorSelectionScoreError(500) + VendorPerformanceEvaluationError(500) + VendorSpendAttributionError(500) + Vendor2FARequiredError(403) + VendorContractNotFoundError(404) + VendorContractExpiredError(410) + VendorContractTerminationError(409) + VendorContractRenewalError(500) + VendorRiskScoreError(500) + VendorCatalogSyncError(500) + VendorBenchmarkError(500) + VendorPerformanceSLAError(500) EXTENSION
- T4.4: 12 NEW audit actions via emit_audit_typed CR 1-1 verbatim EXTENSION 결정 wire + Phase 24 wire `615d478` 의 8 NEW audit actions pattern verbatim EXTENSION + 6 vendor_category source attribution JSONB payload EXTENSION

### T5: Capability matrix v1.51 EXTENSION FINOPS_VENDOR_MANAGEMENT (4 subtasks)
- T5.1: `docs/capability-matrix.md` MODIFIED v1.50 → v1.51 EXTENSION 결정 wire + FINOPS_VENDOR_MANAGEMENT 1 NEW row after FINOPS_BUDGET_PLANNING industry-agnostic 4-industry grants ✅/✅/✅/✅ CR 12-1 L4 precedent verbatim EXTENSION
- T5.2: `apps/api/core/capability.py` MODIFIED EXTENSION + Capability.FINOPS_VENDOR_MANAGEMENT 1 NEW enum 결정 wire
- T5.3: `apps/api/dependencies/capability.py` MODIFIED EXTENSION + require_finops_vendor_management 1 NEW dep 결정 wire + Role.VENDOR_MANAGEMENT_OPERATOR + Role.VENDOR_MANAGEMENT_VIEWER 2 NEW enum EXTENSION + fail-closed 403 Forbidden EXTENSION
- T5.4: `apps/api/modules/finops/__init__.py` MODIFIED EXTENSION + vendor_management submodule export + ALLOWED_SERVICE_SUBMODULES 즉시 sweep EXTENSION = m25_finops_vendor_management 신규 submodule 등록 (Phase 22 m22_finops_chargeback_settlement + Phase 23 m23_finops_unit_economics + Phase 24 m24_finops_budget_planning 패턴 보존) + Phase 11~24 verbatim EXTENSION

### T6: scheduled_vendor_management_jobs wire (2 subtasks)
- T6.1: `apps/api/modules/finops/vendor_management/scheduled_vendor_management_jobs.py` NEW ~+200 LOC + apscheduler==3.10.4 + pytz==2024.1 EXTENSION + 4 cadences (일 1회 KST cron 04:00 scheduled_vendor_lifecycle_job + 1st of month 03:00 KST scheduled_vendor_performance_evaluation_job + 1st of quarter 03:30 KST scheduled_vendor_quarterly_review_job + 1st of month 03:15 KST scheduled_vendor_spend_attribution_job) + LISTEN/NOTIFY 12 channel + recipient resolver Slack + Email + S3 archive 결정 wire
- T6.2: LISTEN/NOTIFY consume trigger EXTENSION 결정 wire = 12 NEW channel (phase_25_vendor_created + phase_25_vendor_updated + phase_25_vendor_status_changed + phase_25_vendor_blacklisted + phase_25_vendor_selection_executed + phase_25_vendor_contract_approved + phase_25_vendor_contract_renewed + phase_25_vendor_contract_terminated + phase_25_vendor_performance_evaluated + phase_25_vendor_spend_attributed + phase_25_vendor_risk_flagged + phase_25_vendor_dry_run_executed) + Phase 24 wire `615d478` LISTEN/NOTIFY pattern verbatim EXTENSION 결정 wire

### T7: dry-run mode + 1 NEW CLI flag (4 subtasks)
- T7.1: dry-run mode EXTENSION 결정 wire = dry-run 시 actual `vendor_created` audit-first INSERT skip + dry-run 결과 preview = phase_25_vendor_management_preview 1 table + audit-first INSERT `vendor_dry_run_executed` EXTENSION
- T7.2: `apps/api/scripts/cli/finops_vendor_management_dry_run.py` NEW ~+100 LOC + `--finops-vendor-management-dry-run` 1 NEW CLI flag EXTENSION (Phase 24 wire `615d478` 의 2 NEW CLI flags pattern verbatim EXTENSION)
- T7.3: dry-run preview UI EXTENSION 결정 wire = VendorCatalogOverviewCard 진입 시 dry-run toggle (default: dry-run) + dry-run 결과 preview UI EXTENSION
- T7.4: dry-run mode integration tests EXTENSION 결정 wire = ~+6 NEW pytest cases (skip audit + preview table + 1 CLI flag + 4 cadences) EXTENSION

### T8: 3중 게이트 FINAL CLEAN atomic commit (4 subtasks)
- T8.1: ruff scoped Phase 25 files 0 NEW EXTENSION 결정 wire + Phase 24 wire `615d478` 의 0 NEW ruff pattern verbatim EXTENSION
- T8.2: pytest ~+82 NEW pytest PASS EXTENSION 결정 wire (vendor_catalog_engine 18 + vendor_selection_engine 18 + vendor_contract_lifecycle_engine 18 + vendor_performance_evaluation 14 + vendor_spend_attribution 14 = ~82 NEW pytest PASS)
- T8.3: vitest ~+28 NEW vitest PASS EXTENSION 결정 wire (VendorCatalogOverviewCard 7 + VendorSelectionScorePanel 6 + VendorContractLifecycleTimeline 5 + VendorPerformanceScorecardTable 5 + VendorSpendAttributionChart 5 = ~28 NEW vitest PASS)
- T8.4: 3중 게이트 FINAL CLEAN atomic commit via `git commit -F <file>` (CR 9-6 D5 prevention + PowerShell here-string 회피) 결정 wire

**Subtotal**: 8+8+6+4+4+2+4+4 = **~40 subtasks** 결정 wire (Phase 24 wire `615d478` 의 ~38 subtasks pattern 의 5-NEW-module post-allocation layer version EXTENSION → 2 subtasks 추가)

## Dev Notes 19종 (CR lessons applied)

- **CR 0-2 RLS** — 1 preview table 의 tenant-scoped RLS 자동 적용 (current_setting('app.tenant_id')::uuid) 보존
- **CR 1-1 audit-first INSERT 12 NEW** — ActionClass.FINOPS_VENDOR_MANAGEMENT 의 12 NEW audit actions (vendor_created + vendor_updated + vendor_status_changed + vendor_blacklisted + vendor_selection_executed + vendor_contract_approved + vendor_contract_renewed + vendor_contract_terminated + vendor_performance_evaluated + vendor_spend_attributed + vendor_risk_flagged + vendor_dry_run_executed) 결정 wire 진입 시점에 audit-first INSERT 자동 활성화 보존
- **CR 1-1 FastAPI ContextVar** — tenant_id ContextVar middleware layer 보존 (CR 1-1 verbatim EXTENSION)
- **CR 1-1 RSC boundary** — Next.js 15.x RSC boundary 보존 (apps/web/app/[locale]/(dashboard)/admin/finops/vendor-management/{page,layout}.tsx)
- **CR 4-3/4-4** — async-test asyncio.run + Industry enum SSOT + A5 drift detector + golden_diff + SDR overclaim 방지
- **CR 5-1 Decimal precision** — banker's rounding 정합 + 소수점 2자리 EXTENSION (Phase 24 wire 의 budget_plan + allocation_engine Decimal precision pattern verbatim 미러)
- **CR 9-6 commit message** — `git commit -F <file>` (D5 prevention) + PowerShell here-string 회피 결정 wire
- **CR 11-3 honest-DEFER 63번째** — D-FINOPS-14 honestly DEFER 보존 (Phase 25 territory 진입) + Phase 11~24 16-capability FinOps territory chain ✅ ALL WIRED 결정 wire
- **ALLOWED_SERVICE_SUBMODULES 즉시 sweep** — Phase 25 wire 진입 시점에 `apps/api/modules/finops/__init__.py` 의 submodule 목록 즉시 sweep EXTENSION = m25_finops_vendor_management 신규 submodule 등록
- **CR 11-4 D-001~D-005** — ko-KR.json `finops_vendor_management.*` namespace EXTENSION ~35 keys SSOT + NFR18 ko-KR SSOT 보존
- **P-015 SSOT** — ko-KR.json finops_vendor_management.* 단일 SSOT 결정 wire
- **CR 12-1 L4** — industry-agnostic capability grants (4-industry ✅/✅/✅/✅) EXTENSION 결정 wire (Phase 24 wire 의 FINOPS_BUDGET_PLANNING 패턴 verbatim 미러)
- **CR 12-5 D-14 typed exception envelope 16 NEW** — Phase 25 wire 의 16 NEW typed exceptions (FinopsVendorManagementError base + VendorNotFoundError + VendorBlacklistError + VendorStatusTransitionError + VendorComplianceViolationError + VendorSelectionScoreError + VendorPerformanceEvaluationError + VendorSpendAttributionError + Vendor2FARequiredError + VendorContractNotFoundError + VendorContractExpiredError + VendorContractTerminationError + VendorContractRenewalError + VendorRiskScoreError + VendorCatalogSyncError + VendorBenchmarkError + VendorPerformanceSLAError) CR 12-5 D-14 envelope 적용
- **CR 12-5 D-PARITY-01 inversion** — TypeScript mirror parity (vendor-management-types.ts + vendor-management-client.ts) 결정 wire
- **CR 12-5 D-GATE-01 inversion** — capability gate inversion (require_finops_vendor_management + fail-closed 403 Forbidden) 결정 wire
- **A19 cohesion 9 surface EXTENSION PASS** — FinOps Vendor Management surface NEW 결정 wire 진입 후에도 9 surface 모두 PASS 보존
- **A36 SDR 검증 4-step** — 자동 적용 결정 wire (spec entry 진입 시점에 자동)
- **AD-14 stack pin** — Recharts 2.12.7 + TanStack Table v8 + noto-sans-cjk-kr + apscheduler 3.10.4 + pytz 2024.1 EXTENSION 결정 wire (Phase 24 wire 의 AD-14 stack pin verbatim 미러 + TanStack Table v8 EXTENSION)
- **AD-22 owner-only RBAC** — vendor_management dashboard UI 모두 owner-only RBAC EXTENSION (VendorCatalogOverviewCard + VendorSelectionScorePanel + VendorContractLifecycleTimeline + VendorPerformanceScorecardTable + VendorSpendAttributionChart + auto-execute enable 모두 owner-only)
- **Epic 12 2FA 챌린지 mandatory** — destructive endpoint 의 3-layer defense EXTENSION 결정 wire (vendor contract approval ≥ 10M KRW/year + over-budget threshold override ≥ 10M KRW/year + vendor_blacklist action → owner approval flow + 2FA 챌린지)
- **NFR4 PII minimization** ✅ PRESERVED — Phase 25 wire 결정 wire 시에도 PII minimization 자동 보존
- **NFR18 ko-KR SSOT** — apps/web/messages/ko-KR.json finops_vendor_management.* namespace EXTENSION ~35 keys SSOT 보존 결정 wire
- **AD-50 + AD-51 + AD-52 + AD-53 신규** — AD-50 (a)~(g) 7 sub-decisions + AD-51 (a)~(g) 7 sub-decisions + AD-52 (a)~(g) 7 sub-decisions + AD-53 (a)~(g) 7 sub-decisions 모두 결정 wire 진입

## Architecture Alignment (ALLOWED sweep) — Phase 24 wire 정합

- **Backend (FastAPI, Python 3.12)**:
  - 5 NEW modules `apps/api/modules/finops/vendor_management/` (~+1,560 LOC: vendor_catalog_engine + vendor_selection_engine + vendor_contract_lifecycle_engine + vendor_performance_evaluation + vendor_spend_attribution)
  - 1 NEW serializers.py (~+320 LOC)
  - 1 NEW __init__.py submodule
  - 1 NEW scheduled_vendor_management_jobs.py (~+200 LOC)
  - 1 NEW alembic 0057 phase_25_vendor_management.py (1 preview table ONLY + RLS)
  - 1 NEW apps/api/scripts/cli/finops_vendor_management_dry_run.py (~+100 LOC)
  - MODIFIED apps/api/core/capability.py (Capability.FINOPS_VENDOR_MANAGEMENT)
  - MODIFIED apps/api/dependencies/capability.py (require_finops_vendor_management + fail-closed)
  - MODIFIED apps/api/core/audit_action.py (ActionClass.FINOPS_VENDOR_MANAGEMENT + FinopsVendorManagementAction 12 NEW Literal + _ActionRegistry._REGISTRY 1 NEW entry)
  - MODIFIED apps/api/core/errors.py (16 NEW typed exception classes)
  - MODIFIED apps/api/modules/finops/__init__.py (ALLOWED_SERVICE_SUBMODULES EXTENSION)
- **Frontend (Next.js 15.x, TypeScript 5.x)**:
  - 2 NEW apps/web/app/[locale]/(dashboard)/admin/finops/vendor-management/{page,layout}.tsx (~+350 LOC)
  - 1 NEW apps/web/components/finops/FinopsVendorManagementDashboardPanel.tsx (~+300 LOC)
  - 1 NEW apps/web/lib/finops/vendor-management-types.ts (6 NEW TypeScript interfaces)
  - 1 NEW apps/web/lib/finops/vendor-management-client.ts (9 NEW methods)
  - MODIFIED apps/web/messages/ko-KR.json (EXTENSION ~35 keys finops_vendor_management.* namespace)
- **Tests**:
  - ~+82 NEW pytest PASS (vendor_catalog_engine 18 + vendor_selection_engine 18 + vendor_contract_lifecycle_engine 18 + vendor_performance_evaluation 14 + vendor_spend_attribution 14)
  - ~+28 NEW vitest PASS (VendorCatalogOverviewCard 7 + VendorSelectionScorePanel 6 + VendorContractLifecycleTimeline 5 + VendorPerformanceScorecardTable 5 + VendorSpendAttributionChart 5)
  - 0 NEW ruff + 0 NEW tsc + 0 regressions
- **Docs (cumulative; wire sprint will write)**:
  - Spec file (this file) NEW ~+440 LOC
  - Handoff memory NEW
  - Commit-msg NEW
  - Sprint-status MODIFIED v3.82 → v3.83
  - MEMORY.md MODIFIED hook EXTENSION

## Files Affected (estimate ~24 files = 19 NEW + 5 MODIFIED, **wire sprint scope**) — **spec entry sprint 5 files = 3 NEW + 2 MODIFIED**

### Spec entry sprint (cj 172, this sprint) — 5 files = 3 NEW + 2 MODIFIED
1. NEW: `_bmad-output/implementation-artifacts/phase-25-finops-vendor-management-spec.md` (this file, ~+440 LOC)
2. NEW: `memory/handoff-2026-08-27-phase-25-spec-entry-done.md`
3. NEW: `_bmad-output/implementation-artifacts/commit-msg-cj-172.txt`
4. MODIFIED: `_bmad-output/implementation-artifacts/sprint-status.yaml` (v3.82 → v3.83 EXTENSION)
5. MODIFIED: `memory/MEMORY.md` (Phase 25 spec entry hook EXTENSION)

### Wire sprint (cj 173, future) — estimated ~24 files = 19 NEW + 5 MODIFIED (Phase 24 wire `615d478` 의 ~33 files pattern 의 5-NEW-module post-allocation layer version EXTENSION)
- Backend: 5 NEW modules (~+1,560 LOC) + 1 NEW serializers.py + 1 NEW __init__.py + 1 NEW alembic 0057 (1 preview table only) + 1 NEW scheduled_jobs + 1 NEW scripts/cli (~+2,180 LOC)
- Frontend: 2 NEW RSC pages (~+350 LOC) + 1 NEW Client component (~+300 LOC) + 2 NEW TS mirrors (~+220 LOC)
- Tests: ~+82 NEW pytest PASS + ~+28 NEW vitest PASS
- MODIFIED: 5 core files (capability.py + dependencies/capability.py + audit_action.py + errors.py + modules/finops/__init__.py) + ko-KR.json + capability-matrix.md + test_audit_action_v1_51_drift.py = 9 MODIFIED actual count estimate

(Actual wire sprint file count will be verified at wire time via `git show --stat HEAD`.)

## 3중 게이트 impact

- **cj 172 (this sprint, docs-only)**: ruff 0 NEW / pytest 0 NEW / vitest 0 NEW / tsc 0 NEW (apps/api backend unchanged, apps/web frontend unchanged)
- **cj 173 (wire sprint)**: ruff scoped 0 NEW / pytest ~+82 NEW PASS / vitest ~+28 NEW PASS / tsc 0 NEW
- **cj 174 (retro sprint, docs-only)**: ruff 0 NEW / pytest 0 NEW / vitest 0 NEW / tsc 0 NEW

## A695~A698 4 NEW 결정 wire (cj-style 172번째)

- **A695**: 옵션 (a) Phase 25 spec entry 진입 결정 wire (rationale 5종: ① cj-style discipline 회피 위험 방지 = 171번째 Phase 25 PRD entry 진입 직후 자연스러운 spec entry 진입 결정 wire ② Phase 25 PRD entry cj-style 171번째 진입 직후 자연스러운 spec entry 진입 = 172번째 진입 결정 wire ③ Phase 11~24 16-capability FinOps territory chain ✅ ALL WIRED 진입 정합 보존 + Phase 17/18/19/20/21/22/23/24 8-module chain ✅ ALL WIRED ④ 5-NEW-module post-allocation layer = Phase 14 optimization + Phase 18 commitment + Phase 19 pricing + Phase 22 settlement + Phase 23 unit_economics + Phase 24 budget_plan ledger data 활용 → 새 backend infra 불필요 + reuse 최대화 + risk 최소화 + 비즈니스 가치 최고 (vendor 비용 직접 통제 layer 직접적 ROI = executive vendor control surface + SLA compliance + risk mitigation) ⑤ Epic 1 ~ Epic 17 + Phase 3 ~ Phase 24 + Phase 19.5 + Phase 20.5 + Phase 21 audit-fixes + 1st release cycle 정합 보존)
- **A696**: spec 파일 생성 결정 wire (`_bmad-output/implementation-artifacts/phase-25-finops-vendor-management-spec.md` ~+440 LOC + baseline_commit `5e8d435` + cj_style_entry_point 172 + status `ready-for-dev` + Story + 8 ACs §F41.1~§F41.8 verbatim → ~88 detailed sub-ACs (5+5+5+8+6+4+5+10) pre-flight 정합 sweep 만족 + T1~T8 + ~40 subtasks + Dev Notes 19종 + Architecture Alignment ALLOWED sweep + Files Affected ~24 files estimate (~19 NEW + ~5 MODIFIED))
- **A697**: 8 ACs §F41.1~§F41.8 verbatim → ~88 sub-ACs 전개 결정 wire (§F41.1 vendor_catalog engine + 6 vendor_category taxonomy 5 sub-ACs + §F41.2 vendor_selection + 5-dim weighted scoring 5 sub-ACs + §F41.3 vendor_contract_lifecycle sequential + Epic 12 2FA 챌린지 5 sub-ACs + §F41.4 vendor_performance_evaluation + dashboard UI 5 sub-components 8 sub-ACs + §F41.5 Capability matrix v1.51 EXTENSION FINOPS_VENDOR_MANAGEMENT 6 sub-ACs + §F41.6 audit action EXTENSION 12 NEW + 16 NEW typed exception classes 4 sub-ACs + §F41.7 vendor_spend_attribution + cross-budget reconciliation 5 sub-ACs + §F41.8 dry-run + Tests + wire scope T1~T8 10 sub-ACs = ~88 sub-ACs pre-flight 정합 sweep 만족)
- **A698**: Tasks T1~T8 + ~40 subtasks 결정 wire (T1 5 NEW backend vendor_management modules 8 subtasks + T2 dashboard UI 5 sub-components 8 subtasks + T3 alembic 0057 1 preview table 6 subtasks + T4 audit action EXTENSION 12 NEW + 16 NEW typed exception classes 4 subtasks + T5 capability v1.51 EXTENSION 4 subtasks + T6 scheduled_jobs wire 2 subtasks + T7 dry-run mode + 1 NEW CLI flag 4 subtasks + T8 3중 게이트 FINAL CLEAN atomic commit 4 subtasks = ~40 subtasks) + sprint-status v3.82 → v3.83 EXTENSION + atomic commit via `git commit -F <file>` CR 9-6 D5 prevention + commit-msg-cj-172.txt 신규 + handoff memory 신규 + MEMORY.md hook EXTENSION + **5 files = 3 NEW + 2 MODIFIED atomic single sprint** 결정 wire (1 NEW spec file + 1 NEW handoff memory + 1 NEW commit-msg = 3 NEW; 1 MODIFIED sprint-status; 1 MODIFIED MEMORY.md) 진입 완료 보존.

## CR lessons applied 19종

CR 0-2 RLS 1 preview table + CR 1-1 audit-first INSERT 12 NEW + CR 1-1 FastAPI ContextVar + CR 1-1 RSC boundary + CR 4-3/4-4 + CR 5-1 Decimal precision banker's rounding + CR 9-6 commit message `git commit -F <file>` + CR 11-3 honest-DEFER 63번째 D-FINOPS-14 honestly DEFER 보존 + Phase 11~24 16-capability FinOps territory chain ✅ ALL WIRED 결정 wire + ALLOWED_SERVICE_SUBMODULES 즉시 sweep EXTENSION = m25_finops_vendor_management 신규 submodule 등록 + CR 11-4 D-001~D-005 + P-015 SSOT + CR 12-1 L4 industry-agnostic capability matrix v1.51 FINOPS_VENDOR_MANAGEMENT 4-industry grants ✅/✅/✅/✅ + CR 12-5 D-14 typed exception envelope 16 NEW + CR 12-5 D-PARITY-01 inversion TypeScript mirror parity finops_vendor_management.* namespace + CR 12-5 D-GATE-01 inversion capability gate inversion require_finops_vendor_management + A19 cohesion 9 surface EXTENSION PASS + A36 SDR 검증 4-step 자동 적용 + AD-14 stack pin Recharts 2.12.7 + TanStack Table v8 + noto-sans-cjk-kr + apscheduler 3.10.4 + pytz 2024.1 + AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory + NFR4 PII minimization ✅ PRESERVED + AD-50 (a)~(g) 7 sub-decisions + AD-51 (a)~(g) 7 sub-decisions + AD-52 (a)~(g) 7 sub-decisions + AD-53 (a)~(g) 7 sub-decisions + NFR18 ko-KR SSOT

## D-DEFER-* honestly 결정 wire 보존

- D-1-1-DEFER-1/2/3 + D-EPIC-16-REVIEW-DEFER-1/2~6 + D-PHASE-4-DR-DEFER-1/2 + D-EPIC-17-WIRE-DEFER-T2-T3-UI + D-RETENTION-1 + D-OBSERVABILITY-1 + D-PERFORMANCE-1 + D-CHAOS-1 + D-SLO-1 + D-FINOPS-1~13 모두 ✅ ALL RESOLVED 보존
- **D-FINOPS-14 신규 honestly DEFER 보존** — Phase 25 PRD entry 진입 시점에 carry-over chain 정직 회복 결정 wire 진입 = vendor_catalog 6 vendor_category CRUD + lifecycle + vendor_selection 5-dim weighted scoring + vendor_contract_lifecycle sequential + Epic 12 2FA 챌린지 high-value threshold + vendor_performance_evaluation monthly + quarterly cadence + vendor_spend_attribution cross-budget reconciliation + vendor_blacklist compliance gate + vendor marketplace integration external AWS/Azure/GCP marketplace + vendor auto-procurement auto PO generation + vendor consolidation analytics multi-vendor → single-vendor + vendor ESG scorecard environmental + social + governance + vendor AI-driven RFP generation + vendor SLA auto-inforcement + multi-currency vendor contract FX conversion USD/EUR/JPY + vendor invoice reconciliation OCR + line-item matching + vendor onboarding KYC automated + vendor risk scoring ML prediction — 모두 단일 sprint `wire` 진입이 아닌 docs-only entry 에서 honestly defer 결정 wire 보존
- **Phase 25 spec entry = D-FINOPS-14 의 carry-over chain 정직 회복 verification** 결정 wire (CR 11-3 honest-DEFER 63번째 epic 연속 정직 회복)

## Epic 1~17 + Phase 3~24 + Phase 19.5 + Phase 20.5 + 1st release cycle 정합 보존

cj-style 172번째 epic 연속 정직 회복 진입 시점에 pre-flight 정합 sweep 만족 결정 wire 보존:
- Phase 25 PRD entry `5e8d435` (cj-style 171번째) DONE 진입 정합 보존
- Phase 24 close-out retro retroactive correction `1f30b64` (cj-style 170 follow-up) DONE 진입 정합 보존
- Phase 24 close-out retro `c14199b` (cj-style 170번째) DONE 진입 정합 보존
- Phase 24 wire retroactive correction `69c5e28` (cj-style 169 follow-up) DONE 진입 정합 보존
- Phase 24 wire `615d478` (cj-style 169번째) DONE 진입 정합 보존
- Phase 24 spec entry `b3c6c7c` (cj-style 168번째) DONE 진입 정합 보존
- Phase 24 PRD entry `278f37f` (cj-style 167번째) DONE 진입 정합 보존
- audit-fixes sprint entry `a4ae56d` (cj-style 166번째) DONE 진입 정합 보존
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
- Phase 11~20 audit-fixes-infrastructure sprint `7b8e31b` (cj-style 157번째) DONE 진입 정합 보존
- Phase 11~20 audit-fixes Layer 3 P2 docs backfill sprint `21daea8` (cj-style 156번째) DONE 진입 정합 보존
- Phase 11~20 audit-fixes Layer 2 P1 test backfill sprint `4e1f0b3` (cj-style 155번째) DONE 진입 정합 보존
- Phase 11~20 audit-fixes sprint `379ca8e` (cj-style 154번째) DONE 진입 정합 보존
- Phase 21 audit-fixes sprint `f7d1f41` (cj-style 153번째) DONE 진입 정합 보존
- Phase 21 close-out retro `1b101bf` (cj-style 152번째) DONE 진입 정합 보존
- Phase 21 atomic wire `f7d1f41` (cj-style 151번째) DONE 진입 정합 보존
- Phase 21 spec entry `47545d6` (cj-style 150번째) DONE 진입 정합 보존
- Phase 21 PRD entry `563ac9c` (cj-style 149번째) DONE 진입 정합 보존
- Phase 20.5 close-out retro `8505d98` (cj-style 148번째) DONE 진입 정합 보존
- Phase 20.5 atomic wire `46ddcc5` (cj-style 147번째) DONE 진입 정합 보존
- Phase 20.5 spec entry `e23141d` (cj-style 146번째) DONE 진입 정합 보존
- Phase 20 close-out retro `f361016` (cj-style 145번째) DONE 진입 정합 보존
- Phase 20 atomic wire `52dad7f` (cj-style 144번째) DONE 진입 정합 보존
- Phase 20 spec entry `efc3c59` (cj-style 143번째) DONE 진입 정합 보존
- Phase 20 PRD entry `eacb0a5` (cj-style 142번째) DONE 진입 정합 보존
- Phase 19.5 carry-over 결정 wire `b2fb1d8` (cj-style 141번째) DONE 진입 정합 보존
- Phase 19 close-out retro `18ca1ae` (cj-style 140번째) + Phase 19 atomic wire `8db3cfc` (cj-style 139번째) + Phase 19 spec entry `59d15fb` (cj-style 138번째) + Phase 19 PRD entry `ff8a797` (cj-style 137번째) DONE 진입 정합 보존
- Phase 11~24 16-capability FinOps territory chain ✅ ALL WIRED 진입 정합 보존 + Phase 17/18/19/20/21/22/23/24 8-module chain ✅ ALL WIRED 진입 정합 보존
- Epic 1~17 ALL DONE 진입 정합 보존
- 1st release cycle ALL DONE 진입 정합 보존

## 결정 wire 일자 + next

- 결정 wire 일자: 2026-08-27 (KST)
- next 옵션:
  - (a) Phase 25 atomic wire T1~T8 진입 결정 wire (cj-style 173번째) — 5 NEW backend vendor_management modules + 1 NEW alembic 0057 phase_25_vendor_management 1 preview table + 5 NEW dashboard sub-components + audit action 12 NEW + 16 NEW typed exceptions + capability v1.51 + scheduled jobs + dry-run + 1 CLI flag = ~24 files atomic single sprint
  - (b) Phase 25 close-out retro 진입 결정 wire (cj-style 174번째) — 14-section §1~§14 verbatim retro document
  - (c) Layer 2 P1 + Layer 3 P2 carry-over sprint 진입
  - (d) Epic 25+ 진입 결정 wire
  - (e) D-DEFER-* follow-up 결정 wire 보류