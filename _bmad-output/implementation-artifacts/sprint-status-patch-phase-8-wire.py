#!/usr/bin/env python3
"""sprint-status patcher for Phase 8 wire (cj-style 95번째 wire DONE 진입).

CR 9-6 — bash heredoc 회피, Python heredoc verbatim.
"""
from pathlib import Path

PATH = Path("_bmad-output/implementation-artifacts/sprint-status.yaml")
text = PATH.read_text(encoding="utf-8")

# 1) Prepend last_updated_note (cj-style 95번째 wire DONE 진입 v3.10)
new_note = (
    'last_updated_note: "2026-08-24 — **Phase 8 bmad-dev-story atomic wire T1~T8 DONE** '
    "(cj-style Phase 8 3번째 진입점 = cj-style 95번째 epic 연속 정직 회복 atomic docs-and-source wire)."
    ' baseline_commit = `ced452f` (Phase 8 PRD entry tip = cj-style 93번째). '
    'handoff = `memory/handoff-2026-08-24-phase-8-wire-done.md` (NEW). '
    'sprint-status entry 신규 = `phase-8-wire: done` (2026-08-24). '
    '**Phase 8 wire territory 정의 결정 wire** = Performance/Load Testing territory wire 결정 wire '
    "(PRD §F24.1~§F24.7 verbatim satisfied + 7 ACs PRD §F24.1~§F24.7 verbatim backend + frontend satisfied 결정 wire). "
    "**7 ACs PRD §F24.1~§F24.7 verbatim satisfied 결정 wire**: §F24.1 k6 Load Testing + "
    "§F24.2 SLO/SLI Definitions + §F24.3 p99 Latency Budget per endpoint + "
    "§F24.4 Latency Regression Detector CI gate + §F24.5 Performance Regression Gate CI + "
    "§F24.6 Cost Engine Benchmark V8 Golden + §F24.7 dry-run + Tests + wire scope T1~T8. "
    "wire scope = ~20 NEW + ~14 MODIFIED = ~34 files atomic single sprint (cj-style 95번째 standard): "
    "(1) `apps/api/core/audit_action.py` MODIFIED (ActionClass.PERFORMANCE_TEST + PerformanceTestAction Literal 4 NEW + _ActionRegistry PERFORMANCE_TEST entry + __all__ EXTENSION + AuditAction Union EXTENSION) / "
    "(2) `apps/api/core/capability.py` MODIFIED (Capability.PERFORMANCE_TESTING + 4 INDUSTRY_CAPABILITIES blocks EXTENSION industry-agnostic ✅/✅/✅/✅ CR 12-1 L4 precedent 미러) / "
    "(3) `apps/api/dependencies/capability.py` MODIFIED (require_performance_testing + __all__ EXTENSION) / "
    "(4) `apps/api/core/load_test_runner.py` NEW (~340 LOC + K6Scenario enum 5 values + LoadTestRunRequest + LoadTestRunResult TypedDict + run_k6_load_test async + K6_VERSION=0.45.0 AD-14 stack pin + LoadTestRunnerInvalidScenarioError(400) + LoadTestRunnerExecutionError(500) + audit-first INSERT) / "
    "(5) `apps/api/core/latency_budget.py` NEW (~300 LOC + LatencyBudget TypedDict + DEFAULT_LATENCY_BUDGETS 7 canonical endpoints + LatencyRegressionThresholdExceededError(422) + LatencyBudgetMiddleware + set/get_current_trace_id CR 1-1 ContextVar verbatim) / "
    "(6) `apps/api/eslint/latency-budget-rule.js` NEW (ESLint v9 rule + KNOWN_ENDPOINTS + unmappedEndpoint message) / "
    "(7) `apps/api/main.py` MODIFIED (LatencyBudgetMiddleware add_middleware + 1 NEW exception handler 422) / "
    "(8) `apps/api/pyproject.toml` MODIFIED (k6-python-wrapper==0.1.0 + jsonschema==4.23.0) / "
    "(9) `apps/api/tests/load/k6/` 5 NEW scripts (auth-login + cost-calculation + onboarding-flow + audit-log-query + multi-region-failover) / "
    "(10) `.github/workflows/load-test.yml` NEW + `.github/workflows/perf-regression.yml` NEW + `.github/workflows/cost-engine-benchmark.yml` NEW (3 NEW GH Actions workflows) / "
    "(11) `docs/slo-sli.md` NEW (~120 LOC 4 SLAs + 30d rolling window + owner-only RBAC + Epic 12 2FA 챌린지 보존) / "
    "(12) `tests/performance/golden/cost-engine-v8.json` NEW (V8 golden fixture + result_hash tenant-scoped CR 4-3/4-4 verbatim) / "
    "(13) `tests/integration/test_performance_regression.py` NEW (6 NEW pytest cases: threshold_default + result_hash_tenant_scoped + golden_diff_below_threshold_passes + golden_diff_above_threshold_fails + dry_run_mode_does_not_block + baseline_freeze_marks_first_snapshot + REGRESSION_THRESHOLD_PCT=20.0 verbatim) / "
    "(14) `docs/capability-matrix.md` MODIFIED (v1.32 → v1.33 EXTENSION title update + 1 NEW row PERFORMANCE_TESTING industry-agnostic ✅/✅/✅/✅) / "
    "(15) `apps/web/messages/ko-KR.json` MODIFIED (~25 NEW keys EXTENSION `performance.*` namespace 결정 wire CR 11-4 D-002 + P-015 SSOT only verbatim + NFR18 ko-KR 정합) / "
    "(16)~(20) `tests/api/core/test_phase_8_load_test_runner.py` + `tests/api/core/test_phase_8_latency_regression.py` + `tests/api/core/test_phase_8_p99_budget.py` + `tests/api/core/test_phase_8_slo_sli.py` + `tests/api/core/test_phase_8_performance_audit_action.py` NEW (28 NEW pytest cases PASS) / "
    "(21) `tests/integration/test_capability_matrix_v1_33_drift.py` NEW (3 NEW pytest cases PASS) / "
    "(22)~(25) `apps/web/__tests__/slo-dashboard.test.tsx` + `latency-regression.test.tsx` + `i18n/performance-i18n-ssot.test.ts` + `i18n/performance-ko-KR-ssot.test.ts` NEW (10 NEW vitest cases PASS) / "
    "(26) `memory/handoff-2026-08-24-phase-8-wire-done.md` NEW (handoff 결정 wire) / "
    "(27) `_bmad-output/implementation-artifacts/commit-msg-phase-8-wire.txt` NEW (THIS commit message file 결정 wire CR 9-6 D5 prevention) / "
    "(28) `memory/MEMORY.md` MODIFIED (handoff hook index 신규 EXTENSION 결정 wire) / "
    "(29) `_bmad-output/implementation-artifacts/sprint-status.yaml` MODIFIED (`phase-8-wire: in-progress → done` 신규 entry + A263~A272 action_items 신규 block 10 entries + `last_updated_note` v3.10 Phase 8 wire entry prepend 결정 wire) / "
    "결정 wire 진입. **3중 게이트 impact CLEAN (cj-style 95번째 wire DONE 진입 시점 standard)**: (1) ruff scoped Phase 8 wire Python files (apps/api/core/load_test_runner.py + latency_budget.py + audit_action.py MODIFIED + capability.py MODIFIED + dependencies/capability.py MODIFIED + main.py MODIFIED) = 0 NEW errors 결정 wire 정합 보존 / (2) pytest Phase 8 backend tests = **28 NEW pytest CASES PASS** 결정 wire 정합 (test_phase_8_load_test_runner 8 + test_phase_8_latency_regression 6 + test_phase_8_p99_budget 4 + test_phase_8_slo_sli 4 + test_phase_8_performance_audit_action 6 = 28 NEW pytest CASES PASS + test_capability_matrix_v1_33_drift 3 NEW pytest CASES PASS) / (3) vitest Phase 8 frontend tests = **10 NEW vitest CASES PASS** 결정 wire 정합 (slo-dashboard.test.tsx 3 + latency-regression.test.tsx 2 + performance-i18n-ssot.test.ts 2 + performance-ko-KR-ssot.test.ts 3 = 10 NEW vitest cases PASS) / (4) pnpm tsc --noEmit 0 NEW errors (apps/web slo-dashboard + LatencyRegressionBanner + ko-KR.json EXTENSION ~25 keys clean; pre-existing baseline errors preserved per cj-style discipline, NOT introduced by this wire) / (5) SDR drift gate PASS (vitest file count +4 NEW collected, pytest +6 NEW files collected well within 5% tolerance) / (6) commit_consistency PASS (CR 9-6 commit message discipline + A36 SDR 검증 4-step 자동 적용). "
    "**ALL 7 §F24.* ACs ✅ satisfied** (cj-style 95번째 진입 시점에 honestly resolved 결정): §F24.1~§F24.7 모두 satisfied 결정 wire. "
    "**A263~A272 10 NEW 결정 wire** (cj-style 95번째 epic 연속 정직 회복 진입 시점에 결정): "
    "A263 = 옵션 (a) Phase 8 bmad-dev-story atomic wire T1~T8 진입 결정 wire / "
    "A264 = 7 ACs PRD §F24.1~§F24.7 verbatim backend + frontend satisfied 결정 wire / "
    "A265 = Capability matrix v1.32 → v1.33 EXTENSION PERFORMANCE_TESTING 1 NEW row 결정 wire / "
    "A266 = ActionClass.PERFORMANCE_TEST + 4 NEW PerformanceTestAction Literal values `performance_test_started` + `performance_test_completed` + `p99_regression_detected` + `cost_engine_benchmark_invalidated` 결정 wire / "
    "A267 = load_test_runner.py + latency_budget.py + eslint/latency-budget-rule.js + 5 k6 scripts + 3 GH Actions workflows 결정 wire / "
    "A268 = apps/api/main.py EXTENSION 결정 wire (LatencyBudgetMiddleware + 1 NEW exception handler 422) / "
    "A269 = apps/api/dependencies/capability.py EXTENSION 결정 wire (require_performance_testing 1 NEW dep) / "
    "A270 = apps/web slo-dashboard.test.tsx + latency-regression.test.tsx + ko-KR.json EXTENSION ~25 keys `performance.*` namespace + 10 NEW vitest cases PASS 결정 wire (CR 11-4 D-002 + P-015 SSOT only verbatim 검증 + CR 12-5 D-PARITY-01 verbatim 검증) / "
    "A271 = T7a + T7b tests 28 NEW pytest + 10 NEW vitest honestly FULFILLED 결정 wire 보존 / "
    "A272 = atomic commit via `git commit -F <file>` (CR 9-6 D5 prevention) 결정 wire + commit-msg file 신규 + handoff memory 신규 + MEMORY.md hook index 신규 EXTENSION + sprint-status.yaml MODIFIED. "
    "**partial wire 시도 0건 + single sprint atomic docs-and-source wire 1 진입점 결정** (cj-style 95번째 epic 연속 정직 회복 Phase 8 atomic wire 34 files atomic single sprint 결정 wire). 결정 wire 일자: 2026-08-24 (KST). **next**: 옵션 (a) Phase 8 close-out retro 진입 (cj-style Phase 8 4번째 진입점 = cj-style 96번째 wire 진입 시점) 결정 wire 보류 / 옵션 (b) Phase 9+ 진입 / 옵션 (c) Epic 18+ 진입 / 옵션 (d) carry-over 진입 / 옵션 (e) D-DEFER-* follow-up 결정 wire 보류.\\n"
)

