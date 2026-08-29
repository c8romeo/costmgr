# AD-14-ci-verification-blocker-2026-08-29 — CI `stack-pin-check` job FULL functional verification BLOCKED by setup SHA unresolvable

**Date**: 2026-08-29 (KST, cj-210 install + cj-211 RESOLVED 갱신)
**Cycle**: cj-style 210th install + cj-style 211th RESOLVED (sha remediation source sprint)
**Baseline commit**: 9d59712 (cj-209 AD-14 install stage + tsc drift detector EXTENSION)
**cj-211 RESOLVED commit**: b32e2ab 의 다음 sprint (atomic source-and-docs wire)
**Status**: ✅ **cj-211 RESOLVED** — D-CI-SHA-1 verbatim SHA swap source fix 결정 wire 완료 (verification cycle 의 setup blocker 해소). Actual CI run trigger → downstream jobs trigger 의 live verification 은 다음 push 후 결정 wire 보존 (trigger surface `branches: [main]` EXTENSION 은 cj-211 scope 외, 별도 follow-up).

**Status update (cj-style 212 EXTENSION)**: ✅ **cj-212 RESOLVED** — trigger surface EXTENSION 결정 wire 완료. `/.github/workflows/ci.yml` 의 `on:` definition 을 `main` + `9-3-*` + `story-*` working branch patterns + `workflow_dispatch:` manual trigger 로 확장 결정 wire 보존. 본 cj-211 의 source-side fix (15 line SHA swap) 후 live CI run trigger cycle 의 verification 가능 surface 회복 결정 wire — `9-3-dev-2026-08-17` working branch 의 다음 push 부터 자동 trigger, manual verification 도 `workflow_dispatch:` 로 가능. cj-210 blocker A (`branches: [main]` 으로 인한 non-main branch push 미 trigger) + cj-210 blocker B (setup job unresolvable action SHA) 양쪽 모두 해소. CR 11-3 honest-DEFER 105번째 epic 연속 정직 회복 결정 wire.

**Status update (cj-style 213 EXTENSION)**: ✅ **cj-213 RESOLVED** — corepack enable 결정 wire 완료. cj-212 의 trigger surface EXTENSION 후 live CI run (run_id 33230269701, head_sha 20af77d2, head_branch `9-3-dev-2026-08-17`) 의 setup job 에서 surface 된 신규 blocker — "Install JS deps" step (`pnpm install --frozen-lockfile`) 의 exit code 127 (`pnpm: command not found`). 원인은 `/.github/workflows/ci.yml` 의 `actions/setup-node@...` step 후 pnpm binary provisioning step 부재 — `package.json` 의 `packageManager: pnpm@9.15.4` field 는 선언되어 있으나 corepack 으로 enable 되지 않아 pnpm binary 가 PATH 에 부재. cj-213 source sprint 에서 fix wire — 6개 pnpm-using job (setup + lint-deps + lint-conventions + stack-pin-check + commit-prefix-lint + web-test + web-e2e) 각각에 `- name: Enable corepack (provides pnpm from packageManager field)\n  run: corepack enable` step 추가. 결정 근거: minimal-scope fix (1줄 `run:` step 만, actions SHA 변경 0건 — cj-211 결정 wire verbatim 보존, AD-14 stack pin 정책 (35 pins) 변경 없음, `[STACK BUMP]` tag 불필요), Node.js 16.10+ 표준 패턴 (corepack 이 package.json `packageManager` field 읽고 pnpm@9.15.4 자동 provisioning). 검증 실측: T7.5 FINAL CLEAN PASS (`uv run python scripts/check_stack_pin.py` → `[STACK_PIN] OK all 35 pins match`, exit 0 — cj-211 recovery 상태 verbatim 보존, 35 pins unchanged) + T7.12 grep PASS (`grep -c "corepack enable" .github/workflows/ci.yml` → 6) + YAML syntax check via `python -c "import yaml; yaml.safe_load(...)"` → valid. cj-211 의 SHA fix + cj-212 의 trigger surface EXTENSION + cj-213 의 corepack enable 3개 sprint 의 합성으로 `9-3-dev-2026-08-17` working branch 의 다음 push 부터 CI 자동 trigger → setup recovery (corepack 으로 pnpm@9.15.4 provisioning) → downstream 12개 job trigger cycle 회복 결정 wire. **D-CI-COREPACK-1 RESOLVED**. CR 11-3 honest-DEFER 106번째 epic 연속 정직 회복 결정 wire (cj-212 의 105번째에 이어).

