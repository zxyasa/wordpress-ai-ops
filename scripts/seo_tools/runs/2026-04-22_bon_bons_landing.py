"""New page /bon-bons-australia/ — 8×120g retail flavours + 2×3kg Kingsway bulk only."""
import sys, json, os
from pathlib import Path
sys.path.insert(0, '.')
from common import wp_get, safe_request, WP_BASE, SEO_TOKEN

DRY = os.environ.get('DRY_RUN','0')=='1'
SLUG = 'bon-bons-australia'
TITLE_H1 = 'Bon Bons Australia'
WP_TITLE = 'Bon Bons Australia | 8 Flavours + Kingsway 3kg Bulk | SweetsWorld'
RM_TITLE = 'Bon Bons Australia | 8 Flavours + Kingsway 3kg Bulk | SweetsWorld'
RM_DESC = 'Buy bon bons online in Australia — Blue Raspberry, Strawberry, Toffee, Lemon, Bubblegum, Cherry, Green Apple, Watermelon 120g + Kingsway 3kg bulk. Same-day dispatch from SweetsWorld Newcastle.'
FOCUS = 'bon bons'

# 8 retail flavours + 2 Kingsway 3kg bulk — ONLY
PRODUCTS = [12598, 12601, 12725, 14740, 14742, 14744, 15589, 16987, 68622, 68624]
PRODUCTS_STR = ','.join(str(x) for x in PRODUCTS)

def fd(q,a):
    return (f'<details style="margin-bottom:18px;border:1px solid #e5e5e5;border-radius:6px">'
            f'<summary style="padding:16px 18px;font-weight:600;cursor:pointer;line-height:1.6">{q}</summary>'
            f'<div style="padding:16px 18px 18px;line-height:1.8">{a}</div></details>')

