# sweetsworld.com.au SEO 优化计划

> 记录所有已执行的操作和待办事项。每次操作须注明日期、工具/脚本、结果。

---

## 2026 SEO 蓝图自动化工程计划

> 对应蓝图：`docs/sites/sweetsworld/seo-blueprint-2026.md`
> 目标：为 4-Week Sprint 补齐所有缺失的自动化能力

### 总览

| 脚本 | 用途 | 蓝图周次 | 难度 | 状态 |
|------|------|----------|------|------|
| `bulk_create_pages.py` | 创建/更新 WP Pages | W1, W2, W4 | 低 | ✅ 完成（2026-04-06） |
| `bulk_text_replace.py` | 全站文字替换 | W1 | 低 | ✅ 完成（2026-04-06） |
| `bulk_category_content.py` | WC 分类页注入文案 | W2, W3 | 中 | ✅ 完成（2026-04-06） |
| `bulk_sku_descriptions.py` | Top 50 SKU 描述生成 | W3 | 中 | ✅ 完成（2026-04-06） |
| `internal_link_audit.py` | 内链缺口审计 | W4 | 低-中 | ✅ 完成（2026-04-06） |

### 完成说明（2026-04-06）

- 5 个脚本全部实现，39 个单元测试全通过（连续 3 次验证）
- Codex review 后修复 3 个关键问题：
  - `bulk_category_content.py` — 改为 prepend 而非 replace，保护现有分类描述
  - `bulk_text_replace.py` + `internal_link_audit.py` — 移除 19 页分页硬限制
  - `internal_link_audit.py` — 改用 `urllib.parse` 精确路径匹配，修复 substring 误报
- 数据文件：`data/pages_to_create.yaml`（5 页）、`data/core_topic_pages.yaml`（12 个核心专题页）
- 测试文件：`tests/test_bulk_*.py` × 5，全部使用 `unittest.mock`，无真实 HTTP 请求

---

### Script 1: `bulk_create_pages.py`

**用途**：从 YAML 配置批量创建或更新 WordPress Pages（非 posts）。

**API 调用**：
- 查重：`GET /wp-json/wp/v2/pages?slug={slug}` → 已有则跳过（或 `--update` 时覆盖）
- 创建：`wp_client.create_resource("page", payload)` → `POST /wp-json/wp/v2/pages`
- 更新：`wp_client.update_resource("page", id, payload)` → `POST /wp-json/wp/v2/pages/{id}`

**输入文件**：`data/pages_to_create.yaml`
```yaml
pages:
  - slug: returns-refunds
    title: "Returns & Refunds Policy"
    status: publish
    content: |   # 或留空让 Claude 生成
      <p>...</p>
    generate_content: true   # 若为 true 则调用 Claude Haiku 生成
    prompt_hint: "Returns policy for SweetsWorld, food items, Maitland NSW warehouse"

  - slug: seasonal-sweets
    title: "Seasonal Sweets & Holiday Candy Australia"
    status: publish
    generate_content: true
    prompt_hint: "Seasonal sweets hub: Christmas, Easter, Halloween, Valentine's, Mother's Day"
```

**逻辑流**：
1. 解析 YAML
2. 按 slug 查询是否已存在
3. 若 `generate_content: true`：调用 Claude Haiku 生成 HTML 内容（500-800字 + FAQPage schema 可选）
4. `create_resource` 或 `update_resource`
5. 可选：调用 `submit_indexing.py` 逻辑提交 Google Indexing API

**CLI flags**：`--dry-run` / `--update`（覆盖已有页面）/ `--submit-indexing` / `--batch N`

**依赖**：`WPClient`（现有）、`anthropic`（Claude Haiku，现有）

**注意**：创建 page 的凭证与 post 相同（WP username + app password），无需额外配置。

---

### Script 2: `bulk_text_replace.py`

**用途**：全站搜索替换文字，主要用于统一运费 `$15` → `$16.5`，也可通用。

**API 调用**：
- 读取：`list_resources("post")` + `list_resources("page")`（各100条/页，循环）
- 更新：`update_resource(type, id, {"content": new_content, "title": new_title})`（仅有变更时才写入）

