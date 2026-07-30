"""packages.cost_engine.core — pure domain logic.

AD-1 + AD-5:
  - No imports of sqlalchemy, fastapi, requests, datetime.now, time, random.
  - All inputs are explicit parameters (no globals, no env reads).
  - All outputs are deterministic dataclasses.

AD-11:
  - core MUST NOT import packages.cost_engine.adapters. Enforced by import-linter.

The first concrete function lands in Story 4.1 (`compute_period_cost`).
"""
