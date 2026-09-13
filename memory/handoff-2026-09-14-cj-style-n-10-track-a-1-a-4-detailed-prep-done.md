---
name: handoff-2026-09-14-cj-style-n-10-track-a-1-a-4-detailed-prep-done
description: "Track A-1~A-4 운영자 실행 prep 확장 (cj-style N+10 wire, 2026-09-14 KST, D-Day Pilot W1 launch) — cj-style N+3 handoff §2-§5 verbatim mirror + 4개 NEW 섹션 (Pre-flight verify + endpoint 부재 영향 degraded verify gate + Evidence capture templates + Emergency rollback + Post-Track-A 후속). K-4 wire 3 honestly DEFER (N+6) + Sprint 0 env-free verified (N+7~N+9) 결과 반영. 운영자 dashboard 작업 효율성 극대화."
metadata:
  node_type: memory
  type: project
  originSessionId: cj-style-310-wire-session
  modified: 2026-09-14T08:00:00.000Z
---

# Track A-1~A-4 운영자 실행 prep 확장 — DONE (cj-style N+10 wire)

**일자**: 2026-09-14 (KST, **D-Day Pilot W1 launch**)
**territory**: Phase 30 — Track A-1~A-4 운영자 dashboard actions prep 확장
**sprint type**: 단일 docs-only 확장 sprint (cj-style N+3 verbatim mirror + 4 NEW 섹션)
**출처**: cj-style N+3 handoff (`handoff-2026-09-13-cj-style-n-3-track-a1-a4-operator-checklist-done.md`) §2-§5 verbatim mirror + 본 sprint NEW 섹션 (§2 Pre-flight + §4 endpoint 부재 영향 + §5 Evidence templates + §6 Emergency rollback + §7 Post-Track-A)

---

## §1 의도 분석 — Track A-1~A-4 운영자 prep 확장의 4가지 신규 섹션

### 1.1 cj-style N+3 의 강점 + 한계 verbatim mirror

> **cj-style N+3 §1.3**: "본 체크리스트의 모든 step 은 운영자 (kjw) 의 dashboard 로그인 + click + 입력 작업임. Claude 는 코드를 commit/실행할 수 있어도 실제 운영 환경 (Resend / Supabase / Railway / Vercel) 의 dashboard 액션은 실행할 수 없음. 따라서 본 체크리스트는 **운전자 가이드 문서**이며, 실행은 운영자 본인이 진행."

**N+3 의 강점 (verbatim mirror 보존)**:
- §2 의 6 액션 (A-1 + A-2 + A-3 + A-4 + 신규 CORS_ORIGINS + 신규 NEXT_PUBLIC_API_URL)
- §5.1 의 시간 추정 (~37-52분)
- §5.2 의 우선순위 (1=§2 / 2=§3 / 3=§4)
- §5.3 의 failure fallback table

**N+10 의 확장 의도** — N+3 작성 이후 발견된 4가지 갭:

1. **Pre-flight verify 갭** — N+3 는 §2 의 step 1 부터 즉시 진입. 운영자가 dashboard access 미보유 / Railway service 미배포 / Vercel project 미연결 상태에서 시작하면 §2 step 1 부터 fail → 시간 낭비 + 비정상 종료 위험. **본 sprint §2 신규**.

2. **Track A-4 endpoint 부재 영향 미반영** — cj-style N+6 (K-4 wire 3 main runtime smoke honestly DEFER post-W1) 결과, **54 cases 모두 404 Not Found** (m3_calculate 2 + m8_budget 1 + 확인 필요 5 = 8건 specifically identified). Track A-4 §4 step 4 의 "CSV 업로드 또는 report 생성 (1개 동작)" 이 일부 endpoint 부재 영향으로 404 가능. 운영자가 이를 "Track A 실패" 로 오인할 위험. **본 sprint §4 신규 (degraded verify gate)**.

3. **Evidence capture 형식 미정의** — N+3 §3 step 7 "Dashboard screenshot capture (GV-3 evidence)" / §4 step 8 "Verify-gate-results 형식 capture (GV-5)" 가 있으나, **capture 형식 자체는 미정의**. 운영자가 어떤 파일명/경로/형식으로 저장해야 할지 모호. **본 sprint §5 신규**.

4. **Emergency rollback 절차 미정의** — N+3 §5.3 은 "실패 시 fallback" 만 있고, **Railway service 가 production 에 잘못 배포** / **Supabase RLS 가 비활성화** / **CORS_ORIGINS 가 와일드카드** 같은 D-Day-critical rollback 시나리오 미커버. **본 sprint §6 신규**.

