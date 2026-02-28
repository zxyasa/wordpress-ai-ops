# Plan: add-test-suite

## Steps
- [x] Step 1: 已有的 165 个测试 (models, handlers, safety, weekly, reporting, storage, resolver, wp_client, runner, batch, config) | Risk: done
- [ ] Step 2: 添加 rollback.py 测试 | Files: tests/unit/test_rollback.py, src/wp_ai_ops/rollback.py | Risk: low
- [ ] Step 3: 添加 cli.py 测试 | Files: tests/unit/test_cli.py, src/wp_ai_ops/cli.py | Risk: medium
- [ ] Step 4: 添加 handoff.py 测试 | Files: tests/unit/test_handoff.py, src/wp_ai_ops/handoff.py | Risk: low
- [ ] Step 5: 添加 openclaw_consumer.py 测试 | Files: tests/unit/test_openclaw_consumer.py, src/wp_ai_ops/openclaw_consumer.py | Risk: low
- [ ] Step 6: 添加 openclaw_http.py 测试 | Files: tests/unit/test_openclaw_http.py, src/wp_ai_ops/openclaw_http.py | Risk: low
- [ ] Step 7: 添加 notify.py 测试 | Files: tests/unit/test_notify.py, src/wp_ai_ops/notify.py | Risk: low
- [ ] Step 8: 添加 ui_bridge.py 测试 | Files: tests/unit/test_ui_bridge.py, src/wp_ai_ops/ui_bridge.py | Risk: low
- [ ] Step 9: 添加 gsc_export.py 测试 | Files: tests/unit/test_gsc_export.py, src/wp_ai_ops/gsc_export.py | Risk: low
- [ ] Step 10: 添加 exceptions.py 测试 | Files: tests/unit/test_exceptions.py, src/wp_ai_ops/exceptions.py | Risk: low
- [ ] Step 11: 全量测试运行 + 验收 | Risk: low

## Dependencies
Steps 2-10 互相独立，可任意顺序执行。Step 11 依赖所有前序步骤。

## Estimated Token Budget
Total steps: 11 | High-risk steps: 1 (cli) | Recommend: 2-3 sessions
