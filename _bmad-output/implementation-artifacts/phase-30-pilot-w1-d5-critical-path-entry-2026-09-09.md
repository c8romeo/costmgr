---
title: "cj-308 Pilot W1 D-5 Critical Path 결정 wire — entry DONE (cj-style 263번째)"
type: sprint-entry
date: 2026-09-09
sprint_key: phase-30-pilot-w1-d5-critical-path
status: ready-for-dev
cj_style_entry_point: 263
baseline_commit: a1cb7ad
territory: Phase 30 Pilot W1 D-5 Critical Path
sprint_type: entry (docs-only atomic)
CR: 11-3 honest-DEFER 263번째
---

# cj-308 Pilot W1 D-5 Critical Path 결정 wire — entry DONE (cj-style 263번째)

**일자**: 2026-09-09 (KST, **D-5 = D-day 2026-09-14 까지 5일**)
**territory**: Phase 30 Pilot W1 D-5 Critical Path
**sprint type**: entry (docs-only atomic single sprint)
**CR 11-3 honest-DEFER 263번째**

---

## §1 sprint scope — 의도 + 진입 결정 wire

### 의도 분석

cj-305b Resend migration wire (`53b8bbf`) + cj-305b retroactive correction (`c69dea5`) + cj-307 auth-callback aal1 minimum fix (`a1cb7ad`) 까지 결정 wire 완료. **현재 보류 결정 4건** (memory/MEMORY.md "Active sprint state" verbatim):

- **(a) RECOMMENDED next**: Resend + Supabase signup 즉시 시작 (D-5 today, ~2-3h, code 변경 없음, operator 액션)
- (b) Pilot candidate list (B-1) 작성 (D-2 2026-09-12 KST 까지 발송 필수)
- (c) cj-303 carryover 4건 fix
- (d) PRD v2 EXTENSION / Epic 29+ spec impl

### 진입 결정 wire

> **옵션 (a) Resend + Supabase signup 즉시 시작 결정 wire 진입** — D-day critical path 의 **first unblock step** 이고, (b)(c)(d) 모두 (a) 완료 후 진입 가능.

**rationale 5종**:
1. **D-day critical path 1순위**: 5일 남은 countdown 에서 가장 critical 한 unblock = 신규 사용자 signup 가능 상태. (a) 없이는 (b) 발송해도 candidate 가 login 불가.
2. **cj-307 + cj-305b 직결**: auth-callback aal1 fix + Resend migration 의 **검증 단계**가 곧 (a) — wire 만 했지 live verify 안 함.
3. **operator 액션 위주 (low risk)**: code 변경 0건. Web `.env.local` + Railway API env + Supabase Auth dashboard 3-step 으로 완결.
4. **(b)(c)(d) blocker 해소**: (b) 발송은 candidate 가 signup 가능해야 의미 있고, (c)(d) 는 post-W1 가능.
5. **cj-style discipline 보존**: cj-307 직후 자연스러운 cj-308 entry. 263번째 cj-style 연속 정직 회복 atomic single sprint.

## §2 결정 보류 옵션 4종 비교

| 옵션 | territory | critical path? | effort | D-day 의존 | 우선순위 |
|---|---|---|---|---|---|
| **(a) Resend + Supabase signup** | Operator config + live verify | ✅ 1순위 | ~2-3h (operator) | 즉시 | **★★★ P0** |
| (b) Pilot candidate list (B-1) 작성 | Outreach prep | 🟡 2순위 | ~1-2h | D-2 발송 | ★★ P1 |
| (c) cj-303 carryover 4건 fix | Carryover honestly DEFER | ❌ non-critical | ~3-4h | post-W1 | ★ P3 |
| (d) PRD v2 EXTENSION / Epic 29+ spec | New territory | ❌ non-critical | ~6-8h | post-W1 | ★ P3 |

## §3 Operator Action Checklist (운전자 실행)

