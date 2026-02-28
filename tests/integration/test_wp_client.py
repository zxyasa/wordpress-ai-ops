from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from wp_ai_ops.exceptions import WPClientError
from wp_ai_ops.wp_client import WPClient


@pytest.fixture
def client():
    return WPClient("https://example.com/wp-json/wp/v2", "user", "pass", timeout=5)


class TestRequest:
    def test_get_success(self, client):
        body = json.dumps({"id": 1, "title": "Test"})
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = f"{body}\n200"

        with patch("subprocess.run", return_value=mock_proc) as mock_run:
            result = client._request("GET", "posts/1")
            assert result == {"id": 1, "title": "Test"}
            call_args = mock_run.call_args[0][0]
            assert "GET" in call_args
            assert any("Authorization" in str(a) for a in call_args)

    def test_post_success(self, client):
        body = json.dumps({"id": 1})
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = f"{body}\n201"

        with patch("subprocess.run", return_value=mock_proc):
            result = client._request("POST", "posts", json_payload={"title": "New"})
            assert result == {"id": 1}

    def test_http_error(self, client):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = '{"error": "not found"}\n404'

        with patch("subprocess.run", return_value=mock_proc):
            with pytest.raises(WPClientError, match="404"):
                client._request("GET", "posts/999")

    def test_retry_logic(self, client):
        fail_proc = MagicMock()
        fail_proc.returncode = 1
        fail_proc.stderr = "connection refused"

        success_proc = MagicMock()
        success_proc.returncode = 0
        success_proc.stdout = '{"id": 1}\n200'

        with patch("subprocess.run", side_effect=[fail_proc, success_proc]) as mock_run:
            result = client._request("GET", "posts/1")
            assert result == {"id": 1}
            assert mock_run.call_count == 2

    def test_auth_header(self, client):
        assert client.auth_header.startswith("Basic ")


class TestListResources:
    def test_success(self, client):
        body = json.dumps([{"id": 1}, {"id": 2}])
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = f"{body}\n200"

        with patch("subprocess.run", return_value=mock_proc):
            rows = client.list_resources("post")
            assert len(rows) == 2

    def test_empty_result(self, client):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = '"not a list"\n200'

        with patch("subprocess.run", return_value=mock_proc):
            rows = client.list_resources("post")
            assert rows == []


class TestGetResource:
    def test_success(self, client):
        body = json.dumps({"id": 42, "title": "Test"})
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = f"{body}\n200"

        with patch("subprocess.run", return_value=mock_proc):
            result = client.get_resource("post", 42)
            assert result["id"] == 42


class TestUpdateResource:
    def test_success(self, client):
        body = json.dumps({"id": 42, "title": "Updated"})
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = f"{body}\n200"

        with patch("subprocess.run", return_value=mock_proc):
            result = client.update_resource("post", 42, {"title": "Updated"})
            assert result["title"] == "Updated"


class TestCreateResource:
    def test_success(self, client):
        body = json.dumps({"id": 99, "title": "New"})
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = f"{body}\n201"

        with patch("subprocess.run", return_value=mock_proc):
            result = client.create_resource("post", {"title": "New"})
            assert result["id"] == 99


class TestContextFallback:
    def test_list_resources_fallback_to_view_on_forbidden_context(self, client):
        with patch.object(client, "_request") as mock_req:
            mock_req.side_effect = [
                WPClientError("GET https://example.com/wp-json/wp/v2/pages failed: 401 {\"code\":\"rest_forbidden_context\"}"),
                [{"id": 1, "slug": "home"}],
            ]
            rows = client.list_resources("page", params={"slug": "home"})
            assert rows == [{"id": 1, "slug": "home"}]
            assert mock_req.call_count == 2
            # Verify fallback happened by checking second call explicitly switched to view.
            assert mock_req.call_args_list[1].kwargs["params"]["context"] == "view"

    def test_get_resource_fallback_post_then_view(self, client):
        with patch.object(client, "_request") as mock_req:
            mock_req.side_effect = [
                WPClientError("GET https://example.com/wp-json/wp/v2/pages/42 failed: 401 {\"code\":\"rest_forbidden_context\"}"),
                {"id": 42, "content": {"raw": "<!-- AI_SLOT:INTRO --><!-- /AI_SLOT:INTRO -->"}},
            ]
            row = client.get_resource("page", 42)
            assert row["id"] == 42
            assert mock_req.call_args_list[0].args[:2] == ("GET", "pages/42")
            assert mock_req.call_args_list[1].args[:2] == ("POST", "pages/42")
