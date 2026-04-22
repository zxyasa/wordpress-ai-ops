#!/usr/bin/env python3
"""Fill missing RankMath focus_keyword + title/desc for 9 pages (2026-04-22).

Backup (edit context) → write_rank_math_meta → live curl verify (title+desc)
→ server-side audit verify (focus_kw) → Indexing API.

Usage:
  python 2026-04-22_fill_missing_focus_kw.py --ids 71760
  python 2026-04-22_fill_missing_focus_kw.py --ids 71756,71757,71758,71759,22499,22503,71832,71060
  python 2026-04-22_fill_missing_focus_kw.py --ids all
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import (
    WP_BASE, wp_get, safe_request, write_rank_math_meta, SEO_TOKEN,
    SSH_KEY, SSH_USER, SSH_HOST, SSH_PORT,
)

TARGETS: dict[int, dict] = {
    71760: {
        'focus_kw': 'mothers day sweets australia',
        'title': "Mother's Day Sweets & Chocolate Gifts Australia | SweetsWorld",
        'description': "Mother's Day chocolate & sweet gift ideas — Nan's Bag, Mum's Bag, hampers & Darrell Lea. Delivered Australia-wide in time for May 10.",
    },
    71756: {
        'focus_kw': 'christmas sweets australia',
        'title': 'Christmas Sweets & Candy Australia | SweetsWorld',
        'description': 'Shop Christmas sweets, chocolate & candy online in Australia. Nostalgic brands, bulk packs & gift-ready treats. Delivery Australia-wide.',
    },
    71757: {
        'focus_kw': 'easter chocolate australia',
        'title': 'Easter Chocolate & Sweets Australia | SweetsWorld',
        'description': 'Easter chocolate, eggs & sweets delivered across Australia. Cadbury, Lindt, Kinder, Darrell Lea & rare imports — shop online now.',
    },
    71758: {
        'focus_kw': 'halloween lollies australia',
        'title': 'Halloween Lollies & Candy Australia | SweetsWorld',
        'description': 'Halloween lollies, bulk candy & spooky treats delivered Australia-wide. Trick-or-treat packs, American imports & party favourites.',
    },
    71759: {
        'focus_kw': 'valentines day chocolate australia',
        'title': "Valentine's Day Sweets & Chocolate Australia | SweetsWorld",
        'description': "Valentine's Day chocolate & sweet gifts for him & her. Heart-shaped boxes, Lindt, Lindor, Ferrero & rare imports — delivered across AU.",
    },
    22503: {
        'focus_kw': 'british lollies australia',
        'title': 'British Lollies Australia | SweetsWorld',
        'description': 'Shop British lollies, chocolate & sweets online in Australia. Cadbury UK, Haribo, Wine Gums, Maynards, Bassetts & more — delivered AU-wide.',
    },
    22499: {
        'focus_kw': 'new lollies australia',
        'title': 'New Arrivals | SweetsWorld Australia',
        'description': 'The latest lollies, chocolate & imported candy landing at SweetsWorld. Fresh stock every week — American, British & Aussie favourites.',
    },
    71832: {
        'focus_kw': 'darrell lea sweets australia',
        'title': 'Darrell Lea Sweets Online – Delivered Across Australia | SweetsWorld',
        'description': 'Buy Darrell Lea liquorice, Rocklea Road, Batch 37 & chocolate online. Full range in stock, delivered Australia-wide from Newcastle HQ.',
    },
    71060: {
        'focus_kw': 'sweetsworld store locations',
        'title': 'Find SweetsWorld Near You | Store Locator',
        'description': "Find SweetsWorld stores near you in Newcastle and Australia. Browse locations, hours & stockist info for Australia's favourite lolly shop.",
    },
}


def backup_page(pid: int, out_dir: Path) -> Path | None:
    data = wp_get(f'wp/v2/pages/{pid}', context='edit')
    if not data:
        return None
    p = out_dir / f'page_{pid}_pre.json'
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return p


def curl_live(url: str) -> str:
    """Fetch page HTML via curl (bypasses WP Rocket for logged-out view)."""
    r = subprocess.run(
        ['curl', '-sL', '-A', 'Mozilla/5.0', '--max-time', '30', url],
        capture_output=True, text=True,
    )
    return r.stdout or ''


def verify_live(url: str, expected_title: str, expected_desc: str) -> dict:
    import html as html_lib
    import re
    raw = curl_live(url)
    status = 'ok'
    issues = []
    t = re.search(r'<title[^>]*>(.*?)</title>', raw, re.S | re.I)
    live_title = html_lib.unescape((t.group(1) if t else '').strip())
    d = re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)', raw, re.I)
    live_desc = html_lib.unescape(d.group(1) if d else '')
    if expected_title and expected_title[:30] not in live_title:
        issues.append(f'title_mismatch(live={live_title[:60]!r})')
        status = 'warn'
    if expected_desc and expected_desc[:30] not in live_desc:
        issues.append(f'desc_mismatch(live={live_desc[:60]!r})')
        status = 'warn'
    return {
        'status': status, 'issues': issues,
        'live_title': live_title, 'live_desc': live_desc,
    }


def verify_focus_kw_server(pids: list[int]) -> dict[int, dict]:
    """SSH into server, run audit_focus_kw.php, return {pid: row}."""
    cmd_run = (
        f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no -o LogLevel=ERROR '
        f'-p {SSH_PORT} {SSH_USER}@{SSH_HOST} '
        f'"cd ~/public_html && php audit_focus_kw.php"'
    )
    subprocess.run(cmd_run, shell=True, capture_output=True)
    cmd_fetch = (
        f'scp -i {SSH_KEY} -o StrictHostKeyChecking=no -o LogLevel=ERROR '
        f'-P {SSH_PORT} {SSH_USER}@{SSH_HOST}:/home/sweetsworld/audit_result.json '
        f'/tmp/audit_result.json'
    )
    subprocess.run(cmd_fetch, shell=True, capture_output=True)
    try:
        rows = json.loads(Path('/tmp/audit_result.json').read_text())
    except Exception:
        return {}
    return {r['id']: r for r in rows if r['id'] in pids}


def submit_indexing(url: str) -> bool:
    """Submit via google_indexing.submit_url."""
    agent_root = Path('/Users/michaelzhao/agents/agents/sweetsworld-seo-agent')
    sys.path.insert(0, str(agent_root / 'src'))
    try:
        from google_indexing import submit_url  # type: ignore
    except Exception as e:
        print(f'    (indexing import failed: {e})')
        return False
    creds = str(agent_root / 'gsc_credentials.json')
    res = submit_url(url, creds, notify_type='URL_UPDATED')
    return res.get('status') == 'success'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ids', required=True,
                    help='Comma-separated page IDs, or "all"')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    if args.ids == 'all':
        ids = list(TARGETS.keys())
    else:
        ids = [int(x.strip()) for x in args.ids.split(',')]
    for pid in ids:
        if pid not in TARGETS:
            print(f'ERROR: {pid} not in TARGETS')
            sys.exit(1)

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    repo_root = Path('/Users/michaelzhao/agents/apps/wordpress-ai-ops')
    backup_dir = repo_root / 'scripts/seo_tools/backups' / f'fill_focus_kw_{ts}'
    backup_dir.mkdir(parents=True, exist_ok=True)

    report = {'started': ts, 'ids': ids, 'results': {}}

    for pid in ids:
        tgt = TARGETS[pid]
        print(f'\n=== {pid} ===')
        print(f'  focus_kw: {tgt["focus_kw"]}')

        # 1. backup
        bk = backup_page(pid, backup_dir)
        if not bk:
            report['results'][pid] = {'error': 'backup_failed'}
            print('  ✗ backup failed, SKIP')
            continue
        print(f'  ✓ backup: {bk.name}')

        if args.dry_run:
            print(f'  [dry] would write: {tgt}')
            report['results'][pid] = {'dry_run': True}
            continue

        # 2. write
        ok = write_rank_math_meta(
            pid,
            keyword=tgt['focus_kw'],
            title=tgt['title'],
            description=tgt['description'],
        )
        if not ok:
            report['results'][pid] = {'error': 'write_failed'}
            print('  ✗ write_rank_math_meta returned False')
            continue
        print('  ✓ RankMath meta written')

        time.sleep(2)  # let WP Rocket flush

        # 3. live verify (title + desc)
        page_data = wp_get(f'wp/v2/pages/{pid}', _fields='link')
        url = page_data.get('link') if page_data else ''
        live = verify_live(url, tgt['title'], tgt['description'])
        mark = '✓' if live['status'] == 'ok' else '⚠'
        print(f'  {mark} live: {live["status"]}  {live["issues"] or ""}')

        # 4. indexing API
        idx_ok = submit_indexing(url)
        print(f'  {"✓" if idx_ok else "?"} indexing API submitted')

        report['results'][pid] = {
            'backup': str(bk),
            'url': url,
            'live_verify': live,
            'indexing': idx_ok,
        }

    # 5. server-side focus_kw cross-check (all targeted pids)
    if not args.dry_run:
        print('\n=== Server-side focus_kw cross-check ===')
        time.sleep(3)
        srv = verify_focus_kw_server(ids)
        for pid in ids:
            got = (srv.get(pid) or {}).get('focus_kw', '')
            want = TARGETS[pid]['focus_kw']
            m = '✓' if got == want else '✗'
            print(f'  {m} {pid}: got={got!r} want={want!r}')
            report['results'].setdefault(pid, {})['focus_kw_verified'] = (got == want)
            report['results'][pid]['focus_kw_server'] = got

    manifest = backup_dir / 'MANIFEST.json'
    manifest.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f'\n=== MANIFEST: {manifest} ===')


if __name__ == '__main__':
    main()
