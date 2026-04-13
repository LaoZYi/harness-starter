#!/bin/bash
# PreCompact hook: 上下文压缩前的 checkpoint
#
# Claude Code 文档明确 PreCompact "无 decision control"，不能 block 压缩，
# 只能做副作用。本脚本做两件事：
#   1. 往 audit.jsonl 追加一条 pre-compact 检查点（复用 Issue #12 基础设施）
#   2. 往 stderr 打印软提示，让 AI 在响应中主动总结关键决策到 current-task.md
#
# Claude Code 在压缩前会注入这段 stderr 作为系统消息。
set -euo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
AUDIT="$PROJECT_DIR/.agent-harness/audit.jsonl"

# 消费 stdin（含 session_id / transcript_path / matcher=manual|auto）
INPUT="$(cat 2>/dev/null || true)"

# 1. 写 audit 条目（best-effort：audit 目录不存在时跳过，不影响压缩）
if [ -d "$PROJECT_DIR/.agent-harness" ]; then
  mkdir -p "$PROJECT_DIR/.agent-harness"
  TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  AGENT="${HARNESS_AGENT:-claude-code}"
  TRIGGER="$(printf '%s' "$INPUT" | python3 -c 'import sys,json; d=json.loads(sys.stdin.read() or "{}"); print(d.get("trigger") or d.get("matcher") or "unknown")' 2>/dev/null || echo unknown)"
  printf '{"ts":"%s","file":"current-task.md","op":"update","agent":"%s","summary":"pre-compact checkpoint (trigger=%s)"}\n' \
    "$TS" "$AGENT" "$TRIGGER" >> "$AUDIT"
fi

# 2. 向 stderr 发软提示（Claude Code 会把 stderr 注入系统消息给 AI）
cat >&2 <<'EOF'
⚠️ 上下文即将被压缩。请在压缩前：
  1. 把本次会话的关键决策写入 .agent-harness/current-task.md 的 Decisions 段
  2. 值得沉淀的经验用 /compound 写入 lessons.md
  3. 长期参考的信息写入 docs/ 对应文档

压缩后回看时，AI 读 current-task + memory-index 能迅速恢复上下文（见 ADR 0001 分层记忆加载）。
EOF

exit 0