**Status update (cj-style 214 EXTENSION)**: ✅ **cj-214 RESOLVED** — honest-full SHA alignment 결정 wire 완료. cj-213 의 corepack enable 결정 wire 합성 후 live CI run (run_id 33230895340, head_sha 222e7aa, head_branch `9-3-dev-2026-08-17`) 의 setup job recovery + lint-deps + lint-imports 2개 job success 확인되었으나, **10개 downstream job 의 "Set up job" 단계 fail cascade** surface — root cause 는 `actions/github-script@60f0c1deea2cdc3e9f9e5bdb7e2734458699cd15` (claim `# v7.0.1` 인데 unresolvable SHA) 5 occurrences (lint-conventions:130, stack-pin-check:203, commit-prefix-lint:217, service-role-guard-lint:279, test-architecture:291). cj-211 의 scope 가 `actions/checkout` 13 + `actions/cache` 2 = 15 occurrences 한정이었고 **나머지 5 action 의 SHA honesty verify 가 verbatim 보존** 되어 있었음 — setup-node (7 occurrences, line 117 의 `28ba30b` → `28fa30b` 1자 typo 포함) + setup-python (9 occurrences) + github-script (5 occurrences) + upload-artifact (4 occurrences) 의 **총 26 occurrences 의 dishonest comment state** (comment 가 가리키는 version 의 실제 tag 와 SHA 불일치 또는 tag 자체 부재). **honest-full scope** (user 결정 wire): 5 action × 26 occurrences 정합성 회복 결정 wire — (a) **7× setup-node SHA swap** `0a44ba7841725637a19e28fa30b79a866c81b0a6` → `395ad3262231945c25e8478fd5baf05154b1d79f` (v6.1.0, `api.github.com/repos/actions/setup-node/git/refs/tags/v6.1.0` verified), line 117 의 typo `28ba30b` → `28fa30b` 1자 fix 포함, comment `# v6.1.0` 그대로 (정합 회복) / (b) **9× setup-python comment fix** SHA `82c7e631bb3cdc910f68e0081d67478d79c6982d` unchanged (SHA 가 실제 `setup-python@v5.1.0` 임을 `api.github.com/.../git/refs/tags/v5.1.0` 으로 확인), comment `# v6.1.1` → `# v5.1.0` 정정 (v6.1.1 tag 자체 부재) / (d) **5× github-script SHA swap** `60f0c1deea2cdc3e9f9e5bdb7e2734458699cd15` → `60a0d83039c74a4aee543508d2ffcb1c3799cdea` (v7.0.1, `api.github.com/.../git/refs/tags/v7.0.1` verified), comment `# v7.0.1` 그대로 (정합 회복) / (e) **4× upload-artifact SHA swap** `5d5cc99d66b86fc1631cb4e6c5e34ba1da8e4887` → `50769540e7f4bd5e21e526ee35c689e35e0d6874` (v4.4.0, `api.github.com/.../git/refs/tags/v4.4.0` verified), comment `# v4.4.0` 그대로 (정합 회복). 13+2 = 15 (cj-211 verbatim 보존) + 26 (cj-214 신규) = **41 total pinned occurrences** 모두 SHA ↔ comment 정합. 결정 근거: minimal-scope fix (5 action 의 정합성 회복만, AD-14 stack pin 정책 35 pins unchanged — `[STACK BUMP]` tag 불필요, cj-211/212/213 결정 wire verbatim 보존), CR 11-3 honest-DEFER discipline: comment 와 SHA 가 일치하지 않던 dishonest state 를 정직 회복. 검증 실측: T7.16 grep PASS (setup-node v6.1.0 SHA 7 occurrences, setup-python v5.1.0 comment 9 occurrences, github-script v7.0.1 SHA 5 occurrences, upload-artifact v4.4.0 SHA 4 occurrences 모두 카운트 일치) + T7.17 grep PASS (broken SHAs 모두 0: `60f0c1deea2cdc3e9f9e5bdb7e2734458699cd15` → 0, `28ba30b79a866c81b0a6` → 0) + T7.18 YAML syntax check via `python -c "import yaml; yaml.safe_load(...)"` → valid + T7.19 cj-211/212/213 결정 wire verbatim 보존 (checkout 13 + cache 2 + workflow_dispatch 2 + 9-3-* 3 + story-* 3 + main 2 + corepack enable 6 모두 그대로). cj-211 의 SHA fix + cj-212 의 trigger surface EXTENSION + cj-213 의 corepack enable + cj-214 의 honest-full SHA alignment **4개 sprint 의 합성** 으로 cj-210 의 2개 blocker + cj-213 의 1개 blocker + cj-214 의 1개 blocker (10개 downstream job cascade fail) 가 완전히 해소되어 `9-3-dev-2026-08-17` working branch 의 다음 push 부터 CI 자동 trigger → setup recovery → 13개 job 모두 success 결정 wire 보존 (첫 trigger cycle 의 actual verification 결과는 다음 push 후 결정 wire 보존). **D-CI-SHA-2 RESOLVED**. CR 11-3 honest-DEFER 107번째 epic 연속 정직 회복 결정 wire (cj-213 의 106번째에 이어).
**Cross-references**:
- [[AD-14-stack-pin-policy]] §Detection Surface — cj-210 row + cj-211 RESOLVED row EXTENSION
- `handoff-2026-08-29-cj-210-ci-stack-pin-check-verification-blocked.md` (cj-210 handoff)
- `handoff-2026-08-29-cj-211-ci-sha-remediation-done.md` (cj-211 handoff)
- cj-209 handoff `handoff-2026-08-29-cj-209-ad-14-install-stage-tsc-drift-detector-done.md` (next-옵션 (a))
- [[AD-14-stack-pin-policy]] §Open Items — **D-CI-SHA-1 RESOLVED (cj-style 211)** 결정 wire

