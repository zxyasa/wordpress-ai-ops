#!/usr/bin/env python3
"""Set noindex on 5 legal/utility pages that shouldn't participate in SEO.

Pattern: backup → write noindex via extended wp-seo-meta.php bridge → curl verify.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import WP_BASE, wp_get, write_rank_math_noindex

TARGETS = {
    22225: '/contact/',
    22816: '/faqs/',
    25972: '/returns-refunds/',
    69872: '/terms-of-service/',
    70152: '/data-deletion/',
}


def curl_live(url: str) -> str:
    r = subprocess.run(
        ['curl', '-sL', '-A', 'Mozilla/5.0', '--max-time', '30', url],
        capture_output=True, text=True,
    )
    return r.stdout or ''


def main():
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    repo_root = Path('/Users/michaelzhao/agents/apps/wordpress-ai-ops')
    bkdir = repo_root / 'scripts/seo_tools/backups' / f'noindex_legal_{ts}'
    bkdir.mkdir(parents=True, exist_ok=True)
    report = {'started': ts, 'results': {}}

    for pid, slug in TARGETS.items():
        print(f'\n=== {pid} {slug} ===')
        # backup
        data = wp_get(f'wp/v2/pages/{pid}', context='edit')
        if not data:
            print('  ✗ backup failed'); report['results'][pid] = {'error': 'backup'}; continue
        (bkdir / f'page_{pid}_pre.json').write_text(
            json.dumps(data, indent=2, ensure_ascii=False))
        print(f'  ✓ backup: page_{pid}_pre.json')

        # write noindex
        ok = write_rank_math_noindex(pid, on=True)
        if not ok:
            print('  ✗ noindex write failed')
            report['results'][pid] = {'error': 'write'}; continue
        print('  ✓ noindex set')

        # purge cache
        subprocess.run(
            f'ssh -i /Users/michaelzhao/.ssh/sweetsworld_agent_nopass.pem '
            f'-o StrictHostKeyChecking=no -o LogLevel=ERROR -p 2222 '
            f'sweetsworld@103.27.35.29 '
            f'"rm -rf ~/public_html/wp-content/cache/wp-rocket/sweetsworld.com.au{slug} 2>&1"',
            shell=True, capture_output=True, timeout=30,
        )
        time.sleep(2)

        # verify live
        url = WP_BASE + slug
        html = curl_live(url)
        import re
        robots_m = re.search(r'<meta\s+name=["\']robots["\']\s+content=["\']([^"\']+)', html, re.I)
        robots_live = robots_m.group(1) if robots_m else ''
        ok_live = 'noindex' in robots_live
        print(f'  {"✓" if ok_live else "⚠"} live robots: {robots_live or "(not set)"}')
        report['results'][pid] = {
            'slug': slug, 'noindex_set': ok, 'live_robots': robots_live,
            'live_ok': ok_live,
        }

    (bkdir / 'MANIFEST.json').write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f'\n=== MANIFEST: {bkdir}/MANIFEST.json ===')


if __name__ == '__main__':
    main()
