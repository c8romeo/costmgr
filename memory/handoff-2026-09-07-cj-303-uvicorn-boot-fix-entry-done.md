---
name: handoff-2026-09-07-cj-303-uvicorn-boot-fix-entry-done
description: "cj-303 uvicorn boot fix entry decision wire (cj-style 306번째) — AD-14 stack pin EXTENSION 결정 wire 진입 (cj-300 'already pinned' claim 정직 회복). 5 files = 3 NEW + 2 MODIFIED docs-only atomic. CR 11-3 honest-DEFER 248번째."
metadata:
  node_type: memory
  type: project
  originSessionId: e85acf61-c75a-4985-990b-b5f6b80a7640
  modified: 2026-09-07T13:00:00.000Z
---

# cj-303 uvicorn boot fix — entry decision wire DONE (cj-style 306번째)

**일자**: 2026-09-07 (KST)
**territory**: Epic 30+ Pilot Gate (cj-297 PRD OQ-3 OPEN) → cj-302 carryover chain 정직 회복
**sprint type**: docs-only atomic single sprint (cj-303 entry)
**baseline_commit**: `3305b36` (cj-302 MINIMAL fix tip)

---

## §1 의도 분석

cj-302 fix sprint 의 CI run 34120876777 결과 = 8/14 ✅ + 6/14 ❌. ZERO regressions vs cj-301 baseline — 6 failures ALL PRE-EXISTING honestly DEFER carryover. 그 중 1건 = **uvicorn boot failure** (smoke-e2e + web-e2e 양쪽). cj-302 MINIMAL fix 의 verify gate (web-e2e csv-export.spec.ts Case 2+3) 차단 → MINIMAL fix effectiveness = UNVERIFIED ⚠️ 보존.

운전자 옵션 (a) "uvicorn boot fix 진행" 승인 → cj-303 sprint 진입.

cj-303 의 단일 목적 = **uvicorn boot failure 의 root cause 를 정확히 식별 + fix scope 를 결정 wire 으로 명문화** (source code 변경 없음, docs-only). 실제 source 변경은 cj-303 wire sprint (cj-style 307번째) 에서 결정 wire 적용.

## §2 Root Cause (재현 + Import chain)

### 로컬 재현

```bash
$ cd C:/Users/c8rom/desktop/a/costmgr
$ uv run python -c "from apps.api.main import app; print('OK')"
File "C:\Users\c8rom\desktop\a\costmgr\apps\api\main.py", line 655, in <module>
    from apps.api.modules.reports.scheduled_routes import (  # noqa: E402
  File "C:\Users\c8rom\desktop\a\costmgr\apps\api\modules\reports\scheduled_routes.py", line 79, in <module>
    from apps.api.jobs.scheduled_reports import (
  File "C:\Users\c8rom\desktop\a\costmgr\apps\api\jobs\scheduled_reports.py", line 54, in <module>
    import pytz
ModuleNotFoundError: No module named 'pytz'
```

### Import chain (transitive crash)

```
uvicorn apps.api.main:app
  ↓
apps/api/main.py:655
  from apps.api.modules.reports.scheduled_routes import router as scheduled_reports_router
  ↓
apps/api/modules/reports/scheduled_routes.py:79
  from apps.api.jobs.scheduled_reports import (...)
  ↓
apps/api/jobs/scheduled_reports.py:54
  import pytz    # ← TOP-LEVEL — module load time
  ↓
apps/api/jobs/scheduled_reports.py:72
  KST = pytz.timezone("Asia/Seoul")    # ← MODULE-LEVEL CONSTANT
  ↓
ModuleNotFoundError: No module named 'pytz'
```

### 왜 unpinned 상태가 됐나 (cj-300 정직 회복)

cj-300 wire sprint handoff (handoff-2026-09-07-cj-300-wire-done.md) 의 claim:
> "AD-14 stack pin — apscheduler==3.10.4 + pytz==2024.1 (already pinned, [STACK BUMP] tag 불필요)"

