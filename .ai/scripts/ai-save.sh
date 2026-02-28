#!/bin/bash
# AI 紧急保存脚本
# 无论当前状态如何，立即保存所有变更到 git
# 用于: Claude token 即将用尽、手动中断前、定时备份
#
# 用法: .ai/scripts/ai-save.sh [可选备注]
#
# 示例:
#   .ai/scripts/ai-save.sh
#   .ai/scripts/ai-save.sh "halfway through step 5"
#
# 定时使用 (每 10 分钟自动保存):
#   watch -n 600 .ai/scripts/ai-save.sh "auto"

set -e

NOTE="${1:-}"
TIMESTAMP=$(date +%Y%m%dT%H%M%S)

# 读取当前任务名（如果有）
TASK="unknown"
if [ -f ".ai/active-task.json" ]; then
    TASK_NAME=$(python3 -c "import json; print(json.load(open('.ai/active-task.json')).get('task') or 'unknown')" 2>/dev/null || echo "unknown")
    if [ "$TASK_NAME" != "null" ] && [ "$TASK_NAME" != "" ]; then
        TASK="$TASK_NAME"
    fi
fi

# 检查是否有变更
if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
    echo "没有需要保存的变更。"
    exit 0
fi

# Stage and commit
git add -A

MSG="[ai:autosave] ${TIMESTAMP} task:${TASK}"
if [ -n "$NOTE" ]; then
    MSG="${MSG} — ${NOTE}"
fi

git commit -m "$MSG"

echo "✓ 已保存: $MSG"
