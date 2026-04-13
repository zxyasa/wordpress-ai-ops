#!/usr/bin/env python3
"""
Inject Claude-generated lead paragraph into WooCommerce product category descriptions.

Usage:
  python scripts/bulk_category_content.py --dry-run
  python scripts/bulk_category_content.py --category american-candy
  python scripts/bulk_category_content.py --batch 3
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
from urllib import error as urlerror
from urllib import request as urlrequest
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).parent))
from wp_snapshot import Snapshotter

WC_API_BASE = "https://sweetsworld.com.au/wp-json/wc/v3"

TARGET_SLUGS = [
    "american-candy",
    "uk-sweets",
    "australian-lollies",
    "bulk-lollies",
    "gift-boxes",
    "party-sweets",
    "chocolate",
]


class WCClient:
    def __init__(self, wc_api_base: str, consumer_key: str, consumer_secret: str, timeout: int = 20):
        self.base = wc_api_base.rstrip("/")
        self.timeout = timeout
        token = base64.b64encode(f"{consumer_key}:{consumer_secret}".encode()).decode()
        self.auth_header = f"Basic {token}"

    def _request(self, method: str, path: str, *, params=None, json_payload=None):
        url = f"{self.base}/{path.lstrip('/')}"
        if params:
            url = f"{url}?{urlencode(params)}"
        headers = {"Authorization": self.auth_header, "Accept": "application/json"}
        body = None
        if json_payload is not None:
            headers["Content-Type"] = "application/json; charset=utf-8"
            body = json.dumps(json_payload, ensure_ascii=False).encode("utf-8")
        for attempt in range(3):
            try:
                req = urlrequest.Request(url=url, data=body, headers=headers, method=method.upper())
                with urlrequest.urlopen(req, timeout=self.timeout) as resp:
                    data = resp.read() or b""
                return json.loads(data.decode("utf-8", errors="replace")) if data else None
            except urlerror.HTTPError as exc:
                err = exc.read().decode("utf-8", errors="replace")[:300] if hasattr(exc, "read") else str(exc)
                if attempt < 2:
                    time.sleep(1)
                    continue
                raise RuntimeError(f"{method} {url} failed: {exc.code} {err}") from exc
            except Exception as exc:
                if attempt < 2:
                    time.sleep(1)
                    continue
                raise RuntimeError(f"{method} {url} failed: {exc}") from exc

    def list_categories(self, per_page: int = 100) -> list[dict]:
        result = self._request("GET", "products/categories", params={"per_page": per_page})
        return result if isinstance(result, list) else []

    def get_category(self, category_id: int) -> dict:
        result = self._request("GET", f"products/categories/{category_id}")
        return result if isinstance(result, dict) else {}

    def update_category(self, category_id: int, payload: dict) -> dict:
        path = f"products/categories/{category_id}"
        try:
            result = self._request("PUT", path, json_payload=payload)
        except RuntimeError as exc:
            if " failed: 405" not in str(exc):
                raise
            result = self._request("POST", path, json_payload=payload)
        return result if isinstance(result, dict) else {}


def _load_env() -> dict:
    env_file = Path(__file__).parent.parent / ".env"
    env: dict = {}
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


def _prepend_description(lead_html: str, existing_description: str | None) -> str:
    lead = lead_html.strip()
    existing = (existing_description or "").strip()
    if not existing:
        return lead
    if not lead:
        return existing
    return f"{lead}\n\n{existing}"


def _strip_code_fences(text: str) -> str:
    value = (text or "").strip()
    if not value.startswith("```"):
        return value

    value = re.sub(r"^```[A-Za-z0-9_-]*\s*\n?", "", value, count=1)
    value = re.sub(r"\n?```$", "", value, count=1)
    return value.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Inject Claude-generated lead paragraph into WC category descriptions")
    parser.add_argument("--category", help="Single category slug to process")
    parser.add_argument("--dry-run", action="store_true", help="Preview only — no writes")
    parser.add_argument("--batch", type=int, default=0, help="Max categories to process (0=all)")
    args = parser.parse_args()

    env = _load_env()
    consumer_key = env.get("WC_CONSUMER_KEY") or os.environ.get("WC_CONSUMER_KEY", "")
    consumer_secret = env.get("WC_CONSUMER_SECRET") or os.environ.get("WC_CONSUMER_SECRET", "")
    anthropic_key = env.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY", "")

    if not consumer_key or not consumer_secret:
        print("WARNING: WC_CONSUMER_KEY / WC_CONSUMER_SECRET not set — WooCommerce calls will fail at runtime")

    import anthropic

    wc = WCClient(WC_API_BASE, consumer_key, consumer_secret)
    ai = anthropic.Anthropic(api_key=anthropic_key)

    print("Fetching WooCommerce categories...")
    all_cats = wc.list_categories()
    print(f"  {len(all_cats)} categories fetched")

    target_slugs = [args.category] if args.category else TARGET_SLUGS
    categories = [c for c in all_cats if c.get("slug") in target_slugs]
    print(f"  {len(categories)} matching target slugs")

    if args.batch:
        categories = categories[: args.batch]

    if args.dry_run:
        print("[DRY RUN — no changes will be written]\n")

    updated = 0
    failed = 0

    for cat in categories:
        cat_id = cat["id"]
        cat_name = cat["name"]
        cat_slug = cat.get("slug", "")

        print(f"Processing [{cat_slug}]: {cat_name}")

        prompt = (
            f"Write a 150-200 word HTML lead paragraph for the '{cat_name}' product category at SweetsWorld Australia. "
            "Include the word 'Australia' at least once. "
            "Mention variety and Australia-wide delivery. "
            "Return ONLY HTML using p and strong tags."
        )

        try:
            resp = ai.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            )
            html = _strip_code_fences(resp.content[0].text)

            if args.dry_run:
                print(f"  WOULD UPDATE: {cat_name}: {html[:100]}...")
                continue

            existing_category = wc.get_category(cat_id)
            if not existing_category:
                raise RuntimeError(f"Failed to fetch existing description for category {cat_slug}")
            existing_description = existing_category.get("description")
            merged_description = _prepend_description(html, existing_description)

            Snapshotter("bulk_category_content").save("category", cat_id, cat_name, existing_description or "")
            wc.update_category(cat_id, {"description": merged_description})
            print(f"  Updated: {cat_name}")
            updated += 1
            time.sleep(0.5)

        except Exception as exc:
            print(f"  ERROR [{cat_slug}]: {exc}")
            failed += 1

    print(f"\nDone. Updated: {updated}, Failed: {failed}")


if __name__ == "__main__":
    main()
