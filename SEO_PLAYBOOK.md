# SweetsWorld SEO Playbook

> **单一权威文档** — 所有 landing / 产品 SEO / site audit / rescue 工作的统一规范。
> 新会话、新 subagent、新开发者开工前**必读**。
>
> Last updated: 2026-04-22 (by Michael + Claude consolidation)
> Location: `apps/wordpress-ai-ops/SEO_PLAYBOOK.md`

---

## 0. 核心原则（写在最前）

1. **Preflight > Fire** — 动手前查 URL 存在性 + 类型，分清 `WP page` / `WC category` / `WC tag` / `WP post`，各类型改法不同
2. **Backup > Write** — 任何 WP 写入前先 dump 当前 JSON 到本地文件。`rollback.py` 能用全靠它
3. **Verify > Assume** — 写完 curl 实地抓，grep 预期 marker，HTTP 200 + schema live 才算完成
4. **Internal links not optional** — 建 landing 默认包含"从 3-5 个相关页加反向内链"，不做 = 孤岛 = 白建
5. **Never touch homepage casually** — 首页改了要沉淀 2-4 周看 Google 信号
6. **Deterministic + Generative 分离** — 产品选择/slug/去重走确定性代码，文本内容交给 LLM 生成
7. **永久工具 > 临时脚本** — 所有 `/tmp/*.py` 一次性脚本必须固化到 `seo_tools/`，Michael 原话："不要做成临时的"
8. **Slug 必带 `-australia` 后缀** — SW 站启用"Strip Category Base"，`/<slug>/` 被 58 cat + 279 tag + 51 page 三类对象共享。新 landing slug 不带国家后缀 = 随时撞暗雷（#20）。例：`/dutch-licorice-australia/` ✅，`/dutch-licorice/` ❌。建 page 前必跑 `common.check_slug_collision(slug)`，`publish_landing.py` 已硬拦。

---

## 1. 技术栈

### 1.1 API 层

| 目标 | 用什么 | 注意 |
|---|---|---|
| 读/写 WP page / post | `GET/POST /wp-json/wp/v2/pages/{id}` or `/posts/{id}` | Basic Auth with `WP_USERNAME` + `WP_APP_PASSWORD` |
| 读/写 WC product | `GET/POST /wp-json/wc/v3/products/{id}` | 同上 |
| 读/写 WC category description | `GET/POST /wp-json/wc/v3/products/categories/{id}` | ⚠️ **仅短文案**（300-800 字），不要塞视觉 hub |
| **写 RankMath SEO meta** | `GET /wp-seo-meta.php?token=...&post_id=...&keyword=...&title=...&description=...` | 🔴 REST API 返回 403，必须走 DB bridge。Token: `sw_seo_meta_k8x2`（env `WP_SEO_BRIDGE_TOKEN`）|
| 读/写 term meta (category SEO) | 暂无永久 endpoint | 目前需临时 PHP 文件 scp 上传 → curl 执行 → rm 清理 |
| Google 推送重爬 | Indexing API `urlNotifications:publish` `type=URL_UPDATED` | Service account `gsc_credentials.json` |
| 日度排名监控 | GSC API → SQLite `rank_history.db` | launchd `com.sweetsworld.rank-tracker.daily` 9:30 AEST |

### 1.2 共享工具

```python
# 所有 SEO 脚本第一行必须写
from common import wp_get, wp_post, write_rank_math_meta, safe_request, find_by_slug, validate_product
```

位置：`apps/wordpress-ai-ops/scripts/seo_tools/common.py`
- `safe_request` 自带 3 次重试 + 30s timeout
- `find_by_slug(slug)` 自动扫 product / post / page 3 类，返回 `(kind, id, url)`
- `validate_product(pid)` 校验 stock + image + publish + visibility

### 1.3 venv

```bash
# 别用 wp-ai-ops 自己的 .venv（没装 requests）
# 用 sweetsworld-seo-agent 的 venv
/Users/michaelzhao/agents/agents/sweetsworld-seo-agent/.venv/bin/python
```

### 1.4 Credentials

