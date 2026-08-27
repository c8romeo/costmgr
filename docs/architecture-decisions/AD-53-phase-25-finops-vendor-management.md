# AD-53 Phase 25 FinOps Vendor Management

> **Status:** Active (forward-lock target: Phase 25 FinOps territory maintenance)
> **Deciders:** kjw
> **Date:** 2026-08-27 (Phase 25 PRD entry cj-style 171번째)
> **Source PRD:** §F41 (Phase 25 territory 신규) + Phase 11~24 FinOps territory chain

## Context

Phase 11~24 wire cycles delivered 16-capability FinOps territory chain
(`FINOPS_SHOWBACK` + `FINOPS_CHARGEBACK` + `FINOPS_ANOMALY_DETECTION` +
`FINOPS_BUDGET_ALERT` + `FINOPS_FORECASTING_CAPACITY_PLANNING` +
`FINOPS_OPTIMIZATION` + `FINOPS_TAG_GOVERNANCE` + `FINOPS_REPORTING` +
`FINOPS_SUSTAINABILITY` + `FINOPS_COMMITMENT` + `FINOPS_PRICING` +
`FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION` +
`FINOPS_RESERVED_CAPACITY_PLANNING` + `FINOPS_CHARGEBACK_SETTLEMENT` +
`FINOPS_UNIT_ECONOMICS` + `FINOPS_BUDGET_PLANNING`)
— covering showback/chargeback, anomaly detection, forecasting,
optimization, tagging, sustainability, commitment, pricing,
multi-cloud reconciliation, reserved capacity planning,
chargeback settlement, unit economics, and budget planning.

Phase 24 close-out retro `1f30b64` (cj-style 170번째) verified the
chain is wired (Phase 11~24 16-capability FinOps territory chain ✅
ALL WIRED via Phase 24 wire `615d478` + retroactive correction
`69c5e28`). Phase 25 PRD entry (cj-style 171번째) extends the chain
with the **vendor management layer** — the post-budget-allocation
counterpart to Phase 24 budget planning. Where Phase 24 operates on
forward-looking budget plans (allocation_lines + approval_chain),
Phase 25 operates on actual vendor selection, contract lifecycle,
performance evaluation, and spend attribution that closes the
loop between budget and realized vendor cost.

Phase 24 budget_allocation lines + Phase 14 optimization
recommendations + Phase 18 commitment data + Phase 19 pricing
data + Phase 22 chargeback settlement results + Phase 23
unit_economics ledger data → Phase 25 vendor_catalog +
vendor_selection + vendor_contract_lifecycle +
vendor_performance_evaluation + vendor_spend_attribution 결정 wire.

## Decision

AD-53 specifies 7 sub-decisions for Phase 25 FinOps Vendor
Management:

### (a) vendor_catalog + CRUD + lifecycle decision

The vendor catalog engine manages CRUD operations for vendor
records. Each vendor has (vendor_id UUID PK + tenant_id UUID +
vendor_name TEXT + vendor_category TEXT e.g. "cloud" /
"saas" / "outsourcing" / "consulting" / "other" +
vendor_status enum active/inactive/under_review/blacklisted +
contract_start_date DATE + contract_end_date DATE nullable +
total_contract_value + currency_code + payment_terms
enum net_30/net_60/net_90/prepaid + primary_contact JSONB
+ tags JSONB + risk_score NUMERIC(5,2) +
performance_score NUMERIC(5,2) + created_at + updated_at +
trace_id + actor_id). Lifecycle transitions: `active` →
`under_review` (triggered by performance drop or risk flag) →
`inactive` (voluntary offboarding) OR `blacklisted` (compliance
violation). Audit-first INSERT `vendor_created` +
`vendor_updated` + `vendor_status_changed` +
`vendor_blacklisted` CR 1-1 verbatim 결정 wire. Multi-tenant
RLS via `tenant_id` column CR 0-2 verbatim 결정 wire. Industry
baseline `vendor_category` taxonomy: cloud / saas / outsourcing /
consulting / hardware / other 6 categories 결정 wire.

