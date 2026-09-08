---
name: cj-305 production deploy day-1 wire
description: cj-style 254번째, Pilot W1 D-6 launch prep runbook (4-service minimal viable scope, compressed entry+wire 결정 wire)
metadata:
  type: project
---

# cj-305 production deploy day-1 wire sprint DONE

**cj-style**: 254번째
**날짜**: 2026-09-08 (KST)
**sprint-status**: v4.77 → v4.78 EXTENSION (A722)

## What was done

cj-305 production deploy day-1 wire sprint 결정 wire — Epic 30+ Pilot Gate 의 운영자 실행 단계 진입, Pilot W1 D-day launch 까지 **6일 카운트다운 시작**.

**핵심 결정 wire**:

1. **Compressed entry+wire** — cj-style 3-sub-sprint chain (entry → wire → retro) 의 ~90분 ceremony overhead 가 6-day time-boxed launch 에서 context switching 비용보다 큼 → entry skip, wire 로 흡수. Rationale 5종: ① ceremony overhead ② entry docs 50% stale 위험 ③ Pilot candidate outreach (B-1) critical path 누락 정직 회복 ④ 4-service minimal viable 결정 wire (Sentry + DNS post-W1 defer) ⑤ cj-304 wire 의 4 critical gaps 결정 wire 보존.

2. **4-service minimal viable scope** — Pilot W1 에 Postmark + Supabase + Railway + Vercel 만. Sentry + custom DNS post-W1 honestly DEFER. 월 burn $77 → $50 (35% 절감), signup 시간 ~4-6h → ~2-3h. `*.vercel.app` + `*.up.railway.app` default subdomain 으로 W1 기능 완결 (technical credibility > brand credibility for SaaS 제조 스타트업 5-10 user pilot).

3. **Day-by-day execution runbook** — `docs/deployment-account-setup.md` NEW (~280 LOC 11-section). D-6 (today, signup phase 2-3h) → D-5 (deploy phase, Railway + Supabase alembic) → D-4 (Vercel + E2E smoke test) → D-3 (pilot tenant CLI dry-run → real) → D-2 (outreach 발송) → D-1 (pilot user self-test) → **D-0 Pilot W1 KICKOFF 🚀**.

## File scope (6 files = 2 NEW docs + 2 NEW meta + 2 MODIFIED docs/meta)

1. `docs/deployment-account-setup.md` **NEW** — Pilot W1 day-1 runbook (signup URLs, capture tables, day-by-day plan, smoke tests)
2. `docs/deployment.md` **MODIFIED** — Related link EXTENSION → deployment-account-setup.md
3. `_bmad-output/implementation-artifacts/commit-msg-cj-305wire.txt` **NEW**
4. `_bmad-output/implementation-artifacts/handoff-2026-09-08-cj-305-wire-done.md` **NEW** (본 파일)
5. `_bmad-output/implementation-artifacts/sprint-status.yaml` **MODIFIED** — v4.77 → v4.78 EXTENSION (A722 + last_updated_note_v4_78)
6. `memory/MEMORY.md` **MODIFIED** — cj-305 wire hook + Active sprint state post cj-305 wire EXTENSION

## 결정 wire 보존 확인

- **OQ 결정 wire 4/4 apply 보존** (reportlab + Postmark + APScheduler + matplotlib)
- **AD bind 4/4 active 보존** (cj-305 wire 는 docs+meta, source code 변경 0건)
- **NFR bind 7/7 active 보존**
- **capability matrix v1.54 EXTENSION preserved**
- **audit actions EXTENSION preserved**
- **34/34 cumulative 결정 wire 보존**
- **CR 11-3 honest-DEFER 254번째**

## Runtime 동작 변화

- source code 변경 0건
- dev_seed 변경 0건
- ci.yml 변경 0건
- alembic 변경 0건
- 37 pins unchanged (cj-303 EXTENSION 보존)
- 14 job matrix unchanged

## PRE-EXISTING honestly DEFER carryover

- 4건 그대로 보존: web-e2e Playwright + test-suite-measure 잔여 + web-test + lint-conventions
- 2건 추가 defer (cj-305 wire 신규): Sentry + custom DNS → post-W1

## 결정 보류 (운전자)

① **옵션 (a, RECOMMENDED next)**: cj-305 wire commit 즉시 + Postmark + Supabase signup 즉시 시작 (D-6 오늘 2026-09-08 KST, 병렬, ~2-3h)
② 옵션 (b): Pilot candidate list (B-1) 먼저 작성
③ 옵션 (c): cj-303 carryover 4건 fix (post-pilot 또는 별도 sprint)
④ 옵션 (d): PRD v2 EXTENSION / Epic 29+ spec impl (pilot feedback 후)

## 다음 세션 resume path

1. cj-305 wire commit 후, 옵션 (a) 즉시 실행:
   - Postmark sandbox signup (browser, 5분)
   - Supabase Pro signup (browser, 3분)
   - Token capture → 1Password secure note
2. Day 2 (D-5): Railway signup + repo connect + env vars fill + deploy → `/health` 200 verify
3. Day 3 (D-4): Vercel signup + deploy + CORS update → browser smoke test
4. Day 4 (D-3): Pilot tenant CLI dry-run → real
5. Day 5 (D-2): Pilot candidate outreach (B-1) 발송
6. Day 7 (D-0, 2026-09-14 KST): **Pilot W1 KICKOFF 🚀**

## Cross-references

- **cj-304 prod deploy prep wire** (`1fdb67d`): 4 critical gaps fix + Pilot tenant CLI + env.example + railway.toml + Dockerfile + docs/deployment.md
- **cj-304 prod deploy prep retro** (`e7fb753`): 결정 wire 적용 확인, 33/33 cumulative
- **cj-303 uvicorn boot fix wire**: AD-14 stack pin EXTENSION (apscheduler + pytz)
- **cj-299 email delivery wire**: Postmark HTTP API 결정 wire
- **cj-300 scheduled reports wire**: APScheduler 4 cron + pytz KST
- **cj-301 pilot outreach prep**: 5-10 SaaS 제조 스타트업 8-week pilot
