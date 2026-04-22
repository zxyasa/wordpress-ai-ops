"""Batch upgrade: Jaffas (72480) + Minties (72482) + Lotus Biscoff (72452).
All posts → NO inline H1, wp:html wrap, <details> FAQ, backup-first, verify."""
import sys, json, os, time
from pathlib import Path
sys.path.insert(0, '.')
from common import wp_get, safe_request, WP_BASE, SEO_TOKEN

DRY = os.environ.get('DRY_RUN','0')=='1'
TS = "20260422_125500"
BK = Path(f"backups/batch3_upgrade_{TS}")
BK.mkdir(parents=True, exist_ok=True)

def fd(q,a):
    return (f'<details style="margin-bottom:18px;border:1px solid #e5e5e5;border-radius:6px">'
            f'<summary style="padding:16px 18px;font-weight:600;cursor:pointer;line-height:1.6">{q}</summary>'
            f'<div style="padding:16px 18px 18px;line-height:1.8">{a}</div></details>')

# -------------- JAFFAS (post 72480) --------------
JAFFAS_PRODUCTS = [15084, 67588, 15080, 15100, 15086, 15088, 15102, 15104, 15090, 15092, 15094]
JAFFAS_STR = ','.join(str(x) for x in JAFFAS_PRODUCTS)
JAFFAS_INNER = f"""<div style="background:linear-gradient(135deg,#d16688 0%,#32455a 100%);padding:52px 28px;text-align:center;color:#fff;margin-bottom:28px;border-radius:8px">
<p style="font-size:40px;margin:0 0 12px;color:#fff;font-weight:700;line-height:1.1">Jaffas &amp; Allen's Lollies Australia</p>
<p style="font-size:18px;max-width:720px;margin:0 auto 18px;line-height:1.6;color:#fff8fb">Allen's Jaffas, Chico's, Red Frogs, Killer Pythons and the Aussie classics you grew up with. Bulk 1kg packs, same-day dispatch from SweetsWorld Newcastle.</p>
<a href="#jaffas-shop" style="background:#5eb4d8;color:#fff;padding:12px 28px;border-radius:6px;text-decoration:none;font-weight:600;display:inline-block">Shop Jaffas &amp; Allen's</a>
</div>

<h2 class="wp-block-heading">The story of Jaffas</h2>
<p><strong>Jaffas</strong> — the iconic orange-coated milk-chocolate balls — have been an Australian and New Zealand favourite since 1931. Originally named after the Jaffa orange (a Middle Eastern citrus), the hard candy shell hides a soft milk chocolate centre. Every generation of Aussies has rolled a Jaffa down a cinema aisle at some point — the cultural reference is baked into the country.</p>

<p>Allen's (owned by Nestlé Australia) is the maker behind Jaffas today, along with most of Australia's most-loved lolly brands: <strong>Chico's</strong> (chocolate-coated milk-flavoured gum drops), <strong>Killer Pythons</strong> (rainbow jelly snakes), <strong>Red Frogs</strong> (the bright red jelly frog that launched a thousand childhood memories), <strong>Snake Alive</strong>, <strong>Milko Chews</strong>, <strong>Pineapples</strong>, and the legendary <strong>Minties</strong> and <strong>Fantales</strong>.</p>

<h2 class="wp-block-heading">Classic Allen's lollies we stock</h2>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px;margin:26px 0">
<div style="background:#fff8fb;padding:18px;border-left:4px solid #d16688;border-radius:6px"><h3 style="margin:0 0 8px">🟠 Jaffas 1kg</h3><p style="margin:0">Orange-chocolate balls. Cinema classic.</p></div>
<div style="background:#fff8fb;padding:18px;border-left:4px solid #5eb4d8;border-radius:6px"><h3 style="margin:0 0 8px">🍫 Chico's 1.3kg</h3><p style="margin:0">Chocolate-coated milk gum drops, nostalgic flavor.</p></div>
<div style="background:#fff8fb;padding:18px;border-left:4px solid #83c9b8;border-radius:6px"><h3 style="margin:0 0 8px">🟢 Killer Pythons 1kg</h3><p style="margin:0">Rainbow gummy snakes. Party bag hero.</p></div>
<div style="background:#fff8fb;padding:18px;border-left:4px solid #32455a;border-radius:6px"><h3 style="margin:0 0 8px">🐸 Red Frogs 1.3kg</h3><p style="margin:0">Bright red jelly frogs. Uni mission culture icon.</p></div>
<div style="background:#fff8fb;padding:18px;border-left:4px solid #d16688;border-radius:6px"><h3 style="margin:0 0 8px">🍍 Pineapples 1.3kg</h3><p style="margin:0">Chewy yellow pineapple lollies. School canteen classic.</p></div>
<div style="background:#fff8fb;padding:18px;border-left:4px solid #5eb4d8;border-radius:6px"><h3 style="margin:0 0 8px">🥛 Milko Chews 800g</h3><p style="margin:0">Soft white vanilla milk-flavour chew.</p></div>
</div>

<h2 class="wp-block-heading" id="jaffas-shop">Shop Jaffas &amp; Allen's lollies online</h2>
<p>All bulk Allen's lollies below ship same-day from our Newcastle warehouse Australia-wide.</p>

[products ids="{JAFFAS_STR}" columns="4"]

<div class="sw-faq-block" style="margin-top:40px"><h2 class="wp-block-heading">Frequently Asked Questions</h2>
""" + "\n".join([
    fd("Where to buy Jaffas in bulk in Australia?",
       "SweetsWorld stocks Allen's Jaffas in 1kg bulk bags — ships same-day from Newcastle. Perfect for wedding bomboniere, party lolly bars, movie-themed events, and bulk pick-and-mix. Major AU cities receive orders in 2-5 business days. For very large orders (5kg+), contact us for wholesale pricing."),
    fd("Are Allen's Jaffas still made the same way as the 1930s?",
       "The fundamental recipe — orange candy shell over milk chocolate — hasn't changed since 1931. Some minor formulation tweaks happen for modern food safety and ingredient regulations (e.g. natural vs synthetic colours). Compared to the 1980s version, today's Jaffas have slightly less intense orange flavour but a smoother chocolate centre."),
    fd("What are Red Frogs and why are they an Aussie university tradition?",
       "Allen's <strong>Red Frogs</strong> became a university mission icon because of the <strong>Red Frogs Crew</strong> — a volunteer welfare group that hands out Red Frogs and provides sober support to students at Schoolies Week and uni events across Australia since 1997. The bright red frog became their symbol. Today they're more than a lolly — they're a cultural marker."),
    fd("Are Allen's lollies gluten free or vegetarian?",
       "Most Allen's Jaffas, Pineapples, and hard-candy lollies are labelled gluten-free. Jellies (Killer Pythons, Red Frogs, Snake Alive) typically contain gelatin and are <strong>not</strong> suitable for vegetarians/vegans. Chico's and Milko Chews contain milk-based ingredients. Always check the current pack label for definitive info."),
    fd("What's the best Allen's lolly mix for kids' parties?",
       "Our top 5 for kids ages 5-12: <strong>Killer Pythons</strong> (sharable), <strong>Red Frogs</strong> (kid-classic), <strong>Jaffas</strong> (small enough to portion), <strong>Pineapples</strong> (school canteen nostalgia), <strong>Chico's</strong> (sweet variety). Buy 1kg bulk of each, portion into 50g bags for each kid."),
    fd("Can I put Jaffas in a microwave?",
       "No — the hard orange candy shell will melt and the chocolate centre will burn. Jaffas are designed to be eaten at room temperature. If you want melty chocolate, use regular chocolate bars instead."),
]) + """
</div>

<p><em>See also: <a href="https://sweetsworld.com.au/newcastle/pick-and-mix-lollies-australia/">Pick and Mix Lollies guide</a>, <a href="https://sweetsworld.com.au/candy-types/minties-australia/">Minties Australia</a>, <a href="https://sweetsworld.com.au/candy/old-fashion-lollies/">Old-fashioned Australian lollies</a>.</em></p>

<div style="background:linear-gradient(135deg,#32455a 0%,#d16688 100%);padding:36px 22px;text-align:center;color:#fff;border-radius:8px;margin-top:32px">
<p style="color:#fff;margin:0 0 12px;font-size:26px;font-weight:700">Order Allen's bulk today</p>
<p style="max-width:580px;margin:0 auto 16px;color:#fff8fb">11 classic Allen's lollies in-stock — 1kg / 1.3kg bulk packs. Same-day dispatch.</p>
<a href="#jaffas-shop" style="background:#5eb4d8;color:#fff;padding:11px 26px;border-radius:6px;text-decoration:none;font-weight:600;display:inline-block">Shop Now</a>
</div>"""