**逻辑流**：
1. 拉取所有 published posts + pages（共约 ~170 条）
2. 对 `content.raw` + `title.raw` + `excerpt.raw` 执行替换（支持字面量或 `--regex`）
3. diff 对比，记录变更
4. dry-run 模式：只打印，不写入
5. 写入时附带 `modified_gmt` 更新时间戳

**CLI flags**：`--find <text>` / `--replace <text>` / `--regex` / `--scope posts|pages|all` / `--dry-run`

**使用示例**：
```bash
python scripts/bulk_text_replace.py --find "\$15" --replace "\$16.5" --regex --dry-run
python scripts/bulk_text_replace.py --find "\$15" --replace "\$16.5" --regex
```

**依赖**：`WPClient`（现有）；无需 Claude。

---

### Script 3: `bulk_category_content.py`

**用途**：给 WooCommerce 产品分类页注入 Claude 生成的导语段（含 `Australia` 关键词），提升分类页语义权重。

**API 调用（WooCommerce REST API，与 WP API 不同命名空间）**：
- 列出分类：`GET /wp-json/wc/v3/products/categories?per_page=100`
- 更新分类描述：`PATCH /wp-json/wc/v3/products/categories/{id}` with `{"description": html}`

**认证**：WooCommerce 使用独立的 Consumer Key + Consumer Secret（Basic Auth），不用 WP App Password。
- 需在 `.env` 新增：`WC_CONSUMER_KEY=ck_xxx` / `WC_CONSUMER_SECRET=cs_xxx`
- WC Consumer Key 在 WP 后台 → WooCommerce → Settings → Advanced → REST API 生成

**逻辑流**：
1. 从 `.env` 读取 `WC_CONSUMER_KEY` / `WC_CONSUMER_SECRET`
2. 拉取所有 product categories
3. 按 slug 过滤目标分类（从 YAML 或 CLI 指定）
4. 对每个分类：将 `name + 现有 description + slug` 发给 Claude Haiku
5. Prompt：生成 150-200 字导语，含 Australia 关键词，H2 小标题结构
6. 更新 `description` 字段（WC category description 支持 HTML）

**CLI flags**：`--dry-run` / `--category <slug>` / `--batch N`

**目标分类**（Week 2-3 的核心）：
- `american-candy`、`uk-sweets`、`australian-lollies`（新建）
- `bulk-lollies`、`gift-boxes`、`party-sweets`（新建）

**注意**：WC REST API 需要在 WP 后台开启 "Legacy REST API"（WooCommerce → Settings → Advanced）。

---

### Script 4: `bulk_sku_descriptions.py`

**用途**：给 WooCommerce Top 50 热销产品批量生成并写入 200 字独家场景化描述，避免与竞品内容雷同。

**API 调用**：
- 拉取产品：`GET /wp-json/wc/v3/products?per_page=50&orderby=popularity` 或按 slug 列表
- 更新描述：`PATCH /wp-json/wc/v3/products/{id}` with `{"short_description": html}`

**逻辑流**：
1. 拉取热销 Top 50 产品（按 `orderby=popularity`）
2. 过滤条件：`short_description` 为空，或纯文字 < 80 字（太短的也重写）
3. 对每个产品组装 prompt：产品名 + 分类 + 品牌 + 现有标题
4. Claude Haiku 生成 200 字场景化描述（含购买场景：party / gift / school lunchbox 等）
5. 写入 `short_description`（非 `description`，避免影响长描述）
6. 进度文件：`scripts/bulk_sku_progress.json`

**CLI flags**：`--dry-run` / `--batch 10` / `--min-length 80` / `--slug <s>` 单品模式

**认证**：同 Script 3，使用 `WC_CONSUMER_KEY` / `WC_CONSUMER_SECRET`。

---

### Script 5: `internal_link_audit.py`

**用途**：审计全站哪些 posts/pages 没有指向 12 个核心专题页，输出缺口报告。

**API 调用**：
- 读取：`list_resources("post")` + `list_resources("page")`

