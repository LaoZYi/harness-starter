# 运行手册

## 常用命令

- `make check`：校验框架仓库结构、模板入口、Python 语法和 dogfood 漂移检测。
- `make test`：运行框架级回归测试（304 个）。
- `make ci`：串联 `check` 和 `test`。
- `make dogfood`：同步框架自身的技能/规则文件（改了模板后运行此命令）。
- `make sync-superpowers`：从 3 个上游源拉取最新 skills 变更报告。
- `make assess TARGET=/path/to/repo`：探测目标项目并输出接入评估和建议。
- `make upgrade-plan TARGET=/path/to/repo ARGS="..."`：预览升级会新增和改动哪些文件。
- `make upgrade-apply TARGET=/path/to/repo ARGS="..."`：执行升级并自动备份被覆盖文件。
- `make init TARGET=/path/to/repo ARGS="..."`：初始化目标项目。

## 多 agent 日志隔离（子 agent diary）

- `harness agent init <id>`：创建 `.agent-harness/agents/<id>/{diary.md, status.md}`（幂等）
- `harness agent diary <id> "..."`：追加过程日志（时间戳 + 文本）
- `harness agent status <id> "..."`：覆盖当前状态
- `harness agent list`：按最近活动列出 agent
- `harness agent aggregate [<id>...]`：汇总 diary 供主 agent 归档决策
- id 规范：`^[a-z0-9][a-z0-9-]{0,30}$`（与 /squad 一致）

## 变更审计

**推荐用项目自带运行时（clone 即用，无需 harness CLI）**：

- `.agent-harness/bin/audit append --file lessons.md --op append --summary "..."`：追加审计记录（agent 身份读 `HARNESS_AGENT` env）
- `.agent-harness/bin/audit tail [--limit N] [--json]`：查看最近 N 条（默认 20，按时间倒序）
- `.agent-harness/bin/audit stats [--json]`：按 file / op / agent 聚合统计
- `.agent-harness/bin/audit truncate --before YYYY-MM-DD`：裁剪早于指定日期的记录

也可用 `harness audit ...`（等价，但需维护者机器装了 harness CLI）。

## 项目自带运行时（.agent-harness/bin/）

**Issue #24**：AI 工作流调用的命令已项目内嵌，**无需使用者装 harness CLI**。

结构：

```
.agent-harness/bin/
├── audit      # 等价于 harness audit
├── memory     # 等价于 harness memory
├── README.md  # 说明
└── _runtime/  # 纯 stdlib 源码副本（harness 自动管理，勿手工改）
```

**定位**：
- **`harness` CLI**（`pipx install agent-harness-starter`）—— 项目**维护者**用，负责 init / upgrade / doctor / export / stats / sync
- **`.agent-harness/bin/`** —— 项目**使用者**（clone 仓库的人）用，AI 工作流所需的所有命令都从这里调

**升级**：`.agent-harness/bin/_runtime/` 在 `harness upgrade apply` 时强制覆盖（无用户数据）。

## 使用 harness 命令

安装后（`pip install -e .`）可直接使用：

```bash
harness init /path/to/repo --assess-only
harness init /path/to/repo --assess-only --json
harness upgrade plan /path/to/repo
harness upgrade plan /path/to/repo --show-diff
harness upgrade plan /path/to/repo --only AGENTS.md
harness upgrade apply /path/to/repo
harness upgrade apply /path/to/repo --only AGENTS.md
harness init /path/to/repo
harness init /path/to/repo --scaffold ~/frameworks/vue-admin-template
harness init /path/to/repo --config examples/init-config.example.json --non-interactive
harness doctor /path/to/repo
harness export /path/to/repo
harness export /path/to/repo -o snapshot.md --json
harness stats /path/to/repo
harness sync --all                                          # 在 meta repo 内同步所有服务
harness sync /path/to/service --meta /path/to/meta          # 同步单个服务
harness sync /path/to/service                               # 再次同步（meta 路径已记住）
harness memory rebuild .                                    # 从 lessons/task-log 重建 memory-index.md
harness memory rebuild . --force                            # 覆盖已有索引
harness squad create spec.yaml                              # 按 YAML 创建 tmux 多 agent squad（仅启动 wave 0）
harness squad status                                        # 显示三态（done/running/pending）+ 阻塞时长
harness squad attach <worker>                               # 输出 tmux attach 命令
harness squad stop <worker|task_id|all>                     # 停止 worker / 整个 squad
harness squad done <worker>                                 # 标记 worker 完成（供 advance 识别，Issue #19a）
harness squad advance                                       # 启动依赖已满足的 pending worker（幂等）
harness squad watch [--interval 3]                          # 常驻进程：轮询 mailbox 自动 advance + Tier 0 watchdog（Issue #21/#22，Ctrl+C / 全部 done / session 死亡退出）
harness squad dump                                          # 导出 mailbox 事件为 JSONL（调试用，Issue #21）
```

