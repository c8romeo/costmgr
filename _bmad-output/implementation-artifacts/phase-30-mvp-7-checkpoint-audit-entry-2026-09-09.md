# cj-311 7-Checkpoint MVP Audit — Sprint Entry

> **Sprint**: cj-311 7-Checkpoint MVP Audit Entry (cj-style 268번째 docs-only atomic single sprint)
> **Date**: 2026-09-09 KST (D-5, Pilot W1 launch D-day 2026-09-14 KST)
> **Territory**: Phase 30 — MVP hardening 7-checkpoint audit 결정 wire 진입
> **Author**: Claude (operator = kjw)
> **Sprint form**: entry (감사 methodology 결정 wire, audit 실행 = cj-312 wire)

---

## §1 의도 분석 — 결정 보류 옵션 비교

### 결정 보류 4개 옵션 (cj-310 retroactive correction 직후)

| 옵션 | 의도 | trade-off | 사용자 선택 |
|---|---|---|---|
| **(a)** cj-310 close-out retro 진입 (4 verify gate 결과 종합) | Pilot W1 production deploy verify | **Railway/Vercel/Resend/Supabase 비용 발생**, 현 시점에서 deploy 우선순위 낮음 | ❌ |
| **(b)** Pilot candidate outreach 즉시 (cj-309b B-1) | 실제 candidate 발송 | signup 가능 상태 전 발송 무의미, deploy 미완 | ❌ |
| **(c)** cj-303 carryover 4건 fix (post-W1 honestly DEFER 유지) | 기존 carryover 처리 | post-W1 보류 유지 (현 시점 아님) | ❌ |
| **(d)** **MVP hardening 7-checkpoint audit entry 진입** | **제품 자체 완결성 audit, 비용 $0, deploy 이전 우선** | **사용자 cj-style feedback `prioritize-mvp-hardening-before-deploy` 정직 회복** | ✅ **선택** |

### cj-style feedback 매칭 (CR 11-3 honest-DEFER 268번째 정직 회복)

사용자 cj-style feedback (2026-09-07):
> "D-day countdown 중에도 MVP deployment-ready hardening 을 deployment signup 보다 우선. 7-checkpoint audit 우선."

이 결정 wire 는 cj-style feedback verbatim mirror + cj-306 audit findings (D-6 hardening) 의 후속. **사용자 결정 wire = cj-style discipline 보존 정직 회복**.

---

## §2 7-Checkpoint 결정 wire (sprint scope)

### Checkpoint 1: PRD AC coverage (§F + §M + §R)

**Audit target**: PRD v7.0 의 모든 AC 가 실제 구현되어 있는가?
- **§F (functional ACs)**: Epic 1~17 + Phase 17~30 (총 17 epic + 24 phase sprints)
- **§M (migration/integration ACs)**: multi-tenancy + RLS (CR 0-2) + capability matrix v1.54 EXTENSION
- **§R (reliability/NFR ACs)**: NFR4 PII minimization + NFR8 error envelope + NFR18 ko-KR SSOT

**Audit 방법론**:
- `grep -rn "AC #" apps/api/modules/ apps/web/components/ docs/` 로 AC ID 추출
- sprint-status.yaml 의 AC count vs PRD acceptance criteria count 비교
- Gap list 형태: `AC ID | status (satisfied/missing/partial) | fix sprint 결정`

**Expected output**: PRD §F/§M/§R AC gap list (severity HIGH/MEDIUM/LOW)

### Checkpoint 2: Test coverage (pytest + vitest + tsc + ruff + Playwright)

**Audit target**: 모든 테스트 suite 의 failure/error/collection error 정직 회복
- **pytest (apps/api)**: cj-307 carryover — 32 test failures + 22 errors + 3 collection errors
- **vitest (apps/web)**: Phase 24 + 23 frontend test debt (cj-303 carryover)
- **tsc (apps/web)**: typed routes (cj-271 D-CI-FUNC-5) + D-PARITY-01 verbatim
- **ruff (apps/web lint conventions)**: PRE-EXISTING honestly DEFER 보존 4건 중 1건
- **Playwright (apps/web e2e)**: 6 closing-guard tests describe.skip (cj-282a) + 17 bulk e2e skip (cj-282b) + 6 test-suite-measure 잔여

