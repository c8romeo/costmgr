"""packages.cost_engine.adapters — I/O boundary implementations.

This is where DB drivers, HTTP clients, file readers, etc. live. AD-11 forbids
core → adapters. Adapters may depend on core; core may not depend on adapters.

Subpackages created by later stories:
  - adapters/db        (SQLAlchemy, Story 0.2+)
  - adapters/rest      (FastAPI integration, Epic 4+)
  - adapters/csv_excel (Excel upload, Epic 3+)

Story 0.1 leaves these empty by design.
"""