未安装时也可通过 `PYTHONPATH=src python -m agent_harness` 替代 `harness`。

## 多 agent 协作（/squad，阶段 1 MVP）

### 前置依赖
- `tmux` ≥ 3.0
  - macOS：`brew install tmux`
  - Debian/Ubuntu：`sudo apt install tmux`
- `claude` CLI 已登录并在 PATH 中
- Windows：用 WSL（阶段 1 不支持原生 Windows）

### 典型用例

```bash
# 1) 编写 YAML spec
cat > /tmp/auth.yaml <<EOF
task_id: auth-rewrite
base_branch: master
workers:
  - name: scout
    capability: scout          # 只读探索
    prompt: "探索 src/auth/"
  - name: builder
    capability: builder        # 读写实现
    depends_on: [scout]
    prompt: "等 scout 的 report.md 就绪后按 specs/auth.md 实现"
  - name: reviewer
    capability: reviewer       # 只读审查
    depends_on: [builder]
    prompt: "对 builder 的 worktree 做 /multi-review"
EOF

# 2) 创建 squad（自动起 tmux session + N 个 worktree）
harness squad create /tmp/auth.yaml

# 3) 观察
harness squad status
tmux attach -t squad-auth-rewrite   # 实时看每个 worker 的终端

# 4) 停止（不删 worktree，留给 /finish-branch 合并）
harness squad stop all
```

### 故障排查
| 现象 | 排查点 |
|---|---|
| `未找到 tmux` | 按上面装 tmux |
| worker 启动即退出 | `tmux attach` 看具体错误；检查 worktree 下 `.claude/settings.local.json` 是否渲染正确 |
| capability 没有生效（worker 写了禁用的文件） | 检查 Claude Code 版本；`permissions.deny` 要求较新 CLI |
| 多 worker 同时写 `.agent-harness/lessons.md` 冲突 | 硬规则：worker 只能写 `workers/<name>/lessons.pending.md`，coordinator 合并 |
| `harness squad watch` 立即退出，提示"tmux session 'X' not found" | tmux session 已被外部 kill 或从未启动；先 `harness squad status` 看 manifest，再 `tmux ls` 确认；必要时重新 `harness squad create` |
| watch 日志频繁打印 "worker 失联：X" | tmux 窗口被 kill / claude 进程崩溃；`harness squad dump` 看 worker_crashed 时间点；本期不自动重启，需手工处理（删 worker 后重 create 或人工 attach 调试） |
| 想暂时关闭 watchdog（比如手动调试 worker） | `touch .agent-harness/.watchdog-skip`；watch 主循环仍跑 advance，仅静默失联检测；删除 sentinel 即可恢复 |
| watch 报 "watchdog 内部异常（已隔离，watch 继续）" | 通常是 mailbox SQLite I/O 故障（磁盘满、权限、db 损坏）或 tmux 卡住；watch 主调度不受影响；查 `mailbox.db`、`mailbox.db-wal`、磁盘空间和 `tmux ls` 响应 |

## 初始化建议流程

1. 先跑 `harness init /path/to/repo --assess-only` 看探测和评估结果。
2. 如果仓库已经接入过旧版本 harness，先跑 `harness upgrade plan` 看哪些文件会变。
3. 如果需要先 review 内容差异，加 `--show-diff`。
4. 如果只想先升级部分文件，使用 `--only`。
5. 如果接受这些变化，再运行 `harness upgrade apply`，它会先备份被覆盖文件。
6. 如有需要先用 `--dry-run` 预演初始化结果。
7. 再运行 `harness init /path/to/repo`，补充项目目标、命令和部署信息。
8. 初始化后进入目标项目，检查生成的 `AGENTS.md`、`docs/`、`.agent-harness/project.json` 和 `.agent-harness/init-summary.md`。

## 配置自动发现

如果目标仓库中有 `.harness.json`，所有命令会自动读取其中的配置作为默认值，无需每次传 `--config`。

## Meta 项目类型

Meta 项目是微服务系统的中央大脑，不含业务代码，管理服务注册、依赖关系和业务知识。

### 初始化 meta 项目

```bash
harness init /path/to/meta-repo
# 选择项目类型：meta（跳过敏感级别和生产环境问题）
```

初始化后生成的目录结构：

