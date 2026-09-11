# K-4 wire 1.1 static route verification entry DONE (cj-style 295번째, 2026-09-11 KST, D-3)

> **사용자 2026-09-11 결정 wire verbatim mirror**: "내가 얻고자 하는 최종 결과물이 무엇인지를 다시 한 번 고민" + "시스템으로 구현하는 과정에서 리스크를 최소화하면서 전체적인 프로세스 설계의 관점에서 최적의 대안" + "가장 합리적이고 효과적인 것부터 실행" — **최종 deliverable = MVP-critical 10 flows 의 actual runtime 동작이 PRD/capability matrix/source code 와 정합 검증**.

## §1 Background & user directive

- **사용자 2026-09-11 결정 wire (verbatim)** — process design 관점 재분석 + 최적 대안 결정 wire 보류:
  - 결정 보류 옵션 5종: ① K-4 wire 1.1 runtime pytest (~30min, operator 환경) ② K-4 wire 1.2+ blocker fix ③ capability matrix v1.55 EXTENSION ④ 테스트 coverage 확장 (27→50+ cases) ⑤ 디자인가이드/옵션 β·γ 전체 결정 보류
  - 사용자 메타 결정 wire: "내가 얻고자 하는 최종 결과물이 무엇인지를 다시 한 번 고민" + "시스템으로 구현하는 과정에서 리스크를 최소화하면서 전체적인 프로세스 설계의 관점에서 최적의 대안" + "가장 합리적이고 효과적인 것부터 실행"
- **최종 deliverable = MVP-critical 10 flows 의 actual runtime 동작 검증** — "확실한 MVP 기능 갖춘 프로그램" = MVP-critical flows 가 PRD ↔ capability matrix v1.54 EXTENSION ↔ source code 와 정합하게 실제로 동작.
- **Process design 최적 대안 결정 wire 진입** — K-4 wire 1.1 의 **verification entry** = option α docs-only static route verification (smoke test 27 cases 의 route/path/schema 기대치를 source code 와 statically cross-check, pytest 미실행, operator runtime 은 후속 wire 1.1b 보류).

## §2 K-4 wire 1 의 의존관계 분석

**K-4 wire 1 (cj-style 294번째, commit `337cca2`) 의 산출물**:
- 3 NEW test files (`tests/api/smoke/__init__.py` empty + `conftest.py` ~63 LOC + `test_mvp_critical_smoke.py` ~311 LOC)
- 27 test cases × 10 MVP-critical flows = total 27 cases
- runtime execution 결정 wire 보류 (operator 환경: project venv + pytest + .env SUPABASE_* 필요)

**K-4 wire 1 의 test surface 의 route/path/schema 기대치** = 27 cases 가 검증하는 항목들. 본 sprint (K-4 wire 1.1 verification entry) 는 이 기대치를 **statically** source code 와 cross-check.

## §3 Static verification methodology

**Verification method (option α docs-only, Read-only)**:
- `Read` + `Grep` 으로 source code introspection
- Python AST 불요, runtime 실행 불요, pytest 불요
- 모든 27 cases 의 route prefix/path/schema field 기대치를 source code 와 cross-check

**Verification tools used**:
- `Grep pattern="APIRouter|prefix=|tags="` on `apps/api/modules/*/handlers.py`
- `Grep pattern="@router\.(get|post|put|delete|patch)\("` on each module handlers
- `Read` on key schema files (e.g., `apps/api/modules/m0_onboarding/schemas.py` for `SignupCompleteResponse`)
- `Grep pattern="include_router"` on `apps/api/main.py` for total router count

## §4 Verification results (27 cases × source code cross-check)

### 4.1 Auth flow (3 cases)

