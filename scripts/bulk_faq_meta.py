#!/usr/bin/env python3
"""
Bulk FAQ + RankMath meta backfill for sweetsworld.com.au.

Usage:
  python scripts/bulk_faq_meta.py --dry-run     # preview only
  python scripts/bulk_faq_meta.py               # live run
  python scripts/bulk_faq_meta.py --batch 10    # process first 10
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

# Allow importing from src/
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wp_ai_ops.faq_generator import generate_faqs, generate_meta
from wp_ai_ops.handlers import handle_append_faq

SITE_BASE = "https://sweetsworld.com.au"
PROGRESS_FILE = Path(__file__).parent / "bulk_faq_meta_progress.json"


def _auth_headers(username: str, password: str) -> dict:
    creds = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {creds}", "Content-Type": "application/json"}


def fetch_all_posts(username: str, password: str) -> list[dict]:
    headers = _auth_headers(username, password)
    posts = []
    for page in range(1, 10):
        url = f"{SITE_BASE}/wp-json/wp/v2/posts?per_page=100&page={page}&_fields=id,title,date,content,meta,link&context=edit"
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


def needs_faq(post: dict) -> bool:
    content = post.get("content", {}).get("raw") or post.get("content", {}).get("rendered", "")
    return "FAQPage" not in content


def needs_meta(post: dict) -> bool:
    meta = post.get("meta", {})
    return not meta.get("rank_math_focus_keyword", "").strip()


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
        print(f"    HTTP {e.code} updating post {pid}: {e.read()[:200]}")
        return False
    except Exception as e:
        print(f"    Error updating post {pid}: {e}")
        return False


def write_meta_via_db(pid: int, meta: dict, username: str, password: str) -> bool:
    from urllib.parse import urlencode
    token = os.environ.get('WP_SEO_BRIDGE_TOKEN', 'sw_seo_meta_k8x2')
    params = urlencode({
        "token": token,
        "post_id": pid,
        "keyword": meta.get("rank_math_focus_keyword", ""),
        "title": meta.get("rank_math_title", ""),
        "description": meta.get("rank_math_description", ""),
    })
    url = f"{SITE_BASE}/wp-seo-meta.php?{params}"
    req = Request(url)
    try:
        with urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
            return bool(data.get("ok"))
    except Exception as e:
        print(f"    Error writing meta for post {pid}: {e}")
        return False


def load_progress() -> dict:
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text())
    return {"done": [], "failed": []}


def save_progress(progress: dict) -> None:
    PROGRESS_FILE.write_text(json.dumps(progress, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch", type=int, default=0, help="Max posts to process (0=all)")
    parser.add_argument("--reset", action="store_true", help="Reset progress file")
    args = parser.parse_args()

    env_file = Path(__file__).parent.parent / ".env"
    env = {}
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()

    username = env.get("SWEETSWORLD_USERNAME") or os.environ.get("SWEETSWORLD_USERNAME", "")
    password = env.get("SWEETSWORLD_APP_PASSWORD") or os.environ.get("SWEETSWORLD_APP_PASSWORD", "")
    if not username or not password:
        print("ERROR: SWEETSWORLD_USERNAME / SWEETSWORLD_APP_PASSWORD not set")
        sys.exit(1)

    if args.reset and PROGRESS_FILE.exists():
        PROGRESS_FILE.unlink()
        print("Progress reset.")

    progress = load_progress()
    done_ids = set(progress["done"])
    failed_ids = set(progress["failed"])

    print("Fetching all posts...")
    posts = fetch_all_posts(username, password)
    print(f"  {len(posts)} posts fetched")

    to_process = [
        p for p in posts
        if p["id"] not in done_ids
        and (needs_faq(p) or needs_meta(p))
    ]

    if args.batch:
        to_process = to_process[:args.batch]

    print(f"  {len(to_process)} posts need FAQ/meta (batch={args.batch or 'all'})")
    if args.dry_run:
        print("  [DRY RUN — no changes will be made]")
    print()

    for i, post in enumerate(to_process, 1):
        pid = post["id"]
        title = post["title"]["rendered"][:60]
        post_url = post.get("link", f"{SITE_BASE}/?p={pid}")
        do_faq = needs_faq(post)
        do_meta = needs_meta(post)
        label = ("FAQ+meta" if do_faq and do_meta else ("FAQ" if do_faq else "meta"))
        print(f"[{i}/{len(to_process)}] [{pid}] {label}: {title}")

        # Fetch page content for Claude context
        content_raw = post.get("content", {}).get("raw") or post.get("content", {}).get("rendered", "")
        page_title = re.sub(r"<[^>]+>", "", post["title"]["rendered"])

        try:
            # --- Generate meta ---
            meta_result = generate_meta(post_url, page_title, content_raw[:1500], site_context="candy_blog")
            print(f"    meta: title='{meta_result['title'][:50]}' kw='{meta_result['keyword']}'")

            # --- Generate FAQ ---
            faqs = []
            if do_faq:
                faqs = generate_faqs(post_url, page_title, content_raw[:2000], site_context="candy_blog")
                print(f"    faq: {len(faqs)} items generated")

            if args.dry_run:
                print("    [skip — dry run]")
                continue

            # --- Apply FAQ to content ---
            if do_faq and faqs:
                handler_result = handle_append_faq(post, faqs)
                if handler_result.changed:
                    new_content = handler_result.patch_payload.get("content", content_raw)
                    ok = update_post_content(pid, new_content, username, password)
                    print(f"    content updated: {ok}")
                    if not ok:
                        raise RuntimeError("content update failed")
                else:
                    print(f"    FAQ skipped: {handler_result.warnings}")

            # --- Apply meta via DB endpoint ---
            meta_payload = {
                "rank_math_focus_keyword": meta_result["keyword"],
                "rank_math_title": meta_result["title"],
                "rank_math_description": meta_result["description"],
            }
            ok = write_meta_via_db(pid, meta_payload, username, password)
            print(f"    meta written: {ok}")
            if not ok:
                raise RuntimeError("meta write failed")

            progress["done"].append(pid)
            save_progress(progress)

        except Exception as e:
            print(f"    ERROR: {e}")
            progress["failed"].append(pid)
            save_progress(progress)

        # Small pause to avoid hammering the API
        time.sleep(1.5)

    print(f"\nDone. {len(progress['done'])} completed, {len(progress['failed'])} failed.")
    if progress["failed"]:
        print(f"Failed IDs: {progress['failed']}")


if __name__ == "__main__":
    main()
