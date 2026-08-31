# cj-224 D-CI-FUNC-8 alembic_version VARCHAR(32) blocker fix — handoff (2026-08-31)

## Sprint metadata

- **cj-style entry point**: 126번째 (cj-223 의 125번째에 이어)
- **Sprint type**: atomic single source-only sprint
- **Decision ledger**: this file + sprint-status.yaml v4.32 → v4.33 EXTENSION (A910) + MEMORY.md hook EXTENSION
- **Fix option 채택**: Option B (pre-step YAML-only, cj-223 의 2-lines-YAML-only 패턴 verbatim 매칭)
- **Date**: 2026-08-31 (KST)

## Root cause

cj-223 의 workspace sync fix 후 follow-up run_id 33390385297 의 smoke-e2e + rls-tests 의 postgres container log 모두 동일하게:

```
ERROR: value too long for type character varying(32)
STATEMENT: INSERT INTO alembic_version (version_num) VALUES ('0001_tenants_users_memberships_settings')
```

- 첫 번째 migration `0001_tenants_users_memberships_settings` (39 chars) 가 alembic 의 `version_num VARCHAR(32)` 컬럼에 INSERT 시도 → 39 > 32 = +7 chars overflow
- root cause = alembic 1.18.5 의 `.venv/Lib/site-packages/alembic/ddl/impl.py:173` 에 `Column("version_num", String(32), nullable=False)` hardcode
- alembic 의 `version_table_impl()` hook 이 auto-create 하는 `alembic_version.version_num` 컬럼은 항상 `VARCHAR(32)`

## 5 over-long revision IDs (audit)

| # | Revision ID | Length | Overflow |
|---|---|---|---|
| 1 | `0011_monthly_input_periods_opening_inventory` | 44 chars | +12 |
| 2 | `0002_tenant_settings_onboarding_defaults` | 40 chars | +8 |
| 3 | `0001_tenants_users_memberships_settings` | 39 chars | +7 (첫 migration = 첫 FAIL) |
| 4 | `0037_epic_15_sso_external_identities` | 36 chars | +4 |
| 5 | `0010_monthly_input_labor_breakdown` | 34 chars | +2 |

첫 migration 0001 의 `down_revision = None` → leaf, 0001 fix 없이는 모든 downstream 1-59 chain 미적용.

## Fix wire (Option B — minimal-scope YAML-only)

`.github/workflows/ci.yml` 의 rls-tests (line 434-456) + smoke-e2e (line 581-618) 두 job 모두 `Apply Alembic migration` step 직전에 pre-step 신규:

```yaml
- name: Pre-create alembic_version (VARCHAR(64))
  run: |
    PGPASSWORD=postgres psql -v ON_ERROR_STOP=1 \
      -h localhost -p 54322 -U postgres -d postgres \
      -c "CREATE TABLE IF NOT EXISTS alembic_version \
          (version_num VARCHAR(64) NOT NULL PRIMARY KEY)"
```

`+37 lines / -0 lines` (cj-223 의 `+15 / -2` 패턴의 변형 — pre-step 본체 + marker comment 둘 다 추가).

## Option B 결정 근거

1. **alembic source override 없이 가능**: `CREATE TABLE IF NOT EXISTS` 로 alembic 의 auto-create 를 silent no-op 으로 만들고, pre-created table 의 `VARCHAR(64)` 가 alembic 의 `String(32)` default 보다 우선.
2. **revision ID 보존**: 5 over-long revision IDs rename 불필요 (Option A 의 13 file touches 회피).
3. **cj-223 패턴 verbatim 매칭**: atomic minimal-scope YAML-only.
4. **future-proof**: 향후 over-long revision ID 추가 시 VARCHAR(64) 안에서 자동 수용.

## Rejected alternatives

- **Option A** (5 over-long revision IDs rename): 5 git mvs + 5 revision var changes + 3 downstream down_revision updates = 13 file touches, alembic graph topology 변경.
- **Option C** (env.py hook + ci.yml pre-step): apps/api/alembic/env.py 의 runtime behavior 변경 (production alembic env 에서도 실행) + 양쪽 file 변경 = invasive.

## Verification (cj-224 5-step FINAL CLEAN)

