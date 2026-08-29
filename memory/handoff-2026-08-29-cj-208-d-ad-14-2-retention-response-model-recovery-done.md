---
name: handoff-2026-08-29-cj-208-d-ad-14-2-retention-response-model-recovery-done
description: D-AD-14-2 retention response_model 회복 source sprint DONE (cj-style 208th). 5 files = 2 NEW + 3 MODIFIED atomic source-and-docs sprint. cj-206 honestly DEFER 한 retention source defect (RetentionPolicy(dict) 를 response_model= 으로 사용 → FastAPIError at apps.api.main import time) 를 honestly minimum wire 로 회수 = kernel RetentionPolicy(dict) 보존 + API surface RetentionPolicyResponse(BaseModel) 신규 도입 + 3개 route handler wrap + 6 NEW pytest 결정 wire + AD-14 EXTENSION 결정 wire = architecture test GREEN 회복 (cj-206 FAIL → cj-208 23/23 PASS). CR 11-3 honest-DEFER 101번째 epic 연속 정직 회복.
metadata:
  type: project
  cycle: cj-style-208
  phase: d-ad-14-2-retention-response-model
  baseline_commit: f534ba6
---

# D-AD-14-2 retention response_model 회복 DONE (cj-style 208번째)

cj-style 207 LAUNCH_MONITORING sub-item (a) staging smoke_test wire
`f534ba6` 의 next-옵션 (a) **D-AD-14-2 retention `response_model` 회복
source sprint 진입 결정 wire** (cj-style 208번째) 의 **verbatim recovery**.
cj-206 이 honestly DEFER 한 retention source defect 를 즉시 회수 =
**CR 11-3 honest-DEFER 101번째** epic 연속 정직 회복.

관련: [[handoff-2026-08-29-cj-207-d-launch-1-defer-1-staging-smoke-test-done]]
+ [[handoff-2026-08-29-cj-206-d-ad-14-1-phantom-dep-removal-done]]

## Verified actual scope (atomic single sprint)

**5 files = 2 NEW + 3 MODIFIED** (source-and-docs sprint):

2 NEW:
1. `_bmad-output/implementation-artifacts/commit-msg-cj-208.txt`
2. `tests/api/modules/audit/retention/test_retention_routes.py` (~130 LOC,
   6 NEW pytest cases)
3. `memory/handoff-2026-08-29-cj-208-d-ad-14-2-retention-response-model-recovery-done.md`
   (this file)

3 MODIFIED:
1. `apps/api/modules/audit/retention/retention_routes.py` (+56/-16) —
   `RetentionPolicyResponse(BaseModel)` 신규 도입 + GET/POST/PUT 3개
   route handler 의 response_model swap + unused `RetentionPolicy`
   import 제거
2. `docs/architecture-decisions/AD-14-stack-pin-policy.md`
   (§Open Items D-AD-14-2 RESOLVED + §Detection Surface EXTENSION +
   §Cross-references CR 11-3 line RESOLVED 반영 + §Notes cj-208
   EXTENSION paragraph)
3. `_bmad-output/implementation-artifacts/sprint-status.yaml`
   v4.08 → v4.09 EXTENSION (A825~A829 + last_updated_note_v4_09 +
   action_items D-AD-14-2 status: open → done)
4. `memory/MEMORY.md` (hook EXTENSION)

## D-AD-14-2 ✅ RESOLVED — fix wire 결정

원인 (cj-206 baseline repro, cj-208 baseline 재검증):
- `apps/api/modules/audit/retention/retention_dsl.py:52` 의
  `class RetentionPolicy(dict)` 를
  `retention_routes.py:102/118/133` 가 `response_model=` 으로 사용
- `fastapi.utils` `FastAPIError: Invalid args for response field!
  Hint: check that <class 'apps.api.modules.audit.retention.
  retention_dsl.RetentionPolicy'> is a valid Pydantic field type.`
  at `apps.api.main` import time
- `tests/architecture/test_api_calls_only_ports.py::
  test_apps_api_has_no_unintended_dunder_imports_at_module_load`
  fastapi 설치 환경에서 pre-existing FAIL (cj-206 `git stash`
  baseline 재현으로 본 sprint 무관함 증명)

fix wire (honest boundary):

1. **kernel `RetentionPolicy(dict)` 보존** — pure-functional
   `retain()` / `parse_retention_policy()` 의 return type 변경 0건.
   기존 16 kernel tests (`tests/api/modules/audit/retention/
   test_retention_dsl.py`) 의 `policy["action_class"]` access
   pattern 무변경 → CR 12-5 D-PARITY-01 inversion (kernel purity)
   보존.

