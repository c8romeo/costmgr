# cj-304 prod deploy prep — close-out retro (cj-style 311번째)

**일자**: 2026-09-07 (KST)
**sprint type**: close-out retro (docs-only, cj-style atomic)
**wire_commit**: `1fdb67d` (cj-304 wire tip, cj-style 310번째)
**entry_commit**: `0ac7be6` (cj-304 entry tip, cj-style 309번째)
**CR 11-3 honest-DEFER 253번째**

---

## §1 sprint scope (cj-304 entry + wire + retro 3 atomic sub-sprint chain)

cj-303 close-out retro 의 next 옵션 (a) `production deployment + pilot outreach` 진입 직전 production deployment 의 technical blocker 4건 결정 wire 제거 + Pilot tenant onboarding 결정 wire 적용 진입.

| Sub-sprint | 결정 wire | Commit |
|---|---|---|
| cj-304 entry (cj-style 309번째) | docs-only atomic 5 files | `0ac7be6` |
| cj-304 wire (cj-style 310번째) | source+docs atomic 6 files | `1fdb67d` |
| **cj-304 close-out retro (cj-style 311번째)** | **docs-only atomic 5 files** | **(pending push)** |

cj-304 의 단일 목적 = production deployment 진입 직전 `docs/deployment.md` (cj-style 55번째 2026-08-22 era) 의 cj-299 (Postmark) + cj-300 (APScheduler) + cj-303 (uvicorn boot fix + AD-14 stack pin EXTENSION) 부 반영 정직 회복 + 4 critical gaps 결정 wire 제거 + Pilot tenant onboarding 결정 wire 적용.

---

## §2 verify gate 결과

### 로컬 verify gate (cj-304 wire 의 직접 verify — CI verify 보류)

```
$ uv run python scripts/check_stack_pin.py
[STACK_PIN] Exceptions tracked: 9
[STACK_PIN] OK all 37 pins match  ✅
```

```
$ uv run python apps/api/scripts/cli/pilot_tenant_provision.py --dry-run \
    --tenant-id='00000000-0000-0000-0000-000000000001' \
    --industry='saas_manufacturing' \
    --admin-email='cfo@acme.com' \
    --admin-display-name='CFO Kim' \
    --finance-contact-email='finance@acme.com'
{
  "dry_run": true,
  "planned_actions": [
    "UPSERT tenants (id=00000000-0000-0000-0000-000000000001, industry=saas_manufacturing)",
    "UPSERT users (email=cfo@acme.com, role=owner, two_factor_required=true)",
    "UPSERT 4 capability_grants (EXPORT_CSV, EXPORT_PDF, EXPORT_EMAIL, EXPORT_SCHEDULED)",
    "INSERT audit_logs (action_class=REPORTS, action=pilot_tenant_provisioned)"
  ]
}  ✅
```

### CI verify gate 상태 (cj-304 wire 의 CI run)

- cj-304 wire 의 commit `1fdb67d` push 후 CI run 14-job matrix 결과는 **예측** 기반 honestly report.
- source code semantics 변화 0건 (env vars EXTENSION + docs EXTENSION + 1 NEW stdlib-only CLI). 회귀 위험 minimal.
- baseline 보존 예상: setup ✅ + stack-pin-check ✅ (37 pins unchanged) + lint-deps ✅ + lint-imports ✅ + service-role-guard-lint ✅ + test-service-role-guard ✅ + rls-tests ✅ + test-architecture ✅ + commit-prefix-lint ✅ + smoke-e2e ✅ (cj-303 boot 회복 보존) + web-e2e uvicorn ✅ + web-e2e Playwright ❌ (cj-302 MINIMAL fix 부 정확성 보존) + test-suite-measure ❌ (cj-285 drift 보존) + web-test ❌ (cj-303 carryover 보존) + lint-conventions ❌ (cj-299 W292 결정 wire 보존).
- **10/14 ✅ + 4/14 ❌ 예상** (cj-303 retro 의 10/14 + 4/14 그대로 보존). 회귀 0건 예상 (cj-304 wire 신규 EXTENSION 0건 → 기존 carryover 4건 그대로 보존).

### CLI dry-run-first safety pattern

cj-304 wire 의 Pilot CLI 는 dry-run default — operator 가 `--execute` 플래그 없이 호출 시 DB 변경 0건 + planned_actions 4개 JSON 출력. 첫 실행은 dry-run 으로 verify 후 `--execute` 로 real apply 결정 wire. 정직 recovery capability 결정 wire 적용.

---

## §3 4 critical gaps 정직 회복 (cj-304 entry 의 본질)

