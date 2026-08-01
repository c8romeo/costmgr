"""tests.integration.test_m2_input_label_consistency — drift guard for m2_input labels.

Story 3.1 — Task 6.3 + Story 3.2 — Task 4.2.

The canonical six-stream monthly input vocabulary AND the FTE precision
pipeline live in TWO places:

  - `packages/services/m2_input/{stream_completion,labor_conversion}.py`
    (Python, source of truth)
  - `apps/web/lib/{menu-config,l2-input-fte}.ts`
    (TypeScript mirrors, drift-prevention via this test)

This test guards against drift across:

  Stream vocabulary (Story 3.1 — Task 6.3):
  1. The set of MonthlyInputStream values matches.
  2. The Korean label dictionary matches (PRD §8.M2(b)).
  3. The per-industry visibility map matches (PRD §8.M2(b) —
     service hides production).

  FTE precision pipeline (Story 3.2 — Task 4.2):
  4. `PAY_TYPE_VALUES` (TS) ↔ `PayType` enum (Py)
  5. `DEFAULT_PAYROLL` 4 fields match (regex parse + tolerance)
  6. `computeFteForDaily(3, 8, 22)` returns "1.09" (executed via Node)
  7. `computeFteWageForDaily(150_000, 3, 8)` returns 3_600_000
     (NOT 1.09 × 2_500_000 — direct sum, executed via Node)
  8. `mergePayrollSettings` partial override returns merged object

The cross-language tests #6/#7/#8 actually EXECUTE the TS code via
Node (v24+) with the `decimal.js` polyfill resolved through `cd apps/web
&& npm install`. Without Node, the test falls back to regex-based
structural assertions (still catches drift, just less precise).

The regex-based tests (Story 3.1) remain hermetic to the engine
workspace per Epic 2 회고 W4 — they don't need Node / ts-node.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from packages.services.m0_onboarding.industry_menu import Industry
from packages.services.m2_input.labor_conversion import (
    DEFAULT_PAYROLL,
    PayType,
    compute_fte_for_daily,
    compute_fte_wage_for_daily,
    merge_payroll_settings,
)
from packages.services.m2_input.stream_completion import (
    STREAM_LABELS_KO,
    STREAMS_FOR_INDUSTRY,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
TS_PATH = REPO_ROOT / "apps" / "web" / "lib" / "menu-config.ts"
TS_L2_FTE_PATH = REPO_ROOT / "apps" / "web" / "lib" / "l2-input-fte.ts"
TS_L2_WARNINGS_PATH = REPO_ROOT / "apps" / "web" / "lib" / "l2-input-warnings.ts"


# ── Node availability check (Story 3.2 — Task 4.2) ─────────────
_NODE_AVAILABLE = shutil.which("node") is not None
_skip_no_node = pytest.mark.skipif(
    not _NODE_AVAILABLE, reason="Node v24+ required for cross-language exec tests"
)


def _read_ts_source() -> str:
    """Read the TS file as text, stripping line + block comments.

    F-25 (Story 0.2 lesson): strip comments so doc-comment text doesn't
    satisfy label-matching regexes.
    """
    if not TS_PATH.exists():
        pytest.fail(
            f"Required TypeScript mirror not found at {TS_PATH}. "
            "Story 3.1 T5.5 must create this file alongside the Python module."
        )
    raw = TS_PATH.read_text(encoding="utf-8")
    no_block = re.sub(r"/\*.*?\*/", "", raw, flags=re.DOTALL)
    return re.sub(r"^\s*//.*$", "", no_block, flags=re.MULTILINE)


def _extract_ts_stream_values(ts_src: str) -> list[str]:
    """Extract the array literal under `export const MONTHLY_INPUT_STREAM_VALUES = [...]`."""
    m = re.search(
        r"export\s+const\s+MONTHLY_INPUT_STREAM_VALUES\s*=\s*\[(.*?)\]\s*as\s+const",
        ts_src,
        flags=re.DOTALL,
    )
    if not m:
        pytest.fail(
            "MONTHLY_INPUT_STREAM_VALUES declaration not found in TS mirror"
        )
    body = m.group(1)
    return re.findall(r'"([a-z_]+)"', body)


def _extract_ts_dict(ts_src: str, name: str) -> dict[str, str]:
    """Extract a `name: Record<...>` block — keys are quoted strings.

    Handles the `Record<MonthlyInputStream, string> = { key: "label", ... }` shape.
    """
    m = re.search(
        rf"export\s+const\s+{name}\s*:\s*Record<[^>]+>\s*=\s*\{{(.*?)\}};",
        ts_src,
        flags=re.DOTALL,
    )
    if not m:
        pytest.fail(f"{name} declaration not found in TS mirror")
    body = m.group(1)
    pairs = re.findall(r'([a-z_]+)\s*:\s*"([^"]+)"', body)
    return dict(pairs)


def _extract_ts_visibility(ts_src: str, name: str) -> dict[str, list[str]]:
    """Extract `INDUSTRY_VISIBLE_STREAMS: Record<Industry, readonly MonthlyInputStream[]>`.

    Returns {industry_name: [stream, ...]} for each industry.
    """
    m = re.search(
        rf"export\s+const\s+{re.escape(name)}\s*:\s*Record<[^>]+>\s*=\s*\{{(.*?)\}};",
        ts_src,
        flags=re.DOTALL,
    )
    if not m:
        pytest.fail(f"{name} declaration not found in TS mirror")
    body = m.group(1)
    # Match each industry block: industry_name: ["a", "b", ...]
    industry_blocks = re.findall(
        r"([a-z_]+)\s*:\s*\[([^\]]+)\]",
        body,
    )
    out: dict[str, list[str]] = {}
    for industry_name, streams in industry_blocks:
        stream_list = re.findall(r'"([a-z_]+)"', streams)
        out[industry_name] = stream_list
    return out


# ── Test cases ────────────────────────────────────────────────
def test_stream_values_match_python() -> None:
    """MONTHLY_INPUT_STREAM_VALUES (TS) == STREAM_ORDER (Py, canonical)."""
    ts_src = _read_ts_source()
    ts_values = sorted(_extract_ts_stream_values(ts_src))
    from packages.services.m2_input.stream_completion import STREAM_ORDER

    py_values = sorted(STREAM_ORDER)
    assert ts_values == py_values, (
        f"Stream value drift: TS={ts_values!r}, Py={py_values!r}"
    )


def test_stream_label_ko_matches_python() -> None:
    """Korean labels match (PRD §8.M2(b) — 주문/생산/판매/구매/경비/인원)."""
    ts_src = _read_ts_source()
    ts_labels = _extract_ts_dict(ts_src, "MONTHLY_INPUT_STREAM_LABEL_KO")
    assert ts_labels == dict(STREAM_LABELS_KO), (
        f"Label drift: TS={ts_labels!r}, Py={dict(STREAM_LABELS_KO)!r}"
    )


def test_visible_streams_manufacturing_matches_python() -> None:
    """제조업은 6 stream 모두 노출 (PRD §8.M2(b))."""
    ts_src = _read_ts_source()
    ts_visibility = _extract_ts_visibility(ts_src, "INDUSTRY_VISIBLE_STREAMS")
    ts_mfg = sorted(ts_visibility.get("manufacturing", []))
    py_mfg = sorted(STREAMS_FOR_INDUSTRY[Industry.MANUFACTURING])
    assert ts_mfg == py_mfg, (
        f"Manufacturing visibility drift: TS={ts_mfg!r}, Py={py_mfg!r}"
    )


def test_visible_streams_service_excludes_production() -> None:
    """서비스업은 5 stream (production hidden — PRD §8.M2(b))."""
    ts_src = _read_ts_source()
    ts_visibility = _extract_ts_visibility(ts_src, "INDUSTRY_VISIBLE_STREAMS")
    ts_service = sorted(ts_visibility.get("service", []))
    py_service = sorted(STREAMS_FOR_INDUSTRY[Industry.SERVICE])
    assert ts_service == py_service, (
        f"Service visibility drift: TS={ts_service!r}, Py={py_service!r}"
    )
    # Defense in depth — explicitly check production absence.
    assert "production" not in ts_service
    assert "production" not in py_service


def test_visible_streams_count_matches_across_industries() -> None:
    """모든 industry에서 stream 수가 Python과 일치."""
    ts_src = _read_ts_source()
    ts_visibility = _extract_ts_visibility(ts_src, "INDUSTRY_VISIBLE_STREAMS")
    for industry in Industry:
        ts_count = len(ts_visibility.get(industry.value, []))
        py_count = len(STREAMS_FOR_INDUSTRY[industry])
        assert ts_count == py_count, (
            f"{industry.value} stream count drift: "
            f"TS={ts_count}, Py={py_count}"
        )


# ── Story 3.2 — FTE precision cross-language parity (Task 4.2) ─
def _read_ts_l2_fte_source() -> str:
    """Read the `l2-input-fte.ts` mirror as text (F-25: strip comments)."""
    if not TS_L2_FTE_PATH.exists():
        pytest.fail(
            f"Required TS mirror not found at {TS_L2_FTE_PATH}. "
            "Story 3.2 T4.1 must create this file alongside the Python module."
        )
    raw = TS_L2_FTE_PATH.read_text(encoding="utf-8")
    no_block = re.sub(r"/\*.*?\*/", "", raw, flags=re.DOTALL)
    return re.sub(r"^\s*//.*$", "", no_block, flags=re.MULTILINE)


def _exec_ts_module(
    ts_src: str, *, fn_name: str, args: list, _cwd: Path = REPO_ROOT
) -> str:
    """Execute a TS function via Node v24 and return stdout JSON.

    Story 3.2 Task 4.2 — runs the real TS code (no regex guessing)
    against Node v24+ and pipes the serialized result back through JSON.
    The TS source is concatenated as `import { ... } from "<file>"`
    so it picks up `decimal.js` from `apps/web/node_modules`.
    """
    runner = f"""
