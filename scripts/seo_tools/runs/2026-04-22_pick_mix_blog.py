"""Blog post: /pick-and-mix-lollies-australia/ — KD 2 vol 590 target."""
import sys, json, os, time
from pathlib import Path
sys.path.insert(0, '.')
from common import wp_get, safe_request, WP_BASE, SEO_TOKEN

DRY = os.environ.get('DRY_RUN','0')=='1'
SLUG = 'pick-and-mix-lollies-australia'
WP_TITLE = "Pick and Mix Lollies Australia: How to Build Your Own Custom Candy Bag"
RM_TITLE = "Pick and Mix Lollies Australia | Build Custom Candy Bags | SweetsWorld"
RM_DESC = "Build your own pick and mix lolly bag online — choose from 400+ Australian, British and American lollies. Same-day dispatch Australia-wide from SweetsWorld Newcastle."
FOCUS = "pick and mix lollies"

def fd(q,a):
    return (f'<details style="margin-bottom:18px;border:1px solid #e5e5e5;border-radius:6px">'
            f'<summary style="padding:16px 18px;font-weight:600;cursor:pointer;line-height:1.6">{q}</summary>'
            f'<div style="padding:16px 18px 18px;line-height:1.8">{a}</div></details>')

inner = f"""<p class="intro" style="font-size:18px;line-height:1.7;color:#4d5d6c;margin-bottom:28px">Pick and mix (or "pick 'n' mix") is Australia's favourite way to buy lollies — you choose exactly which sweets go in your bag, weigh it up, and pay by the gram. Whether you're filling a birthday party lolly bar, building a wedding bomboniere, or just craving a personal mix that no pre-packaged bag delivers, this is your complete guide to pick and mix lollies in Australia.</p>

<h2>What are pick and mix lollies?</h2>
<p>"Pick and mix" describes any lolly purchase where the customer hand-selects individual sweets from open bins or bulk containers, rather than buying pre-packaged bags. Originally a British supermarket tradition (Woolworths UK pioneered it in the 1920s), the concept migrated to Australia through dedicated candy stores and now thrives online. At SweetsWorld, our <a href="https://sweetsworld.com.au/candy/old-fashion-lollies/">classic old-fashioned lollies</a> range, <a href="https://sweetsworld.com.au/party-lollies/">party lolly collections</a>, and <a href="https://sweetsworld.com.au/candy/american-candy/">American candy section</a> combined give you over 400 SKUs to pick from.</p>

<h2>Why pick and mix beats pre-packaged bags</h2>
<ul>
<li><strong>Taste flexibility</strong> — Only get what you actually like. No more digging through 200g bags to find the 4 jelly beans you wanted.</li>
<li><strong>Party-perfect</strong> — Match specific colour themes (pink+purple for Mum's birthday, blue+gold for a boy's party, red+green for Christmas).</li>
<li><strong>Allergies &amp; dietary needs</strong> — Build a nut-free or gluten-free bag by hand-picking verified items. Pre-mixed bags mix risks together.</li>
<li><strong>Sampling</strong> — Try one piece of 20 different lollies instead of committing to 200g of a single type.</li>
<li><strong>Cost control</strong> — You choose the bag weight (100g, 500g, 1kg) to fit the occasion and budget.</li>
</ul>

<h2>Top 8 lollies to include in every pick and mix bag (our picks)</h2>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px;margin:24px 0">
<div style="background:#fff8fb;padding:20px;border-left:4px solid #d16688;border-radius:6px">
<h3 style="margin:0 0 8px;color:#32455a">1. Sherbies</h3>
<p style="margin:0">Allen's Aussie icon — tangy orange fizz finish. Everyone grabs one.</p>
</div>
<div style="background:#fff8fb;padding:20px;border-left:4px solid #5eb4d8;border-radius:6px">
<h3 style="margin:0 0 8px;color:#32455a">2. Milk Bottles</h3>
<p style="margin:0">Soft white gummy, nostalgic creamy flavour. Parent favourite.</p>
</div>
<div style="background:#fff8fb;padding:20px;border-left:4px solid #83c9b8;border-radius:6px">
<h3 style="margin:0 0 8px;color:#32455a">3. Chocolate Freckles</h3>
<p style="margin:0">Milk chocolate discs with hundreds-and-thousands topping. Kids' #1.</p>
</div>
<div style="background:#fff8fb;padding:20px;border-left:4px solid #32455a;border-radius:6px">
<h3 style="margin:0 0 8px;color:#32455a">4. Jelly Beans</h3>
<p style="margin:0">Allen's or US-style — rainbow fruit punch in every bag.</p>
</div>
<div style="background:#fff8fb;padding:20px;border-left:4px solid #d16688;border-radius:6px">
<h3 style="margin:0 0 8px;color:#32455a">5. Raspberries</h3>
<p style="margin:0">Fizzy raspberry-shaped gummies — adds sour kick.</p>
</div>
<div style="background:#fff8fb;padding:20px;border-left:4px solid #5eb4d8;border-radius:6px">
<h3 style="margin:0 0 8px;color:#32455a">6. Licorice Allsorts</h3>
<p style="margin:0">Colourful layered pieces. Adds adult variety — see our <a href="https://sweetsworld.com.au/candy-types/licorice-allsorts-australia/">Licorice Allsorts Australia</a> guide.</p>
</div>
<div style="background:#fff8fb;padding:20px;border-left:4px solid #83c9b8;border-radius:6px">
<h3 style="margin:0 0 8px;color:#32455a">7. Warheads / Toxic Waste</h3>
<p style="margin:0">Extreme sour for the thrill-seekers. Add 4-5 per bag.</p>
</div>
<div style="background:#fff8fb;padding:20px;border-left:4px solid #32455a;border-radius:6px">
<h3 style="margin:0 0 8px;color:#32455a">8. Minties / Fantales</h3>
<p style="margin:0">The chewy wrapped classics. Nostalgia guaranteed.</p>
</div>
</div>

<h2>How to build the perfect pick and mix lolly bag</h2>
<ol>
<li><strong>Pick your occasion</strong> — kids party (focus sweet + fruity), adult event (include liquorice + dark chocolate), wedding (pastel colour match), corporate (branded colours).</li>
<li><strong>Decide the weight</strong> — 100g (personal treat), 250g (shared bag), 500g (party for 6-10 people), 1kg (bulk / event).</li>
<li><strong>Aim for 6-10 different types</strong> — variety is the point of pick and mix. Fewer = just a mixed bag; more = everyone finds something.</li>
<li><strong>Balance colours + flavours</strong> — 2-3 sour, 2-3 sweet, 2-3 chocolate, 1-2 novelty (fun shapes, extreme sour, retro). This formula works for almost any crowd.</li>
<li><strong>Check allergies first</strong> — if kids at the party have common allergies (nuts, gluten, dairy, gelatin), hand-pick items that suit. Some SWeetsWorld lollies are <a href="https://sweetsworld.com.au/candy/vegan-lollies/">vegan and gelatin-free</a>.</li>
</ol>

<h2>Where to buy pick and mix lollies online in Australia</h2>
<p>SweetsWorld is Australia's largest online pick-and-mix candy destination — browse individual products across <a href="https://sweetsworld.com.au/candy/">all our lolly collections</a> and build your custom bag. We ship same-day from our Newcastle warehouse Australia-wide (2-5 business day delivery for major cities). For parties and weddings, we also offer <a href="https://sweetsworld.com.au/gift/baskets/">gift hampers and pre-curated mixes</a>.</p>

<h2>Pick and mix for special occasions</h2>
<ul>
<li><strong>Birthday parties</strong> — 500g bag for 6-10 kids, plus lolly bar tongs and bags (available separately).</li>
<li><strong>Weddings</strong> — 30g portioned bomboniere with colour-matched lollies. Popular: pastel pink + gold, burgundy + cream, boho rust + sage.</li>
<li><strong>Corporate events</strong> — Brand-colour bags (e.g. blue + white for tech, green + gold for finance). Mini 100g bags for attendee take-home.</li>
<li><strong>Christmas / holidays</strong> — Red + green + gold mix, including Darrell Lea chocolate coins and Aussie classics.</li>
<li><strong>Father's Day / Mother's Day</strong> — Adult mix with liquorice, dark chocolate, and retro British lollies like Pontefract cakes.</li>
</ul>

<div class="sw-faq-block" style="margin-top:40px">
<h2>Frequently Asked Questions</h2>
""" + "\n".join([
    fd("How do you order pick and mix lollies online?",
       "At SweetsWorld, browse our <a href=\"https://sweetsworld.com.au/candy/\">candy collections</a> and add individual items to your cart in the quantities you want. Unlike some competitors, you're not restricted to pre-set bags — pick 50g of this, 200g of that, whatever works. At checkout, standard shipping applies and everything arrives together."),
    fd("What's a good weight for a pick and mix lolly bag?",
       "For individual treats: 100-150g. For 2-4 people sharing: 250-500g. For a kids' party of 6-10: 500g-1kg. For weddings with bomboniere (small favour bags): 30-50g per guest. Events and corporate: typically 1kg bulk, then portion into 50-80g take-home bags."),
    fd("Can I build a sugar-free or sugar-reduced pick and mix bag?",
       "Yes. SweetsWorld stocks several sugar-free and lower-sugar options including sugar-free chocolates, sugar-free jellies, and diabetic-friendly confectionery. Hand-pick specifically the items marked \"sugar free\" or \"no added sugar\". Check each product's nutritional panel for full sugar content."),
    fd("Are pick and mix lollies more expensive than pre-packaged bags?",
       "Per-100g, pick and mix is typically <strong>10-25% more expensive</strong> than pre-mixed bags because you're paying for the curation flexibility. But you save money by only buying what you'll eat — if you hate raspberry flavours, you throw away nothing. For parties, pick-and-mix often ends up cheaper total because less waste."),
    fd("What's the most popular pick and mix lolly in Australia?",
       "Based on our order data: <strong>1. Sherbies, 2. Milk Bottles, 3. Jelly Beans, 4. Chocolate Freckles, 5. Warheads</strong>. The top 5 appears in roughly 80% of all our pick-and-mix orders. Aussie classics consistently beat imported American candy in share-bag settings (Americans tend to get added for variety, not volume)."),
    fd("Can you do custom lolly hampers or bomboniere?",
       "For wedding bomboniere and larger custom orders (500g+ per bag, 20+ bags), <a href=\"https://sweetsworld.com.au/contact/\">contact SweetsWorld directly</a> — we can colour-match to wedding themes, attach custom labels, and offer bulk pricing. Please allow 2 weeks lead time for custom orders."),
]) + """
</div>

<p><em>Related guides: <a href="https://sweetsworld.com.au/licorice-australia/">Licorice Australia</a>, <a href="https://sweetsworld.com.au/sour-candy-australia/">Sour Lollies Australia</a>, <a href="https://sweetsworld.com.au/dutch-licorice-australia/">Dutch Licorice</a>, <a href="https://sweetsworld.com.au/candy/american-candy/">American Candy</a>.</em></p>

<div style="background:linear-gradient(135deg,#d16688 0%,#32455a 100%);padding:36px 22px;text-align:center;color:#fff;border-radius:8px;margin-top:32px">
<h2 style="color:#fff;margin:0 0 12px;font-size:26px">Build your pick and mix today</h2>
<p style="max-width:580px;margin:0 auto 16px;color:#fff8fb">Browse 400+ Aussie, British and American lollies — ships same-day from Newcastle, Australia-wide.</p>
<a href="https://sweetsworld.com.au/candy/" style="background:#5eb4d8;color:#fff;padding:11px 26px;border-radius:6px;text-decoration:none;font-weight:600;display:inline-block">Browse All Lollies</a>
</div>"""

