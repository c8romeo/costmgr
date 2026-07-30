#!/usr/bin/env bash
# scripts/bump_stack_pin.sh — Bump a single stack-pin version with auto [STACK BUMP] tag.
#
# Story 0.3 / AD-14 enforcement helper.
#
# Usage:
#   ./scripts/bump_stack_pin.sh <package> <new_version> [--force]
#
# Behavior:
#   1. Reads current version from docs/STACK_PIN.yaml via PyYAML (BUMP-3:
#      exact key match, no substring matches).
#   2. Updates docs/STACK_PIN.yaml (canonical source).
#   3. Updates the relevant manifest(s) where <package> is declared
#      (BUMP-1: actually edits the files, not just YAML).
#   4. Prints the planned diff and asks for confirmation.
#   5. Commits with message `[STACK BUMP] bump <package> <old> -> <new>`.
#
# Exit codes:
#   0 = success
#   1 = no-op (current == new) — requires --force to override
#   2 = usage error / unknown package

set -euo pipefail

FORCE=0
if [[ "${3:-}" == "--force" ]]; then
  FORCE=1
fi

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <package> <new_version> [--force]" >&2
  echo "Example: $0 next 16.2.11" >&2
  exit 2
fi

PKG="$1"
VER="$2"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PIN_FILE="$REPO_ROOT/docs/STACK_PIN.yaml"

if [[ ! -f "$PIN_FILE" ]]; then
  echo "STACK_PIN.yaml not found at $PIN_FILE" >&2
  exit 1
fi

# BUMP-3 + BUMP-5 (CR 2026-07-25): use PyYAML for exact key match (avoids
# substring matches like `pytest` matching `pytest-asyncio`). BUMP-2:
# use `python` not `python3` for macOS compat.
read_current() {
  python - "$PIN_FILE" "$PKG" <<'PY'
import sys, yaml
path, key = sys.argv[1], sys.argv[2]
with open(path, encoding="utf-8") as fh:
    doc = yaml.safe_load(fh) or {}
pin = (doc.get("stack_pin") or {}).get(key)
# Fall back to notes.<key>.current if absent
if pin is None:
    notes = (doc.get("notes") or {}).get(key) or {}
    pin = notes.get("current")
print(pin if pin is not None else "")
PY
}

CURRENT="$(read_current)"

if [[ -z "$CURRENT" ]]; then
  echo "Package '$PKG' not found in $PIN_FILE" >&2
  echo "Add it first via Edit, then re-run." >&2
  exit 1
fi

# BUMP-6 (CR 2026-07-25): exit 1 on no-op unless --force
if [[ "$CURRENT" == "$VER" ]]; then
  if [[ $FORCE -eq 0 ]]; then
    echo "Package '$PKG' is already at version '$VER' — no bump needed (use --force to override)." >&2
    exit 1
  fi
  echo "[WARN] No-op bump forced — continuing with manifest re-write."
fi

echo "────────────────────────────────────────────────────────"
echo "Stack pin bump"
echo "  package: $PKG"
echo "  current: $CURRENT"
echo "  target:  $VER"
echo "────────────────────────────────────────────────────────"

# Plan the edits — list the files we expect to touch.
PLAN=()

case "$PKG" in
  node|next|react|react-dom|react_dom|typescript|tailwind)
    PLAN+=("apps/web/package.json")
    [[ "$PKG" == "node" ]] && PLAN+=(".nvmrc" "Dockerfile" "package.json")
    [[ "$PKG" == "next" ]] && PLAN+=("pnpm-lock.yaml")
    ;;
  python|python_slim)
    PLAN+=(".python-version" "Dockerfile")
    ;;
  pnpm)
    PLAN+=("package.json")
    ;;
  uv)
    PLAN+=(".github/workflows/ci.yml")
    ;;
  fastapi|pydantic|pydantic_core|pydantic-core|sqlalchemy|alembic|asyncpg|pyjwt|supabase|pydantic-settings|uvicorn|httpx)
    PLAN+=("apps/api/pyproject.toml")
    ;;
  numpy|pytest|ruff|import_linter|import-linter)
    PLAN+=("packages/cost_engine/pyproject.toml" "pyproject.toml")
    ;;
  postgresql|nginx_alpine|node_alpine|python_slim)
    PLAN+=("Dockerfile" ".github/workflows/ci.yml")
    ;;
  hatchling)
    PLAN+=("pyproject.toml" "apps/api/pyproject.toml" "packages/cost_engine/pyproject.toml" "packages/services/pyproject.toml" "packages/ports/pyproject.toml")
    ;;
  *)
    echo "Unknown package '$PKG' — bump only STACK_PIN.yaml manually." >&2
    PLAN=("$PIN_FILE")
    ;;
esac

echo "Files to update (planned):"
printf '  - %s\n' "${PLAN[@]}"
echo

read -r -p "Proceed? [y/N] " ans
if [[ "$ans" != "y" && "$ans" != "Y" ]]; then
  echo "Aborted." >&2
  exit 1
fi

# BUMP-1 (CR 2026-07-25): actually edit the manifest files (not just YAML).
# Use a single Python helper that knows the case-by-case sed substitutions.

python - "$PIN_FILE" "$PKG" "$VER" "${PLAN[@]}" <<'PY'
import re, sys
from pathlib import Path

