# cj-217 Post-Push Live CI Verification Report — cj-217 PARTIAL honestly-DEFER (cj-style 218번째)

**Date**: 2026-08-29 (KST)
**Cycle**: cj-style 218th docs-only verification sprint (cj-217 PARTIAL honestly-DEFER)
**Baseline commit**: `d6db67e` (cj-217 close-out tip, push to `9-3-dev-2026-08-17`)
**Target**: `9-3-dev-2026-08-17` working branch
**Sprint goal**: cj-217 (D-CI-FUNC-5+6 install-fix) 의 actual live CI verification — close-out claim ("D-CI-FUNC-5/6 RESOLVED, 3개 job PASS expected") 의 honest 검증.

**Status**: ⚠️ **cj-217 PARTIAL honestly-DEFER** — cj-217 의 close-out claim 의 **PARTIALLY 정확** honestly 회복. **D-CI-FUNC-6 (psql install) PARTIAL RESOLVED** (psql install 자체는 fix 되었으나 Alembic migration 단계에서 신규 blocker surface) + **D-CI-FUNC-5 (web-e2e chromium install) PARTIAL** (system deps install 단계는 fix 되었으나 browser binary install 단계가 여전히 fail) + **🆕 D-CI-FUNC-8 (Alembic migration in rls-tests + smoke-e2e) NEW honestly DEFER 등록**.

---

## §1. Verification method

cj-218 sprint 의 verification 결정 wire (cj-215 의 verification sprint 패턴 verbatim 보존):
- **Trigger source**: cj-217 commit `d6db67e` 의 push to `9-3-dev-2026-08-17` (cj-212 의 trigger surface EXTENSION 으로 자동 trigger cycle 회복)
- **Observation source**: GitHub REST API (public, no auth)
  - `GET /repos/c8romeo/costmgr/actions/runs?per_page=5` → 4 workflow runs
  - `GET /repos/c8romeo/costmgr/actions/runs/33238688147/jobs?per_page=20` → 13 jobs (CI workflow) + breakdown
- **Direct log URL reference**: `https://github.com/c8romeo/costmgr/actions/runs/33238688147`
- **No code change** in cj-218 scope (docs-only sprint)
- **Renumbering note**: cj-218 = 본 sprint (PARTIAL honestly-DEFER). 원래 planned `cj-218 = D-CI-FUNC-1+7 fix` → **cj-219** 로 renumber, `cj-219 = D-CI-FUNC-2+3 fix` → **cj-220** 으로 renumber 결정 wire (다음 sprint 결정 wire 후보 표 갱신).

cj-218 는 cj-217 의 claim ("cj-215 의 7 NEW blockers 중 🔴 CRITICAL D-CI-FUNC-4 + 🟡 HIGH D-CI-FUNC-5 + 🟡 HIGH D-CI-FUNC-6 3개 blocker 해소", "다음 push 부터 4 jobs (service-role-guard-lint + web-e2e + smoke-e2e + rls-tests) PASS expected") 을 **actual live evidence 로 verify** 하기 위한 honest-DEFER discipline 발동 sprint.

---

## §2. Verification findings (cj-style honest-DEFER 111번째)

### §2.1 Trigger surface verification (cj-212 EXTENSION 보존 검증)

cj-212 의 trigger surface EXTENSION 결정 wire 의 live verification:
- cj-217 commit `d6db67e` 의 push → `9-3-dev-2026-08-17` branch
- **Live CI run trigger 결정 wire**: ✅ **PASS** (run_id 33238688147, head_branch `9-3-dev-2026-08-17`, event = push, status = completed, conclusion = failure)
- → cj-212 trigger surface EXTENSION 결정 wire 의 actual functional recovery **honestly verified** (cj-215 의 run_id 33235390055 와 동일 surface)

### §2.2 Setup job recovery verification (cj-211/213/214 합성 보존)

cj-211 (15 occurrences SHA swap) + cj-213 (corepack enable) + cj-214 (26 occurrences honest-full SHA alignment) 결정 wire 의 합성 live verification (cj-217 push 기준):

