"""apps/api/modules — 13 module folders, one per M0~M12 capability.

This is the modular monolith's module layer (AD-1). Each module is a
self-contained vertical slice with its own router, schemas, and service
adapters. Modules communicate only through packages.ports interfaces.

Story 0.1: empty stubs only. Module code lands in Epic 1+ (M0 onboarding) onward.
"""
