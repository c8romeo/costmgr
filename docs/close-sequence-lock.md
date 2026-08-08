# Close Sequence Lock (v1.0)

> **Single source of truth** for the **monthly close sequence lock** subsystem
> introduced by **Story 11.2** (cj-style 3-story 분할 2번째 — Epic 5 retro §6 W1
> 결정 + Epic 5 retro §6 §11 명시). This doc covers PRD §F11.1 (close sequence
> order), §F11.2 (AD-22 reversal exception), §F11.3 (reversal authorization),
> Architecture Spine §AD-6 (fiscal-period close lock) + §AD-22 (reversal/correction
> exception), and the **4-stage close sequence state machine** that gates every
> monthly close in manufacturing-kind tenants.

## Why this exists

PRD §8.M11(a) explicitly mandates:

> 시스템은 부문분할 → 제조 → ABC → 공동 순서를 강제하고, 부분 마감을 허용하지 않는다.

Without an enforced order, downstream artifacts (closing snapshots, ledger
events, fiscal_period_snapshots) would be inserted in a partial or out-of-order
state, breaking the audit chain and making AD-22 reversals impossible to scope.
The 4-stage state machine plus partial close guard give operations a single,
deterministic flow with one reject reason per failure mode.

## Wire surface (Story 11.2)

Three new HTTP routes (registered under the M11 module authority):

| Method | Path | Capability | Purpose |
| --- | --- | --- | --- |
| `POST` | `/api/v1/close/sequence/initiate` | `CLOSE_SEQUENCE_LOCK` | Create `fiscal_periods` row at `close_sequence_state='divisions'`, audit `closing_sequence_initiated`. |
| `POST` | `/api/v1/close/sequence/step-complete` | `CLOSE_SEQUENCE_LOCK` | Mark the current step complete and advance the state machine. 4-stage order enforced. Audit `closing_sequence_step_completed`. |
| `GET`  | `/api/v1/close/sequence/state` | `CLOSE_SEQUENCE_LOCK` | Read-only state check (returns 4-stage progress + missing step + capability grant). |

All routes are 11-2 wire; they reuse the **11-1 M11 module authority**
(`apps/api/modules/m11_close/`) and the **AD-25 1-channel publisher** for the
final `closing_sequence_confirmed` cache invalidation.

## 4-stage state machine (AC #2, AC #5)

```
divisions (T0)  →  manufacturing (T1)  →  abc (T2)  →  common (T3)  →  confirmed (T4)
```

- The state is **1-way**: each `step_complete` call advances by exactly one
  stage, in order. Out-of-order calls raise
  `CloseSequenceStepMismatchError` (409 `CLOSE_SEQUENCE_STEP_MISMATCH`).
- The state column is `fiscal_periods.close_sequence_state` (TEXT, NOT NULL,
  CHECK ∈ `('divisions', 'manufacturing', 'abc', 'common', 'confirmed')`).
- Timestamps: `divisions_completed_at` / `manufacturing_completed_at` /
  `abc_completed_at` / `common_completed_at` (TIMESTAMPTZ, NULL).
- `closed_at` is set only on `confirm_close_sequence` success
  (`close_sequence_state='confirmed'`).

The pure kernel is `packages/services/m11_close/close_sequence_order.py`
(`validate_close_sequence_order`); see `§Pure kernels` below.

## Partial close guard (AC #3)

A `confirm_close_sequence` call is rejected unless **all 4 stages are complete**.
The guard is a single pure function (`check_partial_close_attempt`) that returns
`PartialCloseGuardResult(blocked, missing_step, reject_reason_ko)`. Failure raises
`PartialCloseBlockedError` (409 `PARTIAL_CLOSE_BLOCKED`) with the Korean message
carrying the missing step name.

This is the runtime enforcement of PRD §8.M11(a) "부분 마감을 허용하지 않는다".

## AD-6 INSERT 거부 (AC #4)

Once `fiscal_periods.status='closed'`, **all business-data INSERTs are rejected
except AD-22 reversal/correction events**. The pure kernel
(`check_ad6_insert_allowed(close_sequence_state, target_table, target_event_type)`)
is consulted by `confirm_close_sequence` immediately before the ledger INSERT.
Allowed: `inventory_ledger` + `event_type IN ('reversal_negating', 'reversal_corrected')`.
Rejected: any other target table on a confirmed fiscal period.

