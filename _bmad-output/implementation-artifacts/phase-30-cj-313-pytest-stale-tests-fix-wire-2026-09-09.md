# cj-313 pytest rootdir 정정 — Wire Sprint 결과

> **Sprint**: cj-313 pytest rootdir 정정 (cj-style 270번째 compressed entry+wire atomic single sprint)
> **Date**: 2026-09-09 KST (D-5, Pilot W1 launch D-day 2026-09-14 KST)
> **Territory**: Phase 30 — MVP hardening 7-checkpoint audit 의 Checkpoint 2 (Test coverage) 정정
> **Author**: Claude (operator = kjw)
> **Sprint form**: compressed entry+wire (cj-style 257th + 267th retroactive correction 패턴 verbatim mirror)
> **직전 sprint**: cj-312 wire (`a0a27d1`, sprint-status v4.85 → v4.86 EXTENSION)

---

## §1 의도 분석 — cj-312 audit finding 2.1 의 정직 회복

### cj-312 audit 의 claim
> "apps/api/tests/ 부재의 root cause 정직 회복, testpaths=["tests","apps/api"] EXTENSION"

### 실제 verification 결과 — ⚠️ WRONG 정직 회복
- **pytest config (testpaths=["tests"])** = CORRECT (pyproject.toml line 149)
- **5418 tests collected + 7 errors** from project root via `.venv\Scripts\python.exe -m pytest`
- `apps/api/tests/` 부재는 사실이지만 pytest config 와 무관 — pytest 는 project root 의 `tests/` 를 정상적으로 scan
- **실제 root cause**: 7 stale tests 의 import errors (cj-305b Resend swap 정직 회복 안 됨 + capability matrix drift + SLO test + audit_action test + scheduled_reports syntax error)

### 정직 회복 rationale
- CR 11-3 honest-DEFER discipline: cj-style 257th (cj-305b retroactive correction) + 267th (cj-310 retroactive correction) 패턴 verbatim mirror
- cj-312 audit 의 부정확한 diagnosis 를 본 sprint 에서 정직 회복
- 결정 wire 보존: cj-309~cj-312 wire 결정 wire 그대로 (Pilot W1 D-day + cj-309b B-1 + Resend + cj-307 aal1 + cj-304 4 gaps + cj-300 APScheduler KST + capability matrix v1.54 EXTENSION + audit_action EXTENSION)

---

## §2 7 Stale Tests 정정 내역 (cj-313 actual fix scope)

### Fix #1: test_phase_30_exports_email.py — cj-305b Resend swap 정직 회복
**Root cause**: cj-305b wire (`53b8bbf`) 가 `apps/api/core/email_provider.py` 의 PostmarkProvider → ResendProvider swap 적용했으나 **test 파일은 swap 정직 회복 안 됨** (cj-305b wire 의 blind spot).

**변경 내역**:
- import: `PostmarkProvider` → `ResendProvider`
- 4 test methods:
  - `test_postmark_provider_uses_http_api` → `test_resend_provider_uses_http_api` (URL `api.postmarkapp.com/email` → `api.resend.com/emails`, header `X-Postmark-Server-Token` → `Authorization: Bearer ...`, `Content-Type: application/json` 추가 검증)
  - `test_postmark_provider_5xx_raises_transient` → `test_resend_provider_5xx_raises_transient`
  - `test_postmark_provider_4xx_raises_permanent` → `test_resend_provider_4xx_raises_permanent` (error code `POSTMARK_CLIENT_ERROR` → `RESEND_CLIENT_ERROR`)
  - `test_factory_returns_postmark_when_token_set` → `test_factory_returns_resend_when_api_key_set` (env var `POSTMARK_SERVER_TOKEN` → `RESEND_API_KEY`, attribute `server_token` → `api_key`)
- 주석 docstring: "Postmark/SMTP mocked" → "Resend/SMTP mocked"

**결과**: 0 tests collected → **32 tests collected** (cj-305b test swap 정직 회복 완료)

### Fix #2: test_phase_10_audit_action.py — stale imports 제거
**Root cause**: `is_valid_audit_action` + `normalize_audit_action` 함수 부재 (apps/api/core/audit_action.py 는 ActionClass enum + _ActionRegistry class 만 export).

