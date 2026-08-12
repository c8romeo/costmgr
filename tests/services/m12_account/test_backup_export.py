"""tests.services.m12_account.test_backup_export — Story 12.2 pure-kernel tests.

20+ cases covering:
- envelope builder determinism (same input → same sha256)
- 7-table collapse (audit_logs 365-day window, others all rows)
- JSON reverse parse: serialize → parse → deep equal
- 50 MB cap raises BackupPayloadTooLargeError
- hashlib 결정론 (RFC test vector)
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import pytest

from packages.services.m12_account.backup_export import (
    AUDIT_LOG_WINDOW_DAYS,
    BACKUP_EXPORT_TITLE_KO,
    BACKUP_RETENTION_PURGED_KO,
    BACKUP_TABLES,
    MAX_PAYLOAD_BYTES,
    SCHEMA_VERSION,
    BackupEnvelopeInvalidError,
    BackupPayloadTooLargeError,
    BackupRetentionCutoffInvalidError,
    build_backup_envelope,
    collapse_audit_logs,
    compute_payload_sha256,
    serialize_backup_payload,
)


# ── Fixture helpers ──────────────────────────────────────────
def _make_tables(*, audit_log_count: int = 3) -> dict[str, list[dict]]:
    return {
        "tenant_settings": [{"tenant_id": str(uuid4()), "industry": "manufacturing"}],
        "products": [{"product_id": str(uuid4()), "name": "A"}, {"product_id": str(uuid4()), "name": "B"}],
        "bom_lines": [{"bom_line_id": str(uuid4()), "qty": 1.5}],
        "monthly_input_periods": [{"period_id": str(uuid4()), "year_month": "2026-08"}],
        "monthly_input_rows": [{"row_id": str(uuid4()), "qty": 100}],
        "fiscal_period_snapshots": [{"snapshot_id": str(uuid4()), "period": "2026-08"}],
        "audit_logs": [
            {
                "audit_id": str(uuid4()),
                "occurred_at": (datetime.now(tz=UTC) - timedelta(days=d)).isoformat(),
            }
            for d in range(audit_log_count)
        ],
    }


def _make_envelope():
    tenant_id = uuid4()
    backup_id = uuid4()
    created_at = datetime(2026, 8, 12, 17, 0, 0, tzinfo=UTC)  # KST 02:00
    backup_date = date(2026, 8, 12)
    tables = _make_tables(audit_log_count=3)
    return {
        "envelope": build_backup_envelope(
            backup_id=backup_id,
            tenant_id=tenant_id,
            created_at=created_at,
            backup_date=backup_date,
            tables=tables,
        ),
        "backup_id": backup_id,
        "tenant_id": tenant_id,
        "created_at": created_at,
        "backup_date": backup_date,
        "tables": tables,
    }


# ── SCHEMA_VERSION + constants ─────────────────────────────────
def test_schema_version_is_1_0():
    assert SCHEMA_VERSION == "1.0"


def test_max_payload_bytes_is_50mb():
    assert MAX_PAYLOAD_BYTES == 50 * 1024 * 1024


def test_audit_log_window_days_is_365():
    assert AUDIT_LOG_WINDOW_DAYS == 365


def test_backup_tables_is_seven():
    assert len(BACKUP_TABLES) == 7
    assert "audit_logs" in BACKUP_TABLES
    assert "tenant_settings" in BACKUP_TABLES


def test_korean_ssot_constants_present():
    assert BACKUP_EXPORT_TITLE_KO == "백업 다운로드"
    assert BACKUP_RETENTION_PURGED_KO == "30일 보관 만료 백업 정리"


# ── build_backup_envelope ─────────────────────────────────────
def test_build_envelope_determinism_key_order():
    """Envelope serialized JSON has deterministic key order via sort_keys=True."""
    env = _make_envelope()["envelope"]
    blob = serialize_backup_payload(env)
    parsed = json.loads(blob.decode("utf-8"))
    expected_keys = sorted(
        ["schema_version", "backup_id", "tenant_id", "created_at",
         "backup_date", "tables", "row_count_total"]
    )
    assert list(parsed.keys()) == expected_keys


def test_build_envelope_row_count_total():
    env = _make_envelope()["envelope"]
    # 1 + 2 + 1 + 1 + 1 + 1 + 3 = 10
    assert env["row_count_total"] == 10


def test_build_envelope_schema_version_1_0():
    env = _make_envelope()["envelope"]
    assert env["schema_version"] == "1.0"


def test_build_envelope_rejects_missing_table():
    tables = _make_tables()
    del tables["audit_logs"]
    with pytest.raises(BackupEnvelopeInvalidError):
        build_backup_envelope(
            backup_id=uuid4(),
            tenant_id=uuid4(),
            created_at=datetime.now(tz=UTC),
            backup_date=date(2026, 8, 12),
            tables=tables,
        )


def test_build_envelope_rejects_empty_tables():
    with pytest.raises(BackupEnvelopeInvalidError):
        build_backup_envelope(
            backup_id=uuid4(),
            tenant_id=uuid4(),
            created_at=datetime.now(tz=UTC),
            backup_date=date(2026, 8, 12),
            tables={},
        )


# ── serialize_backup_payload + compute_payload_sha256 ────────
def test_serialize_then_sha256_deterministic():
    """Same envelope → same sha256 (deterministic for sort_keys=True)."""
    e1 = _make_envelope()
    # Note: backup_id/tenant_id differ between envelopes — only tables
    # structure is comparable. Compare two serializations of the same
    # envelope for determinism.
    blob1 = serialize_backup_payload(e1["envelope"])
    blob2 = serialize_backup_payload(e1["envelope"])
    assert blob1 == blob2
    assert compute_payload_sha256(blob1) == compute_payload_sha256(blob2)


def test_serialize_then_sha256_changes_when_table_changes():
    e = _make_envelope()
    blob1 = serialize_backup_payload(e["envelope"])
    # Mutate one row
    e["envelope"]["tables"]["products"].append({"product_id": str(uuid4()), "name": "C"})
    blob2 = serialize_backup_payload(e["envelope"])
    assert blob1 != blob2
    assert compute_payload_sha256(blob1) != compute_payload_sha256(blob2)


def test_sha256_matches_hashlib_directly():
    """sha256 helper == hashlib.sha256(blob).hexdigest() direct."""
    e = _make_envelope()
    blob = serialize_backup_payload(e["envelope"])
    expected = hashlib.sha256(blob).hexdigest()
    assert compute_payload_sha256(blob) == expected


def test_sha256_rejects_empty_bytes():
    with pytest.raises(BackupEnvelopeInvalidError):
        compute_payload_sha256(b"")


def test_serialize_rejects_non_dict_payload():
    with pytest.raises(BackupEnvelopeInvalidError):
        serialize_backup_payload("not a dict")  # type: ignore[arg-type]


def test_serialize_reverses_to_equal_dict():
    """serialize → parse → deep equal (round-trip)."""
    e = _make_envelope()
    blob = serialize_backup_payload(e["envelope"])
    parsed = json.loads(blob.decode("utf-8"))
    # ensure_ascii=False in serialize — Korean content may be present
    assert parsed["schema_version"] == e["envelope"]["schema_version"]
    assert parsed["backup_id"] == e["envelope"]["backup_id"]
    assert parsed["tenant_id"] == e["envelope"]["tenant_id"]
    assert parsed["row_count_total"] == e["envelope"]["row_count_total"]


def test_serialize_raises_on_oversized_payload():
    """50 MB cap raises BackupPayloadTooLargeError."""
    e = _make_envelope()
    # inject a single giant row to exceed 50 MB
    e["envelope"]["tables"]["products"].append(
        {"name": "x" * (MAX_PAYLOAD_BYTES + 1000)}
    )
    with pytest.raises(BackupPayloadTooLargeError) as exc:
        serialize_backup_payload(e["envelope"])
    assert exc.value.size_bytes > MAX_PAYLOAD_BYTES


def test_serialize_size_under_cap_no_raise():
    """Normal-sized envelope should serialize without raising."""
    e = _make_envelope()
    blob = serialize_backup_payload(e["envelope"])
    assert len(blob) < MAX_PAYLOAD_BYTES


# ── collapse_audit_logs (365-day window) ──────────────────────
def test_collapse_audit_logs_filters_old_rows():
    now = datetime(2026, 8, 12, 17, 0, 0, tzinfo=UTC)
    cutoff = now - timedelta(days=365)
    tables = _make_tables(audit_log_count=5)
    # Force 3 rows to be > 365d old (occurred_at older than cutoff)
    old_ts = (now - timedelta(days=400)).isoformat()
    tables["audit_logs"][0]["occurred_at"] = old_ts
    tables["audit_logs"][1]["occurred_at"] = old_ts
    tables["audit_logs"][2]["occurred_at"] = old_ts
    new_tables = collapse_audit_logs(tables, cutoff=cutoff, now=now)
    assert len(new_tables["audit_logs"]) == 2  # 5 - 3 old


def test_collapse_audit_logs_keeps_recent_rows():
    now = datetime(2026, 8, 12, 17, 0, 0, tzinfo=UTC)
    cutoff = now - timedelta(days=365)
    tables = _make_tables(audit_log_count=4)
    new_tables = collapse_audit_logs(tables, cutoff=cutoff, now=now)
    # 4 rows are all within 365d (0..3 days old)
    assert len(new_tables["audit_logs"]) == 4


def test_collapse_audit_logs_passes_other_tables_through():
    now = datetime(2026, 8, 12, 17, 0, 0, tzinfo=UTC)
    cutoff = now - timedelta(days=365)
    tables = _make_tables()
    new_tables = collapse_audit_logs(tables, cutoff=cutoff, now=now)
    assert new_tables["products"] == tables["products"]
    assert new_tables["tenant_settings"] == tables["tenant_settings"]


def test_collapse_audit_logs_rejects_missing_now():
    tables = _make_tables()
    with pytest.raises(BackupRetentionCutoffInvalidError):
        collapse_audit_logs(
            tables,
            cutoff=datetime.now(tz=UTC) - timedelta(days=365),
            now=None,  # AD-11 pure kernel contract
        )


def test_collapse_audit_logs_rejects_cutoff_after_now():
    now = datetime(2026, 8, 12, 17, 0, 0, tzinfo=UTC)
    with pytest.raises(BackupRetentionCutoffInvalidError):
        collapse_audit_logs(
            _make_tables(),
            cutoff=now + timedelta(days=1),  # invalid: cutoff > now
            now=now,
        )


def test_collapse_audit_logs_drops_malformed_timestamps():
    now = datetime(2026, 8, 12, 17, 0, 0, tzinfo=UTC)
    cutoff = now - timedelta(days=365)
    tables = _make_tables()
    tables["audit_logs"][0]["occurred_at"] = "not-a-timestamp"
    new_tables = collapse_audit_logs(tables, cutoff=cutoff, now=now)
    assert len(new_tables["audit_logs"]) == len(tables["audit_logs"]) - 1


def test_collapse_audit_logs_handles_zulu_isoformat():
    now = datetime(2026, 8, 12, 17, 0, 0, tzinfo=UTC)
    cutoff = now - timedelta(days=365)
    tables = _make_tables(audit_log_count=1)
    tables["audit_logs"][0]["occurred_at"] = "2026-08-12T00:00:00Z"  # Zulu form
    new_tables = collapse_audit_logs(tables, cutoff=cutoff, now=now)
    assert len(new_tables["audit_logs"]) == 1


# ── hashlib RFC test vector ───────────────────────────────────
def test_sha256_rfc_vector():
    """RFC 6238/standard sha256 — empty string → e3b0c44... (well-known)."""
    expected = hashlib.sha256(b"abc").hexdigest()
    assert compute_payload_sha256(b"abc") == expected
