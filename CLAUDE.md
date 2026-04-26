# Claude Code Notes

本仓库的规则以 `AGENTS.md` 为入口，以 `docs/`、`templates/` 和 `src/agent_harness/` 为长期知识源。

开始任务时请先读：

1. `AGENTS.md`
2. 任务相关的 `docs/` 下文档
3. 提交前看 `CONTRIBUTING.md`
4. 涉及运行和排障时看 `docs/runbook.md`
5. 改模板时看 `src/agent_harness/templates/common/`

不要把新的长期规则只写在这里。

## Health Stack

> SSOT 是 Makefile（`make ci` = `check + typecheck + skills-lint + deadcode + shellcheck-hooks + test`）。本节是 gstack `/health` 兼容映射，命令变更时与 Makefile 同步。

- typecheck: `.venv/bin/python -m mypy src/agent_harness`
- lint: `.venv/bin/python -m ruff check src/agent_harness tests scripts`
- test: `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests`
- deadcode: `.venv/bin/python -m vulture src/agent_harness --min-confidence 80`
- shell: `shellcheck .claude/hooks/*.sh`
- skills-lint: `PYTHONPATH=src .venv/bin/python -m agent_harness skills lint .`
- repo-guard: `.venv/bin/python scripts/check_repo.py`

项目专属：`PYTHONPATH=src .venv/bin/python -m agent_harness lfg audit`（15 维 lfg 威力体检，不在 gstack 标准评分内）。
