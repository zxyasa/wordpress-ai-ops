#!/usr/bin/env python3
"""Weekly SEO hygiene monitor for sweetsworld.com.au.

Double audit:
  1. Slug collision — WC cats/tags share `/<slug>/` namespace with WP pages
     because sweetsworld strips `/product-category/` and `/product-tag/` bases.
     Same-slug = silent page hijack.
  2. Missing focus_kw — indexable (non-noindex) publish pages without
     RankMath focus keyword. Happens when Michael creates pages manually in
     WP admin without filling the RankMath sidebar.

State: separate sets tracked for each kind; only alerts Telegram on *new* items.

Usage:
  python slug_collision_monitor.py               # full run (alert on new)
  python slug_collision_monitor.py --report-all  # force full report
  python slug_collision_monitor.py --dry-run     # print only, no Telegram
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import wp_get, SSH_KEY, SSH_USER, SSH_HOST, SSH_PORT

STATE_FILE = Path(__file__).resolve().parent / '.slug_collision_state.json'


def fetch_all(endpoint: str, fields: str) -> list[dict]:
    out: list[dict] = []
    for page in range(1, 30):
        batch = wp_get(endpoint, per_page=100, page=page, _fields=fields)
        if not batch:
            break
        out.extend(batch)
        if len(batch) < 100:
            break
    return out


def fetch_all_pages() -> list[dict]:
    out: list[dict] = []
    for page in range(1, 10):
        batch = wp_get('wp/v2/pages', per_page=100, page=page,
                       status='publish', _fields='id,slug,title,link')
        if not batch:
            break
        out.extend(batch)
        if len(batch) < 100:
            break
    return out


def scan_slug_collisions(pages: list[dict], cats: list[dict], tags: list[dict]) -> list[dict]:
    cat_by_slug = {c['slug']: c for c in cats}
    tag_by_slug = {t['slug']: t for t in tags}
    out = []
    for p in pages:
        cat = cat_by_slug.get(p['slug'])
        tag = tag_by_slug.get(p['slug'])
        if not (cat or tag):
            continue
        out.append({
            'slug': p['slug'],
            'page_id': p['id'],
            'page_title': (p.get('title') or {}).get('rendered', ''),
            'cat': {'id': cat['id'], 'name': cat['name'], 'count': cat['count']} if cat else None,
            'tag': {'id': tag['id'], 'name': tag['name'], 'count': tag['count']} if tag else None,
        })
    return out


def scan_missing_focus_kw() -> list[dict]:
    """SSH + run audit_focus_kw.php, return indexable publish pages with empty focus_kw."""
    ssh = (f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no -o LogLevel=ERROR '
           f'-p {SSH_PORT} {SSH_USER}@{SSH_HOST} '
           f'"cd ~/public_html && php audit_focus_kw.php"')
    subprocess.run(ssh, shell=True, capture_output=True, timeout=60)
    scp = (f'scp -i {SSH_KEY} -o StrictHostKeyChecking=no -o LogLevel=ERROR '
           f'-P {SSH_PORT} {SSH_USER}@{SSH_HOST}:/home/sweetsworld/audit_result.json '
           f'/tmp/audit_result.json')
    subprocess.run(scp, shell=True, capture_output=True, timeout=30)
    try:
        rows = json.loads(Path('/tmp/audit_result.json').read_text())
    except Exception:
        return []
    return [
        {'slug': r['slug'], 'page_id': r['id'], 'page_title': r['title']}
        for r in rows
        if r.get('status') == 'publish'
        and not r.get('noindex')
        and not (r.get('focus_kw') or '').strip()
    ]


def scan() -> dict:
    pages = fetch_all_pages()
    cats = fetch_all('wc/v3/products/categories', 'id,slug,name,count')
    tags = fetch_all('wc/v3/products/tags', 'id,slug,name,count')

    return {
        'scanned_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'totals': {'pages': len(pages), 'cats': len(cats), 'tags': len(tags)},
        'collisions': scan_slug_collisions(pages, cats, tags),
        'missing_focus_kw': scan_missing_focus_kw(),
    }


def load_state() -> dict[str, set[str]]:
    if not STATE_FILE.exists():
        return {'collisions': set(), 'missing_focus_kw': set()}
    try:
        d = json.loads(STATE_FILE.read_text())
    except Exception:
        return {'collisions': set(), 'missing_focus_kw': set()}
    # Back-compat: old key `known_slugs` held collisions only
    if 'known_slugs' in d and 'collisions' not in d:
        return {'collisions': set(d.get('known_slugs', [])),
                'missing_focus_kw': set()}
    return {
        'collisions': set(d.get('collisions', [])),
        'missing_focus_kw': set(d.get('missing_focus_kw', [])),
    }


def save_state(state: dict[str, set[str]]) -> None:
    STATE_FILE.write_text(json.dumps({
        'collisions': sorted(state['collisions']),
        'missing_focus_kw': sorted(state['missing_focus_kw']),
        'saved_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
    }, indent=2))


def format_report(result: dict,
                  new_collisions: list[dict] | None = None,
                  new_missing_kw: list[dict] | None = None,
                  report_all: bool = False) -> str:
    t = result['totals']
    cols_all = result['collisions']
    kw_all = result['missing_focus_kw']
    lines = [
        "*SW SEO Hygiene Monitor*",
        f"Scanned: {t['pages']} pages / {t['cats']} cats / {t['tags']} tags",
        f"Slug collisions: *{len(cols_all)}* | Missing focus_kw (indexable): *{len(kw_all)}*",
    ]

    # Slug collision section
    cols_show = cols_all if report_all else (new_collisions or [])
    lines.append("")
    if report_all or new_collisions is not None:
        lines.append(f"*Slug collisions ({'all' if report_all else 'new'}): {len(cols_show)}*")
        if not cols_show:
            lines.append("  ✅ none")
        else:
            for c in cols_show[:15]:
                bits = []
                if c.get('cat'): bits.append(f"cat#{c['cat']['id']} ({c['cat']['count']} prod)")
                if c.get('tag'): bits.append(f"tag#{c['tag']['id']} ({c['tag']['count']} prod)")
                lines.append(f"  🚫 `/{c['slug']}/` — page {c['page_id']} vs {' + '.join(bits)}")
            if len(cols_show) > 15:
                lines.append(f"  ... +{len(cols_show)-15} more")

    # Missing focus_kw section
    kw_show = kw_all if report_all else (new_missing_kw or [])
    lines.append("")
    if report_all or new_missing_kw is not None:
        lines.append(f"*Missing focus_kw ({'all' if report_all else 'new'}): {len(kw_show)}*")
        if not kw_show:
            lines.append("  ✅ none")
        else:
            for k in kw_show[:15]:
                lines.append(f"  📝 `/{k['slug']}/` — page {k['page_id']} — {k['page_title'][:40]}")
            if len(kw_show) > 15:
                lines.append(f"  ... +{len(kw_show)-15} more")

    return "\n".join(lines)


def send_telegram(msg: str) -> bool:
    """Reuse wp_ai_ops.notify.send_telegram; read env from seo-agent .env."""
    from dotenv import dotenv_values
    env = dotenv_values('/Users/michaelzhao/agents/agents/sweetsworld-seo-agent/.env')
    tok = env.get('TELEGRAM_BOT_TOKEN') or os.environ.get('TELEGRAM_BOT_TOKEN', '')
    chat = env.get('TELEGRAM_CHAT_ID') or os.environ.get('TELEGRAM_CHAT_ID', '')
    if not (tok and chat):
        print('  (no telegram creds — skipping push)')
        return False
    sys.path.insert(0, '/Users/michaelzhao/agents/apps/wordpress-ai-ops/src')
    from wp_ai_ops.notify import send_telegram as _send
    return _send(tok, chat, msg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--report-all', action='store_true',
                    help='Always report, ignore state diff')
    ap.add_argument('--dry-run', action='store_true',
                    help='Print only, no Telegram push')
    ap.add_argument('--json', action='store_true', help='Emit JSON')
    args = ap.parse_args()

    result = scan()

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    curr_cols = {c['slug'] for c in result['collisions']}
    curr_kw = {k['slug'] for k in result['missing_focus_kw']}
    known = load_state()
    new_cols_slugs = curr_cols - known['collisions']
    new_kw_slugs = curr_kw - known['missing_focus_kw']
    resolved_cols = known['collisions'] - curr_cols
    resolved_kw = known['missing_focus_kw'] - curr_kw

    new_col_items = [c for c in result['collisions'] if c['slug'] in new_cols_slugs]
    new_kw_items = [k for k in result['missing_focus_kw'] if k['slug'] in new_kw_slugs]

    report = format_report(
        result,
        new_collisions=None if args.report_all else new_col_items,
        new_missing_kw=None if args.report_all else new_kw_items,
        report_all=args.report_all,
    )
    print(report)
    resolved_summary = []
    if resolved_cols:
        resolved_summary.append(f"✅ Resolved collisions: {', '.join(sorted(resolved_cols))}")
    if resolved_kw:
        resolved_summary.append(f"✅ Resolved focus_kw gaps: {', '.join(sorted(resolved_kw))}")
    if resolved_summary:
        print("\n" + "\n".join(resolved_summary))

    should_push = (args.report_all or new_cols_slugs or new_kw_slugs
                   or resolved_cols or resolved_kw)
    if should_push and not args.dry_run:
        full_msg = report
        if resolved_summary:
            full_msg += "\n\n" + "\n".join(resolved_summary)
        send_telegram(full_msg)

    save_state({'collisions': curr_cols, 'missing_focus_kw': curr_kw})


if __name__ == '__main__':
    main()
