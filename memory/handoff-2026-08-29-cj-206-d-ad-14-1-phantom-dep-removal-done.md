---
name: handoff-2026-08-29-cj-206-d-ad-14-1-phantom-dep-removal-done
description: D-AD-14-1 k6-python-wrapper phantom dep removal DONE (cj-style 206th). 7 files = 2 NEW + 5 MODIFIED atomic source-and-docs sprint. cj-205 가 honestly DEFER 한 phantom dependency 제거 + uv.lock regenerate (+518/-0) → AD-14 Python drift detector NOT runnable → functional 회복 (35 pins match exit 0). D-AD-14-2 신규 honestly DEFER (RetentionPolicy(dict) response_model FastAPIError pre-existing). CR 11-3 honest-DEFER 99번째 epic 연속 정직 회복.
metadata:
  type: project
  cycle: cj-style-206
  phase: d-ad-14-1-phantom-dep-removal
  baseline_commit: 2cb0027
---

# D-AD-14-1 phantom dep removal DONE (cj-style 206번째)

cj-style 205 AD-14 Stack Pin Policy formal AD install `2cb0027` 의
next-옵션 (a) "**D-AD-14-1 phantom dep removal source sprint 진입 결정
wire** (cj-style 206번째)" 의 **verbatim recovery**. cj-205 가 honestly
DEFER 한 `k6-python-wrapper==0.1.0` phantom dependency 를 다음 sprint
에서 즉시 회수 = **CR 11-3 honest-DEFER 99번째 epic 연속 정직 회복**.
관련: [[handoff-2026-08-29-cj-205-ad-14-stack-pin-policy-ad-entry-done]]

## Verified actual scope (atomic single sprint)

**7 files = 2 NEW + 5 MODIFIED** (source-and-docs sprint — cj-205 의
docs-only 5 files 표준에서 source 2건이 추가된 형태):

2 NEW:
1. `_bmad-output/implementation-artifacts/commit-msg-cj-206.txt`
2. `memory/handoff-2026-08-29-cj-206-d-ad-14-1-phantom-dep-removal-done.md`
   (this file)

5 MODIFIED:
1. `apps/api/pyproject.toml` (6 insertions / 3 deletions)
2. `uv.lock` (518 insertions / **0 deletions**)
3. `docs/architecture-decisions/AD-14-stack-pin-policy.md`
   (§Detection Surface + §Cross-references + §Open Items + §Notes)
4. `_bmad-output/implementation-artifacts/sprint-status.yaml`
   v4.06 → v4.07 EXTENSION (A815~A819 + last_updated_note_v4_07 +
   epic 14 action_items D-AD-14-1 open → done + D-AD-14-2 신규 open)
5. `memory/MEMORY.md` (hook EXTENSION)

## D-AD-14-1 ✅ RESOLVED — 근본 원인과 제거 근거

phantom 판정 근거 3종 (모두 실측):
- `apps/api/pyproject.toml:62` 에 `k6-python-wrapper==0.1.0` 선언
- 해당 패키지는 **PyPI 에 존재하지 않음** (`k6-python-wrapper was not
  found in the package registry`) → 애초에 설치된 적이 없음
- `apps/api/core/load_test_runner.py:65` 은
  `K6_BINARY = os.environ.get("K6_BINARY", "k6")` 로 stdlib
  `subprocess` 를 통해 k6 binary 를 직접 invoke — repo 전역
  `k6_python_wrapper` import **0건** (grep 검증)

기존 주석(`pyproject.toml:57-61`)은 "The `k6` Python wrapper below
provides subprocess orchestration for local dev + CI
(load_test_runner.py)" 라고 서술했으나 **사실이 아니었음** → 주석을
subprocess 사실 + D-AD-14-1 근거로 정정. k6 binary 버전 pin 은
`.github/workflows/load-test.yml` 의 `apt-get install k6=0.45.0`
레벨에서 계속 강제되므로 AD-14 §Decision 은 불변. **runtime 동작
변화 0건**.

