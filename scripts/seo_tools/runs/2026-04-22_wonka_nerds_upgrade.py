"""Upgrade post 72462 /candy-types/wonka-australia/ → consolidated Wonka + Nerds hub.

LESSON APPLIED (Playbook Pitfall #1b): Post type → NO inline H1 in content, theme renders entry-title.
"""
import sys, json, os
from pathlib import Path
sys.path.insert(0, '.')
from common import wp_get, safe_request, WP_BASE, SEO_TOKEN

PID = 72462
DRY = os.environ.get('DRY_RUN','0')=='1'

# Backup
TS = "20260422_124500"
BK = Path(f"backups/wonka_nerds_upgrade_{TS}")
BK.mkdir(parents=True, exist_ok=True)
data = wp_get(f'wp/v2/posts/{PID}', context='edit')
(BK/f"wonka-australia_post_{PID}_PRE.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))
print("✅ Backup saved")

# Curated products — mix of Wonka classics + hot Nerds sellers
PRODUCTS = [24804, 14884, 14882, 22422, 22424, 51210, 14477, 56704, 59827, 23934]
PRODUCTS_STR = ','.join(str(x) for x in PRODUCTS)

def fd(q,a):
    return (f'<details style="margin-bottom:18px;border:1px solid #e5e5e5;border-radius:6px">'
            f'<summary style="padding:16px 18px;font-weight:600;cursor:pointer;line-height:1.6">{q}</summary>'
            f'<div style="padding:16px 18px 18px;line-height:1.8">{a}</div></details>')

# NOTE: No <h1> in content — post theme renders entry-title
inner = f"""<div style="background:linear-gradient(135deg,#d16688 0%,#32455a 100%);padding:52px 28px;text-align:center;color:#fff;margin-bottom:28px;border-radius:8px">
<p style="font-size:40px;margin:0 0 12px;color:#fff;font-weight:700;line-height:1.1">Wonka &amp; Nerds Australia</p>
<p style="font-size:18px;max-width:720px;margin:0 auto 18px;line-height:1.6;color:#fff8fb">The ultimate hub for American Wonka candy in Australia — Nerds Gummy Clusters, Rainbow Nerds, Nerds Rope, Everlasting Gobstoppers and more. Imported direct, ships same-day from SweetsWorld Newcastle.</p>
<a href="#wonka-shop" style="background:#5eb4d8;color:#fff;padding:12px 28px;border-radius:6px;text-decoration:none;font-weight:600;display:inline-block">Shop Wonka &amp; Nerds</a>
</div>

<h2 class="wp-block-heading">The Wonka + Nerds universe</h2>
<p><strong>Willy Wonka</strong> (now owned by Nestlé and Ferrara) is one of America's most beloved candy brands — born from Roald Dahl's <em>Charlie and the Chocolate Factory</em> and turned into real candy in the 1970s. The flagship products include:</p>
<ul>
<li><strong>Nerds</strong> — tiny crunchy sugar pebbles in fruit flavours (launched 1983, now the category leader)</li>
<li><strong>Nerds Gummy Clusters</strong> — the viral TikTok sensation: gummy centres coated in Nerds crunchy shell</li>
<li><strong>Nerds Rope</strong> — soft gummy rope studded with Nerds crystals</li>
<li><strong>Everlasting Gobstoppers</strong> — long-lasting jawbreakers that change colour as you suck</li>
<li><strong>Laffy Taffy</strong> — chewy taffy bars with a joke on every wrapper</li>
<li><strong>Runts</strong> — hard candy shaped and flavoured like tiny fruits</li>
<li><strong>Pixy Stix</strong> — powdered sour sugar straws</li>
</ul>

<h2 class="wp-block-heading">Why Nerds are the #1 viral Wonka product right now</h2>
<p>If you've been on TikTok, Instagram Reels, or Aussie candy forums in the last 18 months, <strong>Nerds Gummy Clusters</strong> have exploded globally. The combination of chewy gummy + crunchy Nerds coating creates the textural contrast that social media food videos love. At SweetsWorld, Nerds Gummy Clusters is consistently one of our top 10 fastest-selling products — <strong>get them while in stock.</strong></p>

<h2 class="wp-block-heading">Popular Nerds &amp; Wonka varieties</h2>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:18px;margin:26px 0">

<div style="background:#fff8fb;padding:22px;border-left:4px solid #d16688;border-radius:6px">
<h3 style="margin:0 0 10px;color:#32455a">🔥 Nerds Gummy Clusters</h3>
<p style="margin:0">The TikTok viral hit. Chewy gummy centres with Nerds crystal coating. Rainbow flavours.</p>
</div>

<div style="background:#fff8fb;padding:22px;border-left:4px solid #5eb4d8;border-radius:6px">
<h3 style="margin:0 0 10px;color:#32455a">Rainbow Nerds 141g</h3>
<p style="margin:0">The classic two-compartment box with multi-flavour rainbow Nerds. Kids' #1.</p>
</div>

<div style="background:#fff8fb;padding:22px;border-left:4px solid #83c9b8;border-radius:6px">
<h3 style="margin:0 0 10px;color:#32455a">Nerds Rope (Rainbow / Very Berry)</h3>
<p style="margin:0">Gummy rope studded with Nerds crystals — a full sensory experience in every bite.</p>
</div>

<div style="background:#fff8fb;padding:22px;border-left:4px solid #32455a;border-radius:6px">
<h3 style="margin:0 0 10px;color:#32455a">Everlasting Gobstopper</h3>
<p style="margin:0">The iconic colour-changing jawbreaker. Lasts 30+ minutes of sucking — name is no joke.</p>
</div>

<div style="background:#fff8fb;padding:22px;border-left:4px solid #d16688;border-radius:6px">
<h3 style="margin:0 0 10px;color:#32455a">Nerds Grape &amp; Strawberry 141g</h3>
<p style="margin:0">The flavour combo that launched the brand — still the most popular Nerds box.</p>
</div>

<div style="background:#fff8fb;padding:22px;border-left:4px solid #5eb4d8;border-radius:6px">
<h3 style="margin:0 0 10px;color:#32455a">Wonka Gobstopper 50g</h3>
<p style="margin:0">Smaller travel-size format perfect for pockets, lunchboxes or party goodie bags.</p>
</div>

</div>

<h3 class="wp-block-heading" id="wonka-shop">Shop Wonka &amp; Nerds online in Australia</h3>
<p>All products below ship same-day from our Newcastle warehouse — AU-wide delivery in 2-5 business days.</p>

[products ids="{PRODUCTS_STR}" columns="4"]

<h2 class="wp-block-heading">Wonka / Nerds at SweetsWorld vs Australian supermarkets</h2>
<p>Australian supermarkets (Coles, Woolworths, IGA) stock a limited Wonka range — usually just Rainbow Nerds and occasionally Nerds Rope. The specialty items — <strong>Gummy Clusters, Everlasting Gobstoppers, Laffy Taffy, Pixy Stix, Nerds hair colour</strong> — are only reliably available through dedicated American candy retailers like SweetsWorld. We import direct from US suppliers and keep rotating stock of the viral / hard-to-find lines.</p>

<h2 class="wp-block-heading">How to build the perfect Wonka candy gift</h2>
<p>For birthday gifts, American-themed parties, or care packages to Wonka-loving kids:</p>
<ol>
<li><strong>1 box Nerds Gummy Clusters</strong> — the viral headliner everyone's heard about</li>
<li><strong>1-2 Rainbow Nerds boxes</strong> — the classic visual + flavour</li>
<li><strong>1 Nerds Rope</strong> — novelty format for TikTok-ready unboxing</li>
<li><strong>1 Everlasting Gobstopper</strong> — long-lasting, slows them down</li>
<li><strong>Optional add-ons:</strong> Wonka Gobstopper small pack + Runts (if in stock)</li>
</ol>
<p>Package in a clear cello bag with coloured tissue + gift tag. Total gift cost: ~$35-50 AUD for a premium American candy gift that Coles/Woolies can't match.</p>

<div class="sw-faq-block" style="margin-top:40px">
<h2 class="wp-block-heading">Frequently Asked Questions</h2>
""" + "\n".join([
    fd("Where to buy Nerds Gummy Clusters in Australia?",
       "SweetsWorld stocks Nerds Gummy Clusters 141g imported direct from the USA. Ships same-day Australia-wide from our Newcastle warehouse. Supply fluctuates due to high global demand (TikTok-driven) — order while in stock. Sydney, Melbourne, Brisbane, Perth, Adelaide deliveries typically arrive in 2-5 business days."),
    fd("What's the difference between regular Nerds and Nerds Gummy Clusters?",
       "<strong>Regular Nerds</strong> are tiny crunchy sugar pebbles with crystal texture — fruit flavours like grape, strawberry, watermelon. <strong>Nerds Gummy Clusters</strong> wrap a soft chewy gummy centre in a shell of the crystal Nerds — so you get chewy + crunchy in every bite. Clusters are significantly more viral on social media and higher-priced."),
    fd("Are Wonka candies and Nerds made in Australia?",
       "No — Wonka and Nerds are <strong>American brands</strong>, originally produced by the Willy Wonka Candy Company (now owned by Ferrara Candy, which is owned by Ferrero). Everything sold at SweetsWorld is imported direct from USA production. Some flavours get minor regional formulation tweaks but the core products are identical worldwide."),
    fd("Are Nerds gluten free? Vegan?",
       "Most Nerds products (including Rainbow Nerds and Gummy Clusters) are <strong>gluten-free</strong> in standard US formulations — but they are <strong>not certified</strong>, so consult the current pack label if you have coeliac disease. Nerds Gummy Clusters contain gelatin and are <strong>not vegan</strong>. Standard Nerds (crystals only) are typically vegan-friendly but check the current pack."),
    fd("Can you ship Wonka candy internationally from SweetsWorld?",
       "SweetsWorld ships within Australia (including Tasmania and remote AU). International shipping is not currently offered. Customers in New Zealand occasionally find us via other partner retailers."),
    fd("What's the best Wonka candy for kids' birthday parties?",
       "Our top 3 for party lolly bags: <strong>Rainbow Nerds 141g</strong> (divide across bags), <strong>Nerds Rope individual</strong>, and <strong>Wonka Gobstopper 50g</strong> (one per bag). For a full party snack table, add Nerds Gummy Clusters for the viral effect and novelty items like Fun Dip and Pixy Stix when in stock."),
    fd("Do you stock Willy Wonka Golden Ticket promotional items?",
       "These are typically limited seasonal releases tied to the movie remakes — we stock them when in production. Not currently in stock but worth checking back periodically, or follow SweetsWorld on social for new arrivals."),
]) + """
</div>

<p><em>Explore more: <a href="https://sweetsworld.com.au/candy/american-candy/">American Candy collection</a>, <a href="https://sweetsworld.com.au/newcastle/nerds-gummy-clusters/">Nerds Gummy Clusters deep dive</a>, <a href="https://sweetsworld.com.au/sour-candy-australia/">Sour Lollies Australia</a>, <a href="https://sweetsworld.com.au/takis-australia/">Takis Australia</a>.</em></p>

<div style="background:linear-gradient(135deg,#32455a 0%,#d16688 100%);padding:38px 22px;text-align:center;color:#fff;border-radius:8px;margin-top:32px">
<p style="color:#fff;margin:0 0 12px;font-size:26px;font-weight:700">Order Wonka &amp; Nerds today</p>
<p style="max-width:600px;margin:0 auto 18px;color:#fff8fb">10+ Nerds &amp; Wonka products in stock — same-day dispatch from SweetsWorld Newcastle.</p>
<a href="#wonka-shop" style="background:#5eb4d8;color:#fff;padding:11px 26px;border-radius:6px;text-decoration:none;font-weight:600;display:inline-block">Shop Now</a>
</div>"""

content = f"<!-- wp:html -->\n{inner}\n<!-- /wp:html -->"
print(f"[{'DRY' if DRY else 'LIVE'}] Upgrade post {PID}: 11,553 → {len(content):,} chars")

WP_TITLE = 'Wonka Candy & Nerds Australia | Gummy Clusters, Nerds Rope | SweetsWorld'
RM_TITLE = 'Wonka Candy & Nerds Australia | Gummy Clusters, Rope, Gobstoppers | SweetsWorld'
RM_DESC = 'Buy American Wonka candy and Nerds in Australia — Gummy Clusters, Rainbow Nerds, Nerds Rope, Everlasting Gobstoppers. Imported direct USA, same-day dispatch Newcastle.'
FOCUS = 'nerds gummy clusters'

if DRY:
    Path('/tmp/preview_wonka.html').write_text(content)
    print("Preview → /tmp/preview_wonka.html")
    sys.exit(0)

r = safe_request('POST', f"{WP_BASE}/wp-json/wp/v2/posts/{PID}", json={'content': content, 'title': WP_TITLE})
print(f"Content: HTTP {r.status_code if r else 'FAIL'}")

r2 = safe_request('GET', f"{WP_BASE}/wp-seo-meta.php",
                 params={'token':SEO_TOKEN,'post_id':PID,'keyword':FOCUS,'title':RM_TITLE,'description':RM_DESC}, auth=None)
print(f"RankMath: HTTP {r2.status_code if r2 else 'FAIL'}")
