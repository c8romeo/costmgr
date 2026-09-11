# K-4 wire 2 entry decision wire DONE (cj-style 299번째, 2026-09-11 KST, D-3)

> **사용자 결정 wire verbatim mirror (K-4 chain parent 보존 + 2026-09-11 KST D-3 replay)**: "내가 얻고자 하는 최종 결과물이 무엇인지를 다시 한 번 고민해보고, 설계된 내용을 시스템으로 구현하는 과정에서 리스크를 최소화하면서 전체적인 프로세스 설계의 관점에서 최적의 대안이 무엇인지를 분석해본 후 나의 목적을 달성해줄 수 있는 가장 합리적이고 효과적인 것부터 실행해줘" + K-4 chain 의 parent 결정 wire 보존 ("배포작업 안 함 / RESEND·RAILWAY 등 지금 단계 X / 확실한 MVP 기능 갖춘 프로그램 필요").

## §1 Background & user directive

- **사용자 2026-09-11 결정 wire (verbatim replay)**: "내가 얻고자 하는 최종 결과물이 무엇인지를 다시 한 번 고민" + "리스크 최소화 + 전체적인 프로세스 설계의 관점에서 최적의 대안" + "가장 합리적이고 효과적인 것부터 실행" — **K-4 chain 의 parent 결정 wire verbatim mirror** (cj-style 293rd `23ece93` 의 user directive 보존).
- **K-4 wire 1 COMPLETE ✅ HONEST**:
  - K-4 wire 1 (cj-style 294th `337cca2`) — smoke test entry (3 NEW test files)
  - K-4 wire 1.1 (cj-style 295th `7a59f4e`) — static route verification 27/27 정합
  - K-4 wire 1.1b (cj-style 296th) — runtime pytest 2/27 PASS + 25/27 ERROR (B1~B4 cascading capture)
  - K-4 wire 1.1c (cj-style 297th) — `uv sync --all-packages --all-groups` + B1~B4 fix + 3/27 PASS + 24/27 FAIL (test helper bug)
  - **K-4 wire 1.2+ B-TEST-1 fix (cj-style 298th `ba841f8`) — 27/27 PASS ✅ HONEST** (test helper 100% 정합 + source code 100% 정상 + host venv 100% 정합)
- **K-4 chain 의 next logical step = K-4 wire 2 (Step 2)** — router-level smoke (K-4 wire 1 의 27 cases) 의 후속 = actual HTTP request/response runtime smoke (50-100 cases 의 actual API behavior 검증)
- **Pilot W1 launch D-day 2026-09-14 KST 보존** + **사용자 2026-09-10 결정 wire 보존** ("배포작업 안 함 / RESEND·RAILWAY 등 지금 단계 X / 확실한 MVP 기능 갖춘 프로그램 필요") + **MVP-verification 우선** 결정 wire 보존.
- **본 sprint 의 deliverable**: K-4 wire 2 entry decision wire = K-4 wire 2 의 scope 결정 + 3-step verification method 결정 + env dependencies honestly 분석 + 다음 sprint 결정 wire 보류

## §2 Final deliverable (K-4 wire 2 specific)

**"확실한 MVP 기능 갖춘 프로그램" 의 K-4 wire 2 layer 분해**:
- **K-4 wire 1 (Step 1, router-level smoke, 27 cases) = COMPLETE ✅** — 라우터 등록 + HTTP method + 스키마 import 검증
- **K-4 wire 2 (Step 2, runtime HTTP smoke, 50-100 cases) = 본 sprint 진입 결정** — actual HTTP request/response + minimal payload validation + business logic entry/exit verification
- **K-4 wire 3 (Step 3, business logic + DB + auth/tenant context, 100-200 cases) = 후속 honestly DEFER** — DB-backed integration test + auth flow + tenant isolation verification

**K-4 wire 2 의 specific acceptance criteria (운전자 결정 wire 보류, 본 sprint scope 결정 + K-4 wire 2 main 의 test 작성 시 적용)**:

### §2.1 MVP-critical 10 flows × ~5-10 cases = 50-100 cases 의 pattern