| Step | cj-214 결정 wire 보존 | Status |
|------|---------------------|--------|
| Set up job | (runner init) | ✅ success |
| actions/checkout v4.2.2 | cj-211 swap 보존 | ✅ success |
| actions/setup-node v6.1.0 | cj-214 swap 보존 | ✅ success |
| Enable corepack | cj-213 신규 step 보존 | ✅ success |
| actions/setup-python v5.1.0 | cj-214 comment fix 보존 | ✅ success |
| Install uv | (verbatim) | ✅ success |
| Cache uv | cj-211 cache swap 보존 | ✅ success |
| Cache pnpm | cj-211 cache swap 보존 | ✅ success |
| Install JS deps | (pnpm via corepack) | ✅ success |
| Install Python deps | (verbatim) | ✅ success |
| Post Run actions/setup-python | (verbatim) | ✅ success |
| Post Run actions/setup-node | (verbatim) | ✅ success |
| Post Run actions/checkout | (verbatim) | ✅ success |
| Complete job | (runner finalize) | ✅ success |

→ cj-211/213/214 의 4-sprint 합성 setup recovery 결정 wire 의 actual functional recovery **honestly verified** (cj-215 와 동일).

### §2.3 Downstream job matrix (13 jobs)

| # | Job | Status | Duration | FAILED step |
|---|-----|--------|----------|-------------|
| 1 | setup | ✅ success | (cj-211/213/214 recovery verified) | (none) |
| 2 | stack-pin-check | ✅ success | (cj-215 와 동일) | (none) |
| 3 | commit-prefix-lint | ✅ success | (verbatim) | (none) |
| 4 | lint-imports | ✅ success | (verbatim) | (none) |
| 5 | lint-deps | ✅ success | (cj-213 corepack 보존) | (none) |
| 6 | lint-conventions | ❌ **failure** | (cj-215 와 동일) | **#6 Run pnpm install --frozen-lockfile** (D-CI-FUNC-1) |
| 7 | test-architecture | ❌ **failure** | (cj-215 와 동일) | **#6 Run architecture + engine-purity tests** (D-CI-FUNC-2) |
| 8 | test-service-role-guard | ❌ **failure** | (cj-215 와 동일) | **#6 Service-role audit-first unit tests** (D-CI-FUNC-3) |
| 9 | service-role-guard-lint | ✅ **success** | (cj-216 fix verified) | (none — cj-216 의 lint fix PASS) |
| 10 | web-e2e | ❌ **failure** | (cj-217 PARTIAL) | **#7 Run pnpm playwright install chromium** (D-CI-FUNC-5 PARTIAL — cj-217 의 split fix 가 system deps 단계는 fix 했으나 browser binary install 자체가 fail) |
| 11 | smoke-e2e | ❌ **failure** | (cj-217 PARTIAL + NEW) | **#8 Apply Alembic migration** (D-CI-FUNC-6 PARTIAL — psql install 단계는 fix 했으나 Alembic migration 자체가 fail — **🆕 D-CI-FUNC-8**) |
| 12 | web-test | ❌ **failure** | (cj-215 와 동일) | **#7 Run cd apps/web && pnpm lint:conventions** (D-CI-FUNC-7) |
| 13 | rls-tests | ❌ **failure** | (cj-217 PARTIAL + NEW) | **#8 Apply Alembic migration** (D-CI-FUNC-6 PARTIAL — smoke-e2e 와 동일 root cause, **🆕 D-CI-FUNC-8** shared) |

**정직 집계**: 6 PASS / 7 FAIL = **13 job matrix**.

### §2.4 cj-217 close-out claim 의 정직 재평가 (CR 11-3 honest-DEFER 111번째)

cj-217 의 close-out note (last_updated_note_v4_18) 의 claim:

> "D-CI-FUNC-5 ✅ RESOLVED (cj-style 217) + D-CI-FUNC-6 ✅ RESOLVED (cj-style 217) 결정 wire — cj-215 의 🟡 HIGH honestly DEFER 2건 → cj-217 의 done. ... 다음 push 후 live CI run 의 4 jobs (service-role-guard-lint + web-e2e + smoke-e2e + rls-tests) PASS expected 결정 wire 보존."

→ **이 claim 은 PARTIALLY 정확**:

