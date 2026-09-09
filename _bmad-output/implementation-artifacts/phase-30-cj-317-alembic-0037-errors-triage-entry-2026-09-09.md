# cj-317 alembic 0037 errors triage + fix — Phase 30 Entry Sprint

> **Sprint**: cj-317 alembic 0037 errors triage + fix (cj-style 273번째, compressed entry+wire atomic single sprint)
> **Date**: 2026-09-09 KST (D-5)
> **Status**: ✅ **CLOSED ✅ HONEST** (sprint-status v4.89 → v4.90 EXTENSION, A734)
> **Territory**: Cost Engineering API / Alembic Migration Test Verification
> **Trigger**: cj-307 carryover 의 HIGH RISK item (cj-314 entry §4 의 risk-prioritized 분류 #1)

---

## §1 Sprint Overview

cj-317 은 **cj-307 carryover 의 88 items 중 HIGH RISK 로 분류된 alembic 0037 22 errors** 의 atomic single sprint fix 입니다. cj-316 의 Phase A item 1 CLOSED 직후 Phase A item 2 진입 (운전자 2026-09-09 결정 wire).

cj-314 entry 의 risk 분류에서 HIGH RISK 2건:
1. **alembic 0037 22 errors** (DB schema 검증) — Phase A item 2 ← 본 sprint
2. **cj-316 FastAPI on_event deprecation** — Phase A item 1 ✅ CLOSED (`1281ca5`)

cj-317 = Phase A item 2.

---

## §2 Sprint Scope (7 files = 3 MODIFIED tests + 4 meta atomic)

| File | Type | LOC | Description |
|---|---|---|---|
| `tests/api/core/test_epic_15_alembic_0037_external_identities.py` | MODIFIED test | +1/-1 | `parents[2]` → `parents[3]` (cj-307 carryover scope) |
| `tests/api/core/test_epic_15_sso_jit_provisioning.py` | MODIFIED test | +1/-1 | `parents[2]` → `parents[3]` (bonus correction, cj-307 carryover scope 외) |
| `tests/api/core/test_epic_15_sso_validator.py` | MODIFIED test | +1/-1 | `parents[2]` → `parents[3]` (bonus correction, cj-307 carryover scope 외) |
| `phase-30-cj-317-alembic-0037-errors-triage-entry-2026-09-09.md` | NEW content | ~280 | 본 sprint doc (9-section) |
| `commit-msg-cj-317.txt` | NEW meta | ~75 | commit message |
| `handoff-2026-09-09-cj-317-alembic-0037-errors-triage-done.md` | NEW meta | ~140 | handoff doc |
| `sprint-status.yaml` | MODIFIED meta | +A734 +last_updated_note_v4_90 | v4.89 → v4.90 EXTENSION |
| `memory/MEMORY.md` | MODIFIED meta | +cj-317 hook +active sprint state | hook EXTENSION |

**Note**: compressed entry+wire atomic single sprint (cj-style 273번째, cj-313/cj-316 와 동일 패턴).

---

## §3 Triage 결과 — TEST BUG (migration source code OK)

### 3.1 Root cause 분석

22 errors 모두 setup fixture `migration_content` 실패:
```
AssertionError: alembic 0037 missing
assert False
+  where False = exists()
+    where exists = WindowsPath('C:/Users/c8rom/Desktop/A/costmgr/tests/apps/api/alembic/versions/0037_epic_15_sso_external_identities.py').exists
```

Test code (line 15):
```python
REPO_ROOT = Path(__file__).resolve().parents[2]  # ❌ WRONG: gives tests/
ALEMBIC_0037 = REPO_ROOT / "apps" / "api" / "alembic" / "versions" / "0037_..."
```

`parents[2]` from `tests/api/core/test_epic_15_alembic_0037_external_identities.py`:
- `parents[0]` = `tests/api/core`
- `parents[1]` = `tests/api`
- `parents[2]` = `tests`  ← REPO_ROOT (WRONG)
- `parents[3]` = `<repo_root>` ← should be this

ALEMBIC_0037 의 actual resolved path = `<repo_root>/tests/apps/api/alembic/versions/0037_...` (does NOT exist).

### 3.2 Fix: `parents[2]` → `parents[3]`

Verified by similar working test:
- `tests/api/core/test_epic_16_alembic_0038_tenant_idps.py:15:REPO_ROOT = Path(__file__).resolve().parents[3]` ← correct pattern

### 3.3 Migration source code 검증

`apps/api/alembic/versions/0037_epic_15_sso_external_identities.py` 자체는 OK:
- `revision: str = "0037_epic_15_sso_external_identities"` ✓
- `down_revision: str | None = "0036_phase_4_backup_strategy"` ✓
- 외부_identities table + 9 columns + 4 indexes + 2 CHECK constraints + 4 RLS policies 모두 정상 작성됨 (수동 검증 완료)

**결론**: cj-317 은 **TEST BUG 단독 fix** (migration source code 변경 0건).

---

## §4 Bonus Correction — 2 sso test files (cj-307 carryover scope 외)

### 4.1 동일 `parents[2]` 버그 발견

`grep -rn "REPO_ROOT = Path(__file__).resolve().parents" tests/api/core/` 결과:
- `test_epic_15_alembic_0037_external_identities.py:15` → `parents[2]` ❌ (cj-307 carryover)
- `test_epic_15_sso_jit_provisioning.py:18` → `parents[2]` ❌ (cj-307 carryover scope 외)
- `test_epic_15_sso_validator.py:15` → `parents[2]` ❌ (cj-307 carryover scope 외)

### 4.2 sso tests 는 동일 fix 적용 후에도 13 skipped 보존

Before fix: 13 silently broken (path wrong)
After fix: 13 skipped (PRE-EXISTING missing `python3-saml` dependency)

Test skip 의 의도적 design:
```python
try:
    spec.loader.exec_module(module)
except Exception as exc:
    pytest.skip(f"jit_provisioning import failed: {exc}")
```

`python3-saml` (onelogin.saml2) is **not installed** in test env. sso tests 의 의도적 gracefully-skip behavior 보존.

### 4.3 CR 11-3 honest-DEFER 정직 회복 (cj-style 257th + 267th + 270th + 272th verbatim mirror)

**scope 정직 회복**:
- cj-307 carryover scope = 22 errors (test_epic_15_alembic_0037_external_identities.py only)
- cj-317 의 main fix = 22 errors → 22 passed (FULL FIX)
- cj-317 의 bonus fix = 2 sso test paths corrected (side-effect improvement, not in scope)
- 13 skipped PRE-EXISTING behavior (missing python3-saml) honestly DEFER 보존

---

## §5 Verify Gate 결과

### 5.1 cj-307 carryover 의 22 errors fix
```
.venv/Scripts/python.exe -m pytest tests/api/core/test_epic_15_alembic_0037_external_identities.py
→ 22 passed in 2.05s (was 22 errors in 0.40s)
```

Test coverage:
- TestMigrationShape: 11 tests (revision_id + down_revision_chain + table_creation + 7 columns + metadata_jsonb)
- TestIndexes: 4 tests (provider_puid_unique + user_provider + tenant_provider + last_used_at_desc)
- TestCheckConstraints: 2 tests (provider_check + puid_not_empty_check)
- TestRLSPolicies: 4 tests (rls_enabled + tenant_isolation + service_role_bypass + anon_block)
- TestDowngrade: 2 tests (drop_table + drop_rls)

### 5.2 sso tests bonus fix
```
.venv/Scripts/python.exe -m pytest tests/api/core/test_epic_15_sso_jit_provisioning.py tests/api/core/test_epic_15_sso_validator.py
→ 13 skipped (PRE-EXISTING missing python3-saml dependency, intentional pytest.skip() design preserved)
```

### 5.3 Combined verify (cj-316 + cj-317)
```
.venv/Scripts/python.exe -m pytest tests/api/test_main_lifespan.py tests/api/test_main_lifespan_14_1.py tests/api/core/test_epic_15_alembic_0037_external_identities.py tests/api/core/test_phase_4_health_check.py tests/api/m12_account/test_exception_handlers_registered.py
→ 79 passed, 17 warnings in 5.02s (0 failures, 0 errors, 0 regressions)
```

### 5.4 Migration source code unchanged
- `apps/api/alembic/versions/0037_epic_15_sso_external_identities.py` unchanged
- `apps/api/alembic/versions/0036_phase_4_backup_strategy.py` unchanged (down_revision target)
- alembic 전체 검증: revision + down_revision + 9 columns + 4 indexes + 2 CHECK constraints + 4 RLS policies + 2 downgrade paths 모두 정합

---

## §6 결정 wire 보존 (cj-307~cj-316 wire/entry 결정 wire 그대로)

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

### 6.2 cj-317 의 결정 wire (Phase A item 2 closed)
- 88 items 의 risk-prioritized triage 진입 (운전자 2026-09-09 결정 wire)
- Phase A item 1 (cj-316) ✅ CLOSED (`1281ca5`)
- **Phase A item 2 (cj-317 alembic 0037) ✅ CLOSED (본 sprint)**
- Phase B (MEDIUM RISK items: Phase 30 + Phase 5 capability + Phase 3 hook) — 다음 sprint
- Phase C (LOW RISK honestly DEFER post-W1)

---

## §7 cj-style 273번째 + CR 11-3 honest-DEFER

### 7.1 결정 wire chain
- cj-282 (220번째) → ... → cj-316 (272번째) → **cj-317 (273번째, 본 sprint)**
- **cumulative 45 → 46 sprints** 결정 wire 보존
- sprint-status v4.89 → **v4.90 EXTENSION** 결정 wire (A734 cj-317 + last_updated_note_v4_90)

### 7.2 정직 회복
- 3 MODIFIED tests (1 char each: `parents[2]` → `parents[3]`)
- 0 source code 변경 (apps/api/* unchanged)
- 0 alembic 변경 (migration 자체 unchanged, 검증 완료)
- 37 pins unchanged (cj-303 EXTENSION 보존)
- 14 job matrix unchanged (cj-style baseline-green 보존)
- PRD v7.0 §F/§M/§R unchanged
- capability matrix v1.54 EXTENSION preserved
- audit actions EXTENSION preserved

---

## §8 Cross-references

### 8.1 Related sprints
- **cj-314 entry** (`3e2ed73`) — 88 items 의 risk-prioritized 분류 출처
- **cj-316 wire** (`1281ca5`) — Phase A item 1 closed (cj-317 의 prerequisite, cj-style 272nd)
- **cj-313 wire** (`cfe5eca`) — pytest rootdir 정정 (cj-317 의 prerequisite, cj-style 270th)
- **cj-317** (본 sprint) — alembic 0037 errors triage + fix (cj-style 273rd, Phase A item 2 closed)

### 8.2 cj-style feedback
- `prioritize-mvp-hardening-before-deploy` (2026-09-07) — 본 sprint 의 trigger (HIGH RISK 먼저)
- `count-remaining-before-start` (2026-09-07) — 매 주요 업무 진입 직전 잔여 주요 업무 개수 안내

---

## §9 결정 보류 + 결정 wire 일자

### 9.1 결정 보류 (운전자)
다음 옵션 (운전자 결정 wire 보류):
① **옵션 (a, RECOMMENDED next) cj-314 wire HIGH** (Phase B item, cj-style 274번째, ~1-2h) — Phase 30 scheduled reports 3 + Phase 5 capability integration 2 + Phase 3 hook migration
② 옵션 (b) cj-314 wire LOW (Phase C honestly DEFER 유지, post-W1)
③ 옵션 (c) cj-313 close-out retro (~30min, docs-only)
④ 옵션 (d) cj-312 close-out retro (~30min, docs-only)
⑤ 옵션 (e) cj-309b B-1 Pilot candidate outreach (D-2 발송, 운전자 결정)
⑥ 옵션 (f) PRD v2 EXTENSION (cj-314 wire HIGH 후)

### 9.2 결정 wire 일자
- **2026-09-09 KST (D-5)**

### 9.3 Honestly DEFER 결정 wire 보존
- ① Pilot launch D-day (2026-09-14) → 비용 발생 결정 wire 보류
- ② W1~W8 weekly follow-up (launch day 부터)
- ③ PRD v2 EXTENSION (cj-314 fix 후)
- ④ 비용 발생 항목 모두 (사용자 결정 wire, launch day 까지 honestly DEFER)
- ⑤ sso 13 skipped tests (missing python3-saml, PRE-EXISTING honestly DEFER)

---

**CJ-317 결정 wire 보존 완료**

**CR 11-3 honest-DEFER 273번째 결정 wire chain: cj-282 (220번째) → ... → cj-316 (272번째) → cj-317 (273번째, 본 sprint)**

**Next**: cj-314 wire HIGH (Phase B item, RECOMMENDED next) 또는 cj-314 wire LOW (Phase C honestly DEFER) 또는 cj-313 close-out retro