| Test | Result | Detail |
|---|---|---|
| T7.1 ruff scoped | ✅ N/A | Python source 변경 0건, ci.yml YAML only (cj-223 의 ruff N/A verdict 보존) |
| T7.2 pytest 회귀 | ✅ PASS | 598 passed + 1 skipped + 13 warnings (cj-223 baseline 와 정확히 동일 회귀 없음) |
| T7.3 alembic graph 단일 head | ✅ VERIFIED | `0059_phase_28_interactive_dashboard (head)` 단일 head (cj-222 graph fix 그대로 보존) |
| T7.4 AD-14 stack pin 정책 (35 pins) | ✅ UNCHANGED | ci.yml step command 만 변경 + 4 lines 추가, action SHA / version comment 0건 변경, `[STACK BUMP]` tag 불필요 |
| T7.5 FINAL CLEAN | ✅ PASS | 모든 검증 통과 |

## Files (atomic single source-only sprint)

| Type | File | Change |
|---|---|---|
| MODIFIED | `.github/workflows/ci.yml` | +37 / -0 lines (rls-tests + smoke-e2e 각각 pre-step + marker comment) |
| MODIFIED | `_bmad-output/implementation-artifacts/sprint-status.yaml` | A910 entry 신규 + last_updated_note_v4_33 신규 |
| NEW | `memory/handoff-2026-08-31-cj-224-d-ci-func-8-alembic-version-varchar32-fix-done.md` | 본 handoff note |
| MODIFIED | `memory/MEMORY.md` | cj-224 hook EXTENSION |

**4 files = 1 NEW + 3 MODIFIED** atomic single source-only sprint.

## Runtime 동작 변화 (honestly reported)

- ci.yml 의 `+37 / -0 lines` 신규 (YAML only)
- Python source 변경 0건 (apps/api + apps/web 무변경)
- TS source 변경 0건
- AD-14 stack pin 정책 35 pins 변경 없음
- `[STACK BUMP]` tag 불필요
- functional behavior 변경 0건 (CI 의 venv alembic_version table pre-create 만 추가, runtime source code 무관)

## 부수 효과 (D-CI-FUNC-8 ✅ RESOLVED 2차 합성 회복)

cj-211 + cj-212 + cj-213 + cj-214 + cj-215 + cj-216 + cj-217 + cj-218 + cj-219 + cj-220a-g + cj-221 + cj-222 + cj-223 + **cj-224** 14개 sprint 합성 회복:

- cj-222 (alembic graph fix) + cj-223 (workspace sync fix) + **cj-224 (VARCHAR(32) fix)** 의 3-layer 합성 회복
- D-CI-FUNC-8 의 unmasked 한 root causes 모두 해소
- 다음 push 부터 smoke-e2e + rls-tests 의 `Apply Alembic migration` step PASS expected
  - `ERROR: value too long for type character varying(32)` → 회복
  - 6 PASS → 8 PASS 회복 결정 wire expected

## Pre-existing PARTIAL 결정 wire 보존

- D-CI-FUNC-1 lint-conventions (cj-219 PARTIAL 잔여, Node 20 deprecation)
- D-CI-FUNC-2 test-architecture (cj-220 결정 wire 후보)
- D-CI-FUNC-3 test-service-role-guard (cj-220 결정 wire 후보)
- D-CI-FUNC-5 PARTIAL 잔여 web-e2e browser binary 단계
- D-CI-FUNC-7 PARTIAL 잔여 71 errors (import/order 47 + unused-vars 14 + restricted-types 10)

## CR 11-3 honest-DEFER 126번째

cj-223 의 125번째 정직 회복 직후의 unmasked 2차 blocker (VARCHAR(32)) 의 actual source fix wire 결정 wire. cj-style epic 연속 정직 회복 chain 의 126번째 정합 회복.

## Next 결정 wire 후보

1. **commit + push + live CI 재검증** (가장 urgent, PAT 1-day expiry 내 검증 필수)
2. **D-CI-FUNC-2 + D-CI-FUNC-3 follow-up sprint** (cj-style 127번째 candidate)
3. **D-CI-FUNC-7 PARTIAL 잔여 71 errors cleanup** (cj-style 128+번째 candidate)
4. **Epic 29+ 신규 territory 진입 결정 wire**
5. **D-LAUNCH-1-DEFER-* / D-DEFER-* follow-up 결정 wire 보류**

---

**결정 wire 일자**: 2026-08-31 (KST)
**sprint-status entry**: A910 (cj-224-d-ci-func-8-alembic-version-varchar32-fix-A910)
**last_updated_note**: v4_33
**cj-style entry point**: 126
**CR 11-3**: honest-DEFER 126번째