5. **Post-Track-A 후속 미정의** — N+3 §7 결정 보류 에는 있으나, **Track A 완료 후 다음 1시간 이내 무엇을 해야 하는지** 미정의. 결정 보류 #1 (Sprint 1 actual run) 진입이 자연스러우나, Track A 와의 연결 고리 미서술. **본 sprint §7 신규**.

### 1.2 본 sprint 의 정확한 scope

- **NEW 섹션**: §2 Pre-flight + §4 endpoint 부재 영향 + §5 Evidence templates + §6 Emergency rollback + §7 Post-Track-A
- **verbatim mirror 섹션**: §3 Track A-1~A-4 + 신규 CORS/NEXT_PUBLIC 운영자 체크리스트 (N+3 §2~§4)
- **업데이트 섹션**: §8 결정 wire + §9 결정 보류 + §10 Cross-References

### 1.3 정직 인정 — Claude 는 실행 불가 (N+3 §1.3 verbatim mirror)

> **본 prep 확장의 모든 step 은 운영자 (kjw) 의 dashboard 로그인 + click + 입력 작업임.** Claude 는 코드를 commit/실행할 수 있어도 실제 운영 환경 (Resend / Supabase / Railway / Vercel) 의 dashboard 액션은 실행할 수 없음. 따라서 본 prep 확장은 **운전자 가이드 문서**이며, 실행은 운영자 본인이 출근 후 진행.

---

## §2 Pre-flight verify — Track A 시작 전 (NEW, ~3-5분)

### 2.1 의도

N+3 의 §2 부터 즉시 진입 시, dashboard access 미보유 / service 미배포 / project 미연결 상태에서 fail 하면 ~5분 손실 + 비정상 종료 위험. **본 섹션은 Track A 시작 ~3-5분 전 운영자가 반드시 verify 하는 5 항목**.

### 2.2 5개 Pre-flight 항목

| # | 항목 | 확인 방법 | 통과 기준 | 실패 시 |
|---|---|---|---|---|
| 1 | **Railway service deployed** | Railway dashboard → costmgr-pilot-api service → **Deployments** 탭 | Latest deployment **Success** 상태, ~10분 이내 빌드 | Service 가 **Building** / **Crashed** / **Not deployed** → §6.1 rollback |
| 2 | **Vercel project connected** | Vercel dashboard → costmgr-pilot project → **Deployments** 탭 | Latest production deployment **Ready** 상태 | **Building** / **Error** → §6.2 rollback |
| 3 | **Resend API key 존재 (test 또는 prod)** | Resend dashboard → **API Keys** | 최소 1개 API key 존재 (기존 prod key 또는 새로 생성) | 0건 → A-1 에서 즉시 생성 (정상) |
| 4 | **Supabase project access** | Supabase dashboard → costmgr-pilot project 진입 가능 | project home 진입 시 200 OK, Authentication 메뉴 진입 가능 | **Access denied** / **Project not found** → §6.3 rollback |
| 5 | **Vercel production URL live** | 브라우저에서 `https://costmgr-pilot.vercel.app` 접속 | 200 OK + 로그인 페이지 렌더 (Track A-4 step 1 사전 확인) | **404** / **Domain not configured** → §6.4 rollback |

### 2.3 Pre-flight verify gate

**§2 통과 후에만 §3 진입 권장**. §2 fail 시 §3 시작하지 말 것.

- [ ] Railway service deployed ✅
- [ ] Vercel project connected ✅
- [ ] Resend API key 존재 ✅
- [ ] Supabase project access ✅
- [ ] Vercel production URL live ✅

**Risk**: LOW (단순 dashboard 확인, ~3-5분)

---

## §3 Track A-1~A-4 + 신규 CORS/NEXT_PUBLIC 운영자 체크리스트 (cj-style N+3 verbatim mirror)

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

### A-3 Supabase Auth dashboard live verify (~10분)

**선행**: cj-307 aal1 minimum fix (`a1cb7ad`, cj-style 261st) + cj-308 결정 wire 보존 — Confirm email OFF.

| Step | 액션 | 검증 값 |
|---|---|---|
| 1 | Supabase dashboard → **Authentication** → **Providers** → **Email** | — |
| 2 | Email provider **Enabled** ✅ ON 확인 | ✅ |
| 3 | **Confirm email** ❌ OFF 확인 (cj-307 aal1 fix 보존) | ❌ |
| 4 | **Authentication** → **URL Configuration** → **Site URL** | `https://costmgr-pilot.vercel.app` |
| 5 | **Redirect URLs** 3개 등록 | ① `https://costmgr-pilot.vercel.app/auth/callback` ② `https://costmgr-pilot.vercel.app/dashboard` ③ `http://localhost:3000/auth/callback` |
| 6 | **Database** → **Policies** 메뉴 → RLS policies 활성 확인 (cj-303 + cj-314 wire 1 보존) | ✅ |
| 7 | Dashboard screenshot capture (GV-3 evidence) → §5.1 형식 | `.png` 1장 |