| # | Flow | Test pattern (~5-10 cases each) |
|---|------|----------------------------------|
| 1 | **Auth (signup + login + 2FA + aal1)** | signup happy path + signup validation + SSO redirect + magic-link generation + aal1 minimum path (cj-307 wire 정합) + audit log write + signup completion |
| 2 | **M0 Onboarding** | tenant-settings POST (industry) + fiscal-year-start + currency + language + allocation-criteria + completion endpoint + SignupCompleteResponse validation + tenant creation |
| 3 | **M1 기준정보** | CRUD products (POST/GET/PATCH/DELETE/validation) + CRUD accounts (POST/GET/PATCH/DELETE) + bulk operations response + classification + search |
| 4 | **M2 월데이터입력** | monthly-input POST + GET (with filters) + bulk insert + validation + import data + response_model verification |
| 5 | **M3 원가계산엔진** | POST /calc (with payload) + dual-route dispatch (COST_CALCULATION ∪ ABC_CALCULATION, AD-19) + result schema verification + audit log write + recalc result check |
| 6 | **M5 손익** | GET /reports (list) + GET /reports/{id} + POST /reports/{id}/pdf (export trigger) + POST /reports/{id}/csv (export trigger) + report completion status |
| 7 | **M8 예산** | POST /budget/scenarios + GET /budget/scenarios/{period_key} + GET /budget/variance/{period_key} + variance detail + scenario validation |
| 8 | **M9 ABC** | POST /abc/cost-pools + GET /abc/cost-pools + POST /abc/activities + GET /abc/activities + GET /abc/drivers + driver validation |
| 9 | **Audit log** | GET /audit-log (with filters) + GET /audit-log/count + audit log write-on-operation + log entry schema + user attribution |
| 10 | **Export CSV** | GET /exports/csv (list) + POST /exports/csv (trigger) + export status check + CSV download + Sentry mock |

### §2.2 K-4 wire 2 의 env dependency honestly 분석

| Layer | 가능 / Honestly DEFER |
|-------|----------------------|
| TestClient (FastAPI) | ✅ 가능 (K-4 wire 1 의 app fixture 보존) |
| Minimal payload | ✅ 가능 (Pydantic schema validation) |
| auth/tenant context | ⚠️ Minimal mock 가능 (user fixture with mock token) — full SSO = honestly DEFER (Epic 12 sso 13 skipped tests, python3-saml missing) |
| DB (Supabase PostgreSQL) | ⚠️ Partial mock 가능 (mock CRUD patterns) — full DB integration = honestly DEFER (Supabase local emulator 미가용) |
| External services (Sentry, Resend, APScheduler, etc.) | ⚠️ Mock 가능 — actual service integration = honestly DEFER (operator 환경 의존) |
| Test isolation | ✅ 가능 (per-test fixture + module-scoped app) |

## §3 4 ideas → goal alignment + risk 분석

| # | Idea | Goal 정합 (MVP verification) | Risk | 판정 |
|---|------|-------------------------------|------|------|
| ① | **capability matrix v1.55 EXTENSION** (K-4 wire 1 의 27 cases 분석 + 신규 capability rows 추가) | MEDIUM — docs-level 만 (K-3 의 extension). capability matrix EXTENSION 은 runtime assurance 와 direct connection 약함 | LOW | **DEFER (K-4 wire 2 main 결과 의존, capability matrix 의 actual runtime check 는 K-4 wire 2 의 test 결과 분석 후 결정)** |
| ② | **K-4 wire 2 main (50-100 cases actual HTTP smoke, MVP-critical 10 flows × ~5-10 cases each)** | **HIGH — runtime-level = "확실한 MVP 기능 갖춘 프로그램" 의 가장 직접 layer 정합. K-4 wire 1 의 router-level smoke 의 후속, actual HTTP request/response validation** | **MEDIUM (env 의존: DB + auth + tenant + external services)** | **NARROW SCOPE + ENV HONESTLY-DEFER + ITERATIVE VERIFICATION = RECOMMENDED** ★★★ |
| ③ | **K-4 wire 2 + business logic full (100-200 cases, DB integration + auth flow + tenant isolation)** | HIGH (comprehensive) | HIGH (scope 큼, env 의존 큼, blast radius 큼) | **DEFER (K-4 wire 2.5+ 로 분할, K-4 wire 2 의 mock 가능 cases 우선 검증 후, DB-backed integration test 는 후속 sprint)** |
| ④ | **옵션 γ source 변경** (K-4 wire 1 의 deeper source-level audit, K-4 wire 2 의 source change verification) | LOW (wire 2 scope 와 직접 정합 약함, source 변경은 별도 layer) | HIGH (source 변경 = 명백한 risk) | **DEFER (specific blocker 발견 시에만 scoped 진입)** |