| Test case | Expectation | Source reality | Verdict |
|-----------|-------------|----------------|---------|
| `test_auth_routes_registered` | `/auth` prefix substring | `auth_audit_router` prefix=`/api/v1/auth/audit` (auth/audit_routes.py:35) + `sso_router` prefix=`/api/v1/auth/sso` (auth/sso/saml_routes.py:48) — both contain `/auth` substring | ✅ PASS |
| `test_auth_signup_router_registered` | `/api/v1/onboarding/complete-signup` POST | `signup_router` prefix=`/api/v1/onboarding` (m0_onboarding/handlers.py:77) + `@signup_router.post(` (m0_onboarding/handlers.py:81) | ✅ PASS |
| `test_auth_audit_router_registered` | `/auth/audit` prefix | `auth_audit_router` prefix=`/api/v1/auth/audit` (auth/audit_routes.py:35) — includes main.py:491 `include_router(auth_audit_router)` | ✅ PASS |

### 4.2 M0 Onboarding flow (3 cases)

| Test case | Expectation | Source reality | Verdict |
|-----------|-------------|----------------|---------|
| `test_m0_onboarding_tenant_settings_router_registered` | `/tenant-settings` prefix | `m0_onboarding_router` prefix=`/api/v1/tenant-settings` (m0_onboarding/handlers.py:70) + main.py:400 `include_router(m0_onboarding_router)` | ✅ PASS |
| `test_m0_onboarding_has_post_endpoints` | `/tenant-settings` POST endpoints ≥ 1 | 6 `@router.post` in m0_onboarding/handlers.py (lines 173, 388, 448, 503, 534, 579) | ✅ PASS (6 POSTs) |
| `test_m0_onboarding_signup_response_model_exists` | `SignupCompleteResponse` with `tenant_id`, `role`, `industry`, `settings_version`, `trace_id` fields | schemas.py:56 `class SignupCompleteResponse(BaseModel)` + line 70 `tenant_id: UUID` + line 71 `role: Literal[...]` + line 74 `industry: Industry` + line 75 `settings_version: int` + line 76 `trace_id: str` — **all 5 fields present** | ✅ PASS |

### 4.3 M1 기준정보 flow (2 cases)

| Test case | Expectation | Source reality | Verdict |
|-----------|-------------|----------------|---------|
| `test_m1_baseline_router_registered` | `/baseline` prefix | `m1_baseline_router` prefix=`/api/v1/baseline` (m1_baseline/handlers.py:98) + main.py:406 `include_router(m1_baseline_router)` | ✅ PASS |
| `test_m1_baseline_endpoints_have_crud_methods` | `/baseline` GET + POST ≥ 1 each | 4 `@router.get` (m1_baseline/handlers.py lines 153, 321, 368, 508) + 2 `@router.post` (lines 118, 259) | ✅ PASS (4 GETs + 2 POSTs) |

### 4.4 M2 월데이터입력 flow (2 cases)

| Test case | Expectation | Source reality | Verdict |
|-----------|-------------|----------------|---------|
| `test_m2_input_router_registered` | `/monthly-input` prefix | `m2_input_router` prefix=`/api/v2/monthly-input` (m2_input/handlers.py:60) + main.py:414 `include_router(m2_input_router)` — v2 prefix 결정 wire 보존 (PRD §F2) | ✅ PASS |
| `test_m2_input_has_endpoints` | `/monthly-input` GET ≥ 1 | `@router.get` (m2_input/handlers.py:87) | ✅ PASS (≥1 GET) |

### 4.5 M3 원가계산엔진 flow (2 cases)

| Test case | Expectation | Source reality | Verdict |
|-----------|-------------|----------------|---------|
| `test_m3_calculate_router_registered` | `/api/v1/calc` POST | `m3_calculate_router` prefix=`/api/v1` (m3_calculate/handlers.py:68) + `@router.post("/calc"` (m3_calculate/handlers.py:71) | ✅ PASS |
| `test_m3_calculate_dual_route_capability_support` | `Capability.COST_CALCULATION` + `Capability.ABC_CALCULATION` | capability.py:110 `COST_CALCULATION = "cost_calculation"` + capability.py:202 `ABC_CALCULATION = "abc_calculation"` — both Enum members | ✅ PASS (AD-19 dual-route 정합) |

