"""Upgrade post 72476 /candy-types/wicked-fizz-australia/ from 7.8K thin SEO to 20K+ visual hub."""
import sys, json, os, time
from pathlib import Path
sys.path.insert(0, '.')
from common import wp_get, safe_request, WP_BASE, SEO_TOKEN

PID = 72476
DRY = os.environ.get('DRY_RUN','0')=='1'

# Backup first
TS = "20260422_123000"
BK = Path(f"backups/wicked_fizz_upgrade_{TS}")
BK.mkdir(parents=True, exist_ok=True)
data = wp_get(f'wp/v2/posts/{PID}', context='edit')
(BK/f"wicked-fizz-australia_post_{PID}_PRE.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))
print(f"✅ Backup saved")

# Curated products: 1 Wicked Fizz + 7 in-stock fizzy candy alternatives
PRODUCTS = [61136, 15409, 17715, 22619, 22623, 24329, 16319, 17811]
PRODUCTS_STR = ','.join(str(x) for x in PRODUCTS)

def fd(q,a):
    return (f'<details style="margin-bottom:18px;border:1px solid #e5e5e5;border-radius:6px">'
            f'<summary style="padding:16px 18px;font-weight:600;cursor:pointer;line-height:1.6">{q}</summary>'
            f'<div style="padding:16px 18px 18px;line-height:1.8">{a}</div></details>')

inner = f"""<div style="background:linear-gradient(135deg,#5eb4d8 0%,#32455a 100%);padding:56px 28px;text-align:center;color:#fff;margin-bottom:32px;border-radius:8px">
<h1 style="font-size:42px;margin:0 0 14px;color:#fff;font-weight:700">Wicked Fizz Australia</h1>
<p style="font-size:18px;max-width:720px;margin:0 auto 20px;line-height:1.6;color:#fff8fb">Chewy, fizzy, sour — the cult-favourite Australian candy plus the best fizzy chew alternatives. Same-day dispatch from SweetsWorld Newcastle, ships Australia-wide.</p>
<a href="#wicked-fizz-shop" style="background:#d16688;color:#fff;padding:12px 28px;border-radius:6px;text-decoration:none;font-weight:600;display:inline-block">Shop Fizzy Chews</a>
</div>

<h2 class="wp-block-heading">What are Wicked Fizz chews?</h2>
<p>Wicked Fizz is an Australian confectionery brand famous for their <strong>individually-wrapped fizzy chewy candies</strong> — each 12g piece packs an intense fizz-burst the moment you bite in. Popular flavours include <strong>Cola, Grape, Blue Raspberry, Fizz Berry, Orange, Watermelon</strong> and the original sour sherbet-filled chews that made them an Aussie party and pick-and-mix lolly bowl staple.</p>

<p>The magic is the combination: a <strong>chewy taffy-like outer</strong> holds a <strong>fizzy sherbet-style centre</strong> that activates with saliva — giving you that signature "wicked" tingle. Kids love them for the bright colours and novelty texture; adults love them for nostalgia.</p>

<div style="background:#fff5f0;border-left:4px solid #d16688;padding:18px 22px;margin:24px 0">
<strong>⚠️ Current stock note:</strong> Wicked Fizz supply has been intermittent in Australia recently due to import issues. We currently stock the <strong>105g Sour Chewy Box</strong> while supplies last, and we've curated the <strong>best alternative fizzy chews</strong> below (Fizzers, Fizzer, Fini, Chupa Chups 3D Fizzy) to fill the gap until individual flavours are back.</p>
</div>

<h2 class="wp-block-heading">Wicked Fizz flavours — the complete lineup</h2>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px;margin:24px 0">

<div style="background:#fff8fb;padding:20px;border-left:4px solid #d16688;border-radius:6px">
<h3 style="margin:0 0 10px;color:#32455a">Cola</h3>
<p style="margin:0">Classic brown cola chew with the distinctive caramel-vanilla cola fizz. Most popular single flavour.</p>
</div>

<div style="background:#fff8fb;padding:20px;border-left:4px solid #5eb4d8;border-radius:6px">
<h3 style="margin:0 0 10px;color:#32455a">Blue Raspberry</h3>
<p style="margin:0">Vibrant blue chew with tart raspberry + citric fizz. Kids' #1.</p>
</div>

<div style="background:#fff8fb;padding:20px;border-left:4px solid #83c9b8;border-radius:6px">
<h3 style="margin:0 0 10px;color:#32455a">Grape</h3>
<p style="margin:0">Deep purple grape flavour with a sweet-tart balance. Surprisingly popular with adults.</p>
</div>

<div style="background:#fff8fb;padding:20px;border-left:4px solid #32455a;border-radius:6px">
<h3 style="margin:0 0 10px;color:#32455a">Fizz Berry</h3>
<p style="margin:0">Mixed berry combo — strawberry, raspberry, blackberry notes. Limited release favourite.</p>
</div>

<div style="background:#fff8fb;padding:20px;border-left:4px solid #d16688;border-radius:6px">
<h3 style="margin:0 0 10px;color:#32455a">Orange</h3>
<p style="margin:0">Bright zesty orange citrus punch. Great for kids' party mixes.</p>
</div>

<div style="background:#fff8fb;padding:20px;border-left:4px solid #5eb4d8;border-radius:6px">
<h3 style="margin:0 0 10px;color:#32455a">Watermelon</h3>
<p style="margin:0">Sweet summery watermelon with a mild fizz. Newest addition to the range.</p>
</div>

</div>

<h2 class="wp-block-heading" id="wicked-fizz-shop">Shop Wicked Fizz + best fizzy chew alternatives</h2>
<p>Currently available: Wicked Fizz Sour Chewy Box (105g) + curated fizzy chew alternatives — all in-stock, ships same-day from our Newcastle warehouse.</p>

[products ids="{PRODUCTS_STR}" columns="4"]

<h2 class="wp-block-heading">Best alternatives when Wicked Fizz is low stock</h2>
<p>Because Wicked Fizz supply fluctuates, here's our ranking of the closest-experience alternatives:</p>
<ol>
<li><strong>Swizzels Giant Fizzers 40g</strong> — similar chew+fizz combo, UK import. Five fruit flavours per pack.</li>
<li><strong>FIZZER Sour Strawberry / Creamy Soda / Grape Soda 11.6g</strong> — Individually wrapped fizzy chews from South African specialty brand, very similar texture profile.</li>
<li><strong>Fizzy Strawberry Bricks 150g</strong> — Chewy fizzy taffy squares, great for bulk pick-and-mix.</li>
<li><strong>Chupa Chups 3D Fizzy Drinks 15g</strong> — Novel 3D-printed fizzy candies shaped like soft drink bottles.</li>
<li><strong>Trolli Fizzy Soda Bottle 2kg</strong> — Gummy soda bottles with a strong fizz coating, German classic.</li>
</ol>

<h2 class="wp-block-heading">Who makes Wicked Fizz chews?</h2>
<p>Wicked Fizz is produced in <strong>Australia</strong> and primarily distributed domestically. The brand is owned by one of Australia's mid-size confectionery importers and has been a staple at corner stores, milk bars and party supply shops since the mid-2000s. Like many smaller Aussie candy brands, distribution can be patchy — which is why shops like SweetsWorld specialise in tracking down and importing available stock.</p>

<h2 class="wp-block-heading">Wicked Fizz for parties, lolly bars and bomboniere</h2>
<p>The 12g individually-wrapped format makes Wicked Fizz ideal for:</p>
<ul>
<li><strong>Kids' birthday party lolly bars</strong> — each kid picks 5-10 chews, grabs them in tongs, into a bag</li>
<li><strong>Pick and mix wedding bomboniere</strong> (see our <a href="https://sweetsworld.com.au/newcastle/pick-and-mix-lollies-australia/">pick and mix lollies guide</a>)</li>
<li><strong>School fete stalls</strong> — 20c-50c each at typical fete markup</li>
<li><strong>Sports team treat bags</strong> — the fizz fuels post-match energy</li>
<li><strong>Corporate conference buffets</strong> — retro novelty hits hard with adult crowds</li>
</ul>

<div class="sw-faq-block" style="margin-top:40px">
<h2 class="wp-block-heading">Frequently Asked Questions</h2>
""" + "\n".join([
    fd("Where to buy Wicked Fizz chews in Australia?",
       "SweetsWorld ships Wicked Fizz Sour Chewy Box (105g) and curated fizzy chew alternatives Australia-wide from our Newcastle warehouse. Individual-flavour 12g boxes come and go with import availability — check the product listings for current stock. Sydney, Melbourne, Brisbane, Perth, and Adelaide orders typically arrive in 2-5 business days."),
    fd("Why is Wicked Fizz hard to find in supermarkets?",
       "Wicked Fizz has smaller distribution than mass-market brands like Allen's or Nestle, so it rotates in and out of supermarket specialty aisles. Party supply stores, milk bars, and dedicated candy retailers (like SweetsWorld online) are typically where you find the full range or bulk packs."),
    fd("Are Wicked Fizz chews vegan or gluten free?",
       "Wicked Fizz chews typically contain gelatin (not vegan) and may contain wheat-based thickeners (not reliably gluten-free). Always check the current pack label — formulations can change between production runs. If you need vegan/GF options, look for our certified <a href=\"https://sweetsworld.com.au/candy/vegan-lollies/\">vegan lollies range</a>."),
    fd("What's the difference between Wicked Fizz and Fizzers (Swizzels)?",
       "<strong>Wicked Fizz</strong> is Australian-made with a soft chewy taffy outer and fizzy sherbet centre. <strong>Swizzels Fizzers</strong> are British-made with a harder compressed-tablet texture and more pronounced fizz-tingle. Fans of soft chew usually prefer Wicked Fizz; fans of sharp crispy fizz prefer Fizzers. Both are in-stock at SweetsWorld."),
    fd("How long do Wicked Fizz chews last?",
       "Unopened, Wicked Fizz chews last 12-18 months from manufacture date stored at room temperature (below 22°C). Once opened, the individual 12g wrappers keep each chew fresh — consume within 6-8 weeks for optimal chewy texture. Older chews can become hard or sticky but remain safe if stored properly."),
    fd("Can I order Wicked Fizz in bulk boxes?",
       "We stock the <strong>Wicked Fizz Sour Chewy Box (105g)</strong> as a retail-pack option; larger bulk boxes (72-piece flavour boxes) come and go with supply. Contact SweetsWorld for wholesale enquiries if you need larger quantities for events, resale, or corporate gifts."),
    fd("Are Wicked Fizz chews safe for kids?",
       "Wicked Fizz chews are sold as confectionery suitable for kids aged 4+ (younger children risk choking on chewy candy). The acidity of the fizz can irritate sensitive teeth/gums — moderation recommended. Not suitable for anyone with braces due to stickiness."),
]) + """
</div>

<p><em>Related: <a href="https://sweetsworld.com.au/sour-candy-australia/">Sour Lollies Australia</a>, <a href="https://sweetsworld.com.au/newcastle/pick-and-mix-lollies-australia/">Pick and Mix Lollies</a>, <a href="https://sweetsworld.com.au/candy/old-fashion-lollies/">Old-fashioned Australian lollies</a>, <a href="https://sweetsworld.com.au/candy/party-sweets/">Party sweets</a>.</em></p>

<div style="background:linear-gradient(135deg,#32455a 0%,#5eb4d8 100%);padding:36px 22px;text-align:center;color:#fff;border-radius:8px;margin-top:32px">
<h2 style="color:#fff;margin:0 0 12px;font-size:26px">Order Wicked Fizz today</h2>
<p style="max-width:580px;margin:0 auto 16px;color:#fff8fb">Wicked Fizz Sour Chewy Box + 7 curated fizzy chew alternatives — all in-stock, ships same-day from SweetsWorld Newcastle.</p>
<a href="#wicked-fizz-shop" style="background:#d16688;color:#fff;padding:11px 26px;border-radius:6px;text-decoration:none;font-weight:600;display:inline-block">Shop Now</a>
</div>"""

content = f"<!-- wp:html -->\n{inner}\n<!-- /wp:html -->"
print(f"[{'DRY' if DRY else 'LIVE'}] Upgrade post {PID}: 7,848 → {len(content):,} chars")

WP_TITLE = 'Wicked Fizz Australia | Buy Fizzy Chews + Alternatives | SweetsWorld'
RM_TITLE = 'Wicked Fizz Australia | Sour Chewy Box + Fizzy Chews Online | SweetsWorld'
RM_DESC = 'Buy Wicked Fizz Sour Chewy Box online in Australia + curated fizzy chew alternatives (Swizzels Fizzers, FIZZER, Trolli). Same-day dispatch Newcastle.'
FOCUS = 'wicked fizz'

if DRY:
    Path('/tmp/preview_wicked.html').write_text(content)
    print("Preview → /tmp/preview_wicked.html")
    sys.exit(0)

r = safe_request('POST', f"{WP_BASE}/wp-json/wp/v2/posts/{PID}",
                json={'content': content, 'title': WP_TITLE})
print(f"Content: HTTP {r.status_code if r else 'FAIL'}")
r2 = safe_request('GET', f"{WP_BASE}/wp-seo-meta.php",
                 params={'token':SEO_TOKEN,'post_id':PID,'keyword':FOCUS,'title':RM_TITLE,'description':RM_DESC}, auth=None)
print(f"RankMath: HTTP {r2.status_code if r2 else 'FAIL'}")
