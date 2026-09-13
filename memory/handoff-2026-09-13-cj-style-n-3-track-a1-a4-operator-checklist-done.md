---
name: handoff-2026-09-13-cj-style-n-3-track-a1-a4-operator-checklist-done
description: "Track A-1~A-4 운영자 체크리스트 (cj-style N+3 wire, 2026-09-13 KST, D-1 Pilot W1 launch) — 100% operator dashboard actions (Resend API key + Supabase JWT secret + CORS_ORIGINS + NEXT_PUBLIC_API_URL + Auth dashboard live verify + Live signup smoke test). cj-318 §2 + cj-319 §6 통합 운전자 친화적 단일 체크리스트."
metadata:
  node_type: memory
  type: project
  originSessionId: cj-style-307-wire-session
  modified: 2026-09-13T15:00:00.000Z
---

# Track A-1~A-4 운영자 체크리스트 — DONE (cj-style N+3 wire)

**일자**: 2026-09-13 (KST, D-1 Pilot W1 launch, launch D-day 2026-09-14 KST Mon 까지 ~12-24시간 잔여)
**territory**: Phase 30 — Track A-1~A-4 100% operator dashboard actions
**sprint type**: 단일 운전자 친화적 체크리스트 (docs-only, no source change)
**출처**: cj-318 handoff §2 (Track A 4 Deploy-Blocking Actions) + cj-319 handoff §6 (F4 정정 반영 + A-0 wire 의 선행 조건 회복)

---

## §1 의도 분석 — Track A-1~A-4 의 100% 운영자 액션 정직 인정

### 1.1 cj-318 §1.1 verbatim mirror

> **cj-318 §1.1**: "Track A 를 실행 가능하게 만들기 위해 코드 측 계약을 sweep 한 결과, **A-1/A-4 를 무효화하는 deploy-blocking 드리프트 4건** 발견. ... 따라서 Track A 를 **두 층으로 정직 분리**: | **A-1~A-4** (원래 정의) | operator (kjw) | 대시보드 캡처 + live verify + smoke test | **A-0** (cj-319 신규) | Claude | A-1~A-4 를 **성립시키는 코드 측 선행 조건** |"

### 1.2 본 체크리스트의 정확한 scope

- **cj-318 §2 의 A-1 + A-2 + A-3 + A-4** = 4 deploy-blocking actions
- **cj-319 §6 의 F4 정정** = Web `.env.local` ❌ / Railway Variables ✅ + apps/api `.env` (local dev only)
- **cj-319 §6 의 신규 2건** = CORS_ORIGINS + NEXT_PUBLIC_API_URL (cj-319 F2 + F3 정직 회복)

**총 6 액션 = A-1 + A-2 + A-3 + A-4 + 신규 CORS_ORIGINS + 신규 NEXT_PUBLIC_API_URL**

### 1.3 정직 인정 — Claude 는 실행 불가

> **본 체크리스트의 모든 step 은 운영자 (kjw) 의 dashboard 로그인 + click + 입력 작업임.**
> Claude 는 코드를 commit/실행할 수 있어도 **실제 운영 환경 (Resend / Supabase / Railway / Vercel) 의 dashboard 액션은 실행할 수 없음**.
> 따라서 본 체크리스트는 **운전자 가이드 문서**이며, 실행은 운영자 본인이 진행.

---

## §2 환경 변수 캡처 (A-1 + A-2 + 신규 CORS_ORIGINS)

### A-1 RESEND_API_KEY + RESEND_FROM_EMAIL 캡처 (~5분)

**선행**: cj-305b wire (`53b8bbf` + `c69dea5`, cj-style 256+257th) 결정 wire 보존 — Resend swap 완료.

| Step | 액션 | 캡처 값 |
|---|---|---|
| 1 | Resend dashboard 로그인 (`resend.com`) | — |
| 2 | **API Keys** → **Create API Key** → Name `costmgr-pilot-w1-prod` + Permission **Full access** | — |
| 3 | API key (`re_xxxxxxxxxx`) 1회만 표시 → 안전한 곳에 저장 (1Password) | `re_xxxxxxxxxx` |
| 4 | Railway service → Variables (production) 입력 | `RESEND_API_KEY=re_xxxxxxxxxx` |
| 5 | Railway service → Variables (production) 입력 | `RESEND_FROM_EMAIL=onboarding@resend.dev` |
| 6 | (Local dev only) `apps/api/.env` 동일 key | `RESEND_API_KEY=re_xxxxxxxxxx` |