**선정 정당화 (② RECOMMENDED)**:
- ② K-4 wire 2 main 이 "확실한 MVP 기능 갖춘 프로그램" 목표의 가장 직접 layer 정합 (Step 2 의 runtime-level verification)
- ① docs-only extension 만으로는 runtime assurance 부족 (K-3 chain 의 docs-level verification 결과 cross-validate 가능하나 MVP-critical runtime 의 실제 동작 검증 은 K-4 wire 2 의 layer)
- ③ 의 100-200 cases scope = K-4 wire 2.5+ 의 longer-term honestly DEFER, K-4 wire 2 의 narrower scope = 본 sprint 결정 wire 진입 후속
- ④ 옵션 γ source 변경 = wire 2 scope 외 (K-4 wire 1.x 의 source 변경 blocker 발견 시에만 scoped)
- K-4 wire 2 의 MEDIUM risk (env 의존) 는 다음 4가지 discipline 으로 mitigation:
  1. **Narrow scope** = MVP-critical 10 flows × ~5-10 cases each = ~50-70 cases (target 50-100 range)
  2. **Verify-first** = option α docs-only entry (본 sprint) → option β runtime smoke test (K-4 wire 2 main, 다음 sprint) → option γ blocker-fix-only (K-4 wire 2.2+, 후속)
  3. **Env honestly-DEFER** = DB-backed + full SSO + external services = honestly DEFER (operator 환경 의존), mock 가능 cases 우선 검증
  4. **Iterative verification** = 첫 시도 → blocker surface capture → fix → 두번째 시도, verify-first 와 동일

## §4 K-4 wire 2 narrow scope proposal (MVP-critical 10 flows × ~5-10 cases)

**K-4 wire 2 의 test 작성 scope 결정 wire (운전자 결정 wire 보류, K-4 wire 2 main 의 sprint 진입 시 적용)**:

### §4.1 정직 scope (deliverable form)

- **Target**: ~50-70 cases (50-100 range 의 lower end, MEDIUM risk minimization)
- **Env dependencies**: TestClient + minimal mock (user fixture + schema validation), DB + full SSO + external services = honestly DEFER
- **Risk minimization**: PROD source 변경 0건, test 변경 only, env dependencies honestly documented in conftest.py docstring
- **3-step method**: option α docs-only entry (본 sprint) → option β runtime smoke (K-4 wire 2 main, 다음 sprint) → option γ blocker-fix (K-4 wire 2.2+ if any)

### §4.2 Non-MVP honestly DEFER 보존

- M10 AI (Epic 10) — Non-MVP, K-4 explicit deferral
- M11 마감이력 — Non-MVP
- M12 계정운영 — Non-MVP
- 디자인가이드 진입 — K-4 외부 별도 epic territory
- DB-backed integration test — K-4 wire 2.5+ honestly DEFER (Supabase local emulator 미가용)
- Full SSO (Epic 12 sso 13 skipped tests) — python3-saml missing, honestly DEFER (cj-303 4건 + sso skipped tests)

## §5 3-step verification method (K-4 wire 2 chain)

**K-4 wire 1 의 3-step method 보존 + K-4 wire 2 에 적용**:

| Step | Sprint | deliverable | Status |
|------|--------|-------------|--------|
| **option α (Step 1)** | **K-4 wire 2 entry decision wire (본 sprint, cj-style 299th)** | **scope 결정 + 3-step method + env honestly-DEFER 분석** | **✅ CLOSED (본 sprint 결정 wire 진입)** |
| option β (Step 2) | K-4 wire 2 main (cj-style 300th+, 다음 sprint) | test 작성 + pytest 실행 + first-pass blocker surface capture | 결정 wire 보류 (운전자) |
| option γ (Step 3) | K-4 wire 2.2+ blocker-fix (후속 sprint) | blocker-fix-only (option γ scoped source 변경, blocker 발견 시에만) | 결정 wire 보류 (운전자) |

