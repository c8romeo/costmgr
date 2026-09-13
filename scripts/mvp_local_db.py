"""scripts.mvp_local_db — MVP 로컬 시연용 embedded-postgres + alembic + seed 통합 부트스트랩.

사용법:
    uv run python scripts/mvp_local_db.py up        # DB 시작 + migration + seed
    uv run python scripts/mvp_local_db.py status     # 실행 중인지 확인
    uv run python scripts/mvp_local_db.py down       # DB 종료 (cleanup)
    uv run python scripts/mvp_local_db.py wait       # DB 살아있는 동안 대기 (별도 터미널)

환경:
    - port auto-allocated by embedded-postgres (pgdata in user %TEMP%)
    - DATABASE_URL 자동 export (.mvp_local_db_url 파일)
    - PID file: .mvp_local_db.pid (postgres master PID)

K-4 wire 3 main runtime execution 의 env-free local dev 진입로.
cj-style N+7 Sprint 0 환경 준비 + TO-DO D (alembic) + TO-DO E (seed) 통합.

Sprint 0 (cj-style N+9) env-free fix-forward:
- LC_ALL=C / LANG=C / LC_COLLATE=C / LC_CTYPE=C 자동 설정 (Windows Korean 949
  codepage 의 initdb text-search config 부재 회피)
- TMPDIR unset (비표준 ESTsoft/CreatorTemp override 회피)
- mkdtemp(prefix='pgdata_mvp_local_') for fresh pgdata per invocation
  (cj-style N+7 conftest.py verbatim mirror)
"""

from __future__ import annotations

import argparse
import asyncio
import os

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

import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

PID_FILE = Path(__file__).parent.parent / ".mvp_local_db.pid"
PORT = 54329
DB_USER = "postgres"
DB_PASS = ""
DB_NAME = "postgres"
DATA_DIR_NAME = "pgdata_mvp_local"


def _pid_alive(pid: int) -> bool:
    """Return True if a process with the given PID is alive."""
    if sys.platform == "win32":
        import ctypes
        kernel32 = ctypes.windll.kernel32
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        STILL_ACTIVE = 259
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if handle == 0:
            return False
        try:
            exit_code = ctypes.c_ulong()
            ok = kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
            return bool(ok) and exit_code.value == STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)
    else:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


def _read_pid() -> int | None:
    """Read PID from file. Return None if no file or stale PID."""
    if not PID_FILE.exists():
        return None
    try:
        pid = int(PID_FILE.read_text().strip())
    except (ValueError, OSError):
        return None
    if not _pid_alive(pid):
        PID_FILE.unlink(missing_ok=True)
        return None
    return pid


def _write_pid(pid: int) -> None:
    PID_FILE.write_text(str(pid))


def _project_root() -> Path:
    return Path(__file__).parent.parent


def _pgdata_dir() -> Path:
    """Allocate a fresh pgdata directory under the user TEMP.

    Sprint 0 (cj-style N+9): use mkdtemp for env-free uniqueness.
    cj-style N+7 conftest.py `tempfile.mkdtemp(prefix='pgdata_mvp_')`
    pattern verbatim mirror. Replaces cj-style N+8 fixed-dir
    (`tempfile.gettempdir() / DATA_DIR_NAME`) which conflicted with
    non-standard TMPDIR paths (e.g. ESTsoft/CreatorTemp) and rmtree's
    `ignore_errors=True` silently swallowed permission/IO failures.
    """
    return Path(tempfile.mkdtemp(prefix="pgdata_mvp_local_"))


def _build_database_url() -> str:
    return f"postgresql://{DB_USER}@{DB_USER}:{DB_PASS}@{('127.0.0.1' if not DB_PASS else '127.0.0.1')}:{PORT}/{DB_NAME}"


