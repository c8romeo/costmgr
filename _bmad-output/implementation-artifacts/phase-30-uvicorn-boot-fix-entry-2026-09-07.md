# cj-303 uvicorn boot fix — entry decision wire (cj-style 306번째)

**일자**: 2026-09-07 (KST)
**territory**: Epic 30+ Pilot Gate (cj-297 PRD OQ-3 OPEN) → cj-302 carryover chain 정직 회복 (uvicorn boot PRE-EXISTING failure)
**sprint type**: docs-only atomic single sprint (cj-303 entry)
**baseline_commit**: `3305b36` (cj-302 MINIMAL fix tip)

---

## §1 의도 분석

cj-302 fix sprint 의 CI run 34120876777 결과 = 8/14 ✅ + 6/14 ❌. ZERO regressions vs cj-301 baseline (run 34117397393) — 6 failures ALL PRE-EXISTING honestly DEFER carryover. 그러나 그 중 1건이 **uvicorn boot failure** (smoke-e2e + web-e2e 양쪽) — cj-302 MINIMAL fix 의 verify gate (web-e2e csv-export.spec.ts Case 2+3) 를 차단. 즉, **MINIMAL fix effectiveness = UNVERIFIED ⚠️** 보존.

운전자 옵션 (a) "uvicorn boot fix 진행" 승인 → cj-303 sprint 진입.

cj-303 의 단일 목적 = **uvicorn boot failure 의 root cause 를 정확히 식별 + fix scope 를 결정 wire 으로 명문화** (source code 변경 없음, docs-only). 실제 source 변경은 cj-303 wire sprint (cj-style 307번째) 에서 결정 wire 적용.

---

## §2 Root Cause 분석

### 재현 (로컬 Windows, uv 0.11.32)