**Verify gate**:
- [ ] Email provider Enabled ✅ ON
- [ ] Confirm email ❌ OFF
- [ ] Site URL = `https://costmgr-pilot.vercel.app`
- [ ] Redirect URLs 3개 등록 완료
- [ ] RLS policies 활성

**Risk**: LOW

### A-4 Live signup smoke test (~15-30분)

**선행**: §3 A-1 + A-2 + 신규 2건 + A-3 모두 완료 후에만 실행 가능.

| Step | 액션 | 검증 값 |
|---|---|---|
| 1 | Vercel production URL 접속 (`https://costmgr-pilot.vercel.app`) | 200 OK |
| 2 | **Sign Up** (test email 1, e.g. `smoketest1@gmail.com`) | signup 성공 |
| 3 | Confirm email OFF → 즉시 dashboard 진입 (cj-307 aal1 fix 보존) | dashboard 진입 ✅ |
| 4 | CSV 업로드 또는 report 생성 (1개 동작) — **§4 endpoint 부재 영향 참조** | 동작 성공 (또는 §4 degraded verify gate 통과) |
| 5 | **Logout** → 재-login | 재-login 성공 |
| 6 | dashboard 재진입 + 잔여 데이터 확인 | 정상 |
| 7 | **2nd signup** (test email 2, e.g. `smoketest2@gmail.com`) → multi-tenant 격리 검증 | tenant 격리 ✅ |
| 8 | Verify-gate-results 형식 capture (GV-5) → §5.2 형식 | `.md` 1건 |
| 9 | 2 test 계정 삭제 (cleanup) | DB 정리 완료 |

**Verify gate (기본)**:
- [ ] signup → dashboard → logout → re-login PASS
- [ ] 2nd signup 격리 PASS
- [ ] CSV 업로드 / report 생성 1개 동작 PASS (또는 §4 degraded verify gate 적용)
- [ ] GV-5 verify-gate-results capture 완료

**Risk**: MEDIUM

---

## §4 Track A-4 endpoint 부재 영향 + degraded verify gate (NEW, cj-style N+6 honestly DEFER 반영)

### 4.1 의도

**cj-style N+6 (K-4 wire 3 main runtime smoke honestly DEFER post-W1) 결과**:
- `cost_engine` 577/1 skip ✅ (cj-style N+7 의 embedded-postgres fixture 정상)
- `test_k4_wire_3` **54 cases 모두 404 Not Found**
- specifically identified: m3_calculate 2건 + m8_budget 1건 + 확인 필요 5건 = **8건**

이는 **production API endpoint 자체가 부재**함을 의미. Track A-4 §3 A-4 step 4 의 "CSV 업로드 또는 report 생성 (1개 동작)" 이 일부 endpoint 부재 영향으로 404 가능.

**운영자가 이를 "Track A 실패" 로 오인하지 않도록** 본 섹션에서 영향 범위 + degraded verify gate 명시.

### 4.2 영향 범위 (cj-style N+6 verbatim mirror)

| Endpoint category | 부재 건수 | Track A-4 영향 | 운영자 액션 |
|---|---|---|---|
| **m3_calculate** | 2 | CSV 업로드 (M6 close_period 일부) 가 404 가능 | M5 report 생성 으로 fallback |
| **m8_budget** | 1 | Budget endpoint 호출 시 404 가능 | Dashboard 표시만 verify (write 액션 skip) |
| **확인 필요 5건** | 5 | CSV 업로드 + report 생성 모두 영향 가능 | 양쪽 모두 404 시 §4.3 degraded verify gate 적용 |
| **합계** | **8 specifically identified** | — | — |

**참고**: cj-style N+6 의 `test_k4_wire_3` 54 failed cases 는 모두 404 Not Found 이며, **8건 만 specifically identified** (나머지 46건 은 sprint 1.1+ 에서 추가 triage).

### 4.3 Degraded verify gate (Track A-4 step 4 실패 시 적용)

**§3 A-4 step 4 의 "CSV 업로드 또는 report 생성 (1개 동작)" 이 404 시**:

| 조건 | 판정 | 다음 액션 |
|---|---|---|
| Step 4 동작 1개 이상 성공 (CSV 업로드 또는 report 생성 중 어느 하나) | **Track A-4 PASS** (정상) | Step 5-9 계속 진행 |
| Step 4 두 동작 모두 404 | **Track A-4 DEGRADED PASS** (honestly DEFER 인정) | Step 5-9 계속 진행 + §5.3 GV-5 capture 에 "step 4 404" honestly 기록 |
| Step 4 그 외 다른 에러 (CORS / 500 / network) | **Track A-4 FAIL** | §6 emergency rollback 진입 |

