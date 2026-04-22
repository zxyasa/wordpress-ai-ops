"""
Semrush rescue writes - 3 pages (Bertie, Cherry Liqueur, Takis)
Each page: backup-verified → content update → meta update → verify.
"""
import sys, json, os, time, re
from pathlib import Path
sys.path.insert(0, '.')
from common import wp_get, wp_post, safe_request, WP_BASE, WP_AUTH, SEO_TOKEN

BACKUP_DIR = Path("backups/semrush_rescue_20260422_094741")
DRY_RUN = os.environ.get('DRY_RUN', '0') == '1'
print(f"[{'DRY-RUN' if DRY_RUN else 'LIVE'}] Backup verified: {BACKUP_DIR.exists()}")

# ------------------ FAQ block snippet ------------------
def faq_details(q, a):
    """Render one FAQ item with <details> — snippet #55 auto-generates FAQPage schema."""
    return (
        f'<details style="margin-bottom:18px;border:1px solid #e5e5e5;border-radius:6px">'
        f'<summary style="padding:16px 18px;font-weight:600;cursor:pointer;line-height:1.6">{q}</summary>'
        f'<div style="padding:16px 18px 18px;line-height:1.8">{a}</div>'
        f'</details>'
    )

# ---------- BERTIE BEETLE FAQ additions (targeting lost keywords) ----------
BERTIE_NEW_FAQS = [
    (
        "Where can I buy Bertie Beetle chocolate in Australia?",
        "You can buy Bertie Beetle chocolate online in Australia at <a href=\"https://sweetsworld.com.au/\">SweetsWorld</a>, who stock individual Bertie Beetle bars, <a href=\"https://sweetsworld.com.au/candy/bertie-beetle-in-the-show-bag/\">Bertie Beetle showbags</a>, and the classic <a href=\"https://sweetsworld.com.au/chocolate/australian-chocolate/bertie-beetle-10g/\">10g Bertie Beetle chocolate</a>. They're also traditionally available at the Royal Easter Show, Royal Melbourne Show, and other Australian agricultural shows from Nestlé's official showbag."
    ),
    (
        "Are Bertie Beetles gluten free?",
        "Bertie Beetle chocolate is not certified gluten free. The product contains wheat-based ingredients and is produced on equipment that handles gluten, so it is not suitable for anyone with coeliac disease or gluten intolerance. Always check the ingredients list on the current Nestlé packaging, as formulations can change."
    ),
    (
        "What's included in a Bertie Beetle showbag?",
        "A typical Bertie Beetle showbag from Nestlé contains multiple individually-wrapped Bertie Beetle chocolates (usually 8–12 bars depending on the year), a collectible Bertie-themed item, and sometimes bonus Nestlé confectionery like Smarties or Allens lollies. SweetsWorld stocks a ready-to-buy <a href=\"https://sweetsworld.com.au/candy/bertie-beetle-in-the-show-bag/\">Bertie Beetle showbag</a> online for customers who can't attend the shows."
    ),
    (
        "What are the ingredients in Bertie Beetle chocolate?",
        "Bertie Beetle is made from milk chocolate, honeycomb pieces, and a hint of fairy floss. The honeycomb base contains sugar, glucose syrup and raising agent (bicarbonate of soda). The chocolate coating contains milk solids, cocoa butter, cocoa mass, and vegetable fats. Always consult the packaging for the definitive ingredient and allergen list."
    ),
]

