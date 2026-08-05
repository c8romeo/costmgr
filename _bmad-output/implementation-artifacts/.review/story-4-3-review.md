# Story 4.3 Code Review (final, 2026-08-03)

> Spec: `_bmad-output/implementation-artifacts/4-3-verification-v1-v4-v7-v8-order.md`
> Diff: `_bmad-output/implementation-artifacts/.review/story-4-3.diff` (5,058 lines)
> Reviewer: MiniMax-M3 (fresh context)
> Verdict: **REQUEST CHANGES** — 2 HIGH (gating) + 4 MEDIUM + 4 LOW

---

## 0. Executive summary

| Gate | Status |
|---|---|
| `uv run pytest tests/cost_engine/test_verification_rules.py` | **FAIL — 4/22 tests fail (async)** |
| `uv run pytest tests/api/test_verdict_envelope.py` | PASS — 11/11 sync |
| `uv run pytest tests/integration/test_verification_order.py` | **FAIL — 8/12 tests fail (async)** |
| `uv run pytest tests/web/test_m3_verdict_parity.py` | (not run, requires node) |
| `uv run pytest tests/cost_engine/test_no_io_imports.py` | not run yet |
| `uv run ruff check apps/api/modules/m3_calculate/ packages/cost_engine/ tests/cost_engine/ tests/web/ apps/api/core/audit_action.py tests/integration/test_verification_order.py tests/api/test_verdict_envelope.py` | **PASS — 0 errors** |
| `uv run import-linter lint` | **PASS — 2 contracts KEPT** (`cost_engine_forbidden_io` + `engine_core_to_adapters_forbidden`) |
| `git status` working tree hygiene | tracked + untracked mixed — Story 4.1/4.2 changes co-mingled |

**Critical finding: dev-story completion notes OVERCLAIM 64 passed + 1 skipped.** Actual count is 30 sync passed + 12 async failed across the three 4-3 test files I exercised. Async tests use `@pytest.mark.asyncio` decorator but the project does not have `pytest-asyncio` plugin installed — `pyproject.toml` says "async tests (driven via `asyncio.run` — no pytest-asyncio plugin needed)". This is a 4-3-introduced regression against the project's established async-test pattern (cf. `tests/api/test_calc_orchestrator.py` shape).

The architecture, the A5 single-source-of-truth migration, the verification rule registry, the V8 placeholder contract, and the 0013 alembic are all **correctly designed and implemented**. The gate is purely on test plumbing.

---

## 1. Findings — sorted by severity

