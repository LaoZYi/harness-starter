# 产品规则

这个仓库的目标不是承载某个具体业务，而是把"项目认知初始化"和"AI agent 协作入口"产品化。

## 框架提供什么

1. **探测**：扫描目标项目，产出结构化画像（语言、包管理器、命令、目录结构）。
2. **评估**：根据画像产出接入评分、缺口和建议。
3. **初始化**：根据项目类型和探测结果生成 23 个文档/配置文件。支持 `--scaffold` 从现有技术框架创建。
4. **首次分析**：初始化后 current-task.md 预填分析任务，AI 打开项目自动补全文档。
5. **升级**：对已接入的项目做增量升级，支持 diff 预览、选择性升级和自动备份。
6. **运维**：doctor（健康检查）、export（画像导出）、stats（任务统计）。
7. **扩展**：插件机制，用户可在 .harness-plugins/ 下放自定义规则和模板。

## 支持的项目类型（8 种）

backend-service、web-app、cli-tool、library、worker、mobile-app、monorepo、data-pipeline

每种类型在 `presets/` 下有独立的 JSON 预设，定义行为变化判定、架构关注点、发布检查项和默认完成标准。

## CLI 命令清单

| 命令 | 作用 |
|------|------|
| `harness init <target>` | 交互式初始化（可选框架脚手架 + 5 个问题 + 自动探测） |
| `harness init <target> --scaffold <path>` | 基于现有技术框架创建 |
| `harness init <target> --assess-only` | 只看探测评估结果 |
| `harness init <target> --non-interactive` | 全自动初始化 |
| `harness upgrade plan <target>` | 升级预览 |
| `harness upgrade apply <target>` | 执行升级（自动备份） |
| `harness doctor <target>` | 健康检查 |
| `harness export <target>` | 导出项目画像 |
| `harness stats <target>` | 任务数据统计 |

## 什么算行为变化

- 影响探测结果字段的改动
- 影响评估结果和接入建议的改动
- 影响模板生成内容的改动
- 影响初始化默认值或交互流程的改动
- 影响生成文件列表或目录结构的改动
- 影响 CLI 命令参数或输出格式的改动

## 变更原则

- 改了初始化输出，必须补对应测试。
- 改了探测字段，必须同步更新文档和模板。
- 改了 CLI 命令或参数，必须同步更新 `docs/runbook.md`。
- 改了模板，必须验证生成结果（`harness init /tmp/test --dry-run`）。
