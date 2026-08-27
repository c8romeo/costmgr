# AD-52 Phase 24 FinOps Budget Planning

> **Status:** Active (forward-lock target: Phase 24 FinOps territory maintenance)
> **Deciders:** kjw
> **Date:** 2026-08-27 (Phase 24 PRD entry cj-style 167번째)
> **Source PRD:** §F40 (Phase 24 territory 신규) + Phase 11~23 FinOps territory chain

## Context

Phase 11~23 wire cycles delivered 15-capability FinOps territory chain
(`FINOPS_SHOWBACK` + `FINOPS_CHARGEBACK` + `FINOPS_ANOMALY_DETECTION` +
`FINOPS_BUDGET_ALERT` + `FINOPS_FORECASTING_CAPACITY_PLANNING` +
`FINOPS_OPTIMIZATION` + `FINOPS_TAG_GOVERNANCE` + `FINOPS_REPORTING` +
`FINOPS_SUSTAINABILITY` + `FINOPS_COMMITMENT` + `FINOPS_PRICING` +
`FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION` +
`FINOPS_RESERVED_CAPACITY_PLANNING` + `FINOPS_CHARGEBACK_SETTLEMENT` +
`FINOPS_UNIT_ECONOMICS`)
— covering cost reporting, anomaly detection, forecasting,
optimization, tagging, sustainability, commitment, pricing,
multi-cloud reconciliation, reserved capacity planning,
chargeback settlement, and unit economics.

Phase 23 close-out retro `7875ac9` (cj-style 165번째) verified the
chain is wired (Phase 11~23 15-capability FinOps territory chain ✅
ALL WIRED via Phase 23 wire `f850d0e` + retroactive correction
`948ff35`). Phase 24 PRD entry (cj-style 167번째) extends the chain
with the **budget planning layer** — the pre-allocation counterpart
to Phase 22 chargeback settlement and Phase 23 unit economics. Where
Phase 22/23 operate on actual ledger data (post-hoc attribution),
Phase 24 operates on forward-looking budget plans that drive the
allocation logic, approval workflows, and over-budget alerting
that closes the loop between plan and actual.

## Decision

AD-52 specifies 7 sub-decisions for Phase 24 FinOps Budget
Planning:

### (a) budget_plan engine + CRUD + lifecycle decision

The budget plan engine manages CRUD operations for budget plans
across three period types: annual (1 plan/year/tenant),
quarterly (4 plans/year/tenant), and monthly
(12 plans/year/tenant). Each plan has a `period_key` formatted
as `YYYY` (annual), `YYYY-Qn` (quarterly), or `YYYY-MM`
(monthly). The lifecycle transitions through 4 states:
`draft` → `pending_approval` → `approved` → `closed`. The
5-dimension cross-join (cost_center + department + business_unit +
tag + tenant) builds on Phase 22/23's 5-dimension weighted
allocation pattern. Same ledger-key dedup applies to avoid
double-counting during allocation. Budget plans are audited
via `budget_plan_created`, `budget_plan_updated`,
`budget_plan_submitted_for_approval`, `budget_plan_approved`,
`budget_plan_rejected`, and `budget_plan_closed`. Dry-run mode
(`--finops-budget-planning-dry-run`) skips actual INSERTs.

### (b) budget_allocation + 5-dim weighted allocation decision

Budget allocation uses the same 5-dimension model as Phase 22
chargeback settlement and Phase 23 unit economics:
(cost_center: 0.30, department: 0.25, business_unit: 0.20,
tag: 0.15, tenant: 0.10). Each allocation line carries
(tenant_id, plan_id, dimension, dimension_value,
allocated_amount, currency_code, allocation_pct). Per-tenant
override (`tenant_settings.budget_planning_overrides.allocation_weights`)
takes precedence over industry baseline, which falls back to
system default. Total verification: sum of
`BudgetAllocationLine.allocated_amount` across all allocation
rows must equal `BudgetPlan.total_budget_amount` within ±0.01
KRW tolerance (CR 5-1 Decimal precision banker's rounding
verbatim). Zero-amount allocations are skipped (no allocation_line
created); negative-amount allocations (refund/adjustment)
preserve the negative sign.

### (c) budget_approval_workflow + sequential approval decision