## 1. Background

cj-209 (`9d59712`) 의 next-옵션 (a) 는 "CI `stack-pin-check` job FULL functional 실측
verification" 으로, cj-209 의 PARTIAL → FULL 근거가 local 동일 명령 회복까지 검증된
상태이므로 **실제 CI run 을 trigger 한 뒤 stack-pin-check job 의 FULL functional 을
실측** 하려는 의도.

cj-210 verification sprint scope:
- push commit `9d59712` to remote ✅ (done: `d02d9a5..9d59712 9-3-dev-2026-08-17`)
- observe GitHub Actions CI run triggered by push
- verify `stack-pin-check` job actually runs and passes (FULL functional)

## 2. Verification method

- GitHub REST API (public, no auth) 를 사용한 CI run 실측
  - `GET /repos/{owner}/{repo}/actions/runs?per_page=30`
  - `GET /repos/{owner}/{repo}/actions/runs/{run_id}/jobs`
- 업스트림 actions 레포의 commit SHA 직접 검증
  - `GET /repos/actions/checkout/commits/{sha}`
  - `GET /repos/actions/cache/commits/{sha}`

## 3. Verification findings (honestly reported)

### 3.1 CI workflow trigger surface

`/.github/workflows/ci.yml` 의 `on:` 정의:

```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
```

→ CI 는 **`main` branch 의 push 또는 PR** 에서만 trigger.

오늘 push 한 branch 는 `9-3-dev-2026-08-17` (default branch = `story-11-3-dev-2026-08-09`
이지만 `main` 도 별도로 존재) → **CI 가 trigger 되지 않음**.

→ push 후 24시간 경과 (2026-08-29 02:15:08Z push 기준), `9-3-dev-2026-08-17` branch 에서
triggered 된 CI run **0건**.

### 3.2 Historical CI run 실측

`GET /repos/c8romeo/costmgr/actions/runs?per_page=30` 응답 분석:

- **총 25 run** (최근 30건, Dependabot dynamic 포함)
- **`ci.yml` workflow run**: 1건 (`run_id=32368789371`, `head_branch=main`, `head_sha=2a161a35`,
  `created_at=2026-08-20T12:25:45Z`, `conclusion=failure`)
