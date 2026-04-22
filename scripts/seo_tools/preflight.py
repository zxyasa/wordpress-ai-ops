#!/usr/bin/env python3
"""Preflight for new landing page: URL availability + inventory scan.

Usage:
    python3 preflight.py --slug dubai-chocolate --keywords "dubai chocolate,pistachio chocolate"

Output: JSON with URL existence across page/cat/tag/post + matching product inventory.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import wp_get


def check_url_existence(slug: str) -> dict:
    out = {}
    for ep, label in (
        ('wp/v2/pages', 'page'),
        ('wc/v3/products/categories', 'category'),
        ('wc/v3/products/tags', 'tag'),
        ('wp/v2/posts', 'post'),
    ):
        data = wp_get(ep, slug=slug, status='any') if 'wp/v2' in ep else wp_get(ep, slug=slug)
        if data:
            out[label] = [{'id': d.get('id'), 'slug': d.get('slug'),
                           'count': d.get('count', '')} for d in data]
    return out


def inventory_scan(keywords: list[str]) -> dict:
    """Find instock + imaged products matching keyword list (union-dedupe)."""
    unique: dict[int, dict] = {}
    for q in keywords:
        data = wp_get('wc/v3/products', search=q, per_page=30, status='publish')
        if not data:
            continue
        for p in data:
            if p['id'] in unique:
                continue
            if p.get('stock_status') != 'instock' or not p.get('images'):
                continue
            unique[p['id']] = {
                'id': p['id'],
                'name': p['name'],
                'slug': p['slug'],
                'permalink': p.get('permalink', ''),
            }

    # Brand breakdown
    brand_patterns = [
        ("Reese's", 'reese'), ("Hershey's", 'hershey'), ('Jolly Rancher', 'jolly rancher'),
        ('Nerds', 'nerd'), ('Skittles', 'skittle'), ('Airheads', 'airhead'),
        ('Starburst', 'starburst'), ('Jelly Belly', 'jelly belly'),
        ('Hostess/Twinkies', 'hostess'), ('Fluff', 'fluff'), ('Nik-L-Nip', 'nik'),
        ('Takis', 'takis'), ('Sour Patch Kids', 'sour patch'), ('Warheads', 'warhead'),
        ('Mike & Ike', 'mike and ike'), ('Hot Tamales', 'hot tamales'),
        ('Tootsie', 'tootsie'), ('Darrell Lea', 'darrell lea'), ('Allens', 'allens'),
        ('Cheetos', 'cheeto'), ('Doritos', 'dorito'), ('Pringles', 'pringles'),
    ]
    brands: dict[str, int] = defaultdict(int)
    for p in unique.values():
        n = p['name'].lower()
        matched = False
        for label, pat in brand_patterns:
            if pat in n:
                brands[label] += 1
                matched = True
                break
        if not matched:
            brands['Other'] += 1

    return {
        'total_unique': len(unique),
        'products': list(unique.values()),
        'brands': dict(sorted(brands.items(), key=lambda x: -x[1])),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--slug', required=True, help='Candidate URL slug')
    ap.add_argument('--keywords', required=True, help='Comma-separated search terms')
    ap.add_argument('--output', default='-')
    args = ap.parse_args()

    keywords = [k.strip() for k in args.keywords.split(',') if k.strip()]

    result = {
        'slug': args.slug,
        'url_conflicts': check_url_existence(args.slug),
        'inventory': inventory_scan(keywords),
    }

    if args.output == '-':
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        json.dump(result, open(args.output, 'w'), indent=2, ensure_ascii=False)
        print(f"→ {args.output}", file=sys.stderr)


if __name__ == '__main__':
    main()
