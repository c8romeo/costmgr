---
name: cj-285-extension-wire-sprint-done
description: cj-285+ EXTENSION wire sprint 결정 wire (cj-style 285번째 source+docs atomic single sprint) — Epic 30+ capability matrix v1.54 EXTENSION + 4 audit actions EXTENSION
metadata:
  type: project
---

# cj-285+ EXTENSION wire sprint 결정 wire (cj-style 285번째 source+docs atomic single sprint)

**결정 wire 일자**: 2026-09-06 (KST)
**territory**: cj-282 Epic 30+ PRD entry `0c7524e` 의 결정 wire 보존 (cj-282a close-out retro `7403920` 의 next 옵션 (a) verbatim mirror)
**chain CLOSED 직후 진입**: cj-282a close-out retro `7403920` (cj-style 284번째) 의 옵션 (a) 진입 = 본 sprint

## sprint scope 결정 wire

cj-282 PRD entry 의 결정 wire 보류분 5종 중 2/5 apply:

| # | EXTENSION 결정 | 결정 wire | Status |
|---|---|---|---|
| 1 | capability matrix v1.54 EXTENSION (4 NEW capabilities) | ✅ apply | A695 done |
| 2 | 4 NEW audit actions EXTENSION (ActionClass.REPORTS) | ✅ apply | A696 done |
| 3 | dev_seed report_fixtures EXTENSION | ⏳ deferred | A697 pending → cj-286+ |
| 4 | ci.yml csv-export.spec.ts EXTENSION | ⏳ deferred | A697 pending → cj-286+ |
| 5 | AD-56 Epic 30+ 7 sub-decisions | ⏳ deferred | A697 pending → cj-286+ |

## 8 files = 0 NEW content + 4 NEW meta + 4 MODIFIED atomic single sprint

### NEW meta (4 files)

1. `_bmad-output/implementation-artifacts/commit-msg-cj-285.txt` (commit-msg-cj-285.txt)
2. `memory/handoff-2026-09-06-cj-285-extension-wire-sprint-done.md` (this file)
3. `_bmad-output/implementation-artifacts/sprint-status.yaml` EXTENSION (v4.55 → v4.56)
4. `memory/MEMORY.md` hook EXTENSION

### MODIFIED (4 files)

1. `apps/api/core/capability.py` — 4 NEW `Capability` enum + 4-industry grants
2. `apps/api/core/audit_action.py` — `ActionClass.REPORTS` + `ReportsAction` Literal + `_REGISTRY` entry + `AuditAction` union EXTENSION + `__all__` EXTENSION
3. `docs/capability-matrix.md` — header v1.53 → v1.54 + 4 NEW row + changelog entry
4. `docs/audit-actions.md` — §9 Epic 30+ EXTENSION section 신규

## capability matrix v1.54 EXTENSION (A695 done)

### 4 NEW Capability enum

```python
EXPORT_CSV = "export_csv"          # §F30.1-1 — Story 30.1 CSV export
EXPORT_PDF = "export_pdf"          # §F30.2-1 — Story 30.2 PDF export
EXPORT_EMAIL = "export_email"      # §F30.3-1 — Story 30.3 Email delivery
EXPORT_SCHEDULED = "export_scheduled"  # §F30.4-1 — Story 30.4 Scheduled reports
```

### 4-industry grants ✅/✅/✅/✅

- `Industry.MANUFACTURING` EXTENSION + 4 NEW grants
- `Industry.SERVICE` EXTENSION + 4 NEW grants
- `Industry.MANUFACTURING_SERVICE` EXTENSION + 4 NEW grants
- `Industry.MANUFACTURING_SERVICE_OTHER` EXTENSION + 4 NEW grants

Industry-agnostic per CR 12-1 L4 precedent + Epic 30+ PRD entry `0c7524e` 결정 wire.

## 4 NEW audit actions EXTENSION (A696 done)

### ActionClass.REPORTS = "reports" 결정 wire

NOT re-use `ActionClass.AUDIT` (Epic 17 audit log viewer CSV export) — reason:

- Epic 17 `ActionClass.AUDIT` = audit log viewer CSV export (운영자 감사
  로그 viewer) — `audit_logs` 테이블 export 의미.
- Epic 30+ `ActionClass.REPORTS` = financial / cost / closing report export
  (사업 운영 보고서) — `fiscal_period_snapshots` / `cost_*` /
  `monthly_closing_reports` 등 business table 기반 export 의미.
