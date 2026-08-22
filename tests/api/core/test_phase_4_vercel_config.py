"""tests/api/core/test_phase_4_vercel_config.py — vercel.json schema validation.

Phase 4 (cj-style 55번째 epic 연속 정직 회복 wire) — AC #7.1.
JSON schema verification of root `vercel.json` deployment config.
"""

from __future__ import annotations

import json
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
VERCEL_JSON = REPO_ROOT / "vercel.json"


@pytest.fixture(scope="module")
def vercel_config() -> dict:
    assert VERCEL_JSON.exists(), f"vercel.json not found at {VERCEL_JSON}"
    with VERCEL_JSON.open(encoding="utf-8") as f:
        return json.load(f)


class TestVercelJsonSchema:
    """vercel.json MUST satisfy the Vercel Next.js deployment config schema."""

    def test_vercel_json_exists(self) -> None:
        assert VERCEL_JSON.is_file()

    def test_vercel_json_parses_as_valid_json(self, vercel_config: dict) -> None:
        assert isinstance(vercel_config, dict)
        assert len(vercel_config) > 0

    def test_framework_is_nextjs(self, vercel_config: dict) -> None:
        assert vercel_config.get("framework") == "nextjs"

    def test_build_command_targets_web_filter(self, vercel_config: dict) -> None:
        build_cmd = vercel_config.get("buildCommand", "")
        assert "pnpm --filter web build" in build_cmd

    def test_install_command_uses_frozen_lockfile(
        self, vercel_config: dict
    ) -> None:
        install_cmd = vercel_config.get("installCommand", "")
        assert "pnpm install --frozen-lockfile" in install_cmd

    def test_output_directory_matches_web_next(self, vercel_config: dict) -> None:
        out_dir = vercel_config.get("outputDirectory", "")
        assert out_dir == "apps/web/.next"


class TestVercelRegions:
    """Vercel region MUST include Seoul (icn1) for NFR16 latency."""

    def test_regions_contains_seoul(self, vercel_config: dict) -> None:
        regions = vercel_config.get("regions", [])
        assert "icn1" in regions, f"Seoul region missing, got: {regions}"

    def test_regions_is_list(self, vercel_config: dict) -> None:
        assert isinstance(vercel_config.get("regions"), list)


class TestVercelHeaders:
    """Security headers MUST include CSP + HSTS + X-Frame-Options."""

    def test_headers_block_exists(self, vercel_config: dict) -> None:
        assert "headers" in vercel_config
        assert isinstance(vercel_config["headers"], list)
        assert len(vercel_config["headers"]) > 0

    def test_csp_header_present(self, vercel_config: dict) -> None:
        headers = vercel_config.get("headers", [])
        all_keys = {
            h["key"]
            for block in headers
            for h in block.get("headers", [])
        }
        assert "Content-Security-Policy" in all_keys

    def test_hsts_header_present(self, vercel_config: dict) -> None:
        headers = vercel_config.get("headers", [])
        all_keys = {
            h["key"]
            for block in headers
            for h in block.get("headers", [])
        }
        assert "Strict-Transport-Security" in all_keys

    def test_x_frame_options_present(self, vercel_config: dict) -> None:
        headers = vercel_config.get("headers", [])
        all_keys = {
            h["key"]
            for block in headers
            for h in block.get("headers", [])
        }
        assert "X-Frame-Options" in all_keys


class TestVercelRedirects:
    """Legacy /ko-KR/* MUST redirect to /ko/* (next-intl i18n routing)."""

    def test_redirects_block_present(self, vercel_config: dict) -> None:
        assert "redirects" in vercel_config
        redirects = vercel_config["redirects"]
        assert isinstance(redirects, list)

    def test_ko_kr_redirect_to_ko(self, vercel_config: dict) -> None:
        redirects = vercel_config.get("redirects", [])
        has_ko_kr = any(
            r.get("source", "").startswith("/ko-KR/")
            and r.get("destination", "").startswith("/ko/")
            for r in redirects
        )
        assert has_ko_kr, "Legacy /ko-KR/* → /ko/* redirect missing"