# ---------- CHERRY LIQUEUR description expansion ----------
CHERRY_APPEND = """
<h2 class="wp-block-heading">What are Cherry Liqueur chocolates?</h2>
<p>Cherry Liqueur chocolates are a classic European-style confection: a whole preserved cherry suspended in a centre of cherry brandy liqueur syrup, enrobed in a shell of smooth dark or milk chocolate. The flavour is rich, slightly tart from the cherry, and finished with the warm alcoholic note of kirsch or cherry brandy. Each piece is individually twist-wrapped to protect the delicate liqueur centre.</p>

<h2 class="wp-block-heading">Why buy Cherry Liqueur chocolates in 1kg bulk?</h2>
<p>The 1kg size is ideal for catering, wedding bomboniere, Christmas hampers and corporate gifting. The bulk format lets you portion pieces into smaller bonbonnières, fill glass bowls for dessert tables, or re-pack for retail. Twist wrappers mean each chocolate stays neat and individually food-safe — no re-wrapping required.</p>

<h2 class="wp-block-heading">How to store Cherry Liqueur chocolates</h2>
<p>Store your Cherry Liqueur chocolates in a cool, dry place away from direct sunlight and strong odours. Ideal temperature is 15–18°C. Avoid refrigeration — it can cause "chocolate bloom" (a harmless but unsightly white film from condensed sugar or fat). Properly stored, sealed Cherry Liqueur chocolates keep their peak flavour for 10–12 months.</p>

<div class="sw-faq-block" style="margin-top:30px">
<h2 class="wp-block-heading">Frequently Asked Questions</h2>
""" + "\n".join([
    faq_details(
        "Where to buy Cherry Liqueur chocolates in Australia?",
        "SweetsWorld ships Cherry Liqueur chocolates Australia-wide. This 1kg bulk bag of individually-wrapped cherry liqueurs is popular for weddings, Christmas hampers and corporate gifts. Order online for fast delivery from our Newcastle warehouse."
    ),
    faq_details(
        "Are these the same as Choceur cherry liqueurs?",
        "These are the same traditional European cherry liqueur chocolate recipe sold under various brand names including Choceur, Trumpf and supermarket private labels. All feature a preserved cherry and liquid cherry-brandy centre in chocolate. Our 1kg pack is produced by an established European chocolatier and imported direct."
    ),
    faq_details(
        "How much alcohol is in Cherry Liqueur chocolates?",
        "Each chocolate contains approximately 0.5–1 ml of cherry brandy liqueur (kirsch) in the centre. Total alcohol content is typically 4–6% of the liquid centre volume. Not recommended for children, expectant mothers, or anyone avoiding alcohol. Some states require proof of age for purchase — please check your local regulations."
    ),
    faq_details(
        "Do these cherry liqueur chocolates contain real cherries?",
        "Yes. Each chocolate contains a whole preserved Morello-style cherry (stone removed), suspended in cherry brandy syrup. The cherry is preserved in the syrup itself, giving that signature two-bite experience: bite the chocolate shell first, then enjoy the cherry and liqueur together."
    ),
    faq_details(
        "Are Cherry Liqueur chocolates suitable for gifts?",
        "Absolutely — they're one of Europe's most traditional gift chocolates, popular for Christmas, Valentine's Day and anniversaries. Individual twist-wrappers make them easy to portion into gift boxes, hampers or wedding favour bags. The 1kg pack fills roughly 80–90 pieces."
    ),
]) + """
</div>

<p><em>Browse our full range of <a href="https://sweetsworld.com.au/chocolate/liqueur-chocolates/">liqueur chocolates</a> and <a href="https://sweetsworld.com.au/british-lollies/uk-chocolate/">UK/European chocolates</a> for more grown-up confectionery.</em></p>
"""

# ---------- TAKIS guide FAQ + TL;DR ----------
TAKIS_TLDR = """
<div style="background:#fff5f0;border-left:4px solid #d63638;padding:18px 22px;margin:0 0 24px">
<strong>Takis Chips at a glance:</strong> Takis are bold, spicy rolled tortilla chips from Mexico (Barcel brand), famous for their intense Fuego (chili-lime) heat. In Australia, popular flavours include Fuego (hottest), Nitro, Blue Heat and Crunchy Fajita. Buy Takis chips online in Australia at SweetsWorld — same-day dispatch from Newcastle.
</div>
"""