- WP：`agents/sweetsworld-seo-agent/.env` (WP_BASE_URL / WP_USERNAME / WP_APP_PASSWORD / WP_SEO_BRIDGE_TOKEN)
- SSH：`~/.ssh/sweetsworld_agent_nopass.pem` port 2222 user `sweetsworld` host `103.27.35.29`
- GSC：`agents/sweetsworld-seo-agent/gsc_credentials.json`

---

## 2. 活跃 Code Snippets（SW 站，~35 个 active）

Snippet 是 site-wide 逻辑的载体。**不要删这些 snippet，否则以下功能会崩。**

### 2.1 SEO 关键 snippets

| ID | 名称 | 作用 | 删会怎样 |
|---|---|---|---|
| **43** | SEO: WC archives H1 | 所有 product category / tag / shop 页自动注入 H1 | 100+ 分类页 H1 全消失 |
| **55** | SEO: Auto FAQPage schema | 扫 `<details>/<summary>` → 生成 FAQPage JSON-LD + 智能跳过已有 inline | 所有 landing 丢失 FAQPage rich result |
| **48** | LocalBusiness Schema NAP | 首页 + 4 city 页输出 LocalBusiness schema | GBP + Local SEO 断裂 |
| **8** | Canonical for `?add-to-cart=` | 剥去 query 参数的 canonical + noindex | 购物车参数 URL 被 Google 索引，稀释权重 |
| **40** | Admin Update Throttle | 限制 wp-admin 更新检查到每日 4:15 AM + 插件 UI bypass | 后台从 6.5s 回到 18s |

### 2.2 Site structure

| ID | 名称 | 作用 |
|---|---|---|
| 15 | Homepage Top Bar | 顶部 banner（$80 免运提示）|
| 34 | Cart Free Shipping Progress | 购物车进度条 |

### 2.3 CRO Bundle（2026-04-21 部署）

| ID | 名称 |
|---|---|
| 49-54 | Cart→Checkout 优化（sticky CTA / trust badges / exit intent / shipping countdown / progress indicator）|

**计划合并**：35 → ~21 个（`project_snippet_consolidation.md`），**05-12 母亲节后执行**。

### 2.4 如何修改 snippet

```bash
# 1. 通过 DB 写入（Code Snippets plugin 存在 wp5c_snippets 表）
# 2. 🔴 写完必须 flush transient cache（见 Pitfall #7）
# 3. 去 wp-admin 的 Snippets 页面手动 Save+Activate 一次最稳
```

---

## 3. Landing Page 统一视觉模板（`/party-sweets/` pattern）

所有 visual hub landing 复用这个格式，**不允许自由发挥**：

### 3.1 结构

```
┌─ Hero (gradient background + 40-50px H1 + subtitle + CTA button)
├─ 3-6 品牌卡 / 口味卡 (grid, 2-3 cols)
├─ 产品 grid (占位符: <!-- WOOCOMMERCE_PRODUCT_GRID: ids=X,Y cols=N -->)
├─ <details>/<summary> FAQ ×  5-10 个 (snippet #55 自动生成 schema)
└─ Navy gradient CTA box (#32455a)
```

### 3.2 色板

| 用途 | Hex |
|---|---|
| 主粉 | `#d16688` |
| 蓝 | `#5eb4d8` |
| 薄荷 | `#83c9b8` |
| 深蓝（CTA）| `#32455a` |
| 背景粉 | `#fff8fb` |

### 3.3 H1 规则（🔴 最常踩的坑）

**Hero 标题必须用 `<h1>`**，不能用 `<h2 font-size:40px>`。整页**有且仅有一个 `<h1>`**。

```html
<!-- ✅ 正确 -->
<h1 style="font-size:40px;color:#32455a">Dubai Chocolate Australia</h1>

<!-- 🔴 错误 -->
<h2 style="font-size:40px;color:#32455a">Dubai Chocolate Australia</h2>
```

Subagent prompt 必须显式说明：`Hero 标题用 <h1>，不是 <h2>。整页只能有一个 h1。`

### 3.4 产品 grid 占位符

Bundle 里不直接写 WC shortcode，用占位符：

