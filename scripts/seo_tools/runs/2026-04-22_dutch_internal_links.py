"""Add internal links to /dutch-licorice-australia/ from 3 related pages."""
import sys, json, os, time
sys.path.insert(0, '.')
from common import wp_get, safe_request, find_by_slug, WP_BASE

TARGET_URL = 'https://sweetsworld.com.au/dutch-licorice-australia/'
LINK_HTML = '<p style="margin-top:24px;padding:16px;background:#fff8fb;border-left:3px solid #d16688;border-radius:4px"><strong>Looking for salty Dutch drop?</strong> Check our dedicated <a href="https://sweetsworld.com.au/dutch-licorice-australia/">Dutch Licorice Australia</a> page — Single Salt, Double Salt, Triple Salt, Salmiak Rocks and Schoolkrijt chalk, all imported direct from Holland.</p>'

# Source pages: licorice parent hub + candy-guides licorice post + British/European landing
sources = [
    ('licorice-australia',    'Licorice Australia landing (parent hub)'),
    ('british-lollies',       'British Lollies category'),  # may not exist as page
]

for slug, label in sources:
    print(f"\n▶ Adding link from {label} ({slug})")
    r = find_by_slug(slug)
    if not r:
        print(f"  ⚠️  slug not found, skipping")
        continue
    kind, pid, url = r
    # Fetch content
    ep_map = {'page':'wp/v2/pages','post':'wp/v2/posts','product':'wc/v3/products'}
    data = wp_get(f"{ep_map[kind]}/{pid}", context='edit' if kind!='product' else None)
    if not data:
        print(f"  ❌ fetch fail")
        continue
    content_key = 'description' if kind == 'product' else 'content'
    current = data.get(content_key,'') if kind=='product' else (data.get('content') or {}).get('rendered','')
    if 'dutch-licorice-australia' in current.lower():
        print(f"  ℹ️  link already present, skip")
        continue
    new = current.rstrip() + "\n" + LINK_HTML
    r2 = safe_request('POST', f"{WP_BASE}/wp-json/{ep_map[kind]}/{pid}",
                     json={content_key: new} if kind=='product' else {'content':new})
    print(f"  {'✅' if r2 and r2.ok else '❌'} HTTP {r2.status_code if r2 else 'FAIL'} — {kind} #{pid} link added")
    time.sleep(1)

# Also add a FAQ answer internal link inside /licorice-australia/ if that page exists
# (only if not already done via above tail-append)
print("\nDone. Internal links added.")