def cmd_up() -> int:
    """Start embedded-postgres + run alembic + seed data."""
    if (existing := _read_pid()) is not None:
        print(f"[mvp_local_db] already running PID={existing}")
        return 0

    pgdata = _pgdata_dir()
    print(f"[mvp_local_db] pgdata (fresh, mkdtemp) = {pgdata}")

    print(f"[mvp_local_db] starting embedded-postgres")
    import embedded_postgres
    server = embedded_postgres.PostgresServer(pgdata)
    server.ensure_pgdata_inited()
    server.ensure_postgres_running()

    info = server.get_postmaster_info()
    port_actual = int(info.port)
    host_actual = info.hostname
    database_url = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{host_actual}:{port_actual}/{DB_NAME}"
    print(f"[mvp_local_db] PostgreSQL on {host_actual}:{port_actual}")
    print(f"[mvp_local_db] DATABASE_URL = {database_url}")
    print(f"[mvp_local_db] pgdata = {pgdata}")

    # Run alembic upgrade head
    print("[mvp_local_db] running alembic upgrade head...")
    env = os.environ.copy()
    env["DATABASE_URL"] = database_url
    env["OTEL_SDK_DISABLED"] = "true"
    env.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret-for-mvp-local-32chars-minimum")
    env.setdefault("JWT_SECRET", "test-jwt-secret-for-mvp-local-32chars-minimum")

    project_root = _project_root()

    # Sprint 0 (cj-style N+7) — embedded-postgres has no Supabase roles AND no
    # `public.set_updated_at()` trigger function. RLS policies and trigger
    # creation in 0001/0038 expect both. Apply the CI shim
    # (supabase/policies/0000_supabase_ci_shim.sql) which creates the roles
    # AND set_updated_at() in one shot. Production Supabase already has these;
    # the shim is idempotent (DO $$ IF NOT EXISTS ... CREATE ...). No behavior
    # change in production. After the shim, also pre-create alembic_version
    # with VARCHAR(255) so revision IDs >32 chars don't truncate.
    print("[mvp_local_db] applying supabase CI shim (roles + set_updated_at)...")
    import asyncpg
    async def precreate():
        sync_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(sync_url)
        try:
            shim_path = project_root / "supabase" / "policies" / "0000_supabase_ci_shim.sql"
            if shim_path.exists():
                shim_sql = shim_path.read_text(encoding="utf-8")
                await conn.execute(shim_sql)
                print("[mvp_local_db] CI shim applied (roles + set_updated_at)")
            else:
                print(f"[mvp_local_db] WARNING: shim not found at {shim_path}")
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS alembic_version ("
                "    version_num VARCHAR(255) NOT NULL PRIMARY KEY"
                ")"
            )
            print("[mvp_local_db] alembic_version ready (VARCHAR 255)")
        finally:
            await conn.close()
    asyncio.run(precreate())

    result = subprocess.run(
        [
            sys.executable, "-m", "alembic",
            "-c", str(project_root / "apps" / "api" / "alembic.ini"),
            "upgrade", "head",
        ],
        cwd=str(project_root),
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"[mvp_local_db] alembic FAILED")
        print("STDOUT:", result.stdout[-2000:])
        print("STDERR:", result.stderr[-2000:])
        server.cleanup()
        shutil.rmtree(pgdata, ignore_errors=True)
        return 1
    print(f"[mvp_local_db] alembic OK")

    # Write database_url to a file so other processes can read it
    dburl_file = project_root / ".mvp_local_db_url"
    dburl_file.write_text(database_url)

    # Record postgres master PID (not parent python PID) so `mvp_local_db.py down`
    # kills the actual server, not the wait-loop parent.
    _write_pid(info.pid)

    print(f"[mvp_local_db] ready. DATABASE_URL={database_url}")
    print(f"[mvp_local_db] postgres master PID={info.pid} recorded in {PID_FILE}")
    print("[mvp_local_db] next steps:")
    print("  1. open a NEW terminal and run seed:")
    print(f'     set DATABASE_URL={database_url}')
    print("     uv run python apps/api/scripts/cli/pilot_tenant_provision.py --tenant-id 00000000-0000-0000-0000-000000000001 --industry saas_manufacturing --admin-email demo@costmgr.local --admin-display-name \"Demo Owner\" --finance-contact-email finance@costmgr.local")
    print("  2. start FastAPI:")
    print(f'     set DATABASE_URL={database_url}')
    print("     uv run uvicorn apps.api.main:app --reload --port 8000")
    print("  3. in ANOTHER terminal, start Next.js:")
    print("     cd apps/web && pnpm dev")
    print("  4. open http://localhost:3000")
    print("  5. when done, press Ctrl+C here OR run: uv run python scripts/mvp_local_db.py down")

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n[mvp_local_db] shutting down...")
    finally:
        _cleanup(server, pgdata)
    return 0


def _cleanup(server, pgdata: Path) -> None:
    try:
        server.cleanup()
    except Exception as e:
        print(f"[mvp_local_db] server.cleanup error: {e}")
    shutil.rmtree(pgdata, ignore_errors=True)
    PID_FILE.unlink(missing_ok=True)
    dburl_file = _project_root() / ".mvp_local_db_url"
    dburl_file.unlink(missing_ok=True)
    print("[mvp_local_db] cleanup done")


def cmd_status() -> int:
    pid = _read_pid()
    if pid is None:
        print("[mvp_local_db] not running")
        return 1
    print(f"[mvp_local_db] running PID={pid}")
    dburl_file = _project_root() / ".mvp_local_db_url"
    if dburl_file.exists():
        print(f"[mvp_local_db] DATABASE_URL={dburl_file.read_text().strip()}")
    return 0


def cmd_down() -> int:
    pid = _read_pid()
    if pid is None:
        print("[mvp_local_db] not running")
        return 0
    print(f"[mvp_local_db] killing PID={pid}")
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
    else:
        os.kill(pid, signal.SIGTERM)
    PID_FILE.unlink(missing_ok=True)
    # Sprint 0 (cj-style N+9): also clean up .mvp_local_db_url that cmd_up writes.
    # taskkill /F bypasses the KeyboardInterrupt-triggered _cleanup(), so we
    # explicitly unlink the URL file here. pgdata dirs (mkdtemp under %TEMP%)
    # are left for OS temp cleanup; cj-style N+9 close-out scope decision.
    (_project_root() / ".mvp_local_db_url").unlink(missing_ok=True)
    print("[mvp_local_db] down")
    return 0


def cmd_wait() -> int:
    """Block until the DB is shut down."""
    pid = _read_pid()
    if pid is None:
        print("[mvp_local_db] no DB running")
        return 1
    print(f"[mvp_local_db] waiting for PID={pid} to exit...")
    while _pid_alive(pid):
        time.sleep(5)
    print("[mvp_local_db] DB exited")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("up")
    sub.add_parser("status")
    sub.add_parser("down")
    sub.add_parser("wait")
    args = parser.parse_args()

    if args.cmd == "up":
        return cmd_up()
    if args.cmd == "status":
        return cmd_status()
    if args.cmd == "down":
        return cmd_down()
    if args.cmd == "wait":
        return cmd_wait()
    return 1


if __name__ == "__main__":
    sys.exit(main())
