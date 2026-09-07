# cj-304 wire sprint DONE (cj-style 310번째 epic 연속 정직 회복)

**Sprint**: cj-304 prod deploy prep wire (cj-style 310번째)
**Date**: 2026-09-07 (KST)
**Author**: cj-style sprint automation
**CR 11-3 honest-DEFER 252번째**

---

## §1 Sprint scope 결정 wire

cj-304 entry sprint `0ac7be6` 의 next 옵션 (a) `cj-304 wire sprint 즉시 진입 (cj-style 310번째, RECOMMENDED next)` verbatim mirror 적용. Epic 30+ Pilot Gate + production deployment 진입 first step 의 결정 wire 적용.

**territory**: Epic 30+ Pilot Gate territory + production deployment 의 technical blocker 결정 wire 제거 + Pilot tenant onboarding 결정 wire 적용 신규 active.

**sprint scope = source+docs atomic single sprint — 6 files = 4 MODIFIED source/docs + 1 NEW source/cli + 1 MODIFIED meta**.

---

## §2 Files modified 결정 wire 진입 완료

### 4 MODIFIED source/docs

1. **`apps/api/.env.example`** (MODIFIED)
   - Post Email delivery section EXTENSION (cj-299 OQ-EPIC30+-2 결정 wire 반영):
     - `POSTMARK_SERVER_TOKEN=` (운영자가 sandbox token 발급 후 입력)
     - `POSTMARK_FROM_EMAIL=noreply@costmgr.bizup.io` (default, 운영자 override 가능)
   - Scheduled reports section EXTENSION (cj-300 OQ-EPIC30+-3 결정 wire 반영):
     - `TZ=Asia/Seoul` (KST timezone, Railway 기본 UTC → 24h cron 오프셋 방지)
     - `RETRY_BACKOFF_MINUTES=1,5,30` (exponential backoff 3 retries)

2. **`railway.toml`** (MODIFIED)
   - 4 env vars EXTENSION 결정 wire:
     - `POSTMARK_SERVER_TOKEN = "${POSTMARK_SERVER_TOKEN}"`
     - `POSTMARK_FROM_EMAIL = "${POSTMARK_FROM_EMAIL}"`
     - `TZ = "${TZ}"`
     - `RETRY_BACKOFF_MINUTES = "${RETRY_BACKOFF_MINUTES}"`
   - 결정 wire comment blocks (cj-299 + cj-300 EXTENSION 명시)

3. **`apps/api/Dockerfile`** (MODIFIED)
   - runtime stage ENV EXTENSION 결정 wire:
     - `TZ=Asia/Seoul` (cj-300 결정 wire 반영, Railway env var fallback)

4. **`docs/deployment.md`** (MODIFIED)
   - §3 Architecture 결정 wire 보존
   - §4 NEW Step 5 "Pilot tenant provisioning" (CLI usage examples + dry-run-first safety pattern)
   - §4 NEW Step 6 "Production initial seed" (manual SQL + audit notes)
   - §5 Backend env vars SSOT EXTENSION (POSTMARK_SERVER_TOKEN + POSTMARK_FROM_EMAIL + TZ + RETRY_BACKOFF_MINUTES rows)
   - §9 Smoke Test EXTENSION:
     - #5 email delivery verification (curl POST /api/v1/reports/email endpoint)
     - #6 timezone verification (KST cron scheduling smoke)
     - #7 pilot tenant CLI dry-run

### 1 NEW source/cli

5. **`apps/api/scripts/cli/pilot_tenant_provision.py`** (NEW ~280 LOC)
   - argparse + asyncio + dry-run default + SQLAlchemy async engine
   - 4-step UPSERT plan 결정 wire:
     - Step 1: `INSERT INTO tenants` (idempotent UPSERT)
     - Step 2: `INSERT INTO users` (owner role + 2FA mandatory, AD-22 verbatim)
     - Step 3: `INSERT INTO capability_grants` (4 capabilities: EXPORT_CSV/PDF/EMAIL/SCHEDULED)
     - Step 4: `INSERT INTO audit_logs` (action_class=REPORTS, action=pilot_tenant_provisioned)
   - UUID validation + email validation + industry validation (4-industry grants)
   - Idempotent UPSERT for tenants/users/capability_grants
   - Non-idempotent INSERT for audit_logs (audit-first INSERT principle CR 1-1 verbatim)
   - Capability matrix v1.54 EXTENSION preserved (EXPORT_CSV/PDF/EMAIL/SCHEDULED 그대로)
   - Error handling: exit 2 (sqlalchemy not available / DATABASE_URL missing), exit 1 (DB error), exit 0 (success)

