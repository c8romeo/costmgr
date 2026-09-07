---
name: handoff-2026-09-07-cj-304-prod-deploy-prep-entry-done
description: "cj-304 prod deploy prep entry (cj-style 309번째) — docs/deployment.md currency check + 4 critical gaps 정직 회복 (POSTMARK_SERVER_TOKEN + APScheduler cron/TZ + Pilot tenant provisioning + Production seed). CR 11-3 honest-DEFER 251번째."
metadata:
  node_type: memory
  type: project
  originSessionId: e85acf61-c75a-4985-990b-b5f6b80a7640
  modified: 2026-09-07T15:00:00.000Z
---

# cj-304 prod deploy prep — entry DONE (cj-style 309번째)

**일자**: 2026-09-07 (KST)
**territory**: Epic 30+ Pilot Gate + option (a) production deployment 진입 직전
**sprint type**: docs-only atomic entry (cj-style 251번째)

---

## §1 sprint scope

cj-303 close-out retro 종료 후 option (a) production deployment 진입. 첫 단계 = deployment artifacts currency verification + gap analysis.

## §2 currency check 결과

Phase 4 의 `docs/deployment.md` (cj-style 55번째, 2026-08-22 era) 가 cj-299 (Postmark) + cj-300 (APScheduler) + cj-303 (uvicorn boot fix + AD-14 stack pin EXTENSION) 의 변경을 반영하지 못함 → **5개 section 갱신 필요** + **4 critical gaps** 식별.

## §3 4 critical gaps

### Gap 1 — POSTMARK_SERVER_TOKEN missing ⚠️ CRITICAL
- 영향: cj-299 Postmark 결정 wire 무력화, production email 발송이 LoggingProvider fallback (stdout 로그만 출력)
- Fix: 3 files EXTENSION (env.example + railway.toml + deployment.md)

### Gap 2 — APScheduler cron env vars + TZ missing ⚠️ CRITICAL
- 영향: Railway 기본 UTC → cj-300 KST scheduled reports 가 24시간 오프셋
- Fix: 4 files EXTENSION (env.example + railway.toml + Dockerfile + deployment.md)

### Gap 3 — Pilot tenant provisioning strategy 부재 ⚠️ MEDIUM
- 영향: 5-10 SaaS 제조 스타트업 tenant onboarding CLI 부재
- Fix: NEW `apps/api/scripts/cli/pilot_tenant_provision.py` (~150 LOC interactive CLI)

### Gap 4 — Production seed plan 부재 ⚠️ LOW
- 영향: platform admin + capability matrix + default cron 초기화 부재
- Fix: `docs/deployment.md` §4 Step 6 NEW (운영자 수동 SQL 권장)

## §4 cj-304 wire scope (6-7 files)

| File | Type | Change |
|---|---|---|
| `apps/api/.env.example` | MODIFIED | EXTENSION 5 env vars |
| `railway.toml` | MODIFIED | EXTENSION 5 env vars + cj-303 comment |
| `apps/api/Dockerfile` | MODIFIED | runtime stage ENV TZ=Asia/Seoul |
| `docs/deployment.md` | MODIFIED | §3 + §4 + §5 + §9 EXTENSION |
| `apps/api/scripts/cli/pilot_tenant_provision.py` | NEW | ~150 LOC CLI |
| `sprint-status.yaml` | MODIFIED | v4.74 → v4.75 |
| `MEMORY.md` | MODIFIED | cj-304 wire hook 1-line |

## §5 결정 보류 (운전자)

| # | 옵션 | 결정자 |
|---|---|---|
| ① | **cj-304 wire sprint 즉시 진입** (cj-style 310번째, RECOMMENDED next) | 운전자 |
| ② | Vercel/Railway/Supabase/Sentry account setup 병행 | operator |
| ③ | Pilot candidate list 작성 (B-1) 병행 | operator |
| ④ | cj-303 carryover 4건 fix | 기술 결정 |

## §6 CR 11-3 honest-DEFER 251번째

```
cj-style chain: cj-282 (220번째) → ... → cj-303 close-out retro (250번째) → cj-304 prod deploy prep entry (251번째)
```

## Cross-references

- Plan file: TBD (cj-304 plan 필요 시)
- Phase 4 deployment runbook: `docs/deployment.md`
- cj-299 Postmark: `memory/handoff-2026-09-06-cj-299-email-delivery-wire-done.md`
- cj-300 APScheduler: `memory/handoff-2026-09-07-cj-300-wire-done.md`
- cj-303 EXTENSION: `memory/handoff-2026-09-07-cj-303-uvicorn-boot-fix-wire-done.md`
- Root cause: `apps/api/main.py:625` (POSTMARK 부재) + `apps/api/jobs/scheduled_reports.py` (KST + RETRY_BACKOFF)