```bash
$ cd C:/Users/c8rom/desktop/a/costmgr
$ uv run python -c "from apps.api.main import app; print('OK')"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
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

### 왜 unpinned 상태가 됐나

cj-300 wire sprint handoff (handoff-2026-09-07-cj-300-wire-done.md) 에서 다음과 같이 주장:

> "AD-14 stack pin — apscheduler==3.10.4 + pytz==2024.1 (already pinned, [STACK BUMP] tag 불필요)"

**그러나 실제 grep 결과**:

| 위치 | apscheduler | pytz |
|---|---|---|
| `apps/api/pyproject.toml` (line 14-79) | ❌ 부재 | ❌ 부재 |
| root `pyproject.toml` | ❌ 부재 | ❌ 부재 |
| `uv.lock` (1559 lines) | ❌ 0 matches | ❌ 0 matches |
| `docs/STACK_PIN.yaml` | ❌ 부재 | ❌ 부재 |

**cj-300 의 claim 은 부 정확** — declaration 없이 wire 만 작성. CR 11-3 honest-DEFER 248번째 결정 wire 적용 — cj-303 에서 정직 회복.

---

## §3 영향 범위 (Explore agent 검증 완료)

### Critical (cj-303 fix 대상)

| Package | Version | Usage sites |
|---|---|---|
| **`pytz`** | 2024.1 | **7 files top-level `import pytz`** (module load 시 실행): `scheduled_reports.py:54` (cj-303 root cause) + `scheduled_executive_dispatch.py:38` + `scheduled_unit_economics_calculation_job.py:41` + `scheduled_multi_cloud_dispatch_job.py:42` + `scheduled_commitment_dispatch.py:39` + `scheduled_chargeback_settlement_dispatch_job.py:40` + `executive_report_delivery.py:32`. `pytz.timezone("Asia/Seoul")` module-level 상수가 `scheduled_reports.py:72` 에서 평가됨 |
| **`apscheduler`** | 3.10.4 | **14 files `from apscheduler.triggers.cron import CronTrigger`** (lazy in `_validate_cron_expression`) + 6 files scheduler variants (`AsyncIOScheduler`/`BackgroundScheduler`). `_validate_cron_expression` → `schedule_report` → `scheduled_routes.py:195` 호출 chain 으로 trigger |

### ✅ Verified clean (cj-303 fix scope 외 — fix 시 영향 없음)

- `email_routes.py` / `scheduled_routes.py`: fastapi==0.139.2 + sqlalchemy==2.0.36 + internal modules 만 import
- `email_service.py` / `email_provider.py`: stdlib `smtplib` + pinned `httpx==0.27.0` (Postmark raw HTTP API). **Postmark SDK 미사용** — cj-299 의 "Postmark 결정 wire" 가 raw HTTP 라 SDK pin 불필요
- `apps/api/main.py:619-700` (cj-299/300 added region): 모든 declared import 가 traceable
- `alembic/versions/0061`: alembic==1.18.5 + sqlalchemy==2.0.36 only
- `EmailExportTab.tsx` + `ScheduledJobsList.tsx`: React only
- `apps/api/jobs/errors.py`: stdlib + internal apps.api.core.errors only

### Deferred (cj-303 fix scope 외)

- `slack-sdk==3.23.0` + `sendgrid==6.11.0`: `scheduled_executive_dispatch.py` docstring 에만 언급, **실제 import 없음** (lazy/optional). cj-300 의 stale docstring, post-pilot cleanup 결정 wire 보존

---

## §4 Fix Scope 결정 wire

### 4 files EXTENSION (cj-303 wire sprint 진입 시 적용)

1. **`apps/api/pyproject.toml`** — dependencies block EXTENSION (after line 78, before closing `]`):
   ```toml
   # cj-303 wire sprint (cj-style 307번째 wire) — AD-14 stack pin EXTENSION.
   # 결정 wire: pytz + apscheduler — apps/api/jobs/scheduled_reports.py:54 의
   # top-level `import pytz` 가 uvicorn boot 시 transitive crash 유발
   # (cj-300 wire 의 "already pinned" claim 은 부 정확 — 정직 회복).
   # cj-300 docstring 의 11 precedent scheduled_*.py files + 14 apscheduler.*
   # files 모두 동일 deps 사용. [STACK BUMP] tag 동반 (신규 pin EXTENSION).
   "apscheduler==3.10.4",
   "pytz==2024.1",
   ```

2. **`docs/STACK_PIN.yaml`** — `stack_pin:` Backend section EXTENSION (after line 49 `httpx: "0.27.0"`, before line 51 optional/transitive section):
   ```yaml
   # cj-303 wire sprint — AD-14 stack pin EXTENSION.
   apscheduler: "3.10.4"
   pytz: "2024.1"
   ```

3. **`scripts/check_stack_pin.py`** — line 203-213 의 hard-coded package list EXTENSION:
   ```python
   for pkg, pin_key in [
       ("sqlalchemy", "sqlalchemy"),
       ("alembic", "alembic"),
       ("asyncpg", "asyncpg"),
       ("pyjwt", "pyjwt"),
       ("supabase", "supabase"),
       ("pydantic-settings", "pydantic_settings"),
       ("fastapi", "fastapi"),
       ("uvicorn", "uvicorn"),
       ("httpx", "httpx"),
       # cj-303 wire sprint — AD-14 stack pin EXTENSION:
       ("apscheduler", "apscheduler"),
       ("pytz", "pytz"),
   ]:
   ```

4. **`uv.lock`** — `uv lock` 으로 자동 재생성. apscheduler + pytz + transitive deps (`six`, `python-dateutil`, `tzlocal`, `tzdata` 등) 자동 resolve.

### 결정 wire 보존

- **OQ 결정 wire 4/4 apply 보존**: OQ-EPIC30+-1 reportlab + OQ-EPIC30+-2 Postmark + OQ-EPIC30+-3 APScheduler + OQ-EPIC30+-4 matplotlib (cj-301 의 보존 그대로)
- **AD bind 4/4 active 보존**: AD-2 + AD-3 + AD-10 + AD-12 (cj-301 의 보존 그대로)
- **NFR bind 7/7 active 보존**: NFR4 + NFR5 + NFR7 + NFR8 + NFR12 + NFR18 + NFR19 (cj-301 의 보존 그대로)
- **capability matrix v1.54 EXTENSION preserved** (cj-285 EXTENSION 그대로, cj-303 신규 EXTENSION 0건)
- **audit actions EXTENSION preserved** (cj-285 EXTENSION 그대로, cj-303 신규 EXTENSION 0건)
- **AD-14 stack pin EXTENSION**: `[STACK BUMP]` tag 동반 — CR 2026-07-25 PIN-1 정책 준수 (cj-300 wire 의 claim "no [STACK BUMP] tag 불필요" 부 정확 → 정직 회복)

### runtime 동작 변화 (cj-303 entry 자체)

- docs-only atomic single sprint — 0 NEW source / 0 MODIFIED source
- alembic graph 보존 (0061 revision 무변경)
- ci.yml 무변경
- runtime API surface 무변경 (router endpoint 무변경)
- 단, fix 적용 후 (cj-303 wire): pytz + apscheduler 가 `uv sync --frozen --all-packages` 로 install 가능 → uvicorn boot ✅ 회복

### 결정 wire 일자

2026-09-07 (KST) — cj-303 entry sprint 종료 시점.

---

## §5 Risk Profile

### Risk categorization (사용자 5-rubric: velocity / reversibility / production impact / external action / dependency)

| Rubric | Rating | 비고 |
|---|---|---|
| **velocity** | **medium** | docs-only entry + source wire 합산 ~30min — bounded 4-file EXTENSION |
| **reversibility** | **highest** | 1 git revert per sprint (cj-303 entry → cj-303 wire) |
| **production impact** | **none** | runtime API surface 무변경, uvicorn boot 회복 = PRE-EXISTING state → normal state |
| **external action** | **0** | real email 0 / production deploy 0 / pilot launch 영향 0 |
| **dependency** | **none** | cj-300 wire 와 무관 (cj-300 의 wire 자체는 완료, 본 fix 는 dependency declaration 누락만 회복) |

### Overall risk: **LOW**

**Rationale**:
- 단 4 files EXTENSION (pyproject.toml + STACK_PIN.yaml + check_stack_pin.py + uv.lock)
- 0 NEW source code (apps/api/*.py 무변경)
- 0 MODIFIED source code (apps/api/*.py 무변경)
- alembic graph 보존 (0061 revision 무변경)
- ci.yml 무변경
- runtime API surface 무변경
- capability matrix v1.54 + audit actions EXTENSION preserved
- 기존 dev/CI 환경에서 `uv lock --frozen` 사용처는 그대로 작동 (lockfile regen 후 동일 hash 보존)
- Regression risk 0건 예상 (cj-300 wire 의 scheduled_reports.py 가 boot 안 됐을 뿐, runtime API 는 wire 완료 상태 그대로)

### Migration safety

기존 uv lockfile 사용자 (`uv sync --frozen`) 는 본 fix 후 `uv lock` regen 한 번 실행 필요 → 이후 동일 hash 보장. CI 의 `uv sync --frozen --all-packages` step 은 변경 없음 (ci.yml line 528 rls-tests, 705 web-e2e, 873 smoke-e2e, 329 test-architecture, 376 test-suite-measure, 441 test-service-role-guard — 모두 `--frozen --all-packages` 패턴 일관, pyproject.toml 변경 후 자동 lockfile 변경 흡수).

---

## §6 검증 계획 (cj-303 wire sprint 진입 시)

### Step 1: 로컬 reproduce

```bash
# Before fix (cj-303 entry 시점, 이미 검증됨):
uv run python -c "from apps.api.main import app"
# → ModuleNotFoundError: No module named 'pytz'