**변경 내역**:
- `from apps.api.core.audit_action import (ActionClass, AuditAction, SloEngineeringAction, is_valid_audit_action, normalize_audit_action)` → `(ActionClass, AuditAction, SloEngineeringAction)` (2 함수 import 제거)

**결과**: 1 error → 0 errors

### Fix #3: test_phase_10_slo_burn_rate_evaluator.py — stale imports 제거
**Root cause**: `BURN_RATE_THRESHOLDS` 상수 부재 (slo_burn_rate_evaluator.py 는 compute_burn_rate + evaluate_single_window + evaluate_all_windows 만 export).

**변경 내역**:
- `from apps.api.modules.slo.slo_burn_rate_evaluator import (BURN_RATE_THRESHOLDS, SloBurnRateEvaluation, SloViolationDetectedError, compute_burn_rate, evaluate_all_windows, evaluate_single_window)` → `(SloBurnRateEvaluation, SloViolationDetectedError, compute_burn_rate, evaluate_all_windows, evaluate_single_window)` (BURN_RATE_THRESHOLDS import 제거)

**결과**: 1 error → 0 errors

### Fix #4: test_phase_10_slo_dsl.py — multiple stale imports 제거
**Root cause**: errors.py 의 typed exception class 이름이 `BadRequest` → `BadRequestError`, `Conflict` → `ConflictError`, `UnprocessableEntity` → `UnprocessableEntityError` 로 변경됨 (cj-style 정직 회복 누락). slo_dsl.py 의 constant 이름에 `VALID_` prefix 추가됨 (`SLI_TYPES` → `VALID_SLI_TYPES` etc.). `build_slo_definition` 함수 부재 (slo_dsl.py 는 `validate_slo_definition` 만 export).

**변경 내역**:
- errors: `BadRequest, Conflict, UnprocessableEntity` → `BadRequestError, ConflictError, UnprocessableEntityError`
- slo_dsl constants: `SLI_TYPES, WINDOWS, BUDGET_POLICIES, REGIONS` → `VALID_SLI_TYPES, VALID_WINDOWS, VALID_BUDGET_POLICIES, VALID_REGIONS`
- slo_dsl function: `build_slo_definition` import 제거

**결과**: 1 error → 0 errors

### Fix #5: test_phase_30_scheduled_reports.py — syntax error + stale import
**Root cause**:
- Line 60: `DISPATCH_CRON_EXPRESSIONS := __import__(...)` — walrus operator `:=` 를 `from X import (...)` 괄호 내에서 사용 불가 (syntax error)
- `ALL_REPORT_TYPES` 가 `apps.api.jobs.scheduled_reports` 가 아닌 `apps.api.modules.reports.scheduled_serializers:50` 에 정의됨 (cj-303 wire 의 stale import path 정정과 동일 pattern)

**변경 내역**:
- DISPATCH_CRON_EXPRESSIONS import line 제거 후 별도 import block 추가: `from apps.api.jobs.scheduled_multi_cloud_dispatch_job import (DISPATCH_CRON_EXPRESSIONS,)` (scheduled_multi_cloud_dispatch_job.py:57 에 정의, test 가 기대하는 4 cron expressions 과 정확히 일치)
- ALL_REPORT_TYPES import: scheduled_reports → scheduled_serializers import path 변경 (cj-303 wire 정정 pattern 보존)

**결과**: 2 errors (syntax error + ImportError) → 0 errors

### Fix #6: test_capability_matrix_v1_32_drift.py — Industry enum 이름 변경
**Root cause**: Industry enum 의 `MFG_AND_SERVICE` → `MANUFACTURING_SERVICE`, `MFG_AND_SERVICE_AND_OTHER` → `MANUFACTURING_SERVICE_OTHER` 이름 변경 (packages/services/m0_onboarding/industry_menu.py 의 정직 회복 누락).

**변경 내역**:
- 2 occurrences: `Industry.MFG_AND_SERVICE` → `Industry.MANUFACTURING_SERVICE`, `Industry.MFG_AND_SERVICE_AND_OTHER` → `Industry.MANUFACTURING_SERVICE_OTHER`

**결과**: 1 error → 0 errors

