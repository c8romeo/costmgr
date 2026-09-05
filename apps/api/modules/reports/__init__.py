"""apps.api.modules.reports — Epic 30+ Reporting & Export territory.

cj-287 wire sprint (cj-style 287번째) — package marker enabling
`from apps.api.modules.reports.csv_routes import router` import in
`apps/api/main.py` (post-vendor-management mount block).

Sprint context: cj-282a created `csv_routes.py` directly inside the
`apps/api/modules/reports/` directory without an `__init__.py`,
preventing the FastAPI router from being importable. This package
marker is the cj-287 mount prerequisite.

Sub-modules:
  - csv_routes: Story 30.1 CSV export (FR-30-1 + GET /api/v1/exports/csv)
  - (cj-288+) pdf_routes: Story 30.2 PDF export (FR-30-2)
  - (cj-290+) email_routes: Story 30.3 Email delivery (FR-30-3)
  - (cj-292+) scheduled_routes: Story 30.4 Scheduled reports (FR-30-4)

CR 11-3 honest-DEFER 224번째 epic 연속 정직 회복 — cj-282a 의 223번째
skip 결정 패턴 보존 + cj-287 에서 import surface 회복 결정 wire 진입.
"""