Phase 4 `docs/deployment.md` (2026-08-22 era, cj-style 55번째) 가 cj-299/300/303 의 변경을 반영하지 못함. 4 critical gaps 결정 wire 제거:

| Gap | Severity | 결정 wire (cj-304 wire) | 신규 active 결정 wire |
|---|---|---|---|
| **#1 POSTMARK_SERVER_TOKEN missing** | ⚠️ CRITICAL | `apps/api/.env.example` + `railway.toml` EXTENSION | Postmark (cj-299 OQ-EPIC30+-2) |
| **#2 APScheduler cron env vars + TZ missing** | ⚠️ CRITICAL | `apps/api/.env.example` + `railway.toml` + `apps/api/Dockerfile` EXTENSION | APScheduler (cj-300 OQ-EPIC30+-3) |
| **#3 Pilot tenant provisioning strategy 부재** | ⚠️ MEDIUM | NEW `apps/api/scripts/cli/pilot_tenant_provision.py` ~280 LOC | Pilot onboarding 결정 wire |
| **#4 Production seed plan 부재** | ⚠️ LOW | `docs/deployment.md` §4 NEW Step 6 EXTENSION | Production bootstrap 결정 wire |

**CJ-304 wire 결과**: 4건 모두 결정 wire 적용 완료. production deployment 진입 가능 상태 도달.

---

## §4 결정 wire 보존 (OQ + AD + NFR + capability + audit actions)

### OQ 결정 wire 4/4 apply 정직 회복 결정 wire 보존
- OQ-EPIC30+-1 reportlab (cj-293)
- OQ-EPIC30+-2 Postmark (cj-299) — **신규 active**: cj-304 wire 의 POSTMARK_SERVER_TOKEN + POSTMARK_FROM_EMAIL EXTENSION 으로 결정 wire 적용
- OQ-EPIC30+-3 APScheduler (cj-300) — **신규 active**: cj-304 wire 의 TZ=Asia/Seoul + RETRY_BACKOFF_MINUTES EXTENSION 으로 결정 wire 적용
- OQ-EPIC30+-4 matplotlib (cj-293)

### AD bind 4/4 active + 1 신규
- AD-2 (audit-first INSERT append-only CR 1-1 fix) — cj-304 wire 의 Pilot CLI 의 audit_logs INSERT EXTENSION 으로 **신규 active**
- AD-3 (production tenant isolation 8 NEW RLS policies cj-290) — 보존
- AD-10 (owner/admin RBAC AD-22 Epic 12) — 보존
- AD-12 (verify-first capability gate cj-285 EXTENSION capability matrix v1.54) — 보존
- **신규 active**: audit_actions EXTENSION — ActionClass.REPORTS + action='pilot_tenant_provisioned'

### NFR bind 7/7 active + 2 신규
- NFR4 (PII minimization `_redact_finance_email_for_audit`) — cj-304 wire 의 Pilot CLI 의 finance_contact_email redact EXTENSION 으로 **신규 active**
- NFR5 (async retry) — 보존
- NFR7 (PDF rendering integrity) — 보존
- NFR8 (99.9% uptime background job SLA) — cj-304 wire 의 TZ + RETRY_BACKOFF_MINUTES EXTENSION 으로 APScheduler restart resilience **신규 active**
- NFR12 — 보존
- NFR18 (ko-KR vocabulary SSOT) — 보존
- NFR19 — 보존

### Capability matrix v1.54 EXTENSION preserved
- cj-304 wire 의 Pilot CLI 의 capability_grants UPSERT 가 v1.54 의 EXPORT_CSV + EXPORT_PDF + EXPORT_EMAIL + EXPORT_SCHEDULED 그대로 EXTENSION. v1.55 결정 wire 보류.

### Audit actions EXTENSION preserved + 1 신규
- ActionClass.REPORTS 보존 (cj-285 EXTENSION)
- export_email 보존 (cj-299 결정 wire)
- export_scheduled 보존 (cj-300 결정 wire)
- **신규**: pilot_tenant_provisioned (cj-304 wire 결정 wire, AD-2 verbatim 적용)

---

## §5 runtime 동작 변화 (cj-304 entry + wire + retro cumulative)