### 4.4 verify gate 결과 honestly DEFER chain 보존

본 §4 의 degraded verify gate 는 **cj-style N+6 의 honestly DEFER post-W1 chain 의 Track A-4 mirror**:
- **cj-style N+6 의 결정**: endpoint 부재 54건 honestly DEFER post-W1 (Pilot W1 launch 후 회복)
- **본 §4 의 결정**: Track A-4 step 4 가 endpoint 부재 영향 시 **Track A-4 전체 fail 이 아닌 DEGRADED PASS** 로 판정
- **Track A-4 본질** = dashboard 진입 + logout + 재-login + multi-tenant 격리 = **signup/auth 흐름의 end-to-end 검증**. CSV/report 는 1개 동작 smoke 일 뿐, **endpoint 부재 ≠ Track A 실패**.

### 4.5 §3 A-4 verify gate 업데이트

**§3 A-4 verify gate 의 "CSV 업로드 / report 생성 1개 동작 PASS" 항목** 을 다음으로 교체:

- [ ] CSV 업로드 / report 생성 1개 동작 PASS (정상), 또는
- [ ] 위 항목 404 시 §4.3 degraded verify gate 적용 (DEGRADED PASS + §5.3 honestly 기록)

**Risk**: LOW-MEDIUM (degraded verify gate 추가로 운영자 confusion 방지)

---

## §5 Evidence capture templates (NEW)

### 5.1 GV-3 Dashboard screenshot 캡처 형식 (§3 A-3 step 7)

**파일명**: `gv-3-supabase-auth-config-{YYYYMMDD-HHMM}.png`

**캡처 위치**:
- `_bmad-output/cj-evidence/gv-3-supabase-auth-config-20260914-0800.png` (예시)
- 또는 운영자 지정 evidence 디렉토리

**캡처 내용 (1장 또는 2장)**:
- 1장: **Authentication → Providers → Email** 화면 — Email provider Enabled ✅ ON + Confirm email ❌ OFF 동시 보임
- 2장 (선택): **Authentication → URL Configuration** 화면 — Site URL + Redirect URLs 3개

**Risk**: LOW

### 5.2 GV-5 Verify-gate-results 캡처 형식 (§3 A-4 step 8)

**파일명**: `gv-5-track-a-4-verify-gate-results-{YYYYMMDD-HHMM}.md`

**템플릿**:

```markdown
# Track A-4 Live Signup Smoke Test — Verify Gate Results

**일자**: 2026-09-14 (KST, D-Day)
**환경**: https://costmgr-pilot.vercel.app (production)
**테스트 계정**: smoketest1@gmail.com, smoketest2@gmail.com

## §3 A-4 Verify Gate Results

| Step | 결과 | 비고 |
|---|---|---|
| 1. Vercel production URL 접속 | ✅ PASS / ❌ FAIL | (200 OK 확인) |
| 2. Sign Up (test email 1) | ✅ PASS / ❌ FAIL | (signup 성공) |
| 3. Confirm email OFF → 즉시 dashboard 진입 | ✅ PASS / ❌ FAIL | (dashboard 진입) |
| 4. CSV 업로드 또는 report 생성 (1개 동작) | ✅ PASS / ❌ FAIL / ⚠️ DEGRADED | (§4.3 적용 시 ⚠️ DEGRADED) |
| 5. Logout → 재-login | ✅ PASS / ❌ FAIL | (재-login 성공) |
| 6. dashboard 재진입 + 잔여 데이터 확인 | ✅ PASS / ❌ FAIL | (정상) |
| 7. 2nd signup multi-tenant 격리 검증 | ✅ PASS / ❌ FAIL | (tenant 격리) |
| 8. Verify-gate-results capture | ✅ PASS | (본 파일) |
| 9. 2 test 계정 삭제 (cleanup) | ✅ PASS / ❌ FAIL | (DB 정리 완료) |

## §4.3 Degraded Verify Gate 적용 여부

(적용 시) Step 4 가 404 발생 → §4.3 degraded verify gate 적용 → **DEGRADED PASS** 판정.

## 종합 판정

- **PASS**: 모든 step ✅
- **DEGRADED PASS**: step 4 만 ⚠️ DEGRADED, 나머지 ✅
- **FAIL**: step 4 외 다른 step ❌ → §6 emergency rollback 진입

## 결정 보류 (다음 sprint)

(필요 시) Sprint 1 actual run 진입 시 이 GV-5 결과를 인용.
```

**Risk**: LOW

### 5.3 honestly 기록 의무 (cj-style discipline)

