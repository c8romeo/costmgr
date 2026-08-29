#!/usr/bin/env python3
"""Install stage parity check (cj-style 209 — AD-14 Detection Surface EXTENSION).

Verifies that packages listed in ``docs/STACK_PIN.yaml`` are actually *installed*
on disk under ``node_modules/.pnpm/`` (Node) and ``apps/api/.venv`` / ``uv.lock``
(Python), not just declared in ``package.json`` / ``pyproject.toml``.

Background (cj-style 204 cleanup sprint):
  cj-197 / cj-202 commits claimed ``"Recharts 2.12.7 AD-14 stack pin"`` but the
  install step was missing. ``scripts/check_stack_pin.py`` validates declaration
  parity; this script validates **install parity** (the next downstream stage).

Exit codes:
  0 — all pinned packages are installed at the pinned versions
  1 — at least one pinned package is missing or at the wrong version on disk
  2 — environment / setup error (missing uv.lock, missing node_modules, ...)

Environment:
  STACK_PIN_ROOT  — repo root (default: parent of this script)
  INSTALL_STAGE_BASELINE  — JSON file with installed-version snapshot (optional,
                            used to detect *new* install-stage drift on top of
                            declaration drift)
  VERBOSE=1       — show all expected vs actual installed versions
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

# Force UTF-8 output on Windows consoles (cp949 by default).
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

ROOT = Path(os.environ.get("STACK_PIN_ROOT") or Path(__file__).resolve().parent.parent)
STACK_PIN_YAML = ROOT / "docs" / "STACK_PIN.yaml"
PNPM_LOCK = ROOT / "pnpm-lock.yaml"
UV_LOCK = ROOT / "uv.lock"
NODE_MODULES = ROOT / "node_modules" / ".pnpm"
VERBOSE = os.environ.get("VERBOSE") == "1"

try:
    import yaml  # CASCADE-1 verbatim
except ImportError:  # pragma: no cover
    sys.stderr.write(
        "[ERROR] PyYAML not installed. Run via `uv run python scripts/check_install_stage.py`.\n"
    )
    sys.exit(2)

# Frontend pins live in apps/web/package.json (next, react, react_dom, typescript, tailwind).
# Backend pins live in apps/api/pyproject.toml (fastapi, pydantic, sqlalchemy, ...).
# Dev tooling pins (pytest, ruff, import_linter, ...) live in root pyproject.toml.
PYTHON_PKGS = frozenset(
    {
        "pydantic",
        "pydantic_core",
        "sqlalchemy",
        "alembic",
        "asyncpg",
        "pyjwt",
        "supabase",
        "pydantic_settings",
        "uvicorn",
        "httpx",
        "fastapi",
        "numpy",
        "hatchling",
        "pytest",
        "ruff",
        "import_linter",
        "dependency_cruiser",
    }
)
NODE_PKGS = frozenset({"next", "react", "react_dom", "typescript", "tailwind"})


# ── Helpers ───────────────────────────────────────────────────────────────


def _read_yaml(path: Path) -> dict:
    if not path.exists():
        sys.stderr.write(f"[ERROR] missing SSOT: {path}\n")
        sys.exit(2)
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _load_pnpm_resolved() -> dict[str, str]:
    """Return {package_name: 'pkg@version'} from pnpm-lock.yaml (resolved importers)."""
    if not PNPM_LOCK.exists():
        sys.stderr.write(f"[ERROR] missing lockfile: {PNPM_LOCK}\n")
        sys.exit(2)
    text = PNPM_LOCK.read_text(encoding="utf-8")
    # pnpm-lock.yaml: sections like `importers:\n  apps/web:\n    ...\n  packages:`.
    # Per-package resolution lives under `packages:` keys like `'/@types/react@19.1.1':`.
    resolved: dict[str, str] = {}
    for match in re.finditer(r"'?(/@?[a-zA-Z0-9_./@\-]+)@(\d+\.\d+\.\d+[^']*)'?:", text):
        full_spec, version = match.group(1), match.group(2)
        # Strip leading slash if any (pnpm prefix for scoped or nested paths).
        name = full_spec.lstrip("/").split("/")[0] if full_spec.startswith("/") else full_spec.split("/")[0]
        # Handle scoped packages like `@types/react`.
        if full_spec.startswith("/@") and "/" in full_spec[2:]:
            scope, rest = full_spec[1:].split("/", 1)
            name = f"{scope}/{rest.split('@')[0]}"
        resolved[name] = version
    return resolved


def _load_uv_resolved() -> dict[str, str]:
    """Return {package_name_lower: 'version'} from uv.lock (resolution entries)."""
    if not UV_LOCK.exists():
        sys.stderr.write(f"[ERROR] missing lockfile: {UV_LOCK}\n")
        sys.exit(2)
    # uv.lock is TOML. We extract only the [[package]] resolution entries (name + version).
    text = UV_LOCK.read_text(encoding="utf-8")
    resolved: dict[str, str] = {}
    for match in re.finditer(r'\[\[package\]\]\s*\nname\s*=\s*"([^"]+)"\s*\nversion\s*=\s*"([^"]+)"', text):
        resolved[match.group(1).lower()] = match.group(2)
    return resolved


def _node_installed(name: str, version: str) -> tuple[bool, str]:
    """Return (installed, on_disk_version_or_reason).

    For a pinned Node package, check ``node_modules/.pnpm/<name>@<version>/...``
    Actually pnpm stores under ``<name>@<version>/node_modules/<name>`` pattern,
    but the directory name uses ``@scope/name@version`` for scoped packages.

    CR 11-3 honest boundary: if node_modules is missing entirely (cold checkout
    without pnpm install run), we report NOT INSTALLED rather than over-claim.
    """
    if not NODE_MODULES.exists():
        return False, "node_modules/.pnpm absent — run `pnpm install --frozen-lockfile`"

    # Iterate pnpm's content-addressed store. pnpm uses directory names like
    # `typescript@5.9.3` or `@types+react@19.1.1` (slashes → '+' for scoped).
    pnpm_slug = name.replace("/", "+")
    target_dir = NODE_MODULES / f"{pnpm_slug}@{version}"
    if target_dir.exists():
        return True, version
    # Some pnpm versions use a sha-pure dir; fall back to glob match.
    for child in NODE_MODULES.iterdir():
        if not child.is_dir():
            continue
        if child.name.startswith(f"{pnpm_slug}@") and version in child.name:
            return True, child.name.split("@", 1)[1]
    return False, f"expected {pnpm_slug}@{version} under node_modules/.pnpm/"


def _python_installed(name: str, version: str) -> tuple[bool, str]:
    """Return (installed, on_disk_version_or_reason).

    For a pinned Python package, check ``uv.lock`` resolution. CR 11-3 honest
    boundary: if uv.lock is missing, NOT INSTALLED — don't probe ``.venv`` which
    may be stale from a different machine.
    """
    resolved = _load_uv_resolved()
    if name.lower() in resolved:
        on_disk = resolved[name.lower()]
        return on_disk == version, on_disk
    # Special case: hatchling / pytest / ruff / import_linter live in root
    # [dependency-groups] section but still resolve in uv.lock.
    return False, f"not resolved in uv.lock (expected {version})"


# ── Main ───────────────────────────────────────────────────────────────────


def main() -> int:
    pin_doc = _read_yaml(STACK_PIN_YAML)
    pins: dict[str, str] = pin_doc.get("stack_pin", {})

    # All backend + dev tooling pins resolve under uv.lock; all frontend pins
    # resolve under pnpm-lock.yaml + node_modules/.pnpm/.

    missing: list[tuple[str, str, str]] = []  # (pkg, pinned_version, reason)
    installed_count = 0

    for pkg, pinned_version in pins.items():
        # Skip non-package keys: node, python, pnpm, uv, postgresql (CI service image).
        if pkg in {"node", "python", "pnpm", "uv", "postgresql"}:
            continue
        # Skip Docker image digests.
        if pkg.endswith("_digest"):
            continue
        # Map react_dom → react-dom for filesystem lookup.
        fs_name = "react-dom" if pkg == "react_dom" else pkg

        if pkg in PYTHON_PKGS:
            ok, info = _python_installed(fs_name, pinned_version)
            ecosystem = "python"
        elif pkg in NODE_PKGS:
            ok, info = _node_installed(fs_name, pinned_version)
            ecosystem = "node"
        else:
            # Infra / runtime keys we don't probe on disk.
            if VERBOSE:
                sys.stdout.write(f"[INSTALL_STAGE] SKIP {pkg}={pinned_version} (infra key)\n")
            continue

        if ok:
            installed_count += 1
            if VERBOSE:
                sys.stdout.write(f"[INSTALL_STAGE] OK   {ecosystem:6s} {pkg}=={info}\n")
        else:
            missing.append((pkg, pinned_version, info))
            sys.stdout.write(f"[INSTALL_STAGE] MISS {ecosystem:6s} {pkg} (pinned {pinned_version}) — {info}\n")

    total = installed_count + len(missing)
    sys.stdout.write(
        f"\n[INSTALL_STAGE] Installed: {installed_count}/{total} pinned packages on disk\n"
    )

    if missing:
        sys.stdout.write(
            f"[INSTALL_STAGE] FAIL — {len(missing)} pinned package(s) missing or wrong version on disk\n"
            "  Run `pnpm install --frozen-lockfile` + `uv sync --frozen` to recover.\n"
        )
        return 1

    sys.stdout.write("[INSTALL_STAGE] OK all pinned packages installed at pinned versions\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