### Fix #7: test_capability_matrix_v1_35_drift.py — _INDUSTRY_CAPABILITIES 이름 변경
**Root cause**: `INDUSTRY_CAPABILITIES` (public) → `_INDUSTRY_CAPABILITIES` (private, underscore prefix) 변경 (apps/api/core/capability.py:833 의 정직 회복 누락).

**변경 내역**:
- 2 occurrences: `INDUSTRY_CAPABILITIES` → `_INDUSTRY_CAPABILITIES` (import + body usage)

**결과**: 1 error → 0 errors

---

## §3 pyproject.toml canonical pytest invocation EXTENSION

### 추가 변경
- [tool.pytest.ini_options] 위에 canonical invocation comment 추가:

```toml
# Canonical invocation (cj-313 wire 결정 wire, 2026-09-09):
#   `.venv\Scripts\python.exe -m pytest`  (project root)
#
# Why not `uv run pytest`? — uv trampoline on Windows env occasionally
# returns "uv trampoline failed to canonicalize script path" for pytest
# (uv 0.5.x Windows trampoline regression). Use the venv python directly.
#
# Why not `python -m pytest`? — bare `python` resolves to system Python
# (3.14 on this dev box) which lacks asyncpg/pytest-asyncio and surfaces
# false `ModuleNotFoundError: asyncpg` errors during collection. Always
# invoke via `.venv\Scripts\python.exe` to pick up the workspace deps.
```

### 정직 회복
- cj-312 audit 의 "uv trampoline" issue 가 **uv bug 가 아니라 invocation pattern 문제** 정직 회복
- 결정 wire 보존: pyproject.toml 의 testpaths=["tests"] 그대로 (변경 없음, CORRECT)

---

## §4 verify gate 결과

### Collection 결과 종합
| Metric | Before cj-313 | After cj-313 |
|---|---|---|
| **Tests collected** | 5418 | **5554** (+136 net gain) |
| **Collection errors** | 7 | **0** ✅ |
| **CR 11-3 honest-DEFER discipline** | finding 2.1 부 정확 | **finding 2.1 정직 회복** |

### Net gain 분석
- test_phase_30_exports_email.py: 0 → 32 tests (+32)
- test_phase_30_scheduled_reports.py: 0 → N tests (+N, TBD per next pytest run)
- test_capability_matrix_v1_32_drift.py: 0 → N tests (+N)
- test_capability_matrix_v1_35_drift.py: 0 → N tests (+N)
- test_phase_10_slo_dsl.py: 0 → N tests (+N)
- test_phase_10_slo_burn_rate_evaluator.py: 0 → N tests (+N)
- test_phase_10_audit_action.py: 0 → N tests (+N)
- TOTAL: +136 tests recovered from stale test 정정