```
<!-- WOOCOMMERCE_PRODUCT_GRID: ids=12345,67890 cols=4 -->
```

`publish_landing.py` 发布时替换为 `[products ids="12345,67890" columns="4"]`。

### 3.5 FAQ 格式

```html
<div class="sw-faq-block" style="margin-top:40px">
<h2>Frequently Asked Questions</h2>
<details style="margin-bottom:18px;border:1px solid #e5e5e5;border-radius:6px">
<summary style="padding:16px 18px;font-weight:600;cursor:pointer;line-height:1.6">
Your question here
</summary>
<div style="padding:16px 18px 18px;line-height:1.8">
Your answer here, can include <a href="/internal-link/">internal links</a>.
</div>
</details>
<!-- more <details> blocks -->
</div>
```

**不要**手写 `<script type="application/ld+json">FAQPage...` —— Snippet #55 从 `<details>` 自动生成。

### 3.6 WC category 例外

WC category description **仅塞文字**（300-800 字段落 + 少量内链）。**不要** 塞视觉 hero / 品牌卡网格 —— 会和自动渲染的产品 grid 冲突。视觉 hub 去建独立 WP page，用不同 slug（如 `/american-candy-australia/`）。

---

## 4. 标准作业流程（SOP）

### 4.1 新 landing 发布（5 步 + 验收）

```bash
cd apps/wordpress-ai-ops/scripts/seo_tools

# 1. Preflight（🔴 必做）
python3 preflight.py --slug <slug> --keywords "<kw1>,<kw2>"
# 输出: URL 是否存在 + 类型 + 库存扫描

# 2. Subagent 生成 bundle.json 到 /tmp/landing_pages/<slug>/
#    包含: content HTML / products_to_feature / meta / internal_links_plan

# 3. 发布
python3 publish_landing.py --bundle /tmp/landing_pages/<slug>/bundle.json
# 自动: 产品校验 → 占位符替换 → POST /wp/v2/pages → RankMath meta → WP Rocket purge

# 4. 验收（🔴 必做）
curl -s "https://sweetsworld.com.au/<slug>/" | grep -c '<h1'   # 应 = 1
curl -s "https://sweetsworld.com.au/<slug>/" | grep -c 'FAQPage'  # 应 >= 1

# 5. 提交 Indexing API
python3 -c "from common import *; submit_indexing(['https://sweetsworld.com.au/<slug>/'])"
```

### 4.2 产品页 SEO 批量增强（Stage 模式）

```bash
# 1. 找候选（从 rank tracker DB）
python3 product_candidates.py --min-imp 15 --output /tmp/cands.csv

# 2. Subagent 生成 bundles.json — 每个产品包含:
#    - pid / slug / focus_keyword
#    - new description HTML (含 <details> FAQ + 内链)
#    - new_meta_title / new_meta_description

# 3. 应用（自动备份 + 写 + 验证）
python3 product_enhance.py --bundles /path/to/bundles.json
# 写入 backups/<timestamp>/product_<pid>.json

# 4. Verify
python3 product_enhance.py --verify /path/to/results.json
```

### 4.3 Site Audit 修复

```bash
# Title 太长 / H1=title dupe
python3 batch_titles.py --csv apps/wordpress-ai-ops/data/semrush/site_audit/2026-04-20_title_too_long.csv

# Sitemap 重复（移除 Uncategorized）
python3 remove_uncategorized.py --csv apps/wordpress-ai-ops/data/semrush/site_audit/2026-04-20_wrong_sitemap.csv
```

### 4.4 救援掉排名页（rescue pattern — 今早 2026-04-22 成熟模式）

```bash
# 1. 诊断：从 Semrush Position Changes CSV 切出目标页
# 2. 备份 4 页 JSON → backups/semrush_rescue_<timestamp>/
# 3. 判断类型：纯救援 / 蚕食治理 / URL 迁移验证
# 4. 执行 DRY_RUN=1 预览 → 用户批准 → 写入
# 5. curl + grep markers + Indexing API + 更新 MANIFEST
```

