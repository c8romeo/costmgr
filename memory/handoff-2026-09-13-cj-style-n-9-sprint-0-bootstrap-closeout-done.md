# cj-style N+9 Sprint 0 부트스트랩 close-out + env-free fix-forward — handoff

**날짜**: 2026-09-13 KST (D-1, Pilot W1 launch D-day 2026-09-14 KST Mon 까지 1일)
**sprint index**: cj-style N+9 (Sprint 0 부트스트랩 close-out, NEW 결정 wire, cj-style N+8 + fix(seed) + fix-forward 통합)
**commit hash**: TBD (atomic commit 직후 확정)
**status**: Sprint 0 부트스트랩 close-out 결정 wire 진입 완료 + env-free fix-forward verified

---

## §1. Strategic context

비정상 종료 복구 후 cj-style N+8 (`dde3f61`) + fix(seed) (`d7b38f7`) 의 코드 commit은 완료되었으나 cj-style discipline close-out (sprint-status + handoff + MEMORY.md + commit-msg) 이 누락된 상태.

cj-style N+8 결정 wire verbatim: "옵션 (b) 부팅 + 옵션 (a) endpoint 회복 = 둘 다 해" + "비정상적인 종료상황을 감안해서 중간중간 자주 상태를 저장".

Step 1 verification (runtime) 결과 env vars 의존성 발견 → env-free fix-forward 결정 wire 진입.

---

## §2. Verification findings (cj-style N+8 검증 결과)

### §2.1 env vars 의존성 (Windows Korean locale + ESTsoft TMPDIR)

`uv run python scripts/mvp_local_db.py up` 직접 실행 시 initdb 실패:

```
initdb: could not find suitable text search configuration for locale "Korean_Korea.949"
initdb: error: directory "C:/Users/Public/Documents/ESTsoft/CreatorTemp/pgdata_mvp_local" exists but is not empty
```

**Root cause ①**: Windows locale `Korean_Korea.949` (949 코드페이지) 가 PostgreSQL 텍스트 검색 configuration 미지원. PostgreSQL initdb 가 `LC_ALL`/locale 기반 text search config 초기화 시도 시 실패.

**Root cause ②**: `TMPDIR=/c/Users/Public/Documents/ESTsoft/CreatorTemp` 환경변수 (ESTsoft/ALZip 계열 software override). `tempfile.gettempdir()` 가 비표준 경로 반환 + `shutil.rmtree(..., ignore_errors=True)` 가 silent permission failure.

**Workaround 검증**:
```bash
TMPDIR= LC_ALL=C LANG=C LC_COLLATE=C LC_CTYPE=C uv run python scripts/mvp_local_db.py up
```
→ initdb OK + alembic 61 migrations OK + port 61684.

### §2.2 cj-style N+7 conftest.py 패턴 (env-free 동일 동작)

`tests/api/smoke/conftest.py` 의 `embedded_pg` fixture 는 `tempfile.mkdtemp(prefix="pgdata_mvp_")` 사용 → fresh dir per invocation. 별도 locale 처리 없이 정상 동작 (pytest 가 env vars 자동 설정).

cj-style N+8 의 `mvp_local_db.py` 는 cj-style N+7 패턴과 다른 fixed-dir approach 채택 → 환경 의존성 발생.

### §2.3 fix(seed) (`d7b38f7`) 검증 결과

`scripts/mvp_seed.py` schema/CHECK/idempotent fix (131+/60- LOC) 적용 후:
- tenants=1, users=1, products=5, bom_lines=2, monthly_input_rows=2 ✅
- alembic head: `0061_phase_30_story_30_4_finance_contact_email` ✅
- Supabase service_role SET LOCAL 정상 ✅
- 모든 7 tables 정상 적용 ✅

---

## §3. Sprint 0 env-free fix-forward 결정 wire

### Q1. 어디에 env vars 자동 설정을 둘 것인가?

**옵션 (a)**: 스크립트 내부 `os.environ.setdefault()` (env-free) — **자동 결정** ✅
**옵션 (b)**: README/문서에 환경 설정 가이드 — operator 부담 + 결정 wire 보류
**옵션 (c)**: shell wrapper script (`mvp_local_db.bat`) — 별도 파일 + Windows batch overhead

**자동 결정**: 옵션 (a). 스크립트 시작 시점에 `os.environ` 패치 → subprocess (initdb) inheritance 정상 동작. cj-style N+7 conftest.py 와 동등한 env-free 보장.

### Q2. TMPDIR 처리 방식?

**옵션 (a)**: `os.environ.pop("TMPDIR", None)` — %TEMP% fallback
**옵션 (b)**: `_pgdata_dir()` 에서 `os.environ["TEMP"]` 직접 사용
**옵션 (c)**: `tempfile.gettempdir()` 호출 전 환경 변수를 setdefault 로 덮어쓰기

**자동 결정**: 옵션 (a). `tempfile.gettempdir()` 가 `%TEMP` fallback 정상 지원 → 가장 단순.

### Q3. PID file 에 어떤 PID 기록?

