#!/usr/bin/env python3
"""TypeScript drift detector (cj-style 209 — AD-14 Detection Surface EXTENSION).

Captures the current ``tsc --noEmit`` error counts (by error code) for each
``tsconfig.json`` in the repo and compares to a committed baseline JSON snapshot.

Background (cj-style 204 cleanup sprint):
  Pre-existing 21 tsc errors accumulated silently between sprints. cj-204
  manually cleaned them up, but the *drift* mechanism (new errors introduced
  between sprints) had no automated detection. This script is the detection.

Baseline:
  ``docs/architecture-decisions/AD-14-tsc-baseline.json`` — committed snapshot
  of total error counts and per-code breakdown per tsconfig. First run creates
  the baseline (no drift possible). Subsequent runs compare against it.

Exit codes:
  0 — no drift (counts match baseline, or baseline freshly created)
  1 — drift detected (new error code or count increase)
  2 — environment / setup error (tsc not invokable, tsconfig missing)

Environment:
  STACK_PIN_ROOT — repo root (default: parent of this script)
  UPDATE_TSC_BASELINE=1 — overwrite baseline with current counts (used after
    intentional error cleanup, e.g. cj-204 cleanup sprint pattern)
  VERBOSE=1 — show per-error-code breakdown

CR 11-3 honest boundary:
  If tsc binary is not invokable (cold checkout without ``pnpm install``),
  the script reports ``NOT INVOKABLE`` rather than over-claiming drift.
  Drift detection is meaningful only when tsc actually runs.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Force UTF-8 output on Windows consoles (cp949 by default).
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

ROOT = Path(os.environ.get("STACK_PIN_ROOT") or Path(__file__).resolve().parent.parent)
BASELINE_PATH = ROOT / "docs" / "architecture-decisions" / "AD-14-tsc-baseline.json"
VERBOSE = os.environ.get("VERBOSE") == "1"
UPDATE_BASELINE = os.environ.get("UPDATE_TSC_BASELINE") == "1"

# pnpm 9.x content-addressed store: typescript is hoisted under
# node_modules/.pnpm/typescript@<version>/node_modules/typescript/lib/tsc.js
TSC_CANDIDATES = [
    ROOT / "node_modules" / ".pnpm" / "typescript@5.9.3" / "node_modules" / "typescript" / "lib" / "tsc.js",
    ROOT / "node_modules" / ".ignored" / "typescript" / "bin" / "tsc",  # cj-208 pattern (legacy)
]

# tsconfig targets under drift watch.
TSCONFIG_TARGETS = [
    ("apps/web", ROOT / "apps" / "web" / "tsconfig.json"),
]


# ── Helpers ───────────────────────────────────────────────────────────────


def _find_tsc() -> Path | None:
    for candidate in TSC_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def _parse_tsc_output(stderr: str) -> dict[str, int]:
    """Return {TS_error_code: count} from ``tsc --noEmit`` stderr."""
    counts: dict[str, int] = {}
    # Format: ``path/to/file.ts(line,col): error TS2307: Cannot find module 'foo'.``
    pattern = re.compile(r"error\s+(TS\d+):")
    for match in pattern.finditer(stderr):
        code = match.group(1)
        counts[code] = counts.get(code, 0) + 1
    return counts


def _run_tsc(tsc_js: Path, tsconfig: Path) -> tuple[dict[str, int], str]:
    """Run tsc and return (counts_by_code, raw_stderr).

    Exit code is intentionally ignored — tsc returns non-zero when it finds
    errors, which is the normal case this script is designed to analyze.
    """
    proc = subprocess.run(
        ["node", str(tsc_js), "--noEmit", "-p", str(tsconfig)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    return _parse_tsc_output(proc.stderr or ""), proc.stderr or ""


def _read_baseline() -> dict | None:
    if not BASELINE_PATH.exists():
        return None
    try:
        return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        sys.stderr.write(f"[WARN] baseline JSON malformed: {BASELINE_PATH}\n")
        return None


def _write_baseline(snapshot: dict) -> None:
    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_PATH.write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _tsc_version(tsc_js: Path) -> str:
    proc = subprocess.run(
        ["node", str(tsc_js), "--version"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
    )
    return (proc.stdout or "").strip() or "unknown"


# ── Main ───────────────────────────────────────────────────────────────────


def main() -> int:
    tsc_js = _find_tsc()
    if tsc_js is None:
        sys.stderr.write(
            "[TSC_DRIFT] NOT INVOKABLE — tsc binary not found at any candidate path.\n"
            "  Candidates:\n"
            + "\n".join(f"    - {c}" for c in TSC_CANDIDATES)
            + "\n  Run `pnpm install --frozen-lockfile` to install typescript, then re-run.\n"
        )
        return 2

    sys.stdout.write(f"[TSC_DRIFT] Using tsc: {tsc_js}\n")

    current: dict[str, dict] = {}
    drift_details: list[str] = []

    for label, tsconfig in TSCONFIG_TARGETS:
        if not tsconfig.exists():
            sys.stdout.write(f"[TSC_DRIFT] SKIP {label} (missing {tsconfig.relative_to(ROOT)})\n")
            continue
        counts, raw = _run_tsc(tsc_js, tsconfig)
        total = sum(counts.values())
        current[label] = {"total": total, "by_code": dict(sorted(counts.items()))}
        sys.stdout.write(
            f"[TSC_DRIFT] {label}: {total} errors"
            + (f" ({', '.join(f'{k}={v}' for k, v in sorted(counts.items()))})" if counts else "")
            + "\n"
        )
        if VERBOSE and raw:
            sys.stdout.write(raw)

    if not current:
        sys.stderr.write("[TSC_DRIFT] No tsconfig targets checked — nothing to compare.\n")
        return 2

    snapshot = {
        "schema_version": 1,
        "captured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),  # noqa: UP017
        "tsc_version": _tsc_version(tsc_js),
        "targets": current,
    }

    baseline = _read_baseline()
    if baseline is None:
        sys.stdout.write(
            f"[TSC_DRIFT] No baseline found — writing initial snapshot to {BASELINE_PATH.relative_to(ROOT)}\n"
        )
        _write_baseline(snapshot)
        sys.stdout.write("[TSC_DRIFT] OK baseline established (no drift possible on first run)\n")
        return 0

    if UPDATE_BASELINE:
        sys.stdout.write("[TSC_DRIFT] UPDATE_TSC_BASELINE=1 — overwriting baseline with current counts.\n")
        _write_baseline(snapshot)
        sys.stdout.write(f"[TSC_DRIFT] OK baseline updated at {BASELINE_PATH.relative_to(ROOT)}\n")
        return 0

    # Compare current vs baseline.
    base_targets = baseline.get("targets", {})
    drift = False
    for label, cur_counts in current.items():
        base_counts = base_targets.get(label, {"total": 0, "by_code": {}})
        base_total = base_counts.get("total", 0)
        base_by_code = base_counts.get("by_code", {})
        cur_total = cur_counts["total"]
        cur_by_code = cur_counts["by_code"]

        if cur_total > base_total:
            drift = True
            new_codes = {k: v for k, v in cur_by_code.items() if k not in base_by_code}
            increased = {
                k: (base_by_code.get(k, 0), v)
                for k, v in cur_by_code.items()
                if v > base_by_code.get(k, 0)
            }
            detail_parts = []
            if new_codes:
                detail_parts.append(f"new codes: {new_codes}")
            if increased:
                detail_parts.append(
                    "increased: " + ", ".join(f"{k} {v[0]}→{v[1]}" for k, v in increased.items())
                )
            detail = "; ".join(detail_parts) or f"total {base_total}→{cur_total}"
            drift_details.append(f"{label}: +{cur_total - base_total} errors ({detail})")
        elif cur_total < base_total:
            # Error count went down — improvement. Note but don't fail.
            sys.stdout.write(
                f"[TSC_DRIFT] {label}: {base_total}→{cur_total} (improvement; "
                "consider UPDATE_TSC_BASELINE=1 to commit new baseline)\n"
            )

    if drift:
        sys.stdout.write("\n[TSC_DRIFT] FAIL — drift detected:\n")
        for d in drift_details:
            sys.stdout.write(f"  - {d}\n")
        sys.stdout.write(
            "\n  Investigate the new errors above. If intentional (e.g. cleanup sprint),\n"
            "  re-run with UPDATE_TSC_BASELINE=1 to commit the new baseline.\n"
        )
        return 1

    sys.stdout.write(
        f"\n[TSC_DRIFT] OK no drift vs baseline "
        f"(captured {baseline.get('captured_at', 'unknown')})\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