### (b) vendor_selection + 5-dim weighted scoring decision

Vendor selection uses a 5-dimension weighted scoring model:
(cost: 0.30, performance: 0.25, reliability: 0.20, compliance: 0.15,
strategic_fit: 0.10). Each vendor gets a per-dimension score
(NUMERIC(5,2) range 0.00~100.00) and a weighted total score
(0.00~100.00). Per-tenant override
(`tenant_settings.vendor_selection_overrides.dimension_weights`)
takes precedence over industry baseline, which falls back to
system default. The selection engine selects top-N vendors per
`vendor_category` based on weighted_total_score. Reuses Phase 22
allocation_lines + Phase 14 optimization recommendations +
Phase 18 commitment data + Phase 19 pricing data → score
calculation. CR 5-1 Decimal precision banker's rounding
verbatim 적용. Score version <= 100.00 strict range +
selection_threshold default 60.00 → below threshold 자동
excluded + selection_candidate_limit default 10 (top-N) 결정 wire.

### (c) vendor_contract_lifecycle + Epic 12 2FA 챌린지 decision

Vendor contract lifecycle: `draft` → `pending_approval` →
`approved` → `active` → `expiring_soon` → `renewed` OR
`expired` OR `terminated`. Each transition triggers audit-first
INSERT. High-value contracts (≥ 10M KRW/year) require Epic 12
2FA 챌린지 mandatory (RFC 6238 TOTP) for tenant_owner approval
(Slack DM + 2FA + approval_chain). System-generated renewals
skip 2FA verification. Contract value computation uses
Phase 19 pricing data (rate cards) + Phase 18 commitment data
(RI/SP/CUD utilization) + Phase 24 budget_plan.total_budget_amount
(allocated budget ceiling) → computed_total_contract_value
within budget ceiling auto-approved, over budget ceiling
requires Epic 12 2FA 챌린지 mandatory 결정 wire. Auto-renewal
window 90 days before contract_end_date (Phase 24 budget_plan
auto-rollover cadence pattern verbatim EXTENSION). CR 12-5 D-14
typed exception envelope 16 NEW typed exception classes
(VendorContractNotFoundError 404 + VendorContractExpiredError
410 + VendorContractTerminationError 409 + VendorSelectionScoreError
500 + VendorPerformanceEvaluationError 500 + VendorSpendAttributionError
500 + Vendor2FARequiredError 403 + VendorBlacklistError 403 +
VendorContractRenewalError 500 + VendorComplianceViolationError
403 + VendorRiskScoreError 500 + VendorCatalogSyncError 500 +
VendorBenchmarkError 500 + VendorContractApprovalTimeoutError
500 + VendorSpendAllocationError 500 + VendorPerformanceSLAError
500) 결정 wire.

### (d) vendor_performance_evaluation + dashboard UI 5 sub-components decision

Vendor performance evaluation computes per-vendor scores across
4 dimensions: (sla_compliance: 0.30, cost_efficiency: 0.25,
support_quality: 0.25, innovation: 0.20). Performance evaluation
runs monthly (1st of month 03:00 KST) + quarterly (1st of
quarter 03:30 KST) + on-demand (manual trigger). Score
computation pulls Phase 11~24 ledger data (Phase 11 chargeback
data + Phase 18 commitment utilization + Phase 22 settlement
results + Phase 24 budget_vs_actual variance) → per-vendor
score_card. Dashboard UI 5 NEW sub-components:
`VendorCatalogOverviewCard` (vendor list + CRUD + filter) +
`VendorSelectionScorePanel` (5-dim Recharts radar chart) +
`VendorContractLifecycleTimeline` (contract timeline +
renewal alerts) +
`VendorPerformanceScorecardTable` (TanStack Table monthly +
quarterly scores) +
`VendorSpendAttributionChart` (Recharts stacked bar chart:
vendor vs budget vs actual). Recharts 2.12.7 (AD-14 stack pin) +
owner-only RBAC (AD-22) + Epic 12 2FA 챌린지 preservation +
ko-KR.json `finops_vendor_management.*` namespace (~35 NEW keys,
NFR18 SSOT) 결정 wire.