import * as lib from "./apps/web/lib/l2-input-fte.ts";
const result = lib.{fn_name}(...{json.dumps(args)});
console.log(JSON.stringify(result));
"""
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", runner],
        cwd=_cwd,
        capture_output=True,
        text=True,
        timeout=10,
        shell=False,
    )
    if completed.returncode != 0:
        pytest.fail(
            f"Node execution failed for {fn_name}: {completed.stderr}"
        )
    return completed.stdout.strip()


def test_pay_type_values_match_python() -> None:
    """PAY_TYPE_VALUES (TS) ↔ PayType enum (Py). Regex-based structural check."""
    ts_src = _read_ts_l2_fte_source()
    m = re.search(
        r"export\s+const\s+PAY_TYPE_VALUES\s*=\s*\[(.*?)\]\s*as\s+const",
        ts_src,
        flags=re.DOTALL,
    )
    if not m:
        pytest.fail("PAY_TYPE_VALUES declaration not found in TS mirror")
    ts_values = sorted(re.findall(r'"([a-z_]+)"', m.group(1)))
    py_values = sorted(p.value for p in PayType)
    assert ts_values == py_values, (
        f"PayType value drift: TS={ts_values!r}, Py={py_values!r}"
    )


def test_default_payroll_matches_python() -> None:
    """DEFAULT_PAYROLL 4 fields match between TS and Py."""
    ts_src = _read_ts_l2_fte_source()
    # numeric extraction from `monthlySalaryBasisKrw: 2_500_000n`
    basis_match = re.search(
        r"monthlySalaryBasisKrw:\s*([\d_]+)n", ts_src
    )
    if not basis_match:
        pytest.fail("DEFAULT_PAYROLL.monthlySalaryBasisKrw not found in TS")
    ts_basis = int(basis_match.group(1).replace("_", ""))
    assert ts_basis == DEFAULT_PAYROLL.monthly_salary_basis_krw, (
        f"monthlySalaryBasisKrw drift: TS={ts_basis}, "
        f"Py={DEFAULT_PAYROLL.monthly_salary_basis_krw}"
    )

    workdays_match = re.search(r"workdaysInMonth:\s*(\d+)", ts_src)
    assert workdays_match and int(
        workdays_match.group(1)
    ) == DEFAULT_PAYROLL.workdays_in_month, (
        f"workdaysInMonth drift: TS={workdays_match.group(1) if workdays_match else None}, "
        f"Py={DEFAULT_PAYROLL.workdays_in_month}"
    )

    hours_match = re.search(r"standardMonthlyHours:\s*(\d+)", ts_src)
    assert hours_match and int(
        hours_match.group(1)
    ) == DEFAULT_PAYROLL.standard_monthly_hours, (
        f"standardMonthlyHours drift: TS={hours_match.group(1) if hours_match else None}, "
        f"Py={DEFAULT_PAYROLL.standard_monthly_hours}"
    )

    # Company burden rate — string representation tolerance (TS Decimal
    # serializes the same as Python Decimal("0.115")).
    rate_match = re.search(
        r'companyBurdenRate:\s*new\s+Decimal\("([\d.]+)"\)', ts_src
    )
    assert rate_match, "companyBurdenRate default not found in TS"
    assert rate_match.group(1) == str(DEFAULT_PAYROLL.company_burden_rate), (
        f"companyBurdenRate drift: TS={rate_match.group(1)}, "
        f"Py={DEFAULT_PAYROLL.company_burden_rate}"
    )


@_skip_no_node
def test_compute_fte_for_daily_matches_python() -> None:
    """3×8/22 → "1.09" — Python result string == TS result string.

    Banker's rounding tolerance: both sides round half-even.
    TS exposes `computeFteForDaily(workers, daysPerWorker, workdaysInMonth)`
    as an ergonomic 3-arg form (workdays only), while Python takes the
    full `PayrollSettings` NamedTuple.
    """
    py_result = str(compute_fte_for_daily(3, 8, DEFAULT_PAYROLL))
    ts_src = _read_ts_l2_fte_source()
    ts_result = _exec_ts_module(
        ts_src, fn_name="computeFteForDaily", args=[3, 8, 22]
    )
    # TS may serialize Decimal as either number or string — coerce both
    # to string for comparison.
    if isinstance(ts_result, str):
        try:
            ts_value = json.loads(ts_result)
            ts_serialized = str(ts_value) if ts_value is not None else ""
        except json.JSONDecodeError:
            ts_serialized = ts_result
    else:
        ts_serialized = str(ts_result)
    assert py_result == "1.09", f"Python sanity failed: {py_result!r}"
    # Allow Decimal serializes as Decimal string ("1.09") or raw "1.09"
    assert ts_serialized in ("1.09", '"1.09"'), (
        f"FTE daily drift: Py={py_result!r}, TS={ts_serialized!r}"
    )


@_skip_no_node
def test_compute_fte_wage_for_daily_direct_sum() -> None:
    """3 × 8 × 150_000 = 3_600_000 (direct sum, NOT basis 환산).

    The TS code MUST NOT multiply `dailyWageKrw` by
    `monthlySalaryBasisKrw` — that's the basis 환산 path, only valid
    for monthly mode. This drift sentinel catches the most likely
    LLM mistake (regression of `compute_fte_wage_krw`).
    """
    py_result = compute_fte_wage_for_daily(150_000, 3, 8)
    assert py_result == 3_600_000  # sanity check Python side first

    # Node: BigInt is not JSON-serializable; wrap result with `.toString()`
    # before stringify. Use a custom replacer pattern.
    runner = """