# -------------- MINTIES (post 72482) --------------
MINTIES_PRODUCTS = [20048, 307, 14801, 13579, 14437, 14453, 1253, 17689, 14943]
MINTIES_STR = ','.join(str(x) for x in MINTIES_PRODUCTS)
MINTIES_INNER = f"""<div style="background:linear-gradient(135deg,#83c9b8 0%,#32455a 100%);padding:52px 28px;text-align:center;color:#fff;margin-bottom:28px;border-radius:8px">
<p style="font-size:40px;margin:0 0 12px;color:#fff;font-weight:700;line-height:1.1">Minties Australia</p>
<p style="font-size:18px;max-width:720px;margin:0 auto 18px;line-height:1.6;color:#fff8fb">Allen's Minties 1kg bulk + the best Australian mint lollies. Mint Leaves, White Knights Mint Chews, Peppermint Cream, Spearmint Leaves. Same-day dispatch from SweetsWorld Newcastle.</p>
<a href="#minties-shop" style="background:#d16688;color:#fff;padding:12px 28px;border-radius:6px;text-decoration:none;font-weight:600;display:inline-block">Shop Minties &amp; Mint</a>
</div>

<h2 class="wp-block-heading">What are Minties?</h2>
<p><strong>Minties</strong> are Australia's iconic chewy white mint lolly, made by Allen's (Nestlé Australia) since 1922. The distinctive crinkled white wrapper hides a dense, soft mint chew that's strong peppermint up front and lingers for 20-30 minutes. Every Aussie has a Minties story — from school tuck shops to dental waiting rooms to the bottom of grandma's handbag.</p>

<p>Beyond Minties themselves, Australia has a rich heritage of mint-forward lollies: <strong>Mint Leaves</strong> (chewy jellies with peppermint kick), <strong>White Knights Mint Chews</strong> (from the NZ chocolatier), <strong>Fry's Peppermint Cream</strong> (UK chocolate-coated fondant classic), <strong>Spearmint Leaves</strong> (milder cousin of Mint Leaves), and specialty gluten-free options like <strong>Davies Mint Centres</strong>.</p>

<h2 class="wp-block-heading">Minties — the Aussie classics</h2>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px;margin:26px 0">
<div style="background:#fff8fb;padding:18px;border-left:4px solid #83c9b8;border-radius:6px"><h3 style="margin:0 0 8px">🌿 Allen's Minties 1kg</h3><p style="margin:0">The classic — chewy white peppermint lolly. Bulk size.</p></div>
<div style="background:#fff8fb;padding:18px;border-left:4px solid #32455a;border-radius:6px"><h3 style="margin:0 0 8px">🍃 Mint Leaves 500g</h3><p style="margin:0">Soft jellied mint leaves, stronger mint kick than Minties.</p></div>
<div style="background:#fff8fb;padding:18px;border-left:4px solid #d16688;border-radius:6px"><h3 style="margin:0 0 8px">⚪ White Knights Mint Chews 120g</h3><p style="margin:0">NZ chocolate-mint combination. Cult favourite across the ditch.</p></div>
<div style="background:#fff8fb;padding:18px;border-left:4px solid #5eb4d8;border-radius:6px"><h3 style="margin:0 0 8px">🍬 Fry's Peppermint Cream 49g</h3><p style="margin:0">UK classic — chocolate-coated peppermint fondant bar.</p></div>
</div>

<h2 class="wp-block-heading" id="minties-shop">Shop Minties &amp; mint lollies online</h2>
[products ids="{MINTIES_STR}" columns="4"]

<div class="sw-faq-block" style="margin-top:40px"><h2 class="wp-block-heading">Frequently Asked Questions</h2>
""" + "\n".join([
    fd("Where to buy Allen's Minties in bulk?",
       "SweetsWorld stocks Allen's Minties 1kg bulk bags — ships same-day from Newcastle Australia-wide. Perfect for wedding bomboniere, corporate events, party lolly bars, and bulk pick-and-mix. For 5kg+ wholesale orders, contact us for pricing."),
    fd("Why do people chew Minties so slowly?",
       "Minties have a dense, slow-melting chewy texture that rewards patience. Bite too hard and it sticks to your teeth; chew too fast and the peppermint hits in one burst. The classic Aussie technique: bite off a small piece, let it soften for 10-20 seconds, then slow-chew for 2-3 minutes. This is why Minties is the go-to dental waiting-room lolly."),
    fd("Are Minties gluten free or vegan?",
       "Standard Allen's Minties contain gelatin (not vegan) and are not certified gluten-free. For gluten-free mint alternatives, try <strong>Davies Mint Centres 200g</strong> (explicitly labelled gluten-free) — also stocked at SweetsWorld."),
    fd("What are the best mint lollies for fresh breath?",
       "For actual breath-freshening, <strong>Mint Leaves 500g</strong> has the strongest menthol kick. Minties provide longer-lasting mild mint. Extra-strength options like Fisherman's Friends (when stocked) work for serious mint fixes but aren't really a lolly — more of a medicated lozenge."),
    fd("What's the difference between Mint Leaves and Spearmint Leaves?",
       "<strong>Mint Leaves</strong> use peppermint oil — sharp, cooling, classic mint flavour. <strong>Spearmint Leaves</strong> use spearmint oil — milder, sweeter, slightly herbal. Fans tend to firmly prefer one or the other. Many Aussie households stock both."),
    fd("Can Minties pull out your fillings?",
       "Old-style ultra-dense Minties (pre-2000s formulations) were infamous for loosening fillings. Modern Minties are slightly softer — still chewy enough to mind loose fillings, but not the dental hazard they once were. Bite smaller pieces if you have fillings."),
]) + """
</div>

<p><em>See also: <a href="https://sweetsworld.com.au/candy-types/jaffas-lollies-australia/">Jaffas &amp; Allen's Lollies</a>, <a href="https://sweetsworld.com.au/candy/old-fashion-lollies/">Old-fashioned Australian lollies</a>, <a href="https://sweetsworld.com.au/newcastle/pick-and-mix-lollies-australia/">Pick and Mix Lollies</a>.</em></p>

<div style="background:linear-gradient(135deg,#32455a 0%,#83c9b8 100%);padding:36px 22px;text-align:center;color:#fff;border-radius:8px;margin-top:32px">
<p style="color:#fff;margin:0 0 12px;font-size:26px;font-weight:700">Order Minties today</p>
<p style="max-width:580px;margin:0 auto 16px;color:#fff8fb">Allen's Minties 1kg + 8 mint lolly alternatives, in-stock now.</p>
<a href="#minties-shop" style="background:#d16688;color:#fff;padding:11px 26px;border-radius:6px;text-decoration:none;font-weight:600;display:inline-block">Shop Now</a>
</div>"""

