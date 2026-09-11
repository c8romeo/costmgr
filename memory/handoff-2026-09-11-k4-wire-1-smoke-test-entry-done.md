# K-4 wire 1 MVP-critical smoke test entry DONE (cj-style 294번째, 2026-09-11 KST, D-3)

> **사용자 2026-09-11 결정 wire verbatim mirror**: "옵션 β로 K-4 wire 1 진입해줘" + "배포작업 안 함 / RESEND·RAILWAY 등 지금 단계 X / 확실한 MVP 기능 갖춘 프로그램 필요" + "시스템으로 구현하는 과정에서 리스크 최소화 + 전체적인 프로세스 설계의 관점에서 최적의 대안".

## §1 Background & user directive

- **사용자 2026-09-11 결정 wire (verbatim)**: "옵션 β로 K-4 wire 1 진입해줘" — K-4 chain Step 2 진입 = MVP-critical runtime smoke test entry, option β docs+test method 적용.
- **K-4 entry decision wire (cj-style 293번째, commit `23ece93`) 의 step 2 정합**:
  - Step 1 (K-4 entry) DONE — option α docs-only, scope narrowing + 결정 wire
  - **Step 2 (K-4 wire 1, 본 sprint)** — option β docs+test, MVP-critical runtime smoke test entry
  - Step 3 (K-4 wire 2+, 다음 sprint) — option γ scoped, blocker-bug-fix only
- **K-3 chain 5/5 DONE ✅ HONEST** 보존 — chunk 1 (`9842dc7`) + chunk 2 (`3ebd493`) + chunk 3 (`ab31195`) + chunk 4 (cj-style 291번째) + chunk 5 (`f568bd9`, cj-style 292번째).
- **Pilot W1 launch D-day 2026-09-14 KST 보존** + **MVP-verification 우선 (사용자 2026-09-10 결정 wire) 보존**.

## §2 K-4 wire 1 scope (본 sprint actual scope)

**Verification scope**: MVP-critical 10 flows × ~3 cases each = **27 test cases** (lightweight smoke).
1. **Auth** (3 cases) — `/auth` + `/onboarding/complete-signup` + `/auth/audit` registration
2. **M0 Onboarding** (3 cases) — `/tenant-settings` router + POST endpoint + `SignupCompleteResponse` schema
3. **M1 기준정보** (2 cases) — `/baseline` router + GET/POST CRUD
4. **M2 월데이터입력** (2 cases) — `/monthly-input` router + GET endpoints
5. **M3 원가계산엔진** (2 cases) — `/api/v1/calc` + capability dual-route (COST_CALCULATION ∪ ABC_CALCULATION)
6. **M5 손익** (2 cases) — `/reports` router + GET endpoints
7. **M8 예산** (3 cases) — `/budget/scenarios` + `/budget/variance` + POST endpoints
8. **M9 ABC** (2 cases) — `/abc` router + GET endpoints
9. **Audit log** (3 cases) — `/audit-log` + `/audit-log` GET + `/audit-log/count` GET
10. **Export (CSV)** (2 cases) — `/exports/csv` + GET `/exports/csv`
11. **Summary** (3 cases) — 10 flows all registered + health endpoint + total routes baseline ≥ 40

**Test method (option β docs+test)**:
- **Router registration 검증** — main app 의 include_router 정합 검증
- **Endpoint path + HTTP method 정합 검증** — FastAPI route introspection
- **Schema import 검증** — pydantic model fields 존재 확인 (response_model cross-section)
- **Total routes baseline regression detection** — baseline ≥ 40 routes (drift 감지)

**runtime = test only 변경 (PROD source 변경 0건)**:
- NEW `tests/api/smoke/__init__.py` (empty)
- NEW `tests/api/smoke/conftest.py` (~50 LOC, fixtures + helpers)
- NEW `tests/api/smoke/test_mvp_critical_smoke.py` (~330 LOC, 27 test cases)

## §3 Test environment honestly DEFER (runtime execution)

**runtime test execution 결정 wire 보류 (운전자)**:
- pytest + project venv (`uv sync` or `pip install -e .`) + `.env` (SUPABASE_*, DATABASE_URL) 필요
- 현재 host 환경 검증 결과 (2026-09-11 KST, 본 sprint 진입 시점):
  - pytest CLI 없음 (`which pytest` → no pytest)
  - `opentelemetry.exporter` module missing (K-4 entry decision wire 의 "TestClient health" 환경 의존 변동 보존)
  - Python 3.14.4 + FastAPI 0.139.0 가능하나 project 의 python 3.12 spec 과 transitive deps 불일치
