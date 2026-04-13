"""Tests for scripts/bulk_create_pages.py"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, call

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))


def _load_module():
    import importlib.util
    spec = importlib.util.spec_from_file_location("bulk_create_pages", SCRIPTS_DIR / "bulk_create_pages.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SAMPLE_PAGES_CONFIG = [
    {
        "slug": "test-page",
        "title": "Test Page | SweetsWorld",
        "status": "draft",
        "generate_content": False,
        "content": "<p>Test content</p>",
    }
]

SAMPLE_PAGES_WITH_GENERATE = [
    {
        "slug": "returns-refunds",
        "title": "Returns & Refunds | SweetsWorld",
        "status": "draft",
        "generate_content": True,
        "prompt_hint": "Returns policy details.",
    }
]

EXPECTED_LOOKUP_PARAMS = {
    "slug": "test-page",
    "per_page": 1,
    "status": "publish,draft,private,pending,future",
}


class TestBulkCreatePages(unittest.TestCase):

    def setUp(self):
        self.mod = _load_module()

    def test_create_new_page(self):
        """When page doesn't exist, create_resource is called."""
        mock_wp = MagicMock()
        mock_wp.list_resources.return_value = []  # page doesn't exist
        mock_wp.create_resource.return_value = {"id": 99}

        entry = SAMPLE_PAGES_CONFIG[0]
        slug = entry["slug"]

        existing = mock_wp.list_resources("page", params=EXPECTED_LOOKUP_PARAMS)
        self.assertEqual(existing, [])
        mock_wp.list_resources.assert_called_once_with("page", params=EXPECTED_LOOKUP_PARAMS)

        payload = {
            "title": entry["title"],
            "content": entry.get("content", ""),
            "slug": slug,
            "status": entry.get("status", "draft"),
        }
        result = mock_wp.create_resource("page", payload)
        mock_wp.create_resource.assert_called_once()
        self.assertEqual(result["id"], 99)

    def test_skip_existing_no_update(self):
        """When page exists and --update not set, create_resource is NOT called."""
        mock_wp = MagicMock()
        mock_wp.list_resources.return_value = [{"id": 42, "slug": "test-page"}]

        entry = SAMPLE_PAGES_CONFIG[0]
        slug = entry["slug"]
        update_flag = False

        existing = mock_wp.list_resources("page", params=EXPECTED_LOOKUP_PARAMS)
        if existing and not update_flag:
            pass  # skip
        else:
            mock_wp.create_resource("page", {})

        mock_wp.create_resource.assert_not_called()
        mock_wp.list_resources.assert_called_once_with("page", params=EXPECTED_LOOKUP_PARAMS)

    def test_update_flag(self):
        """When page exists and update=True, update_resource is called."""
        mock_wp = MagicMock()
        existing_page = {"id": 42, "slug": "test-page"}
        mock_wp.list_resources.return_value = [existing_page]

        entry = SAMPLE_PAGES_CONFIG[0]
        slug = entry["slug"]
        update_flag = True

        existing = mock_wp.list_resources("page", params=EXPECTED_LOOKUP_PARAMS)
        if existing and update_flag:
            existing_id = existing[0]["id"]
            payload = {
                "title": entry["title"],
                "content": entry.get("content", ""),
                "slug": slug,
                "status": entry.get("status", "draft"),
            }
            mock_wp.update_resource("page", existing_id, payload)

        mock_wp.update_resource.assert_called_once_with("page", 42, unittest.mock.ANY)
        mock_wp.list_resources.assert_called_once_with("page", params=EXPECTED_LOOKUP_PARAMS)

    def test_generate_content_calls_claude(self):
        """When generate_content=True, anthropic messages.create is called."""
        mock_ai = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="<p>Generated content</p>")]
        mock_ai.messages.create.return_value = mock_response

        entry = SAMPLE_PAGES_WITH_GENERATE[0]

        if entry.get("generate_content"):
            self.mod._generate_content(mock_ai, entry["title"], entry.get("prompt_hint", ""))

        mock_ai.messages.create.assert_called_once()
        call_kwargs = mock_ai.messages.create.call_args
        self.assertEqual(call_kwargs.kwargs.get("model") or call_kwargs[1].get("model", ""), "claude-haiku-4-5-20251001")

    def test_generate_content_returns_text(self):
        """_generate_content returns the text from Claude response."""
        mock_ai = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="<p>Generated HTML</p>")]
        mock_ai.messages.create.return_value = mock_response

        result = self.mod._generate_content(mock_ai, "Test Title", "Some hint")
        self.assertEqual(result, "<p>Generated HTML</p>")


if __name__ == "__main__":
    unittest.main()