import * as lib from "./apps/web/lib/l2-input-fte.ts";
const result = lib.computeFteWageForDaily(150000n, 3, 8);
console.log(result.toString());
"""
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", runner],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
        shell=False,
    )
    if completed.returncode != 0:
        pytest.fail(
            f"Node execution failed: {completed.stderr}"
        )
    ts_result = int(completed.stdout.strip())
    assert ts_result == 3_600_000, (
        f"TS daily wage drift: expected 3_600_000, got {ts_result}"
    )
    # And the wrong (basis 환산) value: 1.09 × 2_500_000 ≈ 2_725_000
    # MUST NOT match — confirms the direct-sum semantic is preserved.
    assert ts_result != 2_725_000


@_skip_no_node
def test_merge_payroll_settings_partial_override() -> None:
    """Partial override: only `workdays_in_month=20` (Py snake_case) /
    `workdaysInMonth=20` (TS camelCase) should preserve the other 3
    fields at their default values. Cross-language parity: same input
    → same result (modulo case-sensitivity).
    """
    # Python: snake_case keys (canonical, matches tenant_settings JSONB shape)
    py_override = {"workdays_in_month": 20}
    py_result = merge_payroll_settings(py_override)
    assert (
        py_result.monthly_salary_basis_krw
        == DEFAULT_PAYROLL.monthly_salary_basis_krw
    )
    assert py_result.workdays_in_month == 20  # overridden
    assert py_result.company_burden_rate == DEFAULT_PAYROLL.company_burden_rate
    # Python sanity: monthly_salary_basis_krw unchanged
    assert (
        py_result.monthly_salary_basis_krw
        == DEFAULT_PAYROLL.monthly_salary_basis_krw
    )
    assert py_result.workdays_in_month == 20  # overridden
    assert py_result.company_burden_rate == DEFAULT_PAYROLL.company_burden_rate
    # TS — execute with snake_case → camelCase conversion is automatic
    # because TS accepts both (we serialize override as camelCase keys).
    ts_src = _read_ts_l2_fte_source()
    ts_override = json.dumps({"workdaysInMonth": 20})
    runner = f"""
