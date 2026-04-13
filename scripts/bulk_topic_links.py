#!/usr/bin/env python3
"""
Inject internal links to core topic pages across all published posts.

Strategy (safe, non-destructive):
  1. Claude picks relevant topics + suggests anchor text that EXISTS in the post
  2. Python finds that exact text in the raw HTML and wraps it with <a href="...">
  3. Claude NEVER rewrites HTML — the original structure is always preserved

Usage:
  python scripts/bulk_topic_links.py --dry-run --batch 5
  python scripts/bulk_topic_links.py --batch 5
  python scripts/bulk_topic_links.py --reset   # clear progress, then exit
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

import yaml

import sys as _sys
_sys.path.insert(0, str(Path(__file__).parent))
from wp_snapshot import Snapshotter

SITE_BASE = "https://sweetsworld.com.au"
PROGRESS_FILE = Path(__file__).parent / "bulk_topic_links_progress.json"
CORE_TOPICS_FILE = Path(__file__).parent.parent / "data" / "core_topic_pages.yaml"


def _auth_headers(username: str, password: str) -> dict:
    creds = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {creds}", "Content-Type": "application/json"}


def load_topic_pages() -> list[dict]:
    data = yaml.safe_load(CORE_TOPICS_FILE.read_text())
    # Only use SEO topic pages (not trust pages like faq/shipping/returns)
    trust_slugs = {"faq", "shipping", "returns-refunds"}
    return [p for p in data.get("pages", []) if p["slug"] not in trust_slugs]


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


def strip_html(h: str) -> str:
    text = re.sub(r"<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", text).strip()


def already_linked_slugs(content_html: str, topic_pages: list[dict]) -> list[str]:
    linked = []
    for t in topic_pages:
        if t["url"] in content_html or t["slug"] in content_html:
            linked.append(t["slug"])
    return linked


def select_topics_and_anchors(
    post_title: str,
    post_plain_text: str,
    topic_pages: list[dict],
) -> list[dict]:
    """
    Ask Claude to select relevant topics and find anchor text that exists in the post.
    Returns list of {"slug": ..., "url": ..., "anchor": ...} dicts.
    Claude only does analysis — no HTML output.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("ANTHROPIC_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    topics_list = "\n".join(
        f'  {{"slug": "{t["slug"]}", "url": "{SITE_BASE}{t["url"]}", "label": "{t["label"]}"}}'
        for t in topic_pages
    )

    prompt = f"""You are an SEO analyst for SweetsWorld.com.au, an Australian candy store.

Post title: {post_title}

Post plain text (first 2000 chars):
{post_plain_text[:2000]}

Available topic pages:
{topics_list}

Task:
1. Choose 1–3 topic pages that are TOPICALLY RELEVANT to this post
2. For each chosen topic, find a SHORT PHRASE (2–5 words) that:
   - Already exists VERBATIM in the post text above
   - Would make natural anchor text for that topic page
   - Is NOT already a link
3. Return ONLY a JSON array, no explanation. Example:
[
  {{"slug": "american-candy", "url": "https://sweetsworld.com.au/american-candy/", "anchor": "American candy"}},
  {{"slug": "bulk-lollies", "url": "https://sweetsworld.com.au/bulk-lollies/", "anchor": "bulk lollies"}}
]
If no suitable anchor text exists in the post for a topic, skip that topic.
Return an empty array [] if nothing fits."""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    result = message.content[0].text.strip()

    # Strip markdown fences
    result = re.sub(r"^```(?:json)?\s*", "", result)
    result = re.sub(r"\s*```$", "", result)
    result = result.strip()

    try:
        selections = json.loads(result)
        if not isinstance(selections, list):
            return []
        return [s for s in selections if isinstance(s, dict) and "slug" in s and "anchor" in s]
    except json.JSONDecodeError:
        return []


