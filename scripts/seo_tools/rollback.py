#!/usr/bin/env python3
"""Roll back product description / page content from a backup file or directory.

Backups are created automatically by product_enhance.py in `seo_tools/backups/<ts>/`.

Usage:
  # Rollback single product from a backup file
  python3 rollback.py --file backups/20260421_150530/product_22428_candy-bra-280g.json

  # Rollback all products in a backup directory
  python3 rollback.py --dir backups/20260421_150530/
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import wp_get, wp_post, purge_wp_rocket_paths, WP_BASE


def rollback_product(backup: dict, dry_run: bool = False) -> dict:
    pid = backup['pid']
    # Verify slug still matches
    current = wp_get(f'wc/v3/products/{pid}', _fields='id,slug')
    if not current:
        return {'pid': pid, 'error': 'not_found'}
    if current.get('slug') != backup.get('slug'):
        return {'pid': pid, 'error': f"slug_mismatch now={current.get('slug')} backup={backup.get('slug')}"}
    if dry_run:
        return {'pid': pid, 'slug': backup['slug'], 'would_restore_len': len(backup['description'])}
    u = wp_post(f'wc/v3/products/{pid}', {'description': backup['description']})
    if backup.get('permalink'):
        path = backup['permalink'].replace(WP_BASE, '').strip('/')
        purge_wp_rocket_paths([path])
    return {
        'pid': pid, 'slug': backup['slug'],
        'restored_len': len(backup['description']),
        'ok': bool(u and u.ok),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--file', help='Single backup JSON file')
    ap.add_argument('--dir', help='Directory of backups to roll back')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    if args.file:
        files = [Path(args.file)]
    elif args.dir:
        files = sorted(Path(args.dir).glob('product_*.json'))
    else:
        ap.error('Need --file or --dir')

    print(f"Rolling back {len(files)} product(s){' (dry-run)' if args.dry_run else ''}\n")
    for f in files:
        backup = json.load(open(f))
        result = rollback_product(backup, args.dry_run)
        status = '✅' if result.get('ok') or result.get('would_restore_len') else '❌'
        print(f"  {status} {result}")


if __name__ == '__main__':
    main()