**Audit 방법론**:
- `uv run pytest --collect-only 2>&1 | head -50` (failure/error summary)
- `pnpm tsc --noEmit` (apps/web compile check)
- `pnpm test` (vitest)
- `pnpm lint` (ruff/eslint conventions)
- `pnpm exec playwright test --list` (e2e suite inventory)
- Gap list 형태: `test name | error message | fix sprint 결정`

**Expected output**: test debt gap list (cj-307 carryover + cj-303 carryover + 6 PRE-EXISTING)

### Checkpoint 3: Error envelope (typed exceptions + NFR8 envelope)

**Audit target**: 모든 error path 가 typed exception + envelope 으로 처리되는가?
- **typed exception classes**: cj-299 16 NEW + cj-300 EXTENSION + cj-304 EXTENSION (총 50+ classes 추정)
- **NFR8 envelope**: CR 12-5 D-14 envelope pattern (모든 API response 의 envelope 검증)
- **AD-2 audit-first INSERT**: caller-side audit row emitted BEFORE error raise

**Audit 방법론**:
- `grep -rn "Error(" apps/api/modules/` (typed exception 정의)
- `grep -rn "raise" apps/api/modules/` (raw raise vs typed exception ratio)
- `apps/api/core/errors.py` 의 typed exception base classes 확인
- Gap list 형태: `module | raw raise location | typed exception 후보`

**Expected output**: missing typed exception + raw raise 정직 회복

### Checkpoint 4: Audit & observability (audit_first INSERT + ActionClass enum)

**Audit target**: 모든 mutating action 이 audit_logs INSERT 되는가?
- **audit_first INSERT**: AD-2 + CR 1-1 (모든 mutating action 의 audit row emitted BEFORE actual mutation)
- **ActionClass enum**: cj-299 8 NEW (FINOPS_BUDGET_PLANNING) + cj-300 EXTENSION + cj-305 EXTENSION + cj-304 EXTENSION (`pilot_tenant_provisioned`)
- **observability stack**: Phase 7 OTEL SDK + Sentry post-W1 honestly DEFER
- **audit_logs RLS**: Phase 6 audit log retention wire + RLS policy

**Audit 방법론**:
- `apps/api/core/audit_action.py` 의 ActionClass enum list 확인
- `grep -rn "audit_action" apps/api/modules/` (audit_first INSERT 호출 위치)
- `grep -rn "audit_logs" apps/api/alembic/versions/` (audit_logs table + RLS policy)
- Gap list 형태: `action | audit_action 매핑 | RLS policy | observability`

**Expected output**: missing audit action + missing RLS + observability gap

### Checkpoint 5: Security (RLS + 2FA + NFR4 + capability matrix)

**Audit target**: 모든 security invariant 가 강제되는가?
- **RLS (CR 0-2)**: 모든 table 에 RLS policy + tenant_id scoping
- **2FA (Epic 12)**: cj-307 aal1 minimum fix + tenant_owner MFA 챌린지 (≥10M KRW/year)
- **NFR4 PII minimization**: email_service.redact_pii() upstream + 모든 외부 출력 정직 회복
- **capability matrix v1.54**: FINOPS_BUDGET_PLANNING + REPORTING_EXPORT 4-industry grants ✅/✅/✅/✅

**Audit 방법론**:
- `grep -rn "ENABLE ROW LEVEL SECURITY" apps/api/alembic/versions/` (RLS 정책)
- `apps/api/core/capability.py` 의 Capability enum + grants list
- `apps/api/modules/auth/` 의 2FA enrollment/verification flow
- Gap list 형태: `table | RLS policy | capability gate | 2FA gate | PII redaction`

**Expected output**: RLS gap + capability matrix gap + 2FA flow gap + PII redaction gap

### Checkpoint 6: Performance & reliability (NFR latency + retry + APScheduler)

**Audit target**: 모든 reliability invariant 가 강제되는가?
- **NFR latency**: API response time target (p50/p95/p99)
- **retry policy**: cj-304 RETRY_BACKOFF_MINUTES=[1,5,30] EXTENSION (exponential backoff)
- **APScheduler KST**: cj-300 TZ=Asia/Seoul EXTENSION (cron scheduling KST 정직 회복)
- **DB connection pool**: asyncpg pool sizing + timeout config
- **AD-14 stack pin**: 37 pins match (cj-303 EXTENSION 보존)

