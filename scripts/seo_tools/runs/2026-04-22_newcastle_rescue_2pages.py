"""Newcastle 2 pages rescue — hottest chilli + brain licker."""
import sys, json, os, time, re
from pathlib import Path
sys.path.insert(0, '.')
from common import wp_get, safe_request, WP_BASE, SEO_TOKEN

BK = Path("backups/newcastle_rescue_20260422_113256")
DRY = os.environ.get('DRY_RUN','0')=='1'

def fd(q,a):
    return (f'<details style="margin-bottom:18px;border:1px solid #e5e5e5;border-radius:6px">'
            f'<summary style="padding:16px 18px;font-weight:600;cursor:pointer;line-height:1.6">{q}</summary>'
            f'<div style="padding:16px 18px 18px;line-height:1.8">{a}</div></details>')

# ---- HOTTEST CHILLI (post 14289) — add <details> FAQ block (page has no existing <details>) ----
hot = json.load(open(BK/"hottest-chilli-sauce-newcastle_post_14289.json"))
hot_content = (hot.get('content') or {}).get('rendered','')

HOT_FAQ_BLOCK = """
<div class="sw-faq-block" style="margin-top:40px">
<h2 class="wp-block-heading">Frequently Asked Questions</h2>
""" + "\n".join([
    fd("Where can I buy the hottest chilli sauce in Newcastle?",
       "SweetsWorld stocks some of Australia's hottest chilli sauces online with same-day dispatch from our Newcastle warehouse. Visit our <a href=\"https://sweetsworld.com.au/chilli/\">Chilli Sauces collection</a> to see current stock including Carolina Reaper, Ghost Pepper and Scorpion heat levels."),
    fd("What is the hottest chilli sauce you can buy?",
       "Current Scoville record-holders commonly found in Australia include sauces made with Carolina Reaper (~1.6M SHU), Ghost Pepper (~1M SHU) and Trinidad Moruga Scorpion (~1.2M SHU). SweetsWorld stocks a rotating range from mild to extreme — look for \"Reaper\", \"Ghost\" or \"Scorpion\" in the product name for the hottest options."),
    fd("Is the hottest chilli sauce safe to eat?",
       "Super-hot chilli sauces are safe in small amounts for healthy adults but can cause severe burning, nausea and upset stomach in sensitive people. Never give to children, pregnant women, or anyone with ulcers or acid reflux. Always start with a single drop and build tolerance gradually."),
    fd("How long does hot chilli sauce last once opened?",
       "Most commercial hot chilli sauces last 6-12 months refrigerated once opened. The vinegar and salt act as preservatives. If the sauce darkens significantly, develops mould, or smells rancid, discard immediately."),
]) + """
</div>
"""

hot_new = hot_content.rstrip() + "\n\n" + HOT_FAQ_BLOCK

# ---- BRAIN LICKER (post 59706) — add 3 NEW commercial FAQ (avoid duplicating existing 5) ----
brain = json.load(open(BK/"brain-licker-2_post_59706.json"))
brain_content = (brain.get('content') or {}).get('rendered','')

BRAIN_NEW_FAQS = [
    fd("What is a Brain Licker made of?",
       "Brain Licker is a liquid candy made from sweetened water, food-grade citric acid (for the sour kick), sugar, natural and artificial flavours, and food colouring. The distinctive \"brain\" bottle design houses a roller-ball applicator so kids can lick the sour candy directly from the ball. Consult the pack for current ingredients and allergens."),
    fd("How sour is Brain Licker compared to Warheads?",
       "Brain Licker is mildly to moderately sour — less intense than Warheads Extreme Sour Spray but more sour than standard candy. The sourness comes from citric acid (not malic acid used in Warheads), giving a different flavour profile. Both are popular with kids who enjoy sour candy."),
    fd("Are Brain Lickers gluten free?",
       "Brain Lickers contain no wheat or gluten-based ingredients per standard formulations, but are not certified gluten free and may be produced on shared equipment. Always check the current pack label if you have coeliac disease."),
]
last_details = brain_content.rfind('</details>')
if last_details < 0:
    raise SystemExit("Brain licker FAQ structure not found")
brain_new = (brain_content[:last_details + len('</details>')]
             + "\n" + "\n".join(BRAIN_NEW_FAQS) + "\n"
             + brain_content[last_details + len('</details>'):])

# ---- Plans ----
plans = [
    {
        'label':'HOTTEST CHILLI','kind':'post','id':14289,
        'url':'https://sweetsworld.com.au/candy-guides/hottest-chilli-sauce-newcastle/',
        'old_len':len(hot_content),'new_content':hot_new,'new_len':len(hot_new),
        'meta':{'keyword':'hottest chilli',
                'title':'Hottest Chilli Sauce Australia | Carolina Reaper & Ghost Pepper | SweetsWorld',
                'description':'Australia\'s hottest chilli sauces online from SweetsWorld Newcastle — Carolina Reaper, Ghost Pepper, Scorpion, Trinidad Moruga. Same-day dispatch AU-wide.'},
        'verify':['Where can I buy the hottest chilli sauce', 'Carolina Reaper', 'Ghost Pepper'],
    },
    {
        'label':'BRAIN LICKER','kind':'post','id':59706,
        'url':'https://sweetsworld.com.au/candy-guides/brain-licker-2/',
        'old_len':len(brain_content),'new_content':brain_new,'new_len':len(brain_new),
        'meta':{'keyword':'brain licker',
                'title':'Brain Licker Candy Australia | Sour Liquid Candy Where to Buy | SweetsWorld',
                'description':'Brain Licker sour liquid candy in Australia — roller-ball sour kick, multiple flavours, buy online with same-day dispatch from SweetsWorld Newcastle.'},
        'verify':['What is a Brain Licker made of', 'How sour is Brain Licker', 'gluten free'],
    },
]

print(f"[{'DRY' if DRY else 'LIVE'}] {len(plans)} plans")
for p in plans:
    print(f"\n▶ {p['label']} ({p['kind']} #{p['id']}) {p['old_len']:,} → {p['new_len']:,} chars (+{p['new_len']-p['old_len']:,})")
    if DRY: continue
    r = safe_request('POST', f"{WP_BASE}/wp-json/wp/v2/posts/{p['id']}", json={'content': p['new_content']})
    print(f"  content: HTTP {r.status_code if r else 'FAIL'}")
    if r and r.ok:
        r2 = safe_request('GET', f"{WP_BASE}/wp-seo-meta.php",
                         params={'token':SEO_TOKEN,'post_id':p['id'],**p['meta']}, auth=None)
        print(f"  meta: HTTP {r2.status_code if r2 else 'FAIL'}")
    time.sleep(2)
print("\nDONE")