§3 A-4 step 4 가 **404 인 경우 반드시 §5.2 템플릿의 "§4.3 Degraded Verify Gate 적용 여부" 섹션에 honestly 기록**. **"step 4 가 404 인데 PASS 로 적기"** 는 cj-style discipline 위반 (cj-style 257/267/304/305/306/307 + N-1/N+1/N+2/N+3/N+4/N+5/N+6/N+7/N+8/N+9 honest-DEFER chain 의 267번째).

**Risk**: LOW (절차 준수만으로 OK)

---

## §6 Emergency rollback procedures (NEW)

### 6.1 Railway service 잘못 배포 시

**시나리오**: §3 의 Variables 입력 중 잘못된 값 (e.g., `CORS_ORIGINS=*` 와일드카드, `RESEND_FROM_EMAIL` 오타) → production API 영향.

**즉시 회복 절차**:

| Step | 액션 | 결과 |
|---|---|---|
| 1 | Railway dashboard → costmgr-pilot-api → **Variables** | 잘못된 변수 확인 |
| 2 | 잘못된 변수 **수정** (e.g., `CORS_ORIGINS=https://costmgr-pilot.vercel.app` 로 변경) | 즉시 redeploy 트리거 |
| 3 | **Deployments** 탭 → 새 deployment **Success** 대기 (~2-3분) | production 정상화 |
| 4 | Track A-4 §3 step 1-2 재실행 (Vercel production URL 정상 확인) | PASS 시 §3 step 3-9 계속 |

**Rollback time**: ~3-5분

### 6.2 Vercel project 빌드 실패 시

**시나리오**: §3 신규 NEXT_PUBLIC_API_URL 입력 후 Vercel 자동 redeploy 트리거 → 빌드 실패.

**즉시 회복 절차**:

| Step | 액션 | 결과 |
|---|---|---|
| 1 | Vercel dashboard → costmgr-pilot → **Deployments** → 실패한 deployment 확인 | 빌드 로그 확인 |
| 2 | **Settings** → **Environment Variables** → `NEXT_PUBLIC_API_URL` 값 재확인 (URL 형식, trailing slash 없음 등) | 형식 오류 시 수정 |
| 3 | Vercel 자동 redeploy 대기 (또는 **Redeploy** 버튼 수동 클릭) | 새 빌드 시도 |
| 4 | 빌드 **Success** 후 Track A-4 §3 step 1 재실행 | PASS 시 §3 step 2-9 계속 |

**Rollback time**: ~3-5분

### 6.3 Supabase RLS 비활성화 시

**시나리오**: §3 A-3 step 6 의 RLS policies 확인 중 실수로 RLS OFF 전환 (또는 별도 작업 중 RLS 영향).

**즉시 회복 절차**:

| Step | 액션 | 결과 |
|---|---|---|
| 1 | Supabase dashboard → costmgr-pilot → **Database** → **Policies** | RLS 상태 확인 |
| 2 | RLS OFF 확인 시 → 해당 테이블 (e.g., `tenants`, `users`) → **Enable RLS** 클릭 | 즉시 활성화 |
| 3 | cj-314 wire 1 의 capability matrix EXTENSION 정합 확인 (변경된 policy 없는지) | 정책 변경 없으면 OK |
| 4 | Track A-4 §3 step 7 의 2nd signup 격리 재실행 | PASS 확인 |

**Rollback time**: ~2-3분

### 6.4 Vercel production URL 404 / Domain not configured 시

**시나리오**: §2 Pre-flight step 5 또는 §3 A-4 step 1 에서 Vercel URL 접속 시 404.

**즉시 회복 절차**:

| Step | 액션 | 결과 |
|---|---|---|
| 1 | Vercel dashboard → costmgr-pilot → **Settings** → **Domains** | 도메인 상태 확인 |
| 2 | `costmgr-pilot.vercel.app` 도메인 **Valid Configuration** 상태인지 확인 | Invalid 시 **Edit** → DNS 확인 |
| 3 | production deployment 가 도메인에 연결되어 있는지 확인 | 미연결 시 **Redeploy** |
| 4 | 도메인 정상화 후 Track A-4 §3 step 1 재실행 | PASS 시 §3 step 2-9 계속 |

**Rollback time**: ~3-5분 (DNS propagation 대기 시 +5-10분)

### 6.5 Emergency rollback 종합 gate

**§6 의 어느 시나리오든 rollback 후**:
- [ ] Production 환경 정상화 확인 (Vercel URL 200 OK + Railway service running)
- [ ] Track A-4 §3 step 1-9 재실행 가능 상태
- [ ] §5.2 GV-5 verify-gate-results capture 시 rollback 이력 honestly 기록

**Risk**: MEDIUM (production 환경 영향 가능성)

---

## §7 Post-Track-A 후속 가이드 (NEW)

### 7.1 의도