# After fix (cj-303 wire):
uv lock
uv run python -c "from apps.api.main import app; print('OK', app)"
# → OK <fastapi.applications.FastAPI object>
```

### Step 2: check_stack_pin.py 로컬 verify

```bash
uv run python scripts/check_stack_pin.py
# → exit 0, 두 패키지 drift 0건
```

### Step 3: stack-pin-check CI job verify

- `stack-pin-check` job 의 Python pin check step (ci.yml:195-205) 이 exit 0 인지 확인
- 기존 통과 상태 (cj-302 baseline 동일) 유지 — 추가 drift 없음

### Step 4: smoke-e2e + web-e2e CI verify gate (cj-303 의 핵심)

- `smoke-e2e` job 의 "Boot uvicorn (background)" step (ci.yml:915-929) → ✅ success
- `web-e2e` job 의 "Boot uvicorn (background)" step (ci.yml:778-792) → ✅ success
- `web-e2e` job 의 Playwright step (cj-302 의 MINIMAL fix 가 적용된 csv-export.spec.ts Case 2+3) → ✅ pass (cj-302 MINIMAL fix 의 verify gate 회복)
- 기준선 (cj-302 fix run 34120876777) 대비 regressions 0건 확인

### Step 5: [STACK BUMP] tag 적용 검증

- Commit message 첫 줄에 `[STACK BUMP]` tag 포함 → check_stack_pin.py 가 bump_ok=True 로 인식 → drift 있더라도 pass

---

## §7 carryover 회복 (cj-302 → cj-303)

PRE-EXISTING honestly DEFER carryover 6건 중 **#6 (uvicorn boot failure)** 가 cj-303 wire 후 ✅ 회복.

**cj-303 wire 후 잔여 carryover (5건)**:

| # | Job | Failure | Verdict | cj-303 fix 후 상태 |
|---|-----|---------|---------|------------------|
| ① | test-architecture | workspace sync / collect error | PRE-EXISTING | 보존 |
| ② | lint-conventions | money-type linter / AD-8 AD-15 violation | PRE-EXISTING | 보존 |
| ③ | web-test | vitest 0/0 skip | PRE-EXISTING | 보존 |
| ④ | test-suite-measure | 45 failed / 28 errors (Phase 5·8·9·10·26 + pytz 부재) | PRE-EXISTING | **pytz 부재 부분 회복** (cj-303 wire 시) — 28 errors 중 pytz-related collection errors 0건 확인 |
| ⑤ | smoke-e2e | uvicorn boot failure | PRE-EXISTING | **✅ 회복** (cj-303 wire 시) |
| ⑥ | web-e2e | uvicorn boot failure | PRE-EXISTING | **✅ 회복** (cj-303 wire 시) + Playwright step 활성화 → csv-export.spec.ts Case 2+3 verify gate 회복 |

---

## §8 결정 보류 (운전자)

| # | Item | Provider | 비고 |
|---|------|----------|------|
| ① | cj-303 entry sprint 실행 승인 | 사용자 | 본 sprint 자체 |
| ② | cj-303 wire sprint 실행 승인 | 사용자 | entry commit push 후 |
| ③ | cj-303 close-out retro sprint 실행 승인 | 사용자 | wire CI verify gate 통과 후 |
| ④ | cj-300 의 stale docstring cleanup (`slack-sdk==3.23.0` + `sendgrid==6.11.0`) | 사용자 | cj-303 scope 외, post-pilot 결정 wire 보존 |
| ⑤ | 잔여 PRE-EXISTING carryover 5건 일괄 fix (test-architecture + lint-conventions + web-test + test-suite-measure 잔여 + smoke-e2e 의 source-side drift) | 사용자 | cj-303 외 별도 sprint 결정 wire 보존 |

---

## §9 CR 11-3 honest-DEFER 248번째

본 cj-303 entry sprint 의 결정 wire 가 **CR 11-3 honest-DEFER 카운트의 248번째**. cj-300 wire 의 "AD-14 stack pin apscheduler==3.10.4 + pytz==2024.1 already pinned, [STACK BUMP] tag 불필요" claim 의 부 정확성을 정직 회복.

```
cj-style history chain (CR 11-3 honest-DEFER count):
...
cj-282 (220번째) → cj-282a (221~223번째) → cj-285 (223번째) → cj-286 (223번째)
→ cj-287 (224번째) → cj-288 (225번째) → cj-289 (226번째) → cj-290 (227번째)
→ cj-291 (228번째) → cj-292 (229~232번째 cycle) → cj-293 (233번째)
→ cj-294 (234번째) → cj-295 (235번째) → cj-296 (236번째) → cj-297 (237번째)
→ cj-298 (238번째) → cj-299 (239번째) → cj-299fix take-1 (240번째)
→ cj-299fix take-2 (241번째) → cj-299retro (242번째) → cj-300 entry (243번째)
→ cj-300 wire (244번째) → cj-301 pilot prep (245번째) → cj-302 docs (246번째)
→ cj-302 MINIMAL fix (247번째) → **cj-303 entry (248번째)**
```

종합 28 sprints 정직 회복 결정 wire 진입.

---

## §10 Cross-References

- Plan file: `C:\Users\c8rom\.claude\plans\rippling-tumbling-wind.md`
- cj-300 wire handoff: `memory/handoff-2026-09-07-cj-300-wire-done.md`
- cj-301 pilot prep handoff: `memory/handoff-2026-09-07-cj-301-pilot-prep-done.md`
- cj-302 exec + MINIMAL fix handoff: `memory/handoff-2026-09-07-cj-302-exec-and-minimal-fix-done.md`
- Root cause file: `apps/api/jobs/scheduled_reports.py:54` (top-level `import pytz`)
- Transitive trigger: `apps/api/main.py:655` (`from apps.api.modules.reports.scheduled_routes import ...`)
- Stack pin source of truth: `docs/STACK_PIN.yaml` (Backend section EXTENSION 예정)
- Drift detector: `scripts/check_stack_pin.py` (hard-coded list EXTENSION 예정)

---

**결정 wire 일자**: 2026-09-07 (KST)
**cj-style 306번째** | **CR 11-3 honest-DEFER 248번째** | **26/26 cumulative 결정 wire 보존**