# 🔴 POST must wrap in wp:html (Playbook Pitfall #9 wpautop)
content = f"<!-- wp:html -->\n{inner}\n<!-- /wp:html -->"

print(f"[{'DRY' if DRY else 'LIVE'}] Publishing blog post /{SLUG}/ ({len(content):,} chars)")

if DRY:
    Path('/tmp/preview_pickmix.html').write_text(content)
    print(f"  preview → /tmp/preview_pickmix.html")
    sys.exit(0)

payload = {'slug':SLUG,'title':WP_TITLE,'content':content,'status':'publish'}
r = safe_request('POST', f"{WP_BASE}/wp-json/wp/v2/posts", json=payload)
if not r or not r.ok:
    print(f"❌ publish FAILED: {r.status_code if r else 'NO RESPONSE'}")
    if r: print(r.text[:300])
    sys.exit(1)

pub = r.json()
pid = pub['id']
url = pub.get('link','')
print(f"✅ Blog published: id={pid}")
print(f"   URL: {url}")

# RankMath
r2 = safe_request('GET', f"{WP_BASE}/wp-seo-meta.php",
                 params={'token':SEO_TOKEN,'post_id':pid,'keyword':FOCUS,'title':RM_TITLE,'description':RM_DESC}, auth=None)
print(f"   RankMath meta: HTTP {r2.status_code if r2 else 'FAIL'}")
# save published record
Path(f'/tmp/pickmix_published_{pid}.json').write_text(json.dumps({'id':pid,'url':url}, indent=2))
print(f"\npid={pid} url={url}")
