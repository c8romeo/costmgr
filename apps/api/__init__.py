"""apps.api — FastAPI modular monolith (AD-1).

Story 0.1 lands only the entry point and module folders. The 13 module
implementations (m0_onboarding … m12_account) populate in Epic 1+.

The package is a regular (non-namespace) package so import-linter can
discover `apps.api` as a concrete module.
"""

__version__ = "0.1.0"
