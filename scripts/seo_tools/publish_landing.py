#!/usr/bin/env python3
"""Publish a new landing page with the 5-step SEO workflow:
  1. Validate featured products (stock + image + publish)
  2. Substitute WOOCOMMERCE_PRODUCT_GRID placeholder with shortcode
  3. Create/update WP page
  4. Write RankMath SEO meta
  5. Add inbound internal links from related hub pages

Bundle schema (per landing):
{
  "slug": "...",
  "page_title": "...",
  "meta_description": "...",
  "focus_keyword": "...",
  "content_html": "<full HTML with <details> for FAQ>",
  "featured_product_ids": [int],
  "internal_links": [{"anchor":"...","url":"..."}],
  "hero_image_prompt": "..."
}
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (WP_BASE, wp_get, wp_post, write_rank_math_meta,
                    validate_product, strip_flatsome_grid_conflict,
                    purge_wp_rocket_paths, check_slug_collision,
                    suggest_safe_slug)


def substitute_grid_placeholder(content: str, product_ids: list[int]) -> str:
    ids_str = ','.join(str(x) for x in product_ids)
    return re.sub(
        r'<!--\s*WOOCOMMERCE_PRODUCT_GRID:\s*ids=[0-9,\s]+\s+cols=(\d+)\s*-->',
        lambda m: f'[products ids="{ids_str}" columns="{m.group(1)}" orderby="menu_order"]',
        content,
    )


def publish_landing(bundle: dict, dry_run: bool = False,
                    force: bool = False) -> dict:
    slug = bundle['slug']

    # Step 0: slug collision preflight (hard gate)
    col = check_slug_collision(slug)
    if not col['safe']:
        hits = []
        if col['cats']:
            hits.append(f"WC cat {col['cats'][0]['id']} '{col['cats'][0]['name']}' "
                        f"({col['cats'][0]['count']} products)")
        if col['tags']:
            hits.append(f"WC tag {col['tags'][0]['id']} '{col['tags'][0]['name']}' "
                        f"({col['tags'][0]['count']} products)")
        suggestion = suggest_safe_slug(slug)
        msg = (f"🚫 SLUG COLLISION on '/{slug}/' — {' + '.join(hits)}. "
               f"This URL renders a WC archive, the page would be invisible. "
               f"Suggested safe slug: /{suggestion}/")
        if force:
            print(f"  ⚠️  {msg}")
            print("  (continuing because --force)")
        else:
            print(f"  {msg}")
            return {'slug': slug, 'error': 'slug_collision', 'collision': col,
                    'suggestion': suggestion}

    # Step 1: validate products
    valid_ids = []
    invalid = []
    for pid in bundle.get('featured_product_ids', []):
        v = validate_product(pid)
        if v['ok']:
            valid_ids.append(pid)
        else:
            invalid.append({'pid': pid, 'issues': v.get('issues', [])})
    print(f"  Products: {len(valid_ids)}/{len(bundle.get('featured_product_ids',[]))} valid")
    if invalid:
        for inv in invalid[:5]:
            print(f"    ⚠️  pid={inv['pid']}: {inv['issues']}")

    # Step 2: substitute grid placeholder + strip Flatsome/grid conflict
    content = bundle['content_html']
    content = strip_flatsome_grid_conflict(content)
    content = substitute_grid_placeholder(content, valid_ids)

    if dry_run:
        return {'dry': True, 'slug': slug, 'valid_products': len(valid_ids)}

    # Step 3: publish WP page (upsert)
    payload = {
        'title': bundle['page_title'],
        'content': content,
        'status': 'publish',
        'slug': slug,
    }
    existing = wp_get('wp/v2/pages', slug=slug, status='any', context='edit')
    if existing:
        pid = existing[0]['id']
        r = wp_post(f'wp/v2/pages/{pid}', payload)
        action = 'updated'
    else:
        r = wp_post('wp/v2/pages', payload)
        pid = r.json().get('id') if r and r.ok else None
        action = 'created'
    print(f"  Page {action}: pid={pid}  code={r.status_code if r else '?'}")

    if not pid:
        return {'slug': slug, 'error': 'publish_failed'}

    # Step 4: RankMath meta
    seo_ok = write_rank_math_meta(
        pid,
        keyword=bundle.get('focus_keyword', ''),
        title=bundle.get('page_title', ''),
        description=bundle.get('meta_description', ''),
    )
    print(f"  SEO meta: {'✅' if seo_ok else '❌'}")

    # Step 5: purge cache
    purge_wp_rocket_paths([slug])

    return {'slug': slug, 'pid': pid, 'action': action, 'valid_products': len(valid_ids), 'seo_ok': seo_ok}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bundle', required=True, help='Path to landing bundle.json')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--force', action='store_true',
                    help='Bypass slug-collision preflight (only if you know what you are doing)')
    args = ap.parse_args()

    b = json.load(open(args.bundle))
    print(f"Publishing: {b.get('slug')}")
    result = publish_landing(b, dry_run=args.dry_run, force=args.force)
    print(f"\n🔗 {WP_BASE}/{b['slug']}/")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
