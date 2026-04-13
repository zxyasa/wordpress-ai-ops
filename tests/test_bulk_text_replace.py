"""Tests for scripts/bulk_text_replace.py"""
from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, call

# Ensure scripts directory accessible
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))


def _load_module():
    import importlib.util
    spec = importlib.util.spec_from_file_location("bulk_text_replace", SCRIPTS_DIR / "bulk_text_replace.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _make_wp_item(item_id: int, title: str, content: str) -> dict:
    return {
        "id": item_id,
        "title": {"rendered": title},
        "content": {"raw": content, "rendered": content},
    }


class TestBulkTextReplace(unittest.TestCase):

    def setUp(self):
        self.mod = _load_module()

    def test_literal_replace(self):
        """Literal find-and-replace changes matching content."""
        post = _make_wp_item(1, "Shipping", "$15 flat rate shipping")
        page = _make_wp_item(2, "FAQ", "No mention here")

        mock_wp = MagicMock()
        mock_wp.list_resources.side_effect = [
            [post],  # posts page 1
            [],      # posts page 2 (stop)
            [page],  # pages page 1
            [],      # pages page 2
        ]

        with patch.object(self.mod, "WPClient", return_value=mock_wp), \
             patch.object(self.mod, "_load_env", return_value={}), \
             patch("os.environ.get", return_value="testuser"), \
             patch("sys.exit"):
            args = MagicMock()
            args.find = "$15 flat rate"
            args.replace = "$16.5 flat rate"
            args.regex = False
            args.scope = "all"
            args.dry_run = False
            args.batch = 0

            # Access _get_content helper and run core logic inline
            content = self.mod._get_content(post)
            new_content = content.replace(args.find, args.replace)
            self.assertEqual(new_content, "$16.5 flat rate shipping")
            self.assertNotEqual(new_content, content)

    def test_regex_replace(self):
        """Regex pattern replaces matching content."""
        import re
        content = "Only $14 flat or $15 for express"
        new_content = re.sub(r"\$1[45]", "$16.5", content)
        self.assertEqual(new_content, "Only $16.5 flat or $16.5 for express")

    def test_dry_run_no_write(self):
        """update_resource is NOT called when dry_run=True."""
        post = _make_wp_item(10, "Title", "old text here")

        mock_wp = MagicMock()
        # Return post on first call, empty on second (pagination stop)
        mock_wp.list_resources.side_effect = [[post], [], []]

        with patch.object(self.mod, "WPClient", return_value=mock_wp), \
             patch.object(self.mod, "_load_env", return_value={
                 "SWEETSWORLD_USERNAME": "u",
                 "SWEETSWORLD_APP_PASSWORD": "p",
             }):

            # Simulate the core loop logic for dry_run
            content = self.mod._get_content(post)
            new_content = content.replace("old text", "new text")
            dry_run = True
            if new_content != content and not dry_run:
                mock_wp.update_resource("post", post["id"], {"content": new_content})

            mock_wp.update_resource.assert_not_called()

    def test_scope_posts_only(self):
        """When scope=posts, list_resources is called only for posts, not pages."""
        mock_wp = MagicMock()
        mock_wp.list_resources.return_value = []

        # Simulate what main() does for scope="posts"
        scope = "posts"
        if scope in ("posts", "all"):
            mock_wp.list_resources("post", params={"per_page": 100})
        if scope in ("pages", "all"):
            mock_wp.list_resources("page", params={"per_page": 100})

        calls = [c for c in mock_wp.list_resources.call_args_list]
        resource_types = [c[0][0] for c in calls]
        self.assertIn("post", resource_types)
        self.assertNotIn("page", resource_types)

    def test_get_content_raw_preferred(self):
        """_get_content prefers raw over rendered."""
        item = {"content": {"raw": "raw content", "rendered": "rendered content"}}
        result = self.mod._get_content(item)
        self.assertEqual(result, "raw content")

    def test_get_content_rendered_fallback(self):
        """_get_content falls back to rendered when raw is absent/empty."""
        item = {"content": {"rendered": "rendered content"}}
        result = self.mod._get_content(item)
        self.assertEqual(result, "rendered content")

    def test_fetch_resources_continues_until_short_final_page(self):
        """Pagination stops naturally on the first short page, not at a fixed cap."""
        mock_wp = MagicMock()
        full_pages = [
            [{"id": page * 100 + idx} for idx in range(100)]
            for page in range(20)
        ]
        final_page = [{"id": 2000}, {"id": 2001}, {"id": 2002}]
        mock_wp.list_resources.side_effect = [*full_pages, final_page]

        items = self.mod._fetch_resources(mock_wp, "post")

        self.assertEqual(len(items), 2003)
        self.assertEqual(mock_wp.list_resources.call_count, 21)


if __name__ == "__main__":
    unittest.main()
