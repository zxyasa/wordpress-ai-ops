#!/usr/bin/env python3
"""
Find and fix posts where Claude accidentally injected ```html code fences.

Usage:
  python scripts/fix_markdown_fences.py --dry-run          # scan only, no writes
  python scripts/fix_markdown_fences.py --dry-run --limit 1 # check first affected post
  python scripts/fix_markdown_fences.py --limit 1           # fix first affected post
  python scripts/fix_markdown_fences.py                     # fix all affected posts
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from pathlib import Path

SITE_BASE = "https://sweetsworld.com.au"


def _auth_headers(username: str, password: str) -> dict:
    creds = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {creds}", "Content-Type": "application/json"}


def fetch_all_posts(username: str, password: str) -> list[dict]:
    from urllib.request import Request, urlopen

    headers = _auth_headers(username, password)
    posts = []
    for page in range(1, 20):
        url = (
            f"{SITE_BASE}/wp-json/wp/v2/posts"
            f"?per_page=100&page={page}"
            f"&_fields=id,title,link,content"
            f"&context=edit&status=publish"
        )
        req = Request(url, headers=headers)
        try:
            with urlopen(req, timeout=30) as r:
                data = json.loads(r.read())
                if not data:
                    break
                posts.extend(data)
                if len(data) < 100:
                    break
        except Exception as e:
            print(f"  Error fetching page {page}: {e}")
            break
    return posts


def strip_fences(content: str) -> str:
    """Remove ```html ... ``` or ``` ... ``` wrapping from content."""
    fixed = re.sub(r"^```(?:html)?\s*\n?", "", content)
    fixed = re.sub(r"\n?```\s*$", "", fixed)
    return fixed.strip()


def update_post(pid: int, new_content: str, username: str, password: str) -> bool:
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError

    url = f"{SITE_BASE}/wp-json/wp/v2/posts/{pid}?context=edit"
    headers = _auth_headers(username, password)
    body = json.dumps({"content": new_content}).encode()
    req = Request(url, data=body, headers=headers, method="POST")
    try:
        with urlopen(req, timeout=30) as r:
            result = json.loads(r.read())
            return "id" in result
    except HTTPError as e:
        print(f"    HTTP {e.code}: {e.read()[:200]}")
        return False
    except Exception as e:
        print(f"    Error: {e}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0, help="Max posts to fix (0=all)")
    args = parser.parse_args()

    env_file = Path(__file__).parent.parent / ".env"
    env = {}
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()

    username = env.get("SWEETSWORLD_USERNAME", "")
    password = env.get("SWEETSWORLD_APP_PASSWORD", "")

    print("Fetching all posts...")
    all_posts = fetch_all_posts(username, password)
    print(f"  {len(all_posts)} posts fetched")

    # Find affected posts
    affected = []
    for p in all_posts:
        raw = p.get("content", {}).get("raw", "")
        if "```" in raw:
            affected.append(p)

    print(f"  {len(affected)} posts contain ``` fences\n")

    if not affected:
        print("Nothing to fix.")
        return

    to_fix = affected[:args.limit] if args.limit else affected

    for i, post in enumerate(to_fix, 1):
        pid = post["id"]
        title = post["title"]["rendered"]
        raw = post["content"]["raw"]
        fixed = strip_fences(raw)

        print(f"[{i}/{len(to_fix)}] [{pid}] {title[:65]}")
        print(f"    before: {raw[:80]!r}")
        print(f"    after:  {fixed[:80]!r}")

        if args.dry_run:
            print("    [skip — dry run]")
            continue

        ok = update_post(pid, fixed, username, password)
        print(f"    updated: {ok}")

    print(f"\nDone.")


if __name__ == "__main__":
    main()
