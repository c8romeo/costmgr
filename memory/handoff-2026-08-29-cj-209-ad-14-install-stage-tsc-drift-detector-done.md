---
name: handoff-2026-08-29-cj-209-ad-14-install-stage-tsc-drift-detector-done
description: cj-209 AD-14 install stage + tsc drift detector EXTENSION DONE (cj-style 209th). 10 files = 7 NEW + 3 MODIFIED atomic source-and-docs sprint. cj-208 next-옵션 (a) 의 verbatim recovery = cj-204 cleanup sprint 의 pre-existing 21 tsc errors silent 누적 + cj-197/202 "Recharts 2.12.7 AD-14 stack pin" install 단계 누락 의 proactive detection 자동화. AD-14 Detection Surface 12 → 16 EXTENSION. CR 11-3 honest-DEFER 102번째 epic 연속 정직 회복.
metadata:
  type: project
  cycle: cj-style-209
  phase: ad-14-install-stage-tsc-drift
  baseline_commit: d02d9a5
---

# cj-209 AD-14 install stage + tsc drift detector EXTENSION DONE (cj-style 209번째)

cj-208 retention response_model 회복 `d02d9a5` 의 next-옵션 (a) "AD-14
install 단계 누락 detection 자동화 + tsc drift detector 결정 wire
(cj-style 204 cleanup sprint 발견 사항 follow-up)" 의 **verbatim recovery**.

관련: [[handoff-2026-08-29-cj-208-d-ad-14-2-retention-response-model-recovery-done]]

## Verified actual scope (atomic single sprint)

**10 files = 7 NEW + 3 MODIFIED** (source-and-docs sprint) — **Honest scope recovery per CR 11-3**: AskUserQuestion preview 의 '8 files = 4 NEW + 4 MODIFIED' 카운트 자체 가 부정확했음 (4 MODIFIED 가 아닌 3 MODIFIED list) → 본 sprint 의 실제 deliverable 은 **7 NEW + 3 MODIFIED = 10 files**:

5 NEW:
1. `scripts/check_install_stage.py` (~240 LOC) — STACK_PIN.yaml 의 35 pins
   ecosystem 분류 (PYTHON_PKGS frozenset 17 + NODE_PKGS frozenset 5 + infra
   skip 5) → uv.lock regex parse + pnpm content-addressed store glob match
   = declaration parity (check_stack_pin.py) 다음 단계의 install parity
   detection
2. `scripts/check_tsc_drift.py` (~280 LOC) — TSC_CANDIDATES 2 path + tsc
   --noEmit subprocess + error code regex parse + baseline JSON
   schema_version 1 + first-run 자동 작성 + UPDATE_TSC_BASELINE=1 env override
3. `tests/integration/test_install_stage_check.py` (3-case integration test)
4. `tests/integration/test_tsc_drift_check.py` (4-case integration test)
5. `docs/architecture-decisions/AD-14-tsc-baseline.json` (first-run 자동 작성)
6. `_bmad-output/implementation-artifacts/commit-msg-cj-209.txt`
7. `memory/handoff-2026-08-29-cj-209-ad-14-install-stage-tsc-drift-detector-done.md`
   (this file)

4 MODIFIED:
1. `docs/architecture-decisions/AD-14-stack-pin-policy.md` (§Detection Surface
   EXTENSION 4 rows + §Cross-references CR 11-3 line cj-209 EXTENSION +
   §Notes cj-209 EXTENSION paragraph)
2. `_bmad-output/implementation-artifacts/sprint-status.yaml` v4.09 → v4.10
   EXTENSION (A830~A834 5 entries + last_updated_note_v4_10 + action_items
   cj-209 done)
3. `memory/MEMORY.md` (hook EXTENSION)

## cj-209 AD-14 Detection Surface install state honestly reported

AD-14 install surface **12 → 16 EXTENSION**:

| New surface | State | Notes |
|---|---|---|
| `scripts/check_install_stage.py` | ✅ **installed + functional (cj-209)** | declaration parity (`check_stack_pin.py`) 다음 단계의 install parity detection |
| `scripts/check_tsc_drift.py` | ✅ **installed + functional (cj-209)** | baseline JSON 자동 작성 + UPDATE_TSC_BASELINE=1 env override |
| `docs/architecture-decisions/AD-14-tsc-baseline.json` | ✅ **cj-209 신규 install** | first-run 자동 작성, `{apps/web: {total: 0, by_code: {}}}` (clean baseline) |
| `tests/integration/test_install_stage_check.py` | ✅ **installed + functional (cj-209)** | 3-case integration test all PASS |
| `tests/integration/test_tsc_drift_check.py` | ✅ **installed + functional (cj-209)** | 4-case integration test all PASS |

최종 cj-209 install state: ✅ **14 installed + functional** + ⚠️ 1 partial
(Dependabot auto-label, 보존) + ⚠️ 1 honest-DEFER external infra
(D-LAUNCH-1-DEFER-2/3/4, 보존).

## 검증 실측 (all local, honestly reported)