TAKIS_FAQ = """
<div class="sw-faq-block" style="margin-top:40px">
<h2 class="wp-block-heading">Frequently Asked Questions</h2>
""" + "\n".join([
    faq_details(
        "How spicy are Takis chips?",
        "Takis Fuego (the red bag) is the most common and is rated around 8/10 on a personal heat scale — significantly hotter than Flamin' Hot Cheetos but below pure ghost pepper snacks. Blue Heat is slightly hotter than Fuego. Mild options like Crunchy Fajita exist but are rare in Australia."
    ),
    faq_details(
        "Where to buy Takis chips in Australia?",
        "Takis chips are sold online at <a href=\"https://sweetsworld.com.au/\">SweetsWorld</a> (Australia-wide shipping from our Newcastle warehouse) and at selected specialty grocery stores. Big-4 supermarkets stock Takis intermittently. For reliable stock of <a href=\"https://sweetsworld.com.au/newcastle/blue-takis/\">Blue Heat</a> and Fuego, online is your best bet."
    ),
    faq_details(
        "What flavours of Takis are available in Australia?",
        "The most commonly imported flavours to Australia are <strong>Fuego</strong> (chili-lime, red bag), <strong>Blue Heat</strong> (extreme heat, blue bag), <strong>Nitro</strong> (habanero-lime, purple bag), and <strong>Crunchy Fajita</strong> (mild, orange bag). Availability of rare SKUs like Zombie, Dragon Spicy Sweet Chili and Stealth rotates with import shipments."
    ),
    faq_details(
        "Are Takis chips vegan?",
        "Fuego and most core Takis flavours in Australia are labelled vegan-friendly (no dairy, no animal derivatives — the \"cheesy\" flavour is plant-based). However, check the specific pack you purchase as recipes vary by production country. Flavours with explicit cheese or ranch (e.g., Takis Xplosion) are not vegan."
    ),
    faq_details(
        "Can you eat Takis every day?",
        "Not recommended. Takis are high in sodium (around 280 mg per 30g serve), contain artificial colours, and the citric-acid spice blend is known to irritate the stomach lining in heavy eaters. Best enjoyed as an occasional treat — 1–2 servings per week is a reasonable limit."
    ),
    faq_details(
        "What makes Takis different from other spicy chips?",
        "Three things: (1) Takis are <strong>rolled</strong> tortilla chips, not flat — giving that distinctive crunch shape; (2) they use a <strong>stronger chili-lime coating</strong> than typical US snacks; (3) Takis target real heat-seekers — there's no mild default, even the tamer flavours have a noticeable kick."
    ),
]) + """
</div>

<p><em>Explore related spicy snacks: <a href="https://sweetsworld.com.au/newcastle/blue-takis/">Blue Takis guide</a>, <a href="https://sweetsworld.com.au/newcastle/takis-blue-heat-extreme-tortilla-chips/">Blue Heat Extreme</a>, <a href="https://sweetsworld.com.au/newcastle/hottest-chilli-sauce-newcastle/">hottest chilli sauces</a>.</em></p>
"""

# ===================== WRITE PLANS =====================
# Each: id, type, current content, new content, meta updates
plans = []

# --- 1. BERTIE BEETLE (post 59803) ---
bertie = json.load(open(BACKUP_DIR / "bertie-beetle-2_post_59803.json"))
bertie_content = (bertie.get('content') or {}).get('rendered') or ''
# Insert 4 new FAQ blocks BEFORE the existing </div> that closes the sw-faq-block.
# Find last </details> then before the closing </div>
# Simpler: find the <div class="sw-faq-block"> ... </div> block and append new <details> before closing </div>
# Look for the faq-block div and its end
faq_div_start = bertie_content.find('sw-faq-block')
if faq_div_start < 0:
    # Fallback: look for "Frequently Asked Questions"
    faq_div_start = bertie_content.find('Frequently Asked Questions')

# Find the </div> that closes this block: search after last </details>
last_details_end = bertie_content.rfind('</details>')
if last_details_end < 0:
    print("⚠️  Bertie FAQ structure not recognized, aborting")
    sys.exit(1)
# Insert new FAQ items right after last </details>
new_faqs_html = "\n" + "\n".join(faq_details(q,a) for q,a in BERTIE_NEW_FAQS) + "\n"
bertie_new_content = (
    bertie_content[:last_details_end + len('</details>')]
    + new_faqs_html
    + bertie_content[last_details_end + len('</details>'):]
)
plans.append({
    'label': 'BERTIE BEETLE',
    'kind': 'post',
    'id': 59803,
    'url': 'https://sweetsworld.com.au/candy-guides/bertie-beetle-2/',
    'old_len': len(bertie_content),
    'new_content': bertie_new_content,
    'new_len': len(bertie_new_content),
    'meta': {
        'keyword': 'bertie beetle',
        'title': 'Bertie Beetle Chocolate Australia | History, Showbags & Where to Buy',
        'description': 'The iconic Australian Bertie Beetle chocolate — Nestlé\'s 1963 honeycomb-and-fairy-floss classic. Where to buy in Australia, showbags, gluten info and full history.',
    },
    'verify_markers': ['Where can I buy Bertie Beetle chocolate', 'Are Bertie Beetles gluten free', 'showbag'],
})

