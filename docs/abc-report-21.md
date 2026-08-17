# ABC Report #21 Cost Object Breakdown (Story 9.4, Epic 9)

> **PRD §9 #21 verbatim** (prd.md §7.3 + §9 #21): **"부문귀속명세서 (카브아웃 근거 공시, §7.3)"** — 법인세법 시행규칙 제76조 2기준.
> **epics.md Story 9.4 UX label** (line 1052, 1056): **"원가대상별 원가 집계표 (Cost Object Breakdown)"** — ABC 결과 표시 보고서.
> **9-4 implementation**: **합성 scope** (PRD §9 #21 SSOT + epics.md 9.4 product_id별 행 extension) wire.
> **정합 차이 RESOLVED (9-5)**: PDF 라벨 = **"원가대상별 원가 집계표 (부문귀속명세서 §9 #21 기반)"** hybrid (PRD §9 #21 verbatim + epics.md UX label 모두 존중, 9-4 wire 변경 최소). UX 표기 = `[원가대상별 원가 집계표]` (epics.md 9.4 UX label 보존). 상세: deferred-work.md "Deferred from: Epic 9 close-out follow-up (2026-08-17)" D-9-4-DEFER-1 RESOLVED.
> Epic 9 (ABC / TDABC Engine — Service Business) 4번째 진입점.
>
> **baseline_commit:** `a67951b` (Story 9.3 T10 close-out tip — 2026-08-17)
> **cj-style:** Epic 9 4번째 진입점 (cj-style 4-story 분할: 9-1 + 9-2 + 9-3 + **9-4** + Epic 9 close-out retro 5번째 진입점)
> **A30 forward-lock:** SHARED PDF generator 결정 wire (Report #21 본 story + Report #15 후속 placeholder). Discriminated union
> `report_id: Literal[15, 16, 17, 18, 19, 20, 21]` factory pattern
> (`packages/services/m5_reports/pdf_generator.py`).

## What is Report #21?

Report #21 (원가대상별 원가 집계표, Cost Object Breakdown) is the
**Post-2 closing report** that visualizes ABC allocation outcomes
broken down by cost object (product). It is the formal output of
the 9.3 wire's `fiscal_period_snapshots.cost_object_breakdown JSONB`
column (Alembic 0028) + the `unused_capacity_breakdown JSONB` column.

PRD §9 #21 mandates this report for legal compliance per
법인세법 시행규칙 제76조 2기준 (Corporation Tax Act Enforcement
Decree Article 76, Paragraph 2) — companies must demonstrate that
indirect costs have been allocated to cost objects using a defensible
methodology (ABC satisfies the "활동별 원가 집계 → 원가대상별 전가"
two-step methodology).

## Report #21 Endpoint Architecture (AD-18 + AD-19 + A30)

AD-18 mandates **1 endpoint per Report #N**. M5 owns ONLY Report #21
endpoint:

| Method | Path | Capability | Role | Returns |
|--------|------|------------|------|---------|
| `GET` | `/api/v1/reports/21` | `COST_CALCULATION` OR `ABC_CALCULATION` | `owner` + `member` | `Report21Response` (JSON breakdown) |
| `POST` | `/api/v1/reports/21/pdf` | `COST_CALCULATION` OR `ABC_CALCULATION` | `owner` + `member` | `Report21PdfResponse` (Base64-encoded PDF) |

The **dual-route capability gate** uses
`require_any_capability(COST_CALCULATION, ABC_CALCULATION)` — ANY-OF
semantics (CR 12-5 D-14 envelope handler pattern + CR 12-1 L4
variadic helper precedent).

A30 forward-lock 결정 wire: The PDF export uses the SHARED factory
`packages/services/m5_reports/pdf_generator.py` with Discriminated
union `report_id: Literal[15, 16, 17, 18, 19, 20, 21]` — Report #21
본 story routes to `_compose_report21_pdf` (stdlib-only PDF byte
composition, Type0 CIDFont + Identity-H CMap pattern matching Story
6-3 `closing_pdf_export` 3rd sweep B1 precedent).

## Response Envelope (Report #21)

```python
class Report21CostObjectRow(BaseModel):
    product_id: str
    activity_id: str
    driver_id: str
    allocated_krw: Decimal = Field(ge=0)  # 1-Won precision

class Report21UnusedCapacityRow(BaseModel):
    department_id: str
    unused_hours: Decimal
    unused_cost_krw: Decimal = Field(ge=0)

class Report21Response(BaseModel):
    period_key: str
    cost_object_breakdown: list[Report21CostObjectRow]
    unused_capacity_breakdown: list[Report21UnusedCapacityRow]
    v7_verdict_is_balanced: bool  # AD-12 V7 ABC 무결성
    generation_hash: str  # sha256: + 64-char hexdigest
    report_code: Literal["COST_OBJECT_BREAKDOWN"] = "COST_OBJECT_BREAKDOWN"

class Report21PdfResponse(BaseModel):
    period_key: str
    pdf_base64: str  # Base64-encoded PDF bytes
    size_bytes: int
    generation_hash: str
    report_code: Literal["COST_OBJECT_BREAKDOWN"]
```

## V7 ABC 무결성 Invariant

PRD §V7 (ABC 무결성): Σ(원가대상별 배부액) + 미사용능력 = Σ(부서 원가)

This invariant is enforced at the pure kernel layer via
`compute_report21_hash` in `packages/cost_engine/abc_engine.py`:

```python
def compute_report21_hash(
    *,
    cost_object_breakdown: list[CostObjectRow],
    unused_capacity_breakdown: list[UnusedCapacityRow],
    period_key: str,
    v7_verdict: bool,
) -> str:
    # Returns "sha256:" + 64-char hexdigest
    # 1-Won precision (Decimal-as-string)
    # Deterministic: V8 byte-equality
```

`Report21InconsistentStateError` (V4 violation) is raised when:
- `Σ allocated_krw ≠ Σ department_total_cost - unused_capacity`
- `cost_object_breakdown` is empty AND `unused_capacity_breakdown` is empty

## Capability Dual-Route Gate (CR 12-1 L4 + CR 12-5 D-14)

```python
# apps/api/modules/m5_reports/handlers.py
@router.get("/api/v1/reports/21")
async def get_report21(
    period_key: str,
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    _: None = Depends(
            require_any_capability(
                Capability.COST_CALCULATION,
                Capability.ABC_CALCULATION,
            )
        ),
    __: None = Depends(require_any_role("owner", "member")),
):
    state = await Report21Service(session).build_report21(
        tenant_id=tenant_ctx.tenant_id,
        period_key=period_key,
    )
    return serialize_report21_state(state)
```

The variadic helper `require_any_capability(*capabilities)` accepts
N+ arguments and returns a FastAPI dependency that grants access if
the tenant has ANY of the listed capabilities. CR 12-5 D-14 envelope
handler pattern ensures the dual-route gate is preserved across
all industry matrix changes.

## A30 SHARED PDF Generator Factory (Discriminated Union)

```python
# packages/services/m5_reports/pdf_generator.py
ReportId = Literal[15, 16, 17, 18, 19, 20, 21]

@dataclass(frozen=True, slots=True)
class ReportPdfRequest:
    tenant_id: str
    period_key: str
    report_id: ReportId  # Discriminated union
    payload: tuple  # Per-report data
    metadata: tuple  # Per-report metadata

@dataclass(frozen=True, slots=True)
class ReportPdfResult:
    pdf_bytes: bytes
    size_bytes: int
    generation_hash: str
    page_count: int

def generate_report_pdf(*, request: ReportPdfRequest) -> ReportPdfResult:
    """A30 SHARED factory — Dispatch via Discriminated union."""
    if request.report_id == 21:
        return _compose_report21_pdf(request)
    elif request.report_id == 15:
        return _compose_report15_pdf(request)  # A31+ placeholder
    else:
        raise ReportPdfGenerationError(reason=f"unsupported report_id={request.report_id}")
```

The `_compose_report21_pdf` is stdlib-only PDF byte composition
(NO reportlab dependency) — uses Type0 CIDFont + Identity-H CMap
pattern matching Story 6-3 `closing_pdf_export` 3rd sweep B1 precedent.

## CR 12-1 L3 ORM→Kernel Boundary (`_to_report21_state`)

Per CR 12-1 L3 precedent (mirroring `_to_calc_state` and
`_to_report21_state`), the M5 service layer translates ORM rows
into a pure DTO before invoking the pure kernel:

```python
# apps/api/modules/m5_reports/services/report21_service.py
@dataclass(frozen=True, slots=True)
class Report21State:
    period_key: str
    cost_object_breakdown: tuple[CostObjectRow, ...]
    unused_capacity_breakdown: tuple[UnusedCapacityRow, ...]
    v7_verdict_is_balanced: bool
    generation_hash: str

def _to_report21_state(*, orm_rows: list[ORM]) -> Report21State:
    """Pure ORM→kernel boundary function (CR 12-1 L3)."""
    ...

def serialize_report21_state(state: Report21State) -> dict:
    """AD-15 §1 JSON-safe envelope serialization."""
    ...
```

The kernel functions (`compute_report21_hash`) operate ONLY on the
frozen DTO, never on ORM rows directly. This isolation enables
golden-fixture-based V8 byte-equality testing in the kernel layer.

## CR 11-4 D-002 (ko-KR.json SSOT) + TS Mirror Pattern

Frontend uses ko-KR.json SSOT for 9-4 surface strings:

```json
// apps/web/messages/ko-KR.json
{
  "report21": {
    "page_title": "원가대상별 원가 집계표",
    "page_subtitle": "법인세법 시행규칙 제76조 2기준",
    "cost_object_breakdown": { "title": "원가대상별 배부액", ... },
    "unused_capacity": { "title": "미사용 능력", ... },
    "v7_verdict_balanced": "ABC 무결성 검증 통과",
    "v7_verdict_unbalanced": "ABC 무결성 검증 실패"
  },
  "pdf_common": {
    "download_label": "PDF 다운로드",
    "title_prefix": "보고서"
  }
}
```

TypeScript mirrors (`apps/web/lib/report21.ts` + `report21-pdf.ts`)
define type-narrowing guards via `isReport21ResponseEnvelope` (CR
11-4 D-005 unknown reject pattern).

## Deferred Work (D-9-4-DEFER-1~4)

| ID | Description | Reason | Follow-up |
|----|-------------|--------|-----------|
| D-9-4-DEFER-1 | ✅ RESOLVED (9-5): epics.md "원가대상별 원가 집계표" vs PRD §9 #21 "부문귀속명세서" 정합 — hybrid PDF 라벨 "원가대상별 원가 집계표 (부문귀속명세서 §9 #21 기반)" + UX 표기 보존. architecture-inventory.md §9.4 incorrect verbatim claim 정정. | 9-4 scope-out | **DONE (2026-08-17)** |
| D-9-4-DEFER-2 | Report #15 wire (활동원가 내역서) — A30 SHARED factory 패턴 재사용 entry | A31+ forward-lock 결정 후속 | Epic 9 close-out retro |
| D-9-4-DEFER-3 | AI 자동 분석의견 (PRD §9 #16 + §A11 + §10) | 9-4 scope-out | Epic 11+ AI capability epic |
| D-9-4-DEFER-4 | Playwright E2E (Report #21 폼 + PDF 다운로드 end-to-end) | Epic 9 close-out follow-up 결정 | Epic 9 close-out retro A31+ 결정 후 dedicated sprint |

## Reference

- baseline_commit: `a67951b` (Story 9.3 T10 close-out)
- A30 forward-lock 결정 wire: `handoff-2026-08-17-9-3-done.md` Section 9.4
- A29 forward-lock 결정 wire: `handoff-2026-08-17-9-3-done.md` Section 9.3
- ABC engine: `packages/cost_engine/abc_engine.py` (A19 cohesion pattern 7 surface)
- A30 SHARED factory: `packages/services/m5_reports/pdf_generator.py` (A19 cohesion pattern 8 surface)
- Capability matrix v1.20: `docs/capability-matrix.md`
- Test: `tests/cost_engine/test_abc_engine_report21.py` (~32 cases)
- Test: `tests/services/m5_reports/test_pdf_generator.py` (~30 cases)
- Test: `tests/services/test_m5_reports_report21_service.py` (~25 cases)
- Test: `tests/api/m5_reports/test_report21_handlers.py` (~20 cases)
- Test: `tests/integration/test_capability_matrix_v1_20_drift.py` (~10 cases)
- Test: `apps/web/__tests__/components/m5-reports.Report21Panel.test.tsx` (~23 cases)
- Story spec: `_bmad-output/implementation-artifacts/9-4-abc-report-21-cost-object-breakdown.md`