```
services/registry.yaml         # 服务注册表（名称、路径、领域、负责人）
services/dependency-graph.yaml  # 依赖关系图（provides/consumes）
business/domains/               # 按领域组织的业务知识
business/products/              # 产品需求
business/roadmap.md             # 版本规划
shared-plugins/                 # 分发到各服务的共享规则和模板
tasks/                          # 跨服务任务文件（YAML 格式）
BEST-PRACTICES.md               # 最佳实践指南
```

### 同步服务上下文

从 meta 仓库向各服务仓库同步上下文信息（服务间依赖、微服务规则、领域知识、共享插件）：

```bash
# 在 meta repo 内批量同步所有已注册服务
harness sync --all

# 同步单个服务（首次需指定 meta 路径）
harness sync /path/to/service --meta /path/to/meta-repo

# 再次同步同一服务（meta 路径已记住）
harness sync /path/to/service
```

同步后各服务仓库会生成：
- `docs/service-context.md` — 本服务的上下游关系和接口影响范围
- `.claude/rules/microservice.md` — 微服务协作规则（接口变更需协调谁）

### Meta 专属命令

初始化后可在 meta 项目中使用以下技能命令：
- `/meta-sync` — 等同于 `harness sync --all`
- `/meta-populate` — 从已注册仓库扫描推理，自动填充 meta 空缺
- `/meta-create-task` — 从会议纪要生成跨服务任务草稿
- `/meta-activate-task` — 激活任务，创建 worktree 工作空间

## 项目类型差异

不同项目类型会影响：
1. **生成的规则文件**：每种类型有专属规则（如 cli-tool 有退出码/管道规则，web-app 有无障碍/组件规则），不相关的通用规则会被排除（如 library 排除 api.md/database.md）
2. **评估加分项**：assessment 根据类型检查特征文件（如 backend-service 检查 Dockerfile，monorepo 检查 workspace 配置）
3. **init 流程**：meta 类型跳过敏感级别和生产环境问题

9 种类型：backend-service、web-app、cli-tool、library、worker、mobile-app、monorepo、data-pipeline、meta。

## 分层记忆加载

`.agent-harness/` 使用四层记忆策略，避免 lessons/task-log 随增长挤占上下文：

| 层 | 文件 | 加载时机 |
|---|------|---------|
| L0 | `project.json` | Claude 读 AGENTS.md 时顺带 |
| L1 | `current-task.md` + `memory-index.md` | `task-lifecycle` 规则在新任务开始时必读 |
| L2 | `lessons.md` + `references/*.md`（a11y/perf/security/testing checklist） | 按需：`/recall <关键词>` 或 grep |
| L3 | `task-log.md` 全文 | 显式：`/recall --history <关键词>` 或 grep |

### 维护流程

- `/compound` 技能写新教训时会自动同步 `memory-index.md`（"最近教训"段顶部插一行，超 10 条挤出最老；"最近任务"同理，上限 5 条）
- 老项目首次启用或索引被污染时，运行 `harness memory rebuild .` 从现有 lessons/task-log/references 重建
- 升级时 `memory-index.md` 按 `skip` 策略、`references/*` 按 `three_way` 策略处理（均保留用户编辑）
- `references/*.md` 用 `/recall --refs <关键词>` 定向检索（避免全文读入）

### 常见问题

1. `memory-index.md` 和 lessons.md 不一致
   → 运行 `harness memory rebuild . --force` 重建；今后 `/compound` 会保证原子更新
2. 索引中没有某条教训
   → 可能是在引入分层加载前写的。运行 rebuild 即可补齐

## 常见问题

1. 初始化时很多文件被跳过
   默认不会覆盖已有文件；如果确认需要覆盖，请加 `--force`。
2. 探测结果不准确
   这属于框架允许的情况，初始化阶段应该人工确认关键字段。
3. 新项目类型不适配
   先补 `presets/`，再补模板和测试。
4. 团队想把初始化参数标准化
   在目标仓库中维护 `.harness.json`，之后 `harness init --non-interactive` 即可。
5. 升级后出现合并冲突标记（`<<<<<<< 当前内容`）
   在文件中搜索 `<<<<<<<`，手动选择保留哪个版本，删除冲突标记后保存。冲突只出现在用户和框架修改了同一行时。
6. 升级覆盖了本地自定义内容
   先到 `.agent-harness/backups/<timestamp>/` 找回旧文件。注意：升级默认使用三方合并保留用户内容，只有无基准版本的老项目首次升级时才会覆盖（有备份）。
6. `make check` 报告"技能/规则模板已变更但生成产物未同步"
   运行 `make dogfood` 同步框架自身的 `.claude/commands/` 和 `.claude/rules/`，然后重新提交。
