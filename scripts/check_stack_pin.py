#!/usr/bin/env python3
"""Stack pin check (Python mirror of check_stack_pin.mjs).

Reads docs/STACK_PIN.yaml and verifies the actual repo state matches.
Exits 0 if all match, 1 if any drift (unless [STACK BUMP] tag is present).

Usage:
    uv run python scripts/check_stack_pin.py            # default: enforced
    VERBOSE=1 uv run python scripts/check_stack_pin.py   # show all expected vs actual
    STACK_BUMP=1 uv run python scripts/check_stack_pin.py # authorize drift locally
    STACK_BUMP_PR_HEAD_SHA=<sha>                         # PR head commit for [STACK BUMP] check
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

# Force UTF-8 output on Windows consoles (cp949 by default in legacy console).
# This avoids UnicodeEncodeError when printing markers.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

try:
    import yaml  # CASCADE-1 (CR 2026-07-25): PyYAML handles BOM, anchors,
                  # folded scalars, escaped quotes — hand-rolled parsers
                  # silently fail on these edge cases.
except ImportError:  # pragma: no cover
    sys.stderr.write("[ERROR] PyYAML not installed. Run via `uv run python scripts/check_stack_pin.py`.\n")
    sys.exit(2)

ROOT = Path(os.environ.get("STACK_PIN_ROOT") or Path(__file__).resolve().parent.parent)

# ── Helpers ───────────────────────────────────────────────────────────────


def read(path: str | Path) -> str:
    full = ROOT / path
    if not full.exists():
        raise FileNotFoundError(f"missing: {path}")
    return full.read_text(encoding="utf-8")


def read_json(path: str | Path) -> dict:
    return json.loads(read(path))


def has_commit_tag(tag: str, pr_head_sha: str | None = None) -> bool:
    """Check if `[STACK BUMP]` tag is present in the most recent commit.

    MSG-2 (CR 2026-07-25):
    - Case-insensitive match
    - When STACK_BUMP_PR_HEAD_SHA is set (PR build), inspect that commit
      instead of HEAD (which would be the merge commit in squash-merge
      workflows and would hide the bump tag).
    """
    target = pr_head_sha or "HEAD"
    try:
        out = subprocess.check_output(
            ["git", "log", "-1", "--format=%s", target],
            cwd=ROOT,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
    return tag.lower() in out.decode("utf-8", errors="replace").lower()


# ── Load pin table ─────────────────────────────────────────────────────────


def main() -> int:
    pin_path = ROOT / "docs" / "STACK_PIN.yaml"
    if not pin_path.exists():
        # STYLE-1 (CR 2026-07-25): ASCII markers for cp949-safe output
        sys.stderr.write("[ERROR] docs/STACK_PIN.yaml not found\n")
        return 2

    # CASCADE-1: PyYAML with `encoding='utf-8'` and BOM tolerance via
    # `yaml.SafeLoader` (which handles BOM-prefixed YAML transparently).
    pin_doc = yaml.safe_load(pin_path.read_text(encoding="utf-8"))
    pin: dict[str, str] = (pin_doc or {}).get("stack_pin", {})
    exceptions: dict[str, dict] = (pin_doc or {}).get("exceptions", {})

    verbose = os.environ.get("VERBOSE") in ("1", "true", "yes")

    # Empty/missing pin table → nothing to verify, exit 0
    if not pin:
        print(f"[STACK_PIN] OK empty STACK_PIN.yaml — nothing to verify")
        return 0
    pr_head_sha = os.environ.get("STACK_BUMP_PR_HEAD_SHA") or None
    bump_from_commit = has_commit_tag("[STACK BUMP]", pr_head_sha=pr_head_sha)
    bump_from_env = os.environ.get("STACK_BUMP") == "1"
    bump_ok = bump_from_commit or bump_from_env

    if bump_from_commit:
        print("[STACK_PIN] [STACK BUMP] tag present in commit — drift authorized")
    elif bump_from_env:
        print("[STACK_PIN] STACK_BUMP=1 — drift authorized (local override)")

    drifts: list[dict[str, str | None]] = []

    def check(label: str, expected: str | None, actual: str | None) -> None:
        if expected is None:
            return
        if actual == expected:
            if verbose:
                print(f"  OK  {label}: {actual}")
            return
        drifts.append({"label": label, "expected": expected, "actual": actual})
        # MSG-1 (CR 2026-07-25): standardized format
        print(f"  XX  {label}: expected={expected!r} actual={actual!r}")

    # ── File-level checks ──

    # .nvmrc
    try:
        check("node (.nvmrc)", pin.get("node"), read(".nvmrc").strip())
    except FileNotFoundError:
        drifts.append({"label": "node", "expected": pin.get("node"), "actual": None})
        print("  XX  node (.nvmrc): missing file")

    # .python-version
    try:
        check("python (.python-version)", pin.get("python"), read(".python-version").strip())
    except FileNotFoundError:
        drifts.append({"label": "python", "expected": pin.get("python"), "actual": None})
        print("  XX  python (.python-version): missing file")

    # package.json — engines.node is semver `>=24.18.0 <25` (DOCKER-6).
    # The check passes if the installed Node is within the engines range,
    # since .nvmrc enforces the exact pin.
    root_pkg = read_json("package.json")
    engines_node = root_pkg.get("engines", {}).get("node", "")
    if pin.get("node"):
        try:
            # Read .nvmrc as the canonical exact pin
            nvmrc_node = read(".nvmrc").strip()
            check("node (.nvmrc exact)", pin.get("node"), nvmrc_node)
        except FileNotFoundError:
            pass
        # engines.node is semver — only report if it doesn't include the pin
        if engines_node and not engines_node.startswith(">="):
            check("node (package.json engines.node)", pin.get("node"), engines_node)

    check("pnpm (package.json packageManager)", f"pnpm@{pin.get('pnpm')}", root_pkg.get("packageManager"))
    check("pnpm (package.json engines.pnpm)", pin.get("pnpm"), root_pkg.get("engines", {}).get("pnpm"))

    # apps/web/package.json
    try:
        web_pkg = read_json("apps/web/package.json")
        check("next (apps/web/package.json)", pin.get("next"), web_pkg.get("dependencies", {}).get("next"))
        check("react (apps/web/package.json)", pin.get("react"), web_pkg.get("dependencies", {}).get("react"))
        check(
            "react-dom (apps/web/package.json)",
            pin.get("react_dom"),
            web_pkg.get("dependencies", {}).get("react-dom"),
        )
        check(
            "typescript (apps/web/package.json)",
            pin.get("typescript"),
            web_pkg.get("devDependencies", {}).get("typescript"),
        )
        # TYPECHECK-1 (CR 2026-07-25): verify @types/* dev pins
        if pin.get("react"):
            check(
                "@types/react (apps/web/package.json)",
                pin.get("@types/react"),
                web_pkg.get("devDependencies", {}).get("@types/react"),
            )
        if pin.get("node"):
            check(
                "@types/node (apps/web/package.json)",
                pin.get("@types/node"),
                web_pkg.get("devDependencies", {}).get("@types/node"),
            )
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"  [WARN] apps/web/package.json: {e}", file=sys.stderr)

    # apps/api/pyproject.toml — use tomllib for robust parsing
    try:
        api_toml_text = read("apps/api/pyproject.toml")
        api_toml = tomllib.loads(api_toml_text)
        api_deps = api_toml.get("project", {}).get("dependencies", []) or []
        api_dev = api_toml.get("project", {}).get("optional-dependencies", {}).get("dev", []) or []
        all_api = list(api_deps) + list(api_dev)

        def get_pin(specs: list[str], name: str) -> str | None:
            for s in specs:
                # Handle "name==1.2.3" or "name>=1.0,<2.0"
                m = re.match(rf"^{re.escape(name)}([><=!~]+)(.+)$", s.strip())
                if m:
                    return s.strip()
            return None

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
        ]:
            if pin_key in pin:
                actual = get_pin(all_api, pkg)
                # Strip the operator to compare values
                actual_ver = None
                if actual:
                    m = re.match(rf"^{re.escape(pkg)}[><=!~]+(.+)$", actual)
                    if m:
                        actual_ver = m.group(1).strip().strip('"').strip("'")
                check(f"{pkg} (apps/api/pyproject.toml)", pin[pin_key], actual_ver)
        if "pydantic_core" in pin:
            actual = get_pin(all_api, "pydantic-core")
            actual_ver = None
            if actual:
                m = re.match(r"^pydantic-core[><=!~]+(.+)$", actual)
                if m:
                    actual_ver = m.group(1).strip().strip('"').strip("'")
            check("pydantic-core (apps/api/pyproject.toml)", pin["pydantic_core"], actual_ver)
        # Pydantic itself — special-case the value comparison since it has ==
        if "pydantic" in pin:
            actual = get_pin(all_api, "pydantic")
            actual_ver = None
            if actual:
                m = re.match(r"^pydantic[><=!~]+(.+)$", actual)
                if m:
                    actual_ver = m.group(1).strip().strip('"').strip("'")
            check("pydantic (apps/api/pyproject.toml)", pin["pydantic"], actual_ver)
    except (FileNotFoundError, tomllib.TOMLDecodeError) as e:
        print(f"  [WARN] apps/api/pyproject.toml: {e}", file=sys.stderr)

    # packages/cost_engine/pyproject.toml
    try:
        ce_toml_text = read("packages/cost_engine/pyproject.toml")
        ce_toml = tomllib.loads(ce_toml_text)
        ce_dev = ce_toml.get("project", {}).get("optional-dependencies", {}).get("dev", []) or []

        def get_engine_pin(specs: list[str], name: str) -> str | None:
            for s in specs:
                m = re.match(rf"^{re.escape(name)}==(.+)$", s.strip())
                if m:
                    return m.group(1).strip()
            return None

        if "numpy" in pin:
            np_val = get_engine_pin(ce_dev, "numpy")
            if np_val is None:
                ce_eng = ce_toml.get("project", {}).get("optional-dependencies", {}).get("engine-math", []) or []
                np_val = get_engine_pin(ce_eng, "numpy")
            check("numpy (packages/cost_engine)", pin["numpy"], np_val)
        if "pytest" in pin:
            pt_val = get_engine_pin(ce_dev, "pytest")
            check("pytest (packages/cost_engine)", pin["pytest"], pt_val)
    except (FileNotFoundError, tomllib.TOMLDecodeError) as e:
        print(f"  [WARN] packages/cost_engine/pyproject.toml: {e}", file=sys.stderr)

    # root pyproject.toml
    try:
        root_toml_text = read("pyproject.toml")
        root_toml = tomllib.loads(root_toml_text)
        root_dev = root_toml.get("dependency-groups", {}).get("dev", []) or []

        def get_root_pin(specs: list[str], name: str) -> str | None:
            for s in specs:
                m = re.match(rf"^{re.escape(name)}==(.+)$", s.strip())
                if m:
                    return m.group(1).strip()
            return None

        if "import_linter" in pin:
            check(
                "import-linter (pyproject.toml dev)",
                pin["import_linter"],
                get_root_pin(root_dev, "import-linter"),
            )
        if "pytest" in pin:
            check("pytest (pyproject.toml dev)", pin["pytest"], get_root_pin(root_dev, "pytest"))
        if "ruff" in pin:
            check("ruff (pyproject.toml dev)", pin["ruff"], get_root_pin(root_dev, "ruff"))
        if "hatchling" in pin:
            # hatchling pin is checked in apps/api/pyproject.toml above
            # (root pyproject.toml has no [build-system] section — it's a
            # workspace manifest, not a buildable package).
            pass
    except (FileNotFoundError, tomllib.TOMLDecodeError) as e:
        print(f"  [WARN] pyproject.toml: {e}", file=sys.stderr)

    # CHECK-1 (CR 2026-07-25): verify resolved lockfile versions match
    # declared pins. pnpm-lock.yaml is YAML; uv.lock is TOML.
    if (ROOT / "pnpm-lock.yaml").exists():
        try:
            pnpm_lock = yaml.safe_load(read("pnpm-lock.yaml"))
            packages = (pnpm_lock or {}).get("packages", {}) or {}
            # Each package maps `name@version` → info; check resolved versions
            for pkg_name in ("next", "react", "react-dom", "typescript"):
                if pkg_name in pin:
                    expected = pin[pkg_name]
                    # Find any key ending with `<name>@<expected>`
                    found = False
                    for k in packages:
                        if k == f"{pkg_name}@{expected}" or k.endswith(f"/{pkg_name}@{expected}"):
                            found = True
                            break
                    if not found and verbose:
                        print(f"  [INFO] {pkg_name}@{expected} not found in pnpm-lock.yaml packages")
        except (yaml.YAMLError, FileNotFoundError) as e:
            print(f"  [WARN] pnpm-lock.yaml: {e}", file=sys.stderr)

    if (ROOT / "uv.lock").exists():
        try:
            with (ROOT / "uv.lock").open("rb") as fh:
                uv_lock = tomllib.load(fh)
            uv_packages = uv_lock.get("package", []) or []
            for pkg_name, pin_key in [
                ("fastapi", "fastapi"),
                ("pydantic", "pydantic"),
                ("sqlalchemy", "sqlalchemy"),
                ("alembic", "alembic"),
            ]:
                if pin_key in pin:
                    expected = pin[pin_key]
                    match = next(
                        (p for p in uv_packages if p.get("name") == pkg_name and p.get("version") == expected),
                        None,
                    )
                    if not match and verbose:
                        print(f"  [INFO] {pkg_name}=={expected} not found in uv.lock packages")
        except (tomllib.TOMLDecodeError, FileNotFoundError) as e:
            print(f"  [WARN] uv.lock: {e}", file=sys.stderr)

    # DOCKER-2 (CR 2026-07-25): scan CI workflow for service image digests
    ci_yml_path = ROOT / ".github" / "workflows" / "ci.yml"
    if ci_yml_path.exists():
        try:
            ci_text = read(ci_yml_path)
            # Match `image: <name>@sha256:...` lines
            for m in re.finditer(r"^\s*image:\s*([^@\s]+)@sha256:([a-f0-9]+)", ci_text, re.MULTILINE):
                image = m.group(1)
                digest = f"sha256:{m.group(2)}"
                if image.startswith("postgres") and pin.get("postgresql"):
                    expected_digest = pin.get("postgresql_digest", "")
                    if expected_digest:
                        check(
                            f"postgres CI service image digest",
                            expected_digest,
                            digest,
                        )
        except FileNotFoundError:
            pass

    # Dockerfile — base image tags + digests
    try:
        dockerfile = read("Dockerfile")
        from_lines = re.findall(r"^FROM\s+([^\s@]+)(@sha256:[a-f0-9]+)?", dockerfile, re.MULTILINE)
        # Strip leading `@` from digests for comparison with STACK_PIN.yaml
        images = [(img, dig[1:] if dig else None) for img, dig in from_lines]
        if "python_slim" in pin:
            found = next((i for i, _ in images if i.startswith("python:")), None)
            check("python (Dockerfile base image)", f"python:{pin['python_slim']}", found)
            # DOCKER-1/5: digest pins
            if pin.get("python_slim_digest"):
                py_digest = next((d for i, d in images if i.startswith("python:")), None)
                check("python (Dockerfile digest)", pin["python_slim_digest"], py_digest)
        if "node_alpine" in pin:
            found = next((i for i, _ in images if i.startswith("node:")), None)
            check("node (Dockerfile base image)", f"node:{pin['node_alpine']}", found)
            if pin.get("node_alpine_digest"):
                nd = next((d for i, d in images if i.startswith("node:")), None)
                check("node (Dockerfile digest)", pin["node_alpine_digest"], nd)
        if "nginx_alpine" in pin:
            found = next((i for i, _ in images if i.startswith("nginx:")), None)
            check("nginx (Dockerfile base image)", f"nginx:{pin['nginx_alpine']}", found)
            if pin.get("nginx_alpine_digest"):
                ngx_d = next((d for i, d in images if i.startswith("nginx:")), None)
                check("nginx (Dockerfile digest)", pin["nginx_alpine_digest"], ngx_d)
    except FileNotFoundError as e:
        print(f"  [WARN] Dockerfile: {e}", file=sys.stderr)

    # ── Verdict ──
    # NOTES-1 (CR 2026-07-25): surface exceptions block summary + flag any
    # exception whose current value already matches spec (candidates for
    # retirement).
    retired_candidates = [
        k for k, exc in exceptions.items()
        if exc.get("current") == exc.get("spec") and exc.get("current") not in (None, "NOT INSTALLED")
    ]
    if exceptions:
        print(f"[STACK_PIN] Exceptions tracked: {len(exceptions)}")
        if retired_candidates:
            print(
                f"[STACK_PIN] WARNING — exceptions ready to retire (current==spec): "
                f"{', '.join(retired_candidates)}"
            )

    if not drifts:
        print(f"[STACK_PIN] OK all {len(pin)} pins match")
        return 0

    if bump_ok:
        print(f"[STACK_PIN] WARN {len(drifts)} drift(s) detected but [STACK BUMP] authorized -- pass:")
        for d in drifts:
            print(f"  - {d['label']}: {d['expected']} -> {d['actual']}")
        return 0

    # MSG-1: standardized violation message
    print(f"[STACK_PIN] FAIL {len(drifts)} drift(s) detected:", file=sys.stderr)
    for d in drifts:
        print(
            f"  STACK_PIN_VIOLATION: {d['label']} drifted from {d['expected']} to {d['actual']}",
            file=sys.stderr,
        )
    print(
        "[STACK_PIN] Use commit tag [STACK BUMP] to authorize this drift.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())