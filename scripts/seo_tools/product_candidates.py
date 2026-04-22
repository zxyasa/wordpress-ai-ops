#!/usr/bin/env python3
"""Find product pages with SEO upside from rank tracker DB.

Criteria: product URL, position 5-40, impressions >= N (default 15), 7-day window.
Outputs CSV ready for FAQ-bundle generation workflow.
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

DB_PATH = Path('/Users/michaelzhao/agents/apps/wordpress-ai-ops/scripts/rank_tracker/rank_history.db')

PRODUCT_URL_PREFIXES = (
    '/candy/', '/chocolate/', '/party-lollies/', '/british-lollies/',
    '/uncategorized/', '/lolly/', '/easterchocolate/', '/grocery/',
    '/gift/', '/party-sweets/',
)
# Exclude these (blog/guides/hubs — not single product pages)
EXCLUDE_PATTERNS = ('/candy-guides/', '/where-to-buy/', '/newcastle/', '/page/')


def find_candidates(min_imp: int = 15, pos_min: float = 5.0, pos_max: float = 40.0, days: int = 7) -> list[dict]:
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    latest = db.execute('SELECT MAX(date) FROM snapshots').fetchone()[0]
    start = (date.fromisoformat(latest) - timedelta(days=days - 1)).isoformat()

    rows = db.execute('''
        SELECT url, keyword,
               AVG(position) AS avg_pos,
               SUM(impressions) AS total_imp,
               SUM(clicks) AS total_clk
        FROM snapshots
        WHERE date BETWEEN ? AND ? AND position > 0
        GROUP BY url, keyword
        HAVING total_imp >= ? AND avg_pos BETWEEN ? AND ?
        ORDER BY total_imp DESC
    ''', (start, latest, min_imp, pos_min, pos_max)).fetchall()

    out = []
    for r in rows:
        url = r['url']
        if not any(url.startswith(p) for p in PRODUCT_URL_PREFIXES):
            continue
        if any(p in url for p in EXCLUDE_PATTERNS):
            continue
        segs = url.strip('/').split('/')
        if len(segs) < 2:
            continue
        out.append(dict(r))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', default='-', help='CSV path or - for stdout')
    ap.add_argument('--min-imp', type=int, default=15)
    ap.add_argument('--pos-min', type=float, default=5.0)
    ap.add_argument('--pos-max', type=float, default=40.0)
    ap.add_argument('--days', type=int, default=7)
    args = ap.parse_args()

    cands = find_candidates(args.min_imp, args.pos_min, args.pos_max, args.days)
    print(f"Found {len(cands)} candidates", file=sys.stderr)

    fh = sys.stdout if args.output == '-' else open(args.output, 'w')
    w = csv.writer(fh)
    w.writerow(['url', 'keyword', 'avg_pos', 'total_imp', 'total_clk'])
    for c in cands:
        w.writerow([c['url'], c['keyword'], round(c['avg_pos'], 1),
                    c['total_imp'], c['total_clk']])
    if fh is not sys.stdout:
        fh.close()
        print(f"→ {args.output}", file=sys.stderr)


if __name__ == '__main__':
    main()
