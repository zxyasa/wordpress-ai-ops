from __future__ import annotations

import os

import pytest

import wp_ai_ops.config as config_mod
from wp_ai_ops.config import resolve_auth, resolve_site


@pytest.fixture(autouse=True)
def reset_dotenv_loaded():
    """Reset the dotenv loaded flag before each test."""
    config_mod._DOTENV_LOADED = False
    yield
    config_mod._DOTENV_LOADED = False


class TestDotenvParsing:
    def test_normal(self, tmp_path, monkeypatch):
        dotenv = tmp_path / ".env"
        dotenv.write_text("MY_VAR=hello\nMY_OTHER=world\n")
        monkeypatch.chdir(tmp_path)
        # Ensure vars aren't already set
        monkeypatch.delenv("MY_VAR", raising=False)
        monkeypatch.delenv("MY_OTHER", raising=False)
        config_mod._load_dotenv_if_exists()
        assert os.environ["MY_VAR"] == "hello"
        assert os.environ["MY_OTHER"] == "world"

    def test_comments_and_empty_lines(self, tmp_path, monkeypatch):
        dotenv = tmp_path / ".env"
        dotenv.write_text("# comment\n\nVALID_KEY=value\n")
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("VALID_KEY", raising=False)
        config_mod._load_dotenv_if_exists()
        assert os.environ["VALID_KEY"] == "value"

    def test_quoted_values(self, tmp_path, monkeypatch):
        dotenv = tmp_path / ".env"
        dotenv.write_text('QUOTED="hello world"\nSINGLE=\'test\'\n')
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("QUOTED", raising=False)
        monkeypatch.delenv("SINGLE", raising=False)
        config_mod._load_dotenv_if_exists()
        assert os.environ["QUOTED"] == "hello world"
        assert os.environ["SINGLE"] == "test"

    def test_no_override_existing(self, tmp_path, monkeypatch):
        dotenv = tmp_path / ".env"
        dotenv.write_text("EXISTING=dotenv_value\n")
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("EXISTING", "original")
        config_mod._load_dotenv_if_exists()
        assert os.environ["EXISTING"] == "original"


class TestResolveAuth:
    def test_default(self, monkeypatch):
        monkeypatch.setenv("WP_USERNAME", "user1")
        monkeypatch.setenv("WP_APP_PASSWORD", "pass1")
        auth = resolve_auth(None)
        assert auth.username == "user1"
        assert auth.app_password == "pass1"

    def test_custom_auth_ref(self, monkeypatch):
        monkeypatch.setenv("MYSITE_USERNAME", "site_user")
        monkeypatch.setenv("MYSITE_APP_PASSWORD", "site_pass")
        auth = resolve_auth("MYSITE")
        assert auth.username == "site_user"
        assert auth.app_password == "site_pass"

    def test_missing_vars(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)  # no .env file here
        monkeypatch.delenv("WP_USERNAME", raising=False)
        monkeypatch.delenv("WP_APP_PASSWORD", raising=False)
        with pytest.raises(ValueError, match="Missing required env var"):
            resolve_auth(None)


class TestResolveSite:
    def test_base_url_only(self, monkeypatch):
        monkeypatch.delenv("WP_API_BASE", raising=False)
        site = resolve_site({"base_url": "https://example.com"})
        assert site.base_url == "https://example.com"
        assert site.wp_api_base == "https://example.com/wp-json/wp/v2"

    def test_wp_api_base_only(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)  # no .env file here
        monkeypatch.delenv("WP_BASE_URL", raising=False)
        site = resolve_site({"wp_api_base": "https://example.com/wp-json/wp/v2"})
        assert site.wp_api_base == "https://example.com/wp-json/wp/v2"
        assert site.base_url == "https://example.com"

    def test_both(self, monkeypatch):
        site = resolve_site({
            "base_url": "https://example.com",
            "wp_api_base": "https://example.com/wp-json/wp/v2",
        })
        assert site.base_url == "https://example.com"
        assert site.wp_api_base == "https://example.com/wp-json/wp/v2"

    def test_missing_both(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)  # no .env file here
        monkeypatch.delenv("WP_BASE_URL", raising=False)
        monkeypatch.delenv("WP_API_BASE", raising=False)
        with pytest.raises(ValueError, match="site.base_url or site.wp_api_base"):
            resolve_site({})