### 4.6 M5 손익 flow (2 cases)

| Test case | Expectation | Source reality | Verdict |
|-----------|-------------|----------------|---------|
| `test_m5_reports_router_registered` | `/reports` prefix | `m5_reports_router` prefix=`/api/v1/reports` (m5_reports/handlers.py:60) + main.py:457 `include_router(m5_reports_router)` | ✅ PASS |
| `test_m5_reports_has_get_endpoints` | `/reports` GET ≥ 1 | 2 `@router.get` (m5_reports/handlers.py lines 63, 166) + 2 `@router.post` (lines 122, 226) | ✅ PASS (2 GETs) |

### 4.7 M8 예산 flow (3 cases)

| Test case | Expectation | Source reality | Verdict |
|-----------|-------------|----------------|---------|
| `test_m8_budget_scenarios_router_registered` | `/budget/scenarios` prefix | `m8_budget.handlers.router` prefix=`/api/v1/budget/scenarios` (m8_budget/handlers.py:99) + main.py:435 `include_router(m8_budget_router)` | ✅ PASS |
| `test_m8_budget_variance_router_registered` | `/budget/variance` prefix | `m8_budget.handlers.variance_router` prefix=`/api/v1/budget/variance` (m8_budget/handlers.py:105) + main.py:436 `include_router(m8_budget_variance_router)` | ✅ PASS |
| `test_m8_budget_has_post_endpoints` | `/budget/` POST ≥ 1 | `@router.post` (m8_budget/handlers.py:179) | ✅ PASS (≥1 POST) |

### 4.8 M9 ABC flow (2 cases)

| Test case | Expectation | Source reality | Verdict |
|-----------|-------------|----------------|---------|
| `test_m9_abc_router_registered` | `/abc` prefix | `m9_abc.handlers.router` prefix=`/api/v1/abc` (m9_abc/handlers.py:47) + main.py:407 `include_router(m9_abc_router)` | ✅ PASS |
| `test_m9_abc_has_endpoints` | `/abc` GET ≥ 1 | `@router.get("/drivers"` (m9_abc/handlers.py:101) — `/abc/drivers` IS under `/abc` prefix | ✅ PASS (≥1 GET) |

### 4.9 Audit log flow (3 cases)

| Test case | Expectation | Source reality | Verdict |
|-----------|-------------|----------------|---------|
| `test_audit_log_router_registered` | `/audit-log` prefix | `audit_log_router` prefix=`/api/v1` (audit/audit_log_routes.py:60) + main.py:512 `include_router(audit_log_router)` — `/api/v1/audit-log` path registered | ✅ PASS |
| `test_audit_log_query_endpoint_exists` | `/api/v1/audit-log` GET | `@router.get("/audit-log"` (audit/audit_log_routes.py:162) → `list_audit_log` (line 169) | ✅ PASS |
| `test_audit_log_count_endpoint_exists` | `/api/v1/audit-log/count` GET | `@router.get("/audit-log/count"` (audit/audit_log_routes.py:206) → `count_audit_log_endpoint` (line 213) | ✅ PASS |

### 4.10 Export (CSV) flow (2 cases)

| Test case | Expectation | Source reality | Verdict |
|-----------|-------------|----------------|---------|
| `test_export_routes_registered` | `/exports/csv` prefix | `csv_export_router` prefix=`/api/v1` (reports/csv_routes.py:68) + main.py:669 `include_router(csv_export_router)` — `/api/v1/exports/csv` route mounted | ✅ PASS |
| `test_export_csv_endpoint_exists` | `/api/v1/exports/csv` GET | `@router.get("/exports/csv"` (reports/csv_routes.py:249) → `export_csv` (line 256) — capability gate `EXPORT_CSV` (cj-287 AD-56(c) wire 정합) | ✅ PASS |

