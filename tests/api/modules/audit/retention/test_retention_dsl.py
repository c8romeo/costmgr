"""tests.api.modules.audit.retention.test_retention_dsl — pure kernel tests.

Phase 6 (cj-style 87번째 epic 연속 정직 회복 wire) — T7a tests —
F22.1 retention policy DSL. 12 NEW pytest cases covering:
  - retain() builder happy path (4 classes)
  - retain() invalid class → AuditLogRetentionPolicyInvalidError(400)
  - retain() days < 30 → error
  - retain() security + archive=False → ARCHIVE_REQUIRED error
  - parse_retention_policy() happy path with RLS bind
  - parse_retention_policy() invalid tenant_uuid → error
  - parse_retention_policy() invalid payload type → error
  - parse_retention_policy() invalid class → error
  - parse_retention_policy() days out of range → error
  - parse_retention_policy() security archive missing → error
  - DEFAULT_RETENTION_DAYS class mapping (admin/auth/data/security)
  - RetentionClass Literal type compatible with VALID_RETENTION_CLASSES
"""
from __future__ import annotations

import uuid

import pytest

from apps.api.modules.audit.retention.retention_dsl import (
    DEFAULT_RETENTION_DAYS,
    VALID_RETENTION_CLASSES,
    AuditLogRetentionPolicyInvalidError,
    parse_retention_policy,
    retain,
)


class TestRetainBuilder:
    """retain() builder — 4 NEW cases."""

    def test_retain_admin_defaults_to_5y(self) -> None:
        policy = retain("admin")
        assert policy["action_class"] == "admin"
        assert policy["days"] == 1825
        assert policy["archive"] is True
        assert policy["mask_pii"] is True

    def test_retain_auth_defaults_to_3y(self) -> None:
        policy = retain("auth")
        assert policy["days"] == 1095

    def test_retain_security_defaults_to_7y(self) -> None:
        policy = retain("security")
        assert policy["days"] == 2555

    def test_retain_explicit_days_override(self) -> None:
        policy = retain("data", days=180)
        assert policy["days"] == 180


class TestRetainInvalidInputs:
    """retain() failure modes — 4 NEW cases."""

    def test_invalid_class_raises(self) -> None:
        with pytest.raises(AuditLogRetentionPolicyInvalidError) as exc:
            retain("nonexistent")  # type: ignore[arg-type]
        assert exc.value.code == "AUDIT_LOG_RETENTION_INVALID_CLASS"

    def test_days_too_low_raises(self) -> None:
        with pytest.raises(AuditLogRetentionPolicyInvalidError) as exc:
            retain("admin", days=10)
        assert exc.value.code == "AUDIT_LOG_RETENTION_DAYS_TOO_LOW"

    def test_security_requires_archive(self) -> None:
        with pytest.raises(AuditLogRetentionPolicyInvalidError) as exc:
            retain("security", archive=False)
        assert exc.value.code == "AUDIT_LOG_RETENTION_ARCHIVE_REQUIRED"

    def test_typed_envelope_has_code_message_details(self) -> None:
        with pytest.raises(AuditLogRetentionPolicyInvalidError) as exc:
            retain("admin", days=10)
        assert exc.value.code
        assert exc.value.message_ko
        assert exc.value.details.get("action_class") == "admin"


class TestParseRetentionPolicy:
    """parse_retention_policy() — 6 NEW cases."""

    def _tenant(self) -> uuid.UUID:
        return uuid.UUID("11111111-1111-1111-1111-111111111111")

    def test_parse_happy_path(self) -> None:
        policy = parse_retention_policy(
            self._tenant(),
            {"action_class": "admin", "days": 365, "archive": True, "mask_pii": True},
        )
        assert policy["tenant_id"] == "11111111-1111-1111-1111-111111111111"
        assert policy["action_class"] == "admin"
        assert policy["days"] == 365

    def test_parse_invalid_tenant_raises(self) -> None:
        with pytest.raises(AuditLogRetentionPolicyInvalidError) as exc:
            parse_retention_policy("not-a-uuid", {"action_class": "admin"})  # type: ignore[arg-type]
        assert exc.value.code == "AUDIT_LOG_RETENTION_INVALID_TENANT"

    def test_parse_non_dict_payload_raises(self) -> None:
        with pytest.raises(AuditLogRetentionPolicyInvalidError) as exc:
            parse_retention_policy(self._tenant(), [])  # type: ignore[arg-type]
        assert exc.value.code == "AUDIT_LOG_RETENTION_INVALID_PAYLOAD"

    def test_parse_invalid_class_raises(self) -> None:
        with pytest.raises(AuditLogRetentionPolicyInvalidError) as exc:
            parse_retention_policy(self._tenant(), {"action_class": "bogus"})
        assert exc.value.code == "AUDIT_LOG_RETENTION_INVALID_CLASS"

    def test_parse_days_out_of_range_raises(self) -> None:
        with pytest.raises(AuditLogRetentionPolicyInvalidError) as exc:
            parse_retention_policy(
                self._tenant(),
                {"action_class": "admin", "days": 5000},
            )
        assert exc.value.code == "AUDIT_LOG_RETENTION_DAYS_OUT_OF_RANGE"

    def test_parse_security_archive_missing_raises(self) -> None:
        with pytest.raises(AuditLogRetentionPolicyInvalidError) as exc:
            parse_retention_policy(
                self._tenant(),
                {"action_class": "security", "archive": False},
            )
        assert exc.value.code == "AUDIT_LOG_RETENTION_ARCHIVE_REQUIRED"


class TestConstants:
    """Constants — 1 NEW case."""

    def test_default_retention_days_class_mapping(self) -> None:
        assert DEFAULT_RETENTION_DAYS == {
            "admin": 1825,
            "auth": 1095,
            "data": 1825,
            "security": 2555,
        }

    def test_valid_retention_classes_contains_all_four(self) -> None:
        assert frozenset({"admin", "auth", "data", "security"}) == VALID_RETENTION_CLASSES
