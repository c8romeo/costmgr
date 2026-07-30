"""packages.ports — cross-cutting interface contracts.

This package defines Protocol types and dataclasses that the UI, API, and
services all share. It must remain stdlib + typing only (AD-11).

Future contents:
  - settings_port.py       (typed settings aggregate, AD-23)
  - tenant_context_port.py (Story 0.2)
  - report_view_port.py    (Epic 6)
  - ai_insight_port.py     (Epic 10)
"""
