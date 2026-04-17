PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
PACKAGE = src/agent_harness
HARNESS = PYTHONPATH=src $(PYTHON) -m agent_harness

.PHONY: test check ci lint typecheck skills-lint assess upgrade-plan upgrade-apply init sync-superpowers dogfood setup help

help:
	@echo "常用目标："
	@echo "  make setup     首次 clone 后初始化 .venv 和依赖（自动选 uv 或 pip，含 dev 工具）"
	@echo "  make test      跑测试"
	@echo "  make check     仓库健康检查 + lint"
	@echo "  make lint      ruff 代码风格检查"
	@echo "  make typecheck mypy 类型检查"
	@echo "  make ci        check + lint + typecheck + skills-lint + test（提交前运行）"
	@echo "  make init TARGET=/path/to/repo      对目标仓库执行 init"
	@echo "  make upgrade-plan TARGET=/path      查看升级计划"
	@echo "  make upgrade-apply TARGET=/path     应用升级"

setup:
	@if [ -d .venv ]; then \
	  echo ".venv 已存在，跳过创建（如需重建：rm -rf .venv && make setup）"; \
	elif command -v uv >/dev/null 2>&1; then \
	  echo "检测到 uv，使用 uv sync 初始化..."; uv sync --extra dev; \
	else \
	  echo "未检测到 uv，使用 python3 -m venv 初始化..."; \
	  python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'; \
	fi
	@echo "环境就绪。下一步：make test"

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v

lint:
	@if $(PYTHON) -c "import ruff" 2>/dev/null || command -v $(PYTHON) >/dev/null && $(PYTHON) -m ruff --version >/dev/null 2>&1; then \
	  $(PYTHON) -m ruff check $(PACKAGE) tests scripts; \
	else \
	  echo "ruff 未安装。运行：.venv/bin/python -m pip install -e '.[dev]' 或 uv sync --extra dev"; \
	  exit 1; \
	fi

typecheck:
	@if $(PYTHON) -m mypy --version >/dev/null 2>&1; then \
	  $(PYTHON) -m mypy $(PACKAGE); \
	else \
	  echo "mypy 未安装。运行：.venv/bin/python -m pip install -e '.[dev]' 或 uv sync --extra dev"; \
	  exit 1; \
	fi

check: lint
	$(PYTHON) scripts/check_repo.py
	$(PYTHON) -m compileall -q $(PACKAGE) tests scripts

skills-lint:
	$(HARNESS) skills lint .

ci: check typecheck skills-lint test

assess:
ifndef TARGET
	$(error 请指定 TARGET，例如：make assess TARGET=/path/to/repo)
endif
	$(HARNESS) init "$(TARGET)" --assess-only

upgrade-plan:
ifndef TARGET
	$(error 请指定 TARGET，例如：make upgrade-plan TARGET=/path/to/repo)
endif
	$(HARNESS) upgrade plan "$(TARGET)" $(ARGS)

upgrade-apply:
ifndef TARGET
	$(error 请指定 TARGET，例如：make upgrade-apply TARGET=/path/to/repo)
endif
	$(HARNESS) upgrade apply "$(TARGET)" $(ARGS)

dogfood:
	$(PYTHON) scripts/dogfood.py

sync-superpowers:
	$(PYTHON) scripts/sync_superpowers.py

init:
ifndef TARGET
	$(error 请指定 TARGET，例如：make init TARGET=/path/to/repo)
endif
	$(HARNESS) init "$(TARGET)" $(ARGS)
