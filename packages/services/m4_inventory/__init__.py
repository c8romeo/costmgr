"""packages.services.m4_inventory — Epic 5 shared domain-data primitives.

Pure-Python, stdlib-only subpackage. NO DB, NO clock, NO random.
AD-1 / AD-11 binding: shared vocabulary consumed by BOTH
`apps.api.modules.m4_inventory.services.*` (Python) and the TS
mirror at `apps/web/lib/l2-input-inventory-ledger.ts` (drift caught
by `tests/integration/test_inventory_ledger_label_consistency.py`).

Submodules:
- `ledger` (Story 5.2) — InventoryLedgerEvent NamedTuple + event
  payload builders + event_type/whitelist validators + append-only
  violation message builder.
- `ledger_query` (Story 5.2) — read-only SQL fragment builders for
  period-closing aggregate + recursive carry-chain query.

Future shared domain-data additions land here only after passing the
"no orchestration, no engine I/O, no ports, only NamedTuples + pure
functions" check. Drift between Python and TS is caught by the
`_label_consistency` integration test (Story 5.3 + Story 0.5
plumbing entry activates the TS side).
"""