参考实现：`scripts/seo_tools/runs/2026-04-22_semrush_rescue_3pages.py`

---

## 5. 踩过的坑 & 对应规则（Pitfall → Prevention）

### #1 Hero 用了 H2，Landing 全部 missing H1（2026-04-21 Semrush Site Audit）
**预防**：subagent prompt 必须显式要求 `<h1>`；发布后 `grep -c '<h1'` 验证 = 1

### #1b Post 和 Page H1 规则不同（2026-04-22 三连坑）
**规则**：
- **WP Page**：theme **不自动**渲染 H1，content **必须**自带 `<h1>`
- **WP Post**：theme **自动** `<h1 class="entry-title">` 从 WP title 渲染，content **不要**再放 `<h1>` → 双 H1 冲突

**发生**：2026-04-22 同一天连续 3 次踩坑：hottest-chilli-sauce-newcastle / licorice-allsorts / wicked-fizz，都是 post 升级时 content 里写了 hero `<h1>`，live 页面 H1=2。

**预防**：
- 发布脚本生成 post content 时，用 `<div>` hero block 但 **标题用大字号 `<h2>` 或 `<p>` 样式**，不用 `<h1>`
- 发布脚本生成 page content 时，**必须** content 自带 `<h1>`
- 验收一律 `grep -c '<h1'` 必须 = 1

### #2 把 visual hub 塞进 WC category（2026-04-20 American Candy）
**预防**：preflight 查类型 → category 只能塞短文案 + 内链，hero/卡片网格放独立 WP page

### #3 Featured 产品缺货 → landing 只显示 2 款（2026-04-20 Dubai）
**预防**：`publish_landing.py` 自动 `validate_product()`，缺货/无图的在发布前淘汰或替换

### #4 建新 landing 不加内链 → 孤岛页（2026-04-20 Michael 明确指示）
**预防**：发布工作流强制第 5 步"加 3-5 个反向内链"，缺一不可

### #5 RankMath REST API 403
**预防**：绝对不走 REST，只走 `/wp-seo-meta.php?token=...` DB bridge

### #6 WC product description 里 `<script>` 被剥
**预防**：产品描述**永远不要**写 `<script type="application/ld+json">` —— 只放 `<details>`，snippet #55 从 `wp_head` 注入

### #7 改了 Snippet 表但 live 不生效
**预防**：
```php
$wpdb->query("DELETE FROM {$wpdb->options} WHERE option_name LIKE '%code_snippet%' OR option_name LIKE '_transient_%snippet%'");
wp_cache_flush();
```
或去 wp-admin Snippets 页面手动 Save+Activate。

### #8 Subagent 搞错 product ID → 覆盖无辜产品（2026-04-21 晚）
**预防**：`product_enhance.py` 加 slug check（写前验证 pid 对应的 slug 是否匹配 bundle 声明的 slug），失败 abort；强制 backup → rollback.py 能用

### #9 wpautop 破坏 post HTML（破坏 inline `<script>`、换行毁排版）
**预防**：blog post 内容必须 `<!-- wp:html --> ... <!-- /wp:html -->` 包裹才算 Gutenberg HTML block，不会被 wpautop 摧残

### #10 URL 迁移忘了 301（2026-04-22 发现 /newcastle/ → /candy-guides/ 是对的）
**预防**：任何 slug 改动都要 curl 旧 URL 确认 301 到位，HTTP 200 直接走则是 redirect 没生效

### #11 关键词蚕食（Bertie Beetle 4 页抢 vol 4400，今早发现）
**预防**：新 landing / 产品页**前**先 `grep` Position Changes CSV 看是否已有同词的多页面，确认只有 1 个 hub；否则要么 301 合并，要么改 focus keyword

### #12 Homepage 频繁改 → Google 信号乱
**预防**：首页改完**至少 2-4 周不再动**。数据沉淀后再评估是否需要下一轮

### #13 Tag slug 和 Category slug 冲突
**预防**：新建 product tag 前查同名 category；冲突必须加 `tag-` 前缀