# PAGE type — inline H1 required
inner = f"""<div style="background:linear-gradient(135deg,#d16688 0%,#5eb4d8 100%);padding:56px 28px;text-align:center;color:#fff;margin-bottom:32px;border-radius:8px">
<h1 style="font-size:42px;margin:0 0 14px;color:#fff;font-weight:700;line-height:1.2">Bon Bons Australia</h1>
<p style="font-size:18px;max-width:720px;margin:0 auto 20px;line-height:1.6;color:#fff8fb">Classic chewy bon bons in 8 fruit flavours — plus 3kg Kingsway bulk bags for weddings, parties and pick-and-mix lolly bars. Same-day dispatch from SweetsWorld Newcastle.</p>
<a href="#bon-bons-shop" style="background:#32455a;color:#fff;padding:12px 28px;border-radius:6px;text-decoration:none;font-weight:600;display:inline-block">Shop Bon Bons</a>
</div>

<h2 class="wp-block-heading">What are Bon Bons?</h2>
<p>Bon bons are the classic <strong>chewy fruit-flavoured lolly</strong> wrapped in twisted cellophane — one of the longest-standing pick-and-mix staples in Australian candy culture. Each 120g bag holds 30-35 individually twist-wrapped pieces in a single intense flavour. The texture is <strong>firm-chewy</strong> (somewhere between a taffy and a fudge), with a concentrated fruit flavour burst that takes 30-60 seconds to chew through.</p>

<p>Classic uses: lolly bars at kids' parties, wedding bomboniere, school canteen treats, pick-and-mix bowls, office conference buffets. The twist-wrapped format keeps each piece food-safe, stackable, and easy to portion out — which is why bon bons have survived every candy trend since the 1960s.</p>

<h2 class="wp-block-heading">The 8 bon bon flavours in stock</h2>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin:26px 0">
<div style="background:#fff8fb;padding:18px;border-left:4px solid #5eb4d8;border-radius:6px"><h3 style="margin:0 0 8px;color:#32455a">🔵 Blue Raspberry</h3><p style="margin:0;font-size:14px">Vivid blue, tart raspberry kick. Kids' top pick.</p></div>
<div style="background:#fff8fb;padding:18px;border-left:4px solid #d16688;border-radius:6px"><h3 style="margin:0 0 8px;color:#32455a">🍓 Strawberry (Gluten Free)</h3><p style="margin:0;font-size:14px">Sweet classic strawberry. The most universally loved.</p></div>
<div style="background:#fff8fb;padding:18px;border-left:4px solid #83c9b8;border-radius:6px"><h3 style="margin:0 0 8px;color:#32455a">🍋 Lemon</h3><p style="margin:0;font-size:14px">Zesty citrus punch. Great palate cleanser.</p></div>
<div style="background:#fff8fb;padding:18px;border-left:4px solid #32455a;border-radius:6px"><h3 style="margin:0 0 8px;color:#32455a">🍒 Cherry</h3><p style="margin:0;font-size:14px">Deep rich cherry — adult-favourite of the range.</p></div>
<div style="background:#fff8fb;padding:18px;border-left:4px solid #83c9b8;border-radius:6px"><h3 style="margin:0 0 8px;color:#32455a">🍏 Green Apple</h3><p style="margin:0;font-size:14px">Tart + sweet granny smith profile.</p></div>
<div style="background:#fff8fb;padding:18px;border-left:4px solid #d16688;border-radius:6px"><h3 style="margin:0 0 8px;color:#32455a">🍉 Watermelon</h3><p style="margin:0;font-size:14px">Summer-fresh pink watermelon flavour.</p></div>
<div style="background:#fff8fb;padding:18px;border-left:4px solid #5eb4d8;border-radius:6px"><h3 style="margin:0 0 8px;color:#32455a">🫧 Bubblegum</h3><p style="margin:0;font-size:14px">Iconic bubblegum note without actual gum texture.</p></div>
<div style="background:#fff8fb;padding:18px;border-left:4px solid #32455a;border-radius:6px"><h3 style="margin:0 0 8px;color:#32455a">🥫 Toffee</h3><p style="margin:0;font-size:14px">Rich caramel-butterscotch — only non-fruit flavour.</p></div>
</div>

<h2 class="wp-block-heading">Kingsway 3kg bulk — for weddings, fetes &amp; events</h2>
<p>For large-scale use we stock <strong>Kingsway 3kg bulk bags</strong> of the two most-ordered single flavours: <strong>Bubblegum</strong> and <strong>Blue Raspberry</strong>. Both are <strong>gluten-free certified</strong>. At roughly 700-800 individually-wrapped pieces per 3kg bag, these are purpose-built for:</p>
<ul>
<li><strong>Wedding bomboniere</strong> — portion 10-15 pieces per guest into favour bags</li>
<li><strong>School fetes</strong> — fundraising stall, ~50-100 pieces per jar</li>
<li><strong>Kids' party lolly bars</strong> — one 3kg bag serves 30+ kids</li>
<li><strong>Corporate events</strong> — conference buffet bowls</li>
<li><strong>Pick-and-mix retail</strong> (re-pack)</li>
</ul>

<h2 class="wp-block-heading" id="bon-bons-shop">Shop Bon Bons online</h2>
<p>All 8 retail 120g flavours + 2 Kingsway 3kg bulk bags are in stock and ship same-day from our Newcastle warehouse, Australia-wide (2-5 business days for major cities).</p>

[products ids="{PRODUCTS_STR}" columns="4"]

<h2 class="wp-block-heading">How to serve bon bons</h2>
<ul>
<li><strong>Pick-and-mix bowl</strong> — unwrap 30-50 pieces, arrange by colour. Twist-wrapped bon bons look great unwrapped too.</li>
<li><strong>Wedding favour bag</strong> — 10-15 wrapped pieces per organza bag with ribbon. The colour variety creates visual appeal.</li>
<li><strong>Party lolly bar</strong> — display 3-4 flavours in individual jars with tongs. Kids love choosing their own mix.</li>
<li><strong>Christmas bonbon tradition</strong> — stuff into paper Christmas crackers alongside the paper hat and joke.</li>
<li><strong>Corporate conference</strong> — small ceramic bowls of wrapped bon bons at each table. Nostalgic + adult-appropriate.</li>
</ul>

<div class="sw-faq-block" style="margin-top:40px">
<h2 class="wp-block-heading">Frequently Asked Questions</h2>
""" + "\n".join([
    fd("Where to buy bon bons in bulk in Australia?",
       "SweetsWorld stocks Kingsway 3kg bulk bon bons (Bubblegum and Blue Raspberry, both gluten-free) plus 8 flavours at 120g retail size. Ships same-day from our Newcastle warehouse Australia-wide. For 10kg+ wholesale orders contact us for pricing."),
    fd("Which bon bon flavours are gluten free?",
       "The <strong>Strawberry 120g</strong> retail bag and both <strong>Kingsway 3kg bulk bags</strong> (Bubblegum and Blue Raspberry) are explicitly labelled gluten free. The other 120g retail flavours are not certified gluten free — always check the individual product pack label if you have coeliac disease."),
    fd("How many bon bons are in a 120g retail bag?",
       "A typical 120g bon bon bag contains <strong>30-35 individually twist-wrapped pieces</strong> (roughly 3.5-4 grams each). This makes them ideal for pick-and-mix where each piece is a single serving. For party portioning, 3-5 pieces per child per treat bag is the standard ratio."),
    fd("How many bon bons in a Kingsway 3kg bag?",
       "Kingsway 3kg bulk bags hold approximately <strong>700-800 individually-wrapped pieces</strong>. For wedding bomboniere at 10 pieces per guest that's 70-80 guests; for lolly bar pick-and-mix you're looking at 30+ kids worth at generous portions."),
    fd("Are bon bons suitable for young children?",
       "Bon bons are <strong>recommended for ages 4+</strong> due to the chewy texture — smaller children risk choking on candy this firm. Supervise young children while eating. Not suitable for anyone with braces (the chewiness can dislodge brackets)."),
    fd("How long do bon bons stay fresh?",
       "Unopened, twist-wrapped bon bons last <strong>12-18 months</strong> from manufacture date in a cool, dry place (below 22°C). The individual wrappers protect each piece from moisture, so even once the outer bag is opened they stay fresh for 3-6 months. Store out of direct sunlight."),
    fd("Can bon bons melt in Australian summer?",
       "Bon bons are sugar-based not chocolate-based, so they <strong>resist melting</strong> much better than chocolate lollies. They can get soft and sticky above 30°C (the twist wrappers start sticking to the lolly) but don't truly melt. Still recommend cool-storage in QLD summer and Express shipping during January-February heatwaves."),
    fd("What's the difference between Bon Bons and Fruit Chews?",
       "<strong>Bon bons</strong> are firmer, denser, and individually twist-wrapped — more of a long-chew experience (30-60 seconds per piece). <strong>Fruit chews</strong> (like Starburst or Chupa Chups Chews) tend to be softer, smaller, and sometimes unwrapped or in 'stick' format. Bon bons are better for portion control because each piece is wrapped separately."),
]) + """
</div>

<p><em>Related: <a href="https://sweetsworld.com.au/newcastle/pick-and-mix-lollies-australia/">Pick and Mix Lollies guide</a>, <a href="https://sweetsworld.com.au/sour-candy-australia/">Sour Lollies Australia</a>, <a href="https://sweetsworld.com.au/candy/old-fashion-lollies/">Old-fashioned Australian lollies</a>, <a href="https://sweetsworld.com.au/candy-types/jaffas-lollies-australia/">Jaffas &amp; Allen's classics</a>.</em></p>

<div style="background:linear-gradient(135deg,#5eb4d8 0%,#d16688 100%);padding:38px 22px;text-align:center;color:#fff;border-radius:8px;margin-top:32px">
<h2 style="color:#fff;margin:0 0 14px">Order bon bons today</h2>
<p style="max-width:600px;margin:0 auto 18px;color:#fff8fb">8 flavours 120g + Kingsway 3kg bulk — in-stock, ships same-day from SweetsWorld Newcastle.</p>
<a href="#bon-bons-shop" style="background:#32455a;color:#fff;padding:12px 28px;border-radius:6px;text-decoration:none;font-weight:600;display:inline-block">Shop Now</a>
</div>"""