import * as lib from "./apps/web/lib/l2-input-fte.ts";
const override = {ts_override};
const result = lib.mergePayrollSettings(override);
const out = {{
  monthlySalaryBasisKrw: result.monthlySalaryBasisKrw.toString(),
  workdaysInMonth: result.workdaysInMonth,
  standardMonthlyHours: result.standardMonthlyHours,
  companyBurdenRate: result.companyBurdenRate.toString(),
}};
console.log(JSON.stringify(out));
"""
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", runner],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
        shell=False,
    )
    if completed.returncode != 0:
        pytest.fail(f"Node execution failed: {completed.stderr}")
    ts_out = json.loads(completed.stdout.strip())
    assert int(ts_out["monthlySalaryBasisKrw"]) == DEFAULT_PAYROLL.monthly_salary_basis_krw
    assert ts_out["workdaysInMonth"] == 20
    assert ts_out["standardMonthlyHours"] == DEFAULT_PAYROLL.standard_monthly_hours
    assert ts_out["companyBurdenRate"] == str(
        DEFAULT_PAYROLL.company_burden_rate
    )


# ── Story 3.3 — Warning aggregate cross-language parity ─────────
def _read_ts_l2_warnings_source() -> str:
    """Read the `l2-input-warnings.ts` mirror as text (F-25: strip comments)."""
    if not TS_L2_WARNINGS_PATH.exists():
        pytest.fail(
            f"Required TS mirror not found at {TS_L2_WARNINGS_PATH}. "
            "Story 3.3 T5 must create this file alongside the Python module."
        )
    raw = TS_L2_WARNINGS_PATH.read_text(encoding="utf-8")
    no_block = re.sub(r"/\*.*?\*/", "", raw, flags=re.DOTALL)
    return re.sub(r"^\s*//.*$", "", no_block, flags=re.MULTILINE)


def test_warning_codes_match_python() -> None:
    """WARNING_CODE_VALUES (TS) ↔ WarningCode enum (Py). Structural check."""
    from packages.services.m2_input.warnings import WarningCode

    ts_src = _read_ts_l2_warnings_source()
    m = re.search(
        r"export\s+const\s+WARNING_CODE_VALUES\s*=\s*\[(.*?)\]\s*as\s+const",
        ts_src,
        flags=re.DOTALL,
    )
    if not m:
        pytest.fail("WARNING_CODE_VALUES declaration not found in TS mirror")
    ts_values = sorted(re.findall(r'"([A-Z_]+)"', m.group(1)))
    py_values = sorted(c.value for c in WarningCode)
    assert ts_values == py_values, (
        f"WarningCode drift: TS={ts_values!r}, Py={py_values!r}"
    )


def test_inventory_product_types_match_python() -> None:
    """INVENTORY_PRODUCT_TYPES (TS) ↔ Python frozenset. Structural check."""
    from packages.services.m2_input.inventory_projection import (
        INVENTORY_PRODUCT_TYPES,
    )

    ts_src = _read_ts_l2_warnings_source()
    # Read the literal Set construction (Set of strings in TS).
    m = re.search(
        r"INVENTORY_PRODUCT_TYPES:\s*ReadonlySet<string>\s*=\s*new\s+Set\(\["
        r"(.*?)"
        r"\]\)",
        ts_src,
        flags=re.DOTALL,
    )
    if not m:
        pytest.fail("INVENTORY_PRODUCT_TYPES not found in TS mirror")
    ts_values = sorted(re.findall(r'"([a-z_]+)"', m.group(1)))
    py_values = sorted(INVENTORY_PRODUCT_TYPES)
    assert ts_values == py_values, (
        f"INVENTORY_PRODUCT_TYPES drift: TS={ts_values!r}, Py={py_values!r}"
    )


@_skip_no_node
def test_inventory_warning_korean_message_matches_python() -> None:
    """PRD §V3 message: 'PRD-0001(달걀) 기말재고 -30 → 음수 경고'.

    Python and TS must produce identical Korean text including
    trailing-zero stripping (AC #1 spec literal).
    """
    from packages.services.m2_input.inventory_projection import InventoryMovement
    from packages.services.m2_input.warnings import format_inventory_warning_ko

    pid = "00000000-0000-0000-0000-000000000001"  # not used by formatter
    m_py = InventoryMovement(
        product_id=__import__("uuid").UUID(pid),
        opening_qty=__import__("decimal").Decimal("100"),
        inbound_qty=__import__("decimal").Decimal("0"),
        outbound_qty=__import__("decimal").Decimal("130"),
    )
    product = type("P", (), {"product_code": "PRD-0001", "name_ko": "달걀"})()
    py_msg = format_inventory_warning_ko(product, m_py)
    assert py_msg == "PRD-0001(달걀) 기말재고 -30 → 음수 경고"

    # Execute TS mirror against the same fixture
    _read_ts_l2_warnings_source()  # ensure file exists
    runner = f"""
import * as lib from "./apps/web/lib/l2-input-warnings.ts";
const product = {{ productCode: "PRD-0001", nameKo: "달걀" }};
const m = {{
  productId: "{pid}",
  openingQty: "100",
  inboundQty: "0",
  outboundQty: "130",
}};
const out = lib.formatInventoryWarningKo(product, m);
console.log(out);
"""
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", runner],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",  # Korean text — force UTF-8 (Windows cp949 default crashes)
        timeout=10,
        shell=False,
    )
    if completed.returncode != 0:
        pytest.fail(f"Node execution failed: {completed.stderr}")
    ts_msg = completed.stdout.strip()
    assert ts_msg == py_msg, (
        f"Korean inventory warning drift: Py={py_msg!r}, TS={ts_msg!r}"
    )


@_skip_no_node
def test_operating_rate_warning_korean_matches_python() -> None:
    """PRD §V5 message: '총작업가능시간 248.52h(1.09 × 228) < 생산요구시간 250h → 100.6% (한도 초과)'.

    Trailing-zero stripping: '100.60' → '100.6' on both sides (AC #3).
    """
    from packages.services.m2_input.warnings import format_operating_rate_ko

    py_msg = format_operating_rate_ko(
        total_fte_headcount=__import__("decimal").Decimal("1.09"),
        standard_monthly_hours=228,
        total_available_hours=__import__("decimal").Decimal("248.52"),
        production_required_hours=__import__("decimal").Decimal("250"),
        operating_rate_pct=__import__("decimal").Decimal("100.60"),
    )
    assert "100.6" in py_msg
    assert "한도 초과" in py_msg

    runner = """
import * as lib from "./apps/web/lib/l2-input-warnings.ts";
const out = lib.formatOperatingRateKo({
  totalFteHeadcount: "1.09",
  standardMonthlyHours: 228,
  totalAvailableHours: "248.52",
  productionRequiredHours: "250",
  operatingRatePct: "100.60",
});
console.log(out);
"""
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", runner],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",  # Korean text — force UTF-8 (Windows cp949 default crashes)
        timeout=10,
        shell=False,
    )
    if completed.returncode != 0:
        pytest.fail(f"Node execution failed: {completed.stderr}")
    ts_msg = completed.stdout.strip()
    assert ts_msg == py_msg, (
        f"Korean operating-rate warning drift: Py={py_msg!r}, TS={ts_msg!r}"
    )


@_skip_no_node
def test_compute_operating_rate_rounding_matches_python() -> None:
    """250h / 248.52h → 100.60 → 100.6% after strip.

    Cross-language banker's rounding tolerance via Node.
    """
    from packages.services.m2_input.operating_rate import compute_operating_rate

    py_rate = compute_operating_rate(
        available_hours=__import__("decimal").Decimal("248.52"),
        required_hours=__import__("decimal").Decimal("250"),
    )
    assert py_rate == __import__("decimal").Decimal("100.60")

    runner = """
import * as lib from "./apps/web/lib/l2-input-warnings.ts";
const r = lib.computeOperatingRate("248.52", "250");
console.log(r.toFixed(2));
"""
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", runner],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
        shell=False,
    )
    if completed.returncode != 0:
        pytest.fail(f"Node execution failed: {completed.stderr}")
    ts_rate_str = completed.stdout.strip()
    assert ts_rate_str == "100.60", (
        f"TS operating rate drift: expected '100.60', got {ts_rate_str!r}"
    )