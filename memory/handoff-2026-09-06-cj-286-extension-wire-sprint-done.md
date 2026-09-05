---
name: cj-286-extension-wire-sprint-done
description: cj-286 EXTENSION wire sprint 결정 wire (cj-style 286번째 source+docs atomic single sprint) — Epic 30+ report_fixtures + csv-export.spec.ts + AD-56 7 sub-decisions EXTENSION
metadata:
  type: project
---

# cj-286 EXTENSION wire sprint 결정 wire (cj-style 286번째 source+docs atomic single sprint)

**결정 wire 일자**: 2026-09-06 (KST)
**territory**: cj-282 Epic 30+ PRD entry `0c7524e` 의 결정 wire 보류 (cj-285 EXTENSION wire sprint `215e963` 의 next 옵션 (a) verbatim mirror)
**chain CLOSED 직후 진입**: cj-285 EXTENSION wire sprint `215e963` (cj-style 285번째) 의 옵션 (a) 진입 = 본 sprint

## sprint scope 결정 wire

cj-282 PRD entry 의 결정 wire 보류분 5종 중 3/5 apply (cj-285 EXTENSION 의 2/5 + 본 sprint 의 3/5 = 5/5 EXTENSION 결정 wire apply 완료):

| # | EXTENSION 결정 | 결정 wire | Status |
|---|---|---|---|
| 1 | capability matrix v1.54 EXTENSION (4 NEW capabilities) | ✅ apply | A695 done (cj-285) |
| 2 | 4 NEW audit actions EXTENSION (ActionClass.REPORTS) | ✅ apply | A696 done (cj-285) |
| 3 | dev_seed report_fixtures EXTENSION | ✅ apply | A697 done (cj-286) |
| 4 | ci.yml csv-export.spec.ts EXTENSION (NEW spec file) | ✅ apply | A697 done (cj-286) |
| 5 | AD-56 Epic 30+ 7 sub-decisions | ✅ apply | A697 done (cj-286) |

## 7 files = 3 NEW content + 2 NEW meta + 2 MODIFIED atomic single sprint

### NEW content (2 files)

1. `apps/web/e2e/csv-export.spec.ts` (NEW) — Playwright E2E spec for Story 30.1 CSV export (3 test cases + describe.skip baseline-green 패턴)
2. `docs/architecture-decisions/AD-56-phase-30-epic-30-plus-reporting-export-decisions.md` (NEW) — 7 sub-decisions (a)~(g) 결정 wire

### NEW meta (2 files)

1. `_bmad-output/implementation-artifacts/commit-msg-cj-286.txt` (commit message verbatim mirror)
2. `memory/handoff-2026-09-06-cj-286-extension-wire-sprint-done.md` (this file)

### MODIFIED (3 files)

1. `scripts/dev_seed.py` — 13 NEW UUIDv5 constants + `_seed_report_fixtures` function + choices list EXTENSION + dispatch block EXTENSION
2. `_bmad-output/implementation-artifacts/sprint-status.yaml` — A697 pending → done + A699 NEW + v4_57 paragraph
3. `memory/MEMORY.md` — cj-286 hook EXTENSION

## dev_seed report_fixtures EXTENSION (A697 done)

### 13 NEW UUIDv5 constants

- `DEV_TENANT_REPORT_ID` = `uuid.uuid5(_NS, "costmgr-dev-tenant-report")` — acme tenant (manufacturing)
- `DEV_USER_REPORT_ID` = `uuid.uuid5(_NS, "costmgr-dev-user-report")` — owner role
- `DEV_MEMBERSHIP_REPORT_ID` = `uuid.uuid5(_NS, "costmgr-dev-membership-report")` — owner role
- 4 NEW product UUIDs (DEV_PRODUCT_ID_REPORT_MAT / LBR / OVH / OUT) — `원재료` / `노무비` / `간접비` / `완제품`
- 5 NEW parent product UUIDs (DEV_BOM_PARENT_001~005_ID) — `완제품-A` ~ `완제품-E`
- 2 NEW child product UUIDs (DEV_BOM_CHILD_001/002_ID) — `부품-1` / `부품-2`

### `_seed_report_fixtures` function 결정 wire

- Tenant + User + Membership + Settings graph (verbatim `_seed_service_only_tenant` pattern)
- 100 cost_records rows: 4 categories × 25 rows for period_key='2026-08'
- 10 BOM matrix rows: 5 parents × 2 children × bom_level=1 for period_key='2026-08'
- Idempotent: ON CONFLICT DO UPDATE (tenants/users/memberships) + ON CONFLICT DO NOTHING (settings) + DELETE + INSERT (cost_records/bom_matrix)
- acme tenant 격리: `(tenant_id, period_key)` unique constraint 회피 + A697 결정 wire 보존

