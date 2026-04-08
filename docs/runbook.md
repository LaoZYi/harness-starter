# 运行手册

## 常用命令

- `make check`：校验框架仓库结构、模板入口、Python 语法和 dogfood 漂移检测。
- `make test`：运行框架级回归测试（87 个）。
- `make ci`：串联 `check` 和 `test`。
- `make dogfood`：同步框架自身的技能/规则文件（改了模板后运行此命令）。
- `make sync-superpowers`：从 3 个上游源拉取最新 skills 变更报告。
- `make assess TARGET=/path/to/repo`：探测目标项目并输出接入评估和建议。
- `make upgrade-plan TARGET=/path/to/repo ARGS="..."`：预览升级会新增和改动哪些文件。
- `make upgrade-apply TARGET=/path/to/repo ARGS="..."`：执行升级并自动备份被覆盖文件。
- `make init TARGET=/path/to/repo ARGS="..."`：初始化目标项目。

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
```

未安装时也可通过 `PYTHONPATH=src python -m agent_harness` 替代 `harness`。

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

## 常见问题

1. 初始化时很多文件被跳过
   默认不会覆盖已有文件；如果确认需要覆盖，请加 `--force`。
2. 探测结果不准确
   这属于框架允许的情况，初始化阶段应该人工确认关键字段。
3. 新项目类型不适配
   先补 `presets/`，再补模板和测试。
4. 团队想把初始化参数标准化
   在目标仓库中维护 `.harness.json`，之后 `harness init --non-interactive` 即可。
5. 自动升级覆盖了本地自定义内容
   先到 `.agent-harness/backups/<timestamp>/` 找回旧文件，再决定如何合并。
6. `make check` 报告"技能/规则模板已变更但生成产物未同步"
   运行 `make dogfood` 同步框架自身的 `.claude/commands/` 和 `.claude/rules/`，然后重新提交。
