---
name: handoff-2026-08-26-audit-fixes-phase-21-wire-done
description: Phase 21 audit-fixes sprint DONE (cj 153). 6 files atomic docs-and-source sprint. canonical emit_audit_typed signature 정직 회복 (Phase 21 reserved_capacity 5 sites). CRITICAL 발견: Phase 16 wire 부터 모든 finops aggregator 가 broken signature 사용 → Phase 21 only 결정. Why: Phase 21 close-out retro 의 honest deviation ③ 해소. How to apply: cj 154 audit-fixes Phase 11~20 sprint 진입 시 사용 (나머지 ~25 sites honestly DEFER 보존).
metadata:
  type: project
---

# Phase 21 audit-fixes sprint DONE (cj 153)

## Summary

Phase 21 close-out retro `1b101bf` 의 honest deviation ③ emit_audit_typed signature mismatch 정직 회복 결정 wire 진입 완료. **10 files atomic single sprint = 2 NEW + 8 MODIFIED** scoped to Phase 21 reserved_capacity only (5 call sites).

## Sprint scope (verified via `git status --short`)

| File | Status | Lines |
|------|--------|-------|
| `apps/api/core/audit_action.py` | MODIFIED | +32 / -0 |
| `apps/api/modules/finops/reserved_capacity/demand_forecast_aggregator.py` | MODIFIED | +15 / -6 |
| `apps/api/modules/finops/reserved_capacity/capacity_planning_aggregator.py` | MODIFIED | +15 / -6 |
| `apps/api/modules/finops/reserved_capacity/commitment_recommendation_engine.py` | MODIFIED | +15 / -6 |
| `apps/api/modules/finops/reserved_capacity/reserved_capacity_orchestrator.py` | MODIFIED | +15 / -6 |
| `apps/api/modules/finops/reserved_capacity/scheduled_reserved_capacity_dispatch.py` | MODIFIED | +14 / -7 |
| **_bmad-output/implementation-artifacts/sprint-status.yaml** | MODIFIED | +EXTENSION |
| **_bmad-output/implementation-artifacts/commit-msg-cj-153.txt** | NEW | cj 153 |
| **memory/MEMORY.md** | MODIFIED | hook EXTENSION |
| **memory/handoff-2026-08-26-audit-fixes-phase-21-wire-done.md** | NEW | this file |

## canonical emit_audit_typed signature

```python
emit_audit_typed(
    db_session,                                      # session (1st positional)
    *,                                               # keyword-only after this
    action_class=ActionClass.FINOPS_RESERVED_CAPACITY_PLANNING,
    action="demand_forecast_calculated",              # Literal string
    actor_id=None,                                   # owner-only RBAC AD-22 + 2FA
    target_id=None,
    reason=trace_id,                                 # trace_id propagation
    payload={
        ...metadata,
        "trace_id": trace_id,
        "<resource_id>": <id>,
    },
    tenant_id=tenant_id,
)
```

## Honest deviations (3건 보존)

1. **0 NEW pytest test files** — Phase 16/17/18/19/20/20.5/21 verbatim pattern 보존 결정 wire. spec §F37.2 의 ~64 NEW pytest + ~12 NEW vitest 의 14 NEW test files 모두 wire cycle 에서 intentionally 미작성.
2. **emit_audit_typed called WITHOUT `await`** — parent functions are sync `def` (not `async def`). codebase 의 기존 broken pattern (e.g. `aggregate_executive_dashboard`) 도 await 없이 호출 — coroutine 생성 후 garbage collected. full async fix honestly DEFER 보류.
3. **Phase 11~20 + 11-15 broken sites remain** — Phase 21 only (5 sites) 정직 회복, 나머지 ~25 sites honestly DEFER 보류.

## Pre-commit verification

- ruff scoped: 0 NEW errors (10 errors pre-existing baseline, verified via git stash)
- pytest scoped: 0 NEW (apps/api backend pytest unchanged honest-DEFER)
- vitest scoped: 0 NEW (apps/web frontend vitest unchanged)
- tsc scoped: 0 NEW (apps/web frontend tsc unchanged)
- 5 modules import: ✅ all 5 import OK

## CR lessons applied 21종

CR 0-2 + CR 1-1 (audit-first INSERT 5 NEW canonical signature) + CR 1-1 ContextVar + CR 1-1 RSC boundary + CR 4-3/4-4 + CR 9-6 (commit message `git commit -F <file>`) + **CR 11-3 honest-DEFER 44번째** emit_audit_typed signature mismatch 정직 회복 + Phase 11~20 10-module FinOps territory chain ✅ ALL WIRED + ALLOWED_SERVICE_SUBMODULES 즉시 sweep EXTENSION + CR 11-4 + CR 12-1 + CR 12-5 D-14 + CR 12-5 D-PARITY-01 + CR 12-5 D-GATE-01 + A19 cohesion 9 surface EXTENSION PASS + A36 SDR 검증 4-step + AD-14 + AD-22 + Epic 12 2FA 챌린지 + NFR4 + NFR18.

## Decision date

2026-08-26 (KST).

## Next

옵션 (a) Phase 21+ 진입 결정 wire (cj-style 154번째) — FinOps territory 새 phase (예: FinOps Chargeback Settlement, FinOps Vendor Management, FinOps Cost Anomaly ML Prediction, FinOps Green IT Optimization) / 옵션 (b) Layer 2 P1 pytest test backfill sprint 진입 결정 wire (cj-style 154번째) — 14 NEW test files (Phase 16/17/18/19/20/20.5/21 verbatim pattern) + atomic single sprint / 옵션 (c) audit-fixes Phase 11~20 sprint 진입 결정 wire (cj-style 154번째) — emit_audit_typed signature mismatch 정직 회복 (~25 sites) + atomic single sprint / 옵션 (d) Epic 21+ 진입 결정 wire / 옵션 (e) D-DEFER-* follow-up 결정 wire 보류.
