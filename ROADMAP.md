# wordpress-ai-ops — 产品路线图

最后更新：2026-04-05

---

## 已完成

### 批量 SEO 改造（2026-03-27～29）
- 106 篇内容已完成 FAQPage JSON-LD、RankMath meta 和 Google Indexing API 提交。
- 53 篇旧内容已完成内链织入，并再次提交 Google Indexing API。
- 已提供 `wp_ai_ops.cli run` 的 dry-run / live 执行入口。
- 已接入 `growth-graph` auto action 消费链路：`src/wp_ai_ops/action_queue_consumer.py`。

### 运维能力
- `task_runner.py` 已具备任务执行、确认、审计和状态目录流程。
- 已具备快照和回滚能力，支持批量 SEO 变更的安全执行。
- `weekly_cycle.py` 已支持识别机会页并生成周任务。

## 当前问题

- [HIGH] `src/wp_ai_ops/weekly_cycle.py:426` — `append_faq` 不在 `SUPPORTED_TASK_TYPES`，自动分发链路会生成不可执行任务。
- [HIGH] `src/wp_ai_ops/wp_client.py:149` — bridge token 硬编码，存在泄漏和轮换风险。

## 待办

- TODO: 修复 `append_faq` 任务类型契约，让 weekly planner、task runner、consumer 使用同一枚举。
- TODO: 把 WP bridge token 移到 `.env` 或安全配置，移除代码内明文。
- TODO: 修正失败任务的写审计语义，避免 `record_write()` 在失败路径上误记成功。
- TODO: 对缺失 `wp_task_json` 的 auto item 增加告警或失败状态，而不是静默跳过。
- TODO: 收敛 `openclaw_http.py` 的 bearer token 暴露面，避免在 curl argv 中泄漏。
