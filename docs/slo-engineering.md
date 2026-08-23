# SLO Engineering / Error Budget Management Runbook

> **Phase 10 bmad-dev-story atomic wire T1~T8 DONE (cj-style 103번째)**.
> Owner: SRE platform team. Last updated: 2026-08-24 (KST).

이 문서는 Phase 10 wire 의 운영/런북 가이드입니다. PRD §F26.1~§F26.7
verbatim 7 ACs 의 운영 절차를 다루며, AD-37 의 7 sub-decisions (SLO 정의
DSL + multi-window burn-rate + error budget + multi-region aggregation +
tenant-scoped override + governance review + auto-rollback trigger) 를
운영상 어떻게 다루는지 설명합니다.

## 1. SLO Definition DSL (PRD §F26.1)

SLO 정의는 `apps/api/modules/slo/slo_dsl.py` 의 `SloDefinition`
TypedDict 13 fields 를 따릅니다:

| Field | Type | Notes |
|-------|------|-------|
| `slo_id` | TEXT PK | `slo:<service>:<sli_type>` 명명 규약 |
| `tenant_id` | UUID FK | RLS 자동 적용 CR 0-2 |
| `service` | TEXT | cost-engine / signups / logins / audit_purge |
| `sli_type` | TEXT enum 5 | latency / availability / throughput / error_rate / freshness |
| `objective` | NUMERIC(5,2) | 0 < x ≤ 100 (% 가용성) |
| `window` | TEXT enum 6 | 1h / 6h / 24h / 3d / 7d / 30d |
| `burn_rate_threshold` | NUMERIC(8,2) | default 14.4 (fast_burn) |
| `error_budget_policy` | TEXT enum 3 | freeze_on_exhaust / alert_only / auto_rollback |
| `region` | TEXT enum 3 | seoul / tokyo / all |
| `multi_region_aggregation` | TEXT enum 4 | weighted_avg / min / max / any_failure |
| `freeze_enabled` | BOOL | default FALSE |
| `auto_rollback_trigger` | BOOL | default TRUE |
| `governance_required` | BOOL | default FALSE |

`validate_slo_definition(payload)` 가 CR 11-4 P-015 verbatim pure
validator 이며, 5 가지 typed exception (CR 12-5 D-14 envelope) 으로
검증 실패를 surface 합니다:

- `SloDefinitionInvalidError(400)` — invalid field
- `SloOverrideConflictError(409)` — duplicate override
- `SloBudgetExhaustedError(422)` — freeze_on_exhaust 정책 + 잔여 ≤ 0
- `SloViolationDetectedError(422)` — composite breach
- `SloGovernanceRequiredForbiddenError(403)` — pending governance bypass

## 2. Multi-Window Burn-Rate Evaluation (PRD §F26.2)

Google SRE Workbook "multi-window, multi-burn-rate criteria" verbatim
4 windows 가 `apps/api/modules/slo/slo_burn_rate_evaluator.py` 에
구현되어 있습니다.

| Window | Threshold | Alert Window | Purpose |
|--------|-----------|--------------|---------|
| `fast_burn` | 14.4x | 5 min | page 즉시, 빠른 사고 감지 |
| `slow_burn` | 6.0x | 30 min | budget 빠른 소진 감지 |
| `exhaustion` | 3.0x | 2 hours | budget 고갈 임박 |
| `long_window` | 1.0x | 6 hours | 장기 drift 감지 |

Composite alert logic:

```
alert = (fast OR slow) AND (slow OR exhaustion) AND (exhaustion OR long)
```

이 식은 Google SRE Workbook Ch. 5 "Alerting on SLOs" 의 공식 패턴을
verbatim 따릅니다. `evaluate_all_windows()` 가 composite breach 감지 시
`SloViolationDetectedError` 를 발생시키고, 이 이벤트는 `_ActionRegistry`
에서 `slo_violation_detected` 액션으로 audit-first INSERT 됩니다.

## 3. Error Budget Lifecycle (PRD §F26.3)

`apps/api/modules/slo/error_budget.py` 의 `ErrorBudget` TypedDict 8
fields:

- `budget_total_minutes`, `budget_consumed_minutes`, `budget_remaining_minutes`
- `freeze_triggered` (BOOL)
- `exhaustion_predicted_at` (TIMESTAMPTZ)
- `last_evaluated_at`

Budget 정책:

- `freeze_on_exhaust`: 잔여 ≤ 0 시 freeze 트리거 + `SloBudgetExhaustedError`
- `alert_only`: alert 만 발송, freeze 하지 않음
- `auto_rollback`: 잔여 ≤ 0 시 Phase 9 chaos_experiment_aborted + chaos_rollback_triggered 자동 fire

`predict_exhaustion_at()` 는 linear extrapolation 으로 7-day horizon
내 소진 시각을 예측합니다.

## 4. Multi-Region Aggregation (PRD §F26.4)

`apps/api/modules/slo/multi_region_aggregator.py` 의 가중치:

```
DEFAULT_REGION_WEIGHT_MAP = {seoul: 0.6, tokyo: 0.3, singapore: 0.1}
```

Phase 5 wire 정합 + cross-region replication lag threshold 100MB, 1.2x
multiplier 적용.

Aggregation methods:
- `weighted_avg`: 가중 평균
- `min`: 가장 보수적 (가장 낮은 성능)
- `max`: 가장 낙관적
- `any_failure`: 한 region 실패 시 전체 실패

## 5. Tenant-Scoped SLO Override (PRD §F26.5)

`TenantSloOverride` TypedDict 6 fields:

- `override_id`, `tenant_id`, `slo_id`
- `objective_override` (NUMERIC(5,2) NULL)
- `window_override` (TEXT NULL)
- `effective_from`, `expires_at`