**❌ 하지 말 것** (cj-319 F4 정정):
- `apps/web/.env.local` 에 `RESEND_API_KEY` 입력 ❌ (서버 전용 시크릿, Next.js web 참조 0건)
- `NEXT_PUBLIC_RESEND_API_KEY` ❌ (클라이언트 번들 노출 위험)

**Verify gate**:
- [ ] Railway Variables: `RESEND_API_KEY` ✅
- [ ] Railway Variables: `RESEND_FROM_EMAIL=onboarding@resend.dev` ✅
- [ ] `apps/api/.env` (local dev only): `RESEND_API_KEY` ✅

**Risk**: LOW

### A-2 SUPABASE_JWT_SECRET 캡처 (~5분)

**선행**: cj-308 wire 결정 wire 보존 — Supabase Pro project 생성 완료.

| Step | 액션 | 캡처 값 |
|---|---|---|
| 1 | Supabase dashboard → costmgr-pilot project → **Settings** → **API** | — |
| 2 | **JWT Secret** 클릭 → Copy | `<jwt-secret>` |
| 3 | 안전한 곳에 저장 (1Password) | — |
| 4 | Railway service → Variables (production) 입력 | `SUPABASE_JWT_SECRET=<jwt-secret>` |
| 5 | (Local dev only) `apps/api/.env` 동일 JWT | `SUPABASE_JWT_SECRET=<jwt-secret>` |

**❌ 하지 말 것** (cj-319 F4 정정):
- `apps/web/.env.local` 에 `SUPABASE_JWT_SECRET` 입력 ❌ (서버 전용 시크릿)
- git commit ❌ + client-side 노출 ❌

**Verify gate**:
- [ ] Railway Variables: `SUPABASE_JWT_SECRET` ✅
- [ ] `apps/api/.env` (local dev only): `SUPABASE_JWT_SECRET` ✅

**Risk**: LOW

### 신규 CORS_ORIGINS Railway Variables (cj-319 F2 정직 회복)

**선행**: cj-319 wire 결정 wire 보존 — `apps/api/main.py` 에 `CORSMiddleware` 등록 완료.

| Step | 액션 | 캡처 값 |
|---|---|---|
| 1 | Railway service → Variables (production) 입력 | `CORS_ORIGINS=https://costmgr-pilot.vercel.app` |

**왜 필수인가**:
- `vercel.json` 의 CSP `connect-src ... https://*.railway.app` 는 브라우저가 Vercel(web) → Railway(API) cross-origin 호출 구조 전제
- `apps/web/lib/**` 의 `apiBaseUrl()` 도 절대 origin 조립
- CORS 헤더 없으면 **브라우저가 전 API 호출 차단** → Track A-4 live signup smoke test 실패 확정

**Verify gate**:
- [ ] Railway Variables: `CORS_ORIGINS=https://costmgr-pilot.vercel.app` ✅

**Risk**: LOW (cj-319 wire 의 fail-closed 기본값 = 미설정 시 `["http://localhost:3000"]` 만 허용)

### 신규 NEXT_PUBLIC_API_URL Vercel Environment Variables (cj-319 F3 정직 회복)

**선행**: cj-319 wire 결정 wire 보존 — `apps/web/.env.example` 에 `NEXT_PUBLIC_API_URL` 추가 완료.

| Step | 액션 | 캡처 값 |
|---|---|---|
| 1 | Railway service URL 확인 (e.g. `https://costmgr-pilot-api.up.railway.app`) | `<service-url>` |
| 2 | Vercel project → Settings → Environment Variables 입력 | `NEXT_PUBLIC_API_URL=<service-url>` |

**왜 필수인가**:
- `apps/web/lib/audit/audit-log-client.ts:82-85` 등이 `process.env.NEXT_PUBLIC_API_URL` 읽음, 없으면 `http://localhost:8765` 로 fallback
- 운영자가 Vercel 에 누락하면 **파일럿 프론트엔드가 localhost 를 호출** → 전 API 호출 실패

**Verify gate**:
- [ ] Vercel Environment Variables: `NEXT_PUBLIC_API_URL=<service-url>` ✅

**Risk**: LOW

---

## §3 Supabase Auth dashboard live verify (A-3, ~10분)

**선행**: cj-307 aal1 minimum fix (`a1cb7ad`, cj-style 261st) + cj-308 결정 wire 보존 — Confirm email OFF.

