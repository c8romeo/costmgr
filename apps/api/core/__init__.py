"""apps/api/core — API-side shared core (settings, security, db, audit).

This package is a sibling of apps/api/modules/ and is intentionally minimal
in Story 0.1. Future stories will add:
  - settings.py   (Pydantic Settings, AD-9 env var reading)
  - db.py         (SQLAlchemy 2.0 async, Story 0.2)
  - security.py   (JWT decoder, Story 0.2)
  - tenant_context.py (Story 0.2)
  - audit.py / service_role.py (Story 0.2)
"""
