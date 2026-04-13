#!/usr/bin/env python3
"""
Restore all posts to their latest revision before a given timestamp.

Usage:
  python scripts/restore_to_timestamp.py --before "2026-04-06T17:22:00" --dry-run
  python scripts/restore_to_timestamp.py --before "2026-04-06T17:22:00" --batch 10
  python scripts/restore_to_timestamp.py --before "2026-04-06T17:22:00"
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

SITE_BASE = "https://sweetsworld.com.au"
PROGRESS_FILE = Path(__file__).parent / "restore_to_timestamp_progress.json"


def _auth_headers(username: str, password: str) -> dict:
    creds = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {creds}", "Content-Type": "application/json"}


def fetch_all_posts(username: str, password: str) -> list[dict]:
    headers = _auth_headers(username, password)
    posts = []
    for page in range(1, 20):
        url = (
            f"{SITE_BASE}/wp-json/wp/v2/posts"
            f"?per_page=100&page={page}"
            f"&_fields=id,title,modified"
            f"&status=publish"
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


def fetch_revisions(pid: int, username: str, password: str) -> list[dict]:
    headers = _auth_headers(username, password)
    url = f"{SITE_BASE}/wp-json/wp/v2/posts/{pid}/revisions?per_page=100"
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"    Error fetching revisions: {e}")
        return []


def restore_post(pid: int, content: str, username: str, password: str) -> bool:
    headers = _auth_headers(username, password)
    url = f"{SITE_BASE}/wp-json/wp/v2/posts/{pid}?context=edit"
    body = json.dumps({"content": content}).encode()
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
    return {"done": [], "skipped": [], "failed": []}


def save_progress(progress: dict) -> None:
    PROGRESS_FILE.write_text(json.dumps(progress, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", required=True, help="Restore to latest revision before this timestamp (e.g. 2026-04-06T17:22:00)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch", type=int, default=0)
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

    print(f"Restoring all posts to latest revision before: {args.before}")
    print("Fetching all posts...")
    all_posts = fetch_all_posts(username, password)
    print(f"  {len(all_posts)} posts found")

    to_process = [p for p in all_posts if p["id"] not in done_ids]
    if args.batch:
        to_process = to_process[:args.batch]

    print(f"  {len(to_process)} posts to process")
    if args.dry_run:
        print("  [DRY RUN]\n")

    for i, post in enumerate(to_process, 1):
        pid = post["id"]
        title = post["title"]["rendered"]
        print(f"[{i}/{len(to_process)}] [{pid}] {title[:65]}")

        revisions = fetch_revisions(pid, username, password)
        if not revisions:
            print("    no revisions found — skipping")
            progress["skipped"].append(pid)
            save_progress(progress)
            continue

        # Find latest revision before the cutoff timestamp
        eligible = [r for r in revisions if r["modified"] <= args.before]
        if not eligible:
            print(f"    no revision before {args.before} — skipping")
            progress["skipped"].append(pid)
            save_progress(progress)
            continue

        # Sort by modified descending, pick latest before cutoff
        eligible.sort(key=lambda r: r["modified"], reverse=True)
        target = eligible[0]
        print(f"    restoring revision {target['id']} ({target['modified']})")

        if args.dry_run:
            content_preview = target.get("content", {}).get("rendered", "")[:80]
            print(f"    preview: {content_preview!r}")
            print("    [skip — dry run]")
            continue

        content = target.get("content", {}).get("rendered", "")
        ok = restore_post(pid, content, username, password)
        print(f"    updated: {ok}")

        if ok:
            progress["done"].append(pid)
        else:
            progress["failed"].append(pid)
        save_progress(progress)
        time.sleep(0.5)

    print(f"\nDone. {len(progress['done'])} restored, {len(progress['skipped'])} skipped, {len(progress['failed'])} failed.")


if __name__ == "__main__":
    main()