- **honest-DEFER**: K-4 wire 1 에서 test file NEW + syntax validation 만 수행. runtime pytest execution 은 operator 환경 (project venv activated) 에서 실행 결정 wire 보류.
- **차후 K-4 wire 1.1 결정 보류** — operator 환경 에서 `pytest tests/api/smoke/ -v` 실행 + blocker surface + 결과 capture.

## §4 PRD §F cross-section 정합 (간접 검증)

| Smoke test case | PRD §F reference | K-3 chunk cross-ref |
|-----------------|------------------|---------------------|
| test_auth_signup_router_registered | §F15.1 + §F15.2 (Auth + Signup) | K-3 chunk 1 UJ-1 + K-3 chunk 3 §F15 |
| test_m0_onboarding_signup_response_model_exists | §F15.4 NFR18 (ko-KR SSOT) + §F0 (Onboarding 4-step) | K-3 chunk 4 NFR18 |
| test_m1_baseline_endpoints_have_crud_methods | §F1 (기준정보 CRUD) | K-3 chunk 2 M1 |
| test_m2_input_router_registered (v2 prefix) | §F2 (월데이터입력 v2) | K-3 chunk 2 M2 |
| test_m3_calculate_dual_route_capability_support | §F3 + §F9 (M3 + AD-19 dual-route) | K-3 chunk 2 M3 + K-3 chunk 3 §F9 |
| test_m5_reports_router_registered | §F5 (손익보고서) | K-3 chunk 2 M5 |
| test_m8_budget_scenarios_router_registered | §F8 (예산시나리오) | K-3 chunk 2 M8 |
| test_m9_abc_router_registered | §F9 (ABC) | K-3 chunk 2 M9 |
| test_audit_log_router_registered | §F21 (Audit Log) | K-3 chunk 3 §F21 |
| test_export_csv_endpoint_exists | §F30.1 (Epic 30+ Export) | K-3 chunk 3 §F30.1 + K-3 chunk 5 §F30 |

모두 capability matrix v1.54 EXTENSION + K-3 chain 5/5 DONE 결과 와 정합 보존.

## §5 runtime impact + verify gate

**runtime = PROD source 변경 0건**:
- ✅ 0 source 변경 (test file NEW only)
- ✅ 0 test 변경 (NEW tests 추가, 기존 tests untouched)
- ✅ 0 alembic 변경
- ✅ 0 PRD 변경
- ✅ 0 capability matrix 변경 (K-4 wire 1 scope 외, honestly DEFER 보류)
- ✅ 0 migration source 변경
- ✅ 37 pins unchanged (no package files touched)
- ✅ 14 job matrix unchanged
- ✅ PRD v7.0 §F/§M/§R unchanged
- ✅ capability matrix v1.54 EXTENSION preserved
- ✅ audit actions EXTENSION preserved
- ✅ AD-14 stack pin EXTENSION preserved

**Test file static verification (본 sprint 진입 시점)**:
- ✅ `tests/api/smoke/__init__.py` Python syntax valid (empty)
- ✅ `tests/api/smoke/conftest.py` Python syntax valid (ast.parse OK)
- ✅ `tests/api/smoke/test_mvp_critical_smoke.py` Python syntax valid (ast.parse OK)
- ✅ 27 test functions detected (`grep -c "^def test_"`)
- ✅ Test names follow `test_<flow>_<aspect>_<expected>` convention

**runtime execution honestly DEFER 보존**:
- operator 환경 (project venv activated + .env SUPABASE_*) 에서 `pytest tests/api/smoke/ -v` 실행 결정 wire 보류
- pytest 결과 (pass/fail/error/blocker) capture protocol = K-4 wire 1.1 진입 시 결정

## §6 Decision wire 보존 + 결정 보류 (운전자)

**결정 보류 (운전자, 본 sprint 후속)**:
- **K-4 wire 1.1 진입 결정 보류** — runtime pytest execution + blocker surface (~30min, project venv 환경)
- **K-4 wire 1.2+ blocker-bug-fix 결정 보류** — K-4 wire 1.1 의 blocker 결과 분석 후 option γ scoped 진입
- **capability matrix EXTENSION 결정 보류** — K-4 wire 1 의 smoke test 결과를 capability matrix v1.55 EXTENSION 으로 반영 결정 wire 보류
- **테스트 coverage 확장 결정 보류** — 현재 27 cases → 50-100 cases 확장 시점 결정 wire 보류 (K-4 entry spec 의 10 flows × 5-10 cases 목표)
- **operator 환경 runtime verification 결정 보류** — pytest 실제 실행 환경 + DB + Sentry emulator 준비 결정 wire 보류