### Step 1: RESEND_API_KEY 캡처 (~10min)
- [ ] Resend dashboard (https://resend.com/api-keys) 로그인
- [ ] Production API key 생성 (cj-305b 에서 명시한 `re_xxx...` 형식)
- [ ] Web `.env.local` EXTENSION: `RESEND_API_KEY=re_xxx...`
- [ ] Railway API env EXTENSION: `RESEND_API_KEY=re_xxx...` (production + preview)

### Step 2: SUPABASE_JWT_SECRET 캡처 (~5min)
- [ ] Supabase project dashboard → Settings → API → JWT Secret
- [ ] Railway API env EXTENSION: `SUPABASE_JWT_SECRET=eyJ...` (production only)

### Step 3: Supabase Auth dashboard live verify (~15min)
- [ ] Signup enable 확인: Authentication → Providers → Email (Enabled ✅)
- [ ] Confirm email OFF (cj-307 D-6 완료 보존)
- [ ] URL Configuration:
  - [ ] Site URL: `https://costmgr-web.vercel.app` (또는 운영 도메인)
  - [ ] Redirect URLs: `/auth/callback`, `/**` (wildcard)
- [ ] MFA settings: TOTP enabled (cj-307 aal1 fix 검증용)

### Step 4: Live signup smoke test (~30min)
- [ ] Pilot candidate 1명 test invite 발송 (self 또는 internal)
- [ ] Magic-link 수신 → click → `/auth/callback` → aal1 → dashboard 진입 검증
- [ ] MFA listFactors() 호출 결과 verified=[] → /auth/2fa skip 검증 (cj-307 fix)
- [ ] 첫 invoice/budget 생성 → audit log INSERT 검증
- [ ] Resend API 호출 결과 200 (transactional email 발송 검증)

### Step 5: Handoff 검증 (~10min)
- [ ] 4 critical gaps (cj-304) + Resend migration (cj-305b) + auth-callback aal1 (cj-307) + cj-308 live verify **모두 DONE** ✅
- [ ] D-4 (2026-09-10) 부터 (b) Pilot candidate list 작성 시작 가능
- [ ] D-2 (2026-09-12) 까지 발송 → D-1 응답 확인 → D-0 launch

## §4 영향 범위 + Risk Profile

**code 변경 0건** — operator env/dashboard 액션 only.

**risk profile**: **LOW** (이론적으로 서비스 down 가능성 0%, 단 dashboard 설정 실수 시 signup 차단)

**rollback**: env var 미설정 시 → cj-305b + cj-307 wire 그대로 유효. Supabase Auth dashboard 변경 → revert 즉시 가능.

**검증**:
- 단위 테스트: cj-305b (Resend) + cj-307 (auth-callback aal1) 기존 test 그대로 ✅
- 통합 테스트: live signup smoke test (Step 4)
- E2E: pilot candidate 1명 full flow

## §5 carryover 보존 (cj-307 + cj-305b + cj-304 + cj-303)

- **cj-307 carryover 보존**: 32 test failures + 22 errors (Phase 5/8/10/16/26) + 3 collection errors + FastAPI @app.on_event deprecation → post-W1 honestly DEFER
- **cj-305b Resend migration**: 9 files = 4 MODIFIED source + 1 MODIFIED docs + 2 NEW meta + 2 MODIFIED meta source+docs atomic, headline 정직 회복 (commit `c69dea5`) 보존
- **cj-304 4 critical gaps**: ① POSTMARK_SERVER_TOKEN ② APScheduler cron TZ ③ Pilot tenant provisioning ④ Production seed → 모두 DONE 진입 보존
- **cj-303 carryover 4건**: post-W1 honestly DEFER 보존
- **PRE-EXISTING honestly DEFER 6건**: web-e2e Playwright + test-suite-measure 잔여 + web-test + lint-conventions + Sentry + custom DNS → post-W1 honestly DEFER 보존

## §6 결정 보류 (post-cj-308)

**즉시 wire (cj-309) 후보** (운전자 결정 보류):
- (a-1) cj-309 Resend + Supabase signup live verify wire — Step 1~4 완료 후 결과 wire
- (a-2) cj-309b Pilot candidate list (B-1) 작성 wire — D-2 2026-09-12 발송 직결
- (b) carryover fix sprint — post-W1 honestly DEFER 보류 유지
- (c) PRD v2 EXTENSION / Epic 29+ spec — post-W1 honestly DEFER 보류 유지

## §7 CR 11-3 honest-DEFER 263번째

- **cj-307 의 "Pilot W1 blocker 해결" headline 의 한계 명시**: code fix 만 했지 live verify 안 함. cj-308 에서 live verify 결정 wire 진입.
- **cj-305b 의 "Resend migration wire CLOSED ✅ HONEST" headline 의 한계 명시**: email delivery layer swap 만, auth flow live verify 안 함. cj-308 에서 통합 verify.
- **MEMORY.md "Active sprint state" 의 "옵션 (a, RECOMMENDED next)" 의 결정 wire 진입**: cj-308 = option (a) 의 docs-only atomic entry.

## §8 Cross-references

- cj-307 auth-callback aal1 minimum fix (`a1cb7ad`) — 1 file, D-6
- cj-305b Resend migration wire (`53b8bbf`) — 9 files, D-6
- cj-305b retroactive correction (`c69dea5`) — file count 정직 회복, D-6
- cj-305 production deploy day-1 wire (`b732153`) — 4-service minimal viable runbook, D-6
- cj-304 prod deploy prep wire (`1fdb67d`) — 4 critical gaps fix, D-7
- cj-304 prod deploy prep close-out retro (`e7fb753`) — D-7
- cj-303 uvicorn boot fix wire (`537d17d`) — AD-14 stack pin EXTENSION, D-7
- cj-303 uvicorn boot fix close-out retro (`4fcf61e`) — D-7
- D-6 operator config 종합 완료 handoff (`handoff-2026-09-08-operator-config-done.md`) — D-6
- Epic 30+ Reporting & Export MVP chain (cj-282 ~ cj-296) ✅ ALL CLOSED
- Pilot launch 결정 wire (cj-297) — PRD OQ-3 파일럿 게이트 정식 OPEN, D-3
- Phase 30 Pilot W1 close-out retro (cj-298) — Epic 30+ 16 sprints CLOSED ✅ HONEST

## §9 결정 wire 일자 + Next

**결정 wire 일자**: 2026-09-09 (KST, D-5)

**next (cj-309)**: 옵션 (a-1) live verify wire OR 옵션 (a-2) Pilot candidate list 작성 — 운전자 결정 보류.
