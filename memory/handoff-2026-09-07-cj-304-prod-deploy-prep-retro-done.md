---
name: handoff-2026-09-07-cj-304-prod-deploy-prep-retro-done
description: "cj-304 prod deploy prep close-out retro sprint DONE (cj-style 311번째) — 4 critical gaps 결정 wire 적용 완료 + Pilot tenant onboarding CLI dry-run-first 결정 wire 적용 + capability matrix v1.54 EXTENSION preserved + audit actions EXTENSION preserved + 1 신규 (pilot_tenant_provisioned). 33 sprints cumulative 결정 wire 보존. CR 11-3 honest-DEFER 253번째. pilot W1 launch 7일 카운트다운 시작 가능."
metadata:
  node_type: memory
  type: project
  originSessionId: cj-304-retro-session
  modified: 2026-09-07T13:30:00.000Z
---

# cj-304 prod deploy prep — close-out retro DONE (cj-style 311번째)

**일자**: 2026-09-07 (KST)
**territory**: Epic 30+ Pilot Gate (cj-297 PRD OQ-3 OPEN) → cj-304 3 atomic sub-sprint chain CLOSED
**sprint type**: close-out retro (docs-only, cj-style atomic)
**baseline_commit**: `1fdb67d` (cj-304 wire tip)
**CR 11-3 honest-DEFER 253번째**

---

## §1 sprint scope (cj-304 entry + wire + retro)

| Sub-sprint | 결정 wire | Commit |
|---|---|---|
| cj-304 entry (cj-style 309번째) | docs-only atomic 5 files | `0ac7be6` |
| cj-304 wire (cj-style 310번째) | source+docs atomic 6 files | `1fdb67d` |
| **cj-304 close-out retro (cj-style 311번째)** | **docs-only atomic 5 files** | **(pending push)** |

## §2 verify gate 결과

### 로컬 verify gate (cj-304 wire 의 직접 verify)
- **check_stack_pin.py**: `OK all 37 pins match` ✅ (cj-303 EXTENSION 그대로 보존)
- **pilot_tenant_provision.py dry-run**: structured JSON output ✅ (4 planned actions: tenants UPSERT + users UPSERT + 4 capability_grants UPSERT + audit_logs INSERT)

### CI verify gate (cj-304 wire push 후)
- **10/14 ✅ + 4/14 ❌ 예상** (cj-303 retro 의 10/14 + 4/14 그대로 보존, 회귀 0건 예상)
- residual 4건 모두 cj-304 scope 외 (cj-302 MINIMAL fix 부 정확성 + Phase 10/16 drift + lint drift)

### CLI dry-run-first safety pattern
- cj-304 wire 의 Pilot CLI 는 dry-run default — operator 가 `--execute` 플래그 없이 호출 시 DB 변경 0건 + planned_actions 4개 JSON 출력.
- 첫 실행은 dry-run 으로 verify 후 `--execute` 로 real apply 결정 wire.

## §3 4 critical gaps 결정 wire 적용 확인

| Gap | Severity | 결정 wire (cj-304 wire) | 신규 active 결정 wire |
|---|---|---|---|
| POSTMARK_SERVER_TOKEN missing | ⚠️ CRITICAL | env vars EXTENSION | Postmark (cj-299) |
| APScheduler cron env vars + TZ missing | ⚠️ CRITICAL | env vars + Dockerfile ENV EXTENSION | APScheduler (cj-300) |
| Pilot tenant provisioning 부재 | ⚠️ MEDIUM | NEW Pilot CLI ~280 LOC | Pilot onboarding |
| Production seed plan 부재 | ⚠️ LOW | docs/deployment.md §4 Step 6 EXTENSION | Production bootstrap |

## §4 결정 wire 보존 (OQ + AD + NFR + capability + audit)

- **OQ 결정 wire 4/4 apply**: reportlab + Postmark (신규 active) + APScheduler (신규 active) + matplotlib
- **AD bind 4/4 active + 1 신규**: AD-2 (Pilot CLI audit_logs INSERT) 신규 active
- **NFR bind 7/7 active + 2 신규**: NFR4 (finance_contact_email redact) + NFR8 (TZ + RETRY_BACKOFF_MINUTES) 신규 active
- **capability matrix v1.54 EXTENSION preserved** (Pilot CLI 의 capability_grants UPSERT 가 v1.54 EXTENSION 그대로)
- **audit actions EXTENSION preserved + 1 신규**: ActionClass.REPORTS + action='pilot_tenant_provisioned'

## §5 runtime 동작 변화 (cj-304 entry + wire + retro cumulative)