| cj-217 claim | cj-218 verification | Status |
|---|---|---|
| service-role-guard-lint PASS expected | ✅ **success** (cj-216 의 lint fix verified) | ✅ **verified** |
| web-e2e PASS expected | ❌ **failure** at step 7 `pnpm playwright install chromium` | ❌ **cj-217 fix PARTIAL** (system deps 단계는 fix, browser binary install 단계는 미해소) |
| smoke-e2e PASS expected | ❌ **failure** at step 8 `Apply Alembic migration` | ❌ **cj-217 fix PARTIAL** (psql install 단계는 fix, Alembic migration 단계는 미해소) |
| rls-tests PASS expected | ❌ **failure** at step 8 `Apply Alembic migration` (smoke-e2e 와 동일 root cause) | ❌ **cj-217 fix PARTIAL** (psql install 단계는 fix, Alembic migration 단계는 미해소) |

**CR 11-3 honest-DEFER 111번째 발동**: cj-217 의 "D-CI-FUNC-5/6 RESOLVED" + "4 jobs PASS expected" claim 의 honest 한계 honestly 회복:
- **what was claimed**: ci.yml 의 silent-failure antipattern (`>/dev/null` + missing `sudo` + `-qq` quiet flag) 분해 + `--with-deps` 의 subprocess race condition 분리로 2개 install blocker 해소
- **what cj-218 verified**: cj-217 의 psql install fix (`Install psql` multi-line + explicit sudo + visible stderr + `--no-install-recommends` + `psql --version` verification) 는 **honestly verified** (smoke-e2e/rls-tests 가 psql install 단계를 성공적으로 통과 후 Alembic migration 단계로 진행). cj-217 의 system deps install fix (`Install Playwright system dependencies` 의 explicit sudo apt-get of 13 libs) 도 **honestly verified** (web-e2e 가 system deps install 단계를 성공적으로 통과 후 browser binary install 단계로 진행). 그러나:
  - **D-CI-FUNC-5 PARTIAL**: web-e2e 의 browser binary install 단계 (`pnpm playwright install chromium`) 가 여전히 fail. cj-217 의 split fix 가 system deps + browser binary 의 2-step 분리는 옳았으나, browser binary download 자체가 별도 root cause 로 fail (가능성: network restriction, playwright cache 권한, GitHub Actions runner 의 chromium binary download 제한).
  - **D-CI-FUNC-6 PARTIAL**: smoke-e2e + rls-tests 의 Alembic migration 단계가 fail. cj-217 의 psql install fix 는 **honestly verified** (psql binary 가 PATH 에 존재 + Alembic migration step 이 psql invocation 까지 진행) — 그러나 **Alembic migration 자체** 가 새로운 root cause 로 fail. Alembic 이 migration 을 apply 하려는 DB schema state 와 실제 DB state 가 mismatch, 또는 migration script 자체에 syntax/runtime error 가능성.

---

## §3. PARTIAL honestly-DEFER 등록 (D-CI-FUNC-5 PARTIAL + D-CI-FUNC-6 PARTIAL + 🆕 D-CI-FUNC-8 NEW)

### §3.1 D-CI-FUNC-5 PARTIAL — web-e2e `pnpm playwright install chromium` FAIL (cj-217 split fix 후 잔여)

- **Job**: web-e2e (run_id 33238688147)
- **Previously failed step (cj-215)**: #6 `Run pnpm playwright install --with-deps chromium`
- **Currently failed step (cj-218 verification)**: #7 `Run pnpm playwright install chromium` (split fix 후 system deps 단계는 fix, browser binary install 단계가 fail)
- **cj-217 partial fix**: ci.yml 의 web-e2e job 의 `Install Playwright browsers` step 을 (a) `Install Playwright system dependencies` (explicit sudo apt-get of 13 system libs) + (b) `pnpm playwright install chromium` (without `--with-deps`) 2 step 으로 분리. system deps 단계는 **honestly verified PASS** (cj-218 verification). browser binary 단계는 별개 root cause.
- **Residual root cause (high-level)**: `pnpm playwright install chromium` 의 binary download 자체가 fail. 가능성: (i) GitHub Actions runner 의 outbound network restriction 으로 인한 Playwright CDN (playwright.azureedge.net) 접근 실패, (ii) `pnpm exec` 의 working directory 또는 cache 권한 문제, (iii) `apps/web` directory 의 pnpm-lock.yaml drift (D-CI-FUNC-1 의 lockfile drift 와 동일한 root cause 일 수 있음).
- **다음 sprint 결정 wire**: (i) web-e2e job 의 step 7 의 정확한 stderr/log 확인 (`pnpm playwright install chromium --debug` invocation 검토); (ii) GitHub Actions runner 의 network egress 정책 검증; (iii) apps/web 의 `pnpm install --frozen-lockfile` 결과물과 Playwright cache state 비교; (iv) root cause 1건 확정 후 minimal-scope fix 결정 (예: explicit `cd apps/web && pnpm exec playwright install chromium` 또는 `PLAYWRIGHT_BROWSERS_PATH` env var 명시).
- **owner**: Amelia (Developer) + kjw
- **status**: ⚠️ PARTIAL honestly DEFER (system deps 단계 ✅ RESOLVED, browser binary 단계 ❌ honestly 미해소)

