#!/bin/bash
# Stop hook: 防止未保存进度丢失
#
# 逻辑：
#   1. 若存在 .agent-harness/.stop-hook-skip 文件 → 放行（人工开关，用户主动跳过）
#   2. 若 current-task.md 不存在或为空 → 放行（无进行中任务）
#   3. 若包含以下任一"等用户"状态字面 → 放行（AI 已明确暂停等用户）：
#      "状态：待验证"（完成态，等验证）/ "状态：待用户确认" / "状态：待需求确认"
#      / "状态：待方向确认" / "状态：待确认"（通用兜底）
#   4. 若包含 "- [ ]" 未打勾的 checkbox → **block**，要求 AI 先把进度写到 current-task.md
#   5. 其他 → 放行
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

# 3. AI 明确已进入等用户状态（5 个同义字面）
grep -qE "状态：待(验证|用户确认|需求确认|方向确认|确认)" "$CUR_TASK" && pass

# 4. 存在未完成 checkbox
if grep -qE '^\s*-\s*\[\s*\]' "$CUR_TASK"; then
  block "current-task.md 存在未完成的 checkbox（- [ ] 未勾选）。
停止前请：
  1. 把已完成步骤勾选为 [x]
  2. 若任务完结、等用户验证，标 ## 状态：待验证；
     若任务规划/方案已出、等用户确认需求方向，标 ## 状态：待用户确认 / 待需求确认 / 待方向确认
  3. 若要强制跳过此检查，touch .agent-harness/.stop-hook-skip 后重试

这是 Agent Harness 的会话保护 hook（Issue #13，吸收自 MemPalace）。"
fi

# 5. 其他情况放行
pass
