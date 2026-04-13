#!/bin/bash
# PostToolUse hook: 工具调用计数 + 阈值提醒。
#
# 设计说明（为什么不是 GSD 原版）：
# GSD 用 statusline 读 Claude Code 的 context remaining_percentage 字段，
# 但该字段未在官方 statusline schema 中暴露（仅 session_id / model / workspace /
# transcript_path / cwd / version）。所以降级为"工具调用计数"代理指标——
# 虽然不精确，但与上下文消耗正相关，且不依赖未公开 API，跨平台可用。
#
# 阈值：每 50 次工具调用提示可以考虑 /compact；每 100 次强警告；每 150 次建议 /clear。
# 计数存在 .agent-harness/.tool-call-count（纯文本），会话开始由 session-start.sh 重置。
#
# 开关：touch .agent-harness/.context-monitor-skip 可以关闭警告。

SKIP_FLAG=".agent-harness/.context-monitor-skip"
COUNT_FILE=".agent-harness/.tool-call-count"

# 用户显式关闭
[ -f "$SKIP_FLAG" ] && exit 0

# 确保目录存在
mkdir -p .agent-harness 2>/dev/null || exit 0

# 读取当前计数（默认 0）
current=0
if [ -f "$COUNT_FILE" ]; then
  current=$(cat "$COUNT_FILE" 2>/dev/null | tr -d '[:space:]')
  case "$current" in ''|*[!0-9]*) current=0 ;; esac
fi

new=$((current + 1))
echo "$new" > "$COUNT_FILE"

# 阈值提醒（只在关键节点提示，避免刷屏）
case "$new" in
  50)
    echo "⚠️  [context-monitor] 已调用 50 次工具 — 可以考虑运行 /compact 释放上下文" >&2
    ;;
  100)
    echo "🔴 [context-monitor] 已调用 100 次工具 — 强烈建议运行 /compact，否则接下来可能遇到 context 溢出" >&2
    ;;
  150)
    echo "🔴🔴 [context-monitor] 已调用 150 次工具 — 考虑 /clear 并从 current-task.md 恢复任务" >&2
    ;;
esac

exit 0