**Track A-1~A-4 완료 후 다음 1시간 이내 무엇을 해야 하는지** 정의. 결정 보류 #1 (Sprint 1 actual run) 자연스러운 진입 + 결정 보류 #9 (Track C D-1 사전 verify) 보완.

### 7.2 Track A 완료 후 3 액션 (총 ~30분)

| # | 액션 | 시간 | 출처 |
|---|---|---|---|
| **P-1** | §5.2 GV-5 verify-gate-results 최종 commit + 본 handoff 의 결정 보류 §9 업데이트 | ~5분 | 운영자 |
| **P-2** | **Track C D-1 사전 verify (C-1 6-surface 종합 verify 중 Surface 3+4 부분 회복 검증)** | ~15분 | 결정 보류 #9, Track A-4 가 Surface 3 (signup) + Surface 4 (multi-tenant 격리) 부분 회복 |
| **P-3** | **Sprint 1 actual run entry 결정** (cj-style N+4 의 entry decision wire 진입 결정) | ~10분 | 결정 보류 #1, Track A + Track C 완료 후 K-4 wire 3 main runtime execution 진입 가능 |

### 7.3 P-2 Track C D-1 사전 verify (간소화)

Track A-4 가 다음을 이미 verify 함:
- Surface 3 (signup) → Track A-4 §3 step 2-3 ✅
- Surface 4 (multi-tenant 격리) → Track A-4 §3 step 7 ✅

따라서 Track C D-1 사전 verify 는 **Surface 1 (Railway health) + Surface 2 (Vercel health) + Surface 5 (CSV export) + Surface 6 (report generation)** 의 4 surface 만 verify (~15분).

| Surface | verify 방법 | 시간 |
|---|---|---|
| 1. Railway health | `curl https://<service-url>/health` 200 OK | ~2분 |
| 2. Vercel health | 브라우저 `https://costmgr-pilot.vercel.app` 200 OK + homepage render | ~2분 |
| 5. CSV export | 로그인 후 M5/M6 dashboard 에서 CSV export 1건 다운로드 | ~5분 (또는 §4.3 degraded verify gate) |
| 6. Report generation | 로그인 후 M5 dashboard 에서 report 생성 1건 | ~5분 (또는 §4.3 degraded verify gate) |

**Risk**: LOW

### 7.4 P-3 Sprint 1 actual run entry 결정

cj-style N+4 handoff (`handoff-2026-09-13-cj-style-n-4-k4-wire-3-main-runtime-execution-entry-done.md`) 의 결정 wire 진입 결정:

- **DATABASE_URL env 의존 결정**: 옵션 (a) 스크립트 내부 `os.environ.setdefault()` ✅ (cj-style N+7 + N+9 에서 env-free verified)
- **Sprint 1 actual run scope**: skipif guard 해제 + 100 cases actual pytest
- **진입 시점**: Track A + Track C 완료 후 즉시

본 §7.4 는 **P-3 의 "진입 결정" 만** 다루며, 실제 Sprint 1 actual run 실행은 cj-style N+11+ 후속 sprint.

**Risk**: LOW (decision wire only)

### 7.5 결정 보류 업데이트 (§9 verbatim mirror)

본 §7 의 P-1 + P-2 + P-3 완료 후:
- 결정 보류 #1 (Sprint 1 actual run) **entry decision** → 해소
- 결정 보류 #7 (Track A-1~A-4 운영자 실제 실행) → 해소
- 결정 보류 #9 (Track C D-1 사전 verify) → 부분 해소 (Surface 3+4 Track A-4 에서 회복, Surface 1+2+5+6 Track C 에서 회복)

---

## §8 결정 wire 보존

