# SEO Tools (SweetsWorld)

Permanent scripts that replace the ad-hoc `/tmp/*.py` we used during Apr 20-21 SEO sprint.
All tools share credentials from `agents/sweetsworld-seo-agent/.env`.

## Tools

| Script | Purpose |
|---|---|
| `common.py` | Shared WP/WC client + auth + helpers |
| `preflight.py` | URL existence check + inventory scan for new landings |
| `product_candidates.py` | Query rank tracker DB to find product pages with SEO upside |
| `product_enhance.py` | Apply FAQ + internal links + RankMath meta to products from bundles.json |
| `publish_landing.py` | Full 5-step publish: validate products → sub grid → publish → SEO meta → inbound links |
| `batch_titles.py` | Batch-rewrite RankMath titles (too-long / H1=title dupe fix) |
| `remove_uncategorized.py` | Clean Uncategorized from products to fix duplicate URL in sitemap |
| `landing_h1_audit.py` | Check H2→H1 hero on visual-hub landings |
| `rank_tracker/` | Daily GSC snapshot + winners/losers reports (launchd) |

## PHP endpoints installed on WP

| File | Purpose |
|---|---|
| `/wp-seo-meta.php` | Write rank_math_title / description / focus_keyword for posts |
| (none for categories yet — rebuild when needed) | |

## Active code snippets on WP

| ID | Name | Purpose |
|---|---|---|
| 40 | Admin: Throttle update checks | Limit wp-admin API to 4:15AM (with plugins/themes UI bypass) |
| 43 | SEO: Add H1 to WC archives | Auto-inject H1 on category/tag/shop pages |
| 55 | SEO: Auto FAQPage schema | Parse `<details>` blocks → FAQPage JSON-LD in head |

## Common workflow for new landing page

```bash
# 1. Preflight: check URL availability + existing inventory
python3 preflight.py --slug dubai-chocolate --keywords "dubai chocolate"

# 2. Generate content bundle (subagent)
# [manual — write bundle.json to /tmp/landing_pages/<slug>/]

# 3. Publish
python3 publish_landing.py --bundle /tmp/landing_pages/<slug>/bundle.json
```

## Common workflow for product SEO batch

```bash
# 1. Find candidates from rank tracker data
python3 product_candidates.py --output /tmp/candidates.csv

# 2. Generate FAQ bundles (subagent)
# [manual — write bundles.json]

# 3. Apply
python3 product_enhance.py --bundles /tmp/bundles.json
```
