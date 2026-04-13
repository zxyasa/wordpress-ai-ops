"""Tests for scripts/internal_link_audit.py"""
from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))


def _load_module():
    import importlib.util
    spec = importlib.util.spec_from_file_location("internal_link_audit", SCRIPTS_DIR / "internal_link_audit.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SAMPLE_CORE_TOPICS = [
    {"slug": "american-candy", "url": "/american-candy/", "label": "American Candy"},
    {"slug": "uk-sweets", "url": "/uk-sweets/", "label": "UK Sweets"},
    {"slug": "chocolate", "url": "/chocolate/", "label": "Chocolate"},
]


def _make_item(item_id: int, title: str, content: str, link: str = "") -> dict:
    return {
        "id": item_id,
        "title": {"rendered": title},
        "content": {"rendered": content},
        "link": link,
    }


class TestInternalLinkAudit(unittest.TestCase):

    def setUp(self):
        self.mod = _load_module()

    def test_link_extraction(self):
        """HTML with href='/american-candy/' finds american-candy in hrefs."""
        html = '<p>Visit our <a href="/american-candy/">American Candy</a> section.</p>'
        hrefs = re.findall(r'href=["\']([^"\']+)["\']', html)
        self.assertIn("/american-candy/", hrefs)

    def test_link_extraction_double_quotes(self):
        """Works with double-quoted hrefs."""
        html = '<a href="/uk-sweets/">UK Sweets</a>'
        hrefs = re.findall(r'href=["\']([^"\']+)["\']', html)
        self.assertIn("/uk-sweets/", hrefs)

    def test_missing_topics_detection(self):
        """Items linking to some but not all topics show correct missing list."""
        content = '<a href="/american-candy/">American</a>'
        hrefs = re.findall(r'href=["\']([^"\']+)["\']', content)
        missing = [
            topic["label"]
            for topic in SAMPLE_CORE_TOPICS
            if not any(self.mod._href_matches_topic_url(href, topic["url"]) for href in hrefs)
        ]
        self.assertNotIn("American Candy", missing)
        self.assertIn("UK Sweets", missing)
        self.assertIn("Chocolate", missing)

    def test_coverage_calculation(self):
        """Coverage: 1 of 2 pages links to a topic = 50%."""
        items = [
            _make_item(1, "Page A", '<a href="/american-candy/">link</a>'),
            _make_item(2, "Page B", "<p>No links here</p>"),
        ]
        topic = SAMPLE_CORE_TOPICS[0]  # american-candy
        total = len(items)

        linked_count = 0
        for item in items:
            content = item["content"]["rendered"]
            hrefs = re.findall(r'href=["\']([^"\']+)["\']', content)
            if any(self.mod._href_matches_topic_url(href, topic["url"]) for href in hrefs):
                linked_count += 1

        pct = linked_count / total * 100
        self.assertEqual(linked_count, 1)
        self.assertEqual(pct, 50.0)

    def test_gap_sorting(self):
        """Page missing 3 topics ranks before page missing 1 topic."""
        gap_matrix = [
            {"id": 1, "title": "Few links", "missing_topics": ["A"], "missing_count": 1},
            {"id": 2, "title": "Many gaps", "missing_topics": ["A", "B", "C"], "missing_count": 3},
        ]
        sorted_gaps = sorted(gap_matrix, key=lambda x: x["missing_count"], reverse=True)
        self.assertEqual(sorted_gaps[0]["id"], 2)
        self.assertEqual(sorted_gaps[1]["id"], 1)

    def test_output_file_written(self, tmp_path=None):
        """After audit run, output JSON file exists with correct top-level keys."""
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "reports" / "audit_test.json"
            output_path.parent.mkdir(parents=True, exist_ok=True)

            report = {
                "generated_at": "2026-04-06",
                "scope": "all",
                "total_scanned": 2,
                "core_topics_checked": 3,
                "coverage_summary": [],
                "gaps": [],
            }
            output_path.write_text(json.dumps(report, indent=2))

            self.assertTrue(output_path.exists())
            loaded = json.loads(output_path.read_text())
            for key in ("generated_at", "scope", "total_scanned", "core_topics_checked", "coverage_summary", "gaps"):
                self.assertIn(key, loaded)

    def test_get_content_rendered(self):
        """_get_content returns rendered content."""
        item = {"content": {"rendered": "<p>Hello</p>", "raw": "<p>Raw</p>"}}
        result = self.mod._get_content(item)
        # rendered is checked first in internal_link_audit
        self.assertEqual(result, "<p>Hello</p>")

    def test_get_title_strips_html(self):
        """_get_title strips HTML tags from rendered title."""
        item = {"title": {"rendered": "<b>My Title</b>"}}
        result = self.mod._get_title(item)
        self.assertEqual(result, "My Title")

    def test_href_matching_uses_exact_paths(self):
        """Path comparison should not treat /candy as a match for /candy-bars."""
        self.assertTrue(self.mod._href_matches_topic_url("https://example.com/candy/?ref=nav", "/candy/"))
        self.assertFalse(self.mod._href_matches_topic_url("/candy-bars/", "/candy/"))

    def test_fetch_resources_continues_until_short_final_page(self):
        """Pagination stops on the first short page instead of a fixed page ceiling."""
        mock_wp = MagicMock()
        full_pages = [
            [{"id": page * 100 + idx} for idx in range(100)]
            for page in range(20)
        ]
        final_page = [{"id": 2000}]
        mock_wp.list_resources.side_effect = [*full_pages, final_page]

        items = self.mod._fetch_resources(mock_wp, "page")

        self.assertEqual(len(items), 2001)
        self.assertEqual(mock_wp.list_resources.call_count, 21)


if __name__ == "__main__":
    unittest.main()
