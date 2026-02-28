# Task: add-test-suite
Created: 2026-02-15
Status: active

## Goal
为 wordpress-ai-ops 的所有源码模块补齐单元测试和集成测试。

## Scope
- 已有测试的模块: models, handlers, safety, weekly_scoring, reporting, storage, target_resolver, wp_client, task_runner, batch_runner, config (11个)
- 缺失测试的模块: cli, exceptions, gsc_export, handoff, notify, openclaw_consumer, openclaw_http, rollback, ui_bridge (9个)

## Acceptance Criteria
- [ ] 所有 9 个缺失模块都有对应测试文件
- [ ] 所有测试通过 (`pytest --tb=short -q` 零失败)
- [ ] 核心路径覆盖（正常流程 + 主要错误路径）
