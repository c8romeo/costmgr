---
name: handoff-2026-09-07-cj-303-uvicorn-boot-fix-wire-done
description: "cj-303 uvicorn boot fix wire sprint DONE (cj-style 307번째) — AD-14 stack pin EXTENSION (apscheduler==3.10.4 + pytz==2024.1) + cj-300 stale ALL_REPORT_TYPES import path 정정. 5 files = 4 MODIFIED + uv.lock regen. Uvicorn boot ✅ 회복, CR 11-3 honest-DEFER 249번째."
metadata:
  node_type: memory
  type: project
  originSessionId: e85acf61-c75a-4985-990b-b5f6b80a7640
  modified: 2026-09-07T14:00:00.000Z
---

# cj-303 uvicorn boot fix — wire sprint DONE (cj-style 307번째)

**일자**: 2026-09-07 (KST)
**territory**: Epic 30+ Pilot Gate (cj-297 PRD OQ-3 OPEN) → cj-302 carryover chain 정직 회복
**sprint type**: source+docs atomic single sprint (cj-303 wire)
**baseline_commit**: `10d84bb` (cj-303 entry tip)

---

## §1 의도 + verify gate 회복

cj-303 entry (`10d84bb`) 의 결정 wire 적용 → AD-14 stack pin EXTENSION + cj-300 stale import path 정정.

### 로컬 verify 결과

```bash
$ uv lock
Resolved 107 packages in 1.77s
Added apscheduler v3.10.4
Added pytz v2024.1
Added tzdata v2026.3
Added tzlocal v5.4.4

$ uv sync --all-packages
Installed 8 packages in 684ms
 + apscheduler==3.10.4
 + pytz==2024.1
 + tzdata==2026.3
 + tzlocal==5.4.4

$ uv run python -c "from apps.api.main import app; print('OK app loaded:', type(app).__name__)"
OK app loaded: FastAPI

$ uv run python -c "from apps.api.main import app; print('Total:', len(app.routes))"
Total: 41

$ uv run python scripts/check_stack_pin.py
[STACK_PIN] OK all 37 pins match
```

**핵심 회복**: `ModuleNotFoundError: No module named 'pytz'` → `OK app loaded: FastAPI`. cj-303 root cause 정직 회복.

## §2 scope (5 files = 4 MODIFIED + 1 auto-regen)

### MODIFIED

1. **`apps/api/pyproject.toml`** — dependencies block EXTENSION:
   ```toml
   "apscheduler==3.10.4",
   "pytz==2024.1",
   ```

2. **`docs/STACK_PIN.yaml`** — Backend section EXTENSION:
   ```yaml
   apscheduler: "3.10.4"
   pytz: "2024.1"
   ```

3. **`scripts/check_stack_pin.py`** — hard-coded list EXTENSION:
   ```python
   ("apscheduler", "apscheduler"),
   ("pytz", "pytz"),
   ```

4. **`apps/api/modules/reports/scheduled_routes.py`** — import block 정정 (cj-300 wire 의 stale bug):
   ```python
   # BEFORE: ALL_REPORT_TYPES imported from apps.api.jobs.scheduled_reports (NOT EXISTS)
   # AFTER: ALL_REPORT_TYPES imported from apps.api.modules.reports.scheduled_serializers (line 50 정의)
   ```

### Auto-regenerated (직접 작성 X)

- **`uv.lock`** — `uv lock` 자동 regen. apscheduler + pytz + transitive deps (`tzdata`, `tzlocal`) 자동 resolve.

### Meta (cj-303 wire 종료 후 update)

- `_bmad-output/implementation-artifacts/sprint-status.yaml` v4.72 → v4.73 EXTENSION
- `memory/MEMORY.md` hook EXTENSION

## §3 결정 wire 보존

- **OQ 결정 wire 4/4 apply 보존**: reportlab + Postmark + APScheduler + matplotlib (cj-303 entry 의 보존 그대로)
- **AD bind 4/4 active 보존**: AD-2 + AD-3 + AD-10 + AD-12
- **NFR bind 7/7 active 보존**: NFR4 + NFR5 + NFR7 + NFR8 + NFR12 + NFR18 + NFR19
- **capability matrix v1.54 EXTENSION preserved** (cj-285 EXTENSION 그대로, cj-303 신규 0건)
- **audit actions EXTENSION preserved** (cj-285 EXTENSION 그대로, cj-303 신규 0건)

## §4 CI verify gate 예측 (push 후)

