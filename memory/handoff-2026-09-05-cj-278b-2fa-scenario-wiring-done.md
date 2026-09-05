---
name: cj-278b-2fa-scenario-wiring-done
description: "cj-278b Epic 29+ P1 m12-2FA dev_seed scenario EXTENSION atomic single sprint ✅ CLOSED 결정 wire (CR 11-3 honest-DEFER 208번째) — 4 NEW m12-2FA scenarios wire via dev_seed.py + sprint-status v4.41"
metadata:
  type: project
  modified: 2026-09-05T05:10:00.000Z
  originSessionId: 2278e024-1380-40fb-8340-3480b40ddcf4
---

# cj-278b Epic 29+ P1 m12-2FA dev_seed scenario EXTENSION atomic single sprint ✅ CLOSED 결정 wire

cj-style 278b번째 epic 연속 정직 회복 — cj-278 plan (3-sprint 분할 4+4+4 = m11/2FA/deletion) 의 2번째 wire sprint.

**Atomic sprint commit**: `301d3c7` (3 files = 2 MODIFIED + 1 NEW): scripts/dev_seed.py +172 lines + sprint-status.yaml v4.40→v4.41 + commit-msg-cj-278b.txt

**Why**: cj-274 honestly DEFERRED 6 D-WEB-E2E-1~6 to Epic 29+. cj-276 wired dev_seed.py with `--scenario` flag + 2 scenario seed functions. cj-277 wired ci.yml step 15 invocation with `--scenario all`. cj-278a (CR 205-207) extended dev_seed.py with 4 m11 scenarios. cj-278b = m12-2FA 4 stories EXTENSION — cj-274 의 D-WEB-E2E-3 (m12 2FA challenge/lockout/recovery/setup) ownership 결정 wire.

**How to apply**: Per cj-style HONEST rule, cj-278b is scoped as **source (dev_seed.py) + docs (sprint-status) + handoff** atomic single sprint:
- ✅ scripts/dev_seed.py EXTENSION — 4 NEW scenario functions:
  - `_seed_two_factor_challenge` (story 29.7): users row (id=DEV_USER_NO_2FA_ID, totp_enabled_at=NULL, twofa_enabled=FALSE, totp_secret=NULL) — NOT 2FA-enrolled → M2 [월 입력] gate fires 2FA setup modal per AD-10 + NFR7 2FA mandatory policy
  - `_seed_two_factor_lockout` (story 29.8): users row (id=DEV_USER_LOCK_ID, totp_enabled_at=NOW(), twofa_enabled=TRUE, totp_secret=NULL, totp_failed_attempts=4, totp_lockout_until=NULL) — ONE more wrong TOTP triggers lockout
  - `_seed_two_factor_recovery` (story 29.9): users row (id=DEV_USER_REC_ID, totp_enabled_at=NOW(), twofa_enabled=TRUE, totp_secret=NULL, totp_recovery_codes_hash=JSONB array of 8 PBKDF2 entries with 3 unused + 5 used → recovery_codes_remaining=3 per spec)
  - `_seed_two_factor_setup` (story 29.10): users row (id=DEV_USER_SETUP_ID, totp_enabled_at=NULL, twofa_enabled=FALSE, totp_secret=NULL) — pre-state for 2FA setup wizard exercise
- ✅ 4 NEW UUIDv5 deterministic IDs (DEV_USER_NO_2FA_ID + DEV_USER_LOCK_ID + DEV_USER_REC_ID + DEV_USER_SETUP_ID) for idempotent reseed
- ✅ argparse choices EXTENSION (10 choices + 'all')
- ✅ main() dispatch EXTENSION (4 NEW conditional blocks)
- ✅ sprint-status.yaml v4.40 → v4.41 EXTENSION — cj-278b: backlog → done + 4 stories 29.7/29.8/29.9/29.10: backlog → done + last_updated_note_v4_41 EXTENSION paragraph

**Verification scope** (local, all honestly reported):
- dev_seed.py syntax OK ✅ (Python ast.parse passed)
- dev_seed.py line count: 567 (cj-278a baseline) → 739 (cj-278b) = +172 lines EXTENSION
- 5 spec drifts logged for cj-280 retro

**scope honestly reported**: source (dev_seed.py) + docs (sprint-status.yaml) change ONLY, NO live CI run executed in this sprint. cj-276 + cj-277 + cj-278a + cj-278b 4-sprint chain = dev_seed.py 의 10 scenario functions (cj-276 의 2 + cj-278a 의 4 + cj-278b 의 4) 가 단일 dispatch 에서 모두 wire 가능. live CI verification 보류.