| Step | 액션 | 검증 값 |
|---|---|---|
| 1 | Supabase dashboard → **Authentication** → **Providers** → **Email** | — |
| 2 | Email provider **Enabled** ✅ ON 확인 | ✅ |
| 3 | **Confirm email** ❌ OFF 확인 (cj-307 aal1 fix 보존) | ❌ |
| 4 | **Authentication** → **URL Configuration** → **Site URL** | `https://costmgr-pilot.vercel.app` |
| 5 | **Redirect URLs** 3개 등록 | ① `https://costmgr-pilot.vercel.app/auth/callback` ② `https://costmgr-pilot.vercel.app/dashboard` ③ `http://localhost:3000/auth/callback` |
| 6 | **Database** → **Policies** 메뉴 → RLS policies 활성 확인 (cj-303 + cj-314 wire 1 보존) | ✅ |
| 7 | Dashboard screenshot capture (GV-3 evidence) | `.png` 1장 |

**Verify gate**:
- [ ] Email provider Enabled ✅ ON
- [ ] Confirm email ❌ OFF
- [ ] Site URL = `https://costmgr-pilot.vercel.app`
- [ ] Redirect URLs 3개 등록 완료
- [ ] RLS policies 활성

**Risk**: LOW

---

## §4 Live signup smoke test (A-4, ~15-30분)

**선행**: §2 + §3 모두 완료 후에만 실행 가능 (CORS_ORIGINS + NEXT_PUBLIC_API_URL 양쪽 채워진 상태).

| Step | 액션 | 검증 값 |
|---|---|---|
| 1 | Vercel production URL 접속 (`https://costmgr-pilot.vercel.app`) | 200 OK |
| 2 | **Sign Up** (test email 1, e.g. `smoketest1@gmail.com`) | signup 성공 |
| 3 | Confirm email OFF → 즉시 dashboard 진입 (cj-307 aal1 fix 보존) | dashboard 진입 ✅ |
| 4 | CSV 업로드 또는 report 생성 (1개 동작) | 동작 성공 |
| 5 | **Logout** → 재-login | 재-login 성공 |
| 6 | dashboard 재진입 + 잔여 데이터 확인 | 정상 |
| 7 | **2nd signup** (test email 2, e.g. `smoketest2@gmail.com`) → multi-tenant 격리 검증 | tenant 격리 ✅ |
| 8 | Verify-gate-results 형식 capture (GV-5) | `.md` 1건 |
| 9 | 2 test 계정 삭제 (cleanup) | DB 정리 완료 |

**Verify gate** (Track C C-1 6-surface 종합 verify 의 Surface 3+4 검증):
- [ ] signup → dashboard → logout → re-login PASS
- [ ] 2nd signup 격리 PASS
- [ ] CSV 업로드 / report 생성 1개 동작 PASS
- [ ] GV-5 verify-gate-results capture 완료

**Risk**: MEDIUM

---

## §5 종합 timeline + 우선순위

### 5.1 시간 추정

| 액션 | 시간 | 위험도 |
|---|---|---|
| §2 A-1 Resend | ~5분 | LOW |
| §2 A-2 Supabase JWT | ~5분 | LOW |
| §2 신규 CORS_ORIGINS | ~1분 | LOW |
| §2 신규 NEXT_PUBLIC_API_URL | ~1분 | LOW |
| §3 A-3 Auth dashboard verify | ~10분 | LOW |
| §4 A-4 Live signup smoke test | ~15-30분 | MEDIUM |
| **총합** | **~37-52분** | **LOW-MEDIUM** |

### 5.2 우선순위 (cj-319 §6 verbatim mirror)

| 우선순위 | 액션 | 이유 |
|---|---|---|
| 1 | §2 A-1 + A-2 + 신규 2건 | deploy-blocking — §4 A-4 의 선행 조건 |
| 2 | §3 A-3 | Supabase Auth 검증 — §4 A-4 의 선행 조건 |
| 3 | §4 A-4 | Live signup smoke test — Track C C-1 의 Surface 3+4 검증 |

**§2 + §3 완료 후 §4 진입 권장** — §4 가 §2 + §3 모두에 의존.

### 5.3 실패 시 fallback