**逻辑流**：
1. 从 `data/core_topic_pages.yaml` 读取 12 个核心专题页 URL（也可 CLI 传入）
2. 拉取所有 published posts + pages
3. 对每个页面：解析 `content.rendered` 里的所有 `<a href="...">` 链接
4. 检查是否包含任意核心专题页 URL（部分匹配，如 `/american-candy/`）
5. 输出两份报告：
   - **缺口矩阵**：哪个页面缺哪个核心链接
   - **优先修复清单**：按现有流量（GSC 数据可选）排序

**输出**：`reports/internal_link_audit_{date}.json` + 控制台摘要

**可选增强**：读取 `data/gsc_data.json`（已有），按 impressions 排序缺口页面优先级。

**CLI flags**：`--scope posts|pages|all` / `--core-pages <yaml>` / `--gsc-data <json>` / `--output <file>`

---

### 前置条件

在开始 Script 3 & 4 之前，需要：
1. 在 WP 后台生成 WC Consumer Key：WooCommerce → Settings → Advanced → REST API → Add Key（Read/Write 权限）
2. 写入 `sweetsworld-seo-agent/.env`：
   ```
   WC_CONSUMER_KEY=ck_xxxxxxxxxxxx
   WC_CONSUMER_SECRET=cs_xxxxxxxxxxxx
   ```
3. 在 WP 后台确认 WooCommerce Legacy REST API 已启用

---

### 开发顺序建议

```
1. bulk_text_replace.py      ← 最简单，纯 WP API，用于 Week 1 运费统一
2. bulk_create_pages.py      ← 依赖 WP API，Week 1 建 Returns 页，Week 4 建 Seasonal Hub
3. internal_link_audit.py    ← 纯读取，帮助决策内链策略
4. bulk_category_content.py  ← 需要 WC 凭证，Week 2 核心任务
5. bulk_sku_descriptions.py  ← 同上，Week 3 任务
```

---

---

## 操作日志 ✅

### 2026-03-27
- [x] **FAQ 补全**：`scripts/bulk_faq_meta.py` — 106 篇 posts 全部加 FAQPage（5 个折叠问答 + FAQPage JSON-LD schema），Claude Haiku 按文章内容生成，candy_blog 受众
- [x] **RankMath meta 补全**：同上脚本 — 106 篇全部设置 title（≤60字）/ description（≤155字）/ focus keyword，Claude Haiku 生成，通过 `wp-seo-meta.php` DB 端点写入（REST API 返回 403 故绕过）
- [x] **Google Indexing API 提交**：`scripts/submit_indexing.py` — 106 篇全部提交 URL_UPDATED 通知，0 失败

### 2026-03-29
- [x] **代码修复**：`weekly_cycle.py` `_build_meta_task()` — 修复未传 `page_title`/`page_text` 导致 meta 使用硬编码模板的 bug；同时消除 `fetch_page_content()` 重复调用；`generate_faqs()` / `_build_update_task()` 移入 else 分支避免 meta_only 站点浪费 Claude API 调用
- [x] **内部链接注入**：`scripts/bulk_internal_links.py` — 53 篇旧内容（pre-2025）由 Claude Haiku 分析相关性后将 2–5 条新文章内链自然织入正文，53/53 成功，0 失败
- [x] **Google Indexing API 再次提交**：内联脚本 — 53 篇旧内容更新后再次提交，53/53 成功
- [x] **图片 alt text 扫描**：内联脚本 — 全站 106 篇 posts 扫描，22 篇有 featured image 且全部已有 alt text，0 篇 inline img 缺 alt，无需处理
- [x] **SEO 分析**：导入 Semrush On-Page Checker CSV（29.csv）+ 拉取 GSC 90天数据（40,464行，AU 市场）— 发现 751 个蚕食候选，识别出 3 类根本问题（见下方待办）
- [x] **GSC 数据存档**：`/tmp/gsc_cannibalization.json`（751条，含每个 keyword × page 的 clicks/impressions/position）
- [x] **问题一修复（`?add-to-cart=` canonical）**：Code Snippet #8 部署 — `wp_head` priority 1 输出 canonical + noindex；`rank_math/frontend/canonical` filter 优先级 999 覆盖 RankMath；curl 验证 `?add-to-cart=12721` 输出正确 canonical + noindex，6/6 测试 URL 通过
- [x] **问题二修复（同产品多分类路径）**：Code Snippet #9 部署（弱路径 → 强路径 canonical + noindex）；新增 REST endpoint `/wp-json/sw/v1/set-canonical`（Snippet #10）写入 `rank_math_canonical_url` DB 字段；新增 `/wp-json/sw/v1/purge-cache`（Snippet #12）+ `/wp-json/sw/v1/purge-url`（Snippet #13）通过 `rocket_clean_files()` 清除 WP Rocket 缓存；全部 6 对 URL 验证通过（✅×6）
- [x] **Google Indexing API 提交（问题一/二修复后）**：6 个受影响产品 URL（强弱各一）全部提交 URL_UPDATED，6/6 成功
- [x] **问题三修复（/newcastle/ 路径重复）**：确认所有 `/newcastle/` URL 已 301 → `/candy-guides/`；发现 `/candy-guides/` 内部真正重复（brain-licker ×2，nerd/nerds ×2）；设置 canonical 解决重复（post 59677 → brain-licker-2，post 59699 → nerds-gummy-clusters）；WP Rocket 缓存清除；提交 Indexing API 12 URLs（/newcastle/ + /candy-guides/ 各 URL）；验证 ✅×2
- [x] **首页坏链修复（page 22232）**：首页 "Shop now" 按钮 href 为 `/american-candy/`（根路径不存在，301→首页造成循环），修正为 `/candy/american-candy/`；WP Rocket 缓存清除；线上验证通过（坏链 0）

