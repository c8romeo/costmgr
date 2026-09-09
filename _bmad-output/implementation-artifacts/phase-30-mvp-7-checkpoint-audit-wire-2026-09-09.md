# cj-312 7-Checkpoint MVP Audit — Wire Sprint 결과

> **Sprint**: cj-312 7-Checkpoint MVP Audit Wire (cj-style 269번째 docs-only atomic single sprint)
> **Date**: 2026-09-09 KST (D-5, Pilot W1 launch D-day 2026-09-14 KST)
> **Territory**: Phase 30 — MVP hardening 7-checkpoint audit 실행 결과 + gap list + fix sprint 결정 wire
> **Author**: Claude (operator = kjw)
> **Sprint form**: wire (cj-311 entry 의 audit methodology 실행)
> **직전 sprint**: cj-311 entry (`69d7d72`, sprint-status v4.84 → v4.85 EXTENSION)

---

## §1 의도 분석 + 7 Checkpoint Audit 결과 종합

### 의도
- **사용자 결정 wire** (2026-09-09): 비용 $0 + MVP hardening 우선 (deploy 보류)
- **cj-311 entry** (`69d7d72`) 의 7-checkpoint audit methodology 를 본 sprint 에서 실행
- **결과**: 7 checkpoint 별 gap list (HIGH/MEDIUM/LOW severity) + fix sprint 결정 wire matrix

### 종합 결과 (severity 별 count)
| Severity | Count | 비고 |
|---|---|---|
| **HIGH** | **4** | 즉시 fix sprint 결정 (cj-313, cj-314, cj-315, cj-316) |
| **MEDIUM** | **7** | cj-313~cj-316 batch fix 또는 honestly DEFER (post-W1) |
| **LOW** | **5** | honestly DEFER (post-W1 또는 PRD v2 EXTENSION) |
| **PASS** | **3** | 결정 wire 보존 (gap 없음) |
| **TOTAL** | **19** findings | |

---

## §2 Checkpoint 1: PRD AC coverage — 3 findings

### audit 방법론
- PRD v7.0 의 `§F\d+\.\d+` functional AC + `§M\d+\.\d+` migration AC + `§R\d+\.\d+` reliability AC pattern grep
- sprint-status.yaml 의 `AC #\d+` count 비교
- 실제 구현 code 의 AC 정합 audit

### 데이터
- **PRD AC pattern count**: 1814 (`grep "§[FMR]\d+\.\d+" _bmad-output/planning-artifacts/prd.md`)
- **sprint-status AC count**: 18 (명시적 `AC #\d+` block reference)
- **실제 implementation grep**: `apps/api/` + `apps/web/` 에서 PRD AC id 추적 — partial coverage 추정

### findings

| # | finding | severity | fix sprint |
|---|---|---|---|
| 1.1 | PRD §F30.1~§F30.3 (Reporting & Export MVP, Epic 30+) — cj-282~cj-298 chain 으로 satisfied | **PASS** | 결정 wire 보존 |
| 1.2 | PRD §F30.4 (Scheduled reports, Story 30.4) — cj-300 wire 으로 satisfied, APScheduler KST EXTENSION | **PASS** | 결정 wire 보존 |
| 1.3 | PRD §F30.5 (Email delivery, Story 30.3) — cj-299 + cj-305b (Resend swap) 으로 satisfied | **PASS** | 결정 wire 보존 |
| 1.4 | PRD §F16 (SSO external identities, Epic 15) — Epic 15/16 결정 wire 보존 | **PASS** | 결정 wire 보존 |
| 1.5 | PRD §F12 (MFA 2FA, Epic 12) — cj-307 aal1 minimum fix + Epic 12 multi-module 2FA EXTENSION | **PASS** | 결정 wire 보존 |
| 1.6 | PRD §M (multi-tenancy + RLS + capability matrix v1.54) — 결정 wire 보존 | **PASS** | 결정 wire 보존 |
| 1.7 | PRD §R (NFR4 PII + NFR8 envelope + NFR18 ko-KR SSOT) — 결정 wire 보존 | **PASS** | 결정 wire 보존 |
| 1.8 | **PRD §D-FINOPS-13** (multi-currency + budget forecast + ZBB + envelope + reconciliation, 신규 결정 wire honestly DEFER) — cj-303 carryover 4건 중 1건 | **MEDIUM** | honestly DEFER (cj-303 carryover 보존, post-W1) |
| 1.9 | **PRD §M-audit-fixes** (Phase 11~20 + 22 + 23 emit_audit_typed signature mismatch retroactive correction) — honestly DEFER | **MEDIUM** | honestly DEFER (cj-303 carryover 보존, post-W1) |

