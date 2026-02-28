from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


_DOTENV_LOADED = False


@dataclass
class AuthConfig:
    username: str
    app_password: str


@dataclass
class SiteConfig:
    base_url: str
    wp_api_base: str
    auth_ref: str | None = None


def _must_get_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required env var: {name}")
    return value


def _load_dotenv_if_exists() -> None:
    global _DOTENV_LOADED
    if _DOTENV_LOADED:
        return
    dotenv_path = Path(".env")
    if dotenv_path.exists() and dotenv_path.is_file():
        for raw in dotenv_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    _DOTENV_LOADED = True


def resolve_auth(auth_ref: str | None) -> AuthConfig:
    _load_dotenv_if_exists()
    if auth_ref:
        username = _must_get_env(f"{auth_ref}_USERNAME")
        password = _must_get_env(f"{auth_ref}_APP_PASSWORD")
    else:
        username = _must_get_env("WP_USERNAME")
        password = _must_get_env("WP_APP_PASSWORD")
    return AuthConfig(username=username, app_password=password)


def resolve_site(site_payload: dict) -> SiteConfig:
    _load_dotenv_if_exists()
    base_url = site_payload.get("base_url") or os.getenv("WP_BASE_URL")
    wp_api_base = site_payload.get("wp_api_base") or os.getenv("WP_API_BASE")
    if not base_url and not wp_api_base:
        raise ValueError("site.base_url or site.wp_api_base is required")
    if not wp_api_base:
        wp_api_base = f"{base_url.rstrip('/')}/wp-json/wp/v2"
    if not base_url:
        base_url = wp_api_base.replace("/wp-json/wp/v2", "")

    return SiteConfig(
        base_url=base_url,
        wp_api_base=wp_api_base,
        auth_ref=site_payload.get("auth_ref"),
    )