| 실패 지점 | fallback |
|---|---|
| §2 A-1 Resend API key 캡처 실패 | Resend status page 확인 → 재시도 |
| §2 A-2 Supabase JWT 캡처 실패 | Supabase status page 확인 → 재시도 |
| §3 A-3 Email provider enabled OFF | Supabase dashboard 에서 즉시 ON |
| §3 A-3 Confirm email ON | 즉시 OFF 전환 (cj-307 결정 wire 보존) |
| §4 A-4 signup 실패 | CORS_ORIGINS + NEXT_PUBLIC_API_URL 양쪽 확인 → Railway logs 확인 → Supabase Auth logs 확인 |
| §4 A-4 2nd signup 격리 실패 | Supabase RLS policies 확인 → cj-314 wire 1 의 capability matrix EXTENSION 정합 확인 |

---

## §6 결정 wire 보존

- **cj-318 operator immediate execution entry** (`241fd3a`, cj-style 284th) 결정 wire 보존 — §2 의 A-1~A-4 원본 정의
- **cj-319 Track A-0 deploy-blocking wire** (`2249fec`, cj-style 285th) 결정 wire 보존 — §2 의 F4 정정 + 신규 CORS_ORIGINS + NEXT_PUBLIC_API_URL (선행 조건 회복)
- **cj-307 aal1 minimum fix** (`a1cb7ad`, cj-style 261st) 결정 wire 보존 — §3 의 Confirm email OFF
- **cj-305b Postmark → Resend swap** (`53b8bbf` + `c69dea5`, cj-style 256+257th) 결정 wire 보존 — §2 A-1 의 Resend 선택
- **cj-308 Pilot W1 D-5 critical path entry** (`07f06d0`, cj-style 263rd) 결정 wire 보존 — Supabase Pro project
- **cj-303 uvicorn boot fix wire** 결정 wire 보존 (AD-14 stack pin EXTENSION)
- **cj-304 prod deploy prep wire** (`1fdb67d`, cj-style 252nd) 결정 wire 보존 — 4 critical gaps
- **cj-314 wire 1 capability matrix** 결정 wire 보존 — §3 의 RLS policies 활성 검증
- **Pilot W1 launch D-day 2026-09-14 KST 보존**

**83/83 cumulative 결정 wire 보존** (cj-style N+2 의 82 + **NEW 83번째 Track A-1~A-4 운영자 체크리스트**)

---

## §7 결정 보류 (운전자)

① **Track A-1~A-4 실제 실행** (~37-52분, **운전자 본인이 dashboard 에서 진행**, **D-day 직결**)
② **Track B Pilot outreach** (~4h, launch 후 자연스럽게)
③ **Track C D-1 사전 verify** (현재 FINAL CLEAN, 부분 회복됨)
④ cj-314 batch B (post-W1)
⑤ PRD v2 EXTENSION (post-W1)
⑥ N-1 mojibake triage (post-W1)
⑦ epics.md 1478 lines triage (post-W1)
⑧ cj-275 chain retroactive commit 진입 (post-W1)
⑨ **순서: 3 — K-4 wire 3 main runtime execution** (DATABASE_URL env 준비 후, **cj-style N+4 entry decision wire** 진입 결정 보류)

---

## §8 Cross-References

- cj-318 handoff §2 (Track A 4 Deploy-Blocking Actions 원본) → `memory/handoff-2026-09-10-cj-318-operator-immediate-execution-entry-done.md`
- cj-319 handoff §6 (F4 정정 + 신규 CORS_ORIGINS + NEXT_PUBLIC_API_URL 선행 조건) → `memory/handoff-2026-09-10-cj-319-track-a0-deploy-blocking-wire-done.md`
- cj-305b Resend swap 결정 wire (cj-style 256+257th) → `memory/handoff-2026-09-08-cj-305b-resend-migration-done.md`
- cj-307 aal1 minimum fix 결정 wire → `memory/handoff-2026-09-08-cj-307-auth-callback-fix-done.md`
- cj-308 Pilot W1 D-5 critical path entry 결정 wire → `memory/handoff-2026-09-09-cj-308-pilot-w1-d5-critical-path-entry-done.md`

---

**TRACK A-1~A-4 운영자 체크리스트 DONE**

**운전자 액션 가이드**: 본 체크리스트 6 액션을 §2 → §3 → §4 순서로 진행. §2 + §3 완료 후 §4 진입 권장. §4 실패 시 §5.3 fallback 참조.

**Next**: Track A-1~A-4 운영자 실제 실행 (~37-52분) → 순서: 3 — K-4 wire 3 main runtime execution (cj-style N+4 entry decision wire 진입)
