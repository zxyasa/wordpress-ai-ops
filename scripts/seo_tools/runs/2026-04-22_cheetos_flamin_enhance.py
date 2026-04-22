"""Stage 2-style enhancement for Cheetos Flamin Hot Limon 226.8g (pid 70038)."""
import sys, json, os
from pathlib import Path
sys.path.insert(0, '.')
from common import safe_request, WP_BASE, SEO_TOKEN

PID = 70038
DRY = os.environ.get('DRY_RUN','0')=='1'

def fd(q,a):
    return (f'<details style="margin-bottom:18px;border:1px solid #e5e5e5;border-radius:6px">'
            f'<summary style="padding:16px 18px;font-weight:600;cursor:pointer;line-height:1.6">{q}</summary>'
            f'<div style="padding:16px 18px 18px;line-height:1.8">{a}</div></details>')

desc = """<p><strong>Cheetos Flamin' Hot Limon 226.8g</strong> — one of the most sought-after imported American snacks in Australia. Intense Mexican-inspired chili heat meets zesty lime for a puckering, fiery flavour that's totally unlike anything on Australian supermarket shelves. Imported direct from the USA, in-stock and ready to ship from SweetsWorld Newcastle.</p>

<p>If you've searched for <a href="https://sweetsworld.com.au/candy/american-candy/">American Cheetos</a> in Australia, you'll know the Flamin' Hot Limon variant is one of the rarest — a step up from regular Flamin' Hot with a distinctive lime tang. The large 226.8g (8oz) bag is the authentic American size, perfect for sharing, gaming sessions, or party snack bowls.</p>

<h2 class="wp-block-heading">What makes Cheetos Flamin' Hot Limon different?</h2>
<p>Regular Flamin' Hot Cheetos bring a bold chili-cheese heat. The Limon variant adds a <strong>sharp, citrus-forward lime note</strong> that lifts the flavour and cuts through the richness. The result is a snack that's:</p>
<ul>
<li><strong>Hotter than regular Cheetos</strong> — rated around 7/10 on most personal heat scales</li>
<li><strong>Tangier than Flamin' Hot Crunchy</strong> — lime acid balances the chili</li>
<li><strong>Addictively moreish</strong> — the salt-spice-sour combo triggers classic "one more handful" cravings</li>
<li><strong>Vegetarian-friendly</strong> — no animal-derived ingredients in the standard recipe (check current pack)</li>
</ul>

<h2 class="wp-block-heading">Why buy Cheetos Flamin' Hot Limon from SweetsWorld?</h2>
<ul>
<li><strong>Authentic American import</strong> — direct from USA supplier, not a regional reformulation</li>
<li><strong>Full 226.8g bag</strong> — the genuine 8oz American size (Australian supermarket varieties, when you can find them, are typically 170g or less)</li>
<li><strong>Same-day dispatch</strong> from our Newcastle NSW warehouse, Australia-wide delivery</li>
<li><strong>In stock now</strong> — Flamin' Hot Limon supply is intermittent globally, so order while available</li>
<li><strong>Bulk-friendly pricing</strong> — buy multiples for parties, gaming LANs, or to stockpile</li>
</ul>

<h2 class="wp-block-heading">Perfect for:</h2>
<ul>
<li>🎮 Gaming marathons — the salt-spice keeps you alert</li>
<li>🎉 Party snack bowls (alongside regular Cheetos and Takis)</li>
<li>🎁 Gift for friends who love spicy American snacks</li>
<li>📺 Movie nights — pairs perfectly with cold drinks (especially lime sodas)</li>
<li>🌶️ Spice challenges — a good "tier 2" spicy chip before moving up to Takis Blue Heat</li>
</ul>

<div class="sw-faq-block" style="margin-top:30px">
<h2 class="wp-block-heading">Frequently Asked Questions</h2>
""" + "\n".join([
    fd("How spicy are Cheetos Flamin' Hot Limon compared to regular Flamin' Hot?",
       "Flamin' Hot Limon is <strong>slightly hotter</strong> than regular Flamin' Hot Cheetos because the lime acid amplifies the chili sensation on your tongue. On a personal heat scale most rate Flamin' Hot at 6/10 and Limon at 7/10. Both are significantly hotter than regular Cheetos but less extreme than <a href=\"https://sweetsworld.com.au/takis-australia/\">Takis Fuego</a> or Takis Blue Heat."),
    fd("Where to buy Cheetos Flamin' Hot Limon in Australia?",
       "SweetsWorld ships Cheetos Flamin' Hot Limon Australia-wide from our Newcastle warehouse. Import supply is intermittent globally, so we recommend buying while in stock. Sydney, Melbourne, Brisbane, Perth and Adelaide orders typically arrive within 2-5 business days."),
    fd("Are Flamin' Hot Limon vegan or vegetarian?",
       "Cheetos Flamin' Hot Limon is typically labelled <strong>vegetarian</strong> — the cheesy flavour is created with plant-based ingredients and dairy-derived seasonings. Check the current pack for the definitive ingredients list, as formulations vary slightly by production country. It is <strong>not</strong> vegan due to the milk-based cheese flavouring."),
    fd("How big is the 226.8g bag?",
       "226.8g is the authentic American 8-ounce size — significantly larger than the 170g or smaller bags sometimes found in Australian supermarket specialty aisles. Contains roughly 7 servings at the 28g serving size listed on the Nutrition Facts panel. Great for sharing or stockpiling."),
    fd("Are Flamin' Hot Limon gluten free?",
       "Cheetos Flamin' Hot Limon is <strong>not certified gluten free</strong>. Standard formulations use cornmeal (naturally gluten-free) but the seasoning mix and production environment may include gluten-containing ingredients. If you have coeliac disease, always verify the current pack label."),
    fd("What other spicy American snacks pair well with Flamin' Hot Limon?",
       "For a spice-crawl snack bowl: combine Flamin' Hot Limon with <a href=\"https://sweetsworld.com.au/takis-australia/\">Takis Fuego</a> (extreme heat), regular Cheetos Crunchy (mild), <a href=\"https://sweetsworld.com.au/candy/american-candy/\">Doritos Flamin' Hot</a> when in stock, and something sweet like <a href=\"https://sweetsworld.com.au/sour-candy-australia/\">Warheads sour candy</a> to cleanse the palate between heats."),
]) + """
</div>

<p><em>Explore more: <a href="https://sweetsworld.com.au/takis-australia/">Takis Australia</a>, <a href="https://sweetsworld.com.au/candy/american-candy/">American Candy collection</a>, <a href="https://sweetsworld.com.au/american-food-australia/">American Food Australia hub</a>.</em></p>"""

print(f"[{'DRY' if DRY else 'LIVE'}] Cheetos Flamin Hot Limon enhance: 0 → {len(desc):,} chars")

if DRY:
    Path('/tmp/preview_cheetos.html').write_text(desc)
    print("Preview → /tmp/preview_cheetos.html")
    sys.exit(0)

r = safe_request('POST', f"{WP_BASE}/wp-json/wc/v3/products/{PID}", json={'description': desc})
print(f"Description: HTTP {r.status_code if r else 'FAIL'}")

RM_TITLE = "Cheetos Flamin' Hot Limon 226.8g Australia | Import American Snack | SweetsWorld"
RM_DESC = "Buy authentic American Cheetos Flamin' Hot Limon 226.8g in Australia — imported direct from USA. Zesty lime + chili heat. Same-day dispatch from SweetsWorld Newcastle."
r2 = safe_request('GET', f"{WP_BASE}/wp-seo-meta.php",
                 params={'token':SEO_TOKEN,'post_id':PID,'keyword':'cheetos flamin hot limon',
                         'title':RM_TITLE,'description':RM_DESC}, auth=None)
print(f"RankMath: HTTP {r2.status_code if r2 else 'FAIL'}")
