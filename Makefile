PYTHON ?= python3
PACKAGE = src/agent_harness

.PHONY: test check ci discover assess upgrade-plan init

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v

check:
	$(PYTHON) scripts/check_repo.py
	$(PYTHON) -m py_compile $(PACKAGE)/*.py tests/*.py scripts/*.py

ci: check test

discover:
	$(PYTHON) scripts/discover_project.py $(TARGET)

assess:
	$(PYTHON) scripts/assess_project.py $(TARGET)

upgrade-plan:
	$(PYTHON) scripts/plan_upgrade.py --target "$(TARGET)" $(ARGS)

init:
	$(PYTHON) scripts/init_project.py --target "$(TARGET)" $(ARGS)