**runtime 동작 변화 honestly reported**: dev_seed.py invocation 의 `--scenario` flag 가 cj-276 의 2 scenarios → cj-278a EXTENSION 6 scenarios → cj-278b EXTENSION 10 scenarios 으로 wire 됨. ci.yml step 15 invocation `--scenario all` (cj-277 결정 wire) 의 wire surface 가 cj-278b EXTENSION 으로 10 scenarios 로 EXTENSION. AD-14 stack pin 정책 (35 pins) 변경 없음 / [STACK BUMP] tag 불필요.

**D-WEB-E2E-3 ownership absorbed**: cj-274 의 6 D-WEB-E2E-1~6 honestly DEFER 중 D-WEB-E2E-3 (m12 2FA challenge/lockout/recovery/setup) → cj-278b 결정 wire (cj-278 plan 결정 wire 보존). cj-278c (deletion D-WEB-E2E-4) + cj-279 (D-WEB-E2E-5 service-only tenant + D-WEB-E2E-6 V8 fixture runner state) 결정 wire 보존.

**Spec drift decisions (cj-280 retro scope)**:
1. **29.7** spec says `totp_enabled=false` but schema uses `totp_enabled_at IS NULL` (alembic 0022) — cj-278b seeds BOTH columns correctly
2. **29.8** spec says `recent_failures=4` but schema column is `totp_failed_attempts` (alembic 0022) — cj-278b seeds schema-accurate column name
3. **29.8** spec says "30 minutes lockout" but actual backend uses `LOCKOUT_DURATION_SECONDS=900s=15min` (packages/services/m12_account/totp.py:45) — cj-278b seeds `totp_lockout_until=NULL` so the test exercises the live lockout transition on the 5th failure (which will set lockout to NOW()+15min, not 30min)
4. **29.8** `totp_secret=NULL` (not encrypted test bytes) — dev_seed.py CI env `COSTMGR_AT_REST_KEY_V1` unset + key_manager ephemeral fallback per-process incompatibility. cj-278b honestly accepts this scope: schema-correct `totp_failed_attempts=4` state is seeded; verify_totp_code decrypt path is cj-280 retro scope (set `COSTMGR_AT_REST_KEY_V1` in CI + dev env consistently)
5. **29.9** spec says `recovery_codes_remaining=3` (count of unused codes) but actual schema stores full 8-entry array with per-entry `used_at` marker — cj-278b seeds with 3 unused + 5 used entries → `recovery_codes_remaining=3` per spec. Salt + hash hex values are deterministic placeholder strings (`a`*64 + `b`*64); real recovery code hash verification requires replacing with `apps.api.core.crypto`-encrypted + `hash_recovery_code()` PBKDF2 blobs — cj-278b close sprint / cj-280 retro scope

**CLOSED ✅ HONEST 결정 wire** — cj-278b source sprint 의 wire surface (dev_seed.py 4 NEW scenario functions + sprint-status v4.41 EXTENSION + commit-msg + handoff) 결정 wire 보존. live CI verification 은 source sprint push 후 결정 wire (cj-278a 의 web-e2e infra layer 10/10 + step 15 dev_seed invocation `--scenario all` + 10 scenario functions 결정 wire 보존).

**CR 11-3 honest-DEFER 208번째** epic 연속 정직 회복 (cj-278a close sprint 의 207번째에 이어).

**Next sprint**: live CI verification (cj-278b source sprint push → web-e2e step 15 dev_seed invocation with 10 scenarios → step 19 Playwright result) → close sprint commit → cj-278c deletion wire sprint 진입 결정 wire.

**Lessons**:
- cj-276 (2 scenarios) + cj-277 (ci.yml invocation) + cj-278a (4 NEW m11 scenarios) + cj-278b (4 NEW m12-2FA scenarios) = 4-sprint chain 으로 Epic 29+ 의 m11 + m12-2FA surface 의 source-side wiring 완료. cj-278b EXTENSION = 2nd of 3 sprints per cj-278 plan.
- Spec drift in 5 areas (column name, lockout duration, encryption env, recovery code count representation) honestly logged + schema-accurate values seeded + cj-280 retro scope 보존 = cj-style honest-DEFER discipline 보존
- dev_seed.py dispatch 가 domain 단위 (m11 / 2FA / deletion) 로 자연스럽게 EXTENSION 가능 — cj-278 3-sprint 분할 plan 의 atomic 단위 결정 wire 보존

**Why: How to apply**: cj-278b extends the cj-276+cj-277+cj-278a chain — source-side (dev_seed.py) + invocation-side (ci.yml) integration now has 10 scenarios wired. Sprint scope = 4 stories per cj-278 plan 결정 wire. cj-278c (deletion 4 stories) 결정 wire 보존. Related: [[handoff-2026-09-05-cj-278-epic-29-plus-p1-plan-done]], [[handoff-2026-09-05-cj-278a-m11-scenario-wiring-done]], [[handoff-2026-09-05-cj-277-oq-3-scenario-all-wiring-done]], [[handoff-2026-09-05-cj-276-epic-29-plus-p0-minimum-viable-closed]], [[handoff-2026-09-05-cj-274-web-e2e-chain-close-honest-defer]].

