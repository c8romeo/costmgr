# Story 6.2 — Code Review Triage

**Skill:** bmad-code-review · **Step:** 3 (Triage) · **Story:** 6-2-monthly-closing-report
**Review mode:** full · **Spec:** `_bmad-output/implementation-artifacts/6-2-monthly-closing-report.md`
**Baseline commit:** `418ca2d` · **Reviewed:** `HEAD` (diff = 6838 lines / 44 files)

## Inputs

| Layer        | Output | Count | Format             |
| ------------ | ------ | ----- | ------------------ |
| Blind Hunter | prose  | 35    | markdown list      |
| Edge Case    | JSON   | 50    | location/trigger   |
| Auditor      | prose  | 21    | AC/constraint ref  |
| **Raw total** |       | **106** |                    |

Independent verification (ruff scoped + pytest collection + TS compile + V8 verifier execution) ran in parallel with the three layers. Every surviving finding below is anchored to a command output or a direct read of source.

## Disposition summary

| Bucket            | Count |
| ----------------- | ----- |
| decision_needed   | 0     |
| patch             | 12    |
| defer             | 5     |
| dismiss           | 89    |
| **Surviving**     | **17** |

> All Critical findings concentrate on a single systemic root cause: **four independent guardrails (backend `response_model`, TS unchecked `as` cast, vitest mocks shaped to the TS interface, parity-drift detectors neutered by `or True`) were each bypassed**, so the wire contract breaks end-to-end while every CI signal is green. The triage below treats the guardrails (not just the symptoms) as patch items.

---

## Severity ranking — surviving findings (17)

### HIGH (9)

#### H1 — V4 semantic bug: comparing `manufacturing_cost` against qty ⇒ permanent FAIL  `[patch]`
- **Source:** blind+edge+auditor
- **Location:** `packages/cost_engine/monthly_closing_report_aggregator.py:209-246`; `_query_fiscal_period_snapshot_aggregate` `apps/api/modules/m4_inventory/services/monthly_closing_report_service.py:684-702` returns KRW `manufacturing_cost` but the verifier treats it as a qty source.
- **Evidence:** Docstring at `:681` explicitly says *"Each product → total manufacturing_cost (PRD §6.1 산식 체인)"* — i.e. KRW, not qty. The verifier compares it for equality with ledger qty after `ROUND_HALF_EVEN` quantization → `ledger_q != closing_q` and `ledger_q != fiscal_q` triggers ⇒ `status = V4_STATUS_FAILED` for **every manufacturing tenant, every period**.
- **Why HIGH:** V4 is the read-only consistency check exposed to the user via `/monthly-closing-report/v4-verdict`. It will always read `failed` in production and the verifier is silently shipping a wrong-result wire.
- **Fix direction:** Either (a) add a 5th qty source (e.g. `fiscal_period_snapshots.engine_type='trad'.qty`) so the 4-source contract is honest, or (b) drop `fiscal_period_snapshot_aggregate` from the verifier call entirely and document 3-source semantics. The PRD §6.1 산식 체인 wording needs kjw's call before patching — **route this to 6-2 carry-over as a decision item** (see D1 below).
- **Decision call-out:** see `D1` below.

#### H2 — V4 verdict unreachable from panel: handler returns flat `dict(verdict)`, TS expects `{period_key, verdict, trace_id}` envelope  `[patch]`
- **Source:** blind+edge
- **Location:** `apps/api/modules/m4_inventory/handlers.py:809` (`return dict(verdict)`) vs `apps/web/lib/monthly-closing-report.ts:188-198` `MonthlyClosingReportV4Verdict { period_key; verdict; trace_id }`.
- **Evidence:** Backend returns a flat dict (`{status, failures, skip_reason_ko, verified_at, product_count, source_count}`). TS awaits `{period_key, verdict: {status, ...}, trace_id}`. Result: `v4_verdict = null` ⇒ panel's `v4_status === "FAIL"` branch never fires, even if the verifier were correct.
- **Why HIGH:** Blocks the entire V4 UX surface (panel shows no badge).
- **Fix direction:** Handler wraps in envelope: `return {"period_key": period_key, "verdict": dict(verdict), "trace_id": ctx.trace_id}`.

