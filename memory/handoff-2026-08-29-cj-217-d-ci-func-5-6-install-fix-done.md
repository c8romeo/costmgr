---
name: handoff-2026-08-29-cj-217-d-ci-func-5-6-install-fix-done
description: cj-217 D-CI-FUNC-5+6 install-fix source sprint 결정 wire handoff (cj-style 217번째 🟡 HIGH) — 2026-08-29 (KST)
metadata:
  type: project
---

# cj-217 D-CI-FUNC-5+6 install-fix source sprint handoff (cj-style 217번째)

**일자**: 2026-08-29 (KST)
**sprint**: cj-style 217번째 🟡 HIGH install-fix source sprint
**baseline**: `3a25b9d` (cj-216 D-CI-FUNC-4 service-role-guard-lint fix sprint)
**target**: `9-3-dev-2026-08-17` working branch
**sprint goal**: cj-215 의 7 NEW blockers 중 🟡 HIGH D-CI-FUNC-5 (web-e2e chromium install) + 🟡 HIGH D-CI-FUNC-6 (smoke-e2e + rls-tests psql install, 2 jobs 공유 root cause) 의 actual source fix DONE

## 결정 wire 요약

### fix scope

ci.yml 의 4 step 변경/신규:
1. **rls-tests** job 의 `Install psql` step — single-line → multi-line (3 commands: `sudo apt-get update -qq` + `sudo apt-get install -y --no-install-recommends postgresql-client` + `psql --version` verification)
2. **smoke-e2e** job 의 `Install psql` step — 동일 pattern (D-CI-FUNC-6 의 2 jobs 공유 root cause → 1개 fix cycle 동시 적용)
3. **web-e2e** job 의 `Install Playwright system dependencies` step 신규 — `sudo apt-get install -y --no-install-recommends` 13 chromium system libs (Playwright 1.62.1 공식 sys-deps list verbatim)
4. **web-e2e** job 의 `Run pnpm playwright install chromium` step 신규 — browser binary download only (apt-get subprocess race 회피)

### 결정 boundary

- **Option B 채택**: silent-failure antipattern 분해 = `>/dev/null` redirect 제거 + missing `sudo` 명시 추가 + `-qq` quiet flag 제거 + `--no-install-recommends` flag 추가 + `psql --version` verification step 추가
- **Option A 기각** (`--with-deps` 와 `>/dev/null` 을 verbatim 보존): fix 효과 0건
- **Option C 기각** (Docker image 사용): AD-14 stack pin 정책 변경 위험
- 결정 근거 4종: ① silent-failure antipattern 완전 제거 ② stderr visible + exit code propagated ③ `--no-install-recommends` 로 minimal install ④ AD-14 stack pin 정책 (35 pins) unchanged (action SHA / version comment 변경 0건, `[STACK BUMP]` tag 불필요)

## 검증 실측 (all local, honestly reported)

- T7.5 FINAL CLEAN ✅ PASS — `[STACK_PIN] OK all 35 pins match` exit 0
- T7.30 ci.yml yaml syntax ✅ PASS — valid YAML
- T7.31 install step structural diff ✅ PASS — 4 step 변경/신규
- T7.32 sudo + visible stderr + verification pattern ✅ PASS — `sudo apt-get` 4 + `>/dev/null` 0 + `psql --version` 2
- T7.33 cj-211~216 결정 wire verbatim 보존 ✅ PASS — 41 SHA pinned occurrences + 6 corepack enable + 5 trigger surface unchanged
- T7.34 install step exit code propagation ✅ PASS — `--no-install-recommends` flag 의 exit code propagation (manual reasoning)

## runtime 동작 변화 honestly reported

- ci.yml 의 4 step 변경/신규 (silent-failure antipattern 제거)
- AD-14 stack pin 정책 (35 pins) unchanged + `[STACK BUMP]` tag 불필요
- Python + TS source 변경 0건 / apps/api + apps/web 무변경 / functional behavior 변경 0건
- 다음 push 후 4 jobs (service-role-guard-lint + web-e2e + smoke-e2e + rls-tests) 의 install step 정상 동작 expected 결정 wire

## 결정 wire 보존 (8 files)

3 NEW:
1. `_bmad-output/implementation-artifacts/cj-217-d-ci-func-5-6-install-fix-report.md` (~270 LOC §1~§5)
2. `_bmad-output/implementation-artifacts/commit-msg-cj-217.txt`
3. `memory/handoff-2026-08-29-cj-217-d-ci-func-5-6-install-fix-done.md` (this file)

