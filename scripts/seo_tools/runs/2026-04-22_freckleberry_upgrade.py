"""Upgrade post 72456 /candy-types/freckleberry-australia/ → personalized chocolate gift hub."""
import sys, json, os
from pathlib import Path
sys.path.insert(0, '.')
from common import wp_get, safe_request, WP_BASE, SEO_TOKEN

PID = 72456
DRY = os.environ.get('DRY_RUN','0')=='1'

TS = "20260422_132000"
BK = Path(f"backups/freckleberry_upgrade_{TS}")
BK.mkdir(parents=True, exist_ok=True)
data = wp_get(f'wp/v2/posts/{PID}', context='edit')
(BK/f"freckleberry-australia_post_{PID}_PRE.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))
print("✅ Backup saved")

# Heart + Love + sample letters A,M,S + sample numbers 1-5 + more letters
PRODUCTS = [13376, 13378, 14553, 19737, 19753, 19755, 19777, 19739, 19743, 19757, 19767, 19769]
PRODUCTS_STR = ','.join(str(x) for x in PRODUCTS)

def fd(q,a):
    return (f'<details style="margin-bottom:18px;border:1px solid #e5e5e5;border-radius:6px">'
            f'<summary style="padding:16px 18px;font-weight:600;cursor:pointer;line-height:1.6">{q}</summary>'
            f'<div style="padding:16px 18px 18px;line-height:1.8">{a}</div></details>')

inner = f"""<div style="background:linear-gradient(135deg,#d16688 0%,#5eb4d8 100%);padding:52px 28px;text-align:center;color:#fff;margin-bottom:28px;border-radius:8px">
<p style="font-size:40px;margin:0 0 12px;color:#fff;font-weight:700;line-height:1.1">Freckleberry Australia</p>
<p style="font-size:18px;max-width:720px;margin:0 auto 18px;line-height:1.6;color:#fff8fb">Personalised Australian chocolate letters, numbers, hearts &amp; loves — the original milk chocolate Freckle with hundreds &amp; thousands topping. Perfect for birthdays, weddings, baby names and spelled-out gifts. Ships same-day from SweetsWorld Newcastle.</p>
<a href="#freckleberry-shop" style="background:#32455a;color:#fff;padding:12px 28px;border-radius:6px;text-decoration:none;font-weight:600;display:inline-block">Shop Freckleberry</a>
</div>

<h2 class="wp-block-heading">What is Freckleberry?</h2>
<p><strong>Freckleberry</strong> is an Australian chocolatier founded on one charming idea: the classic <em>chocolate freckle</em> (milk chocolate disc topped with hundreds and thousands), reimagined as <strong>any letter of the alphabet, any number 0-9, plus hearts and "love" shapes</strong>. Originally inspired by the Australian childhood freckle lolly, Freckleberry turns nostalgic chocolate into personalised gifts that spell names, dates, ages, or affectionate messages.</p>

<p>Each piece is a premium <strong>40g milk chocolate shape</strong> topped with coloured rainbow sprinkles ("hundreds and thousands" / "nonpareils") in the signature Freckleberry multicolour pattern. They're <strong>individually wrapped</strong> in clear cello so each one can be gifted separately or combined.</p>

<h2 class="wp-block-heading">Who buys Freckleberry? (real use cases)</h2>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:18px;margin:26px 0">
<div style="background:#fff8fb;padding:22px;border-left:4px solid #d16688;border-radius:6px">
<h3 style="margin:0 0 10px;color:#32455a">🎂 Birthday Spell-Outs</h3>
<p style="margin:0">Spell the name + age with letters + numbers. Kids 4-10 adore unwrapping their own name.</p>
</div>
<div style="background:#fff8fb;padding:22px;border-left:4px solid #5eb4d8;border-radius:6px">
<h3 style="margin:0 0 10px;color:#32455a">💍 Wedding Bomboniere</h3>
<p style="margin:0">Couple initials + "LOVE" + heart combo on each guest's place setting. Cost-effective favour.</p>
</div>
<div style="background:#fff8fb;padding:22px;border-left:4px solid #83c9b8;border-radius:6px">
<h3 style="margin:0 0 10px;color:#32455a">👶 Baby Announcements</h3>
<p style="margin:0">Spell the newborn's name + birth date for grandparents and the nursery.</p>
</div>
<div style="background:#fff8fb;padding:22px;border-left:4px solid #32455a;border-radius:6px">
<h3 style="margin:0 0 10px;color:#32455a">💼 Corporate Gifts</h3>
<p style="margin:0">Company initials or spell-out on each client's gift box. Custom branding, no setup fees.</p>
</div>
<div style="background:#fff8fb;padding:22px;border-left:4px solid #d16688;border-radius:6px">
<h3 style="margin:0 0 10px;color:#32455a">❤️ Valentine's Day</h3>
<p style="margin:0">Heart 40g + Love 60g + partner's initial = personal Valentine's without the generic heart-shaped box.</p>
</div>
<div style="background:#fff8fb;padding:22px;border-left:4px solid #5eb4d8;border-radius:6px">
<h3 style="margin:0 0 10px;color:#32455a">🎓 Graduation / Milestones</h3>
<p style="margin:0">"GRAD 2026" or "25" (for a 25th) — chocolate markers for life celebrations.</p>
</div>
</div>

<h2 class="wp-block-heading" id="freckleberry-shop">Shop Freckleberry online</h2>
<p>We stock the full A-Z alphabet + 0-9 numbers + Heart &amp; Love shapes. All 38+ varieties are 40g milk chocolate with rainbow sprinkles, individually wrapped. Same-day dispatch from Newcastle Australia-wide.</p>

[products ids="{PRODUCTS_STR}" columns="4"]

<p style="text-align:center;margin:18px 0"><em>Looking for a specific letter, number or combination? <a href="https://sweetsworld.com.au/search?q=freckleberry">Search all Freckleberry items</a> or contact us for bulk orders.</em></p>

<h2 class="wp-block-heading">How to spell a name with Freckleberry</h2>
<ol>
<li><strong>Work out the letters + numbers needed</strong> — e.g. "MIA 5" = M + I + A + (space) + 5 = 4 pieces</li>
<li><strong>Order each letter/number individually</strong> — each 40g piece is sold separately (hearts and loves slightly larger)</li>
<li><strong>For longer spell-outs</strong>, we recommend ordering 2-3 days before you need it for delivery time</li>
<li><strong>Arrange on the gift plate/table</strong> — they sit naturally due to flat back. Some customers use a gift box lined with tissue paper</li>
<li><strong>Tip:</strong> Add a Heart or Love piece as "punctuation" between sections (e.g. "MIA ❤ 5")</li>
</ol>

<h2 class="wp-block-heading">Freckleberry chocolate quality</h2>
<p>Freckleberry uses premium Australian milk chocolate (roughly 30-33% cocoa, smooth creamy profile — closer to Cadbury than European dark chocolate). The hundreds and thousands are food-grade sugar beads in non-bleeding colours. Each 40g piece is handmade in small batches in Australia, then individually wrapped for freshness. <strong>Best before</strong>: 8-10 months from production date. <strong>Store</strong>: cool dry place, below 22°C.</p>

<div class="sw-faq-block" style="margin-top:40px">
<h2 class="wp-block-heading">Frequently Asked Questions</h2>
""" + "\n".join([
    fd("Where to buy Freckleberry chocolate in Australia?",
       "SweetsWorld stocks the full Freckleberry A-Z alphabet, 0-9 numbers, and Heart &amp; Love shapes — ships same-day from Newcastle Australia-wide. Supermarkets carry limited Freckleberry range (usually just hearts at Valentine's), so online specialty retailers are your best bet for the full personalisation range."),
    fd("Are Freckleberry chocolates gluten free?",
       "Most Freckleberry products are labelled <strong>gluten free</strong>, using Australian milk chocolate and gluten-free sprinkles. However they are produced in a shared facility, so may not be suitable for severe coeliac disease. Always verify the current individual product pack label."),
    fd("How do I order a name or word made from Freckleberry letters?",
       "Work out the letters/numbers you need (e.g. \"EMMA 6\" = 5 items), order each individually via the product page, and we'll ship everything together. For longer spell-outs (6+ letters) contact us before ordering so we can reserve stock — individual letters can go out of stock quickly during peak seasons."),
    fd("How big is each Freckleberry letter/number?",
       "Standard letters and numbers are <strong>40g each</strong>, approximately 6-7 cm wide. Hearts are also ~40g at 7cm. The Love 60g is slightly larger at 7-8 cm with more chocolate volume. Each is thick enough to feel substantial when held — not a wafer-thin novelty."),
    fd("Can I get custom Freckleberry colours or prints for corporate orders?",
       "Standard Freckleberry pieces use the signature multicolour rainbow sprinkles (not customisable per-piece). For corporate orders 50+ pieces, the manufacturer can occasionally accommodate single-colour sprinkles (e.g. red+white for Christmas, blue+white for company branding) — contact SweetsWorld and we can enquire on your behalf. Standard 4-week lead time applies."),
    fd("Do Freckleberry chocolates melt in Australian summer?",
       "Yes — like all milk chocolate, Freckleberry melts above 32-35°C. In QLD summer, we recommend <strong>Express Shipping</strong> with a note to the courier, and we include ice packs in orders placed between December and March. Never leave chocolate gifts in a car or direct sunlight during transport."),
    fd("What's the difference between Freckleberry and regular chocolate freckles?",
       "Regular Australian chocolate freckles are small round discs (2-3cm). <strong>Freckleberry</strong> is the premium Australian brand that reimagines freckles as <strong>personalised shapes</strong> (letters A-Z, numbers 0-9, hearts, love). Same general flavour profile (milk chocolate + hundreds-and-thousands), but made for gifting rather than pick-and-mix snacking."),
]) + """
</div>

<p><em>Related: <a href="https://sweetsworld.com.au/gift/baskets/">Chocolate gift baskets</a>, <a href="https://sweetsworld.com.au/candy-types/jaffas-lollies-australia/">Allen's Lollies Australia</a>, <a href="https://sweetsworld.com.au/candy/old-fashion-lollies/">Old-fashioned Australian lollies</a>, <a href="https://sweetsworld.com.au/newcastle/pick-and-mix-lollies-australia/">Pick and Mix Lollies guide</a>.</em></p>

<div style="background:linear-gradient(135deg,#5eb4d8 0%,#d16688 100%);padding:36px 22px;text-align:center;color:#fff;border-radius:8px;margin-top:32px">
<p style="color:#fff;margin:0 0 12px;font-size:26px;font-weight:700">Spell a name in chocolate today</p>
<p style="max-width:580px;margin:0 auto 16px;color:#fff8fb">Full A-Z + 0-9 + Heart &amp; Love — 38+ Freckleberry pieces in stock. Same-day dispatch from SweetsWorld Newcastle.</p>
<a href="#freckleberry-shop" style="background:#32455a;color:#fff;padding:11px 26px;border-radius:6px;text-decoration:none;font-weight:600;display:inline-block">Shop Now</a>
</div>"""

content = f"<!-- wp:html -->\n{inner}\n<!-- /wp:html -->"
old_len = len((data.get('content') or {}).get('raw','') or (data.get('content') or {}).get('rendered',''))
print(f"[{'DRY' if DRY else 'LIVE'}] Upgrade post {PID}: {old_len:,} → {len(content):,} chars")

WP_TITLE = "Freckleberry Australia | Personalised Letter & Number Chocolates | SweetsWorld"
RM_TITLE = "Freckleberry Australia | A-Z Letters, 0-9 Numbers, Hearts &amp; Loves | SweetsWorld"
RM_DESC = "Buy Freckleberry chocolate letters, numbers, hearts and loves online in Australia — personalised for birthdays, weddings, baby names, corporate gifts. Same-day dispatch from SweetsWorld Newcastle."
FOCUS = "freckleberry"

if DRY:
    Path('/tmp/preview_freckleberry.html').write_text(content)
    print("Preview → /tmp/preview_freckleberry.html")
    sys.exit(0)

r = safe_request('POST', f"{WP_BASE}/wp-json/wp/v2/posts/{PID}",
                json={'content': content, 'title': WP_TITLE})
print(f"Content: HTTP {r.status_code if r else 'FAIL'}")
r2 = safe_request('GET', f"{WP_BASE}/wp-seo-meta.php",
                 params={'token':SEO_TOKEN,'post_id':PID,'keyword':FOCUS,'title':RM_TITLE,'description':RM_DESC}, auth=None)
print(f"RankMath: HTTP {r2.status_code if r2 else 'FAIL'}")