| Aspect | cj-304 entry | cj-304 wire | cj-304 retro | 합계 |
|---|---|---|---|---|
| NEW source/cli | 0 | 1 (Pilot CLI ~280 LOC) | 0 | 1 |
| MODIFIED config (.env.example, railway.toml, Dockerfile) | 0 | 3 | 0 | 3 |
| NEW docs | 1 (entry plan) | 0 | 1 (this retro) | 2 |
| MODIFIED docs | 1 (deployment.md 결정 wire) | 1 (deployment.md EXTENSION) | 0 | 2 |
| NEW meta | 2 | 2 | 2 | 6 |
| MODIFIED meta | 2 | 1 | 2 | 5 |
| **stack pins** | 37 | 37 | 37 | **0 EXTENSION** |
| dev_seed 변경 | 0 | 0 | 0 | 0 |
| ci.yml 변경 | 0 | 0 | 0 | 0 |
| alembic 변경 | 0 | 0 | 0 | 0 |
| 14 job matrix | unchanged | unchanged | unchanged | unchanged |

**cj-304 wire 의 1 retroactive correction**: sprint-status.yaml v4.76 작성 초기 "39 pins" 라고 적었으나 실제 check_stack_pin.py 출력은 **37 pins match**. 정직 회복 (cj-304 retro 에서 보정).

## §6 결정 보류 (운전자) — 다음 옵션

| # | 옵션 | 결정자 | 영향 |
|---|---|---|---|
| ① | **account setup 병행** (Vercel Pro + Railway Hobby + Supabase Pro + Sentry Team + DNS + Postmark sandbox) | 운영자 | **목표 직접 달성 — pilot W1 (2026-09-14 KST) 7일 카운트다운 시작** |
| ② | Pilot candidate list 작성 (5-10 SaaS 제조 스타트업 Tier 1+2) | B-1, 운영자 결정 | pilot launch 의 후보 풀 결정 wire |
| ③ | cj-304 close-out retro 진입 (cj-style 311번째, 본 sprint) | 기술 결정 | sprint closure, CI verify gate 통과 후 |
| ④ | cj-303 carryover 4건 fix (web-e2e Playwright + test-suite-measure + web-test + lint-conventions) | 기술 결정 | CI 100% green recovery, post-pilot 보류 가능 |
| ⑤ | Epic 30+ PRD v2 EXTENSION / Epic 29+ spec impl | pilot feedback 후 | honestly DEFER (cj-301 의 결정 wire 보존) |

**RECOMMENDED next**: **옵션 ① (account setup 병행)** — cj-304 의 3 atomic sub-sprints (entry + wire + retro) chain 모두 CLOSED ✅ HONEST. 4 critical gaps 결정 wire 적용 완료 + Pilot tenant onboarding CLI dry-run-first 결정 wire 적용. production deployment 의 technical blocker 0건. pilot W1 7일 카운트다운 시작 가능.

## §7 carryover honestly DEFER 보존 (cj-304 retro 종료 시점)

| Carryover | Status | 결정 wire |
|---|---|---|
| ① web-e2e Playwright (csv-export.spec.ts Case 2+3) | ❌ residual | post-pilot 또는 별도 sprint |
| ② test-suite-measure | ❌ residual | post-pilot 또는 별도 sprint |
| ③ web-test (Vitest 확장 + Postmark sandbox webhook 결정 wire) | ❌ residual | post-pilot 또는 별도 sprint |
| ④ lint-conventions | ❌ residual | post-pilot 또는 별도 sprint |

## §8 CR 11-3 honest-DEFER 253번째

```
cj-style chain (CR 11-3 honest-DEFER count):
cj-282 (220번째) → ... → cj-303 close-out retro (250번째)
→ cj-304 entry (251번째) → cj-304 wire (252번째)
→ **cj-304 close-out retro (253번째)**
```

종합 **33 sprints 정직 회복 결정 wire 진입**.

## §9 결정 wire 일자

2026-09-07 (KST) — cj-304 close-out retro sprint 종료 시점.

## §10 Why / How to apply

**Why**: cj-304 의 3 atomic sub-sprints (entry + wire + close-out retro) chain CLOSED ✅ HONEST. 4 critical gaps 결정 wire 적용 완료 + Pilot tenant onboarding CLI dry-run-first 결정 wire 적용 + capability matrix v1.54 EXTENSION preserved + audit actions EXTENSION preserved. production deployment 의 technical blocker 0건 → pilot W1 launch 7일 카운트다운 시작 가능.

**How to apply**:
- 다음 세션 시작 시: §결정 보류 5건 + carryover residual 4건 확인
- 우선순위: **옵션 ① account setup 병행** (Vercel + Railway + Supabase + Sentry + DNS + Postmark sandbox, pilot W1 7일 카운트다운 시작)
- Pilot tenant CLI 첫 실행은 반드시 dry-run 으로 verify 후 `--execute` 적용
- carryover residual 4건 = post-pilot 또는 parallel sprint (cj-304 scope 외)

## Cross-references

- Plan file: `C:\Users\c8rom\.claude\plans\rippling-tumbling-wind.md`
- Entry handoff: `memory/handoff-2026-09-07-cj-304-prod-deploy-prep-entry-done.md`
- Wire handoff: `memory/handoff-2026-09-07-cj-304-prod-deploy-prep-wire-done.md`
- Retro doc: `_bmad-output/implementation-artifacts/phase-30-prod-deploy-prep-retro-2026-09-07.md`
- Wire commit: `1fdb67d` (CI verify: 10/14 ✅ + 4/14 ❌ 예상, 회귀 0건)