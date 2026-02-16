# Context: restaurant-square-setup
Last updated: 2026-02-16T15:10:00+11:00

## Key Files (ONLY read these on resume)
- `examples/tasks/publish_growth_hub_page.execute.json` — 真实 publish_post 格式参考
- `examples/tasks/set_meta_rankmath.json` — set_meta 格式参考
- `examples/tasks/inject_schema_faq.json` — FAQ schema 格式参考
- `examples/tasks/growth_hub_add_restaurant_link.execute.json` — growth hub 内链追加任务（已做幂等 regex 修复）
- `src/wp_ai_ops/handlers.py` — 如需确认 handler 支持的字段

## Architecture Notes
- 站点: newcastlehub.info，WordPress + Flatsome 主题
- 页面内容使用 Flatsome section/row/col 结构
- AI_SLOT 标记用于可编辑区域
- task JSON 通过 cli run --task 执行

## Recent Changes Summary
- 已完成 Step 8 dry-run 校验（临时 task_id 方式，绕过 idempotent_skip）
- 修复 `growth_hub_add_restaurant_link.execute.json` 的 regex，使任务在“链接已存在”时返回 noop 而非失败

## Search Hints
- 查找已发布页面格式: rg "publish_post" examples/tasks/
- 查找 Flatsome HTML 结构: rg "section-content" examples/tasks/
