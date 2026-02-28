# Plan: restaurant-square-setup

## Steps
- [ ] Step 1: 主着陆页 publish_post task JSON (含完整 HTML 内容) | Files: examples/tasks/restaurant_square_main.publish.json | Risk: medium (长内容)
- [ ] Step 2: 主着陆页 set_meta SEO | Files: examples/tasks/restaurant_square_main.seo.json | Risk: low
- [ ] Step 3: 主着陆页 inject_schema_faq (12+ FAQs) | Files: examples/tasks/restaurant_square_main.faq.json | Risk: medium
- [ ] Step 4: GBP 支撑页 publish + SEO | Files: examples/tasks/restaurant_gbp.publish.json, restaurant_gbp.seo.json | Risk: low
- [ ] Step 5: Facebook 支撑页 publish + SEO | Files: examples/tasks/restaurant_fb.publish.json, restaurant_fb.seo.json | Risk: low
- [ ] Step 6: QR Ordering 支撑页 publish + SEO | Files: examples/tasks/restaurant_qr.publish.json, restaurant_qr.seo.json | Risk: low
- [ ] Step 7: SOP 文档 (5个) | Files: docs/SOP_*.md | Risk: medium (多文件但独立)
- [ ] Step 8: dry-run 验证所有 task JSON | Risk: low

## Dependencies
Steps 1-3 先做主页。Steps 4-6 独立但内链依赖主页 slug。Step 7 独立。Step 8 最后。

## Estimated Token Budget
Total steps: 8 | High-risk steps: 2 (Step 1, 3 内容较长) | Recommend: 2-3 sessions
