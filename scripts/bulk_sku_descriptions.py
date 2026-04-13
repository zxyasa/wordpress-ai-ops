#!/usr/bin/env python3
"""
Generate 200-word short_descriptions for Top 50 WooCommerce products.

Usage:
  python scripts/bulk_sku_descriptions.py --dry-run
  python scripts/bulk_sku_descriptions.py --batch 10
  python scripts/bulk_sku_descriptions.py --slug my-product-slug
  python scripts/bulk_sku_descriptions.py --reset
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

WC_API_BASE = "https://sweetsworld.com.au/wp-json/wc/v3"
PROGRESS_FILE = Path(__file__).parent / "bulk_sku_progress.json"


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

    def list_products(self, per_page: int = 50, orderby: str = "popularity", order: str = "desc") -> list[dict]:
        result = self._request("GET", "products", params={"per_page": per_page, "orderby": orderby, "order": order})
        return result if isinstance(result, list) else []

    def get_product_by_slug(self, slug: str) -> dict | None:
        result = self._request("GET", "products", params={"slug": slug, "per_page": 1})
        if isinstance(result, list) and result:
            return result[0]
        return None

    def update_product(self, product_id: int, payload: dict) -> dict:
        result = self._request("POST", f"products/{product_id}", json_payload=payload)
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


def _load_progress() -> dict:
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text())
    return {"done": [], "failed": []}


def _save_progress(progress: dict) -> None:
    PROGRESS_FILE.write_text(json.dumps(progress, indent=2))


def _count_words(html: str) -> int:
    """Strip HTML tags, then count words."""
    text = re.sub(r"<[^>]+>", " ", html)
    return len(text.split())


def _is_bad_html(html: str) -> bool:
    """Detect corrupted/React HTML that should be replaced."""
    if not html:
        return False
    return any(marker in html for marker in ["data-start=", "react-scroll", "overflow-hidden", "flex-1"])


def _strip_markdown_fences(text: str) -> str:
    return re.sub(r"^```(?:html)?\n?|\n?```$", "", text.strip(), flags=re.MULTILINE)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate short_descriptions for top WC products")
    parser.add_argument("--dry-run", action="store_true", help="Preview only — no writes")
    parser.add_argument("--batch", type=int, default=50, help="Max products to process (default: 50)")
    parser.add_argument("--min-length", type=int, default=80, help="Skip if word count >= this (default: 80)")
    parser.add_argument("--slug", help="Single product slug to process")
    parser.add_argument("--reset", action="store_true", help="Clear progress file before starting")
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

    if args.reset and PROGRESS_FILE.exists():
        PROGRESS_FILE.unlink()
        print("Progress reset.")

    progress = _load_progress()
    done_ids = set(progress["done"])

    if args.slug:
        product = wc.get_product_by_slug(args.slug)
        products = [product] if product else []
        print(f"Single product mode: {args.slug}")
    else:
        print(f"Fetching top {args.batch} products by popularity...")
        products = wc.list_products(per_page=args.batch, orderby="popularity", order="desc")
        print(f"  {len(products)} products fetched")

    if args.dry_run:
        print("[DRY RUN — no changes will be written]\n")

    processed = 0
    skipped = 0
    failed = 0

    for product in products:
        pid = product["id"]
        name = product.get("name", "Unknown")

        if pid in done_ids:
            print(f"SKIP [{name}] (already in progress)")
            skipped += 1
            continue

        short_desc = product.get("short_description", "")
        long_desc = product.get("description", "")
        short_words = _count_words(short_desc)
        long_words = _count_words(long_desc)

        needs_short = short_words < args.min_length or _is_bad_html(short_desc)
        needs_long = long_words < 100 or _is_bad_html(long_desc)

        if not needs_short and not needs_long:
            print(f"SKIP [{name}] (short: {short_words}w ✅, long: {long_words}w ✅)")
            skipped += 1
            continue

        cats = product.get("categories", [])[:2]
        categories_str = ", ".join(c["name"] for c in cats) if cats else "candy"

        print(f"Processing [{name}] (short: {short_words}w→{'generate' if needs_short else 'keep'}, long: {long_words}w→{'generate' if needs_long else 'keep'})...")

        try:
            payload: dict = {}

            if needs_short:
                prompt_short = (
                    f"Write a 200-word engaging short description for '{name}', "
                    f"a {categories_str} candy available at SweetsWorld Australia. "
                    "Highlight taste, texture, and occasions (party, gift, school lunchbox). "
                    "Return ONLY HTML using p and strong tags. Do not mention price or shipping."
                )
                resp = ai.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=512,
                    messages=[{"role": "user", "content": prompt_short}],
                )
                payload["short_description"] = _strip_markdown_fences(resp.content[0].text)

            if needs_long:
                prompt_long = (
                    f"Write a 400-word product description for '{name}', "
                    f"a {categories_str} candy available at SweetsWorld Australia. "
                    "Cover: taste and texture, background/history if relevant, serving suggestions, "
                    "occasions (parties, gifts, lunchboxes), and why to buy from SweetsWorld. "
                    "Return ONLY HTML using h2, p, ul, li, and strong tags. Do not mention price or shipping."
                )
                resp_long = ai.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt_long}],
                )
                payload["description"] = _strip_markdown_fences(resp_long.content[0].text)

            if args.dry_run:
                for field, content in payload.items():
                    print(f"  WOULD UPDATE {field}: {content[:80]}...")
                processed += 1
                continue

            wc.update_product(pid, payload)
            progress["done"].append(pid)
            _save_progress(progress)
            print(f"  Updated: {name} ({', '.join(payload.keys())})")
            processed += 1
            time.sleep(0.4)

        except Exception as exc:
            print(f"  ERROR [{name}]: {exc}")
            progress["failed"].append(pid)
            _save_progress(progress)
            failed += 1

    print(f"\nDone. Processed: {processed}, Skipped: {skipped}, Failed: {failed}")


if __name__ == "__main__":
    main()