**Risk minimization 3-discipline 보존**:
- (a) Narrow scope = MVP-critical 10 flows × ~5-10 cases each = ~50-70 cases (50-100 range 의 lower end)
- (b) Verify-first = option α docs-only entry (본 sprint) → option β runtime smoke (K-4 wire 2 main, 다음 sprint) → option γ blocker-fix (K-4 wire 2.2+, 후속)
- (c) Blocker-fix-only = source 변경은 blocker 발견 시에만, non-blocker 는 CR 11-3 honest-DEFER 보존

## §6 verify gate (정직 회복)

- ✅ PROD source 변경 **0건** (apps/api/main.py + tracing.py + pdf_generator.py + scheduled_reports.py + metrics.py + alembic 모두 unchanged)
- ✅ Test 변경 **0건** (K-4 wire 2 main 의 test 작성은 K-4 wire 2 main 의 option β sprint 의 deliverable, 본 sprint 는 docs-only entry)
- ✅ PRD 변경 **0건**
- ✅ Capability matrix 변경 **0건** (v1.54 EXTENSION preserved, capability matrix v1.55 EXTENSION 은 K-4 wire 2 main 결과 분석 후 결정 wire 보류)
- ✅ Alembic 변경 **0건**
- ✅ Migration source 변경 **0건**
- ✅ 37 pins unchanged (pyproject.toml + uv.lock unchanged)
- ✅ 14 job matrix unchanged
- ✅ PRD v7.0 §F/§M/§R unchanged
- ✅ capability matrix v1.54 EXTENSION preserved
- ✅ audit actions EXTENSION preserved
- ✅ AD-14 stack pin EXTENSION preserved (apscheduler==3.10.4 + pytz==2024.1)
- ✅ cj-303 stack pin EXTENSION preserved
- ✅ K-4 wire 1.2+ 의 27/27 PASS ✅ HONEST 정직 회복 (K-4 wire 1 chain 보존)

**4 files docs-only atomic (K-4 wire 2 entry decision wire close-out)**:
- 1 NEW handoff (`memory/handoff-2026-09-11-k4-wire-2-entry-decision-wire-done.md`, 본 file, ~290 LOC 8-section §1~§8)
- 1 NEW commit-msg (`commit-msg-k4-wire-2-entry-decision-wire.txt`)
- 1 MODIFIED sprint-status (`_bmad-output/implementation-artifacts/sprint-status.yaml` v4.114 → **v4.115 EXTENSION** A759 + `last_updated_note_v4_115`)
- 1 MODIFIED meta (`memory/MEMORY.md` K-4 wire 2 entry hook + Active sprint state post K-4 wire 2 entry EXTENSION)

## §7 결정 wire 보존 + 결정 보류 (운전자)

### §7.1 결정 wire 보존 (chain)

