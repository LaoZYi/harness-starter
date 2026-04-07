PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
PACKAGE = src/agent_harness
HARNESS = PYTHONPATH=src $(PYTHON) -m agent_harness

.PHONY: test check ci assess upgrade-plan upgrade-apply init sync-superpowers

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v

check:
	$(PYTHON) scripts/check_repo.py
	$(PYTHON) -m py_compile $(PACKAGE)/*.py tests/*.py scripts/*.py

ci: check test

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

sync-superpowers:
	$(PYTHON) scripts/sync_superpowers.py

init:
ifndef TARGET
	$(error 请指定 TARGET，例如：make init TARGET=/path/to/repo)
endif
	$(HARNESS) init "$(TARGET)" $(ARGS)
