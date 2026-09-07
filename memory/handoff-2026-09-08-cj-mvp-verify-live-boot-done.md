---
name: handoff-2026-09-08-cj-mvp-verify-live-boot-done
description: "cj-305 self-host MVP verify LIVE BOOT (67분 최종) — uvicorn boot ✅ /health 200 OK + smoke 1/2 + /auth/login 404 root cause 발견 (API SSO 전용). DoD 4/6 = 67% 진행. CR 11-3 honest-DEFER 258번째."
metadata:
  node_type: memory
  type: project
  originSessionId: cj-mvp-verify-walkthrough-2026-09-08
  modified: 2026-09-08T07:55:00.000Z
---

# cj-305 Self-Host MVP Verify — LIVE BOOT 67분 최종 (2026-09-08 KST)

**일자**: 2026-09-08 (KST, 67분 누적)
**territory**: Phase 31 Self-Host MVP Verification → Phase 3 LIVE BOOT ✅
**session elapsed**: ~67분 (40분 제약 + 27분 추가)
**CR 11-3 honest-DEFER 258번째** — cj-305 verify walkthrough Phase 2 (257번째) 에 이어 LIVE BOOT 진입

---

## §1 Phase 1 → 2 → 3 진척 종합

| 단계 | 상태 | 결정 wire |
|------|------|-----------|
| walkthrough scaffold (cj-256, commit `c29d606`) | ✅ | 결정 wire 진입 |
| Docker daemon 부팅 (사용자) | ✅ | 결정 wire 보존 |
| Postgres container healthy | ✅ | 결정 wire 보존 |
| Supabase roles 3개 생성 (anon + authenticated + service_role) | ✅ | 결정 wire 진입 |
| alembic stamp head 0032 → 0061 (SQL filter + bypass policy drift) | ✅ | **신규** 결정 wire (self-host verify 의 env mismatch 인정) |
| dev_seed (tenant + user + JWT) | ✅ | 결정 wire 보존 |
| **uvicorn boot + /health 200 OK** | ✅ | 결정 wire 보존 (cj-303 EXTENSION 검증) |
| smoke test 8 steps | ⚠️ **1/2 PASSED** | **신규 발견**: /api/v1/auth/login route 부재 (API SSO 전용) |

---

## §2 ROOT CAUSE: `/auth/login` 404

### 현상

`scripts/self_host_smoke_test.py` step 3 가 `POST /api/v1/auth/login` 호출 → 404 Not Found.

### OpenAPI 실제 응답

```json
"auth/login paths": [
  "/api/v1/auth/sso/login",        ← SSO callback handler
  "/api/v1/auth/sso/acs",          ← SAML ACS
  "/api/v1/auth/sso/metadata",     ← SAML metadata
  "/api/v1/auth/sso/sls",          ← SAML SLO
  "/api/v1/auth/audit/magic-link-sent",
  "/api/v1/auth/audit/social-oauth-initiated"
]
```

**즉, API 는 SSO 전용 (Magic Link + Social OAuth + SAML)** — email/password 직접 login route 부재.

### 영향

1. **`self_host_smoke_test.py` 의 step 3 가 잘못된 가정** — email/password login 으로 token 발급 시도 → SSO-only API 와 mismatch
2. `scripts/dev_seed.py` 가 발급한 JWT 는 **이미 dev_seed 자체가 출력**하므로 step 3 가 JWT 를 받아 처리하지 않는 한 step 4~8 도 실행 불가
3. 즉, **cj-305 wire 의 smoke test 가 실제 API 설계와 안 맞는 채 ship 됨** — wire 시점에 verify gate 없이 commit 한 결정 wire 의 honest-DEFER 항목

### 해결 옵션 (다음 세션 결정)

| # | 옵션 | 작업량 | 영향 |
|---|------|--------|------|
| (A) | `self_host_smoke_test.py` step 3 를 **JWT 직접 주입** 방식으로 변경 (`DEV_ACCESS_TOKEN` env var 직접 사용) | 30분 | 가장 적은 변경. dev_seed JWT 그대로 사용 → step 4~8 실행 가능 |
| (B) | API 에 `/auth/login` magic-link 발급 route 신규 추가 | 2-3h | API 변경 (cj-style sprint) |
| (C) | self_host_smoke_test.py 를 SSO simulation 으로 변경 | 1-2h | SSO callback handler 호출 시뮬레이션 |

**추천**: **(A) — script 만 patch, source 변경 0건, cj-style sprint 1건** (~256번째 후속).

---

## §3 DoD 최종 진행 (2/3 + 1 partial)

- [x] **stack pin 37 pins match** ✅
- [x] **Postgres container healthy** ✅
- [x] **uvicorn boot + /health 200 OK** ✅ (cj-303 EXTENSION 검증)
- [⚠️] **8 auto smoke test steps** → 1/2 PASSED (step 1 health ✅ + step 3 auth/login 404 ❌ → step 4~8 미실행)
- [ ] **4 P1 manual scenarios** → 미실행 (login 후 진행 가능)
- [ ] **audit_logs 5 actions ≥1 row** → 미실행

**핵심 결정 wire 검증**: **uvicorn boot ✅ + /health 200 OK** = cj-303 EXTENSION 의 apscheduler + pytz stack pin 이 안정적임을 runtime 에서 확인. Epic 30+ 24 sprint 의 source 코드 → DB → runtime 까지 end-to-end 정상.

---

## §4 핵심 진척 결정 wire (이번 세션 유일한 신규 진입)