# -------------- LOTUS BISCOFF (post 72452) --------------
BISCOFF_PRODUCTS = [64542, 65419, 64657, 68775]
BISCOFF_STR = ','.join(str(x) for x in BISCOFF_PRODUCTS)
BISCOFF_INNER = f"""<div style="background:linear-gradient(135deg,#d16688 0%,#32455a 100%);padding:52px 28px;text-align:center;color:#fff;margin-bottom:28px;border-radius:8px">
<p style="font-size:40px;margin:0 0 12px;color:#fff;font-weight:700;line-height:1.1">Lotus Biscoff Australia</p>
<p style="font-size:18px;max-width:720px;margin:0 auto 18px;line-height:1.6;color:#fff8fb">Lotus Biscoff Spread in 400g retail + 1.6kg bulk, plus Biscoff Vanilla 110g. Belgian caramelised biscuit spread direct from Europe. Same-day dispatch from SweetsWorld Newcastle.</p>
<a href="#biscoff-shop" style="background:#5eb4d8;color:#fff;padding:12px 28px;border-radius:6px;text-decoration:none;font-weight:600;display:inline-block">Shop Lotus Biscoff</a>
</div>

<h2 class="wp-block-heading">What is Lotus Biscoff?</h2>
<p><strong>Lotus Biscoff</strong> is the Belgian caramelised biscuit brand that conquered the world thanks to one thing: airline food. First served by Delta Airlines in the 1980s, the unassuming rectangular biscuit with burnt-sugar caramel flavour became a transatlantic obsession. In 2007 Lotus released the spread (<em>speculoos</em> / biscuit butter) and by 2015 it had become the Nutella of the 2010s — appearing in cafes, ice cream shops, TikTok desserts, and home pantries across Australia.</p>

<p>The base flavour is <strong>caramelised sugar + gentle cinnamon + a hint of nutmeg</strong> — like a graham cracker but denser, smoother and more butterscotch-forward.</p>

<h2 class="wp-block-heading">Lotus Biscoff varieties we stock</h2>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px;margin:26px 0">
<div style="background:#fff8fb;padding:18px;border-left:4px solid #d16688;border-radius:6px"><h3 style="margin:0 0 8px">🥫 Biscoff Spread 1.6kg Bulk</h3><p style="margin:0">Commercial catering size — cafes, bakeries, dessert businesses. Smooth format.</p></div>
<div style="background:#fff8fb;padding:18px;border-left:4px solid #5eb4d8;border-radius:6px"><h3 style="margin:0 0 8px">🥄 Biscoff Spread 400g Smooth</h3><p style="margin:0">Retail size for home baking and breakfast spreading.</p></div>
<div style="background:#fff8fb;padding:18px;border-left:4px solid #83c9b8;border-radius:6px"><h3 style="margin:0 0 8px">🍪 Lotus Biscoff Vanilla 110g</h3><p style="margin:0">Biscuit format with vanilla twist — sandwich-style with cream centre.</p></div>
<div style="background:#fff8fb;padding:18px;border-left:4px solid #32455a;border-radius:6px"><h3 style="margin:0 0 8px">🔥 Kelly's Toasted Mallows 140g</h3><p style="margin:0">Perfect pairing — toast on top of Biscoff spread, or use as dipper.</p></div>
</div>

<h2 class="wp-block-heading">What to do with Biscoff spread</h2>
<ol>
<li><strong>Stirred into coffee</strong> — 1 tsp in hot milk = instant caramel-cinnamon latte</li>
<li><strong>Swirled through ice cream</strong> — melt 2 tbsp, drizzle over vanilla</li>
<li><strong>Banana toast</strong> — smear on sourdough, top with sliced banana and sea salt</li>
<li><strong>Cheesecake base / topping</strong> — crushed Biscoff biscuits + melted butter = next-level base</li>
<li><strong>Filling for brownies/cupcakes</strong> — spoon centres while still warm</li>
<li><strong>Apple dipper</strong> — quick afternoon snack for kids</li>
<li><strong>Replacement for peanut butter in PB&amp;J</strong> — totally different vibe, works</li>
</ol>

<h2 class="wp-block-heading" id="biscoff-shop">Shop Lotus Biscoff online</h2>
[products ids="{BISCOFF_STR}" columns="4"]

<div class="sw-faq-block" style="margin-top:40px"><h2 class="wp-block-heading">Frequently Asked Questions</h2>
""" + "\n".join([
    fd("Where to buy Lotus Biscoff spread in Australia?",
       "SweetsWorld stocks Lotus Biscoff Spread in both 400g retail and 1.6kg bulk (catering) sizes, shipped same-day from Newcastle Australia-wide. Major supermarkets carry 400g intermittently — for reliable bulk supply (cafes, bakeries, dessert businesses), online specialty retailers are your best bet."),
    fd("Is Lotus Biscoff vegan?",
       "Yes — the original Lotus Biscoff biscuits and the Biscoff spread are <strong>both vegan</strong>. No dairy, no eggs, no animal products. This is one reason for the brand's popularity in plant-based baking — it provides the caramel-cinnamon flavour that usually comes from butter."),
    fd("Is Biscoff spread gluten free?",
       "<strong>No</strong> — Lotus Biscoff spread contains wheat flour (it's made from ground biscuits). Gluten-free alternatives with similar flavour include homemade speculoos paste using gluten-free shortbread, or Speculoos-flavoured brands that make dedicated GF versions (rare). Always check individual product labels."),
    fd("Smooth vs Crunchy Biscoff — which is better?",
       "<strong>Smooth</strong> is best for drinks, ice cream swirls, and cheesecake toppings — integrates evenly. <strong>Crunchy</strong> (when available) adds texture to cookies, brownies, and toast spreads. For most baking uses, smooth is the safer default."),
    fd("Can I use Biscoff spread instead of peanut butter?",
       "Yes — most recipes work 1:1 but the flavour profile is very different (caramel-cinnamon vs nutty). Biscoff has more sugar and less protein/fat than peanut butter, so baked goods may spread slightly more. For cookies and frostings, Biscoff works beautifully. For peanut-butter-and-jelly sandwiches, it's a revelation."),
    fd("What's the difference between Lotus Biscoff and speculoos?",
       "<strong>Speculoos</strong> is the generic Belgian/Dutch term for caramelised spiced biscuits — a category. <strong>Lotus Biscoff</strong> is a specific commercial brand of speculoos. Other speculoos brands exist (TRADER JOE'S Cookie Butter, De Ruijter Spice Cookie) but Lotus dominates global distribution. Flavour is very similar across brands with minor variations."),
]) + """
</div>

<p><em>Related: <a href="https://sweetsworld.com.au/candy/american-candy/">American Candy</a>, <a href="https://sweetsworld.com.au/chocolate/">Chocolates</a>, <a href="https://sweetsworld.com.au/newcastle/pick-and-mix-lollies-australia/">Pick and Mix Lollies</a>.</em></p>

<div style="background:linear-gradient(135deg,#32455a 0%,#d16688 100%);padding:36px 22px;text-align:center;color:#fff;border-radius:8px;margin-top:32px">
<p style="color:#fff;margin:0 0 12px;font-size:26px;font-weight:700">Order Lotus Biscoff today</p>
<p style="max-width:580px;margin:0 auto 16px;color:#fff8fb">400g retail + 1.6kg bulk + Biscoff Vanilla. In-stock, ships same-day.</p>
<a href="#biscoff-shop" style="background:#5eb4d8;color:#fff;padding:11px 26px;border-radius:6px;text-decoration:none;font-weight:600;display:inline-block">Shop Now</a>
</div>"""

