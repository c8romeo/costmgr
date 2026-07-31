# Validation Report — Story 2.1: Product & Item Master with Type Tags

**Date:** 2026-07-31
**Validator:** bmad-create-story (manual checklist.md walk-through)
**Story file:** `_bmad-output/implementation-artifacts/2-1-product-item-master-type-tags.md`
**Baseline commit:** c48b30e (Story 1.2 review patches)
**Story status (post-validate):** ready-for-dev → dev-ready (validation cleared)

---

## 1. Summary

| Severity | Found | Fixed | Deferred |
|----------|------|-------|----------|
| CRITICAL | 2 | 2 | 0 |
| MEDIUM | 2 | 2 | 0 |
| MINOR | 3 | 0 (cosmetic) | 3 |
| ENHANCEMENT | 4 | 4 (folded into story) | 0 |

**Result:** Story is **dev-ready**. All CRITICAL and MEDIUM findings were patched in-place on the story file; MINOR items carry forward as observation, not blockers.

---

## 2. Validation Method

bmad-create-story ships only one workflow (create), so validation was executed manually against the `checklist.md` rubric:

- Title & meta block (baseline_commit, status, story header)
- AC BDD quality (Given/When/Then shape, AD coverage, error contract)
- Task coverage (every AC has at least 1 subtask; L4 cross-language drift test)
- Dev Notes — architecture AD cross-references
- Cold-start stack pin additions — AD-14 exact pin compliance
- Testing standards — CR lessons applied
- Anti-pattern prevention — common-LLM-mistake guardrails

Each section scored against:
- **CRITICAL** — would cause silent regression, AD violation, or fail CI before dev agent even starts
- **MEDIUM** — would cause dev agent pause + rework; not silent
- **MINOR** — cosmetic / doc noise; noted but not patched

---

## 3. Findings

### CRITICAL-1 — `shadcn/ui Toast (sonner)` violations of AD-14

**Where (story pre-fix):** Task 5.4 referenced `sonner - latest` (no version pin). The toast helper is a code-path dependency for 409 (duplicate code) and 403 (industry) error feedback; specifying `latest` is forbidden by AD-14 stack-pin exact-pin rule (CR 0.3 lesson).

**Fix applied:** Added sonner to the "Required additions" table under "Cold-start stack pin additions", explicitly noting AD-14 forbids `latest` and requiring `[STACK BUMP]` workflow + `bump_stack_pin.sh`. Also added Open Question #5 to surface the toolchain dependency. The story now also references the same requirement for `@tanstack/react-table` (8.21.3) and `decimal.js` (^10.4.3).

**Status:** ✅ Fixed in-place.

### CRITICAL-2 — Story stack-pin section drifted from `docs/STACK_PIN.yaml`

**Where (story pre-fix):** The "Cold-start stack pin additions" section referenced spec targets only (Next 16.2.11, React 19.2.8, TS 7.0.2, Pydantic 2.13.4). The actual installed versions per `docs/STACK_PIN.yaml` exceptions block are 15.5.4 / 19.1.1 / 5.9.3 / 2.11.9 — these are tracked exceptions, not the spec. A dev agent reading the story alone would attempt to upgrade to spec targets and break the lockfile.

**Fix applied:** Added an "Installed (per docs/STACK_PIN.yaml exceptions block — current pins as of 2026-07-31)" subsection listing the 6 actual pinned dependencies (Next, React, TS, FastAPI, Pydantic, SQLAlchemy, pytest) with side-by-side spec-target comments. Dev agent now reads the actual pins first and only upgrades if explicitly told to follow up with a [STACK BUMP] workflow.

**Status:** ✅ Fixed in-place.

### MEDIUM-1 — Testing standards omitted CR 0.2/1.1 lessons

**Where:** The original "Testing standards" section had general guidance but did not call out:
- CR 0.2: RLS tests must use `psql -v ON_ERROR_STOP=1` + non-bypassrls role + explicit transaction
- CR 1.1: audit `payload` must be self-describing `{changed_fields, before, after}` map
- CR 1.1: pytest.skip vs xfail strict=False distinction for DB/RLS-backed tests

**Fix applied:** Expanded "Testing standards" with all three lessons as bullet lines. Dev agent will see the patterns before writing tests.

**Status:** ✅ Fixed in-place.

### MEDIUM-2 — Anti-pattern prevention missing common-LLM-mistake guardrails