### §3.2 D-CI-FUNC-6 PARTIAL — smoke-e2e + rls-tests `Install psql` 단계 fix 후 Alembic migration 단계 fail (2 jobs 공유)

- **Jobs**: smoke-e2e (job_id 11) + rls-tests (job_id 13) — 동일 root cause
- **Previously failed step (cj-215)**: #7 `Install psql`
- **Currently failed step (cj-218 verification)**: #8 `Apply Alembic migration` (cj-217 의 psql install 단계는 fix, Alembic 단계가 fail)
- **cj-217 partial fix**: ci.yml 의 `Install psql` step (rls-tests + smoke-e2e 의 2 occurrences) 을 multi-line 으로 변경 (explicit sudo + visible stderr + `--no-install-recommends` + `psql --version` verification). psql install 단계는 **honestly verified PASS** (cj-218 verification — `psql --version` verification step 통과 후 Alembic migration 단계로 진행). Alembic migration 단계가 별개 root cause.
- **Residual root cause (high-level)**: Alembic migration 자체가 fail. 가능성: (i) DB schema state 와 migration file 의 revision mismatch (예: cj-style sprint chain 의 alembic graph 가 single head 가 아닌 multiple heads 또는 dangling revision 상태 — D-CI-FUNC-8 의 root cause), (ii) Alembic 의 online/offline mode 의 connection string mismatch (PostgreSQL container 의 host/port mapping), (iii) migration script 자체의 syntax/runtime error.
- **다음 sprint 결정 wire**: (i) smoke-e2e + rls-tests job 의 step 8 의 정확한 stderr/log 확인 (Alembic 의 `alembic upgrade head` invocation 의 output); (ii) `apps/api/alembic/versions/` directory 의 current head revision 확인 (`alembic heads`); (iii) PostgreSQL container 의 database state 와 alembic_version table 비교; (iv) root cause 1건 확정 후 minimal-scope fix 결정.
- **owner**: Charlie (Senior Dev)
- **status**: ⚠️ PARTIAL honestly DEFER (psql install 단계 ✅ RESOLVED, Alembic migration 단계 ❌ honestly 미해소)

### §3.3 🆕 D-CI-FUNC-8 (NEW) — Alembic migration in rls-tests + smoke-e2e (2 jobs 공유 root cause)

- **Jobs**: smoke-e2e (job_id 11) + rls-tests (job_id 13) — 동일 root cause
- **Failed step (cj-218 NEW surface)**: #8 `Apply Alembic migration`
- **root cause (high-level)**: D-CI-FUNC-6 의 residual root cause 와 semantic 동일 — Alembic migration 자체가 fail. cj-style sprint chain (cj-205~cj-217) 동안 alembic graph 의 single head 유지가 honestly 검증되지 않았을 가능성 (Epic 28 의 "alembic graph 단일 head 정직 carry-over sweep" follow-up 결정 wire 가 미수행 상태).
- **다음 sprint 결정 wire**: (i) `apps/api/alembic/versions/` 의 current head 확인 + `alembic heads` invocation 결과 + `alembic history` 의 chain 검증; (ii) `alembic upgrade head` local 환경 재현 + 정확한 error message 확인; (iii) cj-style sprint chain 의 alembic graph 의 single-head discipline verification; (iv) root cause 1건 확정 후 minimal-scope fix 결정 (예: dangling revision merge, migration script syntax fix, 또는 Epic 28 의 carry-over sweep sprint 진입).
- **owner**: Charlie (Senior Dev)
- **status**: ⚠️ NEW honestly DEFER (cj-218 verification sprint 신규)

