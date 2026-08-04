# Story 5.2 Code Review — bmad-code-review

> Generated 2026-08-04
> Reviewer: bmad-code-review (3-layer adversarial: Blind Hunter + Edge Case Hunter + Acceptance Auditor)
> Range: b4b84da..HEAD (8 commits, 7,769 raw lines, 37 files)
> Spec: `_bmad-output/implementation-artifacts/5-2-inventory-ledger-append-only-events.md`
> Diff: `_bmad-output/implementation-artifacts/.review/story-5-2.diff`
> Triage: `_bmad-output/implementation-artifacts/.review/story-5-2-triage.md`

## Verdict

**Status**: `review` → cannot promote to `done` without patch resolution.

**Surface tension**: author pre-flight claimed `pytest 975/91/0` (pass/skip/fail). Actual: `985/119/1 FAILING` — SDR drift detector failure not detected (cluster C24).

**Surviving findings**: 23 (3 decision-needed + 16 patch + 4 defer) + 6 dismissed.

**HIGH severity patches blocking `done`**: 15 (P1-P15). 3 are critical for table safety:
- **P2**: `qty >= 0` CHECK blocks negative qty for outbound events (PRD §6.2 signed qty required).
- **P11**: `supabase/policies/0007_inventory_ledger_rls.sql` MISSING — table exposed to cross-tenant queries via raw Supabase path.
- **P12**: `ALTER TABLE inventory_ledger ENABLE ROW LEVEL SECURITY` missing — even if P11 file exists, RLS must be enabled at table level.

| Bucket | Count | Notes |
|---|---|---|
| **DECISION_NEEDED** | 3 | spec/code drift, AC/Deferral conflict |
| **PATCH** | 16 | 15 HIGH + 1 MEDIUM |
| **DEFER** | 4 | spec-mandated deferrals |
| **DISMISS** | 6 | false positives / by design |

## Pre-flight reality check

| Claim | Author pre-flight | Actual | Status |
|---|---|---|---|
| ruff 0 errors | 0 | 0 | ✅ matches |
| import-linter 2 KEPT | 2 KEPT | 2 KEPT | ✅ matches |
| pytest passed | 975 | 985 | ⚠️ +10 (additional tests counted) |
| pytest skipped (CI-shim) | 91 | 119 | ⚠️ +28 (CI-shim count grew) |
| pytest failed | 0 | **1** | ❌ **A7 wire SDR drift detector FAILING** |
| 3중 게이트 clean | yes | **NO** | ❌ one HIGH patch item (P14) |
| A5 forward-lock 6 values fill | yes | yes | ✅ verified |
| A7 wire SDR overclaim | pass | **FAIL** | ❌ drift 82 (C24) |

## Decision-needed (3)

### D1. LedgerQuery NamedTuple shape spec/코드 drift
- Cluster: C19
- Spec: `LedgerQuery(period_key, product_id, closing_qty)` value object
- Actual: `LedgerQuery(sql, params, description)` SQL builder
- Both work; actual is better engineering. Service layer binds via SQLAlchemy `text().bindparams()`.

### D2. build_period_closing_query signature spec/코드 drift
- Cluster: C20
- Spec: `build_period_closing_query(tenant_id, period_key) -> str`
- Actual: `build_period_closing_query() -> LedgerQuery`

### D3. production_material_consumption event_type emit — spec self-contradiction
- Cluster: C18
- AC #4: dual emit (output + consumption)
- Deferral #9: deferred to Story 5.3+ BOM-aware reconciliation
- Code matches Deferral #9; whitelist has the value but no caller invokes it.

## PATCH (16, 15 HIGH + 1 MEDIUM)

### Critical (table safety — blocks done)
- **P2 [HIGH]**: `qty >= 0` CHECK blocks outbound events (1 file, 1 row)
- **P11 [HIGH]**: `0007_inventory_ledger_rls.sql` missing (1 file, ~25 lines)
- **P12 [HIGH]**: `ENABLE ROW LEVEL SECURITY` missing (1 file, 1 line)

### DB-level hardening (HIGH)
- **P1**: `event_id` missing `DEFAULT gen_random_uuid()`
- **P3**: AD-22 UNIQUE constraint (currently INDEX)
- **P4**: Idempotency partial unique index missing

