#!/usr/bin/env python3
"""
Audit posts/pages for missing links to 12 core topic pages.

Usage:
  python scripts/internal_link_audit.py
  python scripts/internal_link_audit.py --scope posts
  python scripts/internal_link_audit.py --gsc-data /path/to/gsc.json
  python scripts/internal_link_audit.py --output reports/my_audit.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wp_ai_ops.wp_client import WPClient

SITE_API = "https://sweetsworld.com.au/wp-json/wp/v2"

DEFAULT_CORE_PAGES = Path(__file__).parent.parent / "data" / "core_topic_pages.yaml"


def _load_env() -> dict:
    env_file = Path(__file__).parent.parent / ".env"
    env: dict = {}
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


def _fetch_resources(wp: WPClient, resource_type: str) -> list[dict]:
    items: list[dict] = []
    page = 1
    per_page = 100
    while True:
        batch = wp.list_resources(
            resource_type,
            params={"per_page": per_page, "page": page, "status": "publish", "context": "edit"},
        )
        if not batch:
            break
        items.extend(batch)
        if len(batch) < per_page:
            break
        page += 1
    return items


def _get_content(item: dict) -> str:
    c = item.get("content", {})
    if isinstance(c, dict):
        return c.get("rendered", "") or c.get("raw", "")
    return str(c)


def _get_title(item: dict) -> str:
    t = item.get("title", {})
    if isinstance(t, dict):
        return re.sub(r"<[^>]+>", "", t.get("rendered", ""))
    return str(t)


def _normalized_path(url: str) -> str:
    path = urlparse(url).path.rstrip("/")
    return path or "/"


def _href_matches_topic_url(href: str, topic_url: str) -> bool:
    return _normalized_path(href) == _normalized_path(topic_url)


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit WP posts/pages for missing core topic links")
    parser.add_argument(
        "--scope",
        choices=["posts", "pages", "all"],
        default="all",
        help="Which resources to scan (default: all)",
    )
    parser.add_argument(
        "--core-pages",
        type=Path,
        default=DEFAULT_CORE_PAGES,
        help="Path to core_topic_pages.yaml",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output JSON path (default: reports/internal_link_audit_YYYY-MM-DD.json)",
    )
    parser.add_argument(
        "--gsc-data",
        type=Path,
        default=None,
        help="Optional GSC JSON list [{page, impressions, clicks}]",
    )
    args = parser.parse_args()

    if args.output is None:
        args.output = (
            Path(__file__).parent.parent / "reports" / f"internal_link_audit_{date.today()}.json"
        )

    env = _load_env()
    username = env.get("SWEETSWORLD_USERNAME") or os.environ.get("SWEETSWORLD_USERNAME", "")
    password = env.get("SWEETSWORLD_APP_PASSWORD") or os.environ.get("SWEETSWORLD_APP_PASSWORD", "")
    if not username or not password:
        print("ERROR: SWEETSWORLD_USERNAME / SWEETSWORLD_APP_PASSWORD not set")
        sys.exit(1)

    wp = WPClient(wp_api_base=SITE_API, username=username, app_password=password)

    # Load core topic pages
    if not args.core_pages.exists():
        print(f"ERROR: Core pages file not found: {args.core_pages}")
        sys.exit(1)

    with open(args.core_pages, encoding="utf-8") as f:
        core_data = yaml.safe_load(f)
    core_topics = core_data.get("pages", [])
    print(f"Loaded {len(core_topics)} core topic pages")

    # Load GSC data if provided
    gsc_map: dict[str, dict] = {}
    if args.gsc_data and args.gsc_data.exists():
        with open(args.gsc_data, encoding="utf-8") as f:
            gsc_list = json.load(f)
        for entry in gsc_list:
            page = entry.get("page", "")
            if page:
                gsc_map[page] = entry

    # Fetch resources
    all_items: list[dict] = []
    if args.scope in ("posts", "all"):
        print("Fetching posts...")
        posts = _fetch_resources(wp, "post")
        print(f"  {len(posts)} posts fetched")
        all_items.extend(posts)
    if args.scope in ("pages", "all"):
        print("Fetching pages...")
        pages = _fetch_resources(wp, "page")
        print(f"  {len(pages)} pages fetched")
        all_items.extend(pages)

    print(f"\nAnalyzing {len(all_items)} items...")

    gap_matrix: list[dict] = []

    for item in all_items:
        content = _get_content(item)
        hrefs = re.findall(r'href=["\']([^"\']+)["\']', content)
        missing = [
            topic["label"]
            for topic in core_topics
            if not any(_href_matches_topic_url(href, topic["url"]) for href in hrefs)
        ]

        item_url = item.get("link", "")
        entry: dict = {
            "id": item["id"],
            "title": _get_title(item),
            "url": item_url,
            "missing_topics": missing,
            "missing_count": len(missing),
        }

        # Enrich with GSC data
        if gsc_map and item_url:
            gsc_entry = gsc_map.get(item_url, {})
            if gsc_entry:
                entry["impressions"] = gsc_entry.get("impressions", 0)
                entry["clicks"] = gsc_entry.get("clicks", 0)

        gap_matrix.append(entry)

    # Sort by missing count descending
    gap_matrix.sort(key=lambda x: x["missing_count"], reverse=True)

    # Coverage summary: for each topic, count items that DO link to it
    total = len(all_items)
    coverage_summary = []
    for topic in core_topics:
        linked_count = sum(
            1 for entry in gap_matrix if topic["label"] not in entry["missing_topics"]
        )
        pct = round(linked_count / total * 100, 1) if total else 0.0
        coverage_summary.append(
            {
                "topic": topic["label"],
                "slug": topic["slug"],
                "url": topic["url"],
                "linked_in": linked_count,
                "total": total,
                "coverage_pct": pct,
            }
        )

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "generated_at": date.today().isoformat(),
        "scope": args.scope,
        "total_scanned": total,
        "core_topics_checked": len(core_topics),
        "coverage_summary": coverage_summary,
        "gaps": gap_matrix,
    }

    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nReport written to: {output_path}")

    # Print coverage table
    print(f"\n{'Topic':<25} {'Coverage'}")
    print("-" * 45)
    for entry in coverage_summary:
        label = entry["topic"]
        linked = entry["linked_in"]
        pct = entry["coverage_pct"]
        print(f"{label:<25} {linked}/{total} ({pct}%)")


if __name__ == "__main__":
    main()