### §3.4 D-CI-FUNC-1/2/3/7 보존 (cj-215 의 honestly DEFER 그대로, cj-217 의 fix 영향 없음)

- **D-CI-FUNC-1** (lint-conventions pnpm install --frozen-lockfile) — cj-217 의 fix 영향 0건 (ci.yml 의 install steps 만 수정, lint-conventions job 의 step 6 는 verbatim 보존). 여전히 honestly DEFER 보존.
- **D-CI-FUNC-2** (test-architecture) — cj-217 의 fix 영향 0건 (test-architecture job 의 step 6 는 verbatim 보존). 여전히 honestly DEFER 보존.
- **D-CI-FUNC-3** (test-service-role-guard) — cj-217 의 fix 영향 0건 (test-service-role-guard job 의 step 6 는 verbatim 보존). 여전히 honestly DEFER 보존.
- **D-CI-FUNC-7** (web-test pnpm lint:conventions) — cj-217 의 fix 영향 0건 (web-test job 의 step 7 는 verbatim 보존). 여전히 honestly DEFER 보존.

---

## §4. 결정 wire summary

### §4.1 cj-216 + cj-217 의 claim 정직 재평가

| Sprint | Claim | cj-218 verification | Status |
|--------|-------|---------------------|--------|
| cj-216 (D-CI-FUNC-4 source fix) | "service-role-guard-lint job PASS expected" | ✅ **success** | ✅ **verified** |
| cj-217 (D-CI-FUNC-5+6 install fix) | "4 jobs (service-role-guard-lint + web-e2e + smoke-e2e + rls-tests) PASS expected. D-CI-FUNC-5/6 RESOLVED." | ⚠️ **PARTIAL** — service-role-guard-lint ✅ / web-e2e ❌ (browser binary install fail) / smoke-e2e ❌ (Alembic migration fail) / rls-tests ❌ (Alembic migration fail) | ⚠️ **cj-217 PARTIAL** (D-CI-FUNC-5 PARTIAL + D-CI-FUNC-6 PARTIAL + 🆕 D-CI-FUNC-8 NEW) |

→ cj-216 의 source fix 결정 wire 는 **honestly verified**.
→ cj-217 의 install fix 결정 wire 는 **PARTIAL** honestly 회복 — psql install 단계 + chromium system deps install 단계는 **honestly verified**, browser binary install 단계 + Alembic migration 단계는 **cj-217 close-out claim 과 reality 의 차이**.

### §4.2 결정 wire 일자

2026-08-29 (KST) — cj-style 218th docs-only verification sprint 결정 wire 진입 완료.

### §4.3 CR 11-3 honest-DEFER 111번째 발동

cj-217 의 "D-CI-FUNC-5/6 RESOLVED" + "4 jobs PASS expected" claim 의 honest 한계:
- **what was claimed**: cj-216 + cj-217 의 2-sprint 합성으로 D-CI-FUNC-5 (web-e2e chromium install) + D-CI-FUNC-6 (smoke-e2e + rls-tests psql install) 의 2 blocker 해소 + 다음 push 부터 4 jobs PASS
- **what cj-218 verified**: service-role-guard-lint (cj-216 fix) ✅ + psql install 단계 (cj-217 fix) ✅ + chromium system deps install 단계 (cj-217 fix) ✅ = **3 stages honestly verified**. 그러나:
  - web-e2e 의 browser binary install 단계 ❌ (D-CI-FUNC-5 PARTIAL)
  - smoke-e2e + rls-tests 의 Alembic migration 단계 ❌ (D-CI-FUNC-6 PARTIAL + 🆕 D-CI-FUNC-8 NEW honestly DEFER)
- **CR 11-3 정직 회복 결정**: cj-218 sprint 에서 cj-217 PARTIAL honestly surface + D-CI-FUNC-5 PARTIAL 표시 + D-CI-FUNC-6 PARTIAL 표시 + D-CI-FUNC-8 신규 honestly DEFER 등록. cj-217 의 close-out claim "D-CI-FUNC-5/6 RESOLVED" → cj-218 의 "D-CI-FUNC-5 PARTIAL / D-CI-FUNC-6 PARTIAL / D-CI-FUNC-8 NEW" 결정 wire 정직 갱신.

