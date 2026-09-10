---
name: cj-319 Track A-0 deploy-blocking wire DONE
description: cj-318 Track A 진입 시 A-1~A-4 가 100% 운영자 대시보드 액션임을 정직 인정 + 그 선행 조건의 deploy-blocking 드리프트 4건 (F1 railway.toml Postmark stale 계약 / F2 CORSMiddleware 전무 / F3 NEXT_PUBLIC_API_URL 누락 / F4 cj-318 서버 시크릿 위치 오지시) 정직 회복 (source+tests+docs atomic, cj-style 285th)
metadata:
  type: project
---

# cj-319 Track A-0 deploy-blocking wire — DONE

> **Sprint**: cj-319 Track A-0 deploy-blocking wire (cj-style 285번째 atomic single sprint)
> **Date**: 2026-09-10 KST (D-4, Pilot W1 launch D-day 2026-09-14 KST)
> **Status**: ✅ CLOSED ✅ HONEST (sprint-status v4.100 → **v4.101 EXTENSION** A745)
> **Territory**: Phase 30 — Track A 선행 조건 (deploy-blocking 드리프트 회복)
> **Author**: Claude (operator = kjw)
> **Sprint form**: wire (source + tests + docs atomic, **CR 11-3 honest-DEFER 285번째**)

---

## §1 의도 분석 — Track A 실행 가능성 분리 정직 인정

### 1.1 운전자 결정 wire

운전자 지시 = **"옵션 (a) Track A 즉시 실행 진입"** (cj-318 §7.1 옵션 8건 중 (a), 잔여 7건).

진입 직후 정직 인정: **cj-318 §2 의 A-1~A-4 는 100% 운영자 대시보드 액션**이다
(Resend / Supabase / Railway / Vercel 로그인 ��요). Claude 가 대신 실행할 수 없다.

따라서 Track A 를 **두 층으로 정직 분리**:

| 층 | 담당 | 내용 |
|---|---|---|
| **A-1~A-4** (원래 정의) | operator (kjw) | 대시보드 캡처 + live verify + smoke test |
| **A-0** (본 sprint, 신규) | Claude | A-1~A-4 를 **성립시키는 코드 측 선행 조건** |

### 1.2 A-0 발견 경위

Track A 를 실행 가능하게 만들기 위해 코드 측 계약을 sweep 한 결과,
**A-1/A-4 를 무효화하는 deploy-blocking 드리프트 4건** 발견. 운전자 승인 후 본 wire 진입
(범위 = F1+F2+F3+F4 전체, 형식 = cj-style 정식).

---

## §2 발견 4건 + 회복 내용

### F1 🔴 `railway.toml` Postmark → Resend stale 계약

**발견**: `railway.toml` `[env]` 가 `POSTMARK_SERVER_TOKEN` / `POSTMARK_FROM_EMAIL` 를 선언.
cj-305b (`53b8bbf`) 가 **코드만** Postmark → Resend 로 swap 하고 railway.toml 은 갱신하지 않음.

**영향**: `apps/api/core/email_provider.py::get_email_provider` 는 `RESEND_API_KEY` 만 읽는다
(line 280). 계약 행이 없으면 운영자가 **Track A-1 에서 캡처한 API key 가 컨테이너에 도달하지 못하고**
LoggingProvider 로 **조용히** fallback (line 305) → 파일럿 이메일 미발송 + 실패가 로그에만 남음.

**회복**: `RESEND_API_KEY` / `RESEND_FROM_EMAIL` 로 swap + `CORS_ORIGINS` 행 EXTENSION.
cj-305b 결정 wire 정합 회복.

### F2 🔴 `apps/api/main.py` CORSMiddleware 전무

**발견**: repo 전체에서 `CORSMiddleware` 참조 **0건**. 등록 미들웨어는
`TraceContextMiddleware` + `LatencyBudgetMiddleware` 2개뿐.

**영향**: `vercel.json` 의 CSP `connect-src ... https://*.railway.app` 는
**브라우저가 Vercel(web) origin 에서 Railway(API) origin 으로 직접 cross-origin 호출**하는
구조를 전제한다. `apps/web/lib/**` 의 `apiBaseUrl()` 도 절대 origin 을 조립한다.
CORS 헤더가 없으면 브라우저가 전 API 호출을 차단 → **Track A-4 live signup smoke test 실패 확정**.

