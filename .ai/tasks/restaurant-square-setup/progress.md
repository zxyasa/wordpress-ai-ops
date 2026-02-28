# Progress: restaurant-square-setup
Last updated: 2026-02-16T15:28:00+11:00
Terminal: macbook-vscode
Current step: 11 / 11

## Completed
- [x] Step 1: 主着陆页 publish_post ← restaurant_square_main.publish.json
- [x] Step 2: 主着陆页 SEO ← restaurant_square_main.seo.json
- [x] Step 3: 主着陆页 FAQ Schema (12 FAQs) ← restaurant_square_main.faq.json
- [x] Step 4: GBP 支撑页 ← restaurant_gbp.publish.json + restaurant_gbp.seo.json
- [x] Step 5: Facebook 支撑页 ← restaurant_fb.publish.json + restaurant_fb.seo.json
- [x] Step 6: QR Ordering 支撑页 ← restaurant_qr.publish.json + restaurant_qr.seo.json
- [x] Step 7: SOP 文档 (5个) ← docs/SOP_Discovery.md, SOP_Setup.md, SOP_GoLive.md, SOP_Training.md, SOP_MonthlySupport.md

## Current
- [x] Step 8: dry-run 验证所有 task JSON
  - Status: completed
  - Validation result:
    - 10 个 task JSON 使用临时 task_id 完成真实 `--plan-only`
    - `growth_hub_add_restaurant_link.execute.json` 原正则不幂等，已修复为“可匹配已存在/不存在链接”两种状态
    - 修复后该任务 dry-run 结果为 `noop`（符合预期）
- [x] Step 9: 核心页补内链到 Growth Hub + Hosting 子页
  - Status: completed (plan-only passed)
  - Task: `examples/tasks/link_bridge_growth_hub.execute.json`
  - Result: 7 个核心页全部命中 `AI_SLOT:CTA`，均生成可预期 diff（每页新增 Related reads 3 链接）
- [x] Step 10: 执行补链任务并复核前台入链
  - Status: completed
  - Execution: `link_bridge_growth_hub.execute.json` 已执行，7页更新成功
  - Verification: `/newcastle-growth-hub` 入链由 0 提升到 7
- [x] Step 11: 重写 Growth Hub 正文为“真实业务内容 + 统一风格”
  - Status: completed
  - Task: `examples/tasks/growth_hub_rewrite_content.execute.json`
  - Dry-run: page 676 生成单段替换 diff，chars_delta=1372
  - Execute: `idempotent_skip`（此前已执行）
  - Frontend verification:
    - `/newcastle-growth-hub/` 已存在真实正文模块 `#ai-growth-hub`
    - 已确认文案含 `Newcastle Growth Hub`、`Implementation Paths`、`Restaurant Square Setup`
    - 已确认 `AI_SLOT:INTRO`、`AI_SLOT:CTA`、`AI_SLOT:SCHEMA` 均在前台源码中

## Recovery Notes
当前任务 11/11 全部完成。后续可进入下一任务（全站基础优化或 SEO meta 插件化）。

## Post-Step Verification
- 2026-02-16T04:09Z 再次执行全套 10 个任务（`--confirm`）：
  - `rs-main-publish-001`
  - `rs-main-seo-003`
  - `rs-main-faq-002`
  - `rs-gbp-publish-001`
  - `rs-gbp-seo-003`
  - `rs-fb-publish-001`
  - `rs-fb-seo-003`
  - `rs-qr-publish-001`
  - `rs-qr-seo-003`
  - `gh-add-restaurant-link-001`
- 结果全部为 `idempotent_skip`，说明任务已执行过且幂等保护生效。

## Additional Work (2026-02-16)
- 目标：补齐 pages 薄内容并做基础 SEO（仅 pages，不动文章）
- 已执行内容增强（成功）：
  - page 36 `/portfolio/`
  - page 92 `/web-hosting-starter/`
  - page 95 `/web-hosting-freedom/`
  - page 99 `/web-hosting-premier/`