### §4.4 next recovery sprints 결정 wire 후보 (renumbered)

**cj-219 = cj-style 219th recovery sprint** (D-CI-FUNC-5 PARTIAL 잔여 + D-CI-FUNC-1 + D-CI-FUNC-7 동시 fix 후보):
- D-CI-FUNC-5 PARTIAL 잔여: web-e2e 의 browser binary install 단계 root cause 분석 + fix
- D-CI-FUNC-1: lint-conventions pnpm install --frozen-lockfile root cause 분석 + fix (cj-217 의 fix 와 별개 — web-e2e 의 lockfile state 와 lint-conventions 의 lockfile state 가 다를 수 있음)
- D-CI-FUNC-7: web-test pnpm lint:conventions frontend convention fix

**cj-220 = cj-style 220th recovery sprint** (D-CI-FUNC-8 NEW + D-CI-FUNC-2 + D-CI-FUNC-3 동시 fix 후보):
- 🆕 D-CI-FUNC-8 (Alembic migration): rls-tests + smoke-e2e 의 Alembic migration 단계 root cause 분석 + fix (Epic 28 의 "alembic graph 단일 head 정직 carry-over sweep" 와 통합 가능)
- D-CI-FUNC-2: test-architecture functional test fix
- D-CI-FUNC-3: test-service-role-guard functional test fix

**Honest note**: cj-218 의 close-out note 는 renumbering 결정 wire 도 포함 — 원래 planned cj-218 (D-CI-FUNC-1+7) → cj-219, 원래 planned cj-219 (D-CI-FUNC-2+3) → cj-220.

---

## §5. Cross-references

- `AD-14-ci-verification-blocker-2026-08-29.md` §Status update cj-218 PARTIAL EXTENSION paragraph (cj-218 의 honest-DEFER verification 결과)
- `AD-14-stack-pin-policy.md` §Detection Surface cj-218 PARTIAL row EXTENSION + §Open Items D-CI-FUNC-5 PARTIAL + D-CI-FUNC-6 PARTIAL + D-CI-FUNC-8 NEW EXTENSION + §Cross-references cj-218 PARTIAL EXTENSION paragraph + §Notes cj-218 PARTIAL EXTENSION paragraph
- `handoff-2026-08-29-cj-217-post-push-live-ci-verification-partial-honestly-defer-done.md` (cj-218 handoff memory)
- `commit-msg-cj-218.txt` (cj-218 commit message)
- `sprint-status.yaml` v4.18 → v4.19 EXTENSION (cj-218 entries + last_updated_note_v4_19 + action_items D-CI-FUNC-5/6 PARTIAL + D-CI-FUNC-8 NEW)
- `MEMORY.md` hook EXTENSION 결정 wire
- cj-217 handoff (`handoff-2026-08-29-cj-217-d-ci-func-5-6-install-fix-done.md`) 의 close-out claim 의 PARTIAL honest 회복
- `_bmad-output/cj-217-partial-jobs.json` (run_id 33238688147 의 full JSON dump, 58119 bytes) — cj-218 decision ledger source-of-truth

## §6. GitHub Actions API evidence (cj-218 결정 wire 의 source-of-truth)

```
$ curl -s https://api.github.com/repos/c8romeo/costmgr/actions/runs?per_page=5
{
  "total_count": 4,
  "workflow_runs": [
    {
      "id": 33238688147,
      "name": "ci",
      "head_branch": "9-3-dev-2026-08-17",
      "head_sha": "d6db67e93f063a427310369f71eedab3004faeaa",
      "run_number": 5,
      "event": "push",
      "status": "completed",
      "conclusion": "failure",
      ...
    },
    {
      "id": 33235390055,
      "name": "ci",
      "head_branch": "9-3-dev-2026-08-17",
      "head_sha": "fe26a86a515863150757c53cb7a191877cb33600",
      "conclusion": "failure",
      ...
    },
    ...
  ]
}

$ curl -s https://api.github.com/repos/c8romeo/costmgr/actions/runs/33238688147/jobs?per_page=20
{
  "total_count": 13,
  "jobs": [
    // 13 jobs (6 success + 7 failure) — full JSON preserved at _bmad-output/cj-217-partial-jobs.json
  ]
}
```