#### H3 — Wire contract break (3 sites): `currency_pair`, `closing_per_product[*]`, audit-trail entry  `[patch]`
- **Source:** blind+edge
- **Location:**
  - `monthly_closing_report_service.py:303-310` (`from_currency/to_currency/rate_source_ko`) vs `monthly-closing-report.ts:39-42` (`base/quote/source`)
  - `monthly_closing_report_service.py:316-327` (`opening_qty_krw/closing_qty_krw/delta_krw`) vs `monthly-closing-report.ts:101-110` (`opening_qty/closing_qty/delta_qty`)
  - `monthly_closing_report_service.py:374-379` (`{action, payload, occurred_at}` no `id`/`actor_id`) vs `monthly-closing-report.ts:170-176` (`{id, action, actor_id, created_at, payload}`)
- **Evidence:** Panel renders `{aggregate.currency_pair.base}/{aggregate.currency_pair.quote} @ {aggregate.currency_pair.source}` (`MonthlyClosingReportPanel.tsx:149-155`) → in production shows `undefined/undefined @ undefined`. Closing-per-product cells render `undefined` (TS uses `opening_qty`). Audit-trail React key uses `entry.id` ⇒ key collision + undefined `created_at`.
- **Why HIGH:** The read-only report is the only deliverable for PRD §F5 / §F5.2. With this break, every KRW/USD cell is blank and the audit trail is unrenderable.
- **Fix direction:** Backend payload fields align to TS mirror. Renaming the TS mirror to match the backend is **not** correct (backend has `_krw` suffix that must stay for AD-15 snake_case / type clarity).

#### H4 — AC #3 (5 NEW state fields + service extensions) entirely unimplemented  `[patch]`
- **Source:** auditor
- **Location:** Spec `6-2-monthly-closing-report.md:198-224` (AC #3) vs `apps/api/modules/m4_inventory/services/monthly_input_service.py` (zero edits in diff).
- **Evidence:** `git diff 418ca2d..HEAD -- apps/api/modules/m4_inventory/services/monthly_input_service.py` returns empty. Spec mandates `MonthlyInputStateResponse` 5 NEW fields and a `MonthlyInputService.get_monthly_closing_report` method — neither shipped.
- **Why HIGH:** AC #3 is one of four PRIMARY acceptance criteria (AC #1-#4). Story cannot be marked `done` with this gap.
- **Fix direction:** Implement the missing fields + method; or update spec AC #3 to reflect actual scope if 6-2 is decoupling from monthly-input. **Needs kjw's call** → routes to carry-over decision.

#### H5 — Broken V8 golden fixture: `v4_closing_period_pass_manufacturing.json` expects `passed`, verifier returns `failed`  `[patch]`
- **Source:** blind+edge
- **Location:** `packages/cost_engine/tests/regression_v8/fixtures/v4_closing_period_pass_manufacturing.json:1-28`; runner `tests/regression_v8/test_regression_v8_fixtures.py:31` (`assert V8_FIXTURE_COUNT == 18` and glob `*.json`).
- **Evidence:** Ran the real `verify_monthly_closing_report_consistency(...)` against the fixture dict: returned `{'status': 'failed', 'failures': [{...closing↔fiscal mismatch}, {...ledger↔fiscal mismatch}], ...}`. Runner only counts `.json` files — never loads or executes them, so the broken lock passed CI.
- **Why HIGH:** A11 mandate is byte-identical V8 fixture matrix. A "PASS" fixture that the verifier proves FAILs inverts the contract.
- **Fix direction:** Either fix the fixture's `fiscal_period_snapshot_aggregate` to be a qty (matching H1's resolution), or repurpose it as a known-FAIL golden with `expected_v4_status: "failed"` and matching `expected_v4_failures[]`. Replace `PLACEHOLDER_LOCK_WILL_BE_REGENERATED_BY_PUBLISHER` with the real SHA after the fix.

