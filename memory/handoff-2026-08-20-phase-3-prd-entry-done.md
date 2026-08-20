---
name: handoff-2026-08-20-phase-3-prd-entry-done
description: Phase 3 PRD entry DONE (cj-style Phase 3 1번째 진입점 = cj-style 49번째 epic 연속 정직 회복 atomic docs-only wire). master PRD v2.5→v3.0 + §F15 Auth Foundation + capability matrix v1.24 + AD-26 + A65+A66+A67+A68+A69 결정 wire 진입.
metadata:
  type: project
  originSessionId: fe01bd10-d5e7-46a8-83b8-29a6226222f3
  modified: 2026-08-20T14:30:00.000Z
---

# Phase 3 PRD Entry DONE — Auth Foundation (handoff-2026-08-20)

## Phase 3 = 로그인/회원가입 UI + auth middleware (Epic 1 완성 territory 진입 결정 wire)

cj-style Phase 2 close-out atomic wire (`3020823`) 직후의 다음 territory 진입 결정.
사용자 directive: "cj-style 1+2+3 진입점 (Recommended)" for Phase 3 entry.

## Phase 3 결정 wire Summary

| 결정 | 내용 |
|------|------|
| **A65** | Phase 3 PRD entry 진입 결정 (Epic 1 carry-over 정직 회복, D-1-1-DEFER-1/2/3 honestly preserved) |
| **A66** | AD-26 Auth Foundation 신규 결정 (Supabase SSR + sb-access-token cookie session + next-intl middleware EXTENSION) |
| **A67** | Capability matrix v1.23 → v1.24 EXTENSION 5 NEW rows (LOGIN + SIGNUP + AUTH_MIDDLEWARE + FORGOT_PASSWORD + LOGOUT) |
| **A68** | Epic 1 carry-over DEFER 1~N honestly preserved (D-1-1-DEFER-1 Magic link + D-1-1-DEFER-2 Social login OAuth + D-1-1-DEFER-3 SSO enterprise SAML) |
| **A69** | Phase 3 wire scope T1~T8 결정 (T1 Supabase SSR client + T2 login page + T3 signup page + T4 auth middleware EXTENSION + T5 logout + T6 forgot-password + T7 capability v1.24 EXTENSION + T8 tests + 3중 게이트 FINAL CLEAN atomic commit) + Epic 1 partial scaffold 보존 결정 |

## Phase 3 PRD Entry wire scope (master PRD v3.0 atomic edit, 1 file)

### 1. master PRD v2.5 → v3.0 atomic edit (1 file)

- **front matter** v2.5 → v3.0 + changelog v3.0 entry 신규 (Phase 3 PRD entry 진입 결정 verbatim bind)
- **§F15 신규** (F15.1 login UI + Supabase SSR auth client / F15.2 signup UI + tenant creation flow / F15.3 auth middleware EXTENSION / F15.4 logout / F15.5 forgot-password / F15.6 tests + wire scope T1~T8 결정)
- **§8.1 M0-(d) login + M0-(e) signup + M0-(f) auth middleware** 3 NEW 인수 불릿
- **§15 로드맵 Phase 3 row** status 백로그 → in-progress (PRD entry DONE 진입 wire)
- **§부록 A A65+A66+A67+A68+A69** 신규 결정 표
- **AD-26 Auth Foundation** 신규 결정 (Supabase SSR + sb-access-token cookie session + next-intl middleware EXTENSION)
- **§8.1 M0-(d) ko-KR SSOT 메시지**: `LOGIN_INVALID_CREDENTIALS_KO` + `LOGIN_NETWORK_ERROR_KO` + `LOGIN_RATE_LIMITED_KO` + `SIGNUP_DUPLICATE_EMAIL_KO` + `SIGNUP_WEAK_PASSWORD_KO` + `SIGNUP_INVALID_EMAIL_KO` + `SIGNUP_PASSWORD_MISMATCH_KO` + `LOGOUT_FAILED_KO` + `LOGOUT_NETWORK_ERROR_KO` + `FORGOT_PASSWORD_EMAIL_SENT_KO` + `RESET_PASSWORD_INVALID_TOKEN_KO` + `RESET_PASSWORD_WEAK_PASSWORD_KO` (CR 12-5 D-14 envelope `{code, message_ko, details, trace_id}` 정합)

### 2. capability matrix v1.23 → v1.24 EXTENSION (1 file)

