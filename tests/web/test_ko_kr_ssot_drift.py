"""tests.web.test_ko_kr_ssot_drift — ko-KR.json SSOT drift detector.

Story 11.4 (A13 sprint-up) — P-015 review patch: cross-surface drift
detector between the lib/ko-KR.json (formerly `apps/web/ko-KR.json`) and
`apps/web/messages/ko-KR.json` (next-intl loaded file).

D-002 review decision: `apps/web/ko-KR.json` was DELETED (zero consumers;
all 96 lines duplicated in `messages/ko-KR.json` which is the next-intl
loaded file per `apps/web/i18n.ts:15`). This test enforces that decision
and prevents accidental re-introduction of dead-code label files.

CR 6-3 lesson applied: cross-language parity drift detector across
multiple surfaces (Python ko-KR + TS mirror + ko-KR.json + API envelope
+ Vitest mock + service exception mapping). This test focuses on the
`apps/web/` SSOT layer: there must be exactly ONE ko-KR.json file
(loaded by next-intl), not multiple competing files.

Test cases:
  1. messages/ko-KR.json exists (next-intl loaded file).
  2. apps/web/ko-KR.json does NOT exist (dead-code deletion guard).
  3. messages/ko-KR.json has m11_close-related namespaces (snapshot
     persistence + reversal execute + reopen + cache invalidation +
     close sequence).
  4. i18n.ts loads from messages/ (not lib/).
  5. The m11_close drift surface (m11_close.*) is fully covered by
     messages/ko-KR.json sections (snapshot_persistence_panel +
     reversal_execute_dialog + reopen_operator_dialog +
     cache_invalidation_channel_badge + close_sequence_panel).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# ── Path resolution ───────────────────────────────────────────────
_REPO_ROOT = Path(__file__).resolve().parents[2]
_WEB_ROOT = _REPO_ROOT / "apps" / "web"
_MESSAGES_KO_KR = _WEB_ROOT / "messages" / "ko-KR.json"
_LIB_KO_KR_DELETED = _WEB_ROOT / "ko-KR.json"  # D-002: must NOT exist
_I18N_TS = _WEB_ROOT / "i18n.ts"


def _read_messages_ko_kr() -> dict:
    """Load the canonical next-intl messages file."""
    if not _MESSAGES_KO_KR.exists():
        pytest.fail(f"messages/ko-KR.json missing: {_MESSAGES_KO_KR}")
    return json.loads(_MESSAGES_KO_KR.read_text(encoding="utf-8"))


# M11 close-related namespaces that must be present in messages/ko-KR.json
# (Story 11.4 A13 sprint-up wire: snapshot persistence + reversal execute
# + reopen + cache invalidation 4 channels + close sequence).
_M11_CLOSE_NAMESPACES: tuple[str, ...] = (
    "snapshot_persistence_panel",
    "reversal_execute_dialog",
    "reopen_operator_dialog",
    "cache_invalidation_channel_badge",
    "close_sequence_panel",
)


# ── 1. messages/ko-KR.json exists (next-intl loaded file) ─────────
@pytest.mark.engine
def test_messages_ko_kr_exists() -> None:
    """apps/web/messages/ko-KR.json is the next-intl loaded file (i18n.ts:15)."""
    assert _MESSAGES_KO_KR.exists(), (
        f"Canonical next-intl messages file missing: {_MESSAGES_KO_KR}. "
        f"i18n.ts loads from `./messages/${{locale}}.json` (apps/web/i18n.ts:15)."
    )


# ── 2. apps/web/ko-KR.json does NOT exist (D-002 deletion guard) ──
@pytest.mark.engine
def test_apps_web_ko_kr_does_not_exist() -> None:
    """D-002 review decision: `apps/web/ko-KR.json` is dead code.

    Story 11.4 D-002 patch — `apps/web/ko-KR.json` was DELETED because:
      - Zero consumers (no imports anywhere in apps/web/).
      - All 96 lines duplicated in `messages/ko-KR.json` (loaded by
        next-intl per `i18n.ts:15`).
      - Components use `useTranslations("m11_close")` (etc.) which
        reads from `messages/ko-KR.json` — the deleted file was never
        wired at runtime.

    This test enforces the deletion. If the file re-appears, this test
    fails and the author must either (a) re-justify its existence, or
    (b) re-delete and update this test.
    """
    assert not _LIB_KO_KR_DELETED.exists(), (
        f"Dead-code ko-KR.json re-introduced: {_LIB_KO_KR_DELETED}. "
        f"Per D-002, this file is dead code — all content is in "
        f"messages/ko-KR.json (the next-intl loaded file). "
        f"Delete the file or update this test with new justification."
    )


# ── 3. messages/ko-KR.json has m11_close-related namespaces ───────
@pytest.mark.engine
def test_messages_ko_kr_has_m11_close_namespaces() -> None:
    """Story 11.4 A13 sprint-up — 5 m11_close namespaces must be present.

    Each namespace is a section in `apps/web/messages/ko-KR.json`
    consumed by `<M11Component>.tsx` via `useTranslations(namespace)`:
      - snapshot_persistence_panel (SnapshotPersistencePanel.tsx)
      - reversal_execute_dialog (ReversalExecuteDialog.tsx)
      - reopen_operator_dialog (ReopenOperatorDialog.tsx)
      - cache_invalidation_channel_badge (CacheInvalidationChannelBadge.tsx)
      - close_sequence_panel (CloseSequencePanel.tsx)
    """
    data = _read_messages_ko_kr()
    for namespace in _M11_CLOSE_NAMESPACES:
        assert namespace in data, (
            f"messages/ko-KR.json missing m11_close namespace: {namespace}. "
            f"Available: {sorted(data.keys())}"
        )


# ── 4. i18n.ts loads from messages/ (not lib/) ───────────────────
@pytest.mark.engine
def test_i18n_loads_from_messages_directory() -> None:
    """`apps/web/i18n.ts` must load from `./messages/${{locale}}.json`.

    Drift detector: if i18n.ts ever switches to `./lib/ko-KR.json` or
    `./ko-KR.json`, this test fails — the lib/ko-KR.json file is dead
    code by design (D-002).
    """
    if not _I18N_TS.exists():
        pytest.fail(f"i18n.ts missing: {_I18N_TS}")
    src = _I18N_TS.read_text(encoding="utf-8")
    assert "./messages/${locale}.json" in src or "./messages/" in src, (
        f"i18n.ts must load from './messages/${{locale}}.json'. "
        f"Found no './messages/' import path. Current source:\n{src}"
    )
    # Negative assertion: must NOT reference ./ko-KR.json or ./lib/ko-KR.json
    assert "./ko-KR.json" not in src, (
        f"i18n.ts must NOT load './ko-KR.json' (D-002 dead-code decision). "
        f"Found forbidden import path."
    )
    assert "./lib/ko-KR.json" not in src, (
        f"i18n.ts must NOT load './lib/ko-KR.json' (D-002 dead-code decision). "
        f"Found forbidden import path."
    )


# ── 5. m11_close drift surface covered by messages/ko-KR.json ────
@pytest.mark.engine
def test_m11_close_drift_surface_fully_covered() -> None:
    """Each m11_close namespace in messages/ko-KR.json has ≥1 non-empty string.

    Drift detector: catches accidental namespace deletion (e.g. someone
    trims `snapshot_persistence_panel` to `{}` during a refactor).
    Story 11.4 A13 sprint-up wire ensures all 5 namespaces are wired
    end-to-end; this test guards the wire.
    """
    data = _read_messages_ko_kr()
    for namespace in _M11_CLOSE_NAMESPACES:
        section = data[namespace]
        assert isinstance(section, dict), (
            f"Namespace {namespace!r} must be an object, got {type(section).__name__}"
        )
        assert len(section) >= 1, (
            f"Namespace {namespace!r} is empty. "
            f"Story 11.4 A13 sprint-up requires ≥1 string per namespace."
        )
        # All values must be non-empty strings.
        for key, value in section.items():
            assert isinstance(value, str) and value.strip(), (
                f"Namespace {namespace!r}.{key!r} must be non-empty string, "
                f"got {value!r}"
            )


# ── Total: 5 cross-surface drift cases ──────────────────────────