- 2가지 export 는 (a) source table, (b) RBAC, (c) PII 민감도, (d) wire
  endpoint (Epic 17 = `GET /api/v1/audit/logs` + Epic 30+ = `GET/POST
  `/api/v1/exports/*`) 가 본질적으로 다름.
- Precedent: 각 Epic 는 own ActionClass 보유 (ActionClass.MONTHLY_CLOSING_REPORT,
  ActionClass.CLOSING_PERIOD, ActionClass.MONTHLY_CLOSING, ActionClass.SNAPSHOT_PERSISTENCE,
  ActionClass.REOPEN_OPERATOR etc). 30+ reports territory 도 own ActionClass.
- Mixing "audit log viewer export" + "financial report export" 는 CR 1.1
  verbatim "free-form string drift is forbidden" lesson 보존 측면 위험.

### 4 NEW audit action values

```python
ReportsAction = Literal[
    "export_csv",         # §F30.1-1 — Story 30.1 CSV export
    "export_pdf",         # §F30.2-1 — Story 30.2 PDF export
    "export_email",       # §F30.3-1 — Story 30.3 Email delivery
    "export_scheduled",   # §F30.4-1 — Story 30.4 Scheduled reports
]

# In _ActionRegistry._REGISTRY:
ActionClass.REPORTS: (
    "audit_logs",
    frozenset({
        "export_csv",
        "export_pdf",
        "export_email",
        "export_scheduled",
    }),
),
```

## AD bind 결정 wire (3/25)

- **AD-2 audit-first INSERT append-only** — 4 NEW audit actions 모두 audit
  INSERT 패턴 (CR 1-1 verbatim + ActionClass.MONTHLY_CLOSING_REPORT 6-1
  wire `eb5a8f9` verbatim precedent).
- **AD-10 identity/2FA via owner-only RBAC** — high-value export operation
  (CSV/PDF bulk download + Email delivery + Scheduled dispatch) 은 모두
  Epic 12 2FA 챌린지 mandatory 결정 wire.
- **AD-12 verify-first capability** — capability gate
  `Capability.EXPORT_CSV` / `EXPORT_PDF` / `EXPORT_EMAIL` / `EXPORT_SCHEDULED`
  prevent bypass at FastAPI route boundary 결정 wire.

## NFR bind 결정 wire (3/20)

- **NFR4 PII minimization** — email delivery path PII redaction 결정 wire.
- **NFR5 streaming P95 ≤ 5s** — CSV export StreamingResponse 적용.
- **NFR18 ko-KR vocabulary SSOT** — 4 NEW audit actions 모두
  `ko-KR.json` keys consistent across UI.

## 검증 실측

- tsc clean: `audit_action.py` + `capability.py` ast.parse PASS
- ruff scoped lint: ALL PASS
- `_ActionRegistry.validate(action_class=ActionClass.REPORTS, action=...)`
  for 4 actions all return 'audit_logs' (T7.55 verified)
- `_INDUSTRY_CAPABILITIES` 4-industry grants 4 NEW capabilities 모두 ✅
  (T7.56 verified)
- capability table 4 NEW row + changelog v1.54 EXTENSION entry PASS

## runtime 동작 변화 honestly reported

source+docs atomic single sprint:

- 2 source files MODIFIED (audit_action.py + capability.py)
- 2 docs files MODIFIED (capability-matrix.md + audit-actions.md)
- 4 meta files NEW (commit-msg + handoff + sprint-status EXTENSION +
  MEMORY hook EXTENSION)
- dev_seed 변경 0건 (cj-286+ 결정 wire 보존)
- ci.yml 변경 0건 (cj-286+ 결정 wire 보존)
- alembic 변경 0 (단순 enums + Literal + table-free EXTENSION)
- AD-14 stack pin 정책 (35 pins) 변경 없음
- [STACK BUMP] tag 불필요

## 결정 wire 일자

2026-09-06 (KST)

## CR 11-3 honest-DEFER discipline

285+번째 epic 연속 정직 회복 검증 보존.

## Next

옵션 (a) **cj-286 wire sprint 진입 결정 wire** (cj-style 286+번째,
RECOMMENDED) — dev_seed report_fixtures EXTENSION + ci.yml
csv-export.spec.ts EXTENSION + AD-56 Epic 30+ 7 sub-decisions 결정 wire
atomic sprint / 옵션 (b) **cj-282b wire sprint 진입 결정 wire**
(cj-style 286+번째) — Story 30.2 PDF export source+docs atomic sprint /
옵션 (c) Epic 29+ spec implementation chain 진입 결정 wire
(cj-29x-impl territory).