Budget approval uses a sequential approval chain. Each
approval step has (step_index, approver_user_id, approver_role,
status pending/approved/rejected/skipped, approved_at,
2fa_verified boolean, comment). Steps are processed in order;
a rejection at any step rolls the plan back to `draft`. A high-value
budget plan (≥ 10M KRW/year) triggers Epic 12 2FA 챌린지 mandatory
(RFC 6238 TOTP) for each approver. System-generated approval
chains skip 2FA verification. Approval chain transitions are audited
via `budget_plan_submitted_for_approval`, `budget_plan_approved`,
`budget_plan_rejected`, `budget_plan_approval_2fa_verified`.

### (d) budget_vs_actual + dashboard UI 5 sub-components decision

Budget vs actual is computed by joining Phase 22
`settlement_results.total_settlement_amount` (actuals) with
Phase 24 `BudgetPlan.total_budget_amount` (plan) on
(tenant_id, period_key, dimension). Variance is computed
per-dimension: `variance_amount = budget_allocation - actual_allocation`,
`variance_pct = variance_amount / budget_allocation`. The dashboard
UI consists of 5 NEW sub-components:
`BudgetPlanOverviewCard` (plan summary + CRUD actions) +
`BudgetAllocationBreakdownPanel` (5-dim Recharts pie chart) +
`BudgetVsActualTrendChart` (12-month Recharts line chart) +
`OverBudgetAlertPanel` (variance alerts + auto-escalation status) +
`ApprovalChainStatusPanel` (sequential approval visualization).
Recharts 2.12.7 (AD-14 stack pin), owner-only RBAC (AD-22),
Epic 12 2FA 챌린지 preservation, and ko-KR.json
`finops_budget_planning.*` namespace (~30 NEW keys, NFR18 SSOT).

### (e) NFR4 PII minimization preserved decision

NFR4 PII minimization is preserved across all 5 modules:
budget_plan_engine (only plan metadata + amounts, no employee
data) + budget_allocation (only dimension labels + amounts,
no employee data) + budget_approval_workflow (only user IDs
as UUIDs, no employee names or emails) + budget_vs_actual (only
aggregate amounts + dimension labels) + budget_alert
(only threshold breach + escalation status, no employee data).
All audit log entries (`budget_plan_created` +
`budget_plan_updated` + `budget_plan_submitted_for_approval` +
`budget_plan_approved` + `budget_plan_rejected` +
`budget_allocation_verified` + `budget_alert_triggered` +
`budget_planning_dry_run_executed`) carry only `actor_id`
(UUID) + `tenant_id` (UUID) + monetary amounts + status flags
— no raw PII. `Cache-Control: no-store` header on all
budget_planning endpoints.

### (f) NFR18 ko-KR SSOT decision

All UI strings in `apps/web/messages/ko-KR.json` under the
`finops_budget_planning.*` namespace (~30 NEW keys):
plans + allocation + alerts + approval + dashboard.
Korean font: `noto-sans-cjk-kr` (AD-14 stack pin).
Error messages in Korean only
(`BudgetPlanNotFoundError("예산 계획을 찾을 수 없습니다")` pattern).
Audit log action names in English (SSOT for cross-system
queryability) but UI labels in Korean (NFR18 ko-KR SSOT).

### (g) Epic 12 2FA 챌린지 mandatory + owner-only decision

Budget plan approval for high-value plans (≥ 10M KRW/year) requires
Epic 12 2FA 챌린지 mandatory (RFC 6238 TOTP) + tenant_owner approval
chain (Slack DM + 2FA + approval_chain) per Phase 22 settlement
high-value pattern and Phase 23 unit_economics margin high-value
pattern. Over-budget threshold override ≥ 10M KRW/year also requires
Epic 12 2FA 챌린지. 2FA 미설정 tenant 의 경우
`/account/security?reason=2fa_required` redirect.
Owner-only RBAC (AD-22 verbatim) on all budget_planning
endpoints + Epic 12 M12-a 2FA 챌린지 mandatory.
`BudgetApproval2FARequiredError(403)` for non-owner access
to high-value budget_planning endpoints.

## Consequences

### Positive

