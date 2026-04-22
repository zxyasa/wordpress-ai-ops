#!/usr/bin/env python3
"""Batch rewrite RankMath titles for too-long / H1=title duplicate URLs.

Input: CSV of URLs (one per row, column "Page URL").
Output: idempotent rewrite using the pattern:
    <Product Name> | SweetsWorld Australia  (if fits ≤65)
    <Product Name> | SweetsWorld             (if fits ≤70)
    <Product Name truncated>                  (fallback)

This tool was used 2026-04-21 to fix 740 URLs from Semrush Site Audit.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import WP_BASE, wp_get, write_rank_math_meta, safe_request, SEO_TOKEN


def make_title(name: str) -> str:
    name = (name or '').strip()
    if not name:
        return ''
    suffix_long = ' | SweetsWorld Australia'    # 25 chars
    suffix_short = ' | SweetsWorld'              # 14 chars
    if len(name) + len(suffix_long) <= 65:
        return name + suffix_long
    if len(name) + len(suffix_short) <= 70:
        return name + suffix_short
    return name[:70].rstrip()


def url_to_slug(url: str) -> str:
    return url.replace(WP_BASE, '').strip('/').split('/')[-1]


def normalize_name(name: str) -> str:
    return (name
            .replace('&#8217;', "'")
            .replace('&#038;', '&')
            .replace('&#8212;', '—')
            .replace('&amp;', '&')
            .replace('&mdash;', '—'))


def find_post(slug: str) -> tuple[int, str] | None:
    """Return (pid, name) for slug, checking products/posts/pages in order."""
    for ep in ('wc/v3/products', 'wp/v2/posts', 'wp/v2/pages'):
        data = wp_get(ep, slug=slug, status='any')
        if data:
            name = data[0].get('name') or data[0].get('title', {}).get('rendered', '')
            return data[0]['id'], normalize_name(name)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--csv', required=True, help='CSV with "Page URL" column')
    ap.add_argument('--rate-sleep', type=float, default=0.2)
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    urls = set()
    with open(args.csv) as f:
        for row in csv.DictReader(f):
            if 'Page URL' in row:
                urls.add(row['Page URL'])

    print(f"Total URLs: {len(urls)}")
    stats = {'ok': 0, 'fail': 0, 'not_found': 0}
    for i, url in enumerate(sorted(urls), 1):
        slug = url_to_slug(url)
        found = find_post(slug)
        if not found:
            stats['not_found'] += 1
            continue
        pid, name = found
        new_title = make_title(name)
        if not new_title:
            continue
        if args.dry_run:
            print(f"  [dry] {pid} {slug[:40]}: {new_title}")
            continue
        ok = write_rank_math_meta(pid, title=new_title)
        stats['ok' if ok else 'fail'] += 1
        if i % 25 == 0:
            print(f"  {i}/{len(urls)}  {stats}")
        time.sleep(args.rate_sleep)

    print(f"\n=== DONE ===  {stats}")


if __name__ == '__main__':
    main()