# ===================== EXECUTE =====================
plans = [
    {'pid':72480,'slug':'jaffas-lollies-australia','inner':JAFFAS_INNER,
     'wp_title':"Jaffas & Allen's Lollies Australia | Bulk 1kg Aussie Classics | SweetsWorld",
     'rm_title':"Jaffas Lollies Australia | Allen's Bulk 1kg Pack | SweetsWorld",
     'rm_desc':"Buy Allen's Jaffas and classic Aussie lollies online — Chico's, Killer Pythons, Red Frogs, Pineapples in 1kg bulk. Ships same-day Australia-wide from Newcastle.",
     'focus':'jaffas lollies australia'},
    {'pid':72482,'slug':'minties-australia','inner':MINTIES_INNER,
     'wp_title':"Minties Australia | Allen's Minties Bulk 1kg + Mint Lollies | SweetsWorld",
     'rm_title':"Minties Australia | Allen's Minties Bulk 1kg + Mint Lollies | SweetsWorld",
     'rm_desc':"Allen's Minties 1kg bulk + best Australian mint lollies (Mint Leaves, White Knights, Fry's Peppermint, Davies GF). Ships same-day from SweetsWorld Newcastle.",
     'focus':'minties'},
    {'pid':72452,'slug':'lotus-biscoff-australia','inner':BISCOFF_INNER,
     'wp_title':"Lotus Biscoff Australia | Spread 400g & 1.6kg Bulk | SweetsWorld",
     'rm_title':"Lotus Biscoff Australia | Spread 400g & 1.6kg Bulk | SweetsWorld",
     'rm_desc':"Buy Lotus Biscoff spread online in Australia — 400g retail & 1.6kg bulk cafe size. Belgian caramelised biscuit spread. Same-day dispatch from SweetsWorld Newcastle.",
     'focus':'lotus biscoff'},
]

for p in plans:
    pid = p['pid']
    # Backup
    data = wp_get(f'wp/v2/posts/{pid}', context='edit')
    (BK/f"{p['slug']}_post_{pid}_PRE.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))
    content = f"<!-- wp:html -->\n{p['inner']}\n<!-- /wp:html -->"
    old_len = len((data.get('content') or {}).get('raw','') or (data.get('content') or {}).get('rendered',''))
    print(f"\n▶ post #{pid} {p['slug']}: {old_len:,} → {len(content):,} chars")
    if DRY: continue
    r = safe_request('POST', f"{WP_BASE}/wp-json/wp/v2/posts/{pid}", json={'content': content, 'title': p['wp_title']})
    print(f"  Content: HTTP {r.status_code if r else 'FAIL'}")
    r2 = safe_request('GET', f"{WP_BASE}/wp-seo-meta.php",
                     params={'token':SEO_TOKEN,'post_id':pid,'keyword':p['focus'],'title':p['rm_title'],'description':p['rm_desc']}, auth=None)
    print(f"  RankMath: HTTP {r2.status_code if r2 else 'FAIL'}")
    time.sleep(2)
print("\nDone")
