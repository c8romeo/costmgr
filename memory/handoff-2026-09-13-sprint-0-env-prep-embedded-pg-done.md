# Sprint 0 환경 준비 (embedded-postgres 18.6.3) — handoff

**날짜**: 2026-09-13 KST (D-1, Pilot W1 launch D-day 2026-09-14 KST Mon 까지 1일)
**sprint index**: cj-style N+7 (Sprint 0 환경 준비, NEW 결정 wire)
**commit hash**: TBD (atomic commit 직후 확정)
**status**: Sprint 0 환경 준비 결정 wire 진입 완료

---

## §1. Strategic context

사용자 2026-09-13 결정 wire verbatim mirror: "내가 얻고자 하는 최종 결과물이 무엇인지를 다시 한 번 고민해보고, 설계된 내용을 시스템으로 구현하는 과정에서 리스크를 최소화하면서 전체적인 프로세스 설계의 관점에서 최적의 대안이 무엇인지를 분석해본 후 나의 목적을 달성해줄 수 있는 가장 합리적이고 효과적인 것부터 실행해줘."

cj-style N+5 (K-4 MVP readiness 정직 평가 분석 보고서) 의 결정 보류 11건 중:

> ① **K-4 wire 3 main runtime execution** — 본 sprint 의 ~100 cases 의 runtime execution 결과 의존 (option β first-pass). operator 환경 (TestClient + minimal mock + host venv activation) 준비 후 actual pytest execution

이 결정 보류 ① 의 환경 의존성을 해결하기 위한 Sprint 0 환경 준비.

사용자 결정 wire (2026-09-10) 의 분리: "배포작업 안 함 / RESEND·RAILWAY 등 지금 단계 X / 확실한 MVP 기능 갖춘 검증 대상 제품에 집중"

Sprint 0 = "확실한 MVP 기능 갖춘 검증 대상 제품" 의 첫 단계 = **로컬 환경에서 검증 가능한 PostgreSQL 환경 준비**.

---

## §2. Q1 환경 결정 분석

### 옵션 (a) Docker Desktop PostgreSQL 이미지
- Docker Desktop 미설치 (`docker: command not found`) → 설치 ~10-20분 필요
- Production 100% 동일, lifecycle 단순

### 옵션 (b) Windows native PostgreSQL install
- PostgreSQL native 미설치 (`psql: command not found`) → 설치 ~15-30분 필요
- Production 100% 동일, 가장 빠른 startup

### 옵션 (c) SQLite fallback (in-memory)
- ❌ RLS 미지원, JSONB 미지원, GIN 인덱스 미지원
- ❌ alembic migration 부분 호환
- ❌ 본질적으로 다른 환경 — verification 흉내 수준

### 옵션 (d-1) embedded-postgres 자동 다운로드
- ✅ `uv pip install embedded-postgres==18.6.3` (17.5MB 자동 다운로드, ~4초)
- ✅ PostgreSQL 18.6 production 100% parity
- ✅ RLS / JSONB / UUID (gen_random_uuid built-in) / GIN 모두 정상
- ✅ lifecycle 자동 관리 (pytest session scope)
- ✅ 즉시 사용 가능 (Docker / native install 불필요)

**결정**: 옵션 (d-1) — 사용 가능성 + 즉시 setup + production parity 모두 충족

---

## §3. Sprint 0 환경 준비 결정 wire

### Q1 자동 결정: 옵션 (d-1) embedded-postgres 18.6.3
- uv pip install 로 즉시 설치 (~1초)
- PostgreSQL 18.6 binary 자동 다운로드 (17.5MB, ~4초)
- ephemeral instance 자동 생성 + 자동 정리
- DATABASE_URL 환경 변수 자동 설정
- K-4 wire 3 main 의 skipif guard 우회

### Q2 자동 결정: 옵션 (b) Realistic (시연 가능한 수준)
- 결정 보류 — Sprint 0 은 환경 준비만, Seed data 작성은 Sprint 1 의 일부로 진입

### Q3 자동 결정: 옵션 (b) Deeper flow (시연 가능한 수준)
- 결정 보류 — Sprint 0 은 환경 준비만, End-to-end 시나리오는 Sprint 1~2 진입 후 결정

---

## §4. 변경 verbatim

### 4.1 conftest.py EXTENSION (`tests/api/smoke/conftest.py`)

**Before**: K-4 wire 1 의 `app` fixture 만 존재 + OTEL_SDK_DISABLED 자동 설정
**After**: `embedded_pg` session-scoped fixture 추가 + `app` fixture 가 `embedded_pg` 에 의존

```python
# 신규 추가: Sprint 0 (cj-style N+7)
@pytest.fixture(scope="session")
def embedded_pg():
    """Session-scoped embedded-postgres fixture — auto-downloads PostgreSQL 18.6."""
    global _epg_server, _epg_pgdata
    import tempfile
    import shutil
    import embedded_postgres

    _epg_pgdata = Path(tempfile.mkdtemp(prefix="pgdata_mvp_"))
    _epg_server = embedded_postgres.PostgresServer(_epg_pgdata)
    _epg_server.ensure_pgdata_inited()
    _epg_server.ensure_postgres_running()

    info = _epg_server.get_postmaster_info()
    host, port = info.hostname, int(info.port)
    database_url = f"postgresql://postgres@{host}:{port}/postgres"
    os.environ["DATABASE_URL"] = database_url
    os.environ.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret-for-mvp-local-32chars-minimum")
    os.environ.setdefault("JWT_SECRET", "test-jwt-secret-for-mvp-local-32chars-minimum")

    yield {...}

    if _epg_server is not None:
        _epg_server.cleanup()
    if _epg_pgdata is not None and _epg_pgdata.exists():
        shutil.rmtree(_epg_pgdata, ignore_errors=True)
```

