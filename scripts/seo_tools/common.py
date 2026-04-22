"""Shared helpers for SEO tools — WP/WC auth, safe HTTP, common patterns."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

# Load SW env from canonical location
ENV_PATH = Path('/Users/michaelzhao/agents/agents/sweetsworld-seo-agent/.env')
load_dotenv(ENV_PATH)

WP_BASE = os.environ['WP_BASE_URL'].rstrip('/')
WP_AUTH = (os.environ['WP_USERNAME'], os.environ['WP_APP_PASSWORD'])
SEO_TOKEN = os.environ.get('WP_SEO_BRIDGE_TOKEN', 'sw_seo_meta_k8x2')

SSH_KEY = '/Users/michaelzhao/.ssh/sweetsworld_agent_nopass.pem'
SSH_USER = 'sweetsworld'
SSH_HOST = '103.27.35.29'
SSH_PORT = '2222'

# --------------------------------------------------------------
# HTTP with retry — WP is slow so 30s timeout and 3 retries
# --------------------------------------------------------------
def safe_request(method: str, url: str, **kwargs) -> requests.Response | None:
    """HTTP request with 3 retries, 30s timeout."""
    kwargs.setdefault('timeout', 30)
    kwargs.setdefault('auth', WP_AUTH)
    for attempt in range(3):
        try:
            return requests.request(method, url, **kwargs)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            if attempt < 2:
                time.sleep(5 * (attempt + 1))
                continue
            return None
    return None


def wp_get(path: str, **params) -> Any:
    """GET to /wp-json/<path>, return parsed JSON or None."""
    r = safe_request('GET', f"{WP_BASE}/wp-json/{path.lstrip('/')}", params=params)
    return r.json() if r and r.ok else None


def wp_post(path: str, json_body: dict) -> requests.Response | None:
    return safe_request('POST', f"{WP_BASE}/wp-json/{path.lstrip('/')}", json=json_body)


def write_rank_math_meta(post_id: int, *, keyword: str = '', title: str = '',
                          description: str = '') -> bool:
    """Write RankMath SEO fields via the WP endpoint."""
    params = {'token': SEO_TOKEN, 'post_id': post_id}
    if keyword: params['keyword'] = keyword
    if title: params['title'] = title
    if description: params['description'] = description
    r = safe_request('GET', f"{WP_BASE}/wp-seo-meta.php", params=params)
    return bool(r and r.ok and 'true' in r.text)


def write_rank_math_noindex(post_id: int, on: bool = True) -> bool:
    """Set rank_math_robots to ['noindex'] (on=True) or ['index'] (on=False).
    Use for legal/utility pages that shouldn't participate in search."""
    params = {'token': SEO_TOKEN, 'post_id': post_id, 'noindex': '1' if on else '0'}
    r = safe_request('GET', f"{WP_BASE}/wp-seo-meta.php", params=params)
    return bool(r and r.ok and 'true' in r.text)


def write_rank_math_term_meta(term_id: int, *, keyword: str = '', title: str = '',
                               description: str = '') -> bool:
    """Write RankMath SEO fields for a WC category/tag/term via wp-seo-term-meta.php.
    Use this when URL resolves to a WooCommerce category archive (WC overrides page slug)."""
    params = {'token': SEO_TOKEN, 'term_id': term_id}
    if keyword: params['keyword'] = keyword
    if title: params['title'] = title
    if description: params['description'] = description
    r = safe_request('GET', f"{WP_BASE}/wp-seo-term-meta.php", params=params)
    return bool(r and r.ok and 'true' in r.text)


def purge_wp_rocket_paths(paths: list[str]) -> None:
    """Delete WP Rocket cache for given URL paths (relative to domain)."""
    import subprocess
    cache_dir = f"~/public_html/wp-content/cache/wp-rocket/sweetsworld.com.au"
    args = ' '.join(f"{cache_dir}/{p.lstrip('/')}" for p in paths)
    cmd = (f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no -o LogLevel=ERROR '
           f'-p {SSH_PORT} -T {SSH_USER}@{SSH_HOST} "rm -rf {args} 2>&1"')
    subprocess.run(cmd, shell=True, capture_output=True)