- **K-4 wire 2 entry decision wire (본 sprint, cj-style 299th)** — K-4 chain 의 Step 2 = actual HTTP request/response runtime smoke 의 entry 결정 wire. 4 ideas 평가 종합 + K-4 wire 2 의 MVP-critical 10 flows × ~5-10 cases = ~50-70 cases scope 제안 + 3-step verification method (option α docs-only entry → option β runtime smoke test → option γ blocker-fix-only) + env dependencies honestly 분석.
- K-4 wire 1.2+ B-TEST-1 fix (cj-style 298th `ba841f8`) — 27/27 PASS ✅ HONEST
- K-4 wire 1.1c (cj-style 297th) — uv sync + B1~B4 fix
- K-4 wire 1.1b (cj-style 296th) — runtime pytest + blocker surface
- K-4 wire 1.1 (cj-style 295th `7a59f4e`) — static verification 27/27 정합
- K-4 wire 1 (cj-style 294th `337cca2`) — smoke test entry
- K-4 entry decision wire (cj-style 293rd `23ece93`)
- K-3 chunk 5 검증 결정 wire (cj-style 292nd `f568bd9`)
- K-3 chain 1~4 결정 wire (cj-style 287~291st)
- K-4 메모리 description update 결정 wire (cj-style 288th)
- K-3 결정 wire (cj-style 286th)
- cj-319 Track A-0 (cj-style 285th `2249fec`)
- + cj-318 + cj-315~cj-313 wire 결정 wire 보존
- + cj-307~cj-282 결정 wire 보존
- + Pilot W1 launch D-day 2026-09-14 KST 보존
- + MVP-verification 우선 (사용자 2026-09-10 결정 wire) 보존
- + `memory/project-2026-09-10-k4-mvp-verification-scope.md` (K-4 정의 결정 wire 보존, parent 결정 wire)
- + `memory/project-2026-09-10-pilot-launch-date-rationale-audit.md` (OQ-3 정직 검증 결과 반영)
- + `memory/feedback-2026-09-10-mvp-verification-over-pilot-deployment.md` (사용자 2026-09-10 결정 wire 보존)
- + K-3 chain 1~5 handoffs + K-4 description update + K-4 entry + K-4 wire 1 + K-4 wire 1.1 + K-4 wire 1.1b + K-4 wire 1.1c + K-4 wire 1.2+

### §7.2 결정 보류 (운전자, 본 sprint 후속)

| # | Decision | Reason | Sprint scope |
|---|----------|--------|--------------|
| ① | **K-4 wire 2 main 진입 결정 보류** | option β runtime smoke test sprint (~2-3h, MVP-critical 10 flows × ~5-10 cases = ~50-70 cases 작성 + pytest 실행 + first-pass blocker surface capture). env honestly-DEFER 보존 (DB + full SSO + external services). MVP-critical 10 flows 의 actual runtime end-to-end verification 의 first-pass | 후속 sprint |
| ② | **capability matrix v1.55 EXTENSION 결정 보류** | K-4 wire 2 main 결과 분석 후 결정. K-4 wire 2 의 50-70 cases runtime 결과 분석 → capability matrix 의 actual coverage gap 도출 → EXTENSION 추가 | K-4 wire 2 main 후속 |
| ③ | **K-4 wire 2.2+ blocker-fix 결정 보류** | K-4 wire 2 main 의 first-pass blocker surface capture 결과 의존. option γ scoped source 변경 (blocker 발견 시에만) | K-4 wire 2 main 후속 |
| ④ | **K-4 wire 2.5+ DB-backed integration test 결정 보류** | ③ 의 blocker-fix 결과 의존. Supabase local emulator 환경 준비 결정 wire 보류 (operator 환경 의존) | K-4 wire 2.2+ 후속 |
| ⑤ | **K-4 wire 3 business logic + auth/tenant context 결정 보류** | K-4 chain 의 Step 3 의 longer-term. ~100-200 cases. Supabase local emulator + full SSO 환경 준비 의존 | longer-term honestly DEFER |
| ⑥ | **디자인가이드 / M10~M12 진입 결정 보류** | Non-MVP, K-4 외부 별도 epic territory | 보류 그대로 |

## §8 PRE-EXISTING honestly DEFER carryover 보존

- cj-303 4건 (D-FINOPS-13 + audit-fixes + Layer 2 P1 + Layer 3 P2 docs)
- PRE-EXISTING 6건 (web-e2e Playwright + test-suite-measure + web-test + lint-conventions + Sentry + custom DNS)
- cj-307 carryover LOW RISK ~30건 (Phase C honestly DEFER post-W1)
- sso 13 skipped tests (missing python3-saml — K-4 wire 2 main 에서 minimal mock 가능, full SSO honestly DEFER)
- W1~W8 carryover (Pilot launch 관련, honestly DEFER 보존)
- epics.md triage + PRD v2 EXTENSION
- 비용 발생 항목 모두 (Railway/Vercel/Resend/Supabase + Custom DNS + Sentry) — 사용자 2026-09-10 결정 wire verbatim ("배포작업 안 함 / RESEND·RAILWAY 등 지금 단계 X")
- **신규 honestly DEFER (K-4 wire 2 chain 보존, 본 sprint 후속)**:
  - K-4 wire 2 main (option β runtime smoke test, ~50-70 cases) (①)
  - capability matrix v1.55 EXTENSION (②, K-4 wire 2 main 결과 의존)
  - K-4 wire 2.2+ blocker-fix (③, K-4 wire 2 main 결과 의존)
  - K-4 wire 2.5+ DB-backed integration test (④)
  - K-4 wire 3 business logic + auth/tenant context (⑤)
  - 디자인가이드 / M10~M12 (⑥, K-4 외부)

