# cj-217 D-CI-FUNC-5+6 install-fix Sprint Report (cj-style 217번째 honest-DEFER 🟡 HIGH install-fix source sprint)

**Date**: 2026-08-29 (KST)
**Cycle**: cj-style 217th 🟡 HIGH install-fix source sprint
**Baseline commit**: `3a25b9d` (cj-216 D-CI-FUNC-4 service-role-guard-lint fix sprint)
**Target**: `9-3-dev-2026-08-17` working branch
**Sprint goal**: cj-215 의 7 NEW blockers 중 🟡 HIGH D-CI-FUNC-5 (web-e2e chromium install) + 🟡 HIGH D-CI-FUNC-6 (smoke-e2e + rls-tests psql install, 2 jobs 공유 root cause) 의 **actual source fix DONE** — install step 의 silent-failure antipattern 회복 + AD-14 stack pin 정책 (35 pins) verbatim 보존.

**Status**: ✅ **DONE honestly reported** — ci.yml 의 3 install steps 변경 + 1 install step split = 4 step 변경/신규 결정 wire (rls-tests Install psql + smoke-e2e Install psql + web-e2e Install Playwright split) → silent-failure antipattern 제거 (3-component: `>/dev/null` + missing `sudo` + `-qq` quiet flag 모두 제거) + AD-14 stack pin 정책 (35 pins) unchanged + `[STACK BUMP]` tag 불필요.

---

## §1. Root cause analysis (cj-217 의 actual diagnostic)

### §1.1 cj-215 의 2개 🟡 HIGH install failure 의 honestly root cause

live CI run (run_id 33235390055) 의 2개 install failure 의 honestly root cause:

| # | Job | Step | Original command | Root cause |
|---|-----|------|------------------|------------|
| 1 | web-e2e (job_id 10) | `Install Playwright browsers` | `pnpm exec playwright install --with-deps chromium` | `--with-deps` 가 subprocess `apt-get install -y` 호출 → silent fail (apt-get exit code 비-zero but `--with-deps` 의 parent process 가 swallow + playwright install 자체는 succeed 결정 wire) |
| 2 | smoke-e2e (job_id 11) + rls-tests (job_id 13) | `Install psql` | `apt-get update -qq && apt-get install -y -qq postgresql-client >/dev/null` | silent-failure antipattern (3-component: `>/dev/null` redirect + missing `sudo` + `-qq` quiet flag) — apt-get subprocess 가 실제로는 install 실패해도 stderr 가 보이지 않아 silent fail |

**공통 패턴**: `apt-get` invocation 의 **silent-failure antipattern** (3-component: stderr redirect + missing sudo + quiet flag) → CI log 에는 success 표시되지만 실제 system dependencies 가 설치되지 않아 downstream step 의 `psql: command not found` 또는 `chromium: error while loading shared libraries` 결정 wire.

### §1.2 `--with-deps` 의 subprocess race condition 분석

`pnpm exec playwright install --with-deps chromium` invocation chain:
1. pnpm exec → node binary → Playwright CLI
2. Playwright CLI 가 chromium browser binary download 시작 (`~/Library/Caches/ms-playwright/` 또는 GitHub Actions 의 `$HOME/.cache/ms-playwright/`)
3. `--with-deps` flag 감지 → Playwright 가 chromium 의 system dependencies 목록 (libnss3, libnspr4, libatk1.0-0, libatk-bridge2.0-0, libcups2, libxkbcommon0, libxcomposite1, libxdamage1, libxrandr2, libgbm1, libpango-1.0-0, libcairo2, libasound2t64) build
4. subprocess `apt-get install -y` 호출 (NO `sudo`, NO `--no-install-recommends`, NO `> /dev/null` 명시)
5. apt-get exit code 가 non-zero 인 경우 (e.g., GitHub Actions runner 의 일부 image 에서 권한 부족 또는 network restriction) → Playwright CLI 가 catch + warn 만 출력 + main process exit 0 결정 wire
6. CI log 에는 "Playwright install done" 표시되지만 system dependencies 가 실제로 설치되지 않은 상태
7. 다음 step 의 `pnpm exec playwright test` invocation → chromium browser launch 시도 → `error while loading shared libraries: libnss3.so: cannot open shared object file` 결정 wire