**app fixture EXTENSION**:
```python
@pytest.fixture(scope="module")
def app(embedded_pg) -> FastAPI:  # embedded_pg dependency 추가
    """FastAPI app fixture — DATABASE_URL set BEFORE app import."""
    from apps.api.main import app as fastapi_app
    return fastapi_app
```

### 4.2 발견 사항

- **Python requirement**: 프로젝트는 Python 3.12 (<3.13), `.python-version` = 3.12, `uv run` default Python 3.12.13
- **embedded-postgres API**: `init_data_dir()` → `ensure_pgdata_inited()`, `start()` → `ensure_postgres_running()`
- **pgdata Path**: `Path` 객체 필요 (str ❌)
- **URI 파싱**: `get_uri()` = `postgresql://postgres:@127.0.0.1:53947/postgres` (password 빈 문자열)
- **uuid-ossp extension**: PostgreSQL 18 binary 에 미포함 → 그러나 built-in `gen_random_uuid()` 정상 작동 → project 가 uuid-ossp 에 의존하지 않으면 문제 없음

---

## §5. verify gate

| 항목 | 상태 |
|------|------|
| **PROD source 변경** | 0건 |
| **Test 변경** | 1 file (conftest.py EXTENSION, +75 LOC embedded_pg fixture) |
| **alembic 변경** | 0건 |
| **PRD 변경** | 0건 (PRD v7.0 §F/§M/§R unchanged) |
| **Capability matrix source 변경** | 0건 (v1.54 EXTENSION preserved) |
| **Migration source 변경** | 0건 |
| **37 pins unchanged** | ✅ |
| **14 job matrix unchanged** | ✅ |
| **AD-14 stack pin EXTENSION preserved** | ✅ |
| **A19 cohesion 9 surface EXTENSION PASS preserved** | ✅ |
| **3중 게이트 FINAL CLEAN 보존** | ✅ |

---

## §6. Sprint 0 환경 준비 후속 (다음 sprint 결정 보류)

| # | 항목 | 결정 시점 |
|---|------|----------|
| ① | Sprint 1 = K-4 wire 3 main runtime execution actual run (skipif guard 해제 + 100 cases actual pytest) | Sprint 0 commit 후 즉시 |
| ② | Sprint 1.1 = skipif guard 해제 (test_k4_wire_3_runtime_smoke.py 의 DATABASE_URL 가드 제거) | Sprint 1 진입 시 |
| ③ | Sprint 1.2 = alembic upgrade head (모든 migration 적용) | Sprint 1 진입 시 |
| ④ | Sprint 1.3 = Seed data 작성 (1 tenant + 1 owner + 5 products + 1 BOM + 1 month data) | Sprint 1 진입 시 |
| ⑤ | Sprint 2 = Endpoint 부재 54건 회복 (K-4 wire 3 main first-pass 결과 분석 후) | Sprint 1 결과 분석 후 |
| ⑥ | Sprint 3 = End-to-end 시나리오 manual click verify (Login → 각 module → export) | Sprint 2 완료 후 |
| ⑦ | 결정 보류 11건 (디자인가이드 / M10~M12 / cj-314 wire 2~6 / batch A/B/C / Pilot outreach / 운영 cleanup / CI/web-e2e / Phase C 잔여 / 화면정의 / PRD v2 EXTENSION) | honestly DEFER post-MVP |

---

## §7. 결정 wire 보존

**87/87 cumulative 결정 wire 보존** (cj-style N+6 의 86 + **NEW 87번째 Sprint 0 환경 준비 (cj-style N+7th)**)

**CR 11-3 honest-DEFER 264번째** chain cj-style 257 → 267 → 279 → 281 → 283 → 285 → 304 → 305 → 306 → 307 + N-1 + N+1 + N+2 + N+3 + N+4 + N+5 + N+6 + **N+7** verbatim mirror.

**PRE-EXISTING honestly DEFER carryover 보존**:
- cj-303 4건
- PRE-EXISTING 6건
- cj-307 carryover LOW RISK ~30건
- sso 13 skipped tests
- W1~W8 carryover
- epics.md triage (1478 lines uncommitted change)
- PRD v2 EXTENSION
- 비용 발생 항목 모두 (사용자 2026-09-10 결정 wire verbatim '배포작업 안 함 / RESEND·RAILWAY 등 지금 단계 X')

---

## §8. 결정 wire 일자

2026-09-13 (KST, D-1, Pilot W1 launch D-day 2026-09-14 KST Mon 까지 ~12-24시간 잔여)

후속 마감 = 본 commit (sprint-status v4.124 EXTENSION + MEMORY.md hook + handoff + commit-msg + conftest.py = 5 files atomic single sprint)