#### H6 — Pre-existing 6-1 runtime crash carried into 6-2 surface area  `[patch]`
- **Source:** edge
- **Location:** `closing_period_service.py:528` (`ledger_service.count_period_events(...)`), `:531` (`ledger_service.query_period_closing_snapshot_all(...)`); `closing_period_snapshot_verifier.py:146`.
- **Evidence:** `LedgerService.count_period_events` / `.query_period_closing_snapshot_all` have zero definitions under `packages/services/m5_ledger/`. Since 6-2's monthly closing report reuses the same data path (4-source join), any tenant that hits a closing-period route will raise `AttributeError` in production.
- **Why HIGH:** Pre-existing but newly reachable from the 6-2 monthly-closing-report hot path.
- **Fix direction:** Implement the two missing LedgerService methods (or stub them as CR 5-3's "shared kernel" pattern) — defer to a dedicated Story if too large.

#### H7 — Three NEW backend routes ship without `response_model`  `[patch]`
- **Source:** auditor
- **Location:** `apps/api/modules/m4_inventory/handlers.py:711-721,748-758,782-792` (3 routes) vs every pre-existing m4 route that declares `response_model` (e.g. `ClosingPeriodAuditTrailResponse` at `:667-670`).
- **Evidence:** All 3 NEW routes return `dict[str, object]` with no `response_model=`. This is the only m4 module where this is done.
- **Why HIGH:** `response_model` is the schema-enforcement boundary (CR 1.1 lesson). Without it, the backend cannot refuse drift at the FastAPI boundary, which is why H3 surfaced as a runtime breakage instead of a 422.
- **Fix direction:** Add `response_model=MonthlyClosingReportResponse` (and the other two) using the project's per-module `schemas.py` convention (not `pydantic_schemas.py` — that's an Auditor false positive I dismissed; the project convention is per-module `schemas.py`).

#### H8 — Dead `MonthlyClosingReportKrwUsdRateMissingError` exception class  `[patch]`
- **Source:** blind
- **Location:** Defined in `monthly_closing_report_service.py` (definition found by grep) but `grep -n "raise MonthlyClosingReportKrwUsdRateMissingError"` returns **empty**.
- **Evidence:** Spec promises a 422 on missing rate. Service silently returns `currency_pair: null` and HTTP 200.
- **Why HIGH:** Capability-gated observability promises are not enforced; downstream code (panel) renders blank instead of surfacing the failure.
- **Fix direction:** Either raise the exception in the missing-rate branch and wire a 422 handler, or remove the dead class and update spec.

#### H9 — `verify_monthly_closing_report_v4` returns raw status (not upper-cased) ⇒ TS `'PASS'|'FAIL'|'SKIP'` discriminator mismatch  `[patch]`
- **Source:** blind
- **Location:** `monthly_closing_report_service.py:442` returns `v4_verdict_dict` (status is `'passed'|'failed'|'skipped'` from `monthly_closing_report_aggregator.py:73-75`); TS expects `'PASS'|'FAIL'|'SKIP'` (`monthly-closing-report.ts:188`).
- **Evidence:** Panel checks `v4_status === "FAIL"` / `=== "PASS"` (`MonthlyClosingReportPanel.tsx:204-219`).
- **Why HIGH (downgraded by H2):** Independent of H2's envelope break, status casing is also wrong. Once H2 is fixed, status still won't match — both must be patched.
- **Fix direction:** Upper-case in the kernel (`V4_STATUS_PASSED = "PASS"`) or in the service (`v4_verdict_dict["status"] = v4_verdict_dict["status"].upper()`).

### MEDIUM (6)