- 每页均追加了统一结构块：`AI_SLOT:INTRO` / `AI_SLOT:FAQ` / `AI_SLOT:CTA` / `AI_SLOT:SCHEMA`
- 前台校验：4 页均命中新增 section id（`ai-portfolio-seo-block`、`ai-hosting-*-seo`）
- 已尝试写 RankMath meta（`rank_math_title/description/focus_keyword`），执行器返回 updated
  - 但 REST after 快照 `meta` 仅有 `footnotes`
  - 结论：当前站点未开放 RankMath meta keys 的 REST 可写映射，需安装最小插件片段后再写入

## Site Structure Upgrade (2026-02-16)
- 已按“行业 + 解决方案 + 成果导向”上线 12 个任务（目录 `examples/tasks/site_structure_20260216`）
- 首页（page 403）已更新定位文案与 CTA：
  - Hero: `Helping Newcastle Local Businesses Grow & Keep More Profit`
  - Sub: `POS Setup • Online Ordering • Websites • Google Growth • Social Media`
  - CTA: `Get Free Business Audit` + `Book a Strategy Call`
  - 三大卖点：利润、流量掌控、本地支持
- 服务页（page 39）已追加 `Our Services + Packages` 结构区块
- 新增并发布页面：
  - `/restaurant-solutions/`
  - `/beauty-salon-solutions/`
  - `/trades-solutions/`
  - `/retail-solutions/`
  - `/mechanic-solutions/`
  - `/pos-setup-newcastle/`
  - `/online-ordering-newcastle/`
  - `/google-business-optimisation-newcastle/`
  - `/why-choose-newcastle-hub/`
  - `/free-newcastle-business-audit/`

## Continuous Optimization (2026-02-16)
- 新增产品/服务分流页：
  - `/ecommerce-setup-newcastle/`
  - `/booking-system-newcastle/`
- 行业页分流优化：
  - `retail` 主推 ecommerce 路径
  - `beauty / trades / mechanic` 主推 booking 路径
- Audit 页新增“产品型/服务型”分流区块并补相关引导
- 首页首屏 CTA 区新增双路径按钮（Products vs Services）
- 新增 FAQ+Schema：
  - `ecommerce-setup-newcastle`（FAQPage）
  - `booking-system-newcastle`（FAQPage）
- 主导航已增量添加并前台验证可见：
  - `Industries` → `/restaurant-solutions/`
  - `Products` → `/ecommerce-setup-newcastle/`
  - `Audit` → `/free-newcastle-business-audit/`

## Lead Form Embed (2026-02-16)
- 目标：为 `/free-newcastle-business-audit/` 落地可提交表单
- 已执行任务：
  - `examples/tasks/site_structure_20260216_v4/audit_form_embed_718.execute.json`
- 执行结果：
  - `--plan-only` 成功，变更仅命中 `AI_SLOT:CTA`
  - `--confirm` 成功，page 718 状态 `updated`
  - 前台校验命中 `wpcf7-f400-p718-o1`，表单已渲染可提交
- 备注：
  - 当前通过 shortcode 复用已有 `CF7 form id=400 (quote form)` 完成上线
  - 使用 `api-bot` 直写 CF7 表单定义未落库（权限限制），后续需管理员级可写凭据再升级为定制字段版（industry/POS/revenue 等）

## Mail Delivery Fix (2026-02-17)
- 目标：修复“CF7 返回 mail_sent 但收件箱收不到”的投递问题
- 已完成：
  - 通过 REST 安装插件：`wp-mail-smtp/wp_mail_smtp`（HTTP 201）
  - 通过 REST 启用插件：`status=active`（HTTP 200）
  - 再次确认表单提交 API 返回 `mail_sent`（功能链路通）
- 当前阻塞：
  - SMTP 账户参数未配置（host/port/encryption/username/password）
  - 未完成前，仍可能由主机默认 `wp_mail()` 投递，存在进箱不稳定
- 参数校验：
  - 用户提供的 Google Workspace SMTP 凭据已做独立连通性验证（STARTTLS + LOGIN）
  - 结果：`SMTP_LOGIN_OK`（账号密码可用）
  - 说明：当前剩余工作是把凭据写入 WP Mail SMTP 插件设置并完成投递验收