### (e) NFR4 PII minimization preserved decision

NFR4 PII minimization is preserved across all 5 modules:
vendor_catalog (only vendor metadata + scores, no employee
data) + vendor_selection (only weighted scores + threshold
metadata, no employee data) + vendor_contract_lifecycle
(only contract terms + amounts + dates, no employee data
beyond owner UUIDs) + vendor_performance_evaluation (only
aggregate scores + dimension labels) + vendor_spend_attribution
(only attributed amounts + vendor IDs, no employee data).
All audit log entries (`vendor_created` + `vendor_updated` +
`vendor_status_changed` + `vendor_blacklisted` +
`vendor_selection_executed` + `vendor_contract_approved` +
`vendor_contract_renewed` + `vendor_contract_terminated` +
`vendor_performance_evaluated` + `vendor_spend_attributed` +
`vendor_risk_flagged` + `vendor_compliance_violation_detected` +
`vendor_dry_run_executed`) carry only `actor_id` (UUID) +
`tenant_id` (UUID) + monetary amounts + score metrics — no
raw PII. `Cache-Control: no-store` header on all
vendor_management endpoints.

### (f) NFR18 ko-KR SSOT decision

All UI strings in `apps/web/messages/ko-KR.json` under the
`finops_vendor_management.*` namespace (~35 NEW keys):
catalog + selection + contract + performance + dashboard +
alerts + renewal + risk. Korean font: `noto-sans-cjk-kr`
(AD-14 stack pin). Error messages in Korean only
(`VendorContractNotFoundError("공급업체契約を 찾을 수 없습니다")`
pattern). Audit log action names in English (SSOT for
cross-system queryability) but UI labels in Korean (NFR18
ko-KR SSOT).

### (g) Epic 12 2FA 챌린지 mandatory + owner-only decision

Vendor contract approval for high-value contracts (≥ 10M KRW/year)
requires Epic 12 2FA 챌린지 mandatory (RFC 6238 TOTP) +
tenant_owner approval chain (Slack DM + 2FA + approval_chain)
per Phase 18 commitment high-value pattern and Phase 19 pricing
TCO high-value pattern and Phase 22 settlement high-value pattern
and Phase 24 budget_plan high-value pattern. Vendor blacklist
action requires Epic 12 2FA 챌린지 mandatory (compliance
violation trace). 2FA 미설정 tenant 의 경우
`/account/security?reason=2fa_required` redirect.
Owner-only RBAC (AD-22 verbatim) on all vendor_management
endpoints + Epic 12 M12-a 2FA 챌린지 mandatory.
`Vendor2FARequiredError(403)` for non-owner access to high-value
vendor_management endpoints. `VendorBlacklistError(403)` for
blacklisted vendor access attempt.

## Consequences

### Positive

- Closes the post-budget-allocation gap: budget planning
  (Phase 24) → vendor selection (Phase 25) → contract lifecycle
  (Phase 25) → performance evaluation (Phase 25) → spend
  attribution (Phase 25) → over-budget alert (Phase 24 close-loop)
- Reuses Phase 14 optimization + Phase 18 commitment + Phase 19
  pricing + Phase 22 settlement + Phase 23 unit_economics +
  Phase 24 budget_plan ledger data (no new ledger ingestion
  required) — pure vendor layer that mirrors Phase 11~24
  5-dimension weighted scoring pattern
- High-value vendor contract approval workflow + 2FA 챌린지
  gate — preserves security posture while enabling self-service
  for low-value contracts
- Pure function computation (vendor in → score out, contract in
  → spend out, ledger in → variance out) — easy to test, easy
  to verify, low risk of drift