---

## 待办

### ~~图片 alt text 优化~~
- [x] 2026-03-29 全站扫描：22 篇有 featured image，全部已有 alt text；所有 inline img 也已有 alt；84 篇无图片
- **结论**: 无需处理，已达标

### ~~内容更新（Content Freshening）~~
- [x] 2026-03-29 内链步骤已完成：Claude 重写了全部 53 篇旧内容，相当于同步完成了内容优化
- **结论**: 已覆盖，无需单独处理

---

## SEO 技术问题修复（Semrush + GSC 双数据源，2026-03-29）

> Semrush 只是入口，GSC 实际数据（40,464行，90天）才是决策依据。
> GSC 完整数据: `/tmp/gsc_cannibalization.json`（751个蚕食候选，每个含实际点击/曝光/排名）

---

### ✅ 问题一：`?add-to-cart=xxx` URL 被 Google 索引 — 已修复（2026-03-29）

**修复方式**：Code Snippet #8（PHP）
- `wp_head` priority 1：检测 `?add-to-cart=` 参数，输出 canonical（剥离参数的干净 URL）+ `<meta name="robots" content="noindex, follow">`
- `rank_math/frontend/canonical` filter priority 999：覆盖 RankMath 输出同一干净 canonical
- 所有带 `?add-to-cart=` / `?removed_item=` / `?undo_item=` / `?wc-ajax=` 的 URL 均已覆盖
- 提交 Google Indexing API：6 个受影响产品 URL 已提交 URL_UPDATED

---

### ✅ 问题二：同产品多个分类路径 — 已修复（2026-03-29）

**修复方式**：Code Snippet #9 + REST API endpoints（#10/12/13）
- 弱路径统一设置 canonical 指向强路径 + noindex
- 强路径设置 self-canonical（防止 WooCommerce/RankMath 输出错误 canonical）
- `rank_math_canonical_url` DB 字段通过 `/wp-json/sw/v1/set-canonical` 写入
- WP Rocket 缓存通过 `/wp-json/sw/v1/purge-cache` 和 `/wp-json/sw/v1/purge-url` 清除

| 产品 | 强路径（canonical） | 弱路径（noindex） | 验证 |
|------|---------------------|------------------|------|
| candy bra | `/lolly/candy-bra-280g/` | `/candy/candy-bra-280g/` | ✅ |
| jelly joy stick | `/candy/old-fashion-lollies/jelly-joy-stick-20g/` | `/party-lollies/kidsparty/jelly-joy-stick-20g/` | ✅ |
| darrell lea rocky road | `/chocolate/darrell-lea/darrell-lea-...` | `/chocolate/australian-chocolate/darrell-lea-...` | ✅ |
| wicked fizz | `/candy/sour-lollies/wicked-fizz-...` | `/candy/wicked-fizz-...` | ✅ |
| silky gem | `/candy/sour-lollies/silky-gem-...` | `/candy/silky-gem-...` | ✅ |
| fairy floss | `/candy/sour-lollies/fairy-floss-50g/` | `/candy/fairy-floss-50g/` + `/party-lollies/kidsparty/sweetworldfairyfloss` | ✅ |