def inject_links_into_html(raw_html: str, selections: list[dict]) -> tuple[str, list[str]]:
    """
    Inject <a href="..."> tags into raw_html by finding anchor text.
    - Only wraps the FIRST occurrence of each anchor phrase
    - Skips if the phrase is already inside an <a> tag
    - Never modifies HTML structure
    Returns (new_html, list_of_injected_anchors).
    """
    injected = []
    result = raw_html

    for sel in selections:
        anchor = sel.get("anchor", "").strip()
        url = sel.get("url", "").strip()
        if not anchor or not url:
            continue

        # Build pattern: case-insensitive, match exact phrase, not already in <a>
        escaped = re.escape(anchor)
        pattern = re.compile(escaped, re.IGNORECASE)

        # Check if this phrase appears outside of <a>...</a> tags
        # Strategy: find first match, then check it's not inside an <a> tag
        match = pattern.search(result)
        if not match:
            continue

        # Check not already inside <a> tag: look for <a before match without closing </a>
        before = result[:match.start()]
        open_a = before.rfind("<a ")
        close_a = before.rfind("</a>")
        if open_a > close_a:
            # We're inside an <a> tag — skip
            continue

        # Inject link
        linked_text = f'<a href="{url}">{match.group(0)}</a>'
        result = result[:match.start()] + linked_text + result[match.end():]
        injected.append(f"{anchor} → {url}")

    return result, injected


def update_post_content(pid: int, new_content: str, username: str, password: str) -> bool:
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError

    url = f"{SITE_BASE}/wp-json/wp/v2/posts/{pid}?context=edit"
    headers = _auth_headers(username, password)
    body = json.dumps({"content": new_content}).encode()
    req = Request(url, data=body, headers=headers, method="POST")
    try:
        with urlopen(req, timeout=30) as r:
            res = json.loads(r.read())
            return "id" in res
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
    parser.add_argument("--dry-run", action="store_true", help="Preview only, no writes")
    parser.add_argument("--batch", type=int, default=0, help="Max posts to process (0=all)")
    parser.add_argument("--reset", action="store_true", help="Clear progress and exit")
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

    if not username or not password:
        print("ERROR: SWEETSWORLD_USERNAME / SWEETSWORLD_APP_PASSWORD not set in .env")
        sys.exit(1)

    if args.reset:
        if PROGRESS_FILE.exists():
            PROGRESS_FILE.unlink()
        print("Progress reset. Run again without --reset to process posts.")
        sys.exit(0)

    topic_pages = load_topic_pages()
    print(f"Loaded {len(topic_pages)} topic pages:")
    for t in topic_pages:
        print(f"  {t['label']} → {t['url']}")

    progress = load_progress()
    done_ids = set(progress["done"])

    print("\nFetching all published posts...")
    all_posts = fetch_all_posts(username, password)
    print(f"  {len(all_posts)} posts fetched")

    to_process = [p for p in all_posts if p["id"] not in done_ids]
    if args.batch:
        to_process = to_process[:args.batch]

    print(f"  {len(to_process)} posts to process")
    if args.dry_run:
        print("  [DRY RUN — no writes]\n")

    for i, post in enumerate(to_process, 1):
        pid = post["id"]
        title = html.unescape(post["title"]["rendered"])
        raw = post.get("content", {}).get("raw") or post.get("content", {}).get("rendered", "")

        print(f"[{i}/{len(to_process)}] [{pid}] {title[:65]}")

        already = already_linked_slugs(raw, topic_pages)
        available = [t for t in topic_pages if t["slug"] not in already]
        if not available:
            print("    all topics already linked — skipping")
            progress["skipped"].append(pid)
            save_progress(progress)
            continue

        if already:
            print(f"    already links to: {', '.join(already)}")

        try:
            plain = strip_html(raw)
            selections = select_topics_and_anchors(title, plain, available)

            if not selections:
                print("    Claude found no suitable anchor text — skipping")
                progress["skipped"].append(pid)
                save_progress(progress)
                continue

            new_html, injected = inject_links_into_html(raw, selections)

            if not injected:
                print("    anchor text not found in HTML — skipping")
                progress["skipped"].append(pid)
                save_progress(progress)
                continue

            print(f"    +{len(injected)} links:")
            for item in injected:
                print(f"      {item}")

            if args.dry_run:
                print("    [skip — dry run]")
                continue

            # Snapshot before writing
            Snapshotter("bulk_topic_links").save("post", pid, title, raw)
            print(f"    snapshot saved → snapshots/bulk_topic_links/post_{pid}.json")

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

        time.sleep(1)

    print(f"\nDone. {len(progress['done'])} updated, {len(progress['skipped'])} skipped, {len(progress['failed'])} failed.")


if __name__ == "__main__":
    main()