- **cj-style N+3 Track A-1~A-4 운영자 체크리스트** (`ef3326f`, 5 files atomic, cj-style 256th) 결정 wire 보존 — 본 §3 verbatim mirror 원본
- **cj-style N+4 K-4 wire 3 main runtime execution entry decision wire** (`f99e86d`, cj-style 257th) 결정 wire 보존 — 본 §7.4 의 Sprint 1 entry 결정 기반
- **cj-style N+5 MVP readiness 정직 평가** (`1c9fdb6`, cj-style 258th) 결정 wire 보존 — 본 §4 의 honestly DEFER chain 정합
- **cj-style N+6 K-4 wire 3 main runtime smoke honestly DEFER post-W1** (`1aa6519`, cj-style 259th) 결정 wire 보존 — **본 §4 endpoint 부재 영향 + degraded verify gate 의 verbatim mirror 출처**
- **cj-style N+7 Sprint 0 환경 준비** (`dae1887`, cj-style 260th) 결정 wire 보존 — embedded-postgres env-free 패턴
- **cj-style N+8 Sprint 0 부트스트랩** (`dde3f61`, cj-style 261st) 결정 wire 보존 — alembic + seed + orchestration
- **cj-style N+9 Sprint 0 부트스트랩 close-out + env-free fix-forward** (`05470a7`, cj-style 262nd) 결정 wire 보존 — env-free fix-forward + 본 §7.4 의 DATABASE_URL env-free 결정 기반
- **cj-style 307 aal1 minimum fix** (`a1cb7ad`, cj-style 261st) 결정 wire 보존 — §3 A-3 의 Confirm email OFF
- **cj-305b Postmark → Resend swap** (`53b8bbf` + `c69dea5`, cj-style 256+257th) 결정 wire 보존 — §3 A-1 의 Resend 선택
- **cj-308 Pilot W1 D-5 critical path entry** (`07f06d0`, cj-style 263rd) 결정 wire 보존 — Supabase Pro project
- **cj-319 Track A-0 deploy-blocking wire** (`2249fec`, cj-style 285th) 결정 wire 보존 — §3 의 F4 정정 + 신규 CORS_ORIGINS + NEXT_PUBLIC_API_URL
- **cj-318 operator immediate execution entry** (`241fd3a`, cj-style 284th) 결정 wire 보존 — §3 의 A-1~A-4 원본 정의
- **cj-303 uvicorn boot fix wire** 결정 wire 보존 (AD-14 stack pin EXTENSION)
- **cj-304 prod deploy prep wire** (`1fdb67d`, cj-style 252nd) 결정 wire 보존 — 4 critical gaps
- **cj-314 wire 1 capability matrix** 결정 wire 보존 — §3 A-3 의 RLS policies 활성 검증
- **Pilot W1 launch D-day 2026-09-14 KST 보존**

**92/92 cumulative 결정 wire 보존** (cj-style N+9 의 91 + **NEW 92번째 Track A-1~A-4 운영자 실행 prep 확장**)

---

## §9 결정 보류 (운전자)

### 9.1 본 sprint 후속 (~30분, 결정 보류 해소 권장)

① **P-1** (§7.2): §5.2 GV-5 verify-gate-results 최종 commit + 본 handoff 의 결정 보류 §9 업데이트 (~5분, **Track A 완료 즉시**)
② **P-2** (§7.3): Track C D-1 사전 verify — Surface 1+2+5+6 4-surface verify (~15분, **Track A 완료 후 즉시**)
③ **P-3** (§7.4): Sprint 1 actual run entry 결정 (cj-style N+4 entry decision wire 진입, ~10분, **Track A + Track C 완료 후**)

### 9.2 결정 보류 해소 (cj-style N+9 chain verbatim mirror)

| 결정 보류 ID | 내용 | 본 sprint 영향 |
|---|---|---|
| #7 Track A-1~A-4 운영자 실제 실행 | §2 pre-flight + §3 6 액션 + §4 endpoint 부재 영향 + §5 evidence + §6 emergency rollback | **본 sprint §3 의 prep 확장으로 운영자 효율성 극대화**. 결정 보류 #7 자체는 **Track A 실제 실행 완료 시 해소** |
| #1 Sprint 1 actual run | K-4 wire 3 main runtime execution actual run | 본 §7.4 의 entry 결정 후 cj-style N+11+ 에서 실행 |
| #9 Track C D-1 사전 verify | 6-surface 종합 verify | 본 §7.3 의 P-2 로 Track A 완료 후 즉시 진입 |

### 9.3 결정 보류 verbatim mirror (cj-style N+9 §9 보존)

- ① Sprint 1 actual run (embedded-postgres 자동)
- ② Sprint 1.1 skipif guard 해제 (cj-style N+7 의 env-free verified 후 자동 결정 가능)
- ③ Sprint 1.2 alembic upgrade head (cj-style N+9 에서 env-free verified)
- ④ Sprint 1.3 Seed data (cj-style N+9 에서 env-free verified)
- ⑤ Sprint 2 Endpoint 부재 54건 회복 (m3_calculate 2 + m8_budget 1 + 확인 필요 5 specifically identified)
- ⑥ Sprint 3 End-to-end 시나리오 manual click verify (Login → 각 module → export)
- ⑦ Track B Pilot outreach (~4h, launch 후)
- ⑧ 결정 보류 11건 honestly DEFER post-MVP

---

## §10 Cross-References