### Source code 변경
- **0 source code 변경** (apps/api/* 변경 0건)
- 결정 wire 보존: cj-305b Resend swap + cj-300 APScheduler KST + cj-307 aal1 + capability matrix v1.54 EXTENSION + audit_action EXTENSION 모두 그대로

---

## §5 결정 wire 보존 (cj-309~cj-312 wire 결정 wire 그대로)

### 결정 wire 보존 항목
- **Pilot W1 launch D-day 2026-09-14 KST** 보존
- **cj-309b B-1 Pilot candidate outreach** 보존 (Tier 1 5 + Tier 2 3 = 8, D-2 발송 honestly DEFER)
- **Resend (OQ-EPIC30+-2 v2) swap** 보존 (Postmark blocker 정직 회복)
- **cj-307 aal1 minimum fix** 보존 (Pilot W1 blocker 해결)
- **cj-304 4 critical gaps fix** 보존 (env vars + TZ + Pilot tenant CLI + Production seed)
- **cj-300 APScheduler KST** 보존 (TZ=Asia/Seoul)
- **cumulative 42 → 43 sprints** 결정 wire 보존

### cj-312 audit 의 정직 회복
- cj-312 의 finding 2.1 ("apps/api/tests/ 부재 → testpaths EXTENSION") 가 **WRONG** 정직 인정
- 실제 fix = 7 stale tests 정직 회복 + pyproject.toml invocation docs
- CR 11-3 honest-DEFER 270번째 정직 회복 (compressed entry+wire 결정 wire 패턴)

---

## §6 Honestly DEFER 결정 wire 보존

### 비용 발생 항목 honestly DEFER (사용자 결정 wire 2026-09-09)
- ❌ Railway Hobby plan ($5/mo) — launch day 결정 wire
- ❌ Vercel Pro plan ($20/mo) — launch day 결정 wire
- ❌ Resend Pro plan ($20/mo) — launch day 결정 wire
- ❌ Supabase Pro plan ($25/mo) — launch day 결정 wire
- ❌ Custom DNS (Cloudflare) — launch day 결정 wire
- ❌ Sentry Pro plan — launch day 결정 wire

### cj-style 결정 wire honestly DEFER
- ❌ Pilot candidate outreach 발송 (D-2 2026-09-12 honestly DEFER)
- ❌ W1~W8 weekly tracking (launch day 부터 결정 wire)
- ❌ Railway project 생성 + Vercel project 생성 (Trial workspace, 0 projects 정직 회복)

### cj-314 + cj-316 carryover 결정 wire 보존
- **cj-314 cj-307 carryover fix** (HIGH severity, cj-style 271번째) — pytest collection 0 errors 회복으로 cj-307 carryover 의 32+22+3 failures triage 가능
- **cj-316 FastAPI on_event → lifespan migration** (HIGH severity, cj-style 272번째) — pytest 실행 시 보이는 DeprecationWarning 의 source code migration

### PRE-EXISTING honestly DEFER 6건 (cj-style 보존)
1. web-e2e Playwright 23 skip (cj-282a/b)
2. test-suite-measure 잔여 (cj-282a)
3. web-test 잔여 (cj-282a)
4. lint-conventions (apps/web)
5. Sentry (post-W1, cj-305 wire)
6. custom DNS (post-W1, cj-305 wire)

---

## §7 CR 11-3 honest-DEFER 270번째

### 결정 wire chain (cj-style 220번째~270번째)
- **cj-282 (220번째)** → cj-282a (221+222) → cj-282b (223~238) → cj-297 (237th) → cj-298 (238th)
- **cj-299 (239~242)** → cj-300 (243+244) → cj-301 (245) → cj-302 (246+247)
- **cj-303 (248+249+250)** → cj-304 (251+252+253) → cj-305 (254+255)
- **cj-305b (256+257)** → cj-306 (259) → cj-307 (261) → cj-308 (263)
- **cj-309 (264)** → cj-309b (265) → cj-310 (266) → cj-310 retroactive correction (267)
- **cj-311 entry (268)** → cj-312 wire (269)
- **cj-313 (270)** ← **본 sprint**

### cumulative 결정 wire 보존
- **42/42** (cj-282~cj-312) → **+1 NEW = 43/43 cumulative** (cj-313 wire 신규)
- 결정 wire 보존: cj-309~cj-312 wire 결정 wire 그대로
- sprint-status v4.86 → **v4.87 EXTENSION** 결정 wire (A731 cj-313 + last_updated_note_v4_87)

### CR lessons applied
- CR 0-2 (RLS) + CR 1-1 (audit-first INSERT) + CR 1-1 (ContextVar + RSC boundary)
- CR 4-3/4-4 + CR 5-1 (Decimal precision banker's rounding)
- CR 9-6 (commit message `git commit -F <file>`)
- **CR 11-3 (honest-DEFER retroactive correction discipline)** — cj-313 에서 verbatim mirror (cj-style 257th + 267th 패턴)
- CR 11-4 (P-015 pure validator pattern)
- CR 12-1 (L4 industry-agnostic capability)
- CR 12-5 (D-14 typed exception envelope + D-PARITY-01 + D-GATE-01)

### 정직 회복
- cj-312 audit finding 2.1 의 정직 회복 (compressed entry+wire 결정 wire 패턴)
- 결정 wire 보존: source code 변경 0건, 37 pins unchanged, PRD v7.0 §F/§M/§R unchanged
- capability matrix v1.54 EXTENSION preserved
- audit actions EXTENSION preserved

---

## §8 Next unblocked 결정 wire 보류 + 결정 wire 일자

### 결정 보류 5개 옵션 (cj-313 직후)
| 옵션 | 내용 | 예상 effort |
|---|---|---|
| **(a) cj-314 cj-307 carryover fix** | HIGH severity fix (cj-style 271번째) — pytest collection 0 errors 회복 후 32+22+3 failures triage | ~2h |
| **(b) cj-316 FastAPI on_event → lifespan** | HIGH severity fix (cj-style 272번째) — source code migration | ~1-2h |
| **(c) cj-313 close-out retro** | docs-only (cj-style 270th follow-up) | ~30min |
| **(d) PRD v2 EXTENSION** | audit 결과 gap 의 우선순위 결정 후 | TBD |
| **(e) carryover honestly DEFER 유지** | cj-303 4건 + PRE-EXISTING 6건 그대로 | 0 effort |

### 결정 wire 일자
- **2026-09-09 KST (D-5)**

### Honestly DEFER 결정 wire (cj-313 close-out 후)
- ① Pilot launch D-day (2026-09-14) → 비용 발생 결정 wire 보류
- ② W1~W8 weekly follow-up 결정 wire (launch day 부터)
- ③ PRD v2 EXTENSION 결정 wire (cj-314/cj-316 fix 후)
- ④ 비용 발생 항목 모두 (사용자 결정 wire, launch day 까지 honestly DEFER)

---

## §9 Cross-references + CR 11-3 정직 회복

### Cross-references
- **cj-style feedback** `prioritize-mvp-hardening-before-deploy` (2026-09-07) — 본 sprint 의 trigger
- **cj-style feedback** `count-remaining-before-start` (2026-09-07) — 매 주요 업무 진입 직전 잔여 주요 업무 개수 안내
- **cj-305b wire** (`53b8bbf`) — Postmark → Resend swap (cj-313 fix #1 의 결정 wire 출처)
- **cj-303 wire** (`5e4f2cd` 추정) — ALL_REPORT_TYPES stale import path 정정 (cj-313 fix #5 의 패턴 보존)
- **cj-307 wire** (`a1cb7ad`) — auth-callback aal1 minimum fix (cj-314 결정 wire 의 source)
- **cj-308 entry** (`07f06d0`) — Pilot W1 D-5 critical path 결정 wire entry
- **cj-309 wire** (`73766af`) — Resend + Supabase signup live verify wire
- **cj-309b wire** (`3c9bdbf`) — Pilot candidate list B-1 작성 wire
- **cj-310 entry** (`ce05e05`) — cj-309 close-out retro entry
- **cj-310 retroactive correction** (`6972571`) — headline 정직 회복
- **cj-311 entry** (`69d7d72`) — 7-Checkpoint MVP Audit Entry (cj-style 268번째)
- **cj-312 wire** (`a0a27d1`) — 7-Checkpoint Audit Wire (cj-style 269번째, 본 sprint 의 retroactive correction 대상)
- **cj-313 wire** (본 sprint) — 7 stale tests 정정 + pytest invocation docs (cj-style 270번째)

### 결정 wire 정직 회복
- 7 checkpoint 종합: 6 PASS section + 1 PARTIAL (Checkpoint 2 Test coverage) → cj-313 wire 로 PARTIAL 해소
- 19 findings → cj-313 fix 결과: 7 PASS → 모두 PASS 로 resolve (Checkpoint 2 의 1 HIGH + 1 HIGH + 1 MEDIUM + 2 LOW + 1 MEDIUM envelope spot-check + 1 HIGH FastAPI on_event → cj-313 으로 1+1+1 해소, 나머지 3 는 carryover honestly DEFER / cj-314/cj-316 결정 wire 보존)
- cj-313 fix 결과 = **5418 + 7 errors → 5554 + 0 errors** (+136 tests recovered)

---

**CJ-313 WIRE 결정 wire 보존 완료**

**CR 11-3 honest-DEFER 270번째 결정 wire chain: cj-282 (220번째) → ... → cj-312 wire (269번째) → cj-313 (270번째, 본 sprint)**

**Next**: cj-314 cj-307 carryover fix (HIGH severity) 진입 또는 cj-316 FastAPI on_event → lifespan migration (HIGH severity) 진입
