from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from wp_ai_ops.exceptions import TargetNotFoundError
from wp_ai_ops.models import MatchSpec, TargetSpec
from wp_ai_ops.target_resolver import (
    _extract_slug_from_url,
    normalize_resource_type,
    resolve_target,
)


class TestNormalizeResourceType:
    def test_post(self):
        assert normalize_resource_type("post") == "post"

    def test_posts_alias(self):
        assert normalize_resource_type("posts") == "post"

    def test_pages_alias(self):
        assert normalize_resource_type("pages") == "page"

    def test_categories_alias(self):
        assert normalize_resource_type("categories") == "category"

    def test_tags_alias(self):
        assert normalize_resource_type("tags") == "tag"

    def test_unknown_passthrough(self):
        assert normalize_resource_type("custom_type") == "custom_type"


class TestExtractSlugFromUrl:
    def test_simple_path(self):
        assert _extract_slug_from_url("https://example.com/my-page") == "my-page"

    def test_nested_path(self):
        assert _extract_slug_from_url("https://example.com/blog/my-post") == "my-post"

    def test_trailing_slash(self):
        assert _extract_slug_from_url("https://example.com/my-page/") == "my-page"

    def test_root_url(self):
        assert _extract_slug_from_url("https://example.com/") == ""

    def test_no_path(self):
        assert _extract_slug_from_url("https://example.com") == ""


class TestResolveTarget:
    def _mock_client(self, get_result=None, list_result=None):
        client = MagicMock()
        if get_result is not None:
            client.get_resource.return_value = get_result
        if list_result is not None:
            client.list_resources.return_value = list_result
        return client

    def test_by_id(self):
        resource = {"id": 42, "title": {"rendered": "Test"}}
        client = self._mock_client(get_result=resource)
        rtype, result = resolve_target(client, TargetSpec("post", MatchSpec("id", 42)))
        assert rtype == "post"
        assert result["id"] == 42
        client.get_resource.assert_called_once_with("post", 42)

    def test_by_slug(self):
        resource = {"id": 42, "slug": "test-page"}
        client = self._mock_client(list_result=[resource])
        rtype, result = resolve_target(client, TargetSpec("page", MatchSpec("slug", "test-page")))
        assert rtype == "page"
        assert result["id"] == 42

    def test_by_title(self):
        resource = {"id": 42, "title": {"rendered": "My Title"}}
        client = self._mock_client(list_result=[resource])
        rtype, result = resolve_target(client, TargetSpec("post", MatchSpec("title", "My Title")))
        assert result["id"] == 42

    def test_by_url(self):
        resource = {"id": 42, "slug": "my-page"}
        client = self._mock_client(list_result=[resource])
        rtype, result = resolve_target(
            client, TargetSpec("page", MatchSpec("url", "https://example.com/my-page"))
        )
        assert result["id"] == 42
        client.list_resources.assert_called_once_with("page", params={"slug": "my-page", "per_page": 1})

    def test_by_search(self):
        resource = {"id": 42, "title": {"rendered": "Result"}}
        client = self._mock_client(list_result=[resource])
        rtype, result = resolve_target(client, TargetSpec("post", MatchSpec("search", "query")))
        assert result["id"] == 42

    def test_not_found(self):
        client = self._mock_client(list_result=[])
        with pytest.raises(TargetNotFoundError, match="Target not found"):
            resolve_target(client, TargetSpec("post", MatchSpec("slug", "nonexistent")))

    def test_unsupported_by(self):
        client = self._mock_client()
        with pytest.raises(TargetNotFoundError, match="Unsupported target match.by"):
            resolve_target(client, TargetSpec("post", MatchSpec("xpath", "//div")))
