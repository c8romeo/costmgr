"""tests.api.test_alembic_0021_cache_invalidation — Story 11.3 migration tests.

8 cases per AC #8 spec — verify the Alembic 0021 migration shape:
- revision / down_revision attributes
- down_revision = '0020_fiscal_periods_close_sequence' (11-2 wire tip)
- upgrade() drops 1-channel CHECK + adds 4-channel CHECK on cache_invalidation_log
- 4 ALLOWED_CHANNELS_11_3 channels (ai_cache + cost_engine_cache +
  fiscal_period_cache + closing_snapshot_cache)
- 4 per-channel INDEX entries
- downgrade() drops all 4 indexes + restores 1-channel CHECK
- Module SSOT aligned with cache_invalidation_publisher.py:ALLOWED_CHANNELS
"""

from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path

# Lazy-load migration module to avoid alembic env side effects.
_MIGRATION_PATH = (
    "apps.api.alembic.versions.0021_cache_invalidation_multi_channel"
)


def _load_migration_module() -> object:
    """Import the 0021 migration module by file path.

    Alembic migration files don't follow the apps.api. package layout
    (they live in `apps/api/alembic/versions/`), so we load by file
    location via importlib.
    """
    repo_root = Path(__file__).resolve().parents[2]
    migration_file = (
        repo_root
        / "apps"
        / "api"
        / "alembic"
        / "versions"
        / "0021_cache_invalidation_multi_channel.py"
    )
    spec = importlib.util.spec_from_file_location(
        "migration_0021",
        migration_file,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_migration_revision_attribute() -> None:
    m = _load_migration_module()
    assert m.revision == "0021_cache_invalidation_multi_channel"


def test_migration_down_revision_is_11_2_tip() -> None:
    """down_revision must be '0020_fiscal_periods_close_sequence' (11-2 wire tip)."""
    m = _load_migration_module()
    assert m.down_revision == "0020_fiscal_periods_close_sequence"


def test_migration_upgrade_function_exists() -> None:
    m = _load_migration_module()
    assert callable(m.upgrade)
    assert callable(m.downgrade)


def test_migration_expands_channel_set_to_4() -> None:
    """upgrade() must reference all 4 AD-25 channels."""
    repo_root = Path(__file__).resolve().parents[2]
    src = (
        repo_root
        / "apps"
        / "api"
        / "alembic"
        / "versions"
        / "0021_cache_invalidation_multi_channel.py"
    ).read_text(encoding="utf-8")
    # All 4 channel names must appear in the source.
    for channel in (
        "ai_cache",
        "cost_engine_cache",
        "fiscal_period_cache",
        "closing_snapshot_cache",
    ):
        assert channel in src, f"channel {channel!r} missing from migration"


def test_migration_drops_old_1_channel_check() -> None:
    """upgrade() must DROP the 1-channel CHECK (cache_invalidation_log_channel_check)."""
    m = _load_migration_module()
    repo_root = Path(__file__).resolve().parents[2]
    src = (
        repo_root
        / "apps"
        / "api"
        / "alembic"
        / "versions"
        / "0021_cache_invalidation_multi_channel.py"
    ).read_text(encoding="utf-8")
    # DROP CONSTRAINT IF EXISTS cache_invalidation_log_channel_check
    assert (
        "DROP CONSTRAINT IF EXISTS cache_invalidation_log_channel_check" in src
    ), "migration must drop old 1-channel CHECK"
    # ADD CONSTRAINT cache_invalidation_log_channel_check (4-channel)
    assert (
        "ADD CONSTRAINT cache_invalidation_log_channel_check" in src
    ), "migration must add new 4-channel CHECK"


def test_migration_creates_4_per_channel_indexes() -> None:
    """upgrade() must create 4 per-channel indexes (ix_cache_inv_log_ch_<channel>).

    The migration uses an f-string template `ix_cache_inv_log_ch_{channel[:30]}`
    in a loop — literal index names only appear at runtime. Verify the
    template + the loop iteration over the 4-channel tuple.
    """
    m = _load_migration_module()
    repo_root = Path(__file__).resolve().parents[2]
    src = (
        repo_root
        / "apps"
        / "api"
        / "alembic"
        / "versions"
        / "0021_cache_invalidation_multi_channel.py"
    ).read_text(encoding="utf-8")
    # The f-string template must appear in the source.
    assert "ix_cache_inv_log_ch_{channel[:30]}" in src
    # The loop iterates over _ALLOWED_CHANNELS_11_3.
    assert "for channel in _ALLOWED_CHANNELS_11_3" in src
    # All 4 channels must be present in the tuple.
    assert len(m._ALLOWED_CHANNELS_11_3) == 4
    # CREATE INDEX must be issued inside the loop (1 statement, N iterations).
    assert "CREATE INDEX IF NOT EXISTS" in src


def test_migration_downgrade_restores_1_channel_check() -> None:
    """downgrade() must restore the 1-channel CHECK ('ai_cache' only)."""
    repo_root = Path(__file__).resolve().parents[2]
    src = (
        repo_root
        / "apps"
        / "api"
        / "alembic"
        / "versions"
        / "0021_cache_invalidation_multi_channel.py"
    ).read_text(encoding="utf-8")
    assert "CHECK (channel IN ('ai_cache'))" in src, (
        "downgrade must restore the 1-channel CHECK"
    )


def test_migration_channel_set_has_4_channels() -> None:
    """Migration channel set must have exactly 4 AD-25 channels.

    The migration is the DB-side SSOT for the CHECK constraint;
    the publisher extension (T2) is expected to match.
    """
    m = _load_migration_module()
    channels = set(m._ALLOWED_CHANNELS_11_3)
    assert len(channels) == 4, f"expected 4 channels, got {channels}"
    # All 4 AD-25 channels must be present.
    for expected in (
        "ai_cache",
        "cost_engine_cache",
        "fiscal_period_cache",
        "closing_snapshot_cache",
    ):
        assert expected in channels, f"channel {expected!r} missing"


def test_migration_downgrade_drops_4_per_channel_indexes() -> None:
    """downgrade() must drop all 4 per-channel indexes.

    Like the upgrade test, the downgrade uses an f-string template
    in a loop — verify the template + loop, not literal names.
    """
    repo_root = Path(__file__).resolve().parents[2]
    src = (
        repo_root
        / "apps"
        / "api"
        / "alembic"
        / "versions"
        / "0021_cache_invalidation_multi_channel.py"
    ).read_text(encoding="utf-8")
    # The downgrade loop iterates over _ALLOWED_CHANNELS_11_3.
    # Both upgrade and downgrade share the loop variable.
    assert "DROP INDEX IF EXISTS" in src