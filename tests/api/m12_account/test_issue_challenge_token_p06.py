"""tests.api.m12_account.test_issue_challenge_token_p06 — Story 12.5 P-06 fix.

P-06 fix (Story 12.5, AC #7): the `POST /api/v1/account/2fa/challenge-tokens`
endpoint now requires a fresh 6-digit TOTP `current_code` in the request body.
Prior to P-06 the endpoint accepted an empty body, which meant any
authenticated owner/member could mint a challenge token even with misconfigured
or compromised 2FA.

5 NEW cases verify the P-06 wire (IssueChallengeTokenRequest schema +
handler validation path):

  case 1: IssueChallengeTokenRequest accepts a valid 6-digit code
  case 2: missing current_code → 422 Pydantic ValidationError
  case 3: malformed (non-6-digit) current_code → 422 Pydantic ValidationError
  case 4: short (5-digit) current_code → 422 Pydantic ValidationError
  case 5: empty string current_code → 422 Pydantic ValidationError

Together with the route-shape test (`test_handlers_route_shape.py`), these
cover the schema-layer defense for the endpoint — the handler-layer call to
`verify_totp_challenge` is exercised in the existing `tests/api/m12_account/
test_two_factor_service.py` suite.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from apps.api.modules.m12_account.handlers import IssueChallengeTokenRequest


# ── Case 1: valid 6-digit code accepted ─────────────────────────
def test_issue_request_accepts_valid_6_digit_code() -> None:
    """Valid 6-digit TOTP code populates `current_code` field."""
    payload = IssueChallengeTokenRequest(current_code="123456")
    assert payload.current_code == "123456"


# ── Case 2: missing current_code → 422 ──────────────────────────
def test_issue_request_missing_current_code_raises_validation_error() -> None:
    """Pydantic forbids missing required field — empty body rejected."""
    with pytest.raises(ValidationError) as excinfo:
        IssueChallengeTokenRequest()  # type: ignore[call-arg]
    errors = excinfo.value.errors()
    assert any(e["loc"] == ("current_code",) for e in errors), (
        f"expected current_code missing error, got {errors}"
    )


# ── Case 3: malformed code → 422 ────────────────────────────────
@pytest.mark.parametrize("bad_code", ["abcdef", "12.456", "12-456"])
def test_issue_request_malformed_current_code_raises_validation_error(
    bad_code: str,
) -> None:
    """Non-6-digit code → Pydantic pattern fails → 422 envelope."""
    with pytest.raises(ValidationError) as excinfo:
        IssueChallengeTokenRequest(current_code=bad_code)
    errors = excinfo.value.errors()
    assert any(e["loc"] == ("current_code",) for e in errors), (
        f"expected current_code pattern error, got {errors}"
    )


# ── Case 4: short code (5 digits) → 422 ────────────────────────
def test_issue_request_short_current_code_raises_validation_error() -> None:
    """5-digit code is below the min_length 6 floor → 422."""
    with pytest.raises(ValidationError) as excinfo:
        IssueChallengeTokenRequest(current_code="12345")
    errors = excinfo.value.errors()
    assert any(e["loc"] == ("current_code",) for e in errors), (
        f"expected current_code min_length error, got {errors}"
    )


# ── Case 5: empty string → 422 ──────────────────────────────────
def test_issue_request_empty_current_code_raises_validation_error() -> None:
    """Empty string violates both pattern and min_length → 422."""
    with pytest.raises(ValidationError) as excinfo:
        IssueChallengeTokenRequest(current_code="")
    errors = excinfo.value.errors()
    assert any(e["loc"] == ("current_code",) for e in errors), (
        f"expected current_code validation error, got {errors}"
    )
