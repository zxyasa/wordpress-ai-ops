#!/usr/bin/env python3
"""
Find-and-replace text across all WP posts and/or pages.

Usage:
  python scripts/bulk_text_replace.py --find "$15 flat rate" --replace "$16.5 flat rate" --dry-run
  python scripts/bulk_text_replace.py --find "old text" --replace "new text" --scope posts
  python scripts/bulk_text_replace.py --find r"\\$1[45]" --replace "$16.5" --regex
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

from wp_ai_ops.wp_client import WPClient
from wp_snapshot import Snapshotter

SITE_API = "https://sweetsworld.com.au/wp-json/wp/v2"


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
        return c.get("raw") or c.get("rendered", "")
    return str(c)


def main() -> None:
    parser = argparse.ArgumentParser(description="Bulk find-and-replace across WP posts/pages")
    parser.add_argument("--find", required=True, help="Text (or regex pattern) to find")
    parser.add_argument("--replace", required=True, help="Replacement text")
    parser.add_argument("--regex", action="store_true", help="Treat --find as Python regex")
    parser.add_argument(
        "--scope",
        choices=["posts", "pages", "all"],
        default="all",
        help="Which resources to scan (default: all)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview only — no writes")
    parser.add_argument("--batch", type=int, default=0, help="Max items to process (0=all)")
    args = parser.parse_args()

    env = _load_env()
    username = env.get("SWEETSWORLD_USERNAME") or os.environ.get("SWEETSWORLD_USERNAME", "")
    password = env.get("SWEETSWORLD_APP_PASSWORD") or os.environ.get("SWEETSWORLD_APP_PASSWORD", "")
    if not username or not password:
        print("ERROR: SWEETSWORLD_USERNAME / SWEETSWORLD_APP_PASSWORD not set")
        sys.exit(1)

    wp = WPClient(wp_api_base=SITE_API, username=username, app_password=password)

    all_items: list[tuple[str, dict]] = []  # (resource_type, item)
    if args.scope in ("posts", "all"):
        print("Fetching posts...")
        posts = _fetch_resources(wp, "post")
        print(f"  {len(posts)} posts fetched")
        all_items.extend(("post", p) for p in posts)
    if args.scope in ("pages", "all"):
        print("Fetching pages...")
        pages = _fetch_resources(wp, "page")
        print(f"  {len(pages)} pages fetched")
        all_items.extend(("page", p) for p in pages)

    if args.batch:
        all_items = all_items[: args.batch]

    if args.dry_run:
        print("[DRY RUN — no changes will be written]\n")

    changed = 0
    skipped = 0

    for resource_type, item in all_items:
        pid = item["id"]
        title_raw = item.get("title", {})
        title = (title_raw.get("rendered", "") if isinstance(title_raw, dict) else str(title_raw))[:50]
        content = _get_content(item)

        if args.regex:
            new_content = re.sub(args.find, args.replace, content)
        else:
            new_content = content.replace(args.find, args.replace)

        if new_content == content:
            skipped += 1
            continue

        print(f"[{pid}] {title} — changed")
        changed += 1

        if not args.dry_run:
            Snapshotter("bulk_text_replace").save(resource_type, pid, title, content)
            wp.update_resource(resource_type, pid, {"content": new_content})
            time.sleep(0.3)

    print(f"\nDone. Changed: {changed}, Skipped: {skipped}")


if __name__ == "__main__":
    main()