**정직 인정**: `docs/deployment-account-setup.md` §4.4 에는 `CORS_ORIGINS` env var row 가
**이미 존재**했다 (line 138). 즉 **docs 는 옳았고 소스가 틀렸다**. 운영자가 Railway 에
CORS_ORIGINS 를 채워도 아무 효과가 없는 상태였음.

**회복**: `parse_cors_origins()` 순수 함수 + `CORSMiddleware` 등록.
- **fail-closed**: 미설정 / 공백 / `,,` → `["http://localhost:3000"]` 만 허용
- **wildcard 거부**: `*` 는 `allow_credentials=True` 와 병용 불가 + AD-10 최소권한 → 무시
- **최외곽 등록**: 마지막 `add_middleware` → OPTIONS preflight 와 4xx/5xx 응답에도 헤더 부착
- **`expose_headers=["X-Trace-Id"]`**: Phase 7 tracing 결정 wire 보존 (브라우저 JS 가 읽을 수 있게)

### F3 🟡 `apps/web/.env.example` `NEXT_PUBLIC_API_URL` 누락

**발견**: `apps/web/lib/audit/audit-log-client.ts:82-85` 등 다수가
`process.env.NEXT_PUBLIC_API_URL` 을 읽고, 없으면 `http://localhost:8765` 로 폴백.
`docs/deployment-account-setup.md` §4.5 (line 164) 에는 Vercel env var 로 문서화되어 있으나
`.env.example` 에는 누락 → 계약 surface 드리프트.

**영향**: 운영자가 Vercel 에 넣는 것을 누락하면 **파일럿 프론트엔드가 localhost 를 호출**.

**회복**: `.env.example` 에 주석 + 기본값 추가.

**의도적 미조치 (정직 인정)**: docs §4.5 는 `NEXT_PUBLIC_APP_URL` 도 나열하지만
`apps/web` 소스 참조 **0건** (grep verified). 존재하지 않는 계약을 날조하지 않기 위해
**추가하지 않았다**. docs 측 드리프트로 별도 triage honestly DEFER.

### F4 🟡 cj-318 §2 서버 전용 시크릿 위치 오지시

**발견**: cj-318 §2 의 **A-1 step 5** ("Web `.env.local` 업데이트: `RESEND_API_KEY=...`") 와
**A-2 step 4** ("Web `.env.local` + Railway + apps/api `.env` 모두 동일 JWT") 는 틀렸다.
`apps/web` 소스 전체에서 `RESEND_API_KEY` / `SUPABASE_JWT_SECRET` 참조 **0건** (grep verified).

**영향**: 무의미할 뿐 아니라, `NEXT_PUBLIC_` 접두사 실수 시 **클라이언트 번들에 프로덕션 시크릿 ��출**.

**회복**: 올바른 위치 = **Railway service Variables (production) + `apps/api/.env` (local dev only)**.
cj-318 handoff §2 상단에 정정 note EXTENSION (append-only fix-forward, `git commit --amend` 0건 —
cj-style 257th / 267th / 279th / 281st / 283rd retroactive correction discipline verbatim mirror).

---

## §3 변경 파일 (source + tests + docs atomic)

| # | 파일 | 종류 | 내용 |
|---|---|---|---|
| 1 | `apps/api/main.py` | MODIFIED source | `import os` + `CORSMiddleware` import + `parse_cors_origins()` + `DEFAULT_CORS_ORIGINS` + `CORS_ALLOWED_ORIGINS` + `add_middleware(CORSMiddleware, ...)` |
| 2 | `railway.toml` | MODIFIED source | POSTMARK_* 2행 → RESEND_* 2행 swap + `CORS_ORIGINS` 1행 EXTENSION |
| 3 | `apps/api/.env.example` | MODIFIED env surface | `CORS_ORIGINS` 섹션 신규 |
| 4 | `apps/web/.env.example` | MODIFIED env surface | `NEXT_PUBLIC_API_URL` 섹션 신규 |
| 5 | `tests/api/test_cj_319_cors_middleware.py` | **NEW tests** | 15 pytest cases |
| 6 | `memory/handoff-2026-09-10-cj-318-...md` | MODIFIED docs | §2 상단 F4 정정 note EXTENSION |
| 7 | `_bmad-output/implementation-artifacts/commit-msg-cj-319.txt` | NEW meta | commit message |
| 8 | `memory/handoff-2026-09-10-cj-319-...md` | NEW meta | 본 handoff |
| 9 | `_bmad-output/implementation-artifacts/sprint-status.yaml` | MODIFIED meta | v4.100 → **v4.101** A745 |
| 10 | `memory/MEMORY.md` | MODIFIED meta | cj-319 hook |