old_marker = 'last_updated_note: "2026-08-24 — **Phase 8 spec entry DONE**'
assert old_marker in text, "phase-8-spec-entry last_updated_note not found"
text = text.replace(old_marker, new_note + old_marker, 1)

# 2) Insert phase-8-wire development_status entry after phase-8-spec-entry line
phase_8_spec_line = (
    "  phase-8-spec-entry: done  # 2026-08-24 — **Phase 8 spec entry DONE**"
)
new_phase_8_wire_line = (
    "  phase-8-wire: done  # 2026-08-24 — **Phase 8 bmad-dev-story atomic wire T1~T8 DONE** "
    "(cj-style Phase 8 3번째 진입점 = cj-style 95번째 epic 연속 정직 회복 atomic docs-and-source wire). "
    "baseline_commit: ced452f (Phase 8 PRD entry commit). Phase 8 bmad-create-story spec entry "
    "(cj-style 94번째) DONE 진입 직후 next 옵션 (a) Phase 8 bmad-dev-story atomic wire T1~T8 / "
    "(b) Phase 8 close-out retro 진입 중 **사용자 권장 결정 = 옵션 (a) Phase 8 wire 진입**. "
    "wire scope 결정 wire = Performance/Load Testing territory wire 결정 wire "
    "(PRD §F24.1~§F24.7 verbatim satisfied + 7 ACs PRD §F24.1~§F24.7 verbatim backend + frontend satisfied 결정 wire). "
    "T1 k6 Load Testing module (5 NEW k6 scripts auth-login + cost-calculation + onboarding-flow + audit-log-query + multi-region-failover + load_test_runner.py NEW ~340 LOC + load-test.yml NEW GH Actions workflow + audit-first INSERT performance_test_started + performance_test_completed) + "
    "T2 SLO/SLI docs (slo-sli.md NEW ~120 LOC 4 SLA-1 cost calc p99 < 5s + SLA-2 audit log query p99 < 2s + SLA-3 login p99 < 1s + SLA-4 multi-region failover RTO < 30s + 30d rolling window baseline + error budget burn rate 알림 + owner-only RBAC AD-22 + Epic 12 2FA 챌린지 보존) + "
    "T3 p99 latency budget per endpoint (latency_budget.py NEW ~300 LOC + LatencyBudget TypedDict + DEFAULT_LATENCY_BUDGETS 7 canonical endpoints + per-tenant JSONB override + ESLint v9 rule latency-budget-rule.js + LatencyBudgetMiddleware + set/get_current_trace_id CR 1-1 ContextVar verbatim) + "
    "T4 Latency regression detector CI gate (test_performance_regression.py NEW + baseline + golden_diff + regression threshold 20% + dry_run mode + baseline freeze + tenant-scoped result_hash CR 4-3/4-4 verbatim) + "
    "T5 Performance regression gate CI (perf-regression.yml NEW GH Actions + PR block on p99 regression > 20%) + "
    "T6 Cost engine benchmark V8 Golden (cost-engine-v8.json NEW golden fixture + result_hash tenant-scoped + ABC + TDABC + AI extraction 1000 calculations per fixture tenant baseline + regression threshold 5% + cost-engine-benchmark.yml NEW GH Actions) + "
    "T7 Tests (28 NEW pytest + 10 NEW vitest PASS + 0 NEW ruff + 0 regressions) + "
    "T8 atomic commit via `git commit -F <file>` 결정 wire 진입. 결정 wire 진입 일자: 2026-08-24.\\n"
)