- **title** v1.23 → v1.24
- **v1.24 changelog entry 신규** (Phase 3 PRD entry)
- **5 NEW rows** added: `LOGIN` + `SIGNUP` + `AUTH_MIDDLEWARE` + `FORGOT_PASSWORD` + `LOGOUT` (모두 industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러, AI_INSIGHT 10-1 + LISTEN_NOTIFY 13-1 + LISTEN_NOTIFY_TENANT_FANOUT 14-1 + LISTEN_NOTIFY_MULTIPROCESS 14-1 wire pattern)
- **title test forward-lock** v1.21 → v1.24 (relaxed in `tests/integration/test_capability_matrix_v1_21_drift.py`)

### 3. Epic 1 partial scaffold 보존 결정 wire

- `apps/web/app/[locale]/(auth)/layout.tsx` minimal shell 보존 (Phase 3 wire 진입 시점에 design tokens EXTENSION 결정 wire 보존)
- `apps/web/app/[locale]/(auth)/onboarding/industry/page.tsx` 보존 (Phase 3 T3 signup wire 시점에 atomic redirect 보존)
- `apps/web/components/onboarding/IndustrySelector.tsx` + `IndustryCard.tsx` 보존 (Phase 3 wire 영향 0)
- `apps/web/middleware.ts` next-intl EXTENSION 결정 wire (Phase 3 T4 진입 시점에 EXTENSION)
- `apps/web/e2e/fixtures/supabase-test.ts` rls_db fixture 보존 (Phase 3 T1 wire 진입 시점에 F-30 honestly RESOLVE 결정)

## 변경 파일 (Atomic Wire)

### MODIFIED (3 files)
1. `_bmad-output/planning-artifacts/prd.md` — title v2.5 → v3.0 + changelog v3.0 entry + §F15 신규 + §8.1 M0-(d)·M0-(e)·M0-(f) 3 NEW 인수 불릿 + §15 로드맵 Phase 3 row + §부록 A A65~A69 신규 결정 표 + AD-26 신규 결정
2. `docs/capability-matrix.md` — title v1.23 → v1.24 + v1.24 changelog entry + 5 NEW rows added
3. `tests/integration/test_capability_matrix_v1_21_drift.py` — title test forward-lock ≥ v1.24 (relaxed)

### NEW (3 files)
1. `_bmad-output/implementation-artifacts/commit-msg-phase-3-prd-entry.txt` (commit message)
2. `memory/handoff-2026-08-20-phase-3-prd-entry-done.md` (this file)
3. MEMORY.md index entry 추가

### sprint-status 신규 entry
- `phase-3-prd-entry: done` (cj-style Phase 3 1번째 진입점 진입 결정 verbatim bind)

## Phase 3 진입 flow (cj-style 1~3번째 진입점 결정 보존)

| 진입점 | 진입 시점 | 결정 wire 보존 |
|--------|----------|----------------|
| **cj-style Phase 3 1번째 진입점** = Phase 3 PRD entry (cj-style 49번째) | ✅ DONE 2026-08-20 (master PRD v3.0 atomic edit) | 본 sprint |
| **cj-style Phase 3 2번째 진입점** = bmad-create-story spec (cj-style 50번째) | 진입 대기 | Phase 3 wire spec (T1~T8) 결정 wire + Epic 1 carry-over F-1/F-4/F-30 honestly RESOLVE 결정 wire 진입 |
| **cj-style Phase 3 3번째 진입점** = bmad-dev-story atomic wire (cj-style 51번째) | 진입 대기 | Phase 3 본체 wire T1~T8 atomic single sprint |

## CR Lessons Applied (보존)
- CR 11-3 honest-DEFER discipline (Phase 3 PRD entry 진입 시점에 D-1-1-DEFER-1/2/3 honestly preserved)
- A36 SDR 검증 4-step 자동 적용 (commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS)
- CR 12-5 D-GATE-01 + D-PARITY-01 inversion 적용 보존 (ko-KR SSOT 메시지 + envelope `{code, message_ko, details, trace_id}`)
- A19 cohesion pattern 9 surface EXTENSION PASS 결정 (auth surface NEW = T1~T6 SSR client + Server Components + Client Components + Middleware + Server Actions / Route Handlers)
- CR 0-2 RLS lesson (Auth Foundation 자체는 tenant 격리에 영향 없으나 Epic 12 2FA 게이트 정합 보존)
- CR 1-1 audit-first INSERT (tenant_created + user_logged_out + password_reset audit_logs 3-row)
- CR 9-6 commit message discipline (`git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention)

## 결정 wire 일자
2026-08-20

## Next
- **Phase 3 cj-style 2번째 진입점**: bmad-create-story spec 진입 (cj-style 50번째 epic 연속 정직 회복 진입 대기)
- **Phase 4**: 배포 config + Dockerfile 진입 결정
- **Phase 5**: 옵션 (a) master PRD v3 / (b) Epic 15 / (c) carry-over 진입 결정
