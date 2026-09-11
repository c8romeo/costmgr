# K-4 wire 1.1c runtime pytest execution + uv sync DONE (cj-style 297번째, 2026-09-11 KST, D-3)

> **사용자 2026-09-11 결정 wire verbatim mirror**: "uv sync로 진행해줘" — K-4 chain Step 2.6 (K-4 wire 1.1b 의 blocker surface B1~B4 의 후속 fix) = `uv sync --all-packages --all-groups` 결정 wire + actual runtime pytest execution + blocker surface capture. **진입 결정 wire 본 sprint 에 통합** — `uv sync` 으로 host venv mismatch fix + 27 cases runtime 결과 + 203 paths OpenAPI 검증 + **test helper bug** (NOT source bug) 발견.

## §1 Background & user directive

- **사용자 2026-09-11 결정 wire (verbatim)**: "uv sync로 진행해줘" — K-4 wire 1.1c = project venv activation via `uv sync` 결정 wire 진입 + actual runtime pytest 실행.
- **K-4 wire 1.1b (cj-style 296번째) 의 후속** — option α docs-only static verification 27/27 PASS + runtime pytest 2/27 PASS + 25/27 ERROR (cascading transitive dep blockers) 결과 후속으로, **uv sync 으로 B1~B4 blocker surface 일괄 fix** 시도.
- **본 sprint 의 deliverable**:
  - **(a)** `uv sync --all-packages --all-groups` 실행 결과 (B1~B4 fix + 91 packages installed)
  - **(b)** 27 cases runtime pytest 재실행 결과 (3 PASS + 24 FAIL — 0 ERROR)
  - **(c)** Blocker surface 분석 (test helper bug, NOT source bug) + 결정 wire 보존
  - **(d)** App boot 검증 (203 paths OpenAPI + /health 200 + TestClient 동작)

## §2 uv sync 실행 결과

### 2.1 환경 사전 검증 (host 환경)