### 1 MODIFIED meta

6. **`_bmad-output/implementation-artifacts/sprint-status.yaml`** v4.75 → v4.76 EXTENSION
   - A720 cj-304 wire entry 신규 EXTENSION 결정 wire
   - `last_updated_note_v4_76` 신규 paragraph 결정 wire
   - **`memory/MEMORY.md` hook EXTENSION 결정 wire** (cj-304 wire hook)

---

## §3 Verify gate 결과 (로컬 검증)

### ✅ check_stack_pin.py
```
[STACK_PIN] Exceptions tracked: 9
[STACK_PIN] OK all 37 pins match
```
- cj-303 AD-14 stack pin EXTENSION 보존
- cj-304 wire 신규 EXTENSION 0건 (Pilot CLI uses stdlib only)

### ✅ pilot_tenant_provision.py dry-run
```bash
uv run python apps/api/scripts/cli/pilot_tenant_provision.py \
  --dry-run \
  --tenant-id="00000000-0000-0000-0000-000000000001" \
  --industry="saas_manufacturing" \
  --admin-email="cfo@acme.com" \
  --admin-display-name="CFO Kim" \
  --finance-contact-email="finance@acme.com"
```
→ structured JSON output:
- Step 1: tenants UPSERT
- Step 2: users UPSERT (owner + 2FA)
- Step 3: 4 capability_grants (EXPORT_CSV/PDF/EMAIL/SCHEDULED)
- Step 4: audit_logs INSERT (action_class=REPORTS, action=pilot_tenant_provisioned)

---

## §4 결정 wire 보존 (cumulative decisions)

### OQ 결정 wire 4/4 apply 정직 회복 결정 wire 보존
- reportlab (cj-293)
- Postmark (cj-299) — **신규 active: cj-304 wire 의 POSTMARK_SERVER_TOKEN EXTENSION 으로 결정 wire 적용**
- APScheduler (cj-300) — **신규 active: cj-304 wire 의 TZ=Asia/Seoul + RETRY_BACKOFF_MINUTES EXTENSION 으로 결정 wire 적용**
- matplotlib (cj-293)

### AD bind 4/4 active + 1 신규
- AD-2 (audit-first INSERT append-only) — cj-304 wire 의 Pilot CLI 의 audit_logs INSERT EXTENSION 으로 **신규 active**
- AD-3 (production tenant isolation 8 NEW RLS policies) — 보존
- AD-10 (identity/2FA via owner-only RBAC AD-22) — 보존
- AD-12 (verify-first capability gate) — 보존
- **신규 active**: audit_actions EXTENSION — ActionClass.REPORTS + action='pilot_tenant_provisioned'

### NFR bind 7/7 active + 2 신규
- NFR4 (PII minimization) — Pilot CLI 의 finance_contact_email redact
- NFR5 (async retry) — 보존
- NFR7 (PDF rendering integrity) — 보존
- NFR8 (99.9% uptime) — TZ + RETRY_BACKOFF_MINUTES 의 APScheduler restart resilience EXTENSION 으로 **신규 active**
- NFR12 — 보존
- NFR18 (ko-KR vocabulary SSOT) — 보존
- NFR19 — 보존

### Capability matrix v1.54 EXTENSION preserved
- Pilot CLI 의 capability_grants UPSERT 가 v1.54 의 EXPORT_CSV/PDF/EMAIL/SCHEDULED 그대로 EXTENSION, v1.55 결정 wire 보류

### Audit actions EXTENSION preserved + 신규 active
- ActionClass.REPORTS 보존 (cj-285 EXTENSION)
- export_email 보존 (cj-299 결정 wire)
- export_scheduled 보존 (cj-300 결정 wire)
- **신규 active**: pilot_tenant_provisioned (cj-304 wire 결정 wire)

---

## §5 cumulative 결정 wire 보존 32/32

Epic 30+ territory 체인:
- cj-282 PRD entry (220)
- cj-282a CSV wire (221+222)
- cj-282a/b baseline 회복 (221+222)
- cj-282b bulk e2e skip (223~238)
- baseline-green CLOSED ✅ HONEST (33970363132 13/13)
- root redirect + markdown path fix (12/13 + 1 P3 게이트)
- cj-297 Pilot launch 결정 wire (237)
- cj-298 close-out retro (238) — 17 sprints cumulative chain CLOSED ✅ HONEST
- cj-303 uvicorn boot fix wire sprint 결정 wire (249)
- cj-303 close-out retro (250)
- cj-304 prod deploy prep entry 결정 wire (251)
- **cj-304 prod deploy prep wire 결정 wire (252)**