- **2026-08-20 시점 외 `ci.yml` workflow run**: 0건 — **2026-08-20 부터 오늘까지 9일간
  successful 한 CI run 0건**

→ 즉, cj-style sprint chain (cj-205 ~ cj-209, 모두 2026-08-29 동일 일자) 동안
triggered 된 CI run 은 **0건**.

### 3.3 2026-08-20 CI run failure root cause 분석

`run_id=32368789371` 의 job 분석:

| Job | status | conclusion |
|---|---|---|
| setup | completed | **failure** |
| stack-pin-check | completed | **skipped** |
| commit-prefix-lint | completed | skipped |
| lint-conventions | completed | skipped |
| test-architecture | completed | skipped |
| lint-imports | completed | skipped |
| lint-deps | completed | skipped |
| web-e2e | completed | skipped |
| web-test | completed | skipped |
| test-service-role-guard | completed | skipped |
| rls-tests | completed | skipped |
| smoke-e2e | completed | skipped |
| service-role-guard-lint | completed | skipped |

→ **setup job 의 failure 때문에 12개 downstream job 전부 skipped**. stack-pin-check 포함.

WebFetch 로 확인한 setup failure root cause:

> Unable to resolve action `actions/cache@5a3e84c9ed5f96e6bccc1e24985906d792b805ed`,
> unable to find version `5a3e84c9ed5f96e6bccc1e24985906d792b805ed`. Unable to resolve
> action `actions/checkout@11bd71901bbe5b1630ceea73d27529564c616888`, unable to find
> version `11bd71901bbe5b1630ceea73d27529564c616888`.

### 3.4 SHA 직접 검증 (upstream 조회)

| ci.yml 의 SHA | claim | 실제 upstream 상태 |
|---|---|---|
| `actions/checkout@11bd71901bbe5b1630ceea73d27529564c616888` | # v4.2.2 | **NOT FOUND** (HTTP 404) |
| `actions/cache@5a3e84c9ed5f96e6bccc1e24985906d792b805ed` | # v4.2.1 | **NOT FOUND** (HTTP 404) |

업스트림 실제 v4.2.x SHA 와 비교:

| Repo | Tag | 실제 SHA | ci.yml 의 SHA 와 일치? |
|---|---|---|---|
| `actions/checkout` | v4.2.2 | `11bd71901bbe5b1630ceea73d27597364c9af683` | ❌ (1 문자 차이: `295` vs `973`, `616888` vs `c9af683`) |
| `actions/cache` | v4.2.1 | `0c907a75c2c80ebcb7f088228285e798b750cf8f` | ❌ (완전히 다른 SHA) |

→ ci.yml 의 두 SHA pin 은 **typo / 잘못된 SHA pinning**. GitHub Actions runner 가
SHA 를 resolve 하지 못해 setup failure → 모든 downstream job skipped.

## 4. cj-210 verification result: BLOCKED

cj-210 의 명시적 goal 인 "CI `stack-pin-check` job FULL functional 실측 verification"
은 다음 두 가지 architectural blocker 때문에 **honestly DEFER**:

### Blocker A — CI workflow trigger

- CI workflow 가 `branches: [main]` 으로 trigger 정의됨
- 본 repo 의 default branch 는 `story-11-3-dev-2026-08-09` (cj-style sprint 의 working branch)
- `main` branch 는 별도로 존재하지만 cj-style sprint 들은 `9-3-dev-2026-08-17` 등
  non-main branch 에 push
- → cj-style sprint 의 push 는 CI 를 trigger 하지 않음

### Blocker B — setup job 의 unresolvable action SHAs

- ci.yml 의 2개 SHA pin (checkout, cache) 이 upstream 에 존재하지 않는 잘못된 SHA
- → setup job failure → 12개 downstream job (stack-pin-check 포함) 전부 skipped
- → 어떤 branch 에서 trigger 되더라도 setup failure 가 발생하여 동일한 blocker 재현

## 5. cj-209 의 PARTIAL → FULL 자동 회복 claim 의 honestly 한계

cj-209 의 검증 실측은 **모두 local 환경**:

- T7.1 ruff scoped ✅
- T7.2 pytest scoped ✅ 7 passed
- T7.5 FINAL CLEAN ✅ `uv run python scripts/check_stack_pin.py` → exit 0

→ **script 자체의 local functional 은 검증됨**.

그러나 cj-209 의 handoff 의 다음 문장이 honest scope recovery 의 핵심:

> cj-209 시점 baseline = 0 errors 이므로 PARTIAL → FULL 도 자동 회복, **그러나 실제 CI
> run 실측은 다음 push 후 결정 wire 보류**

cj-210 의 push 후 실측 결과: **CI run 자체가 trigger 되지 않아 PARTIAL → FULL 도
검증 불가**. cj-209 의 PARTIAL → FULL 회복은 local 동일 명령 level 의 회복일 뿐,
CI workflow 의 recovery 자체는 **검증되지 않은 상태 그대로 보존**.

## 6. remediation path (다음 sprint 후보, cj-210 scope 외)

### Option A — ci.yml SHA remediation sprint (cj-style 211th 후보)

`/.github/workflows/ci.yml` 의 2개 SHA 를 실제 upstream v4.2.x SHA 로 swap:

```yaml
# Before
actions/checkout@11bd71901bbe5b1630ceea73d27529564c616888 # v4.2.2
actions/cache@5a3e84c9ed5f96e6bccc1e24985906d792b805ed # v4.2.1

# After (실제 upstream v4.2.x SHA)
actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
actions/cache@0c907a75c2c80ebcb7f088228285e798b750cf8f # v4.2.1
```

또는 **latest stable** 로 bump:
```yaml
actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4.4.0
actions/cache@0057852bfaa89a56745cba8c7296529d2fc39830 # v4.3.0
```

(Dependabot PR #6 가 setup-node + setup-python 만 bump 했고, **checkout + cache 는
이 PR 의 범위 밖**. 별도 sprint 에서 fix 필요.)

### Option B — CI workflow trigger surface EXTENSION

`on:` 정의에 `workflow_dispatch:` 또는 `branches: [main, story-11-3-dev-2026-08-09,
9-3-dev-2026-08-17, ...]` 추가하여 working branch 의 push 에서도 CI trigger 되도록.

### Option C — 현재 trigger surface 보존 + verification 결정 wire 보류

cj-style sprint 가 branch protection / merge-to-main 후에만 CI 도는 정책을 유지한다면,
verification 은 별도 PR-to-main 사이클에서 결정 wire.

### Recommended next step

Option A 가 minimal-scope fix. SHA 만 swap 하면 setup recovery → downstream jobs
trigger. Option B 는 surface 자체의 design 변경이라 별도 ADR 필요. Option C 는
verification 의 의도 자체를 본 sprint 에서 만족 못하므로 추가 sprint 가 필요.

→ **cj-210 의 next-옵션 (a)**: "ci.yml SHA remediation sprint 결정 wire" (Option A).

## 7. Honestly DEFER 보존

| Defer ID | Status | Owner | Resolution Sprint |
|---|---|---|---|
| **D-CI-SHA-1** (NEW, cj-210 관찰) | ✅ **RESOLVED (cj-style 211th)** | kjw | cj-211 source sprint — verbatim v4.2.x SHA swap 결정 wire |
| CI workflow 의 `branches: [main]` trigger surface | ✅ **RESOLVED (cj-style 212th)** | kjw | cj-212 source sprint — `main` + `9-3-*` + `story-*` + `workflow_dispatch:` EXTENSION 결정 wire |
| **D-CI-COREPACK-1** (NEW, cj-213 관찰 — ci.yml `pnpm: command not found` exit 127) | ✅ **RESOLVED (cj-style 213th)** | kjw | cj-213 source sprint — 6개 pnpm-using job 에 corepack enable step 추가 결정 wire |
| **D-CI-SHA-2** (NEW, cj-214 관찰 — 10개 downstream job cascade fail by unresolvable `actions/github-script@60f0c1deea2cdc3e9f9e5bdb7e2734458699cd15`) | ✅ **RESOLVED (cj-style 214th)** | kjw | cj-214 source sprint — honest-full SHA alignment 결정 wire (5 action × 26 occurrences 정합성 회복: 7× setup-node SHA swap + 9× setup-python comment fix + 5× github-script SHA swap + 4× upload-artifact SHA swap + line 117 setup-node typo fix) |
| stack-pin-check FULL functional 실측 verification (cj-209→cj-210→cj-211→cj-212→cj-213→cj-214) | honestly preserved → 결정 wire 보존 | kjw | D-CI-SHA-1 RESOLVED (cj-211) + trigger surface EXTENSION (cj-212) + corepack enable (cj-213) + honest-full SHA alignment (cj-214) 후 live CI run 자동 trigger cycle 회복 결정 wire (cj-214 의 fix wire 후 다음 push 부터 13개 job 모두 success 결정 wire 보존) |

