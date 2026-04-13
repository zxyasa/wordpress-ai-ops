#!/usr/bin/env python3
"""
Bulk internal link injection for sweetsworld.com.au old posts (pre-2025).
Uses Claude Haiku to find relevant new posts and weave links naturally into content.

Usage:
  python scripts/bulk_internal_links.py --dry-run --batch 5
  python scripts/bulk_internal_links.py --batch 10
  python scripts/bulk_internal_links.py           # all old posts
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))
from wp_snapshot import Snapshotter

SITE_BASE = "https://sweetsworld.com.au"
PROGRESS_FILE = Path(__file__).parent / "bulk_internal_links_progress.json"


def _auth_headers(username: str, password: str) -> dict:
    creds = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {creds}", "Content-Type": "application/json"}


def fetch_all_posts(username: str, password: str) -> list[dict]:
    headers = _auth_headers(username, password)
    posts = []
    for page in range(1, 10):
        url = f"{SITE_BASE}/wp-json/wp/v2/posts?per_page=100&page={page}&_fields=id,title,date,link,content&context=edit&status=publish"
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


def strip_html(h: str) -> str:
    text = re.sub(r"<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", text).strip()


def decode_title(t: str) -> str:
    return html.unescape(t)


def build_link_catalog(new_posts: list[dict]) -> list[dict]:
    """Compact catalog of new posts for Claude context."""
    catalog = []
    for p in new_posts:
        title = decode_title(p["title"]["rendered"])
        raw = p.get("content", {}).get("raw") or p.get("content", {}).get("rendered", "")
        excerpt = strip_html(raw)[:300]
        catalog.append({
            "title": title,
            "url": p["link"],
            "excerpt": excerpt,
        })
    return catalog


def optimize_content_with_links(
    post_url: str,
    post_title: str,
    post_content_html: str,
    link_catalog: list[dict],
) -> str | None:
    """Ask Claude to rewrite content with 2-4 natural internal links. Returns new HTML or None on failure."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        # Try loading from .env
        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("ANTHROPIC_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    catalog_text = "\n".join(
        f'- "{c["title"]}" → {c["url"]}\n  Summary: {c["excerpt"][:150]}'
        for c in link_catalog
    )

    # Strip HTML to plain for Claude, but keep paragraph structure markers
    plain = strip_html(post_content_html)

    prompt = f"""You are an SEO content editor for an Australian candy/lolly ecommerce blog.

Current post:
URL: {post_url}
Title: {post_title}
Content (plain text):
{plain[:3000]}

Available internal links (other posts on the same site):
{catalog_text}

Your task:
1. Choose 2–4 of the most TOPICALLY RELEVANT links from the list above (based on the post content)
2. Rewrite the post content in HTML, adding those links naturally within the text — NOT just at the end
3. Links must feel like natural recommendations, e.g. "...you can find a full range of <a href="...">bulk lollies in Australia</a>..."
4. Keep ALL existing content — do not shorten or remove sections
5. Do NOT link back to the current post URL
6. Do NOT add FAQ sections (already handled separately)
7. Return ONLY the updated HTML content, no commentary

Return the complete post HTML with internal links woven in naturally."""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    result = message.content[0].text.strip()

    # Sanity check: result should contain at least one href to the site
    if "sweetsworld.com.au" not in result:
        return None
    # Should be longer than 100 chars
    if len(result) < 100:
        return None
    return result


def update_post_content(pid: int, new_content: str, username: str, password: str) -> bool:
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


def load_progress() -> dict:
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text())
    return {"done": [], "failed": [], "skipped": []}


def save_progress(progress: dict) -> None:
    PROGRESS_FILE.write_text(json.dumps(progress, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch", type=int, default=0, help="Max posts to process (0=all)")
    parser.add_argument("--reset", action="store_true")
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

    if args.reset and PROGRESS_FILE.exists():
        PROGRESS_FILE.unlink()
        print("Progress reset.")

    progress = load_progress()
    done_ids = set(progress["done"])

    print("Fetching all posts...")
    all_posts = fetch_all_posts(username, password)

    # Split old (pre-2025) vs new (2025+)
    old_posts = [p for p in all_posts if p["date"][:4] < "2025"]
    new_posts = [p for p in all_posts if p["date"][:4] >= "2025"]
    print(f"  Old posts: {len(old_posts)}, New posts (link targets): {len(new_posts)}")

    link_catalog = build_link_catalog(new_posts)

    to_process = [p for p in old_posts if p["id"] not in done_ids]
    if args.batch:
        to_process = to_process[:args.batch]

    print(f"  {len(to_process)} old posts to process")
    if args.dry_run:
        print("  [DRY RUN]\n")

    for i, post in enumerate(to_process, 1):
        pid = post["id"]
        title = decode_title(post["title"]["rendered"])
        post_url = post["link"]
        raw = post.get("content", {}).get("raw") or post.get("content", {}).get("rendered", "")

        print(f"[{i}/{len(to_process)}] [{pid}] {title[:60]}")

        try:
            new_html = optimize_content_with_links(post_url, title, raw, link_catalog)

            if new_html is None:
                print("    Claude returned no usable links — skipping")
                progress["skipped"].append(pid)
                save_progress(progress)
                continue

            # Count links added
            new_links = re.findall(r'href="https://sweetsworld\.com\.au[^"]*"', new_html)
            old_links = re.findall(r'href="https://sweetsworld\.com\.au[^"]*"', raw)
            added = len(new_links) - len(old_links)
            print(f"    +{added} internal links added ({len(new_links)} total)")

            if args.dry_run:
                # Show which links were added
                new_hrefs = set(re.findall(r'href="(https://sweetsworld\.com\.au[^"]*)"', new_html))
                old_hrefs = set(re.findall(r'href="(https://sweetsworld\.com\.au[^"]*)"', raw))
                for href in new_hrefs - old_hrefs:
                    print(f"      → {href}")
                print("    [skip — dry run]")
                continue

            Snapshotter("bulk_internal_links").save("post", pid, title, raw)
            ok = update_post_content(pid, new_html, username, password)
            print(f"    updated: {ok}")
            if not ok:
                raise RuntimeError("update failed")

            progress["done"].append(pid)
            save_progress(progress)

        except Exception as e:
            print(f"    ERROR: {e}")
            progress["failed"].append(pid)
            save_progress(progress)

        time.sleep(2)

    print(f"\nDone. {len(progress['done'])} updated, {len(progress['skipped'])} skipped, {len(progress['failed'])} failed.")


if __name__ == "__main__":
    main()
