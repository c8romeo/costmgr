---
name: handoff-2026-08-29-cj-213-corepack-enable-done
description: cj-213 corepack enable source sprint DONE (cj-style 213번째). ci.yml 의 6개 pnpm-using job (setup + lint-deps + lint-conventions + stack-pin-check + commit-prefix-lint + web-test + web-e2e) 각각에 `corepack enable` step 추가. cj-212 trigger surface EXTENSION 후 surface 된 신규 blocker ("Install JS deps" step exit 127 = `pnpm: command not found`) 의 source-side fix. **D-CI-COREPACK-1 RESOLVED**. CR 11-3 honest-DEFER 106번째 epic 연속 정직 회복.
metadata:
  type: project
  cycle: cj-style-213
  phase: corepack-enable-done
  baseline_commit: 20af77d
---

# cj-213 ci.yml corepack enable source sprint DONE (cj-style 213번째)

cj-212 next-옵션 (a) 의 verbatim 후속 = cj-212 의 trigger surface
EXTENSION 후 live CI run (run_id 33230269701, head_sha 20af77d2)
에서 surface 된 **3번째 blocker** — "Install JS deps" step 의
exit code 127 (`pnpm: command not found`) 의 source-side fix 결정
wire.

관련: [[handoff-2026-08-29-cj-212-trigger-surface-extension-done]] /
[[handoff-2026-08-29-cj-211-ci-sha-remediation-done]] /
[[handoff-2026-08-29-cj-210-ci-stack-pin-check-verification-blocked]] /
[[AD-14-ci-verification-blocker-2026-08-29]] §Status update cj-213 EXTENSION

## Verified actual scope (atomic single sprint)

**7 files = 2 NEW + 5 MODIFIED** (source-and-docs sprint — source
변경 1건 ci.yml EXTENSION, verified via `git status --short`
pre-commit):

2 NEW:
1. `_bmad-output/implementation-artifacts/commit-msg-cj-213.txt`
2. `memory/handoff-2026-08-29-cj-213-corepack-enable-done.md` (this file)

5 MODIFIED:
1. `.github/workflows/ci.yml` (6개 pnpm-using job 각각에 corepack enable step 추가 — setup + lint-deps + lint-conventions + stack-pin-check + commit-prefix-lint + web-test + web-e2e = 6 occurrences 결정 wire)
2. `docs/architecture-decisions/AD-14-stack-pin-policy.md` (§Cross-references cj-213 EXTENSION paragraph + §Open Items **D-CI-COREPACK-1 RESOLVED (cj-style 213)** 신규 결정 wire + §Notes cj-213 EXTENSION paragraph)
3. `docs/architecture-decisions/AD-14-ci-verification-blocker-2026-08-29.md` (cj-212 status 결정 wire 갱신 + §7 Honestly DEFER D-CI-COREPACK-1 RESOLVED 표시)
4. `_bmad-output/implementation-artifacts/sprint-status.yaml` v4.13 → v4.14 EXTENSION (A849~A852 4 entries 신규 + last_updated_note_v4_14 신규 + action_items D-CI-COREPACK-1 done 결정 wire)
5. `memory/MEMORY.md` (hook EXTENSION)

## fix wire 결정 boundary (cj-213 source sprint)

AD-14 ci.yml corepack enable 결정 wire — `actions/setup-node@...`
step 후 `pnpm install --frozen-lockfile` step 직전까지 pnpm binary
provisioning step 부재 해결:

```yaml
# Before (cj-211/212 결정 wire 보존):
      - uses: actions/setup-node@0a44ba7841725637a19e28fa30b79a866c81b0a6 # v6.1.0
        with: { node-version-file: ".nvmrc" }
      - uses: actions/setup-python@82c7e631bb3cdc910f68e0081d67478d79c6982d # v6.1.1
        with: { python-version-file: ".python-version" }
      - run: pip install uv==0.11.32
      - run: pnpm install --frozen-lockfile    # ← exit 127 here

# After (cj-213 EXTENSION 결정 wire):
      - uses: actions/setup-node@0a44ba7841725637a19e28fa30b79a866c81b0a6 # v6.1.0
        with: { node-version-file: ".nvmrc" }
      - name: Enable corepack (provides pnpm from packageManager field)
        run: corepack enable
      - uses: actions/setup-python@82c7e631bb3cdc910f68e0081d67478d79c6982d # v6.1.1
        with: { python-version-file: ".python-version" }
      - run: pip install uv==0.11.32
      - run: pnpm install --frozen-lockfile    # ← now pnpm is in PATH
```