- 下一步（待用户提供 SMTP 参数）：
  - 在 WP Mail SMTP 中配置发件通道
  - 再次发起自动化测试提交
  - 以“收到邮件”为验收条件闭环

## Site Optimization Batch 2 (2026-02-17)
- 目标：继续做 pages 维度的安全增量优化（FAQ/CTA/Schema），不破坏 Flatsome 结构
- 已执行任务目录：`examples/tasks/site_structure_20260217_v5/`
  - `ai_pack_789_faq_cta.execute.json`（page 789）
  - `online_ordering_722_faq.execute.json`（page 722）
  - `why_choose_719_faq.execute.json`（page 719）
- 执行结果：
  - `run-batch --plan-only`：3/3 planned，全部通过
  - `run-batch --confirm`：3/3 updated，0 failed
- 前台验证：
  - `/ai-service-implementation-pack/` 命中 `#ai-pack-seo-block` + FAQPage JSON-LD
  - `/online-ordering-newcastle/` 命中 `#ai-online-ordering-faq` + FAQPage JSON-LD
  - `/why-choose-newcastle-hub/` 命中 `#ai-why-choose-faq` + FAQPage JSON-LD

## FAQ Accordion Upgrade (2026-02-17)
- 需求：FAQ 改为可展开/收起样式
- 执行任务：
  - `examples/tasks/site_structure_20260217_v5/faq_accordion_789.execute.json`
  - `examples/tasks/site_structure_20260217_v5/faq_accordion_722.execute.json`
  - `examples/tasks/site_structure_20260217_v5/faq_accordion_719.execute.json`
- 结果：
  - 三页均 `updated`
  - FAQ 由 `h3 + p` 改为 `details/summary` 折叠结构
  - 前台已确认出现 `<details>`，支持收起/展开

## Industry FAQ Accordion Rollout (2026-02-17)
- 目标：把 5 个行业页补齐可收起 FAQ + FAQ Schema + 审计 CTA
- 执行任务目录：`examples/tasks/site_structure_20260217_v6/`
  - `industry_restaurant-solutions_715_accordion_faq.execute.json`
  - `industry_beauty-salon-solutions_713_accordion_faq.execute.json`
  - `industry_trades-solutions_717_accordion_faq.execute.json`
  - `industry_retail-solutions_716_accordion_faq.execute.json`
  - `industry_mechanic-solutions_714_accordion_faq.execute.json`
- 执行结果：
  - `run-batch --plan-only`：5/5 planned
  - `run-batch --confirm`：5/5 updated，0 failed
- 前台验证：
  - 5 个行业页均新增 `ai-*-faq` section，并命中 `<details>` 折叠结构
  - 均附带 FAQPage JSON-LD 与审计导向 CTA

## Core FAQ Accordion Rollout (2026-02-17)
- 目标：核心服务页 FAQ 统一折叠样式（details/summary）
- 执行任务目录：`examples/tasks/site_structure_20260217_v7/`
  - `faq_accordion_contact_28.execute.json`（updated）
  - `faq_accordion_hosting-plan_85.execute.json`（updated）
  - `faq_accordion_marketing-service_548.execute.json`（updated）
  - `faq_accordion_website-service_494.execute.json`（updated）
  - `faq_accordion_services_39.execute.json`（被频控跳过）
  - `faq_accordion_services_39_override.execute.json`（one-off 提升上限后 updated）
- 结果：
  - 核心 5 页均完成 FAQ 折叠化
  - `services` 页保留原“Newcastle Growth Services”引导文案，仅将 FAQ 结构改为折叠样式

## FAQ Unified Standard (2026-02-17)
- 用户反馈：折叠 FAQ 间距过紧，且各页面样式不一致。
- 已完成两层统一：
  - 代码层（未来生成）：`src/wp_ai_ops/handlers.py` 的 `_build_faq_html` 改为统一输出 `details/summary + ai-faq-accordion` 样式。
  - 线上层（历史页面）：批量标准化 20 个页面 FAQ 插槽，统一为同一套宽松间距样式。
- 新标准（统一值）：
  - `details` 间距 `margin-bottom: 18px`
  - `summary` 内边距 `16px 18px`
  - 展开内容内边距 `16px 18px 18px`
  - `line-height` 分别为 `1.6 / 1.8`