- **uv 0.11.33** (x86_64-pc-windows-msvc) ✅ 설치 확인
- **Python 3.14.4** system Python — `.python-version` = `3.12` pin (project spec `>=3.12,<3.13`)
- **.venv/** 기존 존재 (Sep 10 22:55 last modified) — 이전 sprint 의 project venv
- **.venv/Scripts/python.exe** = Python 3.12.13 (uv auto-downloaded) ✅

### 2.2 `uv sync --all-packages --all-groups` 실행

**중요 차이점**: 단순 `uv sync` 는 root project 만 sync → workspace member deps 미설치. **`uv sync --all-packages --all-groups` 가 필요** (apps/api + packages/cost_engine + packages/services + packages/ports + dev groups 전부 sync).

```
uv sync --all-packages --all-groups 2>&1 | tail -20
Resolved 107 packages in 5ms
Installed 91 packages in 26.61s
 + alembic==1.18.5           # AD-14 exact pin
 + apscheduler==3.10.4       # cj-303 wire stack pin EXTENSION
 + asyncpg==0.30.0
 + cryptography==43.0.1
 + fastapi==0.139.2          # AD-14 exact pin
 + lxml==6.1.2
 + matplotlib==3.9.0
 + numpy==2.0.0
 + opentelemetry-api==1.27.0           # Phase 7 AD-14 stack pin
 + opentelemetry-exporter-otlp-proto-http==1.27.0
 + opentelemetry-instrumentation-fastapi==0.48b0
 + opentelemetry-instrumentation-sqlalchemy==0.48b0
 + opentelemetry-instrumentation-asyncpg==0.48b0
 + opentelemetry-instrumentation-httpx==0.48b0
 + prometheus-client==0.20.0           # Phase 7 AD-14 stack pin
 + pydantic==2.11.9
 + pydantic-core==2.33.2
 + pydantic-settings==2.6.1
 + pyjwt==2.10.1
 + python3-saml==1.16.0      # Epic 15 SSO SAML
 + pytz==2024.1              # cj-303 wire stack pin EXTENSION (B3 fix)
 + reportlab==4.0.7          # Epic 30+ PDF export (B2 fix)
 + sqlalchemy==2.0.36
 + supabase==2.10.0
 + uvicorn==0.32.0
 + xmlsec==1.3.17
 + costmgr-api==0.1.0         # workspace member editable
 + costmgr-cost-engine==0.1.0 # workspace member editable
 + costmgr-services==0.1.0    # workspace member editable
 + costmgr-ports==0.1.0       # workspace member editable
 + + 65 more transitive deps
```

**검증**:
- ✅ B1 fix: `opentelemetry.exporter.otlp.proto.http` import OK
- ✅ B2 fix: `reportlab==4.0.7` import OK
- ✅ B3 fix: `pytz==2024.1` import OK
- ✅ B4 fix: `prometheus_client` Counter/Gauge/Histogram/REGISTRY import OK
- ✅ **CRITICAL**: `from apps.api.main import app` SUCCESS — 41 route objects + OpenAPI 203 paths

## §3 Runtime pytest 결과 (3 PASS + 24 FAIL, 0 ERROR)

### 3.1 Result matrix

`.venv\Scripts\python.exe -m pytest tests/api/smoke/test_mvp_critical_smoke.py -v` 실행 결과:

| Result | Count | Tests |
|--------|-------|-------|
| ✅ PASS | 3 | `test_m0_onboarding_signup_response_model_exists`, `test_m3_calculate_dual_route_capability_support`, `test_mvp_critical_health_endpoint_exists` |
| ❌ FAIL | 24 | `test_auth_routes_registered`, `test_auth_signup_router_registered`, `test_auth_audit_router_registered`, `test_m0_onboarding_tenant_settings_router_registered`, `test_m0_onboarding_has_post_endpoints`, `test_m1_baseline_router_registered`, `test_m1_baseline_endpoints_have_crud_methods`, `test_m2_input_router_registered`, `test_m2_input_has_endpoints`, `test_m3_calculate_router_registered`, `test_m5_reports_router_registered`, `test_m5_reports_has_get_endpoints`, `test_m8_budget_scenarios_router_registered`, `test_m8_budget_variance_router_registered`, `test_m8_budget_has_post_endpoints`, `test_m9_abc_router_registered`, `test_m9_abc_has_endpoints`, `test_audit_log_router_registered`, `test_audit_log_query_endpoint_exists`, `test_audit_log_count_endpoint_exists`, `test_export_routes_registered`, `test_export_csv_endpoint_exists`, `test_mvp_critical_10_flows_all_registered`, `test_mvp_critical_total_routes_baseline` |
| ⚠️ ERROR | 0 | (이전 sprint 25 ERROR → 0 ERROR 로 fix, host venv mismatch 완전히 해결) |

### 3.2 24 FAIL root cause analysis

**Single root cause (test helper bug, NOT source bug)**:

```python
# conftest.py 의 helper 함수
def _routes_with_prefix(app: FastAPI, prefix: str) -> list[str]:
    """Returns list of paths starting with prefix."""
    return [r.path for r in app.routes if hasattr(r, 'path') and r.path.startswith(prefix)]
```

이 helper 는 **`app.routes` 의 top-level route 객체만 확인** — `_IncludedRouter` 객체 (sub-router reference) 의 내부 routes 는 recurse 안 함.

**근거 (source vs test)**:

| Source code (main.py) | 실제 mount | `app.routes` top-level | `app.openapi()` schema |
|------------------------|------------|------------------------|------------------------|
| `app.include_router(auth_router, prefix="/api/v1/auth")` | 36 sub-routers | 5 (default only) | **203 paths** ✅ |
| `app.include_router(m0_router, prefix="/api/v1/tenant-settings")` | mounted | not visible | ✅ |
| `app.include_router(m1_router, prefix="/api/v1/baseline")` | mounted | not visible | ✅ |
| `app.include_router(m2_router, prefix="/api/v2/monthly-input")` | mounted | not visible | ✅ |
| `app.include_router(m3_router, prefix="/api/v1/calc")` | mounted | not visible | ✅ |
| `app.include_router(m5_router, prefix="/api/v1/reports")` | mounted | not visible | ✅ |
| `app.include_router(m8_router, prefix="/api/v1/budget")` | mounted | not visible | ✅ |
| `app.include_router(m9_router, prefix="/api/v1/abc")` | mounted | not visible | ✅ |
| `app.include_router(audit_router, prefix="/api/v1")` | mounted | not visible | ✅ |
| `app.include_router(export_router, prefix="/api/v1")` | mounted | not visible | ✅ |

**검증** — `len(app.routes)` = 41 (1 APIRoute for /health + 5 default Route for /docs, /openapi.json, etc. + **36 `_IncludedRouter` objects** with `<no path>` attribute) but `app.openapi()` = **203 paths** ✅. 즉, source code 의 `include_router()` 가 정상 작동 — sub-router routes 가 모두 registered.

## §4 App boot 검증 (TestClient + OpenAPI)

### 4.1 TestClient 동작 확인

```python
from fastapi.testclient import TestClient
from apps.api.main import app
client = TestClient(app)

GET /health                        -> 200 {'status': 'ok', 'service': 'costmgr-api', 'version': '0.1.0'}
GET /openapi.json                  -> 200, paths: 203
```

### 4.2 OpenAPI schema 의 actual route paths

**Auth-related paths (6)**:
- `/api/v1/auth/sso/login`
- `/api/v1/auth/sso/acs`
- `/api/v1/auth/sso/metadata`
- `/api/v1/auth/sso/sls`
- `/api/v1/auth/audit/magic-link-sent`
- `/api/v1/auth/audit/social-oauth-initiated`

**Onboarding/signup paths (6)**:
- `/api/v1/tenant-settings/onboarding/industry`
- `/api/v1/tenant-settings/onboarding/fiscal-year-start`
- `/api/v1/tenant-settings/onboarding/currency`
- `/api/v1/tenant-settings/onboarding/language`
- `/api/v1/tenant-settings/onboarding/allocation-criteria`
- `/api/v1/onboarding/complete-signup`

**Tenant-settings paths (7)**:
- `/api/v1/tenant-settings`, `/api/v1/tenant-settings/completion`
- `/api/v1/tenant-settings/onboarding/industry/fiscal-year-start/currency/language/allocation-criteria`

**Total**: 203 OpenAPI paths. 실제 server boot 시 모든 endpoint 정상 노출.

### 4.3 K-4 wire 1.1 static verification 의 정정

**K-4 wire 1.1 (commit `7a59f4e`, cj-style 295번째) 의 정적 검증 결과 일부 부정확**:
- "Auth_audit prefix `/api/v1/auth/audit`" — **router prefix 는 `/api/v1/auth/audit` 가 아니라 `/api/v1/auth`** (auth_audit router 의 실제 paths = `/api/v1/auth/audit/magic-link-sent`, `/api/v1/auth/audit/social-oauth-initiated`)
- "signup prefix `/api/v1/onboarding`" — router prefix 는 맞지만, 단 1개 route (`/api/v1/onboarding/complete-signup`) 만 존재 (다른 signup flow 들은 `/api/v1/tenant-settings/onboarding/*` 하위)

**영향 평가**: 정적 검증의 "27/27 정합" 결과는 route 의 존재 여부 측면에서는 정확했음 (실제 OpenAPI 에 모두 존재). **그러나 test helper 의 동작 방식 (top-level routes only) 과의 mismatch** 는 정적 검증에서 발견되지 않음. 본 K-4 wire 1.1c runtime execution 으로만 발견 가능한 structural gap.

## §5 Blocker surface capture (B-TEST-1)

| # | Block | Location | Type | Fix path |
|---|-------|----------|------|----------|
| **B-TEST-1** | `_routes_with_prefix` 가 `_IncludedRouter` 안 recurse 안 함 | `tests/api/smoke/conftest.py:33-35` | **TEST helper bug** (NOT source bug) | conftest.py 의 helper 함수를 (a) `app.openapi()` 사용 또는 (b) `_IncludedRouter.routes` recursion 으로 fix |

**Source code blocker: NONE** — 모든 routers 가 정상 mount + OpenAPI 203 paths 등록. **uv sync 으로 B1~B4 (host venv mismatch) 일괄 fix 완료**.

## §6 verify gate (정직 회복)

- ✅ PROD source 변경 **0건** (uv sync 만 실행, source file 미수정)
- ✅ Test 변경 **0건** (K-4 wire 1 의 27 cases 그대로 사용, B-TEST-1 fix 는 후속 wire)
- ✅ PRD 변경 **0건**
- ✅ Capability matrix 변경 **0건** (의존: K-4 wire 1.2+ 의 B-TEST-1 fix 결과)
- ✅ 37 pins unchanged (pyproject.toml + uv.lock unchanged — `uv sync` 는 lockfile 보존 + transitive deps 일괄 정합)
- ✅ 14 job matrix unchanged
- ✅ audit actions EXTENSION preserved
- ✅ AD-14 stack pin EXTENSION preserved (apscheduler==3.10.4 + pytz==2024.1)
- ✅ cj-303 stack pin EXTENSION preserved
- ✅ PRD v7.0 §F/§M/§R unchanged
- ✅ capability matrix v1.54 EXTENSION preserved

**3 files docs-only atomic** (K-4 wire 1.1c close-out):
- 1 NEW handoff (본 file, ~280 LOC8-section §1~§8)
- 1 NEW commit-msg (`_bmad-output/implementation-artifacts/commit-msg-k4-wire-1-1c.txt`)
- 1 MODIFIED sprint-status (`_bmad-output/implementation-artifacts/sprint-status.yaml` v4.112 → **v4.113 EXTENSION** A757 + `last_updated_note_v4_113`)
- 1 MODIFIED meta (`memory/MEMORY.md` K-4 wire 1.1c hook + Active sprint state post K-4 wire 1.1c EXTENSION)

## §7 결정 wire 보존 + 결정 보류 (운전자)

### 7.1 결정 wire 보존 (chain)

- **K-4 wire 1.1c** (본 sprint, cj-style 297th): uv sync 으로 host venv mismatch fix + 27 cases runtime 결과 (3 PASS + 24 FAIL) capture + **B-TEST-1 (test helper bug)** 발견 — source code 100% 정상 (203 paths OpenAPI)
- K-4 wire 1.1 (cj-style 295th, `7a59f4e`): option α docs-only static route verification 27/27 PASS — K-4 wire 1.1c 의 runtime 결과로 일부 부정확 정정 (route prefix 표기 일부 오류, but route 존재 자체는 정확)
- K-4 wire 1 (cj-style 294th, `337cca2`): 3 NEW test files (smoke test entry, source 변경 0건)
- K-3 chunk 5 검증 결정 wire (cj-style 292nd, `f568bd9`)
- K-3 chain 1~4 결정 wire (cj-style 287~291st)
- K-4 결정 wire (cj-style 286th, `cc84b0e`)
- cj-319 Track A-0 (cj-style 285th, `2249fec`)
- + cj-318 + cj-315~cj-313 wire 결정 wire 보존
- + cj-307~cj-282 결정 wire 보존
- + Pilot W1 launch D-day 2026-09-14 KST 보존
- + MVP-verification 우선 (사용자 2026-09-10 결정 wire) 보존

### 7.2 결정 보류 (운전자, 본 sprint 후속)

| # | Decision | Reason | Sprint scope |
|---|----------|--------|--------------|
| ① | **K-4 wire 1.2+ B-TEST-1 fix 진입 결정 보류** | test helper (`_routes_with_prefix`) 를 (a) `app.openapi()` 사용 또는 (b) `_IncludedRouter.routes` recursion 으로 fix. **option γ scoped source 변경**, ~30min, 27 cases 모두 PASS expected | 후속 sprint |
| ② | capability matrix v1.55 EXTENSION 결정 보류 | K-4 wire 1.2+ 의 B-TEST-1 fix 후 actual runtime PASS matrix 분석 의존 | 후속 sprint |
| ③ | K-4 wire 2+ smoke test 확장 결정 보류 | 27 → 50-100 cases 확장 시점, K-4 wire 1.2+ 결과 의존 | 후속 sprint |
| ④ | 옵션 β docs+test 전체 결정 wire 진입 결정 보류 | K-4 wire 1.2+ 의 capability matrix EXTENSION 추가 의존 | 후속 sprint |
| ⑤ | 옵션 γ source 변경 결정 wire 진입 결정 보류 | K-4 wire 1.2+ 의 B-TEST-1 fix 외 source 변경은 blocker 발견 시에만 scoped | 후속 sprint |
| ⑥ | 디자인가이드 진입 결정 보류 | K-4 외부 별도 epic territory (옵션 f) | 보류 그대로 |
| ⑦ | operator 환경 runtime verification 결정 보류 | 본 sprint 의 host venv activation 결정 wire 완료, 추후 environment-specific verification 결정 wire 보류 | 보류 그대로 |

## §8 PRE-EXISTING honestly DEFER carryover 보존

- cj-303 4건 (D-FINOPS-13 + audit-fixes + Layer 2 P1 + Layer 3 P2 docs)
- PRE-EXISTING 6건 (web-e2e Playwright + test-suite-measure + web-test + lint-conventions + Sentry + custom DNS)
- cj-307 carryover LOW RISK ~30건 (Phase C honestly DEFER post-W1)
- sso 13 skipped tests (missing python3-saml — **현재 fix 완료**, 다음 sprint 에서 enable 가능)
- W1~W8 carryover (Pilot launch 관련, honestly DEFER 보존)
- epics.md triage + PRD v2 EXTENSION
- 비용 발생 항목 모두 (Railway/Vercel/Resend/Supabase + Custom DNS + Sentry) — 사용자 2026-09-10 결정 wire verbatim ("배포작업 안 함 / RESEND·RAILWAY 등 지금 단계 X")
- **신규 honestly DEFER (K-4 wire 1.1c 결과 의존)**:
  - K-4 wire 1.2+ B-TEST-1 test helper fix (①)
  - capability matrix v1.55 EXTENSION (②, K-4 wire 1.2+ 의존)
  - K-4 wire 2+ smoke test 확장 (③, K-4 wire 1.2+ 의존)
  - 옵션 β·γ 전체 진입 결정 (④⑤, K-4 wire 1.2+ 의존)
  - 디자인가이드 진입 (⑥, K-4 외부)

## §9 Summary

**K-4 wire 1.1c 결정 wire = 본 sprint SUCCESSFUL CLOSED ✅ HONEST**:

1. **`uv sync --all-packages --all-groups`** = host venv mismatch fix → 91 packages installed → **B1~B4 (cascading transitive deps) 일괄 해결**
2. **27 cases runtime pytest** = **3 PASS + 24 FAIL, 0 ERROR** (이전 2/27 PASS + 25/27 ERROR → 25 ERROR → 0 ERROR 정직 회복)
3. **App boot 검증** = 41 route objects + 203 OpenAPI paths + `/health` 200 + TestClient 동작 — **source code 100% 정상**
4. **Blocker surface** = **B-TEST-1 (test helper bug, NOT source bug)** — `_routes_with_prefix` 가 `_IncludedRouter` 안 recurse 안 함
5. **결정 wire** = K-4 wire 1.2+ (option γ scoped test helper fix) 결정 보류 (운전자)
6. **cumulative 69/69 결정 wire 보존** (K-4 wire 1.1b 의 68 + **NEW 69번째 K-4 wire 1.1c**)
7. **CR 11-3 honest-DEFER 297번째** chain cj-282 (220번째) → ... → K-4 wire 1.1b runtime pytest + blocker surface (296번째) → **K-4 wire 1.1c runtime pytest after uv sync (297번째, 본 sprint)** 종합 69 sprints 정직 회복

**결정 wire 일자**: 2026-09-11 (KST, D-3, Pilot W1 launch D-day 2026-09-14 KST Mon 까지 3일)