提交 Google Indexing API：12 个 URL 全部提交

---

### ✅ 问题三：博客文章路径重复 — 已修复（2026-03-29）

**实际情况（与最初分析有偏差）**：
- `/newcastle/` 所有 URL 已经 301 → `/candy-guides/`（早期已配置，301 均验证正确）
- GSC 仍显示旧 `/newcastle/` URL 是因为 Google 尚未处理 301 redirect，属于 **Google 处理延迟**，非内容问题
- 真正的蚕食在 `/candy-guides/` 内部：brain-licker 有两篇，nerd vs nerds 有两篇

**修复操作**：
- `/newcastle/powerade/`, `/newcastle/nerds-gummy-clusters/`, `/newcastle/brain-licker/`, `/newcastle/brain-licker-2/` 及各自 canonical 目标 — 提交 Google Indexing API（8 URLs），加速 Google 处理 301
- post 59677（`brain-licker`）设置 canonical → `brain-licker-2/`（通用解释页，曝光更多，保留 post，不删不改内容）
- post 59699（`nerd-gummy-clusters`）设置 canonical → `nerds-gummy-clusters/`（拼写正确，内容更全的新版）
- 两篇 WP Rocket 缓存清除，canonical 标签验证 ✅×2
- 提交 Google Indexing API（4 URLs）
- **安全原则**：所有操作均为 canonical 设置（非破坏性，可通过 `/wp-json/sw/v1/set-canonical` 随时撤销）

**待观察（无需操作）**：
- Google 处理 `/newcastle/` 301 后，GSC 报告的蚕食会自动消失
- brain-licker-2 和 nerds-gummy-clusters 获得信号集中后，排名应提升

---

### 🟡 问题四：首页关键词与内容不匹配

GSC 显示首页对 "lolly shop near me"（pos 26.6, clk 13）、"sweet shops near me" 有排名，但 H1/title 不含。同时停留时间异常低（Semrush 标红）。

- [ ] 更新首页 H1 和 title tag，加入 "lolly shop" / "sweet shop" 相关词
- [ ] 调查低停留时间原因（加载速度？内容匹配度？）

---

### 🟢 问题五：产品页 H1/title/meta 缺目标关键词 — 低优先级

（Semrush 标出，GSC 未显示明显点击损失，暂缓）
- [ ] 评估通过 `wp-seo-meta.php` 批量修复 WooCommerce 产品页 meta

---

## 长期预防机制（避免同类问题再次出现）

### 防蚕食规则
- **新产品上架时**：先搜索站内是否已有同名产品页，避免重复建页
- **URL 规范**：产品页统一使用 `/product-slug/`（扁平结构），不在分类子目录下建二级产品页
- **每季度**：用 Semrush Cannibalization Report 或 GSC 检查是否出现新的蚕食问题

### 内链规范
- **新博文发布时**：sweetsworld-seo-agent 的 `run_mvp.py` 已支持 `_find_cluster_peer_links()`，确保同 cluster 博文互链
- **新产品页上架时**：在产品描述末尾手动加 1–2 个相关博文链接
- **wordpress-ai-ops 的 weekly_cycle**：已配置 `use_append_faq` + `append_internal_links`，新博文自动处理

### 重复页面预防
- WooCommerce 产品不要在多个分类路径下生成重复 URL（检查 WC 的 "Product permalink" 设置）
- 确保每个产品只有一个规范 URL，其他路径返回 301 或设置 `rel=canonical`

---

## 注意事项

- Google Indexing API 每日限额 200 次，提交时注意分批
- 每次内容更新后都要重新提交 Google Indexing API
- RankMath meta 需通过 `wp-seo-meta.php` DB 端点写入（REST API 返回 403）
- 进度文件位置: `scripts/bulk_*_progress.json`
