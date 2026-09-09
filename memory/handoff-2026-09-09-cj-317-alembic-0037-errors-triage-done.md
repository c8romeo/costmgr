# cj-317 alembic 0037 errors triage + fix — Handoff

> **Sprint**: cj-317 alembic 0037 errors triage + fix (cj-style 273번째)
> **Date**: 2026-09-09 KST (D-5)
> **Status**: ✅ **CLOSED ✅ HONEST** (compressed entry+wire atomic single sprint, sprint-status v4.89 → v4.90 EXTENSION)
> **Source code change**: 0 source files (TEST BUG 단독 fix)
> **Test verification**: 22 errors → 22 passed, 79 passed regression check, 0 regressions

---

## §1 Sprint Overview

cj-317 은 **cj-307 carryover 의 HIGH RISK item** 중 두 번째 (Phase A item 2). cj-316 (`1281ca5`) 의 Phase A item 1 CLOSED 직후 진입. Triage 결과: **22 errors 모두 TEST BUG** (migration source code 자체는 OK).

---

## §2 Sprint Scope (7 files = 3 MODIFIED tests + 4 meta atomic)

| File | Type | LOC | Description |
|---|---|---|---|
| `tests/api/core/test_epic_15_alembic_0037_external_identities.py` | MODIFIED test | +1/-1 | `parents[2]` → `parents[3]` (cj-307 carryover scope, **22 errors → 22 passed**) |
| `tests/api/core/test_epic_15_sso_jit_provisioning.py` | MODIFIED test | +1/-1 | `parents[2]` → `parents[3]` (bonus correction, **4 skipped preserved** PRE-EXISTING missing python3-saml) |
| `tests/api/core/test_epic_15_sso_validator.py` | MODIFIED test | +1/-1 | `parents[2]` → `parents[3]` (bonus correction, **9 skipped preserved** PRE-EXISTING missing python3-saml) |
| `phase-30-cj-317-alembic-0037-errors-triage-entry-2026-09-09.md` | NEW content | ~280 | sprint doc 9-section §1~§9 |
| `commit-msg-cj-317.txt` | NEW meta | ~75 | commit message |
| `handoff-2026-09-09-cj-317-alembic-0037-errors-triage-done.md` | NEW meta | ~140 | 본 handoff |
| `sprint-status.yaml` | MODIFIED meta | +A734 +last_updated_note_v4_90 | v4.89 → v4.90 EXTENSION |
| `memory/MEMORY.md` | MODIFIED meta | +cj-317 hook +active sprint state | hook EXTENSION |

---

## §3 Triage — TEST BUG (migration source code OK)

### 3.1 Root cause
22 errors 모두 setup fixture `migration_content` 실패:
- Test: `tests/api/core/test_epic_15_alembic_0037_external_identities.py:15`
- `REPO_ROOT = Path(__file__).resolve().parents[2]` → wrong (gives `tests/`)
- Actual path needed: `<repo_root>/apps/api/alembic/versions/0037_...`
- Resolved wrong path: `tests/apps/api/alembic/versions/0037_...` (does NOT exist)

### 3.2 Fix
- `parents[2]` → `parents[3]` (1 character change per file)
- Verified by similar working test: `test_epic_16_alembic_0038_tenant_idps.py:15` uses `parents[3]`

### 3.3 Migration source code unchanged
- `apps/api/alembic/versions/0037_epic_15_sso_external_identities.py` unchanged
- 22/22 tests pass after fix → confirms migration code is correct

---

## §4 Bonus Correction — 2 sso test files

### 4.1 Discovery
`grep -rn "REPO_ROOT = Path(__file__).resolve().parents" tests/api/core/` revealed 2 additional files with the same `parents[2]` bug:
- `test_epic_15_sso_jit_provisioning.py:18` (4 tests silently broken)
- `test_epic_15_sso_validator.py:15` (9 tests silently broken)

### 4.2 After fix
- 13 tests still skip (PRE-EXISTING missing `python3-saml` dependency)
- Intentional `pytest.skip()` design preserved (module load failures → graceful skip)

### 4.3 CR 11-3 honest-DEFER 정직 회복
- sso test path fix = bonus correction (cj-307 carryover scope 외)
- sso module load failures = PRE-EXISTING missing dependency → honestly DEFER

---

## §5 Verify Gate 결과

### 5.1 cj-307 carryover 의 22 errors fix
- `tests/api/core/test_epic_15_alembic_0037_external_identities.py`
- 22 errors (was) → **22 passed (now)** ✅

### 5.2 sso tests bonus fix
- 13 skipped preserved (PRE-EXISTING missing python3-saml)

### 5.3 Combined regression check
- 79 tests passed (cj-316 tests + alembic 0037 tests + Phase 4 health + exception handlers)
- 0 regressions ✅

### 5.4 Migration source unchanged
- 0 alembic 변경
- migration 자체 정합 (revision + down_revision + 9 columns + 4 indexes + 2 CHECK constraints + 4 RLS policies + 2 downgrade paths 모두 OK)

