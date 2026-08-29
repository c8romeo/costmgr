---
name: handoff-2026-08-29-cj-205-ad-14-stack-pin-policy-ad-entry-done
description: AD-14 Stack Pin Policy formal AD install DONE (cj-style 205th). 5 files = 3 NEW + 2 MODIFIED atomic docs-only sprint. AD-14 의 formal architecture decision document 신규 install — 100+ cross-reference 의 AD 부재 정직 회복 + Node detector functional + Python detector NOT runnable honestly reported + D-AD-14-1 신규 honestly DEFER. CR 11-3 honest-DEFER 98번째 epic 연속 정직 회복.
metadata:
  type: project
  cycle: cj-style-205
  phase: ad-14-stack-pin-policy-ad-entry
  baseline_commit: 32dcf47
---

# AD-14 Stack Pin Policy formal AD install DONE (cj-style 205번째)

cj-style 204 pre-existing 21 tsc errors cleanup sprint `32dcf47` 의
next-옵션 (d) "AD-14 install 단계 누락 detection 자동화 + tsc drift
detector (cj-style 204 cleanup sprint 발견 사항 follow-up)" 의 **부분
verbatim recovery** + cj-style 198 Epic 28 T2 frontend follow-up close-out
retro `0f01c66` 의 Phase 28 T2 frontend follow-up PRD entry `b847d34`
+ spec entry `a15f45b` 의 **"Recharts 2.12.7 AD-14 stack pin" + "Korean
font: `noto-sans-cjk-kr` (AD-14 stack pin)" + AD-49 ~ AD-57 의 100+
cross-reference** 의 formal AD 부재 정직 회복 결정 wire = **CR 11-3
honest-DEFER 98번째 epic 연속 정직 회복**.

## Verified actual scope (atomic single sprint)

**5 files = 3 NEW + 2 MODIFIED** (atomic single sprint 의 docs only 변경,
cj-style 200 wire cj-201 retro cj-202 retroactive cj-203 verification
cj-204 cleanup 의 5 files = 3 NEW + 2 MODIFIED 표준 verbatim mirror):

