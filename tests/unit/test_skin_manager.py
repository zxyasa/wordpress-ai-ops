"""
Unit tests for SkinManager.

All tests use mocks — no real WordPress connection required.
"""
from __future__ import annotations

import json
import os
import tempfile
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from wp_ai_ops.skin_manager import SkinManager, _parse_skin_file, FLATSOME_TOKEN_MAP


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_state_dir(tmp_path: Path) -> Path:
    return tmp_path / "state"


@pytest.fixture()
def manager(tmp_state_dir: Path) -> SkinManager:
    return SkinManager(
        wp_base_url="https://example.com",
        wp_username="admin",
        wp_app_password="xxxx yyyy zzzz",
        dry_run=True,
        state_dir=str(tmp_state_dir),
    )


@pytest.fixture()
def default_skin_file(tmp_path: Path) -> Path:
    """A minimal skin .md file for testing."""
    content = textwrap.dedent("""\
        skin_id: "test-skin"
        skin_name: "Test Skin"

        # Colour tokens
        color_primary: "#aabbcc"
        color_cta_accent: "#ff0000"
        color_text_primary: "#333333"
        color_card_bg: "#ffffff"

        # Typography (not mapped to Flatsome)
        font_size_h2: "1.5rem"
    """)
    p = tmp_path / "test-skin.md"
    p.write_text(content)
    return p


@pytest.fixture()
def skin_with_css(tmp_path: Path) -> Path:
    content = textwrap.dedent("""\
        skin_id: "css-skin"
        color_primary: "#123456"

        ```css
        :root { --primary: #123456; }
        body { color: #333; }
        ```
    """)
    p = tmp_path / "css-skin.md"
    p.write_text(content)
    return p


# ---------------------------------------------------------------------------
# _parse_skin_file
# ---------------------------------------------------------------------------

class TestParseSkinFile:
    def test_parses_quoted_values(self, default_skin_file: Path) -> None:
        tokens = _parse_skin_file(default_skin_file)
        assert tokens["color_primary"] == "#aabbcc"
        assert tokens["skin_id"] == "test-skin"

    def test_ignores_comments(self, default_skin_file: Path) -> None:
        tokens = _parse_skin_file(default_skin_file)
        for k in tokens:
            assert not k.startswith("#")

    def test_parses_non_colour_tokens(self, default_skin_file: Path) -> None:
        tokens = _parse_skin_file(default_skin_file)
        assert tokens["font_size_h2"] == "1.5rem"

    def test_parses_custom_css_block(self, skin_with_css: Path) -> None:
        tokens = _parse_skin_file(skin_with_css)
        assert "custom_css" in tokens
        assert ":root" in tokens["custom_css"]
        assert "color: #333" in tokens["custom_css"]

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            _parse_skin_file(tmp_path / "nonexistent.md")

    def test_empty_file_returns_empty_dict(self, tmp_path: Path) -> None:
        p = tmp_path / "empty.md"
        p.write_text("")
        tokens = _parse_skin_file(p)
        assert tokens == {}


# ---------------------------------------------------------------------------
# SkinManager.load_skin
# ---------------------------------------------------------------------------

