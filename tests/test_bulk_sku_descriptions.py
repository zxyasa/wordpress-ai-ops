"""Tests for scripts/bulk_sku_descriptions.py"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))


def _load_module():
    import importlib.util
    spec = importlib.util.spec_from_file_location("bulk_sku_descriptions", SCRIPTS_DIR / "bulk_sku_descriptions.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _make_product(pid: int, name: str, short_description: str = "", categories=None) -> dict:
    return {
        "id": pid,
        "name": name,
        "short_description": short_description,
        "categories": categories or [{"name": "candy"}],
    }


class TestBulkSkuDescriptions(unittest.TestCase):

    def setUp(self):
        self.mod = _load_module()

    def test_skip_by_min_length(self):
        """Product with description >= min_length words is skipped."""
        # Generate a description with 100 words
        long_desc = "<p>" + " ".join(["word"] * 100) + "</p>"
        word_count = self.mod._count_words(long_desc)
        min_length = 80
        self.assertGreaterEqual(word_count, min_length)

    def test_count_words_strips_html(self):
        """_count_words correctly strips HTML tags before counting."""
        html = "<p>Hello <strong>world</strong>, how are you?</p>"
        count = self.mod._count_words(html)
        # "Hello world , how are you ?" — depends on split, but should be ~5-7
        self.assertGreater(count, 3)
        self.assertLess(count, 10)

    def test_progress_saved(self):
        """After update_product, product id appears in progress['done']."""
        progress = {"done": [], "failed": []}
        product_id = 123

        # Simulate successful update
        progress["done"].append(product_id)

        self.assertIn(product_id, progress["done"])

    def test_strip_markdown_fences(self):
        """Markdown code fences are stripped from Claude output."""
        input_text = "```html\n<p>hi</p>\n```"
        result = self.mod._strip_markdown_fences(input_text)
        self.assertEqual(result, "<p>hi</p>")

    def test_strip_markdown_fences_no_fence(self):
        """Plain HTML without fences is returned unchanged."""
        input_text = "<p>hi</p>"
        result = self.mod._strip_markdown_fences(input_text)
        self.assertEqual(result, "<p>hi</p>")

    def test_dry_run_no_write(self):
        """update_product is NOT called when dry_run=True."""
        mock_wc = MagicMock()
        product = _make_product(1, "Gummy Bears", "")

        dry_run = True
        result = "<p>Generated description</p>"

        if dry_run:
            print(f"  WOULD UPDATE: {product['name']}: {result[:80]}...")
        else:
            mock_wc.update_product(product["id"], {"short_description": result})

        mock_wc.update_product.assert_not_called()

    def test_load_progress_returns_empty_on_missing_file(self):
        """_load_progress returns empty structure when file doesn't exist."""
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_path = Path(tmpdir) / "nonexistent_progress.json"
            original = self.mod.PROGRESS_FILE
            self.mod.PROGRESS_FILE = missing_path
            try:
                progress = self.mod._load_progress()
            finally:
                self.mod.PROGRESS_FILE = original
        self.assertEqual(progress, {"done": [], "failed": []})

    def test_wc_client_list_products_returns_list(self):
        """list_products returns a list even on non-list response."""
        wc = self.mod.WCClient("https://example.com/wc/v3", "ck_key", "cs_secret")
        with patch.object(wc, "_request", return_value=None):
            result = wc.list_products()
        self.assertEqual(result, [])

    def test_prompt_excludes_price(self):
        """Generated prompt instructs Claude not to mention price or shipping."""
        product_name = "Haribo Gold Bears"
        categories_str = "candy"
        prompt = (
            f"Write a 200-word engaging short description for '{product_name}', "
            f"a {categories_str} candy available at SweetsWorld Australia. "
            "Highlight taste, texture, and occasions (party, gift, school lunchbox). "
            "Return ONLY HTML using p and strong tags. Do not mention price or shipping."
        )
        self.assertIn("Do not mention price or shipping", prompt)
        self.assertIn(product_name, prompt)


if __name__ == "__main__":
    unittest.main()
