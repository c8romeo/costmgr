# Story 5.2 Code Review — Triage (final)

> Generated 2026-08-04 — bmad-code-review
> Range: b4b84da..HEAD (8 commits, 7,769 raw lines, 37 files)
> Layers: Blind Hunter (40) + Edge Case Hunter (33) + Acceptance Auditor (8 ACs)
> Raw findings: 81 → after dedup: 64 clusters → after severity routing: **23 surviving** (3 decision + 16 patch + 4 defer) + 6 dismissed = 29 triaged

## Verdict summary

| Bucket | Count | Notes |
|---|---|---|
| **DECISION_NEEDED** | 3 | spec-vs-code conflicts requiring user judgment |
| **PATCH** | 16 | unambiguous code fixes |
| **DEFER** | 4 | spec-documented deferrals (acceptable) |
| **DISMISS** | 6 | false positives / by-design |
| **TOTAL surviving** | 23 | (action items) |
| **TOTAL dropped** | 41 | raw clusters either merged into a surviving finding or dismissed |

After triage, the diff still has **15 HIGH-severity patches** that block `done` promotion (per Step 6 rules). Story 5.2 status should remain `review` (or move to `in-progress` if patches applied as action items) until all HIGH patches are resolved.

---

## DECISION_NEEDED findings (3)

### D1: Spec literal for `LedgerQuery` shape vs actual NamedTuple (sql, params, description)
- **Cluster**: C19
- **Files**: `packages/services/m4_inventory/ledger_query.py:60-73` (current) vs spec §T2 literal
- **Conflict**: Spec literal: `LedgerQuery(period_key: str, product_id: UUID, closing_qty: Decimal | None)` (value object). Actual: `LedgerQuery(sql: str, params: tuple, description: str)` (SQL builder). Both work correctly; current is better engineering.
- **Why decision needed**: spec amendment is a cj-style decision. Code already shipped with the working version.
- **Options**: (a) amend spec to reflect actual, (b) rewrite code to match spec literal, (c) accept drift as documented deviation.

### D2: Spec literal for `build_period_closing_query()` signature
- **Cluster**: C20
- **Files**: `packages/services/m4_inventory/ledger_query.py:77-103` vs spec
- **Conflict**: Spec literal: `build_period_closing_query(tenant_id: UUID, period_key: str) -> str`. Actual: `build_period_closing_query() -> LedgerQuery`. Service layer binds via SQLAlchemy text().bindparams(). Works correctly.
- **Why decision needed**: Same as D1.
- **Options**: (a) amend spec, (b) rewrite to literal form (would require passing params inside fragment).