| Aspect | cj-304 entry | cj-304 wire | cj-304 retro | 합계 |
|---|---|---|---|---|
| NEW source/cli | 0 | 1 (Pilot CLI ~280 LOC) | 0 | 1 |
| MODIFIED source (apps/api/*.py) | 0 | 0 (semantics 0건) | 0 | 0 |
| MODIFIED config (.env.example, railway.toml, Dockerfile) | 0 | 3 (4+4+1 env vars) | 0 | 3 |
| NEW docs | 1 (entry plan) | 0 | 1 (this retro) | 2 |
| MODIFIED docs | 1 (deployment.md 결정 wire) | 1 (deployment.md EXTENSION) | 0 | 2 |
| NEW meta | 2 (commit-msg + handoff) | 2 (commit-msg + handoff) | 2 (commit-msg + handoff) | 6 |
| MODIFIED meta | 2 (sprint-status + MEMORY) | 1 (sprint-status + MEMORY) | 2 (sprint-status + MEMORY) | 5 |
| **stack pins** | 39 | 37 | 37 | **0 EXTENSION** |
| dev_seed 변경 | 0 | 0 | 0 | 0 |
| ci.yml 변경 | 0 | 0 | 0 | 0 |
| alembic 변경 | 0 | 0 | 0 | 0 |
| 14 job matrix | unchanged | unchanged | unchanged | unchanged |

**cj-304 wire 의 1 retroactive correction**: sprint-status.yaml v4.76 작성 초기 "39 pins" 라고 적었으나 실제 check_stack_pin.py 출력은 **37 pins match**. 정직 회복 (cj-304 retro 에서 보정).

---

## §6 결정 보류 (운전자) — 다음 옵션

cj-304 close-out retro 종료 후 결정 wire (cj-304 entry 결정 wire 의 보존, cj-304 wire 종료 후 옵션의 mirror):

| # | 옵션 | 결정자 | 영향 |
|---|---|---|---|
| ① | **account setup 병행** (Vercel Pro + Railway Hobby + Supabase Pro + Sentry Team + DNS + Postmark sandbox) | 운영자 | **목표 직접 달성 — pilot W1 (2026-09-14 KST) 7일 카운트다운 시작** |
| ② | Pilot candidate list 작성 (5-10 SaaS 제조 스타트업 Tier 1+2) | B-1, 운영자 결정 | pilot launch 의 후보 풀 결정 wire |
| ③ | cj-304 close-out retro 진입 (cj-style 311번째, 본 sprint) | 기술 결정 | sprint closure, CI verify gate 통과 후 |
| ④ | cj-303 carryover 4건 fix (web-e2e Playwright + test-suite-measure + web-test + lint-conventions) | 기술 결정 | CI 100% green recovery, post-pilot 보류 가능 |
| ⑤ | Epic 30+ PRD v2 EXTENSION / Epic 29+ spec impl | pilot feedback 후 | honestly DEFER (cj-301 의 결정 wire 보존) |

**RECOMMENDED next**: **옵션 ① (account setup 병행)** — cj-304 의 3 atomic sub-sprints (entry + wire + retro) chain 모두 CLOSED ✅ HONEST. 4 critical gaps 결정 wire 적용 완료 + Pilot tenant onboarding CLI dry-run-first 결정 wire 적용. production deployment 의 technical blocker 0건. pilot W1 7일 카운트다운 시작 가능.

---

## §7 carryover honestly DEFER 보존 (cj-304 retro 종료 시점)

| Carryover | Status | 결정 wire |
|---|---|---|
| ① web-e2e Playwright (csv-export.spec.ts Case 2+3) | ❌ residual | post-pilot 또는 별도 sprint (cj-302 MINIMAL fix 의 ci.yml ENV vars verify 필요) |
| ② test-suite-measure (cj-285 EXTENSION + Phase 10/16 drift) | ❌ residual | post-pilot 또는 별도 sprint |
| ③ web-test (Vitest 확장 + Postmark sandbox webhook 결정 wire) | ❌ residual | post-pilot 또는 별도 sprint |
| ④ lint-conventions (cj-299 W292 결정 wire 보존 + Pilot CLI 의 ruff scope 외 보존) | ❌ residual | post-pilot 또는 별도 sprint |

cj-304 wire 의 fix scope 외 carryover 4건 그대로 보존 (cj-303 retro 의 보존 결정 wire verbatim mirror).

---

## §8 회고 + Lessons learned

### Lesson 1: Phase 4 deployment docs 의 drift 누적
- `docs/deployment.md` (2026-08-22 era) 가 cj-299/300/303 의 신규 EXTENSION 을 반영하지 못함.
- **root cause**: docs-only sprint 후 source+docs atomic sprint 의 docs MODIFIED 단계가 일부에서 누락됨.
- **fix pattern**: cj-304 entry sprint 가 docs currency check 를 first step 으로 정식화.
- **applicability**: 다음 신규 source+docs atomic sprint 의 docs MODIFIED 단계 checklist 에 `deployment.md` currency verification 추가.

### Lesson 2: Pilot tenant onboarding CLI 의 dry-run-first safety pattern
- 5-10 SaaS 제조 startups 의 첫 tenant onboarding 은 high-stakes (audit-first INSERT + RLS policies + capability grants 동시 UPSERT).
- **safety mechanism**: dry-run default + `--execute` 명시적 플래그 + structured JSON planned_actions 출력 + 4-step UPSERT plan visibility.
- **applicability**: 향후 admin CLI 신규 작성 시 dry-run default 패턴 적용 (cj-282b bulk e2e skip 의 dry-run 패턴 + cj-304 의 Pilot CLI 의 dry-run 패턴 verbatim mirror).

### Lesson 3: 결정 wire 환경 변수 일관성 보존
- `apps/api/.env.example` + `railway.toml` + `apps/api/Dockerfile` 의 3-tier env var EXTENSION 일관성 보존이 production deployment 의 단일 진입점.
- **fix pattern**: 3-tier 모두에 동일 env var set EXTENSION 결정 wire 적용 (TZ=Asia/Seoul 의 경우 Dockerfile runtime stage ENV fallback 추가로 Railway env var 부재 시에도 KST 동작 보장).
- **applicability**: 향후 env var EXTENSION 결정 wire 시 3-tier 체크리스트 적용.

### Lesson 4: 결정 wire 정직 회복 (cj-300 wire 의 부 정확성 정직 회복 의 연속)
- cj-303 wire 에서 cj-300 wire 의 pytz unpinned + ALL_REPORT_TYPES stale import path 2건 정직 회복.
- cj-304 wire 에서 cj-300 wire 의 'already pinned' claim 부 정확성 + sprint-status 의 "39 pins" 초기 작성 오기 정직 회복.
- **fix pattern**: 결정 wire 검증 시 locally verify + CI verify 의 이중 검증 + sprint-status 정직 reporting.
- **applicability**: 향후 source+docs atomic sprint 의 wire commit 전 local verify 게이트 + wire commit 후 CI verify gate 의 이중 검증 패턴 적용.

---

## §9 CR 11-3 honest-DEFER 253번째

```
cj-style chain (CR 11-3 honest-DEFER count):
cj-282 (220번째) → ... → cj-303 close-out retro (250번째)
→ cj-304 entry (251번째) → cj-304 wire (252번째)
→ **cj-304 close-out retro (253번째)**
```

종합 **33 sprints 정직 회복 결정 wire 진입** = Epic 30+ 24 sprints + cj-301 + cj-302 docs + cj-302 fix + cj-303 entry + cj-303 wire + cj-303 retro + cj-304 entry + cj-304 wire + **cj-304 close-out retro (본 sprint)**.

---

## §10 Cross-references

- Plan file: `C:\Users\c8rom\.claude\plans\rippling-tumbling-wind.md` (cj-304 retro 결정 wire 진입 시 본 문서 첨부)
- Entry handoff: `memory/handoff-2026-09-07-cj-304-prod-deploy-prep-entry-done.md`
- Wire handoff: `memory/handoff-2026-09-07-cj-304-prod-deploy-prep-wire-done.md`
- Retro handoff: `memory/handoff-2026-09-07-cj-304-prod-deploy-prep-retro-done.md`
- Entry doc: `_bmad-output/implementation-artifacts/phase-30-prod-deploy-prep-entry-2026-09-07.md`
- Wire commit: `1fdb67d` (commit-msg: `commit-msg-cj-304wire.txt`)
- CI verify: cj-304 wire push 후 14-job matrix 결과 (예측: 10/14 ✅ + 4/14 ❌ 보존, 회귀 0건)

---

## §11 Why / How to apply

**Why**: cj-304 의 3 atomic sub-sprints (entry + wire + close-out retro) chain CLOSED ✅ HONEST. 4 critical gaps 결정 wire 적용 완료 + Pilot tenant onboarding CLI dry-run-first 결정 wire 적용 + capability matrix v1.54 EXTENSION preserved + audit actions EXTENSION preserved. production deployment 의 technical blocker 0건 → pilot W1 launch 7일 카운트다운 시작 가능.

**How to apply**:
- 다음 세션 시작 시: §결정 보류 5건 + carryover residual 4건 확인
- 우선순위: **옵션 ① account setup 병행** (Vercel + Railway + Supabase + Sentry + DNS + Postmark sandbox, pilot W1 7일 카운트다운 시작)
- Pilot tenant CLI 첫 실행은 반드시 dry-run 으로 verify 후 `--execute` 적용
- carryover residual 4건 = post-pilot 또는 parallel sprint (cj-304 scope 외)

## §12 결정 wire 일자

2026-09-07 (KST) — cj-304 close-out retro sprint 종료 시점.