**그러나 실제 grep 결과**:

| 위치 | apscheduler | pytz |
|---|---|---|
| `apps/api/pyproject.toml` (line 14-79) | ❌ 부재 | ❌ 부재 |
| root `pyproject.toml` | ❌ 부재 | ❌ 부재 |
| `uv.lock` (1559 lines) | ❌ 0 matches | ❌ 0 matches |
| `docs/STACK_PIN.yaml` | ❌ 부재 | ❌ 부재 |

**cj-300 의 claim 은 부 정확** — declaration 없이 wire 만 작성. CR 11-3 honest-DEFER 248번째 결정 wire 적용.

## §3 영향 범위 (Explore agent 검증 완료)

### Critical (cj-303 fix 대상)

| Package | Version | Usage sites |
|---|---|---|
| **`pytz`** | 2024.1 | **7 files top-level `import pytz`**: `scheduled_reports.py:54` (cj-303 root cause) + `scheduled_executive_dispatch.py:38` + `scheduled_unit_economics_calculation_job.py:41` + `scheduled_multi_cloud_dispatch_job.py:42` + `scheduled_commitment_dispatch.py:39` + `scheduled_chargeback_settlement_dispatch_job.py:40` + `executive_report_delivery.py:32`. `pytz.timezone("Asia/Seoul")` module-level 상수가 `scheduled_reports.py:72` 에서 평가됨 |
| **`apscheduler`** | 3.10.4 | **14 files `from apscheduler.triggers.cron import CronTrigger`** (lazy in `_validate_cron_function`) + 6 files scheduler variants. `_validate_cron_expression` → `schedule_report` → `scheduled_routes.py:195` 호출 chain 으로 trigger |

### ✅ Verified clean (cj-303 fix scope 외)

- `email_routes.py` / `scheduled_routes.py`: fastapi==0.139.2 + sqlalchemy==2.0.36 + internal modules 만 import
- `email_service.py` / `email_provider.py`: stdlib `smtplib` + pinned `httpx==0.27.0` (Postmark raw HTTP API)
- `apps/api/main.py:619-700` (cj-299/300 added region): 모든 declared import 가 traceable
- `alembic/versions/0061`: alembic==1.18.5 + sqlalchemy==2.0.36 only
- `EmailExportTab.tsx` + `ScheduledJobsList.tsx`: React only
- `apps/api/jobs/errors.py`: stdlib + internal apps.api.core.errors only

### Deferred (cj-303 scope 외)

- `slack-sdk==3.23.0` + `sendgrid==6.11.0`: `scheduled_executive_dispatch.py` docstring 에만 언급, 실제 import 없음. cj-300 의 stale docstring, post-pilot cleanup 결정 wire 보존

## §4 Fix Scope 결정 wire (4 files EXTENSION)

### cj-303 wire sprint 진입 시 적용

1. **`apps/api/pyproject.toml`** (line 78~closing bracket) — dependencies block EXTENSION:
   ```toml
   "apscheduler==3.10.4",
   "pytz==2024.1",
   ```
2. **`docs/STACK_PIN.yaml`** (line 49~51) — Backend section EXTENSION:
   ```yaml
   apscheduler: "3.10.4"
   pytz: "2024.1"
   ```
3. **`scripts/check_stack_pin.py`** (line 203-213) — hard-coded list EXTENSION:
   ```python
   ("apscheduler", "apscheduler"),
   ("pytz", "pytz"),
   ```
4. **`uv.lock`** — `uv lock` 자동 재생성

## §5 결정 wire 보존

- **OQ 결정 wire 4/4 apply 보존**: reportlab + Postmark + APScheduler + matplotlib (cj-301 그대로)
- **AD bind 4/4 active 보존**: AD-2 + AD-3 + AD-10 + AD-12
- **NFR bind 7/7 active 보존**: NFR4 + NFR5 + NFR7 + NFR8 + NFR12 + NFR18 + NFR19
- **capability matrix v1.54 EXTENSION preserved** (cj-285 EXTENSION 그대로, cj-303 신규 0건)
- **audit actions EXTENSION preserved** (cj-285 EXTENSION 그대로, cj-303 신규 0건)
- **AD-14 stack pin EXTENSION**: `[STACK BUMP]` tag 동반 (cj-300 의 claim 정직 회복)

