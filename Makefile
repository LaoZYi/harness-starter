PYTHON ?= python3
PACKAGE = src/agent_harness

.PHONY: test check ci discover init

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v

check:
	$(PYTHON) scripts/check_repo.py
	$(PYTHON) -m py_compile $(PACKAGE)/*.py tests/*.py scripts/*.py

ci: check test

discover:
	$(PYTHON) scripts/discover_project.py $(TARGET)

init:
	$(PYTHON) scripts/init_project.py --target "$(TARGET)" $(ARGS)
