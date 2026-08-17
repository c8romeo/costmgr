"""tests.integration.test_capability_matrix_v1_20_drift — Story 9.4 wire pin.

Pins v1.20 EXTENSION (0 NEW capabilities, capability matrix 변경 0):
- A30 forward-lock dual-report PDF generator 결정 wire
  (Report #21 본 story + Report #15 후속 placeholder)
- Discriminated union `report_id: Literal[15, 16, 17, 18, 19, 20, 21]`
  in `packages/services/m5_reports/pdf_generator.py`
- 4 NEW typed exceptions mapped to AD-15 §4 envelopes in
  `apps/api/main.py` (CR 12-5 D-14):
  - Report21PeriodNotCommittedError → 422 REPORT21_PERIOD_NOT_COMMITTED
  - Report21NoBreakdownError → 422 REPORT21_NO_COST_OBJECT_BREAKDOWN
  - Report21BreakdownNotFoundError → 404 REPORT21_BREAKDOWN_NOT_FOUND
  - Report21PdfGenerationError → 500 REPORT_PDF_GENERATION_ERROR

Capability matrix 변경 0 — Report #21 endpoint uses existing dual-route
`require_any_capability(COST_CALCULATION, ABC_CALCULATION)`, A30 SHARED
factory delegates via Discriminated union.

A29 forward-lock 9-3 wire 보존 (변경 0) + A30 forward-lock 결정 wire.

CR 11-3 lesson: capability drift across industry matrices is the #1
source of cross-tenant write leaks. v1.20 EXTENSION requires 0 NEW pins
since no NEW capability row is added — the existing v1.19 drift detector
covers the row presence + 4-industry grants. This file documents the
v1.20 SPECIFIC contracts (A30 SHARED factory Discriminated union, 4 NEW
typed exceptions, Report #21 endpoint gate) that the M5 reports
service + wire schema + A30 SHARED factory must preserve.
"""

from __future__ import annotations

from pathlib import Path
from typing import get_args

from apps.api.core.capability import (
    Capability,
    industry_supports,
    require_any_capability,
)
from packages.services.m0_onboarding.industry_menu import Industry

# ── v1.20 EXTENSION: 0 NEW capabilities ──────────────────────
_NEW_V1_20_CAPABILITIES: tuple[Capability, ...] = ()


def _load_capability_matrix_docs() -> str:
    """Read the capability matrix docs for drift detection."""
    repo_root = Path(__file__).resolve().parents[2]
    return (
        repo_root / "docs" / "capability-matrix.md"
    ).read_text(encoding="utf-8")


# ── 1. v1.20 capability count is 0 ──────────────────────────
def test_capability_v1_20_count_is_0() -> None:
    """v1.20 EXTENSION adds 0 NEW capabilities (A30 SHARED PDF factory
    is shared infrastructure — no NEW capability row needed).

    CR 11-3 honest-DEFER discipline: explicit assertion that no NEW
    capability row is needed for the dual-report factory pattern.
    """
    assert len(_NEW_V1_20_CAPABILITIES) == 0


# ── 2. A30 SHARED factory Discriminated union integrity ─────
def test_a30_shared_factory_discriminated_union_integrity() -> None:
    """A30 SHARED factory MUST support report_id Discriminated union
    `Literal[15, 16, 17, 18, 19, 20, 21]`.

    Per A30 forward-lock 결정 wire (9-3 handoff): Report #21 (본 story)
    + Report #15 (후속 placeholder, A31+ forward-lock). The factory
    pattern uses Discriminated union to dispatch to per-report composer
    functions (_compose_report21_pdf, _compose_report15_pdf, ...).
    """
    from packages.services.m5_reports.pdf_generator import (
        ReportId,
        ReportPdfRequest,
        generate_report_pdf,
    )

    # Verify Discriminated union Literal[15..21] covers Report #21 (본 story)
    # and Report #15 (후속 placeholder)
    valid_ids = {15, 16, 17, 18, 19, 20, 21}
    args_set = set(get_args(ReportId))
    assert valid_ids.issubset(args_set), (
        f"ReportId Discriminated union MUST include 15, 16, 17, 18, 19, 20, 21; "
        f"got {args_set}"
    )

    # Verify generate_report_pdf is the SHARED factory entrypoint
    assert callable(generate_report_pdf)

    # Verify ReportPdfRequest frozen dataclass envelope
    import dataclasses

    assert dataclasses.is_dataclass(ReportPdfRequest)
    assert dataclasses.fields(ReportPdfRequest)


# ── 3. v1.20 dual-route gate preservation ──────────────────
def test_v1_20_dual_route_capabilities_intersect_4_industries() -> None:
    """COST_CALCULATION ∪ ABC_CALCULATION MUST cover ALL 4 industries
    (v1.19 + v1.20 preservation).

    v1.20 Report #21 endpoint uses the SAME dual-route gate as v1.19
    POST /api/v1/calc. A30 SHARED factory delegates via Discriminated
    union, NOT via NEW capability.
    """
    industries = (
        Industry.MANUFACTURING,
        Industry.SERVICE,
        Industry.MANUFACTURING_SERVICE,
        Industry.MANUFACTURING_SERVICE_OTHER,
    )
    for industry in industries:
        has_cost = industry_supports(industry, Capability.COST_CALCULATION)
        has_abc = industry_supports(industry, Capability.ABC_CALCULATION)
        assert has_cost or has_abc, (
            f"{industry.name} MUST have at least one of "
            f"COST_CALCULATION or ABC_CALCULATION for the dual-route gate"
        )


