"""M5 Reports module — Epic 6 + Epic 9 4번째 진입점 (Story 9.4) wire.

Story 9.4 (Epic 9 cj-style 4번째 진입점):
- GET /api/v1/reports/21         (Report #21 Cost Object Breakdown 조회)
- POST /api/v1/reports/21/pdf    (A30 SHARED PDF generator factory)
"""

from apps.api.modules.m5_reports.handlers import router

__all__ = ["router"]