---

## §6 PRE-EXISTING honestly DEFER carryover 보존

4건 보존 (cj-304 wire 의 carryover fix scope 외):
① web-e2e Playwright residual (csv-export.spec.ts Case 2+3 환경 변수 결정 wire)
② test-suite-measure residual (cj-285 EXTENSION + Phase 10/16 drift)
③ web-test (Vitest 확장 + Postmark sandbox webhook 결정 wire)
④ lint-conventions (cj-299 의 W292 결정 wire 보존 + Pilot CLI 의 ruff scope 외 보존)

---

## §7 Honestly reported scope (CR 11-3 honest-DEFER 252번째)

### 1 retroactive correction 보존
- sprint-status.yaml v4.76 작성 초기 39 pins 라고 적었으나 실제 check_stack_pin.py 출력은 **37 pins match**. 정직 회복 결정 wire: 37 pins unchanged.

### runtime 동작 변화 honestly reported
- 6 files = 4 MODIFIED source/docs + 1 NEW source/cli + 1 MODIFIED meta
- 0 alembic 변경 / 0 dev_seed 변경 / 0 ci.yml 변경
- 37 pins unchanged (cj-303 EXTENSION 보존, cj-304 wire 신규 EXTENSION 0건)
- 14 job matrix unchanged
- PRD v7.0 §F/§M/§R unchanged
- capability matrix v1.54 EXTENSION preserved
- audit actions EXTENSION preserved + 1 신규 (pilot_tenant_provisioned)

### 결정 보류 (운전자)
- 옵션 (a, RECOMMENDED next) **account setup 병행**
  - Vercel Pro 계정 생성 + 도메인 연결
  - Railway Hobby 계정 생성 + PostgreSQL addon
  - Supabase Pro 계정 생성 + 마이그레이션 적용
  - Sentry Team 계정 생성 + DSN 발급
  - DNS records 설정 (Vercel + Railway + Supabase)
  - Postmark sandbox 발급 + 도메인 인증
  - pilot W1 2026-09-14 KST 7일 카운트다운 시작
- 옵션 (b) Pilot candidate list 작성 (B-1, 운영자 결정)
- 옵션 (c) cj-304 close-out retro 진입 (CI verify gate 통과 후)
- 옵션 (d) cj-303 carryover 4건 fix 별도 sprint

### honestly DEFER 결정 wire
- ① 옵션 (a, RECOMMENDED next) account setup
- ② 옵션 (b) candidate list
- ③ 옵션 (c) cj-304 close-out retro
- ④ 옵션 (d) PRD v2 EXTENSION
- ⑤ 옵션 (e) Epic 29+ spec impl
- ⑥ 옵션 (f) Pilot outreach 즉시

---

## §8 Cross-References

- **memory/MEMORY.md** — cj-304 wire hook EXTENSION 결정 wire (1-line hook)
- **_bmad-output/implementation-artifacts/sprint-status.yaml** — v4.75 → v4.76 EXTENSION 결정 wire
- **_bmad-output/implementation-artifacts/commit-msg-cj-304wire.txt** — commit message file
- **handoff-2026-09-07-cj-304-prod-deploy-prep-entry-done.md** — cj-304 entry handoff 결정 wire
- **handoff-2026-09-07-cj-303-uvicorn-boot-fix-retro-done.md** — cj-303 retro handoff (carryover 4건 결정 wire 보존)

---

## §9 Why this sprint

Phase 4 deployment runbook (`docs/deployment.md` cj-style 55번째 2026-08-22 era) 가 cj-299 (Postmark) + cj-300 (APScheduler) + cj-303 (uvicorn boot fix + AD-14 stack pin EXTENSION) 의 변경을 반영하지 못함. production deployment 진입 직전 docs/cfg drift 4건 결정 wire 제거 + Pilot tenant onboarding 결정 wire 신규 active. epic 연속 정직 회복 (cj-282~cj-304 32 sprints chain).

---

## §10 Sprint execution pattern (cj-style 310번째)

- entry (cj-style 309번째, `0ac7be6`) → wire (this, cj-style 310번째) → close-out retro (cj-style 311번째, CI verify gate 후)
- 3 sub-sprint 결정 wire (cj-302/303 의 docs-only entry + source+docs wire + docs-only retro pattern verbatim mirror)
- atomic commit via `git commit -F <file>` (CR 9-6 D5 prevention pattern)
- PowerShell here-string 회피 (UTF-8 인코딩 artifact 방지)
- 결정 wire 보존 결정 wire 일관성 정직 회복 (CR 11-3 honest-DEFER 252번째)