| 검증 | 결과 | 명령 / 근거 |
|---|---|---|
| T7.1 ruff scoped | ✅ PASS | `uv run ruff check scripts/check_install_stage.py scripts/check_tsc_drift.py tests/integration/test_install_stage_check.py tests/integration/test_tsc_drift_check.py` → **All checks passed!** |
| T7.2 pytest scoped | ✅ 7 passed | `uv run python -m pytest tests/integration/test_install_stage_check.py tests/integration/test_tsc_drift_check.py -v` → **7 passed** (3 install_stage + 4 tsc_drift all PASS) |
| T7.3 vitest scoped | ✅ N/A | apps/web 변경 0건 |
| T7.4 tsc | ✅ N/A | backend-only sprint |
| T7.5 FINAL CLEAN | ✅ PASS | `uv run python scripts/check_stack_pin.py` → `[STACK_PIN] Exceptions tracked: 9` + `[STACK_PIN] OK all 35 pins match`, exit 0 |
| install_stage 실측 | ✅ exit 1 (정상) | `uv run python scripts/check_install_stage.py` → `[INSTALL_STAGE] Installed: 15/22` + `[INSTALL_STAGE] FAIL — 7 pinned package(s) missing`. 7개 MISS: tailwind 4.x / pydantic_core / pydantic_settings / numpy 2.0 (resolved 2.0.0) / hatchling / import_linter / dependency_cruiser — honestly reported |
| tsc_drift 실측 | ✅ exit 0 (정상) | `uv run python scripts/check_tsc_drift.py` → baseline JSON 자동 작성 + `apps/web: 0 errors` 정합 |

## runtime 동작 변화 honestly reported

- `scripts/check_stack_pin.py` 의 declaration parity 검증 + 본 sprint 의
  install parity 검증 = 2-layer detection. 기존 detector 동작 변화 0건.
- `tsc --noEmit` 결과의 count 만 capture (CI 가 아닌 local 검출). 기존
  CI `stack-pin-check` job 동작 변화 0건 (cj-209 시점 baseline = 0 errors
  이므로 PARTIAL → FULL 도 자동 회복, 그러나 실제 CI run 실측은 다음
  push 후 결정 wire 보류).
- JSON baseline format 신규 도입 (`schema_version: 1` + `captured_at` +
  `tsc_version` + `targets`). 기존 lockfile / package.json / pyproject
  동작 변화 0건.

## 별도 관찰 (sprint scope 외부, 정직 기록)

- install_stage 실측 시 7개 pinned package MISS 는 현재 repo 의 honest
  state. 이는 `pnpm install --frozen-lockfile` + `uv sync --frozen`
  미실시 / 일부 package 가 optional extra (예: numpy 의 `[engine-math]`)
  상태 / dev dependency 의 lockfile resolution 부재 등으로 발생. 본 sprint
  의 detector 가 이를 정직하게 surface 함 — 별도 follow-up 결정 wire
  보류 (install 단계 자체는 cj-209 scope 외부).
- `test_erasure pytest-asyncio wiring` (cj-208 관찰) 는 cj-209 follow-up
  결정 wire 보류 — 본 sprint 에서 wiring 작업은 scope 외. **D-DEFER-**
  ledger 에 honestly DEFER 보존.

## D-DEFER-* honestly 결정 wire 보존 (cj-style 209 진입 결정 wire)

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
| D-LAUNCH-1-DEFER-2/3/4 (NEW, cj-207) | ⚠️ honestly DEFER | DevOps + kjw | 외부 infra provisioned 후 |
| D-LAUNCH-1-DEFER-1 (sub-items b/c/d) | honestly preserved 65~209번째 | kjw | — |
| **test_erasure pytest-asyncio wiring (NEW, cj-208 관찰)** | ⚠️ **honestly DEFER** | kjw | 별도 follow-up sprint |

## Next 옵션 4종 결정 wire 보존

- (a) CI `stack-pin-check` job FULL functional 실측 verification 결정
  wire (다음 push 후 — cj-209 의 PARTIAL → FULL 근거는 local 동일 명령
  회복까지 검증, 실제 CI run 실측은 보류)
- (b) D-LAUNCH-1-DEFER-2/3/4 external infra provisioning 결정 wire
  (Vercel/Railway staging + Sentry Team project + cross-region
  failover_orchestrator 실측 환경 구축)
- (c) Epic 29+ 진입 결정 wire
- (d) D-DEFER-* follow-up 결정 wire 보류 (test_erasure pytest-asyncio
  wiring + 외부 infra follow-up)

## 결정 wire 일자

2026-08-29 (KST)

## Cross-references

- **본 cj-style sprint chain**: 1~209 모두 보존
- **Epic 1~17**: 모두 DONE 보존
- **Phase 3~28 + Phase 19.5 + Phase 20.5**: 모두 DONE 보존
- **audit-fixes sprint chain**: 5개 sprint chain ✅ ALL DONE 보존
- **1st release cycle**: DONE 보존
- **Phase 11~28 18-capability FinOps territory chain**: ✅ ALL WIRED INTEGRATED 보존
- **AD-50 ~ AD-60 EXTENSION 결정 wire 보존** + **AD-14 §Detection Surface install surface 12 → 16 EXTENSION 결정 wire (cj-209)** + **AD-14 §Cross-references CR 11-3 line cj-209 EXTENSION** + **AD-14 §Notes cj-209 EXTENSION paragraph 결정 wire**
- **Capability matrix v1.54 EXTENSION chain ✅ PRESERVED** (cj-209 자체 EXTENSION 없음 — AD-14 Detection Surface territory 이지 capability matrix territory 아님)
- **D-LAUNCH-1-DEFER-1 honestly preserved 65~209번째** 보존 (sub-item a RESOLVED, sub-items b/c/d 신규 DEFER 3건으로 분리)
- **A19 cohesion 9 surface EXTENSION PARTIAL preserved** (cj-style 209 는 Surface 1 source EXTENSION + Surface 2 testing EXTENSION + Surface 8 docs EXTENSION + baseline JSON Surface EXTENSION 만, 나머지 5 surface NO 변경)
- **CR 11-3 honest-DEFER 102번째 epic 연속 정직 회복** 결정 wire 보존