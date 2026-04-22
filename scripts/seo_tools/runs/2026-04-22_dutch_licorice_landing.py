"""Publish /dutch-licorice-australia/ landing — party-sweets visual hub pattern."""
import sys, json, os, time
from pathlib import Path
sys.path.insert(0, '.')
from common import wp_get, safe_request, WP_BASE, SEO_TOKEN

DRY = os.environ.get('DRY_RUN','0')=='1'
SLUG = 'dutch-licorice-australia'
TITLE_H1 = 'Dutch Licorice Australia'
RANKMATH_TITLE = 'Dutch Licorice Australia | Salt, Double Salt, Salmiak & More | SweetsWorld'
RANKMATH_DESC = 'Authentic Dutch licorice online in Australia — Single Salt, Double Salt, Triple Salt, Salmiak Rocks, Schoolkrijt Chalk. Imported from Holland, shipped Australia-wide from SweetsWorld Newcastle.'
FOCUS_KW = 'dutch licorice'

# Curated product ids (from preflight, all instock + publish)
PRODUCTS = [14351, 18050, 24032, 15751, 15752, 18406, 18409, 46350, 18413, 50845, 23961, 23967]
PRODUCTS_STR = ','.join(str(p) for p in PRODUCTS)

def fd(q,a):
    return (f'<details style="margin-bottom:18px;border:1px solid #e5e5e5;border-radius:6px">'
            f'<summary style="padding:16px 18px;font-weight:600;cursor:pointer;line-height:1.6">{q}</summary>'
            f'<div style="padding:16px 18px 18px;line-height:1.8">{a}</div></details>')