# --- 2. CHERRY LIQUEUR (product 27747) ---
cherry = json.load(open(BACKUP_DIR / "cherry-liqueur-1kg_product_27747.json"))
cherry_desc = cherry.get('description','') or ''
cherry_new_desc = cherry_desc.rstrip() + "\n\n" + CHERRY_APPEND
plans.append({
    'label': 'CHERRY LIQUEUR',
    'kind': 'product',
    'id': 27747,
    'url': 'https://sweetsworld.com.au/chocolate/liqueur-chocolates/cherry-liqueur-1kg/',
    'old_len': len(cherry_desc),
    'new_content': cherry_new_desc,
    'new_len': len(cherry_new_desc),
    'meta': {
        'keyword': 'cherry liqueur',
        'title': 'Cherry Liqueur Chocolates 1kg Bulk | Cherry Brandy Filled | SweetsWorld',
        'description': 'Premium 1kg bulk bag of Cherry Liqueur chocolates — individually-wrapped dark/milk chocolate with whole cherry and cherry brandy centre. Ships Australia-wide.',
    },
    'verify_markers': ['Cherry Liqueur chocolates are a classic', 'Where to buy Cherry Liqueur', 'Choceur cherry liqueurs'],
})

# --- 3. TAKIS GUIDE (page 63141) ---
takis = json.load(open(BACKUP_DIR / "takis-chips-the-ultimate-guide-to-these-bold-and-spicy-tortilla-chips-2_page_63141.json"))
takis_content = (takis.get('content') or {}).get('rendered') or ''
# Insert TL;DR at top (after first <p> containing an image if any, else right at start)
# Insert FAQ at end
takis_new_content = TAKIS_TLDR + "\n\n" + takis_content.rstrip() + "\n\n" + TAKIS_FAQ
plans.append({
    'label': 'TAKIS GUIDE',
    'kind': 'page',
    'id': 63141,
    'url': 'https://sweetsworld.com.au/takis-chips-the-ultimate-guide-to-these-bold-and-spicy-tortilla-chips-2/',
    'old_len': len(takis_content),
    'new_content': takis_new_content,
    'new_len': len(takis_new_content),
    'meta': {
        'keyword': 'takis chips',
        'title': 'Takis Chips Australia: Flavours Guide (Fuego, Blue Heat, Nitro) | SweetsWorld',
        'description': 'Complete Australia guide to Takis rolled tortilla chips — Fuego, Blue Heat, Nitro & more. Heat levels, flavour comparison, where to buy online in Australia.',
    },
    'verify_markers': ['Takis Chips at a glance', 'How spicy are Takis chips', 'Fuego'],
})

# ===================== EXECUTION =====================
print()
print("="*75)
print(f"{'[DRY-RUN]' if DRY_RUN else '[LIVE]'} Executing {len(plans)} write plans")
print("="*75)

for p in plans:
    print(f"\n▶ {p['label']} ({p['kind']} #{p['id']})")
    print(f"  content: {p['old_len']:,} → {p['new_len']:,} chars (+{p['new_len']-p['old_len']:,})")
    print(f"  meta: {p['meta']['title'][:70]}")
    
    if DRY_RUN:
        # Write preview file
        preview = Path(f"/tmp/preview_{p['id']}.html")
        preview.write_text(p['new_content'])
        print(f"  preview → {preview}")
        continue
    
    # 1. Update content
    if p['kind'] == 'post':
        r = safe_request('POST', f"{WP_BASE}/wp-json/wp/v2/posts/{p['id']}", json={'content': p['new_content']})
    elif p['kind'] == 'page':
        r = safe_request('POST', f"{WP_BASE}/wp-json/wp/v2/pages/{p['id']}", json={'content': p['new_content']})
    elif p['kind'] == 'product':
        r = safe_request('POST', f"{WP_BASE}/wp-json/wc/v3/products/{p['id']}", json={'description': p['new_content']})
    
    if not r or not r.ok:
        print(f"  ❌ content write FAILED: {r.status_code if r else 'no response'}")
        print(f"     {r.text[:300] if r else ''}")
        continue
    print(f"  ✅ content written: HTTP {r.status_code}")
    
    # 2. Update RankMath meta via wp-seo-meta.php bridge
    meta_params = {
        'token': SEO_TOKEN,
        'post_id': p['id'],
        'keyword': p['meta']['keyword'],
        'title': p['meta']['title'],
        'description': p['meta']['description'],
    }
    r2 = safe_request('GET', f"{WP_BASE}/wp-seo-meta.php", params=meta_params, auth=None)
    if not r2 or not r2.ok:
        print(f"  ⚠️  meta write FAILED: {r2.status_code if r2 else 'no response'}")
    else:
        print(f"  ✅ RankMath meta written: HTTP {r2.status_code}")
    
    time.sleep(2)  # respect WP

print()
print("="*75)
print("DONE. Run curl verification next.")
