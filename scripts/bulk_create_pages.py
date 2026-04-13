#!/usr/bin/env python3
"""
Create or upsert WP Pages from a YAML file, optionally generating content with Claude.

Usage:
  python scripts/bulk_create_pages.py --dry-run
  python scripts/bulk_create_pages.py --update
  python scripts/bulk_create_pages.py --input data/pages_to_create.yaml
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wp_ai_ops.wp_client import WPClient

SITE_API = "https://sweetsworld.com.au/wp-json/wp/v2"
SITE_BASE = "https://sweetsworld.com.au"
EXISTING_PAGE_STATUSES = "publish,draft,private,pending,future"

DEFAULT_INPUT = Path(__file__).parent.parent / "data" / "pages_to_create.yaml"


def _load_env() -> dict:
    env_file = Path(__file__).parent.parent / ".env"
    env: dict = {}
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


def _generate_content(ai_client, title: str, prompt_hint: str) -> str:
    prompt = (
        f'Write a WordPress page for sweetsworld.com.au titled "{title}". '
        f"{prompt_hint}. "
        "Return ONLY valid HTML using p, h2, ul, li, strong tags. No markdown. ~600 words."
    )
    resp = ai_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    import re
    raw = resp.content[0].text
    # Strip markdown code fences
    raw = re.sub(r"^```html\s*\n?", "", raw)
    raw = re.sub(r"\n?```\s*$", "", raw)
    raw = raw.strip()
    # Strip full HTML document wrapper if AI returned <!DOCTYPE html>...</html>
    body_match = re.search(r"<body[^>]*>(.*?)</body>", raw, re.DOTALL | re.IGNORECASE)
    if body_match:
        raw = body_match.group(1).strip()
    return raw


def _submit_indexing(url: str) -> None:
    """Silently submit URL to Google Indexing API — skip if SA JSON unavailable."""
    try:
        sa_json = os.environ.get("GOOGLE_SA_JSON_PATH", "")
        if not sa_json or not Path(sa_json).exists():
            return
        from google.oauth2 import service_account  # type: ignore
        from googleapiclient.discovery import build  # type: ignore

        creds = service_account.Credentials.from_service_account_file(
            sa_json, scopes=["https://www.googleapis.com/auth/indexing"]
        )
        svc = build("indexing", "v3", credentials=creds)
        svc.urlNotifications().publish(body={"url": url, "type": "URL_UPDATED"}).execute()
        print(f"  Submitted to Google Indexing: {url}")
    except Exception:
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or upsert WP Pages from YAML")
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="Path to YAML file (default: data/pages_to_create.yaml)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview only — no writes")
    parser.add_argument("--update", action="store_true", help="Overwrite existing page by slug")
    parser.add_argument(
        "--submit-indexing",
        action="store_true",
        help="Submit created pages to Google Indexing API (requires SA JSON)",
    )
    args = parser.parse_args()

    env = _load_env()
    username = env.get("SWEETSWORLD_USERNAME") or os.environ.get("SWEETSWORLD_USERNAME", "")
    password = env.get("SWEETSWORLD_APP_PASSWORD") or os.environ.get("SWEETSWORLD_APP_PASSWORD", "")
    if not username or not password:
        print("ERROR: SWEETSWORLD_USERNAME / SWEETSWORLD_APP_PASSWORD not set")
        sys.exit(1)

    anthropic_key = env.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY", "")

    wp = WPClient(wp_api_base=SITE_API, username=username, app_password=password)

    import anthropic

    ai = anthropic.Anthropic(api_key=anthropic_key) if anthropic_key else None

    if not args.input.exists():
        print(f"ERROR: Input file not found: {args.input}")
        sys.exit(1)

    with open(args.input, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    pages_config = data.get("pages", [])
    print(f"Loaded {len(pages_config)} pages from {args.input}")

    if args.dry_run:
        print("[DRY RUN — no changes will be written]\n")

    created = 0
    updated = 0
    skipped = 0

    for entry in pages_config:
        slug = entry["slug"]
        title = entry["title"]
        status = entry.get("status", "draft")
        generate = entry.get("generate_content", False)

        # Check if page already exists
        existing = wp.list_resources(
            "page",
            params={"slug": slug, "per_page": 1, "status": EXISTING_PAGE_STATUSES},
        )
        if existing and not args.update:
            print(f"SKIP [{slug}] — already exists (use --update to overwrite)")
            skipped += 1
            continue

        # Generate content if requested
        content = entry.get("content", "")
        if generate and ai:
            print(f"  Generating content for [{slug}]...")
            content = _generate_content(ai, title, entry.get("prompt_hint", ""))
        elif generate and not ai:
            print(f"  WARNING: generate_content=true but ANTHROPIC_API_KEY not set for [{slug}]")

        payload = {
            "title": title,
            "content": content,
            "slug": slug,
            "status": status,
        }

        if args.dry_run:
            action = "UPDATE" if existing else "CREATE"
            print(f"WOULD {action} [{slug}]: {title}")
            continue

        if existing and args.update:
            existing_id = existing[0]["id"]
            wp.update_resource("page", existing_id, payload)
            print(f"UPDATED [{slug}]: {title}")
            updated += 1
            if args.submit_indexing:
                _submit_indexing(f"{SITE_BASE}/{slug}/")
        else:
            result = wp.create_resource("page", payload)
            print(f"CREATED [{slug}]: {title} (id={result.get('id', '?')})")
            created += 1
            if args.submit_indexing:
                _submit_indexing(f"{SITE_BASE}/{slug}/")

        time.sleep(0.5)

    print(f"\nDone. Created: {created}, Updated: {updated}, Skipped: {skipped}")


if __name__ == "__main__":
    main()
