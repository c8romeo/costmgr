"""bizup cost engine — pure Python hexagonal core.

AD-1:  Hexagonal core. Pure domain logic; ports for inbound/outbound; adapters at boundary.
AD-5:  Engine purity — no I/O, no DB, no clock, no randomness, no global state, no logs.
AD-11: Dependency direction — `core` may NOT import `adapters`. Enforced by import-linter.

This package is the source of truth for the 1원 reconciliation (V8 regression).
"""