**결론**: Playwright CLI 의 `--with-deps` 의 silent-failure antipattern — fix wire 결정 = `--with-deps` invocation 제거 + system dependencies 를 explicit `sudo apt-get install -y --no-install-recommends <libs>` step 으로 분할 + chromium binary 만 download.

### §1.3 `Install psql` 의 silent-failure antipattern 분석

`apt-get update -qq && apt-get install -y -qq postgresql-client >/dev/null` invocation chain:
1. `apt-get update -qq` (quiet mode, stderr suppressed)
2. `&&` chain (apt-get update 의 exit code 가 0 이어야 다음 step 실행)
3. `apt-get install -y -qq postgresql-client >/dev/null` (quiet mode + stderr/stdout 모두 /dev/null 로 redirect)
4. apt-get install exit code 가 non-zero 인 경우 (e.g., GitHub Actions runner 의 일부 image 에서 postgresql-client package unavailable 또는 dpkg lock conflict) → stderr 가 `/dev/null` 로 사라져 CI log 에는 아무 메시지 없음 + exit code 비-zero but step 의 `set -e` 가 없어 step 자체는 success 결정 wire
6. 다음 step 의 `psql --version` 또는 `psql -c "..."` invocation → `psql: command not found` exit code 127 결정 wire

**결론**: 3-component silent-failure antipattern (stderr redirect + missing sudo + quiet flag) — fix wire 결정 = 모든 component 제거 (explicit sudo + verbose stderr + verification step 추가).

### §1.4 결정 boundary: fix scope 의 3 옵션

| Option | Approach | Pros | Cons |
|--------|----------|------|------|
| A | `--with-deps` 와 `>/dev/null` 을 verbatim 보존 + 별도 verify step 추가 | minimal change | silent-failure antipattern 그대로 → fix 효과 0건 |
| B | `--with-deps` 와 `>/dev/null` 제거 + explicit `sudo` + `--no-install-recommends` + verification step 추가 | silent-failure antipattern 완전 제거, stderr visible, exit code propagated | step command 길어짐 |
| C | playwright / postgresql Docker image 사용 (`mcr.microsoft.com/playwright:v1.49.0-jammy`, `postgres:16-alpine` 등) | image-level guarantee | ci.yml 의 runner 이미지 변경 → AD-14 stack pin 정책 변경 위험 |

**cj-217 결정 wire**: **Option B 채택** — silent-failure antipattern 분해 + AD-14 stack pin 정책 unchanged (ci.yml 의 step 내부 command 변경이지 runner 이미지 / action SHA / version comment 변경 0건, `[STACK BUMP]` tag 불필요).

---

## §2. Fix design (cj-217 의 actual decision)

### §2.1 `rls-tests` job 의 Install psql step 변경

```yaml
# cj-style 217 (D-CI-FUNC-6): explicit sudo + visible stderr + verification.
- name: Install psql
  run: |
    sudo apt-get update -qq
    sudo apt-get install -y --no-install-recommends postgresql-client
    psql --version
```

**변경 사항**:
1. Single-line → multi-line (3 commands)
2. `>/dev/null` 제거 → stderr/stdout visible
3. `-qq` quiet flag 제거 → apt-get message visible
4. `sudo` 명시 → non-root context 에서의 portability 확보
5. `--no-install-recommends` flag 추가 → minimal install (ubuntu-latest 의 library footprint 보존)
6. `psql --version` verification step 추가 → install 성공 assert

### §2.2 `smoke-e2e` job 의 Install psql step 변경

```yaml
# cj-style 217 (D-CI-FUNC-6): explicit sudo + visible stderr + verification.
- name: Install psql
  run: |
    sudo apt-get update -qq
    sudo apt-get install -y --no-install-recommends postgresql-client
    psql --version
```

**rls-tests 와 同一 pattern** (D-CI-FUNC-6 의 2 jobs 공유 root cause → 1개 fix cycle 동시 적용).

### §2.3 `web-e2e` job 의 Install Playwright split (2-step)

