# Context: add-test-suite
Last updated: 2026-02-16T14:30:00+11:00

## Key Files (ONLY read these on resume)
- `src/wp_ai_ops/rollback.py` — 下一步要写测试的模块
- `tests/unit/test_safety.py` — 参考已有测试的编写风格
- `tests/integration/test_task_runner.py` — 参考集成测试的 mock 模式
- `src/wp_ai_ops/models.py` — 数据模型定义，测试中常用

## Architecture Notes
- 项目使用纯 Python stdlib，无外部依赖（除 pytest）
- 测试分 unit/ 和 integration/ 两层
- WP API 调用通过 wp_client.py 封装，测试中用 mock/patch
- 状态存储在 storage.py，使用 JSONL 格式

## Recent Changes Summary
- 2/15: 添加了 165 个测试覆盖 11 个模块（commit 4f93ddc）
- 还需为剩余 9 个模块添加测试

## Search Hints
- 查找模块公共接口: `rg "^def " src/wp_ai_ops/<module>.py`
- 查找已有测试模式: `rg "def test_" tests/`
- 查找 mock 使用: `rg "patch\(" tests/`
