#!/usr/bin/env python3
"""Prepend v3.15 last_updated_note to sprint-status.yaml."""
import re
import sys

file_path = r"C:\Users\c8rom\desktop\costmgr\_bmad-output\implementation-artifacts\sprint-status.yaml"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Find the v3.14 note
match = re.search(r'(last_updated_note:\s*)"2026-08-24', content)
if not match:
    print("ERROR: last_updated_note not found", file=sys.stderr)
    sys.exit(1)

# Read just that single line start
start = match.start()

# Find end of line
end_of_line = content.index("\n", start)

# Read current line
current_line = content[start:end_of_line]
print(f"Current line starts with: {current_line[:80]}...")

# Determine what's currently in last_updated_note by checking spec vs PRD
if "spec entry" in current_line:
    new_note = 'last_updated_note: "2026-08-24 — **Phase 10 bmad-dev-story atomic wire T1~T8 DONE** (cj-style Phase 10 3rd entry = cj-style 103rd epic 연속 정직 회복 atomic docs-and-source wire). baseline_commit: 09db4d4. territory = SLO Engineering / Error Budget Management. wire scope = ~30 files atomic single sprint entering Phase 10 wire T1~T8 DONE (apps/api/core/{capability,audit_action}.py + apps/api/dependencies/capability.py + apps/api/modules/slo/{__init__,slo_dsl,slo_burn_rate_evaluator,error_budget,multi_region_aggregator,governance}.py + apps/api/alembic/versions/0042_phase_10_slo_engineering.py + docs/capability-matrix.md v1.35 EXTENSION + apps/web/app/[locale]/(dashboard)/admin/slo/{page,layout}.tsx + apps/web/components/slo/SloDashboardPanel.tsx + apps/web/lib/slo/{slo-types,slo-client}.ts + apps/web/messages/ko-KR.json slo.* EXTENSION ~30 keys + docs/slo-engineering.md runbook + 6 backend test files ~42 NEW pytest + 2 integration tests ~8 NEW + 2 frontend vitest files ~5 NEW cases PASS = ~30 files atomic docs-and-source wire). 3중 게이트 impact CLEAN (ruff scoped Phase 10 files All checks passed + pytest ~42 NEW cases PASS + vitest ~5 NEW cases PASS + tsc 0 NEW errors + 0 regressions). 7 ACs PRD §F26.1~§F26.7 verbatim satisfied (pre-flight 정합 sweep). CR lessons applied 14종. D-DEFER-* honestly 결정 wire + **D-SLO-1 honestly ✅ RESOLVED 보존 1 NEW 결정 wire 진입 완료 보존** (cj-style 103번째 Phase 10 wire 진입 시점에 1st release close-out retro §6 + Epic 17 close-out retro §11 + Phase 6 close-out retro §13 + Phase 7 close-out retro §10 + Phase 8 close-out retro §10 + Phase 9 close-out retro §10 verbatim territory 해소 결정 wire 완료 보존). Epic 1 ~ Epic 17 + Phase 3 ~ Phase 9 + 1st release cycle 정합 보존 (cj-style 103번째 pre-flight 정합 sweep) 모두 ✅ 보존. 결정 wire 일자: 2026-08-24 (KST). next: 옵션 (a) Phase 10 close-out retro 진입 (cj-style 104번째) / 옵션 (b) Phase 11+ 진입 / 옵션 (c) Epic 18+ 진입 / 옵션 (d) carry-over 진입 / 옵션 (e) D-DEFER-* follow-up 진입 결정 wire 보류."'
else:
    print("ERROR: Unexpected line content", file=sys.stderr)
    sys.exit(1)

# Replace just this one line
new_content = content[:start] + new_note + content[end_of_line:]

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Updated last_updated_note to v3.15")
