#!/bin/bash
# Stop hook: 防止未保存进度丢失
#
# 逻辑(2026-04-26 范式革命:从内容形式识别 → 行为信号):
#   1. .stop-hook-skip 文件存在 → 放行(人工兜底开关)
#   2. current-task.md 不存在或为空 → 放行(无任务)
#   3. 含「(无进行中的任务)」/「(no active task)」占位符 → 放行(任务已收尾)
#   4. 顶部含 `## 状态[:：]<非空>` 字段 → 放行(向后兼容旧文件)
#   5. 无未勾 `- [ ]` checkbox → 放行(现状已合规)
#   6. **行为信号**:本会话 transcript 中 AI 用 Write/Edit/MultiEdit/NotebookEdit/Bash
#      操作过 current-task.md → 放行(AI 显式在管理任务,内容形式不重要)
#   7. **mtime 兜底**:文件最近 HARNESS_STOP_HOOK_MTIME_SECONDS 秒(默认 1800)内被改过
#      → 放行(跨会话续做场景)
#   8. 都不满足 → **block**(真"AI 静默丢进度"场景:文件存在 + 有未勾 + AI 本会话
#      从未碰过文件 + mtime 也很老)
#
# 设计哲学:
#   过去 5 次试图用「内容形式识别」(grep 状态字段)捕获「AI 是否管理任务」的语义信号,
#   每次都被自然语言变体击穿(同义词/标题级别/粗体/冒号变体/块引用/BOM/嵌套子项/
#   代码块示例)。本次换轨到「行为信号」——AI 写没写过文件是客观事实,无变体歧义。
#   架构上对应 architecture-patterns.md 反模式 1 第 1 优先级"自动发现",而非维护
#   AI 写法白名单。
#
# 输出:Claude Code 官方约定的 Stop hook JSON
#   { "decision": "block", "reason": "..." }  (https://code.claude.com/docs/en/hooks)
#
# 反自锁:读不到项目根就直接放行,不拦死用户。
set -euo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
CUR_TASK="$PROJECT_DIR/.agent-harness/current-task.md"
SKIP_FLAG="$PROJECT_DIR/.agent-harness/.stop-hook-skip"
MTIME_THRESHOLD="${HARNESS_STOP_HOOK_MTIME_SECONDS:-1800}"

# 保留 stdin 内容(Claude Code 发 transcript_path / session_id / hook_event_name)
STDIN_PAYLOAD=$(cat 2>/dev/null || true)

pass() { exit 0; }

block() {
  local reason="$1"
  printf '{"decision":"block","reason":%s}\n' \
    "$(printf '%s' "$reason" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')"
  exit 0
}

# 1. 人工放行开关
[ -f "$SKIP_FLAG" ] && pass

# 2. 文件不存在或为空
[ ! -s "$CUR_TASK" ] && pass

# 3. 占位符识别(任务已收尾的明确标记)
grep -qE '（无进行中的任务）|\(no active task\)' "$CUR_TASK" && pass

# 4. AI 主动声明状态字段(向后兼容旧文件)
grep -qE '^##[[:space:]]*状态[:：][[:space:]]*[^[:space:]]' "$CUR_TASK" && pass

# 5. 无未勾 checkbox → 无忧
grep -qE '^\s*-\s*\[\s*\]' "$CUR_TASK" || pass

# === 到这里:有未勾 + 文件非空 + 无收尾标记 + 无状态字段,需进一步判断 ===

# 6. 行为信号:从 stdin 提取 transcript_path,扫描本会话是否有 AI 写过 current-task.md
transcript_path=$(printf '%s' "$STDIN_PAYLOAD" | python3 -c '
import json, sys
try:
    data = json.loads(sys.stdin.read())
    p = data.get("transcript_path", "")
    if isinstance(p, str): print(p)
except Exception:
    pass
' 2>/dev/null || true)

if [ -n "$transcript_path" ] && [ -f "$transcript_path" ]; then
  if python3 - "$transcript_path" <<'PY' 2>/dev/null
import json, sys
WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit", "Bash"}
TARGET = "current-task.md"
try:
    with open(sys.argv[1], encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
            except Exception:
                continue
            msg = entry.get("message", {})
            if not isinstance(msg, dict):
                continue
            content = msg.get("content", [])
            if not isinstance(content, list):
                continue
            for c in content:
                if not isinstance(c, dict): continue
                if c.get("type") != "tool_use": continue
                if c.get("name") not in WRITE_TOOLS: continue
                inp = c.get("input", {})
                if TARGET in json.dumps(inp, ensure_ascii=False):
                    sys.exit(0)  # 行为信号命中 → 放行
except Exception:
    pass
sys.exit(1)  # 未命中 / 异常 → 走下一道兜底
PY
  then
    pass
  fi
fi

# 7. mtime 兜底:文件最近 X 秒内被改过(跨会话续做)
mtime=$(stat -f %m "$CUR_TASK" 2>/dev/null || stat -c %Y "$CUR_TASK" 2>/dev/null || echo 0)
now=$(date +%s)
if [ "$mtime" -gt 0 ] && [ $((now - mtime)) -lt "$MTIME_THRESHOLD" ]; then
  pass
fi

# 8. 真"AI 静默丢进度"场景 → block
block "current-task.md 存在未完成的 checkbox（- [ ] 未勾选）。
停止前请：
  1. 把已完成步骤勾选为 [x]
  2. 在文件顶部声明当前阶段，例如：
       ## 状态: 待验证                  （任务完结，等用户验证）
       ## 状态: 待用户确认               （方案已出，等用户拍板）
       ## 状态: 调研中,等用户回复关键问题  （暂停沟通，自定义描述也认）
     全角/半角冒号都行，状态值任意非空——只要主动声明就放行
  3. 若要强制跳过此检查，touch .agent-harness/.stop-hook-skip 后重试

这是 Agent Harness 的会话保护 hook（Issue #13，吸收自 MemPalace）。"
