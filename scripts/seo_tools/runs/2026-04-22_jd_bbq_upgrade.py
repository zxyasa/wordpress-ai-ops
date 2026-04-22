"""Upgrade post 72466 /candy-types/jack-daniels-bbq-australia/ → visual hub with full JD BBQ range."""
import sys, json, os, time
from pathlib import Path
sys.path.insert(0, '.')
from common import wp_get, safe_request, WP_BASE, SEO_TOKEN

PID = 72466
DRY = os.environ.get('DRY_RUN','0')=='1'

TS = "20260422_131000"
BK = Path(f"backups/jd_bbq_upgrade_{TS}")
BK.mkdir(parents=True, exist_ok=True)
data = wp_get(f'wp/v2/posts/{PID}', context='edit')
(BK/f"jack-daniels-bbq-australia_post_{PID}_PRE.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))
print("✅ Backup saved")

# 4 JD Rub Jars + 3 JD 320g rubs + Tennessee Honey 100g + Whiskey Barrel Chips + 3 related BBQ sauces
PRODUCTS = [19278, 19280, 19282, 19292, 69287, 69289, 69291, 28370, 56311, 25094, 46356, 48065]
PRODUCTS_STR = ','.join(str(x) for x in PRODUCTS)

def fd(q,a):
    return (f'<details style="margin-bottom:18px;border:1px solid #e5e5e5;border-radius:6px">'
            f'<summary style="padding:16px 18px;font-weight:600;cursor:pointer;line-height:1.6">{q}</summary>'
            f'<div style="padding:16px 18px 18px;line-height:1.8">{a}</div></details>')

# NO <h1> — post theme handles it
inner = f"""<div style="background:linear-gradient(135deg,#32455a 0%,#d16688 100%);padding:52px 28px;text-align:center;color:#fff;margin-bottom:28px;border-radius:8px">
<p style="font-size:40px;margin:0 0 12px;color:#fff;font-weight:700;line-height:1.1">Jack Daniel's BBQ Sauce Australia</p>
<p style="font-size:18px;max-width:720px;margin:0 auto 18px;line-height:1.6;color:#fff8fb">Official Jack Daniel's BBQ rubs &amp; sauces imported from the USA — Old No. 7, Tennessee Fire, Tennessee Honey, beef / pork / chicken / steak rub jars. Ships same-day from SweetsWorld Newcastle.</p>
<a href="#jd-bbq-shop" style="background:#5eb4d8;color:#fff;padding:12px 28px;border-radius:6px;text-decoration:none;font-weight:600;display:inline-block">Shop JD BBQ Range</a>
</div>

<h2 class="wp-block-heading">Why Jack Daniel's BBQ?</h2>
<p><strong>Jack Daniel's</strong> — the Tennessee whiskey distillery — launched a premium BBQ line that's become the gold standard for smokehouse flavour: <strong>whiskey barrel wood smoke</strong> + <strong>charred oak character</strong> + <strong>sweet-savoury balance</strong>. The JD BBQ range is the only barbecue brand officially licensed by the Jack Daniel's distillery, so the whiskey flavour notes are authentic rather than approximations.</p>

<p>For Australian BBQ enthusiasts, the JD range is particularly prized because:</p>
<ul>
<li><strong>USA authenticity</strong> — imported direct from Lynchburg, Tennessee production</li>
<li><strong>Full rub + sauce ecosystem</strong> — match a Beef Rub to the Old No. 7 BBQ Rub finishing spice for layered flavour</li>
<li><strong>Whiskey barrel smoke chips</strong> — add real Jack Daniel's barrel oak to your smoker for the full experience</li>
<li><strong>Gift-worthy packaging</strong> — the square Jack Daniel's jar designs look premium on the shelf</li>
</ul>

<h2 class="wp-block-heading">The Jack Daniel's BBQ rub range</h2>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px;margin:26px 0">
<div style="background:#fff8fb;padding:18px;border-left:4px solid #d16688;border-radius:6px">
<h3 style="margin:0 0 8px">🥩 Beef &amp; Steak Rub</h3>
<p style="margin:0">Coarse grind — black pepper, onion, garlic, whiskey oak. Best for ribeye, rump, brisket.</p>
</div>
<div style="background:#fff8fb;padding:18px;border-left:4px solid #5eb4d8;border-radius:6px">
<h3 style="margin:0 0 8px">🐷 Pork Rub</h3>
<p style="margin:0">Sweeter notes — brown sugar + smoked paprika. Great for pulled pork, ribs, pork shoulder.</p>
</div>
<div style="background:#fff8fb;padding:18px;border-left:4px solid #83c9b8;border-radius:6px">
<h3 style="margin:0 0 8px">🍗 Chicken Rub</h3>
<p style="margin:0">Herb-forward — thyme, parsley, garlic. Drums, wings, whole roast chicken.</p>
</div>
<div style="background:#fff8fb;padding:18px;border-left:4px solid #32455a;border-radius:6px">
<h3 style="margin:0 0 8px">🌶️ Tennessee Fire BBQ Rub 320g</h3>
<p style="margin:0">Cayenne + chipotle heat with whiskey balance. For hot wings, spicy brisket, fire-lovers.</p>
</div>
<div style="background:#fff8fb;padding:18px;border-left:4px solid #d16688;border-radius:6px">
<h3 style="margin:0 0 8px">🍯 Tennessee Honey BBQ Rub 337g</h3>
<p style="margin:0">Sweet honey-whiskey glaze flavour. Perfect for ribs, chicken, salmon, grilled vegetables.</p>
</div>
<div style="background:#fff8fb;padding:18px;border-left:4px solid #5eb4d8;border-radius:6px">
<h3 style="margin:0 0 8px">🥃 Old No. 7 BBQ Rub 320g</h3>
<p style="margin:0">The signature blend. Balanced whiskey oak + sweet-savoury — universal meat + veg rub.</p>
</div>
</div>

<h2 class="wp-block-heading" id="jd-bbq-shop">Shop Jack Daniel's BBQ online</h2>
<p>All products below ship same-day from our Newcastle warehouse — AU-wide delivery in 2-5 business days.</p>

[products ids="{PRODUCTS_STR}" columns="4"]

<h2 class="wp-block-heading">How to use JD BBQ rubs on the grill</h2>
<ol>
<li><strong>Pat meat dry</strong> — rubs stick best to dry surfaces, not wet</li>
<li><strong>Apply 1-2 tablespoons per 500g</strong> of meat, massaged into all surfaces</li>
<li><strong>Rest 20-60 minutes before cooking</strong> — lets the salt + spices penetrate</li>
<li><strong>For low &amp; slow smoking (brisket, pulled pork)</strong>: apply the rub, rest 2-4 hours, then smoke at 110°C for 8-12 hours using Jack Daniel's Whiskey Barrel Chips</li>
<li><strong>For hot &amp; fast grilling (steak, chops)</strong>: apply the rub, rest 20 min, sear 2-3 minutes per side over high heat</li>
<li><strong>Finish with a baste</strong> of Old No. 7 sauce (when stocked) or your own whiskey+apple cider reduction</li>
</ol>

<h2 class="wp-block-heading">Jack Daniel's whiskey barrel smoke chips — the secret weapon</h2>
<p>We stock the authentic <strong>Jack Daniel's Tennessee Whiskey Barrel Chips 650g</strong> — oak staves sourced from retired whiskey-aging barrels at the Lynchburg distillery. Soak in water 30 minutes, add to your Weber or smoker, and the residual whiskey-oak flavour permeates the meat. This is the <em>actual barrel wood</em>, not "whiskey flavoured" chips.</p>

<h2 class="wp-block-heading">Pairing ideas: BBQ platter + Aussie summer drinks</h2>
<ul>
<li><strong>Backyard ribs</strong> — JD Pork Rub + Old No. 7 BBQ Rub finish + Coopers Pale Ale</li>
<li><strong>Brisket + slaw</strong> — JD Beef Rub + Whiskey Barrel smoke + Smoked Hickory sauce as dip</li>
<li><strong>Hot wings</strong> — JD Tennessee Fire Rub + Bloodhound BBQ Hot Sauce on the side</li>
<li><strong>Father's Day gift pack</strong> — Rub sampler + Whiskey Barrel Chips + Whiskey Honey 100g in a presentation box</li>
</ul>

<div class="sw-faq-block" style="margin-top:40px">
<h2 class="wp-block-heading">Frequently Asked Questions</h2>
""" + "\n".join([
    fd("Where to buy Jack Daniel's BBQ rub in Australia?",
       "SweetsWorld stocks the full Jack Daniel's BBQ rub range — Beef, Pork, Chicken, Steak (9-11oz jars), plus the larger 320g Tennessee Fire, Tennessee Honey and Old No. 7 formats. All imported direct from USA and shipped same-day from our Newcastle warehouse. Australian supermarket BBQ aisles occasionally stock 1-2 variants but for the full range and larger sizes, specialty online retailers like SweetsWorld are your best bet."),
    fd("Does Jack Daniel's BBQ rub contain alcohol?",
       "No — the rubs contain <strong>whiskey-barrel-aged flavourings</strong> (oak extract, smoke essence) but no actual alcohol in measurable amounts. Completely safe for kids, pregnant women, and anyone avoiding alcohol. The flavour profile replicates whiskey character through spices and oak, not ethanol."),
    fd("Is Jack Daniel's BBQ range gluten free?",
       "Most Jack Daniel's BBQ rubs are labelled <strong>gluten-free</strong> — the dry spice blends don't contain wheat or malt. Always check the individual product pack label as formulations can change. The whiskey barrel chips are pure oak wood so no gluten concerns."),
    fd("Which JD BBQ rub is best for pulled pork?",
       "The <strong>JD Pork Rub 11oz</strong> is purpose-formulated for pork — sweeter base with brown sugar and smoked paprika. For competition-style pulled pork, combine: 2 tbsp Pork Rub + 1 tbsp Old No. 7 Rub + 1 tsp Tennessee Honey Rub for sweetness. Rub heavy, smoke at 110°C for 10-14 hours until internal temp hits 95°C."),
    fd("How spicy is JD Tennessee Fire BBQ Rub?",
       "Tennessee Fire sits around 4/10 on a personal heat scale — noticeable kick but not overwhelming. The heat comes from cayenne and chipotle, balanced by the whiskey oak and sugar base. Much milder than pure cayenne or chipotle rubs. Kids sensitive to heat should start with half the usual amount."),
    fd("Can I use JD BBQ rubs on vegetables?",
       "Absolutely — the Old No. 7 and Tennessee Honey rubs are excellent on grilled corn, eggplant, capsicum, mushrooms and sweet potato. The whiskey-oak notes pair especially well with char-grilled eggplant and smoky grilled pineapple. Brush vegetables with olive oil first so the rub adheres."),
    fd("Are these authentic Jack Daniel's products?",
       "Yes — all items in this collection are officially licensed Jack Daniel's brand products, produced in partnership with the Lynchburg distillery. We import direct from authorised USA distributors. Counterfeit JD BBQ products circulate globally — we source only from verified channels."),
]) + """
</div>

<p><em>Related: <a href="https://sweetsworld.com.au/american-food-australia/">American Food Australia</a>, <a href="https://sweetsworld.com.au/candy/american-candy/">American Candy collection</a>, <a href="https://sweetsworld.com.au/candy-guides/hottest-chilli-sauce-newcastle/">Hottest Chilli Sauce Australia</a>.</em></p>

<div style="background:linear-gradient(135deg,#d16688 0%,#32455a 100%);padding:36px 22px;text-align:center;color:#fff;border-radius:8px;margin-top:32px">
<p style="color:#fff;margin:0 0 12px;font-size:26px;font-weight:700">Order Jack Daniel's BBQ today</p>
<p style="max-width:580px;margin:0 auto 16px;color:#fff8fb">12 JD BBQ rubs, sauces, whiskey barrel chips — all in stock, ships same-day.</p>
<a href="#jd-bbq-shop" style="background:#5eb4d8;color:#fff;padding:11px 26px;border-radius:6px;text-decoration:none;font-weight:600;display:inline-block">Shop Now</a>
</div>"""

content = f"<!-- wp:html -->\n{inner}\n<!-- /wp:html -->"
old_len = len((data.get('content') or {}).get('raw','') or (data.get('content') or {}).get('rendered',''))
print(f"[{'DRY' if DRY else 'LIVE'}] Upgrade post {PID}: {old_len:,} → {len(content):,} chars")

WP_TITLE = "Jack Daniel's BBQ Rub & Sauce Australia | Old No.7, Tennessee Fire/Honey | SweetsWorld"
RM_TITLE = "Jack Daniel's BBQ Australia | Beef/Pork/Chicken Rub + Tennessee Fire | SweetsWorld"
RM_DESC = "Buy authentic Jack Daniel's BBQ rubs and sauces online in Australia — Old No. 7, Tennessee Fire, Tennessee Honey, Beef/Pork/Chicken rub jars. Imported direct USA. Same-day dispatch Newcastle."
FOCUS = "jack daniels bbq"

if DRY:
    Path('/tmp/preview_jd.html').write_text(content)
    print("Preview → /tmp/preview_jd.html")
    sys.exit(0)

r = safe_request('POST', f"{WP_BASE}/wp-json/wp/v2/posts/{PID}",
                json={'content': content, 'title': WP_TITLE})
print(f"Content: HTTP {r.status_code if r else 'FAIL'}")
r2 = safe_request('GET', f"{WP_BASE}/wp-seo-meta.php",
                 params={'token':SEO_TOKEN,'post_id':PID,'keyword':FOCUS,'title':RM_TITLE,'description':RM_DESC}, auth=None)
print(f"RankMath: HTTP {r2.status_code if r2 else 'FAIL'}")
