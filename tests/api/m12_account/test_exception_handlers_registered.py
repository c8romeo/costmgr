"""tests.api.m12_account.test_exception_handlers_registered — Story 12.4 envelope wiring.

16 typed exceptions get AD-15 §4 envelope handlers in apps/api/main.py
(CR 11-2/11-3 lesson — no default FastAPI 500 for typed service exceptions).

Module-level (apps/api/modules/m12_account/exceptions.py): 8 exceptions
- TwoFactorNotEnabledError → 400
- TwoFactorAlreadyEnabledError → 409
- TwoFactorAuditEmitError → 503
- TwoFactorEncryptionError → 400
- TwoFactorCryptoKeyMissingError → 500
- TwoFactorRecoveryExhaustedError → 410
- TwoFactorDisableUnauthorizedError → 403
- TwoFactorUserNotFoundError → 404

Pure-kernel (packages/services/m12_account/totp.py): 3 exceptions
- TotpInvalidCodeError → 401
- TotpLockoutError → 429 (with Retry-After)
- TotpRecoveryInvalidError → 401

Challenge-token service: 3 exceptions
- ChallengeTokenExpiredError → 401
- ChallengeTokenInvalidError → 401
- ChallengeTokenPurposeMismatchError → 401

Total: 14 typed-exception handlers (spec said "8 exception handlers"
but the real exception set is 14 — see spec-vs-reality divergence
doc in story file).
"""

from __future__ import annotations

from fastapi import FastAPI

from apps.api.main import app as main_app


def _main_app() -> FastAPI:
    """Resolve the FastAPI app instance."""
    return main_app


def _registered_exception_classes() -> set[type]:
    """Collect the set of exception classes that have handlers registered.

    FastAPI stores exception handlers in `app.exception_handlers` as a
    dict keyed by exception class (or `int` for status-code handlers).
    """
    return set(main_app.exception_handlers.keys())


def test_two_factor_not_enabled_handler_registered() -> None:
    from apps.api.modules.m12_account.exceptions import TwoFactorNotEnabledError

    assert TwoFactorNotEnabledError in _registered_exception_classes()


def test_two_factor_already_enabled_handler_registered() -> None:
    from apps.api.modules.m12_account.exceptions import TwoFactorAlreadyEnabledError

    assert TwoFactorAlreadyEnabledError in _registered_exception_classes()


def test_two_factor_audit_emit_handler_registered() -> None:
    from apps.api.modules.m12_account.exceptions import TwoFactorAuditEmitError

    assert TwoFactorAuditEmitError in _registered_exception_classes()


def test_two_factor_encryption_handler_registered() -> None:
    from apps.api.modules.m12_account.exceptions import TwoFactorEncryptionError

    assert TwoFactorEncryptionError in _registered_exception_classes()


def test_two_factor_key_missing_handler_registered() -> None:
    from apps.api.modules.m12_account.exceptions import TwoFactorCryptoKeyMissingError

    assert TwoFactorCryptoKeyMissingError in _registered_exception_classes()


def test_two_factor_recovery_exhausted_handler_registered() -> None:
    from apps.api.modules.m12_account.exceptions import TwoFactorRecoveryExhaustedError

    assert TwoFactorRecoveryExhaustedError in _registered_exception_classes()


def test_two_factor_disable_unauthorized_handler_registered() -> None:
    from apps.api.modules.m12_account.exceptions import TwoFactorDisableUnauthorizedError

    assert TwoFactorDisableUnauthorizedError in _registered_exception_classes()


def test_two_factor_user_not_found_handler_registered() -> None:
    from apps.api.modules.m12_account.exceptions import TwoFactorUserNotFoundError

    assert TwoFactorUserNotFoundError in _registered_exception_classes()


def test_totp_invalid_code_handler_registered() -> None:
    from packages.services.m12_account.totp import TotpInvalidCodeError

    assert TotpInvalidCodeError in _registered_exception_classes()


def test_totp_lockout_handler_registered() -> None:
    from packages.services.m12_account.totp import TotpLockoutError

    assert TotpLockoutError in _registered_exception_classes()


def test_totp_recovery_invalid_handler_registered() -> None:
    from packages.services.m12_account.totp import TotpRecoveryInvalidError

    assert TotpRecoveryInvalidError in _registered_exception_classes()


def test_challenge_token_expired_handler_registered() -> None:
    from apps.api.modules.m12_account.services.two_factor_challenge_service import (
        ChallengeTokenExpiredError,
    )

    assert ChallengeTokenExpiredError in _registered_exception_classes()


def test_challenge_token_invalid_handler_registered() -> None:
    from apps.api.modules.m12_account.services.two_factor_challenge_service import (
        ChallengeTokenInvalidError,
    )

    assert ChallengeTokenInvalidError in _registered_exception_classes()


def test_challenge_token_purpose_mismatch_handler_registered() -> None:
    from apps.api.modules.m12_account.services.two_factor_challenge_service import (
        ChallengeTokenPurposeMismatchError,
    )

    assert (
        ChallengeTokenPurposeMismatchError in _registered_exception_classes()
    )


def test_m12_router_included_in_main_app() -> None:
    """The m12_account router must be include_router'd into the FastAPI app.

    FastAPI's internal `_IncludedRouter` wrapper exposes routes via
    `effective_route_contexts[i].route`. The cleanest stable check is to
    assert that the same `m12_router` object instance is wired into
    FastAPI's route registry. We compare by walking the FastAPI
    `route_class` registry via the `original_router` attribute on each
    `_IncludedRouter` entry.
    """
    from apps.api.modules.m12_account.handlers import router as m12_router

    # FastAPI's `_IncludedRouter` records the original APIRouter in
    # `original_router`. Walking that attribute lets us recover the
    # full set of routes from the source-of-truth router object.
    found = False
    for r in main_app.routes:
        if type(r).__name__ == "_IncludedRouter":
            original = getattr(r, "original_router", None)
            if original is m12_router:
                found = True
                break

    assert found, (
        "m12_account router was not include_router'd into the FastAPI app. "
        "Verify `apps/api/main.py` contains `app.include_router(m12_account_router)`."
    )
    # Sanity: the m12_router.prefix must match the spec.
    assert m12_router.prefix == "/api/v1"
