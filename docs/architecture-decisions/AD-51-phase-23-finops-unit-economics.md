# AD-51 Phase 23 FinOps Unit Economics

> **Status:** Active (forward-lock target: Phase 23 FinOps territory maintenance)
> **Deciders:** kjw
> **Date:** 2026-08-27 (Phase 23 PRD entry cj-style 162번째)
> **Source PRD:** §F39 (Phase 23 territory 신규) + Phase 11~22 FinOps territory chain

## Context

Phase 11~22 wire cycles delivered 14-capability FinOps territory chain
(`FINOPS_SHOWBACK` + `FINOPS_CHARGEBACK` + `FINOPS_ANOMALY_DETECTION` +
`FINOPS_BUDGET_ALERT` + `FINOPS_FORECASTING_CAPACITY_PLANNING` +
`FINOPS_OPTIMIZATION` + `FINOPS_TAG_GOVERNANCE` + `FINOPS_REPORTING` +
`FINOPS_SUSTAINABILITY` + `FINOPS_COMMITMENT` + `FINOPS_PRICING` +
`FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION` +
`FINOPS_RESERVED_CAPACITY_PLANNING` + `FINOPS_CHARGEBACK_SETTLEMENT`)
— covering cost reporting, anomaly detection, forecasting,
optimization, tagging, sustainability, commitment, pricing,
multi-cloud reconciliation, reserved capacity planning, and
chargeback settlement.

Phase 22 close-out retro `c5726ff` (cj-style 161번째) verified the
chain is wired (Phase 11~22 14-capability FinOps territory chain ✅
ALL WIRED via Phase 22 wire `7acbac0` + retroactive correction
`9dbffc5`). Phase 23 PRD entry (cj-style 162번째) extends the chain
with the **derived metric layer** that consumes ledger data from
Phase 22's 5-dimension weighted allocation + settlement results
and produces cost-per-business-unit / cost-per-transaction /
margin analysis — the executive-facing KPI surface that closes the
gap between FinOps data and business value.

## Decision

AD-51 specifies 7 sub-decisions for Phase 23 FinOps Unit
Economics:

### (a) unit_economics engine + 5-dim cross-join decision

The unit economics engine consumes ledger data from Phase 22's
5-dimension weighted allocation (`cost_center` + `department` +
`business_unit` + `tag` + `tenant`) and produces a single
`UnitEconomicsResult.cost_per_dimension_amount` per
(tenant × period × dimension). The composition rule is:
`cost_per_X = settlement.total_settlement_amount / count_distinct(X)`
where `X ∈ {cost_center, department, business_unit, tag, tenant}`.
This derives from Phase 22's allocation_lines (no new ledger
ingestion required) and uses ledger-key dedup to avoid
double-counting. The composition mirrors Phase 22's
`allocation_engine` + `settlement_rules` pattern (Phase 22 wire
`7acbac0`).

### (b) cost_per_business_unit engine + 5-dim rollup decision

