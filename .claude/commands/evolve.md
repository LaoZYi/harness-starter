# 自我进化：搜索、评估、提案

自动搜索 AI 编码工具领域的新项目和实践，评估是否值得吸收到本框架，合格的创建 GitHub Issue 提案等待人工审批。

当前项目：`Agent Harness Framework`（cli-tool / python）

---

## 第 1 步：搜索新项目

### 1.1 固定关键词搜索（覆盖研发全生命周期）

按研发阶段组织关键词，确保不遗漏：

```bash
# Agent 生态
gh search repos "agent skill" --sort stars --limit 15
gh search repos "claude code" --sort updated --limit 15
# 编码/实现
gh search repos "ai coding agent" --sort stars --limit 15
# 设计/架构
gh search repos "architecture decision record" --sort stars --limit 15
# 评审/质量
gh search repos "ai code review" --sort stars --limit 15
# 部署/发布
gh search repos "changelog generator" --sort stars --limit 15
gh search repos "release automation tool" --sort stars --limit 15
# 运维/监控
gh search repos "incident response tool" --sort stars --limit 15
```

### 1.2 新项目发现（不依赖关键词）

用 GitHub API 按 topic + 创建时间搜索，捕获用新概念命名的项目：

```bash
# 最近 30 天创建的 AI agent 相关项目（star > 30）
gh api search/repositories \
  -f q="topic:ai-agent created:>$(date -u -v-30d '+%Y-%m-%d' 2>/dev/null || date -u -d '30 days ago' '+%Y-%m-%d') stars:>30" \
  -f sort=stars -f order=desc -f per_page=15 \
  --jq '.items[] | "\(.full_name)\t\(.stargazers_count)\t\(.description)"'
```

### 1.3 趋势概念捕获（WebSearch → 关键词提取 → GitHub 搜索）

用 WebSearch 搜索最新趋势文章，从中**提取新出现的概念术语**，再拿回 GitHub 搜：

1. 执行 WebSearch：
   - "AI coding agent new methodology {当前年份}"
   - "software engineering agent trend {当前年份}"
2. 从文章中提取 2-3 个新概念关键词（如 "vibe coding"、"ADLC"、"multi-agent coding"）
3. 用这些关键词执行 `gh search repos "<新概念>" --sort stars --limit 10`

### 1.4 监控已知上游

检查已跟踪的 3 个上游仓库是否有新的技能发布：

```bash
# 检查 superpowers 最近 commit
gh api repos/obra/superpowers/commits --jq '.[0:5] | .[] | .commit.message' 2>/dev/null

# 检查 compound-engineering 最近 commit
gh api repos/EveryInc/compound-engineering-plugin/commits --jq '.[0:5] | .[] | .commit.message' 2>/dev/null

# 检查 gstack 最近 commit
gh api repos/garrytan/gstack/commits --jq '.[0:5] | .[] | .commit.message' 2>/dev/null
```

### 1.5 监控已吸收项目的更新

从已关闭的 `evolution` Issue 中提取吸收过的项目，检查它们是否有值得再次评估的新特性：

```bash
# 提取已吸收项目的 GitHub 链接（去除 .git 后缀，排除非仓库 URL）
gh issue list --label evolution --state closed --json body --limit 500 \
  | python3 -c "
import sys, json, re
for i in json.load(sys.stdin):
    for u in re.findall(r'https://github\.com/[\w-]+/[\w.-]+', i.get('body','')):
        u = re.sub(r'\.git$', '', u)  # 去除 .git 后缀
        if u.count('/') == 4:  # 确保是 github.com/owner/repo 格式
            print(u)
" | sort -u
```

对每个已吸收的项目，检查自上次吸收以来的更新：

```bash
# 获取最近 commit（与上游监控逻辑一致）
gh api repos/<owner>/<repo>/commits --jq '.[0:10] | .[] | "\(.commit.author.date) \(.commit.message)"' 2>/dev/null
# 检查是否有新的 release
gh api repos/<owner>/<repo>/releases/latest --jq '.tag_name + " " + .published_at' 2>/dev/null
```

**判断标准**：如果发现以下情况，创建 `evolution-update` 标签的 Issue：

- 新增了我们尚未吸收的技能/模块
- 对已吸收的技能有重大方法论更新
- 发布了新版本且 CHANGELOG 中有与我们相关的变更

> 注意：已吸收项目的**重复能力**不需要再次提案，只关注**新增的、我们没有的**能力。

**`evolution-update` Issue 内容格式**：

```markdown
## 项目更新

- **链接**：<GitHub URL>
- **原始吸收 Issue**：#<原 evolution Issue 编号>
- **检测日期**：<YYYY-MM-DD>

## 发现的新特性

### 新特性 1：<名称>
- **什么变了**：<对比上次吸收时的差异>
- **我们是否需要**：<对比现有技能，是否填补空白>
- **建议操作**：吸收 / 参考 / 跳过

## 近期更新摘要

<最近 10 条 commit 或最新 release 的要点>

*此 Issue 由 /evolve 步骤 1.5 自动创建。审批后可通过 `/lfg` 实施更新集成。*
```