class TestLoadSkin:
    def test_returns_dict(self, manager: SkinManager, default_skin_file: Path) -> None:
        tokens = manager.load_skin(str(default_skin_file))
        assert isinstance(tokens, dict)
        assert "color_primary" in tokens

    def test_raises_on_missing_file(self, manager: SkinManager, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            manager.load_skin(str(tmp_path / "missing.md"))


# ---------------------------------------------------------------------------
# SkinManager.snapshot (dry_run=True)
# ---------------------------------------------------------------------------

class TestSnapshot:
    def test_dry_run_returns_path_string(self, manager: SkinManager) -> None:
        path = manager.snapshot()
        assert isinstance(path, str)
        assert "snapshot_" in path

    def test_dry_run_does_not_create_file(self, manager: SkinManager, tmp_state_dir: Path) -> None:
        manager.snapshot()
        # In dry_run mode the directory may be created but the JSON file should not
        snapshots = list(tmp_state_dir.glob("snapshot_*.json"))
        assert snapshots == [], "Dry-run must not write snapshot file to disk"

    def test_live_mode_creates_snapshot_file(self, tmp_state_dir: Path) -> None:
        live_manager = SkinManager(
            wp_base_url="https://example.com",
            wp_username="admin",
            wp_app_password="pw",
            dry_run=False,
            state_dir=str(tmp_state_dir),
        )
        # Patch _read_flatsome_options so we don't need a real WP server
        with patch.object(live_manager, "_read_flatsome_options", return_value={"primary_color": "#abc"}):
            path = live_manager.snapshot()

        assert Path(path).exists()
        data = json.loads(Path(path).read_text())
        assert data["flatsome_options"] == {"primary_color": "#abc"}
        assert "timestamp" in data


# ---------------------------------------------------------------------------
# SkinManager.apply (dry_run=True)
# ---------------------------------------------------------------------------

class TestApply:
    def test_dry_run_does_not_call_wp(self, manager: SkinManager, capsys: pytest.CaptureFixture) -> None:
        tokens = {
            "color_primary": "#aabbcc",
            "color_cta_accent": "#ff0000",
        }
        with patch.object(manager, "_write_flatsome_options") as mock_write:
            manager.apply(tokens)
            mock_write.assert_not_called()

    def test_dry_run_prints_mapped_tokens(self, manager: SkinManager, capsys: pytest.CaptureFixture) -> None:
        tokens = {"color_primary": "#aabbcc", "color_cta_accent": "#ff0000"}
        manager.apply(tokens)
        out = capsys.readouterr().out
        # Keys are now confirmed — output should show the confirmed Flatsome key names
        assert "color_primary" in out
        assert "color_alert" in out

    def test_unmapped_tokens_silently_skipped(self, manager: SkinManager, capsys: pytest.CaptureFixture) -> None:
        # font tokens have no Flatsome mapping — should not appear in output
        tokens = {"font_size_h2": "1.5rem", "space_lg": "24px"}
        manager.apply(tokens)
        out = capsys.readouterr().out
        assert "font_size_h2" not in out
        assert "space_lg" not in out

    def test_live_mode_calls_write(self, tmp_state_dir: Path) -> None:
        """In live mode, apply() calls _write_flatsome_options (keys are now confirmed)."""
        live_manager = SkinManager(
            wp_base_url="https://example.com",
            wp_username="admin",
            wp_app_password="pw",
            dry_run=False,
            state_dir=str(tmp_state_dir),
        )
        with patch.object(live_manager, "_write_flatsome_options") as mock_write:
            live_manager.apply({"color_primary": "#aabbcc"})
        mock_write.assert_called_once_with({"color_primary": "#aabbcc"})


# ---------------------------------------------------------------------------
# SkinManager.rollback (dry_run=True)
# ---------------------------------------------------------------------------

class TestRollback:
    def test_dry_run_prints_snapshot_info(self, manager: SkinManager, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        snap = tmp_path / "snapshot_20260101T000000Z.json"
        snap.write_text(json.dumps({
            "timestamp": "20260101T000000Z",
            "wp_base_url": "https://example.com",
            "flatsome_options": {"primary_color": "#old"},
        }))
        manager.rollback(str(snap))
        out = capsys.readouterr().out
        assert "DRY-RUN" in out

    def test_missing_snapshot_raises(self, manager: SkinManager, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            manager.rollback(str(tmp_path / "nonexistent.json"))

    def test_live_mode_calls_write(self, tmp_state_dir: Path, tmp_path: Path) -> None:
        snap = tmp_path / "snapshot_20260101T000000Z.json"
        snap.write_text(json.dumps({
            "timestamp": "20260101T000000Z",
            "wp_base_url": "https://example.com",
            "flatsome_options": {"primary_color": "#restored"},
        }))
        live_manager = SkinManager(
            wp_base_url="https://example.com",
            wp_username="admin",
            wp_app_password="pw",
            dry_run=False,
            state_dir=str(tmp_state_dir),
        )
        with patch.object(live_manager, "_write_flatsome_options") as mock_write:
            live_manager.rollback(str(snap))
        mock_write.assert_called_once_with({"primary_color": "#restored"})


# ---------------------------------------------------------------------------
# SkinManager.apply_custom_css (dry_run=True)
# ---------------------------------------------------------------------------

class TestApplyCustomCss:
    def test_dry_run_prints_preview(self, manager: SkinManager, capsys: pytest.CaptureFixture) -> None:
        css = ":root { --primary: #abc; }\nbody { color: #333; }"
        manager.apply_custom_css(css)
        out = capsys.readouterr().out
        assert "DRY-RUN" in out
        assert "--primary" in out

    def test_live_mode_posts_to_settings(self, tmp_state_dir: Path) -> None:
        live_manager = SkinManager(
            wp_base_url="https://example.com",
            wp_username="admin",
            wp_app_password="pw",
            dry_run=False,
            state_dir=str(tmp_state_dir),
        )
        fake_response = MagicMock()
        fake_response.read.return_value = json.dumps({"custom_css": "ok"}).encode()
        fake_response.__enter__ = lambda s: s
        fake_response.__exit__ = MagicMock(return_value=False)

        with patch("wp_ai_ops.skin_manager.urlrequest.urlopen", return_value=fake_response):
            live_manager.apply_custom_css(":root{}")  # should not raise

    def test_live_mode_raises_on_http_error(self, tmp_state_dir: Path) -> None:
        from urllib.error import HTTPError
        live_manager = SkinManager(
            wp_base_url="https://example.com",
            wp_username="admin",
            wp_app_password="pw",
            dry_run=False,
            state_dir=str(tmp_state_dir),
        )
        err = HTTPError(url="http://x", code=403, msg="Forbidden", hdrs=None, fp=MagicMock(read=lambda: b"no auth"))
        with patch("wp_ai_ops.skin_manager.urlrequest.urlopen", side_effect=err):
            with pytest.raises(RuntimeError, match="403"):
                live_manager.apply_custom_css(":root{}")


# ---------------------------------------------------------------------------
# SkinManager.latest_snapshot_path
# ---------------------------------------------------------------------------

class TestLatestSnapshotPath:
    def test_returns_none_when_no_snapshots(self, manager: SkinManager) -> None:
        assert manager.latest_snapshot_path() is None

    def test_returns_most_recent(self, manager: SkinManager, tmp_state_dir: Path) -> None:
        tmp_state_dir.mkdir(parents=True, exist_ok=True)
        older = tmp_state_dir / "snapshot_20260101T000000Z.json"
        newer = tmp_state_dir / "snapshot_20260201T000000Z.json"
        older.write_text("{}")
        newer.write_text("{}")
        result = manager.latest_snapshot_path()
        assert result is not None
        assert "20260201" in result


# ---------------------------------------------------------------------------
# FLATSOME_TOKEN_MAP integrity
# ---------------------------------------------------------------------------

class TestFlatsomeTokenMap:
    def test_all_keys_are_colour_tokens(self) -> None:
        for k in FLATSOME_TOKEN_MAP:
            assert k.startswith("color_"), f"Expected color_ prefix: {k}"

    def test_all_values_are_strings(self) -> None:
        for k, v in FLATSOME_TOKEN_MAP.items():
            assert isinstance(v, str), f"Flatsome key for {k} must be str"

    def test_no_duplicate_flatsome_keys(self) -> None:
        values = list(FLATSOME_TOKEN_MAP.values())
        assert len(values) == len(set(values)), "Duplicate Flatsome keys detected"