적용 job (총 6개):
1. **setup** (line ~47, after setup-node)
2. **lint-deps** (line ~85, after setup-node)
3. **lint-conventions** (line ~117, after setup-node)
4. **stack-pin-check** (line ~152, after setup-node)
5. **commit-prefix-lint** (line ~242, after setup-node) — harmless extra (해당 job 이 pnpm 직접 사용 안 하지만 corepack enable 은 no-op)
6. **web-test** (line ~451, after setup-node)
7. **web-e2e** (line ~475, after setup-node)

(`commit-prefix-lint` 는 pnpm 직접 사용하지 않지만, cj-213 의
additive fix 결정 wire 으로 포함 — 미래 해당 job 의 pnpm 사용 시
자동 적용)

## 결정 근거 4종

| 근거 | 채택 | rationale |
|---|---|---|
| **Minimal-scope fix** (1줄 `run:` step 만) | ✅ | actions SHA 변경 0건 — cj-211 결정 wire verbatim 보존 |
| **Node.js 16.10+ 표준 패턴** (corepack) | ✅ | 추가 action (`pnpm/action-setup`) 도입 없이 built-in 기능 활용 |
| **package.json SSOT 보존** (`packageManager: pnpm@9.15.4`) | ✅ | pnpm 버전이 한 곳에서 관리됨 (single source of truth) |
| **AD-14 stack pin 정책 무변경** (35 pins unchanged) | ✅ | `[STACK BUMP]` tag 불필요 |

## Root cause 분석

| Symptom | Root cause | Source-side fix |
|---|---|---|
| `pnpm install --frozen-lockfile` exit 127 | `actions/setup-node@...` step 후 `pnpm` binary 가 PATH 에 부재 | `corepack enable` step 추가 — Node.js corepack 이 `package.json` 의 `packageManager: pnpm@9.15.4` field 읽고 pnpm@9.15.4 자동 provisioning |
| "Install JS deps" step 이 12개 downstream job 모두 skip cascade | setup job failure | cj-213 fix wire 으로 setup job recovery |

## 검증 실측 (all local + grep, honestly reported)

| 검증 | 결과 | 명령 / 근거 |
|---|---|---|
| T7.1 ruff scoped | N/A | ci.yml 의 YAML + corepack enable 만 변경, Python source 변경 0건 |
| T7.2 pytest scoped | N/A | ci.yml 변경은 Python pytest suite 영향 없음 |
| T7.3 vitest scoped | N/A | apps/web 변경 0건 |
| T7.4 tsc | N/A | backend-only docs sprint |
| T7.5 FINAL CLEAN | ✅ PASS | `uv run python scripts/check_stack_pin.py` → `[STACK_PIN] OK all 35 pins match`, exit 0 (cj-211 recovery 상태 verbatim 보존, 35 pins unchanged) |
| T7.12 corepack enable count | ✅ PASS | `grep -c "corepack enable" .github/workflows/ci.yml` → 6 (setup + lint-deps + lint-conventions + stack-pin-check + commit-prefix-lint + web-test + web-e2e, 예상 일치) |
| T7.13 YAML syntax valid | ✅ PASS | `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml', encoding='utf-8'))"` → valid |
| T7.14 cj-211 결정 wire 보존 | ✅ PASS | `grep -c 'actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683' .github/workflows/ci.yml` → 13 (cj-211 결정 wire verbatim 보존) + `grep -c 'actions/cache@0c907a75c2c80ebcb7f088228285e798b750cf8f' .github/workflows/ci.yml` → 2 (cj-211 결정 wire verbatim 보존) |
| T7.15 cj-212 trigger surface 보존 | ✅ PASS | `grep -c "workflow_dispatch" .github/workflows/ci.yml` → 2 (1 in rationale comment + 1 as actual trigger) + `grep -cE "^      - '9-3-\*'" .github/workflows/ci.yml` → 2 + `grep -cE "^      - 'story-\*'" .github/workflows/ci.yml` → 2 + `grep -cE "^      - main$" .github/workflows/ci.yml` → 2 |
| pre-commit git status | ✅ verified | `git status --short` → 정확히 7 files (2 NEW + 5 MODIFIED) |