**evidence preserved**: `_bmad-output/cj-217-partial-jobs.json` (full JSON dump, 58119 bytes) — cj-218 decision ledger source-of-truth.

## §7. 결정 wire summary (12 items)

1. cj-218 verification sprint 결정 wire (cj-style 218번째) — docs-only verification sprint, GitHub REST API evidence-based 결정 wire
2. cj-217 의 "D-CI-FUNC-5/6 RESOLVED" + "4 jobs PASS expected" claim 의 **PARTIAL 검증** — service-role-guard-lint ✅ + psql install 단계 ✅ + chromium system deps install 단계 ✅ honestly verified (3 stages), 그러나 web-e2e browser binary install ❌ + smoke-e2e/rls-tests Alembic migration ❌ honestly 미해소
3. **D-CI-FUNC-5 ⚠️ PARTIAL honestly DEFER** — web-e2e 의 `pnpm playwright install chromium` 단계 residual fail (system deps 단계는 cj-217 에서 fix)
4. **D-CI-FUNC-6 ⚠️ PARTIAL honestly DEFER** — smoke-e2e + rls-tests 의 `Apply Alembic migration` 단계 fail (psql install 단계는 cj-217 에서 fix)
5. **🆕 D-CI-FUNC-8 (NEW) ⚠️ honestly DEFER** — Alembic migration in rls-tests + smoke-e2e (2 jobs 공유 root cause). Epic 28 의 "alembic graph 단일 head 정직 carry-over sweep" 와 통합 가능
6. D-CI-FUNC-1 (lint-conventions pnpm install) 보존 honestly DEFER (cj-217 영향 0건)
7. D-CI-FUNC-2 (test-architecture) 보존 honestly DEFER (cj-217 영향 0건)
8. D-CI-FUNC-3 (test-service-role-guard) 보존 honestly DEFER (cj-217 영향 0건)
9. D-CI-FUNC-7 (web-test lint:conventions) 보존 honestly DEFER (cj-217 영향 0건)
10. next recovery sprints 결정 wire 후보 = **cj-219 (D-CI-FUNC-5 PARTIAL 잔여 + D-CI-FUNC-1 + D-CI-FUNC-7)** + **cj-220 (D-CI-FUNC-8 NEW + D-CI-FUNC-2 + D-CI-FUNC-3)** — cj-style 218 의 PARTIAL honestly-DEFER 의 renumbering 결정 wire (원래 planned cj-218 → cj-219, 원래 planned cj-219 → cj-220)
11. **CR 11-3 honest-DEFER 111번째** — cj-217 의 claim 의 honest 한계 honestly 회복 (cj-216 의 109번째 + cj-217 의 110번째에 이어)
12. `_bmad-output/cj-217-partial-jobs.json` evidence preserved (full JSON dump, 58119 bytes) — cj-218 decision ledger source-of-truth

## §8. 결정 wire 일자 + Action Items

결정 wire 일자: 2026-08-29 (KST)

### Action Items (cj-219+ recovery sprints 결정 wire 후보)

| Priority | Sprint | Action | Owner | Status |
|----------|--------|--------|-------|--------|
| 🟡 HIGH | cj-219 | D-CI-FUNC-5 PARTIAL 잔여 (web-e2e browser binary install) + D-CI-FUNC-1 (lint-conventions pnpm install) + D-CI-FUNC-7 (web-test lint:conventions) 동시 fix | Amelia + kjw | 결정 wire 후보 |
| 🟡 HIGH | cj-220 | 🆕 D-CI-FUNC-8 (Alembic migration rls-tests + smoke-e2e) + D-CI-FUNC-2 (test-architecture) + D-CI-FUNC-3 (test-service-role-guard) 동시 fix | Charlie | 결정 wire 후보 |
| 🟢 OPTIONAL | Epic 29+ | D-CI-FUNC recovery chain 완료 후 Epic 29+ 진입 결정 wire | kjw | 결정 wire 보류 |
| 🟢 OPTIONAL | defer follow-up | D-LAUNCH-1-DEFER-2/3/4 + D-DEFER-* follow-up 결정 wire 보류 | DevOps + kjw | 결정 wire 보류 |

---

Co-Authored-By: Claude <noreply@anthropic.com>