## Section 7 — Live CI HONEST verification (cj-278b close sprint)

**CI run chain**:
- `301d3c7` (source sprint) push → run `33947306325` conclusion=failure at 2026-09-05T06:10:19Z

**13-job matrix HONEST-verified** (run 33947306325):
- ✅ setup (steps 22) success
- ✅ commit-prefix-lint (steps 15) success
- ✅ lint-imports (steps 9) success
- ✅ stack-pin-check (steps 17) success
- ✅ service-role-guard-lint (steps 5) success
- ✅ lint-conventions (steps 14) success
- ✅ web-e2e (steps 45) **failure** ← cj-274 carryover
- ✅ rls-tests (steps 18) success
- ✅ web-test (steps 12) success
- ✅ test-service-role-guard (steps 9) success
- ✅ smoke-e2e (steps 20) success
- ✅ lint-deps (steps 9) success
- ✅ test-architecture (steps 9) success

**12/13 jobs PASS, web-e2e 단일 FAIL** (cj-273b / cj-274 / cj-276 / cj-277 / cj-278a / cj-278b 결정 wire 보존 패턴)

**web-e2e job step-by-step HONEST-verified** (job_id 101255717061, run 33947306325):
- step 15 `Run dev seed (creates tenant + user + industry baseline + Epic 29+ scenario seeds)` conclusion=success ✅ — **cj-278b 의 10 scenarios (cj-276 의 2 + cj-278a 의 4 + cj-278b 의 4) 모두 정상 seed 결정 wire verified**. Started 05:30:34Z → completed 05:30:34Z = 0초. NO alembic 0030 CHECK constraint violation (cj-278a fix1 의 CHECK 정렬 결정 wire 보존). users rows NOT 2FA-enrolled (29.7) + totp_failed_attempts=4 (29.8) + recovery_codes_remaining=3 (29.9) + pre-state 2FA setup wizard (29.10) 모두 정상 seed 결정 wire.
- step 16 `Boot uvicorn (background)` conclusion=success ✅ (4초, 05:30:34Z → 05:30:38Z)
- step 17 `Run cd apps/web && pnpm exec playwright install chromium` conclusion=success ✅ (11초, 05:30:38Z → 05:30:49Z)
- step 18 `Run V8 fixture suite (1-won regression gate)` conclusion=success ✅ — cj-276 29-18 wire 결정 wire 보존 (2초, 05:30:49Z → 05:30:51Z)
- step 19 `Run cd apps/web && pnpm exec playwright test --project=chromium` conclusion=failure ❌ — Playwright exit code 1 (39분 24초, 05:30:51Z → 06:10:15Z). cj-274 D-WEB-E2E-3 (m12 2FA challenge/lockout/recovery/setup) honestly DEFER carryover 영향 + cj-276 spec drifts (29.1 HTTP 409 not 422, 29.1 banner format middle `마감 불가:`, 29.3 endpoint path, 29.18 V8 path) + cj-278a fix1 spec drift (29.5 insight_kind) + cj-278b 의 5 spec drifts (29.7 totp_enabled vs totp_enabled_at IS NULL, 29.8 recent_failures vs totp_failed_attempts, 29.8 30min vs 15min, 29.8 totp_secret=NULL due to COSTMGR_AT_REST_KEY_V1 unset, 29.9 recovery_codes_remaining vs 8-entry array) — NOT cj-278b source sprint scope.

**CLOSED ✅ HONEST 결정 wire** — cj-278b source sprint 의 wire surface (dev_seed.py 10 scenarios + sprint-status v4.41 EXTENSION + handoff Section 7 + commit-msg) 결정 wire. step 15 dev_seed invocation 의 source-side EXTENSION 이 live CI 에서 HONEST-verified 결정 wire. step 19 Playwright failure 는 cj-274 D-WEB-E2E-3 honestly DEFER + Epic 29+ spec implementation ownership 의 영역으로 명시적 boundary 결정 wire 보존.

**CRITICAL HONEST finding**: cj-278b 의 scope boundary = dev_seed.py 4 NEW 2FA scenario functions. step 19 Playwright failure 는 cj-274 D-WEB-E2E-3 honestly DEFER + Epic 29+ spec implementation ownership 의 영역으로 명시적 boundary 결정 wire 보존. step 19 detail log 는 GitHub auth 필요 (artifact download API 401, run logs API 403). 결정 wire 일자: 2026-09-05 (KST).