### Carry-chain query (HIGH)
- **P5**: date/text join mismatch in CTE (broken query)
- **P6**: missing `opening_carried_stale_overwrite` filter
- **P7**: recursion depth + ORDER BY direction

### Service-layer wire (HIGH)
- **P8**: `uuid.uuid4()` violates AD-15 UUID v7 SSOT
- **P9**: `_assert_not_modifying` AST guard is dead code
- **P10**: substring error parsing fragile

### A5/A7 wire (HIGH)
- **P13**: `MonthlyInputStateResponse` 4 NEW ledger fields missing
- **P14**: SDR drift detector failing (drift 82)
- **P15**: `_compute_inventory_projection_for_state` dead append + unused param

### Test coverage (MEDIUM)
- **P16**: `test_audit_action_centralization.py` extension missing

## Defer (4, spec-mandated)

- W1: `production_material_consumption` emit deferred (Deferral #9)
- W2: TS mirror `apps/web/lib/l2-input-inventory-ledger.ts` deferred (5-3 vitest wire)
- W3: TS mirror parity tests 6 skipped (5-3 vitest wire)
- W4: `_emit_inventory_ledger_event_for_row` no isolated unit tests (integration coverage sufficient)

## Dismiss (6, false positives)

- R1: `_assert_not_modifying` substring false-positive (dead code, no caller)
- R2: Trigger `OLD.event_id` reference (correctly uses COALESCE)
- R3: `_validate_uuid7` accepts v4 (by design MVP)
- R4: `EXTRA_FORBIDDEN_CONFIG` module constant (no such constant exists)
- R5: `InventoryLedger.inserted_at` comment mismatch (correctly defaulted)
- R6: `PeriodClosingResponse` naming collision (correctly wrapped in handlers)

## CR Lessons Applied (positive)

- **CR 0-2 (RLS)**: pattern NOT fully applied — table RLS file missing (P11)
- **CR 1-1 (audit-first + idempotent)**: applied — `append_event` audit-first + idempotent
- **CR 2.1 (capability-gated type subset)**: applied — INVENTORY_LEDGER gate
- **CR 2.3 (extra='forbid')**: applied — 4 Pydantic schemas
- **CR 4-3 F-1 (async test pattern)**: applied — `asyncio.run` wrapper
- **CR 4-3 F-2 (SDR overclaim)**: violated — drift detector failing (P14)
- **CR 4-3 F-6 (A5 forward-lock)**: applied — 6 INVENTORY_LEDGER values fill
- **cr-5-1-lessons**: applied — pure kernel + service layer + 4 hooks wire

## Carry-forward to next agents

- **5-3 frontend toast sonner**: gated on A6 Story 0.5 plumbing (Epic 4 close-out retro A6 NEW 결정). 5-2 backend-only completion does not unblock 5-3.
- **Epic 11 reversal module**: actual reversal sequence INSERT = Epic 11 module authority. 5-2 wires entrypoint + audit marker only.
- **Epic 6 close-out**: `build_inventory_projection` legacy + `LEDGER_REFERENCE_QUERY_STUB` removal = Epic 6 retro. 5-2 ships swap completed.

## Recommended next actions

1. **HALT for D1+D2+D3 user decision** (3 cj-style questions).
2. After D1+D2+D3 resolved, decide patch handling:
   - (a) Apply all 15 HIGH + 1 MEDIUM patches immediately (full sweep)
   - (b) Apply critical 3 (P2/P11/P12) first, defer remaining as Action Items
   - (c) Walk through each patch one by one
3. Re-run 3중 게이트 after patches applied.
4. Update sprint-status.yaml: `5-2: review` → `done` (if all HIGH cleared) or `in-progress` (if patches deferred as Action Items).

## Story status recommendation

**Keep `5-2: review` until at minimum P11/P12 (RLS file + ENABLE ROW LEVEL SECURITY) + P2 (qty CHECK) are resolved.** These three are blocking — without them, the inventory_ledger table is unsafe at the DB layer.

The remaining PATCH items (P1, P3-P10, P13-P15) can be applied as a batch (similar to 5-1 review pattern: 13 applied + 16 carry-over).