**Where:** The original list covered data-integrity mistakes (no float, no hard delete, audit-first) but did not cover:
- AD-14 exact pin (no `latest` or `*` versions)
- AD-11 layer rule (apps/api/core/ can't import packages.services — product_code.py belongs in packages/services/m1_baseline/)
- No-op audit skip distinction (CR 1.1 lesson)
- FastAPI typed error mapping for ProductCodeDuplicateError / ProductImmutableFieldError
- Audit payload redaction (structlog)
- service_role guard-lint

**Fix applied:** Added 4 new DO-NOT bullets covering all six categories. The dev agent gets these reminders inline next to the existing anti-patterns.

**Status:** ✅ Fixed in-place.

### MINOR — Cosmetic / observational

- **MINOR-1**: Story header `Status: ready-for-dev` is correct at the validate gate (post-fix), but does not auto-flip to `in-progress` until dev starts. Carrying forward for sprint-status.yaml update only.
- **MINOR-2**: References section at line 444 lists `docs/architecture-decisions/AD-11-dependency-direction.md` and the new AD-7 entry — these files exist (verified) but the file-anchored permalinks are coarse. Carrying forward as observation; full deep-link anchors are out of scope for story body.
- **MINOR-3**: Open Question #5 (bump_stack_pin.sh gap) overlaps with the Cold-start section. Kept both for discoverability — dev agent should see it twice if the toolchain breaks.

**Status:** ⚠ Carried forward, not patched.

### ENHANCEMENT — Folded into story during validate

These items were not findings but valuable context added during the validation pass:

- **ENH-1**: Open Question #1 (service industry catalog scope) got a default applied (capability gate at type level per Task 2.1) — eliminates ambiguity before dev starts.
- **ENH-2**: Open Question #2 (goods type) got a default applied — separate `product_type='goods'` per epics AC.
- **ENH-3**: Open Question #3 (description max length) got default 2000 chars — matches Story 0.4 patterns.
- **ENH-4**: Open Question #4 (unit field) got default `free-text max_length=20` — PRD does not constrain, cj-style prefers flexibility.

**Status:** ✅ Folded into story.

---

## 4. Cross-checks Against CR Lessons

| Lesson | Applied? | Notes |
|--------|----------|-------|
| CR 0.2 (RLS infra + CI shim + service_role guard-lint) | ✅ | psql -v ON_ERROR_STOP=1 + service_role rule referenced in anti-pattern |
| CR 0.3 (spec mirror + bump full automation + yaml lib) | ✅ | STACK_PIN additions table with bump_stack_pin.sh requirement |
| CR 0.4 (AST linter + ESLint flat config + chunk-application) | ✅ | Cold-start prerequisites section flags `.eslint.config.mjs` + Tailwind 4.x |
| CR 1.1 (RSC boundary + ContextVar yield-finally + audit self-describing + capability) | ✅ | testing standards bullet; capability 403 mapping bullet |
| New: AD-11 layer rule | ✅ | DO NOT add file under apps/api/core importing packages.cost_engine; product_code.py lives in packages/services/ |

---

## 5. Story Quality Self-Check

- [x] **Every AC mapped to ≥1 task** (AC #1 → T1/T3/T4; AC #2 → T5.2/T5.3; AC #3 → T1/T3/T4/T6.2; AC #4 → T4/T6.2; AC #5 → T4.6/T6.2; AC #6 → T2/T6.4)
- [x] **Every AD cited** (AD-1, AD-2, AD-3, AD-5, AD-8, AD-11, AD-15, AD-18, AD-23) with implementation note
- [x] **Anti-pattern guardrails present** (13 DO-NOTs + 8 DOs)
- [x] **Testing standards cover CR lessons** (3 CR lessons applied)
- [x] **Frontend test items have explicit defer path** (T6.5/T6.6 — Story 0.5 plumbing)
- [x] **Capability gate documented** (PRODUCT + PRODUCT_MATERIAL enum values + industry map)
- [x] **Cross-language drift test specified** (T6.7)
- [x] **RLS test pattern specified** (psql shim + 4 cases per table)
- [x] **Error contract mapped** (AD-15 §4 with trace_id)
- [x] **Open Questions resolved** (4 with cj-style defaults + 1 toolchain reminder)

---

## 6. Story Lifecycle State

| Field | Value |
|-------|-------|
| Pre-validate | ready-for-dev (with 2 CRITICAL gaps) |
| Post-validate | ready-for-dev (post-validate cleared) — **dev-ready** |
| Next action | `bmad-dev-story` execute (Task #3) |

**Note on workflow gap:** bmad-create-story does not ship a separate `validate` action. The dev agent reads story files from `ready-for-dev` status directly. If validation were a hard gate, the workflow would refuse `in-progress` transitions without a `*-validation.md` sidecar. Current behavior: dev agent reads story content; this report is metadata for sprint-status and post-mortem use.

---

## 7. Validation Complete — Ready for Dev

✅ All CRITICAL/MEDIUM items fixed.
✅ ENHANCEMENT items folded.
⚠ MINOR items observed; not blockers.
🚀 Next: invoke `bmad-dev-story` for Story 2.1 to begin implementation.