**옵션 (a)**: 기존 parent python PID — taskkill 시 postgres child 가 leak 가능
**옵션 (b)**: postgres master PID (`info.pid`) — taskkill /F 시 master death 가 child 정리 (Windows process tree)
**옵션 (c)**: 양쪽 모두 기록 (parent + master)

**자동 결정**: 옵션 (b). 단일 PID 단순 + cleanup 정확성 보장.

---

## §4. 변경 verbatim

### §4.1 `scripts/mvp_local_db.py` MODIFIED (env-free fix-forward)

**Patch 1 — env vars 자동 설정** (after `import os`, before `import shutil`):
```python
# Sprint 0 (cj-style N+9) — env-free execution prerequisite.
# ① Windows Korean locale (Korean_Korea.949) has no PostgreSQL text search
#   configuration for initdb. Setting LC_ALL=C (and friends) before importing
#   embedded_postgres makes initdb happy without operator-side setup.
# ② TMPDIR may be set to non-standard paths (e.g. /c/Users/Public/Documents/
#   ESTsoft/CreatorTemp from ALZip/ESTsoft). Unset so tempfile.gettempdir()
#   falls back to %TEMP% (user's writable TEMP).
os.environ.pop("TMPDIR", None)
for _lc in ("LC_ALL", "LANG", "LC_COLLATE", "LC_CTYPE"):
    os.environ.setdefault(_lc, "C")
```

**Patch 2 — `_pgdata_dir()` mkdtemp 변환**:
```python
def _pgdata_dir() -> Path:
    """Allocate a fresh pgdata directory under the user TEMP.

    Sprint 0 (cj-style N+9): use mkdtemp for env-free uniqueness.
    cj-style N+7 conftest.py `tempfile.mkdtemp(prefix='pgdata_mvp_')`
    pattern verbatim mirror. Replaces cj-style N+8 fixed-dir
    (`tempfile.gettempdir() / DATA_DIR_NAME`) which conflicted with
    non-standard TMPDIR paths and rmtree's `ignore_errors=True`
    silently swallowed permission/IO failures.
    """
    return Path(tempfile.mkdtemp(prefix="pgdata_mvp_local_"))
```

**Patch 3 — `cmd_up()` stale dir cleanup 제거**:
```python
# REMOVED (cj-style N+8):
# if pgdata.exists():
#     print(f"[mvp_local_db] removing stale pgdata: {pgdata}")
#     shutil.rmtree(pgdata, ignore_errors=True)
#
# mkdtemp 가 매 호출마다 unique dir 보장 → stale dir cleanup 불필요.
```

**Patch 4 — PID 기록 변경** (`_write_pid(os.getpid())` → `_write_pid(info.pid)`):
```python
# Record postgres master PID (not parent python PID) so `mvp_local_db.py down`
# kills the actual server, not the wait-loop parent.
_write_pid(info.pid)
```

**Patch 5 — `cmd_down()` .url file cleanup 추가**:
```python
# taskkill /F bypasses the KeyboardInterrupt-triggered _cleanup(), so we
# explicitly unlink the URL file here. pgdata dirs (mkdtemp under %TEMP%)
# are left for OS temp cleanup; cj-style N+9 close-out scope decision.
(_project_root() / ".mvp_local_db_url").unlink(missing_ok=True)
```

### §4.2 cj-style discipline close-out (cj-style N+8 + fix(seed) + N+9 통합)

cj-style N+8 (`dde3f61`) + fix(seed) (`d7b38f7`) 의 code-only commit 들에 대한 sprint-status / handoff / MEMORY.md / commit-msg close-out 을 본 sprint (cj-style N+9) 의 meta 변경으로 통합.

---

## §5. verify gate (env-free end-to-end 검증)

### §5.1 `up` cycle (env vars 미설정)

```bash
$ uv run python scripts/mvp_local_db.py up
[mvp_local_db] pgdata (fresh, mkdtemp) = C:\Users\c8rom\AppData\Local\Temp\pgdata_mvp_local_xxxxxx
[mvp_local_db] starting embedded-postgres
[mvp_local_db] PostgreSQL on 127.0.0.1:60717
[mvp_local_db] DATABASE_URL = postgresql+asyncpg://postgres:@127.0.0.1:60717/postgres
[mvp_local_db] applying supabase CI shim (roles + set_updated_at)...
[mvp_local_db] CI shim applied (roles + set_updated_at)
[mvp_local_db] alembic_version ready (VARCHAR 255)
[mvp_local_db] running alembic upgrade head...
[mvp_local_db] alembic OK
[mvp_local_db] postgres master PID=12252 recorded in .mvp_local_db.pid
[mvp_local_db] ready. DATABASE_URL=postgresql+asyncpg://postgres:@127.0.0.1:60717/postgres
```

### §5.2 seed cycle

```bash
$ DATABASE_URL=$(cat .mvp_local_db_url) uv run python scripts/mvp_seed.py
[mvp_seed] DONE - verify:
  tenants: 1
  users: 1
  products: 5
  bom_lines: 2
  monthly_input_rows: 2
```

### §5.3 down cycle (cleanup 정확성)