This is the Architecture Spine §AD-6 Rule expressed in code.

## 11-1 reversal authorization 양쪽 가드 (AC #6)

`packages/services/m11_close/reversal_authorization.py:authorize_reversal` now
takes **two** status inputs:

```python
def authorize_reversal(
    *,
    capability_granted: bool,
    period_status: str,            # monthly_input_periods.status
    fiscal_period_status: str,     # fiscal_periods.status  (NEW in 11-2)
    target_event_type: str,
) -> AuthorizationDecision:
```

Both statuses must be in the allowed set (`PERIOD_STATUS_ALLOWED = {'open', 'closed'}` —
note `'closed'` is allowed at the reversal-authorization layer; the actual
AD-22 reversal/correction exception is what permits the insert). The wire
contract preserves 11-1 compatibility: callers that don't yet pass
`fiscal_period_status='open'` are treated as the legacy single-guard path and
fall through to the original decision.

## Confirm flow (AC #5 — `confirm_close_sequence` 7-step atomic)

1. (0.5) Call legacy `confirm_closing_period` (6-1 wire) → sets
   `monthly_input_periods.status='closed'` (idempotent no-op skip).
2. (1) `SELECT ... FOR UPDATE` on `fiscal_periods` (idempotent no-op skip on
   `close_sequence_state='confirmed'` → `ClosingSequenceAlreadyConfirmedError`).
3. (2) Partial close guard (see §Partial close guard).
4. (3.5) AD-6 INSERT 거부 guard (see §AD-6 INSERT 거부).
5. (4) Ledger INSERT — `closing_snapshot` event_type per product (6-1 wire entry).
6. (5) V4 verifier dispatch (6-1 wire entry).
7. (6) UPDATE `fiscal_periods` → `status='closed'`, `close_sequence_state='confirmed'`, `closed_at=now()`.
8. (7) Audit-first emit `closing_sequence_confirmed` (AD-15 §11 Korean message).

CR 1.1 audit-first ordering is preserved: ledger INSERT (4) → fiscal_periods
UPDATE (6) → audit log INSERT (7) within a single REPEATABLE READ transaction.

## Capability matrix v1.11 (AC #8)

`Capability.CLOSE_SEQUENCE_LOCK` is new in this story:

| Industry | CLOSE_SEQUENCE_LOCK |
| --- | --- |
| `manufacturing` | ✅ |
| `manufacturing_service` | ✅ |
| `manufacturing_service_other` | ✅ |
| `service` | ❌ (403 INDUSTRY_NOT_SUPPORTED) |

Rationale: PRD §6.4 + §Q-I (industry × engine fixed mapping). Service-only
tenants do not run the 4-stage close sequence because they have no manufacturing
ABC; their path is the service P&L roll-up covered by Epic 12.

## A5 forward-lock (AC #7)

`ActionClass.MONTHLY_CLOSING` (separate frozenset from `ActionClass.CLOSING_PERIOD`
preserved by 6-1 wire) gets 4 NEW values:

- `closing_sequence_initiated` — `initiate_close_sequence` succeeded.
- `closing_sequence_step_completed` — `step_complete` succeeded for a step.
- `closing_sequence_blocked` — partial close guard rejected a `confirm`.
- `closing_sequence_confirmed` — `confirm_close_sequence` succeeded.

11-1's `ActionClass.REVERSAL_LOG` 5 values + `ActionClass.MONTHLY_INPUT_PERIOD`
`opening_inventory_unlocked` extension are preserved unchanged.

## Typed exceptions and AD-15 envelope mapping

| Exception | Status | Code | When |
| --- | --- | --- | --- |
| `PartialCloseBlockedError` | 409 | `PARTIAL_CLOSE_BLOCKED` | confirm before all 4 stages complete |
| `CloseSequenceAlreadyInitiatedError` | 409 | `CLOSE_SEQUENCE_ALREADY_INITIATED` | `initiate` called when row exists |
| `CloseSequenceStepMismatchError` | 409 | `CLOSE_SEQUENCE_STEP_MISMATCH` | out-of-order `step_complete` |
| `CloseSequenceCapabilityDeniedError` | 403 | `CLOSE_SEQUENCE_CAPABILITY_DENIED` | service-only tenant |
| `ClosingSequenceAlreadyConfirmedError` | 409 | `ALREADY_CONFIRMED` | idempotent re-confirm |
| `ClosingSequenceAuditEmitError` | 500 | `AUDIT_EMIT_FAILED` | audit-first emit failure |
| `LockedPeriodReversalRejectedError` | 422 | `LOCKED_PERIOD_REVERSAL_REJECTED` | 11-1 carry, now with fiscal_periods.status dispatch |