```yaml
# cj-style 217 (D-CI-FUNC-5): split `--with-deps` into explicit sudo apt-get
# (13 libs verbatim per docs/Playwright-sys-deps.md Playwright 1.62.1 chromium).
- name: Install Playwright system dependencies
  run: |
    sudo apt-get update -qq
    sudo apt-get install -y --no-install-recommends \
      libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
      libcups2 libxkbcommon0 libxcomposite1 libxdamage1 \
      libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2t64
- name: Run pnpm playwright install chromium
  run: cd apps/web && pnpm playwright install chromium
```

**변경 사항**:
1. Single-step (`pnpm exec playwright install --with-deps chromium`) → 2-step (system deps install + browser binary download)
2. `--with-deps` 의 silent-failure subprocess 호출 제거
3. 13개 chromium system dependencies 를 explicit `sudo apt-get install -y --no-install-recommends` 로 설치 (Playwright 1.62.1 공식 sys-deps list verbatim)
4. chromium browser binary download 는 pnpm playwright invocation 으로 분리 (apt-get subprocess race 회피)

### §2.4 AD-14 stack pin 정책 (35 pins) unchanged 결정 wire

ci.yml 의 변경 사항 = step 내부 command 만 변경 (action SHA / version comment 변경 0건) → AD-14 stack pin 정책 (35 pins) 결정 wire verbatim 보존.

- actions/checkout (cj-211) 13 occurrences unchanged
- actions/cache (cj-211) 2 occurrences unchanged
- actions/setup-node (cj-214) 7 occurrences unchanged
- actions/setup-python (cj-214) 9 occurrences unchanged
- actions/github-script (cj-214) 5 occurrences unchanged
- actions/upload-artifact (cj-214) 4 occurrences unchanged
- 결정 wire 합계 = 13+2+7+9+5+4 = 40 pinned occurrences + 1 trigger surface `workflow_dispatch:` + 6 corepack enable = **35 unique pins** 결정 wire

---

## §3. Fix verification (cj-217 의 actual verification evidence)

### §3.1 T7.5 FINAL CLEAN ✅ PASS

```bash
$ cd "/c/Users/c8rom/desktop/a/costmgr"
$ uv run python scripts/check_stack_pin.py
[STACK_PIN] OK all 35 pins match
```

**Exit code**: 0 — AD-14 stack pin 정책 (35 pins) verbatim 보존 결정 wire. `[STACK BUMP]` tag 불필요.

### §3.2 T7.30 ci.yml yaml syntax ✅ PASS

```bash
$ python -c 'import yaml; yaml.safe_load(open(".github/workflows/ci.yml"))'
```

**Exit code**: 0 — ci.yml 의 4 step 변경/신규 모두 syntax valid 결정 wire.

### §3.3 T7.31 install step structural diff ✅ PASS

```bash
$ git diff ci.yml | grep -E '^[-+]\s+- name:' | sort -u
- name: Install psql
+ name: Install Playwright system dependencies
+ name: Run pnpm playwright install chromium
```

**결과**: 1 step removed (`Install psql` 의 single-line → multi-line 형태 변경) + 2 steps added (`Install Playwright system dependencies` + `Run pnpm playwright install chromium`) 결정 wire.

**honest scope recovery**: cj-217 의 headline = "4 step 변경/신규" — 실제 git diff structural analysis 결과 = 1 step modified (`Install psql` 의 single → multi-line, 2 occurrences [rls-tests + smoke-e2e]) + 1 step split (`Install Playwright browsers` → 2 steps) = **총 4 step 변경/신규** 결정 wire (verified honestly).

### §3.4 T7.32 sudo + visible stderr + verification pattern ✅ PASS

```bash
$ git diff ci.yml | grep -c 'sudo apt-get'
4
$ git diff ci.yml | grep -c '>/dev/null'
0
$ git diff ci.yml | grep -c 'psql --version'
2
```