**Audit 방법론**:
- `apps/api/scheduled_reports.py` 의 4 cron + 13 functions + pytz KST + RETRY_BACKOFF_MINUTES 검증
- `apps/api/core/database.py` 의 pool sizing + timeout
- `apps/api/main.py` 의 middleware timing
- `uv run python scripts/check_stack_pin.py` → 'OK all 37 pins match' ✅
- Gap list 형태: `component | config | target | actual`

**Expected output**: retry/timezone/pool config gap + latency 측정 결과

### Checkpoint 7: Documentation (README + runbook + decision wire ledger)

**Audit target**: 모든 documentation invariant 가 최신인가?
- **README**: project root 의 README.md + 각 apps/* 의 README
- **runbook**: docs/deployment.md + docs/deployment-account-setup.md
- **decision wire ledger**: sprint-status.yaml v4.84 EXTENSION, **41 cumulative sprints** 보존 (cj-282~cj-311)
- **MEMORY.md hooks**: cj-style hook for each sprint (cj-282 hook ~ cj-311 hook)
- **commit-msg hygiene**: CR 9-6 D5 prevention (file count + breakdown arithmetic 정직 회복)

**Audit 방법론**:
- `ls docs/` (docs inventory)
- sprint-status.yaml 의 cumulative count + last_updated_note 정합 검증
- memory/MEMORY.md 의 hook count vs sprint count 비교
- `git log --oneline -50` (commit message 정직 회복 검증)
- Gap list 형태: `doc | last_updated | stale_since | fix sprint 결정`

**Expected output**: missing docs + stale decision wire + missing memory hooks

---

## §3 Audit Methodology 결정 wire

### 실행 방식
- **Claude (in-session)**: 7 checkpoint 의 audit 실행 (code/docs 정독, grep/script 활용)
- **Operator (kjw, out-of-session work hours)**: 결과 review + fix sprint 결정
- **In-session sprint scope**: cj-311 entry (감사 methodology 결정 wire, 본 sprint)
- **Wire sprint scope**: cj-312 wire (audit 실행 결과 → gap list → fix sprint 결정)

### In-session vs Out-of-session 구분
| Task | In-session (Claude) | Out-of-session (kjw) |
|---|---|---|
| 7 checkpoint audit 실행 | ✅ | review |
| 결과 gap list 작성 | ✅ | confirm |
| fix sprint 결정 | ✅ (suggest) | confirm |
| actual fix implementation | ❌ (post-cj-312 fix sprints) | ✅ |

### Estimated effort
- **cj-311 entry (본 sprint)**: ~30min (docs-only atomic)
- **cj-312 wire (audit 실행)**: ~2-3h (7 checkpoint × 20-30min each)
- **fix sprints (post-cj-312)**: TBD per gap list severity

---

## §4 Expected Output (cj-312 wire 의 산출물 형태)

### Gap list format (YAML)
```yaml
checkpoint_1_prd_ac_coverage:
  total_acs: 0
  satisfied: 0
  missing: 0
  partial: 0
  gaps:
    - ac_id: "AC #X.Y"
      severity: HIGH  # HIGH | MEDIUM | LOW
      status: missing  # missing | partial | satisfied
      fix_sprint: "cj-313 PRD-AC-gap-fix"  # 또는 honestly DEFER
      rationale: "..."

checkpoint_2_test_coverage:
  pytest_failures: 32  # cj-307 carryover 보존
  pytest_errors: 22
  pytest_collection_errors: 3
  vitest_failures: 0  # 또는 TBD
  tsc_errors: 0  # 또는 TBD
  ruff_errors: 0  # 또는 TBD
  playwright_skip: 23  # 6 + 17 closing-guard + bulk e2e
  ...
```

### Sprint decision matrix (post-audit)
- **HIGH severity gap**: 즉시 fix sprint 결정 (cj-313, cj-314, ...)
- **MEDIUM severity gap**: cj-313+ batch fix 또는 honestly DEFER (post-W1)
- **LOW severity gap**: honestly DEFER (post-W1 또는 PRD v2 EXTENSION)

---

## §5 Carryover 정직 회복

### cj-303 carryover 4건 (Phase 30 Pilot Gate)
1. emit_audit_typed signature mismatch (Phase 11~20 + 22 + 23 retroactive correction honestly DEFER)
2. Layer 2 P1 pytest test backfill
3. Layer 3 P2 docs backfill
4. D-FINOPS-13 신규 honestly DEFER (multi-currency + budget forecast + ZBB + envelope + reconciliation)

### cj-307 carryover (auth-callback aal1 minimum fix)
- 32 pytest failures + 22 errors + 3 collection errors
- FastAPI `@app.on_event` deprecation (post-FastAPI 0.109+)
- 결정 wire 보존: cj-307 fix (aal1 MFA listFactors verified=[] skip) 보존 + carryover honestly DEFER

### PRE-EXISTING honestly DEFER 6건 (cjw-style 6건)
1. web-e2e Playwright 6 closing-guard tests describe.skip (cj-282a)
2. test-suite-measure 잔여 (cj-282a)
3. web-test 잔여 (cj-282a)
4. lint-conventions (apps/web lint)
5. Sentry (post-W1 honestly DEFER 보존, cj-305 wire 결정 wire)
6. custom DNS (post-W1 honestly DEFER 보존, cj-305 wire 결정 wire)

### 결정 wire 일치
- 위 6건 모두 cj-311 audit 의 **Checkpoint 2 + 7** 의 audit target
- audit 결과로 severity 재평가 → fix sprint 결정 또는 honestly DEFER 유지

---

## §6 결정 wire 보존 (cj-309~cj-310 wire 의 결정 wire 그대로)

### cj-309~cj-310 결정 wire 보존 항목
- **Pilot W1 launch D-day = 2026-09-14 KST** 보존 (정직 회복, 조정 아님)
- **8개 Pilot candidate outreach 결정 wire** (cj-309b B-1) 보존 (Tier 1 5 + Tier 2 3)
- **Resend (OQ-EPIC30+-2 v2)** swap 결정 wire 보존 (Postmark blocker 정직 회복)
- **cj-307 aal1 minimum fix** 결정 wire 보존 (Pilot W1 blocker 해결)
- **cj-304 4 critical gaps fix** 결정 wire 보존 (env vars + TZ + Pilot tenant CLI + Production seed)
- **cj-300 APScheduler KST** 결정 wire 보존 (TZ=Asia/Seoul)

### cj-311 entry 의 **새 우선순위 EXTENSION** (reframe)
- **비용 $0** = Railway/Vercel/Resend/Supabase 모두 **launch day 까지 honestly DEFER**
- **MVP hardening 우선** = 7-checkpoint audit → gap fix → MVP 완결성 확보 → launch day

### 두 결정 wire 의 양립 가능성
- cj-309~cj-310 의 **deploy 결정 wire** = 그대로 보존 (launch day 에 실행)
- cj-311 의 **MVP hardening 우선순위** = **launch day 이전까지 우선순위 1순위** EXTENSION
- 결과: Pilot launch D-0 시점에 **MVP 완결 + deploy 결정 wire 보존** = 양립 가능

---

## §7 Honestly DEFER 결정 wire 보존

### Launch day 까지 honestly DEFER (cj-309~cj-310 결정 wire 그대로)
- Railway project 생성 + Vercel project 생성 (현재 `{A.R.M.Y}YouTube듀링` workspace, Trial $5 잔여, 0 projects 정직 회복)
- Resend API key 캡처 (Step 1) + dashboard 설정 (Step 3)
- Supabase project 설정 (production env)
- Pilot candidate outreach 발송 (D-2 2026-09-12 honestly DEFER 보존)
- W1~W8 weekly tracking (launch day 부터 결정 wire)

### 비용 발생 항목 honestly DEFER (사용자 결정 wire)
- Railway Hobby plan upgrade ($5/mo) — **honestly DEFER 보존**
- Vercel Pro plan upgrade ($20/mo) — **honestly DEFER 보존**
- Resend Pro plan (3,000/mo → 50,000/mo, $20/mo) — **honestly DEFER 보존**
- Supabase Pro plan upgrade ($25/mo) — **honestly DEFER 보존**
- Custom DNS (Cloudflare) — **honestly DEFER 보존** (cj-305 wire 결정)
- Sentry Pro plan — **honestly DEFER 보존** (cj-305 wire 결정)

### 결정 wire 보존
- 모든 비용 발생 항목은 **launch day 직전** 결정 wire 진입
- 사용자가 launch day 결정 시: 4-service minimal viable (cj-305 wire 결정 wire) 또는 scaled launch

---

## §8 CR 11-3 honest-DEFER discipline 적용

### CR 11-3 정직 회복 chain
- **cj-282 (220번째)** → ... → **cj-310 retroactive correction (267번째)** → **cj-311 entry (268번째)**
- **40 sprints** (cj-282~cj-310 retroactive) → **+1 NEW = 41 sprints** (cj-311 entry 신규)

### sprint-status v4.84 → **v4.85 EXTENSION** 결정 wire
- **A729**: cj-311 entry (본 sprint) 신규 block entry
- **last_updated_note_v4_85**: 신규 paragraph
- **memory/MEMORY.md**: cj-311 hook EXTENSION + active sprint state post cj-311

### 결정 wire 보존
- **41/41 cumulative 결정 wire** = 40 (cj-282~cj-310 retroactive) + 1 (cj-311 entry)
- **source code 변경 0건** (cj-311 entry 는 docs-only sprint)
- **37 pins unchanged** (cj-303 EXTENSION 보존, cj-311 신규 EXTENSION 0건)
- **PRD v7.0 §F/§M/§R unchanged** (cj-311 entry 신규 EXTENSION 0건)
- **capability matrix v1.54 EXTENSION preserved** (cj-311 entry capability 직접 변경 없음)
- **audit actions EXTENSION preserved** (cj-311 entry audit action 직접 변경 없음)

---

## §9 Cross-references + 결정 wire 일자

### Cross-references
- **cj-style 257th**: cj-305b retroactive correction (`c69dea5`)
- **cj-style 266th**: cj-310 cj-309 close-out retro entry (`07f06d0` 직전)
- **cj-style 267th**: cj-310 retroactive correction (`6972571`)
- **cj-306 audit findings**: MVP deployment-ready audit — D-6 hardening (auth flow SSO-only blocker, cj-307 fix 의 선행)
- **cj-307 wire**: auth-callback aal1 minimum fix (`a1cb7ad`)
- **cj-308 entry**: Pilot W1 D-5 critical path 결정 wire entry (`07f06d0`)
- **cj-309 wire**: Resend + Supabase signup live verify wire (`73766af`)
- **cj-309b wire**: Pilot candidate list B-1 작성 wire (`3c9bdbf`)
- **cj-310 entry**: cj-309 close-out retro entry (`ce05e05`)
- **cj-style feedback** `prioritize-mvp-hardening-before-deploy` (2026-09-07): 사용자 cj-style feedback 결정 wire
- **cj-style feedback** `count-remaining-before-start` (2026-09-07): 매 주요 업무 진입 직전 잔여 주요 업무 개수 안내

### 결정 wire 일자
- **2026-09-09 KST (D-5)**

### Next unblocked 결정 wire 보류
- **옵션 (a) cj-312 wire 진입** = 7-checkpoint audit 실행 + gap list 작성 (cj-style 269번째)
- **옵션 (b) cj-311 entry close-out retro 진입** = cj-311 entry 결정 wire 종합 (cj-style 269번째 follow-up)
- **옵션 (c) PRD v2 EXTENSION 진입** = audit 결과 gap 의 우선순위 결정 후 PRD v2 작성
- **옵션 (d) fix sprint 진입** = cj-303/307 carryover fix (HIGH severity gap 일 경우)

### Honestly DEFER 결정 wire
- ① Railway/Vercel/Resend/Supabase signup (launch day 결정 wire)
- ② Pilot candidate outreach 발송 (D-2 honestly DEFER)
- ③ W1~W8 weekly tracking (launch day 부터 결정 wire)
- ④ 비용 발생 항목 모두 (사용자 결정 wire, launch day 까지 honestly DEFER)

---

**CJ-STYLE 268번째 결정 wire 진입 완료 보존**