- Closes the pre-allocation gap: budget planning → settlement
  (Phase 22) → unit economics (Phase 23) → budget vs actual
  (Phase 24) → over-budget alert (Phase 24)
- Reuses Phase 22 settlement_results and Phase 23 unit_economics
  ledger data (no new ledger ingestion required) — pure
  forward-planning layer that mirrors Phase 22/23's 5-dimension
  weighted allocation pattern
- Approval workflow + 2FA 챌린지 gate high-value plans — preserves
  security posture while enabling self-service for low-value plans
- Pure function computation (plan in → allocation out, ledger in →
  variance out) — easy to test, easy to verify, low risk of drift
- Industry-agnostic (4-industry grants ✅/✅/✅/✅) — same as
  Phase 11~23 FinOps territory chain
- Sequential approval chain + Slack DM notification gives auditability
  for every approval decision
- Auto-escalation on critical over-budget (25% over) closes the
  loop without manual intervention

### Negative / Risks honestly DEFERred

- **D-FINOPS-13 신규 honestly DEFER**: budget_planning 의
  5-dim cross-join backend detail + budget_allocation
  5-dim weighted allocation + budget_approval_workflow sequential
  + Epic 12 2FA 챌린지 high-value threshold detail + over-budget
  auto-escalation chain + per-budget approval override +
  per-budget plan vs actual reconcile — 모두 Phase 24 wire cycle
  진입 시점에 honestly DEFER 결정 wire 보존 (spec entry
  cj-style 168번째 진입 시점에 detail 결정 wire 진입, wire
  cycle cj-style 169번째 진입 시점에 implementation 결정 wire
  진입, retro cj-style 170번째 진입 시점에 close-out 결정
  wire 진입)
- **Multi-currency budget planning DEFERred**: Phase 24 budget
  planning 는 KRW base 만 지원, USD/EUR/JPY FX conversion 추가 시
  별도 sprint 필요
- **Budget forecast auto-rollover DEFERred**: annual → quarterly
  → monthly 자동 rollover 시 별도 epic 필요
- **Budget scenario comparison (A/B testing) DEFERred**: 복수
  budget plan 비교 시 별도 epic 필요
- **Budget vs actual variance auto-investigation DEFERred**:
  variance > 25% 시 자동 investigation workflow 추가 시 별도 epic 필요
- **Zero-based budgeting (ZBB) DEFERred**: 0-base budget plan 추가 시
  별도 epic 필요
- **Incremental budgeting DEFERred**: incremental budget plan 추가 시
  별도 epic 필요
- **Envelope budgeting DEFERred**: envelope-based budget plan 추가 시
  별도 epic 필요

## Related

- [[AD-51]] Phase 23 unit economics
- [[AD-50]] Phase 22 chargeback settlement
- [[AD-49]] Phase 11~20 audit-fixes canonical signature recovery
- [[AD-47]] Phase 20 multi-cloud reconciliation
- [[AD-48]] Phase 20.5 critical gap resolution carry-over
- [[AD-45]] Phase 18 commitment management
- [[AD-44]] Phase 17 sustainability
- [[AD-43]] Phase 16 reporting
- [[handoff-2026-08-27-phase-23-close-out-done]] (cj 165)
- [[handoff-2026-08-27-phase-24-prd-entry-done]] (cj 167)
- Phase 24 PRD entry §F40 (master PRD v9.0 → v10.0 EXTENSION)
- Phase 24 spec entry cj-style 168 진입 대기
- Phase 24 atomic wire T1~T8 cj-style 169 진입 대기
- Phase 24 close-out retro cj-style 170 진입 대기

## Date

2026-08-27 (KST) — Phase 24 PRD entry 결정 wire 진입 시점

## Next

옵션 (a) Phase 24 spec entry 진입 결정 wire (cj-style 168번째) / 옵션 (b) Phase 24 atomic wire T1~T8 진입 결정 wire (cj-style 169번째) / 옵션 (c) Phase 24 close-out retro 진입 결정 wire (cj-style 170번째) / 옵션 (d) Layer 2 P1 + Layer 3 P2 carry-over sprint 진입 / 옵션 (e) audit-fixes sprint 진입 결정 wire / 옵션 (f) Epic 24+ 진입 결정 wire / 옵션 (g) D-DEFER-* follow-up 결정 wire 보류.