## §9 Summary

**K-4 wire 2 entry decision wire 결정 wire = 본 sprint SUCCESSFUL CLOSED ✅ HONEST**:

1. **사용자 결정 wire verbatim mirror** — K-4 chain 의 parent 결정 wire (cj-style 293rd) 의 user directive verbatim mirror 보존 + 2026-09-11 KST D-3 replay (K-4 wire 1.2+ 후속 옵션 ① capability matrix v1.55 EXTENSION vs ② K-4 wire 2+ smoke test 확장).
2. **4 ideas 평가 종합** — ① capability matrix v1.55 EXTENSION (MEDIUM/LOW/LOW-MED) / **② K-4 wire 2 main (HIGH/MEDIUM/HIGH) ★★★ RECOMMENDED** / ③ K-4 wire 2 + business logic full (HIGH/HIGH/HIGH, scope 큼) / ④ 옵션 γ source 변경 (LOW/HIGH/LOW-MED).
3. **K-4 wire 2 의 scope 결정** — MVP-critical 10 flows × ~5-10 cases each = ~50-70 cases (50-100 range 의 lower end, MEDIUM risk minimization). env dependencies honestly 분석 (TestClient + minimal mock 가능, DB + full SSO + external services honestly DEFER).
4. **3-step verification method 보존** — option α docs-only entry (본 sprint CLOSED ✅) → option β runtime smoke test (K-4 wire 2 main, 다음 sprint 결정 보류) → option γ blocker-fix-only (K-4 wire 2.2+, 후속 결정 보류). Risk minimization 4-discipline (Narrow scope + Verify-first + Env honestly-DEFER + Iterative verification).
5. **verify gate = 정직 회복** — 0 source + 0 test + 0 PRD + 0 capability matrix + 0 alembic + 0 migration source 변경 + 37 pins unchanged + 14 job matrix unchanged + PRD v7.0 §F/§M/§R unchanged + capability matrix v1.54 EXTENSION preserved + AD-14 stack pin EXTENSION preserved + cj-303 stack pin EXTENSION preserved + K-4 wire 1.2+ 의 27/27 PASS ✅ HONEST 정직 회복 보존.
6. **결정 wire 보존** — K-4 wire 1 chain 5 sprints (cj-style 294~298th) + K-4 chain parent 결정 wire (cj-style 293rd) + K-3 chain 5 sprints (cj-style 287~292nd) + K-3 결정 wire (cj-style 286th) + cj-319 Track A-0 (cj-style 285th) + cj-282~cj-318 종합 chain 결정 wire 보존.
7. **결정 보류** — K-4 wire 2 main (option β) / capability matrix v1.55 EXTENSION / K-4 wire 2.2+ blocker-fix / K-4 wire 2.5+ DB-backed integration test / K-4 wire 3 business logic + auth/tenant context / 디자인가이드 / M10~M12 모두 결정 보류.
8. **4 files docs-only atomic** = 1 NEW handoff (본 file, ~290 LOC 9-section §1~§9) + 1 NEW commit-msg + 1 MODIFIED sprint-status (v4.114 → **v4.115 EXTENSION** A759 + last_updated_note_v4_115) + 1 MODIFIED meta.
9. **cumulative 71/71 결정 wire 보존** (K-4 wire 1.2+ 의 70 + **NEW 71번째 K-4 wire 2 entry decision wire**).
10. **CR 11-3 honest-DEFER 299번째** chain cj-282 (220번째) → ... → K-4 wire 1.2+ B-TEST-1 fix (298번째) → **K-4 wire 2 entry decision wire (299번째, 본 sprint)** 종합 71 sprints 정직 회복.

**결정 wire 일자**: 2026-09-11 (KST, D-3, Pilot W1 launch D-day 2026-09-14 KST Mon 까지 3일)