# ------------ CONTENT ------------
content = f"""
<div style="background:linear-gradient(135deg,#32455a 0%,#5eb4d8 100%);padding:60px 30px;text-align:center;color:#fff;margin-bottom:40px;border-radius:8px">
<h1 style="font-size:44px;margin:0 0 16px;color:#fff;font-weight:700">Dutch Licorice Australia</h1>
<p style="font-size:18px;max-width:720px;margin:0 auto 24px;line-height:1.6;color:#fff8fb">Authentic Dutch <em>drop</em> imported direct from Holland — Single Salt, Double Salt, Triple Salt, Salmiak Rocks, Schoolkrijt chalk sticks. From mild to face-puckering Dutch salty licorice lovers swear by.</p>
<a href="#dutch-licorice-shop" style="background:#d16688;color:#fff;padding:14px 32px;border-radius:6px;text-decoration:none;font-weight:600;font-size:16px;display:inline-block">Shop Dutch Licorice</a>
</div>

<h2 class="wp-block-heading">What makes Dutch licorice different?</h2>
<p>Dutch licorice — known locally as <em>drop</em> — is a completely different beast from Australian or American red/black licorice. Holland produces over <strong>80 varieties</strong>, rated on two axes: <strong>sweet to salty</strong> (zoet to zout), and <strong>soft to hard</strong>. The salt comes from <strong>ammonium chloride (salmiak)</strong>, which gives Dutch licorice its unique, tongue-tingling finish that Scandinavians and Northern Europeans crave.</p>

<p>The Netherlands is the world's biggest consumer of licorice per capita — roughly <strong>2 kg per person per year</strong>. Expats, Dutch Australians, Northern European migrants, and adventurous candy lovers all keep the Australian market alive.</p>

<h2 class="wp-block-heading">Dutch licorice types — a buyer's guide</h2>

<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px;margin:30px 0">

<div style="background:#fff8fb;padding:24px;border-left:4px solid #d16688;border-radius:6px">
<h3 style="margin:0 0 12px;color:#32455a">Single Salt (Enkel Zout)</h3>
<p style="margin:0">Mildly salty, the entry-level Dutch licorice. Pleasantly salty finish but not overwhelming. <strong>Best for first-timers</strong> trying Dutch drop.</p>
</div>

<div style="background:#fff8fb;padding:24px;border-left:4px solid #5eb4d8;border-radius:6px">
<h3 style="margin:0 0 12px;color:#32455a">Double Salt (Dubbel Zout)</h3>
<p style="margin:0">Twice the salmiak. A noticeable tongue-tingle that lingers. Popular with Dutch expats and experienced licorice fans.</p>
</div>

<div style="background:#fff8fb;padding:24px;border-left:4px solid #83c9b8;border-radius:6px">
<h3 style="margin:0 0 12px;color:#32455a">Triple Salt (Drie Zout)</h3>
<p style="margin:0">Maximum saltiness — <strong>not for beginners</strong>. Intense salty finish with a cooling numb sensation. Cult favourite among hardcore drop lovers.</p>
</div>

<div style="background:#fff8fb;padding:24px;border-left:4px solid #32455a;border-radius:6px">
<h3 style="margin:0 0 12px;color:#32455a">Salmiak Rocks</h3>
<p style="margin:0">Hard salmiak pieces with intense ammonium chloride punch. Looks like grey-black rocks, tastes like nothing you've tried before.</p>
</div>

<div style="background:#fff8fb;padding:24px;border-left:4px solid #d16688;border-radius:6px">
<h3 style="margin:0 0 12px;color:#32455a">Schoolkrijt (School Chalk)</h3>
<p style="margin:0">White chalk-shaped sticks — sweet outside, salmiak core. A Dutch childhood classic. Surprising but addictive.</p>
</div>

<div style="background:#fff8fb;padding:24px;border-left:4px solid #5eb4d8;border-radius:6px">
<h3 style="margin:0 0 12px;color:#32455a">Gemengde (Assorted)</h3>
<p style="margin:0">Mixed bags of sweet + salty drop — perfect if you can't decide or want to sample the Dutch licorice spectrum.</p>
</div>

</div>

<h2 class="wp-block-heading" id="dutch-licorice-shop">Shop Dutch licorice online</h2>
<p>All products below ship same-day from our Newcastle warehouse with fast Australia-wide delivery. Genuine Dutch imports, no local substitutes.</p>

<!-- WOOCOMMERCE_PRODUCT_GRID: ids={PRODUCTS_STR} cols=4 -->

<h2 class="wp-block-heading">Why buy Dutch licorice from SweetsWorld?</h2>
<ul>
<li><strong>Genuine imports</strong> — direct from Dutch suppliers, not knock-offs</li>
<li><strong>1kg bulk options</strong> — ideal for expats, weddings, Dutch clubs</li>
<li><strong>Same-day dispatch</strong> from Newcastle NSW, delivered Australia-wide</li>
<li><strong>Bulk pricing</strong> — 1kg packs cost significantly less per 100g than retail</li>
<li><strong>Expert curation</strong> — we select varieties Aussies actually want, not the full 80-variety Dutch range</li>
</ul>

<div class="sw-faq-block" style="margin-top:40px">
<h2 class="wp-block-heading">Frequently Asked Questions</h2>
""" + "\n".join([
    fd("Where to buy Dutch licorice in Australia?",
       "SweetsWorld is Australia's online destination for imported Dutch licorice, shipping Australia-wide from our Newcastle warehouse. We stock Single Salt, Double Salt, Triple Salt, Salmiak Rocks and Schoolkrijt chalk sticks. Major cities like Sydney, Melbourne, Brisbane, Perth and Adelaide usually receive orders in 2-5 business days."),
    fd("What's the difference between Dutch licorice and regular licorice?",
       "Dutch licorice (drop) contains <strong>ammonium chloride (salmiak)</strong> giving it a salty, tongue-tingling finish that regular black licorice doesn't have. Dutch drop also comes in many textures — hard rocks, soft chews, chewy coins, chalk sticks — while most Australian and American licorice is limited to soft chewy strands."),
    fd("Is salmiak licorice safe to eat?",
       "For healthy adults in moderation, yes. However, salmiak (ammonium chloride) can interact with medications for blood pressure and can worsen potassium imbalances in large quantities. <strong>Pregnant women should avoid high-salt Dutch licorice</strong> as the glycyrrhizin can affect pregnancy. Always consult a doctor if you have heart, kidney or blood pressure concerns."),
    fd("What's the most salty Dutch licorice available?",
       "<strong>Triple Salt (Drie Zout)</strong> and <strong>Salmiak Rocks</strong> are the saltiest varieties commonly available. Both pack serious salmiak intensity. Triple Salt is soft and chewy; Salmiak Rocks are hard and crunchy. Both should be sampled in small amounts first — many people find Triple Salt overwhelming until they build tolerance."),
    fd("Is Dutch licorice gluten free or vegan?",
       "Some Dutch licorice varieties are vegan-friendly (most are), but <strong>not all are gluten free</strong> — some use wheat flour as a binder. Always check the individual product page for the most current ingredients list. Our Single Salt, Double Salt, Triple Salt are typically vegan-friendly but may contain wheat."),
    fd("How long does Dutch licorice last?",
       "Unopened, Dutch licorice keeps 12-18 months in a cool, dry place (below 22°C). Once opened, store in an airtight container and consume within 6-8 weeks for best texture — soft varieties become dry and hard, hard varieties become sticky over time."),
]) + """
</div>

<p><em>Explore more from SweetsWorld: <a href="https://sweetsworld.com.au/licorice-australia/">Licorice Australia (all varieties)</a>, <a href="https://sweetsworld.com.au/british-lollies/">British &amp; European sweets</a>, <a href="https://sweetsworld.com.au/candy/">All candy collections</a>.</em></p>

<div style="background:linear-gradient(135deg,#32455a 0%,#5eb4d8 100%);padding:40px 24px;text-align:center;color:#fff;border-radius:8px;margin-top:40px">
<h2 style="color:#fff;margin:0 0 16px">Order Dutch licorice today</h2>
<p style="max-width:600px;margin:0 auto 20px;color:#fff8fb">Same-day dispatch from SweetsWorld Newcastle — free shipping on orders over $80.</p>
<a href="#dutch-licorice-shop" style="background:#d16688;color:#fff;padding:12px 28px;border-radius:6px;text-decoration:none;font-weight:600;display:inline-block">Shop Now</a>
</div>
"""