- **cj-style N+3 Track A-1~A-4 운영자 체크리스트 원본** → `memory/handoff-2026-09-13-cj-style-n-3-track-a1-a4-operator-checklist-done.md`
- **cj-style N+4 K-4 wire 3 main runtime execution entry** → `memory/handoff-2026-09-13-cj-style-n-4-k4-wire-3-main-runtime-execution-entry-done.md`
- **cj-style N+5 MVP readiness 정직 평가** → `memory/handoff-2026-09-13-cj-style-n-5-mvp-readiness-honest-assessment-done.md`
- **cj-style N+6 K-4 wire 3 main runtime smoke honestly DEFER** → `memory/handoff-2026-09-13-cj-style-n-6-k4-wire-3-runtime-smoke-honestly-defer-post-w1-done.md` (**본 §4 의 verbatim mirror 출처**)
- **cj-style N+7 Sprint 0 환경 준비** → `memory/handoff-2026-09-13-cj-style-n-7-sprint-0-env-prep-embedded-pg-done.md`
- **cj-style N+8 Sprint 0 부트스트랩** → `memory/handoff-2026-09-13-cj-style-n-8-sprint-0-bootstrap-done.md`
- **cj-style N+9 Sprint 0 부트스트랩 close-out + env-free fix-forward** → `memory/handoff-2026-09-13-cj-style-n-9-sprint-0-bootstrap-closeout-done.md`
- **cj-318 handoff §2 (Track A 4 Deploy-Blocking Actions 원본)** → `memory/handoff-2026-09-10-cj-318-operator-immediate-execution-entry-done.md`
- **cj-319 handoff §6 (F4 정정 + 신규 CORS_ORIGINS + NEXT_PUBLIC_API_URL 선행 조건)** → `memory/handoff-2026-09-10-cj-319-track-a0-deploy-blocking-wire-done.md`
- **cj-305b Resend swap 결정 wire (cj-style 256+257th)** → `memory/handoff-2026-09-08-cj-305b-resend-migration-done.md`
- **cj-307 aal1 minimum fix 결정 wire** → `memory/handoff-2026-09-08-cj-307-auth-callback-fix-done.md`
- **cj-308 Pilot W1 D-5 critical path entry 결정 wire** → `memory/handoff-2026-09-09-cj-308-pilot-w1-d5-critical-path-entry-done.md`

---

## §11 cj-style discipline 5 files atomic (N+10 신규 작성)

본 sprint 의 **5 files atomic** (cj-style discipline 표준):

| # | File | 변경 종류 | 비고 |
|---|---|---|---|
| 1 | `memory/handoff-2026-09-14-cj-style-n-10-track-a-1-a-4-detailed-prep-done.md` | **NEW** | 본 파일 (11-section §1~§11) |
| 2 | `_bmad-output/implementation-artifacts/commit-msg-cj-style-n-10.txt` | **NEW** | commit message with Co-Authored-By |
| 3 | `_bmad-output/implementation-artifacts/sprint-status.yaml` | **MODIFIED** | v4.125 → **v4.126 EXTENSION** + A772 신규 결정 wire + last_updated_note_v4_126 |
| 4 | `memory/MEMORY.md` | **MODIFIED** | cj-style N+10 hook EXTENSION + 92/92 cumulative 결정 wire + §9 결정 보류 업데이트 |
| 5 | `_bmad-output/implementation-artifacts/cj-style-n-10-summary.md` | **NEW** | atomic single sprint summary (cj-style N+9 의 close-out meta 패턴 mirror) |

**§11 의 §1 verbatim mirror**: 본 handoff 는 docs-only sprint (no source change) 이므로, **5 files 모두 문서/메타 파일**. verify gate:
- PROD source 변경 0건 ✅
- Test 변경 0건 ✅
- alembic 변경 0건 ✅
- PRD 변경 0건 ✅
- Capability matrix source 변경 0건 (v1.54 EXTENSION preserved) ✅
- Migration source 변경 0건 ✅
- 37 pins unchanged ✅
- 14 job matrix unchanged ✅
- AD-14 stack pin EXTENSION preserved ✅
- A19 cohesion 9 surface EXTENSION PASS preserved ✅
- 3중 게이트 FINAL CLEAN 보존 ✅

---

**TRACK A-1~A-4 운영자 실행 prep 확장 DONE**

**운전자 액션 가이드 (D-Day 2026-09-14 KST)**:
1. **§2 Pre-flight verify 5 항목** (~3-5분) — 통과 후에만 §3 진입
2. **§3 Track A-1~A-4 + 신규 2건** (~37-52분) — N+3 verbatim mirror, §3 A-4 step 4 시 §4 degraded verify gate 적용
3. **§5 Evidence capture** — §3 A-3 step 7 GV-3 + §3 A-4 step 8 GV-5
4. **§6 Emergency rollback** — §3 진행 중 실패 시 즉시 회복
5. **§7 Post-Track-A 후속** — P-1 + P-2 + P-3 (~30분, Track A 완료 후 즉시)

**Next**: §7 P-1+P-2+P-3 (~30분) → cj-style N+11+ (Sprint 1 actual run)