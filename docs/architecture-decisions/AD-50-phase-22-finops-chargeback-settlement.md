# AD-50 Phase 22 FinOps Chargeback Settlement

> **Status:** Active (forward-lock target: Phase 22 FinOps territory maintenance)
> **Deciders:** kjw
> **Date:** 2026-08-27 (Phase 22 PRD entry cj-style 158번째)
> **Source PRD:** §F38 (Phase 22 territory 신규) + Phase 11~21 FinOps territory chain

## Context

Phase 11~21 wire cycles delivered 11-module FinOps territory chain
(`FINOPS_SHOWBACK` + `FINOPS_CHARGEBACK` + `FINOPS_ANOMALY_DETECTION` +
`FINOPS_BUDGET_ALERT` + `FINOPS_FORECASTING_CAPACITY_PLANNING` +
`FINOPS_OPTIMIZATION` + `FINOPS_TAG_GOVERNANCE` + `FINOPS_REPORTING` +
`FINOPS_SUSTAINABILITY` + `FINOPS_COMMITMENT` + `FINOPS_PRICING` +
`FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION` +
`FINOPS_RESERVED_CAPACITY_PLANNING`) — covering cost reporting,
anomaly detection, forecasting, optimization, tagging, sustainability,
commitment, pricing, multi-cloud reconciliation, reserved capacity
planning. The natural settlement/chargeback layer for closing the
loop on these reports (turning insights into billable line items
across tenants, departments, and cost centers) was honestly DEFERred
to Phase 21+ per Epic 17 close-out retro `be8f3bd` §11 ("FinOps
Reserved Capacity Planning 결정 wire 보류, Phase 21+ 진입 시점")
and the chain continues into Phase 22.

Phase 21 close-out retro `1b101bf` (cj-style 152번째) verified the
chain is wired (Phase 17/18/19/20 4-module FinOps territory chain ✅
ALL WIRED via Phase 20.5 wire `46ddcc5`). Phase 22 PRD entry
(cj-style 158번째) extends the chain with the **settlement layer**
that consumes ledger data from the prior 11 modules and produces
tenant-level invoices + allocation breakdowns + reconciliation
results — the directly-ROI surface that closes the FinOps value
loop.

## Decision

AD-50 specifies 7 sub-decisions for Phase 22 FinOps Chargeback
Settlement:

### (a) settlement_rules engine + 5-module cross-join decision

The settlement engine consumes ledger data from 5 prior FinOps
modules (Phase 11 chargeback_engine ledger + Phase 18 commitment
cost + Phase 19 pricing rate × usage + Phase 20 multi_cloud cost
variance + Phase 21 reserved_capacity commitment cost) via
weighted average (`FIVE_MODULE_WEIGHTS = {chargeback: 0.30,
commitment: 0.20, pricing: 0.20, multi_cloud: 0.15,
reserved_capacity: 0.15}`) to produce a single
`SettlementResult.total_settlement_amount` per tenant × period.
This composition mirrors Phase 21's 5-module cross-join
(`demand_forecast_aggregator`) and avoids double-counting via
ledger-key dedup.

### (b) allocation_engine + 5-dimension weighted allocation decision

The allocation engine distributes `SettlementResult.total_settlement_amount`
across 5 dimensions (`cost_center` + `department` + `business_unit`
+ `tag` + `tenant`) with default weights
(`{cost_center: 0.30, department: 0.25, business_unit: 0.20,
tag: 0.15, tenant: 0.10}`). Per-tenant override
(`tenant_settings.settlement_overrides.allocation_weights`)
takes precedence over industry baseline, which falls back to
system default. Total verification: sum of
`AllocationLine.allocated_amount` across all allocation lines
must equal `SettlementResult.total_settlement_amount` within
±0.01 KRW tolerance.

### (c) invoice_generation + PDF/XLSX/CSV template decision

Invoice generation supports 3 formats (PDF via `reportlab==4.0.7` +
XLSX via `xlsxwriter==3.1.9` + CSV via standard library) with
AD-14 stack pin. Korean font: `noto-sans-cjk-kr`. Page size: A4
landscape (allocation breakdown wide table). Recipient list:
`tenant_settings.settlement_overrides.recipient_emails` override
> `SETTLEMENT_RECIPIENT_TEMPLATES` (manager + finance + tenant
owner) fallback. Rate limit: 1 invoice / minute / owner (Phase 10
SLO breach rate limit pattern verbatim EXTENSION).

### (d) reconciliation 3-way match decision

Reconciliation performs 3-way match:
`settlement_amount` ↔ `invoice_amount` ↔ `allocation_amount`.
Tolerance: default 1.0% (per-tenant override via
`tenant_settings.settlement_overrides.reconciliation_tolerance_pct`,
range 0~10%). On mismatch: 3 auto-retries with 5-minute interval
(Phase 12 budget_alert pattern verbatim EXTENSION). On persistent
failure: `SettlementReconciliationFailedError(500)` + admin email
alert. High-value settlements (≥ 10M KRW/year) require Epic 12
2FA 챌린지 + tenant_owner approval chain (Slack DM + 2FA +
approval_chain) per Phase 21 reserved_capacity_orchestrator
pattern.

### (e) NFR4 PII minimization preserved decision

NFR4 PII minimization is preserved across all 4 modules:
settlement_rules (no PII, only rule metadata) + allocation_engine
(only aggregate amounts + dimension labels, no employee names) +
invoice_generation (recipient email only, no SSN/phone/address) +
reconciliation (only monetary amounts, no employee data). All
audit log entries (`settlement_rule_created` +
`settlement_rule_updated` + `settlement_calculated` +
`allocation_verified` + `settlement_invoice_generated` +
`settlement_reconciled` + `settlement_dry_run_executed` +
`settlement_approval_required`) carry only `actor_id` (UUID) +
`tenant_id` (UUID) + monetary amounts + status flags — no raw
PII. `Cache-Control: no-store` header on all settlement
endpoints.

### (f) NFR18 ko-KR SSOT decision

All UI strings in `apps/web/messages/ko-KR.json` under the
`finops_chargeback_settlement.*` namespace (~30 NEW keys):
rules + allocation + invoice + reconciliation + trend. Korean
font: `noto-sans-cjk-kr` (AD-14 stack pin). Error messages in
Korean only (`SettlementRuleNotFoundError("정산 규칙을 찾을 수
없습니다")` pattern). Audit log action names in English
(SSOT for cross-system queryability) but UI labels in Korean
(NFR18 ko-KR SSOT).

### (g) Epic 12 2FA 챌린지 mandatory for high-value decision

Settlements ≥ 10M KRW/year savings require Epic 12 2FA 챌린지
mandatory (RFC 6238 TOTP) + tenant_owner approval flow
(Slack DM + 2FA + approval_chain). 2FA 미설정 tenant 의 경우
`/account/security?reason=2fa_required` redirect. Owner-only RBAC
(AD-22 verbatim) on all settlement endpoints + Epic 12 M12-a
2FA 챌린지 mandatory. `SettlementApprovalRequiredError(403)`
for non-owner access to high-value settlement endpoints.

## Consequences

### Positive

- Closes the FinOps value loop: insights → allocation → invoice
  → reconciliation → billable line items (direct ROI)
- Reuses ledger data from 5 prior modules (Phase 11 chargeback
  + Phase 18 commitment + Phase 19 pricing + Phase 20 multi_cloud
  + Phase 21 reserved_capacity) — no new backend infra required
- Pure function computation (ledger in → settlement out) — easy
  to test, easy to verify, low risk of drift
- Industry-agnostic (4-industry grants ✅/✅/✅/✅) — same as
  Phase 11~21 FinOps territory chain
- Owner-only + Epic 12 2FA 챌린지 for high-value — preserves
  security posture

### Negative / Risks honestly DEFERred

- **D-FINOPS-11 신규 honestly DEFER**: settlement 의 5-module
  cross-join backend detail + allocation 5-dimension weight +
  invoice 3-format template + reconciliation 3-way match
  algorithm + Epic 12 2FA 챌린지 high-value threshold detail
  — 모두 Phase 22 wire cycle 진입 시점에 honestly DEFER
  결정 wire 보존 (spec entry cj-style 159번째 진입 시점에
  detail 결정 wire 진입, wire cycle cj-style 160번째 진입
  시점에 implementation 결정 wire 진입, retro cj-style 161번째
  진입 시점에 close-out 결정 wire 진입)
- **Multi-currency settlement DEFERred**: Phase 22 의 settlement
  는 KRW base 만 지원, USD/EUR/JPY 추가 시 별도 sprint 필요
- **Tax compliance (VAT, GST, withholding) DEFERred**: 10% VAT
  (default) 만 지원, per-country tax rule 적용 시 별도 sprint
  필요
- **Settlement dispute workflow DEFERred**: tenant가 invoice 에
  dispute 신청 시 workflow, 별도 epic 필요
- **Settlement refund / credit note DEFERred**: refund/credit note
  처리 시 별도 sprint 필요

## Related

- [[AD-49]] Phase 11~20 audit-fixes canonical signature recovery
- [[AD-47]] Phase 20 multi-cloud reconciliation
- [[AD-48]] Phase 20.5 critical gap resolution carry-over
- [[AD-45]] Phase 18 commitment management
- [[AD-44]] Phase 17 sustainability
- [[AD-43]] Phase 16 reporting
- [[handoff-2026-08-27-phase-22-prd-entry-done]] (cj 158)
- Phase 22 PRD entry §F38 (master PRD v7.0 → v8.0 EXTENSION)
- Phase 22 spec entry cj-style 159 진입 대기
- Phase 22 atomic wire T1~T8 cj-style 160 진입 대기
- Phase 22 close-out retro cj-style 161 진입 대기

## Date

2026-08-27 (KST) — Phase 22 PRD entry 결정 wire 진입 시점

## Next

옵션 (a) Phase 22 spec entry 진입 결정 wire (cj-style 159번째) / 옵션 (b) Phase 22 atomic wire T1~T8 진입 결정 wire (cj-style 160번째) / 옵션 (c) Phase 22 close-out retro 진입 결정 wire (cj-style 161번째) / 옵션 (d) Layer 2 P1 + Layer 3 P2 carry-over sprint 진입 / 옵션 (e) audit-fixes sprint 진입 / 옵션 (f) Epic 22+ 진입 결정 wire / 옵션 (g) D-DEFER-* follow-up 결정 wire 보류.