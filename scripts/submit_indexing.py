#!/usr/bin/env python3
"""
Submit all sweetsworld.com.au posts to Google Indexing API (URL_UPDATED).

Usage:
  python scripts/submit_indexing.py --dry-run
  python scripts/submit_indexing.py
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

SITE_BASE = "https://sweetsworld.com.au"
CREDS_FILE = Path("/Users/michaelzhao/agents/agents/sweetsworld-seo-agent/gsc_credentials.json")

# Google Indexing API
INDEXING_SCOPE = "https://www.googleapis.com/auth/indexing"
INDEXING_ENDPOINT = "https://indexing.googleapis.com/v3/urlNotifications:publish"


def submit_url(url: str, session) -> dict:
    import json as _json
    resp = session.post(INDEXING_ENDPOINT, json={"url": url, "type": "URL_UPDATED"}, timeout=20)
    if resp.status_code >= 400:
        return {"status": "error", "message": f"HTTP {resp.status_code}: {resp.text[:300]}"}
    return {"status": "success", "url": url}


def fetch_all_post_links(username: str, password: str) -> list[str]:
    creds = base64.b64encode(f"{username}:{password}".encode()).decode()
    headers = {"Authorization": f"Basic {creds}"}
    links = []
    for page in range(1, 10):
        url = f"{SITE_BASE}/wp-json/wp/v2/posts?per_page=100&page={page}&_fields=link&status=publish"
        req = Request(url, headers=headers)
        try:
            with urlopen(req, timeout=30) as r:
                data = json.loads(r.read())
                if not data:
                    break
                links.extend(p["link"] for p in data if p.get("link"))
                if len(data) < 100:
                    break
        except Exception as e:
            print(f"  Error fetching page {page}: {e}")
            break
    return links


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    # Load credentials from .env
    env_file = Path(__file__).parent.parent / ".env"
    env = {}
    for line in env_file.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()

    username = env.get("SWEETSWORLD_USERNAME", "")
    password = env.get("SWEETSWORLD_APP_PASSWORD", "")

    print("Fetching all published post URLs...")
    links = fetch_all_post_links(username, password)
    print(f"  {len(links)} URLs to submit\n")

    if args.dry_run:
        for url in links:
            print(f"  [dry-run] {url}")
        print(f"\n(dry-run — {len(links)} URLs listed, nothing submitted)")
        return

    # Setup Google auth
    try:
        from google.auth.transport.requests import AuthorizedSession
        from google.oauth2 import service_account
    except ImportError:
        print("ERROR: pip install google-auth google-auth-httplib2")
        sys.exit(1)

    creds = service_account.Credentials.from_service_account_file(
        str(CREDS_FILE), scopes=[INDEXING_SCOPE]
    )
    session = AuthorizedSession(creds)

    ok = 0
    failed = 0
    for i, url in enumerate(links, 1):
        result = submit_url(url, session)
        if result["status"] == "success":
            print(f"  [{i}/{len(links)}] ✓ {url}")
            ok += 1
        else:
            print(f"  [{i}/{len(links)}] ✗ {url} — {result['message']}")
            failed += 1
        # Google Indexing API rate limit: 200 req/day, be gentle
        time.sleep(0.5)

    print(f"\nDone: {ok} submitted, {failed} failed")


if __name__ == "__main__":
    main()