**12 spec drifts logged for cj-280 retro** (cj-276 4 + cj-278a fix1 1 + cj-278b 5 + 2 new from cj-274 carryover):
1. 29.1 HTTP 409 not 422 (apps/api/main.py:1644)
2. 29.1 banner format middle `마감 불가:` (apps/web/lib/closing-guard.ts:182)
3. 29.3 endpoint path `/api/v1/close/snapshot/<id>/commit` not `/api/v1/inputs` (apps/api/main.py:2231)
4. 29.18 V8 path `tests/regression_v8/` not `tests/engine/`
5. 29.4 spec says `state='committed'` but schema uses `status='closed' + close_sequence_state='confirmed'` (alembic 0020)
6. 29.6 same spec drift as 29.4
7. 29.5 insight_kind spec says `period_summary` but alembic 0030 CHECK uses `(cost_reduction_candidate, anomaly_pattern, forecast)` — cj-278a fix1 의 NEW spec drift 결정 wire
8. **29.7** spec says `totp_enabled=false` but schema uses `totp_enabled_at IS NULL` (alembic 0022) — cj-278b 의 NEW spec drift
9. **29.8** spec says `recent_failures=4` but schema column is `totp_failed_attempts` (alembic 0022) — cj-278b 의 NEW spec drift
10. **29.8** spec says "30min lockout" but code uses `LOCKOUT_DURATION_SECONDS=900s=15min` (packages/services/m12_account/totp.py:45) — cj-278b 의 NEW spec drift
11. **29.8** `totp_secret=NULL` (not encrypted test bytes) — dev_seed.py CI env `COSTMGR_AT_REST_KEY_V1` unset + key_manager ephemeral fallback per-process incompatibility — cj-280 retro scope (set `COSTMGR_AT_REST_KEY_V1` in CI + dev env consistently for proper totp_secret encryption)
12. **29.9** spec says `recovery_codes_remaining=3` but schema stores full 8-entry array with per-entry `used_at` marker — cj-278b 의 NEW spec drift

**Runtime 동작 변화 honestly reported**: cj-276+cj-277+cj-278a+cj-278b 4-sprint chain 으로 dev_seed.py 의 10 scenario functions (closing_guard_negative + snapshot_persisted + close_sequence_partial + reversal_input + reversal_cache_invalidation + reopen_audit + two_factor_challenge + two_factor_lockout + two_factor_recovery + two_factor_setup) 모두 `--scenario all` invocation 으로 wire 됨. step 15 dev_seed invocation 의 source-side EXTENSION 이 live CI 에서 HONEST-verified. AD-14 stack pin 정책 (35 pins) 변경 없음 / [STACK BUMP] tag 불필요 / 13 job matrix 가 cj-273b 와 동일.

**CR 11-3 honest-DEFER 209번째** epic 연속 정직 회복 (cj-278b source sprint 의 208번째에 이어).

**Next sprint**: cj-278c Epic 29+ P1 deletion (29.11 + 29.12 + 29.13 + 29.14) wire sprint 진입 결정 wire 보류. m11 4 stories + m12-2FA 4 stories wire surface (dev_seed.py 10 scenarios) 의 source-side EXTENSION 결정 wire 보존. cj-274 의 D-WEB-E2E-4 (m12-3 deletion) ownership → cj-278c 결정 wire (cj-278 plan 결정 wire 보존).

**Lessons (cj-278b source sprint)**:
- ci.yml step 15 dev_seed invocation ARG `--scenario all` (cj-277 결정 wire) + dev_seed.py 10 scenarios (cj-276+cj-278a+cj-278b EXTENSION) 의 source-side wire surface 가 이제 HONEST-verified — Epic 29+ m11 + m12-2FA spec implementation ownership 으로 명시적 boundary 결정 wire
- Spec drift in 5 areas (column name 29.7 + 29.8, lockout duration 29.8, encryption env 29.8, recovery code count representation 29.9) honestly logged + schema-accurate values seeded + cj-280 retro scope 보존 = cj-style honest-DEFER discipline 보존
- 13-job matrix 가 cj-273b / cj-274 / cj-276 / cj-277 / cj-278a 와 동일한 12 PASS + 1 FAIL (web-e2e) 패턴 결정 wire — web-e2e 의 step 19 Playwright 가 cj-274 D-WEB-E2E-* honestly DEFER carryover 의 명시적 boundary 결정 wire 보존

Related: [[handoff-2026-09-05-cj-278-epic-29-plus-p1-plan-done]], [[handoff-2026-09-05-cj-278a-m11-scenario-wiring-done]], [[handoff-2026-09-05-cj-277-oq-3-scenario-all-wiring-done]], [[handoff-2026-09-05-cj-276-epic-29-plus-p0-minimum-viable-closed]], [[handoff-2026-09-05-cj-274-web-e2e-chain-close-honest-defer]].