3 NEW:
1. `docs/architecture-decisions/AD-14-stack-pin-policy.md` (~+330 LOC,
   AD-8 / AD-11 / AD-49 ~ AD-55 format verbatim mirror):
   - **§Context** — AD-1 (Modular Monolith) + AD-8 (Money Types) +
     AD-15 (Cross-Language Conventions) + AD-22 (Owner-only RBAC)
     cold-start pinning layer + 100+ cross-reference 의 formal AD
     부재 정직 회복 + silent breakage table 5 scenarios (pydantic-core
     PYD-1 + sqlalchemy event-listener + recharts major bump +
     Dockerfile base image tag + pnpm install CI) + cj-style 197/202
     commit 메시지가 "Recharts 2.12.7 AD-14 stack pin" claimed 했으나
     install 단계 누락 → cj-style 204 cleanup sprint 에서 정직 회복
     verbatim.
   - **§Decision** — 6-tuple 강제: (1) pin the version (35 pins:
     .nvmrc / .python-version / package.json engines.node +
     packageManager / apps/web/package.json 5 deps + @types/*
     / apps/api/pyproject.toml 11 deps / packages/cost_engine
     pyproject.toml numpy + pytest / root pyproject.toml import-linter
     + pytest + ruff / Dockerfile 3 base images tags + digests /
     pnpm-lock.yaml + uv.lock / .github/workflows/ci.yml postgres:15
     + uv==0.11.32) + (2) lock the resolution (`--frozen-lockfile`) +
     (3) bump deliberately 3-step ([STACK BUMP] tag + V8 regression +
     CODEOWNER approval) + (4) CI gate fail-closed (`.github/workflows/
     ci.yml` lines 110-195 `stack-pin-check` job) + (5) exceptions
     block + retirement policy (NOTES-1) + (6) anti-patterns 5종
     (`^`/`~` 금지 + `latest` 금지 + silent bump 금지 + Dependabot
     auto-merge 금지 + `pnpm install` CI 금지).
   - **§Consequences** — positive 5종 (결정성 보장 + silent breakage
     방지 + cross-AD 일관성 + auditability + CODEOWNER enforcement)
     + negative 3종 (bump friction + exception debt + lockfile
     resolution drift) + mitigations 4종 (`bump_stack_pin.sh` helper
     + NOTES-1 ready-to-retire + V8 regression + `dep:check:verbose`).
   - **§Alternatives Considered** — 6 candidates (free dep / carets
     / Dependabot auto-merge / pin only without gate / digest only /
     runtime detection only) verbatim.
   - **§Detection Surface — install/runtime 검증 surface honestly
     reported** — 12 surface honestly reported per CR 11-3: 8 ✅
     functional (Node detector + Python detector (script) +
     regenerate_stack_pin.py + bump_stack_pin.sh +
     test_stack_pin_check.py + pnpm dep:check + pnpm test:stack-pin +
     make dep-check + make test-stack-pin + docs/STACK_PIN.{md,yaml})
     + 1 ⚠️ `k6-python-wrapper==0.1.0` phantom dep honestly DEFER
     (Python detector NOT runnable via `uv run`) + 3 partial (CI job
     PARTIAL + Dependabot auto-label 미검증 + AD-14 doc 부재 → THIS
     sprint 신규 install).
   - **§Cross-references** — AD-1/8/15/22/49~57 + CR 9-6/11-3 +
     CASCADE-1/DOCKER-2/MSG-1/MSG-2/SCHEMA-1 verbatim cross-reference.
   - **§Open Items** — D-AD-14-1 (k6-python-wrapper phantom dep
     honestly DEFER to cj-206+) + V8 regression suite (Story 4.4) +
     Dependabot auto-label wiring verification 미실시.
   - **§Notes** — cj-style 205 honest recovery + 5 CR lessons applied
     verbatim + 본 AD 의 SSOT 가 `docs/STACK_PIN.yaml` 이고
     `docs/STACK_PIN.md` 는 mirror 라는 사실 명시.

2. `_bmad-output/implementation-artifacts/commit-msg-cj-205.txt` (this
   file's commit message draft).
3. `memory/handoff-2026-08-29-cj-205-ad-14-stack-pin-policy-ad-entry-done.md`
   (this file).

2 MODIFIED:
1. `_bmad-output/implementation-artifacts/sprint-status.yaml` v4.05 →
   v4.06 EXTENSION (cj-205-ad-14-stack-pin-policy-ad-entry: backlog →
   done 신규 entry EXTENSION + cj-205-ad-14-stack-pin-policy-ad-entry-
   cycle: backlog → done 신규 entry EXTENSION + A810~A814 action_items
   신규 block 5 entries EXTENSION + last_updated_note_v4_06 신규).
2. `memory/MEMORY.md` (hook EXTENSION).

## cj-style 205 sprint 결정 wire — AD-14 install surface honestly reported

### Node detector functional ✅

`node scripts/check_stack_pin.mjs` 실행 결과:

```
[STACK_PIN] OK all 35 pins match
```

35 pins 모두 일치 — Node 측 stack pin install surface 100% functional
honestly reported 결정 wire 보존. cj-style 205 검증 시점의 8개 active
exception (next/react/typescript/pydantic/sqlalchemy/postgresql/
tailwind/structlog/opentelemetry_api) 모두 `current != spec` 상태로
NOTES-1 warning emit 보존.

### Python detector NOT runnable ⚠️ (D-AD-14-1 honestly DEFER)

`uv run python scripts/check_stack_pin.py` 실행 시:

```
× No solution found when resolving dependencies:
╰─▶ Because k6-python-wrapper was not found in the package registry and
    costmgr-api depends on k6-python-wrapper==0.1.0, we can conclude that
    costmgr-api's requirements are unsatisfiable.
    And because your workspace requires costmgr-api[dev], we can conclude
    that your workspace's requirements are unsatisfiable.
```

근본 원인:
- `apps/api/pyproject.toml:62` 선언: `k6-python-wrapper==0.1.0`
- `apps/api/core/load_test_runner.py:1-30` 은 subprocess 로 `k6` binary
  직접 invoke — `k6_python_wrapper` import 0건 (phantom dep)
- `uv.lock` 에 k6-python-wrapper 항목 0건 (declared != resolved drift)

→ **`uv sync --frozen` 가 fail** → CI `stack-pin-check` job 의 Python
detector step 도 동일하게 fail 가능성 → install surface 의 50% only
functional honestly reported.

**D-AD-14-1 신규 honestly DEFER (CR 11-3 honest-DEFER 98번째)** to
follow-up cj-206+ source sprint:
1. `apps/api/pyproject.toml:62` `k6-python-wrapper==0.1.0` 제거
2. `uv.lock` regenerate (`uv lock` + `uv sync --frozen`)
3. `uv run python scripts/check_stack_pin.py` verification — 35 pins
   match EXPECTED
4. CI `stack-pin-check` job PARTIAL → FULL functional honestly
   recovered verification

### Integration test ✅

`make test-stack-pin` 실행 시:
- `tests/integration/test_stack_pin_check.py` 4-case all PASS:
  - exit 0 on clean repo
  - exit 1 on apps/web/package.json next version drift
  - `[STACK BUMP]` / STACK_BUMP=1 authorizes drift, exit 0
  - drift output reports the drifted package name

→ integration test install surface 100% functional honestly reported
결정 wire 보존.

## D-DEFER-* honestly 결정 wire 보존 (cj-style 205 진입 결정 wire)

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
| **D-AD-14-1 (NEW)** | ⚠️ **honestly DEFER** | kjw | **cj-206+ source sprint 결정 wire 보류** |
| D-LAUNCH-1-DEFER-1 | honestly preserved 65~205번째 | kjw | 보존 |

## 3중 게이트 impact verification

| Gate | Result | Notes |
|---|---|---|
| T7.1 ruff scoped | ✅ N/A | apps/api 변경 0건 verified via `git diff --stat apps/api` |
| T7.2 pytest | ✅ N/A | no Python source changes |
| T7.3 vitest scoped | ✅ N/A | apps/web 변경 0건 verified via `git diff --stat apps/web` |
| T7.4 tsc | ✅ N/A | apps/web 변경 0건 |
| T7.5 3중 게이트 FINAL CLEAN | ✅ PASS | docs only 변경 = standard atomic docs-only sprint |
| Node detector | ✅ PASS | `pnpm dep:check` → `[STACK_PIN] OK all 35 pins match` |
| Python detector | ⚠️ NOT RUN | uv sync phantom dep fail → D-AD-14-1 honestly DEFER |
| Integration test | ✅ PASS | `make test-stack-pin` 4-case all PASS |

## Next 옵션 5종 결정 wire 보존

- (a) **D-AD-14-1 phantom dep removal source sprint 진입 결정 wire**
  (cj-style 206번째) — `apps/api/pyproject.toml:62` phantom dep 제거 +
  `uv.lock` regenerate + Python detector verification + CI `stack-pin-
  check` job PARTIAL → FULL functional honestly recovered
- (b) AD-14 install 단계 누락 detection 자동화 + tsc drift detector
  결정 wire (cj-style 204 cleanup sprint 발견 사항 follow-up)
- (c) Epic 29+ 진입 결정 wire
- (d) Layer 2 P1 + Layer 3 P2 + emit_audit_typed signature mismatch
  carry-over 결정 wire
- (e) D-DEFER-* follow-up 결정 wire 보류

## 결정 wire 일자

2026-08-29 (KST)

## Cross-references

- **본 cj-style sprint chain**: 1~205 모두 보존
- **Epic 1~17**: 모두 DONE 보존
- **Phase 3~28 + Phase 19.5 + Phase 20.5**: 모두 DONE 보존
- **audit-fixes sprint chain**: 5개 sprint chain ✅ ALL DONE 보존
- **1st release cycle**: DONE 보존
- **Phase 11~28 18-capability FinOps territory chain**: ✅ ALL WIRED INTEGRATED 보존
- **AD-50 ~ AD-57 + AD-58 (cj-203) + AD-59 (cj-203) + AD-60 (cj-204) EXTENSION 결정 wire 보존** + **AD-14 신규 install 결정 wire (cj-205)**
- **Capability matrix v1.36 → v1.53 EXTENSION chain ✅ PRESERVED** (19 EXTENSION steps 보존)
- **D-LAUNCH-1-DEFER-1 honestly preserved 65~205번째** 보존
- **A19 cohesion 9 surface EXTENSION PARTIAL preserved** (cj-style 205 AD install sprint 는 Surface 8 docs EXTENSION 만, 나머지 8 surface NO 변경)
- **CR 11-3 honest-DEFER 98번째 epic 연속 정직 회복** 결정 wire 보존