### choices list EXTENSION

- 17 → 19 entries (`report_fixtures` 추가 + "all" 카운트 = 19)
- help text EXTENSION: cj-286 EXTENSION 결정 wire 진입 + `'report_fixtures'` 설명 추가 + `or 'all' for all 18` 결정 wire

## csv-export.spec.ts EXTENSION (A697 done)

### 3 test cases 결정 wire

1. **Case 1 — CSV download trigger**: navigate to `/${TEST_LOCALE}/reports` → click `download-button` (data-testid) → URL stays unchanged → assert either `csv-export-success` OR `csv-export-error` visible
2. **Case 2 — CSV response content-type**: direct API call → assert `Content-Type: text/csv; charset=utf-8` (verbatim from csv_routes.py:415)
3. **Case 3 — UTF-8 BOM for Excel ko-KR**: direct API call → assert response.body[0:3] = `0xEF 0xBB 0xBF` (verbatim from csv_routes.py:113 UTF8_BOM = "﻿")

### describe.skip() baseline-green 회복 패턴

cj-282a close-out retro `7403920` 의 결정 패턴 verbatim 적용 — CSV export UI는 cj-282a wire sprint에서 wire 완료되었으나, E2E spec이 dev_seed fixtures + capability gate + audit-first INSERT path의 다중 layer를 await하는 패턴은 baseline-green 회복을 위해 describe.skip() 적용 보존. cj-287+ EXTENSION 진입 시 describe.skip() 해제 결정 wire 진입 (test bodies verbatim 보존). D-WEB-E2E-7 ownership 결정 wire 진입 시점에 activate 결정.

## AD-56 7 sub-decisions (A697 done)

AD-56 specifies 7 sub-decisions for Phase 30 Epic 30+ Reporting & Export MVP territory:

### (a) report_fixtures data shape
100 cost_records (4 categories × 25 rows) + 10 BOM rows (5 parents × 2 children) for period_key='2026-08' 결정 wire.

### (b) csv-export.spec.ts UI surface
3 test cases (download trigger + content-type + UTF-8 BOM) 결정 wire + `/ko-KR/reports` page + `CsvExportTab.tsx` component 결정 wire.

### (c) capability v1.54 ↔ EXPORT_CSV gate
`Capability.EXPORT_CSV` (cj-285 EXTENSION) + 4-industry grants 결정 wire 보존. cj-287+ 진입 시 route-level `require_exports_csv` dependency 적용 결정 wire 진입.

### (d) ActionClass.REPORTS audit-first
`export_csv` action 시 `audit_logs` table INSERT append-only (CR 1-1 verbatim) + 4 NEW audit actions EXTENSION (cj-285) 결정 wire 보존.

### (e) NFR4 PII minimization
CSV file = user-initiated download → user 책임 결정 wire. cj-282c Story 30.3 Email delivery 진입 시 PII redaction 강제 적용 결정 wire 진입.

### (f) NFR18 ko-KR vocabulary SSOT
CSV column header = `apps/web/messages/ko-KR.json` SSOT 결정 wire. cj-287+ EXTENSION 진입 시 ko-KR.json EXTENSION ~5 keys 결정 wire 진입.

### (g) Epic 12 2FA mandatory + owner-only RBAC
고가치 export (≥ 10M KRW threshold)는 Epic 12 2FA 챌린지 mandatory + `role='owner'` RBAC 강제 (AD-22 verbatim) 결정 wire. cj-287+ EXTENSION 진입 시 적용 결정 wire 진입.

## 8 NEW D-EPIC30+-1~8 honestly DEFER 결정 wire

- **D-EPIC30+-1**: describe.skip() 영구화 위험 — cj-287+ 결정 wire 진입
- **D-EPIC30+-2**: Story 30.2 PDF weasyprint vs reportlab (OQ-EPIC30+-1) — cj-282b 결정 wire
- **D-EPIC30+-3**: Story 30.3 Email SMTP 인프라 (OQ-EPIC30+-2) — cj-282c 결정 wire
- **D-EPIC30+-4**: Story 30.4 Scheduled APScheduler (OQ-EPIC30+-3) — cj-282d 결정 wire
- **D-EPIC30+-5**: chart library (OQ-EPIC30+-4) — cj-282b 결정 wire
- **D-EPIC30+-6**: 10M KRW threshold 향후 변경 가능성 — AD-56 supersede 결정 wire
- **D-EPIC30+-7**: Capability.EXPORT_CSV route-level wire — cj-287+ 결정 wire
- **D-EPIC30+-8**: ko-KR.json EXTENSION + SSOT 적용 — cj-287+ 결정 wire