创建流程与 `evolution` Issue 一致（GitHub + GitLab 双向同步）。

### 1.6 已处理项目去重

在评估新发现的候选项目之前，先拉取所有（open + closed）带 `evolution` 或 `evolution-update` 标签的 Issue：

```bash
gh issue list --label evolution --state all --json title,body,state --limit 500 \
  | python3 -c "import sys,json; [print(i['state'], i['title']) for i in json.load(sys.stdin)]"
gh issue list --label evolution-update --state all --json title,body,state --limit 500 \
  | python3 -c "import sys,json; [print(i['state'], i['title']) for i in json.load(sys.stdin)]"
```

**去重规则**：
- `evolution` Issue 中出现过的项目 → **排除**（不创建新的 `evolution` 提案）
- 但步骤 1.5 仍会检查这些项目的更新（可能创建 `evolution-update` 提案）
- `evolution-update` Issue 中的项目 → 如果是 **open 且创建超过 30 天**，视为过期，关闭后允许重新检查；如果是 open 且不到 30 天，跳过

### 1.7 初筛条件

从搜索结果中筛选，保留满足以下条件的项目：

- Star ≥ 50（有一定社区认可）
- 最近 30 天内有更新（活跃维护）
- 非 fork（原创项目）
- 与 AI 编码工具/方法论/工作流相关
- 不是已跟踪的 3 个上游仓库
- **不在已处理项目排除列表中**（步骤 1.6）

---

## 第 2 步：深度评估

对每个通过初筛的项目，读取其 README 和核心文件，回答以下问题：

### 2.1 基本信息

- 项目名称和链接
- 核心功能（一句话）
- 技术栈
- Star 数和活跃度

### 2.2 独特性评估

与本框架已有的 29 个技能逐一对比：

| 已有技能 | 是否覆盖 |
|---------|---------|
| `/ideate` — 结构化构思 | ? |
| `/brainstorm` — 设计对话 | ? |
| `/spec` — 规格驱动开发 | ? |
| `/adr` — 架构决策记录 | ? |
| `/write-plan` — 实施计划 | ? |
| `/tdd` — 测试驱动开发 | ? |
| `/debug` — 系统性排障 | ? |
| `/execute-plan` — 按计划执行 | ? |
| `/subagent-dev` — 子代理协作开发 | ? |
| `/dispatch-agents` — 并行任务分发 | ? |
| `/use-worktrees` — Git worktree 隔离 | ? |
| `/verify` — 完成前验证 | ? |
| `/multi-review` — 多角度评审 + 辩论质证 | ? |
| `/request-review` — 评审请求准备 | ? |
| `/receive-review` — 评审反馈处理 | ? |
| `/compound` — 知识沉淀 | ? |
| `/lint-lessons` — 知识库维护 | ? |
| `/cso` — 安全审计 | ? |
| `/health` — 质量仪表盘 | ? |
| `/careful` — 安全拦截 | ? |
| `/git-commit` — 结构化提交 | ? |
| `/finish-branch` — 分支收尾 | ? |
| `/todo` — 任务管理 | ? |
| `/doc-release` — 文档同步 | ? |
| `/retro` — 工程回顾 | ? |
| `/lfg` — 全自主流水线 | ? |
| `/write-skill` — 编写新技能 | ? |
| `/use-superpowers` — 技能选择引导 | ? |
| `/evolve` — 自我进化 | ? |
| `/squad` — 多 agent 常驻协作（tmux + worktree + capability 分权） | ? |

**关键问题**：这个项目提供了什么我们**没有**的独特能力？

### 2.3 可行性评估

| 维度 | 评估 |
|------|------|
| 可模板化？ | 纯方法论（Markdown 可表达）还是需要运行时代码？ |
| 依赖？ | 零依赖 / 需要安装外部工具 / 需要 API key？ |
| 通用性？ | 适用于所有项目类型，还是只适用于特定语言/框架？ |
| 与 `/lfg` 兼容？ | 能嵌入到 LFG 的哪个阶段？ |

### 2.4 评估结论

每个项目产出一个结论：

- **吸收** — 有独特价值，可模板化，建议集成
- **参考** — 有启发但不适合直接集成（如只加一行引用）
- **跳过** — 已覆盖、不可模板化、或价值不足

---

## 第 3 步：创建提案 Issue

对每个结论为"吸收"的项目，**同时在所有远端仓库创建 Issue**（GitHub + GitLab）。

### 创建流程（每个 Issue 必须执行两步）

**第一步：创建 GitHub Issue**

```bash
gh issue create --title "..." --label "evolution" --body "..."
```

**第二步：立即同步到 GitLab**

```bash
curl -sS --request POST \
  --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  --header "Content-Type: application/json" \
  --data '{"title":"<同 GitHub>","description":"<同 GitHub body>","labels":"evolution"}' \
  "http://192.168.4.102/api/v4/projects/ai-x%2Fzjaf-harness/issues"
```