**0 alembic 변경 + 0 PRD 변경 + 0 capability matrix 변경 + 0 migration source 변경**
+ 37 pins unchanged + 14 job matrix unchanged + `git commit --amend` 0건.

---

## §4 Verify gate

| Gate | 방법 | 결과 |
|---|---|---|
| GV-1 신규 테스트 | `pytest tests/api/test_cj_319_cors_middleware.py` | **15 passed** ✅ |
| GV-2 fail-closed 기본값 | `CORS_ORIGINS` 미설정 import | `['http://localhost:3000']` ✅ |
| GV-3 최외곽 배치 | `app.user_middleware` | `['CORSMiddleware', 'LatencyBudgetMiddleware', 'TraceContextMiddleware']` ✅ |
| GV-4 preflight allow/deny | TestClient OPTIONS | allowed → `200` + allow-origin ✅ / denied → `400` + allow-origin **없음** ✅ |
| GV-5 오류 응답 CORS | TestClient 404 / 401 | allow-origin + `expose=X-Trace-Id` 부착 ✅ |
| GV-6 광역 회귀 | `pytest tests/api -q` | **2322 passed / 32 failed / 117 skipped** |
| GV-7 회귀 귀속 판정 | `git stash` 대조 재현 | 32 failures **PRE-EXISTING 확인** → **regression 0건** ✅ |

**GV-7 상세 (정직 회복)**: 32 failures 는 전부 Phase 10 SLO family 6 files
(`test_phase_10_audit_action` / `error_budget` / `governance` / `multi_region_aggregator` /
`slo_burn_rate_evaluator` / `slo_dsl`). 해당 파일들은 `TestClient` / `apps.api.main` import
**0건** → CORS 미들웨어와 인과 없음. `git stash` 로 본 wire 변경 제거 후 동일 실패 재현 확인.
cj-307 carryover 의 **LOW RISK Phase 10 SLO family ~30건** (Phase C honestly DEFER) 과 일치.

---

## §5 신규 발견 (본 sprint scope 외, honestly DEFER)

| # | 발견 | 상태 |
|---|---|---|
| N-1 | `sprint-status.yaml` line 536 **YAML 파서 오류 PRE-EXISTING** (`expected <block end>, but found '?'`). `git stash` 대조로 본 wire 이전부터 존재 확인. append 한 A745 블록 자체는 단독 파싱 정상. | honestly DEFER (별도 triage) |
| N-2 | `docs/deployment-account-setup.md` §4.5 의 `NEXT_PUBLIC_APP_URL` 은 `apps/web` 소스 참조 0건 (docs-only 유령 계약) | honestly DEFER |
| N-3 | `/api/v1/health` 가 TestClient 기본 모드에서 `'dict' object has no attribute 'encode'` 발생 (PRE-EXISTING, CORS 무관) | honestly DEFER |
| N-4 | `apps/web/.env.local` (git-ignored, 운영자 실사용 파일) 은 **의도적으로 미변경** — 운영자 실값 clobber 회피 | operator 조치 |

---

## §6 운영자 잔여 액션 (Track A-1~A-4, 본 wire 로 선행 조건 해소됨)

| 액션 | 캡처 값 | **올바른 투입 위치 (F4 정정 반영)** |
|---|---|---|
| **A-1** | `RESEND_API_KEY=re_...` | Railway Variables ✅ / `apps/api/.env` (local dev) / ~~web `.env.local`~~ ❌ |
| **A-1** | `RESEND_FROM_EMAIL=onboarding@resend.dev` | Railway Variables |
| **A-2** | `SUPABASE_JWT_SECRET=...` | Railway Variables ✅ / `apps/api/.env` (local dev) / ~~web `.env.local`~~ ❌ |
| **신규** | `CORS_ORIGINS=https://costmgr-pilot.vercel.app` | Railway Variables (**미설정 시 파일럿 프론트 전 API 호출 차단**) |
| **신규** | `NEXT_PUBLIC_API_URL=https://<service>.up.railway.app` | Vercel Environment Variables (**미설정 시 localhost 호출**) |
| **A-3** | — | Supabase Auth dashboard live verify (Email enabled / Confirm OFF / Site URL / 3 Redirect URLs) |
| **A-4** | — | Live signup smoke test (signup → dashboard → logout → re-login → 2nd signup 격리) |