## uv.lock regenerate — k6 1건보다 넓었던 drift

`uv lock` 결과 **518 insertions / 0 deletions**. deletions 0 이므로
**기존 pin 은 1건도 변경되지 않음** (ruff 0.7.0 / pytest 9.1.1 /
import-linter 2.13 / fastapi 0.139.2 / pydantic 2.11.9 / pydantic-core
2.33.2 / sqlalchemy 2.0.36 전부 불변 → RANGE-1 + PYD-1 보존).
따라서 pin bump 0건 = `[STACK BUMP]` tag 불필요.

추가 해결된 항목은 cj-205 시점에 이미 pyproject 에 declared 였으나
lock 에는 resolved 되지 않았던 drift (`costmgr-api` requires-dist
**lock 13 → 25**, dev extra 포함):
lxml 6.1.2 + opentelemetry-{api,sdk,exporter-otlp-proto-http,
instrumentation-{fastapi,sqlalchemy,httpx,asyncpg}} +
prometheus-client 0.20.0 + pyyaml 6.0.2 + python3-saml 1.16.0
(+ xmlsec 1.3.17 transitive) + jsonschema 4.23.0 + 나머지 transitive.

→ 본 sprint 는 k6 1건 뿐 아니라 **declared/resolved parity 자체를
회복** (AD-14 §Decision (2) "lock the resolution" 의 실질 회복).

## 검증 실측 (all local, honestly reported)

| 검증 | 결과 | 명령 / 근거 |
|---|---|---|
| **Python detector** | ✅ **회복** | `uv run python scripts/check_stack_pin.py` → `[STACK_PIN] Exceptions tracked: 9` + `[STACK_PIN] OK all 35 pins match`, exit 0 |
| Node detector | ✅ PASS | `node scripts/check_stack_pin.mjs` → 35 pins match, exit 0 |
| lock 무결성 | ✅ PASS | `uv lock` / `uv lock --check` / `uv sync --frozen` / `uv sync --frozen --all-packages` 모두 exit 0 (xmlsec 1.3.17 Windows 설치 성공) |
| Integration test | ✅ PASS | `tests/integration/test_stack_pin_check.py` **9 passed** |
| T7.1 ruff scoped | ✅ N/A | `.py` 변경 0건 (`ruff check apps/api` 전역 573 findings 는 전부 pre-existing, 본 sprint 무관) |
| T7.2 pytest | ✅ PASS (1 pre-existing FAIL) | `pytest tests/architecture tests/cost_engine` → **586 passed / 1 skipped / 1 failed** (D-AD-14-2) |
| T7.3 vitest scoped | ✅ N/A | apps/web 변경 0건 |
| T7.4 tsc | ✅ N/A | apps/web 변경 0건 |
| T7.5 FINAL CLEAN | ✅ PASS | pre-existing 1건 honestly carry-over |
| CI `stack-pin-check` job | ⚠️ **추정 (실측 아님)** | local 에서 CI 와 동일 시퀀스(`uv sync --frozen` → `uv run python scripts/check_stack_pin.py`) exit 0 회복 확인. **실제 CI run 은 다음 push 에서 확인** |

## D-AD-14-2 신규 honestly DEFER (CR 11-3 honest-DEFER 99번째)

`tests/architecture/test_api_calls_only_ports.py::
test_apps_api_has_no_unintended_dunder_imports_at_module_load` 가
**fastapi 설치 환경에서 pre-existing FAIL**.

- 원인: `apps/api/modules/audit/retention/retention_dsl.py:52` 의
  `class RetentionPolicy(dict)` 를
  `apps/api/modules/audit/retention/retention_routes.py:102` 가
  `response_model=` 으로 사용 → `fastapi.utils` `FastAPIError`
  (dict subclass 는 valid response field 아님) at `apps.api.main`
  import time