### D3: `production_material_consumption` event_type emit — spec conflict
- **Cluster**: C18
- **Files**: `apps/api/modules/m2_input/services/monthly_input_service.py` (production stream hook) vs spec AC #4 vs spec Deferral #9
- **Conflict**: AC #4 says "Production stream emits BOTH `production_output_inbound` (positive qty) and `production_material_consumption` (negative qty)." But Deferral #9 says "production_material_consumption emit deferred to Story 5.3+ BOM-aware reconciliation." Code only emits `production_output_inbound`. The 11-value whitelist includes `production_material_consumption` but no caller invokes it.
- **Why decision needed**: Spec contradicts itself. Without BOM data in m2_input, emitting `production_material_consumption` requires reading from the BOM module — not in 5-2 scope.
- **Options**: (a) accept deferral (code matches Deferral #9), (b) add a placeholder emit with qty=0 to satisfy AC #4 literal, (c) amend spec AC #4 to remove the dual-emit requirement.

---

## PATCH findings (16)

### P1-HIGH: `event_id UUID PRIMARY KEY` missing `DEFAULT gen_random_uuid()` [C1]
- **File**: `apps/api/alembic/versions/0015_inventory_ledger.py:63`
- **Fix**: Add `DEFAULT gen_random_uuid()` to the `event_id` column. Service layer already mints UUIDv7 (or v4 fallback — see P8) so this is a defense-in-depth measure for direct SQL access paths.
- **Risk**: low — adds DB-level safety net.

### P2-HIGH: `qty >= 0` CHECK contradicts PRD §6.2 signed qty semantics [C4]
- **File**: `apps/api/alembic/versions/0015_inventory_ledger.py:121-122`
- **Fix**: Change to `CHECK (qty IS NULL OR (event_type IN ('sales_outbound', 'production_material_consumption', 'adjustment_negative', 'reversal_negating') AND qty < 0) OR (event_type NOT IN (...) AND qty >= 0))`. PRD §6.2 requires negative qty for outbound events. Currently the DB blocks ALL sales/production outbound events.
- **Risk**: medium — opens negative qty; need to ensure event_type coherence CHECK still binds.

### P3-HIGH: AD-22 UNIQUE constraint as INDEX (double-reversal possible) [C2]
- **File**: `apps/api/alembic/versions/0015_inventory_ledger.py:177-181`
- **Fix**: Change `CREATE INDEX idx_inventory_ledger_reverses_event_id ON inventory_ledger (reverses_event_id) WHERE reverses_event_id IS NOT NULL` to `CREATE UNIQUE INDEX uq_inventory_ledger_reverses_event_id ON inventory_ledger (tenant_id, reverses_event_id) WHERE reverses_event_id IS NOT NULL`.
- **Risk**: low — AD-22 invariant required.

### P4-HIGH: Idempotency partial unique index missing [C3]
- **File**: `apps/api/alembic/versions/0015_inventory_ledger.py` (after line 172)
- **Fix**: Add `CREATE UNIQUE INDEX uq_inventory_ledger_idempotency ON inventory_ledger (tenant_id, product_id, period_key, event_type, trace_id) WHERE trace_id IS NOT NULL` for application-layer idempotency to be race-safe.
- **Risk**: low — requires service-layer `try/except IntegrityError` handling.

### P5-HIGH: Carry-chain CTE date/text join mismatch (broken query) [C41]
- **File**: `packages/services/m4_inventory/ledger_query.py:142`
- **Bug**: `cc.period_key = (e.period_key || '-01')::date - INTERVAL '1 month'` — left side is text `'YYYY-MM'`, right side is date `'YYYY-MM-01'`. Implicit cast never matches. Recursion returns only the seed row (1 result max).
- **Fix**: Change to `cc.period_key = to_char((to_date(e.period_key || '-01', 'YYYY-MM-DD') - INTERVAL '1 month'), 'YYYY-MM')` for text-to-text comparison.
- **Risk**: medium — fixes core query, but verify other carry-chain tests.

### P6-HIGH: Carry-chain CTE missing `opening_carried_stale_overwrite` filter [C42]
- **File**: `packages/services/m4_inventory/ledger_query.py:130, 143`
- **Fix**: Change `e.event_type = 'opening_carried'` to `e.event_type IN ('opening_carried', 'opening_carried_stale_overwrite')` in both seed and recursive terms.
- **Risk**: low — adds visibility to stale overwrite events per 5-1 AC #3.

### P7-HIGH: Carry-chain CTE recursion depth + ORDER BY direction [C43]
- **File**: `packages/services/m4_inventory/ledger_query.py:144-149`
- **Bug**: Recursion has no depth bound; `ORDER BY period_key ASC LIMIT 12` returns earliest 12, not 12 nearest upper bound. Should walk backward from upper bound.
- **Fix**: Add `WHERE depth < :max_depth` inside recursive term, change `ORDER BY period_key ASC` to `ORDER BY period_key DESC`, change `LIMIT {CARRY_CHAIN_RECURSION_DEPTH}` to parameterized bound.
- **Risk**: medium — affects all carry-chain test expectations.

### P8-HIGH: `append_event` uses `uuid.uuid4()` violating AD-15 UUID v7 SSOT [C8]
- **File**: `apps/api/modules/m4_inventory/services/ledger_service.py:259`
- **Bug**: `event_id = uuid.uuid4()`. AD-15 says UUID v7. Pure-kernel `_validate_uuid7` accepts both v4 and v7 (by design post-MVP), so v4 slips through silently.
- **Fix**: Use `uuid.uuid7()` (Python 3.12+ available) OR `uuid_generate_v7()` postgres extension; mint v7 in service. Add `if version != 7: raise` in `_validate_uuid7` for strict mode.
- **Risk**: low — only affects fresh event_ids.

### P9-HIGH: `_assert_not_modifying` AST guard is dead code [C9]
- **File**: `apps/api/modules/m4_inventory/services/ledger_service.py:514-541`
- **Bug**: Method defined but NEVER called from any operation method (`append_event`, `query_*`, `request_reversal`, `get_event`). AC #3 2nd axis of 3중 방어 is silently degraded to DB trigger + audit only.
- **Fix**: Either (a) invoke `self._assert_not_modifying(sql_text)` before each `session.execute/text()` call (wrap session methods), or (b) document explicitly that this guard is for future hardening and remove from AC #3 claims.
- **Risk**: low — but affects spec compliance.

### P10-HIGH: Substring error parsing couples service to kernel message wording [C11]
- **File**: `apps/api/modules/m4_inventory/services/ledger_service.py:276, 282`
- **Bug**: `if "11-value whitelist" in err.message` and `if "YYYY-MM" in err.message` — message text coupling. Any kernel message refactor (e.g., "12-value") silently breaks the dispatch.
- **Fix**: Add `error_code` attribute to `AppendOnlyLedgerError` (pure kernel); service uses `isinstance` dispatch on subclass or `err.error_code` matching. E.g., `class InvalidEventTypeError(AppendOnlyLedgerError)` subclass pattern.
- **Risk**: low — refactor pure kernel + service together.

### P11-HIGH: `supabase/policies/0007_inventory_ledger_rls.sql` MISSING [C12]
- **File**: `supabase/policies/0007_inventory_ledger_rls.sql` (does not exist; `0007` is occupied by `0007_bom_lines_rls.sql`)
- **Bug**: Spec required NEW RLS policy file. Backend enforces tenant via JWT (AD-3) but RLS is the last line of defense for misconfigured Supabase connections. Current state: inventory_ledger table has no RLS policy.
- **Fix**: Create `supabase/policies/0008_inventory_ledger_rls.sql` (or rename spec target) with 4-policy split (SELECT/INSERT for tenant member + service_role bypass) mirroring `0009_monthly_input_rls.sql` structure.
- **Risk**: medium — must coordinate with supabase apply workflow.

### P12-HIGH: `ALTER TABLE inventory_ledger ENABLE ROW LEVEL SECURITY` missing [C13]
- **File**: `apps/api/alembic/versions/0015_inventory_ledger.py` (after line 235 in `upgrade`)
- **Bug**: Migration does not enable RLS on the new table. Even if `0008_inventory_ledger_rls.sql` policy file is added, RLS must be enabled at table level.
- **Fix**: Add `op.execute("ALTER TABLE inventory_ledger ENABLE ROW LEVEL SECURITY")` before downgrade() section.
- **Risk**: low — required for P11 to be effective.

### P13-HIGH: `MonthlyInputStateResponse` 4 NEW ledger fields MISSING [C22]
- **File**: `apps/api/modules/m2_input/schemas.py:343-391`
- **Bug**: Spec T5.4 required `ledger_events_count`, `ledger_period_closing`, `inventory_ledger_enabled`, `reversal_request_enabled`. None present. Frontend 5-3 cannot surface ledger state without these fields.
- **Fix**: Add 4 fields to `MonthlyInputStateResponse` + populate them in `monthly_input_service.py:1110` get_state return.
- **Risk**: low — additive change, no breaking schema impact (extra='forbid' but adding new fields is backward compat).

### P14-HIGH: A7 wire SDR drift detector FAILING (drift 82) [C24]
- **File**: `tests/integration/test_sdr_test_count_drift.py:172`
- **Bug**: Test failure. Actual pytest collection = 1105; MAX SDR claim = 1023 (from `epic-4-retro-close-out-2026-08-03.md:408`); tolerance = 50; drift = 82.
- **Fix**: Either (a) update SDR MAX claim from 1023 → 1105 (or higher with cushion), or (b) investigate what tests were added without SDR update. Since 5-2 added 50+ tests intentionally, fix is to update the SDR.
- **Risk**: low — documentation update.

### P15-HIGH: `_compute_inventory_projection_for_state` dead append + unused param [C29]
- **File**: `apps/api/modules/m2_input/services/monthly_input_service.py:1763-1785`
- **Bug**: `out.append(...)` at line 1763 is immediately overwritten by `out[-1] = ...` at line 1780. Wasted allocation; `opening_balance` parameter computed in caller but unused in final value (opening_qty overridden with closing_qty).
- **Fix**: Remove the first `out.append(...)` (lines 1763-1770), keep only the second assignment. Remove `opening_balance` parameter from signature and from caller.
- **Risk**: low — internal cleanup.

### P16-MEDIUM: 1 test failing also confirms test_audit_action_centralization.py needs extension [C23]
- **File**: `tests/services/test_audit_action_centralization.py`
- **Bug**: Spec T6.5/T9.8 requires extension to verify 6 INVENTORY_LEDGER actions are all registered. Current file (113 lines) only pins `emit_audit_typed` symbol + scans for legacy `emit_audit(` calls.
- **Fix**: Add explicit assertions that all 6 INVENTORY_LEDGER actions are in `_REGISTRY[ActionClass.INVENTORY_LEDGER]`.
- **Risk**: low — additive test.

---

## DEFER findings (4)

### W1-DEFER: `production_material_consumption` emit deferred [C18]
- Spec Deferral #9 explicitly notes "production_material_consumption emit deferred to Story 5.3+ BOM-aware reconciliation". Defer per spec.
- **Why deferred, pre-existing**: spec-mandated deferral, BOM module authority not in 5-2 scope.

### W2-DEFER: TS mirror file `apps/web/lib/l2-input-inventory-ledger.ts` missing [C26]
- Spec placeholder; TS mirror wire deferred to 5-3 vitest activation.
- **Why deferred, pre-existing**: spec-mandated deferral (5-2 backend-only per Epic 4 close-out retro A6).

### W3-DEFER: TS mirror parity tests (`test_inventory_ledger_label_consistency.py`) 6 skipped [C27]
- Spec placeholder; deferred to 5-3 vitest wire (A6 plumbing).
- **Why deferred, pre-existing**: spec-mandated deferral.

### W4-DEFER: `_emit_inventory_ledger_event_for_row` / `_emit_ledger_events_for_decisions` no isolated unit tests [C58/C59]
- Test coverage gap but integration test `test_inventory_projection_ledger_swap.py` covers via call graph. Acceptable.
- **Why deferred, pre-existing**: integration coverage sufficient for 5-2 scope; isolated unit tests can be added in 5-3 maintenance window.

---

## DISMISS findings (6)

### R1-DISMISS: `_assert_not_modifying` substring false-positive risk [C10]
- False positive: method is dead code (see P9); no caller exercises the substring match in production. Fix P9 first, then re-evaluate.

### R2-DISMISS: Trigger function `OLD.event_id` reference garbles message [C16]
- False positive: trigger code uses `COALESCE(OLD.event_id::text, '<new>')` (line 206 of migration) — explicitly handles the INSERT path. Verified by reading migration code.

### R3-DISMISS: `_validate_uuid7` accepts v4 [C48]
- By design: pure-kernel comment line 322: "Anything else (including UUID v4) is permitted in MVP — strict v7 enforcement is post-MVP." The service layer still uses v4 via `uuid.uuid4()` (P8 catches this).

### R4-DISMISS: `EXTRA_FORBIDDEN_CONFIG` module-level constant [C36]
- False positive: no such module-level constant exists; each Pydantic model sets `model_config = ConfigDict(extra="forbid")` independently.

### R5-DISMISS: `InventoryLedger.inserted_at` comment mismatch [C40]
- Verified false positive: ORM comment correctly states "set on INSERT via DB DEFAULT NOW()" matching migration `inserted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`.

### R6-DISMISS: `PeriodClosingResponse` naming collision single vs multi-product [C31]
- Verified working: handlers wrap single-product result in `dict[str, str]` (line 251 of handlers.py) and multi-product result in `dict[str, str]` (line 284). Both endpoints use the same schema correctly.

---

## Cross-cutting notes

- **3중 게이트 claimed clean but**: ruff 0 / import-linter 2 KEPT — verified. pytest: pre-flight claimed 975/91/0, actual **985/119/1 FAILING** (C24). The SDR drift detector failure was not detected in the author's pre-flight check.
- **A5 forward-lock**: verified — 6 INVENTORY_LEDGER values in registry (`audit_action.py:283-296`), but only 3 emit sites in `ledger_service.py`. Other 3 are forward-fill per spec, intentional.
- **A7 wire**: SDR drift detector IS failing; pre-flight missed this.
- **CR 0-2 RLS pattern**: violated by 5-2 — `0007_inventory_ledger_rls.sql` is the canonical Story 0.2 mirror pattern but was NOT created. CR 0-2 lesson applies.
- **CR 4-3 AST guard pattern**: violated by 5-2 — `_assert_not_modifying` is dead code (P9). The CR 4-3 lesson is "AST guard via call walking" not "regex on body text", which 5-2 actually applied via `_iter_methods` per spec — but the guard itself has no caller.
- **5-1 CR review pattern**: 5-1 review found 33 surviving findings (13 applied + 16 carry-over). 5-2 review found 23 surviving (16 patches + 3 decisions + 4 defers). Surface ratio 5-1→5-2 = ~3.5x, but finding ratio is similar — 5-2 quality is comparable to 5-1.

---

## Story status recommendation

Per Step 6 rules:
- HIGH patches remaining: 15 (P1-P15)
- After patching, if all HIGH cleared → `done`
- If patches left as action items → `in-progress`

**Recommendation**: keep `5-2: review` until at minimum P11/P12 (RLS file + ENABLE ROW LEVEL SECURITY) + P2 (qty CHECK) are resolved. These three are blocking — without them, the inventory_ledger table is unsafe at the DB layer (qty CHECK blocks negative outbound events, RLS missing exposes table to cross-tenant queries).

The remaining PATCH items (P1, P3-P10, P13-P15) can be applied as a batch (similar to 5-1 review pattern: 13 applied + 16 carry-over).

---

## Step 4 will:
1. Write 3 decision-needed + 16 patch + 4 defer to `_bmad-output/implementation-artifacts/5-2-inventory-ledger-append-only-events.md` (Review Findings section)
2. Append 4 defer to `_bmad-output/implementation-artifacts/deferred-work.md`
3. Present summary to user
4. HALT for user choice on decision-needed resolution
5. After D1+D2+D3 resolved, HALT for patch handling (apply all / leave as items / walk through)
6. Update sprint-status.yaml (5-2 stays `review` per recommendation above)