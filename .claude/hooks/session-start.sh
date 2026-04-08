#!/bin/bash
# SessionStart hook: 检查未完成任务 + evolution 定时任务

# 1. 显示未完成任务
if [ -s .agent-harness/current-task.md ]; then
  echo "=== 当前未完成任务（来自 .agent-harness/current-task.md）==="
  cat .agent-harness/current-task.md
  echo "=== 如果上面有未完成任务，请从断点继续，不要重新开始 ==="
fi

# 2. 检查 evolution 定时任务是否存在
if [ -f .claude/scheduled_tasks.json ]; then
  if grep -q "/evolve" .claude/scheduled_tasks.json 2>/dev/null; then
    exit 0  # 定时任务存在，一切正常
  fi
fi

echo ""
echo "⚠️ Evolution 每日进化定时任务未找到。"
echo "请重建：CronCreate(cron=\"37 9 * * *\", prompt=\"运行 /evolve 命令搜索新项目并创建 Issue 提案\", durable=true, recurring=true)"