2. **API surface `RetentionPolicyResponse(BaseModel)` 신규 도입**
   — `apps/api/modules/audit/retention/retention_routes.py` 에 전용
   Pydantic BaseModel 결정 wire (5 fields: tenant_id: str +
   action_class: RetentionClass Literal + days: int + archive: bool +
   mask_pii: bool). JSON shape 이 kernel dict 와 verbatim 동일 →
   CR 12-5 D-PARITY-01 Python ↔ TypeScript parity 손상 없음.

3. **3개 route 의 `response_model=` swap** — GET single +
   POST create + PUT update 의 `response_model=RetentionPolicy` →
   `response_model=RetentionPolicyResponse` + 각 handler 의
   `parse_retention_policy(...)` 결과를
   `RetentionPolicyResponse(**result)` 로 wrap. function return
   type annotation 도 `-> RetentionPolicyResponse` 변경.

4. **unused `RetentionPolicy` import 제거** — retention_routes.py
   의 `RetentionPolicy` import 는 더 이상 직접 사용되지 않음 (kernel
   모듈 re-export 자체는 `__init__.py` 에서 보존).

5. **`tests/api/modules/audit/retention/test_retention_routes.py`
   NEW 6 pytest cases** —
   - TestRetentionPolicyResponseShape: field set matches kernel +
     field types match (Literal action_class 검증 포함)
   - TestRetentionPolicyResponseRoundTrip: parse → Response round-trip
     preserves 5 fields + model_dump() JSON shape 동등 + 4-class
     default days round-trip
   - TestImportAppsApiMainRegressionGuard: import apps.api.main
     회귀 방지 (D-AD-14-2 재발 방지)

## 검증 실측 (all local, honestly reported)

| 검증 | 결과 | 명령 / 근거 |
|---|---|---|
| **import smoke** | ✅ PASS | `uv run python -c "import apps.api.main"` → `import OK` (cj-206 baseline 에서 `FastAPIError` raise → 본 sprint 회복) |
| **architecture test** | ✅ PASS (GREEN 회복) | `uv run python -m pytest tests/architecture/test_api_calls_only_ports.py::test_apps_api_has_no_unintended_dunder_imports_at_module_load` → **1 passed** (cj-206 의 1 failed → 본 sprint GREEN) |
| **kernel tests** | ✅ PASS (16/16 무변경) | `uv run python -m pytest tests/api/modules/audit/retention/test_retention_dsl.py` → 16 passed (kernel `RetentionPolicy(dict)` 보존, `["key"]` access pattern 무변경) |
| **NEW response tests** | ✅ PASS (6/6) | `uv run python -m pytest tests/api/modules/audit/retention/test_retention_routes.py` → 6 passed |
| **retention+architecture 합산** | ✅ PASS (23/23) | `uv run python -m pytest tests/api/modules/audit/retention/ "tests/architecture/test_api_calls_only_ports.py::test_apps_api_has_no_unintended_dunder_imports_at_module_load"` → **23 passed** |
| **T7.1 ruff scoped** | ✅ PASS | `ruff check apps/api/modules/audit/retention/retention_routes.py tests/api/modules/audit/retention/test_retention_routes.py` → All checks passed! |
| **T7.2 pytest scoped (cj-206 parity)** | ✅ PASS (1 up) | `pytest tests/architecture tests/cost_engine` → **587 passed / 1 skipped** (cj-206 의 586 passed / 1 skipped / **1 failed** → 본 sprint **+1 architecture test GREEN 회복** = 587/587) |
| **T7.3 vitest scoped** | ✅ N/A | `apps/web` 변경 0건 (`git status --short` confirmed) |
| **T7.4 tsc** | ✅ N/A | `apps/web` 변경 0건 |
| **T7.5 FINAL CLEAN** | ✅ PASS | `uv run python scripts/check_stack_pin.py` → `[STACK_PIN] Exceptions tracked: 9` + `[STACK_PIN] OK all 35 pins match`, exit 0 (cj-206 의 functional 회복 상태 verbatim 보존) |

## runtime 동작 변화 honestly reported

- JSON wire-format 변경 **0건** — 5 field shape verbatim 보존
  (TS mirror parity CR 12-5 D-PARITY-01 손상 없음).
- HTTP response status code 변경 **0건** (201/200/204 그대로).
- OpenAPI schema 변경: response_model 명세에 `RetentionPolicyResponse`
  가 노출됨 (이전엔 `RetentionPolicy(dict)` 로 FastAPI 가 거부 →
  OpenAPI schema 자체에 retention CRUD endpoint 가 **등재되지
  못하던 상태** → 본 sprint 로 정상 등재). 이 변경은 OpenAPI
  schema 정확성 회복이며 runtime client 동작에는 영향 없음
  (JSON 응답 본문 verbatim 동일).