# Replace placeholder with WC shortcode
content = content.replace(
    f'<!-- WOOCOMMERCE_PRODUCT_GRID: ids={PRODUCTS_STR} cols=4 -->',
    f'[products ids="{PRODUCTS_STR}" columns="4"]'
)

# ------------ PUBLISH ------------
payload = {
    'slug': SLUG,
    'title': TITLE_H1,
    'content': content,
    'status': 'publish',
    'template': '',  # default
}

print(f"[{'DRY' if DRY else 'LIVE'}] Publishing /dutch-licorice-australia/ ({len(content):,} chars, {len(PRODUCTS)} products)")

if DRY:
    Path('/tmp/preview_dutch.html').write_text(content)
    print("  preview → /tmp/preview_dutch.html")
    sys.exit(0)

r = safe_request('POST', f"{WP_BASE}/wp-json/wp/v2/pages", json=payload)
if not r or not r.ok:
    print(f"❌ publish FAILED: HTTP {r.status_code if r else 'no response'}")
    if r: print(r.text[:500])
    sys.exit(1)

pub = r.json()
pid = pub['id']
url = pub.get('link','') or f"https://sweetsworld.com.au/{SLUG}/"
print(f"✅ Page published: id={pid}")
print(f"   URL: {url}")

# RankMath meta
r2 = safe_request('GET', f"{WP_BASE}/wp-seo-meta.php",
                 params={'token':SEO_TOKEN,'post_id':pid,
                         'keyword':FOCUS_KW,'title':RANKMATH_TITLE,'description':RANKMATH_DESC}, auth=None)
print(f"   RankMath meta: HTTP {r2.status_code if r2 else 'FAIL'}")

# Save publish record
Path(f'/tmp/dutch_licorice_published_{pid}.json').write_text(json.dumps({'id':pid,'url':url,'products':PRODUCTS}, indent=2))
print(f"\nNext: internal links + Indexing API (separate step)")
print(f"pid={pid} url={url}")