## §7 K-3 chain + K-4 entry cross-references

**K-3 → K-4 chain 종합 정합 보존**:
- K-3 = PRD ↔ capability matrix v1.54 EXTENSION ↔ source code 정합 검증 (docs-only level)
- K-4 = runtime-level 검증 (system level, MVP-critical flows 의 actual 동작 검증)
- K-3 → K-4 = **level transition**: docs-level → runtime-level (K-4 entry decision wire 의 `K-3 → K-4 level transition` 결정 wire 보존)
- 본 K-4 wire 1 = **runtime smoke test entry** (10 flows 의 lightweight router-level smoke, full request/response 검증은 wire 2+)

**MVP-critical 10 flows Cross-ref (K-3 chain 5/5 결과 활용)**:
- Auth (K-3 chunk 1 UJ-1 + chunk 3 §F15) ✅ PASS
- M0 Onboarding (K-3 chunk 2 M0 + chunk 3 §F15.4) ✅ PASS
- M1 기준정보 (K-3 chunk 2 M1) ✅ PASS
- M2 월데이터입력 (K-3 chunk 2 M2) ✅ PASS
- M3 원가계산엔진 (K-3 chunk 2 M3 + chunk 3 §F9 dual-route) ✅ PASS
- M5 손익 (K-3 chunk 2 M5) ✅ PASS
- M8 예산 (K-3 chunk 2 M8) ✅ PASS
- M9 ABC (K-3 chunk 2 M9 + chunk 3 §F9) ✅ PASS
- Audit log (K-3 chunk 3 §F21) ✅ PASS
- Export CSV (K-3 chunk 3 §F30 + chunk 5 §F30) ✅ PASS

**66/66 cumulative 결정 wire 보존** (K-4 entry decision wire 의 65 + **NEW 66번째 K-4 wire 1 smoke test entry**).

**CR 11-3 honest-DEFER 294번째** chain cj-282 (220번째) → ... → K-4 entry decision wire (293번째, commit `23ece93`) → **K-4 wire 1 smoke test entry (294번째, 본 sprint)**.

## §8 PRE-EXISTING honestly DEFER carryover 보존

**PRE-EXISTING honestly DEFER carryover 보존**:
- cj-303 4건 (D-FINOPS-13 + audit-fixes + Layer 2 P1 + Layer 3 P2 docs)
- PRE-EXISTING 6건 (web-e2e Playwright + test-suite-measure 잔여 + web-test + lint-conventions + Sentry + custom DNS)
- cj-307 carryover LOW RISK ~30건 (Phase 10 SLO family, batch B 결정 wire 보류)
- sso 13 skipped tests (PRE-EXISTING missing python3-saml) honestly DEFER
- W1~W8 carryover honestly DEFER
- epics.md triage + PRD v2 EXTENSION 결정 wire 보류
- 비용 발생 항목 모두 (Railway/Vercel/Resend/Supabase/Sentry/Custom DNS, launch day 결정) honestly DEFER

**신규 honestly DEFER (K-4 chain 보존, 본 sprint 추가)**:
- K-4 wire 1.1 runtime pytest execution (operator 환경 결정 wire 보류)
- K-4 wire 1.2+ blocker-bug-fix (K-4 wire 1.1 blocker 결과 분석 후 결정 wire 보류)
- capability matrix v1.55 EXTENSION (K-4 wire 1 결과 반영 결정 wire 보류)
- 테스트 coverage 확장 (27 → 50-100 cases, 결정 wire 보류)
- operator 환경 runtime verification 환경 준비 결정 wire 보류
- K-3 chunk 1/2/3/4/5 결정 보류 (옵션 β·γ) + 디자인가이드 + 옵션 β 전체 + 옵션 γ 전체 결정 보류 그대로 보존
- M10 AI + M11 마감이력 + M12 계정운영 (Non-MVP, K-4 explicit deferral) 결정 보류 그대로 보존

**결정 wire 일자**: 2026-09-11 (KST, D-3, Pilot W1 launch D-day 2026-09-14 KST Mon 까지 3일).