#### M1 — Audit-trail V4 branch unreachable in production  `[patch]`
- **Source:** blind+edge
- **Location:** `monthly_closing_report_service.py:350-372`. The branch `target_table = 'verification' AND payload->>'action_name' = 'verify_v4_closing_period_consistency'` never matches because `_emit_audit_v4_dispatched` (`:785-809`) writes to `verification_log` (via `ActionClass.VERIFICATION`) **without** an `action_name` key in its payload.
- **Evidence:** Spec CR 1.1 says audit-first must be observable; the V4 audit row is queryable only because the fallback `target_table IN ('monthly_closing_report','closing_period')` covers the view emission, but the V4-specific dispatch row is invisible to the audit-trail route.
- **Fix direction:** Add `action_name: 'verify_v4_closing_period_consistency'` to the `_emit_audit_v4_dispatched` payload.

#### M2 — `rate_as_of` and `rate_source_ko` fall back to `"1970-01-01"` / `"한국은행"` instead of raising  `[patch]`
- **Source:** blind
- **Location:** `monthly_closing_report_service.py:606-643` `_query_currency_pair` defaults.
- **Evidence:** Silent fallback hides missing-rate conditions and contradicts H8.
- **Fix direction:** Raise / return None on missing, let the caller decide.

#### M3 — Test-integrity regression: 4 `or True` vacuous assertions + a PASS-named test asserting FAILED  `[patch]`
- **Source:** blind+edge
- **Location:**
  - `tests/api/m4_inventory/test_monthly_closing_report_service.py:179,202`
  - `tests/integration/test_monthly_closing_report_label_consistency.py:82,90`
  - `tests/cost_engine/test_monthly_closing_report_aggregator.py:79-99` (test name `test_verify_v4_pass_all_three_sources_match` asserts `V4_STATUS_FAILED`, with comment `# cost basis — NOT qty!` — confession in source)
  - `apps/web/__tests__/monthly-closing-report-panel.test.tsx:76-105` (mocks shaped to TS interface, not real payload — that's why green vitest hides H3)
- **Evidence:** `tests/integration/test_product_type_change_consistency.py:25,188` documents this exact anti-pattern having been previously caught (per CR 5-1 lesson). All `or True` and the broken assertion must be fixed.
- **Fix direction:** Replace each `or True` with the real assertion; rewrite the PASS-named test to either rename or invert; rebuild panel mocks from a fixture-shaped payload that matches the backend's actual wire.

#### M4 — A5 audit_action drift detectors not extended  `[defer]`  → see also D2
- **Source:** auditor
- **Location:** `apps/api/core/audit_action.py:55,60-61,218` adds `VERIFICATION_LOG` target table, `CLOSING_PERIOD` / `MONTHLY_CLOSING_REPORT` action classes, and `MonthlyClosingReportAction` Literal — but no test in `tests/api/test_audit_action_drift.py` or equivalent asserts drift detection for the new entries.
- **Why MEDIUM (not HIGH):** This is a 6.1/5.3 pattern carry-over (A5 forward-lock partial). Deferred fixes historically accumulate to the next A5 sweep.
- **Fix direction:** Carry to next A5 sweep OR add 3-line drift-detector assertions in this patch batch.

#### M5 — Docs drift: capability-matrix header v1.9 (spec said v1.8), nonexistent fixture reference, route drift  `[patch]`
- **Source:** auditor
- **Location:**
  - `docs/capability-matrix.md` header says v1.9 vs spec mandate v1.8; references `closing-period-fixture-1.json` (does not exist)
  - `docs/architecture-inventory.md:289-292` documents `/closing-period/report*` (actual: `/monthly-closing-report*`)
  - `docs/closing-period.md:193`, `docs/monthly-closing-report.md:43,270`, `docs/conventions.md:608` (maps `monthly_closing_report_viewed` to `ActionClass.CLOSING_PERIOD`; code uses `MONTHLY_CLOSING_REPORT`)
- **Why MEDIUM:** Docs drift only blocks discovery, not runtime correctness.
- **Fix direction:** Sweep + bump capability-matrix to v1.9 (or fix spec wording) in this patch batch.

#### M6 — SDR overclaim: ruff scoped 21 errors (claim: clean); 1 pytest failure (claim: 0 failed)  `[patch]`
- **Source:** independent gate measurement
- **Location:** `_bmad-output/implementation-artifacts/6-2-monthly-closing-report.md:407,492,591`
- **Evidence:** `uv run ruff check --no-fix` on the 10 changed Python files = **21 errors** (mostly F841 unused + SIM222 `or True` + W292 trailing newline; 14 auto-fixable). pytest run = **1 failed / 1226 passed / 127 skipped** (`tests/integration/test_sdr_test_count_drift.py::test_max_sdr_claim_matches_pytest_collection`).
- **Why MEDIUM:** CI failure is on a meta-test (the SDR drift detector itself), not on feature code. But the spec's claim that "All checks passed" is materially false and must be corrected or the SDR must be regenerated.
- **Fix direction:** Either (a) bring test/ruff counts to match the SDR claim, or (b) regenerate the SDR with corrected numbers before sprint-status sync.

### LOW (defer / dismiss)

#### W1 — `apps/api/modules/m4_inventory/services/__init__.py` re-export of new service  `[defer]`
- Pre-existing pattern (other services have similar `__init__` re-exports). Doc-only addition in 6-2; not a defect.

#### W2 — `_fixture_lock_sha256` placeholder string `PLACEHOLDER_LOCK_WILL_BE_REGENERATED_BY_PUBLISHER`  `[defer]`
- Pre-existing 5-3 pattern (deferred to A11 publisher). Not a 6-2-introduced regression. Will be regenerated by the lockfile publisher once H5's fixture content is fixed.

#### W3 — TS-side `formatKrwUsd` helper inside `MonthlyClosingReportPanel.tsx` bypassing parity helper  `[defer]`
- Pre-6-2 pattern (the panel does its own KRW/USD formatting). The `monthly-closing-report-parity.ts` exports `parityFormatPeriodClosingKrwUsd` but it's **imported only by the route test**, never on the production path. Refactor to parity helper is a Story 0.5 plumbing follow-up.

#### W4 — 6 of 8 spec-claimed test files delivered  `[defer]`
- Spec lines 312/407/492 mention 8 NEW test files; diff ships 6 (`test_regression_v8_fixtures.py`, `test_monthly_closing_report_aggregator.py`, `test_monthly_closing_report_service.py`, `test_monthly_closing_report_label_consistency.py`, `monthly-closing-report-panel.test.tsx`, `monthly-closing-report-route.test.tsx`). Two spec-mentioned files (likely `test_v8_runner_e2e.py` and a frontend Playwright spec beyond what was shipped) missing. Defer to follow-up sweep.

#### W5 — `_query_currency_pair` `industry` filter (`engine_type='trad'`) may over-restrict service tenants  `[defer]`
- V4 SKIP gate for industry='service' is correctly implemented (`monthly_closing_report_service.py:417,720-736`). However the `fiscal_period_snapshots` query at `:691` hard-codes `engine_type = 'trad'`, which excludes service-industry snapshots entirely. If service tenants later need this route, they'll see zeros. Defer to industry-extension story.

---

## Dismissed (89)

Top dismissals by category:

- **Null-guard crash claims (4) — false positives.** Edge-case-hunter reported `occurred_at` ISO-format crash when NULL. The code at `monthly_closing_report_service.py:378` has `row[2].isoformat() if row[2] is not None else None` — guard exists.
- **`pydantic_schemas.py` placement (1) — spec wording.** Auditor flagged missing `response_model`. The project convention is per-module `schemas.py`; the auditor's `pydantic_schemas.py` claim is incorrect and was replaced by H7.
- **`REPORT_VIEW_MODE_READY` casing (1) — parity correct.** Auditor flagged `'READY'`/`'PARTIAL'`/`'EMPTY'` (TS) vs Python. Both Python (`monthly_closing_report.py:71-73`) and TS (`monthly-closing-report.ts:24-26`) use upper-case — parity holds.
- **Backend capability-gate not enforced (1) — false positive.** All 3 NEW routes have `Depends(require_capability(Capability.MONTHLY_CLOSING_REPORT))`. Gate is correctly enforced.
- **TS `as` cast at `server-api.ts:233,268,303` (3) — folded into H7's fix narrative.** The cast itself is acceptable as a project pattern; the contract break (H3) is the real defect. Don't remove the cast — remove the contract mismatch.
- **TS-side docstring mirror claim (1) — wording.** `packages/services/m4_inventory/monthly_closing_report.py:120-121` says `CurrencyPair` "Mirrors TS `apps/web/lib/monthly-closing-report.ts::CurrencyPair`". The TS `CurrencyPair` exists at line 39-42 but with **different field names** (the actual contract break is H3). This is a docstring-staleness issue already covered by H3 — no separate dismiss entry needed.
- **Naming collision V4 slots (1) — false positive on 6-2.** The 6-1 V4 slot collision (cost/income reconciliation) does not apply to 6-2's V4 wire (qty verification, not cost/income).
- **Bulk Adversarial/Edge items (76) — duplicate or already-covered.** Many findings overlap one of H1-H9; after dedup the unique set collapses to 17.

---

## Decision items requiring kjw

### D1 — V4 qty source: 5th wire or drop `fiscal_period_snapshot_aggregate` from V4 contract?  `[decision_needed → patch via carry-over]`
- H1 + H5 are bound together. PRD §6.1 산식 체인 wording says `fiscal_period_snapshots` holds `manufacturing_cost` (KRW), not qty. Two coherent fixes:
  - **(a) Honest 4-source:** Add a new `fiscal_period_snapshots.qty` (or new column on `closing_period_snapshots`) so V4 has 4 qty sources. Then fix the V8 fixture to use qty values.
  - **(b) Honest 3-source:** Drop `fiscal_period_snapshot_aggregate` from the V4 verifier call; update spec §V4 and PRD to say "V4 verifies 3 qty sources + product whitelist" and repurpose the V8 fixture as a known-FAIL golden for the 3-source contract.
- Needs kjw's call before patching. Defaulting to (b) for the carry-over plan, but flagging explicitly.

### D2 — Add A5 drift-detector assertions now or defer to next A5 sweep?  `[decision_needed → patch via carry-over]`
- M4 is a 6.1/5.3 carry-over pattern. A5 forward-lock discipline says "add the drift assertion in the same PR that adds the action class". If kjw wants strict A5, add 3 lines to `tests/api/test_audit_action_drift.py`. Otherwise defer to next sweep.
- Defaulting to defer per the 6.1 carry-over pattern.

### D3 — How to handle AC #3 monthly-input-service extension?  `[decision_needed → patch via carry-over]`
- H4 says AC #3 is unimplemented (zero edits to `monthly_input_service.py`). Two coherent fixes:
  - **(a) Implement:** Add the 5 NEW state fields + `get_monthly_closing_report` method on `MonthlyInputService`.
  - **(b) De-scope:** Update spec AC #3 to reflect that 6-2 ships only the standalone `MonthlyClosingReportService` and the monthly-input extension is deferred to Story 6.3+.
- Needs kjw's call.

---

## Sprint-status intent

After triage + apply: story `6-2` will be `review` → `in-progress` (carry-over patch batch) or `done` (if kjw opts for the lighter sweep and the H1/H4/D1/D3 decisions resolve to defer).

Carrying the remaining patches via the same sweep pattern as Story 6.1 R4 triage (commit `f069961`).
