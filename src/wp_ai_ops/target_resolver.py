from __future__ import annotations

from urllib.parse import urlparse

from .exceptions import TargetNotFoundError
from .models import TargetSpec
from .wp_client import WPClient


RESOURCE_ALIAS = {
    "post": "post",
    "posts": "post",
    "page": "page",
    "pages": "page",
    "category": "category",
    "categories": "category",
    "tag": "tag",
    "tags": "tag",
    "ux-blocks": "ux-blocks",
    "blocks": "ux-blocks",
    "menu-items": "menu-items",
    "nav_menu_item": "menu-items",
    "template-parts": "template-parts",
    "wp_template_part": "template-parts",
}


def normalize_resource_type(value: str) -> str:
    return RESOURCE_ALIAS.get(value, value)


def _extract_slug_from_url(url: str) -> str:
    path = urlparse(url).path.strip("/")
    if not path:
        return ""
    return path.split("/")[-1]


def _normalize_url_path(url: str) -> str:
    path = urlparse(url).path or "/"
    normalized = "/" + path.strip("/") if path.strip("/") else "/"
    return normalized


def resolve_target(client: WPClient, target: TargetSpec) -> tuple[str, dict]:
    resource_type = normalize_resource_type(target.type)
    by = target.match.by
    value = target.match.value

    if by == "id":
        item = client.get_resource(resource_type, int(value))
        return resource_type, item

    if by == "slug":
        rows = client.list_resources(resource_type, params={"slug": value, "per_page": 1})
    elif by == "title":
        rows = client.list_resources(resource_type, params={"search": value, "per_page": 20})
        rows = [r for r in rows if (r.get("title", {}).get("rendered", "").strip().lower() == str(value).strip().lower())]
    elif by == "url":
        requested_url = str(value)
        slug = _extract_slug_from_url(requested_url)
        rows = []
        if slug:
            rows = client.list_resources(resource_type, params={"slug": slug, "per_page": 1})
        # Fallback for root URL or custom permalink edge cases.
        if not rows:
            path = _normalize_url_path(requested_url)
            candidates = client.list_resources(resource_type, params={"per_page": 100})
            rows = [r for r in candidates if _normalize_url_path(str(r.get("link", ""))) == path]
    elif by == "search":
        rows = client.list_resources(resource_type, params={"search": value, "per_page": 1})
    else:
        raise TargetNotFoundError(f"Unsupported target match.by: {by}")

    if not rows:
        raise TargetNotFoundError(f"Target not found: type={resource_type}, by={by}, value={value}")
    return resource_type, rows[0]