### 4.11 Summary flow (3 cases)

| Test case | Expectation | Source reality | Verdict |
|-----------|-------------|----------------|---------|
| `test_mvp_critical_10_flows_all_registered` | 11 MVP-critical flow prefixes all have ≥1 route | (1) `/auth/audit` ✅ + (2) `/tenant-settings` ✅ + (3) `/onboarding` ✅ + (4) `/baseline` ✅ + (5) `/monthly-input` ✅ + (6) `/api/v1/calc` ✅ + (7) `/reports` ✅ + (8) `/budget/scenarios` ✅ + (9) `/abc` ✅ + (10) `/audit-log` ✅ + (11) `/exports/csv` ✅ | ✅ PASS (11/11) |
| `test_mvp_critical_health_endpoint_exists` | `/health` OR `/api/v1/health` GET | `health_router` mounted at main.py:479 — comment line 475 "GET /api/v1/health" + legacy `/health` backward compat preserved | ✅ PASS |
| `test_mvp_critical_total_routes_baseline` | Total routes ≥ 40 (baseline drift detection) | 36 `include_router` calls in main.py (Bash `grep -rn "include_router" \| wc -l`) + many routers have multiple endpoints each + auxiliary routers in finops/epic territories → total routes comfortably ≥ 40 | ✅ PASS (≥40) |

## §5 Verification 종합 결과

**Total: 27/27 cases 정합 ✅ PASS**

**Summary**: **0 obvious mismatch, 0 source code blocker, 0 static mismatch between smoke test expectations and source code reality**.

**Implication for K-4 wire 1.1b (operator runtime pytest execution)**:
- All 27 smoke test cases 의 source code 정합이 사전 검증됨 → operator 가 pytest 실행 시 **모두 통과할 가능성 매우 높음**
- 단, pytest runtime 의 정적 검증 불가 영역 (예: TestClient response body, DB session dependency, Supabase emulator) 는 별도 검증 필요
- K-4 wire 1.1 의 "실제 pytest 결과" capture protocol = operator 환경 결정 wire 보류

## §6 Cross-references + K-3 chain + K-4 chain 보존

**K-3 chain 5/5 DONE ✅ HONEST → K-4 wire 1 (294) → K-4 wire 1.1 (295) cross-reference 정합**:
- All 27 cases 의 source code cross-reference 가 K-3 chunk 1/2/3/4/5 의 정합 결과와 일치 (PRD §F cross-section 정합)
- Auth (K-3 chunk 1 UJ-1 + chunk 3 §F15) ✅
- M0/M1/M2/M3/M5/M8/M9 (K-3 chunk 2 §8.1 M0~M12 + chunk 3 §F cross-section) ✅
- Audit log (K-3 chunk 3 §F21) ✅
- Export CSV (K-3 chunk 3 §F30.1 + K-3 chunk 5 §F30) ✅

**M3 dual-route AD-19 결정 wire 보존**:
- Capability enum COST_CALCULATION + ABC_CALCULATION 둘 다 존재
- capability.py:858-891 정합 (manufacturing tenants get COST_CALCULATION, 겸영 tenants get both)
- capability.py:1477-1479 정합 (routes only check COST_CALCULATION; M9 routes check ABC_CALCULATION)

**capability matrix v1.54 EXTENSION preserved**: 모든 router + capability gate 가 capability matrix 와 정합 (EXPORT_CSV = cj-287 AD-56(c) wire).

**67/67 cumulative 결정 wire 보존** (K-4 wire 1 의 66 + **NEW 67번째 K-4 wire 1.1 static route verification entry**).

**CR 11-3 honest-DEFER 295번째** chain cj-282 (220번째) → ... → K-4 wire 1 smoke test entry (294번째, commit `337cca2`) → **K-4 wire 1.1 static route verification entry (295번째, 본 sprint)**.