UNIQUE constraint `(tenant_id, slo_id)` + RLS 정책 CR 0-2 verbatim
자동 적용. `override_is_active(override, now)` 가 effective_from ~
expires_at 윈도우 검증.

## 6. SLO Governance Review (PRD §F26.6)

`apps/api/modules/slo/governance.py` 의 `GovernanceReview` TypedDict 7
fields + 4 status (pending/approved/rejected/escalated).

Trigger 조건 4가지:

1. `budget_consumed_pct > 75%` for 7d
2. `burn_rate_3d > 1x` sustained
3. `freeze_until expired + budget_negative`
4. `error_budget exhausted < 24h to reset`

Review 가 `pending` 상태인 동안에는 `require_governance_approval` 가
`SloGovernanceRequiredForbiddenError(403)` 으로 차단합니다. owner-only
RBAC AD-22 + Epic 12 2FA 챌린지 보존.

## 7. Auto-Rollback SLO Breach Trigger (PRD §F26.7)

`should_trigger_auto_rollback()` 가 4가지 조건 평가:

| Condition | Trigger Within |
|-----------|----------------|
| `fast_burn` | 60 seconds |
| `slow_burn` | 30 minutes |
| `composite` | 60 seconds |
| `exhaustion` | 60 seconds |

Trigger 시 `AutoRollbackDecision` TypedDict 5 fields 생성 +
`link_to_chaos_rollback()` 으로 Phase 9 chaos_experiment 와 correlation
id `slo:<slo_id>:<trace_id>` 로 연결.

## 8. Audit-First INSERT (CR 1-1 verbatim)

3 가지 audit log entries 가 `ActionClass.SLO_ENGINEERING` 하위:

- `slo_target_updated` — 목표 변경 시
- `slo_budget_exhausted` — budget 소진 시
- `slo_violation_detected` — composite breach 감지 시

`_ActionRegistry` 3 frozenset entries 신규 등록.

## 9. Capability Gate (CR 12-1 L4)

`apps/api/core/capability.py` 에 `Capability.SLO_ENGINEERING` 1 NEW
enum 정의 + 4 INDUSTRY_CAPABILITIES blocks 모두 ✅/✅/✅/✅ grant.
`apps/api/dependencies/capability.py` 에 `require_slo_engineering` 1 NEW
dep + `__all__` EXTENSION.

drift detector: `tests/integration/test_capability_matrix_v1_35_drift.py`
NEW 4 NEW pytest cases.

## 10. Frontend Dashboard (apps/web/components/slo)

`apps/web/app/[locale]/(dashboard)/admin/slo/page.tsx` + `layout.tsx` +
`SloDashboardPanel.tsx` (4 panels: SloDefinitionList + ErrorBudgetTracker
+ SloGovernanceReviewList + SloFreezeButton) + `slo-client.ts` (TypedDict
parity CR 12-5 D-PARITY-01) + `slo-types.ts` (CR 12-5 D-PARITY-01) +
ko-KR.json `slo.*` namespace EXTENSION ~30 keys (CR 11-4 D-002 SSOT).

모든 액션은 owner-only RBAC AD-22 + Epic 12 2FA 챌린지 보존.

## 11. Operational Runbook

### 11.1 새 SLO 정의 추가

```
POST /api/v1/admin/slo/definitions
Authorization: Bearer <owner-access-token>
Content-Type: application/json

{
  "slo_id": "slo:cost-engine:p99-latency",
  "service": "cost-engine",
  "sli_type": "latency",
  "objective": 99.9,
  "window": "1h",
  "burn_rate_threshold": 14.4,
  "error_budget_policy": "freeze_on_exhaust",
  "region": "all",
  "multi_region_aggregation": "weighted_avg",
  "freeze_enabled": true,
  "auto_rollback_trigger": true,
  "governance_required": false,
  "state": "draft"
}
```

owner-only RBAC AD-22 — admin role 도 403 Forbidden. Epic 12 2FA 챌린지
필수.

### 11.2 Error Budget Freeze

```
POST /api/v1/admin/slo/error-budgets/{slo_id}/freeze
Authorization: Bearer <owner-access-token>
Content-Type: application/json

{
  "reason": "스모크 테스트 후 수동 freeze"
}
```

### 11.3 Governance Review Approve

```
POST /api/v1/admin/slo/governance/reviews/{review_id}/approve
Authorization: Bearer <owner-access-token>
Content-Type: application/json

{
  "notes": "Approved via dashboard"
}
```

## 12. Cross-References

- Master PRD v4.0→v4.1 EXTENSION: Phase 10 PRD entry `09db4d4` (cj-style 101번째)
- Spec: Phase 10 spec entry (cj-style 102번째) — `_bmad-output/implementation-artifacts/phase-10-slo-engineering-wire.md`
- Phase 8 SLO/SLI 정의: `docs/slo-sli-definition.md` (Phase 8 wire 정합)
- Phase 9 chaos_experiment baseline + auto-rollback: `apps/api/modules/chaos/`
- Phase 5 multi-region carry-over chain: `apps/api/modules/region/`
- Phase 7 observability metrics: `apps/api/core/metrics.py` (3 NEW SLO metrics)
- Phase 6 audit log retention: NFR4 5년 audit_logs 보존 결정 wire

## 13. 결정 wire 일자 / next

결정 wire 일자: 2026-08-24 (KST).
**next**: (a) Phase 10 close-out retro 진입 (cj-style 104번째) / (b) Phase 11+ 진입 / (c) Epic 18+ 진입 / (d) carry-over / (e) D-DEFER-* follow-up 결정 wire 보류.