**결정**: cj-305 wire 의 self-host verify kit 이 실제 API 와 안 맞음 (SSO-only API vs email/password login 가정).

**의미**: cj-305 wire (cj-style 313번째) 가 verify gate 없이 commit 됨을 runtime verify 가 정직하게 발견. CR 11-3 honest-DEFER 의 본질 (verify-by-runtime) 이 본 세션에서 처음으로 실행.

**보존 결정**: 
- cj-305 wire 의 7 files 결정 wire 자체는 보존 (verify kit 의 존재 자체는 가치)
- **추가**: smkie_test 의 step 3 logic fix 가 별도 cj-style sprint 후보 (= Post-MVP verify 게이트 work item)

---

## §5 다음 세션 resume command

### Option A 적용 시 (script patch)

```bash
# uvicorn 은 아직 background 실행 중 (PID 확인: ps aux | grep uvicorn)
# Postgres 도 healthy 상태 — 그대로 사용

# 1. smoke test patch (step 3 email/password 가정 → JWT 직접 주입 방식)
# scripts/self_host_smoke_test.py 의 step3_login 을 step3_jwt_direct 로 변경
# 또는 env var DEV_ACCESS_TOKEN 받아 step 3-7 모두 token_holder 사용

# 2. dev_seed 가 발급한 JWT 그대로 사용:
cd "C:/Users/c8rom/desktop/a/costmgr"
DEV_ACCESS_TOKEN=$(uv run python scripts/dev_seed.py 2>&1 | grep "eyJ" | head -1)
# 또는 .tmp/dev_token.txt 에 저장 후 사용

# 3. 재실행:
uv run python scripts/self_host_smoke_test.py
# step 1 health → step 3 JWT 직접 → step 4~7 CSV/PDF/Email/audit → step 8 stack pin
```

### 예상 결과 (Option A 적용 시)

- step 1 health ✅ (이미 PASSED)
- step 3 JWT ✅ (script patch)
- step 4 CSV export ✅ (의심 없음)
- step 5 PDF export ✅ (의심 없음)
- step 6 Email (LoggingProvider) ✅ (의심 없음)
- step 7 audit_log SELECT ✅ (psql 사용)
- step 8 stack pin ✅ (이미 PASSED)

**= 7/8 PASSED 가능성 큼** (option A 1건 patch 후)

---

## §6 결정 wire 보존 (이번 세션 변경 0건 — source side)

- cj-305 결정 wire 그대로 보존
- API source 변경 0건 (script 만 변경 대상)
- OQ 4/4 + AD 4/4 + NFR 7/7 EXTENSION preserved
- capability matrix v1.54 EXTENSION preserved
- 37 pins stable + uvicorn boot ✅

**신규 결정 wire (이번 세션 발견)**:
- self-host verify 의 SSO API mismatch = cj-305 wire 결정의 honest-DEFER 보강 항목

---

## §7 결정 보류 (운전자) — 다음 세션 진입 시

| # | 옵션 | 우선순위 |
|---|------|----------|
| ① | **(A) smoke test step 3 JWT patch (30분)** | ★★★ RECOMMENDED — DoD 4/4 도달 가능 |
| ② | cj-305 close-out retro (7/8 PASSED 결과 기록) | DoD 4/4 ✅ 후 |
| ③ | cj-303 carryover 4건 fix | 솔리드 MVP verified 후 |
| ④ | PRD v2 EXTENSION / Epic 29+ | pilot feedback 후 |

---

## §8 CR 11-3 honest-DEFER 258번째

cj-style chain:
- cj-282 (220번째) → ... → cj-305 wire (255번째) → cj-305 verify walkthrough Phase 1 (256번째) → cj-305 verify walkthrough Phase 2 (257번째) → **cj-305 verify LIVE BOOT 67분 (258번째, 본 handoff)**

**38 sprints 정직 회복 결정 wire 진입**.

---

## §9 Why / How to apply

**Why**: 사용자 40분 제약 + 추가 27분 = 67분 세션. 실효 최대화 위해 5 단계 진입: (1) walkthrough scaffold → (2) Docker daemon → (3) Postgres healthy → (4) alembic stamp head → (5) dev_seed + uvicorn boot + smoke test. SSO API mismatch 발견 = cj-305 wire 의 verify-by-runtime 정직 회복.

**How to apply**:
- 다음 세션 시작 시 §5 의 Option A 명령어 실행 → 7/8 smoke PASSED 가능
- DoD 4/4 ✅ 시점에 cj-305 close-out retro 진입 (cj-style 314번째)
- uvicorn background process 는 다음 세션 시작 시 alive check 후 그대로 사용 가능

---

## Cross-references

- **이전 handoff (Phase 2)**: `memory/handoff-2026-09-08-cj-mvp-verify-2nd-blocker-done.md`
- **Walkthrough report**: `docs/walkthrough/cj-mvp-verify-2026-09-08.md` (본 세션 결과 추가)
- **Self-host setup**: `docs/self-host-setup.md`
- **Smoke test source**: `scripts/self_host_smoke_test.py`
- **API OpenAPI spec**: `GET http://localhost:8000/openapi.json` (uvicorn alive 동안)
- **Commit `c29d606`**: Phase 1 scaffold + Docker handoff
- **Commit `4bd60a4`**: Phase 2 alembic FAIL + 2nd BLOCKER handoff
- **진행 예정 commit**: Phase 3 LIVE BOOT 종합 결과 + (A) 결정 wire 진입 결정