5 MODIFIED:
1. `.github/workflows/ci.yml` (4 step 변경/신규)
2. `docs/architecture-decisions/AD-14-ci-verification-blocker-2026-08-29.md` (cj-217 EXTENSION)
3. `docs/architecture-decisions/AD-14-stack-pin-policy.md` (cj-217 EXTENSION)
4. `_bmad-output/implementation-artifacts/sprint-status.yaml` v4.17 → v4.18 EXTENSION
5. `memory/MEMORY.md` (hook EXTENSION)

## 결정 wire 결과물 (CR 11-3 honest-DEFER 110번째)

- **D-CI-FUNC-5 ✅ RESOLVED (cj-style 217)** 결정 wire — cj-215 의 🟡 HIGH honestly DEFER → cj-217 의 done
- **D-CI-FUNC-6 ✅ RESOLVED (cj-style 217)** 결정 wire — cj-215 의 🟡 HIGH honestly DEFER → cj-217 의 done (2 jobs 동시 fix: smoke-e2e + rls-tests)
- **나머지 4개 FAIL blocker (D-CI-FUNC-1/2/3/7) honestly DEFER 보존** (cj-218/219 결정 wire 후보)

## next 결정 wire 후보

- 옵션 (a) **cj-218** D-CI-FUNC-1 (lint-conventions pnpm install --frozen-lockfile) + D-CI-FUNC-7 (web-test pnpm lint:conventions) 동시 fix sprint (Amelia)
- 옵션 (b) **cj-219** D-CI-FUNC-2 (test-architecture) + D-CI-FUNC-3 (test-service-role-guard) functional fix sprint (Charlie)
- 옵션 (c) 다음 push 후 live CI run actual verification (cj-216 + cj-217 fix 의 4 jobs PASS expected)
- 옵션 (d) Epic 29+ 진입 결정 wire
- 옵션 (e) D-LAUNCH-1-DEFER-2/3/4 / D-DEFER-* follow-up 결정 wire 보류

## Cross-references

- cj-216 handoff: `handoff-2026-08-29-cj-216-d-ci-func-4-service-role-guard-lint-fix-done.md`
- cj-215 handoff: `handoff-2026-08-29-cj-215-live-ci-verification-done.md`
- cj-216 verification report: `_bmad-output/implementation-artifacts/cj-216-d-ci-func-4-service-role-guard-lint-fix-report.md`
- AD-14 ci-verification-blocker: `docs/architecture-decisions/AD-14-ci-verification-blocker-2026-08-29.md`
- AD-14 stack-pin-policy: `docs/architecture-decisions/AD-14-stack-pin-policy.md`
- sprint-status: `_bmad-output/implementation-artifacts/sprint-status.yaml` v4.18 EXTENSION

## Why

cj-217 의 sprint goal = cj-215 의 7 NEW blockers 중 🟡 HIGH 2개 (D-CI-FUNC-5 + D-CI-FUNC-6) 의 silent-failure antipattern 제거. silent-failure antipattern (3-component: `>/dev/null` redirect + missing `sudo` + `-qq` quiet flag) 이 install failure 의 root cause 이며, ci.yml 의 step 내부 command 만 변경하여 AD-14 stack pin 정책 (35 pins) verbatim 보존 + `[STACK BUMP]` tag 불필요 결정 wire.

## How to apply

cj-217 의 fix wire 결정 (Option B 채택) 패턴을 다른 ci.yml install step 에 동일하게 적용 가능:
1. `>/dev/null` redirect 제거 → stderr visible
2. explicit `sudo` prefix 추가 → non-root context portability
3. `-qq` quiet flag 제거 → apt-get message visible
4. `--no-install-recommends` flag 추가 → minimal install
5. `xxx --version` 또는 equivalent verification step 추가 → install 성공 assert

cj-218 / cj-219 / Epic 29+ sprint 에서 동일 pattern 의 install step (e.g., 새로운 PostgreSQL version 추가 시) 에 verbatim 적용 가능.

## Related memories

- [[handoff-2026-08-29-cj-216-d-ci-func-4-service-role-guard-lint-fix-done]]
- [[handoff-2026-08-29-cj-215-live-ci-verification-done]]
- [[cj-style-atomic-sprint-pattern]] (cj-style 결정 wire 보존 패턴)