---

## §6 결정 wire 보존

### 6.1 결정 wire 보존 항목
- Pilot W1 launch D-day 2026-09-14 KST
- cj-309b B-1 Pilot candidate outreach (Tier 1 5 + Tier 2 3 = 8, D-2 발송 honestly DEFER)
- Resend (OQ-EPIC30+-2 v2) swap
- cj-307 aal1 minimum fix
- cj-304 4 critical gaps fix
- cj-300 APScheduler KST
- capability matrix v1.54 EXTENSION
- audit_action EXTENSION
- **45 → 46 sprints** 결정 wire 보존

### 6.2 Phase A 완료 결정 wire
- Phase A item 1 (cj-316) ✅ CLOSED
- Phase A item 2 (cj-317 alembic 0037) ✅ CLOSED ← 본 sprint
- Phase B (MEDIUM RISK items) — 다음 sprint
- Phase C (LOW RISK honestly DEFER post-W1)

---

## §7 CR 11-3 honest-DEFER 273번째

### 7.1 결정 wire chain
- cj-282 (220번째) → ... → cj-316 (272번째) → **cj-317 (273번째, 본 sprint)**
- **cumulative 45 → 46 sprints** 결정 wire 보존
- sprint-status v4.89 → **v4.90 EXTENSION** 결정 wire (A734 + last_updated_note_v4_90)

### 7.2 정직 회복
- 3 MODIFIED tests (1 char each: `parents[2]` → `parents[3]`)
- 0 source code 변경
- 0 alembic 변경
- 37 pins unchanged
- 14 job matrix unchanged
- PRD v7.0 §F/§M/§R unchanged
- capability matrix v1.54 EXTENSION preserved
- audit actions EXTENSION preserved

### 7.3 CR 11-3 honest-DEFER scope 정직 회복
- cj-317 의 main fix = 22 errors → 22 passed (FULL FIX, cj-307 carryover scope)
- cj-317 의 bonus fix = 2 sso test paths corrected (cj-307 carryover scope 외)
- sso 13 skipped = PRE-EXISTING missing python3-saml → honestly DEFER 보존

---

## §8 결정 보류 + 결정 wire 일자

### 8.1 결정 보류 (운전자)
다음 옵션 (운전자 결정 wire 보류):
① **옵션 (a, RECOMMENDED next) cj-314 wire HIGH** (Phase B item, cj-style 274번째, ~1-2h) — Phase 30 scheduled reports 3 + Phase 5 capability integration 2 + Phase 3 hook migration
② 옵션 (b) cj-314 wire LOW (Phase C honestly DEFER 유지, post-W1)
③ 옵션 (c) cj-313 close-out retro (~30min, docs-only)
④ 옵션 (d) cj-312 close-out retro (~30min, docs-only)
⑤ 옵션 (e) cj-309b B-1 Pilot candidate outreach (D-2 발송, 운전자 결정)
⑥ 옵션 (f) PRD v2 EXTENSION (cj-314 wire HIGH 후)

### 8.2 결정 wire 일자
- **2026-09-09 KST (D-5)**

### 8.3 Honestly DEFER 결정 wire 보존
- ① Pilot launch D-day (2026-09-14) → 비용 발생 결정 wire 보류
- ② W1~W8 weekly follow-up (launch day 부터)
- ③ PRD v2 EXTENSION (cj-314 fix 후)
- ④ 비용 발생 항목 모두 (사용자 결정 wire, launch day 까지 honestly DEFER)
- ⑤ sso 13 skipped tests (PRE-EXISTING missing python3-saml)

---

## §9 Cross-references + CR 11-3 정직 회복

### Cross-references
- **cj-314 entry** (`3e2ed73`) — 88 items 의 risk-prioritized 분류 출처
- **cj-316 wire** (`1281ca5`) — Phase A item 1 closed (cj-317 의 prerequisite, cj-style 272nd)
- **cj-313 wire** (`cfe5eca`) — pytest rootdir 정정 (cj-317 의 prerequisite, cj-style 270th)
- **cj-317** (본 sprint) — alembic 0037 errors triage + fix (cj-style 273rd, Phase A item 2 closed)

### 결정 wire 정직 회복
- 3 MODIFIED tests (1 char each: `parents[2]` → `parents[3]`)
- 결정 wire 보존: cj-307~cj-316 wire/entry 결정 wire 그대로
- CR 11-3 honest-DEFER 273번째 정직 회복 (Phase A item 2 closed, scope 정직 회복)

---

**CJ-317 결정 wire 보존 완료**

**CR 11-3 honest-DEFER 273번째 결정 wire chain: cj-282 (220번째) → ... → cj-316 (272번째) → cj-317 (273번째, 본 sprint)**

**Next**: cj-314 wire HIGH (Phase B item, RECOMMENDED next) 또는 cj-314 wire LOW (Phase C honestly DEFER) 또는 cj-313 close-out retro