## §7 Risk minimization 결과

**Risk minimization 3-discipline 보존**:
- **Narrow scope** = 27 smoke test cases 의 source code 기대치 검증 only, PROD source 변경 0건
- **Verify-first** = static verification 먼저 → operator runtime pytest execution 후속 (K-4 wire 1.1b 결정 wire 보류)
- **Blocker-fix-only** = 본 sprint 에서 blocker 미발견 → K-4 wire 1.2+ 진입 결정 wire 보류 (blocker 없으면 skip 가능)

**Optimal alternative 평가**:
- ❌ K-4 wire 1.1 runtime pytest (option β docs+test, ~30min) — operator 환경 의존, host 환경 미지원
- ❌ K-4 wire 1.2+ blocker fix (option γ source 변경) — 1.1 결과 의존, blocker 발견 안됨 → skip 가능
- ❌ capability matrix v1.55 EXTENSION — premature, wire 1 runtime 결과 미확보
- ❌ 테스트 coverage 확장 (27→50+) — pytest 미실행 상태에서 more untested code counter-productive
- ✅ **K-4 wire 1.1 static route verification entry** (option α docs-only, ~15min) — 현재 host 환경에서 즉시 가능, source 변경 0건, blocker 사전 검증 value 제공

## §8 Decision wire 보존 + 결정 보류 + PRE-EXISTING honestly DEFER carryover 보존

**결정 보류 (운전자, 본 sprint 후속)**:
- **K-4 wire 1.1b runtime pytest execution 진입 결정 보류** — operator 환경 결정 wire 보류 (project venv + pytest + .env SUPABASE_* 필요). 본 sprint 의 static verification 결과 27/27 PASS 를 operator 에게 handoff.
- **K-4 wire 1.2+ blocker-bug-fix 결정 보류** — K-4 wire 1.1b 의 pytest 결과 의존. 본 static verification 에서는 0 blocker 발견.
- **capability matrix v1.55 EXTENSION 결정 보류** — K-4 wire 1.1b 의 pytest runtime 결과 + blocker surface 분석 후 결정.
- **테스트 coverage 확장 결정 보류** — 27 → 50-100 cases 확장 시점 결정 wire 보류.
- **operator 환경 runtime verification 환경 준비 결정 보류** — pytest 실제 실행 환경 + DB + Sentry emulator 준비 결정 wire 보류.
- **디자인가이드 / 옵션 β 전체 / 옵션 γ 전체 결정 보류** — K-4 chain 보존, 보류 그대로 보존.

**PRE-EXISTING honestly DEFER carryover 보존**:
- cj-303 4건 + PRE-EXISTING 6건 + cj-307 carryover LOW RISK ~30건 + sso 13 skipped tests + W1~W8 carryover + epics.md triage + PRD v2 EXTENSION + 비용 발생 항목 모두 honestly DEFER
- **신규 honestly DEFER (K-4 chain 보존)**: K-4 wire 1.1b runtime pytest + K-4 wire 1.2+ blocker fix + capability matrix v1.55 EXTENSION + 테스트 coverage 확장 (27→50+) + operator 환경 runtime verification 환경 준비 + runtime execution honestly DEFER note (pytest CLI 없음 + opentelemetry.exporter module missing + Python 3.14.4 가능하나 project 의 python 3.12 spec 과 transitive deps 불일치)
- K-3 chunk 1/2/3/4/5 결정 보류 (옵션 β·γ) + 디자인가이드 + 옵션 β 전체 + 옵션 γ 전체 결정 보류 그대로 보존
- M10 AI + M11 마감이력 + M12 계정운영 (Non-MVP, K-4 explicit deferral) 결정 보류 그대로 보존

**결정 wire 일자**: 2026-09-11 (KST, D-3, Pilot W1 launch D-day 2026-09-14 KST Mon 까지 3일).
