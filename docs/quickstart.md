# Agent Harness 速查手册

> 完整版见 `docs/usage-manual.md`

## 一句话定位

给任意项目装一套 AI Agent 协作基础设施（文档、规则、命令、记忆、审计），让 Claude Code / Codex 开箱即用。

---

## 安装（30 秒）

```bash
git clone https://github.com/LaoZYi/harness-starter.git
cd harness-starter
make setup && make test
```

---

## 最常用的 5 个命令

```bash
# 1. 评估目标项目（不改文件，先看看）
harness init /path/to/repo --assess-only

# 2. 初始化（交互式，问 5 个问题后生成全套文件）
harness init /path/to/repo

# 3. 升级已接入项目（框架更新后）
harness upgrade plan /path/to/repo --show-diff   # 先看
harness upgrade apply /path/to/repo              # 再改

# 4. 健康检查
harness doctor /path/to/repo

# 5. 任务统计
harness stats /path/to/repo
```

---

## 初始化后发生了什么

```
your-project/
├── AGENTS.md              # AI 读这个开始工作
├── docs/                  # 产品/架构/运行手册（AI 自动补全）
├── .claude/
│   ├── rules/             # AI 行为约束（安全/测试/自治等）
│   ├── commands/           # 36 个工作流技能（/tdd /debug /lfg ...）
│   └── hooks/             # 会话保护（防丢进度、提醒 compact）
└── .agent-harness/
    ├── current-task.md    # 当前任务（预填了首次分析任务）
    ├── task-log.md        # 完成的任务归档
    ├── lessons.md         # 经验教训
    ├── memory-index.md    # 热知识索引（AI 优先读这个）
    └── bin/               # 内嵌运行时（clone 即用，无需装 CLI）
```

打开 Claude Code 进入项目，AI 自动接管首次分析任务。

---

## 技能速查（最常用 10 个）

| 要做什么 | 输入 |
|---------|------|
| 全自动从需求到交付 | `/lfg` |
| 写新功能（测试驱动） | `/tdd` |
| 修 bug | `/debug` |
| 不确定用什么技能 | `/which-skill` |
| 明确需求规格 | `/spec` |
| 写实现计划 | `/write-plan` |
| 完成前验证 | `/verify` |
| 代码评审 | `/multi-review` |
| 沉淀经验 | `/compound` |
| 检索历史教训 | `/recall <关键词>` |

完整 36 个技能见 `.claude/rules/superpowers-workflow.md`。

---

## 记忆系统（30 秒理解）

```
L0  rules/          ← 每次自动加载（硬规则）
L1  memory-index.md  ← 任务开始时加载（最近 10 条教训 + 5 条任务）
L2  lessons.md       ← 按需 /recall 检索
L3  task-log.md      ← 显式查询
```

索引坏了？`harness memory rebuild . --force`

---

## 多 Agent 协作（3 种模式选 1）

| 场景 | 用什么 | 一句话 |
|------|-------|--------|
| 几个独立小任务并行跑 | `/dispatch-agents` | 一次分发，一次收回 |
| 规划和执行分离 | `/subagent-dev` | 规划者想，执行者做 |
| 长任务 + 角色分权 + 实时看 | `/squad` | tmux 多窗口，每人一个 worktree |

### Squad 最小示例

```json
{
  "task_id": "auth-rewrite",
  "base_branch": "master",
  "workers": [
    { "name": "scout", "capability": "scout", "prompt": "探索 src/auth/" },
    { "name": "builder", "capability": "builder", "depends_on": ["scout"], "prompt": "实现重构" },
    { "name": "reviewer", "capability": "reviewer", "depends_on": ["builder"], "prompt": "评审代码" }
  ]
}
```

```bash
harness squad create spec.json    # 启动
harness squad status              # 看状态
harness squad watch               # 自动推进 + 监控
harness squad stop all            # 收工
```

---

## 审计和 Hooks

**审计**：对 current-task / task-log / lessons 的每次改动自动记录。

```bash
.agent-harness/bin/audit tail     # 看最近变更
.agent-harness/bin/audit stats    # 看统计
```

**Hooks**（自动生效，无需配置）：
- 开始会话 → 显示未完成任务
- 停止会话 → 检查是否有未保存进度
- 工具调用 50/100/150 次 → 提醒 `/compact`

---

## 9 种项目类型

`backend-service` · `web-app` · `cli-tool` · `library` · `worker` · `mobile-app` · `monorepo` · `data-pipeline` · `meta`

初始化时自动探测，也可手动选。不同类型生成不同的专属规则。

---

## 插件（团队自定义）

```
.harness-plugins/
├── rules/team-style.md       # → .claude/rules/team-style.md
└── templates/docs/guide.md   # → docs/guide.md
```

支持 `{{project_name}}` 等模板变量。init/upgrade 自动处理。

---

## 项目内嵌运行时

**维护者**用 `harness` CLI（init / upgrade / doctor）。
**使用者**用 `.agent-harness/bin/*`（clone 即用，无需装任何东西）。

---

## 急救

| 问题 | 解法 |
|------|------|
| 初始化跳过文件 | 加 `--force` |
| 升级有冲突标记 | 搜 `<<<<<<<`，手动选一边 |
| 升级覆盖了自定义内容 | `.agent-harness/backups/` 里找 |
| 记忆索引不一致 | `harness memory rebuild . --force` |
| stop hook 挡住退出 | `touch .agent-harness/.stop-hook-skip` |
| context-monitor 烦人 | `touch .agent-harness/.context-monitor-skip` |
| Squad worker 挂了 | `harness squad dump` 看时间点，手动重建 |
