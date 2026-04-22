"""Upgrade post 72490 /candy-types/licorice-allsorts-australia/ from 8K → 25K+ visual hub."""
import sys, json, os, time
from pathlib import Path
sys.path.insert(0, '.')
from common import wp_get, safe_request, WP_BASE, SEO_TOKEN

PID = 72490
DRY = os.environ.get('DRY_RUN','0')=='1'

# ---- BACKUP (mandatory per feedback rule) ----
TS = "20260422_120000"
BK = Path(f"backups/licorice_allsorts_upgrade_{TS}")
BK.mkdir(parents=True, exist_ok=True)
data = wp_get(f'wp/v2/posts/{PID}', context='edit')
assert data, "fetch failed"
(BK / f"licorice-allsorts-australia_post_{PID}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))
print(f"✅ Backup: {BK}/licorice-allsorts-australia_post_{PID}.json")

PRODUCTS = [14511, 51157, 59276, 59460, 14608]  # D/L 270g, D/L 470g Value, Maynards 130g, Big Lolly 850g bulk, Aniseed Rainbow
PRODUCTS_STR = ','.join(str(x) for x in PRODUCTS)

def fd(q,a):
    return (f'<details style="margin-bottom:18px;border:1px solid #e5e5e5;border-radius:6px">'
            f'<summary style="padding:16px 18px;font-weight:600;cursor:pointer;line-height:1.6">{q}</summary>'
            f'<div style="padding:16px 18px 18px;line-height:1.8">{a}</div></details>')

# Post — must wrap in <!-- wp:html --> per Playbook Pitfall #1 (wpautop)
inner = f"""<div style="background:linear-gradient(135deg,#d16688 0%,#32455a 100%);padding:56px 28px;text-align:center;color:#fff;margin-bottom:32px;border-radius:8px">
<h1 style="font-size:42px;margin:0 0 14px;color:#fff;font-weight:700">Licorice Allsorts Australia</h1>
<p style="font-size:18px;max-width:720px;margin:0 auto 20px;line-height:1.6;color:#fff8fb">Darrell Lea, Bassetts, Maynards and Big Lolly — every classic licorice allsorts brand Aussies grew up with. Same-day dispatch from SweetsWorld Newcastle, ships Australia-wide.</p>
<a href="#licorice-allsorts-shop" style="background:#5eb4d8;color:#fff;padding:12px 28px;border-radius:6px;text-decoration:none;font-weight:600;display:inline-block">Shop Licorice Allsorts</a>
</div>

<h2 class="wp-block-heading">What are Licorice Allsorts?</h2>
<p>Licorice Allsorts (also spelled "liquorice allsorts") are a classic British-Australian confectionery mix: layered bite-size pieces combining soft black licorice with coloured coconut-fondant, sweet jelly, and aniseed. Originally created by <strong>Geo Bassett &amp; Co in Sheffield, England in 1899</strong>, they quickly became a staple across the Commonwealth — and nowhere more beloved than Australia.</p>

<p>Each bag is a cross-section of different bite shapes:</p>
<ul>
<li><strong>Licorice sandwiches</strong> — coconut fondant between licorice layers (the iconic stripes)</li>
<li><strong>Licorice wheels</strong> — spiral coil of coconut + licorice</li>
<li><strong>Aniseed jellies</strong> — bright jewel-coloured jellies flavoured with aniseed</li>
<li><strong>Chocolate-coated licorice</strong> — licorice centre under creamy milk chocolate</li>
<li><strong>Pink &amp; blue cream rocks</strong> — sugar-coated fondant pieces for the sweet-tooth</li>
</ul>

<h2 class="wp-block-heading">Best Licorice Allsorts brands in Australia</h2>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:18px;margin:26px 0">

<div style="background:#fff8fb;padding:22px;border-left:4px solid #d16688;border-radius:6px">
<h3 style="margin:0 0 10px;color:#32455a">Darrell Lea</h3>
<p style="margin:0">Australia's home-grown licorice legend — softer texture than UK originals, sweeter fondant. <strong>D/L 270g</strong> the everyday pack, <strong>D/L 470g Value Pack</strong> for families and events.</p>
</div>

<div style="background:#fff8fb;padding:22px;border-left:4px solid #5eb4d8;border-radius:6px">
<h3 style="margin:0 0 10px;color:#32455a">Bassetts (Maynards)</h3>
<p style="margin:0">The original 1899 British recipe — firmer licorice, classic coconut-fondant layers. Nostalgic for British expats and older Aussies. <strong>Maynards 130g</strong> or bulk packs.</p>
</div>

<div style="background:#fff8fb;padding:22px;border-left:4px solid #83c9b8;border-radius:6px">
<h3 style="margin:0 0 10px;color:#32455a">Big Lolly 850g Bulk</h3>
<p style="margin:0">Wholesale-size bag perfect for parties, weddings, catering, retail re-pack. Classic allsorts mix at best-value per-100g pricing.</p>
</div>

<div style="background:#fff8fb;padding:22px;border-left:4px solid #32455a;border-radius:6px">
<h3 style="margin:0 0 10px;color:#32455a">Rainbow Licorice Delights</h3>
<p style="margin:0">Aniseed Sparkles' colourful licorice variant — bright pastel coatings over licorice centres. A lighter, fruitier take on the classic mix.</p>
</div>

</div>

<h2 class="wp-block-heading" id="licorice-allsorts-shop">Shop Licorice Allsorts online</h2>
<p>All products below ship same-day from our Newcastle warehouse, Australia-wide. In stock as of this publication.</p>

[products ids="{PRODUCTS_STR}" columns="4"]

<h2 class="wp-block-heading">How to serve Licorice Allsorts</h2>
<ul>
<li><strong>Lolly jar on the counter</strong> — classic shop-front display</li>
<li><strong>Mixed into a pick-and-mix bowl</strong> — alongside jelly beans and rocky road pieces</li>
<li><strong>Wedding bomboniere</strong> — 30-40g portions in favour bags, especially for vintage/British-themed weddings</li>
<li><strong>Baking topping</strong> — chopped allsorts stirred through fudge, sliced on brownies, or studded in rocky road</li>
<li><strong>After-dinner platter</strong> — alongside Turkish delight and dark chocolate coins</li>
</ul>

<h2 class="wp-block-heading">Licorice Allsorts Slice — the classic Aussie recipe</h2>
<p>One of Australia's most-searched no-bake desserts: <em>licorice allsorts slice</em>. Crushed biscuit base, condensed milk + butter binder, topped with a layer of halved licorice allsorts pressed into set chocolate. Five ingredients, zero baking, legendary CFA lamington-tray status.</p>

<div class="sw-faq-block" style="margin-top:40px">
<h2 class="wp-block-heading">Frequently Asked Questions</h2>
""" + "\n".join([
    fd("Where to buy Licorice Allsorts in Australia?",
       "SweetsWorld ships Licorice Allsorts Australia-wide from our Newcastle warehouse. We stock Darrell Lea, Bassetts (Maynards), Big Lolly 850g bulk bags and Rainbow Licorice Delights. Major cities (Sydney, Melbourne, Brisbane, Perth, Adelaide) typically receive orders in 2-5 business days."),
    fd("What's in a typical Licorice Allsorts bag?",
       "Standard mix contains 6 shapes: licorice sandwiches (black-pink-black layers), licorice wheels (coiled coconut), aniseed jellies (coloured cubes), chocolate-coated licorice pieces, pink cream rocks, and blue cream rocks. Proportions vary by brand — Bassetts leans classic, Darrell Lea has softer texture and sweeter fondant."),
    fd("Are Licorice Allsorts gluten free?",
       "Most commercial Licorice Allsorts are <strong>not gluten free</strong> because the licorice layers contain wheat flour. A few specialty brands offer gluten-free versions (check the individual product pages). If you have coeliac disease, always verify the current pack label."),
    fd("What's the best Licorice Allsorts recipe to make at home?",
       "The <strong>Licorice Allsorts Slice</strong> is Australia's most-loved recipe: 250g crushed plain biscuits + 395g tin condensed milk + 125g butter + 250g halved licorice allsorts + 200g melted chocolate topping. Press into a slice tin, refrigerate 2 hours, slice into squares. Serves 16-20."),
    fd("How many calories in Licorice Allsorts?",
       "Approximately 380-420 kcal per 100g depending on brand. A typical serving (30g, ~6 pieces) is 110-130 kcal. High in sugar (60-70g per 100g) so best enjoyed as an occasional treat, not daily."),
    fd("Bassetts vs Darrell Lea Licorice Allsorts — what's the difference?",
       "<strong>Bassetts</strong> (made in the UK by Maynards) uses the original 1899 recipe — firmer licorice, crisper fondant, more traditional flavour. <strong>Darrell Lea</strong> (Australian) uses softer licorice with sweeter, creamier fondant and slightly looser layering — made for the Australian palate. Dedicated fans usually prefer one or the other distinctly."),
]) + """
</div>

<p><em>Explore more: <a href="https://sweetsworld.com.au/licorice-australia/">All Licorice Australia hub</a>, <a href="https://sweetsworld.com.au/dutch-licorice-australia/">Dutch Licorice (salty drop)</a>, <a href="https://sweetsworld.com.au/candy/old-fashion-lollies/">Old-fashioned Australian lollies</a>.</em></p>

<div style="background:linear-gradient(135deg,#32455a 0%,#d16688 100%);padding:38px 22px;text-align:center;color:#fff;border-radius:8px;margin-top:32px">
<h2 style="color:#fff;margin:0 0 14px">Order Licorice Allsorts today</h2>
<p style="max-width:600px;margin:0 auto 18px;color:#fff8fb">Darrell Lea, Bassetts, Big Lolly bulk — all in stock, ships same-day from SweetsWorld Newcastle.</p>
<a href="#licorice-allsorts-shop" style="background:#5eb4d8;color:#fff;padding:11px 26px;border-radius:6px;text-decoration:none;font-weight:600;display:inline-block">Shop Now</a>
</div>"""

# CRITICAL: wrap in wp:html for post (wpautop protection)
content = f"<!-- wp:html -->\n{inner}\n<!-- /wp:html -->"

WP_TITLE = 'Licorice Allsorts Australia | Darrell Lea, Bassetts, Maynards | SweetsWorld'
RM_TITLE = 'Licorice Allsorts Australia | Bassetts, Darrell Lea, Maynards | SweetsWorld'
RM_DESC = 'Buy Licorice Allsorts online in Australia — Darrell Lea, Bassetts Maynards, Big Lolly 850g bulk. Classic British recipe, same-day dispatch from SweetsWorld Newcastle.'
FOCUS = 'licorice allsorts'

print(f"\n[{'DRY' if DRY else 'LIVE'}] Upgrade post {PID}: 8,375 → {len(content):,} chars")

if DRY:
    Path('/tmp/preview_allsorts.html').write_text(content)
    print("Preview → /tmp/preview_allsorts.html")
    sys.exit(0)

r = safe_request('POST', f"{WP_BASE}/wp-json/wp/v2/posts/{PID}",
                json={'content': content, 'title': WP_TITLE})
print(f"Content/title: HTTP {r.status_code if r else 'FAIL'}")

r2 = safe_request('GET', f"{WP_BASE}/wp-seo-meta.php",
                 params={'token':SEO_TOKEN,'post_id':PID,'keyword':FOCUS,'title':RM_TITLE,'description':RM_DESC}, auth=None)
print(f"RankMath: HTTP {r2.status_code if r2 else 'FAIL'}")
