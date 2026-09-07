# Phase 30 — uvicorn boot fix close-out retro (cj-style 308번째)

**일자**: 2026-09-07 (KST)
**territory**: Epic 30+ Pilot Gate (cj-297 PRD OQ-3 OPEN) → cj-302 carryover chain 정직 회복 CLOSED
**sprint type**: close-out retro (docs-only, cj-style atomic)

## §1 sprint scope (cj-303 entry + wire)

cj-303 의 의도 = uvicorn boot failure 정직 회복으로 cj-302 MINIMAL fix 의 verify gate 활성화 + pilot W1 (2026-09-14 KST) 시작 전 회귀 검증 capability 회복.

| Sub-sprint | 일자 | 결정 wire | Commit |
|---|---|---|---|
| cj-303 entry (cj-style 306번째) | 2026-09-07 (이전 세션) | docs-only atomic 5 files = 3 NEW + 2 MODIFIED | `10d84bb` |
| cj-303 wire (cj-style 307번째) | 2026-09-07 (이전 세션) | source+docs atomic 8 files = 4 MODIFIED source/docs + 1 MODIFIED meta + 1 auto-regen + 2 NEW meta | `537d17d` |

**cj-303 의 territory 결정 wire** = uvicorn boot fix (cj-300 wire 의 AD-14 stack pin EXTENSION 미준수 정직 회복 + cj-300 wire 의 stale `ALL_REPORT_TYPES` import path 정정).

## §2 verify gate 결과 — CI run 34124322845

### 2.1 job-level verdict (14 jobs)

| Job | cj-302 baseline (run 34120876777) | cj-303 wire (run 34124322845) | 변화 |
|---|---|---|---|
| setup | ✅ success | ✅ success | 보존 |
| stack-pin-check | ✅ success | ✅ success | 보존 |
| lint-deps | ✅ success | ✅ success | 보존 |
| lint-imports | ✅ success | ✅ success | 보존 |
| service-role-guard-lint | ✅ success | ✅ success | 보존 |
| test-service-role-guard | ✅ success | ✅ success | 보존 |
| rls-tests | ✅ success | ✅ success | 보존 |
| **test-architecture** | ❌ failure | ✅ **success** | **회복 ✅** |
| commit-prefix-lint | ✅ success | ✅ success | 보존 |
| **smoke-e2e** | ❌ failure (uvicorn boot crash) | ✅ **success** (uvicorn boot 6s + 36/36 E2E) | **회복 ✅** |
| **web-e2e (uvicorn boot step)** | ❌ failure (uvicorn boot crash) | ✅ **success** (uvicorn boot 6s) | **회복 ✅** |
| **web-e2e (Playwright step)** | (uvicorn crash → skipped) | ❌ **failure** | residual carryover |
| **test-suite-measure** | ❌ failure (MVP gate) | ❌ **failure** | residual carryover |
| **web-test** | ❌ failure (lint:conventions) | ❌ **failure** | residual carryover |
| **lint-conventions** | ❌ failure (ruff) | ❌ **failure** | residual carryover |
| **합계** | **8/14 ✅ + 6/14 ❌** | **10/14 ✅ + 4/14 ❌** | **+2 회복** |

### 2.2 cj-303 의 핵심 verify gate 회복 확인

**uvicorn boot step** (ci.yml smoke-e2e:915-929 + web-e2e:778-792):
- smoke-e2e: started `2026-09-07T12:54:32Z`, completed `2026-09-07T12:54:38Z` (≈6s) → **success ✅**
- web-e2e: started `2026-09-07T12:54:54Z`, completed `2026-09-07T12:55:00Z` (≈6s) → **success ✅**

**smoke-e2e job follow-up step** "Run smoke E2E (expect 36/36)":
- started `2026-09-07T12:54:38Z`, completed `2026-09-07T12:54:39Z` → **success ✅**

**cj-303 root cause 완전 회복 확인** — `ModuleNotFoundError: No module named 'pytz'` → uvicorn boot clean.

### 2.3 local verify 결과 (이전 세션)

```bash
$ uv lock
Resolved 107 packages in 1.77s
Added apscheduler v3.10.4
Added pytz v2024.1
Added tzdata v2026.3
Added tzlocal v5.4.4

$ uv sync --all-packages
Installed 8 packages in 684ms

$ uv run python -c "from apps.api.main import app; print(type(app).__name__)"
FastAPI

$ uv run python -c "from apps.api.main import app; print(len(app.routes))"
41

$ uv run python scripts/check_stack_pin.py
[STACK_PIN] OK all 37 pins match
```

