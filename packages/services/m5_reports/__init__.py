"""packages.services.m5_reports — A30 SHARED M5 reports service module.

Story 9.4 (Epic 9 4번째 진입점):
  - `pdf_generator` — A30 SHARED PDF generator factory for Report #15 +
    Report #21 (Discriminated union `report_id: Literal[15, 16, 17, 18,
    19, 20, 21]`).

A30 forward-lock SHARED PDF generator 결정 wire (9-3 handoff lock):
  Report #21 (Cost Object Breakdown, 본 Story 9.4) + Report #15 (활동원가
  내역서, 후속 진입점) = SHARED factory pattern via Discriminated union
  `report_id: Literal[15, 16, 17, 18, 19, 20, 21]`.

AD-5 / AD-11 binding: pure-Python, stdlib-only, NO reportlab dependency
(PDF byte composition = stdlib only, matching `closing_pdf_export`
precedent). NO DB, NO clock, NO random.

Drift catch: PDF byte-equality V8 determinism via
`packages.cost_engine.abc_engine.compute_report_pdf_hash`.
"""