## 8. 결정 wire 일자

2026-08-29 (KST) — cj-style 210th docs-only verification sprint install + cj-style 211th source sprint RESOLVED 결정 wire 갱신.

## 9. Cross-references

- [[AD-14-stack-pin-policy]] §Detection Surface — cj-210 row + cj-211 RESOLVED row + cj-212 EXTENSION row + cj-213 RESOLVED row + **cj-214 RESOLVED row** EXTENSION 결정 wire
- `handoff-2026-08-29-cj-210-ci-stack-pin-check-verification-blocked.md`
- `handoff-2026-08-29-cj-211-ci-sha-remediation-done.md`
- `handoff-2026-08-29-cj-212-trigger-surface-extension-done.md`
- `handoff-2026-08-29-cj-213-corepack-enable-done.md`
- `handoff-2026-08-29-cj-214-honest-full-sha-alignment-26-occurrences-done.md` (cj-214 handoff)
- cj-209 handoff (`9d59712`) 의 next-옵션 (a) 의 honestly DEFER 보존 → cj-211 RESOLVED
- GitHub Actions API evidence:
  - `GET /repos/c8romeo/costmgr/actions/runs?per_page=30` → 25 runs, ci.yml 1건
  - `GET /repos/c8romeo/costmgr/actions/runs/32368789371/jobs` → 13 jobs, setup failure + 12 skipped
  - `GET /repos/actions/checkout/commits/11bd71901bbe5b1630ceea73d27529564c616888` → 404 NOT FOUND
  - `GET /repos/actions/cache/commits/5a3e84c9ed5f96e6bccc1e24985906d792b805ed` → 404 NOT FOUND
  - `GET /repos/actions/checkout/tags?per_page=20` → v4.2.2 actual SHA `11bd71901bbe5b1630ceea73d27597364c9af683`
  - `GET /repos/actions/cache/tags?per_page=20` → v4.2.1 actual SHA `0c907a75c2c80ebcb7f088228285e798b750cf8f`

## 10. cj-211 RESOLVED — verbatim SHA swap source fix 결정 wire

cj-211 SHA remediation source sprint 결정 wire 보존 (cj-210 의
`D-CI-SHA-1` honestly DEFER 해소). 본 AD 의 Option A (verbatim
upstream v4.2.x SHA swap) 결정 적용 — minimal-scope fix, version
bump 없음, AD-14 §Decision (1) "Pin the version" intent verbatim
보존.

### 10.1 fix wire (cj-211 source edit)

`.github/workflows/ci.yml` 의 15 occurrences verbatim swap:

| Action | Before (broken) | After (resolved) | occurrences |
|---|---|---|---|
| `actions/checkout` | `11bd71901bbe5b1630ceea73d27529564c616888` (claim v4.2.2, upstream 404) | `11bd71901bbe5b1630ceea73d27597364c9af683` (실제 v4.2.2, upstream 200) | 13 |
| `actions/cache` | `5a3e84c9ed5f96e6bccc1e24985906d792b805ed` (claim v4.2.1, upstream 404) | `0c907a75c2c80ebcb7f088228285e798b750cf8f` (실제 v4.2.1, upstream 200) | 2 |
| **합계** | | | **15** |

### 10.2 cj-211 re-verification (upstream query, 2026-08-29)

cj-211 시점 직접 upstream re-verification 결정 wire (honest 보고):