The cost_per_business_unit engine performs 5-dimension rollup
(`cost_center` + `department` + `business_unit` + `tag` + `tenant`)
with default weights inherited from Phase 22
(`{cost_center: 0.30, department: 0.25, business_unit: 0.20,
tag: 0.15, tenant: 0.10}`). Per-tenant override
(`tenant_settings.unit_economics_overrides.dimension_weights`)
takes precedence over industry baseline, which falls back to
system default. Total verification: sum of
`CostPerBusinessUnit.amount` across all rollup rows must equal
`SettlementResult.total_settlement_amount` within ±0.01 KRW
tolerance (CR 5-1 Decimal precision banker's rounding verbatim).

### (c) cost_per_transaction + tag propagation decision

Cost-per-transaction is derived when `transaction_id` is present
in Phase 22 allocation_lines. Tag propagation rule:
`cost_per_transaction = sum(allocation_lines where
transaction_id=X).allocated_amount`. Optional `tag_filter`
(`transaction_tag`, `environment_tag`, `application_tag`)
filters the rollup. Without transaction_id, returns
`None` (not zero — preserves honest DEFER discipline when
data is absent). CR 5-1 Decimal precision + banker's rounding
verbatim applied for KRW currency. KRW base only; USD/EUR/JPY
extension honestly DEFERred to D-FINOPS-12.

### (d) margin_analysis + revenue attribution decision

Margin analysis is OPTIONAL — only executed when revenue is
tagged (via Phase 15 `FINOPS_TAG_GOVERNANCE` extending with
`revenue_amount` tag + `revenue_source` enum). Rule:
`margin = revenue_amount - allocated_amount` per
(business_unit × period). Default: skip when no revenue tag.
Margin margin_pct = margin / revenue. High-value margin
(≥ 10M KRW/year margin positive) auto-triggers
`unit_economics_margin_alert` audit log entry + admin email.
Margin negative (`margin < 0`) auto-triggers
`unit_economics_margin_negative_alert` + tenant_owner Slack DM.
NFR4 PII minimization preserved.

### (e) NFR4 PII minimization preserved decision

NFR4 PII minimization is preserved across all 5 modules:
unit_economics (no PII, only aggregate amounts + dimension
labels) + cost_per_business_unit (only aggregate amounts +
dimension labels, no employee names) + cost_per_transaction
(only transaction_id + amounts, no employee data) +
margin_analysis (only aggregate revenue + amounts, no employee
data) + tag_propagation (only tag values, no employee data).
All audit log entries (`unit_economics_calculated` +
`cost_per_business_unit_refreshed` +
`margin_analysis_executed` +
`unit_economics_dry_run_executed` +
`unit_economics_margin_alert` +
`unit_economics_margin_negative_alert`) carry only `actor_id`
(UUID) + `tenant_id` (UUID) + monetary amounts + status flags
— no raw PII. `Cache-Control: no-store` header on all unit
economics endpoints.

### (f) NFR18 ko-KR SSOT decision

All UI strings in `apps/web/messages/ko-KR.json` under the
`finops_unit_economics.*` namespace (~30 NEW keys):
cost_per_dimension + cost_per_business_unit +
cost_per_transaction + margin_analysis +
dry_run + dashboard. Korean font: `noto-sans-cjk-kr`
(AD-14 stack pin). Error messages in Korean only
(`UnitEconomicsDimensionNotFoundError("단위 경제성 차원을 찾을
수 없습니다")` pattern). Audit log action names in English
(SSOT for cross-system queryability) but UI labels in Korean
(NFR18 ko-KR SSOT).

### (g) Epic 12 2FA 챌린지 mandatory + owner-only decision

Unit economics margin adjustments ≥ 10M KRW/year require Epic
12 2FA 챌린지 mandatory (RFC 6238 TOTP) + tenant_owner
approval flow (Slack DM + 2FA + approval_chain) per Phase 22
settlement high-value pattern. Cost-per-transaction overrides
≥ 10M KRW/year also require Epic 12 2FA 챌린지. 2FA 미설정
tenant 의 경우 `/account/security?reason=2fa_required` redirect.
Owner-only RBAC (AD-22 verbatim) on all unit_economics
endpoints + Epic 12 M12-a 2FA 챌린지 mandatory.
`UnitEconomicsApprovalRequiredError(403)` for non-owner access
to high-value unit_economics endpoints.

## Consequences

### Positive

- Closes the gap between FinOps data and business value:
  cost_per_business_unit → executive KPI surface
- Reuses Phase 22 5-dim allocation_lines data (no new ledger
  ingestion required) — pure derived metric layer
- Pure function computation (ledger in → unit economics out)
  — easy to test, easy to verify, low risk of drift
- Industry-agnostic (4-industry grants ✅/✅/✅/✅) — same as
  Phase 11~22 FinOps territory chain
- Owner-only + Epic 12 2FA 챌린지 for high-value margin
  adjustments — preserves security posture
- Tag propagation extends Phase 15 `FINOPS_TAG_GOVERNANCE`
  naturally without breaking existing tag schema

### Negative / Risks honestly DEFERred

- **D-FINOPS-12 신규 honestly DEFER**: unit_economics 의
  5-dim cross-join backend detail + cost_per_business_unit
  5-dim rollup + cost_per_transaction tag propagation +
  margin_analysis revenue attribution + Epic 12 2FA 챌린지
  high-value threshold detail + per-business_unit margin
  alerting + cost_per_customer (requires CRM integration) +
  multi-currency unit economics (FX conversion) — 모두 Phase
  23 wire cycle 진입 시점에 honestly DEFER 결정 wire 보존
  (spec entry cj-style 163번째 진입 시점에 detail 결정 wire
  진입, wire cycle cj-style 164번째 진입 시점에 implementation
  결정 wire 진입, retro cj-style 165번째 진입 시점에
  close-out 결정 wire 진입)
- **Cost-per-customer DEFERred**: requires CRM integration
  (Salesforce/HubSpot) — 별도 epic 필요
- **Multi-currency unit economics DEFERred**: Phase 23 unit
  economics 는 KRW base 만 지원, USD/EUR/JPY FX conversion
  추가 시 별도 sprint 필요
- **Per-business_unit cost target DEFERred**: target vs actual
  variance tracking 추가 시 별도 epic 필요
- **Margin anomaly auto-investigation DEFERred**: margin
  negative auto-trigger investigation workflow 추가 시 별도
  epic 필요
- **Real-time unit economics stream DEFERred**: 현재 batch
  computation (일 1회 KST cron), real-time stream 시 별도
  epic 필요

## Related

- [[AD-50]] Phase 22 chargeback settlement
- [[AD-49]] Phase 11~20 audit-fixes canonical signature recovery
- [[AD-47]] Phase 20 multi-cloud reconciliation
- [[AD-48]] Phase 20.5 critical gap resolution carry-over
- [[AD-45]] Phase 18 commitment management
- [[AD-44]] Phase 17 sustainability
- [[AD-43]] Phase 16 reporting
- [[handoff-2026-08-27-phase-22-close-out-done]] (cj 161)
- [[handoff-2026-08-27-phase-23-prd-entry-done]] (cj 162)
- Phase 23 PRD entry §F39 (master PRD v8.0 → v9.0 EXTENSION)
- Phase 23 spec entry cj-style 163 진입 대기
- Phase 23 atomic wire T1~T8 cj-style 164 진입 대기
- Phase 23 close-out retro cj-style 165 진입 대기

## Date

2026-08-27 (KST) — Phase 23 PRD entry 결정 wire 진입 시점

## Next

옵션 (a) Phase 23 spec entry 진입 결정 wire (cj-style 163번째) / 옵션 (b) Phase 23 atomic wire T1~T8 진입 결정 wire (cj-style 164번째) / 옵션 (c) Phase 23 close-out retro 진입 결정 wire (cj-style 165번째) / 옵션 (d) Layer 2 P1 + Layer 3 P2 carry-over sprint 진입 / 옵션 (e) audit-fixes sprint 진입 / 옵션 (f) Epic 23+ 진입 결정 wire / 옵션 (g) D-DEFER-* follow-up 결정 wire 보류.