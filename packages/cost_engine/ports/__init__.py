"""packages.cost_engine.ports — Protocol interfaces (no I/O).

The engine exposes its capabilities through these Protocol types. Adapters
implement them; the API layer consumes them. Core logic does not import
ports (it only defines them as input/output types for service callers).
"""