- Industry-agnostic (4-industry grants ✅/✅/✅/✅) — same as
  Phase 11~24 FinOps territory chain
- Sequential approval chain + Slack DM notification gives
  auditability for every vendor contract decision
- Auto-renewal 90-day window + over-budget cross-check closes
  the loop without manual intervention
- Vendor blacklist compliance gate preserves regulatory posture
  while enabling fast vendor onboarding

### Negative / Risks honestly DEFERred

- **D-FINOPS-14 신규 honestly DEFER**: vendor_management 의
  5-dim weighted scoring backend detail + vendor_contract_lifecycle
  sequential + Epic 12 2FA 챌린지 high-value threshold detail +
  vendor_performance_evaluation monthly + quarterly cadence +
  vendor_spend_attribution cross-budget reconciliation — 모두
  Phase 25 wire cycle 진입 시점에 honestly DEFER 결정 wire 보존
  (spec entry cj-style 172번째 진입 시점에 detail 결정 wire
  진입, wire cycle cj-style 173번째 진입 시점에 implementation
  결정 wire 진입, retro cj-style 174번째 진입 시점에 close-out
  결정 wire 진입)
- **Vendor marketplace integration DEFERred**: external vendor
  marketplace (AWS Marketplace / Azure Marketplace / GCP Marketplace
  + SaaS directories) integration 시 별도 epic 필요
- **Vendor auto-procurement DEFERred**: 자동 PO (purchase order)
  generation + 자동 송금 처리 + 자동 세금계산서 발행 추가 시
  별도 epic 필요
- **Vendor consolidation analytics DEFERred**: 단일 vendor
  consolidation 추천 (multi-vendor → single-vendor) 시
  별도 epic 필요
- **Vendor ESG scorecard DEFERred**: ESG (Environmental +
  Social + Governance) 점수 + sustainability 정합 시
  별도 epic 필요 (Phase 17 sustainability 와 cross-reference)
- **Vendor AI-driven RFP generation DEFERred**: AI 기반
  RFP (request for proposal) 자동 생성 + vendor response
  자동 parsing 시 별도 epic 필요
- **Vendor SLA auto-enforcement DEFERred**: SLA 위반 자동
  detection + 자동 penalty + 자동 credit note 발행 시
  별도 epic 필요
- **Multi-currency vendor contract DEFERred**: USD/EUR/JPY
  vendor contract + FX conversion 시 별도 epic 필요 (Phase 24
  multi-currency budget planning 와 cross-reference)

## Related

- [[AD-52]] Phase 24 budget planning
- [[AD-51]] Phase 23 unit economics
- [[AD-50]] Phase 22 chargeback settlement
- [[AD-49]] Phase 11~20 audit-fixes canonical signature recovery
- [[AD-45]] Phase 18 commitment management
- [[AD-43]] Phase 16 reporting
- [[handoff-2026-08-27-phase-24-close-out-done]] (cj 170)
- [[handoff-2026-08-27-phase-25-prd-entry-done]] (cj 171)
- Phase 25 PRD entry §F41 (master PRD v10.0 → v11.0 EXTENSION)
- Phase 25 spec entry cj-style 172 진입 대기
- Phase 25 atomic wire T1~T8 cj-style 173 진입 대기
- Phase 25 close-out retro cj-style 174 진입 대기

## Date

2026-08-27 (KST) — Phase 25 PRD entry 결정 wire 진입 시점

## Next

옵션 (a) Phase 25 spec entry 진입 결정 wire (cj-style 172번째) / 옵션 (b) Phase 25 atomic wire T1~T8 진입 결정 wire (cj-style 173번째) / 옵션 (c) Phase 25 close-out retro 진입 결정 wire (cj-style 174번째) / 옵션 (d) Layer 2 P1 + Layer 3 P2 carry-over sprint 진입 / 옵션 (e) audit-fixes sprint 진입 결정 wire / 옵션 (f) Epic 25+ 진입 결정 wire / 옵션 (g) D-DEFER-* follow-up 결정 wire 보류.