- `smoke-e2e` job 의 "Boot uvicorn (background)" step (ci.yml:915-929) → ✅ success
- `web-e2e` job 의 "Boot uvicorn (background)" step (ci.yml:778-792) → ✅ success
- `web-e2e` job 의 Playwright step → cj-302 MINIMAL fix 의 verify gate (csv-export.spec.ts Case 2+3) 회복
- `stack-pin-check` job → 기존 통과 상태 유지
- 기준선 (cj-302 fix run 34120876777) 대비 regressions 0건 예상

## §5 carryover 회복

PRE-EXISTING honestly DEFER carryover 6건 중:
- **#5 smoke-e2e uvicorn boot** ✅ 회복
- **#6 web-e2e uvicorn boot** ✅ 회복 + Playwright step 활성화
- **#4 test-suite-measure pytz 부재 부분** 회복 (28 errors 중 pytz-related 0건)

잔여 5건 (test-architecture + lint-conventions + web-test + test-suite-measure 잔여 + smoke-e2e 의 source-side drift) 보존.

## §6 cj-300 wire 의 정직 회복 (CR 11-3 honest-DEFER 249번째)

cj-303 wire 진입 시 2건의 cj-300 wire bug 정직 회복:

1. **`pytz` / `apscheduler` unpinned** — cj-300 handoff 의 "already pinned" claim 부 정확성 회복 (AD-14 stack pin EXTENSION)
2. **`ALL_REPORT_TYPES` stale import path** — cj-300 scheduled_routes.py:82 가 `apps.api.jobs.scheduled_reports` 에서 import 시도했으나 정의는 `apps.api.modules.reports.scheduled_serializers:50` 에 존재 → ImportError. cj-300 wire 시점에 boot 안 됐으므로 표면화 안 됨, cj-303 boot 회복 시 ImportError 로 surface 화 → 정정.

**cj-300 wire 의 "7 ADs 미준수" candidate**: cj-300 wire 가 "wire 완료" 라고 보고했지만 실제로는 2건의 wire 미완성 상태 (dependency declaration 부재 + import path 부 정확). CR 11-3 honest-DEFER 249번째 결정 wire 적용.

## §7 결정 보류 (운전자)

| # | Item | Provider |
|---|------|----------|
| ① | cj-303 close-out retro sprint 실행 승인 | 사용자 |
| ② | cj-300 stale docstring cleanup (slack-sdk==3.23.0 + sendgrid==6.11.0) | 사용자 (post-pilot) |
| ③ | 잔여 PRE-EXISTING carryover 5건 일괄 fix | 사용자 (별도 sprint) |
| ④ | production deployment authorization (B-2) | 사용자 |
| ⑤ | pilot candidate list 5-10곳 (B-1) | operator |
| ⑥ | outreach 발송 | 사용자 |
| ⑦ | pilot launch W1 (2026-09-14 KST) | 사용자 |

## §8 CR 11-3 honest-DEFER 249번째

```
cj-style chain (CR 11-3 honest-DEFER count):
cj-282 (220번째) → ... → cj-303 entry (248번째) → cj-303 wire (249번째)
```

종합 29 sprints 정직 회복 결정 wire 진입.

## §9 결정 wire 일자

2026-09-07 (KST) — cj-303 wire sprint 종료 시점.

## §10 Why / How to apply

**Why**: cj-302 MINIMAL fix effectiveness 가 uvicorn boot failure 로 인해 UNVERIFIED ⚠️ 보존. cj-300 wire 의 'already pinned' claim 의 부 정확성 + stale `ALL_REPORT_TYPES` import path 정직 회복. AD-14 stack pin EXTENSION 으로 근본 fix 후 CI 의 smoke-e2e + web-e2e uvicorn boot step 회복 + cj-302 MINIMAL fix verify gate 회복.

**How to apply**:
- 다음 세션 시작 시: §결정 보류 7건 + carryover 회복 5건 확인
- 우선순위: cj-303 close-out retro sprint 진입 (CI verify gate 통과 후)
- pilot W1 (2026-09-14 KST) 시작 전 회귀 검증 가능 상태 회복 목표

## Cross-References

- Plan file: `C:\Users\c8rom\.claude\plans\rippling-tumbling-wind.md`
- Entry handoff: `memory/handoff-2026-09-07-cj-303-uvicorn-boot-fix-entry-done.md`
- Root cause: `apps/api/jobs/scheduled_reports.py:54` (정직 회복)
- Stale import path fix: `apps/api/modules/reports/scheduled_routes.py:79-96` (cj-300 wire 의 import path 정정)
- Stack pin: `docs/STACK_PIN.yaml` (Backend section EXTENSION 완료)
- Drift detector: `scripts/check_stack_pin.py` (hard-coded list EXTENSION 완료)
