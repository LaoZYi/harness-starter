#!/bin/bash
# SessionStart hook: 检查未完成任务 + 重置工具调用计数

# 重置 context-monitor 计数器（新会话 = 新 context）
mkdir -p .agent-harness 2>/dev/null
echo "0" > .agent-harness/.tool-call-count 2>/dev/null || true

if [ -s .agent-harness/current-task.md ]; then
  echo "=== 当前未完成任务（来自 .agent-harness/current-task.md）==="
  cat .agent-harness/current-task.md
  echo "=== 如果上面有未完成任务，请从断点继续，不要重新开始 ==="
fi
