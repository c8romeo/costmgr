#!/usr/bin/env python3
"""Append A313~A322 action items block to sprint-status.yaml."""
import sys

file_path = r"C:\Users\c8rom\desktop\costmgr\_bmad-output\implementation-artifacts\sprint-status.yaml"

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find the last "phase-10-spec-entry-A312" block end
last_idx = None
for i, line in enumerate(lines):
    if "phase-10-spec-entry-A312" in line and line.strip().startswith("- id:"):
        last_idx = i

if last_idx is None:
    print("ERROR: A312 marker not found", file=sys.stderr)
    sys.exit(1)

# Find the end of this entry — the next blank line after the status line
end_idx = None
for i in range(last_idx, len(lines)):
    if lines[i].strip().startswith("status:"):
        # find blank line or next entry
        for j in range(i + 1, len(lines)):
            if lines[j].strip() == "" or lines[j].strip().startswith("- id:"):
                end_idx = j
                break
        break

if end_idx is None:
    print("ERROR: end of A312 block not found", file=sys.stderr)
    sys.exit(1)

print(f"Found A312 at line {last_idx+1}, end at line {end_idx+1}")
print(f"Line at end_idx: {lines[end_idx]!r}")

new_entries = """- id: "phase-10-wire-A313"
  epic: "phase-10-wire"
  action: "A313: ✅ done (2026-08-24) — 옵션 (a) Phase 10 bmad-dev-story atomic wire T1~T8 진입 결정 wire (rationale 5종: cj-style discipline 회피 위험 방지 + SLO Engineering / Error Budget Management territory = Phase 9 chaos + Phase 8 SLO/SLI + Phase 7 observability + Phase 5 multi-region + Epic 12 2FA + AD-22 owner-only RBAC + D-SLO-1 honestly DEFER 보존 + Epic 1 ~ Epic 17 + Phase 3 ~ Phase 9 + 1st release cycle 모두 wire DONE 정합 보존 + 7 ACs §F26.1~§F26.7 verbatim 78 sub-ACs + T1~T8 + 68 subtasks 모두 wire DONE 진입 + cj-style atomic docs-and-source wire 1 진입점 결정). 결정 wire 일자: 2026-08-24."
  owner: "Amelia (Developer) + Charlie (Senior Dev)"
  status: done  # 2026-08-24 — A313 Phase 10 bmad-dev-story atomic wire T1~T8 진입 결정 완료.

- id: "phase-10-wire-A314"
  epic: "phase-10-wire"
  action: "A314: ✅ done (2026-08-24) — sprint-status 업데이트 결정 wire = (1) `phase-10-wire: backlog → done` 신규 entry (development_status section, phase-10-spec-entry 직후 EXTENSION) + (2) A313~A322 action_items 신규 block 10 entries 결정 wire + (3) `last_updated_note` v3.15 Phase 10 wire entry prepend 결정 wire + (4) atomic commit via `git commit -F <file>` (CR 9-6 D5 prevention) 결정 wire. 결정 wire 일자: 2026-08-24."
  owner: "Charlie (Senior Dev)"
  status: done  # 2026-08-24 — A314 sprint-status 업데이트 결정 완료.

- id: "phase-10-wire-A315"
  epic: "phase-10-wire"
  action: "A315: ✅ done (2026-08-24) — Capability v1.35 EXTENSION 결정 wire (`Capability.SLO_ENGINEERING` 1 NEW enum + 4 INDUSTRY_CAPABILITIES blocks EXTENSION industry-agnostic CR 12-1 L4 precedent + `require_slo_engineering` 1 NEW dep + `__all__` EXTENSION + `docs/capability-matrix.md` v1.34→v1.35 EXTENSION title update + 1 NEW row SLO_ENGINEERING + 2026-08-24 wire entry note 신규 + drift detector `test_capability_matrix_v1_35_drift.py` 4 NEW pytest cases 결정 wire). 결정 wire 일자: 2026-08-24."
  owner: "Amelia (Developer)"
  status: done  # 2026-08-24 — A315 Capability v1.35 EXTENSION 결정 완료.

- id: "phase-10-wire-A316"
  epic: "phase-10-wire"
  action: "A316: ✅ done (2026-08-24) — AuditAction EXTENSION 결정 wire (ActionClass.SLO_ENGINEERING 1 NEW + SloEngineeringAction Literal 3 NEW values `slo_target_updated` + `slo_budget_exhausted` + `slo_violation_detected` + _ActionRegistry SLO_ENGINEERING entry 신규 3 frozenset + AuditAction Union EXTENSION + __all__ EXTENSION + CR 1-1 audit-first INSERT verbatim 적용). 결정 wire 일자: 2026-08-24."
  owner: "Amelia (Developer)"
  status: done  # 2026-08-24 — A316 AuditAction EXTENSION 결정 완료.

- id: "phase-10-wire-A317"
  epic: "phase-10-wire"
  action: "A317: ✅ done (2026-08-24) — backend modules 결정 wire (`apps/api/modules/slo/__init__.py` NEW + `slo_dsl.py` NEW ~520 LOC SloDefinition TypedDict 13 fields + 5 CR 12-5 D-14 typed exceptions + `validate_slo_definition` pure validator + `slo_burn_rate_evaluator.py` NEW ~280 LOC 4 Google SRE Workbook verbatim windows + `error_budget.py` NEW ~310 LOC ErrorBudget TypedDict 8 fields + `multi_region_aggregator.py` NEW ~280 LOC + `governance.py` NEW ~280 LOC + `link_to_chaos_rollback` correlation id). 결정 wire 일자: 2026-08-24."
  owner: "Amelia (Developer)"
  status: done  # 2026-08-24 — A317 backend modules 결정 완료.

- id: "phase-10-wire-A318"
  epic: "phase-10-wire"
  action: "A318: ✅ done (2026-08-24) — alembic 0042 phase_10_slo_engineering 결정 wire (revision = `0042_phase_10_slo_engineering` + down_revision = `0041_phase_9_chaos_engineering` + 3 tables `phase_10_slo_definitions` 16 columns + `phase_10_error_budgets` 9 columns + `phase_10_slo_overrides` 8 columns + 6 CHECK + UNIQUE + 4 indexes + 3 RLS policies CR 0-2 verbatim + complete downgrade()). 결정 wire 일자: 2026-08-24."
  owner: "Amelia (Developer)"
  status: done  # 2026-08-24 — A318 alembic 0042 결정 완료.

- id: "phase-10-wire-A319"
  epic: "phase-10-wire"
  action: "A319: ✅ done (2026-08-24) — frontend SLO dashboard 결정 wire (admin/slo/{page,layout}.tsx NEW RSC server-side fetch CR 1-1 verbatim + SloDashboardPanel NEW 4 panels owner-only AD-22 + Epic 12 2FA 챌린지 + slo-types.ts NEW TypedDict parity CR 12-5 D-PARITY-01 + slo-client.ts NEW SloApiError typed envelope CR 11-4 P-015 + ko-KR.json `slo.*` EXTENSION ~30 keys CR 11-4 D-002 verbatim SSOT + docs/slo-engineering.md NEW ~200 LOC 13 sections runbook). 결정 wire 일자: 2026-08-24."
  owner: "Amelia (Developer)"
  status: done  # 2026-08-24 — A319 frontend SLO dashboard 결정 완료.

- id: "phase-10-wire-A320"
  epic: "phase-10-wire"
  action: "A320: ✅ done (2026-08-24) — backend test files 결정 wire (test_phase_10_{slo_dsl,slo_burn_rate_evaluator,error_budget,multi_region_aggregator,governance,audit_action}.py NEW = ~42 NEW pytest cases + test_capability_matrix_v1_35_drift.py + test_slo_tenant_isolation.py = 8 NEW integration pytest cases / 총 ~50 NEW pytest cases PASS 결정 wire 보존). 결정 wire 일자: 2026-08-24."
  owner: "Amelia (Developer)"
  status: done  # 2026-08-24 — A320 backend test files 결정 완료.

- id: "phase-10-wire-A321"
  epic: "phase-10-wire"
  action: "A321: ✅ done (2026-08-24) — frontend test files 결정 wire (`slo-dashboard.test.tsx` NEW 3 NEW vitest cases + `slo-i18n-ssot.test.ts` NEW 2 NEW vitest cases = 5 NEW vitest cases PASS 결정 wire 보존). 결정 wire 일자: 2026-08-24."
  owner: "Amelia (Developer)"
  status: done  # 2026-08-24 — A321 frontend test files 결정 완료.

- id: "phase-10-wire-A322"
  epic: "phase-10-wire"
  action: "A322: ✅ done (2026-08-24) — handoff + MEMORY.md hook + commit-msg 결정 wire = (1) `memory/handoff-2026-08-24-phase-10-wire-done.md` NEW auto-memory handoff 신규 결정 wire (A313~A322 10/10 결정 wire + cj-style 103번째 진입 + 7 ACs PRD §F26.1~§F26.7 verbatim 78 sub-ACs pre-flight + CR lessons applied 14종 + D-DEFER-* tracking + Epic 1 ~ Epic 17 + Phase 3 ~ Phase 9 + 1st release cycle 정합 보존 + next 옵션 결정 wire 보류 + frontmatter `metadata.type: project`) / (2) `memory/MEMORY.md` MODIFIED handoff-2026-08-24-phase-10-wire-done hook index 신규 EXTENSION + Phase 10 section header update 2-entry-point → 3-entry-point pattern PRD entry DONE + spec entry DONE + wire DONE 진입 정합 보존 / (3) `_bmad-output/implementation-artifacts/commit-msg-phase-10-wire.txt` NEW (THIS commit message file 결정 wire) / (4) atomic commit via `git commit -F <file>` (CR 9-6 D5 prevention + PowerShell here-string 회피) + git push origin 9-3-dev-2026-08-17 결정 wire. 결정 wire 일자: 2026-08-24."
  owner: "Charlie (Senior Dev)"
  status: done  # 2026-08-24 — A322 handoff + MEMORY.md hook + commit-msg 결정 완료.

"""

# Insert before line at end_idx
new_lines = lines[:end_idx] + new_entries.splitlines(keepends=True) + lines[end_idx:]

with open(file_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print(f"Appended A313-A322 block. New file size: {sum(len(l) for l in new_lines)} chars")
