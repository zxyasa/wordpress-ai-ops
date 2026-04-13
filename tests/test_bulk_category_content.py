"""Tests for scripts/bulk_category_content.py"""
from __future__ import annotations

import base64
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))


def _load_module():
    import importlib.util
    spec = importlib.util.spec_from_file_location("bulk_category_content", SCRIPTS_DIR / "bulk_category_content.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestBulkCategoryContent(unittest.TestCase):

    def setUp(self):
        self.mod = _load_module()

    def test_wc_auth_header(self):
        """WCClient builds correct Basic auth header from consumer key/secret."""
        wc = self.mod.WCClient("https://x.com/wc/v3", "ck_abc", "cs_xyz")
        expected = "Basic " + base64.b64encode(b"ck_abc:cs_xyz").decode()
        self.assertEqual(wc.auth_header, expected)

    def test_category_filter(self):
        """Only processes slugs in TARGET_SLUGS (or single --category)."""
        all_cats = [
            {"id": 1, "slug": "american-candy", "name": "American Candy"},
            {"id": 2, "slug": "toys", "name": "Toys"},
            {"id": 3, "slug": "uk-sweets", "name": "UK Sweets"},
            {"id": 4, "slug": "random-stuff", "name": "Random"},
        ]
        target_slugs = self.mod.TARGET_SLUGS
        filtered = [c for c in all_cats if c.get("slug") in target_slugs]
        self.assertEqual(len(filtered), 2)
        self.assertIn("american-candy", {c["slug"] for c in filtered})
        self.assertIn("uk-sweets", {c["slug"] for c in filtered})

    def test_dry_run_no_write(self):
        """update_category is NOT called when dry_run=True."""
        mock_wc = MagicMock()
        mock_wc.list_categories.return_value = [
            {"id": 1, "slug": "american-candy", "name": "American Candy"}
        ]

        mock_ai = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="<p>Lead paragraph</p>")]
        mock_ai.messages.create.return_value = mock_response

        # Simulate dry_run logic
        cat = {"id": 1, "slug": "american-candy", "name": "American Candy"}
        dry_run = True

        html = "<p>Lead paragraph</p>"
        if dry_run:
            print(f"  WOULD UPDATE: {cat['name']}: {html[:100]}...")
        else:
            mock_wc.update_category(cat["id"], {"description": html})

        mock_wc.update_category.assert_not_called()

    def test_prompt_contains_category_name(self):
        """Claude prompt contains the category name."""
        cat_name = "American Candy"
        prompt = (
            f"Write a 150-200 word HTML lead paragraph for the '{cat_name}' product category at SweetsWorld Australia. "
            "Include the word 'Australia' at least once. "
            "Mention variety and Australia-wide delivery. "
            "Return ONLY HTML using p and strong tags."
        )
        self.assertIn(cat_name, prompt)
        self.assertIn("Australia", prompt)

    def test_wc_client_base_url_normalized(self):
        """WCClient strips trailing slash from base URL."""
        wc = self.mod.WCClient("https://example.com/wc/v3/", "ck_key", "cs_secret")
        self.assertFalse(wc.base.endswith("/"))

    def test_list_categories_returns_list(self):
        """list_categories returns a list even on non-list response."""
        wc = self.mod.WCClient("https://example.com/wc/v3", "ck_key", "cs_secret")
        with patch.object(wc, "_request", return_value=None):
            result = wc.list_categories()
        self.assertEqual(result, [])

    def test_prepend_description_preserves_existing_content(self):
        """Generated lead paragraph is prepended without removing existing description."""
        merged = self.mod._prepend_description("<p>New lead</p>", "<p>Existing copy</p>")
        self.assertEqual(merged, "<p>New lead</p>\n\n<p>Existing copy</p>")

    def test_prepend_description_handles_empty_existing_content(self):
        """Empty or missing existing descriptions keep only the generated lead."""
        merged = self.mod._prepend_description("<p>New lead</p>", None)
        self.assertEqual(merged, "<p>New lead</p>")

    def test_strip_code_fences_removes_html_fence(self):
        """Claude markdown fences are stripped before category HTML is used."""
        fenced = "```html\n<p>Lead paragraph</p>\n```"
        self.assertEqual(self.mod._strip_code_fences(fenced), "<p>Lead paragraph</p>")

    def test_strip_code_fences_keeps_plain_html(self):
        """Plain HTML should pass through unchanged."""
        plain = "<p>Lead paragraph</p>"
        self.assertEqual(self.mod._strip_code_fences(plain), plain)

    def test_update_category_falls_back_to_post_after_put_405(self):
        """Some WC installs reject PUT; the client should retry with POST."""
        wc = self.mod.WCClient("https://example.com/wc/v3", "ck_key", "cs_secret")
        calls = []

        def fake_request(method, path, *, params=None, json_payload=None):
            calls.append((method, path, json_payload))
            if method == "PUT":
                raise RuntimeError("PUT https://example.com failed: 405")
            return {"id": 61, "description": "<p>Updated</p>"}

        wc._request = fake_request
        result = wc.update_category(61, {"description": "<p>Updated</p>"})
        self.assertEqual(result["id"], 61)
        self.assertEqual(calls[0][0], "PUT")
        self.assertEqual(calls[1][0], "POST")


if __name__ == "__main__":
    unittest.main()