> A-4 는 **CORS_ORIGINS + NEXT_PUBLIC_API_URL 양쪽이 채워진 뒤에만** 통과 가능하다.

---

## §7 결정 wire 보존

- **cj-318 operator immediate execution entry** (`241fd3a`, cj-style 284th) 결정 wire 보존 (3-track 구조 그대로, §2 만 F4 정정 EXTENSION)
- **cj-305b Postmark → Resend swap** (`53b8bbf` + `c69dea5`, cj-style 256+257th) 결정 wire **정합 회복** (railway.toml 까지 확장)
- **cj-304 prod deploy prep** (`1fdb67d`, cj-style 252nd) 의 4 critical gaps 결정 wire 보존 (TZ / RETRY_BACKOFF_MINUTES 등 기존 행 무변경)
- **cj-307 aal1 minimum fix** (`a1cb7ad`, cj-style 261st) 결정 wire 보존
- **Phase 7 tracing** X-Trace-Id 응답 헤더 결정 wire 보존 (`expose_headers` 로 브라우저 노출)
- **AD-10 최소권한** 보존 (wildcard 거부 + fail-closed 기본값)
- **CR 11-3 honest-DEFER retroactive correction discipline** (cj-style 257th / 267th / 279th / 281st / 283rd) verbatim mirror — `git commit --amend` 0건, append-only fix-forward
- Pilot W1 launch D-day **2026-09-14 KST** 보존

**57/57 cumulative 결정 wire 보존** (cj-318 entry 의 56 + NEW 57번째 cj-319 Track A-0 wire)

---

## §8 결정 보류 (운전자) — 잔여 주요 업무 7건

① **옵션 (a, RECOMMENDED next) Track A-1~A-4 운영자 실행** — 대시보드 캡처 + live verify (~35-50분, D-3 deadline)
② 옵션 (b) **Track B 즉시 실행** — B-1 + B-2 + B-3 (~4h, D-2 deadline)
③ 옵션 (c) **Track A + B 병렬 실행** (~4-5h)
④ 옵션 (d) **Track C D-1 사전 verify** (~30분)
⑤ 옵션 (e) **cj-309b B-1 retroactive correction** (8개 `(operator network)` placeholder → 실제 회사명, post-D-2)
⑥ 옵션 (f) **PRD v2 EXTENSION** (post-W1)
⑦ 옵션 (g) **cj-314 batch B** (~4-5h, post-W1 honestly DEFER 권장)
⑧ 옵션 (h) **`epics.md` 미커밋 대형 변경 triage** (별도 sprint)
⑨ **신규** 옵션 (i) **N-1 sprint-status YAML 파서 오류 triage** (~30min)

---

## §9 Honestly DEFER 결정 wire 보존

- ① 비용 발생 항목 모두 (Railway / Vercel / Resend / Supabase / Sentry / Custom DNS) — 운전자 결정
- ② W1~W8 weekly follow-up (launch day 부터)
- ③ PRD v2 EXTENSION (post-W1)
- ④ sso 13 skipped tests (missing python3-saml, PRE-EXISTING)
- ⑤ web-e2e Playwright 23 skip + test-suite-measure 잔여 + web-test 잔여 + lint-conventions + Sentry + custom DNS (PRE-EXISTING)
- ⑥ cj-303 carryover 4건 (D-FINOPS-13 + audit-fixes + Layer 2 P1 + Layer 3 P2 docs)
- ⑦ cj-307 carryover LOW RISK ~30건 (Phase 10 SLO family = 본 wire GV-7 의 32 failures)
- ⑧ **신규** N-1 / N-2 / N-3 (§5)

---

**CJ-319 TRACK A-0 DEPLOY-BLOCKING WIRE 결정 wire 보존 완료**

**CR 11-3 honest-DEFER 285번째 결정 wire chain: cj-282 (220번째) → ... → cj-318 entry (284번째) → cj-319 Track A-0 wire (285번째, 본 sprint)**

**Next**: Track A-1~A-4 운영자 실행 (대시보드, ~35-50분) → Track B outreach (~4h) → Track C D-0 종합 verify (~1.5h)