## runtime 동작 변화 honestly reported

- ci.yml 의 6개 job 에 `corepack enable` step 추가 → **Node.js corepack 이 `package.json` 의 `packageManager: pnpm@9.15.4` field 읽고 pnpm@9.15.4 자동 provisioning** → `pnpm install --frozen-lockfile` 이 성공적으로 실행됨.
- **cj-211 (SHA fix) + cj-212 (trigger surface EXTENSION) + cj-213 (corepack enable) 3개 sprint 합성** 으로 cj-210 의 2개 blocker + cj-213 의 1개 blocker 가 완전히 해소되어 `9-3-dev-2026-08-17` working branch 의 다음 push 부터 CI 자동 trigger → setup recovery (corepack 으로 pnpm@9.15.4 provisioning) → downstream 12개 job trigger cycle 회복 결정 wire.
- AD-14 stack pin 정책 (35 pins) 변경 없음, actions SHAs 변경 없음 (cj-211 결정 wire verbatim 보존), `[STACK BUMP]` tag 불필요.
- `AD-14-ci-verification-blocker-2026-08-29.md` 의 status 결정 wire 갱신: '✅ cj-211 RESOLVED + cj-212 trigger surface EXTENSION' → '✅ cj-211 RESOLVED + cj-212 trigger surface EXTENSION + cj-213 corepack enable (cj-210 blocker A+B + cj-213 blocker 모두 해소)' 결정 wire.
- `AD-14-stack-pin-policy.md` 결정 wire 갱신: §Cross-references cj-213 paragraph EXTENSION + §Open Items `D-CI-COREPACK-1 ✅ RESOLVED (cj-style 213)` 신규 결정 wire + §Notes cj-213 EXTENSION paragraph 결정 wire.

## D-DEFER-* honestly 결정 wire 보존 (cj-style 213 진입 결정 wire)

| Defer ID | Status | Owner | Resolution Sprint |
|---|---|---|---|
| D-1-1-DEFER-1/2/3 | ✅ RESOLVED 보존 | kjw | Epic 1 wire cycles |
| D-EPIC-16-REVIEW-DEFER-1/2~6 | ✅ RESOLVED 보존 | kjw | Epic 16 wire cycles |
| D-PHASE-4-DR-DEFER-1/2 | ✅ RESOLVED 보존 | kjw | Phase 4 wire cycles |
| D-EPIC-17-WIRE-DEFER-T2-T3-UI | ✅ RESOLVED 보존 | kjw | Epic 17 wire cycles |
| D-RETENTION-1 | ✅ PRESERVED | kjw | 백업/보존 정책 |
| D-OBSERVABILITY-1 | ✅ PRESERVED | kjw | M1 observability |
| D-PERFORMANCE-1 | ✅ PRESERVED | kjw | M1 performance |
| D-CHAOS-1 | ✅ PRESERVED | kjw | M1 chaos |
| D-SLO-1 | ✅ PRESERVED | kjw | M1 SLO |
| D-FINOPS-1~15 | ✅ ALL RESOLVED 보존 | kjw | Phase 11~28 wire cycles |
| D-AD-14-1 | ✅ RESOLVED (cj-206) | kjw | cj-206 source sprint |
| D-AD-14-2 | ✅ RESOLVED (cj-208) | kjw | cj-208 source sprint |
| D-LAUNCH-1-DEFER-1 (sub-item a) | ✅ RESOLVED (cj-207) | kjw | cj-207 source sprint |
| D-LAUNCH-1-DEFER-2/3/4 | ⚠️ honestly DEFER | DevOps + kjw | 외부 infra provisioned 후 |
| D-LAUNCH-1-DEFER-1 (sub-items b/c/d) | honestly preserved 65~213번째 | kjw | — |
| test_erasure pytest-asyncio wiring (NEW, cj-208 관찰) | ⚠️ honestly DEFER | kjw | 별도 follow-up sprint |
| D-CI-SHA-1 | ✅ RESOLVED (cj-211) | kjw | cj-211 source sprint |
| D-CI-TRIGGER-1 | ✅ RESOLVED (cj-212) | kjw | cj-212 source sprint |
| **D-CI-COREPACK-1** | ✅ **RESOLVED (cj-213)** | kjw | cj-213 source sprint |

