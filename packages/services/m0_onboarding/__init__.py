"""packages.services.m0_onboarding — M0 onboarding shared domain (Story 1.1).

Pure-Python domain logic for the M0 onboarding module. Imports only stdlib
+ `enum` + `typing` — **no DB, no web, no clock, no random** (AD-1/AD-5).

This package is the **single source of truth** for industry → menu mapping
(PRD §4.1 + §8.M0(a)). Both the API (FastAPI handlers) and the web (Next.js
sidebar) consume the canonical definitions. The TypeScript mirror in
`apps/web/lib/menu-config.ts` is checked for drift by
`tests/integration/test_menu_config_consistency.py`.

Per AD-15: snake_case enum values (e.g. `manufacturing_service`), PascalCase
class names (`Industry`, `MenuItem`).
"""
