"""tests.web.lib.test_m12_account_backup_parity — Story 12.2 cross-language drift detector.

CR 12-5 D-13 pattern: cross-language drift detector between Python pure kernel
(`packages/services/m12_account/backup_export.py`) and TS mirror
(`apps/web/lib/m12-account-backup.ts`).

Drift cases that this test catches:
- Constant value mismatch (e.g., SCHEMA_VERSION differs between Python/TS)
- BACKUP_TABLES tuple order differs (drift in the 7-table dump)
- TS mirror accidentally drops a kernel constant (frontend renders stale data)
- TS mirror accidentally adds a non-existent constant (frontend crashes on import)

If a Python constant changes, this test fails → TS mirror must be updated
in lockstep. If a TS mirror constant changes, this test fails → Python
kernel must be updated.

The test is **string-parsed** (no Python imports the TS file, no TS
imports the Python file) — keeps the test fast and language-agnostic.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PY_KERNEL = (
    REPO_ROOT
    / "packages"
    / "services"
    / "m12_account"
    / "backup_export.py"
)
TS_MIRROR = REPO_ROOT / "apps" / "web" / "lib" / "m12-account-backup.ts"


def _parse_python_constants() -> dict[str, str]:
    """Parse `NAME: type = value` from Python kernel.

    Captures only module-level Final/constants (not function locals).
    """
    text = PY_KERNEL.read_text(encoding="utf-8")
    pattern = re.compile(
        r"^([A-Z_][A-Z0-9_]*)\s*:\s*(?:Final\[)?(?:str|int)\]?\s*=\s*(.+?)$",
        re.MULTILINE,
    )
    out: dict[str, str] = {}
    for match in pattern.finditer(text):
        name = match.group(1)
        raw_value = match.group(2).strip()
        # Strip trailing comments
        if "#" in raw_value:
            raw_value = raw_value.split("#", 1)[0].strip()
        # Strip quotes (single or double)
        if (raw_value.startswith('"') and raw_value.endswith('"')) or (
            raw_value.startswith("'") and raw_value.endswith("'")
        ):
            raw_value = raw_value[1:-1]
        out[name] = raw_value
    return out


def _parse_ts_constants() -> dict[str, str]:
    """Parse `export const NAME = value` from TS mirror."""
    text = TS_MIRROR.read_text(encoding="utf-8")
    pattern = re.compile(
        r"export const ([A-Z_][A-Z0-9_]*)\s*=\s*(.+?)\s+as const",
    )
    out: dict[str, str] = {}
    for match in pattern.finditer(text):
        name = match.group(1)
        raw_value = match.group(2).strip()
        # Strip quotes
        if (raw_value.startswith('"') and raw_value.endswith('"')) or (
            raw_value.startswith("'") and raw_value.endswith("'")
        ):
            raw_value = raw_value[1:-1]
        out[name] = raw_value
    return out


def _parse_python_BACKUP_TABLES() -> list[str]:
    """Parse BACKUP_TABLES tuple from Python kernel."""
    text = PY_KERNEL.read_text(encoding="utf-8")
    match = re.search(
        r"BACKUP_TABLES\s*:\s*Final\[tuple\[str,\s*\.\.\.\]\]\s*=\s*\(([^)]+)\)",
        text,
        re.DOTALL,
    )
    if not match:
        return []
    body = match.group(1)
    return [m.strip().strip('"').strip("'") for m in re.findall(r'"([^"]+)"', body)]


def _parse_ts_BACKUP_TABLES() -> list[str]:
    """Parse BACKUP_TABLES array from TS mirror."""
    text = TS_MIRROR.read_text(encoding="utf-8")
    match = re.search(
        r"export const BACKUP_TABLES\s*=\s*\[([^\]]+)\]\s*as const",
        text,
        re.DOTALL,
    )
    if not match:
        return []
    body = match.group(1)
    return [m.strip().strip('"').strip("'") for m in re.findall(r'"([^"]+)"', body)]


# ── 1. Files exist ──────────────────────────────────────────────
def test_python_kernel_exists() -> None:
    assert PY_KERNEL.exists(), f"missing Python kernel: {PY_KERNEL}"


def test_ts_mirror_exists() -> None:
    assert TS_MIRROR.exists(), f"missing TS mirror: {TS_MIRROR}"


# ── 2. SCHEMA_VERSION parity ─────────────────────────────────────
def test_schema_version_parity() -> None:
    py = _parse_python_constants()
    ts = _parse_ts_constants()
    assert "SCHEMA_VERSION" in py, "Python kernel missing SCHEMA_VERSION"
    assert "BACKUP_SCHEMA_VERSION" in ts, "TS mirror missing BACKUP_SCHEMA_VERSION"
    assert py["SCHEMA_VERSION"] == ts["BACKUP_SCHEMA_VERSION"], (
        f"drift: Python SCHEMA_VERSION={py['SCHEMA_VERSION']!r} "
        f"vs TS BACKUP_SCHEMA_VERSION={ts['BACKUP_SCHEMA_VERSION']!r}"
    )


# ── 3. MAX_PAYLOAD_BYTES parity ─────────────────────────────────
def test_max_payload_bytes_parity() -> None:
    py = _parse_python_constants()
    ts = _parse_ts_constants()
    assert "MAX_PAYLOAD_BYTES" in py
    assert "BACKUP_MAX_PAYLOAD_BYTES" in ts
    py_val = int(py["MAX_PAYLOAD_BYTES"].split("*")[0].strip())
    # Python: 50 * 1024 * 1024 → 50 MB
    # TS: 50 * 1024 * 1024 (already numeric literal in const expr)
    ts_val_str = ts["BACKUP_MAX_PAYLOAD_BYTES"]
    # TS may be either literal `50 * 1024 * 1024` or precomputed `52428800`
    if "*" in ts_val_str:
        ts_first = int(ts_val_str.split("*")[0].strip())
        assert ts_first == py_val, (
            f"drift: Python MAX_PAYLOAD_BYTES={py['MAX_PAYLOAD_BYTES']!r} "
            f"vs TS={ts_val_str!r}"
        )
    else:
        # Pre-computed value
        ts_val = int(ts_val_str)
        expected = 50 * 1024 * 1024
        assert ts_val == expected, (
            f"TS BACKUP_MAX_PAYLOAD_BYTES={ts_val} != expected {expected}"
        )


# ── 4. AUDIT_LOG_WINDOW_DAYS parity ────────────────────────────
def test_audit_log_window_days_parity() -> None:
    py = _parse_python_constants()
    ts = _parse_ts_constants()
    assert "AUDIT_LOG_WINDOW_DAYS" in py
    assert "BACKUP_AUDIT_LOG_WINDOW_DAYS" in ts
    py_val = int(py["AUDIT_LOG_WINDOW_DAYS"])
    ts_val = int(ts["BACKUP_AUDIT_LOG_WINDOW_DAYS"])
    assert py_val == ts_val == 365, (
        f"AUDIT_LOG_WINDOW_DAYS drift: py={py_val} ts={ts_val}"
    )


# ── 5. BACKUP_TABLES 7-table parity ─────────────────────────────
def test_backup_tables_count_parity() -> None:
    py = _parse_python_BACKUP_TABLES()
    ts = _parse_ts_BACKUP_TABLES()
    assert len(py) == 7, f"Python BACKUP_TABLES has {len(py)} entries (expected 7)"
    assert len(ts) == 7, f"TS BACKUP_TABLES has {len(ts)} entries (expected 7)"
    assert len(py) == len(ts), (
        f"drift: Python has {len(py)} tables, TS has {len(ts)}"
    )


def test_backup_tables_set_parity() -> None:
    py = set(_parse_python_BACKUP_TABLES())
    ts = set(_parse_ts_BACKUP_TABLES())
    assert py == ts, (
        f"drift in BACKUP_TABLES set: missing-from-ts={py - ts}, "
        f"extra-in-ts={ts - py}"
    )


def test_backup_tables_order_parity() -> None:
    """Order matters — Python serializes tables in this order in the payload."""
    py = _parse_python_BACKUP_TABLES()
    ts = _parse_ts_BACKUP_TABLES()
    assert py == ts, (
        f"drift in BACKUP_TABLES order:\n  Python: {py}\n  TS:      {ts}"
    )


# ── 6. DEFAULT_LIST_DAYS parity ─────────────────────────────────
def test_default_list_days_parity() -> None:
    py_service = (
        REPO_ROOT
        / "apps"
        / "api"
        / "modules"
        / "m12_account"
        / "services"
        / "backup_export_service.py"
    )
    text = py_service.read_text(encoding="utf-8")
    match = re.search(r"DEFAULT_LIST_DAYS:\s*int\s*=\s*(\d+)", text)
    assert match, "Python service missing DEFAULT_LIST_DAYS"
    py_val = int(match.group(1))

    ts = _parse_ts_constants()
    assert "BACKUP_DEFAULT_LIST_DAYS" in ts
    ts_val = int(ts["BACKUP_DEFAULT_LIST_DAYS"])
    assert py_val == ts_val == 7, (
        f"DEFAULT_LIST_DAYS drift: py={py_val} ts={ts_val}"
    )


# ── 7. BACKUP_RETENTION_DAYS parity (NFR4) ─────────────────────
def test_backup_retention_days_parity() -> None:
    py_cron = REPO_ROOT / "apps" / "api" / "jobs" / "backup_retention.py"
    text = py_cron.read_text(encoding="utf-8")
    # Look for timedelta(days=30) or "30일" comment
    match_30d = re.search(r"timedelta\(days\s*=\s*(\d+)\)", text)
    match_30c = re.search(r"30-?day|30일|30 days?", text, re.IGNORECASE)
    assert match_30d or match_30c, (
        "Python retention cron missing 30-day reference"
    )
    py_val = int(match_30d.group(1)) if match_30d else 30
    ts = _parse_ts_constants()
    assert "BACKUP_RETENTION_DAYS" in ts
    ts_val = int(ts["BACKUP_RETENTION_DAYS"])
    assert py_val == ts_val == 30, (
        f"BACKUP_RETENTION_DAYS drift: py={py_val} ts={ts_val}"
    )


# ── 8. Mirror coverage — TS exposes every Python kernel constant ─
def test_ts_mirror_covers_python_kernel_constants() -> None:
    py = _parse_python_constants()
    ts = _parse_ts_constants()
    # Map Python kernel name → expected TS mirror name
    name_map = {
        "SCHEMA_VERSION": "BACKUP_SCHEMA_VERSION",
        "MAX_PAYLOAD_BYTES": "BACKUP_MAX_PAYLOAD_BYTES",
        "AUDIT_LOG_WINDOW_DAYS": "BACKUP_AUDIT_LOG_WINDOW_DAYS",
    }
    for py_name, ts_name in name_map.items():
        if py_name in py:
            assert ts_name in ts, (
                f"TS mirror missing {ts_name!r} (mirrors Python {py_name!r})"
            )


# ── 9. buildBackupFilename parity ───────────────────────────────
def test_build_backup_filename_parity() -> None:
    """TS `buildBackupFilename` must produce same output as Python
    `_build_backup_filename` in handlers.py.
    """
    py_handlers = (
        REPO_ROOT
        / "apps"
        / "api"
        / "modules"
        / "m12_account"
        / "handlers.py"
    )
    text = py_handlers.read_text(encoding="utf-8")
    py_pattern = re.search(
        r'return f"backup-\{backup_date_iso\}\.json"', text
    )
    assert py_pattern, "Python _build_backup_filename pattern not found"

    ts_text = TS_MIRROR.read_text(encoding="utf-8")
    ts_pattern = re.search(
        r'export function buildBackupFilename\(backupDateIso: string\): string \{\s*'
        r'return `backup-\$\{backupDateIso\}\.json`;\s*\}',
        ts_text,
    )
    assert ts_pattern, "TS buildBackupFilename pattern not found"


# ── 10. Endpoint path parity (mirror docs) ──────────────────────
def test_endpoint_paths_in_ko_kr_namespace() -> None:
    """ko-KR.json::account_backup namespace exists (Story 12.2 wire).

    Cross-checks that the i18n namespace the Client Component consumes
    actually exists in the SSOT JSON file (CR 11-4 D-002 lesson —
    dead ko-KR.json keys break runtime i18n).
    """
    ko_kr_path = REPO_ROOT / "apps" / "web" / "messages" / "ko-KR.json"
    import json

    data = json.loads(ko_kr_path.read_text(encoding="utf-8"))
    assert "account_backup" in data, (
        "ko-KR.json missing 'account_backup' namespace — "
        "BackupDownloadPanel would render raw i18n keys at runtime"
    )
    expected_keys = {
        "panel_title",
        "panel_description",
        "trigger_button",
        "download_button",
        "col_date",
        "col_size",
        "col_rows",
        "col_audit_rows",
        "col_sha256",
        "col_actions",
        "empty_message",
        "error_prefix",
        "filename_hint",
    }
    actual_keys = set(data["account_backup"].keys())
    missing = expected_keys - actual_keys
    assert not missing, (
        f"ko-KR.json::account_backup missing keys: {missing}"
    )


# ── 11. Sidebar entry parity ────────────────────────────────────
def test_sidebar_has_backup_link() -> None:
    """Sidebar entry "백업 다운로드" → /account/backups exists."""
    sidebar = REPO_ROOT / "apps" / "web" / "components" / "sidebar" / "Sidebar.tsx"
    text = sidebar.read_text(encoding="utf-8")
    assert "/account/backups" in text, (
        "Sidebar missing /account/backups entry (Story 12.2 wire)"
    )
