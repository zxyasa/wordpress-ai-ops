# Progress: restaurant-square-setup
Last updated: 2026-02-16T15:08:00+11:00
Terminal: macbook-vscode
Current step: 8 / 8

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

## Recovery Notes
所有内容文件已创建并完成 dry-run 校验。共 10 个 task JSON + 5 个 SOP。
如需上线执行，可按顺序先跑 publish，再跑 seo/faq，再跑 growth_hub link。