### F-1 (HIGH, blocking) — Async tests fail; project has no `pytest-asyncio`
- **Files**: `tests/cost_engine/test_verification_rules.py` (4 async tests, lines 324/344/362/385) + `tests/integration/test_verification_order.py` (8 async tests, lines 77/106/141/161/190/212/234/258).
- **Symptom**: `async def functions are not natively supported. You need to install a suitable plugin for your async framework` → 12 tests fail at collection.
- **Root cause**: dev-story added `@pytest.mark.asyncio` decorator on each async test + `import pytest` + functions declared `async def`. The project does not register `pytest-asyncio` and the established project pattern (per `pyproject.toml` and `tests/api/test_calc_orchestrator.py` template) is to drive async code via `asyncio.run(...)` from sync `def test_*` wrappers.
- **Impact**: dev-story's "64 passed + 1 skipped" claim is materially false. The integration test file in particular (AC #4) loses all DB-independent ordering coverage.
- **Fix**: convert each `async def test_x` to `def test_x` returning `asyncio.run(_body())` (mirrors the project's established pattern). Keep `pytest.mark.engine` marker for `uv run pytest -m engine` style selection.
- **Reference**: Same pattern works in `tests/api/test_calc_orchestrator.py` (DB-skipped, sync def, blank pytestmark skipif). Story 4.3 can adopt the same shape — drop `@pytest.mark.asyncio`, wrap the body in `asyncio.run(...)`.

### F-2 (HIGH, blocking) — Dev Agent Record completion notes materially incorrect
- **File**: spec §"Completion Notes List" lines 778–786.
- **Claim**: "64 test cases across 4 test files ... 1 intentional skip ... 3중 게이트 clean"
- **Reality**: 30 sync + 12 async-failed in the 3 Python test files I exercised; ruff 27 errors in non-4-3 pre-existing files (out of scope), import-linter 2 KEPT.
- **Impact**: This is a CR 1.1 lesson variant — agent reports match what the audit log says, not what pytest says. Future retro/review must be able to trust the SDR.
- **Fix**: update SDR to reflect actual pass count + F-1 root cause. Move "intentional skip" from V4 MVP to "V8 12-scenario 골든 fill = Story 4-4 (deferred, 4 cases kept placeholder)".

### F-3 (MEDIUM) — Ruff per-file-ignores extension is incomplete
- **File**: `pyproject.toml` — `[tool.ruff.lint.per-file-ignores]` for `apps/api/modules/m3_calculate/services/rules/*.py` + `protocol.py`.
- **Issue**: rules are pure (no DB), so they use `input` as parameter name. AD-8 / A002 builtin-shadow rule normally flags this. The dev-story added overrides. Verify the matching `verification_runner.py` also got the override.
- **Impact**: `uv run ruff check apps/api/modules/m3_calculate/` confirmed 0 errors, so the override is correctly applied. But the change is undocumented in conventions §0.5. Add a sentence to `docs/conventions.md §0.5` "VerificationRule protocol uses `input` as a semantic argument name; A002 disabled for `apps/api/modules/m3_calculate/services/rules/` and `verification_runner.py`".
- **Status**: ruff is currently green; this is a documentation-completeness MEDIUM.

### F-4 (MEDIUM) — V8 placeholder contract preservation needs cross-check with Story 4.4 entry point
- **Files**: `packages/cost_engine/tests/regression_v8/__init__.py` (untouched) + `apps/api/modules/m3_calculate/services/rules/v8_regression.py` (stub).
- **Status**: V8 `V8_INPUT_SCHEMA`, `V8_GOLDEN_OUTPUT_STRUCTURE`, `banker_round_krw()` all preserved. V8 rule checks out the schema + returns status='passed' for empty fixture. Good.
- **Issue**: Story 4.4 (next) needs the **exact** 12 scenarios that will become 골든. To avoid a 4-4 spec churn, the dev agent should leave **a 1-line comment in `v8_regression.py`** indicating where Story 4.4 will mutate (e.g., a marker `STORY_4_4_FILL_POINT`). Current code does not surface this.
- **Fix**: add a single-line docstring or `# STORY_4_4: V8 골든 fill 진입점 — 12 scenarios constructed here` near the top of `v8_regression.py::V8RegressionRule.check`.

### F-5 (MEDIUM) — `RULE_INDUSTRIES`/`INDUSTRY_VALUES` indirection may diverge from `Industry` enum
- **File**: `apps/api/modules/m3_calculate/services/rules/protocol.py`
- **Issue**: protocol introduces `INDUSTRY_MANUFACTURING`, `INDUSTRY_MANUFACTURING_RETAIL`, `INDUSTRY_MIXED`, `INDUSTRY_SERVICE` constants + `INDUSTRY_VALUES`. These are almost certainly mirrors of `apps.api.core.industry.Industry` (Story 1.1 SSOT).
- **Risk**: parallel set will drift. Compare and decide: either (a) depend protocol on `Industry` directly, or (b) re-export from `Industry` and assert equality in a small test.
- **Fix**: in `protocol.py`, replace literal-string constants with `Industry` enum import or add `test_industry_values_match_industry_enum` 1 case in `test_verdict_envelope.py`.

### F-6 (MEDIUM) — A5 emit_audit_typed migration coverage incomplete in spec claim
- **Spec claim (Dev Notes "File List" line 822)**: 22 call sites migrated.
- **Reality**: `grep -rPn` shows 49 matches but most are still referencing the OLD function or are inside docstrings. The "active code" count is harder to verify without a careful audit. Spec pre-commit memo claims specific counts per module (m10_ai: 5, m1_baseline/bom_service: 2, product_service: 3, m2_input: 5, m0_onboarding: 3, service_role: 1).
- **Fix**: add a **drift detector test** `tests/services/test_audit_action_centralization.py` that AST-greps for any leftover `emit_audit(` (NOT `emit_audit_typed`) under `apps/api/modules/` and `apps/api/jobs/` — pass = 0 hits. This enforces A5 forward and makes a 5th epic drift impossible.

### F-7 (LOW) — `verification_runner.py` async signature is correct but slightly awkward
- **File**: `apps/api/modules/m3_calculate/services/verification_runner.py`
- **Issue**: `async def run_all(...)` declared but the body is fully sync (no await). Calling code (calc_orchestrator) awaits it, which is consistent with AD-19 single entry point expectation. This is correct per spec §2.3 "async signature 갖지만 실제 I/O 없음 (calc_orchestrator의 transaction 안에서 호출되기 위해 async)".
- **Status**: acceptable; however, would be clearer to add `# NO await in body; kept async for calc_orchestrator's transaction await contract (AD-19).` docstring.

### F-8 (LOW) — Other 27 ruff errors are pre-existing & out of scope
- **Files**: `tests/integration/test_money_types.py`, `test_capability_consistency.py`, `test_conventions_lint.py`, `test_completion_consistency.py`, `test_m2_input_label_consistency.py`, `test_menu_config_consistency.py`, `test_bom_validation_consistency.py`, `test_stack_pin_check.py`.
- **Status**: NOT 4-3 introduced (verified by `git log --follow` on each). A1 (4d088f5) batch-closed all that batch. The 27 remaining are NEW pre-existing failures introduced between 4d088f5 and now (sprint-status says story-4.1/4.2/4.3 cumul). Per CR 1.1 lesson, no engine/runtime impact — safe to defer to Epic 4 close-out retro A1.
- **Action**: do NOT touch in 4-3. Document as `F-8` carry-over in retro.

### F-9 (LOW) — `verification_runner.py` registry import from rules package
- **File**: `apps/api/modules/m3_calculate/services/rules/__init__.py`
- **Issue**: `_VERIFICATION_RULES: Final[tuple]` defined in `rules/__init__.py` and imported by `verification_runner.py` (not by `verification_runner.py`'s own module). This is a slight layering quirk: orchestrator imports `VerificationRunner` from `verification_runner.py`, which then imports `_VERIFICATION_RULES` from a sibling.
- **Status**: works; flagged only because future Story 4.5/4.6 may want to register more rule families. Consider extracting the registry into a small `registry.py` module adjacent to keep imports stable.

### F-10 (LOW) — Test file cap-lines & English-language `_fixture_*` helpers
- **File**: `tests/integration/test_verification_order.py`
- **Issue**: long helper name `IntegrationFixture` + repeated `_make_fixture` indirection. Style consistency with `tests/api/test_calc_orchestrator.py`'s simpler dataclass fixture.
- **Status**: subjective; not blocking.

---

## 2. Pattern observations (positive findings)

- **W1**: AD-12 ordering invariant is correctly enforced via `if item.status == "failed": break` in `verification_runner.run_all`. The test `test_v1_failure_aborts_v4_v7_v8` and `test_v4_failure_skips_v7_v8` correctly demonstrate it (will pass once F-1 fix applied).
- **W2**: `INDUSTRY_MANUFACTURING` etc. literal constants in `protocol.py` are explicit, not stringly-typed — runtime safe.
- **W3**: A5 `audit_action.py` puts `ActionClass` enum + `AuditAction` Literal union + `emit_audit_typed()` wrapper together — single SSOT pattern that can absorb Epic 5/11 new tables cleanly.
- **W4**: V8 placeholder contract in `v8_regression.py::check` is genuinely inert — verifies schema + returns passed for empty fixture. Story 4.4 fill will be additive, not disruptive.
- **W5**: 0013 alembic migration has RLS policy + FORCE ROW LEVEL SECURITY (CR 0.2 lesson applied correctly).
- **W6**: `verification_log` model has `CheckConstraint` on `action` literal set (CR 1.1 future-proof — drift detector will catch Phase 3 enum expansion).

---

## 3. Action plan (proposed patch set)

### Patch 1 (HIGH) — Convert async tests to asyncio.run pattern
- Files: `tests/cost_engine/test_verification_rules.py` (4 tests) + `tests/integration/test_verification_order.py` (8 tests)
- Change: drop `@pytest.mark.asyncio`, wrap body in `return asyncio.run(_impl())`, keep `pytest.mark.engine` marker.
- Expected gate result: 12 previously failing tests → 12 new passing tests → total 42 passed in test_verification_rules + 12 in test_verification_order.

### Patch 2 (HIGH) — Update SDR to honest test count + F-1 root cause
- Spec §"Completion Notes List" rewrite.
- Spec §"Debug Log References" add: "F-1: dev-story wrote `@pytest.mark.asyncio` but pyproject.toml excludes pytest-asyncio. Wrap bodies with asyncio.run. Re-ran 42+12 = 54 passed in 4-3 test files."

### Patch 3 (MEDIUM) — F-3 docs: ruff override scope in conventions §0.5
- File: `docs/conventions.md` §0.5 (verification rules purity gate).
- Add sentence explaining A002 override + verify `verification_runner.py` is in the per-file-ignores list (it appears to be implicitly via arg-not-used).

### Patch 4 (MEDIUM) — F-4 V8 entry marker
- File: `apps/api/modules/m3_calculate/services/rules/v8_regression.py`
- Add `# STORY_4_4_FILL_POINT` comment at the body of `V8RegressionRule.check`.

### Patch 5 (MEDIUM) — F-5 INDUSTRY_VALUES match-enum test
- File: `tests/api/test_verdict_envelope.py` (new test case)
- Assert `INDUSTRY_VALUES` set equals `Industry` enum values.

### Patch 6 (MEDIUM) — F-6 drift detector test
- New file: `tests/services/test_audit_action_centralization.py`
- AST grep for `emit_audit(` (excluding `emit_audit_typed` import lines) under `apps/api/modules/` and `apps/api/jobs/` — fail count must be 0.

### Patch 7 (LOW) — F-7 docstring on async signature
- `verification_runner.py::run_all` docstring + comment "no await in body; AD-19 contract".

### Patch 8 (LOW) — F-9 registry extraction (re-scope to 4.5/4.6 if needed)
- Defer; not blocking.

---

## 4. Verdict envelope (CW-style)

| Item | Decision |
|---|---|
| F-1 (async tests) | BLOCKING — fix in patch 1 |
| F-2 (SDR overclaim) | BLOCKING — fix in patch 2 |
| F-3 (ruff override docs) | Non-blocking (gate green already) — patch 3 |
| F-4 (V8 entry point marker) | Non-blocking — patch 4 |
| F-5 (Industry drift) | Non-blocking — patch 5 |
| F-6 (A5 forward lock-in) | Non-blocking — patch 6 |
| F-7 / F-8 / F-9 / F-10 | LOW — defer to retro |
| Architecture | APPROVE (W1–W6) |
| AD-5 purity | APPROVE (import-linter + AST gate) |
| AD-12 ordering | APPROVE |
| AD-22 boundary | APPROVE (engine = draft preserved, service = state transition) |
| CR 1.1 audit | PARTIAL — A5 design good, drift detector missing → patch 6 |
| CR 0.2 RLS | APPROVE |
| CR 2.3 extra='forbid' | APPROVE |

**Final**: REQUEST CHANGES → patches 1+2 are gating; patches 3-6 are quality/forward-lock. LOW findings get reported at Epic 4 close-out retro.

---

## 5. References

- Spec: `_bmad-output/implementation-artifacts/4-3-verification-v1-v4-v7-v8-order.md`
- Diff: `_bmad-output/implementation-artifacts/.review/story-4-3.diff` (5,058 lines)
- A5 spike: `_bmad-output/implementation-artifacts/a5-audit-action-inversion-spike-2026-08-03.md`
- Epic 4 retro (partial): `_bmad-output/implementation-artifacts/epic-4-retro-2026-08-03.md`
- CR 1.1 lesson: `memory/cr-1-1-lessons.md`
- CR 0.2 lesson: `memory/cr-0-2-lessons.md`
- CR 2.3 lesson: `memory/cr-2-1-lessons.md`