- 본 test 는 fastapi 미설치 시 `pytest.skip` 하며, CI 의
  `uv sync --frozen` 은 root dev group 15 packages 만 설치하므로
  CI 에서는 skip 되어 왔음 — cj-206 의
  `uv sync --frozen --all-packages` 환경에서 처음 표면화
- **무관함 증명**: `git stash` 로 본 sprint 변경 제거 후 동일 test
  재실행 → **동일 FAIL 재현** (baseline 에서도 FAIL)
- follow-up cj-207+ source sprint 에서 `RetentionPolicy` 를 pydantic
  `BaseModel` 로 승격하거나 `response_model` 제거 결정 wire 필요

## 별도 관찰 (sprint scope 외부, 정직 기록)

`_bmad-output/implementation-artifacts/sprint-status.yaml` 은 **HEAD
시점에도 PyYAML 로 parse 되지 않음** (line 536 `expected <block end>,
but found '?'`). 본 sprint 의 v4.07 EXTENSION 블록 자체는 격리 parse
로 OK 검증했으며, parse 실패는 HEAD 와 working tree 양쪽에서 동일하게
재현되는 **pre-existing** 상태 (본 sprint 무관). 향후 sprint 에서
sprint-status.yaml 을 기계 판독 대상으로 쓰려면 별도 회복 필요.

## D-DEFER-* honestly 결정 wire 보존 (cj-style 206 진입 결정 wire)

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
| **D-AD-14-1** | ✅ **RESOLVED (cj-206)** | kjw | **본 sprint** |
| **D-AD-14-2 (NEW)** | ⚠️ **honestly DEFER** | kjw | **cj-207+ source sprint 결정 wire 보류** |
| D-LAUNCH-1-DEFER-1 | honestly preserved 65~206번째 | kjw | 보존 |

## Next 옵션 5종 결정 wire 보존

- (a) **D-AD-14-2 retention `response_model` 회복 source sprint 진입
  결정 wire** (cj-style 207번째) — `RetentionPolicy(dict)` → pydantic
  `BaseModel` 승격 또는 `response_model` 제거 +
  `test_apps_api_has_no_unintended_dunder_imports_at_module_load`
  GREEN 회복
- (b) AD-14 install 단계 누락 detection 자동화 + tsc drift detector
  결정 wire (cj-style 204 cleanup sprint 발견 사항 follow-up)
- (c) CI `stack-pin-check` job FULL functional **실측** verification
  결정 wire (다음 push 후 — 본 sprint 는 추정까지만 기록)
- (d) Epic 29+ 진입 결정 wire
- (e) D-DEFER-* follow-up 결정 wire 보류

## 결정 wire 일자

2026-08-29 (KST)

## Cross-references

- **본 cj-style sprint chain**: 1~206 모두 보존
- **Epic 1~17**: 모두 DONE 보존
- **Phase 3~28 + Phase 19.5 + Phase 20.5**: 모두 DONE 보존
- **audit-fixes sprint chain**: 5개 sprint chain ✅ ALL DONE 보존
- **1st release cycle**: DONE 보존
- **Phase 11~28 18-capability FinOps territory chain**: ✅ ALL WIRED INTEGRATED 보존
- **AD-50 ~ AD-60 EXTENSION 결정 wire 보존** + **AD-14 Detection Surface EXTENSION (cj-206)**
- **Capability matrix v1.36 → v1.53 EXTENSION chain ✅ PRESERVED** (19 EXTENSION steps 보존)
- **D-LAUNCH-1-DEFER-1 honestly preserved 65~206번째** 보존
- **A19 cohesion 9 surface EXTENSION PARTIAL preserved** (cj-style 206 은 Surface 8 docs EXTENSION + build/dep surface 만, 나머지 NO 변경)
- **CR 11-3 honest-DEFER 99번째 epic 연속 정직 회복** 결정 wire 보존