### #14 Flatsome `.row` class + 内联 CSS Grid 冲突
**预防**：visual hub 的 grid 用独立容器 class，别混用 Flatsome 原生 `.row`

### #15 GA4 分析没加国家过滤
**预防**：所有 GA4 分析必须 `country=AU`，全球数据被垃圾流量稀释（AOV 差一倍）

### #16 WP Rocket 缓存绕过 PHP 条件
**预防**：首页特定样式用 `body.home` CSS 选择器，不用 `is_front_page()`

### #17 邮件 logo 用 sweetsworld.com.au 被 WebP 转换
**预防**：邮件图片用 Klaviyo CDN，不用自己域名

### #18 Cart/Checkout 自定义 slug (`/candycart/` `/sweet-checkout/`)
**预防**：调试购物车问题用**真实 slug**，不用默认 `/cart/` `/checkout/`

### #19 Meta 有 2 个 App
**预防**：Sweetsworld Marketing (1653910315647003) 投广告，Sweetsworld (468345310980112) 网站集成。操作 API 前确认 App。

### #20 WC category slug 覆盖 WP page 同 slug（2026-04-22）
**现象**：写 RankMath meta 到 WP page 22503（slug `british-lollies`），live URL `/british-lollies/` 无效果。
**原因**：WP option `woocommerce_permalinks.category_base = product-category` 本该让 cat 在 `/product-category/<slug>/`，但站点启用了 RankMath 或同类"Strip Category Base"插件，把 WC cat + tag 全压到 `/<slug>/`。所以 51 page + 58 cat + 279 tag **共享同一 URL 命名空间**。同 slug 时 WC rewrite 优先，page 静默被架空。
**规则**：
- 写 meta 前查 `wc/v3/products/categories?slug=<x>` 和 `.../tags?slug=<x>`。命中 → 走 term_meta bridge；未命中 → 走 post_meta bridge
- 建 page 前必跑 `common.check_slug_collision(slug)`（`publish_landing.py` 已硬拦）
- 新 landing slug **必带 `-australia` 后缀**（惯例 #8），天然避开 tag 池（tag 通常不带国家词）
**工具**：
- `common.check_slug_collision(slug)` → `{safe: bool, pages, cats, tags}`
- `common.suggest_safe_slug(slug)` → 自动追加 `-australia`
- `common.write_rank_math_term_meta(term_id, ...)` → term 专用 bridge
- `scripts/seo_tools/slug_collision_monitor.py` → 周一 08:30 launchd 扫描 + Telegram（**双审计**：slug 冲突 + 缺 focus_kw 页面）
**预防**：任何 page 新建/救援前跑一次 slug collision check。每周一 monitor 自动扫，新冲突或新 focus_kw 空缺推 Telegram。已 seed 现有已知项，只对**增量**报警。

---

## 6. 验收清单 (必做，每次)

### 6.1 写入后立即（T+0）
- [ ] HTTP 200 on live URL
- [ ] `<h1>` 有且仅有 1 个（landing / page / post）
- [ ] FAQPage schema 出现在 HTML（如有 FAQ）
- [ ] RankMath title 和 meta description 在 `<head>` 里
- [ ] 所有 FAQ 标记 marker 在 live HTML 中 grep 到
- [ ] 内链 3-5 个（新 landing）
- [ ] Google Indexing API 提交成功（返回 `urlNotificationMetadata`）

### 6.2 短期（T+3 天）
- [ ] GSC URL Inspection API 查索引状态 → `INDEX, AUTO_INDEXED` 或 `VERDICT: PASS`
- [ ] 确认 Indexing 的 `latestUpdate.notifyTime` 已被 Google 处理

### 6.3 中期（T+14 天）
- [ ] 重导 Semrush Position Changes，对比基线
- [ ] GSC 看 impressions + clicks 是否出现
- [ ] Rank Tracker（GSC API）DB 里看每日排名曲线

### 6.4 长期（T+6 周）
- [ ] CTR 对比改前数据（RankMath meta 升级验证）
- [ ] 评估是否二次优化

---

## 7. 备份与回滚

### 7.1 备份目录结构