- 批量执行结果：`updated=20, failed=0`
- 代表页面抽查：`/`、`/services/`、`/about/` 已命中新样式。

## Step 2 SEO Meta (2026-02-17)
- 已安装并启用 Rank Math 插件（slug: `seo-by-rank-math/rank-math`）。
- 直接 REST 写入测试：`rank_math_title` POST 返回 200 但未持久化（meta 仍未暴露）。
- 结论：仍需 meta bridge（register_post_meta + show_in_rest）才能让 `set_meta` 生效。
- 限制：WP REST `/wp/v2/plugins` 仅支持 `slug` 安装，不支持上传本地 zip 插件；本地 `wp-aiops-meta-bridge.zip` 无法直接通过该接口安装。
- 已收紧本地 bridge 插件默认策略：只开放 RankMath 3 个 key（Yoast 改为可选扩展）。

## Step 3 Baseline Auto Cycle (2026-02-17)
- 已建立无 GSC 真实数据可跑的 baseline 输入：
  - `examples/csv/newcastle_baseline_gsc.csv`
  - `examples/csv/newcastle_baseline_ga.csv`
- 新增脚本：`scripts/run_newcastle_weekly_baseline.sh`
- `plan` 结果已生成：`weekly-output-newcastle-baseline/`
- `execute` 尝试结果：任务生成成功，但执行阶段全部因本机 Python DNS 解析异常失败（`[Errno 8] nodename nor servname provided`），未写线上内容。

## Step 2 Completed: RankMath REST Meta Write Enabled (2026-02-17)
- 通过 REST 安装并启用插件：
  - `seo-by-rank-math/rank-math`
  - `code-snippets/code-snippets`
- 通过 Code Snippets REST 新建并启用 snippet（id=5）：
  - `AI Ops Meta Bridge (RankMath REST)`
  - 仅开放：`rank_math_title`, `rank_math_description`, `rank_math_focus_keyword`
  - 权限限制：仅 `api-bot` 且需 `edit_post`
- 回归验证：
  - `pages/29` 已可见并可写 `rank_math_*` 字段
  - 实写成功并持久化验证通过
- 已执行一轮核心页面 meta 自动写入（5 页）：
  - 首页 `403`
  - Services `39`
  - Online Ordering `722`
  - Restaurant Solutions `715`
  - Trades Solutions `717`

## Step 3 Progress: Baseline Auto Weekly Execute (2026-02-17)
- 新增 baseline 数据与脚本：
  - `examples/csv/newcastle_baseline_gsc.csv`
  - `examples/csv/newcastle_baseline_ga.csv`
  - `scripts/run_newcastle_weekly_baseline.sh`

## Demo Landing Page Published (2026-02-17)
- 用户需求：先做一个独立 demo 页面，不改首页。
- 已创建任务：
  - `examples/tasks/demo_newcastle_conversion.publish.json`
- 执行记录：
  - `--plan-only` 成功（planned）
  - 首次 `--confirm` 失败，原因为旧凭据失效 + 401
  - 用户提供新 `api-bot` 应用密码后恢复鉴权，重新 `--confirm` 成功
- 发布结果：
  - 页面 ID: `856`
  - URL: `https://newcastlehub.info/newcastle-demo-conversion/`
  - 状态: `created`
- 前台验证：
  - 已命中 Hero 标题 `Helping Newcastle Local Businesses Grow and Keep More Profit`
  - 已命中 `Demo Page FAQ`
  - 已命中 CTA `Approve and Continue`
- 修复关键 bug：根 URL 目标解析失败（空 slug）
  - 代码：`src/wp_ai_ops/target_resolver.py`
  - 新增 fallback：按 `link` path 精确匹配
  - 测试：`tests/integration/test_target_resolver.py`（新增 root URL 场景）
- 回归测试：`pytest` 通过（57 passed）
- 执行结果：`weekly-output-newcastle-baseline-exec/tasks`
  - 批次成功执行，包含 `updated` 与 `cooldown` 跳过
  - 频控/idempotency 行为符合预期