## §6 runtime 동작 변화 (cj-303 entry 자체)

- docs-only atomic — 0 NEW source / 0 MODIFIED source / dev_seed 0 / ci.yml 0 / alembic 0
- 37 pins unchanged (cj-303 wire 시 EXTENSION 예정)
- 14 job matrix unchanged
- PRD §F/§M/§R unchanged / capability matrix v1.54 EXTENSION preserved / audit actions EXTENSION preserved

## §7 Risk Profile — **LOW**

| Rubric | Rating | 비고 |
|---|---|---|
| velocity | medium | docs entry + wire 합산 ~30min, 4-file EXTENSION |
| reversibility | highest | 1 git revert per sprint |
| production impact | none | uvicorn boot 회복 = PRE-EXISTING → normal state |
| external action | 0 | real email 0 / production deploy 0 / pilot 영향 0 |
| dependency | none | cj-300 wire 완료 후 dependency declaration 누락만 회복 |

## §8 carryover 회복 (cj-303 wire 후)

PRE-EXISTING honestly DEFER carryover 6건 중:
- **#5 smoke-e2e uvicorn boot** ✅ 회복
- **#6 web-e2e uvicorn boot** ✅ 회복 + Playwright step 활성화 → csv-export.spec.ts Case 2+3 verify gate 회복
- **#4 test-suite-measure pytz 부재 부분** 회복 (28 errors 중 pytz-related 0건)

잔여 5건 (test-architecture + lint-conventions + web-test + test-suite-measure 잔여 + smoke-e2e 의 source-side drift) 보존.

## §9 결정 보류 (운전자)

| # | Item | Provider |
|---|------|----------|
| ① | cj-303 wire sprint 실행 승인 | 사용자 |
| ② | cj-303 close-out retro sprint 실행 승인 | 사용자 |
| ③ | cj-300 stale docstring cleanup (slack-sdk + sendgrid) | 사용자 (post-pilot) |
| ④ | 잔여 carryover 5건 일괄 fix | 사용자 (별도 sprint) |

## §10 CR 11-3 honest-DEFER 248번째

```
cj-style chain (CR 11-3 honest-DEFER count):
cj-282 (220번째) → ... → cj-300 wire (244번째) → cj-301 pilot prep (245번째)
→ cj-302 docs (246번째) → cj-302 MINIMAL fix (247번째) → cj-303 entry (248번째)
```

종합 28 sprints 정직 회복 결정 wire 진입.

## §11 결정 wire 일자

2026-09-07 (KST) — cj-303 entry sprint 종료 시점.

## §12 Why / How to apply

**Why**: cj-302 MINIMAL fix effectiveness 가 uvicorn boot failure 로 인해 UNVERIFIED ⚠️ 보존. cj-300 wire 의 "already pinned" claim 의 부 정확성을 정직 회복하면서 AD-14 stack pin EXTENSION 으로 근본 fix.

**How to apply**:
- 다음 세션 시작 시: §결정 보류 4건 + carryover 회복 5건 확인
- 우선순위: cj-303 wire sprint 진입 (entry commit push 후)
- cj-303 wire 종료 후 close-out retro sprint 결정 wire 보존
- pilot W1 (2026-09-14 KST) 시작 전 회귀 검증 가능 상태 회복 목표

## Cross-References

- Plan file: `C:\Users\c8rom\.claude\plans\rippling-tumbling-wind.md`
- Root cause: `apps/api/jobs/scheduled_reports.py:54` + `apps/api/main.py:655`
- Stack pin: `docs/STACK_PIN.yaml` (Backend section EXTENSION 예정)
- Drift detector: `scripts/check_stack_pin.py` (hard-coded list EXTENSION 예정)