```
apps/wordpress-ai-ops/scripts/seo_tools/backups/
├── <timestamp>/                      # 每次写入前自动创建
│   ├── product_<pid>_<slug>.json    # 完整 WP/WC API 返回
│   └── MANIFEST.json                 # 目录 + verification 字段
└── semrush_rescue_<timestamp>/       # 按操作命名
    └── ...
```

### 7.2 回滚

```bash
python3 rollback.py --backup backups/<timestamp>/ --pid <id>
# 从 backup JSON 读出原 content/description，POST 回 WP
```

### 7.3 命名约定

- Rescue / 一次性操作：`<operation_name>_<YYYYMMDD_HHMMSS>/`
- Stage 批量：`stage<N>_<YYYYMMDD>/`
- Site audit 修复：`siteaudit_<issue>_<YYYYMMDD>/`

---

## 8. 数据源 reference

### 8.1 Semrush 数据总仓

`apps/wordpress-ai-ops/data/semrush/` (README.md 详述)

- `position_changes/` — SW 位置变化时间序列（最新 2026-04-22 6,075 kws 6-mo）
- `positions/` — 4 家 Positions：SW / sweetas / lollyworld / joysdelights
- `keyword_magic/` — 8 个种子：dubai-chocolate / takis / american-candy / licorice / sour-candy / candy-bar / lollipops / bubble-gum
- `keyword_gap/` — 3 份（strong / weak / missing）
- `site_audit/` — 19 个 issue 类别
- `backlinks/` — backlinks_matrix
- `traffic_analytics/` — `.Trends` 竞品流量画像

### 8.2 每次分析都先 glob 看有什么

```bash
ls apps/wordpress-ai-ops/data/semrush/*/
```

**不要重复导数据**。Semrush 导出有次数限制 + 凭空浪费时间。

---

## 9. 分支策略

大多 SEO 操作是 live 数据写入，没有 staging。**所以 backup + verify 是唯一防线**。

如果涉及代码变更（脚本 / snippet 源码）：
- 脚本：git feature branch，dry-run 通过后合 master
- Snippet：DB 写入前 export 现有 snippet 到本地 JSON

---

## 10. 当前已完成 landing（不要重建）

2026-04-19 ~ 04-20 共 9 + Newcastle 旧 10 + 今早 American Food (pid 72434) = 20+ landing。

| Slug | PID | 目标词 | 月 vol |
|---|---|---|---|
| /dubai-chocolate/ | 72287 | dubai chocolate | 157K |
| /takis-australia/ | 72288 | takis australia | 33K |
| /lolly-chocolate-gift-delivery-australia/ | 72289 | lolly gift delivery | 27K |
| /nik-l-nip-wax-bottles/ | 72290 | nik-l-nip | 6.3K |
| /licorice-australia/ | 72322 | licorice australia | 6.6K |
| /sour-candy-australia/ | 72328 | sour candy | 1.9K |
| /candy-bar/ | 72329 | candy bar | 607 |
| /lollipops-australia/ | 72339 | lollipops | 11.5K |
| /bubble-gum-australia/ | 72344 | bubble gum | 7.7K |
| /american-food-australia/（pid 72434）| 72434 | american food | 2.4K |

**建新 landing 前 grep 这个清单**，避免重复。

---

## 11. 相关 memory 文件索引

动手前最低限度要读的 memories：

- `feedback_landing_hero_h1.md` — H1 规则
- `feedback_landing_page_preflight_check.md` — URL 类型排查
- `feedback_landing_page_product_validation.md` — 产品校验
- `feedback_landing_pages_internal_links.md` — 内链强制
- `feedback_wc_script_stripping_and_faqpage_snippet.md` — script 剥离 + snippet #55
- `feedback_sweetsworld_lessons.md` — 9 条综合教训
- `reference_seo_tools.md` — 工具清单
- `reference_sweetsworld_credentials.md` — 凭据地图

---

## 12. 变更记录

- **2026-04-22**：本文档首次建立（Michael 要求）— 整合 20+ feedback memories 和 8 个 project records
- Upcoming: 05-12 snippet consolidation 后更新 Code Snippets 清单