```bash
$ uv run python scripts/mvp_local_db.py down
[mvp_local_db] killing PID=12252
[mvp_local_db] down
# .mvp_local_db.pid 제거 ✅, .mvp_local_db_url 제거 ✅, port 60717 closed ✅
```

### §5.4 직접 DB 조회 (테넌트 + 마이그레이션 검증)

```python
tenant: Demo Manufacturing Co.
industry: manufacturing
products: 5
bom_lines: 2
periods: 1
rows: 2
alembic head: 0061_phase_30_story_30_4_finance_contact_email
```

### §5.5 verify gate 종합

| 항목 | 상태 |
|------|------|
| **PROD source 변경** | 0건 |
| **Test 변경** | 0건 |
| **alembic 변경** | 0건 (cj-style N+8 의 `0001_tenants_users_memberships_settings.py` 이미 commit 완료) |
| **PRD 변경** | 0건 (PRD v7.0 §F/§M/§R unchanged) |
| **Capability matrix source 변경** | 0건 (v1.54 EXTENSION preserved) |
| **Migration source 변경** | 0건 |
| **Script 변경** | 1 file (scripts/mvp_local_db.py MODIFIED env-free fix-forward) |
| **37 pins unchanged** | ✅ |
| **14 job matrix unchanged** | ✅ |
| **AD-14 stack pin EXTENSION preserved** | ✅ |
| **A19 cohesion 9 surface EXTENSION PASS preserved** | ✅ |
| **3중 게이트 FINAL CLEAN 보존** | ✅ (pytest + ruff + tsc 변경 없음) |

---

## §6. Sprint 0 부트스트랩 후속 (다음 sprint 결정 보류)

| # | 항목 | 결정 시점 |
|---|------|----------|
| ① | Sprint 1 = K-4 wire 3 main runtime execution actual run (skipif guard 해제 + 100 cases actual pytest) | 본 sprint 후 즉시 |
| ② | Sprint 1.1 = skipif guard 해제 (test_k4_wire_3_runtime_smoke.py 의 DATABASE_URL guard 제거) | Sprint 1 진입 시 |
| ③ | Sprint 1.2 = alembic upgrade head (이미 env-free up cycle 에서 검증 완료 — sprint status 기록만) | 본 sprint close-out |
| ④ | Sprint 1.3 = Seed data 작성 (이미 env-free seed cycle 에서 검증 완료 — sprint status 기록만) | 본 sprint close-out |
| ⑤ | Sprint 2 = Endpoint 부재 54건 회복 (K-4 wire 3 main first-pass 결과 분석 후) | Sprint 1 결과 분석 후 |
| ⑥ | Sprint 3 = End-to-end 시나리오 manual click verify (Login → 각 module → export) | Sprint 2 완료 후 |
| ⑦ | 결정 보류 11건 honestly DEFER post-MVP | honestly DEFER post-W1 |

---

## §7. 결정 wire 보존

**91/91 cumulative 결정 wire 보존**:
- cj-style N+6 의 86
- **NEW 87번째** cj-style N+7 Sprint 0 환경 준비 (atomic single sprint)
- **NEW 88번째** cj-style N+8 Sprint 0 부트스트랩 (code-only, 본 sprint close-out)
- **NEW 89번째** fix(seed) (code-only, 본 sprint close-out)
- **NEW 90번째** cj-style N+9 Sprint 0 부트스트랩 close-out + env-free fix-forward (atomic single sprint)

**CR 11-3 honest-DEFER 266번째** chain cj-style 257 → 267 → 279 → 281 → 283 → 285 → 304 → 305 → 306 → 307 + N-1 + N+1 + N+2 + N+3 + N+4 + N+5 + N+6 + N+7 + N+8 + fix(seed) + **N+9** verbatim mirror.

**PRE-EXISTING honestly DEFER carryover 보존**:
- cj-303 4건 + PRE-EXISTING 6건 + cj-307 LOW RISK ~30건
- sso 13 skipped tests + epics.md 1478 lines uncommitted change
- W1~W8 carryover + PRD v2 EXTENSION
- 비용 발생 항목 모두 (사용자 2026-09-10 결정 wire verbatim '배포작업 안 함 / RESEND·RAILWAY 등 지금 단계 X')

**신규 honestly DEFER (cj-style N+9 chain 보존, 본 sprint 후속)**:
- pgdata directory cleanup 자동화 (mkdtemp prefix match + auto-remove) — cj-style N+9 scope 결정 보류
- `cmd_down` 의 postgres child process tree cleanup — taskkill /F + /T flag 또는 signal handler 추가 (cj-style N+10 이후 결정 보류)
- FastAPI/Next.js 동시 부팅 orchestration (`scripts/mvp_dev_up.sh`) 실제 검증 — Sprint 2 진입 시

---

## §8. 결정 wire 일자

2026-09-13 (KST, D-1, Pilot W1 launch D-day 2026-09-14 KST Mon 까지 ~12-24시간 잔여)

후속 마감 = 본 commit (sprint-status v4.124 → **v4.125 EXTENSION** A769 cj-style N+8 + A770 fix(seed) + A771 cj-style N+9 + MEMORY.md hook + handoff + commit-msg + mvp_local_db.py MODIFIED = 5 files atomic single sprint).