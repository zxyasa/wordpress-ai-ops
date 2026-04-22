#!/usr/bin/env python3
"""Apply FAQ + internal links + RankMath meta to WooCommerce products from bundles.json.

Bundle schema per product:
{
  "product_id": int,
  "slug": str,
  "target_keyword": str,
  "new_meta_title": str (60-70 chars),
  "new_meta_description": str (150-160 chars),
  "new_focus_keyword": str,
  "faq_html": "<h2>FAQs</h2>...<details>...</details>...",
  "internal_links_to_add_in_description": [
    {"anchor_text": str, "url": str}
  ]
}
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (WP_BASE, wp_get, wp_post, write_rank_math_meta,
                    purge_wp_rocket_paths)

BACKUP_ROOT = Path(__file__).resolve().parent / 'backups'


def apply_bundle(b: dict) -> dict:
    pid = b['product_id']
    slug = b.get('slug', '?')
    p = wp_get(f'wc/v3/products/{pid}', context='edit')
    if not p:
        return {'pid': pid, 'slug': slug, 'error': 'fetch_failed'}
    # Sanity check: slug must match to prevent wrong-product overwrites
    if slug and slug != '?' and p.get('slug') != slug:
        return {'pid': pid, 'slug': slug, 'error': f'slug_mismatch WC={p.get("slug")} bundle={slug}'}
    orig_desc = p.get('description', '')
    orig_len = len(orig_desc)

    # 🔒 MANDATORY BACKUP before any write
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = BACKUP_ROOT / ts
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_file = backup_dir / f'product_{pid}_{p.get("slug","unknown")}.json'
    json.dump({
        'pid': pid,
        'slug': p.get('slug'),
        'name': p.get('name'),
        'description': orig_desc,
        'permalink': p.get('permalink', ''),
        'timestamp': ts,
    }, backup_file.open('w'), ensure_ascii=False, indent=2)

    # Mode: replace OR append
    # If bundle has new_description → replace entire description (Stage 2 style)
    # Else → keep existing and just enhance with FAQ/links (Stage 1 style)
    if b.get('new_description'):
        desc = b['new_description']
    else:
        desc = orig_desc

    # 1. Inject internal links (first match only, skip already-anchored text)
    for link in b.get('internal_links_to_add_in_description', []):
        anchor = link['anchor_text']
        url = link['url']
        pattern = re.compile(r'(?<!>)(' + re.escape(anchor) + r')(?![^<]*</a>)', re.IGNORECASE)
        if pattern.search(desc):
            desc = pattern.sub(f'<a href="{url}">\\1</a>', desc, count=1)

    # 2. Append FAQ block — insert before any trailing CTA paragraph if present
    faq_html = b.get('faq_html', '')
    if faq_html and faq_html not in desc:  # idempotent
        cta = re.search(r'(<p>[^<]*<strong>(?:Shop|Buy|Order)[\s\S]*?</p>\s*)$', desc)
        if cta:
            desc = desc[:cta.start()] + '\n' + faq_html + '\n\n' + desc[cta.start():]
        else:
            desc = desc.rstrip() + '\n\n' + faq_html + '\n'

    # 3. Apply description
    u = wp_post(f'wc/v3/products/{pid}', {'description': desc})
    desc_ok = bool(u and u.ok)

    # 4. RankMath meta
    seo_ok = write_rank_math_meta(
        pid,
        keyword=b.get('new_focus_keyword', ''),
        title=b.get('new_meta_title', ''),
        description=b.get('new_meta_description', ''),
    )

    # 5. Purge cache for this URL
    permalink = p.get('permalink', '')
    if permalink:
        path = permalink.replace(WP_BASE, '').strip('/')
        purge_wp_rocket_paths([path])

    return {
        'pid': pid, 'slug': slug,
        'desc_orig': orig_len, 'desc_new': len(desc),
        'desc_ok': desc_ok, 'seo_ok': seo_ok,
        'backup': str(backup_file),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bundles', required=True, help='Path to bundles.json')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    bundles = json.load(open(args.bundles))
    print(f"Loaded {len(bundles)} bundles from {args.bundles}\n")

    results = []
    for b in bundles:
        if args.dry_run:
            print(f"  [dry] {b.get('product_id')} {b.get('slug','?')} — "
                  f"{len(b.get('faq_html',''))} chars FAQ, "
                  f"{len(b.get('internal_links_to_add_in_description',[]))} links")
            continue
        r = apply_bundle(b)
        results.append(r)
        status = '✅' if r.get('desc_ok') and r.get('seo_ok') else '⚠️'
        print(f"  {status} {r['pid']} {r['slug'][:40]}: desc {r.get('desc_orig',0)}→{r.get('desc_new',0)}  SEO={r.get('seo_ok')}")

    if results:
        out = Path(args.bundles).parent / 'apply_results.json'
        json.dump(results, open(out, 'w'), indent=2)
        print(f"\nResults → {out}")


if __name__ == '__main__':
    main()