> 如果 `GITLAB_TOKEN` 未设置 → **🔴 停下来提示用户**：`export GITLAB_TOKEN=<your-token>`
> 如果 GitLab API 调用失败，告知用户"GitHub Issue 已创建但 GitLab 同步失败"，不要静默忽略。

### Issue 内容模板

Issue body 必须包含以下所有章节，每个章节都要展开写，不能只写一行概括：

```markdown
## 项目信息

- **链接**：<GitHub URL>
- **Star**：<数量>
- **最近更新**：<日期>
- **核心能力**：<一句话描述>
- **技术栈**：<语言/框架>

## 目标项目亮点分析

<展开 3-5 段详细说明这个项目做得好的地方：>
<- 它解决了什么问题？用什么独特方法？>
<- 它的核心设计哲学是什么？>
<- 它的用户体验/开发体验有什么可借鉴之处？>
<- 哪些具体功能或模式让人眼前一亮？>
<- 引用 README 或代码中的关键描述，用 > 引用块标注>

## 我们要吸收什么

<明确列出要吸收的具体内容，每一项展开说明：>

### 吸收项 1：<能力名称>
- **源项目中的实现**：<它怎么做的，读了哪些文件，核心逻辑是什么>
- **我们缺少什么**：<对比现有技能，具体差在哪里>
- **吸收后变成什么**：<新技能名或增强哪个现有技能>
- **嵌入 /lfg 阶段**：<阶段 N，为什么放在这个阶段>

### 吸收项 2：<能力名称>
- （同上格式）

## 怎么吸收（实施方案）

<具体的实施步骤，每步都要可执行：>

1. **模板创建**：在 `templates/superpowers/.claude/commands/` 下创建 `<skill-name>.md.tmpl`
2. **核心逻辑**：<要写什么内容，从源项目提取哪些方法论，如何改写为中文>
3. **集成点**：<修改哪些现有文件——workflow 规则、决策树、preset、lfg.md>
4. **测试**：<在 tests/ 中添加什么测试>
5. **文档同步**：<更新 product.md/architecture.md 的哪些章节>
6. **dogfood**：运行 `make dogfood && make ci` 验证

## 预期效果

<吸收后框架能力会有什么变化：>

- **覆盖的研发阶段**：<从"缺少 X 阶段"到"完整覆盖 X">
- **用户体验改善**：<用户原来要 Y 步手动操作，现在自动化为 Z>
- **与竞品的差距**：<吸收后在 X 维度上追平/超越 Y 项目>

## 可行性与风险

| 维度 | 评估 |
|------|------|
| 可模板化 | <是/否，为什么> |
| 外部依赖 | <无/需要 xxx，如何处理> |
| 通用性 | <所有项目/仅 xxx 类型> |
| 工作量预估 | <改动文件数、新增行数量级> |
| 风险 | <可能的问题、与现有技能的冲突、维护负担> |

发现日期：<YYYY-MM-DD>
发现来源：<第 1 层固定关键词 / 第 2 层新项目发现 / 第 3 层趋势概念>

*此 Issue 由 /evolve 自动创建。审批后可通过 `/lfg #<编号>` 实施集成。*
```

对结论为"参考"的项目，同样双向创建 Issue 但标签为 `evolution-reference`，降低优先级。

**提示**：审批后用 `/lfg #<编号>` 执行 GitHub Issue，用 `/lfg gl#<编号>` 执行 GitLab Issue。

---

## 第 4 步：输出汇总

完成搜索和评估后，输出今日进化报告：

```
## 🧬 进化报告 (YYYY-MM-DD)

搜索范围：GitHub + Web
候选项目：<N> 个
通过初筛：<N> 个
深度评估：<N> 个

### 结果

| 项目 | Star | 结论 | Issue |
|------|------|------|-------|
| <name> | <N> | 吸收 | #<issue_id> |
| <name> | <N> | 参考 | #<issue_id> |
| <name> | <N> | 跳过 | — |

### 上游动态

- superpowers: <最近更新摘要或"无新变化">
- compound-engineering: <最近更新摘要或"无新变化">
- gstack: <最近更新摘要或"无新变化">

### 已吸收项目更新（步骤 1.5）

| 项目 | 上次吸收 | 新变化 | 操作 |
|------|---------|--------|------|
| <name> | #<原Issue> | <新特性摘要或"无新变化"> | evolution-update / 无需操作 |
```

---

## 注意事项

- **不要自动实施任何集成**。`/evolve` 只搜索、评估和提案，不写代码
- **不要创建重复 Issue**。步骤 1.6 已拉取所有状态的 evolution Issue（含已关闭），确保已处理的项目不会重复提案。已吸收项目的**新特性**用 `evolution-update` 标签单独提案（步骤 1.5）
- **控制 Issue 数量**。每天最多创建 3 个"吸收"提案，避免信息过载
- **标记搜索日期**。在 Issue 中注明发现日期，方便追踪新鲜度