# Page type — wrap for safety but not strictly required
content = inner  # pages don't need wp:html wrap

print(f"[{'DRY' if DRY else 'LIVE'}] NEW page /{SLUG}/ ({len(content):,} chars, {len(PRODUCTS)} products)")

if DRY:
    Path('/tmp/preview_bonbons.html').write_text(content)
    print(f"  preview → /tmp/preview_bonbons.html")
    sys.exit(0)

payload = {'slug':SLUG,'title':WP_TITLE,'content':content,'status':'publish'}
r = safe_request('POST', f"{WP_BASE}/wp-json/wp/v2/pages", json=payload)
if not r or not r.ok:
    print(f"❌ FAILED: HTTP {r.status_code if r else 'NO RESPONSE'}")
    if r: print(r.text[:300])
    sys.exit(1)
pub = r.json()
pid = pub['id']
url = pub.get('link','')
print(f"✅ Page published: id={pid}")
print(f"   URL: {url}")

r2 = safe_request('GET', f"{WP_BASE}/wp-seo-meta.php",
                 params={'token':SEO_TOKEN,'post_id':pid,'keyword':FOCUS,'title':RM_TITLE,'description':RM_DESC}, auth=None)
print(f"   RankMath: HTTP {r2.status_code if r2 else 'FAIL'}")
# Save publish record
Path(f'/tmp/bonbons_published_{pid}.json').write_text(json.dumps({'id':pid,'url':url,'products':PRODUCTS}, indent=2))
print(f"\npid={pid} url={url}")