pin_file = Path(sys.argv[1])
pkg = sys.argv[2]
ver = sys.argv[3]
plan = sys.argv[4:]

# 1) Update STACK_PIN.yaml — exact key match.
text = pin_file.read_text(encoding="utf-8")
new = re.sub(
    rf"^(\s*{re.escape(pkg)}\s*:\s*).*$",
    rf'\g<1>"{ver}"',
    text,
    count=1,
    flags=re.MULTILINE,
)
if new != text:
    pin_file.write_text(new, encoding="utf-8")
    print(f"  updated {pin_file}")
else:
    print(f"  [WARN] no STACK_PIN.yaml substitution for {pkg}")

# 2) Edit each planned manifest file using the substitution rules below.
SUBS = {
    "next": (r'"next"\s*:\s*"[^"]+"', f'"next": "{ver}"'),
    "react": (r'"react"\s*:\s*"[^"]+"', f'"react": "{ver}"'),
    "react-dom": (r'"react-dom"\s*:\s*"[^"]+"', f'"react-dom": "{ver}"'),
    "typescript": (r'"typescript"\s*:\s*"[^"]+"', f'"typescript": "{ver}"'),
    "@types/node": (r'"@types/node"\s*:\s*"[^"]+"', f'"@types/node": "{ver}"'),
    "@types/react": (r'"@types/react"\s*:\s*"[^"]+"', f'"@types/react": "{ver}"'),
    "fastapi": (r'"fastapi==[^"]+"', f'"fastapi=={ver}"'),
    "pydantic": (r'"pydantic[><=!~]+[^"]+"', f'"pydantic=={ver}"'),
    "pydantic-core": (r'"pydantic-core==[^"]+"', f'"pydantic-core=={ver}"'),
    "sqlalchemy": (r'"sqlalchemy==[^"]+"', f'"sqlalchemy=={ver}"'),
    "alembic": (r'"alembic==[^"]+"', f'"alembic=={ver}"'),
    "asyncpg": (r'"asyncpg==[^"]+"', f'"asyncpg=={ver}"'),
    "pyjwt": (r'"pyjwt==[^"]+"', f'"pyjwt=={ver}"'),
    "supabase": (r'"supabase==[^"]+"', f'"supabase=={ver}"'),
    "pydantic-settings": (r'"pydantic-settings==[^"]+"', f'"pydantic-settings=={ver}"'),
    "uvicorn": (r'"uvicorn==[^"]+"', f'"uvicorn=={ver}"'),
    "httpx": (r'"httpx==[^"]+"', f'"httpx=={ver}"'),
    "pytest": (r'"pytest==[^"]+"', f'"pytest=={ver}"'),
    "ruff": (r'"ruff==[^"]+"', f'"ruff=={ver}"'),
    "numpy": (r'"numpy==[^"]+"', f'"numpy=={ver}"'),
    "import-linter": (r'"import-linter==[^"]+"', f'"import-linter=={ver}"'),
    "hatchling": (r'"hatchling[><=!~]+[^"]+"', f'"hatchling=={ver}"'),
}

pattern, replacement = SUBS.get(pkg, (None, None))
if pattern:
    for path_str in plan:
        p = Path(path_str)
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        if re.search(pattern, text):
            new = re.sub(pattern, replacement, text, count=1)
            p.write_text(new, encoding="utf-8")
            print(f"  updated {p}")
        else:
            print(f"  [INFO] {p}: pattern for {pkg} not found (skipped)")
PY

# Special case: Dockerfile (regex-based; tag replacement)
if [[ "$PKG" == "python_slim" || "$PKG" == "node_alpine" || "$PKG" == "nginx_alpine" || "$PKG" == "postgresql" ]]; then
  python - "$PKG" "$VER" <<'PY'
import re, sys
from pathlib import Path
pkg, ver = sys.argv[1], sys.argv[2]
base = pkg.replace("_alpine", "").replace("_slim", "")
for p in [Path("Dockerfile"), Path(".github/workflows/ci.yml")]:
    if not p.exists():
        continue
    text = p.read_text(encoding="utf-8")
    new = re.sub(
        rf"^(FROM\s+{re.escape(base)}):[\w.-]+(@sha256:[a-f0-9]+)?",
        rf"\1:{ver}\2",
        text,
        flags=re.MULTILINE,
    )
    if new != text:
        p.write_text(new, encoding="utf-8")
        print(f"  updated {p}")
PY
fi

git add "$PIN_FILE" "${PLAN[@]}" 2>/dev/null || git add "$PIN_FILE"
git commit -m "[STACK BUMP] bump ${PKG} ${CURRENT} -> ${VER}"

echo
echo "────────────────────────────────────────────────────────"
echo "Done. Next steps:"
echo "  1. Run 'pnpm install --no-frozen-lockfile' (npm) or 'uv lock' (pip)."
echo "  2. Verify locally:"
echo "       pnpm dep:check"
echo "       uv run python scripts/check_stack_pin.py"
echo "  3. Run the V8 regression gate:"
echo "       uv run pytest packages/cost_engine/tests/regression_v8 -v"
echo "  4. Push the branch and open a PR."
echo "────────────────────────────────────────────────────────"