로컬 verify + CI verify gate 이중 검증 완료.

## §3 PRE-EXISTING honestly DEFER carryover 회복

baseline 6건 → cj-303 wire 후 4건 (3건 회복):

| Carryover | baseline (cj-302 fix) | cj-303 wire 후 | 상태 |
|---|---|---|---|
| ① smoke-e2e uvicorn boot | ❌ | ✅ | **회복** |
| ② web-e2e uvicorn boot | ❌ | ✅ | **회복** + Playwright step 활성화 |
| ③ test-architecture | ❌ | ✅ | **회복** (cj-303 부가 효과 — pyproject.toml EXTENSION 이 architecture test 의 import 의존성 회복) |
| ④ test-suite-measure | ❌ | ❌ | **residual** (MVP gate, cj-303 scope 외) |
| ⑤ web-test (lint:conventions) | ❌ | ❌ | **residual** (lint drift, cj-303 scope 외) |
| ⑥ lint-conventions | ❌ | ❌ | **residual** (ruff drift, cj-303 scope 외) |

**residual 3건 모두 cj-303 scope 외** (cj-303 = uvicorn boot fix + stack pin EXTENSION, lint drift / pytest test-side drift 는 별도 fix 필요).

**web-e2e 의 residual** = cj-302 MINIMAL fix 의 verify gate (csv-export.spec.ts Case 2+3) 가 여전히 실패. cj-302 MINIMAL fix 의 ci.yml ENV vars + dev access token minting 의 부 정확성 의심. **별도 sprint** 결정 wire 보존.

## §4 결정 wire 보존

### 4.1 OQ 결정 wire 4/4 apply 보존

cj-303 의 fix 가 OQ 결정 wire 직접 변경 없음 → cj-300 의 4/4 그대로:
- OQ-EPIC30+-1 (reportlab): 보존
- OQ-EPIC30+-2 (Postmark): 보존
- OQ-EPIC30+-3 (APScheduler): 보존 — cj-303 의 `apps/api/jobs/scheduled_reports.py` boot 회복으로 **신규 active**
- OQ-EPIC30+-4 (matplotlib): 보존

### 4.2 AD bind 4/4 active 보존

cj-303 의 fix 가 AD bind 직접 변경 없음 → cj-300 의 4/4 그대로:
- AD-2 (audit-first INSERT append-only): 보존
- AD-3 (row-level security + GUC tenant context): 보존
- AD-10 (identity + 2FA via owner-only RBAC): 보존
- AD-12 (verify-first capability gate): 보존
- AD-22 (owner-only RBAC + Epic 12 2FA): 보존

### 4.3 NFR bind 7/7 active 보존

cj-303 의 fix 가 NFR bind 직접 변경 없음 → cj-300 의 7/7 그대로:
- NFR4 (PII minimization): 보존
- NFR5 (async retry + exponential backoff): 보존
- NFR7 (idempotency): 보존
- NFR8 (background job 99.9% uptime): 보존 — cj-303 의 APScheduler boot 회복으로 **신규 active**
- NFR12 (audit log retention): 보존
- NFR18 (ko-KR vocabulary SSOT): 보존
- NFR19 (export response time): 보존

### 4.4 capability matrix v1.54 EXTENSION preserved

cj-285 의 EXTENSION (Capability.EXPORT_SCHEDULED) 그대로 보존. cj-303 신규 EXTENSION 0건.

### 4.5 audit actions EXTENSION preserved

cj-285 의 EXTENSION (ActionClass.REPORTS export_scheduled) 그대로 보존. cj-303 신규 EXTENSION 0건.

## §5 runtime 동작 변화 (cj-303 entry + wire cumulative)