All map to AD-15 §4 typed envelope contract. Handler wiring is in
`apps/api/main.py` (4 NEW exception handlers added on top of 11-1's 6).

## Pure kernels (AD-11 layer rule — stdlib-only)

| Kernel | File | Purpose |
| --- | --- | --- |
| `validate_close_sequence_order` | `packages/services/m11_close/close_sequence_order.py` | 4-stage ordering + chronological invariant + violation reasons |
| `compute_close_sequence_state` + `check_ad6_insert_allowed` | `packages/services/m11_close/close_sequence_state.py` | state machine + AD-6 enforcement matrix |
| `check_partial_close_attempt` | `packages/services/m11_close/partial_close_guard.py` | partial close detection + Korean reject message |

All three are stdlib-only, no DB, no clock (inputs explicit), no random — per
AD-11 + the project convention.

## Alembic 0020 + RLS (AC #1, AC #9)

`apps/api/alembic/versions/0020_fiscal_periods_close_sequence.py` is the
greenfield migration that adds the `fiscal_periods` table. It is **chained** from
`0019_m11_reversal_ledger` (11-1 wire tip). 5 CHECK constraints, 1 UNIQUE,
2 INDEXes. The companion `supabase/policies/0011_fiscal_periods_rls.sql` enables
+ forces RLS with the standard 4-policy split
(`tenant_select_own` / `tenant_insert_own` / `tenant_update_own_blocked_status` /
`tenant_delete_blocked`).

## V8 골든 fixture matrix extension (AC #all — deferred)

V8 fixture matrix will extend from 18 → 22 by adding 4 NEW fixtures:

- `close_sequence_initiated.json` — T0 state, capability_granted=true.
- `close_sequence_step_completed_partial_blocked.json` — confirm attempt with
  3/4 stages complete → `PartialCloseBlockedError`.
- `close_sequence_confirmed.json` — T4 state, fiscal_periods.status='closed',
  ledger closing_snapshot event_type present.
- `close_sequence_reversal_blocked.json` — AD-22 reversal attempt against a
  non-allowed event type → 422 LOCKED_PERIOD_REVERSAL_REJECTED.

These fixtures are part of the **bmad-code-review carry-over sweep** along
with the frontend panel (Task 10). They are not committed in this story's
checkpoint commit (1dbb01f).

## Carry-over & follow-ups

The following items remain deferred to `bmad-code-review` sweep or the
follow-up cycle:

- **Task 10** (Frontend close sequence panel + Playwright E2E) — entirely
  frontend; deferred.
- **TS mirror + parity test** (`apps/web/lib/m11-close-sequence.ts` +
  `m11-close-sequence-parity.ts`) — covered by Task 2.3 / 2.4 / 4.3.
- **Audit drift detector extensions** (`test_audit_action_centralization.py` +
  `test_audit_action_consistency.py`) — covered by Task 7.3 / 7.4.
- **Capability matrix drift test** (`test_capability_matrix_drift.py`) —
  Task 8.5.
- **V8 골든 fixture JSON files + regression test extension** — Task 11.8 /
  11.9 / 11.10.

## Reference (related docs)

- `docs/architecture-inventory.md` — M11 module authority + fiscal_periods
  table + 4-stage state (Story 11.2 EXTENSION).
- `docs/closing-period.md` — 6-1 wire baseline; this doc extends it with the
  4-stage state dimension.
- `docs/closing-guard.md` — Story 5.3 closing_guard; this doc extends it with
  the 4-stage close sequence guard + AD-6 close lock.
- `docs/reversal-sequence.md` — 11-1 wire baseline; this doc extends the
  reversal authorization with the fiscal_periods.status second guard.
- `docs/audit-actions.md` — `ActionClass.MONTHLY_CLOSING` 4 NEW values wire
  contract.
- `docs/conventions.md §10` — Audit Actions SSOT extension.
- `docs/capability-matrix.md` v1.11 — CLOSE_SEQUENCE_LOCK capability row.