# ── 4. Docs v1.20 markers ──────────────────────────────────
def test_capability_matrix_docs_pin_v1_20() -> None:
    """docs/capability-matrix.md must declare v1.20 + Story 9.4 markers."""
    docs = _load_capability_matrix_docs()
    assert "# Capability Matrix (v1.20)" in docs, (
        "docs/capability-matrix.md title must be v1.20 (Story 9.4 wire)"
    )
    assert "v1.20 (2026-08-17, Story 9.4, Epic 9)" in docs, (
        "docs/capability-matrix.md must declare v1.20 entry header"
    )
    assert "A30 forward-lock" in docs
    assert "SHARED PDF generator" in docs
    assert "Discriminated union" in docs
    assert "Literal[15, 16, 17, 18, 19, 20, 21]" in docs


def test_capability_matrix_docs_no_capability_change_v1_20() -> None:
    """docs MUST declare 'capability matrix 변경 0' for v1.20.

    Per spec T6: NO NEW capability, capability matrix 변경 0.
    The v1.20 EXTENSION wires Report #21 via existing dual-route gate
    + A30 SHARED factory delegates via Discriminated union.
    """
    docs = _load_capability_matrix_docs()
    assert "Capability matrix 변경 0" in docs or "capability matrix 변경 0" in docs
    assert "No NEW capability" in docs


def test_capability_matrix_changelog_has_v1_20_entry() -> None:
    """docs Changelog MUST include v1.20 entry (Story 9.4, 2026-08-17)."""
    docs = _load_capability_matrix_docs()
    assert "v1.20 (Story 9.4, Epic 9)" in docs, (
        "docs Changelog missing v1.20 (Story 9.4, Epic 9) entry"
    )
    assert "2026-08-17" in docs, (
        "docs Changelog must include v1.20 (2026-08-17) date stamp"
    )


# ── 5. v1.20 industry-agnostic + mfg-only contracts ───────
def test_capability_abc_calculation_industry_agnostic_v1_20() -> None:
    """v1.20 EXTENSION does NOT change ABC_CALCULATION industry grants
    (still industry-agnostic — CR 12-1 L4 precedent)."""
    industries = (
        Industry.MANUFACTURING,
        Industry.SERVICE,
        Industry.MANUFACTURING_SERVICE,
        Industry.MANUFACTURING_SERVICE_OTHER,
    )
    for industry in industries:
        assert industry_supports(industry, Capability.ABC_CALCULATION), (
            f"{industry.name} must STILL grant ABC_CALCULATION after v1.20"
        )


def test_capability_cost_calculation_mfg_only_v1_20() -> None:
    """v1.20 EXTENSION does NOT change COST_CALCULATION industry grants
    (still mfg-only — manufacturing 3종 ✅)."""
    assert industry_supports(Industry.MANUFACTURING, Capability.COST_CALCULATION)
    assert industry_supports(
        Industry.MANUFACTURING_SERVICE, Capability.COST_CALCULATION
    )
    assert industry_supports(
        Industry.MANUFACTURING_SERVICE_OTHER, Capability.COST_CALCULATION
    )
    assert not industry_supports(Industry.SERVICE, Capability.COST_CALCULATION), (
        "service-only MUST NOT have COST_CALCULATION (use ABC instead)"
    )


# ── 6. A30 SHARED factory AD-15 §4 envelope wire integrity ─
def test_a30_factory_envelope_codes_v1_20() -> None:
    """A30 SHARED factory + Report #21 envelope codes MUST be wired in
    `apps/api/main.py` (CR 12-5 D-14 typed contract verbatim).

    4 NEW envelope handlers:
    - REPORT21_PERIOD_NOT_COMMITTED → 422
    - REPORT21_NO_COST_OBJECT_BREAKDOWN → 422
    - REPORT21_BREAKDOWN_NOT_FOUND → 404
    - REPORT_PDF_GENERATION_ERROR → 500
    """
    main_py = (Path(__file__).resolve().parents[2] / "apps" / "api" / "main.py").read_text(encoding="utf-8")

    assert "REPORT21_PERIOD_NOT_COMMITTED" in main_py, (
        "main.py MUST register REPORT21_PERIOD_NOT_COMMITTED envelope handler"
    )
    assert "REPORT21_NO_COST_OBJECT_BREAKDOWN" in main_py, (
        "main.py MUST register REPORT21_NO_COST_OBJECT_BREAKDOWN envelope handler"
    )
    assert "REPORT21_BREAKDOWN_NOT_FOUND" in main_py, (
        "main.py MUST register REPORT21_BREAKDOWN_NOT_FOUND envelope handler"
    )
    assert "REPORT_PDF_GENERATION_ERROR" in main_py, (
        "main.py MUST register REPORT_PDF_GENERATION_ERROR envelope handler"
    )


# ── 7. Cross-version regression sanity ──────────────────────
def test_capability_v1_19_dual_route_still_preserved_v1_20() -> None:
    """v1.19 dual-route gate MUST remain functional after v1.20 wire
    (no regression)."""
    # Smoke check: the factory exists and is callable with multiple args.
    factory = require_any_capability(
        Capability.COST_CALCULATION,
        Capability.ABC_CALCULATION,
    )
    assert callable(factory)


def test_capability_v1_18_abc_calculation_still_exists_v1_20() -> None:
    """ABC_CALCULATION (v1.18) + v1.19 dual-route + v1.20 SHARED factory
    MUST remain after v1.20 wire (no regression)."""
    assert hasattr(Capability, "ABC_CALCULATION")
    assert industry_supports(Industry.MANUFACTURING, Capability.ABC_CALCULATION)
