#!/usr/bin/env python3
"""Remove 'Uncategorized' (cat id=15) from products that have other categories.

Fixes duplicate URL in sitemap where products accessible at both
/uncategorized/<slug>/ and /<real-cat>/<slug>/. Removing Uncategorized makes
WP serve only the real-category URL.

Safe: skips products where Uncategorized is the ONLY category.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import wp_get, wp_post

UNCATEGORIZED_ID = 15


def clean_slug(slug: str) -> dict:
    p = wp_get(f'wc/v3/products', slug=slug, status='any', _fields='id,name,categories')
    if not p:
        return {'slug': slug, 'status': 'not_found'}
    prod = p[0]
    cur_ids = [c['id'] for c in prod.get('categories', [])]
    if UNCATEGORIZED_ID not in cur_ids:
        return {'pid': prod['id'], 'slug': slug, 'status': 'already_clean'}
    new_ids = [c for c in cur_ids if c != UNCATEGORIZED_ID]
    if not new_ids:
        return {'pid': prod['id'], 'slug': slug, 'status': 'only_uncategorized'}
    r = wp_post(f'wc/v3/products/{prod["id"]}',
                {'categories': [{'id': c} for c in new_ids]})
    return {
        'pid': prod['id'], 'slug': slug, 'name': prod['name'][:50],
        'status': 'cleaned' if r and r.ok else 'fail',
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--csv', required=True, help='Sitemap CSV from Semrush or custom list')
    ap.add_argument('--url-col', default='Link URL')
    ap.add_argument('--rate-sleep', type=float, default=0.15)
    args = ap.parse_args()

    slugs = set()
    with open(args.csv) as f:
        for row in csv.DictReader(f):
            url = row.get(args.url_col, '')
            if '/uncategorized/' in url:
                slugs.add(url.rstrip('/').split('/')[-1])

    print(f"Slugs to check: {len(slugs)}")
    stats = {'cleaned': 0, 'already_clean': 0, 'only_uncategorized': 0, 'not_found': 0, 'fail': 0}
    for slug in sorted(slugs):
        r = clean_slug(slug)
        stats[r['status']] = stats.get(r['status'], 0) + 1
        if r['status'] == 'cleaned':
            print(f"  ✅ {r['pid']} {slug}")
        elif r['status'] == 'only_uncategorized':
            print(f"  ⚠️  {slug}: only has Uncategorized, needs manual review")
        time.sleep(args.rate_sleep)

    print(f"\n=== DONE === {stats}")


if __name__ == '__main__':
    main()
