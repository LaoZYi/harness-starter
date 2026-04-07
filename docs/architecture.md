# 架构约束

## 模块职责

### CLI 层
- `src/agent_harness/cli.py`：统一入口，argparse 子命令注册和路由，不超过 280 行。
- `src/agent_harness/init_flow.py`：交互式和非交互式初始化流程（从 cli.py 拆出）。

### 核心功能层
- `src/agent_harness/discovery.py`：扫描目标项目并给出结构化画像。
- `src/agent_harness/assessment.py`：根据画像给出接入评分、缺口和建议。
- `src/agent_harness/initializer.py`：整合探测结果、预设和用户输入，渲染模板并生成文件。含插件渲染逻辑。
- `src/agent_harness/upgrade.py`：比较模板生成结果与现有文件，给出升级计划并执行。含 verify_upgrade 验证。
- `src/agent_harness/templating.py`：模板发现、占位符替换和落盘。

### 运维工具层
- `src/agent_harness/doctor.py`：健康检查（task-log 使用率、教训积累、占位符、长度）。
- `src/agent_harness/export.py`：项目画像导出（Markdown 或 JSON）。
- `src/agent_harness/stats.py`：任务统计分析（返工率、活跃度、教训数）。

### 辅助层
- `src/agent_harness/cli_utils.py`：rich 输出函数、语言默认值映射。
- `src/agent_harness/lang_detect.py`：语言/框架/ORM 检测。
- `src/agent_harness/models.py`：数据模型（ProjectProfile、InitializationResult 等）。

### 资源层
- `src/agent_harness/templates/common/`：生成到目标项目的通用模板。含规则、命令、文档、任务追踪等。
- `src/agent_harness/templates/superpowers/`：结构化工作流技能模板（25 个命令 + 1 个规则），默认启用，可通过 `--no-superpowers` 关闭。融合了 obra/superpowers（14 个基础技能）、EveryInc/compound-engineering-plugin（6 个增强技能）和 garrytan/gstack（5 个运维技能）。
- `src/agent_harness/presets/`：8 种项目类型的 JSON 预设，含 `workflow_skills_summary` 指定项目类型重点技能。
- `scripts/check_repo.py`：框架仓库守卫脚本。
- `scripts/sync_superpowers.py`：上游 skills 同步工具，支持双上游源。

### 测试层
- `tests/`：78 个回归测试，覆盖探测、评估、初始化、升级、CLI 集成、superpowers/compound 技能。

## 约束

1. 每个 Python 模块不超过 280 行。超过时拆分到新模块。
2. 模板内容必须通用，禁止引入样例业务代码。
3. 脚本逻辑和模板文本分离，禁止把长文案塞进 Python 代码。
4. CLI 新增子命令时，handler 放在独立模块，cli.py 只注册路由。
5. 自检脚本（check_repo.py）优先检查文件存在、模板连通、模块长度。

## 数据流

```
用户输入/配置
     ↓
discover_project() → ProjectProfile
     ↓
assess_project() → AssessmentResult
     ↓
prepare_initialization() → context dict (69 个模板变量)
     ↓
materialize_templates() → 写入目标项目（common 模板）
     ↓
materialize_templates() → 写入 superpowers 模板 (如果启用)
     ↓
_materialize_plugins() → 渲染 .harness-plugins/ (如果存在)
     ↓
verify_upgrade() → 验证结果
```

## 插件机制

目标项目中 `.harness-plugins/` 目录的文件在 init/upgrade 时被渲染：
- `rules/*.md` → 合并到 `.claude/rules/`
- `templates/**` → 保持目录结构渲染到项目根

插件文件支持与内置模板相同的 `{{variable}}` 占位符。

## 推荐扩展方式

- 想增加新项目类型：先加 `src/agent_harness/presets/*.json`，再补模板、评估逻辑和测试。
- 想增加新生成文件：先加模板，再补初始化测试和仓库自检。
- 想增加新 CLI 命令：新建模块放 handler，cli.py 只注册子命令，更新 runbook。
- 想增加新规则模板：放到 `src/agent_harness/templates/common/.claude/rules/`，加 paths frontmatter。
- 想增加新 Claude Code 命令：放到 `src/agent_harness/templates/common/.claude/commands/`（通用）或 `src/agent_harness/templates/superpowers/.claude/commands/`（工作流技能），文件名即命令名。