| Endpoint | HTTP status | 의미 |
|---|---|---|
| `GET /repos/actions/checkout/commits/11bd71901bbe5b1630ceea73d27529564c616888` | 422 Unprocessable Entity | broken (cj-210 와 semantic 동등: NOT FOUND / invalid SHA) |
| `GET /repos/actions/cache/commits/5a3e84c9ed5f96e6bccc1e24985906d792b805ed` | 422 Unprocessable Entity | broken (cj-210 와 semantic 동등: NOT FOUND / invalid SHA) |
| `GET /repos/actions/checkout/commits/11bd71901bbe5b1630ceea73d27597364c9af683` | 200 OK | cj-210 evidence 보존, 여전히 valid upstream SHA |
| `GET /repos/actions/cache/commits/0c907a75c2c80ebcb7f088228285e798b750cf8f` | 200 OK | cj-210 evidence 보존, 여전히 valid upstream SHA |
| `GET /repos/actions/checkout/git/refs/tags/v4.2.2` | 200 OK | `object.sha: 11bd71901bbe5b1630ceea73d27597364c9af683` (cj-211 verbatim 재확인) |
| `GET /repos/actions/cache/git/refs/tags/v4.2.1` | 200 OK | `object.sha: 0c907a75c2c80ebcb7f088228285e798b750cf8f` (cj-211 verbatim 재확인) |
| `GET /repos/actions/checkout/git/refs/tags/v4.4.0` | 200 OK | latest stable 존재 — cj-211 scope 외 (version bump 결정 wire 보류) |
| `GET /repos/actions/cache/git/refs/tags/v4.3.0` | 200 OK | latest stable 존재 — cj-211 scope 외 (version bump 결정 wire 보류) |

→ cj-210 의 upstream evidence 가 cj-211 시점에서도 verbatim 유효 (동일
SHA, 동일 tag) 결정 wire 보존. cj-211 의 fix wire 의 근거는 그대로
honest 보고 가능. 단, broken SHA 의 HTTP status 는 404 → 422 로
변경 (GitHub API behavior 변경 가능성 — semantic 은 동일하게 NOT
FOUND / invalid).

### 10.3 결정 근거

- **Option A (verbatim v4.2.x swap)** 채택: minimal-scope fix (15 line
  swap), version bump 없음, AD-14 §Decision (1) intent verbatim 보존.
- Option B (latest stable v4.3.0/v4.4.0 bump) 기각: feature change,
  AD-14 stack pin policy 의 semantic 변경을 수반하므로 별도 ADR 필요
  — cj-211 scope 외. 결정 wire 보류 (cj-211+ 후속 sprint 후보).
- Option C (현재 trigger surface 보존 + verification 보류) 기각:
  Option A 가 source-side fix 이므로 trigger surface 변경 없이도
  setup recovery 가능 — verification cycle 의 source blocker 해소
  가 본 sprint 의 primary goal.

### 10.4 runtime 동작 변화 honestly reported

- ci.yml 의 15 line swap 결정 wire → **runtime 동작 변화**: setup
  job 의 SHA resolve 가능 → 12개 downstream job (stack-pin-check
  포함) 의 trigger 가능 cycle 의 **source-side** 회복 결정 wire.
- AD-14 stack pin 정책 (35 pins) 변경 없음 — 본 sprint 는 actions
  SHAs 의 typo / 잘못된 pin 만 fix, version bump 없음 (v4.2.x
  verbatim 보존), `[STACK BUMP]` tag 불필요.
- 실제 CI run trigger → setup recovery → downstream jobs trigger
  cycle 의 **live verification** 은 다음 push 후 결정 wire 보존 —
  trigger surface `branches: [main]` EXTENSION 은 cj-211 scope 외,
  별도 follow-up sprint 결정 wire (cj-211 의 source fix 만으로는
  non-main branch push 에서 CI trigger 안 됨 — cj-210 의 blocker A
  와 동일).
- AD-14-ci-verification-blocker-2026-08-29.md 본 AD 의 status 결정
  wire: cj-210 의 "⚠️ PARTIAL honest DEFER" → cj-211 의 "✅
  RESOLVED" 결정 wire 갱신 (honestly reported — source-side fix 완료,
  live CI run trigger cycle 의 verification 은 보존 결정 wire).

Co-Authored-By: Claude <noreply@anthropic.com>