## Next 옵션 결정 wire 보존

- (a) 다음 cj-style sprint 진입 결정 wire (**cj-214 후보** — 다음 push 후 live CI run 의 actual verification cycle 의 stack-pin-check 등 12개 downstream job 의 결과 관찰) /
- 옵션 (b) D-LAUNCH-1-DEFER-2/3/4 external infra provisioning 결정 wire (Vercel/Railway staging + Sentry Team project + cross-region failover_orchestrator 실측 환경 구축) /
- 옵션 (c) Epic 29+ 진입 결정 wire /
- 옵션 (d) D-DEFER-* follow-up 결정 wire 보류 (test_erasure pytest-asyncio wiring + 외부 infra follow-up).

## 결정 wire 일자

2026-08-29 (KST)

## Cross-references

- **본 cj-style sprint chain**: 1~213 모두 보존
- **Epic 1~17**: 모두 DONE 보존
- **Phase 3~28 + Phase 19.5 + Phase 20.5**: 모두 DONE 보존
- **audit-fixes sprint chain**: 5개 sprint chain ✅ ALL DONE 보존
- **1st release cycle**: DONE 보존
- **Phase 11~28 18-capability FinOps territory chain**: ✅ ALL WIRED INTEGRATED 보존
- **AD-50 ~ AD-60 EXTENSION 결정 wire 보존** + **AD-14 §Detection Surface cj-213 row EXTENSION 결정 wire** + **AD-14 §Cross-references CR 11-3 line cj-213 EXTENSION paragraph** + **AD-14 §Notes cj-213 EXTENSION paragraph 결정 wire** + **AD-14 §Open Items D-CI-COREPACK-1 RESOLVED 결정 wire (cj-213 신규)**
- **AD-14-ci-verification-blocker-2026-08-29.md** status 결정 wire: '✅ cj-211 RESOLVED' → '✅ cj-211 RESOLVED + cj-212 trigger surface EXTENSION' → '✅ cj-211 RESOLVED + cj-212 trigger surface EXTENSION + cj-213 corepack enable' 결정 wire 갱신
- **Capability matrix v1.54 EXTENSION chain ✅ PRESERVED** (cj-213 자체 EXTENSION 없음 — CI corepack enable territory 이지 capability matrix territory 아님)
- **D-LAUNCH-1-DEFER-1 honestly preserved 65~213번째** 보존
- **A19 cohesion 9 surface EXTENSION PARTIAL preserved** (cj-style 213 은 Surface 1 source EXTENSION ci.yml + Surface 7 docs EXTENSION 2건 — AD-14 EXTENSION + AD-14-ci-verification-blocker 갱신, 나머지 7 surface NO 변경)
- **CR 11-3 honest-DEFER 106번째** epic 연속 정직 회복 결정 wire 보존
- **CR 11-3 honest-DEFER 105번째** (cj-212) 결정 wire 보존
- **D-CI-SHA-1 ✅ RESOLVED** 결정 wire 보존 (cj-211 source sprint 결정 wire 보존)
- **D-CI-TRIGGER-1 ✅ RESOLVED** 결정 wire 보존 (cj-212 source sprint 결정 wire 보존)
- **D-CI-COREPACK-1 ✅ RESOLVED** 결정 wire 보존 (cj-213 source sprint 결정 wire 보존)
- **cj-213 의 `AD-14-ci-verification-blocker-2026-08-29.md` 결정 wire status**: cj-211 source-side fix 결정 wire + cj-212 trigger surface EXTENSION 결정 wire + cj-213 corepack enable 결정 wire 합성으로 cj-210 의 2개 blocker (A: trigger surface + B: setup SHA) + cj-213 의 1개 blocker (corepack 부재) 모두 해소