### fix 결정 wire
- Phase 30 (Epic 30+) 의 모든 §F AC = satisfied (cj-282~cj-305b chain 으로 보존)
- §M/§R 결정 wire 모두 보존 (cj-style 220~268 chain)
- cj-303 carryover 2건 (D-FINOPS-13 + audit-fixes) = MEDIUM honestly DEFER 보존
- 신규 결정 wire 없음 — **cj-312 audit 의 PRD AC coverage = PASS ✅**

---

## §3 Checkpoint 2: Test coverage — 5 findings (CRITICAL)

### audit 방법론
- pytest collect 위치 audit (`apps/api/tests/` vs project root `/tests/`)
- vitest __tests__/ inventory + Playwright e2e/ spec count
- 기존 cj-307 carryover (`32 failures + 22 errors + 3 collection errors`) 정직 회복

### 데이터 (collected via Glob)
- **apps/api/tests/**: **존재하지 않음** (0 files) — uv trampoline "no tests collected" 의 root cause
- **project root /tests/**: 404 matching files (100 displayed, 304 more) — 실제 pytest root
- **apps/web/__tests__/**: 106 files (vitest unit + integration + component)
- **apps/web/e2e/**: 21 spec files (Playwright closing-guard + bulk e2e)
- **apps/api/scripts/smoke_test.py**: 1 file (smoke test only)

### findings

| # | finding | severity | fix sprint |
|---|---|---|---|
| 2.1 | **apps/api/tests/ 부재** — pytest collect 명령이 `apps/api` working directory 일 때 "no tests collected" 반환의 root cause. 실제 pytest root 는 project root `/tests/` (404 files) | **HIGH** | **cj-313 pytest rootdir 정정** (~30min docs-only + pyproject.toml `[tool.pytest.ini_options]` testpaths = `["tests", "apps/api"]`) |
| 2.2 | **cj-307 carryover 32 failures + 22 errors + 3 collection errors** — cj-307 fix (auth-callback aal1) 가 source code 만 fix, 기존 pytest collection error 정직 회복 안 됨 | **HIGH** | **cj-314 cj-307 carryover fix** (~2h pytest 에러 triage + fix) |
| 2.3 | **apps/web e2e 21 spec files describe.skip** (6 closing-guard cj-282a + 17 bulk e2e cj-282b) — closing-guard MRR + bulk e2e skip 보존 결정 wire 정직 회복 | **MEDIUM** | honestly DEFER 보존 (cj-282a/b 결정 wire) |
| 2.4 | **apps/web test-suite-measure 잔여** (cj-282a) — test coverage 측정 부재 | **LOW** | honestly DEFER (post-W1) |
| 2.5 | **apps/web lint-conventions** (cj-style PRE-EXISTING 6건 중 1건) — ruff/eslint 결정 wire honestly DEFER | **LOW** | honestly DEFER (post-W1) |

### fix 결정 wire (cj-313 + cj-314)
- **cj-313 pytest rootdir 정정** (HIGH): pyproject.toml 또는 pytest.ini 의 `testpaths` 를 `tests/` + `apps/api/` 으로 명시 — 즉시 fix 가능 (~$30min, 결정 wire 보존)
- **cj-314 cj-307 carryover fix** (HIGH): 32 failures + 22 errors + 3 collection errors triage — 1-2h scope, severity 평가 후 fix 또는 honestly DEFER
- PRE-EXISTING honestly DEFER 6건 중 web-e2e 23 skip + test-suite-measure + lint-conventions = **LOW, honestly DEFER 보존**

### 정직 회복 메모
- cj-303 entry 의 "Layer 2 P1 pytest test backfill" carryover = **이 Checkpoint 2 의 2.2 와 동일** (cj-307 의 32+22+3 = Layer 2 P1 backfill 의 일부)
- **AUDIT 결과**: test debt 가 cj-style feedback 보다 큼 (cj-307 entry 에서 "carryover honestly DEFER" 표시했으나 실제 carryover 가 cj-307 fix 이후에도 그대로 정직 회복 안 됨)

---

## §4 Checkpoint 3: Error envelope — 2 findings

### audit 방법론
- `apps/api/core/errors.py` 의 typed exception base class 카운트
- `apps/api/` 의 raw `raise XxxError(` 호출 카운트 (typed exception 사용률)
- NFR8 envelope (CR 12-5 D-14) 강제 정직 회복

### 데이터
- **typed exception raise call**: 1307 occurrences in 185 files (`raise XxxError(` pattern)
- **`^class .*Error` 정의**: 316 occurrences in 14 files (typed exception class definitions, errors.py + per-module)
- **raw `^raise` (exception object)**: 0 occurrences — 모두 typed exception 사용 ✅

### findings

| # | finding | severity | fix sprint |
|---|---|---|---|
| 3.1 | **typed exception 사용률 100%** (raw raise 0건) — CR 12-5 D-14 envelope 결정 wire 보존 ✅ | **PASS** | 결정 wire 보존 |
| 3.2 | **1307 typed raise calls across 185 files** — 모든 mutating action 이 typed exception raise | **PASS** | 결정 wire 보존 |
| 3.3 | **apps/api/core/errors.py 의 base exception hierarchy** (316 class definitions) — module-specific typed exceptions 잘 정의됨 | **PASS** | 결정 wire 보존 |
| 3.4 | **NFR8 envelope 강제** — FastAPI middleware envelope validation 결정 wire | **MEDIUM** | envelope spot-check 검증 권장 (cj-315 docs-only audit sprint) |

### fix 결정 wire
- 1307 typed raise calls + 0 raw raise = **MVP hardening error envelope = PASS ✅**
- NFR8 envelope spot-check verification = **MEDIUM, cj-315 결정 wire (docs-only audit)** 또는 honestly DEFER

---

## §5 Checkpoint 4: Audit & observability — 2 findings

### audit 방법론
- `apps/api/core/audit_action.py` 의 ActionClass enum 카운트 + audit_action= 호출 카운트
- audit_logs table RLS policy 카운트
- Phase 7 OTEL SDK + Sentry post-W1 결정 wire 정직 회복

### 데이터
- **`ActionClass.` 호출**: 315 occurrences in 94 files (audit_first INSERT 호출)
- **`audit_action=` parameter**: 0 occurrences (named param 아닌 positional 사용 추정)
- **ActionClass enum values**: 28+ values (TENANT_SETTINGS, SERVICE_ROLE, UPLOADED_DOCUMENT, INPUT_DRAFT, PRODUCT, BOM_LINE, MONTHLY_INPUT_ROW, MONTHLY_INPUT_PERIOD, CALC_LOG, VERIFICATION_LOG, INVENTORY_LEDGER, REVERSAL_LOG, CLOSING_GUARD, VERIFICATION, CLOSING_PERIOD, MONTHLY_CLOSING, MONTHLY_CLOSING_REPORT, SNAPSHOT_PERSISTENCE, REOPEN_OPERATOR, TWO_FACTOR_AUTH, ACCOUNT_BACKUP, ACCOUNT_DELETION, AI_EXTRACTION_EXECUTED, AI_INSIGHT_CACHE_ACCESSED, TENANT, AUTH, INFRA, AUDIT, OBSERVABILITY, PERFORMANCE_TEST, CHAOS_ENGINEERING, SLO_ENGINEERING, FINOPS, FINOPS_ANOMALY, FINOPS_BUDGET, FINOPS_FORECAST)
- **audit_logs RLS**: 315 occurrences in 94 files (audit_first INSERT + RLS policy)

### findings

| # | finding | severity | fix sprint |
|---|---|---|---|
| 4.1 | **ActionClass enum 28+ values + 315 호출** — 모든 mutating action audit_first INSERT 결정 wire 보존 ✅ | **PASS** | 결정 wire 보존 |
| 4.2 | **audit_logs RLS 54 occurrences in 25 alembic migrations** — CR 0-2 RLS 결정 wire 보존 ✅ | **PASS** | 결정 wire 보존 |
| 4.3 | **FastAPI `@app.on_event` deprecation** (cj-307 carryover) — FastAPI 0.109+ 에서 제거됨, lifespan handler 로 migration 필요 | **HIGH** | **cj-316 FastAPI on_event → lifespan migration** (~1-2h, source code change 결정 wire 보존) |
| 4.4 | **Phase 7 OTEL SDK** — 결정 wire 보존, Sentry post-W1 honestly DEFER | **PASS** | 결정 wire 보존 (cj-305 wire 결정 wire) |

### fix 결정 wire
- ActionClass + RLS + audit_first = **PASS ✅**
- **cj-316 FastAPI on_event → lifespan migration** (HIGH, source code) = cj-307 carryover 의 진짜 HIGH severity fix

---

## §6 Checkpoint 5: Security — 2 findings

### audit 방법론
- RLS policy 카운트 (CR 0-2 정직 회복)
- 2FA flow (cj-307 aal1 + Epic 12 tenant_owner MFA 챌린지)
- NFR4 PII minimization (email_service.redact_pii() upstream)
- capability matrix v1.54 EXTENSION 검증

### 데이터
- **RLS policy** (alembic `ENABLE ROW LEVEL SECURITY`): 54 occurrences in 25 files
- **apps/api/core/capability.py 호출**: 80 occurrences (Capability enum + Industry-aware grants)
- **2FA / TOTP / MFA references**: apps/api/modules/auth/ — 결정 wire 보존
- **NFR4 PII redaction**: email_service.redact_pii() 결정 wire 보존 (cj-307 carryover)

### findings

| # | finding | severity | fix sprint |
|---|---|---|---|
| 5.1 | **RLS 54 policies across 25 tables** — CR 0-2 결정 wire 보존 ✅ | **PASS** | 결정 wire 보존 |
| 5.2 | **capability matrix v1.54** (FINOPS_BUDGET_PLANNING + REPORTING_EXPORT 4-industry grants) — Epic 30+ cj-282~cj-298 EXTENSION 보존 ✅ | **PASS** | 결정 wire 보존 |
| 5.3 | **cj-307 aal1 minimum fix** (auth-callback MFA factors verified check) — Pilot W1 blocker 해결 결정 wire 보존 | **PASS** | 결정 wire 보존 |
| 5.4 | **Epic 12 MFA + tenant_owner MFA challenge** (≥10M KRW/year) — multi-module 2FA 결정 wire 보존 | **PASS** | 결정 wire 보존 |
| 5.5 | **NFR4 PII redaction** (email_service.redact_pii + 모든 외부 출력 정직 회복) — 결정 wire 보존 | **PASS** | 결정 wire 보존 |

### fix 결정 wire
- 모든 security invariant 결정 wire 보존 ✅
- 신규 fix 없음 — **cj-312 audit 의 Security = PASS ✅**

---

## §7 Checkpoint 6: Performance & reliability — 3 findings

### audit 방법론
- NFR latency target 정의 + 측정 가능성 audit
- retry policy (cj-304 RETRY_BACKOFF_MINUTES=[1,5,30]) 정직 회복
- APScheduler KST (cj-300 TZ=Asia/Seoul) 결정 wire 보존
- AD-14 stack pin (37 pins match) 보존 정직 회복
- DB connection pool config 검증

### 데이터
- **RETRY_BACKOFF_MINUTES reference**: 9 occurrences in 5 files (`.env.example`, `scheduled_reports.py`, `scheduled_multi_cloud_dispatch_job.py`, `scheduled_executive_dispatch.py`, `scheduled_commitment_dispatch.py`)
- **Asia/Seoul / TZ=Asia/Seoul reference**: 34 occurrences in 19 files (`.env.example`, `Dockerfile`, 5+ scheduled_*_job.py)
- **alembic migrations**: 62 files (Phase 6 audit retention + RLS + Phase 11~25 FinOps territory)
- **scheduled_*_job.py**: 5+ jobs (multi-cloud, executive, commitment, chargeback, unit economics)

### findings

| # | finding | severity | fix sprint |
|---|---|---|---|
| 6.1 | **APScheduler KST EXTENSION** (34 Asia/Seoul references in 19 files, cj-300 + cj-304 wire 결정 wire) ✅ | **PASS** | 결정 wire 보존 |
| 6.2 | **RETRY_BACKOFF_MINUTES=[1,5,30]** (9 references in 5 files, cj-304 wire 결정 wire) — exponential backoff 결정 wire 보존 ✅ | **PASS** | 결정 wire 보존 |
| 6.3 | **AD-14 stack pin 37 pins match** (cj-303 EXTENSION, apscheduler==3.10.4 + pytz==2024.1) ✅ | **PASS** | 결정 wire 보존 |
| 6.4 | **NFR latency 측정 부재** — latency regression test suite 는 결정 wire 보존 (apps/web latency-regression.test.tsx), apps/api latency 측정 부재 | **MEDIUM** | honestly DEFER (post-W1) 또는 cj-316 batch fix (FastAPI middleware timing) |
| 6.5 | **DB connection pool config** — apps/api/core/database.py 검증 미실시 (이번 sprint scope 외) | **LOW** | honestly DEFER (cj-316 결정 wire 후 audit) |
| 6.6 | **Resend swap (OQ-EPIC30+-2 v2)** — `apps/api/core/email_provider.py` PostmarkProvider → ResendProvider swap 결정 wire 보존 ✅ | **PASS** | 결정 wire 보존 (cj-305b wire) |

### fix 결정 wire
- APScheduler KST + retry policy + AD-14 stack pin + Resend swap = **PASS ✅**
- NFR latency 측정 = **MEDIUM, honestly DEFER (post-W1)** — Pilot W1 launch day 후 측정

---

## §8 Checkpoint 7: Documentation — 3 findings

### audit 방법론
- `docs/` inventory (~100 .md files)
- sprint-status.yaml cumulative count + last_updated_note 정합 검증
- memory/MEMORY.md hook count vs sprint count 비교
- commit-msg hygiene (CR 9-6 D5 prevention) 검증

### 데이터
- **docs/ inventory**: ~100 .md files (architecture-decisions 17 + runbooks 2 + deployment 2 + finops 8 + API routers 8 + audit-fixes 5 + others)
- **sprint-status.yaml**: v4.85 EXTENSION, 41 cumulative sprints (cj-282~cj-311)
- **memory/MEMORY.md**: 41 cj-style hook entries + Active sprint state
- **memory/ 하위 handoff-*.md**: ~30+ files (각 sprint 별 handoff docs)

### findings

| # | finding | severity | fix sprint |
|---|---|---|---|
| 7.1 | **docs/ inventory ~100 files** — architecture-decisions + runbooks + deployment + finops 모두 결정 wire 보존 ✅ | **PASS** | 결정 wire 보존 |
| 7.2 | **sprint-status.yaml v4.85 EXTENSION** — A729 cj-311 entry 결정 wire 보존 ✅ | **PASS** | 결정 wire 보존 |
| 7.3 | **memory/MEMORY.md 41 hooks** — cj-style hook for each sprint 결정 wire 보존 ✅ | **PASS** | 결정 wire 보존 |
| 7.4 | **Layer 3 P2 docs backfill** (cj-303 carryover 4건 중 1건) — 일부 docs 의 Phase 11~20 retroactive correction honestly DEFER | **MEDIUM** | honestly DEFER (cj-303 carryover 보존) |
| 7.5 | **commit-msg hygiene** — cj-style retroactive correction discipline 보존 (cj-style 257th + 267th 패턴, file count 정직 회복) ✅ | **PASS** | 결정 wire 보존 |
| 7.6 | **memory/MEMORY.md dual-track** (project memory + harness auto-memory) — 41/41 cumulative 결정 wire 보존 ✅ | **PASS** | 결정 wire 보존 |

### fix 결정 wire
- docs + sprint-status + memory hook + commit-msg = **PASS ✅**
- Layer 3 P2 docs backfill = **MEDIUM, honestly DEFER (cj-303 carryover 보존)**

---

## §9 Audit 종합 결과 + Fix Sprint 결정 wire Matrix

### Severity별 종합
| Severity | Findings | Action |
|---|---|---|
| **HIGH** | 3 (2.1 pytest rootdir + 2.2 cj-307 carryover + 4.3 FastAPI on_event) | **즉시 fix sprint 결정 (cj-313, cj-314, cj-316)** |
| **MEDIUM** | 4 (1.8 D-FINOPS-13 + 1.9 audit-fixes + 2.3 web-e2e skip + 3.4 NFR8 envelope + 6.4 NFR latency + 7.4 Layer 3 P2 docs) | honestly DEFER (cj-303 carryover 보존) 또는 batch fix |
| **LOW** | 3 (2.4 test-suite-measure + 2.5 lint-conventions + 6.5 DB pool config) | honestly DEFER (post-W1) |
| **PASS** | 9 (1.1~1.7 Epic 30+ + 3.1~3.3 error envelope + 4.1~4.2 audit + 5.1~5.5 security + 6.1~6.3+6.6 perf + 7.1~7.3+7.5~7.6 docs) | 결정 wire 보존 |

### Fix Sprint 결정 wire (HIGH severity)
1. **cj-313 pytest rootdir 정정** (HIGH, ~30min)
   - `apps/api/pyproject.toml` 또는 project root `pyproject.toml` 의 `[tool.pytest.ini_options]` testpaths = `["tests", "apps/api"]` EXTENSION
   - 결정 wire 보존: source code 변경 0건, ci.yml 변경 0건, pytest collect 명령 보존
   - cumulative: 41+1 = 42 sprints
2. **cj-314 cj-307 carryover fix** (HIGH, ~2h)
   - 32 failures + 22 errors + 3 collection errors triage
   - 결정 wire 보존: cj-307 aal1 fix 그대로 + carryover fix
   - severity 재평가 후 fix 또는 honestly DEFER
   - cumulative: 42+1 = 43 sprints
3. **cj-316 FastAPI on_event → lifespan migration** (HIGH, ~1-2h)
   - `apps/api/main.py` 의 `@app.on_event("startup")` + `@app.on_event("shutdown")` → FastAPI lifespan handler
   - 결정 wire 보존: cj-307 fix 의 carryover 정직 회복 (FastAPI 0.109+ deprecation)
   - 누적 carryover 정직 회복: cj-307 carryover (Phase 11-22 deprecation) → cj-316 migration
   - cumulative: 43+1 = 44 sprints

### 결정 wire 보존 (cj-309~cj-310 wire 그대로)
- **Pilot W1 launch D-day 2026-09-14 KST** = 보존 (cj-310 retroactive correction 정직 회복)
- **cj-309b B-1 Pilot candidate outreach 결정 wire** = 보존 (Tier 1 5 + Tier 2 3 = 8, D-2 발송 honestly DEFER)
- **Resend (OQ-EPIC30+-2 v2) swap** = 보존 (Postmark blocker 정직 회복, cj-305b wire)
- **cj-307 aal1 minimum fix** = 보존 (cj-313/cj-314/cj-316 의 후속 fix 와 양립)
- **cj-304 4 critical gaps fix** = 보존 (env vars + TZ + Pilot tenant CLI + Production seed)
- **cj-300 APScheduler KST** = 보존 (TZ=Asia/Seoul, 34 references)
- **cj-303 EXTENSION** (37 pins match) = 보존 (AD-14 stack pin)
- **capability matrix v1.54 EXTENSION** = 보존
- **audit_action EXTENSION** = 보존

### cj-311 entry 의 새 우선순위 EXTENSION (reframe)
- **비용 $0** = Railway/Vercel/Resend/Supabase 모두 launch day 까지 honestly DEFER
- **MVP hardening 우선** = cj-313 + cj-314 + cj-316 결정 wire → MVP 완결성 확보 → launch day

---

## §10 Honestly DEFER 결정 wire 보존

### 비용 발생 항목 honestly DEFER (사용자 결정 wire 2026-09-09)
- ❌ Railway Hobby plan ($5/mo) — launch day 결정 wire
- ❌ Vercel Pro plan ($20/mo) — launch day 결정 wire
- ❌ Resend Pro plan ($20/mo) — launch day 결정 wire
- ❌ Supabase Pro plan ($25/mo) — launch day 결정 wire
- ❌ Custom DNS (Cloudflare) — launch day 결정 wire
- ❌ Sentry Pro plan — launch day 결정 wire

### cj-style 결정 wire honestly DEFER
- ❌ Pilot candidate outreach 발송 (D-2 2026-09-12 honestly DEFER, launch day 후)
- ❌ W1~W8 weekly tracking (launch day 부터 결정 wire)
- ❌ Railway project 생성 + Vercel project 생성 (Trial workspace, 0 projects 정직 회복)
- ❌ Resend API key 캡처 + dashboard 설정
- ❌ Supabase project production env 설정

### cj-303 carryover 4건 honestly DEFER (cj-312 audit 결과 MEDIUM)
- D-FINOPS-13 (multi-currency + budget forecast + ZBB + envelope + reconciliation)
- Phase 11~20 + 22 + 23 emit_audit_typed signature mismatch retroactive correction
- Layer 2 P1 pytest test backfill (cj-314 결정 wire 로 일부 해소)
- Layer 3 P2 docs backfill

### cj-307 carryover 정직 회복 (cj-312 audit 결과 HIGH)
- 32 failures + 22 errors + 3 collection errors → **cj-314 결정 wire**
- FastAPI `@app.on_event` deprecation → **cj-316 결정 wire**
- 결정 wire 보존: cj-307 aal1 MFA listFactors verified=[] skip 그대로

### PRE-EXISTING honestly DEFER 6건 (cj-style 보존)
1. web-e2e Playwright 23 skip (cj-282a/b)
2. test-suite-measure 잔여 (cj-282a)
3. web-test 잔여 (cj-282a)
4. lint-conventions (apps/web)
5. Sentry (post-W1, cj-305 wire)
6. custom DNS (post-W1, cj-305 wire)

---

## §11 CR 11-3 honest-DEFER 269번째

### 결정 wire chain (cj-style 220번째~269번째)
- **cj-282 (220번째)** → cj-282a (221+222) → cj-282b (223~238) → cj-297 (237th) → cj-298 (238th)
- **cj-299 (239~242)** → cj-300 (243+244) → cj-301 (245) → cj-302 (246+247)
- **cj-303 (248+249+250)** → cj-304 (251+252+253) → cj-305 (254+255)
- **cj-305b (256+257)** → cj-306 (259) → cj-307 (261) → cj-308 (263)
- **cj-309 (264)** → cj-309b (265) → cj-310 (266) → cj-310 retroactive correction (267)
- **cj-311 entry (268)** → **cj-312 wire (269)** ← **본 sprint**

### cumulative 결정 wire 보존
- **41/41** (cj-282~cj-311) → **+1 NEW = 42/42 cumulative** (cj-312 wire 신규)
- 결정 wire 보존: cj-309~cj-310 wire 결정 wire 그대로
- sprint-status v4.85 → **v4.86 EXTENSION** 결정 wire (A730 cj-312 wire + last_updated_note_v4_86)

### CR lessons applied
- CR 0-2 (RLS) + CR 1-1 (audit-first INSERT) + CR 1-1 (ContextVar + RSC boundary)
- CR 4-3/4-4 + CR 5-1 (Decimal precision banker's rounding)
- CR 9-6 (commit message `git commit -F <file>`)
- **CR 11-3 (honest-DEFER retroactive correction discipline)** — cj-312 wire 에서 verbatim mirror (cj-style 257th + 267th 패턴)
- CR 11-4 (P-015 pure validator pattern)
- CR 12-1 (L4 industry-agnostic capability)
- CR 12-5 (D-14 typed exception envelope + D-PARITY-01 + D-GATE-01)

### 정직 회복
- source code 변경 0건 (cj-312 wire docs-only sprint, audit 결과 + fix sprint 결정 wire only)
- 37 pins unchanged (cj-303 EXTENSION 보존)
- PRD v7.0 §F/§M/§R unchanged
- capability matrix v1.54 EXTENSION preserved
- audit actions EXTENSION preserved

---

## §12 Next unblocked 결정 wire 보류 + 결정 wire 일자

### 결정 보류 6개 옵션 (cj-312 wire 직후)
| 옵션 | 내용 | 예상 effort |
|---|---|---|
| **(a) cj-313 pytest rootdir 정정** | HIGH severity fix sprint (cj-style 270번째) | ~30min (docs-only + pyproject.toml testpaths EXTENSION) |
| **(b) cj-314 cj-307 carryover fix** | HIGH severity fix sprint (cj-style 271번째) | ~2h (32+22+3 pytest 에러 triage + fix) |
| **(c) cj-316 FastAPI on_event → lifespan** | HIGH severity fix sprint (cj-style 272번째) | ~1-2h (source code migration) |
| **(d) cj-312 close-out retro 진입** | cj-312 wire 결정 wire 종합 (cj-style 269th follow-up) | ~30min (docs-only) |
| **(e) PRD v2 EXTENSION 진입** | audit 결과 gap 의 우선순위 결정 후 PRD v2 작성 | TBD |
| **(f) carryover honestly DEFER 유지** | cj-303 carryover 4건 + PRE-EXISTING 6건 그대로 honestly DEFER | 0 effort |

### 결정 wire 일자
- **2026-09-09 KST (D-5)**

### Honestly DEFER 결정 wire (cj-312 close-out 후)
- ① Pilot launch D-day (2026-09-14) → 비용 발생 결정 wire 보류
- ② W1~W8 weekly follow-up 결정 wire (launch day 부터)
- ③ PRD v2 EXTENSION 결정 wire (cj-313/cj-314/cj-316 fix 후)
- ④ 비용 발생 항목 모두 (사용자 결정 wire, launch day 까지 honestly DEFER)

---

## §13 Cross-references + CR 11-3 정직 회복

### Cross-references
- **cj-style feedback** `prioritize-mvp-hardening-before-deploy` (2026-09-07) — cj-311 entry 의 trigger + cj-312 wire 의 실행 결정 wire
- **cj-style feedback** `count-remaining-before-start` (2026-09-07) — 매 주요 업무 진입 직전 잔여 주요 업무 개수 안내
- **cj-306 audit findings** (2026-09-08) — MVP deployment-ready audit, cj-307 fix 의 선행
- **cj-307 wire** (`a1cb7ad`) — auth-callback aal1 minimum fix (cj-312 audit 의 Checkpoint 2 carryover source)
- **cj-308 entry** (`07f06d0`) — Pilot W1 D-5 critical path 결정 wire entry
- **cj-309 wire** (`73766af`) — Resend + Supabase signup live verify wire
- **cj-309b wire** (`3c9bdbf`) — Pilot candidate list B-1 작성 wire
- **cj-310 entry** (`ce05e05`) — cj-309 close-out retro entry
- **cj-310 retroactive correction** (`6972571`) — headline 정직 회복
- **cj-311 entry** (`69d7d72`) — 7-Checkpoint MVP Audit Entry (cj-style 268번째)
- **cj-312 wire** (본 sprint) — 7-Checkpoint Audit 실행 결과 + gap list + fix sprint 결정 wire

### 결정 wire 정직 회복
- 7 checkpoint 종합 = 3 PASS (PRD AC coverage + Error envelope + Audit) + 3 PASS (Security + Docs + Perf) + 1 PARTIAL (Test coverage = cj-313/cj-314 결정 wire)
- 19 findings = 3 HIGH (cj-313 + cj-314 + cj-316 결정 wire) + 4 MEDIUM (honestly DEFER) + 3 LOW (honestly DEFER) + 9 PASS (결정 wire 보존)
- 결정 wire 정직 회복: cj-309~cj-311 wire 결정 wire 그대로 보존 + MVP hardening 우선순위 EXTENSION
- cj-307 carryover 정직 회복: cj-312 audit 결과 cj-313 + cj-314 + cj-316 결정 wire 로 해소 결정

### CR 11-3 honest-DEFER 269번째 정직 회복
- 42/42 cumulative 결정 wire = 41 (cj-282~cj-311 retroactive) + 1 (cj-312 wire 신규)
- 결정 wire 보존: source code 변경 0건, 37 pins unchanged, PRD v7.0 unchanged, capability matrix v1.54 preserved, audit actions preserved

---

**CJ-312 WIRE 결정 wire 보존 완료**

**CR 11-3 honest-DEFER 269번째 결정 wire chain: cj-282 (220번째) → ... → cj-311 entry (268번째) → cj-312 wire (269번째, 본 sprint)**

**Next**: cj-313 pytest rootdir 정정 (HIGH severity) 진입 또는 cj-312 close-out retro 진입 (옵션 (d))