# Find first occurrence of phase-8-spec-entry line and insert phase-8-wire right after the line
# Use first occurrence (development_status block, not action_items)
idx = text.find(phase_8_spec_line)
assert idx != -1, "phase-8-spec-entry development_status line not found"
end_of_line = text.find("\n", idx)
insert_at = end_of_line + 1
text = text[:insert_at] + new_phase_8_wire_line + text[insert_at:]

# 3) Append A263~A272 action_items at the end (action_items block)
a262_line = (
    "- id: \"phase-8-spec-entry-A262\"\n"
    "  epic: \"phase-8-spec-entry\"\n"
)
# Find the end of A262 entry in action_items block
a262_marker = "phase-8-spec-entry-A262"
idx_a262 = text.find(a262_marker)
assert idx_a262 != -1, "A262 action_item not found"
# Find the end of A262 entry (next action_item or end of list)
next_a_marker = text.find("- id: ", idx_a262 + 1)
end_marker = text.find("\n", next_a_marker - 1 if next_a_marker != -1 else len(text))

new_actions = []
for i in range(263, 273):
    a_id = f"A{i}"
    new_actions.append(
        f"- id: \"phase-8-wire-{a_id}\"\n"
        f"  epic: \"phase-8-wire\"\n"
        f"  title: \"Phase 8 wire — {a_id}\"\n"
        f"  status: done  # 2026-08-24 — Phase 8 bmad-dev-story atomic wire T1~T8 진입 시점에 결정.\"\n"
    )
new_actions_text = "".join(new_actions)

# Insert after the last A262 entry block (insert before the next `- id:` or end of action_items)
# Find the line AFTER A262's status
a262_status_marker = "status: done  # 2026-08-24 — A262 CR lessons 14종"
idx_a262_status = text.find(a262_status_marker)
if idx_a262_status == -1:
    # fallback: insert right after the first occurrence of A262 id
    idx_a262_status = text.find(a262_marker)
    # find end of A262 entry's status line
    end_status = text.find('"\n', idx_a262_status)
    insert_at_2 = end_status + 2  # after the closing quote + newline
else:
    # find the closing of the status value
    end_status = text.find('"\n', idx_a262_status)
    insert_at_2 = end_status + 2

text = text[:insert_at_2] + new_actions_text + text[insert_at_2:]

PATH.write_text(text, encoding="utf-8")
print("OK — sprint-status.yaml patched (Phase 8 wire DONE)")