## 별도 관찰 (sprint scope 외부, 정직 기록)

`tests/api/modules/audit/retention/test_erasure.py` 의 6개
`TestRequestAuditLogErasure` 케이스가 **pre-existing FAIL**
(`async def functions are not natively supported — pytest-asyncio
plugin 필요`). 본 sprint 변경과 무관함 — `git stash` baseline 에서
동일 FAIL 재현됨 (cj-208 sprint scope 는 `apps/api/modules/audit/
retention/retention_routes.py` 1 MODIFIED + `test_retention_routes.py`
1 NEW 만, `test_erasure.py` 무수정). cj-208+ follow-up sprint 에서
pytest-asyncio wiring 결정 wire 보류 (별도 DEFER ledger 후보).

`_bmad-output/implementation-artifacts/sprint-status.yaml` 자체는
HEAD 시점에도 PyYAML parse 실패 (cj-206 관찰 verbatim 보존). 본
sprint 의 v4.09 EXTENSION 블록 자체는 격리 parse OK 검증, parse
실패는 HEAD/working tree 양쪽 동일 재현되는 pre-existing.

## D-DEFER-* honestly 결정 wire 보존 (cj-style 208 진입 결정 wire)

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
| **D-AD-14-2 (NEW, cj-206)** | ✅ **RESOLVED (cj-208)** | kjw | **본 sprint** |
| D-LAUNCH-1-DEFER-1 (sub-item a) | ✅ RESOLVED (cj-207) | kjw | cj-207 source sprint |
| D-LAUNCH-1-DEFER-2/3/4 (NEW, cj-207) | ⚠️ honestly DEFER | DevOps + kjw | 외부 infra provisioned 후 |
| D-LAUNCH-1-DEFER-1 (sub-items b/c/d) | honestly preserved 65~208번째 | kjw | — |
| test_erasure pytest-asyncio wiring | ⚠️ honestly DEFER (cj-208 관찰) | kjw | 별도 follow-up sprint |

## Next 옵션 5종 결정 wire 보존

- (a) AD-14 install 단계 누락 detection 자동화 + tsc drift detector
  결정 wire (cj-style 204 cleanup sprint 발견 사항 follow-up)
- (b) CI `stack-pin-check` job FULL functional **실측** verification
  결정 wire (다음 push 후 — cj-206 의 PARTIAL → FULL 근거는 local
  동일 명령 회복까지 검증, 실제 CI run 실측은 보류)
- (c) D-LAUNCH-1-DEFER-2/3/4 external infra provisioning 결정 wire
  (Vercel/Railway staging + Sentry Team project + cross-region
  failover_orchestrator 실측 환경 구축)
- (d) Epic 29+ 진입 결정 wire
- (e) D-DEFER-* follow-up 결정 wire 보류 (test_erasure pytest-asyncio
  wiring 포함)

## 결정 wire 일자

2026-08-29 (KST)

## Cross-references

- **본 cj-style sprint chain**: 1~208 모두 보존
- **Epic 1~17**: 모두 DONE 보존
- **Phase 3~28 + Phase 19.5 + Phase 20.5**: 모두 DONE 보존
- **audit-fixes sprint chain**: 5개 sprint chain ✅ ALL DONE 보존
- **1st release cycle**: DONE 보존
- **Phase 11~28 18-capability FinOps territory chain**: ✅ ALL WIRED INTEGRATED 보존
- **AD-50 ~ AD-60 EXTENSION 결정 wire 보존** + **AD-14 Open Items + Detection Surface + Notes EXTENSION (cj-208)** + **AD-14 Cross-references CR 11-3 line RESOLVED 반영 (cj-208)**
- **Capability matrix v1.36 → v1.54 EXTENSION chain ✅ PRESERVED** (cj-208 자체 EXTENSION 없음 — D-AD-14-2 는 AD-14 territory 결정 wire 이지 capability matrix territory 아님)
- **D-LAUNCH-1-DEFER-1 honestly preserved 65~208번째** (sub-item a RESOLVED, sub-items b/c/d 신규 DEFER 3건으로 분리)
- **A19 cohesion 9 surface EXTENSION PARTIAL preserved** (cj-style 208 은 Surface 1 source EXTENSION + Surface 7 docs EXTENSION 만, 나머지 7 surface NO 변경)
- **CR 11-3 honest-DEFER 101번째 epic 연속 정직 회복** 결정 wire 보존
- **CR 12-5 D-PARITY-01 inversion 손상 없음**: kernel RetentionPolicy(dict) 보존 + RetentionPolicyResponse(BaseModel) JSON shape 5 field verbatim 동일 → TS mirror `apps/web/lib/audit/audit-log-retention-client.ts` `RetentionPolicy` interface 와 parity 결정 wire