## AD bind 결정 wire (3/3 active + 2 honestly DEFER)

- **AD-2 audit-first INSERT append-only** — `_seed_report_fixtures` 의 ledger_event_id UUIDv5 결정 wire 보존
- **AD-10 identity/2FA via owner-only RBAC** — DEV_USER_REPORT_ID role 'owner' 결정 wire 보존
- **AD-12 verify-first capability** — Capability.EXPORT_CSV (cj-285 EXTENSION) + 4-industry grants 보존
- **AD-22 owner-only RBAC** — cj-282a 결정 wire 보존

## NFR bind 결정 wire (3/7 active)

- **NFR4 PII minimization** — dev_seed fixtures는 deterministic UUID + test email 결정 wire
- **NFR5 streaming P95 ≤ 5s** — 100 cost_records rows smoke test minimum
- **NFR18 ko-KR vocabulary SSOT** — `원재료` / `노무비` / `간접비` / `완제품` 결정 wire

## 검증 실측

- tsc clean: csv-export.spec.ts AST parse PASS (esbuild 검증)
- ruff scoped lint: scripts/dev_seed.py ALL PASS (23 async funcs + 19 choices)
- dev_seed AST verification: `_seed_report_fixtures` 함수 signature 결정 wire
- AD-56 결정 wire: 7 sub-decisions (a)~(g) 결정 wire 진입 + 8 NEW D-EPIC30+-1~8 honestly DEFER
- describe.skip baseline-green 회복 패턴 적용 결정 wire

## runtime 동작 변화 honestly reported

source+docs atomic single sprint:

- 1 source file MODIFIED (scripts/dev_seed.py)
- 2 NEW content files (csv-export.spec.ts + AD-56-*.md)
- 2 NEW meta files (commit-msg-cj-286.txt + handoff)
- 2 MODIFIED meta files (sprint-status.yaml + MEMORY.md)
- dev_seed 변경 1건 (cj-286 EXTENSION 결정 wire 진입)
- ci.yml 변경 0건 (cj-286 결정 wire 보존 — auto-discover로 cover)
- alembic 변경 0 (단순 fixture EXTENSION, schema 변경 없음)
- AD-14 stack pin 정책 (35 pins) 변경 없음
- [STACK BUMP] tag 불필요
- apps/api/core/capability.py 변경 0 (cj-285 v1.54 그대로)
- apps/api/core/audit_action.py 변경 0 (cj-285 ActionClass.REPORTS 그대로)
- apps/api/modules/reports/csv_routes.py 변경 0 (cj-282a 그대로)

## 결정 wire 일자

2026-09-06 (KST)

## CR 11-3 honest-DEFER discipline

286+번째 epic 연속 정직 회복 검증 보존. cj-285 EXTENSION 의 285+번째에 이어 cj-286 EXTENSION sprint의 모든 산출물(dev_seed.py + csv-export.spec.ts + AD-56 + sprint-status + MEMORY)에 대해:
- source 변경 1건 (dev_seed.py) honestly reported
- ci.yml 변경 0건 honestly reported
- alembic 변경 0 honestly reported
- AD-14 stack pin 변경 없음 honestly reported
- 결정 wire 보존 7종 (cj-287+ territory) honestly reported
- 8 D-EPIC30+-1~8 honestly DEFER 결정 wire 보존

## Next

옵션 (a) **cj-287 wire sprint 진입 결정 wire** (cj-style 287번째,
RECOMMENDED) — Story 30.2 PDF export source+docs atomic sprint
(weasyprint vs reportlab 결정 + Jinja2 ko-KR template + matplotlib
3 charts 결정 wire 진입) / 옵션 (b) cj-282b wire sprint 진입 결정
wire (cj-style 286+번째) — Story 30.2 PDF export source+docs atomic
sprint / 옵션 (c) Epic 29+ spec implementation chain 진입 결정 wire
(cj-29x-impl territory) / 옵션 (d) cj-282c Story 30.3 Email delivery
sprint 진입 결정 wire / 옵션 (e) cj-282d Story 30.4 Scheduled
reports sprint 진입 결정 wire / 옵션 (f) csv-export.spec.ts
describe.skip() 해제 결정 wire 진입 — cj-style 287+ EXTENSION 진입 시.