# --------------------------------------------------------------
# Common product/page helpers
# --------------------------------------------------------------
def find_by_slug(slug: str) -> tuple[str, int, str] | None:
    """Return (type, id, full_url) for a given slug.
    Searches product, post, page in that order."""
    for ep, label in (
        ('wc/v3/products', 'product'),
        ('wp/v2/posts', 'post'),
        ('wp/v2/pages', 'page'),
    ):
        data = wp_get(ep, slug=slug, status='any')
        if data:
            pid = data[0]['id']
            link = data[0].get('permalink') or data[0].get('link', '')
            return label, pid, link
    return None


def validate_product(pid: int) -> dict:
    """Check a product's SEO-relevant status: stock, images, publish, visibility."""
    data = wp_get(f'wc/v3/products/{pid}', _fields='id,name,status,stock_status,images,catalog_visibility')
    if not data:
        return {'ok': False, 'reason': 'not_found'}
    issues = []
    if data.get('status') != 'publish': issues.append(f"status={data.get('status')}")
    if data.get('stock_status') != 'instock': issues.append(f"stock={data.get('stock_status')}")
    if not data.get('images'): issues.append('no_image')
    if data.get('catalog_visibility') not in ('visible', 'catalog'):
        issues.append(f"vis={data.get('catalog_visibility')}")
    return {'ok': not issues, 'issues': issues, 'name': data.get('name','')}


def check_slug_collision(slug: str) -> dict:
    """Check if a slug collides with any existing WC category / WC tag / other WP page.

    Sweetsworld strips the /product-category/ and /product-tag/ bases, so all three
    live at /<slug>/ — a shared namespace. Any collision = silent page hijack.

    Returns a dict:
      {
        'slug': <s>,
        'safe': bool,
        'pages': [{'id','title'}, ...],
        'cats':  [{'id','name','count'}, ...],
        'tags':  [{'id','name','count'}, ...],
      }
    """
    out = {'slug': slug, 'safe': True, 'pages': [], 'cats': [], 'tags': []}
    pages = wp_get('wp/v2/pages', slug=slug, status='any',
                   _fields='id,title,status') or []
    out['pages'] = [
        {'id': p['id'], 'title': (p.get('title') or {}).get('rendered', ''),
         'status': p.get('status', '')}
        for p in pages
    ]
    cats = wp_get('wc/v3/products/categories', slug=slug,
                  _fields='id,name,count') or []
    out['cats'] = [{'id': c['id'], 'name': c['name'], 'count': c.get('count', 0)}
                   for c in cats]
    tags = wp_get('wc/v3/products/tags', slug=slug,
                  _fields='id,name,count') or []
    out['tags'] = [{'id': t['id'], 'name': t['name'], 'count': t.get('count', 0)}
                   for t in tags]
    # safe if: no cats, no tags, and (no pages OR the only page has same slug being re-published)
    if out['cats'] or out['tags']:
        out['safe'] = False
    return out


def suggest_safe_slug(base_slug: str, suffix: str = '-australia') -> str:
    """Return a collision-free slug by appending suffix if needed."""
    if base_slug.endswith(suffix):
        return base_slug
    candidate = base_slug + suffix
    col = check_slug_collision(candidate)
    return candidate if col['safe'] else base_slug + '-au'


def flatten_whitespace_for_wpautop(html: str) -> str:
    """Remove newlines between HTML tags to neutralize wpautop on posts."""
    import re
    return re.sub(r'>\s*\n\s*<', '><', html)


def strip_flatsome_grid_conflict(html: str) -> str:
    """Remove Flatsome `.row row-small` class when combined with inline CSS grid."""
    import re
    html = re.sub(r'class="row row-small"\s+style="(display:grid;[^"]*)"', r'style="\1"', html)
    html = re.sub(r'class="row"\s+style="(display:grid;[^"]*)"', r'style="\1"', html)
    return html
