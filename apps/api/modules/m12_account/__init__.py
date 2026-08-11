"""M12 Account & Security Operations — Epic 12 stories 12.1~12.3 populate this.

Story 12.1 — `ActionClass.TWO_FACTOR_AUTH` + pure kernel (`packages/services/m12_account/`).
Story 12.4 — `router` wire (8 routes + 1 M2 entry-gate route under `/api/v1/account`
            + `/api/v1/m2-entry-gate`) + 16 typed exception handlers in `apps/api/main.py`.

Routes:
- POST /api/v1/account/2fa/setup                       — initiate 2FA setup (Story 12.1)
- POST /api/v1/account/2fa/verify                      — verify first TOTP code, flip twofa_enabled
- POST /api/v1/account/2fa/challenge                   — M2 entry gate TOTP verification
- POST /api/v1/account/2fa/recovery                    — verify 1회용 recovery code
- POST /api/v1/account/2fa/disable                     — disable 2FA (owner-only mutation)
- GET  /api/v1/account/2fa/status                     — read enrollment state (no UPDATE)
- POST /api/v1/account/2fa/challenge-tokens            — issue HS256 challenge token (5-min TTL)
- POST /api/v1/account/2fa/challenge-tokens/consume   — consume HS256 challenge token
- GET  /api/v1/m2-entry-gate                          — M2 entry gate state (PRD §M12-a)

AD-10 4-role gate: mutations (`disable`) require `owner` role. Reads
(`status`, `challenge`) are open to any role that has a valid TenantContext.
The 2FA capability gate is intentionally absent: 2FA is an industry-agnostic
security baseline (CR 12-1 L4 — applies to ALL tenants regardless of industry).
"""

from apps.api.modules.m12_account.handlers import router

__all__ = ["router"]
