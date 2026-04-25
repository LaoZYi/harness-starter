#!/bin/bash
# Stop hook: 防止未保存进度丢失
#
# 逻辑：
#   1. 若存在 .agent-harness/.stop-hook-skip 文件 → 放行（人工开关，用户主动跳过）
#   2. 若 current-task.md 不存在或为空 → 放行（无进行中任务）
#   3. 若顶部含 `## 状态[:：]<非空>` 字段 → 放行（AI 已主动声明当前阶段，
#      不限定字面：待验证/待用户确认/调研中/暂停沟通等任意值都认）
#   4. 若包含 "- [ ]" 未打勾的 checkbox → **block**，要求 AI 先把进度写到 current-task.md
#   5. 其他 → 放行
#
# 设计哲学（2026-04-25 更新）：
#   核心保护场景是"AI 静默 stop 丢进度"。AI 主动写了状态字段（无论字面）就说明
#   它已显式思考过当前阶段，不该继续被拦。之前的 5 字面白名单（待验证/待用户确认/
#   待需求确认/待方向确认/待确认）实际中 AI 难记忆完整，频繁误拦"AI 想暂停沟通"。
#
# 输出：Claude Code 官方约定的 Stop hook JSON
#   { "decision": "block", "reason": "..." }  （见 https://code.claude.com/docs/en/hooks）
#
# 反自锁：读不到项目根就直接放行，不拦死用户。
set -euo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
CUR_TASK="$PROJECT_DIR/.agent-harness/current-task.md"
SKIP_FLAG="$PROJECT_DIR/.agent-harness/.stop-hook-skip"

# 消费 stdin（Claude Code 会发 session_id / transcript_path / cwd 等 JSON，我们不依赖其字段）
cat >/dev/null 2>&1 || true

pass() {
  # 默认放行：无 JSON 输出 + exit 0
  exit 0
}

block() {
  local reason="$1"
  printf '{"decision":"block","reason":%s}\n' "$(printf '%s' "$reason" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')"
  exit 0
}

# 1. 人工放行开关
[ -f "$SKIP_FLAG" ] && pass

# 2. current-task 不存在或为空
[ ! -s "$CUR_TASK" ] && pass

# 3. AI 已主动声明当前任务阶段（任何 `## 状态[:：]<非空>` 字段都放行）
#    - 全角冒号 `状态：` 和半角冒号 `状态:` 都认
#    - 状态值任意（待验证/调研中/暂停沟通/等用户回复...），不限定字面
#    - 但 `## 状态：` 后只有空白不算标记，仍走下游 checkbox 检查
grep -qE "^##[[:space:]]*状态[:：][[:space:]]*[^[:space:]]" "$CUR_TASK" && pass

# 4. 存在未完成 checkbox
if grep -qE '^\s*-\s*\[\s*\]' "$CUR_TASK"; then
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
fi

# 5. 其他情况放行
pass