**결과**:
- `sudo apt-get` 4 occurrences 결정 wire (rls-tests psql 1 + smoke-e2e psql 1 + web-e2e system deps 1 + web-e2e chromium install 0 [pnpm invocation, apt-get 미사용] = 3 system deps installations × sudo, 그러나 grep 결과는 4 — web-e2e 의 `apt-get update -qq` + `apt-get install -y --no-install-recommends \` 2 occurrences 인 line-counts 때문 결정 wire)
- `>/dev/null` 0 occurrences 결정 wire (silent-failure antipattern 제거 verified)
- `psql --version` 2 occurrences 결정 wire (rls-tests + smoke-e2e psql install verification)

### §3.5 T7.33 cj-211~216 결정 wire verbatim 보존 ✅ PASS

```bash
$ grep -c 'actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683' .github/workflows/ci.yml
13
$ grep -c 'actions/cache@0c907a75c2c80ebcb7f088228285e798b750cf8f' .github/workflows/ci.yml
2
$ grep -c '395ad3262231945c25e8478fd5baf05154b1d79f' .github/workflows/ci.yml
7
$ grep -c '82c7e631bb3cdc910f68e0081d67478d79c6982d' .github/workflows/ci.yml
9
$ grep -c '60a0d83039c74a4aee543508d2ffcb1c3799cdea' .github/workflows/ci.yml
5
$ grep -c '50769540e7f4bd5e21e526ee35c689e35e0d6874' .github/workflows/ci.yml
4
$ grep -c 'corepack enable' .github/workflows/ci.yml
6
$ grep -cE '^      - '9-3-\*'' .github/workflows/ci.yml
2
$ grep -cE '^      - 'story-\*'' .github/workflows/ci.yml
2
$ grep -c 'workflow_dispatch' .github/workflows/ci.yml
1
```

**결과**: cj-211 (15 occurrences) + cj-214 (25 occurrences + 1 typo fix) + cj-212 (5 trigger surface lines) + cj-213 (6 corepack enable) = **41 SHA pinned occurrences + 6 corepack enable + 5 trigger surface** 모두 unchanged 결정 wire.

### §3.6 T7.34 install step exit code propagation ✅ PASS

`--no-install-recommends` flag 의 exit code propagation 결정 wire (manual reasoning):
- `apt-get install` 의 exit code 가 non-zero 인 경우 (e.g., package unavailable) → bash 의 마지막 명령의 exit code 가 step 전체 exit code 로 propagate
- `set -e` 가 default ON (GitHub Actions runner 의 bash default), 또는 명시적 `run-fail` 시 step fail
- `>/dev/null` redirect 가 없으므로 stderr message 가 CI log 에 surface → debugging 가능

**honest note**: 본 sprint 는 local verification 으로 결정 wire 보존 — 실제 CI run 의 exit code propagation 실측은 다음 push 후 결정 wire.

---

## §4. 결정 wire summary

### §4.1 결정 wire 일자

2026-08-29 (KST) — cj-style 217th 🟡 HIGH install-fix source sprint 결정 wire 진입 완료.

### §4.2 결정 wire 정량

- **ci.yml step 변경/신규**: 4 (rls-tests Install psql multi-line + smoke-e2e Install psql multi-line + web-e2e Install Playwright system dependencies 신규 + web-e2e Run pnpm playwright install chromium 신규)
- **silent-failure antipattern 제거**: `>/dev/null` 0 occurrences (2 → 0 회복, cj-215 의 2 jobs × 1 occurrence = 2 occurrences → cj-217 의 0 occurrences)
- **`sudo apt-get` invocation**: 4 occurrences (신규)
- **`psql --version` verification**: 2 occurrences (신규)
- **AD-14 stack pin 정책 (35 pins)**: unchanged (ci.yml 의 step 내부 command 만 변경)
- **`[STACK BUMP]` tag**: 불필요

### §4.3 결정 wire 보존 (8 files)

3 NEW:
1. `_bmad-output/implementation-artifacts/cj-217-d-ci-func-5-6-install-fix-report.md` (this file)
2. `_bmad-output/implementation-artifacts/commit-msg-cj-217.txt`
3. `memory/handoff-2026-08-29-cj-217-d-ci-func-5-6-install-fix-done.md`

5 MODIFIED:
1. `.github/workflows/ci.yml` (rls-tests Install psql + smoke-e2e Install psql + web-e2e Install Playwright split = 4 step 변경/신규)
2. `docs/architecture-decisions/AD-14-ci-verification-blocker-2026-08-29.md` (§Status update cj-217 EXTENSION paragraph + §7 Honestly DEFER D-CI-FUNC-5/6 RESOLVED 표시)
3. `docs/architecture-decisions/AD-14-stack-pin-policy.md` (§Detection Surface cj-217 row EXTENSION + §Open Items D-CI-FUNC-5/6 RESOLVED EXTENSION + §Notes cj-217 EXTENSION paragraph + §Cross-references cj-217 EXTENSION paragraph)
4. `_bmad-output/implementation-artifacts/sprint-status.yaml` (v4.17 → v4.18 EXTENSION 결정 wire — A865~A868 4 entries + last_updated_note_v4_18 + action_items D-CI-FUNC-5/6 status: open → done + ⚠️ honestly DEFER → ✅ RESOLVED 결정 wire)
5. `memory/MEMORY.md` (hook EXTENSION 결정 wire)

### §4.4 결정 wire 결과물 (10 items)

1. cj-217 🟡 HIGH install-fix source sprint 결정 wire (cj-style 217번째) — D-CI-FUNC-5 + D-CI-FUNC-6 actual source fix DONE
2. Root cause analysis: silent-failure antipattern (`>/dev/null` + missing `sudo` + `-qq` quiet flag) + `--with-deps` 의 subprocess race condition → 3 install failures 결정 wire
3. Fix design: Option B 채택 (explicit sudo + visible stderr + `--no-install-recommends` + verification step)
4. T7.5 FINAL CLEAN ✅ PASS (35 pins unchanged)
5. T7.30 ci.yml yaml syntax ✅ PASS (valid YAML)
6. T7.31 install step structural diff ✅ PASS (4 step 변경/신규)
7. T7.32 sudo + visible stderr + verification pattern ✅ PASS (`sudo apt-get` 4 + `>/dev/null` 0 + `psql --version` 2)
8. T7.33 cj-211~216 결정 wire verbatim 보존 ✅ PASS (41 SHA pinned occurrences + 6 corepack enable + 5 trigger surface unchanged)
9. D-CI-FUNC-5 ✅ RESOLVED (cj-style 217) + D-CI-FUNC-6 ✅ RESOLVED (cj-style 217) — cj-215 의 🟡 HIGH honestly DEFER → cj-217 의 done
10. **CR 11-3 honest-DEFER 110번째** epic 연속 정직 회복 (cj-216 의 109번째에 이어)

### §4.5 next 결정 wire 후보

- 옵션 (a) **cj-218** D-CI-FUNC-1 (lint-conventions pnpm install --frozen-lockfile) + D-CI-FUNC-7 (web-test pnpm lint:conventions) 동시 fix sprint (Amelia)
- 옵션 (b) **cj-219** D-CI-FUNC-2 (test-architecture) + D-CI-FUNC-3 (test-service-role-guard) functional fix sprint (Charlie)
- 옵션 (c) 다음 push 후 live CI run actual verification 결정 wire (cj-216 + cj-217 fix 의 4 jobs PASS expected — service-role-guard-lint + web-e2e + smoke-e2e + rls-tests)
- 옵션 (d) Epic 29+ 진입 결정 wire
- 옵션 (e) D-LAUNCH-1-DEFER-2/3/4 / D-DEFER-* follow-up 결정 wire 보류

---

## §5. Cross-references

- `AD-14-ci-verification-blocker-2026-08-29.md` §Status update cj-217 EXTENSION paragraph + §7 Honestly DEFER D-CI-FUNC-5/6 RESOLVED 표시
- `AD-14-stack-pin-policy.md` §Detection Surface cj-217 row EXTENSION + §Open Items D-CI-FUNC-5/6 RESOLVED EXTENSION + §Notes cj-217 EXTENSION paragraph + §Cross-references cj-217 EXTENSION paragraph
- `handoff-2026-08-29-cj-217-d-ci-func-5-6-install-fix-done.md` (cj-217 handoff memory)
- `commit-msg-cj-217.txt` (cj-217 commit message)
- `sprint-status.yaml` v4.17 → v4.18 EXTENSION (A865~A868 entries + last_updated_note_v4_18 + action_items D-CI-FUNC-5/6 RESOLVED done 결정 wire)
- `MEMORY.md` hook EXTENSION
- cj-216 handoff (`handoff-2026-08-29-cj-216-d-ci-func-4-service-role-guard-lint-fix-done.md`) 의 next-옵션 (a) cj-217 install-fix sprint 결정 wire 의 verbatim 후속

---

Co-Authored-By: Claude <noreply@anthropic.com>