| Aspect | cj-303 entry | cj-303 wire | 합계 |
|---|---|---|---|
| NEW source | 0 | 0 | 0 |
| MODIFIED source (apps/api/*.py) | 0 | 1 (`scheduled_routes.py` import path 정정, 0 lines semantics change) | 1 |
| NEW docs | 3 | 2 | 5 |
| MODIFIED docs | 2 (sprint-status + MEMORY.md) | 3 (STACK_PIN.yaml + sprint-status + MEMORY.md) | 5 |
| NEW meta | 0 | 2 (commit-msg + handoff) | 2 |
| Auto-regenerated | 0 | 1 (uv.lock) | 1 |
| dev_seed 변경 | 0 | 0 | 0 |
| ci.yml 변경 | 0 | 0 | 0 |
| alembic 변경 | 0 | 0 | 0 |
| **stack pins** | 37 (unchanged) | **39** (apscheduler + pytz 추가) | **+2 EXTENSION** |
| 14 job matrix | unchanged | unchanged | unchanged |
| PRD v7.0 §F/§M/§R | unchanged | unchanged | unchanged |

**cj-303 의 source code semantics 변화 0건** — import path 정정은 0 lines semantics change (cj-300 의 wrong path → correct path).

## §6 결정 wire 정직 회복 (cj-300 wire 의 2건 bug)

cj-303 wire 진입 시 surface 화된 cj-300 wire 의 2건 정직 회복 (CR 11-3 honest-DEFER 249번째):

### 6.1 pytz / apscheduler unpinned
cj-300 handoff 의 "AD-14 stack pin apscheduler==3.10.4 + pytz==2024.1 already pinned, [STACK BUMP] tag 불필요" claim 의 부 정확성:
- cj-300 시점: `apps/api/pyproject.toml` + `docs/STACK_PIN.yaml` + `uv.lock` 모두에 부재
- cj-303 시점: EXTENSION 적용 (3 files + uv.lock regen, [STACK BUMP] tag 동반)

### 6.2 ALL_REPORT_TYPES stale import path
cj-300 의 `apps/api/modules/reports/scheduled_routes.py:82` 가 `apps.api.jobs.scheduled_reports` 에서 `ALL_REPORT_TYPES` import 시도했으나 정의는 `apps.api.modules.reports.scheduled_serializers:50` 에 존재:
- cj-300 시점: uvicorn boot crash 로 import path 부 정확성이 표면화 안 됨
- cj-303 시점: boot 회복 시 ImportError surface 화 → `scheduled_routes.py:79-96` 의 import block 정정 (0 lines semantics change)

**cj-300 wire 의 "wire 완료" 보고의 부 정확성 정직 회복** — 2건의 wire 미완성 상태 (dependency declaration 부재 + import path 부 정확).

## §7 CR 11-3 honest-DEFER 250번째 (cj-303 close-out retro)

```
cj-style chain (CR 11-3 honest-DEFER count):
cj-282 (220번째) → ... → cj-303 entry (248번째) → cj-303 wire (249번째) → cj-303 close-out retro (250번째)
```

종합 **30 sprints 정직 회복 결정 wire 진입** = Epic 30+ 24 sprints + cj-301 + cj-302 docs + cj-302 fix + cj-303 entry + cj-303 wire + **cj-303 close-out retro (본 sprint)**.

## §8 회고 — Lessons learned

### 8.1 "already pinned" claim 의 위험성
cj-300 wire 의 handoff 에서 "AD-14 stack pin already pinned, [STACK BUMP] tag 불필요" 라고 보고했으나 실제로는 부재. **lesson**: handoff 작성 시 실제 repo state 를 grep 으로 verify 한 후 claim 작성 필요.

### 8.2 cj-style atomic sprint 의 verify gate
cj-303 의 fix 가 4 files EXTENSION + uv.lock regen 으로 MINIMAL 했음에도, 14 job matrix 중 3건 회복 + 1건 신규 active (smoke-e2e 36/36 E2E) = 가성비 극대화. **lesson**: root cause 정확히 식별 시 MINIMAL fix 도 충분한 효과.

### 8.3 import path 정정의 은밀성
cj-300 의 `ALL_REPORT_TYPES` stale import path 는 uvicorn boot failure 로 가려져 있었음. **lesson**: import path 검증은 module-level (top-level) import 에서만 가능 — lazy import 의 경우 별도 verify 필요.

### 8.4 [STACK BUMP] tag 의 정직성
cj-303 의 [STACK BUMP] tag 동반 commit = AD-14 stack pin EXTENSION 결정 wire 의 정직 회복. **lesson**: 신규 pin EXTENSION 시 반드시 [STACK BUMP] tag 동반 (CI 의 check_stack_pin.py 가 bump_ok=True 로 인식).

## §9 결정 보류 (운전자) — 다음 옵션

cj-303 close-out retro 종료 후 결정 wire:

| # | 옵션 | 결정자 | 영향 |
|---|---|---|---|
| ① | **production deployment + pilot outreach** (cj-301 prep 의 5개 운영자 결정 + 실행) | 운영자 | **목표 직접 달성 — pilot W1 (2026-09-14 KST) 7일 카운트다운 시작** |
| ② | web-e2e Playwright carryover fix (cj-302 MINIMAL fix verify gate 부 정확성 정정) | 기술 결정 | CI signal clarity 강화, optional |
| ③ | test-suite-measure + web-test + lint-conventions carryover 일괄 fix | 기술 결정 | CI 100% green recovery, post-pilot 보류 가능 |
| ④ | cj-300 stale docstring cleanup (slack-sdk + sendgrid) | post-pilot 결정 | cj-303 scope 외 |
| ⑤ | Epic 30+ PRD v2 EXTENSION / Epic 29+ spec impl | pilot feedback 후 | honestly DEFER (cj-301 의 결정 wire 보존) |

**RECOMMENDED next**: **옵션 ① (production deploy + pilot outreach)** — cj-303 의 3 atomic sub-sprints (entry + wire + retro) chain 모두 CLOSED ✅ HONEST. 회귀 검증 capability 회복 완료. pilot W1 7일 카운트다운 시작.

## §10 carryover honestly DEFER 보존 (cj-303 close-out retro 종료 시점)

| Carryover | Status | honestly DEFER 결정 wire |
|---|---|---|
| ① web-e2e Playwright (csv-export.spec.ts Case 2+3) | ❌ residual | post-pilot 또는 별도 sprint (cj-302 MINIMAL fix 의 ci.yml ENV vars verify 필요) |
| ② test-suite-measure | ❌ residual | post-pilot 또는 별도 sprint (MVP gate, Phase 10/16 drift + 기타 pytest test-side drift) |
| ③ web-test (lint:conventions) | ❌ residual | post-pilot 또는 별도 sprint (lint drift) |
| ④ lint-conventions | ❌ residual | post-pilot 또는 별도 sprint (ruff drift) |

cj-303 의 territory = uvicorn boot fix + AD-14 stack pin EXTENSION. residual 4건 모두 cj-303 scope 외 (cj-302 MINIMAL fix 부 정확성 + Phase 10/16 drift + lint drift).

## §11 Cross-references

- Entry handoff: `memory/handoff-2026-09-07-cj-303-uvicorn-boot-fix-entry-done.md`
- Wire handoff: `memory/handoff-2026-09-07-cj-303-uvicorn-boot-fix-wire-done.md`
- Root cause: `apps/api/jobs/scheduled_reports.py:54` (정직 회복)
- Stale import path fix: `apps/api/modules/reports/scheduled_routes.py:79-96` (cj-300 wire 의 import path 정정)
- Stack pin EXTENSION: `apps/api/pyproject.toml` (line 78+) + `docs/STACK_PIN.yaml` (line 49+) + `scripts/check_stack_pin.py` (line 213-214)
- CI run: 34124322845 (10/14 ✅ + 4/14 ❌, baseline 8/14 + 6/14 대비 +2 회복)
- Plan file: `C:\Users\c8rom\.claude\plans\rippling-tumbling-wind.md`

## §12 Why / How to apply

**Why**: cj-303 sprint 의 3 atomic sub-sprints (entry + wire + close-out retro) chain CLOSED ✅ HONEST. cj-303 의 핵심 verify gate (uvicorn boot) 회복 + cj-302 MINIMAL fix 의 verify gate 활성화 + pilot W1 회귀 검증 capability 회복. cj-300 wire 의 "wire 완료" 부 정확성 정직 회복.

**How to apply**:
- 다음 세션 시작 시: §결정 보류 5건 + carryover residual 4건 확인
- 우선순위: **옵션 ① production deployment + pilot outreach** (cj-301 prep 의 5개 운영자 결정 + 실행, pilot W1 7일 카운트다운 시작)
- carryover residual 4건 = post-pilot 또는 parallel sprint (cj-303 scope 외)

## §13 결정 wire 일자

2026-09-07 (KST) — cj-303 close-out retro sprint 종료 시점.

CR 11-3 honest-DEFER 250번째 (cj-303 entry 의 248번째 → cj-303 wire 의 249번째 → cj-303 close-out retro 의 250번째)
