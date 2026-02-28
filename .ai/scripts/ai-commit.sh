#!/bin/bash
# AI 标准化小步 commit 脚本
# 用法: .ai/scripts/ai-commit.sh <task-name> <step> <total> "<message>"
#
# 示例:
#   .ai/scripts/ai-commit.sh add-test-suite 3 8 "Add rollback module tests"

set -e

TASK="${1:?用法: ai-commit.sh <task-name> <step> <total> \"<message>\"}"
STEP="${2:?缺少 step 编号}"
TOTAL="${3:?缺少 total 步数}"
MSG="${4:?缺少 commit message}"

# 确保 progress.md 已被修改（防止忘记更新进度）
PROGRESS_FILE=".ai/tasks/${TASK}/progress.md"
if [ -f "$PROGRESS_FILE" ]; then
    if ! git diff --name-only --cached -- "$PROGRESS_FILE" | grep -q .; then
        if ! git diff --name-only -- "$PROGRESS_FILE" | grep -q .; then
            echo "⚠️  警告: progress.md 未被修改。请先更新进度再 commit。"
            echo "   文件: $PROGRESS_FILE"
            read -p "是否继续? (y/N) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    fi
fi

# Stage all changes
git add -A

# Commit with standard format
git commit -m "$(cat <<EOF
[ai:${TASK}] step ${STEP}/${TOTAL}: ${MSG}

refs: .ai/tasks/${TASK}/progress.md
EOF
)"

echo "✓ Committed: [ai:${TASK}] step ${STEP}/${TOTAL}: ${MSG}"
